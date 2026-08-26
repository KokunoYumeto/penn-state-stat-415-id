#!/usr/bin/env python3
"""Deterministic cumulative QA for the 13-of-14 STAT 415 id-ID reader."""

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
import build_through_lesson11 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON11_QA_RECEIPT.json"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON11_BUILD_RECEIPT.json"
MANIFEST = ROOT / "build" / "THROUGH_LESSON11_MANIFEST.csv"
DOCUMENTS = ROOT / "backend" / "through_lesson11_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson11_corrections.jsonl"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson11.html"
SEGMENTS = ROOT / "working" / "lesson11_segments.csv"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson11_translation.csv"
BINDINGS = ROOT / "backend" / "lesson11_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON11_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON11_NORMALIZATION_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
PORTRAIT = ROOT / "authority" / "assets" / "stat415" / "lesson11" / "assets" / "bayes.png"
NORMALIZE_SCRIPT = ROOT / "scripts" / "normalize_lesson11.py"
MERGE_SCRIPT = ROOT / "scripts" / "merge_lesson11_translations.py"
BUILD_SCRIPT = ROOT / "scripts" / "build_through_lesson11.py"
CORRECTION_MODULE = ROOT / "scripts" / "lesson11_corrections.py"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_COMPONENTS = ["index", *[f"Lesson{i:02d}" for i in range(12)]]
EXPECTED_COUNTS = {
    "index": (197, 0),
    "Lesson00": (363, 331),
    "Lesson01": (188, 169),
    "Lesson02": (228, 209),
    "Lesson03": (421, 440),
    "Lesson04": (335, 289),
    "Lesson05": (1_475, 108),
    "Lesson06": (149, 102),
    "Lesson07": (399, 148),
    "Lesson08": (594, 156),
    "Lesson09": (414, 219),
    "Lesson10": (625, 369),
    "Lesson11": (264, 264),
}
EXPECTED_IDS = {
    "index": "O006-PSU-000",
    **{f"Lesson{i:02d}": f"O006-PSU-{i + 1:03d}" for i in range(12)},
}
EXPECTED_EDITION_STATUS = (
    "partial: 13 of 14 documents complete; landing and Lessons 00–11"
)
EXPECTED_GLOSSARY_BYTES = 17_727
EXPECTED_GLOSSARY_SHA256 = (
    "1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65"
)
EXPECTED_GLOSSARY_ROWS = 168
LESSON11_CORRECTION_IDS = [f"O006-PSU-ADV-{i:04d}" for i in range(199, 219)]
LESSON11_MATH_EDIT_IDS = {
    "O006-PSU-012-M0057",
    "O006-PSU-012-M0118",
    "O006-PSU-012-M0134",
    "O006-PSU-012-M0253",
    "O006-PSU-012-M0263",
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
LESSON11_SOLUTION_UNIT_IDS = [
    "O006-PSU-012-U0064",
    "O006-PSU-012-U0100",
    "O006-PSU-012-U0131",
    "O006-PSU-012-U0151",
    "O006-PSU-012-U0189",
    "O006-PSU-012-U0227",
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def matches_identity(record: object, path: Path) -> bool:
    expected = identity(path)
    return isinstance(record, dict) and all(
        record.get(key) == value for key, value in expected.items()
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
    if (
        payload.startswith(b"\xef\xbb\xbf")
        or b"\r" in payload
        or not payload.endswith(b"\n")
    ):
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
        timeout=180,
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
        "normalization": replay_check_only(NORMALIZE_SCRIPT, "Lesson11 normalization"),
        "translation_merge": replay_check_only(MERGE_SCRIPT, "Lesson11 translation merge"),
        "cumulative_build": replay_check_only(BUILD_SCRIPT, "through-Lesson11 build"),
    }


def glossary_gate() -> dict[str, object]:
    data = GLOSSARY.read_bytes()
    if len(data) < EXPECTED_GLOSSARY_BYTES:
        raise RuntimeError("cumulative glossary is shorter than the Lesson11 boundary")
    prefix = data[:EXPECTED_GLOSSARY_BYTES]
    text = canonical_text_gate(prefix, "Lesson11 glossary prefix")
    if sha256(prefix) != EXPECTED_GLOSSARY_SHA256:
        raise RuntimeError("Lesson11 admitted glossary prefix differs")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    expected_ids = [f"O006-TERM-{i:04d}" for i in range(1, 169)]
    if (
        reader.fieldnames != ["term_id", "en_US", "id_ID", "decision"]
        or len(rows) != EXPECTED_GLOSSARY_ROWS
        or [row["term_id"] for row in rows] != expected_ids
        or rows[-1]["term_id"] != "O006-TERM-0168"
    ):
        raise RuntimeError("Lesson11 glossary sequence differs")
    return {
        "path": GLOSSARY.relative_to(ROOT).as_posix(),
        "bytes": EXPECTED_GLOSSARY_BYTES,
        "sha256": EXPECTED_GLOSSARY_SHA256,
        "rows": EXPECTED_GLOSSARY_ROWS,
        "last_term_id": "O006-TERM-0168",
        "scope": "immutable cumulative glossary prefix through the 18 Lesson 11 decisions",
    }


def deterministic_build_gate() -> tuple[
    dict[str, bytes], dict[str, object], set[PurePosixPath]
]:
    expected_builder_constants = {
        "segments": 354,
        "units": 264,
        "math": 264,
        "assets": 1,
        "asset_bytes": 142_195,
        "corrections": 20,
        "total_segments": 4_352,
        "total_units": 5_664,
        "target_units": 5_652,
        "total_math": 2_804,
        "total_corrections": 218,
        "reader_files": 96,
        "glossary_rows": 168,
    }
    actual_builder_constants = {
        "segments": builder.EXPECTED_SEGMENTS,
        "units": builder.EXPECTED_UNITS,
        "math": builder.EXPECTED_MATH,
        "assets": builder.EXPECTED_ASSETS,
        "asset_bytes": builder.EXPECTED_ASSET_BYTES,
        "corrections": builder.EXPECTED_CORRECTIONS,
        "total_segments": builder.EXPECTED_TOTAL_SEGMENTS,
        "total_units": builder.EXPECTED_TOTAL_UNITS,
        "target_units": builder.EXPECTED_TARGET_UNITS,
        "total_math": builder.EXPECTED_TOTAL_MATH,
        "total_corrections": builder.EXPECTED_TOTAL_CORRECTIONS,
        "reader_files": builder.EXPECTED_READER_FILES,
        "glossary_rows": builder.EXPECTED_GLOSSARY_ROWS,
    }
    if actual_builder_constants != expected_builder_constants:
        raise RuntimeError("Lesson11 builder census contract differs")

    outputs, receipt, reader_files = builder.compute()
    for relative, payload in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"deterministic Lesson11 build differs: {relative}")
    if shared.current_reader_files() != reader_files:
        raise RuntimeError("reader inventory differs from deterministic Lesson11 build")

    coverage = receipt.get("coverage", {})
    math = receipt.get("math_nodes", {})
    corrections = receipt.get("corrections", {})
    reader = receipt.get("reader", {})
    assets = receipt.get("new_assets", {})
    layout = receipt.get("layout", {})
    offline = receipt.get("offline", {})
    rights = receipt.get("rights", {})
    inputs = receipt.get("inputs", {})
    inventory = assets.get("inventory", []) if isinstance(assets, dict) else []
    removed_widths = sum(
        row.get("source_inline_style") != row.get("target_inline_style")
        for row in inventory
        if isinstance(row, dict)
    )
    lesson11_rights = str(rights.get("Lesson11 assets", "")).casefold()
    if (
        receipt.get("schema") != "o006.stat415.through-lesson11-build.v1"
        or receipt.get("status") != "built"
        or receipt.get("locale") != "id-ID"
        or receipt.get("translation_provenance") != PROVENANCE
        or coverage.get("complete_documents") != EXPECTED_COMPONENTS
        or coverage.get("complete_count") != 13
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson12"
        or receipt.get("translation_segments") != 4_352
        or receipt.get("structural_units_normalized") != 5_664
        or receipt.get("structural_units_target") != 5_652
        or math.get("Lesson11") != 264
        or math.get("total") != 2_804
        or corrections.get("count") != 218
        or corrections.get("through_lesson10_count") != 198
        or corrections.get("lesson11_count") != 20
        or reader.get("files") != 96
        or len(reader_files) != 96
        or reader.get("manifest_path") != MANIFEST.relative_to(ROOT).as_posix()
        or reader.get("manifest_bytes") != MANIFEST.stat().st_size
        or reader.get("manifest_sha256") != sha256(MANIFEST.read_bytes())
        or assets.get("count") != 1
        or assets.get("bytes") != 142_195
        or assets.get("all_byte_preserving") is not True
        or not isinstance(inventory, list)
        or len(inventory) != 1
        or layout.get("reader_css_path") != "assets/reader-13of14.css"
        or layout.get("lesson11_inline_width_constraints_removed") != removed_widths
        or removed_widths != 1
        or offline.get("external_runtime_requests") != 0
        or offline.get("analytics") is not False
        or offline.get("cookies") is not False
        or offline.get("local_mathjax") is not True
        or offline.get("third_party_iframes") != 0
        or rights.get("Penn State content")
        != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
        or "one" not in lesson11_rights
        or "portrait" not in lesson11_rights
        or "byte" not in lesson11_rights
        or not matches_identity(inputs.get("normalization"), NORMALIZATION_RECEIPT)
        or not matches_identity(inputs.get("translation"), TRANSLATION_RECEIPT)
        or not matches_identity(inputs.get("builder"), BUILD_SCRIPT)
        or not matches_identity(inputs.get("correction_module"), CORRECTION_MODULE)
    ):
        raise RuntimeError("Lesson11 build receipt contract differs")
    targets = receipt.get("target_documents")
    if not isinstance(targets, list) or len(targets) != 13:
        raise RuntimeError("Lesson11 target-document receipt differs")
    for record in targets:
        receipt_identity_gate(record, "Lesson11 target document")
    return outputs, receipt, reader_files


def translation_backend_gate(
    build_receipt: dict[str, object], glossary: dict[str, object]
) -> dict[str, object]:
    source_rows, source_fields, _ = load_csv(SEGMENTS, "Lesson11 segment template")
    target_rows, target_fields, _ = load_csv(TRANSLATIONS, "Lesson11 translation CSV")
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson11 bindings")
    expected_fields = [
        "segment_id",
        "document_id",
        "component_id",
        "section_id",
        "source_sha256",
        "source_text",
        "target_text",
        "status",
    ]
    if (
        source_fields != expected_fields
        or target_fields != expected_fields
        or len(source_rows) != 354
        or len(target_rows) != 354
        or len(bindings) != 354
    ):
        raise RuntimeError("Lesson11 translation/backend census differs")

    identical: list[str] = []
    for ordinal, (source, target, binding) in enumerate(
        zip(source_rows, target_rows, bindings), start=1
    ):
        segment_id = f"O006-PSU-012-S{ordinal:04d}"
        if source["segment_id"] != segment_id or target["segment_id"] != segment_id:
            raise RuntimeError(f"Lesson11 segment order differs: {segment_id}")
        for field in expected_fields[:6]:
            if target[field] != source[field]:
                raise RuntimeError(
                    f"Lesson11 immutable translation field differs: {segment_id}"
                )
        if sha256(source["source_text"].encode("utf-8")) != source["source_sha256"]:
            raise RuntimeError(f"Lesson11 source hash differs: {segment_id}")
        text = target["target_text"]
        source_leading = source["source_text"][:
            len(source["source_text"]) - len(source["source_text"].lstrip())
        ]
        source_trailing = source["source_text"][len(source["source_text"].rstrip()) :]
        target_leading = text[: len(text) - len(text.lstrip())]
        target_trailing = text[len(text.rstrip()) :]
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": segment_id,
            "document_id": "O006-PSU-012",
            "component_id": "Lesson11",
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
            raise RuntimeError(
                f"Lesson11 translation/backend binding differs: {segment_id}"
            )
        if source["source_text"] == text:
            identical.append(segment_id)

    receipt_payload = TRANSLATION_RECEIPT.read_bytes()
    canonical_text_gate(receipt_payload, "Lesson11 translation receipt")
    receipt = json.loads(receipt_payload.decode("utf-8"))
    validation = receipt.get("validation", {})
    if (
        receipt.get("schema") != "o006.stat415.lesson11-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document") != "Lesson11"
        or receipt.get("document_id") != "O006-PSU-012"
        or receipt.get("locale") != "id-ID"
        or receipt.get("segment_count") != 354
        or receipt.get("translated_status_count") != 354
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
        raise RuntimeError("Lesson11 translation receipt differs")

    batches = receipt.get("batches")
    expected_batches = (
        ("A", 48, "O006-PSU-012-S0001", "O006-PSU-012-S0048"),
        ("B", 238, "O006-PSU-012-S0049", "O006-PSU-012-S0286"),
        ("C", 68, "O006-PSU-012-S0287", "O006-PSU-012-S0354"),
    )
    if not isinstance(batches, list) or len(batches) != 3:
        raise RuntimeError("Lesson11 translation batch receipt differs")
    batch_evidence: list[dict[str, object]] = []
    for row, (name, count, first_id, last_id) in zip(batches, expected_batches):
        if (
            not isinstance(row, dict)
            or row.get("batch") != name
            or row.get("segments") != count
            or row.get("range") != [first_id, last_id]
        ):
            raise RuntimeError(f"Lesson11 translation batch {name} differs")
        batch_evidence.append(receipt_identity_gate(row, f"Lesson11 batch {name}"))
    if sum(int(row["segments"]) for row in batches) != 354:
        raise RuntimeError("Lesson11 translation batch total differs")

    terminology = receipt.get("terminology_inputs")
    if terminology != [glossary]:
        raise RuntimeError("Lesson11 translation glossary prefix differs")
    normalization_inputs = receipt.get("normalization_inputs")
    if not isinstance(normalization_inputs, list) or len(normalization_inputs) != 2:
        raise RuntimeError("Lesson11 normalization-input receipt differs")
    for ordinal, record in enumerate(normalization_inputs, start=1):
        receipt_identity_gate(record, f"Lesson11 normalization input {ordinal}")

    build_inputs = build_receipt.get("inputs", {})
    if not matches_identity(build_inputs.get("translation"), TRANSLATION_RECEIPT):
        raise RuntimeError("Lesson11 build/translation receipt binding differs")
    return {
        "new_segments": 354,
        "cumulative_segments": 4_352,
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
                raise RuntimeError(
                    f"registered stable-unit removal duplicates: {correction_id}"
                )
            found[correction_id] = set(removed_units)
    if found != EXPECTED_REMOVED_UNITS_BY_CORRECTION:
        raise RuntimeError(
            "registered stable-unit removals differ: "
            f"found={{{', '.join(f'{key!r}: {sorted(value)!r}' for key, value in sorted(found.items()))}}}"
        )
    return found


def structural_math_correction_gate() -> dict[str, object]:
    corrections = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    expected_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(1, 219)]
    if (
        len(corrections) != 218
        or [row.get("correction_id") for row in corrections] != expected_ids
    ):
        raise RuntimeError("cumulative correction registry differs")
    lesson11_rows = corrections[198:]
    expected_findings = [f"L11-D{i:03d}" for i in range(1, 21)]
    if (
        [row.get("correction_id") for row in lesson11_rows]
        != LESSON11_CORRECTION_IDS
        or [row.get("source_defect_id") for row in lesson11_rows]
        != expected_findings
    ):
        raise RuntimeError("Lesson11 correction/finding binding differs")
    for row in lesson11_rows:
        surfaces = row.get("surfaces")
        if (
            row.get("status") != "applied-target-only"
            or not isinstance(surfaces, list)
            or not surfaces
            or row.get("replacement_count") != len(surfaces)
            or not str(row.get("note") or "").strip()
        ):
            raise RuntimeError(
                f"Lesson11 correction record incomplete: {row.get('correction_id')}"
            )

    source = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser").select_one(
        "main#quarto-document-content"
    )
    target_path = ROOT / "source" / "id-ID" / "Lesson11.html"
    target = BeautifulSoup(target_path.read_bytes(), "html.parser").select_one(
        "main#quarto-document-content"
    )
    if source is None or target is None:
        raise RuntimeError("Lesson11 source/target instructional main is missing")
    expected_units = [f"O006-PSU-012-U{i:04d}" for i in range(1, 265)]
    expected_math = [f"O006-PSU-012-M{i:04d}" for i in range(1, 265)]
    source_units = shared.stable_values(source, "data-o006-id")
    target_units = shared.stable_values(target, "data-o006-id")
    source_math_ids = shared.stable_values(source, "data-o006-math-id")
    target_math_ids = shared.stable_values(target, "data-o006-math-id")
    if source_units != expected_units or target_units != source_units:
        raise RuntimeError("Lesson11 stable-unit identity/order differs")
    if source_math_ids != expected_math or target_math_ids != source_math_ids:
        raise RuntimeError("Lesson11 math identity/order differs")

    source_math = {
        str(node.get("data-o006-math-id")): node.get_text()
        for node in source.select("[data-o006-math-id]")
    }
    target_math = {
        str(node.get("data-o006-math-id")): node.get_text()
        for node in target.select("[data-o006-math-id]")
    }
    changed = {key for key in source_math if source_math[key] != target_math[key]}
    registered = changed_math_ids_from_corrections(lesson11_rows, "O006-PSU-012")
    if changed != LESSON11_MATH_EDIT_IDS or registered != LESSON11_MATH_EDIT_IDS:
        raise RuntimeError(
            "Lesson11 changed/registered math differs: "
            f"changed={sorted(changed)} registered={sorted(registered)}"
        )

    if shared.native_id_duplicates(source) or shared.native_id_duplicates(target):
        raise RuntimeError("Lesson11 source/target native IDs are not unique")
    markers = {
        str(node.get("data-o006-correction-id"))
        for node in target.select("[data-o006-correction-id]")
    }
    if not markers or not markers.issubset(set(LESSON11_CORRECTION_IDS)):
        raise RuntimeError("Lesson11 target contains an unregistered correction marker")
    return {
        "cumulative_corrections": 218,
        "lesson11_corrections": 20,
        "backend": identity(CORRECTIONS),
        "stable_units": len(target_units),
        "math_nodes": len(target_math_ids),
        "changed_registered_math": sorted(changed),
        "target_correction_markers": sorted(markers),
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


def attribute_tokens(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(token) for token in value]
    return str(value or "").split()


def lesson11_semantics(main: Tag, css_text: str) -> dict[str, object]:
    if len(main.select(".example")) != 7:
        raise RuntimeError("Lesson11 example census differs")
    original_solution_nodes: list[Tag] = []
    for unit_id in LESSON11_SOLUTION_UNIT_IDS:
        matches = main.select(f'[data-o006-id="{unit_id}"]')
        if len(matches) != 1:
            raise RuntimeError(f"Lesson11 solution heading differs: {unit_id}")
        original_solution_nodes.append(matches[0])
    added = main.select("h4#solusi-contoh-11-6.target-only-solution-heading")
    solution_nodes = [
        node
        for node in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if node.get_text(" ", strip=True).casefold() in {"penyelesaian", "solusi"}
    ]
    if (
        len(original_solution_nodes) != 6
        or len(added) != 1
        or added[0].get("data-o006-correction-id") != "O006-PSU-ADV-0209"
        or len(solution_nodes) != 7
    ):
        raise RuntimeError("Lesson11 seven-solution-heading repair differs")

    tables = main.select('table[data-o006-id="O006-PSU-012-U0041"]')
    if len(tables) != 1:
        raise RuntimeError("Lesson11 horse table census differs")
    table = tables[0]
    rows = table.select("tr")
    caption = table.find("caption", recursive=False)
    if (
        len(rows) != 6
        or any(len(row.find_all(["th", "td"], recursive=False)) != 2 for row in rows)
        or caption is None
        or len(caption.get_text(" ", strip=True)) < 20
        or attribute_tokens(table.get("aria-describedby")) != [str(caption.get("id"))]
        or len(rows[0].select('th[scope="col"]')) != 2
        or any(len(row.select('th[scope="row"]')) != 1 for row in rows[1:])
    ):
        raise RuntimeError("Lesson11 table caption/scope semantics differ")

    images = main.select('img[data-o006-asset-id="O006-PSU-012-A0001"]')
    figures = main.select('figure[data-o006-id="O006-PSU-012-U0018"]')
    if len(images) != 1 or len(figures) != 1:
        raise RuntimeError("Lesson11 portrait census differs")
    image = images[0]
    figure = figures[0]
    classes = set(attribute_tokens(image.get("class")))
    figure_classes = set(attribute_tokens(figure.get("class")))
    caption_node = figure.find("figcaption")
    if (
        image.get("src") != "assets/lesson11/assets/bayes.png"
        or image.get("style")
        or not {"lesson11-portrait", "reader-responsive-image"}.issubset(classes)
        or {"float-lg-end", "w-50", "ps-3"}.intersection(classes)
        or "reader-full-width-figure" not in figure_classes
        or len(str(image.get("alt") or "").strip()) < 30
        or caption_node is None
        or "Thomas Bayes" not in caption_node.get_text(" ", strip=True)
        or "main#quarto-document-content img[data-o006-asset-id]" not in css_text
        or "display: block" not in css_text
        or "margin-inline: auto" not in css_text
        or "height: auto" not in css_text
        or "max-width: 100%" not in css_text
    ):
        raise RuntimeError("Lesson11 centered responsive portrait differs")

    if (
        len(main.select("div.cell")) != 1
        or len(main.select("div.cell-code")) != 2
        or len(main.select("div.cell-output")) != 2
        or len(main.select("div.cell-output-stdout")) != 2
        or len(main.select("pre")) != 4
        or len(main.select("code")) != 4
    ):
        raise RuntimeError("Lesson11 qbeta code/output census differs")
    expected_pre = {
        "O006-PSU-012-U0237": "qbeta(0.05, shape1=4, shape2=4)",
        "O006-PSU-012-U0242": "[1] 0.2253216",
        "O006-PSU-012-U0247": "qbeta(0.95, shape1=4, shape2=4)",
        "O006-PSU-012-U0252": "[1] 0.7746784",
    }
    target_pre_nodes = main.select("pre[data-o006-id]")
    if any(len(node.find_all("code", recursive=False)) != 1 for node in target_pre_nodes):
        raise RuntimeError("Lesson11 Base-R pre/code topology differs")
    target_pre = {
        str(node.get("data-o006-id")): node.find("code", recursive=False).get_text().strip()
        for node in target_pre_nodes
    }
    source_main = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser").select_one(
        "main#quarto-document-content"
    )
    assert source_main is not None
    source_pre_nodes = source_main.select("pre[data-o006-id]")
    if any(len(node.find_all("code", recursive=False)) != 1 for node in source_pre_nodes):
        raise RuntimeError("Lesson11 source Base-R pre/code topology differs")
    source_pre = {
        str(node.get("data-o006-id")): node.find("code", recursive=False).get_text().strip()
        for node in source_pre_nodes
    }
    if target_pre != expected_pre or source_pre != expected_pre:
        raise RuntimeError("Lesson11 Base-R qbeta source/output contract differs")
    for node in main.select("pre, .sourceCode, .cell-output"):
        hidden = str(node.get("style") or "").casefold().replace(" ", "")
        if node.has_attr("hidden") or "display:none" in hidden:
            raise RuntimeError("Lesson11 qbeta code/output surface is hidden")
    runtime_notes = main.select(
        '[data-o006-correction-id="O006-PSU-ADV-0217"].r-runtime-note'
    )
    runtime_text = " ".join(
        note.get_text(" ", strip=True) for note in runtime_notes
    ).casefold()
    required_runtime_terms = (
        "base r",
        "stats::qbeta",
        "0,2253216",
        "0,7746784",
        "seed",
    )
    if (
        len(runtime_notes) != 1
        or runtime_notes[0].get("role") != "note"
        or any(term not in runtime_text for term in required_runtime_terms)
    ):
        raise RuntimeError("Lesson11 Base-R runtime/expected-output disclosure differs")
    return {
        "examples": 7,
        "solution_headings": 7,
        "semantic_tables": 1,
        "portrait_images": 1,
        "source_code_blocks": 2,
        "published_output_blocks": 2,
        "runtime_disclosures": 1,
    }


