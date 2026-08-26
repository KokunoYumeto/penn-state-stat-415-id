#!/usr/bin/env python3
"""Serialize final Lesson 10 translation batches as canonical UTF-8/LF CSV."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "working" / "lesson10_segments.csv"
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
RANGES = {"A": (1, 176), "B": (177, 305), "C": (306, 427), "D": (428, 540)}


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load(path: Path) -> list[dict[str, str]]:
    payload = path.read_bytes()
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    rows = list(reader)
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise RuntimeError(f"unexpected schema: {path.relative_to(ROOT)}")
    return rows


def boundary(text: str) -> tuple[str, str]:
    return (
        text[: len(text) - len(text.lstrip())],
        text[len(text.rstrip()) :],
    )


def serialize(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def main() -> None:
    template_rows = load(TEMPLATE)
    if len(template_rows) != 540:
        raise RuntimeError("Lesson 10 frozen segment census differs")
    template = {row["segment_id"]: row for row in template_rows}
    results: list[dict[str, object]] = []
    for name, (lo, hi) in RANGES.items():
        path = ROOT / "working" / f"lesson10_translation_batch_{name}.csv"
        rows = load(path)
        expected_ids = [f"O006-PSU-011-S{i:04d}" for i in range(lo, hi + 1)]
        if [row["segment_id"] for row in rows] != expected_ids:
            raise RuntimeError(f"Lesson 10 batch {name} sequence differs")
        repaired_boundaries = 0
        for row in rows:
            frozen = template[row["segment_id"]]
            if any(row[field] != frozen[field] for field in SOURCE_FIELDS):
                raise RuntimeError(f"Lesson 10 batch {name} source differs: {row['segment_id']}")
            if row["status"] != "translated" or not row["target_text"].strip():
                raise RuntimeError(f"Lesson 10 batch {name} target differs: {row['segment_id']}")
            source_boundary = boundary(frozen["source_text"])
            if boundary(row["target_text"]) != source_boundary:
                repaired_boundaries += 1
                row["target_text"] = (
                    source_boundary[0] + row["target_text"].strip() + source_boundary[1]
                )
        payload = serialize(rows)
        atomic_write(path, payload)
        results.append(
            {
                "batch": name,
                "rows": len(rows),
                "boundary_repairs": repaired_boundaries,
                "bytes": len(payload),
                "sha256": digest(payload),
            }
        )
    print(json.dumps({"status": "canonicalized", "batches": results}, sort_keys=True))


if __name__ == "__main__":
    main()
