#!/usr/bin/env python3
"""Prepare accessible SVG math fallbacks and deterministically finalize EPUB3."""

from __future__ import annotations

import argparse
import copy
import hashlib
import html
import io
import json
import posixpath
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
RAW_EPUB = ROOT / "build" / "book" / "stat415-id-book.raw.epub"
FORMULA_DIR = ROOT / "build" / "book" / "math-fallbacks"
FORMULA_JSON = FORMULA_DIR / "formulas.json"
RENDER_HTML = FORMULA_DIR / "render.html"
RENDER_RECEIPT = ROOT / "build" / "EPUB_MATH_FALLBACK_RENDER_RECEIPT.json"
FINAL_EPUB = ROOT / "output" / "epub" / "stat415-pengantar-statistika-matematis-id.epub"
FINAL_RECEIPT = ROOT / "build" / "CONSOLIDATED_EPUB_BUILD_RECEIPT.json"
EPUB_CSS = ROOT / "source" / "book" / "epub.css"
EXPECTED_FALLBACKS = 17
EXPECTED_FOCUSABLE_MATH = 125
DISPLAY_MATH_TEX_MIN_CHARS = 180
INLINE_MATH_TEX_MIN_CHARS = 80
MTABLE_MAX_ROW_TOKEN_MIN_CHARS = 40
MTABLE_MAX_ROW_CELLS_MIN = 5
FIXED_MODIFIED = "2026-08-26T00:00:00Z"
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
XHTML_NS = "http://www.w3.org/1999/xhtml"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"
EPUB_NS = "http://www.idpf.org/2007/ops"
XML_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.-]*$")
CLASS_MATH_XPATH = (
    '//*[contains(concat(" ", normalize-space(@class), " "), " math ") '
    'and not(ancestor::*[contains(concat(" ", normalize-space(@class), " "), " math ")])]'
)
LESSON07_EMPTY_OBJECTIVES_ID = "O006-PSU-008-U0020"
LESSON07_EMPTY_OBJECTIVES_INTRO = (
    "Setelah menyelesaikan pelajaran ini, Anda diharapkan mampu:"
)
RENDITION_SPECIFIC_OMISSIONS = (
    {
        "epub_document": "EPUB/text/ch001.xhtml",
        "reason": (
            "The primary Lesson 07 source contains the objectives heading and "
            "introductory sentence but no objective list; the empty reader-facing "
            "block is omitted and no objectives are synthesized."
        ),
        "source_element_id": LESSON07_EMPTY_OBJECTIVES_ID,
    },
)
INDONESIAN_IMAGE_ALT_REPAIRS = (
    {
        "expected": "Coordinate graph of f(x) = 1/2x",
        "replacement": "Grafik koordinat f(x) = 1/2x.",
        "source_element_id": "O006-PSU-002-U0048",
        "target_evidence_ids": ["O006-PSU-002-U0046", "O006-PSU-002-U0049"],
    },
    {
        "expected": "Number line showing 6 values less than 1.",
        "replacement": "Garis bilangan yang menunjukkan enam nilai kurang dari satu.",
        "source_element_id": "O006-PSU-002-U0068",
        "target_evidence_ids": ["O006-PSU-002-U0063"],
    },
    {
        "expected": (
            "Number line showing four values less than and two greater than one."
        ),
        "replacement": (
            "Garis bilangan yang menunjukkan empat nilai kurang dari satu dan dua "
            "nilai lebih dari satu."
        ),
        "source_element_id": "O006-PSU-002-U0075",
        "target_evidence_ids": ["O006-PSU-002-U0070"],
    },
    {
        "expected": "Density plot for r = 1, 4, 6",
        "replacement": "Plot kepadatan untuk r = 1, 4, 6.",
        "source_element_id": "O006-PSU-002-U0177",
        "target_evidence_ids": ["O006-PSU-002-S0206", "O006-PSU-002-U0178"],
    },
)
EXPECTED_HEADING_FORWARD_SKIPS = (
    ("O006-PSU-000-U0014", "O006-PSU-000-U0023"),
    ("O006-PSU-002-U0025", "O006-PSU-002-U0032"),
    ("O006-PSU-002-U0117", "O006-PSU-002-U0130"),
    ("O006-PSU-004-U0030", "O006-PSU-004-U0033"),
    ("O006-PSU-004-U0302", "O006-PSU-004-U0307"),
    ("O006-PSU-005-U0028", "O006-PSU-005-U0041"),
    ("O006-PSU-005-U0087", "O006-PSU-005-U0090"),
    ("O006-PSU-005-U0160", "O006-PSU-005-U0165"),
    ("O006-PSU-005-U0253", "O006-PSU-005-U0257"),
    ("O006-PSU-007-U0042", "O006-PSU-007-U0068"),
    ("O006-PSU-007-U0121", "O006-PSU-007-U0133"),
    ("O006-PSU-008-U0024", "O006-PSU-008-U0049"),
    ("O006-PSU-010-U0195", "O006-PSU-010-U0210"),
    ("O006-PSU-010-U0291", "O006-PSU-010-U0296"),
    ("O006-PSU-011-U0028", "O006-PSU-011-U0038"),
    ("O006-PSU-011-U0138", "O006-PSU-011-U0145"),
    ("O006-PSU-012-U0037", "O006-PSU-012-U0064"),
    ("O006-PSU-012-U0093", "O006-PSU-012-U0100"),
    ("O006-PSU-012-U0217", "O006-PSU-012-U0227"),
    ("O006-PSU-013-U0083", "O006-PSU-013-U0094"),
    ("O006-PSU-013-U0556", "O006-PSU-013-U0722"),
)
KNOWN_SOURCE_TABLE_LIMITATIONS = (
    {
        "expected_rows": 2,
        "expected_scope_attributes": 0,
        "expected_table_headers": 5,
        "source_element_id": "O006-PSU-001-U0334",
        "source_path": "source/id-ID/Lesson00.html",
        "summary": (
            "Historical two-row PMF table has column header cells but no caption "
            "or explicit scope associations; surrounding source prose introduces it."
        ),
    },
    {
        "expected_rows": 2,
        "expected_scope_attributes": 0,
        "expected_table_headers": 0,
        "source_element_id": "O006-PSU-008-U0100",
        "source_path": "source/id-ID/Lesson07.html",
        "summary": (
            "Historical two-row inline display of ten Bernoulli observations uses "
            "table layout without caption or header cells."
        ),
    },
)
FORMULA_ALT_BY_KEY = {
    "0e2c238e54fc02fcfb0a": (
        "g subskrip 5 dari y sama dengan tiga suku. Suku pertama dan ketiga "
        "dicoret; suku yang tersisa adalah 6 faktorial dibagi 4 faktorial kali "
        "1 faktorial, dikali 1 kurang y kuadrat per 4, dikali y kuadrat per 4 "
        "pangkat 4, dikali 2y per 4."
    ),
    "101ddb1d8278c7f1c369": (
        "Koefisien binomial n pilih k dikali k sama dengan n faktorial dibagi "
        "hasil kali k kurang 1 faktorial dan n kurang k faktorial; faktor k "
        "dicoret dari k faktorial."
    ),
    "153e1e35a26f99477ddc": (
        "Koefisien binomial n pilih k dikali n kurang k sama dengan n faktorial "
        "dibagi hasil kali k faktorial dan n kurang k kurang 1 faktorial; faktor "
        "n kurang k dicoret."
    ),
    "a5926beaa6c1a7eb76e6": (
        "Fungsi massa bersama sampel Poisson difaktorkan menjadi phi dari jumlah "
        "x_i dan lambda, yaitu e pangkat minus n lambda kali lambda pangkat n "
        "x-bar, dikali h dari x_1 sampai x_n, yaitu satu dibagi hasil kali semua "
        "x_i faktorial."
    ),
    "09301f856efc33c97242": (
        "Fungsi massa Bernoulli f dari x dan p sama dengan p pangkat x dikali "
        "1 kurang p pangkat 1 kurang x, lalu ditulis dalam bentuk eksponensial: "
        "x log p per 1 kurang p, ditambah log 1, ditambah log 1 kurang p."
    ),
    "db49d867f00eff608565": (
        "Fungsi massa Bernoulli dalam bentuk keluarga eksponensial: f dari x dan p "
        "sama dengan eksponensial dari x log p per 1 kurang p, ditambah log 1, "
        "ditambah log 1 kurang p."
    ),
    "47e24b5f9770070ed068": (
        "Kepadatan normal dengan rataan mu dan varians satu ditulis sebagai satu "
        "per akar 2 pi kali e pangkat minus x kurang mu kuadrat per 2, dan sebagai "
        "eksponensial dari x mu, minus x kuadrat per 2, minus mu kuadrat per 2, "
        "minus setengah log 2 pi."
    ),
    "064aca50187f49b280e2": (
        "Kepadatan eksponensial f dari x dan theta sama dengan satu per theta kali "
        "e pangkat minus x per theta; bentuk keluarga eksponensialnya memakai "
        "k dari x sama dengan minus x, p dari theta sama dengan satu per theta, "
        "s dari x sama dengan log 1, dan q dari theta sama dengan minus log theta."
    ),
    "f5bf473e5d41fcb23c60": (
        "Kepadatan bersama keluarga eksponensial satu parameter difaktorkan menjadi "
        "phi dari jumlah K dari x_i dan theta, dikali h dari x_1 sampai x_n. "
        "Faktor pertama adalah eksponensial dari p theta kali jumlah K x_i ditambah "
        "n q theta; faktor kedua adalah eksponensial dari jumlah S x_i."
    ),
    "4dd8d54aed5c4255e901": (
        "Kepadatan normal dua parameter dalam bentuk keluarga eksponensial: "
        "eksponensial dari minus x kuadrat per 2 theta_2, ditambah theta_1 per "
        "theta_2 kali x, ditambah suku q theta_1 theta_2 yang memuat minus "
        "theta_1 kuadrat per 2 theta_2 dan minus log akar 2 pi theta_2."
    ),
    "83f670e3f9a4dd0b88e4": "Huruf L berwarna merah.",
    "b3c177bd20500cdab1d9": "Huruf I berwarna merah.",
    "652ad926f86cfaa76c5a": "Huruf N berwarna merah.",
    "c6af31cac47a9844011c": "Huruf E berwarna merah.",
    "1d528d29765aea1a824f": "Kata L-I-N-E berwarna merah.",
    "a2d123598650116857c6": (
        "Log kemungkinan L sama dengan minus n per 2 log 2 pi, minus n per 2 log "
        "sigma kuadrat, minus satu per 2 sigma kuadrat dikali jumlah dari i sama "
        "dengan 1 sampai n atas Y_i kurang alpha kurang beta kali x_i kurang x-bar, "
        "seluruhnya dikuadratkan."
    ),
    "0f8f7a4262e8b110e76f": (
        "Jumlah kuadrat galat dibagi sigma kuadrat, yang berdistribusi khi-kuadrat "
        "dengan n derajat bebas, diuraikan menjadi alpha-topi kurang alpha kuadrat "
        "dibagi sigma kuadrat per n, ditambah beta-topi kurang beta kuadrat dibagi "
        "sigma kuadrat per jumlah x_i kurang x-bar kuadrat, ditambah n sigma-topi "
        "kuadrat dibagi sigma kuadrat; dua suku pertama masing-masing berdistribusi "
        "khi-kuadrat satu, sedangkan distribusi suku terakhir ditandai sebagai yang "
        "akan ditentukan."
    ),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def parse_xml(data: bytes) -> etree._ElementTree:
    return etree.parse(
        io.BytesIO(data), etree.XMLParser(resolve_entities=False, remove_blank_text=False)
    )


def serialize_xml(tree: etree._ElementTree) -> bytes:
    doctype = tree.docinfo.doctype or None
    return etree.tostring(
        tree,
        encoding="utf-8",
        xml_declaration=True,
        doctype=doctype,
        pretty_print=False,
    )


def strip_math_delimiters(value: str, css_class: str) -> tuple[str, bool]:
    text = value.strip()
    display = "display" in css_class.split()
    pairs = (("$$", "$$"), (r"\[", r"\]"), ("$", "$"), (r"\(", r"\)"))
    for opening, closing in pairs:
        if text.startswith(opening) and text.endswith(closing):
            text = text[len(opening) : len(text) - len(closing)].strip()
            display = opening in {"$$", r"\["}
            break
    return text, display


def formula_alt(key: str) -> str:
    if key not in FORMULA_ALT_BY_KEY:
        raise RuntimeError(f"Missing Indonesian spoken-math alternative for {key}")
    return FORMULA_ALT_BY_KEY[key]


def raw_formula_nodes(tree: etree._ElementTree) -> list[etree._Element]:
    nodes: list[etree._Element] = []
    for node in tree.xpath(CLASS_MATH_XPATH):
        if not node.xpath('.//*[local-name()="math"]'):
            nodes.append(node)
    return nodes


def read_epub(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def find_opf(entries: dict[str, bytes]) -> str:
    container = parse_xml(entries["META-INF/container.xml"])
    path = container.xpath('string(//*[local-name()="rootfile"]/@full-path)')
    if not path or path not in entries:
        raise RuntimeError("EPUB container does not resolve to an OPF package")
    return str(path)


def collect_formulas(entries: dict[str, bytes]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for name in sorted(entries):
        if not name.endswith((".xhtml", ".html")):
            continue
        tree = parse_xml(entries[name])
        for local_ordinal, node in enumerate(raw_formula_nodes(tree), start=1):
            raw = "".join(node.itertext()).strip()
            css_class = str(node.get("class", ""))
            tex, display = strip_math_delimiters(raw, css_class)
            key = sha256_bytes(("display\0" if display else "inline\0").encode() + tex.encode())[
                :20
            ]
            records.append(
                {
                    "alt": formula_alt(key),
                    "display": display,
                    "epub_document": name,
                    "epub_document_ordinal": local_ordinal,
                    "key": key,
                    "raw_sha256": sha256_bytes(raw.encode("utf-8")),
                    "tex": tex,
                }
            )
    if len(records) != EXPECTED_FALLBACKS:
        raise RuntimeError(
            f"Expected {EXPECTED_FALLBACKS} raw math fallbacks, found {len(records)}"
        )
    keys = [str(record["key"]) for record in records]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Fallback formulas are not unique by stable TeX hash")
    return records


def prepare(raw_epub: Path) -> None:
    entries = read_epub(raw_epub)
    formulas = collect_formulas(entries)
    FORMULA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "formulas": formulas,
        "schema": "o006.stat415.epub-math-fallback-input.v1",
        "status": "prepared",
    }
    FORMULA_JSON.write_bytes(canonical_json_bytes(payload))
    surfaces = []
    for record in formulas:
        opening, closing = (r"\[", r"\]") if record["display"] else (r"\(", r"\)")
        surfaces.append(
            '<div class="fallback-surface" data-key="{}">{}{}</div>'.format(
                html.escape(str(record["key"]), quote=True),
                opening + html.escape(str(record["tex"])),
                closing,
            )
        )
    render = """<!doctype html>
<html lang="id-ID"><head><meta charset="utf-8">
<script>
window.MathJax = {
  loader: {load: ['[tex]/color', '[tex]/cancel']},
  tex: {packages: {'[+]': ['color', 'cancel']}},
  // Standalone EPUB fallbacks must carry their glyph paths directly.  A
  // shared/local font cache leaves <use> references dependent on browser DOM
  // IDs and produced broken, collapsed formulas in EPUB readers.
  svg: {fontCache: 'none'}
};
</script>
<script defer src="../../html-id/assets/MathJax/tex-svg.js"></script>
</head><body>
""" + "\n".join(surfaces) + "\n</body></html>\n"
    RENDER_HTML.write_bytes(render.encode("utf-8"))
    print(
        json.dumps(
            {
                "fallbacks": len(formulas),
                "formula_json_sha256": sha256_bytes(FORMULA_JSON.read_bytes()),
                "mode": "prepared",
            },
            sort_keys=True,
        )
    )


def add_accessibility_metadata(opf: etree._ElementTree) -> None:
    metadata = opf.xpath('//*[local-name()="metadata"]')[0]
    for node in opf.xpath(
        '//*[local-name()="meta" and @property="dcterms:modified"]'
    ):
        node.text = FIXED_MODIFIED
    existing = {
        str(node.text)
        for node in opf.xpath(
            '//*[local-name()="meta" and @property="schema:accessibilityFeature"]'
        )
    }
    for feature in ("MathML", "alternativeText"):
        if feature not in existing:
            node = etree.SubElement(metadata, f"{{{OPF_NS}}}meta")
            node.set("property", "schema:accessibilityFeature")
            node.text = feature
    summaries = opf.xpath(
        '//*[local-name()="meta" and @property="schema:accessibilitySummary"]'
    )
    summary_text = (
        "Publikasi ini menyediakan navigasi struktural, teks alternatif "
        "gambar, MathML, dan fallback SVG berteks alternatif. Anomali tingkat "
        "judul sumber diperbaiki hanya dalam rendisi EPUB; dua tabel historis "
        "mempertahankan keterbatasan sumber yang didokumentasikan dalam bukti build."
    )
    if not summaries:
        summary = etree.SubElement(metadata, f"{{{OPF_NS}}}meta")
        summary.set("property", "schema:accessibilitySummary")
        summary.text = summary_text
    elif len(summaries) != 1:
        raise RuntimeError("Expected at most one accessibility summary")
    else:
        summaries[0].text = summary_text
    if not opf.xpath('//*[local-name()="source"]'):
        source = etree.SubElement(metadata, f"{{{DC_NS}}}source")
        source.set("id", "epub-source-1")
        source.text = "https://online.stat.psu.edu/stat415/"
    if not opf.xpath(
        '//*[local-name()="meta" and @property="dcterms:provenance"]'
    ):
        provenance = etree.SubElement(metadata, f"{{{OPF_NS}}}meta")
        provenance.set("property", "dcterms:provenance")
        provenance.text = "OpenAI Codex gpt-5.6-sol, Ultra"


def local_entry_target(base_name: str, value: str) -> tuple[str, str] | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path)
    target = (
        posixpath.normpath(posixpath.join(posixpath.dirname(base_name), path))
        if path
        else base_name
    )
    return target, unquote(parsed.fragment)


def restore_lost_table_headers(tree: etree._ElementTree) -> int:
    """Restore two exact H0-false headers dropped by Pandoc's table parser."""

    repairs = 0
    expected = (
        (
            "o006-psu-010-table-1-h0-true",
            "o006-psu-010-table-1-h0-false",
            "O006-PSU-010-U0069",
            "O006-PSU-010-M0010",
        ),
        (
            "o006-psu-010-table-2-h0-true",
            "o006-psu-010-table-2-h0-false",
            "O006-PSU-010-U0089",
            "O006-PSU-010-M0015",
        ),
    )
    for true_id, false_id, unit_id, math_id in expected:
        if tree.xpath(f'//*[@id="{false_id}"]'):
            continue
        true_nodes = tree.xpath(f'//*[@id="{true_id}"]')
        if len(true_nodes) != 1 or etree.QName(true_nodes[0]).localname != "th":
            raise RuntimeError(f"Cannot restore missing table header {false_id}")
        restored = copy.deepcopy(true_nodes[0])
        restored.set("id", false_id)
        restored.set("data-o006-id", unit_id)
        math_nodes = restored.xpath('.//*[@data-o006-math-id]')
        if len(math_nodes) != 1:
            raise RuntimeError(f"Unexpected math structure in {true_id}")
        math_nodes[0].set("data-o006-math-id", math_id)
        strong = restored.xpath('.//*[local-name()="strong"]')
        if len(strong) != 1 or "benar" not in "".join(strong[0].itertext()):
            raise RuntimeError(f"Unexpected label structure in {true_id}")
        strong[0].text = "salah"
        true_nodes[0].addnext(restored)
        repairs += 1
    return repairs


def omit_lesson07_empty_objectives(tree: etree._ElementTree) -> int:
    """Omit the exact source-empty Lesson 07 objectives block from the EPUB."""

    nodes = tree.xpath(f'//*[@data-o006-id="{LESSON07_EMPTY_OBJECTIVES_ID}"]')
    if len(nodes) != 1:
        raise RuntimeError(
            "Expected exactly one Lesson 07 empty objectives block, "
            f"found {len(nodes)}"
        )
    node = nodes[0]
    if etree.QName(node).localname != "div" or "objectiveblock" not in str(
        node.get("class", "")
    ).split():
        raise RuntimeError("Unexpected Lesson 07 objectives container structure")
    paragraphs = node.xpath('./*[local-name()="p"]')
    if len(paragraphs) != 2:
        raise RuntimeError("Lesson 07 objectives block is no longer source-empty")
    title = " ".join("".join(paragraphs[0].itertext()).split())
    intro = " ".join("".join(paragraphs[1].itertext()).split())
    if title != "Tujuan" or intro != LESSON07_EMPTY_OBJECTIVES_INTRO:
        raise RuntimeError("Lesson 07 objectives block text changed unexpectedly")
    if node.xpath('.//*[local-name()="ul" or local-name()="ol" or local-name()="li"]'):
        raise RuntimeError("Lesson 07 objectives block now contains objective items")

    marker = etree.Comment(
        " EPUB rendition omission: source element "
        f"{LESSON07_EMPTY_OBJECTIVES_ID} contains no objective list; "
        "no objectives synthesized. "
    )
    node.getparent().replace(node, marker)
    return 1


def repair_indonesian_image_alternatives(tree: etree._ElementTree) -> int:
    """Use existing Indonesian target evidence for four inherited English alts."""

    repairs = 0
    for record in INDONESIAN_IMAGE_ALT_REPAIRS:
        source_id = str(record["source_element_id"])
        nodes = tree.xpath(
            f'//*[local-name()="img" and @data-o006-id="{source_id}"]'
        )
        if len(nodes) != 1:
            raise RuntimeError(
                f"Expected exactly one EPUB image for {source_id}, found {len(nodes)}"
            )
        image = nodes[0]
        if image.get("alt") != record["expected"]:
            raise RuntimeError(f"Inherited image alternative changed for {source_id}")
        image.set("alt", str(record["replacement"]))
        repairs += 1
    return repairs


def repair_heading_order(tree: etree._ElementTree) -> int:
    """Repair inherited h2-to-h4/h5 jumps only in the EPUB rendition."""

    repairs = 0
    card_headings = tree.xpath(
        '//*[local-name()="h5" and contains(concat(" ", normalize-space(@class), " "), '
        '" card-title ") and contains(concat(" ", normalize-space(@class), " "), '
        '" listing-title ")]'
    )
    if len(card_headings) != 13:
        raise RuntimeError(f"Expected 13 lesson-card h5 headings, found {len(card_headings)}")
    for heading in card_headings:
        heading.tag = f"{{{XHTML_NS}}}h3"
        repairs += 1

    target_ids = [target for source, target in EXPECTED_HEADING_FORWARD_SKIPS if source != "O006-PSU-000-U0014"]
    if len(target_ids) != 20:
        raise RuntimeError("Unexpected non-card heading repair inventory")
    for stable_id in target_ids:
        nodes = tree.xpath(
            f'//*[local-name()="h4" and @data-o006-id="{stable_id}"]'
        )
        if len(nodes) != 1:
            raise RuntimeError(f"Expected one inherited h4 heading for {stable_id}")
        nodes[0].tag = f"{{{XHTML_NS}}}h3"
        repairs += 1
    return repairs


def flatten_static_tabset_aria(tree: etree._ElementTree) -> int:
    """Remove browser-tab roles from the fully expanded static EPUB rendition."""

    tabs = tree.xpath('//*[@role="tab"]')
    panels = tree.xpath('//*[@role="tabpanel"]')
    if len(tabs) != 2 or len(panels) != 2:
        raise RuntimeError(
            f"Expected the two-source-tab static set, found {len(tabs)} tabs and "
            f"{len(panels)} panels"
        )
    for tab in tabs:
        for attr in ("aria-controls", "aria-selected", "href", "role"):
            if tab.get(attr) is not None:
                del tab.attrib[attr]
    for panel in panels:
        for attr in ("aria-labelledby", "role"):
            if panel.get(attr) is not None:
                del panel.attrib[attr]
    return len(tabs) + len(panels)


def label_lesson_card_links(tree: etree._ElementTree) -> int:
    """Name the 13 empty overlay links from their existing lesson headings."""

    anchors = tree.xpath(
        '//*[local-name()="a" and contains(concat(" ", normalize-space(@class), " "), '
        '" quarto-grid-link ")]'
    )
    if len(anchors) != 13:
        raise RuntimeError(f"Expected 13 lesson-card links, found {len(anchors)}")
    repairs = 0
    for anchor in anchors:
        resolved = local_entry_target("EPUB/text/ch001.xhtml", str(anchor.get("href")))
        if resolved is None or resolved[0] != "EPUB/text/ch001.xhtml" or not resolved[1]:
            raise RuntimeError("Lesson-card link does not resolve within the book body")
        targets = tree.xpath(f'//*[@id="{resolved[1]}"]')
        if len(targets) != 1:
            raise RuntimeError(f"Lesson-card target changed: {resolved[1]}")
        headings = targets[0].xpath('.//*[local-name()="h1"]')
        if not headings:
            raise RuntimeError(f"Lesson-card target has no heading: {resolved[1]}")
        label = " ".join("".join(headings[0].itertext()).split())
        anchor.set("aria-label", label)
        repairs += 1
    return repairs


def label_math_only_table_headers(tree: etree._ElementTree) -> int:
    """Give math-only headers a clipped text equivalent for reading systems."""

    repairs = 0
    for header in tree.xpath('//*[local-name()="th"]'):
        if header.get("aria-hidden") == "true" or header.get("hidden") is not None:
            continue
        outside_math = " ".join(
            " ".join(
                str(value)
                for value in header.xpath(
                    './/text()[not(ancestor::*[local-name()="math"])]'
                )
            ).split()
        )
        if outside_math:
            continue
        label = str(header.get("aria-label", "")).strip()
        if not label:
            annotations = header.xpath(
                './/*[local-name()="annotation" and '
                '@encoding="application/x-tex"]/text()'
            )
            if annotations:
                label = "Rumus matematika TeX: " + " ".join(
                    str(annotations[0]).split()
                )
        if not label:
            raise RuntimeError(
                "Empty table header lacks a deterministic text equivalent: "
                f"id={header.get('id')!r}, data-o006-id={header.get('data-o006-id')!r}"
            )
        fallback = etree.Element(f"{{{XHTML_NS}}}span")
        fallback.set("class", "epub-sr-only")
        fallback.text = label
        header.insert(0, fallback)
        repairs += 1
    if repairs != 22:
        raise RuntimeError(f"Expected 22 math-only/empty table headers, found {repairs}")
    return repairs


def make_scrollable_code_focusable(tree: etree._ElementTree) -> int:
    """Expose the one horizontally scrollable long code region to keyboards."""

    nodes = tree.xpath('//*[@id="cb245"]')
    if len(nodes) != 1:
        raise RuntimeError("Expected one long scrollable code region cb245")
    node = nodes[0]
    node.set("aria-label", "Kode R yang dapat digulir")
    node.set("role", "region")
    node.set("tabindex", "0")
    return 1


def math_reflow_risk_record(wrapper: etree._Element) -> dict[str, object] | None:
    """Return the deterministic static width-risk record for one math wrapper."""

    classes = set(str(wrapper.get("class", "")).split())
    annotations = wrapper.xpath(
        './/*[local-name()="annotation" and '
        '@encoding="application/x-tex"]/text()'
    )
    tex = " ".join(" ".join(str(value).split()) for value in annotations)
    mtables = wrapper.xpath('.//*[local-name()="mtable"]')
    max_row_cells = 0
    max_row_token_chars = 0
    for table in mtables:
        for row in table.xpath(
            './*[local-name()="mtr" or local-name()="mlabeledtr"]'
        ):
            cells = row.xpath('./*[local-name()="mtd"]')
            max_row_cells = max(max_row_cells, len(cells))
            token_text = "".join(
                str(value)
                for value in row.xpath(
                    './/*[local-name()="mi" or local-name()="mn" or '
                    'local-name()="mo" or local-name()="mtext"]/text()'
                )
            )
            max_row_token_chars = max(
                max_row_token_chars, len("".join(token_text.split()))
            )

    is_display = "display" in classes
    is_inline = "inline" in classes
    reasons: list[str] = []
    if mtables and (
        max_row_token_chars >= MTABLE_MAX_ROW_TOKEN_MIN_CHARS
        or max_row_cells >= MTABLE_MAX_ROW_CELLS_MIN
    ):
        reasons.append("wide-structural-mtable")
    if is_display and len(tex) >= DISPLAY_MATH_TEX_MIN_CHARS:
        reasons.append("long-display")
    if is_inline and len(tex) >= INLINE_MATH_TEX_MIN_CHARS:
        reasons.append("long-inline")
    if not reasons:
        return None
    return {
        "kind": "display" if is_display else "inline",
        "math_id": str(wrapper.get("data-o006-math-id")),
        "max_mtable_row_cells": max_row_cells,
        "max_mtable_row_token_chars": max_row_token_chars,
        "reasons": reasons,
        "tex_chars": len(tex),
    }


def make_math_reflow_regions_focusable(tree: etree._ElementTree) -> int:
    """Make only statically width-risky native MathML scroll regions focusable."""

    selected = 0
    wrappers = tree.xpath(
        '//*[@data-o006-math-id and '
        'contains(concat(" ", normalize-space(@class), " "), " math ") and '
        './/*[local-name()="math"]]'
    )
    for wrapper in wrappers:
        record = math_reflow_risk_record(wrapper)
        if record is None:
            continue
        wrapper.set("aria-label", "Rumus matematika yang dapat digulir secara horizontal")
        wrapper.set("data-o006-reflow-risk", "static-width-v1")
        wrapper.set("role", "group")
        wrapper.set("tabindex", "0")
        selected += 1
    if selected != EXPECTED_FOCUSABLE_MATH:
        raise RuntimeError(
            f"Expected {EXPECTED_FOCUSABLE_MATH} statically width-risky math "
            f"regions, found {selected}"
        )
    return selected


def collect_math_reflow_inventory(
    xhtml_trees: dict[str, etree._ElementTree],
) -> list[dict[str, object]]:
    """Bind the exact focusable width-risk inventory into the build receipt."""

    inventory: list[dict[str, object]] = []
    for name, tree in sorted(xhtml_trees.items()):
        for wrapper in tree.xpath('//*[@data-o006-reflow-risk="static-width-v1"]'):
            record = math_reflow_risk_record(wrapper)
            if record is None:
                raise RuntimeError("Focusable math wrapper no longer meets width-risk rule")
            if wrapper.get("tabindex") != "0" or wrapper.get("role") != "group":
                raise RuntimeError("Width-risk math wrapper is not keyboard focusable")
            record["epub_document"] = name
            inventory.append(record)
    inventory.sort(key=lambda item: (str(item["epub_document"]), str(item["math_id"])))
    ids = [str(item["math_id"]) for item in inventory]
    if len(inventory) != EXPECTED_FOCUSABLE_MATH or len(ids) != len(set(ids)):
        raise RuntimeError("Math reflow inventory count or stable-ID uniqueness failed")
    return inventory


def repair_xhtml(tree: etree._ElementTree, name: str) -> dict[str, int]:
    repairs = {
        "aria_dangling_removed": 0,
        "aria_targets_restored": 0,
        "duplicate_ids_renamed": 0,
        "empty_table_headers_labeled": 0,
        "illegal_attributes_removed": 0,
        "image_alt_texts_localized": 0,
        "lesson07_empty_objectives_omitted": 0,
        "lesson_card_links_labeled": 0,
        "lightbox_links_rewritten": 0,
        "math_reflow_regions_focusable": 0,
        "scrollable_code_regions_focusable": 0,
        "static_tab_aria_flattened": 0,
        "table_headers_restored": 0,
    }
    if name.endswith("/ch001.xhtml"):
        repairs["table_headers_restored"] = restore_lost_table_headers(tree)
        repairs["image_alt_texts_localized"] = repair_indonesian_image_alternatives(
            tree
        )
        repairs["heading_levels_repaired"] = repair_heading_order(tree)
        repairs["lesson_card_links_labeled"] = label_lesson_card_links(tree)
        repairs["lesson07_empty_objectives_omitted"] = (
            omit_lesson07_empty_objectives(tree)
        )
        repairs["static_tab_aria_flattened"] = flatten_static_tabset_aria(tree)
        repairs["empty_table_headers_labeled"] = label_math_only_table_headers(tree)
        repairs["scrollable_code_regions_focusable"] = (
            make_scrollable_code_focusable(tree)
        )
        repairs["math_reflow_regions_focusable"] = (
            make_math_reflow_regions_focusable(tree)
        )

    seen: dict[str, int] = {}
    for node in tree.xpath('//*[@id]'):
        value = str(node.get("id"))
        ordinal = seen.get(value, 0) + 1
        seen[value] = ordinal
        if ordinal > 1:
            node.set("id", f"{value}--nested-{ordinal}")
            repairs["duplicate_ids_renamed"] += 1

    for node in tree.xpath('//*[@alt or @width]'):
        local = etree.QName(node).localname
        if node.get("alt") is not None and local not in {"area", "img", "input"}:
            del node.attrib["alt"]
            repairs["illegal_attributes_removed"] += 1
        if node.get("width") is not None and local in {"div", "span"}:
            del node.attrib["width"]
            repairs["illegal_attributes_removed"] += 1

    ids = {str(node.get("id")) for node in tree.xpath('//*[@id]')}
    for node in tree.xpath('//*[@aria-describedby]'):
        kept: list[str] = []
        for target in str(node.get("aria-describedby")).split():
            if target in ids:
                kept.append(target)
                continue
            captions = node.xpath(
                './/*[local-name()="caption" or local-name()="figcaption"]'
            )
            caption = next((item for item in captions if item.get("id") is None), None)
            if caption is not None:
                caption.set("id", target)
                ids.add(target)
                kept.append(target)
                repairs["aria_targets_restored"] += 1
            else:
                repairs["aria_dangling_removed"] += 1
        if kept:
            node.set("aria-describedby", " ".join(kept))
        else:
            del node.attrib["aria-describedby"]
    return repairs


def repair_missing_image_links(
    entries: dict[str, bytes], trees: dict[str, etree._ElementTree]
) -> int:
    repaired = 0
    for name, tree in trees.items():
        for anchor in tree.xpath('//*[local-name()="a" and @href]'):
            resolved = local_entry_target(name, str(anchor.get("href")))
            if resolved is None or resolved[0] in entries:
                continue
            images = anchor.xpath('.//*[local-name()="img" and @src]')
            if len(images) != 1:
                continue
            image_target = local_entry_target(name, str(images[0].get("src")))
            if image_target is None or image_target[0] not in entries:
                continue
            # EPUB reading systems do not treat image resources as spine
            # navigation targets.  Preserve the image and its alternative
            # text, but disable the browser-only lightbox anchor rather than
            # linking either to a missing source path or a non-spine image.
            del anchor.attrib["href"]
            repaired += 1
    return repaired


def split_rights_document(
    entries: dict[str, bytes], trees: dict[str, etree._ElementTree]
) -> None:
    chapter_name = "EPUB/text/ch001.xhtml"
    rights_name = "EPUB/text/edition_rights.xhtml"
    chapter = trees[chapter_name]
    rights = chapter.xpath('//*[@id="edition-rights--document"]')
    if len(rights) != 1:
        raise RuntimeError("Expected one terminal edition-rights section")
    section = rights[0]
    section.getparent().remove(section)

    source_root = chapter.getroot()
    new_root = etree.Element(f"{{{XHTML_NS}}}html", nsmap=source_root.nsmap)
    for attr, value in source_root.attrib.items():
        new_root.set(attr, value)
    head = copy.deepcopy(chapter.xpath('//*[local-name()="head"]')[0])
    titles = head.xpath('.//*[local-name()="title"]')
    if titles:
        titles[0].text = "Provenans, hak, dan perubahan"
    new_root.append(head)
    body = etree.SubElement(new_root, f"{{{XHTML_NS}}}body")
    body.append(section)
    trees[rights_name] = etree.ElementTree(new_root)
    entries[rights_name] = b""

    for name, tree in trees.items():
        for anchor in tree.xpath('//*[local-name()="a" and @href]'):
            resolved = local_entry_target(name, str(anchor.get("href")))
            if resolved == (chapter_name, "edition-rights"):
                relative = posixpath.relpath(rights_name, posixpath.dirname(name))
                anchor.set("href", f"{relative}#edition-rights")

    ncx = parse_xml(entries["EPUB/toc.ncx"])
    for content in ncx.xpath('//*[local-name()="content" and @src]'):
        if str(content.get("src")) == "text/ch001.xhtml#edition-rights":
            content.set("src", "text/edition_rights.xhtml#edition-rights")
    entries["EPUB/toc.ncx"] = serialize_xml(ncx)


def expand_document_navigation(
    entries: dict[str, bytes], trees: dict[str, etree._ElementTree]
) -> dict[str, int]:
    """Cover every logical source document in EPUB nav and legacy NCX."""

    chapter = trees["EPUB/text/ch001.xhtml"]
    lessons: list[tuple[str, str]] = []
    for ordinal in range(13):
        section_id = f"lesson{ordinal:02d}--document"
        sections = chapter.xpath(f'//*[@id="{section_id}"]')
        if len(sections) != 1:
            raise RuntimeError(f"Expected one logical lesson target {section_id}")
        headings = sections[0].xpath('.//*[local-name()="h1"]')
        if not headings:
            raise RuntimeError(f"Logical lesson target {section_id} has no title")
        label = " ".join("".join(headings[0].itertext()).split())
        lessons.append((f"text/ch001.xhtml#{section_id}", label))

    records: list[dict[str, object]] = [
        {"href": "text/title_page.xhtml", "label": "Halaman judul"},
        {"href": "nav.xhtml#toc", "label": "Daftar isi"},
        {
            "href": "text/ch001.xhtml#index--document",
            "label": "STAT 415 | Pengantar Statistika Matematis",
            "children": [
                {
                    "href": "text/ch001.xhtml#tentang-mata-kuliah-ini",
                    "label": "Tentang mata kuliah ini",
                },
                {
                    "href": "text/ch001.xhtml#pelajaran",
                    "label": "Pelajaran",
                    "children": [
                        {"href": href, "label": label} for href, label in lessons
                    ],
                },
            ],
        },
        {
            "href": "text/edition_rights.xhtml#edition-rights",
            "label": "Provenans, hak, dan perubahan",
        },
    ]

    nav_tree = trees["EPUB/nav.xhtml"]
    old_toc = nav_tree.xpath(
        '//*[local-name()="nav" and @*[local-name()="type"]="toc"]'
    )
    if len(old_toc) != 1:
        raise RuntimeError("Expected one EPUB navigation table of contents")
    new_toc = etree.Element(f"{{{XHTML_NS}}}nav")
    new_toc.set(f"{{{EPUB_NS}}}type", "toc")
    new_toc.set("role", "doc-toc")
    new_toc.set("id", "toc")
    heading = etree.SubElement(new_toc, f"{{{XHTML_NS}}}h1")
    heading.set("id", "toc-title")
    heading.text = "STAT 415: Pengantar Statistika Matematis - edisi Bahasa Indonesia"
    top_list = etree.SubElement(new_toc, f"{{{XHTML_NS}}}ol")
    top_list.set("class", "toc")
    toc_count = 0

    def append_toc_item(parent: etree._Element, record: dict[str, object]) -> None:
        nonlocal toc_count
        toc_count += 1
        item = etree.SubElement(parent, f"{{{XHTML_NS}}}li")
        item.set("id", f"toc-li-{toc_count}")
        anchor = etree.SubElement(item, f"{{{XHTML_NS}}}a")
        anchor.set("href", str(record["href"]))
        anchor.text = str(record["label"])
        children = list(record.get("children", []))
        if children:
            nested = etree.SubElement(item, f"{{{XHTML_NS}}}ol")
            nested.set("class", "toc")
            for child in children:
                append_toc_item(nested, child)

    for record in records:
        append_toc_item(top_list, record)
    old_toc[0].getparent().replace(old_toc[0], new_toc)

    landmarks = nav_tree.xpath(
        '//*[local-name()="nav" and @*[local-name()="type"]="landmarks"]'
    )
    if len(landmarks) != 1:
        raise RuntimeError("Expected one EPUB landmarks navigation")
    for child in list(landmarks[0]):
        landmarks[0].remove(child)
    landmark_list = etree.SubElement(landmarks[0], f"{{{XHTML_NS}}}ol")
    for href, label, epub_type in (
        ("text/title_page.xhtml", "Halaman judul", "titlepage"),
        ("#toc", "Daftar isi", "toc"),
        ("text/ch001.xhtml#index--document", "Isi utama", "bodymatter"),
        (
            "text/edition_rights.xhtml#edition-rights",
            "Provenans, hak, dan perubahan",
            "copyright-page",
        ),
    ):
        item = etree.SubElement(landmark_list, f"{{{XHTML_NS}}}li")
        anchor = etree.SubElement(item, f"{{{XHTML_NS}}}a")
        anchor.set("href", href)
        anchor.set(f"{{{EPUB_NS}}}type", epub_type)
        anchor.text = label

    ncx = parse_xml(entries["EPUB/toc.ncx"])
    nav_maps = ncx.xpath('//*[local-name()="navMap"]')
    if len(nav_maps) != 1:
        raise RuntimeError("Expected one NCX navMap")
    nav_map = nav_maps[0]
    for child in list(nav_map):
        nav_map.remove(child)
    ncx_count = 0

    def append_ncx_item(parent: etree._Element, record: dict[str, object]) -> None:
        nonlocal ncx_count
        ncx_count += 1
        point = etree.SubElement(parent, f"{{{NCX_NS}}}navPoint")
        point.set("id", f"navPoint-{ncx_count - 1}")
        label = etree.SubElement(point, f"{{{NCX_NS}}}navLabel")
        text = etree.SubElement(label, f"{{{NCX_NS}}}text")
        text.text = str(record["label"])
        content = etree.SubElement(point, f"{{{NCX_NS}}}content")
        content.set("src", str(record["href"]))
        for child in list(record.get("children", [])):
            append_ncx_item(point, child)

    for record in records:
        append_ncx_item(nav_map, record)
    depth = ncx.xpath(
        '//*[local-name()="meta" and @name="dtb:depth"]'
    )
    if len(depth) != 1:
        raise RuntimeError("Expected one NCX depth declaration")
    depth[0].set("content", "3")
    entries["EPUB/toc.ncx"] = serialize_xml(ncx)
    return {
        "epub_landmark_links": 4,
        "epub_toc_links": toc_count,
        "lesson_links": len(lessons),
        "ncx_navpoints": ncx_count,
    }


def document_known_source_limitations(tree: etree._ElementTree) -> dict[str, object]:
    """Verify and record inherited hierarchy/table limitations without rewriting."""

    headings = tree.xpath(
        '//*[local-name()="h1" or local-name()="h2" or local-name()="h3" '
        'or local-name()="h4" or local-name()="h5" or local-name()="h6"]'
    )
    skips: list[dict[str, object]] = []
    for previous, current in zip(headings, headings[1:]):
        previous_level = int(etree.QName(previous).localname[1])
        current_level = int(etree.QName(current).localname[1])
        if current_level - previous_level <= 1:
            continue
        ancestors = current.xpath('ancestor::*[@data-book-source-document][1]')
        source_document = (
            str(ancestors[0].get("data-book-source-document"))
            if ancestors
            else "unknown"
        )
        skips.append(
            {
                "from_id": str(previous.get("data-o006-id", "")),
                "from_level": previous_level,
                "source_document": source_document,
                "to_id": str(current.get("data-o006-id", "")),
                "to_level": current_level,
            }
        )
    observed_pairs = tuple((item["from_id"], item["to_id"]) for item in skips)
    if observed_pairs != EXPECTED_HEADING_FORWARD_SKIPS:
        raise RuntimeError("Inherited heading-forward-skip inventory changed")

    table_records: list[dict[str, object]] = []
    for expected in KNOWN_SOURCE_TABLE_LIMITATIONS:
        source_id = str(expected["source_element_id"])
        tables = tree.xpath(
            f'//*[local-name()="table" and @data-o006-id="{source_id}"]'
        )
        if len(tables) != 1:
            raise RuntimeError(f"Expected one historical source table {source_id}")
        table = tables[0]
        observed = {
            "caption_count": len(table.xpath('./*[local-name()="caption"]')),
            "row_count": len(table.xpath('.//*[local-name()="tr"]')),
            "scope_attribute_count": len(table.xpath('.//*[@scope]')),
            "source_element_id": source_id,
            "source_path": expected["source_path"],
            "summary": expected["summary"],
            "table_header_count": len(table.xpath('.//*[local-name()="th"]')),
        }
        if (
            observed["caption_count"] != 0
            or observed["row_count"] != expected["expected_rows"]
            or observed["scope_attribute_count"]
            != expected["expected_scope_attributes"]
            or observed["table_header_count"]
            != expected["expected_table_headers"]
        ):
            raise RuntimeError(f"Historical source table structure changed for {source_id}")
        table_records.append(observed)

    by_document: dict[str, int] = {}
    for item in skips:
        source_document = str(item["source_document"])
        by_document[source_document] = by_document.get(source_document, 0) + 1
    return {
        "heading_hierarchy": {
            "audit": (
                "Adjacent h1-h6 elements in DOM order; forward skip when the next "
                "numeric heading level increases by more than one."
            ),
            "disposition": (
                "Recorded before EPUB-only repair; the id-ID HTML source remains "
                "unchanged, while the rendition normalizes the lesson-card, proof, "
                "solution, definition, and notation headings to h3."
            ),
            "forward_skip_count": len(skips),
            "heading_count": len(headings),
            "per_source_document": dict(sorted(by_document.items())),
            "records": skips,
        },
        "historical_source_tables": table_records,
    }


def validate_xml_surfaces(entries: dict[str, bytes]) -> dict[str, int]:
    parsed: dict[str, etree._ElementTree] = {}
    for name, data in entries.items():
        if name.endswith((".xhtml", ".html", ".svg")):
            parsed[name] = parse_xml(data)

    for name, tree in parsed.items():
        ids = [str(node.get("id")) for node in tree.xpath('//*[@id]')]
        duplicates = sorted({value for value in ids if ids.count(value) > 1})
        if duplicates:
            raise RuntimeError(f"Duplicate XML IDs remain in {name}: {duplicates[:5]}")
        invalid = [value for value in ids if not XML_ID_RE.fullmatch(value)]
        if invalid:
            raise RuntimeError(f"Invalid XML IDs remain in {name}: {invalid[:5]}")
        id_set = set(ids)
        for node in tree.xpath('//*[@aria-describedby or @aria-labelledby]'):
            for attr in ("aria-describedby", "aria-labelledby"):
                if node.get(attr):
                    missing = set(str(node.get(attr)).split()) - id_set
                    if missing:
                        raise RuntimeError(
                            f"Dangling {attr} targets in {name}: {sorted(missing)[:5]}"
                        )
        for node in tree.xpath('//*[@href or @src]'):
            for attr in ("href", "src"):
                value = node.get(attr)
                if not value:
                    continue
                target = local_entry_target(name, str(value))
                if target is None:
                    continue
                target_name, fragment = target
                if target_name not in entries:
                    raise RuntimeError(f"Missing local resource {target_name} from {name}")
                if fragment and target_name in parsed:
                    target_ids = {
                        str(item.get("id"))
                        for item in parsed[target_name].xpath('//*[@id]')
                    }
                    if fragment not in target_ids:
                        raise RuntimeError(
                            f"Missing fragment {fragment} in {target_name} from {name}"
                        )
    return {
        "parsed_xml_surfaces": len(parsed),
        "xhtml_documents": sum(name.endswith(".xhtml") for name in parsed),
    }


def finalize(raw_epub: Path, output: Path, receipt_path: Path) -> None:
    entries = read_epub(raw_epub)
    formulas = collect_formulas(entries)
    rendered = json.loads(RENDER_RECEIPT.read_text(encoding="utf-8"))
    if rendered.get("status") != "passed":
        raise RuntimeError("Math fallback render receipt is not passing")
    rendered_by_key = {str(item["key"]): item for item in rendered["inventory"]}
    if set(rendered_by_key) != {str(item["key"]) for item in formulas}:
        raise RuntimeError("Rendered SVG inventory does not match fallback formulas")

    replacements = 0
    formula_index = 0
    xhtml_trees: dict[str, etree._ElementTree] = {}
    xhtml_repairs: dict[str, int] = {}
    for name in sorted(entries):
        if not name.endswith((".xhtml", ".html")):
            continue
        tree = parse_xml(entries[name])
        nodes = raw_formula_nodes(tree)
        for node in nodes:
            record = formulas[formula_index]
            formula_index += 1
            if record["epub_document"] != name:
                raise RuntimeError("Raw formula document order changed")
            raw = "".join(node.itertext()).strip()
            if sha256_bytes(raw.encode("utf-8")) != record["raw_sha256"]:
                raise RuntimeError("Raw formula identity changed during finalization")
            key = str(record["key"])
            wrapper = etree.Element(f"{{{XHTML_NS}}}span")
            wrapper.set(
                "class",
                "math-fallback "
                + ("math-fallback-display" if record["display"] else "math-fallback-inline"),
            )
            image = etree.SubElement(wrapper, f"{{{XHTML_NS}}}img")
            image.set("src", f"../media/math-{key}.svg")
            image.set("alt", str(record["alt"]))
            image.set("class", "math-fallback-image")
            node.getparent().replace(node, wrapper)
            replacements += 1
        if nodes:
            entries[name] = serialize_xml(tree)
        xhtml_trees[name] = tree
    if replacements != EXPECTED_FALLBACKS or formula_index != EXPECTED_FALLBACKS:
        raise RuntimeError("Not all raw TeX fallbacks were replaced")

    known_source_limitations = document_known_source_limitations(
        xhtml_trees["EPUB/text/ch001.xhtml"]
    )
    for name, tree in xhtml_trees.items():
        repairs = repair_xhtml(tree, name)
        for key, value in repairs.items():
            xhtml_repairs[key] = xhtml_repairs.get(key, 0) + value
    split_rights_document(entries, xhtml_trees)
    navigation = expand_document_navigation(entries, xhtml_trees)
    xhtml_repairs["lightbox_links_rewritten"] = repair_missing_image_links(
        entries, xhtml_trees
    )
    math_reflow_inventory = collect_math_reflow_inventory(xhtml_trees)
    for name, tree in xhtml_trees.items():
        entries[name] = serialize_xml(tree)

    css_bytes = EPUB_CSS.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    entries["EPUB/styles/stylesheet1.css"] = css_bytes

    opf_path = find_opf(entries)
    opf = parse_xml(entries[opf_path])
    manifest = opf.xpath('//*[local-name()="manifest"]')[0]
    for record in formulas:
        key = str(record["key"])
        rendered_item = rendered_by_key[key]
        svg_path = FORMULA_DIR / f"math-{key}.svg"
        svg_bytes = svg_path.read_bytes()
        if len(svg_bytes) != int(rendered_item["bytes"]):
            raise RuntimeError(f"SVG byte count changed for {key}")
        if sha256_bytes(svg_bytes) != rendered_item["sha256"]:
            raise RuntimeError(f"SVG SHA-256 changed for {key}")
        entry_name = f"EPUB/media/math-{key}.svg"
        entries[entry_name] = svg_bytes
        item = etree.SubElement(manifest, f"{{{OPF_NS}}}item")
        item.set("id", f"math_{key}")
        item.set("href", f"media/math-{key}.svg")
        item.set("media-type", "image/svg+xml")
    add_accessibility_metadata(opf)

    rights_item = etree.SubElement(manifest, f"{{{OPF_NS}}}item")
    rights_item.set("id", "edition_rights_xhtml")
    rights_item.set("href", "text/edition_rights.xhtml")
    rights_item.set("media-type", "application/xhtml+xml")
    spine = opf.xpath('//*[local-name()="spine"]')[0]
    rights_ref = etree.SubElement(spine, f"{{{OPF_NS}}}itemref")
    rights_ref.set("idref", "edition_rights_xhtml")
    rights_ref.set("linear", "yes")
    entries[opf_path] = serialize_xml(opf)

    validation = validate_xml_surfaces(entries)

    if entries.get("mimetype") != b"application/epub+zip":
        raise RuntimeError("Invalid EPUB mimetype payload")
    ordered = ["mimetype"] + sorted(name for name in entries if name != "mimetype")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name in ordered:
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits = 0x800
            if name == "mimetype":
                info.compress_type = zipfile.ZIP_STORED
            else:
                info.compress_type = zipfile.ZIP_DEFLATED
                info._compresslevel = 9
            archive.writestr(info, entries[name])
    epub_bytes = buffer.getvalue()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(epub_bytes)

    with zipfile.ZipFile(io.BytesIO(epub_bytes)) as check:
        if check.namelist()[0] != "mimetype":
            raise RuntimeError("EPUB mimetype is not the first ZIP member")
        if check.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            raise RuntimeError("EPUB mimetype is compressed")
        check.testzip()
    receipt = {
        "book_source_sha256": sha256_bytes(
            (ROOT / "build" / "book" / "stat415-id-book.html").read_bytes()
        ),
        "bytes": len(epub_bytes),
        "entries": len(entries),
        "epub_css_sha256": sha256_bytes(css_bytes),
        "image_alt_repairs": list(INDONESIAN_IMAGE_ALT_REPAIRS),
        "known_source_limitations": known_source_limitations,
        "mathml_nodes": sum(
            len(parse_xml(data).xpath('//*[local-name()="math"]'))
            for name, data in entries.items()
            if name.endswith((".xhtml", ".html"))
        ),
        "output": output.relative_to(ROOT).as_posix(),
        "postprocess_script_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "raw_epub": {
            "bytes": raw_epub.stat().st_size,
            "path": raw_epub.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(raw_epub.read_bytes()),
        },
        "raw_tex_remaining": 0,
        "navigation": navigation,
        "rendition_specific_omissions": list(RENDITION_SPECIFIC_OMISSIONS),
        "schema": "o006.stat415.consolidated-epub.v1",
        "sha256": sha256_bytes(epub_bytes),
        "status": "passed",
        "svg_math_fallbacks": replacements,
        "svg_math_fallbacks_with_indonesian_spoken_alternatives": replacements,
        "math_fallback_render_receipt": {
            "bytes": RENDER_RECEIPT.stat().st_size,
            "path": RENDER_RECEIPT.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(RENDER_RECEIPT.read_bytes()),
        },
        "math_reflow": {
            "candidate_count": len(math_reflow_inventory),
            "candidate_inventory": math_reflow_inventory,
            "css_containment_scope": "all .math.display and .math.inline wrappers",
            "focus_rule": {
                "display_min_tex_chars": DISPLAY_MATH_TEX_MIN_CHARS,
                "inline_min_tex_chars": INLINE_MATH_TEX_MIN_CHARS,
                "mtable_max_row_cells_min": MTABLE_MAX_ROW_CELLS_MIN,
                "mtable_max_row_token_chars_min": MTABLE_MAX_ROW_TOKEN_MIN_CHARS,
                "version": "static-width-v1",
            },
        },
        "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        "validation": validation,
        "xhtml_repairs": dict(sorted(xhtml_repairs.items())),
        "zip_timestamp": "1980-01-01T00:00:00",
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_bytes(canonical_json_bytes(receipt))
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "finalize"))
    parser.add_argument("--raw", type=Path, default=RAW_EPUB)
    parser.add_argument("--output", type=Path, default=FINAL_EPUB)
    parser.add_argument("--receipt", type=Path, default=FINAL_RECEIPT)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.raw.resolve())
    else:
        finalize(args.raw.resolve(), args.output.resolve(), args.receipt.resolve())


if __name__ == "__main__":
    main()
