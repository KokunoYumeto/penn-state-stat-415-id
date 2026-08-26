#!/usr/bin/env python3
"""Anonymously verify the complete 14-of-14 GitHub commit and Pages reader.

The commit and successful workflow run are supplied explicitly.  Verification
uses only public HTTPS endpoints: no credential and no local Git command is
used.  Every public commit blob is checked against the Git object identity
published by the recursive tree API; the 106 reader files are additionally
checked against the committed SHA-256 manifest and the deployed Pages bytes.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
import threading
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
MANIFEST_TREE_PATH = "build/THROUGH_LESSON12_MANIFEST.csv"
LOCAL_MANIFEST = ROOT / MANIFEST_TREE_PATH
READER_PREFIX = "build/html-id/"
RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_CHECKPOINT_RECEIPT_2026-08-26_THROUGH_LESSON12.json"
)
EXPECTED_PAGES_FILES = 106
EXPECTED_READER_BYTES = 17_614_553
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
RECEIPT_SCHEMA = "o006.stat415.github-through-lesson12-checkpoint.v1"
COVERAGE = {
    "complete_count": 14,
    "complete_documents": ["index", *[f"Lesson{i:02d}" for i in range(13)]],
    "corpus_document_count": 14,
    "next_document": None,
    "pending_documents": [],
}
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "O006-STAT415-anonymous-readback/14.0",
    "X-GitHub-Api-Version": "2022-11-28",
}
THREAD_LOCAL = threading.local()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    temporary.replace(path)


def session() -> requests.Session:
    current = getattr(THREAD_LOCAL, "session", None)
    if current is None:
        current = requests.Session()
        current.headers.update(HEADERS)
        THREAD_LOCAL.session = current
    return current


def fetch(url: str) -> tuple[bytes, str]:
    for attempt in range(6):
        response = session().get(url, timeout=300)
        if response.status_code == 200:
            return response.content, response.url
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 5:
            raise RuntimeError(
                f"anonymous readback failed with HTTP {response.status_code}: {url}"
            )
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def fetch_json(url: str) -> dict[str, object]:
    payload, _ = fetch(url)
    try:
        value = json.loads(payload.decode("utf-8"))
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
    if sum(int(row["bytes"]) for row in rows) != EXPECTED_READER_BYTES:
        raise RuntimeError("reader manifest byte total differs")
    return rows


def local_contract() -> dict[str, object]:
    payload = LOCAL_MANIFEST.read_bytes()
    rows = manifest_rows(payload)
    for row in rows:
        path = ROOT / "build" / "html-id" / str(row["path"])
        data = path.read_bytes()
        if len(data) != row["bytes"] or sha256(data) != row["sha256"]:
            raise RuntimeError(f"local reader file differs from manifest: {row['path']}")
    return {
        "manifest_bytes": len(payload),
        "manifest_sha256": sha256(payload),
        "reader_bytes": sum(int(row["bytes"]) for row in rows),
        "reader_files": len(rows),
    }


def public_tree(commit: str) -> tuple[str, list[dict[str, str]]]:
    commit_value = fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/commits/{commit}"
    )
    tree_value = commit_value.get("tree")
    if (
        commit_value.get("sha") != commit
        or not isinstance(tree_value, dict)
        or not isinstance(tree_value.get("sha"), str)
    ):
        raise RuntimeError("public commit identity is absent or differs")
    tree_sha = str(tree_value["sha"])
    value = fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/trees/{tree_sha}?recursive=1"
    )
    if value.get("sha") != tree_sha or value.get("truncated") is not False:
        raise RuntimeError("public recursive tree is absent, truncated, or differs")
    raw_entries = value.get("tree")
    if not isinstance(raw_entries, list):
        raise RuntimeError("public recursive tree has no entries")
    blobs: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in raw_entries:
        if not isinstance(entry, dict) or entry.get("type") != "blob":
            continue
        path = entry.get("path")
        object_id = entry.get("sha")
        if (
            not isinstance(path, str)
            or not isinstance(object_id, str)
            or not re.fullmatch(r"[0-9a-f]{40}", object_id)
            or path in seen
        ):
            raise RuntimeError("public recursive tree contains a malformed blob")
        seen.add(path)
        blobs.append({"path": path, "git_blob_sha1": object_id})
    if not blobs:
        raise RuntimeError("public commit tree contains no blobs")
    blobs.sort(key=lambda item: item["path"].casefold())
    return tree_sha, blobs


def verify_public_blob(job: tuple[str, str, str]) -> tuple[dict[str, object], bytes | None]:
    commit, path, expected_git_sha = job
    url = (
        f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit}/"
        f"{quote(path, safe='/')}"
    )
    data, final_url = fetch(url)
    if git_blob_sha1(data) != expected_git_sha:
        raise RuntimeError(f"raw public blob differs from the commit tree: {path}")
    row = {
        "path": path,
        "bytes": len(data),
        "git_blob_sha1": expected_git_sha,
        "sha256": sha256(data),
        "url": url,
        "final_url": final_url,
    }
    return row, data if path == MANIFEST_TREE_PATH or path.startswith(READER_PREFIX) else None


def verify_pages(job: tuple[str, bytes, dict[str, object], str]) -> dict[str, object]:
    path, committed_data, declared, commit = job
    url = f"{PAGES}/{quote(path, safe='/')}?checkpoint={commit[:12]}"
    public, final_url = fetch(url)
    if public != committed_data:
        raise RuntimeError(f"Pages bytes differ from the exact commit: {path}")
    identity = {"bytes": len(public), "sha256": sha256(public)}
    if identity != {"bytes": declared["bytes"], "sha256": declared["sha256"]}:
        raise RuntimeError(f"Pages bytes differ from the committed manifest: {path}")
    return {"path": path, **identity, "url": url, "final_url": final_url}


def compute(commit: str, workflow_run: int) -> bytes:
    truststore.inject_into_ssl()
    local = local_contract()
    tree_sha, blobs = public_tree(commit)
    paths = {item["path"] for item in blobs}
    if MANIFEST_TREE_PATH not in paths:
        raise RuntimeError("public commit omits the 14-of-14 reader manifest")

    jobs = [(commit, item["path"], item["git_blob_sha1"]) for item in blobs]
    with ThreadPoolExecutor(max_workers=10) as pool:
        verified = list(pool.map(verify_public_blob, jobs))
    raw_rows = [item[0] for item in verified]
    retained = {item[0]["path"]: item[1] for item in verified if item[1] is not None}

    committed_manifest = retained.get(MANIFEST_TREE_PATH)
    if committed_manifest is None:
        raise RuntimeError("verified commit manifest bytes were not retained")
    declared = manifest_rows(committed_manifest)
    if {
        path[len(READER_PREFIX) :]
        for path in paths
        if path.startswith(READER_PREFIX)
    } != {str(row["path"]) for row in declared}:
        raise RuntimeError("reader commit tree and manifest inventories differ")
    if {
        "manifest_bytes": len(committed_manifest),
        "manifest_sha256": sha256(committed_manifest),
        "reader_bytes": sum(int(row["bytes"]) for row in declared),
        "reader_files": len(declared),
    } != local:
        raise RuntimeError("public committed reader manifest differs from local boundary")

    page_jobs: list[tuple[str, bytes, dict[str, object], str]] = []
    for row in declared:
        reader_path = str(row["path"])
        data = retained.get(READER_PREFIX + reader_path)
        if data is None:
            raise RuntimeError(f"verified commit reader bytes were not retained: {reader_path}")
        if len(data) != row["bytes"] or sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader commit blob differs from manifest: {reader_path}")
        page_jobs.append((reader_path, data, row, commit))
    with ThreadPoolExecutor(max_workers=10) as pool:
        pages_rows = list(pool.map(verify_pages, page_jobs))
    pages_rows.sort(key=lambda row: str(row["path"]).casefold())

    run = fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/actions/runs/{workflow_run}"
    )
    if (
        run.get("head_sha") != commit
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
    ):
        raise RuntimeError("public workflow run did not succeed at the supplied commit")

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
            "all_git_blob_identities_verified": True,
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
        "local_git_commands_used": False,
    }
    return (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--contract-check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit")
    parser.add_argument("--workflow-run", type=int)
    args = parser.parse_args()
    if args.contract_check:
        value = local_contract()
        print(json.dumps({"mode": "contract-verified", **value}, sort_keys=True))
        return
    if not isinstance(args.commit, str) or not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("--commit must be a full lowercase SHA-1 outside --contract-check")
    if args.workflow_run is None or args.workflow_run <= 0:
        parser.error("--workflow-run must be positive outside --contract-check")
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
