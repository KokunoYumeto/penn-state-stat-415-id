#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative C140 companion C5 release.

The adapter pins the already verified 57-asset C4 release and admits exactly
eight additional C5 assets.  All C5 asset names, byte counts and SHA-256
digests come from the deterministic C5 packager and its written receipt; this
script contains no guessed C5 artifact identities.

``--contract-only`` is local, credential-free, network-free, Git-free and
browser-free.  The remaining modes reuse the hardened GitHub transaction
engine and always perform credential-free public-byte readback.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath
import stat
import sys
import tempfile
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import package_c140_companion_c5_release as packager
import publish_verify_github_c140_companion_c4 as c4pub


engine = c4pub.engine
_ENGINE_ANONYMOUS_READBACK = engine.anonymous_readback
ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "c140-companion"
PACKAGE_RELATIVE = "build/C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / PACKAGE_RELATIVE
TOKEN_FILE = Path.home() / "Downloads" / "Github Tokens.md"
PRIOR_RECEIPT_RELATIVE = (
    "00_control/GITHUB_RELEASE_RECEIPT_2026-08-29_C140_COMPANION_C4.json"
)
CONTENT_RECEIPT_RELATIVE = (
    "00_control/GITHUB_CONTENT_READBACK_2026-08-31_C5_COMMIT.json"
)
BUILD_RELATIVE = "components/c140-companion/build/C5_BUILD_RECEIPT.json"
QA_RELATIVE = "components/c140-companion/build/C5_QA_RECEIPT.json"
VERIFICATION_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-31_C140_COMPANION_C5.json"
)
PUBLICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_PUBLICATION_2026-08-31_C140_COMPANION_C5.json"
)

PACKAGE_SCHEMA = "o006.c140.companion-c5-release-package.v1"
PACKAGE_VERSION = "2026.08.31.c140-companion-c5"
VERIFICATION_SCHEMA = "o006.c140.companion-c5.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c5.github-release-publication.v1"
CONTENT_RECEIPT_SCHEMA = "o006.c140.c5.github-content-readback.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TAG = "v2026.08.31.c140-companion-c5"
PRIOR_TAG = "v2026.08.29.c140-companion-c4"
PRIOR_RELEASE_ID = 379_047_752
PRIOR_COMMIT = "9b10b3e04b451232b1233d0b35cf31c3860d63db"
PRIOR_TAG_OBJECT = "1dd397eeb0d717046e4f31a5d65abe97c3c9567b"
PRIOR_RECEIPT_BYTES = 63_441
PRIOR_RECEIPT_SHA256 = (
    "efd537d327dcd6d4a02a74c1194696c860f8f1273b88cbd6db920c81faa9598c"
)
PRIOR_RECEIPT_SCHEMA = "o006.c140.companion-c4.github-release-readback.v1"
PRIOR_FILE_COUNT = 57
PRIOR_TOTAL_BYTES = 93_850_993
EXPECTED_NEW_FILES = 8
EXPECTED_FILE_COUNT = PRIOR_FILE_COUNT + EXPECTED_NEW_FILES
MAX_RELEASE_BYTES = 500_000_000
MAX_PUBLIC_FILE_BYTES = 100_000_000
MAX_AUTHENTICATED_RELEASE_PAGES = 100
MAX_RECEIPT_BYTES = 64 * 1024 * 1024
INHERITED_NAMES = tuple(c4pub.EXPECTED_NAMES)
_CONTENT_WITNESS: dict[str, object] | None = None

TITLE = "O006/C140 Statistika Matematis — Pendamping Orisinal C5 (Bahasa Indonesia)"
BODY = (
    "Rilis kumulatif ini mempertahankan secara byte-identik seluruh 57 aset "
    "checkpoint C4 yang telah dibaca balik secara anonim, lalu menambahkan "
    "tepat delapan aset C5 yang diakui oleh receipt paket deterministik. C5 "
    "memuat asesmen kumulatif dan capstone terakhir beserta sumber, backend, "
    "data berhak-jelas, hasil analisis deterministik, dan bukti QA statis. "
    "Cakupan serta status persis dinyatakan di catatan rilis dan receipt. Hak "
    "Penn State, donor Random, data capstone, dan pendamping orisinal tetap "
    "dipisahkan per komponen; agregat tidak direlisensi secara seragam. Semua "
    "produksi dan QA bersifat tanpa browser. Provenans: "
    + MODEL_PROVENANCE
    + "."
)
TAG_MESSAGE = "O006/C140 original companion C5 cumulative release (2026-08-31)"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


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


def safe_directory_node(path: Path, label: str) -> None:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} directory is unavailable") from exc
    if path.is_symlink() or not stat.S_ISDIR(metadata.st_mode) or reparse(metadata):
        raise RuntimeError(f"{label} crosses a symlink/reparse directory")


def safe_repo_directory_chain(path: Path, label: str) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"{label} lies outside the repository") from exc
    safe_directory_node(ROOT, label)
    current = ROOT
    for part in relative.parts:
        current /= part
        safe_directory_node(current, label)


def safe_file_snapshot(
    path: Path,
    label: str,
    *,
    minimum_bytes: int = 0,
    maximum_bytes: int | None = None,
    expected_bytes: int | None = None,
) -> bytes:
    try:
        before_path = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(before_path.st_mode) or reparse(before_path):
        raise RuntimeError(f"{label} is not a regular non-reparse file")
    if before_path.st_size < minimum_bytes or (
        maximum_bytes is not None and before_path.st_size > maximum_bytes
    ) or (
        expected_bytes is not None and before_path.st_size != expected_bytes
    ):
        raise RuntimeError(f"{label} size is outside its admitted bound")
    read_limit = expected_bytes if expected_bytes is not None else maximum_bytes
    try:
        with path.open("rb") as handle:
            before_handle = os.fstat(handle.fileno())
            payload = handle.read(read_limit + 1) if read_limit is not None else handle.read()
            after_handle = os.fstat(handle.fileno())
        after_path = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} cannot be snapshotted") from exc
    identities = {
        file_identity(before_path),
        file_identity(before_handle),
        file_identity(after_handle),
        file_identity(after_path),
    }
    if (
        len(identities) != 1
        or len(payload) != before_path.st_size
        or (read_limit is not None and len(payload) > read_limit)
        or path.is_symlink()
        or reparse(after_path)
    ):
        raise RuntimeError(f"{label} changed while being snapshotted")
    return payload


