#!/usr/bin/env python3
"""Build the cumulative id-ID reader through Penn State STAT 415 Lesson 01.

This builder deliberately leaves every historical FIRST_UNIT evidence file
untouched.  It reuses stable, side-effect-free helpers from build_first_unit,
recomputes the cumulative reader, and emits a distinct evidence lineage.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import posixpath
import re
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup, NavigableString, Tag

import build_first_unit as first


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
TARGET = ROOT / "source" / "id-ID"
LESSON01_TRANSLATIONS = TARGET / "lesson01_translation.csv"
LESSON01_ASSET_AUDIT = ROOT / "working" / "lesson01_asset_rights_audit.json"
LESSON01_SOURCE_FINDINGS = ROOT / "working" / "lesson01_source_findings.md"

DOCUMENTS_BACKEND = ROOT / "backend" / "through_lesson01_documents.jsonl"
CORRECTIONS_BACKEND = ROOT / "backend" / "through_lesson01_corrections.jsonl"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "THROUGH_LESSON01_MANIFEST.csv"
RECEIPT = ROOT / "build" / "THROUGH_LESSON01_BUILD_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
LESSON01_SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson01"
LESSON01_DOCUMENT_ID = "O006-PSU-002"
EXPECTED_FIRST_SEGMENTS = 523
EXPECTED_LESSON01_SEGMENTS = 221
EXPECTED_TOTAL_SEGMENTS = 744
EXPECTED_LESSON01_MATH = 169
EXPECTED_TOTAL_MATH = 500
EXPECTED_FIRST_UNITS = 562
EXPECTED_LESSON01_UNITS = 188
EXPECTED_TOTAL_UNITS = 750
EXPECTED_READER_FILES = 28
FIRST_UNIT_REMOVED_STABLE_UNITS = {
    "O006-PSU-001-U0342",
    "O006-PSU-001-U0350",
}

HISTORICAL_PROTECTED_OUTPUTS = {
    "build/FIRST_UNIT_MANIFEST.csv",
    "build/FIRST_UNIT_BUILD_RECEIPT.json",
    "backend/first_unit_documents.jsonl",
    "backend/first_unit_corrections.jsonl",
}

# These inputs existed at the admitted first-unit/Lesson01 boundary.  A change
# requires a new adjudicated build contract, not a silent rebuild.
FROZEN_INPUTS: dict[str, tuple[int, str]] = {
    "scripts/build_first_unit.py": (27123, "ac004ef651fe77ab17e51b52ad45d3662687eba0674caf28e15a7667e0a8f624"),
    "source/normalized/en-US/index.html": (26025, "bf7231efa163c2056d1474edcb829c7cabd796fed194ed67accef04a973f0406"),
    "source/normalized/en-US/Lesson00.html": (65253, "411b3973f5f0b343f87450a6c66760b6a8e827a1966232f80f1634d446eebf9f"),
    "source/normalized/en-US/Lesson01.html": (44561, "80af5060d5b87190c82b553500024b0926af28aa4b2310091092c1873b47f02c"),
    "source/id-ID/first_unit_translation.csv": (108105, "e6bce1b1dd51c057ac36424b46bb47e2cc8a6c3f48894d548dfea79e74d448c4"),
    "source/id-ID/lesson01_translation.csv": (54021, "f7c6cc3c2089f1e3f0fb500dddd93b803cb2c63007b30349a41e88c9d52e9eeb"),
    "backend/first_unit_segments.jsonl": (207177, "4706f76a8c7cd1bc9d477676d132ebcc69c5fbc41973ab6f6c46977c20b6bbb5"),
    "backend/lesson01_translation_bindings.jsonl": (88776, "bc5a0914d1515636ad3dee36933f3a93ffaea4056d79a80bf0e4125b06d3dd0e"),
    "backend/first_unit_corrections.jsonl": (3915, "f437ae0f73d36f93d46398971c0a7e10a11182a873c8964aed709115b2c1af3a"),
    "backend/first_unit_documents.jsonl": (1223, "2eb5c55778a4c013e6f9766e40a0483ec7182f3c76bddfda633944e6f4ccb944"),
    "build/FIRST_UNIT_MANIFEST.csv": (1854, "73e6eaefca1e2a75415053da302c2ee7e56ac4e02ff025d1d3a074775f13e630"),
    "build/FIRST_UNIT_BUILD_RECEIPT.json": (1755, "8f182e1e2ac2fa14892397af51015e8c91162c252b7e972e1dc9cae7eb73893a"),
    "build/LESSON01_TRANSLATION_RECEIPT.json": (1483, "fa67729b94a38fc602d6e89d646bde76d3e24fdf575087262e1b088f2f363db2"),
    "source/id-ID/reader.css": (5890, "1d463e04c51aff4750dec54523952488635c08fc5d3ead30ffc399a43f96f77b"),
    "source/id-ID/course_card_alt_text.json": (1273, "ce580bfe695bfadd8ed0d866f5b3991554e76d7a878ee8365f07f203a61c9561"),
    "authority/FIRST_UNIT_ASSET_MANIFEST.csv": (4666, "e6973f56735defb100ac9c1b7ed2a1301a32377582b82a72d6ea3eb7db830e31"),
    "authority/runtime/MathJax-3.1.2/tex-svg.js": (1704911, "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a"),
    "authority/runtime/MathJax-3.1.2/LICENSE.txt": (11358, "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"),
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/color.js": (9192, "412863c1ea3db035795f39a6850f963261b81d260de61862c85013b2c96c01d7"),
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/enclose.js": (3071, "fed0d0fca9402ad9f23bba26a158cc6a802a267f900c238769e16ed30b4410ab"),
    "authority/runtime/MathJax-3.1.2/input/tex/extensions/cancel.js": (4029, "6b5ede35a63fb92d69e0648755746867efdbaebbf452506ebd878c33568aadf0"),
    "working/lesson01_asset_rights_audit.json": (17937, "165eea7fc029c154198e6b4aa271d18d562aba083fbc4eea08d41dc9b01fcdd9"),
    "working/lesson01_source_findings.md": (5601, "8183157dc52b1adde5c4b26783c50e772476d60f9d70f226c00cbaf0cbc6a0ae"),
}

LESSON01_ASSETS: dict[str, tuple[str, int, str]] = {
    "STAT-415-SEC-3-18-09.svg": (
        "O006-PSU-002-A0001", 1821,
        "375775fae6e23602ebb80a69f1b6bfe187415a932e9bbc608cf1864ad364440c",
    ),
    "stat-415-sec-3-18-10.svg": (
        "O006-PSU-002-A0002", 2693,
        "d6880dd245560b31efe664744a9c953adb77d349002b16fd785f1b7ec39255fa",
    ),
    "stat-415-sec-3-18-11.svg": (
        "O006-PSU-002-A0003", 2688,
        "7c94f0c22d3be28edc7b4fb969d14152543be180df0fa5bf029020912082caab",
    ),
    "stat-415-sec-3-18-12.svg": (
        "O006-PSU-002-A0004", 2690,
        "0e7a00a04750e9da3d55f39b202fc10ca8cfebed000a6aa7cd55f2744bc8a5d8",
    ),
    "STAT-415-SEC-3-18-13.svg": (
        "O006-PSU-002-A0005", 52253,
        "b3fc3f936d4aee619981611d7c0d8797ef7cc8135fe5e40b4e8d4ad9f0849e3f",
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


def translatable_nodes(main: Tag) -> list[NavigableString]:
    return [
        node for node in main.find_all(string=True)
        if isinstance(node, NavigableString) and first.is_translatable(node)
    ]


def boundary_whitespace(text: str) -> tuple[bool, bool]:
    return bool(re.match(r"^\s", text)), bool(re.search(r"\s$", text))


def stable_values(main: Tag, attribute: str) -> list[str]:
    values = [str(node.get(attribute)) for node in main.select(f"[{attribute}]")]
    if len(values) != len(set(values)):
        raise RuntimeError(f"duplicate stable identity: {attribute}")
    return values


def ensure_math_ids(main: Tag, document_id: str, expected_count: int) -> list[str]:
    """Add locale-neutral formula identities where the older normalization lacked them."""
    nodes = main.select(".math")
    if len(nodes) != expected_count:
        raise RuntimeError(f"math-node count differs before identity assignment: {document_id}")
    expected = [f"{document_id}-M{i:04d}" for i in range(1, expected_count + 1)]
    existing = [str(node.get("data-o006-math-id", "")) for node in nodes]
    if all(not value for value in existing):
        for node, math_id in zip(nodes, expected):
            node["data-o006-math-id"] = math_id
    elif existing != expected:
        raise RuntimeError(f"math stable-ID sequence differs: {document_id}")
    return expected


def native_id_duplicates(main: Tag) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in main.select("[id]"):
        value = str(node.get("id"))
        counts[value] = counts.get(value, 0) + 1
    return {key: value for key, value in counts.items() if value > 1}


def load_lesson01() -> tuple[
    BeautifulSoup,
    Tag,
    list[dict[str, str]],
    dict[str, NavigableString],
    list[str],
    list[str],
    list[str],
]:
    if not LESSON01_TRANSLATIONS.is_file():
        raise RuntimeError("Lesson01 translation CSV is not yet present")
    with LESSON01_TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        expected_fields = [
            "segment_id", "document_id", "component_id", "section_id",
            "source_sha256", "source_text", "target_text", "status",
        ]
        if reader.fieldnames != expected_fields:
            raise RuntimeError("Lesson01 translation CSV schema differs")
        rows = list(reader)
    if len(rows) != EXPECTED_LESSON01_SEGMENTS:
        raise RuntimeError("Lesson01 translation boundary is not 221 segments")

    soup = BeautifulSoup((NORMALIZED / "Lesson01.html").read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("normalized Lesson01 main is missing")
    source_math = [node.get_text() for node in main.select(".math")]
    if len(source_math) != EXPECTED_LESSON01_MATH:
        raise RuntimeError("normalized Lesson01 math-node count differs")
    unit_ids = stable_values(main, "data-o006-id")
    math_ids = stable_values(main, "data-o006-math-id")
    if unit_ids != [f"O006-PSU-002-U{i:04d}" for i in range(1, EXPECTED_LESSON01_UNITS + 1)]:
        raise RuntimeError("Lesson01 structural-unit identity sequence differs")
    if math_ids != [f"O006-PSU-002-M{i:04d}" for i in range(1, EXPECTED_LESSON01_MATH + 1)]:
        raise RuntimeError("Lesson01 math identity sequence differs")
    if native_id_duplicates(main) != {"fig-stat415sec31812": 2}:
        raise RuntimeError("Lesson01 native-ID defect surface differs")

    nodes = translatable_nodes(main)
    if len(nodes) != EXPECTED_LESSON01_SEGMENTS:
        raise RuntimeError("Lesson01 translatable-node count differs")
    target_nodes: dict[str, NavigableString] = {}
    for ordinal, (row, node) in enumerate(zip(rows, nodes), start=1):
        sid = f"O006-PSU-002-S{ordinal:04d}"
        if row["segment_id"] != sid:
            raise RuntimeError(f"Lesson01 segment order differs: {sid}")
        if row["document_id"] != LESSON01_DOCUMENT_ID or row["component_id"] != "Lesson01":
            raise RuntimeError(f"Lesson01 segment identity differs: {sid}")
        source_text = str(node)
        if row["source_text"] != source_text:
            raise RuntimeError(f"Lesson01 source text differs: {sid}")
        if row["source_sha256"] != first.sha256(source_text.encode("utf-8")):
            raise RuntimeError(f"Lesson01 source hash differs: {sid}")
        target_text = row["target_text"]
        if row["status"] != "translated" or not target_text.strip():
            raise RuntimeError(f"Lesson01 translation unfinished: {sid}")
        if "\ufffd" in target_text:
            raise RuntimeError(f"Lesson01 target contains replacement character: {sid}")
        if boundary_whitespace(source_text) != boundary_whitespace(target_text):
            raise RuntimeError(f"Lesson01 boundary whitespace differs: {sid}")
        replacement = NavigableString(target_text)
        node.replace_with(replacement)
        target_nodes[sid] = replacement
    return soup, main, rows, target_nodes, source_math, unit_ids, math_ids


def rewrite_math(
    main: Tag,
    math_id: str,
    old: str,
    new: str,
) -> dict[str, str]:
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"math correction identity differs: {math_id}")
    node = nodes[0]
    before = node.get_text()
    if before.count(old) != 1:
        raise RuntimeError(f"math correction source differs: {math_id}")
    after = before.replace(old, new, 1)
    node.clear()
    node.append(NavigableString(after))
    return {
        "math_id": math_id,
        "source_surface_sha256": first.sha256(before.encode("utf-8")),
        "target_surface_sha256": first.sha256(after.encode("utf-8")),
    }


def apply_lesson01_corrections(main: Tag) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    # L01-D001 / ADV-0015: duplicate native figure ID.
    duplicates = main.select("#fig-stat415sec31812")
    if len(duplicates) != 2:
        raise RuntimeError("L01-D001 duplicate-ID surface differs")
    image = next((node for node in duplicates if node.name == "img"), None)
    wrapper = next((node for node in duplicates if node.name == "div"), None)
    if image is None or wrapper is None:
        raise RuntimeError("L01-D001 duplicate-ID topology differs")
    target_id = "psu415-l01-fig-stat415sec31812-image"
    if main.find(id=target_id) is not None:
        raise RuntimeError("L01-D001 target ID already exists")
    image["data-source-id"] = "fig-stat415sec31812"
    image["id"] = target_id
    records.append({
        "correction_id": "O006-PSU-ADV-0015",
        "source_defect_id": "L01-D001",
        "status": "applied-target-only",
        "surface": "html-id",
        "source_value": "fig-stat415sec31812",
        "target_value": target_id,
        "replacement_count": 1,
    })

    # L01-D002 / ADV-0016: extra LaTeX \right] delimiter in summary.
    surface = rewrite_math(
        main,
        "O006-PSU-002-M0169",
        r"\left[F(y)]\right]^{r-1}",
        r"\left[F(y)\right]^{r-1}",
    )
    records.append({
        "correction_id": "O006-PSU-ADV-0016",
        "source_defect_id": "L01-D002",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    # L01-D003 / ADV-0017: both six-trial examples stop the index at five.
    index_surfaces = [
        rewrite_math(main, math_id, r"i=1, 2, \cdots, 5", r"i=1, 2, \cdots, 6")
        for math_id in ("O006-PSU-002-M0045", "O006-PSU-002-M0065")
    ]
    records.append({
        "correction_id": "O006-PSU-ADV-0017",
        "source_defect_id": "L01-D003",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 2,
        "surfaces": index_surfaces,
    })

    # L01-D004 / ADV-0018: the theorem proof counts all n trials, not r.
    surface = rewrite_math(
        main,
        "O006-PSU-002-M0104",
        r"i=1, 2, \cdots, r",
        r"i=1, 2, \cdots, n",
    )
    records.append({
        "correction_id": "O006-PSU-ADV-0018",
        "source_defect_id": "L01-D004",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    # L01-D005 / ADV-0019: unrelated Celsius/Fahrenheit alt text.
    wrappers = main.select('[data-o006-id="O006-PSU-002-U0057"]')
    images = main.select('[data-o006-id="O006-PSU-002-U0061"][src="assets/stat-415-sec-3-18-10.svg"]')
    if (
        len(wrappers) != 1
        or wrappers[0].name != "div"
        or wrappers[0].get("alt") != "Celsius vs Fahrenheit scatterplot"
        or len(images) != 1
        or images[0].name != "img"
        or images[0].get("alt") != "Celsius vs Fahrenheit scatterplot"
    ):
        raise RuntimeError("L01-D005 alt-text surface differs")
    source_wrapper_alt = str(wrappers[0]["alt"])
    source_image_alt = str(images[0]["alt"])
    target_alt = (
        "Garis bilangan yang menunjukkan lima nilai kurang dari satu "
        "dan satu nilai tidak kurang dari satu."
    )
    del wrappers[0]["alt"]
    images[0]["alt"] = target_alt
    records.append({
        "correction_id": "O006-PSU-ADV-0019",
        "source_defect_id": "L01-D005",
        "status": "applied-target-only",
        "surface": "html-alt",
        "asset_id": "O006-PSU-002-A0002",
        "replacement_count": 2,
        "surfaces": [
            {
                "unit_id": "O006-PSU-002-U0057",
                "action": "remove-nonsemantic-wrapper-alt",
                "source_surface_sha256": first.sha256(source_wrapper_alt.encode("utf-8")),
                "target_value": None,
            },
            {
                "unit_id": "O006-PSU-002-U0061",
                "action": "replace-image-alt",
                "source_surface_sha256": first.sha256(source_image_alt.encode("utf-8")),
                "target_surface_sha256": first.sha256(target_alt.encode("utf-8")),
            },
        ],
    })

    # L01-D006 / ADV-0020: Equation 1.1 drops the binomial coefficient.
    surface = rewrite_math(
        main,
        "O006-PSU-002-M0127",
        r"+\sum_{k=r}^{n-1}[F(y)]^k",
        r"+\sum_{k=r}^{n-1}{n\choose k}[F(y)]^k",
    )
    records.append({
        "correction_id": "O006-PSU-ADV-0020",
        "source_defect_id": "L01-D006",
        "status": "applied-target-only",
        "surface": "math",
        "replacement_count": 1,
        **surface,
    })

    expected_ids = {f"O006-PSU-ADV-{i:04d}" for i in range(15, 21)}
    if {str(row["correction_id"]) for row in records} != expected_ids or len(records) != 6:
        raise RuntimeError("Lesson01 correction registry differs")
    for row in records:
        expected_count = 2 if row["source_defect_id"] in {"L01-D003", "L01-D005"} else 1
        if row["replacement_count"] != expected_count or row["status"] != "applied-target-only":
            raise RuntimeError(f"Lesson01 correction count/status differs: {row['source_defect_id']}")
    return records


def normalize_index(main: Tag, alt_text: dict[str, str]) -> None:
    first.normalize_chrome(main, "index", alt_text)
    for anchor in main.select("a[href]"):
        href = str(anchor.get("href"))
        if href == "Lesson00.html":
            anchor["data-translation-status"] = "complete"
        elif href == LESSON01_SOURCE_URL:
            anchor["href"] = "Lesson01.html"
            anchor["data-translation-status"] = "complete"
            classes = [value for value in (anchor.get("class") or []) if value != "pending-source"]
            if classes:
                anchor["class"] = classes
            else:
                anchor.attrs.pop("class", None)
            anchor.attrs.pop("title", None)

    for lesson in range(13):
        expected_href = (
            f"Lesson{lesson:02d}.html" if lesson <= 1
            else f"https://online.stat.psu.edu/stat415/Lesson{lesson:02d}"
        )
        anchors = main.select(f'a[href="{expected_href}"]')
        if len(anchors) != 1:
            raise RuntimeError(f"index Lesson{lesson:02d} route count differs")
        expected_status = "complete" if lesson <= 1 else "pending"
        if anchors[0].get("data-translation-status") != expected_status:
            raise RuntimeError(f"index Lesson{lesson:02d} status differs")
        if lesson >= 2 and "pending-source" not in (anchors[0].get("class") or []):
            raise RuntimeError(f"index Lesson{lesson:02d} pending marker differs")


def normalize_lesson(main: Tag, filename: str) -> None:
    for node in main.select("[onclick]"):
        del node["onclick"]
    for node in main.select("[data-bs-toggle], [data-bs-target]"):
        node.attrs.pop("data-bs-toggle", None)
        node.attrs.pop("data-bs-target", None)
    center = main.find("center")
    if center is not None:
        center.name = "div"
        center["class"] = ["action-center"]
    breadcrumb = main.select("nav[aria-label='breadcrumb'] a[href]")
    if len(breadcrumb) != 2:
        raise RuntimeError(f"{filename} breadcrumb topology differs")
    breadcrumb[0]["href"] = "index.html#lessons"
    breadcrumb[1]["href"] = filename
    nav = main.select_one("nav[aria-label='breadcrumb']")
    if nav is None:
        raise RuntimeError(f"{filename} breadcrumb missing")
    nav["aria-label"] = "Jejak navigasi"


def page_document(main: Tag, component: str, source_url: str) -> bytes:
    title_node = main.select_one("h1")
    if title_node is None:
        raise RuntimeError(f"missing translated title: {component}")
    title = html.escape(title_node.get_text(" ", strip=True))
    source = html.escape(source_url, quote=True)
    note = (
        '<aside class="edition-note" aria-label="Status edisi">'
        '<strong>Edisi Bahasa Indonesia — 3 dari 14 dokumen.</strong> '
        'Laman utama serta Pelajaran 00 dan 01 telah diterjemahkan sepenuhnya. '
        'Pelajaran 02–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai. '
        f'<a href="{source}">Sumber resmi halaman ini</a>. '
        '<a href="licenses/index.html">Atribusi, perubahan, dan lisensi</a>.'
        '</aside>'
    )
    script = '<script defer src="assets/MathJax/tex-svg.js"></script>\n' if component != "index" else ""
    markup = (
        "<!doctype html>\n"
        '<html lang="id-ID">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{source}">\n'
        f'<meta name="translation-provenance" content="{PROVENANCE}">\n'
        '<meta name="edition-status" content="partial: 3 of 14 documents complete; landing and Lessons 00–01">\n'
        '<link rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">\n'
        '<link rel="stylesheet" href="assets/reader.css">\n'
        f"{script}</head>\n<body>\n"
        '<a class="skip-link" href="#quarto-document-content">Lewati ke isi utama</a>\n'
        '<header class="site-header"><div class="site-header__inner">'
        '<div><p class="site-title">STAT 415 — Pengantar Statistika Matematis</p>'
        '<p class="site-subtitle">Rekonstruksi dan terjemahan Bahasa Indonesia · O006/C140</p></div>'
        '<nav class="site-nav" aria-label="Navigasi utama">'
        '<a href="index.html">Daftar pelajaran</a><a href="Lesson00.html">Pelajaran 00</a>'
        '<a href="Lesson01.html">Pelajaran 01</a><a href="licenses/index.html">Lisensi</a>'
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
<link rel="stylesheet" href="../assets/reader.css"></head><body>
<a class="skip-link" href="#licence-main">Lewati ke isi utama</a>
<header class="site-header"><div class="site-header__inner"><div><p class="site-title">Atribusi dan lisensi komponen</p>
<p class="site-subtitle">STAT 415 — edisi Bahasa Indonesia</p></div><nav class="site-nav" aria-label="Navigasi utama"><a href="../index.html">Daftar pelajaran</a><a href="../Lesson00.html">Pelajaran 00</a><a href="../Lesson01.html">Pelajaran 01</a></nav></div></header>
<div class="page-shell"><main id="licence-main"><h1>Atribusi, perubahan, dan lisensi</h1>
<h2>Konten Penn State</h2><p>Catatan mata kuliah resmi dirancang dan dikembangkan oleh <a href="https://science.psu.edu/stat">Departemen Statistika Penn State</a>. Menurut halaman sumber, kontennya tersedia di bawah <a rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)</a>, kecuali dinyatakan lain.</p>
<p>Edisi ini merupakan terjemahan dan rekonstruksi tidak resmi. Perubahan meliputi penerjemahan ke id-ID, sumber HTML semantik yang dinormalisasi, identitas mesin tambahan, gaya pembaca lokal, kontrol HTML aksesibel, teks alternatif gambar, serta empat belas koreksi Lesson 00 dan enam koreksi Lesson 01 yang dicatat secara terpisah. Byte sumber resmi tidak diubah. Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat.</p>
<p>Lima gambar pengajaran Lesson 01 dipertahankan dari URL resmi halaman tersebut di bawah pemberitahuan CC BY-NC 4.0 yang sama; setiap identitas, URL, byte, hash, dan keterbatasan bukti hak dicatat dalam audit aset. Sumber resmi: <a href="https://online.stat.psu.edu/stat415/">STAT 415</a>. Status edisi saat ini: laman utama serta Pelajaran 00 dan 01 lengkap; Pelajaran 02–12 belum diterjemahkan.</p>
<h2>MathJax</h2><p>MathJax 3.1.2 digunakan secara lokal untuk merender matematika dan tersedia di bawah Apache License 2.0. <a href="MathJax-3.1.2-LICENSE.txt">Baca teks lisensi yang disertakan</a>.</p>
<h2>Provenans</h2><p>{PROVENANCE}. Seluruh kredit sumber dan kontributor manusia tetap dipertahankan.</p>
</main></div><footer class="site-footer"><div class="site-footer__inner">Koleksi C140 mempertahankan identitas dan lisensi setiap komponen; tidak ada relisensi seragam.</div></footer></body></html>
"""
    return markup.encode("utf-8")


