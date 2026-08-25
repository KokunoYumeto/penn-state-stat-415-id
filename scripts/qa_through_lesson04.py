#!/usr/bin/env python3
"""Deterministic cumulative QA for the 6-of-14 STAT 415 id-ID reader."""

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
import build_through_lesson04 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON04_QA_RECEIPT.json"
TRANSLATION = ROOT / "source" / "id-ID" / "lesson04_translation.csv"
TEMPLATE = ROOT / "working" / "lesson04_segments.csv"
BINDINGS = ROOT / "backend" / "lesson04_translation_bindings.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson04_corrections.jsonl"
DOCUMENTS = ROOT / "backend" / "through_lesson04_documents.jsonl"
MANIFEST = ROOT / "build" / "THROUGH_LESSON04_MANIFEST.csv"
SOURCE = ROOT / "source" / "normalized" / "en-US" / "Lesson04.html"
TARGET = ROOT / "source" / "id-ID" / "Lesson04.html"
AUTHORITY_ASSET = ROOT / "authority" / "assets" / "stat415" / "lesson04" / "STAT-415-SEC-1-15.svg"
TARGET_ASSET = BUILD / "assets" / "lesson04" / "STAT-415-SEC-1-15.svg"

DOCUMENT_COUNTS = {
    "index": (197, 0),
    "Lesson00": (363, 331),
    "Lesson01": (188, 169),
    "Lesson02": (228, 209),
    "Lesson03": (421, 440),
    "Lesson04": (335, 289),
}
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_IDENTICAL_SEGMENTS = {"O006-PSU-005-S0004", "O006-PSU-005-S0005"}


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
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]


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
            raise RuntimeError(f"deterministic Lesson04 build differs: {relative}")
    actual = shared.current_reader_files()
    if actual != reader_files:
        raise RuntimeError(f"reader inventory differs: extra={sorted(actual-reader_files)} missing={sorted(reader_files-actual)}")
    if (
        receipt.get("status") != "built"
        or receipt.get("coverage", {}).get("complete_count") != 6
        or receipt.get("translation_segments") != 1_971
        or receipt.get("structural_units_normalized") != 1_734
        or receipt.get("structural_units_target") != 1_732
        or receipt.get("math_nodes", {}).get("total") != 1_438
        or receipt.get("corrections", {}).get("count") != 81
        or receipt.get("reader", {}).get("files") != 34
    ):
        raise RuntimeError("Lesson04 build receipt contract differs")
    return receipt, reader_files


