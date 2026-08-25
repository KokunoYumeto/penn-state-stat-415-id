#!/usr/bin/env python3
"""Freeze dependencies and write or byte-verify STAT 415 Lesson 08 normalization."""

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
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson08.html"
ASSET_ROOT = ROOT / "authority" / "assets" / "stat415" / "lesson08"
SCRIPT = ROOT / "scripts" / "normalize_lesson08.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-009"
COMPONENT_ID = "Lesson08"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson08"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."

EXPECTED_SOURCE_BYTES = 135_460
EXPECTED_SOURCE_SHA256 = "7d2d365cc7300a2ef54edf82b79fca07899a8e8dcc5fb437237cbaf4501f6953"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
EXPECTED_ASSETS = [
    {
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-1-1.png",
        "bytes": 47_071,
        "sha256": "215b809d8213ef56a36c6bf69f1886f964d39d607532d551779f859052c17c0b",
        "width": 1_344,
        "height": 960,
        "last_modified": "Tue, 15 Jul 2025 11:06:07 GMT",
        "etag": '"b7df-639f5c35285c0"',
        "visual_validation": (
            "Histogram of 25 y values over six unit-width bins from -3 to 3; the two central "
            "bins contain 7 and 8 observations and each outer positive bin contains 2."
        ),
        "recommended_alt": (
            "Histogram of the 25 t-sample observations y, ranging from about -2.3 to 2.6, "
            "with most values between -1 and 1."
        ),
    },
    {
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-8-1.png",
        "bytes": 55_503,
        "sha256": "c41f8223ba0306e6027ea44ec0c293b0b4a9ffdd558d7738e0c911ecc69725b6",
        "width": 1_344,
        "height": 960,
        "last_modified": "Tue, 15 Jul 2025 11:06:07 GMT",
        "etag": '"d8cf-639f5c35285c0"',
        "visual_validation": (
            "Histogram of 1,000 parametric-bootstrap df estimates on a 0 to about 28-million "
            "axis; most occupy the leftmost bin and sparse extreme estimates form a long right tail."
        ),
        "recommended_alt": (
            "Strongly right-skewed histogram of 1,000 parametric-bootstrap estimates of the "
            "t degrees of freedom; most are near the left edge, with sparse values up to about 28 million."
        ),
    },
    {
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-14-1.png",
        "bytes": 59_111,
        "sha256": "51ed4921773d92575cf3cb560d692c49e2022581b479093ad0a870302208798e",
        "width": 1_344,
        "height": 960,
        "last_modified": "Tue, 15 Jul 2025 11:06:07 GMT",
        "etag": '"e6e7-639f5c35285c0"',
        "visual_validation": (
            "Histogram of 1,000 nonparametric-bootstrap df estimates on a 0 to about 28-million "
            "axis; roughly nine hundred occupy the leftmost bin and a few extreme estimates form a long right tail."
        ),
        "recommended_alt": (
            "Strongly right-skewed histogram of 1,000 nonparametric-bootstrap estimates of the "
            "t degrees of freedom; nearly all are near the left edge, with sparse values up to about 28 million."
        ),
    },
    {
        "source_ref": "Lesson08_files/figure-html/unnamed-chunk-18-1.png",
        "bytes": 52_007,
        "sha256": "11820bf246f37f1463f0384ce77672b0ce0d63466c186e6fb8bf25c5b1f522ad",
        "width": 1_344,
        "height": 960,
        "last_modified": "Tue, 15 Jul 2025 11:06:07 GMT",
        "etag": '"cb27-639f5c35285c0"',
        "visual_validation": (
            "Histogram of 40 Pareto observations: 27 fall below 10, 8 from 10 to 20, 4 from "
            "20 to 30, none from 30 to 60, and one value near 66."
        ),
        "recommended_alt": (
            "Strongly right-skewed histogram of 40 Pareto observations from 5.06 to 66.05; "
            "most are below 10 and one isolated observation is near 66."
        ),
    },
]

base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "8 Asymptotic Distribution of MLE (Part II)"
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


def code_with(codes: list[str], *markers: str) -> str | None:
    return next((text for text in codes if all(marker in text for marker in markers)), None)


