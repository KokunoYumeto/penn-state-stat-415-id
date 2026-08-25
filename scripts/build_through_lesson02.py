#!/usr/bin/env python3
"""Build the cumulative id-ID reader through Penn State STAT 415 Lesson 02."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first
import build_through_lesson01 as prior


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
TARGET = ROOT / "source" / "id-ID"
TRANSLATIONS = TARGET / "lesson02_translation.csv"
ASSET_AUDIT = ROOT / "working" / "lesson02_asset_rights_audit.json"
ASSET_ROOT = ROOT / "authority" / "assets" / "stat415" / "lesson02"

DOCUMENTS_BACKEND = ROOT / "backend" / "through_lesson02_documents.jsonl"
CORRECTIONS_BACKEND = ROOT / "backend" / "through_lesson02_corrections.jsonl"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON02_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON02_BUILD_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson02"
DOCUMENT_ID = "O006-PSU-003"
EXPECTED_SEGMENTS = 324
EXPECTED_UNITS = 228
EXPECTED_MATH = 209
EXPECTED_TOTAL_SEGMENTS = 1068
EXPECTED_TOTAL_UNITS = 978
EXPECTED_TOTAL_MATH = 709
EXPECTED_READER_FILES = 31
CURRENT_CSS_NAME = "reader-4of14.css"

LESSON02_REFLOW_CSS = b"""

/* Cumulative reader reflow admitted with Lesson 02. */
main img:not(.card-img),
main svg,
main video,
main canvas {
  display: block;
  max-width: 100%;
  height: auto;
  margin-inline: auto;
}

