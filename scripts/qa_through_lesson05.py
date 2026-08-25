#!/usr/bin/env python3
"""Deterministic cumulative QA for the 7-of-14 STAT 415 id-ID reader."""

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

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson05 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON05_QA_RECEIPT.json"
TRANSLATION = ROOT / "source" / "id-ID" / "lesson05_translation.csv"
TEMPLATE = ROOT / "working" / "lesson05_segments.csv"
BINDINGS = ROOT / "backend" / "lesson05_translation_bindings.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson05_corrections.jsonl"
DOCUMENTS = ROOT / "backend" / "through_lesson05_documents.jsonl"
MANIFEST = ROOT / "build" / "THROUGH_LESSON05_MANIFEST.csv"
SOURCE = ROOT / "source" / "normalized" / "en-US" / "Lesson05.html"
TARGET = ROOT / "source" / "id-ID" / "Lesson05.html"
ASSET_CLOSURE = ROOT / "working" / "lesson05_asset_closure.json"
SEEDED_ASSET = ROOT / "source" / "id-ID" / "assets" / "lesson05" / "seeded-z1000.png"

DOCUMENT_COUNTS = {
    "index": (197, 0),
    "Lesson00": (363, 331),
    "Lesson01": (188, 169),
    "Lesson02": (228, 209),
    "Lesson03": (421, 440),
    "Lesson04": (335, 289),
    "Lesson05": (1_475, 108),
}
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_FIELDS = [
    "segment_id", "document_id", "component_id", "section_id",
    "source_sha256", "source_text", "target_text", "status",
]
EXPECTED_REQUIRED_TERMS = (
    "pendugaan kemungkinan maksimum secara numerik",
    "pencarian grid",
    "optimisasi numerik",
    "fungsi skor",
    "newton–raphson",
    "negatif fungsi log-kemungkinan",
    "fungsi objektif",
    "nilai awal",
    "iterasi",
    "evaluasi fungsi",
    "kriteria konvergensi",
    "rataan/skala",
    "simpangan baku",
    "kerangka data",
    "kuantil",
)
EXPECTED_FORBIDDEN_TERMS = (
    "maximum likelihood estimation",
    "maximum likelihood estimate",
    "grid search method",
    "numerical optimization",
    "negative log-likelihood function",
    "pencarian kisi",
    "optimasi numerik",
    "fungsi kemungkinan negatif",
)


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


def deterministic_build_gate() -> tuple[dict[str, object], set[PurePosixPath]]:
    outputs, receipt, reader_files = builder.compute()
    for relative, expected in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != expected:
            raise RuntimeError(f"deterministic Lesson05 build differs: {relative}")
    actual = shared.current_reader_files()
    if actual != reader_files:
        raise RuntimeError(
            f"reader inventory differs: extra={sorted(actual-reader_files)} "
            f"missing={sorted(reader_files-actual)}"
        )
    if (
        receipt.get("schema") != "o006.stat415.through-lesson05-build.v1"
        or receipt.get("status") != "built"
        or receipt.get("coverage", {}).get("complete_count") != 7
        or receipt.get("coverage", {}).get("next_document") != "Lesson06"
        or receipt.get("translation_segments") != 2_311
        or receipt.get("structural_units_normalized") != 3_209
        or receipt.get("structural_units_target") != 3_207
        or receipt.get("math_nodes", {}).get("total") != 1_546
        or receipt.get("corrections", {}).get("count") != 112
        or receipt.get("corrections", {}).get("lesson05_count") != 31
        or receipt.get("reader", {}).get("files") != 50
    ):
        raise RuntimeError("Lesson05 build receipt contract differs")
    return receipt, reader_files


