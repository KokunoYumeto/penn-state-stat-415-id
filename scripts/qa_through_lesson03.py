#!/usr/bin/env python3
"""Independent deterministic QA for STAT 415 id-ID through Lesson 03."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString

import qa_through_lesson02 as prior


shared = prior.prior
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON03_MANIFEST.csv"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON03_BUILD_RECEIPT.json"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON03_QA_RECEIPT.json"
DOCUMENTS = ROOT / "backend" / "through_lesson03_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson03_corrections.jsonl"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson03_translation.csv"
SEGMENTS = ROOT / "working" / "lesson03_segments.csv"
BINDINGS = ROOT / "backend" / "lesson03_translation_bindings.jsonl"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON03_NORMALIZATION_RECEIPT.json"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON03_TRANSLATION_RECEIPT.json"
ZERO_ASSET_CLOSURE = ROOT / "working" / "lesson03_zero_asset_closure.json"
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

CONTENT = {
    "index": ("O006-PSU-000", 77, 197, 0, "https://online.stat.psu.edu/stat415/"),
    "Lesson00": ("O006-PSU-001", 446, 365, 331, "https://online.stat.psu.edu/stat415/Lesson00"),
    "Lesson01": ("O006-PSU-002", 221, 188, 169, "https://online.stat.psu.edu/stat415/Lesson01"),
    "Lesson02": ("O006-PSU-003", 324, 228, 209, "https://online.stat.psu.edu/stat415/Lesson02"),
    "Lesson03": ("O006-PSU-004", 531, 421, 440, "https://online.stat.psu.edu/stat415/Lesson03"),
}
EXPECTED_READER = (
    prior.EXPECTED_READER
    - {PurePosixPath("assets/reader-4of14.css")}
    | {PurePosixPath("assets/reader-5of14.css"), PurePosixPath("Lesson03.html")}
)
PARTS = {
    "a": (ROOT / "working" / "lesson03_translation_part_a.json", 1, 177),
    "b": (ROOT / "working" / "lesson03_translation_part_b.json", 178, 354),
    "c": (ROOT / "working" / "lesson03_translation_part_c.json", 355, 531),
}
PUNCTUATION_BOUNDARY_EXCEPTIONS = {
    "O006-PSU-004-S0246": ",",
    "O006-PSU-004-S0248": ",",
    "O006-PSU-004-S0306": ".",
    "O006-PSU-004-S0419": ",",
}
WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS = {
    "O006-PSU-004-S0135",
    "O006-PSU-004-S0137",
    "O006-PSU-004-S0208",
    "O006-PSU-004-S0209",
    "O006-PSU-004-S0263",
    "O006-PSU-004-S0501",
    "O006-PSU-004-S0504",
    "O006-PSU-004-S0521",
    "O006-PSU-004-S0523",
}
EXPECTED_CORRECTIONS = {f"O006-PSU-ADV-{number:04d}" for number in range(1, 47)}
EXPECTED_LESSON03_MATH_CHANGES = {
    "O006-PSU-004-M0086",
    "O006-PSU-004-M0105",
    "O006-PSU-004-M0143",
    "O006-PSU-004-M0173",
    "O006-PSU-004-M0199",
    "O006-PSU-004-M0209",
    "O006-PSU-004-M0216",
    "O006-PSU-004-M0226",
    "O006-PSU-004-M0258",
    "O006-PSU-004-M0290",
    "O006-PSU-004-M0299",
    "O006-PSU-004-M0302",
    "O006-PSU-004-M0304",
    "O006-PSU-004-M0311",
    "O006-PSU-004-M0318",
    "O006-PSU-004-M0345",
    "O006-PSU-004-M0389",
    "O006-PSU-004-M0401",
    "O006-PSU-004-M0402",
}
HISTORICAL = {
    "backend/through_lesson02_corrections.jsonl": (10143, "db6ec366a1461c545d4c1ca93b2a76664868bb4e99878a0719d8e9ab2a976c19"),
    "backend/through_lesson02_documents.jsonl": (2680, "22f36e9a27466c271b8a9b507d356f73246b1484e1d9d13439329fc932bca474"),
    "build/THROUGH_LESSON02_BUILD_RECEIPT.json": (6845, "f061911bb9dc8ab1c9f3a30701f00fcaf35ad96f260f49847d1c2d46cff4ee0e"),
    "build/THROUGH_LESSON02_MANIFEST.csv": (3081, "e0fe3c91465284cb10cf0bc802c32102bccb0eb0c84f108405a66044faf9f7ef"),
    "build/THROUGH_LESSON02_QA_RECEIPT.json": (11352, "79f83cf4e5690c1509c8c6fea415340c44b2513390955c62f42398bfe84dd14c"),
    "build/THROUGH_LESSON02_VISUAL_QA_RECEIPT.json": (7262, "ff88c85188969656be6bebb9a82504c148506baca7fba8bcdbe1738583f69d8e"),
}


def reader_manifest_gate() -> dict[str, object]:
    header, rows = shared.load_csv(MANIFEST)
    if header != ["relative_path", "bytes", "sha256"] or len(rows) != 32:
        raise RuntimeError("Lesson03 reader manifest schema or row count differs")
    paths: list[PurePosixPath] = []
    for row in rows:
        path = PurePosixPath(row["relative_path"])
        if path.is_absolute() or ".." in path.parts or path.as_posix() != row["relative_path"]:
            raise RuntimeError(f"unsafe reader path: {row['relative_path']}")
        if not HEX64.fullmatch(row["sha256"]):
            raise RuntimeError(f"malformed reader hash: {path}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise RuntimeError(f"malformed reader byte count: {path}") from exc
        raw = shared.require_file(BUILD / Path(path.as_posix()))
        if len(raw) != expected_bytes or shared.sha256(raw) != row["sha256"]:
            raise RuntimeError(f"reader identity differs: {path}")
        paths.append(path)
    if paths != sorted(paths, key=lambda value: value.as_posix().casefold()):
        raise RuntimeError("reader manifest order is not canonical")
    if len(paths) != len(set(paths)) or set(paths) != EXPECTED_READER:
        raise RuntimeError("reader manifest has a missing, extra, or duplicate file")
    actual = {
        PurePosixPath(path.relative_to(BUILD).as_posix())
        for path in BUILD.rglob("*")
        if path.is_file()
    }
    if actual != EXPECTED_READER:
        raise RuntimeError(
            f"reader tree differs; missing={sorted(EXPECTED_READER-actual, key=str)}, "
            f"extra={sorted(actual-EXPECTED_READER, key=str)}"
        )
    manifest_raw = shared.require_file(MANIFEST)
    return {
        "files": 32,
        "bytes": sum(int(row["bytes"]) for row in rows),
        "manifest_bytes": len(manifest_raw),
        "manifest_sha256": shared.sha256(manifest_raw),
    }


def load_pages() -> tuple[dict[PurePosixPath, BeautifulSoup], dict[str, BeautifulSoup]]:
    paths = [*(PurePosixPath(f"{name}.html") for name in CONTENT), PurePosixPath("licenses/index.html")]
    pages = {
        path: BeautifulSoup(shared.require_file(BUILD / Path(path.as_posix())), "html.parser")
        for path in paths
    }
    return pages, {name: pages[PurePosixPath(f"{name}.html")] for name in CONTENT}


def translation_gate() -> dict[str, object]:
    historical = prior.translation_gate()
    required = [
        "segment_id", "document_id", "component_id", "section_id",
        "source_sha256", "source_text", "target_text", "status",
    ]
    header, rows = shared.load_csv(TRANSLATIONS)
    template_header, template = shared.load_csv(SEGMENTS)
    if header != required or template_header != required or len(rows) != 531 or len(template) != 531:
        raise RuntimeError("Lesson03 translation/template schema or census differs")
    expected_ids = [f"O006-PSU-004-S{number:04d}" for number in range(1, 532)]
    if [row["segment_id"] for row in rows] != expected_ids or [row["segment_id"] for row in template] != expected_ids:
        raise RuntimeError("Lesson03 segment order differs")
    parts: dict[str, str] = {}
    part_counts: dict[str, int] = {}
    for name, (path, first, last) in PARTS.items():
        values = shared.load_json(path)
        expected = {f"O006-PSU-004-S{number:04d}" for number in range(first, last + 1)}
        if set(values) != expected or any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise RuntimeError(f"Lesson03 translation partition differs: {name}")
        if set(parts).intersection(values):
            raise RuntimeError("Lesson03 translation partitions overlap")
        parts.update({str(key): str(value) for key, value in values.items()})
        part_counts[name] = len(values)
    template_by_id = {row["segment_id"]: row for row in template}
    for row in rows:
        sid = row["segment_id"]
        source = row["source_text"]
        witness = template_by_id[sid]
        if any(row[field] != witness[field] for field in (
            "document_id", "component_id", "section_id", "source_sha256", "source_text"
        )):
            raise RuntimeError(f"Lesson03 source binding differs: {sid}")
        if row["document_id"] != "O006-PSU-004" or row["component_id"] != "Lesson03":
            raise RuntimeError(f"Lesson03 component identity differs: {sid}")
        if shared.sha256(source.encode("utf-8")) != row["source_sha256"]:
            raise RuntimeError(f"Lesson03 source hash differs: {sid}")
        leading = re.match(r"^\s*", source).group(0)
        trailing = re.search(r"\s*$", source).group(0)
        raw_target = parts[sid]
        if sid in PUNCTUATION_BOUNDARY_EXCEPTIONS:
            punctuation = PUNCTUATION_BOUNDARY_EXCEPTIONS[sid]
            if not raw_target.lstrip().startswith(punctuation) or (punctuation == "," and not leading):
                raise RuntimeError(f"Lesson03 punctuation-boundary exception differs: {sid}")
            leading = ""
        if sid in WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS:
            if not raw_target.startswith(" "):
                raise RuntimeError(f"Lesson03 word-boundary exception differs: {sid}")
            leading = " "
        expected_target = leading + raw_target.strip() + trailing
        if row["status"] != "translated" or row["target_text"] != expected_target:
            raise RuntimeError(f"Lesson03 target/partition differs: {sid}")
    bindings = shared.load_jsonl(BINDINGS)
    if len(bindings) != 531:
        raise RuntimeError("Lesson03 translation-binding census differs")
    for ordinal, (row, binding) in enumerate(zip(rows, bindings), start=1):
        expected = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": row["segment_id"],
            "document_id": "O006-PSU-004",
            "component_id": "Lesson03",
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": shared.sha256(row["target_text"].encode("utf-8")),
            "status": "translated",
        }
        if binding != expected:
            raise RuntimeError(f"Lesson03 translation binding differs: {row['segment_id']}")
    visible = "\n".join(row["target_text"] for row in rows).casefold()
    for term in (
        "statistik cukup", "teorema faktorisasi", "fungsi satu-satu", "bentuk eksponensial",
        "kriteria eksponensial", "metode momen", "momen teoretis", "momen sampel",
        "distribusi empiris",
    ):
        if term not in visible:
            raise RuntimeError(f"required Lesson03 term missing: {term}")
    for forbidden in (
        "statistik sufisien", "teorema pemfaktoran", "one-to-one function",
        "method of moments", "sample mean", "learning objectives", "factorization theorem",
        "sufficient statistics", "exponential criterion", "solution", "proof",
    ):
        if forbidden in visible:
            raise RuntimeError(f"visible Lesson03 English/superseded surface remains: {forbidden}")
    if "\ufffd" in visible:
        raise RuntimeError("Lesson03 target contains a replacement character")
    receipt_raw = shared.require_file(TRANSLATION_RECEIPT)
    if len(receipt_raw) != 3131 or shared.sha256(receipt_raw) != "d120e1d1b8248070450a4e3d314a890e4b38b199faab364ce525638038676bc6":
        raise RuntimeError("Lesson03 final translation receipt identity differs")
    receipt = shared.load_json(TRANSLATION_RECEIPT)
    if (
        receipt.get("schema") != "o006.stat415.lesson03-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("segment_count") != 531
        or receipt.get("translation_provenance") != PROVENANCE
        or receipt.get("word_boundary_leading_space_exceptions") != sorted(WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS)
    ):
        raise RuntimeError("Lesson03 translation receipt contract differs")
    expected_punctuation = [
        {"punctuation": value, "segment_id": key}
        for key, value in sorted(PUNCTUATION_BOUNDARY_EXCEPTIONS.items())
    ]
    if receipt.get("punctuation_boundary_exceptions") != expected_punctuation:
        raise RuntimeError("Lesson03 punctuation registry differs")
    for field, path in (("translation_csv", TRANSLATIONS), ("bindings", BINDINGS)):
        record = receipt.get(field)
        actual = shared.identity(path)
        if not isinstance(record, dict) or record.get("path") != actual["path"] or record.get("bytes") != actual["bytes"] or record.get("sha256") != actual["sha256"]:
            raise RuntimeError(f"Lesson03 translation receipt identity differs: {field}")
    return {
        "historical": historical,
        "lesson03_segments": 531,
        "cumulative_segments": 1599,
        "partition_counts": part_counts,
        "translation_csv": shared.identity(TRANSLATIONS),
        "bindings": shared.identity(BINDINGS),
        "receipt": shared.identity(TRANSLATION_RECEIPT),
        "source_bindings_exact": True,
        "punctuation_and_word_boundaries_exact": True,
    }


def normalization_gate() -> dict[str, object]:
    historical = prior.normalization_gate()
    receipt = shared.load_json(NORMALIZATION_RECEIPT)
    counts = receipt.get("counts")
    expected = {
        "asset_occurrences": 0, "assets": 0, "catalogue_records": 1393,
        "code_nodes": 0, "corollaries": 0, "definitions": 1, "examples": 11,
        "figure_captions": 0, "figures": 0, "headings": 26, "images": 0,
        "links": 4, "math_display": 91, "math_inline": 349, "math_nodes": 440,
        "native_id_occurrences": 41, "pre_nodes": 0, "proofs": 1,
        "sections": 25, "solutions": 11, "structural_units": 421,
        "tables": 0, "theorem_class_nodes": 14, "theorems": 2,
        "translation_segments": 531, "unique_asset_sources": 0, "unique_native_ids": 41,
    }
    if (
        receipt.get("schema") != "o006.stat415.lesson03-normalization.v1"
        or receipt.get("status") != "normalized-source-ready"
        or receipt.get("source_defect_count") != 17
        or not isinstance(counts, dict)
        or counts != expected
    ):
        raise RuntimeError("Lesson03 normalization receipt contract/census differs")
    defects = receipt.get("source_defects")
    if not isinstance(defects, list) or [row.get("defect_id") for row in defects if isinstance(row, dict)] != [f"L03-D{i:03d}" for i in range(1, 18)]:
        raise RuntimeError("Lesson03 source-defect registry differs")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Lesson03 normalization outputs missing")
    for field, expected_path in (
        ("normalized", "source/normalized/en-US/Lesson03.html"),
        ("catalogue", "backend/lesson03_source_catalogue.jsonl"),
        ("segments", "working/lesson03_segments.csv"),
        ("zero_asset_closure", "working/lesson03_zero_asset_closure.json"),
    ):
        shared.validate_identity_record(outputs.get(field), expected_path=expected_path, label=f"Lesson03 {field}")
    closure = shared.load_json(ZERO_ASSET_CLOSURE)
    census = closure.get("dependency_census")
    if (
        closure.get("schema") != "o006.stat415.lesson03-zero-asset-closure.v1"
        or closure.get("status") != "verified-zero-main-content-assets"
        or not isinstance(census, dict)
        or any(value != 0 for value in census.values())
    ):
        raise RuntimeError("Lesson03 zero-asset closure differs")
    return {
        "historical": historical,
        "lesson03_receipt": shared.identity(NORMALIZATION_RECEIPT),
        "source_structural_units": 1399,
        "lesson03_counts": expected,
        "source_defects": [f"L03-D{i:03d}" for i in range(1, 18)],
        "zero_asset_closure": shared.identity(ZERO_ASSET_CLOSURE),
    }


def corrections_and_math_gate(content_pages: dict[str, BeautifulSoup]) -> tuple[list[dict[str, object]], dict[str, object]]:
    historical_pages = {key: content_pages[key] for key in ("index", "Lesson00", "Lesson01", "Lesson02")}
    historical_rows = shared.load_jsonl(ROOT / "backend" / "through_lesson02_corrections.jsonl")
    historical_math = prior.corrections_and_math_gate(historical_pages)
    rows = shared.load_jsonl(CORRECTIONS)
    if len(rows) != 46 or {row.get("correction_id") for row in rows} != EXPECTED_CORRECTIONS:
        raise RuntimeError("cumulative correction registry differs")
    if rows[:29] != historical_rows:
        raise RuntimeError("one or more historical correction records changed")
    current = rows[29:]
    if [row.get("source_defect_id") for row in current] != [f"L03-D{i:03d}" for i in range(1, 18)]:
        raise RuntimeError("Lesson03 correction/defect binding differs")
    if [row.get("replacement_count") for row in current] != [1, 1, 1, 1, 1, 1, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2]:
        raise RuntimeError("Lesson03 correction replacement census differs")
    if any(row.get("status") != "applied-target-only" for row in current):
        raise RuntimeError("Lesson03 contains an unapplied correction")

    source_soup = BeautifulSoup(shared.require_file(NORMALIZED / "Lesson03.html"), "html.parser")
    source_main = source_soup.select_one("main#quarto-document-content")
    target_main = content_pages["Lesson03"].select_one("main#quarto-document-content")
    if source_main is None or target_main is None:
        raise RuntimeError("Lesson03 semantic main missing")
    source_units = [str(node["data-o006-id"]) for node in source_main.select("[data-o006-id]")]
    target_units = [str(node["data-o006-id"]) for node in target_main.select("[data-o006-id]")]
    if len(source_units) != 421 or source_units != target_units or len(set(source_units)) != 421:
        raise RuntimeError("Lesson03 stable-unit topology differs")
    source_nodes = source_main.select(".math")
    target_nodes = target_main.select(".math")
    source_ids = [str(node.get("data-o006-math-id", "")) for node in source_nodes]
    target_ids = [str(node.get("data-o006-math-id", "")) for node in target_nodes]
    if len(source_nodes) != 440 or source_ids != target_ids or len(set(source_ids)) != 440:
        raise RuntimeError("Lesson03 math-ID topology differs")
    source_by_id = {mid: node.get_text() for mid, node in zip(source_ids, source_nodes)}
    target_by_id = {mid: node.get_text() for mid, node in zip(target_ids, target_nodes)}
    actual_changes = {mid for mid in source_ids if source_by_id[mid] != target_by_id[mid]}
    if actual_changes != EXPECTED_LESSON03_MATH_CHANGES:
        raise RuntimeError("Lesson03 changed-math set differs from registered corrections")
    evidence: dict[str, tuple[str, str]] = {}
    for row in current:
        surfaces = row.get("surfaces")
        if surfaces is None and row.get("surface") == "math":
            surfaces = [row]
        if surfaces is not None:
            if not isinstance(surfaces, list):
                raise RuntimeError(f"correction surface evidence malformed: {row.get('correction_id')}")
            for surface in surfaces:
                if not isinstance(surface, dict):
                    raise RuntimeError(f"correction surface is not an object: {row.get('correction_id')}")
                mid = surface.get("math_id")
                before = surface.get("source_surface_sha256")
                after = surface.get("target_surface_sha256")
                if not isinstance(mid, str) or mid in evidence or not isinstance(before, str) or not isinstance(after, str) or not HEX64.fullmatch(before) or not HEX64.fullmatch(after):
                    raise RuntimeError(f"correction math evidence differs: {row.get('correction_id')}")
                evidence[mid] = (before, after)
    if set(evidence) != EXPECTED_LESSON03_MATH_CHANGES:
        raise RuntimeError("Lesson03 correction math-evidence set differs")
    for mid, (before, after) in evidence.items():
        if shared.sha256(source_by_id[mid].encode("utf-8")) != before or shared.sha256(target_by_id[mid].encode("utf-8")) != after:
            raise RuntimeError(f"Lesson03 correction surface hash differs: {mid}")

    by_defect = {str(row["source_defect_id"]): row for row in current}
    d005 = by_defect["L03-D005"]
    d008 = by_defect["L03-D008"]
    for defect, row, unit_id, math_ids in (
        ("L03-D005", d005, "O006-PSU-004-U0127", [f"O006-PSU-004-M{i:04d}" for i in range(152, 155)]),
        ("L03-D008", d008, "O006-PSU-004-U0140", [f"O006-PSU-004-M{i:04d}" for i in range(165, 169)]),
    ):
        units = target_main.select(f'[data-o006-id="{unit_id}"]')
        if len(units) != 1 or row.get("unit_id") != unit_id or row.get("protected_math_ids") != math_ids:
            raise RuntimeError(f"{defect} prose-unit identity differs")
        unit = units[0]
        if [str(node.get("data-o006-math-id")) for node in unit.select("[data-o006-math-id]")] != math_ids:
            raise RuntimeError(f"{defect} protected math topology differs")
        if row.get("target_unit_sha256") != shared.sha256(str(unit).encode("utf-8")):
            raise RuntimeError(f"{defect} target-unit evidence differs")
    d005_text = target_main.select_one('[data-o006-id="O006-PSU-004-U0127"]').get_text(" ", strip=True)
    if not all(fragment in d005_text for fragment in ("Sampel konstan", "rasio fungsi kemungkinan", "bergantung pada parameter", "tidak cukup")):
        raise RuntimeError("L03-D005 lacks the admitted likelihood-ratio counterexample")
    d008_text = target_main.select_one('[data-o006-id="O006-PSU-004-U0140"]').get_text(" ", strip=True)
    if not all(fragment in d008_text for fragment in ("mengalikan seluruh", "faktor yang memuat", "menjumlahkan seluruh", "pada eksponen")):
        raise RuntimeError("L03-D008 does not distinguish products from exponent sums")
    if d008.get("application_layer") != "translation-bindings":
        raise RuntimeError("L03-D008 correction layer differs")
    return rows, {
        "historical": historical_math,
        "source_stable_units": 1399,
        "target_stable_units": 1397,
        "math_nodes": 1149,
        "corrections": 46,
        "lesson03_corrections": 17,
        "lesson03_changed_math_surfaces": sorted(actual_changes),
        "d005_likelihood_ratio_counterexample": True,
        "d008_product_exponent_distinction": True,
        "correction_backend": shared.identity(CORRECTIONS),
    }


def document_and_language_gate(content_pages: dict[str, BeautifulSoup]) -> dict[str, object]:
    rows = shared.load_jsonl(DOCUMENTS)
    if len(rows) != 5 or [row.get("component_id") for row in rows] != list(CONTENT):
        raise RuntimeError("document backend coverage/order differs")
    result: dict[str, object] = {}
    global_units: list[str] = []
    global_math: list[str] = []
    total_target_units = 0
    for row, (component, (document_id, segments, source_units, math, url)) in zip(rows, CONTENT.items()):
        target_path = ROOT / "source" / "id-ID" / f"{component}.html"
        target_raw = shared.require_file(target_path)
        build_raw = shared.require_file(BUILD / f"{component}.html")
        page = content_pages[component]
        main = page.select_one("main#quarto-document-content")
        if target_raw != build_raw or main is None:
            raise RuntimeError(f"target/reader or semantic main differs: {component}")
        if (
            row.get("schema") != "o006.stat415.document.v1"
            or row.get("document_id") != document_id
            or row.get("locale") != "id-ID"
            or row.get("translation_status") != "complete"
            or row.get("translation_segments") != segments
            or row.get("structural_units") != source_units
            or row.get("math_nodes") != math
            or row.get("source_url") != url
            or row.get("source_path") != f"source/normalized/en-US/{component}.html"
            or row.get("target_path") != f"source/id-ID/{component}.html"
            or row.get("target_bytes") != len(target_raw)
            or row.get("target_sha256") != shared.sha256(target_raw)
        ):
            raise RuntimeError(f"document backend record differs: {component}")
        if page.html is None or page.html.get("lang") != "id-ID":
            raise RuntimeError(f"id-ID document metadata missing: {component}")
        provenance = page.select_one('meta[name="translation-provenance"]')
        status = page.select_one('meta[name="edition-status"]')
        source_meta = page.select_one('meta[name="source-url"]')
        if provenance is None or provenance.get("content") != PROVENANCE or status is None or "5 of 14" not in str(status.get("content")) or source_meta is None or source_meta.get("content") != url:
            raise RuntimeError(f"document provenance/status/source metadata differs: {component}")
        stable = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
        math_ids = [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")]
        native_ids = [str(node["id"]) for node in page.select("[id]")]
        if len(stable) != len(set(stable)) or len(math_ids) != math or len(math_ids) != len(set(math_ids)) or len(native_ids) != len(set(native_ids)):
            raise RuntimeError(f"duplicate or missing stable/native IDs: {component}")
        global_units.extend(stable)
        global_math.extend(math_ids)
        total_target_units += len(stable)
        result[component] = {"segments": segments, "source_units": source_units, "target_units": len(stable), "math_nodes": math}
    if total_target_units != 1397 or len(global_units) != len(set(global_units)) or len(global_math) != 1149 or len(global_math) != len(set(global_math)):
        raise RuntimeError("cumulative stable-ID topology differs")

    lesson = content_pages["Lesson03"]
    folded = lesson.get_text(" ", strip=True).casefold()
    for required in (
        "Pendugaan (Bagian II)", "Gambaran Umum", "Tujuan", "Kecukupan",
        "Definisi Kecukupan", "Teorema Faktorisasi", "Bentuk Eksponensial",
        "Dua Parameter atau Lebih", "Metode Momen", "Ringkasan",
    ):
        if required.casefold() not in folded:
            raise RuntimeError(f"Lesson03 Indonesian semantic surface missing: {required}")
    for forbidden in (
        "Learning Objectives", "Sufficiency", "Definition of Sufficiency",
        "Factorization Theorem", "One-to-One Functions", "The Exponential Family",
        "The Exponential Criterion", "Method of Moments", "Finding M.M.E.",
        "Another Form of This Method", "Solution", "Proof", "Example 3.",
    ):
        if forbidden.casefold() in folded:
            raise RuntimeError(f"visible Lesson03 English surface remains: {forbidden}")
    if len(lesson.select(".theorem.example")) != 11 or len(lesson.select(".theorem.definition")) != 1:
        raise RuntimeError("Lesson03 example/definition topology differs")
    if len([node for node in lesson.select("h4") if node.get_text(" ", strip=True) == "Penyelesaian"]) != 11:
        raise RuntimeError("Lesson03 worked-solution heading census differs")
    if len([node for node in lesson.select("h4") if node.get_text(" ", strip=True) == "Bukti"]) != 1:
        raise RuntimeError("Lesson03 proof heading census differs")
    if lesson.select("main img, main audio, main video, main iframe, main object, main embed"):
        raise RuntimeError("Lesson03 zero-asset document gained a media surface")
    for math_node in lesson.select("span.math"):
        sibling = math_node.next_sibling
        if not isinstance(sibling, NavigableString) or not str(sibling):
            continue
        text = str(sibling)
        first_nonspace = text.lstrip()[:1]
        if first_nonspace and first_nonspace in ",." and text[:1].isspace():
            raise RuntimeError(f"Lesson03 whitespace before punctuation after {math_node.get('data-o006-math-id')}")
        if text[:1].isalpha():
            raise RuntimeError(f"Lesson03 missing word boundary after {math_node.get('data-o006-math-id')}")
    markup = shared.require_file(BUILD / "Lesson03.html").decode("utf-8")
    if "assets/reader.css" in markup or "assets/reader-4of14.css" in markup:
        raise RuntimeError("Lesson03 stale CSS route remains")
    for required_math in (
        r"\(N(\theta_1, \theta_2).\)",
        r"\exp\left[x\ln p+\ln(1-p)-x\ln(1-p)\right]",
        r"\widehat{\mu}_{MM}^{\,2}",
        r"x_i^{\alpha-1}e^{-x_i/\theta}",
    ):
        if required_math not in markup:
            raise RuntimeError(f"admitted Lesson03 repair absent: {required_math}")
    return {
        "documents": result,
        "cumulative_target_units": total_target_units,
        "cumulative_math_nodes": len(global_math),
        "global_stable_ids_unique": True,
        "native_ids_unique_per_document": True,
        "lesson03_examples": 11,
        "lesson03_definitions": 1,
        "lesson03_worked_solutions": 11,
        "lesson03_proofs": 1,
        "visible_language": "id-ID",
        "document_backend": shared.identity(DOCUMENTS),
    }


def links_assets_gate(
    pages: dict[PurePosixPath, BeautifulSoup],
    content_pages: dict[str, BeautifulSoup],
    corrections: list[dict[str, object]],
) -> dict[str, object]:
    edges: list[dict[str, str]] = []
    external = 0
    for owner, page in pages.items():
        for tag, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src")):
            for node in page.select(f"{tag}[{attr}]"):
                reference = str(node.get(attr, ""))
                parsed = urlparse(reference)
                local = shared.local_reference(owner, reference)
                if local is None:
                    if tag != "a" and not (tag == "link" and "license" in (node.get("rel") or [])):
                        raise RuntimeError(f"external executable/asset reference: {owner} -> {reference}")
                    if parsed.scheme not in {"http", "https", "mailto", "tel"}:
                        raise RuntimeError(f"unsupported reference scheme: {owner} -> {reference}")
                    external += 1
                    continue
                resolved, fragment = local
                if resolved not in EXPECTED_READER or not (BUILD / Path(resolved.as_posix())).is_file():
                    raise RuntimeError(f"broken or unmanifested local reference: {owner} -> {reference}")
                if fragment and resolved.suffix.lower() in {".html", ".htm"}:
                    target = pages.get(resolved) or BeautifulSoup(shared.require_file(BUILD / Path(resolved.as_posix())), "html.parser")
                    if target.find(id=fragment) is None:
                        raise RuntimeError(f"broken local fragment: {owner} -> {reference}")
                edges.append({"owner": owner.as_posix(), "reference": reference, "resolved": resolved.as_posix()})
    css = shared.require_file(BUILD / "assets" / "reader-5of14.css")
    if len(css) != 6213 or shared.sha256(css) != "37fc52f724e0ea76443dc12ef243bf874ab6fb8c3c0640e03ab8cf1a6939f989":
        raise RuntimeError("responsive reader CSS identity differs")
    css_text = css.decode("utf-8")
    for fragment in ("main img:not(.card-img)", "max-width: 100%", "height: auto", "main .quarto-float"):
        if fragment not in css_text:
            raise RuntimeError(f"reader reflow rule missing: {fragment}")
    if (BUILD / "assets" / "reader.css").exists() or (BUILD / "assets" / "reader-4of14.css").exists():
        raise RuntimeError("stale reader CSS remains")
    historical_assets = shared.asset_gate(content_pages, corrections)
    lesson02_images = content_pages["Lesson02"].select("img[src]")
    if [node.get("src") for node in lesson02_images] != ["assets/dartboard.png", "assets/unnamed-chunk-1-1.png"]:
        raise RuntimeError("Lesson02 reader asset sequence differs")
    for filename, (size, digest) in prior.LESSON02_ASSETS.items():
        authority = shared.require_file(ROOT / "authority" / "assets" / "stat415" / "lesson02" / filename)
        reader = shared.require_file(BUILD / "assets" / filename)
        if authority != reader or len(reader) != size or shared.sha256(reader) != digest:
            raise RuntimeError(f"Lesson02 frozen PNG identity differs: {filename}")
    if content_pages["Lesson03"].select("main img, main audio, main video, main source"):
        raise RuntimeError("Lesson03 asset closure differs")
    return {
        "local_edges": len(edges),
        "local_edges_sha256": shared.sha256(shared.canonical_json(sorted(edges, key=lambda row: (row["owner"], row["reference"], row["resolved"])))),
        "external_anchor_edges": external,
        "all_local_targets_manifested": True,
        "historical_assets": historical_assets,
        "lesson02_assets": 2,
        "lesson03_assets": 0,
        "responsive_reader_css": shared.identity(BUILD / "assets" / "reader-5of14.css"),
    }


def privacy_runtime_rights_gate(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    forbidden = (
        "google-analytics", "googletagmanager", "gtag(", "matomo", "plausible.io", "hotjar",
        "clarity.ms", "segment.io", "document.cookie", "cookieconsent", "onetrust",
    )
    secrets = re.compile(r"github\s+tokens?\.md|zenodo\s+token|figshare\s+token|(?:api|access)[_-]?token|api[_-]?key|authorization\s*:\s*bearer", re.I)
    absolute = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|(?:^|[\"'\s])/(?:Users|home|tmp)/", re.I)
    for path in EXPECTED_READER:
        if path.suffix.lower() not in {".html", ".css", ".svg"}:
            continue
        text = shared.require_file(BUILD / Path(path.as_posix())).decode("utf-8")
        if any(marker in text.casefold() for marker in forbidden) or secrets.search(text) or absolute.search(text):
            raise RuntimeError(f"privacy/runtime marker present: {path}")
    content_paths = {PurePosixPath(f"Lesson{i:02d}.html") for i in range(4)}
    for owner, page in pages.items():
        if page.select("iframe, object, embed"):
            raise RuntimeError(f"embedded external-capable object present: {owner}")
        if any(any(str(attr).lower().startswith("on") for attr in node.attrs) for node in page.find_all(True)):
            raise RuntimeError(f"inline event handler present: {owner}")
        scripts = page.select("script")
        expected_scripts = 1 if owner in content_paths else 0
        if len(scripts) != expected_scripts:
            raise RuntimeError(f"reader script census differs: {owner}")
        for script in scripts:
            if script.get("src") != "assets/MathJax/tex-svg.js" or script.get_text(strip=True):
                raise RuntimeError(f"nonlocal or inline script present: {owner}")
        styles = page.select('link[rel~="stylesheet"]')
        expected_href = "../assets/reader-5of14.css" if owner == PurePosixPath("licenses/index.html") else "assets/reader-5of14.css"
        if len(styles) != 1 or styles[0].get("href") != expected_href:
            raise RuntimeError(f"reader stylesheet route differs: {owner}")
    runtime_pairs = [
        (BUILD / "assets" / "MathJax" / "tex-svg.js", ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "tex-svg.js"),
        *((BUILD / "assets" / "MathJax" / "input" / "tex" / "extensions" / name, ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "input" / "tex" / "extensions" / name) for name in ("color.js", "enclose.js", "cancel.js")),
        (BUILD / "licenses" / "MathJax-3.1.2-LICENSE.txt", ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "LICENSE.txt"),
    ]
    if any(shared.require_file(left) != shared.require_file(right) for left, right in runtime_pairs):
        raise RuntimeError("local MathJax closure differs from frozen authority")
    licence = pages[PurePosixPath("licenses/index.html")]
    licence_text = licence.get_text(" ", strip=True)
    for fragment in (
        "Penn State", "CC BY-NC 4.0", "kecuali dinyatakan lain", "MathJax 3.1.2",
        "Apache License 2.0", PROVENANCE, "tidak resmi", "tujuh belas koreksi Lesson 03",
        "Lesson 03 tidak memiliki aset isi", "tidak ada relisensi seragam",
    ):
        if fragment not in licence_text:
            raise RuntimeError(f"rights/provenance surface missing: {fragment}")
    if licence.select_one('a[rel~="license"][href="https://creativecommons.org/licenses/by-nc/4.0/"]') is None:
        raise RuntimeError("Penn State licence link missing")
    return {
        "external_runtime_requests": 0,
        "inline_scripts": 0,
        "analytics": False,
        "cookies": False,
        "credential_paths": False,
        "local_absolute_paths": False,
        "local_mathjax_only": True,
        "penn_state": "CC BY-NC 4.0 except where otherwise noted",
        "lesson03_assets": "verified zero main-content assets",
        "mathjax_3_1_2": "Apache-2.0",
        "aggregate_uniform_relicense": False,
        "translation_provenance": PROVENANCE,
    }


def build_receipt_gate(reader: dict[str, object]) -> dict[str, object]:
    data = shared.load_json(BUILD_RECEIPT)
    if data.get("schema") != "o006.stat415.through-lesson03-build.v1" or data.get("status") != "built":
        raise RuntimeError("Lesson03 build receipt schema/status differs")
    if data.get("coverage") != {"complete_count": 5, "complete_documents": list(CONTENT), "corpus_document_count": 14, "next_document": "Lesson04"}:
        raise RuntimeError("Lesson03 build coverage differs")
    if (
        data.get("translation_segments") != 1599
        or data.get("structural_units_normalized") != 1399
        or data.get("structural_units_target") != 1397
        or data.get("math_nodes") != {"index": 0, "Lesson00": 331, "Lesson01": 169, "Lesson02": 209, "Lesson03": 440, "total": 1149}
    ):
        raise RuntimeError("Lesson03 build census differs")
    receipt_reader = data.get("reader")
    if not isinstance(receipt_reader, dict) or receipt_reader.get("path") != "build/html-id" or receipt_reader.get("files") != 32 or receipt_reader.get("bytes") != reader["bytes"] or receipt_reader.get("manifest_bytes") != reader["manifest_bytes"] or receipt_reader.get("manifest_sha256") != reader["manifest_sha256"]:
        raise RuntimeError("Lesson03 build reader identity differs")
    layout = data.get("layout")
    css_identity = shared.identity(BUILD / "assets" / "reader-5of14.css")
    if not isinstance(layout, dict) or layout.get("reader_css_path") != "assets/reader-5of14.css" or layout.get("reader_css_bytes") != css_identity["bytes"] or layout.get("reader_css_sha256") != css_identity["sha256"]:
        raise RuntimeError("Lesson03 build reflow contract differs")
    for field, path in (("documents_backend", DOCUMENTS), ("corrections", CORRECTIONS)):
        record = data.get(field)
        actual = shared.identity(path)
        if not isinstance(record, dict) or record.get("path") != actual["path"] or record.get("bytes") != actual["bytes"] or record.get("sha256") != actual["sha256"]:
            raise RuntimeError(f"Lesson03 build backend identity differs: {field}")
    if data.get("locale") != "id-ID" or data.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("Lesson03 build locale/provenance differs")
    if data.get("corrections") != {"bytes": 18084, "count": 46, "lesson03_count": 17, "path": "backend/through_lesson03_corrections.jsonl", "sha256": "07a58f960890e58bb90be43c8d90102fc8edfae7201750fc036036e67c0baa83", "through_lesson02_count": 29}:
        raise RuntimeError("Lesson03 build correction identity/census differs")
    frozen = data.get("inputs", {}).get("frozen", {})
    translation_record = frozen.get("build/LESSON03_TRANSLATION_RECEIPT.json") if isinstance(frozen, dict) else None
    if translation_record != {"bytes": 3131, "sha256": "d120e1d1b8248070450a4e3d314a890e4b38b199faab364ce525638038676bc6"}:
        raise RuntimeError("build did not use the final Lesson03 translation receipt")
    builder = data.get("inputs", {}).get("builder", {})
    actual_builder = shared.identity(ROOT / "scripts" / "build_through_lesson03.py")
    if not isinstance(builder, dict) or builder.get("path") != actual_builder["path"] or builder.get("bytes") != actual_builder["bytes"] or builder.get("sha256") != actual_builder["sha256"]:
        raise RuntimeError("Lesson03 build script identity differs")
    target_records = data.get("target_documents")
    if not isinstance(target_records, list) or len(target_records) != 5:
        raise RuntimeError("Lesson03 target-document receipt differs")
    for record, component in zip(target_records, CONTENT):
        actual = shared.identity(ROOT / "source" / "id-ID" / f"{component}.html")
        if record != actual:
            raise RuntimeError(f"Lesson03 target-document identity differs: {component}")
    for name, (size, digest) in HISTORICAL.items():
        raw = shared.require_file(ROOT / name)
        if len(raw) != size or shared.sha256(raw) != digest or data.get("historical_lesson02_evidence", {}).get(name) != {"bytes": size, "sha256": digest}:
            raise RuntimeError(f"historical evidence changed: {name}")
    return shared.identity(BUILD_RECEIPT)


def compute() -> bytes:
    reader = reader_manifest_gate()
    pages, content_pages = load_pages()
    translation = translation_gate()
    normalization = normalization_gate()
    corrections, corrections_math = corrections_and_math_gate(content_pages)
    documents_language = document_and_language_gate(content_pages)
    links_assets = links_assets_gate(pages, content_pages, corrections)
    privacy_rights = privacy_runtime_rights_gate(pages)
    build_receipt = build_receipt_gate(reader)
    receipt = {
        "schema": "o006.stat415.through-lesson03-qa.v1",
        "status": "pass",
        "coverage": {"complete_documents": list(CONTENT), "complete_count": 5, "corpus_document_count": 14, "next_document": "Lesson04"},
        "locale": "id-ID",
        "reader": reader,
        "build_receipt": build_receipt,
        "translation": translation,
        "normalization": normalization,
        "structure_math_and_corrections": corrections_math,
        "documents_semantics_and_language": documents_language,
        "links_assets_and_reflow": links_assets,
        "privacy_runtime_rights_and_provenance": privacy_rights,
        "gates": [
            "exact-32-file-reader-and-manifest", "five-of-fourteen-document-coverage",
            "exact-1599-translated-segments-and-bindings", "exact-1399-normalized-and-1397-target-units",
            "exact-1149-math-nodes", "exact-46-target-only-corrections-seventeen-for-lesson03",
            "exact-nineteen-lesson03-changed-math-surfaces", "d005-likelihood-ratio-counterexample",
            "d008-product-versus-exponent-sum-distinction", "preserved-historical-lesson02-evidence",
            "unique-stable-unit-math-and-native-dom-identities", "indonesian-semantics-terminology-and-boundaries",
            "all-local-links-fragments-assets-and-runtime", "verified-zero-lesson03-content-assets",
            "versioned-responsive-reader-css", "no-analytics-cookies-credentials-or-local-paths",
            "component-rights-and-exact-model-provenance",
        ],
    }
    return shared.canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payload = compute()
    if args.write:
        shared.atomic_write(QA_RECEIPT, payload)
        state = "written"
    else:
        if not QA_RECEIPT.is_file() or QA_RECEIPT.read_bytes() != payload:
            raise RuntimeError("Lesson03 cumulative QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({
        "mode": state,
        "status": data["status"],
        "documents": data["coverage"]["complete_count"],
        "reader_files": data["reader"]["files"],
        "reader_bytes": data["reader"]["bytes"],
        "segments": data["translation"]["cumulative_segments"],
        "source_units": data["normalization"]["source_structural_units"],
        "target_units": data["structure_math_and_corrections"]["target_stable_units"],
        "math_nodes": data["structure_math_and_corrections"]["math_nodes"],
        "corrections": data["structure_math_and_corrections"]["corrections"],
        "receipt_sha256": shared.sha256(payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
