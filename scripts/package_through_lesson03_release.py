#!/usr/bin/env python3
"""Create deterministic reader-first release packages through Lesson 03.

The packager owns only new, boundary-specific release outputs.  It never
rewrites any FIRST_UNIT, THROUGH_LESSON01, or other historical package.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

import package_through_lesson01_release as common


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
READER = ROOT / "build" / "html-id"

READER_ZIP = "00_stat415-id-through-lesson03-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson03-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON03_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_THROUGH_LESSON03_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON03_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON03_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_THROUGH_LESSON03_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS_THROUGH_LESSON03.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON03_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON03_PACKAGE_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = ["index", "Lesson00", "Lesson01", "Lesson02", "Lesson03"]
EXPECTED_COVERAGE = {
    "complete_count": 5,
    "complete_documents": COMPLETE_DOCUMENTS,
    "corpus_document_count": 14,
    "next_document": "Lesson04",
}

# Exact, reviewable closure for the 5-of-14 release.  Membership is a release
# decision and is never inferred from a recursive workspace scan.
SOURCE_PACKAGE_FILES = (
    "LICENSE.md",
    "README.md",
    "requirements.txt",
    ".github/workflows/pages.yml",
    # Deterministic source, normalization, translation, build, QA, and package
    # scripts needed to reproduce the cumulative reader.
    "scripts/freeze_stat415.py",
    "scripts/freeze_mathjax.py",
    "scripts/freeze_first_unit_assets.py",
    "scripts/freeze_lesson01_assets.py",
    "scripts/freeze_lesson02_assets.py",
    "scripts/normalize_first_unit.py",
    "scripts/normalize_lesson01.py",
    "scripts/normalize_lesson02.py",
    "scripts/normalize_lesson03.py",
    "scripts/merge_first_unit_translations.py",
    "scripts/merge_lesson01_translations.py",
    "scripts/merge_lesson02_translations.py",
    "scripts/merge_lesson03_translations.py",
    "scripts/build_first_unit.py",
    "scripts/build_through_lesson01.py",
    "scripts/build_through_lesson02.py",
    "scripts/build_through_lesson03.py",
    "scripts/qa_first_unit.py",
    "scripts/qa_through_lesson01.py",
    "scripts/qa_through_lesson02.py",
    "scripts/qa_through_lesson03.py",
    "scripts/package_through_lesson01_release.py",
    "scripts/package_through_lesson03_release.py",
    # Frozen official authority for the complete translated boundary.
    "authority/SOURCE_URL_MANIFEST.csv",
    "authority/SOURCE_FREEZE_RECEIPT.json",
    "authority/upstream/stat415/index.html",
    "authority/upstream/stat415/Lesson00.html",
    "authority/upstream/stat415/Lesson01.html",
    "authority/upstream/stat415/Lesson02.html",
    "authority/upstream/stat415/Lesson03.html",
    # Frozen offline MathJax runtime.
    "authority/runtime/MathJax-3.1.2/URL_MANIFEST.csv",
    "authority/runtime/MathJax-3.1.2/FREEZE_RECEIPT.json",
    "authority/runtime/MathJax-3.1.2/LICENSE.txt",
    "authority/runtime/MathJax-3.1.2/tex-svg.js",
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/color.js",
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/enclose.js",
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/cancel.js",
    # Complete bounded asset closure through Lesson 03.  Lesson 03 itself has
    # a separately proved zero-main-content-asset closure.
    "authority/FIRST_UNIT_ASSET_MANIFEST.csv",
    "authority/FIRST_UNIT_ASSET_RECEIPT.json",
    "authority/assets/stat415/assets/415lesson0thumb.png",
    "authority/assets/stat415/assets/415lesson1thumb.png",
    "authority/assets/stat415/assets/415lesson2thumb.png",
    "authority/assets/stat415/assets/415lesson3thumb.png",
    "authority/assets/stat415/assets/415lesson4thumb.png",
    "authority/assets/stat415/assets/415lesson5thumb.png",
    "authority/assets/stat415/assets/415lesson6thumb.png",
    "authority/assets/stat415/assets/415lesson7thumb.png",
    "authority/assets/stat415/assets/415lesson8thumb.png",
    "authority/assets/stat415/assets/415lesson9thumb.png",
    "authority/assets/stat415/assets/415lesson10thumb.png",
    "authority/assets/stat415/assets/415lesson11thumb.png",
    "authority/assets/stat415/assets/415lesson12thumb.png",
    "authority/LESSON01_ASSET_MANIFEST.csv",
    "authority/LESSON01_ASSET_FREEZE_RECEIPT.json",
    "authority/assets/stat415/lesson01/STAT-415-SEC-3-18-09.svg",
    "authority/assets/stat415/lesson01/stat-415-sec-3-18-10.svg",
    "authority/assets/stat415/lesson01/stat-415-sec-3-18-11.svg",
    "authority/assets/stat415/lesson01/stat-415-sec-3-18-12.svg",
    "authority/assets/stat415/lesson01/STAT-415-SEC-3-18-13.svg",
    "authority/LESSON02_ASSET_MANIFEST.csv",
    "authority/LESSON02_ASSET_FREEZE_RECEIPT.json",
    "authority/assets/stat415/lesson02/dartboard.png",
    "authority/assets/stat415/lesson02/unnamed-chunk-1-1.png",
    # Normalized source and reader-facing Indonesian authoring source.
    "source/normalized/en-US/index.html",
    "source/normalized/en-US/Lesson00.html",
    "source/normalized/en-US/Lesson01.html",
    "source/normalized/en-US/Lesson02.html",
    "source/normalized/en-US/Lesson03.html",
    "source/id-ID/index.html",
    "source/id-ID/Lesson00.html",
    "source/id-ID/Lesson01.html",
    "source/id-ID/Lesson02.html",
    "source/id-ID/Lesson03.html",
    "source/id-ID/reader.css",
    "source/id-ID/course_card_alt_text.json",
    "source/id-ID/first_unit_translation.csv",
    "source/id-ID/lesson01_translation.csv",
    "source/id-ID/lesson02_translation.csv",
    "source/id-ID/lesson03_translation.csv",
    # Complete modular machine layer through Lesson 03.
    "backend/first_unit_segments.jsonl",
    "backend/first_unit_structures.jsonl",
    "backend/first_unit_translation_bindings.jsonl",
    "backend/first_unit_documents.jsonl",
    "backend/first_unit_corrections.jsonl",
    "backend/lesson01_source_catalogue.jsonl",
    "backend/lesson01_translation_bindings.jsonl",
    "backend/lesson02_source_catalogue.jsonl",
    "backend/lesson02_translation_bindings.jsonl",
    "backend/lesson03_source_catalogue.jsonl",
    "backend/lesson03_translation_bindings.jsonl",
    "backend/through_lesson01_documents.jsonl",
    "backend/through_lesson01_corrections.jsonl",
    "backend/through_lesson02_documents.jsonl",
    "backend/through_lesson02_corrections.jsonl",
    "backend/through_lesson03_documents.jsonl",
    "backend/through_lesson03_corrections.jsonl",
    # Bounded translation inputs, correction evidence, terminology evidence,
    # and asset-rights decisions.  Draft notes and redundant dumps are absent.
    "working/translation_part_a.json",
    "working/translation_part_b.json",
    "working/translation_part_c.json",
    "working/lesson01_translation_part_a.json",
    "working/lesson01_translation_part_b.json",
    "working/lesson01_translation_part_c.json",
    "working/lesson01_segments.csv",
    "working/lesson01_terminology_candidates.csv",
    "working/lesson01_asset_rights_audit.json",
    "working/lesson01_source_findings.md",
    "working/lesson02_translation_part_a.json",
    "working/lesson02_translation_part_b.json",
    "working/lesson02_translation_part_c.json",
    "working/lesson02_segments.csv",
    "working/lesson02_terminology_qa.md",
    "working/lesson02_asset_rights_audit.json",
    "working/lesson02_source_findings.md",
    "working/lesson03_translation_part_a.json",
    "working/lesson03_translation_part_b.json",
    "working/lesson03_translation_part_c.json",
    "working/lesson03_segments.csv",
    "working/lesson03_terminology_qa.md",
    "working/lesson03_zero_asset_closure.json",
    "working/lesson03_source_findings.md",
    # Stable semantic controls.  Volatile cursors, checkpoints, publication
    # receipts, credentials, and lineage transactions are deliberately absent.
    "00_control/ADVERSE_LEDGER.jsonl",
    "00_control/COMPONENT_BOUNDARY.md",
    "00_control/DECISION_LOG.md",
    "00_control/RIGHTS_AND_COMPONENTS.md",
    "00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv",
    "00_control/TRANSLATION_LEDGER.csv",
    "00_control/WORKFLOW.md",
    # Deterministic evidence chain through the exact current boundary.
    "build/FIRST_UNIT_NORMALIZATION_RECEIPT.json",
    "build/FIRST_UNIT_TRANSLATION_RECEIPT.json",
    "build/FIRST_UNIT_BUILD_RECEIPT.json",
    "build/FIRST_UNIT_MANIFEST.csv",
    "build/FIRST_UNIT_QA_RECEIPT.json",
    "build/FIRST_UNIT_VISUAL_QA_RECEIPT.json",
    "build/LESSON01_NORMALIZATION_RECEIPT.json",
    "build/LESSON01_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON01_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON01_MANIFEST.csv",
    "build/THROUGH_LESSON01_QA_RECEIPT.json",
    "build/THROUGH_LESSON01_VISUAL_QA_RECEIPT.json",
    "build/LESSON02_NORMALIZATION_RECEIPT.json",
    "build/LESSON02_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON02_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON02_MANIFEST.csv",
    "build/THROUGH_LESSON02_QA_RECEIPT.json",
    "build/THROUGH_LESSON02_VISUAL_QA_RECEIPT.json",
    "build/LESSON03_NORMALIZATION_RECEIPT.json",
    "build/LESSON03_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON03_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON03_MANIFEST.csv",
    "build/THROUGH_LESSON03_QA_RECEIPT.json",
    "build/THROUGH_LESSON03_VISUAL_QA_RECEIPT.json",
)


def snapshot_source_files() -> dict[PurePosixPath, bytes]:
    relatives = [common.safe_relative(value) for value in SOURCE_PACKAGE_FILES]
    folded = [relative.as_posix().casefold() for relative in relatives]
    if len(set(folded)) != len(folded):
        raise RuntimeError("case-insensitive duplicate in source-package allowlist")
    snapshot: dict[PurePosixPath, bytes] = {}
    for relative in relatives:
        common.reject_sensitive_source_name(relative)
        payload = common.read_confined_regular_file(
            ROOT, relative, relative.as_posix()
        )
        common.reject_machine_local_text(relative, payload)
        snapshot[relative] = payload
    return snapshot


def validate_receipts(source: dict[PurePosixPath, bytes]) -> dict[str, bytes]:
    def admitted(relative: str) -> bytes:
        try:
            return source[PurePosixPath(relative)]
        except KeyError as exc:
            raise RuntimeError(f"validated input absent from allowlist: {relative}") from exc

    build_payload = admitted("build/THROUGH_LESSON03_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON03_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON03_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON03_MANIFEST.csv")
    build = common.decode_json_object(build_payload, "Lesson03 build receipt")
    qa = common.decode_json_object(qa_payload, "Lesson03 QA receipt")
    visual = common.decode_json_object(visual_payload, "Lesson03 visual receipt")
    manifest_sha = common.sha256(manifest_payload)

    if build.get("schema") != "o006.stat415.through-lesson03-build.v1":
        raise RuntimeError("unexpected cumulative build schema")
    if build.get("status") != "built" or build.get("coverage") != EXPECTED_COVERAGE:
        raise RuntimeError("build receipt is not the exact 5-of-14 boundary")
    if build.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("build receipt has wrong model provenance")
    reader = build.get("reader", {})
    if (
        reader.get("files") != 32
        or reader.get("bytes") != 2_804_159
        or reader.get("manifest_sha256") != manifest_sha
        or reader.get("path") != "build/html-id"
    ):
        raise RuntimeError("build receipt does not bind the exact 32-file reader")
    if (
        build.get("translation_segments") != 1_599
        or build.get("structural_units_normalized") != 1_399
        or build.get("structural_units_target") != 1_397
        or build.get("math_nodes", {}).get("total") != 1_149
        or build.get("corrections", {}).get("count") != 46
    ):
        raise RuntimeError("build receipt cumulative counts differ")

    if qa.get("schema") != "o006.stat415.through-lesson03-qa.v1":
        raise RuntimeError("unexpected cumulative QA schema")
    if qa.get("status") != "pass" or qa.get("coverage") != EXPECTED_COVERAGE:
        raise RuntimeError("deterministic QA has not passed for 5 of 14")
    qa_reader = qa.get("reader", {})
    if (
        qa_reader.get("files") != 32
        or qa_reader.get("bytes") != 2_804_159
        or qa_reader.get("manifest_sha256") != manifest_sha
    ):
        raise RuntimeError("QA receipt does not bind the exact reader")
    rights = qa.get("privacy_runtime_rights_and_provenance", {})
    if (
        rights.get("penn_state") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("mathjax_3_1_2") != "Apache-2.0"
        or rights.get("aggregate_uniform_relicense") is not False
        or rights.get("translation_provenance") != PROVENANCE
    ):
        raise RuntimeError("component rights or provenance QA is incomplete")

    if visual.get("schema") != "o006.stat415.through-lesson03-visual-qa.v1":
        raise RuntimeError("unexpected cumulative visual-QA schema")
    if visual.get("status") != "pass" or visual.get("coverage") != (
        "landing/index plus complete Lesson00, Lesson01, Lesson02, and Lesson03"
    ):
        raise RuntimeError("desktop/mobile visual QA has not passed for 5 of 14")
    evidence = visual.get("evidence", {})
    if evidence.get("manifest", {}).get("sha256") != manifest_sha:
        raise RuntimeError("visual QA does not bind the reader manifest")
    if evidence.get("build_receipt", {}).get("sha256") != common.sha256(build_payload):
        raise RuntimeError("visual QA does not bind the build receipt")
    if evidence.get("qa_receipt", {}).get("sha256") != common.sha256(qa_payload):
        raise RuntimeError("visual QA does not bind the QA receipt")
    if (
        visual.get("desktop", {}).get("console_errors_or_warnings") != 0
        or visual.get("mobile", {}).get("console_errors_or_warnings") != 0
    ):
        raise RuntimeError("visual QA reports browser warnings or errors")

    license_payload = admitted("LICENSE.md")
    license_text = license_payload.decode("utf-8")
    for required in ("CC BY-NC 4.0", "Apache License 2.0", "CC BY-SA 4.0"):
        if required not in license_text:
            raise RuntimeError(f"component right missing from LICENSE.md: {required}")
    if PROVENANCE not in admitted("README.md").decode("utf-8"):
        raise RuntimeError("exact model provenance is missing from README.md")

    return {
        "build": build_payload,
        "qa": qa_payload,
        "visual": visual_payload,
        "manifest": manifest_payload,
        "license": license_payload,
    }


def reader_package(manifest_payload: bytes) -> tuple[bytes, dict[str, Any]]:
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != 32:
        raise RuntimeError(f"expected exactly 32 reader files, found {len(rows)}")

    actual_paths: set[PurePosixPath] = set()
    for path in READER.rglob("*"):
        relative = PurePosixPath(path.relative_to(READER).as_posix())
        if path.is_symlink():
            raise RuntimeError(f"symlinked reader input is forbidden: {relative}")
        if path.is_file():
            actual_paths.add(relative)

    files: dict[PurePosixPath, bytes] = {}
    manifested: set[PurePosixPath] = set()
    reader_bytes = 0
    root = PurePosixPath("stat415-id-through-lesson03")
    for row in rows:
        relative = common.safe_relative(row["relative_path"])
        if relative in manifested:
            raise RuntimeError(f"duplicate reader-manifest path: {relative}")
        data = common.read_confined_regular_file(READER, relative, relative.as_posix())
        if len(data) != int(row["bytes"]) or common.sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {relative}")
        manifested.add(relative)
        reader_bytes += len(data)
        files[root / relative] = data
    if reader_bytes != 2_804_159:
        raise RuntimeError(f"unexpected reader byte count: {reader_bytes}")
    if actual_paths != manifested:
        missing = sorted(path.as_posix() for path in manifested - actual_paths)
        extra = sorted(path.as_posix() for path in actual_paths - manifested)
        raise RuntimeError(f"reader inventory differs; missing={missing}; extra={extra}")

    embedded = root / "THROUGH_LESSON03_MANIFEST.csv"
    files[embedded] = manifest_payload
    payload = common.archive(files)
    return payload, {
        "reader_files": len(rows),
        "reader_bytes": reader_bytes,
        "package_entries": len(files),
        "uncompressed_bytes": sum(len(value) for value in files.values()),
        "manifest_bytes": len(manifest_payload),
        "manifest_sha256": common.sha256(manifest_payload),
        "archive_method": "ZIP_STORED",
    }


def source_package(source: dict[PurePosixPath, bytes]) -> tuple[bytes, dict[str, Any]]:
    root = PurePosixPath("penn-state-stat-415-id")
    files = {root / relative: data for relative, data in source.items()}
    payload = common.archive(files)
    allowlist_manifest = common.canonical_json(
        [
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "sha256": common.sha256(data),
            }
            for relative, data in sorted(
                source.items(), key=lambda item: item[0].as_posix().casefold()
            )
        ]
    )
    return payload, {
        "entries": len(files),
        "uncompressed_bytes": sum(len(value) for value in files.values()),
        "allowlist_manifest_sha256": common.sha256(allowlist_manifest),
        "archive_method": "ZIP_STORED",
    }


def notes_payload() -> bytes:
    return (
        "# STAT 415 — edisi Bahasa Indonesia: hingga Pelajaran 03\n\n"
        "Status: **sebagian; 5 dari 14 dokumen lengkap**. Paket ini memuat "
        "laman utama serta seluruh Pelajaran 00–03 dalam Bahasa Indonesia. "
        "Pelajaran 04–12 belum diterjemahkan dan tetap menaut ke sumber resmi "
        "berbahasa Inggris.\n\n"
        "Pembaca luring adalah berkas utama: 32 berkas pembaca dengan "
        "2.804.159 byte. Ekstrak ZIP pembaca, layani direktori hasil ekstraksi "
        "melalui peladen HTTP statis, lalu buka `index.html`. Paket source-backend "
        "yang ringkas memuat otoritas beku, authoring source, 1.599 segmen "
        "terjemahan, backend modular, skrip reproduksi, kontrol semantik, "
        "lisensi, dan bukti QA yang diperlukan untuk melanjutkan edisi. Batas "
        "ini memuat 1.399 unit sumber, 1.397 unit target, 1.149 permukaan "
        "matematika, dan 46 koreksi turunan terverifikasi.\n\n"
        "Konten Penn State dan adaptasinya tetap CC BY-NC 4.0 kecuali "
        "dinyatakan lain; MathJax 3.1.2 tetap Apache-2.0; lapisan asli "
        "repositori memiliki lisensi terpisah CC BY-SA 4.0. Lihat berkas "
        "lisensi. Koleksi ini tidak direlisensi secara seragam, dan tidak ada "
        "dukungan atau pengesahan oleh Penn State yang tersirat.\n\n"
        f"Provenans terjemahan: {PROVENANCE}. Seluruh kredit sumber dan "
        "kontributor manusia dipertahankan.\n\n"
        "Semantik inventaris: manifes rilis mencakup enam aset substantif dan "
        "mengecualikan dirinya sendiri, berkas checksum, serta root receipt "
        "untuk menghindari siklus hash. Berkas checksum mencakup keenam aset "
        "dan manifes. Root receipt mengikat setiap aset unggahan lain dan hanya "
        "mengecualikan dirinya sendiri.\n"
    ).encode("utf-8")


def compute() -> tuple[dict[str, bytes], bytes]:
    source = snapshot_source_files()
    validated = validate_receipts(source)
    reader_zip, reader_info = reader_package(validated["manifest"])
    source_zip, source_info = source_package(source)

    payloads: dict[str, bytes] = {
        READER_ZIP: reader_zip,
        SOURCE_ZIP: source_zip,
        RELEASE_NOTES: notes_payload(),
        RELEASE_LICENSE: validated["license"],
        RELEASE_QA: validated["qa"],
        RELEASE_VISUAL_QA: validated["visual"],
    }
    roles = {
        READER_ZIP: "primary-offline-reader",
        SOURCE_ZIP: "compact-resumable-source-backend",
        RELEASE_NOTES: "scope-status-rights-and-provenance",
        RELEASE_LICENSE: "component-rights",
        RELEASE_QA: "deterministic-qa",
        RELEASE_VISUAL_QA: "desktop-mobile-visual-qa",
    }
    substantive = list(payloads)

    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=("filename", "bytes", "sha256", "role"),
        lineterminator="\n",
    )
    writer.writeheader()
    for filename in substantive:
        data = payloads[filename]
        writer.writerow(
            {
                "filename": filename,
                "bytes": len(data),
                "sha256": common.sha256(data),
                "role": roles[filename],
            }
        )
    payloads[RELEASE_MANIFEST] = output.getvalue().encode("utf-8")
    roles[RELEASE_MANIFEST] = "six-substantive-assets-manifest"
    payloads[CHECKSUMS] = "".join(
        f"{common.sha256(data)}  {filename}\n"
        for filename, data in payloads.items()
    ).encode("utf-8")
    roles[CHECKSUMS] = "sha256-for-substantive-assets-and-manifest"

    covered_by_root = list(payloads)
    payloads[ROOT_RECEIPT] = common.canonical_json(
        {
            "schema": "o006.stat415.through-lesson03-release-root.v1",
            "status": "ready",
            "coverage": EXPECTED_COVERAGE,
            "self_exclusion": {
                "filename": ROOT_RECEIPT,
                "reason": "non-self-referential cryptographic root",
            },
            "inventory_semantics": {
                "release_manifest": {
                    "filename": RELEASE_MANIFEST,
                    "covers": substantive,
                    "excludes": [RELEASE_MANIFEST, CHECKSUMS, ROOT_RECEIPT],
                },
                "sha256sums": {
                    "filename": CHECKSUMS,
                    "covers": substantive + [RELEASE_MANIFEST],
                    "excludes": [CHECKSUMS, ROOT_RECEIPT],
                },
                "root_receipt": {
                    "filename": ROOT_RECEIPT,
                    "covers": covered_by_root,
                    "excludes": [ROOT_RECEIPT],
                },
            },
            "files": [
                {
                    "filename": filename,
                    "bytes": len(payloads[filename]),
                    "sha256": common.sha256(payloads[filename]),
                    "role": roles[filename],
                }
                for filename in covered_by_root
            ],
            "file_count": len(covered_by_root),
            "total_bytes": sum(len(payloads[name]) for name in covered_by_root),
            "upload_order": covered_by_root,
        }
    )
    roles[ROOT_RECEIPT] = "non-self-referential-release-root"

    inputs = {
        "reader_manifest": validated["manifest"],
        "build_receipt": validated["build"],
        "qa_receipt": validated["qa"],
        "visual_qa_receipt": validated["visual"],
        "license": validated["license"],
    }
    receipt = common.canonical_json(
        {
            "schema": "o006.stat415.through-lesson03-package.v1",
            "status": "ready",
            "coverage": {
                **EXPECTED_COVERAGE,
                "statement": (
                    "landing/index plus complete Lesson00-Lesson03; "
                    "5 of 14 documents"
                ),
            },
            "locale": "id-ID",
            "translation_provenance": PROVENANCE,
            "rights": {
                "penn_state": "CC BY-NC 4.0 except where otherwise noted",
                "mathjax_3_1_2": "Apache-2.0",
                "original_repository_layer": "CC BY-SA 4.0",
                "aggregate_uniform_relicense": False,
            },
            "inputs": {
                name: {"bytes": len(data), "sha256": common.sha256(data)}
                for name, data in inputs.items()
            },
            "files": [
                {
                    "filename": filename,
                    "bytes": len(data),
                    "sha256": common.sha256(data),
                }
                for filename, data in payloads.items()
            ],
            "file_count": len(payloads),
            "total_bytes": sum(len(data) for data in payloads.values()),
            "primary_file": READER_ZIP,
            "reader_zip": {"filename": READER_ZIP, **reader_info},
            "source_zip": {"filename": SOURCE_ZIP, **source_info},
            "inventory_semantics": {
                "release_manifest_excludes": [
                    RELEASE_MANIFEST,
                    CHECKSUMS,
                    ROOT_RECEIPT,
                ],
                "sha256sums_excludes": [CHECKSUMS, ROOT_RECEIPT],
                "root_receipt_excludes": [ROOT_RECEIPT],
            },
            "upload_order": list(payloads),
        }
    )
    return payloads, receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    payloads, receipt = compute()
    outputs = {f"release/{name}": data for name, data in payloads.items()}
    outputs[RECEIPT.relative_to(ROOT).as_posix()] = receipt
    if args.write:
        historical_names = {
            path.name
            for path in RELEASE.iterdir()
            if path.is_file() and "LESSON03" not in path.name.upper()
        }
        if any(name in historical_names for name in payloads):
            raise RuntimeError("new output name collides with a historical release file")
        for relative, data in outputs.items():
            common.atomic_write(ROOT / relative, data)
        state = "written"
    else:
        for relative, data in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != data:
                raise RuntimeError(f"release-package output differs: {relative}")
        state = "verified"

    info = json.loads(receipt)
    print(
        json.dumps(
            {
                "mode": state,
                "files": info["file_count"],
                "bytes": info["total_bytes"],
                "reader_files": info["reader_zip"]["reader_files"],
                "source_entries": info["source_zip"]["entries"],
                "receipt_sha256": common.sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
