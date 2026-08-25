#!/usr/bin/env python3
"""Anonymously verify the cumulative 5-of-14 GitHub commit and Pages reader."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
PAGES = "https://kokunoyumeto.github.io/penn-state-stat-415-id"
RECEIPT = ROOT / "00_control" / "GITHUB_PUBLICATION_RECEIPT_2026-08-25_THROUGH_LESSON03.json"
MANIFEST = ROOT / "build" / "THROUGH_LESSON03_MANIFEST.csv"
MANIFEST_TREE_PATH = "build/THROUGH_LESSON03_MANIFEST.csv"
READER_PREFIX = "build/html-id/"
EXPECTED_PAGES_FILES = 32
COMPLETE_DOCUMENTS = ("index", "Lesson00", "Lesson01", "Lesson02", "Lesson03")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    temporary.replace(path)


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    return result.stdout


def tree_files(commit: str) -> list[str]:
    raw = git("ls-tree", "-r", "-z", "--name-only", commit)
    paths = [part.decode("utf-8") for part in raw.split(b"\0") if part]
    if not paths or len(paths) != len(set(paths)):
        raise RuntimeError("release commit tree inventory is empty or duplicated")
    return paths


def blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}")


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-anonymous-readback/5.0"})
    for attempt in range(5):
        response = session.get(url, timeout=180, headers={"Cache-Control": "no-cache"})
        if response.status_code == 200:
            return response.content
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
            raise RuntimeError(f"anonymous readback failed with HTTP {response.status_code}: {url}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def verify_pair(item: tuple[str, bytes, str]) -> dict[str, object]:
    path, expected, url = item
    actual = fetch(url)
    if actual != expected:
        raise RuntimeError(f"public bytes differ: {path}")
    return {"path": path, "bytes": len(actual), "sha256": sha256(actual), "url": url}


def manifest_rows(payload: bytes) -> list[dict[str, object]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("reader manifest is not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != ["relative_path", "bytes", "sha256"]:
        raise RuntimeError("reader manifest columns differ")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in reader:
        path = str(raw.get("relative_path", ""))
        size_text = str(raw.get("bytes", ""))
        digest = str(raw.get("sha256", ""))
        if (
            not path
            or path.startswith("/")
            or "\\" in path
            or any(part in ("", ".", "..") for part in path.split("/"))
            or path in seen
            or not size_text.isdigit()
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise RuntimeError(f"reader manifest row is invalid: {path!r}")
        seen.add(path)
        rows.append({"path": path, "bytes": int(size_text), "sha256": digest})
    if len(rows) != EXPECTED_PAGES_FILES:
        raise RuntimeError(f"expected {EXPECTED_PAGES_FILES} reader manifest rows, found {len(rows)}")
    if [str(row["path"]) for row in rows] != sorted(seen, key=str.casefold):
        raise RuntimeError("reader manifest is not canonically ordered")
    return rows


def workflow_metadata(workflow_run: int) -> dict[str, object]:
    result = subprocess.run(
        [
            "gh", "run", "view", str(workflow_run), "--json",
            "databaseId,headSha,status,conclusion,url",
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        raise RuntimeError("GitHub workflow metadata is not an object")
    return value


def compute(commit_sha: str, workflow_run: int) -> bytes:
    truststore.inject_into_ssl()
    tree_sha = git("rev-parse", f"{commit_sha}^{{tree}}").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
        raise RuntimeError("local checkpoint commit omits its tree identity")
    local_paths = tree_files(commit_sha)
    run = workflow_metadata(workflow_run)
    if run.get("headSha") != commit_sha or run.get("status") != "completed" or run.get("conclusion") != "success":
        raise RuntimeError("public workflow run did not succeed at the checkpoint commit")

    local_manifest = MANIFEST.read_bytes()
    committed_manifest = blob(commit_sha, MANIFEST_TREE_PATH)
    if committed_manifest != local_manifest:
        raise RuntimeError("local reader manifest differs from the checkpoint commit")
    declared = manifest_rows(committed_manifest)
    declared_by_path = {str(row["path"]): row for row in declared}

    raw_jobs: list[tuple[str, bytes, str]] = []
    pages_jobs: list[tuple[str, bytes, str]] = []
    reader_tree_paths: set[str] = set()
    for path in local_paths:
        data = blob(commit_sha, path)
        raw_jobs.append(
            (path, data, f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit_sha}/{quote(path, safe='/')}")
        )
        if path.startswith(READER_PREFIX):
            reader_path = path[len(READER_PREFIX):]
            reader_tree_paths.add(reader_path)
            wanted = declared_by_path.get(reader_path)
            if wanted is None:
                raise RuntimeError(f"reader tree contains an undeclared file: {reader_path}")
            if len(data) != wanted["bytes"] or sha256(data) != wanted["sha256"]:
                raise RuntimeError(f"reader commit blob differs from manifest: {reader_path}")
            pages_jobs.append((reader_path, data, f"{PAGES}/{quote(reader_path, safe='/')}"))
    if reader_tree_paths != set(declared_by_path) or len(pages_jobs) != EXPECTED_PAGES_FILES:
        raise RuntimeError("reader commit tree and 32-row manifest inventories differ")

    with ThreadPoolExecutor(max_workers=10) as pool:
        raw_rows = list(pool.map(verify_pair, raw_jobs))
        pages_rows = list(pool.map(verify_pair, pages_jobs))
    raw_rows.sort(key=lambda row: str(row["path"]).casefold())
    pages_rows.sort(key=lambda row: str(row["path"]).casefold())
    receipt = {
        "schema": "o006.stat415.github-through-lesson03-publication.v1",
        "status": "pass",
        "coverage": {
            "complete_documents": list(COMPLETE_DOCUMENTS),
            "complete_count": 5,
            "corpus_document_count": 14,
            "next_document": "Lesson04",
        },
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "visibility": "public",
        "release_commit": commit_sha,
        "commit_tree": {
            "sha": tree_sha,
            "files": len(local_paths),
            "all_blobs_read_back_at_exact_public_commit": True,
        },
        "workflow": {
            "run_id": workflow_run,
            "url": run.get("url"),
            "status": "completed",
            "conclusion": "success",
        },
        "pages": {
            "url": f"{PAGES}/",
            "files": len(pages_rows),
            "bytes": sum(int(row["bytes"]) for row in pages_rows),
            "inventory": pages_rows,
        },
        "raw_commit": {
            "files": len(raw_rows),
            "bytes": sum(int(row["bytes"]) for row in raw_rows),
            "inventory": raw_rows,
        },
        "reader_manifest": {
            "path": MANIFEST_TREE_PATH,
            "rows": len(declared),
            "bytes": len(committed_manifest),
            "sha256": sha256(committed_manifest),
            "exact_commit_and_pages_match": True,
        },
        "credential_access": {
            "workflow_metadata_via_github_cli": True,
            "public_byte_readback": False,
        },
        "anonymous_readback": True,
    }
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--workflow-run", required=True, type=int)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise RuntimeError("--commit must be a full lowercase SHA-1")
    payload = compute(args.commit, args.workflow_run)
    if args.write:
        atomic_write(RECEIPT, payload)
        mode_name = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub publication receipt differs")
        mode_name = "verified"
    value = json.loads(payload)
    print(json.dumps({"mode": mode_name, "status": value["status"], "commit": args.commit, "tree": value["commit_tree"]["sha"], "raw_files": value["raw_commit"]["files"], "pages_files": value["pages"]["files"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