def source_defects(main: Tag) -> list[dict[str, object]]:
    """Register only high-confidence defects proved at the frozen Lesson08 boundary."""
    formulas = base.formula_texts(main)
    codes = [node.get_text() for node in main.select("code")]
    prose = main.get_text(" ", strip=True)
    defects: list[dict[str, object]] = []

    def add(defect_id: str, kind: str, evidence: object, note: str) -> None:
        defects.append({"defect_id": defect_id, "kind": kind, "evidence": evidence, "note": note})

    missing_hats = [text for text in formulas if text == r"\(\{\theta^{(m)}\}\)"]
    if len(missing_hats) == 3 and prose.count("estimate the parameter") >= 3:
        add(
            "L08-D001",
            "parameter-estimator-estimate-notation-conflated",
            {"unhatted_bootstrap_estimate_sets": len(missing_hats), "repeated_phrase": "estimate the parameter hat-theta"},
            "Estimate theta with the estimator hat-theta; bootstrap realizations are hat-theta^(m), not theta^(m).",
        )

    malformed_percentile = formula_with(formulas, r"\hat{q}_{.975}\left\{\{\hat{\theta}^{(1)}")
    if malformed_percentile:
        add(
            "L08-D002",
            "percentile-interval-extra-opening-brace",
            malformed_percentile,
            "The upper empirical-quantile argument has two opening braces but only one matching set brace.",
        )

    empirical_pmf = formula_with(formulas, r"P(X=x)", r"1/n", r"x=x_i")
    if empirical_pmf:
        add(
            "L08-D003",
            "empirical-pmf-ignores-duplicate-multiplicity",
            empirical_pmf,
            "At a distinct value x, the empirical mass is n^(-1) times the number of observations equal to x, not always 1/n.",
        )

    stale_y_blocks = [
        code for code in codes
        if "out=optim(1,fn=nll.t,y=y,hessian=TRUE)" in code and "x=c(" not in code
    ]
    if len(stale_y_blocks) == 3 and prose.count("re-introduce the data") + prose.count("re-state the model and data") == 2:
        add(
            "L08-D004",
            "restated-t-examples-use-stale-data-object",
            {"all_y_fit_blocks": len(stale_y_blocks), "restated_data_object": "x", "stale_argument": "y=y"},
            "The two restated examples define x but refit with y; they work only because a same-valued y survives from an earlier section.",
        )

    short_buffers = [code for code in codes if "rep(NA,n)" in code and "for(m in 1:M)" in code]
    if len(short_buffers) == 3:
        add(
            "L08-D005",
            "bootstrap-result-vectors-sized-by-n-not-M",
            {"affected_code_blocks": len(short_buffers), "allocation": "rep(NA,n)", "loop": "1:M"},
            "Bootstrap result vectors must have length M. R extends them here only because M exceeds n; if M<n, trailing NA values remain.",
        )

    t_objective = code_with(codes, "nll.t=function(df,y)", "dt(y,df=df")
    pareto_objective = code_with(codes, "nll.pareto=function(theta,x)", "dpareto(x,location=L,shape=a)")
    if t_objective and pareto_objective and "method=\"L-BFGS-B\"" not in prose and "out$convergence" not in prose:
        add(
            "L08-D006",
            "optimizer-domains-and-diagnostics-unguarded",
            {"positive_parameters": ["t df", "Pareto L", "Pareto a"], "warnings_suppressed": prose.count("suppressWarnings")},
            "The shown optim calls enforce neither positive parameter domains nor convergence checks, and bootstrap fits suppress warnings.",
        )

    stochastic_codes = [code for code in codes if "rt(n," in code or "sample(x,size=n,replace=TRUE)" in code]
    if len(stochastic_codes) == 4 and "set.seed" not in prose and "RNGversion" not in prose:
        add(
            "L08-D007",
            "stochastic-code-has-no-reproducibility-state",
            {"stochastic_code_blocks": len(stochastic_codes), "set_seed_calls": 0, "rng_version_calls": 0},
            "No seed/RNG version or package/session identity is supplied, so the bootstrap samples, figures, and quantiles cannot be reproduced from the lesson.",
        )

    numerical_mismatches = [
        {"printed": [2.612500e0, 1.342177e7], "prose": [2.5789, 2.68e7]},
        {"printed": [3.339766e0, 6.710887e6], "prose": [3.2688, 6.8787e6]},
        {"printed": [1.277910, 2.270643], "prose": [1.2912, 2.2905]},
    ]
    if all(str(pair["printed"][0]) in prose or str(pair["prose"][0]) in prose for pair in numerical_mismatches):
        # The exact fixed strings below are the unambiguous HTML-output/prose witness.
        if all(marker in prose for marker in ("2.612500e+00", "2.5789", "3.339766e+00", "3.2688", "1.277910", "1.2912")):
            add(
                "L08-D008",
                "printed-bootstrap-output-and-prose-disagree",
                numerical_mismatches,
                "Three prose intervals differ from the immediately preceding fixed R output; choose a seeded run and make code, output, plots, and prose agree.",
            )

    information_formula = formula_with(formulas, r"I(\theta)", r"-E_x", r"\partial^2")
    hessian_code = code_with(codes, "Get Fisher Information", "I=out$hessian")
    if information_formula and hessian_code and "observed Fisher information" in prose:
        add(
            "L08-D009",
            "expected-and-observed-information-conflated",
            [information_formula, hessian_code, "I(hat-theta) is the observed Fisher information"],
            "The expected information -E ell'' and observed information -ell''(data) are distinct; optim's NLL Hessian estimates the latter.",
        )

    mle_normal = formula_with(formulas, r"\hat{\theta}\sim N", r"I(\hat{\theta}_{ML})")
    if mle_normal and "regularity" not in prose.casefold():
        add(
            "L08-D010",
            "asymptotic-mle-law-stated-as-exact-with-random-variance",
            mle_normal,
            "Under regularity and consistency, state a convergence result (with per-observation or full-sample information defined); use plug-in information only for an approximate standard error.",
        )

    delta_law = formula_with(formulas, r"g(\hat{\theta})\sim N", r"g'(\hat{\theta})")
    if delta_law and "is an invertible function" in prose:
        add(
            "L08-D011",
            "delta-method-condition-and-limit-law-wrong",
            ["g(theta) is an invertible function", delta_law],
            "The first-order delta method needs differentiability at the true parameter, not invertibility; evaluate the limiting derivative at theta_0 and identify plug-in quantities as estimates.",
        )

    if "does not have any restrictions on the function" in prose and "without strict distributional assumptions" in prose:
        add(
            "L08-D012",
            "bootstrap-validity-overclaimed",
            ["does not have any restrictions on g", "robust inference without strict distributional assumptions"],
            "Bootstrap inference remains method-, statistic-, and model-dependent; parametric bootstrap assumes a fitted family and nonparametric bootstrap still needs sampling/regularity conditions.",
        )

    pareto_support = formula_with(formulas, r"x_i \in (L,\infty)")
    if pareto_support and pareto_objective:
        add(
            "L08-D013",
            "pareto-support-endpoint-excluded",
            pareto_support,
            "EnvStats::dpareto assigns positive density at x=L, so the implemented support is [L,infinity), not (L,infinity).",
        )

    if "5.06  5.28" in prose and "The 95% nonparametric bootstrap confidence interval for the location parameter" in prose:
        add(
            "L08-D014",
            "nonparametric-percentile-bootstrap-invalid-for-pareto-endpoint",
            {"sample_minimum": 5.06, "reported_interval": [5.06, 5.28]},
            "Every resample minimum is at least the observed minimum, while a continuous Pareto sample minimum exceeds true L almost surely; this percentile interval therefore cannot provide nominal coverage for L.",
        )

    images = main.select("img[src]")
    captions = main.select("figcaption.quarto-uncaptioned")
    if (
        len(images) == 4
        and len(captions) == 4
        and any("boostrap" in (tag.get("alt") or "") for tag in images)
        and all((tag.get("style") or "") == "width:70.0%" for tag in images)
    ):
        add(
            "L08-D015",
            "figures-lack-complete-text-equivalents",
            {"images": 4, "number_only_captions": 4, "source_alt_texts": [tag.get("alt") for tag in images]},
            "The generic alts omit axes, shape, and inferential meaning; one misspells bootstrap, and every visible caption is only a figure number.",
        )

    internal_notes = [
        text for text in ("The following was in the current notes", "This was in the new list lessons.qmd")
        if text in prose
    ]
    if len(internal_notes) == 2:
        add(
            "L08-D016",
            "internal-authoring-notes-exposed-to-readers",
            internal_notes,
            "Remove the two editorial workflow notes from reader prose while retaining the substantive summary.",
        )

    surface_markers = [
        r"\(m\) data sets",
        "Each of the data set are",
        "this is called",
        "model.c.",
        "opti line",
        "as shown in Section 5",
    ]
    if all(marker in prose for marker in surface_markers):
        add(
            "L08-D017",
            "surface-notation-grammar-and-crossreference-defects",
            surface_markers,
            "Use M consistently, repair agreement/capitalization and the corrupted template lists, and point the transformation recipe to Section 8.1 rather than Section 5.",
        )

    expected_ids = [f"L08-D{ordinal:03d}" for ordinal in range(1, 18)]
    if [row["defect_id"] for row in defects] != expected_ids:
        raise RuntimeError(f"Lesson08 defect census differs: {[row['defect_id'] for row in defects]}")
    return defects


