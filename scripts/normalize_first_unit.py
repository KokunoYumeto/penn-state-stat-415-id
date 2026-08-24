#!/usr/bin/env python3
"""Create or verify normalized landing/Lesson00 source and stable-ID catalogs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from copy import deepcopy
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "authority" / "upstream" / "stat415"
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
SEGMENTS = ROOT / "backend" / "first_unit_segments.jsonl"
STRUCTURES = ROOT / "backend" / "first_unit_structures.jsonl"
TRANSLATION_TEMPLATE = ROOT / "source" / "id-ID" / "first_unit_translation.csv"
RECEIPT = ROOT / "build" / "FIRST_UNIT_NORMALIZATION_RECEIPT.json"
DOCUMENTS = (
    (0, "index", "index.html", "https://online.stat.psu.edu/stat415/"),
    (1, "Lesson00", "Lesson00.html", "https://online.stat.psu.edu/stat415/Lesson00"),
)
STRUCTURAL_TAGS = {
    "main", "header", "nav", "section", "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "ol", "ul", "li", "blockquote", "table", "thead", "tbody", "tr", "th", "td",
    "pre", "code", "button", "figure", "figcaption", "img", "a", "div",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in rows
    )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def is_translatable(node: NavigableString) -> bool:
    text = str(node)
    if not text.strip():
        return False
    parent = node.parent
    if parent is None or parent.find_parent(["script", "style", "code"]) is not None or parent.name in {"script", "style", "code"}:
        return False
    if parent.find_parent(class_="math") is not None or "math" in (parent.get("class") or []):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def section_context(node: NavigableString) -> str | None:
    section = node.parent.find_parent("section") if node.parent else None
    return section.get("id") if section else None


def normalized_document(ordinal: int, component: str, filename: str, url: str) -> tuple[bytes, list[dict[str, object]], list[dict[str, object]]]:
    source_path = UPSTREAM / filename
    payload = source_path.read_bytes()
    soup = BeautifulSoup(payload, "html.parser")
    original_main = soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError(f"missing semantic main: {filename}")
    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError(f"failed to normalize main: {filename}")
    for unwanted in main.select("script, style"):
        unwanted.decompose()
    if main.find("h1") is None:
        source_title = soup.select_one("h1.title")
        heading = fragment.new_tag("h1")
        heading["class"] = ["title"]
        heading.string = source_title.get_text(" ", strip=True) if source_title else soup.title.get_text(" ", strip=True)
        main.insert(0, heading)
    main["data-source-url"] = url
    main["data-component-id"] = component

    structure_rows: list[dict[str, object]] = []
    unit = 0
    for tag in main.find_all(True):
        if tag.name not in STRUCTURAL_TAGS:
            continue
        unit += 1
        stable_id = f"O006-PSU-{ordinal:03d}-U{unit:04d}"
        tag["data-o006-id"] = stable_id
        classes = tag.get("class") or []
        structure_rows.append(
            {
                "entity_id": stable_id,
                "document_id": f"O006-PSU-{ordinal:03d}",
                "component_id": component,
                "ordinal": unit,
                "tag": tag.name,
                "native_id": tag.get("id"),
                "classes": classes,
                "href": tag.get("href"),
                "src": tag.get("src"),
            }
        )

    segment_rows: list[dict[str, object]] = []
    segment = 0
    for node in main.find_all(string=True):
        if not isinstance(node, NavigableString) or not is_translatable(node):
            continue
        segment += 1
        text = str(node)
        segment_id = f"O006-PSU-{ordinal:03d}-S{segment:04d}"
        parent = node.parent
        segment_rows.append(
            {
                "segment_id": segment_id,
                "document_id": f"O006-PSU-{ordinal:03d}",
                "component_id": component,
                "ordinal": segment,
                "source_text": text,
                "source_sha256": sha256(text.encode("utf-8")),
                "parent_tag": parent.name if parent else None,
                "parent_unit_id": parent.get("data-o006-id") if parent else None,
                "section_id": section_context(node),
                "locale": "en-US",
                "translation_status": "pending",
            }
        )

    title = soup.title.get_text(" ", strip=True) if soup.title else component
    body = str(main)
    normalized = (
        "<!doctype html>\n"
        '<html lang="en-US">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{url}">\n'
        '<meta name="translation-provenance" content="OpenAI Codex gpt-5.6-sol, Ultra">\n'
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>\n"
    ).encode("utf-8")
    return normalized, segment_rows, structure_rows


def translation_template(segment_rows: list[dict[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    fields = (
        "segment_id", "document_id", "component_id", "section_id", "source_sha256",
        "source_text", "target_text", "status",
    )
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in segment_rows:
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
    return output.getvalue().encode("utf-8")


def compute() -> dict[str, bytes]:
    outputs: dict[str, bytes] = {}
    all_segments: list[dict[str, object]] = []
    all_structures: list[dict[str, object]] = []
    documents: list[dict[str, object]] = []
    for ordinal, component, filename, url in DOCUMENTS:
        normalized, segments, structures = normalized_document(ordinal, component, filename, url)
        relative = f"source/normalized/en-US/{filename}"
        outputs[relative] = normalized
        all_segments.extend(segments)
        all_structures.extend(structures)
        documents.append(
            {
                "ordinal": ordinal,
                "component_id": component,
                "source_path": f"authority/upstream/stat415/{filename}",
                "source_bytes": (UPSTREAM / filename).stat().st_size,
                "source_sha256": sha256((UPSTREAM / filename).read_bytes()),
                "normalized_path": relative,
                "normalized_bytes": len(normalized),
                "normalized_sha256": sha256(normalized),
                "segments": len(segments),
                "structures": len(structures),
            }
        )
    segment_payload = canonical_jsonl(all_segments)
    structure_payload = canonical_jsonl(all_structures)
    template_payload = translation_template(all_segments)
    outputs["backend/first_unit_segments.jsonl"] = segment_payload
    outputs["backend/first_unit_structures.jsonl"] = structure_payload
    outputs["source/id-ID/first_unit_translation.csv"] = template_payload
    receipt = {
        "schema": "o006.stat415.first-unit-normalization.v1",
        "status": "normalized-source-ready",
        "documents": documents,
        "document_count": len(documents),
        "segment_count": len(all_segments),
        "structure_count": len(all_structures),
        "segments": {"path": "backend/first_unit_segments.jsonl", "bytes": len(segment_payload), "sha256": sha256(segment_payload)},
        "structures": {"path": "backend/first_unit_structures.jsonl", "bytes": len(structure_payload), "sha256": sha256(structure_payload)},
        "translation_template": {"path": "source/id-ID/first_unit_translation.csv", "bytes": len(template_payload), "sha256": sha256(template_payload)},
        "source_rule": "semantic main only; scripts/styles excluded; formulas/code protected; stable IDs additive",
    }
    outputs["build/FIRST_UNIT_NORMALIZATION_RECEIPT.json"] = canonical_json(receipt)
    return outputs


def validate_live_translation(live: bytes, pending_template: bytes) -> None:
    """Permit completed targets while proving the immutable template fields."""
    fields = (
        "segment_id", "document_id", "component_id", "section_id",
        "source_sha256", "source_text", "target_text", "status",
    )
    try:
        live_rows = list(csv.DictReader(io.StringIO(live.decode("utf-8"))))
        expected_rows = list(csv.DictReader(io.StringIO(pending_template.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid live translation ledger: {exc}") from exc
    if len(live_rows) != len(expected_rows):
        raise RuntimeError("live translation ledger row count differs from normalized segments")
    if not live_rows or tuple(live_rows[0].keys()) != fields:
        raise RuntimeError("live translation ledger header differs")
    immutable = fields[:-2]
    for number, (actual, expected) in enumerate(zip(live_rows, expected_rows), start=2):
        if any(actual[key] != expected[key] for key in immutable):
            raise RuntimeError(f"live translation ledger source fields differ at CSV row {number}")
        if actual["status"] not in {"pending", "translated"}:
            raise RuntimeError(f"invalid translation status at CSV row {number}")
        if actual["status"] == "translated" and not actual["target_text"].strip():
            raise RuntimeError(f"translated row has empty target at CSV row {number}")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if relative == "source/id-ID/first_unit_translation.csv" and path.is_file():
                validate_live_translation(path.read_bytes(), payload)
                continue
            atomic_write(path, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"normalized output missing: {relative}")
            if relative == "source/id-ID/first_unit_translation.csv":
                validate_live_translation(path.read_bytes(), expected)
            elif path.read_bytes() != expected:
                raise RuntimeError(f"normalized output differs: {relative}")
        mode_name = "verified"
    receipt = json.loads(outputs["build/FIRST_UNIT_NORMALIZATION_RECEIPT.json"])
    print(
        json.dumps(
            {
                "mode": mode_name,
                "documents": receipt["document_count"],
                "segments": receipt["segment_count"],
                "structures": receipt["structure_count"],
                "receipt_sha256": sha256(outputs["build/FIRST_UNIT_NORMALIZATION_RECEIPT.json"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
