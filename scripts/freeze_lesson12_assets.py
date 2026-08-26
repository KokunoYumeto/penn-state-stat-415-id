#!/usr/bin/env python3
"""Freeze and deterministically verify Lesson 12 images and video provenance."""

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
from urllib.parse import urljoin

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson12.html"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson12.html"
SOURCE_BYTES = 144_220
SOURCE_SHA256 = "89569622b8fea9bcfc17d51717002ab9840b44e6d80a34ee476d94acd45b515d"
DOCUMENT_ID = "O006-PSU-013"
COMPONENT_ID = "Lesson12"
ASSET_ROOT = ROOT / "authority" / "assets" / "stat415" / "lesson12"
MANIFEST = ROOT / "authority" / "LESSON12_ASSET_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "LESSON12_ASSET_FREEZE_RECEIPT.json"
VIDEO_PROVENANCE = ROOT / "authority" / "LESSON12_VIDEO_PROVENANCE.csv"

ASSETS = (
    {
        "source_reference": "Lesson12_files/figure-html/fig-lesson9_1-1.png",
        "bytes": 13_405,
        "sha256": "57bc330a84ba949ab460ce4d50492a3792a20b66cb8c26849cff86372c48a3cc",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"345d-659cca3a58c80"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-skin-cancer-1.png",
        "bytes": 17_916,
        "sha256": "4d239855552a56a136f002906cd7ed057096b3cb27127ce22d309aa4cdfc71a9",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"45fc-659cca3a58c80"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-htwt1-1.png",
        "bytes": 14_851,
        "sha256": "3bf6c1015f516ec2249e7ac8676cd4258b14db4c5097d2aebc8937eceb16c449",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"3a03-659cca3a58c80"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-gpavsentrance3-1.png",
        "bytes": 42_716,
        "sha256": "f2e1adb76725be49ed02f701d798afead28b8b977fafe15f0db55a98b58cd0fb",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 2,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"a6dc-659cca3a58c80"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-samplegpaentrance4-1.png",
        "bytes": 19_117,
        "sha256": "ac3f75e1cff2554fa5b6da07fc00a4d7a92d72cb6e503288c36f018cdda1582c",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"4aad-659cca3a58c80"',
    },
    {
        "source_reference": "assets/lesson9_11.png",
        "bytes": 72_948,
        "sha256": "91988678ff539a42d6e9e8d24a5710e444e7f40aeb2f132b0b2b6dbdf21b052d",
        "width": 944,
        "height": 582,
        "bit_depth": 8,
        "color_type": 6,
        "last_modified": "Fri, 25 Apr 2025 18:21:47 GMT",
        "etag": '"11cf4-6339e683de4c0"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-scattertemp-1.png",
        "bytes": 16_153,
        "sha256": "b20ba0424f94a88a120cbfec3c77a62ff5a1f5bd2339034e449d6272683468af",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"3f19-659cca3a58c80"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-scattertemp2-1.png",
        "bytes": 17_373,
        "sha256": "fe9f05fdb5d00e24dd20f727b67230385f3b3ecdee954d224488d8cae4ae89bd",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"43dd-659cca3a58c80"',
    },
    {
        "source_reference": "Lesson12_files/figure-html/fig-iqnormal-1.png",
        "bytes": 18_596,
        "sha256": "1e1ecda44208f545e38e8298f62c338fe5dbf2af265e7f60db1738903fca67ce",
        "width": 1344,
        "height": 960,
        "bit_depth": 8,
        "color_type": 3,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"48a4-659cca3a58c80"',
    },
)

