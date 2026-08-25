#!/usr/bin/env python3
"""Merge the three bounded Lesson 02 translation maps deterministically."""

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
TEMPLATE = ROOT / "working" / "lesson02_segments.csv"
TARGET = ROOT / "source" / "id-ID" / "lesson02_translation.csv"
BINDINGS = ROOT / "backend" / "lesson02_translation_bindings.jsonl"
RECEIPT = ROOT / "build" / "LESSON02_TRANSLATION_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
TERMINOLOGY_QA = ROOT / "working" / "lesson02_terminology_qa.md"
SOURCE_FINDINGS = ROOT / "working" / "lesson02_source_findings.md"
PARTS = {
    "a": ROOT / "working" / "lesson02_translation_part_a.json",
    "b": ROOT / "working" / "lesson02_translation_part_b.json",
    "c": ROOT / "working" / "lesson02_translation_part_c.json",
}
FIELDS = (
    "segment_id", "document_id", "component_id", "section_id", "source_sha256",
    "source_text", "target_text", "status",
)
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"


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
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def expected_part_keys() -> dict[str, set[str]]:
    return {
        "a": {f"O006-PSU-003-S{i:04d}" for i in range(1, 109)},
        "b": {f"O006-PSU-003-S{i:04d}" for i in range(109, 217)},
        "c": {f"O006-PSU-003-S{i:04d}" for i in range(217, 325)},
    }


def load_template() -> tuple[list[dict[str, str]], bytes]:
    data = TEMPLATE.read_bytes()
    try:
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid Lesson 02 segment CSV: {exc}") from exc
    if not rows or tuple(rows[0].keys()) != FIELDS or len(rows) != 324:
        raise RuntimeError("Lesson 02 segment CSV header or row count differs")
    expected_ids = [f"O006-PSU-003-S{i:04d}" for i in range(1, 325)]
    if [row["segment_id"] for row in rows] != expected_ids:
        raise RuntimeError("Lesson 02 segment IDs are not the admitted sequential boundary")
    if any(
        row["document_id"] != "O006-PSU-003"
        or row["component_id"] != "Lesson02"
        or row["target_text"]
        or row["status"] != "pending"
        for row in rows
    ):
        raise RuntimeError("Lesson 02 pending template fields differ")
    return rows, data


def load_parts() -> tuple[dict[str, str], list[dict[str, object]]]:
    expected = expected_part_keys()
    merged: dict[str, str] = {}
    evidence: list[dict[str, object]] = []
    for name in ("a", "b", "c"):
        data = PARTS[name].read_bytes()
        try:
            values = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid Lesson 02 translation part {name}: {exc}") from exc
        if not isinstance(values, dict) or set(values) != expected[name]:
            raise RuntimeError(f"Lesson 02 translation part {name} has the wrong key set")
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise RuntimeError(f"Lesson 02 translation part {name} has an empty target")
        if set(merged).intersection(values):
            raise RuntimeError("Lesson 02 translation partitions overlap")
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


def input_evidence(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def compute() -> dict[str, bytes]:
    rows, template_data = load_template()
    translations, part_evidence = load_parts()
    expected_ids = {row["segment_id"] for row in rows}
    if set(translations) != expected_ids:
        raise RuntimeError("Lesson 02 translation parts do not cover all segments")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    binding_rows: list[dict[str, object]] = []
    translated_text: list[str] = []
    for ordinal, row in enumerate(rows, start=1):
        source = row["source_text"]
        raw_target = translations[row["segment_id"]]
        leading = re.match(r"^\s*", source).group(0)
        trailing = re.search(r"\s*$", source).group(0)
        target = leading + raw_target.strip() + trailing
        if not target.strip():
            raise RuntimeError(f"normalized target is empty: {row['segment_id']}")
        complete = dict(row)
        complete["target_text"] = target
        complete["status"] = "translated"
        writer.writerow(complete)
        translated_text.append(target)
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

    joined = "\n".join(translated_text).casefold()
    required_terms = (
        "pendugaan", "penduga titik", "penduga tak bias", "ruang parameter",
        "rataan kuadrat galat", "kecukupan", "metode momen",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise RuntimeError(f"required Lesson 02 terminology absent: {missing_terms}")
    forbidden_terms = ("galat kuadrat rata-rata", "mean squared error")
    present_forbidden = [term for term in forbidden_terms if term in joined]
    if present_forbidden:
        raise RuntimeError(f"superseded Lesson 02 terminology present: {present_forbidden}")
    if "\ufffd" in joined:
        raise RuntimeError("Lesson 02 translation contains a replacement character")

    csv_payload = output.getvalue().encode("utf-8")
    bindings_payload = canonical_jsonl(binding_rows)
    receipt = {
        "schema": "o006.stat415.lesson02-translation.v1",
        "status": "complete",
        "document": "Lesson02",
        "document_id": "O006-PSU-003",
        "segment_count": len(binding_rows),
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "boundary_whitespace_rule": "exact source-node leading/trailing whitespace wrapped around translated prose core",
        "terminology_rule": "component glossary plus the Lesson 02 Indonesian field-evidence decision",
        "template": {
            "path": TEMPLATE.relative_to(ROOT).as_posix(),
            "bytes": len(template_data),
            "sha256": sha256(template_data),
        },
        "parts": part_evidence,
        "terminology_inputs": [
            input_evidence(GLOSSARY),
            input_evidence(TERMINOLOGY_QA),
        ],
        "source_findings": input_evidence(SOURCE_FINDINGS),
        "translation_csv": {
            "path": TARGET.relative_to(ROOT).as_posix(),
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
        TARGET.relative_to(ROOT).as_posix(): csv_payload,
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
                raise RuntimeError(f"Lesson 02 translation output differs: {relative}")
        state = "verified"
    receipt_payload = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(
        json.dumps(
            {"mode": state, "segments": 324, "receipt_sha256": sha256(receipt_payload)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
