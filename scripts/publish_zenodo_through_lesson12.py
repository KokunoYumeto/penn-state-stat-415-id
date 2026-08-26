#!/usr/bin/env python3
"""Publish and anonymously verify the complete 14-document STAT 415 component.

This bounded adapter can create only a new version inside the existing Zenodo
concept 10.5281/zenodo.22077422.  Importing, compiling, or invoking
``--local-preflight`` neither reads the credential nor accesses the network.
The transaction engine publishes the version, anonymously reads back and
hashes every public file, and supports a separate authenticated lineage audit
that hard-fails any surviving draft in the concept.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import publish_zenodo_through_lesson05 as engine


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
RELEASE = ROOT / "release"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON12_PACKAGE_RECEIPT.json"
DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-26_THROUGH_LESSON12.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-26_THROUGH_LESSON12.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-26_THROUGH_LESSON12.json"
LINEAGE = ROOT / "00_control" / "ZENODO_LINEAGE.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-26_THROUGH_LESSON12.json"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia Lengkap"
VERSION = "2026.08.26.14of14"
PACKAGE_SCHEMA = "o006.stat415.through-lesson12-package.v1"
PUBLICATION_SCHEMA = "o006.stat415.zenodo-through-lesson12-publication.v1"
RELEASE_ROOT_SCHEMA = "o006.stat415.through-lesson12-release-root.v1"
FILES = (
    "00_stat415-id-through-lesson12-offline-reader.zip",
    "10_stat415-id-through-lesson12-source-backend.zip",
    "20_THROUGH_LESSON12_RELEASE_NOTES.md",
    "30_THROUGH_LESSON12_LICENSE.md",
    "40_THROUGH_LESSON12_QA_RECEIPT.json",
    "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON12.txt",
    "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json",
)
ROOT_RECEIPT = FILES[-1]
COMPLETE_DOCUMENTS = ("index", *[f"Lesson{i:02d}" for i in range(13)])
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

# These constants bind this publisher to the final, independently verified
# package.  The package-receipt hash transitively binds all nine uploads; the
# manifest and cryptographic-root identities are repeated as explicit gates.
EXPECTED_PACKAGE_RECEIPT_BYTES = 4_428
EXPECTED_PACKAGE_RECEIPT_SHA256 = "1d1fda56a6cb0368615a8ccc81af2f7d95109e50ee405196493a02727fa7b503"
EXPECTED_RELEASE_MANIFEST_BYTES = 854
EXPECTED_RELEASE_MANIFEST_SHA256 = "63844453a55f41003f977d064f016852e00aca0ae71b1e9848c16c59ed2902e5"
EXPECTED_RELEASE_ROOT_BYTES = 4_763
EXPECTED_RELEASE_ROOT_SHA256 = "664bcd32fb9bd0692217056ab54735a27f7423645f6ffb1ad28dc7e42464fec0"
EXPECTED_TOTAL_BYTES = 55_308_347
EXPECTED_RELEASE_IDENTITIES = {
    "00_stat415-id-through-lesson12-offline-reader.zip": (17_648_138, "e6c5829452e9d023ae7c54e802673a0e1fb0ddf220716d8f5156f1169ecb01e1"),
    "10_stat415-id-through-lesson12-source-backend.zip": (37_616_984, "3ff417044f3334130f3e039c2be8997ca927b49578b568e6d5ce2f1277ca6e46"),
    "20_THROUGH_LESSON12_RELEASE_NOTES.md": (1_213, "7db90c69118f75e41fef99d0ddd0704471710ff97b1b58957aa8e86a0b36f339"),
    "30_THROUGH_LESSON12_LICENSE.md": (1_515, "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d"),
    "40_THROUGH_LESSON12_QA_RECEIPT.json": (12_428, "e64f9dc9ef3eb041287b0c88be48c1dc6a4833000651cbdceed2185a1999bd19"),
    "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json": (21_702, "5dd1dd0ddfa4249ef08f2a70f070a8fc8532734656cd146ec5235c37a8baa345"),
    "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv": (854, "63844453a55f41003f977d064f016852e00aca0ae71b1e9848c16c59ed2902e5"),
    "SHA256SUMS_THROUGH_LESSON12.txt": (750, "a85f942017f17d558daf3b2ab681e5c0e05c34aa35cdfa2d00e7d283edc30b60"),
    "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json": (4_763, "664bcd32fb9bd0692217056ab54735a27f7423645f6ffb1ad28dc7e42464fec0"),
}

BASE_LOCAL_INVENTORY = engine.local_inventory


def exact_identity(path: Path, expected_bytes: int, expected_sha256: str, label: str) -> None:
    payload = path.read_bytes()
    if len(payload) != expected_bytes or hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise RuntimeError(f"{label} differs from the frozen complete-package identity")


def local_inventory() -> tuple[list[dict[str, object]], dict[str, object]]:
    exact_identity(
        PACKAGE_RECEIPT,
        EXPECTED_PACKAGE_RECEIPT_BYTES,
        EXPECTED_PACKAGE_RECEIPT_SHA256,
        "package receipt",
    )
    inventory, coverage = BASE_LOCAL_INVENTORY()
    exact_identity(
        PACKAGE_RECEIPT,
        EXPECTED_PACKAGE_RECEIPT_BYTES,
        EXPECTED_PACKAGE_RECEIPT_SHA256,
        "package receipt after snapshot",
    )
    actual = {str(row["name"]): (int(row["bytes"]), str(row["sha256"])) for row in inventory}
    if actual != EXPECTED_RELEASE_IDENTITIES:
        raise RuntimeError("release inventory differs from the hard-bound complete package")
    if len(inventory) != len(FILES) or sum(int(row["bytes"]) for row in inventory) != EXPECTED_TOTAL_BYTES:
        raise RuntimeError("release package aggregate identity differs")
    exact_identity(
        RELEASE / FILES[6],
        EXPECTED_RELEASE_MANIFEST_BYTES,
        EXPECTED_RELEASE_MANIFEST_SHA256,
        "release manifest",
    )
    exact_identity(
        RELEASE / ROOT_RECEIPT,
        EXPECTED_RELEASE_ROOT_BYTES,
        EXPECTED_RELEASE_ROOT_SHA256,
        "release root receipt",
    )
    return inventory, coverage


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-26",
        "description": (
            "Edisi lengkap Bahasa Indonesia (id-ID) dari seluruh rangkaian publik Penn State STAT 415, "
            "Introduction to Mathematical Statistics: laman utama serta Pelajaran 00–12, 14 dari 14 dokumen. "
            "Cakupan meliputi tinjauan peluang, statistik urutan, estimasi, kecukupan, metode momen, estimasi "
            "kemungkinan maksimum, selang kepercayaan, informasi Fisher, asimtotik kemungkinan, bootstrap, "
            "metode delta, pengujian hipotesis, daya uji, nilai-p, metode Bayesian, dan regresi linear sederhana. "
            "Berkas pertama adalah pembaca HTML luring lengkap; paket source-backend, manifes, checksum, lisensi "
            "komponen, serta bukti build, QA deterministik, dan QA visual turut disertakan. Status lengkap hanya "
            "berlaku untuk komponen Penn State 14 dokumen ini; donor kelengkapan dan pendamping orisinal C140 "
            "merupakan komponen terpisah. Konten Penn State beserta adaptasinya tetap CC BY-NC 4.0 kecuali "
            "dinyatakan lain; MathJax 3.1.2 tetap Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. "
            "Koleksi komponen tidak direlisensi secara seragam, sehingga metadata agregat memakai other-open "
            "dan LICENSE menjadi pernyataan hak yang mengikat. Byte sumber resmi tidak diubah. Provenans "
            f"terjemahan: {MODEL_PROVENANCE}. Seluruh kredit sumber dan kontributor manusia dipertahankan. "
            "Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat."
        ),
        "creators": [{"name": "Penn State Department of Statistics"}],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia", "id-ID", "mathematical statistics", "statistika matematis",
            "order statistics", "estimation", "sufficient statistics", "maximum likelihood estimation",
            "Fisher information", "asymptotic inference", "bootstrap", "delta method",
            "hypothesis testing", "power analysis", "Bayesian methods", "simple linear regression",
            "open educational resources", "offline HTML", "machine-readable curriculum",
            "AI translation", "complete Penn State component",
        ],
        "language": "ind",
        "version": VERSION,
        "related_identifiers": [
            {"identifier": "https://online.stat.psu.edu/stat415/", "relation": "isDerivedFrom", "resource_type": "publication-other", "scheme": "url"},
            {"identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id", "relation": "isSupplementedBy", "resource_type": "software", "scheme": "url"},
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
        "EXPECTED_COMPLETE_COUNT": 14,
        "NEXT_DOCUMENT": None,
    }
    for name, value in values.items():
        setattr(engine, name, value)
    engine.metadata = metadata
    engine.local_inventory = local_inventory


def main() -> None:
    configure()
    engine.main()


if __name__ == "__main__":
    main()