VIDEOS = (
    {
        "source_url": "https://www.youtube.com/embed/oAaPR1qVedw",
        "section_id": "least-squares-estimates",
        "caption": "Video 12.1: Proof: Deriving the formulas for the intercept a and slope b",
    },
    {
        "source_url": "https://www.youtube.com/embed/pWMp1vhStDE",
        "section_id": "least-squares-estimates",
        "caption": "Video 12.2: Proof: Deriving formulas for the intercept and slope, Part 2",
    },
    {
        "source_url": "https://www.youtube.com/embed/mdzP-v6vl74",
        "section_id": "what-do-a-and-b-estimate",
        "caption": "Video 12.3: Example: Test scores and GPA, understanding the parameters",
    },
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def source_boundary() -> tuple[list[str], list[dict[str, str]]]:
    payload = SOURCE.read_bytes()
    if len(payload) != SOURCE_BYTES or sha256(payload) != SOURCE_SHA256:
        raise RuntimeError("Lesson 12 authority differs from its frozen identity")
    soup = BeautifulSoup(payload.decode("utf-8", errors="strict"), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson 12 authority lacks its semantic main")
    image_refs = list(dict.fromkeys(tag.get("src") for tag in main.select("img[src]")))
    expected_images = [str(row["source_reference"]) for row in ASSETS]
    if image_refs != expected_images:
        raise RuntimeError("Lesson 12 image-reference sequence differs")
    actual_videos: list[dict[str, str]] = []
    for tag in main.select("iframe[src]"):
        figure = tag.find_parent("figure")
        caption_tag = figure.find("figcaption") if figure else None
        section = tag.find_parent("section")
        actual_videos.append(
            {
                "source_url": str(tag.get("src")),
                "section_id": str(section.get("id")) if section else "",
                "caption": caption_tag.get_text(" ", strip=True).replace("\xa0", " ") if caption_tag else "",
            }
        )
        if tag.get("title") not in (None, ""):
            raise RuntimeError("Lesson 12 video title witness unexpectedly changed")
    if actual_videos != list(VIDEOS):
        raise RuntimeError(f"Lesson 12 video provenance differs: {actual_videos}")
    return image_refs, actual_videos


def validate_png(data: bytes, expected: dict[str, object]) -> dict[str, int]:
    if len(data) != expected["bytes"] or sha256(data) != expected["sha256"]:
        raise RuntimeError(f"Lesson 12 asset bytes differ: {expected['source_reference']}")
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise RuntimeError(f"Lesson 12 asset is not a PNG: {expected['source_reference']}")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", data[16:26])
    geometry = {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
    }
    expected_geometry = {key: int(expected[key]) for key in geometry}
    if geometry != expected_geometry:
        raise RuntimeError(f"Lesson 12 PNG geometry differs: {expected['source_reference']}")
    return geometry


def download(expected: dict[str, object]) -> bytes:
    url = urljoin(SOURCE_URL, str(expected["source_reference"]))
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "O006-STAT415-id Lesson12 asset freeze/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()
        if response.status != 200 or response.geturl() != url:
            raise RuntimeError(f"Lesson 12 asset did not resolve exactly: {url}")
        if response.headers.get_content_type() != "image/png":
            raise RuntimeError(f"Lesson 12 asset media type differs: {url}")
        if (
            response.headers.get("Last-Modified") != expected["last_modified"]
            or response.headers.get("ETag") != expected["etag"]
        ):
            raise RuntimeError(f"Lesson 12 asset response validators differ: {url}")
    return data


def manifest_bytes() -> bytes:
    fields = (
        "asset_id",
        "source_reference",
        "official_url",
        "local_path",
        "bytes",
        "sha256",
        "media_type",
        "width",
        "height",
        "bit_depth",
        "color_type",
        "last_modified",
        "etag",
        "license",
        "disposition",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for ordinal, row in enumerate(ASSETS, start=1):
        ref = str(row["source_reference"])
        writer.writerow(
            {
                "asset_id": f"{DOCUMENT_ID}-A{ordinal:04d}",
                "source_reference": ref,
                "official_url": urljoin(SOURCE_URL, ref),
                "local_path": (ASSET_ROOT / ref).relative_to(ROOT).as_posix(),
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "media_type": "image/png",
                "width": row["width"],
                "height": row["height"],
                "bit_depth": row["bit_depth"],
                "color_type": row["color_type"],
                "last_modified": row["last_modified"],
                "etag": row["etag"],
                "license": "CC BY-NC 4.0 except where otherwise noted (page-level witness)",
                "disposition": "freeze-authority; derivative redistribution retains attribution/change notice and per-asset caveat",
            }
        )
    return stream.getvalue().encode("utf-8")


def video_provenance_bytes() -> bytes:
    fields = (
        "video_id",
        "document_id",
        "component_id",
        "occurrence",
        "source_url",
        "provider",
        "section_id",
        "caption",
        "source_title_attribute",
        "local_binary",
        "redistributed",
        "disposition",
    )
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for ordinal, row in enumerate(VIDEOS, start=1):
        writer.writerow(
            {
                "video_id": f"{DOCUMENT_ID}-V{ordinal:04d}",
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "occurrence": ordinal,
                "source_url": row["source_url"],
                "provider": "YouTube",
                "section_id": row["section_id"],
                "caption": row["caption"],
                "source_title_attribute": "",
                "local_binary": "",
                "redistributed": "false",
                "disposition": "external-provenance-link-only; author offline textual/static equivalent",
            }
        )
    return stream.getvalue().encode("utf-8")


def receipt_bytes(
    binaries: list[bytes],
    geometries: list[dict[str, int]],
    manifest: bytes,
    video_provenance: bytes,
) -> bytes:
    assets = []
    for ordinal, (row, data, geometry) in enumerate(zip(ASSETS, binaries, geometries), start=1):
        ref = str(row["source_reference"])
        assets.append(
            {
                "asset_id": f"{DOCUMENT_ID}-A{ordinal:04d}",
                "source_reference": ref,
                "source_url": urljoin(SOURCE_URL, ref),
                "path": (ASSET_ROOT / ref).relative_to(ROOT).as_posix(),
                "bytes": len(data),
                "sha256": sha256(data),
                **geometry,
                "last_modified": row["last_modified"],
                "etag": row["etag"],
            }
        )
    return canonical_json(
        {
            "schema": "o006.stat415.lesson12-asset-freeze.v1",
            "status": "pass",
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "source": {
                "path": SOURCE.relative_to(ROOT).as_posix(),
                "url": SOURCE_URL,
                "bytes": SOURCE_BYTES,
                "sha256": SOURCE_SHA256,
            },
            "asset_count": len(assets),
            "asset_occurrences": 10,
            "total_bytes": sum(len(data) for data in binaries),
            "assets": assets,
            "manifest": {
                "path": MANIFEST.relative_to(ROOT).as_posix(),
                "bytes": len(manifest),
                "sha256": sha256(manifest),
            },
            "external_video_boundary": {
                "count": len(VIDEOS),
                "binary_bytes_downloaded": False,
                "binary_bytes_redistributed": False,
                "provenance_path": VIDEO_PROVENANCE.relative_to(ROOT).as_posix(),
                "provenance_bytes": len(video_provenance),
                "provenance_sha256": sha256(video_provenance),
                "source_urls": [row["source_url"] for row in VIDEOS],
                "disposition": "provenance links only; derivative requires offline textual/static equivalents",
            },
            "rights": {
                "page_level_license": "CC BY-NC 4.0 except where otherwise noted",
                "asset_specific_exception_found_in_page": False,
                "disposition": "preserve component rights, attribution, change notice, and exception caveat",
            },
        }
    )


def compute(fetch: bool) -> dict[Path, bytes]:
    source_boundary()
    binaries: list[bytes] = []
    geometries: list[dict[str, int]] = []
    for row in ASSETS:
        ref = str(row["source_reference"])
        target = ASSET_ROOT / ref
        data = download(row) if fetch else target.read_bytes()
        binaries.append(data)
        geometries.append(validate_png(data, row))
    manifest = manifest_bytes()
    video_provenance = video_provenance_bytes()
    receipt = receipt_bytes(binaries, geometries, manifest, video_provenance)
    outputs = {
        ASSET_ROOT / str(row["source_reference"]): data
        for row, data in zip(ASSETS, binaries)
    }
    outputs.update(
        {
            MANIFEST: manifest,
            VIDEO_PROVENANCE: video_provenance,
            RECEIPT: receipt,
        }
    )
    return outputs


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
        mode_name = "written"
    else:
        for path, expected in outputs.items():
            if not path.is_file():
                raise RuntimeError(f"Lesson 12 asset output missing: {path.relative_to(ROOT)}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson 12 asset output differs: {path.relative_to(ROOT)}; "
                    f"actual={sha256(actual)} expected={sha256(expected)}"
                )
        mode_name = "verified"
    print(
        json.dumps(
            {
                "mode": mode_name,
                "status": "pass",
                "assets": len(ASSETS),
                "asset_occurrences": 10,
                "bytes": sum(int(row["bytes"]) for row in ASSETS),
                "videos_provenance_only": len(VIDEOS),
                "receipt_sha256": sha256(outputs[RECEIPT]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
