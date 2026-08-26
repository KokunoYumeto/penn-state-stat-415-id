#!/usr/bin/env python3
"""Append the verified Lesson 12 row to the exact translation-ledger prefix."""

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
BUILD = ROOT / "build" / "THROUGH_LESSON12_BUILD_RECEIPT.json"
NORMALIZATION = ROOT / "build" / "LESSON12_NORMALIZATION_RECEIPT.json"
TRANSLATION = ROOT / "build" / "LESSON12_TRANSLATION_RECEIPT.json"
MATERIALIZATION = ROOT / "build" / "LESSON12_MATERIALIZATION_RECEIPT.json"
QA_RELATIVE = "build/THROUGH_LESSON12_QA_RECEIPT.json"
TARGET_RELATIVE = "source/id-ID/Lesson12.html"

EXPECTED_PREFIX_ROWS = 13
EXPECTED_PREFIX_BYTES = 5_417
EXPECTED_PREFIX_SHA256 = "d674909cce4e6ed9a144eda1808fff6634f1b0d91748df94241dfedd6a278a2f"
EXPECTED_DOCUMENT_IDS = [f"O006-PSU-{ordinal:03d}" for ordinal in range(13)]
EXPECTED_TARGET_PATHS = [
    "source/id-ID/index.html",
    *[f"source/id-ID/Lesson{ordinal:02d}.html" for ordinal in range(13)],
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


def verify_file_spec(spec: dict[str, Any], expected_relative: str) -> bytes:
    if str(spec.get("path", expected_relative)) != expected_relative:
        fail(f"artifact path differs: {spec.get('path')!r} != {expected_relative!r}")
    payload = (ROOT / expected_relative).read_bytes()
    if int(spec.get("bytes", -1)) != len(payload) or str(spec.get("sha256")) != sha256(payload):
        fail(f"artifact identity differs: {expected_relative}")
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


def load_prefix(current_payload: bytes) -> bytes:
    if len(current_payload) < EXPECTED_PREFIX_BYTES:
        fail("translation ledger is shorter than the admitted 13-row prefix")
    prefix = current_payload[:EXPECTED_PREFIX_BYTES]
    if len(prefix) != EXPECTED_PREFIX_BYTES or sha256(prefix) != EXPECTED_PREFIX_SHA256:
        fail("translation ledger does not preserve the exact admitted 13-row byte prefix")
    if prefix.startswith(b"\xef\xbb\xbf") or b"\r" in prefix or not prefix.endswith(b"\n"):
        fail("translation-ledger prefix is not canonical UTF-8/LF")
    reader = csv.DictReader(io.StringIO(prefix.decode("utf-8"), newline=""))
    rows = list(reader)
    if list(reader.fieldnames or []) != list(FIELDS) or len(rows) != EXPECTED_PREFIX_ROWS:
        fail("translation-ledger prefix schema or row count differs")
    if [row["document_id"] for row in rows] != EXPECTED_DOCUMENT_IDS:
        fail("translation-ledger prefix document order differs")
    return prefix


def lesson12_row() -> dict[str, str]:
    normalization_payload, normalization = load_json(NORMALIZATION)
    translation_payload, translation = load_json(TRANSLATION)
    materialization_payload, materialization = load_json(MATERIALIZATION)
    _, build = load_json(BUILD)
    document = normalization.get("document")
    counts = normalization.get("counts")
    outputs = normalization.get("outputs")
    if (
        normalization.get("schema") != "o006.stat415.lesson12-normalization.v1"
        or not isinstance(document, dict)
        or not isinstance(counts, dict)
        or not isinstance(outputs, dict)
        or document.get("document_id") != "O006-PSU-013"
        or document.get("component_id") != "Lesson12"
        or counts.get("translation_segments") != 580
        or counts.get("structural_units") != 846
        or counts.get("math_nodes") != 352
    ):
        fail("Lesson12 normalization boundary differs")
    source_relative = str(document.get("source_path"))
    source_payload = (ROOT / source_relative).read_bytes()
    if document.get("source_bytes") != len(source_payload) or document.get("source_sha256") != sha256(source_payload):
        fail("Lesson12 authority identity differs")
    normalized_relative = str(document.get("normalized_path"))
    normalized_spec = outputs.get(normalized_relative)
    if not isinstance(normalized_spec, dict):
        fail("Lesson12 normalized output is absent")
    normalized_payload = verify_file_spec(normalized_spec, normalized_relative)
    if (
        document.get("normalized_bytes") != len(normalized_payload)
        or document.get("normalized_sha256") != sha256(normalized_payload)
    ):
        fail("Lesson12 normalized document identity differs")
    if (
        translation.get("schema") != "o006.stat415.lesson12-translation.v1"
        or translation.get("status") != "complete"
        or translation.get("document_id") != "O006-PSU-013"
        or translation.get("segment_count") != 580
        or translation.get("translated_status_count") != 580
    ):
        fail("Lesson12 translation receipt is not complete")
    verify_file_spec(translation["bindings"], "backend/lesson12_translation_bindings.jsonl")
    verify_file_spec(translation["translation_csv"], "source/id-ID/lesson12_translation.csv")
    if (
        materialization.get("schema") != "o006.stat415.lesson12-materialization.v1"
        or materialization.get("status") != "pass"
        or materialization.get("counts", {}).get("stable_source_units") != 846
        or materialization.get("counts", {}).get("stable_source_math") != 352
        or materialization.get("counts", {}).get("registered_target_corrections") != 24
    ):
        fail("Lesson12 materialization receipt differs")
    target_spec = materialization.get("outputs", {}).get(TARGET_RELATIVE)
    if not isinstance(target_spec, dict):
        fail("Lesson12 materialization target is absent")
    target_payload = verify_file_spec(target_spec, TARGET_RELATIVE)
    if build.get("schema") != "o006.stat415.through-lesson12-build.v1" or build.get("status") != "built":
        fail("through-Lesson12 build receipt is not complete")
    inputs = build.get("inputs")
    coverage = build.get("coverage")
    targets = build.get("target_documents")
    if not isinstance(inputs, dict) or not isinstance(coverage, dict) or not isinstance(targets, list):
        fail("through-Lesson12 build surfaces are incomplete")
    if (
        coverage.get("complete_count") != 14
        or coverage.get("pending_documents") != []
        or coverage.get("next_document") is not None
        or [str(item.get("path")) for item in targets] != EXPECTED_TARGET_PATHS
    ):
        fail("through-Lesson12 build coverage or target sequence differs")
    for key, relative, payload in (
        ("normalization", "build/LESSON12_NORMALIZATION_RECEIPT.json", normalization_payload),
        ("translation", "build/LESSON12_TRANSLATION_RECEIPT.json", translation_payload),
        ("materialization", "build/LESSON12_MATERIALIZATION_RECEIPT.json", materialization_payload),
    ):
        reference = inputs.get(key)
        if not isinstance(reference, dict):
            fail(f"through-Lesson12 build lacks {key} input")
        verify_receipt_reference(reference, relative, payload)
    target_by_path = {str(item.get("path")): item for item in targets}
    build_target = target_by_path.get(TARGET_RELATIVE)
    if (
        not isinstance(build_target, dict)
        or build_target.get("bytes") != len(target_payload)
        or build_target.get("sha256") != sha256(target_payload)
    ):
        fail("through-Lesson12 build does not bind the semantic target")
    return {
        "document_id": "O006-PSU-013",
        "component_id": "Lesson12",
        "source_path": source_relative,
        "source_bytes": str(len(source_payload)),
        "source_sha256": sha256(source_payload),
        "normalized_path": normalized_relative,
        "normalized_bytes": str(len(normalized_payload)),
        "normalized_sha256": sha256(normalized_payload),
        "target_path": TARGET_RELATIVE,
        "target_bytes": str(len(target_payload)),
        "target_sha256": sha256(target_payload),
        "segments": "580",
        "structures": "846",
        "math_nodes": "352",
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
    prefix = load_prefix(current)
    expected = prefix + serialize_row(lesson12_row())
    if current not in (prefix, expected):
        fail("translation ledger is neither the exact 13-row prefix nor the exact Lesson12 result")
    was_complete = current == expected
    if args.write and not was_complete:
        atomic_write(LEDGER, expected)
        if LEDGER.read_bytes() != expected:
            fail("translation ledger failed post-write byte verification")
    print(json.dumps({
        "bytes": len(expected),
        "current_rows": 14 if was_complete else 13,
        "expected_rows": 14,
        "mode": "write" if args.write else "check-only",
        "sha256": sha256(expected),
        "status": "verified" if was_complete else ("updated" if args.write else "ready"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