def reader_gate(
    reader_files: set[PurePosixPath], build_receipt: dict[str, object]
) -> dict[str, object]:
    if len(reader_files) != 96:
        raise RuntimeError("reader file count differs")
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
    if "Lessons 07–11" not in css_text:
        raise RuntimeError("Lesson11 cumulative responsive CSS label differs")
    layout = build_receipt.get("layout", {})
    if (
        builder.CURRENT_CSS != PurePosixPath("assets/reader-13of14.css")
        or layout.get("reader_css_path") != builder.CURRENT_CSS.as_posix()
        or layout.get("reader_css_bytes") != len(css)
        or layout.get("reader_css_sha256") != sha256(css)
    ):
        raise RuntimeError("Lesson11 responsive CSS receipt differs")

    total_units = 0
    total_math = 0
    total_images = 0
    total_tables = 0
    expected_nav = [
        "index.html",
        *[f"Lesson{i:02d}.html" for i in range(12)],
        "licenses/index.html",
    ]
    lesson11_main: Tag | None = None
    corrections = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    removals_by_correction = registered_removed_units_by_correction(corrections)
    registered_removals = set().union(*removals_by_correction.values())
    reader_payloads = {
        path: BUILD.joinpath(*path.parts).read_bytes() for path in reader_files
    }
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
            or not str(source_url.get("content") or "").startswith(
                "https://online.stat.psu.edu/stat415"
            )
            or license_link is None
            or license_link.get("href")
            != "https://creativecommons.org/licenses/by-nc/4.0/"
            or stylesheet is None
            or stylesheet.get("href") != "assets/reader-13of14.css"
        ):
            raise RuntimeError(f"{component} reader metadata differs")
        nav = soup.select_one("nav.site-nav")
        if nav is None or [str(link.get("href")) for link in nav.select("a[href]")] != expected_nav:
            raise RuntimeError(f"{component} reader navigation differs")
        main = soup.select_one("main#quarto-document-content")
        if main is None:
            raise RuntimeError(f"{component} reader main missing")
        expected_units, expected_math = EXPECTED_COUNTS[component]
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
            unit_id
            for unit_id in registered_removals
            if unit_id.startswith(document_id + "-U")
        }
        expected_source_units = [
            f"{document_id}-U{i:04d}"
            for i in range(1, expected_units + len(component_removals) + 1)
        ]
        expected_target_units = [
            unit_id for unit_id in expected_source_units if unit_id not in component_removals
        ]
        expected_math_ids = [
            f"{document_id}-M{i:04d}" for i in range(1, expected_math + 1)
        ]
        if source_units != expected_source_units:
            raise RuntimeError(f"{component} reader stable-unit sequence differs")
        if component == "Lesson00":
            # The registered Lesson 00 table repair changes DOM traversal order;
            # its historical gate therefore enforces exact membership, while the
            # target identity and the reader-to-target sequence remain exact.
            if (
                len(target_units) != len(expected_target_units)
                or set(target_units) != set(expected_target_units)
            ):
                raise RuntimeError(f"{component} reader stable-unit topology differs")
        elif target_units != expected_target_units:
            raise RuntimeError(f"{component} reader stable-unit sequence differs")
        if units != target_units:
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
        )
        present = [phrase for phrase in forbidden if phrase in prose]
        if present:
            raise RuntimeError(f"{component} visible untranslated phrase remains: {present}")
        for image in main.select("img[data-o006-asset-id]"):
            if len(str(image.get("alt") or "").strip()) < 20:
                raise RuntimeError(f"{component} image alternative incomplete")
            if image.get("style") and re.search(
                r"(?:^|;)\s*width\s*:", str(image.get("style")).casefold()
            ):
                raise RuntimeError(f"{component} image retains inline width")
        for node in soup.select("script[src], img[src], link[href]"):
            value = str(node.get("src") or node.get("href") or "")
            if value.startswith(("http://", "https://", "//")):
                if node.name == "link" and "license" in attribute_tokens(node.get("rel")):
                    continue
                raise RuntimeError(f"{component} external runtime/asset reference: {value}")
        if component == "Lesson11":
            lesson11_main = main
            if (
                soup.title is None
                or soup.title.get_text(" ", strip=True) != "11 Metode Bayesian"
                or main.select_one("h1") is None
                or main.select_one("h1").get_text(" ", strip=True)
                != "11 Metode Bayesian"
            ):
                raise RuntimeError("Lesson11 clean reader title differs")
        total_units += len(units)
        total_math += len(maths)
        total_images += len(main.select("img[data-o006-asset-id]"))
        total_tables += len(main.select("table"))

    if lesson11_main is None:
        raise RuntimeError("Lesson11 reader main was not reached")
    lesson11 = lesson11_semantics(lesson11_main, css_text)
    shared.validate_reader_links(reader_payloads)

    index = BeautifulSoup(reader_payloads[PurePosixPath("index.html")], "html.parser")
    for number in range(13):
        expected = (
            f"Lesson{number:02d}.html"
            if number <= 11
            else "https://online.stat.psu.edu/stat415/Lesson12"
        )
        links = index.select(f'a[data-translation-status][href="{expected}"]')
        if len(links) != 1:
            raise RuntimeError(f"index Lesson{number:02d} route differs")
        status = "complete" if number <= 11 else "pending"
        if links[0].get("data-translation-status") != status:
            raise RuntimeError(f"index Lesson{number:02d} status differs")

    if (
        total_units != 5_652
        or total_math != 2_804
        or total_images != 57
        or total_tables != 8
    ):
        raise RuntimeError("cumulative reader structural census differs")
    license_payload = reader_payloads[PurePosixPath("licenses/index.html")]
    if b"\xef\xbf\xbd" in license_payload:
        raise RuntimeError("license reader contains U+FFFD")
    license_text = license_payload.decode("utf-8", errors="strict")
    license_folded = license_text.casefold()
    for phrase in (
        "pelajaran 00–11 lengkap",
        "pelajaran 12 belum diterjemahkan",
        "cc by-nc 4.0",
        PROVENANCE.casefold(),
        "dua puluh koreksi lesson 11",
        "satu png potret lesson 11 dibekukan byte demi byte",
        "tidak ada relisensi seragam",
    ):
        if phrase not in license_folded:
            raise RuntimeError(f"license/status/provenance disclosure missing: {phrase}")
    license_soup = BeautifulSoup(license_payload, "html.parser")
    expected_license_nav = [
        "../index.html",
        *[f"../Lesson{i:02d}.html" for i in range(12)],
    ]
    nav = license_soup.select_one("nav.site-nav")
    if nav is None or [str(link.get("href")) for link in nav.select("a[href]")] != expected_license_nav:
        raise RuntimeError("license reader navigation differs")
    stylesheet = license_soup.select_one('link[rel~="stylesheet"]')
    if stylesheet is None or stylesheet.get("href") != "../assets/reader-13of14.css":
        raise RuntimeError("license reader stylesheet differs")
    return {
        "files": len(reader_files),
        "bytes": sum(len(payload) for payload in reader_payloads.values()),
        "stable_units": total_units,
        "source_units": 5_664,
        "math_nodes": total_math,
        "substantive_images": total_images,
        "tables": total_tables,
        "responsive_css": identity(css_path),
        "registered_removed_units": {
            correction_id: sorted(unit_ids)
            for correction_id, unit_ids in sorted(removals_by_correction.items())
        },
        "lesson11": lesson11,
    }


