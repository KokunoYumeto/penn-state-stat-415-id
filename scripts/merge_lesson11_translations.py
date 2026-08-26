#!/usr/bin/env python3
"""Merge the three bounded Lesson 11 translation batches deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "working" / "lesson11_segments.csv"
TARGET = ROOT / "source" / "id-ID" / "lesson11_translation.csv"
BINDINGS = ROOT / "backend" / "lesson11_translation_bindings.jsonl"
RECEIPT = ROOT / "build" / "LESSON11_TRANSLATION_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON11_NORMALIZATION_RECEIPT.json"
ASSET_INVENTORY = ROOT / "working" / "lesson11_asset_inventory.csv"
SCRIPT = ROOT / "scripts" / "merge_lesson11_translations.py"

PARTS = {
    "A": ROOT / "working" / "lesson11_translation_batch_A.csv",
    "B": ROOT / "working" / "lesson11_translation_batch_B.csv",
    "C": ROOT / "working" / "lesson11_translation_batch_C.csv",
}
PART_RANGES = {
    "A": (1, 48),
    "B": (49, 286),
    "C": (287, 354),
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

DOCUMENT_ID = "O006-PSU-012"
COMPONENT_ID = "Lesson11"
SEGMENT_COUNT = 354
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_SHA256 = "4a007ab235242a27f000a8e8865fab06d2b8507a2e2e7400faf6112ce83a7c32"
NORMALIZATION_SCHEMA = "o006.stat415.lesson11-normalization.v1"

# This is the immutable byte prefix from the glossary header through
# O006-TERM-0168. Later lessons may append rows without changing this gate.
GLOSSARY_PREFIX_BYTES = 17_727
GLOSSARY_PREFIX_SHA256 = "1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65"
GLOSSARY_ROWS = 168
GLOSSARY_LAST_TERM_ID = "O006-TERM-0168"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode(
            "utf-8"
        )
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
        reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise RuntimeError(f"{label} has the wrong schema")
    if any(None in row for row in rows):
        raise RuntimeError(f"{label} has fields beyond its declared schema")
    return rows, data


def boundary_whitespace(value: str) -> tuple[str, str]:
    leading_length = len(value) - len(value.lstrip())
    trailing_start = len(value.rstrip())
    return value[:leading_length], value[trailing_start:]


def load_template() -> tuple[list[dict[str, str]], bytes]:
    rows, data = load_csv(TEMPLATE, "Lesson 11 segment template")
    expected = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, SEGMENT_COUNT + 1)]
    if len(rows) != SEGMENT_COUNT or [row["segment_id"] for row in rows] != expected:
        raise RuntimeError("Lesson 11 template is not the exact sequential boundary")
    for row in rows:
        if (
            row["document_id"] != DOCUMENT_ID
            or row["component_id"] != COMPONENT_ID
            or row["target_text"]
            or row["status"] != "pending"
            or sha256(row["source_text"].encode("utf-8")) != row["source_sha256"]
        ):
            raise RuntimeError(f"Lesson 11 pending template differs: {row['segment_id']}")
    return rows, data


def glossary_identity() -> dict[str, object]:
    data = GLOSSARY.read_bytes()
    if len(data) < GLOSSARY_PREFIX_BYTES:
        raise RuntimeError("Lesson 11 admitted glossary prefix is truncated")
    prefix = data[:GLOSSARY_PREFIX_BYTES]
    if (
        prefix.startswith(b"\xef\xbb\xbf")
        or b"\r" in prefix
        or not prefix.endswith(b"\n")
        or sha256(prefix) != GLOSSARY_PREFIX_SHA256
    ):
        raise RuntimeError("Lesson 11 admitted glossary prefix differs")
    try:
        reader = csv.DictReader(io.StringIO(prefix.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid Lesson 11 glossary prefix: {exc}") from exc
    expected_fields = ("term_id", "en_US", "id_ID", "decision")
    if (
        tuple(reader.fieldnames or ()) != expected_fields
        or len(rows) != GLOSSARY_ROWS
        or rows[-1]["term_id"] != GLOSSARY_LAST_TERM_ID
        or [row["term_id"] for row in rows]
        != [f"O006-TERM-{i:04d}" for i in range(1, GLOSSARY_ROWS + 1)]
    ):
        raise RuntimeError("Lesson 11 admitted glossary row boundary differs")
    return {
        "path": GLOSSARY.relative_to(ROOT).as_posix(),
        "bytes": GLOSSARY_PREFIX_BYTES,
        "sha256": GLOSSARY_PREFIX_SHA256,
        "rows": GLOSSARY_ROWS,
        "last_term_id": GLOSSARY_LAST_TERM_ID,
        "scope": "immutable cumulative glossary prefix through the 18 Lesson 11 decisions",
    }


def normalization_identity(template_data: bytes) -> dict[str, object]:
    data = NORMALIZATION_RECEIPT.read_bytes()
    if data.startswith(b"\xef\xbb\xbf") or b"\r" in data or not data.endswith(b"\n"):
        raise RuntimeError("Lesson 11 normalization receipt is not canonical UTF-8/LF")
    try:
        receipt = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid Lesson 11 normalization receipt: {exc}") from exc
    document = receipt.get("document", {})
    counts = receipt.get("counts", {})
    ranges = receipt.get("stable_id_ranges", {})
    template_output = receipt.get("outputs", {}).get(
        "working/lesson11_segments.csv", {}
    )
    if (
        receipt.get("schema") != NORMALIZATION_SCHEMA
        or document.get("document_id") != DOCUMENT_ID
        or document.get("component_id") != COMPONENT_ID
        or document.get("source_sha256") != SOURCE_SHA256
        or counts.get("translation_segments") != SEGMENT_COUNT
        or ranges.get("segments")
        != [f"{DOCUMENT_ID}-S0001", f"{DOCUMENT_ID}-S{SEGMENT_COUNT:04d}"]
        or template_output.get("bytes") != len(template_data)
        or template_output.get("sha256") != sha256(template_data)
        or template_output.get("rows") != SEGMENT_COUNT
    ):
        raise RuntimeError("Lesson 11 normalization receipt does not bind this template")
    return {
        "path": NORMALIZATION_RECEIPT.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
        "schema": NORMALIZATION_SCHEMA,
        "source_sha256": SOURCE_SHA256,
    }


def load_parts(
    template: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    by_id = {row["segment_id"]: row for row in template}
    merged: list[dict[str, str]] = []
    evidence: list[dict[str, object]] = []
    seen: set[str] = set()
    for name in ("A", "B", "C"):
        rows, data = load_csv(PARTS[name], f"Lesson 11 translation batch {name}")
        low, high = PART_RANGES[name]
        expected = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(low, high + 1)]
        if [row["segment_id"] for row in rows] != expected:
            raise RuntimeError(f"Lesson 11 batch {name} has the wrong ordered range")
        for row in rows:
            source = by_id[row["segment_id"]]
            if any(row[field] != source[field] for field in SOURCE_FIELDS):
                raise RuntimeError(
                    f"Lesson 11 batch {name} changed a source field: "
                    f"{row['segment_id']}"
                )
            if sha256(row["source_text"].encode("utf-8")) != row["source_sha256"]:
                raise RuntimeError(
                    f"Lesson 11 batch {name} has a false source hash: "
                    f"{row['segment_id']}"
                )
            if (
                row["status"] != "translated"
                or not row["target_text"].strip()
                or "\ufffd" in row["target_text"]
                or row["segment_id"] in seen
            ):
                raise RuntimeError(
                    f"Lesson 11 batch {name} has an invalid target: "
                    f"{row['segment_id']}"
                )
            if boundary_whitespace(row["target_text"]) != boundary_whitespace(
                source["source_text"]
            ):
                raise RuntimeError(
                    f"Lesson 11 batch {name} changed boundary whitespace: "
                    f"{row['segment_id']}"
                )
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
    if (
        len(merged) != SEGMENT_COUNT
        or len(seen) != SEGMENT_COUNT
        or [row["segment_id"] for row in merged] != expected_all
        or any(row["status"] != "translated" for row in merged)
    ):
        raise RuntimeError("Lesson 11 batches do not form one exact translated ledger")
    return merged, evidence


def compute() -> dict[str, bytes]:
    template, template_data = load_template()
    normalization = normalization_identity(template_data)
    rows, batch_evidence = load_parts(template)

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    csv_payload = output.getvalue().encode("utf-8")
    if b"\r" in csv_payload or not csv_payload.endswith(b"\n"):
        raise RuntimeError("Lesson 11 merged CSV is not canonical UTF-8/LF")

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
                "translation_provenance": PROVENANCE,
            }
        )
    bindings_payload = canonical_jsonl(bindings)

    receipt = {
        "schema": "o006.stat415.lesson11-translation.v1",
        "status": "complete",
        "document": COMPONENT_ID,
        "document_id": DOCUMENT_ID,
        "segment_count": SEGMENT_COUNT,
        "translated_status_count": sum(
            row["status"] == "translated" for row in rows
        ),
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
        "terminology_inputs": [glossary_identity()],
        "normalization_inputs": [normalization, identity(ASSET_INVENTORY)],
        "validation": {
            "source_fields_exact": True,
            "source_hashes_recomputed": True,
            "canonical_utf8_lf": True,
            "boundary_whitespace_exact": True,
            "all_segments_translated": True,
            "replacement_character_absent_from_targets": True,
        },
        "translation_csv": {
            "path": TARGET.relative_to(ROOT).as_posix(),
            "bytes": len(csv_payload),
            "sha256": sha256(csv_payload),
        },
        "bindings": {
            "path": BINDINGS.relative_to(ROOT).as_posix(),
            "bytes": len(bindings_payload),
            "sha256": sha256(bindings_payload),
            "records": len(bindings),
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
                raise RuntimeError(f"Lesson 11 translation output differs: {relative}")
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
