#!/usr/bin/env python3
"""Paced, credential-free direct readback of the public C140 C4 Zenodo record.

``--write`` performs exactly one logical public-record metadata fetch, then
downloads all 57 files sequentially over HTTPS.  Transient failures and HTTP
429 responses are retried with bounded exponential delay; an admitted
``Retry-After`` value takes precedence.  No credential, environment proxy,
browser, Git operation, or Zenodo deposition endpoint is used.

``--check`` is deliberately network-free.  It validates the canonical receipt
against the current package contract and verifier bytes, so a write followed by
a check does not turn the requested one-metadata-fetch readback into a second
network run.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.parse import urljoin, urlparse

import requests


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json"
OUTPUT_RECEIPT = (
    ROOT
    / "00_control"
    / "ZENODO_DIRECT_READBACK_2026-08-29_C140_COMPANION_C4.json"
)

SCHEMA = "o006.c140.companion-c4.zenodo-direct-readback.v1"
PACKAGE_SCHEMA = "o006.c140.companion-c4-release-package.v1"
VERSION = "2026.08.29.c140-companion-c4"
RECORD_ID = "22164344"
RECORD_DOI = "10.5281/zenodo.22164344"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
RECORD_API_URL = f"https://zenodo.org/api/records/{RECORD_ID}"
RECORD_PUBLIC_URL = f"https://zenodo.org/records/{RECORD_ID}"

EXPECTED_FILE_COUNT = 57
EXPECTED_BYTES = 93_850_993
USER_AGENT = "O006-C140-C4-Zenodo-direct-readback/2026.08.29"
PACE_SECONDS = 0.80
MAX_ATTEMPTS = 7
MAX_REDIRECTS = 4
MAX_BACKOFF_SECONDS = 60.0
CONNECT_TIMEOUT_SECONDS = 30
READ_TIMEOUT_SECONDS = 900
CHUNK_BYTES = 1024 * 1024
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
REDIRECT_STATUS = frozenset({301, 302, 303, 307, 308})
ALLOWED_HOST = "zenodo.org"
FORBIDDEN_REQUEST_HEADERS = frozenset(
    {"authorization", "cookie", "proxy-authorization"}
)
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SAFE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


class VerificationError(RuntimeError):
    """A fail-closed package, metadata, or public-byte verification error."""


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
        or package.get("version") != VERSION
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
            or row.get("source_path") != f"release/{name}"
            or row.get("upload_order") != index
        ):
            raise VerificationError(f"package inventory row {index} is not admitted")
        names.add(name)
        byte_total += size
        admitted.append(
            {
                "upload_order": index,
                "filename": name,
                "bytes": size,
                "sha256": digest,
            }
        )
    if byte_total != EXPECTED_BYTES:
        raise VerificationError("package inventory byte sum differs")
    return admitted


def validate_https_url(value: object, label: str, *, record_file: bool) -> str:
    if not isinstance(value, str) or not value:
        raise VerificationError(f"{label} omitted its URL")
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise VerificationError(f"{label} has an invalid port") from exc
    admitted_prefixes = (
        f"/api/records/{RECORD_ID}/",
        "/api/files/",
        f"/records/{RECORD_ID}/",
    )
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != ALLOWED_HOST
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or (record_file and not any(parsed.path.startswith(p) for p in admitted_prefixes))
    ):
        raise VerificationError(f"{label} is not an admitted Zenodo HTTPS URL")
    return value


def anonymous_session(accept: str) -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.clear()
    session.headers.update({"Accept": accept, "User-Agent": USER_AGENT})
    session.cookies.clear()
    return session


def assert_anonymous_request(response: requests.Response, label: str) -> None:
    sent = {key.casefold() for key in response.request.headers}
    if sent.intersection(FORBIDDEN_REQUEST_HEADERS):
        raise VerificationError(f"credential-bearing header appeared in {label}")


def retry_delay(response: requests.Response | None, attempt: int) -> float:
    value = response.headers.get("Retry-After") if response is not None else None
    if value:
        stripped = value.strip()
        try:
            seconds = float(stripped)
        except ValueError:
            try:
                when = parsedate_to_datetime(stripped)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                seconds = (when - datetime.now(timezone.utc)).total_seconds()
            except (TypeError, ValueError, OverflowError):
                seconds = 0.0
        if seconds > 0:
            return min(seconds, MAX_BACKOFF_SECONDS)
    return min(float(2 ** (attempt - 1)), MAX_BACKOFF_SECONDS)


def bounded_sleep(seconds: float) -> None:
    remaining = max(0.0, seconds)
    while remaining > 0:
        interval = min(remaining, MAX_BACKOFF_SECONDS)
        time.sleep(interval)
        remaining -= interval


def request_once(
    url: str, *, accept: str, stream: bool, label: str
) -> tuple[requests.Session, requests.Response, str, int]:
    current = validate_https_url(url, label, record_file=(url != RECORD_API_URL))
    redirects = 0
    while True:
        session = anonymous_session(accept)
        try:
            response = session.get(
                current,
                allow_redirects=False,
                stream=stream,
                timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
            )
        except requests.RequestException:
            session.close()
            raise
        assert_anonymous_request(response, label)
        if response.status_code not in REDIRECT_STATUS:
            return session, response, current, redirects
        if redirects >= MAX_REDIRECTS:
            response.close()
            session.close()
            raise VerificationError(f"too many redirects for {label}")
        location = response.headers.get("Location")
        target = urljoin(current, str(location or ""))
        validate_https_url(target, f"redirect for {label}", record_file=True)
        response.close()
        session.close()
        current = target
        redirects += 1


def fetch_metadata_once() -> tuple[dict[str, Any], int, int]:
    """Fetch one successful metadata document, retrying only transient failures."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        session: requests.Session | None = None
        response: requests.Response | None = None
        try:
            session, response, _url, redirects = request_once(
                RECORD_API_URL,
                accept="application/json",
                stream=False,
                label="public record metadata",
            )
            if response.status_code in RETRYABLE_STATUS:
                if attempt == MAX_ATTEMPTS:
                    raise VerificationError(
                        f"public metadata remained HTTP {response.status_code}"
                    )
                delay = retry_delay(response, attempt)
                response.close()
                session.close()
                response = None
                session = None
                bounded_sleep(delay)
                continue
            if response.status_code != 200:
                raise VerificationError(
                    f"public metadata returned HTTP {response.status_code}"
                )
            try:
                value = response.json()
            except (ValueError, requests.RequestException) as exc:
                raise VerificationError("public metadata is not valid JSON") from exc
            if not isinstance(value, dict):
                raise VerificationError("public metadata root is not an object")
            return value, attempt, redirects
        except requests.RequestException as exc:
            if attempt == MAX_ATTEMPTS:
                raise VerificationError("public metadata request failed repeatedly") from exc
            bounded_sleep(retry_delay(None, attempt))
        finally:
            if response is not None:
                response.close()
            if session is not None:
                session.close()
    raise VerificationError("unreachable metadata retry state")