def asset_rights_privacy_gate(build_receipt: dict[str, object]) -> dict[str, object]:
    assets = build_receipt.get("new_assets", {}).get("inventory", [])
    if (
        not isinstance(assets, list)
        or len(assets) != 1
        or [row.get("asset_id") for row in assets if isinstance(row, dict)]
        != ["O006-PSU-012-A0001"]
    ):
        raise RuntimeError("Lesson11 portrait evidence differs")
    row = assets[0]
    if not isinstance(row, dict):
        raise RuntimeError("Lesson11 portrait evidence is not an object")
    source = ROOT / str(row["source_path"])
    target = BUILD.joinpath(*PurePosixPath(str(row["target_path"])).parts)
    source_data = source.read_bytes()
    target_data = target.read_bytes()
    if (
        source != PORTRAIT
        or str(row.get("target_path")) != "assets/lesson11/assets/bayes.png"
        or row.get("official_url")
        != "https://online.stat.psu.edu/stat415/assets/bayes.png"
        or source_data != target_data
        or len(source_data) != 142_195
        or len(target_data) != 142_195
        or len(source_data) != int(row["source_bytes"])
        or len(target_data) != int(row["target_bytes"])
        or sha256(source_data) != row["source_sha256"]
        or sha256(target_data) != row["target_sha256"]
        or row.get("target_is_byte_preserving") is not True
    ):
        raise RuntimeError("Lesson11 portrait byte preservation differs")

    rights = build_receipt.get("rights", {})
    rights_text = str(rights.get("Lesson11 assets", "")).casefold()
    if (
        rights.get("Penn State content")
        != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
        or "portrait" not in rights_text
        or "byte" not in rights_text
    ):
        raise RuntimeError("Lesson11 rights disclosure differs")
    sensitive = re.compile(
        r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
        r"Bearer\s+[A-Za-z0-9._-]{16,}|C:\\Users\\|/Users/|"
        r"Downloads[/\\].*token|zenodo.*token|figshare.*token)",
        re.IGNORECASE,
    )
    scanned = 0
    for path in shared.current_reader_files():
        if path.suffix.lower() not in {
            ".html",
            ".css",
            ".js",
            ".txt",
            ".csv",
            ".json",
            ".svg",
        }:
            continue
        text = BUILD.joinpath(*path.parts).read_text("utf-8", errors="ignore")
        if sensitive.search(text):
            raise RuntimeError(f"sensitive/local path surface found: {path}")
        scanned += 1
    return {
        "authority_assets": 1,
        "authority_asset_bytes": 142_195,
        "byte_preserving_targets": 1,
        "text_files_privacy_scanned": scanned,
        "rights": "CC BY-NC 4.0 except where otherwise noted",
        "external_runtime_dependencies": 0,
    }