def translation_gate() -> dict[str, object]:
    template_fields, template = load_csv(TEMPLATE)
    target_fields, target = load_csv(TRANSLATION)
    expected_fields = [
        "segment_id", "document_id", "component_id", "section_id",
        "source_sha256", "source_text", "target_text", "status",
    ]
    if template_fields != expected_fields or target_fields != expected_fields or len(template) != 372 or len(target) != 372:
        raise RuntimeError("Lesson04 translation CSV schema/census differs")
    bindings = load_jsonl(BINDINGS)
    if len(bindings) != 372:
        raise RuntimeError("Lesson04 translation binding census differs")
    identical: set[str] = set()
    all_target: list[str] = []
    for ordinal, (source, row, binding_row) in enumerate(zip(template, target, bindings), start=1):
        sid = f"O006-PSU-005-S{ordinal:04d}"
        if row["segment_id"] != sid or source["segment_id"] != sid:
            raise RuntimeError(f"Lesson04 translation order differs: {sid}")
        for field in ("document_id", "component_id", "section_id", "source_sha256", "source_text"):
            if row[field] != source[field]:
                raise RuntimeError(f"Lesson04 immutable translation field differs: {sid}: {field}")
        target_text = row["target_text"]
        if row["status"] != "translated" or not target_text.strip() or "\ufffd" in target_text or "<" in target_text or ">" in target_text:
            raise RuntimeError(f"Lesson04 target surface invalid: {sid}")
        expected_boundary = boundary(source["source_text"])
        actual_boundary = boundary(target_text)
        if sid == "O006-PSU-005-S0088":
            if actual_boundary[0] != " " or actual_boundary[1] != expected_boundary[1]:
                raise RuntimeError("Lesson04 S0088 registered boundary repair differs")
        elif actual_boundary != expected_boundary:
            raise RuntimeError(f"Lesson04 target boundary differs: {sid}")
        if source["source_text"] == target_text:
            identical.add(sid)
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "segment_id": sid,
            "document_id": "O006-PSU-005",
            "component_id": "Lesson04",
            "section_id": row["section_id"] or None,
            "ordinal": ordinal,
            "locale": "id-ID",
            "source_sha256": row["source_sha256"],
            "target_sha256": sha256(target_text.encode("utf-8")),
            "status": "translated",
        }
        if binding_row != expected_binding:
            raise RuntimeError(f"Lesson04 backend binding differs: {sid}")
        all_target.append(target_text)
    if identical != EXPECTED_IDENTICAL_SEGMENTS:
        raise RuntimeError(f"Lesson04 untranslated/identity surface set differs: {sorted(identical)}")

    joined = "\n".join(all_target).casefold()
    required = (
        "fungsi kemungkinan", "fungsi log-kemungkinan", "penduga kemungkinan maksimum",
        "nilai dugaan kemungkinan maksimum", "fungsi indikator", "himpunan dukungan",
        "model berparameter tunggal", "model multiparameter", "statistik urutan",
        "subgradien", "supremum",
    )
    forbidden = (
        "maximum likelihood estimator", "maximum likelihood estimate", "log-likelihood function",
        "indicator function", "indication function", "joint probability distribution",
        "definition og", "0ne parameter", "the the", "suppose we", "find the mle",
        "the likelihood", "setting the derivative", "is the median",
    )
    missing = [term for term in required if term not in joined]
    present = [term for term in forbidden if term in joined]
    if missing or present:
        raise RuntimeError(f"Lesson04 language/terminology gate differs: missing={missing} forbidden={present}")
    return {
        "segments": len(target),
        "bindings": len(bindings),
        "identical_allowed": sorted(identical),
        "required_terms": list(required),
        "forbidden_surfaces_absent": list(forbidden),
        "translation": identity(TRANSLATION),
        "bindings_file": identity(BINDINGS),
    }


