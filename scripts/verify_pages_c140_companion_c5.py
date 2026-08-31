#!/usr/bin/env python3
"""Verify the cumulative C5 Pages collection without a browser process.

One immutable in-memory snapshot binds the collection receipt, C5 BUILD/QA
receipts, 39 required document IDs, and live companion partition for the whole
transaction. The hardened static-HTTPS engine reads exactly that frozen
collection payload. Its result must match the snapshot's hash and totals and
is then bound to the named commit's credential-free committed-content receipt.
No browser process is launched.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests
import truststore

import verify_pages_c140_companion_c1 as engine


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "build" / "PAGES_COLLECTION_RECEIPT.json"
COMPONENT = ROOT / "components" / "c140-companion"
COMPANION_HTML = COMPONENT / "build" / "html-id"
BUILD_RECEIPT = COMPONENT / "build" / "C5_BUILD_RECEIPT.json"
QA_RECEIPT = COMPONENT / "build" / "C5_QA_RECEIPT.json"
CONTENT_RECEIPT = (
    ROOT / "00_control" / "GITHUB_CONTENT_READBACK_2026-08-31_C5_COMMIT.json"
)
RECEIPT = ROOT / "00_control" / "GITHUB_PAGES_RECEIPT_2026-08-31_C140_COMPANION_C5.json"
COLLECTION_RELATIVE = "build/PAGES_COLLECTION_RECEIPT.json"
BUILD_RELATIVE = "components/c140-companion/build/C5_BUILD_RECEIPT.json"
QA_RELATIVE = "components/c140-companion/build/C5_QA_RECEIPT.json"
CONTENT_RELATIVE = "00_control/GITHUB_CONTENT_READBACK_2026-08-31_C5_COMMIT.json"
SCHEMA = "o006.c140.companion-c5.github-pages-readback.v1"
BUILD_SCHEMA = "o006.c140.companion-cumulative-c5-build.v1"
QA_SCHEMA = "o006.c140.companion-cumulative-c5-qa.v1"
CONTENT_SCHEMA = "o006.c140.c5.github-content-readback.v1"
EXPECTED_COMPANION_IDS = {
    "O006-C140-CMP-INDEX",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 14)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 7)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(0, 13)),
    *(f"O006-C140-CMP-CA{i:02d}" for i in range(1, 5)),
    *(f"O006-C140-CMP-CP{i:02d}" for i in range(1, 3)),
}
MAX_LOCAL_FILE_BYTES = 64 * 1024 * 1024
MAX_PUBLIC_FILE_BYTES = 100_000_000
MAX_CONTROL_JSON_BYTES = 8 * 1024 * 1024
GIT_COMMAND_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class LocalSnapshot:
    collection_payload: bytes
    collection: dict[str, Any]
    rows: tuple[dict[str, object], ...]
    build_payload: bytes
    qa_payload: bytes
    contract: dict[str, object]


@dataclass(frozen=True)
class FrozenCollection:
    payload: bytes

    def read_bytes(self) -> bytes:
        return self.payload


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


def safe_directory(path: Path, label: str) -> None:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise RuntimeError(f"{label} lies outside the repository") from exc
    current = ROOT
    for candidate in (ROOT, *(ROOT / Path(*relative.parts[:index]) for index in range(1, len(relative.parts) + 1))):
        current = candidate
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise RuntimeError(f"{label} is unavailable") from exc
        if current.is_symlink() or not stat.S_ISDIR(metadata.st_mode) or reparse(metadata):
            raise RuntimeError(f"{label} crosses a symlink/reparse directory")


def safe_read_bytes(
    path: Path,
    label: str,
    *,
    expected_bytes: int | None = None,
    maximum_bytes: int = MAX_LOCAL_FILE_BYTES,
) -> bytes:
    safe_directory(path.parent, f"{label} parent")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or reparse(metadata):
        raise RuntimeError(f"{label} is not a regular non-reparse file")
    if (
        metadata.st_size < 1
        or metadata.st_size > maximum_bytes
        or (expected_bytes is not None and metadata.st_size != expected_bytes)
    ):
        raise RuntimeError(f"{label} size is outside its admitted bound")
    read_limit = expected_bytes if expected_bytes is not None else maximum_bytes
    try:
        with path.open("rb") as handle:
            before_handle = os.fstat(handle.fileno())
            payload = handle.read(read_limit + 1)
            after_handle = os.fstat(handle.fileno())
        after_path = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} cannot be read") from exc
    safe_directory(path.parent, f"{label} parent")
    if (
        len(
            {
                file_identity(metadata),
                file_identity(before_handle),
                file_identity(after_handle),
                file_identity(after_path),
            }
        )
        != 1
        or len(payload) != metadata.st_size
        or len(payload) > read_limit
        or path.is_symlink()
        or reparse(after_path)
    ):
        raise RuntimeError(f"{label} changed while being snapshotted")
    return payload


def json_payload(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def object_file(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    payload = safe_read_bytes(path, label)
    return json_payload(payload, label), payload


def capture_html() -> dict[str, bytes]:
    safe_directory(COMPANION_HTML, "C5 companion HTML root")
    captured: dict[str, bytes] = {}
    for current_text, directory_names, file_names in os.walk(
        COMPANION_HTML, topdown=True, followlinks=False
    ):
        current = Path(current_text)
        safe_directory(current, "C5 companion HTML directory")
        directory_names.sort()
        for name in directory_names:
            safe_directory(current / name, "C5 companion HTML subdirectory")
        for name in sorted(file_names):
            path = current / name
            relative = path.relative_to(COMPANION_HTML).as_posix()
            if not relative or ".." in Path(relative).parts or relative in captured:
                raise RuntimeError("C5 companion HTML path is unsafe or duplicated")
            captured[relative] = safe_read_bytes(path, "C5 companion HTML file")
    if not captured or "MANIFEST.csv" not in captured:
        raise RuntimeError("C5 companion HTML snapshot is incomplete")
    return captured


def capture_snapshot() -> LocalSnapshot:
    collection_payload = safe_read_bytes(COLLECTION, "Pages collection receipt")
    collection, validated_rows = engine.validate_collection(collection_payload)
    build, build_payload = object_file(BUILD_RECEIPT, "C5 build receipt")
    qa, qa_payload = object_file(QA_RECEIPT, "C5 QA receipt")
    ids = build.get("cumulative_required_ids")
    collection_info = collection.get("collection")
    if (
        not isinstance(collection_info, dict)
        or collection_info.get("files") != len(validated_rows)
        or collection_info.get("bytes")
        != sum(int(row["bytes"]) for row in validated_rows)
    ):
        raise RuntimeError("Pages collection aggregate is internally inconsistent")
    if (
        build.get("schema") != BUILD_SCHEMA
        or build.get("status") != "pass"
        or build.get("boundary") != "cumulative-through-c5"
        or build.get("browser_processes_used") is not False
        or build.get("network_access") is not False
        or not isinstance(ids, list)
        or set(ids) != EXPECTED_COMPANION_IDS
        or len(ids) != len(EXPECTED_COMPANION_IDS)
        or qa.get("schema") != QA_SCHEMA
        or qa.get("status") != "pass"
        or qa.get("browser_processes_used") is not False
        or qa.get("network_access") is not False
        or qa.get("build_receipt_sha256") != sha256(build_payload)
    ):
        raise RuntimeError("C5 build/QA authority differs")

    html_payloads = capture_html()
    expected = [
        {"source_path": path, "bytes": len(payload), "sha256": sha256(payload)}
        for path, payload in sorted(html_payloads.items())
    ]
    partition = sorted(
        (
            row
            for row in validated_rows
            if row.get("source") == "c140-original-companion"
        ),
        key=lambda row: str(row["source_path"]),
    )
    actual = [
        {
            "source_path": row["source_path"],
            "bytes": row["bytes"],
            "sha256": row["sha256"],
        }
        for row in partition
    ]
    if actual != expected:
        raise RuntimeError("Pages companion partition differs from the frozen C5 reader")

    inputs = collection.get("inputs")
    info = inputs.get("c140_original_companion") if isinstance(inputs, dict) else None
    build_html = build.get("html")
    html_bytes = sum(len(payload) for payload in html_payloads.values())
    html_manifest_sha = sha256(html_payloads["MANIFEST.csv"])
    if (
        not isinstance(info, dict)
        or not isinstance(build_html, dict)
        or info.get("path") != "components/c140-companion/build/html-id"
        or info.get("mount") != "components/c140-companion"
        or info.get("files") != len(html_payloads)
        or info.get("bytes") != html_bytes
        or build_html.get("files") != len(html_payloads)
        or build_html.get("bytes") != html_bytes
        or build_html.get("manifest_sha256") != html_manifest_sha
    ):
        raise RuntimeError("Pages C5 input aggregate differs from the frozen build")

    c5_gate = {
        "boundary": "cumulative-through-c5",
        "required_document_ids": sorted(EXPECTED_COMPANION_IDS),
        "required_document_id_count": len(EXPECTED_COMPANION_IDS),
        "build_receipt": {
            "path": BUILD_RELATIVE,
            "bytes": len(build_payload),
            "sha256": sha256(build_payload),
        },
        "qa_receipt": {
            "path": QA_RELATIVE,
            "bytes": len(qa_payload),
            "sha256": sha256(qa_payload),
        },
        "browser_processes_used": False,
        "network_access_during_build_qa": False,
        "status": "pass",
    }
    contract: dict[str, object] = {
        "browser_processes_used": False,
        "collection_bytes": collection_info["bytes"],
        "collection_files": collection_info["files"],
        "collection_manifest_sha256": collection_info["manifest_sha256"],
        "collection_receipt": {
            "path": COLLECTION_RELATIVE,
            "bytes": len(collection_payload),
            "sha256": sha256(collection_payload),
        },
        "companion_bytes": info["bytes"],
        "companion_files": info["files"],
        "companion_html_manifest_sha256": html_manifest_sha,
        "c5_gate": c5_gate,
        "credential_access": False,
        "mode": "contract-only",
        "network_access": False,
        "schema": SCHEMA,
        "status": "pass",
    }
    return LocalSnapshot(
        collection_payload=collection_payload,
        collection=collection,
        rows=tuple(dict(row) for row in validated_rows),
        build_payload=build_payload,
        qa_payload=qa_payload,
        contract=contract,
    )


def committed_content_witness(
    snapshot: LocalSnapshot, commit_id: str
) -> dict[str, object]:
    content, payload = object_file(CONTENT_RECEIPT, "C5 committed-content receipt")
    gate = content.get("c5_gate")
    manifest = content.get("commit_manifest")
    privacy = content.get("privacy_scan")
    files = content.get("files")
    expected_gate = snapshot.contract["c5_gate"]
    assert isinstance(expected_gate, dict)
    gate_build = gate.get("build_receipt") if isinstance(gate, dict) else None
    gate_qa = gate.get("qa_receipt") if isinstance(gate, dict) else None
    expected_build = expected_gate["build_receipt"]
    expected_qa = expected_gate["qa_receipt"]
    assert isinstance(expected_build, dict) and isinstance(expected_qa, dict)
    if (
        content.get("schema") != CONTENT_SCHEMA
        or content.get("status") != "pass"
        or content.get("commit") != commit_id
        or content.get("all_match") is not True
        or content.get("credentials_read") is not False
        or content.get("authorization_header_sent") is not False
        or content.get("browser_used") is not False
        or content.get("browser_processes_launched") is not False
        or not isinstance(files, list)
        or content.get("file_count") != len(files)
        or content.get("public_total_bytes") != content.get("total_bytes")
        or not isinstance(gate, dict)
        or not isinstance(gate_build, dict)
        or any(gate_build.get(key) != expected_build[key] for key in expected_build)
        or not isinstance(gate_qa, dict)
        or any(gate_qa.get(key) != expected_qa[key] for key in expected_qa)
        or gate.get("authority") != "exact committed Git blobs at the verified C5 commit"
        or content.get("changed_file_set_manifest_closed") is not True
        or not isinstance(manifest, dict)
        or manifest.get("changed_files_including_manifest") != len(files)
        or not isinstance(privacy, dict)
        or privacy.get("files_scanned") != len(files)
        or privacy.get("forbidden_markers_found") != 0
        or privacy.get("status") != "pass"
        or any(not isinstance(row, dict) or row.get("match") is not True for row in files)
    ):
        raise RuntimeError("C5 committed-content witness differs from the Pages gate")
    return {
        "path": CONTENT_RELATIVE,
        "bytes": len(payload),
        "sha256": sha256(payload),
        "schema": CONTENT_SCHEMA,
        "commit": commit_id,
        "parent": content.get("parent"),
        "files": content.get("file_count"),
        "bytes_verified": content.get("total_bytes"),
        "aggregate_sha256": content.get("aggregate_sha256"),
        "all_match": True,
    }


def named_git_read(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Read only named commit objects; never inspect the working-tree index."""
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *arguments],
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=GIT_COMMAND_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("bounded named-commit Git read failed") from exc
    if len(result.stdout) > MAX_CONTROL_JSON_BYTES:
        raise RuntimeError("named-commit Git response exceeds its byte cap")
    return result