def safe_read_confined(
    relative: str,
    label: str,
    *,
    expected_bytes: int | None = None,
) -> bytes:
    canonical = engine.canonical_relative(relative, label)
    path = ROOT.joinpath(*PurePosixPath(canonical).parts)
    safe_repo_directory_chain(path.parent, label)
    payload = safe_file_snapshot(
        path,
        label,
        maximum_bytes=MAX_RELEASE_BYTES,
        expected_bytes=expected_bytes,
    )
    safe_repo_directory_chain(path.parent, label)
    return payload


def safe_read_token() -> str:
    """Read exactly one supported GitHub token from the pinned file only."""
    # Ambient environment credentials are intentionally not admitted.
    for directory in reversed(TOKEN_FILE.parents):
        safe_directory_node(directory, "bounded GitHub credential source")
    payload = safe_file_snapshot(
        TOKEN_FILE,
        "bounded GitHub credential source",
        minimum_bytes=1,
        maximum_bytes=65_536,
    )
    for directory in reversed(TOKEN_FILE.parents):
        safe_directory_node(directory, "bounded GitHub credential source")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("bounded GitHub credential source is not strict UTF-8") from exc
    matches = engine.TOKEN_RE.findall(text)
    if len(matches) != 1 or engine.TOKEN_RE.fullmatch(matches[0]) is None:
        raise RuntimeError("bounded GitHub credential source must contain exactly one token")
    return matches[0]


