#!/usr/bin/env python3
"""Append the exact Lesson 11 correction suffix to the adverse ledger.

The first 198 records are pinned byte-for-byte.  The only admitted suffix is
the canonical correction sequence O006-PSU-ADV-0199 through 0218, paired in
order with L11-D001 through L11-D020 from the verified cumulative build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
CUMULATIVE = ROOT / "backend" / "through_lesson11_corrections.jsonl"
BUILD = ROOT / "build" / "THROUGH_LESSON11_BUILD_RECEIPT.json"
NORMALIZATION = ROOT / "build" / "LESSON11_NORMALIZATION_RECEIPT.json"
TRANSLATION = ROOT / "build" / "LESSON11_TRANSLATION_RECEIPT.json"

EXPECTED_PREFIX_ROWS = 198
EXPECTED_PREFIX_BYTES = 302_856
EXPECTED_PREFIX_SHA256 = "6ae4f60460fcc97c3e4b92ad6246e7bb3afdb5f4bfc3622aebc73e31cea7c3da"
EXPECTED_ALL_ROWS = 218
EXPECTED_PREFIX_IDS = [f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(1, 199)]
EXPECTED_SUFFIX_IDS = [f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(199, 219)]
EXPECTED_DEFECT_IDS = [f"L11-D{ordinal:03d}" for ordinal in range(1, 21)]


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


def parse_canonical_jsonl(payload: bytes, expected_rows: int) -> tuple[list[bytes], list[dict[str, Any]]]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        fail("correction backend is not canonical UTF-8/LF JSONL")
    lines = payload.splitlines(keepends=True)
    if len(lines) != expected_rows or any(not line.endswith(b"\n") for line in lines):
        fail("correction backend line count or termination differs")
    rows: list[dict[str, Any]] = []
    for ordinal, line in enumerate(lines, start=1):
        row = json.loads(line.decode("utf-8"))
        if not isinstance(row, dict):
            fail(f"correction record {ordinal} is not an object")
        canonical = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        if line != canonical:
            fail(f"correction record {ordinal} is not canonical JSONL")
        rows.append(row)
    return lines, rows


def exact_prefix(current: bytes) -> bytes:
    if len(current) < EXPECTED_PREFIX_BYTES:
        fail("adverse ledger is shorter than the admitted 198-row prefix")
    prefix = current[:EXPECTED_PREFIX_BYTES]
    if len(prefix) != EXPECTED_PREFIX_BYTES or sha256(prefix) != EXPECTED_PREFIX_SHA256:
        fail("adverse ledger does not preserve the exact admitted 198-row byte prefix")
    _, rows = parse_canonical_jsonl(prefix, EXPECTED_PREFIX_ROWS)
    if [row.get("correction_id") for row in rows] != EXPECTED_PREFIX_IDS:
        fail("adverse-ledger prefix correction sequence differs")
    return prefix


def expected_payload(prefix: bytes) -> bytes:
    normalization_payload, normalization = load_json(NORMALIZATION)
    translation_payload, translation = load_json(TRANSLATION)
    build_payload, build = load_json(BUILD)

    if normalization.get("schema") != "o006.stat415.lesson11-normalization.v1":
        fail("Lesson 11 normalization schema differs")
    if normalization.get("source_defect_ids") != EXPECTED_DEFECT_IDS:
        fail("Lesson 11 normalization defect sequence differs")
    if int(normalization.get("source_defect_count", -1)) != 20:
        fail("Lesson 11 normalization defect count differs")
    if (
        translation.get("schema") != "o006.stat415.lesson11-translation.v1"
        or translation.get("status") != "complete"
        or translation.get("document_id") != "O006-PSU-012"
        or int(translation.get("segment_count", -1)) != 354
        or int(translation.get("translated_status_count", -1)) != 354
    ):
        fail("Lesson 11 translation receipt is not complete")
    if build.get("schema") != "o006.stat415.through-lesson11-build.v1" or build.get("status") != "built":
        fail("through-Lesson 11 build receipt is not complete")

    inputs = build.get("inputs")
    corrections = build.get("corrections")
    if not isinstance(inputs, dict) or not isinstance(corrections, dict):
        fail("through-Lesson 11 build inputs or corrections are absent")
    for key, relative, payload in (
        ("normalization", "build/LESSON11_NORMALIZATION_RECEIPT.json", normalization_payload),
        ("translation", "build/LESSON11_TRANSLATION_RECEIPT.json", translation_payload),
    ):
        reference = inputs.get(key)
        if not isinstance(reference, dict):
            fail(f"through-Lesson 11 build lacks {key} input")
        verify_receipt_reference(reference, relative, payload)

    cumulative_payload = CUMULATIVE.read_bytes()
    if (
        str(corrections.get("path")) != "backend/through_lesson11_corrections.jsonl"
        or int(corrections.get("bytes", -1)) != len(cumulative_payload)
        or str(corrections.get("sha256")) != sha256(cumulative_payload)
        or int(corrections.get("count", -1)) != EXPECTED_ALL_ROWS
        or int(corrections.get("through_lesson10_count", -1)) != EXPECTED_PREFIX_ROWS
        or int(corrections.get("lesson11_count", -1)) != 20
    ):
        fail("through-Lesson 11 correction receipt differs")

    lines, rows = parse_canonical_jsonl(cumulative_payload, EXPECTED_ALL_ROWS)
    # The adverse ledger's first 170 records use the older curated control
    # schema, whereas the cumulative build backend uses rendering-surface
    # records.  Lesson 10 appended its raw build records at rows 171–198.
    # Therefore pin the whole ledger prefix by its own identity, validate the
    # shared Lesson 10 suffix semantically, and append only fresh Lesson 11
    # backend rows; the two distinct schemas must not be conflated.
    _, prefix_rows = parse_canonical_jsonl(prefix, EXPECTED_PREFIX_ROWS)
    if [row.get("correction_id") for row in rows[:EXPECTED_PREFIX_ROWS]] != EXPECTED_PREFIX_IDS:
        fail("cumulative correction backend prefix ID sequence differs")
    if prefix_rows[170:198] != rows[170:198]:
        fail("adverse ledger does not preserve the exact Lesson 10 backend suffix")
    suffix = rows[EXPECTED_PREFIX_ROWS:]
    if [row.get("correction_id") for row in suffix] != EXPECTED_SUFFIX_IDS:
        fail("Lesson 11 correction-ID suffix differs")
    if [row.get("source_defect_id") for row in suffix] != EXPECTED_DEFECT_IDS:
        fail("Lesson 11 source-defect pairing differs")
    if any(row.get("status") != "applied-target-only" for row in suffix):
        fail("Lesson 11 correction status differs")

    # The parsed build object is intentionally tied to its exact on-disk bytes.
    if len(build_payload) == 0:
        fail("empty through-Lesson 11 build receipt")
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
        fail("adverse ledger is neither the exact 198-row prefix nor the exact Lesson 11 result")

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
