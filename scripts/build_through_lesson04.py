#!/usr/bin/env python3
"""Build the cumulative id-ID reader through Penn State STAT 415 Lesson 04."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import tempfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson03 as prior
import lesson04_corrections as corrections


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson04.html"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson04_translation.csv"
BINDINGS = ROOT / "backend" / "lesson04_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON04_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON04_NORMALIZATION_RECEIPT.json"
ASSET = ROOT / "authority" / "assets" / "stat415" / "lesson04" / "STAT-415-SEC-1-15.svg"
ASSET_RECEIPT = ROOT / "authority" / "LESSON04_ASSET_FREEZE_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
DOCUMENTS = ROOT / "backend" / "through_lesson04_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson04_corrections.jsonl"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON04_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON04_BUILD_RECEIPT.json"

DOCUMENT_ID = "O006-PSU-005"
COMPONENT_ID = "Lesson04"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson04"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_SEGMENTS = 372
EXPECTED_UNITS = 335
EXPECTED_MATH = 289
EXPECTED_TOTAL_SEGMENTS = 1_971
EXPECTED_TOTAL_UNITS = 1_734
EXPECTED_TARGET_UNITS = 1_732
EXPECTED_TOTAL_MATH = 1_438
EXPECTED_READER_FILES = 34
PRIOR_CSS = PurePosixPath("assets/reader-5of14.css")
CURRENT_CSS = PurePosixPath("assets/reader-6of14.css")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": sha256(data)}


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


def replay_prior() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    glossary = GLOSSARY.read_bytes()
    key = "00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv"
    saved = prior.FROZEN_INPUTS
    admitted = dict(saved)
    admitted[key] = (len(glossary), sha256(glossary))
    prior.FROZEN_INPUTS = admitted
    try:
        outputs, receipt, files = prior.compute()
    finally:
        prior.FROZEN_INPUTS = saved
    if receipt.get("coverage", {}).get("complete_count") != 5 or len(files) != 32:
        raise RuntimeError("replayed Lesson03 boundary differs")
    for name in (
        "backend/through_lesson03_documents.jsonl",
        "backend/through_lesson03_corrections.jsonl",
        "build/THROUGH_LESSON03_MANIFEST.csv",
    ):
        if outputs.get(name) != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson03 evidence does not replay: {name}")
    return outputs, receipt, files


def validate_translation_receipt() -> None:
    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    if (
        receipt.get("schema") != "o006.stat415.lesson04-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("segment_count") != EXPECTED_SEGMENTS
        or receipt.get("translation_provenance") != PROVENANCE
    ):
        raise RuntimeError("Lesson04 translation receipt contract differs")
    for field, path in (("translation_csv", TRANSLATIONS), ("bindings", BINDINGS)):
        record = receipt.get(field)
        data = path.read_bytes()
        if not isinstance(record, dict) or (
            record.get("path") != relative(path)
            or record.get("bytes") != len(data)
            or record.get("sha256") != sha256(data)
        ):
            raise RuntimeError(f"Lesson04 translation output identity differs: {field}")
    if receipt.get("word_boundary_leading_space_exceptions") != ["O006-PSU-005-S0088"]:
        raise RuntimeError("Lesson04 boundary registry differs")


def validate_asset() -> bytes:
    receipt = json.loads(ASSET_RECEIPT.read_text("utf-8"))
    asset = ASSET.read_bytes()
    record = receipt.get("authority_asset")
    if (
        receipt.get("schema") != "o006.stat415.lesson04-asset-freeze.v1"
        or receipt.get("status") != "frozen-and-verified"
        or receipt.get("document_id") != DOCUMENT_ID
        or not isinstance(record, dict)
        or record.get("bytes") != len(asset)
        or record.get("sha256") != sha256(asset)
    ):
        raise RuntimeError("Lesson04 asset receipt differs")
    return asset


def load_lesson04() -> tuple[Tag, list[dict[str, str]], list[str], list[str], list[str], bytes]:
    validate_translation_receipt()
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        expected_fields = [
            "segment_id", "document_id", "component_id", "section_id",
            "source_sha256", "source_text", "target_text", "status",
        ]
        if reader.fieldnames != expected_fields:
            raise RuntimeError("Lesson04 translation CSV schema differs")
        rows = list(reader)
    if len(rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson04 translation row count differs")
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson04 translation bindings")
    if len(bindings) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson04 translation binding count differs")

    soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("normalized Lesson04 main is missing")
    units = shared.stable_values(main, "data-o006-id")
    maths = shared.stable_values(main, "data-o006-math-id")
    if units != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson04 stable-unit sequence differs")
    if maths != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson04 math-ID sequence differs")
    if shared.native_id_duplicates(main):
        raise RuntimeError("Lesson04 normalized source has duplicate native IDs")
    source_math = [node.get_text() for node in main.select(".math")]
    nodes = shared.translatable_nodes(main)
    if len(nodes) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson04 translatable-node count differs")
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
            raise RuntimeError(f"Lesson04 translation binding differs: {sid}")
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
            raise RuntimeError(f"Lesson04 backend translation binding differs: {sid}")
        node.replace_with(NavigableString(target))

    authority_asset = validate_asset()
    correction_rows, target_asset = corrections.apply_lesson04_corrections(main, rows, authority_asset)

    images = main.select('img[src="assets/STAT-415-SEC-1-15.svg"]')
    lightboxes = main.select('a.lightbox[href="assets/STAT-415-SEC-1-15.svg"]')
    if len(images) != 1 or len(lightboxes) != 1:
        raise RuntimeError("Lesson04 asset reference topology differs")
    images[0]["src"] = "assets/lesson04/STAT-415-SEC-1-15.svg"
    images[0]["alt"] = "Grafik y = ln(x) yang monoton naik; x₁ < x₂ menghasilkan f(x₁) < f(x₂)."
    lightboxes[0]["href"] = "assets/lesson04/STAT-415-SEC-1-15.svg"

    shared.normalize_lesson(main, "Lesson04.html")
    if shared.stable_values(main, "data-o006-id") != units:
        raise RuntimeError("Lesson04 target stable-unit topology differs")
    if shared.stable_values(main, "data-o006-math-id") != maths:
        raise RuntimeError("Lesson04 target math topology differs")
    if len(main.select(".math")) != EXPECTED_MATH:
        raise RuntimeError("Lesson04 target math count differs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson04 target retains an executable/embed dependency")
    return main, rows, source_math, units, maths, target_asset


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lesson04 cumulative patch surface differs: {label}: {text.count(old)}")
    return text.replace(old, new, 1)


def patch_page(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        ('partial: 5 of 14 documents complete; landing and Lessons 00–03', 'partial: 6 of 14 documents complete; landing and Lessons 00–04', "metadata"),
        ('<a href="Lesson03.html">Pelajaran 03</a><a href="licenses/index.html">Lisensi</a>', '<a href="Lesson03.html">Pelajaran 03</a><a href="Lesson04.html">Pelajaran 04</a><a href="licenses/index.html">Lisensi</a>', "navigation"),
        ('<strong>Edisi Bahasa Indonesia — 5 dari 14 dokumen.</strong>', '<strong>Edisi Bahasa Indonesia — 6 dari 14 dokumen.</strong>', "edition note"),
        ('Laman utama serta Pelajaran 00–03 telah diterjemahkan sepenuhnya.', 'Laman utama serta Pelajaran 00–04 telah diterjemahkan sepenuhnya.', "complete range"),
        ('Pelajaran 04–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.', 'Pelajaran 05–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.', "pending range"),
        ('assets/reader-5of14.css', 'assets/reader-6of14.css', "stylesheet"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, f"{filename} {label}")
    if filename == "index.html":
        old_anchor = '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0078" data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson04" title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        new_anchor = '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0078" data-translation-status="complete" href="Lesson04.html">'
        text = replace_once(text, old_anchor, new_anchor, "index Lesson04 route")
        text = replace_once(text, "Estimasi Kemungkinan Maksimum (MLE) (Bagian I)", "Pendugaan Kemungkinan Maksimum (MLE) (Bagian I)", "index terminology")
    return text.encode("utf-8")


def patch_license(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        ('<a href="../Lesson03.html">Pelajaran 03</a></nav>', '<a href="../Lesson03.html">Pelajaran 03</a><a href="../Lesson04.html">Pelajaran 04</a></nav>', "license navigation"),
        ('../assets/reader-5of14.css', '../assets/reader-6of14.css', "license stylesheet"),
        ('serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, dan tujuh belas koreksi Lesson 03 yang dicatat secara terpisah.', 'serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, tujuh belas koreksi Lesson 03, dan tiga puluh lima koreksi Lesson 04 yang dicatat secara terpisah.', "license corrections"),
        ('Lesson 03 tidak memiliki aset isi yang perlu dibekukan.', 'Lesson 03 tidak memiliki aset isi yang perlu dibekukan. Satu SVG pengajaran Lesson 04 dibekukan dari URL resmi; byte sumber dipertahankan dan salah label x₁/x₂ diperbaiki hanya pada aset turunan dengan catatan perubahan.', "license asset"),
        ('laman utama serta Pelajaran 00–03 lengkap; Pelajaran 04–12 belum diterjemahkan.', 'laman utama serta Pelajaran 00–04 lengkap; Pelajaran 05–12 belum diterjemahkan.', "license status"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text.encode("utf-8")


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in ("index.html", "Lesson00.html", "Lesson01.html", "Lesson02.html", "Lesson03.html", "Lesson04.html"):
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
        raise RuntimeError("replayed Lesson03 reader inventory differs")
    css = reader.pop(PRIOR_CSS, None)
    if css is None or len(css) != 6_213 or sha256(css) != "37fc52f724e0ea76443dc12ef243bf874ab6fb8c3c0640e03ab8cf1a6939f989":
        raise RuntimeError("responsive reader CSS differs")
    reader[CURRENT_CSS] = css

    target_outputs: dict[str, bytes] = {}
    document_rows = parse_jsonl(prior_outputs["backend/through_lesson03_documents.jsonl"], "Lesson03 documents")
    if len(document_rows) != 5:
        raise RuntimeError("Lesson03 document backend count differs")
    by_filename = {PurePosixPath(str(row["target_path"])).name: row for row in document_rows}
    prior_filenames = ("index.html", "Lesson00.html", "Lesson01.html", "Lesson02.html", "Lesson03.html")
    if set(by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson03 document backend filenames differ")
    for filename in prior_filenames:
        patched = patch_page(reader[PurePosixPath(filename)], filename)
        reader[PurePosixPath(filename)] = patched
        target_outputs[f"source/id-ID/{filename}"] = patched
        by_filename[filename]["target_bytes"] = len(patched)
        by_filename[filename]["target_sha256"] = sha256(patched)

    main, rows, source_math, unit_ids, math_ids, target_asset = load_lesson04()
    lesson_payload = patch_page(prior.page_document(main, COMPONENT_ID, SOURCE_URL), "Lesson04.html")
    reader[PurePosixPath("Lesson04.html")] = lesson_payload
    reader[PurePosixPath("assets/lesson04/STAT-415-SEC-1-15.svg")] = target_asset
    target_outputs["source/id-ID/Lesson04.html"] = lesson_payload
    target_math = [node.get_text() for node in main.select(".math")]

    document_rows = [by_filename[name] for name in prior_filenames]
    document_rows.append(shared.document_row(
        COMPONENT_ID, "Lesson04.html", DOCUMENT_ID, SOURCE_URL,
        source_math, target_math, lesson_payload, len(rows), len(unit_ids),
    ))
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math count differs")

    prior_corrections = parse_jsonl(prior_outputs["backend/through_lesson03_corrections.jsonl"], "Lesson03 corrections")
    fresh_corrections, checked_asset = corrections.apply_lesson04_corrections(
        BeautifulSoup(NORMALIZED.read_bytes(), "html.parser").select_one("main#quarto-document-content"),
        rows,
        ASSET.read_bytes(),
    )
    # The second application above is only a deterministic correction-registry replay.
    if checked_asset != target_asset or len(fresh_corrections) != 35:
        raise RuntimeError("Lesson04 correction replay differs")
    correction_rows = prior_corrections + fresh_corrections
    if len(correction_rows) != 81 or [row["correction_id"] for row in correction_rows] != [f"O006-PSU-ADV-{i:04d}" for i in range(1, 82)]:
        raise RuntimeError("cumulative correction registry differs")

    reader[PurePosixPath("licenses/index.html")] = patch_license(prior.license_page())
    if len(reader) != EXPECTED_READER_FILES or target_unit_count(reader) != EXPECTED_TARGET_UNITS:
        raise RuntimeError("cumulative reader file/unit census differs")
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
        "schema": "o006.stat415.through-lesson04-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", "Lesson00", "Lesson01", "Lesson02", "Lesson03", "Lesson04"],
            "complete_count": 6,
            "corpus_document_count": 14,
            "next_document": "Lesson05",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "structural_units_target": EXPECTED_TARGET_UNITS,
        "math_nodes": {
            "index": 0, "Lesson00": 331, "Lesson01": 169, "Lesson02": 209,
            "Lesson03": 440, "Lesson04": 289, "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson03_count": len(prior_corrections),
            "lesson04_count": len(fresh_corrections),
            "path": relative(CORRECTIONS),
            "bytes": len(corrections_payload),
            "sha256": sha256(corrections_payload),
        },
        "documents_backend": {
            "path": relative(DOCUMENTS), "bytes": len(documents_payload), "sha256": sha256(documents_payload),
        },
        "reader": {
            "path": relative(BUILD),
            "files": len(reader),
            "bytes": sum(len(payload) for payload in reader.values()),
            "manifest_path": relative(MANIFEST),
            "manifest_bytes": len(manifest_payload),
            "manifest_sha256": sha256(manifest_payload),
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lesson04 SVG": "CC BY-NC 4.0 under the official page notice; authority bytes frozen; one disclosed derivative label repair",
            "MathJax 3.1.2": "Apache-2.0",
            "aggregate_uniform_relicense": False,
        },
        "offline": {"external_runtime_requests": 0, "analytics": False, "cookies": False, "local_mathjax": True},
        "layout": {
            "reader_css_path": CURRENT_CSS.as_posix(), "reader_css_bytes": len(css), "reader_css_sha256": sha256(css),
            "rule": "responsive instructional-media reflow remains active for all translated documents",
        },
        "inputs": {
            "prior_public_build_receipt": identity(ROOT / "build" / "THROUGH_LESSON03_BUILD_RECEIPT.json"),
            "normalization": identity(NORMALIZATION_RECEIPT),
            "translation": identity(TRANSLATION_RECEIPT),
            "asset_freeze": identity(ASSET_RECEIPT),
            "glossary_current_additive_file": identity(GLOSSARY),
            "builder": identity(Path(__file__)),
            "correction_module": identity(ROOT / "scripts" / "lesson04_corrections.py"),
        },
        "target_documents": [
            {"path": str(row["target_path"]), "bytes": int(row["target_bytes"]), "sha256": str(row["target_sha256"])}
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
                raise RuntimeError(f"Lesson04 cumulative output differs: {relative_path}")
        actual_reader = shared.current_reader_files()
        if actual_reader != expected_reader:
            raise RuntimeError(f"Lesson04 reader inventory differs: extra={sorted(actual_reader-expected_reader)} missing={sorted(expected_reader-actual_reader)}")
        state = "verified"
    print(json.dumps({
        "mode": state,
        "documents": receipt["coverage"]["complete_count"],
        "segments": receipt["translation_segments"],
        "math_nodes": receipt["math_nodes"]["total"],
        "corrections": receipt["corrections"]["count"],
        "reader_files": receipt["reader"]["files"],
        "receipt_sha256": sha256(outputs[relative(RECEIPT)]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
