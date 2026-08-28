#!/usr/bin/env python3
"""Publish the cumulative C140 original-companion C1 Zenodo boundary.

This is a narrow adapter over the already hardened Random-completeness Zenodo
publisher.  It pins the only deposition-creation request to
``POST /api/deposit/depositions/22143454/actions/newversion``.  That operation
must inherit the 25 files of public version
``2026.08.28.c140-random-completeness`` byte-for-byte; only the eight C1
additions are uploaded.  No file is deleted or replaced.

``--local-preflight`` is credential- and network-free.  Publication and
lineage audit use the existing non-browser API implementation, followed by
anonymous full-byte readback and an authenticated zero-draft audit.  This
module never launches a browser.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import publish_zenodo_random_completeness as _engine


ROOT = Path(__file__).resolve().parents[1]
BASE_RECORD_ID = "22143454"
BASE_VERSION = "2026.08.28.c140-random-completeness"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
VERSION = "2026.08.28.c140-companion-c1"
TITLE = (
    "O006/C140 Statistika Matematis — STAT 415, Random, dan Pendamping "
    "Orisinal C1 (Bahasa Indonesia)"
)
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C1_RELEASE_PACKAGE_RECEIPT.json"
PUBLICATION_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-28_C140_COMPANION_C1.json"
)
READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-28_C140_COMPANION_C1.json"
)
BASE_READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_BASE_READBACK_2026-08-28_C140_COMPANION_C1.json"
)
AUDIT_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-28_C140_COMPANION_C1.json"
)
DRAFT_MARKER = (
    ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-28_C140_COMPANION_C1.json"
)
LINEAGE_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_2026-08-28_C140_COMPANION_C1.json"
)

PACKAGE_SCHEMA = "o006.c140.companion-c1-release-package.v1"
PUBLICATION_SCHEMA = "o006.c140.zenodo-c140-companion-c1-publication.v1"
MARKER_SCHEMA = "o006.c140.zenodo-c140-companion-c1-draft-marker.v1"
LINEAGE_SCHEMA = "o006.c140.zenodo-c140-companion-c1-lineage.v1"
BASE_READBACK_SCHEMA = "o006.c140.zenodo-base-readback-c140-companion-c1.v1"
USER_AGENT = "O006-C140-companion-c1/2026.08.28"
MAX_RELEASE_BYTES = 500_000_000

# Exact public inventory of record 22143454.  These are inherited, never
# uploaded, replaced, or deleted by this adapter.
BASE_SPECS = (
    ("00_00_stat415-pengantar-statistika-matematis-id.pdf", 20_170_549,
     "f39c1c438cc3e793fe9522eb11f5b02704d89fcdc7aecb2207a599087d458964"),
    ("00_01_stat415-pengantar-statistika-matematis-id.epub", 12_301_415,
     "e122d65348971b91a5ac0c7a8219e0fa3e0eabedb92d130c661648e399e3c574"),
    ("20_COMPLETE_CONSOLIDATED_READERS_RELEASE_NOTES.md", 1_142,
     "c7f8f330bf0db8400eb7f164be3b9c9e5bc9ab4b0f8a72638e949be095b41f40"),
    ("30_COMPLETE_CONSOLIDATED_READERS_LICENSE.md", 1_515,
     "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d"),
    ("40_COMPLETE_CONSOLIDATED_READERS_QA_EVIDENCE.zip", 44_505,
     "bdfb9612b64c9a5280d6533b6bf756fd07b7fea0a85755e01d5d69994546945d"),
    ("00_stat415-id-through-lesson12-offline-reader.zip", 17_648_138,
     "e6c5829452e9d023ae7c54e802673a0e1fb0ddf220716d8f5156f1169ecb01e1"),
    ("10_stat415-id-through-lesson12-source-backend.zip", 37_621_137,
     "510bd0255f1ddbb925f3abb8594b04eac51fa688f0c0f5b184259033e578ada0"),
    ("20_THROUGH_LESSON12_RELEASE_NOTES.md", 1_213,
     "7db90c69118f75e41fef99d0ddd0704471710ff97b1b58957aa8e86a0b36f339"),
    ("30_THROUGH_LESSON12_LICENSE.md", 1_515,
     "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d"),
    ("40_THROUGH_LESSON12_QA_RECEIPT.json", 12_428,
     "d12c9dcb4293de0ec929cc2d2c330e197d936a86e17e27adc20dede10bef15db"),
    ("41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json", 21_702,
     "02583cecceba1db5f8a9f7561f567ebd98585c441a6e4cae5ba1ef92f8710d6e"),
    ("50_THROUGH_LESSON12_RELEASE_MANIFEST.csv", 854,
     "92fb966e8e2d6df14810571bdb171eafa2305e9c0241f7a87f5c3c85545c1528"),
    ("SHA256SUMS_THROUGH_LESSON12.txt", 750,
     "ed97539fb0dd796edcc287cae67920acb04e62bb5e65cd0775e8afbfb7d3d663"),
    ("60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json", 4_763,
     "d9306b66b26a5faf0b90cfc7c1266001cba9a4159cef1394692fb07b6cc7ac49"),
    ("50_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_MANIFEST.csv", 3_655,
     "a55022c0c3f601f6bb25d9b0f41a761f75132f681d869412c7e4cb09a643d9fd"),
    ("SHA256SUMS_COMPLETE_CONSOLIDATED_READERS.txt", 1_661,
     "1b9fdbc6e88b50983488e41eb3df01ea38853f243a319375cfa73bd403aff03e"),
    ("60_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_ROOT_RECEIPT.json", 11_484,
     "a88abbdaac65574089d155613e422ec91896c49ae842b3eaab7935037727260a"),
    ("01_RANDOM_COMPLETENESS_DONOR_OFFLINE_READER.zip", 610_303,
     "45487bfcf873f4fd282c92e5b9f7c3453701f3aafa90de9bfc1c69f99ce41a5b"),
    ("11_RANDOM_COMPLETENESS_DONOR_SOURCE_BACKEND.zip", 741_277,
     "485e5264c694284de2eea5511cbb7955a620a042e9caac354440b3a2a76a773b"),
    ("21_RANDOM_COMPLETENESS_DONOR_RELEASE_NOTES.md", 1_249,
     "d6ec13b8d1303a95d25695a246d335411e9a7d6799a624afb94c143bd0777256"),
    ("31_RANDOM_COMPLETENESS_DONOR_LICENSE_AND_ATTRIBUTION.md", 2_197,
     "d6aad0f8d75ef1083b5fc7d7dc3c50282e093d24e9ea45f75466eb5cc7c8b66b"),
    ("41_RANDOM_COMPLETENESS_DONOR_STATIC_QA_EVIDENCE.zip", 9_581,
     "dfb1bd1f1c7c49918a7d3cb670895750173d23302270c989d5cad9d4f1bbc79a"),
    ("70_C140_RANDOM_COMPLETENESS_FULL_UNION_MANIFEST.csv", 5_870,
     "3ea8a737dfaa1bb5d44e33d0f340bd001d1c2f7daf82a167d8cc22d961e8d663"),
    ("SHA256SUMS_C140_RANDOM_COMPLETENESS.txt", 2_598,
     "7f18459f7f60a4aac7b6ec8fa7563a0f5da31904ef4bcdf02125f620b7d52d32"),
    ("80_C140_RANDOM_COMPLETENESS_FULL_UNION_ROOT_RECEIPT.json", 16_724,
     "efb58a21302c56c0c5f4d1936296dc42cf43dce36135b3bfc61e3d5e22bede9b"),
)

ADDED_NAMES = (
    "02_C140_COMPANION_C1_OFFLINE_READER.zip",
    "12_C140_COMPANION_C1_SOURCE_BACKEND.zip",
    "22_C140_COMPANION_C1_RELEASE_NOTES.md",
    "32_C140_COMPANION_C1_LICENSE.md",
    "42_C140_COMPANION_C1_STATIC_QA_EVIDENCE.zip",
    "90_C140_COMPANION_C1_FULL_UNION_MANIFEST.csv",
    "SHA256SUMS_C140_COMPANION_C1.txt",
    "91_C140_COMPANION_C1_FULL_UNION_ROOT_RECEIPT.json",
)
EXPECTED_ORDER = tuple(row[0] for row in BASE_SPECS) + ADDED_NAMES


def snapshot() -> _engine.ReleaseSnapshot:
    """Freeze and validate the exact live 33-file C1 package."""
    relative_receipt = PACKAGE_RECEIPT.relative_to(ROOT).as_posix()
    receipt_payload = _engine.read_confined(relative_receipt, "C140 companion C1 package receipt")
    package = _engine.decode_object(receipt_payload, "C140 companion C1 package receipt")
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    coverage = package.get("coverage")
    rights = package.get("rights")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or not isinstance(publication, dict)
        or not isinstance(rows, list)
        or publication.get("file_count") != len(EXPECTED_ORDER)
        or len(rows) != len(EXPECTED_ORDER)
        or not isinstance(coverage, dict)
        or coverage.get("c140_course") != "incomplete"
        or coverage.get("c140_original_companion")
        != "C1 coherent partial checkpoint complete"
        or coverage.get("penn_state_spine") != "complete"
        or coverage.get("random_completeness_donor") != "complete"
        or rights != {
            "aggregate_uniform_relicense": False,
            "platform_license": "other-open",
        }
    ):
        raise RuntimeError("package receipt is not the admitted C140 companion C1 boundary")

    artifacts: list[_engine.Artifact] = []
    names: set[str] = set()
    paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"package file row {index} is malformed")
        name = row.get("filename")
        relative = _engine.canonical_relative(
            row.get("source_path"), f"package file row {index} path"
        )
        declared_size, declared_sha = _engine.checked_identity(
            row, f"package file row {index}"
        )
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_ORDER[index]
            or not isinstance(name, str)
            or not _engine._SAFE_NAME.fullmatch(name)
            or _engine._SENSITIVE_NAME.search(name)
            or relative != f"release/{name}"
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or not isinstance(row.get("lineage"), str)
            or not row.get("lineage")
            or not isinstance(row.get("media_type"), str)
            or "/" not in row.get("media_type", "")
            or row.get("primary_reader") is not (index == 0)
            or name in names
            or relative in paths
        ):
            raise RuntimeError(f"package file row {index} has an unsafe identity or path")
        payload = _engine.read_confined(relative, f"release asset {name}")
        if (len(payload), _engine.sha256(payload)) != (declared_size, declared_sha):
            raise RuntimeError(f"release asset differs from package receipt: {name}")
        total += len(payload)
        if total > MAX_RELEASE_BYTES:
            raise RuntimeError("release payload exceeds the 500 MB boundary")
        artifacts.append(
            _engine.Artifact(name, relative, len(payload), declared_sha, payload)
        )
        names.add(name)
        paths.add(relative)

    if publication.get("bytes") != total:
        raise RuntimeError("package aggregate byte count is stale")
    for item, (name, size, digest) in zip(artifacts[: len(BASE_SPECS)], BASE_SPECS):
        if (item.name, item.bytes, item.sha256) != (name, size, digest):
            raise RuntimeError(f"package changed an inherited base asset: {name}")
    if tuple(item.name for item in artifacts[len(BASE_SPECS):]) != ADDED_NAMES:
        raise RuntimeError("package appended inventory differs from the eight admitted C1 files")

    final_receipt = _engine.read_confined(
        relative_receipt, "C140 companion C1 package receipt"
    )
    if final_receipt != receipt_payload:
        raise RuntimeError("package receipt changed while being snapshotted")
    return _engine.ReleaseSnapshot(
        package=package,
        receipt_bytes=len(receipt_payload),
        receipt_sha256=_engine.sha256(receipt_payload),
        files=tuple(artifacts),
        inherited=tuple(artifacts[: len(BASE_SPECS)]),
        additions=tuple(artifacts[len(BASE_SPECS):]),
    )


def metadata() -> dict[str, object]:
    """Exact reader-facing metadata for the coherent but partial C1 boundary."""
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-28",
        "description": (
            "Rilis kumulatif O006/C140 Bahasa Indonesia (id-ID). Versi ini "
            "mempertahankan byte demi byte seluruh 25 berkas versi "
            "2026.08.28.c140-random-completeness—tulang punggung Penn State STAT "
            "415 yang lengkap (laman utama dan Pelajaran 00–12) serta donor "
            "kelengkapan Random yang lengkap—dan menambahkan tepat delapan berkas "
            "checkpoint pendamping orisinal C1. C1 adalah batas parsial yang koheren: "
            "tujuh bab D001–D007 tentang likelihood reguler, konsistensi dan "
            "normalitas MLE, delta method, Wald/score/LR/Wilks, kasus nonreguler, "
            "Neyman–Pearson/UMP, risiko, efisiensi, Rao–Blackwell, dan "
            "Lehmann–Scheffé; empat simulasi deterministik SIM001–SIM004; empat set "
            "penguasaan MS07–MS10 dengan 32 soal dan solusi lengkap; serta asesmen "
            "kumulatif CA01 dengan sepuluh soal dan rubrik 100 poin. C140 secara "
            "keseluruhan belum lengkap: model linear Gaussian matriks dan regresi "
            "berganda, perbandingan Bayesian–frequentist, simulasi tersisa, sembilan "
            "set penguasaan, tiga asesmen kumulatif, dan dua capstone masih harus "
            "diselesaikan. Hak komponen tidak diseragamkan: materi Penn State tetap "
            "CC BY-NC 4.0 kecuali dinyatakan lain; halaman Random mempertahankan saksi "
            "CC BY 2.0 pada laman utama dan tautan CC BY 1.0 pada Credits; materi "
            "pendamping orisinal C1 adalah CC BY-SA 4.0; MathJax tetap Apache-2.0. "
            "Karena itu metadata agregat memakai other-open dan berkas lisensi per "
            "komponen bersifat mengikat. Provenans produksi pendamping dan rekayasa "
            f"edisi: {MODEL_PROVENANCE}. Seluruh kredit sumber dipertahankan; tidak "
            "ada dukungan Penn State atau Kyle Siegrist yang tersirat."
        ),
        "creators": [
            {"name": "Penn State Department of Statistics"},
            {"name": "Siegrist, Kyle"},
            {"name": "OpenAI Codex"},
        ],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia",
            "id-ID",
            "mathematical statistics",
            "statistika matematis",
            "maximum likelihood",
            "Fisher information",
            "Wald test",
            "score test",
            "likelihood-ratio test",
            "Wilks theorem",
            "Neyman-Pearson lemma",
            "Rao-Blackwell theorem",
            "Lehmann-Scheffe theorem",
            "nonregular likelihood",
            "reproducible simulation",
            "mastery assessment",
            "Penn State STAT 415",
            "Random",
            "open educational resources",
            "offline HTML",
            "PDF",
            "EPUB",
            "machine-readable curriculum",
            "AI translation",
            "component-separated licensing",
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
                "identifier": "https://www.randomservices.org/random/point/Sufficient.html",
                "relation": "isDerivedFrom",
                "resource_type": "publication-other",
                "scheme": "url",
            },
            {
                "identifier": "10.5281/zenodo.22076539",
                "relation": "isSupplementedBy",
                "resource_type": "publication-book",
                "scheme": "doi",
            },
            {
                "identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
                "relation": "isSupplementedBy",
                "resource_type": "software",
                "scheme": "url",
            },
        ],
    }


def verify_base_record(
    session: _engine.requests.Session,
    snap: _engine.ReleaseSnapshot,
) -> dict[str, object]:
    """Anonymously bind the pinned 25-file base before any mutation."""
    record = _engine.public_record(session, BASE_RECORD_ID)
    if record.get("metadata", {}).get("version") != BASE_VERSION:
        raise RuntimeError("public C1 base record has the wrong version")
    verified = _engine.download_exact(session, record, snap.inherited)
    doi = str(record.get("doi", ""))
    if doi != f"10.5281/zenodo.{BASE_RECORD_ID}":
        raise RuntimeError("public C1 base record DOI is unexpected")
    result = {
        "record_id": BASE_RECORD_ID,
        "doi": doi,
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "version": BASE_VERSION,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "anonymous_readback": True,
        "environment_proxy_trust": False,
    }
    _engine.atomic_json(
        BASE_READBACK_RECEIPT,
        {
            "schema": BASE_READBACK_SCHEMA,
            "target_version": VERSION,
            "package_receipt_sha256": snap.receipt_sha256,
            "credential_access": False,
            "public_base": result,
        },
    )
    return result


def write_public_receipts(
    base: dict[str, object],
    public: dict[str, object],
    mode: str,
    **extra: object,
) -> None:
    """Persist sanitized C1-suffixed publication and lineage receipts."""
    _engine.atomic_json(
        READBACK_RECEIPT,
        {
            **base,
            "mode": "verify-published",
            "credential_access": False,
            "environment_proxy_trust": False,
            "public": public,
        },
    )
    _engine.atomic_json(
        PUBLICATION_RECEIPT,
        {
            **base,
            "mode": mode,
            "credential_access": mode != "verify-published",
            "public": public,
            **extra,
        },
    )
    _engine.atomic_json(
        LINEAGE_RECEIPT,
        {
            "schema": LINEAGE_SCHEMA,
            "record_id": public["record_id"],
            "doi": public["doi"],
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "url": public["url"],
            "version": VERSION,
        },
    )


def configure_engine() -> None:
    """Pin every mutable lineage parameter before entering the robust engine."""
    _engine.BASE_RECORD_ID = BASE_RECORD_ID
    _engine.BASE_VERSION = BASE_VERSION
    _engine.CONCEPT_RECORD_ID = CONCEPT_RECORD_ID
    _engine.CONCEPT_DOI = CONCEPT_DOI
    _engine.VERSION = VERSION
    _engine.NEW_VERSION_URL = (
        f"{_engine.DEPOSITIONS}/{BASE_RECORD_ID}/actions/newversion"
    )
    _engine.TITLE = TITLE
    _engine.MODEL_PROVENANCE = MODEL_PROVENANCE
    _engine.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    _engine.PUBLICATION_RECEIPT = PUBLICATION_RECEIPT
    _engine.READBACK_RECEIPT = READBACK_RECEIPT
    _engine.BASE_READBACK_RECEIPT = BASE_READBACK_RECEIPT
    _engine.AUDIT_RECEIPT = AUDIT_RECEIPT
    _engine.DRAFT_MARKER = DRAFT_MARKER
    _engine.LINEAGE_RECEIPT = LINEAGE_RECEIPT
    _engine.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    _engine.PUBLICATION_SCHEMA = PUBLICATION_SCHEMA
    _engine.MARKER_SCHEMA = MARKER_SCHEMA
    _engine.USER_AGENT = USER_AGENT
    _engine.MAX_RELEASE_BYTES = MAX_RELEASE_BYTES
    _engine.BASE_SPECS = BASE_SPECS
    _engine.ADDED_NAMES = ADDED_NAMES
    _engine.EXPECTED_ORDER = EXPECTED_ORDER
    _engine.snapshot = snapshot
    _engine.metadata = metadata
    _engine.verify_base_record = verify_base_record
    _engine.write_public_receipts = write_public_receipts


def main() -> None:
    configure_engine()
    _engine.main()


if __name__ == "__main__":
    main()
