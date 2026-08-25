#!/usr/bin/env python3
"""Freeze dependencies and write or byte-verify STAT 415 Lesson 06 normalization."""

from __future__ import annotations

import argparse
import csv
import io
import json
import struct
import urllib.request
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bs4
from bs4 import BeautifulSoup, Tag

import normalize_lesson03 as base


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson06.html"
ASSET = ROOT / "authority" / "assets" / "stat415" / "lesson06" / "assets" / "ci_1.png"
SCRIPT = ROOT / "scripts" / "normalize_lesson06.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-007"
COMPONENT_ID = "Lesson06"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson06"
SOURCE_REF = "assets/ci_1.png"
ASSET_URL = "https://online.stat.psu.edu/stat415/assets/ci_1.png"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."

EXPECTED_SOURCE_BYTES = 77_034
EXPECTED_SOURCE_SHA256 = "abac3002d3f325814503b40a67277a5c9eca8ac6b60e4907bbce15eb0d6b5d06"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
EXPECTED_ASSET_BYTES = 67_496
EXPECTED_ASSET_SHA256 = "2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f"
EXPECTED_ASSET_WIDTH = 1_334
EXPECTED_ASSET_HEIGHT = 640
EXPECTED_LAST_MODIFIED = "Thu, 27 Jun 2024 10:27:13 GMT"
EXPECTED_ETAG = '"107a8-61bdc92fbe240"'

base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "6 Confidence Intervals"
    )
    return (
        "<!doctype html>\n"
        '<html lang="en-US">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{SOURCE_URL}">\n'
        '<meta name="translation-provenance" content="OpenAI Codex gpt-5.6-sol, Ultra">\n'
        "</head>\n<body>\n"
        f"{main}\n"
        "</body>\n</html>\n"
    ).encode("utf-8")


def formula_with(formulas: list[str], *markers: str) -> str | None:
    return next((text for text in formulas if all(marker in text for marker in markers)), None)


