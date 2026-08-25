#!/usr/bin/env python3
"""Build the cumulative id-ID reader through STAT 415 Lesson 09."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson03 as page_base
import build_through_lesson04 as patch04
import build_through_lesson05 as patch05
import build_through_lesson06 as prior
import lesson07_corrections as corrections07
import lesson08_corrections as corrections08
import lesson09_corrections as corrections09


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
DOCUMENTS = ROOT / "backend" / "through_lesson09_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson09_corrections.jsonl"
MANIFEST = ROOT / "build" / "THROUGH_LESSON09_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON09_BUILD_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
PRIOR_CSS = PurePosixPath("assets/reader-8of14.css")
CURRENT_CSS = PurePosixPath("assets/reader-11of14.css")
EXPECTED_PRIOR_CSS_BYTES = 7_760
EXPECTED_PRIOR_CSS_SHA256 = "a80552e645d5dfecb2cc79787213cd5a928c8f7a477c30b475c21a4db90c5f7a"
EXPECTED_TOTAL_SEGMENTS = 3_458
EXPECTED_TOTAL_UNITS = 4_775
EXPECTED_TARGET_UNITS = 4_763
EXPECTED_TOTAL_MATH = 2_171
EXPECTED_TOTAL_CORRECTIONS = 170
EXPECTED_READER_FILES = 71
EXPECTED_ASSET_FILES = 16
EXPECTED_ASSET_BYTES = 4_574_263
EXPECTED_GLOSSARY_ROWS = 142

REFLOW_CSS = """

/* Lessons 07–09: readable, centered, full-width instructional surfaces. */
main#quarto-document-content figure,
main#quarto-document-content .quarto-figure,
main#quarto-document-content .cell-output-display,
main#quarto-document-content a.lightbox {
  display: block;
  width: 100%;
  max-width: 100%;
  margin-inline: auto;
}

main#quarto-document-content figure img,
main#quarto-document-content .quarto-figure img,
main#quarto-document-content img[data-o006-asset-id] {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  margin-inline: auto;
}

main#quarto-document-content pre,
main#quarto-document-content .sourceCode,
main#quarto-document-content .cell-output {
  max-width: 100%;
  overflow-x: auto;
  white-space: pre;
}