def correction_math_gate() -> dict[str, object]:
    rows = load_jsonl(CORRECTIONS)
    prior_rows = load_jsonl(ROOT / "backend" / "through_lesson03_corrections.jsonl")
    if len(rows) != 81 or rows[:46] != prior_rows:
        raise RuntimeError("historical correction prefix differs")
    lesson_rows = rows[46:]
    if [row.get("correction_id") for row in lesson_rows] != [f"O006-PSU-ADV-{i:04d}" for i in range(47, 82)]:
        raise RuntimeError("Lesson04 correction ID sequence differs")
    if [row.get("source_defect_id") for row in lesson_rows] != [f"L04-D{i:03d}" for i in range(1, 36)]:
        raise RuntimeError("Lesson04 defect binding sequence differs")
    if any(row.get("status") != "applied-target-only" for row in lesson_rows):
        raise RuntimeError("Lesson04 correction status differs")

    source = BeautifulSoup(SOURCE.read_bytes(), "html.parser").select_one("main#quarto-document-content")
    target = BeautifulSoup(TARGET.read_bytes(), "html.parser").select_one("main#quarto-document-content")
    if source is None or target is None:
        raise RuntimeError("Lesson04 semantic main missing")
    source_ids = shared.stable_values(source, "data-o006-math-id")
    target_ids = shared.stable_values(target, "data-o006-math-id")
    if source_ids != target_ids or len(source_ids) != 289:
        raise RuntimeError("Lesson04 math topology differs")
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
    if changed != registered or len(changed) != 34:
        raise RuntimeError(f"Lesson04 changed-math registry differs: changed={len(changed)} registered={len(registered)}")
    for row in lesson_rows:
        for surface in row.get("surfaces", []):
            if surface.get("surface") != "math":
                continue
            node = target.select_one(f'[data-o006-math-id="{surface["math_id"]}"]')
            if node is None or sha256(node.get_text().encode("utf-8")) != surface.get("target_surface_sha256"):
                raise RuntimeError(f"Lesson04 correction target hash differs: {surface.get('math_id')}")

    target_markup = TARGET.read_text("utf-8")
    forbidden_target = (
        "L(P)", "f(x_i\\theta)", "L(p)=\\prod_{i=1}^n \\frac{1}{\\Gamma",
        "\\ln \\left(\\ln \\prod", "if $y=$ or", "\\sum y_1", "x_i&gt;m",
        "e^{\\frac{|x_i-\\mu|}{b}}", "\\hat{\\theta_p}", "definition og",
        "0ne Parameter", "indication function", "joint probability distribution",
    )
    remaining = [surface for surface in forbidden_target if surface in target_markup]
    if remaining:
        raise RuntimeError(f"Lesson04 admitted defect remains: {remaining}")
    finding_ids = re.findall(r"^## (L04-D\d{3})\b", (ROOT / "working" / "lesson04_source_findings.md").read_text("utf-8"), re.MULTILINE)
    if finding_ids != [f"L04-D{i:03d}" for i in range(1, 36)]:
        raise RuntimeError("Lesson04 source-finding registry differs")
    return {
        "corrections": len(rows),
        "historical_prefix": len(prior_rows),
        "lesson04_corrections": len(lesson_rows),
        "changed_math_nodes": len(changed),
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
    }
    total_math = 0
    total_units = 0
    for component, (document_id, expected_math) in expected_pages.items():
        path = BUILD / f"{component}.html"
        payload = path.read_bytes()
        soup = BeautifulSoup(payload, "html.parser")
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"reader locale differs: {component}")
        if component != "index" and soup.select_one('meta[name="translation-provenance"]') is None:
            raise RuntimeError(f"reader provenance metadata missing: {component}")
        if soup.select_one('link[href="assets/reader-6of14.css"]') is None:
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
        for math_node in main.select(".math"):
            text = math_node.get_text()
            if re.search(r"\\n(?=\s|\\end)", text) or text.count("{") != text.count("}"):
                raise RuntimeError(f"malformed target TeX surface: {math_node.get('data-o006-math-id')}")
            if text.count(r"\begin{align") != text.count(r"\end{align"):
                raise RuntimeError(f"unbalanced align environment: {math_node.get('data-o006-math-id')}")
        if "googletagmanager" in payload.decode("utf-8") or "site_libs/" in payload.decode("utf-8"):
            raise RuntimeError(f"tracking/upstream runtime leaked: {component}")
        if soup.select('script[src^="http"], iframe, object, embed, audio, video'):
            raise RuntimeError(f"external/embedded runtime remains: {component}")
        for image in main.select("img"):
            if not str(image.get("alt", "")).strip():
                raise RuntimeError(f"reader image lacks alt text: {component}")
        total_math += len(maths)
        total_units += len(units)
    if total_math != 1_438 or total_units != 1_732:
        raise RuntimeError("reader cumulative stable-ID census differs")

    license_soup = BeautifulSoup((BUILD / "licenses" / "index.html").read_bytes(), "html.parser")
    if license_soup.select_one('link[href="../assets/reader-6of14.css"]') is None:
        raise RuntimeError("license stylesheet route differs")
    license_text = license_soup.get_text(" ", strip=True)
    for required in ("CC BY-NC 4.0", "MathJax 3.1.2", PROVENANCE, "tiga puluh lima koreksi Lesson 04"):
        if required not in license_text:
            raise RuntimeError(f"license/change notice missing: {required}")
    shared.validate_reader_links({path: (BUILD / Path(path.as_posix())).read_bytes() for path in reader_files})

    manifest_fields, manifest_rows = load_csv(MANIFEST)
    if manifest_fields != ["relative_path", "bytes", "sha256"] or len(manifest_rows) != len(reader_files):
        raise RuntimeError("reader manifest schema/census differs")
    expected_manifest = {
        path.as_posix(): (len((BUILD / Path(path.as_posix())).read_bytes()), sha256((BUILD / Path(path.as_posix())).read_bytes()))
        for path in reader_files
    }
    actual_manifest = {row["relative_path"]: (int(row["bytes"]), row["sha256"]) for row in manifest_rows}
    if actual_manifest != expected_manifest:
        raise RuntimeError("reader manifest identity differs")
    return {
        "files": len(reader_files),
        "bytes": sum(value[0] for value in expected_manifest.values()),
        "stable_units": total_units,
        "math_nodes": total_math,
        "manifest": identity(MANIFEST),
    }