def documents_manifest_gate(
    reader_files: set[PurePosixPath], build_receipt: dict[str, object]
) -> dict[str, object]:
    rows = parse_jsonl(DOCUMENTS.read_bytes(), "document backend")
    if len(rows) != 13 or [row.get("component_id") for row in rows] != EXPECTED_COMPONENTS:
        raise RuntimeError("document backend sequence differs")
    if (
        sum(int(row["translation_segments"]) for row in rows) != 4_352
        or sum(int(row["structural_units"]) for row in rows) != 5_664
        or sum(int(row["math_nodes"]) for row in rows) != 2_804
    ):
        raise RuntimeError("document backend cumulative census differs")
    for row in rows:
        target = ROOT / str(row["target_path"])
        data = target.read_bytes()
        if row.get("target_bytes") != len(data) or row.get("target_sha256") != sha256(data):
            raise RuntimeError(
                f"document target identity differs: {row.get('component_id')}"
            )
    reader = {path: BUILD.joinpath(*path.parts).read_bytes() for path in reader_files}
    expected_manifest = first.manifest_payload(reader)
    manifest_payload = MANIFEST.read_bytes()
    if manifest_payload != expected_manifest:
        raise RuntimeError("reader manifest differs")
    receipt_reader = build_receipt.get("reader", {})
    if (
        receipt_reader.get("manifest_path") != MANIFEST.relative_to(ROOT).as_posix()
        or receipt_reader.get("manifest_bytes") != len(manifest_payload)
        or receipt_reader.get("manifest_sha256") != sha256(manifest_payload)
    ):
        raise RuntimeError("reader manifest receipt differs")
    return {
        "documents": len(rows),
        "backend": identity(DOCUMENTS),
        "manifest": identity(MANIFEST),
        "manifest_matches_exact_reader_inventory": True,
    }


