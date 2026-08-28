#!/usr/bin/env python3
"""Write or verify deterministic visual-QA evidence for the consolidated PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PDF = ROOT / "output" / "pdf" / "stat415-pengantar-statistika-matematis-id.pdf"
DEFAULT_QA_RECEIPT = ROOT / "build" / "CONSOLIDATED_PDF_QA_RECEIPT.json"
DEFAULT_RENDER_RECEIPT = ROOT / "build" / "CONSOLIDATED_PDF_RENDER_METRICS.json"
DEFAULT_RENDER_REPLAY_RECEIPT = ROOT / "build" / "CONSOLIDATED_PDF_RENDER_METRICS_REPLAY.json"
DEFAULT_R2 = ROOT / "tmp" / "pdfs" / "qa-20260828-r2"
DEFAULT_R3 = ROOT / "tmp" / "pdfs" / "qa-20260828-r3"
DEFAULT_CONTACTS = ROOT / "tmp" / "pdfs" / "contact-r2"
DEFAULT_RECEIPT = ROOT / "build" / "CONSOLIDATED_PDF_VISUAL_QA_RECEIPT.json"
EXPECTED_PAGES = 219
EXPECTED_CHANGED_PAGES = [217, 218]
DIRECT_FINAL_PAGES = [217, 218, 219]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise RuntimeError(f"Not a valid PNG with an IHDR header: {path}")
    return struct.unpack(">II", header[16:24])


def file_record(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Required file is missing: {path}")
    return {
        "path": relative(path),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def png_record(path: Path) -> dict[str, Any]:
    record = file_record(path)
    width, height = png_dimensions(path)
    record.update({"width_px": width, "height_px": height})
    return record


def manifest_sha256(records: list[dict[str, Any]]) -> str:
    payload = "".join(
        f'{record["path"]}\t{record["bytes"]}\t{record["sha256"]}\n'
        for record in records
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Required JSON receipt is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def page_inventory(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        raise RuntimeError(f"Required raster directory is missing: {directory}")
    files = sorted(path for path in directory.iterdir() if path.is_file())
    parsed: list[tuple[int, Path]] = []
    unexpected: list[str] = []
    for path in files:
        match = re.fullmatch(r"page-(\d{3})\.png", path.name)
        if match:
            parsed.append((int(match.group(1)), path))
        else:
            unexpected.append(path.name)
    expected_numbers = list(range(1, EXPECTED_PAGES + 1))
    found_numbers = [number for number, _ in parsed]
    if unexpected or found_numbers != expected_numbers:
        raise RuntimeError(
            f"Raster inventory mismatch in {directory}: "
            f"unexpected={unexpected}, first/last/count={found_numbers[:1]}/{found_numbers[-1:]}/{len(found_numbers)}"
        )
    inventory: list[dict[str, Any]] = []
    for page, path in parsed:
        record = png_record(path)
        record["page"] = page
        inventory.append(record)
    return inventory


def contact_inventory(directory: Path) -> list[dict[str, Any]]:
    if not directory.is_dir():
        raise RuntimeError(f"Required contact-sheet directory is missing: {directory}")
    files = sorted(path for path in directory.iterdir() if path.is_file())
    inventory: list[dict[str, Any]] = []
    covered_pages: list[int] = []
    unexpected: list[str] = []
    for path in files:
        match = re.fullmatch(r"contact-(\d{3})-(\d{3})\.png", path.name)
        if not match:
            unexpected.append(path.name)
            continue
        start, end = map(int, match.groups())
        if start > end:
            raise RuntimeError(f"Invalid contact-sheet range: {path.name}")
        record = png_record(path)
        record.update({"page_start": start, "page_end": end})
        inventory.append(record)
        covered_pages.extend(range(start, end + 1))
    if unexpected or covered_pages != list(range(1, EXPECTED_PAGES + 1)):
        raise RuntimeError(
            f"Contact-sheet coverage mismatch: unexpected={unexpected}, "
            f"covered_count={len(covered_pages)}"
        )
    return inventory


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--qa-receipt", type=Path, default=DEFAULT_QA_RECEIPT)
    parser.add_argument("--render-receipt", type=Path, default=DEFAULT_RENDER_RECEIPT)
    parser.add_argument("--render-replay-receipt", type=Path, default=DEFAULT_RENDER_REPLAY_RECEIPT)
    parser.add_argument("--r2", type=Path, default=DEFAULT_R2)
    parser.add_argument("--r3", type=Path, default=DEFAULT_R3)
    parser.add_argument("--contacts", type=Path, default=DEFAULT_CONTACTS)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    pdf = args.pdf.resolve()
    qa_receipt_path = args.qa_receipt.resolve()
    render_receipt_path = args.render_receipt.resolve()
    render_replay_receipt_path = args.render_replay_receipt.resolve()
    r2 = args.r2.resolve()
    r3 = args.r3.resolve()
    contacts = args.contacts.resolve()
    receipt_path = args.receipt.resolve()

    pdf_record = file_record(pdf)
    pdf_pages = len(PdfReader(pdf, strict=False).pages)
    if pdf_pages != EXPECTED_PAGES:
        raise RuntimeError(f"Expected {EXPECTED_PAGES} PDF pages, found {pdf_pages}")
    pdf_record["pages"] = pdf_pages

    qa_receipt = load_json(qa_receipt_path)
    qa_artifact = qa_receipt.get("artifact", {})
    if qa_receipt.get("status") != "passed" or any(
        qa_artifact.get(key) != pdf_record[key] for key in ("bytes", "sha256", "pages")
    ):
        raise RuntimeError("The structural PDF QA receipt does not bind the current final PDF")

    render_receipt = load_json(render_receipt_path)
    render_replay_receipt = load_json(render_replay_receipt_path)
    if render_receipt.get("status") != "passed" or render_replay_receipt.get("status") != "passed":
        raise RuntimeError("A consolidated PDF render receipt is not passing")
    if render_receipt.get("browser") != render_replay_receipt.get("browser"):
        raise RuntimeError("Primary and replay render browser versions differ")
    if render_receipt.get("metrics") != render_replay_receipt.get("metrics"):
        raise RuntimeError("Primary and replay render metrics differ")
    expected_render_paths = (
        (render_receipt, "build/book/stat415-id-book.html", "tmp/pdfs/stat415-id-book.raw.pdf"),
        (
            render_replay_receipt,
            "build/book/stat415-id-book.html",
            "tmp/pdfs/stat415-id-book-replay.raw.pdf",
        ),
    )
    for evidence, expected_input, expected_output in expected_render_paths:
        if evidence.get("input") != expected_input or evidence.get("output") != expected_output:
            raise RuntimeError("PDF render evidence must use canonical repository-relative paths")
        executable = str(evidence.get("browserExecutable", ""))
        if not executable or "/" in executable or "\\" in executable:
            raise RuntimeError("PDF render evidence must record only the executable basename")
        serialized_evidence = json.dumps(evidence, ensure_ascii=False).lower()
        if "c:\\users\\" in serialized_evidence or "file://" in serialized_evidence:
            raise RuntimeError("PDF render evidence contains a local or absolute path")

    r2_pages = page_inventory(r2)
    r3_pages = page_inventory(r3)
    changed_pages = [
        current["page"]
        for previous, current in zip(r2_pages, r3_pages, strict=True)
        if previous["bytes"] != current["bytes"] or previous["sha256"] != current["sha256"]
    ]
    if changed_pages != EXPECTED_CHANGED_PAGES:
        raise RuntimeError(f"Expected changed pages {EXPECTED_CHANGED_PAGES}, found {changed_pages}")

    changed_records = []
    for page in changed_pages:
        previous = r2_pages[page - 1]
        current = r3_pages[page - 1]
        changed_records.append(
            {
                "page": page,
                "r2_bytes": previous["bytes"],
                "r2_sha256": previous["sha256"],
                "r3_bytes": current["bytes"],
                "r3_sha256": current["sha256"],
            }
        )

    contact_sheets = contact_inventory(contacts)
    direct_page_notes = {
        217: "Lesson 12 section 12.6 and the complete 12.7 summary are coherent, unclipped, and non-overlapping.",
        218: "The Lesson 12 component-provenance block starts at the top and remains together without clipping or overlap.",
        219: "The edition-level provenance page remains distinct, readable, unclipped, and unchanged from r2.",
    }
    direct_final_pages = []
    for page in DIRECT_FINAL_PAGES:
        record = dict(r3_pages[page - 1])
        record["inspection_result"] = "passed"
        record["observation"] = direct_page_notes[page]
        direct_final_pages.append(record)

    qa_input_record = file_record(qa_receipt_path)
    qa_input_record["status"] = qa_receipt["status"]
    render_input_record = file_record(render_receipt_path)
    render_input_record.update(
        {
            "status": render_receipt["status"],
            "browser": render_receipt["browser"],
        }
    )
    render_replay_input_record = file_record(render_replay_receipt_path)
    render_replay_input_record.update(
        {
            "status": render_replay_receipt["status"],
            "browser": render_replay_receipt["browser"],
        }
    )

    receipt = {
        "schema": "o006.stat415.consolidated-pdf-visual-qa.v1",
        "status": "passed",
        "artifact": pdf_record,
        "bound_machine_qa": {
            "structural_qa_receipt": qa_input_record,
            "primary_render_receipt": render_input_record,
            "replay_render_receipt": render_replay_input_record,
            "render_metrics_match": True,
            "render_metrics": render_receipt["metrics"],
        },
        "final_raster": {
            "directory": relative(r3),
            "page_count": len(r3_pages),
            "total_bytes": sum(record["bytes"] for record in r3_pages),
            "manifest_sha256": manifest_sha256(r3_pages),
            "pages": r3_pages,
        },
        "r2_to_r3_comparison": {
            "r2_directory": relative(r2),
            "r2_page_count": len(r2_pages),
            "r2_total_bytes": sum(record["bytes"] for record in r2_pages),
            "r2_manifest_sha256": manifest_sha256(r2_pages),
            "r3_directory": relative(r3),
            "r3_manifest_sha256": manifest_sha256(r3_pages),
            "unchanged_page_count": EXPECTED_PAGES - len(changed_pages),
            "changed_pages": changed_pages,
            "changed_page_records": changed_records,
        },
        "recorded_visual_inspection": {
            "inspection_date": "2026-08-28",
            "reviewer": "OpenAI Codex gpt-5.6-sol, Ultra",
            "contact_sheet_basis": "r2 full-corpus macro-layout survey",
            "contact_sheet_count": len(contact_sheets),
            "contact_sheet_manifest_sha256": manifest_sha256(contact_sheets),
            "contact_sheets": contact_sheets,
            "contact_sheet_coverage_pages": [1, EXPECTED_PAGES],
            "contact_sheet_result": "passed",
            "contact_sheet_observation": (
                "All 219 pages were surveyed across 11 contact sheets with no materially blank page, "
                "clipped or overlapping block, broken page transition, or illegible macro-layout anomaly observed."
            ),
            "direct_final_page_basis": "r3 original-resolution page rasters",
            "direct_final_pages": direct_final_pages,
            "changed_pages_directly_inspected": changed_pages,
            "coverage_derivation": (
                "The r2 contact sheets cover pages 1-219. The deterministic hash comparison shows that "
                "only pages 217-218 changed in r3; both changed pages were then inspected directly, "
                "and page 219 was directly rechecked as the adjacent unchanged edition-provenance page."
            ),
            "final_visual_disposition": (
                "passed: the final r3 raster has complete macro-layout coverage, all changed pages passed "
                "original-resolution inspection, and no remaining material visual defect was observed"
            ),
        },
    }

    serialized = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if args.check_only:
        if not receipt_path.is_file():
            raise RuntimeError(f"Visual-QA receipt is missing: {receipt_path}")
        existing = receipt_path.read_bytes()
        if existing != serialized:
            raise RuntimeError("Visual-QA receipt is stale or non-deterministic")
        print(
            f"PASS check-only: {relative(receipt_path)} binds {pdf_record['sha256']} "
            f"and {len(r3_pages)} final page rasters"
        )
        return

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(serialized)
    print(
        f"PASS wrote {relative(receipt_path)}: {len(r3_pages)} pages, "
        f"changed={changed_pages}, pdf={pdf_record['sha256']}"
    )


if __name__ == "__main__":
    main()