def validate_metadata(
    record: dict[str, Any], expected: list[dict[str, object]]
) -> tuple[dict[str, dict[str, Any]], dict[str, object]]:
    metadata = record.get("metadata")
    if not isinstance(metadata, dict):
        raise VerificationError("public record lacks metadata")
    concept_id = str(record.get("conceptrecid") or record.get("concept_record_id") or "")
    concept_doi = str(record.get("conceptdoi") or record.get("concept_doi") or "")
    if (
        str(record.get("id")) != RECORD_ID
        or str(record.get("doi")) != RECORD_DOI
        or concept_id != CONCEPT_RECORD_ID
        or concept_doi != CONCEPT_DOI
        or metadata.get("version") != VERSION
    ):
        raise VerificationError("public record/concept/DOI/version identity differs")

    access_right = metadata.get("access_right")
    if access_right not in (None, "open"):
        raise VerificationError("public record metadata is not open access")
    top_access = record.get("access")
    if isinstance(top_access, dict):
        if top_access.get("record") not in (None, "public"):
            raise VerificationError("top-level record access is not public")
        if top_access.get("files") not in (None, "public"):
            raise VerificationError("top-level file access is not public")

    rows = record.get("files")
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise VerificationError("public record file inventory is malformed")
    names = [str(row.get("key", "")) for row in rows]
    expected_names = [str(row["filename"]) for row in expected]
    if len(names) != len(set(names)) or set(names) != set(expected_names):
        raise VerificationError("public record file inventory is not the exact package set")
    by_name = {str(row["key"]): row for row in rows}
    for item in expected:
        name = str(item["filename"])
        row = by_name[name]
        if row.get("size") != item["bytes"]:
            raise VerificationError(f"public metadata byte count differs: {name}")
        links = row.get("links")
        if not isinstance(links, dict):
            raise VerificationError(f"public metadata lacks file links: {name}")
        validate_https_url(
            links.get("content") or links.get("self"),
            f"public file {name}",
            record_file=True,
        )

    normalized_access = {
        "metadata_access_right": access_right,
        "top_level_record_access": (
            top_access.get("record") if isinstance(top_access, dict) else None
        ),
        "top_level_file_access": (
            top_access.get("files") if isinstance(top_access, dict) else None
        ),
        "public_record_api_access": True,
        "anonymous_file_access_required": True,
    }
    return by_name, normalized_access


