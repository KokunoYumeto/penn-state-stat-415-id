#!/usr/bin/env python3
"""Credential-free static-HTTPS readback for the exact C4 publication state commit.

The verifier derives its bounded file set from the named parent/commit pair,
reads each exact committed blob from Git, downloads the corresponding immutable
``raw.githubusercontent.com`` URL, and compares byte count and SHA-256.  It
never reads a credential and never launches a browser process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "00_control" / "GITHUB_STATE_READBACK_2026-08-29_C4_PUBLICATION_COMMIT.json"
REPOSITORY = "KokunoYumeto/penn-state-stat-415-id"
PARENT = "9b10b3e04b451232b1233d0b35cf31c3860d63db"
COMMIT = "cd9dcd763d55f864d21d517ff0f75abb50413e44"
EXPECTED_FILES = 25
SCHEMA = "o006.c140.c4.github-state-readback.v1"


def git(*arguments: str, binary: bool = False) -> bytes | str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8", errors="strict").strip()


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def changed_files() -> list[tuple[str, str]]:
    raw = git(
        "diff-tree",
        "--no-commit-id",
        "--name-status",
        "-z",
        "-r",
        PARENT,
        COMMIT,
        binary=True,
    )
    assert isinstance(raw, bytes)
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) % 2:
        raise RuntimeError("unexpected diff-tree record shape")
    rows: list[tuple[str, str]] = []
    for offset in range(0, len(fields), 2):
        status = fields[offset].decode("ascii")
        path = fields[offset + 1].decode("utf-8")
        if status not in {"A", "M"}:
            raise RuntimeError(f"unexpected change status {status!r} for {path!r}")
        if not path or path.startswith("/") or ".." in Path(path).parts:
            raise RuntimeError(f"unsafe changed path: {path!r}")
        rows.append((status, path))
    if len(rows) != EXPECTED_FILES:
        raise RuntimeError(f"expected {EXPECTED_FILES} changed files, found {len(rows)}")
    if len({path for _, path in rows}) != len(rows):
        raise RuntimeError("duplicate changed path")
    return sorted(rows, key=lambda row: row[1])


def tree_entry(path: str) -> tuple[str, str, bytes]:
    raw = git("ls-tree", "-z", COMMIT, "--", path, binary=True)
    assert isinstance(raw, bytes)
    records = [record for record in raw.split(b"\0") if record]
    if len(records) != 1:
        raise RuntimeError(f"expected one commit-tree entry for {path!r}")
    header, recorded_path = records[0].split(b"\t", 1)
    if recorded_path.decode("utf-8") != path:
        raise RuntimeError(f"commit-tree path mismatch for {path!r}")
    mode, object_type, blob_sha1 = header.decode("ascii").split(" ")
    if object_type != "blob" or mode not in {"100644", "100755"}:
        raise RuntimeError(f"unsupported commit-tree entry for {path!r}")
    payload = git("cat-file", "blob", blob_sha1, binary=True)
    assert isinstance(payload, bytes)
    return mode, blob_sha1, payload


def git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def download(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": "o006-c140-c4-state-static-readback/1.0",
        },
        method="GET",
    )
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status} for {url}")
                final_url = response.geturl()
                if not final_url.startswith("https://raw.githubusercontent.com/"):
                    raise RuntimeError(f"unexpected redirect target for {url}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"static HTTPS readback failed for {url}: {last_error}")


def build_receipt() -> dict[str, object]:
    resolved_commit = git("rev-parse", f"{COMMIT}^{{commit}}")
    resolved_parent = git("rev-parse", f"{COMMIT}^")
    if resolved_commit != COMMIT or resolved_parent != PARENT:
        raise RuntimeError("local commit ancestry differs from the fixed C4 publication-state boundary")

    files: list[dict[str, object]] = []
    total_bytes = 0
    aggregate = hashlib.sha256()
    for status, path in changed_files():
        mode, blob_sha1, local_payload = tree_entry(path)
        if git_blob_sha1(local_payload) != blob_sha1:
            raise RuntimeError(f"local committed blob identity mismatch for {path}")
        encoded_path = quote(path, safe="/")
        public_url = (
            f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/{encoded_path}"
        )
        public_payload = download(public_url)
        local_digest = sha256(local_payload)
        public_digest = sha256(public_payload)
        if len(public_payload) != len(local_payload) or public_digest != local_digest:
            raise RuntimeError(f"public byte mismatch for {path}")
        total_bytes += len(local_payload)
        aggregate.update(path.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(str(len(local_payload)).encode("ascii"))
        aggregate.update(b"\0")
        aggregate.update(local_digest.encode("ascii"))
        aggregate.update(b"\n")
        files.append(
            {
                "status": status,
                "path": path,
                "git_mode": mode,
                "git_blob_sha1": blob_sha1,
                "bytes": len(local_payload),
                "sha256": local_digest,
                "public_url": public_url,
                "public_bytes": len(public_payload),
                "public_sha256": public_digest,
                "match": True,
            }
        )

    return {
        "schema": SCHEMA,
        "kind": "credential_free_static_github_https_publication_state_commit_readback",
        "repository": REPOSITORY,
        "commit": COMMIT,
        "parent": PARENT,
        "change_scope": "files changed by the C4 publication state commit relative to the fixed parent",
        "credential_mode": "none",
        "credentials_read": False,
        "authorization_header_sent": False,
        "browser_used": False,
        "browser_processes_launched": False,
        "transport": "static HTTPS GET to immutable raw commit URLs",
        "local_authority": "exact committed Git blob bytes",
        "file_count": len(files),
        "total_bytes": total_bytes,
        "public_total_bytes": total_bytes,
        "aggregate_sha256": aggregate.hexdigest(),
        "all_match": True,
        "files": files,
    }


def serialized(receipt: dict[str, object]) -> bytes:
    return (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    receipt = build_receipt()
    expected = serialized(receipt)
    if args.write:
        RECEIPT.write_bytes(expected)
        print(
            f"C4 publication state commit readback written: {receipt['file_count']} files / "
            f"{receipt['total_bytes']} bytes / {sha256(expected)}"
        )
        return 0

    try:
        actual = RECEIPT.read_bytes()
    except OSError as exc:
        raise RuntimeError("C4 publication state commit readback receipt is unavailable") from exc
    if actual != expected:
        raise RuntimeError("C4 publication state commit readback receipt is stale or non-deterministic")
    print(
        f"C4 publication state commit readback check passed: {receipt['file_count']} files / "
        f"{receipt['total_bytes']} bytes / {sha256(actual)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
