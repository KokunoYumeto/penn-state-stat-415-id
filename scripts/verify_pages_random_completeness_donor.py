#!/usr/bin/env python3
"""Anonymously verify the exact Penn + Random-donor GitHub Pages tree."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
from typing import Any
from urllib.parse import quote, unquote, urlparse

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "build" / "PAGES_COLLECTION_RECEIPT.json"
RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_PAGES_RECEIPT_2026-08-28_RANDOM_COMPLETENESS_DONOR.json"
)
COMMIT = "5ed0e501e3a41c1274d90c9f02aee15bc210324a"
RUN_ID = 33_164_278_836
BASE_URL = "https://kokunoyumeto.github.io/penn-state-stat-415-id/"
API = "https://api.github.com/repos/KokunoYumeto/penn-state-stat-415-id"
SCHEMA = "o006.c140.random-completeness.github-pages-readback.v1"
COLLECTION_BYTES = 34_342
COLLECTION_SHA256 = "17b60a65cfb181d170f3302fb5f527608e026fcdbcab39839bcc3aad119f329a"
COLLECTION_MANIFEST_SHA256 = (
    "c7e31332d0401ad149185af3fc2ab2b39baf54a2b37f84dbc0f2720edd8241fa"
)
SHA256_RE = re.compile(r"[0-9a-f]{64}")
HEADERS = {
    "Accept": "*/*",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "O006-C140-static-pages-readback/2026.08.28",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def get(url: str, *, params: dict[str, str] | None = None) -> requests.Response:
    last_status: int | None = None
    last_transport_error: str | None = None
    with requests.Session() as session:
        # A fresh credential-free session makes the readback genuinely anonymous:
        # no .netrc, proxy credentials, ambient Authorization header, or cookies.
        session.trust_env = False
        session.headers.update(HEADERS)
        for attempt in range(8):
            try:
                response = session.get(url, params=params, timeout=180)
            except requests.RequestException as exc:
                last_transport_error = type(exc).__name__
                if attempt == 7:
                    break
                time.sleep(2 * (attempt + 1))
                continue
            last_status = response.status_code
            if response.status_code == 200:
                return response
            if (
                response.status_code not in {404, 429, 500, 502, 503, 504}
                or attempt == 7
            ):
                break
            time.sleep(2 * (attempt + 1))
    detail = (
        f"HTTP {last_status}"
        if last_status is not None
        else f"transport error {last_transport_error or 'unknown'}"
    )
    raise RuntimeError(f"anonymous public readback failed with {detail}: {url}")


def public_json(url: str) -> dict[str, Any]:
    response = get(url)
    try:
        value = response.json()
    except ValueError as exc:
        raise RuntimeError(f"public endpoint returned non-JSON bytes: {url}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"public endpoint returned a non-object: {url}")
    return value


def verify_control_plane() -> dict[str, object]:
    # Bind immutable evidence. A later receipt-only commit may advance `main`
    # without changing the deployed collection, so branch-head equality would
    # make check-only replay non-deterministic.
    commit = public_json(f"{API}/commits/{COMMIT}")
    if commit.get("sha") != COMMIT:
        raise RuntimeError("public immutable donor commit lookup differs")
    run = public_json(f"{API}/actions/runs/{RUN_ID}")
    if (
        run.get("head_sha") != COMMIT
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("path") != ".github/workflows/pages.yml"
    ):
        raise RuntimeError("public Pages workflow identity or result differs")
    return {
        "repository": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
        "content_commit": COMMIT,
        "immutable_commit_api_url": f"{API}/commits/{COMMIT}",
        "workflow_run_id": RUN_ID,
        "workflow_run_url": run.get("html_url"),
        "workflow_status": "completed",
        "workflow_conclusion": "success",
    }


def verify_file(row: dict[str, object]) -> dict[str, object]:
    path = str(row["path"])
    expected_bytes = int(row["bytes"])
    expected_sha = str(row["sha256"])
    url = BASE_URL + quote(path, safe="/")
    response = get(url, params={"o006_commit": COMMIT})
    parsed = urlparse(response.url)
    if parsed.scheme != "https" or (parsed.hostname or "").casefold() != "kokunoyumeto.github.io":
        raise RuntimeError(f"public Pages file redirected outside the admitted host: {path}")
    if response.history or unquote(parsed.path) != unquote(urlparse(url).path):
        raise RuntimeError(f"public Pages file followed an unexpected redirect/path: {path}")
    payload = response.content
    if len(payload) != expected_bytes or sha256(payload) != expected_sha:
        raise RuntimeError(f"public Pages file identity differs: {path}")
    return {
        "path": path,
        "source": row["source"],
        "bytes": expected_bytes,
        "sha256": expected_sha,
        "url": url,
        "http_status": 200,
        "final_host": parsed.hostname,
    }


def validate_collection(collection: dict[str, Any], collection_bytes: bytes) -> list[dict[str, object]]:
    if len(collection_bytes) != COLLECTION_BYTES or sha256(collection_bytes) != COLLECTION_SHA256:
        raise RuntimeError("local Pages collection receipt byte identity differs")
    rows = collection.get("files")
    expected_inputs = {
        "penn_reader": {
            "bytes": 17_614_553,
            "files": 106,
            "manifest_sha256": "cd76da2cda42a7e0b5f0e89281f7d5b8832266c34d01d60bdc5471ba5ce9fe89",
            "path": "build/html-id",
            "selection": "git-tracked-files-only",
        },
        "random_completeness_donor": {
            "bytes": 1_798_250,
            "files": 18,
            "manifest_sha256": "fb0bf5a27de7b6f38373f962ed1597522e4b912002be73b3ac08a908b272376e",
            "mount": "components/random-completeness",
            "path": "components/random-completeness/build/html-id",
        },
    }
    expected_collection = {
        "bytes": 19_412_803,
        "files": 124,
        "manifest_sha256": COLLECTION_MANIFEST_SHA256,
        "path": "build/pages",
    }
    expected_verification = {
        "case_insensitive_collisions": 0,
        "collisions": 0,
        "payload_transformations": 0,
        "penn_reader_files_byte_identical": True,
        "random_completeness_files_byte_identical": True,
    }
    if (
        collection.get("schema") != "o006.c140.pages-collection.v1"
        or collection.get("status") != "assembled"
        or collection.get("inputs") != expected_inputs
        or collection.get("collection") != expected_collection
        or collection.get("verification") != expected_verification
        or not isinstance(rows, list)
        or len(rows) != 124
    ):
        raise RuntimeError("local Pages collection receipt structure differs")

    validated: list[dict[str, object]] = []
    paths: set[str] = set()
    folded_paths: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise RuntimeError(f"collection row {index} is not an object")
        path = raw.get("path")
        source = raw.get("source")
        byte_count = raw.get("bytes")
        digest = raw.get("sha256")
        if (
            not isinstance(path, str)
            or not path
            or path.startswith("/")
            or "\\" in path
            or "?" in path
            or "#" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or PurePosixPath(path).as_posix() != path
        ):
            raise RuntimeError(f"collection row {index} has an unsafe path")
        if source not in {"penn-reader", "random-completeness-donor"}:
            raise RuntimeError(f"collection row {index} has an unknown source")
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
            raise RuntimeError(f"collection row {index} has an invalid byte count")
        if not isinstance(digest, str) or SHA256_RE.fullmatch(digest) is None:
            raise RuntimeError(f"collection row {index} has an invalid SHA-256")
        folded = path.casefold()
        if path in paths or folded in folded_paths:
            raise RuntimeError(f"collection path is duplicated: {path}")
        paths.add(path)
        folded_paths.add(folded)
        validated.append(raw)

    ordered = sorted(validated, key=lambda row: str(row["path"]))
    manifest = "".join(
        f"{row['path']}\t{row['bytes']}\t{row['sha256']}\n" for row in ordered
    ).encode("utf-8")
    if sha256(manifest) != COLLECTION_MANIFEST_SHA256:
        raise RuntimeError("recomputed Pages collection manifest differs")
    return ordered


def compute() -> bytes:
    control_plane = verify_control_plane()
    collection_bytes = COLLECTION.read_bytes()
    collection = json.loads(collection_bytes)
    rows = validate_collection(collection, collection_bytes)
    with ThreadPoolExecutor(max_workers=8) as pool:
        verified = list(pool.map(verify_file, rows))
    verified.sort(key=lambda row: str(row["path"]))
    penn = [row for row in verified if row["source"] == "penn-reader"]
    donor = [row for row in verified if row["source"] == "random-completeness-donor"]
    if (
        len(penn) != 106
        or sum(int(row["bytes"]) for row in penn) != 17_614_553
        or len(donor) != 18
        or sum(int(row["bytes"]) for row in donor) != 1_798_250
    ):
        raise RuntimeError("public component partition differs")
    receipt = {
        "schema": SCHEMA,
        "status": "pass",
        "anonymous_readback": True,
        "browser_processes_used": False,
        "control_plane": control_plane,
        "public_base_url": BASE_URL,
        "collection_receipt": {
            "path": "build/PAGES_COLLECTION_RECEIPT.json",
            "bytes": len(collection_bytes),
            "sha256": sha256(collection_bytes),
        },
        "collection": {
            "files": len(verified),
            "bytes": sum(int(row["bytes"]) for row in verified),
            "manifest_sha256": collection["collection"]["manifest_sha256"],
        },
        "penn_reader": {
            "files": len(penn),
            "bytes": sum(int(row["bytes"]) for row in penn),
            "all_files_match": True,
        },
        "random_completeness_donor": {
            "url": BASE_URL + "components/random-completeness/",
            "files": len(donor),
            "bytes": sum(int(row["bytes"]) for row in donor),
            "all_files_match": True,
        },
        "files": verified,
        "credential_access": False,
        "machine_local_paths_recorded": False,
    }
    return canonical_json(receipt)


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
        ) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    truststore.inject_into_ssl()
    payload = compute()
    if args.write:
        atomic_write(RECEIPT, payload)
        state = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub Pages public receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": state,
                "status": data["status"],
                "commit": COMMIT,
                "workflow_run_id": RUN_ID,
                "files": data["collection"]["files"],
                "bytes": data["collection"]["bytes"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