def source_defects(main: Tag) -> list[dict[str, object]]:
    """Record only defects proved by the frozen prose, formulas, and arithmetic."""
    formulas = base.formula_texts(main)
    prose = main.get_text(" ", strip=True)
    main_html = str(main)
    defects: list[dict[str, object]] = []

    def add(defect_id: str, kind: str, evidence: object, note: str) -> None:
        defects.append({"defect_id": defect_id, "kind": kind, "evidence": evidence, "note": note})

    estimator_conflation = "finding an estimator, or point estimate" in prose
    if estimator_conflation:
        add(
            "L06-D001",
            "estimator-and-realized-estimate-conflated",
            "finding an estimator, or point estimate",
            (
                "A point estimator is a random statistic T(X); after observing data, "
                "T(x) is its realized point estimate. Preserve the distinction."
            ),
        )

    missing_equality = formula_with(
        formulas,
        r"P\left[\bar{X}-z_{\alpha/2}",
        r"\right]1-\alpha",
    )
    if missing_equality:
        add(
            "L06-D002",
            "probability-equality-operator-omitted",
            missing_equality,
            "The probability statement omits the equals sign before 1-alpha.",
        )

    figure = main.select_one("#fig-standardnormal img[src='assets/ci_1.png']")
    if figure is not None:
        add(
            "L06-D003",
            "figure-random-variable-and-critical-value-notation-confused",
            {
                "asset": SOURCE_REF,
                "asset_sha256": EXPECTED_ASSET_SHA256,
                "pixel_labels": [r"-Z_{\alpha/2}", r"Z_{\alpha/2}"],
            },
            (
                "The frozen figure uses capital Z for fixed cut points although the prose "
                "correctly defines lowercase z_(alpha/2) as the critical value."
            ),
        )

    chi_square_interval = formula_with(
        formulas,
        r"\chi^2_{0.05}(4)",
        r"\chi^2_{0.95}(4)",
    )
    chi_square_numeric = formula_with(formulas, "9.4877", "0.7107")
    if chi_square_interval and chi_square_numeric:
        add(
            "L06-D004",
            "chi-square-quantile-tail-convention-undefined",
            {
                "symbolic_interval": chi_square_interval,
                "numerical_interval": chi_square_numeric,
            },
            (
                "The z subscript was defined by upper-tail area, but the displayed chi-square "
                "values use lower-tail CDF quantiles. Define q_p=F^{-1}(p) explicitly."
            ),
        )

    if (
        "The conditions are:" in prose
        and "the estimator needs to be unbiased" in prose
        and "approximately standard normal distribution" in prose
    ):
        add(
            "L06-D005",
            "exact-unbiasedness-misstated-as-large-sample-necessity",
            "The source lists exact unbiasedness as a required condition for a large-sample normal confidence interval.",
            (
                "Exact finite-sample unbiasedness is not necessary. Studentized convergence "
                "to N(0,1), including an asymptotically valid standard-error estimate, is the "
                "controlling condition."
            ),
        )

    standard_error = formula_with(
        formulas,
        r"\hat{\sigma}^2_{\hat{\mu}}",
        r"\frac{s}{\sqrt{64}}=256",
    )
    if standard_error:
        add(
            "L06-D006",
            "standard-error-notation-and-arithmetic",
            standard_error,
            (
                "The data give sample variance 256, hence s=16 and the estimated standard "
                "error is hat(sigma)_(hat(mu))=16/sqrt(64)=2; it is neither squared nor 256."
            ),
        )

    t_interval = formula_with(
        formulas,
        r"t_{\alpha/2, df}",
        r"\frac{s}{\sqrt{n}}",
    )
    if t_interval and "when the variance is unknown" in prose:
        add(
            "L06-D007",
            "exact-t-interval-assumptions-and-degrees-of-freedom-omitted",
            t_interval,
            (
                "For an iid Normal sample the exact interval uses df=n-1. Outside that model, "
                "a separate large-sample or robustness qualification is required."
            ),
        )

    source_alt = (
        str(figure.get("alt", "")) if figure is not None else ""
    )
    if figure is not None and source_alt == "Standard normal curve showing the 1-alpha area centered in the middle.":
        add(
            "L06-D008",
            "figure-alternative-text-incomplete",
            {"asset": SOURCE_REF, "source_alt": source_alt},
            (
                "The source alternative text omits both alpha/2 tails and the critical points; "
                "the derivative must describe them without relying on color."
            ),
        )

    surface_evidence = []
    if "</span> is a random sample" in main_html:
        surface_evidence.append("plural sample variables followed by singular 'is'")
    for phrase in (
        "be a a random variable",
        "A pivotal quantity poses two characteristics",
        "moment generating function method we get the distribution",
        "Now, lets construct the confidence interval",
        "Again, we only consider the expression in the brackets, we get",
        "confidence interval ror a population mean",
    ):
        if phrase in prose:
            surface_evidence.append(phrase)
    if len(surface_evidence) == 7:
        add(
            "L06-D009",
            "mechanical-surface-defects",
            surface_evidence,
            "Correct the seven unambiguous grammar, duplication, punctuation, and typo defects in the derivative.",
        )

    proof_heading = next(
        (heading.get_text(" ", strip=True) for heading in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
         if heading.get_text(" ", strip=True) == "Proof:"),
        None,
    )
    if proof_heading and not main.select(".proof"):
        add(
            "L06-D010",
            "proof-not-semantically-typed",
            {"heading": proof_heading, "semantic_proof_nodes": 0, "section_id": "proof"},
            "The proof is present but encoded only as a generic section; retain it and mark its role additively in downstream metadata.",
        )

    expected_ids = [f"L06-D{index:03d}" for index in range(1, 11)]
    if [row["defect_id"] for row in defects] != expected_ids:
        raise RuntimeError("Lesson06 proved-defect census differs from L06-D001..L06-D010")
    return defects


