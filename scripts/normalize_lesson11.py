#!/usr/bin/env python3
"""Normalize Lesson 11 and byte-verify its source, asset, and stable IDs."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path

import bs4
from bs4 import BeautifulSoup, Tag

import normalize_lesson03 as base


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson11.html"
SCRIPT = ROOT / "scripts" / "normalize_lesson11.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-012"
COMPONENT_ID = "Lesson11"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson11.html"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
RECEIPT_SCHEMA = "o006.stat415.lesson11-normalization.v1"
LICENSE_TEXT = (
    "Except where otherwise noted, content on this site is licensed under a "
    "CC BY-NC 4.0 license."
)

EXPECTED_SOURCE_BYTES = 99_359
EXPECTED_SOURCE_SHA256 = "4a007ab235242a27f000a8e8865fab06d2b8507a2e2e7400faf6112ce83a7c32"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
EXPECTED_TOPOLOGY_SHA256 = "9dc34953c3bbddbe8d4001d3fa76547ab0f8d85f226bbbf6fca1edd63a87efcd"
EXPECTED_FORMULA_SHA256 = "cadc74feeb0269a091b90cdd8f6e1cfc13065dfd4dbec72dab008a03e681a0a7"
EXPECTED_SEMANTIC_TEXT_SHA256 = "f6a5f814d6ab012db44cb82e092da4b64c19ba285fbf45ade699bdc1f9671a2a"
EXPECTED_CODE_TEXT_SHA256 = "4ad48e48d37e566da85447efcc47257cc667427ba8a9de1e624eeecb528b2d83"
EXPECTED_STYLE_TEXT_SHA256 = "ae5c8e57160dcb78f6e4958172fee8ba69698cf5603338693684dbf5f71d8551"

EXPECTED_COUNTS = {
    "sections": 12,
    "headings": 13,
    "theorem_class_nodes": 7,
    "theorems": 0,
    "definitions": 0,
    "examples": 7,
    "corollaries": 0,
    "solutions": 6,
    "proofs": 0,
    "math_nodes": 264,
    "math_inline": 209,
    "math_display": 55,
    "pre_nodes": 4,
    "code_nodes": 4,
    "figures": 1,
    "images": 1,
    "asset_occurrences": 1,
    "unique_asset_sources": 1,
    "figure_captions": 1,
    "links": 5,
    "tables": 1,
}
EXPECTED_ROLE_COUNTS = {
    "code": 8,
    "example": 7,
    "figure": 1,
    "figure-caption": 1,
    "heading": 8,
    "image": 1,
    "link": 5,
    "section": 6,
    "solution": 12,
    "structure": 215,
}
EXPECTED_ASSET_REFS = ["assets/bayes.png"]
ASSET_PATH = ROOT / "authority" / "assets" / "stat415" / "lesson11" / "assets" / "bayes.png"
ASSET_MANIFEST = ROOT / "authority" / "LESSON11_ASSET_MANIFEST.csv"
ASSET_FREEZE_RECEIPT = ROOT / "authority" / "LESSON11_ASSET_FREEZE_RECEIPT.json"
SOURCE_FINDINGS = ROOT / "working" / "lesson11_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson11_math_audit.md"
TERMINOLOGY_QA = ROOT / "working" / "lesson11_terminology_qa.md"
EXPECTED_ASSET_BYTES = 142_195
EXPECTED_ASSET_SHA256 = "2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22"
EXPECTED_ASSET_MANIFEST_BYTES = 434
EXPECTED_ASSET_MANIFEST_SHA256 = "a10a6bc2c5ba7738916eeb2ac1cb12d2ed52a77d505e9843190ffa39a726379b"
EXPECTED_ASSET_RECEIPT_BYTES = 1_062
EXPECTED_ASSET_RECEIPT_SHA256 = "2d128b3d4b4635aa45855b8d5ba82cbec408f139a1ac51bcddcbd7682221f3e2"
EXPECTED_SOURCE_FINDINGS = (4_908, "72de17541e6e76d2e28ab64c47b21e0fffd7a46fae2eabb37d11c1e7aabc397f")
EXPECTED_MATH_AUDIT = (1_228, "5d97555b9526f82c028a231846b61221b5825692b5fbc7f0c14b95f2871202b5")
EXPECTED_TERMINOLOGY_QA = (942, "1f760ac99bfd9f112438ce2cb6fd205150c0e2dae5eb638e52625a922ab6c52c")
BATCHES = (
    ("A", 1, 48, "opening, overview, objectives, and complete 11.1"),
    ("B", 49, 286, "complete 11.2 Bayesian Estimation"),
    ("C", 287, 354, "complete 11.3 Credible Intervals and summary"),
)

# The shared helper is parameterized through these module globals.
base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "11 Bayesian Methods"
    )
    return (
        "<!doctype html>\n"
        '<html lang="en-US">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{SOURCE_URL}">\n'
        '<meta name="translation-provenance" '
        'content="OpenAI Codex gpt-5.6-sol, Ultra">\n'
        "</head>\n<body>\n"
        f"{main}\n"
        "</body>\n</html>\n"
    ).encode("utf-8")


def asset_inventory_csv(rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    fields = (
        "asset_id",
        "document_id",
        "component_id",
        "source_ref",
        "source_url",
        "occurrences",
        "first_unit_id",
        "first_parent_unit_id",
        "section_ids",
        "alt_texts",
        "local_path",
        "bytes",
        "sha256",
        "media_type",
        "width",
        "height",
        "license",
        "disposition",
        "binary_status",
    )
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        unit_ids = [value for value in row["unit_ids"] if value]
        writer.writerow(
            {
                "asset_id": row["asset_id"],
                "document_id": row["document_id"],
                "component_id": row["component_id"],
                "source_ref": row["source_ref"],
                "source_url": row["source_url"],
                "occurrences": row["occurrences"],
                "first_unit_id": unit_ids[0] if unit_ids else "",
                "first_parent_unit_id": row["first_parent_unit_id"] or "",
                "section_ids": json.dumps(row["section_ids"], ensure_ascii=False),
                "alt_texts": json.dumps(row["alt_texts"], ensure_ascii=False),
                "local_path": ASSET_PATH.relative_to(ROOT).as_posix(),
                "bytes": EXPECTED_ASSET_BYTES,
                "sha256": EXPECTED_ASSET_SHA256,
                "media_type": "image/png",
                "width": 308,
                "height": 321,
                "license": "CC BY-NC 4.0",
                "disposition": "redistribute-with-page-attribution-and-change-notice",
                "binary_status": "frozen-and-byte-verified",
            }
        )
    return stream.getvalue().encode("utf-8")


def output_record(path: str, payload: bytes, **extra: object) -> dict[str, object]:
    return {
        "path": path,
        "bytes": len(payload),
        "sha256": base.sha256(payload),
        **extra,
    }


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson11 normalization helper differs from its frozen implementation")

    asset_payload_bytes = ASSET_PATH.read_bytes()
    manifest_payload = ASSET_MANIFEST.read_bytes()
    freeze_receipt_payload = ASSET_FREEZE_RECEIPT.read_bytes()
    source_findings_payload = SOURCE_FINDINGS.read_bytes()
    math_audit_payload = MATH_AUDIT.read_bytes()
    terminology_qa_payload = TERMINOLOGY_QA.read_bytes()
    if (
        len(asset_payload_bytes) != EXPECTED_ASSET_BYTES
        or base.sha256(asset_payload_bytes) != EXPECTED_ASSET_SHA256
        or len(manifest_payload) != EXPECTED_ASSET_MANIFEST_BYTES
        or base.sha256(manifest_payload) != EXPECTED_ASSET_MANIFEST_SHA256
        or len(freeze_receipt_payload) != EXPECTED_ASSET_RECEIPT_BYTES
        or base.sha256(freeze_receipt_payload) != EXPECTED_ASSET_RECEIPT_SHA256
        or (len(source_findings_payload), base.sha256(source_findings_payload)) != EXPECTED_SOURCE_FINDINGS
        or (len(math_audit_payload), base.sha256(math_audit_payload)) != EXPECTED_MATH_AUDIT
        or (len(terminology_qa_payload), base.sha256(terminology_qa_payload)) != EXPECTED_TERMINOLOGY_QA
    ):
        raise RuntimeError("Lesson11 frozen asset/audit closure differs")

    source_payload = SOURCE.read_bytes()
    if (
        len(source_payload) != EXPECTED_SOURCE_BYTES
        or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256
    ):
        raise RuntimeError("Lesson11 authority differs from the frozen 14-document manifest")
    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson11 authority is not valid UTF-8") from exc

    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson11 authority lacks main#quarto-document-content")
    if original_main.select("script"):
        raise RuntimeError("unexpected executable script in Lesson11 semantic main")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson11 page-level CC BY-NC 4.0 witness is missing")

    source_counts = base.content_counts(original_main)
    if source_counts != EXPECTED_COUNTS:
        raise RuntimeError(f"Lesson11 content census differs: {source_counts}")
    source_topology_sha = base.topology_sha256(original_main)
    formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(formulas).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    code_nodes = [tag.get_text() for tag in original_main.select("pre, code")]
    code_payload = "\n".join(code_nodes).encode("utf-8")
    style_nodes = original_main.select("style")
    style_payload = "\n".join(tag.get_text() for tag in style_nodes).encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(
        key for key, count in Counter(native_ids).items() if count > 1
    )
    if (
        source_topology_sha != EXPECTED_TOPOLOGY_SHA256
        or base.sha256(formula_payload) != EXPECTED_FORMULA_SHA256
        or base.sha256(semantic_text_payload) != EXPECTED_SEMANTIC_TEXT_SHA256
        or base.sha256(code_payload) != EXPECTED_CODE_TEXT_SHA256
        or base.sha256(style_payload) != EXPECTED_STYLE_TEXT_SHA256
        or len(style_nodes) != 2
        or len(native_ids) != 26
        or len(set(native_ids)) != 26
        or duplicate_ids
    ):
        raise RuntimeError("Lesson11 topology/formula/text/code/style/native-id witnesses differ")
    if any("codeblock-with-label" not in tag.get_text() for tag in style_nodes):
        raise RuntimeError("Lesson11 embedded code-label styles differ")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson11 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    segment_rows = base.extract_segments(main)
    role_counts = dict(sorted(Counter(str(row["role"]) for row in unit_rows).items()))
    if (
        len(unit_rows) != 264
        or len(math_rows) != 264
        or len(asset_rows) != 1
        or len(segment_rows) != 354
        or role_counts != EXPECTED_ROLE_COUNTS
        or [str(row["source_ref"]) for row in asset_rows] != EXPECTED_ASSET_REFS
    ):
        raise RuntimeError("Lesson11 stable structural/segment census differs")

    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(
        original_main, normalized_payload, source_topology_sha, source_counts
    )
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None:
        raise RuntimeError("Lesson11 normalized semantic main is missing")
    if [tag.get_text() for tag in target_main.select("pre, code")] != code_nodes:
        raise RuntimeError("Lesson11 code surfaces changed during normalization")
    if [tag.get_text() for tag in target_main.select("style")] != [
        tag.get_text() for tag in style_nodes
    ]:
        raise RuntimeError("Lesson11 code-label styles changed during normalization")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 12,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson11.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson11.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "semantic_text_sha256": base.sha256(semantic_text_payload),
        "formula_count": len(formulas),
        "formula_sha256": base.sha256(formula_payload),
        "code_node_count": len(original_main.select("code")),
        "pre_node_count": len(original_main.select("pre")),
        "code_text_sha256": base.sha256(code_payload),
        "inline_style_count": len(style_nodes),
        "inline_style_text_sha256": base.sha256(style_payload),
        "unit_count": len(unit_rows),
        "segment_count": len(segment_rows),
        "asset_count": len(asset_rows),
        "dependency_count": sum(base.dependency_census(original_main).values()),
        "native_id_occurrences": len(native_ids),
        "unique_native_ids": len(set(native_ids)),
        "duplicate_native_ids": duplicate_ids,
    }
    catalogue_segments = [
        {
            "schema": CATALOGUE_SCHEMA,
            "record_type": "segment",
            "entity_id": row["segment_id"],
            "segment_id": row["segment_id"],
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "ordinal": row["ordinal"],
            "parent_tag": row["parent_tag"],
            "parent_unit_id": row["parent_unit_id"],
            "section_id": row["section_id"],
            "locale": "en-US",
            "source_text": row["source_text"],
            "source_sha256": row["source_sha256"],
            "translation_status": "pending",
        }
        for row in segment_rows
    ]
    catalogue_rows = [document_row, *unit_rows, *math_rows, *asset_rows, *catalogue_segments]
    if len(catalogue_rows) != 884:
        raise RuntimeError("Lesson11 catalogue-record census differs")

    segments_payload = base.segment_csv(segment_rows)
    catalogue_payload = base.canonical_jsonl(catalogue_rows)
    asset_payload = asset_inventory_csv(asset_rows)
    batch_templates = {
        f"working/lesson11_translation_batch_{label}.csv": base.segment_csv(
            [row for row in segment_rows if first <= int(row["ordinal"]) <= last]
        )
        for label, first, last, _boundary in BATCHES
    }
    expected_batch_rows = {"A": 48, "B": 238, "C": 68}
    for label, first, last, _boundary in BATCHES:
        actual = sum(first <= int(row["ordinal"]) <= last for row in segment_rows)
        if actual != expected_batch_rows[label]:
            raise RuntimeError(f"Lesson11 batch {label} census differs: {actual}")

    script_payload = SCRIPT.read_bytes()
    outputs_without_receipt: dict[str, bytes] = {
        "source/normalized/en-US/Lesson11.html": normalized_payload,
        "working/lesson11_segments.csv": segments_payload,
        "backend/lesson11_source_catalogue.jsonl": catalogue_payload,
        "working/lesson11_asset_inventory.csv": asset_payload,
    }
    output_records = {
        path: output_record(
            path,
            payload,
            **(
                {"rows": len(segment_rows)}
                if path == "working/lesson11_segments.csv"
                else {"records": len(catalogue_rows)}
                if path == "working/lesson11_source_catalogue.jsonl"
                else {}
            ),
        )
        for path, payload in outputs_without_receipt.items()
    }
    receipt: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "status": "normalized-source-and-asset-ready; translation-batches-initialized",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "assets": len(asset_rows),
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
            "inline_style_nodes": len(style_nodes),
        },
        "stable_id_ranges": {
            "units": [f"{DOCUMENT_ID}-U0001", f"{DOCUMENT_ID}-U0264"],
            "math": [f"{DOCUMENT_ID}-M0001", f"{DOCUMENT_ID}-M0264"],
            "assets": [f"{DOCUMENT_ID}-A0001", f"{DOCUMENT_ID}-A0001"],
            "segments": [f"{DOCUMENT_ID}-S0001", f"{DOCUMENT_ID}-S0354"],
        },
        "role_counts": role_counts,
        "source_defect_count": 20,
        "source_defect_ids": [f"L11-D{i:03d}" for i in range(1, 21)],
        "audits": {
            "source_findings": output_record(SOURCE_FINDINGS.relative_to(ROOT).as_posix(), source_findings_payload),
            "math": output_record(MATH_AUDIT.relative_to(ROOT).as_posix(), math_audit_payload),
            "terminology": output_record(TERMINOLOGY_QA.relative_to(ROOT).as_posix(), terminology_qa_payload),
        },
        "dependency_census": base.dependency_census(original_main),
        "asset_boundary": {
            "references_inventoried": True,
            "source_refs": EXPECTED_ASSET_REFS,
            "binary_bytes_frozen": True,
            "asset": output_record(ASSET_PATH.relative_to(ROOT).as_posix(), asset_payload_bytes),
            "manifest": output_record(ASSET_MANIFEST.relative_to(ROOT).as_posix(), manifest_payload),
            "freeze_receipt": output_record(ASSET_FREEZE_RECEIPT.relative_to(ROOT).as_posix(), freeze_receipt_payload),
            "blocking_unresolved_assets": 0,
        },
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "code_text_sha256": base.sha256(code_payload),
            "inline_style_text_sha256": base.sha256(style_payload),
            "formula_nodes_byte_preserved": True,
            "code_nodes_text_preserved": True,
            "inline_code_label_styles_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "authority_mutated": False,
        },
        "translation_batches": [
            {
                "batch": label,
                "range": [
                    f"{DOCUMENT_ID}-S{first:04d}",
                    f"{DOCUMENT_ID}-S{last:04d}",
                ],
                "rows": last - first + 1,
                "boundary": boundary,
                "template_sha256": base.sha256(batch_templates[f"working/lesson11_translation_batch_{label}.csv"]),
                "status": "initialized; target status validated separately",
            }
            for label, first, last, boundary in BATCHES
        ],
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": (
            "semantic main only; authority immutable; formulas, code, styles, tables, "
            "anchors, links, and asset references protected; stable IDs additive"
        ),
        "script": output_record("scripts/normalize_lesson11.py", script_payload),
        "helper_script": output_record("scripts/normalize_lesson03.py", helper_payload),
        "outputs": output_records,
    }
    receipt_payload = base.canonical_json(receipt)
    return {
        **outputs_without_receipt,
        "build/LESSON11_NORMALIZATION_RECEIPT.json": receipt_payload,
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
            base.atomic_write(ROOT / relative, payload)
        # Translation batches are initialized once and never overwritten by a
        # normalization replay after translators have filled their targets.
        source_rows = list(csv.DictReader(io.StringIO((ROOT / "working" / "lesson11_segments.csv").read_text("utf-8"))))
        for label, first, last, _boundary in BATCHES:
            path = ROOT / "working" / f"lesson11_translation_batch_{label}.csv"
            if not path.exists():
                selected = [row for row in source_rows if first <= int(row["segment_id"][-4:]) <= last]
                base.atomic_write(path, base.segment_csv(selected))
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson11 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson11 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    # Whether pending or translated, each live batch must retain the exact
    # frozen source fields and contiguous range.  Target fields are merge-stage
    # responsibility and therefore do not affect normalization replay.
    segment_rows = list(csv.DictReader(io.StringIO((ROOT / "working" / "lesson11_segments.csv").read_text("utf-8"))))
    by_id = {row["segment_id"]: row for row in segment_rows}
    source_fields = ("segment_id", "document_id", "component_id", "section_id", "source_sha256", "source_text")
    for label, first, last, _boundary in BATCHES:
        path = ROOT / "working" / f"lesson11_translation_batch_{label}.csv"
        rows = list(csv.DictReader(io.StringIO(path.read_text("utf-8"))))
        expected_ids = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(first, last + 1)]
        if [row["segment_id"] for row in rows] != expected_ids:
            raise RuntimeError(f"Lesson11 batch {label} range differs")
        for row in rows:
            source = by_id[row["segment_id"]]
            if any(row[field] != source[field] for field in source_fields):
                raise RuntimeError(f"Lesson11 batch {label} changed source field: {row['segment_id']}")

    receipt_payload = outputs["build/LESSON11_NORMALIZATION_RECEIPT.json"]
    receipt = json.loads(receipt_payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "segments": receipt["counts"]["translation_segments"],
                "units": receipt["counts"]["structural_units"],
                "math": receipt["counts"]["math_nodes"],
                "assets": receipt["counts"]["assets"],
                "catalogue_records": receipt["counts"]["catalogue_records"],
                "receipt_sha256": base.sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
