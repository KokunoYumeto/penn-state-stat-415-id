#!/usr/bin/env python3
"""Build the cumulative id-ID reader through Penn State STAT 415 Lesson 05."""

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
import build_through_lesson04 as prior
import lesson05_corrections as corrections


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson05.html"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson05_translation.csv"
BINDINGS = ROOT / "backend" / "lesson05_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON05_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON05_NORMALIZATION_RECEIPT.json"
ASSET_CLOSURE = ROOT / "working" / "lesson05_asset_closure.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
MATHJAX_RUNTIME = ROOT / "authority" / "runtime" / "MathJax-3.1.2"
MATHJAX_BOLDSYMBOL = MATHJAX_RUNTIME / "input" / "tex" / "extensions" / "boldsymbol.js"
MATHJAX_MANIFEST = MATHJAX_RUNTIME / "URL_MANIFEST.csv"
MATHJAX_RECEIPT = MATHJAX_RUNTIME / "FREEZE_RECEIPT.json"
DOCUMENTS = ROOT / "backend" / "through_lesson05_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson05_corrections.jsonl"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON05_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON05_BUILD_RECEIPT.json"

DOCUMENT_ID = "O006-PSU-006"
COMPONENT_ID = "Lesson05"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson05"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_SEGMENTS = 340
EXPECTED_UNITS = 1_475
EXPECTED_MATH = 108
EXPECTED_ASSETS = 14
EXPECTED_TARGET_ASSET_BYTES = 498_847
EXPECTED_TOTAL_SEGMENTS = 2_311
EXPECTED_TOTAL_UNITS = 3_209
EXPECTED_TARGET_UNITS = 3_207
EXPECTED_TOTAL_MATH = 1_546
EXPECTED_READER_FILES = 50
EXPECTED_BOLDSYMBOL_BYTES = 4_709
EXPECTED_BOLDSYMBOL_SHA256 = "716cf8735d00abfb1627f8adbbf4aeb915ac9b5c55d47aeaf276e73dac6a2aa1"
PRIOR_CSS = PurePosixPath("assets/reader-6of14.css")
CURRENT_CSS = PurePosixPath("assets/reader-7of14.css")
CODE_REFLOW_CSS = b"""

/* Lesson 05: readable, full-width static code blocks. */
.code-copy-outer-scaffold {
  position: relative;
  max-width: 100%;
  margin: 1rem 0;
}

main .cell,
main .cell-output,
main .cell-output-display,
main .sourceCode {
  min-width: 0;
  max-width: 100%;
}

main pre {
  position: relative;
  display: block;
  width: 100%;
  min-width: 0;
  max-width: 100%;
  margin: 0;
  padding: 1rem 1.1rem;
  overflow-x: auto;
  color: #17202a;
  background: #f6f8fa;
  border: 1px solid #d9e0e6;
  border-radius: 0.4rem;
  font: 0.9rem/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  white-space: pre;
}

.codeblock-with-label pre[class*="lang-label-"] {
  padding-top: 2.65rem;
}

.codeblock-with-label pre[class*="lang-label-"]::before {
  position: absolute;
  inset: 0 0 auto 0;
  display: block;
  padding: 0.42rem 0.8rem;
  color: #34404c;
  background: #e9eef4;
  border-bottom: 1px solid #d0d8e1;
  font: 700 0.76rem/1.25 ui-sans-serif, system-ui, sans-serif;
  letter-spacing: 0.04em;
}

/* Quarto's copy runtime is deliberately absent in the static offline reader. */
.code-copy-button { display: none !important; }
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


def replay_prior() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    outputs, receipt, files = prior.compute()
    if receipt.get("coverage", {}).get("complete_count") != 6 or len(files) != 34:
        raise RuntimeError("replayed Lesson04 boundary differs")
    for name in (
        "backend/through_lesson04_documents.jsonl",
        "backend/through_lesson04_corrections.jsonl",
        "build/THROUGH_LESSON04_MANIFEST.csv",
    ):
        if outputs.get(name) != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson04 evidence does not replay: {name}")
    return outputs, receipt, files


def validate_translation_receipt() -> None:
    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    if (
        receipt.get("schema") != "o006.stat415.lesson05-translation.v1"
        or receipt.get("status") != "complete"
        or receipt.get("document_id") != DOCUMENT_ID
        or receipt.get("segment_count") != EXPECTED_SEGMENTS
        or receipt.get("translation_provenance") != PROVENANCE
        or receipt.get("identical_segments") != []
    ):
        raise RuntimeError("Lesson05 translation receipt contract differs")
    for field, path in (("translation_csv", TRANSLATIONS), ("bindings", BINDINGS)):
        record = receipt.get(field)
        data = path.read_bytes()
        if not isinstance(record, dict) or (
            record.get("path") != relative(path)
            or record.get("bytes") != len(data)
            or record.get("sha256") != sha256(data)
        ):
            raise RuntimeError(f"Lesson05 translation output identity differs: {field}")

    admitted_assets = receipt.get("asset_inputs")
    if not isinstance(admitted_assets, list):
        raise RuntimeError("Lesson05 translation asset-input evidence is missing")
    admitted_by_path = {str(row.get("path")): row for row in admitted_assets if isinstance(row, dict)}
    for path in (ASSET_CLOSURE, NORMALIZATION_RECEIPT):
        record = admitted_by_path.get(relative(path))
        data = path.read_bytes()
        if not isinstance(record, dict) or (
            record.get("bytes") != len(data) or record.get("sha256") != sha256(data)
        ):
            raise RuntimeError(f"Lesson05 admitted asset input differs: {relative(path)}")


def load_mathjax_boldsymbol() -> bytes:
    payload = MATHJAX_BOLDSYMBOL.read_bytes()
    if len(payload) != EXPECTED_BOLDSYMBOL_BYTES or sha256(payload) != EXPECTED_BOLDSYMBOL_SHA256:
        raise RuntimeError("MathJax 3.1.2 boldsymbol authority differs")

    manifest_data = MATHJAX_MANIFEST.read_bytes()
    with MATHJAX_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        manifest_rows = list(csv.DictReader(stream))
    expected_fields = ["relative_path", "url", "bytes", "sha256", "component", "license"]
    if stream.closed is not True or not manifest_rows:
        raise RuntimeError("MathJax 3.1.2 manifest could not be read")
    if list(manifest_rows[0]) != expected_fields or len(manifest_rows) != 6:
        raise RuntimeError("MathJax 3.1.2 manifest contract differs")
    by_path = {row["relative_path"]: row for row in manifest_rows}
    bold = by_path.get("input/tex/extensions/boldsymbol.js")
    if bold != {
        "relative_path": "input/tex/extensions/boldsymbol.js",
        "url": "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/input/tex/extensions/boldsymbol.js",
        "bytes": str(EXPECTED_BOLDSYMBOL_BYTES),
        "sha256": EXPECTED_BOLDSYMBOL_SHA256,
        "component": "MathJax 3.1.2",
        "license": "Apache-2.0",
    }:
        raise RuntimeError("MathJax 3.1.2 boldsymbol manifest row differs")

    receipt = json.loads(MATHJAX_RECEIPT.read_text("utf-8"))
    receipt_manifest = receipt.get("manifest")
    receipt_files = receipt.get("files")
    if (
        receipt.get("schema") != "o006.stat415.mathjax-freeze.v1"
        or receipt.get("component") != "MathJax"
        or receipt.get("version") != "3.1.2"
        or receipt.get("license") != "Apache-2.0"
        or receipt.get("file_count") != 6
        or receipt.get("total_bytes") != 1_737_270
        or not isinstance(receipt_manifest, dict)
        or receipt_manifest.get("path") != relative(MATHJAX_MANIFEST)
        or receipt_manifest.get("bytes") != len(manifest_data)
        or receipt_manifest.get("sha256") != sha256(manifest_data)
        or not isinstance(receipt_files, list)
        or len(receipt_files) != 6
        or next(
            (row for row in receipt_files if row.get("relative_path") == "input/tex/extensions/boldsymbol.js"),
            None,
        )
        != {
            "relative_path": "input/tex/extensions/boldsymbol.js",
            "url": "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/input/tex/extensions/boldsymbol.js",
            "bytes": EXPECTED_BOLDSYMBOL_BYTES,
            "sha256": EXPECTED_BOLDSYMBOL_SHA256,
            "component": "MathJax 3.1.2",
            "license": "Apache-2.0",
        }
    ):
        raise RuntimeError("MathJax 3.1.2 freeze receipt differs")
    return payload


def load_asset_closure(main: Tag) -> tuple[dict[PurePosixPath, bytes], list[dict[str, object]]]:
    audit = json.loads(ASSET_CLOSURE.read_text("utf-8"))
    counts = audit.get("counts")
    assets = audit.get("frozen_images")
    if (
        audit.get("schema") != "o006.stat415.lesson05-asset-closure.v1"
        or audit.get("status")
        != "same-origin-images-closed-external-video-excluded-reader-remediation-required"
        or audit.get("document_id") != DOCUMENT_ID
        or not isinstance(counts, dict)
        or counts.get("frozen_png_files") != EXPECTED_ASSETS
        or counts.get("image_occurrences") != EXPECTED_ASSETS
        or counts.get("external_iframe_occurrences") != 2
        or not isinstance(assets, list)
        or len(assets) != EXPECTED_ASSETS
    ):
        raise RuntimeError("Lesson05 asset-closure contract differs")

    expected_ids = [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, EXPECTED_ASSETS + 1)]
    if [row.get("asset_id") for row in assets] != expected_ids:
        raise RuntimeError("Lesson05 asset identity sequence differs")

    reader_assets: dict[PurePosixPath, bytes] = {}
    evidence: list[dict[str, object]] = []
    target_paths: set[str] = set()
    for row in assets:
        asset_id = str(row["asset_id"])
        source_ref = str(row.get("source_ref"))
        local_path = str(row.get("local_path"))
        rights = row.get("rights")
        if (
            row.get("disposition") != "freeze"
            or not isinstance(rights, dict)
            or rights.get("applied_license") != "CC BY-NC 4.0"
            or not source_ref.endswith(".png")
        ):
            raise RuntimeError(f"Lesson05 asset admission differs: {asset_id}")
        source_path = ROOT / Path(local_path)
        source = source_path.read_bytes()
        if len(source) != row.get("bytes") or sha256(source) != row.get("sha256"):
            raise RuntimeError(f"Lesson05 authority asset differs: {asset_id}")

        images = main.select(f'[data-o006-asset-id="{asset_id}"]')
        if len(images) != 1 or images[0].name != "img":
            raise RuntimeError(f"Lesson05 target image topology differs: {asset_id}")
        image = images[0]

        if asset_id == f"{DOCUMENT_ID}-A0004":
            destination = PurePosixPath("assets/lesson05/seeded-z1000.png")
            target = corrections.SEEDED_PLOT.read_bytes()
            if (
                image.get("src") != destination.as_posix()
                or len(target) != corrections.SEEDED_PLOT_BYTES
                or sha256(target) != corrections.SEEDED_PLOT_SHA256
                or len(source) != corrections.SOURCE_PLOT_BYTES
                or sha256(source) != corrections.SOURCE_PLOT_SHA256
            ):
                raise RuntimeError("Lesson05 seeded target asset differs")
            derivative = True
        else:
            destination = PurePosixPath(f"assets/lesson05/{PurePosixPath(source_ref).name}")
            if image.get("src") != source_ref:
                raise RuntimeError(f"Lesson05 normalized image route differs: {asset_id}")
            image["src"] = destination.as_posix()
            target = source
            derivative = False

        lightbox_count = int(row.get("lightbox_href_occurrences", -1))
        lightboxes = main.select(f'a.lightbox[href="{source_ref}"]')
        if len(lightboxes) != lightbox_count:
            raise RuntimeError(f"Lesson05 lightbox topology differs: {asset_id}")
        for lightbox in lightboxes:
            lightbox["href"] = destination.as_posix()

        if destination.as_posix() in target_paths or destination in reader_assets:
            raise RuntimeError(f"Lesson05 reader asset collision: {destination}")
        target_paths.add(destination.as_posix())
        reader_assets[destination] = target
        evidence.append({
            "asset_id": asset_id,
            "source_path": local_path,
            "source_bytes": len(source),
            "source_sha256": sha256(source),
            "target_path": destination.as_posix(),
            "target_bytes": len(target),
            "target_sha256": sha256(target),
            "target_is_seeded_derivative": derivative,
        })

    if (
        len(reader_assets) != EXPECTED_ASSETS
        or sum(len(payload) for payload in reader_assets.values()) != EXPECTED_TARGET_ASSET_BYTES
        or len(main.select("img[data-o006-asset-id]")) != EXPECTED_ASSETS
    ):
        raise RuntimeError("Lesson05 target asset census differs")
    for image in main.select("img[data-o006-asset-id]"):
        if str(image.get("src")) not in target_paths or not str(image.get("alt") or "").strip():
            raise RuntimeError("Lesson05 image route or Indonesian alternative differs")
    if any(str(node.get("href")) not in target_paths for node in main.select("a.lightbox[href]")):
        raise RuntimeError("Lesson05 target lightbox retains an unclosed route")
    return reader_assets, evidence


def load_lesson05() -> tuple[
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
            "segment_id", "document_id", "component_id", "section_id",
            "source_sha256", "source_text", "target_text", "status",
        ]
        if reader.fieldnames != expected_fields:
            raise RuntimeError("Lesson05 translation CSV schema differs")
        rows = list(reader)
    if len(rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson05 translation row count differs")
    bindings = parse_jsonl(BINDINGS.read_bytes(), "Lesson05 translation bindings")
    if len(bindings) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson05 translation binding count differs")

    soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("normalized Lesson05 main is missing")
    units = shared.stable_values(main, "data-o006-id")
    maths = shared.stable_values(main, "data-o006-math-id")
    if units != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson05 stable-unit sequence differs")
    if maths != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson05 math-ID sequence differs")
    source_math = [node.get_text() for node in main.select(".math")]
    nodes = shared.translatable_nodes(main)
    if len(nodes) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson05 translatable-node count differs")
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
            raise RuntimeError(f"Lesson05 translation binding differs: {sid}")
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
            raise RuntimeError(f"Lesson05 backend translation binding differs: {sid}")
        node.replace_with(NavigableString(target))

    correction_rows = corrections.apply_lesson05_corrections(main, rows)
    if len(correction_rows) != 31:
        raise RuntimeError("Lesson05 correction count differs")
    reader_assets, asset_evidence = load_asset_closure(main)

    shared.normalize_lesson(main, "Lesson05.html")
    if shared.stable_values(main, "data-o006-id") != units:
        raise RuntimeError("Lesson05 target stable-unit topology differs")
    if shared.stable_values(main, "data-o006-math-id") != maths:
        raise RuntimeError("Lesson05 target math topology differs")
    if len(main.select(".math")) != EXPECTED_MATH:
        raise RuntimeError("Lesson05 target math count differs")
    if shared.native_id_duplicates(main):
        raise RuntimeError("Lesson05 target retains duplicate native IDs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson05 target retains an executable/embed dependency")
    if "cdnapisec.kaltura.com" in str(main):
        raise RuntimeError("Lesson05 target retains the excluded Kaltura route")
    return main, rows, source_math, units, maths, correction_rows, reader_assets, asset_evidence


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lesson05 cumulative patch surface differs: {label}: {text.count(old)}")
    return text.replace(old, new, 1)


def patch_page(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            "partial: 6 of 14 documents complete; landing and Lessons 00–04",
            "partial: 7 of 14 documents complete; landing and Lessons 00–05",
            "metadata",
        ),
        (
            '<a href="Lesson04.html">Pelajaran 04</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson04.html">Pelajaran 04</a><a href="Lesson05.html">Pelajaran 05</a><a href="licenses/index.html">Lisensi</a>',
            "navigation",
        ),
        (
            "<strong>Edisi Bahasa Indonesia — 6 dari 14 dokumen.</strong>",
            "<strong>Edisi Bahasa Indonesia — 7 dari 14 dokumen.</strong>",
            "edition note",
        ),
        (
            "Laman utama serta Pelajaran 00–04 telah diterjemahkan sepenuhnya.",
            "Laman utama serta Pelajaran 00–05 telah diterjemahkan sepenuhnya.",
            "complete range",
        ),
        (
            "Pelajaran 05–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "Pelajaran 06–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.",
            "pending range",
        ),
        ("assets/reader-6of14.css", "assets/reader-7of14.css", "stylesheet"),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, f"{filename} {label}")
    if filename == "index.html":
        old_anchor = (
            '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0090" '
            'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson05" '
            'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        )
        new_anchor = (
            '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0090" '
            'data-translation-status="complete" href="Lesson05.html">'
        )
        text = replace_once(text, old_anchor, new_anchor, "index Lesson05 route")
        text = replace_once(
            text,
            "Estimasi Kemungkinan Maksimum (MLE) (Bagian II)",
            "Pendugaan Kemungkinan Maksimum (MLE) (Bagian II)",
            "index terminology",
        )
    return text.encode("utf-8")


def patch_license(payload: bytes) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<a href="../Lesson04.html">Pelajaran 04</a></nav>',
            '<a href="../Lesson04.html">Pelajaran 04</a><a href="../Lesson05.html">Pelajaran 05</a></nav>',
            "license navigation",
        ),
        ("../assets/reader-6of14.css", "../assets/reader-7of14.css", "license stylesheet"),
        (
            "serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, tujuh belas koreksi Lesson 03, dan tiga puluh lima koreksi Lesson 04 yang dicatat secara terpisah.",
            "serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, tujuh belas koreksi Lesson 03, tiga puluh lima koreksi Lesson 04, dan tiga puluh satu koreksi Lesson 05 yang dicatat secara terpisah.",
            "license corrections",
        ),
        (
            "Satu SVG pengajaran Lesson 04 dibekukan dari URL resmi; byte sumber dipertahankan dan salah label x₁/x₂ diperbaiki hanya pada aset turunan dengan catatan perubahan.",
            "Satu SVG pengajaran Lesson 04 dibekukan dari URL resmi; byte sumber dipertahankan dan salah label x₁/x₂ diperbaiki hanya pada aset turunan dengan catatan perubahan. Empat belas slot gambar Lesson 05 ditutup secara lokal: tiga belas mempertahankan byte sumber resmi dan satu histogram simulasi dibuat ulang secara deterministik dengan seed yang dicatat. Dua iframe Kaltura pihak ketiga tidak dibundel dan diganti dengan penjelasan statis lengkap.",
            "license Lesson05 assets",
        ),
        (
            "laman utama serta Pelajaran 00–04 lengkap; Pelajaran 05–12 belum diterjemahkan.",
            "laman utama serta Pelajaran 00–05 lengkap; Pelajaran 06–12 belum diterjemahkan.",
            "license status",
        ),
    )
    for old, new, label in replacements:
        text = replace_once(text, old, new, label)
    return text.encode("utf-8")


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in (
        "index.html", "Lesson00.html", "Lesson01.html", "Lesson02.html",
        "Lesson03.html", "Lesson04.html", "Lesson05.html",
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
        raise RuntimeError("replayed Lesson04 reader inventory differs")
    css = reader.pop(PRIOR_CSS, None)
    if (
        css is None
        or len(css) != 6_213
        or sha256(css) != "37fc52f724e0ea76443dc12ef243bf874ab6fb8c3c0640e03ab8cf1a6939f989"
    ):
        raise RuntimeError("responsive reader CSS differs")
    css += CODE_REFLOW_CSS
    reader[CURRENT_CSS] = css
    boldsymbol = load_mathjax_boldsymbol()
    boldsymbol_reader_path = PurePosixPath(
        "assets/MathJax/input/tex/extensions/boldsymbol.js"
    )
    if boldsymbol_reader_path in reader:
        raise RuntimeError("MathJax boldsymbol reader path already exists at Lesson04 boundary")
    reader[boldsymbol_reader_path] = boldsymbol

    target_outputs: dict[str, bytes] = {}
    document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson04_documents.jsonl"], "Lesson04 documents"
    )
    if len(document_rows) != 6:
        raise RuntimeError("Lesson04 document backend count differs")
    by_filename = {PurePosixPath(str(row["target_path"])).name: row for row in document_rows}
    prior_filenames = (
        "index.html", "Lesson00.html", "Lesson01.html",
        "Lesson02.html", "Lesson03.html", "Lesson04.html",
    )
    if set(by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson04 document backend filenames differ")
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
    ) = load_lesson05()
    base_lesson = prior.patch_page(
        prior.prior.page_document(main, COMPONENT_ID, SOURCE_URL), "Lesson05.html"
    )
    lesson_payload = patch_page(base_lesson, "Lesson05.html")
    reader[PurePosixPath("Lesson05.html")] = lesson_payload
    for path, payload in lesson_assets.items():
        if path in reader:
            raise RuntimeError(f"Lesson05 asset collides with prior reader: {path}")
        reader[path] = payload
    target_outputs["source/id-ID/Lesson05.html"] = lesson_payload
    target_math = [node.get_text() for node in main.select(".math")]

    document_rows = [by_filename[name] for name in prior_filenames]
    document_rows.append(shared.document_row(
        COMPONENT_ID,
        "Lesson05.html",
        DOCUMENT_ID,
        SOURCE_URL,
        source_math,
        target_math,
        lesson_payload,
        len(rows),
        len(unit_ids),
    ))
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math count differs")

    prior_corrections = parse_jsonl(
        prior_outputs["backend/through_lesson04_corrections.jsonl"], "Lesson04 corrections"
    )
    if len(prior_corrections) != 81 or len(fresh_corrections) != 31:
        raise RuntimeError("cumulative correction partition differs")
    correction_rows = prior_corrections + fresh_corrections
    if (
        len(correction_rows) != 112
        or [row["correction_id"] for row in correction_rows]
        != [f"O006-PSU-ADV-{i:04d}" for i in range(1, 113)]
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
        "schema": "o006.stat415.through-lesson05-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": [
                "index", "Lesson00", "Lesson01", "Lesson02",
                "Lesson03", "Lesson04", "Lesson05",
            ],
            "complete_count": 7,
            "corpus_document_count": 14,
            "next_document": "Lesson06",
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
            "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson04_count": len(prior_corrections),
            "lesson05_count": len(fresh_corrections),
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
        "lesson05_assets": {
            "count": len(lesson_assets),
            "bytes": sum(len(payload) for payload in lesson_assets.values()),
            "authority_slots": 14,
            "authority_bytes": 484_520,
            "seeded_derivatives": 1,
            "external_iframe_occurrences_removed": 2,
            "inventory": asset_evidence,
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lesson05 PNGs": "fourteen same-origin authority images frozen under the official page notice; thirteen target slots retain authority bytes and one simulation plot is a disclosed seeded derivative",
            "Lesson05 Kaltura iframe": "not bundled; third-party derivative/redistribution grant not established; complete static fallbacks retained",
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
        "runtime_closure": {
            "MathJax 3.1.2": {
                "freeze_receipt": identity(MATHJAX_RECEIPT),
                "url_manifest": identity(MATHJAX_MANIFEST),
                "added_autoload_dependency": {
                    "path": boldsymbol_reader_path.as_posix(),
                    "bytes": len(boldsymbol),
                    "sha256": sha256(boldsymbol),
                    "reason": "tex-svg autoloads the boldsymbol extension when source mathematics uses its macros",
                },
            },
        },
        "layout": {
            "reader_css_path": CURRENT_CSS.as_posix(),
            "reader_css_bytes": len(css),
            "reader_css_sha256": sha256(css),
            "rule": "responsive instructional-media reflow remains active for all translated documents",
        },
        "inputs": {
            "prior_build_receipt": identity(ROOT / "build" / "THROUGH_LESSON04_BUILD_RECEIPT.json"),
            "normalization": identity(NORMALIZATION_RECEIPT),
            "translation": identity(TRANSLATION_RECEIPT),
            "asset_closure": identity(ASSET_CLOSURE),
            "seeded_target_plot": identity(corrections.SEEDED_PLOT),
            "mathjax_freeze_receipt": identity(MATHJAX_RECEIPT),
            "mathjax_url_manifest": identity(MATHJAX_MANIFEST),
            "mathjax_boldsymbol": identity(MATHJAX_BOLDSYMBOL),
            "glossary": identity(GLOSSARY),
            "builder": identity(Path(__file__)),
            "correction_module": identity(ROOT / "scripts" / "lesson05_corrections.py"),
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
                raise RuntimeError(f"Lesson05 cumulative output differs: {relative_path}")
        actual_reader = shared.current_reader_files()
        if actual_reader != expected_reader:
            raise RuntimeError(
                "Lesson05 reader inventory differs: "
                f"extra={sorted(actual_reader - expected_reader)} "
                f"missing={sorted(expected_reader - actual_reader)}"
            )
        state = "verified"
    print(json.dumps({
        "mode": state,
        "documents": receipt["coverage"]["complete_count"],
        "segments": receipt["translation_segments"],
        "math_nodes": receipt["math_nodes"]["total"],
        "corrections": receipt["corrections"]["count"],
        "lesson05_assets": receipt["lesson05_assets"]["count"],
        "reader_files": receipt["reader"]["files"],
        "receipt_sha256": sha256(outputs[relative(RECEIPT)]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
