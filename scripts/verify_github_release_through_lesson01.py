#!/usr/bin/env python3
"""Anonymously verify the cumulative 3-of-14 tagged GitHub release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
TAG = "v2026.08.24.3of14"
PACKAGE = ROOT / "build" / "THROUGH_LESSON01_PACKAGE_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-24_THROUGH_LESSON01.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-GitHub-release-readback/3.0"})
    for attempt in range(5):
        response = session.get(url, timeout=300, headers={"Cache-Control": "no-cache"})
        if response.status_code == 200:
            return response.content
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
            raise RuntimeError(f"anonymous GitHub release readback failed with HTTP {response.status_code}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def compute(commit_sha: str) -> bytes:
    truststore.inject_into_ssl()
    package = json.loads(PACKAGE.read_text("utf-8"))
    rows = package.get("files") if isinstance(package, dict) else None
    if package.get("status") != "ready" or not isinstance(rows, list):
        raise RuntimeError("package receipt is not ready")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    if len(expected) != len(rows):
        raise RuntimeError("package receipt contains duplicate filenames")
    release = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"))
    if release.get("draft") or release.get("prerelease") or release.get("tag_name") != TAG:
        raise RuntimeError("GitHub release state differs")
    tag = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/tags/{TAG}"))
    if tag.get("object", {}).get("sha") != commit_sha:
        raise RuntimeError("GitHub release tag does not point to the checkpoint commit")
    assets = {str(row.get("name")): row for row in release.get("assets") or [] if isinstance(row, dict)}
    if set(assets) != set(expected):
        raise RuntimeError("GitHub release asset names differ")

    def verify(filename: str) -> dict[str, object]:
        asset = assets[filename]
        data = fetch(str(asset["browser_download_url"]))
        wanted = expected[filename]
        if len(data) != wanted["bytes"] or sha256(data) != wanted["sha256"]:
            raise RuntimeError(f"GitHub release asset differs: {filename}")
        return {"name": filename, "bytes": len(data), "sha256": sha256(data), "url": asset["browser_download_url"]}

    with ThreadPoolExecutor(max_workers=8) as pool:
        verified = list(pool.map(verify, expected))
    receipt = {
        "schema": "o006.stat415.github-release-through-lesson01.v1",
        "status": "pass",
        "coverage": {"complete_documents": ["index", "Lesson00", "Lesson01"], "complete_count": 3, "corpus_document_count": 14},
        "tag": TAG,
        "commit": commit_sha,
        "url": release.get("html_url"),
        "assets": verified,
        "asset_count": len(verified),
        "asset_bytes": sum(int(row["bytes"]) for row in verified),
        "anonymous_readback": True,
        "credential_access": False,
    }
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise RuntimeError("--commit must be a full lowercase SHA-1")
    payload = compute(args.commit)
    if args.write:
        with tempfile.NamedTemporaryFile(dir=RECEIPT.parent, prefix=RECEIPT.name + ".", suffix=".tmp", delete=False) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(RECEIPT)
        mode_name = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub release receipt differs")
        mode_name = "verified"
    value = json.loads(payload)
    print(json.dumps({"mode": mode_name, "status": value["status"], "assets": value["asset_count"], "bytes": value["asset_bytes"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
