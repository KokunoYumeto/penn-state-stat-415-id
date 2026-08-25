#!/usr/bin/env python3
"""Freeze dependencies and write or byte-verify STAT 415 Lesson 07 normalization."""

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
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson07.html"
SCRIPT = ROOT / "scripts" / "normalize_lesson07.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-008"
COMPONENT_ID = "Lesson07"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson07"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."

EXPECTED_SOURCE_BYTES = 105_026
EXPECTED_SOURCE_SHA256 = "2351d07b45be5be79373d0e641a38703b2554c729c250537791c271bce85018c"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
EXPECTED_FORMULA_SHA256 = "c2da24f78e6d812d1bd5245e5cb671b52c1f3c5053de56e8141d13512fa36bb3"
EXPECTED_CODE_SHA256 = "13fd8dd901b6d2b5c74d5b0fb06308684cbd29b5afb9e88913dd30a391b411c5"
EXPECTED_TEXT_SHA256 = "8d2e049caea5ae07bb28954c0f0162a2623f2dac8c7525ac7cafeb93675feafa"
EXPECTED_TOPOLOGY_SHA256 = "2a5de57cd542d33c0dd5b24c028b19c86f34bed16f5c9887181b4f3b25ddb17c"

EXPECTED_COUNTS = {
    "asset_occurrences": 2,
    "code_nodes": 47,
    "corollaries": 0,
    "definitions": 0,
    "examples": 6,
    "figure_captions": 2,
    "figures": 4,
    "headings": 17,
    "images": 2,
    "links": 44,
    "math_display": 26,
    "math_inline": 122,
    "math_nodes": 148,
    "pre_nodes": 28,
    "proofs": 0,
    "sections": 16,
    "solutions": 6,
    "tables": 1,
    "theorem_class_nodes": 6,
    "theorems": 0,
    "unique_asset_sources": 2,
}

EXPECTED_ROLE_COUNTS = {
    "code": 75,
    "example": 6,
    "figure": 4,
    "figure-caption": 2,
    "heading": 12,
    "image": 2,
    "link": 44,
    "section": 10,
    "solution": 12,
    "structure": 232,
}

ASSETS = (
    {
        "asset_id": "O006-PSU-008-A0001",
        "source_ref": "Lesson07_files/figure-html/unnamed-chunk-1-1.png",
        "url": "https://online.stat.psu.edu/stat415/Lesson07_files/figure-html/unnamed-chunk-1-1.png",
        "local_path": "authority/assets/stat415/lesson07/Lesson07_files/figure-html/unnamed-chunk-1-1.png",
        "bytes": 51_500,
        "sha256": "261e8fee2ada5d25b3cf92d4fde1825dfcce67f97629120efc6d432b06a89372",
        "width": 1_344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:45:17 GMT",
        "etag": '"c92c-659ccdf6e1d40"',
        "alt": "Histogram of geometric distribution",
        "unit_id": "O006-PSU-008-U0186",
        "parent_unit_id": "O006-PSU-008-U0185",
        "section_id": "single-parameter-case",
        "visual_validation": (
            "pass: histogram of the frozen geometric sample, with integer-valued bars "
            "concentrated near zero and a long right tail extending to about 27"
        ),
    },
    {
        "asset_id": "O006-PSU-008-A0002",
        "source_ref": "Lesson07_files/figure-html/unnamed-chunk-6-1.png",
        "url": "https://online.stat.psu.edu/stat415/Lesson07_files/figure-html/unnamed-chunk-6-1.png",
        "local_path": "authority/assets/stat415/lesson07/Lesson07_files/figure-html/unnamed-chunk-6-1.png",
        "bytes": 49_223,
        "sha256": "18e14d1763554c43bcc8c31ba57756918ea7e47985abbf840f40ee3842460e65",
        "width": 1_344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:45:17 GMT",
        "etag": '"c047-659ccdf6e1d40"',
        "alt": "Histogram of normal distribution",
        "unit_id": "O006-PSU-008-U0301",
        "parent_unit_id": "O006-PSU-008-U0300",
        "section_id": "multiple-parameter-case",
        "visual_validation": (
            "pass: histogram of the seeded Normal sample, roughly bell-shaped and centered "
            "near -7, spanning approximately -16 to 3"
        ),
    },
)

