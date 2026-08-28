#!/usr/bin/env python3
"""Rewrite the browser PDF with fixed metadata and a deterministic trailer ID."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    ByteStringObject,
    DictionaryObject,
    IndirectObject,
    NameObject,
    TextStringObject,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "tmp" / "pdfs" / "stat415-id-book.raw.pdf"
DEFAULT_OUTPUT = ROOT / "output" / "pdf" / "stat415-pengantar-statistika-matematis-id.pdf"
BOOK_SOURCE = ROOT / "build" / "book" / "stat415-id-book.html"
FIXED_DATE = "D:20260826000000+02'00'"
STRUCTURE_ID = re.compile(r"node\d{8}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_structure_ids(writer: PdfWriter) -> int:
    """Canonicalize Chromium's opaque, run-dependent tagged-table node IDs."""

    found: set[str] = set()
    seen: set[int] = set()

    def collect(value: object) -> None:
        if isinstance(value, IndirectObject):
            return
        if isinstance(value, TextStringObject):
            text = str(value)
            if STRUCTURE_ID.fullmatch(text):
                found.add(text)
            return
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)
        if isinstance(value, DictionaryObject):
            for key in value.keys():
                collect(value.raw_get(key))
        elif isinstance(value, ArrayObject):
            for child in value:
                collect(child)

    for value in writer._objects:
        if value is not None:
            collect(value)

    mapping = {
        old: f"node{ordinal:08d}"
        for ordinal, old in enumerate(sorted(found, key=lambda item: int(item[4:])), start=1)
    }
    seen.clear()

    def replace(value: object) -> object:
        if isinstance(value, IndirectObject):
            return value
        if isinstance(value, TextStringObject):
            return TextStringObject(mapping.get(str(value), str(value)))
        marker = id(value)
        if marker in seen:
            return value
        seen.add(marker)
        if isinstance(value, DictionaryObject):
            for key in list(value.keys()):
                value[key] = replace(value.raw_get(key))
        elif isinstance(value, ArrayObject):
            for index, child in enumerate(list(value)):
                value[index] = replace(child)
        return value

    for index, value in enumerate(list(writer._objects)):
        if value is not None:
            writer._objects[index] = replace(value)
    return len(mapping)


def normalize_outline_titles(writer: PdfWriter) -> int:
    """Replace Chromium's duplicated/glyph-damaged labels with source headings."""

    def readable_title(text: str) -> str:
        return (
            text.replace("\\sigma^2", "σ²")
            .replace("\\alpha", "α")
            .replace("\\beta", "β")
            .replace("\\(", "")
            .replace("\\)", "")
        )

    soup = BeautifulSoup(BOOK_SOURCE.read_text(encoding="utf-8"), "html.parser")
    expected_titles = [
        "Pengantar Statistika Matematis",
        "Daftar Isi",
        *[
            readable_title(" ".join(heading.stripped_strings))
            for heading in soup.select("h1, h2, h3, h4, h5, h6")
        ],
    ]
    outlines = writer.root_object.get(NameObject("/Outlines"))
    if isinstance(outlines, IndirectObject):
        outlines = outlines.get_object()
    if not isinstance(outlines, DictionaryObject):
        raise RuntimeError("Chromium PDF did not contain the expected outline tree")

    entries: list[DictionaryObject] = []

    def visit_siblings(value: object) -> None:
        current = value
        while current is not None:
            if isinstance(current, IndirectObject):
                current = current.get_object()
            if not isinstance(current, DictionaryObject):
                raise RuntimeError("Malformed PDF outline entry")
            entries.append(current)
            child = current.get(NameObject("/First"))
            if child is not None:
                visit_siblings(child)
            current = current.get(NameObject("/Next"))

    first = outlines.get(NameObject("/First"))
    if first is not None:
        visit_siblings(first)
    if len(entries) != len(expected_titles):
        raise RuntimeError(
            f"Outline/source heading mismatch: {len(entries)} entries versus "
            f"{len(expected_titles)} expected titles"
        )
    for entry, title in zip(entries, expected_titles, strict=True):
        if not title or "\ufffd" in title:
            raise RuntimeError(f"Invalid source-derived outline title: {title!r}")
        entry[NameObject("/Title")] = TextStringObject(title)
    return len(entries)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("output", nargs="?", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    source = args.input.resolve()
    target = args.output.resolve()
    if not source.exists():
        raise RuntimeError(f"Missing raw PDF: {source}")
    if not BOOK_SOURCE.exists():
        raise RuntimeError(f"Missing consolidated source: {BOOK_SOURCE}")

    reader = PdfReader(source)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.root_object.pop(NameObject("/Metadata"), None)
    writer.root_object[NameObject("/Lang")] = TextStringObject("id-ID")
    writer.add_metadata(
        {
            "/Title": "STAT 415: Pengantar Statistika Matematis - Edisi Bahasa Indonesia",
            "/Author": (
                "Departemen Statistika, The Pennsylvania State University (sumber); "
                "OpenAI Codex gpt-5.6-sol, Ultra (terjemahan dan rekonstruksi)"
            ),
            "/Subject": "Statistika matematis; laman utama dan Pelajaran 00-12",
            "/Keywords": (
                "statistika matematis, pendugaan, MLE, selang kepercayaan, "
                "pengujian hipotesis, Bayesian, regresi linear, id-ID"
            ),
            "/Creator": "OpenAI Codex gpt-5.6-sol, Ultra",
            "/Producer": "Chromium print engine; canonicalized with pypdf",
            "/CreationDate": FIXED_DATE,
            "/ModDate": FIXED_DATE,
        }
    )
    stable_id = hashlib.sha256(BOOK_SOURCE.read_bytes() + b"\0pdf-v1").digest()[:16]
    writer._ID = ArrayObject([ByteStringObject(stable_id), ByteStringObject(stable_id)])
    normalized_structure_ids = normalize_structure_ids(writer)
    normalized_outline_titles = normalize_outline_titles(writer)

    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as stream:
        writer.write(stream)

    check = PdfReader(target)
    if len(check.pages) != len(reader.pages):
        raise RuntimeError("Page count changed during canonicalization")
    metadata = check.metadata or {}
    if metadata.get("/CreationDate") != FIXED_DATE or metadata.get("/ModDate") != FIXED_DATE:
        raise RuntimeError("Fixed PDF metadata dates were not preserved")
    result = {
        "bytes": target.stat().st_size,
        "input_bytes": source.stat().st_size,
        "input_sha256": sha256(source),
        "output": target.relative_to(ROOT).as_posix(),
        "pages": len(check.pages),
        "schema": "o006.stat415.canonical-pdf.v1",
        "sha256": sha256(target),
        "status": "passed",
        "outline_titles_normalized": normalized_outline_titles,
        "tagged_structure_ids_normalized": normalized_structure_ids,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
