#!/usr/bin/env python3
"""Deterministic structural, mathematical, rights, link, and accessibility QA."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "FIRST_UNIT_MANIFEST.csv"
BUILD_RECEIPT = ROOT / "build" / "FIRST_UNIT_BUILD_RECEIPT.json"
QA_RECEIPT = ROOT / "build" / "FIRST_UNIT_QA_RECEIPT.json"
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
CORRECTIONS = ROOT / "backend" / "first_unit_corrections.jsonl"
TRANSLATIONS = ROOT / "source" / "id-ID" / "first_unit_translation.csv"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_READER = {
    PurePosixPath("index.html"), PurePosixPath("Lesson00.html"),
    PurePosixPath("assets/reader.css"), PurePosixPath("assets/MathJax/tex-svg.js"),
    PurePosixPath("licenses/index.html"), PurePosixPath("licenses/MathJax-3.1.2-LICENSE.txt"),
    *(PurePosixPath(f"assets/415lesson{i}thumb.png") for i in range(13)),
}
REMOVED_STABLE_UNITS = {"O006-PSU-001-U0342", "O006-PSU-001-U0350"}


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


def manifest_rows() -> list[dict[str, str]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if {PurePosixPath(row["relative_path"]) for row in rows} != EXPECTED_READER:
        raise RuntimeError("reader manifest path set differs")
    if len(rows) != 19:
        raise RuntimeError("reader manifest count differs")
    for row in rows:
        data = (BUILD / Path(PurePosixPath(row["relative_path"]).as_posix())).read_bytes()
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {row['relative_path']}")
    return rows


def local_reference(owner: PurePosixPath, reference: str) -> tuple[PurePosixPath, str | None] | None:
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(("mailto:", "tel:", "data:")):
        return None
    path = parsed.path
    if not path:
        resolved = owner
    else:
        combined = owner.parent / PurePosixPath(path)
        parts: list[str] = []
        for part in combined.parts:
            if part in {"", "."}:
                continue
            if part == "..":
                if not parts:
                    raise RuntimeError(f"local reference escapes reader: {owner} -> {reference}")
                parts.pop()
            else:
                parts.append(part)
        resolved = PurePosixPath(*parts)
    return resolved, parsed.fragment or None


def validate_links(pages: dict[PurePosixPath, BeautifulSoup]) -> list[dict[str, str]]:
    edges: list[dict[str, str]] = []
    for owner, soup in pages.items():
        for tag, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src")):
            for node in soup.select(f"{tag}[{attr}]"):
                reference = str(node[attr])
                local = local_reference(owner, reference)
                if local is None:
                    continue
                resolved, fragment = local
                candidate = BUILD / Path(resolved.as_posix())
                if not candidate.is_file():
                    raise RuntimeError(f"broken local reference: {owner} -> {reference}")
                if fragment and resolved.suffix.lower() in {".html", ".htm"}:
                    target = pages.get(resolved)
                    if target is None:
                        target = BeautifulSoup(candidate.read_bytes(), "html.parser")
                    if target.find(id=fragment) is None:
                        raise RuntimeError(f"broken local fragment: {owner} -> {reference}")
                edges.append({"owner": owner.as_posix(), "reference": reference, "resolved": resolved.as_posix()})
    return sorted(edges, key=lambda row: (row["owner"], row["reference"], row["resolved"]))


def math_and_structure(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    source_soups = {
        PurePosixPath(name): BeautifulSoup((NORMALIZED / name).read_bytes(), "html.parser")
        for name in ("index.html", "Lesson00.html")
    }
    source_stable: set[str] = set()
    target_stable: set[str] = set()
    math_differences: list[dict[str, object]] = []
    per_document: dict[str, object] = {}
    for path in (PurePosixPath("index.html"), PurePosixPath("Lesson00.html")):
        source_main = source_soups[path].select_one("main#quarto-document-content")
        target_main = pages[path].select_one("main#quarto-document-content")
        if source_main is None or target_main is None:
            raise RuntimeError(f"semantic main missing: {path}")
        source_ids = [str(node["data-o006-id"]) for node in source_main.select("[data-o006-id]")]
        target_ids = [str(node["data-o006-id"]) for node in target_main.select("[data-o006-id]")]
        if len(source_ids) != len(set(source_ids)) or len(target_ids) != len(set(target_ids)):
            raise RuntimeError(f"stable unit ID repeated: {path}")
        source_stable.update(source_ids)
        target_stable.update(target_ids)
        source_math = [node.get_text() for node in source_main.select(".math")]
        target_math = [node.get_text() for node in target_main.select(".math")]
        if len(source_math) != len(target_math):
            raise RuntimeError(f"math count differs: {path}")
        for ordinal, (before, after) in enumerate(zip(source_math, target_math), start=1):
            if before != after:
                math_differences.append({
                    "document": path.as_posix(), "ordinal": ordinal,
                    "source_sha256": sha256(before.encode("utf-8")),
                    "target_sha256": sha256(after.encode("utf-8")),
                })
        per_document[path.as_posix()] = {
            "source_stable_units": len(source_ids), "target_stable_units": len(target_ids),
            "math_nodes": len(target_math),
        }
    if source_stable - target_stable != REMOVED_STABLE_UNITS or target_stable - source_stable:
        raise RuntimeError("target stable-unit topology differs beyond the registered empty-column removal")
    if len(source_stable) != 562 or len(target_stable) != 560:
        raise RuntimeError("stable-unit census differs")
    if len(math_differences) != 8:
        raise RuntimeError("math differences are not the eight registered formula corrections")
    if per_document["Lesson00.html"]["math_nodes"] != 331 or per_document["index.html"]["math_nodes"] != 0:
        raise RuntimeError("math-node census differs")
    return {
        "source_stable_units": len(source_stable), "target_stable_units": len(target_stable),
        "removed_stable_units": sorted(REMOVED_STABLE_UNITS),
        "math_differences": math_differences, "per_document": per_document,
    }


def page_semantics(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    for path, soup in pages.items():
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"locale metadata missing: {path}")
        if "\ufffd" in str(soup):
            raise RuntimeError(f"Unicode replacement character present: {path}")
        ids = [str(node["id"]) for node in soup.select("[id]")]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"duplicate DOM ID: {path}")
        if soup.select("[onclick], [data-bs-toggle], [data-bs-target], script[src^='http']"):
            raise RuntimeError(f"upstream runtime or inline event handler retained: {path}")
        provenance = soup.select_one(f'meta[name="translation-provenance"][content="{PROVENANCE}"]')
        if provenance is None:
            raise RuntimeError(f"exact model provenance missing: {path}")

    index = pages[PurePosixPath("index.html")]
    lesson = pages[PurePosixPath("Lesson00.html")]
    images = index.select("main img[src]")
    if len(images) != 13 or any(not image.get("alt", "").strip() for image in images):
        raise RuntimeError("landing image/alt-text census differs")
    pending = index.select("a.pending-source[data-translation-status='pending']")
    if len(pending) != 12 or any(not str(anchor.get("href", "")).startswith("https://online.stat.psu.edu/stat415/Lesson") for anchor in pending):
        raise RuntimeError("pending-lesson routing differs")
    local_lesson = index.select('main a[href="Lesson00.html"]')
    if len(local_lesson) != 1:
        raise RuntimeError("local Lesson00 card route differs")

    details = lesson.select("details.solution")
    if len(details) != 4:
        raise RuntimeError("accessible solution disclosure count differs")
    for node in details:
        summary = node.find("summary", recursive=False)
        if summary is None or summary.get_text(" ", strip=True) != "Penyelesaian" or not node.get("data-source-control-id"):
            raise RuntimeError("solution disclosure semantics differ")
        if len(node.get_text(" ", strip=True)) <= len("Penyelesaian"):
            raise RuntimeError("solution disclosure body is empty")
    if lesson.select("button, .collapse"):
        raise RuntimeError("Bootstrap solution controls remain")
    if len(lesson.select(".example")) != 5:
        raise RuntimeError("worked-example count differs")
    inline_solutions = [node for node in lesson.select("strong") if node.get_text(" ", strip=True) == "Penyelesaian"]
    if len(inline_solutions) != 1:
        raise RuntimeError("inline solution count differs")
    table = lesson.select_one("#exm-cdf table")
    if table is None or any(len(row.find_all(["th", "td"], recursive=False)) != 5 for row in table.select("tr")):
        raise RuntimeError("corrected Example 5 table differs")
    if lesson.select("pre") or "Therefore," in lesson.get_text(" "):
        raise RuntimeError("accidental source code block remains")
    if lesson.select_one("#psu415-l00-def-margpdf[data-source-id='def-margpmf']") is None:
        raise RuntimeError("duplicate source anchor mapping missing")
    if len(lesson.select("#def-margpmf")) != 1:
        raise RuntimeError("first marginal-PMF source anchor not preserved uniquely")
    scripts = lesson.select("script[src]")
    if len(scripts) != 1 or scripts[0]["src"] != "assets/MathJax/tex-svg.js":
        raise RuntimeError("local MathJax script route differs")
    if index.select("script"):
        raise RuntimeError("landing page contains unnecessary script")
    return {
        "landing_images_with_alt": len(images), "pending_official_lesson_links": len(pending),
        "accessible_solution_details": len(details), "inline_solutions": len(inline_solutions),
        "worked_examples": len(lesson.select(".example")), "dom_ids_unique": True,
        "analytics": False, "cookies": False, "local_mathjax_only": True,
    }


def correction_gate() -> dict[str, object]:
    rows = [json.loads(line) for line in CORRECTIONS.read_text("utf-8").splitlines() if line]
    expected = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 15)}
    if len(rows) != 14 or {row.get("correction_id") for row in rows} != expected:
        raise RuntimeError("correction backend differs")
    if any(not str(row.get("status", "")).startswith("applied") for row in rows):
        raise RuntimeError("correction backend contains an unapplied record")
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        translations = list(csv.DictReader(stream))
    if len(translations) != 523 or any(row["status"] != "translated" or not row["target_text"].strip() for row in translations):
        raise RuntimeError("translation completion gate differs")
    return {"registered": 14, "applied": 14, "translation_segments_complete": 523}


def compute() -> bytes:
    rows = manifest_rows()
    page_paths = (PurePosixPath("index.html"), PurePosixPath("Lesson00.html"), PurePosixPath("licenses/index.html"))
    pages = {path: BeautifulSoup((BUILD / Path(path.as_posix())).read_bytes(), "html.parser") for path in page_paths}
    links = validate_links(pages)
    structure = math_and_structure(pages)
    semantics = page_semantics({path: pages[path] for path in page_paths[:2]})
    corrections = correction_gate()
    build_receipt = BUILD_RECEIPT.read_bytes()
    build_data = json.loads(build_receipt)
    if build_data.get("status") != "built" or build_data.get("translation_segments") != 523:
        raise RuntimeError("build receipt status differs")
    receipt = {
        "schema": "o006.stat415.first-unit-qa.v1", "status": "pass",
        "coverage": "landing/index plus complete Lesson00", "locale": "id-ID",
        "reader": {"files": len(rows), "bytes": sum(int(row["bytes"]) for row in rows), "manifest_sha256": sha256(MANIFEST.read_bytes())},
        "build_receipt": {"path": BUILD_RECEIPT.relative_to(ROOT).as_posix(), "bytes": len(build_receipt), "sha256": sha256(build_receipt)},
        "structure_and_math": structure, "semantics_accessibility_privacy": semantics,
        "corrections_and_translation": corrections,
        "local_reference_edges": {"count": len(links), "edges": links},
        "gates": [
            "manifest-identities", "complete-translation-ledger", "stable-id-topology",
            "registered-formula-differences-only", "local-links-and-fragments",
            "asset-alt-text", "accessible-solutions", "unique-dom-ids",
            "rights-and-provenance", "offline-runtime", "no-analytics-or-cookies",
        ],
    }
    return canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payload = compute()
    if args.write:
        atomic_write(QA_RECEIPT, payload)
        state = "written"
    else:
        if not QA_RECEIPT.is_file() or QA_RECEIPT.read_bytes() != payload:
            raise RuntimeError("first-unit QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({"mode": state, "status": data["status"], "reader_files": data["reader"]["files"], "reader_bytes": data["reader"]["bytes"], "receipt_sha256": sha256(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
