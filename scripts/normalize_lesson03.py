#!/usr/bin/env python3
"""Create or byte-verify the isolated normalized-source lane for STAT 415 Lesson 03."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

import bs4
from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson03.html"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson03.html"
SEGMENTS = ROOT / "working" / "lesson03_segments.csv"
CATALOGUE = ROOT / "backend" / "lesson03_source_catalogue.jsonl"
ZERO_ASSET_CLOSURE = ROOT / "working" / "lesson03_zero_asset_closure.json"
RECEIPT = ROOT / "build" / "LESSON03_NORMALIZATION_RECEIPT.json"
SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-004"
COMPONENT_ID = "Lesson03"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson03"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."
STRUCTURAL_TAGS = {
    "main", "header", "nav", "section", "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "ol", "ul", "li", "blockquote", "table", "thead", "tbody", "tr", "th", "td",
    "pre", "code", "button", "figure", "figcaption", "img", "a", "div",
}
DEPENDENCY_SELECTORS = {
    "images": "img[src]",
    "videos": "video[src]",
    "audio": "audio[src]",
    "media_sources": "source[src]",
    "iframes": "iframe[src]",
    "objects": "object[data]",
    "embeds": "embed[src]",
    "downloads": "a[download]",
    "scripts": "script[src]",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def is_translatable(node: NavigableString) -> bool:
    text = str(node)
    if not text.strip():
        return False
    parent = node.parent
    if parent is None:
        return False
    if parent.name in {"script", "style", "code"} or parent.find_parent(["script", "style", "code"]):
        return False
    if "math" in (parent.get("class") or []) or parent.find_parent(class_="math"):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def section_id(tag: Tag, *, include_self: bool = False) -> str | None:
    section = tag if include_self and tag.name == "section" else tag.find_parent("section")
    return section.get("id") if section else None


def nearest_unit_id(tag: Tag) -> str | None:
    parent = tag.find_parent(attrs={"data-o006-id": True})
    return parent.get("data-o006-id") if parent else None


def direct_heading(tag: Tag) -> Tag | None:
    return tag.find(["h1", "h2", "h3", "h4", "h5", "h6"], recursive=False)


def semantic_role(tag: Tag) -> str:
    classes = set(tag.get("class") or [])
    heading = direct_heading(tag)
    heading_text = heading.get_text(" ", strip=True).casefold() if heading else ""
    own_text = tag.get_text(" ", strip=True).casefold()
    if heading_text == "solution" or (tag.name.startswith("h") and own_text == "solution"):
        return "solution"
    if heading_text == "proof" or (tag.name.startswith("h") and own_text == "proof"):
        return "proof"
    if "example" in classes:
        return "example"
    if "definition" in classes:
        return "definition"
    if "corollary" in classes:
        return "corollary"
    if "theorem" in classes:
        return "theorem"
    if tag.name == "figure":
        return "figure"
    if tag.name == "figcaption":
        return "figure-caption"
    if tag.name == "img":
        return "image"
    if tag.name in {"pre", "code"}:
        return "code"
    if tag.name == "a":
        return "link"
    if tag.name == "section":
        return "section"
    if tag.name.startswith("h"):
        return "heading"
    return "structure"


def topology_rows(main: Tag) -> list[dict[str, object]]:
    """Represent every descendant edge while ignoring only additive data attributes."""
    tags = [main, *main.find_all(True)]
    positions = {id(tag): ordinal for ordinal, tag in enumerate(tags)}
    rows: list[dict[str, object]] = []
    for ordinal, tag in enumerate(tags):
        parent = tag.parent if isinstance(tag.parent, Tag) else None
        rows.append(
            {
                "ordinal": ordinal,
                "parent_ordinal": positions.get(id(parent)),
                "tag": tag.name,
                "native_id": tag.get("id"),
                "classes": tag.get("class") or [],
                "href": tag.get("href"),
                "src": tag.get("src"),
            }
        )
    return rows


def topology_sha256(main: Tag) -> str:
    return sha256(canonical_json(topology_rows(main)))


def asset_sources(main: Tag) -> list[str]:
    """Return first-occurrence-ordered image dependencies from the semantic main."""
    return list(dict.fromkeys(tag.get("src") for tag in main.select("img[src]")))


def dependency_census(main: Tag) -> dict[str, int]:
    return {name: len(main.select(selector)) for name, selector in DEPENDENCY_SELECTORS.items()}


def content_counts(main: Tag) -> dict[str, int]:
    solution_headings = [
        heading for heading in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if heading.get_text(" ", strip=True).casefold() == "solution"
    ]
    proof_headings = [
        heading for heading in main.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        if heading.get_text(" ", strip=True).casefold() == "proof"
    ]
    return {
        "sections": len(main.select("section")),
        "headings": len(main.find_all(re.compile(r"^h[1-6]$"))),
        "theorem_class_nodes": len(main.select(".theorem")),
        "theorems": len(main.select(".theorem:not(.definition):not(.example):not(.corollary)")),
        "definitions": len(main.select(".definition")),
        "examples": len(main.select(".example")),
        "corollaries": len(main.select(".corollary")),
        "solutions": len(solution_headings),
        "proofs": len(proof_headings),
        "math_nodes": len(main.select(".math")),
        "math_inline": len(main.select(".math.inline")),
        "math_display": len(main.select(".math.display")),
        "pre_nodes": len(main.select("pre")),
        "code_nodes": len(main.select("code")),
        "figures": len(main.select("figure")),
        "images": len(main.select("img")),
        "asset_occurrences": len(main.select("img[src]")),
        "unique_asset_sources": len(asset_sources(main)),
        "figure_captions": len(main.select("figcaption")),
        "links": len(main.select("a[href]")),
        "tables": len(main.select("table")),
    }


def formula_texts(main: Tag) -> list[str]:
    return [node.get_text() for node in main.select(".math")]


def source_defects(main: Tag) -> list[dict[str, object]]:
    """Record only errors proved from exact source context and elementary identities."""
    defects: list[dict[str, object]] = []
    formulas = formula_texts(main)

    malformed_normal = r"\(N(\theta_1, \theta_2.\)"
    if malformed_normal in formulas:
        defects.append(
            {
                "defect_id": "L03-D001",
                "kind": "formula-delimiter",
                "evidence": malformed_normal,
                "note": "The normal-distribution call opens N( but omits its closing parenthesis before the period.",
            }
        )

    broken_product = next((text for text in formulas if r"\times ... \times =" in text), None)
    if broken_product:
        defects.append(
            {
                "defect_id": "L03-D002",
                "kind": "normal-density-product-operator",
                "evidence": broken_product,
                "note": "The displayed product inserts an equality sign between the multiplication sign and the final normal-density factor.",
            }
        )

    wrong_sufficient_label = next((text for text in formulas if r"u_1(\sum x_1^2)" in text), None)
    if wrong_sufficient_label:
        defects.append(
            {
                "defect_id": "L03-D003",
                "kind": "summation-index",
                "evidence": wrong_sufficient_label,
                "note": "The sufficient statistic derived immediately above is sum_i x_i^2; its underbrace label instead repeats x_1^2 inside the summation.",
            }
        )

    wrong_normal_kernel = next(
        (
            text for text in formulas
            if r"\underbrace{\color{black}\frac{\theta_1^2}{2\theta_2}-log\sqrt{2\pi\theta_2}" in text
        ),
        None,
    )
    if wrong_normal_kernel:
        defects.append(
            {
                "defect_id": "L03-D004",
                "kind": "normal-density-normalization-sign",
                "evidence": wrong_normal_kernel,
                "note": (
                    "The outer minus applied to theta_1^2/(2 theta_2) - log sqrt(2 pi theta_2) "
                    "makes the log-normalizing term positive. A normal density requires both "
                    "-theta_1^2/(2 theta_2) and -log sqrt(2 pi theta_2)."
                ),
            }
        )

    prose = main.get_text(" ", strip=True)
    if (
        "is not a sufficient statistic for" in prose
        and "because it is not a one-to-one function" in prose
    ):
        defects.append(
            {
                "defect_id": "L03-D005",
                "kind": "insufficient-sufficiency-argument",
                "evidence": "Y = X-bar^2 is declared insufficient solely because it is not one-to-one.",
                "note": (
                    "Non-injectivity alone does not prove insufficiency. Here the conclusion is true, but it "
                    "requires a likelihood-ratio counterexample for samples with means a and -a."
                ),
            }
        )

    malformed_h = next((text for text in formulas if r"h((x_1" in text), None)
    if malformed_h:
        defects.append(
            {
                "defect_id": "L03-D006",
                "kind": "formula-delimiter",
                "evidence": malformed_h,
                "note": "The factor h opens two parentheses but closes only one.",
            }
        )

    malformed_phi_labels = [
        text
        for text in formulas
        if any(
            marker in text
            for marker in (
                r"\phi[u(\Sigma{x_i})_i\lambda)]",
                r"\phi[\mu(\bar{x});\mu)]",
                r"\phi[\mu(\sum x_i);\theta]",
                r"\phi[u(\sum K(x_i);\theta)]",
            )
        )
    ]
    if malformed_phi_labels:
        defects.append(
            {
                "defect_id": "L03-D007",
                "kind": "factor-label-syntax",
                "evidence": malformed_phi_labels,
                "note": (
                    "Four underbrace labels have mismatched delimiters, a stray subscript, or the wrong "
                    "function symbol; each label should expose phi(statistic; parameter)."
                ),
            }
        )

    if (
        "Now, simplifying, by adding up all" in prose
        and r"of the \(\theta\) s and the" in prose
        and r"\(x_i\)" in prose
        and "in the exponents" in prose
    ):
        defects.append(
            {
                "defect_id": "L03-D008",
                "kind": "factor-versus-exponent-explanation",
                "evidence": "adding up all n of the theta factors and the n x_i terms in the exponents",
                "note": (
                    "The n factors theta^-1 multiply to theta^-n; only the exponential arguments sum."
                ),
            }
        )

    ambiguous_log = next((text for text in formulas if r"\text{ln}(1-p)^{1-x}" in text), None)
    if ambiguous_log:
        defects.append(
            {
                "defect_id": "L03-D009",
                "kind": "logarithm-grouping",
                "evidence": ambiguous_log,
                "note": "The exponent must lie inside the logarithm: ln((1-p)^(1-x)).",
            }
        )

    wrong_bernoulli_step = next(
        (text for text in formulas if r"x\text{ln}(1-p)" in text and r"s(x,p)" in text),
        None,
    )
    if wrong_bernoulli_step:
        defects.append(
            {
                "defect_id": "L03-D010",
                "kind": "bernoulli-exponential-equality",
                "evidence": wrong_bernoulli_step,
                "note": (
                    "The displayed exponent simplifies to x ln p rather than the Bernoulli log-pmf; "
                    "retain x ln p + ln(1-p) - x ln(1-p) before combining terms."
                ),
            }
        )

    wrong_poisson_form = next(
        (text for text in formulas if r"\frac{e^{-\lambda}\lambda^x}{x!}" in text and r"\text{ln}(x!)" in text),
        None,
    )
    if wrong_poisson_form:
        defects.append(
            {
                "defect_id": "L03-D011",
                "kind": "poisson-exponential-signs",
                "evidence": wrong_poisson_form,
                "note": "The exponential form requires -ln(x!) and -lambda, not plus signs.",
            }
        )

    wrong_normal_form = next(
        (text for text in formulas if r"\underbrace{\color{black}u" in text and r"p(\mu)" in text),
        None,
    )
    if wrong_normal_form:
        defects.append(
            {
                "defect_id": "L03-D012",
                "kind": "normal-exponential-form",
                "evidence": wrong_normal_form,
                "note": (
                    "The coefficient of x must be mu, not u, and the log-normalizing term must be "
                    "-1/2 log(2 pi), not positive after an outer minus."
                ),
            }
        )

    trailing_product = next(
        (text for text in formulas if r"f(x_n;\theta_1, \theta_2) \times\]" in text),
        None,
    )
    if trailing_product:
        defects.append(
            {
                "defect_id": "L03-D013",
                "kind": "trailing-product-operator",
                "evidence": trailing_product,
                "note": "The joint-density product ends with an unpaired multiplication sign.",
            }
        )

    wrong_log_power = next(
        (text for text in formulas if r"\text{log}\left(\dfrac{1}{\sqrt{2\pi\theta_2}}\right)^n" in text),
        None,
    )
    if wrong_log_power:
        defects.append(
            {
                "defect_id": "L03-D014",
                "kind": "logarithm-power-grouping",
                "evidence": wrong_log_power,
                "note": "(log a)^n is not log(a^n); the exponent should contain n log(a).",
            }
        )

    wrong_variance_symbol = next((text for text in formulas if r"S_2&=" in text), None)
    if wrong_variance_symbol:
        defects.append(
            {
                "defect_id": "L03-D015",
                "kind": "variance-statistic-symbol",
                "evidence": wrong_variance_symbol,
                "note": "The prose and standard definition use S^2; the display instead labels it S_2.",
            }
        )

    unknown_parameter_estimator = next(
        (text for text in formulas if r"\hat{\sigma}^2_{MM}" in text and r"-\mu^2" in text),
        None,
    )
    if unknown_parameter_estimator:
        defects.append(
            {
                "defect_id": "L03-D016",
                "kind": "unknown-parameter-in-estimator",
                "evidence": unknown_parameter_estimator,
                "note": (
                    "An estimator cannot retain the unknown mu; write -mu_hat_MM^2 and then -X-bar^2."
                ),
            }
        )

    gamma_variable_mismatch = next(
        (text for text in formulas if r"f(x_i)" in text and r"x^{\alpha-1}e^{-x/\theta}" in text),
        None,
    )
    if gamma_variable_mismatch:
        defects.append(
            {
                "defect_id": "L03-D017",
                "kind": "gamma-density-variable",
                "evidence": gamma_variable_mismatch,
                "note": "The left side uses x_i while the density and support switch to x; use x_i consistently.",
            }
        )
    return defects


def assign_units(main: Tag) -> list[dict[str, object]]:
    unit_tags = [tag for tag in main.find_all(True) if tag.name in STRUCTURAL_TAGS]
    native_occurrences: Counter[str] = Counter()
    for ordinal, tag in enumerate(unit_tags, start=1):
        tag["data-o006-id"] = f"{DOCUMENT_ID}-U{ordinal:04d}"
    rows: list[dict[str, object]] = []
    for ordinal, tag in enumerate(unit_tags, start=1):
        native_id = tag.get("id")
        occurrence = None
        if native_id:
            native_occurrences[native_id] += 1
            occurrence = native_occurrences[native_id]
        rows.append(
            {
                "schema": CATALOGUE_SCHEMA,
                "record_type": "unit",
                "entity_id": tag["data-o006-id"],
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "ordinal": ordinal,
                "tag": tag.name,
                "role": semantic_role(tag),
                "native_id": native_id,
                "native_id_occurrence": occurrence,
                "classes": tag.get("class") or [],
                "parent_unit_id": nearest_unit_id(tag),
                "section_id": section_id(tag, include_self=True),
                "href": tag.get("href"),
                "src": tag.get("src"),
                "text_sha256": sha256(tag.get_text().encode("utf-8")),
            }
        )
    return rows


def assign_math(main: Tag) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for ordinal, tag in enumerate(main.select(".math"), start=1):
        entity_id = f"{DOCUMENT_ID}-M{ordinal:04d}"
        tag["data-o006-math-id"] = entity_id
        text = tag.get_text()
        classes = tag.get("class") or []
        rows.append(
            {
                "schema": CATALOGUE_SCHEMA,
                "record_type": "math",
                "entity_id": entity_id,
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "ordinal": ordinal,
                "math_kind": "display" if "display" in classes else "inline",
                "parent_unit_id": nearest_unit_id(tag),
                "section_id": section_id(tag),
                "source_text": text,
                "source_sha256": sha256(text.encode("utf-8")),
            }
        )
    return rows


def assign_assets(main: Tag) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    by_source: dict[str, list[Tag]] = {}
    for tag in main.select("img[src]"):
        by_source.setdefault(tag.get("src"), []).append(tag)
    for ordinal, (source_ref, tags) in enumerate(by_source.items(), start=1):
        entity_id = f"{DOCUMENT_ID}-A{ordinal:04d}"
        for tag in tags:
            tag["data-o006-asset-id"] = entity_id
        first = tags[0]
        alt_texts = [tag.get("alt") for tag in tags]
        rows.append(
            {
                "schema": CATALOGUE_SCHEMA,
                "record_type": "asset",
                "entity_id": entity_id,
                "asset_id": entity_id,
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "ordinal": ordinal,
                "source_ref": source_ref,
                "source_url": urljoin(SOURCE_URL, source_ref),
                "occurrences": len(tags),
                "unit_ids": [tag.get("data-o006-id") for tag in tags],
                "parent_unit_ids": [nearest_unit_id(tag) for tag in tags],
                "section_ids": [section_id(tag) for tag in tags],
                "alt_texts": alt_texts,
                "alt_texts_sha256": sha256(canonical_json(alt_texts)),
                "first_parent_unit_id": nearest_unit_id(first),
            }
        )
    return rows


def extract_segments(main: Tag) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for node in main.find_all(string=True):
        if not isinstance(node, NavigableString) or not is_translatable(node):
            continue
        ordinal = len(rows) + 1
        segment_id = f"{DOCUMENT_ID}-S{ordinal:04d}"
        text = str(node)
        parent = node.parent
        rows.append(
            {
                "segment_id": segment_id,
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "section_id": section_id(parent) if parent else None,
                "source_sha256": sha256(text.encode("utf-8")),
                "source_text": text,
                "ordinal": ordinal,
                "parent_tag": parent.name if parent else None,
                "parent_unit_id": (
                    parent.get("data-o006-id") or nearest_unit_id(parent)
                    if parent else None
                ),
            }
        )
    return rows


def segment_csv(rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    fields = (
        "segment_id", "document_id", "component_id", "section_id", "source_sha256",
        "source_text", "target_text", "status",
    )
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "segment_id": row["segment_id"],
                "document_id": row["document_id"],
                "component_id": row["component_id"],
                "section_id": row["section_id"] or "",
                "source_sha256": row["source_sha256"],
                "source_text": row["source_text"],
                "target_text": "",
                "status": "pending",
            }
        )
    return stream.getvalue().encode("utf-8")


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = source_soup.title.get_text(" ", strip=True) if source_soup.title else "3 Estimation (Part II)"
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


def assert_preservation(
    source_main: Tag,
    normalized_payload: bytes,
    source_topology_sha: str,
    source_counts: dict[str, int],
) -> None:
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None:
        raise RuntimeError("normalized Lesson03 lacks semantic main")
    if topology_sha256(target_main) != source_topology_sha:
        raise RuntimeError("main-content topology changed during normalization")
    if formula_texts(target_main) != formula_texts(source_main):
        raise RuntimeError("formula nodes changed during normalization")
    source_native_ids = [tag.get("id") for tag in source_main.select("[id]")]
    target_native_ids = [tag.get("id") for tag in target_main.select("[id]")]
    if target_native_ids != source_native_ids:
        raise RuntimeError("native anchors changed during normalization")
    if [tag.get("href") for tag in target_main.select("a[href]")] != [
        tag.get("href") for tag in source_main.select("a[href]")
    ]:
        raise RuntimeError("link topology changed during normalization")
    if [tag.get("src") for tag in target_main.select("img[src]")] != [
        tag.get("src") for tag in source_main.select("img[src]")
    ]:
        raise RuntimeError("image topology changed during normalization")
    if dependency_census(target_main) != dependency_census(source_main):
        raise RuntimeError("dependency census changed during normalization")
    if content_counts(target_main) != source_counts:
        raise RuntimeError("semantic content counts changed during normalization")


def zero_asset_closure(source_payload: bytes, source_soup: BeautifulSoup, main: Tag) -> bytes:
    census = dependency_census(main)
    if any(census.values()):
        raise RuntimeError(f"Lesson03 semantic main is not zero-asset: {census}")
    page_text = source_soup.get_text(" ", strip=True)
    if LICENSE_TEXT not in page_text:
        raise RuntimeError("Lesson03 page-level CC BY-NC 4.0 witness is missing")
    links = [
        {"href": tag.get("href"), "text": tag.get_text(" ", strip=True)}
        for tag in main.select("a[href]")
    ]
    closure = {
        "schema": "o006.stat415.lesson03-zero-asset-closure.v1",
        "status": "verified-zero-main-content-assets",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson03.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": census,
        "main_links": links,
        "main_link_classification": {
            "navigation": 2,
            "internal_anchor_occurrences": 2,
            "download_or_asset_links": 0,
        },
        "rights": {
            "page_license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "witness_text": LICENSE_TEXT,
            "per_asset_rights_review_required": False,
            "blocking_unresolved_asset_rights": 0,
        },
        "excluded_site_chrome": [
            "head and sidebar institutional images",
            "footer license badge",
            "Quarto/Bootstrap/MathJax site libraries",
            "analytics and consent tooling",
        ],
        "conclusion": (
            "Lesson03 has no instructional media, data, download, embed, object, or non-library "
            "runtime dependency inside its semantic main; no asset bytes need freezing."
        ),
    }
    return canonical_json(closure)


def compute() -> dict[str, bytes]:
    source_payload = SOURCE.read_bytes()
    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson03 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson03 authority lacks main#quarto-document-content")
    if original_main.select("script, style"):
        raise RuntimeError("unexpected embedded script/style in Lesson03 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson03 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = topology_sha256(original_main)
    source_counts = content_counts(original_main)
    source_formulas = formula_texts(original_main)
    source_formula_payload = "\n".join(source_formulas).encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(key for key, count in Counter(native_ids).items() if count > 1)

    unit_rows = assign_units(main)
    math_rows = assign_math(main)
    asset_rows = assign_assets(main)
    segment_rows = extract_segments(main)
    normalized_payload = normalized_html(source_soup, main)
    assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)

    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 4,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson03.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson03.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "formula_count": len(source_formulas),
        "formula_sha256": sha256(source_formula_payload),
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
    csv_payload = segment_csv(segment_rows)
    catalogue_payload = canonical_jsonl(catalogue_rows)
    zero_asset_payload = zero_asset_closure(source_payload, source_soup, original_main)

    script_payload = SCRIPT.read_bytes()
    defects = source_defects(original_main)
    receipt = {
        "schema": "o006.stat415.lesson03-normalization.v1",
        "status": "normalized-source-ready",
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
        "asset_inventory": [],
        "duplicate_native_ids": duplicate_ids,
        "source_defects": defects,
        "source_defect_count": len(defects),
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "formula_sha256": sha256(source_formula_payload),
            "formula_nodes_byte_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson03.html",
                "bytes": len(normalized_payload),
                "sha256": sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson03_segments.csv",
                "bytes": len(csv_payload),
                "sha256": sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson03_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "zero_asset_closure": {
                "path": "working/lesson03_zero_asset_closure.json",
                "bytes": len(zero_asset_payload),
                "sha256": sha256(zero_asset_payload),
            },
            "script": {
                "path": "scripts/normalize_lesson03.py",
                "bytes": len(script_payload),
                "sha256": sha256(script_payload),
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
        "source/normalized/en-US/Lesson03.html": normalized_payload,
        "working/lesson03_segments.csv": csv_payload,
        "backend/lesson03_source_catalogue.jsonl": catalogue_payload,
        "working/lesson03_zero_asset_closure.json": zero_asset_payload,
        "build/LESSON03_NORMALIZATION_RECEIPT.json": canonical_json(receipt),
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
            atomic_write(ROOT / relative, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson03 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson03 normalized output differs: {relative}; "
                    f"actual={sha256(actual)} expected={sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON03_NORMALIZATION_RECEIPT.json"]
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
                "receipt_sha256": sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
