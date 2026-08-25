#!/usr/bin/env python3
"""Independent deterministic QA for STAT 415 id-ID through Lesson 02."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup

import qa_through_lesson01 as prior


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON02_MANIFEST.csv"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON02_BUILD_RECEIPT.json"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON02_QA_RECEIPT.json"
DOCUMENTS = ROOT / "backend" / "through_lesson02_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson02_corrections.jsonl"
TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson02_translation.csv"
SEGMENTS = ROOT / "working" / "lesson02_segments.csv"
BINDINGS = ROOT / "backend" / "lesson02_translation_bindings.jsonl"
NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON02_NORMALIZATION_RECEIPT.json"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON02_TRANSLATION_RECEIPT.json"
ASSET_RECEIPT = ROOT / "authority" / "LESSON02_ASSET_FREEZE_RECEIPT.json"
ASSET_MANIFEST = ROOT / "authority" / "LESSON02_ASSET_MANIFEST.csv"
ASSET_AUDIT = ROOT / "working" / "lesson02_asset_rights_audit.json"
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

CONTENT = {
    "index": ("O006-PSU-000", 77, 197, 0, "https://online.stat.psu.edu/stat415/"),
    "Lesson00": ("O006-PSU-001", 446, 365, 331, "https://online.stat.psu.edu/stat415/Lesson00"),
    "Lesson01": ("O006-PSU-002", 221, 188, 169, "https://online.stat.psu.edu/stat415/Lesson01"),
    "Lesson02": ("O006-PSU-003", 324, 228, 209, "https://online.stat.psu.edu/stat415/Lesson02"),
}
LESSON01_SVGS = {
    "STAT-415-SEC-3-18-09.svg",
    "stat-415-sec-3-18-10.svg",
    "stat-415-sec-3-18-11.svg",
    "stat-415-sec-3-18-12.svg",
    "STAT-415-SEC-3-18-13.svg",
}
LESSON02_ASSETS = {
    "dartboard.png": (32701, "c8ddb1d7befe425ac72efd04abd75c0835aae62c786765256f3f8d93ee3ec0cd"),
    "unnamed-chunk-1-1.png": (10942, "564048b4327b3a379fe9921efa9224760f6c6afd01135f17d941af393a8f4532"),
}
EXPECTED_READER = {
    *(PurePosixPath(f"{name}.html") for name in CONTENT),
    PurePosixPath("assets/reader-4of14.css"),
    PurePosixPath("assets/MathJax/tex-svg.js"),
    PurePosixPath("assets/MathJax/input/tex/extensions/color.js"),
    PurePosixPath("assets/MathJax/input/tex/extensions/enclose.js"),
    PurePosixPath("assets/MathJax/input/tex/extensions/cancel.js"),
    PurePosixPath("licenses/index.html"),
    PurePosixPath("licenses/MathJax-3.1.2-LICENSE.txt"),
    *(PurePosixPath(f"assets/415lesson{i}thumb.png") for i in range(13)),
    *(PurePosixPath(f"assets/{name}") for name in LESSON01_SVGS),
    *(PurePosixPath(f"assets/{name}") for name in LESSON02_ASSETS),
}
PARTS = {
    "a": (ROOT / "working" / "lesson02_translation_part_a.json", 1, 108),
    "b": (ROOT / "working" / "lesson02_translation_part_b.json", 109, 216),
    "c": (ROOT / "working" / "lesson02_translation_part_c.json", 217, 324),
}
EXPECTED_CORRECTIONS = {f"O006-PSU-ADV-{number:04d}" for number in range(1, 30)}
EXPECTED_LESSON02_MATH_CHANGES = {
    "O006-PSU-003-M0062",
    "O006-PSU-003-M0073",
    "O006-PSU-003-M0075",
    "O006-PSU-003-M0078",
    "O006-PSU-003-M0102",
    "O006-PSU-003-M0152",
    "O006-PSU-003-M0160",
    "O006-PSU-003-M0177",
    "O006-PSU-003-M0200",
    "O006-PSU-003-M0208",
}
HISTORICAL = {
    "backend/through_lesson01_corrections.jsonl": (6506, "f66a3106401d473d2aa8208e5e04823f1b6d4e830c86d5fed61285e96fd5c7c4"),
    "backend/through_lesson01_documents.jsonl": (2005, "d8983d875f55fad9df56b1dfe6962456fa357b359c14d42c253318f8775a5bc1"),
    "build/THROUGH_LESSON01_BUILD_RECEIPT.json": (7122, "ae926ca4f9a3d0d1723b059fbc578365bfd5fc704521a7a990b98bdd4bc4a1c2"),
    "build/THROUGH_LESSON01_MANIFEST.csv": (2798, "6a047b981eeb71e740450678b4f802fb7ec3eb954cf92ffc3cebbaf8a050b5a7"),
}


def reader_manifest_gate() -> dict[str, object]:
    header, rows = prior.load_csv(MANIFEST)
    if header != ["relative_path", "bytes", "sha256"] or len(rows) != 31:
        raise RuntimeError("Lesson02 reader manifest schema or row count differs")
    paths: list[PurePosixPath] = []
    for row in rows:
        path = PurePosixPath(row["relative_path"])
        if path.is_absolute() or ".." in path.parts or path.as_posix() != row["relative_path"]:
            raise RuntimeError(f"unsafe reader path: {row['relative_path']}")
        if not HEX64.fullmatch(row["sha256"]):
            raise RuntimeError(f"malformed reader hash: {path}")
        try:
            expected_bytes = int(row["bytes"])
        except ValueError as exc:
            raise RuntimeError(f"malformed reader byte count: {path}") from exc
        raw = prior.require_file(BUILD / Path(path.as_posix()))
        if len(raw) != expected_bytes or prior.sha256(raw) != row["sha256"]:
            raise RuntimeError(f"reader identity differs: {path}")
        paths.append(path)
    if paths != sorted(paths, key=lambda value: value.as_posix().casefold()):
        raise RuntimeError("reader manifest order is not canonical")
    if len(paths) != len(set(paths)) or set(paths) != EXPECTED_READER:
        raise RuntimeError("reader manifest has a missing, extra, or duplicate file")
    actual = {
        PurePosixPath(path.relative_to(BUILD).as_posix())
        for path in BUILD.rglob("*")
        if path.is_file()
    }
    if actual != EXPECTED_READER:
        raise RuntimeError(
            f"reader tree differs; missing={sorted(EXPECTED_READER-actual, key=str)}, "
            f"extra={sorted(actual-EXPECTED_READER, key=str)}"
        )
    manifest_raw = prior.require_file(MANIFEST)
    return {
        "files": 31,
        "bytes": sum(int(row["bytes"]) for row in rows),
        "manifest_bytes": len(manifest_raw),
        "manifest_sha256": prior.sha256(manifest_raw),
    }


def load_pages() -> tuple[dict[PurePosixPath, BeautifulSoup], dict[str, BeautifulSoup]]:
    paths = [*(PurePosixPath(f"{name}.html") for name in CONTENT), PurePosixPath("licenses/index.html")]
    pages = {
        path: BeautifulSoup(prior.require_file(BUILD / Path(path.as_posix())), "html.parser")
        for path in paths
    }
    return pages, {name: pages[PurePosixPath(f"{name}.html")] for name in CONTENT}


def translation_gate() -> dict[str, object]:
    historical = prior.translation_gate()
    required = [
        "segment_id", "document_id", "component_id", "section_id",
        "source_sha256", "source_text", "target_text", "status",
    ]
    header, rows = prior.load_csv(TRANSLATIONS)
    template_header, template = prior.load_csv(SEGMENTS)
    if header != required or template_header != required or len(rows) != 324 or len(template) != 324:
        raise RuntimeError("Lesson02 translation/template schema or census differs")
    expected_ids = [f"O006-PSU-003-S{number:04d}" for number in range(1, 325)]
    if [row["segment_id"] for row in rows] != expected_ids or [row["segment_id"] for row in template] != expected_ids:
        raise RuntimeError("Lesson02 segment order differs")
    parts: dict[str, str] = {}
    part_counts: dict[str, int] = {}
    for name, (path, first, last) in PARTS.items():
        values = prior.load_json(path)
        expected = {f"O006-PSU-003-S{number:04d}" for number in range(first, last + 1)}
        if set(values) != expected or any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise RuntimeError(f"Lesson02 translation partition differs: {name}")
        if set(parts).intersection(values):
            raise RuntimeError("Lesson02 translation partitions overlap")
        parts.update({str(key): str(value) for key, value in values.items()})
        part_counts[name] = len(values)
    template_by_id = {row["segment_id"]: row for row in template}
    for row in rows:
        sid = row["segment_id"]
        source = row["source_text"]
        witness = template_by_id[sid]
        if any(row[field] != witness[field] for field in (
            "document_id", "component_id", "section_id", "source_sha256", "source_text"
        )):
            raise RuntimeError(f"Lesson02 source binding differs: {sid}")
        if row["document_id"] != "O006-PSU-003" or row["component_id"] != "Lesson02":
            raise RuntimeError(f"Lesson02 component identity differs: {sid}")
        if prior.sha256(source.encode("utf-8")) != row["source_sha256"]:
            raise RuntimeError(f"Lesson02 source hash differs: {sid}")
        leading = source[: len(source) - len(source.lstrip())]
        trailing = source[len(source.rstrip()) :]
        expected_target = leading + parts[sid].strip() + trailing
        if row["status"] != "translated" or row["target_text"] != expected_target:
            raise RuntimeError(f"Lesson02 target/partition differs: {sid}")
    bindings = prior.load_jsonl(BINDINGS)
    if len(bindings) != 324:
        raise RuntimeError("Lesson02 translation-binding census differs")
    for ordinal, (row, binding) in enumerate(zip(rows, bindings), start=1):
        if (
            binding.get("schema") != "o006.stat415.translation-binding.v1"
            or binding.get("segment_id") != row["segment_id"]
            or binding.get("document_id") != "O006-PSU-003"
            or binding.get("component_id") != "Lesson02"
            or binding.get("ordinal") != ordinal
            or binding.get("locale") != "id-ID"
            or binding.get("source_sha256") != row["source_sha256"]
            or binding.get("target_sha256") != prior.sha256(row["target_text"].encode("utf-8"))
            or binding.get("status") != "translated"
        ):
            raise RuntimeError(f"Lesson02 translation binding differs: {row['segment_id']}")
    visible = "\n".join(row["target_text"] for row in rows).casefold()
    for term in ("penduga titik", "penduga tak bias", "ruang parameter", "rataan kuadrat galat", "kecukupan", "metode momen"):
        if term not in visible:
            raise RuntimeError(f"required Lesson02 term missing: {term}")
    if "mean squared error" in visible or "galat kuadrat rata-rata" in visible or "\ufffd" in visible:
        raise RuntimeError("Lesson02 target contains superseded or damaged terminology")
    receipt = prior.load_json(TRANSLATION_RECEIPT)
    if receipt.get("schema") != "o006.stat415.lesson02-translation.v1" or receipt.get("status") != "complete" or receipt.get("segment_count") != 324 or receipt.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("Lesson02 translation receipt contract differs")
    for field, path in (("translation_csv", TRANSLATIONS), ("bindings", BINDINGS)):
        record = receipt.get(field)
        actual = prior.identity(path)
        if not isinstance(record, dict) or record.get("path") != actual["path"] or record.get("bytes") != actual["bytes"] or record.get("sha256") != actual["sha256"]:
            raise RuntimeError(f"Lesson02 translation receipt identity differs: {field}")
    return {
        "historical_segments": historical["cumulative_segments"],
        "lesson02_segments": 324,
        "cumulative_segments": 1068,
        "partition_counts": part_counts,
        "translation_csv": prior.identity(TRANSLATIONS),
        "bindings": prior.identity(BINDINGS),
        "receipt": prior.identity(TRANSLATION_RECEIPT),
        "source_bindings_exact": True,
        "boundary_whitespace_preserved": True,
    }


def normalization_gate() -> dict[str, object]:
    historical = prior.normalization_gate()
    receipt = prior.load_json(NORMALIZATION_RECEIPT)
    counts = receipt.get("counts")
    expected = {
        "structural_units": 228, "translation_segments": 324, "math_nodes": 209,
        "math_inline": 161, "math_display": 48, "figures": 3, "images": 2,
        "solutions": 6, "proofs": 0, "examples": 12, "theorems": 0,
        "definitions": 3, "code_nodes": 0, "assets": 2, "catalogue_records": 764,
    }
    if receipt.get("schema") != "o006.stat415.lesson02-normalization.v1" or receipt.get("status") != "normalized-source-ready" or not isinstance(counts, dict):
        raise RuntimeError("Lesson02 normalization receipt contract differs")
    if any(counts.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Lesson02 normalization census differs")
    defects = receipt.get("source_defects")
    if not isinstance(defects, list) or {row.get("defect_id") for row in defects if isinstance(row, dict)} != {f"L02-D{i:03d}" for i in range(1, 10)}:
        raise RuntimeError("Lesson02 source-defect registry differs")
    outputs = receipt.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Lesson02 normalization outputs missing")
    for field, expected_path in (
        ("normalized", "source/normalized/en-US/Lesson02.html"),
        ("catalogue", "backend/lesson02_source_catalogue.jsonl"),
        ("segments", "working/lesson02_segments.csv"),
    ):
        prior.validate_identity_record(outputs.get(field), expected_path=expected_path, label=f"Lesson02 {field}")
    return {
        "historical": historical,
        "lesson02_receipt": prior.identity(NORMALIZATION_RECEIPT),
        "source_structural_units": 978,
        "lesson02_counts": expected,
        "source_defects": [f"L02-D{i:03d}" for i in range(1, 10)],
    }


def corrections_and_math_gate(content_pages: dict[str, BeautifulSoup]) -> dict[str, object]:
    historical_pages = {key: content_pages[key] for key in ("index", "Lesson00", "Lesson01")}
    historical_rows = prior.load_jsonl(ROOT / "backend" / "through_lesson01_corrections.jsonl")
    historical_math = prior.formula_and_unit_gate(historical_pages, historical_rows)
    rows = prior.load_jsonl(CORRECTIONS)
    if len(rows) != 29 or {row.get("correction_id") for row in rows} != EXPECTED_CORRECTIONS:
        raise RuntimeError("cumulative correction registry differs")
    if rows[:20] != historical_rows:
        raise RuntimeError("one or more historical correction records changed")
    current = rows[20:]
    expected_counts = [1, 3, 1, 1, 1, 1, 1, 1, 10]
    if [row.get("replacement_count") for row in current] != expected_counts:
        raise RuntimeError("Lesson02 correction replacement census differs")
    if [row.get("source_defect_id") for row in current] != [f"L02-D{i:03d}" for i in range(1, 10)]:
        raise RuntimeError("Lesson02 correction/defect binding differs")
    if any(row.get("status") != "applied-target-only" for row in current):
        raise RuntimeError("Lesson02 contains an unapplied correction")

    source = BeautifulSoup(prior.require_file(NORMALIZED / "Lesson02.html"), "html.parser")
    source_main = source.select_one("main#quarto-document-content")
    target_main = content_pages["Lesson02"].select_one("main#quarto-document-content")
    if source_main is None or target_main is None:
        raise RuntimeError("Lesson02 semantic main missing")
    source_units = [str(node["data-o006-id"]) for node in source_main.select("[data-o006-id]")]
    target_units = [str(node["data-o006-id"]) for node in target_main.select("[data-o006-id]")]
    if len(source_units) != 228 or source_units != target_units or len(set(source_units)) != 228:
        raise RuntimeError("Lesson02 stable-unit topology differs")
    source_nodes = source_main.select(".math")
    target_nodes = target_main.select(".math")
    source_ids = [str(node.get("data-o006-math-id", "")) for node in source_nodes]
    target_ids = [str(node.get("data-o006-math-id", "")) for node in target_nodes]
    if len(source_nodes) != 209 or source_ids != target_ids or len(set(source_ids)) != 209:
        raise RuntimeError("Lesson02 math-ID topology differs")
    source_by_id = {mid: node.get_text() for mid, node in zip(source_ids, source_nodes)}
    target_by_id = {mid: node.get_text() for mid, node in zip(target_ids, target_nodes)}
    actual_changes = {mid for mid in source_ids if source_by_id[mid] != target_by_id[mid]}
    if actual_changes != EXPECTED_LESSON02_MATH_CHANGES:
        raise RuntimeError("Lesson02 changed-math set differs from the nine registered corrections")
    evidence: dict[str, tuple[str, str]] = {}
    for row in current:
        surfaces = row.get("surfaces")
        if surfaces is None:
            surfaces = [row]
        if not isinstance(surfaces, list):
            raise RuntimeError(f"correction surface evidence malformed: {row.get('correction_id')}")
        for surface in surfaces:
            if not isinstance(surface, dict):
                raise RuntimeError(f"correction surface is not an object: {row.get('correction_id')}")
            mid = surface.get("math_id")
            before = surface.get("source_surface_sha256")
            after = surface.get("target_surface_sha256")
            if not isinstance(mid, str) or mid in evidence or not isinstance(before, str) or not isinstance(after, str) or not HEX64.fullmatch(before) or not HEX64.fullmatch(after):
                raise RuntimeError(f"correction math evidence differs: {row.get('correction_id')}")
            evidence[mid] = (before, after)
    if set(evidence) != EXPECTED_LESSON02_MATH_CHANGES:
        raise RuntimeError("Lesson02 correction math-evidence set differs")
    for mid, (before, after) in evidence.items():
        if prior.sha256(source_by_id[mid].encode("utf-8")) != before or prior.sha256(target_by_id[mid].encode("utf-8")) != after:
            raise RuntimeError(f"Lesson02 correction surface hash differs: {mid}")
    return {
        "historical": historical_math,
        "source_stable_units": 978,
        "target_stable_units": 976,
        "math_nodes": 709,
        "corrections": 29,
        "lesson02_corrections": 9,
        "lesson02_changed_math_surfaces": sorted(actual_changes),
        "correction_backend": prior.identity(CORRECTIONS),
    }


def document_and_language_gate(content_pages: dict[str, BeautifulSoup]) -> dict[str, object]:
    rows = prior.load_jsonl(DOCUMENTS)
    if len(rows) != 4 or [row.get("component_id") for row in rows] != list(CONTENT):
        raise RuntimeError("document backend coverage/order differs")
    result: dict[str, object] = {}
    for row, (component, (document_id, segments, source_units, math, url)) in zip(rows, CONTENT.items()):
        target_path = ROOT / "source" / "id-ID" / f"{component}.html"
        normalized_path = ROOT / "source" / "normalized" / "en-US" / f"{component}.html"
        target_raw = prior.require_file(target_path)
        build_raw = prior.require_file(BUILD / f"{component}.html")
        page = content_pages[component]
        main = page.select_one("main#quarto-document-content")
        if target_raw != build_raw or main is None:
            raise RuntimeError(f"target/reader or semantic main differs: {component}")
        if (
            row.get("schema") != "o006.stat415.document.v1"
            or row.get("document_id") != document_id
            or row.get("locale") != "id-ID"
            or row.get("translation_status") != "complete"
            or row.get("translation_segments") != segments
            or row.get("structural_units") != source_units
            or row.get("math_nodes") != math
            or row.get("source_url") != url
            or row.get("source_path") != f"source/normalized/en-US/{component}.html"
            or row.get("target_path") != f"source/id-ID/{component}.html"
            or row.get("target_bytes") != len(target_raw)
            or row.get("target_sha256") != prior.sha256(target_raw)
        ):
            raise RuntimeError(f"document backend record differs: {component}")
        if page.html is None or page.html.get("lang") != "id-ID":
            raise RuntimeError(f"id-ID document metadata missing: {component}")
        provenance = page.select_one('meta[name="translation-provenance"]')
        status = page.select_one('meta[name="edition-status"]')
        source_meta = page.select_one('meta[name="source-url"]')
        if provenance is None or provenance.get("content") != PROVENANCE or status is None or "4 of 14" not in str(status.get("content")) or source_meta is None or source_meta.get("content") != url:
            raise RuntimeError(f"document provenance/status/source metadata differs: {component}")
        stable = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
        math_ids = [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")]
        if len(stable) != len(set(stable)) or len(math_ids) != math or len(math_ids) != len(set(math_ids)):
            raise RuntimeError(f"duplicate or missing stable IDs: {component}")
        result[component] = {"segments": segments, "source_units": source_units, "target_units": len(stable), "math_nodes": math}

    lesson = content_pages["Lesson02"]
    text = lesson.get_text(" ", strip=True)
    folded = text.casefold()
    for required in (
        "Pendugaan (Bagian I)", "Gambaran Umum", "Tujuan", "Pendugaan Titik",
        "Pendugaan Tak Bias", "Varians dan Rataan Kuadrat Galat", "Kecukupan", "Metode Momen",
    ):
        if required.casefold() not in folded:
            raise RuntimeError(f"Lesson02 Indonesian semantic surface missing: {required}")
    for forbidden in (
        "Learning Objectives", "Point Estimation", "Unbiased Estimation", "Properties of Estimators",
        "Sufficient Statistics", "Method of Moments", "Mean Squared Error", "Solution", "Example 2.",
    ):
        if forbidden.casefold() in folded:
            raise RuntimeError(f"visible Lesson02 English surface remains: {forbidden}")
    if len(lesson.select(".theorem.example")) != 12 or len(lesson.select(".theorem.definition")) != 3:
        raise RuntimeError("Lesson02 example/definition topology differs")
    if len([node for node in lesson.select("h4") if node.get_text(" ", strip=True) == "Penyelesaian"]) != 6:
        raise RuntimeError("Lesson02 worked-solution heading census differs")
    alts = [str(node.get("alt", "")).strip() for node in lesson.select("[alt]")]
    if not alts or any(not alt or re.search(r"different dartboards|Graph of two estimators", alt, re.I) for alt in alts):
        raise RuntimeError("Lesson02 accessibility text is empty or remains in English")
    markup = prior.require_file(BUILD / "Lesson02.html").decode("utf-8")
    if "</span>merupakan" in markup or "assets/reader.css" in markup:
        raise RuntimeError("Lesson02 word boundary or stale CSS route remains")
    required_math = (
        r"E(X) = np",
        r"y^{1/\theta} \ln y - \theta y^{1/\theta}",
        r"\text{MSE}(\hat{\theta})=\text{Var}(\hat{\theta})+",
        r"\frac{p(1-p)}{30}+0.01",
    )
    if any(value not in markup for value in required_math):
        raise RuntimeError("one or more admitted Lesson02 mathematical repairs is absent")
    return {
        "documents": result,
        "lesson02_examples": 12,
        "lesson02_definitions": 3,
        "lesson02_worked_solutions": 6,
        "visible_language": "id-ID",
        "accessibility_text_localized": True,
        "document_backend": prior.identity(DOCUMENTS),
    }


def links_assets_gate(pages: dict[PurePosixPath, BeautifulSoup], content_pages: dict[str, BeautifulSoup]) -> dict[str, object]:
    edges: list[dict[str, str]] = []
    external = 0
    for owner, page in pages.items():
        for tag, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src")):
            for node in page.select(f"{tag}[{attr}]"):
                reference = str(node.get(attr, ""))
                parsed = urlparse(reference)
                local = prior.local_reference(owner, reference)
                if local is None:
                    if tag != "a" and not (tag == "link" and "license" in (node.get("rel") or [])):
                        raise RuntimeError(f"external executable/asset reference: {owner} -> {reference}")
                    if parsed.scheme not in {"http", "https", "mailto", "tel"}:
                        raise RuntimeError(f"unsupported reference scheme: {owner} -> {reference}")
                    external += 1
                    continue
                resolved, fragment = local
                if resolved not in EXPECTED_READER or not (BUILD / Path(resolved.as_posix())).is_file():
                    raise RuntimeError(f"broken or unmanifested local reference: {owner} -> {reference}")
                if fragment and resolved.suffix.lower() in {".html", ".htm"}:
                    target = pages.get(resolved) or BeautifulSoup(prior.require_file(BUILD / Path(resolved.as_posix())), "html.parser")
                    if target.find(id=fragment) is None:
                        raise RuntimeError(f"broken local fragment: {owner} -> {reference}")
                edges.append({"owner": owner.as_posix(), "reference": reference, "resolved": resolved.as_posix()})
    css = prior.require_file(BUILD / "assets" / "reader-4of14.css")
    css_text = css.decode("utf-8")
    for fragment in ("main img:not(.card-img)", "max-width: 100%", "height: auto", "main .quarto-float"):
        if fragment not in css_text:
            raise RuntimeError(f"reader reflow rule missing: {fragment}")
    if (BUILD / "assets" / "reader.css").exists():
        raise RuntimeError("stale unversioned reader CSS remains")
    lesson_images = content_pages["Lesson02"].select("img[src]")
    if [node.get("src") for node in lesson_images] != ["assets/dartboard.png", "assets/unnamed-chunk-1-1.png"]:
        raise RuntimeError("Lesson02 reader asset sequence differs")
    for filename, (size, digest) in LESSON02_ASSETS.items():
        authority = prior.require_file(ROOT / "authority" / "assets" / "stat415" / "lesson02" / filename)
        reader = prior.require_file(BUILD / "assets" / filename)
        if authority != reader or len(reader) != size or prior.sha256(reader) != digest or not reader.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError(f"Lesson02 frozen PNG identity differs: {filename}")
    freeze = prior.load_json(ASSET_RECEIPT)
    audit = prior.load_json(ASSET_AUDIT)
    if freeze.get("status") != "frozen-and-verified" or freeze.get("assets") != 2 or freeze.get("asset_bytes") != 43643:
        raise RuntimeError("Lesson02 asset freeze receipt differs")
    if audit.get("blocking_unresolved_rights") != [] or audit.get("summary", {}).get("frozen_assets") != 2:
        raise RuntimeError("Lesson02 asset rights audit is unresolved")
    return {
        "local_edges": len(edges),
        "local_edges_sha256": prior.sha256(prior.canonical_json(sorted(edges, key=lambda row: (row["owner"], row["reference"], row["resolved"])))),
        "external_anchor_edges": external,
        "all_local_targets_manifested": True,
        "lesson02_assets": 2,
        "lesson02_asset_bytes": 43643,
        "asset_manifest": prior.identity(ASSET_MANIFEST),
        "asset_receipt": prior.identity(ASSET_RECEIPT),
        "asset_audit": prior.identity(ASSET_AUDIT),
        "responsive_reader_css": prior.identity(BUILD / "assets" / "reader-4of14.css"),
    }


def privacy_runtime_rights_gate(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    forbidden = (
        "google-analytics", "googletagmanager", "gtag(", "matomo", "plausible.io", "hotjar",
        "clarity.ms", "segment.io", "document.cookie", "cookieconsent", "onetrust",
    )
    secrets = re.compile(r"github\s+tokens?\.md|zenodo\s+token|figshare\s+token|(?:api|access)[_-]?token|api[_-]?key|authorization\s*:\s*bearer", re.I)
    absolute = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|(?:^|[\"'\s])/(?:Users|home|tmp)/", re.I)
    for path in EXPECTED_READER:
        if path.suffix.lower() not in {".html", ".css", ".svg"}:
            continue
        text = prior.require_file(BUILD / Path(path.as_posix())).decode("utf-8")
        if any(marker in text.casefold() for marker in forbidden) or secrets.search(text) or absolute.search(text):
            raise RuntimeError(f"privacy/runtime marker present: {path}")
    for owner, page in pages.items():
        if page.select("iframe, object, embed"):
            raise RuntimeError(f"embedded external-capable object present: {owner}")
        if any(any(str(attr).lower().startswith("on") for attr in node.attrs) for node in page.find_all(True)):
            raise RuntimeError(f"inline event handler present: {owner}")
        scripts = page.select("script")
        expected_scripts = 1 if owner in {PurePosixPath(f"Lesson{i:02d}.html") for i in range(3)} else 0
        if len(scripts) != expected_scripts:
            raise RuntimeError(f"reader script census differs: {owner}")
        for script in scripts:
            if script.get("src") != "assets/MathJax/tex-svg.js" or script.get_text(strip=True):
                raise RuntimeError(f"nonlocal or inline script present: {owner}")
        styles = page.select('link[rel~="stylesheet"]')
        expected_href = "../assets/reader-4of14.css" if owner == PurePosixPath("licenses/index.html") else "assets/reader-4of14.css"
        if len(styles) != 1 or styles[0].get("href") != expected_href:
            raise RuntimeError(f"reader stylesheet route differs: {owner}")
    runtime_pairs = [
        (BUILD / "assets" / "MathJax" / "tex-svg.js", ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "tex-svg.js"),
        *( (BUILD / "assets" / "MathJax" / "input" / "tex" / "extensions" / name, ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "input" / "tex" / "extensions" / name) for name in ("color.js", "enclose.js", "cancel.js") ),
        (BUILD / "licenses" / "MathJax-3.1.2-LICENSE.txt", ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "LICENSE.txt"),
    ]
    if any(prior.require_file(left) != prior.require_file(right) for left, right in runtime_pairs):
        raise RuntimeError("local MathJax closure differs from frozen authority")
    licence = pages[PurePosixPath("licenses/index.html")]
    licence_text = licence.get_text(" ", strip=True)
    for fragment in ("Penn State", "CC BY-NC 4.0", "kecuali dinyatakan lain", "MathJax 3.1.2", "Apache License 2.0", PROVENANCE, "tidak resmi", "sembilan koreksi Lesson 02", "dua gambar Lesson 02", "tidak ada relisensi seragam"):
        if fragment not in licence_text:
            raise RuntimeError(f"rights/provenance surface missing: {fragment}")
    if licence.select_one('a[rel~="license"][href="https://creativecommons.org/licenses/by-nc/4.0/"]') is None:
        raise RuntimeError("Penn State licence link missing")
    return {
        "external_runtime_requests": 0,
        "inline_scripts": 0,
        "analytics": False,
        "cookies": False,
        "credential_paths": False,
        "local_absolute_paths": False,
        "local_mathjax_only": True,
        "penn_state": "CC BY-NC 4.0 except where otherwise noted",
        "mathjax_3_1_2": "Apache-2.0",
        "aggregate_uniform_relicense": False,
        "translation_provenance": PROVENANCE,
    }


def build_receipt_gate(reader: dict[str, object]) -> dict[str, object]:
    data = prior.load_json(BUILD_RECEIPT)
    if data.get("schema") != "o006.stat415.through-lesson02-build.v1" or data.get("status") != "built":
        raise RuntimeError("Lesson02 build receipt schema/status differs")
    if data.get("coverage") != {"complete_count": 4, "complete_documents": list(CONTENT), "corpus_document_count": 14, "next_document": "Lesson03"}:
        raise RuntimeError("Lesson02 build coverage differs")
    if data.get("translation_segments") != 1068 or data.get("structural_units_normalized") != 978 or data.get("math_nodes") != {"index": 0, "Lesson00": 331, "Lesson01": 169, "Lesson02": 209, "total": 709}:
        raise RuntimeError("Lesson02 build census differs")
    receipt_reader = data.get("reader")
    if not isinstance(receipt_reader, dict) or receipt_reader.get("path") != "build/html-id" or receipt_reader.get("files") != 31 or receipt_reader.get("bytes") != reader["bytes"] or receipt_reader.get("manifest_bytes") != reader["manifest_bytes"] or receipt_reader.get("manifest_sha256") != reader["manifest_sha256"]:
        raise RuntimeError("Lesson02 build reader identity differs")
    layout = data.get("layout")
    css_identity = prior.identity(BUILD / "assets" / "reader-4of14.css")
    if not isinstance(layout, dict) or layout.get("base_css_bytes") != 5890 or layout.get("base_css_sha256") != "1d463e04c51aff4750dec54523952488635c08fc5d3ead30ffc399a43f96f77b" or layout.get("reader_css_path") != "assets/reader-4of14.css" or layout.get("reader_css_bytes") != css_identity["bytes"] or layout.get("reader_css_sha256") != css_identity["sha256"]:
        raise RuntimeError("Lesson02 build reflow contract differs")
    for field, path in (("documents_backend", DOCUMENTS), ("corrections", CORRECTIONS)):
        record = data.get(field)
        actual = prior.identity(path)
        if not isinstance(record, dict) or record.get("path") != actual["path"] or record.get("bytes") != actual["bytes"] or record.get("sha256") != actual["sha256"]:
            raise RuntimeError(f"Lesson02 build backend identity differs: {field}")
    if data.get("locale") != "id-ID" or data.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("Lesson02 build locale/provenance differs")
    for name, (size, digest) in HISTORICAL.items():
        raw = prior.require_file(ROOT / name)
        if len(raw) != size or prior.sha256(raw) != digest or data.get("historical_lesson01_evidence", {}).get(name) != {"bytes": size, "sha256": digest}:
            raise RuntimeError(f"historical evidence changed: {name}")
    return prior.identity(BUILD_RECEIPT)


def compute() -> bytes:
    reader = reader_manifest_gate()
    pages, content_pages = load_pages()
    translation = translation_gate()
    normalization = normalization_gate()
    corrections_math = corrections_and_math_gate(content_pages)
    documents_language = document_and_language_gate(content_pages)
    links_assets = links_assets_gate(pages, content_pages)
    privacy_rights = privacy_runtime_rights_gate(pages)
    build_receipt = build_receipt_gate(reader)
    receipt = {
        "schema": "o006.stat415.through-lesson02-qa.v1",
        "status": "pass",
        "coverage": {"complete_documents": list(CONTENT), "complete_count": 4, "corpus_document_count": 14, "next_document": "Lesson03"},
        "locale": "id-ID",
        "reader": reader,
        "build_receipt": build_receipt,
        "translation": translation,
        "normalization": normalization,
        "structure_math_and_corrections": corrections_math,
        "documents_semantics_and_language": documents_language,
        "links_assets_and_reflow": links_assets,
        "privacy_runtime_rights_and_provenance": privacy_rights,
        "gates": [
            "exact-31-file-reader-and-manifest", "four-of-fourteen-document-coverage",
            "exact-1068-translated-segments-and-bindings", "exact-978-normalized-source-units",
            "exact-709-math-nodes", "exact-29-target-only-corrections-nine-for-lesson02",
            "exact-ten-lesson02-changed-math-surfaces", "preserved-historical-lesson01-evidence",
            "unique-stable-unit-math-and-dom-identities", "indonesian-semantics-terminology-and-alt-text",
            "all-local-links-fragments-assets-and-runtime", "two-frozen-rights-adjudicated-lesson02-pngs",
            "versioned-responsive-reader-css", "no-analytics-cookies-credentials-or-local-paths",
            "component-rights-and-exact-model-provenance",
        ],
    }
    return prior.canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payload = compute()
    if args.write:
        prior.atomic_write(QA_RECEIPT, payload)
        state = "written"
    else:
        if not QA_RECEIPT.is_file() or QA_RECEIPT.read_bytes() != payload:
            raise RuntimeError("Lesson02 cumulative QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({
        "mode": state,
        "status": data["status"],
        "documents": data["coverage"]["complete_count"],
        "reader_files": data["reader"]["files"],
        "reader_bytes": data["reader"]["bytes"],
        "math_nodes": data["structure_math_and_corrections"]["math_nodes"],
        "receipt_sha256": prior.sha256(payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