def safe_atomic_json(path: Path, value: dict[str, object]) -> None:
    """Write one repository receipt without following path indirection."""

    payload = engine.canonical_json(value)
    if not payload or len(payload) > MAX_RECEIPT_BYTES:
        raise RuntimeError("C5 GitHub receipt exceeds its admitted byte bound")
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError("C5 GitHub receipt destination lies outside the repository") from exc
    canonical = engine.canonical_relative(relative.as_posix(), "C5 GitHub receipt path")
    if ROOT.joinpath(*PurePosixPath(canonical).parts) != path:
        raise RuntimeError("C5 GitHub receipt destination is not canonical")
    safe_repo_directory_chain(path.parent, "C5 GitHub receipt destination")
    if path.exists() or path.is_symlink():
        safe_file_snapshot(path, "C5 GitHub receipt destination", maximum_bytes=MAX_RECEIPT_BYTES)
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
        if safe_file_snapshot(
            temporary,
            "temporary C5 GitHub receipt",
            expected_bytes=len(payload),
        ) != payload:
            raise RuntimeError("temporary C5 GitHub receipt differs")
        safe_repo_directory_chain(path.parent, "C5 GitHub receipt destination")
        if safe_file_snapshot(
            temporary,
            "temporary C5 GitHub receipt before replace",
            expected_bytes=len(payload),
        ) != payload:
            raise RuntimeError("temporary C5 GitHub receipt changed")
        os.replace(temporary, path)
        temporary = None
        if safe_file_snapshot(
            path,
            "written C5 GitHub receipt",
            expected_bytes=len(payload),
        ) != payload:
            raise RuntimeError("written C5 GitHub receipt differs")
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def prior_receipt_contract() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and validate the immutable C4 GitHub public-byte witness."""
    payload = safe_read_confined(
        PRIOR_RECEIPT_RELATIVE,
        "C4 GitHub public readback",
        expected_bytes=PRIOR_RECEIPT_BYTES,
    )
    if len(payload) != PRIOR_RECEIPT_BYTES or sha256(payload) != PRIOR_RECEIPT_SHA256:
        raise RuntimeError("C4 GitHub public-readback receipt identity differs")
    receipt = json_object(payload, "C4 GitHub public-readback receipt")
    public = receipt.get("public")
    local = receipt.get("local_inventory")
    public_files = public.get("files") if isinstance(public, dict) else None
    annotated = public.get("annotated_tag") if isinstance(public, dict) else None
    if (
        receipt.get("schema") != PRIOR_RECEIPT_SCHEMA
        or receipt.get("status") != "pass"
        or receipt.get("mode") != "public-byte-verification"
        or receipt.get("tag") != PRIOR_TAG
        or receipt.get("commit") != PRIOR_COMMIT
        or receipt.get("local_files") != PRIOR_FILE_COUNT
        or receipt.get("local_bytes") != PRIOR_TOTAL_BYTES
        or receipt.get("public_asset_readback_anonymous") is not True
        or receipt.get("prior_release_untouched") is not True
        or receipt.get("remote_writes") is not False
        or receipt.get("browser_processes_used") is not False
        or not isinstance(public, dict)
        or public.get("release_id") != PRIOR_RELEASE_ID
        or public.get("tag") != PRIOR_TAG
        or public.get("file_count") != PRIOR_FILE_COUNT
        or public.get("total_bytes") != PRIOR_TOTAL_BYTES
        or public.get("reader_first") is not True
        or public.get("public_asset_readback_anonymous") is not True
        or not isinstance(annotated, dict)
        or annotated.get("annotated") is not True
        or annotated.get("tag_object") != PRIOR_TAG_OBJECT
        or annotated.get("peeled_commit") != PRIOR_COMMIT
        or not isinstance(local, list)
        or not isinstance(public_files, list)
        or len(local) != PRIOR_FILE_COUNT
        or len(public_files) != PRIOR_FILE_COUNT
    ):
        raise RuntimeError("C4 GitHub public-readback contract differs")

    inventory: list[dict[str, Any]] = []
    for index, (local_row, public_row) in enumerate(
        zip(local, public_files, strict=True)
    ):
        if not isinstance(local_row, dict) or not isinstance(public_row, dict):
            raise RuntimeError(f"malformed C4 GitHub inventory row {index}")
        name = local_row.get("name")
        if (
            name != INHERITED_NAMES[index]
            or public_row.get("name") != name
            or public_row.get("bytes") != local_row.get("bytes")
            or public_row.get("sha256") != local_row.get("sha256")
            or public_row.get("validated_download") is not True
            or public_row.get("http_status") != 200
            or public_row.get("automatic_redirects_followed") is not False
            or not isinstance(local_row.get("bytes"), int)
            or local_row.get("bytes") <= 0
            or not isinstance(local_row.get("sha256"), str)
            or engine.SHA256_RE.fullmatch(local_row["sha256"]) is None
            or not isinstance(local_row.get("role"), str)
            or not isinstance(local_row.get("lineage"), str)
        ):
            raise RuntimeError(f"C4 GitHub inventory identity differs at row {index}")
        inventory.append(dict(local_row))
    if sum(int(row["bytes"]) for row in inventory) != PRIOR_TOTAL_BYTES:
        raise RuntimeError("C4 GitHub inventory byte total differs")
    return receipt, inventory


def content_receipt_contract(package: dict[str, Any]) -> dict[str, object]:
    """Bind release lineage to the exact verified C5 content commit."""
    payload = safe_read_confined(
        CONTENT_RECEIPT_RELATIVE,
        "C5 committed-content readback receipt",
    )
    content = json_object(payload, "C5 committed-content readback receipt")
    commit = content.get("commit")
    parent = content.get("parent")
    files = content.get("files")
    gate = content.get("c5_gate")
    gate_build = gate.get("build_receipt") if isinstance(gate, dict) else None
    gate_qa = gate.get("qa_receipt") if isinstance(gate, dict) else None
    manifest = content.get("commit_manifest")
    privacy = content.get("privacy_scan")
    release_snapshot = content.get("release_snapshot")
    package_gates = package.get("gates")
    inputs = (
        package_gates.get("input_receipts")
        if isinstance(package_gates, dict)
        else None
    )
    expected_build = (
        inputs.get("build/C5_BUILD_RECEIPT.json") if isinstance(inputs, dict) else None
    )
    expected_qa = (
        inputs.get("build/C5_QA_RECEIPT.json") if isinstance(inputs, dict) else None
    )
    if (
        content.get("schema") != CONTENT_RECEIPT_SCHEMA
        or content.get("status") != "pass"
        or not isinstance(commit, str)
        or engine.SHA1_RE.fullmatch(commit) is None
        or not isinstance(parent, str)
        or engine.SHA1_RE.fullmatch(parent) is None
        or content.get("all_match") is not True
        or content.get("credential_mode") != "none"
        or content.get("credentials_read") is not False
        or content.get("authorization_header_sent") is not False
        or content.get("browser_used") is not False
        or content.get("browser_processes_launched") is not False
        or not isinstance(files, list)
        or content.get("file_count") != len(files)
        or not isinstance(content.get("total_bytes"), int)
        or content.get("total_bytes") <= 0
        or content.get("public_total_bytes") != content.get("total_bytes")
        or not isinstance(content.get("aggregate_sha256"), str)
        or engine.SHA256_RE.fullmatch(content["aggregate_sha256"]) is None
        or any(not isinstance(row, dict) or row.get("match") is not True for row in files)
        or not isinstance(gate, dict)
        or gate.get("authority")
        != "exact committed Git blobs at the verified C5 commit"
        or not isinstance(gate_build, dict)
        or not isinstance(expected_build, dict)
        or any(
            gate_build.get(key) != expected_build.get(key)
            for key in ("bytes", "sha256")
        )
        or gate_build.get("path") != BUILD_RELATIVE
        or not isinstance(gate_qa, dict)
        or not isinstance(expected_qa, dict)
        or any(
            gate_qa.get(key) != expected_qa.get(key)
            for key in ("bytes", "sha256")
        )
        or gate_qa.get("path") != QA_RELATIVE
        or content.get("changed_file_set_manifest_closed") is not True
        or not isinstance(manifest, dict)
        or manifest.get("changed_files_including_manifest") != len(files)
        or not isinstance(privacy, dict)
        or privacy.get("files_scanned") != len(files)
        or privacy.get("forbidden_markers_found") != 0
        or privacy.get("status") != "pass"
    ):
        raise RuntimeError("C5 committed-content readback contract differs")
    file_by_path: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(files):
        assert isinstance(row, dict)
        path = row.get("path")
        if (
            not isinstance(path, str)
            or engine.canonical_relative(path, f"C5 content row {index} path") != path
            or path in file_by_path
            or not isinstance(row.get("bytes"), int)
            or isinstance(row.get("bytes"), bool)
            or row.get("bytes") <= 0
            or not isinstance(row.get("sha256"), str)
            or engine.SHA256_RE.fullmatch(row["sha256"]) is None
            or row.get("public_bytes") != row.get("bytes")
            or row.get("public_sha256") != row.get("sha256")
        ):
            raise RuntimeError(f"C5 committed-content row is not admitted: {index}")
        file_by_path[path] = row

    written_package = safe_read_confined(
        PACKAGE_RELATIVE, "written C5 package receipt for commit binding"
    )
    if json_object(written_package, "written C5 package receipt") != package:
        raise RuntimeError("written C5 package receipt differs from computed contract")
    publication = package.get("publication_inventory")
    package_rows = publication.get("files") if isinstance(publication, dict) else None
    release_files = (
        release_snapshot.get("files") if isinstance(release_snapshot, dict) else None
    )
    if (
        not isinstance(release_snapshot, dict)
        or release_snapshot.get("authority")
        != "exact cumulative release blobs in the verified C5 commit tree"
        or release_snapshot.get("all_match") is not True
        or not isinstance(package_rows, list)
        or not isinstance(release_files, list)
        or release_snapshot.get("file_count") != len(package_rows)
        or len(release_files) != len(package_rows)
        or release_snapshot.get("bytes") != publication.get("bytes")
    ):
        raise RuntimeError("C5 committed release-snapshot gate differs")
    package_identity = release_snapshot.get("package_receipt")
    content_package_row = file_by_path.get(PACKAGE_RELATIVE)
    if (
        not isinstance(package_identity, dict)
        or package_identity.get("path") != PACKAGE_RELATIVE
        or package_identity.get("bytes") != len(written_package)
        or package_identity.get("sha256") != sha256(written_package)
        or not isinstance(content_package_row, dict)
        or content_package_row.get("bytes") != len(written_package)
        or content_package_row.get("sha256") != sha256(written_package)
    ):
        raise RuntimeError("C5 committed package-receipt binding differs")
    for index, (package_row, release_row) in enumerate(
        zip(package_rows, release_files, strict=True), start=1
    ):
        if not isinstance(package_row, dict) or not isinstance(release_row, dict):
            raise RuntimeError(f"C5 committed release row is malformed: {index}")
        if (
            release_row.get("upload_order") != index
            or release_row.get("filename") != package_row.get("filename")
            or release_row.get("path") != package_row.get("source_path")
            or release_row.get("bytes") != package_row.get("bytes")
            or release_row.get("sha256") != package_row.get("sha256")
            or release_row.get("match") is not True
        ):
            raise RuntimeError(f"C5 committed release row differs: {index}")
    release_aggregate = sha256(
        json.dumps(
            [
                {
                    "path": row["path"],
                    "bytes": row["bytes"],
                    "sha256": row["sha256"],
                }
                for row in release_files
            ],
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    )
    if release_snapshot.get("aggregate_sha256") != release_aggregate:
        raise RuntimeError("C5 committed release aggregate identity differs")
    return {
        "path": CONTENT_RECEIPT_RELATIVE,
        "bytes": len(payload),
        "sha256": sha256(payload),
        "schema": CONTENT_RECEIPT_SCHEMA,
        "commit": commit,
        "parent": parent,
        "files": len(files),
        "bytes_verified": content["total_bytes"],
        "aggregate_sha256": content["aggregate_sha256"],
        "all_match": True,
        "release_snapshot": {
            "authority": release_snapshot["authority"],
            "file_count": release_snapshot["file_count"],
            "bytes": release_snapshot["bytes"],
            "aggregate_sha256": release_aggregate,
            "package_receipt_sha256": sha256(written_package),
            "all_match": True,
        },
        "credential_access": False,
        "browser_processes_used": False,
    }


def frozen_content_witness() -> dict[str, object]:
    if _CONTENT_WITNESS is None:
        raise RuntimeError("C5 committed-content witness is not frozen")
    return dict(_CONTENT_WITNESS)


def validate_input_receipt(
    input_receipts: dict[str, Any], relative: str, path: Path
) -> None:
    witness = input_receipts.get(relative)
    if not isinstance(witness, dict):
        raise RuntimeError(f"C5 input receipt is missing or unsafe: {relative}")
    expected_size = witness.get("bytes")
    if not isinstance(expected_size, int) or isinstance(expected_size, bool) or expected_size <= 0:
        raise RuntimeError(f"C5 input receipt size is invalid: {relative}")
    try:
        repo_relative = path.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise RuntimeError(f"C5 input receipt lies outside repository: {relative}") from exc
    payload = safe_read_confined(
        repo_relative,
        f"C5 input receipt {relative}",
        expected_bytes=expected_size,
    )
    if witness != {"bytes": len(payload), "sha256": sha256(payload)}:
        raise RuntimeError(f"C5 input receipt identity differs: {relative}")


def computed_contract() -> tuple[
    dict[str, bytes],
    bytes,
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Recompute and validate the complete receipt-driven C5 contract."""
    outputs, receipt_payload = packager.compute()
    if not isinstance(outputs, dict) or not outputs:
        raise RuntimeError("C5 packager did not return an artifact mapping")
    package = json_object(receipt_payload, "computed C5 package receipt")
    _prior_receipt, prior_inventory = prior_receipt_contract()
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != PACKAGE_VERSION
        or package.get("status") != "ready"
        or not isinstance(publication, dict)
        or publication.get("file_count") != EXPECTED_FILE_COUNT
        or not isinstance(publication.get("bytes"), int)
        or publication.get("bytes") <= PRIOR_TOTAL_BYTES
        or publication.get("bytes") > MAX_RELEASE_BYTES
        or not isinstance(rows, list)
        or len(rows) != EXPECTED_FILE_COUNT
    ):
        raise RuntimeError("computed C5 package identity or totals differ")

    names: list[str] = []
    seen_paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"malformed C5 package row {index}")
        name = row.get("filename")
        size = row.get("bytes")
        digest = row.get("sha256")
        source_path = row.get("source_path")
        if (
            not isinstance(name, str)
            or engine.SAFE_NAME_RE.fullmatch(name) is None
            or engine.SENSITIVE_NAME_RE.search(name) is not None
            or name in names
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size <= 0
            or size > MAX_PUBLIC_FILE_BYTES
            or not isinstance(digest, str)
            or engine.SHA256_RE.fullmatch(digest) is None
            or source_path != f"release/{name}"
            or source_path in seen_paths
            or row.get("upload_order") != index + 1
            or row.get("primary_reader") is not (index == 0)
            or not isinstance(row.get("media_type"), str)
            or "/" not in row["media_type"]
            or not isinstance(row.get("role"), str)
            or not row["role"]
            or not isinstance(row.get("lineage"), str)
            or not row["lineage"]
        ):
            raise RuntimeError(f"C5 publication row is not admitted: {index}")
        payload = outputs.get(name)
        if payload is None or len(payload) != size or sha256(payload) != digest:
            raise RuntimeError(f"C5 computed artifact differs from receipt: {name}")
        names.append(name)
        seen_paths.add(source_path)
        total += size
    if tuple(outputs) != tuple(names) or total != publication.get("bytes"):
        raise RuntimeError("C5 output order or byte total differs from its receipt")

    for index, prior in enumerate(prior_inventory):
        row = rows[index]
        if (
            row.get("filename") != prior["name"]
            or row.get("bytes") != prior["bytes"]
            or row.get("sha256") != prior["sha256"]
            or row.get("role") != prior["role"]
            or row.get("lineage") != prior["lineage"]
        ):
            raise RuntimeError(f"inherited C4 GitHub asset changed at row {index}")

    additions = rows[PRIOR_FILE_COUNT:]
    if len(additions) != EXPECTED_NEW_FILES:
        raise RuntimeError("C5 must append exactly eight assets")
    for row in additions:
        marker = " ".join(
            str(row[key]).casefold() for key in ("filename", "role", "lineage")
        )
        if "c5" not in marker:
            raise RuntimeError(f"C5 addition lacks an explicit C5 identity: {row['filename']}")

    preservation = package.get("preservation")
    if (
        not isinstance(preservation, dict)
        or preservation.get("inherited_file_count") != PRIOR_FILE_COUNT
        or preservation.get("inherited_files_byte_identical") is not True
        or preservation.get("new_file_count") != EXPECTED_NEW_FILES
    ):
        raise RuntimeError("C5 preservation contract differs")
    reader_order = package.get("reader_order")
    if (
        not isinstance(reader_order, dict)
        or reader_order.get("inherited_union_first") is not True
        or reader_order.get("c5_first_upload_order") != PRIOR_FILE_COUNT + 1
        or reader_order.get("pdf_upload_order") != 1
        or reader_order.get("epub_upload_order") != 2
    ):
        raise RuntimeError("C5 reader/upload order differs")
    rights = package.get("rights")
    lineage = package.get("lineage")
    packaging = package.get("packager")
    if (
        not isinstance(rights, dict)
        or rights.get("aggregate_uniform_relicense") is not False
        or rights.get("component_licenses_unchanged") is not True
        or not isinstance(lineage, dict)
        or lineage.get("create_competing_concept") is not False
        or not isinstance(packaging, dict)
        or packaging.get("browser_processes_used") is not False
        or packaging.get("credential_access") is not False
        or packaging.get("git_operations") is not False
        or packaging.get("network_access") is not False
        or packaging.get("publication_side_effects") is not False
        or packaging.get("recursive_repository_discovery") is not False
    ):
        raise RuntimeError("C5 rights, lineage, or packager safety contract differs")

    gates = package.get("gates")
    archives = gates.get("archives") if isinstance(gates, dict) else None
    boundary = gates.get("c5_boundary") if isinstance(gates, dict) else None
    input_receipts = gates.get("input_receipts") if isinstance(gates, dict) else None
    publication_size = gates.get("publication_size") if isinstance(gates, dict) else None
    if (
        not isinstance(gates, dict)
        or not isinstance(gates.get("privacy"), dict)
        or gates["privacy"].get("forbidden_markers_found") != 0
        or set(gates["privacy"]) != {
            "forbidden_markers_found", "public_source_email_evidence",
            "public_source_email_policy"
        }
        or not isinstance(gates["privacy"]["public_source_email_evidence"], list)
        or not isinstance(gates["privacy"]["public_source_email_policy"], str)
        or not isinstance(boundary, dict)
        or boundary.get("status") != "pass"
        or not isinstance(input_receipts, dict)
        or publication_size
        != {
            "bytes": total,
            "cap_bytes": MAX_RELEASE_BYTES,
            "file_cap_bytes": MAX_PUBLIC_FILE_BYTES,
            "maximum_file_bytes": max(int(row["bytes"]) for row in rows),
            "status": "pass",
        }
        or not isinstance(archives, dict)
    ):
        raise RuntimeError("C5 package gates differ")
    validate_input_receipt(
        input_receipts,
        "build/C5_BUILD_RECEIPT.json",
        COMPONENT / "build" / "C5_BUILD_RECEIPT.json",
    )
    validate_input_receipt(
        input_receipts,
        "build/C5_QA_RECEIPT.json",
        COMPONENT / "build" / "C5_QA_RECEIPT.json",
    )
    addition_by_name = {str(row["filename"]): row for row in additions}
    zip_names = {
        name
        for name, row in addition_by_name.items()
        if row.get("media_type") == "application/zip"
    }
    if set(archives) != zip_names:
        raise RuntimeError("C5 archive gates do not cover exactly the new ZIP assets")
    for name, archive in archives.items():
        row = addition_by_name[name]
        if (
            not isinstance(archive, dict)
            or archive.get("bytes") != row["bytes"]
            or archive.get("sha256") != row["sha256"]
            or archive.get("privacy") != {"forbidden_markers_found": 0}
        ):
            raise RuntimeError(f"C5 archive gate differs: {name}")
    return outputs, receipt_payload, package, rows, prior_inventory


