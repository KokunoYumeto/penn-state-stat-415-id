#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative STAT 415 Lesson 05 checkpoint.

The mature Lesson 03 publisher remains the transaction engine. This adapter
admits only the exact reader-first 7-of-14 package and can create a new version
only inside the existing Zenodo concept 10.5281/zenodo.22077422. It has no code
path that creates a new deposition/concept.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import publish_zenodo_through_lesson03 as prior


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
RELEASE = ROOT / "release"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON05_PACKAGE_RECEIPT.json"
DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-25_THROUGH_LESSON05.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-25_THROUGH_LESSON05.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-25_THROUGH_LESSON05.json"
LINEAGE = ROOT / "00_control" / "ZENODO_LINEAGE.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-25_THROUGH_LESSON05.json"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia (7 dari 14 Dokumen)"
VERSION = "2026.08.25.7of14"
PACKAGE_SCHEMA = "o006.stat415.through-lesson05-package.v1"
PUBLICATION_SCHEMA = "o006.stat415.zenodo-through-lesson05-publication.v1"
RELEASE_ROOT_SCHEMA = "o006.stat415.through-lesson05-release-root.v1"
FILES = (
    "00_stat415-id-through-lesson05-offline-reader.zip",
    "10_stat415-id-through-lesson05-source-backend.zip",
    "20_THROUGH_LESSON05_RELEASE_NOTES.md",
    "30_THROUGH_LESSON05_LICENSE.md",
    "40_THROUGH_LESSON05_QA_RECEIPT.json",
    "41_THROUGH_LESSON05_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON05_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON05.txt",
    "60_THROUGH_LESSON05_RELEASE_ROOT_RECEIPT.json",
)
ROOT_RECEIPT = FILES[-1]
COMPLETE_DOCUMENTS = (
    "index",
    "Lesson00",
    "Lesson01",
    "Lesson02",
    "Lesson03",
    "Lesson04",
    "Lesson05",
)
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"


