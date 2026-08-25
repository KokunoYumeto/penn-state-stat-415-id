#!/usr/bin/env python3
"""Create or byte-verify the isolated normalized-source lane for STAT 415 Lesson 04."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bs4
from bs4 import BeautifulSoup, Tag

import normalize_lesson03 as base


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson04.html"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson04.html"
SEGMENTS = ROOT / "working" / "lesson04_segments.csv"
CATALOGUE = ROOT / "backend" / "lesson04_source_catalogue.jsonl"
ASSET_INVENTORY = ROOT / "working" / "lesson04_asset_inventory.json"
RECEIPT = ROOT / "build" / "LESSON04_NORMALIZATION_RECEIPT.json"
SCRIPT = ROOT / "scripts" / "normalize_lesson04.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-005"
COMPONENT_ID = "Lesson04"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson04"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."
EXPECTED_SOURCE_BYTES = 106_614
EXPECTED_SOURCE_SHA256 = "9fe5790e577c6ce0b808c92683aea45442187f80f74d540b20bd4514bdefc060"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"

# Reuse the already established, deterministic structural primitives.  They
# read these module globals at call time, so set the Lesson 04 identity before
# invoking any of them.
base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "4 Maximum Likelihood Estimation (MLE) (Part I)"
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
    """Return only exact, mechanically demonstrable defects in the frozen source."""
    formulas = base.formula_texts(main)
    prose = main.get_text(" ", strip=True)
    defects: list[dict[str, object]] = []

    wrong_case = formula_with(formulas, r"\frac{d}{dp}L(P)")
    if wrong_case:
        defects.append(
            {
                "defect_id": "L04-D001",
                "kind": "parameter-case-mismatch",
                "evidence": wrong_case,
                "note": "The likelihood is L(p), but its derivative is labeled dL(P)/dp with an uppercase P.",
            }
        )

    missing_condition_bar = formula_with(formulas, r"\sum_{i=1}^n \ln f(x_i\theta)")
    if missing_condition_bar:
        defects.append(
            {
                "defect_id": "L04-D002",
                "kind": "conditional-density-delimiter",
                "evidence": missing_condition_bar,
                "note": "The final log-likelihood summand drops the conditioning bar: f(x_i theta) should be f(x_i|theta).",
            }
        )

    wrong_gamma_likelihood_label = formula_with(
        formulas,
        r"L(p)=\prod_{i=1}^n",
        r"\Gamma(\alpha)\theta^\alpha",
    )
    if wrong_gamma_likelihood_label:
        defects.append(
            {
                "defect_id": "L04-D003",
                "kind": "likelihood-parameter-mismatch",
                "evidence": wrong_gamma_likelihood_label,
                "note": "This Gamma model varies theta, so the likelihood must be L(theta), not L(p).",
            }
        )

    nested_log = formula_with(formulas, r"(\alpha-1)\ln \left(\ln \prod x_i\right)")
    if nested_log:
        defects.append(
            {
                "defect_id": "L04-D004",
                "kind": "gamma-loglikelihood-extra-logarithm",
                "evidence": nested_log,
                "note": (
                    "Taking logs of (product x_i)^(alpha-1) gives "
                    "(alpha-1) ln(product x_i), not (alpha-1) ln(ln(product x_i))."
                ),
            }
        )

    if (
        "observations from a Geometric distribution" in prose
        and "Find the maximum likelihood estimate of \\(\\theta\\)" in prose
        and r"\hat{p}=\frac{n}{\sum x_i}" in prose
    ):
        defects.append(
            {
                "defect_id": "L04-D005",
                "kind": "geometric-parameter-name",
                "evidence": "Example 4.6 asks for an estimate of theta but immediately applies the Geometric MLE for p.",
                "note": "The requested parameter should be p, consistently with the stated model and solution.",
            }
        )

    unfinished_gamma_estimate = formula_with(
        formulas,
        r"\frac{3.4+8.1+5.5}{3(3)}=",
    )
    if unfinished_gamma_estimate and unfinished_gamma_estimate.rstrip().endswith("=\n\\end{align*}\\]"):
        defects.append(
            {
                "defect_id": "L04-D006",
                "kind": "unfinished-numerical-estimate",
                "evidence": unfinished_gamma_estimate,
                "note": "The worked estimate ends after an equals sign; the exact value is 17/9.",
            }
        )

    wrong_poisson_sign = formula_with(
        formulas,
        r"\ell(\lambda)=-n\lambda",
        r"+\ln \left(\prod x_i!\right)",
    )
    if wrong_poisson_sign:
        defects.append(
            {
                "defect_id": "L04-D007",
                "kind": "poisson-loglikelihood-sign",
                "evidence": wrong_poisson_sign,
                "note": "The factorial product is in the likelihood denominator, so its logarithm carries a minus sign.",
            }
        )

    uniform_derivative = formula_with(formulas, r"\frac{d}{da}\ell(a)=-\frac{n}{a}")
    if (
        uniform_derivative
        and "the likelihood function is monotonic increasing" in prose
        and r"\hat{a}=\infty" in prose
    ):
        defects.append(
            {
                "defect_id": "L04-D008",
                "kind": "uniform-monotonicity-and-critical-point",
                "evidence": {
                    "derivative": uniform_derivative,
                    "source_claims": [
                        "setting -n/a=0 gives a-hat=infinity",
                        "the likelihood a^(-n) is monotonic increasing",
                    ],
                },
                "note": (
                    "For a>0, d[-n ln a]/da=-n/a is strictly negative and never zero: "
                    "a^(-n) is decreasing, and solving the score equation does not yield infinity."
                ),
            }
        )

    missing_zero = formula_with(formulas, r"\text{ if $y=$ or $y=1$}")
    if missing_zero:
        defects.append(
            {
                "defect_id": "L04-D009",
                "kind": "bernoulli-support-value-omission",
                "evidence": missing_zero,
                "note": "The first support value is missing; the indicator case must read y=0 or y=1.",
            }
        )

    wrong_bernoulli_product = formula_with(
        formulas,
        r"\prod_{i=1}^n p^{y_1}(1-p)^{1-y_1}",
    )
    if wrong_bernoulli_product:
        defects.append(
            {
                "defect_id": "L04-D010",
                "kind": "bernoulli-product-index",
                "evidence": wrong_bernoulli_product,
                "note": "Each product factor must use y_i; repeating y_1 cannot produce the displayed sums over y_i.",
            }
        )

    wrong_bernoulli_score = formula_with(formulas, r"\frac{d}{dp}=\frac{\sum y_1}{p}")
    wrong_bernoulli_equation = formula_with(formulas, r"\frac{\sum y_1}{p}=", r"\sum y_i=np")
    if wrong_bernoulli_score and wrong_bernoulli_equation:
        defects.append(
            {
                "defect_id": "L04-D011",
                "kind": "bernoulli-score-label-and-index",
                "evidence": [wrong_bernoulli_score, wrong_bernoulli_equation],
                "note": (
                    "The score's left side omits ell(p), and both displayed numerators use sum y_1 "
                    "where the subsequent algebra requires sum y_i."
                ),
            }
        )

    wrong_uniform_product = formula_with(
        formulas,
        r"L(a)=\prod_{i=1}^n",
        r"\mathbf{1}_{x\in (0, a)}",
    )
    if wrong_uniform_product:
        defects.append(
            {
                "defect_id": "L04-D012",
                "kind": "uniform-product-index",
                "evidence": wrong_uniform_product,
                "note": "The indicator inside the product must depend on x_i, not an unindexed x.",
            }
        )

    open_uniform_support = formula_with(formulas, r"\mathbf{1}_{x\in (0, a)}")
    uniform_endpoint_estimator = formula_with(formulas, r"\hat{a}=\max(X_i)=Y_n")
    if open_uniform_support and uniform_endpoint_estimator:
        defects.append(
            {
                "defect_id": "L04-D013",
                "kind": "uniform-support-endpoint-inconsistency",
                "evidence": [open_uniform_support, uniform_endpoint_estimator],
                "note": (
                    "With the source's strict support x in (0,a), setting a=max(x_i) makes the "
                    "largest observation fall on an excluded endpoint. The support must include the "
                    "right endpoint or the result must be described as a supremum rather than an attained MLE."
                ),
            }
        )

    pareto_density = formula_with(formulas, r"x\ge m")
    pareto_likelihood = formula_with(formulas, r"\mathbf{1}_{\{x_i>m\}}")
    if pareto_density and pareto_likelihood:
        defects.append(
            {
                "defect_id": "L04-D014",
                "kind": "pareto-support-inequality",
                "evidence": [pareto_density, pareto_likelihood],
                "note": (
                    "The density states x>=m, but the likelihood switches to x_i>m. The strict "
                    "indicator would be zero at the claimed estimate m=min(x_i)."
                ),
            }
        )

    malformed_vector_subscript = formula_with(formulas, r"\hat{\theta_p}")
    if malformed_vector_subscript:
        defects.append(
            {
                "defect_id": "L04-D015",
                "kind": "vector-component-subscript",
                "evidence": malformed_vector_subscript,
                "note": "The final component should be written hat(theta)_p, not a hat over the subscripted expression theta_p.",
            }
        )

    laplace_sign = formula_with(
        formulas,
        r"\prod_{i=1}^n \frac{1}{2b}e^{\frac{|x_i-\mu|}{b}}",
        r"e^{-\frac{\sum |x_i-\mu|}{b}}",
    )
    if laplace_sign:
        defects.append(
            {
                "defect_id": "L04-D016",
                "kind": "laplace-likelihood-exponent-sign",
                "evidence": laplace_sign,
                "note": "The first product drops the negative sign from the stated Laplace density, contradicting the final equality.",
            }
        )

    laplace_piecewise = formula_with(
        formulas,
        r"\frac{d}{d\mu}|x_i-\mu|=\begin{cases}",
        r"x_i\ge \mu",
        r"x_i\le \mu",
    )
    if laplace_piecewise:
        defects.append(
            {
                "defect_id": "L04-D017",
                "kind": "absolute-value-derivative-at-kink",
                "evidence": laplace_piecewise,
                "note": (
                    "At x_i=mu both stated cases apply but assign -1 and +1; the derivative is "
                    "undefined there and the median argument requires a subgradient/set-valued treatment."
                ),
            }
        )

    malformed_laplace_estimator = formula_with(
        formulas,
        r"\hat{\theta}=(\hat{\mu}=",
        r"|x_i-\text{median}",
    )
    if malformed_laplace_estimator and "x_n))" in malformed_laplace_estimator:
        defects.append(
            {
                "defect_id": "L04-D018",
                "kind": "laplace-estimator-delimiter",
                "evidence": malformed_laplace_estimator,
                "note": "The final absolute-value expression lacks its closing vertical bar and has mismatched closing parentheses.",
            }
        )

    if (
        "Gamma distribution with parameters \\(\\alpha\\) and \\(\\beta\\)" in prose
        and r"\underline{\theta}=(\alpha, \beta)" in prose
        and formula_with(formulas, r"\Gamma(\alpha)\theta^\alpha")
    ):
        defects.append(
            {
                "defect_id": "L04-D019",
                "kind": "gamma-scale-parameter-name",
                "evidence": "Example 4.16 defines (alpha,beta) but every likelihood and score formula uses theta as the scale parameter.",
                "note": "The scale parameter must be named consistently throughout the example.",
            }
        )

    malformed_gamma_score = formula_with(formulas, r"\frac{\ell(\underline{\theta})}{d\theta}")
    if malformed_gamma_score:
        defects.append(
            {
                "defect_id": "L04-D020",
                "kind": "gamma-score-derivative-numerator",
                "evidence": malformed_gamma_score,
                "note": "The theta score's left side is missing the differential d in its numerator.",
            }
        )

    gamma_alpha_score = formula_with(
        formulas,
        r"\frac{d\ell(\underline{\theta})}{d\alpha}",
        r"+\sum \ln x_i",
    )
    if gamma_alpha_score and r"-n\ln \theta" not in gamma_alpha_score:
        defects.append(
            {
                "defect_id": "L04-D021",
                "kind": "gamma-alpha-score-omitted-term",
                "evidence": gamma_alpha_score,
                "note": "Differentiating -n alpha ln(theta) with respect to alpha contributes -n ln(theta), which is omitted.",
            }
        )

    return defects


def asset_inventory(
    source_payload: bytes,
    source_soup: BeautifulSoup,
    main: Tag,
    asset_rows: list[dict[str, object]],
) -> bytes:
    census = base.dependency_census(main)
    if census != {
        "images": 1,
        "videos": 0,
        "audio": 0,
        "media_sources": 0,
        "iframes": 0,
        "objects": 0,
        "embeds": 0,
        "downloads": 0,
        "scripts": 0,
    }:
        raise RuntimeError(f"unexpected Lesson04 semantic-main dependency census: {census}")
    if len(asset_rows) != 1:
        raise RuntimeError("Lesson04 must expose exactly one unique image asset")
    row = asset_rows[0]
    if row["source_ref"] != "assets/STAT-415-SEC-1-15.svg":
        raise RuntimeError("Lesson04 image reference changed")
    image = main.select_one('img[src="assets/STAT-415-SEC-1-15.svg"]')
    if image is None or image.get("alt") != "Natural logarithm graph":
        raise RuntimeError("Lesson04 logarithm-graph image/alt witness changed")
    lightbox = main.select_one('a.lightbox[href="assets/STAT-415-SEC-1-15.svg"]')
    if lightbox is None or image not in lightbox.descendants:
        raise RuntimeError("Lesson04 same-asset lightbox reference changed")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson04 page-level CC BY-NC 4.0 witness is missing")
    official_url = urljoin(SOURCE_URL, str(row["source_ref"]))
    if urlparse(official_url).netloc != urlparse(SOURCE_URL).netloc:
        raise RuntimeError("Lesson04 instructional asset is not same-origin")
    payload = {
        "schema": "o006.stat415.lesson04-asset-inventory.v1",
        "status": "reference-inventory-complete-asset-bytes-not-frozen-by-normalization",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson04.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": base.sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": census,
        "assets": [
            {
                "asset_id": row["asset_id"],
                "source_ref": row["source_ref"],
                "official_url": official_url,
                "same_origin": True,
                "img_occurrences": row["occurrences"],
                "lightbox_href_occurrences": 1,
                "alt_texts": row["alt_texts"],
                "roles": ["instructional-image", "same-asset-lightbox-target"],
                "local_bytes_frozen": False,
                "integrity_sha256": None,
                "disposition": "requires-separate-authority-asset-freeze-before-offline-reader-build",
            }
        ],
        "rights": {
            "page_license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "witness_text": LICENSE_TEXT,
            "per_asset_exception_in_lesson_main": False,
            "rights_disposition": "same-origin page-covered candidate; verify bytes and embedded/per-asset metadata at freeze",
        },
        "closure": {
            "reference_inventory_complete": True,
            "unresolved_references": 0,
            "asset_freezes_required": 1,
            "blocking_missing_asset_bytes": 1,
            "normalization_may_proceed": True,
            "offline_reader_build_may_not_claim_asset_closure": True,
        },
    }
    return base.canonical_json(payload)


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson04 normalization helper differs from its frozen implementation")
    source_payload = SOURCE.read_bytes()
    if len(source_payload) != EXPECTED_SOURCE_BYTES or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Lesson04 authority differs from the frozen 14-document manifest")
    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson04 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson04 authority lacks main#quarto-document-content")
    if original_main.select("script, style"):
        raise RuntimeError("unexpected embedded script/style in Lesson04 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson04 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = base.topology_sha256(original_main)
    source_counts = base.content_counts(original_main)
    source_formulas = base.formula_texts(original_main)
    source_formula_payload = "\n".join(source_formulas).encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(key for key, count in Counter(native_ids).items() if count > 1)

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    segment_rows = base.extract_segments(main)
    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)

    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 5,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson04.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson04.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "formula_count": len(source_formulas),
        "formula_sha256": base.sha256(source_formula_payload),
        "unit_count": len(unit_rows),
        "segment_count": len(segment_rows),
        "asset_count": len(asset_rows),
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
    asset_payload = asset_inventory(source_payload, source_soup, original_main, asset_rows)
    defects = source_defects(original_main)

    script_payload = SCRIPT.read_bytes()
    receipt = {
        "schema": "o006.stat415.lesson04-normalization.v1",
        "status": "normalized-source-ready-asset-freeze-required-before-reader-build",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "assets": len(asset_rows),
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
        },
        "role_counts": role_counts,
        "asset_inventory": [
            {
                "asset_id": row["asset_id"],
                "source_ref": row["source_ref"],
                "source_url": row["source_url"],
                "occurrences": row["occurrences"],
                "alt_texts": row["alt_texts"],
            }
            for row in asset_rows
        ],
        "asset_closure": {
            "reference_inventory_complete": True,
            "asset_freezes_required": 1,
            "offline_reader_build_blocked_until_asset_freeze": True,
        },
        "duplicate_native_ids": duplicate_ids,
        "source_defects": defects,
        "source_defect_count": len(defects),
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "formula_sha256": base.sha256(source_formula_payload),
            "formula_nodes_byte_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson04.html",
                "bytes": len(normalized_payload),
                "sha256": base.sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson04_segments.csv",
                "bytes": len(csv_payload),
                "sha256": base.sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson04_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": base.sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "asset_inventory": {
                "path": "working/lesson04_asset_inventory.json",
                "bytes": len(asset_payload),
                "sha256": base.sha256(asset_payload),
            },
            "script": {
                "path": "scripts/normalize_lesson04.py",
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
            "semantic main only; no authority correction; formulas/code protected; stable unit, "
            "math, asset, and segment IDs additive"
        ),
    }
    return {
        "source/normalized/en-US/Lesson04.html": normalized_payload,
        "working/lesson04_segments.csv": csv_payload,
        "backend/lesson04_source_catalogue.jsonl": catalogue_payload,
        "working/lesson04_asset_inventory.json": asset_payload,
        "build/LESSON04_NORMALIZATION_RECEIPT.json": base.canonical_json(receipt),
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
                raise RuntimeError(f"Lesson04 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson04 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON04_NORMALIZATION_RECEIPT.json"]
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
                "source_defects": receipt["source_defect_count"],
                "receipt_sha256": base.sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
