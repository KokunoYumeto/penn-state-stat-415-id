#!/usr/bin/env python3
"""Paced, credential-free direct readback of the public C140 C5 Zenodo record.

``--write --record-id ID`` fetches one successful public-record metadata
document and downloads all 65 files sequentially over HTTPS.  Transient
failures and HTTP 429 responses use the bounded, Retry-After-aware policy of
the independently exercised C4 verifier.  No credential, environment proxy,
browser, Git operation, or Zenodo deposition endpoint is used.

``--check`` is network-free.  The published record identity is recovered from
the existing receipt and every expected filename, byte count, and SHA-256 is
re-derived from the frozen C5 package receipt.  The publication publisher,
separately, performs the authenticated zero-draft lineage audit.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

import package_c140_companion_c5_release as packager
import publish_zenodo_c140_companion_c5 as publisher
import verify_zenodo_direct_c140_companion_c4 as shared


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
OUTPUT_RECEIPT = (
    ROOT / "00_control" / "ZENODO_DIRECT_READBACK_2026-08-31_C140_COMPANION_C5.json"
)
PUBLICATION_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-31_C140_COMPANION_C5.json"
)
AUDIT_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-31_C140_COMPANION_C5.json"
)

SCHEMA = "o006.c140.companion-c5.zenodo-direct-readback.v1"
PACKAGE_SCHEMA = "o006.c140.companion-c5-release-package.v1"
VERSION = "2026.08.31.c140-companion-c5"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
BASE_FILE_COUNT = 57
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
EXPECTED_FILE_COUNT = BASE_FILE_COUNT + len(ADDED_NAMES)
MAX_PUBLICATION_BYTES = 500_000_000
MAX_PUBLIC_FILE_BYTES = 100_000_000
MAX_LOCAL_RECEIPT_BYTES = 16 * 1024 * 1024
USER_AGENT = "O006-C140-C5-Zenodo-direct-readback/2026.08.31"
_SHARED_VALIDATE_METADATA = shared.validate_metadata
PACKAGE_RECEIPT_RELATIVE = "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
OUTPUT_RECEIPT_RELATIVE = (
    "00_control/ZENODO_DIRECT_READBACK_2026-08-31_C140_COMPANION_C5.json"
)
_WINDOWS_REPARSE_POINT = 0x0400


class VerificationError(RuntimeError):
    """A fail-closed package, metadata, or public-byte verification error."""


def canonical_json(value: object) -> bytes:
    return shared.canonical_json(value)


def sha256_bytes(payload: bytes) -> str:
    return shared.sha256_bytes(payload)


def safe_error_message(value: object) -> str:
    """Remove local absolute user paths from every user-visible error."""
    message = str(value)
    replacements = (
        (str(PACKAGE_RECEIPT), PACKAGE_RECEIPT_RELATIVE),
        (PACKAGE_RECEIPT.as_posix(), PACKAGE_RECEIPT_RELATIVE),
        (str(OUTPUT_RECEIPT), OUTPUT_RECEIPT_RELATIVE),
        (OUTPUT_RECEIPT.as_posix(), OUTPUT_RECEIPT_RELATIVE),
        (str(ROOT), "."),
        (ROOT.as_posix(), "."),
        (str(Path.home()), "<user-home>"),
        (Path.home().as_posix(), "<user-home>"),
    )
    for absolute, replacement in replacements:
        message = message.replace(absolute, replacement)
    # Defense in depth for exceptions produced by imported transport code.
    message = re.sub(
        r"(?i)[a-z]:[\\/]users[\\/][^\\/\s:]+(?:[\\/][^\r\n]*)?",
        "<local-path>",
        message,
    )
    return message


def require_regular_receipt(
    path: Path, label: str, *, allow_absent: bool = False
) -> os.stat_result | None:
    """Reject any escape/reparse from repository root through the final node."""
    try:
        packager.assert_bounded_nonreparse(path, label=label)
    except (OSError, RuntimeError) as exc:
        raise VerificationError(safe_error_message(exc)) from exc
    try:
        info = os.lstat(path)
    except FileNotFoundError as exc:
        if allow_absent:
            return None
        raise VerificationError(f"missing {label}") from exc
    except OSError as exc:
        raise VerificationError(f"cannot inspect {label}") from exc
    attributes = int(getattr(info, "st_file_attributes", 0))
    if stat.S_ISLNK(info.st_mode) or attributes & _WINDOWS_REPARSE_POINT:
        raise VerificationError(f"{label} is a symlink or reparse point")
    if not stat.S_ISREG(info.st_mode):
        raise VerificationError(f"{label} is not a regular file")
    try:
        packager.assert_bounded_nonreparse(path, label=label)
    except (OSError, RuntimeError) as exc:
        raise VerificationError(safe_error_message(exc)) from exc
    return info


def read_bounded_receipt(
    path: Path, label: str, *, expected_size: int | None = None
) -> bytes:
    """Read a receipt with capped, handle/path-bound pre/post identity checks."""
    info = require_regular_receipt(path, label)
    if info is None:
        raise VerificationError(f"missing {label}")
    size = int(info.st_size)
    if (
        size <= 0
        or size > MAX_LOCAL_RECEIPT_BYTES
        or (expected_size is not None and size != expected_size)
    ):
        raise VerificationError(f"{label} has an inadmissible byte size")
    try:
        return publisher.safe_bounded_repo_read(path, size, label)
    except (OSError, RuntimeError) as exc:
        raise VerificationError(safe_error_message(exc)) from exc


def safe_atomic_receipt(path: Path, payload: bytes, label: str) -> None:
    """Use the C5 repository-confined atomic writer and exact post-read gate."""
    if not payload or len(payload) > MAX_LOCAL_RECEIPT_BYTES:
        raise VerificationError(f"{label} has an inadmissible byte size")
    try:
        publisher.safe_atomic_repo_write(path, payload, label)
    except (OSError, RuntimeError) as exc:
        raise VerificationError(safe_error_message(exc)) from exc
    if read_bounded_receipt(path, label, expected_size=len(payload)) != payload:
        raise VerificationError(f"{label} post-write bytes differ")


class SafeReceiptPath:
    """Minimal path facade forcing shared receipt checks through the safe reader."""

    def __init__(self, path: Path, label: str, display: str) -> None:
        self._path = path
        self._label = label
        self._display = display

    def read_bytes(self) -> bytes:
        return read_bounded_receipt(self._path, self._label)

    def __str__(self) -> str:
        return self._display


def read_package() -> tuple[dict[str, Any], bytes]:
    payload = read_bounded_receipt(PACKAGE_RECEIPT, "C5 package receipt")
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("package receipt is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict) or canonical_json(value) != payload:
        raise VerificationError("package receipt is not canonical JSON")
    return value, payload


def read_canonical_receipt(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    payload = read_bounded_receipt(path, label)
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict) or canonical_json(value) != payload:
        raise VerificationError(f"{label} is not canonical JSON")
    return value, payload


def publication_lineage_authority(
    record_id: str, expected_bytes: int, package_payload: bytes
) -> dict[str, object]:
    """Bind direct bytes to the authenticated unique/newest/zero-draft audit."""

    publication, publication_payload = read_canonical_receipt(
        PUBLICATION_RECEIPT, "C5 Zenodo publication receipt"
    )
    audit, audit_payload = read_canonical_receipt(
        AUDIT_RECEIPT, "C5 Zenodo lineage-audit receipt"
    )
    publication_public = publication.get("public")
    audit_public = audit.get("public")
    expected_package = {
        "path": "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json",
        "bytes": len(package_payload),
        "sha256": sha256_bytes(package_payload),
    }
    common = {
        "schema": publisher.PUBLICATION_SCHEMA,
        "version": VERSION,
        "required_base_record_id": "22164344",
        "required_base_version": "2026.08.29.c140-companion-c4",
        "required_concept_record_id": CONCEPT_RECORD_ID,
        "required_concept_doi": CONCEPT_DOI,
        "local_files": EXPECTED_FILE_COUNT,
        "local_bytes": expected_bytes,
        "inherited_files": BASE_FILE_COUNT,
        "appended_files": len(ADDED_NAMES),
        "inherited_files_untouched": True,
        "package_receipt": expected_package,
    }
    for label, receipt in (("publication", publication), ("audit", audit)):
        if any(receipt.get(key) != value for key, value in common.items()):
            raise VerificationError(f"C5 Zenodo {label} authority differs")
    expected_public = {
        "record_id": record_id,
        "doi": f"10.5281/zenodo.{record_id}",
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "version": VERSION,
        "file_count": EXPECTED_FILE_COUNT,
        "total_bytes": expected_bytes,
        "anonymous_readback": True,
    }
    if (
        publication.get("mode") not in {"publish", "already-published"}
        or publication.get("credential_access") is not True
        or publication.get("unsubmitted_concept_drafts") != 0
        or audit.get("mode") != "audit-lineage"
        or audit.get("credential_access") is not True
        or audit.get("submitted_matching_versions") != 1
        or audit.get("target_is_newest_public_version") is not True
        or str(audit.get("target_record_id")) != record_id
        or audit.get("unsubmitted_concept_drafts") != 0
        or not isinstance(publication_public, dict)
        or not isinstance(audit_public, dict)
        or publication_public != audit_public
        or any(publication_public.get(key) != value for key, value in expected_public.items())
    ):
        raise VerificationError("C5 Zenodo publication/lineage closure differs")
    return {
        "publication_receipt": {
            "path": "00_control/ZENODO_PUBLICATION_RECEIPT_2026-08-31_C140_COMPANION_C5.json",
            "bytes": len(publication_payload),
            "sha256": sha256_bytes(publication_payload),
        },
        "lineage_audit_receipt": {
            "path": "00_control/ZENODO_LINEAGE_AUDIT_2026-08-31_C140_COMPANION_C5.json",
            "bytes": len(audit_payload),
            "sha256": sha256_bytes(audit_payload),
        },
        "record_id": record_id,
        "unique_target_version": True,
        "target_is_newest_public_version": True,
        "unsubmitted_concept_drafts": 0,
    }


def expected_inventory(package: dict[str, Any]) -> list[dict[str, object]]:
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != VERSION
        or package.get("status") != "ready"
    ):
        raise VerificationError("package receipt identity/status differs")
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if not isinstance(rows, list) or len(rows) != EXPECTED_FILE_COUNT:
        raise VerificationError("package publication inventory is not the 65-file union")
    declared_bytes = publication.get("bytes") if isinstance(publication, dict) else None
    if (
        not isinstance(declared_bytes, int)
        or isinstance(declared_bytes, bool)
        or declared_bytes <= 0
        or declared_bytes > MAX_PUBLICATION_BYTES
    ):
        raise VerificationError("package publication byte total exceeds the admitted cap")
    if tuple(str(row.get("filename")) for row in rows[BASE_FILE_COUNT:] if isinstance(row, dict)) != ADDED_NAMES:
        raise VerificationError("package C5 additions are not the exact admitted eight")

    lineage = package.get("lineage")
    preservation = package.get("preservation")
    rights = package.get("rights")
    gates = package.get("gates")
    publication_size_gate = (
        gates.get("publication_size") if isinstance(gates, dict) else None
    )
    if (
        lineage
        != {
            "base_record_doi": "10.5281/zenodo.22164344",
            "base_record_id": "22164344",
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
        or not isinstance(rights, dict)
        or rights.get("aggregate_uniform_relicense") is not False
        or rights.get("component_licenses_unchanged") is not True
        or rights.get("cp01_dataset_license") != "CC-BY-4.0"
        or rights.get("cp02_dataset_license") != "CC0-1.0"
        or rights.get("platform_license") != "other-open"
    ):
        raise VerificationError("package lineage/preservation/rights boundary differs")

    admitted: list[dict[str, object]] = []
    names: set[str] = set()
    byte_total = 0
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise VerificationError(f"package inventory row {index} is not an object")
        name = row.get("filename")
        size = row.get("bytes")
        digest = row.get("sha256")
        if (
            not isinstance(name, str)
            or shared.SAFE_NAME_RE.fullmatch(name) is None
            or "/" in name
            or "\\" in name
            or name in names
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size <= 0
            or size > MAX_PUBLIC_FILE_BYTES
            or not isinstance(digest, str)
            or shared.SHA256_RE.fullmatch(digest) is None
            or row.get("source_path") != f"release/{name}"
            or row.get("upload_order") != index
            or row.get("primary_reader") is not (index == 1)
        ):
            raise VerificationError(f"package inventory row {index} is not admitted")
        names.add(name)
        byte_total += size
        if byte_total > MAX_PUBLICATION_BYTES:
            raise VerificationError("package inventory exceeds the 500,000,000-byte cap")
        admitted.append(
            {
                "upload_order": index,
                "filename": name,
                "bytes": size,
                "sha256": digest,
            }
        )
    if (
        publication.get("file_count") != EXPECTED_FILE_COUNT
        or publication.get("bytes") != byte_total
        or admitted[0]["filename"] != "00_00_stat415-pengantar-statistika-matematis-id.pdf"
        or admitted[1]["filename"] != "00_01_stat415-pengantar-statistika-matematis-id.epub"
    ):
        raise VerificationError("package inventory totals/reader order differ")
    if publication_size_gate != {
        "bytes": byte_total,
        "cap_bytes": MAX_PUBLICATION_BYTES,
        "file_cap_bytes": MAX_PUBLIC_FILE_BYTES,
        "maximum_file_bytes": max(int(row["bytes"]) for row in admitted),
        "status": "pass",
    }:
        raise VerificationError("package publication-size gate differs")

    try:
        _base_outputs, base_rows, base_readback = packager.validate_base_public_union()
    except (OSError, RuntimeError) as exc:
        raise VerificationError(safe_error_message(exc)) from exc
    public = base_readback.get("public")
    if (
        not isinstance(public, dict)
        or public.get("record_id") != "22164344"
        or public.get("doi") != "10.5281/zenodo.22164344"
        or public.get("concept_record_id") != CONCEPT_RECORD_ID
        or public.get("concept_doi") != CONCEPT_DOI
        or public.get("anonymous_readback") is not True
        or len(base_rows) != BASE_FILE_COUNT
    ):
        raise VerificationError("pinned C4 public-base evidence differs")
    for index, base_row in enumerate(base_rows):
        wanted = admitted[index]
        if (
            wanted["filename"],
            wanted["bytes"],
            wanted["sha256"],
        ) != (
            base_row.get("filename"),
            base_row.get("bytes"),
            base_row.get("sha256"),
        ):
            raise VerificationError(
                f"C5 receipt changed inherited C4 asset: {wanted['filename']}"
            )
    return admitted


def validate_public_metadata(
    record: dict[str, Any], expected: list[dict[str, object]]
) -> tuple[dict[str, dict[str, Any]], dict[str, object]]:
    """Add an exact C5 rights/provenance check to the shared transport gate."""
    by_name, access = _SHARED_VALIDATE_METADATA(record, expected)
    actual = record.get("metadata")
    wanted = publisher.metadata()
    if not isinstance(actual, dict):
        raise shared.VerificationError("public record lacks metadata")
    for key in ("title", "publication_date", "description", "language", "version"):
        if actual.get(key) != wanted[key]:
            raise shared.VerificationError(f"public C5 metadata differs: {key}")
    licence = actual.get("license")
    if not isinstance(licence, dict) or licence.get("id") != "other-open":
        raise shared.VerificationError("public C5 license metadata is not other-open")
    actual_creators = [
        str(row.get("name"))
        for row in actual.get("creators", [])
        if isinstance(row, dict)
    ]
    wanted_creators = [
        str(row.get("name"))
        for row in wanted["creators"]
        if isinstance(row, dict)
    ]
    if (
        actual_creators != wanted_creators
        or set(actual.get("keywords") or []) != set(wanted["keywords"])
        or actual.get("related_identifiers") != wanted["related_identifiers"]
    ):
        raise shared.VerificationError("public C5 creator/keyword/relation metadata differs")
    return by_name, access


def configure_shared(
    record_id: str,
    expected_bytes: int,
    package: dict[str, Any],
    package_payload: bytes,
    expected: list[dict[str, object]],
) -> None:
    """Configure the hardened C4 transport for this C5 immutable contract."""
    if re.fullmatch(r"[1-9][0-9]*", record_id) is None:
        raise VerificationError("record id must be a positive decimal integer")
    shared.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    shared.OUTPUT_RECEIPT = SafeReceiptPath(
        OUTPUT_RECEIPT,
        "C5 direct-readback receipt",
        OUTPUT_RECEIPT_RELATIVE,
    )
    shared.SCHEMA = SCHEMA
    shared.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    shared.VERSION = VERSION
    shared.RECORD_ID = record_id
    shared.RECORD_DOI = f"10.5281/zenodo.{record_id}"
    shared.CONCEPT_RECORD_ID = CONCEPT_RECORD_ID
    shared.CONCEPT_DOI = CONCEPT_DOI
    shared.RECORD_API_URL = f"https://zenodo.org/api/records/{record_id}"
    shared.RECORD_PUBLIC_URL = f"https://zenodo.org/records/{record_id}"
    shared.EXPECTED_FILE_COUNT = EXPECTED_FILE_COUNT
    shared.EXPECTED_BYTES = expected_bytes
    shared.USER_AGENT = USER_AGENT
    shared.validate_metadata = validate_public_metadata
    # Freeze the package expectation for the entire readback transaction.
    # This removes a package-receipt reread/TOCTOU gap in the shared transport.
    shared.read_package = lambda: (package, package_payload)
    shared.expected_inventory = lambda _package: expected
    # The shared verifier intentionally hashes its own module path.  Pointing
    # that module-global at this adapter makes the receipt attest the C5 script
    # actually invoked, while retaining the already hardened transport code.
    shared.__file__ = str(Path(__file__).resolve())


def receipt_record_id() -> str:
    try:
        value = json.loads(
            read_bounded_receipt(OUTPUT_RECEIPT, "C5 direct-readback receipt")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("direct-readback receipt is not UTF-8 JSON") from exc
    record = value.get("record") if isinstance(value, dict) else None
    record_id = str(record.get("record_id", "")) if isinstance(record, dict) else ""
    if re.fullmatch(r"[1-9][0-9]*", record_id) is None:
        raise VerificationError("direct-readback receipt lacks a valid record id")
    return record_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="perform public readback and write receipt")
    mode.add_argument("--check", action="store_true", help="network-free receipt check")
    parser.add_argument("--record-id", help="new public Zenodo record id; required with --write")
    args = parser.parse_args(argv)

    package, package_payload = read_package()
    expected = expected_inventory(package)
    expected_bytes = sum(int(row["bytes"]) for row in expected)
    if args.write:
        if args.record_id is None:
            parser.error("--write requires --record-id")
        record_id = args.record_id
        require_regular_receipt(
            OUTPUT_RECEIPT,
            "C5 direct-readback receipt destination",
            allow_absent=True,
        )
    else:
        if args.record_id is not None:
            parser.error("--record-id is valid only with --write")
        record_id = receipt_record_id()
    configure_shared(record_id, expected_bytes, package, package_payload, expected)
    lineage_authority = publication_lineage_authority(
        record_id, expected_bytes, package_payload
    )

    try:
        if args.write:
            receipt = shared.build_receipt()
            receipt["verified_on"] = "2026-08-31"
            receipt["expected_source"]["path"] = (
                "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
            )
            receipt["verifier"]["path"] = (
                "scripts/verify_zenodo_direct_c140_companion_c5.py"
            )
            receipt["publication_lineage_authority"] = lineage_authority
            current_package = read_bounded_receipt(
                PACKAGE_RECEIPT,
                "C5 package receipt",
                expected_size=len(package_payload),
            )
            if current_package != package_payload:
                raise VerificationError("C5 package receipt changed during public readback")
            payload = canonical_json(receipt)
            safe_atomic_receipt(
                OUTPUT_RECEIPT, payload, "C5 direct-readback receipt"
            )
            action = "wrote"
        else:
            payload, receipt = shared.check_local_receipt()
            if (
                receipt.get("verified_on") != "2026-08-31"
                or receipt.get("expected_source", {}).get("path")
                != "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
                or receipt.get("verifier", {}).get("path")
                != "scripts/verify_zenodo_direct_c140_companion_c5.py"
                or receipt.get("publication_lineage_authority") != lineage_authority
            ):
                raise VerificationError("C5 direct-readback receipt attribution differs")
            action = "checked-locally-without-network"
    except shared.VerificationError as exc:
        raise VerificationError(safe_error_message(exc)) from exc
    except (OSError, RuntimeError, ValueError) as exc:
        raise VerificationError(safe_error_message(exc)) from exc

    print(
        json.dumps(
            {
                "status": "pass",
                "action": action,
                "record_id": record_id,
                "receipt": OUTPUT_RECEIPT_RELATIVE,
                "receipt_bytes": len(payload),
                "receipt_sha256": sha256_bytes(payload),
                "package_receipt_bytes": len(package_payload),
                "package_receipt_sha256": sha256_bytes(package_payload),
                "files": EXPECTED_FILE_COUNT,
                "bytes": expected_bytes,
                "credential_access": False,
                "browser_processes_used": False,
                "git_operations": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {safe_error_message(exc)}", file=sys.stderr)
        raise SystemExit(1)
