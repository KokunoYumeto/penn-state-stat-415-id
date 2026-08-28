#!/usr/bin/env python3
"""Deterministically audit the consolidated STAT 415 Indonesian PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "output" / "pdf" / "stat415-pengantar-statistika-matematis-id.pdf"
DEFAULT_REPLAY = ROOT / "tmp" / "pdfs" / "stat415-pengantar-statistika-matematis-id-replay.pdf"
DEFAULT_RECEIPT = ROOT / "build" / "CONSOLIDATED_PDF_QA_RECEIPT.json"
EXPECTED_PAGES = 219
EXPECTED_TITLE = "STAT 415: Pengantar Statistika Matematis - Edisi Bahasa Indonesia"
EXPECTED_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_PAGE_WIDTH = 594.96
EXPECTED_PAGE_HEIGHT = 841.92


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def dereference(value: Any) -> Any:
    return value.get_object() if isinstance(value, IndirectObject) else value


def object_identity(value: Any) -> str:
    if isinstance(value, IndirectObject):
        return f"{value.idnum}:{value.generation}"
    return f"direct:{id(value)}"


def embedded_font(font: DictionaryObject) -> bool:
    if str(font.get("/Subtype")) == "/Type3":
        return bool(font.get("/CharProcs"))
    descendants = dereference(font.get("/DescendantFonts"))
    candidates = []
    if isinstance(descendants, ArrayObject):
        candidates.extend(dereference(item) for item in descendants)
    candidates.append(font)
    for candidate in candidates:
        if not isinstance(candidate, DictionaryObject):
            continue
        descriptor = dereference(candidate.get("/FontDescriptor"))
        if isinstance(descriptor, DictionaryObject) and any(
            descriptor.get(key) is not None for key in ("/FontFile", "/FontFile2", "/FontFile3")
        ):
            return True
    return False


def flatten_outline(items: list[Any]) -> list[str]:
    labels: list[str] = []
    for item in items:
        if isinstance(item, list):
            labels.extend(flatten_outline(item))
        else:
            title = getattr(item, "title", None)
            if title:
                labels.append(str(title))
    return labels


def readable_outline_title(text: str) -> str:
    return (
        text.replace("\\sigma^2", "σ²")
        .replace("\\alpha", "α")
        .replace("\\beta", "β")
        .replace("\\(", "")
        .replace("\\)", "")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--replay", type=Path, default=DEFAULT_REPLAY)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    pdf = args.pdf.resolve()
    replay = args.replay.resolve()
    receipt_path = args.receipt.resolve()
    if not pdf.is_file() or not replay.is_file():
        raise RuntimeError("Canonical PDF and deterministic replay must both exist")

    pdf_hash = sha256(pdf)
    replay_hash = sha256(replay)
    if replay.stat().st_size != pdf.stat().st_size or replay_hash != pdf_hash:
        raise RuntimeError("Independent canonical PDF replay is not byte-identical")

    reader = PdfReader(pdf, strict=False)
    root = reader.root_object
    metadata = reader.metadata or {}
    if len(reader.pages) != EXPECTED_PAGES:
        raise RuntimeError(f"Expected {EXPECTED_PAGES} pages, found {len(reader.pages)}")
    if metadata.get("/Title") != EXPECTED_TITLE:
        raise RuntimeError("PDF title metadata mismatch")
    if metadata.get("/Creator") != EXPECTED_PROVENANCE:
        raise RuntimeError("PDF provenance metadata mismatch")
    if str(root.get("/Lang")) != "id-ID":
        raise RuntimeError("PDF catalog language is not id-ID")
    mark_info = dereference(root.get("/MarkInfo"))
    if not root.get("/StructTreeRoot") or not isinstance(mark_info, DictionaryObject) or not mark_info.get("/Marked"):
        raise RuntimeError("PDF is not tagged as a structured document")
    if root.get("/AcroForm") or root.get("/JavaScript") or root.get("/OpenAction") or root.get("/AA"):
        raise RuntimeError("Unexpected interactive form or active-content entry")

    page_text_lengths: list[int] = []
    page_word_counts: list[int] = []
    replacement_character_pages: list[int] = []
    page_size_failures: list[dict[str, Any]] = []
    font_records: dict[str, dict[str, Any]] = {}
    image_objects: set[str] = set()
    annotations = {"total": 0, "links": 0, "uri": 0, "internal": 0, "other": 0, "widgets": 0}
    all_text: list[str] = []

    for page_number, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if abs(width - EXPECTED_PAGE_WIDTH) > 0.1 or abs(height - EXPECTED_PAGE_HEIGHT) > 0.1:
            page_size_failures.append({"page": page_number, "width": width, "height": height})

        text = page.extract_text() or ""
        all_text.append(text)
        page_text_lengths.append(len(text.strip()))
        page_word_counts.append(len(re.findall(r"\b\w+\b", text, flags=re.UNICODE)))
        if "\ufffd" in text:
            replacement_character_pages.append(page_number)

        resources = dereference(page.get("/Resources"))
        if isinstance(resources, DictionaryObject):
            fonts = dereference(resources.get("/Font"))
            if isinstance(fonts, DictionaryObject):
                for value in fonts.values():
                    key = object_identity(value)
                    font = dereference(value)
                    if isinstance(font, DictionaryObject) and key not in font_records:
                        font_records[key] = {
                            "base_font": str(font.get("/BaseFont", "")),
                            "embedded": embedded_font(font),
                            "subtype": str(font.get("/Subtype", "")),
                            "to_unicode": font.get("/ToUnicode") is not None,
                        }
            xobjects = dereference(resources.get("/XObject"))
            if isinstance(xobjects, DictionaryObject):
                for value in xobjects.values():
                    candidate = dereference(value)
                    if isinstance(candidate, DictionaryObject) and str(candidate.get("/Subtype")) == "/Image":
                        image_objects.add(object_identity(value))

        annots = dereference(page.get("/Annots"))
        if isinstance(annots, ArrayObject):
            for value in annots:
                annotation = dereference(value)
                if not isinstance(annotation, DictionaryObject):
                    continue
                annotations["total"] += 1
                subtype = str(annotation.get("/Subtype", ""))
                if subtype == "/Widget":
                    annotations["widgets"] += 1
                if subtype != "/Link":
                    annotations["other"] += 1
                    continue
                annotations["links"] += 1
                action = dereference(annotation.get("/A"))
                if isinstance(action, DictionaryObject) and str(action.get("/S")) == "/URI":
                    annotations["uri"] += 1
                elif annotation.get("/Dest") is not None or (
                    isinstance(action, DictionaryObject) and str(action.get("/S")) == "/GoTo"
                ):
                    annotations["internal"] += 1
                else:
                    annotations["other"] += 1

    text_joined = "\n".join(all_text)
    if not EXPECTED_PROVENANCE in text_joined:
        raise RuntimeError("Reader-visible provenance is missing")
    blank_pages = [index for index, length in enumerate(page_text_lengths, start=1) if length == 0]
    missing_embedded_fonts = [record for record in font_records.values() if not record["embedded"]]
    missing_unicode_fonts = [record for record in font_records.values() if not record["to_unicode"]]
    if blank_pages or replacement_character_pages or page_size_failures:
        raise RuntimeError("Blank pages, replacement characters, or non-A4 pages found")
    if missing_embedded_fonts or missing_unicode_fonts:
        raise RuntimeError("Unembedded font or font without ToUnicode mapping found")
    if annotations["widgets"]:
        raise RuntimeError("Unexpected widget annotation found")

    raw_lower = pdf.read_bytes().lower()
    sensitive_markers = [b"c:\\users\\", b"github token", b"zenodo token", b"figshare token"]
    found_sensitive_markers = [marker.decode("ascii") for marker in sensitive_markers if marker in raw_lower]
    if found_sensitive_markers:
        raise RuntimeError(f"Sensitive/local marker found: {found_sensitive_markers}")

    outline_titles = flatten_outline(reader.outline)
    soup = BeautifulSoup((ROOT / "build" / "book" / "stat415-id-book.html").read_text(encoding="utf-8"), "html.parser")
    expected_outline_titles = [
        "Pengantar Statistika Matematis",
        "Daftar Isi",
        *[
            readable_outline_title(" ".join(heading.stripped_strings))
            for heading in soup.select("h1, h2, h3, h4, h5, h6")
        ],
    ]
    if outline_titles != expected_outline_titles:
        raise RuntimeError("PDF outline titles do not exactly match source heading order")
    receipt = {
        "artifact": {
            "bytes": pdf.stat().st_size,
            "path": relative(pdf),
            "pages": len(reader.pages),
            "sha256": pdf_hash,
        },
        "deterministic_replay": {
            "bytes": replay.stat().st_size,
            "matches_artifact": True,
            "path": relative(replay),
            "sha256": replay_hash,
        },
        "metadata": {
            "author": metadata.get("/Author"),
            "creation_date": metadata.get("/CreationDate"),
            "creator": metadata.get("/Creator"),
            "language": str(root.get("/Lang")),
            "modification_date": metadata.get("/ModDate"),
            "subject": metadata.get("/Subject"),
            "title": metadata.get("/Title"),
        },
        "privacy_and_active_content": {
            "acroform": False,
            "active_actions": False,
            "encrypted": reader.is_encrypted,
            "sensitive_markers": found_sensitive_markers,
        },
        "schema": "o006.stat415.consolidated-pdf-qa.v1",
        "structure": {
            "annotations": annotations,
            "blank_pages": blank_pages,
            "embedded_fonts": len(font_records),
            "image_xobjects": len(image_objects),
            "outline_entries": len(outline_titles),
            "outline_titles": outline_titles,
            "page_height_points": EXPECTED_PAGE_HEIGHT,
            "page_size_failures": page_size_failures,
            "page_width_points": EXPECTED_PAGE_WIDTH,
            "replacement_character_pages": replacement_character_pages,
            "tagged": True,
            "text_characters": sum(page_text_lengths),
            "word_like_tokens": sum(page_word_counts),
        },
        "status": "passed",
    }
    serialized = f"{json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)}\n"
    if args.check_only:
        if not receipt_path.is_file() or receipt_path.read_text(encoding="utf-8") != serialized:
            raise RuntimeError("Stored PDF QA receipt differs from deterministic replay")
    else:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(serialized, encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "bytes": receipt["artifact"]["bytes"],
                "outline_entries": receipt["structure"]["outline_entries"],
                "pages": receipt["artifact"]["pages"],
                "replay_match": receipt["deterministic_replay"]["matches_artifact"],
                "sha256": receipt["artifact"]["sha256"],
                "status": receipt["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
