#!/usr/bin/env python3
"""Publish and anonymously verify the 11-of-14 STAT 415 checkpoint."""

from pathlib import Path

import publish_zenodo_through_lesson05 as engine


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
RELEASE = ROOT / "release"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON09_PACKAGE_RECEIPT.json"
DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-25_THROUGH_LESSON09.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-25_THROUGH_LESSON09.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-25_THROUGH_LESSON09.json"
LINEAGE = ROOT / "00_control" / "ZENODO_LINEAGE.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-25_THROUGH_LESSON09.json"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia (11 dari 14 Dokumen)"
VERSION = "2026.08.25.11of14"
PACKAGE_SCHEMA = "o006.stat415.through-lesson09-package.v1"
PUBLICATION_SCHEMA = "o006.stat415.zenodo-through-lesson09-publication.v1"
RELEASE_ROOT_SCHEMA = "o006.stat415.through-lesson09-release-root.v1"
FILES = (
    "00_stat415-id-through-lesson09-offline-reader.zip",
    "10_stat415-id-through-lesson09-source-backend.zip",
    "20_THROUGH_LESSON09_RELEASE_NOTES.md",
    "30_THROUGH_LESSON09_LICENSE.md",
    "40_THROUGH_LESSON09_QA_RECEIPT.json",
    "41_THROUGH_LESSON09_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON09_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON09.txt",
    "60_THROUGH_LESSON09_RELEASE_ROOT_RECEIPT.json",
)
ROOT_RECEIPT = FILES[-1]
COMPLETE_DOCUMENTS = ("index", *[f"Lesson{i:02d}" for i in range(10)])
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-25",
        "description": (
            "Checkpoint kumulatif substansial tetapi masih sebagian untuk rekonstruksi dan terjemahan "
            "Bahasa Indonesia (id-ID) rangkaian publik Penn State STAT 415, Introduction to Mathematical "
            "Statistics. Cakupan tepatnya adalah laman utama serta seluruh Pelajaran 00–09: 11 dari 14 "
            "dokumen lengkap. Materinya meliputi tinjauan peluang, statistik urutan, pendugaan titik dan "
            "selang, kecukupan, keluarga eksponensial, metode momen, pendugaan kemungkinan maksimum, "
            "distribusi asimtotik, informasi Fisher, bootstrap parametrik dan nonparametrik, metode delta, "
            "serta pengujian hipotesis untuk proporsi dan satu rata-rata. Berkas pertama adalah pembaca "
            "HTML luring; paket source-backend, manifes, checksum, lisensi komponen, dan bukti QA "
            "deterministik serta visual turut disertakan. Pelajaran 10–12 belum diterjemahkan dan tetap "
            "menaut ke sumber resmi berbahasa Inggris. Konten Penn State beserta adaptasinya tetap "
            "CC BY-NC 4.0 kecuali dinyatakan lain; MathJax 3.1.2 tetap Apache-2.0; lapisan asli repositori "
            "tetap CC BY-SA 4.0. Koleksi tidak direlisensi secara seragam, sehingga metadata agregat "
            "memakai other-open dan LICENSE.md menjadi pernyataan hak yang mengikat. Byte sumber resmi "
            f"tidak diubah. Provenans terjemahan: {MODEL_PROVENANCE}. Seluruh kredit sumber dan "
            "kontributor manusia dipertahankan. Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat."
        ),
        "creators": [{"name": "Penn State Department of Statistics"}],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia", "id-ID", "mathematical statistics", "statistika matematis",
            "maximum likelihood estimation", "Fisher information", "asymptotic inference",
            "bootstrap", "delta method", "hypothesis testing", "open educational resources",
            "offline HTML", "machine-readable curriculum", "AI translation", "partial edition",
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


def configure() -> None:
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
        "EXPECTED_COMPLETE_COUNT": 11,
        "NEXT_DOCUMENT": "Lesson10",
    }
    for name, value in values.items():
        setattr(engine, name, value)
    engine.metadata = metadata


def main() -> None:
    configure()
    engine.main()


if __name__ == "__main__":
    main()
