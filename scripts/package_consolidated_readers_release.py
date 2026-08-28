#!/usr/bin/env python3
"""Build the deterministic, reader-first consolidated STAT 415 release union.

This packager is intentionally offline and browser-free.  It reads only an
explicit allowlist of final artifacts, QA receipts, the exact nine files in the
previous Zenodo version, and one historical Ace report.  It never invokes a
subprocess, performs network access, discovers files recursively, reads
credentials, publishes, or changes lane-control files.

The current PDF and EPUB are admitted only when their final static receipts,
deterministic replay identities, and artifact hashes all agree.  The historical
Ace report is retained solely as clearly labelled historical evidence; it is
not represented as validation of the current EPUB bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
BUILD = ROOT / "build"

VERSION = "2026.08.28.complete-stat415-readers"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
CONCEPT_DOI = "10.5281/zenodo.22077422"
PRIOR_RECORD_ID = "22105616"
PRIOR_RECORD_DOI = "10.5281/zenodo.22105616"

PDF_SOURCE = "output/pdf/stat415-pengantar-statistika-matematis-id.pdf"
EPUB_SOURCE = "output/epub/stat415-pengantar-statistika-matematis-id.epub"
PDF_FILE = "00_00_stat415-pengantar-statistika-matematis-id.pdf"
EPUB_FILE = "00_01_stat415-pengantar-statistika-matematis-id.epub"
NOTES_FILE = "20_COMPLETE_CONSOLIDATED_READERS_RELEASE_NOTES.md"
LICENSE_FILE = "30_COMPLETE_CONSOLIDATED_READERS_LICENSE.md"
QA_ZIP_FILE = "40_COMPLETE_CONSOLIDATED_READERS_QA_EVIDENCE.zip"
MANIFEST_FILE = "50_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_MANIFEST.csv"
CHECKSUMS_FILE = "SHA256SUMS_COMPLETE_CONSOLIDATED_READERS.txt"
ROOT_RECEIPT_FILE = "60_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_ROOT_RECEIPT.json"
PACKAGE_RECEIPT = BUILD / "CONSOLIDATED_READERS_PACKAGE_RECEIPT.json"

PDF_QA = "build/CONSOLIDATED_PDF_QA_RECEIPT.json"
PDF_VISUAL_QA = "build/CONSOLIDATED_PDF_VISUAL_QA_RECEIPT.json"
EPUB_BUILD = "build/CONSOLIDATED_EPUB_BUILD_RECEIPT.json"
EPUB_QA = "build/CONSOLIDATED_EPUB_QA_RECEIPT.json"
EPUB_STATIC_REFLOW_QA = "build/CONSOLIDATED_EPUB_STATIC_REFLOW_QA_RECEIPT.json"
EPUB_MATH_RECEIPT = "build/EPUB_MATH_FALLBACK_RENDER_RECEIPT.json"

HISTORICAL_ACE = "tmp/epubqa/ace-official-20260828/report.json"
HISTORICAL_ACE_SHA256 = "c6fa76293f5c179050aa19d8b6288ed5f6ffa218b74fcfc4d0c72f5441304c35"
HISTORICAL_ACE_BYTES = 117_127
HISTORICAL_ACE_AUDITED_EPUB_SHA256 = "acf81b8aa62ef77cd574d45d04490ebe173539ea3f8419c5c5e1ffcea5536729"

COMPLETE_DOCUMENTS = ["index", *[f"Lesson{i:02d}" for i in range(13)]]
COVERAGE = {
    "component": "Penn State STAT 415 external narrative spine",
    "complete_documents": COMPLETE_DOCUMENTS,
    "complete_count": 14,
    "corpus_document_count": 14,
    "statement": "landing/index plus complete Lesson00-Lesson12; 14 of 14 Penn State documents",
    "c140_course_status": "incomplete: the distinct Random donor and original companion remain separate follow-on components",
}

# Exact anonymous public inventory of Zenodo record 22105616.  These bytes are
# immutable inputs to the new union: the packager verifies but never rewrites
# them.
PRIOR_RELEASE: tuple[dict[str, Any], ...] = (
    {
        "filename": "00_stat415-id-through-lesson12-offline-reader.zip",
        "bytes": 17_648_138,
        "sha256": "e6c5829452e9d023ae7c54e802673a0e1fb0ddf220716d8f5156f1169ecb01e1",
        "role": "preserved-prior-html-offline-reader",
        "media_type": "application/zip",
    },
    {
        "filename": "10_stat415-id-through-lesson12-source-backend.zip",
        "bytes": 37_621_137,
        "sha256": "510bd0255f1ddbb925f3abb8594b04eac51fa688f0c0f5b184259033e578ada0",
        "role": "preserved-prior-source-backend",
        "media_type": "application/zip",
    },
    {
        "filename": "20_THROUGH_LESSON12_RELEASE_NOTES.md",
        "bytes": 1_213,
        "sha256": "7db90c69118f75e41fef99d0ddd0704471710ff97b1b58957aa8e86a0b36f339",
        "role": "preserved-prior-release-notes",
        "media_type": "text/markdown",
    },
    {
        "filename": "30_THROUGH_LESSON12_LICENSE.md",
        "bytes": 1_515,
        "sha256": "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d",
        "role": "preserved-prior-component-rights",
        "media_type": "text/markdown",
    },
    {
        "filename": "40_THROUGH_LESSON12_QA_RECEIPT.json",
        "bytes": 12_428,
        "sha256": "d12c9dcb4293de0ec929cc2d2c330e197d936a86e17e27adc20dede10bef15db",
        "role": "preserved-prior-deterministic-qa",
        "media_type": "application/json",
    },
    {
        "filename": "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json",
        "bytes": 21_702,
        "sha256": "02583cecceba1db5f8a9f7561f567ebd98585c441a6e4cae5ba1ef92f8710d6e",
        "role": "preserved-prior-html-visual-qa",
        "media_type": "application/json",
    },
    {
        "filename": "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv",
        "bytes": 854,
        "sha256": "92fb966e8e2d6df14810571bdb171eafa2305e9c0241f7a87f5c3c85545c1528",
        "role": "preserved-prior-manifest",
        "media_type": "text/csv",
    },
    {
        "filename": "SHA256SUMS_THROUGH_LESSON12.txt",
        "bytes": 750,
        "sha256": "ed97539fb0dd796edcc287cae67920acb04e62bb5e65cd0775e8afbfb7d3d663",
        "role": "preserved-prior-checksums",
        "media_type": "text/plain",
    },
    {
        "filename": "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json",
        "bytes": 4_763,
        "sha256": "d9306b66b26a5faf0b90cfc7c1266001cba9a4159cef1394692fb07b6cc7ac49",
        "role": "preserved-prior-release-root",
        "media_type": "application/json",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, separators=(",", ": "))
        + "\n"
    ).encode("utf-8")


def read_exact(relative: str) -> bytes:
    path = ROOT / relative
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"required regular file is missing or symlinked: {relative}")
    return path.read_bytes()


def read_json(relative: str) -> tuple[bytes, dict[str, Any]]:
    payload = read_exact(relative)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid UTF-8 JSON: {relative}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root is not an object: {relative}")
    return payload, value


def identity(payload: bytes) -> dict[str, Any]:
    return {"bytes": len(payload), "sha256": sha256(payload)}


def require_identity(label: str, record: Any, payload: bytes, expected_path: str | None = None) -> None:
    if not isinstance(record, dict):
        raise RuntimeError(f"{label} identity is absent")
    if record.get("bytes") != len(payload) or record.get("sha256") != sha256(payload):
        raise RuntimeError(f"{label} byte/hash identity is stale")
    if expected_path is not None and record.get("path") != expected_path:
        raise RuntimeError(f"{label} path differs: {record.get('path')!r}")


def require_status(label: str, receipt: dict[str, Any], schema: str) -> None:
    if receipt.get("schema") != schema or receipt.get("status") not in {"passed", "pass"}:
        raise RuntimeError(f"{label} is not a passed {schema} receipt")


def validate_prior_union() -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    for expected in PRIOR_RELEASE:
        payload = read_exact(f"release/{expected['filename']}")
        if len(payload) != expected["bytes"] or sha256(payload) != expected["sha256"]:
            raise RuntimeError(f"preserved prior release identity differs: {expected['filename']}")
        verified.append(dict(expected))
    if len(verified) != 9 or sum(item["bytes"] for item in verified) != 55_312_500:
        raise RuntimeError("preserved prior nine-file release union is incomplete")
    return verified


def validate_pdf() -> tuple[bytes, dict[str, bytes], dict[str, Any]]:
    artifact = read_exact(PDF_SOURCE)
    qa_payload, qa = read_json(PDF_QA)
    visual_payload, visual = read_json(PDF_VISUAL_QA)
    require_status("PDF structural QA", qa, "o006.stat415.consolidated-pdf-qa.v1")
    require_status("PDF visual QA", visual, "o006.stat415.consolidated-pdf-visual-qa.v1")
    require_identity("PDF QA artifact", qa.get("artifact"), artifact, PDF_SOURCE)
    require_identity("PDF visual artifact", visual.get("artifact"), artifact, PDF_SOURCE)
    if not artifact.startswith(b"%PDF-") or b"%%EOF" not in artifact[-4096:]:
        raise RuntimeError("PDF signature or EOF marker is absent")
    if qa.get("artifact", {}).get("pages") != 219 or visual.get("artifact", {}).get("pages") != 219:
        raise RuntimeError("PDF receipts do not bind the exact 219-page edition")
    replay = qa.get("deterministic_replay", {})
    if replay.get("matches_artifact") is not True:
        raise RuntimeError("PDF deterministic replay does not pass")
    require_identity("PDF deterministic replay", replay, artifact)
    bound = visual.get("bound_machine_qa", {}).get("structural_qa_receipt")
    require_identity("PDF visual-to-structural QA binding", bound, qa_payload, PDF_QA)
    if visual.get("final_raster", {}).get("page_count") != 219:
        raise RuntimeError("PDF final-raster receipt is incomplete")
    inspection = visual.get("recorded_visual_inspection", {})
    if (
        inspection.get("contact_sheet_result") != "passed"
        or inspection.get("changed_pages_directly_inspected") != [217, 218]
        or not str(inspection.get("final_visual_disposition", "")).startswith("passed:")
    ):
        raise RuntimeError("PDF visual inspection disposition is incomplete")
    return artifact, {PDF_QA: qa_payload, PDF_VISUAL_QA: visual_payload}, {
        "artifact": {"path": PDF_SOURCE, **identity(artifact), "pages": 219},
        "structural_qa": {"path": PDF_QA, **identity(qa_payload)},
        "visual_qa": {"path": PDF_VISUAL_QA, **identity(visual_payload)},
        "deterministic_replay_matches": True,
    }


def validate_epub_package(artifact: bytes, expected_entries: int) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(artifact), "r") as archive:
            infos = archive.infolist()
            if len(infos) != expected_entries or not infos:
                raise RuntimeError("EPUB ZIP entry count differs")
            if infos[0].filename != "mimetype" or infos[0].compress_type != zipfile.ZIP_STORED:
                raise RuntimeError("EPUB mimetype is not first and stored")
            if archive.read("mimetype") != b"application/epub+zip":
                raise RuntimeError("EPUB mimetype payload differs")
            if archive.testzip() is not None:
                raise RuntimeError("EPUB ZIP CRC verification failed")
            if any(info.date_time != (1980, 1, 1, 0, 0, 0) for info in infos):
                raise RuntimeError("EPUB contains a non-canonical ZIP timestamp")
            for info in infos:
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or ".." in name.split("/"):
                    raise RuntimeError(f"unsafe EPUB entry name: {info.filename}")
    except zipfile.BadZipFile as exc:
        raise RuntimeError("EPUB is not a valid ZIP package") from exc


def _receipt_binding(receipt: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in receipt:
            return receipt[name]
    return None


def validate_epub() -> tuple[bytes, dict[str, bytes], dict[str, Any]]:
    artifact = read_exact(EPUB_SOURCE)
    build_payload, build = read_json(EPUB_BUILD)
    qa_payload, qa = read_json(EPUB_QA)
    static_payload, static = read_json(EPUB_STATIC_REFLOW_QA)
    math_payload, math_receipt = read_json(EPUB_MATH_RECEIPT)

    require_status("EPUB build", build, "o006.stat415.consolidated-epub.v1")
    require_status("EPUB QA", qa, "o006.stat415.consolidated-epub-qa.v1")
    require_status(
        "EPUB static-reflow QA",
        static,
        "o006.stat415.consolidated-epub-static-reflow-qa.v1",
    )

    require_identity("EPUB build artifact", {"bytes": build.get("bytes"), "sha256": build.get("sha256"), "path": build.get("output")}, artifact, EPUB_SOURCE)
    require_identity("EPUB QA artifact", qa.get("artifact"), artifact, EPUB_SOURCE)
    require_identity("EPUB static-reflow artifact", static.get("artifact"), artifact, EPUB_SOURCE)
    require_identity("EPUB QA-to-build binding", qa.get("build_receipt"), build_payload, EPUB_BUILD)

    static_build = _receipt_binding(static, ("build_receipt", "bound_build_receipt", "epub_build_receipt"))
    require_identity("EPUB static-to-build binding", static_build, build_payload, EPUB_BUILD)
    static_qa = _receipt_binding(static, ("qa_receipt", "bound_qa_receipt", "epub_qa_receipt"))
    require_identity("EPUB static-to-QA binding", static_qa, qa_payload, EPUB_QA)

    replays = qa.get("deterministic_replays")
    if not isinstance(replays, list) or len(replays) < 2:
        raise RuntimeError("EPUB QA lacks two deterministic replay identities")
    for index, replay in enumerate(replays, 1):
        require_identity(f"EPUB deterministic replay {index}", replay, artifact)

    static_replays = _receipt_binding(static, ("replays", "deterministic_replays"))
    if not isinstance(static_replays, list) or len(static_replays) < 2:
        raise RuntimeError("EPUB static-reflow receipt replay list is incomplete")
    for index, replay in enumerate(static_replays, 1):
        require_identity(f"EPUB static-reflow replay {index}", replay, artifact)

    package = qa.get("package", {})
    if (
        package.get("entries") != 111
        or package.get("fixed_zip_timestamps") != 111
        or package.get("manifest_items") != 107
        or package.get("spine_items") != 4
        or package.get("mimetype_first_and_stored") is not True
        or package.get("zip_crc") != "passed"
    ):
        raise RuntimeError("EPUB package QA differs from the admitted final structure")
    structure = qa.get("structure", {})
    if (
        structure.get("xhtml_documents") != 4
        or structure.get("epub_toc_links") != 19
        or structure.get("landmark_links") != 4
        or structure.get("ncx_navpoints") != 19
        or structure.get("mathml_nodes") != 3159
        or structure.get("svg_math_fallbacks") != 17
        or structure.get("heading_forward_skips_after_rendition_repair") != 0
        or structure.get("images_with_nonempty_alternatives") != structure.get("image_occurrences")
    ):
        raise RuntimeError("EPUB structural QA differs from the admitted final structure")
    if qa.get("privacy", {}).get("sensitive_or_local_markers") != []:
        raise RuntimeError("EPUB QA reports sensitive or local markers")

    static_checks = static.get("checks", {})
    if (
        static_checks.get("css_containment_and_focus_contract") != "passed"
        or static_checks.get("math_reflow_candidate_count") != 125
        or static_checks.get("math_wrapper_count") != 3139
        or static_checks.get("mathml_count") != 3159
        or static_checks.get("fixed_zip_timestamps") != 111
        or static_checks.get("zip_crc") != "passed"
        or static_checks.get("epubcheck_messages") != 0
        or static_checks.get("epubcheck_status") != "Well-formed"
    ):
        raise RuntimeError("EPUB final static reflow/package gate differs")
    if (
        build.get("xhtml_repairs", {}).get("math_reflow_regions_focusable") != 125
        or build.get("xhtml_repairs", {}).get("scrollable_code_regions_focusable") != 1
        or structure.get("math_reflow_focusable_regions") != 125
    ):
        raise RuntimeError("EPUB final math/code reflow focusability gate differs")
    forbidden_for_final = set(static.get("validation_scope", {}).get("not_run_for_final_hash", []))
    if forbidden_for_final != {
        "Ace",
        "Chrome",
        "Chromium",
        "Playwright",
        "Puppeteer",
        "Electron",
        "WebView",
    }:
        raise RuntimeError("EPUB receipt does not preserve the permanent no-browser final-hash scope")
    prior_ace = static.get("prior_ace_tested_candidate", {})
    if (
        prior_ace.get("artifact", {}).get("sha256") != HISTORICAL_ACE_AUDITED_EPUB_SHA256
        or prior_ace.get("artifact", {}).get("bytes") != 12_299_659
        or prior_ace.get("ace_report", {}).get("sha256") != HISTORICAL_ACE_SHA256
        or prior_ace.get("ace_report", {}).get("bytes") != HISTORICAL_ACE_BYTES
        or prior_ace.get("failed_assertions") != 0
        or "only" not in str(prior_ace.get("scope_note", "")).lower()
        or "final hash" not in str(prior_ace.get("scope_note", "")).lower()
    ):
        raise RuntimeError("historical Ace evidence is not explicitly and exactly scoped to the prior EPUB")

    math_binding = build.get("math_fallback_render_receipt")
    require_identity("EPUB build-to-math receipt binding", math_binding, math_payload, EPUB_MATH_RECEIPT)
    validate_epub_package(artifact, 111)

    return artifact, {
        EPUB_BUILD: build_payload,
        EPUB_QA: qa_payload,
        EPUB_STATIC_REFLOW_QA: static_payload,
        EPUB_MATH_RECEIPT: math_payload,
    }, {
        "artifact": {"path": EPUB_SOURCE, **identity(artifact), "entries": 111},
        "build_receipt": {"path": EPUB_BUILD, **identity(build_payload)},
        "qa_receipt": {"path": EPUB_QA, **identity(qa_payload)},
        "static_reflow_qa": {"path": EPUB_STATIC_REFLOW_QA, **identity(static_payload)},
        "math_fallback_receipt": {"path": EPUB_MATH_RECEIPT, **identity(math_payload)},
        "deterministic_replay_count": len(replays),
    }


def release_notes(pdf: bytes, epub: bytes) -> bytes:
    return (
        "# STAT 415 — pembaca lengkap PDF dan EPUB (Bahasa Indonesia)\n\n"
        "Status komponen: **lengkap; 14 dari 14 dokumen Penn State**. Rilis ini "
        "memuat laman utama dan seluruh Pelajaran 00–12 sebagai PDF 219 halaman "
        "serta EPUB yang dapat direflow. Kelengkapan ini berlaku untuk spine eksternal "
        "Penn State, bukan untuk seluruh kursus C140; donor Random dan pendamping asli "
        "tetap merupakan komponen terpisah.\n\n"
        f"Berkas utama adalah `{PDF_FILE}` ({len(pdf):,} byte), diikuti `{EPUB_FILE}` "
        f"({len(epub):,} byte). Paket bukti QA ringkas mengikat artefak final pada build "
        "dan pemeriksaan statisnya. Laporan Ace di dalam paket itu diberi label historis "
        "karena memeriksa hash EPUB terdahulu, bukan byte EPUB final.\n\n"
        "Konten Penn State dan adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan lain; "
        "MathJax 3.1.2 tetap Apache-2.0; lapisan editorial dan build asli tetap CC BY-SA "
        "4.0. Koleksi ini tidak direlisensi secara seragam dan tidak menyiratkan pengesahan.\n\n"
        f"Provenans terjemahan dan rekonstruksi: {PROVENANCE}. Kredit sumber dan "
        "kontributor manusia dipertahankan.\n"
    ).encode("utf-8")


def deterministic_zip(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(entries, key=str.casefold):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return output.getvalue()


def qa_evidence_zip(pdf_receipts: dict[str, bytes], epub_receipts: dict[str, bytes]) -> tuple[bytes, dict[str, Any]]:
    historical_ace = read_exact(HISTORICAL_ACE)
    if len(historical_ace) != HISTORICAL_ACE_BYTES or sha256(historical_ace) != HISTORICAL_ACE_SHA256:
        raise RuntimeError("historical Ace report identity differs")
    lowered = historical_ace.lower()
    for marker in (b"c:\\users", b"file://", b"token", b"password", b"secret"):
        if marker in lowered:
            raise RuntimeError(f"historical Ace report contains a forbidden local/sensitive marker: {marker!r}")

    entries: dict[str, bytes] = {}
    classifications: dict[str, str] = {}
    for source, payload in {**pdf_receipts, **epub_receipts}.items():
        name = f"final-static/{Path(source).name}"
        entries[name] = payload
        classifications[name] = "final-static-receipt"
    ace_name = "historical-accessibility/Ace-1.4.6-report.json"
    entries[ace_name] = historical_ace
    classifications[ace_name] = "historical-browser-derived-accessibility-report-not-final-artifact-validation"
    notice_name = "HISTORICAL_EVIDENCE_NOTICE.md"
    entries[notice_name] = (
        "# Lingkup bukti historis\n\n"
        "`historical-accessibility/Ace-1.4.6-report.json` adalah laporan historis "
        "yang memeriksa EPUB dengan SHA-256 "
        f"`{HISTORICAL_ACE_AUDITED_EPUB_SHA256}`. Laporan itu **tidak** memvalidasi "
        "byte EPUB final dalam rilis ini dan tidak dijalankan ulang oleh packager. "
        "Keputusan rilis EPUB final bertumpu pada receipt build, QA deterministik, "
        "dan QA reflow statis tanpa peluncuran peramban di direktori `final-static/`.\n"
    ).encode("utf-8")
    classifications[notice_name] = "scope-notice"

    inventory_name = "QA_EVIDENCE_INVENTORY.json"
    inventory = canonical_json({
        "schema": "o006.stat415.consolidated-readers-qa-evidence.v1",
        "status": "passed",
        "current_artifact_validation": "final-static receipts only",
        "historical_ace": {
            "entry": ace_name,
            "report_sha256": HISTORICAL_ACE_SHA256,
            "audited_epub_sha256": HISTORICAL_ACE_AUDITED_EPUB_SHA256,
            "current_artifact_gate": False,
        },
        "entries": [
            {"entry": name, **identity(entries[name]), "classification": classifications[name]}
            for name in sorted(entries, key=str.casefold)
        ],
        "self_exclusion": {
            "entry": inventory_name,
            "reason": "non-self-referential cryptographic evidence inventory",
        },
    })
    entries[inventory_name] = inventory
    classifications[inventory_name] = "evidence-inventory"
    payload = deterministic_zip(entries)
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        if archive.testzip() is not None or len(archive.infolist()) != len(entries):
            raise RuntimeError("deterministic QA evidence ZIP verification failed")
    return payload, {
        "entries": len(entries),
        "uncompressed_bytes": sum(len(value) for value in entries.values()),
        "archive_method": "ZIP_DEFLATED level 9; fixed 1980-01-01 timestamps; canonical entry order",
        "inventory": {"entry": inventory_name, **identity(inventory)},
        "historical_ace": {
            "entry": ace_name,
            **identity(historical_ace),
            "audited_epub_sha256": HISTORICAL_ACE_AUDITED_EPUB_SHA256,
            "current_artifact_gate": False,
        },
    }


def manifest_payload(files: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    fields = (
        "upload_order",
        "filename",
        "bytes",
        "sha256",
        "role",
        "lineage",
        "media_type",
        "primary_reader",
        "source_path",
    )
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for item in files:
        writer.writerow({field: item[field] for field in fields})
    return output.getvalue().encode("utf-8")


def record(
    order: int,
    filename: str,
    payload: bytes,
    role: str,
    lineage: str,
    media_type: str,
    primary_reader: bool = False,
) -> dict[str, Any]:
    return {
        "upload_order": order,
        "filename": filename,
        **identity(payload),
        "role": role,
        "lineage": lineage,
        "media_type": media_type,
        "primary_reader": primary_reader,
        "source_path": f"release/{filename}",
    }


def compute() -> tuple[dict[str, bytes], bytes]:
    prior = validate_prior_union()
    pdf, pdf_receipts, pdf_gate = validate_pdf()
    epub, epub_receipts, epub_gate = validate_epub()
    license_payload = read_exact("LICENSE.md")
    license_text = license_payload.decode("utf-8")
    for statement in ("CC BY-NC 4.0", "Apache License 2.0", "CC BY-SA 4.0"):
        if statement not in license_text:
            raise RuntimeError(f"component rights statement missing from LICENSE.md: {statement}")
    notes = release_notes(pdf, epub)
    qa_zip, qa_zip_info = qa_evidence_zip(pdf_receipts, epub_receipts)

    new_payloads: dict[str, bytes] = {
        PDF_FILE: pdf,
        EPUB_FILE: epub,
        NOTES_FILE: notes,
        LICENSE_FILE: license_payload,
        QA_ZIP_FILE: qa_zip,
    }
    payloads: dict[str, bytes] = dict(new_payloads)
    for item in prior:
        payloads[item["filename"]] = read_exact(f"release/{item['filename']}")

    substantive: list[dict[str, Any]] = [
        record(1, PDF_FILE, pdf, "primary-complete-pdf-reader", "current-consolidated-readers", "application/pdf", True),
        record(2, EPUB_FILE, epub, "secondary-complete-reflowable-reader", "current-consolidated-readers", "application/epub+zip"),
        record(3, NOTES_FILE, notes, "current-scope-status-rights-provenance", "current-consolidated-readers", "text/markdown"),
        record(4, LICENSE_FILE, license_payload, "current-component-rights", "current-consolidated-readers", "text/markdown"),
        record(5, QA_ZIP_FILE, qa_zip, "compact-current-static-qa-and-labelled-historical-evidence", "current-consolidated-readers", "application/zip"),
    ]
    order = 6
    for item in prior:
        substantive.append(record(
            order,
            item["filename"],
            payloads[item["filename"]],
            item["role"],
            f"preserved-zenodo-record-{PRIOR_RECORD_ID}",
            item["media_type"],
        ))
        order += 1

    manifest = manifest_payload(substantive)
    payloads[MANIFEST_FILE] = manifest
    manifest_record = record(order, MANIFEST_FILE, manifest, "full-union-substantive-manifest", "current-consolidated-readers", "text/csv")
    order += 1
    checksums_covered = substantive + [manifest_record]
    checksums = "".join(f"{item['sha256']}  {item['filename']}\n" for item in checksums_covered).encode("utf-8")
    payloads[CHECKSUMS_FILE] = checksums
    checksums_record = record(order, CHECKSUMS_FILE, checksums, "full-union-sha256-checksums", "current-consolidated-readers", "text/plain")
    order += 1
    root_covered = checksums_covered + [checksums_record]
    root_receipt = canonical_json({
        "schema": "o006.stat415.complete-consolidated-readers-full-union-root.v1",
        "status": "ready",
        "version": VERSION,
        "coverage": COVERAGE,
        "concept_doi": CONCEPT_DOI,
        "preserved_prior_release": {
            "record_id": PRIOR_RECORD_ID,
            "doi": PRIOR_RECORD_DOI,
            "file_count": len(prior),
            "bytes": sum(item["bytes"] for item in prior),
            "identity_verified": True,
        },
        "inventory_semantics": {
            "manifest": {"filename": MANIFEST_FILE, "covers": [item["filename"] for item in substantive]},
            "checksums": {"filename": CHECKSUMS_FILE, "covers": [item["filename"] for item in checksums_covered]},
            "root_receipt": {
                "filename": ROOT_RECEIPT_FILE,
                "covers": [item["filename"] for item in root_covered],
                "self_excluded": True,
            },
        },
        "files": root_covered,
        "file_count": len(root_covered),
        "total_bytes": sum(item["bytes"] for item in root_covered),
        "self_exclusion": {
            "filename": ROOT_RECEIPT_FILE,
            "reason": "non-self-referential cryptographic release root",
        },
    })
    payloads[ROOT_RECEIPT_FILE] = root_receipt
    root_record = record(order, ROOT_RECEIPT_FILE, root_receipt, "full-union-release-root-receipt", "current-consolidated-readers", "application/json")
    publication_files = substantive + [manifest_record, checksums_record, root_record]

    packager_payload = read_exact("scripts/package_consolidated_readers_release.py")
    package_receipt = canonical_json({
        "schema": "o006.stat415.consolidated-readers-package.v1",
        "status": "ready",
        "version": VERSION,
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "coverage": COVERAGE,
        "lineage": {
            "concept_doi": CONCEPT_DOI,
            "prior_record_id": PRIOR_RECORD_ID,
            "prior_record_doi": PRIOR_RECORD_DOI,
            "create_competing_concept": False,
        },
        "rights": {
            "penn_state_content_and_adaptation": "CC BY-NC 4.0 except where otherwise noted",
            "mathjax_3_1_2": "Apache-2.0",
            "original_repository_layer": "CC BY-SA 4.0",
            "aggregate_uniform_relicense": False,
        },
        "gates": {
            "pdf": pdf_gate,
            "epub": epub_gate,
            "prior_release": {
                "file_count": len(prior),
                "bytes": sum(item["bytes"] for item in prior),
                "identity_verified": True,
            },
            "qa_evidence_zip": {"filename": QA_ZIP_FILE, **identity(qa_zip), **qa_zip_info},
        },
        "packager": {
            "path": "scripts/package_consolidated_readers_release.py",
            **identity(packager_payload),
            "network_access": False,
            "browser_processes": False,
            "credential_access": False,
            "publication_side_effects": False,
        },
        "publication_inventory": {
            "primary_file": PDF_FILE,
            "secondary_reader": EPUB_FILE,
            "reader_first": True,
            "file_count": len(publication_files),
            "total_bytes": sum(item["bytes"] for item in publication_files),
            "fields": [
                "upload_order",
                "filename",
                "bytes",
                "sha256",
                "role",
                "lineage",
                "media_type",
                "primary_reader",
                "source_path",
            ],
            "files": publication_files,
            "upload_order": [item["filename"] for item in publication_files],
        },
        "outputs": {
            "manifest": {"filename": MANIFEST_FILE, **identity(manifest)},
            "checksums": {"filename": CHECKSUMS_FILE, **identity(checksums)},
            "root_receipt": {"filename": ROOT_RECEIPT_FILE, **identity(root_receipt)},
            "package_receipt": {
                "path": "build/CONSOLIDATED_READERS_PACKAGE_RECEIPT.json",
                "self_hash_excluded": True,
            },
        },
    })
    return payloads, package_receipt


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.packager-tmp")
    if temporary.exists():
        if temporary.is_dir() or temporary.is_symlink():
            raise RuntimeError(f"unsafe temporary output collision: {temporary}")
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists() and temporary.is_file() and not temporary.is_symlink():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    payloads, receipt = compute()
    outputs = {RELEASE / name: payload for name, payload in payloads.items()}
    outputs[PACKAGE_RECEIPT] = receipt
    if args.write:
        for path, payload in outputs.items():
            if path.exists() and (path.is_dir() or path.is_symlink()):
                raise RuntimeError(f"release output collides with a directory or symlink: {path}")
            atomic_write(path, payload)
        state = "written"
    else:
        for path, expected in outputs.items():
            if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"release-package output differs: {path.relative_to(ROOT).as_posix()}")
        state = "verified"

    parsed = json.loads(receipt.decode("utf-8"))
    print(json.dumps({
        "mode": state,
        "schema": parsed["schema"],
        "files": parsed["publication_inventory"]["file_count"],
        "bytes": parsed["publication_inventory"]["total_bytes"],
        "primary_file": parsed["publication_inventory"]["primary_file"],
        "primary_sha256": parsed["publication_inventory"]["files"][0]["sha256"],
        "secondary_reader": parsed["publication_inventory"]["secondary_reader"],
        "secondary_sha256": parsed["publication_inventory"]["files"][1]["sha256"],
        "package_receipt_sha256": sha256(receipt),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