main figure,
main .quarto-figure,
main .quarto-float,
main .quarto-figure > *,
main .quarto-float > * {
  max-width: 100%;
}
"""

HISTORICAL_PROTECTED_OUTPUTS = {
    "build/THROUGH_LESSON01_MANIFEST.csv",
    "build/THROUGH_LESSON01_BUILD_RECEIPT.json",
    "backend/through_lesson01_documents.jsonl",
    "backend/through_lesson01_corrections.jsonl",
}

FROZEN_INPUTS: dict[str, tuple[int, str]] = {
    "scripts/build_through_lesson01.py": (43347, "0596b9e167f2b174f13848a96f7c425c4bb31b91312b8a01d5c1e444ad38742f"),
    "build/THROUGH_LESSON01_BUILD_RECEIPT.json": (7122, "ae926ca4f9a3d0d1723b059fbc578365bfd5fc704521a7a990b98bdd4bc4a1c2"),
    "build/THROUGH_LESSON01_MANIFEST.csv": (2798, "6a047b981eeb71e740450678b4f802fb7ec3eb954cf92ffc3cebbaf8a050b5a7"),
    "backend/through_lesson01_documents.jsonl": (2005, "d8983d875f55fad9df56b1dfe6962456fa357b359c14d42c253318f8775a5bc1"),
    "backend/through_lesson01_corrections.jsonl": (6506, "f66a3106401d473d2aa8208e5e04823f1b6d4e830c86d5fed61285e96fd5c7c4"),
    "source/normalized/en-US/Lesson02.html": (55530, "efb5376be5d16d085bbc8d668b31839e0270c7a37e3a2abd52cd742a1410e646"),
    "source/id-ID/lesson02_translation.csv": (76070, "26159d7d4beae3f16b83df0f51a7deb3afb5cd23fb5b1be1dd0056c527c3764a"),
    "backend/lesson02_translation_bindings.jsonl": (132573, "3c75bfc1cc9dc38213cf03d43c2b6b3e1ec106536a4e4ac1b04e836ef568c25f"),
    "build/LESSON02_TRANSLATION_RECEIPT.json": (2213, "bb4c79ea2511448ddd9d877d70c0f9fb6a64f597be3585f73990896b1feddd5b"),
    "working/lesson02_asset_rights_audit.json": (9531, "f142b7257b8b36417d2d1bb145c2bec13d02274d1ee61698a1a21993e4bc86b0"),
    "authority/LESSON02_ASSET_MANIFEST.csv": (681, "ef3739fabe02a1e77258d559e6a20be48f727e9e55b05a93851b6a037b715407"),
    "authority/LESSON02_ASSET_FREEZE_RECEIPT.json": (2064, "ebd00288c159889b7a255ad571735a5428ab9d431e4bc73b48c077bd6c4aaf05"),
    "working/lesson02_source_findings.md": (4684, "b3ab5a3aa17a2c47aff1b4177ff64f5c7222c34b08d47a2bbee5fd69ef8897c9"),
    "working/lesson02_terminology_qa.md": (2330, "204743e2737e38a508c2205fa0075f1240e7572f2425f9935f5175555a7845ee"),
    "00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv": (3160, "6911989a604c656575245e84cf22765591ee7ba9da6b2f1a7d738fde85956c54"),
    "authority/assets/stat415/lesson02/dartboard.png": (32701, "c8ddb1d7befe425ac72efd04abd75c0835aae62c786765256f3f8d93ee3ec0cd"),
    "authority/assets/stat415/lesson02/unnamed-chunk-1-1.png": (10942, "564048b4327b3a379fe9921efa9224760f6c6afd01135f17d941af393a8f4532"),
}

ASSETS: dict[str, tuple[str, str, int, str]] = {
    "dartboard.png": (
        "O006-PSU-003-A0001",
        "assets/dartboard.png",
        32701,
        "c8ddb1d7befe425ac72efd04abd75c0835aae62c786765256f3f8d93ee3ec0cd",
    ),
    "unnamed-chunk-1-1.png": (
        "O006-PSU-003-A0002",
        "Lesson02_files/figure-html/unnamed-chunk-1-1.png",
        10942,
        "564048b4327b3a379fe9921efa9224760f6c6afd01135f17d941af393a8f4532",
    ),
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


def load_lesson02() -> tuple[
    BeautifulSoup,
    Tag,
    list[dict[str, str]],
    dict[str, NavigableString],
    list[str],
    list[str],
    list[str],
]:
    if not TRANSLATIONS.is_file():
        raise RuntimeError("Lesson02 translation CSV is not yet present")
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        expected_fields = [
            "segment_id", "document_id", "component_id", "section_id",
            "source_sha256", "source_text", "target_text", "status",
        ]
        if reader.fieldnames != expected_fields:
            raise RuntimeError("Lesson02 translation CSV schema differs")
        rows = list(reader)
    if len(rows) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson02 translation boundary is not 324 segments")

    soup = BeautifulSoup((NORMALIZED / "Lesson02.html").read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("normalized Lesson02 main is missing")
    source_math = [node.get_text() for node in main.select(".math")]
    if len(source_math) != EXPECTED_MATH:
        raise RuntimeError("normalized Lesson02 math-node count differs")
    unit_ids = prior.stable_values(main, "data-o006-id")
    math_ids = prior.stable_values(main, "data-o006-math-id")
    if unit_ids != [f"O006-PSU-003-U{i:04d}" for i in range(1, EXPECTED_UNITS + 1)]:
        raise RuntimeError("Lesson02 structural-unit identity sequence differs")
    if math_ids != [f"O006-PSU-003-M{i:04d}" for i in range(1, EXPECTED_MATH + 1)]:
        raise RuntimeError("Lesson02 math identity sequence differs")
    if prior.native_id_duplicates(main):
        raise RuntimeError("Lesson02 normalized source has unexpected duplicate native IDs")

    nodes = prior.translatable_nodes(main)
    if len(nodes) != EXPECTED_SEGMENTS:
        raise RuntimeError("Lesson02 translatable-node count differs")
    target_nodes: dict[str, NavigableString] = {}
    for ordinal, (row, node) in enumerate(zip(rows, nodes), start=1):
        sid = f"O006-PSU-003-S{ordinal:04d}"
        if row["segment_id"] != sid:
            raise RuntimeError(f"Lesson02 segment order differs: {sid}")
        if row["document_id"] != DOCUMENT_ID or row["component_id"] != "Lesson02":
            raise RuntimeError(f"Lesson02 segment identity differs: {sid}")
        source_text = str(node)
        if row["source_text"] != source_text:
            raise RuntimeError(f"Lesson02 source text differs: {sid}")
        if row["source_sha256"] != first.sha256(source_text.encode("utf-8")):
            raise RuntimeError(f"Lesson02 source hash differs: {sid}")
        target_text = row["target_text"]
        if row["status"] != "translated" or not target_text.strip():
            raise RuntimeError(f"Lesson02 translation unfinished: {sid}")
        if "\ufffd" in target_text:
            raise RuntimeError(f"Lesson02 target contains replacement character: {sid}")
        if prior.boundary_whitespace(source_text) != prior.boundary_whitespace(target_text):
            raise RuntimeError(f"Lesson02 boundary whitespace differs: {sid}")
        replacement = NavigableString(target_text)
        node.replace_with(replacement)
        target_nodes[sid] = replacement
    return soup, main, rows, target_nodes, source_math, unit_ids, math_ids


def set_math_surface(
    main: Tag,
    math_id: str,
    expected: str,
    target: str,
) -> dict[str, str]:
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"math correction identity differs: {math_id}")
    node = nodes[0]
    before = node.get_text()
    if before != expected:
        raise RuntimeError(f"math correction source differs: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "math_id": math_id,
        "source_surface_sha256": first.sha256(before.encode("utf-8")),
        "target_surface_sha256": first.sha256(target.encode("utf-8")),
    }


def apply_lesson02_corrections(main: Tag) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    node = main.select_one('[data-o006-math-id="O006-PSU-003-M0062"]')
    if node is None:
        raise RuntimeError("L02-D001 surface missing")
    before = node.get_text()
    if before.count(r"\frac{X_1}{n}") != 1:
        raise RuntimeError("L02-D001 source differs")
    target = before.replace(r"\frac{X_1}{n}", r"\frac{X_1}{10}", 1)
    surface = set_math_surface(main, "O006-PSU-003-M0062", before, target)
    records.append({
        "correction_id": "O006-PSU-ADV-0021",
        "source_defect_id": "L02-D001",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    node = main.select_one('[data-o006-math-id="O006-PSU-003-M0073"]')
    if node is None:
        raise RuntimeError("L02-D002 surface missing")
    before = node.get_text()
    if before.count("&amp;") != 3:
        raise RuntimeError("L02-D002 escaped-alignment count differs")
    target = before.replace("&amp;", "&")
    surface = set_math_surface(main, "O006-PSU-003-M0073", before, target)
    records.append({
        "correction_id": "O006-PSU-ADV-0022",
        "source_defect_id": "L02-D002",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 3,
        **surface,
    })

    surface = set_math_surface(
        main,
        "O006-PSU-003-M0075",
        r"\(E(X) = p\)",
        r"\(E(X) = np\)",
    )
    records.append({
        "correction_id": "O006-PSU-ADV-0023",
        "source_defect_id": "L02-D003",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    old_bias = r"\[\begin{align}\text{Bias}_1 &= E(\hat{p}_1) - p\\ &= E\left[\frac{X_1}{10}\right] - p\\ &= \frac{E(X_1)}{10} - p\\ &= \frac{10p}{10} - p\\ &= p - p = 0 \end{align}\]"
    new_bias = r"""\[\begin{align}
\text{Bias}_1 &= E(\hat{p}_1)-p = E\left[\frac{X_1}{10}\right]-p = 0\\
\text{Bias}_2 &= E(\hat{p}_2)-p = E\left[\frac{X_1+X_2+X_3}{30}\right]-p = 0\\
\text{Bias}_3 &= E(\hat{p}_3)-p = E(\hat{p}_2+0.1)-p = 0.1
\end{align}\]"""
    surface = set_math_surface(main, "O006-PSU-003-M0078", old_bias, new_bias)
    records.append({
        "correction_id": "O006-PSU-ADV-0024",
        "source_defect_id": "L02-D004",
        "status": "applied-target-only",
        "surface": "math-extension",
        "replacement_count": 1,
        "note": "completed the two omitted bias results in the existing worked-solution math surface",
        **surface,
    })

    old_variance = r"""\[\begin{align*}
\hat{\sigma}^2 &= \frac{1}{n}\sum_{i=1}^n (x_i - \bar{x})^2 = \frac{1}{n}\left(x_i^2 - 2x_i\bar{x} + \bar{x}^2\right)^2 \\&= \frac{1}{n}\sum_{i=1}^n x_i^2 - 2\bar{x}\sum_{i=1}^n x_i + \frac{1}{n}(n\bar{x}^2)\\ &= \frac{1}{n}\sum_{i=1}^n x_i^2 - \bar{x}^2
\end{align*}\]"""
    new_variance = r"""\[\begin{align*}
\hat{\sigma}^2
&= \frac{1}{n}\sum_{i=1}^n (x_i-\bar{x})^2\\
&= \frac{1}{n}\sum_{i=1}^n\left(x_i^2-2x_i\bar{x}+\bar{x}^2\right)\\
&= \frac{1}{n}\sum_{i=1}^n x_i^2-\frac{2\bar{x}}{n}\sum_{i=1}^n x_i+\bar{x}^2\\
&= \frac{1}{n}\sum_{i=1}^n x_i^2-\bar{x}^2
\end{align*}\]"""
    surface = set_math_surface(main, "O006-PSU-003-M0102", old_variance, new_variance)
    records.append({
        "correction_id": "O006-PSU-ADV-0025",
        "source_defect_id": "L02-D005",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    old_antiderivative = r"""\[
\begin{align*}
E(\ln Y_i) = \lim_{a \rightarrow 0} \left[ y^{1/\theta} \ln y - \theta y^{1-\theta} \right]_a^1 = -\theta
\end{align*}
\]"""
    new_antiderivative = old_antiderivative.replace(r"y^{1-\theta}", r"y^{1/\theta}")
    surface = set_math_surface(main, "O006-PSU-003-M0152", old_antiderivative, new_antiderivative)
    records.append({
        "correction_id": "O006-PSU-ADV-0026",
        "source_defect_id": "L02-D006",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    surface = set_math_surface(main, "O006-PSU-003-M0160", r"\(\theta\)", r"\(p\)")
    records.append({
        "correction_id": "O006-PSU-ADV-0027",
        "source_defect_id": "L02-D007",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    surface = set_math_surface(
        main,
        "O006-PSU-003-M0177",
        r"\(\text{Var}(\hat{p}_1)>\text{Var}(\hat{p}_2.\)",
        r"\(\text{Var}(\hat{p}_1)>\text{Var}(\hat{p}_2).\)",
    )
    records.append({
        "correction_id": "O006-PSU-ADV-0028",
        "source_defect_id": "L02-D008",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    old_identity = r"""\[\begin{align*}
        \text{MSE}(\hat{\theta})=\text{Var}(\hat{\theta})-\left[\text{Bias}(\theta)\right]^2
    \end{align*}\]"""
    new_identity = r"""\[\begin{align*}
        \text{MSE}(\hat{\theta})=\text{Var}(\hat{\theta})+\left[\text{Bias}(\hat{\theta})\right]^2
    \end{align*}\]"""
    identity_surface = set_math_surface(main, "O006-PSU-003-M0200", old_identity, new_identity)
    old_example = r"""\[\begin{align*}
    & MSE(\hat{p}_1)=\text{Var}(\hat{p}_1)-\left[\text{Bias}(\hat{p}_1\right]^2=\frac{p(1-p)}{10}\\
    & MSE(\hat{p}_2)=\text{Var}(\hat{p}_2)-\left[\text{Bias}(\hat{p}_2\right]^2=\frac{p(1-p)}{30}\\
    & MSE(\hat{p}_3)=\text{Var}(\hat{p}_3)-\left[\text{Bias}(\hat{p}_3\right]^2=\frac{p(1-p)}{30}-0.1^2=\frac{p(1-p)}{30}-0.01\\
\end{align*}\]"""
    new_example = r"""\[\begin{align*}
    & MSE(\hat{p}_1)=\text{Var}(\hat{p}_1)+\left[\text{Bias}(\hat{p}_1)\right]^2=\frac{p(1-p)}{10}\\
    & MSE(\hat{p}_2)=\text{Var}(\hat{p}_2)+\left[\text{Bias}(\hat{p}_2)\right]^2=\frac{p(1-p)}{30}\\
    & MSE(\hat{p}_3)=\text{Var}(\hat{p}_3)+\left[\text{Bias}(\hat{p}_3)\right]^2=\frac{p(1-p)}{30}+0.1^2=\frac{p(1-p)}{30}+0.01\\
\end{align*}\]"""
    example_surface = set_math_surface(main, "O006-PSU-003-M0208", old_example, new_example)
    records.append({
        "correction_id": "O006-PSU-ADV-0029",
        "source_defect_id": "L02-D009",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 10,
        "surfaces": [identity_surface, example_surface],
    })

    expected_ids = {f"O006-PSU-ADV-{i:04d}" for i in range(21, 30)}
    if len(records) != 9 or {str(row["correction_id"]) for row in records} != expected_ids:
        raise RuntimeError("Lesson02 correction registry differs")
    if any(row["status"] != "applied-target-only" for row in records):
        raise RuntimeError("Lesson02 correction status differs")
    return records


def normalize_lesson02_assets(main: Tag) -> None:
    images = main.select("img[src]")
    source_refs = [str(node.get("src")) for node in images]
    expected_refs = ["assets/dartboard.png", "Lesson02_files/figure-html/unnamed-chunk-1-1.png"]
    if source_refs != expected_refs:
        raise RuntimeError("Lesson02 image sequence differs")
    alt_texts = [
        (
            "Empat papan sasaran berlabel A–D: A tidak akurat dan tidak presisi; "
            "B tidak akurat tetapi lebih presisi; C lebih akurat tetapi kurang "
            "presisi; D akurat dan presisi."
        ),
        (
            "Dua kurva kepadatan penduga di sekitar nilai parameter sebenarnya: "
            "penduga pertama berpusat tetapi lebih menyebar; penduga kedua lebih "
            "sempit tetapi bergeser ke kiri."
        ),
    ]
    targets = ["assets/dartboard.png", "assets/unnamed-chunk-1-1.png"]
    for image, target, alt_text in zip(images, targets, alt_texts):
        image["src"] = target
        image["alt"] = alt_text
        image.attrs.pop("style", None)
    inherited_alt = main.select('[alt="4 different dartboards showing different types of bias"]')
    if len(inherited_alt) != 1 or inherited_alt[0].name != "div":
        raise RuntimeError("Lesson02 inherited dartboard alt surface differs")
    inherited_alt[0]["alt"] = alt_texts[0]
    lightboxes = main.select("a.lightbox[href]")
    if len(lightboxes) != 1 or lightboxes[0].get("href") != "assets/dartboard.png":
        raise RuntimeError("Lesson02 lightbox surface differs")
    anchor = lightboxes[0]
    classes = [value for value in (anchor.get("class") or []) if value != "lightbox"]
    if classes:
        anchor["class"] = classes
    else:
        anchor.attrs.pop("class", None)
    anchor.attrs.pop("data-gallery", None)
    anchor.attrs.pop("title", None)


def patch_previous_document(payload: bytes, filename: str) -> bytes:
    text = payload.decode("utf-8")
    replacements = (
        (
            '<meta name="edition-status" content="partial: 3 of 14 documents complete; landing and Lessons 00–01">',
            '<meta name="edition-status" content="partial: 4 of 14 documents complete; landing and Lessons 00–02">',
        ),
        (
            '<a href="Lesson01.html">Pelajaran 01</a><a href="licenses/index.html">Lisensi</a>',
            '<a href="Lesson01.html">Pelajaran 01</a><a href="Lesson02.html">Pelajaran 02</a><a href="licenses/index.html">Lisensi</a>',
        ),
        (
            '<strong>Edisi Bahasa Indonesia — 3 dari 14 dokumen.</strong>',
            '<strong>Edisi Bahasa Indonesia — 4 dari 14 dokumen.</strong>',
        ),
        (
            'Laman utama serta Pelajaran 00 dan 01 telah diterjemahkan sepenuhnya.',
            'Laman utama serta Pelajaran 00–02 telah diterjemahkan sepenuhnya.',
        ),
        (
            'Pelajaran 02–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.',
            'Pelajaran 03–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai.',
        ),
    )
    for old, new in replacements:
        if text.count(old) != 1:
            raise RuntimeError(f"previous-page status surface differs: {filename}: {old}")
        text = text.replace(old, new, 1)
    old_css = '<link rel="stylesheet" href="assets/reader.css">'
    new_css = f'<link rel="stylesheet" href="assets/{CURRENT_CSS_NAME}">'
    if text.count(old_css) != 1:
        raise RuntimeError(f"previous-page CSS surface differs: {filename}")
    text = text.replace(old_css, new_css, 1)
    if filename == "index.html":
        old_anchor = (
            '<a class="pending-source quarto-grid-link" data-o006-id="O006-PSU-000-U0044" '
            'data-translation-status="pending" href="https://online.stat.psu.edu/stat415/Lesson02" '
            'title="Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris">'
        )
        new_anchor = (
            '<a class="quarto-grid-link" data-o006-id="O006-PSU-000-U0044" '
            'data-translation-status="complete" href="Lesson02.html">'
        )
        if text.count(old_anchor) != 1:
            raise RuntimeError("index Lesson02 card surface differs")
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
        '<strong>Edisi Bahasa Indonesia — 4 dari 14 dokumen.</strong> '
        'Laman utama serta Pelajaran 00–02 telah diterjemahkan sepenuhnya. '
        'Pelajaran 03–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai. '
        f'<a href="{source}">Sumber resmi halaman ini</a>. '
        '<a href="licenses/index.html">Atribusi, perubahan, dan lisensi</a>.'
        '</aside>'
    )
    script = '<script defer src="assets/MathJax/tex-svg.js"></script>\n'
    markup = (
        "<!doctype html>\n"
        '<html lang="id-ID">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{source}">\n'
        f'<meta name="translation-provenance" content="{PROVENANCE}">\n'
        '<meta name="edition-status" content="partial: 4 of 14 documents complete; landing and Lessons 00–02">\n'
        '<link rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">\n'
        f'<link rel="stylesheet" href="assets/{CURRENT_CSS_NAME}">\n'
        f"{script}</head>\n<body>\n"
        '<a class="skip-link" href="#quarto-document-content">Lewati ke isi utama</a>\n'
        '<header class="site-header"><div class="site-header__inner">'
        '<div><p class="site-title">STAT 415 — Pengantar Statistika Matematis</p>'
        '<p class="site-subtitle">Rekonstruksi dan terjemahan Bahasa Indonesia · O006/C140</p></div>'
        '<nav class="site-nav" aria-label="Navigasi utama">'
        '<a href="index.html">Daftar pelajaran</a><a href="Lesson00.html">Pelajaran 00</a>'
        '<a href="Lesson01.html">Pelajaran 01</a><a href="Lesson02.html">Pelajaran 02</a>'
        '<a href="licenses/index.html">Lisensi</a>'
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
<p class="site-subtitle">STAT 415 — edisi Bahasa Indonesia</p></div><nav class="site-nav" aria-label="Navigasi utama"><a href="../index.html">Daftar pelajaran</a><a href="../Lesson00.html">Pelajaran 00</a><a href="../Lesson01.html">Pelajaran 01</a><a href="../Lesson02.html">Pelajaran 02</a></nav></div></header>
<div class="page-shell"><main id="licence-main"><h1>Atribusi, perubahan, dan lisensi</h1>
<h2>Konten Penn State</h2><p>Catatan mata kuliah resmi dirancang dan dikembangkan oleh <a href="https://science.psu.edu/stat">Departemen Statistika Penn State</a>. Menurut halaman sumber, kontennya tersedia di bawah <a rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)</a>, kecuali dinyatakan lain.</p>
<p>Edisi ini merupakan terjemahan dan rekonstruksi tidak resmi. Perubahan meliputi penerjemahan ke id-ID, sumber HTML semantik yang dinormalisasi, identitas mesin tambahan, gaya pembaca lokal, kontrol HTML aksesibel, teks alternatif gambar, serta empat belas koreksi Lesson 00, enam koreksi Lesson 01, dan sembilan koreksi Lesson 02 yang dicatat secara terpisah. Byte sumber resmi tidak diubah. Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat.</p>
<p>Lima gambar pengajaran Lesson 01 dan dua gambar Lesson 02 dipertahankan dari URL resmi halaman masing-masing di bawah pemberitahuan CC BY-NC 4.0 yang sama; setiap identitas, URL, byte, hash, dan keterbatasan bukti hak dicatat dalam audit aset. Sumber resmi: <a href="https://online.stat.psu.edu/stat415/">STAT 415</a>. Status edisi saat ini: laman utama serta Pelajaran 00–02 lengkap; Pelajaran 03–12 belum diterjemahkan.</p>
<h2>MathJax</h2><p>MathJax 3.1.2 digunakan secara lokal untuk merender matematika dan tersedia di bawah Apache License 2.0. <a href="MathJax-3.1.2-LICENSE.txt">Baca teks lisensi yang disertakan</a>.</p>
<h2>Provenans</h2><p>{PROVENANCE}. Seluruh kredit sumber dan kontributor manusia tetap dipertahankan.</p>
</main></div><footer class="site-footer"><div class="site-footer__inner">Koleksi C140 mempertahankan identitas dan lisensi setiap komponen; tidak ada relisensi seragam.</div></footer></body></html>
"""
    return markup.encode("utf-8")


def add_lesson02_assets(reader: dict[PurePosixPath, bytes]) -> None:
    audit = json.loads(ASSET_AUDIT.read_text("utf-8"))
    if audit.get("schema_version") != "o006.stat415.lesson_asset_rights_audit.v1":
        raise RuntimeError("Lesson02 asset-audit schema differs")
    if audit.get("blocking_unresolved_rights") != []:
        raise RuntimeError("Lesson02 has blocking unresolved asset rights")
    assets = audit.get("assets")
    if not isinstance(assets, list) or len(assets) != 2:
        raise RuntimeError("Lesson02 asset-audit count differs")
    seen: set[str] = set()
    for row in assets:
        local_path = str(row.get("local_path"))
        filename = PurePosixPath(local_path).name
        if filename not in ASSETS or filename in seen:
            raise RuntimeError(f"Lesson02 asset inventory differs: {filename}")
        seen.add(filename)
        expected_id, source_reference, expected_bytes, expected_sha256 = ASSETS[filename]
        if row.get("asset_id") != expected_id or row.get("disposition") != "freeze":
            raise RuntimeError(f"Lesson02 asset identity/disposition differs: {filename}")
        if row.get("source_reference", {}).get("relative_url") != source_reference:
            raise RuntimeError(f"Lesson02 asset source reference differs: {filename}")
        rights = row.get("rights")
        integrity = row.get("integrity")
        if not isinstance(rights, dict) or rights.get("applied_license") != "CC BY-NC 4.0":
            raise RuntimeError(f"Lesson02 asset licence differs: {filename}")
        if not isinstance(integrity, dict):
            raise RuntimeError(f"Lesson02 asset integrity evidence missing: {filename}")
        if integrity.get("bytes") != expected_bytes or integrity.get("sha256") != expected_sha256:
            raise RuntimeError(f"Lesson02 asset audit hash differs: {filename}")
        data = (ASSET_ROOT / filename).read_bytes()
        if len(data) != expected_bytes or first.sha256(data) != expected_sha256:
            raise RuntimeError(f"Lesson02 asset bytes differ: {filename}")
        destination = PurePosixPath(f"assets/{filename}")
        if destination in reader:
            raise RuntimeError(f"reader asset collision: {destination}")
        reader[destination] = data
    if seen != set(ASSETS):
        raise RuntimeError("Lesson02 asset set differs")


def compute() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    frozen_evidence = read_frozen_inputs()
    prior_outputs, prior_receipt, prior_reader_files = prior.compute()
    if len(prior_reader_files) != 28 or int(prior_receipt["coverage"]["complete_count"]) != 3:
        raise RuntimeError("admitted Lesson01 boundary differs")
    for name in HISTORICAL_PROTECTED_OUTPUTS:
        payload = prior_outputs.get(name)
        if payload is None or payload != (ROOT / name).read_bytes():
            raise RuntimeError(f"historical Lesson01 evidence does not replay: {name}")

    reader: dict[PurePosixPath, bytes] = {
        PurePosixPath(name.removeprefix("build/html-id/")): payload
        for name, payload in prior_outputs.items()
        if name.startswith("build/html-id/")
    }
    if set(reader) != prior_reader_files:
        raise RuntimeError("replayed Lesson01 reader inventory differs")
    base_css_path = PurePosixPath("assets/reader.css")
    css_path = PurePosixPath(f"assets/{CURRENT_CSS_NAME}")
    base_css = reader.pop(base_css_path, None)
    if base_css is None or len(base_css) != 5890 or first.sha256(base_css) != "1d463e04c51aff4750dec54523952488635c08fc5d3ead30ffc399a43f96f77b":
        raise RuntimeError("admitted base reader CSS differs")
    reader[css_path] = base_css + LESSON02_REFLOW_CSS

    target_outputs: dict[str, bytes] = {}
    prior_document_rows = parse_jsonl(
        prior_outputs["backend/through_lesson01_documents.jsonl"],
        "Lesson01 document backend",
    )
    if len(prior_document_rows) != 3:
        raise RuntimeError("Lesson01 document backend row count differs")
    prior_by_filename = {
        PurePosixPath(str(row["target_path"])).name: row for row in prior_document_rows
    }
    if set(prior_by_filename) != {"index.html", "Lesson00.html", "Lesson01.html"}:
        raise RuntimeError("Lesson01 document backend identity differs")
    for filename in ("index.html", "Lesson00.html", "Lesson01.html"):
        patched = patch_previous_document(reader[PurePosixPath(filename)], filename)
        reader[PurePosixPath(filename)] = patched
        target_outputs[f"source/id-ID/{filename}"] = patched
        prior_by_filename[filename]["target_bytes"] = len(patched)
        prior_by_filename[filename]["target_sha256"] = first.sha256(patched)

    (
        lesson_soup, lesson_main, lesson_rows, _lesson_target_nodes,
        lesson_source_math, lesson_unit_ids, lesson_math_ids,
    ) = load_lesson02()
    lesson_correction_rows = apply_lesson02_corrections(lesson_main)
    normalize_lesson02_assets(lesson_main)
    prior.normalize_lesson(lesson_main, "Lesson02.html")
    if prior.stable_values(lesson_main, "data-o006-id") != lesson_unit_ids:
        raise RuntimeError("Lesson02 structural identity/topology differs")
    if prior.stable_values(lesson_main, "data-o006-math-id") != lesson_math_ids:
        raise RuntimeError("Lesson02 math identities differ")
    if prior.native_id_duplicates(lesson_main):
        raise RuntimeError("Lesson02 target retains duplicate native IDs")
    lesson_target_math = [node.get_text() for node in lesson_main.select(".math")]
    if len(lesson_target_math) != EXPECTED_MATH:
        raise RuntimeError("Lesson02 target math-node count differs")
    lesson_payload = page_document(lesson_main, "Lesson02", SOURCE_URL)
    reader[PurePosixPath("Lesson02.html")] = lesson_payload
    target_outputs["source/id-ID/Lesson02.html"] = lesson_payload

    document_rows = [prior_by_filename[name] for name in ("index.html", "Lesson00.html", "Lesson01.html")]
    document_rows.append(prior.document_row(
        "Lesson02", "Lesson02.html", DOCUMENT_ID, SOURCE_URL,
        lesson_source_math, lesson_target_math, lesson_payload,
        len(lesson_rows), len(lesson_unit_ids),
    ))
    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative translation segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative structural-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math-node count differs")

    prior_correction_rows = parse_jsonl(
        prior_outputs["backend/through_lesson01_corrections.jsonl"],
        "Lesson01 correction backend",
    )
    correction_rows = sorted(
        prior_correction_rows + lesson_correction_rows,
        key=lambda row: str(row["correction_id"]),
    )
    expected_correction_ids = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 30)}
    if len(correction_rows) != 29 or {str(row["correction_id"]) for row in correction_rows} != expected_correction_ids:
        raise RuntimeError("cumulative correction registry differs")

    reader[PurePosixPath("licenses/index.html")] = license_page()
    add_lesson02_assets(reader)
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError("cumulative reader is not exactly 31 files")
    prior.validate_reader_links(reader)

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
        "schema": "o006.stat415.through-lesson02-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", "Lesson00", "Lesson01", "Lesson02"],
            "complete_count": 4,
            "corpus_document_count": 14,
            "next_document": "Lesson03",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "math_nodes": {
            "index": 0,
            "Lesson00": 331,
            "Lesson01": 169,
            "Lesson02": 209,
            "total": EXPECTED_TOTAL_MATH,
        },
        "corrections": {
            "count": len(correction_rows),
            "through_lesson01_count": 20,
            "lesson02_count": len(lesson_correction_rows),
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
            "base_css_bytes": len(base_css),
            "base_css_sha256": first.sha256(base_css),
            "reader_css_bytes": len(reader[css_path]),
            "reader_css_sha256": first.sha256(reader[css_path]),
            "reader_css_path": css_path.as_posix(),
            "rule": "large instructional media reflow within the full reader content column",
        },
        "historical_lesson01_evidence": {
            name: frozen_evidence[name] for name in sorted(HISTORICAL_PROTECTED_OUTPUTS)
        },
        "inputs": {
            "frozen": frozen_evidence,
            "lesson02_translation": {
                "path": relative(TRANSLATIONS),
                "bytes": len(translation_bytes),
                "sha256": first.sha256(translation_bytes),
                "rows": len(lesson_rows),
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
        raise RuntimeError("Lesson02 output set would overwrite historical Lesson01 evidence")
    return outputs, receipt, reader_files


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    outputs, receipt, expected_reader_files = compute()
    existing_extra = prior.current_reader_files() - expected_reader_files
    replaced_css = PurePosixPath("assets/reader.css")
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
            raise RuntimeError("refusing to replace an unrecognized reader.css")
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
    prior.verify_outputs(outputs, expected_reader_files)
    receipt_payload = outputs[relative(RECEIPT)]
    print(json.dumps({
        "mode": state,
        "documents": int(receipt["coverage"]["complete_count"]),
        "segments": int(receipt["translation_segments"]),
        "math_nodes": int(receipt["math_nodes"]["total"]),
        "corrections": int(receipt["corrections"]["count"]),
        "reader_files": int(receipt["reader"]["files"]),
        "reader_bytes": int(receipt["reader"]["bytes"]),
        "receipt_sha256": first.sha256(receipt_payload),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
