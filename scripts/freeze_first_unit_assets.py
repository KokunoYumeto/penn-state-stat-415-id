#!/usr/bin/env python3
"""Freeze or verify the direct main-content assets for landing plus Lesson00."""

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
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin

import requests
import truststore
from bs4 import BeautifulSoup


truststore.inject_into_ssl()

ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
ASSETS = ROOT / "authority" / "assets" / "stat415"
MANIFEST = ROOT / "authority" / "FIRST_UNIT_ASSET_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "FIRST_UNIT_ASSET_RECEIPT.json"
BASE = "https://online.stat.psu.edu/stat415/"
DOCUMENTS = ("index.html", "Lesson00.html")
EXPECTED_NAMES = {f"assets/415lesson{number}thumb.png" for number in range(13)}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def discover() -> list[str]:
    names: set[str] = set()
    for filename in DOCUMENTS:
        soup = BeautifulSoup((NORMALIZED / filename).read_bytes(), "html.parser")
        for image in soup.select("main#quarto-document-content img[src]"):
            value = str(image["src"]).removeprefix("./")
            path = PurePosixPath(value)
            if path.is_absolute() or ".." in path.parts or not re.fullmatch(r"assets/415lesson(?:[0-9]|1[0-2])thumb\.png", path.as_posix()):
                raise RuntimeError(f"unexpected first-unit content asset: {value}")
            names.add(path.as_posix())
    if names != EXPECTED_NAMES:
        raise RuntimeError(f"first-unit asset set mismatch: {sorted(names ^ EXPECTED_NAMES)}")
    return sorted(names, key=str.casefold)


def canonical_manifest(rows: list[dict[str, object]]) -> bytes:
    fields = (
        "relative_path", "url", "final_url", "status", "content_type",
        "last_modified", "etag", "bytes", "sha256", "rights_status",
    )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def write_assets() -> None:
    names = discover()
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-first-unit-assets/1.0", "Accept": "image/png"})
    fetched: list[tuple[str, bytes]] = []
    rows: list[dict[str, object]] = []
    for name in names:
        url = urljoin(BASE, name)
        response = session.get(url, timeout=120, allow_redirects=True)
        if response.status_code != 200 or not response.headers.get("Content-Type", "").lower().startswith("image/png"):
            raise RuntimeError(f"invalid asset response: {url} / {response.status_code} / {response.headers.get('Content-Type')}")
        payload = response.content
        fetched.append((name, payload))
        rows.append(
            {
                "relative_path": name,
                "url": url,
                "final_url": response.url,
                "status": response.status_code,
                "content_type": response.headers.get("Content-Type", ""),
                "last_modified": response.headers.get("Last-Modified", ""),
                "etag": response.headers.get("ETag", ""),
                "bytes": len(payload),
                "sha256": sha256(payload),
                "rights_status": "page-level-CC-BY-NC-4.0-no-component-exception-observed",
            }
        )
    manifest = canonical_manifest(rows)
    retrieved = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    receipt = (
        json.dumps(
            {
                "schema": "o006.stat415.first-unit-assets.v1",
                "status": "frozen",
                "retrieved_utc": retrieved,
                "documents": list(DOCUMENTS),
                "asset_count": len(rows),
                "bytes": sum(len(payload) for _, payload in fetched),
                "manifest": {"path": "authority/FIRST_UNIT_ASSET_MANIFEST.csv", "bytes": len(manifest), "sha256": sha256(manifest)},
                "rights_basis": (
                    "The official landing and Lesson00 pages state CC BY-NC 4.0 except where otherwise noted; "
                    "no asset-specific exception is visible for these thirteen course thumbnails. Preserve the "
                    "manifest and do not generalize this status to other course assets."
                ),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    for name, payload in fetched:
        atomic_write(ASSETS / Path(name), payload)
    atomic_write(MANIFEST, manifest)
    atomic_write(RECEIPT, receipt)
    print(json.dumps({"mode": "written", "assets": len(rows), "bytes": sum(len(payload) for _, payload in fetched), "manifest_sha256": sha256(manifest), "receipt_sha256": sha256(receipt)}, sort_keys=True))


def check_only() -> None:
    names = discover()
    if not MANIFEST.is_file() or not RECEIPT.is_file():
        raise RuntimeError("asset manifest or receipt is missing")
    manifest = MANIFEST.read_bytes()
    rows = list(csv.DictReader(io.StringIO(manifest.decode("utf-8"), newline="")))
    if [row["relative_path"] for row in rows] != names:
        raise RuntimeError("asset manifest inventory differs from normalized first unit")
    total = 0
    for row in rows:
        path = ASSETS / Path(row["relative_path"])
        payload = path.read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"asset identity mismatch: {row['relative_path']}")
        total += len(payload)
    receipt_payload = RECEIPT.read_bytes()
    receipt = json.loads(receipt_payload.decode("utf-8"))
    if receipt.get("asset_count") != len(rows) or receipt.get("bytes") != total or receipt.get("manifest", {}).get("sha256") != sha256(manifest):
        raise RuntimeError("asset receipt differs from current evidence")
    print(json.dumps({"mode": "verified", "assets": len(rows), "bytes": total, "manifest_sha256": sha256(manifest), "receipt_sha256": sha256(receipt_payload)}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.write:
        write_assets()
    else:
        check_only()


if __name__ == "__main__":
    main()