def validate_pages_identity(commit_id: str, deployment_commit: str, run_id: int) -> None:
    for value in (commit_id, deployment_commit):
        if re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise RuntimeError("commit must be a full 40-character lowercase Git SHA")
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        raise RuntimeError("run-id must be positive")


def deployment_content_binding(
    snapshot: LocalSnapshot, commit_id: str, deployment_commit: str
) -> dict[str, object]:
    """Bind a descendant deployment to the original immutable C5 content."""
    for value in (commit_id, deployment_commit):
        if re.fullmatch(r"[0-9a-f]{40}", value) is None:
            raise RuntimeError("deployment binding requires full lowercase commit IDs")
    commits = tuple(dict.fromkeys((commit_id, deployment_commit)))
    for value in commits:
        kind = named_git_read(["cat-file", "-t", value])
        if kind.returncode != 0 or kind.stdout != b"commit\n":
            raise RuntimeError("source/deployment identity is not a local commit object")
    ancestry = named_git_read(
        ["merge-base", "--is-ancestor", commit_id, deployment_commit]
    )
    if ancestry.returncode != 0 or ancestry.stdout:
        raise RuntimeError("source commit is not a verified ancestor of deployment commit")

    payloads = (
        (BUILD_RELATIVE, snapshot.build_payload),
        (QA_RELATIVE, snapshot.qa_payload),
        (COLLECTION_RELATIVE, snapshot.collection_payload),
    )
    for value in commits:
        for relative, expected in payloads:
            if not expected or len(expected) > MAX_CONTROL_JSON_BYTES:
                raise RuntimeError("frozen deployment receipt exceeds its byte cap")
            object_name = f"{value}:{relative}"
            # Size-check before reading an immutable, replacement-disabled blob.
            size = named_git_read(["cat-file", "-s", object_name])
            if size.returncode != 0 or size.stdout != f"{len(expected)}\n".encode("ascii"):
                raise RuntimeError(f"committed deployment receipt size differs: {relative}")
            blob = named_git_read(["cat-file", "blob", object_name])
            if blob.returncode != 0 or blob.stdout != expected:
                raise RuntimeError(f"committed deployment receipt bytes differ: {relative}")
    return {
        "source_commit": commit_id,
        "deployment_commit": deployment_commit,
        "source_is_ancestor_of_deployment": True,
        "authority": "exact named Git blobs at source and deployment commits",
        "frozen_receipts_match_both_commits": [
            {"path": relative, "bytes": len(payload), "sha256": sha256(payload)}
            for relative, payload in payloads
        ],
        "status": "pass",
    }


