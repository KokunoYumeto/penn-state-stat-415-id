#!/usr/bin/env python3
"""Create deterministic reader-first packages through complete Lesson 01.

This script deliberately writes only the cumulative release payloads and its
package receipt.  Historical FIRST_UNIT artifacts are inputs and are never
rewritten.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
READER = ROOT / "build" / "html-id"

READER_ZIP = "00_stat415-id-through-lesson01-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-through-lesson01-source-backend.zip"
RELEASE_NOTES = "20_THROUGH_LESSON01_RELEASE_NOTES.md"
RELEASE_LICENSE = "30_LICENSE.md"
RELEASE_QA = "40_THROUGH_LESSON01_QA_RECEIPT.json"
RELEASE_VISUAL_QA = "41_THROUGH_LESSON01_VISUAL_QA_RECEIPT.json"
RELEASE_MANIFEST = "50_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS.txt"
ROOT_RECEIPT = "60_THROUGH_LESSON01_RELEASE_ROOT_RECEIPT.json"
RECEIPT = ROOT / "build" / "THROUGH_LESSON01_PACKAGE_RECEIPT.json"

ZIP_TIME = (2026, 8, 24, 0, 0, 0)
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPLETE_DOCUMENTS = ["index", "Lesson00", "Lesson01"]
# Immutable, reviewable closure for the exact 3-of-14 boundary.  Never replace
# this with recursive directory discovery: source-package membership is a
# publication decision, not a filesystem side effect.
SOURCE_PACKAGE_FILES = (
    "LICENSE.md",
    "README.md",
    "requirements.txt",
    # Reproducibility scripts.  Publishers and remote-release verifiers are
    # deliberately absent, as is the next-boundary Lesson 02 normalizer.
    "scripts/freeze_mathjax.py",
    "scripts/freeze_first_unit_assets.py",
    "scripts/normalize_first_unit.py",
    "scripts/merge_first_unit_translations.py",
    "scripts/build_first_unit.py",
    "scripts/freeze_lesson01_assets.py",
    "scripts/normalize_lesson01.py",
    "scripts/merge_lesson01_translations.py",
    "scripts/build_through_lesson01.py",
    "scripts/qa_through_lesson01.py",
    "scripts/package_through_lesson01_release.py",
    # Frozen upstream authority for the exact translated boundary.
    "authority/upstream/stat415/index.html",
    "authority/upstream/stat415/Lesson00.html",
    "authority/upstream/stat415/Lesson01.html",
    # Frozen reader runtime.
    "authority/runtime/MathJax-3.1.2/URL_MANIFEST.csv",
    "authority/runtime/MathJax-3.1.2/FREEZE_RECEIPT.json",
    "authority/runtime/MathJax-3.1.2/LICENSE.txt",
    "authority/runtime/MathJax-3.1.2/tex-svg.js",
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/color.js",
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/enclose.js",
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/cancel.js",
    # First-unit and Lesson 01 asset closures.
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
    # Normalized source, Indonesian source, and reusable backend records.
    "source/normalized/en-US/index.html",
    "source/normalized/en-US/Lesson00.html",
    "source/normalized/en-US/Lesson01.html",
    "source/id-ID/index.html",
    "source/id-ID/Lesson00.html",
    "source/id-ID/Lesson01.html",
    "source/id-ID/reader.css",
    "source/id-ID/course_card_alt_text.json",
    "source/id-ID/first_unit_translation.csv",
    "source/id-ID/lesson01_translation.csv",
    "backend/first_unit_segments.jsonl",
    "backend/first_unit_structures.jsonl",
    "backend/first_unit_translation_bindings.jsonl",
    "backend/first_unit_documents.jsonl",
    "backend/first_unit_corrections.jsonl",
    "backend/lesson01_source_catalogue.jsonl",
    "backend/lesson01_translation_bindings.jsonl",
    "backend/through_lesson01_documents.jsonl",
    "backend/through_lesson01_corrections.jsonl",
    # Exact bounded translation inputs and deterministic Lesson 01 evidence.
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
    # The sole semantic control input.  CURRENT_CURSOR/CURRENT_STATE,
    # checkpoints, notes, and every publication/lineage receipt are excluded.
    "00_control/ADVERSE_LEDGER.jsonl",
    # Deterministic build and QA evidence through the current boundary.
    "build/FIRST_UNIT_NORMALIZATION_RECEIPT.json",
    "build/FIRST_UNIT_TRANSLATION_RECEIPT.json",
    "build/FIRST_UNIT_BUILD_RECEIPT.json",
    "build/FIRST_UNIT_MANIFEST.csv",
    "build/LESSON01_NORMALIZATION_RECEIPT.json",
    "build/LESSON01_TRANSLATION_RECEIPT.json",
    "build/THROUGH_LESSON01_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON01_MANIFEST.csv",
    "build/THROUGH_LESSON01_QA_RECEIPT.json",
    "build/THROUGH_LESSON01_VISUAL_QA_RECEIPT.json",
)

SECRET_EXACT_NAMES = {
    ".env",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "credentials",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
}
SECRET_NAME_FRAGMENTS = (
    "access_key",
    "api_key",
    "credential",
    "private_key",
    "secret",
    "token",
)
SECRET_SUFFIXES = (".key", ".kdbx", ".p12", ".pem", ".pfx")
TEMP_NAME_SUFFIXES = (".bak", ".pyc", ".swp", ".temp", ".tmp", "~")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def decode_json_object(payload: bytes, label: str) -> dict[str, Any]:
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON receipt is not an object: {label}")
    return value


def safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or "\\" in value
        or (path.parts and ":" in path.parts[0])
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise RuntimeError(f"unsafe manifest path: {value!r}")
    return path


def read_confined_regular_file(base: Path, relative: PurePosixPath, label: str) -> bytes:
    base_resolved = base.resolve(strict=True)
    if base.is_symlink():
        raise RuntimeError(f"symlinked package root is forbidden: {label}")
    try:
        base_resolved.relative_to(ROOT.resolve(strict=True))
    except ValueError as exc:
        raise RuntimeError(f"package root resolves outside ROOT: {label}") from exc
    path = base.joinpath(*relative.parts)
    cursor = path
    while cursor != base:
        if cursor.is_symlink():
            raise RuntimeError(f"symlinked package input is forbidden: {label}")
        cursor = cursor.parent
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise RuntimeError(f"package input is missing: {label}") from exc
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise RuntimeError(f"package input resolves outside its admitted root: {label}") from exc
    if not resolved.is_file():
        raise RuntimeError(f"package input is not a regular file: {label}")
    return resolved.read_bytes()


def reject_sensitive_source_name(relative: PurePosixPath) -> None:
    for part in relative.parts:
        lowered = part.casefold()
        if (
            lowered in SECRET_EXACT_NAMES
            or any(fragment in lowered for fragment in SECRET_NAME_FRAGMENTS)
            or lowered.endswith(SECRET_SUFFIXES)
        ):
            raise RuntimeError(f"secret-like source-package filename is forbidden: {relative}")
        if lowered == "__pycache__" or lowered.endswith(TEMP_NAME_SUFFIXES):
            raise RuntimeError(f"cache or temporary source-package filename is forbidden: {relative}")


def reject_machine_local_text(relative: PurePosixPath, payload: bytes) -> None:
    lowered = payload.lower()
    backslash = bytes((92,))
    markers = (
        b"c:" + backslash + b"users" + backslash,
        b"c:" + b"/" + b"users" + b"/",
    )
    if any(marker in lowered for marker in markers):
        raise RuntimeError(f"machine-local Windows profile path in source-package input: {relative}")


def snapshot_source_files() -> dict[PurePosixPath, bytes]:
    relatives = [safe_relative(value) for value in SOURCE_PACKAGE_FILES]
    if len(relatives) != 86:
        raise RuntimeError("source-package allowlist is not the admitted 86-file closure")
    folded = [relative.as_posix().casefold() for relative in relatives]
    if len(set(folded)) != len(folded):
        raise RuntimeError("case-insensitive duplicate in source-package allowlist")
    snapshot: dict[PurePosixPath, bytes] = {}
    for relative in relatives:
        reject_sensitive_source_name(relative)
        payload = read_confined_regular_file(ROOT, relative, relative.as_posix())
        reject_machine_local_text(relative, payload)
        snapshot[relative] = payload
    return snapshot


def archive(files: dict[PurePosixPath, bytes]) -> bytes:
    ordered = sorted(files, key=lambda value: value.as_posix().casefold())
    if len({path.as_posix().casefold() for path in ordered}) != len(ordered):
        raise RuntimeError("case-insensitive duplicate path in release ZIP")

    output = io.BytesIO()
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_STORED,
    ) as bundle:
        for path in ordered:
            info = zipfile.ZipInfo(path.as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            bundle.writestr(
                info,
                files[path],
                compress_type=zipfile.ZIP_STORED,
            )

    payload = output.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError("release ZIP integrity test failed")
        expected_names = [path.as_posix() for path in ordered]
        if bundle.namelist() != expected_names:
            raise RuntimeError("release ZIP entry inventory differs")
        for path in ordered:
            if bundle.read(path.as_posix()) != files[path]:
                raise RuntimeError(
                    f"release ZIP entry identity differs: {path.as_posix()}"
                )
    return payload


def validate_receipts(source_snapshot: dict[PurePosixPath, bytes]) -> dict[str, bytes]:
    def admitted(relative: str) -> bytes:
        try:
            return source_snapshot[PurePosixPath(relative)]
        except KeyError as exc:
            raise RuntimeError(f"validated input is absent from source allowlist: {relative}") from exc

    build_payload = admitted("build/THROUGH_LESSON01_BUILD_RECEIPT.json")
    qa_payload = admitted("build/THROUGH_LESSON01_QA_RECEIPT.json")
    visual_payload = admitted("build/THROUGH_LESSON01_VISUAL_QA_RECEIPT.json")
    manifest_payload = admitted("build/THROUGH_LESSON01_MANIFEST.csv")
    build = decode_json_object(build_payload, "build/THROUGH_LESSON01_BUILD_RECEIPT.json")
    qa = decode_json_object(qa_payload, "build/THROUGH_LESSON01_QA_RECEIPT.json")
    visual = decode_json_object(
        visual_payload, "build/THROUGH_LESSON01_VISUAL_QA_RECEIPT.json"
    )
    manifest_sha = sha256(manifest_payload)

    expected_coverage = {
        "complete_count": 3,
        "complete_documents": COMPLETE_DOCUMENTS,
        "corpus_document_count": 14,
        "next_document": "Lesson02",
    }
    if build.get("schema") != "o006.stat415.through-lesson01-build.v1":
        raise RuntimeError("unexpected cumulative build-receipt schema")
    if build.get("status") != "built" or build.get("coverage") != expected_coverage:
        raise RuntimeError("cumulative build receipt is not the exact 3-of-14 boundary")
    if build.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("cumulative build receipt has wrong model provenance")
    build_reader = build.get("reader", {})
    if (
        build_reader.get("files") != 28
        or build_reader.get("manifest_sha256") != manifest_sha
        or build_reader.get("path") != "build/html-id"
    ):
        raise RuntimeError("cumulative build receipt does not bind the 28-file reader")

    if qa.get("schema") != "o006.stat415.through-lesson01-qa.v1":
        raise RuntimeError("unexpected cumulative QA-receipt schema")
    if qa.get("status") != "pass" or qa.get("coverage") != expected_coverage:
        raise RuntimeError("cumulative deterministic QA has not passed for 3 of 14")
    qa_reader = qa.get("reader", {})
    if qa_reader.get("files") != 28 or qa_reader.get("manifest_sha256") != manifest_sha:
        raise RuntimeError("cumulative QA receipt does not bind the 28-file reader")
    rights = qa.get("rights_and_provenance", {})
    if (
        rights.get("penn_state") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("mathjax_3_1_2") != "Apache-2.0"
        or rights.get("aggregate_uniform_relicense") is not False
        or rights.get("source_and_human_credits_preserved") is not True
        or rights.get("translation_provenance") != PROVENANCE
    ):
        raise RuntimeError("component rights or provenance QA is incomplete")

    if visual.get("schema") != "o006.stat415.through-lesson01-visual-qa.v1":
        raise RuntimeError("unexpected cumulative visual-QA schema")
    if visual.get("status") != "pass":
        raise RuntimeError("cumulative desktop/mobile visual QA has not passed")
    visual_evidence = visual.get("evidence", {})
    if visual_evidence.get("manifest_sha256") != manifest_sha:
        raise RuntimeError("visual QA does not bind the cumulative reader manifest")
    if visual_evidence.get("build_receipt_sha256") != sha256(build_payload):
        raise RuntimeError("visual QA does not bind the cumulative build receipt")
    if visual_evidence.get("qa_receipt_sha256") != sha256(qa_payload):
        raise RuntimeError("visual QA does not bind the cumulative QA receipt")
    if visual.get("visual_findings") not in ([], None):
        raise RuntimeError("visual QA contains unresolved findings")

    license_payload = admitted("LICENSE.md")
    license_text = license_payload.decode("utf-8")
    for required in ("CC BY-NC 4.0", "Apache License 2.0", "CC BY-SA 4.0"):
        if required not in license_text:
            raise RuntimeError(f"component-rights statement missing from LICENSE.md: {required}")
    if PROVENANCE not in admitted("README.md").decode("utf-8"):
        raise RuntimeError("exact translation provenance is missing from README.md")

    return {
        "build": build_payload,
        "qa": qa_payload,
        "visual": visual_payload,
        "manifest": manifest_payload,
        "license": license_payload,
    }


def reader_package(manifest_payload: bytes) -> tuple[bytes, dict[str, Any]]:
    rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"))))
    if len(rows) != 28:
        raise RuntimeError(f"expected exactly 28 reader files, found {len(rows)}")

    reader_paths: set[PurePosixPath] = set()
    for path in READER.rglob("*"):
        relative = PurePosixPath(path.relative_to(READER).as_posix())
        if path.is_symlink():
            raise RuntimeError(f"symlinked reader input is forbidden: {relative}")
        if path.is_file():
            reader_paths.add(relative)
    files: dict[PurePosixPath, bytes] = {}
    manifested: set[PurePosixPath] = set()
    reader_bytes = 0
    for row in rows:
        relative = safe_relative(row["relative_path"])
        if relative in manifested:
            raise RuntimeError(f"duplicate reader-manifest path: {relative}")
        data = read_confined_regular_file(READER, relative, relative.as_posix())
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {relative}")
        manifested.add(relative)
        reader_bytes += len(data)
        files[PurePosixPath("stat415-id-through-lesson01") / relative] = data
    if reader_paths != manifested:
        missing = sorted(path.as_posix() for path in manifested - reader_paths)
        extra = sorted(path.as_posix() for path in reader_paths - manifested)
        raise RuntimeError(f"reader inventory differs; missing={missing}; extra={extra}")

    embedded_manifest = PurePosixPath(
        "stat415-id-through-lesson01/THROUGH_LESSON01_MANIFEST.csv"
    )
    files[embedded_manifest] = manifest_payload
    payload = archive(files)
    return payload, {
        "reader_files": len(rows),
        "reader_bytes": reader_bytes,
        "package_entries": len(files),
        "uncompressed_bytes": sum(len(value) for value in files.values()),
        "manifest_bytes": len(manifest_payload),
        "manifest_sha256": sha256(manifest_payload),
    }


def source_package(
    source_snapshot: dict[PurePosixPath, bytes],
) -> tuple[bytes, dict[str, Any]]:
    files: dict[PurePosixPath, bytes] = {}
    package_root = PurePosixPath("penn-state-stat-415-id")
    for relative, data in source_snapshot.items():
        files[package_root / relative] = data

    payload = archive(files)
    allowlist_manifest = canonical_json(
        [
            {
                "path": relative.as_posix(),
                "bytes": len(data),
                "sha256": sha256(data),
            }
            for relative, data in sorted(
                source_snapshot.items(), key=lambda item: item[0].as_posix().casefold()
            )
        ]
    )
    return payload, {
        "entries": len(files),
        "uncompressed_bytes": sum(len(value) for value in files.values()),
        "allowlist_manifest_sha256": sha256(allowlist_manifest),
        "archive_method": "ZIP_STORED",
    }


def notes_payload() -> bytes:
    return (
        "# STAT 415 — edisi Bahasa Indonesia: hingga Pelajaran 01\n\n"
        "Status: **sebagian; 3 dari 14 dokumen lengkap**. Paket ini memuat "
        "laman utama, seluruh Pelajaran 00, dan seluruh Pelajaran 01 dalam "
        "Bahasa Indonesia. Pelajaran 02–12 belum diterjemahkan dan tetap "
        "menaut ke sumber resmi berbahasa Inggris.\n\n"
        "Pembaca luring adalah berkas utama. Ekstrak ZIP pembaca dan buka "
        "`index.html` melalui peladen HTTP statis. Paket source-backend memuat "
        "otoritas beku, terjemahan, backend modular, skrip reproduksi, lisensi, "
        "dan bukti QA ringkas yang diperlukan untuk melanjutkan edisi. Batas "
        "ini mencakup 744 segmen terjemahan dan 500 permukaan matematika.\n\n"
        "Konten Penn State tetap CC BY-NC 4.0 kecuali dinyatakan lain; MathJax "
        "3.1.2 tetap Apache-2.0; lapisan asli repositori memiliki lisensi "
        "terpisah di bawah CC BY-SA 4.0. Lihat `LICENSE.md`. Koleksi ini tidak "
        "direlisensi secara seragam, dan tidak ada dukungan atau pengesahan "
        "oleh Penn State yang tersirat.\n\n"
        f"Provenans terjemahan: {PROVENANCE}. Seluruh kredit sumber dan "
        "kontributor manusia dipertahankan.\n\n"
        "Semantik inventaris: `50_RELEASE_MANIFEST.csv` mencakup enam aset "
        "substantif dan mengecualikan dirinya sendiri, `SHA256SUMS.txt`, serta "
        "root receipt untuk menghindari siklus hash. `SHA256SUMS.txt` mencakup "
        "keenam aset tersebut dan manifes, tetapi mengecualikan dirinya sendiri "
        "dan root receipt. `60_THROUGH_LESSON01_RELEASE_ROOT_RECEIPT.json` "
        "mengikat setiap aset unggahan lain dan hanya mengecualikan dirinya "
        "sendiri.\n"
    ).encode("utf-8")


def compute() -> tuple[dict[str, bytes], bytes]:
    source_snapshot = snapshot_source_files()
    validated = validate_receipts(source_snapshot)
    reader_zip, reader_info = reader_package(validated["manifest"])
    source_zip, source_info = source_package(source_snapshot)
    notes = notes_payload()

    payloads: dict[str, bytes] = {
        READER_ZIP: reader_zip,
        SOURCE_ZIP: source_zip,
        RELEASE_NOTES: notes,
        RELEASE_LICENSE: validated["license"],
        RELEASE_QA: validated["qa"],
        RELEASE_VISUAL_QA: validated["visual"],
    }
    roles = {
        READER_ZIP: "primary-offline-reader",
        SOURCE_ZIP: "resumable-source-backend",
        RELEASE_NOTES: "scope-status-rights-and-provenance",
        RELEASE_LICENSE: "component-rights",
        RELEASE_QA: "deterministic-qa",
        RELEASE_VISUAL_QA: "desktop-mobile-visual-qa",
    }

    manifest_output = io.StringIO(newline="")
    writer = csv.DictWriter(
        manifest_output,
        fieldnames=("filename", "bytes", "sha256", "role"),
        lineterminator="\n",
    )
    writer.writeheader()
    for filename, data in payloads.items():
        writer.writerow(
            {
                "filename": filename,
                "bytes": len(data),
                "sha256": sha256(data),
                "role": roles[filename],
            }
        )
    release_manifest = manifest_output.getvalue().encode("utf-8")
    payloads[RELEASE_MANIFEST] = release_manifest
    roles[RELEASE_MANIFEST] = "six-substantive-assets-manifest"
    payloads[CHECKSUMS] = "".join(
        f"{sha256(data)}  {filename}\n" for filename, data in payloads.items()
    ).encode("utf-8")
    roles[CHECKSUMS] = "sha256-for-substantive-assets-and-manifest"

    covered_by_root = list(payloads)
    root_receipt = canonical_json(
        {
            "schema": "o006.stat415.through-lesson01-release-root.v1",
            "status": "ready",
            "coverage": {
                "complete_count": 3,
                "complete_documents": COMPLETE_DOCUMENTS,
                "corpus_document_count": 14,
                "next_document": "Lesson02",
            },
            "self_exclusion": {
                "filename": ROOT_RECEIPT,
                "reason": "non-self-referential cryptographic root",
            },
            "inventory_semantics": {
                "release_manifest": {
                    "filename": RELEASE_MANIFEST,
                    "covers": list(payloads)[:6],
                    "excludes": [RELEASE_MANIFEST, CHECKSUMS, ROOT_RECEIPT],
                },
                "sha256sums": {
                    "filename": CHECKSUMS,
                    "covers": list(payloads)[:-1],
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
                    "sha256": sha256(payloads[filename]),
                    "role": roles[filename],
                }
                for filename in covered_by_root
            ],
            "file_count": len(covered_by_root),
            "total_bytes": sum(len(payloads[name]) for name in covered_by_root),
            "upload_order": covered_by_root,
        }
    )
    payloads[ROOT_RECEIPT] = root_receipt
    roles[ROOT_RECEIPT] = "non-self-referential-release-root"

    input_records = {
        "reader_manifest": validated["manifest"],
        "build_receipt": validated["build"],
        "qa_receipt": validated["qa"],
        "visual_qa_receipt": validated["visual"],
        "license": validated["license"],
    }
    receipt = {
        "schema": "o006.stat415.through-lesson01-package.v1",
        "status": "ready",
        "coverage": {
            "complete_count": 3,
            "complete_documents": COMPLETE_DOCUMENTS,
            "corpus_document_count": 14,
            "next_document": "Lesson02",
            "statement": "landing/index plus complete Lesson00 and Lesson01; 3 of 14 documents",
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
            name: {"bytes": len(data), "sha256": sha256(data)}
            for name, data in input_records.items()
        },
        "files": [
            {
                "filename": filename,
                "bytes": len(data),
                "sha256": sha256(data),
            }
            for filename, data in payloads.items()
        ],
        "file_count": len(payloads),
        "total_bytes": sum(len(data) for data in payloads.values()),
        "primary_file": READER_ZIP,
        "reader_zip": {"filename": READER_ZIP, **reader_info},
        "source_zip": {"filename": SOURCE_ZIP, **source_info},
        "inventory_semantics": {
            "release_manifest_excludes": [RELEASE_MANIFEST, CHECKSUMS, ROOT_RECEIPT],
            "sha256sums_excludes": [CHECKSUMS, ROOT_RECEIPT],
            "root_receipt_excludes": [ROOT_RECEIPT],
        },
        "upload_order": list(payloads),
    }
    return payloads, canonical_json(receipt)


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
            atomic_write(ROOT / relative, data)
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
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
