#!/usr/bin/env python3
"""Anonymously verify the cumulative 8-of-14 GitHub commit and Pages reader."""

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
MANIFEST_TREE_PATH = "build/THROUGH_LESSON06_MANIFEST.csv"
READER_PREFIX = "build/html-id/"
RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_CHECKPOINT_RECEIPT_2026-08-25_THROUGH_LESSON06.json"
)
EXPECTED_PAGES_FILES = 52
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
RECEIPT_SCHEMA = "o006.stat415.github-through-lesson06-checkpoint.v1"
COVERAGE = {
    "complete_count": 8,
    "complete_documents": [
        "index", "Lesson00", "Lesson01", "Lesson02", "Lesson03",
        "Lesson04", "Lesson05", "Lesson06",
    ],
    "corpus_document_count": 14,
    "next_document": "Lesson07",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    temporary.replace(path)


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def tree_files(commit: str) -> list[str]:
    raw = git("ls-tree", "-r", "-z", "--name-only", commit)
    paths = [part.decode("utf-8") for part in raw.split(b"\0") if part]
    if not paths or len(paths) != len(set(paths)):
        raise RuntimeError("checkpoint tree inventory is empty or duplicated")
    return paths


def blob(commit: str, path: str) -> bytes:
    return git("show", f"{commit}:{path}")


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update(
        {
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "O006-STAT415-anonymous-readback/8.0",
        }
    )
    for attempt in range(6):
        response = session.get(url, timeout=300)
        if response.status_code == 200:
            return response.content
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 5:
            raise RuntimeError(
                f"anonymous readback failed with HTTP {response.status_code}: {url}"
            )
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def fetch_json(url: str) -> dict[str, object]:
    try:
        value = json.loads(fetch(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"public endpoint did not return UTF-8 JSON: {url}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"public endpoint did not return a JSON object: {url}")
    return value


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
        raise RuntimeError(
            f"expected {EXPECTED_PAGES_FILES} manifest rows, found {len(rows)}"
        )
    if [str(row["path"]) for row in rows] != sorted(seen, key=str.casefold):
        raise RuntimeError("reader manifest is not canonically ordered")
    return rows


def verify_pair(item: tuple[str, bytes, str]) -> dict[str, object]:
    path, expected, url = item
    actual = fetch(url)
    if actual != expected:
        raise RuntimeError(f"public bytes differ: {path}")
    return {"path": path, "bytes": len(actual), "sha256": sha256(actual), "url": url}


def compute(commit: str, workflow_run: int) -> bytes:
    truststore.inject_into_ssl()
    tree_sha = git("rev-parse", f"{commit}^{{tree}}").decode("ascii").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", tree_sha):
        raise RuntimeError("local checkpoint tree identity is invalid")

    public_commit = fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits/{commit}"
    )
    public_tree = public_commit.get("tree")
    if (
        public_commit.get("sha") != commit
        or not isinstance(public_tree, dict)
        or public_tree.get("sha") != tree_sha
    ):
        raise RuntimeError("public commit or tree differs from the local checkpoint")

    run = fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{workflow_run}"
    )
    if (
        run.get("head_sha") != commit
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
    ):
        raise RuntimeError("public workflow run did not succeed at the checkpoint")

    paths = tree_files(commit)
    committed_manifest = blob(commit, MANIFEST_TREE_PATH)
    declared = manifest_rows(committed_manifest)
    declared_by_path = {str(row["path"]): row for row in declared}

    raw_jobs: list[tuple[str, bytes, str]] = []
    pages_jobs: list[tuple[str, bytes, str]] = []
    reader_tree_paths: set[str] = set()
    for path in paths:
        data = blob(commit, path)
        raw_jobs.append(
            (
                path,
                data,
                f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit}/"
                f"{quote(path, safe='/')}",
            )
        )
        if path.startswith(READER_PREFIX):
            reader_path = path[len(READER_PREFIX) :]
            reader_tree_paths.add(reader_path)
            wanted = declared_by_path.get(reader_path)
            if wanted is None:
                raise RuntimeError(f"reader tree contains undeclared file: {reader_path}")
            if len(data) != wanted["bytes"] or sha256(data) != wanted["sha256"]:
                raise RuntimeError(f"reader commit blob differs from manifest: {reader_path}")
            pages_jobs.append(
                (
                    reader_path,
                    data,
                    f"{PAGES}/{quote(reader_path, safe='/')}?checkpoint={commit[:12]}",
                )
            )
    if reader_tree_paths != set(declared_by_path):
        raise RuntimeError("reader commit tree and manifest inventories differ")

    with ThreadPoolExecutor(max_workers=10) as pool:
        raw_rows = list(pool.map(verify_pair, raw_jobs))
        pages_rows = list(pool.map(verify_pair, pages_jobs))
    raw_rows.sort(key=lambda row: str(row["path"]).casefold())
    pages_rows.sort(key=lambda row: str(row["path"]).casefold())

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": "pass",
        "coverage": COVERAGE,
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "checkpoint_commit": commit,
        "commit_tree": {
            "sha": tree_sha,
            "files": len(raw_rows),
            "bytes": sum(int(row["bytes"]) for row in raw_rows),
            "all_blobs_read_back_at_exact_public_commit": True,
            "inventory": raw_rows,
        },
        "workflow": {
            "run_id": workflow_run,
            "url": run.get("html_url"),
            "status": "completed",
            "conclusion": "success",
        },
        "pages": {
            "url": f"{PAGES}/",
            "files": len(pages_rows),
            "bytes": sum(int(row["bytes"]) for row in pages_rows),
            "inventory": pages_rows,
        },
        "reader_manifest": {
            "path": MANIFEST_TREE_PATH,
            "rows": len(declared),
            "bytes": len(committed_manifest),
            "sha256": sha256(committed_manifest),
            "exact_commit_and_pages_match": True,
        },
        "translation_provenance": PROVENANCE,
        "anonymous_readback": True,
        "credentials_used": False,
    }
    return (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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
    if args.workflow_run <= 0:
        raise RuntimeError("--workflow-run must be positive")
    payload = compute(args.commit, args.workflow_run)
    if args.write:
        atomic_write(RECEIPT, payload)
        mode_name = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub checkpoint receipt differs")
        mode_name = "verified"
    value = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "status": value["status"],
                "commit": args.commit,
                "tree": value["commit_tree"]["sha"],
                "raw_files": value["commit_tree"]["files"],
                "pages_files": value["pages"]["files"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
