#!/usr/bin/env python3
"""Verify the public Penn + donor + C140 companion Pages collection."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import time
from typing import Any
from urllib.parse import quote, unquote, urlparse

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "build" / "PAGES_COLLECTION_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_PAGES_RECEIPT_2026-08-28_C140_COMPANION_C1.json"
BASE_URL = "https://kokunoyumeto.github.io/penn-state-stat-415-id/"
API = "https://api.github.com/repos/KokunoYumeto/penn-state-stat-415-id"
SCHEMA = "o006.c140.companion-c1.github-pages-readback.v1"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
CONTENT_HEADERS = {
    "Accept": "*/*",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "O006-C140-companion-static-readback/2026.08.28",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def get_with_retry(session: requests.Session, url: str, *, params: dict[str, str] | None = None) -> requests.Response:
    last_status: int | None = None
    last_error: str | None = None
    for attempt in range(8):
        try:
            response = session.get(url, params=params, timeout=180)
        except requests.RequestException as exc:
            last_error = type(exc).__name__
            if attempt == 7:
                break
            time.sleep(2 * (attempt + 1))
            continue
        last_status = response.status_code
        if response.status_code == 200:
            return response
        if response.status_code not in {403, 404, 429, 500, 502, 503, 504} or attempt == 7:
            break
        time.sleep(2 * (attempt + 1))
    detail = f"HTTP {last_status}" if last_status is not None else f"transport error {last_error or 'unknown'}"
    raise RuntimeError(f"public readback failed with {detail}: {url}")


def public_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.update(CONTENT_HEADERS)
    return session


def control_session() -> tuple[requests.Session, bool]:
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"Accept": "application/vnd.github+json", "User-Agent": CONTENT_HEADERS["User-Agent"]})
    token = os.environ.get("O006_GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"
    return session, bool(token)


def public_json(session: requests.Session, url: str) -> dict[str, Any]:
    response = get_with_retry(session, url)
    try:
        value = response.json()
    except ValueError as exc:
        raise RuntimeError(f"control endpoint returned non-JSON bytes: {url}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"control endpoint returned a non-object: {url}")
    return value


def verify_control_plane(commit_id: str, run_id: int) -> dict[str, object]:
    session, authenticated = control_session()
    try:
        commit = public_json(session, f"{API}/commits/{commit_id}")
        run = public_json(session, f"{API}/actions/runs/{run_id}")
    finally:
        session.close()
    if commit.get("sha") != commit_id:
        raise RuntimeError("immutable public commit identity differs")
    if (
        run.get("head_sha") != commit_id
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("path") != ".github/workflows/pages.yml"
    ):
        raise RuntimeError("Pages workflow identity or result differs")
    return {
        "api_authentication_used": authenticated,
        "content_commit": commit_id,
        "repository": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
        "workflow_conclusion": "success",
        "workflow_run_id": run_id,
        "workflow_run_url": run.get("html_url"),
        "workflow_status": "completed",
    }


def validate_collection(payload: bytes) -> tuple[dict[str, Any], list[dict[str, object]]]:
    value = json.loads(payload)
    if value.get("schema") != "o006.c140.pages-collection.v2" or value.get("status") != "assembled":
        raise RuntimeError("Pages collection schema/status differs")
    inputs = value.get("inputs")
    collection = value.get("collection")
    verification = value.get("verification")
    rows = value.get("files")
    if not isinstance(inputs, dict) or set(inputs) != {"penn_reader", "random_completeness_donor", "c140_original_companion"}:
        raise RuntimeError("Pages collection component inventory differs")
    if not isinstance(collection, dict) or not isinstance(verification, dict) or not isinstance(rows, list):
        raise RuntimeError("Pages collection structure differs")
    required_verification = {
        "collisions": 0,
        "case_insensitive_collisions": 0,
        "payload_transformations": 0,
        "penn_reader_files_byte_identical": True,
        "random_completeness_files_byte_identical": True,
        "c140_original_companion_files_byte_identical": True,
    }
    if verification != required_verification:
        raise RuntimeError("Pages collection verification claims differ")

    sources = {
        "penn-reader": "penn_reader",
        "random-completeness-donor": "random_completeness_donor",
        "c140-original-companion": "c140_original_companion",
    }
    validated: list[dict[str, object]] = []
    paths: set[str] = set()
    folded: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise RuntimeError(f"collection row {index} is not an object")
        path = raw.get("path")
        source = raw.get("source")
        size = raw.get("bytes")
        digest = raw.get("sha256")
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or "\\" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or PurePosixPath(path).as_posix() != path
        ):
            raise RuntimeError(f"unsafe collection path at row {index}")
        if source not in sources or isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise RuntimeError(f"invalid source/size at row {index}")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            raise RuntimeError(f"invalid digest at row {index}")
        if path in paths or path.casefold() in folded:
            raise RuntimeError(f"duplicate collection path: {path}")
        paths.add(path)
        folded.add(path.casefold())
        validated.append(raw)
    validated.sort(key=lambda row: str(row["path"]))
    manifest = "".join(f"{row['path']}\t{row['bytes']}\t{row['sha256']}\n" for row in validated).encode("utf-8")
    if (
        collection.get("path") != "build/pages"
        or collection.get("files") != len(validated)
        or collection.get("bytes") != sum(int(row["bytes"]) for row in validated)
        or collection.get("manifest_sha256") != sha256(manifest)
    ):
        raise RuntimeError("Pages collection aggregate differs")
    for source, input_key in sources.items():
        partition = [row for row in validated if row["source"] == source]
        info = inputs[input_key]
        source_manifest = "".join(
            f"{row['source_path']}\t{row['bytes']}\t{row['sha256']}\n"
            for row in sorted(partition, key=lambda row: str(row["source_path"]))
        ).encode("utf-8")
        if (
            info.get("files") != len(partition)
            or info.get("bytes") != sum(int(row["bytes"]) for row in partition)
            or info.get("manifest_sha256") != sha256(source_manifest)
        ):
            raise RuntimeError(f"Pages component partition differs: {input_key}")
    return value, validated


def verify_file(row: dict[str, object], commit_id: str) -> dict[str, object]:
    path = str(row["path"])
    url = BASE_URL + quote(path, safe="/")
    with public_session() as session:
        response = get_with_retry(session, url, params={"o006_commit": commit_id})
    parsed = urlparse(response.url)
    if parsed.scheme != "https" or (parsed.hostname or "").casefold() != "kokunoyumeto.github.io":
        raise RuntimeError(f"public Pages file left the admitted host: {path}")
    if response.history or unquote(parsed.path) != unquote(urlparse(url).path):
        raise RuntimeError(f"public Pages file followed an unexpected path: {path}")
    payload = response.content
    if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
        raise RuntimeError(f"public Pages byte identity differs: {path}")
    return {
        "bytes": row["bytes"],
        "http_status": 200,
        "path": path,
        "sha256": row["sha256"],
        "source": row["source"],
        "url": url,
    }


def compute(commit_id: str, run_id: int) -> bytes:
    if re.fullmatch(r"[0-9a-f]{40}", commit_id) is None:
        raise RuntimeError("commit must be a full 40-character lowercase Git SHA")
    collection_payload = COLLECTION.read_bytes()
    collection, rows = validate_collection(collection_payload)
    control = verify_control_plane(commit_id, run_id)
    with ThreadPoolExecutor(max_workers=8) as pool:
        verified = list(pool.map(lambda row: verify_file(row, commit_id), rows))
    verified.sort(key=lambda row: str(row["path"]))
    partitions = {}
    for source in ("penn-reader", "random-completeness-donor", "c140-original-companion"):
        group = [row for row in verified if row["source"] == source]
        partitions[source] = {"bytes": sum(int(row["bytes"]) for row in group), "files": len(group)}
    return canonical_json({
        "anonymous_content_readback": True,
        "browser_processes_used": False,
        "collection": collection["collection"],
        "collection_receipt_bytes": len(collection_payload),
        "collection_receipt_sha256": sha256(collection_payload),
        "control_plane": control,
        "files": verified,
        "network_runtime_dependencies_tested": 0,
        "partitions": partitions,
        "public_base_url": BASE_URL,
        "schema": SCHEMA,
        "status": "pass",
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit")
    parser.add_argument("--run-id", type=int)
    args = parser.parse_args()
    if args.write:
        if not args.commit or args.run_id is None:
            raise RuntimeError("--write requires --commit and --run-id")
        commit_id, run_id = args.commit, args.run_id
    else:
        if args.commit or args.run_id is not None:
            raise RuntimeError("--check-only reads the pinned receipt identity")
        existing = json.loads(RECEIPT.read_text(encoding="utf-8"))
        commit_id = existing["control_plane"]["content_commit"]
        run_id = int(existing["control_plane"]["workflow_run_id"])
    payload = compute(commit_id, run_id)
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_bytes(payload)
        state = "written"
    else:
        if RECEIPT.read_bytes() != payload:
            raise RuntimeError("public Pages receipt deterministic replay mismatch")
        state = "verified"
    value = json.loads(payload)
    print(json.dumps({
        "bytes": value["collection"]["bytes"],
        "files": value["collection"]["files"],
        "mode": state,
        "receipt_sha256": sha256(payload),
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    truststore.inject_into_ssl()
    main()
