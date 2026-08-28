#!/usr/bin/env python3
"""Browser-free deterministic reflow and package-delta audit for the final EPUB."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "output" / "epub" / "stat415-pengantar-statistika-matematis-id.epub"
REPLAY_A = ROOT / "tmp" / "epubqa" / "final-replay-A-2026-08-28.epub"
REPLAY_B = ROOT / "tmp" / "epubqa" / "final-replay-B-2026-08-28.epub"
BUILD_RECEIPT = ROOT / "build" / "CONSOLIDATED_EPUB_BUILD_RECEIPT.json"
QA_RECEIPT = ROOT / "build" / "CONSOLIDATED_EPUB_QA_RECEIPT.json"
EPUBCHECK_REPORT = ROOT / "tmp" / "epubqa" / "epubcheck-official-2026-08-28.xml"
PRIOR_ACE_REPORT = ROOT / "tmp" / "epubqa" / "ace-official-20260828" / "report.json"
OUTPUT = ROOT / "build" / "CONSOLIDATED_EPUB_STATIC_REFLOW_QA_RECEIPT.json"

EXPECTED_ENTRIES = 111
EXPECTED_MATH_WRAPPERS = 3139
EXPECTED_MATHML = 3159
EXPECTED_REFLOW_CANDIDATES = 125
DISPLAY_TEX_MIN = 180
INLINE_TEX_MIN = 80
MTABLE_ROW_TOKEN_MIN = 40
MTABLE_ROW_CELLS_MIN = 5
PRIOR_ACE_ARTIFACT = {
    "bytes": 12299659,
    "sha256": "acf81b8aa62ef77cd574d45d04490ebe173539ea3f8419c5c5e1ffcea5536729",
}
PRIOR_QA_RECEIPT_SHA256 = "5ffa18a600633848edbda52873c69b235524382d9b690fc89b849fc83bdd824f"
PRIOR_ACE_PACKAGE_INVARIANTS = {
    "entries": 111,
    "headings": 271,
    "image_occurrences": 102,
    "manifest_items": 107,
    "mathml_nodes": 3159,
    "spine_items": 4,
    "svg_math_fallbacks": 17,
    "xhtml_documents": 4,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def identity(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "path": rel(path), "sha256": sha256(path)}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


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


def math_record(wrapper: etree._Element, document: str) -> dict[str, Any]:
    classes = set(str(wrapper.get("class", "")).split())
    annotations = wrapper.xpath(
        './/*[local-name()="annotation" and @encoding="application/x-tex"]/text()'
    )
    tex = " ".join(" ".join(str(value).split()) for value in annotations)
    max_cells = 0
    max_token_chars = 0
    for row in wrapper.xpath(
        './/*[local-name()="mtable"]/*[local-name()="mtr" or local-name()="mlabeledtr"]'
    ):
        max_cells = max(max_cells, len(row.xpath('./*[local-name()="mtd"]')))
        token_text = "".join(
            str(value)
            for value in row.xpath(
                './/*[local-name()="mi" or local-name()="mn" or '
                'local-name()="mo" or local-name()="mtext"]/text()'
            )
        )
        max_token_chars = max(max_token_chars, len("".join(token_text.split())))
    reasons: list[str] = []
    if max_token_chars >= MTABLE_ROW_TOKEN_MIN or max_cells >= MTABLE_ROW_CELLS_MIN:
        reasons.append("wide-structural-mtable")
    if "display" in classes and len(tex) >= DISPLAY_TEX_MIN:
        reasons.append("long-display")
    if "inline" in classes and len(tex) >= INLINE_TEX_MIN:
        reasons.append("long-inline")
    return {
        "epub_document": document,
        "kind": "display" if "display" in classes else "inline",
        "math_id": str(wrapper.get("data-o006-math-id")),
        "max_mtable_row_cells": max_cells,
        "max_mtable_row_token_chars": max_token_chars,
        "reasons": reasons,
        "tex_chars": len(tex),
    }


def audit() -> dict[str, Any]:
    required = [
        OFFICIAL,
        REPLAY_A,
        REPLAY_B,
        BUILD_RECEIPT,
        QA_RECEIPT,
        EPUBCHECK_REPORT,
        PRIOR_ACE_REPORT,
    ]
    missing = [rel(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing static EPUB evidence: {missing}")

    artifact = identity(OFFICIAL)
    replays = [identity(REPLAY_A), identity(REPLAY_B)]
    if any((item["bytes"], item["sha256"]) != (artifact["bytes"], artifact["sha256"]) for item in replays):
        raise RuntimeError("Official EPUB and deterministic replays differ")

    build = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    qa = json.loads(QA_RECEIPT.read_text(encoding="utf-8"))
    if build.get("status") != "passed" or build.get("sha256") != artifact["sha256"]:
        raise RuntimeError("Build receipt does not bind the final EPUB")
    if qa.get("status") != "passed" or qa.get("artifact", {}).get("sha256") != artifact["sha256"]:
        raise RuntimeError("Final QA receipt does not bind the final EPUB")
    final_invariants = {
        "entries": qa.get("package", {}).get("entries"),
        "headings": qa.get("structure", {}).get("headings"),
        "image_occurrences": qa.get("structure", {}).get("image_occurrences"),
        "manifest_items": qa.get("package", {}).get("manifest_items"),
        "mathml_nodes": qa.get("structure", {}).get("mathml_nodes"),
        "spine_items": qa.get("package", {}).get("spine_items"),
        "svg_math_fallbacks": qa.get("structure", {}).get("svg_math_fallbacks"),
        "xhtml_documents": qa.get("structure", {}).get("xhtml_documents"),
    }
    if final_invariants != PRIOR_ACE_PACKAGE_INVARIANTS:
        raise RuntimeError("Final package no longer preserves prior Ace-candidate invariants")

    with zipfile.ZipFile(OFFICIAL) as archive:
        infos = archive.infolist()
        if len(infos) != EXPECTED_ENTRIES or infos[0].filename != "mimetype":
            raise RuntimeError("EPUB ZIP entry count/order changed")
        if infos[0].compress_type != zipfile.ZIP_STORED or archive.testzip() is not None:
            raise RuntimeError("EPUB ZIP storage/CRC validation failed")
        if any(info.date_time != (1980, 1, 1, 0, 0, 0) for info in infos):
            raise RuntimeError("EPUB ZIP timestamps are not deterministic")
        entries = {info.filename: archive.read(info.filename) for info in infos}

    css = entries["EPUB/styles/stylesheet1.css"].decode("utf-8")
    required_css = [
        ".math.display {",
        ".math.inline {",
        "max-width: 100%;",
        "overflow-x: auto;",
        "overflow-y: hidden;",
        '.math[tabindex="0"]:focus {',
        "pre code > span {",
        "word-break: break-word;",
    ]
    if any(fragment not in css for fragment in required_css):
        raise RuntimeError("CSS containment/focus contract is incomplete")

    all_records: list[dict[str, Any]] = []
    mathml = 0
    for name, data in sorted(entries.items()):
        if not name.endswith(".xhtml"):
            continue
        tree = etree.parse(io.BytesIO(data), etree.XMLParser(resolve_entities=False))
        mathml += len(tree.xpath('//*[local-name()="math"]'))
        for wrapper in tree.xpath(
            '//*[@data-o006-math-id and '
            'contains(concat(" ", normalize-space(@class), " "), " math ") and '
            './/*[local-name()="math"]]'
        ):
            record = math_record(wrapper, name)
            selected = bool(record["reasons"])
            marked = wrapper.get("data-o006-reflow-risk") == "static-width-v1"
            focusable = (
                wrapper.get("tabindex") == "0"
                and wrapper.get("role") == "group"
                and wrapper.get("aria-label")
                == "Rumus matematika yang dapat digulir secara horizontal"
            )
            if selected != marked or selected != focusable:
                raise RuntimeError(f"Math reflow selection/semantics mismatch: {record['math_id']}")
            all_records.append(record)

    candidates = [record for record in all_records if record["reasons"]]
    candidates.sort(key=lambda item: (item["epub_document"], item["math_id"]))
    if len(all_records) != EXPECTED_MATH_WRAPPERS or mathml != EXPECTED_MATHML:
        raise RuntimeError("Static mathematics census changed")
    if len(candidates) != EXPECTED_REFLOW_CANDIDATES:
        raise RuntimeError("Static reflow candidate census changed")
    build_inventory = build.get("math_reflow", {}).get("candidate_inventory", [])
    if build_inventory != candidates:
        raise RuntimeError("Build receipt math inventory differs from independent static audit")

    code_focus = entries["EPUB/text/ch001.xhtml"].count(
        b'id="cb245" data-o006-code-id="O006-PSU-ADV-0237-CODE01" '
        b'aria-label="Kode R yang dapat digulir" role="region" tabindex="0"'
    )
    if code_focus != 1:
        raise RuntimeError("Long code reflow region is not uniquely keyboard focusable")

    epubcheck = etree.parse(str(EPUBCHECK_REPORT))
    messages = epubcheck.xpath('//*[local-name()="message"]')
    status = str(epubcheck.xpath('string(//*[local-name()="status"])'))
    release = str(epubcheck.getroot().get("release", ""))
    if messages or status != "Well-formed" or release != "5.3.0":
        raise RuntimeError("Final EPUBCheck 5.3.0 report is not clean")

    ace = json.loads(PRIOR_ACE_REPORT.read_text(encoding="utf-8"))
    ace_revision = str(ace.get("earl:assertedBy", {}).get("doap:release", {}).get("doap:revision", ""))
    if ace_revision != "1.4.6" or ace.get("earl:result", {}).get("earl:outcome") != "pass" or ace_failures(ace):
        raise RuntimeError("Prior-candidate Ace evidence is not passing")

    threshold_census = {
        "display_tex_chars": {
            str(value): sum(record["kind"] == "display" and record["tex_chars"] >= value for record in all_records)
            for value in (80, 100, 120, 160, 180)
        },
        "inline_tex_chars": {
            str(value): sum(record["kind"] == "inline" and record["tex_chars"] >= value for record in all_records)
            for value in (60, 80, 100)
        },
        "mtable_max_row_token_chars": {
            str(value): sum(record["max_mtable_row_token_chars"] >= value for record in all_records)
            for value in (32, 40)
        },
    }
    entry_manifest = [
        {"bytes": len(data), "path": name, "sha256": sha256_bytes(data)}
        for name, data in sorted(entries.items())
    ]

    return {
        "artifact": artifact,
        "build_receipt": identity(BUILD_RECEIPT),
        "checks": {
            "candidate_inventory_sha256": sha256_bytes(canonical(candidates)),
            "css_containment_and_focus_contract": "passed",
            "delta_from_prior_ace_tested_candidate": {
                "artifact_byte_delta": artifact["bytes"] - PRIOR_ACE_ARTIFACT["bytes"],
                "final_reflow_surfaces": {
                    "css_sha256": sha256_bytes(entries["EPUB/styles/stylesheet1.css"]),
                    "focusable_code_regions": code_focus,
                    "focusable_math_candidate_count": len(candidates),
                    "focusable_math_candidate_inventory_sha256": sha256_bytes(canonical(candidates)),
                },
                "package_topology_and_content_surface_invariants": final_invariants,
                "proof_scope": "Exact base/final identities plus preserved package invariants and a complete final reflow inventory; this is not an Ace or browser validation of the final hash.",
            },
            "epubcheck_messages": len(messages),
            "epubcheck_release": release,
            "epubcheck_status": status,
            "fixed_zip_timestamps": len(entries),
            "math_reflow_candidate_count": len(candidates),
            "math_reflow_rule": {
                "display_min_tex_chars": DISPLAY_TEX_MIN,
                "inline_min_tex_chars": INLINE_TEX_MIN,
                "mtable_max_row_cells_min": MTABLE_ROW_CELLS_MIN,
                "mtable_max_row_token_chars_min": MTABLE_ROW_TOKEN_MIN,
                "version": "static-width-v1",
            },
            "math_wrapper_count": len(all_records),
            "mathml_count": mathml,
            "package_entry_manifest_sha256": sha256_bytes(canonical(entry_manifest)),
            "threshold_census": threshold_census,
            "zip_crc": "passed",
        },
        "prior_ace_tested_candidate": {
            "artifact": PRIOR_ACE_ARTIFACT,
            "ace_report": identity(PRIOR_ACE_REPORT),
            "ace_revision": ace_revision,
            "ace_status": "passed",
            "failed_assertions": 0,
            "prior_qa_receipt_sha256": PRIOR_QA_RECEIPT_SHA256,
            "scope_note": "Ace applies only to the exact prior artifact hash; no Ace or browser claim is made for the final hash.",
        },
        "qa_receipt": identity(QA_RECEIPT),
        "replays": replays,
        "schema": "o006.stat415.consolidated-epub-static-reflow-qa.v1",
        "status": "passed",
        "validation_scope": {
            "final_hash": ["deterministic replay A", "deterministic replay B", "EPUBCheck 5.3.0", "static XML/link/package audit", "static CSS/reflow/focusability audit"],
            "not_run_for_final_hash": ["Ace", "Chrome", "Chromium", "Playwright", "Puppeteer", "Electron", "WebView"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    receipt = audit()
    data = canonical(receipt)
    if args.check_only:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != data:
            raise RuntimeError("Stored static reflow QA receipt differs from replay")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(data)
    print(json.dumps({"bytes": receipt["artifact"]["bytes"], "candidates": receipt["checks"]["math_reflow_candidate_count"], "sha256": receipt["artifact"]["sha256"], "status": receipt["status"]}, sort_keys=True))


if __name__ == "__main__":
    main()
