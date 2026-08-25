#!/usr/bin/env python3
"""Merge the three bounded Lesson 06 translation maps deterministically."""

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
TEMPLATE = ROOT / "working" / "lesson06_segments.csv"
TARGET = ROOT / "source" / "id-ID" / "lesson06_translation.csv"
BINDINGS = ROOT / "backend" / "lesson06_translation_bindings.jsonl"
RECEIPT = ROOT / "build" / "LESSON06_TRANSLATION_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
TERMINOLOGY_QA = ROOT / "working" / "lesson06_terminology_qa.md"
SOURCE_FINDINGS = ROOT / "working" / "lesson06_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson06_math_audit.md"
ASSET_CLOSURE = ROOT / "working" / "lesson06_asset_closure.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON06_NORMALIZATION_RECEIPT.json"
SCRIPT = ROOT / "scripts" / "merge_lesson06_translations.py"
PARTS = {
    "a": ROOT / "working" / "lesson06_translation_part_a.json",
    "b": ROOT / "working" / "lesson06_translation_part_b.json",
    "c": ROOT / "working" / "lesson06_translation_part_c.json",
}
NOTES = {
    name: ROOT / "working" / f"lesson06_translation_part_{name}_notes.md"
    for name in PARTS
}
FIELDS = (
    "segment_id",
    "document_id",
    "component_id",
    "section_id",
    "source_sha256",
    "source_text",
    "target_text",
    "status",
)
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
DOCUMENT_ID = "O006-PSU-007"
COMPONENT_ID = "Lesson06"
SEGMENT_COUNT = 176
GLOSSARY_BYTES = 9_305
GLOSSARY_SHA256 = "01e2a24359d82a32973c6bbd291dba661fac9d17a54111c37d8df64e12ccea3d"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def glossary_identity() -> dict[str, object]:
    data = GLOSSARY.read_bytes()
    if len(data) != GLOSSARY_BYTES or sha256(data) != GLOSSARY_SHA256:
        raise RuntimeError("Lesson 06 admitted glossary identity differs")
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    if len(rows) != 94 or rows[-1]["term_id"] != "O006-TERM-0094":
        raise RuntimeError("Lesson 06 admitted glossary row boundary differs")
    return {
        "path": GLOSSARY.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
        "rows": len(rows),
        "scope": "exact cumulative glossary through the ten Lesson 06 decisions",
    }


def expected_part_keys() -> dict[str, set[str]]:
    return {
        "a": {f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, 61)},
        "b": {f"{DOCUMENT_ID}-S{i:04d}" for i in range(61, 121)},
        "c": {f"{DOCUMENT_ID}-S{i:04d}" for i in range(121, 177)},
    }


def load_template() -> tuple[list[dict[str, str]], bytes]:
    data = TEMPLATE.read_bytes()
    try:
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid Lesson 06 segment CSV: {exc}") from exc
    if not rows or tuple(rows[0].keys()) != FIELDS or len(rows) != SEGMENT_COUNT:
        raise RuntimeError("Lesson 06 segment CSV header or row count differs")
    expected_ids = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, SEGMENT_COUNT + 1)]
    if [row["segment_id"] for row in rows] != expected_ids:
        raise RuntimeError("Lesson 06 segment IDs are not the admitted sequential boundary")
    if any(
        row["document_id"] != DOCUMENT_ID
        or row["component_id"] != COMPONENT_ID
        or row["target_text"]
        or row["status"] != "pending"
        for row in rows
    ):
        raise RuntimeError("Lesson 06 pending template fields differ")
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
            raise RuntimeError(f"invalid Lesson 06 translation part {name}: {exc}") from exc
        if (
            not isinstance(values, dict)
            or set(values) != expected[name]
            or list(values) != sorted(expected[name])
        ):
            raise RuntimeError(f"Lesson 06 translation part {name} has the wrong key set")
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise RuntimeError(f"Lesson 06 translation part {name} has an empty target")
        if set(merged).intersection(values):
            raise RuntimeError("Lesson 06 translation partitions overlap")
        merged.update(values)
        evidence.append(
            {
                "part": name,
                "range": [min(expected[name]), max(expected[name])],
                "segments": len(values),
                **identity(PARTS[name]),
                "notes": identity(NOTES[name]),
            }
        )
    return merged, evidence


