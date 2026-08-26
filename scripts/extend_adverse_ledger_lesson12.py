#!/usr/bin/env python3
"""Append the exact Lesson 12 correction suffix to the adverse ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
CUMULATIVE = ROOT / "backend" / "through_lesson12_corrections.jsonl"
TARGET_CORRECTIONS = ROOT / "backend" / "lesson12_target_corrections.jsonl"
BUILD = ROOT / "build" / "THROUGH_LESSON12_BUILD_RECEIPT.json"
NORMALIZATION = ROOT / "build" / "LESSON12_NORMALIZATION_RECEIPT.json"
TRANSLATION = ROOT / "build" / "LESSON12_TRANSLATION_RECEIPT.json"
MATERIALIZATION = ROOT / "build" / "LESSON12_MATERIALIZATION_RECEIPT.json"

EXPECTED_PREFIX_ROWS = 218
EXPECTED_PREFIX_BYTES = 315_281
EXPECTED_PREFIX_SHA256 = "376515c286f48ee5f648097cfa093b2b305e7dec9c67e6ca986300815fc2c17d"
EXPECTED_ALL_ROWS = 242
EXPECTED_PREFIX_IDS = [f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(1, 219)]
EXPECTED_SUFFIX_IDS = [f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(219, 243)]
EXPECTED_DEFECT_IDS = [f"L12-D{ordinal:03d}" for ordinal in range(1, 25)]


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


def verify_receipt_reference(
    spec: dict[str, Any], expected_relative: str, expected_payload: bytes
) -> None:
    if (
        str(spec.get("path")) != expected_relative
        or int(spec.get("bytes", -1)) != len(expected_payload)
        or str(spec.get("sha256")) != sha256(expected_payload)
    ):
        fail(f"receipt reference differs: {expected_relative}")


def parse_canonical_jsonl(
    payload: bytes, expected_rows: int, label: str
) -> tuple[list[bytes], list[dict[str, Any]]]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        fail(f"{label} is not canonical UTF-8/LF JSONL")
    lines = payload.splitlines(keepends=True)
    if len(lines) != expected_rows or any(not line.endswith(b"\n") for line in lines):
        fail(f"{label} line count or termination differs")
    rows: list[dict[str, Any]] = []
    for ordinal, line in enumerate(lines, start=1):
        row = json.loads(line.decode("utf-8"))
        if not isinstance(row, dict):
            fail(f"{label} record {ordinal} is not an object")
        canonical = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        if line != canonical:
            fail(f"{label} record {ordinal} is not canonical JSONL")
        rows.append(row)
    return lines, rows


def exact_prefix(current: bytes) -> bytes:
    if len(current) < EXPECTED_PREFIX_BYTES:
        fail("adverse ledger is shorter than the admitted 218-row prefix")
    prefix = current[:EXPECTED_PREFIX_BYTES]
    if len(prefix) != EXPECTED_PREFIX_BYTES or sha256(prefix) != EXPECTED_PREFIX_SHA256:
        fail("adverse ledger does not preserve the exact admitted 218-row byte prefix")
    _, rows = parse_canonical_jsonl(prefix, EXPECTED_PREFIX_ROWS, "adverse-ledger prefix")
    if [row.get("correction_id") for row in rows] != EXPECTED_PREFIX_IDS:
        fail("adverse-ledger prefix correction sequence differs")
    return prefix


def expected_payload(prefix: bytes) -> bytes:
    normalization_payload, normalization = load_json(NORMALIZATION)
    translation_payload, translation = load_json(TRANSLATION)
    materialization_payload, materialization = load_json(MATERIALIZATION)
    _, build = load_json(BUILD)
    if (
        normalization.get("schema") != "o006.stat415.lesson12-normalization.v1"
        or normalization.get("source_defect_count") != 24
        or normalization.get("source_defect_ids") != EXPECTED_DEFECT_IDS
    ):
        fail("Lesson12 normalization defect boundary differs")
    if (
        translation.get("schema") != "o006.stat415.lesson12-translation.v1"
        or translation.get("status") != "complete"
        or translation.get("document_id") != "O006-PSU-013"
        or translation.get("segment_count") != 580
        or translation.get("translated_status_count") != 580
    ):
        fail("Lesson12 translation receipt is not complete")
    if (
        materialization.get("schema") != "o006.stat415.lesson12-materialization.v1"
        or materialization.get("status") != "pass"
        or materialization.get("counts", {}).get("registered_target_corrections") != 24
    ):
        fail("Lesson12 materialization receipt differs")
    if build.get("schema") != "o006.stat415.through-lesson12-build.v1" or build.get("status") != "built":
        fail("through-Lesson12 build receipt is not complete")
    inputs = build.get("inputs")
    corrections = build.get("corrections")
    if not isinstance(inputs, dict) or not isinstance(corrections, dict):
        fail("through-Lesson12 build inputs or corrections are absent")
    for key, relative, payload in (
        ("normalization", "build/LESSON12_NORMALIZATION_RECEIPT.json", normalization_payload),
        ("translation", "build/LESSON12_TRANSLATION_RECEIPT.json", translation_payload),
        ("materialization", "build/LESSON12_MATERIALIZATION_RECEIPT.json", materialization_payload),
    ):
        reference = inputs.get(key)
        if not isinstance(reference, dict):
            fail(f"through-Lesson12 build lacks {key} input")
        verify_receipt_reference(reference, relative, payload)

    cumulative_payload = CUMULATIVE.read_bytes()
    if (
        corrections.get("path") != "backend/through_lesson12_corrections.jsonl"
        or corrections.get("bytes") != len(cumulative_payload)
        or corrections.get("sha256") != sha256(cumulative_payload)
        or corrections.get("count") != EXPECTED_ALL_ROWS
        or corrections.get("through_lesson11_count") != EXPECTED_PREFIX_ROWS
        or corrections.get("lesson12_count") != 24
    ):
        fail("through-Lesson12 correction receipt differs")
    lines, rows = parse_canonical_jsonl(cumulative_payload, EXPECTED_ALL_ROWS, "cumulative correction backend")
    _, prefix_rows = parse_canonical_jsonl(prefix, EXPECTED_PREFIX_ROWS, "adverse-ledger prefix")
    if [row.get("correction_id") for row in rows[:EXPECTED_PREFIX_ROWS]] != EXPECTED_PREFIX_IDS:
        fail("cumulative correction backend prefix ID sequence differs")
    # Rows 001–170 use an older curated control schema. Rows 171–218 are raw
    # cumulative rendering records and must match exactly before extending.
    if prefix_rows[170:EXPECTED_PREFIX_ROWS] != rows[170:EXPECTED_PREFIX_ROWS]:
        fail("adverse ledger does not preserve the exact shared cumulative suffix")
    suffix = rows[EXPECTED_PREFIX_ROWS:]
    if (
        [row.get("correction_id") for row in suffix] != EXPECTED_SUFFIX_IDS
        or [row.get("source_defect_id") for row in suffix] != EXPECTED_DEFECT_IDS
    ):
        fail("Lesson12 correction suffix pairing differs")
    target_payload = TARGET_CORRECTIONS.read_bytes()
    target_lines, target_rows = parse_canonical_jsonl(target_payload, 24, "Lesson12 target corrections")
    if target_rows != suffix or target_lines != lines[EXPECTED_PREFIX_ROWS:]:
        fail("Lesson12 cumulative suffix differs from the materialization correction registry")
    output_spec = materialization.get("outputs", {}).get("backend/lesson12_target_corrections.jsonl")
    if (
        not isinstance(output_spec, dict)
        or output_spec.get("bytes") != len(target_payload)
        or output_spec.get("sha256") != sha256(target_payload)
        or output_spec.get("records") != 24
    ):
        fail("Lesson12 materialization does not bind its correction registry")
    return prefix + b"".join(lines[EXPECTED_PREFIX_ROWS:])


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
    prefix = exact_prefix(current)
    expected = expected_payload(prefix)
    if current not in (prefix, expected):
        fail("adverse ledger is neither the exact 218-row prefix nor the exact Lesson12 result")
    was_complete = current == expected
    if args.write and not was_complete:
        atomic_write(LEDGER, expected)
        if LEDGER.read_bytes() != expected:
            fail("adverse ledger failed post-write byte verification")
    print(json.dumps({
        "bytes": len(expected),
        "current_rows": EXPECTED_ALL_ROWS if was_complete else EXPECTED_PREFIX_ROWS,
        "expected_rows": EXPECTED_ALL_ROWS,
        "mode": "write" if args.write else "check-only",
        "sha256": sha256(expected),
        "status": "verified" if was_complete else ("updated" if args.write else "ready"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
