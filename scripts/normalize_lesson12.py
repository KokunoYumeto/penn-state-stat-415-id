#!/usr/bin/env python3
"""Normalize Lesson 12 and verify its source, media closure, and stable IDs."""

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
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson12.html"
SCRIPT = ROOT / "scripts" / "normalize_lesson12.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"
FREEZE_SCRIPT = ROOT / "scripts" / "freeze_lesson12_assets.py"

DOCUMENT_ID = "O006-PSU-013"
COMPONENT_ID = "Lesson12"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson12.html"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
RECEIPT_SCHEMA = "o006.stat415.lesson12-normalization.v1"
LICENSE_TEXT = (
    "Except where otherwise noted, content on this site is licensed under a "
    "CC BY-NC 4.0 license."
)

EXPECTED_SOURCE_BYTES = 144_220
EXPECTED_SOURCE_SHA256 = "89569622b8fea9bcfc17d51717002ab9840b44e6d80a34ee476d94acd45b515d"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
EXPECTED_FREEZE_SCRIPT = (
    16_680,
    "a605b1311dd831232d261246d6cf87b29de66601dd728350c7dbb7e5bf6b1188",
)
EXPECTED_TOPOLOGY_SHA256 = "2adf6ef893702fdf0eb7094f26bffb728f2cab5a271cb9e21de00607cfc1ddca"
EXPECTED_FORMULA_SHA256 = "1e5b97f1531ce06c3a150184c29694dcf08fb80e2e100517c032a10ad76e71a4"
EXPECTED_SEMANTIC_TEXT_SHA256 = "13b074b39f5969f4c792c49af0abb757610014bc7aeeff691b6c8101f7452ce6"
EXPECTED_EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

