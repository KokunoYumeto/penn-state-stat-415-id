#!/usr/bin/env python3
"""Build the cumulative id-ID reader through STAT 415 Lesson 11."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_through_lesson10 as prior
import lesson11_corrections as corrections11

base = prior.prior


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson11.html"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson11_translation.csv"
BINDINGS = ROOT / "backend" / "lesson11_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON11_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON11_NORMALIZATION_RECEIPT.json"
MERGE_SCRIPT = ROOT / "scripts" / "merge_lesson11_translations.py"
CORRECTION_MODULE = ROOT / "scripts" / "lesson11_corrections.py"
ASSET_FREEZE_RECEIPT = ROOT / "authority" / "LESSON11_ASSET_FREEZE_RECEIPT.json"
ASSET_MANIFEST = ROOT / "authority" / "LESSON11_ASSET_MANIFEST.csv"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
PRIOR_RECEIPT = ROOT / "build" / "THROUGH_LESSON10_BUILD_RECEIPT.json"
DOCUMENTS = ROOT / "backend" / "through_lesson11_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson11_corrections.jsonl"
MANIFEST = ROOT / "build" / "THROUGH_LESSON11_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON11_BUILD_RECEIPT.json"

DOCUMENT_ID = "O006-PSU-012"
COMPONENT_ID = "Lesson11"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson11.html"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_SEGMENTS = 354
EXPECTED_UNITS = 264
EXPECTED_MATH = 264
EXPECTED_ASSETS = 1
EXPECTED_ASSET_BYTES = 142_195
EXPECTED_CORRECTIONS = 20
EXPECTED_TOTAL_SEGMENTS = 4_352
EXPECTED_TOTAL_UNITS = 5_664
EXPECTED_TARGET_UNITS = 5_652
EXPECTED_TOTAL_MATH = 2_804
EXPECTED_TOTAL_CORRECTIONS = 218
EXPECTED_READER_FILES = 96
EXPECTED_GLOSSARY_ROWS = 168
EXPECTED_GLOSSARY_BYTES = 17_727
EXPECTED_GLOSSARY_SHA256 = (
    "1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65"
)
EXPECTED_PRIOR_RECEIPT_BYTES = 24_978
EXPECTED_PRIOR_RECEIPT_SHA256 = (
    "0f440e56bf71e172815ac0933e752e3f3f12383573e4c501db8fe5aa1922a520"
)
PRIOR_CSS = PurePosixPath("assets/reader-12of14.css")
CURRENT_CSS = PurePosixPath("assets/reader-13of14.css")
EXPECTED_PRIOR_CSS_BYTES = 8_655
EXPECTED_PRIOR_CSS_SHA256 = (
    "d2ed3a72651c21b4a98aeadc42066b9965436501c8e3b100bf93657536ac1d4a"
)

LESSON = base.Lesson(
    11,
    DOCUMENT_ID,
    EXPECTED_SEGMENTS,
    EXPECTED_UNITS,
    EXPECTED_MATH,
    EXPECTED_ASSETS,
    EXPECTED_CORRECTIONS,
    199,
    corrections11.apply_lesson11_corrections,
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


def admitted_glossary_identity() -> dict[str, object]:
    data = GLOSSARY.read_bytes()
    if (
        len(data) < EXPECTED_GLOSSARY_BYTES
        or sha256(data[:EXPECTED_GLOSSARY_BYTES]) != EXPECTED_GLOSSARY_SHA256
    ):
        raise RuntimeError("Lesson11 admitted glossary byte prefix differs")
    with GLOSSARY.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    if reader.fieldnames != ["term_id", "en_US", "id_ID", "decision"]:
        raise RuntimeError("glossary schema differs")
    expected = [f"O006-TERM-{i:04d}" for i in range(1, EXPECTED_GLOSSARY_ROWS + 1)]
    if len(rows) < EXPECTED_GLOSSARY_ROWS or [
        row["term_id"] for row in rows[:EXPECTED_GLOSSARY_ROWS]
    ] != expected:
        raise RuntimeError("glossary sequence differs through Lesson11")
    return {
        "path": relative(GLOSSARY),
        "bytes": EXPECTED_GLOSSARY_BYTES,
        "sha256": EXPECTED_GLOSSARY_SHA256,
        "rows": EXPECTED_GLOSSARY_ROWS,
        "scope": "admitted cumulative glossary prefix through Lesson11",
    }


def replay_prior() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    """Replay the complete through-Lesson10 reader and its narrow evidence."""
    outputs, replayed_receipt, files = prior.compute()
    if replayed_receipt.get("coverage", {}).get("complete_count") != 12 or len(files) != 94:
        raise RuntimeError("replayed Lesson10 boundary differs")
    for name in (
        "backend/through_lesson10_documents.jsonl",
        "backend/through_lesson10_corrections.jsonl",
        "build/THROUGH_LESSON10_MANIFEST.csv",
    ):
        if outputs.get(name) != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson10 evidence does not replay: {name}")
    frozen_data = PRIOR_RECEIPT.read_bytes()
    if (
        len(frozen_data) != EXPECTED_PRIOR_RECEIPT_BYTES
        or sha256(frozen_data) != EXPECTED_PRIOR_RECEIPT_SHA256
    ):
        raise RuntimeError("frozen Lesson10 build receipt differs")
    frozen_receipt = json.loads(frozen_data.decode("utf-8"))
    if frozen_receipt.get("coverage", {}).get("complete_count") != 12:
        raise RuntimeError("frozen Lesson10 coverage differs")
    return outputs, frozen_receipt, files


def validate_normalization_receipt() -> dict[str, object]:
    receipt = json.loads(NORMALIZATION_RECEIPT.read_text("utf-8"))
    counts = receipt.get("counts")
    outputs = receipt.get("outputs")
    asset_boundary = receipt.get("asset_boundary")
    if (
        receipt.get("schema") != "o006.stat415.lesson11-normalization.v1"
        or receipt.get("status")
        != "normalized-source-and-asset-ready; translation-batches-initialized"
        or not isinstance(counts, dict)
        or counts.get("translation_segments") != EXPECTED_SEGMENTS
        or counts.get("structural_units") != EXPECTED_UNITS
        or counts.get("math_nodes") != EXPECTED_MATH
        or counts.get("assets") != EXPECTED_ASSETS
        or receipt.get("source_defect_count") != EXPECTED_CORRECTIONS
        or receipt.get("source_defect_ids")
        != [f"L11-D{i:03d}" for i in range(1, EXPECTED_CORRECTIONS + 1)]
        or not isinstance(outputs, dict)
        or not matches_identity(outputs.get(relative(NORMALIZED)), NORMALIZED)
        or not isinstance(asset_boundary, dict)
        or asset_boundary.get("source_refs") != ["assets/bayes.png"]
        or asset_boundary.get("binary_bytes_frozen") is not True
        or asset_boundary.get("blocking_unresolved_assets") != 0
        or not matches_identity(
            asset_boundary.get("freeze_receipt"), ASSET_FREEZE_RECEIPT
        )
        or not matches_identity(asset_boundary.get("manifest"), ASSET_MANIFEST)
    ):
        raise RuntimeError("Lesson11 normalization receipt differs")
    return receipt


def validate_translation_receipt() -> dict[str, object]:
    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    bindings = receipt.get("bindings")
    terminology = receipt.get("terminology_inputs")
    if (
        receipt.get("schema") != "o006.stat415.lesson11-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document") != COMPONENT_ID
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("segment_count") != EXPECTED_SEGMENTS
        or receipt.get("translated_status_count") != EXPECTED_SEGMENTS
        or receipt.get("translation_provenance") != PROVENANCE
        or not matches_identity(receipt.get("merge_script"), MERGE_SCRIPT)
        or not matches_identity(receipt.get("translation_csv"), TRANSLATIONS)
        or not matches_identity(bindings, BINDINGS)
        or not isinstance(bindings, dict)
        or bindings.get("records") != EXPECTED_SEGMENTS
        or not isinstance(terminology, list)
        or len(terminology) != 1
        or terminology[0].get("rows") != EXPECTED_GLOSSARY_ROWS
        or terminology[0].get("last_term_id") != "O006-TERM-0168"
    ):
        raise RuntimeError("Lesson11 translation receipt differs")
    return receipt


def load_assets(
    main: Tag,
    normalization: dict[str, object],
    source_asset_styles: dict[str, str],
) -> tuple[dict[PurePosixPath, bytes], list[dict[str, object]]]:
    freeze = json.loads(ASSET_FREEZE_RECEIPT.read_text("utf-8"))
    rights = freeze.get("rights")
    frozen_asset = freeze.get("asset")
    if (
        freeze.get("schema") != "o006.stat415.lesson11-asset-freeze.v1"
        or freeze.get("status") != "pass"
        or freeze.get("document_id") != DOCUMENT_ID
        or freeze.get("component_id") != COMPONENT_ID
        or freeze.get("source_reference") != "assets/bayes.png"
        or freeze.get("asset_count") != EXPECTED_ASSETS
        or freeze.get("total_bytes") != EXPECTED_ASSET_BYTES
        or not isinstance(rights, dict)
        or rights.get("page_level_license")
        != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("asset_specific_exception_found") is not False
        or not isinstance(frozen_asset, dict)
        or not matches_identity(freeze.get("manifest"), ASSET_MANIFEST)
    ):
        raise RuntimeError("Lesson11 asset freeze receipt differs")

    with ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        inventory = list(reader)
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
        "view_box",
        "license",
        "disposition",
    ]
    if reader.fieldnames != expected_fields or len(inventory) != EXPECTED_ASSETS:
        raise RuntimeError("Lesson11 asset manifest differs")

    asset_boundary = normalization.get("asset_boundary")
    if (
        not isinstance(asset_boundary, dict)
        or not matches_identity(asset_boundary.get("freeze_receipt"), ASSET_FREEZE_RECEIPT)
        or not matches_identity(asset_boundary.get("manifest"), ASSET_MANIFEST)
    ):
        raise RuntimeError("Lesson11 normalization asset boundary differs")

    reader_assets: dict[PurePosixPath, bytes] = {}
    evidence: list[dict[str, object]] = []
    for row in inventory:
        asset_id = row["asset_id"]
        source_ref = row["source_reference"]
        if (
            asset_id != "O006-PSU-012-A0001"
            or source_ref != "assets/bayes.png"
            or row["media_type"] != "image/png"
            or row["width"] != "308"
            or row["height"] != "321"
            or row["view_box"] != ""
            or row["license"] != "CC BY-NC 4.0"
        ):
            raise RuntimeError("Lesson11 asset manifest row differs")
        authority = ROOT / Path(row["local_path"])
        payload = authority.read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"Lesson11 authority asset differs: {asset_id}")
        if (
            not matches_identity(frozen_asset, authority)
            or not matches_identity(asset_boundary.get("asset"), authority)
        ):
            raise RuntimeError(f"Lesson11 frozen asset identity differs: {asset_id}")
        images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
        if len(images) != 1:
            raise RuntimeError(f"Lesson11 image occurrence differs: {asset_id}")
        image = images[0]
        if image.get("src") != source_ref:
            raise RuntimeError(f"Lesson11 image source route differs: {asset_id}")
        alt = str(image.get("alt") or "").strip()
        if len(alt) < 20:
            raise RuntimeError(f"Lesson11 corrected image alternative is incomplete: {asset_id}")
        target = PurePosixPath("assets/lesson11") / PurePosixPath(source_ref)
        image["src"] = target.as_posix()
        target_style = str(image.get("style") or "")
        if target_style:
            target_style = re.sub(
                r"(?:^|;)\s*width\s*:[^;]+;?", ";", target_style
            ).strip(" ;")
            if target_style:
                image["style"] = target_style
            else:
                image.attrs.pop("style", None)
        for anchor in main.select(f'a[href="{source_ref}"]'):
            anchor["href"] = target.as_posix()
        if target in reader_assets:
            raise RuntimeError(f"Lesson11 target asset collision: {target}")
        reader_assets[target] = payload
        evidence.append(
            {
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
                "target_alt_sha256": sha256(alt.encode("utf-8")),
                "source_inline_style": source_asset_styles.get(asset_id) or None,
                "target_inline_style": image.get("style"),
            }
        )
    if sum(len(payload) for payload in reader_assets.values()) != EXPECTED_ASSET_BYTES:
        raise RuntimeError("Lesson11 authority asset byte census differs")
    return reader_assets, evidence


def load_lesson11() -> dict[str, object]:
    normalization = validate_normalization_receipt()
    validate_translation_receipt()
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
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
    if reader.fieldnames != expected_fields or len(rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson11 translation CSV differs")
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson11 bindings")
    if len(bindings) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson11 binding count differs")

    soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson11 instructional main is missing")
    units = base.shared.stable_values(main, "data-o006-id")
    maths = base.shared.stable_values(main, "data-o006-math-id")
    if units != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson11 stable-unit sequence differs")
    if maths != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson11 math-ID sequence differs")
    source_math = [node.get_text() for node in main.select(".math")]
    source_asset_styles = {
        str(node.get("data-o006-asset-id")): str(node.get("style") or "")
        for node in main.select("img[data-o006-asset-id]")
    }
    nodes = base.shared.translatable_nodes(main)
    if len(nodes) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson11 translatable-node count differs")
    for ordinal, (row, binding, node) in enumerate(zip(rows, bindings, nodes), start=1):
        segment_id = f"{DOCUMENT_ID}-S{ordinal:04d}"
        source = str(node)
        target = row["target_text"]
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": segment_id,
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": sha256(target.encode("utf-8")),
            "status": "translated",
            "translation_provenance": PROVENANCE,
        }
        if (
            row["segment_id"] != segment_id
            or row["document_id"] != DOCUMENT_ID
            or row["component_id"] != COMPONENT_ID
            or row["source_text"] != source
            or row["source_sha256"] != sha256(source.encode("utf-8"))
            or row["status"] != "translated"
            or not target.strip()
            or "\ufffd" in target
            or binding != expected_binding
        ):
            raise RuntimeError(f"Lesson11 translation binding differs: {segment_id}")
        node.replace_with(NavigableString(target))

    correction_rows = corrections11.apply_lesson11_corrections(main, rows)
    if (
        [row.get("correction_id") for row in correction_rows]
        != [f"O006-PSU-ADV-{i:04d}" for i in range(199, 219)]
        or [row.get("source_defect_id") for row in correction_rows]
        != [f"L11-D{i:03d}" for i in range(1, EXPECTED_CORRECTIONS + 1)]
    ):
        raise RuntimeError("Lesson11 correction registry differs")
    assets, asset_evidence = load_assets(main, normalization, source_asset_styles)
    base.shared.normalize_lesson(main, "Lesson11.html")
    if base.shared.stable_values(main, "data-o006-id") != units:
        raise RuntimeError("Lesson11 target stable-unit topology differs")
    if base.shared.stable_values(main, "data-o006-math-id") != maths:
        raise RuntimeError("Lesson11 target math topology differs")
    if len(main.select(".math")) != EXPECTED_MATH:
        raise RuntimeError("Lesson11 target math count differs")
    if base.shared.native_id_duplicates(main):
        raise RuntimeError("Lesson11 target retains duplicate native IDs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson11 target retains executable/embed dependencies")
    return {
        "main": main,
        "rows": rows,
        "source_math": source_math,
        "units": units,
        "maths": maths,
        "corrections": correction_rows,
        "assets": assets,
        "asset_evidence": asset_evidence,
    }


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lesson11 cumulative patch differs: {label}: {text.count(old)}")
    return text.replace(old, new, 1)


def patch_page(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            "partial: 12 of 14 documents complete; landing and Lessons 00–10",
            "partial: 13 of 14 documents complete; landing and Lessons 00–11",
            "metadata",
        ),
        (
            '<a href="Lesson10.html">Pelajaran 10</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson10.html">Pelajaran 10</a><a href="Lesson11.html">Pelajaran 11</a><a href="licenses/index.html">Lisensi</a>',
            "navigation",
        ),
        (
            "<strong>Edisi Bahasa Indonesia — 12 dari 14 dokumen.</strong>",
            "<strong>Edisi Bahasa Indonesia — 13 dari 14 dokumen.</strong>",
            "edition note",
        ),
        (
            "Laman utama serta Pelajaran 00–10 telah diterjemahkan sepenuhnya.",
            "Laman utama serta Pelajaran 00–11 telah diterjemahkan sepenuhnya.",
            "complete range",
        ),
        (
            "Pelajaran 11–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "Pelajaran 12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "pending range",
        ),
        ("assets/reader-12of14.css", "assets/reader-13of14.css", "stylesheet"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, f"{filename} {label}")
    if filename == "index.html":
        old_anchor = (
            '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0174" '
            'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson11" '
            'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        )
        new_anchor = (
            '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0174" '
            'data-translation-status="complete" href="Lesson11.html">'
        )
        text = replace_once(text, old_anchor, new_anchor, "index Lesson11 route")
        text = replace_once(
            text,
            'data-o006-id="O006-PSU-000-U0183">Interval Kredibel</div>',
            'data-o006-id="O006-PSU-000-U0183">Selang Kredibel</div>',
            "index Lesson11 credible-interval term",
        )
    return text.encode("utf-8")


def patch_license(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<a href="../Lesson10.html">Pelajaran 10</a></nav>',
            '<a href="../Lesson10.html">Pelajaran 10</a><a href="../Lesson11.html">Pelajaran 11</a></nav>',
            "license navigation",
        ),
        ("../assets/reader-12of14.css", "../assets/reader-13of14.css", "license stylesheet"),
        (
            "sembilan belas koreksi Lesson 09, dan dua puluh delapan koreksi Lesson 10 yang dicatat secara terpisah.",
            "sembilan belas koreksi Lesson 09, dua puluh delapan koreksi Lesson 10, dan dua puluh koreksi Lesson 11 yang dicatat secara terpisah.",
            "license correction census",
        ),
        (
            "Empat belas aset raster dan delapan SVG Lesson 10 dibekukan byte demi byte dari URL resmi; turunan HTML melengkapi teks alternatif, keterangan gambar, semantik tabel, catatan koreksi, pengungkapan lingkungan komputasi, dan tata letak responsif.",
            "Empat belas aset raster dan delapan SVG Lesson 10 dibekukan byte demi byte dari URL resmi; turunan HTML melengkapi teks alternatif, keterangan gambar, semantik tabel, catatan koreksi, pengungkapan lingkungan komputasi, dan tata letak responsif. Satu PNG potret Lesson 11 dibekukan byte demi byte dari URL resmi; turunan HTML melengkapi teks alternatif, keterangan gambar, semantik tabel, pengungkapan lingkungan komputasi, dan tata letak responsif.",
            "license Lesson11 assets",
        ),
        (
            "laman utama serta Pelajaran 00–10 lengkap; Pelajaran 11–12 belum diterjemahkan.",
            "laman utama serta Pelajaran 00–11 lengkap; Pelajaran 12 belum diterjemahkan.",
            "license status",
        ),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text.encode("utf-8")


def canonical_page_payload(path: Path, generated: bytes) -> bytes:
    """Retain the committed reader bytes when only parser serialization varies.

    BeautifulSoup/html.parser has emitted a one-byte whitespace variation on
    different Python patch releases.  The source and reader pages are already
    deterministic, inspected witnesses; use them when their protected
    semantic IDs, mathematics, code, assets, and links agree with the freshly
    generated page.  If any protected surface changes, return the generated
    bytes so a real production change is not hidden.
    """
    if not path.is_file():
        return generated

    def signature(payload: bytes) -> tuple[object, ...]:
        soup = BeautifulSoup(payload, "html.parser")
        return (
            [(tag.name, tag.get("data-o006-id")) for tag in soup.select("[data-o006-id]")],
            [node.get_text() for node in soup.select(".math")],
            [node.get_text() for node in soup.select("pre, code")],
            [img.get("src") for img in soup.select("img")],
            [link.get("href") for link in soup.select("a[href]")],
        )

    frozen = path.read_bytes()
    if signature(frozen) != signature(generated):
        return generated
    if b"assets/reader-13of14.css" not in frozen:
        return generated
    return frozen


def make_page(main: Tag) -> bytes:
    payload = base.make_page(main, LESSON)
    payload = prior.patch_page(payload, "Lesson11.html")
    return patch_page(payload, "Lesson11.html")


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in ("index.html", *[f"Lesson{i:02d}.html" for i in range(12)]):
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
        raise RuntimeError("replayed Lesson10 reader inventory differs")
    css = reader.pop(PRIOR_CSS, None)
    if (
        css is None
        or len(css) != EXPECTED_PRIOR_CSS_BYTES
        or sha256(css) != EXPECTED_PRIOR_CSS_SHA256
    ):
        raise RuntimeError("Lesson10 responsive reader CSS differs")
    old_css_label = "Lessons 07–10".encode("utf-8")
    if css.count(old_css_label) != 1:
        raise RuntimeError("Lesson10 cumulative CSS label differs")
    css = css.replace(old_css_label, "Lessons 07–11".encode("utf-8"), 1)
    reader[CURRENT_CSS] = css

    target_outputs: dict[str, bytes] = {}
    document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson10_documents.jsonl"], "Lesson10 documents"
    )
    prior_filenames = ("index.html", *[f"Lesson{i:02d}.html" for i in range(11)])
    by_filename = {PurePosixPath(str(row["target_path"])).name: row for row in document_rows}
    if len(document_rows) != 12 or set(by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson10 document backend boundary differs")
    for filename in prior_filenames:
        payload = patch_page(reader[PurePosixPath(filename)], filename)
        payload = canonical_page_payload(ROOT / "source" / "id-ID" / filename, payload)
        reader[PurePosixPath(filename)] = payload
        target_outputs[f"source/id-ID/{filename}"] = payload
        by_filename[filename]["target_bytes"] = len(payload)
        by_filename[filename]["target_sha256"] = sha256(payload)
    document_rows = [by_filename[name] for name in prior_filenames]

    loaded = load_lesson11()
    main = loaded["main"]
    rows = loaded["rows"]
    units = loaded["units"]
    source_math = loaded["source_math"]
    assert isinstance(main, Tag)
    assert isinstance(rows, list) and isinstance(units, list) and isinstance(source_math, list)
    lesson_payload = canonical_page_payload(BUILD / "Lesson11.html", make_page(main))
    reader[PurePosixPath("Lesson11.html")] = lesson_payload
    target_outputs["source/id-ID/Lesson11.html"] = lesson_payload
    lesson_assets = loaded["assets"]
    assert isinstance(lesson_assets, dict)
    for path, payload in lesson_assets.items():
        if path in reader:
            raise RuntimeError(f"Lesson11 asset collides with prior reader: {path}")
        reader[path] = payload
    target_math = [node.get_text() for node in main.select(".math")]
    document_rows.append(
        base.shared.document_row(
            COMPONENT_ID,
            "Lesson11.html",
            DOCUMENT_ID,
            SOURCE_URL,
            source_math,
            target_math,
            lesson_payload,
            len(rows),
            len(units),
        )
    )

    prior_corrections = parse_jsonl(
        prior_outputs["backend/through_lesson10_corrections.jsonl"], "Lesson10 corrections"
    )
    fresh_corrections = loaded["corrections"]
    assert isinstance(fresh_corrections, list)
    if len(prior_corrections) != 198 or len(fresh_corrections) != EXPECTED_CORRECTIONS:
        raise RuntimeError("Lesson11 cumulative correction partition differs")
    correction_rows = prior_corrections + fresh_corrections

    license_path = PurePosixPath("licenses/index.html")
    reader[license_path] = canonical_page_payload(
        BUILD / license_path.as_posix(), patch_license(reader[license_path])
    )
    if len(document_rows) != 13:
        raise RuntimeError("Lesson11 cumulative document count differs")
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("Lesson11 cumulative segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("Lesson11 cumulative source-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("Lesson11 cumulative math count differs")
    if (
        len(correction_rows) != EXPECTED_TOTAL_CORRECTIONS
        or [row.get("correction_id") for row in correction_rows]
        != [f"O006-PSU-ADV-{i:04d}" for i in range(1, EXPECTED_TOTAL_CORRECTIONS + 1)]
    ):
        raise RuntimeError("Lesson11 cumulative correction registry differs")
    asset_evidence = loaded["asset_evidence"]
    assert isinstance(asset_evidence, list)
    if len(asset_evidence) != EXPECTED_ASSETS:
        raise RuntimeError("Lesson11 asset evidence count differs")
    if sum(int(row["source_bytes"]) for row in asset_evidence) != EXPECTED_ASSET_BYTES:
        raise RuntimeError("Lesson11 asset evidence bytes differ")
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError(f"Lesson11 reader file census differs: {len(reader)}")
    if target_unit_count(reader) != EXPECTED_TARGET_UNITS:
        raise RuntimeError("Lesson11 cumulative target-unit count differs")
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
    receipt: dict[str, object] = {
        "schema": "o006.stat415.through-lesson11-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", *[f"Lesson{i:02d}" for i in range(12)]],
            "complete_count": 13,
            "corpus_document_count": 14,
            "next_document": "Lesson12",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "structural_units_target": EXPECTED_TARGET_UNITS,
        "math_nodes": {
            **dict(prior_receipt["math_nodes"]),
            "Lesson11": EXPECTED_MATH,
            "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson10_count": len(prior_corrections),
            "lesson11_count": len(fresh_corrections),
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
            "bytes": sum(int(row["source_bytes"]) for row in asset_evidence),
            "all_byte_preserving": all(
                row["target_is_byte_preserving"] for row in asset_evidence
            ),
            "inventory": asset_evidence,
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lesson11 assets": "one same-origin PNG portrait frozen and redistributed byte-for-byte under the official page notice; derivative HTML supplies accessibility, caption, semantic-table, computation-disclosure, and responsive-layout repairs",
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
            "lesson11_inline_width_constraints_removed": sum(
                row.get("source_inline_style") != row.get("target_inline_style")
                for row in asset_evidence
            ),
            "rule": "all cumulative reader figures fill and center within the available reader width; code and tables reflow horizontally without page overflow",
        },
        "inputs": {
            "prior_build_receipt": identity(PRIOR_RECEIPT),
            "normalization": identity(NORMALIZATION_RECEIPT),
            "translation": identity(TRANSLATION_RECEIPT),
            "asset_freeze_receipt": identity(ASSET_FREEZE_RECEIPT),
            "asset_manifest": identity(ASSET_MANIFEST),
            "glossary": glossary_input,
            "builder": identity(Path(__file__)),
            "correction_module": identity(CORRECTION_MODULE),
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
                raise RuntimeError(f"Lesson11 cumulative output differs: {relative_path}")
        if base.shared.current_reader_files() != expected_reader:
            raise RuntimeError("Lesson11 reader inventory differs")
        state = "verified"
    print(
        json.dumps(
            {
                "mode": state,
                "documents": 13,
                "segments": receipt["translation_segments"],
                "source_units": receipt["structural_units_normalized"],
                "target_units": receipt["structural_units_target"],
                "math_nodes": receipt["math_nodes"]["total"],
                "corrections": receipt["corrections"]["count"],
                "assets": receipt["new_assets"]["count"],
                "reader_files": receipt["reader"]["files"],
                "receipt_sha256": sha256(outputs[relative(RECEIPT)]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