def document_row(
    component: str,
    filename: str,
    document_id: str,
    source_url: str,
    source_math: list[str],
    target_math: list[str],
    target_payload: bytes,
    segments: int,
    structural_units: int,
) -> dict[str, object]:
    return {
        "schema": "o006.stat415.document.v1",
        "document_id": document_id,
        "component_id": component,
        "source_url": source_url,
        "source_path": f"source/normalized/en-US/{filename}",
        "target_path": f"source/id-ID/{filename}",
        "locale": "id-ID",
        "translation_status": "complete",
        "translation_segments": segments,
        "structural_units": structural_units,
        "math_nodes": len(target_math),
        "source_math_sha256": first.sha256("\n".join(source_math).encode("utf-8")),
        "target_math_sha256": first.sha256("\n".join(target_math).encode("utf-8")),
        "target_bytes": len(target_payload),
        "target_sha256": first.sha256(target_payload),
    }


def add_first_unit_assets(reader: dict[PurePosixPath, bytes]) -> None:
    with first.ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 13:
        raise RuntimeError("first-unit asset manifest differs")
    for row in rows:
        filename = PurePosixPath(row["relative_path"]).name
        data = (first.ASSETS / filename).read_bytes()
        if len(data) != int(row["bytes"]) or first.sha256(data) != row["sha256"]:
            raise RuntimeError(f"first-unit asset differs: {filename}")
        destination = PurePosixPath(f"assets/{filename}")
        if destination in reader:
            raise RuntimeError(f"reader asset collision: {destination}")
        reader[destination] = data