def validate_release_root(inventory: list[dict[str, object]]) -> None:
    root_rows = [row for row in inventory if row.get("name") == ROOT_RECEIPT]
    if len(root_rows) != 1 or not isinstance(root_rows[0].get("payload"), bytes):
        raise RuntimeError("release root receipt snapshot is absent")
    value = json.loads(root_rows[0]["payload"].decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("release root receipt is not an object")
    covered = list(FILES[:-1])
    if (
        value.get("schema") != RELEASE_ROOT_SCHEMA
        or value.get("status") != "ready"
        or value.get("upload_order") != covered
        or value.get("file_count") != len(covered)
    ):
        raise RuntimeError("release root receipt has the wrong boundary or inventory")
    self_exclusion = value.get("self_exclusion")
    if not isinstance(self_exclusion, dict) or self_exclusion.get("filename") != ROOT_RECEIPT:
        raise RuntimeError("release root receipt does not declare its sole self-exclusion")
    expected = {str(row["name"]): row for row in inventory if row["name"] != ROOT_RECEIPT}
    rows = value.get("files")
    if not isinstance(rows, list):
        raise RuntimeError("release root receipt file inventory is absent")
    actual = {str(row.get("filename")): row for row in rows if isinstance(row, dict)}
    if set(actual) != set(covered) or len(rows) != len(covered):
        raise RuntimeError("release root receipt does not cover every other upload")
    for filename in covered:
        if (
            actual[filename].get("bytes") != expected[filename]["bytes"]
            or actual[filename].get("sha256") != expected[filename]["sha256"]
        ):
            raise RuntimeError(f"release root receipt identity differs: {filename}")
    if value.get("total_bytes") != sum(int(expected[name]["bytes"]) for name in covered):
        raise RuntimeError("release root receipt aggregate byte count differs")
    semantics = value.get("inventory_semantics")
    if not isinstance(semantics, dict):
        raise RuntimeError("release root receipt omits inventory semantics")
    manifest_semantics = semantics.get("release_manifest")
    checksum_semantics = semantics.get("sha256sums")
    root_semantics = semantics.get("root_receipt")
    if (
        not isinstance(manifest_semantics, dict)
        or manifest_semantics.get("covers") != list(FILES[:6])
        or manifest_semantics.get("excludes") != [FILES[6], FILES[7], ROOT_RECEIPT]
        or not isinstance(checksum_semantics, dict)
        or checksum_semantics.get("covers") != list(FILES[:7])
        or checksum_semantics.get("excludes") != [FILES[7], ROOT_RECEIPT]
        or not isinstance(root_semantics, dict)
        or root_semantics.get("covers") != covered
        or root_semantics.get("excludes") != [ROOT_RECEIPT]
    ):
        raise RuntimeError("release root receipt inventory semantics differ")


def local_inventory() -> tuple[list[dict[str, object]], dict[str, object]]:
    package = json.loads(PACKAGE_RECEIPT.read_text("utf-8"))
    if not isinstance(package, dict):
        raise RuntimeError("release package receipt is not an object")
    rows = package.get("files")
    coverage = package.get("coverage")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("upload_order") != list(FILES)
        or package.get("translation_provenance") != MODEL_PROVENANCE
        or not isinstance(rows, list)
        or not isinstance(coverage, dict)
    ):
        raise RuntimeError("release package receipt is not the admitted cumulative boundary")
    if (
        coverage.get("complete_count") != 7
        or coverage.get("corpus_document_count") != 14
        or coverage.get("complete_documents") != list(COMPLETE_DOCUMENTS)
        or coverage.get("next_document") != "Lesson06"
    ):
        raise RuntimeError("release package coverage is not exactly index plus Lessons 00–05")
    by_name = {str(row.get("filename")): row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(FILES) or len(rows) != len(FILES) or min(FILES, key=str.casefold) != FILES[0]:
        raise RuntimeError("release package file set is not exact and reader-first")
    release_root = RELEASE.resolve(strict=True)
    if RELEASE.is_symlink():
        raise RuntimeError("release directory may not be a symlink")
    inventory: list[dict[str, object]] = []
    snapshot_bytes = 0
    for filename in FILES:
        path = RELEASE / filename
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"release file missing: {filename}")
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(release_root)
        except ValueError as exc:
            raise RuntimeError(f"release file resolves outside release directory: {filename}") from exc
        size = resolved.stat().st_size
        snapshot_bytes += size
        if snapshot_bytes > 500_000_000:
            raise RuntimeError("release payload exceeds the 500 MB task cap")
        payload = resolved.read_bytes()
        if len(payload) != size:
            raise RuntimeError(f"release file changed while being snapshotted: {filename}")
        row = {
            "name": filename,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "md5": hashlib.md5(payload, usedforsecurity=False).hexdigest(),
            "payload": payload,
        }
        expected = by_name[filename]
        if row["bytes"] != expected.get("bytes") or row["sha256"] != expected.get("sha256"):
            raise RuntimeError(f"release file differs from package receipt: {filename}")
        inventory.append(row)
    validate_release_root(inventory)
    total_bytes = sum(int(row["bytes"]) for row in inventory)
    if package.get("file_count") != len(inventory) or package.get("total_bytes") != total_bytes:
        raise RuntimeError("release package aggregate counts differ")
    return inventory, coverage


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-25",
        "description": (
            "Checkpoint kumulatif yang substansial tetapi masih sebagian untuk rekonstruksi dan terjemahan "
            "Bahasa Indonesia (id-ID) rangkaian publik Penn State STAT 415, Introduction to Mathematical "
            "Statistics. Cakupan tepatnya adalah laman utama serta seluruh Pelajaran 00–05: 7 dari 14 "
            "dokumen lengkap, termasuk tinjauan peluang, statistik urutan, estimasi titik, kecukupan, "
            "keluarga eksponensial, metode momen, estimasi kemungkinan maksimum (MLE) analitik dan numerik, "
            "serta pengantar R. Berkas pertama adalah pembaca HTML luring; paket source-backend yang ringkas, "
            "manifes, checksum, lisensi komponen, serta bukti QA deterministik dan visual turut disertakan. "
            "Pelajaran 06–12 belum diterjemahkan dan tetap menaut ke sumber resmi berbahasa Inggris. Konten "
            "Penn State beserta adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan lain; MathJax 3.1.2 tetap "
            "Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. Koleksi komponen ini tidak direlisensi "
            "secara seragam, sehingga metadata agregat memakai other-open dan LICENSE.md menjadi pernyataan "
            "hak yang mengikat. Byte sumber resmi tidak diubah. Provenans terjemahan: "
            f"{MODEL_PROVENANCE}. Seluruh kredit sumber dan kontributor manusia dipertahankan. Tidak ada "
            "dukungan atau pengesahan oleh Penn State yang tersirat."
        ),
        "creators": [{"name": "Penn State Department of Statistics"}],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia",
            "id-ID",
            "mathematical statistics",
            "statistika matematis",
            "order statistics",
            "statistik urutan",
            "point estimation",
            "sufficient statistics",
            "method of moments",
            "maximum likelihood estimation",
            "numerical optimization",
            "R programming",
            "sampling distributions",
            "open educational resources",
            "offline HTML",
            "machine-readable curriculum",
            "AI translation",
            "partial edition",
        ],
        "language": "ind",
        "version": VERSION,
        "related_identifiers": [
            {
                "identifier": "https://online.stat.psu.edu/stat415/",
                "relation": "isDerivedFrom",
                "resource_type": "publication-other",
                "scheme": "url",
            },
            {
                "identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
                "relation": "isSupplementedBy",
                "resource_type": "software",
                "scheme": "url",
            },
        ],
    }


