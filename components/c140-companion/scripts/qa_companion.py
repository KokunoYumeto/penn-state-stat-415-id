#!/usr/bin/env python3
"""Static and deterministic QA for the browser-free C140 companion boundary."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from bs4 import BeautifulSoup

import build_companion as build


ROOT = build.ROOT
HTML = build.HTML_TARGET
BACKEND = build.BACKEND_TARGET
RECEIPT = ROOT / "build" / "C2_QA_RECEIPT.json"
SIM_RECEIPTS = build.SIMULATION_RECEIPTS
ENVIRONMENT = ROOT / "environment.lock.json"
PROBLEM_META_RE = re.compile(r"<!--PROBLEM_META\s+(\{[^\n]+\})-->")
PROHIBITED_IMPORTS = {"playwright", "selenium", "pyppeteer", "requests", "httpx", "socket"}
PRIVATE_PATTERNS = [
    re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?:api[_-]?key|access[_-]?token|password)\s*[:=]\s*[^\s<]+", re.IGNORECASE),
]


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(message)


def check_source_scripts() -> list[dict[str, object]]:
    rows = []
    paths = sorted((ROOT / "scripts").glob("*.py")) + [
        ROOT / "simulations" / "run_c1_simulations.py",
        ROOT / "simulations" / "run_c2_simulations.py",
    ]
    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        forbidden = sorted(imports & PROHIBITED_IMPORTS)
        if forbidden:
            fail(f"Prohibited browser/network import in {path.name}: {forbidden}")
        rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path.read_bytes())})
    return rows


def heading_anchors(document: build.Document) -> int:
    lines = document.body.splitlines()
    fenced = False
    headings = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if fenced or not re.match(r"^#{1,6}\s+", line):
            continue
        headings += 1
        cursor = index - 1
        while cursor >= 0 and not lines[cursor].strip():
            cursor -= 1
        if cursor < 0 or not build.ANCHOR_RE.fullmatch(lines[cursor].strip()):
            fail(f"Unanchored heading in {document.source_rel}: {line}")
    return headings


def section_after_anchor(body: str, anchor: str) -> str:
    marker = f'<a id="{anchor}"></a>'
    start = body.find(marker)
    if start < 0:
        return ""
    tail = body[start + len(marker):]
    match = re.search(r'\n<a id="[^"]+"></a>\n', tail)
    return tail[: match.start()] if match else tail


def check_problem_document(document: build.Document, expected: int) -> dict[str, object]:
    document_id = str(document.metadata["id"])
    problem_ids = sorted(anchor for anchor in document.anchors if re.fullmatch(re.escape(document_id) + r"-P\d{2}", anchor))
    if len(problem_ids) != expected:
        fail(f"{document_id} has {len(problem_ids)} problems, expected {expected}")
    expected_ids = [f"{document_id}-P{i:02d}" for i in range(1, expected + 1)]
    if problem_ids != expected_ids:
        fail(f"Non-contiguous problem IDs in {document_id}")
    metadata_rows: dict[str, dict[str, object]] = {}
    for raw in PROBLEM_META_RE.findall(document.body):
        row = json.loads(raw)
        metadata_rows[str(row.get("id"))] = row
    solution_words = 0
    for problem_id in problem_ids:
        row = metadata_rows.get(problem_id)
        if row is None:
            fail(f"Missing PROBLEM_META for {problem_id}")
        for key in ("prerequisites", "objective", "difficulty", "misconceptions"):
            if key not in row or row[key] in (None, "", []):
                fail(f"Empty problem metadata {key} for {problem_id}")
        for suffix in ("-H01", "-H02", "-ANS", "-SOL"):
            if problem_id + suffix not in document.anchors:
                fail(f"Missing {suffix} for {problem_id}")
        solution = section_after_anchor(document.body, problem_id + "-SOL")
        words = len(re.findall(r"\b[\wÀ-ÿ]+\b", solution, flags=re.UNICODE))
        if words < 25:
            fail(f"Worked solution is too short for {problem_id}: {words} words")
        solution_words += words
    return {"document_id": document_id, "problems": len(problem_ids), "solution_words": solution_words}


def check_sources(documents: list[build.Document]) -> dict[str, object]:
    anchors: set[str] = set()
    heading_count = 0
    mastery_rows = []
    assessment_rows = []
    for document in documents:
        document_id = str(document.metadata["id"])
        if document_id != "O006-C140-CMP-INDEX" and document.metadata["status"] != "complete":
            fail(f"Non-complete cumulative C2 document {document_id}")
        heading_count += heading_anchors(document)
        for anchor in document.anchors:
            if not anchor.startswith(document_id + "-"):
                fail(f"Anchor {anchor} is outside document namespace {document_id}")
            if anchor in anchors:
                fail(f"Duplicate anchor {anchor}")
            anchors.add(anchor)
        if document.body.count(r"\(") != document.body.count(r"\)"):
            fail(f"Unbalanced inline math delimiters in {document.source_rel}")
        if document.body.count(r"\[") != document.body.count(r"\]"):
            fail(f"Unbalanced display math delimiters in {document.source_rel}")
        dollar_remainder = build.DOLLAR_DISPLAY_RE.sub("", document.body).replace(r"\$", "")
        if dollar_remainder.count("$") % 2:
            fail(f"Unbalanced dollar math delimiters in {document.source_rel}")
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(document.body):
                fail(f"Privacy or credential pattern in {document.source_rel}")
        if document.metadata["type"] == "mastery":
            mastery_rows.append(check_problem_document(document, 8))
        if document.metadata["type"] == "assessment":
            row = check_problem_document(document, 10)
            rubrics = [anchor for anchor in document.anchors if re.search(r"-RUB\d*$", anchor)]
            if not rubrics:
                fail(f"Assessment lacks rubric: {document_id}")
            row["rubrics"] = len(rubrics)
            assessment_rows.append(row)
    mastery_ids = [str(row["document_id"]) for row in mastery_rows]
    expected_mastery_ids = [
        "O006-C140-CMP-MS07",
        "O006-C140-CMP-MS08",
        "O006-C140-CMP-MS09",
        "O006-C140-CMP-MS10",
        "O006-C140-CMP-MS12",
    ]
    if mastery_ids != expected_mastery_ids or len(assessment_rows) != 1:
        fail("Cumulative C2 mastery/assessment document census mismatch")
    problem_count = sum(int(row["problems"]) for row in mastery_rows + assessment_rows)
    if problem_count != 50:
        fail(f"Cumulative C2 problem census mismatch: {problem_count}, expected 50")
    return {
        "anchors": len(anchors),
        "assessments": assessment_rows,
        "documents": len(documents),
        "headings": heading_count,
        "mastery_sets": mastery_rows,
        "problems": problem_count,
        "references": sum(len(item.references) for item in documents),
        "source_bytes": sum(len(item.raw) for item in documents),
    }


def check_simulations() -> dict[str, object]:
    batch_rows: list[dict[str, object]] = []
    simulation_ids: list[str] = []
    total_files = 0
    for batch, receipt_path in SIM_RECEIPTS.items():
        if not receipt_path.is_file():
            fail(f"Missing {batch.upper()} simulation receipt")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("status") != "pass":
            fail(f"{batch.upper()} simulation receipt does not pass")
        if receipt.get("browser_processes_used") is not False or receipt.get("network_access") is not False:
            fail(f"{batch.upper()} simulation receipt browser/network claim mismatch")
        if batch == "c1":
            if receipt.get("schema") != "o006.c140.companion-c1-simulations.v1":
                fail("C1 simulation receipt schema mismatch")
            ids = [row["id"] for row in receipt.get("simulations", [])]
            expected = [f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 5)]
            if receipt.get("all_assertions_pass") is not True:
                fail("C1 aggregate simulation assertion failed")
            if not all(all(row["assertions"].values()) for row in receipt.get("simulations", [])):
                fail("A C1 numerical simulation assertion failed")
        elif batch == "c2":
            if receipt.get("schema") != "o006.c140.companion-c2-simulations.v1":
                fail("C2 simulation receipt schema mismatch")
            ids = ["O006-C140-CMP-SIM005"]
            expected = ids
            assertions = receipt.get("summary", {}).get("assertions", {})
            if not assertions or not all(assertions.values()):
                fail("A C2 numerical simulation assertion failed")
        else:
            fail(f"Unknown simulation batch {batch}")
        if ids != expected:
            fail(f"{batch.upper()} simulation ID order mismatch: {ids}")
        simulation_ids.extend(ids)

        manifest_path = build.GENERATED_BATCHES[batch] / "MANIFEST.csv"
        manifest_rows = list(csv.DictReader(manifest_path.read_text(encoding="utf-8").splitlines()))
        expected_files = 9 if batch == "c1" else 3
        if len(manifest_rows) != expected_files:
            fail(f"{batch.upper()} simulation file census mismatch: {len(manifest_rows)}")
        for row in manifest_rows:
            relative = row.get("path") or row.get("filename")
            if not relative:
                fail(f"{batch.upper()} simulation manifest lacks a path column")
            path = ROOT / PurePosixPath(relative) if row.get("path") else build.GENERATED_BATCHES[batch] / relative
            payload = path.read_bytes()
            if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
                fail(f"Simulation manifest mismatch: {relative}")
            if path.suffix == ".svg":
                svg_root = ElementTree.fromstring(payload)
                namespace = "{http://www.w3.org/2000/svg}"
                if svg_root.find(namespace + "title") is None or svg_root.find(namespace + "desc") is None:
                    fail(f"Accessible SVG title/desc missing: {relative}")
            built_path = HTML / "assets" / "simulations" / path.name
            if not built_path.is_file() or built_path.read_bytes() != payload:
                fail(f"Built simulation asset mismatch: {relative}")
        built_manifest = HTML / "assets" / "simulations" / "manifests" / f"{batch}.csv"
        if not built_manifest.is_file() or built_manifest.read_bytes() != manifest_path.read_bytes():
            fail(f"Built {batch.upper()} simulation manifest mismatch")
        built_receipt = HTML / "assets" / "simulations" / "receipts" / receipt_path.name
        if not built_receipt.is_file() or built_receipt.read_bytes() != receipt_path.read_bytes():
            fail(f"Built {batch.upper()} simulation receipt mismatch")
        if batch == "c1":
            manifest_record = receipt.get("manifest", {})
            if (
                manifest_record.get("bytes") != len(manifest_path.read_bytes())
                or manifest_record.get("sha256") != sha256(manifest_path.read_bytes())
                or receipt.get("files") != len(manifest_rows) + 1
            ):
                fail("C1 simulation receipt inventory mismatch")
        else:
            expected_outputs = [
                {
                    "bytes": path.stat().st_size,
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path.read_bytes()),
                }
                for path in [manifest_path] + [
                    build.GENERATED_BATCHES[batch] / str(row["filename"])
                    for row in manifest_rows
                ]
            ]
            if receipt.get("outputs") != expected_outputs:
                fail("C2 simulation receipt inventory mismatch")
        total_files += len(manifest_rows)
        batch_rows.append({
            "batch": batch,
            "files": len(manifest_rows),
            "manifest_sha256": sha256(manifest_path.read_bytes()),
            "receipt_sha256": sha256(receipt_path.read_bytes()),
            "simulations": len(ids),
        })
    expected_all = [f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 6)]
    if simulation_ids != expected_all:
        fail(f"Cumulative simulation census mismatch: {simulation_ids}")
    return {
        "batches": batch_rows,
        "files": total_files,
        "simulation_ids": simulation_ids,
        "simulations": len(simulation_ids),
    }


def resolve_local(page: Path, value: str) -> Path | None:
    split = urlsplit(value)
    if split.scheme or split.netloc or value.startswith("#") or value.startswith("mailto:"):
        return None
    clean = unquote(split.path)
    if not clean:
        return None
    candidate = (page.parent / PurePosixPath(clean)).resolve()
    try:
        candidate.relative_to(HTML.resolve())
    except ValueError:
        fail(f"Path escapes HTML closure: {page.name} -> {value}")
    return candidate


def check_html(documents: list[build.Document]) -> dict[str, object]:
    manifest_rows = list(csv.DictReader((HTML / "MANIFEST.csv").read_text(encoding="utf-8").splitlines()))
    for row in manifest_rows:
        path = HTML / PurePosixPath(row["path"])
        payload = path.read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            fail(f"HTML manifest mismatch: {row['path']}")
    page_count = 0
    image_count = 0
    local_links = 0
    external_links = 0
    ids: set[str] = set()
    for document in documents:
        page = HTML / PurePosixPath(document.output_rel)
        soup = BeautifulSoup(page.read_bytes(), "html.parser")
        page_count += 1
        if soup.html is None or soup.html.get("lang") != "id-ID" or soup.title is None:
            fail(f"HTML language/title missing: {document.output_rel}")
        page_ids = [str(node["id"]) for node in soup.find_all(attrs={"id": True})]
        if len(page_ids) != len(set(page_ids)):
            fail(f"Duplicate HTML ID in {document.output_rel}")
        for anchor in document.anchors:
            if anchor not in page_ids:
                fail(f"Source anchor missing from HTML: {anchor}")
        ids.update(page_ids)
        for image in soup.find_all("img"):
            image_count += 1
            if not str(image.get("alt", "")).strip():
                fail(f"Empty image alternative in {document.output_rel}")
        for node, attribute in [(node, "href") for node in soup.find_all(href=True)] + [(node, "src") for node in soup.find_all(src=True)]:
            value = str(node.get(attribute))
            split = urlsplit(value)
            if split.scheme in {"http", "https"}:
                if node.name != "a" or attribute != "href":
                    fail(f"External runtime resource in {document.output_rel}: {value}")
                external_links += 1
                continue
            if value.lower().startswith("javascript:"):
                fail(f"javascript URL in {document.output_rel}")
            target = resolve_local(page, value)
            if target is not None:
                local_links += 1
                if not target.is_file():
                    fail(f"Broken local link in {document.output_rel}: {value}")
        text = page.read_text(encoding="utf-8")
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                fail(f"Privacy pattern in built HTML {document.output_rel}")
    css = (HTML / "assets" / "style.css").read_text(encoding="utf-8")
    if "@media(max-width:780px)" not in css or "overflow-x:auto" not in css:
        fail("Static responsive/reflow CSS gate failed")
    return {
        "external_links": external_links,
        "files": len(manifest_rows) + 1,
        "images": image_count,
        "local_links": local_links,
        "manifest_sha256": sha256((HTML / "MANIFEST.csv").read_bytes()),
        "pages": page_count,
        "unique_html_ids": len(ids),
    }


def check_backend(documents: list[build.Document]) -> dict[str, object]:
    entities = [json.loads(line) for line in (BACKEND / "entities.jsonl").read_text(encoding="utf-8").splitlines()]
    entity_ids = [row["entity_id"] for row in entities]
    if len(entity_ids) != len(set(entity_ids)):
        fail("Duplicate backend entity ID")
    local_ids = set(entity_ids)
    external_urls, _ = build.load_external_targets()
    relations = list(csv.DictReader((BACKEND / "relations.csv").read_text(encoding="utf-8").splitlines()))
    for row in relations:
        if row["subject"] not in local_ids:
            fail(f"Unknown relation subject {row['subject']}")
        if row["scope"] == "local" and row["object"] not in local_ids:
            fail(f"Unknown local relation object {row['object']}")
        if row["scope"] == "external" and row["object"] not in external_urls:
            fail(f"Unknown external relation object {row['object']}")
    manifest = BACKEND / "MANIFEST.csv"
    for row in csv.DictReader(manifest.read_text(encoding="utf-8").splitlines()):
        payload = (BACKEND / row["path"]).read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            fail(f"Backend manifest mismatch: {row['path']}")
    document_rows = (BACKEND / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    if len(document_rows) != len(documents):
        fail("Backend document census mismatch")
    return {
        "documents": len(document_rows),
        "entities": len(entities),
        "manifest_sha256": sha256(manifest.read_bytes()),
        "relations": len(relations),
    }


def compute_receipt() -> bytes:
    environment = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    if environment != {
        "browser_processes_permitted": False,
        "locale": "id-ID",
        "numpy": "2.4.4",
        "python": "3.13.9",
        "schema": "o006.c140.companion-environment.v1",
        "status": "locked",
    }:
        fail("Environment lock differs from the admitted cumulative C2 environment")
    documents = build.load_documents()
    receipt = {
        "backend": check_backend(documents),
        "browser_processes_used": False,
        "build_receipt_sha256": sha256(build.RECEIPT_TARGET.read_bytes()),
        "environment_sha256": sha256(ENVIRONMENT.read_bytes()),
        "html": check_html(documents),
        "network_access": False,
        "schema": "o006.c140.companion-cumulative-c2-qa.v1",
        "scripts": check_source_scripts(),
        "simulations": check_simulations(),
        "source": check_sources(documents),
        "status": "pass",
        "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
    }
    return build.canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payload = compute_receipt()
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT.write_bytes(payload)
        mode_name = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            fail("C2 QA receipt deterministic replay mismatch")
        mode_name = "verified"
    receipt = json.loads(payload)
    print(json.dumps({
        "documents": receipt["source"]["documents"],
        "entities": receipt["backend"]["entities"],
        "mode": mode_name,
        "problems": receipt["source"]["problems"],
        "receipt_sha256": sha256(payload),
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
