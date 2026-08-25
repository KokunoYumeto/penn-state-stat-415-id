#!/usr/bin/env python3
"""Build the cumulative id-ID reader through Penn State STAT 415 Lesson 03."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as shared
import build_through_lesson02 as prior


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
TARGET = ROOT / "source" / "id-ID"
TRANSLATIONS = TARGET / "lesson03_translation.csv"
TRANSLATION_BINDINGS = ROOT / "backend" / "lesson03_translation_bindings.jsonl"
TRANSLATION_RECEIPT = ROOT / "build" / "LESSON03_TRANSLATION_RECEIPT.json"
ZERO_ASSET_CLOSURE = ROOT / "working" / "lesson03_zero_asset_closure.json"
SOURCE_FINDINGS = ROOT / "working" / "lesson03_source_findings.md"

DOCUMENTS_BACKEND = ROOT / "backend" / "through_lesson03_documents.jsonl"
CORRECTIONS_BACKEND = ROOT / "backend" / "through_lesson03_corrections.jsonl"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON03_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON03_BUILD_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson03"
DOCUMENT_ID = "O006-PSU-004"
EXPECTED_SEGMENTS = 531
EXPECTED_UNITS = 421
EXPECTED_MATH = 440
EXPECTED_TOTAL_SEGMENTS = 1599
EXPECTED_TOTAL_UNITS = 1399
EXPECTED_TARGET_UNITS = 1397
EXPECTED_TOTAL_MATH = 1149
EXPECTED_READER_FILES = 32
PRIOR_CSS_NAME = "reader-4of14.css"
CURRENT_CSS_NAME = "reader-5of14.css"

PUNCTUATION_BOUNDARY_EXCEPTIONS = {
    "O006-PSU-004-S0246": ",",
    "O006-PSU-004-S0248": ",",
    "O006-PSU-004-S0306": ".",
    "O006-PSU-004-S0419": ",",
}
WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS = {
    "O006-PSU-004-S0135",
    "O006-PSU-004-S0137",
    "O006-PSU-004-S0208",
    "O006-PSU-004-S0209",
    "O006-PSU-004-S0263",
    "O006-PSU-004-S0501",
    "O006-PSU-004-S0504",
    "O006-PSU-004-S0521",
    "O006-PSU-004-S0523",
}

HISTORICAL_REPLAY_OUTPUTS = {
    "build/THROUGH_LESSON02_MANIFEST.csv",
    "backend/through_lesson02_documents.jsonl",
    "backend/through_lesson02_corrections.jsonl",
}

HISTORICAL_PROTECTED_OUTPUTS = HISTORICAL_REPLAY_OUTPUTS | {
    "build/THROUGH_LESSON02_BUILD_RECEIPT.json",
    "build/THROUGH_LESSON02_QA_RECEIPT.json",
    "build/THROUGH_LESSON02_VISUAL_QA_RECEIPT.json",
}

FROZEN_INPUTS: dict[str, tuple[int, str]] = {
    "scripts/build_through_lesson02.py": (40684, "22d58702d08ca55c2301f0e3652fc9adc8d9469450c259413890854711cdc3b7"),
    "build/THROUGH_LESSON02_BUILD_RECEIPT.json": (6845, "f061911bb9dc8ab1c9f3a30701f00fcaf35ad96f260f49847d1c2d46cff4ee0e"),
    "build/THROUGH_LESSON02_MANIFEST.csv": (3081, "e0fe3c91465284cb10cf0bc802c32102bccb0eb0c84f108405a66044faf9f7ef"),
    "build/THROUGH_LESSON02_QA_RECEIPT.json": (11352, "79f83cf4e5690c1509c8c6fea415340c44b2513390955c62f42398bfe84dd14c"),
    "build/THROUGH_LESSON02_VISUAL_QA_RECEIPT.json": (7262, "ff88c85188969656be6bebb9a82504c148506baca7fba8bcdbe1738583f69d8e"),
    "backend/through_lesson02_documents.jsonl": (2680, "22f36e9a27466c271b8a9b507d356f73246b1484e1d9d13439329fc932bca474"),
    "backend/through_lesson02_corrections.jsonl": (10143, "db6ec366a1461c545d4c1ca93b2a76664868bb4e99878a0719d8e9ab2a976c19"),
    "authority/upstream/stat415/Lesson03.html": (118925, "26dd4efe75abc879a5316c215eaedbfe713c77e742898eb86e7f3d88cb0c04c9"),
    "scripts/normalize_lesson03.py": (35668, "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"),
    "source/normalized/en-US/Lesson03.html": (98397, "b7bf8db106f1e38d478220284c39ce89e6a9eaaaa1ae98804217c1733b75b17b"),
    "backend/lesson03_source_catalogue.jsonl": (654743, "6ee066954be5e3777a655d6c43440f7bb2a9379e665a5ba4997136aef509ed7a"),
    "working/lesson03_segments.csv": (94343, "ba6c4d7c905ec14babb1ac9a971a7195968978c581eeb0d4088d92889bdf8b8a"),
    "build/LESSON03_NORMALIZATION_RECEIPT.json": (12791, "693b5fbb2b410567e0c81e2232e46ad159a9958605b691b2badbd2f4b08d5fc6"),
    "source/id-ID/lesson03_translation.csv": (123145, "ab96512a2b7f8eb5d86b60dbcc2ad6779f74623367e4537b04167ce22bc8215a"),
    "backend/lesson03_translation_bindings.jsonl": (215593, "00202b65c0376c7065de20270980da6f0d14c50f38e7e946609e31981b903781"),
    "build/LESSON03_TRANSLATION_RECEIPT.json": (3131, "d120e1d1b8248070450a4e3d314a890e4b38b199faab364ce525638038676bc6"),
    "working/lesson03_source_findings.md": (6449, "904b9e72ccb362402ec1ef47df5ab13a8afad0738720220b6d37c00995c86df2"),
    "working/lesson03_zero_asset_closure.json": (1800, "e235e8ab499aa0ce542898d4aaf016e6932c807da8a06fdb9f0976f60547d705"),
    "00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv": (4774, "c1fe0f172a974c049973da3a9fcf40d724d8ce5f7ff2690e9ab8c78efbd35ae3"),
    "working/lesson03_terminology_qa.md": (2239, "d46c722d4c9748a0f1df35231492f850dab4789869ff9d00c75e14fe8c53e23b"),
}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_frozen_inputs() -> dict[str, dict[str, object]]:
    evidence: dict[str, dict[str, object]] = {}
    for name, (expected_bytes, expected_sha256) in sorted(FROZEN_INPUTS.items()):
        path = ROOT / name
        if not path.is_file():
            raise RuntimeError(f"frozen input missing: {name}")
        payload = path.read_bytes()
        actual_sha256 = first.sha256(payload)
        if len(payload) != expected_bytes or actual_sha256 != expected_sha256:
            raise RuntimeError(f"frozen input differs: {name}")
        evidence[name] = {"bytes": len(payload), "sha256": actual_sha256}
    return evidence


def parse_jsonl(payload: bytes, label: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    try:
        for line in payload.decode("utf-8").splitlines():
            if line:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise RuntimeError(f"{label} contains a non-object row")
                rows.append(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid {label}: {exc}") from exc
    return rows


def validate_translation_receipt() -> None:
    receipt = json.loads(TRANSLATION_RECEIPT.read_text("utf-8"))
    if receipt.get("schema") != "o006.stat415.lesson03-translation.v1":
        raise RuntimeError("Lesson03 translation-receipt schema differs")
    if receipt.get("status") != "complete" or receipt.get("segment_count") != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson03 translation receipt is not complete")
    if receipt.get("translation_provenance") != PROVENANCE:
        raise RuntimeError("Lesson03 translation provenance differs")
    expected_punctuation = [
        {"punctuation": punctuation, "segment_id": segment_id}
        for segment_id, punctuation in sorted(PUNCTUATION_BOUNDARY_EXCEPTIONS.items())
    ]
    if receipt.get("punctuation_boundary_exceptions") != expected_punctuation:
        raise RuntimeError("Lesson03 punctuation-boundary registry differs")
    if receipt.get("word_boundary_leading_space_exceptions") != sorted(WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS):
        raise RuntimeError("Lesson03 word-boundary registry differs")
    csv_record = receipt.get("translation_csv")
    binding_record = receipt.get("bindings")
    if not isinstance(csv_record, dict) or not isinstance(binding_record, dict):
        raise RuntimeError("Lesson03 translation receipt lacks output identities")
    csv_payload = TRANSLATIONS.read_bytes()
    binding_payload = TRANSLATION_BINDINGS.read_bytes()
    expected = (
        (csv_record, relative(TRANSLATIONS), csv_payload),
        (binding_record, relative(TRANSLATION_BINDINGS), binding_payload),
    )
    for record, path, payload in expected:
        if (
            record.get("path") != path
            or record.get("bytes") != len(payload)
            or record.get("sha256") != first.sha256(payload)
        ):
            raise RuntimeError(f"Lesson03 translation receipt identity differs: {path}")


def validate_zero_asset_closure(main: Tag) -> None:
    closure = json.loads(ZERO_ASSET_CLOSURE.read_text("utf-8"))
    if (
        closure.get("schema") != "o006.stat415.lesson03-zero-asset-closure.v1"
        or closure.get("status") != "verified-zero-main-content-assets"
        or closure.get("component_id") != "Lesson03"
        or closure.get("document_id") != DOCUMENT_ID
    ):
        raise RuntimeError("Lesson03 zero-asset closure identity differs")
    source = closure.get("source")
    if not isinstance(source, dict) or source.get("bytes") != 118925 or source.get("sha256") != FROZEN_INPUTS["authority/upstream/stat415/Lesson03.html"][1]:
        raise RuntimeError("Lesson03 zero-asset source identity differs")
    census = closure.get("dependency_census")
    if not isinstance(census, dict) or any(value != 0 for value in census.values()):
        raise RuntimeError("Lesson03 zero-asset census differs")
    if main.select("img, audio, video, source, iframe, embed, object, script"):
        raise RuntimeError("Lesson03 normalized main unexpectedly contains an asset/runtime node")
    for node in main.select("a[href]"):
        href = str(node.get("href"))
        if href.lower().endswith((".csv", ".doc", ".docx", ".pdf", ".r", ".rdata", ".txt", ".xls", ".xlsx", ".zip")):
            raise RuntimeError(f"Lesson03 normalized main unexpectedly contains a download: {href}")


def load_lesson03() -> tuple[
    BeautifulSoup,
    Tag,
    list[dict[str, str]],
    list[str],
    list[str],
    list[str],
]:
    validate_translation_receipt()
    if not TRANSLATIONS.is_file():
        raise RuntimeError("Lesson03 translation CSV is not yet present")
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        expected_fields = [
            "segment_id", "document_id", "component_id", "section_id",
            "source_sha256", "source_text", "target_text", "status",
        ]
        if reader.fieldnames != expected_fields:
            raise RuntimeError("Lesson03 translation CSV schema differs")
        rows = list(reader)
    if len(rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson03 translation boundary is not 531 segments")

    soup = BeautifulSoup((NORMALIZED / "Lesson03.html").read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("normalized Lesson03 main is missing")
    validate_zero_asset_closure(main)
    source_math = [node.get_text() for node in main.select(".math")]
    if len(source_math) != EXPECTED_MATH:
        raise RuntimeError("normalized Lesson03 math-node count differs")
    unit_ids = shared.stable_values(main, "data-o006-id")
    math_ids = shared.stable_values(main, "data-o006-math-id")
    if unit_ids != [f"O006-PSU-004-U{i:04d}" for i in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson03 structural-unit identity sequence differs")
    if math_ids != [f"O006-PSU-004-M{i:04d}" for i in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson03 math identity sequence differs")
    if shared.native_id_duplicates(main):
        raise RuntimeError("Lesson03 normalized source has unexpected duplicate native IDs")

    binding_rows = parse_jsonl(TRANSLATION_BINDINGS.read_bytes(), "Lesson03 translation bindings")
    if len(binding_rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson03 translation binding count differs")
    nodes = shared.translatable_nodes(main)
    if len(nodes) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson03 translatable-node count differs")
    for ordinal, (row, binding, node) in enumerate(zip(rows, binding_rows, nodes), start=1):
        sid = f"O006-PSU-004-S{ordinal:04d}"
        if row["segment_id"] != sid or row["document_id"] != DOCUMENT_ID or row["component_id"] != "Lesson03":
            raise RuntimeError(f"Lesson03 segment identity differs: {sid}")
        source_text = str(node)
        target_text = row["target_text"]
        source_sha256 = first.sha256(source_text.encode("utf-8"))
        target_sha256 = first.sha256(target_text.encode("utf-8"))
        if row["source_text"] != source_text or row["source_sha256"] != source_sha256:
            raise RuntimeError(f"Lesson03 source text/hash differs: {sid}")
        if row["status"] != "translated" or not target_text.strip():
            raise RuntimeError(f"Lesson03 translation unfinished: {sid}")
        if "\ufffd" in target_text:
            raise RuntimeError(f"Lesson03 target contains replacement character: {sid}")
        if sid in PUNCTUATION_BOUNDARY_EXCEPTIONS:
            punctuation = PUNCTUATION_BOUNDARY_EXCEPTIONS[sid]
            if not source_text.startswith(" ") or not target_text.startswith(punctuation) or target_text.startswith(f" {punctuation}"):
                raise RuntimeError(f"Lesson03 punctuation-boundary exception differs: {sid}")
            if source_text.endswith(" ") != target_text.endswith(" "):
                raise RuntimeError(f"Lesson03 trailing boundary whitespace differs: {sid}")
        elif sid in WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS:
            if not target_text.startswith(" ") or target_text.startswith("  "):
                raise RuntimeError(f"Lesson03 word-boundary leading-space exception differs: {sid}")
            if source_text.endswith(" ") != target_text.endswith(" "):
                raise RuntimeError(f"Lesson03 word-boundary trailing whitespace differs: {sid}")
        elif shared.boundary_whitespace(source_text) != shared.boundary_whitespace(target_text):
            raise RuntimeError(f"Lesson03 boundary whitespace differs: {sid}")
        expected_binding = {
            "schema": "o006.stat415.translation-binding.v1",
            "document_id": DOCUMENT_ID,
            "component_id": "Lesson03",
            "locale": "id-ID",
            "ordinal": ordinal,
            "segment_id": sid,
            "section_id": row["section_id"] or None,
            "source_sha256": source_sha256,
            "target_sha256": target_sha256,
            "status": "translated",
        }
        if binding != expected_binding:
            raise RuntimeError(f"Lesson03 translation binding differs: {sid}")
        node.replace_with(NavigableString(target_text))
    return soup, main, rows, source_math, unit_ids, math_ids


def set_math_surface(main: Tag, math_id: str, expected_sha256: str, target: str) -> dict[str, str]:
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"math correction identity differs: {math_id}")
    node = nodes[0]
    before = node.get_text()
    if first.sha256(before.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"math correction source differs: {math_id}")
    if before == target:
        raise RuntimeError(f"math correction makes no change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "math_id": math_id,
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": first.sha256(target.encode("utf-8")),
    }


def single_math_record(
    main: Tag,
    defect_number: int,
    math_id: str,
    source_sha256: str,
    target: str,
    *,
    note: str | None = None,
) -> dict[str, object]:
    record: dict[str, object] = {
        "correction_id": f"O006-PSU-ADV-{29 + defect_number:04d}",
        "source_defect_id": f"L03-D{defect_number:03d}",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **set_math_surface(main, math_id, source_sha256, target),
    }
    if note is not None:
        record["note"] = note
    return record


def rebuild_prose_unit(
    main: Tag,
    *,
    defect_number: int,
    unit_id: str,
    expected_before_sha256: str,
    segment_ids: list[str],
    math_ids: list[str],
    parts: list[str],
    note: str,
) -> dict[str, object]:
    units = main.select(f'[data-o006-id="{unit_id}"]')
    if len(units) != 1:
        raise RuntimeError(f"prose correction unit identity differs: {unit_id}")
    unit = units[0]
    before_markup = str(unit)
    before_sha256 = first.sha256(before_markup.encode("utf-8"))
    if before_sha256 != expected_before_sha256:
        raise RuntimeError(f"prose correction source differs: {unit_id}")
    math_nodes = {str(node.get("data-o006-math-id")): node for node in unit.select("[data-o006-math-id]")}
    if list(math_nodes) != math_ids:
        raise RuntimeError(f"prose correction protected-math sequence differs: {unit_id}")
    for node in math_nodes.values():
        node.extract()
    unit.clear()
    for part in parts:
        if part in math_nodes:
            unit.append(math_nodes[part])
        else:
            unit.append(NavigableString(part))
    after_markup = str(unit)
    after_sha256 = first.sha256(after_markup.encode("utf-8"))
    if before_sha256 == after_sha256:
        raise RuntimeError(f"prose correction makes no change: {unit_id}")
    if shared.stable_values(unit, "data-o006-math-id") != math_ids:
        raise RuntimeError(f"prose correction altered protected math identities: {unit_id}")
    return {
        "correction_id": f"O006-PSU-ADV-{29 + defect_number:04d}",
        "source_defect_id": f"L03-D{defect_number:03d}",
        "status": "applied-target-only",
        "surface": "prose-unit",
        "replacement_count": 1,
        "unit_id": unit_id,
        "segment_ids": segment_ids,
        "protected_math_ids": math_ids,
        "source_unit_sha256": before_sha256,
        "target_unit_sha256": after_sha256,
        "note": note,
    }


def record_translation_layer_prose_correction(
    main: Tag,
    *,
    defect_number: int,
    unit_id: str,
    expected_source_sha256: str,
    expected_target_sha256: str,
    segment_ids: list[str],
    math_ids: list[str],
    note: str,
) -> dict[str, object]:
    source_soup = BeautifulSoup((NORMALIZED / "Lesson03.html").read_bytes(), "html.parser")
    source_units = source_soup.select(f'[data-o006-id="{unit_id}"]')
    target_units = main.select(f'[data-o006-id="{unit_id}"]')
    if len(source_units) != 1 or len(target_units) != 1:
        raise RuntimeError(f"translation-layer prose correction identity differs: {unit_id}")
    source_unit = source_units[0]
    target_unit = target_units[0]
    source_sha256 = first.sha256(str(source_unit).encode("utf-8"))
    target_sha256 = first.sha256(str(target_unit).encode("utf-8"))
    if source_sha256 != expected_source_sha256 or target_sha256 != expected_target_sha256:
        raise RuntimeError(f"translation-layer prose correction surface differs: {unit_id}")
    if shared.stable_values(source_unit, "data-o006-math-id") != math_ids:
        raise RuntimeError(f"translation-layer source math identities differ: {unit_id}")
    if shared.stable_values(target_unit, "data-o006-math-id") != math_ids:
        raise RuntimeError(f"translation-layer target math identities differ: {unit_id}")
    return {
        "correction_id": f"O006-PSU-ADV-{29 + defect_number:04d}",
        "source_defect_id": f"L03-D{defect_number:03d}",
        "status": "applied-target-only",
        "surface": "prose-unit",
        "application_layer": "translation-bindings",
        "replacement_count": 1,
        "unit_id": unit_id,
        "segment_ids": segment_ids,
        "protected_math_ids": math_ids,
        "source_unit_sha256": source_sha256,
        "target_unit_sha256": target_sha256,
        "note": note,
    }


def apply_lesson03_corrections(main: Tag) -> list[dict[str, object]]:
    finding_ids = re.findall(r"^### (L03-D\d{3})\b", SOURCE_FINDINGS.read_text("utf-8"), re.MULTILINE)
    expected_finding_ids = [f"L03-D{i:03d}" for i in range(1, 18)]
    if finding_ids != expected_finding_ids:
        raise RuntimeError("Lesson03 source-finding identity sequence differs")

    records: list[dict[str, object]] = []
    records.append(single_math_record(
        main, 1, "O006-PSU-004-M0290",
        "942abd5476d3e7d6b0df018b4fbcc134c90aab7da68a8cf0109a63ebeb652168",
        r"\(N(\theta_1, \theta_2).\)",
    ))
    records.append(single_math_record(
        main, 2, "O006-PSU-004-M0302",
        "86beff73307117c1fdc80ad1b313a70c48067146bdac7639278fe120ca974674",
        r"\[f(x_1, x_2, ... , x_n;\theta_1, \theta_2) = \dfrac{1}{\sqrt{2\pi\theta_2}} \exp \left[-\dfrac{1}{2}\dfrac{(x_1-\theta_1)^2}{\theta_2} \right] \times \cdots \times \dfrac{1}{\sqrt{2\pi\theta_2}} \exp \left[-\dfrac{1}{2}\dfrac{(x_n-\theta_1)^2}{\theta_2} \right]\]",
    ))
    records.append(single_math_record(
        main, 3, "O006-PSU-004-M0311",
        "85fd8f7b04cdf792d3d6740e95004cb8e9ecb718e2a53bb1b63f512951c5d40a",
        r"\[f(x_1, x_2, ... , x_n;\theta_1, \theta_2) = \color{blue}{\underbrace{{\color{black}{\exp \left[ -\dfrac{1}{2\theta_2}\sum_{i=1}^{n}x_{i}^{2}+\dfrac{\theta_1}{\theta_2}\sum_{i=1}^{n}x_{i} -\dfrac{n\theta_{1}^{2}}{2\theta_2}-n\log\sqrt{2\pi\theta_2} \right]}}}_{\textstyle \phi[u_1(\sum_i x_i^2),u_2(\sum_i x_i);\theta_1,\theta_2]}}\times \color{red}\underbrace{\color{black}{1}}_{\textstyle h(x_1,...,x_n)}\]",
    ))
    records.append(single_math_record(
        main, 4, "O006-PSU-004-M0345",
        "55865a1339c32dcc239c348f30ff19ece27bbfaf4a457f50edc2e97b3c94dd22",
        r"\[f(x;\theta_1,\theta_2) = \exp[-\frac{1}{2\theta_2}{\color{blue}\underbrace{\color{black}x^2}_{\textstyle K_1(x)}}+\frac{\theta_1}{\theta_2}{\color{blue}\underbrace{\color{black}x}_{\textstyle K_2(x)}}-{\color{brown}\underbrace{\color{black}\log(1)}_{\textstyle S(x)}}+{\color{green}\underbrace{\color{black}\left(-\frac{\theta_1^2}{2\theta_2}-\log\sqrt{2\pi\theta_2}\right)}_{\textstyle q(\theta_1,\theta_2)}}]\]",
    ))
    records.append(rebuild_prose_unit(
        main,
        defect_number=5,
        unit_id="O006-PSU-004-U0127",
        expected_before_sha256="b6efa055510ecd5f5bf554621d8c916cf6f841364d330acf6b0694b70bd13c6d",
        segment_ids=[f"O006-PSU-004-S{i:04d}" for i in range(190, 194)],
        math_ids=[f"O006-PSU-004-M{i:04d}" for i in range(152, 155)],
        parts=[
            "Sebaliknya, ", "O006-PSU-004-M0152", " bukan merupakan statistik cukup bagi ",
            "O006-PSU-004-M0153", ". Sampel konstan (a, …, a) dan (−a, …, −a) memberikan nilai ",
            "O006-PSU-004-M0154", " yang sama, tetapi rasio fungsi kemungkinan keduanya adalah exp(2naμ), "
            "yang bergantung pada parameter. Jadi, kriteria rasio fungsi kemungkinan membuktikan bahwa statistik tersebut tidak cukup.",
        ],
        note="replaced non-injectivity alone with an explicit equal-statistic, parameter-dependent likelihood-ratio counterexample",
    ))
    records.append(single_math_record(
        main, 6, "O006-PSU-004-M0086",
        "d4304a305b0bf8e3b94fd1d8323f3f39df0334dbb85671ee358ea29fa6e71301",
        r"\(h(x_1, x_2, \ldots, x_n)\)",
    ))

    d007_surfaces = [
        set_math_surface(
            main, "O006-PSU-004-M0105",
            "cb7f0d3050b0456f24a62eb87f359c89adf77042a519129afad04736d575aa34",
            r"\[f(x_1, x_2, \ldots, x_n;\lambda) = {\color{blue}\underbrace{\color{black} \left(e^{-n\lambda}\lambda^{n\bar{x}} \right)}_{\textstyle \color{blue}{\phi(\sum_{i=1}^{n}x_i;\lambda)}}} \times {\color{red}\underbrace{\color{black}\left( \frac{1}{x_1! x_2! \ldots x_n!} \right)}_{\textstyle \color{red}{h(x_1, x_2, \ldots,x_n)}}}\]",
        ),
        set_math_surface(
            main, "O006-PSU-004-M0143",
            "67af0b1eedb0fd2e74947603bf7942b210c2d125e25cccc6a47b963a91f83aa2",
            r"\[f(x_1, x_2, ... , x_n;\mu) = {\color{blue}{\underbrace{\color{black}{\left\{ \exp \left[ -\dfrac{n}{2} (\bar{x}-\mu)^2 \right] \right\}}}_{\textstyle \color{blue}{\phi(\bar{x};\mu)}}}} \times \color{red}{\underbrace{\color{black}{\left\{ \dfrac{1}{(2\pi)^{n/2}} \exp \left[ -\dfrac{1}{2}\sum_{i=1}^{n} (x_i - \bar{x})^2 \right] \right\}}}_{\textstyle\color{red}{h(x_1, x_2,...,x_n)}}}\]",
        ),
        set_math_surface(
            main, "O006-PSU-004-M0173",
            "657092633e82cc6d308b2f0c47ae786cd30c1e6974a721c2bbe097a6f1978237",
            r"\[f(x_1, x_2, ... , x_n;\theta) ={\color{blue}{\underbrace{\color{black}{\dfrac{1}{\theta^n}\exp\left( - \dfrac{1}{\theta} \sum_{i=1}^{n} x_i\right)}}_{\textstyle \color{blue}{\phi(\sum_{i=1}^{n}x_i;\theta)}}}}\times{\color{red}{\underbrace{\color{black}1}_{\textstyle \color{red}h(x_1,x_2,...,x_n)}}}\]",
        ),
        set_math_surface(
            main, "O006-PSU-004-M0258",
            "fc67dbb9c69bd9809fca4e9bdded2f92ca05cb2682649712b787ccc6f2d30313",
            r"\[f(x_1, ... , x_n;\theta)={\color{blue} \underbrace{\color{black}{\left\{ \exp\left[p(\theta)\sum_{i=1}^{n}K(x_i) + nq(\theta)\right]\right\}}}_{\textstyle \color{blue}\phi(\sum_{i=1}^{n}K(x_i);\theta)}} \times {\color{red}\underbrace{\color{black}\left\{ \exp\left[\sum_{i=1}^{n}S(x_i)\right] \right\}}_{\textstyle \color{red}h(x_1,...,x_n)}}\]",
        ),
    ]
    records.append({
        "correction_id": "O006-PSU-ADV-0036",
        "source_defect_id": "L03-D007",
        "status": "applied-target-only",
        "surface": "math-multiple",
        "replacement_count": len(d007_surfaces),
        "surfaces": d007_surfaces,
    })
    records.append(record_translation_layer_prose_correction(
        main,
        defect_number=8,
        unit_id="O006-PSU-004-U0140",
        expected_source_sha256="612e19ffe48aebd21781ef6bf24d9ba0c3493f610129714619143862c2d3ee6f",
        expected_target_sha256="2e247039db2e7c98be3b22a3e2853ec5faee81d040ef3dbb70401250d99bbf75",
        segment_ids=[f"O006-PSU-004-S{i:04d}" for i in range(206, 210)],
        math_ids=[f"O006-PSU-004-M{i:04d}" for i in range(165, 169)],
        note="translation bindings distinguish combining theta factors from adding the exponential-argument terms",
    ))
    records.append(single_math_record(
        main, 9, "O006-PSU-004-M0199",
        "69758d2a91e0d92ff4a0c9f0618cecb7d479a117998a6d04e684da6e48ee9674",
        r"\[f(x;p) = \exp\left[\ln(p^x) + \ln((1-p)^{1-x}) \right]\]",
    ))
    records.append(single_math_record(
        main, 10, "O006-PSU-004-M0209",
        "b5adbe972215404d0340ed5489a70b75c7cb5ab70cd824d97ef992658c0f9a09",
        r"\[f(x;p) = \exp\left[x\ln p+\ln(1-p)-x\ln(1-p)\right]\]",
        note="retained the genuine Bernoulli log-pmf identity before collecting the x terms",
    ))
    records.append(single_math_record(
        main, 11, "O006-PSU-004-M0216",
        "aa5230296814891c9b006bb464dd04bdf76799b35f96abf506fbf1d8b5671f9b",
        r"\[f(x;\lambda) =\frac{e^{-\lambda}\lambda^x}{x!}=\exp[{\color{blue}\underbrace{\color{black}x}_{\textstyle k(x)}}{\color{red}\underbrace{\color{black}\ln\lambda}_{\textstyle p(\lambda)}}+{\color{brown}\underbrace{\color{black}(-\ln(x!))}_{\textstyle s(x)}}+{\color{green}\underbrace{\color{black}(-\lambda)}_{\textstyle q(\lambda)}}]\]",
    ))
    records.append(single_math_record(
        main, 12, "O006-PSU-004-M0226",
        "afc46213c4dc25b0b45b4965ea44e69ada35bd7cc8c18fba8264983ab99d1287",
        r"\[f(x;\mu) =\frac{1}{\sqrt{2\pi}}e^{-(x-\mu)^2/2}=\exp\left\{{\color{blue}\underbrace{\color{black}x}_{\textstyle k(x)}}{\color{red}\underbrace{\color{black}\mu}_{\textstyle p(\mu)}}+{\color{brown}\underbrace{\color{black}\left(-\frac{x^2}{2}\right)}_{\textstyle s(x)}}+{\color{green}\underbrace{\color{black}\left(-\frac{\mu^2}{2}-\frac{1}{2}\ln(2\pi)\right)}_{\textstyle q(\mu)}}\right\}\]",
    ))
    records.append(single_math_record(
        main, 13, "O006-PSU-004-M0299",
        "22bff8653ae6a127edf519bd93a8d0cc3dcf0690754ce95f5e0e6a7c398c72ff",
        r"\[f(x_1, x_2, ... , x_n;\theta_1, \theta_2) = f(x_1;\theta_1, \theta_2) \times f(x_2;\theta_1, \theta_2) \times ... \times f(x_n;\theta_1, \theta_2)\]",
    ))
    records.append(single_math_record(
        main, 14, "O006-PSU-004-M0304",
        "695cac85e3f5b9b2af16f88b16353a025539a4989481f1825e01b45e06c7d6d1",
        r"\[f(x_1, x_2, ... , x_n;\theta_1, \theta_2) = \exp \left[n\log\left(\dfrac{1}{\sqrt{2\pi\theta_2}}\right)-\dfrac{1}{2\theta_2}\left\{ \sum_{i=1}^{n}x_{i}^{2} -2\theta_1\sum_{i=1}^{n}x_{i} +\sum_{i=1}^{n}\theta_{1}^{2} \right\}\right]\]",
    ))
    records.append(single_math_record(
        main, 15, "O006-PSU-004-M0318",
        "84c2b866d975e917220b86355a487586bcb8455849c43aec6385eb7ed36c4b45",
        r"\[\begin{align}\bar{X} &=\dfrac{Y_2}{n}=\dfrac{1}{n}\sum_{i=1}^{n}X_i \\ &\text{ and }\\ S^2&=\dfrac{Y_1-(Y_{2}^{2}/n)}{n-1}\\&=\dfrac{1}{n-1} \left[\sum_{i=1}^{n}X_{i}^{2}-n\bar{X}^2 \right]\end{align}\]",
    ))
    records.append(single_math_record(
        main, 16, "O006-PSU-004-M0389",
        "8b4383f37c691d1f0769516705301f5132a465f0254cfc5b6693242c3fd893a6",
        r"\[\hat{\sigma}^2_{MM}=\dfrac{1}{n}\sum\limits_{i=1}^n X_i^2-\widehat{\mu}_{MM}^{\,2}=\dfrac{1}{n}\sum\limits_{i=1}^n X_i^2-\bar{X}^2\]",
    ))
    d017_surfaces = [
        set_math_surface(
            main, "O006-PSU-004-M0401",
            "1352cf3e7b94ae1e9f7039638f298e56177fd0570a213afce068a6905f8bee72",
            r"\[f(x_i)=\dfrac{1}{\Gamma(\alpha) \theta^\alpha}x_i^{\alpha-1}e^{-x_i/\theta}\]",
        ),
        set_math_surface(
            main, "O006-PSU-004-M0402",
            "256f1007fd0984d60701c31da2eb3a6b025372345bfa2764d8e0206cf42db96d",
            r"\(x_i>0.\)",
        ),
    ]
    records.append({
        "correction_id": "O006-PSU-ADV-0046",
        "source_defect_id": "L03-D017",
        "status": "applied-target-only",
        "surface": "math-multiple",
        "replacement_count": len(d017_surfaces),
        "surfaces": d017_surfaces,
    })

    expected_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(30, 47)]
    if [str(row["correction_id"]) for row in records] != expected_ids:
        raise RuntimeError("Lesson03 correction registry order differs")
    if [str(row["source_defect_id"]) for row in records] != expected_finding_ids:
        raise RuntimeError("Lesson03 correction/finding mapping differs")
    if any(row["status"] != "applied-target-only" for row in records):
        raise RuntimeError("Lesson03 correction status differs")
    return records


def patch_previous_document(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<meta name="edition-status" content="partial: 4 of 14 documents complete; landing and Lessons 00–02">',
            '<meta name="edition-status" content="partial: 5 of 14 documents complete; landing and Lessons 00–03">',
        ),
        (
            '<a href="Lesson02.html">Pelajaran 02</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson02.html">Pelajaran 02</a><a href="Lesson03.html">Pelajaran 03</a><a href="licenses/index.html">Lisensi</a>',
        ),
        (
            '<strong>Edisi Bahasa Indonesia — 4 dari 14 dokumen.</strong>',
            '<strong>Edisi Bahasa Indonesia — 5 dari 14 dokumen.</strong>',
        ),
        (
            'Laman utama serta Pelajaran 00–02 telah diterjemahkan sepenuhnya.',
            'Laman utama serta Pelajaran 00–03 telah diterjemahkan sepenuhnya.',
        ),
        (
            'Pelajaran 03–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.',
            'Pelajaran 04–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.',
        ),
    )
    for old, new in replacements:
        if text.count(old) != 1:
            raise RuntimeError(f"previous-page status surface differs: {filename}: {old}")
        text = text.replace(old, new, 1)
    old_css = f'<link rel="stylesheet" href="assets/{PRIOR_CSS_NAME}">'
    new_css = f'<link rel="stylesheet" href="assets/{CURRENT_CSS_NAME}">'
    if text.count(old_css) != 1:
        raise RuntimeError(f"previous-page CSS surface differs: {filename}")
    text = text.replace(old_css, new_css, 1)
    if filename == "index.html":
        old_anchor = (
            '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0061" '
            'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson03" '
            'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        )
        new_anchor = (
            '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0061" '
            'data-translation-status="complete" href="Lesson03.html">'
        )
        if text.count(old_anchor) != 1:
            raise RuntimeError("index Lesson03 card surface differs")
        text = text.replace(old_anchor, new_anchor, 1)
    return text.encode("utf-8")


def page_document(main: Tag, component: str, source_url: str) -> bytes:
    title_node = main.select_one("h1")
    if title_node is None:
        raise RuntimeError(f"missing translated title: {component}")
    title = html.escape(title_node.get_text(" ", strip=True))
    source = html.escape(source_url, quote=True)
    note = (
        '<aside class="edition-note" aria-label="Status edisi">'
        '<strong>Edisi Bahasa Indonesia — 5 dari 14 dokumen.</strong> '
        'Laman utama serta Pelajaran 00–03 telah diterjemahkan sepenuhnya. '
        'Pelajaran 04–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai. '
        f'<a href="{source}">Sumber resmi halaman ini</a>. '
        '<a href="licenses/index.html">Atribusi, perubahan, dan lisensi</a>.'
        '</aside>'
    )
    markup = (
        "<!doctype html>\n"
        '<html lang="id-ID">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{source}">\n'
        f'<meta name="translation-provenance" content="{PROVENANCE}">\n'
        '<meta name="edition-status" content="partial: 5 of 14 documents complete; landing and Lessons 00–03">\n'
        '<link rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">\n'
        f'<link rel="stylesheet" href="assets/{CURRENT_CSS_NAME}">\n'
        '<script defer src="assets/MathJax/tex-svg.js"></script>\n</head>\n<body>\n'
        '<a class="skip-link" href="#quarto-document-content">Lewati ke isi utama</a>\n'
        '<header class="site-header"><div class="site-header__inner">'
        '<div><p class="site-title">STAT 415 — Pengantar Statistika Matematis</p>'
        '<p class="site-subtitle">Rekonstruksi dan terjemahan Bahasa Indonesia · O006/C140</p></div>'
        '<nav class="site-nav" aria-label="Navigasi utama">'
        '<a href="index.html">Daftar pelajaran</a><a href="Lesson00.html">Pelajaran 00</a>'
        '<a href="Lesson01.html">Pelajaran 01</a><a href="Lesson02.html">Pelajaran 02</a>'
        '<a href="Lesson03.html">Pelajaran 03</a><a href="licenses/index.html">Lisensi</a>'
        '</nav></div></header>\n'
        f'<div class="page-shell">{note}{str(main)}</div>\n'
        '<footer class="site-footer"><div class="site-footer__inner">'
        'Konten sumber: Departemen Statistika Penn State, CC BY-NC 4.0 kecuali dinyatakan lain. '
        f'Terjemahan dan rekonstruksi: {PROVENANCE}. Tidak ada dukungan atau pengesahan yang tersirat.'
        '</div></footer>\n</body>\n</html>\n'
    )
    return markup.encode("utf-8")


def license_page() -> bytes:
    markup = f"""<!doctype html>
