#!/usr/bin/env python3
"""Build the cumulative id-ID reader through Penn State STAT 415 Lesson 06."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson05 as prior
import lesson06_corrections as corrections


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson06.html"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson06_translation.csv"
BINDINGS = ROOT / "backend" / "lesson06_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON06_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON06_NORMALIZATION_RECEIPT.json"
MERGE_SCRIPT = ROOT / "scripts" / "merge_lesson06_translations.py"
ASSET_CLOSURE = ROOT / "working" / "lesson06_asset_closure.json"
ASSET_MANIFEST = ROOT / "authority" / "LESSON06_ASSET_MANIFEST.csv"
AUTHORITY_ASSET = (
    ROOT / "authority" / "assets" / "stat415" / "lesson06" / "assets" / "ci_1.png"
)
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
DOCUMENTS = ROOT / "backend" / "through_lesson06_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson06_corrections.jsonl"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON06_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON06_BUILD_RECEIPT.json"

DOCUMENT_ID = "O006-PSU-007"
COMPONENT_ID = "Lesson06"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson06"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_SEGMENTS = 176
EXPECTED_UNITS = 149
EXPECTED_MATH = 102
EXPECTED_ASSETS = 1
EXPECTED_CORRECTIONS = 10
EXPECTED_ASSET_BYTES = 67_496
EXPECTED_TOTAL_SEGMENTS = 2_487
EXPECTED_TOTAL_UNITS = 3_358
EXPECTED_TARGET_UNITS = 3_356
EXPECTED_TOTAL_MATH = 1_648
EXPECTED_TOTAL_CORRECTIONS = 122
EXPECTED_READER_FILES = 52
EXPECTED_GLOSSARY_ROWS = 94
EXPECTED_PRIOR_CSS_BYTES = 7_353
EXPECTED_PRIOR_CSS_SHA256 = (
    "cb2364225b333e1f0284265466724b47b933b98df84532fc0aa2e8a3130425f8"
)
PRIOR_CSS = PurePosixPath("assets/reader-7of14.css")
CURRENT_CSS = PurePosixPath("assets/reader-8of14.css")
TARGET_ASSET = PurePosixPath("assets/lesson06/ci_1.png")
FIGURE_REFLOW_CSS = b"""

/* Lesson 06: use the available reader width for the centered normal-curve figure. */
#fig-standardnormal,
#fig-standardnormal figure,
#fig-standardnormal [aria-describedby],
#fig-standardnormal a.lightbox {
  display: block;
  width: 100%;
  max-width: 100%;
  margin-inline: auto;
}

