#!/usr/bin/env python3
"""Freeze or verify the exact fourteen-document Penn State STAT 415 authority."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import requests
import truststore


truststore.inject_into_ssl()


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "authority" / "expected" / "PSU_14_DOCUMENT_MANIFEST_20260821.csv"
UPSTREAM = ROOT / "authority" / "upstream" / "stat415"
MANIFEST = ROOT / "authority" / "SOURCE_URL_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "SOURCE_FREEZE_RECEIPT.json"
EXPECTED_MANIFEST_SHA256 = "d944524e9afb5d6dabba3bd0968b159397d7014a6e736f002f4db0ee2420ce91"
USER_AGENT = "O006-STAT415-source-freeze/1.0 (+https://github.com/KokunoYumeto)"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_expected() -> tuple[bytes, list[dict[str, str]]]:
    payload = EXPECTED.read_bytes()
    if digest(payload) != EXPECTED_MANIFEST_SHA256:
        raise RuntimeError("expected coordinator manifest identity mismatch")
    rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
    if len(rows) != 14:
        raise RuntimeError(f"expected exactly 14 documents, found {len(rows)}")
    ids: set[str] = set()
    for ordinal, row in enumerate(rows):
        component = row.get("component_id", "")
        if int(row.get("ordinal", "-1")) != ordinal:
            raise RuntimeError(f"non-contiguous ordinal at {ordinal}")
        if not re.fullmatch(r"index|Lesson(?:0[0-9]|1[0-2])", component):
            raise RuntimeError(f"unsafe component id: {component}")
        if component in ids:
            raise RuntimeError(f"duplicate component id: {component}")
        ids.add(component)
        if not row.get("url", "").startswith("https://online.stat.psu.edu/stat415/"):
            raise RuntimeError(f"unexpected authority URL: {row.get('url')}")
        if not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", "")):
            raise RuntimeError(f"invalid expected SHA-256: {component}")
    return payload, rows


def filename(component: str) -> str:
    return "index.html" if component == "index" else f"{component}.html"


def canonical_csv(rows: list[dict[str, object]]) -> bytes:
    fields = (
        "ordinal",
        "component_id",
        "url",
        "final_url",
        "status",
        "content_type",
        "last_modified",
        "etag",
        "bytes",
        "sha256",
        "local_path",
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def fetch_all(expected_rows: list[dict[str, str]]) -> tuple[list[tuple[dict[str, str], bytes]], list[dict[str, object]]]:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    fetched: list[tuple[dict[str, str], bytes]] = []
    manifest_rows: list[dict[str, object]] = []
    for row in expected_rows:
        response = session.get(row["url"], timeout=120, allow_redirects=True)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {row['url']}")
        payload = response.content
        actual_sha = digest(payload)
        actual_bytes = len(payload)
        if actual_bytes != int(row["bytes"]) or actual_sha != row["sha256"]:
            raise RuntimeError(
                f"authority drift at {row['component_id']}: "
                f"expected {row['bytes']}/{row['sha256']}, found {actual_bytes}/{actual_sha}"
            )
        component = row["component_id"]
        local_path = f"authority/upstream/stat415/{filename(component)}"
        fetched.append((row, payload))
        manifest_rows.append(
            {
                "ordinal": int(row["ordinal"]),
                "component_id": component,
                "url": row["url"],
                "final_url": response.url,
                "status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "last_modified": response.headers.get("Last-Modified", ""),
                "etag": response.headers.get("ETag", ""),
                "bytes": actual_bytes,
                "sha256": actual_sha,
                "local_path": local_path,
            }
        )
    return fetched, manifest_rows


def build_receipt(expected_payload: bytes, manifest_payload: bytes, manifest_rows: list[dict[str, object]], retrieved: str) -> bytes:
    total = sum(int(row["bytes"]) for row in manifest_rows)
    value = {
        "schema": "o006.stat415.source-freeze.v1",
        "status": "frozen",
        "retrieved_utc": retrieved,
        "authority": "official Penn State STAT 415 public semantic HTML",
        "boundary": "landing/index plus Lessons 00-12",
        "document_count": len(manifest_rows),
        "bytes": total,
        "expected_manifest": {
            "path": "authority/expected/PSU_14_DOCUMENT_MANIFEST_20260821.csv",
            "bytes": len(expected_payload),
            "sha256": digest(expected_payload),
        },
        "source_manifest": {
            "path": "authority/SOURCE_URL_MANIFEST.csv",
            "bytes": len(manifest_payload),
            "sha256": digest(manifest_payload),
        },
        "documents": manifest_rows,
        "source_limitation": (
            "Official semantic Quarto-generated HTML is frozen. No public QMD, "
            "Quarto configuration, source archive, tag, or commit is claimed."
        ),
    }
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_freeze() -> None:
    expected_payload, expected_rows = read_expected()
    fetched, manifest_rows = fetch_all(expected_rows)
    manifest_payload = canonical_csv(manifest_rows)
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt_payload = build_receipt(expected_payload, manifest_payload, manifest_rows, retrieved)
    for row, payload in fetched:
        atomic_write(UPSTREAM / filename(row["component_id"]), payload)
    atomic_write(MANIFEST, manifest_payload)
    atomic_write(RECEIPT, receipt_payload)
    print(
        json.dumps(
            {
                "mode": "written",
                "documents": len(manifest_rows),
                "bytes": sum(int(row["bytes"]) for row in manifest_rows),
                "manifest_sha256": digest(manifest_payload),
                "receipt_sha256": digest(receipt_payload),
            },
            sort_keys=True,
        )
    )


def check_only() -> None:
    expected_payload, expected_rows = read_expected()
    if not MANIFEST.is_file() or not RECEIPT.is_file():
        raise RuntimeError("source manifest or receipt is missing")
    manifest_payload = MANIFEST.read_bytes()
    manifest_rows = list(csv.DictReader(io.StringIO(manifest_payload.decode("utf-8"), newline="")))
    if len(manifest_rows) != 14:
        raise RuntimeError("frozen manifest is not exactly fourteen rows")
    for expected, actual in zip(expected_rows, manifest_rows, strict=True):
        component = expected["component_id"]
        if actual.get("component_id") != component or int(actual.get("ordinal", "-1")) != int(expected["ordinal"]):
            raise RuntimeError(f"frozen manifest order mismatch: {component}")
        path = ROOT / actual["local_path"]
        payload = path.read_bytes()
        if len(payload) != int(expected["bytes"]) or digest(payload) != expected["sha256"]:
            raise RuntimeError(f"frozen authority identity mismatch: {component}")
        if int(actual["bytes"]) != len(payload) or actual["sha256"] != digest(payload):
            raise RuntimeError(f"frozen source-manifest identity mismatch: {component}")
    receipt_payload = RECEIPT.read_bytes()
    receipt = json.loads(receipt_payload.decode("utf-8"))
    if (
        receipt.get("status") != "frozen"
        or receipt.get("document_count") != 14
        or receipt.get("bytes") != sum(int(row["bytes"]) for row in expected_rows)
        or receipt.get("expected_manifest", {}).get("sha256") != digest(expected_payload)
        or receipt.get("source_manifest", {}).get("sha256") != digest(manifest_payload)
    ):
        raise RuntimeError("source-freeze receipt differs from current evidence")
    print(
        json.dumps(
            {
                "mode": "verified",
                "documents": 14,
                "bytes": sum(int(row["bytes"]) for row in expected_rows),
                "manifest_sha256": digest(manifest_payload),
                "receipt_sha256": digest(receipt_payload),
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_freeze()
    else:
        check_only()


if __name__ == "__main__":
    main()
