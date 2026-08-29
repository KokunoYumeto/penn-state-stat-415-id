#!/usr/bin/env python3
"""Anonymous raw-HTTPS readback for the C3 state/receipt commit.

The file set is the exact diff between the fixed parent and commit.  No GitHub
API, credentials, browser, or mutable branch URL is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "00_control" / "GITHUB_C3_STATE_COMMIT_DIRECT_READBACK.json"
REPOSITORY = "KokunoYumeto/penn-state-stat-415-id"
PARENT = "1c8f97f02e9bccfdbe4df91dd77af969cd6e33d6"
COMMIT = "6a0cc291fd7bf505d8e444aa100d6a4fc4e0d853"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def changed_paths() -> list[str]:
    raw = git("diff-tree", "--no-commit-id", "--name-only", "-r", PARENT, COMMIT, "--")
    paths = [line.decode("utf-8") for line in raw.splitlines() if line]
    if not paths or len(paths) != len(set(paths)):
        raise RuntimeError("empty or duplicate commit path set")
    if any(path.startswith("/") or ".." in Path(path).parts for path in paths):
        raise RuntimeError("unsafe commit path")
    return sorted(paths)


def local_bytes(path: str) -> bytes:
    return git("show", f"{COMMIT}:{path}")


def download(url: str) -> bytes:
    request = Request(url, headers={"Accept": "*/*", "User-Agent": "c140-static-readback/1.0"})
    last: Exception | None = None
    for attempt in range(5):
        try:
            with urlopen(request, timeout=45) as response:
                if response.status != 200:
                    raise RuntimeError(f"HTTP {response.status}")
                if not response.geturl().startswith("https://raw.githubusercontent.com/"):
                    raise RuntimeError(f"unexpected redirect {response.geturl()}")
                return response.read()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt < 4:
                time.sleep(0.8 * (attempt + 1))
    raise RuntimeError(f"readback failed: {last}")


def build() -> dict[str, object]:
    paths = changed_paths()
    files: list[dict[str, object]] = []
    aggregate = hashlib.sha256()
    total = 0
    for path in paths:
        local = local_bytes(path)
        url = f"https://raw.githubusercontent.com/{REPOSITORY}/{COMMIT}/{quote(path, safe='/')}"
        public = download(url)
        digest = sha256(local)
        if public != local:
            raise RuntimeError(f"byte mismatch: {path}")
        aggregate.update(path.encode("utf-8")); aggregate.update(b"\0")
        aggregate.update(str(len(local)).encode("ascii")); aggregate.update(b"\0")
        aggregate.update(digest.encode("ascii")); aggregate.update(b"\n")
        total += len(local)
        files.append({"path": path, "bytes": len(local), "sha256": digest,
                      "public_bytes": len(public), "public_sha256": sha256(public),
                      "public_url": url, "match": True})
    return {
        "schema": "o006.c140.c3.github-state-commit-direct-readback.v1",
        "repository": REPOSITORY, "parent": PARENT, "commit": COMMIT,
        "transport": "anonymous static HTTPS raw commit URLs",
        "credentials_read": False, "authorization_header_sent": False,
        "browser_used": False, "api_used": False,
        "file_count": len(files), "total_bytes": total,
        "aggregate_sha256": aggregate.hexdigest(), "all_match": True,
        "files": files,
    }


def payload(value: dict[str, object]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    expected = payload(build())
    if args.write:
        RECEIPT.write_bytes(expected)
    elif RECEIPT.read_bytes() != expected:
        raise SystemExit("direct state-commit receipt is stale")
    print(json.dumps({"files": json.loads(expected)["file_count"],
                      "bytes": json.loads(expected)["total_bytes"],
                      "receipt_sha256": sha256(expected), "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
