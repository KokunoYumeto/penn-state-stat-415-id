#!/usr/bin/env python3
"""Write or verify the deterministic Lesson 02 asset closure."""

from __future__ import annotations

import argparse
import binascii
import csv
import hashlib
import io
import json
import struct
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson02.html"
ASSET_ROOT = ROOT / "authority" / "assets" / "stat415" / "lesson02"
AUDIT = ROOT / "working" / "lesson02_asset_rights_audit.json"
MANIFEST = ROOT / "authority" / "LESSON02_ASSET_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "LESSON02_ASSET_FREEZE_RECEIPT.json"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson02"
LICENSE = "CC BY-NC 4.0"
EXPECTED = (
    {
        "asset_id": "O006-PSU-003-A0001",
        "source_reference": "assets/dartboard.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/dartboard.png",
        "filename": "dartboard.png",
        "bytes": 32701,
        "sha256": "c8ddb1d7befe425ac72efd04abd75c0835aae62c786765256f3f8d93ee3ec0cd",
        "width": 1753,
        "height": 544,
        "bit_depth": 8,
        "color_type": 2,
        "interlace": 0,
    },
    {
        "asset_id": "O006-PSU-003-A0002",
        "source_reference": "Lesson02_files/figure-html/unnamed-chunk-1-1.png",
        "official_url": "https://online.stat.psu.edu/stat415/Lesson02_files/figure-html/unnamed-chunk-1-1.png",
        "filename": "unnamed-chunk-1-1.png",
        "bytes": 10942,
        "sha256": "564048b4327b3a379fe9921efa9224760f6c6afd01135f17d941af393a8f4532",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "interlace": 0,
    },
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EMBEDDED_METADATA_CHUNKS = {"tEXt", "zTXt", "iTXt", "eXIf", "iCCP"}
ANIMATION_CHUNKS = {"acTL", "fcTL", "fdAT"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def validate_png(data: bytes, filename: str) -> dict[str, object]:
    if not data.startswith(PNG_SIGNATURE):
        raise RuntimeError(f"invalid PNG signature: {filename}")
    position = len(PNG_SIGNATURE)
    chunks: list[str] = []
    metadata: list[str] = []
    animation: list[str] = []
    ihdr: tuple[int, int, int, int, int, int, int] | None = None
    saw_idat = False
    saw_iend = False
    while position < len(data):
        if position + 12 > len(data):
            raise RuntimeError(f"truncated PNG chunk header: {filename}")
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type_bytes = data[position + 4 : position + 8]
        try:
            chunk_type = chunk_type_bytes.decode("ascii")
        except UnicodeDecodeError as exc:
            raise RuntimeError(f"non-ASCII PNG chunk type: {filename}") from exc
        data_start = position + 8
        data_end = data_start + length
        crc_end = data_end + 4
        if crc_end > len(data):
            raise RuntimeError(f"truncated PNG chunk payload: {filename}: {chunk_type}")
        chunk_data = data[data_start:data_end]
        wanted_crc = struct.unpack(">I", data[data_end:crc_end])[0]
        actual_crc = binascii.crc32(chunk_type_bytes + chunk_data) & 0xFFFFFFFF
        if wanted_crc != actual_crc:
            raise RuntimeError(f"PNG CRC mismatch: {filename}: {chunk_type}")
        chunks.append(chunk_type)
        if chunk_type in EMBEDDED_METADATA_CHUNKS:
            metadata.append(chunk_type)
        if chunk_type in ANIMATION_CHUNKS:
            animation.append(chunk_type)
        if chunk_type == "IHDR":
            if ihdr is not None or len(chunk_data) != 13 or len(chunks) != 1:
                raise RuntimeError(f"invalid PNG IHDR placement or size: {filename}")
            ihdr = struct.unpack(">IIBBBBB", chunk_data)
        elif chunk_type == "IDAT":
            saw_idat = True
        elif chunk_type == "IEND":
            if length != 0:
                raise RuntimeError(f"invalid PNG IEND size: {filename}")
            saw_iend = True
            position = crc_end
            break
        position = crc_end
    if ihdr is None or not saw_idat or not saw_iend:
        raise RuntimeError(f"incomplete PNG structure: {filename}")
    if position != len(data):
        raise RuntimeError(f"PNG has trailing bytes: {filename}")
    width, height, bit_depth, color_type, compression, filtering, interlace = ihdr
    if compression != 0 or filtering != 0:
        raise RuntimeError(f"unsupported PNG compression/filter method: {filename}")
    if metadata or animation:
        raise RuntimeError(f"PNG contains unexpected metadata or animation: {filename}")
    return {
        "signature_valid": True,
        "chunk_crc_valid": True,
        "chunks": chunks,
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "compression": compression,
        "filter": filtering,
        "interlace": interlace,
        "animated": False,
        "embedded_text_or_profile": False,
        "trailing_bytes": 0,
    }


def compute() -> dict[str, bytes]:
    source = SOURCE.read_bytes()
    if len(source) != 93418 or sha256(source) != "29890184a4f2ba91fcd10425e0a941e7eab0f3ac9ab158b2ba469d0744ec69e5":
        raise RuntimeError("Lesson 02 authority differs")
    soup = BeautifulSoup(source, "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson 02 semantic main is missing")
    source_refs = [str(node.get("src")) for node in main.select("img[src]")]
    expected_refs = [str(item["source_reference"]) for item in EXPECTED]
    if source_refs != expected_refs:
        raise RuntimeError("Lesson 02 image reference sequence differs")
    lightbox_refs = [str(node.get("href")) for node in main.select("a.lightbox[href]")]
    if lightbox_refs != [expected_refs[0]]:
        raise RuntimeError("Lesson 02 lightbox reference sequence differs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("unexpected executable/embed dependency inside Lesson 02 main")
    source_text = source.decode("utf-8")
    licence_witness = "Except where otherwise noted, content on this site is licensed under a"
    if licence_witness not in source_text or "CC BY-NC 4.0" not in source_text:
        raise RuntimeError("Lesson 02 page-wide licence witness is missing")

    audit_bytes = AUDIT.read_bytes()
    audit = json.loads(audit_bytes.decode("utf-8"))
    if audit.get("blocking_unresolved_rights") != []:
        raise RuntimeError("Lesson 02 audit contains a blocking rights gap")
    audit_assets = audit.get("assets")
    if not isinstance(audit_assets, list) or len(audit_assets) != len(EXPECTED):
        raise RuntimeError("Lesson 02 asset audit inventory differs")

    rows: list[dict[str, object]] = []
    validations: list[dict[str, object]] = []
    for expected, audit_row in zip(EXPECTED, audit_assets):
        filename = str(expected["filename"])
        if audit_row.get("asset_id") != expected["asset_id"]:
            raise RuntimeError(f"audit stable ID differs: {filename}")
        if audit_row.get("official_url") != expected["official_url"]:
            raise RuntimeError(f"audit official URL differs: {filename}")
        data = (ASSET_ROOT / filename).read_bytes()
        if len(data) != expected["bytes"] or sha256(data) != expected["sha256"]:
            raise RuntimeError(f"frozen Lesson 02 asset differs: {filename}")
        validation = validate_png(data, filename)
        for key in ("width", "height", "bit_depth", "color_type", "interlace"):
            if validation[key] != expected[key]:
                raise RuntimeError(f"PNG {key} differs: {filename}")
            if audit_row.get("png_validation", {}).get(key) != validation[key]:
                raise RuntimeError(f"audit PNG {key} differs: {filename}")
        rows.append(
            {
                "asset_id": expected["asset_id"],
                "source_reference": expected["source_reference"],
                "official_url": expected["official_url"],
                "local_path": f"authority/assets/stat415/lesson02/{filename}",
                "bytes": len(data),
                "sha256": sha256(data),
                "media_type": "image/png",
                "width": validation["width"],
                "height": validation["height"],
                "license": LICENSE,
                "disposition": "freeze",
            }
        )
        validations.append({"asset_id": expected["asset_id"], **validation})

    output = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes",
        "sha256", "media_type", "width", "height", "license", "disposition",
    )
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest = output.getvalue().encode("utf-8")
    receipt = {
        "schema": "o006.stat415.lesson02-asset-freeze.v1",
        "status": "frozen-and-verified",
        "component_id": "Lesson02",
        "document_id": "O006-PSU-003",
        "source": {
            "path": "authority/upstream/stat415/Lesson02.html",
            "url": SOURCE_URL,
            "bytes": len(source),
            "sha256": sha256(source),
        },
        "reference_census": {
            "images": len(source_refs),
            "same_asset_lightbox_links": len(lightbox_refs),
            "unique_assets": len(rows),
            "other_main_dependencies": 0,
        },
        "assets": len(rows),
        "asset_bytes": sum(int(row["bytes"]) for row in rows),
        "manifest": {
            "path": "authority/LESSON02_ASSET_MANIFEST.csv",
            "bytes": len(manifest),
            "sha256": sha256(manifest),
        },
        "audit": {
            "path": "working/lesson02_asset_rights_audit.json",
            "bytes": len(audit_bytes),
            "sha256": sha256(audit_bytes),
        },
        "rights": {
            "license": LICENSE,
            "exception_found": False,
            "blocking_unresolved": 0,
            "attribution_rule": "preserve the Lesson 02 page and exact official asset URLs",
        },
        "png_validation": validations,
    }
    return {
        MANIFEST.relative_to(ROOT).as_posix(): manifest,
        RECEIPT.relative_to(ROOT).as_posix(): canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            atomic_write(ROOT / relative, payload)
        state = "written"
    else:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"Lesson 02 asset-freeze output differs: {relative}")
        state = "verified"
    receipt_payload = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(
        json.dumps(
            {
                "mode": state,
                "assets": len(EXPECTED),
                "bytes": sum(int(item["bytes"]) for item in EXPECTED),
                "receipt_sha256": sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