base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = source_soup.title.get_text(" ", strip=True) if source_soup.title else "7 Asymptotic Distribution of MLE (Part I)"
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
    """Return only high-confidence defects proved by frozen Lesson07 bytes."""
    formulas = base.formula_texts(main)
    prose = main.get_text(" ", strip=True)
    code = "\n".join(tag.get_text() for tag in main.select("code"))
    defects: list[dict[str, object]] = []

    def add(defect_id: str, kind: str, stable_evidence: object, note: str) -> None:
        defects.append(
            {
                "defect_id": defect_id,
                "kind": kind,
                "stable_evidence": stable_evidence,
                "note": note,
            }
        )

    if "A corollary to this is" in prose and r"E(\hat{\theta}_{mle})" in "\n".join(formulas):
        add(
            "L07-D001",
            "consistency-does-not-imply-expectation-convergence",
            {
                "unit_id": "O006-PSU-008-U0038",
                "segment_ids": ["O006-PSU-008-S0025", "O006-PSU-008-S0026", "O006-PSU-008-S0027", "O006-PSU-008-S0028", "O006-PSU-008-S0029", "O006-PSU-008-S0030"],
            },
            (
                "Convergence in probability alone does not imply convergence of expectations; "
                "uniform integrability (or another sufficient moment condition) is additionally needed."
            ),
        )

    expected_info = formula_with(formulas, r"I(\hat{\theta}_{mle})=-E", r"\ell(\hat{\theta})")
    if expected_info and "hessian is the Fisher Information" in prose:
        add(
            "L07-D002",
            "expected-and-observed-information-conflated",
            {
                "math_ids": ["O006-PSU-008-M0043", "O006-PSU-008-M0102"],
                "segment_ids": ["O006-PSU-008-S0190", "O006-PSU-008-S0191", "O006-PSU-008-S0192", "O006-PSU-008-S0193", "O006-PSU-008-S0194", "O006-PSU-008-S0195", "O006-PSU-008-S0196"],
            },
            (
                "Expected Fisher information is an expectation at a parameter value; optim's "
                "returned Hessian of the minimized negative log-likelihood is observed information."
            ),
        )

    bernoulli_ci = formula_with(formulas, r"0.6\pm \sqrt", "0.3036")
    if bernoulli_ci:
        add(
            "L07-D003",
            "bernoulli-confidence-interval-intermediate-factor-omitted",
            {"math_id": "O006-PSU-008-M0088", "source_formula": bernoulli_ci},
            "The intermediate numeric margin omits 1.96 even though 0.3036 and the endpoints include it.",
        )

    exponential_ci = formula_with(formulas, r"\sqrt{\frac{1}{I(\hat{\theta})}}", r"\sqrt{\frac{n^3}{\bar{x}^2}}")
    if exponential_ci:
        add(
            "L07-D004",
            "exponential-confidence-interval-reciprocal-error",
            {"math_id": "O006-PSU-008-M0104", "source_formula": exponential_ci},
            (
                "Because I(hat theta)=n/bar(x)^2, the standard-error term is "
                "sqrt(bar(x)^2/n)=bar(x)/sqrt(n), not sqrt(n^3/bar(x)^2)."
            ),
        )

    if "5.469399" in prose and "38.620385" in prose and "-6.564774" in code and "12.773473" in code:
        add(
            "L07-D005",
            "normal-example-prose-disagrees-with-frozen-optimizer-output",
            {
                "segment_ids": ["O006-PSU-008-S0212", "O006-PSU-008-S0213", "O006-PSU-008-S0214"],
                "output_values": [-6.564774, 12.773473],
                "prose_values": [5.469399, 38.620385],
            },
            "The prose must report the MLE pair printed by the immediately preceding frozen output.",
        )

    if (
        "out=optim(0.5,nll.geom,x=x)" in code
        and "out=optim(c(-11,1),nll.norm,x=x,hessian=TRUE)" in code
        and "sqrt(vr)" in code
    ):
        add(
            "L07-D006",
            "numerical-optimization-parameter-domains-unguarded",
            {
                "code_unit_ids": [
                    "O006-PSU-008-U0194",
                    "O006-PSU-008-U0206",
                    "O006-PSU-008-U0309",
                    "O006-PSU-008-U0325",
                ],
                "domains": ["0 < p <= 1", "sigma^2 > 0"],
            },
            (
                "The geometric probability and Normal variance have constrained domains; the "
                "demonstration uses unconstrained optim calls and evaluates sqrt(vr) without a guard."
            ),
        )

    if "CI for the MLE of" in prose:
        add(
            "L07-D007",
            "confidence-interval-target-mislabeled-as-estimator",
            {
                "segment_ids": [
                    "O006-PSU-008-S0177",
                    "O006-PSU-008-S0195",
                    "O006-PSU-008-S0196",
                    "O006-PSU-008-S0197",
                    "O006-PSU-008-S0198",
                    "O006-PSU-008-S0199",
                ]
            },
            "The interval estimates the parameter p; the MLE is the statistic used to construct it.",
        )

    if "introduces the bootstrap method" in prose and "Delta method" in prose and "t-distributed and Pareto datasets" in prose:
        add(
            "L07-D008",
            "overview-and-summary-claim-content-absent-from-body",
            {
                "segment_ids": ["O006-PSU-008-S0009", "O006-PSU-008-S0010", "O006-PSU-008-S0236", "O006-PSU-008-S0237"],
                "absent_body_topics": ["parametric bootstrap", "nonparametric bootstrap", "Delta method", "t example", "Pareto example"],
            },
            "The named methods and examples are announced in overview/summary but are not taught in the lesson body.",
        )

    if "The PMF is" in prose and r"\text{Exp}(\theta)" in "\n".join(formulas):
        add(
            "L07-D009",
            "continuous-exponential-density-called-pmf",
            {"segment_ids": ["O006-PSU-008-S0138", "O006-PSU-008-S0139"], "math_id": "O006-PSU-008-M0093"},
            "The exponential model is continuous: f is a probability density (PDF), with x >= 0.",
        )

    if "standard errors = sqrt(1/I.inv[p,p])" in code and "sqrt(diag(solve(I)))" in code:
        add(
            "L07-D010",
            "standard-error-code-comment-reverses-matrix-inverse-entry",
            {"unit_id": "O006-PSU-008-U0353", "source_comment": "standard errors = sqrt(1/I.inv[p,p])"},
            "The executing code is correct: standard errors are sqrt((I^{-1})[p,p]), not sqrt(1/(I^{-1})[p,p]).",
        )

    surfaces = {
        "O006-PSU-008-S0049": "respectfully",
        "O006-PSU-008-S0061": ".Therefore",
        "O006-PSU-008-S0089": "Next, lets",
        "O006-PSU-008-S0099": "Single Parmater",
        "O006-PSU-008-S0131": "it is chosen it",
        "O006-PSU-008-M0098": r"\frac{d}{d\theta}=-",
        "O006-PSU-008-S0152": "Multiple Parmater",
        "O006-PSU-008-S0155": "as follows. as",
        "O006-PSU-008-S0169": "-the parameter",
    }
    if all(marker in ("\n".join(formulas) if entity.endswith("M0098") else prose) for entity, marker in surfaces.items()):
        add(
            "L07-D011",
            "mechanical-surface-defects",
            {"entities": list(surfaces), "markers": list(surfaces.values())},
            "Correct the nine unambiguous spelling, spacing, grammar, and missing-expression surfaces in translation.",
        )

    if "The estimator" in prose and "is NOT on the edge of allowable values" in prose and "MLE is not in the support" in prose:
        add(
            "L07-D012",
            "parameter-boundary-condition-confused-with-data-support",
            {
                "segment_ids": ["O006-PSU-008-S0019", "O006-PSU-008-S0020"],
                "math_id": "O006-PSU-008-M0002",
            },
            (
                "The standard interior-point condition concerns the true parameter and the "
                "boundary of the parameter space; the support is the set of possible data values."
            ),
        )

    expected_ids = [f"L07-D{index:03d}" for index in range(1, 13)]
    if [row["defect_id"] for row in defects] != expected_ids:
        raise RuntimeError("Lesson07 proved-defect census differs from L07-D001..L07-D012")
    return defects