def pinned_pages_identity(existing: dict[str, Any]) -> tuple[str, str, int]:
    if existing.get("schema") != SCHEMA:
        raise RuntimeError("C5 Pages receipt schema differs")
    control = existing.get("control_plane")
    if not isinstance(control, dict):
        raise RuntimeError("C5 Pages receipt lacks control-plane identity")
    commit_id = str(control.get("content_commit", ""))
    deployment_commit = str(control.get("deployment_commit", commit_id))
    run_value = control.get("workflow_run_id", 0)
    if isinstance(run_value, bool) or not isinstance(run_value, int):
        raise RuntimeError("C5 Pages receipt workflow run identity differs")
    validate_pages_identity(commit_id, deployment_commit, run_value)
    return commit_id, deployment_commit, run_value


def c5_control_session() -> tuple[requests.Session, bool]:
    """Return a credential-free GitHub API session regardless of ambient state."""

    session = requests.Session()
    session.trust_env = False
    session.headers.clear()
    session.headers.update(
        {
            "Accept": "application/vnd.github+json",
            "User-Agent": "O006-C140-companion-c5-static-readback/2026.08.31",
        }
    )
    return session, False


def c5_public_json(session: requests.Session, url: str) -> dict[str, Any]:
    """Read one GitHub control response anonymously with a strict byte cap."""

    parsed = urlparse(url)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").casefold() != "api.github.com"
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError("GitHub control URL is not admitted")
    retryable = {403, 404, 429, 500, 502, 503, 504}
    last_error: Exception | None = None
    for attempt in range(4):
        response: requests.Response | None = None
        try:
            response = session.get(
                url,
                timeout=120,
                allow_redirects=False,
                stream=True,
            )
            sent = {key.casefold() for key in response.request.headers}
            if sent.intersection({"authorization", "cookie", "proxy-authorization"}):
                raise RuntimeError("credential-bearing header appeared in control readback")
            if response.status_code != 200:
                status = response.status_code
                if status in retryable and attempt < 3:
                    response.close()
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise RuntimeError(f"GitHub control readback returned HTTP {status}")
            if response.url != url or response.history:
                raise RuntimeError("GitHub control readback redirected")
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                not declared.isdecimal() or int(declared) > MAX_CONTROL_JSON_BYTES
            ):
                raise RuntimeError("GitHub control response exceeds its byte cap")
            payload = bytearray()
            for chunk in response.iter_content(chunk_size=256 * 1024):
                if not chunk:
                    continue
                payload.extend(chunk)
                if len(payload) > MAX_CONTROL_JSON_BYTES:
                    raise RuntimeError("GitHub control response exceeds its byte cap")
            try:
                value = json.loads(bytes(payload).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise RuntimeError("GitHub control response is not UTF-8 JSON") from exc
            if not isinstance(value, dict):
                raise RuntimeError("GitHub control response is not an object")
            return value
        except requests.RequestException as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(0.5 * (attempt + 1))
        finally:
            if response is not None:
                response.close()
    raise RuntimeError(
        "GitHub control transport failed after bounded retries: "
        f"{type(last_error).__name__ if last_error else 'unknown'}"
    )


def c5_verify_file_streamed(
    row: dict[str, object], commit_id: str
) -> dict[str, object]:
    """Read one Pages file anonymously through an exact bounded stream."""

    path = str(row["path"])
    expected_bytes = int(row["bytes"])
    expected_sha256 = str(row["sha256"])
    if expected_bytes < 0 or expected_bytes > MAX_PUBLIC_FILE_BYTES:
        raise RuntimeError(f"public Pages file exceeds its admitted bound: {path}")
    url = engine.BASE_URL + quote(path, safe="/")
    expected_path = unquote(urlparse(url).path)
    retryable = {403, 404, 429, 500, 502, 503, 504}
    last_error: Exception | None = None
    for attempt in range(4):
        session = requests.Session()
        session.trust_env = False
        session.headers.clear()
        session.headers.update(
            {
                "Accept": "application/octet-stream",
                "User-Agent": "O006-C140-companion-c5-static-readback/2026.08.31",
            }
        )
        response: requests.Response | None = None
        try:
            response = session.get(
                url,
                params={"o006_commit": commit_id},
                timeout=180,
                allow_redirects=False,
                stream=True,
            )
            sent = {key.casefold() for key in response.request.headers}
            if sent.intersection({"authorization", "cookie", "proxy-authorization"}):
                raise RuntimeError("credential-bearing header appeared in Pages readback")
            if response.status_code != 200:
                status = response.status_code
                if status in retryable and attempt < 3:
                    response.close()
                    session.close()
                    time.sleep(0.5 * (attempt + 1))
                    continue
                raise RuntimeError(f"public Pages readback returned HTTP {status}: {path}")
            parsed = urlparse(response.url)
            if (
                parsed.scheme != "https"
                or (parsed.hostname or "").casefold() != "kokunoyumeto.github.io"
                or parsed.port not in (None, 443)
                or unquote(parsed.path) != expected_path
                or parse_qs(parsed.query, keep_blank_values=True)
                != {"o006_commit": [commit_id]}
                or parsed.fragment
                or parsed.username
                or parsed.password
                or response.history
            ):
                raise RuntimeError(f"public Pages file left its admitted URL: {path}")
            declared = response.headers.get("Content-Length")
            if declared is not None and (
                not declared.isdecimal() or int(declared) != expected_bytes
            ):
                raise RuntimeError(f"public Pages Content-Length differs: {path}")
            digest = hashlib.sha256()
            total = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > expected_bytes:
                    raise RuntimeError(f"public Pages file exceeds expected bytes: {path}")
                digest.update(chunk)
            if total != expected_bytes or digest.hexdigest() != expected_sha256:
                raise RuntimeError(f"public Pages byte identity differs: {path}")
            return {
                "bytes": expected_bytes,
                "http_status": 200,
                "path": path,
                "sha256": expected_sha256,
                "source": row["source"],
                "url": url,
            }
        except requests.RequestException as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(0.5 * (attempt + 1))
        finally:
            if response is not None:
                response.close()
            session.close()
    raise RuntimeError(
        f"public Pages transport failed after bounded retries: {path}: "
        f"{type(last_error).__name__ if last_error else 'unknown'}"
    )


def configure_engine() -> None:
    for url, label in ((engine.BASE_URL, "Pages base URL"), (engine.API, "GitHub API URL")):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RuntimeError(f"{label} must be static HTTPS")
    engine.RECEIPT = RECEIPT
    engine.SCHEMA = SCHEMA
    engine.CONTENT_HEADERS = {
        **engine.CONTENT_HEADERS,
        "User-Agent": "O006-C140-companion-c5-static-readback/2026.08.31",
    }
    engine.control_session = c5_control_session
    engine.public_json = c5_public_json
    engine.verify_file = c5_verify_file_streamed


def compute(
    snapshot: LocalSnapshot,
    commit_id: str,
    run_id: int,
    deployment_commit: str | None = None,
) -> bytes:
    deployment_commit = commit_id if deployment_commit is None else deployment_commit
    validate_pages_identity(commit_id, deployment_commit, run_id)
    content_witness = committed_content_witness(snapshot, commit_id)
    deployment_binding = deployment_content_binding(snapshot, commit_id, deployment_commit)
    configure_engine()
    previous_collection = engine.COLLECTION
    engine.COLLECTION = FrozenCollection(snapshot.collection_payload)  # type: ignore[assignment]
    try:
        base_payload = engine.compute(deployment_commit, run_id)
    finally:
        engine.COLLECTION = previous_collection
    base = json_payload(base_payload, "hardened Pages engine receipt")
    collection_info = snapshot.collection["collection"]
    files = base.get("files")
    partitions = base.get("partitions")
    if (
        base.get("schema") != SCHEMA
        or base.get("status") != "pass"
        or base.get("collection_receipt_bytes") != len(snapshot.collection_payload)
        or base.get("collection_receipt_sha256") != sha256(snapshot.collection_payload)
        or base.get("collection") != collection_info
        or not isinstance(files, list)
        or len(files) != collection_info["files"]
        or sum(int(row["bytes"]) for row in files if isinstance(row, dict))
        != collection_info["bytes"]
        or not isinstance(partitions, dict)
        or partitions.get("c140-original-companion")
        != {
            "bytes": snapshot.contract["companion_bytes"],
            "files": snapshot.contract["companion_files"],
        }
        or not isinstance(base.get("control_plane"), dict)
        or base["control_plane"].get("content_commit") != deployment_commit
        or base["control_plane"].get("api_authentication_used") is not False
    ):
        raise RuntimeError("Pages engine output differs from the frozen C5 snapshot")
    base["local_snapshot"] = {
        "collection_receipt": snapshot.contract["collection_receipt"],
        "collection_files": snapshot.contract["collection_files"],
        "collection_bytes": snapshot.contract["collection_bytes"],
        "collection_manifest_sha256": snapshot.contract[
            "collection_manifest_sha256"
        ],
    }
    base["c5_gate"] = snapshot.contract["c5_gate"]
    base["committed_content_readback"] = content_witness
    if deployment_commit != commit_id:
        # Preserve the original release/content linkage while naming the commit
        # whose workflow run and public Pages transaction were actually verified.
        base["control_plane"]["content_commit"] = commit_id
        base["control_plane"]["deployment_commit"] = deployment_commit
        base["deployment_content_binding"] = deployment_binding
    base["transaction_used_one_immutable_local_snapshot"] = True
    return engine.canonical_json(base)


def atomic_write(path: Path, payload: bytes) -> None:
    safe_directory(path.parent, "C5 Pages receipt directory")
    if path.exists() or path.is_symlink():
        safe_read_bytes(path, "C5 Pages receipt destination")
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
            "temporary C5 Pages receipt",
            expected_bytes=len(payload),
        ) != payload:
            raise RuntimeError("temporary C5 Pages receipt differs")
        safe_directory(path.parent, "C5 Pages receipt directory before replace")
        if safe_read_bytes(
            temporary,
            "temporary C5 Pages receipt before replace",
            expected_bytes=len(payload),
        ) != payload:
            raise RuntimeError("temporary C5 Pages receipt changed")
        os.replace(temporary, path)
        temporary = None
        if safe_read_bytes(
            path,
            "written C5 Pages receipt",
            expected_bytes=len(payload),
        ) != payload:
            raise RuntimeError("written C5 Pages receipt differs")
    except OSError as exc:
        raise RuntimeError("C5 Pages receipt write failed") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise RuntimeError("C5 Pages temporary receipt cleanup failed") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--contract-only", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit")
    parser.add_argument(
        "--deployment-commit",
        help="CI deployment commit; defaults to the original --commit content identity",
    )
    parser.add_argument("--run-id", type=int)
    args = parser.parse_args()

    snapshot = capture_snapshot()
    if args.contract_only:
        if args.commit or args.deployment_commit is not None or args.run_id is not None:
            raise RuntimeError("--contract-only does not accept remote identities")
        print(json.dumps(snapshot.contract, sort_keys=True))
        return

    if args.write:
        if not args.commit or args.run_id is None:
            raise RuntimeError("--write requires --commit and --run-id")
        commit_id, run_id = args.commit, args.run_id
        deployment_commit = (
            commit_id if args.deployment_commit is None else args.deployment_commit
        )
        validate_pages_identity(commit_id, deployment_commit, run_id)
    else:
        if args.commit or args.deployment_commit is not None or args.run_id is not None:
            raise RuntimeError("--check-only reads the pinned receipt identity")
        existing, _payload = object_file(RECEIPT, "C5 Pages receipt")
        commit_id, deployment_commit, run_id = pinned_pages_identity(existing)

    payload = compute(snapshot, commit_id, run_id, deployment_commit)
    if args.write:
        atomic_write(RECEIPT, payload)
        state = "written"
    else:
        if safe_read_bytes(RECEIPT, "C5 Pages receipt") != payload:
            raise RuntimeError("public C5 Pages receipt deterministic replay mismatch")
        state = "verified"
    value = json_payload(payload, "C5 Pages receipt output")
    print(
        json.dumps(
            {
                "bytes": value["collection"]["bytes"],
                "files": value["collection"]["files"],
                "mode": state,
                "receipt_sha256": sha256(payload),
                "status": "pass",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        truststore.inject_into_ssl()
        main()
    except Exception as exc:
        print(
            f"ERROR: C5 GitHub Pages verifier failed closed [{type(exc).__name__}]",
            file=sys.stderr,
        )
        raise SystemExit(1)