def snapshot() -> engine.Snapshot:
    outputs, receipt_payload, package, rows, prior_inventory = computed_contract()
    if (
        safe_read_confined(
            PACKAGE_RELATIVE,
            "written C5 package receipt",
            expected_bytes=len(receipt_payload),
        )
        != receipt_payload
    ):
        raise RuntimeError("written C5 package receipt differs; run its packager --write")
    artifacts: list[engine.Artifact] = []
    total = 0
    for index, row in enumerate(rows):
        name = str(row["filename"])
        relative = engine.canonical_relative(row["source_path"], f"C5 row {index} path")
        payload = safe_read_confined(
            relative,
            f"C5 release asset {name}",
            expected_bytes=int(row["bytes"]),
        )
        if outputs.get(name) != payload:
            raise RuntimeError(f"written C5 release asset differs: {name}")
        if index < PRIOR_FILE_COUNT:
            prior = prior_inventory[index]
            if len(payload) != prior["bytes"] or sha256(payload) != prior["sha256"]:
                raise RuntimeError(f"written inherited C4 asset changed: {name}")
        artifacts.append(
            engine.Artifact(
                name=name,
                path=relative,
                bytes=len(payload),
                sha256=sha256(payload),
                payload=payload,
                role=str(row["role"]),
                lineage=str(row["lineage"]),
                media_type=str(row["media_type"]),
            )
        )
        total += len(payload)
    if total != package["publication_inventory"]["bytes"]:
        raise RuntimeError("written C5 cumulative byte total differs")
    return engine.Snapshot(
        package=package,
        package_receipt_bytes=len(receipt_payload),
        package_receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited_files=tuple(artifacts[:PRIOR_FILE_COUNT]),
        additions=tuple(artifacts[PRIOR_FILE_COUNT:]),
    )


