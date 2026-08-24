#!/usr/bin/env python3
"""Create or byte-verify the isolated normalized-source lane for STAT 415 Lesson 01."""

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

import bs4
from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson01.html"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson01.html"
SEGMENTS = ROOT / "working" / "lesson01_segments.csv"
CATALOGUE = ROOT / "backend" / "lesson01_source_catalogue.jsonl"
RECEIPT = ROOT / "build" / "LESSON01_NORMALIZATION_RECEIPT.json"
SCRIPT = ROOT / "scripts" / "normalize_lesson01.py"

DOCUMENT_ID = "O006-PSU-002"
COMPONENT_ID = "Lesson01"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson01"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
STRUCTURAL_TAGS = {
    "main", "header", "nav", "section", "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "ol", "ul", "li", "blockquote", "table", "thead", "tbody", "tr", "th", "td",
    "pre", "code", "button", "figure", "figcaption", "img", "a", "div",
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
        "figure_captions": len(main.select("figcaption")),
        "links": len(main.select("a[href]")),
        "tables": len(main.select("table")),
    }


def formula_texts(main: Tag) -> list[str]:
    return [node.get_text() for node in main.select(".math")]


def source_defects(main: Tag) -> list[dict[str, object]]:
    defects: list[dict[str, object]] = []
    native_ids = [tag.get("id") for tag in main.select("[id]")]
    duplicate_ids = {key: count for key, count in Counter(native_ids).items() if count > 1}
    if duplicate_ids.get("fig-stat415sec31812") == 2:
        nodes = main.select("#fig-stat415sec31812")
        defects.append(
            {
                "defect_id": "L01-D001",
                "kind": "duplicate-native-id",
                "evidence": "fig-stat415sec31812 occurs on both the figure wrapper div and its img",
                "node_tags": [node.name for node in nodes],
            }
        )
    formulas = formula_texts(main)
    summary_formula = next((text for text in formulas if "\\left[F(y)]\\right]" in text), None)
    if summary_formula:
        defects.append(
            {
                "defect_id": "L01-D002",
                "kind": "formula-delimiter",
                "evidence": summary_formula,
                "note": "The summary formula has an extra closing bracket after F(y).",
            }
        )
    five_index = "\\(i=1, 2, \\cdots, 5\\)"
    if formulas.count(five_index) == 2:
        defects.append(
            {
                "defect_id": "L01-D003",
                "kind": "index-range",
                "evidence": five_index,
                "occurrences": 2,
                "note": "Both Example 1.2 binomial constructions count six trials but index the event only through 5.",
            }
        )
    proof_index = "\\(\\{X_i\\le y\\},\\;i=1, 2, \\cdots, r\\)"
    if proof_index in formulas:
        defects.append(
            {
                "defect_id": "L01-D004",
                "kind": "index-range",
                "evidence": proof_index,
                "note": "The theorem proof defines Z over n trials, so the indexed event should range over the n observations, not only through r.",
            }
        )
    wrong_alt = main.select_one('img[alt="Celsius vs Fahrenheit scatterplot"]')
    if wrong_alt:
        defects.append(
            {
                "defect_id": "L01-D005",
                "kind": "image-description",
                "evidence": {
                    "src": wrong_alt.get("src"),
                    "alt": wrong_alt.get("alt"),
                },
                "note": "The image occurs in the order-statistics number-line example, not a Celsius/Fahrenheit plot.",
            }
        )
    derivative_formula = next((text for text in formulas if "\\tag{1.1}" in text), None)
    if derivative_formula and "+\\sum_{k=r}^{n-1}[F(y)]^k" in derivative_formula:
        defects.append(
            {
                "defect_id": "L01-D006",
                "kind": "missing-binomial-coefficient",
                "evidence": derivative_formula,
                "note": "The second product-rule sum in Equation 1.1 omits the binomial coefficient {n choose k} carried by every differentiated summand.",
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
    title = source_soup.title.get_text(" ", strip=True) if source_soup.title else "1 Order Statistics"
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
        raise RuntimeError("normalized Lesson01 lacks semantic main")
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
    if content_counts(target_main) != source_counts:
        raise RuntimeError("semantic content counts changed during normalization")


def compute() -> dict[str, bytes]:
    source_payload = SOURCE.read_bytes()
    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson01 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson01 authority lacks main#quarto-document-content")
    if original_main.select("script, style"):
        raise RuntimeError("unexpected embedded script/style in Lesson01 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson01 semantic main")
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
    segment_rows = extract_segments(main)
    normalized_payload = normalized_html(source_soup, main)
    assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 2,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson01.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson01.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "formula_count": len(source_formulas),
        "formula_sha256": sha256(source_formula_payload),
        "unit_count": len(unit_rows),
        "segment_count": len(segment_rows),
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
    catalogue_rows = [document_row, *unit_rows, *math_rows, *catalogue_segment_rows]
    csv_payload = segment_csv(segment_rows)
    catalogue_payload = canonical_jsonl(catalogue_rows)

    script_payload = SCRIPT.read_bytes()
    defects = source_defects(original_main)
    receipt = {
        "schema": "o006.stat415.lesson01-normalization.v1",
        "status": "normalized-source-ready",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
        },
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
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson01.html",
                "bytes": len(normalized_payload),
                "sha256": sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson01_segments.csv",
                "bytes": len(csv_payload),
                "sha256": sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson01_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "script": {
                "path": "scripts/normalize_lesson01.py",
                "bytes": len(script_payload),
                "sha256": sha256(script_payload),
            },
        },
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": "semantic main only; no authority correction; formulas/code protected; stable unit, math, and segment IDs additive",
    }
    return {
        "source/normalized/en-US/Lesson01.html": normalized_payload,
        "working/lesson01_segments.csv": csv_payload,
        "backend/lesson01_source_catalogue.jsonl": catalogue_payload,
        "build/LESSON01_NORMALIZATION_RECEIPT.json": canonical_json(receipt),
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
                raise RuntimeError(f"Lesson01 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson01 normalized output differs: {relative}; "
                    f"actual={sha256(actual)} expected={sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON01_NORMALIZATION_RECEIPT.json"]
    receipt = json.loads(receipt_payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "segments": receipt["counts"]["translation_segments"],
                "units": receipt["counts"]["structural_units"],
                "math": receipt["counts"]["math_nodes"],
                "catalogue_records": receipt["counts"]["catalogue_records"],
                "source_defects": receipt["source_defect_count"],
                "receipt_sha256": sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