def add_lesson01_assets(reader: dict[PurePosixPath, bytes]) -> None:
    audit = json.loads(LESSON01_ASSET_AUDIT.read_text("utf-8"))
    if audit.get("schema_version") != "o006.stat415.lesson_asset_rights_audit.v1":
        raise RuntimeError("Lesson01 asset-audit schema differs")
    if audit.get("blocking_unresolved_rights") != []:
        raise RuntimeError("Lesson01 has blocking unresolved asset rights")
    assets = audit.get("assets")
    if not isinstance(assets, list) or len(assets) != 5:
        raise RuntimeError("Lesson01 asset-audit count differs")
    seen: set[str] = set()
    for row in assets:
        local_path = str(row.get("local_path"))
        filename = PurePosixPath(local_path).name
        if filename not in LESSON01_ASSETS or filename in seen:
            raise RuntimeError(f"Lesson01 asset inventory differs: {filename}")
        seen.add(filename)
        expected_id, expected_bytes, expected_sha256 = LESSON01_ASSETS[filename]
        if row.get("asset_id") != expected_id or row.get("disposition") != "freeze":
            raise RuntimeError(f"Lesson01 asset identity/disposition differs: {filename}")
        rights = row.get("rights")
        integrity = row.get("integrity")
        if not isinstance(rights, dict) or rights.get("applied_license") != "CC BY-NC 4.0":
            raise RuntimeError(f"Lesson01 asset licence differs: {filename}")
        if not isinstance(integrity, dict):
            raise RuntimeError(f"Lesson01 asset integrity evidence missing: {filename}")
        if integrity.get("decompressed_bytes") != expected_bytes or integrity.get("sha256") != expected_sha256:
            raise RuntimeError(f"Lesson01 asset audit hash differs: {filename}")
        path = ROOT / local_path
        data = path.read_bytes()
        if len(data) != expected_bytes or first.sha256(data) != expected_sha256:
            raise RuntimeError(f"Lesson01 asset bytes differ: {filename}")
        destination = PurePosixPath(f"assets/{filename}")
        if destination in reader:
            raise RuntimeError(f"reader asset collision: {destination}")
        reader[destination] = data
    if seen != set(LESSON01_ASSETS):
        raise RuntimeError("Lesson01 asset set differs")


