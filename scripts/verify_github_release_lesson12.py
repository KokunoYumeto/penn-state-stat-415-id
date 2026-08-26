#!/usr/bin/env python3
"""Anonymously verify the public complete 14-of-14 GitHub release.

The verifier reads the final local package receipt and release files, then
checks the public tag, release inventory, and every downloaded asset by byte
count and SHA-256.  It uses no credential and invokes no local Git command.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
DEFAULT_TAG = "v2026.08.26.14of14"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON12_PACKAGE_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-26_THROUGH_LESSON12.json"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_READER_FILES = 106
EXPECTED_READER_BYTES = 17_614_553
EXPECTED_RELEASE_FILES = 9
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "O006-STAT415-anonymous-release-readback/14.0",
    "X-GitHub-Api-Version": "2022-11-28",
}
THREAD_LOCAL = threading.local()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


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
            raise RuntimeError(f"anonymous HTTP {response.status_code}: {url}")
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


def local_package() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    package_payload = PACKAGE_RECEIPT.read_bytes()
    package = json.loads(package_payload.decode("utf-8"))
    files = package.get("files")
    coverage = package.get("coverage")
    declared_total = package.get("total_bytes")
    if (
        package.get("schema") != "o006.stat415.through-lesson12-package.v1"
        or package.get("status") != "ready"
        or package.get("file_count") != EXPECTED_RELEASE_FILES
        or isinstance(declared_total, bool)
        or not isinstance(declared_total, int)
        or declared_total <= 0
        or not isinstance(files, list)
        or len(files) != EXPECTED_RELEASE_FILES
        or not isinstance(coverage, dict)
        or coverage.get("complete_count") != 14
        or coverage.get("next_document") is not None
        or coverage.get("pending_documents") != []
        or package.get("reader_zip", {}).get("reader_files") != EXPECTED_READER_FILES
        or package.get("reader_zip", {}).get("reader_bytes") != EXPECTED_READER_BYTES
    ):
        raise RuntimeError("local release package is not the exact complete 14-of-14 boundary")
    local: dict[str, dict[str, object]] = {}
    for item in files:
        if not isinstance(item, dict):
            raise RuntimeError("local package file record is malformed")
        name = item.get("filename")
        declared_size = item.get("bytes")
        declared_hash = item.get("sha256")
        if (
            not isinstance(name, str)
            or not name
            or "/" in name
            or "\\" in name
            or name in local
            or isinstance(declared_size, bool)
            or not isinstance(declared_size, int)
            or not re.fullmatch(r"[0-9a-f]{64}", str(declared_hash))
        ):
            raise RuntimeError(f"local package file record is invalid: {name!r}")
        path = ROOT / "release" / name
        data = path.read_bytes()
        identity = {"bytes": len(data), "sha256": sha256(data)}
        if identity != {"bytes": declared_size, "sha256": declared_hash}:
            raise RuntimeError(f"local release asset differs from package receipt: {name}")
        local[name] = identity
    if sum(int(item["bytes"]) for item in local.values()) != declared_total:
        raise RuntimeError("local release byte total differs")
    return package, local


def public_tag_commit(tag: str, expected_commit: str) -> dict[str, object]:
    ref_url = (
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/tags/"
        f"{quote(tag, safe='')}"
    )
    ref = fetch_json(ref_url)
    obj = ref.get("object")
    if ref.get("ref") != f"refs/tags/{tag}" or not isinstance(obj, dict):
        raise RuntimeError("public tag ref is absent or malformed")
    initial_sha = obj.get("sha")
    object_type = obj.get("type")
    if not isinstance(initial_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", initial_sha):
        raise RuntimeError("public tag object identity is malformed")
    current_sha = initial_sha
    peel_chain: list[dict[str, str]] = []
    for _ in range(4):
        if object_type == "commit":
            break
        if object_type != "tag":
            raise RuntimeError(f"public tag points to unsupported object type: {object_type}")
        tag_object = fetch_json(
            f"https://api.github.com/repos/{OWNER}/{REPO}/git/tags/{current_sha}"
        )
        nested = tag_object.get("object")
        if tag_object.get("sha") != current_sha or not isinstance(nested, dict):
            raise RuntimeError("public annotated tag object is malformed")
        nested_sha = nested.get("sha")
        nested_type = nested.get("type")
        if not isinstance(nested_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", nested_sha):
            raise RuntimeError("public annotated tag target identity is malformed")
        peel_chain.append({"tag_object": current_sha, "target": nested_sha, "target_type": str(nested_type)})
        current_sha = nested_sha
        object_type = nested_type
    if object_type != "commit" or current_sha != expected_commit:
        raise RuntimeError("public tag does not peel to the supplied release commit")
    return {
        "tag_object": initial_sha,
        "annotated": bool(peel_chain),
        "peel_chain": peel_chain,
        "peeled_commit": current_sha,
        "ref_url": ref_url,
    }


def verify_asset(job: tuple[str, dict[str, object], str]) -> dict[str, object]:
    name, expected, download_root = job
    url = f"{download_root}/{quote(name, safe='')}"
    data, final_url = fetch(url)
    identity = {"bytes": len(data), "sha256": sha256(data)}
    if identity != expected:
        raise RuntimeError(f"public release asset differs: {name}")
    return {
        "filename": name,
        **identity,
        "download_url": url,
        "final_url": final_url,
        "final_host": urlparse(final_url).hostname,
    }


def compute(tag: str, commit: str) -> bytes:
    truststore.inject_into_ssl()
    package, local = local_package()
    release_page = f"https://github.com/{OWNER}/{REPO}/releases/tag/{tag}"
    asset_page = f"https://github.com/{OWNER}/{REPO}/releases/expanded_assets/{tag}"
    download_root = f"https://github.com/{OWNER}/{REPO}/releases/download/{tag}"
    page, page_url = fetch(release_page)
    if tag not in page.decode("utf-8", errors="replace"):
        raise RuntimeError("public release page does not expose the exact tag")
    asset_payload, asset_page_url = fetch(asset_page)
    asset_text = asset_payload.decode("utf-8", errors="replace")
    missing_names = [name for name in local if name not in asset_text]
    if missing_names:
        raise RuntimeError(f"public release page omits assets: {missing_names}")

    with ThreadPoolExecutor(max_workers=6) as pool:
        public_files = list(
            pool.map(
                verify_asset,
                [(name, local[name], download_root) for name in local],
            )
        )
    total_bytes = sum(int(item["bytes"]) for item in public_files)
    if len(public_files) != EXPECTED_RELEASE_FILES or total_bytes != package["total_bytes"]:
        raise RuntimeError("public release inventory total differs")
    return canonical_json(
        {
            "schema": "o006.stat415.github-release-through-lesson12.v1",
            "status": "passed",
            "anonymous": True,
            "authentication_material_used": False,
            "local_git_commands_used": False,
            "coverage": {
                "complete_documents": 14,
                "corpus_documents": 14,
                "next_document": None,
                "pending_documents": [],
            },
            "commit": commit,
            "tag": tag,
            "tag_readback": public_tag_commit(tag, commit),
            "release_page": {
                "url": release_page,
                "final_url": page_url,
                "publicly_readable": True,
                "tag_visible": True,
            },
            "asset_inventory_page": {
                "url": asset_page,
                "final_url": asset_page_url,
                "publicly_readable": True,
                "filenames_matched": len(public_files),
            },
            "files": public_files,
            "file_count": len(public_files),
            "total_bytes": total_bytes,
            "package_receipt": {
                "path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
                "bytes": PACKAGE_RECEIPT.stat().st_size,
                "sha256": sha256(PACKAGE_RECEIPT.read_bytes()),
            },
            "translation_provenance": PROVENANCE,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--contract-check", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--commit")
    args = parser.parse_args()
    if args.contract_check:
        _, local = local_package()
        print(
            json.dumps(
                {
                    "mode": "contract-verified",
                    "files": len(local),
                    "bytes": sum(int(item["bytes"]) for item in local.values()),
                    "package_receipt_sha256": sha256(PACKAGE_RECEIPT.read_bytes()),
                    "default_tag": DEFAULT_TAG,
                },
                sort_keys=True,
            )
        )
        return
    if not isinstance(args.commit, str) or not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("--commit must be a full lowercase SHA-1 outside --contract-check")
    payload = compute(args.tag, args.commit)
    if args.write:
        atomic_write(RECEIPT, payload)
        state = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub release readback receipt differs")
        state = "verified"
    value = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": state,
                "files": value["file_count"],
                "bytes": value["total_bytes"],
                "commit": value["commit"],
                "tag": value["tag"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
