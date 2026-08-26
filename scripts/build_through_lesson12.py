#!/usr/bin/env python3
"""Build the complete cumulative id-ID STAT 415 reader through Lesson 12."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, Tag

import build_through_lesson11 as prior
import materialize_lesson12_translation as materializer


base = prior.base
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson12.html"
TARGET = ROOT / "source" / "id-ID" / "Lesson12.html"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson12_translation.csv"
BINDINGS = ROOT / "backend" / "lesson12_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON12_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON12_NORMALIZATION_RECEIPT.json"
MATERIALIZATION_RECEIPT = ROOT / "build" / "LESSON12_MATERIALIZATION_RECEIPT.json"
TARGET_CORRECTIONS = ROOT / "backend" / "lesson12_target_corrections.jsonl"
NATIVE_ID_MAP = ROOT / "backend" / "lesson12_target_native_id_map.jsonl"
MATERIALIZER = ROOT / "scripts" / "materialize_lesson12_translation.py"
CORRECTION_MODULE = ROOT / "scripts" / "lesson12_corrections.py"
ASSET_FREEZE_RECEIPT = ROOT / "authority" / "LESSON12_ASSET_FREEZE_RECEIPT.json"
ASSET_MANIFEST = ROOT / "authority" / "LESSON12_ASSET_MANIFEST.csv"
VIDEO_PROVENANCE = ROOT / "authority" / "LESSON12_VIDEO_PROVENANCE.csv"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
PRIOR_RECEIPT = ROOT / "build" / "THROUGH_LESSON11_BUILD_RECEIPT.json"
DOCUMENTS = ROOT / "backend" / "through_lesson12_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson12_corrections.jsonl"
MANIFEST = ROOT / "build" / "THROUGH_LESSON12_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON12_BUILD_RECEIPT.json"

DOCUMENT_ID = "O006-PSU-013"
COMPONENT_ID = "Lesson12"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson12.html"
SOURCE_URL_LEGACY = "https://online.stat.psu.edu/stat415/Lesson12"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_SEGMENTS = 580
EXPECTED_UNITS = 846
EXPECTED_MATH = 352
EXPECTED_ASSETS = 9
EXPECTED_ASSET_OCCURRENCES = 10
EXPECTED_ASSET_BYTES = 233_075
EXPECTED_CORRECTIONS = 24
EXPECTED_TOTAL_SEGMENTS = 4_932
EXPECTED_TOTAL_UNITS = 6_510
EXPECTED_TARGET_UNITS = 6_498
EXPECTED_TOTAL_MATH = 3_156
EXPECTED_TOTAL_CORRECTIONS = 242
EXPECTED_READER_FILES = 106
EXPECTED_GLOSSARY_ROWS = 192
EXPECTED_GLOSSARY_BYTES = 20_340
EXPECTED_GLOSSARY_SHA256 = "554dcbfb5161df6f0eb86027822eabbf4fae9179bb152947a8ad6c196cb34b05"
EXPECTED_PRIOR_RECEIPT_BYTES = 8_116
EXPECTED_PRIOR_RECEIPT_SHA256 = "421d60b88849d9f800d4dc1691d28e59f01c86ac4d892c01f797d7114ee4b98d"
PRIOR_CSS = PurePosixPath("assets/reader-13of14.css")
CURRENT_CSS = PurePosixPath("assets/reader-14of14.css")
EXPECTED_PRIOR_CSS_BYTES = 8_655
EXPECTED_PRIOR_CSS_SHA256 = "179c699619bc159953a82d30ccf63a88919adf836209d39ad2a798ab1b924864"

LESSON12_CSS = b"""