def prior_release_witness(
    snap: engine.Snapshot, control_session: Any | None = None
) -> dict[str, object]:
    """Revalidate the exact prior 57-asset C4 release and annotated tag."""
    del snap
    _receipt, inventory = prior_receipt_contract()
    control = control_session or engine.public_session()
    ref_url = f"{engine.REPOSITORY_API}/git/ref/tags/{quote(PRIOR_TAG, safe='')}"
    ref = engine.api_json(control, "GET", ref_url, action="read prior C4 tag", timeout=120)
    obj = ref.get("object")
    if (
        ref.get("ref") != f"refs/tags/{PRIOR_TAG}"
        or not isinstance(obj, dict)
        or obj.get("type") != "tag"
        or obj.get("sha") != PRIOR_TAG_OBJECT
    ):
        raise RuntimeError("prior C4 annotated-tag witness differs")
    tag = engine.api_json(
        control,
        "GET",
        f"{engine.REPOSITORY_API}/git/tags/{PRIOR_TAG_OBJECT}",
        action="peel prior C4 annotated tag",
        timeout=120,
    )
    target = tag.get("object")
    if (
        tag.get("sha") != PRIOR_TAG_OBJECT
        or tag.get("tag") != PRIOR_TAG
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != PRIOR_COMMIT
    ):
        raise RuntimeError("prior C4 tag no longer peels to its fixed commit")
    release = engine.release_by_tag(control, PRIOR_TAG, allow_missing=False)
    assert release is not None
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    by_name = {str(row.get("name")): row for row in assets}
    expected = {row["name"]: row for row in inventory}
    if (
        release.get("id") != PRIOR_RELEASE_ID
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or len(assets) != PRIOR_FILE_COUNT
        or set(by_name) != set(expected)
    ):
        raise RuntimeError("prior C4 release witness differs")
    files: list[dict[str, object]] = []
    for item in inventory:
        remote = by_name[item["name"]]
        if remote.get("size") != item["bytes"] or remote.get("state") != "uploaded":
            raise RuntimeError(f"prior C4 asset metadata differs: {item['name']}")
        files.append(
            {"name": item["name"], "bytes": item["bytes"], "sha256": item["sha256"]}
        )
    witness = {
        "release_id": PRIOR_RELEASE_ID,
        "tag": PRIOR_TAG,
        "url": f"{engine.REPOSITORY_URL}/releases/tag/{PRIOR_TAG}",
        "annotated_tag": {
            "ref_url": ref_url,
            "tag_object": PRIOR_TAG_OBJECT,
            "peeled_commit": PRIOR_COMMIT,
        },
        "files": files,
        "file_count": PRIOR_FILE_COUNT,
        "total_bytes": PRIOR_TOTAL_BYTES,
        "durable_receipt": {
            "path": PRIOR_RECEIPT_RELATIVE,
            "bytes": PRIOR_RECEIPT_BYTES,
            "sha256": PRIOR_RECEIPT_SHA256,
        },
    }
    return {**witness, "witness_sha256": sha256(engine.canonical_json(witness))}