def configure_engine() -> None:
    values = {
        "TOKEN_FILE": TOKEN_FILE,
        "RELEASE": RELEASE,
        "PACKAGE_RECEIPT": PACKAGE_RECEIPT,
        "DEFAULT_RECEIPT": DEFAULT_RECEIPT,
        "READBACK_RECEIPT": READBACK_RECEIPT,
        "AUDIT_RECEIPT": AUDIT_RECEIPT,
        "LINEAGE": LINEAGE,
        "DRAFT_MARKER": DRAFT_MARKER,
        "CONCEPT_RECORD_ID": CONCEPT_RECORD_ID,
        "CONCEPT_DOI": CONCEPT_DOI,
        "TITLE": TITLE,
        "VERSION": VERSION,
        "PACKAGE_SCHEMA": PACKAGE_SCHEMA,
        "FILES": FILES,
        "ROOT_RECEIPT": ROOT_RECEIPT,
        "COMPLETE_DOCUMENTS": COMPLETE_DOCUMENTS,
        "MODEL_PROVENANCE": MODEL_PROVENANCE,
    }
    for name, value in values.items():
        setattr(prior.engine, name, value)
    prior.engine.validate_release_root = validate_release_root
    prior.engine.local_inventory = local_inventory
    prior.engine.metadata = metadata


def configure_prior_adapter() -> None:
    values = {
        "TOKEN_FILE": TOKEN_FILE,
        "RELEASE": RELEASE,
        "PACKAGE_RECEIPT": PACKAGE_RECEIPT,
        "DEFAULT_RECEIPT": DEFAULT_RECEIPT,
        "READBACK_RECEIPT": READBACK_RECEIPT,
        "AUDIT_RECEIPT": AUDIT_RECEIPT,
        "LINEAGE": LINEAGE,
        "DRAFT_MARKER": DRAFT_MARKER,
        "CONCEPT_RECORD_ID": CONCEPT_RECORD_ID,
        "CONCEPT_DOI": CONCEPT_DOI,
        "TITLE": TITLE,
        "VERSION": VERSION,
        "PACKAGE_SCHEMA": PACKAGE_SCHEMA,
        "PUBLICATION_SCHEMA": PUBLICATION_SCHEMA,
        "RELEASE_ROOT_SCHEMA": RELEASE_ROOT_SCHEMA,
        "FILES": FILES,
        "ROOT_RECEIPT": ROOT_RECEIPT,
        "COMPLETE_DOCUMENTS": COMPLETE_DOCUMENTS,
        "MODEL_PROVENANCE": MODEL_PROVENANCE,
    }
    for name, value in values.items():
        setattr(prior, name, value)
    prior.validate_release_root = validate_release_root
    prior.local_inventory = local_inventory
    prior.metadata = metadata
    prior.configure_engine = configure_engine


def main() -> None:
    configure_prior_adapter()
    prior.main()


if __name__ == "__main__":
    main()