def boundary(text: str) -> tuple[str, str]:
    leading = re.match(r"^\s*", text)
    trailing = re.search(r"\s*$", text)
    assert leading is not None and trailing is not None
    return leading.group(0), trailing.group(0)


def compute() -> dict[str, bytes]:
    rows, template_data = load_template()
    translations, part_evidence = load_parts()
    if set(translations) != {row["segment_id"] for row in rows}:
        raise RuntimeError("Lesson 06 translation parts do not cover all segments")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    binding_rows: list[dict[str, object]] = []
    translated_text: list[str] = []
    identical: list[str] = []
    for ordinal, row in enumerate(rows, start=1):
        source = row["source_text"]
        raw_target = translations[row["segment_id"]]
        leading, trailing = boundary(source)
        target = leading + raw_target.strip() + trailing
        if boundary(target) != (leading, trailing):
            raise RuntimeError(f"Lesson 06 boundary whitespace differs: {row['segment_id']}")
        if not target.strip() or "\ufffd" in target:
            raise RuntimeError(f"invalid Lesson 06 target: {row['segment_id']}")
        if source == target:
            identical.append(row["segment_id"])
        complete = dict(row)
        complete["target_text"] = target
        complete["status"] = "translated"
        writer.writerow(complete)
        translated_text.append(target)
        binding_rows.append(
            {
                "schema": "o006.stat415.translation-binding.v1",
                "segment_id": row["segment_id"],
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
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
        "selang kepercayaan",
        "koefisien kepercayaan",
        "tingkat kepercayaan",
        "pendugaan selang",
        "besaran pivot",
        "nilai kritis",
        "fungsi pembangkit momen",
        "selang-z",
        "galat baku",
        "distribusi khi-kuadrat",
        "derajat kebebasan",
    )
    missing = [term for term in required_terms if term not in joined]
    if missing:
        raise RuntimeError(f"required Lesson 06 terminology absent: {missing}")
    forbidden = (
        "interval kepercayaan",
        "interval konfidensi",
        "kuantitas pivotal",
        "standard error",
        "confidence interval",
    )
    present = [term for term in forbidden if term in joined]
    if present:
        raise RuntimeError(f"visible English/superseded Lesson 06 terminology present: {present}")

    csv_payload = output.getvalue().encode("utf-8")
    bindings_payload = canonical_jsonl(binding_rows)
    receipt = {
        "schema": "o006.stat415.lesson06-translation.v1",
        "status": "complete",
        "document": COMPONENT_ID,
        "document_id": DOCUMENT_ID,
        "segment_count": len(binding_rows),
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "merge_script": identity(SCRIPT),
        "boundary_whitespace_rule": (
            "exact source-node leading/trailing whitespace wrapped around translated prose core"
        ),
        "identical_segments": identical,
        "terminology_rule": "cumulative component glossary through O006-TERM-0094",
        "template": {
            "path": TEMPLATE.relative_to(ROOT).as_posix(),
            "bytes": len(template_data),
            "sha256": sha256(template_data),
        },
        "parts": part_evidence,
        "terminology_inputs": [glossary_identity(), identity(TERMINOLOGY_QA)],
        "source_findings": identity(SOURCE_FINDINGS),
        "independent_math_audit": identity(MATH_AUDIT),
        "asset_inputs": [identity(ASSET_CLOSURE), identity(NORMALIZATION_RECEIPT)],
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
                raise RuntimeError(f"Lesson 06 translation output differs: {relative}")
        state = "verified"
    receipt_payload = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(
        json.dumps(
            {
                "mode": state,
                "segments": SEGMENT_COUNT,
                "receipt_sha256": sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
