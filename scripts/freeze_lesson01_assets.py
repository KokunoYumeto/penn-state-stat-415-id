#!/usr/bin/env python3
"""Write or verify the deterministic Lesson 01 asset closure."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson01.html"
ASSET_ROOT = ROOT / "authority" / "assets" / "stat415" / "lesson01"
AUDIT = ROOT / "working" / "lesson01_asset_rights_audit.json"
MANIFEST = ROOT / "authority" / "LESSON01_ASSET_MANIFEST.csv"
RECEIPT = ROOT / "authority" / "LESSON01_ASSET_FREEZE_RECEIPT.json"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson01"
LICENSE = "CC BY-NC 4.0"
EXPECTED = (
    ("O006-PSU-002-A0001", "STAT-415-SEC-3-18-09.svg", 1821, "375775fae6e23602ebb80a69f1b6bfe187415a932e9bbc608cf1864ad364440c"),
    ("O006-PSU-002-A0002", "stat-415-sec-3-18-10.svg", 2693, "d6880dd245560b31efe664744a9c953adb77d349002b16fd785f1b7ec39255fa"),
    ("O006-PSU-002-A0003", "stat-415-sec-3-18-11.svg", 2688, "7c94f0c22d3be28edc7b4fb969d14152543be180df0fa5bf029020912082caab"),
    ("O006-PSU-002-A0004", "stat-415-sec-3-18-12.svg", 2690, "0e7a00a04750e9da3d55f39b202fc10ca8cfebed000a6aa7cd55f2744bc8a5d8"),
    ("O006-PSU-002-A0005", "STAT-415-SEC-3-18-13.svg", 52253, "b3fc3f936d4aee619981611d7c0d8797ef7cc8135fe5e40b4e8d4ad9f0849e3f"),
)


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


def local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1].casefold()


def validate_svg(data: bytes, filename: str) -> dict[str, object]:
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise RuntimeError(f"invalid SVG XML: {filename}: {exc}") from exc
    if local_name(root.tag) != "svg":
        raise RuntimeError(f"asset root is not SVG: {filename}")
    scripts = [node for node in root.iter() if local_name(node.tag) == "script"]
    external: list[str] = []
    embedded_raster: list[str] = []
    for node in root.iter():
        for key, value in node.attrib.items():
            if local_name(key) not in {"href", "src"}:
                continue
            lowered = value.strip().casefold()
            if lowered.startswith(("http://", "https://", "//")):
                external.append(value)
            if lowered.startswith("data:image/"):
                embedded_raster.append(value[:32])
    if scripts or external or embedded_raster:
        raise RuntimeError(f"unsafe or non-closed SVG dependency: {filename}")
    return {
        "xml_valid": True,
        "root_element": "svg",
        "viewBox": root.attrib.get("viewBox"),
        "script_elements": 0,
        "external_references": 0,
        "embedded_raster_references": 0,
        "title_elements": sum(1 for node in root.iter() if local_name(node.tag) == "title"),
        "desc_elements": sum(1 for node in root.iter() if local_name(node.tag) == "desc"),
    }


def compute() -> dict[str, bytes]:
    source = SOURCE.read_bytes()
    if len(source) != 84567 or sha256(source) != "6b3bf5ba7b5cc7960fb4eddec931088f51f588a879444630a83238767fbfce85":
        raise RuntimeError("Lesson 01 authority differs")
    soup = BeautifulSoup(source, "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson 01 semantic main is missing")
    source_refs = [str(node.get("src")) for node in main.select("img[src]")]
    lightbox_refs = [str(node.get("href")) for node in main.select("a.lightbox[href]")]
    expected_refs = [f"assets/{filename}" for _, filename, _, _ in EXPECTED]
    if source_refs != expected_refs or lightbox_refs != expected_refs:
        raise RuntimeError("Lesson 01 image/lightbox reference sequence differs")
    if main.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("unexpected executable/embed dependency inside Lesson 01 main")
    source_text = source.decode("utf-8")
    licence_witness = "Except where otherwise noted, content on this site is licensed under a"
    if licence_witness not in source_text or "CC BY-NC 4.0" not in source_text:
        raise RuntimeError("Lesson 01 page-wide licence witness is missing")

    audit_bytes = AUDIT.read_bytes()
    audit = json.loads(audit_bytes.decode("utf-8"))
    if audit.get("blocking_unresolved_rights") != []:
        raise RuntimeError("Lesson 01 audit contains a blocking rights gap")
    audit_assets = audit.get("assets")
    if not isinstance(audit_assets, list) or len(audit_assets) != len(EXPECTED):
        raise RuntimeError("Lesson 01 asset audit inventory differs")

    rows: list[dict[str, object]] = []
    validations: list[dict[str, object]] = []
    for expected, audit_row in zip(EXPECTED, audit_assets):
        asset_id, filename, wanted_bytes, wanted_sha = expected
        if audit_row.get("asset_id") != asset_id:
            raise RuntimeError(f"audit stable ID differs: {filename}")
        data = (ASSET_ROOT / filename).read_bytes()
        if len(data) != wanted_bytes or sha256(data) != wanted_sha:
            raise RuntimeError(f"frozen Lesson 01 asset differs: {filename}")
        validation = validate_svg(data, filename)
        official = f"https://online.stat.psu.edu/stat415/assets/{filename}"
        if audit_row.get("official_url") != official:
            raise RuntimeError(f"audit official URL differs: {filename}")
        rows.append(
            {
                "asset_id": asset_id,
                "source_reference": f"assets/{filename}",
                "official_url": official,
                "local_path": f"authority/assets/stat415/lesson01/{filename}",
                "bytes": len(data),
                "sha256": sha256(data),
                "media_type": "image/svg+xml",
                "license": LICENSE,
                "disposition": "freeze",
            }
        )
        validations.append({"asset_id": asset_id, **validation})

    output = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes",
        "sha256", "media_type", "license", "disposition",
    )
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest = output.getvalue().encode("utf-8")
    receipt = {
        "schema": "o006.stat415.lesson01-asset-freeze.v1",
        "status": "frozen-and-verified",
        "component_id": "Lesson01",
        "document_id": "O006-PSU-002",
        "source": {
            "path": "authority/upstream/stat415/Lesson01.html",
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
            "path": "authority/LESSON01_ASSET_MANIFEST.csv",
            "bytes": len(manifest),
            "sha256": sha256(manifest),
        },
        "audit": {
            "path": "working/lesson01_asset_rights_audit.json",
            "bytes": len(audit_bytes),
            "sha256": sha256(audit_bytes),
        },
        "rights": {
            "license": LICENSE,
            "exception_found": False,
            "blocking_unresolved": 0,
            "attribution_rule": "preserve the Lesson 01 page and exact official asset URLs",
        },
        "svg_validation": validations,
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
                raise RuntimeError(f"Lesson 01 asset-freeze output differs: {relative}")
        state = "verified"
    receipt_payload = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(json.dumps({"mode": state, "assets": 5, "bytes": 62145, "receipt_sha256": sha256(receipt_payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
