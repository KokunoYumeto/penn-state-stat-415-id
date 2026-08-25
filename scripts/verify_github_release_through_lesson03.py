#!/usr/bin/env python3
"""Anonymously verify the cumulative 5-of-14 tagged GitHub release."""

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
TAG = "v2026.08.25.5of14"
PACKAGE = ROOT / "build" / "THROUGH_LESSON03_PACKAGE_RECEIPT.json"
PACKAGE_TREE_PATH = "build/THROUGH_LESSON03_PACKAGE_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-25_THROUGH_LESSON03.json"
PACKAGE_SCHEMA = "o006.stat415.through-lesson03-package.v1"
COMPLETE_DOCUMENTS = ("index", "Lesson00", "Lesson01", "Lesson02", "Lesson03")
EXACT_FILES = (
    "00_stat415-id-through-lesson03-offline-reader.zip",
    "10_stat415-id-through-lesson03-source-backend.zip",
    "20_THROUGH_LESSON03_RELEASE_NOTES.md",
    "30_THROUGH_LESSON03_LICENSE.md",
    "40_THROUGH_LESSON03_QA_RECEIPT.json",
    "41_THROUGH_LESSON03_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON03_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON03.txt",
    "60_THROUGH_LESSON03_RELEASE_ROOT_RECEIPT.json",
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-GitHub-release-readback/5.0"})
    for attempt in range(5):
        response = session.get(url, timeout=300, headers={"Cache-Control": "no-cache"})
        if response.status_code == 200:
            return response.content
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
            raise RuntimeError(f"anonymous GitHub release readback failed with HTTP {response.status_code}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def resolve_tag_commit(tag_ref: dict[str, object]) -> str:
    obj = tag_ref.get("object")
    if not isinstance(obj, dict):
        raise RuntimeError("GitHub tag reference omits its object")
    kind = obj.get("type")
    object_sha = str(obj.get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", object_sha):
        raise RuntimeError("GitHub tag reference omits a full object SHA")
    if kind == "commit":
        return object_sha
    if kind != "tag":
        raise RuntimeError("GitHub tag reference has an unsupported object type")
    annotated = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/git/tags/{object_sha}"))
    target = annotated.get("object")
    if not isinstance(target, dict) or target.get("type") != "commit":
        raise RuntimeError("annotated GitHub tag does not point directly to a commit")
    commit_sha = str(target.get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise RuntimeError("annotated GitHub tag omits its commit SHA")
    return commit_sha


def load_package(commit_sha: str) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    local_payload = PACKAGE.read_bytes()
    public_payload = fetch(
        f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit_sha}/{PACKAGE_TREE_PATH}"
    )
    if public_payload != local_payload:
        raise RuntimeError("local package receipt differs from the tagged public commit")
    package = json.loads(local_payload.decode("utf-8"))
    rows = package.get("files") if isinstance(package, dict) else None
    coverage = package.get("coverage") if isinstance(package, dict) else None
    if (
        not isinstance(package, dict)
        or package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("upload_order") != list(EXACT_FILES)
        or package.get("file_count") != len(EXACT_FILES)
        or not isinstance(rows, list)
        or not isinstance(coverage, dict)
        or coverage.get("complete_documents") != list(COMPLETE_DOCUMENTS)
        or coverage.get("complete_count") != 5
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson04"
    ):
        raise RuntimeError("package receipt is not the exact ready 5-of-14 boundary")
    expected: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("package receipt contains a non-object file row")
        filename = str(row.get("filename", ""))
        if (
            filename in expected
            or filename not in EXACT_FILES
            or not isinstance(row.get("bytes"), int)
            or int(row["bytes"]) < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", "")))
        ):
            raise RuntimeError(f"package receipt has an invalid file row: {filename!r}")
        expected[filename] = row
    if set(expected) != set(EXACT_FILES):
        raise RuntimeError("package receipt file names differ")
    if package.get("total_bytes") != sum(int(expected[name]["bytes"]) for name in EXACT_FILES):
        raise RuntimeError("package receipt aggregate bytes differ")
    return package, expected


def compute(commit_sha: str) -> bytes:
    truststore.inject_into_ssl()
    commit = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{commit_sha}"))
    if commit.get("sha") != commit_sha:
        raise RuntimeError("public checkpoint commit identity differs")
    release = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{TAG}"))
    if (
        release.get("draft") is not False
        or release.get("prerelease") is not False
        or release.get("tag_name") != TAG
        or not release.get("published_at")
    ):
        raise RuntimeError("GitHub release is not the exact published checkpoint")
    tag = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/tags/{TAG}"))
    if resolve_tag_commit(tag) != commit_sha:
        raise RuntimeError("GitHub release tag does not point to the checkpoint commit")
    package, expected = load_package(commit_sha)

    asset_rows = release.get("assets")
    if not isinstance(asset_rows, list):
        raise RuntimeError("GitHub release asset inventory is absent")
    assets = {str(row.get("name")): row for row in asset_rows if isinstance(row, dict)}
    if len(assets) != len(asset_rows) or set(assets) != set(EXACT_FILES):
        raise RuntimeError("GitHub release asset names differ")

    def verify(filename: str) -> dict[str, object]:
        asset = assets[filename]
        wanted = expected[filename]
        if asset.get("state") != "uploaded" or int(asset.get("size", -1)) != int(wanted["bytes"]):
            raise RuntimeError(f"GitHub release asset metadata differs: {filename}")
        url = str(asset.get("browser_download_url", ""))
        if not url:
            raise RuntimeError(f"GitHub release asset omits its download URL: {filename}")
        data = fetch(url)
        digest = sha256(data)
        if len(data) != wanted["bytes"] or digest != wanted["sha256"]:
            raise RuntimeError(f"GitHub release asset differs: {filename}")
        return {"name": filename, "bytes": len(data), "sha256": digest, "url": url}

    with ThreadPoolExecutor(max_workers=8) as pool:
        by_name = {row["name"]: row for row in pool.map(verify, EXACT_FILES)}
    verified = [by_name[name] for name in EXACT_FILES]
    receipt = {
        "schema": "o006.stat415.github-release-through-lesson03.v1",
        "status": "pass",
        "coverage": package["coverage"],
        "tag": TAG,
        "commit": commit_sha,
        "url": release.get("html_url"),
        "published_at": release.get("published_at"),
        "package_receipt": {
            "path": PACKAGE_TREE_PATH,
            "bytes": PACKAGE.stat().st_size,
            "sha256": sha256(PACKAGE.read_bytes()),
            "exact_tagged_commit_match": True,
        },
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
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
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
    print(json.dumps({"mode": mode_name, "status": value["status"], "tag": value["tag"], "commit": value["commit"], "assets": value["asset_count"], "bytes": value["asset_bytes"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
