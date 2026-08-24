#!/usr/bin/env python3
"""Deterministic cumulative QA for the id-ID STAT 415 reader through Lesson 01.

The verifier is intentionally independent of the builder.  ``--write`` emits
only the canonical QA receipt; ``--check-only`` recomputes every gate and
byte-compares that receipt.  Missing as well as extra reader surfaces fail.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON01_MANIFEST.csv"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON01_BUILD_RECEIPT.json"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON01_QA_RECEIPT.json"
DOCUMENTS = ROOT / "backend" / "through_lesson01_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson01_corrections.jsonl"
FIRST_CORRECTIONS = ROOT / "backend" / "first_unit_corrections.jsonl"
FIRST_TRANSLATIONS = ROOT / "source" / "id-ID" / "first_unit_translation.csv"
LESSON01_TRANSLATIONS = ROOT / "source" / "id-ID" / "lesson01_translation.csv"
LESSON01_SEGMENTS = ROOT / "working" / "lesson01_segments.csv"
LESSON01_TERMS = ROOT / "working" / "lesson01_terminology_candidates.csv"
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

CONTENT_DOCUMENTS = {
    "index": (PurePosixPath("index.html"), "O006-PSU-000", 0),
    "Lesson00": (PurePosixPath("Lesson00.html"), "O006-PSU-001", 331),
    "Lesson01": (PurePosixPath("Lesson01.html"), "O006-PSU-002", 169),
}
SOURCE_URLS = {
    "index": "https://online.stat.psu.edu/stat415/",
    "Lesson00": "https://online.stat.psu.edu/stat415/Lesson00",
    "Lesson01": "https://online.stat.psu.edu/stat415/Lesson01",
}
LESSON01_SVGS = {
    "STAT-415-SEC-3-18-09.svg",
    "stat-415-sec-3-18-10.svg",
    "stat-415-sec-3-18-11.svg",
    "stat-415-sec-3-18-12.svg",
    "STAT-415-SEC-3-18-13.svg",
}
EXPECTED_READER = {
    PurePosixPath("index.html"),
    PurePosixPath("Lesson00.html"),
    PurePosixPath("Lesson01.html"),
    PurePosixPath("assets/reader.css"),
    PurePosixPath("assets/MathJax/tex-svg.js"),
    PurePosixPath("assets/MathJax/input/tex/extensions/color.js"),
    PurePosixPath("assets/MathJax/input/tex/extensions/enclose.js"),
    PurePosixPath("assets/MathJax/input/tex/extensions/cancel.js"),
    PurePosixPath("licenses/index.html"),
    PurePosixPath("licenses/MathJax-3.1.2-LICENSE.txt"),
    *(PurePosixPath(f"assets/415lesson{i}thumb.png") for i in range(13)),
    *(PurePosixPath(f"assets/{name}") for name in LESSON01_SVGS),
}
REMOVED_STABLE_UNITS = {"O006-PSU-001-U0342", "O006-PSU-001-U0350"}
LESSON01_CORRECTIONS = {
    f"L01-D{i:03d}": f"O006-PSU-ADV-{i + 14:04d}" for i in range(1, 7)
}
EXPECTED_CORRECTION_IDS = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 21)}
EXPECTED_LESSON01_SEGMENTS = {
    f"O006-PSU-002-S{i:04d}" for i in range(1, 222)
}
EXPECTED_PARTITIONS = (
    ROOT / "working" / "lesson01_translation_part_a.json",
    ROOT / "working" / "lesson01_translation_part_b.json",
    ROOT / "working" / "lesson01_translation_part_c.json",
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def require_file(path: Path) -> bytes:
    if not path.is_file():
        raise RuntimeError(f"required file missing: {path.relative_to(ROOT).as_posix()}")
    return path.read_bytes()


def load_json(path: Path) -> dict[str, object]:
    raw = require_file(path)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"invalid UTF-8 JSON: {path.relative_to(ROOT).as_posix()}"
        ) from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON root is not an object: {path.relative_to(ROOT).as_posix()}")
    return value


def load_jsonl(path: Path) -> list[dict[str, object]]:
    raw = require_file(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            f"invalid UTF-8 JSONL: {path.relative_to(ROOT).as_posix()}"
        ) from exc
    rows: list[dict[str, object]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            raise RuntimeError(
                f"blank JSONL record: {path.relative_to(ROOT).as_posix()}:{number}"
            )
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"invalid JSONL record: {path.relative_to(ROOT).as_posix()}:{number}"
            ) from exc
        if not isinstance(row, dict):
            raise RuntimeError(
                f"JSONL record is not an object: {path.relative_to(ROOT).as_posix()}:{number}"
            )
        rows.append(row)
    return rows


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    raw = require_file(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(
            f"invalid UTF-8 CSV: {path.relative_to(ROOT).as_posix()}"
        ) from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        raise RuntimeError(f"invalid CSV header: {path.relative_to(ROOT).as_posix()}")
    rows = list(reader)
    if any(None in row for row in rows):
        raise RuntimeError(f"ragged CSV row: {path.relative_to(ROOT).as_posix()}")
    return list(reader.fieldnames), rows


def identity(path: Path) -> dict[str, object]:
    raw = require_file(path)
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(raw),
        "sha256": sha256(raw),
    }


def validate_identity_record(
    record: object, *, expected_path: str | None = None, label: str
) -> dict[str, object]:
    if not isinstance(record, dict):
        raise RuntimeError(f"{label} identity record missing")
    path_value = record.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise RuntimeError(f"{label} identity path missing")
    if expected_path is not None and path_value != expected_path:
        raise RuntimeError(f"{label} identity path differs")
    pure = PurePosixPath(path_value)
    if pure.is_absolute() or ".." in pure.parts:
        raise RuntimeError(f"{label} identity path is unsafe")
    path = ROOT / Path(pure.as_posix())
    actual = identity(path)
    if record.get("bytes") != actual["bytes"] or record.get("sha256") != actual["sha256"]:
        raise RuntimeError(f"{label} identity differs")
    return actual


def manifest_gate() -> tuple[list[dict[str, str]], dict[str, object]]:
    header, rows = load_csv(MANIFEST)
    if header != ["relative_path", "bytes", "sha256"]:
        raise RuntimeError("cumulative reader manifest header differs")
    if len(rows) != 28:
        raise RuntimeError("cumulative reader manifest must contain exactly 28 rows")
    paths: list[PurePosixPath] = []
    for row in rows:
        pure = PurePosixPath(row["relative_path"])
        if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != row["relative_path"]:
            raise RuntimeError(f"unsafe reader manifest path: {row['relative_path']}")
        paths.append(pure)
        try:
            byte_count = int(row["bytes"])
        except ValueError as exc:
            raise RuntimeError(f"invalid manifest byte count: {pure}") from exc
        if byte_count < 0 or not HEX64.fullmatch(row["sha256"]):
            raise RuntimeError(f"invalid manifest identity: {pure}")
        raw = require_file(BUILD / Path(pure.as_posix()))
        if len(raw) != byte_count or sha256(raw) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {pure}")
    if len(paths) != len(set(paths)) or set(paths) != EXPECTED_READER:
        raise RuntimeError("reader manifest has a missing, extra, or duplicate surface")
    actual_files = {
        PurePosixPath(path.relative_to(BUILD).as_posix())
        for path in BUILD.rglob("*")
        if path.is_file()
    }
    if actual_files != EXPECTED_READER:
        missing = sorted((EXPECTED_READER - actual_files), key=str)
        extra = sorted((actual_files - EXPECTED_READER), key=str)
        raise RuntimeError(f"reader tree differs; missing={missing}, extra={extra}")
    manifest_raw = require_file(MANIFEST)
    return rows, {
        "files": 28,
        "bytes": sum(int(row["bytes"]) for row in rows),
        "manifest_bytes": len(manifest_raw),
        "manifest_sha256": sha256(manifest_raw),
    }


def local_reference(
    owner: PurePosixPath, reference: str
) -> tuple[PurePosixPath, str | None] | None:
    parsed = urlparse(reference)
    if parsed.scheme or parsed.netloc or reference.startswith(("mailto:", "tel:")):
        return None
    if reference.startswith(("data:", "javascript:")):
        raise RuntimeError(f"unsafe local reference: {owner} -> {reference[:80]}")
    combined = owner if not parsed.path else owner.parent / PurePosixPath(parsed.path)
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
    return PurePosixPath(*parts), parsed.fragment or None


def link_gate(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    edges: list[dict[str, str]] = []
    external_anchors: list[dict[str, str]] = []
    all_reader_paths = {PurePosixPath(row) for row in EXPECTED_READER}
    for owner, soup in pages.items():
        for tag, attr in (
            ("a", "href"),
            ("link", "href"),
            ("script", "src"),
            ("img", "src"),
        ):
            for node in soup.select(f"{tag}[{attr}]"):
                reference = str(node.get(attr, ""))
                parsed = urlparse(reference)
                local = local_reference(owner, reference)
                if local is None:
                    if tag == "link" and "license" in (node.get("rel") or []):
                        external_anchors.append({"owner": owner.as_posix(), "href": reference})
                        continue
                    if tag != "a" and parsed.scheme in {"http", "https"}:
                        raise RuntimeError(
                            f"external executable or asset reference: {owner} -> {reference}"
                        )
                    if parsed.scheme not in {"http", "https", "mailto", "tel"}:
                        raise RuntimeError(f"unsupported reference scheme: {owner} -> {reference}")
                    if tag == "a":
                        external_anchors.append({"owner": owner.as_posix(), "href": reference})
                    continue
                resolved, fragment = local
                if resolved not in all_reader_paths:
                    raise RuntimeError(f"broken or unmanifested local reference: {owner} -> {reference}")
                candidate = BUILD / Path(resolved.as_posix())
                if not candidate.is_file():
                    raise RuntimeError(f"broken local reference: {owner} -> {reference}")
                if fragment and resolved.suffix.lower() in {".html", ".htm"}:
                    target = pages.get(resolved)
                    if target is None:
                        target = BeautifulSoup(candidate.read_bytes(), "html.parser")
                    if target.find(id=fragment) is None:
                        raise RuntimeError(f"broken local fragment: {owner} -> {reference}")
                edges.append(
                    {
                        "owner": owner.as_posix(),
                        "reference": reference,
                        "resolved": resolved.as_posix(),
                    }
                )
    edge_payload = canonical_json(
        sorted(edges, key=lambda row: (row["owner"], row["reference"], row["resolved"]))
    )
    return {
        "local_edges": len(edges),
        "local_edges_sha256": sha256(edge_payload),
        "external_anchor_edges": len(external_anchors),
        "all_local_targets_manifested": True,
        "all_local_fragments_resolve": True,
    }


def translation_gate() -> dict[str, object]:
    required = [
        "segment_id",
        "document_id",
        "component_id",
        "section_id",
        "source_sha256",
        "source_text",
        "target_text",
        "status",
    ]
    first_header, first = load_csv(FIRST_TRANSLATIONS)
    lesson_header, lesson = load_csv(LESSON01_TRANSLATIONS)
    if first_header != required or lesson_header != required:
        raise RuntimeError("translation CSV schema differs")
    if len(first) != 523 or len(lesson) != 221:
        raise RuntimeError("translation segment census differs from 523 + 221")
    combined = first + lesson
    ids = [row["segment_id"] for row in combined]
    if len(ids) != 744 or len(ids) != len(set(ids)):
        raise RuntimeError("cumulative translation IDs are missing or duplicated")
    if {row["segment_id"] for row in lesson} != EXPECTED_LESSON01_SEGMENTS:
        raise RuntimeError("Lesson01 translation ID set differs")
    for row in combined:
        if row["status"] != "translated" or not row["target_text"].strip():
            raise RuntimeError(f"translation incomplete: {row['segment_id']}")
        if not HEX64.fullmatch(row["source_sha256"]):
            raise RuntimeError(f"translation source hash malformed: {row['segment_id']}")
        if sha256(row["source_text"].encode("utf-8")) != row["source_sha256"]:
            raise RuntimeError(f"translation source hash differs: {row['segment_id']}")
        source = row["source_text"]
        target = row["target_text"]
        source_leading = source[: len(source) - len(source.lstrip())]
        source_trailing = source[len(source.rstrip()) :]
        target_leading = target[: len(target) - len(target.lstrip())]
        target_trailing = target[len(target.rstrip()) :]
        if source_leading != target_leading or source_trailing != target_trailing:
            raise RuntimeError(f"translation boundary whitespace differs: {row['segment_id']}")

    _, template = load_csv(LESSON01_SEGMENTS)
    if len(template) != 221 or {row["segment_id"] for row in template} != EXPECTED_LESSON01_SEGMENTS:
        raise RuntimeError("Lesson01 normalized segment template differs")
    template_by_id = {row["segment_id"]: row for row in template}
    for row in lesson:
        witness = template_by_id[row["segment_id"]]
        for field in (
            "document_id",
            "component_id",
            "section_id",
            "source_sha256",
            "source_text",
        ):
            if row[field] != witness[field]:
                raise RuntimeError(
                    f"Lesson01 translation/source binding differs: {row['segment_id']}:{field}"
                )

    partition_bindings: dict[str, str] = {}
    partition_counts: dict[str, int] = {}
    for path in EXPECTED_PARTITIONS:
        value = load_json(path)
        partition_counts[path.stem] = len(value)
        for key, target in value.items():
            if key in partition_bindings or key not in EXPECTED_LESSON01_SEGMENTS:
                raise RuntimeError(f"Lesson01 partition has duplicate/extra key: {key}")
            if not isinstance(target, str) or not target.strip():
                raise RuntimeError(f"Lesson01 partition target is empty: {key}")
            partition_bindings[key] = target
    if set(partition_bindings) != EXPECTED_LESSON01_SEGMENTS:
        raise RuntimeError("Lesson01 translation partitions do not close all 221 segments")
    for row in lesson:
        source = row["source_text"]
        source_leading = source[: len(source) - len(source.lstrip())]
        source_trailing = source[len(source.rstrip()) :]
        expected_target = (
            source_leading
            + partition_bindings[row["segment_id"]].strip()
            + source_trailing
        )
        if expected_target != row["target_text"]:
            raise RuntimeError(f"Lesson01 partition/CSV target differs: {row['segment_id']}")

    first_receipt = load_json(ROOT / "build" / "FIRST_UNIT_TRANSLATION_RECEIPT.json")
    if first_receipt.get("status") != "complete" or first_receipt.get("segment_count") != 523:
        raise RuntimeError("first-unit translation receipt differs")
    validate_identity_record(
        first_receipt.get("translation_csv"),
        expected_path="source/id-ID/first_unit_translation.csv",
        label="first-unit translation CSV",
    )
    return {
        "first_unit_segments": 523,
        "lesson01_segments": 221,
        "cumulative_segments": 744,
        "partition_counts": partition_counts,
        "lesson01_translation_csv": identity(LESSON01_TRANSLATIONS),
        "all_status_translated": True,
        "source_bindings_exact": True,
        "boundary_whitespace_preserved": True,
    }


def normalization_gate() -> dict[str, object]:
    first = load_json(ROOT / "build" / "FIRST_UNIT_NORMALIZATION_RECEIPT.json")
    lesson = load_json(ROOT / "build" / "LESSON01_NORMALIZATION_RECEIPT.json")
    if (
        first.get("status") != "normalized-source-ready"
        or first.get("document_count") != 2
        or first.get("segment_count") != 523
        or first.get("structure_count") != 562
    ):
        raise RuntimeError("first-unit normalization evidence differs")
    if lesson.get("status") != "normalized-source-ready" or lesson.get("source_defect_count") != 6:
        raise RuntimeError("Lesson01 normalization evidence differs")
    counts = lesson.get("counts")
    if not isinstance(counts, dict):
        raise RuntimeError("Lesson01 normalization counts missing")
    expected_counts = {
        "structural_units": 188,
        "translation_segments": 221,
        "math_nodes": 169,
        "math_inline": 135,
        "math_display": 34,
        "figures": 4,
        "images": 5,
        "solutions": 5,
        "proofs": 1,
        "examples": 3,
        "theorems": 1,
        "definitions": 1,
        "code_nodes": 0,
    }
    if any(counts.get(key) != value for key, value in expected_counts.items()):
        raise RuntimeError("Lesson01 normalization census differs")
    defects = lesson.get("source_defects")
    if not isinstance(defects, list) or len(defects) != 6:
        raise RuntimeError("Lesson01 source-defect evidence differs")
    defect_map = {
        row.get("defect_id"): row for row in defects if isinstance(row, dict)
    }
    if set(defect_map) != set(LESSON01_CORRECTIONS):
        raise RuntimeError("Lesson01 source-defect IDs differ")
    if defect_map["L01-D003"].get("occurrences") != 2:
        raise RuntimeError("Lesson01 two-example index defect census differs")
    outputs = lesson.get("outputs")
    if not isinstance(outputs, dict):
        raise RuntimeError("Lesson01 normalization output evidence missing")
    validate_identity_record(
        outputs.get("normalized"),
        expected_path="source/normalized/en-US/Lesson01.html",
        label="Lesson01 normalized HTML",
    )
    validate_identity_record(
        outputs.get("catalogue"),
        expected_path="backend/lesson01_source_catalogue.jsonl",
        label="Lesson01 source catalogue",
    )
    validate_identity_record(
        outputs.get("segments"),
        expected_path="working/lesson01_segments.csv",
        label="Lesson01 segment template",
    )
    return {
        "documents": 3,
        "structural_units": 750,
        "source_defects_registered": sorted(defect_map),
        "first_unit_receipt": identity(ROOT / "build" / "FIRST_UNIT_NORMALIZATION_RECEIPT.json"),
        "lesson01_receipt": identity(ROOT / "build" / "LESSON01_NORMALIZATION_RECEIPT.json"),
    }


def terminology_gate(lesson_soup: BeautifulSoup) -> dict[str, object]:
    header, rows = load_csv(LESSON01_TERMS)
    required = {
        "candidate_id",
        "en_US",
        "id_ID",
        "category",
        "glossary_status",
        "existing_term_id",
        "source_anchor",
        "decision",
    }
    if set(header) != required or len(rows) != 94:
        raise RuntimeError("Lesson01 terminology evidence schema/census differs")
    if len({row["candidate_id"] for row in rows}) != 94:
        raise RuntimeError("Lesson01 terminology candidate ID duplicated")
    actual = {row["en_US"]: row["id_ID"] for row in rows}
    expected = {
        "order statistics": "statistik urutan",
        "order statistic": "statistik urutan",
        "random variable": "peubah acak",
        "random sample": "sampel acak",
        "probability density function": "fungsi kepadatan peluang (PDF)",
        "cumulative distribution function": "fungsi distribusi kumulatif (CDF)",
    }
    if any(actual.get(term) != target for term, target in expected.items()):
        raise RuntimeError("controlling Lesson01 terminology decisions differ")
    order_row = next(row for row in rows if row["en_US"] == "order statistics")
    if (
        order_row["glossary_status"] != "primary-field-evidence override"
        or "10.24198/jmi.v21.n1.63667.123-130" not in order_row["decision"]
    ):
        raise RuntimeError("Indonesian field witness for statistik urutan is missing")
    visible = lesson_soup.get_text(" ", strip=True).casefold()
    for term in (
        "statistik urutan",
        "peubah acak",
        "sampel acak",
        "fungsi kepadatan peluang",
        "fungsi distribusi kumulatif",
    ):
        if term not in visible:
            raise RuntimeError(f"controlling Indonesian term absent from Lesson01: {term}")
    if "statistik terurut" in visible:
        raise RuntimeError("stale PSU term statistik terurut remains in Lesson01")
    return {
        "candidates": 94,
        "field_witness": "10.24198/jmi.v21.n1.63667.123-130",
        "controlling_order_statistics_term": "statistik urutan",
        "evidence": identity(LESSON01_TERMS),
    }


def correction_gate() -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = load_jsonl(CORRECTIONS)
    if len(rows) != 20:
        raise RuntimeError("cumulative correction backend must contain exactly 20 records")
    ids = [row.get("correction_id") for row in rows]
    if len(ids) != len(set(ids)) or set(ids) != EXPECTED_CORRECTION_IDS:
        raise RuntimeError("cumulative correction record ID set differs")
    first = load_jsonl(FIRST_CORRECTIONS)
    if len(first) != 14:
        raise RuntimeError("first-unit correction witness differs")
    cumulative_by_id = {str(row["correction_id"]): row for row in rows}
    for row in first:
        correction_id = str(row.get("correction_id"))
        if cumulative_by_id.get(correction_id) != row:
            raise RuntimeError(f"prior correction record changed: {correction_id}")
    lesson_rows = [row for row in rows if str(row.get("correction_id")) >= "O006-PSU-ADV-0015"]
    if len(lesson_rows) != 6:
        raise RuntimeError("Lesson01 must have exactly six cumulative correction records")
    by_defect: dict[str, dict[str, object]] = {}
    for row in lesson_rows:
        defect = row.get("source_defect_id")
        if not isinstance(defect, str) or defect in by_defect:
            raise RuntimeError("Lesson01 correction source-defect mapping differs")
        by_defect[defect] = row
    if set(by_defect) != set(LESSON01_CORRECTIONS):
        raise RuntimeError("Lesson01 correction source-defect set differs")
    for defect, correction_id in LESSON01_CORRECTIONS.items():
        row = by_defect[defect]
        expected_count = 2 if defect in {"L01-D003", "L01-D005"} else 1
        if (
            row.get("correction_id") != correction_id
            or row.get("replacement_count") != expected_count
            or row.get("status") != "applied-target-only"
            or not isinstance(row.get("surface"), str)
        ):
            raise RuntimeError(f"Lesson01 correction contract differs: {defect}")
    expected_surfaces = {
        "L01-D001": "html-id",
        "L01-D002": "math",
        "L01-D003": "math",
        "L01-D004": "math",
        "L01-D005": "html-alt",
        "L01-D006": "math",
    }
    if any(by_defect[key].get("surface") != value for key, value in expected_surfaces.items()):
        raise RuntimeError("Lesson01 correction surface classification differs")
    if any(not str(row.get("status", "")).startswith("applied") for row in rows):
        raise RuntimeError("cumulative correction backend contains an unapplied record")
    return rows, {
        "registered": 20,
        "applied": 20,
        "lesson01_registered": 6,
        "lesson01_ids": [LESSON01_CORRECTIONS[key] for key in sorted(LESSON01_CORRECTIONS)],
        "two_occurrence_exceptions": [
            "O006-PSU-ADV-0017",
            "O006-PSU-ADV-0019",
        ],
    }


def formula_and_unit_gate(
    content_pages: dict[str, BeautifulSoup], corrections: list[dict[str, object]]
) -> dict[str, object]:
    source_stable: list[str] = []
    target_stable: list[str] = []
    actual_differences: Counter[tuple[str, str, str]] = Counter()
    difference_rows: list[dict[str, object]] = []
    per_document: dict[str, dict[str, int]] = {}
    for component, (reader_path, _document_id, expected_math) in CONTENT_DOCUMENTS.items():
        source = BeautifulSoup(require_file(NORMALIZED / reader_path.name), "html.parser")
        target = content_pages[component]
        source_main = source.select_one("main#quarto-document-content")
        target_main = target.select_one("main#quarto-document-content")
        if source_main is None or target_main is None:
            raise RuntimeError(f"semantic main missing: {component}")
        source_ids = [str(node["data-o006-id"]) for node in source_main.select("[data-o006-id]")]
        target_ids = [str(node["data-o006-id"]) for node in target_main.select("[data-o006-id]")]
        if len(source_ids) != len(set(source_ids)) or len(target_ids) != len(set(target_ids)):
            raise RuntimeError(f"stable unit ID duplicated: {component}")
        source_stable.extend(source_ids)
        target_stable.extend(target_ids)
        source_math_nodes = source_main.select(".math")
        target_math_nodes = target_main.select(".math")
        if len(source_math_nodes) != expected_math or len(target_math_nodes) != expected_math:
            raise RuntimeError(f"math-node census differs: {component}")
        source_math_ids = [str(node.get("data-o006-math-id", "")) for node in source_math_nodes]
        target_math_ids = [str(node.get("data-o006-math-id", "")) for node in target_math_nodes]
        if component == "Lesson00":
            expected_target_math_ids = [
                f"O006-PSU-001-M{i:04d}" for i in range(1, expected_math + 1)
            ]
            if any(source_math_ids) or target_math_ids != expected_target_math_ids:
                raise RuntimeError("Lesson00 additive formula stable-ID topology differs")
        elif source_math_ids != target_math_ids or (
            source_math_ids and len(source_math_ids) != len(set(source_math_ids))
        ):
            raise RuntimeError(f"formula stable-ID topology differs: {component}")
        for math_id, before_node, after_node in zip(
            source_math_ids, source_math_nodes, target_math_nodes
        ):
            before = before_node.get_text()
            after = after_node.get_text()
            if before != after:
                before_hash = sha256(before.encode("utf-8"))
                after_hash = sha256(after.encode("utf-8"))
                actual_differences[(reader_path.as_posix(), before_hash, after_hash)] += 1
                difference_rows.append(
                    {
                        "document": reader_path.as_posix(),
                        "math_id": math_id,
                        "source_sha256": before_hash,
                        "target_sha256": after_hash,
                    }
                )
        per_document[component] = {
            "source_stable_units": len(source_ids),
            "target_stable_units": len(target_ids),
            "math_nodes": len(target_math_nodes),
        }
    if len(source_stable) != 750 or len(set(source_stable)) != 750:
        raise RuntimeError("normalized cumulative stable-unit census differs")
    if len(target_stable) != 748 or len(set(target_stable)) != 748:
        raise RuntimeError("target cumulative stable-unit census differs")
    if set(source_stable) - set(target_stable) != REMOVED_STABLE_UNITS:
        raise RuntimeError("target stable-unit removal differs from registered correction")
    if set(target_stable) - set(source_stable):
        raise RuntimeError("unregistered target stable unit introduced")

    expected_differences: Counter[tuple[str, str, str]] = Counter()
    for row in corrections:
        if row.get("surface") != "math":
            continue
        number = int(str(row["correction_id"]).rsplit("-", 1)[1])
        document = "Lesson00.html" if number <= 14 else "Lesson01.html"
        surfaces = row.get("surfaces")
        if surfaces is None:
            surfaces = [row]
        if not isinstance(surfaces, list) or len(surfaces) != row.get("replacement_count"):
            raise RuntimeError(f"formula correction occurrence evidence differs: {row.get('correction_id')}")
        for surface in surfaces:
            if not isinstance(surface, dict):
                raise RuntimeError(f"formula correction surface malformed: {row.get('correction_id')}")
            source_hash = surface.get("source_surface_sha256")
            target_hash = surface.get("target_surface_sha256")
            if (
                not isinstance(source_hash, str)
                or not HEX64.fullmatch(source_hash)
                or not isinstance(target_hash, str)
                or not HEX64.fullmatch(target_hash)
            ):
                raise RuntimeError(f"formula correction evidence incomplete: {row.get('correction_id')}")
            expected_differences[(document, source_hash, target_hash)] += 1
    if actual_differences != expected_differences:
        raise RuntimeError("formula changes differ from exact registered target-only corrections")
    if len(difference_rows) != 13:
        raise RuntimeError("cumulative formula-difference occurrence census differs")
    if sum(row["math_nodes"] for row in per_document.values()) != 500:
        raise RuntimeError("cumulative math-node total differs")
    return {
        "source_stable_units": 750,
        "target_stable_units": 748,
        "removed_stable_units": sorted(REMOVED_STABLE_UNITS),
        "math_nodes": 500,
        "registered_formula_difference_occurrences": 13,
        "formula_differences": sorted(
            difference_rows, key=lambda row: (str(row["document"]), str(row["math_id"]))
        ),
        "per_document": per_document,
    }


def document_backend_gate(
    content_pages: dict[str, BeautifulSoup]
) -> dict[str, object]:
    rows = load_jsonl(DOCUMENTS)
    if len(rows) != 3:
        raise RuntimeError("cumulative document backend must contain exactly three records")
    by_component = {row.get("component_id"): row for row in rows}
    if len(by_component) != 3 or set(by_component) != set(CONTENT_DOCUMENTS):
        raise RuntimeError("cumulative document backend coverage differs")
    for component, (reader_path, document_id, expected_math) in CONTENT_DOCUMENTS.items():
        row = by_component[component]
        target_path = f"source/id-ID/{reader_path.name}"
        source_path = f"source/normalized/en-US/{reader_path.name}"
        if (
            row.get("schema") != "o006.stat415.document.v1"
            or row.get("document_id") != document_id
            or row.get("locale") != "id-ID"
            or row.get("translation_status") != "complete"
            or row.get("math_nodes") != expected_math
            or row.get("source_path") != source_path
            or row.get("target_path") != target_path
            or row.get("source_url") != SOURCE_URLS[component]
        ):
            raise RuntimeError(f"cumulative document record differs: {component}")
        target_raw = require_file(ROOT / target_path)
        build_raw = require_file(BUILD / Path(reader_path.as_posix()))
        if target_raw != build_raw:
            raise RuntimeError(f"source target and reader bytes differ: {component}")
        if row.get("target_bytes") != len(target_raw) or row.get("target_sha256") != sha256(target_raw):
            raise RuntimeError(f"document target identity differs: {component}")
        source = BeautifulSoup(require_file(ROOT / source_path), "html.parser")
        target = content_pages[component]
        source_main = source.select_one("main#quarto-document-content")
        target_main = target.select_one("main#quarto-document-content")
        if source_main is None or target_main is None:
            raise RuntimeError(f"document semantic main missing: {component}")
        source_math = [node.get_text() for node in source_main.select(".math")]
        target_math = [node.get_text() for node in target_main.select(".math")]
        if row.get("source_math_sha256") != sha256("\n".join(source_math).encode("utf-8")):
            raise RuntimeError(f"document source-math identity differs: {component}")
        if row.get("target_math_sha256") != sha256("\n".join(target_math).encode("utf-8")):
            raise RuntimeError(f"document target-math identity differs: {component}")
    return {
        "complete": 3,
        "corpus_documents": 14,
        "components": ["index", "Lesson00", "Lesson01"],
        "backend": identity(DOCUMENTS),
    }


def lesson_index_from_href(href: str) -> int | None:
    parsed = urlparse(href)
    match = re.fullmatch(r"/stat415/Lesson(\d{2})(?:\.html)?/?", parsed.path)
    return int(match.group(1)) if match else None


def semantic_gate(content_pages: dict[str, BeautifulSoup]) -> dict[str, object]:
    for component, soup in content_pages.items():
        path = CONTENT_DOCUMENTS[component][0]
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"id-ID document language missing: {component}")
        if "\ufffd" in str(soup):
            raise RuntimeError(f"Unicode replacement character present: {component}")
        ids = [str(node["id"]) for node in soup.select("[id]")]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"duplicate target DOM ID: {component}")
        meta_source = soup.select_one('meta[name="source-url"]')
        meta_provenance = soup.select_one('meta[name="translation-provenance"]')
        meta_status = soup.select_one('meta[name="edition-status"]')
        if (
            meta_source is None
            or meta_source.get("content") != SOURCE_URLS[component]
            or meta_provenance is None
            or meta_provenance.get("content") != PROVENANCE
            or meta_status is None
            or "3" not in str(meta_status.get("content", ""))
            or "14" not in str(meta_status.get("content", ""))
        ):
            raise RuntimeError(f"id-ID metadata differs: {component}")
        if soup.select_one('link[rel~="license"][href="https://creativecommons.org/licenses/by-nc/4.0/"]') is None:
            raise RuntimeError(f"content licence metadata missing: {component}")
        main = soup.select_one("main#quarto-document-content")
        if main is None or main.get("data-component-id") != component:
            raise RuntimeError(f"reader semantic main/component differs: {component}")
        if soup.select_one('a.skip-link[href="#quarto-document-content"]') is None:
            raise RuntimeError(f"skip link missing: {component}")
        if soup.select_one("header.site-header") is None or soup.select_one("footer.site-footer") is None:
            raise RuntimeError(f"reader chrome missing: {component}")
        if not soup.title or not soup.title.get_text(strip=True):
            raise RuntimeError(f"reader title missing: {component}")
        expected_path = path.as_posix()
        if component != "index" and not soup.select(f'a[href="{expected_path}"]'):
            raise RuntimeError(f"self/navigation route missing: {component}")

    index = content_pages["index"]
    local_lessons = {
        int(match.group(1))
        for anchor in index.select("main a[href]")
        if (match := re.fullmatch(r"(?:\./)?Lesson(\d{2})\.html(?:#.*)?", str(anchor["href"])))
    }
    if local_lessons != {0, 1}:
        raise RuntimeError("landing local Lesson00/Lesson01 topology differs")
    if len(index.select('main a[href="Lesson00.html"], main a[href="./Lesson00.html"]')) != 1:
        raise RuntimeError("landing Lesson00 local route differs")
    if len(index.select('main a[href="Lesson01.html"], main a[href="./Lesson01.html"]')) != 1:
        raise RuntimeError("landing Lesson01 local route differs")
    pending = index.select("main a.pending-source[data-translation-status='pending']")
    pending_lessons = [lesson_index_from_href(str(anchor.get("href", ""))) for anchor in pending]
    if len(pending) != 11 or set(pending_lessons) != set(range(2, 13)) or None in pending_lessons:
        raise RuntimeError("landing external pending Lesson02-Lesson12 topology differs")
    if any(urlparse(str(anchor["href"])).netloc != "online.stat.psu.edu" for anchor in pending):
        raise RuntimeError("pending lessons do not route to the official host")
    landing_images = index.select("main img[src]")
    if len(landing_images) != 13 or any(not image.get("alt", "").strip() for image in landing_images):
        raise RuntimeError("landing image/alt-text census differs")

    lesson = content_pages["Lesson01"]
    if len(lesson.select(".theorem.example")) != 3:
        raise RuntimeError("Lesson01 example count differs")
    if len(lesson.select(".theorem.definition")) != 1:
        raise RuntimeError("Lesson01 definition count differs")
    if len(lesson.select(".theorem")) != 5:
        raise RuntimeError("Lesson01 theorem-class census differs")
    proof_sections = lesson.select("section#proof")
    if len(proof_sections) != 1:
        raise RuntimeError("Lesson01 proof count differs")
    solution_titles = [
        node
        for node in lesson.select("h1, h2, h3, h4, h5, h6, summary")
        if node.get_text(" ", strip=True) == "Penyelesaian"
    ]
    if len(solution_titles) != 5:
        raise RuntimeError("Lesson01 must retain exactly five Indonesian Solution headings")
    theorem_titles = [node.get_text(" ", strip=True) for node in lesson.select(".theorem-title strong")]
    if sum(title.startswith("Contoh ") for title in theorem_titles) != 3:
        raise RuntimeError("Lesson01 Indonesian Example labels differ")
    if sum(title.startswith(("Def. ", "Definisi ")) for title in theorem_titles) != 1:
        raise RuntimeError("Lesson01 Indonesian Definition label differs")
    if sum(title.startswith("Teorema ") for title in theorem_titles) != 1:
        raise RuntimeError("Lesson01 Indonesian Theorem label differs")
    proof_heading = proof_sections[0].find(["h2", "h3", "h4", "h5", "h6"])
    if proof_heading is None or proof_heading.get_text(" ", strip=True).rstrip(".:") != "Bukti":
        raise RuntimeError("Lesson01 Indonesian Proof label missing")
    if lesson.select("button, .collapse, [data-bs-toggle], [data-bs-target]"):
        raise RuntimeError("Bootstrap-dependent Lesson01 controls remain")
    if len(lesson.select("figure")) != 4 or len(lesson.select("main img[src]")) != 5:
        raise RuntimeError("Lesson01 figure/image census differs")
    english_heading_labels = {
        "Overview",
        "Objectives",
        "The Basics",
        "Probability Density Functions",
        "Distribution Functions",
        "Summary",
        "Solution",
        "Proof",
    }
    if any(
        node.get_text(" ", strip=True) in english_heading_labels
        for node in lesson.select("h1, h2, h3, h4, h5, h6, summary")
    ):
        raise RuntimeError("untranslated English Lesson01 heading remains")
    return {
        "html_lang": "id-ID",
        "content_documents": 3,
        "landing_local_lessons": [0, 1],
        "landing_pending_official_lessons": list(range(2, 13)),
        "landing_images_with_alt": 13,
        "lesson01": {
            "solutions": 5,
            "proofs": 1,
            "examples": 3,
            "theorems": 1,
            "definitions": 1,
            "figures": 4,
            "images_with_alt": 5,
        },
        "target_dom_ids_unique": True,
        "reader_chrome_present": True,
    }


def asset_gate(
    content_pages: dict[str, BeautifulSoup], corrections: list[dict[str, object]]
) -> dict[str, object]:
    first_receipt = load_json(ROOT / "authority" / "FIRST_UNIT_ASSET_RECEIPT.json")
    if first_receipt.get("status") != "frozen" or first_receipt.get("asset_count") != 13:
        raise RuntimeError("first-unit asset freeze evidence differs")
    validate_identity_record(
        first_receipt.get("manifest"),
        expected_path="authority/FIRST_UNIT_ASSET_MANIFEST.csv",
        label="first-unit asset manifest",
    )
    _, asset_rows = load_csv(ROOT / "authority" / "FIRST_UNIT_ASSET_MANIFEST.csv")
    if len(asset_rows) != 13:
        raise RuntimeError("first-unit asset manifest census differs")
    for row in asset_rows:
        relative = PurePosixPath(row["relative_path"])
        source = ROOT / "authority" / "assets" / "stat415" / Path(relative.as_posix())
        target = BUILD / Path(relative.as_posix())
        source_raw = require_file(source)
        target_raw = require_file(target)
        if (
            source_raw != target_raw
            or int(row["bytes"]) != len(source_raw)
            or row["sha256"] != sha256(source_raw)
        ):
            raise RuntimeError(f"frozen course-card asset identity differs: {relative}")

    source_lesson = BeautifulSoup(require_file(NORMALIZED / "Lesson01.html"), "html.parser")
    source_images = source_lesson.select("main img[src]")
    target_images = content_pages["Lesson01"].select("main img[src]")
    source_names = [PurePosixPath(str(node["src"])).name for node in source_images]
    target_names = [PurePosixPath(str(node["src"])).name for node in target_images]
    if len(source_names) != 5 or Counter(source_names) != Counter(target_names):
        raise RuntimeError("Lesson01 image topology differs")
    if set(source_names) != LESSON01_SVGS or any(not node.get("alt", "").strip() for node in target_images):
        raise RuntimeError("Lesson01 image/alt-text closure differs")
    for name in LESSON01_SVGS:
        source_path = ROOT / "authority" / "assets" / "stat415" / "lesson01" / name
        target_path = BUILD / "assets" / name
        source_raw = require_file(source_path)
        target_raw = require_file(target_path)
        if source_raw != target_raw:
            raise RuntimeError(f"Lesson01 SVG bytes differ from frozen authority: {name}")
        lower = target_raw.lower()
        if b"<!doctype" in lower or b"<!entity" in lower:
            raise RuntimeError(f"unsafe SVG declaration: {name}")
        try:
            root = ET.fromstring(target_raw)
        except ET.ParseError as exc:
            raise RuntimeError(f"invalid SVG XML: {name}") from exc
        if root.tag.rsplit("}", 1)[-1].lower() != "svg":
            raise RuntimeError(f"SVG root differs: {name}")
        for node in root.iter():
            local_tag = node.tag.rsplit("}", 1)[-1].lower()
            if local_tag in {"script", "foreignobject", "iframe", "object", "embed"}:
                raise RuntimeError(f"unsafe SVG element: {name}:{local_tag}")
            for attr, value in node.attrib.items():
                local_attr = attr.rsplit("}", 1)[-1].lower()
                if local_attr.startswith("on"):
                    raise RuntimeError(f"unsafe SVG event attribute: {name}:{local_attr}")
                if local_attr == "href" and not str(value).startswith("#"):
                    raise RuntimeError(f"unsafe SVG external reference: {name}:{value}")

    by_id = {str(row.get("correction_id")): row for row in corrections}
    alt_record = by_id["O006-PSU-ADV-0019"]
    alt_surfaces = alt_record.get("surfaces")
    if not isinstance(alt_surfaces, list) or len(alt_surfaces) != 2:
        raise RuntimeError("Lesson01 image-description correction evidence incomplete")
    actions = {surface.get("action") for surface in alt_surfaces if isinstance(surface, dict)}
    if actions != {"remove-nonsemantic-wrapper-alt", "replace-image-alt"}:
        raise RuntimeError("Lesson01 image-description correction actions differ")
    stale_alt = "Celsius vs Fahrenheit scatterplot"
    target_alt = (
        "Garis bilangan yang menunjukkan lima nilai kurang dari satu "
        "dan satu nilai tidak kurang dari satu."
    )
    source_alt_count = sum(node.get("alt") == stale_alt for node in source_images)
    target_alt_count = sum(node.get("alt") == target_alt for node in target_images)
    wrapper = content_pages["Lesson01"].select_one('[data-o006-id="O006-PSU-002-U0057"]')
    if source_alt_count != 1 or target_alt_count != 1 or wrapper is None or wrapper.has_attr("alt"):
        raise RuntimeError("Lesson01 image-description correction not applied to both surfaces")
    return {
        "course_card_pngs": 13,
        "lesson01_svgs": 5,
        "lesson01_svg_names": sorted(LESSON01_SVGS),
        "all_assets_byte_identical_to_authority": True,
        "all_svg_surfaces_safe": True,
        "all_reader_images_have_alt": True,
    }


def privacy_runtime_gate(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    forbidden_markup = (
        "google-analytics",
        "googletagmanager",
        "gtag(",
        "matomo",
        "plausible.io",
        "hotjar",
        "clarity.ms",
        "segment.io",
        "document.cookie",
        "cookieconsent",
        "onetrust",
    )
    credential_patterns = (
        re.compile(r"github\s+tokens?\.md", re.I),
        re.compile(r"zenodo\s+token", re.I),
        re.compile(r"figshare\s+token", re.I),
        re.compile(r"(?:api|access)[_-]?token", re.I),
        re.compile(r"api[_-]?key", re.I),
        re.compile(r"authorization\s*:\s*bearer", re.I),
    )
    absolute_patterns = (
        re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]"),
        re.compile(r"file://", re.I),
        re.compile(r"(?:^|[\"'\s])/(?:Users|home|tmp)/", re.I),
    )
    scan_paths = [
        path
        for path in EXPECTED_READER
        if path.suffix.lower() in {".html", ".css", ".svg"}
    ]
    for relative in scan_paths:
        raw = require_file(BUILD / Path(relative.as_posix()))
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RuntimeError(f"reader text asset is not UTF-8: {relative}") from exc
        lower = text.casefold()
        if any(marker in lower for marker in forbidden_markup):
            raise RuntimeError(f"analytics/cookie marker present: {relative}")
        if any(pattern.search(text) for pattern in credential_patterns):
            raise RuntimeError(f"credential marker present: {relative}")
        if any(pattern.search(text) for pattern in absolute_patterns):
            raise RuntimeError(f"local absolute path present: {relative}")

    for owner, soup in pages.items():
        if soup.select("iframe, object, embed"):
            raise RuntimeError(f"external-capable embedded object present: {owner}")
        for node in soup.find_all(True):
            if any(str(attr).lower().startswith("on") for attr in node.attrs):
                raise RuntimeError(f"inline event handler present: {owner}")
        scripts = soup.select("script")
        expected_scripts = 1 if owner in {PurePosixPath("Lesson00.html"), PurePosixPath("Lesson01.html")} else 0
        if len(scripts) != expected_scripts:
            raise RuntimeError(f"reader script census differs: {owner}")
        for script in scripts:
            if script.get("src") != "assets/MathJax/tex-svg.js" or script.get_text(strip=True):
                raise RuntimeError(f"nonlocal or inline script present: {owner}")
        for link in soup.select('link[rel~="stylesheet"]'):
            href = str(link.get("href", ""))
            if local_reference(owner, href) is None:
                raise RuntimeError(f"external stylesheet present: {owner}")
    runtime = require_file(BUILD / "assets" / "MathJax" / "tex-svg.js")
    authority_runtime = require_file(
        ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "tex-svg.js"
    )
    if runtime != authority_runtime:
        raise RuntimeError("local MathJax runtime differs from frozen authority")
    runtime_color = require_file(
        BUILD / "assets" / "MathJax" / "input" / "tex" / "extensions" / "color.js"
    )
    authority_color = require_file(
        ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "input" / "tex" / "extensions" / "color.js"
    )
    if runtime_color != authority_color:
        raise RuntimeError("local MathJax color extension differs from frozen authority")
    for extension in ("enclose.js", "cancel.js"):
        runtime_extension = require_file(
            BUILD / "assets" / "MathJax" / "input" / "tex" / "extensions" / extension
        )
        authority_extension = require_file(
            ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "input" / "tex" / "extensions" / extension
        )
        if runtime_extension != authority_extension:
            raise RuntimeError(f"local MathJax {extension} differs from frozen authority")
    runtime_license = require_file(BUILD / "licenses" / "MathJax-3.1.2-LICENSE.txt")
    authority_license = require_file(
        ROOT / "authority" / "runtime" / "MathJax-3.1.2" / "LICENSE.txt"
    )
    if runtime_license != authority_license:
        raise RuntimeError("MathJax license bytes differ from frozen authority")
    return {
        "external_runtime_requests": 0,
        "inline_scripts": 0,
        "analytics": False,
        "cookies": False,
        "credential_paths": False,
        "local_absolute_paths": False,
        "local_mathjax_only": True,
    }


def rights_gate(pages: dict[PurePosixPath, BeautifulSoup]) -> dict[str, object]:
    license_page = pages[PurePosixPath("licenses/index.html")]
    if license_page.html is None or license_page.html.get("lang") != "id-ID":
        raise RuntimeError("licence-page id-ID metadata missing")
    text = license_page.get_text(" ", strip=True)
    required_fragments = (
        "Penn State",
        "CC BY-NC 4.0",
        "kecuali dinyatakan lain",
        "MathJax 3.1.2",
        "Apache License 2.0",
        PROVENANCE,
        "tidak resmi",
    )
    if any(fragment not in text for fragment in required_fragments):
        raise RuntimeError("rights/provenance statement is incomplete")
    if license_page.select_one(
        'a[rel~="license"][href="https://creativecommons.org/licenses/by-nc/4.0/"]'
    ) is None:
        raise RuntimeError("Penn State licence link missing from rights page")
    if license_page.select_one('a[href="MathJax-3.1.2-LICENSE.txt"]') is None:
        raise RuntimeError("MathJax licence route missing from rights page")
    footer_text = " ".join(
        page.get_text(" ", strip=True) for page in pages.values()
    ).casefold()
    if "tidak ada relisensi seragam" not in footer_text:
        raise RuntimeError("component-separated no-uniform-relicense notice missing")
    return {
        "penn_state": "CC BY-NC 4.0 except where otherwise noted",
        "mathjax_3_1_2": "Apache-2.0",
        "aggregate_uniform_relicense": False,
        "translation_provenance": PROVENANCE,
        "source_and_human_credits_preserved": True,
    }


def build_receipt_gate(
    reader: dict[str, object], corrections_identity: dict[str, object], documents_identity: dict[str, object]
) -> dict[str, object]:
    data = load_json(BUILD_RECEIPT)
    if data.get("schema") != "o006.stat415.through-lesson01-build.v1" or data.get("status") != "built":
        raise RuntimeError("cumulative build receipt schema/status differs")
    coverage = data.get("coverage")
    if not isinstance(coverage, dict) or (
        coverage.get("complete_count") != 3
        or coverage.get("complete_documents") != ["index", "Lesson00", "Lesson01"]
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson02"
    ):
        raise RuntimeError("cumulative build receipt coverage differs")
    math = data.get("math_nodes")
    if not isinstance(math, dict) or (
        math.get("index") != 0
        or math.get("Lesson00") != 331
        or math.get("Lesson01") != 169
        or math.get("total") != 500
    ):
        raise RuntimeError("cumulative build receipt math census differs")
    if data.get("translation_segments") != 744:
        raise RuntimeError("cumulative build receipt translation census differs")
    receipt_reader = data.get("reader")
    if not isinstance(receipt_reader, dict) or (
        receipt_reader.get("path") != "build/html-id"
        or receipt_reader.get("files") != 28
        or receipt_reader.get("bytes") != reader["bytes"]
        or receipt_reader.get("manifest_path") != "build/THROUGH_LESSON01_MANIFEST.csv"
        or receipt_reader.get("manifest_bytes") != reader["manifest_bytes"]
        or receipt_reader.get("manifest_sha256") != reader["manifest_sha256"]
    ):
        raise RuntimeError("cumulative build receipt reader identity differs")
    receipt_corrections = data.get("corrections")
    if not isinstance(receipt_corrections, dict) or (
        receipt_corrections.get("count") != 20
        or receipt_corrections.get("lesson01_count") != 6
        or receipt_corrections.get("path") != corrections_identity["path"]
        or receipt_corrections.get("bytes") != corrections_identity["bytes"]
        or receipt_corrections.get("sha256") != corrections_identity["sha256"]
    ):
        raise RuntimeError("cumulative build receipt correction identity differs")
    receipt_documents = data.get("documents_backend")
    if not isinstance(receipt_documents, dict) or (
        receipt_documents.get("path") != documents_identity["path"]
        or receipt_documents.get("bytes") != documents_identity["bytes"]
        or receipt_documents.get("sha256") != documents_identity["sha256"]
    ):
        raise RuntimeError("cumulative build receipt document-backend identity differs")
    rights = data.get("rights")
    offline = data.get("offline")
    if not isinstance(rights, dict) or (
        rights.get("Penn State content") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("MathJax 3.1.2") != "Apache-2.0"
        or rights.get("aggregate_uniform_relicense") is not False
    ):
        raise RuntimeError("cumulative build receipt rights statement differs")
    if not isinstance(offline, dict) or (
        offline.get("external_runtime_requests") != 0
        or offline.get("analytics") is not False
        or offline.get("cookies") is not False
        or offline.get("local_mathjax") is not True
    ):
        raise RuntimeError("cumulative build receipt offline statement differs")
    if data.get("locale") != "id-ID" or data.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("cumulative build receipt locale/provenance differs")
    return identity(BUILD_RECEIPT)


def compute() -> bytes:
    _manifest_rows, reader = manifest_gate()
    all_page_paths = (
        PurePosixPath("index.html"),
        PurePosixPath("Lesson00.html"),
        PurePosixPath("Lesson01.html"),
        PurePosixPath("licenses/index.html"),
    )
    pages = {
        path: BeautifulSoup(require_file(BUILD / Path(path.as_posix())), "html.parser")
        for path in all_page_paths
    }
    content_pages = {
        component: pages[path]
        for component, (path, _document_id, _math) in CONTENT_DOCUMENTS.items()
    }
    translations = translation_gate()
    normalization = normalization_gate()
    correction_rows, correction_summary = correction_gate()
    formulas_units = formula_and_unit_gate(content_pages, correction_rows)
    documents = document_backend_gate(content_pages)
    semantics = semantic_gate(content_pages)
    terminology = terminology_gate(content_pages["Lesson01"])
    assets = asset_gate(content_pages, correction_rows)
    links = link_gate(pages)
    privacy_runtime = privacy_runtime_gate(pages)
    rights = rights_gate(pages)
    build_receipt = build_receipt_gate(
        reader, identity(CORRECTIONS), identity(DOCUMENTS)
    )
    receipt = {
        "schema": "o006.stat415.through-lesson01-qa.v1",
        "status": "pass",
        "coverage": {
            "complete_documents": ["index", "Lesson00", "Lesson01"],
            "complete_count": 3,
            "corpus_document_count": 14,
            "next_document": "Lesson02",
        },
        "locale": "id-ID",
        "reader": reader,
        "build_receipt": build_receipt,
        "documents": documents,
        "normalization": normalization,
        "translation": translations,
        "structure_and_math": formulas_units,
        "corrections": correction_summary,
        "semantics_and_language": semantics,
        "terminology": terminology,
        "assets": assets,
        "links": links,
        "privacy_and_runtime": privacy_runtime,
        "rights_and_provenance": rights,
        "gates": [
            "exact-28-file-reader-surface",
            "manifest-byte-and-sha256-identities",
            "three-of-fourteen-document-coverage",
            "exact-744-translated-segments",
            "normalization-and-partition-bindings",
            "exact-750-source-and-748-target-stable-units",
            "exact-500-math-nodes",
            "registered-target-only-formula-corrections",
            "exact-twenty-correction-records-six-for-lesson01",
            "unique-stable-math-and-dom-ids",
            "local-links-and-fragments",
            "local-lesson01-and-external-pending-lesson02-through-12",
            "five-frozen-safe-svg-assets",
            "indonesian-semantics-and-field-terminology",
            "rights-and-exact-model-provenance",
            "offline-local-runtime-no-analytics-cookies-credentials-or-local-paths",
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
            raise RuntimeError("cumulative QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": state,
                "status": data["status"],
                "documents": data["coverage"]["complete_count"],
                "reader_files": data["reader"]["files"],
                "reader_bytes": data["reader"]["bytes"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
