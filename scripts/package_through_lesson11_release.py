#!/usr/bin/env python3
"""Create a deterministic reader-first 13-of-14 STAT 415 release.

The package is an explicit, bounded closure. It never walks the repository to
discover source-package inputs and deliberately excludes credentials, volatile
cursors, publication transactions, caches, obsolete normalization duplicates,
and unrelated future lessons.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

import package_through_lesson10_release as prior


ROOT = Path(__file__).resolve().parents[1]
common = prior.common
READER = ROOT / "build" / "html-id"

READER_ZIP = "00_stat415-id-through-lesson11-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson11-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON11_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_THROUGH_LESSON11_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON11_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON11_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_THROUGH_LESSON11_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS_THROUGH_LESSON11.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON11_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON11_PACKAGE_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = ["index", *[f"Lesson{i:02d}" for i in range(12)]]
EXPECTED_COVERAGE = {
    "complete_count": 13,
    "complete_documents": COMPLETE_DOCUMENTS,
    "corpus_document_count": 14,
    "next_document": "Lesson12",
}
VISUAL_COVERAGE = "landing/index plus complete Lesson00 through Lesson11 and licenses"
EXPECTED_READER_FILES = 96
EXPECTED_READER_BYTES = 17_232_761
EXPECTED_MANIFEST_SHA = "026ac69ce34ceb77d3174ff167621043bd9ff5d2e5ce82124b8bec3faf365173"
EXPECTED_NEW_ASSETS = 1
EXPECTED_NEW_ASSET_BYTES = 142_195
EXPECTED_TRANSLATION_SEGMENTS = 4_352
EXPECTED_SOURCE_UNITS = 5_664
EXPECTED_TARGET_UNITS = 5_652
EXPECTED_MATH_NODES = 2_804
EXPECTED_CORRECTIONS = 218
EXPECTED_LEDGER_BYTES = 5_417
EXPECTED_LEDGER_SHA = "d674909cce4e6ed9a144eda1808fff6634f1b0d91748df94241dfedd6a278a2f"
EXPECTED_ADVERSE_BYTES = 315_281
EXPECTED_ADVERSE_SHA = "376515c286f48ee5f648097cfa093b2b305e7dec9c67e6ca986300815fc2c17d"
EXPECTED_GLOSSARY_PREFIX_ROWS = 168
EXPECTED_GLOSSARY_PREFIX_BYTES = 17_727
EXPECTED_GLOSSARY_PREFIX_SHA = "1bbc59cbd21477d7f030471bcd2d47001c37cdb4d7781b7a7e24dc2aa3c80b65"


# This is the sole extension to the reviewed 12-of-14 source closure. Every
# input is named individually. In particular, the obsolete duplicate files
# working/lesson11_normalized.html, working/lesson11_source_catalogue.jsonl,
# and working/lesson11_normalization_receipt.json are intentionally absent.
ADDITIONAL_SOURCE_PACKAGE_FILES = (
    "scripts/freeze_lesson11_asset.py",
    "scripts/normalize_lesson11.py",
    "scripts/lesson11_corrections.py",
    "scripts/merge_lesson11_translations.py",
    "scripts/build_through_lesson11.py",
    "scripts/qa_through_lesson11.py",
    "scripts/package_through_lesson11_release.py",
    "scripts/verify_github_release_lesson11.py",
    "scripts/verify_github_checkpoint_lesson11.py",
    "scripts/publish_zenodo_through_lesson11.py",
    "scripts/update_lesson11_translation_ledger.py",
    "scripts/write_lesson11_visual_receipt.py",
    "scripts/extend_adverse_ledger_lesson11.py",
    "authority/upstream/stat415/Lesson11.html",
    "authority/LESSON11_ASSET_MANIFEST.csv",
    "authority/LESSON11_ASSET_FREEZE_RECEIPT.json",
    "authority/assets/stat415/lesson11/assets/bayes.png",
    "source/normalized/en-US/Lesson11.html",
    "source/id-ID/Lesson11.html",
    "source/id-ID/lesson11_translation.csv",
    "backend/lesson11_source_catalogue.jsonl",
    "backend/lesson11_translation_bindings.jsonl",
    "backend/through_lesson11_documents.jsonl",
    "backend/through_lesson11_corrections.jsonl",
    "working/lesson11_segments.csv",
    "working/lesson11_asset_inventory.csv",
    "working/lesson11_math_audit.md",
    "working/lesson11_source_findings.md",
    "working/lesson11_terminology_qa.md",
    "working/lesson11_translation_batch_A.csv",
    "working/lesson11_translation_batch_B.csv",
    "working/lesson11_translation_batch_C.csv",
    "build/LESSON11_NORMALIZATION_RECEIPT.json",
    "build/LESSON11_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON11_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON11_MANIFEST.csv",
    "build/THROUGH_LESSON11_QA_RECEIPT.json",
    "build/THROUGH_LESSON11_VISUAL_QA_RECEIPT.json",
    "00_control/CHECKPOINT_2026-08-26_THROUGH_LESSON11_LOCAL_COMPLETE.md",
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
        # Lesson 12 production may already have extended the shared live
        # glossary while this 13-of-14 boundary is being packaged.  Freeze the
        # exact admitted Lesson 11 prefix in the release rather than leaking
        # future, not-yet-released terminology into this checkpoint.
        if relative == PurePosixPath("00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv"):
            lines = payload.splitlines(keepends=True)
            if len(lines) < EXPECTED_GLOSSARY_PREFIX_ROWS + 1:
                raise RuntimeError("live glossary no longer contains the admitted Lesson11 prefix")
            payload = b"".join(lines[: EXPECTED_GLOSSARY_PREFIX_ROWS + 1])
            if (
                len(payload) != EXPECTED_GLOSSARY_PREFIX_BYTES
                or common.sha256(payload) != EXPECTED_GLOSSARY_PREFIX_SHA
            ):
                raise RuntimeError("admitted Lesson11 glossary prefix identity differs")
        common.reject_machine_local_text(relative, payload)
        snapshot[relative] = payload
    return snapshot


def _json(source: dict[PurePosixPath, bytes], relative: str, label: str) -> dict[str, Any]:
    try:
        return common.decode_json_object(source[PurePosixPath(relative)], label)
    except KeyError as exc:
        raise RuntimeError(f"validated input absent from allowlist: {relative}") from exc


def validate_receipts(source: dict[PurePosixPath, bytes]) -> dict[str, bytes]:
    def admitted(relative: str) -> bytes:
        try:
            return source[PurePosixPath(relative)]
        except KeyError as exc:
            raise RuntimeError(f"validated input absent from allowlist: {relative}") from exc

    build_payload = admitted("build/THROUGH_LESSON11_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON11_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON11_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON11_MANIFEST.csv")
    build = common.decode_json_object(build_payload, "Lesson11 cumulative build receipt")
    qa = common.decode_json_object(qa_payload, "Lesson11 cumulative QA receipt")
    visual = common.decode_json_object(visual_payload, "Lesson11 cumulative visual QA receipt")
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != EXPECTED_READER_FILES:
        raise RuntimeError(f"reader manifest is not the exact 96-file boundary: {len(rows)}")
    manifest_bytes = sum(int(row["bytes"]) for row in rows)
    manifest_sha = common.sha256(manifest_payload)
    if manifest_sha != EXPECTED_MANIFEST_SHA or manifest_bytes != EXPECTED_READER_BYTES:
        raise RuntimeError("reader manifest identity differs from the admitted 13-of-14 boundary")
    if (
        build.get("schema") != "o006.stat415.through-lesson11-build.v1"
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
        or build.get("new_assets", {}).get("bytes") != EXPECTED_NEW_ASSET_BYTES
        or build.get("new_assets", {}).get("all_byte_preserving") is not True
    ):
        raise RuntimeError("build receipt is not the exact 13-of-14 boundary")
    if (
        qa.get("schema") != "o006.stat415.through-lesson11-qa.v1"
        or qa.get("status") != "passed"
        or qa.get("coverage") != {
            "complete_documents": 13,
            "corpus_documents": 14,
            "next_document": "Lesson12",
            "pending_documents": ["Lesson12"],
        }
        or qa.get("reader_accessibility_reflow", {}).get("files") != EXPECTED_READER_FILES
        or qa.get("reader_accessibility_reflow", {}).get("bytes") != EXPECTED_READER_BYTES
        or qa.get("reader_accessibility_reflow", {}).get("stable_units") != EXPECTED_TARGET_UNITS
        or qa.get("reader_accessibility_reflow", {}).get("source_units") != EXPECTED_SOURCE_UNITS
        or qa.get("reader_accessibility_reflow", {}).get("math_nodes") != EXPECTED_MATH_NODES
        or qa.get("reader_accessibility_reflow", {}).get("substantive_images") != 57
        or qa.get("reader_accessibility_reflow", {}).get("tables") != 8
        or qa.get("asset_rights_privacy", {}).get("authority_assets") != EXPECTED_NEW_ASSETS
        or qa.get("asset_rights_privacy", {}).get("authority_asset_bytes") != EXPECTED_NEW_ASSET_BYTES
        or qa.get("asset_rights_privacy", {}).get("byte_preserving_targets") != EXPECTED_NEW_ASSETS
        or qa.get("structure_math_corrections", {}).get("cumulative_corrections") != EXPECTED_CORRECTIONS
        or qa.get("structure_math_corrections", {}).get("lesson11_corrections") != 20
        or qa.get("structure_math_corrections", {}).get("stable_units") != 264
        or qa.get("structure_math_corrections", {}).get("math_nodes") != 264
        or qa.get("translation_backend", {}).get("new_segments") != 354
        or qa.get("translation_backend", {}).get("cumulative_segments") != EXPECTED_TRANSLATION_SEGMENTS
    ):
        raise RuntimeError("deterministic QA is not passed for the exact 13-of-14 boundary")
    if (
        visual.get("schema") != "o006.stat415.through-lesson11-visual-qa.v1"
        or visual.get("status") != "pass"
        or visual.get("coverage") != VISUAL_COVERAGE
        or visual.get("provenance") != PROVENANCE
        or visual.get("evidence", {}).get("manifest", {}).get("sha256") != manifest_sha
        or visual.get("evidence", {}).get("build_receipt", {}).get("sha256") != common.sha256(build_payload)
        or visual.get("evidence", {}).get("qa_receipt", {}).get("sha256") != common.sha256(qa_payload)
        or visual.get("cumulative_results", {}).get("source_math_nodes") != EXPECTED_MATH_NODES
        or visual.get("cumulative_results", {}).get("rendered_math_containers") != EXPECTED_MATH_NODES
        or visual.get("cumulative_results", {}).get("substantive_images") != 57
        or visual.get("cumulative_results", {}).get("loaded_substantive_images") != 57
        or visual.get("cumulative_results", {}).get("tables") != 8
    ):
        raise RuntimeError("visual QA is not bound to the exact 13-of-14 reader and deterministic QA")
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
        lesson11 = routes.get("Lesson11", {})
        if (
            lesson11.get("stable_units") != 264
            or lesson11.get("loaded_images") != 1
            or lesson11.get("centered_substantive_images") != 1
            or lesson11.get("full_width_substantive_images") != 1
            or lesson11.get("tables") != 1
            or lesson11.get("captioned_tables") != 1
            or lesson11.get("tables_with_complete_header_scopes") != 1
            or lesson11.get("code_surfaces") != 4
            or lesson11.get("hidden_code_surfaces") != 0
        ):
            raise RuntimeError(f"Lesson11 visual evidence differs at {viewport}")

    license_payload = admitted("LICENSE.md")
    license_text = license_payload.decode("utf-8")
    for required in ("CC BY-NC 4.0", "Apache License 2.0", "CC BY-SA 4.0"):
        if required not in license_text:
            raise RuntimeError(f"component right missing from LICENSE.md: {required}")
    ledger_payload = admitted("00_control/TRANSLATION_LEDGER.csv")
    ledger = list(csv.DictReader(io.StringIO(ledger_payload.decode("utf-8"))))
    if len(ledger) != 13 or [row.get("document_id") for row in ledger] != [f"O006-PSU-{i:03d}" for i in range(13)]:
        raise RuntimeError("translation ledger is not the ordered 13-document boundary")
    if len(ledger_payload) != EXPECTED_LEDGER_BYTES or common.sha256(ledger_payload) != EXPECTED_LEDGER_SHA:
        raise RuntimeError("translation ledger byte identity differs from the admitted 13-row historical ledger")
    if [row.get("qa_receipt") for row in ledger] != ["build/THROUGH_LESSON10_QA_RECEIPT.json"] * 12 + ["build/THROUGH_LESSON11_QA_RECEIPT.json"]:
        raise RuntimeError("translation ledger QA-boundary sequence differs")
    if any(row.get("status") != "complete" for row in ledger):
        raise RuntimeError("translation ledger contains a non-complete row")
    # Rows 000–011 are an intentionally immutable historical prefix whose
    # target hashes describe their prior cumulative checkpoint. Bind the newly
    # appended Lesson11 row to the live 13-of-14 target without rewriting that
    # provenance history.
    lesson11_target = next(
        (item for item in build.get("target_documents", []) if item.get("path") == "source/id-ID/Lesson11.html"),
        None,
    )
    last = ledger[-1]
    if (
        not isinstance(lesson11_target, dict)
        or last.get("target_path") != lesson11_target.get("path")
        or int(last.get("target_bytes", -1)) != lesson11_target.get("bytes")
        or last.get("target_sha256") != lesson11_target.get("sha256")
        or last.get("segments") != "354"
        or last.get("structures") != "264"
        or last.get("math_nodes") != "264"
    ):
        raise RuntimeError("Lesson11 translation-ledger row is not bound to the current target")
    adverse_payload = admitted("00_control/ADVERSE_LEDGER.jsonl")
    if len(adverse_payload) != EXPECTED_ADVERSE_BYTES or common.sha256(adverse_payload) != EXPECTED_ADVERSE_SHA:
        raise RuntimeError("adverse-ledger byte identity differs from the admitted 218-row boundary")
    adverse = [json.loads(line) for line in adverse_payload.decode("utf-8").splitlines() if line.strip()]
    if [row.get("correction_id") for row in adverse] != [f"O006-PSU-ADV-{i:04d}" for i in range(1, EXPECTED_CORRECTIONS + 1)]:
        raise RuntimeError("adverse ledger is not the exact ordered 218-correction boundary")
    if [row.get("source_defect_id") for row in adverse[-20:]] != [f"L11-D{i:03d}" for i in range(1, 21)]:
        raise RuntimeError("Lesson11 adverse-ledger suffix is not the exact L11-D001 through L11-D020 boundary")
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
        raise RuntimeError("reader manifest does not contain 96 files")
    actual: set[PurePosixPath] = set()
    for path in READER.rglob("*"):
        relative = PurePosixPath(path.relative_to(READER).as_posix())
        if path.is_symlink():
            raise RuntimeError(f"symlinked reader input forbidden: {relative}")
        if path.is_file():
            actual.add(relative)
    root = PurePosixPath("stat415-id-through-lesson11")
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
    files[root / "THROUGH_LESSON11_MANIFEST.csv"] = manifest_payload
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
        "# STAT 415 — edisi Bahasa Indonesia: hingga Pelajaran 11\n\n"
        "Status: **sebagian; 13 dari 14 dokumen lengkap**. Paket ini memuat laman utama "
        "serta seluruh Pelajaran 00–11 dalam Bahasa Indonesia. Pelajaran 12 tetap "
        "ditautkan ke sumber resmi berbahasa Inggris sampai diterjemahkan.\n\n"
        f"Pembaca luring adalah berkas utama: {reader_files} berkas dengan {formatted} byte. "
        "Ekstrak ZIP, layani direktorinya melalui peladen HTTP statis, lalu buka `index.html`. "
        "Paket source-backend memuat otoritas, authoring source, backend modular, aset Lesson 11, "
        "skrip reproduksi, lisensi, serta bukti build, QA, dan visual.\n\n"
        "Konten Penn State dan adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan lain; "
        "MathJax 3.1.2 tetap Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. "
        "Koleksi tidak direlisensi secara seragam dan tidak ada pengesahan tersirat.\n\n"
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
        "schema": "o006.stat415.through-lesson11-release-root.v1",
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
        "schema": "o006.stat415.through-lesson11-package.v1",
        "status": "ready",
        "coverage": {**EXPECTED_COVERAGE, "statement": "landing/index plus complete Lesson00-Lesson11; 13 of 14 documents"},
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