def validate_reader_links(reader: dict[PurePosixPath, bytes]) -> None:
    for path, payload in reader.items():
        if path.suffix.lower() != ".html":
            continue
        soup = BeautifulSoup(payload, "html.parser")
        for node, attribute in [(node, "href") for node in soup.select("[href]")] + [
            (node, "src") for node in soup.select("[src]")
        ]:
            value = str(node.get(attribute))
            if not value or value.startswith(("#", "https://", "http://", "mailto:")):
                continue
            clean = value.split("#", 1)[0].split("?", 1)[0]
            resolved = PurePosixPath(posixpath.normpath((path.parent / clean).as_posix()))
            if resolved not in reader:
                raise RuntimeError(f"unresolved reader link: {path} -> {value}")
        for script in soup.select("script[src]"):
            if str(script.get("src")).startswith(("http://", "https://")):
                raise RuntimeError(f"external runtime request remains: {path}")
        markup = payload.decode("utf-8")
        if "googletagmanager" in markup or "site_libs/" in markup:
            raise RuntimeError(f"tracking/library source leaked into reader: {path}")


def compute() -> tuple[dict[str, bytes], dict[str, object], set[PurePosixPath]]:
    frozen_evidence = read_frozen_inputs()
    first_segments, first_translations = first.load_translations()
    if len(first_segments) != EXPECTED_FIRST_SEGMENTS:
        raise RuntimeError("first-unit segment count differs")
    alt_text = json.loads(first.ALT_TEXT.read_text("utf-8"))
    if not isinstance(alt_text, dict) or len(alt_text) != 13:
        raise RuntimeError("course-card alt-text catalog differs")

    reader: dict[PurePosixPath, bytes] = {}
    target_outputs: dict[str, bytes] = {}
    document_rows: list[dict[str, object]] = []
    first_correction_rows: list[dict[str, object]] = []
    first_unit_counts = {"index": (77, 197, 0), "Lesson00": (446, 365, 331)}

    for component, filename, document_id, source_url in first.DOCS:
        soup, main, target_nodes, source_math = first.translate_main(
            filename, document_id, first_translations[document_id]
        )
        source_unit_ids = stable_values(main, "data-o006-id")
        expected_segments, expected_units, expected_math = first_unit_counts[component]
        if len(source_unit_ids) != expected_units or len(source_math) != expected_math:
            raise RuntimeError(f"{component} normalized counts differ")
        if component == "Lesson00":
            first_correction_rows.extend(first.apply_lesson_corrections(soup, main, target_nodes))
            first.make_solutions_accessible(soup, main)
            normalize_lesson(main, filename)
        else:
            normalize_index(main, alt_text)
        expected_target_unit_ids = set(source_unit_ids)
        if component == "Lesson00":
            expected_target_unit_ids -= FIRST_UNIT_REMOVED_STABLE_UNITS
        if set(stable_values(main, "data-o006-id")) != expected_target_unit_ids:
            raise RuntimeError(f"{component} stable structural identities differ")
        ensure_math_ids(main, document_id, expected_math)
        target_math = [node.get_text() for node in main.select(".math")]
        if len(target_math) != expected_math:
            raise RuntimeError(f"{component} target math count differs")
        payload = page_document(main, component, source_url)
        reader[PurePosixPath(filename)] = payload
        target_outputs[f"source/id-ID/{filename}"] = payload
        document_rows.append(document_row(
            component, filename, document_id, source_url, source_math, target_math,
            payload, expected_segments, expected_units,
        ))

    expected_first_ids = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 15)}
    if {str(row["correction_id"]) for row in first_correction_rows} != expected_first_ids:
        raise RuntimeError("first-unit corrections were not preserved")
    historical_corrections = (ROOT / "backend" / "first_unit_corrections.jsonl").read_bytes()
    recomputed_first_corrections = first.canonical_jsonl(
        sorted(first_correction_rows, key=lambda row: str(row["correction_id"]))
    )
    if recomputed_first_corrections != historical_corrections:
        raise RuntimeError("recomputed first-unit correction evidence differs")

    (
        lesson_soup, lesson_main, lesson_rows, _lesson_target_nodes,
        lesson_source_math, lesson_unit_ids, lesson_math_ids,
    ) = load_lesson01()
    lesson_correction_rows = apply_lesson01_corrections(lesson_main)
    normalize_lesson(lesson_main, "Lesson01.html")
    if stable_values(lesson_main, "data-o006-id") != lesson_unit_ids:
        raise RuntimeError("Lesson01 structural identity/topology differs")
    if stable_values(lesson_main, "data-o006-math-id") != lesson_math_ids:
        raise RuntimeError("Lesson01 math identities differ")
    if native_id_duplicates(lesson_main):
        raise RuntimeError("Lesson01 target retains duplicate native IDs")
    ensure_math_ids(lesson_main, LESSON01_DOCUMENT_ID, EXPECTED_LESSON01_MATH)
    lesson_target_math = [node.get_text() for node in lesson_main.select(".math")]
    if len(lesson_target_math) != EXPECTED_LESSON01_MATH:
        raise RuntimeError("Lesson01 target math-node count differs")
    lesson_payload = page_document(lesson_main, "Lesson01", LESSON01_SOURCE_URL)
    reader[PurePosixPath("Lesson01.html")] = lesson_payload
    target_outputs["source/id-ID/Lesson01.html"] = lesson_payload
    document_rows.append(document_row(
        "Lesson01", "Lesson01.html", LESSON01_DOCUMENT_ID, LESSON01_SOURCE_URL,
        lesson_source_math, lesson_target_math, lesson_payload,
        len(lesson_rows), len(lesson_unit_ids),
    ))

    if sum(int(row["translation_segments"]) for row in document_rows) != EXPECTED_TOTAL_SEGMENTS:
        raise RuntimeError("cumulative translation segment count differs")
    if sum(int(row["structural_units"]) for row in document_rows) != EXPECTED_TOTAL_UNITS:
        raise RuntimeError("cumulative structural-unit count differs")
    if sum(int(row["math_nodes"]) for row in document_rows) != EXPECTED_TOTAL_MATH:
        raise RuntimeError("cumulative math-node count differs")

    correction_rows = sorted(
        first_correction_rows + lesson_correction_rows,
        key=lambda row: str(row["correction_id"]),
    )
    expected_all_ids = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 21)}
    if len(correction_rows) != 20 or {str(row["correction_id"]) for row in correction_rows} != expected_all_ids:
        raise RuntimeError("cumulative correction registry differs")

    css = first.CSS.read_bytes()
    runtime = (first.RUNTIME / "tex-svg.js").read_bytes()
    runtime_color = (first.RUNTIME / "input" / "tex" / "extensions" / "color.js").read_bytes()
    runtime_enclose = (first.RUNTIME / "input" / "tex" / "extensions" / "enclose.js").read_bytes()
    runtime_cancel = (first.RUNTIME / "input" / "tex" / "extensions" / "cancel.js").read_bytes()
    runtime_license = (first.RUNTIME / "LICENSE.txt").read_bytes()
    reader[PurePosixPath("assets/reader.css")] = css
    reader[PurePosixPath("assets/MathJax/tex-svg.js")] = runtime
    reader[PurePosixPath("assets/MathJax/input/tex/extensions/color.js")] = runtime_color
    reader[PurePosixPath("assets/MathJax/input/tex/extensions/enclose.js")] = runtime_enclose
    reader[PurePosixPath("assets/MathJax/input/tex/extensions/cancel.js")] = runtime_cancel
    reader[PurePosixPath("licenses/index.html")] = license_page()
    reader[PurePosixPath("licenses/MathJax-3.1.2-LICENSE.txt")] = runtime_license
    add_first_unit_assets(reader)
    add_lesson01_assets(reader)
    if len(reader) != EXPECTED_READER_FILES:
        raise RuntimeError("cumulative reader is not exactly 28 files")
    validate_reader_links(reader)

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

    lesson_translation_bytes = LESSON01_TRANSLATIONS.read_bytes()
    builder_bytes = Path(__file__).read_bytes()
    receipt: dict[str, object] = {
        "schema": "o006.stat415.through-lesson01-build.v1",
        "status": "built",
        "coverage": {
            "complete_documents": ["index", "Lesson00", "Lesson01"],
            "complete_count": 3,
            "corpus_document_count": 14,
            "next_document": "Lesson02",
        },
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "translation_segments": EXPECTED_TOTAL_SEGMENTS,
        "structural_units_normalized": EXPECTED_TOTAL_UNITS,
        "math_nodes": {"index": 0, "Lesson00": 331, "Lesson01": 169, "total": 500},
        "corrections": {
            "count": 20,
            "first_unit_count": 14,
            "lesson01_count": 6,
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
            "MathJax 3.1.2": "Apache-2.0",
            "aggregate_uniform_relicense": False,
        },
        "offline": {
            "external_runtime_requests": 0,
            "analytics": False,
            "cookies": False,
            "local_mathjax": True,
        },
        "historical_first_unit_evidence": {
            name: frozen_evidence[name]
            for name in sorted(HISTORICAL_PROTECTED_OUTPUTS)
        },
        "inputs": {
            "frozen": frozen_evidence,
            "lesson01_translation": {
                "path": relative(LESSON01_TRANSLATIONS),
                "bytes": len(lesson_translation_bytes),
                "sha256": first.sha256(lesson_translation_bytes),
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
        raise RuntimeError("cumulative output set would overwrite historical first-unit evidence")
    return outputs, receipt, reader_files


def current_reader_files() -> set[PurePosixPath]:
    if not BUILD.exists():
        return set()
    return {
        PurePosixPath(path.relative_to(BUILD).as_posix())
        for path in BUILD.rglob("*") if path.is_file()
    }


def verify_outputs(
    outputs: dict[str, bytes],
    expected_reader_files: set[PurePosixPath],
) -> None:
    for name, payload in outputs.items():
        path = ROOT / name
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"cumulative build output differs: {name}")
    actual_reader_files = current_reader_files()
    if actual_reader_files != expected_reader_files:
        missing = sorted(path.as_posix() for path in expected_reader_files - actual_reader_files)
        extra = sorted(path.as_posix() for path in actual_reader_files - expected_reader_files)
        raise RuntimeError(f"reader inventory differs; missing={missing}; extra={extra}")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    outputs, receipt, expected_reader_files = compute()
    existing_extra = current_reader_files() - expected_reader_files
    if existing_extra:
        raise RuntimeError(
            "refusing to delete unexpected reader files: "
            + ", ".join(sorted(path.as_posix() for path in existing_extra))
        )
    if args.write:
        receipt_name = relative(RECEIPT)
        for name in sorted(outputs, key=lambda value: (value == receipt_name, value.casefold())):
            first.atomic_write(ROOT / name, outputs[name])
        state = "written"
    else:
        state = "verified"
    verify_outputs(outputs, expected_reader_files)
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
