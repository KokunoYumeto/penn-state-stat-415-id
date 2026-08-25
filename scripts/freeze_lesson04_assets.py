#!/usr/bin/env python3
"""Write or verify the deterministic Lesson 04 asset closure."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson04.html"
ASSET = ROOT / "authority" / "assets" / "stat415" / "lesson04" / "STAT-415-SEC-1-15.svg"
AUDIT = ROOT / "working" / "lesson04_asset_rights_audit.json"
MANIFEST = ROOT / "authority" / "LESSON04_ASSET_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "LESSON04_ASSET_FREEZE_RECEIPT.json"

SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson04"
ASSET_URL = "https://online.stat.psu.edu/stat415/assets/STAT-415-SEC-1-15.svg"
SOURCE_REF = "assets/STAT-415-SEC-1-15.svg"
SOURCE_BYTES = 106_614
SOURCE_SHA256 = "9fe5790e577c6ce0b808c92683aea45442187f80f74d540b20bd4514bdefc060"
ASSET_BYTES = 2_259
ASSET_SHA256 = "5c6f266e5a56ef3aa37bed6a8af263e64cd235691100b38d7cdf3475812d268c"
ASSET_ID = "O006-PSU-005-A0001"
LICENSE = "CC BY-NC 4.0"
RETRIEVED_UTC = "2026-08-25T00:37:34Z"
LAST_MODIFIED = "Wed, 19 Jun 2024 16:09:23 GMT"
ETAG = '"8d3-61b406befd2c0"'


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


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def validate_svg(data: bytes) -> dict[str, object]:
    if not data.startswith(b"<svg ") or b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise RuntimeError("Lesson 04 SVG prolog/entity policy differs")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise RuntimeError("Lesson 04 SVG is not well-formed XML") from exc
    if local_name(root.tag) != "svg" or root.attrib.get("viewBox") != "0 0 442.19 318.36":
        raise RuntimeError("Lesson 04 SVG root/viewBox differs")

    tags = [local_name(node.tag) for node in root.iter()]
    forbidden = {"script", "foreignObject", "image", "audio", "video"}
    if forbidden.intersection(tags):
        raise RuntimeError("Lesson 04 SVG contains an active or embedded resource")
    hrefs: list[str] = []
    for node in root.iter():
        for key, value in node.attrib.items():
            if local_name(key) == "href":
                hrefs.append(value)
    if hrefs:
        raise RuntimeError("Lesson 04 SVG contains an external/internal href dependency")

    text_values = [
        "".join(node.itertext()).strip()
        for node in root.iter()
        if local_name(node.tag) == "text"
    ]
    if text_values != ["f(x", "2", ")", "f(x", "1", ")", "x", "1", "x", "1", "y = ln (x)"]:
        raise RuntimeError("Lesson 04 SVG visible-text sequence differs")
    typo_surface = (
        b'<text class="cls-8" transform="translate(252.88 244.77) scale(0.58)">1</text>'
    )
    if data.count(typo_surface) != 1:
        raise RuntimeError("Lesson 04 SVG x2-label source-defect surface differs")
    return {
        "well_formed_xml": True,
        "root": "svg",
        "viewBox": "0 0 442.19 318.36",
        "intrinsic_width": 442.19,
        "intrinsic_height": 318.36,
        "element_count": len(tags),
        "script_or_foreign_object": False,
        "embedded_or_external_resources": False,
        "hrefs": [],
        "visible_text_sequence": text_values,
        "registered_source_defect": {
            "defect_id": "L04-D022",
            "description": "The second horizontal-coordinate label repeats x_1; its position and the paired f(x_2) label prove that it should be x_2.",
            "target_only_repair": "Change only the second coordinate subscript from 1 to 2 in the derivative reader asset.",
        },
    }


def compute() -> dict[str, bytes]:
    source = SOURCE.read_bytes()
    if len(source) != SOURCE_BYTES or sha256(source) != SOURCE_SHA256:
        raise RuntimeError("Lesson 04 authority differs")
    soup = BeautifulSoup(source, "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson 04 semantic main is missing")
    image_refs = [str(node.get("src")) for node in main.select("img[src]")]
    lightbox_refs = [str(node.get("href")) for node in main.select("a.lightbox[href]")]
    if image_refs != [SOURCE_REF] or lightbox_refs != [SOURCE_REF]:
        raise RuntimeError("Lesson 04 asset-reference topology differs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson 04 main contains an unexpected executable/embed dependency")
    source_text = source.decode("utf-8")
    if (
        "Except where otherwise noted, content on this site is licensed under a" not in source_text
        or "CC BY-NC 4.0" not in source_text
    ):
        raise RuntimeError("Lesson 04 page-wide licence witness is missing")

    asset = ASSET.read_bytes()
    if len(asset) != ASSET_BYTES or sha256(asset) != ASSET_SHA256:
        raise RuntimeError("frozen Lesson 04 SVG differs")
    validation = validate_svg(asset)

    audit = {
        "schema": "o006.stat415.lesson04-asset-rights-audit.v1",
        "status": "closed-for-offline-derivative-with-one-registered-target-only-label-repair",
        "component_id": "Lesson04",
        "document_id": "O006-PSU-005",
        "source": {
            "path": "authority/upstream/stat415/Lesson04.html",
            "url": SOURCE_URL,
            "bytes": len(source),
            "sha256": sha256(source),
        },
        "retrieval": {
            "url": ASSET_URL,
            "retrieved_utc": RETRIEVED_UTC,
            "http_status": 200,
            "content_type": "image/svg+xml",
            "content_length": ASSET_BYTES,
            "last_modified": LAST_MODIFIED,
            "etag": ETAG,
        },
        "asset": {
            "asset_id": ASSET_ID,
            "source_reference": SOURCE_REF,
            "official_url": ASSET_URL,
            "local_path": "authority/assets/stat415/lesson04/STAT-415-SEC-1-15.svg",
            "bytes": len(asset),
            "sha256": sha256(asset),
            "media_type": "image/svg+xml",
            "alt_text": "Natural logarithm graph",
            "validation": validation,
        },
        "rights": {
            "page_license": LICENSE,
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "per_asset_exception_found": False,
            "embedded_rights_or_creator_metadata": False,
            "disposition": "freeze and redistribute with the Lesson 04 page attribution/change notice; keep the authority asset byte-identical and disclose the derivative label repair",
            "blocking_unresolved": [],
        },
    }
    audit_payload = canonical_json(audit)

    manifest_buffer = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes",
        "sha256", "media_type", "view_box", "license", "disposition",
    )
    writer = csv.DictWriter(manifest_buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerow({
        "asset_id": ASSET_ID,
        "source_reference": SOURCE_REF,
        "official_url": ASSET_URL,
        "local_path": "authority/assets/stat415/lesson04/STAT-415-SEC-1-15.svg",
        "bytes": len(asset),
        "sha256": sha256(asset),
        "media_type": "image/svg+xml",
        "view_box": "0 0 442.19 318.36",
        "license": LICENSE,
        "disposition": "freeze-authority; target-only-x2-label-repair-registered",
    })
    manifest_payload = manifest_buffer.getvalue().encode("utf-8")

    receipt = {
        "schema": "o006.stat415.lesson04-asset-freeze.v1",
        "status": "frozen-and-verified",
        "component_id": "Lesson04",
        "document_id": "O006-PSU-005",
        "source": audit["source"],
        "reference_census": {
            "images": 1,
            "same_asset_lightbox_links": 1,
            "unique_assets": 1,
            "other_main_dependencies": 0,
        },
        "assets": 1,
        "asset_bytes": len(asset),
        "authority_asset": {
            "path": "authority/assets/stat415/lesson04/STAT-415-SEC-1-15.svg",
            "bytes": len(asset),
            "sha256": sha256(asset),
        },
        "manifest": {
            "path": "authority/LESSON04_ASSET_MANIFEST.csv",
            "bytes": len(manifest_payload),
            "sha256": sha256(manifest_payload),
        },
        "audit": {
            "path": "working/lesson04_asset_rights_audit.json",
            "bytes": len(audit_payload),
            "sha256": sha256(audit_payload),
        },
        "rights": {
            "license": LICENSE,
            "exception_found": False,
            "blocking_unresolved": 0,
        },
        "svg_validation": validation,
    }
    return {
        "working/lesson04_asset_rights_audit.json": audit_payload,
        "authority/LESSON04_ASSET_MANIFEST.csv": manifest_payload,
        "authority/LESSON04_ASSET_FREEZE_RECEIPT.json": canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute()
    if args.check_only:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"Lesson 04 asset output differs: {relative}")
    else:
        for relative, payload in outputs.items():
            atomic_write(ROOT / relative, payload)
    receipt = json.loads(outputs["authority/LESSON04_ASSET_FREEZE_RECEIPT.json"])
    print(json.dumps({
        "status": "verified" if args.check_only else "written",
        "assets": receipt["assets"],
        "asset_bytes": receipt["asset_bytes"],
        "asset_sha256": receipt["authority_asset"]["sha256"],
        "registered_asset_defect": receipt["svg_validation"]["registered_source_defect"]["defect_id"],
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