def validate_png(payload: bytes, expected: dict[str, object]) -> dict[str, object]:
    source_ref = str(expected["source_ref"])
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"Lesson08 asset is not PNG: {source_ref}")
    cursor = 8
    chunks: list[dict[str, object]] = []
    width = height = bit_depth = color_type = interlace = None
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise RuntimeError(f"truncated Lesson08 PNG chunk: {source_ref}")
        length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        end = cursor + 12 + length
        if end > len(payload):
            raise RuntimeError(f"Lesson08 PNG chunk extends beyond EOF: {source_ref}")
        chunk_type = payload[cursor + 4:cursor + 8]
        data = payload[cursor + 8:cursor + 8 + length]
        stored_crc = struct.unpack(">I", payload[cursor + 8 + length:end])[0]
        if (zlib.crc32(chunk_type + data) & 0xFFFFFFFF) != stored_crc:
            raise RuntimeError(f"Lesson08 PNG CRC validation failed: {source_ref}")
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
        or width != expected["width"]
        or height != expected["height"]
    ):
        raise RuntimeError(f"Lesson08 PNG structure/dimensions differ: {source_ref}")
    metadata = [row["name"] for row in chunks if row["name"] in {"iCCP", "eXIf", "iTXt", "tEXt", "zTXt"}]
    lowered = payload.lower()
    rights_markers = [
        marker.decode("ascii")
        for marker in (b"copyright", b"creator", b"author", b"license", b"rights")
        if marker in lowered
    ]
    if rights_markers:
        raise RuntimeError(f"Lesson08 PNG has embedded rights/creator markers: {source_ref}")
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
        "chunk_crc_valid": True,
        "chunks": chunks,
        "metadata_chunks": metadata,
        "embedded_rights_or_creator_markers": rights_markers,
        "trailing_bytes": 0,
    }


