#!/usr/bin/env python3
"""Anonymously verify the first-unit GitHub commit, Pages bytes, and workflow."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
from urllib.parse import quote

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
DEFAULT_COMMIT = "f449acfced2baabf9b2436afa77d8995dd0679c2"
DEFAULT_WORKFLOW_RUN = 32701430336
PAGES = "https://kokunoyumeto.github.io/penn-state-stat-415-id"
RECEIPT = ROOT / "00_control" / "GITHUB_PUBLICATION_RECEIPT_2026-08-24_FIRST_UNIT.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    temporary.replace(path)


def git(*args: str) -> bytes:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout


def tree_files(commit: str, expected_files: int | None) -> list[str]:
    raw = git("ls-tree", "-rz", "--name-only", commit)
    paths = [part.decode("utf-8") for part in raw.split(b"\0") if part]
    if len(paths) != len(set(paths)) or (expected_files is not None and len(paths) != expected_files):
        raise RuntimeError("release commit tree count differs")
    return paths


def blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}")


def fetch(session: requests.Session, url: str) -> bytes:
    for attempt in range(4):
        response = session.get(url, timeout=120, headers={"Cache-Control": "no-cache"})
        if response.status_code == 200:
            return response.content
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 3:
            raise RuntimeError(f"anonymous readback failed with HTTP {response.status_code}: {url}")
        time.sleep(2 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def verify_pair(item: tuple[str, bytes, str]) -> dict[str, object]:
    path, expected, url = item
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-anonymous-readback/1.0"})
    actual = fetch(session, url)
    if actual != expected:
        raise RuntimeError(f"public bytes differ: {path}")
    return {"path": path, "bytes": len(actual), "sha256": sha256(actual), "url": url}


def compute(release_commit: str, workflow_run: int, expected_files: int | None) -> bytes:
    truststore.inject_into_ssl()
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-anonymous-readback/1.0"})
    repository = json.loads(fetch(session, f"https://api.github.com/repos/{OWNER}/{REPO}"))
    if repository.get("private") is not False or repository.get("default_branch") != "main":
        raise RuntimeError("public repository metadata differs")
    commit = json.loads(fetch(session, f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{release_commit}"))
    if commit.get("sha") != release_commit:
        raise RuntimeError("public commit identity differs")
    run = json.loads(fetch(session, f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{workflow_run}"))
    if run.get("head_sha") != release_commit or run.get("status") != "completed" or run.get("conclusion") != "success":
        raise RuntimeError("public workflow run did not succeed at the release commit")

    paths = tree_files(release_commit, expected_files)
    raw_jobs: list[tuple[str, bytes, str]] = []
    pages_jobs: list[tuple[str, bytes, str]] = []
    for path in paths:
        data = blob(release_commit, path)
        raw_url = f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{release_commit}/{quote(path, safe='/')}"
        raw_jobs.append((path, data, raw_url))
        prefix = "build/html-id/"
        if path.startswith(prefix):
            reader_path = path[len(prefix):]
            pages_jobs.append((reader_path, data, f"{PAGES}/{quote(reader_path, safe='/')}"))
    if len(pages_jobs) != 19:
        raise RuntimeError("release commit reader path count differs")

    with ThreadPoolExecutor(max_workers=12) as pool:
        raw_rows = list(pool.map(verify_pair, raw_jobs))
        pages_rows = list(pool.map(verify_pair, pages_jobs))
    raw_rows.sort(key=lambda row: str(row["path"]).casefold())
    pages_rows.sort(key=lambda row: str(row["path"]).casefold())
    receipt = {
        "schema": "o006.stat415.github-first-unit-publication.v1", "status": "pass",
        "repository": f"https://github.com/{OWNER}/{REPO}", "visibility": "public",
        "release_commit": release_commit,
        "workflow": {"run_id": workflow_run, "url": run.get("html_url"), "status": "completed", "conclusion": "success"},
        "pages": {"url": f"{PAGES}/", "files": len(pages_rows), "bytes": sum(int(row["bytes"]) for row in pages_rows), "inventory": pages_rows},
        "raw_commit": {"files": len(raw_rows), "bytes": sum(int(row["bytes"]) for row in raw_rows), "inventory": raw_rows},
        "credential_access": False, "anonymous_readback": True,
    }
    return (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit", default=DEFAULT_COMMIT)
    parser.add_argument("--workflow-run", type=int, default=DEFAULT_WORKFLOW_RUN)
    parser.add_argument("--expected-files", type=int)
    args = parser.parse_args()
    if args.write == args.check_only:
        raise RuntimeError("choose exactly one of --write or --check-only")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise RuntimeError("--commit must be a full lowercase SHA-1")
    payload = compute(args.commit, args.workflow_run, args.expected_files)
    if args.write:
        atomic_write(RECEIPT, payload)
        state = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub publication receipt differs")
        state = "verified"
    receipt = json.loads(payload)
    print(json.dumps({"mode": state, "status": receipt["status"], "commit": args.commit, "raw_files": receipt["raw_commit"]["files"], "pages_files": receipt["pages"]["files"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
