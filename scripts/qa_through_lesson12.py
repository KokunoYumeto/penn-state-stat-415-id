#!/usr/bin/env python3
"""Deterministic cumulative QA for the complete 14-document STAT 415 id-ID reader."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson12 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON12_QA_RECEIPT.json"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON12_BUILD_RECEIPT.json"
MANIFEST = ROOT / "build" / "THROUGH_LESSON12_MANIFEST.csv"
DOCUMENTS = ROOT / "backend" / "through_lesson12_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson12_corrections.jsonl"
PRIOR_CORRECTIONS = ROOT / "backend" / "through_lesson11_corrections.jsonl"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson12.html"
TARGET = ROOT / "source" / "id-ID" / "Lesson12.html"
SEGMENTS = ROOT / "working" / "lesson12_segments.csv"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson12_translation.csv"
BINDINGS = ROOT / "backend" / "lesson12_translation_bindings.jsonl"
TARGET_CORRECTIONS = ROOT / "backend" / "lesson12_target_corrections.jsonl"
NATIVE_ID_MAP = ROOT / "backend" / "lesson12_target_native_id_map.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON12_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON12_NORMALIZATION_RECEIPT.json"
MATERIALIZATION_RECEIPT = ROOT / "build" / "LESSON12_MATERIALIZATION_RECEIPT.json"
ASSET_MANIFEST = ROOT / "authority" / "LESSON12_ASSET_MANIFEST.csv"
ASSET_FREEZE_RECEIPT = ROOT / "authority" / "LESSON12_ASSET_FREEZE_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"

FREEZE_SCRIPT = ROOT / "scripts" / "freeze_lesson12_assets.py"
NORMALIZE_SCRIPT = ROOT / "scripts" / "normalize_lesson12.py"
BATCH_SCRIPT = ROOT / "scripts" / "build_lesson12_translation_batches.py"
MERGE_SCRIPT = ROOT / "scripts" / "merge_lesson12_translations.py"
MATERIALIZE_SCRIPT = ROOT / "scripts" / "materialize_lesson12_translation.py"
CORRECTION_MODULE = ROOT / "scripts" / "lesson12_corrections.py"
BUILD_SCRIPT = ROOT / "scripts" / "build_through_lesson12.py"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
DOCUMENT_ID = "O006-PSU-013"
COMPONENT_ID = "Lesson12"
EXPECTED_COMPONENTS = ["index", *[f"Lesson{i:02d}" for i in range(13)]]
EXPECTED_IDS = {
    "index": "O006-PSU-000",
    **{f"Lesson{i:02d}": f"O006-PSU-{i + 1:03d}" for i in range(13)},
}
EXPECTED_SOURCE_COUNTS = {
    "index": (77, 197, 0),
    "Lesson00": (446, 365, 331),
    "Lesson01": (221, 188, 169),
    "Lesson02": (324, 228, 209),
    "Lesson03": (531, 421, 440),
    "Lesson04": (372, 335, 289),
    "Lesson05": (340, 1_475, 108),
    "Lesson06": (176, 149, 102),
    "Lesson07": (237, 399, 148),
    "Lesson08": (291, 604, 156),
    "Lesson09": (443, 414, 219),
    "Lesson10": (540, 625, 369),
    "Lesson11": (354, 264, 264),
    "Lesson12": (580, 846, 352),
}
EXPECTED_TARGET_UNITS = {
    **{key: value[1] for key, value in EXPECTED_SOURCE_COUNTS.items()},
    "Lesson00": 363,
    "Lesson08": 594,
}
EXPECTED_EDITION_STATUS = "complete: 14 of 14 documents; landing and Lessons 00–12"
EXPECTED_GLOSSARY_BYTES = 20_340
EXPECTED_GLOSSARY_SHA256 = "554dcbfb5161df6f0eb86027822eabbf4fae9179bb152947a8ad6c196cb34b05"
EXPECTED_GLOSSARY_ROWS = 192
EXPECTED_READER_FILES = 106
LESSON12_CORRECTION_IDS = [f"O006-PSU-ADV-{i:04d}" for i in range(219, 243)]
LESSON12_FINDING_IDS = [f"L12-D{i:03d}" for i in range(1, 25)]
LESSON12_DISPOSITIONED_IDS = {
    "O006-PSU-ADV-0220",
    "O006-PSU-ADV-0235",
    "O006-PSU-ADV-0242",
}
LESSON12_MATH_EDIT_IDS = {
    f"{DOCUMENT_ID}-{short}"
    for short in (
        "M0056", "M0059", "M0060", "M0136", "M0210", "M0234", "M0236",
        "M0241", "M0260", "M0272", "M0281", "M0283", "M0285", "M0325",
        "M0327", "M0328", "M0331", "M0333", "M0334",
    )
}
EXPECTED_REMOVED_UNITS_BY_CORRECTION = {
    "O006-PSU-ADV-0014": {
        "O006-PSU-001-U0342",
        "O006-PSU-001-U0350",
    },
    "O006-PSU-ADV-0150": {
        *[f"O006-PSU-009-U{i:04d}" for i in range(572, 577)],
        *[f"O006-PSU-009-U{i:04d}" for i in range(598, 603)],
    },
}
EXPECTED_DUPLICATE_NATIVE_IDS = {
    "fig-bidsgraph": 4,
    "fig-bidsgraph-caption-0ceaefa1-69ba-4598-a22c-09a6ac19f8ca": 2,
    "fig-iqnormal": 2,
    "fig-lesson9_1": 2,
    "fig-scattertemp": 2,
    "fig-scattertemp2": 2,
    "fig-skin-cancer": 2,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": sha256(data)}


def matches_identity(record: object, path: Path) -> bool:
    expected = identity(path)
    return isinstance(record, dict) and all(record.get(key) == value for key, value in expected.items())


def matches_keyed_identity(record: object, path: Path) -> bool:
    """Match an identity whose path is supplied by its containing mapping key."""
    expected = identity(path)
    return (
        isinstance(record, dict)
        and record.get("bytes") == expected["bytes"]
        and record.get("sha256") == expected["sha256"]
    )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def canonical_text_gate(payload: bytes, label: str) -> str:
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        raise RuntimeError(f"{label} is not canonical UTF-8/LF with a final newline")
    try:
        return payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} is not strict UTF-8: {exc}") from exc


def parse_jsonl(payload: bytes, label: str) -> list[dict[str, object]]:
    text = canonical_text_gate(payload, label)
    try:
        rows = [json.loads(line) for line in text.splitlines() if line]
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{label} contains a non-object")
    return rows


def load_csv(path: Path, label: str) -> tuple[list[dict[str, str]], list[str], bytes]:
    payload = path.read_bytes()
    text = canonical_text_gate(payload, label)
    try:
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except csv.Error as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    return rows, list(reader.fieldnames or []), payload


def receipt_identity_gate(record: object, label: str) -> dict[str, object]:
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise RuntimeError(f"{label} identity is missing")
    path = ROOT / str(record["path"])
    if not path.is_file() or not matches_identity(record, path):
        raise RuntimeError(f"{label} identity differs")
    return identity(path)


def replay_check_only(script: Path, label: str) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, "-B", str(script), "--check-only"],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()[-2_000:]
        raise RuntimeError(f"{label} check-only replay failed: {detail}")
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    try:
        result = json.loads(lines[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} check-only replay did not return JSON") from exc
    if not isinstance(result, dict) or result.get("mode") != "verified":
        raise RuntimeError(f"{label} check-only replay did not verify")
    return {"script": identity(script), "result": result}


def pipeline_replay_gate() -> dict[str, object]:
    return {
        "asset_freeze": replay_check_only(FREEZE_SCRIPT, "Lesson12 asset freeze"),
        "normalization": replay_check_only(NORMALIZE_SCRIPT, "Lesson12 normalization"),
        "translation_batches": replay_check_only(BATCH_SCRIPT, "Lesson12 translation batches"),
        "translation_merge": replay_check_only(MERGE_SCRIPT, "Lesson12 translation merge"),
        "materialization": replay_check_only(MATERIALIZE_SCRIPT, "Lesson12 materialization"),
        "cumulative_build": replay_check_only(BUILD_SCRIPT, "through-Lesson12 build"),
    }


def glossary_gate() -> dict[str, object]:
    rows, fields, data = load_csv(GLOSSARY, "cumulative glossary")
    expected_ids = [f"O006-TERM-{i:04d}" for i in range(1, 193)]
    if (
        fields != ["term_id", "en_US", "id_ID", "decision"]
        or len(data) != EXPECTED_GLOSSARY_BYTES
        or sha256(data) != EXPECTED_GLOSSARY_SHA256
        or len(rows) != EXPECTED_GLOSSARY_ROWS
        or [row["term_id"] for row in rows] != expected_ids
        or any(not row["en_US"].strip() or not row["id_ID"].strip() or not row["decision"].strip() for row in rows)
    ):
        raise RuntimeError("exact 192-row cumulative glossary differs")
    return {
        **identity(GLOSSARY),
        "rows": EXPECTED_GLOSSARY_ROWS,
        "last_term_id": "O006-TERM-0192",
        "scope": "exact cumulative glossary through the 24 Lesson 12 decisions",
    }


def deterministic_build_gate() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    expected_constants = {
        "EXPECTED_SEGMENTS": 580,
        "EXPECTED_UNITS": 846,
        "EXPECTED_MATH": 352,
        "EXPECTED_ASSETS": 9,
        "EXPECTED_ASSET_BYTES": 233_075,
        "EXPECTED_CORRECTIONS": 24,
        "EXPECTED_TOTAL_SEGMENTS": 4_932,
        "EXPECTED_TOTAL_UNITS": 6_510,
        "EXPECTED_TARGET_UNITS": 6_498,
        "EXPECTED_TOTAL_MATH": 3_156,
        "EXPECTED_TOTAL_CORRECTIONS": 242,
        "EXPECTED_READER_FILES": EXPECTED_READER_FILES,
        "EXPECTED_GLOSSARY_ROWS": EXPECTED_GLOSSARY_ROWS,
    }
    actual = {key: getattr(builder, key, None) for key in expected_constants}
    if actual != expected_constants:
        raise RuntimeError(f"Lesson12 builder census contract differs: {actual}")
    outputs, receipt, reader_files = builder.compute()
    for relative, payload in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"deterministic Lesson12 build differs: {relative}")
    if shared.current_reader_files() != reader_files:
        raise RuntimeError("reader inventory differs from deterministic Lesson12 build")
    if len(reader_files) != EXPECTED_READER_FILES:
        raise RuntimeError("Lesson12 reader file census differs")
    if not BUILD_RECEIPT.is_file() or BUILD_RECEIPT.read_bytes() != outputs[BUILD_RECEIPT.relative_to(ROOT).as_posix()]:
        raise RuntimeError("Lesson12 build receipt does not match deterministic output")
    coverage = receipt.get("coverage", {})
    math = receipt.get("math_nodes", {})
    corrections = receipt.get("corrections", {})
    reader = receipt.get("reader", {})
    offline = receipt.get("offline", {})
    rights = receipt.get("rights", {})
    if (
        receipt.get("schema") != "o006.stat415.through-lesson12-build.v1"
        or receipt.get("status") != "built"
        or receipt.get("locale") != "id-ID"
        or receipt.get("translation_provenance") != PROVENANCE
        or coverage.get("complete_documents") != EXPECTED_COMPONENTS
        or coverage.get("complete_count") != 14
        or coverage.get("corpus_document_count") != 14
        or receipt.get("translation_segments") != 4_932
        or receipt.get("structural_units_normalized") != 6_510
        or receipt.get("structural_units_target") != 6_498
        or math.get("Lesson12") != 352
        or math.get("total") != 3_156
        or corrections.get("count") != 242
        or corrections.get("through_lesson11_count") != 218
        or corrections.get("lesson12_count") != 24
        or reader.get("files") != EXPECTED_READER_FILES
        or reader.get("manifest_path") != MANIFEST.relative_to(ROOT).as_posix()
        or reader.get("manifest_bytes") != MANIFEST.stat().st_size
        or reader.get("manifest_sha256") != sha256(MANIFEST.read_bytes())
        or offline.get("external_runtime_requests") != 0
        or offline.get("analytics") is not False
        or offline.get("cookies") is not False
        or offline.get("local_mathjax") is not True
        or offline.get("third_party_iframes") != 0
        or rights.get("Penn State content") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
    ):
        raise RuntimeError("Lesson12 cumulative build receipt contract differs")
    targets = receipt.get("target_documents")
    if not isinstance(targets, list) or len(targets) != 14:
        raise RuntimeError("Lesson12 target-document receipt differs")
    for record in targets:
        receipt_identity_gate(record, "Lesson12 target document")
    return outputs, receipt, reader_files


def translation_backend_gate(build_receipt: dict[str, object], glossary: dict[str, object]) -> dict[str, object]:
    source_rows, source_fields, _ = load_csv(SEGMENTS, "Lesson12 segment template")
    target_rows, target_fields, _ = load_csv(TRANSLATIONS, "Lesson12 translation CSV")
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson12 bindings")
    expected_fields = [
        "segment_id", "document_id", "component_id", "section_id",
        "source_sha256", "source_text", "target_text", "status",
    ]
    if (
        source_fields != expected_fields
        or target_fields != expected_fields
        or len(source_rows) != 580
        or len(target_rows) != 580
        or len(bindings) != 580
    ):
        raise RuntimeError("Lesson12 translation/backend census differs")
    identical: list[str] = []
    for ordinal, (source, target, binding) in enumerate(zip(source_rows, target_rows, bindings), start=1):
        segment_id = f"{DOCUMENT_ID}-S{ordinal:04d}"
        if source["segment_id"] != segment_id or target["segment_id"] != segment_id:
            raise RuntimeError(f"Lesson12 segment order differs: {segment_id}")
        for field in expected_fields[:6]:
            if target[field] != source[field]:
                raise RuntimeError(f"Lesson12 immutable translation field differs: {segment_id}")
        if sha256(source["source_text"].encode("utf-8")) != source["source_sha256"]:
            raise RuntimeError(f"Lesson12 source hash differs: {segment_id}")
        text = target["target_text"]
        source_leading = source["source_text"][: len(source["source_text"]) - len(source["source_text"].lstrip())]
        source_trailing = source["source_text"][len(source["source_text"].rstrip()) :]
        target_leading = text[: len(text) - len(text.lstrip())]
        target_trailing = text[len(text.rstrip()) :]
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": segment_id,
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "section_id": target["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": target["source_sha256"],
            "target_sha256": sha256(text.encode("utf-8")),
            "status": "translated",
            "translation_provenance": PROVENANCE,
        }
        if (
            target["status"] != "translated"
            or not text.strip()
            or "\ufffd" in text
            or (target_leading, target_trailing) != (source_leading, source_trailing)
            or binding != expected_binding
        ):
            raise RuntimeError(f"Lesson12 translation/backend binding differs: {segment_id}")
        if source["source_text"] == text:
            identical.append(segment_id)

    receipt_payload = TRANSLATION_RECEIPT.read_bytes()
    canonical_text_gate(receipt_payload, "Lesson12 translation receipt")
    receipt = json.loads(receipt_payload.decode("utf-8"))
    validation = receipt.get("validation", {})
    if (
        receipt.get("schema") != "o006.stat415.lesson12-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document") != COMPONENT_ID
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("locale") != "id-ID"
        or receipt.get("segment_count") != 580
        or receipt.get("translated_status_count") != 580
        or receipt.get("translation_provenance") != PROVENANCE
        or receipt.get("identical_segments") != identical
        or not matches_identity(receipt.get("translation_csv"), TRANSLATIONS)
        or not matches_identity(receipt.get("bindings"), BINDINGS)
        or not matches_identity(receipt.get("template"), SEGMENTS)
        or not matches_identity(receipt.get("merge_script"), MERGE_SCRIPT)
        or not isinstance(validation, dict)
        or not validation
        or any(value is not True for value in validation.values())
    ):
        raise RuntimeError("Lesson12 translation receipt differs")
    expected_batches = (
        ("A", 200, f"{DOCUMENT_ID}-S0001", f"{DOCUMENT_ID}-S0200"),
        ("B", 200, f"{DOCUMENT_ID}-S0201", f"{DOCUMENT_ID}-S0400"),
        ("C", 180, f"{DOCUMENT_ID}-S0401", f"{DOCUMENT_ID}-S0580"),
    )
    batches = receipt.get("batches")
    if not isinstance(batches, list) or len(batches) != 3:
        raise RuntimeError("Lesson12 translation batch receipt differs")
    batch_evidence: list[dict[str, object]] = []
    for row, (name, count, first_id, last_id) in zip(batches, expected_batches):
        if (
            not isinstance(row, dict)
            or row.get("batch") != name
            or row.get("segments") != count
            or row.get("range") != [first_id, last_id]
        ):
            raise RuntimeError(f"Lesson12 translation batch {name} differs")
        batch_evidence.append(receipt_identity_gate(row, f"Lesson12 batch {name}"))
    terminology_inputs = receipt.get("terminology_inputs")
    if (
        not isinstance(terminology_inputs, list)
        or len(terminology_inputs) != 1
        or not matches_identity(terminology_inputs[0], GLOSSARY)
        or terminology_inputs[0].get("rows") != EXPECTED_GLOSSARY_ROWS
        or terminology_inputs[0].get("last_term_id") != "O006-TERM-0192"
    ):
        raise RuntimeError("Lesson12 translation glossary binding differs")
    build_inputs = build_receipt.get("inputs", {})
    if isinstance(build_inputs, dict):
        accepted = any(
            matches_identity(build_inputs.get(key), TRANSLATION_RECEIPT)
            for key in ("translation", "translation_receipt")
        )
        if not accepted:
            raise RuntimeError("Lesson12 build/translation receipt binding differs")
    return {
        "new_segments": 580,
        "cumulative_segments": 4_932,
        "translation": identity(TRANSLATIONS),
        "bindings": identity(BINDINGS),
        "translation_receipt": identity(TRANSLATION_RECEIPT),
        "batches": batch_evidence,
        "identical_segments": identical,
    }


def changed_math_ids_from_corrections(
    rows: list[dict[str, object]], document_id: str
) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        stack: list[object] = [row]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                math_id = value.get("math_id")
                if (
                    value.get("surface") == "math"
                    and isinstance(math_id, str)
                    and math_id.startswith(document_id + "-")
                ):
                    ids.add(math_id)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
    return ids


def registered_removed_units_by_correction(
    rows: list[dict[str, object]],
) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for row in rows:
        correction_id = row.get("correction_id")
        removed_units: list[str] = []
        stack: list[object] = [row]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                if "removed_unit_ids" in value:
                    removed = value["removed_unit_ids"]
                    if (
                        not isinstance(removed, list)
                        or not removed
                        or any(not isinstance(unit_id, str) for unit_id in removed)
                    ):
                        raise RuntimeError("registered stable-unit removal is malformed")
                    removed_units.extend(removed)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
        if removed_units:
            if not isinstance(correction_id, str) or correction_id in found:
                raise RuntimeError("registered stable-unit removal ownership differs")
            if len(removed_units) != len(set(removed_units)):
                raise RuntimeError(f"registered stable-unit removal duplicates: {correction_id}")
            found[correction_id] = set(removed_units)
    if found != EXPECTED_REMOVED_UNITS_BY_CORRECTION:
        raise RuntimeError(f"registered stable-unit removals differ: {found}")
    return found


def attribute_tokens(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(token) for token in value]
    return str(value or "").split()


def target_math_text(main: Tag) -> dict[str, str]:
    return {
        str(node.get("data-o006-math-id")): node.get_text()
        for node in main.select("[data-o006-math-id]")
    }


def lesson12_semantics_gate(main: Tag, *, reader_mode: bool = False) -> dict[str, object]:
    tables = main.select("table")
    if (
        len(tables) != 6
        or len(main.select('table th[scope="col"]')) != 31
        or len(main.select('table th[scope="row"]')) != 42
        or len(main.select("table th")) != 73
    ):
        raise RuntimeError("Lesson12 table census/scope contract differs")
    caption_ids: list[str] = []
    for ordinal, table in enumerate(tables, start=1):
        caption = table.find("caption", recursive=False)
        expected_id = f"lesson12-table-{ordinal}-caption"
        if (
            caption is None
            or caption.get("id") != expected_id
            or len(caption.get_text(" ", strip=True)) < 24
            or attribute_tokens(table.get("aria-describedby")) != [expected_id]
            or "reader-responsive-table" not in attribute_tokens(table.get("class"))
            or any(cell.get("scope") not in {"col", "row"} for cell in table.select("th"))
            # Restrict the header-row check to THEAD.  ``tr:first-of-type``
            # without that boundary also selects the first TBODY row, whose
            # leading header correctly has ``scope=\"row\"``.
            or any(cell.get("scope") != "col" for cell in table.select("thead > tr:first-of-type > th"))
        ):
            raise RuntimeError(f"Lesson12 table {ordinal} caption/scope semantics differ")
        caption_ids.append(expected_id)

    manifest_rows, manifest_fields, _ = load_csv(ASSET_MANIFEST, "Lesson12 asset manifest")
    expected_manifest_fields = [
        "asset_id", "source_reference", "official_url", "local_path", "bytes",
        "sha256", "media_type", "width", "height", "bit_depth", "color_type",
        "last_modified", "etag", "license", "disposition",
    ]
    if (
        manifest_fields != expected_manifest_fields
        or len(manifest_rows) != 9
        or [row["asset_id"] for row in manifest_rows]
        != [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, 10)]
    ):
        raise RuntimeError("Lesson12 asset manifest schema/sequence differs")
    manifest = {row["asset_id"]: row for row in manifest_rows}
    images = main.select("img[data-o006-asset-id]")
    image_ids = [str(image.get("data-o006-asset-id")) for image in images]
    if (
        len(images) != 10
        or len(set(image_ids)) != 9
        or Counter(image_ids)[f"{DOCUMENT_ID}-A0006"] != 2
        or any(count != 1 for key, count in Counter(image_ids).items() if key != f"{DOCUMENT_ID}-A0006")
    ):
        raise RuntimeError("Lesson12 image occurrence closure differs")
    for image in images:
        asset_id = str(image.get("data-o006-asset-id"))
        row = manifest.get(asset_id)
        figure = image.find_parent("figure")
        expected_src = (
            "assets/lesson12/" + PurePosixPath(row["local_path"]).relative_to(
                "authority/assets/stat415/lesson12"
            ).as_posix()
            if reader_mode and row is not None
            else "../../" + row["local_path"] if row is not None else None
        )
        if (
            row is None
            or str(image.get("src")) != expected_src
            or str(image.get("width")) != row["width"]
            or str(image.get("height")) != row["height"]
            or len(str(image.get("alt") or "").strip()) < 40
            or image.get("style")
            or image.get("loading") != "lazy"
            or image.get("decoding") != "async"
            or not {"reader-full-width-image", "reader-responsive-image"}.issubset(
                set(attribute_tokens(image.get("class")))
            )
            or figure is None
            or "reader-full-width-figure" not in attribute_tokens(figure.get("class"))
        ):
            raise RuntimeError(f"Lesson12 centered/full-width image differs: {asset_id}")

    videos = main.select("details.offline-video-equivalent")
    expected_video_urls = [
        "https://www.youtube.com/embed/oAaPR1qVedw",
        "https://www.youtube.com/embed/pWMp1vhStDE",
        "https://www.youtube.com/embed/mdzP-v6vl74",
    ]
    if (
        len(videos) != 3
        or [node.get("data-o006-video-id") for node in videos]
        != [f"{DOCUMENT_ID}-V{i:04d}" for i in range(1, 4)]
        or [node.select_one("a[href]").get("href") if node.select_one("a[href]") else None for node in videos]
        != expected_video_urls
        or any(len(node.get_text(" ", strip=True)) < 350 for node in videos)
        or main.select("iframe, object, embed, video, audio, source, script")
    ):
        raise RuntimeError("Lesson12 offline video-equivalent closure differs")

    provenance = main.select(
        '.component-provenance[data-o006-component-provenance-id="O006-PSU-013-PROV"]'
    )
    provenance_text = provenance[0].get_text(" ", strip=True).casefold() if provenance else ""
    if (
        len(provenance) != 1
        or "penn state stat 415" not in provenance_text
        or "cc by-nc 4.0" not in provenance_text
        or "24 koreksi" not in provenance_text
        or PROVENANCE.casefold() not in provenance_text
    ):
        raise RuntimeError("Lesson12 visible provenance/rights/change notice differs")

    recalculation = main.select(
        'details.target-only-reproducibility[data-o006-correction-id="O006-PSU-ADV-0237"]'
    )
    recalculation_text = recalculation[0].get_text(" ", strip=True).casefold() if recalculation else ""
    code = recalculation[0].select_one('code[data-o006-code-id="O006-PSU-ADV-0237-CODE01"]') if recalculation else None
    if (
        len(recalculation) != 1
        or code is None
        or "lm(price ~ catch)" not in code.get_text()
        or "df.residual(fit)" not in code.get_text()
        or "−29,3948251765" not in recalculation_text
        or "seed tidak diperlukan" not in recalculation_text
    ):
        raise RuntimeError("Lesson12 reproducible recalculation contract differs")
    return {
        "semantic_tables": 6,
        "table_captions": 6,
        "column_scopes": 31,
        "row_scopes": 42,
        "unique_frozen_images": 9,
        "image_occurrences": 10,
        "offline_video_equivalents": 3,
        "active_video_or_embed_runtimes": 0,
        "component_provenance_blocks": 1,
        "reproducible_recalculations": 1,
    }


def materialization_and_corrections_gate() -> dict[str, object]:
    receipt_payload = MATERIALIZATION_RECEIPT.read_bytes()
    canonical_text_gate(receipt_payload, "Lesson12 materialization receipt")
    receipt = json.loads(receipt_payload.decode("utf-8"))
    expected_counts = {
        "component_provenance_blocks": 1,
        "external_video_runtimes": 0,
        "image_occurrences": 10,
        "native_id_map_records": 16,
        "offline_video_equivalents": 3,
        "registered_repaired_source_math": 19,
        "registered_target_corrections": 24,
        "semantic_tables": 6,
        "stable_source_math": 352,
        "stable_source_units": 846,
        "table_captions": 6,
        "translation_segments": 580,
        "unique_frozen_images": 9,
    }
    expected_inputs = [
        NORMALIZED, TRANSLATIONS, BINDINGS, TRANSLATION_RECEIPT,
        NORMALIZATION_RECEIPT, ASSET_MANIFEST, MATERIALIZE_SCRIPT, CORRECTION_MODULE,
    ]
    expected_validation = {
        "all_registered_repairs_dispositioned": True,
        "authority_unchanged": True,
        "duplicate_target_ids_removed_with_reversible_map": True,
        "external_video_runtime_removed": True,
        "frozen_images_byte_bound": True,
        "images_centered_responsive_and_dimensioned": True,
        "numerical_recalculation_reproducible": True,
        "source_credit_license_and_change_notice_visible": True,
        "source_math_ids_preserved": True,
        "source_segment_bindings_exact": True,
        "source_stable_ids_preserved": True,
        "tables_captioned_and_scoped": True,
        "target_id_references_resolve": True,
        "target_local_paths_resolve": True,
        "unregistered_source_math_unchanged": True,
        "video_bytes_redistributed": False,
    }
    outputs = receipt.get("outputs", {})
    if (
        receipt.get("schema") != "o006.stat415.lesson12-materialization.v1"
        or receipt.get("status") != "pass"
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("component_id") != COMPONENT_ID
        or receipt.get("locale") != "id-ID"
        or receipt.get("translation_provenance") != PROVENANCE
        or receipt.get("registered_repaired_math_ids") != sorted(LESSON12_MATH_EDIT_IDS)
        or receipt.get("counts") != expected_counts
        or receipt.get("inputs") != [identity(path) for path in expected_inputs]
        or not isinstance(outputs, dict)
        or not all(matches_keyed_identity(outputs.get(path.relative_to(ROOT).as_posix()), path) for path in (TARGET, TARGET_CORRECTIONS, NATIVE_ID_MAP))
        or receipt.get("validation") != expected_validation
    ):
        raise RuntimeError("Lesson12 materialization receipt contract differs")

    cumulative = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    prior = parse_jsonl(PRIOR_CORRECTIONS.read_bytes(), "through-Lesson11 corrections")
    lesson12 = parse_jsonl(TARGET_CORRECTIONS.read_bytes(), "Lesson12 target corrections")
    if (
        len(prior) != 218
        or [row.get("correction_id") for row in prior]
        != [f"O006-PSU-ADV-{i:04d}" for i in range(1, 219)]
        or len(lesson12) != 24
        or [row.get("correction_id") for row in lesson12] != LESSON12_CORRECTION_IDS
        or [row.get("source_defect_id") for row in lesson12] != LESSON12_FINDING_IDS
        or cumulative != [*prior, *lesson12]
    ):
        raise RuntimeError("Lesson12 corrections are not an exact append after 0218")
    for row in lesson12:
        correction_id = str(row.get("correction_id"))
        expected_status = (
            "dispositioned-to-original-companion"
            if correction_id in LESSON12_DISPOSITIONED_IDS
            else "applied-target-only"
        )
        surfaces = row.get("surfaces")
        if (
            row.get("schema") != "o006.stat415.target-correction.v1"
            or row.get("document_id") != DOCUMENT_ID
            or row.get("status") != expected_status
            or not isinstance(surfaces, list)
            or not surfaces
            or row.get("replacement_count") != len(surfaces)
            or not str(row.get("note") or "").strip()
        ):
            raise RuntimeError(f"Lesson12 correction record differs: {correction_id}")

    removals = registered_removed_units_by_correction(cumulative)
    source = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser").select_one("main#quarto-document-content")
    target = BeautifulSoup(TARGET.read_bytes(), "html.parser").select_one("main#quarto-document-content")
    if source is None or target is None:
        raise RuntimeError("Lesson12 source/target instructional main is missing")
    expected_units = [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, 847)]
    expected_math = [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, 353)]
    source_units = shared.stable_values(source, "data-o006-id")
    target_units = shared.stable_values(target, "data-o006-id")
    source_math_ids = shared.stable_values(source, "data-o006-math-id")
    target_math_ids = shared.stable_values(target, "data-o006-math-id")
    if source_units != expected_units or target_units != source_units:
        raise RuntimeError("Lesson12 exact stable-unit identity/order differs")
    if source_math_ids != expected_math or target_math_ids != source_math_ids:
        raise RuntimeError("Lesson12 exact math identity/order differs")
    source_math = target_math_text(source)
    target_math = target_math_text(target)
    changed = {key for key in source_math if source_math[key] != target_math[key]}
    registered = changed_math_ids_from_corrections(lesson12, DOCUMENT_ID)
    if changed != LESSON12_MATH_EDIT_IDS or registered != LESSON12_MATH_EDIT_IDS:
        raise RuntimeError(
            f"Lesson12 changed/registered math differs: changed={sorted(changed)} registered={sorted(registered)}"
        )
    markers = {
        str(node.get("data-o006-correction-id"))
        for node in target.select("[data-o006-correction-id]")
    }
    if not markers or not markers.issubset(set(LESSON12_CORRECTION_IDS)):
        raise RuntimeError("Lesson12 target contains an unregistered correction marker")

    source_native_ids = [str(node.get("id")) for node in source.select("[id]")]
    source_duplicates = {
        key: count for key, count in Counter(source_native_ids).items() if count > 1
    }
    if source_duplicates != EXPECTED_DUPLICATE_NATIVE_IDS:
        raise RuntimeError("Lesson12 source duplicate native-ID witness differs")
    if any(count > 1 for count in Counter(str(node.get("id")) for node in target.select("[id]")).values()):
        raise RuntimeError("Lesson12 target retains duplicate native IDs")
    native_rows = parse_jsonl(NATIVE_ID_MAP.read_bytes(), "Lesson12 native-ID map")
    expected_native_pairs = [
        (source_id, occurrence)
        for source_id in sorted(EXPECTED_DUPLICATE_NATIVE_IDS)
        for occurrence in range(1, EXPECTED_DUPLICATE_NATIVE_IDS[source_id] + 1)
    ]
    if (
        len(native_rows) != 16
        or [(row.get("source_native_id"), row.get("source_occurrence")) for row in native_rows]
        != expected_native_pairs
    ):
        raise RuntimeError("Lesson12 reversible native-ID map sequence differs")
    reference_update_count = 0
    for row in native_rows:
        source_id = str(row.get("source_native_id"))
        occurrence = int(row.get("source_occurrence", 0))
        expected_target_id = f"{source_id}--source-occurrence-{occurrence:02d}"
        node = target.find(id=expected_target_id)
        updates = row.get("reference_updates")
        if (
            row.get("schema") != "o006.stat415.target-native-id-map.v1"
            or row.get("document_id") != DOCUMENT_ID
            or row.get("target_native_id") != expected_target_id
            or node is None
            or node.get("data-o006-source-native-id") != source_id
            or node.get("data-o006-source-native-occurrence") != str(occurrence)
            or node.get("data-o006-id") != row.get("stable_unit_id")
            or not isinstance(updates, list)
        ):
            raise RuntimeError(f"Lesson12 reversible native-ID mapping differs: {expected_target_id}")
        reference_update_count += len(updates)
        for update in updates:
            stable_id = str(update.get("referrer_stable_unit_id"))
            attribute = str(update.get("attribute"))
            refs = target.select(f'[data-o006-id="{stable_id}"]')
            if (
                len(refs) != 1
                or attribute not in {"aria-describedby", "aria-labelledby"}
                or expected_target_id not in attribute_tokens(refs[0].get(attribute))
                or update.get("target_native_id") != expected_target_id
            ):
                raise RuntimeError(f"Lesson12 native-ID reference update differs: {expected_target_id}")
    if reference_update_count != 2:
        raise RuntimeError("Lesson12 native-ID reference-update census differs")

    semantics = lesson12_semantics_gate(target)
    return {
        "cumulative_corrections": 242,
        "lesson12_corrections": 24,
        "backend": identity(CORRECTIONS),
        "lesson12_backend": identity(TARGET_CORRECTIONS),
        "materialization_receipt": identity(MATERIALIZATION_RECEIPT),
        "stable_units": len(target_units),
        "math_nodes": len(target_math_ids),
        "changed_registered_math": sorted(changed),
        "target_correction_markers": sorted(markers),
        "registered_removed_units": {
            correction_id: sorted(unit_ids)
            for correction_id, unit_ids in sorted(removals.items())
        },
        "native_id_mappings": identity(NATIVE_ID_MAP),
        "native_id_map_records": 16,
        "native_id_reference_updates": reference_update_count,
        "semantics": semantics,
    }


def visible_prose(main: Tag) -> str:
    values: list[str] = []
    for node in main.find_all(string=True):
        if not isinstance(node, NavigableString) or not node.strip():
            continue
        if node.find_parent(["code", "pre", "style", "script"]):
            continue
        if node.find_parent(class_="math"):
            continue
        values.append(str(node))
    return "\n".join(values)


def reader_gate(
    reader_files: set[PurePosixPath], build_receipt: dict[str, object]
) -> dict[str, object]:
    if len(reader_files) != EXPECTED_READER_FILES:
        raise RuntimeError("reader file count differs")
    if builder.CURRENT_CSS != PurePosixPath("assets/reader-14of14.css"):
        raise RuntimeError("Lesson12 builder CSS route differs")
    css_path = BUILD.joinpath(*builder.CURRENT_CSS.parts)
    css = css_path.read_bytes()
    css_text = re.sub(r"\s+", " ", css.decode("utf-8", errors="strict"))
    for rule in (
        "width: 100%",
        "max-width: 100%",
        "height: auto",
        "margin-inline: auto",
        "overflow-x: auto",
    ):
        if rule not in css_text:
            raise RuntimeError(f"responsive CSS rule missing: {rule}")
    if "Lessons 07–12" not in css_text:
        raise RuntimeError("Lesson12 cumulative responsive CSS label differs")
    layout = build_receipt.get("layout", {})
    if (
        layout.get("reader_css_path") != builder.CURRENT_CSS.as_posix()
        or layout.get("reader_css_bytes") != len(css)
        or layout.get("reader_css_sha256") != sha256(css)
        or layout.get("lesson12_full_width_image_occurrences") != 10
        or layout.get("lesson12_responsive_tables") != 6
        or "fill and center" not in str(layout.get("rule") or "")
    ):
        raise RuntimeError("Lesson12 responsive-layout receipt differs")

    expected_nav = [
        "index.html",
        *[f"Lesson{i:02d}.html" for i in range(13)],
        "licenses/index.html",
    ]
    corrections = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    removals_by_correction = registered_removed_units_by_correction(corrections)
    registered_removals = set().union(*removals_by_correction.values())
    reader_payloads = {
        path: BUILD.joinpath(*path.parts).read_bytes() for path in reader_files
    }
    total_units = 0
    total_math = 0
    total_images = 0
    total_tables = 0
    lesson12_main: Tag | None = None
    for component in EXPECTED_COMPONENTS:
        filename = "index.html" if component == "index" else f"{component}.html"
        payload = reader_payloads[PurePosixPath(filename)]
        if b"\xef\xbf\xbd" in payload:
            raise RuntimeError(f"{component} reader contains U+FFFD")
        soup = BeautifulSoup(payload, "html.parser")
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"{component} locale metadata differs")
        metadata = soup.select_one('meta[name="edition-status"]')
        provenance = soup.select_one('meta[name="translation-provenance"]')
        source_url = soup.select_one('meta[name="source-url"]')
        license_link = soup.select_one('link[rel~="license"]')
        stylesheet = soup.select_one('link[rel~="stylesheet"]')
        if (
            metadata is None
            or metadata.get("content") != EXPECTED_EDITION_STATUS
            or provenance is None
            or provenance.get("content") != PROVENANCE
            or source_url is None
            or not str(source_url.get("content") or "").startswith("https://online.stat.psu.edu/stat415")
            or license_link is None
            or license_link.get("href") != "https://creativecommons.org/licenses/by-nc/4.0/"
            or stylesheet is None
            or stylesheet.get("href") != "assets/reader-14of14.css"
        ):
            raise RuntimeError(f"{component} reader metadata differs")
        nav = soup.select_one("nav.site-nav")
        if nav is None or [str(link.get("href")) for link in nav.select("a[href]")] != expected_nav:
            raise RuntimeError(f"{component} reader navigation differs")
        edition_note = soup.select_one(".edition-note")
        footer = soup.select_one("footer.site-footer")
        if (
            edition_note is None
            or "14 dari 14 dokumen" not in edition_note.get_text(" ", strip=True)
            or footer is None
            or PROVENANCE not in footer.get_text(" ", strip=True)
            or "CC BY-NC 4.0" not in footer.get_text(" ", strip=True)
        ):
            raise RuntimeError(f"{component} visible status/provenance/license disclosure differs")
        main = soup.select_one("main#quarto-document-content")
        if main is None:
            raise RuntimeError(f"{component} reader main missing")
        segments, source_unit_count, math_count = EXPECTED_SOURCE_COUNTS[component]
        del segments
        document_id = EXPECTED_IDS[component]
        units = shared.stable_values(main, "data-o006-id")
        maths = shared.stable_values(main, "data-o006-math-id")
        source = BeautifulSoup(
            (ROOT / "source" / "normalized" / "en-US" / f"{component}.html").read_bytes(),
            "html.parser",
        ).select_one("main#quarto-document-content")
        target = BeautifulSoup(
            (ROOT / "source" / "id-ID" / f"{component}.html").read_bytes(),
            "html.parser",
        ).select_one("main#quarto-document-content")
        if source is None or target is None:
            raise RuntimeError(f"{component} normalized/localized main missing")
        source_units = shared.stable_values(source, "data-o006-id")
        target_units = shared.stable_values(target, "data-o006-id")
        source_maths = shared.stable_values(source, "data-o006-math-id")
        target_maths = shared.stable_values(target, "data-o006-math-id")
        component_removals = {
            unit_id for unit_id in registered_removals if unit_id.startswith(document_id + "-U")
        }
        expected_source_units = [
            f"{document_id}-U{i:04d}" for i in range(1, source_unit_count + 1)
        ]
        expected_target_sequence = [
            unit_id for unit_id in expected_source_units if unit_id not in component_removals
        ]
        expected_math_ids = [f"{document_id}-M{i:04d}" for i in range(1, math_count + 1)]
        if source_units != expected_source_units:
            raise RuntimeError(f"{component} normalized stable-unit sequence differs")
        if component == "Lesson00":
            if len(target_units) != len(expected_target_sequence) or set(target_units) != set(expected_target_sequence):
                raise RuntimeError(f"{component} target stable-unit topology differs")
        elif target_units != expected_target_sequence:
            raise RuntimeError(f"{component} target stable-unit sequence differs")
        if len(target_units) != EXPECTED_TARGET_UNITS[component] or units != target_units:
            raise RuntimeError(f"{component} reader/target stable-unit sequence differs")
        if (
            (component == "Lesson00" and source_maths)
            or (component != "Lesson00" and source_maths != expected_math_ids)
            or target_maths != expected_math_ids
            or maths != target_maths
        ):
            raise RuntimeError(f"{component} reader math sequence differs")
        if shared.native_id_duplicates(main):
            raise RuntimeError(f"{component} reader native IDs duplicate")
        if main.select("script, iframe, object, embed, video, audio, source"):
            raise RuntimeError(f"{component} reader retains an active/embed dependency")
        for image in main.select("img[data-o006-asset-id]"):
            if len(str(image.get("alt") or "").strip()) < 20:
                raise RuntimeError(f"{component} image alternative incomplete")
            if image.get("style") and re.search(r"(?:^|;)\s*width\s*:", str(image.get("style")).casefold()):
                raise RuntimeError(f"{component} image retains inline width")
        for node in soup.select("script[src], img[src], link[href]"):
            value = str(node.get("src") or node.get("href") or "")
            if value.startswith(("http://", "https://", "//")):
                if node.name == "link" and "license" in attribute_tokens(node.get("rel")):
                    continue
                raise RuntimeError(f"{component} external runtime/asset reference: {value}")
        if component == "Lesson12":
            lesson12_main = main
            if (
                soup.title is None
                or soup.title.get_text(" ", strip=True) != "12 Regresi Linear Sederhana"
                or main.select_one("h1") is None
                or main.select_one("h1").get_text(" ", strip=True) != "12 Regresi Linear Sederhana"
                or source_url.get("content") != "https://online.stat.psu.edu/stat415/Lesson12.html"
                or len(main.select("[data-o006-derived-math-id]")) != 8
            ):
                raise RuntimeError("Lesson12 clean reader identity differs")
        prose = visible_prose(main).casefold()
        forbidden = (
            "in this lesson",
            "the null hypothesis",
            "the alternative hypothesis",
            "confidence interval",
            "standard error",
            "power function",
            "sample size",
            "type i error",
            "type ii error",
            "hypothesis test",
            "test statistic",
            "critical value",
            "bayesian methods",
            "frequentist approach",
            "subjective probability",
            "credible intervals",
            "prior distribution",
            "posterior distribution",
            "solution",
            "example 11.",
            "example 12.",
        )
        present = [phrase for phrase in forbidden if phrase in prose]
        if present:
            raise RuntimeError(f"{component} visible untranslated phrase remains: {present}")
        total_units += len(units)
        total_math += len(maths)
        total_images += len(main.select("img[data-o006-asset-id]"))
        total_tables += len(main.select("table"))

    if lesson12_main is None:
        raise RuntimeError("Lesson12 reader main was not reached")
    lesson12 = lesson12_semantics_gate(lesson12_main, reader_mode=True)
    shared.validate_reader_links(reader_payloads)
    index = BeautifulSoup(reader_payloads[PurePosixPath("index.html")], "html.parser")
    for number in range(13):
        links = index.select(
            f'a[data-translation-status="complete"][href="Lesson{number:02d}.html"]'
        )
        if len(links) != 1:
            raise RuntimeError(f"index Lesson{number:02d} complete route differs")
    if index.select('a[data-translation-status="pending"]'):
        raise RuntimeError("complete index retains a pending route")
    if (
        total_units != 6_498
        or total_math != 3_156
        or total_images != 67
        or total_tables != 14
    ):
        raise RuntimeError(
            "cumulative reader structural census differs: "
            f"units={total_units} math={total_math} images={total_images} tables={total_tables}"
        )

    license_payload = reader_payloads[PurePosixPath("licenses/index.html")]
    if b"\xef\xbf\xbd" in license_payload:
        raise RuntimeError("license reader contains U+FFFD")
    license_text = license_payload.decode("utf-8", errors="strict").casefold()
    for phrase in (
        "pelajaran 00–12 lengkap",
        "seluruh empat belas dokumen",
        "cc by-nc 4.0",
        PROVENANCE.casefold(),
        "dua puluh empat koreksi atau disposisi lesson 12",
        "sembilan png unik dalam sepuluh kemunculan lesson 12",
        "tiga iframe video eksternal tidak dibundel",
        "tidak ada relisensi seragam",
    ):
        if phrase not in license_text:
            raise RuntimeError(f"license/status/provenance disclosure missing: {phrase}")
    license_soup = BeautifulSoup(license_payload, "html.parser")
    expected_license_nav = [
        "../index.html", *[f"../Lesson{i:02d}.html" for i in range(13)]
    ]
    nav = license_soup.select_one("nav.site-nav")
    stylesheet = license_soup.select_one('link[rel~="stylesheet"]')
    if (
        nav is None
        or [str(link.get("href")) for link in nav.select("a[href]")] != expected_license_nav
        or stylesheet is None
        or stylesheet.get("href") != "../assets/reader-14of14.css"
    ):
        raise RuntimeError("license reader navigation/stylesheet differs")
    return {
        "files": len(reader_files),
        "bytes": sum(len(payload) for payload in reader_payloads.values()),
        "stable_units": total_units,
        "source_units": 6_510,
        "math_nodes": total_math,
        "additive_derived_math_nodes": 8,
        "substantive_images": total_images,
        "tables": total_tables,
        "responsive_css": identity(css_path),
        "registered_removed_units": {
            correction_id: sorted(unit_ids)
            for correction_id, unit_ids in sorted(removals_by_correction.items())
        },
        "lesson12": lesson12,
    }


def asset_rights_privacy_gate(build_receipt: dict[str, object]) -> dict[str, object]:
    freeze_payload = ASSET_FREEZE_RECEIPT.read_bytes()
    canonical_text_gate(freeze_payload, "Lesson12 asset-freeze receipt")
    freeze = json.loads(freeze_payload.decode("utf-8"))
    external = freeze.get("external_video_boundary", {})
    if (
        freeze.get("schema") != "o006.stat415.lesson12-asset-freeze.v1"
        or freeze.get("status") != "pass"
        or freeze.get("document_id") != DOCUMENT_ID
        or freeze.get("component_id") != COMPONENT_ID
        or freeze.get("asset_count") != 9
        or freeze.get("asset_occurrences") != 10
        or freeze.get("total_bytes") != 233_075
        or not matches_identity(freeze.get("manifest"), ASSET_MANIFEST)
        or external.get("count") != 3
        or external.get("binary_bytes_downloaded") is not False
        or external.get("binary_bytes_redistributed") is not False
    ):
        raise RuntimeError("Lesson12 frozen-asset/video boundary differs")
    manifest_rows, _, _ = load_csv(ASSET_MANIFEST, "Lesson12 asset manifest")
    assets = build_receipt.get("new_assets", {}).get("inventory", [])
    if not isinstance(assets, list) or len(assets) != 9:
        raise RuntimeError("Lesson12 reader asset inventory differs")
    inventory = {str(row.get("asset_id")): row for row in assets if isinstance(row, dict)}
    if list(inventory) != [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, 10)]:
        raise RuntimeError("Lesson12 reader asset inventory sequence differs")
    occurrences = 0
    total_bytes = 0
    for manifest_row in manifest_rows:
        asset_id = manifest_row["asset_id"]
        row = inventory[asset_id]
        source = ROOT / manifest_row["local_path"]
        target = BUILD.joinpath(*PurePosixPath(str(row.get("target_path"))).parts)
        source_data = source.read_bytes()
        target_data = target.read_bytes()
        expected_occurrences = 2 if asset_id == f"{DOCUMENT_ID}-A0006" else 1
        if (
            row.get("official_url") != manifest_row["official_url"]
            or row.get("source_path") != manifest_row["local_path"]
            or row.get("target_path")
            != (PurePosixPath("assets/lesson12") / PurePosixPath(manifest_row["source_reference"])).as_posix()
            or source_data != target_data
            or len(source_data) != int(manifest_row["bytes"])
            or sha256(source_data) != manifest_row["sha256"]
            or row.get("source_bytes") != len(source_data)
            or row.get("target_bytes") != len(target_data)
            or row.get("source_sha256") != sha256(source_data)
            or row.get("target_sha256") != sha256(target_data)
            or row.get("target_is_byte_preserving") is not True
            or row.get("occurrences") != expected_occurrences
            or row.get("width") != int(manifest_row["width"])
            or row.get("height") != int(manifest_row["height"])
            or row.get("license") != manifest_row["license"]
        ):
            raise RuntimeError(f"Lesson12 asset byte/rights closure differs: {asset_id}")
        occurrences += expected_occurrences
        total_bytes += len(source_data)
    new_assets = build_receipt.get("new_assets", {})
    rights = build_receipt.get("rights", {})
    offline = build_receipt.get("offline", {})
    if (
        occurrences != 10
        or total_bytes != 233_075
        or new_assets.get("count") != 9
        or new_assets.get("occurrences") != 10
        or new_assets.get("bytes") != 233_075
        or new_assets.get("all_byte_preserving") is not True
        or rights.get("Penn State content") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
        or "nine same-origin PNG files in ten occurrences" not in str(rights.get("Lesson12 assets") or "")
        or "no video bytes downloaded or redistributed" not in str(rights.get("Lesson12 external videos") or "")
        or offline.get("external_runtime_requests") != 0
        or offline.get("offline_video_equivalents") != 3
        or offline.get("video_bytes_redistributed") is not False
    ):
        raise RuntimeError("Lesson12 cumulative asset/rights/offline receipt differs")

    sensitive = re.compile(
        r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        r"Bearer\s+[A-Za-z0-9._-]{16,}|C:\\Users\\|/Users/|"
        r"Downloads[/\\].*token|zenodo.*token|figshare.*token)",
        re.IGNORECASE,
    )
    scanned = 0
    for path in shared.current_reader_files():
        if path.suffix.lower() not in {".html", ".css", ".js", ".txt", ".csv", ".json", ".svg"}:
            continue
        text = BUILD.joinpath(*path.parts).read_text("utf-8", errors="ignore")
        if sensitive.search(text):
            raise RuntimeError(f"sensitive/local path surface found: {path}")
        scanned += 1
    return {
        "authority_assets": 9,
        "authority_asset_occurrences": 10,
        "authority_asset_bytes": total_bytes,
        "byte_preserving_targets": 9,
        "offline_video_equivalents": 3,
        "video_bytes_redistributed": False,
        "text_files_privacy_scanned": scanned,
        "rights": "CC BY-NC 4.0 except where otherwise noted",
        "external_runtime_dependencies": 0,
        "asset_manifest": identity(ASSET_MANIFEST),
        "asset_freeze_receipt": identity(ASSET_FREEZE_RECEIPT),
    }


def documents_manifest_gate(
    reader_files: set[PurePosixPath], build_receipt: dict[str, object]
) -> dict[str, object]:
    rows = parse_jsonl(DOCUMENTS.read_bytes(), "document backend")
    if len(rows) != 14 or [row.get("component_id") for row in rows] != EXPECTED_COMPONENTS:
        raise RuntimeError("document backend sequence differs")
    if (
        [int(row["translation_segments"]) for row in rows]
        != [EXPECTED_SOURCE_COUNTS[component][0] for component in EXPECTED_COMPONENTS]
        or [int(row["structural_units"]) for row in rows]
        != [EXPECTED_SOURCE_COUNTS[component][1] for component in EXPECTED_COMPONENTS]
        or [int(row["math_nodes"]) for row in rows]
        != [EXPECTED_SOURCE_COUNTS[component][2] for component in EXPECTED_COMPONENTS]
        or sum(int(row["translation_segments"]) for row in rows) != 4_932
        or sum(int(row["structural_units"]) for row in rows) != 6_510
        or sum(int(row["math_nodes"]) for row in rows) != 3_156
    ):
        raise RuntimeError("document backend cumulative census differs")
    for row in rows:
        target = ROOT / str(row["target_path"])
        data = target.read_bytes()
        if row.get("target_bytes") != len(data) or row.get("target_sha256") != sha256(data):
            raise RuntimeError(f"document target identity differs: {row.get('component_id')}")
    reader = {path: BUILD.joinpath(*path.parts).read_bytes() for path in reader_files}
    expected_manifest = first.manifest_payload(reader)
    manifest_payload = MANIFEST.read_bytes()
    if manifest_payload != expected_manifest:
        raise RuntimeError("reader manifest differs from exact builder inventory")
    manifest_rows, manifest_fields, _ = load_csv(MANIFEST, "Lesson12 reader manifest")
    if (
        manifest_fields != ["relative_path", "bytes", "sha256"]
        or len(manifest_rows) != EXPECTED_READER_FILES
        or len({row.get("relative_path") for row in manifest_rows}) != EXPECTED_READER_FILES
    ):
        raise RuntimeError("reader manifest path inventory differs")
    for row in manifest_rows:
        path = PurePosixPath(str(row["relative_path"]))
        payload = reader.get(path)
        if payload is None or int(row["bytes"]) != len(payload) or row["sha256"] != sha256(payload):
            raise RuntimeError(f"reader manifest identity differs: {path}")
    receipt_reader = build_receipt.get("reader", {})
    if (
        receipt_reader.get("manifest_path") != MANIFEST.relative_to(ROOT).as_posix()
        or receipt_reader.get("manifest_bytes") != len(manifest_payload)
        or receipt_reader.get("manifest_sha256") != sha256(manifest_payload)
        or receipt_reader.get("files") != EXPECTED_READER_FILES
        or receipt_reader.get("bytes") != sum(len(payload) for payload in reader.values())
    ):
        raise RuntimeError("reader manifest receipt differs")
    return {
        "documents": len(rows),
        "backend": identity(DOCUMENTS),
        "manifest": identity(MANIFEST),
        "manifest_fields": manifest_fields,
        "manifest_entries": len(manifest_rows),
        "manifest_matches_exact_reader_inventory": True,
    }


def compute() -> bytes:
    pipeline = pipeline_replay_gate()
    _, build_receipt, reader_files = deterministic_build_gate()
    glossary = glossary_gate()
    translation = translation_backend_gate(build_receipt, glossary)
    structure = materialization_and_corrections_gate()
    reader = reader_gate(reader_files, build_receipt)
    assets = asset_rights_privacy_gate(build_receipt)
    documents = documents_manifest_gate(reader_files, build_receipt)
    receipt = {
        "schema": "o006.stat415.through-lesson12-qa.v1",
        "status": "passed",
        "coverage": {
            "complete_documents": 14,
            "corpus_documents": 14,
            "next_document": None,
            "pending_documents": [],
        },
        "pipeline_check_only_replay": pipeline,
        "glossary": glossary,
        "translation_backend": translation,
        "structure_math_corrections": structure,
        "reader_accessibility_reflow": reader,
        "asset_rights_privacy": assets,
        "documents_manifest": documents,
        "build_receipt": identity(BUILD_RECEIPT),
        "checks": [
            "asset-freeze-normalization-batches-merge-materialization-and-build-check-only-replayed",
            "exact-580-Lesson12-source-target-binding-and-translation-receipt-replay",
            "exact-cumulative-4932-segment-backend",
            "exact-846-Lesson12-stable-unit-and-352-source-math-identity-order",
            "only-nineteen-registered-Lesson12-source-mathematics-surfaces-change",
            "exact-contiguous-242-correction-registry-with-24-Lesson12-findings-0219-through-0242",
            "historical-twelve-registered-unit-removals-preserved-and-none-added-in-Lesson12",
            "six-Lesson12-tables-captioned-with-complete-row-and-column-scopes",
            "nine-unique-Lesson12-images-ten-occurrences-byte-closed-centered-and-full-width",
            "three-offline-video-equivalents-and-zero-active-embeds",
            "sixteen-duplicate-native-ID-occurrences-reversibly-mapped",
            "deterministic-recalculation-recorded-for-conflicting-source-numerics",
            "14-of-14-locale-status-provenance-navigation-ID-and-license-metadata",
            "exact-cumulative-6510-source-unit-6498-target-unit-3156-source-math-census",
            "no-external-runtime-analytics-cookie-or-iframe",
            "sensitive-and-local-path-scan-clear",
            "exact-192-row-glossary-through-O006-TERM-0192",
            "deterministic-106-file-reader-and-exact-manifest-replay",
        ],
    }
    return canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payload = compute()
    if args.write:
        atomic_write(QA_RECEIPT, payload)
        state = "written"
    else:
        if not QA_RECEIPT.is_file() or QA_RECEIPT.read_bytes() != payload:
            raise RuntimeError("Lesson12 QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({
        "mode": state,
        "documents": data["coverage"]["complete_documents"],
        "segments": data["translation_backend"]["cumulative_segments"],
        "source_units": data["reader_accessibility_reflow"]["source_units"],
        "target_units": data["reader_accessibility_reflow"]["stable_units"],
        "math_nodes": data["reader_accessibility_reflow"]["math_nodes"],
        "corrections": data["structure_math_corrections"]["cumulative_corrections"],
        "reader_files": data["reader_accessibility_reflow"]["files"],
        "receipt_sha256": sha256(payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