def validate_png(payload: bytes, spec: dict[str, object]) -> dict[str, object]:
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"{spec['asset_id']} is not PNG")
    cursor = 8
    chunks: list[dict[str, object]] = []
    width = height = bit_depth = color_type = interlace = None
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise RuntimeError(f"truncated PNG chunk in {spec['asset_id']}")
        length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        end = cursor + 12 + length
        if end > len(payload):
            raise RuntimeError(f"PNG chunk extends beyond EOF in {spec['asset_id']}")
        chunk_type = payload[cursor + 4:cursor + 8]
        data = payload[cursor + 8:cursor + 8 + length]
        stored_crc = struct.unpack(">I", payload[cursor + 8 + length:end])[0]
        if (zlib.crc32(chunk_type + data) & 0xFFFFFFFF) != stored_crc:
            raise RuntimeError(f"PNG CRC validation failed in {spec['asset_id']}")
        name = chunk_type.decode("ascii")
        chunks.append({"name": name, "bytes": length})
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filter, interlace = struct.unpack(">IIBBBBB", data)
        cursor = end
        if chunk_type == b"IEND":
            break
    if (
        not chunks
        or chunks[0]["name"] != "IHDR"
        or chunks[-1]["name"] != "IEND"
        or cursor != len(payload)
        or width != spec["width"]
        or height != spec["height"]
    ):
        raise RuntimeError(f"PNG structure/dimensions differ for {spec['asset_id']}")
    lowered = payload.lower()
    rights_markers = [
        marker.decode("ascii")
        for marker in (b"copyright", b"creator", b"author", b"license", b"rights")
        if marker in lowered
    ]
    if rights_markers:
        raise RuntimeError(f"embedded rights/creator marker in {spec['asset_id']}: {rights_markers}")
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
        "chunk_crc_valid": True,
        "chunks": chunks,
        "metadata_chunks": [row["name"] for row in chunks if row["name"] in {"iCCP", "eXIf", "iTXt", "tEXt", "zTXt"}],
        "embedded_rights_or_creator_markers": [],
        "trailing_bytes": 0,
    }


