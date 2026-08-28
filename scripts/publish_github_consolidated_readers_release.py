#!/usr/bin/env python3
"""Publish and anonymously verify the tag-scoped STAT 415 reader release.

The adapter is pinned to ``v2026.08.28.14of14-pdf-epub``.  It never creates or
changes a Git tag, never invokes Git, and contains no PATCH/PUT/DELETE request.
It may create only the release for that already-public tag and upload only
missing assets from the exact 17-file package union.  Existing or older release
assets are never replaced.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import re
import tempfile
import threading
import time
from typing import Any
from urllib.parse import quote, urlparse

import requests
import truststore

import consolidated_release_contract as contract


OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
TAG = "v2026.08.28.14of14-pdf-epub"
PREVIOUS_TAG = "v2026.08.26.14of14"
API = "https://api.github.com"
REPOSITORY_API = f"{API}/repos/{OWNER}/{REPO}"
TOKEN_FILE = Path.home() / "Downloads" / "Github Tokens.md"
RECEIPT = (
    contract.ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-28_CONSOLIDATED_READERS.json"
)
PUBLICATION_RECEIPT = (
    contract.ROOT / "00_control" / "GITHUB_RELEASE_PUBLICATION_2026-08-28_CONSOLIDATED_READERS.json"
)
SCHEMA = "o006.stat415.github-consolidated-readers-release.v1"
TITLE = "STAT 415 Bahasa Indonesia lengkap — PDF dan EPUB"
BODY = (
    "Rilis pembaca lengkap untuk komponen Penn State STAT 415: laman utama dan "
    "Pelajaran 00–12 (14 dari 14 dokumen), dengan PDF 219 halaman, EPUB reflowable, "
    "pembaca HTML luring, source/backend, hak komponen, checksum, dan bukti QA. "
    "Status lengkap berlaku pada komponen Penn State; donor Random dan pendamping "
    "orisinal C140 tetap komponen terpisah. Lisensi komponen dipertahankan dan "
    "agregat tidak direlisensi secara seragam. Provenans terjemahan: "
    f"{contract.MODEL_PROVENANCE}."
)
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "O006-STAT415-consolidated-release/2026.08.28",
    "X-GitHub-Api-Version": "2022-11-28",
}
THREAD_LOCAL = threading.local()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_json(path: Path, value: dict[str, object]) -> None:
    payload = canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def check(response: requests.Response, expected: tuple[int, ...], action: str) -> requests.Response:
    if response.status_code not in expected:
        # Do not include response bodies; an authenticated service may echo
        # sensitive request information.
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    return response


def public_session() -> requests.Session:
    current = getattr(THREAD_LOCAL, "session", None)
    if current is None:
        current = requests.Session()
        current.headers.update(HEADERS)
        THREAD_LOCAL.session = current
    return current


def fetch(url: str) -> tuple[bytes, str]:
    for attempt in range(6):
        response = public_session().get(url, timeout=900)
        if response.status_code == 200:
            return response.content, response.url
        if response.status_code not in (429, 500, 502, 503, 504) or attempt == 5:
            raise RuntimeError(f"anonymous GitHub readback failed with HTTP {response.status_code}")
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable GitHub retry state")


def fetch_json(url: str) -> dict[str, Any]:
    payload, _ = fetch(url)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("public GitHub endpoint did not return UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("public GitHub endpoint did not return a JSON object")
    return value


def read_token() -> str:
    in_memory = os.environ.get("GITHUB_TOKEN", "").strip()
    if re.fullmatch(
        r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})",
        in_memory,
    ):
        return in_memory
    if not TOKEN_FILE.is_file():
        raise RuntimeError(
            "No in-memory GitHub credential is set and the bounded credential file is absent"
        )
    raw = TOKEN_FILE.read_text("utf-8")
    candidates = re.findall(
        r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})",
        raw,
    )
    if not candidates:
        raise RuntimeError("GitHub credential file contains no supported token")
    return max(candidates, key=len)


def tag_commit(expected_commit: str) -> dict[str, object]:
    ref_url = f"{REPOSITORY_API}/git/ref/tags/{quote(TAG, safe='')}"
    ref = fetch_json(ref_url)
    obj = ref.get("object")
    if ref.get("ref") != f"refs/tags/{TAG}" or not isinstance(obj, dict):
        raise RuntimeError("public release tag ref is absent or malformed")
    current = obj.get("sha")
    kind = obj.get("type")
    if not isinstance(current, str) or not re.fullmatch(r"[0-9a-f]{40}", current):
        raise RuntimeError("public tag object identity is malformed")
    initial = current
    peel: list[dict[str, str]] = []
    for _ in range(4):
        if kind == "commit":
            break
        if kind != "tag":
            raise RuntimeError("public tag points to an unsupported object type")
        value = fetch_json(f"{REPOSITORY_API}/git/tags/{current}")
        nested = value.get("object")
        if value.get("sha") != current or not isinstance(nested, dict):
            raise RuntimeError("public annotated tag object is malformed")
        target = nested.get("sha")
        target_type = nested.get("type")
        if not isinstance(target, str) or not re.fullmatch(r"[0-9a-f]{40}", target):
            raise RuntimeError("public annotated tag target is malformed")
        peel.append({"tag_object": current, "target": target, "target_type": str(target_type)})
        current, kind = target, target_type
    if kind != "commit" or current != expected_commit:
        raise RuntimeError("public release tag does not peel to the supplied commit")
    return {
        "ref_url": ref_url,
        "tag_object": initial,
        "annotated": bool(peel),
        "peel_chain": peel,
        "peeled_commit": current,
    }


def release_by_tag(session: requests.Session, tag: str, *, allow_missing: bool) -> dict[str, Any] | None:
    response = session.get(f"{REPOSITORY_API}/releases/tags/{quote(tag, safe='')}", timeout=120)
    if allow_missing and response.status_code == 404:
        return None
    check(response, (200,), f"read GitHub release {tag}")
    value = response.json()
    if not isinstance(value, dict) or value.get("tag_name") != tag:
        raise RuntimeError(f"GitHub release response is malformed for {tag}")
    return value


def old_release_witness() -> dict[str, object]:
    value = release_by_tag(public_session(), PREVIOUS_TAG, allow_missing=False)
    assert value is not None
    assets = [row for row in value.get("assets") or [] if isinstance(row, dict)]
    inventory = sorted(
        [
            {
                "id": row.get("id"),
                "name": row.get("name"),
                "size": row.get("size"),
                "state": row.get("state"),
            }
            for row in assets
        ],
        key=lambda row: str(row["name"]).casefold(),
    )
    witness = {
        "release_id": value.get("id"),
        "tag": PREVIOUS_TAG,
        "draft": value.get("draft"),
        "prerelease": value.get("prerelease"),
        "assets": inventory,
    }
    return {**witness, "sha256": hashlib.sha256(canonical_json(witness)).hexdigest()}


def validate_target_release(value: dict[str, Any]) -> None:
    if (
        value.get("tag_name") != TAG
        or value.get("name") != TITLE
        or value.get("body") != BODY
        or value.get("draft") is not False
        or value.get("prerelease") is not False
        or not isinstance(value.get("id"), int)
    ):
        raise RuntimeError("target GitHub release metadata differs; refusing to edit it")


def public_asset(
    job: tuple[contract.Artifact, dict[str, Any]],
) -> dict[str, object]:
    wanted, row = job
    if row.get("name") != wanted.name or row.get("state") != "uploaded" or row.get("size") != wanted.bytes:
        raise RuntimeError(f"public GitHub asset metadata differs: {wanted.name}")
    url = row.get("browser_download_url")
    parsed = urlparse(str(url))
    expected_path = f"/{OWNER}/{REPO}/releases/download/{TAG}/{quote(wanted.name, safe='')}"
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "github.com"
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(f"public GitHub asset URL is not admitted: {wanted.name}")
    payload, final_url = fetch(str(url))
    if len(payload) != wanted.bytes or hashlib.sha256(payload).hexdigest() != wanted.sha256:
        raise RuntimeError(f"public GitHub asset bytes differ: {wanted.name}")
    return {
        "name": wanted.name,
        "bytes": wanted.bytes,
        "sha256": wanted.sha256,
        "asset_id": row.get("id"),
        "download_url": url,
        "final_url": final_url,
        "final_host": urlparse(final_url).hostname,
    }


def anonymous_readback(
    snap: contract.ReleaseSnapshot,
    commit: str,
) -> dict[str, object]:
    release = release_by_tag(public_session(), TAG, allow_missing=False)
    assert release is not None
    validate_target_release(release)
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    by_name = {str(row.get("name")): row for row in assets}
    expected = {item.name: item for item in snap.files}
    if set(by_name) != set(expected) or len(assets) != len(expected):
        raise RuntimeError("public GitHub release asset inventory is not exact")
    with ThreadPoolExecutor(max_workers=6) as pool:
        verified = list(pool.map(public_asset, [(item, by_name[item.name]) for item in snap.files]))
    tag = tag_commit(commit)
    html_url = str(release.get("html_url"))
    parsed = urlparse(html_url)
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "github.com"
        or parsed.path != f"/{OWNER}/{REPO}/releases/tag/{TAG}"
    ):
        raise RuntimeError("public GitHub release page URL differs")
    return {
        "release_id": release["id"],
        "url": html_url,
        "tag": TAG,
        "tag_readback": tag,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "reader_first": verified[0]["name"] == snap.pdf.name,
        "anonymous_readback": True,
    }


def upload_root(value: object, release_id: int) -> str:
    if not isinstance(value, str):
        raise RuntimeError("GitHub release omitted its upload URL")
    base = value.split("{", 1)[0]
    parsed = urlparse(base)
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "uploads.github.com"
        or parsed.path != f"/repos/{OWNER}/{REPO}/releases/{release_id}/assets"
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("GitHub release returned a non-admitted upload URL")
    return base


def create_release(session: requests.Session, commit: str) -> dict[str, Any]:
    value = check(
        session.post(
            f"{REPOSITORY_API}/releases",
            json={
                "tag_name": TAG,
                "target_commitish": commit,
                "name": TITLE,
                "body": BODY,
                "draft": False,
                "prerelease": False,
                "make_latest": "true",
            },
            timeout=120,
        ),
        (201,),
        "create tag-scoped GitHub release",
    ).json()
    if not isinstance(value, dict):
        raise RuntimeError("GitHub release creation response is not an object")
    validate_target_release(value)
    return value


def upload_missing(
    session: requests.Session,
    release: dict[str, Any],
    snap: contract.ReleaseSnapshot,
) -> tuple[dict[str, Any], list[str]]:
    validate_target_release(release)
    release_id = int(release["id"])
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    by_name = {str(row.get("name")): row for row in assets}
    expected = {item.name: item for item in snap.files}
    extras = sorted(set(by_name) - set(expected), key=str.casefold)
    if extras or len(by_name) != len(assets):
        raise RuntimeError("target release has unexpected or duplicate assets; refusing mutation")
    # Existing assets must already match.  A differing asset is never deleted
    # or replaced; the transaction aborts instead.
    for name in sorted(set(by_name) & set(expected), key=str.casefold):
        public_asset((expected[name], by_name[name]))
    root = upload_root(release.get("upload_url"), release_id)
    uploaded: list[str] = []
    for item in snap.files:
        if item.name in by_name:
            continue
        content_type = mimetypes.guess_type(item.name)[0] or "application/octet-stream"
        response = check(
            session.post(
                root,
                params={"name": item.name},
                data=item.payload,
                headers={"Content-Type": content_type, "Content-Length": str(item.bytes)},
                timeout=900,
            ),
            (201,),
            f"upload GitHub release asset {item.name}",
        )
        value = response.json()
        if (
            not isinstance(value, dict)
            or value.get("name") != item.name
            or value.get("size") != item.bytes
            or value.get("state") != "uploaded"
        ):
            raise RuntimeError(f"GitHub upload response differs: {item.name}")
        uploaded.append(item.name)
    refreshed = release_by_tag(session, TAG, allow_missing=False)
    assert refreshed is not None
    validate_target_release(refreshed)
    return refreshed, uploaded


def receipt_base(snap: contract.ReleaseSnapshot, commit: str) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "version": contract.PUBLICATION_VERSION,
        "repository": f"https://github.com/{OWNER}/{REPO}",
        "tag": TAG,
        "commit": commit,
        "coverage": snap.package["coverage"],
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "local_inventory": [
            {"name": item.name, "bytes": item.bytes, "sha256": item.sha256}
            for item in snap.files
        ],
        "package_receipt": {
            "path": contract.PACKAGE_RECEIPT.relative_to(contract.ROOT).as_posix(),
            "bytes": snap.package_receipt_bytes,
            "sha256": snap.package_receipt_sha256,
        },
        "translation_provenance": contract.MODEL_PROVENANCE,
        "local_git_commands_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local-preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify-published", action="store_true")
    parser.add_argument("--commit")
    args = parser.parse_args()

    snap = contract.snapshot()
    if args.local_preflight:
        print(json.dumps({**contract.preflight_summary(snap), "adapter": "github", "tag": TAG}, ensure_ascii=False, sort_keys=True))
        return
    if not isinstance(args.commit, str) or not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("--commit must be a full lowercase SHA-1 outside --local-preflight")

    truststore.inject_into_ssl()
    base = receipt_base(snap, args.commit)
    if args.verify_published:
        public = anonymous_readback(snap, args.commit)
        receipt = {
            **base,
            "mode": "verify-published",
            "credential_access": False,
            "remote_writes": False,
            "public": public,
        }
        atomic_json(RECEIPT, receipt)
        print(json.dumps({"mode": "verify-published", "tag": TAG, "commit": args.commit, "files": len(snap.files), "status": "pass"}, sort_keys=True))
        return

    # Public tag identity is a prerequisite; this adapter never creates or
    # moves refs.  Credential access begins only after the tag check.
    tag_commit(args.commit)
    before = old_release_witness()
    token = read_token()
    authenticated = requests.Session()
    authenticated.headers.update({**HEADERS, "Authorization": f"Bearer {token}"})
    release = release_by_tag(authenticated, TAG, allow_missing=True)
    created = release is None
    if release is None:
        release = create_release(authenticated, args.commit)
    release, uploaded = upload_missing(authenticated, release, snap)
    public = anonymous_readback(snap, args.commit)
    after = old_release_witness()
    if after != before:
        raise RuntimeError("prior release witness changed during the target-release transaction")
    publication = {
        **base,
        "mode": "publish",
        "credential_access": True,
        "created_target_release": created,
        "uploaded_assets": uploaded,
        "existing_assets_preserved": len(snap.files) - len(uploaded),
        "old_release_untouched": True,
        "old_release_witness": after,
        "public": public,
    }
    atomic_json(PUBLICATION_RECEIPT, publication)
    atomic_json(RECEIPT, {**publication, "mode": "verify-published", "credential_access": False})
    print(json.dumps({"mode": "publish", "tag": TAG, "commit": args.commit, "release_id": public["release_id"], "files": len(snap.files), "uploaded": len(uploaded), "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