def download_one(
    expected: dict[str, object], metadata_row: dict[str, Any]
) -> dict[str, object]:
    name = str(expected["filename"])
    size_expected = int(expected["bytes"])
    sha_expected = str(expected["sha256"])
    links = metadata_row.get("links")
    if not isinstance(links, dict):
        raise VerificationError(f"public metadata lacks file links: {name}")
    stable_url = validate_https_url(
        links.get("content") or links.get("self"),
        f"public file {name}",
        record_file=True,
    )
    metadata_checksum = str(metadata_row.get("checksum") or "")
    metadata_md5 = metadata_checksum[4:] if metadata_checksum.startswith("md5:") else ""
    if metadata_md5 and re.fullmatch(r"[0-9a-f]{32}", metadata_md5) is None:
        raise VerificationError(f"public metadata checksum is malformed: {name}")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        session: requests.Session | None = None
        response: requests.Response | None = None
        try:
            session, response, final_url, redirects = request_once(
                stable_url,
                # Zenodo's public content endpoint returns HTTP 406 for an
                # octet-stream-only Accept header on typed files (for example
                # application/pdf).  A credential-free wildcard admits the
                # record's declared media type without changing the URL.
                accept="*/*",
                stream=True,
                label=f"public file {name}",
            )
            if response.status_code in RETRYABLE_STATUS:
                if attempt == MAX_ATTEMPTS:
                    raise VerificationError(
                        f"public file remained HTTP {response.status_code}: {name}"
                    )
                delay = retry_delay(response, attempt)
                response.close()
                session.close()
                response = None
                session = None
                bounded_sleep(delay)
                continue
            if response.status_code != 200:
                raise VerificationError(
                    f"public file returned HTTP {response.status_code}: {name}"
                )

            sha256 = hashlib.sha256()
            md5 = hashlib.md5(usedforsecurity=False)
            count = 0
            for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
                if not chunk:
                    continue
                count += len(chunk)
                if count > size_expected:
                    raise VerificationError(f"public file exceeds expected size: {name}")
                sha256.update(chunk)
                md5.update(chunk)
            digest = sha256.hexdigest()
            md5_digest = md5.hexdigest()
            if count != size_expected or digest != sha_expected:
                raise VerificationError(f"public file bytes differ: {name}")
            if metadata_md5 and md5_digest != metadata_md5:
                raise VerificationError(f"public file MD5 differs from metadata: {name}")
            return {
                "upload_order": expected["upload_order"],
                "filename": name,
                "download_url": stable_url,
                "final_url": final_url,
                "http_status": 200,
                "redirect_count": redirects,
                "bytes": count,
                "sha256": digest,
                "metadata_checksum": metadata_checksum or None,
                "metadata_checksum_matches": (not metadata_md5) or md5_digest == metadata_md5,
                "validated_download": True,
                "credential_headers_sent": False,
            }
        except requests.RequestException as exc:
            if attempt == MAX_ATTEMPTS:
                raise VerificationError(f"public file request failed repeatedly: {name}") from exc
            bounded_sleep(retry_delay(None, attempt))
        finally:
            if response is not None:
                response.close()
            if session is not None:
                session.close()
    raise VerificationError(f"unreachable file retry state: {name}")


