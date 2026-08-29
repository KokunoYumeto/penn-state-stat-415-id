#!/usr/bin/env python3
"""Verify the cumulative C4 Pages collection without any browser process.

``--contract-only`` validates the complete local Pages assembly against the
live cumulative C4 companion reader and receipts.  It performs no network or
credential access.  ``--write`` and ``--check-only`` retain the hardened C1
static-HTTPS anonymous-byte verifier under C4-specific receipt/schema
identities.  This adapter never launches a browser process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

import truststore

import verify_pages_c140_companion_c1 as engine


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "build" / "PAGES_COLLECTION_RECEIPT.json"
COMPONENT = ROOT / "components" / "c140-companion"
COMPANION_HTML = COMPONENT / "build" / "html-id"
BUILD_RECEIPT = COMPONENT / "build" / "C4_BUILD_RECEIPT.json"
QA_RECEIPT = COMPONENT / "build" / "C4_QA_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_PAGES_RECEIPT_2026-08-29_C140_COMPANION_C4.json"
SCHEMA = "o006.c140.companion-c4.github-pages-readback.v1"
EXPECTED_COLLECTION_FILES = 188
EXPECTED_COLLECTION_BYTES = 22_437_587
EXPECTED_COMPANION_FILES = 64
EXPECTED_COMPANION_IDS = {
    "O006-C140-CMP-INDEX",
    "O006-C140-CMP-CA01",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 14)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 7)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(0, 13)),
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def object_file(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is unavailable or invalid") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def local_contract() -> dict[str, object]:
    collection_payload = COLLECTION.read_bytes()
    collection, rows = engine.validate_collection(collection_payload)
    build = object_file(BUILD_RECEIPT, "C4 build receipt")
    qa = object_file(QA_RECEIPT, "C4 QA receipt")
    ids = build.get("cumulative_required_ids")
    collection_info = collection.get("collection")
    if (
        not isinstance(collection_info, dict)
        or collection_info.get("files") != EXPECTED_COLLECTION_FILES
        or collection_info.get("bytes") != EXPECTED_COLLECTION_BYTES
    ):
        raise RuntimeError("live Pages collection differs from the admitted C4 boundary")
    if (
        build.get("schema") != "o006.c140.companion-cumulative-c4-build.v1"
        or build.get("status") != "pass"
        or build.get("boundary") != "cumulative-through-c4"
        or build.get("browser_processes_used") is not False
        or build.get("network_access") is not False
        or not isinstance(ids, list)
        or set(ids) != EXPECTED_COMPANION_IDS
        or len(ids) != len(EXPECTED_COMPANION_IDS)
        or qa.get("schema") != "o006.c140.companion-cumulative-c4-qa.v1"
        or qa.get("status") != "pass"
        or qa.get("browser_processes_used") is not False
        or qa.get("network_access") is not False
        or qa.get("build_receipt_sha256") != sha256(BUILD_RECEIPT.read_bytes())
    ):
        raise RuntimeError("live C4 build/QA boundary differs")

    partition = sorted(
        (row for row in rows if row.get("source") == "c140-original-companion"),
        key=lambda row: str(row["source_path"]),
    )
    expected: list[dict[str, object]] = []
    if COMPANION_HTML.is_symlink() or not COMPANION_HTML.is_dir():
        raise RuntimeError("live C4 HTML reader is missing or unsafe")
    for path in sorted(COMPANION_HTML.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"symlink in live C4 HTML reader: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(COMPANION_HTML).as_posix()
        payload = path.read_bytes()
        expected.append({"source_path": relative, "bytes": len(payload), "sha256": sha256(payload)})
    expected.sort(key=lambda row: str(row["source_path"]))
    actual = [
        {"source_path": row["source_path"], "bytes": row["bytes"], "sha256": row["sha256"]}
        for row in partition
    ]
    if len(expected) != EXPECTED_COMPANION_FILES or actual != expected:
        raise RuntimeError("Pages companion partition is not byte-identical to the live C4 reader")
    info = collection["inputs"]["c140_original_companion"]
    build_html = build.get("html")
    if (
        not isinstance(build_html, dict)
        or info.get("path") != "components/c140-companion/build/html-id"
        or info.get("mount") != "components/c140-companion"
        or info.get("files") != EXPECTED_COMPANION_FILES
        or info.get("files") != len(expected)
        or info.get("bytes") != sum(int(row["bytes"]) for row in expected)
        or build_html.get("files") != EXPECTED_COMPANION_FILES
        or build_html.get("files") != len(expected)
        or build_html.get("bytes") != sum(int(row["bytes"]) for row in expected)
        or build_html.get("manifest_sha256") != sha256((COMPANION_HTML / "MANIFEST.csv").read_bytes())
    ):
        raise RuntimeError("Pages C4 input aggregate differs from the live build receipt")
    return {
        "browser_processes_used": False,
        "collection_bytes": collection_info["bytes"],
        "collection_files": collection_info["files"],
        "collection_manifest_sha256": collection_info["manifest_sha256"],
        "collection_receipt_sha256": sha256(collection_payload),
        "companion_bytes": info["bytes"],
        "companion_files": info["files"],
        "companion_html_manifest_sha256": build_html["manifest_sha256"],
        "credential_access": False,
        "mode": "contract-only",
        "network_access": False,
        "schema": SCHEMA,
        "status": "pass",
    }


def configure_engine() -> None:
    for url, label in ((engine.BASE_URL, "Pages base URL"), (engine.API, "GitHub API URL")):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RuntimeError(f"{label} must be static HTTPS")
    engine.COLLECTION = COLLECTION
    engine.RECEIPT = RECEIPT
    engine.SCHEMA = SCHEMA
    engine.CONTENT_HEADERS = {
        **engine.CONTENT_HEADERS,
        "User-Agent": "O006-C140-companion-c4-static-readback/2026.08.29",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--contract-only", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit")
    parser.add_argument("--run-id", type=int)
    args = parser.parse_args()
    if args.contract_only:
        if args.commit or args.run_id is not None:
            raise RuntimeError("--contract-only does not accept remote identities")
        print(json.dumps(local_contract(), sort_keys=True))
        return
    configure_engine()
    if args.write:
        if not args.commit or args.run_id is None:
            raise RuntimeError("--write requires --commit and --run-id")
        if re.fullmatch(r"[0-9a-f]{40}", args.commit) is None:
            raise RuntimeError("commit must be a full 40-character lowercase Git SHA")
        commit_id, run_id = args.commit, args.run_id
    else:
        if args.commit or args.run_id is not None:
            raise RuntimeError("--check-only reads the pinned receipt identity")
        existing = object_file(RECEIPT, "C4 Pages receipt")
        commit_id = str(existing["control_plane"]["content_commit"])
        run_id = int(existing["control_plane"]["workflow_run_id"])
    payload = engine.compute(commit_id, run_id)
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_bytes(payload)
        state = "written"
    else:
        if RECEIPT.read_bytes() != payload:
            raise RuntimeError("public C4 Pages receipt deterministic replay mismatch")
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
