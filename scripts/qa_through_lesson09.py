#!/usr/bin/env python3
"""Deterministic cumulative QA for the 11-of-14 STAT 415 id-ID reader."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson09 as builder


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "html-id"
QA_RECEIPT = ROOT / "build" / "THROUGH_LESSON09_QA_RECEIPT.json"
BUILD_RECEIPT = ROOT / "build" / "THROUGH_LESSON09_BUILD_RECEIPT.json"
MANIFEST = ROOT / "build" / "THROUGH_LESSON09_MANIFEST.csv"
DOCUMENTS = ROOT / "backend" / "through_lesson09_documents.jsonl"
CORRECTIONS = ROOT / "backend" / "through_lesson09_corrections.jsonl"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
EXPECTED_COMPONENTS = ["index", *[f"Lesson{i:02d}" for i in range(10)]]
EXPECTED_COUNTS = {
    "index": (197, 0),
    "Lesson00": (363, 331),
    "Lesson01": (188, 169),
    "Lesson02": (228, 209),
    "Lesson03": (421, 440),
    "Lesson04": (335, 289),
    "Lesson05": (1_475, 108),
    "Lesson06": (149, 102),
    "Lesson07": (399, 148),
    "Lesson08": (594, 156),
    "Lesson09": (414, 219),
}
EXPECTED_IDS = {
    "index": "O006-PSU-000",
    **{f"Lesson{i:02d}": f"O006-PSU-{i + 1:03d}" for i in range(10)},
}
NEW_LESSONS = {
    "Lesson07": (237, 399, 148, 12, 123),
    "Lesson08": (291, 604, 156, 17, 135),
    "Lesson09": (443, 414, 219, 19, 152),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def parse_jsonl(payload: bytes, label: str) -> list[dict[str, object]]:
    try:
        rows = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    if any(not isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{label} contains a non-object")
    return rows


def deterministic_build_gate() -> tuple[
    dict[str, bytes], dict[str, object], set[PurePosixPath]
]:
    outputs, receipt, reader_files = builder.compute()
    for relative, payload in outputs.items():
        path = ROOT / relative
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"deterministic Lesson09 build differs: {relative}")
    if shared.current_reader_files() != reader_files:
        raise RuntimeError("reader inventory differs from deterministic build")
    coverage = receipt.get("coverage", {})
    math = receipt.get("math_nodes", {})
    corrections = receipt.get("corrections", {})
    reader = receipt.get("reader", {})
    assets = receipt.get("new_assets", {})
    layout = receipt.get("layout", {})
    offline = receipt.get("offline", {})
    rights = receipt.get("rights", {})
    if (
        receipt.get("schema") != "o006.stat415.through-lesson09-build.v1"
        or receipt.get("status") != "built"
        or coverage.get("complete_count") != 11
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson10"
        or receipt.get("translation_segments") != 3_458
        or receipt.get("structural_units_normalized") != 4_775
        or receipt.get("structural_units_target") != 4_763
        or math.get("total") != 2_171
        or corrections.get("count") != 170
        or corrections.get("lesson07_count") != 12
        or corrections.get("lesson08_count") != 17
        or corrections.get("lesson09_count") != 19
        or reader.get("files") != 71
        or len(reader_files) != 71
        or assets.get("count") != 16
        or assets.get("bytes") != 4_574_263
        or assets.get("all_byte_preserving") is not True
        or layout.get("reader_css_path") != "assets/reader-11of14.css"
        or layout.get("inherited_inline_width_constraints_removed") != 9
        or offline.get("external_runtime_requests") != 0
        or offline.get("analytics") is not False
        or offline.get("cookies") is not False
        or offline.get("local_mathjax") is not True
        or offline.get("third_party_iframes") != 0
        or rights.get("Penn State content") != "CC BY-NC 4.0 except where otherwise noted"
        or rights.get("aggregate_uniform_relicense") is not False
    ):
        raise RuntimeError("Lesson09 build receipt contract differs")
    return outputs, receipt, reader_files


def translation_backend_gate() -> dict[str, object]:
    total = 0
    evidence: list[dict[str, object]] = []
    for component, (segments, _, _, _, _) in NEW_LESSONS.items():
        number = int(component[-2:])
        document_id = EXPECTED_IDS[component]
        template_path = ROOT / "working" / f"lesson{number:02d}_segments.csv"
        target_path = ROOT / "source" / "id-ID" / f"lesson{number:02d}_translation.csv"
        binding_path = ROOT / "backend" / f"lesson{number:02d}_translation_bindings.jsonl"
        with template_path.open("r", encoding="utf-8", newline="") as stream:
            source_rows = list(csv.DictReader(stream))
        with target_path.open("r", encoding="utf-8", newline="") as stream:
            target_rows = list(csv.DictReader(stream))
        bindings = parse_jsonl(binding_path.read_bytes(), f"{component} bindings")
        if len(source_rows) != segments or len(target_rows) != segments or len(bindings) != segments:
            raise RuntimeError(f"{component} translation/backend census differs")
        for ordinal, (source, target, binding) in enumerate(
            zip(source_rows, target_rows, bindings), start=1
        ):
            sid = f"{document_id}-S{ordinal:04d}"
            if source["segment_id"] != sid or target["segment_id"] != sid:
                raise RuntimeError(f"{component} segment order differs: {sid}")
            for field in (
                "document_id", "component_id", "section_id", "source_sha256", "source_text"
            ):
                if target[field] != source[field]:
                    raise RuntimeError(f"{component} immutable translation field differs: {sid}")
            text = target["target_text"]
            expected_binding = {
                "schema": "o006.stat415.translation-binding.v1",
                "segment_id": sid,
                "document_id": document_id,
                "component_id": component,
                "section_id": target["section_id"] or None,
                "ordinal": ordinal,
                "locale": "id-ID",
                "source_sha256": target["source_sha256"],
                "target_sha256": sha256(text.encode("utf-8")),
                "status": "translated",
            }
            if (
                target["status"] != "translated"
                or not text.strip()
                or "\ufffd" in text
                or binding != expected_binding
            ):
                raise RuntimeError(f"{component} translation/backend binding differs: {sid}")
        total += segments
        evidence.append({
            "component": component,
            "segments": segments,
            "translation": identity(target_path),
            "bindings": identity(binding_path),
        })
    if total != 971:
        raise RuntimeError("Lessons07-09 translation total differs")
    return {"new_segments": total, "lessons": evidence}


def changed_math_ids_from_corrections(
    rows: list[dict[str, object]], document_id: str
) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        stack: list[object] = [row]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                math_id = value.get("math_id")
                if (
                    value.get("surface") == "math"
                    and isinstance(math_id, str)
                    and math_id.startswith(document_id + "-")
                ):
                    ids.add(math_id)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
    return ids


def removed_unit_ids_from_corrections(
    rows: list[dict[str, object]], document_id: str
) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        stack: list[object] = [row]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                removed = value.get("removed_unit_ids")
                if value.get("surface") == "removed-editorial-structure" and isinstance(removed, list):
                    for unit_id in removed:
                        if isinstance(unit_id, str) and unit_id.startswith(document_id + "-"):
                            ids.add(unit_id)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
    return ids


def structural_math_correction_gate() -> dict[str, object]:
    corrections = parse_jsonl(CORRECTIONS.read_bytes(), "cumulative corrections")
    if len(corrections) != 170:
        raise RuntimeError("cumulative correction count differs")
    if [row.get("correction_id") for row in corrections] != [
        f"O006-PSU-ADV-{i:04d}" for i in range(1, 171)
    ]:
        raise RuntimeError("cumulative correction ID sequence differs")
    lesson_evidence: list[dict[str, object]] = []
    for component, (_, units, maths, correction_count, first_correction) in NEW_LESSONS.items():
        document_id = EXPECTED_IDS[component]
        source = BeautifulSoup(
            (ROOT / "source" / "normalized" / "en-US" / f"{component}.html").read_bytes(),
            "html.parser",
        ).select_one("main#quarto-document-content")
        target = BeautifulSoup(
            (ROOT / "source" / "id-ID" / f"{component}.html").read_bytes(),
            "html.parser",
        ).select_one("main#quarto-document-content")
        if source is None or target is None:
            raise RuntimeError(f"{component} source/target main missing")
        source_units = shared.stable_values(source, "data-o006-id")
        target_units = shared.stable_values(target, "data-o006-id")
        source_math_ids = shared.stable_values(source, "data-o006-math-id")
        target_math_ids = shared.stable_values(target, "data-o006-math-id")
        partition = corrections[first_correction - 1:first_correction - 1 + correction_count]
        removed_units = removed_unit_ids_from_corrections(partition, document_id)
        expected_target_units = [unit_id for unit_id in source_units if unit_id not in removed_units]
        if target_units != expected_target_units or len(source_units) != units:
            raise RuntimeError(f"{component} stable-unit topology differs")
        if source_math_ids != target_math_ids or len(source_math_ids) != maths:
            raise RuntimeError(f"{component} math topology differs")
        source_math = {
            str(node.get("data-o006-math-id")): node.get_text()
            for node in source.select("[data-o006-math-id]")
        }
        target_math = {
            str(node.get("data-o006-math-id")): node.get_text()
            for node in target.select("[data-o006-math-id]")
        }
        changed = {key for key in source_math if source_math[key] != target_math[key]}
        registered = changed_math_ids_from_corrections(partition, document_id)
        if changed != registered:
            raise RuntimeError(
                f"{component} changed/registered math differs: "
                f"unregistered={sorted(changed-registered)} unchanged-registered={sorted(registered-changed)}"
            )
        expected_findings = [f"L{component[-2:]}-D{i:03d}" for i in range(1, correction_count + 1)]
        if [row.get("source_defect_id") for row in partition] != expected_findings:
            raise RuntimeError(f"{component} source-finding binding differs")
        if shared.native_id_duplicates(target):
            raise RuntimeError(f"{component} target retains duplicate native IDs")
        lesson_evidence.append({
            "component": component,
            "stable_units": len(target_units),
            "registered_removed_units": sorted(removed_units),
            "math_nodes": len(target_math_ids),
            "changed_registered_math": sorted(changed),
            "corrections": correction_count,
        })
    return {
        "corrections": len(corrections),
        "backend": identity(CORRECTIONS),
        "lessons": lesson_evidence,
    }


def visible_prose(main: Tag) -> str:
    values: list[str] = []
    for node in main.find_all(string=True):
        if not isinstance(node, NavigableString) or not node.strip():
            continue
        if node.find_parent(["code", "pre", "style", "script"]):
            continue
        if node.find_parent(class_="math"):
            continue
        values.append(str(node))
    return "\n".join(values)


def reader_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    if len(reader_files) != 71:
        raise RuntimeError("reader file count differs")
    css_path = BUILD / "assets" / "reader-11of14.css"
    css = css_path.read_bytes()
    if not css.endswith(builder.REFLOW_CSS):
        raise RuntimeError("Lessons07-09 reflow CSS suffix differs")
    css_text = re.sub(r"\s+", " ", css.decode("utf-8"))
    for rule in ("width: 100%", "max-width: 100%", "height: auto", "margin-inline: auto", "overflow-x: auto"):
        if rule not in css_text:
            raise RuntimeError(f"responsive CSS rule missing: {rule}")

    total_units = 0
    total_math = 0
    total_images = 0
    total_tables = 0
    for component in EXPECTED_COMPONENTS:
        filename = "index.html" if component == "index" else f"{component}.html"
        soup = BeautifulSoup((BUILD / filename).read_bytes(), "html.parser")
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"{component} locale metadata differs")
        metadata = soup.select_one('meta[name="edition-status"]')
        provenance = soup.select_one('meta[name="translation-provenance"]')
        if (
            metadata is None
            or metadata.get("content") != "partial: 11 of 14 documents complete; landing and Lessons 00–09"
            or provenance is None
            or provenance.get("content") != PROVENANCE
        ):
            raise RuntimeError(f"{component} edition/provenance metadata differs")
        main = soup.select_one("main#quarto-document-content")
        if main is None:
            raise RuntimeError(f"{component} reader main missing")
        expected_units, expected_math = EXPECTED_COUNTS[component]
        units = shared.stable_values(main, "data-o006-id")
        maths = shared.stable_values(main, "data-o006-math-id")
        if len(units) != expected_units or len(maths) != expected_math:
            raise RuntimeError(f"{component} reader unit/math census differs")
        if shared.native_id_duplicates(main):
            raise RuntimeError(f"{component} reader native IDs duplicate")
        if main.select("script, iframe, object, embed, video, audio, source"):
            raise RuntimeError(f"{component} reader retains active/embed dependency")
        prose = visible_prose(main).casefold()
        forbidden = (
            "in this lesson", "the null hypothesis", "the alternative hypothesis",
            "confidence interval", "standard error", "solution", "example 9.",
        )
        present = [phrase for phrase in forbidden if phrase in prose]
        if present:
            raise RuntimeError(f"{component} visible untranslated phrase remains: {present}")
        for node in main.select("img[data-o006-asset-id]"):
            if len(str(node.get("alt") or "").strip()) < 20:
                raise RuntimeError(f"{component} image alternative incomplete")
            if node.get("style") and re.search(
                r"(?:^|;)\s*width\s*:", str(node.get("style")).casefold()
            ):
                raise RuntimeError(f"{component} image retains inline width")
        for node in soup.select("script[src], img[src], link[href]"):
            value = str(node.get("src") or node.get("href") or "")
            if value.startswith(("http://", "https://", "//")):
                if node.name == "link" and node.get("rel") == ["license"]:
                    continue
                raise RuntimeError(f"{component} external runtime/asset reference: {value}")
        total_units += len(units)
        total_math += len(maths)
        total_images += len(main.select("img[data-o006-asset-id]"))
        total_tables += len(main.select("table"))

    index = BeautifulSoup((BUILD / "index.html").read_bytes(), "html.parser")
    for number in range(13):
        expected = f"Lesson{number:02d}.html" if number <= 9 else f"https://online.stat.psu.edu/stat415/Lesson{number:02d}"
        links = index.select(f'a[data-translation-status][href="{expected}"]')
        if len(links) != 1:
            raise RuntimeError(f"index Lesson{number:02d} route differs")
        status = "complete" if number <= 9 else "pending"
        if links[0].get("data-translation-status") != status:
            raise RuntimeError(f"index Lesson{number:02d} status differs")

    lesson08 = BeautifulSoup((BUILD / "Lesson08.html").read_bytes(), "html.parser")
    main08 = lesson08.select_one("main#quarto-document-content")
    assert main08 is not None
    if len(main08.select("pre")) != 28 or len(main08.select("code")) < 20:
        raise RuntimeError("Lesson08 offline code/template surfaces differ")
    for node in main08.select("pre, .sourceCode, .cell-output"):
        hidden = str(node.get("style") or "").casefold()
        if node.has_attr("hidden") or "display:none" in hidden.replace(" ", ""):
            raise RuntimeError("Lesson08 offline code/output surface is hidden")

    lesson09 = BeautifulSoup((BUILD / "Lesson09.html").read_bytes(), "html.parser")
    main09 = lesson09.select_one("main#quarto-document-content")
    assert main09 is not None
    tables = main09.select("table")
    if len(tables) != 3:
        raise RuntimeError("Lesson09 table count differs")
    for table in tables:
        if len(table.select(":scope > caption")) != 1:
            raise RuntimeError("Lesson09 table caption missing")
        headers = table.select("th")
        if not headers or any(
            node.get("scope") not in {"row", "col", "colgroup"} for node in headers
        ):
            raise RuntimeError("Lesson09 table header semantics incomplete")

    if total_units != 4_763 or total_math != 2_171 or total_images != 34 or total_tables != 5:
        raise RuntimeError("cumulative reader structural census differs")
    license_text = (BUILD / "licenses" / "index.html").read_text("utf-8")
    if (
        "Pelajaran 00–09 lengkap" not in license_text
        or "CC BY-NC 4.0" not in license_text
        or PROVENANCE not in license_text
        or "dua belas koreksi Lesson 07" not in license_text
        or "tujuh belas koreksi Lesson 08" not in license_text
        or "sembilan belas koreksi Lesson 09" not in license_text
    ):
        raise RuntimeError("license/status/provenance disclosure differs")
    return {
        "files": len(reader_files),
        "bytes": sum((BUILD.joinpath(*path.parts)).stat().st_size for path in reader_files),
        "stable_units": total_units,
        "math_nodes": total_math,
        "substantive_images": total_images,
        "tables": total_tables,
        "responsive_css": identity(css_path),
        "offline_code_surfaces_lesson08": len(main08.select("pre")),
        "semantic_tables_lesson09": len(tables),
    }


def asset_rights_privacy_gate(build_receipt: dict[str, object]) -> dict[str, object]:
    assets = build_receipt["new_assets"]["inventory"]
    if not isinstance(assets, list) or len(assets) != 16:
        raise RuntimeError("new asset evidence differs")
    total = 0
    for row in assets:
        source = ROOT / str(row["source_path"])
        target = BUILD.joinpath(*PurePosixPath(str(row["target_path"])).parts)
        source_data = source.read_bytes()
        target_data = target.read_bytes()
        if (
            source_data != target_data
            or len(source_data) != int(row["source_bytes"])
            or sha256(source_data) != row["source_sha256"]
            or sha256(target_data) != row["target_sha256"]
        ):
            raise RuntimeError(f"asset byte preservation differs: {row['asset_id']}")
        total += len(source_data)
    if total != 4_574_263:
        raise RuntimeError("new asset byte total differs")
    sensitive = re.compile(
        r"(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|Bearer\s+[A-Za-z0-9._-]{16,}|"
        r"C:\\Users\\|/Users/|Downloads[/\\].*token|zenodo.*token)",
        re.IGNORECASE,
    )
    scanned = 0
    for path in shared.current_reader_files():
        if path.suffix.lower() not in {".html", ".css", ".js", ".txt", ".csv", ".json", ".svg"}:
            continue
        data = BUILD.joinpath(*path.parts).read_text("utf-8", errors="ignore")
        if sensitive.search(data):
            raise RuntimeError(f"sensitive/local path surface found: {path}")
        scanned += 1
    return {
        "authority_assets": len(assets),
        "authority_asset_bytes": total,
        "byte_preserving_targets": len(assets),
        "text_files_privacy_scanned": scanned,
        "rights": "CC BY-NC 4.0 except where otherwise noted",
        "external_runtime_dependencies": 0,
    }


def documents_manifest_gate(reader_files: set[PurePosixPath]) -> dict[str, object]:
    rows = parse_jsonl(DOCUMENTS.read_bytes(), "document backend")
    if len(rows) != 11 or [row.get("component_id") for row in rows] != EXPECTED_COMPONENTS:
        raise RuntimeError("document backend sequence differs")
    if (
        sum(int(row["translation_segments"]) for row in rows) != 3_458
        or sum(int(row["structural_units"]) for row in rows) != 4_775
        or sum(int(row["math_nodes"]) for row in rows) != 2_171
    ):
        raise RuntimeError("document backend cumulative census differs")
    for row in rows:
        target = ROOT / str(row["target_path"])
        data = target.read_bytes()
        if row.get("target_bytes") != len(data) or row.get("target_sha256") != sha256(data):
            raise RuntimeError(f"document target identity differs: {row.get('component_id')}")
    reader = {
        path: BUILD.joinpath(*path.parts).read_bytes() for path in reader_files
    }
    expected_manifest = first.manifest_payload(reader)
    if MANIFEST.read_bytes() != expected_manifest:
        raise RuntimeError("reader manifest differs")
    return {
        "documents": len(rows),
        "backend": identity(DOCUMENTS),
        "manifest": identity(MANIFEST),
    }


def compute() -> bytes:
    _, build_receipt, reader_files = deterministic_build_gate()
    translation = translation_backend_gate()
    structure = structural_math_correction_gate()
    reader = reader_gate(reader_files)
    assets = asset_rights_privacy_gate(build_receipt)
    documents = documents_manifest_gate(reader_files)
    receipt = {
        "schema": "o006.stat415.through-lesson09-qa.v1",
        "status": "passed",
        "coverage": {
            "complete_documents": 11,
            "corpus_documents": 14,
            "next_document": "Lesson10",
        },
        "translation_backend": translation,
        "structure_math_corrections": structure,
        "reader_accessibility_reflow": reader,
        "asset_rights_privacy": assets,
        "documents_manifest": documents,
        "build_receipt": identity(BUILD_RECEIPT),
        "checks": [
            "exact-971-new-segment-source-target-binding-replay",
            "exact-Lesson07-09-stable-unit-and-math-topology",
            "only-registered-mathematics-surfaces-change",
            "exact-contiguous-170-correction-registry",
            "all-sixteen-new-authority-assets-byte-preserved",
            "all-new-image-alternatives-complete",
            "Lesson08-code-and-output-surfaces-offline-visible",
            "Lesson09-three-tables-captioned-and-semantically-headed",
            "Lesson09-duplicate-native-identifiers-removed-in-target",
            "full-width-centered-responsive-figure-code-table-reflow",
            "no-external-runtime-analytics-cookie-or-iframe",
            "rights-provenance-status-and-nonendorsement-preserved",
            "sensitive-and-local-path-scan-clear",
            "deterministic-71-file-reader-and-manifest-replay",
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
            raise RuntimeError("Lesson09 QA receipt differs")
        state = "verified"
    data = json.loads(payload)
    print(json.dumps({
        "mode": state,
        "documents": data["coverage"]["complete_documents"],
        "new_segments": data["translation_backend"]["new_segments"],
        "stable_units": data["reader_accessibility_reflow"]["stable_units"],
        "math_nodes": data["reader_accessibility_reflow"]["math_nodes"],
        "corrections": data["structure_math_corrections"]["corrections"],
        "reader_files": data["reader_accessibility_reflow"]["files"],
        "receipt_sha256": sha256(payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