def asset_gate() -> dict[str, object]:
    authority = AUTHORITY_ASSET.read_bytes()
    target = TARGET_ASSET.read_bytes()
    if len(authority) != 2_259 or sha256(authority) != "5c6f266e5a56ef3aa37bed6a8af263e64cd235691100b38d7cdf3475812d268c":
        raise RuntimeError("Lesson04 authority asset differs")
    if len(target) != 2_259 or sha256(target) != "190a9508422964804260315513eeaae1bc8bce4af5be40d617d1020c9b26e595":
        raise RuntimeError("Lesson04 corrected reader asset differs")
    if b'translate(252.88 244.77) scale(0.58)">2</text>' not in target:
        raise RuntimeError("Lesson04 x2 asset repair absent")
    lesson = BeautifulSoup((BUILD / "Lesson04.html").read_bytes(), "html.parser")
    image = lesson.select_one('img[src="assets/lesson04/STAT-415-SEC-1-15.svg"]')
    lightbox = lesson.select_one('a[href="assets/lesson04/STAT-415-SEC-1-15.svg"]')
    if image is None or lightbox is None or "x₁ < x₂" not in str(image.get("alt")):
        raise RuntimeError("Lesson04 reader asset topology/alt text differs")
    return {"authority": identity(AUTHORITY_ASSET), "reader": identity(TARGET_ASSET), "images": 1, "lightbox_links": 1}


def compute() -> bytes:
    build_receipt, reader_files = deterministic_build_gate()
    translation = translation_gate()
    corrections = correction_math_gate()
    reader = reader_gate(reader_files)
    asset = asset_gate()
    documents = load_jsonl(DOCUMENTS)
    if len(documents) != 6 or sum(int(row["translation_segments"]) for row in documents) != 1_971:
        raise RuntimeError("document backend differs")
    receipt = {
        "schema": "o006.stat415.through-lesson04-qa.v1",
        "status": "passed",
        "coverage": {"complete_documents": 6, "corpus_documents": 14, "next_document": "Lesson05"},
        "translation": translation,
        "structure_math_and_corrections": corrections,
        "reader": reader,
        "asset": asset,
        "documents_backend": identity(DOCUMENTS),
        "build_receipt": identity(ROOT / "build" / "THROUGH_LESSON04_BUILD_RECEIPT.json"),
        "checks": [
            "exact-372-segment-source-target-binding-replay",
            "natural-id-ID-and-glossary-continuity",
            "exact-335-unit-289-math-Lesson04-topology",
            "exact-81-correction-registry-with-35-Lesson04-findings",
            "exact-34-changed-math-node-registry",
            "offline-link-asset-rights-privacy-and-provenance-closure",
            "responsive-reader-css-on-all-six-instructional-routes",
            "deterministic-34-file-reader-replay",
        ],
    }
    del build_receipt
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
            raise RuntimeError("Lesson04 QA receipt differs")
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