EXPECTED_COUNTS = {
    "sections": 24,
    "headings": 25,
    "theorem_class_nodes": 14,
    "theorems": 9,
    "definitions": 1,
    "examples": 4,
    "corollaries": 0,
    "solutions": 4,
    "proofs": 0,
    "math_nodes": 352,
    "math_inline": 266,
    "math_display": 86,
    "pre_nodes": 0,
    "code_nodes": 0,
    "figures": 15,
    "images": 10,
    "asset_occurrences": 10,
    "unique_asset_sources": 9,
    "figure_captions": 15,
    "links": 12,
    "tables": 6,
}
EXPECTED_ROLE_COUNTS = {
    "definition": 1,
    "example": 4,
    "figure": 15,
    "figure-caption": 15,
    "heading": 22,
    "image": 10,
    "link": 12,
    "section": 20,
    "solution": 8,
    "structure": 730,
    "theorem": 9,
}
EXPECTED_DEPENDENCIES = {
    "images": 10,
    "videos": 0,
    "audio": 0,
    "media_sources": 0,
    "iframes": 3,
    "objects": 0,
    "embeds": 0,
    "downloads": 0,
    "scripts": 0,
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
EXPECTED_ASSET_REFS = [
    "Lesson12_files/figure-html/fig-lesson9_1-1.png",
    "Lesson12_files/figure-html/fig-skin-cancer-1.png",
    "Lesson12_files/figure-html/fig-htwt1-1.png",
    "Lesson12_files/figure-html/fig-gpavsentrance3-1.png",
    "Lesson12_files/figure-html/fig-samplegpaentrance4-1.png",
    "assets/lesson9_11.png",
    "Lesson12_files/figure-html/fig-scattertemp-1.png",
    "Lesson12_files/figure-html/fig-scattertemp2-1.png",
    "Lesson12_files/figure-html/fig-iqnormal-1.png",
]
EXPECTED_VIDEO_URLS = [
    "https://www.youtube.com/embed/oAaPR1qVedw",
    "https://www.youtube.com/embed/pWMp1vhStDE",
    "https://www.youtube.com/embed/mdzP-v6vl74",
]

ASSET_MANIFEST = ROOT / "authority" / "LESSON12_ASSET_MANIFEST.csv"
ASSET_FREEZE_RECEIPT = ROOT / "authority" / "LESSON12_ASSET_FREEZE_RECEIPT.json"
VIDEO_PROVENANCE = ROOT / "authority" / "LESSON12_VIDEO_PROVENANCE.csv"
SOURCE_FINDINGS = ROOT / "working" / "lesson12_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson12_math_audit.md"
TERMINOLOGY_QA = ROOT / "working" / "lesson12_terminology_qa.md"

EXPECTED_ASSET_MANIFEST = (
    5_007,
    "47dc68c12a8eedc0a10a0010c7c73346dd2b8a8e4ef5f3ff9d769c24a9764c2a",
)
EXPECTED_ASSET_RECEIPT = (
    7_044,
    "75e46dc6b87346fd898aad96fd59f0045aaeb43fab2a6942a731a3f6b0805559",
)
EXPECTED_VIDEO_PROVENANCE = (
    959,
    "f240f2e9c8aa502eebf712d037c13a9b28331e7045a4582a5bbc46e75d0c3fd2",
)
EXPECTED_SOURCE_FINDINGS = (
    8_203,
    "8b087fb8e545f14ba323afd1caa5672117d60878c3c5924a0b0455136078109c",
)
EXPECTED_MATH_AUDIT = (
    2_521,
    "ed14d3e7c210a2c0025ea9eda55f56c2f8da3f23e7b70242d8aa7dd7cf72d14e",
)
EXPECTED_TERMINOLOGY_QA = (
    3_727,
    "31b7f946de0b7a1756d482d48ee9951b136df228a41ee0e341b5cd6c76174d5c",
)
EXPECTED_ASSET_TOTAL_BYTES = 233_075

# The shared helper is parameterized through these module globals.
base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def output_record(path: str, payload: bytes, **extra: object) -> dict[str, object]:
    return {
        "path": path,
        "bytes": len(payload),
        "sha256": base.sha256(payload),
        **extra,
    }


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "12 Simple Linear Regression"
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


def verify_file(path: Path, expected: tuple[int, str], label: str) -> bytes:
    payload = path.read_bytes()
    if (len(payload), base.sha256(payload)) != expected:
        raise RuntimeError(f"Lesson 12 {label} differs from its frozen identity")
    return payload


def load_asset_closure() -> tuple[
    list[dict[str, str]],
    list[dict[str, str]],
    dict[str, object],
    dict[str, bytes],
]:
    manifest_payload = verify_file(ASSET_MANIFEST, EXPECTED_ASSET_MANIFEST, "asset manifest")
    receipt_payload = verify_file(ASSET_FREEZE_RECEIPT, EXPECTED_ASSET_RECEIPT, "asset receipt")
    video_payload = verify_file(VIDEO_PROVENANCE, EXPECTED_VIDEO_PROVENANCE, "video provenance")
    freeze_script_payload = verify_file(FREEZE_SCRIPT, EXPECTED_FREEZE_SCRIPT, "asset-freeze helper")

    manifest_rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if (
        len(manifest_rows) != 9
        or [row["asset_id"] for row in manifest_rows]
        != [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, 10)]
        or [row["source_reference"] for row in manifest_rows] != EXPECTED_ASSET_REFS
    ):
        raise RuntimeError("Lesson 12 frozen asset manifest sequence differs")

    binary_payloads: dict[str, bytes] = {}
    for row in manifest_rows:
        path = ROOT / row["local_path"]
        payload = path.read_bytes()
        if (
            len(payload) != int(row["bytes"])
            or base.sha256(payload) != row["sha256"]
            or payload[:8] != b"\x89PNG\r\n\x1a\n"
            or row["media_type"] != "image/png"
        ):
            raise RuntimeError(f"Lesson 12 frozen image differs: {row['source_reference']}")
        binary_payloads[row["asset_id"]] = payload
    if sum(len(value) for value in binary_payloads.values()) != EXPECTED_ASSET_TOTAL_BYTES:
        raise RuntimeError("Lesson 12 frozen image byte total differs")

    video_rows = list(csv.DictReader(io.StringIO(video_payload.decode("utf-8"))))
    if (
        len(video_rows) != 3
        or [row["video_id"] for row in video_rows]
        != [f"{DOCUMENT_ID}-V{i:04d}" for i in range(1, 4)]
        or [row["source_url"] for row in video_rows] != EXPECTED_VIDEO_URLS
        or any(row["redistributed"] != "false" or row["local_binary"] for row in video_rows)
    ):
        raise RuntimeError("Lesson 12 video provenance boundary differs")

    receipt = json.loads(receipt_payload)
    external = receipt.get("external_video_boundary", {})
    if (
        receipt.get("schema") != "o006.stat415.lesson12-asset-freeze.v1"
        or receipt.get("status") != "pass"
        or receipt.get("asset_count") != 9
        or receipt.get("asset_occurrences") != 10
        or receipt.get("total_bytes") != EXPECTED_ASSET_TOTAL_BYTES
        or receipt.get("manifest", {}).get("sha256") != base.sha256(manifest_payload)
        or external.get("count") != 3
        or external.get("binary_bytes_downloaded") is not False
        or external.get("binary_bytes_redistributed") is not False
        or external.get("provenance_sha256") != base.sha256(video_payload)
        or external.get("source_urls") != EXPECTED_VIDEO_URLS
    ):
        raise RuntimeError("Lesson 12 asset-freeze receipt semantics differ")

    closure_payloads = {
        "manifest": manifest_payload,
        "receipt": receipt_payload,
        "video_provenance": video_payload,
        "freeze_script": freeze_script_payload,
    }
    return manifest_rows, video_rows, receipt, closure_payloads