/* Lesson 12: complete offline regression surfaces and additive repair notes. */
main#quarto-document-content .target-only-note,
main#quarto-document-content .target-only-proof,
main#quarto-document-content .target-only-reproducibility,
main#quarto-document-content .offline-video-equivalent,
main#quarto-document-content .component-provenance {
  width: 100%;
  max-width: 100%;
  margin: 1rem 0;
  padding: 0.85rem 1rem;
  overflow-wrap: anywhere;
  background: #f7f9fb;
  border: 1px solid #cfd8e1;
  border-radius: 0.4rem;
}

main#quarto-document-content .target-only-note {
  border-inline-start: 0.35rem solid var(--brand);
}

main#quarto-document-content .target-derived-math {
  max-width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
}

main#quarto-document-content table.reader-responsive-table {
  display: block;
  width: max-content;
  max-width: 100%;
  overflow-x: auto;
  margin-inline: auto;
}
"""


def unreachable_correction_adapter(
    _main: Tag, _rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    raise RuntimeError("Lesson12 uses its independently replayed materialization boundary")


LESSON = base.Lesson(
    12,
    DOCUMENT_ID,
    EXPECTED_SEGMENTS,
    EXPECTED_UNITS,
    EXPECTED_MATH,
    EXPECTED_ASSETS,
    EXPECTED_CORRECTIONS,
    219,
    unreachable_correction_adapter,
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def identity(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": relative(path), "bytes": len(payload), "sha256": sha256(payload)}


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


def admitted_glossary_identity() -> dict[str, object]:
    payload = GLOSSARY.read_bytes()
    if len(payload) != EXPECTED_GLOSSARY_BYTES or sha256(payload) != EXPECTED_GLOSSARY_SHA256:
        raise RuntimeError("Lesson12 admitted glossary identity differs")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
    if (
        len(rows) != EXPECTED_GLOSSARY_ROWS
        or [row.get("term_id") for row in rows]
        != [f"O006-TERM-{ordinal:04d}" for ordinal in range(1, EXPECTED_GLOSSARY_ROWS + 1)]
    ):
        raise RuntimeError("Lesson12 admitted glossary sequence differs")
    return {
        "path": relative(GLOSSARY),
        "bytes": len(payload),
        "sha256": sha256(payload),
        "rows": len(rows),
        "scope": "immutable cumulative glossary through Lesson12",
    }


def replay_prior() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    outputs, replayed_receipt, files = prior.compute()
    if replayed_receipt.get("coverage", {}).get("complete_count") != 13 or len(files) != 96:
        raise RuntimeError("replayed Lesson11 boundary differs")
    for name in (
        "backend/through_lesson11_documents.jsonl",
        "backend/through_lesson11_corrections.jsonl",
        "build/THROUGH_LESSON11_MANIFEST.csv",
    ):
        if outputs.get(name) != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson11 evidence does not replay: {name}")
    frozen_payload = PRIOR_RECEIPT.read_bytes()
    if (
        len(frozen_payload) != EXPECTED_PRIOR_RECEIPT_BYTES
        or sha256(frozen_payload) != EXPECTED_PRIOR_RECEIPT_SHA256
    ):
        raise RuntimeError("frozen Lesson11 build receipt differs")
    frozen_receipt = json.loads(frozen_payload.decode("utf-8"))
    if frozen_receipt.get("coverage", {}).get("complete_count") != 13:
        raise RuntimeError("frozen Lesson11 coverage differs")
    return outputs, frozen_receipt, files


def replay_materialization() -> tuple[
    bytes,
    dict[str, object],
    list[dict[str, object]],
    list[dict[str, object]],
]:
    outputs = materializer.compute()
    for relative_path, payload in outputs.items():
        path = ROOT / relative_path
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"Lesson12 materialization does not replay: {relative_path}")
    target_payload = outputs[relative(TARGET)]
    receipt_payload = outputs[relative(MATERIALIZATION_RECEIPT)]
    receipt = json.loads(receipt_payload.decode("utf-8"))
    counts = receipt.get("counts")
    validation = receipt.get("validation")
    if (
        receipt.get("schema") != "o006.stat415.lesson12-materialization.v1"
        or receipt.get("status") != "pass"
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("component_id") != COMPONENT_ID
        or receipt.get("translation_provenance") != PROVENANCE
        or not isinstance(counts, dict)
        or counts.get("translation_segments") != EXPECTED_SEGMENTS
        or counts.get("stable_source_units") != EXPECTED_UNITS
        or counts.get("stable_source_math") != EXPECTED_MATH
        or counts.get("registered_target_corrections") != EXPECTED_CORRECTIONS
        or counts.get("unique_frozen_images") != EXPECTED_ASSETS
        or counts.get("image_occurrences") != EXPECTED_ASSET_OCCURRENCES
        or counts.get("semantic_tables") != 6
        or counts.get("table_captions") != 6
        or counts.get("offline_video_equivalents") != 3
        or counts.get("external_video_runtimes") != 0
        or not isinstance(validation, dict)
        or validation.get("authority_unchanged") is not True
        or validation.get("source_segment_bindings_exact") is not True
        or validation.get("source_stable_ids_preserved") is not True
        or validation.get("source_math_ids_preserved") is not True
        or validation.get("unregistered_source_math_unchanged") is not True
        or validation.get("all_registered_repairs_dispositioned") is not True
        or validation.get("video_bytes_redistributed") is not False
        or validation.get("external_video_runtime_removed") is not True
        or validation.get("frozen_images_byte_bound") is not True
        or validation.get("images_centered_responsive_and_dimensioned") is not True
        or validation.get("tables_captioned_and_scoped") is not True
        or validation.get("duplicate_target_ids_removed_with_reversible_map") is not True
        or validation.get("target_id_references_resolve") is not True
        or validation.get("target_local_paths_resolve") is not True
        or validation.get("numerical_recalculation_reproducible") is not True
        or validation.get("source_credit_license_and_change_notice_visible") is not True
    ):
        raise RuntimeError("Lesson12 materialization receipt differs")
    corrections = parse_jsonl(outputs[relative(TARGET_CORRECTIONS)], "Lesson12 corrections")
    native_map = parse_jsonl(outputs[relative(NATIVE_ID_MAP)], "Lesson12 native-ID map")
    if (
        [row.get("correction_id") for row in corrections]
        != [f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(219, 243)]
        or [row.get("source_defect_id") for row in corrections]
        != [f"L12-D{ordinal:03d}" for ordinal in range(1, 25)]
        or len(native_map) != 16
    ):
        raise RuntimeError("Lesson12 materialized correction/native-ID evidence differs")
    return target_payload, receipt, corrections, native_map


def load_assets(main: Tag) -> tuple[dict[PurePosixPath, bytes], list[dict[str, object]]]:
    freeze = json.loads(ASSET_FREEZE_RECEIPT.read_text("utf-8"))
    if (
        freeze.get("schema") != "o006.stat415.lesson12-asset-freeze.v1"
        or freeze.get("status") != "pass"
        or freeze.get("asset_count") != EXPECTED_ASSETS
        or freeze.get("asset_occurrences") != EXPECTED_ASSET_OCCURRENCES
        or freeze.get("total_bytes") != EXPECTED_ASSET_BYTES
        or freeze.get("external_video_boundary", {}).get("binary_bytes_downloaded") is not False
        or freeze.get("external_video_boundary", {}).get("binary_bytes_redistributed") is not False
        or freeze.get("external_video_boundary", {}).get("count") != 3
        or not matches_identity(freeze.get("manifest"), ASSET_MANIFEST)
    ):
        raise RuntimeError("Lesson12 asset-freeze boundary differs")
    with ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if (
        len(rows) != EXPECTED_ASSETS
        or [row.get("asset_id") for row in rows]
        != [f"{DOCUMENT_ID}-A{ordinal:04d}" for ordinal in range(1, 10)]
    ):
        raise RuntimeError("Lesson12 asset-manifest order differs")
    reader_assets: dict[PurePosixPath, bytes] = {}
    evidence: list[dict[str, object]] = []
    occurrence_total = 0
    for row in rows:
        asset_id = str(row["asset_id"])
        authority = ROOT / str(row["local_path"])
        payload = authority.read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"Lesson12 frozen asset differs: {asset_id}")
        images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
        expected_occurrences = 2 if asset_id == f"{DOCUMENT_ID}-A0006" else 1
        if len(images) != expected_occurrences:
            raise RuntimeError(f"Lesson12 asset occurrence count differs: {asset_id}")
        target = PurePosixPath("assets/lesson12") / PurePosixPath(str(row["source_reference"]))
        for image in images:
            if len(str(image.get("alt") or "").strip()) < 20:
                raise RuntimeError(f"Lesson12 image alternative is incomplete: {asset_id}")
            image["src"] = target.as_posix()
            anchor = image.find_parent("a")
            if isinstance(anchor, Tag) and "lightbox" in (anchor.get("class") or []):
                anchor["href"] = target.as_posix()
        if target in reader_assets:
            raise RuntimeError(f"Lesson12 target asset collision: {target}")
        reader_assets[target] = payload
        occurrence_total += len(images)
        evidence.append({
            "asset_id": asset_id,
            "official_url": row["official_url"],
            "media_type": row["media_type"],
            "source_path": relative(authority),
            "source_bytes": len(payload),
            "source_sha256": sha256(payload),
            "target_path": target.as_posix(),
            "target_bytes": len(payload),
            "target_sha256": sha256(payload),
            "target_is_byte_preserving": True,
            "occurrences": len(images),
            "width": int(row["width"]),
            "height": int(row["height"]),
            "license": row["license"],
        })
    if occurrence_total != EXPECTED_ASSET_OCCURRENCES or sum(map(len, reader_assets.values())) != EXPECTED_ASSET_BYTES:
        raise RuntimeError("Lesson12 reader asset census differs")
    return reader_assets, evidence


def load_lesson12() -> dict[str, object]:
    target_payload, materialization, correction_rows, native_map = replay_materialization()
    target_soup = BeautifulSoup(target_payload, "html.parser")
    main = target_soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson12 materialized instructional main is missing")
    units = base.shared.stable_values(main, "data-o006-id")
    maths = base.shared.stable_values(main, "data-o006-math-id")
    if units != [f"{DOCUMENT_ID}-U{ordinal:04d}" for ordinal in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson12 materialized stable-unit sequence differs")
    if maths != [f"{DOCUMENT_ID}-M{ordinal:04d}" for ordinal in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson12 materialized math-ID sequence differs")
    if (
        len(main.select(".math")) != EXPECTED_MATH
        or len(main.select("[data-o006-derived-math-id]")) != 8
        or len(main.select("table")) != 6
        or len(main.select("table caption")) != 6
        or len(main.select(".offline-video-equivalent")) != 3
        or len(main.select("img")) != EXPECTED_ASSET_OCCURRENCES
        or main.select("iframe, object, embed, video, audio, source, script")
        or base.shared.native_id_duplicates(main)
    ):
        raise RuntimeError("Lesson12 materialized semantic closure differs")
    normalized_soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    normalized_main = normalized_soup.select_one("main#quarto-document-content")
    if normalized_main is None:
        raise RuntimeError("Lesson12 normalized instructional main is missing")
    source_math = [node.get_text() for node in normalized_main.select(".math")]
    if len(source_math) != EXPECTED_MATH:
        raise RuntimeError("Lesson12 normalized source-math count differs")
    base.shared.normalize_lesson(main, "Lesson12.html")
    if base.shared.stable_values(main, "data-o006-id") != units:
        raise RuntimeError("Lesson12 reader normalization changed stable units")
    if base.shared.stable_values(main, "data-o006-math-id") != maths:
        raise RuntimeError("Lesson12 reader normalization changed source-math identities")
    assets, asset_evidence = load_assets(main)
    return {
        "main": main,
        "target_payload": target_payload,
        "source_math": source_math,
        "target_math": [node.get_text() for node in main.select(".math")],
        "units": units,
        "corrections": correction_rows,
        "native_map": native_map,
        "materialization": materialization,
        "assets": assets,
        "asset_evidence": asset_evidence,
    }


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lesson12 cumulative patch differs: {label}: {text.count(old)}")
    return text.replace(old, new, 1)


def patch_page(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            "partial: 13 of 14 documents complete; landing and Lessons 00–11",
            "complete: 14 of 14 documents; landing and Lessons 00–12",
            "metadata",
        ),
        (
            '<a href="Lesson11.html">Pelajaran 11</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson11.html">Pelajaran 11</a><a href="Lesson12.html">Pelajaran 12</a><a href="licenses/index.html">Lisensi</a>',
            "navigation",
        ),
        (
            "<strong>Edisi Bahasa Indonesia — 13 dari 14 dokumen.</strong>",
            "<strong>Edisi Bahasa Indonesia — 14 dari 14 dokumen.</strong>",
            "edition note",
        ),
        (
            "Laman utama serta Pelajaran 00–11 telah diterjemahkan sepenuhnya.",
            "Laman utama serta Pelajaran 00–12 telah diterjemahkan sepenuhnya.",
            "complete range",
        ),
        (
            "Pelajaran 12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "Seluruh empat belas dokumen dalam batas sumber edisi ini kini lengkap.",
            "completed pending range",
        ),
        ("assets/reader-13of14.css", "assets/reader-14of14.css", "stylesheet"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, f"{filename} {label}")
    if filename == "index.html":
        old_anchor = (
            '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0187" '
            'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson12" '
            'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        )
        new_anchor = (
            '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0187" '
            'data-translation-status="complete" href="Lesson12.html">'
        )
        text = replace_once(text, old_anchor, new_anchor, "index Lesson12 route")
    return text.encode("utf-8")


def patch_license(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<a href="../Lesson11.html">Pelajaran 11</a></nav>',
            '<a href="../Lesson11.html">Pelajaran 11</a><a href="../Lesson12.html">Pelajaran 12</a></nav>',
            "license navigation",
        ),
        ("../assets/reader-13of14.css", "../assets/reader-14of14.css", "license stylesheet"),
        (
            "dua puluh delapan koreksi Lesson 10, dan dua puluh koreksi Lesson 11 yang dicatat secara terpisah.",
            "dua puluh delapan koreksi Lesson 10, dua puluh koreksi Lesson 11, dan dua puluh empat koreksi atau disposisi Lesson 12 yang dicatat secara terpisah.",
            "license correction census",
        ),
        (
            "Satu PNG potret Lesson 11 dibekukan byte demi byte dari URL resmi; turunan HTML melengkapi teks alternatif, keterangan gambar, semantik tabel, pengungkapan lingkungan komputasi, dan tata letak responsif.",
            "Satu PNG potret Lesson 11 dibekukan byte demi byte dari URL resmi; turunan HTML melengkapi teks alternatif, keterangan gambar, semantik tabel, pengungkapan lingkungan komputasi, dan tata letak responsif. Sembilan PNG unik dalam sepuluh kemunculan Lesson 12 dibekukan byte demi byte dari URL resmi; tiga iframe video eksternal tidak dibundel dan diganti dengan padanan teks luring lengkap sambil mempertahankan tautan provenance.",
            "license Lesson12 assets and video disposition",
        ),
        (
            "laman utama serta Pelajaran 00–11 lengkap; Pelajaran 12 belum diterjemahkan.",
            "laman utama serta Pelajaran 00–12 lengkap; seluruh empat belas dokumen dalam batas sumber edisi ini telah diterjemahkan.",
            "license final status",
        ),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text.encode("utf-8")


def canonical_page_payload(path: Path, generated: bytes) -> bytes:
    if not path.is_file():
        return generated

    def signature(payload: bytes) -> tuple[object, ...]:
        soup = BeautifulSoup(payload, "html.parser")
        return (
            [(node.name, node.get("data-o006-id")) for node in soup.select("[data-o006-id]")],
            [node.get_text() for node in soup.select(".math")],
            [node.get_text() for node in soup.select("pre, code")],
            [node.get("src") for node in soup.select("img")],
            [node.get("href") for node in soup.select("a[href]")],
            [node.get_text(" ", strip=True) for node in soup.select(".edition-note")],
        )

    frozen = path.read_bytes()
    if signature(frozen) != signature(generated):
        return generated
    if b"assets/reader-14of14.css" not in frozen:
        return generated
    return frozen


def make_page(main: Tag) -> bytes:
    payload = base.make_page(main, LESSON)
    payload = prior.prior.patch_page(payload, "Lesson12.html")
    payload = prior.patch_page(payload, "Lesson12.html")
    payload = patch_page(payload, "Lesson12.html")
    text = payload.decode("utf-8")
    legacy_occurrences = text.count(SOURCE_URL_LEGACY + '"')
    if legacy_occurrences != 2:
        raise RuntimeError(f"Lesson12 reader source-URL surface differs: {legacy_occurrences}")
    return text.replace(SOURCE_URL_LEGACY + '"', SOURCE_URL + '"').encode("utf-8")


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in ("index.html", *[f"Lesson{ordinal:02d}.html" for ordinal in range(13)]):
        soup = BeautifulSoup(reader[PurePosixPath(filename)], "html.parser")
        total += len(soup.select("[data-o006-id]"))
    return total


def compute() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    glossary_input = admitted_glossary_identity()
    prior_outputs, prior_receipt, prior_files = replay_prior()
    reader = {
        PurePosixPath(name.removeprefix("build/html-id/")): payload
        for name, payload in prior_outputs.items()
        if name.startswith("build/html-id/")
    }
    if set(reader) != prior_files:
        raise RuntimeError("replayed Lesson11 reader inventory differs")
    css = reader.pop(PRIOR_CSS, None)
    if (
        css is None
        or len(css) != EXPECTED_PRIOR_CSS_BYTES
        or sha256(css) != EXPECTED_PRIOR_CSS_SHA256
    ):
        raise RuntimeError("Lesson11 responsive reader CSS differs")
    old_css_label = "Lessons 07–11".encode("utf-8")
    if css.count(old_css_label) != 1:
        raise RuntimeError("Lesson11 cumulative CSS label differs")
    css = css.replace(old_css_label, "Lessons 07–12".encode("utf-8"), 1) + LESSON12_CSS
    reader[CURRENT_CSS] = css

    target_outputs: dict[str, bytes] = {}
    document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson11_documents.jsonl"], "Lesson11 documents"
    )
    prior_filenames = ("index.html", *[f"Lesson{ordinal:02d}.html" for ordinal in range(12)])
    by_filename = {PurePosixPath(str(row["target_path"])).name: row for row in document_rows}
    if len(document_rows) != 13 or set(by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson11 document backend boundary differs")
    for filename in prior_filenames:
        payload = patch_page(reader[PurePosixPath(filename)], filename)
        payload = canonical_page_payload(ROOT / "source" / "id-ID" / filename, payload)
        reader[PurePosixPath(filename)] = payload
        target_outputs[f"source/id-ID/{filename}"] = payload
        by_filename[filename]["target_bytes"] = len(payload)
        by_filename[filename]["target_sha256"] = sha256(payload)
    document_rows = [by_filename[name] for name in prior_filenames]

    loaded = load_lesson12()
    main = loaded["main"]
    assert isinstance(main, Tag)
    lesson_payload = make_page(main)
    reader[PurePosixPath("Lesson12.html")] = lesson_payload
    lesson_assets = loaded["assets"]
    assert isinstance(lesson_assets, dict)
    for path, payload in lesson_assets.items():
        if path in reader:
            raise RuntimeError(f"Lesson12 asset collides with prior reader: {path}")
        reader[path] = payload

    source_math = loaded["source_math"]
    target_math = loaded["target_math"]
    units = loaded["units"]
    target_payload = loaded["target_payload"]
    assert isinstance(source_math, list) and isinstance(target_math, list)
    assert isinstance(units, list) and isinstance(target_payload, bytes)
    document_rows.append(base.shared.document_row(
        COMPONENT_ID,
        "Lesson12.html",
        DOCUMENT_ID,
        SOURCE_URL,
        source_math,
        target_math,
        target_payload,
        EXPECTED_SEGMENTS,
        len(units),
    ))

    prior_corrections = parse_jsonl(
        prior_outputs["backend/through_lesson11_corrections.jsonl"], "Lesson11 corrections"
    )
    fresh_corrections = loaded["corrections"]
    assert isinstance(fresh_corrections, list)
    if len(prior_corrections) != 218 or len(fresh_corrections) != EXPECTED_CORRECTIONS:
        raise RuntimeError("Lesson12 cumulative correction partition differs")
    correction_rows = prior_corrections + fresh_corrections

    license_path = PurePosixPath("licenses/index.html")
    reader[license_path] = patch_license(reader[license_path])
    if len(document_rows) != 14:
        raise RuntimeError("Lesson12 cumulative document count differs")
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("Lesson12 cumulative segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("Lesson12 cumulative source-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("Lesson12 cumulative math count differs")
    if (
        len(correction_rows) != EXPECTED_TOTAL_CORRECTIONS
        or [row.get("correction_id") for row in correction_rows]
        != [f"O006-PSU-ADV-{ordinal:04d}" for ordinal in range(1, EXPECTED_TOTAL_CORRECTIONS + 1)]
    ):
        raise RuntimeError("Lesson12 cumulative correction registry differs")
    asset_evidence = loaded["asset_evidence"]
    assert isinstance(asset_evidence, list)
    if (
        len(asset_evidence) != EXPECTED_ASSETS
        or sum(int(row["occurrences"]) for row in asset_evidence) != EXPECTED_ASSET_OCCURRENCES
        or sum(int(row["source_bytes"]) for row in asset_evidence) != EXPECTED_ASSET_BYTES
    ):
        raise RuntimeError("Lesson12 asset evidence differs")
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError(f"Lesson12 reader file census differs: {len(reader)}")
    if target_unit_count(reader) != EXPECTED_TARGET_UNITS:
        raise RuntimeError("Lesson12 cumulative target-unit count differs")
    base.shared.validate_reader_links(reader)

    documents_payload = base.first.canonical_jsonl(document_rows)
    corrections_payload = base.first.canonical_jsonl(correction_rows)
    manifest_payload = base.first.manifest_payload(reader)
    outputs: dict[str, bytes] = dict(target_outputs)
    for path, payload in reader.items():
        outputs[f"build/html-id/{path.as_posix()}"] = payload
    outputs[relative(DOCUMENTS)] = documents_payload
    outputs[relative(CORRECTIONS)] = corrections_payload
    outputs[relative(MANIFEST)] = manifest_payload
    materialization = loaded["materialization"]
    native_map = loaded["native_map"]
    assert isinstance(materialization, dict) and isinstance(native_map, list)
    receipt: dict[str, object] = {
        "schema": "o006.stat415.through-lesson12-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", *[f"Lesson{ordinal:02d}" for ordinal in range(13)]],
            "complete_count": 14,
            "corpus_document_count": 14,
            "pending_documents": [],
            "next_document": None,
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "structural_units_target": EXPECTED_TARGET_UNITS,
        "math_nodes": {
            **dict(prior_receipt["math_nodes"]),
            "Lesson12": EXPECTED_MATH,
            "total": EXPECTED_TOTAL_MATH,
        },
        "additive_derived_math_nodes": len(main.select("[data-o006-derived-math-id]")),
        "corrections": {
            "count": len(correction_rows),
            "through_lesson11_count": len(prior_corrections),
            "lesson12_count": len(fresh_corrections),
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
            "count": len(asset_evidence),
            "occurrences": sum(int(row["occurrences"]) for row in asset_evidence),
            "bytes": sum(int(row["source_bytes"]) for row in asset_evidence),
            "all_byte_preserving": all(row["target_is_byte_preserving"] for row in asset_evidence),
            "inventory": asset_evidence,
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lesson12 assets": "nine same-origin PNG files in ten occurrences frozen and redistributed byte-for-byte under the official page notice; component exceptions remain binding",
            "Lesson12 external videos": "three external iframe runtimes removed; no video bytes downloaded or redistributed; source links retained beside complete offline textual equivalents",
            "MathJax 3.1.2": "Apache-2.0",
            "aggregate_uniform_relicense": False,
        },
        "offline": {
            "external_runtime_requests": 0,
            "analytics": False,
            "cookies": False,
            "local_mathjax": True,
            "third_party_iframes": 0,
            "offline_video_equivalents": 3,
            "video_bytes_redistributed": False,
        },
        "runtime_closure": prior_receipt["runtime_closure"],
        "layout": {
            "reader_css_path": CURRENT_CSS.as_posix(),
            "reader_css_bytes": len(css),
            "reader_css_sha256": sha256(css),
            "lesson12_full_width_image_occurrences": EXPECTED_ASSET_OCCURRENCES,
            "lesson12_responsive_tables": 6,
            "rule": "all cumulative reader figures fill and center within the reader width; tables, code, source mathematics, and additive derivations reflow without page overflow",
        },
        "materialization": {
            "receipt": identity(MATERIALIZATION_RECEIPT),
            "target": identity(TARGET),
            "target_corrections": identity(TARGET_CORRECTIONS),
            "native_id_map": {**identity(NATIVE_ID_MAP), "records": len(native_map)},
            "authority_unchanged": materialization.get("validation", {}).get("authority_unchanged"),
        },
        "inputs": {
            "prior_build_receipt": identity(PRIOR_RECEIPT),
            "normalization": identity(NORMALIZATION_RECEIPT),
            "translation": identity(TRANSLATION_RECEIPT),
            "materialization": identity(MATERIALIZATION_RECEIPT),
            "asset_freeze_receipt": identity(ASSET_FREEZE_RECEIPT),
            "asset_manifest": identity(ASSET_MANIFEST),
            "video_provenance": identity(VIDEO_PROVENANCE),
            "glossary": glossary_input,
            "builder": identity(Path(__file__)),
            "materializer": identity(MATERIALIZER),
            "correction_module": identity(CORRECTION_MODULE),
            "translation_csv": identity(TRANSLATIONS),
            "translation_bindings": identity(BINDINGS),
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
    outputs[relative(RECEIPT)] = base.first.canonical_json(receipt)
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
                raise RuntimeError(f"Lesson12 cumulative output differs: {relative_path}")
        if base.shared.current_reader_files() != expected_reader:
            raise RuntimeError("Lesson12 reader inventory differs")
        state = "verified"
    print(json.dumps({
        "mode": state,
        "documents": 14,
        "segments": receipt["translation_segments"],
        "source_units": receipt["structural_units_normalized"],
        "target_units": receipt["structural_units_target"],
        "math_nodes": receipt["math_nodes"]["total"],
        "corrections": receipt["corrections"]["count"],
        "assets": receipt["new_assets"]["count"],
        "asset_occurrences": receipt["new_assets"]["occurrences"],
        "reader_files": receipt["reader"]["files"],
        "receipt_sha256": sha256(outputs[relative(RECEIPT)]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