def compute() -> bytes:
    pipeline = pipeline_replay_gate()
    _, build_receipt, reader_files = deterministic_build_gate()
    glossary = glossary_gate()
    translation = translation_backend_gate(build_receipt, glossary)
    structure = structural_math_correction_gate()
    reader = reader_gate(reader_files, build_receipt)
    assets = asset_rights_privacy_gate(build_receipt)
    documents = documents_manifest_gate(reader_files, build_receipt)
    receipt = {
        "schema": "o006.stat415.through-lesson11-qa.v1",
        "status": "passed",
        "coverage": {
            "complete_documents": 13,
            "corpus_documents": 14,
            "next_document": "Lesson12",
            "pending_documents": ["Lesson12"],
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
            "normalization-translation-merge-and-cumulative-build-check-only-replayed",
            "exact-354-Lesson11-source-target-binding-and-translation-receipt-replay",
            "exact-cumulative-4352-segment-backend",
            "exact-264-Lesson11-stable-unit-and-math-identity-order",
            "only-five-registered-Lesson11-mathematics-surfaces-change",
            "exact-contiguous-218-correction-registry-with-20-Lesson11-findings-0199-through-0218",
            "one-142195-byte-Lesson11-portrait-preserved-byte-for-byte",
            "Lesson11-table-caption-and-row-column-scopes-complete",
            "Lesson11-portrait-centered-full-width-and-responsive",
            "seven-examples-and-seven-solution-headings-after-repair",
            "two-Base-R-qbeta-code-blocks-and-two-exact-output-snapshots-visible",
            "explicit-Base-R-runtime-and-qbeta-expected-output-contract",
            "13-of-14-locale-status-provenance-navigation-ID-and-license-metadata",
            "Lesson12-is-the-only-pending-document",
            "exact-cumulative-5664-source-unit-5652-target-unit-2804-math-census",
            "no-external-runtime-analytics-cookie-or-iframe",
            "sensitive-and-local-path-scan-clear",
            "glossary-prefix-through-at-least-O006-TERM-0168",
            "deterministic-96-file-reader-and-exact-manifest-replay",
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
            raise RuntimeError("Lesson11 QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": state,
                "documents": data["coverage"]["complete_documents"],
                "new_segments": data["translation_backend"]["new_segments"],
                "source_units": data["reader_accessibility_reflow"]["source_units"],
                "target_units": data["reader_accessibility_reflow"]["stable_units"],
                "math_nodes": data["reader_accessibility_reflow"]["math_nodes"],
                "corrections": data["structure_math_corrections"]["cumulative_corrections"],
                "reader_files": data["reader_accessibility_reflow"]["files"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
