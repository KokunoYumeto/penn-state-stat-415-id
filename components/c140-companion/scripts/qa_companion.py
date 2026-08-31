#!/usr/bin/env python3
"""Static and deterministic QA for the browser-free C140 companion boundary."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import locale
import os
import platform
import re
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree

from bs4 import BeautifulSoup
import numpy
import scipy

import build_companion as build


ROOT = build.ROOT
HTML = build.HTML_TARGET
BACKEND = build.BACKEND_TARGET
RECEIPT = ROOT / "build" / "C3_QA_RECEIPT.json"
ACTIVE_BOUNDARY = "c3"
SIM_RECEIPTS = build.SIMULATION_RECEIPTS
ENVIRONMENT = ROOT / "environment.lock.json"
PROBLEM_META_RE = re.compile(r"<!--PROBLEM_META\s+(\{[^\n]+\})-->")
PROHIBITED_MODULES = {
    "aiohttp",
    "ctypes",
    "ftplib",
    "http.client",
    "httpx",
    "playwright",
    "pyppeteer",
    "requests",
    "selenium",
    "socket",
    "subprocess",
    "urllib.request",
    "urllib3",
    "webbrowser",
    "websocket",
}
PROHIBITED_PROCESS_CALLS = {
    "os.execl",
    "os.execle",
    "os.execlp",
    "os.execlpe",
    "os.execv",
    "os.execve",
    "os.execvp",
    "os.execvpe",
    "os.popen",
    "os.spawnl",
    "os.spawnle",
    "os.spawnlp",
    "os.spawnlpe",
    "os.spawnv",
    "os.spawnve",
    "os.spawnvp",
    "os.spawnvpe",
    "os.startfile",
    "os.system",
}
PRIVATE_PATTERNS = [
    re.compile(r"[A-Za-z]:[/\\]Users[/\\]", re.IGNORECASE),
    re.compile(r"/(?:home|Users)/[^/\s]+/", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?:api[_-]?key|access[_-]?token|password)\s*[:=]\s*[^\s<]+", re.IGNORECASE),
    re.compile(r"\bAuthorization\s*:\s*[^\r\n]+", re.IGNORECASE),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}={0,2}", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"https?://[^/\s:@]+:[^@\s/]+@", re.IGNORECASE),
    re.compile(r"[?&](?:access_token|token|api_key|apikey)=[^&\s]+", re.IGNORECASE),
]
TEXT_ASSET_SUFFIXES = {
    "", ".cfg", ".css", ".csv", ".env", ".html", ".ini", ".json", ".jsonl",
    ".md", ".py", ".svg", ".toml", ".tsv", ".txt", ".xml", ".yaml", ".yml",
}
VISIBLE_BINDING_TOKEN_RE = re.compile(
    r"(?:\[\[CP0[12]_[A-Z]+(?:\s|\])|@@CP0[12]_[^@\n]+@@|<<CP0[12]_[^>\n]+>>)"
)
INERT_TEMPLATE_RE = re.compile(r"<template\b[^>]*>.*?</template>", re.IGNORECASE | re.DOTALL)
FENCED_CODE_RE = re.compile(r"^```[^\n]*\n.*?^```\s*$", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"(`+)(?!`)(.*?)\1", re.DOTALL)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(message)


def check_private_payload(path: str, payload: bytes) -> None:
    if PurePosixPath(path).suffix.lower() not in TEXT_ASSET_SUFFIXES:
        return
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail(f"Non-UTF-8 text asset: {path}")
        raise AssertionError from exc
    for pattern in PRIVATE_PATTERNS:
        if pattern.search(text):
            fail(f"Privacy or credential pattern in packaged asset {path}")


def reader_visible_markdown(body: str) -> str:
    visible = INERT_TEMPLATE_RE.sub("", body)
    visible = FENCED_CODE_RE.sub("", visible)
    return INLINE_CODE_RE.sub("", visible)


def closed_tree_files(root: Path, label: str) -> list[Path]:
    """Enumerate one expected output tree while rejecting links and special entries."""
    if build.is_unsafe_link(root) or not root.is_dir():
        fail(f"{label} root is missing or unsafe")
    files: list[Path] = []
    for path in root.rglob("*"):
        if build.is_unsafe_link(path):
            fail(f"{label} tree contains an unsafe link: {path.relative_to(root).as_posix()}")
        if path.is_file():
            files.append(path)
        elif not path.is_dir():
            fail(f"{label} tree contains an unsafe entry: {path.relative_to(root).as_posix()}")
    return sorted(files)


def check_source_scripts() -> list[dict[str, object]]:
    rows = []
    paths = sorted((ROOT / "scripts").glob("*.py")) + [
        ROOT / "simulations" / "run_c1_simulations.py",
        ROOT / "simulations" / "run_c2_simulations.py",
        ROOT / "simulations" / "run_c3_simulations.py",
    ]
    if ACTIVE_BOUNDARY == "c5":
        # The post-QA release packager must bind the frozen C5 QA receipt; hashing
        # that packager into the same receipt would create an impossible cycle.
        paths = [
            path
            for path in paths
            if path.name != "package_c140_companion_c5_release.py"
        ]
        paths.extend([
            ROOT / "data" / "capstones" / "CP01" / "transform_cp01.py",
            ROOT / "capstones" / "run_cp01_analysis.py",
            ROOT / "data" / "capstones" / "CP02" / "transform_cp02.py",
            ROOT / "capstones" / "run_cp02_analysis.py",
        ])
    for path in sorted(paths):
        if build.is_unsafe_link(path) or not path.is_file():
            fail(f"Required source script is missing or unsafe: {path.relative_to(ROOT).as_posix()}")
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports: set[str] = set()
        bindings: dict[str, str] = {}
        forbidden_calls: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
                    local_name = alias.asname or alias.name.split(".", 1)[0]
                    bindings[local_name] = alias.name if alias.asname else local_name
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
                for alias in node.names:
                    if alias.name == "*":
                        fail(f"Wildcard import is prohibited in checked source {path.name}")
                    qualified = f"{node.module}.{alias.name}"
                    imports.add(qualified)
                    bindings[alias.asname or alias.name] = qualified

        def qualified_name(node: ast.AST) -> str:
            if isinstance(node, ast.Name):
                return bindings.get(node.id, node.id)
            if isinstance(node, ast.Attribute):
                prefix = qualified_name(node.value)
                return f"{prefix}.{node.attr}" if prefix else node.attr
            return ""

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = qualified_name(node.func)
                if name in PROHIBITED_PROCESS_CALLS or name in {"__import__", "importlib.import_module"}:
                    forbidden_calls.add(name)
        forbidden = sorted(
            name
            for name in imports
            if any(name == prefix or name.startswith(prefix + ".") for prefix in PROHIBITED_MODULES)
        )
        if forbidden:
            fail(f"Prohibited browser/network import in {path.name}: {forbidden}")
        if forbidden_calls:
            fail(f"Prohibited dynamic import/process launch in {path.name}: {sorted(forbidden_calls)}")
        rows.append({"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path.read_bytes())})
    return rows


def heading_anchors(document: build.Document) -> int:
    lines = document.body.splitlines()
    fenced = False
    in_template = False
    headings = 0
    for index, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and re.search(r"<template\b", line, flags=re.IGNORECASE):
            in_template = True
        if in_template:
            if re.search(r"</template>", line, flags=re.IGNORECASE):
                in_template = False
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


def problem_solution_after_anchor(body: str, document_id: str, anchor: str) -> str:
    marker = f'<a id="{anchor}"></a>'
    start = body.find(marker)
    if start < 0:
        return ""
    tail = body[start + len(marker):]
    match = re.search(
        rf'\n<a id="{re.escape(document_id)}-(?:P\d{{2}}|RUB00)"></a>\n',
        tail,
    )
    return tail[: match.start()] if match else tail


def check_problem_document(document: build.Document, expected: int) -> dict[str, object]:
    document_id = str(document.metadata["id"])
    visible_body = reader_visible_markdown(document.body)
    visible_anchors = tuple(build.ANCHOR_RE.findall(visible_body))
    problem_ids = sorted(anchor for anchor in visible_anchors if re.fullmatch(re.escape(document_id) + r"-P\d{2}", anchor))
    if len(problem_ids) != expected:
        fail(f"{document_id} has {len(problem_ids)} problems, expected {expected}")
    expected_ids = [f"{document_id}-P{i:02d}" for i in range(1, expected + 1)]
    if problem_ids != expected_ids:
        fail(f"Non-contiguous problem IDs in {document_id}")
    solution_anchors = sorted(
        anchor
        for anchor in visible_anchors
        if re.fullmatch(re.escape(document_id) + r"-P\d{2}-(?:H\d{2}|ANS|SOL)", anchor)
    )
    expected_solution_anchors = sorted(
        problem_id + suffix
        for problem_id in expected_ids
        for suffix in ("-H01", "-H02", "-ANS", "-SOL")
    )
    if solution_anchors != expected_solution_anchors:
        fail(f"Hint/answer/solution anchor contract differs in {document_id}")
    metadata_rows: dict[str, dict[str, object]] = {}
    raw_metadata_rows = PROBLEM_META_RE.findall(visible_body)
    for raw in raw_metadata_rows:
        row = json.loads(raw)
        row_id = str(row.get("id"))
        if row_id in metadata_rows:
            fail(f"Duplicate PROBLEM_META for {row_id}")
        metadata_rows[row_id] = row
    if set(metadata_rows) != set(expected_ids) or len(raw_metadata_rows) != expected:
        fail(f"PROBLEM_META contract differs in {document_id}")
    solution_words = 0
    for problem_id in problem_ids:
        row = metadata_rows.get(problem_id)
        if row is None:
            fail(f"Missing PROBLEM_META for {problem_id}")
        for key in ("prerequisites", "objective", "difficulty", "misconceptions"):
            if key not in row or row[key] in (None, "", []):
                fail(f"Empty problem metadata {key} for {problem_id}")
        for suffix in ("-H01", "-H02", "-ANS", "-SOL"):
            if problem_id + suffix not in visible_anchors:
                fail(f"Missing {suffix} for {problem_id}")
        solution = problem_solution_after_anchor(visible_body, document_id, problem_id + "-SOL")
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
    capstone_rows = []
    for document in documents:
        document_id = str(document.metadata["id"])
        index_may_remain_open = document_id == "O006-C140-CMP-INDEX" and ACTIVE_BOUNDARY != "c5"
        if document.metadata["status"] != "complete" and not index_may_remain_open:
            fail(f"Non-complete cumulative {ACTIVE_BOUNDARY.upper()} document {document_id}")
        heading_count += heading_anchors(document)
        visible_body = reader_visible_markdown(document.body)
        visible_anchors = tuple(build.ANCHOR_RE.findall(visible_body))
        if visible_anchors != document.anchors:
            fail(f"Hidden or code-only anchor in {document.source_rel}")
        for anchor in document.anchors:
            if not anchor.startswith(document_id + "-"):
                fail(f"Anchor {anchor} is outside document namespace {document_id}")
            if anchor in anchors:
                fail(f"Duplicate anchor {anchor}")
            anchors.add(anchor)
        if visible_body.count(r"\(") != visible_body.count(r"\)"):
            fail(f"Unbalanced inline math delimiters in {document.source_rel}")
        if visible_body.count(r"\[") != visible_body.count(r"\]"):
            fail(f"Unbalanced display math delimiters in {document.source_rel}")
        dollar_remainder = build.DOLLAR_DISPLAY_RE.sub("", visible_body).replace(r"\$", "")
        if dollar_remainder.count("$") % 2:
            fail(f"Unbalanced dollar math delimiters in {document.source_rel}")
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(document.body):
                fail(f"Privacy or credential pattern in {document.source_rel}")
        if document.metadata["type"] == "mastery":
            mastery_rows.append(check_problem_document(document, 8))
        if document.metadata["type"] == "assessment":
            row = check_problem_document(document, 10)
            rubrics = sorted(
                anchor
                for anchor in visible_anchors
                if re.fullmatch(re.escape(document_id) + r"-RUB\d{2}", anchor)
            )
            expected_rubrics = [f"{document_id}-RUB{i:02d}" for i in range(0, 11)]
            if rubrics != expected_rubrics:
                fail(f"Assessment rubric contract differs in {document_id}")
            row["rubrics"] = len(rubrics)
            assessment_rows.append(row)
        if document.metadata["type"] == "capstone":
            row = check_problem_document(document, 1)
            rubrics = sorted(
                anchor
                for anchor in visible_anchors
                if re.fullmatch(re.escape(document_id) + r"-RUB\d{2}", anchor)
            )
            expected_rubrics = [f"{document_id}-RUB{i:02d}" for i in range(0, 9)]
            if rubrics != expected_rubrics:
                fail(f"Capstone rubric contract differs in {document_id}")
            row["rubrics"] = len(rubrics)
            capstone_rows.append(row)
    mastery_ids = [str(row["document_id"]) for row in mastery_rows]
    expected_mastery_ids = (
        [f"O006-C140-CMP-MS{i:02d}" for i in range(0, 13)]
        if ACTIVE_BOUNDARY in {"c4", "c5"}
        else [f"O006-C140-CMP-MS{i:02d}" for i in range(7, 13)]
    )
    assessment_ids = [str(row["document_id"]) for row in assessment_rows]
    expected_assessment_ids = (
        [f"O006-C140-CMP-CA{i:02d}" for i in range(1, 5)]
        if ACTIVE_BOUNDARY == "c5"
        else ["O006-C140-CMP-CA01"]
    )
    capstone_ids = [str(row["document_id"]) for row in capstone_rows]
    expected_capstone_ids = (
        [f"O006-C140-CMP-CP{i:02d}" for i in range(1, 3)]
        if ACTIVE_BOUNDARY == "c5"
        else []
    )
    if (
        mastery_ids != expected_mastery_ids
        or assessment_ids != expected_assessment_ids
        or capstone_ids != expected_capstone_ids
    ):
        fail(f"Cumulative {ACTIVE_BOUNDARY.upper()} problem-document census mismatch")
    problem_count = sum(
        int(row["problems"])
        for row in mastery_rows + assessment_rows + capstone_rows
    )
    expected_problem_count = (
        8 * len(expected_mastery_ids)
        + 10 * len(expected_assessment_ids)
        + len(expected_capstone_ids)
    )
    if problem_count != expected_problem_count:
        fail(f"Cumulative {ACTIVE_BOUNDARY.upper()} problem census mismatch: {problem_count}, expected {expected_problem_count}")
    return {
        "anchors": len(anchors),
        "assessments": assessment_rows,
        "capstones": capstone_rows,
        "documents": len(documents),
        "headings": heading_count,
        "mastery_sets": mastery_rows,
        "problems": problem_count,
        "references": sum(len(item.references) for item in documents),
        "source_bytes": sum(len(item.raw) for item in documents),
    }


def receipt_simulation_ids(receipt: dict[str, object]) -> list[str]:
    tokens: set[str] = set()
    for row in receipt.get("outputs", []):
        if not isinstance(row, dict):
            fail("Simulation receipt output row is malformed")
        name = PurePosixPath(str(row.get("path", ""))).name
        match = re.match(r"(SIM\d{3})_", name)
        if match:
            tokens.add(match.group(1))
    return [f"O006-C140-CMP-{token}" for token in sorted(tokens)]


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
            ids = receipt_simulation_ids(receipt)
            expected = ["O006-C140-CMP-SIM005"]
            assertions = receipt.get("summary", {}).get("assertions", {})
            if not assertions or not all(assertions.values()):
                fail("A C2 numerical simulation assertion failed")
        elif batch == "c3":
            if receipt.get("schema") != "o006.c140.companion-c3-simulations.v1":
                fail("C3 simulation receipt schema mismatch")
            ids = receipt_simulation_ids(receipt)
            expected = ["O006-C140-CMP-SIM006"]
            if receipt.get("summary", {}).get("id") != expected[0]:
                fail("C3 simulation summary ID mismatch")
            assertions = receipt.get("summary", {}).get("assertions", {})
            if receipt.get("all_assertions_pass") is not True or not assertions or not all(assertions.values()):
                fail("A C3 numerical simulation assertion failed")
        else:
            fail(f"Unknown simulation batch {batch}")
        if ids != expected:
            fail(f"{batch.upper()} simulation ID order mismatch: {ids}")
        simulation_ids.extend(ids)

        manifest_path, manifest_entries = build.declared_simulation_assets(
            batch, build.GENERATED_BATCHES[batch]
        )
        manifest_rows = [row for row, _path in manifest_entries]
        expected_files = {"c1": 9, "c2": 3, "c3": 4}[batch]
        if len(manifest_rows) != expected_files:
            fail(f"{batch.upper()} simulation file census mismatch: {len(manifest_rows)}")
        for row, path in manifest_entries:
            relative = row.get("path") or row.get("filename")
            if not relative:
                fail(f"{batch.upper()} simulation manifest lacks a path column")
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
            batch_output_paths = [path for _row, path in manifest_entries]
            expected_outputs = [
                {
                    "bytes": path.stat().st_size,
                    "path": path.relative_to(ROOT).as_posix(),
                    "sha256": sha256(path.read_bytes()),
                }
                for path in [manifest_path] + batch_output_paths
            ]
            if receipt.get("outputs") != expected_outputs:
                fail(f"{batch.upper()} simulation receipt inventory mismatch")
        total_files += len(manifest_rows)
        batch_rows.append({
            "batch": batch,
            "files": len(manifest_rows),
            "manifest_sha256": sha256(manifest_path.read_bytes()),
            "receipt_sha256": sha256(receipt_path.read_bytes()),
            "simulations": len(ids),
        })
    expected_all = [f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 7)]
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


def check_accessible_svg(payload: bytes, label: str) -> None:
    try:
        svg_root = ElementTree.fromstring(payload)
    except ElementTree.ParseError as exc:
        fail(f"Malformed SVG in {label}: {exc}")
    namespace = "{http://www.w3.org/2000/svg}"
    title = svg_root.find(namespace + "title")
    description = svg_root.find(namespace + "desc")
    labelled = str(svg_root.attrib.get("aria-labelledby", "")).split()
    ids = {
        str(node.attrib.get("id"))
        for node in (title, description)
        if node is not None and node.attrib.get("id")
    }
    if (
        svg_root.attrib.get("role") != "img"
        or title is None
        or description is None
        or not "".join(title.itertext()).strip()
        or not "".join(description.itertext()).strip()
        or len(labelled) != 2
        or set(labelled) != ids
    ):
        fail(f"Accessible SVG contract differs: {label}")
    for node in svg_root.iter():
        local_name = node.tag.rsplit("}", 1)[-1].lower()
        if local_name == "script":
            fail(f"Script-bearing SVG is prohibited: {label}")
        for attribute, value in node.attrib.items():
            attribute_name = attribute.rsplit("}", 1)[-1].lower()
            if attribute_name.startswith("on"):
                fail(f"Event-bearing SVG is prohibited: {label}")
            if attribute_name == "href" and urlsplit(str(value)).scheme:
                fail(f"External SVG dependency is prohibited: {label}")


def check_html(documents: list[build.Document]) -> dict[str, object]:
    html_files = closed_tree_files(HTML, "HTML")
    build.require_regular_file(HTML / "MANIFEST.csv", "HTML manifest")
    manifest_rows = list(csv.DictReader((HTML / "MANIFEST.csv").read_text(encoding="utf-8").splitlines()))
    manifest_paths = [str(row["path"]) for row in manifest_rows]
    if len(manifest_paths) != len(set(manifest_paths)):
        fail("Duplicate HTML manifest path")
    if ACTIVE_BOUNDARY == "c5":
        raw_coverage = "assets/capstones/CP02/CP02_coverage.csv"
        compressed_coverage = raw_coverage + ".gz"
        if raw_coverage in manifest_paths or compressed_coverage not in manifest_paths:
            fail("CP02 public coverage-ledger derivative boundary differs")
    actual_paths = {path.relative_to(HTML).as_posix() for path in html_files}
    expected_paths = {"MANIFEST.csv", *manifest_paths}
    if actual_paths != expected_paths:
        fail(
            "HTML directory is not manifest-closed: "
            f"missing={sorted(expected_paths - actual_paths)}, "
            f"extra={sorted(actual_paths - expected_paths)}"
        )
    for row in manifest_rows:
        relative = PurePosixPath(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"Unsafe HTML manifest path: {row['path']}")
        path = HTML / relative
        payload = path.read_bytes()
        if len(payload) > 100_000_000:
            fail(f"Public HTML asset exceeds the 100,000,000-byte Git content cap: {row['path']}")
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            fail(f"HTML manifest mismatch: {row['path']}")
        check_private_payload(str(row["path"]), payload)
    page_count = 0
    image_count = 0
    local_links = 0
    external_links = 0
    details_count = 0
    svg_image_count = 0
    table_count = 0
    ids: set[str] = set()
    fragment_ids: dict[Path, set[str]] = {}
    for document in documents:
        page = HTML / PurePosixPath(document.output_rel)
        soup = BeautifulSoup(page.read_bytes(), "html.parser")
        page_count += 1
        if soup.html is None or soup.html.get("lang") != "id-ID" or soup.title is None:
            fail(f"HTML language/title missing: {document.output_rel}")
        mains = soup.find_all("main")
        if (
            len(mains) != 1
            or mains[0].get("id") != "main-content"
            or mains[0].get("tabindex") != "-1"
        ):
            fail(f"Main landmark differs: {document.output_rel}")
        navigation = soup.find_all("nav")
        if (
            len(navigation) != 1
            or navigation[0].get("aria-labelledby") != "companion-nav-title"
            or soup.find(id="companion-nav-title") is None
        ):
            fail(f"Navigation landmark differs: {document.output_rel}")
        skip_links = soup.select('a.skip-link[href="#main-content"]')
        if len(skip_links) != 1:
            fail(f"Skip link differs: {document.output_rel}")
        current_links = navigation[0].select('a[aria-current="page"]')
        if (
            len(current_links) != 1
            or resolve_local(page, str(current_links[0].get("href", ""))) != page.resolve()
        ):
            fail(f"Current-page navigation marker differs: {document.output_rel}")
        heading_levels = [
            int(node.name[1])
            for node in soup.find_all(re.compile(r"^h[1-6]$"))
        ]
        if not heading_levels or heading_levels[0] != 1:
            fail(f"Page heading does not begin at h1: {document.output_rel}")
        if any(current > previous + 1 for previous, current in zip(heading_levels, heading_levels[1:])):
            fail(f"Skipped heading level in {document.output_rel}")
        table_captions: list[str] = []
        for table in soup.find_all("table"):
            table_count += 1
            captions = table.find_all("caption", recursive=False)
            if len(captions) != 1:
                fail(f"Table caption differs: {document.output_rel}")
            caption_text = " ".join(captions[0].stripped_strings)
            if not caption_text:
                fail(f"Empty table caption in {document.output_rel}")
            table_captions.append(caption_text)
            for header in table.find_all("th"):
                if header.get("scope") not in {"col", "row", "colgroup", "rowgroup"}:
                    fail(f"Table header scope differs: {document.output_rel}")
        if len(table_captions) != len(set(table_captions)):
            fail(f"Duplicate table caption in {document.output_rel}")
        for disclosure in soup.find_all("details"):
            details_count += 1
            if len(disclosure.find_all("summary", recursive=False)) != 1:
                fail(f"Disclosure summary differs: {document.output_rel}")
        scripts = soup.find_all("script")
        if (
            len(scripts) != 2
            or scripts[0].get("src") is not None
            or not str(scripts[1].get("src", "")).endswith("assets/MathJax/tex-svg.js")
        ):
            fail(f"Unexpected active script surface in {document.output_rel}")
        if soup.find(["iframe", "object", "embed", "form"]) is not None:
            fail(f"Unexpected active embedded surface in {document.output_rel}")
        for text_node in soup.find_all(string=VISIBLE_BINDING_TOKEN_RE):
            if text_node.find_parent(["template", "code", "pre"]) is None:
                fail(f"Reader-visible unresolved capstone binding in {document.output_rel}")
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
            image_source = str(image.get("src", "")).strip()
            if not image_source:
                fail(f"Empty image source in {document.output_rel}")
            image_target = resolve_local(page, image_source)
            if image_target is not None and image_target.suffix.lower() == ".svg":
                if not image_target.is_file():
                    fail(f"Missing SVG image in {document.output_rel}: {image.get('src')}")
                svg_image_count += 1
                check_accessible_svg(
                    image_target.read_bytes(),
                    image_target.relative_to(HTML).as_posix(),
                )
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
                if split.fragment and target.suffix.lower() == ".html":
                    fragment = unquote(split.fragment)
                    if target not in fragment_ids:
                        target_soup = BeautifulSoup(target.read_bytes(), "html.parser")
                        fragment_ids[target] = {
                            str(node["id"])
                            for node in target_soup.find_all(attrs={"id": True})
                        }
                    if fragment not in fragment_ids[target]:
                        fail(f"Broken local fragment in {document.output_rel}: {value}")
        text = page.read_text(encoding="utf-8")
        for pattern in PRIVATE_PATTERNS:
            if pattern.search(text):
                fail(f"Privacy pattern in built HTML {document.output_rel}")
    css = (HTML / "assets" / "style.css").read_text(encoding="utf-8")
    if "@media(max-width:780px)" not in css or "overflow-x:auto" not in css:
        fail("Static responsive/reflow CSS gate failed")
    return {
        "external_links": external_links,
        "details": details_count,
        "files": len(manifest_rows) + 1,
        "images": image_count,
        "local_links": local_links,
        "manifest_sha256": sha256((HTML / "MANIFEST.csv").read_bytes()),
        "pages": page_count,
        "svg_images": svg_image_count,
        "tables": table_count,
        "unique_html_ids": len(ids),
    }


def check_random_donor_external_targets(
    documents: list[build.Document],
    external_urls: dict[str, str],
    external_titles: dict[str, str],
) -> dict[str, object]:
    expected = build.RANDOM_DONOR_REFERENCE_TARGETS
    referenced = {
        target
        for document in documents
        for target in document.references
        if target in expected
    }
    referenced.update(
        relation["target"]
        for document in documents
        for relation in build.normalized_relations(document)
        if relation["target"] in expected
    )
    if referenced != set(expected):
        fail(
            "Random donor reference closure differs: "
            f"missing={sorted(set(expected) - referenced)}, "
            f"extra={sorted(referenced - set(expected))}"
        )

    target = build.RANDOM_DONOR_TARGET
    if build.is_unsafe_link(target) or not target.is_file():
        fail("Random donor translated target is missing or unsafe")
    target_payload = target.read_bytes()
    target_bytes = len(target_payload)
    target_sha256 = sha256(target_payload)
    if (
        target_bytes != build.RANDOM_DONOR_TARGET_BYTES
        or target_sha256 != build.RANDOM_DONOR_TARGET_SHA256
    ):
        fail("Random donor translated target identity differs")
    target_soup = BeautifulSoup(target_payload, "html.parser")
    target_ids = {
        str(node.get("id"))
        for node in target_soup.find_all(id=True)
    }
    registry_path = (
        build.REPO / "components" / "random-completeness" / "backend" / "entities.jsonl"
    )
    registry = {
        str(row["entity_id"]): row
        for row in (
            json.loads(line)
            for line in registry_path.read_text(encoding="utf-8").splitlines()
        )
    }
    for entity_id, (fragment, label) in expected.items():
        row = registry[entity_id]
        if (
            row.get("translation_target_bytes") != target_bytes
            or row.get("translation_target_sha256") != target_sha256
        ):
            fail(f"Random donor registry target identity differs: {entity_id}")
        expected_url = build.RANDOM_DONOR_PUBLIC_PAGE + (
            f"#{fragment}" if fragment else ""
        )
        actual_url = external_urls.get(entity_id)
        if actual_url != expected_url:
            fail(f"Random donor public target differs: {entity_id} -> {actual_url}")
        parsed = urlsplit(actual_url)
        if not parsed.path.endswith(
            "/components/random-completeness/random/point/Sufficient.html"
        ):
            fail(f"Random donor target points to a base/index page: {entity_id}")
        if parsed.fragment != (fragment or ""):
            fail(f"Random donor public fragment differs: {entity_id}")
        if fragment is not None and fragment not in target_ids:
            fail(f"Random donor public fragment does not exist: {entity_id} -> {fragment}")
        if external_titles.get(entity_id) != label:
            fail(f"Random donor Indonesian label differs: {entity_id}")
        source_text = str(registry[entity_id].get("source_text") or "").strip()
        if source_text and external_titles.get(entity_id) == source_text:
            fail(f"Random donor label fell back to English source_text: {entity_id}")
    return {
        "page": build.RANDOM_DONOR_PUBLIC_PAGE,
        "references": len(referenced),
        "target_bytes": target_bytes,
        "target_sha256": target_sha256,
        "validated_fragments": sum(fragment is not None for fragment, _ in expected.values()),
    }


def check_backend(documents: list[build.Document]) -> dict[str, object]:
    backend_files = closed_tree_files(BACKEND, "backend")
    entities = [json.loads(line) for line in (BACKEND / "entities.jsonl").read_text(encoding="utf-8").splitlines()]
    entity_ids = [row["entity_id"] for row in entities]
    if len(entity_ids) != len(set(entity_ids)):
        fail("Duplicate backend entity ID")
    local_ids = set(entity_ids)
    external_urls, external_titles = build.load_external_targets()
    donor_targets = check_random_donor_external_targets(
        documents, external_urls, external_titles
    )
    relations = list(csv.DictReader((BACKEND / "relations.csv").read_text(encoding="utf-8").splitlines()))
    for row in relations:
        if row["subject"] not in local_ids:
            fail(f"Unknown relation subject {row['subject']}")
        if row["scope"] == "local" and row["object"] not in local_ids:
            fail(f"Unknown local relation object {row['object']}")
        if row["scope"] == "external" and row["object"] not in external_urls:
            fail(f"Unknown external relation object {row['object']}")
    manifest = BACKEND / "MANIFEST.csv"
    manifest_rows = list(csv.DictReader(manifest.read_text(encoding="utf-8").splitlines()))
    manifest_paths = [str(row["path"]) for row in manifest_rows]
    if len(manifest_paths) != len(set(manifest_paths)):
        fail("Duplicate backend manifest path")
    if ACTIVE_BOUNDARY == "c5":
        raw_coverage = "assets/capstones/CP02/CP02_coverage.csv"
        compressed_coverage = raw_coverage + ".gz"
        if raw_coverage in manifest_paths or compressed_coverage not in manifest_paths:
            fail("CP02 backend coverage-ledger derivative boundary differs")
    actual_paths = {path.relative_to(BACKEND).as_posix() for path in backend_files}
    expected_paths = {"MANIFEST.csv", *manifest_paths}
    if actual_paths != expected_paths:
        fail(
            "Backend directory is not manifest-closed: "
            f"missing={sorted(expected_paths - actual_paths)}, "
            f"extra={sorted(actual_paths - expected_paths)}"
        )
    for row in manifest_rows:
        relative = PurePosixPath(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"Unsafe backend manifest path: {row['path']}")
        payload = (BACKEND / relative).read_bytes()
        if len(payload) > 100_000_000:
            fail(f"Public backend asset exceeds the 100,000,000-byte Git content cap: {row['path']}")
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            fail(f"Backend manifest mismatch: {row['path']}")
        check_private_payload(str(row["path"]), payload)
    document_rows = (BACKEND / "documents.jsonl").read_text(encoding="utf-8").splitlines()
    if len(document_rows) != len(documents):
        fail("Backend document census mismatch")
    return {
        "documents": len(document_rows),
        "donor_targets": donor_targets,
        "entities": len(entities),
        "manifest_sha256": sha256(manifest.read_bytes()),
        "relations": len(relations),
    }


def check_capstones() -> dict[str, object]:
    if ACTIVE_BOUNDARY != "c5":
        return {"assets": 0, "capstones": [], "reader_assets": 0, "source_scripts": 0}
    assets = build.collect_capstone_assets()
    rights_payload = build.capstone_rights_payload(assets)
    rights_reader = HTML / "assets" / "capstones" / "ASSET_RIGHTS.jsonl"
    rights_backend = BACKEND / "capstone_asset_rights.jsonl"
    for path in (rights_reader, rights_backend):
        if not path.is_file() or path.read_bytes() != rights_payload:
            fail(f"Capstone rights metadata differs: {path.relative_to(ROOT).as_posix()}")
    rights_rows = [json.loads(line) for line in rights_payload.decode("utf-8").splitlines()]
    expected_ids = [build.capstone_asset_id(asset) for asset in assets]
    if [str(row.get("asset_id")) for row in rights_rows] != expected_ids:
        fail("Capstone rights metadata asset order or identity differs")

    html_manifest_paths = {
        str(row["path"])
        for row in csv.DictReader((HTML / "MANIFEST.csv").read_text(encoding="utf-8").splitlines())
    }
    summaries: list[dict[str, object]] = []
    for capstone, spec in build.CAPSTONE_SPECS.items():
        subset = [asset for asset in assets if asset.capstone == capstone]
        if not subset:
            fail(f"No manifest-closed assets for {capstone}")
        category_counts: dict[str, int] = {}
        svg_count = 0
        text_equivalents = 0
        for asset in subset:
            payload = build.capstone_asset_payload(asset)
            asset_id = build.capstone_asset_id(asset)
            category_counts[asset.category] = category_counts.get(asset.category, 0) + 1
            if asset.dataset_license != str(spec["dataset_license"]):
                fail(f"Dataset license binding differs for {asset_id}")
            if asset.category in {"clean_data", "source_data"}:
                expected_effective = str(spec["dataset_license"])
                expected_rights_model = "dataset-license"
            elif asset.category in {"source_transport_witness", "source_rights_witness"}:
                expected_effective = "NOASSERTION"
                expected_rights_model = "external-evidence-no-relicense"
            else:
                expected_effective = build.COMPANION_LICENSE
                expected_rights_model = "companion-original"
            if (
                asset.effective_license != expected_effective
                or asset.rights_model != expected_rights_model
            ):
                fail(f"Effective license differs for {asset_id}")
            built_backend = BACKEND / PurePosixPath(asset.backend_rel)
            if not built_backend.is_file() or built_backend.read_bytes() != payload:
                fail(f"Built capstone backend asset differs: {asset.backend_rel}")
            check_private_payload(asset.backend_rel, payload)
            if asset.reader_rel is None:
                if asset.category not in {
                    "source_data",
                    "source_metadata",
                    "source_rights_witness",
                    "source_script",
                    "source_transport_witness",
                }:
                    fail(f"Unexpected backend-only capstone asset: {asset_id}")
                if asset.category == "source_script" and any(
                    PurePosixPath(path).name == asset.source.name
                    for path in html_manifest_paths
                ):
                    fail(f"Capstone source script leaked into reader closure: {asset.source.name}")
            else:
                built_reader = HTML / PurePosixPath(asset.reader_rel)
                if asset.reader_rel not in html_manifest_paths:
                    fail(f"Reader manifest omits capstone asset: {asset.reader_rel}")
                if not built_reader.is_file() or built_reader.read_bytes() != payload:
                    fail(f"Built capstone reader asset differs: {asset.reader_rel}")
            if asset.category == "analysis" and asset.source.suffix.lower() in {".md", ".txt"}:
                text_equivalents += 1
            if asset.category == "analysis" and asset.source.suffix.lower() == ".svg":
                svg_count += 1
                svg_root = ElementTree.fromstring(payload)
                namespace = "{http://www.w3.org/2000/svg}"
                title = svg_root.find(namespace + "title")
                description = svg_root.find(namespace + "desc")
                labelled = str(svg_root.attrib.get("aria-labelledby", "")).split()
                ids = {
                    str(node.attrib.get("id"))
                    for node in (title, description)
                    if node is not None and node.attrib.get("id")
                }
                if (
                    svg_root.attrib.get("role") != "img"
                    or title is None
                    or description is None
                    or not "".join(title.itertext()).strip()
                    or not "".join(description.itertext()).strip()
                    or len(labelled) != 2
                    or set(labelled) != ids
                ):
                    fail(f"Accessible SVG contract differs: {asset.source.name}")
                for node in svg_root.iter():
                    local_name = node.tag.rsplit("}", 1)[-1].lower()
                    if local_name == "script":
                        fail(f"Script-bearing SVG is prohibited: {asset.source.name}")
                    for attribute, value in node.attrib.items():
                        attribute_name = attribute.rsplit("}", 1)[-1].lower()
                        if attribute_name.startswith("on"):
                            fail(f"Event-bearing SVG is prohibited: {asset.source.name}")
                        if attribute_name == "href" and urlsplit(str(value)).scheme:
                            fail(f"External SVG dependency is prohibited: {asset.source.name}")
        capstone_page = HTML / "capstones" / f"O006-C140-CMP-{capstone}.html"
        capstone_soup = BeautifulSoup(capstone_page.read_bytes(), "html.parser")
        linked_targets = {
            target
            for link in capstone_soup.find_all("a", href=True)
            if (target := resolve_local(capstone_page, str(link["href"]))) is not None
        }
        expected_reader_targets = {
            (HTML / PurePosixPath(asset.reader_rel)).resolve()
            for asset in subset
            if asset.reader_rel is not None
        }
        expected_reader_targets.add(rights_reader.resolve())
        if not expected_reader_targets.issubset(linked_targets):
            missing = sorted(path.name for path in expected_reader_targets - linked_targets)
            fail(f"{capstone} reader artifact index is incomplete: {missing}")
        if svg_count < 1 or text_equivalents < 1:
            fail(f"{capstone} lacks a static SVG or text-equivalent analysis asset")
        summaries.append({
            "assets": len(subset),
            "bytes": sum(len(build.capstone_asset_payload(asset)) for asset in subset),
            "capstone": capstone,
            "categories": dict(sorted(category_counts.items())),
            "dataset_license": str(spec["dataset_license"]),
            "reader_assets": sum(asset.reader_rel is not None for asset in subset),
            "source_scripts": category_counts.get("source_script", 0),
            "static_svgs": svg_count,
            "text_equivalents": text_equivalents,
        })
    return {
        "assets": len(assets),
        "capstones": summaries,
        "reader_assets": sum(asset.reader_rel is not None for asset in assets),
        "receipts": build.capstone_receipt_records(),
        "rights_sha256": sha256(rights_payload),
        "source_scripts": sum(asset.category == "source_script" for asset in assets),
    }


def check_build_receipt(documents: list[build.Document]) -> dict[str, object]:
    if build.is_unsafe_link(build.RECEIPT_TARGET) or not build.RECEIPT_TARGET.is_file():
        fail(f"Missing {ACTIVE_BOUNDARY.upper()} build receipt")
    payload = build.RECEIPT_TARGET.read_bytes()
    receipt = json.loads(payload)
    expected_schema = f"o006.c140.companion-cumulative-{ACTIVE_BOUNDARY}-build.v1"
    if (
        receipt.get("schema") != expected_schema
        or receipt.get("status") != "pass"
        or receipt.get("network_access") is not False
        or receipt.get("browser_processes_used") is not False
        or receipt.get("boundary") != f"cumulative-through-{ACTIVE_BOUNDARY}"
        or receipt.get("translation_provenance") != "OpenAI Codex gpt-5.6-sol, Ultra"
    ):
        fail(f"{ACTIVE_BOUNDARY.upper()} build receipt contract differs")
    expected_sources = [
        {
            "bytes": len(document.raw),
            "path": f"source/id-ID/{document.source_rel}",
            "sha256": sha256(document.raw),
        }
        for document in documents
    ]
    if (
        receipt.get("cumulative_documents") != len(documents)
        or receipt.get("cumulative_required_ids") != sorted(build.active_required_ids())
        or receipt.get("environment") != build.file_identity(ENVIRONMENT)
        or receipt.get("source") != expected_sources
    ):
        fail(f"{ACTIVE_BOUNDARY.upper()} build receipt source census differs")
    for key, target in (("html", HTML), ("backend", BACKEND)):
        record = receipt.get(key)
        if not isinstance(record, dict):
            fail(f"{ACTIVE_BOUNDARY.upper()} build receipt lacks {key} record")
        files = closed_tree_files(target, key)
        manifest = target / "MANIFEST.csv"
        if (
            record.get("files") != len(files)
            or record.get("bytes") != sum(path.stat().st_size for path in files)
            or record.get("manifest_sha256") != sha256(manifest.read_bytes())
        ):
            fail(f"{ACTIVE_BOUNDARY.upper()} build receipt {key} inventory differs")
    if ACTIVE_BOUNDARY == "c5":
        assets = build.collect_capstone_assets()
        expected_capstones = [
            {
                "assets": sum(1 for asset in assets if asset.capstone == capstone),
                "backend_bytes": sum(
                    len(build.capstone_asset_payload(asset))
                    for asset in assets
                    if asset.capstone == capstone
                ),
                "dataset_license": str(build.CAPSTONE_SPECS[capstone]["dataset_license"]),
                "document_id": f"O006-C140-CMP-{capstone}",
                "reader_assets": sum(
                    asset.reader_rel is not None for asset in assets if asset.capstone == capstone
                ),
                "source_scripts": sum(
                    asset.category == "source_script" for asset in assets if asset.capstone == capstone
                ),
            }
            for capstone in build.CAPSTONE_SPECS
        ]
        rights_payload = build.capstone_rights_payload(assets)
        support_sources = build.c5_support_source_records()
        for row in support_sources:
            backend_path = BACKEND / PurePosixPath(str(row["backend_path"]))
            source_path = build.REPO / PurePosixPath(str(row["path"]))
            if (
                not backend_path.is_file()
                or backend_path.read_bytes() != source_path.read_bytes()
            ):
                fail(f"C5 support source copy differs: {row['backend_path']}")
        if (
            receipt.get("capstones") != expected_capstones
            or receipt.get("capstone_receipts") != build.capstone_receipt_records()
            or receipt.get("rights_metadata_sha256") != sha256(rights_payload)
            or receipt.get("support_sources") != support_sources
            or receipt.get("public_derivatives") != [build.cp02_coverage_derivative_record()]
            or receipt.get("witness_redactions") != [build.cp02_redaction_record()]
        ):
            fail("C5 build receipt capstone inventory differs")
    return {
        "bytes": len(payload),
        "schema": expected_schema,
        "sha256": sha256(payload),
        "status": "pass",
    }


def compute_receipt() -> bytes:
    build.require_regular_file(ENVIRONMENT, "C5 environment lock")
    environment = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    expected_environment = (
        {
            "browser_processes_permitted": False,
            "locale": "id-ID",
            "numeric_locale": "C",
            "numpy": "2.4.4",
            "python": "3.13.9",
            "required_process_environment": {
                "MKL_NUM_THREADS": "1",
                "NUMEXPR_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "PYTHONHASHSEED": "0",
                "TZ": "UTC",
            },
            "scipy": "1.17.1",
            "schema": "o006.c140.companion-environment.v2",
            "status": "locked",
        }
        if ACTIVE_BOUNDARY == "c5"
        else {
            "browser_processes_permitted": False,
            "locale": "id-ID",
            "numpy": "2.4.4",
            "python": "3.13.9",
            "schema": "o006.c140.companion-environment.v1",
            "status": "locked",
        }
    )
    if environment != expected_environment:
        fail(f"Environment lock differs from the admitted cumulative {ACTIVE_BOUNDARY.upper()} environment")
    runtime: dict[str, object] | None = None
    if ACTIVE_BOUNDARY == "c5":
        actual_versions = {
            "numpy": numpy.__version__,
            "python": platform.python_version(),
            "scipy": scipy.__version__,
        }
        expected_versions = {
            name: str(environment[name]) for name in ("numpy", "python", "scipy")
        }
        if actual_versions != expected_versions:
            fail(
                "Runtime differs from the C5 environment lock: "
                f"actual={actual_versions}, expected={expected_versions}"
            )
        actual_numeric_locale = locale.setlocale(locale.LC_NUMERIC)
        if actual_numeric_locale != environment["numeric_locale"]:
            fail(
                "Numeric locale differs from the C5 environment lock: "
                f"actual={actual_numeric_locale}, expected={environment['numeric_locale']}"
            )
        for name, expected in environment["required_process_environment"].items():
            if os.environ.get(name) != expected:
                fail(f"Required deterministic process environment differs: {name}")
        runtime = {
            **actual_versions,
            "numeric_locale": actual_numeric_locale,
            "process_environment": {
                name: os.environ[name]
                for name in sorted(environment["required_process_environment"])
            },
        }
    documents = build.load_documents()
    receipt = {
        "backend": check_backend(documents),
        "build": check_build_receipt(documents),
        "browser_processes_used": False,
        "build_receipt_sha256": sha256(build.RECEIPT_TARGET.read_bytes()),
        "capstones": check_capstones(),
        "environment_sha256": sha256(ENVIRONMENT.read_bytes()),
        "html": check_html(documents),
        "network_access": False,
        **({"runtime": runtime} if runtime is not None else {}),
        "schema": f"o006.c140.companion-cumulative-{ACTIVE_BOUNDARY}-qa.v1",
        "scripts": check_source_scripts(),
        "simulations": check_simulations(),
        "source": check_sources(documents),
        "status": "pass",
        "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
    }
    return build.canonical_json(receipt)


def main() -> None:
    global ACTIVE_BOUNDARY, RECEIPT
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    boundary = parser.add_mutually_exclusive_group()
    boundary.add_argument("--c4", action="store_true", help="QA the cumulative MS00-MS06 boundary")
    boundary.add_argument("--c5", action="store_true", help="QA the cumulative assessment/capstone boundary")
    args = parser.parse_args()
    if args.c4:
        ACTIVE_BOUNDARY = "c4"
        build.ACTIVE_BOUNDARY = "c4"
        build.RECEIPT_TARGET = ROOT / "build" / "C4_BUILD_RECEIPT.json"
        RECEIPT = ROOT / "build" / "C4_QA_RECEIPT.json"
    elif args.c5:
        ACTIVE_BOUNDARY = "c5"
        build.ACTIVE_BOUNDARY = "c5"
        build.RECEIPT_TARGET = ROOT / "build" / "C5_BUILD_RECEIPT.json"
        RECEIPT = ROOT / "build" / "C5_QA_RECEIPT.json"
    payload = compute_receipt()
    if args.write:
        build.atomic_write_file(RECEIPT, payload)
        mode_name = "written"
    else:
        if build.is_unsafe_link(RECEIPT) or not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            fail(f"{ACTIVE_BOUNDARY.upper()} QA receipt deterministic replay mismatch")
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