def asset_inventory_csv(
    asset_rows: list[dict[str, object]],
    manifest_rows: list[dict[str, str]],
) -> bytes:
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
        "bit_depth",
        "color_type",
        "last_modified",
        "etag",
        "license",
        "disposition",
        "binary_status",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for asset, frozen in zip(asset_rows, manifest_rows):
        if asset["asset_id"] != frozen["asset_id"] or asset["source_ref"] != frozen["source_reference"]:
            raise RuntimeError("Lesson 12 normalized/frozen asset mapping differs")
        unit_ids = [value for value in asset["unit_ids"] if value]
        writer.writerow(
            {
                "asset_id": asset["asset_id"],
                "document_id": asset["document_id"],
                "component_id": asset["component_id"],
                "source_ref": asset["source_ref"],
                "source_url": asset["source_url"],
                "occurrences": asset["occurrences"],
                "first_unit_id": unit_ids[0] if unit_ids else "",
                "first_parent_unit_id": asset["first_parent_unit_id"] or "",
                "section_ids": json.dumps(asset["section_ids"], ensure_ascii=False),
                "alt_texts": json.dumps(asset["alt_texts"], ensure_ascii=False),
                "local_path": frozen["local_path"],
                "bytes": frozen["bytes"],
                "sha256": frozen["sha256"],
                "media_type": frozen["media_type"],
                "width": frozen["width"],
                "height": frozen["height"],
                "bit_depth": frozen["bit_depth"],
                "color_type": frozen["color_type"],
                "last_modified": frozen["last_modified"],
                "etag": frozen["etag"],
                "license": frozen["license"],
                "disposition": frozen["disposition"],
                "binary_status": "frozen-and-byte-verified",
            }
        )
    return stream.getvalue().encode("utf-8")