def fetch_asset(spec: dict[str, object]) -> bytes:
    request = urllib.request.Request(
        str(spec["url"]),
        headers={"User-Agent": "O006-STAT415-id deterministic source freezer"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        observed = {
            "status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "content_length": response.headers.get("Content-Length"),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "final_url": response.geturl(),
        }
    expected = {
        "status": 200,
        "content_type": "image/png",
        "content_length": str(spec["bytes"]),
        "last_modified": spec["last_modified"],
        "etag": spec["etag"],
        "final_url": spec["url"],
    }
    if observed != expected or len(payload) != spec["bytes"] or base.sha256(payload) != spec["sha256"]:
        raise RuntimeError(f"official response differs from admitted freeze for {spec['asset_id']}: {observed}")
    validate_png(payload, spec)
    return payload


def asset_manifest(asset_rows: list[dict[str, object]], payloads: dict[str, bytes]) -> bytes:
    stream = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes", "sha256",
        "media_type", "width", "height", "license", "disposition",
    )
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row, spec in zip(asset_rows, ASSETS, strict=True):
        payload = payloads[str(spec["local_path"])]
        writer.writerow(
            {
                "asset_id": row["asset_id"],
                "source_reference": spec["source_ref"],
                "official_url": spec["url"],
                "local_path": spec["local_path"],
                "bytes": len(payload),
                "sha256": base.sha256(payload),
                "media_type": "image/png",
                "width": spec["width"],
                "height": spec["height"],
                "license": "CC BY-NC 4.0",
                "disposition": "freeze-authority-and-redistribute-with-page-attribution-and-change-notice",
            }
        )
    return stream.getvalue().encode("utf-8")


def asset_closure(
    source_payload: bytes,
    source_soup: BeautifulSoup,
    main: Tag,
    asset_rows: list[dict[str, object]],
    payloads: dict[str, bytes],
) -> bytes:
    census = base.dependency_census(main)
    expected_census = {
        "images": 2,
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
        raise RuntimeError(f"Lesson07 dependency census differs: {census}")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson07 page-level CC BY-NC 4.0 witness is missing")
    main_text = main.get_text(" ", strip=True).casefold()
    for marker in ("source:", "credit:", "copyright", "permission", "licensed under"):
        if marker in main_text:
            raise RuntimeError(f"unexpected per-asset rights marker in Lesson07 main: {marker}")

    closed_assets: list[dict[str, object]] = []
    for row, spec in zip(asset_rows, ASSETS, strict=True):
        images = main.select(f'img[src="{spec["source_ref"]}"]')
        if len(images) != 1 or images[0].get("alt") != spec["alt"]:
            raise RuntimeError(f"Lesson07 image occurrence/alt differs for {spec['asset_id']}")
        if urlparse(urljoin(SOURCE_URL, str(spec["source_ref"]))).netloc != urlparse(SOURCE_URL).netloc:
            raise RuntimeError(f"Lesson07 asset is not same-origin: {spec['asset_id']}")
        if row["asset_id"] != spec["asset_id"] or row["unit_ids"] != [spec["unit_id"]]:
            raise RuntimeError(f"Lesson07 stable asset topology differs for {spec['asset_id']}")
        payload = payloads[str(spec["local_path"])]
        closed_assets.append(
            {
                "asset_id": row["asset_id"],
                "source_ref": spec["source_ref"],
                "official_url": spec["url"],
                "local_path": spec["local_path"],
                "img_occurrences": 1,
                "alt_text": spec["alt"],
                "bytes": len(payload),
                "sha256": base.sha256(payload),
                "http_audit": {
                    "status": 200,
                    "content_type": "image/png",
                    "content_length": spec["bytes"],
                    "last_modified": spec["last_modified"],
                    "etag": spec["etag"],
                    "redirected": False,
                    "checked_on": "2026-08-25",
                },
                "png_validation": validate_png(payload, spec),
                "visual_validation": spec["visual_validation"],
                "reader_accessibility": {
                    "source_alt_is_nonempty": True,
                    "source_alt_is_complete": False,
                    "translation_requirement": "replace generic distribution label with the recorded visual description",
                },
            }
        )

    closure = {
        "schema": "o006.stat415.lesson07-asset-closure.v1",
        "status": "same-origin-images-closed-no-external-dependencies-reader-alt-remediation-required",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson07.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": base.sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": census,
        "assets": closed_assets,
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
            "offline_reader_asset_gate_passed": False,
            "reader_alt_repairs_required": 2,
        },
    }
    return base.canonical_json(closure)


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson07 normalization helper differs from its frozen implementation")
    source_payload = SOURCE.read_bytes()
    if len(source_payload) != EXPECTED_SOURCE_BYTES or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Lesson07 authority differs from its frozen manifest identity")

    asset_payloads: dict[str, bytes] = {}
    for spec in ASSETS:
        path = ROOT / str(spec["local_path"])
        if not path.is_file():
            raise RuntimeError(f"frozen Lesson07 asset is missing: {spec['local_path']}")
        payload = path.read_bytes()
        if len(payload) != spec["bytes"] or base.sha256(payload) != spec["sha256"]:
            raise RuntimeError(f"frozen Lesson07 asset differs: {spec['asset_id']}")
        validate_png(payload, spec)
        asset_payloads[str(spec["local_path"])] = payload

    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson07 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson07 authority lacks main#quarto-document-content")
    if original_main.select("script"):
        raise RuntimeError("unexpected executable script in Lesson07 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson07 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = base.topology_sha256(original_main)
    source_counts = base.content_counts(original_main)
    source_formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(source_formulas).encode("utf-8")
    source_code_texts = [tag.get_text() for tag in original_main.select("code")]
    code_payload = "\n".join(source_code_texts).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(key for key, count in Counter(native_ids).items() if count > 1)
    if (
        source_counts != EXPECTED_COUNTS
        or source_topology_sha != EXPECTED_TOPOLOGY_SHA256
        or base.sha256(formula_payload) != EXPECTED_FORMULA_SHA256
        or base.sha256(code_payload) != EXPECTED_CODE_SHA256
        or base.sha256(semantic_text_payload) != EXPECTED_TEXT_SHA256
        or len(native_ids) != 85
        or len(set(native_ids)) != 85
        or duplicate_ids
    ):
        raise RuntimeError("Lesson07 protected source inventory differs")

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    segment_rows = base.extract_segments(main)
    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    if (
        len(unit_rows) != 399
        or len(math_rows) != 148
        or len(asset_rows) != 2
        or len(segment_rows) != 237
        or role_counts != EXPECTED_ROLE_COUNTS
        or [row["source_ref"] for row in asset_rows] != [spec["source_ref"] for spec in ASSETS]
        or segment_rows[0]["segment_id"] != "O006-PSU-008-S0001"
        or segment_rows[-1]["segment_id"] != "O006-PSU-008-S0237"
    ):
        raise RuntimeError("Lesson07 stable-ID inventory differs")

    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None:
        raise RuntimeError("normalized Lesson07 lacks semantic main")
    if [tag.get_text() for tag in target_main.select("code")] != source_code_texts:
        raise RuntimeError("Lesson07 code-node text changed during normalization")
    if [tag.get_text() for tag in target_main.select("style")] != [tag.get_text() for tag in original_main.select("style")]:
        raise RuntimeError("Lesson07 code-label style text changed during normalization")
    if target_main.get_text() != original_main.get_text():
        raise RuntimeError("Lesson07 semantic-main text changed during normalization")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 8,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson07.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson07.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "semantic_text_sha256": base.sha256(semantic_text_payload),
        "formula_count": len(source_formulas),
        "formula_sha256": base.sha256(formula_payload),
        "code_node_count": len(source_code_texts),
        "code_text_sha256": base.sha256(code_payload),
        "style_node_count": len(original_main.select("style")),
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
    manifest_payload = asset_manifest(asset_rows, asset_payloads)
    closure_payload = asset_closure(source_payload, source_soup, original_main, asset_rows, asset_payloads)
    defects = source_defects(original_main)
    script_payload = SCRIPT.read_bytes()

    asset_inventory = []
    output_assets: list[dict[str, object]] = []
    for row, spec in zip(asset_rows, ASSETS, strict=True):
        payload = asset_payloads[str(spec["local_path"])]
        asset_inventory.append(
            {
                "asset_id": row["asset_id"],
                "source_ref": spec["source_ref"],
                "source_url": spec["url"],
                "occurrences": row["occurrences"],
                "alt_texts": row["alt_texts"],
                "bytes": len(payload),
                "sha256": base.sha256(payload),
            }
        )
        output_assets.append({"path": spec["local_path"], "bytes": len(payload), "sha256": base.sha256(payload)})

    receipt = {
        "schema": "o006.stat415.lesson07-normalization.v1",
        "status": "normalized-source-ready-assets-closed-reader-alt-remediation-required",
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
            "style_nodes": len(original_main.select("style")),
        },
        "role_counts": role_counts,
        "code_inventory": {
            "code_nodes": len(source_code_texts),
            "pre_nodes": len(original_main.select("pre")),
            "source_code_blocks": len(original_main.select("pre.sourceCode")),
            "stdout_blocks": len(original_main.select(".cell-output-stdout pre")),
            "image_output_blocks": len(original_main.select(".cell-output-display")),
            "inline_code_nodes": len([tag for tag in original_main.select("code") if tag.find_parent("pre") is None]),
            "style_nodes": len(original_main.select("style")),
            "code_text_sha256": base.sha256(code_payload),
        },
        "asset_inventory": asset_inventory,
        "dependency_inventory": [],
        "asset_closure": {
            "reference_inventory_complete": True,
            "same_origin_png_files": len(ASSETS),
            "same_origin_png_bytes": sum(int(spec["bytes"]) for spec in ASSETS),
            "same_origin_image_bytes_closed": True,
            "external_dependencies": 0,
            "reader_alt_repairs_required": 2,
        },
        "duplicate_native_ids": duplicate_ids,
        "source_limitations": [
            {
                "segment_id": "O006-PSU-008-S0021",
                "classification": "explicit-scope-limitation-not-a-defect",
                "text": segment_rows[20]["source_text"],
                "translation_requirement": "preserve the omission of the full regularity-condition list and proofs without strengthening ANY MLE claims",
            }
        ],
        "source_defects": defects,
        "source_defect_count": len(defects),
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "code_text_sha256": base.sha256(code_payload),
            "formula_nodes_byte_preserved": True,
            "code_nodes_text_preserved": True,
            "style_nodes_text_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {"path": "source/normalized/en-US/Lesson07.html", "bytes": len(normalized_payload), "sha256": base.sha256(normalized_payload)},
            "segments": {"path": "working/lesson07_segments.csv", "bytes": len(csv_payload), "sha256": base.sha256(csv_payload), "rows": len(segment_rows)},
            "catalogue": {"path": "backend/lesson07_source_catalogue.jsonl", "bytes": len(catalogue_payload), "sha256": base.sha256(catalogue_payload), "records": len(catalogue_rows)},
            "assets": output_assets,
            "asset_manifest": {"path": "authority/LESSON07_ASSET_MANIFEST.csv", "bytes": len(manifest_payload), "sha256": base.sha256(manifest_payload)},
            "asset_closure": {"path": "working/lesson07_asset_closure.json", "bytes": len(closure_payload), "sha256": base.sha256(closure_payload)},
            "script": {"path": "scripts/normalize_lesson07.py", "bytes": len(script_payload), "sha256": base.sha256(script_payload)},
            "helper_script": {"path": "scripts/normalize_lesson03.py", "bytes": len(helper_payload), "sha256": base.sha256(helper_payload)},
        },
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": (
            "semantic main only; no authority correction; formula and code text protected; "
            "stable unit, math, asset, and segment IDs additive"
        ),
    }
    outputs = {
        str(spec["local_path"]): asset_payloads[str(spec["local_path"])] for spec in ASSETS
    }
    outputs.update(
        {
            "authority/LESSON07_ASSET_MANIFEST.csv": manifest_payload,
            "source/normalized/en-US/Lesson07.html": normalized_payload,
            "working/lesson07_segments.csv": csv_payload,
            "backend/lesson07_source_catalogue.jsonl": catalogue_payload,
            "working/lesson07_asset_closure.json": closure_payload,
            "build/LESSON07_NORMALIZATION_RECEIPT.json": base.canonical_json(receipt),
        }
    )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.write:
        for spec in ASSETS:
            path = ROOT / str(spec["local_path"])
            if not path.is_file():
                base.atomic_write(path, fetch_asset(spec))
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            base.atomic_write(ROOT / relative, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson07 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson07 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON07_NORMALIZATION_RECEIPT.json"]
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
