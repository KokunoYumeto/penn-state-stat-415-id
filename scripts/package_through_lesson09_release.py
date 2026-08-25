#!/usr/bin/env python3
"""Create deterministic reader-first release packages through Lesson 09."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

import package_through_lesson01_release as common
import package_through_lesson05_release as prior


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
READER = ROOT / "build" / "html-id"
READER_ZIP = "00_stat415-id-through-lesson09-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson09-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON09_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_THROUGH_LESSON09_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON09_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON09_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_THROUGH_LESSON09_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS_THROUGH_LESSON09.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON09_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON09_PACKAGE_RECEIPT.json"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = ["index", *[f"Lesson{i:02d}" for i in range(10)]]
EXPECTED_COVERAGE = {
    "complete_count": 11,
    "complete_documents": COMPLETE_DOCUMENTS,
    "corpus_document_count": 14,
    "next_document": "Lesson10",
}
VISUAL_COVERAGE = "landing/index plus complete Lesson00 through Lesson09"

NEW_ASSETS = (
    "authority/assets/stat415/lesson06/assets/ci_1.png",
    "authority/assets/stat415/lesson07/Lesson07_files/figure-html/unnamed-chunk-1-1.png",
    "authority/assets/stat415/lesson07/Lesson07_files/figure-html/unnamed-chunk-6-1.png",
    "authority/assets/stat415/lesson08/Lesson08_files/figure-html/unnamed-chunk-1-1.png",
    "authority/assets/stat415/lesson08/Lesson08_files/figure-html/unnamed-chunk-8-1.png",
    "authority/assets/stat415/lesson08/Lesson08_files/figure-html/unnamed-chunk-14-1.png",
    "authority/assets/stat415/lesson08/Lesson08_files/figure-html/unnamed-chunk-18-1.png",
    "authority/assets/stat415/lesson09/assets/tetra_die.png",
    "authority/assets/stat415/lesson09/Lesson09_files/figure-html/unnamed-chunk-1-1.png",
    "authority/assets/stat415/lesson09/Lesson09_files/figure-html/unnamed-chunk-2-1.png",
    "authority/assets/stat415/lesson09/assets/STAT-415-SEC-2-03.svg",
    "authority/assets/stat415/lesson09/assets/ht5.png",
    "authority/assets/stat415/lesson09/assets/ht6.png",
    "authority/assets/stat415/lesson09/assets/ht7.png",
    "authority/assets/stat415/lesson09/assets/ht8.png",
    "authority/assets/stat415/lesson09/assets/h10.png",
    "authority/assets/stat415/lesson09/assets/h11.png",
)

ADDITIONAL_SOURCE_PACKAGE_FILES = (
    "scripts/normalize_lesson06.py",
    "scripts/lesson06_corrections.py",
    "scripts/merge_lesson06_translations.py",
    "scripts/build_through_lesson06.py",
    "scripts/qa_through_lesson06.py",
    "scripts/normalize_lesson07.py",
    "scripts/lesson07_corrections.py",
    "scripts/merge_lesson07_translations.py",
    "scripts/normalize_lesson08.py",
    "scripts/lesson08_corrections.py",
    "scripts/merge_lesson08_translations.py",
    "scripts/normalize_lesson09.py",
    "scripts/lesson09_corrections.py",
    "scripts/merge_lesson09_translations.py",
    "scripts/build_through_lesson09.py",
    "scripts/qa_through_lesson09.py",
    "scripts/package_through_lesson09_release.py",
    "scripts/publish_zenodo_through_lesson09.py",
    "scripts/publish_zenodo_through_lesson05.py",
    "scripts/publish_zenodo_through_lesson03.py",
    "scripts/publish_zenodo_through_lesson01.py",
    "scripts/verify_github_checkpoint_lesson09.py",
    "scripts/verify_github_checkpoint_lesson06.py",
    "00_control/CURRENT_STATE.md",
    "00_control/CURRENT_CURSOR.md",
    "00_control/ZENODO_LINEAGE.json",
    "authority/upstream/stat415/Lesson06.html",
    "authority/upstream/stat415/Lesson07.html",
    "authority/upstream/stat415/Lesson08.html",
    "authority/upstream/stat415/Lesson09.html",
    "authority/LESSON06_ASSET_MANIFEST.csv",
    "authority/LESSON07_ASSET_MANIFEST.csv",
    "authority/LESSON08_ASSET_MANIFEST.csv",
    "authority/LESSON09_ASSET_MANIFEST.csv",
    *NEW_ASSETS,
    *tuple(f"source/normalized/en-US/Lesson{i:02d}.html" for i in range(6, 10)),
    *tuple(f"source/id-ID/Lesson{i:02d}.html" for i in range(6, 10)),
    *tuple(f"source/id-ID/lesson{i:02d}_translation.csv" for i in range(6, 10)),
    *tuple(f"backend/lesson{i:02d}_source_catalogue.jsonl" for i in range(6, 10)),
    *tuple(f"backend/lesson{i:02d}_translation_bindings.jsonl" for i in range(6, 10)),
    "backend/through_lesson06_documents.jsonl",
    "backend/through_lesson06_corrections.jsonl",
    "backend/through_lesson09_documents.jsonl",
    "backend/through_lesson09_corrections.jsonl",
    *tuple(f"working/lesson{i:02d}_segments.csv" for i in range(6, 10)),
    *tuple(f"working/lesson{i:02d}_source_findings.md" for i in range(6, 10)),
    *tuple(f"working/lesson{i:02d}_math_audit.md" for i in range(6, 10)),
    *tuple(f"working/lesson{i:02d}_terminology_qa.md" for i in range(6, 10)),
    *tuple(f"working/lesson{i:02d}_asset_closure.json" for i in range(6, 10)),
    *tuple(
        f"working/lesson{i:02d}_translation_part_{part}.json"
        for i in range(6, 10) for part in ("a", "b", "c")
    ),
    *tuple(
        f"working/lesson{i:02d}_translation_part_{part}_notes.md"
        for i in range(6, 10) for part in ("a", "b", "c")
    ),
    *tuple(f"build/LESSON{i:02d}_NORMALIZATION_RECEIPT.json" for i in range(6, 10)),
    *tuple(f"build/LESSON{i:02d}_TRANSLATION_RECEIPT.json" for i in range(6, 10)),
    "build/THROUGH_LESSON06_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON06_MANIFEST.csv",
    "build/THROUGH_LESSON06_QA_RECEIPT.json",
    "build/THROUGH_LESSON06_VISUAL_QA_RECEIPT.json",
    "build/THROUGH_LESSON09_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON09_MANIFEST.csv",
    "build/THROUGH_LESSON09_QA_RECEIPT.json",
    "build/THROUGH_LESSON09_VISUAL_QA_RECEIPT.json",
)
SOURCE_PACKAGE_FILES = prior.SOURCE_PACKAGE_FILES + ADDITIONAL_SOURCE_PACKAGE_FILES


def snapshot_source_files() -> dict[PurePosixPath, bytes]:
    relatives = [common.safe_relative(value) for value in SOURCE_PACKAGE_FILES]
    folded = [relative.as_posix().casefold() for relative in relatives]
    if len(set(folded)) != len(folded):
        duplicates = sorted({x for x in folded if folded.count(x) > 1})
        raise RuntimeError(f"case-insensitive duplicate in source allowlist: {duplicates}")
    snapshot: dict[PurePosixPath, bytes] = {}
    for relative in relatives:
        common.reject_sensitive_source_name(relative)
        payload = common.read_confined_regular_file(ROOT, relative, relative.as_posix())
        common.reject_machine_local_text(relative, payload)
        snapshot[relative] = payload
    return snapshot


def validate_receipts(source: dict[PurePosixPath, bytes]) -> dict[str, bytes]:
    def admitted(relative: str) -> bytes:
        try:
            return source[PurePosixPath(relative)]
        except KeyError as exc:
            raise RuntimeError(f"validated input absent from allowlist: {relative}") from exc

    build_payload = admitted("build/THROUGH_LESSON09_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON09_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON09_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON09_MANIFEST.csv")
    build = common.decode_json_object(build_payload, "Lesson09 build receipt")
    qa = common.decode_json_object(qa_payload, "Lesson09 QA receipt")
    visual = common.decode_json_object(visual_payload, "Lesson09 visual receipt")
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    manifest_bytes = sum(int(row["bytes"]) for row in rows)
    manifest_sha = common.sha256(manifest_payload)
    if len(rows) != 71:
        raise RuntimeError("reader manifest is not the exact 71-file boundary")
    if (
        build.get("schema") != "o006.stat415.through-lesson09-build.v1"
        or build.get("status") != "built"
        or build.get("coverage") != EXPECTED_COVERAGE
        or build.get("translation_provenance") != PROVENANCE
        or build.get("translation_segments") != 3_458
        or build.get("structural_units_normalized") != 4_775
        or build.get("structural_units_target") != 4_763
        or build.get("math_nodes", {}).get("total") != 2_171
        or build.get("corrections", {}).get("count") != 170
        or build.get("reader", {}).get("files") != 71
        or build.get("reader", {}).get("bytes") != manifest_bytes
        or build.get("reader", {}).get("manifest_sha256") != manifest_sha
    ):
        raise RuntimeError("build receipt is not the exact 11-of-14 boundary")
    if (
        qa.get("schema") != "o006.stat415.through-lesson09-qa.v1"
        or qa.get("status") != "passed"
        or qa.get("coverage") != {
            "complete_documents": 11,
            "corpus_documents": 14,
            "next_document": "Lesson10",
        }
        or qa.get("reader_accessibility_reflow", {}).get("files") != 71
        or qa.get("reader_accessibility_reflow", {}).get("math_nodes") != 2_171
        or qa.get("structure_math_corrections", {}).get("corrections") != 170
    ):
        raise RuntimeError("deterministic QA is not passed for 11 of 14")
    if (
        visual.get("schema") != "o006.stat415.through-lesson09-visual-qa.v1"
        or visual.get("status") != "pass"
        or visual.get("coverage") != VISUAL_COVERAGE
        or visual.get("provenance") != PROVENANCE
        or visual.get("evidence", {}).get("manifest", {}).get("sha256") != manifest_sha
        or visual.get("evidence", {}).get("build_receipt", {}).get("sha256")
        != common.sha256(build_payload)
        or visual.get("evidence", {}).get("qa_receipt", {}).get("sha256")
        != common.sha256(qa_payload)
    ):
        raise RuntimeError("visual QA is not bound to the 11-of-14 reader")
    for viewport in ("desktop", "mobile"):
        view = visual.get(viewport, {})
        routes = view.get("routes", {})
        if view.get("console_errors_or_warnings") != 0 or set(routes) != {
            *EXPECTED_COVERAGE["complete_documents"], "licenses"
        }:
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
    readme = admitted("README.md").decode("utf-8")
    readme_requirements = (
        "11 dari 14",
        "3.458 segmen",
        "4.775 unit struktural sumber",
        "4.763 unit turunan",
        "2.171 permukaan matematika",
        "170 koreksi",
        "71 berkas / 8.551.979 byte",
        "python -B scripts/build_through_lesson09.py --check-only",
        "python -B scripts/qa_through_lesson09.py --check-only",
        PROVENANCE,
    )
    missing_readme = [value for value in readme_requirements if value not in readme]
    if missing_readme:
        raise RuntimeError(f"README is not the exact 11-of-14 boundary: {missing_readme}")

    translation_rows = list(csv.DictReader(io.StringIO(
        admitted("00_control/TRANSLATION_LEDGER.csv").decode("utf-8")
    )))
    if len(translation_rows) != 11:
        raise RuntimeError("translation ledger is not the exact eleven-document boundary")
    target_documents = {item["path"]: item for item in build["target_documents"]}
    expected_document_ids = [f"O006-PSU-{index:03d}" for index in range(11)]
    if [row.get("document_id") for row in translation_rows] != expected_document_ids:
        raise RuntimeError("translation ledger document IDs are not the ordered 11-document boundary")
    for row in translation_rows:
        target = target_documents.get(row.get("target_path", ""))
        if (
            target is None
            or int(row.get("target_bytes", -1)) != target["bytes"]
            or row.get("target_sha256") != target["sha256"]
            or row.get("status") != "complete"
            or row.get("qa_receipt") != "build/THROUGH_LESSON09_QA_RECEIPT.json"
        ):
            raise RuntimeError(f"translation ledger target binding differs: {row.get('document_id')}")

    adverse_rows = [
        json.loads(line)
        for line in admitted("00_control/ADVERSE_LEDGER.jsonl").decode("utf-8").splitlines()
        if line.strip()
    ]
    expected_correction_ids = [f"O006-PSU-ADV-{index:04d}" for index in range(1, 171)]
    if [row.get("correction_id") for row in adverse_rows] != expected_correction_ids:
        raise RuntimeError("adverse ledger is not the exact ordered 170-correction boundary")
    return {
        "build": build_payload,
        "qa": qa_payload,
        "visual": visual_payload,
        "manifest": manifest_payload,
        "license": license_payload,
    }


def reader_package(manifest_payload: bytes) -> tuple[bytes, dict[str, Any]]:
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != 71:
        raise RuntimeError("reader manifest does not contain 71 files")
    actual: set[PurePosixPath] = set()
    for path in READER.rglob("*"):
        relative = PurePosixPath(path.relative_to(READER).as_posix())
        if path.is_symlink():
            raise RuntimeError(f"symlinked reader input forbidden: {relative}")
        if path.is_file():
            actual.add(relative)
    files: dict[PurePosixPath, bytes] = {}
    manifested: set[PurePosixPath] = set()
    reader_bytes = 0
    root = PurePosixPath("stat415-id-through-lesson09")
    for row in rows:
        relative = common.safe_relative(row["relative_path"])
        data = common.read_confined_regular_file(READER, relative, relative.as_posix())
        if len(data) != int(row["bytes"]) or common.sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {relative}")
        manifested.add(relative)
        reader_bytes += len(data)
        files[root / relative] = data
    if actual != manifested:
        raise RuntimeError(
            f"reader inventory differs; missing={sorted(manifested-actual)}; extra={sorted(actual-manifested)}"
        )
    files[root / "THROUGH_LESSON09_MANIFEST.csv"] = manifest_payload
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
    allowlist_manifest = common.canonical_json([
        {"path": relative.as_posix(), "bytes": len(data), "sha256": common.sha256(data)}
        for relative, data in sorted(source.items(), key=lambda item: item[0].as_posix().casefold())
    ])
    return payload, {
        "entries": len(files),
        "uncompressed_bytes": sum(len(value) for value in files.values()),
        "allowlist_manifest_sha256": common.sha256(allowlist_manifest),
        "archive_method": "ZIP_STORED",
    }


def notes_payload(reader_files: int, reader_bytes: int) -> bytes:
    formatted = f"{reader_bytes:,}".replace(",", ".")
    return (
        "# STAT 415 — edisi Bahasa Indonesia: hingga Pelajaran 09\n\n"
        "Status: **sebagian; 11 dari 14 dokumen lengkap**. Paket ini memuat laman utama "
        "serta seluruh Pelajaran 00–09 dalam Bahasa Indonesia. Pelajaran 10–12 tetap "
        "menaut ke sumber resmi berbahasa Inggris.\n\n"
        f"Pembaca luring adalah berkas utama: {reader_files} berkas dengan {formatted} byte. "
        "Ekstrak ZIP, layani direktorinya melalui peladen HTTP statis, lalu buka `index.html`. "
        "Paket source-backend memuat otoritas beku, authoring source, 3.458 segmen, 4.775 "
        "unit sumber, 4.763 unit target, 2.171 permukaan matematika, 170 koreksi turunan, "
        "backend modular, skrip reproduksi, lisensi, dan bukti QA.\n\n"
        "Enam belas aset baru Pelajaran 07–09 dipertahankan byte demi byte; teks alternatif, "
        "semantik tabel, dan reflow pembaca diperbaiki pada turunan. Dua plot Lesson 09 "
        "diungkapkan sebagai keluaran beku karena kode dan input pembangkitnya tidak tersedia.\n\n"
        "Konten Penn State dan adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan lain; "
        "MathJax 3.1.2 tetap Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. "
        "Koleksi tidak direlisensi secara seragam dan tidak ada pengesahan yang tersirat.\n\n"
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
    payloads[CHECKSUMS] = "".join(
        f"{common.sha256(data)}  {filename}\n" for filename, data in payloads.items()
    ).encode("utf-8")
    roles[CHECKSUMS] = "sha256-for-substantive-assets-and-manifest"
    covered_by_root = list(payloads)
    payloads[ROOT_RECEIPT] = common.canonical_json({
        "schema": "o006.stat415.through-lesson09-release-root.v1",
        "status": "ready",
        "coverage": EXPECTED_COVERAGE,
        "self_exclusion": {"filename": ROOT_RECEIPT, "reason": "non-self-referential cryptographic root"},
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
            {"filename": filename, "bytes": len(payloads[filename]), "sha256": common.sha256(payloads[filename]), "role": roles[filename]}
            for filename in covered_by_root
        ],
        "file_count": len(covered_by_root),
        "total_bytes": sum(len(payloads[name]) for name in covered_by_root),
        "upload_order": covered_by_root,
    })
    inputs = {
        "reader_manifest": validated["manifest"],
        "build_receipt": validated["build"],
        "qa_receipt": validated["qa"],
        "visual_qa_receipt": validated["visual"],
        "license": validated["license"],
    }
    receipt = common.canonical_json({
        "schema": "o006.stat415.through-lesson09-package.v1",
        "status": "ready",
        "coverage": {**EXPECTED_COVERAGE, "statement": "landing/index plus complete Lesson00-Lesson09; 11 of 14 documents"},
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
            common.atomic_write(ROOT / relative, data)
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
