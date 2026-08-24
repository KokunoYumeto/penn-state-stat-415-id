#!/usr/bin/env python3
"""Merge three bounded translation maps into the canonical first-unit ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "source" / "id-ID" / "first_unit_translation.csv"
SEGMENTS = ROOT / "backend" / "first_unit_segments.jsonl"
BINDINGS = ROOT / "backend" / "first_unit_translation_bindings.jsonl"
RECEIPT = ROOT / "build" / "FIRST_UNIT_TRANSLATION_RECEIPT.json"
PARTS = {
    "a": ROOT / "working" / "translation_part_a.json",
    "b": ROOT / "working" / "translation_part_b.json",
    "c": ROOT / "working" / "translation_part_c.json",
}
FIELDS = (
    "segment_id", "document_id", "component_id", "section_id", "source_sha256",
    "source_text", "target_text", "status",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def expected_part_keys() -> dict[str, set[str]]:
    return {
        "a": (
            {f"O006-PSU-000-S{i:04d}" for i in range(1, 78)}
            | {f"O006-PSU-001-S{i:04d}" for i in range(1, 193)}
        ),
        "b": {f"O006-PSU-001-S{i:04d}" for i in range(193, 356)},
        "c": {f"O006-PSU-001-S{i:04d}" for i in range(356, 447)},
    }


def load_segments() -> list[dict[str, object]]:
    rows = [json.loads(line) for line in SEGMENTS.read_text("utf-8").splitlines() if line]
    if len(rows) != 523 or len({row["segment_id"] for row in rows}) != 523:
        raise RuntimeError("normalized segment catalog is not the admitted 523-row boundary")
    return rows


def load_template(segments: list[dict[str, object]]) -> list[dict[str, str]]:
    try:
        rows = list(csv.DictReader(io.StringIO(TEMPLATE.read_text("utf-8"))))
    except csv.Error as exc:
        raise RuntimeError(f"invalid translation CSV: {exc}") from exc
    if not rows or tuple(rows[0].keys()) != FIELDS or len(rows) != len(segments):
        raise RuntimeError("translation CSV header or row count differs")
    for row, segment in zip(rows, segments):
        for key in ("segment_id", "document_id", "component_id", "source_sha256", "source_text"):
            expected = str(segment[key])
            if row[key] != expected:
                raise RuntimeError(f"translation CSV source mismatch: {segment['segment_id']} / {key}")
        expected_section = str(segment["section_id"] or "")
        if row["section_id"] != expected_section:
            raise RuntimeError(f"translation CSV section mismatch: {segment['segment_id']}")
    return rows


def load_parts() -> tuple[dict[str, str], list[dict[str, object]]]:
    expected = expected_part_keys()
    merged: dict[str, str] = {}
    evidence: list[dict[str, object]] = []
    for name in ("a", "b", "c"):
        data = PARTS[name].read_bytes()
        try:
            values = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid translation part {name}: {exc}") from exc
        if not isinstance(values, dict) or set(values) != expected[name]:
            raise RuntimeError(f"translation part {name} does not match its exact assigned key set")
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise RuntimeError(f"translation part {name} has an empty or non-string target")
        overlap = set(merged).intersection(values)
        if overlap:
            raise RuntimeError(f"translation parts overlap: {sorted(overlap)[:3]}")
        merged.update(values)
        evidence.append(
            {
                "part": name,
                "path": PARTS[name].relative_to(ROOT).as_posix(),
                "segments": len(values),
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    return merged, evidence


def compute() -> dict[str, bytes]:
    segments = load_segments()
    rows = load_template(segments)
    translations, part_evidence = load_parts()
    expected_ids = {str(row["segment_id"]) for row in segments}
    if set(translations) != expected_ids:
        raise RuntimeError("merged parts do not cover the complete segment catalog")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    binding_rows: list[dict[str, object]] = []
    for ordinal, (row, segment) in enumerate(zip(rows, segments), start=1):
        raw_target = translations[row["segment_id"]]
        source = row["source_text"]
        # Text nodes are often split around math/link markup. Reuse the exact
        # source-node boundary whitespace so adjacent translated fragments do
        # not run together even when a translator supplied only the prose core.
        leading = re.match(r"^\s*", source).group(0)
        trailing = re.search(r"\s*$", source).group(0)
        target = leading + raw_target.strip() + trailing
        if not target.strip():
            raise RuntimeError(f"normalized target is empty: {row['segment_id']}")
        complete = dict(row)
        complete["target_text"] = target
        complete["status"] = "translated"
        writer.writerow(complete)
        binding_rows.append(
            {
                "schema": "o006.stat415.translation-binding.v1",
                "segment_id": row["segment_id"],
                "document_id": row["document_id"],
                "component_id": row["component_id"],
                "section_id": row["section_id"] or None,
                "ordinal": ordinal,
                "locale": "id-ID",
                "source_sha256": row["source_sha256"],
                "target_sha256": sha256(target.encode("utf-8")),
                "status": "translated",
            }
        )

    csv_payload = output.getvalue().encode("utf-8")
    bindings_payload = canonical_jsonl(binding_rows)
    receipt = {
        "schema": "o006.stat415.first-unit-translation.v1",
        "status": "complete",
        "documents": ["index", "Lesson00"],
        "segment_count": len(binding_rows),
        "locale": "id-ID",
        "boundary_whitespace_rule": "exact source-node leading/trailing whitespace wrapped around translated prose core",
        "parts": part_evidence,
        "translation_csv": {
            "path": TEMPLATE.relative_to(ROOT).as_posix(),
            "bytes": len(csv_payload),
            "sha256": sha256(csv_payload),
        },
        "bindings": {
            "path": BINDINGS.relative_to(ROOT).as_posix(),
            "bytes": len(bindings_payload),
            "sha256": sha256(bindings_payload),
        },
    }
    return {
        TEMPLATE.relative_to(ROOT).as_posix(): csv_payload,
        BINDINGS.relative_to(ROOT).as_posix(): bindings_payload,
        RECEIPT.relative_to(ROOT).as_posix(): canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            atomic_write(ROOT / relative, payload)
        state = "written"
    else:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"translation output differs: {relative}")
        state = "verified"
    receipt_payload = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(json.dumps({"mode": state, "segments": 523, "receipt_sha256": sha256(receipt_payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