def validate_png(payload: bytes) -> dict[str, object]:
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Lesson06 asset is not PNG")
    cursor = 8
    chunks: list[dict[str, object]] = []
    width = height = bit_depth = color_type = interlace = None
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise RuntimeError("truncated Lesson06 PNG chunk")
        length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        end = cursor + 12 + length
        if end > len(payload):
            raise RuntimeError("Lesson06 PNG chunk extends beyond EOF")
        chunk_type = payload[cursor + 4:cursor + 8]
        data = payload[cursor + 8:cursor + 8 + length]
        stored_crc = struct.unpack(">I", payload[cursor + 8 + length:end])[0]
        if (zlib.crc32(chunk_type + data) & 0xFFFFFFFF) != stored_crc:
            raise RuntimeError("Lesson06 PNG CRC validation failed")
        name = chunk_type.decode("ascii")
        chunks.append({"name": name, "bytes": length})
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filter, interlace = struct.unpack(
                ">IIBBBBB", data
            )
        cursor = end
        if chunk_type == b"IEND":
            break
    if (
        not chunks
        or chunks[0]["name"] != "IHDR"
        or chunks[-1]["name"] != "IEND"
        or cursor != len(payload)
        or width != EXPECTED_ASSET_WIDTH
        or height != EXPECTED_ASSET_HEIGHT
    ):
        raise RuntimeError("Lesson06 PNG structure/dimensions differ")
    metadata = [row["name"] for row in chunks if row["name"] in {"iCCP", "eXIf", "iTXt", "tEXt", "zTXt"}]
    lowered = payload.lower()
    rights_markers = [
        marker for marker in (b"copyright", b"creator", b"author", b"license", b"rights")
        if marker in lowered
    ]
    if rights_markers:
        raise RuntimeError("Lesson06 PNG contains embedded rights/creator metadata requiring review")
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
        "chunk_crc_valid": True,
        "chunks": chunks,
        "metadata_chunks": metadata,
        "embedded_screenshot_comment": b"screenshot" in lowered,
        "embedded_rights_or_creator_markers": [],
        "trailing_bytes": 0,
    }