main#quarto-document-content table {
  display: block;
  width: max-content;
  max-width: 100%;
  overflow-x: auto;
  margin-inline: auto;
}
""".encode("utf-8")


@dataclass(frozen=True)
class Lesson:
    number: int
    document_id: str
    segments: int
    units: int
    maths: int
    assets: int
    corrections: int
    first_correction: int
    apply_corrections: Callable[[Tag, list[dict[str, str]]], list[dict[str, object]]]
    removed_units: tuple[str, ...] = ()

    @property
    def component(self) -> str:
        return f"Lesson{self.number:02d}"

    @property
    def filename(self) -> str:
        return self.component + ".html"

    @property
    def source_url(self) -> str:
        return f"https://online.stat.psu.edu/stat415/{self.component}"


LESSONS = (
    Lesson(7, "O006-PSU-008", 237, 399, 148, 2, 12, 123, corrections07.apply_lesson07_corrections),
    Lesson(
        8,
        "O006-PSU-009",
        291,
        604,
        156,
        4,
        17,
        135,
        corrections08.apply_lesson08_corrections,
        (
            "O006-PSU-009-U0572",
            "O006-PSU-009-U0573",
            "O006-PSU-009-U0574",
            "O006-PSU-009-U0575",
            "O006-PSU-009-U0576",
            "O006-PSU-009-U0598",
            "O006-PSU-009-U0599",
            "O006-PSU-009-U0600",
            "O006-PSU-009-U0601",
            "O006-PSU-009-U0602",
        ),
    ),
    Lesson(9, "O006-PSU-010", 443, 414, 219, 10, 19, 152, corrections09.apply_lesson09_corrections),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": relative(path), "bytes": len(data), "sha256": sha256(data)}


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def parse_jsonl(payload: bytes, label: str) -> list[dict[str, object]]:
    try:
        rows = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{label} contains a non-object row")
    return rows


def matches_identity(record: object, path: Path) -> bool:
    expected = identity(path)
    return isinstance(record, dict) and all(record.get(k) == v for k, v in expected.items())


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lesson09 cumulative patch differs: {label}: {text.count(old)}")
    return text.replace(old, new, 1)


def patch_page(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            "partial: 8 of 14 documents complete; landing and Lessons 00–06",
            "partial: 11 of 14 documents complete; landing and Lessons 00–09",
            "metadata",
        ),
        (
            '<a href="Lesson06.html">Pelajaran 06</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson06.html">Pelajaran 06</a><a href="Lesson07.html">Pelajaran 07</a><a href="Lesson08.html">Pelajaran 08</a><a href="Lesson09.html">Pelajaran 09</a><a href="licenses/index.html">Lisensi</a>',
            "navigation",
        ),
        (
            "<strong>Edisi Bahasa Indonesia — 8 dari 14 dokumen.</strong>",
            "<strong>Edisi Bahasa Indonesia — 11 dari 14 dokumen.</strong>",
            "edition note",
        ),
        (
            "Laman utama serta Pelajaran 00–06 telah diterjemahkan sepenuhnya.",
            "Laman utama serta Pelajaran 00–09 telah diterjemahkan sepenuhnya.",
            "complete range",
        ),
        (
            "Pelajaran 07–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "Pelajaran 10–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "pending range",
        ),
        ("assets/reader-8of14.css", "assets/reader-11of14.css", "stylesheet"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, f"{filename} {label}")
    expected_inline_widths = {"Lesson04.html": 1, "Lesson05.html": 8}.get(filename, 0)
    text, removed_inline_widths = re.subn(
        r'(<img\b[^>]*\bdata-o006-asset-id="[^"]+"[^>]*) style="width:\d+(?:\.\d+)?%"',
        r"\1",
        text,
    )
    if removed_inline_widths != expected_inline_widths:
        raise RuntimeError(
            f"{filename} inherited inline-width census differs: "
            f"{removed_inline_widths} != {expected_inline_widths}"
        )
    if filename == "index.html":
        for number, unit in ((7, "0118"), (8, "0132"), (9, "0146")):
            old = (
                f'<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U{unit}" '
                f'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson{number:02d}" '
                'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
            )
            new = (
                f'<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U{unit}" '
                f'data-translation-status="complete" href="Lesson{number:02d}.html">'
            )
            text = replace_once(text, old, new, f"index Lesson{number:02d} route")
    return text.encode("utf-8")


def patch_license(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<a href="../Lesson06.html">Pelajaran 06</a></nav>',
            '<a href="../Lesson06.html">Pelajaran 06</a><a href="../Lesson07.html">Pelajaran 07</a><a href="../Lesson08.html">Pelajaran 08</a><a href="../Lesson09.html">Pelajaran 09</a></nav>',
            "license navigation",
        ),
        ("../assets/reader-8of14.css", "../assets/reader-11of14.css", "license stylesheet"),
        (
            "dan sepuluh koreksi Lesson 06 yang dicatat secara terpisah.",
            "sepuluh koreksi Lesson 06, dua belas koreksi Lesson 07, tujuh belas koreksi Lesson 08, dan sembilan belas koreksi Lesson 09 yang dicatat secara terpisah.",
            "license correction census",
        ),
        (
            "Satu PNG kurva normal baku Lesson 06 dibekukan dari URL resmi; byte sumber dipertahankan, teks alternatif dilengkapi, dan kekeliruan huruf kapital pada label nilai kritis dijelaskan dalam catatan koreksi turunan.",
            "Satu PNG kurva normal baku Lesson 06 dibekukan dari URL resmi; byte sumber dipertahankan, teks alternatif dilengkapi, dan kekeliruan huruf kapital pada label nilai kritis dijelaskan dalam catatan koreksi turunan. Dua PNG Lesson 07, empat PNG Lesson 08, serta sembilan PNG dan satu SVG Lesson 09 juga dibekukan byte demi byte dari URL resmi; teks alternatif, keterangan, semantik tabel, dan tata letak responsif diperbaiki hanya pada turunan. Dua keluaran plot Lesson 09 tetap diungkapkan sebagai keluaran beku karena kode dan input pembangkitnya tidak tersedia.",
            "license new assets",
        ),
        (
            "laman utama serta Pelajaran 00–06 lengkap; Pelajaran 07–12 belum diterjemahkan.",
            "laman utama serta Pelajaran 00–09 lengkap; Pelajaran 10–12 belum diterjemahkan.",
            "license status",
        ),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text.encode("utf-8")


def validate_glossary() -> None:
    with GLOSSARY.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if reader.fieldnames != ["term_id", "en_US", "id_ID", "decision"]:
        raise RuntimeError("glossary schema differs")
    expected = [f"O006-TERM-{i:04d}" for i in range(1, EXPECTED_GLOSSARY_ROWS + 1)]
    if [row["term_id"] for row in rows] != expected:
        raise RuntimeError("glossary sequence differs through Lesson09")


def input_paths(lesson: Lesson) -> dict[str, Path]:
    key = f"lesson{lesson.number:02d}"
    return {
        "normalized": ROOT / "source" / "normalized" / "en-US" / lesson.filename,
        "translations": ROOT / "source" / "id-ID" / f"{key}_translation.csv",
        "bindings": ROOT / "backend" / f"{key}_translation_bindings.jsonl",
        "translation_receipt": ROOT / "build" / f"LESSON{lesson.number:02d}_TRANSLATION_RECEIPT.json",
        "normalization_receipt": ROOT / "build" / f"LESSON{lesson.number:02d}_NORMALIZATION_RECEIPT.json",
        "merge_script": ROOT / "scripts" / f"merge_{key}_translations.py",
        "correction_module": ROOT / "scripts" / f"{key}_corrections.py",
    }


def load_assets(
    lesson: Lesson,
    main: Tag,
    receipt: dict[str, object],
    source_asset_styles: dict[str, str],
) -> tuple[dict[PurePosixPath, bytes], list[dict[str, object]]]:
    inventory = receipt.get("asset_inventory")
    outputs = receipt.get("outputs")
    if not isinstance(inventory, list) or len(inventory) != lesson.assets:
        raise RuntimeError(f"{lesson.component} asset inventory differs")
    output_assets = outputs.get("assets", []) if isinstance(outputs, dict) else []
    by_hash = {
        str(row.get("sha256")): str(row.get("path"))
        for row in output_assets
        if isinstance(row, dict)
    }
    reader_assets: dict[PurePosixPath, bytes] = {}
    evidence: list[dict[str, object]] = []
    for row in inventory:
        if not isinstance(row, dict):
            raise RuntimeError(f"{lesson.component} asset row is not an object")
        asset_id = str(row.get("asset_id"))
        source_ref = str(row.get("source_ref"))
        local_text = str(row.get("local_path") or by_hash.get(str(row.get("sha256"))) or "")
        if not local_text:
            local_text = f"authority/assets/stat415/lesson{lesson.number:02d}/{source_ref}"
        authority = ROOT / Path(local_text)
        payload = authority.read_bytes()
        if len(payload) != int(row.get("bytes", -1)) or sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"{lesson.component} authority asset differs: {asset_id}")
        images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
        if len(images) != int(row.get("occurrences", -1)) or len(images) != 1:
            raise RuntimeError(f"{lesson.component} image occurrence differs: {asset_id}")
        image = images[0]
        if image.get("src") != source_ref:
            raise RuntimeError(f"{lesson.component} image source route differs: {asset_id}")
        alt = str(image.get("alt") or "").strip()
        if len(alt) < 20:
            raise RuntimeError(f"{lesson.component} corrected image alternative is incomplete: {asset_id}")
        target = PurePosixPath(f"assets/lesson{lesson.number:02d}") / PurePosixPath(source_ref)
        image["src"] = target.as_posix()
        source_style = source_asset_styles.get(asset_id, "")
        target_style = str(image.get("style") or "")
        if target_style:
            target_style = re.sub(r"(?:^|;)\s*width\s*:[^;]+;?", ";", target_style).strip(" ;")
            if target_style:
                image["style"] = target_style
            else:
                image.attrs.pop("style", None)
        for anchor in main.select(f'a[href="{source_ref}"]'):
            anchor["href"] = target.as_posix()
        if target in reader_assets:
            raise RuntimeError(f"{lesson.component} target asset collision: {target}")
        reader_assets[target] = payload
        evidence.append({
            "asset_id": asset_id,
            "source_path": relative(authority),
            "source_bytes": len(payload),
            "source_sha256": sha256(payload),
            "target_path": target.as_posix(),
            "target_bytes": len(payload),
            "target_sha256": sha256(payload),
            "target_is_byte_preserving": True,
            "target_alt_sha256": sha256(alt.encode("utf-8")),
            "source_inline_style": source_style or None,
            "target_inline_style": image.get("style"),
        })
    return reader_assets, evidence


def load_lesson(lesson: Lesson) -> dict[str, object]:
    paths = input_paths(lesson)
    normalization = json.loads(paths["normalization_receipt"].read_text("utf-8"))
    translation_receipt = json.loads(paths["translation_receipt"].read_text("utf-8"))
    counts = normalization.get("counts")
    if (
        normalization.get("schema") != f"o006.stat415.lesson{lesson.number:02d}-normalization.v1"
        or not isinstance(counts, dict)
        or counts.get("translation_segments") != lesson.segments
        or counts.get("structural_units") != lesson.units
        or counts.get("math_nodes") != lesson.maths
        or counts.get("assets") != lesson.assets
        or normalization.get("source_defect_count") != lesson.corrections
    ):
        raise RuntimeError(f"{lesson.component} normalization receipt differs")
    if (
        translation_receipt.get("schema") != f"o006.stat415.lesson{lesson.number:02d}-translation.v1"
        or translation_receipt.get("status") != "complete"
        or translation_receipt.get("document_id") != lesson.document_id
        or translation_receipt.get("segment_count") != lesson.segments
        or translation_receipt.get("translation_provenance") != PROVENANCE
        or not matches_identity(translation_receipt.get("merge_script"), paths["merge_script"])
        or not matches_identity(translation_receipt.get("translation_csv"), paths["translations"])
        or not matches_identity(translation_receipt.get("bindings"), paths["bindings"])
    ):
        raise RuntimeError(f"{lesson.component} translation receipt differs")

    with paths["translations"].open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    expected_fields = [
        "segment_id", "document_id", "component_id", "section_id",
        "source_sha256", "source_text", "target_text", "status",
    ]
    if reader.fieldnames != expected_fields or len(rows) != lesson.segments:
        raise RuntimeError(f"{lesson.component} translation CSV differs")
    bindings = parse_jsonl(paths["bindings"].read_bytes(), f"{lesson.component} bindings")
    if len(bindings) != lesson.segments:
        raise RuntimeError(f"{lesson.component} binding count differs")

    soup = BeautifulSoup(paths["normalized"].read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError(f"{lesson.component} main is missing")
    units = shared.stable_values(main, "data-o006-id")
    maths = shared.stable_values(main, "data-o006-math-id")
    if units != [f"{lesson.document_id}-U{i:04d}" for i in range(1, lesson.units + 1)]:
        raise RuntimeError(f"{lesson.component} stable-unit sequence differs")
    if maths != [f"{lesson.document_id}-M{i:04d}" for i in range(1, lesson.maths + 1)]:
        raise RuntimeError(f"{lesson.component} math-ID sequence differs")
    source_math = [node.get_text() for node in main.select(".math")]
    source_asset_styles = {
        str(node.get("data-o006-asset-id")): str(node.get("style") or "")
        for node in main.select("img[data-o006-asset-id]")
    }
    nodes = shared.translatable_nodes(main)
    if len(nodes) != lesson.segments:
        raise RuntimeError(f"{lesson.component} translatable-node count differs")
    for ordinal, (row, binding, node) in enumerate(zip(rows, bindings, nodes), start=1):
        segment_id = f"{lesson.document_id}-S{ordinal:04d}"
        source = str(node)
        target = row["target_text"]
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": segment_id,
            "document_id": lesson.document_id,
            "component_id": lesson.component,
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": sha256(target.encode("utf-8")),
            "status": "translated",
        }
        if (
            row["segment_id"] != segment_id
            or row["document_id"] != lesson.document_id
            or row["component_id"] != lesson.component
            or row["source_text"] != source
            or row["source_sha256"] != sha256(source.encode("utf-8"))
            or row["status"] != "translated"
            or not target.strip()
            or "\ufffd" in target
            or binding != expected_binding
        ):
            raise RuntimeError(f"{lesson.component} translation binding differs: {segment_id}")
        node.replace_with(NavigableString(target))

    correction_rows = lesson.apply_corrections(main, rows)
    expected_corrections = [
        f"O006-PSU-ADV-{i:04d}"
        for i in range(lesson.first_correction, lesson.first_correction + lesson.corrections)
    ]
    expected_findings = [f"L{lesson.number:02d}-D{i:03d}" for i in range(1, lesson.corrections + 1)]
    if (
        [row.get("correction_id") for row in correction_rows] != expected_corrections
        or [row.get("source_defect_id") for row in correction_rows] != expected_findings
    ):
        raise RuntimeError(f"{lesson.component} correction registry differs")
    assets, asset_evidence = load_assets(lesson, main, normalization, source_asset_styles)
    shared.normalize_lesson(main, lesson.filename)
    removed = set(lesson.removed_units)
    if not removed.issubset(units):
        raise RuntimeError(f"{lesson.component} registered removed-unit identity differs")
    expected_target_units = [unit_id for unit_id in units if unit_id not in removed]
    actual_target_units = shared.stable_values(main, "data-o006-id")
    if actual_target_units != expected_target_units:
        missing = [unit_id for unit_id in expected_target_units if unit_id not in actual_target_units]
        extra = [unit_id for unit_id in actual_target_units if unit_id not in expected_target_units]
        raise RuntimeError(
            f"{lesson.component} target stable-unit topology differs: "
            f"expected={len(expected_target_units)} actual={len(actual_target_units)} "
            f"missing={missing[:8]} extra={extra[:8]}"
        )
    if shared.stable_values(main, "data-o006-math-id") != maths:
        raise RuntimeError(f"{lesson.component} target math topology differs")
    if len(main.select(".math")) != lesson.maths:
        raise RuntimeError(f"{lesson.component} target math count differs")
    if shared.native_id_duplicates(main):
        raise RuntimeError(f"{lesson.component} target retains duplicate native IDs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError(f"{lesson.component} target retains executable/embed dependencies")
    return {
        "main": main,
        "rows": rows,
        "source_math": source_math,
        "units": units,
        "maths": maths,
        "corrections": correction_rows,
        "assets": assets,
        "asset_evidence": asset_evidence,
        "paths": paths,
    }


def make_page(main: Tag, lesson: Lesson) -> bytes:
    payload = page_base.page_document(main, lesson.component, lesson.source_url)
    payload = patch04.patch_page(payload, lesson.filename)
    payload = patch05.patch_page(payload, lesson.filename)
    payload = prior.patch_page(payload, lesson.filename)
    return patch_page(payload, lesson.filename)


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in ("index.html", *[f"Lesson{i:02d}.html" for i in range(10)]):
        soup = BeautifulSoup(reader[PurePosixPath(filename)], "html.parser")
        total += len(soup.select("[data-o006-id]"))
    return total


def compute() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    validate_glossary()
    prior_outputs, prior_receipt, prior_files = prior.compute()
    if prior_receipt.get("coverage", {}).get("complete_count") != 8 or len(prior_files) != 52:
        raise RuntimeError("replayed Lesson06 boundary differs")
    reader = {
        PurePosixPath(name.removeprefix("build/html-id/")): payload
        for name, payload in prior_outputs.items()
        if name.startswith("build/html-id/")
    }
    if set(reader) != prior_files:
        raise RuntimeError("replayed Lesson06 reader inventory differs")
    css = reader.pop(PRIOR_CSS, None)
    if css is None or len(css) != EXPECTED_PRIOR_CSS_BYTES or sha256(css) != EXPECTED_PRIOR_CSS_SHA256:
        raise RuntimeError("Lesson06 responsive reader CSS differs")
    css += REFLOW_CSS
    reader[CURRENT_CSS] = css

    target_outputs: dict[str, bytes] = {}
    document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson06_documents.jsonl"], "Lesson06 documents"
    )
    by_filename = {PurePosixPath(str(row["target_path"])).name: row for row in document_rows}
    prior_filenames = ("index.html", *[f"Lesson{i:02d}.html" for i in range(7)])
    if set(by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson06 document backend filenames differ")
    for filename in prior_filenames:
        payload = patch_page(reader[PurePosixPath(filename)], filename)
        reader[PurePosixPath(filename)] = payload
        target_outputs[f"source/id-ID/{filename}"] = payload
        by_filename[filename]["target_bytes"] = len(payload)
        by_filename[filename]["target_sha256"] = sha256(payload)
    document_rows = [by_filename[name] for name in prior_filenames]

    prior_corrections = parse_jsonl(
        prior_outputs["backend/through_lesson06_corrections.jsonl"], "Lesson06 corrections"
    )
    if len(prior_corrections) != 122:
        raise RuntimeError("Lesson06 correction boundary differs")
    correction_rows = list(prior_corrections)
    lesson_inputs: list[dict[str, object]] = []
    all_asset_evidence: list[dict[str, object]] = []
    for lesson in LESSONS:
        loaded = load_lesson(lesson)
        main = loaded["main"]
        assert isinstance(main, Tag)
        lesson_payload = make_page(main, lesson)
        reader[PurePosixPath(lesson.filename)] = lesson_payload
        target_outputs[f"source/id-ID/{lesson.filename}"] = lesson_payload
        assets = loaded["assets"]
        assert isinstance(assets, dict)
        for path, payload in assets.items():
            if path in reader:
                raise RuntimeError(f"{lesson.component} asset collides with reader: {path}")
            reader[path] = payload
        source_math = loaded["source_math"]
        units = loaded["units"]
        rows = loaded["rows"]
        assert isinstance(source_math, list) and isinstance(units, list) and isinstance(rows, list)
        target_math = [node.get_text() for node in main.select(".math")]
        document_rows.append(shared.document_row(
            lesson.component,
            lesson.filename,
            lesson.document_id,
            lesson.source_url,
            source_math,
            target_math,
            lesson_payload,
            len(rows),
            len(units),
        ))
        fresh = loaded["corrections"]
        evidence = loaded["asset_evidence"]
        assert isinstance(fresh, list) and isinstance(evidence, list)
        correction_rows.extend(fresh)
        all_asset_evidence.extend(evidence)
        paths = loaded["paths"]
        assert isinstance(paths, dict)
        lesson_inputs.append({
            "component": lesson.component,
            "normalization": identity(paths["normalization_receipt"]),
            "translation": identity(paths["translation_receipt"]),
            "correction_module": identity(paths["correction_module"]),
        })

    license_path = PurePosixPath("licenses/index.html")
    reader[license_path] = patch_license(reader[license_path])
    if len(document_rows) != 11:
        raise RuntimeError("cumulative document count differs")
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative source-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math count differs")
    if len(correction_rows) != EXPECTED_TOTAL_CORRECTIONS:
        raise RuntimeError("cumulative correction count differs")
    if [row.get("correction_id") for row in correction_rows] != [
        f"O006-PSU-ADV-{i:04d}" for i in range(1, EXPECTED_TOTAL_CORRECTIONS + 1)
    ]:
        raise RuntimeError("cumulative correction ID sequence differs")
    if len(all_asset_evidence) != EXPECTED_ASSET_FILES:
        raise RuntimeError("new asset count differs")
    if sum(int(row["source_bytes"]) for row in all_asset_evidence) != EXPECTED_ASSET_BYTES:
        raise RuntimeError("new authority asset bytes differ")
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError(f"reader file census differs: {len(reader)}")
    if target_unit_count(reader) != EXPECTED_TARGET_UNITS:
        raise RuntimeError("cumulative target-unit count differs")
    shared.validate_reader_links(reader)

    documents_payload = first.canonical_jsonl(document_rows)
    corrections_payload = first.canonical_jsonl(correction_rows)
    manifest_payload = first.manifest_payload(reader)
    outputs: dict[str, bytes] = dict(target_outputs)
    for path, payload in reader.items():
        outputs[f"build/html-id/{path.as_posix()}"] = payload
    outputs[relative(DOCUMENTS)] = documents_payload
    outputs[relative(CORRECTIONS)] = corrections_payload
    outputs[relative(MANIFEST)] = manifest_payload
    receipt: dict[str, object] = {
        "schema": "o006.stat415.through-lesson09-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", *[f"Lesson{i:02d}" for i in range(10)]],
            "complete_count": 11,
            "corpus_document_count": 14,
            "next_document": "Lesson10",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "structural_units_target": EXPECTED_TARGET_UNITS,
        "math_nodes": {
            **dict(prior_receipt["math_nodes"]),
            "Lesson07": 148,
            "Lesson08": 156,
            "Lesson09": 219,
            "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson06_count": len(prior_corrections),
            "lesson07_count": 12,
            "lesson08_count": 17,
            "lesson09_count": 19,
            "path": relative(CORRECTIONS),
            "bytes": len(corrections_payload),
            "sha256": sha256(corrections_payload),
        },
        "documents_backend": {
            "path": relative(DOCUMENTS),
            "bytes": len(documents_payload),
            "sha256": sha256(documents_payload),
        },
        "reader": {
            "path": relative(BUILD),
            "files": len(reader),
            "bytes": sum(len(payload) for payload in reader.values()),
            "manifest_path": relative(MANIFEST),
            "manifest_bytes": len(manifest_payload),
            "manifest_sha256": sha256(manifest_payload),
        },
        "new_assets": {
            "count": len(all_asset_evidence),
            "bytes": sum(int(row["source_bytes"]) for row in all_asset_evidence),
            "all_byte_preserving": all(row["target_is_byte_preserving"] for row in all_asset_evidence),
            "inventory": all_asset_evidence,
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lessons07-09 assets": "sixteen same-origin authority assets frozen and redistributed byte-for-byte under the official page notice; derivative HTML supplies accessibility and responsive-layout repairs",
            "Lesson09 generated plots": "two frozen generated outputs retained with explicit non-reproducibility disclosure because generating code and inputs are absent",
            "MathJax 3.1.2": "Apache-2.0",
            "aggregate_uniform_relicense": False,
        },
        "offline": {
            "external_runtime_requests": 0,
            "analytics": False,
            "cookies": False,
            "local_mathjax": True,
            "third_party_iframes": 0,
        },
        "runtime_closure": prior_receipt["runtime_closure"],
        "layout": {
            "reader_css_path": CURRENT_CSS.as_posix(),
            "reader_css_bytes": len(css),
            "reader_css_sha256": sha256(css),
            "inherited_inline_width_constraints_removed": 9,
            "rule": "all cumulative reader figures fill and center within the available reader width; code and tables reflow horizontally without page overflow",
        },
        "inputs": {
            "prior_build_receipt": identity(ROOT / "build" / "THROUGH_LESSON06_BUILD_RECEIPT.json"),
            "glossary": identity(GLOSSARY),
            "builder": identity(Path(__file__)),
            "lessons": lesson_inputs,
        },
        "target_documents": [
            {
                "path": str(row["target_path"]),
                "bytes": int(row["target_bytes"]),
                "sha256": str(row["target_sha256"]),
            }
            for row in document_rows
        ],
    }
    outputs[relative(RECEIPT)] = first.canonical_json(receipt)
    return outputs, receipt, set(reader)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs, receipt, expected_reader = compute()
    if args.write:
        for relative_path, payload in outputs.items():
            atomic_write(ROOT / relative_path, payload)
        obsolete = BUILD / Path(PRIOR_CSS.as_posix())
        if obsolete.is_file():
            obsolete.unlink()
        state = "written"
    else:
        for relative_path, payload in outputs.items():
            path = ROOT / relative_path
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"Lesson09 cumulative output differs: {relative_path}")
        if shared.current_reader_files() != expected_reader:
            raise RuntimeError("Lesson09 reader inventory differs")
        state = "verified"
    print(json.dumps({
        "mode": state,
        "documents": 11,
        "segments": receipt["translation_segments"],
        "source_units": receipt["structural_units_normalized"],
        "target_units": receipt["structural_units_target"],
        "math_nodes": receipt["math_nodes"]["total"],
        "corrections": receipt["corrections"]["count"],
        "assets": receipt["new_assets"]["count"],
        "reader_files": receipt["reader"]["files"],
        "receipt_sha256": sha256(outputs[relative(RECEIPT)]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
