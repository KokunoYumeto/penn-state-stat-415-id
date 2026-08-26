#!/usr/bin/env python3
"""Anonymously verify the public 13-of-14 GitHub release and its assets.

The commit is supplied explicitly because a verifier must never guess which
release is authoritative. No credential, token, or authenticated API is used;
only public GitHub pages, tag refs, and release downloads are read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
DEFAULT_TAG = "v2026.08.26.13of14"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON11_PACKAGE_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-26_THROUGH_LESSON11.json"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_READER_FILES = 96
EXPECTED_READER_BYTES = 17_232_761


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    temporary.replace(path)


def fetch(session: requests.Session, url: str) -> tuple[bytes, str]:
    response = session.get(url, timeout=300)
    if response.status_code != 200:
        raise RuntimeError(f"anonymous HTTP {response.status_code}: {url}")
    return response.content, response.url


def public_tag_commit(tag: str, expected_commit: str) -> dict[str, object]:
    result = subprocess.run(
        ["git", "ls-remote", "--tags", f"https://github.com/{OWNER}/{REPO}.git", f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    rows = [line.split("\t", 1) for line in result.stdout.splitlines() if line]
    refs = {ref: object_id for object_id, ref in rows}
    peeled_ref = f"refs/tags/{tag}^{{}}"
    if f"refs/tags/{tag}" not in refs or refs.get(peeled_ref) != expected_commit:
        raise RuntimeError("public tag is absent or does not peel to the requested release commit")
    return {"tag_object": refs[f"refs/tags/{tag}"], "peeled_commit": refs[peeled_ref]}


def compute(tag: str, commit: str) -> bytes:
    truststore.inject_into_ssl()
    package = json.loads(PACKAGE_RECEIPT.read_text(encoding="utf-8"))
    files = package.get("files", [])
    if package.get("file_count") != 9 or len(files) != 9:
        raise RuntimeError("local release package is not the exact nine-file 13-of-14 boundary")
    if package.get("coverage", {}).get("complete_count") != 13 or package.get("coverage", {}).get("next_document") != "Lesson12":
        raise RuntimeError("local package coverage is not 13 of 14")
    if (
        package.get("reader_zip", {}).get("reader_files") != EXPECTED_READER_FILES
        or package.get("reader_zip", {}).get("reader_bytes") != EXPECTED_READER_BYTES
    ):
        raise RuntimeError("local package does not bind the exact 96-file reader")
    local: dict[str, dict[str, object]] = {}
    for item in files:
        name = item["filename"]
        path = ROOT / "release" / name
        data = path.read_bytes()
        identity = {"bytes": len(data), "sha256": sha256(data)}
        if identity != {"bytes": item["bytes"], "sha256": item["sha256"]}:
            raise RuntimeError(f"local release asset differs from package receipt: {name}")
        local[name] = identity

    release_page = f"https://github.com/{OWNER}/{REPO}/releases/tag/{tag}"
    asset_page = f"https://github.com/{OWNER}/{REPO}/releases/expanded_assets/{tag}"
    download_root = f"https://github.com/{OWNER}/{REPO}/releases/download/{tag}"
    session = requests.Session()
    session.headers.update({"Cache-Control": "no-cache", "Pragma": "no-cache", "User-Agent": "O006-STAT415-anonymous-release-readback/13.0"})
    page, page_url = fetch(session, release_page)
    if tag not in page.decode("utf-8", errors="replace"):
        raise RuntimeError("public release page does not expose the exact tag")
    asset_page_payload, asset_page_url = fetch(session, asset_page)
    asset_page_text = asset_page_payload.decode("utf-8", errors="replace")
    missing_names = [name for name in local if name not in asset_page_text]
    if missing_names:
        raise RuntimeError(f"public release page omits assets: {missing_names}")

    def verify_asset(name: str) -> dict[str, object]:
        asset_session = requests.Session()
        asset_session.headers.update(session.headers)
        url = f"{download_root}/{quote(name, safe='')}"
        data, final_url = fetch(asset_session, url)
        identity = {"bytes": len(data), "sha256": sha256(data)}
        if identity != local[name]:
            raise RuntimeError(f"public release asset differs: {name}")
        return {"filename": name, **identity, "download_url": url, "final_host": urlparse(final_url).hostname}

    with ThreadPoolExecutor(max_workers=6) as pool:
        public_files = list(pool.map(verify_asset, local))
    return canonical_json({
        "schema": "o006.stat415.github-release-through-lesson11.v1",
        "status": "passed",
        "anonymous": True,
        "authentication_material_used": False,
        "coverage": {"complete_documents": 13, "corpus_documents": 14, "next_document": "Lesson12"},
        "commit": commit,
        "tag": tag,
        "tag_readback": public_tag_commit(tag, commit),
        "release_page": {"url": release_page, "final_url": page_url, "publicly_readable": True, "tag_visible": True},
        "asset_inventory_page": {"url": asset_page, "final_url": asset_page_url, "publicly_readable": True, "filenames_matched": len(public_files)},
        "files": public_files,
        "file_count": len(public_files),
        "total_bytes": sum(item["bytes"] for item in public_files),
        "package_receipt": {"path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(), "bytes": PACKAGE_RECEIPT.stat().st_size, "sha256": sha256(PACKAGE_RECEIPT.read_bytes())},
        "translation_provenance": PROVENANCE,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default=DEFAULT_TAG)
    parser.add_argument("--commit", required=True, help="expected peeled commit for the public tag")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payload = compute(args.tag, args.commit)
    if args.write:
        atomic_write(RECEIPT, payload)
        state = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub release readback receipt differs")
        state = "verified"
    value = json.loads(payload)
    print(json.dumps({"mode": state, "files": value["file_count"], "bytes": value["total_bytes"], "commit": value["commit"], "tag": value["tag"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