def receipt_base(snap: engine.Snapshot, commit: str) -> dict[str, object]:
    content_witness = frozen_content_witness()
    if commit != content_witness["commit"]:
        raise RuntimeError("release commit differs from the frozen C5 content witness")
    return {
        "version": PACKAGE_VERSION,
        "repository": engine.REPOSITORY_URL,
        "tag": TAG,
        "commit": commit,
        "release_scope": snap.package.get("coverage"),
        "component_separated_rights": True,
        "aggregate_uniform_relicense": False,
        "local_inventory": [
            {
                "name": item.name,
                "bytes": item.bytes,
                "sha256": item.sha256,
                "role": item.role,
                "lineage": item.lineage,
            }
            for item in snap.files
        ],
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "prior_c4_files_preserved": len(snap.inherited_files),
        "companion_c5_additions": len(snap.additions),
        "companion_c5_replacements": 0,
        "package_receipt": {
            "path": PACKAGE_RELATIVE,
            "bytes": snap.package_receipt_bytes,
            "sha256": snap.package_receipt_sha256,
        },
        "prior_public_receipt": {
            "path": PRIOR_RECEIPT_RELATIVE,
            "bytes": PRIOR_RECEIPT_BYTES,
            "sha256": PRIOR_RECEIPT_SHA256,
        },
        "committed_content_receipt": content_witness,
        "translation_provenance": MODEL_PROVENANCE,
        "browser_processes_used": False,
        "machine_local_paths_recorded": False,
    }


def verification_payload(
    snap: engine.Snapshot,
    commit: str,
    public: dict[str, object],
    prior: dict[str, object],
    *,
    control_plane_credential_access: bool,
) -> dict[str, object]:
    del control_plane_credential_access
    reproducible_public = dict(public)
    reproducible_public.pop("authenticated_release_inventory", None)
    reproducible_public.pop("public_release_inventory", None)
    return {
        "schema": VERIFICATION_SCHEMA,
        "status": "pass",
        **receipt_base(snap, commit),
        "mode": "public-byte-verification",
        "public_asset_readback_anonymous": True,
        "control_plane_credential_access": False,
        "credential_access": False,
        "remote_writes": False,
        "prior_release_untouched": True,
        "prior_release_witness": prior,
        "public": reproducible_public,
    }


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt, package, rows, prior = computed_contract()
    content_witness = content_receipt_contract(package)
    return {
        "annotated_tag_required": True,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "component_separated_rights": True,
        "credential_access": False,
        "files": len(rows),
        "inherited_files": len(prior),
        "mode": "contract-only",
        "network_access": False,
        "new_files": len(rows) - len(prior),
        "committed_content_receipt": content_witness,
        "package_receipt_sha256": sha256(receipt),
        "prior_commit": PRIOR_COMMIT,
        "prior_public_receipt_sha256": PRIOR_RECEIPT_SHA256,
        "prior_release_id": PRIOR_RELEASE_ID,
        "prior_tag": PRIOR_TAG,
        "prior_tag_object": PRIOR_TAG_OBJECT,
        "publication_side_effects": False,
        "replacements": 0,
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "tag": TAG,
        "version": PACKAGE_VERSION,
    }


def contract_summary(snap: engine.Snapshot) -> dict[str, object]:
    return {
        "annotated_tag_required": True,
        "browser_processes_used": False,
        "bytes": snap.total_bytes,
        "component_separated_rights": True,
        "credential_access": False,
        "files": len(snap.files),
        "inherited_files": len(snap.inherited_files),
        "mode": "contract-check",
        "network_access": False,
        "new_files": len(snap.additions),
        "package_receipt_sha256": snap.package_receipt_sha256,
        "prior_commit": PRIOR_COMMIT,
        "prior_public_receipt_sha256": PRIOR_RECEIPT_SHA256,
        "prior_release_id": PRIOR_RELEASE_ID,
        "prior_tag": PRIOR_TAG,
        "prior_tag_object": PRIOR_TAG_OBJECT,
        "primary_file": snap.files[0].name,
        "publication_side_effects": False,
        "replacements": 0,
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "tag": TAG,
        "version": PACKAGE_VERSION,
        "coverage": snap.package.get("coverage"),
        "committed_content_receipt": frozen_content_witness(),
    }


