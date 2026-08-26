#!/usr/bin/env python3
"""Restore Lesson 10 batch A's frozen source fields and boundary whitespace."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "working" / "lesson10_segments.csv"
BATCH = ROOT / "working" / "lesson10_translation_batch_A.csv"
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
EXPECTED_INPUT_BYTES = 52_661
EXPECTED_INPUT_SHA256 = "d4e6ff166d30273e96c6eaf6eed3da21bc6bad48ed5c6595c49bf6659174ef34"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_rows(path: Path) -> tuple[list[dict[str, str]], bytes]:
    payload = path.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        raise RuntimeError(f"noncanonical CSV bytes: {path.relative_to(ROOT)}")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8")))
    rows = list(reader)
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise RuntimeError(f"unexpected CSV schema: {path.relative_to(ROOT)}")
    return rows, payload


def boundary(text: str) -> tuple[str, str]:
    leading = text[: len(text) - len(text.lstrip())]
    trailing = text[len(text.rstrip()) :]
    return leading, trailing


def main() -> None:
    template_rows, _ = read_rows(TEMPLATE)
    batch_rows, input_payload = read_rows(BATCH)
    if len(input_payload) != EXPECTED_INPUT_BYTES or sha256(input_payload) != EXPECTED_INPUT_SHA256:
        raise RuntimeError("Lesson 10 batch A input identity differs")
    if len(template_rows) != 540 or len(batch_rows) != 176:
        raise RuntimeError("Lesson 10 batch A row boundary differs")
    template = {row["segment_id"]: row for row in template_rows}
    expected_ids = [f"O006-PSU-011-S{i:04d}" for i in range(1, 177)]
    if [row["segment_id"] for row in batch_rows] != expected_ids:
        raise RuntimeError("Lesson 10 batch A sequence differs")

    source_repairs = 0
    boundary_repairs = 0
    for row in batch_rows:
        frozen = template[row["segment_id"]]
        if any(row[field] != frozen[field] for field in SOURCE_FIELDS):
            source_repairs += 1
            for field in SOURCE_FIELDS:
                row[field] = frozen[field]
        source_leading, source_trailing = boundary(frozen["source_text"])
        target_leading, target_trailing = boundary(row["target_text"])
        if (target_leading, target_trailing) != (source_leading, source_trailing):
            boundary_repairs += 1
            row["target_text"] = source_leading + row["target_text"].strip() + source_trailing
        if row["status"] != "translated" or not row["target_text"].strip():
            raise RuntimeError(f"invalid target row: {row['segment_id']}")
    if source_repairs != 32 or boundary_repairs != 33:
        raise RuntimeError(
            f"unexpected repair census: source={source_repairs}, boundary={boundary_repairs}"
        )

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(batch_rows)
    payload = output.getvalue().encode("utf-8")
    with tempfile.NamedTemporaryFile(
        dir=BATCH.parent, prefix=BATCH.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(BATCH)
    print(
        json.dumps(
            {
                "status": "canonicalized",
                "rows": len(batch_rows),
                "source_field_repairs": source_repairs,
                "boundary_whitespace_repairs": boundary_repairs,
                "bytes": len(payload),
                "sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