def build_receipt() -> dict[str, object]:
    package, package_payload = read_package()
    expected = expected_inventory(package)
    record, metadata_attempts, metadata_redirects = fetch_metadata_once()
    by_name, access = validate_metadata(record, expected)

    verified: list[dict[str, object]] = []
    for index, item in enumerate(expected):
        if index:
            bounded_sleep(PACE_SECONDS)
        verified.append(download_one(item, by_name[str(item["filename"])]))
    if (
        len(verified) != EXPECTED_FILE_COUNT
        or sum(int(row["bytes"]) for row in verified) != EXPECTED_BYTES
    ):
        raise VerificationError("verified public totals differ")

    script_payload = Path(__file__).read_bytes()
    return {
        "schema": SCHEMA,
        "status": "pass",
        "verified_on": "2026-08-29",
        "verification_role": "independent-second-anonymous-readback",
        "record": {
            "record_id": RECORD_ID,
            "doi": RECORD_DOI,
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "version": VERSION,
            "public_url": RECORD_PUBLIC_URL,
            "metadata_url": RECORD_API_URL,
            "metadata_http_status": 200,
            "metadata_successful_fetches": 1,
            "metadata_http_attempts": metadata_attempts,
            "metadata_redirect_count": metadata_redirects,
            "public_access": True,
            "access_evidence": access,
        },
        "expected_source": {
            "path": "build/C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json",
            "schema": PACKAGE_SCHEMA,
            "version": VERSION,
            "bytes": len(package_payload),
            "sha256": sha256_bytes(package_payload),
        },
        "verifier": {
            "path": "scripts/verify_zenodo_direct_c140_companion_c4.py",
            "bytes": len(script_payload),
            "sha256": sha256_bytes(script_payload),
            "network_protocol": "HTTPS-only",
            "metadata_fetch_policy": "one successful public-record metadata document",
            "sequential_downloads": True,
            "pacing_seconds_between_files": PACE_SECONDS,
            "max_attempts_per_request": MAX_ATTEMPTS,
            "retryable_http_statuses": sorted(RETRYABLE_STATUS),
            "retry_after_aware": True,
            "maximum_single_backoff_seconds": MAX_BACKOFF_SECONDS,
            "requests_trust_environment": False,
            "credential_access": False,
            "credential_files_read": False,
            "authorization_headers_sent": False,
            "cookies_sent": False,
            "browser_processes_used": False,
            "browser_modules_used": False,
            "git_operations": False,
            "zenodo_public_record_api_http_attempts": metadata_attempts,
            "zenodo_deposition_api_calls": 0,
            "check_mode_network_calls": 0,
        },
        "public_readback": {
            "mode": "credential-free-static-https-full-byte-readback",
            "file_count": len(verified),
            "bytes": sum(int(row["bytes"]) for row in verified),
            "all_files_downloadable_anonymously": True,
            "all_bytes_and_sha256_match": True,
            "all_metadata_sizes_match": True,
            "reader_first": verified[0]["filename"]
            == "00_00_stat415-pengantar-statistika-matematis-id.pdf",
            "files": verified,
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


def check_local_receipt() -> tuple[bytes, dict[str, Any]]:
    package, package_payload = read_package()
    expected = expected_inventory(package)
    try:
        payload = OUTPUT_RECEIPT.read_bytes()
        receipt = json.loads(payload)
    except OSError as exc:
        raise VerificationError(f"cannot read receipt: {OUTPUT_RECEIPT}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VerificationError("direct-readback receipt is not valid UTF-8 JSON") from exc
    if not isinstance(receipt, dict) or payload != canonical_json(receipt):
        raise VerificationError("direct-readback receipt is not canonical JSON")
    source = receipt.get("expected_source")
    verifier = receipt.get("verifier")
    record = receipt.get("record")
    public = receipt.get("public_readback")
    script_payload = Path(__file__).read_bytes()
    if (
        receipt.get("schema") != SCHEMA
        or receipt.get("status") != "pass"
        or receipt.get("verification_role") != "independent-second-anonymous-readback"
        or not isinstance(source, dict)
        or source.get("bytes") != len(package_payload)
        or source.get("sha256") != sha256_bytes(package_payload)
        or not isinstance(verifier, dict)
        or verifier.get("bytes") != len(script_payload)
        or verifier.get("sha256") != sha256_bytes(script_payload)
        or verifier.get("credential_access") is not False
        or verifier.get("browser_processes_used") is not False
        or verifier.get("check_mode_network_calls") != 0
        or not isinstance(record, dict)
        or record.get("record_id") != RECORD_ID
        or record.get("doi") != RECORD_DOI
        or record.get("concept_record_id") != CONCEPT_RECORD_ID
        or record.get("concept_doi") != CONCEPT_DOI
        or record.get("version") != VERSION
        or record.get("public_access") is not True
        or not isinstance(public, dict)
        or public.get("file_count") != EXPECTED_FILE_COUNT
        or public.get("bytes") != EXPECTED_BYTES
        or public.get("all_files_downloadable_anonymously") is not True
        or public.get("all_bytes_and_sha256_match") is not True
    ):
        raise VerificationError("direct-readback receipt contract differs")
    files = public.get("files")
    if not isinstance(files, list) or len(files) != len(expected):
        raise VerificationError("direct-readback file inventory differs")
    for wanted, got in zip(expected, files):
        if not isinstance(got, dict) or (
            got.get("upload_order"),
            got.get("filename"),
            got.get("bytes"),
            got.get("sha256"),
            got.get("validated_download"),
            got.get("credential_headers_sent"),
        ) != (
            wanted["upload_order"],
            wanted["filename"],
            wanted["bytes"],
            wanted["sha256"],
            True,
            False,
        ):
            raise VerificationError(
                f"direct-readback row differs: {wanted['filename']}"
            )
        validate_https_url(
            got.get("download_url"),
            f"receipt file {wanted['filename']}",
            record_file=True,
        )
    return payload, receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="perform readback and write receipt")
    mode.add_argument("--check", action="store_true", help="network-free receipt check")
    args = parser.parse_args(argv)

    if args.write:
        receipt = build_receipt()
        payload = canonical_json(receipt)
        atomic_write(OUTPUT_RECEIPT, payload)
        action = "wrote"
    else:
        payload, _receipt = check_local_receipt()
        action = "checked-locally-without-network"
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