def require_content_commit(parser: Any, value: str | None) -> str:
    if not isinstance(value, str) or engine.SHA1_RE.fullmatch(value) is None:
        parser.error("--commit must be an explicit full lowercase 40-hex commit")
    witness = frozen_content_witness()
    if value != witness["commit"]:
        parser.error("--commit must equal the verified C5 committed-content receipt")
    return value


def authenticated_target_inventory(
    session: Any,
) -> tuple[dict[str, Any] | None, dict[str, object]]:
    """Enumerate every release page visible to the supplied session."""

    matches: list[dict[str, Any]] = []
    lineage_matches: list[dict[str, Any]] = []
    seen_release_ids: set[int] = set()
    releases_seen = 0
    pages_scanned = 0
    terminated = False
    for page in range(1, MAX_AUTHENTICATED_RELEASE_PAGES + 1):
        response = engine.request(
            session,
            "GET",
            f"{engine.REPOSITORY_API}/releases",
            expected=(200,),
            action="enumerate authenticated releases for fixed C5 tag",
            params={"per_page": "100", "page": str(page)},
            timeout=120,
        )
        try:
            values = response.json()
        except ValueError as exc:
            raise RuntimeError("authenticated release inventory is not JSON") from exc
        if (
            not isinstance(values, list)
            or len(values) > 100
            or any(not isinstance(row, dict) for row in values)
        ):
            raise RuntimeError("authenticated release inventory is malformed")
        for row in values:
            release_id = row.get("id")
            if (
                not isinstance(release_id, int)
                or isinstance(release_id, bool)
                or release_id <= 0
                or release_id in seen_release_ids
            ):
                raise RuntimeError(
                    "authenticated release inventory has an invalid/duplicate id"
                )
            seen_release_ids.add(release_id)
        pages_scanned = page
        releases_seen += len(values)
        page_matches = [row for row in values if row.get("tag_name") == TAG]
        matches.extend(page_matches)
        lineage_matches.extend(
            row
            for row in values
            if row.get("tag_name") == TAG
            or row.get("name") == TITLE
            or (
                isinstance(row.get("body"), str)
                and PACKAGE_VERSION in row["body"]
            )
        )
        if len(values) < 100:
            terminated = True
            break
    if not terminated:
        raise RuntimeError("authenticated release inventory exceeded its page cap")
    if len(matches) > 1:
        raise RuntimeError("multiple authenticated releases exist for the fixed C5 tag")
    lineage_ids = {
        row.get("id") for row in lineage_matches if isinstance(row.get("id"), int)
    }
    if len(lineage_ids) > 1 or (
        lineage_ids
        and (not matches or matches[0].get("id") not in lineage_ids)
    ):
        raise RuntimeError("a competing C5 release lineage marker already exists")
    match = matches[0] if matches else None
    return match, {
        "pages_scanned": pages_scanned,
        "releases_seen": releases_seen,
        "target_matches": len(matches),
        "duplicate_targets": max(0, len(matches) - 1),
        "lineage_matches": len(lineage_ids),
        "duplicate_lineages": max(0, len(lineage_ids) - 1),
        "server_termination_observed": True,
        "page_size": 100,
        "page_cap": MAX_AUTHENTICATED_RELEASE_PAGES,
    }


def authenticated_target_release(session: Any) -> dict[str, Any] | None:
    release, _inventory = authenticated_target_inventory(session)
    return release


def digest_streamed_response(response: Any, wanted: engine.Artifact, label: str) -> None:
    """Hash one bounded response without retaining a second full asset copy."""

    digest = hashlib.sha256()
    total = 0
    try:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > wanted.bytes:
                raise RuntimeError(f"{label} exceeds its admitted byte count: {wanted.name}")
            digest.update(chunk)
    finally:
        response.close()
    if total != wanted.bytes or digest.hexdigest() != wanted.sha256:
        raise RuntimeError(f"{label} bytes differ: {wanted.name}")


def admitted_https_port(parsed: Any, label: str) -> bool:
    try:
        return parsed.port in (None, 443)
    except ValueError as exc:
        raise RuntimeError(f"{label} has an invalid port") from exc


def strict_public_asset_streamed(
    job: tuple[engine.Artifact, dict[str, Any]],
) -> dict[str, object]:
    """Credential-free, redirect-bounded, streaming public asset readback."""

    wanted, row = job
    if (
        row.get("name") != wanted.name
        or row.get("state") != "uploaded"
        or row.get("size") != wanted.bytes
        or not isinstance(row.get("id"), int)
    ):
        raise RuntimeError(f"public asset metadata differs: {wanted.name}")
    download_url = row.get("browser_download_url")
    parsed = urlparse(str(download_url))
    expected_path = (
        f"/{engine.OWNER}/{engine.REPO}/releases/download/{TAG}/"
        f"{quote(wanted.name, safe='')}"
    )
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "github.com"
        or not admitted_https_port(parsed, "public asset URL")
        or parsed.path != expected_path
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError(f"public asset URL is not admitted: {wanted.name}")

    session = engine.public_session()
    first = session.get(
        str(download_url), timeout=900, allow_redirects=False, stream=True
    )
    if first.status_code in (301, 302, 303, 307, 308):
        location = first.headers.get("Location")
        first.close()
        target_url = urljoin(str(download_url), str(location or ""))
        target = urlparse(target_url)
        if (
            target.scheme.casefold() != "https"
            or (target.hostname or "").casefold()
            not in engine.ALLOWED_ASSET_CDN_HOSTS
            or not admitted_https_port(target, "public asset redirect")
            or not target.path
            or target.fragment
            or target.username
            or target.password
        ):
            raise RuntimeError(
                f"public asset returned an unadmitted redirect: {wanted.name}"
            )
        second = session.get(
            target_url, timeout=900, allow_redirects=False, stream=True
        )
        if (
            second.is_redirect
            or second.is_permanent_redirect
            or second.status_code != 200
        ):
            second.close()
            raise RuntimeError(
                f"public asset CDN handoff did not terminate: {wanted.name}"
            )
        digest_streamed_response(second, wanted, "public asset")
    elif first.status_code == 200:
        digest_streamed_response(first, wanted, "public asset")
    else:
        status = first.status_code
        first.close()
        raise RuntimeError(
            f"public asset readback failed with HTTP {status}: {wanted.name}"
        )
    return {
        "name": wanted.name,
        "bytes": wanted.bytes,
        "sha256": wanted.sha256,
        "asset_id": row["id"],
        "download_url": download_url,
        "http_status": 200,
        "validated_download": True,
        "redirect_policy": (
            "no automatic redirects; at most one manually validated GitHub CDN handoff"
        ),
        "automatic_redirects_followed": False,
        "streamed_without_full_response_buffer": True,
    }


