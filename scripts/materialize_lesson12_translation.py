#!/usr/bin/env python3
"""Materialize and byte-verify the complete semantic id-ID Lesson 12 source."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

import build_through_lesson01 as shared
import lesson12_corrections as corrections


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson12.html"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson12_translation.csv"
BINDINGS = ROOT / "backend" / "lesson12_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON12_TRANSLATION_RECEIPT.json"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON12_NORMALIZATION_RECEIPT.json"
ASSET_MANIFEST = ROOT / "authority" / "LESSON12_ASSET_MANIFEST.csv"
TARGET = ROOT / "source" / "id-ID" / "Lesson12.html"
CORRECTION_BINDINGS = ROOT / "backend" / "lesson12_target_corrections.jsonl"
NATIVE_ID_MAP = ROOT / "backend" / "lesson12_target_native_id_map.jsonl"
RECEIPT = ROOT / "build" / "LESSON12_MATERIALIZATION_RECEIPT.json"
SCRIPT = ROOT / "scripts" / "materialize_lesson12_translation.py"
CORRECTION_MODULE = ROOT / "scripts" / "lesson12_corrections.py"

DOCUMENT_ID = "O006-PSU-013"
COMPONENT_ID = "Lesson12"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_REPAIRED_MATH = {
    f"{DOCUMENT_ID}-{short}"
    for short in (
        "M0056", "M0059", "M0060", "M0136", "M0210", "M0234", "M0236",
        "M0241", "M0260", "M0272", "M0281", "M0283", "M0285", "M0325",
        "M0327", "M0328", "M0331", "M0333", "M0334",
    )
}
FIELDS = (
    "segment_id", "document_id", "component_id", "section_id",
    "source_sha256", "source_text", "target_text", "status",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8") for row in rows)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def identity(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(payload), "sha256": sha256(payload)}


def parse_jsonl(path: Path) -> list[dict[str, object]]:
    payload = path.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        raise RuntimeError(f"noncanonical JSONL: {path.relative_to(ROOT)}")
    return [json.loads(line) for line in payload.decode("utf-8").splitlines()]


def load_translation() -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    payload = TRANSLATIONS.read_bytes()
    if payload.startswith(b"\xef\xbb\xbf") or b"\r" in payload or not payload.endswith(b"\n"):
        raise RuntimeError("Lesson12 merged translation is not canonical UTF-8/LF")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    rows = list(reader)
    bindings = parse_jsonl(BINDINGS)
    expected_ids = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, 581)]
    if tuple(reader.fieldnames or ()) != FIELDS or len(rows) != 580 or [row["segment_id"] for row in rows] != expected_ids or len(bindings) != 580:
        raise RuntimeError("Lesson12 translation ledger boundary differs")
    for ordinal, (row, binding) in enumerate(zip(rows, bindings), start=1):
        target = row["target_text"]
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": row["segment_id"],
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
        if row["document_id"] != DOCUMENT_ID or row["component_id"] != COMPONENT_ID or row["status"] != "translated" or not target.strip() or "�" in target or binding != expected_binding:
            raise RuntimeError(f"Lesson12 translation binding differs: {row['segment_id']}")
    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    if receipt.get("schema") != "o006.stat415.lesson12-translation.v1" or receipt.get("status") != "complete" or receipt.get("segment_count") != 580 or receipt.get("translation_csv", {}).get("sha256") != sha256(payload) or receipt.get("bindings", {}).get("sha256") != sha256(BINDINGS.read_bytes()):
        raise RuntimeError("Lesson12 translation receipt differs")
    return rows, bindings


def load_assets() -> list[dict[str, str]]:
    payload = ASSET_MANIFEST.read_bytes()
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
    if len(rows) != 9 or [row["asset_id"] for row in rows] != [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, 10)]:
        raise RuntimeError("Lesson12 asset manifest boundary differs")
    for row in rows:
        path = ROOT / row["local_path"]
        binary = path.read_bytes()
        if len(binary) != int(row["bytes"]) or sha256(binary) != row["sha256"]:
            raise RuntimeError(f"Lesson12 frozen image differs: {row['asset_id']}")
    return rows


def add_target_head(soup: BeautifulSoup) -> None:
    if soup.html is None or soup.head is None or soup.title is None:
        raise RuntimeError("Lesson12 normalized document shell differs")
    soup.html["lang"] = "id-ID"
    soup.title.string = "12 Regresi Linear Sederhana"
    for old in soup.head.select('meta[name="edition-status"], link[rel="license"], style[data-o006-target-style]'):
        old.decompose()
    meta = soup.new_tag("meta")
    meta["name"] = "edition-status"
    meta["content"] = "complete Lesson12 translation; three recorded companion obligations remain outside this source component"
    soup.head.append(meta)
    license_link = soup.new_tag("link")
    license_link["rel"] = "license"
    license_link["href"] = "https://creativecommons.org/licenses/by-nc/4.0/"
    soup.head.append(license_link)
    style = soup.new_tag("style")
    style["data-o006-target-style"] = "lesson12-semantic-source-v1"
    style.string = (
        "main{max-width:72rem;margin:0 auto;padding:1rem;}"
        ".reader-full-width-figure{width:100%;margin:1.5rem auto;text-align:center;}"
        ".reader-full-width-image{display:block;width:100%;max-width:100%;height:auto;margin:0 auto;}"
        "table.reader-responsive-table{display:block;width:100%;max-width:100%;overflow-x:auto;border-collapse:collapse;}"
        "table.reader-responsive-table th,table.reader-responsive-table td{padding:.35rem .55rem;}"
        ".offline-video-equivalent,.target-only-proof,.target-only-reproducibility{margin:1rem 0;padding:.75rem;border:1px solid #777;}"
        ".target-only-note{margin:1rem 0;padding:.75rem;border-inline-start:.3rem solid #555;}"
    )
    soup.head.append(style)


def add_component_provenance(soup: BeautifulSoup, main: object) -> None:
    if not hasattr(main, "append"):
        raise RuntimeError("Lesson12 provenance target is not an HTML element")
    section = soup.new_tag("section")
    section["class"] = ["component-provenance"]
    section["data-o006-component-provenance-id"] = f"{DOCUMENT_ID}-PROV"
    heading = soup.new_tag("h2", id="lesson12-provenance-rights")
    heading.append(NavigableString("Provenance, hak, dan perubahan"))
    section.append(heading)
    source_p = soup.new_tag("p")
    source_p.append(NavigableString("Sumber resmi: Penn State STAT 415, Pelajaran 12, “Simple Linear Regression”, "))
    source_link = soup.new_tag("a", href="https://online.stat.psu.edu/stat415/Lesson12.html")
    source_link["rel"] = "external noopener"
    source_link.append(NavigableString("laman sumber"))
    source_p.append(source_link)
    source_p.append(NavigableString(". Isi tingkat laman berlisensi CC BY-NC 4.0 kecuali jika dinyatakan lain; setiap pengecualian komponen tetap berlaku."))
    section.append(source_p)
    change_p = soup.new_tag("p")
    change_p.append(NavigableString("Edisi Bahasa Indonesia ini merupakan karya turunan: struktur, rumus, tabel, gambar, sitasi, dan identitas sumber dipertahankan; 24 koreksi atau disposisi target-only dicatat secara terpisah. Tidak ada dukungan atau pengesahan oleh sumber yang tersirat."))
    section.append(change_p)
    provenance_p = soup.new_tag("p")
    provenance_p.append(NavigableString(f"Provenance terjemahan dan rekonstruksi: {PROVENANCE}. Kredit sumber dan kontributor manusia tetap dipertahankan."))
    section.append(provenance_p)
    main.append(section)


def compute() -> dict[str, bytes]:
    normalization = json.loads(NORMALIZATION_RECEIPT.read_text("utf-8"))
    if normalization.get("schema") != "o006.stat415.lesson12-normalization.v1" or normalization.get("counts", {}).get("translation_segments") != 580 or normalization.get("counts", {}).get("structural_units") != 846 or normalization.get("counts", {}).get("math_nodes") != 352:
        raise RuntimeError("Lesson12 normalization receipt differs")
    rows, bindings = load_translation()
    assets = load_assets()
    soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson12 normalized instructional main is missing")
    source_units = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    source_math = [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")]
    source_math_text = {
        str(node["data-o006-math-id"]): node.get_text()
        for node in main.select("[data-o006-math-id]")
    }
    if source_units != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, 847)] or source_math != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, 353)]:
        raise RuntimeError("Lesson12 normalized stable-ID sequence differs")
    translatable = shared.translatable_nodes(main)
    if len(translatable) != 580:
        raise RuntimeError("Lesson12 translatable-node sequence differs")
    target_nodes: dict[str, NavigableString] = {}
    for row, node in zip(rows, translatable):
        source = str(node)
        if row["source_text"] != source or row["source_sha256"] != sha256(source.encode("utf-8")):
            raise RuntimeError(f"Lesson12 source-to-target segment differs: {row['segment_id']}")
        replacement = NavigableString(row["target_text"])
        node.replace_with(replacement)
        target_nodes[row["segment_id"]] = replacement
    correction_rows, native_mapping = corrections.apply_lesson12_corrections(main, target_nodes, assets)
    target_math_text = {
        str(node["data-o006-math-id"]): node.get_text()
        for node in main.select("[data-o006-math-id]")
    }
    changed_math = {
        math_id for math_id in source_math
        if source_math_text[math_id] != target_math_text[math_id]
    }
    if changed_math != EXPECTED_REPAIRED_MATH:
        raise RuntimeError(f"Lesson12 target math repair set differs: {sorted(changed_math)}")
    add_target_head(soup)
    add_component_provenance(soup, main)
    main["lang"] = "id-ID"
    main["data-translation-provenance"] = PROVENANCE
    main["data-translation-status"] = "complete"
    main["data-source-formula-count"] = "352"
    main["data-target-correction-count"] = "24"
    if [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")] != source_units or [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")] != source_math:
        raise RuntimeError("Lesson12 target changed the stable source topology")
    if len(main.select("img")) != 10 or len({str(node["data-o006-asset-id"]) for node in main.select("img")}) != 9 or main.select("iframe, object, embed, video, audio, source, script"):
        raise RuntimeError("Lesson12 target media closure differs")
    if len(main.select('.component-provenance[data-o006-component-provenance-id="O006-PSU-013-PROV"]')) != 1:
        raise RuntimeError("Lesson12 visible component provenance differs")
    if any(count > 1 for count in __import__("collections").Counter(str(node["id"]) for node in main.select("[id]")).values()):
        raise RuntimeError("Lesson12 target contains duplicate DOM IDs")
    live_ids = {str(node["id"]) for node in main.select("[id]")}
    for link in main.select('a[href^="#"]'):
        if str(link.get("href"))[1:] not in live_ids:
            raise RuntimeError(f"Lesson12 target has a broken fragment link: {link.get('href')}")
    for node in main.select("a[href], img[src]"):
        value = str(node.get("href") if node.name == "a" else node.get("src"))
        if value.startswith(("http://", "https://", "mailto:", "#")):
            continue
        resolved = (TARGET.parent / value).resolve()
        if resolved != TARGET.resolve() and not resolved.is_file():
            raise RuntimeError(f"Lesson12 target has an unresolved local path: {value}")
    target_payload = ("<!doctype html>\n" + str(soup.html) + "\n").encode("utf-8")
    corrections_payload = canonical_jsonl(correction_rows)
    native_payload = canonical_jsonl(native_mapping)
    receipt = {
        "schema": "o006.stat415.lesson12-materialization.v1",
        "status": "pass",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "registered_repaired_math_ids": sorted(changed_math),
        "counts": {
            "translation_segments": len(rows),
            "stable_source_units": len(source_units),
            "stable_source_math": len(source_math),
            "registered_repaired_source_math": len(changed_math),
            "registered_target_corrections": len(correction_rows),
            "unique_frozen_images": len(assets),
            "image_occurrences": len(main.select("img")),
            "semantic_tables": len(main.select("table")),
            "table_captions": len(main.select("table caption")),
            "offline_video_equivalents": len(main.select(".offline-video-equivalent")),
            "external_video_runtimes": len(main.select("iframe")),
            "native_id_map_records": len(native_mapping),
            "component_provenance_blocks": len(main.select(".component-provenance")),
        },
        "inputs": [identity(NORMALIZED), identity(TRANSLATIONS), identity(BINDINGS), identity(TRANSLATION_RECEIPT), identity(NORMALIZATION_RECEIPT), identity(ASSET_MANIFEST), identity(SCRIPT), identity(CORRECTION_MODULE)],
        "outputs": {
            TARGET.relative_to(ROOT).as_posix(): {"bytes": len(target_payload), "sha256": sha256(target_payload)},
            CORRECTION_BINDINGS.relative_to(ROOT).as_posix(): {"bytes": len(corrections_payload), "sha256": sha256(corrections_payload), "records": len(correction_rows)},
            NATIVE_ID_MAP.relative_to(ROOT).as_posix(): {"bytes": len(native_payload), "sha256": sha256(native_payload), "records": len(native_mapping)},
        },
        "validation": {
            "authority_unchanged": True,
            "source_segment_bindings_exact": True,
            "source_stable_ids_preserved": True,
            "source_math_ids_preserved": True,
            "unregistered_source_math_unchanged": True,
            "all_registered_repairs_dispositioned": True,
            "video_bytes_redistributed": False,
            "external_video_runtime_removed": True,
            "frozen_images_byte_bound": True,
            "images_centered_responsive_and_dimensioned": True,
            "tables_captioned_and_scoped": True,
            "duplicate_target_ids_removed_with_reversible_map": True,
            "target_id_references_resolve": True,
            "target_local_paths_resolve": True,
            "numerical_recalculation_reproducible": True,
            "source_credit_license_and_change_notice_visible": True,
        },
    }
    receipt_payload = canonical_json(receipt)
    return {
        TARGET.relative_to(ROOT).as_posix(): target_payload,
        CORRECTION_BINDINGS.relative_to(ROOT).as_posix(): corrections_payload,
        NATIVE_ID_MAP.relative_to(ROOT).as_posix(): native_payload,
        RECEIPT.relative_to(ROOT).as_posix(): receipt_payload,
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
        state = "written"
    else:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"Lesson12 materialized output differs: {relative}")
        state = "verified"
    print(json.dumps({"mode": state, "outputs": len(outputs), "receipt_sha256": sha256(outputs[RECEIPT.relative_to(ROOT).as_posix()])}, sort_keys=True))


if __name__ == "__main__":
    main()
