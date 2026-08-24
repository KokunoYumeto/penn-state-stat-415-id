#!/usr/bin/env python3
"""Anonymously verify the cumulative 3-of-14 GitHub commit and Pages reader."""

from __future__ import annotations

import argparse
import hashlib
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
RECEIPT = ROOT / "00_control" / "GITHUB_PUBLICATION_RECEIPT_2026-08-24_THROUGH_LESSON01.json"
MANIFEST = ROOT / "build" / "THROUGH_LESSON01_MANIFEST.csv"


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
    raw = git("ls-tree", "-rz", "--name-only", commit)
    paths = [part.decode("utf-8") for part in raw.split(b"\0") if part]
    if not paths or len(paths) != len(set(paths)):
        raise RuntimeError("release commit tree inventory is empty or duplicated")
    return paths


def blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}")


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-anonymous-readback/3.0"})
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


def compute(commit_sha: str, workflow_run: int) -> bytes:
    truststore.inject_into_ssl()
    repository = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}"))
    if repository.get("private") is not False or repository.get("default_branch") != "main":
        raise RuntimeError("public repository metadata differs")
    commit = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{commit_sha}"))
    if commit.get("sha") != commit_sha:
        raise RuntimeError("public commit identity differs")
    run = json.loads(fetch(f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{workflow_run}"))
    if run.get("head_sha") != commit_sha or run.get("status") != "completed" or run.get("conclusion") != "success":
        raise RuntimeError("public workflow run did not succeed at the checkpoint commit")

    raw_jobs: list[tuple[str, bytes, str]] = []
    pages_jobs: list[tuple[str, bytes, str]] = []
    for path in tree_files(commit_sha):
        data = blob(commit_sha, path)
        raw_jobs.append(
            (path, data, f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit_sha}/{quote(path, safe='/')}")
        )
        prefix = "build/html-id/"
        if path.startswith(prefix):
            reader_path = path[len(prefix):]
            pages_jobs.append((reader_path, data, f"{PAGES}/{quote(reader_path, safe='/')}"))
    if len(pages_jobs) != 28:
        raise RuntimeError(f"expected 28 Pages files, found {len(pages_jobs)}")

    with ThreadPoolExecutor(max_workers=10) as pool:
        raw_rows = list(pool.map(verify_pair, raw_jobs))
        pages_rows = list(pool.map(verify_pair, pages_jobs))
    raw_rows.sort(key=lambda row: str(row["path"]).casefold())
    pages_rows.sort(key=lambda row: str(row["path"]).casefold())
    receipt = {
        "schema": "o006.stat415.github-through-lesson01-publication.v1",
        "status": "pass",
        "coverage": {"complete_documents": ["index", "Lesson00", "Lesson01"], "complete_count": 3, "corpus_document_count": 14},
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "visibility": "public",
        "release_commit": commit_sha,
        "workflow": {"run_id": workflow_run, "url": run.get("html_url"), "status": "completed", "conclusion": "success"},
        "pages": {"url": f"{PAGES}/", "files": len(pages_rows), "bytes": sum(int(row["bytes"]) for row in pages_rows), "inventory": pages_rows},
        "raw_commit": {"files": len(raw_rows), "bytes": sum(int(row["bytes"]) for row in raw_rows), "inventory": raw_rows},
        "reader_manifest": {"bytes": MANIFEST.stat().st_size, "sha256": sha256(MANIFEST.read_bytes())},
        "credential_access": False,
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
    print(json.dumps({"mode": mode_name, "status": value["status"], "commit": args.commit, "raw_files": value["raw_commit"]["files"], "pages_files": value["pages"]["files"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