def asset_local_path(source_ref: str) -> Path:
    return ASSET_ROOT / Path(source_ref)


def fetch_asset(expected: dict[str, object]) -> bytes:
    source_ref = str(expected["source_ref"])
    asset_url = urljoin(SOURCE_URL, source_ref)
    request = urllib.request.Request(
        asset_url,
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
        or final_url != asset_url
        or content_type != "image/png"
        or content_length != str(expected["bytes"])
        or last_modified != expected["last_modified"]
        or etag != expected["etag"]
        or len(payload) != expected["bytes"]
        or base.sha256(payload) != expected["sha256"]
    ):
        raise RuntimeError(f"official Lesson08 asset differs from admitted freeze: {source_ref}")
    validate_png(payload, expected)
    return payload


def load_frozen_assets() -> list[bytes]:
    payloads: list[bytes] = []
    for expected in EXPECTED_ASSETS:
        source_ref = str(expected["source_ref"])
        path = asset_local_path(source_ref)
        if not path.is_file():
            raise RuntimeError(f"frozen Lesson08 asset is missing: {source_ref}")
        payload = path.read_bytes()
        if len(payload) != expected["bytes"] or base.sha256(payload) != expected["sha256"]:
            raise RuntimeError(f"frozen Lesson08 asset differs: {source_ref}")
        validate_png(payload, expected)
        payloads.append(payload)
    return payloads


