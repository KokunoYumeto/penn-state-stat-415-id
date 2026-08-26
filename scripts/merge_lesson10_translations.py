#!/usr/bin/env python3
"""Merge four bounded Lesson 10 translation CSV batches deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "working" / "lesson10_segments.csv"
TARGET = ROOT / "source" / "id-ID" / "lesson10_translation.csv"
BINDINGS = ROOT / "backend" / "lesson10_translation_bindings.jsonl"
RECEIPT = ROOT / "build" / "LESSON10_TRANSLATION_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
TERMINOLOGY_QA = ROOT / "working" / "lesson10_terminology_qa.md"
SOURCE_FINDINGS = ROOT / "working" / "lesson10_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson10_math_audit.md"
ASSET_CLOSURE = ROOT / "working" / "lesson10_asset_closure.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON10_NORMALIZATION_RECEIPT.json"
SCRIPT = ROOT / "scripts" / "merge_lesson10_translations.py"
PARTS = {
    "A": ROOT / "working" / "lesson10_translation_batch_A.csv",
    "B": ROOT / "working" / "lesson10_translation_batch_B.csv",
    "C": ROOT / "working" / "lesson10_translation_batch_C.csv",
    "D": ROOT / "working" / "lesson10_translation_batch_D.csv",
}
PART_RANGES = {
    "A": (1, 176),
    "B": (177, 305),
    "C": (306, 427),
    "D": (428, 540),
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
SOURCE_FIELDS = FIELDS[:6]
DOCUMENT_ID = "O006-PSU-011"
COMPONENT_ID = "Lesson10"
SEGMENT_COUNT = 540
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
GLOSSARY_BYTES = 15_519
GLOSSARY_SHA256 = "68e65dbf862ed9e1c1f1d6e5fca857f2112fbb08dc4f9fa9ba86419992425a67"
GLOSSARY_ROWS = 150
GLOSSARY_LAST_TERM_ID = "O006-TERM-0150"
REQUIRED_TERMS = (
    "fungsi kuasa",
    "ukuran sampel",
    "uji wald",
    "tingkat signifikansi",
    "nilai-p",
    "galat tipe i",
    "galat tipe ii",
    "informasi fisher",
)
FORBIDDEN_TERMS = (
    "power function",
    "sample size calculation",
    "approximate wald test",
    "null hypothesis",
    "alternative hypothesis",
    "type i error",
    "type ii error",
    "significance level",
    "p-value",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


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


def load_csv(path: Path, label: str) -> tuple[list[dict[str, str]], bytes]:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
        raise RuntimeError(f"{label} is not canonical UTF-8/LF with a final newline")
    try:
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if rows and tuple(rows[0]) != FIELDS:
        raise RuntimeError(f"{label} has the wrong schema")
    return rows, data


def load_template() -> tuple[list[dict[str, str]], bytes]:
    rows, data = load_csv(TEMPLATE, "Lesson 10 segment template")
    expected = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, SEGMENT_COUNT + 1)]
    if len(rows) != SEGMENT_COUNT or [row["segment_id"] for row in rows] != expected:
        raise RuntimeError("Lesson 10 template is not the exact sequential boundary")
    for row in rows:
        if (
            row["document_id"] != DOCUMENT_ID
            or row["component_id"] != COMPONENT_ID
            or row["target_text"]
            or row["status"] != "pending"
            or sha256(row["source_text"].encode("utf-8")) != row["source_sha256"]
        ):
            raise RuntimeError(f"Lesson 10 pending template differs: {row['segment_id']}")
    return rows, data


def glossary_identity() -> dict[str, object]:
    data = GLOSSARY.read_bytes()
    if len(data) < GLOSSARY_BYTES or sha256(data[:GLOSSARY_BYTES]) != GLOSSARY_SHA256:
        raise RuntimeError("Lesson 10 admitted glossary prefix differs")
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    if len(rows) < GLOSSARY_ROWS or rows[GLOSSARY_ROWS - 1]["term_id"] != GLOSSARY_LAST_TERM_ID:
        raise RuntimeError("Lesson 10 admitted glossary row boundary differs")
    return {
        "path": GLOSSARY.relative_to(ROOT).as_posix(),
        "bytes": GLOSSARY_BYTES,
        "sha256": GLOSSARY_SHA256,
        "rows": GLOSSARY_ROWS,
        "scope": "cumulative component glossary through the eight Lesson 10 decisions",
    }


def load_parts(template: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    by_id = {row["segment_id"]: row for row in template}
    merged: list[dict[str, str]] = []
    evidence: list[dict[str, object]] = []
    seen: set[str] = set()
    for name in ("A", "B", "C", "D"):
        rows, data = load_csv(PARTS[name], f"Lesson 10 translation batch {name}")
        lo, hi = PART_RANGES[name]
        expected = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(lo, hi + 1)]
        if [row["segment_id"] for row in rows] != expected:
            raise RuntimeError(f"Lesson 10 batch {name} has the wrong ordered range")
        for row in rows:
            source = by_id[row["segment_id"]]
            if any(row[field] != source[field] for field in SOURCE_FIELDS):
                raise RuntimeError(f"Lesson 10 batch {name} changed a source field: {row['segment_id']}")
            if (
                row["status"] != "translated"
                or not row["target_text"].strip()
                or "\ufffd" in row["target_text"]
                or row["segment_id"] in seen
            ):
                raise RuntimeError(f"Lesson 10 batch {name} has an invalid target: {row['segment_id']}")
            source_leading = source["source_text"][: len(source["source_text"]) - len(source["source_text"].lstrip())]
            source_trailing = source["source_text"][len(source["source_text"].rstrip()) :]
            target = row["target_text"]
            target_leading = target[: len(target) - len(target.lstrip())]
            target_trailing = target[len(target.rstrip()) :]
            if (target_leading, target_trailing) != (source_leading, source_trailing):
                raise RuntimeError(f"Lesson 10 batch {name} changed boundary whitespace: {row['segment_id']}")
            seen.add(row["segment_id"])
            merged.append(dict(row))
        evidence.append(
            {
                "batch": name,
                "range": [expected[0], expected[-1]],
                "segments": len(rows),
                "path": PARTS[name].relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    expected_all = [row["segment_id"] for row in template]
    if [row["segment_id"] for row in merged] != expected_all:
        raise RuntimeError("Lesson 10 batches do not form one exact contiguous ledger")
    return merged, evidence


def compute() -> dict[str, bytes]:
    template, template_data = load_template()
    rows, batch_evidence = load_parts(template)
    joined = "\n".join(row["target_text"] for row in rows).casefold()
    missing = [term for term in REQUIRED_TERMS if term not in joined]
    if missing:
        raise RuntimeError(f"required Lesson 10 terminology absent: {missing}")
    forbidden = [term for term in FORBIDDEN_TERMS if term in joined]
    if forbidden:
        raise RuntimeError(f"visible English Lesson 10 terminology remains: {forbidden}")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_payload = output.getvalue().encode("utf-8")
    bindings: list[dict[str, object]] = []
    identical: list[str] = []
    for ordinal, row in enumerate(rows, start=1):
        if row["source_text"] == row["target_text"]:
            identical.append(row["segment_id"])
        bindings.append(
            {
                "schema": "o006.stat415.translation-binding.v1",
                "segment_id": row["segment_id"],
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "section_id": row["section_id"] or None,
                "ordinal": ordinal,
                "locale": "id-ID",
                "source_sha256": row["source_sha256"],
                "target_sha256": sha256(row["target_text"].encode("utf-8")),
                "status": "translated",
            }
        )
    bindings_payload = canonical_jsonl(bindings)
    receipt = {
        "schema": "o006.stat415.lesson10-translation.v1",
        "status": "complete",
        "document": COMPONENT_ID,
        "document_id": DOCUMENT_ID,
        "segment_count": SEGMENT_COUNT,
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "merge_script": identity(SCRIPT),
        "template": {
            "path": TEMPLATE.relative_to(ROOT).as_posix(),
            "bytes": len(template_data),
            "sha256": sha256(template_data),
        },
        "batches": batch_evidence,
        "identical_segments": identical,
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
                raise RuntimeError(f"Lesson 10 translation output differs: {relative}")
        state = "verified"
    receipt = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(
        json.dumps(
            {
                "mode": state,
                "segments": SEGMENT_COUNT,
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
