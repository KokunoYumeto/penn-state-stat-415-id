#!/usr/bin/env python3
"""Refresh the cumulative translation ledger from the verified Lesson 10 build."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "00_control" / "TRANSLATION_LEDGER.csv"
BUILD = ROOT / "build" / "THROUGH_LESSON10_BUILD_RECEIPT.json"
NORMALIZATION = ROOT / "build" / "LESSON10_NORMALIZATION_RECEIPT.json"
AUTHORITY = ROOT / "authority" / "upstream" / "stat415" / "Lesson10.html"
QA = "build/THROUGH_LESSON10_QA_RECEIPT.json"
FIELDS = (
    "document_id", "component_id", "source_path", "source_bytes", "source_sha256",
    "normalized_path", "normalized_bytes", "normalized_sha256", "target_path",
    "target_bytes", "target_sha256", "segments", "structures", "math_nodes", "status",
    "qa_receipt",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def atomic_write(path: Path, payload: bytes) -> None:
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def main() -> None:
    existing = list(csv.DictReader(LEDGER.open("r", encoding="utf-8", newline="")))
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    normalization = json.loads(NORMALIZATION.read_text(encoding="utf-8"))
    target_by_path = {str(row["path"]): row for row in build["target_documents"]}
    norm = normalization["outputs"]["normalized"]
    authority_payload = AUTHORITY.read_bytes()
    lesson10 = {
        "document_id": "O006-PSU-011",
        "component_id": "Lesson10",
        "source_path": "authority/upstream/stat415/Lesson10.html",
        "source_bytes": str(len(authority_payload)),
        "source_sha256": sha256(authority_payload),
        "normalized_path": str(norm["path"]),
        "normalized_bytes": str(norm["bytes"]),
        "normalized_sha256": str(norm["sha256"]),
        "target_path": "source/id-ID/Lesson10.html",
        "segments": "540",
        "structures": "625",
        "math_nodes": "369",
        "status": "complete",
        "qa_receipt": QA,
    }
    if len(existing) != 11 or [row["document_id"] for row in existing] != [f"O006-PSU-{i:03d}" for i in range(11)]:
        raise RuntimeError("expected ordered 11-row ledger prefix")
    rows: list[dict[str, str]] = []
    for row in existing:
        target = target_by_path[row["target_path"]]
        row = dict(row)
        row["target_bytes"] = str(target["bytes"])
        row["target_sha256"] = str(target["sha256"])
        row["qa_receipt"] = QA
        rows.append({field: row[field] for field in FIELDS})
    target = target_by_path[lesson10["target_path"]]
    lesson10["target_bytes"] = str(target["bytes"])
    lesson10["target_sha256"] = str(target["sha256"])
    rows.append(lesson10)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    payload = stream.getvalue().encode("utf-8")
    atomic_write(LEDGER, payload)
    print(json.dumps({"status": "updated", "rows": len(rows), "bytes": len(payload), "sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