def translation_gate() -> dict[str, object]:
    template_fields, template = load_csv(TEMPLATE)
    target_fields, target = load_csv(TRANSLATION)
    if (
        template_fields != EXPECTED_FIELDS
        or target_fields != EXPECTED_FIELDS
        or len(template) != 340
        or len(target) != 340
    ):
        raise RuntimeError("Lesson05 translation CSV schema/census differs")
    bindings = load_jsonl(BINDINGS)
    if len(bindings) != 340:
        raise RuntimeError("Lesson05 translation binding census differs")

    identical: set[str] = set()
    all_target: list[str] = []
    for ordinal, (source, row, binding_row) in enumerate(zip(template, target, bindings), start=1):
        sid = f"O006-PSU-006-S{ordinal:04d}"
        if row["segment_id"] != sid or source["segment_id"] != sid:
            raise RuntimeError(f"Lesson05 translation order differs: {sid}")
        for field in ("document_id", "component_id", "section_id", "source_sha256", "source_text"):
            if row[field] != source[field]:
                raise RuntimeError(f"Lesson05 immutable translation field differs: {sid}: {field}")
        target_text = row["target_text"]
        if (
            row["status"] != "translated"
            or not target_text.strip()
            or "\ufffd" in target_text
            or "<" in target_text
            or ">" in target_text
        ):
            raise RuntimeError(f"Lesson05 target surface invalid: {sid}")
        if boundary(target_text) != boundary(source["source_text"]):
            raise RuntimeError(f"Lesson05 target boundary differs: {sid}")
        if source["source_text"] == target_text:
            identical.add(sid)
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": sid,
            "document_id": "O006-PSU-006",
            "component_id": "Lesson05",
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": sha256(target_text.encode("utf-8")),
            "status": "translated",
        }
        if binding_row != expected_binding:
            raise RuntimeError(f"Lesson05 backend binding differs: {sid}")
        all_target.append(target_text)
    if identical:
        raise RuntimeError(f"Lesson05 untranslated/identity surfaces remain: {sorted(identical)}")

    joined = "\n".join(all_target).casefold()
    missing = [term for term in EXPECTED_REQUIRED_TERMS if term not in joined]
    present = [term for term in EXPECTED_FORBIDDEN_TERMS if term in joined]
    if missing or present:
        raise RuntimeError(f"Lesson05 language/terminology gate differs: missing={missing} forbidden={present}")
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
        raise RuntimeError(f"Lesson05 correction target hash missing: {surface}")
    if kind == "math":
        nodes = target_main.select(f'[data-o006-math-id="{surface.get("math_id")}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson05 correction math surface missing: {surface.get('math_id')}")
        actual = nodes[0].get_text().encode("utf-8")
    elif kind == "structural-unit-text":
        nodes = target_main.select(f'[data-o006-id="{surface.get("unit_id")}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson05 correction unit surface missing: {surface.get('unit_id')}")
        actual = nodes[0].get_text().encode("utf-8")
    elif kind == "translation-segment":
        row = translation_by_id.get(str(surface.get("segment_id")))
        if row is None:
            raise RuntimeError(f"Lesson05 correction translation surface missing: {surface.get('segment_id')}")
        actual = row["target_text"].encode("utf-8")
    elif kind == "asset":
        path_value = surface.get("target_path")
        if not isinstance(path_value, str):
            raise RuntimeError("Lesson05 correction asset path missing")
        path = ROOT / path_value
        if not path.is_file():
            raise RuntimeError(f"Lesson05 correction asset missing: {path_value}")
        actual = path.read_bytes()
    elif kind == "external-dependency":
        occurrence = str(surface.get("occurrence"))
        nodes = target_main.select(
            f'[data-o006-dependency-id="{surface.get("dependency_id")}"]'
            f'[data-video-occurrence="{occurrence}"]'
        )
        if len(nodes) != 1 or nodes[0].name != "div":
            raise RuntimeError(f"Lesson05 static dependency fallback missing: occurrence {occurrence}")
        actual = str(nodes[0]).encode("utf-8")
    elif kind == "dom-id":
        target_value = surface.get("target_value")
        nodes = target_main.select(f'[id="{target_value}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson05 repaired DOM ID missing: {target_value}")
        actual = str(target_value).encode("utf-8")
    elif kind == "image-alternative":
        nodes = target_main.select(f'[data-o006-asset-id="{surface.get("asset_id")}"]')
        if len(nodes) != 1 or nodes[0].name != "img":
            raise RuntimeError(f"Lesson05 image alternative surface missing: {surface.get('asset_id')}")
        actual = str(nodes[0].get("alt") or "").encode("utf-8")
    elif kind == "ui-attribute":
        nodes = target_main.select(f'[data-o006-id="{surface.get("unit_id")}"]')
        attribute = surface.get("attribute")
        if len(nodes) != 1 or not isinstance(attribute, str):
            raise RuntimeError(f"Lesson05 UI-attribute surface missing: {surface.get('unit_id')}")
        value = nodes[0].get(attribute)
        if not isinstance(value, str):
            raise RuntimeError(f"Lesson05 UI attribute missing: {surface.get('unit_id')}:{attribute}")
        actual = value.encode("utf-8")
    elif kind == "code-comment":
        anchors = target_main.select(f'a[data-o006-id="{surface.get("anchor_unit_id")}"]')
        if len(anchors) != 1 or anchors[0].parent is None:
            raise RuntimeError(f"Lesson05 code-comment anchor missing: {surface.get('anchor_unit_id')}")
        comments = anchors[0].parent.select(":scope > span.do")
        if len(comments) != 1:
            raise RuntimeError(f"Lesson05 code-comment surface missing: {surface.get('anchor_unit_id')}")
        actual = comments[0].get_text().encode("utf-8")
    else:
        raise RuntimeError(f"unknown Lesson05 correction surface: {kind}")
    if sha256(actual) != expected_hash:
        raise RuntimeError(f"Lesson05 correction target hash differs: {kind}")


def correction_math_gate() -> dict[str, object]:
    rows = load_jsonl(CORRECTIONS)
    prior_rows = load_jsonl(ROOT / "backend" / "through_lesson04_corrections.jsonl")
    if len(rows) != 112 or rows[:81] != prior_rows:
        raise RuntimeError("historical correction prefix differs")
    lesson_rows = rows[81:]
    if [row.get("correction_id") for row in lesson_rows] != [f"O006-PSU-ADV-{i:04d}" for i in range(82, 113)]:
        raise RuntimeError("Lesson05 correction ID sequence differs")
    if [row.get("source_defect_id") for row in lesson_rows] != [f"L05-D{i:03d}" for i in range(1, 32)]:
        raise RuntimeError("Lesson05 defect binding sequence differs")
    if any(row.get("status") != "applied-target-only" for row in lesson_rows):
        raise RuntimeError("Lesson05 correction status differs")

    source_soup = BeautifulSoup(SOURCE.read_bytes(), "html.parser")
    target_soup = BeautifulSoup(TARGET.read_bytes(), "html.parser")
    source = source_soup.select_one("main#quarto-document-content")
    target = target_soup.select_one("main#quarto-document-content")
    if source is None or target is None:
        raise RuntimeError("Lesson05 semantic main missing")
    source_ids = shared.stable_values(source, "data-o006-math-id")
    target_ids = shared.stable_values(target, "data-o006-math-id")
    if source_ids != target_ids or len(source_ids) != 108:
        raise RuntimeError("Lesson05 math topology differs")
    changed = {
        sid for sid, before, after in zip(source_ids, source.select(".math"), target.select(".math"))
        if before.get_text() != after.get_text()
    }
    registered = {
        str(surface["math_id"])
        for row in lesson_rows
        for surface in row.get("surfaces", [])
        if surface.get("surface") == "math"
    }
    if changed != registered or len(changed) != 11:
        raise RuntimeError(
            f"Lesson05 changed-math registry differs: changed={len(changed)} registered={len(registered)}"
        )

    _, translation_rows = load_csv(TRANSLATION)
    translation_by_id = {row["segment_id"]: row for row in translation_rows}
    expected_surface_kinds = {
        "asset", "dom-id", "external-dependency", "image-alternative",
        "math", "structural-unit-text", "translation-segment", "ui-attribute",
        "code-comment",
    }
    seen_surface_kinds: set[str] = set()
    for row in lesson_rows:
        surfaces = row.get("surfaces")
        if not isinstance(surfaces, list) or not surfaces or row.get("replacement_count") != len(surfaces):
            raise RuntimeError(f"Lesson05 correction replacement census differs: {row.get('correction_id')}")
        expected_row_surface = surfaces[0].get("surface") if len(surfaces) == 1 else "multiple"
        if row.get("surface") != expected_row_surface:
            raise RuntimeError(f"Lesson05 correction surface summary differs: {row.get('correction_id')}")
        for surface in surfaces:
            kind = surface.get("surface")
            if isinstance(kind, str):
                seen_surface_kinds.add(kind)
            correction_surface_gate(target, translation_by_id, surface)
    if seen_surface_kinds != expected_surface_kinds:
        raise RuntimeError(f"Lesson05 correction surface-kind closure differs: {sorted(seen_surface_kinds)}")

    if target.select("iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson05 target retains an executable/embed dependency")
    if shared.native_id_duplicates(target):
        raise RuntimeError(f"Lesson05 target retains duplicate native IDs: {shared.native_id_duplicates(target)}")
    target_text = target.get_text("\n", strip=False)
    required_repairs = (
        "set.seed(4150501)", "set.seed(4150502)", "set.seed(4150503)",
        "set.seed(4150504)", "set.seed(4150505)", "NA_real_",
        'method="L-BFGS-B"', "nll.exp(out$par,x)", "8.866665", "8.866664",
        "-3.188414", "14.885495", "Pengganti statis Video 5.1", "Pengganti statis Video 5.2",
    )
    missing_repairs = [value for value in required_repairs if value not in target_text]
    forbidden_old = (
        "[1] 4.580174", "[1] 870", "[1] 0.87", "1.137955e-131",
        "nll.exp(0.112793,x)", "I moved this from under the single header",
        "[1] -3.186135 14.885294",
    )
    remaining_old = [value for value in forbidden_old if value in target_text]
    if missing_repairs or remaining_old:
        raise RuntimeError(
            f"Lesson05 remediation surface differs: missing={missing_repairs} remaining={remaining_old}"
        )
    finding_ids = re.findall(
        r"^### (L05-D\d{3})\b",
        (ROOT / "working" / "lesson05_source_findings.md").read_text("utf-8"),
        re.MULTILINE,
    )
    if finding_ids != [f"L05-D{i:03d}" for i in range(1, 32)]:
        raise RuntimeError("Lesson05 source-finding registry differs")
    return {
        "corrections": len(rows),
        "historical_prefix": len(prior_rows),
        "lesson05_corrections": len(lesson_rows),
        "changed_math_nodes": len(changed),
        "surface_kinds": sorted(seen_surface_kinds),
        "correction_backend": identity(CORRECTIONS),
    }


def reader_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    expected_pages = {
        "index": ("O006-PSU-000", 0),
        "Lesson00": ("O006-PSU-001", 331),
        "Lesson01": ("O006-PSU-002", 169),
        "Lesson02": ("O006-PSU-003", 209),
        "Lesson03": ("O006-PSU-004", 440),
        "Lesson04": ("O006-PSU-005", 289),
        "Lesson05": ("O006-PSU-006", 108),
    }
    total_math = 0
    total_units = 0
    for component, (document_id, expected_math) in expected_pages.items():
        path = BUILD / f"{component}.html"
        payload = path.read_bytes()
        markup = payload.decode("utf-8")
        soup = BeautifulSoup(payload, "html.parser")
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"reader locale differs: {component}")
        if component != "index" and soup.select_one('meta[name="translation-provenance"]') is None:
            raise RuntimeError(f"reader provenance metadata missing: {component}")
        if soup.select_one('link[href="assets/reader-7of14.css"]') is None:
            raise RuntimeError(f"reader stylesheet route differs: {component}")
        main = soup.select_one("main#quarto-document-content")
        if main is None:
            raise RuntimeError(f"reader semantic main missing: {component}")
        units = shared.stable_values(main, "data-o006-id")
        maths = shared.stable_values(main, "data-o006-math-id")
        expected_units = DOCUMENT_COUNTS[component][0]
        if len(units) != expected_units or len(maths) != expected_math:
            raise RuntimeError(f"reader stable-ID census differs: {component}")
        if expected_math and maths != [f"{document_id}-M{i:04d}" for i in range(1, expected_math + 1)]:
            raise RuntimeError(f"reader math sequence differs: {component}")
        duplicates = shared.native_id_duplicates(main)
        if duplicates:
            raise RuntimeError(f"reader duplicate native IDs remain: {component}: {duplicates}")
        for math_node in main.select(".math"):
            text = math_node.get_text()
            if re.search(r"\\n(?=\s|\\end)", text) or text.count("{") != text.count("}"):
                raise RuntimeError(f"malformed target TeX surface: {math_node.get('data-o006-math-id')}")
            if text.count(r"\begin{align") != text.count(r"\end{align"):
                raise RuntimeError(f"unbalanced align environment: {math_node.get('data-o006-math-id')}")
        if "googletagmanager" in markup or "site_libs/" in markup:
            raise RuntimeError(f"tracking/upstream runtime leaked: {component}")
        if soup.select('script[src^="http"], iframe, object, embed, audio, video'):
            raise RuntimeError(f"external/embedded runtime remains: {component}")
        for image in main.select("img"):
            if not str(image.get("alt", "")).strip():
                raise RuntimeError(f"reader image lacks alt text: {component}")
        total_math += len(maths)
        total_units += len(units)
    if total_math != 1_546 or total_units != 3_207:
        raise RuntimeError("reader cumulative stable-ID census differs")

    license_soup = BeautifulSoup((BUILD / "licenses" / "index.html").read_bytes(), "html.parser")
    if license_soup.select_one('link[href="../assets/reader-7of14.css"]') is None:
        raise RuntimeError("license stylesheet route differs")
    license_text = license_soup.get_text(" ", strip=True)
    for required in (
        "CC BY-NC 4.0", "MathJax 3.1.2", PROVENANCE,
        "tiga puluh lima koreksi Lesson 04", "tiga puluh satu koreksi Lesson 05",
    ):
        if required not in license_text:
            raise RuntimeError(f"license/change notice missing: {required}")
    reader_payloads = {path: (BUILD / Path(path.as_posix())).read_bytes() for path in reader_files}
    shared.validate_reader_links(reader_payloads)

    manifest_fields, manifest_rows = load_csv(MANIFEST)
    if manifest_fields != ["relative_path", "bytes", "sha256"] or len(manifest_rows) != len(reader_files):
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


def asset_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    closure = json.loads(ASSET_CLOSURE.read_text("utf-8"))
    frozen = closure.get("frozen_images")
    external = closure.get("external_dependencies")
    if (
        closure.get("schema") != "o006.stat415.lesson05-asset-closure.v1"
        or closure.get("status") != "same-origin-images-closed-external-video-excluded-reader-remediation-required"
        or not isinstance(frozen, list)
        or len(frozen) != 14
        or not isinstance(external, list)
        or len(external) != 1
    ):
        raise RuntimeError("Lesson05 source asset-closure contract differs")
    expected_ids = [f"O006-PSU-006-A{i:04d}" for i in range(1, 15)]
    if [row.get("asset_id") for row in frozen] != expected_ids:
        raise RuntimeError("Lesson05 source asset identity sequence differs")

    lesson = BeautifulSoup((BUILD / "Lesson05.html").read_bytes(), "html.parser")
    main = lesson.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("Lesson05 reader main missing for asset gate")
    images = main.select("img[data-o006-asset-id]")
    if len(images) != 14 or [image.get("data-o006-asset-id") for image in images] != expected_ids:
        raise RuntimeError("Lesson05 reader image identity sequence differs")

    frozen_by_id = {str(row["asset_id"]): row for row in frozen}
    target_asset_paths: set[PurePosixPath] = set()
    total_bytes = 0
    for image in images:
        asset_id = str(image["data-o006-asset-id"])
        source_record = frozen_by_id[asset_id]
        src = str(image.get("src") or "")
        relative = PurePosixPath(src)
        if (
            not src.startswith("assets/lesson05/")
            or relative.is_absolute()
            or ".." in relative.parts
            or relative.suffix.lower() != ".png"
        ):
            raise RuntimeError(f"Lesson05 reader asset route differs: {asset_id}: {src}")
        target_path = BUILD.joinpath(*relative.parts)
        if not target_path.is_file():
            raise RuntimeError(f"Lesson05 reader asset missing: {asset_id}: {src}")
        payload = target_path.read_bytes()
        if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError(f"Lesson05 reader asset is not PNG: {asset_id}")
        if asset_id == "O006-PSU-006-A0004":
            expected = SEEDED_ASSET.read_bytes()
            if image.get("data-derivative-seed") != "4150505":
                raise RuntimeError("Lesson05 seeded derivative marker differs")
            if len(expected) != 26_489 or sha256(expected) != "10db41ec1a607f9eb38f7ec5af4bf3ce589ffe91497a69fe5ce40f344e8a6974":
                raise RuntimeError("Lesson05 seeded derivative authority differs")
        else:
            source_path_value = source_record.get("local_path")
            if not isinstance(source_path_value, str):
                raise RuntimeError(f"Lesson05 source asset path missing: {asset_id}")
            source_path = ROOT / source_path_value
            expected = source_path.read_bytes()
            if (
                source_record.get("bytes") != len(expected)
                or source_record.get("sha256") != sha256(expected)
            ):
                raise RuntimeError(f"Lesson05 source asset identity differs: {asset_id}")
        if payload != expected:
            raise RuntimeError(f"Lesson05 reader asset bytes differ: {asset_id}")
        expected_lightboxes = int(source_record.get("lightbox_href_occurrences", 0))
        if len(main.select(f'a[href="{src}"]')) != expected_lightboxes:
            raise RuntimeError(f"Lesson05 lightbox topology differs: {asset_id}")
        if not str(image.get("alt") or "").strip():
            raise RuntimeError(f"Lesson05 image alternative missing: {asset_id}")
        target_asset_paths.add(relative)
        total_bytes += len(payload)
    reader_lesson_assets = {path for path in reader_files if path.parts[:2] == ("assets", "lesson05")}
    if reader_lesson_assets != target_asset_paths or len(target_asset_paths) != 14:
        raise RuntimeError(
            f"Lesson05 reader asset inventory differs: extra={sorted(reader_lesson_assets-target_asset_paths)} "
            f"missing={sorted(target_asset_paths-reader_lesson_assets)}"
        )
    if main.select("iframe"):
        raise RuntimeError("Lesson05 external video iframe remains")
    fallbacks = main.select('div.static-video-fallback[data-o006-dependency-id="O006-PSU-006-D0001"]')
    if len(fallbacks) != 2:
        raise RuntimeError("Lesson05 static video fallback census differs")
    return {
        "source_closure": identity(ASSET_CLOSURE),
        "images": len(images),
        "reader_asset_files": len(target_asset_paths),
        "reader_asset_bytes": total_bytes,
        "seeded_derivatives": 1,
        "static_video_fallbacks": len(fallbacks),
    }


def documents_gate() -> dict[str, object]:
    rows = load_jsonl(DOCUMENTS)
    expected_components = ["index", "Lesson00", "Lesson01", "Lesson02", "Lesson03", "Lesson04", "Lesson05"]
    if len(rows) != 7 or [row.get("component_id") for row in rows] != expected_components:
        raise RuntimeError("document backend sequence differs")
    if (
        sum(int(row["translation_segments"]) for row in rows) != 2_311
        or sum(int(row["structural_units"]) for row in rows) != 3_209
        or sum(int(row["math_nodes"]) for row in rows) != 1_546
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
        lesson.get("document_id") != "O006-PSU-006"
        or lesson.get("translation_segments") != 340
        or lesson.get("structural_units") != 1_475
        or lesson.get("math_nodes") != 108
    ):
        raise RuntimeError("Lesson05 document backend row differs")
    return {"documents": len(rows), "backend": identity(DOCUMENTS)}


def compute() -> bytes:
    _, reader_files = deterministic_build_gate()
    translation = translation_gate()
    corrections = correction_math_gate()
    reader = reader_gate(reader_files)
    asset = asset_gate(reader_files)
    documents = documents_gate()
    receipt = {
        "schema": "o006.stat415.through-lesson05-qa.v1",
        "status": "passed",
        "coverage": {"complete_documents": 7, "corpus_documents": 14, "next_document": "Lesson06"},
        "translation": translation,
        "structure_math_and_corrections": corrections,
        "reader": reader,
        "asset": asset,
        "documents": documents,
        "build_receipt": identity(ROOT / "build" / "THROUGH_LESSON05_BUILD_RECEIPT.json"),
        "checks": [
            "exact-340-segment-source-target-binding-replay",
            "natural-id-ID-and-glossary-continuity",
            "exact-1475-unit-108-math-Lesson05-topology",
            "exact-112-correction-registry-with-31-Lesson05-findings",
            "exact-11-changed-math-node-registry",
            "exact-seven-correction-surface-kind-closure",
            "seeded-R-output-and-derived-plot-closure",
            "exact-14-image-route-byte-alt-and-lightbox-closure",
            "two-external-video-iframes-replaced-by-static-fallbacks",
            "offline-link-asset-rights-privacy-and-provenance-closure",
            "responsive-reader-css-on-all-seven-instructional-routes",
            "deterministic-50-file-reader-replay",
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
            raise RuntimeError("Lesson05 QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({
        "mode": state,
        "segments": data["translation"]["segments"],
        "math_nodes": data["reader"]["math_nodes"],
        "corrections": data["structure_math_and_corrections"]["corrections"],
        "reader_files": data["reader"]["files"],
        "receipt_sha256": sha256(payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
