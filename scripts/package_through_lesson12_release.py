#!/usr/bin/env python3
"""Create the deterministic reader-first complete STAT 415 release.

The release closes the official fourteen-document Penn State spine: the
landing page and Lessons 00--12.  Every source-package member is explicitly
allowlisted.  The script never discovers repository inputs recursively and it
excludes credentials, publication transactions, volatile cursors, caches, and
unrelated follow-on components.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

import package_through_lesson11_release as prior


ROOT = Path(__file__).resolve().parents[1]
common = prior.common
READER = ROOT / "build" / "html-id"

READER_ZIP = "00_stat415-id-through-lesson12-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson12-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON12_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_THROUGH_LESSON12_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON12_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS_THROUGH_LESSON12.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON12_PACKAGE_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = ["index", *[f"Lesson{i:02d}" for i in range(13)]]
EXPECTED_COVERAGE = {
    "complete_count": 14,
    "complete_documents": COMPLETE_DOCUMENTS,
    "corpus_document_count": 14,
    "next_document": None,
    "pending_documents": [],
}
VISUAL_COVERAGE = "landing/index plus complete Lesson00 through Lesson12 and licenses"
EXPECTED_READER_FILES = 106
EXPECTED_READER_BYTES = 17_614_553
EXPECTED_MANIFEST_SHA = "697c9ee8e23cc10469fea4d1894e16471ffb4276edd1f0d25bebfb5be0dbe79e"
EXPECTED_NEW_ASSETS = 9
EXPECTED_NEW_ASSET_OCCURRENCES = 10
EXPECTED_NEW_ASSET_BYTES = 233_075
EXPECTED_TRANSLATION_SEGMENTS = 4_932
EXPECTED_SOURCE_UNITS = 6_510
EXPECTED_TARGET_UNITS = 6_498
EXPECTED_MATH_NODES = 3_156
EXPECTED_CORRECTIONS = 242
EXPECTED_GLOSSARY_PREFIX_ROWS = 192
EXPECTED_GLOSSARY_PREFIX_BYTES = 20_340
EXPECTED_GLOSSARY_PREFIX_SHA = "554dcbfb5161df6f0eb86027822eabbf4fae9179bb152947a8ad6c196cb34b05"


# Exact extension of the reviewed 13-of-14 source closure.  The list names
# the final lesson's authority, authoring source, modular backend, translation
# evidence, build/QA evidence, and every redistributed asset individually.
ADDITIONAL_SOURCE_PACKAGE_FILES = (
    "scripts/freeze_lesson12_assets.py",
    "scripts/normalize_lesson12.py",
    "scripts/build_lesson12_translation_batches.py",
    "scripts/lesson12_corrections.py",
    "scripts/merge_lesson12_translations.py",
    "scripts/materialize_lesson12_translation.py",
    "scripts/build_through_lesson12.py",
    "scripts/qa_through_lesson12.py",
    "scripts/package_through_lesson12_release.py",
    "scripts/update_lesson12_translation_ledger.py",
    "scripts/extend_adverse_ledger_lesson12.py",
    "scripts/write_lesson12_visual_receipt.py",
    "authority/upstream/stat415/Lesson12.html",
    "authority/LESSON12_ASSET_MANIFEST.csv",
    "authority/LESSON12_ASSET_FREEZE_RECEIPT.json",
    "authority/LESSON12_VIDEO_PROVENANCE.csv",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-lesson9_1-1.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-skin-cancer-1.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-htwt1-1.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-gpavsentrance3-1.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-samplegpaentrance4-1.png",
    "authority/assets/stat415/lesson12/assets/lesson9_11.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-scattertemp-1.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-scattertemp2-1.png",
    "authority/assets/stat415/lesson12/Lesson12_files/figure-html/fig-iqnormal-1.png",
    "source/normalized/en-US/Lesson12.html",
    "source/id-ID/Lesson12.html",
    "source/id-ID/lesson12_translation.csv",
    "backend/lesson12_source_catalogue.jsonl",
    "backend/lesson12_translation_bindings.jsonl",
    "backend/lesson12_target_corrections.jsonl",
    "backend/lesson12_target_native_id_map.jsonl",
    "backend/through_lesson12_documents.jsonl",
    "backend/through_lesson12_corrections.jsonl",
    "working/lesson12_segments.csv",
    "working/lesson12_asset_inventory.csv",
    "working/lesson12_video_inventory.csv",
    "working/lesson12_math_audit.md",
    "working/lesson12_source_findings.md",
    "working/lesson12_terminology_qa.md",
    "working/lesson12_translation_batch_A.csv",
    "working/lesson12_translation_batch_B.csv",
    "working/lesson12_translation_batch_C.csv",
    "working/through_lesson12_visual_observations.template.json",
    "working/through_lesson12_visual_observations.json",
    "build/LESSON12_NORMALIZATION_RECEIPT.json",
    "build/LESSON12_TRANSLATION_RECEIPT.json",
    "build/LESSON12_MATERIALIZATION_RECEIPT.json",
    "build/THROUGH_LESSON12_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON12_MANIFEST.csv",
    "build/THROUGH_LESSON12_QA_RECEIPT.json",
    "build/THROUGH_LESSON12_VISUAL_QA_RECEIPT.json",
)
SOURCE_PACKAGE_FILES = prior.SOURCE_PACKAGE_FILES + ADDITIONAL_SOURCE_PACKAGE_FILES


def snapshot_source_files() -> dict[PurePosixPath, bytes]:
    relatives = [common.safe_relative(value) for value in SOURCE_PACKAGE_FILES]
    folded = [relative.as_posix().casefold() for relative in relatives]
    if len(set(folded)) != len(folded):
        duplicates = sorted({value for value in folded if folded.count(value) > 1})
        raise RuntimeError(f"case-insensitive duplicate in source-package allowlist: {duplicates}")
    snapshot: dict[PurePosixPath, bytes] = {}
    for relative in relatives:
        common.reject_sensitive_source_name(relative)
        payload = common.read_confined_regular_file(ROOT, relative, relative.as_posix())
        # Follow-on donor/companion work may later extend the shared glossary.
        # This component release always freezes the exact admitted 192-row
        # Penn State prefix instead of leaking future terminology into it.
        if relative == PurePosixPath("00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv"):
            lines = payload.splitlines(keepends=True)
            if len(lines) < EXPECTED_GLOSSARY_PREFIX_ROWS + 1:
                raise RuntimeError("live glossary no longer contains the admitted Lesson12 prefix")
            payload = b"".join(lines[: EXPECTED_GLOSSARY_PREFIX_ROWS + 1])
            if (
                len(payload) != EXPECTED_GLOSSARY_PREFIX_BYTES
                or common.sha256(payload) != EXPECTED_GLOSSARY_PREFIX_SHA
            ):
                raise RuntimeError("admitted Lesson12 glossary prefix identity differs")
        common.reject_machine_local_text(relative, payload)
        snapshot[relative] = payload
    return snapshot


def validate_receipts(source: dict[PurePosixPath, bytes]) -> dict[str, bytes]:
    def admitted(relative: str) -> bytes:
        try:
            return source[PurePosixPath(relative)]
        except KeyError as exc:
            raise RuntimeError(f"validated input absent from allowlist: {relative}") from exc

    build_payload = admitted("build/THROUGH_LESSON12_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON12_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON12_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON12_MANIFEST.csv")
    build = common.decode_json_object(build_payload, "Lesson12 cumulative build receipt")
    qa = common.decode_json_object(qa_payload, "Lesson12 cumulative QA receipt")
    visual = common.decode_json_object(visual_payload, "Lesson12 cumulative visual QA receipt")

    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != EXPECTED_READER_FILES:
        raise RuntimeError(f"reader manifest is not the exact 106-file boundary: {len(rows)}")
    manifest_bytes = sum(int(row["bytes"]) for row in rows)
    manifest_sha = common.sha256(manifest_payload)
    if manifest_sha != EXPECTED_MANIFEST_SHA or manifest_bytes != EXPECTED_READER_BYTES:
        raise RuntimeError("reader manifest identity differs from the admitted complete boundary")

    if (
        build.get("schema") != "o006.stat415.through-lesson12-build.v1"
        or build.get("status") != "built"
        or build.get("coverage") != EXPECTED_COVERAGE
        or build.get("translation_provenance") != PROVENANCE
        or build.get("translation_segments") != EXPECTED_TRANSLATION_SEGMENTS
        or build.get("structural_units_normalized") != EXPECTED_SOURCE_UNITS
        or build.get("structural_units_target") != EXPECTED_TARGET_UNITS
        or build.get("math_nodes", {}).get("total") != EXPECTED_MATH_NODES
        or build.get("corrections", {}).get("count") != EXPECTED_CORRECTIONS
        or build.get("reader", {}).get("files") != EXPECTED_READER_FILES
        or build.get("reader", {}).get("bytes") != EXPECTED_READER_BYTES
        or build.get("reader", {}).get("manifest_sha256") != manifest_sha
        or build.get("new_assets", {}).get("count") != EXPECTED_NEW_ASSETS
        or build.get("new_assets", {}).get("occurrences") != EXPECTED_NEW_ASSET_OCCURRENCES
        or build.get("new_assets", {}).get("bytes") != EXPECTED_NEW_ASSET_BYTES
        or build.get("new_assets", {}).get("all_byte_preserving") is not True
        or build.get("offline", {}).get("offline_video_equivalents") != 3
        or build.get("offline", {}).get("third_party_iframes") != 0
        or build.get("offline", {}).get("video_bytes_redistributed") is not False
    ):
        raise RuntimeError("build receipt is not the exact complete Penn State boundary")

    expected_qa_coverage = {
        "complete_documents": 14,
        "corpus_documents": 14,
        "next_document": None,
        "pending_documents": [],
    }
    reader = qa.get("reader_accessibility_reflow", {})
    assets = qa.get("asset_rights_privacy", {})
    structure = qa.get("structure_math_corrections", {})
    translation = qa.get("translation_backend", {})
    if (
        qa.get("schema") != "o006.stat415.through-lesson12-qa.v1"
        or qa.get("status") != "passed"
        or qa.get("coverage") != expected_qa_coverage
        or reader.get("files") != EXPECTED_READER_FILES
        or reader.get("bytes") != EXPECTED_READER_BYTES
        or reader.get("stable_units") != EXPECTED_TARGET_UNITS
        or reader.get("source_units") != EXPECTED_SOURCE_UNITS
        or reader.get("math_nodes") != EXPECTED_MATH_NODES
        or reader.get("substantive_images") != 67
        or reader.get("tables") != 14
        or reader.get("lesson12", {}).get("semantic_tables") != 6
        or reader.get("lesson12", {}).get("image_occurrences") != 10
        or reader.get("lesson12", {}).get("offline_video_equivalents") != 3
        or assets.get("authority_assets") != EXPECTED_NEW_ASSETS
        or assets.get("authority_asset_occurrences") != EXPECTED_NEW_ASSET_OCCURRENCES
        or assets.get("authority_asset_bytes") != EXPECTED_NEW_ASSET_BYTES
        or assets.get("byte_preserving_targets") != EXPECTED_NEW_ASSETS
        or assets.get("offline_video_equivalents") != 3
        or assets.get("video_bytes_redistributed") is not False
        or structure.get("cumulative_corrections") != EXPECTED_CORRECTIONS
        or structure.get("lesson12_corrections") != 24
        or structure.get("stable_units") != 846
        or structure.get("math_nodes") != 352
        or translation.get("new_segments") != 580
        or translation.get("cumulative_segments") != EXPECTED_TRANSLATION_SEGMENTS
    ):
        raise RuntimeError("deterministic QA is not passed for the exact complete boundary")

    if (
        visual.get("schema") != "o006.stat415.through-lesson12-visual-qa.v1"
        or visual.get("status") != "pass"
        or visual.get("coverage") != VISUAL_COVERAGE
        or visual.get("provenance") != PROVENANCE
        or visual.get("evidence", {}).get("manifest", {}).get("sha256") != manifest_sha
        or visual.get("evidence", {}).get("build_receipt", {}).get("sha256") != common.sha256(build_payload)
        or visual.get("evidence", {}).get("qa_receipt", {}).get("sha256") != common.sha256(qa_payload)
        or visual.get("cumulative_results", {}).get("source_math_nodes") != EXPECTED_MATH_NODES
        or visual.get("cumulative_results", {}).get("rendered_math_containers") != EXPECTED_MATH_NODES
        or visual.get("cumulative_results", {}).get("substantive_images") != 67
        or visual.get("cumulative_results", {}).get("loaded_substantive_images") != 67
        or visual.get("cumulative_results", {}).get("tables") != 14
    ):
        raise RuntimeError("visual QA is not bound to the exact complete reader and deterministic QA")
    expected_routes = {*COMPLETE_DOCUMENTS, "licenses"}
    for viewport in ("desktop", "mobile"):
        view = visual.get(viewport, {})
        routes = view.get("routes", {})
        if view.get("console_errors_or_warnings") != 0 or set(routes) != expected_routes:
            raise RuntimeError(f"visual QA {viewport} route closure differs")
        for route, result in routes.items():
            if (
                result.get("broken_images") != 0
                or result.get("page_horizontal_overflow") is not False
                or result.get("navigation_horizontal_overflow") is not False
                or result.get("rendered_math_containers") != result.get("source_math_nodes")
            ):
                raise RuntimeError(f"visual QA differs: {viewport}/{route}")
        lesson12 = routes.get("Lesson12", {})
        if (
            lesson12.get("loaded_images") != 10
            or lesson12.get("centered_substantive_images") != 10
            or lesson12.get("full_width_substantive_images") != 10
            or lesson12.get("tables") != 6
            or lesson12.get("captioned_tables") != 6
            or lesson12.get("tables_with_complete_header_scopes") != 6
            or lesson12.get("offline_video_equivalents") != 3
            or lesson12.get("external_iframes") != 0
            or lesson12.get("offline_video_equivalents_expanded_and_inspected") != 3
            or lesson12.get("offline_video_equivalents_readable_and_unclipped") is not True
            or lesson12.get("code_surfaces") != 1
            or lesson12.get("hidden_code_surfaces") != 0
        ):
            raise RuntimeError(f"Lesson12 visual evidence differs at {viewport}")

    license_payload = admitted("LICENSE.md")
    license_text = license_payload.decode("utf-8")
    for required in ("CC BY-NC 4.0", "Apache License 2.0", "CC BY-SA 4.0"):
        if required not in license_text:
            raise RuntimeError(f"component right missing from LICENSE.md: {required}")

    ledger_payload = admitted("00_control/TRANSLATION_LEDGER.csv")
    ledger = list(csv.DictReader(io.StringIO(ledger_payload.decode("utf-8"))))
    if len(ledger) != 14 or [row.get("document_id") for row in ledger] != [f"O006-PSU-{i:03d}" for i in range(14)]:
        raise RuntimeError("translation ledger is not the ordered 14-document boundary")
    if any(row.get("status") != "complete" for row in ledger):
        raise RuntimeError("translation ledger contains a non-complete row")
    lesson12_target = next(
        (item for item in build.get("target_documents", []) if item.get("path") == "source/id-ID/Lesson12.html"),
        None,
    )
    last = ledger[-1]
    if (
        not isinstance(lesson12_target, dict)
        or last.get("target_path") != lesson12_target.get("path")
        or int(last.get("target_bytes", -1)) != lesson12_target.get("bytes")
        or last.get("target_sha256") != lesson12_target.get("sha256")
        or last.get("segments") != "580"
        or last.get("structures") != "846"
        or last.get("math_nodes") != "352"
        or last.get("qa_receipt") != "build/THROUGH_LESSON12_QA_RECEIPT.json"
    ):
        raise RuntimeError("Lesson12 translation-ledger row is not bound to the current target")

    adverse_payload = admitted("00_control/ADVERSE_LEDGER.jsonl")
    adverse = [json.loads(line) for line in adverse_payload.decode("utf-8").splitlines() if line.strip()]
    if [row.get("correction_id") for row in adverse] != [f"O006-PSU-ADV-{i:04d}" for i in range(1, EXPECTED_CORRECTIONS + 1)]:
        raise RuntimeError("adverse ledger is not the exact ordered 242-correction boundary")
    if [row.get("source_defect_id") for row in adverse[-24:]] != [f"L12-D{i:03d}" for i in range(1, 25)]:
        raise RuntimeError("Lesson12 adverse-ledger suffix is not the exact L12-D001 through L12-D024 boundary")
    return {
        "build": build_payload,
        "qa": qa_payload,
        "visual": visual_payload,
        "manifest": manifest_payload,
        "license": license_payload,
    }


def reader_package(manifest_payload: bytes) -> tuple[bytes, dict[str, Any]]:
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != EXPECTED_READER_FILES:
        raise RuntimeError("reader manifest does not contain 106 files")
    actual: set[PurePosixPath] = set()
    for path in READER.rglob("*"):
        relative = PurePosixPath(path.relative_to(READER).as_posix())
        if path.is_symlink():
            raise RuntimeError(f"symlinked reader input forbidden: {relative}")
        if path.is_file():
            actual.add(relative)
    root = PurePosixPath("stat415-id-through-lesson12")
    files: dict[PurePosixPath, bytes] = {}
    manifested: set[PurePosixPath] = set()
    reader_bytes = 0
    for row in rows:
        relative = common.safe_relative(row["relative_path"])
        data = common.read_confined_regular_file(READER, relative, relative.as_posix())
        if relative in manifested or len(data) != int(row["bytes"]) or common.sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {relative}")
        manifested.add(relative)
        reader_bytes += len(data)
        files[root / relative] = data
    if actual != manifested:
        raise RuntimeError(f"reader inventory differs; missing={sorted(manifested-actual)}; extra={sorted(actual-manifested)}")
    files[root / "THROUGH_LESSON12_MANIFEST.csv"] = manifest_payload
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
    allowlist = common.canonical_json([
        {"path": relative.as_posix(), "bytes": len(data), "sha256": common.sha256(data)}
        for relative, data in sorted(source.items(), key=lambda item: item[0].as_posix().casefold())
    ])
    return payload, {
        "entries": len(files),
        "uncompressed_bytes": sum(len(value) for value in files.values()),
        "allowlist_manifest_sha256": common.sha256(allowlist),
        "archive_method": "ZIP_STORED",
    }


def notes_payload(reader_files: int, reader_bytes: int) -> bytes:
    formatted = f"{reader_bytes:,}".replace(",", ".")
    return (
        "# STAT 415 — edisi Bahasa Indonesia lengkap\n\n"
        "Status komponen: **lengkap; 14 dari 14 dokumen**. Paket ini memuat laman utama "
        "serta seluruh Pelajaran 00–12 dalam Bahasa Indonesia. Status ini menyatakan "
        "kelengkapan spine eksternal Penn State, bukan kelengkapan seluruh kursus C140; "
        "unit kelengkapan/suffisiensi dan pendamping rigor-simulasi-mastery tetap komponen terpisah.\n\n"
        f"Pembaca luring adalah berkas utama: {reader_files} berkas dengan {formatted} byte. "
        "Ekstrak ZIP, layani direktorinya melalui peladen HTTP statis, lalu buka `index.html`. "
        "Paket source-backend memuat otoritas, authoring source, backend modular, aset Lesson 12, "
        "skrip reproduksi, lisensi, serta bukti build, QA deterministik, dan QA visual.\n\n"
        "Konten Penn State dan adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan lain; "
        "MathJax 3.1.2 tetap Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. "
        "Koleksi tidak direlisensi secara seragam dan tidak ada pengesahan tersirat. "
        "Sembilan gambar Lesson 12 dipertahankan byte-for-byte; tiga video eksternal tidak "
        "didistribusikan dan diganti dengan padanan tekstual luring beserta tautan sumber.\n\n"
        f"Provenans terjemahan: {PROVENANCE}. Seluruh kredit sumber dan kontributor manusia dipertahankan.\n"
    ).encode("utf-8")


def compute() -> tuple[dict[str, bytes], bytes]:
    source = snapshot_source_files()
    validated = validate_receipts(source)
    reader_zip, reader_info = reader_package(validated["manifest"])
    source_zip, source_info = source_package(source)
    payloads: dict[str, bytes] = {
        READER_ZIP: reader_zip,
        SOURCE_ZIP: source_zip,
        RELEASE_NOTES: notes_payload(reader_info["reader_files"], reader_info["reader_bytes"]),
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
    writer = csv.DictWriter(output, fieldnames=("filename", "bytes", "sha256", "role"), lineterminator="\n")
    writer.writeheader()
    for filename in substantive:
        data = payloads[filename]
        writer.writerow({"filename": filename, "bytes": len(data), "sha256": common.sha256(data), "role": roles[filename]})
    payloads[RELEASE_MANIFEST] = output.getvalue().encode("utf-8")
    roles[RELEASE_MANIFEST] = "six-substantive-assets-manifest"
    payloads[CHECKSUMS] = "".join(f"{common.sha256(data)}  {filename}\n" for filename, data in payloads.items()).encode("utf-8")
    roles[CHECKSUMS] = "sha256-for-substantive-assets-and-manifest"
    covered = list(payloads)
    payloads[ROOT_RECEIPT] = common.canonical_json({
        "schema": "o006.stat415.through-lesson12-release-root.v1",
        "status": "ready",
        "coverage": EXPECTED_COVERAGE,
        "self_exclusion": {"filename": ROOT_RECEIPT, "reason": "non-self-referential cryptographic root"},
        "inventory_semantics": {
            "release_manifest": {"filename": RELEASE_MANIFEST, "covers": substantive, "excludes": [RELEASE_MANIFEST, CHECKSUMS, ROOT_RECEIPT]},
            "sha256sums": {"filename": CHECKSUMS, "covers": substantive + [RELEASE_MANIFEST], "excludes": [CHECKSUMS, ROOT_RECEIPT]},
            "root_receipt": {"filename": ROOT_RECEIPT, "covers": covered, "excludes": [ROOT_RECEIPT]},
        },
        "files": [
            {"filename": filename, "bytes": len(payloads[filename]), "sha256": common.sha256(payloads[filename]), "role": roles[filename]}
            for filename in covered
        ],
        "file_count": len(covered),
        "total_bytes": sum(len(payloads[name]) for name in covered),
        "upload_order": covered,
    })
    inputs = {
        "reader_manifest": validated["manifest"],
        "build_receipt": validated["build"],
        "qa_receipt": validated["qa"],
        "visual_qa_receipt": validated["visual"],
        "license": validated["license"],
    }
    receipt = common.canonical_json({
        "schema": "o006.stat415.through-lesson12-package.v1",
        "status": "ready",
        "coverage": {**EXPECTED_COVERAGE, "statement": "landing/index plus complete Lesson00-Lesson12; 14 of 14 Penn State documents"},
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "rights": {
            "penn_state": "CC BY-NC 4.0 except where otherwise noted",
            "mathjax_3_1_2": "Apache-2.0",
            "original_repository_layer": "CC BY-SA 4.0",
            "aggregate_uniform_relicense": False,
        },
        "inputs": {name: {"bytes": len(data), "sha256": common.sha256(data)} for name, data in inputs.items()},
        "files": [{"filename": filename, "bytes": len(data), "sha256": common.sha256(data)} for filename, data in payloads.items()],
        "file_count": len(payloads),
        "total_bytes": sum(len(data) for data in payloads.values()),
        "primary_file": READER_ZIP,
        "reader_zip": {"filename": READER_ZIP, **reader_info},
        "source_zip": {"filename": SOURCE_ZIP, **source_info},
        "upload_order": list(payloads),
    })
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
    print(json.dumps({
        "mode": state,
        "files": info["file_count"],
        "bytes": info["total_bytes"],
        "reader_files": info["reader_zip"]["reader_files"],
        "source_entries": info["source_zip"]["entries"],
        "receipt_sha256": common.sha256(receipt),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
