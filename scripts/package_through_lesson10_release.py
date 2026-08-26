#!/usr/bin/env python3
"""Create a deterministic reader-first 12-of-14 STAT 415 release.

The package is an explicit, bounded closure.  It never walks the repository to
discover inputs and it deliberately excludes credentials, volatile cursors,
publication transactions, caches, and unrelated future lessons.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

import package_through_lesson09_release as prior


ROOT = Path(__file__).resolve().parents[1]
common = prior.common
READER = ROOT / "build" / "html-id"

READER_ZIP = "00_stat415-id-through-lesson10-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson10-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON10_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_THROUGH_LESSON10_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON10_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON10_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_THROUGH_LESSON10_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS_THROUGH_LESSON10.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON10_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON10_PACKAGE_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = ["index", *[f"Lesson{i:02d}" for i in range(11)]]
EXPECTED_COVERAGE = {
    "complete_count": 12,
    "complete_documents": COMPLETE_DOCUMENTS,
    "corpus_document_count": 14,
    "next_document": "Lesson11",
}
VISUAL_COVERAGE = "landing/index plus complete Lesson00 through Lesson10"
EXPECTED_READER_FILES = 94
EXPECTED_READER_BYTES = 17_020_141
EXPECTED_MANIFEST_SHA = "08e171f7b87a1ad33d063ed536fca566873d93993a191d0ad1812fe7259e3663"
EXPECTED_ASSETS = 22
EXPECTED_ASSET_BYTES = 8_313_758


# This is the only extension to the reviewed 11-of-14 source closure.  Asset
# paths are listed individually so a missing or extra component cannot be
# silently pulled into a release by a recursive glob.
ADDITIONAL_SOURCE_PACKAGE_FILES = (
    "scripts/normalize_lesson10.py",
    "scripts/lesson10_corrections.py",
    "scripts/merge_lesson10_translations.py",
    "scripts/build_through_lesson10.py",
    "scripts/qa_through_lesson10.py",
    "scripts/package_through_lesson10_release.py",
    "scripts/verify_github_release_lesson10.py",
    "scripts/verify_github_checkpoint_lesson10.py",
    "scripts/publish_zenodo_through_lesson10.py",
    "scripts/canonicalize_lesson10_batch_a.py",
    "scripts/canonicalize_lesson10_batches.py",
    "scripts/update_lesson10_translation_ledger.py",
    "scripts/write_lesson10_visual_receipt.py",
    "scripts/extend_adverse_ledger_lesson10.py",
    "authority/upstream/stat415/Lesson10.html",
    "authority/LESSON10_ASSET_MANIFEST.csv",
    "authority/assets/stat415/lesson10/assets/ht_example1.jpg",
    "authority/assets/stat415/lesson10/assets/415_rttailengineer.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-02.png",
    "authority/assets/stat415/lesson10/assets/415_engineertype1.png",
    "authority/assets/stat415/lesson10/assets/415_engineertype1-B.png",
    "authority/assets/stat415/lesson10/assets/halfemptyglass.jpg",
    "authority/assets/stat415/lesson10/assets/415_engineerpower.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-06.svg",
    "authority/assets/stat415/lesson10/assets/415_IQpower.png",
    "authority/assets/stat415/lesson10/assets/415_IQpowerB.png",
    "authority/assets/stat415/lesson10/assets/415_IQpowerC.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-10.svg",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-11.svg",
    "authority/assets/stat415/lesson10/assets/415_IQtypeI.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-13 Version 7.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-14.svg",
    "authority/assets/stat415/lesson10/assets/415_IQtypeIB.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-16.svg",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-17.png",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-18.svg",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-19.svg",
    "authority/assets/stat415/lesson10/assets/STAT-415-SEC-5-20.svg",
    "source/normalized/en-US/Lesson10.html",
    "source/id-ID/Lesson10.html",
    "source/id-ID/lesson10_translation.csv",
    "backend/lesson10_source_catalogue.jsonl",
    "backend/lesson10_translation_bindings.jsonl",
    "backend/through_lesson10_documents.jsonl",
    "backend/through_lesson10_corrections.jsonl",
    "working/lesson10_segments.csv",
    "working/lesson10_asset_closure.json",
    "working/lesson10_math_audit.md",
    "working/lesson10_source_findings.md",
    "working/lesson10_terminology_qa.md",
    "working/lesson10_translation_batch_A.csv",
    "working/lesson10_translation_batch_B.csv",
    "working/lesson10_translation_batch_C.csv",
    "working/lesson10_translation_batch_D.csv",
    "build/LESSON10_NORMALIZATION_RECEIPT.json",
    "build/LESSON10_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON10_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON10_MANIFEST.csv",
    "build/THROUGH_LESSON10_QA_RECEIPT.json",
    "build/THROUGH_LESSON10_VISUAL_QA_RECEIPT.json",
    "00_control/CHECKPOINT_2026-08-26_THROUGH_LESSON10_LOCAL_COMPLETE.md",
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
        payload = common.read_confined_regular_file(ROOT, relative, relative.as_posix())
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

    build_payload = admitted("build/THROUGH_LESSON10_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON10_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON10_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON10_MANIFEST.csv")
    build = common.decode_json_object(build_payload, "Lesson10 cumulative build receipt")
    qa = common.decode_json_object(qa_payload, "Lesson10 cumulative QA receipt")
    visual = common.decode_json_object(visual_payload, "Lesson10 cumulative visual QA receipt")
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != EXPECTED_READER_FILES:
        raise RuntimeError(f"reader manifest is not the exact 94-file boundary: {len(rows)}")
    manifest_bytes = sum(int(row["bytes"]) for row in rows)
    manifest_sha = common.sha256(manifest_payload)
    if manifest_sha != EXPECTED_MANIFEST_SHA or manifest_bytes != EXPECTED_READER_BYTES:
        raise RuntimeError("reader manifest identity differs from the admitted 12-of-14 boundary")
    if (
        build.get("schema") != "o006.stat415.through-lesson10-build.v1"
        or build.get("status") != "built"
        or build.get("coverage") != EXPECTED_COVERAGE
        or build.get("translation_provenance") != PROVENANCE
        or build.get("translation_segments") != 3998
        or build.get("structural_units_normalized") != 5400
        or build.get("structural_units_target") != 5388
        or build.get("math_nodes", {}).get("total") != 2540
        or build.get("corrections", {}).get("count") != 198
        or build.get("reader", {}).get("files") != EXPECTED_READER_FILES
        or build.get("reader", {}).get("bytes") != EXPECTED_READER_BYTES
        or build.get("reader", {}).get("manifest_sha256") != manifest_sha
        or build.get("new_assets", {}).get("count") != EXPECTED_ASSETS
        or build.get("new_assets", {}).get("bytes") != EXPECTED_ASSET_BYTES
    ):
        raise RuntimeError("build receipt is not the exact 12-of-14 boundary")
    if (
        qa.get("schema") != "o006.stat415.through-lesson10-qa.v1"
        or qa.get("status") != "passed"
        or qa.get("coverage") != {
            "complete_documents": 12,
            "corpus_documents": 14,
            "next_document": "Lesson11",
        }
        or qa.get("reader_accessibility_reflow", {}).get("files") != EXPECTED_READER_FILES
        or qa.get("reader_accessibility_reflow", {}).get("bytes") != EXPECTED_READER_BYTES
        or qa.get("reader_accessibility_reflow", {}).get("stable_units") != 5388
        or qa.get("reader_accessibility_reflow", {}).get("math_nodes") != 2540
        or qa.get("asset_rights_privacy", {}).get("authority_assets") != EXPECTED_ASSETS
        or qa.get("asset_rights_privacy", {}).get("authority_asset_bytes") != EXPECTED_ASSET_BYTES
        or qa.get("structure_math_corrections", {}).get("cumulative_corrections") != 198
    ):
        raise RuntimeError("deterministic QA is not passed for 12 of 14")
    if (
        visual.get("schema") != "o006.stat415.through-lesson10-visual-qa.v1"
        or visual.get("status") != "pass"
        or visual.get("coverage") != VISUAL_COVERAGE
        or visual.get("provenance") != PROVENANCE
        or visual.get("evidence", {}).get("manifest", {}).get("sha256") != manifest_sha
        or visual.get("evidence", {}).get("build_receipt", {}).get("sha256") != common.sha256(build_payload)
        or visual.get("evidence", {}).get("qa_receipt", {}).get("sha256") != common.sha256(qa_payload)
    ):
        raise RuntimeError("visual QA is not bound to the 12-of-14 reader")
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
                or result.get("rendered_math_containers") != result.get("source_math_nodes")
                or (viewport == "mobile" and result.get("navigation_horizontal_overflow") is not False)
            ):
                raise RuntimeError(f"visual QA differs: {viewport}/{route}")

    license_payload = admitted("LICENSE.md")
    license_text = license_payload.decode("utf-8")
    for required in ("CC BY-NC 4.0", "Apache License 2.0", "CC BY-SA 4.0"):
        if required not in license_text:
            raise RuntimeError(f"component right missing from LICENSE.md: {required}")
    ledger = list(csv.DictReader(io.StringIO(admitted("00_control/TRANSLATION_LEDGER.csv").decode("utf-8"))))
    if len(ledger) != 12 or [row.get("document_id") for row in ledger] != [f"O006-PSU-{i:03d}" for i in range(12)]:
        raise RuntimeError("translation ledger is not the ordered 12-document boundary")
    target_documents = {item["path"]: item for item in build.get("target_documents", [])}
    for row in ledger:
        target = target_documents.get(row.get("target_path", ""))
        if (
            target is None
            or int(row.get("target_bytes", -1)) != target["bytes"]
            or row.get("target_sha256") != target["sha256"]
            or row.get("status") != "complete"
            or row.get("qa_receipt") != "build/THROUGH_LESSON10_QA_RECEIPT.json"
        ):
            raise RuntimeError(f"translation ledger target binding differs: {row.get('document_id')}")
    adverse = [json.loads(line) for line in admitted("00_control/ADVERSE_LEDGER.jsonl").decode("utf-8").splitlines() if line.strip()]
    if [row.get("correction_id") for row in adverse] != [f"O006-PSU-ADV-{i:04d}" for i in range(1, 199)]:
        raise RuntimeError("adverse ledger is not the exact ordered 198-correction boundary")
    return {"build": build_payload, "qa": qa_payload, "visual": visual_payload, "manifest": manifest_payload, "license": license_payload}


def reader_package(manifest_payload: bytes) -> tuple[bytes, dict[str, Any]]:
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != EXPECTED_READER_FILES:
        raise RuntimeError("reader manifest does not contain 94 files")
    actual: set[PurePosixPath] = set()
    for path in READER.rglob("*"):
        relative = PurePosixPath(path.relative_to(READER).as_posix())
        if path.is_symlink():
            raise RuntimeError(f"symlinked reader input forbidden: {relative}")
        if path.is_file():
            actual.add(relative)
    root = PurePosixPath("stat415-id-through-lesson10")
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
    files[root / "THROUGH_LESSON10_MANIFEST.csv"] = manifest_payload
    payload = common.archive(files)
    return payload, {"reader_files": len(rows), "reader_bytes": reader_bytes, "package_entries": len(files), "uncompressed_bytes": sum(len(value) for value in files.values()), "manifest_bytes": len(manifest_payload), "manifest_sha256": common.sha256(manifest_payload), "archive_method": "ZIP_STORED"}


def source_package(source: dict[PurePosixPath, bytes]) -> tuple[bytes, dict[str, Any]]:
    root = PurePosixPath("penn-state-stat-415-id")
    files = {root / relative: data for relative, data in source.items()}
    payload = common.archive(files)
    allowlist = common.canonical_json([{"path": relative.as_posix(), "bytes": len(data), "sha256": common.sha256(data)} for relative, data in sorted(source.items(), key=lambda item: item[0].as_posix().casefold())])
    return payload, {"entries": len(files), "uncompressed_bytes": sum(len(value) for value in files.values()), "allowlist_manifest_sha256": common.sha256(allowlist), "archive_method": "ZIP_STORED"}


def notes_payload(reader_files: int, reader_bytes: int) -> bytes:
    formatted = f"{reader_bytes:,}".replace(",", ".")
    return (
        "# STAT 415 — edisi Bahasa Indonesia: hingga Pelajaran 10\n\n"
        "Status: **sebagian; 12 dari 14 dokumen lengkap**. Paket ini memuat laman utama "
        "serta seluruh Pelajaran 00–10 dalam Bahasa Indonesia. Pelajaran 11–12 tetap "
        "ditautkan ke sumber resmi berbahasa Inggris sampai diterjemahkan.\n\n"
        f"Pembaca luring adalah berkas utama: {reader_files} berkas dengan {formatted} byte. "
        "Ekstrak ZIP, layani direktorinya melalui peladen HTTP statis, lalu buka `index.html`. "
        "Paket source-backend memuat otoritas, authoring source, backend modular, seluruh "
        "22 aset Lesson 10, skrip reproduksi, lisensi, dan bukti build/QA/visual.\n\n"
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
        "schema": "o006.stat415.through-lesson10-release-root.v1",
        "status": "ready",
        "coverage": EXPECTED_COVERAGE,
        "self_exclusion": {"filename": ROOT_RECEIPT, "reason": "non-self-referential cryptographic root"},
        "inventory_semantics": {
            "release_manifest": {"filename": RELEASE_MANIFEST, "covers": substantive, "excludes": [RELEASE_MANIFEST, CHECKSUMS, ROOT_RECEIPT]},
            "sha256sums": {"filename": CHECKSUMS, "covers": substantive + [RELEASE_MANIFEST], "excludes": [CHECKSUMS, ROOT_RECEIPT]},
            "root_receipt": {"filename": ROOT_RECEIPT, "covers": covered, "excludes": [ROOT_RECEIPT]},
        },
        "files": [{"filename": filename, "bytes": len(payloads[filename]), "sha256": common.sha256(payloads[filename]), "role": roles[filename]} for filename in covered],
        "file_count": len(covered),
        "total_bytes": sum(len(payloads[name]) for name in covered),
        "upload_order": covered,
    })
    inputs = {"reader_manifest": validated["manifest"], "build_receipt": validated["build"], "qa_receipt": validated["qa"], "visual_qa_receipt": validated["visual"], "license": validated["license"]}
    receipt = common.canonical_json({
        "schema": "o006.stat415.through-lesson10-package.v1",
        "status": "ready",
        "coverage": {**EXPECTED_COVERAGE, "statement": "landing/index plus complete Lesson00-Lesson10; 12 of 14 documents"},
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "rights": {"penn_state": "CC BY-NC 4.0 except where otherwise noted", "mathjax_3_1_2": "Apache-2.0", "original_repository_layer": "CC BY-SA 4.0", "aggregate_uniform_relicense": False},
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
    print(json.dumps({"mode": state, "files": info["file_count"], "bytes": info["total_bytes"], "reader_files": info["reader_zip"]["reader_files"], "source_entries": info["source_zip"]["entries"], "receipt_sha256": common.sha256(receipt)}, sort_keys=True))


if __name__ == "__main__":
    main()
