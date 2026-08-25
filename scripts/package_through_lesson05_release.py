#!/usr/bin/env python3
"""Create deterministic reader-first release packages through Lesson 05.

The packager owns only new, boundary-specific 7-of-14 outputs. Historical
release files are immutable inputs and are never rewritten. Package membership
is an explicit allowlist; it is not inferred from a recursive repository scan.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

import package_through_lesson01_release as common
import package_through_lesson03_release as prior


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
READER = ROOT / "build" / "html-id"

READER_ZIP = "00_stat415-id-through-lesson05-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson05-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON05_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_THROUGH_LESSON05_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON05_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON05_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_THROUGH_LESSON05_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS_THROUGH_LESSON05.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON05_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON05_PACKAGE_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = [
    "index",
    "Lesson00",
    "Lesson01",
    "Lesson02",
    "Lesson03",
    "Lesson04",
    "Lesson05",
]
EXPECTED_COVERAGE = {
    "complete_count": 7,
    "complete_documents": COMPLETE_DOCUMENTS,
    "corpus_document_count": 14,
    "next_document": "Lesson06",
}
VISUAL_COVERAGE = (
    "landing/index plus complete Lesson00, Lesson01, Lesson02, Lesson03, "
    "Lesson04, and Lesson05"
)
EXPECTED_MATH = {
    "index": 0,
    "Lesson00": 331,
    "Lesson01": 169,
    "Lesson02": 209,
    "Lesson03": 440,
    "Lesson04": 289,
    "Lesson05": 108,
    "licenses": 0,
}

# Extend the already explicit, reviewed 5-of-14 closure. This tuple is the
# complete 7-of-14 source/backend allowlist and deliberately excludes volatile
# cursors, checkpoints, publication transactions, credentials, caches, local
# renders, screenshots, draft notes, and every untranslated future lesson.
ADDITIONAL_SOURCE_PACKAGE_FILES = (
    # Lesson 05 uses \boldsymbol; the corrected offline MathJax closure must
    # preserve its exact extension byte in addition to the historical runtime.
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/boldsymbol.js",
    # Deterministic Lesson 04 and Lesson 05 pipeline.
    "scripts/freeze_lesson04_assets.py",
    "scripts/normalize_lesson04.py",
    "scripts/lesson04_corrections.py",
    "scripts/merge_lesson04_translations.py",
    "scripts/build_through_lesson04.py",
    "scripts/qa_through_lesson04.py",
    "scripts/normalize_lesson05.py",
    "scripts/lesson05_corrections.py",
    "scripts/merge_lesson05_translations.py",
    "scripts/build_through_lesson05.py",
    "scripts/qa_through_lesson05.py",
    "scripts/package_through_lesson05_release.py",
    # Exact official HTML authority for the newly completed lessons.
    "authority/upstream/stat415/Lesson04.html",
    "authority/upstream/stat415/Lesson05.html",
    # Lesson 04 asset closure and exact source byte.
    "authority/LESSON04_ASSET_MANIFEST.csv",
    "authority/LESSON04_ASSET_FREEZE_RECEIPT.json",
    "authority/assets/stat415/lesson04/STAT-415-SEC-1-15.svg",
    # Lesson 05 same-origin image closure. The one target-only seeded plot is
    # admitted separately below and never substituted for its source witness.
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/fig-boxplotcornyield-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/fig-histogramcornyield-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/fig-scattercornyield-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-28-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-33-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-38-1.png",
    "authority/assets/stat415/lesson05/assets/numericalmle.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-44-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-44-2.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-44-3.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-44-4.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-44-5.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-45-1.png",
    "authority/assets/stat415/lesson05/Lesson05_files/figure-html/unnamed-chunk-50-1.png",
    # Normalized and reader-facing source, translations, and disclosed target
    # derivative required to rebuild the exact cumulative reader.
    "source/normalized/en-US/Lesson04.html",
    "source/normalized/en-US/Lesson05.html",
    "source/id-ID/Lesson04.html",
    "source/id-ID/Lesson05.html",
    "source/id-ID/lesson04_translation.csv",
    "source/id-ID/lesson05_translation.csv",
    "source/id-ID/assets/lesson05/seeded-z1000.png",
    # Stable source catalogue, translation bindings, documents, corrections.
    "backend/lesson04_source_catalogue.jsonl",
    "backend/lesson04_translation_bindings.jsonl",
    "backend/lesson05_source_catalogue.jsonl",
    "backend/lesson05_translation_bindings.jsonl",
    "backend/through_lesson04_documents.jsonl",
    "backend/through_lesson04_corrections.jsonl",
    "backend/through_lesson05_documents.jsonl",
    "backend/through_lesson05_corrections.jsonl",
    # Exact bounded translation inputs and substantive audit evidence.
    "working/lesson04_translation_part_a.json",
    "working/lesson04_translation_part_b.json",
    "working/lesson04_translation_part_c.json",
    "working/lesson04_segments.csv",
    "working/lesson04_asset_inventory.json",
    "working/lesson04_asset_rights_audit.json",
    "working/lesson04_math_audit.md",
    "working/lesson04_terminology_qa.md",
    "working/lesson04_source_findings.md",
    "working/lesson05_translation_part_a.json",
    "working/lesson05_translation_part_b.json",
    "working/lesson05_translation_part_c.json",
    "working/lesson05_segments.csv",
    "working/lesson05_asset_closure.json",
    "working/lesson05_math_audit.md",
    "working/lesson05_terminology_qa.md",
    "working/lesson05_source_findings.md",
    # Deterministic evidence for both newly completed boundaries. Visual QA is
    # cumulative and required only at the meaningful 7-of-14 release boundary.
    "build/LESSON04_NORMALIZATION_RECEIPT.json",
    "build/LESSON04_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON04_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON04_MANIFEST.csv",
    "build/THROUGH_LESSON04_QA_RECEIPT.json",
    "build/LESSON05_NORMALIZATION_RECEIPT.json",
    "build/LESSON05_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON05_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON05_MANIFEST.csv",
    "build/THROUGH_LESSON05_QA_RECEIPT.json",
    "build/THROUGH_LESSON05_VISUAL_QA_RECEIPT.json",
)

SOURCE_PACKAGE_FILES = prior.SOURCE_PACKAGE_FILES + ADDITIONAL_SOURCE_PACKAGE_FILES


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

    build_payload = admitted("build/THROUGH_LESSON05_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON05_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON05_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON05_MANIFEST.csv")
    build = common.decode_json_object(build_payload, "Lesson05 build receipt")
    qa = common.decode_json_object(qa_payload, "Lesson05 QA receipt")
    visual = common.decode_json_object(visual_payload, "Lesson05 visual receipt")
    manifest_sha = common.sha256(manifest_payload)
    manifest_rows = list(
        csv.DictReader(io.StringIO(manifest_payload.decode("utf-8")))
    )
    if len(manifest_rows) != 50:
        raise RuntimeError(
            f"expected exactly 50 reader-manifest rows, found {len(manifest_rows)}"
        )
    manifest_reader_bytes = sum(int(row["bytes"]) for row in manifest_rows)

    if build.get("schema") != "o006.stat415.through-lesson05-build.v1":
        raise RuntimeError("unexpected cumulative build schema")
    if build.get("status") != "built" or build.get("coverage") != EXPECTED_COVERAGE:
        raise RuntimeError("build receipt is not the exact 7-of-14 boundary")
    if build.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("build receipt has wrong model provenance")
    reader = build.get("reader", {})
    if (
        reader.get("files") != 50
        or reader.get("bytes") != manifest_reader_bytes
        or reader.get("manifest_sha256") != manifest_sha
        or reader.get("path") != "build/html-id"
    ):
        raise RuntimeError("build receipt does not bind the exact 50-file reader")
    if (
        build.get("translation_segments") != 2_311
        or build.get("structural_units_normalized") != 3_209
        or build.get("structural_units_target") != 3_207
        or build.get("math_nodes", {}).get("total") != 1_546
        or build.get("corrections", {}).get("count") != 112
    ):
        raise RuntimeError("build receipt cumulative counts differ")
    if build.get("math_nodes") != {
        key: value for key, value in EXPECTED_MATH.items() if key != "licenses"
    } | {"total": 1_546}:
        raise RuntimeError("build receipt per-document math census differs")
    rights = build.get("rights", {})
    if (
        rights.get("Penn State content")
        != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("MathJax 3.1.2") != "Apache-2.0"
        or rights.get("aggregate_uniform_relicense") is not False
    ):
        raise RuntimeError("build receipt component rights differ")
    lesson05_assets = build.get("lesson05_assets", {})
    if (
        lesson05_assets.get("authority_slots") != 14
        or lesson05_assets.get("count") != 14
        or lesson05_assets.get("seeded_derivatives") != 1
        or lesson05_assets.get("external_iframe_occurrences_removed") != 2
    ):
        raise RuntimeError("Lesson05 asset closure differs")

    if qa.get("schema") != "o006.stat415.through-lesson05-qa.v1":
        raise RuntimeError("unexpected cumulative QA schema")
    if qa.get("status") not in {"pass", "passed"} or qa.get("coverage") != {
        "complete_documents": 7,
        "corpus_documents": 14,
        "next_document": "Lesson06",
    }:
        raise RuntimeError("deterministic QA has not passed for 7 of 14")
    qa_reader = qa.get("reader", {})
    if (
        qa_reader.get("files") != 50
        or qa_reader.get("bytes") != manifest_reader_bytes
        or qa_reader.get("manifest", {}).get("sha256") != manifest_sha
        or qa_reader.get("stable_units") != 3_207
        or qa_reader.get("math_nodes") != 1_546
    ):
        raise RuntimeError("QA receipt does not bind the exact reader")
    correction_qa = qa.get("structure_math_and_corrections", {})
    if (
        correction_qa.get("corrections") != 112
        or correction_qa.get("historical_prefix") != 81
        or correction_qa.get("lesson05_corrections") != 31
        or correction_qa.get("changed_math_nodes") != 11
    ):
        raise RuntimeError("QA correction closure differs")
    asset_qa = qa.get("asset", {})
    if (
        asset_qa.get("images") != 14
        or asset_qa.get("reader_asset_files") != 14
        or asset_qa.get("seeded_derivatives") != 1
        or asset_qa.get("static_video_fallbacks") != 2
    ):
        raise RuntimeError("QA asset closure differs")

    if visual.get("schema") != "o006.stat415.through-lesson05-visual-qa.v1":
        raise RuntimeError("unexpected cumulative visual-QA schema")
    if visual.get("status") != "pass" or visual.get("coverage") != VISUAL_COVERAGE:
        raise RuntimeError("desktop/mobile visual QA has not passed for 7 of 14")
    evidence = visual.get("evidence", {})
    if evidence.get("manifest", {}).get("sha256") != manifest_sha:
        raise RuntimeError("visual QA does not bind the reader manifest")
    if evidence.get("build_receipt", {}).get("sha256") != common.sha256(build_payload):
        raise RuntimeError("visual QA does not bind the build receipt")
    if evidence.get("qa_receipt", {}).get("sha256") != common.sha256(qa_payload):
        raise RuntimeError("visual QA does not bind the QA receipt")
    if visual.get("provenance") != PROVENANCE:
        raise RuntimeError("visual QA has wrong model provenance")
    for viewport in ("desktop", "mobile"):
        view = visual.get(viewport, {})
        if view.get("console_errors_or_warnings") != 0:
            raise RuntimeError(f"visual QA reports {viewport} browser warnings or errors")
        routes = view.get("routes", {})
        if set(routes) != set(EXPECTED_MATH):
            raise RuntimeError(f"visual QA {viewport} route closure differs")
        for route, expected_math in EXPECTED_MATH.items():
            result = routes.get(route, {})
            if (
                result.get("broken_images") != 0
                or result.get("page_horizontal_overflow") is not False
                or result.get("source_math_nodes") != expected_math
                or result.get("rendered_math_containers") != expected_math
            ):
                raise RuntimeError(
                    f"visual QA {viewport} result differs for route {route}"
                )
            if (
                viewport == "mobile"
                and result.get("navigation_horizontal_overflow") is not False
            ):
                raise RuntimeError(f"mobile navigation overflows for route {route}")

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
    if len(rows) != 50:
        raise RuntimeError(f"expected exactly 50 reader files, found {len(rows)}")

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
    root = PurePosixPath("stat415-id-through-lesson05")
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
    if actual_paths != manifested:
        missing = sorted(path.as_posix() for path in manifested - actual_paths)
        extra = sorted(path.as_posix() for path in actual_paths - manifested)
        raise RuntimeError(f"reader inventory differs; missing={missing}; extra={extra}")

    embedded = root / "THROUGH_LESSON05_MANIFEST.csv"
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


def notes_payload(reader_files: int, reader_bytes: int) -> bytes:
    formatted_reader_bytes = f"{reader_bytes:,}".replace(",", ".")
    return (
        "# STAT 415 — edisi Bahasa Indonesia: hingga Pelajaran 05\n\n"
        "Status: **sebagian; 7 dari 14 dokumen lengkap**. Paket ini memuat "
        "laman utama serta seluruh Pelajaran 00–05 dalam Bahasa Indonesia. "
        "Pelajaran 06–12 belum diterjemahkan dan tetap menaut ke sumber resmi "
        "berbahasa Inggris.\n\n"
        f"Pembaca luring adalah berkas utama: {reader_files} berkas pembaca "
        f"dengan {formatted_reader_bytes} byte. Ekstrak ZIP pembaca, layani "
        "direktori hasil ekstraksi "
        "melalui peladen HTTP statis, lalu buka `index.html`. Paket source-backend "
        "ringkas memuat otoritas beku, authoring source, 2.311 segmen "
        "terjemahan, backend modular, skrip reproduksi, kontrol semantik, "
        "lisensi, dan bukti QA yang diperlukan untuk melanjutkan edisi. Batas "
        "ini memuat 3.209 unit sumber, 3.207 unit target, 1.546 permukaan "
        "matematika, dan 112 koreksi turunan terverifikasi.\n\n"
        "Pelajaran 05 memuat empat belas gambar luring. Tiga belas slot memakai "
        "byte otoritas beku; satu histogram simulasi adalah turunan dengan seed "
        "tetap yang diungkapkan. Dua iframe video pihak ketiga tidak dibundel dan diganti "
        "dengan fallback statis yang mempertahankan konteks instruksional.\n\n"
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
        RELEASE_NOTES: notes_payload(
            reader_info["reader_files"], reader_info["reader_bytes"]
        ),
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
            "schema": "o006.stat415.through-lesson05-release-root.v1",
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
            "schema": "o006.stat415.through-lesson05-package.v1",
            "status": "ready",
            "coverage": {
                **EXPECTED_COVERAGE,
                "statement": (
                    "landing/index plus complete Lesson00-Lesson05; "
                    "7 of 14 documents"
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
        for relative, data in outputs.items():
            path = ROOT / relative
            if path.exists() and path.is_dir():
                raise RuntimeError(f"release output collides with a directory: {relative}")
            common.atomic_write(path, data)
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
