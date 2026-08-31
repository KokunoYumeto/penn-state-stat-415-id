#!/usr/bin/env python3
"""Direct anonymous byte readback for the public C140 companion C5 release.

The package receipt supplies the exact 65-file inventory.  The replayable main
readback receipt supplies the published commit, annotated-tag object and release
ID; the separate authenticated publication receipt proves paginated duplicate-
lineage closure.  No C5 hashes or remote identities are guessed.
This adapter never calls the GitHub API, reads credentials, invokes Git, or
launches a browser.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any

import verify_github_release_direct_c140_companion_c4 as engine


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
MAIN_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-31_C140_COMPANION_C5.json"
)
PUBLICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_PUBLICATION_2026-08-31_C140_COMPANION_C5.json"
)
CONTENT_RECEIPT = (
    ROOT / "00_control" / "GITHUB_CONTENT_READBACK_2026-08-31_C5_COMMIT.json"
)
OUTPUT_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_DIRECT_READBACK_2026-08-31_C140_COMPANION_C5.json"
)
PACKAGE_SCHEMA = "o006.c140.companion-c5-release-package.v1"
PACKAGE_VERSION = "2026.08.31.c140-companion-c5"
MAIN_SCHEMA = "o006.c140.companion-c5.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c5.github-release-publication.v1"
CONTENT_SCHEMA = "o006.c140.c5.github-content-readback.v1"
SCHEMA = "o006.c140.companion-c5.github-release-direct-readback.v1"
TAG = "v2026.08.31.c140-companion-c5"
EXPECTED_FILE_COUNT = 65
EXPECTED_INHERITED_FILES = 57
EXPECTED_NEW_FILES = 8
VERIFIED_ON = "2026-08-31"
MAX_AUTHORITY_BYTES = 64 * 1024 * 1024
MAX_PUBLICATION_BYTES = 500_000_000
MAX_PUBLIC_FILE_BYTES = 100_000_000
_FROZEN_PACKAGE: dict[str, Any] | None = None
_FROZEN_PACKAGE_PAYLOAD: bytes | None = None
_FROZEN_LINEAGE: dict[str, object] | None = None

def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def reparse(metadata: os.stat_result) -> bool:
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(int(getattr(metadata, "st_file_attributes", 0)) & flag)


def file_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        int(getattr(metadata, "st_file_attributes", 0)),
    )


def safe_repo_directory_chain(path: Path, label: str) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise engine.VerificationError(f"{label} lies outside the repository") from exc
    current = ROOT
    for candidate in (
        ROOT,
        *(ROOT / Path(*relative.parts[:index]) for index in range(1, len(relative.parts) + 1)),
    ):
        current = candidate
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise engine.VerificationError(f"{label} directory is unavailable") from exc
        if current.is_symlink() or not stat.S_ISDIR(metadata.st_mode) or reparse(metadata):
            raise engine.VerificationError(f"{label} crosses a symlink/reparse directory")


def safe_read_bytes(
    path: Path,
    label: str,
    *,
    expected_bytes: int | None = None,
    maximum_bytes: int = MAX_AUTHORITY_BYTES,
) -> bytes:
    """Read a regular non-reparse file without exposing its machine path."""
    safe_repo_directory_chain(path.parent, f"{label} parent")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise engine.VerificationError(f"{label} is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or reparse(metadata)
    ):
        raise engine.VerificationError(f"{label} is not a regular non-reparse file")
    if (
        metadata.st_size < 1
        or metadata.st_size > maximum_bytes
        or (expected_bytes is not None and metadata.st_size != expected_bytes)
    ):
        raise engine.VerificationError(f"{label} size is outside its admitted bound")
    read_limit = expected_bytes if expected_bytes is not None else maximum_bytes
    try:
        with path.open("rb") as handle:
            before_handle = os.fstat(handle.fileno())
            payload = handle.read(read_limit + 1)
            after_handle = os.fstat(handle.fileno())
        after_path = path.lstat()
    except OSError as exc:
        raise engine.VerificationError(f"{label} cannot be read") from exc
    safe_repo_directory_chain(path.parent, f"{label} parent")
    identities = {
        file_identity(metadata),
        file_identity(before_handle),
        file_identity(after_handle),
        file_identity(after_path),
    }
    if (
        len(identities) != 1
        or len(payload) != metadata.st_size
        or len(payload) > read_limit
        or path.is_symlink()
        or reparse(after_path)
    ):
        raise engine.VerificationError(f"{label} changed while being snapshotted")
    return payload


def read_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        payload = safe_read_bytes(path, label)
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise engine.VerificationError(f"{label} is unavailable or invalid") from exc
    if not isinstance(value, dict):
        raise engine.VerificationError(f"{label} is not a JSON object")
    return value, payload


def authorities() -> tuple[
    dict[str, Any], bytes, dict[str, Any], dict[str, object]
]:
    package, package_payload = read_object(PACKAGE_RECEIPT, "C5 package receipt")
    main, main_payload = read_object(MAIN_RECEIPT, "C5 GitHub main readback receipt")
    publication_auth, publication_auth_payload = read_object(
        PUBLICATION_RECEIPT, "C5 GitHub authenticated publication receipt"
    )
    content, content_payload = read_object(
        CONTENT_RECEIPT, "C5 committed-content readback receipt"
    )
    publication = package.get("publication_inventory")
    package_rows = publication.get("files") if isinstance(publication, dict) else None
    local_rows = main.get("local_inventory")
    public = main.get("public")
    public_rows = public.get("files") if isinstance(public, dict) else None
    annotated = public.get("annotated_tag") if isinstance(public, dict) else None
    preservation = package.get("preservation")
    embedded_package = main.get("package_receipt")
    embedded_content = main.get("committed_content_receipt")
    content_files = content.get("files")
    content_gate = content.get("c5_gate")
    content_build = (
        content_gate.get("build_receipt") if isinstance(content_gate, dict) else None
    )
    content_qa = (
        content_gate.get("qa_receipt") if isinstance(content_gate, dict) else None
    )
    package_gates = package.get("gates")
    publication_size_gate = (
        package_gates.get("publication_size")
        if isinstance(package_gates, dict)
        else None
    )
    input_receipts = (
        package_gates.get("input_receipts")
        if isinstance(package_gates, dict)
        else None
    )
    expected_build = (
        input_receipts.get("build/C5_BUILD_RECEIPT.json")
        if isinstance(input_receipts, dict)
        else None
    )
    expected_qa = (
        input_receipts.get("build/C5_QA_RECEIPT.json")
        if isinstance(input_receipts, dict)
        else None
    )
    content_manifest = content.get("commit_manifest")
    content_privacy = content.get("privacy_scan")
    content_release = content.get("release_snapshot")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != PACKAGE_VERSION
        or package.get("status") != "ready"
        or not isinstance(publication, dict)
        or publication.get("file_count") != EXPECTED_FILE_COUNT
        or not isinstance(publication.get("bytes"), int)
        or publication.get("bytes") <= 0
        or not isinstance(package_rows, list)
        or len(package_rows) != EXPECTED_FILE_COUNT
        or any(not isinstance(row, dict) for row in package_rows)
        or not isinstance(preservation, dict)
        or preservation.get("inherited_file_count") != EXPECTED_INHERITED_FILES
        or preservation.get("inherited_files_byte_identical") is not True
        or preservation.get("new_file_count") != EXPECTED_NEW_FILES
    ):
        raise engine.VerificationError("C5 package authority differs")
    if any(
        not isinstance(row.get("bytes"), int)
        or isinstance(row.get("bytes"), bool)
        or int(row["bytes"]) <= 0
        or int(row["bytes"]) > MAX_PUBLIC_FILE_BYTES
        for row in package_rows
    ):
        raise engine.VerificationError("C5 package contains an oversized or invalid file")
    package_sizes = [int(row["bytes"]) for row in package_rows]
    if (
        sum(package_sizes) != publication.get("bytes")
        or publication.get("bytes") > MAX_PUBLICATION_BYTES
        or publication_size_gate
        != {
            "bytes": publication.get("bytes"),
            "cap_bytes": MAX_PUBLICATION_BYTES,
            "file_cap_bytes": MAX_PUBLIC_FILE_BYTES,
            "maximum_file_bytes": max(package_sizes),
            "status": "pass",
        }
    ):
        raise engine.VerificationError("C5 package size gates differ")
    if (
        main.get("schema") != MAIN_SCHEMA
        or main.get("status") != "pass"
        or main.get("mode") != "public-byte-verification"
        or main.get("version") != PACKAGE_VERSION
        or main.get("tag") != TAG
        or main.get("local_files") != EXPECTED_FILE_COUNT
        or main.get("local_bytes") != publication.get("bytes")
        or main.get("prior_c4_files_preserved") != EXPECTED_INHERITED_FILES
        or main.get("companion_c5_additions") != EXPECTED_NEW_FILES
        or main.get("companion_c5_replacements") != 0
        or main.get("public_asset_readback_anonymous") is not True
        or main.get("control_plane_credential_access") is not False
        or main.get("credential_access") is not False
        or main.get("remote_writes") is not False
        or main.get("browser_processes_used") is not False
        or not isinstance(local_rows, list)
        or len(local_rows) != EXPECTED_FILE_COUNT
        or not isinstance(public, dict)
        or public.get("tag") != TAG
        or public.get("file_count") != EXPECTED_FILE_COUNT
        or public.get("total_bytes") != publication.get("bytes")
        or public.get("reader_first") is not True
        or public.get("public_asset_readback_anonymous") is not True
        or not isinstance(public_rows, list)
        or len(public_rows) != EXPECTED_FILE_COUNT
        or not isinstance(annotated, dict)
        or annotated.get("annotated") is not True
        or annotated.get("peeled_commit") != main.get("commit")
        or not isinstance(annotated.get("tag_object"), str)
        or len(str(annotated["tag_object"])) != 40
        or any(
            char not in "0123456789abcdef"
            for char in str(annotated["tag_object"])
        )
        or not isinstance(public.get("release_id"), int)
        or isinstance(public.get("release_id"), bool)
        or public.get("release_id") <= 0
        or not isinstance(embedded_package, dict)
        or embedded_package.get("path")
        != "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
        or embedded_package.get("bytes") != len(package_payload)
        or embedded_package.get("sha256") != sha256(package_payload)
    ):
        raise engine.VerificationError("C5 main GitHub receipt authority differs")
    publication_public = publication_auth.get("public")
    authenticated_inventory = (
        publication_public.get("authenticated_release_inventory")
        if isinstance(publication_public, dict)
        else None
    )
    if (
        publication_auth.get("schema") != PUBLICATION_SCHEMA
        or publication_auth.get("status") != "pass"
        or publication_auth.get("mode") not in {"publish", "publish-existing-exact"}
        or publication_auth.get("version") != PACKAGE_VERSION
        or publication_auth.get("tag") != TAG
        or publication_auth.get("commit") != main.get("commit")
        or publication_auth.get("credential_access") is not True
        or publication_auth.get("prior_release_untouched") is not True
        or publication_auth.get("local_files") != EXPECTED_FILE_COUNT
        or publication_auth.get("local_bytes") != publication.get("bytes")
        or not isinstance(publication_public, dict)
        or publication_public.get("release_id") != public.get("release_id")
        or publication_public.get("tag") != TAG
        or publication_public.get("file_count") != EXPECTED_FILE_COUNT
        or publication_public.get("total_bytes") != publication.get("bytes")
        or publication_public.get("files") != public_rows
        or publication_public.get("annotated_tag") != annotated
        or publication_public.get("reader_first") is not True
        or publication_public.get("public_asset_readback_anonymous") is not True
        or authenticated_inventory
        != {
            "release_id": public.get("release_id"),
            "exactly_one_target_release": True,
            "target_matches": 1,
            "duplicate_targets": 0,
            "lineage_matches": 1,
            "duplicate_lineages": 0,
            "server_termination_observed": True,
            "page_size": 100,
            "page_cap": 100,
            "visibility": "authenticated",
        }
    ):
        raise engine.VerificationError(
            "C5 authenticated publication/duplicate-lineage authority differs"
        )
    if (
        content.get("schema") != CONTENT_SCHEMA
        or content.get("status") != "pass"
        or content.get("commit") != main.get("commit")
        or content.get("commit") != annotated.get("peeled_commit")
        or not isinstance(content.get("parent"), str)
        or len(str(content["parent"])) != 40
        or any(char not in "0123456789abcdef" for char in str(content["parent"]))
        or content.get("all_match") is not True
        or content.get("credential_mode") != "none"
        or content.get("credentials_read") is not False
        or content.get("authorization_header_sent") is not False
        or content.get("browser_used") is not False
        or content.get("browser_processes_launched") is not False
        or not isinstance(content_files, list)
        or content.get("file_count") != len(content_files)
        or content.get("public_total_bytes") != content.get("total_bytes")
        or any(
            not isinstance(row, dict) or row.get("match") is not True
            for row in content_files
        )
        or not isinstance(content_gate, dict)
        or content_gate.get("authority")
        != "exact committed Git blobs at the verified C5 commit"
        or not isinstance(content_build, dict)
        or content_build.get("path")
        != "components/c140-companion/build/C5_BUILD_RECEIPT.json"
        or not isinstance(expected_build, dict)
        or any(
            content_build.get(key) != expected_build.get(key)
            for key in ("bytes", "sha256")
        )
        or not isinstance(content_qa, dict)
        or content_qa.get("path")
        != "components/c140-companion/build/C5_QA_RECEIPT.json"
        or not isinstance(expected_qa, dict)
        or any(
            content_qa.get(key) != expected_qa.get(key)
            for key in ("bytes", "sha256")
        )
        or content.get("changed_file_set_manifest_closed") is not True
        or not isinstance(content_manifest, dict)
        or content_manifest.get("changed_files_including_manifest")
        != len(content_files)
        or not isinstance(content_privacy, dict)
        or content_privacy.get("files_scanned") != len(content_files)
        or content_privacy.get("forbidden_markers_found") != 0
        or content_privacy.get("status") != "pass"
        or not isinstance(content_release, dict)
        or content_release.get("authority")
        != "exact cumulative release blobs in the verified C5 commit tree"
        or content_release.get("all_match") is not True
        or content_release.get("file_count") != EXPECTED_FILE_COUNT
        or content_release.get("bytes") != publication.get("bytes")
        or not isinstance(content_release.get("files"), list)
        or len(content_release["files"]) != EXPECTED_FILE_COUNT
        or not isinstance(embedded_content, dict)
        or embedded_content.get("path")
        != "00_control/GITHUB_CONTENT_READBACK_2026-08-31_C5_COMMIT.json"
        or embedded_content.get("bytes") != len(content_payload)
        or embedded_content.get("sha256") != sha256(content_payload)
        or embedded_content.get("schema") != CONTENT_SCHEMA
        or embedded_content.get("commit") != content.get("commit")
        or embedded_content.get("parent") != content.get("parent")
        or embedded_content.get("files") != content.get("file_count")
        or embedded_content.get("bytes_verified") != content.get("total_bytes")
        or embedded_content.get("aggregate_sha256")
        != content.get("aggregate_sha256")
        or embedded_content.get("all_match") is not True
    ):
        raise engine.VerificationError("C5 committed-content lineage authority differs")

    release_rows = content_release["files"]
    for index, (package_row, release_row) in enumerate(
        zip(package_rows, release_rows, strict=True), start=1
    ):
        if not isinstance(package_row, dict) or not isinstance(release_row, dict):
            raise engine.VerificationError(f"malformed C5 commit release row {index}")
        if (
            release_row.get("upload_order") != index
            or release_row.get("filename") != package_row.get("filename")
            or release_row.get("path") != package_row.get("source_path")
            or release_row.get("bytes") != package_row.get("bytes")
            or release_row.get("sha256") != package_row.get("sha256")
            or release_row.get("match") is not True
        ):
            raise engine.VerificationError(
                f"C5 tagged-commit release identity differs at row {index}"
            )
    release_aggregate = sha256(
        json.dumps(
            [
                {
                    "path": row["path"],
                    "bytes": row["bytes"],
                    "sha256": row["sha256"],
                }
                for row in release_rows
            ],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    if content_release.get("aggregate_sha256") != release_aggregate:
        raise engine.VerificationError("C5 tagged-commit release aggregate differs")

    for index, (package_row, local_row, public_row) in enumerate(
        zip(package_rows, local_rows, public_rows, strict=True), start=1
    ):
        if not all(isinstance(row, dict) for row in (package_row, local_row, public_row)):
            raise engine.VerificationError(f"malformed C5 authority row {index}")
        if (
            package_row.get("upload_order") != index
            or local_row.get("name") != package_row.get("filename")
            or local_row.get("bytes") != package_row.get("bytes")
            or local_row.get("sha256") != package_row.get("sha256")
            or local_row.get("role") != package_row.get("role")
            or local_row.get("lineage") != package_row.get("lineage")
            or public_row.get("name") != package_row.get("filename")
            or public_row.get("bytes") != package_row.get("bytes")
            or public_row.get("sha256") != package_row.get("sha256")
            or public_row.get("validated_download") is not True
            or public_row.get("http_status") != 200
            or public_row.get("automatic_redirects_followed") is not False
        ):
            raise engine.VerificationError(f"C5 authority inventories differ at row {index}")
    lineage = {
        "authenticated_publication": {
            "path": (
                "00_control/"
                "GITHUB_RELEASE_PUBLICATION_2026-08-31_C140_COMPANION_C5.json"
            ),
            "bytes": len(publication_auth_payload),
            "sha256": sha256(publication_auth_payload),
            "schema": PUBLICATION_SCHEMA,
            "commit": publication_auth["commit"],
            "release_id": publication_public["release_id"],
            "duplicate_lineages": 0,
        },
        "main_github_readback": {
            "path": "00_control/GITHUB_RELEASE_RECEIPT_2026-08-31_C140_COMPANION_C5.json",
            "bytes": len(main_payload),
            "sha256": sha256(main_payload),
            "schema": MAIN_SCHEMA,
            "commit": main["commit"],
        },
        "committed_content_readback": {
            "path": "00_control/GITHUB_CONTENT_READBACK_2026-08-31_C5_COMMIT.json",
            "bytes": len(content_payload),
            "sha256": sha256(content_payload),
            "schema": CONTENT_SCHEMA,
            "commit": content["commit"],
            "parent": content["parent"],
            "aggregate_sha256": content.get("aggregate_sha256"),
        },
    }
    return package, package_payload, main, lineage


def engine_read_package() -> tuple[dict[str, Any], bytes]:
    """Safe replacement for the inherited path-reporting package reader."""
    if _FROZEN_PACKAGE is None or _FROZEN_PACKAGE_PAYLOAD is None:
        raise engine.VerificationError("C5 package authority is not frozen")
    return dict(_FROZEN_PACKAGE), _FROZEN_PACKAGE_PAYLOAD


def adapted_build_receipt() -> dict[str, object]:
    package, package_payload = engine_read_package()
    expected = engine.expected_inventory(package)
    verified: list[dict[str, object] | None] = [None] * len(expected)
    with ThreadPoolExecutor(max_workers=engine.MAX_WORKERS) as pool:
        futures = {
            pool.submit(engine.verify_one, row): index
            for index, row in enumerate(expected)
        }
        try:
            for future in as_completed(futures):
                verified[futures[future]] = future.result()
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    if any(row is None for row in verified):
        raise engine.VerificationError(
            "public verification did not return every C5 inventory row"
        )
    files = [row for row in verified if row is not None]
    if (
        len(files) != engine.EXPECTED_FILE_COUNT
        or sum(int(row["bytes"]) for row in files) != engine.EXPECTED_BYTES
    ):
        raise engine.VerificationError("verified C5 public totals differ")
    script_payload = safe_read_bytes(Path(__file__), "C5 direct verifier source")
    if _FROZEN_LINEAGE is None:
        raise engine.VerificationError("C5 lineage authority is not frozen")
    return {
        "schema": SCHEMA,
        "status": "pass",
        "verified_on": VERIFIED_ON,
        "repository": engine.REPOSITORY,
        "release": {
            "release_id": engine.RELEASE_ID,
            "release_url": engine.RELEASE_URL,
            "tag": engine.TAG,
            "tag_object": engine.TAG_OBJECT,
            "commit": engine.COMMIT,
        },
        "expected_source": {
            "path": "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json",
            "schema": PACKAGE_SCHEMA,
            "version": PACKAGE_VERSION,
            "bytes": len(package_payload),
            "sha256": sha256(package_payload),
        },
        "lineage_authorities": dict(_FROZEN_LINEAGE),
        "verifier": {
            "path": "scripts/verify_github_release_direct_c140_companion_c5.py",
            "bytes": len(script_payload),
            "sha256": sha256(script_payload),
            "github_api_calls": 0,
            "credential_access": False,
            "credential_files_read": False,
            "authorization_headers_sent": False,
            "browser_processes_used": False,
            "browser_modules_used": False,
            "git_operations": False,
            "automatic_redirects_followed": False,
            "redirect_policy": (
                "direct HTTPS github.com release URL; at most one manually "
                "validated HTTPS handoff to an enumerated GitHub-owned asset CDN; "
                "no further redirect"
            ),
            "allowed_initial_host": engine.ALLOWED_INITIAL_HOST,
            "allowed_redirect_hosts": sorted(engine.ALLOWED_CDN_HOSTS),
            "requests_trust_environment": False,
            "worker_count": engine.MAX_WORKERS,
        },
        "public_readback": {
            "mode": "credential-free-direct-release-byte-readback",
            "file_count": len(files),
            "bytes": sum(int(row["bytes"]) for row in files),
            "all_bytes_and_sha256_match": True,
            "all_redirects_github_owned": True,
            "reader_first": files[0]["filename"]
            == "00_00_stat415-pengantar-statistika-matematis-id.pdf",
            "files": files,
        },
    }


def configure_engine() -> None:
    global _FROZEN_PACKAGE, _FROZEN_PACKAGE_PAYLOAD, _FROZEN_LINEAGE
    package, package_payload, main, lineage = authorities()
    _FROZEN_PACKAGE = package
    _FROZEN_PACKAGE_PAYLOAD = package_payload
    _FROZEN_LINEAGE = lineage
    publication = package["publication_inventory"]
    public = main["public"]
    annotated = public["annotated_tag"]
    commit = str(main["commit"])
    tag_object = str(annotated["tag_object"])
    if (
        len(commit) != 40
        or any(char not in "0123456789abcdef" for char in commit)
        or len(tag_object) != 40
        or any(char not in "0123456789abcdef" for char in tag_object)
    ):
        raise engine.VerificationError("C5 commit or tag-object identity is malformed")
    engine.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    engine.OUTPUT_RECEIPT = OUTPUT_RECEIPT
    engine.SCHEMA = SCHEMA
    engine.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    engine.PACKAGE_VERSION = PACKAGE_VERSION
    engine.TAG = TAG
    engine.COMMIT = commit
    engine.TAG_OBJECT = tag_object
    engine.RELEASE_ID = int(public["release_id"])
    engine.RELEASE_URL = f"{engine.REPOSITORY}/releases/tag/{TAG}"
    engine.EXPECTED_FILE_COUNT = EXPECTED_FILE_COUNT
    engine.EXPECTED_BYTES = int(publication["bytes"])
    engine.USER_AGENT = "O006-C140-C5-direct-release-readback/2026.08.31"
    engine.read_package = engine_read_package
    engine.build_receipt = adapted_build_receipt


def safe_atomic_write(path: Path, payload: bytes) -> None:
    """Atomically replace only a regular non-reparse receipt destination."""
    safe_repo_directory_chain(path.parent, "C5 direct-readback receipt destination")
    if path.exists() or path.is_symlink():
        safe_read_bytes(path, "C5 direct-readback receipt destination")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb",
            dir=path.parent,
            prefix=f".{path.name}.c5-",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if safe_read_bytes(
            temporary,
            "temporary C5 direct-readback receipt",
            expected_bytes=len(payload),
        ) != payload:
            raise engine.VerificationError("temporary C5 direct-readback receipt differs")
        safe_repo_directory_chain(
            path.parent, "C5 direct-readback receipt destination before replace"
        )
        if safe_read_bytes(
            temporary,
            "temporary C5 direct-readback receipt before replace",
            expected_bytes=len(payload),
        ) != payload:
            raise engine.VerificationError("temporary C5 direct-readback receipt changed")
        os.replace(temporary, path)
        temporary = None
        if safe_read_bytes(
            path,
            "written C5 direct-readback receipt",
            expected_bytes=len(payload),
        ) != payload:
            raise engine.VerificationError("written C5 direct-readback receipt differs")
    except OSError as exc:
        raise engine.VerificationError("C5 direct-readback receipt write failed") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise engine.VerificationError("C5 temporary receipt cleanup failed") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="verify and write receipt")
    mode.add_argument("--check", action="store_true", help="verify and replay receipt")
    args = parser.parse_args()
    configure_engine()
    receipt = adapted_build_receipt()
    payload = engine.canonical_json(receipt)
    if args.write:
        safe_atomic_write(OUTPUT_RECEIPT, payload)
        action = "wrote"
    else:
        existing = safe_read_bytes(
            OUTPUT_RECEIPT,
            "C5 direct-readback receipt",
            expected_bytes=len(payload),
        )
        if existing != payload:
            raise engine.VerificationError("existing C5 direct-readback receipt differs")
        action = "checked"
    print(
        json.dumps(
            {
                "status": "pass",
                "action": action,
                "receipt": (
                    "00_control/"
                    "GITHUB_RELEASE_DIRECT_READBACK_2026-08-31_C140_COMPANION_C5.json"
                ),
                "receipt_bytes": len(payload),
                "receipt_sha256": sha256(payload),
                "files": engine.EXPECTED_FILE_COUNT,
                "bytes": engine.EXPECTED_BYTES,
                "api_calls": 0,
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
        print(
            f"ERROR: C5 GitHub direct-release verifier failed closed "
            f"[{type(exc).__name__}]",
            file=sys.stderr,
        )
        raise SystemExit(1)
