#!/usr/bin/env python3
"""Freeze and deterministically verify the one direct Lesson 11 image asset."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import struct
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
URL = "https://online.stat.psu.edu/stat415/assets/bayes.png"
SOURCE_REFERENCE = "assets/bayes.png"
TARGET = ROOT / "authority" / "assets" / "stat415" / "lesson11" / SOURCE_REFERENCE
MANIFEST = ROOT / "authority" / "LESSON11_ASSET_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "LESSON11_ASSET_FREEZE_RECEIPT.json"
EXPECTED_BYTES = 142_195
EXPECTED_SHA256 = "2c9265d7c2dde44cd20968f73c051e18169d67e07fe7d66010fd78900e98dd22"
EXPECTED_WIDTH = 308
EXPECTED_HEIGHT = 321
EXPECTED_LAST_MODIFIED = "Thu, 27 Jun 2024 11:42:01 GMT"
EXPECTED_ETAG = '"22b73-61bdd9e7d5440"'


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def validate_png(data: bytes) -> dict[str, int]:
    if len(data) != EXPECTED_BYTES or sha256(data) != EXPECTED_SHA256:
        raise RuntimeError("Lesson 11 portrait bytes differ from the frozen identity")
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError("Lesson 11 portrait is not a canonical PNG")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    if (width, height, bit_depth, color_type) != (EXPECTED_WIDTH, EXPECTED_HEIGHT, 8, 6):
        raise RuntimeError("Lesson 11 portrait PNG geometry or RGBA format differs")
    return {"width": width, "height": height, "bit_depth": bit_depth, "color_type": color_type}


def manifest_bytes() -> bytes:
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes",
        "sha256", "media_type", "width", "height", "view_box", "license", "disposition",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerow(
        {
            "asset_id": "O006-PSU-012-A0001",
            "source_reference": SOURCE_REFERENCE,
            "official_url": URL,
            "local_path": TARGET.relative_to(ROOT).as_posix(),
            "bytes": EXPECTED_BYTES,
            "sha256": EXPECTED_SHA256,
            "media_type": "image/png",
            "width": EXPECTED_WIDTH,
            "height": EXPECTED_HEIGHT,
            "view_box": "",
            "license": "CC BY-NC 4.0",
            "disposition": "freeze-authority-and-redistribute-with-page-attribution-and-change-notice",
        }
    )
    return stream.getvalue().encode("utf-8")


def receipt_bytes(asset: bytes, manifest: bytes, geometry: dict[str, int]) -> bytes:
    return canonical_json(
        {
            "schema": "o006.stat415.lesson11-asset-freeze.v1",
            "status": "pass",
            "document_id": "O006-PSU-012",
            "component_id": "Lesson11",
            "asset_count": 1,
            "total_bytes": len(asset),
            "source_url": URL,
            "source_reference": SOURCE_REFERENCE,
            "last_modified": EXPECTED_LAST_MODIFIED,
            "etag": EXPECTED_ETAG,
            "asset": {
                "path": TARGET.relative_to(ROOT).as_posix(),
                "bytes": len(asset),
                "sha256": sha256(asset),
                **geometry,
            },
            "manifest": {
                "path": MANIFEST.relative_to(ROOT).as_posix(),
                "bytes": len(manifest),
                "sha256": sha256(manifest),
            },
            "rights": {
                "page_level_license": "CC BY-NC 4.0 except where otherwise noted",
                "asset_specific_exception_found": False,
                "disposition": "redistribute with page attribution, change notice, and component-separated rights",
            },
        }
    )


def download() -> bytes:
    request = urllib.request.Request(URL, headers={"User-Agent": "O006-STAT415-id asset freeze/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"Lesson 11 asset returned HTTP {response.status}")
        data = response.read()
        last_modified = response.headers.get("Last-Modified")
        etag = response.headers.get("ETag")
        if last_modified != EXPECTED_LAST_MODIFIED or etag != EXPECTED_ETAG:
            raise RuntimeError("Lesson 11 asset response validators differ")
        return data


def compute(fetch: bool) -> dict[Path, bytes]:
    asset = download() if fetch else TARGET.read_bytes()
    geometry = validate_png(asset)
    manifest = manifest_bytes()
    receipt = receipt_bytes(asset, manifest, geometry)
    return {TARGET: asset, MANIFEST: manifest, RECEIPT: receipt}


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute(fetch=args.write)
    if args.write:
        for path, payload in outputs.items():
            atomic_write(path, payload)
    else:
        for path, payload in outputs.items():
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"Lesson 11 asset output differs: {path.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "mode": "write" if args.write else "check-only",
                "status": "pass",
                "assets": 1,
                "bytes": EXPECTED_BYTES,
                "sha256": EXPECTED_SHA256,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