def assign_video_provenance(
    main: Tag,
    frozen_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], bytes]:
    fields = (
        "video_id",
        "document_id",
        "component_id",
        "occurrence",
        "source_url",
        "provider",
        "section_id",
        "parent_unit_id",
        "caption",
        "source_title_attribute",
        "allow",
        "allowfullscreen",
        "loading",
        "sandbox",
        "local_binary",
        "redistributed",
        "disposition",
    )
    records: list[dict[str, object]] = []
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for ordinal, (tag, frozen) in enumerate(zip(main.select("iframe[src]"), frozen_rows), start=1):
        video_id = f"{DOCUMENT_ID}-V{ordinal:04d}"
        tag["data-o006-video-id"] = video_id
        figure = tag.find_parent("figure")
        caption_tag = figure.find("figcaption") if figure else None
        section = tag.find_parent("section")
        caption = caption_tag.get_text(" ", strip=True).replace("\xa0", " ") if caption_tag else ""
        section_value = str(section.get("id")) if section else ""
        if (
            tag.get("src") != frozen["source_url"]
            or section_value != frozen["section_id"]
            or caption != frozen["caption"]
        ):
            raise RuntimeError(f"Lesson 12 video source witness differs: {video_id}")
        record: dict[str, object] = {
            "video_id": video_id,
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "occurrence": ordinal,
            "source_url": tag.get("src"),
            "provider": "YouTube",
            "section_id": section_value,
            "parent_unit_id": base.nearest_unit_id(tag) or "",
            "caption": caption,
            "source_title_attribute": tag.get("title") or "",
            "allow": tag.get("allow") or "",
            "allowfullscreen": "true" if tag.has_attr("allowfullscreen") else "false",
            "loading": tag.get("loading") or "",
            "sandbox": tag.get("sandbox") or "",
            "local_binary": "",
            "redistributed": "false",
            "disposition": "external-provenance-link-only; author offline textual/static equivalent",
        }
        records.append(record)
        writer.writerow(record)
    if len(records) != 3:
        raise RuntimeError("Lesson 12 video-provenance count differs")
    return records, stream.getvalue().encode("utf-8")


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson 12 normalization helper differs from its frozen implementation")

    manifest_rows, video_rows, freeze_receipt, closure_payloads = load_asset_closure()
    source_findings_payload = verify_file(SOURCE_FINDINGS, EXPECTED_SOURCE_FINDINGS, "source findings")
    math_audit_payload = verify_file(MATH_AUDIT, EXPECTED_MATH_AUDIT, "mathematics audit")
    terminology_qa_payload = verify_file(TERMINOLOGY_QA, EXPECTED_TERMINOLOGY_QA, "terminology audit")

    source_payload = SOURCE.read_bytes()
    if len(source_payload) != EXPECTED_SOURCE_BYTES or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Lesson 12 authority differs from the frozen 14-document manifest")
    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson 12 authority is not valid UTF-8") from exc

    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson 12 authority lacks main#quarto-document-content")
    if original_main.select("script"):
        raise RuntimeError("unexpected executable script in Lesson 12 semantic main")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson 12 page-level CC BY-NC 4.0 witness is missing")

    source_counts = base.content_counts(original_main)
    dependencies = base.dependency_census(original_main)
    source_topology_sha = base.topology_sha256(original_main)
    formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(formulas).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    code_nodes = [tag.get_text() for tag in original_main.select("pre, code")]
    code_payload = "\n".join(code_nodes).encode("utf-8")
    style_nodes = original_main.select("style")
    style_payload = "\n".join(tag.get_text() for tag in style_nodes).encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = dict(
        sorted((key, count) for key, count in Counter(native_ids).items() if count > 1)
    )
    if (
        source_counts != EXPECTED_COUNTS
        or dependencies != EXPECTED_DEPENDENCIES
        or source_topology_sha != EXPECTED_TOPOLOGY_SHA256
        or base.sha256(formula_payload) != EXPECTED_FORMULA_SHA256
        or base.sha256(semantic_text_payload) != EXPECTED_SEMANTIC_TEXT_SHA256
        or base.sha256(code_payload) != EXPECTED_EMPTY_SHA256
        or base.sha256(style_payload) != EXPECTED_EMPTY_SHA256
        or len(style_nodes) != 0
        or len(native_ids) != 76
        or len(set(native_ids)) != 67
        or duplicate_ids != EXPECTED_DUPLICATE_NATIVE_IDS
        or [tag.get("src") for tag in original_main.select("iframe[src]")] != EXPECTED_VIDEO_URLS
    ):
        raise RuntimeError("Lesson 12 topology/content/dependency/native-ID witnesses differ")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson 12 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    segment_rows = base.extract_segments(main)
    video_records, video_inventory_payload = assign_video_provenance(main, video_rows)
    role_counts = dict(sorted(Counter(str(row["role"]) for row in unit_rows).items()))
    if (
        len(unit_rows) != 846
        or len(math_rows) != 352
        or len(asset_rows) != 9
        or len(segment_rows) != 580
        or len(video_records) != 3
        or role_counts != EXPECTED_ROLE_COUNTS
        or [str(row["source_ref"]) for row in asset_rows] != EXPECTED_ASSET_REFS
    ):
        raise RuntimeError("Lesson 12 stable structural/segment/media census differs")

    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None:
        raise RuntimeError("Lesson 12 normalized semantic main is missing")
    if [tag.get_text() for tag in target_main.select("pre, code")] != code_nodes:
        raise RuntimeError("Lesson 12 code surfaces changed during normalization")
    if [tag.get("src") for tag in target_main.select("iframe[src]")] != EXPECTED_VIDEO_URLS:
        raise RuntimeError("Lesson 12 iframe sequence changed during normalization")
    if [tag.get("data-o006-video-id") for tag in target_main.select("iframe[src]")] != [
        f"{DOCUMENT_ID}-V{i:04d}" for i in range(1, 4)
    ]:
        raise RuntimeError("Lesson 12 video stable IDs changed during normalization")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 13,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson12.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson12.html",
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
        "external_video_count": len(video_records),
        "dependency_count": sum(dependencies.values()),
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
    if len(catalogue_rows) != 1_788:
        raise RuntimeError("Lesson 12 catalogue-record census differs")

    segments_payload = base.segment_csv(segment_rows)
    catalogue_payload = base.canonical_jsonl(catalogue_rows)
    asset_inventory_payload = asset_inventory_csv(asset_rows, manifest_rows)
    outputs_without_receipt: dict[str, bytes] = {
        "source/normalized/en-US/Lesson12.html": normalized_payload,
        "working/lesson12_segments.csv": segments_payload,
        "backend/lesson12_source_catalogue.jsonl": catalogue_payload,
        "working/lesson12_asset_inventory.csv": asset_inventory_payload,
        "working/lesson12_video_inventory.csv": video_inventory_payload,
    }
    output_records = {
        path: output_record(
            path,
            payload,
            **(
                {"rows": len(segment_rows)}
                if path == "working/lesson12_segments.csv"
                else {"records": len(catalogue_rows)}
                if path == "backend/lesson12_source_catalogue.jsonl"
                else {"rows": len(asset_rows)}
                if path == "working/lesson12_asset_inventory.csv"
                else {"rows": len(video_records)}
                if path == "working/lesson12_video_inventory.csv"
                else {}
            ),
        )
        for path, payload in outputs_without_receipt.items()
    }

    script_payload = SCRIPT.read_bytes()
    receipt: dict[str, object] = {
        "schema": RECEIPT_SCHEMA,
        "status": "normalized-source-and-media-ready; translation-not-started",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "assets": len(asset_rows),
            "external_video_provenance_records": len(video_records),
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
            "inline_style_nodes": len(style_nodes),
        },
        "stable_id_ranges": {
            "units": [f"{DOCUMENT_ID}-U0001", f"{DOCUMENT_ID}-U0846"],
            "math": [f"{DOCUMENT_ID}-M0001", f"{DOCUMENT_ID}-M0352"],
            "assets": [f"{DOCUMENT_ID}-A0001", f"{DOCUMENT_ID}-A0009"],
            "external_videos": [f"{DOCUMENT_ID}-V0001", f"{DOCUMENT_ID}-V0003"],
            "segments": [f"{DOCUMENT_ID}-S0001", f"{DOCUMENT_ID}-S0580"],
        },
        "role_counts": role_counts,
        "source_defect_count": 24,
        "source_defect_ids": [f"L12-D{i:03d}" for i in range(1, 25)],
        "audits": {
            "source_findings": output_record(SOURCE_FINDINGS.relative_to(ROOT).as_posix(), source_findings_payload),
            "math": output_record(MATH_AUDIT.relative_to(ROOT).as_posix(), math_audit_payload),
            "terminology": output_record(TERMINOLOGY_QA.relative_to(ROOT).as_posix(), terminology_qa_payload),
        },
        "dependency_census": dependencies,
        "asset_boundary": {
            "references_inventoried": True,
            "source_refs": EXPECTED_ASSET_REFS,
            "binary_bytes_frozen": True,
            "asset_occurrences": 10,
            "unique_assets": 9,
            "total_binary_bytes": EXPECTED_ASSET_TOTAL_BYTES,
            "manifest": output_record(ASSET_MANIFEST.relative_to(ROOT).as_posix(), closure_payloads["manifest"]),
            "freeze_receipt": output_record(ASSET_FREEZE_RECEIPT.relative_to(ROOT).as_posix(), closure_payloads["receipt"]),
            "freeze_script": output_record(FREEZE_SCRIPT.relative_to(ROOT).as_posix(), closure_payloads["freeze_script"]),
            "blocking_unresolved_image_assets": 0,
        },
        "external_video_boundary": {
            "source_urls": EXPECTED_VIDEO_URLS,
            "provenance": output_record(VIDEO_PROVENANCE.relative_to(ROOT).as_posix(), closure_payloads["video_provenance"]),
            "binary_bytes_downloaded": False,
            "binary_bytes_redistributed": False,
            "offline_text_or_static_equivalent_present": False,
            "repair_required_in_derivative": True,
            "freeze_receipt_witness": freeze_receipt["external_video_boundary"],
        },
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "code_text_sha256": base.sha256(code_payload),
            "inline_style_text_sha256": base.sha256(style_payload),
            "formula_nodes_byte_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "iframe_sequence_preserved": True,
            "authority_mutated": False,
        },
        "translation": {
            "status": "not-started",
            "target_text_fields_nonempty": 0,
            "pending_source_segments": len(segment_rows),
            "glossary_candidates_appended": False,
        },
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": (
            "semantic main only; authority immutable; formulas, tables, anchors, links, "
            "images, and iframe provenance protected; stable IDs additive"
        ),
        "script": output_record("scripts/normalize_lesson12.py", script_payload),
        "helper_script": output_record("scripts/normalize_lesson03.py", helper_payload),
        "outputs": output_records,
    }
    receipt_payload = base.canonical_json(receipt)
    return {
        **outputs_without_receipt,
        "build/LESSON12_NORMALIZATION_RECEIPT.json": receipt_payload,
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
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson 12 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson 12 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON12_NORMALIZATION_RECEIPT.json"]
    receipt = json.loads(receipt_payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "segments": receipt["counts"]["translation_segments"],
                "units": receipt["counts"]["structural_units"],
                "math": receipt["counts"]["math_nodes"],
                "assets": receipt["counts"]["assets"],
                "videos_provenance_only": receipt["counts"]["external_video_provenance_records"],
                "catalogue_records": receipt["counts"]["catalogue_records"],
                "receipt_sha256": base.sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
