#!/usr/bin/env python3
"""Deterministic cumulative QA for the 12-of-14 STAT 415 id-ID reader."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson10 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON10_QA_RECEIPT.json"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON10_BUILD_RECEIPT.json"
MANIFEST = ROOT / "build" / "THROUGH_LESSON10_MANIFEST.csv"
DOCUMENTS = ROOT / "backend" / "through_lesson10_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson10_corrections.jsonl"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson10.html"
SEGMENTS = ROOT / "working" / "lesson10_segments.csv"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson10_translation.csv"
BINDINGS = ROOT / "backend" / "lesson10_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON10_TRANSLATION_RECEIPT.json"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_COMPONENTS = ["index", *[f"Lesson{i:02d}" for i in range(11)]]
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
}
EXPECTED_IDS = {
    "index": "O006-PSU-000",
    **{f"Lesson{i:02d}": f"O006-PSU-{i + 1:03d}" for i in range(11)},
}
LESSON10_ASSET_IDS = [f"O006-PSU-011-A{i:04d}" for i in range(1, 23)]
LESSON10_TABLE_GEOMETRY = {
    "O006-PSU-011-U0072": (15, 3),
    "O006-PSU-011-U0393": (3, 4),
}
LESSON10_CORRECTION_IDS = [f"O006-PSU-ADV-{i:04d}" for i in range(171, 199)]
EXPECTED_EDITION_STATUS = (
    "partial: 12 of 14 documents complete; landing and Lessons 00–10"
)


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
    return isinstance(record, dict) and all(record.get(k) == v for k, v in expected.items())


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def parse_jsonl(payload: bytes, label: str) -> list[dict[str, object]]:
    try:
        rows = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{label} contains a non-object")
    return rows


def deterministic_build_gate() -> tuple[
    dict[str, bytes], dict[str, object], set[PurePosixPath]
]:
    expected_builder_constants = {
        "segments": 540,
        "units": 625,
        "math": 369,
        "assets": 22,
        "asset_bytes": 8_313_758,
        "corrections": 28,
        "total_segments": 3_998,
        "total_units": 5_400,
        "target_units": 5_388,
        "total_math": 2_540,
        "total_corrections": 198,
        "reader_files": 94,
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
    }
    if actual_builder_constants != expected_builder_constants:
        raise RuntimeError("Lesson10 builder census contract differs")

    outputs, receipt, reader_files = builder.compute()
    for relative, payload in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"deterministic Lesson10 build differs: {relative}")
    if shared.current_reader_files() != reader_files:
        raise RuntimeError("reader inventory differs from deterministic Lesson10 build")

    coverage = receipt.get("coverage", {})
    math = receipt.get("math_nodes", {})
    corrections = receipt.get("corrections", {})
    reader = receipt.get("reader", {})
    assets = receipt.get("new_assets", {})
    layout = receipt.get("layout", {})
    offline = receipt.get("offline", {})
    rights = receipt.get("rights", {})
    inputs = receipt.get("inputs", {})
    asset_inventory = assets.get("inventory", []) if isinstance(assets, dict) else []
    removed_widths = sum(
        row.get("source_inline_style") != row.get("target_inline_style")
        for row in asset_inventory
        if isinstance(row, dict)
    )
    if (
        receipt.get("schema") != "o006.stat415.through-lesson10-build.v1"
        or receipt.get("status") != "built"
        or receipt.get("locale") != "id-ID"
        or receipt.get("translation_provenance") != PROVENANCE
        or coverage.get("complete_documents") != EXPECTED_COMPONENTS
        or coverage.get("complete_count") != 12
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson11"
        or receipt.get("translation_segments") != 3_998
        or receipt.get("structural_units_normalized") != 5_400
        or receipt.get("structural_units_target") != 5_388
        or math.get("Lesson10") != 369
        or math.get("total") != 2_540
        or corrections.get("count") != 198
        or corrections.get("through_lesson09_count") != 170
        or corrections.get("lesson10_count") != 28
        or reader.get("files") != 94
        or len(reader_files) != 94
        or assets.get("count") != 22
        or assets.get("bytes") != 8_313_758
        or assets.get("all_byte_preserving") is not True
        or not isinstance(asset_inventory, list)
        or len(asset_inventory) != 22
        or layout.get("reader_css_path") != "assets/reader-12of14.css"
        or layout.get("lesson10_inline_width_constraints_removed") != removed_widths
        or offline.get("external_runtime_requests") != 0
        or offline.get("analytics") is not False
        or offline.get("cookies") is not False
        or offline.get("local_mathjax") is not True
        or offline.get("third_party_iframes") != 0
        or rights.get("Penn State content")
        != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
        or "fourteen same-origin raster assets and eight same-origin SVG assets"
        not in str(rights.get("Lesson10 assets", ""))
        or not matches_identity(inputs.get("translation"), TRANSLATION_RECEIPT)
        or not matches_identity(inputs.get("builder"), Path(__file__).with_name("build_through_lesson10.py"))
        or not matches_identity(
            inputs.get("correction_module"), Path(__file__).with_name("lesson10_corrections.py")
        )
    ):
        raise RuntimeError("Lesson10 build receipt contract differs")
    return outputs, receipt, reader_files


def receipt_identity_gate(record: object, label: str) -> dict[str, object]:
    if not isinstance(record, dict) or not isinstance(record.get("path"), str):
        raise RuntimeError(f"{label} identity is missing")
    path = ROOT / str(record["path"])
    if not path.is_file() or not matches_identity(record, path):
        raise RuntimeError(f"{label} identity differs")
    return identity(path)


def translation_backend_gate(build_receipt: dict[str, object]) -> dict[str, object]:
    with SEGMENTS.open("r", encoding="utf-8", newline="") as stream:
        source_reader = csv.DictReader(stream)
        source_rows = list(source_reader)
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        target_reader = csv.DictReader(stream)
        target_rows = list(target_reader)
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson10 bindings")
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
        source_reader.fieldnames != expected_fields
        or target_reader.fieldnames != expected_fields
        or len(source_rows) != 540
        or len(target_rows) != 540
        or len(bindings) != 540
    ):
        raise RuntimeError("Lesson10 translation/backend census differs")

    for ordinal, (source, target, binding) in enumerate(
        zip(source_rows, target_rows, bindings), start=1
    ):
        segment_id = f"O006-PSU-011-S{ordinal:04d}"
        if source["segment_id"] != segment_id or target["segment_id"] != segment_id:
            raise RuntimeError(f"Lesson10 segment order differs: {segment_id}")
        for field in (
            "document_id",
            "component_id",
            "section_id",
            "source_sha256",
            "source_text",
        ):
            if target[field] != source[field]:
                raise RuntimeError(f"Lesson10 immutable translation field differs: {segment_id}")
        text = target["target_text"]
        source_text = source["source_text"]
        source_leading = source_text[: len(source_text) - len(source_text.lstrip())]
        source_trailing = source_text[len(source_text.rstrip()) :]
        target_leading = text[: len(text) - len(text.lstrip())]
        target_trailing = text[len(text.rstrip()) :]
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": segment_id,
            "document_id": "O006-PSU-011",
            "component_id": "Lesson10",
            "section_id": target["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": target["source_sha256"],
            "target_sha256": sha256(text.encode("utf-8")),
            "status": "translated",
        }
        if (
            target["status"] != "translated"
            or not text.strip()
            or "\ufffd" in text
            or (target_leading, target_trailing) != (source_leading, source_trailing)
            or binding != expected_binding
        ):
            raise RuntimeError(f"Lesson10 translation/backend binding differs: {segment_id}")

    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    if (
        receipt.get("schema") != "o006.stat415.lesson10-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document") != "Lesson10"
        or receipt.get("document_id") != "O006-PSU-011"
        or receipt.get("locale") != "id-ID"
        or receipt.get("segment_count") != 540
        or receipt.get("translation_provenance") != PROVENANCE
        or receipt.get("identical_segments") != []
        or not matches_identity(receipt.get("translation_csv"), TRANSLATIONS)
        or not matches_identity(receipt.get("bindings"), BINDINGS)
        or not matches_identity(receipt.get("template"), SEGMENTS)
        or not matches_identity(
            receipt.get("merge_script"), Path(__file__).with_name("merge_lesson10_translations.py")
        )
    ):
        raise RuntimeError("Lesson10 translation receipt differs")

    batches = receipt.get("batches")
    expected_batches = (
        ("A", 176, "O006-PSU-011-S0001", "O006-PSU-011-S0176"),
        ("B", 129, "O006-PSU-011-S0177", "O006-PSU-011-S0305"),
        ("C", 122, "O006-PSU-011-S0306", "O006-PSU-011-S0427"),
        ("D", 113, "O006-PSU-011-S0428", "O006-PSU-011-S0540"),
    )
    if not isinstance(batches, list) or len(batches) != 4:
        raise RuntimeError("Lesson10 translation batch receipt differs")
    batch_evidence: list[dict[str, object]] = []
    for row, (name, count, first_id, last_id) in zip(batches, expected_batches):
        if (
            not isinstance(row, dict)
            or row.get("batch") != name
            or row.get("segments") != count
            or row.get("range") != [first_id, last_id]
        ):
            raise RuntimeError(f"Lesson10 translation batch {name} differs")
        batch_evidence.append(receipt_identity_gate(row, f"Lesson10 batch {name}"))
    if sum(int(row["segments"]) for row in batches if isinstance(row, dict)) != 540:
        raise RuntimeError("Lesson10 translation batch total differs")

    for label in ("source_findings", "independent_math_audit"):
        receipt_identity_gate(receipt.get(label), f"Lesson10 {label}")
    for group_name in ("asset_inputs", "terminology_inputs"):
        group = receipt.get(group_name)
        if not isinstance(group, list) or not group:
            raise RuntimeError(f"Lesson10 {group_name} receipt differs")
        for ordinal, row in enumerate(group, start=1):
            receipt_identity_gate(row, f"Lesson10 {group_name} {ordinal}")

    inputs = build_receipt.get("inputs", {})
    if not matches_identity(inputs.get("translation"), TRANSLATION_RECEIPT):
        raise RuntimeError("Lesson10 build/translation receipt binding differs")
    return {
        "new_segments": 540,
        "cumulative_segments": 3_998,
        "translation": identity(TRANSLATIONS),
        "bindings": identity(BINDINGS),
        "translation_receipt": identity(TRANSLATION_RECEIPT),
        "batches": batch_evidence,
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


def structural_math_correction_gate() -> dict[str, object]:
    corrections = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    expected_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(1, 199)]
    if (
        len(corrections) != 198
        or [row.get("correction_id") for row in corrections] != expected_ids
    ):
        raise RuntimeError("cumulative correction registry differs")
    lesson10_rows = corrections[170:]
    expected_findings = [f"L10-D{i:03d}" for i in range(1, 29)]
    if (
        [row.get("correction_id") for row in lesson10_rows]
        != LESSON10_CORRECTION_IDS
        or [row.get("source_defect_id") for row in lesson10_rows]
        != expected_findings
    ):
        raise RuntimeError("Lesson10 correction/finding binding differs")
    for row in lesson10_rows:
        surfaces = row.get("surfaces")
        if (
            row.get("status") != "applied-target-only"
            or not isinstance(surfaces, list)
            or not surfaces
            or row.get("replacement_count") != len(surfaces)
            or not str(row.get("note") or "").strip()
        ):
            raise RuntimeError(f"Lesson10 correction record incomplete: {row.get('correction_id')}")

    source = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser").select_one(
        "main#quarto-document-content"
    )
    target_path = ROOT / "source" / "id-ID" / "Lesson10.html"
    target = BeautifulSoup(target_path.read_bytes(), "html.parser").select_one(
        "main#quarto-document-content"
    )
    if source is None or target is None:
        raise RuntimeError("Lesson10 source/target instructional main is missing")
    source_units = shared.stable_values(source, "data-o006-id")
    target_units = shared.stable_values(target, "data-o006-id")
    source_math_ids = shared.stable_values(source, "data-o006-math-id")
    target_math_ids = shared.stable_values(target, "data-o006-math-id")
    if (
        source_units != [f"O006-PSU-011-U{i:04d}" for i in range(1, 626)]
        or target_units != source_units
    ):
        raise RuntimeError("Lesson10 stable-unit identity/order differs")
    if (
        source_math_ids != [f"O006-PSU-011-M{i:04d}" for i in range(1, 370)]
        or target_math_ids != source_math_ids
    ):
        raise RuntimeError("Lesson10 math identity/order differs")
    source_math = {
        str(node.get("data-o006-math-id")): node.get_text()
        for node in source.select("[data-o006-math-id]")
    }
    target_math = {
        str(node.get("data-o006-math-id")): node.get_text()
        for node in target.select("[data-o006-math-id]")
    }
    changed = {key for key in source_math if source_math[key] != target_math[key]}
    registered = changed_math_ids_from_corrections(lesson10_rows, "O006-PSU-011")
    if changed != registered:
        raise RuntimeError(
            "Lesson10 changed/registered math differs: "
            f"unregistered={sorted(changed-registered)} "
            f"unchanged-registered={sorted(registered-changed)}"
        )

    source_native_ids = [str(node["id"]) for node in source.select("[id]")]
    source_duplicates = sorted(
        native_id for native_id, count in Counter(source_native_ids).items() if count > 1
    )
    if len(source_duplicates) != 19 or shared.native_id_duplicates(target):
        raise RuntimeError("Lesson10 duplicate-DOM-ID repair differs")
    source_id_witnesses = sorted(
        str(node.get("data-o006-source-native-id"))
        for node in target.select("[data-o006-source-native-id]")
    )
    if source_id_witnesses != source_duplicates:
        raise RuntimeError("Lesson10 duplicate-ID provenance witnesses differ")

    markers = {
        str(node.get("data-o006-correction-id"))
        for node in target.select("[data-o006-correction-id]")
    }
    if not markers or not markers.issubset(set(LESSON10_CORRECTION_IDS)):
        raise RuntimeError("Lesson10 target contains an unregistered correction marker")
    return {
        "cumulative_corrections": 198,
        "lesson10_corrections": 28,
        "backend": identity(CORRECTIONS),
        "stable_units": len(target_units),
        "math_nodes": len(target_math_ids),
        "changed_registered_math": sorted(changed),
        "source_duplicate_native_ids_repaired": source_duplicates,
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


def lesson10_accessibility_semantics(main: Tag) -> dict[str, object]:
    images = main.select("img[data-o006-asset-id]")
    if (
        len(images) != 22
        or [str(image.get("data-o006-asset-id")) for image in images]
        != LESSON10_ASSET_IDS
        or len(main.select("figure")) != 22
        or len(main.select("figcaption")) != 22
    ):
        raise RuntimeError("Lesson10 image/figure/caption census differs")
    for image in images:
        asset_id = str(image.get("data-o006-asset-id"))
        alt = str(image.get("alt") or "").strip()
        described_by = attribute_tokens(image.get("aria-describedby"))
        figure = image.find_parent("figure")
        if len(alt) < 20 or len(described_by) != 1 or figure is None:
            raise RuntimeError(f"Lesson10 image alternative/caption link incomplete: {asset_id}")
        caption_matches = main.select(f'figcaption[id="{described_by[0]}"]')
        if len(caption_matches) != 1:
            raise RuntimeError(f"Lesson10 image caption identity differs: {asset_id}")
        caption = caption_matches[0]
        if (
            caption.find_parent("figure") is not figure
            or len(caption.get_text(" ", strip=True)) < 20
            or caption.get("data-o006-correction-id") != "O006-PSU-ADV-0192"
        ):
            raise RuntimeError(f"Lesson10 substantive caption differs: {asset_id}")
        lightbox = image.find_parent("a", class_="lightbox")
        if lightbox is not None and lightbox.get("title") != caption.get_text(" ", strip=True):
            raise RuntimeError(f"Lesson10 lightbox/caption association differs: {asset_id}")

    tables = main.select("table")
    if len(tables) != 2 or {
        str(table.get("data-o006-id")) for table in tables
    } != set(LESSON10_TABLE_GEOMETRY):
        raise RuntimeError("Lesson10 table census differs")
    for table_index, table in enumerate(tables, start=1):
        table_id = str(table.get("data-o006-id"))
        rows = table.select("tr")
        expected_rows, expected_columns = LESSON10_TABLE_GEOMETRY[table_id]
        caption = table.find("caption", recursive=False)
        if (
            len(rows) != expected_rows
            or any(
                len(row.find_all(["th", "td"], recursive=False)) != expected_columns
                for row in rows
            )
            or caption is None
            or len(caption.get_text(" ", strip=True)) < 20
            or caption.get("data-o006-correction-id") != "O006-PSU-ADV-0193"
            or attribute_tokens(table.get("aria-describedby")) != [str(caption.get("id"))]
        ):
            raise RuntimeError(f"Lesson10 table caption/geometry differs: {table_id}")
        header_cells = rows[0].find_all(["th", "td"], recursive=False)
        if any(
            cell.name != "th" or cell.get("scope") != "col" or not cell.get("id")
            for cell in header_cells
        ):
            raise RuntimeError(f"Lesson10 column-header semantics differ: {table_id}")
        for row in rows[1:]:
            cells = row.find_all(["th", "td"], recursive=False)
            row_header = cells[0]
            if (
                row_header.name != "th"
                or row_header.get("scope") != "row"
                or not row_header.get("id")
            ):
                raise RuntimeError(f"Lesson10 row-header semantics differ: {table_id}")
            for column, cell in enumerate(cells[1:], start=1):
                expected_headers = [str(row_header.get("id")), str(header_cells[column].get("id"))]
                if cell.name != "td" or attribute_tokens(cell.get("headers")) != expected_headers:
                    raise RuntimeError(f"Lesson10 data-cell header binding differs: {table_id}")

    if (
        len(main.select("div.cell")) != 5
        or len(main.select("div.cell-code")) != 5
        or len(main.select("pre.sourceCode")) != 5
        or len(main.select("div.cell-output")) != 3
        or len(main.select("div.cell-output-stdout")) != 3
        or len(main.select("pre")) != 8
        or len(main.select("code")) != 9
    ):
        raise RuntimeError("Lesson10 code/output census differs")
    for node in main.select("pre, .sourceCode, .cell-output"):
        hidden = str(node.get("style") or "").casefold().replace(" ", "")
        if node.has_attr("hidden") or "display:none" in hidden:
            raise RuntimeError("Lesson10 code/output surface is hidden")

    source_main = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser").select_one(
        "main#quarto-document-content"
    )
    assert source_main is not None
    expected_pre_ids = [
        f"O006-PSU-011-U{value:04d}"
        for value in (542, 552, 564, 575, 593, 601, 608, 614)
    ]
    target_pres = main.select("pre[data-o006-id]")
    if [str(node.get("data-o006-id")) for node in target_pres] != expected_pre_ids:
        raise RuntimeError("Lesson10 ordered code/output identity topology differs")
    source_by_id = {
        str(node.get("data-o006-id")): node.get_text()
        for node in source_main.select("pre[data-o006-id]")
    }
    target_by_id = {
        str(node.get("data-o006-id")): node.get_text() for node in target_pres
    }
    d019_exceptions = {
        "O006-PSU-011-U0575",
        "O006-PSU-011-U0601",
        "O006-PSU-011-U0614",
    }
    if any(
        target_by_id[unit_id] != source_by_id[unit_id]
        for unit_id in expected_pre_ids
        if unit_id not in d019_exceptions
    ):
        raise RuntimeError("Lesson10 contains an unregistered code/output change")
    expected_corrected_outputs = {
        "O006-PSU-011-U0552": "[1] 4.062198e-05",
        "O006-PSU-011-U0601": "[1] -4.103913",
        "O006-PSU-011-U0614": "[1] 4.062196e-05",
    }
    if any(
        target_by_id[unit_id].strip() != expected
        for unit_id, expected in expected_corrected_outputs.items()
    ):
        raise RuntimeError("Lesson10 expected numeric output contract differs")
    correction_rows = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    d024 = correction_rows[193]
    d024_surfaces = d024.get("surfaces") if isinstance(d024, dict) else None
    runtime_surface = d024_surfaces[0] if isinstance(d024_surfaces, list) and d024_surfaces else None
    if (
        d024.get("correction_id") != "O006-PSU-ADV-0194"
        or not isinstance(runtime_surface, dict)
        or runtime_surface.get("surface") != "r-runtime-output-contract"
        or runtime_surface.get("registered_d019_exceptions") != sorted(d019_exceptions)
        or runtime_surface.get("expected_numeric_outputs")
        != {
            "O006-PSU-011-U0552": 4.062198e-05,
            "O006-PSU-011-U0601": -4.103913,
            "O006-PSU-011-U0614": 4.062196e-05,
        }
    ):
        raise RuntimeError("Lesson10 registered runtime/output evidence differs")
    runtime_notes = main.select(
        '[data-o006-correction-id="O006-PSU-ADV-0194"].runtime-disclosure'
    )
    runtime_text = " ".join(note.get_text(" ", strip=True) for note in runtime_notes).casefold()
    required_runtime_terms = (
        "r dasar",
        "versi r",
        "paket stats",
        "keluaran",
        "platform",
        "sessioninfo()",
    )
    if (
        len(runtime_notes) != 1
        or runtime_notes[0].get("role") != "note"
        or any(term not in runtime_text for term in required_runtime_terms)
    ):
        raise RuntimeError("Lesson10 base-R/runtime/expected-output disclosure differs")
    return {
        "images": len(images),
        "semantic_figures": len(main.select("figure")),
        "substantive_captions": len(main.select("figcaption")),
        "semantic_tables": len(tables),
        "source_code_blocks": len(main.select("pre.sourceCode")),
        "published_output_blocks": len(main.select("div.cell-output pre")),
        "runtime_disclosures": len(runtime_notes),
    }


def reader_gate(
    reader_files: set[PurePosixPath], build_receipt: dict[str, object]
) -> dict[str, object]:
    if len(reader_files) != 94:
        raise RuntimeError("reader file count differs")
    css_path = BUILD.joinpath(*builder.CURRENT_CSS.parts)
    css = css_path.read_bytes()
    css_text = re.sub(r"\s+", " ", css.decode("utf-8"))
    for rule in (
        "width: 100%",
        "max-width: 100%",
        "height: auto",
        "margin-inline: auto",
        "overflow-x: auto",
    ):
        if rule not in css_text:
            raise RuntimeError(f"responsive CSS rule missing: {rule}")
    if "Lessons 07–10" not in css_text:
        raise RuntimeError("Lesson10 cumulative responsive CSS label differs")
    layout = build_receipt.get("layout", {})
    if (
        layout.get("reader_css_path") != builder.CURRENT_CSS.as_posix()
        or layout.get("reader_css_bytes") != len(css)
        or layout.get("reader_css_sha256") != sha256(css)
    ):
        raise RuntimeError("Lesson10 responsive CSS receipt differs")

    total_units = 0
    total_math = 0
    total_images = 0
    total_tables = 0
    expected_nav = [
        "index.html",
        *[f"Lesson{i:02d}.html" for i in range(11)],
        "licenses/index.html",
    ]
    lesson10_main: Tag | None = None
    for component in EXPECTED_COMPONENTS:
        filename = "index.html" if component == "index" else f"{component}.html"
        payload = (BUILD / filename).read_bytes()
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
            or stylesheet.get("href") != "assets/reader-12of14.css"
        ):
            raise RuntimeError(f"{component} reader metadata differs")
        nav = soup.select_one("nav.site-nav")
        if nav is None or [str(link.get("href")) for link in nav.select("a[href]")] != expected_nav:
            raise RuntimeError(f"{component} reader navigation differs")
        main = soup.select_one("main#quarto-document-content")
        if main is None:
            raise RuntimeError(f"{component} reader main missing")
        expected_units, expected_math = EXPECTED_COUNTS[component]
        units = shared.stable_values(main, "data-o006-id")
        maths = shared.stable_values(main, "data-o006-math-id")
        if len(units) != expected_units or len(maths) != expected_math:
            raise RuntimeError(f"{component} reader unit/math census differs")
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
            "solution",
            "example 10.",
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
        if component == "Lesson10":
            lesson10_main = main
            if (
                soup.title is None
                or soup.title.get_text(" ", strip=True) != "10 Uji Hipotesis (Bagian II)"
                or main.select_one("h1") is None
                or main.select_one("h1").get_text(" ", strip=True)
                != "10 Uji Hipotesis (Bagian II)"
            ):
                raise RuntimeError("Lesson10 clean reader title differs")
        total_units += len(units)
        total_math += len(maths)
        total_images += len(main.select("img[data-o006-asset-id]"))
        total_tables += len(main.select("table"))

    if lesson10_main is None:
        raise RuntimeError("Lesson10 reader main was not reached")
    lesson10_semantics = lesson10_accessibility_semantics(lesson10_main)

    index = BeautifulSoup((BUILD / "index.html").read_bytes(), "html.parser")
    for number in range(13):
        expected = (
            f"Lesson{number:02d}.html"
            if number <= 10
            else f"https://online.stat.psu.edu/stat415/Lesson{number:02d}"
        )
        links = index.select(f'a[data-translation-status][href="{expected}"]')
        if len(links) != 1:
            raise RuntimeError(f"index Lesson{number:02d} route differs")
        status = "complete" if number <= 10 else "pending"
        if links[0].get("data-translation-status") != status:
            raise RuntimeError(f"index Lesson{number:02d} status differs")

    if total_units != 5_388 or total_math != 2_540 or total_images != 56 or total_tables != 7:
        raise RuntimeError("cumulative reader structural census differs")
    license_payload = (BUILD / "licenses" / "index.html").read_bytes()
    if b"\xef\xbf\xbd" in license_payload:
        raise RuntimeError("license reader contains U+FFFD")
    license_text = license_payload.decode("utf-8")
    for phrase in (
        "laman utama serta Pelajaran 00–10 lengkap",
        "Pelajaran 11–12 belum diterjemahkan",
        "CC BY-NC 4.0",
        PROVENANCE,
        "dua puluh delapan koreksi Lesson 10",
        "Empat belas aset raster dan delapan SVG Lesson 10",
        "tidak ada relisensi seragam",
    ):
        if phrase not in license_text:
            raise RuntimeError(f"license/status/provenance disclosure missing: {phrase}")
    license_soup = BeautifulSoup(license_payload, "html.parser")
    expected_license_nav = [
        "../index.html",
        *[f"../Lesson{i:02d}.html" for i in range(11)],
    ]
    nav = license_soup.select_one("nav.site-nav")
    if nav is None or [str(link.get("href")) for link in nav.select("a[href]")] != expected_license_nav:
        raise RuntimeError("license reader navigation differs")
    stylesheet = license_soup.select_one('link[rel~="stylesheet"]')
    if stylesheet is None or stylesheet.get("href") != "../assets/reader-12of14.css":
        raise RuntimeError("license reader stylesheet differs")
    return {
        "files": len(reader_files),
        "bytes": sum((BUILD.joinpath(*path.parts)).stat().st_size for path in reader_files),
        "stable_units": total_units,
        "math_nodes": total_math,
        "substantive_images": total_images,
        "tables": total_tables,
        "responsive_css": identity(css_path),
        "lesson10": lesson10_semantics,
    }


def asset_rights_privacy_gate(build_receipt: dict[str, object]) -> dict[str, object]:
    assets = build_receipt.get("new_assets", {}).get("inventory", [])
    if (
        not isinstance(assets, list)
        or len(assets) != 22
        or [row.get("asset_id") for row in assets if isinstance(row, dict)]
        != LESSON10_ASSET_IDS
    ):
        raise RuntimeError("Lesson10 asset evidence differs")
    total = 0
    for row in assets:
        if not isinstance(row, dict):
            raise RuntimeError("Lesson10 asset evidence contains a non-object")
        source = ROOT / str(row["source_path"])
        target = BUILD.joinpath(*PurePosixPath(str(row["target_path"])).parts)
        source_data = source.read_bytes()
        target_data = target.read_bytes()
        if (
            not str(row["source_path"]).startswith("authority/assets/stat415/lesson10/")
            or not str(row["target_path"]).startswith("assets/lesson10/")
            or not str(row.get("official_url") or "").startswith("https://online.stat.psu.edu/stat415/")
            or source_data != target_data
            or len(source_data) != int(row["source_bytes"])
            or len(target_data) != int(row["target_bytes"])
            or sha256(source_data) != row["source_sha256"]
            or sha256(target_data) != row["target_sha256"]
            or row.get("target_is_byte_preserving") is not True
        ):
            raise RuntimeError(f"Lesson10 asset byte preservation differs: {row['asset_id']}")
        total += len(source_data)
    if total != 8_313_758:
        raise RuntimeError("Lesson10 asset byte total differs")

    rights = build_receipt.get("rights", {})
    if (
        rights.get("Penn State content") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
        or "fourteen same-origin raster assets and eight same-origin SVG assets"
        not in str(rights.get("Lesson10 assets", ""))
    ):
        raise RuntimeError("Lesson10 rights disclosure differs")
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
        "authority_assets": len(assets),
        "authority_asset_bytes": total,
        "byte_preserving_targets": len(assets),
        "text_files_privacy_scanned": scanned,
        "rights": "CC BY-NC 4.0 except where otherwise noted",
        "external_runtime_dependencies": 0,
    }


def documents_manifest_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    rows = parse_jsonl(DOCUMENTS.read_bytes(), "document backend")
    if len(rows) != 12 or [row.get("component_id") for row in rows] != EXPECTED_COMPONENTS:
        raise RuntimeError("document backend sequence differs")
    if (
        sum(int(row["translation_segments"]) for row in rows) != 3_998
        or sum(int(row["structural_units"]) for row in rows) != 5_400
        or sum(int(row["math_nodes"]) for row in rows) != 2_540
    ):
        raise RuntimeError("document backend cumulative census differs")
    for row in rows:
        target = ROOT / str(row["target_path"])
        data = target.read_bytes()
        if row.get("target_bytes") != len(data) or row.get("target_sha256") != sha256(data):
            raise RuntimeError(f"document target identity differs: {row.get('component_id')}")
    reader = {path: BUILD.joinpath(*path.parts).read_bytes() for path in reader_files}
    expected_manifest = first.manifest_payload(reader)
    if MANIFEST.read_bytes() != expected_manifest:
        raise RuntimeError("reader manifest differs")
    return {
        "documents": len(rows),
        "backend": identity(DOCUMENTS),
        "manifest": identity(MANIFEST),
    }


def compute() -> bytes:
    _, build_receipt, reader_files = deterministic_build_gate()
    translation = translation_backend_gate(build_receipt)
    structure = structural_math_correction_gate()
    reader = reader_gate(reader_files, build_receipt)
    assets = asset_rights_privacy_gate(build_receipt)
    documents = documents_manifest_gate(reader_files)
    receipt = {
        "schema": "o006.stat415.through-lesson10-qa.v1",
        "status": "passed",
        "coverage": {
            "complete_documents": 12,
            "corpus_documents": 14,
            "next_document": "Lesson11",
        },
        "translation_backend": translation,
        "structure_math_corrections": structure,
        "reader_accessibility_reflow": reader,
        "asset_rights_privacy": assets,
        "documents_manifest": documents,
        "build_receipt": identity(BUILD_RECEIPT),
        "checks": [
            "exact-540-new-segment-source-target-binding-and-translation-receipt-replay",
            "exact-cumulative-3998-segment-backend",
            "exact-Lesson10-stable-unit-and-math-identity-order",
            "only-registered-Lesson10-mathematics-surfaces-change",
            "exact-contiguous-198-correction-registry-with-28-Lesson10-findings",
            "all-22-Lesson10-authority-assets-byte-preserved-and-rights-disclosed",
            "all-19-source-duplicate-native-identifiers-uniquified-with-provenance",
            "all-22-Lesson10-images-have-substantive-linked-alts-and-captions",
            "both-Lesson10-tables-captioned-and-fully-header-associated",
            "five-base-R-code-blocks-and-three-authority-output-snapshots-visible",
            "explicit-runtime-environment-and-expected-output-disclosure",
            "clean-Lesson10-title-and-zero-reader-U+FFFD",
            "12-of-14-locale-status-provenance-navigation-and-license-metadata",
            "full-width-centered-responsive-figure-code-table-reflow",
            "no-external-runtime-analytics-cookie-or-iframe",
            "sensitive-and-local-path-scan-clear",
            "deterministic-94-file-reader-and-manifest-replay",
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
            raise RuntimeError("Lesson10 QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": state,
                "documents": data["coverage"]["complete_documents"],
                "new_segments": data["translation_backend"]["new_segments"],
                "stable_units": data["reader_accessibility_reflow"]["stable_units"],
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
