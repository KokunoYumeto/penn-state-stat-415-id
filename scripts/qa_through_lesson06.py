#!/usr/bin/env python3
"""Deterministic cumulative QA for the 8-of-14 STAT 415 id-ID reader."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup

import build_through_lesson01 as shared
import build_through_lesson05 as prior_builder
import build_through_lesson06 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON06_QA_RECEIPT.json"
TRANSLATION = ROOT / "source" / "id-ID" / "lesson06_translation.csv"
TEMPLATE = ROOT / "working" / "lesson06_segments.csv"
BINDINGS = ROOT / "backend" / "lesson06_translation_bindings.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson06_corrections.jsonl"
PRIOR_CORRECTIONS = ROOT / "backend" / "through_lesson05_corrections.jsonl"
DOCUMENTS = ROOT / "backend" / "through_lesson06_documents.jsonl"
MANIFEST = ROOT / "build" / "THROUGH_LESSON06_MANIFEST.csv"
SOURCE = ROOT / "source" / "normalized" / "en-US" / "Lesson06.html"
TARGET = ROOT / "source" / "id-ID" / "Lesson06.html"
ASSET_CLOSURE = ROOT / "working" / "lesson06_asset_closure.json"
SOURCE_ASSET = ROOT / "authority" / "assets" / "stat415" / "lesson06" / "assets" / "ci_1.png"

DOCUMENT_COUNTS = {
    "index": (197, 0),
    "Lesson00": (363, 331),
    "Lesson01": (188, 169),
    "Lesson02": (228, 209),
    "Lesson03": (421, 440),
    "Lesson04": (335, 289),
    "Lesson05": (1_475, 108),
    "Lesson06": (149, 102),
}
DOCUMENT_IDS = {
    "index": "O006-PSU-000",
    "Lesson00": "O006-PSU-001",
    "Lesson01": "O006-PSU-002",
    "Lesson02": "O006-PSU-003",
    "Lesson03": "O006-PSU-004",
    "Lesson04": "O006-PSU-005",
    "Lesson05": "O006-PSU-006",
    "Lesson06": "O006-PSU-007",
}
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_FIELDS = [
    "segment_id", "document_id", "component_id", "section_id",
    "source_sha256", "source_text", "target_text", "status",
]
EXPECTED_REQUIRED_TERMS = (
    "selang kepercayaan",
    "koefisien kepercayaan",
    "tingkat kepercayaan",
    "pendugaan selang",
    "besaran pivot",
    "nilai kritis",
    "fungsi pembangkit momen",
    "selang-z",
    "galat baku",
    "distribusi khi-kuadrat",
    "derajat kebebasan",
    "peluang ekor bawah",
    "konvergen dalam distribusi",
    "studentisasi",
    "ketakbiasan eksak tidak diperlukan",
    "saling bebas dan berdistribusi identik (iid)",
    "df = n − 1",
)
EXPECTED_FORBIDDEN_TERMS = (
    "interval kepercayaan",
    "interval konfidensi",
    "kuantitas pivotal",
    "standard error",
    "confidence interval",
)
EXPECTED_ASSET_ID = "O006-PSU-007-A0001"
EXPECTED_ASSET_BYTES = 67_496
EXPECTED_ASSET_SHA256 = "2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f"
EXPECTED_READER_ASSET = PurePosixPath("assets/lesson06/ci_1.png")
EXPECTED_ALT_TEXT = (
    "Kurva normal baku: luas tengah 1−α berada di antara nilai kritis tetap "
    "−z_(α/2) dan +z_(α/2); masing-masing ekor kiri dan kanan memiliki luas α/2."
)
EXPECTED_FIGURE_NOTE = (
    "Catatan koreksi Gambar 6.1: kedua titik batas adalah nilai kritis tetap "
    "−z_(α/2) dan +z_(α/2) (z huruf kecil), bukan peubah acak Z; "
    "masing-masing ekor mempunyai peluang α/2."
)
EXPECTED_CHANGED_MATH = {
    "O006-PSU-007-M0042",
    "O006-PSU-007-M0073",
    "O006-PSU-007-M0074",
    "O006-PSU-007-M0075",
    "O006-PSU-007-M0077",
    "O006-PSU-007-M0086",
    "O006-PSU-007-M0087",
    "O006-PSU-007-M0098",
    "O006-PSU-007-M0102",
}
EXPECTED_CORRECTION_SURFACE_KINDS = {
    "adjacent-correction-note", "attribute", "math", "semantic-role",
    "translation-segment",
}


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


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": sha256(data)}


def load_jsonl(path: Path) -> list[dict[str, object]]:
    try:
        rows = [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSONL {path.relative_to(ROOT)}: {exc}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"non-object JSONL row: {path.relative_to(ROOT)}")
    return rows


def load_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    data = path.read_bytes()
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
    return list(reader.fieldnames or []), list(reader)


def boundary(text: str) -> tuple[str, str]:
    leading = re.match(r"^\s*", text)
    trailing = re.search(r"\s*$", text)
    assert leading is not None and trailing is not None
    return leading.group(0), trailing.group(0)


def deterministic_build_gate() -> tuple[
    dict[str, bytes], dict[str, object], set[PurePosixPath]
]:
    outputs, receipt, reader_files = builder.compute()
    for relative, expected in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != expected:
            raise RuntimeError(f"deterministic Lesson06 build differs: {relative}")
    actual = shared.current_reader_files()
    if actual != reader_files:
        raise RuntimeError(
            f"reader inventory differs: extra={sorted(actual-reader_files)} "
            f"missing={sorted(reader_files-actual)}"
        )
    coverage = receipt.get("coverage", {})
    math = receipt.get("math_nodes", {})
    corrections = receipt.get("corrections", {})
    reader = receipt.get("reader", {})
    assets = receipt.get("lesson06_assets", {})
    layout = receipt.get("layout", {})
    rights = receipt.get("rights", {})
    if (
        receipt.get("schema") != "o006.stat415.through-lesson06-build.v1"
        or receipt.get("status") != "built"
        or coverage.get("complete_count") != 8
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson07"
        or receipt.get("translation_segments") != 2_487
        or receipt.get("structural_units_normalized") != 3_358
        or receipt.get("structural_units_target") != 3_356
        or math.get("Lesson06") != 102
        or math.get("total") != 1_648
        or corrections.get("count") != 122
        or corrections.get("through_lesson05_count") != 112
        or corrections.get("lesson06_count") != 10
        or reader.get("files") != 52
        or len(reader_files) != 52
        or assets.get("count") != 1
        or assets.get("bytes") != EXPECTED_ASSET_BYTES
        or assets.get("authority_slots") != 1
        or assets.get("authority_bytes") != EXPECTED_ASSET_BYTES
        or assets.get("byte_preserving_targets") != 1
        or assets.get("inline_width_constraints_removed") != 1
        or layout.get("reader_css_path") != "assets/reader-8of14.css"
        or rights.get("Penn State content") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
    ):
        raise RuntimeError("Lesson06 build receipt contract differs")
    offline = receipt.get("offline", {})
    if (
        offline.get("external_runtime_requests") != 0
        or offline.get("analytics") is not False
        or offline.get("cookies") is not False
        or offline.get("local_mathjax") is not True
        or offline.get("third_party_iframes") != 0
    ):
        raise RuntimeError("Lesson06 privacy/offline build contract differs")
    return outputs, receipt, reader_files


def translation_gate() -> dict[str, object]:
    template_fields, template = load_csv(TEMPLATE)
    target_fields, target = load_csv(TRANSLATION)
    if (
        template_fields != EXPECTED_FIELDS
        or target_fields != EXPECTED_FIELDS
        or len(template) != 176
        or len(target) != 176
    ):
        raise RuntimeError("Lesson06 translation CSV schema/census differs")
    bindings = load_jsonl(BINDINGS)
    if len(bindings) != 176:
        raise RuntimeError("Lesson06 translation binding census differs")

    identical: set[str] = set()
    all_target: list[str] = []
    for ordinal, (source, row, binding_row) in enumerate(zip(template, target, bindings), start=1):
        sid = f"O006-PSU-007-S{ordinal:04d}"
        if row["segment_id"] != sid or source["segment_id"] != sid:
            raise RuntimeError(f"Lesson06 translation order differs: {sid}")
        for field in ("document_id", "component_id", "section_id", "source_sha256", "source_text"):
            if row[field] != source[field]:
                raise RuntimeError(f"Lesson06 immutable translation field differs: {sid}: {field}")
        target_text = row["target_text"]
        if (
            row["status"] != "translated"
            or not target_text.strip()
            or "\ufffd" in target_text
            or "<" in target_text
            or ">" in target_text
        ):
            raise RuntimeError(f"Lesson06 target surface invalid: {sid}")
        if boundary(target_text) != boundary(source["source_text"]):
            raise RuntimeError(f"Lesson06 target boundary differs: {sid}")
        if source["source_text"] == target_text:
            identical.add(sid)
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": sid,
            "document_id": "O006-PSU-007",
            "component_id": "Lesson06",
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": sha256(target_text.encode("utf-8")),
            "status": "translated",
        }
        if binding_row != expected_binding:
            raise RuntimeError(f"Lesson06 backend binding differs: {sid}")
        all_target.append(target_text)
    if identical:
        raise RuntimeError(f"Lesson06 untranslated/identity surfaces remain: {sorted(identical)}")

    joined = "\n".join(all_target).casefold()
    missing = [term for term in EXPECTED_REQUIRED_TERMS if term.casefold() not in joined]
    present = [term for term in EXPECTED_FORBIDDEN_TERMS if term.casefold() in joined]
    if missing or present:
        raise RuntimeError(f"Lesson06 language/terminology gate differs: missing={missing} forbidden={present}")
    return {
        "segments": len(target),
        "bindings": len(bindings),
        "identical_segments": [],
        "required_terms": list(EXPECTED_REQUIRED_TERMS),
        "forbidden_surfaces_absent": list(EXPECTED_FORBIDDEN_TERMS),
        "translation": identity(TRANSLATION),
        "bindings_file": identity(BINDINGS),
    }


def correction_surface_gate(
    target_main: object,
    translation_by_id: dict[str, dict[str, str]],
    surface: dict[str, object],
) -> None:
    kind = surface.get("surface")
    expected_hash = surface.get("target_surface_sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise RuntimeError(f"Lesson06 correction target hash missing: {surface}")
    if kind == "math":
        nodes = target_main.select(f'[data-o006-math-id="{surface.get("math_id")}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson06 correction math surface missing: {surface.get('math_id')}")
        actual = nodes[0].get_text().encode("utf-8")
    elif kind == "structural-unit-text":
        nodes = target_main.select(f'[data-o006-id="{surface.get("unit_id")}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson06 correction unit surface missing: {surface.get('unit_id')}")
        actual = nodes[0].get_text().encode("utf-8")
    elif kind == "translation-segment":
        row = translation_by_id.get(str(surface.get("segment_id")))
        if row is None:
            raise RuntimeError(
                f"Lesson06 correction translation surface missing: {surface.get('segment_id')}"
            )
        actual = row["target_text"].encode("utf-8")
    elif kind == "asset":
        path_value = surface.get("target_path")
        if not isinstance(path_value, str):
            raise RuntimeError("Lesson06 correction asset path missing")
        path = ROOT / path_value
        if not path.is_file():
            raise RuntimeError(f"Lesson06 correction asset missing: {path_value}")
        actual = path.read_bytes()
    elif kind == "attribute":
        if surface.get("asset_id") is not None:
            nodes = target_main.select(
                f'[data-o006-asset-id="{surface.get("asset_id")}"]'
            )
        else:
            nodes = target_main.select(f'[data-o006-id="{surface.get("unit_id")}"]')
        attribute = surface.get("attribute")
        if len(nodes) != 1 or not isinstance(attribute, str):
            raise RuntimeError(f"Lesson06 attribute surface missing: {surface}")
        value = nodes[0].get(attribute)
        if not isinstance(value, str):
            raise RuntimeError(f"Lesson06 attribute missing: {surface}:{attribute}")
        actual = value.encode("utf-8")
    elif kind == "adjacent-correction-note":
        unit_id = str(surface.get("unit_id"))
        asset_id = str(surface.get("asset_id"))
        figures = target_main.select(f'[data-o006-id="{unit_id}"]')
        images = target_main.select(f'img[data-o006-asset-id="{asset_id}"]')
        notes = target_main.select('[data-o006-correction-id="O006-PSU-ADV-0115"]')
        if len(figures) != 1 or len(images) != 1 or len(notes) != 1:
            raise RuntimeError("Lesson06 adjacent figure correction note is missing")
        following = notes[0].find_next_sibling()
        if following is None:
            raise RuntimeError("Lesson06 adjacent figure correction boundary is missing")
        source_marker = "\n".join(
            (unit_id, asset_id, "assets/ci_1.png", str(following.get("data-o006-id")))
        )
        actual = (source_marker + "\n" + str(notes[0])).encode("utf-8")
    elif kind == "semantic-role":
        nodes = target_main.select(f'[data-o006-id="{surface.get("unit_id")}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson06 semantic-role unit missing: {surface.get('unit_id')}")
        if (
            nodes[0].get("data-o006-semantic-role") != surface.get("semantic_role")
            or list(nodes[0].get("class", [])) != surface.get("target_class")
            or surface.get("content_unchanged") is not True
        ):
            raise RuntimeError(f"Lesson06 semantic-role attribute missing: {surface.get('unit_id')}")
        actual = str(nodes[0]).encode("utf-8")
    else:
        raise RuntimeError(f"unknown Lesson06 correction surface: {kind}")
    if sha256(actual) != expected_hash:
        raise RuntimeError(f"Lesson06 correction target hash differs: {kind}")


def structure_math_and_corrections_gate() -> dict[str, object]:
    rows = load_jsonl(CORRECTIONS)
    prior_rows = load_jsonl(PRIOR_CORRECTIONS)
    if len(rows) != 122 or len(prior_rows) != 112 or rows[:112] != prior_rows:
        raise RuntimeError("historical correction prefix differs")
    lesson_rows = rows[112:]
    if [row.get("correction_id") for row in lesson_rows] != [
        f"O006-PSU-ADV-{i:04d}" for i in range(113, 123)
    ]:
        raise RuntimeError("Lesson06 correction ID sequence differs")
    if [row.get("source_defect_id") for row in lesson_rows] != [
        f"L06-D{i:03d}" for i in range(1, 11)
    ]:
        raise RuntimeError("Lesson06 defect binding sequence differs")
    if any(row.get("status") != "applied-target-only" for row in lesson_rows):
        raise RuntimeError("Lesson06 correction status differs")

    source_soup = BeautifulSoup(SOURCE.read_bytes(), "html.parser")
    target_soup = BeautifulSoup(TARGET.read_bytes(), "html.parser")
    source = source_soup.select_one("main#quarto-document-content")
    target = target_soup.select_one("main#quarto-document-content")
    if source is None or target is None:
        raise RuntimeError("Lesson06 semantic main missing")
    expected_units = [f"O006-PSU-007-U{i:04d}" for i in range(1, 150)]
    expected_math = [f"O006-PSU-007-M{i:04d}" for i in range(1, 103)]
    source_units = shared.stable_values(source, "data-o006-id")
    target_units = shared.stable_values(target, "data-o006-id")
    source_math_ids = shared.stable_values(source, "data-o006-math-id")
    target_math_ids = shared.stable_values(target, "data-o006-math-id")
    if source_units != expected_units or target_units != expected_units:
        raise RuntimeError("Lesson06 stable-unit topology differs")
    if source_math_ids != expected_math or target_math_ids != expected_math:
        raise RuntimeError("Lesson06 math topology differs")
    changed = {
        sid
        for sid, before, after in zip(source_math_ids, source.select(".math"), target.select(".math"))
        if before.get_text() != after.get_text()
    }
    registered = {
        str(surface["math_id"])
        for row in lesson_rows
        for surface in row.get("surfaces", [])
        if surface.get("surface") == "math"
    }
    if changed != registered or changed != EXPECTED_CHANGED_MATH:
        raise RuntimeError(
            f"Lesson06 changed-math registry differs: changed={sorted(changed)} "
            f"registered={sorted(registered)}"
        )

    _, translation_rows = load_csv(TRANSLATION)
    translation_by_id = {row["segment_id"]: row for row in translation_rows}
    seen_surface_kinds: set[str] = set()
    for row in lesson_rows:
        surfaces = row.get("surfaces")
        if not isinstance(surfaces, list) or not surfaces or row.get("replacement_count") != len(surfaces):
            raise RuntimeError(
                f"Lesson06 correction replacement census differs: {row.get('correction_id')}"
            )
        expected_row_surface = surfaces[0].get("surface") if len(surfaces) == 1 else "multiple"
        if row.get("surface") != expected_row_surface:
            raise RuntimeError(
                f"Lesson06 correction surface summary differs: {row.get('correction_id')}"
            )
        for surface in surfaces:
            kind = surface.get("surface")
            if isinstance(kind, str):
                seen_surface_kinds.add(kind)
            correction_surface_gate(target, translation_by_id, surface)
    if seen_surface_kinds != EXPECTED_CORRECTION_SURFACE_KINDS:
        raise RuntimeError(
            f"Lesson06 correction surface-kind closure differs: {sorted(seen_surface_kinds)}"
        )

    proofs = target.select("section#proof")
    if len(proofs) != 1:
        raise RuntimeError("Lesson06 complete proof section census differs")
    proof = proofs[0]
    if (
        proof.get("data-o006-semantic-role") != "proof"
        or proof.get("data-o006-correction-id") != "O006-PSU-ADV-0122"
        or "proof" not in set(proof.get("class") or [])
    ):
        raise RuntimeError("Lesson06 proof semantic role is missing")
    proof_math = shared.stable_values(proof, "data-o006-math-id")
    if proof_math != [f"O006-PSU-007-M{i:04d}" for i in range(38, 47)]:
        raise RuntimeError("Lesson06 proof math boundary differs")
    if "Bukti:" not in proof.get_text(" ", strip=True):
        raise RuntimeError("Lesson06 proof heading is missing")

    examples = target.select("div.theorem.example")
    if len(examples) != 2 or [node.get("id") for node in examples] != [
        "exm-gammadistci", "exm-cisupermarket"
    ]:
        raise RuntimeError("Lesson06 worked-example topology differs")
    solutions = target.select("section#solution")
    if len(solutions) != 1 or "Penyelesaian" not in solutions[0].get_text(" ", strip=True):
        raise RuntimeError("Lesson06 Solution topology differs")
    if target.select("pre, code, .cell, .sourceCode"):
        raise RuntimeError("Lesson06 unexpectedly contains code")
    if target.select("script, iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson06 target retains an executable/external dependency")
    if shared.native_id_duplicates(target):
        raise RuntimeError(
            f"Lesson06 target retains duplicate native IDs: {shared.native_id_duplicates(target)}"
        )

    target_text = target.get_text(" ", strip=False)
    required_prose = (
        "subskrip p pada kuantil khi-kuadrat menyatakan peluang ekor bawah p",
        "Taksiran galat baku rataan sampel adalah 2",
        "konvergen dalam distribusi ke distribusi normal baku",
        "hasil studentisasi yang ekuivalen",
        "ketakbiasan eksak tidak diperlukan",
        "saling bebas dan berdistribusi identik (iid)",
        "df = n − 1",
    )
    missing_prose = [value for value in required_prose if value not in target_text]
    if missing_prose:
        raise RuntimeError(f"Lesson06 required clarification differs: missing={missing_prose}")
    notes = target.select('[data-o006-correction-id="O006-PSU-ADV-0115"]')
    if (
        len(notes) != 1
        or notes[0].get("role") != "note"
        or notes[0].get_text() != EXPECTED_FIGURE_NOTE
    ):
        raise RuntimeError("Lesson06 lowercase-z critical-value correction note differs")

    math_by_id = {
        str(node.get("data-o006-math-id")): node.get_text() for node in target.select(".math")
    }
    if "=1-\\alpha" not in re.sub(r"\s+", "", math_by_id["O006-PSU-007-M0042"]):
        raise RuntimeError("Lesson06 proof equality correction is missing")
    se_math = re.sub(r"\s+", "", math_by_id["O006-PSU-007-M0098"])
    if "=2" not in se_math or "=256" in se_math or "\\hat{\\sigma}^2" in se_math:
        raise RuntimeError("Lesson06 corrected SE=2 math differs")
    t_math = re.sub(r"\s+", "", math_by_id["O006-PSU-007-M0102"])
    if "n-1" not in t_math or ",df" in t_math:
        raise RuntimeError("Lesson06 exact iid-Normal t interval df differs")

    finding_ids = re.findall(
        r"^## (L06-D\d{3})\b",
        (ROOT / "working" / "lesson06_source_findings.md").read_text("utf-8"),
        re.MULTILINE,
    )
    if finding_ids != [f"L06-D{i:03d}" for i in range(1, 11)]:
        raise RuntimeError("Lesson06 source-finding registry differs")
    return {
        "source_units": len(source_units),
        "target_units": len(target_units),
        "math_nodes": len(target_math_ids),
        "corrections": len(rows),
        "historical_prefix": len(prior_rows),
        "lesson06_corrections": len(lesson_rows),
        "changed_math_nodes": len(changed),
        "changed_math_ids": sorted(changed),
        "surface_kinds": sorted(seen_surface_kinds),
        "proofs": len(proofs),
        "examples": len(examples),
        "solutions": len(solutions),
        "code_nodes": 0,
        "external_dependencies": 0,
        "correction_backend": identity(CORRECTIONS),
    }


def reader_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    total_math = 0
    total_units = 0
    for component, (expected_units, expected_math) in DOCUMENT_COUNTS.items():
        path = BUILD / f"{component}.html"
        payload = path.read_bytes()
        markup = payload.decode("utf-8")
        soup = BeautifulSoup(payload, "html.parser")
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"reader locale differs: {component}")
        if component != "index" and soup.select_one('meta[name="translation-provenance"]') is None:
            raise RuntimeError(f"reader provenance metadata missing: {component}")
        if soup.select_one('link[href="assets/reader-8of14.css"]') is None:
            raise RuntimeError(f"reader stylesheet route differs: {component}")
        main = soup.select_one("main#quarto-document-content")
        if main is None:
            raise RuntimeError(f"reader semantic main missing: {component}")
        units = shared.stable_values(main, "data-o006-id")
        maths = shared.stable_values(main, "data-o006-math-id")
        if len(units) != expected_units or len(maths) != expected_math:
            raise RuntimeError(f"reader stable-ID census differs: {component}")
        document_id = DOCUMENT_IDS[component]
        if expected_math and maths != [
            f"{document_id}-M{i:04d}" for i in range(1, expected_math + 1)
        ]:
            raise RuntimeError(f"reader math sequence differs: {component}")
        duplicates = shared.native_id_duplicates(main)
        if duplicates:
            raise RuntimeError(f"reader duplicate native IDs remain: {component}: {duplicates}")
        for math_node in main.select(".math"):
            text = math_node.get_text()
            if re.search(r"\\n(?=\s|\\end)", text) or text.count("{") != text.count("}"):
                raise RuntimeError(f"malformed target TeX surface: {math_node.get('data-o006-math-id')}")
            if text.count(r"\begin{align") != text.count(r"\end{align"):
                raise RuntimeError(
                    f"unbalanced align environment: {math_node.get('data-o006-math-id')}"
                )
        if "googletagmanager" in markup or "site_libs/" in markup:
            raise RuntimeError(f"tracking/upstream runtime leaked: {component}")
        if soup.select('script[src^="http"], iframe, object, embed, audio, video'):
            raise RuntimeError(f"external/embedded runtime remains: {component}")
        for image in main.select("img"):
            if not str(image.get("alt", "")).strip():
                raise RuntimeError(f"reader image lacks alt text: {component}")
        total_math += len(maths)
        total_units += len(units)
    if total_math != 1_648 or total_units != 3_356:
        raise RuntimeError("reader cumulative stable-ID census differs")

    license_soup = BeautifulSoup((BUILD / "licenses" / "index.html").read_bytes(), "html.parser")
    if license_soup.select_one('link[href="../assets/reader-8of14.css"]') is None:
        raise RuntimeError("license stylesheet route differs")
    license_text = license_soup.get_text(" ", strip=True)
    for required in (
        "CC BY-NC 4.0", "MathJax 3.1.2", PROVENANCE,
        "tiga puluh satu koreksi Lesson 05", "sepuluh koreksi Lesson 06",
    ):
        if required not in license_text:
            raise RuntimeError(f"license/change notice missing: {required}")
    reader_payloads = {path: (BUILD / Path(path.as_posix())).read_bytes() for path in reader_files}
    shared.validate_reader_links(reader_payloads)

    manifest_fields, manifest_rows = load_csv(MANIFEST)
    if manifest_fields != ["relative_path", "bytes", "sha256"] or len(manifest_rows) != 52:
        raise RuntimeError("reader manifest schema/census differs")
    expected_manifest = {
        path.as_posix(): (len(payload), sha256(payload)) for path, payload in reader_payloads.items()
    }
    actual_manifest = {
        row["relative_path"]: (int(row["bytes"]), row["sha256"]) for row in manifest_rows
    }
    if actual_manifest != expected_manifest:
        raise RuntimeError("reader manifest identity differs")
    return {
        "files": len(reader_files),
        "bytes": sum(value[0] for value in expected_manifest.values()),
        "stable_units": total_units,
        "math_nodes": total_math,
        "manifest": identity(MANIFEST),
    }


def asset_layout_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    closure = json.loads(ASSET_CLOSURE.read_text("utf-8"))
    asset = closure.get("asset")
    rights = closure.get("rights")
    dependency = closure.get("dependency_census")
    closed = closure.get("closure")
    if (
        closure.get("schema") != "o006.stat415.lesson06-asset-closure.v1"
        or closure.get("status") != "same-origin-image-closed-no-external-dependencies"
        or closure.get("document_id") != "O006-PSU-007"
        or not isinstance(asset, dict)
        or asset.get("asset_id") != EXPECTED_ASSET_ID
        or asset.get("bytes") != EXPECTED_ASSET_BYTES
        or asset.get("sha256") != EXPECTED_ASSET_SHA256
        or asset.get("img_occurrences") != 1
        or asset.get("lightbox_href_occurrences") != 1
        or not isinstance(dependency, dict)
        or any(int(dependency.get(name, -1)) != 0 for name in (
            "audio", "downloads", "embeds", "iframes", "media_sources",
            "objects", "scripts", "videos",
        ))
        or not isinstance(closed, dict)
        or closed.get("external_dependencies") != 0
        or closed.get("unresolved_asset_bytes") != 0
        or not isinstance(rights, dict)
        or rights.get("page_license") != "CC BY-NC 4.0"
        or rights.get("per_asset_exception_in_main") is not False
    ):
        raise RuntimeError("Lesson06 source asset/rights closure contract differs")

    source_payload = SOURCE_ASSET.read_bytes()
    if len(source_payload) != EXPECTED_ASSET_BYTES or sha256(source_payload) != EXPECTED_ASSET_SHA256:
        raise RuntimeError("Lesson06 authority PNG identity differs")
    target_path = BUILD.joinpath(*EXPECTED_READER_ASSET.parts)
    target_payload = target_path.read_bytes()
    if target_payload != source_payload or not target_payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("Lesson06 reader PNG bytes differ")

    lesson = BeautifulSoup((BUILD / "Lesson06.html").read_bytes(), "html.parser")
    main = lesson.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson06 reader main missing for asset/layout gate")
    images = main.select(f'img[data-o006-asset-id="{EXPECTED_ASSET_ID}"]')
    if len(images) != 1:
        raise RuntimeError("Lesson06 reader image census differs")
    image = images[0]
    if image.get("src") != EXPECTED_READER_ASSET.as_posix():
        raise RuntimeError("Lesson06 reader image route differs")
    if image.get("style") is not None or image.get("width") is not None:
        raise RuntimeError("Lesson06 reader image retains an inline width constraint")
    if len(main.select(f'a.lightbox[href="{EXPECTED_READER_ASSET.as_posix()}"]')) != 1:
        raise RuntimeError("Lesson06 reader lightbox route differs")
    alt = str(image.get("alt") or "")
    if alt != EXPECTED_ALT_TEXT:
        raise RuntimeError(f"Lesson06 full figure alternative differs: {alt!r}")
    figure = image.find_parent(id="fig-standardnormal")
    if (
        figure is None
        or "quarto-figure-center" not in set(figure.get("class") or [])
        or figure.get("alt") != EXPECTED_ALT_TEXT
    ):
        raise RuntimeError("Lesson06 figure is not centered")

    lesson_asset_files = {
        path for path in reader_files if path.parts[:2] == ("assets", "lesson06")
    }
    if lesson_asset_files != {EXPECTED_READER_ASSET}:
        raise RuntimeError(f"Lesson06 reader asset inventory differs: {sorted(lesson_asset_files)}")

    css_path = BUILD / "assets" / "reader-8of14.css"
    css_payload = css_path.read_bytes()
    if not css_payload.endswith(builder.FIGURE_REFLOW_CSS):
        raise RuntimeError("Lesson06 exact figure-reflow CSS suffix differs")
    css = css_payload.decode("utf-8")
    css_compact = re.sub(r"\s+", " ", css)
    for required in ("max-width: 100%", "height: auto", "margin-inline: auto"):
        if required not in css_compact:
            raise RuntimeError(f"Lesson06 responsive figure CSS missing: {required}")
    return {
        "source_closure": identity(ASSET_CLOSURE),
        "images": 1,
        "reader_png_files": 1,
        "reader_png_bytes": len(target_payload),
        "reader_png_sha256": sha256(target_payload),
        "full_alt_text": alt,
        "full_width_centered": True,
        "responsive_css": identity(css_path),
        "external_dependencies": 0,
        "rights": "CC BY-NC 4.0 except where otherwise noted",
    }


def documents_gate() -> dict[str, object]:
    rows = load_jsonl(DOCUMENTS)
    expected_components = [
        "index", "Lesson00", "Lesson01", "Lesson02",
        "Lesson03", "Lesson04", "Lesson05", "Lesson06",
    ]
    if len(rows) != 8 or [row.get("component_id") for row in rows] != expected_components:
        raise RuntimeError("document backend sequence differs")
    if (
        sum(int(row["translation_segments"]) for row in rows) != 2_487
        or sum(int(row["structural_units"]) for row in rows) != 3_358
        or sum(int(row["math_nodes"]) for row in rows) != 1_648
    ):
        raise RuntimeError("document backend cumulative census differs")
    for row in rows:
        if row.get("schema") != "o006.stat415.document.v1":
            raise RuntimeError(f"document backend schema differs: {row.get('component_id')}")
        target_path_value = row.get("target_path")
        if not isinstance(target_path_value, str):
            raise RuntimeError(f"document backend target path missing: {row.get('component_id')}")
        target_path = ROOT / target_path_value
        payload = target_path.read_bytes()
        if row.get("target_bytes") != len(payload) or row.get("target_sha256") != sha256(payload):
            raise RuntimeError(f"document backend target identity differs: {row.get('component_id')}")
    lesson = rows[-1]
    if (
        lesson.get("document_id") != "O006-PSU-007"
        or lesson.get("translation_segments") != 176
        or lesson.get("structural_units") != 149
        or lesson.get("math_nodes") != 102
    ):
        raise RuntimeError("Lesson06 document backend row differs")
    return {"documents": len(rows), "backend": identity(DOCUMENTS)}


def prior_boundary_gate(outputs: dict[str, bytes]) -> dict[str, object]:
    prior_outputs, prior_receipt, prior_files = prior_builder.compute()
    if (
        prior_receipt.get("coverage", {}).get("complete_count") != 7
        or prior_receipt.get("translation_segments") != 2_311
        or prior_receipt.get("structural_units_normalized") != 3_209
        or prior_receipt.get("structural_units_target") != 3_207
        or prior_receipt.get("math_nodes", {}).get("total") != 1_546
        or prior_receipt.get("corrections", {}).get("count") != 112
        or len(prior_files) != 50
    ):
        raise RuntimeError("replayed Lesson05 boundary differs")

    preserved_pages = [f"Lesson{i:02d}.html" for i in range(0, 6)]
    for filename in preserved_pages:
        key = f"build/html-id/{filename}"
        before = BeautifulSoup(prior_outputs[key], "html.parser").select_one(
            "main#quarto-document-content"
        )
        after = BeautifulSoup(outputs[key], "html.parser").select_one(
            "main#quarto-document-content"
        )
        if before is None or after is None or str(before) != str(after):
            raise RuntimeError(f"prior semantic main differs at Lesson06 boundary: {filename}")

    prior_css = PurePosixPath("assets/reader-7of14.css")
    preserved_non_html = 0
    for path in prior_files:
        if path == prior_css or path.suffix.lower() == ".html":
            continue
        key = f"build/html-id/{path.as_posix()}"
        if outputs.get(key) != prior_outputs.get(key):
            raise RuntimeError(f"prior reader asset differs at Lesson06 boundary: {path}")
        preserved_non_html += 1
    return {
        "prior_documents": 7,
        "prior_translation_segments": 2_311,
        "prior_source_units": 3_209,
        "prior_target_units": 3_207,
        "prior_math_nodes": 1_546,
        "prior_corrections": 112,
        "preserved_semantic_mains": preserved_pages,
        "preserved_non_html_files": preserved_non_html,
    }


def compute() -> bytes:
    outputs, build_receipt, reader_files = deterministic_build_gate()
    translation = translation_gate()
    structure = structure_math_and_corrections_gate()
    reader = reader_gate(reader_files)
    asset_layout = asset_layout_gate(reader_files)
    documents = documents_gate()
    prior_boundary = prior_boundary_gate(outputs)
    receipt = {
        "schema": "o006.stat415.through-lesson06-qa.v1",
        "status": "passed",
        "coverage": {
            "complete_documents": 8,
            "corpus_documents": 14,
            "next_document": "Lesson07",
        },
        "translation": translation,
        "structure_math_and_corrections": structure,
        "reader": reader,
        "asset_layout_rights_privacy": asset_layout,
        "documents": documents,
        "prior_boundary": prior_boundary,
        "build_receipt": identity(ROOT / "build" / "THROUGH_LESSON06_BUILD_RECEIPT.json"),
        "build_contract": {
            "segments": build_receipt["translation_segments"],
            "source_units": build_receipt["structural_units_normalized"],
            "target_units": build_receipt["structural_units_target"],
            "math_nodes": build_receipt["math_nodes"]["total"],
            "corrections": build_receipt["corrections"]["count"],
            "reader_files": build_receipt["reader"]["files"],
        },
        "checks": [
            "exact-176-segment-source-target-binding-replay",
            "natural-id-ID-and-glossary-continuity",
            "exact-149-unit-102-math-Lesson06-topology",
            "only-registered-Lesson06-math-surfaces-change",
            "exact-122-correction-registry-with-L06-D001-through-L06-D010",
            "complete-proof-two-examples-one-solution",
            "no-code-and-no-external-dependency",
            "full-figure-alt-and-lowercase-z-critical-value-note",
            "lower-tail-chi-square-quantile-convention-explicit",
            "corrected-estimated-standard-error-equals-2",
            "large-sample-studentized-convergence-qualified",
            "exact-iid-Normal-t-interval-with-df-n-minus-1",
            "exact-one-PNG-route-byte-alt-lightbox-and-rights-closure",
            "full-width-centered-figure-and-responsive-reflow-CSS",
            "offline-link-asset-rights-privacy-and-provenance-closure",
            "deterministic-52-file-reader-and-manifest-replay",
            "prior-Lesson05-boundary-preserved",
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
            raise RuntimeError("Lesson06 QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({
        "mode": state,
        "documents": data["coverage"]["complete_documents"],
        "segments": data["translation"]["segments"],
        "source_units": data["build_contract"]["source_units"],
        "target_units": data["reader"]["stable_units"],
        "math_nodes": data["reader"]["math_nodes"],
        "corrections": data["structure_math_and_corrections"]["corrections"],
        "reader_files": data["reader"]["files"],
        "receipt_sha256": sha256(payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