<html lang="id-ID"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atribusi, perubahan, dan lisensi — STAT 415 Bahasa Indonesia</title>
<link rel="stylesheet" href="../assets/{CURRENT_CSS_NAME}"></head><body>
<a class="skip-link" href="#licence-main">Lewati ke isi utama</a>
<header class="site-header"><div class="site-header__inner"><div><p class="site-title">Atribusi dan lisensi komponen</p>
<p class="site-subtitle">STAT 415 — edisi Bahasa Indonesia</p></div><nav class="site-nav" aria-label="Navigasi utama"><a href="../index.html">Daftar pelajaran</a><a href="../Lesson00.html">Pelajaran 00</a><a href="../Lesson01.html">Pelajaran 01</a><a href="../Lesson02.html">Pelajaran 02</a><a href="../Lesson03.html">Pelajaran 03</a></nav></div></header>
<div class="page-shell"><main id="licence-main"><h1>Atribusi, perubahan, dan lisensi</h1>
<h2>Konten Penn State</h2><p>Catatan mata kuliah resmi dirancang dan dikembangkan oleh <a href="https://science.psu.edu/stat">Departemen Statistika Penn State</a>. Menurut halaman sumber, kontennya tersedia di bawah <a rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)</a>, kecuali dinyatakan lain.</p>
<p>Edisi ini merupakan terjemahan dan rekonstruksi tidak resmi. Perubahan meliputi penerjemahan ke id-ID, sumber HTML semantik yang dinormalisasi, identitas mesin tambahan, gaya pembaca lokal, kontrol HTML aksesibel, teks alternatif gambar, serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, sembilan koreksi Lesson 02, dan tujuh belas koreksi Lesson 03 yang dicatat secara terpisah. Byte sumber resmi tidak diubah. Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat.</p>
<p>Lima gambar pengajaran Lesson 01 dan dua gambar Lesson 02 dipertahankan dari URL resmi halaman masing-masing di bawah pemberitahuan CC BY-NC 4.0 yang sama; setiap identitas, URL, byte, hash, dan keterbatasan bukti hak dicatat dalam audit aset. Lesson 03 tidak memiliki aset isi yang perlu dibekukan. Sumber resmi: <a href="https://online.stat.psu.edu/stat415/">STAT 415</a>. Status edisi saat ini: laman utama serta Pelajaran 00–03 lengkap; Pelajaran 04–12 belum diterjemahkan.</p>
<h2>MathJax</h2><p>MathJax 3.1.2 digunakan secara lokal untuk merender matematika dan tersedia di bawah Apache License 2.0. <a href="MathJax-3.1.2-LICENSE.txt">Baca teks lisensi yang disertakan</a>.</p>
<h2>Provenans</h2><p>{PROVENANCE}. Seluruh kredit sumber dan kontributor manusia tetap dipertahankan.</p>
</main></div><footer class="site-footer"><div class="site-footer__inner">Koleksi C140 mempertahankan identitas dan lisensi setiap komponen; tidak ada relisensi seragam.</div></footer></body></html>
"""
    return markup.encode("utf-8")


def target_unit_count(reader: dict[PurePosixPath, bytes]) -> int:
    total = 0
    for filename in ("index.html", "Lesson00.html", "Lesson01.html", "Lesson02.html", "Lesson03.html"):
        soup = BeautifulSoup(reader[PurePosixPath(filename)], "html.parser")
        total += len(soup.select("[data-o006-id]"))
    return total


def replay_lesson02_reader() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    """Replay the 4-of-14 reader after the cumulative glossary grew for Lesson03.

    The Lesson02 builder froze the then-current glossary even though that file
    does not participate in its rendering.  The glossary has since grown by
    additive Lesson03 terms.  Admit only this exact, already-frozen new glossary
    identity for replay; retain and protect the original 4-of-14 receipt rather
    than pretending its input evidence changed.
    """
    key = "00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv"
    historical = (3160, "6911989a604c656575245e84cf22765591ee7ba9da6b2f1a7d738fde85956c54")
    current = FROZEN_INPUTS[key]
    if prior.FROZEN_INPUTS.get(key) != historical:
        raise RuntimeError("Lesson02 builder's historical glossary contract differs")
    saved = prior.FROZEN_INPUTS
    admitted = dict(saved)
    admitted[key] = current
    prior.FROZEN_INPUTS = admitted
    try:
        return prior.compute()
    finally:
        prior.FROZEN_INPUTS = saved


def compute() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    frozen_evidence = read_frozen_inputs()
    prior_outputs, prior_receipt, prior_reader_files = replay_lesson02_reader()
    if len(prior_reader_files) != 31 or int(prior_receipt["coverage"]["complete_count"]) != 4:
        raise RuntimeError("admitted Lesson02 boundary differs")
    for name in HISTORICAL_REPLAY_OUTPUTS:
        payload = prior_outputs.get(name)
        if payload is None or payload != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson02 evidence does not replay: {name}")

    reader: dict[PurePosixPath, bytes] = {
        PurePosixPath(name.removeprefix("build/html-id/")): payload
        for name, payload in prior_outputs.items()
        if name.startswith("build/html-id/")
    }
    if set(reader) != prior_reader_files:
        raise RuntimeError("replayed Lesson02 reader inventory differs")
    prior_css_path = PurePosixPath(f"assets/{PRIOR_CSS_NAME}")
    css_path = PurePosixPath(f"assets/{CURRENT_CSS_NAME}")
    css_payload = reader.pop(prior_css_path, None)
    if css_payload is None or len(css_payload) != 6213 or first.sha256(css_payload) != "37fc52f724e0ea76443dc12ef243bf874ab6fb8c3c0640e03ab8cf1a6939f989":
        raise RuntimeError("admitted responsive reader CSS differs")
    reader[css_path] = css_payload

    target_outputs: dict[str, bytes] = {}
    prior_document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson02_documents.jsonl"],
        "Lesson02 document backend",
    )
    if len(prior_document_rows) != 4:
        raise RuntimeError("Lesson02 document backend row count differs")
    prior_by_filename = {
        PurePosixPath(str(row["target_path"])).name: row for row in prior_document_rows
    }
    prior_filenames = ("index.html", "Lesson00.html", "Lesson01.html", "Lesson02.html")
    if set(prior_by_filename) != set(prior_filenames):
        raise RuntimeError("Lesson02 document backend identity differs")
    for filename in prior_filenames:
        patched = patch_previous_document(reader[PurePosixPath(filename)], filename)
        reader[PurePosixPath(filename)] = patched
        target_outputs[f"source/id-ID/{filename}"] = patched
        prior_by_filename[filename]["target_bytes"] = len(patched)
        prior_by_filename[filename]["target_sha256"] = first.sha256(patched)

    lesson_soup, lesson_main, lesson_rows, lesson_source_math, lesson_unit_ids, lesson_math_ids = load_lesson03()
    del lesson_soup
    lesson_correction_rows = apply_lesson03_corrections(lesson_main)
    shared.normalize_lesson(lesson_main, "Lesson03.html")
    if shared.stable_values(lesson_main, "data-o006-id") != lesson_unit_ids:
        raise RuntimeError("Lesson03 structural identity/topology differs")
    if shared.stable_values(lesson_main, "data-o006-math-id") != lesson_math_ids:
        raise RuntimeError("Lesson03 math identities differ")
    if shared.native_id_duplicates(lesson_main):
        raise RuntimeError("Lesson03 target retains duplicate native IDs")
    if lesson_main.select("img, audio, video, source, iframe, embed, object, script"):
        raise RuntimeError("Lesson03 target unexpectedly contains an asset/runtime node")
    lesson_target_math = [node.get_text() for node in lesson_main.select(".math")]
    if len(lesson_target_math) != EXPECTED_MATH:
        raise RuntimeError("Lesson03 target math-node count differs")
    lesson_payload = page_document(lesson_main, "Lesson03", SOURCE_URL)
    reader[PurePosixPath("Lesson03.html")] = lesson_payload
    target_outputs["source/id-ID/Lesson03.html"] = lesson_payload

    document_rows = [prior_by_filename[name] for name in prior_filenames]
    document_rows.append(shared.document_row(
        "Lesson03", "Lesson03.html", DOCUMENT_ID, SOURCE_URL,
        lesson_source_math, lesson_target_math, lesson_payload,
        len(lesson_rows), len(lesson_unit_ids),
    ))
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative translation segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative normalized structural-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math-node count differs")

    prior_correction_rows = parse_jsonl(
        prior_outputs["backend/through_lesson02_corrections.jsonl"],
        "Lesson02 correction backend",
    )
    correction_rows = sorted(
        prior_correction_rows + lesson_correction_rows,
        key=lambda row: str(row["correction_id"]),
    )
    expected_correction_ids = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 47)}
    if len(correction_rows) != 46 or {str(row["correction_id"]) for row in correction_rows} != expected_correction_ids:
        raise RuntimeError("cumulative correction registry differs")

    reader[PurePosixPath("licenses/index.html")] = license_page()
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError("cumulative reader is not exactly 32 files")
    if target_unit_count(reader) != EXPECTED_TARGET_UNITS:
        raise RuntimeError("cumulative target structural-unit count differs")
    shared.validate_reader_links(reader)

    manifest_payload = first.manifest_payload(reader)
    corrections_payload = first.canonical_jsonl(correction_rows)
    documents_payload = first.canonical_jsonl(document_rows)
    reader_files = set(reader)

    outputs: dict[str, bytes] = dict(target_outputs)
    for path, payload in reader.items():
        outputs[f"build/html-id/{path.as_posix()}"] = payload
    outputs[relative(DOCUMENTS_BACKEND)] = documents_payload
    outputs[relative(CORRECTIONS_BACKEND)] = corrections_payload
    outputs[relative(MANIFEST)] = manifest_payload

    translation_bytes = TRANSLATIONS.read_bytes()
    builder_bytes = Path(__file__).read_bytes()
    receipt: dict[str, object] = {
        "schema": "o006.stat415.through-lesson03-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", "Lesson00", "Lesson01", "Lesson02", "Lesson03"],
            "complete_count": 5,
            "corpus_document_count": 14,
            "next_document": "Lesson04",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "structural_units_target": EXPECTED_TARGET_UNITS,
        "math_nodes": {
            "index": 0,
            "Lesson00": 331,
            "Lesson01": 169,
            "Lesson02": 209,
            "Lesson03": 440,
            "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson02_count": 29,
            "lesson03_count": len(lesson_correction_rows),
            "path": relative(CORRECTIONS_BACKEND),
            "bytes": len(corrections_payload),
            "sha256": first.sha256(corrections_payload),
        },
        "documents_backend": {
            "path": relative(DOCUMENTS_BACKEND),
            "bytes": len(documents_payload),
            "sha256": first.sha256(documents_payload),
        },
        "reader": {
            "path": relative(BUILD),
            "files": len(reader),
            "bytes": sum(len(payload) for payload in reader.values()),
            "manifest_path": relative(MANIFEST),
            "manifest_bytes": len(manifest_payload),
            "manifest_sha256": first.sha256(manifest_payload),
        },
        "rights": {
            "Penn State content": "CC BY-NC 4.0 except where otherwise noted",
            "Lesson01 figures": "CC BY-NC 4.0 under the official page notice; per-file creator metadata absent",
            "Lesson02 figures": "CC BY-NC 4.0 under the official page notice; per-file creator metadata absent",
            "Lesson03 assets": "verified zero main-content assets",
            "MathJax 3.1.2": "Apache-2.0",
            "aggregate_uniform_relicense": False,
        },
        "offline": {
            "external_runtime_requests": 0,
            "analytics": False,
            "cookies": False,
            "local_mathjax": True,
        },
        "layout": {
            "reader_css_bytes": len(css_payload),
            "reader_css_sha256": first.sha256(css_payload),
            "reader_css_path": css_path.as_posix(),
            "rule": "responsive instructional-media reflow rules preserved from the admitted 4-of-14 reader",
        },
        "historical_lesson02_evidence": {
            name: frozen_evidence[name] for name in sorted(HISTORICAL_PROTECTED_OUTPUTS)
        },
        "inputs": {
            "frozen": frozen_evidence,
            "lesson03_translation": {
                "path": relative(TRANSLATIONS),
                "bytes": len(translation_bytes),
                "sha256": first.sha256(translation_bytes),
                "rows": len(lesson_rows),
                "punctuation_boundary_exceptions": PUNCTUATION_BOUNDARY_EXCEPTIONS,
                "word_boundary_leading_space_exceptions": sorted(WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS),
            },
            "builder": {
                "path": relative(Path(__file__)),
                "bytes": len(builder_bytes),
                "sha256": first.sha256(builder_bytes),
            },
        },
        "target_documents": [
            {
                "path": str(row["target_path"]),
                "bytes": int(row["target_bytes"]),
                "sha256": str(row["target_sha256"]),
            }
            for row in document_rows
        ],
    }
    outputs[relative(RECEIPT)] = first.canonical_json(receipt)
    if HISTORICAL_PROTECTED_OUTPUTS.intersection(outputs):
        raise RuntimeError("Lesson03 output set would overwrite historical Lesson02 evidence")
    return outputs, receipt, reader_files


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    outputs, receipt, expected_reader_files = compute()
    existing_extra = shared.current_reader_files() - expected_reader_files
    replaced_css = PurePosixPath(f"assets/{PRIOR_CSS_NAME}")
    allowed_extra = {replaced_css}
    if existing_extra and existing_extra != allowed_extra:
        raise RuntimeError(
            "refusing to delete unexpected reader files: "
            + ", ".join(sorted(path.as_posix() for path in existing_extra))
        )
    if existing_extra:
        old_css = BUILD / replaced_css
        old_payload = old_css.read_bytes()
        if len(old_payload) != 6213 or first.sha256(old_payload) != "37fc52f724e0ea76443dc12ef243bf874ab6fb8c3c0640e03ab8cf1a6939f989":
            raise RuntimeError("refusing to replace an unrecognized 4-of-14 reader CSS")
    if args.write:
        receipt_name = relative(RECEIPT)
        for name in sorted(outputs, key=lambda value: (value == receipt_name, value.casefold())):
            first.atomic_write(ROOT / name, outputs[name])
        if existing_extra:
            new_css = BUILD / PurePosixPath(f"assets/{CURRENT_CSS_NAME}")
            if not new_css.is_file() or new_css.read_bytes() != outputs[f"build/html-id/assets/{CURRENT_CSS_NAME}"]:
                raise RuntimeError("versioned reader CSS was not written exactly")
            (BUILD / replaced_css).unlink()
        state = "written"
    else:
        state = "verified"
    shared.verify_outputs(outputs, expected_reader_files)
    receipt_payload = outputs[relative(RECEIPT)]
    print(json.dumps({
        "mode": state,
        "documents": int(receipt["coverage"]["complete_count"]),
        "segments": int(receipt["translation_segments"]),
        "target_units": int(receipt["structural_units_target"]),
        "math_nodes": int(receipt["math_nodes"]["total"]),
        "corrections": int(receipt["corrections"]["count"]),
        "reader_files": int(receipt["reader"]["files"]),
        "reader_bytes": int(receipt["reader"]["bytes"]),
        "receipt_sha256": first.sha256(receipt_payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
