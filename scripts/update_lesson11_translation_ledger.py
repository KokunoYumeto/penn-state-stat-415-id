#!/usr/bin/env python3
"""Append the verified Lesson 11 row to the exact translation-ledger prefix.

The helper is deliberately idempotent.  ``--check-only`` proves that every
Lesson 11 input is internally consistent and reports the would-be ledger
identity without writing.  ``--write`` performs one atomic append, while an
already exact 13-row ledger is accepted as a verified no-op.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "00_control" / "TRANSLATION_LEDGER.csv"
BUILD = ROOT / "build" / "THROUGH_LESSON11_BUILD_RECEIPT.json"
NORMALIZATION = ROOT / "build" / "LESSON11_NORMALIZATION_RECEIPT.json"
TRANSLATION = ROOT / "build" / "LESSON11_TRANSLATION_RECEIPT.json"
QA_RELATIVE = "build/THROUGH_LESSON11_QA_RECEIPT.json"
TARGET_RELATIVE = "source/id-ID/Lesson11.html"

EXPECTED_PREFIX_ROWS = 12
EXPECTED_PREFIX_BYTES = 5_016
EXPECTED_PREFIX_SHA256 = "47de483fbd7e007609a60a4a9490e6f4542c05458568ab2b3aee9bf69f653d5b"
EXPECTED_DOCUMENT_IDS = [f"O006-PSU-{ordinal:03d}" for ordinal in range(12)]
EXPECTED_TARGET_PATHS = [
    "source/id-ID/index.html",
    *[f"source/id-ID/Lesson{ordinal:02d}.html" for ordinal in range(12)],
]
FIELDS = (
    "document_id", "component_id", "source_path", "source_bytes", "source_sha256",
    "normalized_path", "normalized_bytes", "normalized_sha256", "target_path",
    "target_bytes", "target_sha256", "segments", "structures", "math_nodes", "status",
    "qa_receipt",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    payload = path.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload:
        fail(f"non-canonical UTF-8/LF JSON: {path}")
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        fail(f"expected a JSON object: {path}")
    return payload, value


def verify_file_spec(spec: dict[str, Any], expected_relative: str | None = None) -> bytes:
    relative = str(spec.get("path"))
    if expected_relative is not None and relative != expected_relative:
        fail(f"artifact path differs: {relative!r} != {expected_relative!r}")
    path = ROOT / relative
    payload = path.read_bytes()
    if int(spec.get("bytes", -1)) != len(payload) or str(spec.get("sha256")) != sha256(payload):
        fail(f"artifact identity differs: {relative}")
    return payload


def verify_receipt_reference(
    spec: dict[str, Any], expected_relative: str, expected_payload: bytes
) -> None:
    if (
        str(spec.get("path")) != expected_relative
        or int(spec.get("bytes", -1)) != len(expected_payload)
        or str(spec.get("sha256")) != sha256(expected_payload)
    ):
        fail(f"receipt reference differs: {expected_relative}")


def load_prefix(current_payload: bytes) -> tuple[bytes, list[dict[str, str]]]:
    if len(current_payload) < EXPECTED_PREFIX_BYTES:
        fail("translation ledger is shorter than the admitted 12-row prefix")
    prefix = current_payload[:EXPECTED_PREFIX_BYTES]
    if len(prefix) != EXPECTED_PREFIX_BYTES or sha256(prefix) != EXPECTED_PREFIX_SHA256:
        fail("translation ledger does not preserve the exact admitted 12-row byte prefix")
    if prefix.startswith(b"\xef\xbb\xbf") or b"\r" in prefix or not prefix.endswith(b"\n"):
        fail("translation-ledger prefix is not canonical UTF-8/LF")
    rows = list(csv.DictReader(io.StringIO(prefix.decode("utf-8"), newline="")))
    if list(rows[0].keys()) != list(FIELDS):
        fail("translation-ledger header differs")
    if len(rows) != EXPECTED_PREFIX_ROWS:
        fail("translation-ledger prefix row count differs")
    if [row["document_id"] for row in rows] != EXPECTED_DOCUMENT_IDS:
        fail("translation-ledger prefix document order differs")
    return prefix, rows


def lesson11_row() -> dict[str, str]:
    normalization_payload, normalization = load_json(NORMALIZATION)
    translation_payload, translation = load_json(TRANSLATION)
    _, build = load_json(BUILD)

    if normalization.get("schema") != "o006.stat415.lesson11-normalization.v1":
        fail("Lesson 11 normalization schema differs")
    document = normalization.get("document")
    counts = normalization.get("counts")
    outputs = normalization.get("outputs")
    if not isinstance(document, dict) or not isinstance(counts, dict) or not isinstance(outputs, dict):
        fail("Lesson 11 normalization surfaces are incomplete")
    if document.get("document_id") != "O006-PSU-012" or document.get("component_id") != "Lesson11":
        fail("Lesson 11 normalization document identity differs")
    if (
        int(counts.get("translation_segments", -1)) != 354
        or int(counts.get("structural_units", -1)) != 264
        or int(counts.get("math_nodes", -1)) != 264
    ):
        fail("Lesson 11 normalization counts differ")

    source_relative = str(document.get("source_path"))
    source_payload = (ROOT / source_relative).read_bytes()
    if (
        int(document.get("source_bytes", -1)) != len(source_payload)
        or str(document.get("source_sha256")) != sha256(source_payload)
    ):
        fail("Lesson 11 authority identity differs")

    normalized_relative = str(document.get("normalized_path"))
    normalized_spec = outputs.get(normalized_relative)
    if not isinstance(normalized_spec, dict):
        fail("Lesson 11 normalized output is absent from its receipt")
    normalized_payload = verify_file_spec(normalized_spec, normalized_relative)
    if (
        int(document.get("normalized_bytes", -1)) != len(normalized_payload)
        or str(document.get("normalized_sha256")) != sha256(normalized_payload)
    ):
        fail("Lesson 11 normalized document identity differs")

    if (
        translation.get("schema") != "o006.stat415.lesson11-translation.v1"
        or translation.get("status") != "complete"
        or translation.get("document_id") != "O006-PSU-012"
        or int(translation.get("segment_count", -1)) != 354
        or int(translation.get("translated_status_count", -1)) != 354
    ):
        fail("Lesson 11 translation receipt is not complete")
    bindings = translation.get("bindings")
    translation_csv = translation.get("translation_csv")
    if not isinstance(bindings, dict) or not isinstance(translation_csv, dict):
        fail("Lesson 11 translation outputs are absent")
    verify_file_spec(bindings, "backend/lesson11_translation_bindings.jsonl")
    verify_file_spec(translation_csv, "source/id-ID/lesson11_translation.csv")
    normalization_inputs = translation.get("normalization_inputs")
    if not isinstance(normalization_inputs, list):
        fail("Lesson 11 translation normalization inputs are absent")
    normalization_reference = next(
        (item for item in normalization_inputs if item.get("path") == "build/LESSON11_NORMALIZATION_RECEIPT.json"),
        None,
    )
    if not isinstance(normalization_reference, dict):
        fail("Lesson 11 translation does not name the normalization receipt")
    verify_receipt_reference(
        normalization_reference, "build/LESSON11_NORMALIZATION_RECEIPT.json", normalization_payload
    )

    if build.get("schema") != "o006.stat415.through-lesson11-build.v1" or build.get("status") != "built":
        fail("through-Lesson 11 build receipt is not complete")
    inputs = build.get("inputs")
    coverage = build.get("coverage")
    targets = build.get("target_documents")
    if not isinstance(inputs, dict) or not isinstance(coverage, dict) or not isinstance(targets, list):
        fail("through-Lesson 11 build surfaces are incomplete")
    if int(coverage.get("complete_count", -1)) != 13 or coverage.get("next_document") != "Lesson12":
        fail("through-Lesson 11 build coverage differs")
    if [str(item.get("path")) for item in targets] != EXPECTED_TARGET_PATHS:
        fail("through-Lesson 11 target-document sequence differs")
    for key, relative, payload in (
        ("normalization", "build/LESSON11_NORMALIZATION_RECEIPT.json", normalization_payload),
        ("translation", "build/LESSON11_TRANSLATION_RECEIPT.json", translation_payload),
    ):
        reference = inputs.get(key)
        if not isinstance(reference, dict):
            fail(f"through-Lesson 11 build lacks {key} input")
        verify_receipt_reference(reference, relative, payload)

    target_by_path = {str(item.get("path")): item for item in targets}
    target_spec = target_by_path[TARGET_RELATIVE]
    target_payload = verify_file_spec(target_spec, TARGET_RELATIVE)

    return {
        "document_id": "O006-PSU-012",
        "component_id": "Lesson11",
        "source_path": source_relative,
        "source_bytes": str(len(source_payload)),
        "source_sha256": sha256(source_payload),
        "normalized_path": normalized_relative,
        "normalized_bytes": str(len(normalized_payload)),
        "normalized_sha256": sha256(normalized_payload),
        "target_path": TARGET_RELATIVE,
        "target_bytes": str(len(target_payload)),
        "target_sha256": sha256(target_payload),
        "segments": "354",
        "structures": "264",
        "math_nodes": "264",
        "status": "complete",
        "qa_receipt": QA_RELATIVE,
    }


def serialize_row(row: dict[str, str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writerow({field: row[field] for field in FIELDS})
    return stream.getvalue().encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    current = LEDGER.read_bytes()
    prefix, _ = load_prefix(current)
    expected = prefix + serialize_row(lesson11_row())
    if current not in (prefix, expected):
        fail("translation ledger is neither the exact 12-row prefix nor the exact Lesson 11 result")

    was_complete = current == expected
    if args.write and not was_complete:
        atomic_write(LEDGER, expected)
        if LEDGER.read_bytes() != expected:
            fail("translation ledger failed post-write byte verification")

    print(json.dumps({
        "bytes": len(expected),
        "current_rows": 13 if was_complete else 12,
        "expected_rows": 13,
        "mode": "write" if args.write else "check-only",
        "sha256": sha256(expected),
        "status": "verified" if was_complete else ("updated" if args.write else "ready"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