def authenticated_asset_identity_streamed(
    session: Any, wanted: engine.Artifact, row: dict[str, Any]
) -> None:
    """Verify a resumable draft asset without forwarding or buffering secrets."""

    asset_id = row.get("id")
    api_url = row.get("url")
    parsed = urlparse(str(api_url))
    if (
        not isinstance(asset_id, int)
        or parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "api.github.com"
        or not admitted_https_port(parsed, "target draft asset API URL")
        or parsed.path
        != f"/repos/{engine.OWNER}/{engine.REPO}/releases/assets/{asset_id}"
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError(f"target draft asset API URL differs: {wanted.name}")
    first = session.get(
        str(api_url),
        headers={"Accept": "application/octet-stream"},
        timeout=900,
        allow_redirects=False,
        stream=True,
    )
    if first.status_code in (301, 302, 303, 307, 308):
        location = first.headers.get("Location")
        first.close()
        target_url = urljoin(str(api_url), str(location or ""))
        target = urlparse(target_url)
        if (
            target.scheme.casefold() != "https"
            or (target.hostname or "").casefold()
            not in engine.ALLOWED_ASSET_CDN_HOSTS
            or not admitted_https_port(target, "target draft asset redirect")
            or not target.path
            or target.fragment
            or target.username
            or target.password
        ):
            raise RuntimeError(
                f"target draft asset returned an unadmitted CDN handoff: {wanted.name}"
            )
        anonymous = engine.new_session()
        try:
            second = anonymous.get(
                target_url, timeout=900, allow_redirects=False, stream=True
            )
            if (
                second.is_redirect
                or second.is_permanent_redirect
                or second.status_code != 200
            ):
                second.close()
                raise RuntimeError(
                    f"target draft asset CDN handoff did not terminate: {wanted.name}"
                )
            digest_streamed_response(second, wanted, "target draft asset")
        finally:
            anonymous.close()
    elif first.status_code == 200:
        digest_streamed_response(first, wanted, "target draft asset")
    else:
        status = first.status_code
        first.close()
        raise RuntimeError(
            f"target draft asset readback failed with HTTP {status}: {wanted.name}"
        )


def anonymous_readback_with_unique_target(
    snap: engine.Snapshot,
    commit: str,
    *,
    control_session: Any | None = None,
) -> dict[str, object]:
    """Bind public bytes to the sole target in a complete paginated inventory."""

    public = _ENGINE_ANONYMOUS_READBACK(
        snap,
        commit,
        control_session=control_session,
    )
    created_control = control_session is None
    control = control_session or engine.new_session()
    try:
        release, inventory = authenticated_target_inventory(control)
    finally:
        if created_control:
            control.close()
    if (
        release is None
        or release.get("id") != public.get("release_id")
        or release.get("tag_name") != TAG
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or inventory.get("target_matches") != 1
        or inventory.get("duplicate_targets") != 0
        or inventory.get("lineage_matches") != 1
        or inventory.get("duplicate_lineages") != 0
        or inventory.get("server_termination_observed") is not True
    ):
        raise RuntimeError("complete C5 release inventory differs after readback")
    inventory_key = (
        "public_release_inventory" if created_control else "authenticated_release_inventory"
    )
    return {
        **public,
        inventory_key: {
            "release_id": release["id"],
            "exactly_one_target_release": True,
            "target_matches": 1,
            "duplicate_targets": 0,
            "lineage_matches": 1,
            "duplicate_lineages": 0,
            "server_termination_observed": True,
            "page_size": inventory["page_size"],
            "page_cap": inventory["page_cap"],
            "visibility": "public" if created_control else "authenticated",
        },
    }


def configure_engine() -> None:
    global _CONTENT_WITNESS
    snap = snapshot()
    _CONTENT_WITNESS = content_receipt_contract(snap.package)
    names = tuple(item.name for item in snap.files)
    additions = snap.additions
    engine.TOKEN_FILE = TOKEN_FILE
    engine.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    engine.VERIFICATION_RECEIPT = VERIFICATION_RECEIPT
    engine.PUBLICATION_RECEIPT = PUBLICATION_RECEIPT
    engine.TAG = TAG
    engine.PRIOR_TAG = PRIOR_TAG
    engine.PRIOR_RELEASE_ID = PRIOR_RELEASE_ID
    engine.PRIOR_COMMIT = PRIOR_COMMIT
    engine.PRIOR_TAG_OBJECT = PRIOR_TAG_OBJECT
    engine.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    engine.PACKAGE_VERSION = PACKAGE_VERSION
    engine.VERIFICATION_SCHEMA = VERIFICATION_SCHEMA
    engine.PUBLICATION_SCHEMA = PUBLICATION_SCHEMA
    engine.MODEL_PROVENANCE = MODEL_PROVENANCE
    engine.TITLE = TITLE
    engine.BODY = BODY
    engine.TAG_MESSAGE = TAG_MESSAGE
    engine.EXPECTED_NAMES = names
    engine.EXPECTED_ADDITION_ROLES = {
        item.name: item.role for item in additions
    }
    engine.EXPECTED_ADDITION_LINEAGES = {
        item.name: item.lineage for item in additions
    }
    engine.HEADERS = {
        **engine.HEADERS,
        "User-Agent": "O006-C140-companion-c5/2026.08.31",
    }
    engine.read_confined = safe_read_confined
    engine.read_token = safe_read_token
    engine.atomic_json = safe_atomic_json
    engine.snapshot = lambda: snap
    engine.authenticated_target_release = authenticated_target_release
    engine.strict_public_asset = strict_public_asset_streamed
    engine.authenticated_asset_identity = authenticated_asset_identity_streamed
    engine.anonymous_readback = anonymous_readback_with_unique_target
    engine.prior_release_witness = prior_release_witness
    engine.receipt_base = receipt_base
    engine.verification_payload = verification_payload
    engine.contract_summary = contract_summary
    engine.require_commit = require_content_commit


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
            f"ERROR: C5 GitHub publisher failed closed [{type(exc).__name__}]",
            file=sys.stderr,
        )
        raise SystemExit(1)
