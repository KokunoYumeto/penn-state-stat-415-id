#!/usr/bin/env python3
"""Build the original C140 companion with deterministic, browser-free tooling."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import html
import io
import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent.parent
SOURCE = ROOT / "source" / "id-ID"
GENERATED_BATCHES = {
    "c1": ROOT / "generated" / "simulations" / "c1",
    "c2": ROOT / "generated" / "simulations" / "c2",
    "c3": ROOT / "generated" / "simulations" / "c3",
}
SIMULATION_RECEIPTS = {
    "c1": ROOT / "build" / "C1_SIMULATION_RECEIPT.json",
    "c2": ROOT / "build" / "C2_SIMULATION_RECEIPT.json",
    "c3": ROOT / "build" / "C3_SIMULATION_RECEIPT.json",
}
HTML_TARGET = ROOT / "build" / "html-id"
BACKEND_TARGET = ROOT / "backend"
RECEIPT_TARGET = ROOT / "build" / "C3_BUILD_RECEIPT.json"
ENVIRONMENT_LOCK = ROOT / "environment.lock.json"
ACTIVE_BOUNDARY = "c3"
MATHJAX_SOURCE = REPO / "build" / "html-id" / "assets" / "MathJax"
MATHJAX_LICENSE = REPO / "build" / "html-id" / "licenses" / "MathJax-3.1.2-LICENSE.txt"
COMPANION_LICENSE = "CC-BY-SA-4.0"
RANDOM_DONOR_TARGET = (
    REPO
    / "components"
    / "random-completeness"
    / "source"
    / "id-ID"
    / "random"
    / "point"
    / "Sufficient.html"
)
RANDOM_DONOR_TARGET_BYTES = 60_900
RANDOM_DONOR_TARGET_SHA256 = (
    "18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197"
)
RANDOM_DONOR_PUBLIC_PAGE = (
    "https://kokunoyumeto.github.io/penn-state-stat-415-id/"
    "components/random-completeness/random/point/Sufficient.html"
)
# Only these donor entities are referenced by the original C140 companion.
# Labels are deliberately reader-facing id-ID strings: the imported registry
# records source_text in English and does not currently carry target_text.
RANDOM_DONOR_REFERENCE_TARGETS: dict[str, tuple[str | None, str]] = {
    "O006-016-00-0001": (None, "Statistik Cukup, Lengkap, dan Ancillary"),
    "O006-016-02-0001": ("suf1", "Definisi statistik cukup"),
    "O006-016-02-0003": ("fac", "Teorema faktorisasi Fisher–Neyman"),
    "O006-016-02-0010": ("rbt", "Teorema Rao–Blackwell"),
    "O006-016-02-0011": (
        "o006.random.point.sufficient.unit-11",
        "Definisi statistik lengkap",
    ),
    "O006-016-02-0013": ("lst", "Teorema Lehmann–Scheffé"),
    "O006-016-02-0014": (
        "o006.random.point.sufficient.unit-14",
        "Definisi statistik ancillary",
    ),
    "O006-016-02-0015": ("bas", "Teorema Basu"),
}
C5_SUPPORT_SOURCES = (
    (
        "O006-C140-CMP-C5-SOURCE-ENVIRONMENT",
        ENVIRONMENT_LOCK,
        "source/environment.lock.json",
        "environment-lock",
        "CC-BY-SA-4.0",
        "companion-original",
    ),
    (
        "O006-C140-CMP-C5-SOURCE-COMPONENT-LICENSE",
        ROOT / "LICENSE.md",
        "source/rights/component-LICENSE.md",
        "component-rights-notice",
        "CC-BY-SA-4.0",
        "mixed-component-rights-register",
    ),
    (
        "O006-C140-CMP-C5-SOURCE-REPOSITORY-LICENSE",
        REPO / "LICENSE.md",
        "source/rights/repository-LICENSE.md",
        "collection-rights-notice",
        "CC-BY-SA-4.0",
        "mixed-component-collection",
    ),
    (
        "O006-C140-CMP-C5-SOURCE-RIGHTS-CONTROL",
        REPO / "00_control" / "RIGHTS_AND_COMPONENTS.md",
        "source/rights/RIGHTS_AND_COMPONENTS.md",
        "collection-rights-register",
        "CC-BY-SA-4.0",
        "mixed-component-collection",
    ),
)
CAPSTONE_SPECS: dict[str, dict[str, object]] = {
    "CP01": {
        "dataset_license": "CC-BY-4.0",
        "provenance": ("DATASET_PROVENANCE.json", "SHA256SUMS"),
        "clean_files": (
            "COLUMN_MANIFEST.csv",
            "ROW_MANIFEST.csv",
            "TRANSFORM_LEDGER.json",
            "concrete_compressive_strength.csv",
        ),
        "clean_table": "concrete_compressive_strength.csv",
        "clean_manifest": None,
        "transform_receipt": "CP01_TRANSFORM_RECEIPT.json",
        "transform_schema": "o006.c140.cp01-transform-replay.v1",
        "analysis_receipt": "CP01_REPLAY_RECEIPT.json",
        "analysis_receipt_in_generated": True,
        "analysis_schema": "o006.c140.cp01-analysis-replay.v2",
        "transform_script": "data/capstones/CP01/transform_cp01.py",
        "analysis_script": "capstones/run_cp01_analysis.py",
    },
    "CP02": {
        "dataset_license": "CC0-1.0",
        "provenance": (
            "DATASET_PROVENANCE.json",
            "INPUT_MANIFEST.csv",
            "RIGHTS_EVIDENCE.md",
            "SCHEMA.json",
        ),
        "clean_files": None,
        "clean_table": "CP02_cells_clean.csv",
        "clean_manifest": "MANIFEST.csv",
        "transform_receipt": "CP02_TRANSFORM_RECEIPT.json",
        "transform_schema": "o006.c140.cp02-transform.v1",
        "analysis_receipt": "CP02_ANALYSIS_RECEIPT.json",
        "analysis_receipt_in_generated": False,
        "analysis_schema": "o006.c140.cp02-analysis.v1",
        "transform_script": "data/capstones/CP02/transform_cp02.py",
        "analysis_script": "capstones/run_cp02_analysis.py",
    },
}
CP02_CREDENTIAL_WITNESS = (
    ROOT
    / "data"
    / "capstones"
    / "CP02"
    / "witnesses"
    / "doi-10.5061-dryad.573n5tbf3-resolved.html"
)
CP02_REDACTED_WITNESS = CP02_CREDENTIAL_WITNESS.with_name(
    "doi-10.5061-dryad.573n5tbf3-redacted.html"
)
CP02_REDACTION_RECEIPT = CP02_CREDENTIAL_WITNESS.with_name(
    "doi-10.5061-dryad.573n5tbf3-redistribution-redaction.json"
)
CP02_CREDENTIAL_ASSIGNMENT_RE = re.compile(
    rb"(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
    rb"\s*[:=]\s*[\"']?[^\s<\"']{8,}",
    re.IGNORECASE,
)

REQUIRED_METADATA = {
    "id",
    "type",
    "title",
    "locale",
    "license",
    "provenance",
    "prerequisites",
    "objectives",
    "relations",
    "status",
}
REQUIRED_C1 = {
    "O006-C140-CMP-INDEX",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 8)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 5)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(7, 11)),
    "O006-C140-CMP-CA01",
}
REQUIRED_CUMULATIVE_C2 = REQUIRED_C1 | {
    *(f"O006-C140-CMP-D{i:03d}" for i in range(8, 12)),
    "O006-C140-CMP-SIM005",
    "O006-C140-CMP-MS12",
}
REQUIRED_CUMULATIVE_C3 = REQUIRED_CUMULATIVE_C2 | {
    "O006-C140-CMP-D012",
    "O006-C140-CMP-D013",
    "O006-C140-CMP-SIM006",
    "O006-C140-CMP-MS11",
}
REQUIRED_CUMULATIVE_C4 = REQUIRED_CUMULATIVE_C3 | {
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(0, 7)),
}
REQUIRED_CUMULATIVE_C5 = REQUIRED_CUMULATIVE_C4 | {
    *(f"O006-C140-CMP-CA{i:02d}" for i in range(2, 5)),
    *(f"O006-C140-CMP-CP{i:02d}" for i in range(1, 3)),
}
ANCHOR_RE = re.compile(r'<a\s+id="([A-Za-z0-9._:-]+)"\s*></a>')
REF_RE = re.compile(r"\[ref:([A-Za-z0-9._:-]+)\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
DISPLAY_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
INLINE_RE = re.compile(r"\\\((.+?)\\\)")
DOLLAR_DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
DOLLAR_INLINE_RE = re.compile(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def active_required_ids() -> set[str]:
    return {
        "c3": REQUIRED_CUMULATIVE_C3,
        "c4": REQUIRED_CUMULATIVE_C4,
        "c5": REQUIRED_CUMULATIVE_C5,
    }[ACTIVE_BOUNDARY]


def active_receipt_name() -> str:
    return f"{ACTIVE_BOUNDARY.upper()}_BUILD_RECEIPT.json"


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_payload(fieldnames: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_unsafe_link(path: Path) -> bool:
    """Reject symlinks and Windows junctions at every publication boundary."""
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def validate_payload_name(name: str) -> PurePosixPath:
    """Return one canonical, relative POSIX output path or fail closed."""
    if "\\" in name:
        raise RuntimeError(f"Output payload path is not POSIX: {name}")
    relative = PurePosixPath(name)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.name
        or relative.as_posix() != name
    ):
        raise RuntimeError(f"Output payload path is unsafe or non-canonical: {name}")
    return relative


def ensure_safe_parent_chain(path: Path, boundary: Path) -> None:
    """Require an existing, link-free parent chain inside a fixed boundary."""
    boundary_resolved = boundary.resolve()
    cursor = path
    while True:
        if is_unsafe_link(cursor):
            raise RuntimeError(f"Unsafe link or junction in output path: {cursor}")
        if not cursor.is_dir():
            raise RuntimeError(f"Output parent is not a directory: {cursor}")
        if cursor.resolve() == boundary_resolved:
            return
        try:
            cursor.resolve().relative_to(boundary_resolved)
        except ValueError as exc:
            raise RuntimeError(f"Output path escapes its boundary: {path}") from exc
        if cursor.parent == cursor:
            raise RuntimeError(f"Output boundary is unreachable from: {path}")
        cursor = cursor.parent


def prepare_safe_directory(path: Path, boundary: Path) -> None:
    """Create a bounded directory one component at a time without following links."""
    if is_unsafe_link(boundary) or not boundary.is_dir():
        raise RuntimeError(f"Output boundary is missing or unsafe: {boundary}")
    try:
        relative = path.relative_to(boundary)
    except ValueError as exc:
        raise RuntimeError(f"Output directory escapes its boundary: {path}") from exc
    cursor = boundary
    for part in relative.parts:
        if part in {"", ".", ".."}:
            raise RuntimeError(f"Output directory is non-canonical: {path}")
        cursor = cursor / part
        if is_unsafe_link(cursor):
            raise RuntimeError(f"Unsafe link or junction in output path: {cursor}")
        if cursor.exists():
            if not cursor.is_dir():
                raise RuntimeError(f"Output parent is not a directory: {cursor}")
        else:
            cursor.mkdir()
    ensure_safe_parent_chain(path, boundary)


def atomic_write_file(path: Path, payload: bytes, *, boundary: Path = ROOT) -> None:
    """Write one fixed output atomically after link/path and byte readback checks."""
    prepare_safe_directory(path.parent, boundary)
    if is_unsafe_link(path) or (path.exists() and not path.is_file()):
        raise RuntimeError(f"Output file target is unsafe: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        if temporary.read_bytes() != payload:
            raise RuntimeError(f"Temporary output readback differs: {path.name}")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


@dataclass(frozen=True)
class Document:
    path: Path
    source_rel: str
    output_rel: str
    raw: bytes
    body: str
    metadata: dict[str, Any]
    anchors: tuple[str, ...]
    headings: dict[str, str]
    references: tuple[str, ...]


@dataclass(frozen=True)
class CapstoneAsset:
    capstone: str
    category: str
    source: Path
    backend_rel: str
    reader_rel: str | None
    effective_license: str
    dataset_license: str
    rights_scope: str
    rights_model: str = "companion-original"
    payload: bytes | None = None


def capstone_asset_payload(asset: CapstoneAsset) -> bytes:
    return asset.payload if asset.payload is not None else asset.source.read_bytes()


def deterministic_gzip(payload: bytes, *, source_name: str) -> bytes:
    """Create a stable gzip member under the locked C5 Python environment."""
    stream = io.BytesIO()
    with gzip.GzipFile(
        filename=source_name,
        mode="wb",
        fileobj=stream,
        compresslevel=9,
        mtime=0,
    ) as archive:
        archive.write(payload)
    return stream.getvalue()


def cp02_coverage_derivative_record() -> dict[str, object]:
    raw_path = ROOT / "generated" / "capstones" / "CP02" / "CP02_coverage.csv"
    require_regular_file(raw_path, "CP02 canonical coverage ledger")
    raw = raw_path.read_bytes()
    derivative = deterministic_gzip(raw, source_name=raw_path.name)
    return {
        "compression": {
            "algorithm": "gzip",
            "compresslevel": 9,
            "header_filename": raw_path.name,
            "mtime": 0,
        },
        "public_derivative": {
            "bytes": len(derivative),
            "path": "assets/capstones/CP02/CP02_coverage.csv.gz",
            "sha256": sha256(derivative),
        },
        "source": file_identity(raw_path),
        "status": "pass",
    }


def normalized_relations(document: Document) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for relation in document.metadata["relations"]:
        if isinstance(relation, str) and ":" in relation:
            predicate, target = relation.split(":", 1)
        elif isinstance(relation, dict):
            predicate, target = relation.get("predicate"), relation.get("target")
        else:
            raise RuntimeError(f"Invalid relation in {document.source_rel}: {relation!r}")
        if not isinstance(predicate, str) or not predicate or not isinstance(target, str) or not target:
            raise RuntimeError(f"Incomplete relation in {document.source_rel}: {relation!r}")
        rows.append({"predicate": predicate, "target": target})
    return rows


def parse_document(path: Path) -> Document:
    raw = path.read_bytes()
    if b"\r" in raw:
        raise RuntimeError(f"Non-LF newline in {rel(path)}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Non-UTF-8 source {rel(path)}") from exc
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != "---" or lines[2] != "---":
        raise RuntimeError(f"Front matter must be exactly three lines in {rel(path)}")
    try:
        metadata = json.loads(lines[1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid one-line JSON in {rel(path)}: {exc}") from exc
    missing = REQUIRED_METADATA - set(metadata)
    if missing:
        raise RuntimeError(f"Missing metadata {sorted(missing)} in {rel(path)}")
    if metadata["locale"] != "id-ID" or metadata["license"] != "CC-BY-SA-4.0":
        raise RuntimeError(f"Locale/license mismatch in {rel(path)}")
    if metadata["provenance"] != "OpenAI Codex gpt-5.6-sol, Ultra":
        raise RuntimeError(f"Provenance mismatch in {rel(path)}")
    if not isinstance(metadata["relations"], list):
        raise RuntimeError(f"relations is not a list in {rel(path)}")
    body = "\n".join(lines[3:]) + "\n"
    anchors = tuple(ANCHOR_RE.findall(body))
    if len(anchors) != len(set(anchors)):
        raise RuntimeError(f"Duplicate anchor inside {rel(path)}")
    body_lines = body.splitlines()
    headings: dict[str, str] = {}
    for index, line in enumerate(body_lines):
        match = ANCHOR_RE.fullmatch(line.strip())
        if not match:
            continue
        cursor = index + 1
        while cursor < len(body_lines) and not body_lines[cursor].strip():
            cursor += 1
        if cursor < len(body_lines):
            heading = re.match(r"^#{1,6}\s+(.+?)\s*$", body_lines[cursor])
            if heading:
                headings[match.group(1)] = heading.group(1).replace("*", "")
    source_rel = path.relative_to(SOURCE).as_posix()
    return Document(
        path=path,
        source_rel=source_rel,
        output_rel=PurePosixPath(source_rel).with_suffix(".html").as_posix(),
        raw=raw,
        body=body,
        metadata=metadata,
        anchors=anchors,
        headings=headings,
        references=tuple(REF_RE.findall(body)),
    )


def load_documents() -> list[Document]:
    if is_unsafe_link(SOURCE) or not SOURCE.is_dir():
        raise RuntimeError("Companion source root is missing or unsafe")
    source_entries = sorted(SOURCE.rglob("*"))
    for path in source_entries:
        if is_unsafe_link(path):
            raise RuntimeError(f"Companion source tree contains an unsafe link: {path}")
        if not path.is_dir() and not path.is_file():
            raise RuntimeError(f"Companion source tree contains an unsafe entry: {path}")
    documents = [parse_document(path) for path in source_entries if path.is_file() and path.suffix == ".md"]
    order = {"index": 0, "theory": 1, "simulation": 2, "mastery": 3, "assessment": 4, "capstone": 5}
    documents.sort(key=lambda item: (order.get(str(item.metadata["type"]), 99), str(item.metadata["id"])))
    ids = [str(item.metadata["id"]) for item in documents]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate document ID")
    required_ids = active_required_ids()
    missing = sorted(required_ids - set(ids))
    if missing:
        raise RuntimeError(f"Cumulative {ACTIVE_BOUNDARY.upper()} source boundary incomplete; missing {missing}")
    unexpected = sorted(set(ids) - required_ids)
    if unexpected:
        raise RuntimeError(f"Cumulative {ACTIVE_BOUNDARY.upper()} source boundary has unexpected documents {unexpected}")
    all_anchors = [anchor for item in documents for anchor in item.anchors]
    duplicates = sorted({anchor for anchor in all_anchors if all_anchors.count(anchor) > 1})
    if duplicates:
        raise RuntimeError(f"Cross-document duplicate anchors: {duplicates}")
    return documents


def load_external_targets() -> tuple[dict[str, str], dict[str, str]]:
    urls: dict[str, str] = {}
    titles: dict[str, str] = {}
    penn = REPO / "backend" / "through_lesson12_documents.jsonl"
    if is_unsafe_link(penn) or not penn.is_file():
        raise RuntimeError("Penn State backend authority is missing or unsafe")
    for line in penn.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        document_id = row["document_id"]
        component = row["component_id"]
        suffix = "" if component == "index" else f"{component}.html"
        urls[document_id] = f"https://kokunoyumeto.github.io/penn-state-stat-415-id/{suffix}"
        titles[document_id] = "Penn State STAT 415" if component == "index" else component
    donor = REPO / "components" / "random-completeness" / "backend" / "entities.jsonl"
    if is_unsafe_link(donor) or not donor.is_file():
        raise RuntimeError("Random donor backend authority is missing or unsafe")
    if is_unsafe_link(RANDOM_DONOR_TARGET) or not RANDOM_DONOR_TARGET.is_file():
        raise RuntimeError("Random donor translated target is missing or unsafe")
    donor_target_payload = RANDOM_DONOR_TARGET.read_bytes()
    if (
        len(donor_target_payload) != RANDOM_DONOR_TARGET_BYTES
        or sha256(donor_target_payload) != RANDOM_DONOR_TARGET_SHA256
    ):
        raise RuntimeError("Random donor translated target identity differs")
    donor_target_text = donor_target_payload.decode("utf-8")
    donor_target_ids = set(
        re.findall(r'\bid=["\']([A-Za-z0-9._:-]+)["\']', donor_target_text)
    )
    donor_rows: dict[str, dict[str, Any]] = {}
    for line in donor.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        entity_id = str(row["entity_id"])
        if entity_id in donor_rows:
            raise RuntimeError(f"Duplicate Random donor entity ID: {entity_id}")
        donor_rows[entity_id] = row
        candidate = row.get("target_id") or row.get("native_id") or row.get("injected_target_id")
        fragment = str(candidate) if candidate in donor_target_ids else None
        urls[entity_id] = RANDOM_DONOR_PUBLIC_PAGE + (f"#{fragment}" if fragment else "")
        target_label = row.get("target_text")
        titles[entity_id] = (
            str(target_label).replace("\n", " ")[:120]
            if isinstance(target_label, str) and target_label.strip()
            else entity_id
        )
    missing_references = sorted(RANDOM_DONOR_REFERENCE_TARGETS.keys() - donor_rows.keys())
    if missing_references:
        raise RuntimeError(f"Random donor reference entities are missing: {missing_references}")
    for entity_id, (fragment, label) in RANDOM_DONOR_REFERENCE_TARGETS.items():
        row = donor_rows[entity_id]
        if row.get("translation_target_path") != "source/id-ID/random/point/Sufficient.html":
            raise RuntimeError(f"Random donor target path differs: {entity_id}")
        if (
            row.get("translation_target_bytes") != RANDOM_DONOR_TARGET_BYTES
            or row.get("translation_target_sha256") != RANDOM_DONOR_TARGET_SHA256
        ):
            raise RuntimeError(f"Random donor target identity differs: {entity_id}")
        if fragment is not None and fragment not in donor_target_ids:
            raise RuntimeError(f"Random donor target fragment is absent: {entity_id} -> {fragment}")
        if entity_id == "O006-016-00-0001":
            if row.get("entity_type") != "document":
                raise RuntimeError("Random donor document binding differs")
        else:
            if row.get("entity_type") != "unit":
                raise RuntimeError(f"Random donor referenced entity is not a unit: {entity_id}")
            expected_order = int(entity_id.rsplit("-", 1)[1])
            if row.get("kind_order") != expected_order:
                raise RuntimeError(f"Random donor unit order differs: {entity_id}")
            native_target = row.get("native_id")
            if native_target is None:
                generated = f"o006.random.point.sufficient.unit-{expected_order:02d}"
                if fragment != generated:
                    raise RuntimeError(f"Random donor generated unit anchor differs: {entity_id}")
            elif fragment not in {
                str(native_target),
                str(row.get("target_id")),
                str(row.get("injected_target_id")),
            }:
                raise RuntimeError(f"Random donor native unit anchor differs: {entity_id}")
        urls[entity_id] = RANDOM_DONOR_PUBLIC_PAGE + (f"#{fragment}" if fragment else "")
        titles[entity_id] = label
    return urls, titles


def relative_href(current: str, target: str, anchor: str | None = None) -> str:
    start = PurePosixPath(current).parent.as_posix()
    if start == ".":
        start = ""
    value = posixpath.relpath(target, start=start or ".")
    return value + (f"#{anchor}" if anchor else "")


def render_markdown(
    document: Document,
    local_paths: dict[str, tuple[str, str | None]],
    titles: dict[str, str],
    external_urls: dict[str, str],
) -> str:
    tokens: dict[str, str] = {}
    counter = 0

    def token(markup: str, kind: str) -> str:
        nonlocal counter
        counter += 1
        key = f"@@O006{kind}{counter:06d}@@"
        tokens[key] = markup
        return key

    def display(match: re.Match[str]) -> str:
        math_text = html.escape(match.group(1).strip(), quote=False)
        return "\n\n" + token(f'<div class="math-display" role="math">\\[{math_text}\\]</div>', "MATHD") + "\n\n"

    def inline(match: re.Match[str]) -> str:
        math_text = html.escape(match.group(1), quote=False)
        return token(f'<span class="math-inline" role="math">\\({math_text}\\)</span>', "MATHI")

    working = DOLLAR_DISPLAY_RE.sub(display, document.body)
    working = DISPLAY_RE.sub(display, working)
    working = INLINE_RE.sub(inline, working)
    working = DOLLAR_INLINE_RE.sub(inline, working)

    def reference(match: re.Match[str]) -> str:
        target_id = match.group(1)
        label = html.escape(titles.get(target_id, target_id))
        if target_id in local_paths:
            target_page, anchor = local_paths[target_id]
            href = relative_href(document.output_rel, target_page, anchor)
            markup = f'<a class="xref" data-target-id="{target_id}" href="{html.escape(href, quote=True)}">{label}</a>'
        elif target_id in external_urls:
            markup = f'<a class="xref external" data-target-id="{target_id}" href="{html.escape(external_urls[target_id], quote=True)}">{label}</a>'
        else:
            raise RuntimeError(f"Unresolved reference {target_id} in {document.source_rel}")
        return token(markup, "REF")

    working = REF_RE.sub(reference, working)
    renderer = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    # CommonMark does not enable pipe tables by default.  Enable the table
    # rule so source tables become semantic HTML rather than literal pipes.
    renderer.enable("table")
    rendered = renderer.render(working)
    for key, markup in tokens.items():
        rendered = rendered.replace(f"<p>{key}</p>", markup)
        rendered = rendered.replace(key, markup)

    # Add deterministic accessibility metadata to Markdown-rendered tables.
    # Generated captions combine a deterministic per-page ordinal with the
    # nearest preceding heading, so repeated section labels do not create
    # duplicate accessible table names.  Existing captions and scope
    # attributes are preserved.  Raw HTML/code/math are already emitted and
    # are not rewritten by this table-only pass.
    table_number = 0

    def accessible_table(match: re.Match[str]) -> str:
        nonlocal table_number
        table_number += 1
        table = match.group(0)
        if re.search(r"<caption\b", table, flags=re.IGNORECASE):
            captioned = table
        else:
            prior = rendered[: match.start()]
            headings = list(re.finditer(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", prior, flags=re.IGNORECASE | re.DOTALL))
            heading = headings[-1].group(1) if headings else ""
            heading = re.sub(r"<[^>]+>", "", heading)
            heading = html.unescape(re.sub(r"\s+", " ", heading)).strip()
            caption_text = f"Tabel {table_number}" + (f" — {heading}" if heading else "")
            captioned = table.replace(
                "<table>",
                f"<table>\n<caption>{html.escape(caption_text)}</caption>",
                1,
            )

        def scope_columns(section: re.Match[str]) -> str:
            section_html = section.group(0)
            return re.sub(r"<th(?![^>]*\bscope=)(\s|>)", r'<th scope="col"\1', section_html, flags=re.IGNORECASE)

        captioned = re.sub(r"<thead\b[^>]*>.*?</thead>", scope_columns, captioned, flags=re.IGNORECASE | re.DOTALL)
        # A body <th> is unambiguously a row header; leave body <td> cells
        # unchanged because Markdown tables do not identify row headers.
        captioned = re.sub(r"<tbody\b[^>]*>.*?</tbody>", lambda body: re.sub(
            r"<th(?![^>]*\bscope=)(\s|>)", r'<th scope="row"\1', body.group(0), flags=re.IGNORECASE
        ), captioned, flags=re.IGNORECASE | re.DOTALL)
        return captioned

    rendered = re.sub(r"<table\b[^>]*>.*?</table>", accessible_table, rendered, flags=re.IGNORECASE | re.DOTALL)

    asset_prefix = relative_href(document.output_rel, "assets/placeholder").rsplit("/", 1)[0]
    rendered = rendered.replace('src="assets/', f'src="{asset_prefix}/')
    rendered = rendered.replace('href="assets/', f'href="{asset_prefix}/')
    return rendered


STYLE = """\
:root{color-scheme:light;--ink:#17202a;--muted:#566573;--rule:#d5d8dc;--accent:#154360;--paper:#fff;--wash:#f4f6f7}
*{box-sizing:border-box}html{font-size:18px;scroll-behavior:smooth}body{margin:0;background:var(--wash);color:var(--ink);font-family:Georgia,'Times New Roman',serif;line-height:1.62}
.skip-link{position:absolute;left:.5rem;top:-4rem;z-index:100;background:#fff;color:#000;padding:.75rem 1rem;border:2px solid var(--accent)}.skip-link:focus{top:.5rem}.shell{display:grid;grid-template-columns:minmax(15rem,21rem) minmax(0,52rem);gap:2rem;max-width:78rem;margin:0 auto;padding:1.25rem}.sidebar{align-self:start;position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow:auto;background:var(--paper);border:1px solid var(--rule);border-radius:.5rem;padding:1rem}.sidebar .nav-title{font:700 1rem Arial,sans-serif;margin:.2rem 0 .8rem}.sidebar ol{padding-left:1.4rem;margin:0}.sidebar li{margin:.35rem 0}.sidebar a{color:var(--accent)}.sidebar a[aria-current="page"]{font-weight:700}main{min-width:0;background:var(--paper);border:1px solid var(--rule);border-radius:.5rem;padding:clamp(1.25rem,4vw,3.5rem)}h1,h2,h3,h4{font-family:Arial,sans-serif;line-height:1.2;color:#102a43;margin-top:2em}h1{font-size:2.05rem;margin-top:0}h2{font-size:1.45rem}h3{font-size:1.18rem}a{color:#0b5e8e;text-underline-offset:.15em}.metadata{font-family:Arial,sans-serif;font-size:.88rem;color:var(--muted);border-bottom:1px solid var(--rule);padding-bottom:1rem;margin-bottom:2rem}.math-display{max-width:100%;overflow-x:auto;padding:.6rem .25rem;margin:1rem 0}.math-inline{white-space:nowrap}figure{margin:2rem 0}figure img{display:block;width:100%;height:auto;margin:0 auto;border:1px solid var(--rule);background:#fff}figcaption{font:italic .9rem Arial,sans-serif;color:var(--muted);margin-top:.5rem}pre,code{font-family:'Cascadia Mono',Consolas,monospace}pre{overflow:auto;background:#f7f9fa;padding:1rem;border-radius:.3rem}blockquote{border-left:.25rem solid #7fb3d5;margin-left:0;padding-left:1rem;color:#34495e}.xref{font-weight:600}.license{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--rule);font:0.85rem Arial,sans-serif;color:var(--muted)}
.artifact-index{margin-top:2.5rem;padding:1rem;background:#f7f9fa;border:1px solid var(--rule);border-radius:.35rem;font:0.88rem Arial,sans-serif}.artifact-index p{margin-top:0}.artifact-index ul{columns:2;column-gap:2rem;padding-left:1.25rem}.artifact-index li{break-inside:avoid;margin:.3rem 0}.artifact-index .asset-license{color:var(--muted);font-size:.8rem}
@media(max-width:780px){html{font-size:16px}.shell{display:block;padding:.5rem}.sidebar{position:static;max-height:none;margin-bottom:.75rem}main{padding:1.1rem;border-radius:.25rem}h1{font-size:1.7rem}.math-display{margin-left:-.25rem;margin-right:-.25rem}.artifact-index ul{columns:1}}
@media print{body{background:#fff}.shell{display:block;max-width:none;padding:0}.sidebar{display:none}main{border:0;padding:0}.xref{color:inherit}}
"""


def page_template(document: Document, body_html: str, documents: list[Document]) -> bytes:
    css_href = relative_href(document.output_rel, "assets/style.css")
    mathjax_href = relative_href(document.output_rel, "assets/MathJax/tex-svg.js")
    nav_items = []
    for item in documents:
        href = relative_href(document.output_rel, item.output_rel)
        current = ' aria-current="page"' if item.output_rel == document.output_rel else ""
        nav_items.append(
            f'<li><a href="{html.escape(href, quote=True)}"{current}>'
            f'{html.escape(str(item.metadata["title"]))}</a></li>'
        )
    metadata = document.metadata
    page = f"""<!doctype html>
<html lang="id-ID">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="OpenAI Codex gpt-5.6-sol, Ultra">
<title>{html.escape(str(metadata['title']))}</title>
<link rel="stylesheet" href="{html.escape(css_href, quote=True)}">
<script>window.MathJax={{loader:{{load:['[tex]/boldsymbol']}},tex:{{packages:{{'[+]':['boldsymbol']}},inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'local'}}}};</script>
<script defer src="{html.escape(mathjax_href, quote=True)}"></script>
</head>
<body>
<a class="skip-link" href="#main-content">Langsung ke isi utama</a>
<div class="shell">
<nav class="sidebar" aria-labelledby="companion-nav-title"><p class="nav-title" id="companion-nav-title">Isi pendamping</p><ol>{''.join(nav_items)}</ol></nav>
<main id="main-content" tabindex="-1">
<div class="metadata"><strong>{html.escape(str(metadata['id']))}</strong> · id-ID · CC BY-SA 4.0 · {html.escape(str(metadata['provenance']))}</div>
{body_html}
<footer class="license">Materi pendamping orisinal berlisensi CC BY-SA 4.0. Komponen Penn State dan Random tetap berada di bawah lisensinya masing-masing dan tidak direlisensikan oleh halaman ini.</footer>
</main>
</div>
</body>
</html>
"""
    return page.encode("utf-8")


def capstone_artifact_index(document: Document, assets: list[CapstoneAsset]) -> str:
    capstone = str(document.metadata["id"]).rsplit("-", 1)[-1]
    rows = [asset for asset in assets if asset.capstone == capstone and asset.reader_rel is not None]
    if not rows:
        return ""
    items = []
    for asset in sorted(rows, key=capstone_asset_id):
        assert asset.reader_rel is not None
        href = relative_href(document.output_rel, asset.reader_rel)
        items.append(
            '<li><a href="{}">{}</a> <span class="asset-license">({}; {})</span></li>'.format(
                html.escape(href, quote=True),
                html.escape(PurePosixPath(asset.reader_rel).name),
                html.escape(asset.category),
                html.escape(asset.effective_license),
            )
        )
    rights_href = relative_href(document.output_rel, "assets/capstones/ASSET_RIGHTS.jsonl")
    items.append(
        '<li><a href="{}">ASSET_RIGHTS.jsonl</a> '
        '<span class="asset-license">(metadata hak; CC-BY-SA-4.0)</span></li>'.format(
            html.escape(rights_href, quote=True)
        )
    )
    return (
        '<aside class="artifact-index" aria-label="Artefak reproduksi">'
        '<p><strong>Artefak reproduksi.</strong> Berkas di bawah terikat manifest; '
        'lisensi efektif setiap berkas ditampilkan terpisah.</p><ul>'
        + "".join(items)
        + "</ul></aside>"
    )


def generated_asset_id(batch: str, path: Path) -> str:
    name = path.name
    if name == "MANIFEST.csv":
        return f"O006-C140-CMP-{batch.upper()}-SIM-MANIFEST"
    stem = path.stem.upper()
    prefix = stem.split("_", 1)[0]
    suffix = stem.split("_", 1)[1] if "_" in stem else "OUTPUT"
    suffix = re.sub(r"[^A-Z0-9]+", "-", suffix)
    return f"O006-C140-CMP-{prefix}-ASSET-{suffix}-{path.suffix[1:].upper()}"


def generated_output_rel(batch: str, path: Path) -> str:
    if path.name == "MANIFEST.csv":
        return f"assets/simulations/manifests/{batch}.csv"
    return f"assets/simulations/{path.name}"


def declared_simulation_assets(
    batch: str, directory: Path
) -> tuple[Path, list[tuple[dict[str, str], Path]]]:
    """Return the manifest-closed generated asset set for one batch."""
    if is_unsafe_link(directory) or not directory.is_dir():
        raise RuntimeError(f"{batch.upper()} simulation output directory is missing or unsafe")
    manifest = directory / "MANIFEST.csv"
    if is_unsafe_link(manifest) or not manifest.is_file():
        raise RuntimeError(f"{batch.upper()} simulation manifest is missing or unsafe")
    rows = list(csv.DictReader(manifest.read_text(encoding="utf-8").splitlines()))
    if not rows:
        raise RuntimeError(f"{batch.upper()} simulation manifest is empty")
    expected_prefix = PurePosixPath("generated") / "simulations" / batch
    entries: list[tuple[dict[str, str], Path]] = []
    names: set[str] = set()
    for index, row in enumerate(rows, start=2):
        path_value = str(row.get("path") or "")
        filename_value = str(row.get("filename") or "")
        if bool(path_value) == bool(filename_value):
            raise RuntimeError(
                f"{batch.upper()} manifest row {index} must declare exactly one path field"
            )
        if path_value:
            relative = PurePosixPath(path_value)
            if relative.parent != expected_prefix or len(relative.name) == 0:
                raise RuntimeError(
                    f"{batch.upper()} manifest path escapes its batch: {path_value}"
                )
            path = ROOT.joinpath(*relative.parts)
        else:
            relative = PurePosixPath(filename_value)
            if len(relative.parts) != 1 or relative.name != filename_value:
                raise RuntimeError(
                    f"{batch.upper()} manifest filename is unsafe: {filename_value}"
                )
            path = directory / filename_value
        if path.name == manifest.name or path.name in names:
            raise RuntimeError(f"{batch.upper()} manifest duplicates output {path.name}")
        if is_unsafe_link(path) or not path.is_file() or path.parent.resolve() != directory.resolve():
            raise RuntimeError(f"{batch.upper()} declared output is missing or unsafe: {path.name}")
        try:
            expected_bytes = int(str(row.get("bytes", "")))
        except ValueError as exc:
            raise RuntimeError(f"{batch.upper()} manifest byte count is invalid: {path.name}") from exc
        payload = path.read_bytes()
        if len(payload) != expected_bytes or sha256(payload) != str(row.get("sha256", "")):
            raise RuntimeError(f"{batch.upper()} manifest identity differs: {path.name}")
        names.add(path.name)
        entries.append((row, path))
    actual_names: set[str] = set()
    for candidate in directory.iterdir():
        if is_unsafe_link(candidate) or not candidate.is_file():
            raise RuntimeError(
                f"{batch.upper()} simulation directory contains an unsafe entry: {candidate.name}"
            )
        actual_names.add(candidate.name)
    expected_names = {manifest.name, *names}
    if actual_names != expected_names:
        raise RuntimeError(
            f"{batch.upper()} simulation directory is not manifest-closed; "
            f"missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )
    return manifest, entries


def require_regular_file(path: Path, label: str) -> None:
    if is_unsafe_link(path) or not path.is_file():
        try:
            display = path.relative_to(REPO).as_posix()
        except ValueError:
            display = str(path)
        raise RuntimeError(f"{label} is missing or unsafe: {display}")


def file_identity(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "bytes": len(payload),
        "path": rel(path),
        "sha256": sha256(payload),
    }


def c5_support_source_records() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for _source_id, path, backend_rel, role, license_id, rights_model in C5_SUPPORT_SOURCES:
        payload = path.read_bytes()
        rows.append({
            "backend_path": backend_rel,
            "bytes": len(payload),
            "license": license_id,
            "path": path.relative_to(REPO).as_posix(),
            "rights_model": rights_model,
            "role": role,
            "sha256": sha256(payload),
        })
    return rows


def cp02_redaction_record() -> dict[str, object]:
    """Verify public evidence; replay the excluded original only when available."""
    for path, label in (
        (CP02_REDACTED_WITNESS, "CP02 redacted witness"),
        (CP02_REDACTION_RECEIPT, "CP02 redaction receipt"),
    ):
        require_regular_file(path, label)

    derivative = CP02_REDACTED_WITNESS.read_bytes()
    receipt_payload = CP02_REDACTION_RECEIPT.read_bytes()
    if (len(derivative), sha256(derivative)) != (
        45_103,
        "3a03d836ebdb80191a70ff71d4faaa810eee966307482bdae5d04b430d5c8f9f",
    ):
        raise RuntimeError("CP02 pinned public redacted witness identity differs")
    if (len(receipt_payload), sha256(receipt_payload)) != (
        662,
        "5398e6f32c2d0eb81475e37c7a9ea35a8f1833ee387c6119376e308fefa92543",
    ):
        raise RuntimeError("CP02 pinned public redaction receipt identity differs")
    receipt = json.loads(receipt_payload.decode("utf-8"))
    if canonical_json(receipt) != receipt_payload:
        raise RuntimeError("CP02 public redaction receipt is not canonical")
    if CP02_CREDENTIAL_ASSIGNMENT_RE.search(derivative):
        raise RuntimeError("CP02 redacted witness retains a credential assignment")

    if CP02_CREDENTIAL_WITNESS.exists() or is_unsafe_link(CP02_CREDENTIAL_WITNESS):
        require_regular_file(CP02_CREDENTIAL_WITNESS, "CP02 excluded original witness")
        original = CP02_CREDENTIAL_WITNESS.read_bytes()
        matches = list(CP02_CREDENTIAL_ASSIGNMENT_RE.finditer(original))
        if (
            len(matches) != 1
            or not matches[0].group(0).lstrip().lower().startswith(b"apikey")
        ):
            raise RuntimeError("CP02 credential-bearing witness redaction contract differs")
        replay_derivative = (
            original[: matches[0].start()]
            + b"redactedClientField: ''"
            + original[matches[0].end() :]
        )
        expected_receipt = canonical_json({
            "derivative": {
                "bytes": len(replay_derivative),
                "path": rel(CP02_REDACTED_WITNESS),
                "sha256": sha256(replay_derivative),
            },
            "excluded_original": {
                "bytes": len(original),
                "path": rel(CP02_CREDENTIAL_WITNESS),
                "sha256": sha256(original),
            },
            "redactions": [
                {
                    "count": 1,
                    "field": "apiKey",
                    "reason": "credential-like public client key excluded from redistribution",
                }
            ],
            "schema": "o006.c140.cp02-witness-redaction.v1",
            "status": "pass",
        })
        if derivative != replay_derivative:
            raise RuntimeError("CP02 redacted witness bytes differ from deterministic replay")
        if receipt_payload != expected_receipt:
            raise RuntimeError("CP02 witness redaction receipt differs from deterministic replay")
    # In a public checkout, the original is deliberately absent.  This is its
    # historical identity from the pinned sanitized receipt, not a fresh
    # observation of credential-bearing bytes.  The public payloads above have
    # nevertheless both been checked against their exact frozen identities.
    return {
        "derivative": file_identity(CP02_REDACTED_WITNESS),
        "excluded_original": receipt["excluded_original"],
        "receipt": file_identity(CP02_REDACTION_RECEIPT),
        "schema": "o006.c140.cp02-witness-redaction.v1",
        "status": "pass",
    }


def declared_manifest_directory(
    label: str,
    directory: Path,
    *,
    allowed_unlisted: set[str] | None = None,
) -> tuple[Path, list[tuple[dict[str, str], Path]]]:
    """Validate a flat directory whose MANIFEST lists every substantive peer file."""
    if is_unsafe_link(directory) or not directory.is_dir():
        raise RuntimeError(f"{label} directory is missing or unsafe")
    manifest = directory / "MANIFEST.csv"
    require_regular_file(manifest, f"{label} manifest")
    rows = list(csv.DictReader(manifest.read_text(encoding="utf-8").splitlines()))
    if not rows:
        raise RuntimeError(f"{label} manifest is empty")
    entries: list[tuple[dict[str, str], Path]] = []
    names: list[str] = []
    directory_resolved = directory.resolve()
    for index, row in enumerate(rows, start=2):
        path_value = str(row.get("path") or "")
        filename_value = str(row.get("filename") or "")
        if bool(path_value) == bool(filename_value):
            raise RuntimeError(f"{label} manifest row {index} must declare exactly one path field")
        value = path_value or filename_value
        if "\\" in value:
            raise RuntimeError(f"{label} manifest row {index} uses a non-POSIX path")
        relative = PurePosixPath(value)
        if relative.is_absolute() or ".." in relative.parts or not relative.name:
            raise RuntimeError(f"{label} manifest path is unsafe: {value}")
        if len(relative.parts) == 1:
            path = directory / relative.name
        else:
            path = ROOT.joinpath(*relative.parts)
        if path.parent.resolve() != directory_resolved:
            raise RuntimeError(f"{label} manifest path escapes its directory: {value}")
        if path.name == manifest.name or path.name in names:
            raise RuntimeError(f"{label} manifest duplicates output {path.name}")
        require_regular_file(path, f"{label} declared output")
        try:
            expected_bytes = int(str(row.get("bytes", "")))
        except ValueError as exc:
            raise RuntimeError(f"{label} manifest byte count is invalid: {path.name}") from exc
        payload = path.read_bytes()
        expected_sha = str(row.get("sha256", ""))
        if (
            expected_bytes <= 0
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha)
            or len(payload) != expected_bytes
            or sha256(payload) != expected_sha
        ):
            raise RuntimeError(f"{label} manifest identity differs: {path.name}")
        names.append(path.name)
        entries.append((row, path))
    if names != sorted(names):
        raise RuntimeError(f"{label} manifest paths are not canonically ordered")
    actual_names: set[str] = set()
    for candidate in directory.iterdir():
        if is_unsafe_link(candidate) or not candidate.is_file():
            raise RuntimeError(f"{label} directory contains an unsafe entry: {candidate.name}")
        actual_names.add(candidate.name)
    expected_names = {manifest.name, *names, *(allowed_unlisted or set())}
    if actual_names != expected_names:
        raise RuntimeError(
            f"{label} directory is not manifest-closed; "
            f"missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )
    return manifest, entries


def declared_exact_directory(label: str, directory: Path, names: tuple[str, ...]) -> list[Path]:
    """Validate a flat directory closed by a fixed producer contract."""
    if is_unsafe_link(directory) or not directory.is_dir():
        raise RuntimeError(f"{label} directory is missing or unsafe")
    if len(names) != len(set(names)) or list(names) != sorted(names):
        raise RuntimeError(f"{label} fixed inventory is not canonical")
    paths = [directory / name for name in names]
    for path in paths:
        require_regular_file(path, f"{label} output")
    actual_names: set[str] = set()
    for candidate in directory.iterdir():
        if is_unsafe_link(candidate) or not candidate.is_file():
            raise RuntimeError(f"{label} directory contains an unsafe entry: {candidate.name}")
        actual_names.add(candidate.name)
    expected_names = set(names)
    if actual_names != expected_names:
        raise RuntimeError(
            f"{label} directory is not contract-closed; "
            f"missing={sorted(expected_names - actual_names)}, "
            f"extra={sorted(actual_names - expected_names)}"
        )
    return paths


def validate_capstone_receipt(
    label: str,
    receipt_path: Path,
    schema: str,
    output_paths: list[Path],
    manifest_path: Path | None,
    code_paths: list[Path],
    provenance_paths: list[Path] | None = None,
) -> dict[str, object]:
    require_regular_file(receipt_path, f"{label} receipt")
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{label} receipt is not valid JSON") from exc
    if not isinstance(receipt, dict) or receipt.get("schema") != schema:
        raise RuntimeError(f"{label} receipt schema differs")
    if receipt.get("status") != "pass":
        raise RuntimeError(f"{label} receipt does not pass")
    if receipt.get("network_access") is not False or receipt.get("browser_processes_used") is not False:
        raise RuntimeError(f"{label} receipt browser/network claim differs")
    raw_code = receipt.get("code")
    code_rows = [raw_code] if isinstance(raw_code, dict) else raw_code
    if not isinstance(code_rows, list) or not all(isinstance(row, dict) for row in code_rows):
        raise RuntimeError(f"{label} receipt code inventory is missing")
    if len(code_rows) != len(code_paths):
        raise RuntimeError(f"{label} receipt code inventory differs")
    for index, (row, path) in enumerate(zip(code_rows, code_paths, strict=True), start=1):
        identity = file_identity(path)
        record_path = str(row.get("path") or "")
        if record_path not in {path.name, str(identity["path"])}:
            raise RuntimeError(f"{label} receipt code path {index} differs")
        if row.get("bytes") != identity["bytes"] or row.get("sha256") != identity["sha256"]:
            raise RuntimeError(f"{label} receipt code identity {index} differs")
    if provenance_paths is not None:
        rights_rows = receipt.get("rights_provenance_inputs")
        if not isinstance(rights_rows, list) or not rights_rows:
            raise RuntimeError(f"{label} receipt rights/provenance inventory is missing")
        observed_paths: list[str] = []
        for index, row in enumerate(rights_rows, start=1):
            if not isinstance(row, dict):
                raise RuntimeError(f"{label} rights/provenance row {index} is malformed")
            value = str(row.get("path") or "")
            if "\\" in value:
                raise RuntimeError(f"{label} rights/provenance row {index} uses a non-POSIX path")
            relative = PurePosixPath(value)
            if relative.is_absolute() or ".." in relative.parts or not relative.name:
                raise RuntimeError(f"{label} rights/provenance path is unsafe: {value}")
            path = ROOT.joinpath(*relative.parts)
            require_regular_file(path, f"{label} rights/provenance input")
            identity = file_identity(path)
            if row.get("bytes") != identity["bytes"] or row.get("sha256") != identity["sha256"]:
                raise RuntimeError(f"{label} rights/provenance identity differs: {value}")
            observed_paths.append(value)
        if observed_paths != sorted(set(observed_paths)):
            raise RuntimeError(f"{label} rights/provenance paths are not unique and canonical")
        required = {rel(path) for path in provenance_paths}
        if not required.issubset(observed_paths):
            raise RuntimeError(f"{label} receipt omits packaged provenance inputs")
    rows = receipt.get("outputs")
    if not isinstance(rows, list):
        raise RuntimeError(f"{label} receipt output inventory is missing")
    expected = []
    allowed_paths: dict[str, set[str]] = {}
    for path in sorted(output_paths, key=lambda item: item.name):
        identity = file_identity(path)
        expected.append({
            "bytes": identity["bytes"],
            "name": path.name,
            "sha256": identity["sha256"],
        })
        allowed_paths[path.name] = {path.name, str(identity["path"])}
    observed = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise RuntimeError(f"{label} receipt output row {index} is malformed")
        value = str(row.get("path") or "")
        if "\\" in value:
            raise RuntimeError(f"{label} receipt output row {index} uses a non-POSIX path")
        relative = PurePosixPath(value)
        if relative.is_absolute() or ".." in relative.parts or not relative.name:
            raise RuntimeError(f"{label} receipt output path is unsafe: {value}")
        if relative.name not in allowed_paths or value not in allowed_paths[relative.name]:
            raise RuntimeError(f"{label} receipt output path is outside its closed directory: {value}")
        observed.append({
            "bytes": row.get("bytes"),
            "name": relative.name,
            "sha256": row.get("sha256"),
        })
    if observed != expected:
        raise RuntimeError(f"{label} receipt output inventory differs")
    if manifest_path is not None:
        record = receipt.get("manifest")
        identity = file_identity(manifest_path)
        if record is not None:
            if not isinstance(record, dict):
                raise RuntimeError(f"{label} receipt manifest record is malformed")
            record_path = str(record.get("path") or "")
            if record_path not in {manifest_path.name, str(identity["path"])}:
                raise RuntimeError(f"{label} receipt manifest path differs")
            if record.get("bytes") != identity["bytes"] or record.get("sha256") != identity["sha256"]:
                raise RuntimeError(f"{label} receipt manifest identity differs")
    return receipt


def capstone_asset_id(asset: CapstoneAsset) -> str:
    token = re.sub(r"[^A-Z0-9]+", "-", f"{asset.category}-{asset.source.name}".upper()).strip("-")
    return f"O006-C140-CMP-{asset.capstone}-ASSET-{token}"


def collect_capstone_assets() -> list[CapstoneAsset]:
    if ACTIVE_BOUNDARY != "c5":
        return []
    assets: list[CapstoneAsset] = []
    for capstone, spec in CAPSTONE_SPECS.items():
        data_root = ROOT / "data" / "capstones" / capstone
        generated_root = ROOT / "generated" / "capstones" / capstone
        dataset_license = str(spec["dataset_license"])
        redistribution_exclusions: set[Path] = set()
        if capstone == "CP02":
            cp02_redaction_record()
            redistribution_exclusions.add(CP02_CREDENTIAL_WITNESS.resolve())

        provenance_names = tuple(str(name) for name in spec["provenance"])
        for name in provenance_names:
            path = data_root / name
            require_regular_file(path, f"{capstone} provenance asset")
            assets.append(CapstoneAsset(
                capstone=capstone,
                category="provenance",
                source=path,
                backend_rel=f"assets/capstones/{capstone}/provenance/{name}",
                reader_rel=f"assets/capstones/{capstone}/provenance/{name}",
                effective_license=COMPANION_LICENSE,
                dataset_license=dataset_license,
                rights_scope="companion-authored provenance metadata",
            ))

        clean_root = data_root / "clean"
        clean_manifest_name = spec["clean_manifest"]
        if clean_manifest_name is None:
            clean_names = tuple(str(name) for name in spec["clean_files"])
            clean_paths = declared_exact_directory(f"{capstone} clean", clean_root, clean_names)
            clean_manifest = None
        else:
            if clean_manifest_name != "MANIFEST.csv":
                raise RuntimeError(f"{capstone} clean manifest contract is unsupported")
            clean_manifest, clean_entries = declared_manifest_directory(f"{capstone} clean", clean_root)
            clean_paths = [path for _row, path in clean_entries] + [clean_manifest]
        transform_receipt = ROOT / "build" / str(spec["transform_receipt"])
        validate_capstone_receipt(
            f"{capstone} transform",
            transform_receipt,
            str(spec["transform_schema"]),
            clean_paths,
            clean_manifest,
            [ROOT.joinpath(*PurePosixPath(str(spec["transform_script"])).parts)],
        )
        clean_table = str(spec["clean_table"])
        for path in clean_paths:
            is_table = path.name == clean_table
            category = "clean_data" if is_table else "clean_metadata"
            effective_license = dataset_license if is_table else COMPANION_LICENSE
            rights_scope = "dataset-derived clean table" if is_table else "companion-authored clean metadata"
            assets.append(CapstoneAsset(
                capstone=capstone,
                category=category,
                source=path,
                backend_rel=f"assets/capstones/{capstone}/clean/{path.name}",
                reader_rel=f"assets/capstones/{capstone}/clean/{path.name}",
                effective_license=effective_license,
                dataset_license=dataset_license,
                rights_scope=rights_scope,
                rights_model="dataset-license" if is_table else "companion-original",
            ))
        assets.append(CapstoneAsset(
            capstone=capstone,
            category="receipt",
            source=transform_receipt,
            backend_rel=f"assets/capstones/{capstone}/{transform_receipt.name}",
            reader_rel=f"assets/capstones/{capstone}/{transform_receipt.name}",
            effective_license=COMPANION_LICENSE,
            dataset_license=dataset_license,
            rights_scope="companion-authored deterministic receipt",
        ))

        analysis_receipt_name = str(spec["analysis_receipt"])
        receipt_in_generated = bool(spec["analysis_receipt_in_generated"])
        analysis_receipt = (
            generated_root / analysis_receipt_name
            if receipt_in_generated
            else ROOT / "build" / analysis_receipt_name
        )
        allowed_unlisted = {analysis_receipt_name} if receipt_in_generated else set()
        analysis_manifest, analysis_entries = declared_manifest_directory(
            f"{capstone} analysis",
            generated_root,
            allowed_unlisted=allowed_unlisted,
        )
        analysis_paths = [path for _row, path in analysis_entries] + [analysis_manifest]
        analysis_receipt_data = validate_capstone_receipt(
            f"{capstone} analysis",
            analysis_receipt,
            str(spec["analysis_schema"]),
            analysis_paths,
            analysis_manifest,
            [
                ROOT.joinpath(*PurePosixPath(str(spec["transform_script"])).parts),
                ROOT.joinpath(*PurePosixPath(str(spec["analysis_script"])).parts),
            ],
            [data_root / name for name in provenance_names],
        )
        for row in analysis_receipt_data["rights_provenance_inputs"]:
            receipt_input = ROOT.joinpath(*PurePosixPath(str(row["path"])).parts)
            try:
                receipt_input.relative_to(data_root)
            except ValueError as exc:
                raise RuntimeError(
                    f"{capstone} receipt-bound input is outside its data tree: {row['path']}"
                ) from exc
        for path in analysis_paths:
            public_name = path.name
            public_payload: bytes | None = None
            rights_scope = "companion-authored static analysis"
            if capstone == "CP02" and path.name == "CP02_coverage.csv":
                public_name += ".gz"
                public_payload = deterministic_gzip(path.read_bytes(), source_name=path.name)
                rights_scope = (
                    "deterministic gzip redistribution derivative of the local "
                    "receipt-bound companion analysis ledger"
                )
            assets.append(CapstoneAsset(
                capstone=capstone,
                category="analysis",
                source=path,
                backend_rel=f"assets/capstones/{capstone}/{public_name}",
                reader_rel=f"assets/capstones/{capstone}/{public_name}",
                effective_license=COMPANION_LICENSE,
                dataset_license=dataset_license,
                rights_scope=rights_scope,
                payload=public_payload,
            ))
        assets.append(CapstoneAsset(
            capstone=capstone,
            category="receipt",
            source=analysis_receipt,
            backend_rel=f"assets/capstones/{capstone}/{analysis_receipt.name}",
            reader_rel=f"assets/capstones/{capstone}/{analysis_receipt.name}",
            effective_license=COMPANION_LICENSE,
            dataset_license=dataset_license,
            rights_scope="companion-authored deterministic receipt",
        ))

        # Preserve the complete small offline source-data closure in the backend.
        # Reader-facing pages receive only the explicitly linked provenance and
        # reproducibility artifacts above; raw transports and witnesses stay
        # backend-only and retain their own rights model.
        known_sources = {
            asset.source.resolve()
            for asset in assets
            if asset.capstone == capstone
        }
        transform_source = ROOT.joinpath(*PurePosixPath(str(spec["transform_script"])).parts)
        for candidate in sorted(data_root.rglob("*")):
            if is_unsafe_link(candidate):
                raise RuntimeError(f"{capstone} data tree contains a symlink: {rel(candidate)}")
            if candidate.is_dir():
                continue
            if not candidate.is_file():
                raise RuntimeError(f"{capstone} data tree contains an unsafe entry: {rel(candidate)}")
            if (
                candidate.resolve() in known_sources
                or candidate == transform_source
                or candidate.resolve() in redistribution_exclusions
            ):
                continue
            relative = candidate.relative_to(data_root)
            top = relative.parts[0]
            if top == "raw":
                category = "source_data"
                effective_license = dataset_license
                rights_scope = "dataset source bytes retained under the dataset grant"
                rights_model = "dataset-license"
            elif top == "http":
                category = "source_transport_witness"
                effective_license = "NOASSERTION"
                rights_scope = "verbatim HTTP evidence retained without relicense"
                rights_model = "external-evidence-no-relicense"
            elif top == "witnesses":
                if candidate == CP02_REDACTION_RECEIPT:
                    category = "source_metadata"
                    effective_license = COMPANION_LICENSE
                    rights_scope = "companion-authored redistribution redaction receipt"
                    rights_model = "companion-original"
                else:
                    category = "source_rights_witness"
                    effective_license = "NOASSERTION"
                    rights_scope = "public rights/version witness retained without relicense"
                    rights_model = "external-evidence-no-relicense"
            else:
                category = "source_metadata"
                effective_license = COMPANION_LICENSE
                rights_scope = "companion-authored source metadata"
                rights_model = "companion-original"
            assets.append(CapstoneAsset(
                capstone=capstone,
                category=category,
                source=candidate,
                backend_rel=f"source/capstones/{capstone}/data/{relative.as_posix()}",
                reader_rel=None,
                effective_license=effective_license,
                dataset_license=dataset_license,
                rights_scope=rights_scope,
                rights_model=rights_model,
            ))

        for role in ("transform_script", "analysis_script"):
            path = ROOT.joinpath(*PurePosixPath(str(spec[role])).parts)
            require_regular_file(path, f"{capstone} {role}")
            assets.append(CapstoneAsset(
                capstone=capstone,
                category="source_script",
                source=path,
                backend_rel=f"source/capstones/{capstone}/{path.name}",
                reader_rel=None,
                effective_license=COMPANION_LICENSE,
                dataset_license=dataset_license,
                rights_scope="companion-authored deterministic source",
            ))

        packaged_data_sources = {
            asset.source.resolve()
            for asset in assets
            if asset.capstone == capstone
            and (
                asset.source == transform_source
                or data_root in asset.source.parents
            )
        }
        actual_data_sources = {
            candidate.resolve()
            for candidate in data_root.rglob("*")
            if candidate.is_file() and candidate.resolve() not in redistribution_exclusions
        }
        if packaged_data_sources != actual_data_sources:
            raise RuntimeError(
                f"{capstone} offline data-tree closure differs; "
                f"missing={sorted(str(path) for path in actual_data_sources - packaged_data_sources)}, "
                f"extra={sorted(str(path) for path in packaged_data_sources - actual_data_sources)}"
            )

    asset_ids = [capstone_asset_id(asset) for asset in assets]
    backend_paths = [asset.backend_rel for asset in assets]
    reader_paths = [asset.reader_rel for asset in assets if asset.reader_rel is not None]
    if len(asset_ids) != len(set(asset_ids)):
        raise RuntimeError("Duplicate capstone asset ID")
    if len(backend_paths) != len(set(backend_paths)):
        raise RuntimeError("Duplicate capstone backend path")
    if len(reader_paths) != len(set(reader_paths)):
        raise RuntimeError("Duplicate capstone reader path")
    return sorted(assets, key=lambda asset: capstone_asset_id(asset))


def capstone_rights_payload(assets: list[CapstoneAsset]) -> bytes:
    lines = []
    for asset in assets:
        payload = capstone_asset_payload(asset)
        source_payload = asset.source.read_bytes()
        row = {
            "asset_class": asset.category,
            "asset_id": capstone_asset_id(asset),
            "backend_path": asset.backend_rel,
            "bytes": len(payload),
            "capstone_id": f"O006-C140-CMP-{asset.capstone}",
            "companion_license": COMPANION_LICENSE,
            "dataset_license": asset.dataset_license,
            "effective_license": asset.effective_license,
            "reader_path": asset.reader_rel,
            "rights_model": asset.rights_model,
            "rights_scope": asset.rights_scope,
            "sha256": sha256(payload),
            "source_bytes": len(source_payload),
            "source_path": rel(asset.source),
            "source_sha256": sha256(source_payload),
        }
        lines.append(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    return "".join(lines).encode("utf-8")


def capstone_receipt_records() -> list[dict[str, object]]:
    if ACTIVE_BOUNDARY != "c5":
        return []
    rows: list[dict[str, object]] = []
    for capstone, spec in CAPSTONE_SPECS.items():
        transform = ROOT / "build" / str(spec["transform_receipt"])
        analysis = (
            ROOT / "generated" / "capstones" / capstone / str(spec["analysis_receipt"])
            if bool(spec["analysis_receipt_in_generated"])
            else ROOT / "build" / str(spec["analysis_receipt"])
        )
        for role, schema, path in (
            ("transform", str(spec["transform_schema"]), transform),
            ("analysis", str(spec["analysis_schema"]), analysis),
        ):
            identity = file_identity(path)
            rows.append({
                "bytes": identity["bytes"],
                "capstone": capstone,
                "path": identity["path"],
                "role": role,
                "schema": schema,
                "sha256": identity["sha256"],
            })
    return rows


def iter_generated_assets() -> list[tuple[str, Path, str]]:
    rows: list[tuple[str, Path, str]] = []
    output_paths: set[str] = set()
    for batch, directory in GENERATED_BATCHES.items():
        manifest, entries = declared_simulation_assets(batch, directory)
        for path in [manifest, *(path for _row, path in entries)]:
            output_rel = generated_output_rel(batch, path)
            if output_rel in output_paths:
                raise RuntimeError(f"Simulation output collision: {output_rel}")
            output_paths.add(output_rel)
            rows.append((batch, path, output_rel))
    return rows


def collect_static_payloads(capstone_assets: list[CapstoneAsset]) -> dict[str, bytes]:
    if (
        is_unsafe_link(MATHJAX_SOURCE)
        or not MATHJAX_SOURCE.is_dir()
        or is_unsafe_link(MATHJAX_LICENSE)
        or not MATHJAX_LICENSE.is_file()
    ):
        raise RuntimeError("Frozen local MathJax closure is missing")
    payloads: dict[str, bytes] = {"assets/style.css": STYLE.encode("utf-8")}
    for path in sorted(MATHJAX_SOURCE.rglob("*")):
        if is_unsafe_link(path):
            raise RuntimeError(f"Frozen MathJax closure contains an unsafe link: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise RuntimeError(f"Frozen MathJax closure contains an unsafe entry: {path}")
        suffix = path.relative_to(MATHJAX_SOURCE).as_posix()
        payloads[f"assets/MathJax/{suffix}"] = path.read_bytes()
    payloads["licenses/MathJax-3.1.2-LICENSE.txt"] = MATHJAX_LICENSE.read_bytes()
    for _batch, path, output_rel in iter_generated_assets():
        payloads[output_rel] = path.read_bytes()
    for batch, path in SIMULATION_RECEIPTS.items():
        if not path.is_file():
            raise RuntimeError(f"{batch.upper()} simulation receipt is missing")
        payloads[f"assets/simulations/receipts/{path.name}"] = path.read_bytes()
    for asset in capstone_assets:
        if asset.reader_rel is not None:
            payloads[asset.reader_rel] = capstone_asset_payload(asset)
    if capstone_assets:
        payloads["assets/capstones/ASSET_RIGHTS.jsonl"] = capstone_rights_payload(capstone_assets)
    return payloads


def build_payloads(documents: list[Document]) -> tuple[dict[str, bytes], dict[str, bytes], bytes]:
    external_urls, external_titles = load_external_targets()
    local_paths: dict[str, tuple[str, str | None]] = {}
    titles = dict(external_titles)
    for document in documents:
        document_id = str(document.metadata["id"])
        local_paths[document_id] = (document.output_rel, None)
        titles[document_id] = str(document.metadata["title"])
        for anchor in document.anchors:
            local_paths[anchor] = (document.output_rel, anchor)
            titles[anchor] = document.headings.get(anchor, anchor)

    for document in documents:
        for relation in normalized_relations(document):
            target = relation.get("target")
            if target not in local_paths and target not in external_urls:
                raise RuntimeError(f"Unresolved metadata relation {target} in {document.source_rel}")

    capstone_assets = collect_capstone_assets()
    c5_support_sources = list(C5_SUPPORT_SOURCES) if ACTIVE_BOUNDARY == "c5" else []
    for _source_id, source_path, _backend_rel, _role, _license_id, _rights_model in c5_support_sources:
        require_regular_file(source_path, "C5 support source")
    html_payloads = collect_static_payloads(capstone_assets)
    for document in documents:
        body_html = render_markdown(document, local_paths, titles, external_urls)
        if document.metadata["type"] == "capstone":
            body_html += capstone_artifact_index(document, capstone_assets)
        html_payloads[document.output_rel] = page_template(document, body_html, documents)

    manifest_rows = [
        {"path": path, "bytes": len(payload), "sha256": sha256(payload)}
        for path, payload in sorted(html_payloads.items())
    ]
    html_payloads["MANIFEST.csv"] = csv_payload(["path", "bytes", "sha256"], manifest_rows)

    entities: list[dict[str, object]] = []
    relations: set[tuple[str, str, str, str]] = set()
    documents_backend: list[dict[str, object]] = []
    for order, document in enumerate(documents, start=1):
        document_id = str(document.metadata["id"])
        entities.append({
            "entity_id": document_id,
            "entity_type": "document",
            "license": document.metadata["license"],
            "locale": document.metadata["locale"],
            "order": order,
            "output_path": document.output_rel,
            "provenance": document.metadata["provenance"],
            "source_path": f"source/id-ID/{document.source_rel}",
            "source_sha256": sha256(document.raw),
            "title": document.metadata["title"],
        })
        documents_backend.append({
            "anchors": len(document.anchors),
            "bytes": len(document.raw),
            "document_id": document_id,
            "output_path": document.output_rel,
            "references": len(document.references),
            "sha256": sha256(document.raw),
            "source_path": f"source/id-ID/{document.source_rel}",
            "status": document.metadata["status"],
            "title": document.metadata["title"],
            "type": document.metadata["type"],
        })
        for anchor_index, anchor in enumerate(document.anchors, start=1):
            suffix = re.search(r"-([A-Z]+)\d+$", anchor)
            entities.append({
                "document_id": document_id,
                "entity_id": anchor,
                "entity_type": suffix.group(1).lower() if suffix else "anchor",
                "locale": "id-ID",
                "order": anchor_index,
                "source_path": f"source/id-ID/{document.source_rel}",
                "title": document.headings.get(anchor, ""),
            })
            relations.add((anchor, "belongs_to", document_id, "local"))
        for relation in normalized_relations(document):
            target = str(relation["target"])
            scope = "local" if target in local_paths else "external"
            relations.add((document_id, str(relation["predicate"]), target, scope))
        for target in document.references:
            scope = "local" if target in local_paths else "external"
            if scope == "external" and target not in external_urls:
                raise RuntimeError(f"Unresolved body reference {target} in {document.source_rel}")
            relations.add((document_id, "references", target, scope))

    for batch, path, output_rel in iter_generated_assets():
        asset_id = generated_asset_id(batch, path)
        payload = path.read_bytes()
        entities.append({
            "batch": batch,
            "bytes": len(payload),
            "entity_id": asset_id,
            "entity_type": "simulation_asset",
            "license": "CC-BY-SA-4.0",
            "locale": "id-ID",
            "output_path": output_rel,
            "sha256": sha256(payload),
            "source_path": f"generated/simulations/{batch}/{path.name}",
        })
        match = re.match(r"(SIM\d{3})_", path.name)
        if match:
            relations.add((asset_id, "generated_by", f"O006-C140-CMP-{match.group(1)}", "local"))

    batch_simulations = {
        "c1": [f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 5)],
        "c2": ["O006-C140-CMP-SIM005"],
        "c3": ["O006-C140-CMP-SIM006"],
    }
    for batch, path in SIMULATION_RECEIPTS.items():
        payload = path.read_bytes()
        receipt_id = f"O006-C140-CMP-{batch.upper()}-SIM-RECEIPT"
        entities.append({
            "batch": batch,
            "bytes": len(payload),
            "entity_id": receipt_id,
            "entity_type": "simulation_receipt",
            "license": "CC-BY-SA-4.0",
            "locale": "id-ID",
            "output_path": f"assets/simulations/receipts/{path.name}",
            "sha256": sha256(payload),
            "source_path": f"build/{path.name}",
        })
        for simulation_id in batch_simulations[batch]:
            relations.add((receipt_id, "evidences", simulation_id, "local"))

    for asset in capstone_assets:
        asset_id = capstone_asset_id(asset)
        payload = capstone_asset_payload(asset)
        source_payload = asset.source.read_bytes()
        entities.append({
            "asset_class": asset.category,
            "backend_path": asset.backend_rel,
            "bytes": len(payload),
            "capstone_id": f"O006-C140-CMP-{asset.capstone}",
            "dataset_license": asset.dataset_license,
            "entity_id": asset_id,
            "entity_type": f"capstone_{asset.category}",
            "license": asset.effective_license,
            "locale": "und" if asset.category == "clean_data" else "id-ID",
            "output_path": asset.reader_rel or asset.backend_rel,
            "reader_path": asset.reader_rel,
            "rights_model": asset.rights_model,
            "rights_scope": asset.rights_scope,
            "sha256": sha256(payload),
            "source_bytes": len(source_payload),
            "source_path": rel(asset.source),
            "source_sha256": sha256(source_payload),
        })
        relations.add((asset_id, "supports", f"O006-C140-CMP-{asset.capstone}", "local"))

    rights_payload = capstone_rights_payload(capstone_assets) if capstone_assets else b""
    if capstone_assets:
        rights_id = "O006-C140-CMP-C5-ASSET-RIGHTS"
        entities.append({
            "bytes": len(rights_payload),
            "entity_id": rights_id,
            "entity_type": "capstone_rights_metadata",
            "license": COMPANION_LICENSE,
            "locale": "id-ID",
            "output_path": "assets/capstones/ASSET_RIGHTS.jsonl",
            "sha256": sha256(rights_payload),
            "source_path": "generated-by-build",
        })
        for capstone in CAPSTONE_SPECS:
            relations.add((rights_id, "documents_rights_of", f"O006-C140-CMP-{capstone}", "local"))

    for source_id, source_path, backend_rel, role, license_id, rights_model in c5_support_sources:
        payload = source_path.read_bytes()
        source_rel = source_path.relative_to(REPO).as_posix()
        entities.append({
            "bytes": len(payload),
            "entity_id": source_id,
            "entity_type": "build_support_source",
            "license": license_id,
            "locale": "und",
            "output_path": backend_rel,
            "rights_model": rights_model,
            "role": role,
            "sha256": sha256(payload),
            "source_path": source_rel,
        })
        relations.add((source_id, "supports", "O006-C140-CMP-INDEX", "local"))

    entity_lines = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in sorted(entities, key=lambda row: str(row["entity_id"])))
    relation_rows = [
        {"subject": subject, "predicate": predicate, "object": obj, "scope": scope}
        for subject, predicate, obj, scope in sorted(relations)
    ]
    document_lines = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in documents_backend)
    backend_payloads = {
        "entities.jsonl": entity_lines.encode("utf-8"),
        "relations.csv": csv_payload(["subject", "predicate", "object", "scope"], relation_rows),
        "documents.jsonl": document_lines.encode("utf-8"),
    }
    for asset in capstone_assets:
        backend_payloads[asset.backend_rel] = capstone_asset_payload(asset)
    if capstone_assets:
        backend_payloads["capstone_asset_rights.jsonl"] = rights_payload
    for _source_id, source_path, backend_rel, _role, _license_id, _rights_model in c5_support_sources:
        backend_payloads[backend_rel] = source_path.read_bytes()
    backend_manifest_rows = [
        {"path": path, "bytes": len(payload), "sha256": sha256(payload)}
        for path, payload in sorted(backend_payloads.items())
    ]
    backend_payloads["MANIFEST.csv"] = csv_payload(["path", "bytes", "sha256"], backend_manifest_rows)

    source_rows = [
        {"path": f"source/id-ID/{document.source_rel}", "bytes": len(document.raw), "sha256": sha256(document.raw)}
        for document in documents
    ]
    receipt = canonical_json({
        "backend": {
            "bytes": sum(len(value) for value in backend_payloads.values()),
            "entities": len(entities),
            "files": len(backend_payloads),
            "manifest_sha256": sha256(backend_payloads["MANIFEST.csv"]),
            "relations": len(relation_rows),
        },
        "browser_processes_used": False,
        "boundary": f"cumulative-through-{ACTIVE_BOUNDARY}",
        **({
            "capstones": [
                {
                    "assets": sum(1 for asset in capstone_assets if asset.capstone == capstone),
                    "backend_bytes": sum(
                        len(capstone_asset_payload(asset))
                        for asset in capstone_assets
                        if asset.capstone == capstone
                    ),
                    "dataset_license": str(CAPSTONE_SPECS[capstone]["dataset_license"]),
                    "document_id": f"O006-C140-CMP-{capstone}",
                    "reader_assets": sum(
                        1
                        for asset in capstone_assets
                        if asset.capstone == capstone and asset.reader_rel is not None
                    ),
                    "source_scripts": sum(
                        1
                        for asset in capstone_assets
                        if asset.capstone == capstone and asset.category == "source_script"
                    ),
                }
                for capstone in CAPSTONE_SPECS
            ],
            "rights_metadata_sha256": sha256(rights_payload),
            "capstone_receipts": capstone_receipt_records(),
            "public_derivatives": [cp02_coverage_derivative_record()],
            "witness_redactions": [cp02_redaction_record()],
        } if capstone_assets else {}),
        "cumulative_documents": len(documents),
        "cumulative_required_ids": sorted(active_required_ids()),
        "environment": file_identity(ENVIRONMENT_LOCK),
        "html": {
            "bytes": sum(len(value) for value in html_payloads.values()),
            "files": len(html_payloads),
            "manifest_sha256": sha256(html_payloads["MANIFEST.csv"]),
        },
        "network_access": False,
        "schema": f"o006.c140.companion-cumulative-{ACTIVE_BOUNDARY}-build.v1",
        "simulation_receipts": [
            {
                "batch": batch,
                "bytes": path.stat().st_size,
                "path": f"build/{path.name}",
                "sha256": sha256(path.read_bytes()),
            }
            for batch, path in SIMULATION_RECEIPTS.items()
        ],
        **({
            "support_sources": c5_support_source_records(),
        } if c5_support_sources else {}),
        "source": source_rows,
        "status": "pass",
        "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
    })
    return html_payloads, backend_payloads, receipt


def write_payloads(target: Path, payloads: dict[str, bytes]) -> None:
    """Stage a complete tree, verify it, then replace the fixed live tree."""
    if target not in {HTML_TARGET, BACKEND_TARGET}:
        raise RuntimeError(f"Refusing undeclared output tree: {target}")
    prepare_safe_directory(target.parent, ROOT)
    if is_unsafe_link(target) or (target.exists() and not target.is_dir()):
        raise RuntimeError(f"Output tree target is unsafe: {target}")
    if target.is_dir():
        for existing in target.rglob("*"):
            relative = existing.relative_to(target).as_posix()
            if is_unsafe_link(existing):
                raise RuntimeError(f"Refusing to replace output tree with unsafe link: {relative}")
            if not existing.is_dir() and not existing.is_file():
                raise RuntimeError(f"Refusing to replace output tree with unsafe entry: {relative}")

    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=target.parent))
    backup: Path | None = None
    old_moved = False
    new_installed = False
    try:
        for name, payload in sorted(payloads.items()):
            relative = validate_payload_name(name)
            path = staging.joinpath(*relative.parts)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            if path.read_bytes() != payload:
                raise RuntimeError(f"Staged output readback differs: {name}")
        staged_errors = compare_payloads(staging, payloads)
        if staged_errors:
            raise RuntimeError("Staged output verification failed: " + ", ".join(staged_errors[:40]))

        if target.exists():
            backup = Path(tempfile.mkdtemp(prefix=f".{target.name}.previous-", dir=target.parent))
            backup.rmdir()
            os.replace(target, backup)
            old_moved = True
        os.replace(staging, target)
        new_installed = True
    except Exception:
        if old_moved and not new_installed and backup is not None and backup.exists():
            os.replace(backup, target)
            old_moved = False
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    if old_moved and backup is not None and backup.exists():
        shutil.rmtree(backup)


def compare_payloads(target: Path, payloads: dict[str, bytes]) -> list[str]:
    expected = set(payloads)
    for name in expected:
        validate_payload_name(name)
    if is_unsafe_link(target) or (target.exists() and not target.is_dir()):
        return ["unsafe:output-root"]
    actual: set[str] = set()
    unsafe: list[str] = []
    if target.is_dir():
        for path in target.rglob("*"):
            relative = path.relative_to(target).as_posix()
            if is_unsafe_link(path):
                unsafe.append(f"unsafe:{relative}")
            elif path.is_file():
                actual.add(relative)
            elif not path.is_dir():
                unsafe.append(f"unsafe:{relative}")
    errors = [f"missing:{name}" for name in sorted(expected - actual)]
    errors.extend(f"extra:{name}" for name in sorted(actual - expected))
    errors.extend(sorted(unsafe))
    for name in sorted(expected & actual):
        if target.joinpath(*PurePosixPath(name).parts).read_bytes() != payloads[name]:
            errors.append(f"mismatch:{name}")
    return errors


def main() -> None:
    global ACTIVE_BOUNDARY, RECEIPT_TARGET
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    boundary = parser.add_mutually_exclusive_group()
    boundary.add_argument("--c4", action="store_true", help="build the cumulative MS00-MS06 boundary")
    boundary.add_argument("--c5", action="store_true", help="build the cumulative assessment/capstone boundary")
    args = parser.parse_args()

    if args.c4:
        ACTIVE_BOUNDARY = "c4"
        RECEIPT_TARGET = ROOT / "build" / active_receipt_name()
    elif args.c5:
        ACTIVE_BOUNDARY = "c5"
        RECEIPT_TARGET = ROOT / "build" / active_receipt_name()

    documents = load_documents()
    html_payloads, backend_payloads, receipt = build_payloads(documents)
    if args.write:
        write_payloads(HTML_TARGET, html_payloads)
        write_payloads(BACKEND_TARGET, backend_payloads)
        atomic_write_file(RECEIPT_TARGET, receipt)
        mode_name = "written"
    else:
        errors = compare_payloads(HTML_TARGET, html_payloads)
        errors.extend(f"backend/{item}" for item in compare_payloads(BACKEND_TARGET, backend_payloads))
        if not RECEIPT_TARGET.is_file():
            errors.append(f"missing:{active_receipt_name()}")
        elif RECEIPT_TARGET.read_bytes() != receipt:
            errors.append(f"mismatch:{active_receipt_name()}")
        if errors:
            raise RuntimeError("Deterministic replay failed: " + ", ".join(errors[:40]))
        mode_name = "verified"
    print(json.dumps({
        "backend_files": len(backend_payloads),
        "documents": len(documents),
        "html_files": len(html_payloads),
        "mode": mode_name,
        "receipt_sha256": sha256(receipt),
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
