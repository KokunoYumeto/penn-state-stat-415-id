#!/usr/bin/env python3
"""Anonymously verify the tagged first-unit GitHub release assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
TAG = "v2026.08.24.2of14"
COMMIT = "bb9269d36765f03c7991ad0c9adbce55814c2e9d"
PACKAGE = ROOT / "build" / "FIRST_UNIT_PACKAGE_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-24_FIRST_UNIT.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-GitHub-release-readback/1.0"})
    response = session.get(url, timeout=300)
    if response.status_code != 200:
        raise RuntimeError(f"anonymous GitHub release readback failed with HTTP {response.status_code}")
    return response.content


def compute() -> bytes:
    truststore.inject_into_ssl()
    package = json.loads(PACKAGE.read_text("utf-8"))
    rows = package.get("files") if isinstance(package, dict) else None
    if package.get("status") != "ready" or not isinstance(rows, list):
        raise RuntimeError("package receipt is not ready")
    expected = {str(row["filename"]): row for row in rows if isinstance(row, dict)}
    release = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"))
    if release.get("draft") or release.get("prerelease") or release.get("tag_name") != TAG:
        raise RuntimeError("GitHub release state differs")
    tag = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/tags/{TAG}"))
    if tag.get("object", {}).get("sha") != COMMIT:
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
        "schema": "o006.stat415.github-release-first-unit.v1", "status": "pass",
        "tag": TAG, "commit": COMMIT, "url": release.get("html_url"),
        "assets": verified, "asset_count": len(verified),
        "asset_bytes": sum(int(row["bytes"]) for row in verified),
        "anonymous_readback": True, "credential_access": False,
    }
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.write == args.check_only:
        raise RuntimeError("choose exactly one of --write or --check-only")
    payload = compute()
    if args.write:
        with tempfile.NamedTemporaryFile(dir=RECEIPT.parent, prefix=RECEIPT.name + ".", suffix=".tmp", delete=False) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(RECEIPT)
        state = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub release receipt differs")
        state = "verified"
    value = json.loads(payload)
    print(json.dumps({"mode": state, "status": value["status"], "assets": value["asset_count"], "bytes": value["asset_bytes"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
