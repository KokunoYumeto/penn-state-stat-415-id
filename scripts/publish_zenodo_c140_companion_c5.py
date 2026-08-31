#!/usr/bin/env python3
"""Publish the cumulative C140 original-companion C5 Zenodo boundary.

The adapter creates a new public version only from anonymously verified record
22164344 in the existing concept 22077422.  Its 57 files are inherited without
replacement and exactly eight C5 files are appended.  All C5 byte counts and
SHA-256 values are derived from the frozen C5 package receipt; this publisher
contains no guessed C5 artifact identity.

``--contract-only`` is local, credential-free, network-free, browser-free, and
side-effect free.  It never reads the credential file.  The underlying hardened
engine provides owned-draft recovery, exact-union validation, publication,
anonymous full-byte readback, and an authenticated zero-draft lineage audit.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import package_c140_companion_c5_release as packager
import publish_zenodo_c140_companion_c4 as c4pub


engine = c4pub.engine
ROOT = Path(__file__).resolve().parents[1]

BASE_RECORD_ID = "22164344"
BASE_RECORD_DOI = "10.5281/zenodo.22164344"
BASE_VERSION = "2026.08.29.c140-companion-c4"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
VERSION = "2026.08.31.c140-companion-c5"
TITLE = (
    "O006/C140 Statistika Matematis — STAT 415, Random, dan Pendamping "
    "Orisinal Lengkap C5 (Bahasa Indonesia)"
)
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
PUBLICATION_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-31_C140_COMPANION_C5.json"
)
READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-31_C140_COMPANION_C5.json"
)
BASE_READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_BASE_READBACK_2026-08-31_C140_COMPANION_C5.json"
)
AUDIT_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-31_C140_COMPANION_C5.json"
)
DRAFT_MARKER = (
    ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-31_C140_COMPANION_C5.json"
)
LINEAGE_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_2026-08-31_C140_COMPANION_C5.json"
)

PACKAGE_SCHEMA = "o006.c140.companion-c5-release-package.v1"
PUBLICATION_SCHEMA = "o006.c140.zenodo-c140-companion-c5-publication.v1"
MARKER_SCHEMA = "o006.c140.zenodo-c140-companion-c5-draft-marker.v1"
LINEAGE_SCHEMA = "o006.c140.zenodo-c140-companion-c5-lineage.v1"
BASE_READBACK_SCHEMA = "o006.c140.zenodo-base-readback-c140-companion-c5.v1"
USER_AGENT = "O006-C140-companion-c5/2026.08.31"
MAX_RELEASE_BYTES = 500_000_000
MAX_PUBLIC_FILE_BYTES = 100_000_000
LINEAGE_PAGE_SIZE = 25
MAX_LINEAGE_PAGES = 100

BASE_FILE_COUNT = 57
BASE_TOTAL_BYTES = 93_850_993
ADDED_NAMES = (
    "06_C140_COMPANION_C5_OFFLINE_READER.zip",
    "16_C140_COMPANION_C5_SOURCE_BACKEND_DATA_RIGHTS.zip",
    "26_C140_COMPANION_C5_RELEASE_NOTES.md",
    "36_C140_COMPANION_C5_COMPONENT_AND_DATASET_LICENSES.md",
    "46_C140_COMPANION_C5_STATIC_QA_EVIDENCE.zip",
    "98_C140_COMPANION_C5_FULL_UNION_MANIFEST.csv",
    "SHA256SUMS_C140_COMPANION_C5.txt",
    "99_C140_COMPANION_C5_FULL_UNION_ROOT_RECEIPT.json",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_reparse(st: os.stat_result) -> bool:
    return bool(getattr(st, "st_file_attributes", 0) & 0x400)


def safe_external_directory_chain(path: Path, label: str) -> None:
    """Reject symlink/reparse traversal in the fixed external credential path."""

    absolute = path.absolute()
    candidates = list(reversed(absolute.parents))
    for candidate in candidates:
        try:
            metadata = candidate.lstat()
        except OSError as exc:
            raise RuntimeError(f"{label} directory chain is unavailable") from exc
        if (
            candidate.is_symlink()
            or not stat.S_ISDIR(metadata.st_mode)
            or _is_reparse(metadata)
        ):
            raise RuntimeError(f"{label} crosses a symlink/reparse directory")


def safe_read_token() -> str:
    """Read exactly one bounded token from the pinned regular credential file."""
    safe_external_directory_chain(TOKEN_FILE, "Zenodo credential source")
    try:
        before = TOKEN_FILE.lstat()
    except OSError as exc:
        raise RuntimeError("Zenodo credential source is unavailable") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or TOKEN_FILE.is_symlink()
        or _is_reparse(before)
        or before.st_size <= 0
        or before.st_size > 65_536
    ):
        raise RuntimeError("Zenodo credential source is not an admitted regular file")
    try:
        with TOKEN_FILE.open("rb") as stream:
            opened_before = os.fstat(stream.fileno())
            payload = stream.read(65_537)
            opened_after = os.fstat(stream.fileno())
        after = TOKEN_FILE.lstat()
    except OSError as exc:
        raise RuntimeError("Zenodo credential source could not be read safely") from exc
    safe_external_directory_chain(TOKEN_FILE, "Zenodo credential source")
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    opened_identity_before = (
        opened_before.st_dev,
        opened_before.st_ino,
        opened_before.st_size,
        opened_before.st_mtime_ns,
    )
    opened_identity_after = (
        opened_after.st_dev,
        opened_after.st_ino,
        opened_after.st_size,
        opened_after.st_mtime_ns,
    )
    if (
        identity_before != identity_after
        or identity_before != opened_identity_before
        or opened_identity_before != opened_identity_after
        or not stat.S_ISREG(after.st_mode)
        or TOKEN_FILE.is_symlink()
        or _is_reparse(after)
        or len(payload) != before.st_size
    ):
        raise RuntimeError("Zenodo credential source changed during the bounded read")
    try:
        raw = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Zenodo credential source is not valid UTF-8") from exc
    candidates = sorted(set(re.findall(r"(?<![A-Za-z0-9._~-])[A-Za-z0-9._~-]{40,4096}(?![A-Za-z0-9._~-])", raw)))
    if len(candidates) != 1:
        raise RuntimeError("Zenodo credential source must contain exactly one token value")
    return candidates[0]


def safe_bounded_repo_read(path: Path, expected_size: int, label: str) -> bytes:
    """Read one handle-bound exact file through a non-reparse repository chain."""
    if expected_size < 0 or expected_size > MAX_RELEASE_BYTES:
        raise RuntimeError(f"{label} has an inadmissible declared size")
    packager.assert_bounded_nonreparse(path, label=label)
    try:
        before = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} is unavailable") from exc
    if (
        not stat.S_ISREG(before.st_mode)
        or path.is_symlink()
        or packager.is_reparse(path)
        or before.st_size != expected_size
    ):
        raise RuntimeError(f"{label} is not the admitted regular file")
    try:
        with path.open("rb") as stream:
            opened_before = os.fstat(stream.fileno())
            payload = stream.read(expected_size + 1)
            opened_after = os.fstat(stream.fileno())
        after = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} could not be read safely") from exc
    before_id = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_id = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    opened_before_id = (
        opened_before.st_dev,
        opened_before.st_ino,
        opened_before.st_size,
        opened_before.st_mtime_ns,
    )
    opened_after_id = (
        opened_after.st_dev,
        opened_after.st_ino,
        opened_after.st_size,
        opened_after.st_mtime_ns,
    )
    packager.assert_bounded_nonreparse(path, label=label)
    if (
        before_id != after_id
        or before_id != opened_before_id
        or opened_before_id != opened_after_id
        or len(payload) != expected_size
        or not stat.S_ISREG(after.st_mode)
        or path.is_symlink()
        or packager.is_reparse(path)
    ):
        raise RuntimeError(f"{label} changed during the bounded read")
    return payload


def safe_atomic_repo_write(path: Path, payload: bytes, label: str) -> None:
    """Atomically write, then re-open and prove the exact stable repository file."""
    if not payload or len(payload) > MAX_RELEASE_BYTES:
        raise RuntimeError(f"{label} exceeds the admitted byte cap")
    packager.assert_bounded_nonreparse(path, label=label)
    if path.exists() or path.is_symlink():
        try:
            current = path.lstat()
        except OSError as exc:
            raise RuntimeError(f"{label} destination cannot be inspected") from exc
        if (
            not stat.S_ISREG(current.st_mode)
            or path.is_symlink()
            or packager.is_reparse(path)
        ):
            raise RuntimeError(f"{label} destination is not a regular file")
        safe_bounded_repo_read(path, int(current.st_size), label)
    packager.assert_bounded_nonreparse(path.parent, label=f"{label} directory")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb",
            dir=path.parent,
            prefix=f".{path.name}.c5-",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if safe_bounded_repo_read(
            temporary, len(payload), f"temporary {label}"
        ) != payload:
            raise RuntimeError(f"temporary {label} bytes differ")
        packager.assert_bounded_nonreparse(path.parent, label=f"{label} directory")
        if safe_bounded_repo_read(
            temporary, len(payload), f"temporary {label} before replace"
        ) != payload:
            raise RuntimeError(f"temporary {label} changed")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    if safe_bounded_repo_read(path, len(payload), label) != payload:
        raise RuntimeError(f"{label} post-write bytes differ")


def validate_token_boundary() -> None:
    """Pin credential handling without reading or serializing the credential."""
    if engine.TOKEN_FILE != TOKEN_FILE:
        # The shared engine is not configured until publication mode starts;
        # only its compiled default is admitted before that point.
        default = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
        if engine.TOKEN_FILE != default:
            raise RuntimeError("hardened engine token-file boundary differs")
    required_hooks = (
        "read_token",
        "assert_receipt_safe",
        "owned_new_version",
        "validate_inherited_and_partial_additions",
        "upload_missing_additions",
        "exact_complete_draft",
        "anonymous_readback",
        "authenticated_zero_draft_audit",
    )
    if any(not callable(getattr(engine, name, None)) for name in required_hooks):
        raise RuntimeError("hardened engine credential/sanitization hooks are absent")
    engine.assert_receipt_safe(
        {
            "credential_access": False,
            "credential_value_persisted": False,
            "token_file_path_persisted": False,
        }
    )
    try:
        engine.assert_receipt_safe({"forbidden_path": TOKEN_FILE.as_posix()})
    except RuntimeError:
        pass
    else:
        raise RuntimeError("hardened receipt sanitizer accepted the token-file path")


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-31",
        "description": (
            "Rilis kumulatif lengkap O006/C140 Bahasa Indonesia (id-ID). Versi "
            "ini mewarisi byte demi byte seluruh 57 berkas publik versi "
            "2026.08.29.c140-companion-c4, lalu menambahkan tepat delapan "
            "berkas C5. Pendamping orisinal lengkap mencakup D001–D013, "
            "SIM001–SIM006, set penguasaan MS00–MS12, asesmen kumulatif "
            "CA01–CA04, serta capstone CP01–CP02 dengan data, analisis, kunci, "
            "rubrik, artefak statis yang dapat diakses, backend ber-ID stabil, "
            "dan bukti replay deterministik. Bersama tulang punggung Penn State "
            "STAT 415 dan donor kelengkapan Random, C140 lengkap pada batas "
            "komponen yang diterima. Hak komponen tidak diseragamkan: Penn "
            "State tetap CC BY-NC 4.0 kecuali dinyatakan lain; halaman Random "
            "mempertahankan saksi CC BY 2.0 pada laman utama dan tautan CC BY "
            "1.0 pada Credits; pendamping orisinal adalah CC BY-SA 4.0; data "
            "CP01 tetap CC BY 4.0 (SPDX: CC-BY-4.0); data CP02 tetap CC0 1.0 "
            "(SPDX: CC0-1.0); dan MathJax tetap "
            "Apache-2.0. Metadata agregat karena itu memakai other-open; "
            "berkas hak per komponen dan per dataset tetap mengikat. Provenans "
            f"produksi pendamping dan rekayasa edisi: {MODEL_PROVENANCE}. "
            "Seluruh kredit sumber dan kontributor manusia dipertahankan; "
            "tidak ada dukungan Penn State, Kyle Siegrist, atau penyedia data "
            "yang tersirat."
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
            "statistical inference",
            "likelihood asymptotics",
            "Bayesian frequentist comparison",
            "multiple linear regression",
            "reproducible simulation",
            "mastery assessment",
            "capstone",
            "Penn State STAT 415",
            "Random",
            "open educational resources",
            "offline HTML",
            "PDF",
            "EPUB",
            "machine-readable curriculum",
            "AI translation",
            "component-separated licensing",
            "CC BY-NC 4.0",
            "CC BY-SA 4.0",
            "CC BY 4.0",
            "CC0 1.0",
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


def validate_metadata_boundary() -> None:
    value = metadata()
    description = value.get("description")
    required_rights = (
        "CC BY-NC 4.0",
        "CC BY 2.0",
        "CC BY 1.0",
        "CC BY-SA 4.0",
        "CC BY 4.0",
        "CC0 1.0",
        "Apache-2.0",
    )
    if (
        value.get("version") != VERSION
        or value.get("access_right") != "open"
        or value.get("license") != "other-open"
        or value.get("language") != "ind"
        or not isinstance(description, str)
        or "C140 lengkap pada batas" not in description
        or any(right not in description for right in required_rights)
    ):
        raise RuntimeError("C5 public metadata/license boundary differs")
    engine.assert_receipt_safe(value)


def computed_contract() -> tuple[
    dict[str, bytes],
    bytes,
    dict[str, Any],
    list[dict[str, Any]],
    tuple[tuple[str, int, str], ...],
    tuple[tuple[str, int, str], ...],
]:
    """Return the frozen package and derive every C5 identity from its receipt."""
    validate_token_boundary()
    validate_metadata_boundary()
    outputs, receipt_payload = packager.compute()
    try:
        package = json.loads(receipt_payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("computed C5 package receipt is not UTF-8 JSON") from exc
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    coverage = package.get("coverage")
    lineage = package.get("lineage")
    preservation = package.get("preservation")
    reader_order = package.get("reader_order")
    rights = package.get("rights")
    packager_gate = package.get("packager")
    base = package.get("base_public_union")
    c5_gate = package.get("gates", {}).get("c5_boundary")
    publication_size_gate = package.get("gates", {}).get("publication_size")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != VERSION
        or package.get("status") != "ready"
        or not isinstance(publication, dict)
        or not isinstance(rows, list)
        or not all(isinstance(row, dict) for row in rows)
        or publication.get("file_count") != BASE_FILE_COUNT + len(ADDED_NAMES)
        or len(rows) != BASE_FILE_COUNT + len(ADDED_NAMES)
        or publication.get("bytes") != sum(int(row.get("bytes", -1)) for row in rows)
        or tuple(str(row.get("filename")) for row in rows[BASE_FILE_COUNT:])
        != ADDED_NAMES
        or coverage
        != {
            "c140_course": "complete on admitted boundary",
            "c140_original_companion": "C5 complete checkpoint",
            "c5_batch": "complete",
            "penn_state_spine": "complete",
            "random_completeness_donor": "complete",
            "remaining": "none within admitted C140 boundary",
        }
        or lineage
        != {
            "base_record_doi": BASE_RECORD_DOI,
            "base_record_id": BASE_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "concept_record_id": CONCEPT_RECORD_ID,
            "create_competing_concept": False,
        }
        or preservation
        != {
            "inherited_files_byte_identical": True,
            "inherited_file_count": BASE_FILE_COUNT,
            "new_file_count": len(ADDED_NAMES),
            "new_substantive_file_count": 5,
        }
        or reader_order
        != {
            "inherited_union_first": True,
            "pdf_upload_order": 1,
            "epub_upload_order": 2,
            "c5_first_upload_order": BASE_FILE_COUNT + 1,
        }
        or not isinstance(rights, dict)
        or rights.get("aggregate_uniform_relicense") is not False
        or rights.get("component_licenses_unchanged") is not True
        or rights.get("cp01_dataset_license") != "CC-BY-4.0"
        or rights.get("cp02_dataset_license") != "CC0-1.0"
        or rights.get("platform_license") != "other-open"
        or not isinstance(packager_gate, dict)
        or packager_gate.get("browser_processes_used") is not False
        or packager_gate.get("credential_access") is not False
        or packager_gate.get("git_operations") is not False
        or packager_gate.get("network_access") is not False
        or packager_gate.get("publication_side_effects") is not False
        or not isinstance(c5_gate, dict)
        or c5_gate.get("status") != "pass"
        or c5_gate.get("documents") != 39
        or c5_gate.get("problems") != 146
        or c5_gate.get("assessments") != 4
        or c5_gate.get("capstones") != 2
        or publication_size_gate
        != {
            "bytes": publication.get("bytes") if isinstance(publication, dict) else None,
            "cap_bytes": MAX_RELEASE_BYTES,
            "file_cap_bytes": MAX_PUBLIC_FILE_BYTES,
            "maximum_file_bytes": max(int(row.get("bytes", -1)) for row in rows),
            "status": "pass",
        }
        or not isinstance(base, dict)
        or base.get("record_id") != BASE_RECORD_ID
        or base.get("record_doi") != BASE_RECORD_DOI
        or base.get("version") != BASE_VERSION
        or base.get("concept_record_id") != CONCEPT_RECORD_ID
        or base.get("concept_doi") != CONCEPT_DOI
        or base.get("file_count") != BASE_FILE_COUNT
        or base.get("bytes") != BASE_TOTAL_BYTES
        or base.get("anonymous_readback") is not True
        or base.get("package_receipt")
        != {
            "bytes": packager.BASE_PACKAGE_RECEIPT_BYTES,
            "sha256": packager.BASE_PACKAGE_RECEIPT_SHA256,
        }
        or base.get("public_readback")
        != {
            "bytes": packager.BASE_PUBLIC_READBACK_BYTES,
            "sha256": packager.BASE_PUBLIC_READBACK_SHA256,
        }
    ):
        raise RuntimeError("computed C5 package is not the admitted Zenodo boundary")

    base_outputs, base_rows, base_evidence = packager.validate_base_public_union()
    readback = base_evidence.get("public_readback_json")
    public = readback.get("public") if isinstance(readback, dict) else None
    if (
        set(base_outputs) != {str(row.get("filename")) for row in base_rows}
        or not isinstance(public, dict)
        or public.get("record_id") != BASE_RECORD_ID
        or public.get("doi") != BASE_RECORD_DOI
        or public.get("concept_record_id") != CONCEPT_RECORD_ID
        or public.get("concept_doi") != CONCEPT_DOI
        or public.get("version") != BASE_VERSION
        or public.get("anonymous_readback") is not True
        or public.get("file_count") != BASE_FILE_COUNT
        or public.get("total_bytes") != BASE_TOTAL_BYTES
    ):
        raise RuntimeError("pinned public C4 base differs")
    base_specs = tuple(
        (str(row["filename"]), int(row["bytes"]), str(row["sha256"]))
        for row in base_rows
    )

    names: set[str] = set()
    paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        name = row.get("filename")
        relative = engine.canonical_relative(row.get("source_path"), f"C5 package row {index} path")
        size, digest = engine.checked_identity(row, f"C5 package row {index}")
        payload = outputs.get(str(name))
        if (
            row.get("upload_order") != index + 1
            or not isinstance(name, str)
            or not engine._SAFE_NAME.fullmatch(name)
            or engine._SENSITIVE_NAME.search(name)
            or relative != f"release/{name}"
            or row.get("primary_reader") is not (index == 0)
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or not isinstance(row.get("lineage"), str)
            or not row.get("lineage")
            or not isinstance(row.get("media_type"), str)
            or "/" not in str(row.get("media_type"))
            or size > MAX_PUBLIC_FILE_BYTES
            or name in names
            or relative in paths
            or payload is None
            or (len(payload), sha256(payload)) != (size, digest)
        ):
            raise RuntimeError(f"C5 package row {index} has an unsafe identity")
        names.add(name)
        paths.add(relative)
        total += size
    expected_order = tuple(name for name, _size, _digest in base_specs) + ADDED_NAMES
    if (
        total != publication.get("bytes")
        or total > MAX_RELEASE_BYTES
        or tuple(outputs) != expected_order
        or tuple(str(row.get("filename")) for row in rows) != expected_order
    ):
        raise RuntimeError("C5 package aggregate/order differs")

    for index, expected in enumerate(base_specs):
        row = rows[index]
        actual = (row.get("filename"), row.get("bytes"), row.get("sha256"))
        if actual != expected:
            raise RuntimeError(f"C5 package changed inherited base asset: {expected[0]}")
    added_specs = tuple(
        (str(row["filename"]), int(row["bytes"]), str(row["sha256"]))
        for row in rows[BASE_FILE_COUNT:]
    )
    if tuple(name for name, _size, _digest in added_specs) != ADDED_NAMES:
        raise RuntimeError("C5 addition names/order differ")
    if (
        rows[0].get("filename") != "00_00_stat415-pengantar-statistika-matematis-id.pdf"
        or rows[0].get("media_type") != "application/pdf"
        or rows[1].get("filename") != "00_01_stat415-pengantar-statistika-matematis-id.epub"
        or rows[1].get("media_type") != "application/epub+zip"
    ):
        raise RuntimeError("C5 union is not reader-first")
    return outputs, receipt_payload, package, rows, base_specs, added_specs


def snapshot() -> engine.ReleaseSnapshot:
    outputs, receipt_payload, package, rows, base_specs, added_specs = computed_contract()
    if safe_bounded_repo_read(
        PACKAGE_RECEIPT, len(receipt_payload), "C5 package receipt"
    ) != receipt_payload:
        raise RuntimeError("written C5 package receipt differs; run packager --write")
    artifacts: list[engine.Artifact] = []
    total = 0
    for index, row in enumerate(rows):
        name = str(row["filename"])
        relative = engine.canonical_relative(row.get("source_path"), f"C5 package row {index} path")
        size, digest = engine.checked_identity(row, f"C5 package row {index}")
        payload = safe_bounded_repo_read(
            ROOT / relative, size, f"C5 release asset {index + 1}"
        )
        if payload != outputs[name] or (len(payload), sha256(payload)) != (size, digest):
            raise RuntimeError(f"C5 release asset differs: {name}")
        artifacts.append(engine.Artifact(name, relative, size, digest, payload))
        total += size
    if total != sum(item.bytes for item in artifacts) or total > MAX_RELEASE_BYTES:
        raise RuntimeError("C5 release aggregate byte count differs")
    inherited = tuple(artifacts[:BASE_FILE_COUNT])
    additions = tuple(artifacts[BASE_FILE_COUNT:])
    if (
        tuple((item.name, item.bytes, item.sha256) for item in inherited) != base_specs
        or tuple((item.name, item.bytes, item.sha256) for item in additions) != added_specs
    ):
        raise RuntimeError("C5 inherited/addition partition differs")
    return engine.ReleaseSnapshot(
        package=package,
        receipt_bytes=len(receipt_payload),
        receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited=inherited,
        additions=additions,
    )


def c5_download_exact(
    session: engine.requests.Session,
    record: dict[str, Any],
    expected: tuple[engine.Artifact, ...],
) -> list[dict[str, object]]:
    """Hash the exact public Zenodo union with per-file streaming bounds."""

    rows = record.get("files")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise RuntimeError("public Zenodo file inventory is malformed")
    names = [str(row.get("key")) for row in rows]
    expected_names = [item.name for item in expected]
    if len(names) != len(set(names)) or set(names) != set(expected_names):
        raise RuntimeError("public Zenodo file inventory is not exact")
    by_name = dict(zip(names, rows, strict=True))
    verified: list[dict[str, object]] = []
    for item in expected:
        if item.bytes <= 0 or item.bytes > MAX_PUBLIC_FILE_BYTES:
            raise RuntimeError(f"public Zenodo file exceeds its cap: {item.name}")
        row = by_name[item.name]
        if row.get("size") != item.bytes:
            raise RuntimeError(f"public Zenodo metadata size differs: {item.name}")
        links = row.get("links") if isinstance(row.get("links"), dict) else {}
        initial_url = engine.zenodo_url(
            links.get("content") or links.get("self"),
            f"public Zenodo file {item.name}",
            ("/api/records/", "/api/files/", "/records/"),
        )
        response = session.get(
            initial_url,
            stream=True,
            timeout=900,
            allow_redirects=False,
        )
        final = response
        try:
            sent = {key.casefold() for key in response.request.headers}
            if sent.intersection({"authorization", "cookie", "proxy-authorization"}):
                raise RuntimeError("credential-bearing header appeared in Zenodo readback")
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("Location")
                target_url = urljoin(initial_url, str(location or ""))
                target = urlparse(target_url)
                if (
                    target.scheme.casefold() != "https"
                    or (target.hostname or "").casefold() != "zenodo.org"
                    or target.port not in (None, 443)
                    or target.username
                    or target.password
                    or target.fragment
                    or not any(
                        target.path.startswith(prefix)
                        for prefix in ("/api/records/", "/api/files/", "/records/")
                    )
                    or parse_qs(target.query, keep_blank_values=True)
                    not in ({}, {"download": ["1"]})
                ):
                    raise RuntimeError("public Zenodo file redirect is not admitted")
                response.close()
                final = session.get(
                    target_url,
                    stream=True,
                    timeout=900,
                    allow_redirects=False,
                )
                sent = {key.casefold() for key in final.request.headers}
                if sent.intersection({"authorization", "cookie", "proxy-authorization"}):
                    raise RuntimeError(
                        "credential-bearing header appeared after Zenodo redirect"
                    )
            if final.status_code != 200 or final.is_redirect or final.is_permanent_redirect:
                raise RuntimeError(f"public Zenodo file did not resolve exactly: {item.name}")
            declared = final.headers.get("Content-Length")
            if declared is not None and (
                not declared.isdecimal() or int(declared) != item.bytes
            ):
                raise RuntimeError(f"public Zenodo Content-Length differs: {item.name}")
            digest = hashlib.sha256()
            total = 0
            for chunk in final.iter_content(1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > item.bytes:
                    raise RuntimeError(f"public Zenodo file exceeds expected bytes: {item.name}")
                digest.update(chunk)
            if (total, digest.hexdigest()) != (item.bytes, item.sha256):
                raise RuntimeError(f"public Zenodo file differs: {item.name}")
            verified.append(
                {"name": item.name, "bytes": total, "sha256": digest.hexdigest()}
            )
        finally:
            final.close()
            if final is not response:
                response.close()
    return verified


def verify_base_record(
    session: engine.requests.Session, snap: engine.ReleaseSnapshot
) -> dict[str, object]:
    record = engine.public_record(session, BASE_RECORD_ID)
    metadata_value = record.get("metadata")
    if (
        not isinstance(metadata_value, dict)
        or metadata_value.get("version") != BASE_VERSION
        or str(record.get("doi")) != BASE_RECORD_DOI
    ):
        raise RuntimeError("public C4 base record identity differs")
    verified = engine.download_exact(session, record, snap.inherited)
    result = {
        "record_id": BASE_RECORD_ID,
        "doi": BASE_RECORD_DOI,
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "version": BASE_VERSION,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "package_receipt": {
            "bytes": packager.BASE_PACKAGE_RECEIPT_BYTES,
            "sha256": packager.BASE_PACKAGE_RECEIPT_SHA256,
        },
        "prior_public_readback": {
            "bytes": packager.BASE_PUBLIC_READBACK_BYTES,
            "sha256": packager.BASE_PUBLIC_READBACK_SHA256,
        },
        "anonymous_readback": True,
        "environment_proxy_trust": False,
    }
    if result["file_count"] != BASE_FILE_COUNT or result["total_bytes"] != BASE_TOTAL_BYTES:
        raise RuntimeError("public C4 base byte census differs")
    engine.atomic_json(
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
    engine.atomic_json(
        READBACK_RECEIPT,
        {
            **base,
            "mode": "verify-published",
            "credential_access": False,
            "environment_proxy_trust": False,
            "public": public,
        },
    )
    engine.atomic_json(
        PUBLICATION_RECEIPT,
        {
            **base,
            "mode": mode,
            "credential_access": mode != "verify-published",
            "public": public,
            **extra,
        },
    )
    engine.atomic_json(
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


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt_payload, package, rows, base_specs, added_specs = computed_contract()
    return {
        "appended_files": len(added_specs),
        "base_package_receipt_sha256": packager.BASE_PACKAGE_RECEIPT_SHA256,
        "base_public_readback_sha256": packager.BASE_PUBLIC_READBACK_SHA256,
        "base_record_id": BASE_RECORD_ID,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "concept_record_id": CONCEPT_RECORD_ID,
        "credential_access": False,
        "credential_value_persisted": False,
        "files": len(rows),
        "inherited_files": len(base_specs),
        "mode": "contract-only",
        "network_access": False,
        "package_receipt_bytes": len(receipt_payload),
        "package_receipt_sha256": sha256(receipt_payload),
        "publication_side_effects": False,
        "reader_first": True,
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "token_file_accessed": False,
        "token_file_path_persisted": False,
        "version": VERSION,
    }


def safe_atomic_json(path: Path, value: dict[str, object]) -> None:
    """Persist a sanitized receipt through the C5 non-reparse atomic writer."""
    engine.assert_receipt_safe(value)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    safe_atomic_repo_write(path, payload, "C5 Zenodo receipt output")


def safe_marker_value(snap: engine.ReleaseSnapshot) -> dict[str, Any] | None:
    """Read only the exact regular C5 transaction marker, if it exists."""

    packager.assert_bounded_nonreparse(DRAFT_MARKER, label="C5 Zenodo draft marker")
    try:
        info = DRAFT_MARKER.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise RuntimeError("C5 Zenodo draft marker cannot be inspected") from exc
    if (
        not stat.S_ISREG(info.st_mode)
        or DRAFT_MARKER.is_symlink()
        or _is_reparse(info)
        or info.st_size <= 0
        or info.st_size > 1_048_576
    ):
        raise RuntimeError("C5 Zenodo draft marker is not an admitted regular file")
    payload = safe_bounded_repo_read(
        DRAFT_MARKER, int(info.st_size), "C5 Zenodo draft marker"
    )
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("C5 Zenodo draft marker is not valid UTF-8 JSON") from exc
    if (
        not isinstance(value, dict)
        or value.get("schema") != MARKER_SCHEMA
        or value.get("status") not in ("created", "owned")
        or value.get("concept_record_id") != CONCEPT_RECORD_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("base_record_id") != BASE_RECORD_ID
        or value.get("base_version") != BASE_VERSION
        or value.get("target_version") != VERSION
        or value.get("package_receipt_sha256") != snap.receipt_sha256
        or re.fullmatch(r"[1-9][0-9]*", str(value.get("draft_id", ""))) is None
    ):
        raise RuntimeError("C5 Zenodo draft marker is not the admitted transaction")
    return value


def safe_write_marker(
    draft_id: str, status: str, snap: engine.ReleaseSnapshot
) -> None:
    if (
        re.fullmatch(r"[1-9][0-9]*", draft_id) is None
        or draft_id in (BASE_RECORD_ID, CONCEPT_RECORD_ID)
        or status not in ("created", "owned")
    ):
        raise RuntimeError("cannot write an invalid C5 Zenodo draft marker")
    safe_atomic_json(
        DRAFT_MARKER,
        {
            "schema": MARKER_SCHEMA,
            "status": status,
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "base_record_id": BASE_RECORD_ID,
            "base_version": BASE_VERSION,
            "target_version": VERSION,
            "package_receipt_sha256": snap.receipt_sha256,
            "draft_id": draft_id,
        },
    )


def safe_remove_marker(expected_id: str, snap: engine.ReleaseSnapshot) -> None:
    marker = safe_marker_value(snap)
    if marker is None:
        return
    if str(marker["draft_id"]) != expected_id:
        raise RuntimeError("refusing to remove a marker for a different Zenodo draft")
    # Re-snapshot immediately before removing this exact repository path.
    current = safe_marker_value(snap)
    if current != marker:
        raise RuntimeError("C5 Zenodo draft marker changed before removal")
    try:
        DRAFT_MARKER.unlink()
    except OSError as exc:
        raise RuntimeError("C5 Zenodo draft marker removal failed") from exc
    if DRAFT_MARKER.exists() or DRAFT_MARKER.is_symlink():
        raise RuntimeError("C5 Zenodo draft marker remains after removal")


def c5_authenticated_zero_draft_audit(
    authenticated: engine.requests.Session,
    public: dict[str, object],
    base: dict[str, object],
) -> None:
    """Re-prove newest unique public C5 lineage after byte readback, then drafts."""
    public_session = engine.anonymous_session("post-readback-lineage")
    try:
        versions = engine.public_versions(public_session)
    finally:
        public_session.close()
    targets = [
        row
        for row in versions
        if isinstance(row.get("metadata"), dict)
        and row["metadata"].get("version") == VERSION
    ]
    if len(targets) != 1:
        raise RuntimeError("public C5 version is absent or duplicated after readback")
    newest = (
        max(versions, key=lambda row: int(str(row.get("id", "0"))))
        if versions
        else None
    )
    target_id = str(targets[0].get("id", ""))
    if (
        newest is None
        or target_id != str(public.get("record_id", ""))
        or str(newest.get("id", "")) != target_id
    ):
        raise RuntimeError("public C5 version is not the unique newest concept record")
    drafts = engine.authenticated_drafts(authenticated)
    if drafts:
        raise RuntimeError("an unpublished draft remains in the admitted Zenodo concept")
    safe_atomic_json(
        AUDIT_RECEIPT,
        {
            **base,
            "mode": "audit-lineage",
            "credential_access": True,
            "submitted_matching_versions": 1,
            "target_is_newest_public_version": True,
            "target_record_id": target_id,
            "unsubmitted_concept_drafts": 0,
            "public": public,
        },
    )


def c5_public_versions(session: engine.requests.Session) -> list[dict[str, Any]]:
    """Enumerate the complete public concept lineage with a hard page bound."""

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, MAX_LINEAGE_PAGES + 1):
        response = engine.check(
            session.get(
                engine.RECORDS,
                params={
                    "q": f"conceptrecid:{CONCEPT_RECORD_ID}",
                    "all_versions": "true",
                    "size": LINEAGE_PAGE_SIZE,
                    "page": page,
                },
                timeout=120,
            ),
            (200,),
            "list complete public C5 Zenodo concept lineage",
        )
        value = response.json()
        hits = value.get("hits") if isinstance(value, dict) else None
        batch = hits.get("hits") if isinstance(hits, dict) else None
        if (
            not isinstance(batch, list)
            or len(batch) > LINEAGE_PAGE_SIZE
            or any(not isinstance(row, dict) for row in batch)
        ):
            raise RuntimeError("public C5 Zenodo lineage page is malformed")
        for row in batch:
            record_id = str(row.get("id", ""))
            if not record_id.isdigit() or record_id in seen:
                raise RuntimeError("public C5 Zenodo lineage has an invalid/duplicate id")
            seen.add(record_id)
            if engine.concept_identity(row) != (CONCEPT_RECORD_ID, CONCEPT_DOI):
                raise RuntimeError("public C5 Zenodo lineage escaped its concept")
            rows.append(row)
        if len(batch) < LINEAGE_PAGE_SIZE:
            return rows
    raise RuntimeError("public C5 Zenodo lineage exceeded its page cap")


def c5_authenticated_drafts(
    session: engine.requests.Session,
) -> list[dict[str, Any]]:
    """Enumerate all concept depositions and return every unpublished draft."""

    drafts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, MAX_LINEAGE_PAGES + 1):
        response = engine.check(
            session.get(
                engine.DEPOSITIONS,
                params={
                    "q": f"conceptrecid:{CONCEPT_RECORD_ID}",
                    "all_versions": "true",
                    "size": LINEAGE_PAGE_SIZE,
                    "page": page,
                },
                timeout=120,
            ),
            (200,),
            "list complete authenticated C5 Zenodo concept lineage",
        )
        batch = response.json()
        if (
            not isinstance(batch, list)
            or len(batch) > LINEAGE_PAGE_SIZE
            or any(not isinstance(row, dict) for row in batch)
        ):
            raise RuntimeError("authenticated C5 Zenodo lineage page is malformed")
        for row in batch:
            deposition_id = str(row.get("id", ""))
            if not deposition_id.isdigit() or deposition_id in seen:
                raise RuntimeError(
                    "authenticated C5 Zenodo lineage has an invalid/duplicate id"
                )
            seen.add(deposition_id)
            concept_id, concept_doi = engine.concept_identity(row)
            if concept_id != CONCEPT_RECORD_ID or (
                concept_doi and concept_doi != CONCEPT_DOI
            ):
                raise RuntimeError("authenticated C5 Zenodo lineage escaped its concept")
            if not bool(row.get("submitted")):
                drafts.append(row)
        if len(batch) < LINEAGE_PAGE_SIZE:
            return drafts
    raise RuntimeError("authenticated C5 Zenodo lineage exceeded its page cap")


def configure_engine() -> None:
    # Freeze one byte-exact local snapshot for the complete publication
    # transaction.  The engine must not recompute or reread a moving package
    # between configuration, upload validation, and publication.
    snap = snapshot()
    base_specs = tuple(
        (item.name, item.bytes, item.sha256) for item in snap.inherited
    )
    added_specs = tuple(
        (item.name, item.bytes, item.sha256) for item in snap.additions
    )
    expected_order = tuple(item.name for item in snap.files)
    engine.BASE_RECORD_ID = BASE_RECORD_ID
    engine.BASE_VERSION = BASE_VERSION
    engine.CONCEPT_RECORD_ID = CONCEPT_RECORD_ID
    engine.CONCEPT_DOI = CONCEPT_DOI
    engine.VERSION = VERSION
    engine.NEW_VERSION_URL = f"{engine.DEPOSITIONS}/{BASE_RECORD_ID}/actions/newversion"
    engine.TITLE = TITLE
    engine.MODEL_PROVENANCE = MODEL_PROVENANCE
    engine.TOKEN_FILE = TOKEN_FILE
    engine.read_token = safe_read_token
    engine.atomic_json = safe_atomic_json
    engine.marker_value = safe_marker_value
    engine.write_marker = safe_write_marker
    engine.remove_marker = safe_remove_marker
    engine.download_exact = c5_download_exact
    engine.public_versions = c5_public_versions
    engine.authenticated_drafts = c5_authenticated_drafts
    engine.authenticated_zero_draft_audit = c5_authenticated_zero_draft_audit
    engine.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    engine.PUBLICATION_RECEIPT = PUBLICATION_RECEIPT
    engine.READBACK_RECEIPT = READBACK_RECEIPT
    engine.BASE_READBACK_RECEIPT = BASE_READBACK_RECEIPT
    engine.AUDIT_RECEIPT = AUDIT_RECEIPT
    engine.DRAFT_MARKER = DRAFT_MARKER
    engine.LINEAGE_RECEIPT = LINEAGE_RECEIPT
    engine.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    engine.PUBLICATION_SCHEMA = PUBLICATION_SCHEMA
    engine.MARKER_SCHEMA = MARKER_SCHEMA
    engine.USER_AGENT = USER_AGENT
    engine.MAX_RELEASE_BYTES = MAX_RELEASE_BYTES
    engine.BASE_SPECS = base_specs
    engine.ADDED_NAMES = tuple(name for name, _size, _digest in added_specs)
    engine.EXPECTED_ORDER = expected_order
    engine.snapshot = lambda: snap
    engine.metadata = metadata
    engine.verify_base_record = verify_base_record
    engine.write_public_receipts = write_public_receipts


def main() -> None:
    if sys.argv[1:] == ["--contract-only"]:
        print(json.dumps(local_contract_summary(), sort_keys=True))
        return
    configure_engine()
    engine.main()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(
            f"Zenodo C5 operation failed ({type(exc).__name__}).",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
