#!/usr/bin/env python3
"""Audit the final deterministic and accessible STAT 415 EPUB."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import posixpath
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "output" / "epub" / "stat415-pengantar-statistika-matematis-id.epub"
REPLAY_A = ROOT / "tmp" / "epubqa" / "final-replay-A-2026-08-28.epub"
REPLAY_B = ROOT / "tmp" / "epubqa" / "final-replay-B-2026-08-28.epub"
BUILD_RECEIPT = ROOT / "build" / "CONSOLIDATED_EPUB_BUILD_RECEIPT.json"
EPUBCHECK_REPORT = ROOT / "tmp" / "epubqa" / "epubcheck-official-2026-08-28.xml"
ACE_REPORT = ROOT / "tmp" / "epubqa" / "ace-official-20260828" / "report.json"
OUTPUT_RECEIPT = ROOT / "build" / "CONSOLIDATED_EPUB_QA_RECEIPT.json"
EXPECTED_MATHML = 3159
EXPECTED_FALLBACKS = 17
EXPECTED_FOCUSABLE_MATH_REFLOW = 125
DISPLAY_MATH_TEX_MIN_CHARS = 180
INLINE_MATH_TEX_MIN_CHARS = 80
MTABLE_MAX_ROW_TOKEN_MIN_CHARS = 40
MTABLE_MAX_ROW_CELLS_MIN = 5
PRIOR_ACE_ARTIFACT_BYTES = 12299659
PRIOR_ACE_ARTIFACT_SHA256 = "acf81b8aa62ef77cd574d45d04490ebe173539ea3f8419c5c5e1ffcea5536729"
EXPECTED_ENTRIES = 111
EXPECTED_TOC_LINKS = 19
EXPECTED_LANDMARKS = 4
EXPECTED_SPINE_ITEMS = 4
EXPECTED_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_IDENTIFIER = "https://doi.org/10.5281/zenodo.22077422"
FORBIDDEN_ENGLISH_ALTS = {
    "Coordinate graph of f(x) = 1/2x",
    "Number line showing 6 values less than 1.",
    "Number line showing four values less than and two greater than one.",
    "Density plot for r = 1, 4, 6",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def parse_xml(data: bytes) -> etree._ElementTree:
    return etree.parse(io.BytesIO(data), etree.XMLParser(resolve_entities=False))


def local_target(source_name: str, reference: str) -> tuple[str, str] | None:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    target = posixpath.normpath(posixpath.join(posixpath.dirname(source_name), path)) if path else source_name
    return target, unquote(parsed.fragment)


def ace_failures(report: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if (
                value.get("@type") == "earl:assertion"
                and "earl:test" in value
                and value.get("earl:result", {}).get("earl:outcome") == "fail"
            ):
                found.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(report)
    return found


def audit() -> dict[str, Any]:
    required = [OFFICIAL, REPLAY_A, REPLAY_B, BUILD_RECEIPT, EPUBCHECK_REPORT, ACE_REPORT]
    missing = [rel(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing EPUB evidence: {missing}")

    identities = [
        {"bytes": path.stat().st_size, "path": rel(path), "sha256": sha256(path)}
        for path in (OFFICIAL, REPLAY_A, REPLAY_B)
    ]
    if len({(item["bytes"], item["sha256"]) for item in identities}) != 1:
        raise RuntimeError("Official EPUB and two independent replays differ")

    build_receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    if build_receipt.get("status") != "passed":
        raise RuntimeError("EPUB build receipt is not passing")
    if build_receipt.get("sha256") != identities[0]["sha256"]:
        raise RuntimeError("EPUB build receipt does not bind the official artifact")
    if build_receipt.get("xhtml_repairs", {}).get("heading_levels_repaired") != 33:
        raise RuntimeError("Expected 33 stable-ID heading-level repairs")
    if build_receipt.get("svg_math_fallbacks_with_indonesian_spoken_alternatives") != EXPECTED_FALLBACKS:
        raise RuntimeError("Indonesian spoken-math fallback inventory mismatch")
    if build_receipt.get("xhtml_repairs", {}).get("math_reflow_regions_focusable") != EXPECTED_FOCUSABLE_MATH_REFLOW:
        raise RuntimeError("Focusable native-MathML reflow inventory mismatch")

    with zipfile.ZipFile(OFFICIAL) as archive:
        infos = archive.infolist()
        duplicate_entries = sorted(
            {info.filename for info in infos if [item.filename for item in infos].count(info.filename) > 1}
        )
        if duplicate_entries:
            raise RuntimeError(f"Duplicate ZIP entries: {duplicate_entries}")
        if len(infos) != EXPECTED_ENTRIES:
            raise RuntimeError(f"Expected {EXPECTED_ENTRIES} ZIP entries, found {len(infos)}")
        if infos[0].filename != "mimetype" or infos[0].compress_type != zipfile.ZIP_STORED:
            raise RuntimeError("EPUB mimetype is not the first stored entry")
        if archive.read("mimetype") != b"application/epub+zip":
            raise RuntimeError("EPUB mimetype payload is invalid")
        if archive.testzip() is not None:
            raise RuntimeError("EPUB ZIP CRC validation failed")
        timestamp_failures = [info.filename for info in infos if info.date_time != (1980, 1, 1, 0, 0, 0)]
        if timestamp_failures:
            raise RuntimeError(f"Noncanonical ZIP timestamps: {timestamp_failures[:5]}")
        entries = {info.filename: archive.read(info.filename) for info in infos}

    container = parse_xml(entries["META-INF/container.xml"])
    opf_name = str(container.xpath('string(//*[local-name()="rootfile"]/@full-path)'))
    if opf_name not in entries:
        raise RuntimeError("Container does not resolve to the OPF")
    opf = parse_xml(entries[opf_name])
    manifest_nodes = opf.xpath('//*[local-name()="manifest"]/*[local-name()="item"]')
    manifest_by_id = {str(node.get("id")): node for node in manifest_nodes}
    if len(manifest_by_id) != len(manifest_nodes):
        raise RuntimeError("Duplicate or missing manifest IDs")
    missing_manifest_resources: list[str] = []
    for node in manifest_nodes:
        target = posixpath.normpath(posixpath.join(posixpath.dirname(opf_name), unquote(str(node.get("href")))))
        if target not in entries:
            missing_manifest_resources.append(target)
    if missing_manifest_resources:
        raise RuntimeError(f"Missing manifest resources: {missing_manifest_resources[:5]}")
    spine_refs = [str(node.get("idref")) for node in opf.xpath('//*[local-name()="spine"]/*[local-name()="itemref"]')]
    if len(spine_refs) != EXPECTED_SPINE_ITEMS or any(ref not in manifest_by_id for ref in spine_refs):
        raise RuntimeError("EPUB spine inventory is incomplete")

    languages = [str(value).strip() for value in opf.xpath('//*[local-name()="language"]/text()')]
    identifiers = [str(value).strip() for value in opf.xpath('//*[local-name()="identifier"]/text()')]
    titles = [str(value).strip() for value in opf.xpath('//*[local-name()="title"]/text()')]
    creators = [str(value).strip() for value in opf.xpath('//*[local-name()="creator"]/text()')]
    summaries = [str(value).strip() for value in opf.xpath('//*[local-name()="meta" and @property="schema:accessibilitySummary"]/text()')]
    if languages != ["id-ID"] or EXPECTED_IDENTIFIER not in identifiers:
        raise RuntimeError("EPUB language or DOI identifier mismatch")
    if not titles or not any(EXPECTED_PROVENANCE in creator for creator in creators):
        raise RuntimeError("EPUB title or translation provenance is missing")
    if len(summaries) != 1 or "diperbaiki hanya dalam rendisi EPUB" not in summaries[0]:
        raise RuntimeError("EPUB accessibility summary does not disclose rendition repairs")

    parsed: dict[str, etree._ElementTree] = {}
    for name, data in entries.items():
        if name.endswith((".xhtml", ".html", ".svg", ".ncx", ".opf")):
            parsed[name] = parse_xml(data)

    missing_links: list[dict[str, str]] = []
    duplicate_ids: dict[str, list[str]] = {}
    empty_alts: list[dict[str, str]] = []
    forbidden_alts: list[dict[str, str]] = []
    all_image_alts: list[str] = []
    mathml_nodes = 0
    fallback_nodes: list[etree._Element] = []
    xhtml_documents = 0
    for name, tree in parsed.items():
        if name.endswith((".xhtml", ".html")):
            xhtml_documents += 1
            ids = [str(value) for value in tree.xpath('//@id')]
            repeated = sorted({value for value in ids if ids.count(value) > 1})
            if repeated:
                duplicate_ids[name] = repeated
            mathml_nodes += len(tree.xpath('//*[local-name()="math"]'))
            fallback_nodes.extend(
                tree.xpath(
                    '//*[local-name()="img" and contains(concat(" ", normalize-space(@class), " "), " math-fallback-image ")]'
                )
            )
            for image in tree.xpath('//*[local-name()="img"]'):
                alt = str(image.get("alt", "")).strip()
                all_image_alts.append(alt)
                if not alt:
                    empty_alts.append({"document": name, "src": str(image.get("src", ""))})
                if alt in FORBIDDEN_ENGLISH_ALTS:
                    forbidden_alts.append({"document": name, "alt": alt})
        for node in tree.xpath('//*[@href or @src]'):
            reference = str(node.get("href") or node.get("src"))
            target = local_target(name, reference)
            if target is None:
                continue
            target_name, fragment = target
            if target_name not in entries:
                missing_links.append({"document": name, "reference": reference})
                continue
            if fragment and target_name in parsed:
                if not parsed[target_name].xpath('//*[@id=$value]', value=fragment):
                    missing_links.append({"document": name, "reference": reference})
    if duplicate_ids or empty_alts or forbidden_alts or missing_links:
        raise RuntimeError("EPUB duplicate-ID, alternative-text, or link closure failure")
    if mathml_nodes != EXPECTED_MATHML or len(fallback_nodes) != EXPECTED_FALLBACKS:
        raise RuntimeError("EPUB mathematics surface inventory mismatch")
    fallback_alts = [str(node.get("alt", "")).strip() for node in fallback_nodes]
    if any(not alt or alt.startswith("Rumus matematika TeX:") for alt in fallback_alts):
        raise RuntimeError("Raw TeX remained as a fallback image alternative")

    chapter = parsed["EPUB/text/ch001.xhtml"]
    stylesheet = entries["EPUB/styles/stylesheet1.css"].decode("utf-8")
    required_math_reflow_css = (
        ".math.display {",
        ".math.inline {",
        "max-width: 100%;",
        "overflow-x: auto;",
        "overflow-y: hidden;",
        '.math[tabindex="0"]:focus {',
    )
    if any(fragment not in stylesheet for fragment in required_math_reflow_css):
        raise RuntimeError("EPUB stylesheet lacks the deterministic MathML reflow contract")

    math_wrappers = chapter.xpath(
        '//*[@data-o006-math-id and '
        'contains(concat(" ", normalize-space(@class), " "), " math ") and '
        './/*[local-name()="math"]]'
    )
    expected_focusable_math: list[etree._Element] = []
    expected_display_math = 0
    expected_inline_math = 0
    for wrapper in math_wrappers:
        classes = set(str(wrapper.get("class", "")).split())
        annotations = wrapper.xpath(
            './/*[local-name()="annotation" and '
            '@encoding="application/x-tex"]/text()'
        )
        tex = " ".join(" ".join(str(value).split()) for value in annotations)
        max_row_cells = 0
        max_row_token_chars = 0
        for row in wrapper.xpath(
            './/*[local-name()="mtable"]/*[local-name()="mtr" or '
            'local-name()="mlabeledtr"]'
        ):
            max_row_cells = max(
                max_row_cells, len(row.xpath('./*[local-name()="mtd"]'))
            )
            token_text = "".join(
                str(value)
                for value in row.xpath(
                    './/*[local-name()="mi" or local-name()="mn" or '
                    'local-name()="mo" or local-name()="mtext"]/text()'
                )
            )
            max_row_token_chars = max(
                max_row_token_chars, len("".join(token_text.split()))
            )
        selected = (
            ("display" in classes and len(tex) >= DISPLAY_MATH_TEX_MIN_CHARS)
            or max_row_token_chars >= MTABLE_MAX_ROW_TOKEN_MIN_CHARS
            or max_row_cells >= MTABLE_MAX_ROW_CELLS_MIN
            or ("inline" in classes and len(tex) >= INLINE_MATH_TEX_MIN_CHARS)
        )
        if selected:
            expected_focusable_math.append(wrapper)
            if "display" in classes:
                expected_display_math += 1
            else:
                expected_inline_math += 1
    if len(expected_focusable_math) != EXPECTED_FOCUSABLE_MATH_REFLOW:
        raise RuntimeError("Static native-MathML reflow candidate inventory changed")
    invalid_focusable_math = [
        str(wrapper.get("data-o006-math-id"))
        for wrapper in expected_focusable_math
        if wrapper.get("data-o006-reflow-risk") != "static-width-v1"
        or wrapper.get("tabindex") != "0"
        or wrapper.get("role") != "group"
        or wrapper.get("aria-label")
        != "Rumus matematika yang dapat digulir secara horizontal"
    ]
    if invalid_focusable_math:
        raise RuntimeError(
            "Native-MathML reflow candidates lack keyboard/accessibility semantics: "
            f"{invalid_focusable_math[:5]}"
        )
    headings = chapter.xpath('//*[local-name()="h1" or local-name()="h2" or local-name()="h3" or local-name()="h4" or local-name()="h5" or local-name()="h6"]')
    levels = [int(etree.QName(node).localname[1:]) for node in headings]
    heading_forward_skips = [index + 2 for index, (left, right) in enumerate(zip(levels, levels[1:])) if right > left + 1]
    if heading_forward_skips:
        raise RuntimeError(f"Heading-order jumps remain at heading ordinals {heading_forward_skips}")

    nav = parsed["EPUB/nav.xhtml"]
    toc_links = nav.xpath('//*[local-name()="nav" and @*[local-name()="type"]="toc"]//*[local-name()="a"]')
    landmarks = nav.xpath('//*[local-name()="nav" and @*[local-name()="type"]="landmarks"]//*[local-name()="a"]')
    ncx_points = parsed["EPUB/toc.ncx"].xpath('//*[local-name()="navPoint"]')
    if len(toc_links) != EXPECTED_TOC_LINKS or len(landmarks) != EXPECTED_LANDMARKS or len(ncx_points) != EXPECTED_TOC_LINKS:
        raise RuntimeError("EPUB navigation inventory mismatch")

    epubcheck = parse_xml(EPUBCHECK_REPORT.read_bytes())
    epubcheck_status = str(epubcheck.xpath('string(//*[local-name()="status"])'))
    epubcheck_messages = epubcheck.xpath('//*[local-name()="message"]')
    epubcheck_release = str(epubcheck.getroot().get("release", ""))
    if epubcheck_status != "Well-formed" or epubcheck_messages or epubcheck_release != "5.3.0":
        raise RuntimeError("EPUBCheck 5.3.0 did not pass without messages")

    ace = json.loads(ACE_REPORT.read_text(encoding="utf-8"))
    ace_revision = str(ace.get("earl:assertedBy", {}).get("doap:release", {}).get("doap:revision", ""))
    failures = ace_failures(ace)
    if ace.get("earl:result", {}).get("earl:outcome") != "pass" or failures or ace_revision != "1.4.6":
        raise RuntimeError("DAISY Ace 1.4.6 did not pass")

    joined = b"\n".join(entries.values()).lower()
    sensitive_markers = [b"c:\\users\\", b"github token", b"zenodo token", b"figshare token"]
    found_sensitive = [marker.decode("ascii") for marker in sensitive_markers if marker in joined]
    if found_sensitive:
        raise RuntimeError(f"Sensitive/local markers found in EPUB: {found_sensitive}")

    return {
        "artifact": identities[0],
        "prior_candidate_automated_accessibility": {
            "artifact": {
                "bytes": PRIOR_ACE_ARTIFACT_BYTES,
                "sha256": PRIOR_ACE_ARTIFACT_SHA256,
            },
            "ace_missing_certification_metadata": ace.get("a11y-metadata", {}).get("missing", []),
            "ace_revision": ace_revision,
            "ace_status": "passed",
            "failed_assertions": 0,
            "report_sha256": sha256(ACE_REPORT),
            "scope_note": "Ace evidence applies only to the named prior artifact, not the final EPUB hash.",
        },
        "build_receipt": {
            "bytes": BUILD_RECEIPT.stat().st_size,
            "path": rel(BUILD_RECEIPT),
            "sha256": sha256(BUILD_RECEIPT),
        },
        "deterministic_replays": identities[1:],
        "epubcheck": {
            "messages": 0,
            "release": epubcheck_release,
            "report_sha256": sha256(EPUBCHECK_REPORT),
            "status": epubcheck_status,
        },
        "metadata": {
            "accessibility_summary": summaries[0],
            "creators": creators,
            "identifier": EXPECTED_IDENTIFIER,
            "language": languages[0],
            "title": titles[0],
        },
        "package": {
            "entries": len(entries),
            "fixed_zip_timestamps": len(entries),
            "manifest_items": len(manifest_nodes),
            "mimetype_first_and_stored": True,
            "spine_items": len(spine_refs),
            "zip_crc": "passed",
        },
        "privacy": {"sensitive_or_local_markers": found_sensitive},
        "final_hash_validation_scope": {
            "browser_or_ace_run": False,
            "epubcheck_and_static_package_audit": True,
            "restriction": "No Chrome, Chromium, Playwright, Puppeteer, Ace, Electron, or WebView process was launched for the final hash.",
        },
        "schema": "o006.stat415.consolidated-epub-qa.v1",
        "status": "passed",
        "structure": {
            "epub_toc_links": len(toc_links),
            "heading_forward_skips_after_rendition_repair": len(heading_forward_skips),
            "headings": len(headings),
            "image_occurrences": len(all_image_alts),
            "images_with_nonempty_alternatives": len(all_image_alts),
            "landmark_links": len(landmarks),
            "math_reflow_focusable_display_regions": expected_display_math,
            "math_reflow_focusable_inline_regions": expected_inline_math,
            "math_reflow_focusable_regions": len(expected_focusable_math),
            "mathml_nodes": mathml_nodes,
            "ncx_navpoints": len(ncx_points),
            "svg_math_fallbacks": len(fallback_nodes),
            "xhtml_documents": xhtml_documents,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    receipt = audit()
    serialized = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if args.check_only:
        if not OUTPUT_RECEIPT.is_file() or OUTPUT_RECEIPT.read_bytes() != serialized:
            raise RuntimeError("Stored EPUB QA receipt differs from deterministic replay")
    else:
        OUTPUT_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_RECEIPT.write_bytes(serialized)
    print(
        json.dumps(
            {
                "bytes": receipt["artifact"]["bytes"],
                "epubcheck_messages": receipt["epubcheck"]["messages"],
                "mathml": receipt["structure"]["mathml_nodes"],
                "replay_match": True,
                "sha256": receipt["artifact"]["sha256"],
                "status": receipt["status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
