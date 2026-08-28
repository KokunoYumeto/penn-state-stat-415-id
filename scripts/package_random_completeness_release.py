#!/usr/bin/env python3
"""Build the deterministic cumulative STAT 415 + Random-donor release package.

This packager is deliberately offline, credential-free, and browser-free.  It
hard-pins the completed 17-file Penn State reader package, verifies and keeps
those files byte-for-byte and in their original upload order, then appends one
complete Random completeness donor component.  It does not invoke subprocesses,
perform network access, discover the repository recursively, publish, or alter
lane-control files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
BUILD = ROOT / "build"
COMPONENT = ROOT / "components" / "random-completeness"

VERSION = "2026.08.28.c140-random-completeness"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
CONCEPT_DOI = "10.5281/zenodo.22077422"
BASE_RECORD_ID = "22142292"
BASE_RECORD_DOI = "10.5281/zenodo.22142292"

BASE_RECEIPT_PATH = "build/CONSOLIDATED_READERS_PACKAGE_RECEIPT.json"
BASE_RECEIPT_BYTES = 14_830
BASE_RECEIPT_SHA256 = "934f9484dd7fd25a2436c80914c68d9627ba4009da07900a975e168d91d01694"
BASE_RECEIPT_SCHEMA = "o006.stat415.consolidated-readers-package.v1"
BASE_RECEIPT_VERSION = "2026.08.28.complete-stat415-readers"
BASE_FILE_COUNT = 17
BASE_TOTAL_BYTES = 87_848_426
PRIMARY_FILE = "00_00_stat415-pengantar-statistika-matematis-id.pdf"
SECONDARY_READER = "00_01_stat415-pengantar-statistika-matematis-id.epub"

READER_FILE = "01_RANDOM_COMPLETENESS_DONOR_OFFLINE_READER.zip"
SOURCE_FILE = "11_RANDOM_COMPLETENESS_DONOR_SOURCE_BACKEND.zip"
NOTES_FILE = "21_RANDOM_COMPLETENESS_DONOR_RELEASE_NOTES.md"
RIGHTS_FILE = "31_RANDOM_COMPLETENESS_DONOR_LICENSE_AND_ATTRIBUTION.md"
QA_FILE = "41_RANDOM_COMPLETENESS_DONOR_STATIC_QA_EVIDENCE.zip"
MANIFEST_FILE = "70_C140_RANDOM_COMPLETENESS_FULL_UNION_MANIFEST.csv"
CHECKSUMS_FILE = "SHA256SUMS_C140_RANDOM_COMPLETENESS.txt"
ROOT_RECEIPT_FILE = "80_C140_RANDOM_COMPLETENESS_FULL_UNION_ROOT_RECEIPT.json"
PACKAGE_RECEIPT = BUILD / "RANDOM_COMPLETENESS_RELEASE_PACKAGE_RECEIPT.json"

IMPORT_RECEIPT = "components/random-completeness/IMPORT_RECEIPT.json"
BUILD_RECEIPT = "components/random-completeness/build/BUILD_RECEIPT.json"
QA_RECEIPT = "components/random-completeness/build/QA_RECEIPT.json"
READER_MANIFEST = "components/random-completeness/build/MANIFEST.csv"
FREEZE_MANIFEST = "components/random-completeness/authority/FREEZE_MANIFEST.csv"
LIVE_REVERIFY = "components/random-completeness/authority/LIVE_REVERIFY_2026-08-28.json"
COMPONENT_README = "components/random-completeness/README.md"
COMPONENT_RIGHTS = "components/random-completeness/LICENSE_AND_ATTRIBUTION.md"

SOURCE_SUPPORT_FILES: tuple[str, ...] = (
    COMPONENT_README,
    COMPONENT_RIGHTS,
    IMPORT_RECEIPT,
    BUILD_RECEIPT,
    QA_RECEIPT,
    READER_MANIFEST,
    "scripts/import_random_completeness_donor.py",
    "scripts/build_random_completeness_donor.py",
    "scripts/qa_random_completeness_donor.py",
)

TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".html",
    ".js",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".svg",
    ".txt",
}
FORBIDDEN_TEXT_MARKERS = (
    b"c:\\users\\",
    b"c:/users/",
    b"/users/",
    b"file://",
)
SECRET_PATTERNS = (
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"authorization\s*:\s*bearer\s+[A-Za-z0-9._~-]{16,}", re.IGNORECASE),
)

FIELDS = (
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


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def identity(payload: bytes) -> dict[str, Any]:
    return {"bytes": len(payload), "sha256": sha256(payload)}


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


def require_identity(label: str, record: Any, payload: bytes, expected_path: str | None = None) -> None:
    if not isinstance(record, dict):
        raise RuntimeError(f"{label} identity is absent")
    if record.get("bytes") != len(payload) or record.get("sha256") != sha256(payload):
        raise RuntimeError(f"{label} byte/hash identity differs")
    if expected_path is not None and record.get("path") != expected_path:
        raise RuntimeError(f"{label} path differs: {record.get('path')!r}")


def safe_member(name: str) -> None:
    if not name or "\\" in name or "\x00" in name:
        raise RuntimeError(f"unsafe archive member name: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"unsafe archive member name: {name!r}")
    if ":" in path.parts[0]:
        raise RuntimeError(f"unsafe archive member drive prefix: {name!r}")


def assert_unique_names(names: list[str], label: str) -> None:
    for name in names:
        safe_member(name)
    folded = [name.casefold() for name in names]
    if len(folded) != len(set(folded)):
        raise RuntimeError(f"{label} has duplicate or case-insensitive-colliding names")


def privacy_scan(entries: dict[str, bytes], label: str) -> dict[str, int]:
    scanned = 0
    for name, payload in entries.items():
        suffix = PurePosixPath(name).suffix.casefold()
        if suffix not in TEXT_SUFFIXES:
            continue
        scanned += 1
        lowered = payload.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                raise RuntimeError(f"{label} contains forbidden local/sensitive marker in {name}: {marker!r}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(payload):
                raise RuntimeError(f"{label} contains credential-shaped text in {name}: {pattern.pattern!r}")
    return {"text_files_scanned": scanned, "forbidden_markers_found": 0}


def deterministic_zip(entries: dict[str, bytes]) -> bytes:
    names = list(entries)
    assert_unique_names(names, "ZIP input")
    ordered = sorted(names, key=lambda item: (item.casefold(), item))
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in ordered:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(
                info,
                entries[name],
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    payload = output.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        infos = archive.infolist()
        if archive.testzip() is not None:
            raise RuntimeError("deterministic ZIP CRC verification failed")
        if [info.filename for info in infos] != ordered:
            raise RuntimeError("deterministic ZIP entry order differs")
        if any(info.date_time != (1980, 1, 1, 0, 0, 0) for info in infos):
            raise RuntimeError("deterministic ZIP timestamp differs")
    return payload


def validate_base_package() -> tuple[bytes, list[dict[str, Any]]]:
    receipt_payload, receipt = read_json(BASE_RECEIPT_PATH)
    if len(receipt_payload) != BASE_RECEIPT_BYTES or sha256(receipt_payload) != BASE_RECEIPT_SHA256:
        raise RuntimeError("hard-pinned consolidated-readers package receipt differs")
    if (
        receipt.get("schema") != BASE_RECEIPT_SCHEMA
        or receipt.get("status") != "ready"
        or receipt.get("version") != BASE_RECEIPT_VERSION
    ):
        raise RuntimeError("hard-pinned consolidated-readers contract differs")
    inventory = receipt.get("publication_inventory")
    if not isinstance(inventory, dict):
        raise RuntimeError("base publication inventory is absent")
    files = inventory.get("files")
    if not isinstance(files, list) or not all(isinstance(item, dict) for item in files):
        raise RuntimeError("base publication file rows are absent")
    if (
        inventory.get("file_count") != BASE_FILE_COUNT
        or inventory.get("total_bytes") != BASE_TOTAL_BYTES
        or inventory.get("reader_first") is not True
        or inventory.get("primary_file") != PRIMARY_FILE
        or inventory.get("secondary_reader") != SECONDARY_READER
        or files[0].get("filename") != PRIMARY_FILE
        or files[0].get("primary_reader") is not True
        or files[1].get("filename") != SECONDARY_READER
        or list(inventory.get("fields", [])) != list(FIELDS)
    ):
        raise RuntimeError("base reader-first inventory contract differs")
    names = [str(item.get("filename", "")) for item in files]
    assert_unique_names(names, "base publication inventory")
    if inventory.get("upload_order") != names:
        raise RuntimeError("base upload order differs from base file rows")
    verified: list[dict[str, Any]] = []
    for order, item in enumerate(files, 1):
        name = names[order - 1]
        if item.get("upload_order") != order or item.get("source_path") != f"release/{name}":
            raise RuntimeError(f"base row metadata differs: {name}")
        if set(item) != set(FIELDS):
            raise RuntimeError(f"base row fields differ: {name}")
        payload = read_exact(f"release/{name}")
        if item.get("bytes") != len(payload) or item.get("sha256") != sha256(payload):
            raise RuntimeError(f"base release file identity differs: {name}")
        verified.append(dict(item))
    if len(verified) != BASE_FILE_COUNT or sum(item["bytes"] for item in verified) != BASE_TOTAL_BYTES:
        raise RuntimeError("base release union count or bytes differ")
    return receipt_payload, verified


def validate_donor() -> dict[str, Any]:
    import_payload, imported = read_json(IMPORT_RECEIPT)
    build_payload, built = read_json(BUILD_RECEIPT)
    qa_payload, qa = read_json(QA_RECEIPT)
    freeze_payload = read_exact(FREEZE_MANIFEST)
    reader_manifest_payload = read_exact(READER_MANIFEST)
    live_payload, live = read_json(LIVE_REVERIFY)
    rights_payload = read_exact(COMPONENT_RIGHTS)

    if (
        imported.get("schema") != "o006.c140.random-completeness.import.v1"
        or imported.get("component") != "O006/C140 Random completeness donor"
        or imported.get("target_locale") != "id-ID"
        or imported.get("translation_provenance") != PROVENANCE
        or imported.get("source_bytes") != 57_507
        or imported.get("source_sha256") != "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4"
        or imported.get("target_bytes") != 60_895
        or imported.get("target_sha256") != "255ac88f235727301ee341eef79b9578910be88b7e2e038d4dfecc0ed686513c"
        or imported.get("counts") != {
            "adverse_records": 19,
            "entities": 325,
            "relations": 474,
            "translation_ledger_rows": 1,
        }
        or imported.get("rights_discrepancy", {}).get("preserved") is not True
        or imported.get("machine_local_paths_recorded") is not False
    ):
        raise RuntimeError("Random donor import receipt differs from admitted component")

    imported_files = imported.get("files")
    if not isinstance(imported_files, list) or len(imported_files) != 24:
        raise RuntimeError("Random donor import inventory is not the exact 24-file closure")
    imported_names: list[str] = []
    for item in imported_files:
        if not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}:
            raise RuntimeError("Random donor import file row differs")
        relative = str(item["path"])
        safe_member(relative)
        payload = read_exact(f"components/random-completeness/{relative}")
        require_identity(f"Random donor import file {relative}", item, payload, relative)
        imported_names.append(relative)
    assert_unique_names(imported_names, "Random donor import inventory")

    if built.get("schema") != "o006.c140.random-completeness.build.v1" or built.get("status") != "built":
        raise RuntimeError("Random donor build receipt is not admitted")
    require_identity("Random donor build-to-import binding", built.get("authority", {}).get("import_receipt"), import_payload, "IMPORT_RECEIPT.json")
    if (
        built.get("canonical_import_preserved") is not True
        or built.get("offline", {}).get("browser_used") is not False
        or built.get("offline", {}).get("direct_local_dependencies_closed") is not True
        or built.get("reader", {}).get("files") != 18
        or built.get("reader", {}).get("bytes") != 1_798_250
        or built.get("reader", {}).get("manifest_sha256") != sha256(reader_manifest_payload)
    ):
        raise RuntimeError("Random donor deterministic build gate differs")

    require_identity("Random donor QA-to-build binding", qa.get("deterministic_build_replay", {}).get("build_receipt"), build_payload, "build/BUILD_RECEIPT.json")
    if (
        qa.get("schema") != "o006.c140.random-completeness.qa.v1"
        or qa.get("status") != "pass"
        or qa.get("browser_processes_used") is not False
        or qa.get("deterministic_build_replay", {}).get("canonical_import_preserved") is not True
        or qa.get("reader", {}).get("files") != 18
        or qa.get("reader", {}).get("bytes") != 1_798_250
        or qa.get("modular_backend", {}).get("entities") != 325
        or qa.get("modular_backend", {}).get("relations") != 474
        or qa.get("privacy", {}).get("machine_local_paths_found") != 0
        or qa.get("privacy", {}).get("sensitive_values_found") != 0
        or qa.get("rights", {}).get("aggregate_uniform_relicense") is not False
        or "browser-free-static-qa" not in qa.get("gates", [])
    ):
        raise RuntimeError("Random donor static QA gate differs")
    if (
        live.get("schema") != "o006.c140.random-completeness.live-authority-reverify.v1"
        or live.get("all_expected_identities_match") is not True
        or live.get("machine_local_paths_recorded") is not False
        or live.get("rights_witness_discrepancy", {}).get("preserved") is not True
        or "no browser process" not in str(live.get("method", "")).lower()
    ):
        raise RuntimeError("Random donor live authority receipt differs")

    rights_text = rights_payload.decode("utf-8")
    for statement in (
        "creativecommons.org/licenses/by/2.0/",
        "creativecommons.org/licenses/by/1.0/",
        "Apache License 2.0",
        "CC BY-SA",
        "tidak direlisensi secara seragam",
        PROVENANCE,
    ):
        if statement not in rights_text:
            raise RuntimeError(f"Random donor rights statement is absent: {statement}")

    rows = list(csv.DictReader(io.StringIO(reader_manifest_payload.decode("utf-8"))))
    if len(rows) != 18 or list(rows[0]) != ["relative_path", "role", "bytes", "sha256"]:
        raise RuntimeError("Random donor reader manifest shape differs")
    reader_entries: dict[str, bytes] = {}
    for row in rows:
        relative = row["relative_path"]
        safe_member(relative)
        payload = read_exact(f"components/random-completeness/build/html-id/{relative}")
        if int(row["bytes"]) != len(payload) or row["sha256"] != sha256(payload):
            raise RuntimeError(f"Random donor reader manifest identity differs: {relative}")
        reader_entries[relative] = payload
    assert_unique_names(list(reader_entries), "Random donor reader")
    if len(reader_entries) != 18 or sum(len(payload) for payload in reader_entries.values()) != 1_798_250:
        raise RuntimeError("Random donor reader inventory differs")

    return {
        "import_payload": import_payload,
        "import_receipt": imported,
        "imported_files": imported_files,
        "build_payload": build_payload,
        "build_receipt": built,
        "qa_payload": qa_payload,
        "qa_receipt": qa,
        "freeze_payload": freeze_payload,
        "reader_manifest_payload": reader_manifest_payload,
        "live_payload": live_payload,
        "rights_payload": rights_payload,
        "reader_entries": reader_entries,
    }


def build_reader_archive(donor: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    entries = dict(donor["reader_entries"])
    privacy = privacy_scan(entries, "Random donor reader archive")
    payload = deterministic_zip(entries)
    return payload, {
        "substantive_entries": len(entries),
        "uncompressed_bytes": sum(len(value) for value in entries.values()),
        "entry_order": sorted(entries, key=lambda item: (item.casefold(), item)),
        "entry_manifest": [
            {"entry": name, **identity(entries[name])}
            for name in sorted(entries, key=lambda item: (item.casefold(), item))
        ],
        "privacy": privacy,
        "archive_method": "ZIP_DEFLATED level 9; fixed 1980-01-01 timestamps; canonical entry order",
    }


def build_source_archive(donor: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    entries: dict[str, bytes] = {}
    for item in donor["imported_files"]:
        relative = str(item["path"])
        archive_name = f"random-completeness/{relative}"
        entries[archive_name] = read_exact(f"components/random-completeness/{relative}")
    for relative in SOURCE_SUPPORT_FILES:
        if relative.startswith("components/random-completeness/"):
            archive_name = f"random-completeness/{relative.removeprefix('components/random-completeness/')}"
        else:
            archive_name = relative
        if archive_name in entries:
            raise RuntimeError(f"source/backend archive collision: {archive_name}")
        entries[archive_name] = read_exact(relative)
    privacy = privacy_scan(entries, "Random donor source/backend archive")
    inventory_name = "SOURCE_BACKEND_PACKAGE_INVENTORY.json"
    inventory = canonical_json({
        "schema": "o006.c140.random-completeness-source-backend-inventory.v1",
        "status": "complete",
        "component": "exact one-page Random completeness donor",
        "canonical_target_included": True,
        "authority_closure_included": True,
        "modular_backend_included": True,
        "replay_scripts_included": [
            "scripts/import_random_completeness_donor.py",
            "scripts/build_random_completeness_donor.py",
            "scripts/qa_random_completeness_donor.py",
        ],
        "reader_build_excluded": True,
        "reader_build_exclusion_reason": f"published separately as {READER_FILE}",
        "entries": [
            {"entry": name, **identity(entries[name])}
            for name in sorted(entries, key=lambda item: (item.casefold(), item))
        ],
        "self_exclusion": {
            "entry": inventory_name,
            "reason": "non-self-referential cryptographic package inventory",
        },
    })
    entries[inventory_name] = inventory
    payload = deterministic_zip(entries)
    return payload, {
        "entries": len(entries),
        "uncompressed_bytes": sum(len(value) for value in entries.values()),
        "inventory": {"entry": inventory_name, **identity(inventory)},
        "privacy": privacy,
        "archive_method": "ZIP_DEFLATED level 9; fixed 1980-01-01 timestamps; canonical entry order",
    }


def build_qa_archive(donor: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    entries = {
        "authority/FREEZE_MANIFEST.csv": donor["freeze_payload"],
        "authority/LIVE_REVERIFY_2026-08-28.json": donor["live_payload"],
        "component/IMPORT_RECEIPT.json": donor["import_payload"],
        "component/build/BUILD_RECEIPT.json": donor["build_payload"],
        "component/build/MANIFEST.csv": donor["reader_manifest_payload"],
        "component/build/QA_RECEIPT.json": donor["qa_payload"],
    }
    privacy = privacy_scan(entries, "Random donor static QA evidence")
    inventory_name = "QA_EVIDENCE_INVENTORY.json"
    inventory = canonical_json({
        "schema": "o006.c140.random-completeness-static-qa-evidence.v1",
        "status": "passed",
        "method": "static, deterministic, browser-free",
        "current_component_gate": True,
        "entries": [
            {"entry": name, **identity(entries[name]), "classification": "current-static-evidence"}
            for name in sorted(entries, key=lambda item: (item.casefold(), item))
        ],
        "self_exclusion": {
            "entry": inventory_name,
            "reason": "non-self-referential cryptographic evidence inventory",
        },
    })
    entries[inventory_name] = inventory
    payload = deterministic_zip(entries)
    return payload, {
        "entries": len(entries),
        "uncompressed_bytes": sum(len(value) for value in entries.values()),
        "inventory": {"entry": inventory_name, **identity(inventory)},
        "privacy": privacy,
        "archive_method": "ZIP_DEFLATED level 9; fixed 1980-01-01 timestamps; canonical entry order",
    }


def release_notes(reader: bytes, source: bytes, qa: bytes) -> bytes:
    return (
        "# O006/C140 — donor kelengkapan Random (Bahasa Indonesia)\n\n"
        "Status publikasi: **tulang punggung Penn State lengkap (14/14); donor Random "
        "lengkap (tepat satu halaman); kursus C140 belum lengkap sampai pendamping "
        "orisinal selesai**. Donor ini adalah halaman Kyle Siegrist, *Random*, "
        "“Sufficient, Complete, and Ancillary Statistics”; bukan pengganti atau fork "
        "kedua dari edisi lengkap *Random* 29 halaman.\n\n"
        f"`{READER_FILE}` ({len(reader):,} byte) adalah pembaca HTML luring mandiri. "
        f"`{SOURCE_FILE}` ({len(source):,} byte) memuat sumber kanonis, otoritas, backend "
        "modular, receipt, dan skrip pemutaran ulang. "
        f"`{QA_FILE}` ({len(qa):,} byte) memuat bukti QA statis deterministik.\n\n"
        "Hak komponen tetap terpisah: saksi resmi *Random* menyebut CC BY 2.0 sementara "
        "`Credits.html` menautkan CC BY 1.0; MathJax 3.1.2 adalah Apache-2.0; lapisan "
        "orisinal repositori adalah CC BY-SA 4.0; spine Penn State tetap CC BY-NC 4.0 "
        "kecuali dinyatakan lain. Agregat tidak direlisensi secara seragam dan memakai "
        "label platform `other-open`.\n\n"
        f"Provenans terjemahan dan rekayasa edisi: {PROVENANCE}. Semua kredit penulis "
        "sumber dan kontributor manusia dipertahankan.\n"
    ).encode("utf-8")


def manifest_payload(files: list[dict[str, Any]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for item in files:
        writer.writerow({field: item[field] for field in FIELDS})
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
    base_receipt_payload, base_files = validate_base_package()
    donor = validate_donor()
    reader_payload, reader_info = build_reader_archive(donor)
    source_payload, source_info = build_source_archive(donor)
    qa_payload, qa_info = build_qa_archive(donor)
    rights_payload = donor["rights_payload"]
    notes_payload = release_notes(reader_payload, source_payload, qa_payload)

    donor_payloads = {
        READER_FILE: reader_payload,
        SOURCE_FILE: source_payload,
        NOTES_FILE: notes_payload,
        RIGHTS_FILE: rights_payload,
        QA_FILE: qa_payload,
    }
    new_names = list(donor_payloads) + [MANIFEST_FILE, CHECKSUMS_FILE, ROOT_RECEIPT_FILE]
    assert_unique_names([item["filename"] for item in base_files] + new_names, "cumulative release")
    if any((RELEASE / name).is_symlink() for name in new_names):
        raise RuntimeError("new release output collides with a symlink")

    donor_records = [
        record(18, READER_FILE, reader_payload, "standalone-complete-random-completeness-offline-reader", "current-random-completeness-donor", "application/zip"),
        record(19, SOURCE_FILE, source_payload, "compact-resumable-random-completeness-source-backend", "current-random-completeness-donor", "application/zip"),
        record(20, NOTES_FILE, notes_payload, "donor-scope-status-rights-provenance", "current-random-completeness-donor", "text/markdown"),
        record(21, RIGHTS_FILE, rights_payload, "donor-component-rights-and-attribution", "current-random-completeness-donor", "text/markdown"),
        record(22, QA_FILE, qa_payload, "compact-browser-free-static-qa-evidence", "current-random-completeness-donor", "application/zip"),
    ]
    substantive = base_files + donor_records
    manifest = manifest_payload(substantive)
    manifest_record = record(23, MANIFEST_FILE, manifest, "cumulative-union-substantive-manifest", "c140-random-completeness-cumulative-union", "text/csv")
    checksums_covered = substantive + [manifest_record]
    checksums = "".join(
        f"{item['sha256']}  {item['filename']}\n" for item in checksums_covered
    ).encode("utf-8")
    checksums_record = record(24, CHECKSUMS_FILE, checksums, "cumulative-union-sha256-checksums", "c140-random-completeness-cumulative-union", "text/plain")
    root_covered = checksums_covered + [checksums_record]
    root_receipt = canonical_json({
        "schema": "o006.c140.random-completeness-full-union-root.v1",
        "status": "ready",
        "version": VERSION,
        "coverage": {
            "penn_state_spine": "complete: landing/index plus Lesson00-Lesson12 (14 of 14)",
            "random_completeness_donor": "complete: exact one-page donor",
            "c140_course": "incomplete: original rigor, simulation, and mastery companion remains",
        },
        "concept_doi": CONCEPT_DOI,
        "preserved_base_release": {
            "record_id": BASE_RECORD_ID,
            "doi": BASE_RECORD_DOI,
            "package_receipt": {"path": BASE_RECEIPT_PATH, **identity(base_receipt_payload)},
            "file_count": BASE_FILE_COUNT,
            "bytes": BASE_TOTAL_BYTES,
            "byte_identity_and_order_verified": True,
        },
        "rights": {
            "aggregate_platform_license": "other-open",
            "aggregate_uniform_relicense": False,
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
            "reason": "non-self-referential cryptographic cumulative release root",
        },
    })
    root_record = record(25, ROOT_RECEIPT_FILE, root_receipt, "cumulative-union-release-root-receipt", "c140-random-completeness-cumulative-union", "application/json")
    publication_files = substantive + [manifest_record, checksums_record, root_record]
    if [item["upload_order"] for item in publication_files] != list(range(1, 26)):
        raise RuntimeError("cumulative publication order is not contiguous")
    if publication_files[:BASE_FILE_COUNT] != base_files:
        raise RuntimeError("base 17-file rows or order changed")
    if publication_files[0]["filename"] != PRIMARY_FILE or publication_files[1]["filename"] != SECONDARY_READER:
        raise RuntimeError("reader-first order changed")

    payloads = {
        **donor_payloads,
        MANIFEST_FILE: manifest,
        CHECKSUMS_FILE: checksums,
        ROOT_RECEIPT_FILE: root_receipt,
    }
    generated_text = {
        NOTES_FILE: notes_payload,
        RIGHTS_FILE: rights_payload,
        MANIFEST_FILE: manifest,
        CHECKSUMS_FILE: checksums,
        ROOT_RECEIPT_FILE: root_receipt,
    }
    generated_privacy = privacy_scan(generated_text, "generated release controls")

    packager_payload = read_exact("scripts/package_random_completeness_release.py")
    package_receipt = canonical_json({
        "schema": "o006.c140.random-completeness-release-package.v1",
        "status": "ready",
        "version": VERSION,
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "coverage": {
            "penn_state_spine": {
                "status": "complete",
                "documents": 14,
                "boundary": "landing/index plus Lesson00-Lesson12",
            },
            "random_completeness_donor": {
                "status": "complete",
                "boundary": "exact one-page Sufficient, Complete, and Ancillary Statistics donor",
                "source_bytes": 57_507,
                "source_sha256": "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4",
                "target_bytes": 60_895,
                "target_sha256": "255ac88f235727301ee341eef79b9578910be88b7e2e038d4dfecc0ed686513c",
            },
            "c140_course": {
                "status": "incomplete",
                "remaining": "original rigor, simulation, and mastery companion",
            },
        },
        "lineage": {
            "concept_doi": CONCEPT_DOI,
            "base_record_id": BASE_RECORD_ID,
            "base_record_doi": BASE_RECORD_DOI,
            "create_competing_concept": False,
        },
        "rights": {
            "penn_state_content_and_adaptation": "CC BY-NC 4.0 except where otherwise noted",
            "random_landing_witness": "CC BY 2.0",
            "random_credits_witness": "CC BY 1.0",
            "random_rights_discrepancy_preserved": True,
            "mathjax_3_1_2": "Apache-2.0",
            "original_repository_layer": "CC BY-SA 4.0",
            "aggregate_uniform_relicense": False,
            "aggregate_platform_license": "other-open",
        },
        "gates": {
            "base_package": {
                "receipt": {"path": BASE_RECEIPT_PATH, **identity(base_receipt_payload)},
                "file_count": BASE_FILE_COUNT,
                "bytes": BASE_TOTAL_BYTES,
                "byte_identity_and_order_verified": True,
                "primary_pdf_first": True,
                "secondary_epub_second": True,
            },
            "donor_import": {"path": IMPORT_RECEIPT, **identity(donor["import_payload"])},
            "donor_build": {"path": BUILD_RECEIPT, **identity(donor["build_payload"])},
            "donor_static_qa": {"path": QA_RECEIPT, **identity(donor["qa_payload"])},
            "donor_live_authority": {"path": LIVE_REVERIFY, **identity(donor["live_payload"])},
            "archives": {
                READER_FILE: {**identity(reader_payload), **reader_info},
                SOURCE_FILE: {**identity(source_payload), **source_info},
                QA_FILE: {**identity(qa_payload), **qa_info},
            },
            "privacy": generated_privacy,
        },
        "packager": {
            "path": "scripts/package_random_completeness_release.py",
            **identity(packager_payload),
            "network_access": False,
            "browser_processes": False,
            "credential_access": False,
            "publication_side_effects": False,
            "recursive_repository_discovery": False,
        },
        "publication_inventory": {
            "primary_file": PRIMARY_FILE,
            "secondary_reader": SECONDARY_READER,
            "reader_first": True,
            "preserved_base_file_count": BASE_FILE_COUNT,
            "donor_added_file_count": 5,
            "cumulative_control_file_count": 3,
            "file_count": len(publication_files),
            "total_bytes": sum(item["bytes"] for item in publication_files),
            "fields": list(FIELDS),
            "files": publication_files,
            "upload_order": [item["filename"] for item in publication_files],
        },
        "outputs": {
            "manifest": {"filename": MANIFEST_FILE, **identity(manifest)},
            "checksums": {"filename": CHECKSUMS_FILE, **identity(checksums)},
            "root_receipt": {"filename": ROOT_RECEIPT_FILE, **identity(root_receipt)},
            "package_receipt": {
                "path": "build/RANDOM_COMPLETENESS_RELEASE_PACKAGE_RECEIPT.json",
                "self_hash_excluded": True,
            },
        },
    })
    privacy_scan({"package_receipt.json": package_receipt}, "package receipt")
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
    inventory = parsed["publication_inventory"]
    print(json.dumps({
        "mode": state,
        "schema": parsed["schema"],
        "version": parsed["version"],
        "files": inventory["file_count"],
        "bytes": inventory["total_bytes"],
        "primary_file": inventory["primary_file"],
        "primary_sha256": inventory["files"][0]["sha256"],
        "donor_reader": READER_FILE,
        "donor_reader_sha256": next(item["sha256"] for item in inventory["files"] if item["filename"] == READER_FILE),
        "package_receipt_sha256": sha256(receipt),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