#fig-standardnormal img {
  display: block;
  width: 100%;
  max-width: 100%;
  height: auto;
  margin-inline: auto;
}
"""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


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
    return isinstance(record, dict) and all(record.get(key) == value for key, value in expected.items())


def replay_prior() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    outputs, receipt, files = prior.compute()
    if receipt.get("coverage", {}).get("complete_count") != 7 or len(files) != 50:
        raise RuntimeError("replayed Lesson05 boundary differs")
    for name in (
        "backend/through_lesson05_documents.jsonl",
        "backend/through_lesson05_corrections.jsonl",
        "build/THROUGH_LESSON05_MANIFEST.csv",
    ):
        if outputs.get(name) != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson05 evidence does not replay: {name}")
    return outputs, receipt, files


def validate_glossary() -> None:
    with GLOSSARY.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if reader.fieldnames != ["term_id", "en_US", "id_ID", "decision"]:
        raise RuntimeError("terminology glossary schema differs")
    expected_ids = [f"O006-TERM-{i:04d}" for i in range(1, EXPECTED_GLOSSARY_ROWS + 1)]
    if [row["term_id"] for row in rows] != expected_ids:
        raise RuntimeError("terminology glossary sequence differs through Lesson06")


def validate_normalization_receipt() -> None:
    receipt = json.loads(NORMALIZATION_RECEIPT.read_text("utf-8"))
    counts = receipt.get("counts")
    outputs = receipt.get("outputs")
    defects = receipt.get("source_defects")
    if (
        receipt.get("schema") != "o006.stat415.lesson06-normalization.v1"
        or receipt.get("status") != "normalized-source-ready-asset-closed-no-external-dependencies"
        or not isinstance(counts, dict)
        or counts.get("translation_segments") != EXPECTED_SEGMENTS
        or counts.get("structural_units") != EXPECTED_UNITS
        or counts.get("math_nodes") != EXPECTED_MATH
        or counts.get("assets") != EXPECTED_ASSETS
        or receipt.get("source_defect_count") != EXPECTED_CORRECTIONS
        or not isinstance(defects, list)
        or [row.get("defect_id") for row in defects]
        != [f"L06-D{i:03d}" for i in range(1, EXPECTED_CORRECTIONS + 1)]
        or not isinstance(outputs, dict)
        or not matches_identity(outputs.get("normalized"), NORMALIZED)
        or not matches_identity(outputs.get("asset"), AUTHORITY_ASSET)
        or not matches_identity(outputs.get("asset_closure"), ASSET_CLOSURE)
        or not matches_identity(outputs.get("asset_manifest"), ASSET_MANIFEST)
    ):
        raise RuntimeError("Lesson06 normalization receipt contract differs")


def validate_translation_receipt() -> None:
    validate_glossary()
    validate_normalization_receipt()
    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    if (
        receipt.get("schema") != "o006.stat415.lesson06-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("segment_count") != EXPECTED_SEGMENTS
        or receipt.get("translation_provenance") != PROVENANCE
        or receipt.get("identical_segments") != []
        or not matches_identity(receipt.get("merge_script"), MERGE_SCRIPT)
    ):
        raise RuntimeError("Lesson06 translation receipt contract differs")
    for field, path in (("translation_csv", TRANSLATIONS), ("bindings", BINDINGS)):
        if not matches_identity(receipt.get(field), path):
            raise RuntimeError(f"Lesson06 translation output identity differs: {field}")

    admitted_assets = receipt.get("asset_inputs")
    if not isinstance(admitted_assets, list):
        raise RuntimeError("Lesson06 translation asset-input evidence is missing")
    admitted_by_path = {
        str(row.get("path")): row for row in admitted_assets if isinstance(row, dict)
    }
    for path in (ASSET_CLOSURE, NORMALIZATION_RECEIPT):
        if not matches_identity(admitted_by_path.get(relative(path)), path):
            raise RuntimeError(f"Lesson06 admitted asset input differs: {relative(path)}")

    terminology_inputs = receipt.get("terminology_inputs")
    if not isinstance(terminology_inputs, list):
        raise RuntimeError("Lesson06 terminology-input evidence is missing")
    glossary_record = next(
        (
            row
            for row in terminology_inputs
            if isinstance(row, dict) and row.get("path") == relative(GLOSSARY)
        ),
        None,
    )
    if (
        not matches_identity(glossary_record, GLOSSARY)
        or glossary_record.get("rows") != EXPECTED_GLOSSARY_ROWS
        or receipt.get("terminology_rule")
        != "cumulative component glossary through O006-TERM-0094"
    ):
        raise RuntimeError("Lesson06 terminology receipt differs")


def load_asset_manifest() -> dict[str, str]:
    with ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    expected_fields = [
        "asset_id",
        "source_reference",
        "official_url",
        "local_path",
        "bytes",
        "sha256",
        "media_type",
        "width",
        "height",
        "license",
        "disposition",
    ]
    if reader.fieldnames != expected_fields or len(rows) != 1:
        raise RuntimeError("Lesson06 asset manifest contract differs")
    row = rows[0]
    expected = {
        "asset_id": f"{DOCUMENT_ID}-A0001",
        "source_reference": "assets/ci_1.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/ci_1.png",
        "local_path": relative(AUTHORITY_ASSET),
        "bytes": str(EXPECTED_ASSET_BYTES),
        "sha256": corrections.AUTHORITY_ASSET_SHA256,
        "media_type": "image/png",
        "width": "1334",
        "height": "640",
        "license": "CC BY-NC 4.0",
        "disposition": "freeze-authority-and-redistribute-with-page-attribution-and-change-notice",
    }
    if row != expected:
        raise RuntimeError("Lesson06 asset manifest row differs")
    return row


def load_asset_closure(
    main: Tag,
) -> tuple[dict[PurePosixPath, bytes], list[dict[str, object]]]:
    manifest_row = load_asset_manifest()
    audit = json.loads(ASSET_CLOSURE.read_text("utf-8"))
    closure = audit.get("closure")
    dependency_census = audit.get("dependency_census")
    asset = audit.get("asset")
    if (
        audit.get("schema") != "o006.stat415.lesson06-asset-closure.v1"
        or audit.get("status") != "same-origin-image-closed-no-external-dependencies"
        or audit.get("document_id") != DOCUMENT_ID
        or not isinstance(closure, dict)
        or closure.get("offline_reader_asset_gate_passed") is not True
        or closure.get("same_origin_image_bytes_complete") is not True
        or closure.get("unresolved_asset_bytes") != 0
        or not isinstance(dependency_census, dict)
        or dependency_census.get("images") != EXPECTED_ASSETS
        or sum(
            int(value)
            for key, value in dependency_census.items()
            if key != "images"
        )
        != 0
        or not isinstance(asset, dict)
        or asset.get("asset_id") != manifest_row["asset_id"]
        or asset.get("source_ref") != manifest_row["source_reference"]
        or asset.get("local_path") != manifest_row["local_path"]
        or asset.get("bytes") != EXPECTED_ASSET_BYTES
        or asset.get("sha256") != corrections.AUTHORITY_ASSET_SHA256
        or asset.get("img_occurrences") != 1
        or asset.get("lightbox_href_occurrences") != 1
    ):
        raise RuntimeError("Lesson06 asset-closure contract differs")

    payload = AUTHORITY_ASSET.read_bytes()
    if (
        AUTHORITY_ASSET != corrections.AUTHORITY_ASSET
        or len(payload) != corrections.AUTHORITY_ASSET_BYTES
        or len(payload) != EXPECTED_ASSET_BYTES
        or sha256(payload) != corrections.AUTHORITY_ASSET_SHA256
    ):
        raise RuntimeError("Lesson06 authority asset differs")

    asset_id = str(asset["asset_id"])
    source_ref = str(asset["source_ref"])
    images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
    containers = main.select(f'[data-o006-id="{DOCUMENT_ID}-U0051"]')
    notes = main.select('[data-o006-correction-id="O006-PSU-ADV-0115"]')
    if (
        len(images) != 1
        or len(containers) != 1
        or len(notes) != 1
        or images[0].get("src") != source_ref
        or images[0].get("alt") != corrections.FIGURE_ALT_TARGET
        or containers[0].get("alt") != corrections.FIGURE_ALT_TARGET
        or notes[0].get_text() != corrections.FIGURE_NOTE
        or notes[0].get("role") != "note"
    ):
        raise RuntimeError("Lesson06 corrected figure accessibility surface differs")

    image = images[0]
    source_style = str(image.get("style") or "")
    if source_style != "width:70.0%" or image.get("width") is not None:
        raise RuntimeError("Lesson06 figure width source surface differs")
    del image["style"]
    image["src"] = TARGET_ASSET.as_posix()

    lightboxes = main.select(f'a.lightbox[href="{source_ref}"]')
    if len(lightboxes) != 1:
        raise RuntimeError("Lesson06 figure lightbox topology differs")
    lightboxes[0]["href"] = TARGET_ASSET.as_posix()
    if image.get("style") is not None or image.get("src") != TARGET_ASSET.as_posix():
        raise RuntimeError("Lesson06 figure width or target route differs")

    evidence = [{
        "asset_id": asset_id,
        "source_path": relative(AUTHORITY_ASSET),
        "source_bytes": len(payload),
        "source_sha256": sha256(payload),
        "target_path": TARGET_ASSET.as_posix(),
        "target_bytes": len(payload),
        "target_sha256": sha256(payload),
        "target_is_byte_preserving": True,
        "source_inline_style": source_style,
        "target_inline_style": None,
        "target_alt_sha256": sha256(corrections.FIGURE_ALT_TARGET.encode("utf-8")),
        "correction_note_sha256": sha256(corrections.FIGURE_NOTE.encode("utf-8")),
    }]
    return {TARGET_ASSET: payload}, evidence


def load_lesson06() -> tuple[
    Tag,
    list[dict[str, str]],
    list[str],
    list[str],
    list[str],
    list[dict[str, object]],
    dict[PurePosixPath, bytes],
    list[dict[str, object]],
]:
    validate_translation_receipt()
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        expected_fields = [
            "segment_id",
            "document_id",
            "component_id",
            "section_id",
            "source_sha256",
            "source_text",
            "target_text",
            "status",
        ]
        if reader.fieldnames != expected_fields:
            raise RuntimeError("Lesson06 translation CSV schema differs")
        rows = list(reader)
    if len(rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson06 translation row count differs")
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson06 translation bindings")
    if len(bindings) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson06 translation binding count differs")

    soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("normalized Lesson06 main is missing")
    units = shared.stable_values(main, "data-o006-id")
    maths = shared.stable_values(main, "data-o006-math-id")
    if units != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson06 stable-unit sequence differs")
    if maths != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson06 math-ID sequence differs")
    if shared.native_id_duplicates(main):
        raise RuntimeError("Lesson06 normalized source has duplicate native IDs")

    source_math = [node.get_text() for node in main.select(".math")]
    nodes = shared.translatable_nodes(main)
    if len(nodes) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson06 translatable-node count differs")
    for ordinal, (row, binding, node) in enumerate(zip(rows, bindings, nodes), start=1):
        sid = f"{DOCUMENT_ID}-S{ordinal:04d}"
        source = str(node)
        target = row["target_text"]
        if (
            row["segment_id"] != sid
            or row["document_id"] != DOCUMENT_ID
            or row["component_id"] != COMPONENT_ID
            or row["source_text"] != source
            or row["source_sha256"] != sha256(source.encode("utf-8"))
            or row["status"] != "translated"
            or not target.strip()
            or "\ufffd" in target
        ):
            raise RuntimeError(f"Lesson06 translation binding differs: {sid}")
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": sid,
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": sha256(target.encode("utf-8")),
            "status": "translated",
        }
        if binding != expected_binding:
            raise RuntimeError(f"Lesson06 backend translation binding differs: {sid}")
        node.replace_with(NavigableString(target))

    correction_rows = corrections.apply_lesson06_corrections(main, rows)
    if (
        len(correction_rows) != EXPECTED_CORRECTIONS
        or [row["correction_id"] for row in correction_rows]
        != [f"O006-PSU-ADV-{i:04d}" for i in range(113, 123)]
        or [row["source_defect_id"] for row in correction_rows]
        != [f"L06-D{i:03d}" for i in range(1, 11)]
    ):
        raise RuntimeError("Lesson06 correction registry differs")
    reader_assets, asset_evidence = load_asset_closure(main)

    shared.normalize_lesson(main, "Lesson06.html")
    if shared.stable_values(main, "data-o006-id") != units:
        raise RuntimeError("Lesson06 target stable-unit topology differs")
    if shared.stable_values(main, "data-o006-math-id") != maths:
        raise RuntimeError("Lesson06 target math topology differs")
    if len(main.select(".math")) != EXPECTED_MATH:
        raise RuntimeError("Lesson06 target math count differs")
    if shared.native_id_duplicates(main):
        raise RuntimeError("Lesson06 target retains duplicate native IDs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson06 target retains an executable/embed dependency")
    proof = main.select(
        f'section.proof[data-o006-id="{DOCUMENT_ID}-U0067"]'
        '[data-o006-semantic-role="proof"][data-o006-correction-id="O006-PSU-ADV-0122"]'
    )
    if len(proof) != 1:
        raise RuntimeError("Lesson06 target proof semantics differ")
    return (
        main,
        rows,
        source_math,
        units,
        maths,
        correction_rows,
        reader_assets,
        asset_evidence,
    )


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lesson06 cumulative patch surface differs: {label}: {text.count(old)}")
    return text.replace(old, new, 1)


def patch_page(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            "partial: 7 of 14 documents complete; landing and Lessons 00–05",
            "partial: 8 of 14 documents complete; landing and Lessons 00–06",
            "metadata",
        ),
        (
            '<a href="Lesson05.html">Pelajaran 05</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson05.html">Pelajaran 05</a><a href="Lesson06.html">Pelajaran 06</a><a href="licenses/index.html">Lisensi</a>',
            "navigation",
        ),
        (
            "<strong>Edisi Bahasa Indonesia — 7 dari 14 dokumen.</strong>",
            "<strong>Edisi Bahasa Indonesia — 8 dari 14 dokumen.</strong>",
            "edition note",
        ),
        (
            "Laman utama serta Pelajaran 00–05 telah diterjemahkan sepenuhnya.",
            "Laman utama serta Pelajaran 00–06 telah diterjemahkan sepenuhnya.",
            "complete range",
        ),
        (
            "Pelajaran 06–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "Pelajaran 07–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "pending range",
        ),
        ("assets/reader-7of14.css", "assets/reader-8of14.css", "stylesheet"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, f"{filename} {label}")
    if filename == "index.html":
        old_anchor = (
            '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0107" '
            'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson06" '
            'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        )
        new_anchor = (
            '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0107" '
            'data-translation-status="complete" href="Lesson06.html">'
        )
        text = replace_once(text, old_anchor, new_anchor, "index Lesson06 route")
        text = replace_once(
            text,
            'alt="Ilustrasi Pelajaran 6: interval kepercayaan"',
            'alt="Ilustrasi Pelajaran 6: selang kepercayaan"',
            "index Lesson06 image alternative",
        )
        text = replace_once(
            text,
            'data-o006-id="O006-PSU-000-U0112">\nInterval Kepercayaan\n</h5>',
            'data-o006-id="O006-PSU-000-U0112">\nSelang Kepercayaan\n</h5>',
            "index Lesson06 title",
        )
        text = replace_once(
            text,
            'data-o006-id="O006-PSU-000-U0114">Interval Kepercayaan</div>',
            'data-o006-id="O006-PSU-000-U0114">Selang Kepercayaan</div>',
            "index Lesson06 category",
        )
    return text.encode("utf-8")


def patch_license(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<a href="../Lesson05.html">Pelajaran 05</a></nav>',
            '<a href="../Lesson05.html">Pelajaran 05</a><a href="../Lesson06.html">Pelajaran 06</a></nav>',
            "license navigation",
        ),
        ("../assets/reader-7of14.css", "../assets/reader-8of14.css", "license stylesheet"),
        (
            "serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, tujuh belas koreksi Lesson 03, tiga puluh lima koreksi Lesson 04, dan tiga puluh satu koreksi Lesson 05 yang dicatat secara terpisah.",
            "serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, tujuh belas koreksi Lesson 03, tiga puluh lima koreksi Lesson 04, tiga puluh satu koreksi Lesson 05, dan sepuluh koreksi Lesson 06 yang dicatat secara terpisah.",
            "license corrections",
        ),
        (
            "Dua iframe Kaltura pihak ketiga tidak dibundel dan diganti dengan penjelasan statis lengkap.",
            "Dua iframe Kaltura pihak ketiga tidak dibundel dan diganti dengan penjelasan statis lengkap. Satu PNG kurva normal baku Lesson 06 dibekukan dari URL resmi; byte sumber dipertahankan, teks alternatif dilengkapi, dan kekeliruan huruf kapital pada label nilai kritis dijelaskan dalam catatan koreksi turunan.",
            "license Lesson06 asset",
        ),
        (
            "laman utama serta Pelajaran 00–05 lengkap; Pelajaran 06–12 belum diterjemahkan.",
            "laman utama serta Pelajaran 00–06 lengkap; Pelajaran 07–12 belum diterjemahkan.",
            "license status",
        ),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text.encode("utf-8")


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in (
        "index.html",
        "Lesson00.html",
        "Lesson01.html",
        "Lesson02.html",
        "Lesson03.html",
        "Lesson04.html",
        "Lesson05.html",
        "Lesson06.html",
    ):
        soup = BeautifulSoup(reader[PurePosixPath(filename)], "html.parser")
        total += len(soup.select("[data-o006-id]"))
    return total


def compute() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    prior_outputs, prior_receipt, prior_files = replay_prior()
    reader = {
        PurePosixPath(name.removeprefix("build/html-id/")): payload
        for name, payload in prior_outputs.items()
        if name.startswith("build/html-id/")
    }
    if set(reader) != prior_files:
        raise RuntimeError("replayed Lesson05 reader inventory differs")
    css = reader.pop(PRIOR_CSS, None)
    if (
        css is None
        or len(css) != EXPECTED_PRIOR_CSS_BYTES
        or sha256(css) != EXPECTED_PRIOR_CSS_SHA256
    ):
        raise RuntimeError("Lesson05 responsive reader CSS differs")
    css += FIGURE_REFLOW_CSS
    reader[CURRENT_CSS] = css

    target_outputs: dict[str, bytes] = {}
    document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson05_documents.jsonl"], "Lesson05 documents"
    )
    if len(document_rows) != 7:
        raise RuntimeError("Lesson05 document backend count differs")
    by_filename = {
        PurePosixPath(str(row["target_path"])).name: row for row in document_rows
    }
    prior_filenames = (
        "index.html",
        "Lesson00.html",
        "Lesson01.html",
        "Lesson02.html",
        "Lesson03.html",
        "Lesson04.html",
        "Lesson05.html",
    )
    if set(by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson05 document backend filenames differ")
    for filename in prior_filenames:
        patched = patch_page(reader[PurePosixPath(filename)], filename)
        reader[PurePosixPath(filename)] = patched
        target_outputs[f"source/id-ID/{filename}"] = patched
        by_filename[filename]["target_bytes"] = len(patched)
        by_filename[filename]["target_sha256"] = sha256(patched)

    (
        main,
        rows,
        source_math,
        unit_ids,
        math_ids,
        fresh_corrections,
        lesson_assets,
        asset_evidence,
    ) = load_lesson06()
    base_lesson = prior.prior.prior.page_document(main, COMPONENT_ID, SOURCE_URL)
    lesson04_boundary = prior.prior.patch_page(base_lesson, "Lesson06.html")
    lesson05_boundary = prior.patch_page(lesson04_boundary, "Lesson06.html")
    lesson_payload = patch_page(lesson05_boundary, "Lesson06.html")
    reader[PurePosixPath("Lesson06.html")] = lesson_payload
    for path, payload in lesson_assets.items():
        if path in reader:
            raise RuntimeError(f"Lesson06 asset collides with prior reader: {path}")
        reader[path] = payload
    target_outputs["source/id-ID/Lesson06.html"] = lesson_payload
    target_math = [node.get_text() for node in main.select(".math")]

    document_rows = [by_filename[name] for name in prior_filenames]
    document_rows.append(
        shared.document_row(
            COMPONENT_ID,
            "Lesson06.html",
            DOCUMENT_ID,
            SOURCE_URL,
            source_math,
            target_math,
            lesson_payload,
            len(rows),
            len(unit_ids),
        )
    )
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative source-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math count differs")

    prior_corrections = parse_jsonl(
        prior_outputs["backend/through_lesson05_corrections.jsonl"], "Lesson05 corrections"
    )
    if len(prior_corrections) != 112 or len(fresh_corrections) != EXPECTED_CORRECTIONS:
        raise RuntimeError("cumulative correction partition differs")
    correction_rows = prior_corrections + fresh_corrections
    if (
        len(correction_rows) != EXPECTED_TOTAL_CORRECTIONS
        or [row["correction_id"] for row in correction_rows]
        != [f"O006-PSU-ADV-{i:04d}" for i in range(1, EXPECTED_TOTAL_CORRECTIONS + 1)]
    ):
        raise RuntimeError("cumulative correction registry differs")

    reader[PurePosixPath("licenses/index.html")] = patch_license(
        reader[PurePosixPath("licenses/index.html")]
    )
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError(f"cumulative reader file census differs: {len(reader)}")
    actual_target_units = target_unit_count(reader)
    if actual_target_units != EXPECTED_TARGET_UNITS:
        raise RuntimeError(f"cumulative reader unit census differs: {actual_target_units}")
    shared.validate_reader_links(reader)

    manifest_payload = first.manifest_payload(reader)
    documents_payload = first.canonical_jsonl(document_rows)
    corrections_payload = first.canonical_jsonl(correction_rows)
    outputs: dict[str, bytes] = dict(target_outputs)
    for path, payload in reader.items():
        outputs[f"build/html-id/{path.as_posix()}"] = payload
    outputs[relative(DOCUMENTS)] = documents_payload
    outputs[relative(CORRECTIONS)] = corrections_payload
    outputs[relative(MANIFEST)] = manifest_payload

    receipt: dict[str, object] = {
        "schema": "o006.stat415.through-lesson06-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": [
                "index",
                "Lesson00",
                "Lesson01",
                "Lesson02",
                "Lesson03",
                "Lesson04",
                "Lesson05",
                "Lesson06",
            ],
            "complete_count": 8,
            "corpus_document_count": 14,
            "next_document": "Lesson07",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "structural_units_target": EXPECTED_TARGET_UNITS,
        "math_nodes": {
            "index": 0,
            "Lesson00": 331,
            "Lesson01": 169,
            "Lesson02": 209,
            "Lesson03": 440,
            "Lesson04": 289,
            "Lesson05": 108,
            "Lesson06": EXPECTED_MATH,
            "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson05_count": len(prior_corrections),
            "lesson06_count": len(fresh_corrections),
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
        "lesson06_assets": {
            "count": len(lesson_assets),
            "bytes": sum(len(payload) for payload in lesson_assets.values()),
            "authority_slots": EXPECTED_ASSETS,
            "authority_bytes": EXPECTED_ASSET_BYTES,
            "byte_preserving_targets": EXPECTED_ASSETS,
            "inline_width_constraints_removed": EXPECTED_ASSETS,
            "inventory": asset_evidence,
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lesson05 PNGs": "fourteen same-origin authority images frozen under the official page notice; thirteen target slots retain authority bytes and one simulation plot is a disclosed seeded derivative",
            "Lesson05 Kaltura iframe": "not bundled; third-party derivative/redistribution grant not established; complete static fallbacks retained",
            "Lesson06 PNG": "one same-origin authority image frozen and redistributed byte-for-byte under the official page notice; target-only changes are limited to accessible HTML alternative text, a notation correction note, and responsive layout",
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
            "rule": "cumulative responsive media/code reflow remains active; Lesson06 Figure 6.1 has no inline width constraint and fills the available centered figure width",
        },
        "inputs": {
            "prior_build_receipt": identity(
                ROOT / "build" / "THROUGH_LESSON05_BUILD_RECEIPT.json"
            ),
            "normalization": identity(NORMALIZATION_RECEIPT),
            "translation": identity(TRANSLATION_RECEIPT),
            "asset_closure": identity(ASSET_CLOSURE),
            "asset_manifest": identity(ASSET_MANIFEST),
            "authority_asset": identity(AUTHORITY_ASSET),
            "glossary": identity(GLOSSARY),
            "builder": identity(Path(__file__)),
            "correction_module": identity(ROOT / "scripts" / "lesson06_corrections.py"),
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
                raise RuntimeError(f"Lesson06 cumulative output differs: {relative_path}")
        actual_reader = shared.current_reader_files()
        if actual_reader != expected_reader:
            raise RuntimeError(
                "Lesson06 reader inventory differs: "
                f"extra={sorted(actual_reader - expected_reader)} "
                f"missing={sorted(expected_reader - actual_reader)}"
            )
        state = "verified"
    print(
        json.dumps(
            {
                "mode": state,
                "documents": receipt["coverage"]["complete_count"],
                "segments": receipt["translation_segments"],
                "source_units": receipt["structural_units_normalized"],
                "target_units": receipt["structural_units_target"],
                "math_nodes": receipt["math_nodes"]["total"],
                "corrections": receipt["corrections"]["count"],
                "lesson06_assets": receipt["lesson06_assets"]["count"],
                "reader_files": receipt["reader"]["files"],
                "receipt_sha256": sha256(outputs[relative(RECEIPT)]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