def asset_manifest(asset_rows: list[dict[str, object]], payloads: list[bytes]) -> bytes:
    stream = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes", "sha256",
        "media_type", "width", "height", "license", "disposition",
    )
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for expected, row, payload in zip(EXPECTED_ASSETS, asset_rows, payloads):
        source_ref = str(expected["source_ref"])
        writer.writerow(
            {
                "asset_id": row["asset_id"],
                "source_reference": source_ref,
                "official_url": urljoin(SOURCE_URL, source_ref),
                "local_path": f"authority/assets/stat415/lesson08/{source_ref}",
                "bytes": len(payload),
                "sha256": base.sha256(payload),
                "media_type": "image/png",
                "width": expected["width"],
                "height": expected["height"],
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
    payloads: list[bytes],
) -> bytes:
    census = base.dependency_census(main)
    expected_census = {
        "images": 4,
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
        raise RuntimeError(f"Lesson08 dependency census differs: {census}")
    refs = list(dict.fromkeys(tag.get("src") for tag in main.select("img[src]")))
    expected_refs = [str(row["source_ref"]) for row in EXPECTED_ASSETS]
    if refs != expected_refs or len(asset_rows) != 4:
        raise RuntimeError("Lesson08 image inventory differs")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson08 page-level CC BY-NC 4.0 witness is missing")
    main_text = main.get_text(" ", strip=True).casefold()
    for marker in ("source:", "credit:", "copyright", "permission", "licensed under"):
        if marker in main_text:
            raise RuntimeError(f"unexpected per-asset rights marker in Lesson08 main: {marker}")

    frozen: list[dict[str, object]] = []
    for expected, row, payload in zip(EXPECTED_ASSETS, asset_rows, payloads):
        source_ref = str(expected["source_ref"])
        asset_url = urljoin(SOURCE_URL, source_ref)
        if urlparse(asset_url).netloc != urlparse(SOURCE_URL).netloc:
            raise RuntimeError(f"Lesson08 asset is not same-origin: {source_ref}")
        tags = main.select(f'img[src="{source_ref}"]')
        if len(tags) != 1:
            raise RuntimeError(f"Lesson08 image occurrence differs: {source_ref}")
        validation = validate_png(payload, expected)
        frozen.append(
            {
                "asset_id": row["asset_id"],
                "source_ref": source_ref,
                "official_url": asset_url,
                "local_path": f"authority/assets/stat415/lesson08/{source_ref}",
                "img_occurrences": 1,
                "lightbox_href_occurrences": len(main.select(f'a[href="{source_ref}"]')),
                "source_alt_text": tags[0].get("alt"),
                "source_inline_style": tags[0].get("style"),
                "bytes": len(payload),
                "sha256": base.sha256(payload),
                "http_audit": {
                    "status": 200,
                    "content_type": "image/png",
                    "content_length": expected["bytes"],
                    "last_modified": expected["last_modified"],
                    "etag": expected["etag"],
                    "redirected": False,
                    "checked_on": "2026-08-25",
                },
                "png_validation": validation,
                "rights": {
                    "applied_license": "CC BY-NC 4.0",
                    "same_origin": True,
                    "per_asset_exception_in_main": False,
                    "embedded_rights_or_creator_markers": False,
                    "clearance": "cleared-for-noncommercial-derivative-freeze-under-official-page-notice",
                },
                "visual_validation": expected["visual_validation"],
                "recommended_alt": expected["recommended_alt"],
                "disposition": "freeze",
            }
        )

    closure = {
        "schema": "o006.stat415.lesson08-asset-closure.v1",
        "status": "same-origin-images-closed-no-external-dependencies-accessibility-repair-required",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson08.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": base.sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": census,
        "counts": {
            "image_occurrences": 4,
            "unique_image_references": 4,
            "frozen_png_files": 4,
            "frozen_png_bytes": sum(len(payload) for payload in payloads),
            "unique_frozen_payloads": len({base.sha256(payload) for payload in payloads}),
            "same_asset_lightbox_hrefs": 0,
            "external_dependencies": 0,
        },
        "rights": {
            "page_license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "witness_text": LICENSE_TEXT,
            "per_image_exception_in_main": False,
        },
        "frozen_images": frozen,
        "accessibility_gate": {
            "generic_or_incomplete_alt_asset_ids": [row["asset_id"] for row in asset_rows],
            "misspelled_alt_asset_ids": [asset_rows[2]["asset_id"]],
            "number_only_figure_captions": 4,
            "fixed_inline_width_percent": 70,
            "reader_repairs_required": 4,
            "code_tabset_requires_non_javascript_fallback": True,
        },
        "closure": {
            "same_origin_image_reference_inventory_complete": True,
            "same_origin_image_bytes_complete": True,
            "same_origin_image_rights_disposition_complete": True,
            "unresolved_same_origin_asset_bytes": 0,
            "external_dependencies": 0,
            "normalization_may_proceed": True,
            "offline_reader_gate": "supply full figure descriptions and keep both code-tab panels available without JavaScript",
        },
    }
    return base.canonical_json(closure)


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson08 normalization helper differs from its frozen implementation")
    source_payload = SOURCE.read_bytes()
    if len(source_payload) != EXPECTED_SOURCE_BYTES or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Lesson08 authority differs from the frozen manifest")
    asset_payloads = load_frozen_assets()

    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson08 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson08 authority lacks main#quarto-document-content")
    if original_main.select("script"):
        raise RuntimeError("unexpected executable script in Lesson08 semantic main")
    if len(original_main.select("style")) != 20:
        raise RuntimeError("Lesson08 embedded code-label style census differs")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson08 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = base.topology_sha256(original_main)
    source_counts = base.content_counts(original_main)
    source_formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(source_formulas).encode("utf-8")
    source_code_texts = [tag.get_text() for tag in original_main.select("code")]
    code_payload = "\n".join(source_code_texts).encode("utf-8")
    source_pre_texts = [tag.get_text() for tag in original_main.select("pre")]
    pre_payload = "\n".join(source_pre_texts).encode("utf-8")
    source_style_texts = [tag.get_text() for tag in original_main.select("style")]
    style_payload = "\n".join(source_style_texts).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(key for key, count in Counter(native_ids).items() if count > 1)

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    segment_rows = base.extract_segments(main)
    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None:
        raise RuntimeError("normalized Lesson08 lacks semantic main")
    if [tag.get_text() for tag in target_main.select("code")] != source_code_texts:
        raise RuntimeError("Lesson08 code-node text changed during normalization")
    if [tag.get_text() for tag in target_main.select("pre")] != source_pre_texts:
        raise RuntimeError("Lesson08 pre-node text changed during normalization")
    if [tag.get_text() for tag in target_main.select("style")] != source_style_texts:
        raise RuntimeError("Lesson08 embedded style text changed during normalization")
    if target_main.get_text() != original_main.get_text():
        raise RuntimeError("Lesson08 semantic-main text changed during normalization")

    expected_counts = {
        "sections": 13,
        "headings": 14,
        "theorem_class_nodes": 1,
        "theorems": 0,
        "definitions": 0,
        "examples": 1,
        "corollaries": 0,
        "solutions": 0,
        "proofs": 0,
        "math_nodes": 156,
        "math_inline": 140,
        "math_display": 16,
        "pre_nodes": 28,
        "code_nodes": 49,
        "figures": 8,
        "images": 4,
        "asset_occurrences": 4,
        "unique_asset_sources": 4,
        "figure_captions": 4,
        "links": 189,
        "tables": 0,
    }
    if source_counts != expected_counts:
        raise RuntimeError(f"Lesson08 semantic census differs: {source_counts}")
    if len(unit_rows) != 604 or len(segment_rows) != 291 or len(asset_rows) != 4:
        raise RuntimeError("Lesson08 unit/segment/asset census differs")
    if duplicate_ids:
        raise RuntimeError(f"Lesson08 unexpectedly has duplicate native IDs: {duplicate_ids}")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 9,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson08.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson08.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "semantic_text_sha256": base.sha256(semantic_text_payload),
        "formula_count": len(source_formulas),
        "formula_sha256": base.sha256(formula_payload),
        "code_node_count": len(source_code_texts),
        "code_text_sha256": base.sha256(code_payload),
        "pre_node_count": len(source_pre_texts),
        "pre_text_sha256": base.sha256(pre_payload),
        "embedded_style_count": len(source_style_texts),
        "embedded_style_text_sha256": base.sha256(style_payload),
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
    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    script_payload = SCRIPT.read_bytes()

    receipt = {
        "schema": "o006.stat415.lesson08-normalization.v1",
        "status": "normalized-source-ready-assets-closed-reader-remediation-required",
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
            "embedded_styles": len(source_style_texts),
        },
        "role_counts": role_counts,
        "asset_inventory": [
            {
                "asset_id": row["asset_id"],
                "source_ref": row["source_ref"],
                "source_url": row["source_url"],
                "occurrences": row["occurrences"],
                "alt_texts": row["alt_texts"],
                "bytes": len(payload),
                "sha256": base.sha256(payload),
            }
            for row, payload in zip(asset_rows, asset_payloads)
        ],
        "asset_closure": {
            "reference_inventory_complete": True,
            "same_origin_png_files": 4,
            "same_origin_png_bytes": sum(len(payload) for payload in asset_payloads),
            "same_origin_image_bytes_closed": True,
            "external_dependencies": 0,
            "reader_repairs_required": 4,
        },
        "duplicate_native_ids": duplicate_ids,
        "source_defects": defects,
        "source_defect_count": len(defects),
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "code_text_sha256": base.sha256(code_payload),
            "pre_text_sha256": base.sha256(pre_payload),
            "embedded_style_text_sha256": base.sha256(style_payload),
            "formula_nodes_byte_preserved": True,
            "code_nodes_text_preserved": True,
            "pre_nodes_text_preserved": True,
            "embedded_style_text_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson08.html",
                "bytes": len(normalized_payload),
                "sha256": base.sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson08_segments.csv",
                "bytes": len(csv_payload),
                "sha256": base.sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson08_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": base.sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "asset_manifest": {
                "path": "authority/LESSON08_ASSET_MANIFEST.csv",
                "bytes": len(manifest_payload),
                "sha256": base.sha256(manifest_payload),
            },
            "asset_closure": {
                "path": "working/lesson08_asset_closure.json",
                "bytes": len(closure_payload),
                "sha256": base.sha256(closure_payload),
            },
            "script": {
                "path": "scripts/normalize_lesson08.py",
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
            "semantic main only; no authority correction; formula/code/pre/style text protected; "
            "stable unit, math, asset, and segment IDs additive"
        ),
    }
    outputs: dict[str, bytes] = {
        "authority/LESSON08_ASSET_MANIFEST.csv": manifest_payload,
        "source/normalized/en-US/Lesson08.html": normalized_payload,
        "working/lesson08_segments.csv": csv_payload,
        "backend/lesson08_source_catalogue.jsonl": catalogue_payload,
        "working/lesson08_asset_closure.json": closure_payload,
        "build/LESSON08_NORMALIZATION_RECEIPT.json": base.canonical_json(receipt),
    }
    for expected, payload in zip(EXPECTED_ASSETS, asset_payloads):
        outputs[f"authority/assets/stat415/lesson08/{expected['source_ref']}"] = payload
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.write:
        for expected in EXPECTED_ASSETS:
            path = asset_local_path(str(expected["source_ref"]))
            if not path.is_file():
                base.atomic_write(path, fetch_asset(expected))
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            base.atomic_write(ROOT / relative, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson08 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson08 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON08_NORMALIZATION_RECEIPT.json"]
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