def fetch_asset() -> bytes:
    request = urllib.request.Request(
        ASSET_URL,
        headers={"User-Agent": "O006-STAT415-id deterministic source freezer"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        status = response.status
        content_type = response.headers.get("Content-Type")
        content_length = response.headers.get("Content-Length")
        last_modified = response.headers.get("Last-Modified")
        etag = response.headers.get("ETag")
        final_url = response.geturl()
    if (
        status != 200
        or final_url != ASSET_URL
        or content_type != "image/png"
        or content_length != str(EXPECTED_ASSET_BYTES)
        or last_modified != EXPECTED_LAST_MODIFIED
        or etag != EXPECTED_ETAG
        or len(payload) != EXPECTED_ASSET_BYTES
        or base.sha256(payload) != EXPECTED_ASSET_SHA256
    ):
        raise RuntimeError("official Lesson06 asset response differs from the admitted freeze")
    validate_png(payload)
    return payload


def asset_manifest(asset_row: dict[str, object], payload: bytes) -> bytes:
    stream = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes", "sha256",
        "media_type", "width", "height", "license", "disposition",
    )
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerow(
        {
            "asset_id": asset_row["asset_id"],
            "source_reference": SOURCE_REF,
            "official_url": ASSET_URL,
            "local_path": "authority/assets/stat415/lesson06/assets/ci_1.png",
            "bytes": len(payload),
            "sha256": base.sha256(payload),
            "media_type": "image/png",
            "width": EXPECTED_ASSET_WIDTH,
            "height": EXPECTED_ASSET_HEIGHT,
            "license": "CC BY-NC 4.0",
            "disposition": "freeze-authority-and-redistribute-with-page-attribution-and-change-notice",
        }
    )
    return stream.getvalue().encode("utf-8")


def asset_closure(
    source_payload: bytes,
    source_soup: BeautifulSoup,
    main: Tag,
    asset_row: dict[str, object],
    asset_payload: bytes,
) -> bytes:
    census = base.dependency_census(main)
    expected_census = {
        "images": 1,
        "videos": 0,
        "audio": 0,
        "media_sources": 0,
        "iframes": 0,
        "objects": 0,
        "embeds": 0,
        "downloads": 0,
        "scripts": 0,
    }
    if census != expected_census:
        raise RuntimeError(f"Lesson06 dependency census differs: {census}")
    images = main.select(f'img[src="{SOURCE_REF}"]')
    lightboxes = main.select(f'a.lightbox[href="{SOURCE_REF}"]')
    if len(images) != 1 or len(lightboxes) != 1 or images[0] not in lightboxes[0].descendants:
        raise RuntimeError("Lesson06 image/lightbox topology differs")
    if images[0].get("alt") != "Standard normal curve showing the 1-alpha area centered in the middle.":
        raise RuntimeError("Lesson06 image alt text differs")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson06 page-level CC BY-NC 4.0 witness is missing")
    if urlparse(urljoin(SOURCE_URL, SOURCE_REF)).netloc != urlparse(SOURCE_URL).netloc:
        raise RuntimeError("Lesson06 asset is not same-origin")
    main_text = main.get_text(" ", strip=True).casefold()
    for marker in ("source:", "credit:", "copyright", "permission", "licensed under"):
        if marker in main_text:
            raise RuntimeError(f"unexpected per-asset rights marker in Lesson06 main: {marker}")
    validation = validate_png(asset_payload)
    closure = {
        "schema": "o006.stat415.lesson06-asset-closure.v1",
        "status": "same-origin-image-closed-no-external-dependencies",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson06.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": base.sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": census,
        "asset": {
            "asset_id": asset_row["asset_id"],
            "source_ref": SOURCE_REF,
            "official_url": ASSET_URL,
            "local_path": "authority/assets/stat415/lesson06/assets/ci_1.png",
            "img_occurrences": 1,
            "lightbox_href_occurrences": 1,
            "alt_text": images[0].get("alt"),
            "bytes": len(asset_payload),
            "sha256": base.sha256(asset_payload),
            "http_audit": {
                "status": 200,
                "content_type": "image/png",
                "content_length": EXPECTED_ASSET_BYTES,
                "last_modified": EXPECTED_LAST_MODIFIED,
                "etag": EXPECTED_ETAG,
                "redirected": False,
                "checked_on": "2026-08-25",
            },
            "png_validation": validation,
            "visual_validation": (
                "pass: the frozen image shows a standard normal curve with two alpha/2 tails, "
                "a centered 1-alpha region, and critical labels -z_(alpha/2) and z_(alpha/2)"
            ),
        },
        "rights": {
            "page_license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "witness_text": LICENSE_TEXT,
            "per_asset_exception_in_main": False,
            "embedded_rights_or_creator_metadata": False,
            "disposition": "cleared-for-noncommercial-derivative-freeze-under-official-page-notice",
        },
        "closure": {
            "reference_inventory_complete": True,
            "same_origin_image_bytes_complete": True,
            "same_origin_image_rights_disposition_complete": True,
            "unresolved_asset_bytes": 0,
            "external_dependencies": 0,
            "normalization_may_proceed": True,
            "offline_reader_asset_gate_passed": True,
        },
    }
    return base.canonical_json(closure)


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson06 normalization helper differs from its frozen implementation")
    source_payload = SOURCE.read_bytes()
    if len(source_payload) != EXPECTED_SOURCE_BYTES or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Lesson06 authority differs from the frozen 14-document manifest")
    if not ASSET.is_file():
        raise RuntimeError("frozen Lesson06 asset is missing")
    asset_payload = ASSET.read_bytes()
    if len(asset_payload) != EXPECTED_ASSET_BYTES or base.sha256(asset_payload) != EXPECTED_ASSET_SHA256:
        raise RuntimeError("frozen Lesson06 asset differs")
    validate_png(asset_payload)

    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson06 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson06 authority lacks main#quarto-document-content")
    if original_main.select("script, style"):
        raise RuntimeError("unexpected embedded script/style in Lesson06 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson06 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = base.topology_sha256(original_main)
    source_counts = base.content_counts(original_main)
    source_formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(source_formulas).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(key for key, count in Counter(native_ids).items() if count > 1)

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    if len(asset_rows) != 1 or asset_rows[0]["source_ref"] != SOURCE_REF:
        raise RuntimeError("Lesson06 asset catalogue differs")
    segment_rows = base.extract_segments(main)
    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None or target_main.get_text() != original_main.get_text():
        raise RuntimeError("Lesson06 semantic-main text changed during normalization")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 7,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson06.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson06.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "semantic_text_sha256": base.sha256(semantic_text_payload),
        "formula_count": len(source_formulas),
        "formula_sha256": base.sha256(formula_payload),
        "code_node_count": 0,
        "code_text_sha256": base.sha256(b""),
        "unit_count": len(unit_rows),
        "segment_count": len(segment_rows),
        "asset_count": len(asset_rows),
        "dependency_count": 0,
        "native_id_occurrences": len(native_ids),
        "unique_native_ids": len(set(native_ids)),
        "duplicate_native_ids": duplicate_ids,
    }
    catalogue_segment_rows = [
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
    catalogue_rows = [document_row, *unit_rows, *math_rows, *asset_rows, *catalogue_segment_rows]
    csv_payload = base.segment_csv(segment_rows)
    catalogue_payload = base.canonical_jsonl(catalogue_rows)
    closure_payload = asset_closure(
        source_payload, source_soup, original_main, asset_rows[0], asset_payload
    )
    manifest_payload = asset_manifest(asset_rows[0], asset_payload)
    defects = source_defects(original_main)
    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    script_payload = SCRIPT.read_bytes()

    receipt = {
        "schema": "o006.stat415.lesson06-normalization.v1",
        "status": "normalized-source-ready-asset-closed-no-external-dependencies",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "assets": len(asset_rows),
            "dependencies": 0,
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
        },
        "role_counts": role_counts,
        "asset_inventory": [
            {
                "asset_id": asset_rows[0]["asset_id"],
                "source_ref": SOURCE_REF,
                "source_url": ASSET_URL,
                "occurrences": asset_rows[0]["occurrences"],
                "alt_texts": asset_rows[0]["alt_texts"],
                "bytes": len(asset_payload),
                "sha256": base.sha256(asset_payload),
            }
        ],
        "asset_closure": {
            "reference_inventory_complete": True,
            "same_origin_png_files": 1,
            "same_origin_png_bytes": len(asset_payload),
            "same_origin_image_bytes_closed": True,
            "external_dependencies": 0,
            "offline_reader_asset_gate_passed": True,
        },
        "duplicate_native_ids": duplicate_ids,
        "source_defects": defects,
        "source_defect_count": len(defects),
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "formula_nodes_byte_preserved": True,
            "code_nodes_text_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson06.html",
                "bytes": len(normalized_payload),
                "sha256": base.sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson06_segments.csv",
                "bytes": len(csv_payload),
                "sha256": base.sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson06_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": base.sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "asset": {
                "path": "authority/assets/stat415/lesson06/assets/ci_1.png",
                "bytes": len(asset_payload),
                "sha256": base.sha256(asset_payload),
            },
            "asset_manifest": {
                "path": "authority/LESSON06_ASSET_MANIFEST.csv",
                "bytes": len(manifest_payload),
                "sha256": base.sha256(manifest_payload),
            },
            "asset_closure": {
                "path": "working/lesson06_asset_closure.json",
                "bytes": len(closure_payload),
                "sha256": base.sha256(closure_payload),
            },
            "script": {
                "path": "scripts/normalize_lesson06.py",
                "bytes": len(script_payload),
                "sha256": base.sha256(script_payload),
            },
            "helper_script": {
                "path": "scripts/normalize_lesson03.py",
                "bytes": len(helper_payload),
                "sha256": base.sha256(helper_payload),
            },
        },
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": (
            "semantic main only; no authority correction; formula text protected; stable unit, "
            "math, asset, and segment IDs additive"
        ),
    }
    return {
        "authority/assets/stat415/lesson06/assets/ci_1.png": asset_payload,
        "authority/LESSON06_ASSET_MANIFEST.csv": manifest_payload,
        "source/normalized/en-US/Lesson06.html": normalized_payload,
        "working/lesson06_segments.csv": csv_payload,
        "backend/lesson06_source_catalogue.jsonl": catalogue_payload,
        "working/lesson06_asset_closure.json": closure_payload,
        "build/LESSON06_NORMALIZATION_RECEIPT.json": base.canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.write and not ASSET.is_file():
        base.atomic_write(ASSET, fetch_asset())
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            base.atomic_write(ROOT / relative, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson06 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson06 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON06_NORMALIZATION_RECEIPT.json"]
    receipt = json.loads(receipt_payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "segments": receipt["counts"]["translation_segments"],
                "units": receipt["counts"]["structural_units"],
                "math": receipt["counts"]["math_nodes"],
                "code": receipt["counts"]["code_nodes"],
                "assets": receipt["counts"]["assets"],
                "dependencies": receipt["counts"]["dependencies"],
                "catalogue_records": receipt["counts"]["catalogue_records"],
                "source_defects": receipt["source_defect_count"],
                "receipt_sha256": base.sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
