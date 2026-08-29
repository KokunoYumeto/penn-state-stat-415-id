#!/usr/bin/env python3
"""Direct, anonymous byte readback for the public C140 companion C4 release.

This verifier deliberately does not call the GitHub API, read a credential
file, invoke Git, or launch a browser.  It derives the 57-asset expectation
from the local C4 package receipt and downloads each stable public release URL
directly.  Redirects are never followed automatically: at most one HTTPS
handoff to an explicit GitHub-owned asset CDN is admitted.

``--write`` performs the readback and atomically writes the canonical receipt.
``--check`` repeats the readback and requires the canonical bytes to match the
existing receipt exactly.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json"
OUTPUT_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_DIRECT_READBACK_2026-08-29_C140_COMPANION_C4.json"
)

SCHEMA = "o006.c140.companion-c4.github-release-direct-readback.v1"
PACKAGE_SCHEMA = "o006.c140.companion-c4-release-package.v1"
PACKAGE_VERSION = "2026.08.29.c140-companion-c4"
REPOSITORY = "https://github.com/KokunoYumeto/penn-state-stat-415-id"
TAG = "v2026.08.29.c140-companion-c4"
COMMIT = "9b10b3e04b451232b1233d0b35cf31c3860d63db"
TAG_OBJECT = "1dd397eeb0d717046e4f31a5d65abe97c3c9567b"
RELEASE_ID = 379_047_752
RELEASE_URL = f"{REPOSITORY}/releases/tag/{TAG}"

EXPECTED_FILE_COUNT = 57
EXPECTED_BYTES = 93_850_993
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SAFE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
REDIRECT_CODES = {301, 302, 303, 307, 308}
ALLOWED_INITIAL_HOST = "github.com"
ALLOWED_CDN_HOSTS = frozenset(
    {
        "release-assets.githubusercontent.com",
        "objects.githubusercontent.com",
        "github-releases.githubusercontent.com",
    }
)
USER_AGENT = "O006-C140-C4-direct-release-readback/2026.08.29"
MAX_WORKERS = 4
CHUNK_BYTES = 1024 * 1024


class VerificationError(RuntimeError):
    """A fail-closed contract or public-byte verification error."""


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def read_package() -> tuple[dict[str, Any], bytes]:
    try:
        payload = PACKAGE_RECEIPT.read_bytes()
    except OSError as exc:
        raise VerificationError(f"cannot read package receipt: {PACKAGE_RECEIPT}") from exc
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("package receipt is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise VerificationError("package receipt root must be an object")
    return value, payload


def expected_inventory(package: dict[str, Any]) -> list[dict[str, object]]:
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != PACKAGE_VERSION
        or package.get("status") != "ready"
    ):
        raise VerificationError("package receipt identity/status differs")
    publication = package.get("publication_inventory")
    if not isinstance(publication, dict):
        raise VerificationError("package receipt lacks publication_inventory")
    rows = publication.get("files")
    if not isinstance(rows, list):
        raise VerificationError("package publication inventory is not a list")
    if (
        publication.get("file_count") != EXPECTED_FILE_COUNT
        or publication.get("bytes") != EXPECTED_BYTES
        or len(rows) != EXPECTED_FILE_COUNT
    ):
        raise VerificationError("package publication inventory totals differ")

    admitted: list[dict[str, object]] = []
    names: set[str] = set()
    byte_total = 0
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise VerificationError(f"package inventory row {index} is not an object")
        name = row.get("filename")
        size = row.get("bytes")
        digest = row.get("sha256")
        source_path = row.get("source_path")
        upload_order = row.get("upload_order")
        if (
            not isinstance(name, str)
            or SAFE_NAME_RE.fullmatch(name) is None
            or "/" in name
            or "\\" in name
            or name in names
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size <= 0
            or not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
            or source_path != f"release/{name}"
            or upload_order != index
        ):
            raise VerificationError(f"package inventory row {index} is not admitted")
        names.add(name)
        byte_total += size
        stable_url = (
            f"{REPOSITORY}/releases/download/"
            f"{quote(TAG, safe='')}/{quote(name, safe='')}"
        )
        parsed = urlparse(stable_url)
        expected_path_prefix = "/KokunoYumeto/penn-state-stat-415-id/releases/download/"
        if (
            parsed.scheme != "https"
            or parsed.hostname != ALLOWED_INITIAL_HOST
            or parsed.port not in (None, 443)
            or not parsed.path.startswith(expected_path_prefix)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
        ):
            raise VerificationError(f"constructed release URL is not admitted: {name}")
        admitted.append(
            {
                "upload_order": index,
                "filename": name,
                "bytes": size,
                "sha256": digest,
                "download_url": stable_url,
            }
        )
    if byte_total != EXPECTED_BYTES:
        raise VerificationError("package inventory byte sum differs")
    return admitted


def anonymous_session() -> requests.Session:
    session = requests.Session()
    # This prevents requests from consulting .netrc, proxy credentials, or
    # environment-provided authentication material.
    session.trust_env = False
    session.headers.clear()
    session.headers.update(
        {
            "Accept": "application/octet-stream",
            "User-Agent": USER_AGENT,
        }
    )
    return session


def assert_anonymous_request(response: requests.Response, label: str) -> None:
    sent = {key.casefold() for key in response.request.headers}
    forbidden = {"authorization", "cookie", "proxy-authorization"}
    if sent.intersection(forbidden):
        raise VerificationError(f"credential-bearing header appeared in {label}")


def hash_stream(response: requests.Response, expected_size: int, name: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    try:
        for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
            if not chunk:
                continue
            count += len(chunk)
            if count > expected_size:
                raise VerificationError(f"public asset exceeds expected size: {name}")
            digest.update(chunk)
    except requests.RequestException as exc:
        raise VerificationError(f"stream failed for public asset: {name}") from exc
    return count, digest.hexdigest()


def verify_one(row: dict[str, object]) -> dict[str, object]:
    name = str(row["filename"])
    stable_url = str(row["download_url"])
    expected_size = int(row["bytes"])
    expected_sha = str(row["sha256"])
    first_session = anonymous_session()
    first: requests.Response | None = None
    second: requests.Response | None = None
    try:
        try:
            first = first_session.get(
                stable_url,
                allow_redirects=False,
                stream=True,
                timeout=(30, 900),
            )
        except requests.RequestException as exc:
            raise VerificationError(f"initial public request failed: {name}") from exc
        assert_anonymous_request(first, f"initial request for {name}")

        if first.status_code in REDIRECT_CODES:
            location = first.headers.get("Location")
            target_url = urljoin(stable_url, str(location or ""))
            target = urlparse(target_url)
            target_host = (target.hostname or "").casefold()
            if (
                target.scheme.casefold() != "https"
                or target_host not in ALLOWED_CDN_HOSTS
                or target.port not in (None, 443)
                or not target.path
                or target.username is not None
                or target.password is not None
                or target.fragment
            ):
                raise VerificationError(f"unadmitted release redirect target: {name}")
            first.close()
            first = None
            cdn_session = anonymous_session()
            try:
                try:
                    second = cdn_session.get(
                        target_url,
                        allow_redirects=False,
                        stream=True,
                        timeout=(30, 900),
                    )
                except requests.RequestException as exc:
                    raise VerificationError(f"CDN request failed: {name}") from exc
                assert_anonymous_request(second, f"CDN request for {name}")
                if second.status_code in REDIRECT_CODES or second.status_code != 200:
                    raise VerificationError(f"CDN handoff did not terminate with HTTP 200: {name}")
                size, digest = hash_stream(second, expected_size, name)
            finally:
                if second is not None:
                    second.close()
                cdn_session.close()
            handoff = True
            final_host_class = "github-owned-asset-cdn"
        elif first.status_code == 200:
            size, digest = hash_stream(first, expected_size, name)
            handoff = False
            final_host_class = "github.com"
        else:
            raise VerificationError(
                f"public release download returned HTTP {first.status_code}: {name}"
            )
        if size != expected_size or digest != expected_sha:
            raise VerificationError(f"public release bytes differ: {name}")
        return {
            "upload_order": row["upload_order"],
            "filename": name,
            "bytes": size,
            "sha256": digest,
            "download_url": stable_url,
            "http_status": 200,
            "validated_download": True,
            "validated_redirect_chain": True,
            "redirect_handoff_used": handoff,
            "final_host_class": final_host_class,
            "automatic_redirects_followed": False,
            "credential_headers_sent": False,
        }
    finally:
        if first is not None:
            first.close()
        first_session.close()


def build_receipt() -> dict[str, object]:
    package, package_payload = read_package()
    expected = expected_inventory(package)
    verified: list[dict[str, object] | None] = [None] * len(expected)
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(verify_one, row): index for index, row in enumerate(expected)}
        try:
            for future in as_completed(futures):
                index = futures[future]
                verified[index] = future.result()
        except BaseException:
            for future in futures:
                future.cancel()
            raise
    if any(row is None for row in verified):
        raise VerificationError("public verification did not return every inventory row")
    files = [row for row in verified if row is not None]
    if (
        len(files) != EXPECTED_FILE_COUNT
        or sum(int(row["bytes"]) for row in files) != EXPECTED_BYTES
    ):
        raise VerificationError("verified public totals differ")
    script_payload = Path(__file__).read_bytes()
    return {
        "schema": SCHEMA,
        "status": "pass",
        "verified_on": "2026-08-29",
        "repository": REPOSITORY,
        "release": {
            "release_id": RELEASE_ID,
            "release_url": RELEASE_URL,
            "tag": TAG,
            "tag_object": TAG_OBJECT,
            "commit": COMMIT,
        },
        "expected_source": {
            "path": "build/C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json",
            "schema": PACKAGE_SCHEMA,
            "version": PACKAGE_VERSION,
            "bytes": len(package_payload),
            "sha256": sha256_bytes(package_payload),
        },
        "verifier": {
            "path": "scripts/verify_github_release_direct_c140_companion_c4.py",
            "bytes": len(script_payload),
            "sha256": sha256_bytes(script_payload),
            "github_api_calls": 0,
            "credential_access": False,
            "credential_files_read": False,
            "authorization_headers_sent": False,
            "browser_processes_used": False,
            "browser_modules_used": False,
            "git_operations": False,
            "automatic_redirects_followed": False,
            "redirect_policy": (
                "direct HTTPS github.com release URL; at most one manually validated "
                "HTTPS handoff to an enumerated GitHub-owned asset CDN; no further redirect"
            ),
            "allowed_initial_host": ALLOWED_INITIAL_HOST,
            "allowed_redirect_hosts": sorted(ALLOWED_CDN_HOSTS),
            "requests_trust_environment": False,
            "worker_count": MAX_WORKERS,
        },
        "public_readback": {
            "mode": "credential-free-direct-release-byte-readback",
            "file_count": len(files),
            "bytes": sum(int(row["bytes"]) for row in files),
            "all_bytes_and_sha256_match": True,
            "all_redirects_github_owned": True,
            "reader_first": files[0]["filename"]
            == "00_00_stat415-pengantar-statistika-matematis-id.pdf",
            "files": files,
        },
    }


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="verify and write receipt")
    mode.add_argument("--check", action="store_true", help="verify and compare receipt")
    args = parser.parse_args(argv)

    receipt = build_receipt()
    payload = canonical_json(receipt)
    if args.write:
        atomic_write(OUTPUT_RECEIPT, payload)
        action = "wrote"
    else:
        try:
            existing = OUTPUT_RECEIPT.read_bytes()
        except OSError as exc:
            raise VerificationError(f"cannot read existing receipt: {OUTPUT_RECEIPT}") from exc
        if existing != payload:
            raise VerificationError("existing direct-readback receipt differs from replay")
        action = "checked"
    print(
        json.dumps(
            {
                "status": "pass",
                "action": action,
                "receipt": str(OUTPUT_RECEIPT),
                "receipt_bytes": len(payload),
                "receipt_sha256": sha256_bytes(payload),
                "files": EXPECTED_FILE_COUNT,
                "bytes": EXPECTED_BYTES,
                "api_calls": 0,
                "credential_access": False,
                "browser_processes_used": False,
                "git_operations": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except VerificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

