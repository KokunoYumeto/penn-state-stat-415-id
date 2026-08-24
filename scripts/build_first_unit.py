#!/usr/bin/env python3
"""Build the complete id-ID landing page and Lesson 00 offline reader."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
NORMALIZED = ROOT / "source" / "normalized" / "en-US"
TARGET = ROOT / "source" / "id-ID"
TRANSLATIONS = TARGET / "first_unit_translation.csv"
SEGMENTS = ROOT / "backend" / "first_unit_segments.jsonl"
CORRECTIONS = ROOT / "backend" / "first_unit_corrections.jsonl"
DOCUMENTS_BACKEND = ROOT / "backend" / "first_unit_documents.jsonl"
ADVERSE = ROOT / "00_control" / "ADVERSE_LEDGER.jsonl"
ASSETS = ROOT / "authority" / "assets" / "stat415" / "assets"
ASSET_MANIFEST = ROOT / "authority" / "FIRST_UNIT_ASSET_MANIFEST.csv"
RUNTIME = ROOT / "authority" / "runtime" / "MathJax-3.1.2"
BUILD = ROOT / "build" / "html-id"
MANIFEST = ROOT / "build" / "FIRST_UNIT_MANIFEST.csv"
RECEIPT = ROOT / "build" / "FIRST_UNIT_BUILD_RECEIPT.json"
CSS = TARGET / "reader.css"
ALT_TEXT = TARGET / "course_card_alt_text.json"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
DOCS = (
    ("index", "index.html", "O006-PSU-000", "https://online.stat.psu.edu/stat415/"),
    ("Lesson00", "Lesson00.html", "O006-PSU-001", "https://online.stat.psu.edu/stat415/Lesson00"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def is_translatable(node: NavigableString) -> bool:
    text = str(node)
    if not text.strip():
        return False
    parent = node.parent
    if parent is None or parent.find_parent(["script", "style", "code"]) is not None or parent.name in {"script", "style", "code"}:
        return False
    if parent.find_parent(class_="math") is not None or "math" in (parent.get("class") or []):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def load_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line]


def load_translations() -> tuple[list[dict[str, object]], dict[str, dict[str, str]]]:
    segments = load_jsonl(SEGMENTS)
    with TRANSLATIONS.open("r", encoding="utf-8", newline="") as stream:
        translations = list(csv.DictReader(stream))
    if len(segments) != 523 or len(translations) != 523:
        raise RuntimeError("first-unit translation boundary is not 523 segments")
    by_document: dict[str, dict[str, str]] = {doc_id: {} for _, _, doc_id, _ in DOCS}
    for segment, row in zip(segments, translations):
        sid = str(segment["segment_id"])
        for key in ("segment_id", "document_id", "component_id", "source_sha256", "source_text"):
            if row[key] != str(segment[key]):
                raise RuntimeError(f"translation/source mismatch: {sid} / {key}")
        if row["status"] != "translated" or not row["target_text"].strip():
            raise RuntimeError(f"unfinished translation row: {sid}")
        by_document[row["document_id"]][sid] = row["target_text"]
    if set(by_document["O006-PSU-000"]) != {f"O006-PSU-000-S{i:04d}" for i in range(1, 78)}:
        raise RuntimeError("landing translation key set differs")
    if set(by_document["O006-PSU-001"]) != {f"O006-PSU-001-S{i:04d}" for i in range(1, 447)}:
        raise RuntimeError("Lesson00 translation key set differs")
    return segments, by_document


def translate_main(filename: str, doc_id: str, translations: dict[str, str]) -> tuple[BeautifulSoup, Tag, dict[str, NavigableString], list[str]]:
    soup = BeautifulSoup((NORMALIZED / filename).read_bytes(), "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError(f"missing normalized main: {filename}")
    source_math = [node.get_text() for node in main.select(".math")]
    nodes = [node for node in main.find_all(string=True) if isinstance(node, NavigableString) and is_translatable(node)]
    expected_ids = list(translations)
    if len(nodes) != len(expected_ids):
        raise RuntimeError(f"translatable node count differs: {filename}")
    target_nodes: dict[str, NavigableString] = {}
    for node, sid in zip(nodes, expected_ids):
        replacement = NavigableString(translations[sid])
        node.replace_with(replacement)
        target_nodes[sid] = replacement
    return soup, main, target_nodes, source_math


def replace_math(main: Tag, selector: str, old: str, new: str, correction_id: str) -> dict[str, object]:
    container = main.select_one(selector)
    if container is None:
        raise RuntimeError(f"correction selector missing: {correction_id} / {selector}")
    matches: list[Tag] = []
    for node in container.select(".math"):
        if old in node.get_text():
            matches.append(node)
    if len(matches) != 1 or matches[0].get_text().count(old) != 1:
        raise RuntimeError(f"correction occurrence differs: {correction_id}")
    node = matches[0]
    before = node.get_text()
    after = before.replace(old, new, 1)
    node.clear()
    node.append(NavigableString(after))
    return {
        "correction_id": correction_id,
        "status": "applied-target-only",
        "surface": "math",
        "selector": selector,
        "source_surface_sha256": sha256(before.encode("utf-8")),
        "target_surface_sha256": sha256(after.encode("utf-8")),
        "replacement_count": 1,
    }


def apply_lesson_corrections(soup: BeautifulSoup, main: Tag, target_nodes: dict[str, NavigableString]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []

    duplicates = main.select("#def-margpmf")
    if len(duplicates) != 2:
        raise RuntimeError("expected exactly two source def-margpmf anchors")
    duplicates[1]["data-source-id"] = "def-margpmf"
    duplicates[1]["id"] = "psu415-l00-def-margpdf"
    records.append({
        "correction_id": "O006-PSU-ADV-0001", "status": "applied-target-only",
        "surface": "html-id", "source_value": "def-margpmf",
        "target_value": "psu415-l00-def-margpdf", "replacement_count": 1,
    })

    records.extend((
        replace_math(main, "#thm-Bayes", r"S=B_1\cup B_2\cup B_2\cup", r"S=B_1\cup B_2\cup B_3\cup", "O006-PSU-ADV-0002"),
        replace_math(main, "#def-jointpmf", r"\sum_{(x,y)\in S}\sum f(x,y)=1", r"\sum_{(x,y)\in S} f(x,y)=1", "O006-PSU-ADV-0003"),
        replace_math(main, "#def-name", r"f(x,y)>0", r"f(x,y)\ge 0", "O006-PSU-ADV-0004"),
        replace_math(main, "#thm-l16", r"c_i\mu,", r"c_i\mu_i,", "O006-PSU-ADV-0005"),
        replace_math(main, "#thm-l17", r"S^2=\frac{1}{n_1}", r"S^2=\frac{1}{n-1}", "O006-PSU-ADV-0006"),
    ))

    hypothesis_replacements = {
        "O006-PSU-001-S0292": (
            " adalah sampel acak dari distribusi Binomial dengan parameter ",
            " adalah peubah-peubah acak yang saling bebas dan masing-masing berdistribusi Binomial dengan parameter ",
        ),
        "O006-PSU-001-S0297": (
            " adalah sampel acak dari distribusi Poisson dengan parameter ",
            " adalah peubah-peubah acak yang saling bebas dan masing-masing berdistribusi Poisson dengan parameter ",
        ),
        "O006-PSU-001-S0307": (
            " adalah sampel acak dari distribusi Gamma dengan parameter ",
            " adalah peubah-peubah acak yang saling bebas dan masing-masing berdistribusi Gamma dengan parameter ",
        ),
    }
    for sid, (old, new) in hypothesis_replacements.items():
        node = target_nodes[sid]
        if str(node) != old:
            raise RuntimeError(f"hypothesis correction input differs: {sid}")
        replacement = NavigableString(new)
        node.replace_with(replacement)
        target_nodes[sid] = replacement
    records.append({
        "correction_id": "O006-PSU-ADV-0007", "status": "applied-target-only",
        "surface": "translated-prose", "segment_ids": sorted(hypothesis_replacements),
        "replacement_count": 3,
    })

    records.extend((
        replace_math(main, "#exm-continuous", r"f(w)=", r"f(x)=", "O006-PSU-ADV-0008"),
        replace_math(main, "#exm-continuous", r"\frac{1}{7}x^3\mid_0^4", r"\frac{1}{7}x^3\mid_0^2", "O006-PSU-ADV-0009"),
    ))

    pmf_target = str(target_nodes["O006-PSU-001-S0398"])
    if "fungsi massa peluang" not in pmf_target or "pmf" not in pmf_target.lower():
        raise RuntimeError("discrete PMF terminology correction was not carried into the target")
    records.append({
        "correction_id": "O006-PSU-ADV-0010", "status": "applied-in-translation",
        "surface": "translated-prose", "segment_ids": ["O006-PSU-001-S0398"],
        "replacement_count": 1, "target_surface_sha256": sha256(pmf_target.encode("utf-8")),
    })

    records.append(replace_math(
        main, "#exm-probility1", r"P(P^\prime|C^\prime)",
        r"P(P^\prime|C^\prime)=0.9", "O006-PSU-ADV-0011",
    ))

    pre = main.select_one("pre[data-o006-id='O006-PSU-001-U0331']")
    if pre is None or pre.get_text().strip() != "Therefore,":
        raise RuntimeError("accidental Therefore code block differs")
    paragraph = soup.new_tag("p")
    paragraph["data-o006-id"] = pre["data-o006-id"]
    paragraph["data-source-tag"] = "pre"
    inner = soup.new_tag("span")
    code = pre.select_one("code[data-o006-id]")
    if code is None:
        raise RuntimeError("accidental code unit ID missing")
    inner["data-o006-id"] = code["data-o006-id"]
    inner["data-source-tag"] = "code"
    inner.string = "Oleh karena itu,"
    paragraph.append(inner)
    pre.replace_with(paragraph)
    records.append({
        "correction_id": "O006-PSU-ADV-0012", "status": "applied-target-only",
        "surface": "html-topology", "source_tag": "pre/code", "target_tag": "p/span",
        "replacement_count": 1,
    })

    comment_target = str(target_nodes["O006-PSU-001-S0422"])
    if "%" in comment_target or "Bayangkan" not in comment_target:
        raise RuntimeError("source-comment marker was not removed in translation")
    records.append({
        "correction_id": "O006-PSU-ADV-0013", "status": "applied-in-translation",
        "surface": "translated-prose", "segment_ids": ["O006-PSU-001-S0422"],
        "replacement_count": 1, "target_surface_sha256": sha256(comment_target.encode("utf-8")),
    })

    table = main.select_one("#exm-cdf table")
    if table is None:
        raise RuntimeError("Example 5 table missing")
    removed_ids: list[str] = []
    for row in table.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if len(cells) != 6 or cells[-1].get_text(strip=True):
            raise RuntimeError("Example 5 empty sixth column differs")
        removed_ids.append(str(cells[-1].get("data-o006-id")))
        cells[-1].decompose()
    records.append({
        "correction_id": "O006-PSU-ADV-0014", "status": "applied-target-only",
        "surface": "html-table", "removed_unit_ids": removed_ids,
        "replacement_count": len(removed_ids),
    })
    return records


def make_solutions_accessible(soup: BeautifulSoup, main: Tag) -> None:
    buttons = list(main.select("button[data-bs-target][aria-controls]"))
    if len(buttons) != 4:
        raise RuntimeError("expected exactly four Bootstrap solution controls")
    for button in buttons:
        source_id = button.get("aria-controls")
        body = main.find(id=source_id)
        if body is None or "collapse" not in (body.get("class") or []):
            raise RuntimeError(f"solution body missing: {source_id}")
        details = soup.new_tag("details")
        details["class"] = ["solution"]
        details["id"] = source_id
        details["data-source-control-id"] = source_id
        details["data-o006-id"] = body.get("data-o006-id")
        summary = soup.new_tag("summary")
        summary["data-o006-id"] = button.get("data-o006-id")
        summary["data-source-tag"] = "button"
        summary.string = "Penyelesaian"
        details.append(summary)
        for child in list(body.contents):
            details.append(child.extract())
        button.replace_with(details)
        body.decompose()


def normalize_chrome(main: Tag, component: str, alt_text: dict[str, str]) -> None:
    for node in main.select("[onclick]"):
        del node["onclick"]
    for node in main.select("[data-bs-toggle], [data-bs-target]"):
        node.attrs.pop("data-bs-toggle", None)
        node.attrs.pop("data-bs-target", None)
    center = main.find("center")
    if center is not None:
        center.name = "div"
        center["class"] = ["action-center"]
    if component == "index":
        images = main.select("img[src]")
        if len(images) != 13:
            raise RuntimeError("landing image count differs")
        for image in images:
            filename = PurePosixPath(image["src"]).name
            if filename not in alt_text:
                raise RuntimeError(f"missing Indonesian alt text: {filename}")
            image["src"] = f"assets/{filename}"
            image["alt"] = alt_text[filename]
            image.attrs.pop("style", None)
        for anchor in main.select("a[href]"):
            match = re.fullmatch(r"\./Lesson(\d\d)\.html", anchor["href"])
            if not match:
                continue
            lesson = match.group(1)
            if lesson == "00":
                anchor["href"] = "Lesson00.html"
            else:
                anchor["href"] = f"https://online.stat.psu.edu/stat415/Lesson{lesson}"
                anchor["class"] = sorted(set(anchor.get("class") or []).union({"pending-source"}))
                anchor["data-translation-status"] = "pending"
                anchor["title"] = "Terjemahan belum tersedia; tautan menuju sumber resmi berbahasa Inggris"
    else:
        breadcrumb = main.select("nav[aria-label='breadcrumb'] a[href]")
        if len(breadcrumb) != 2:
            raise RuntimeError("Lesson00 breadcrumb topology differs")
        breadcrumb[0]["href"] = "index.html#lessons"
        breadcrumb[1]["href"] = "Lesson00.html"
        nav = main.select_one("nav[aria-label='breadcrumb']")
        nav["aria-label"] = "Jejak navigasi"


def page_document(main: Tag, component: str, source_url: str) -> bytes:
    title_node = main.select_one("h1")
    if title_node is None:
        raise RuntimeError(f"missing translated title: {component}")
    title = title_node.get_text(" ", strip=True)
    note = (
        '<aside class="edition-note" aria-label="Status edisi">'
        '<strong>Edisi Bahasa Indonesia — unit pertama.</strong> '
        'Laman utama dan Pelajaran 00 telah diterjemahkan sepenuhnya. '
        'Pelajaran 01–12 masih menuju sumber resmi berbahasa Inggris sampai unit berikutnya selesai. '
        f'<a href="{source_url}">Sumber resmi halaman ini</a>. '
        '<a href="licenses/index.html">Atribusi, perubahan, dan lisensi</a>.'
        '</aside>'
    )
    script = '<script defer src="assets/MathJax/tex-svg.js"></script>\n' if component == "Lesson00" else ""
    html = (
        "<!doctype html>\n"
        '<html lang="id-ID">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{source_url}">\n'
        f'<meta name="translation-provenance" content="{PROVENANCE}">\n'
        '<meta name="edition-status" content="partial: landing and Lesson00 complete of 14 documents">\n'
        '<link rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">\n'
        '<link rel="stylesheet" href="assets/reader.css">\n'
        f"{script}</head>\n<body>\n"
        '<a class="skip-link" href="#quarto-document-content">Lewati ke isi utama</a>\n'
        '<header class="site-header"><div class="site-header__inner">'
        '<div><p class="site-title">STAT 415 — Pengantar Statistika Matematis</p>'
        '<p class="site-subtitle">Rekonstruksi dan terjemahan Bahasa Indonesia · O006/C140</p></div>'
        '<nav class="site-nav" aria-label="Navigasi utama">'
        '<a href="index.html">Daftar pelajaran</a><a href="Lesson00.html">Pelajaran 00</a>'
        '<a href="licenses/index.html">Lisensi</a></nav></div></header>\n'
        f'<div class="page-shell">{note}{str(main)}</div>\n'
        '<footer class="site-footer"><div class="site-footer__inner">'
        'Konten sumber: Departemen Statistika Penn State, CC BY-NC 4.0 kecuali dinyatakan lain. '
        f'Terjemahan dan rekonstruksi: {PROVENANCE}. Tidak ada dukungan atau pengesahan yang tersirat.'
        '</div></footer>\n</body>\n</html>\n'
    )
    return html.encode("utf-8")


def license_page() -> bytes:
    html = f"""<!doctype html>
<html lang="id-ID"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atribusi, perubahan, dan lisensi — STAT 415 Bahasa Indonesia</title>
<link rel="stylesheet" href="../assets/reader.css"></head><body>
<a class="skip-link" href="#licence-main">Lewati ke isi utama</a>
<header class="site-header"><div class="site-header__inner"><div><p class="site-title">Atribusi dan lisensi komponen</p>
<p class="site-subtitle">STAT 415 — edisi Bahasa Indonesia</p></div><nav class="site-nav" aria-label="Navigasi utama"><a href="../index.html">Daftar pelajaran</a><a href="../Lesson00.html">Pelajaran 00</a></nav></div></header>
<div class="page-shell"><main id="licence-main"><h1>Atribusi, perubahan, dan lisensi</h1>
<h2>Konten Penn State</h2><p>Catatan mata kuliah resmi dirancang dan dikembangkan oleh <a href="https://science.psu.edu/stat">Departemen Statistika Penn State</a>. Menurut halaman sumber, kontennya tersedia di bawah <a rel="license" href="https://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0)</a>, kecuali dinyatakan lain.</p>
<p>Edisi ini merupakan terjemahan dan rekonstruksi tidak resmi. Perubahan meliputi penerjemahan ke id-ID, sumber HTML semantik yang dinormalisasi, identitas mesin tambahan, gaya pembaca lokal, penggantian kontrol Bootstrap dengan elemen HTML aksesibel, teks alternatif gambar, serta empat belas koreksi turunan yang dicatat. Byte sumber resmi tidak diubah. Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat.</p>
<p>Sumber resmi: <a href="https://online.stat.psu.edu/stat415/">STAT 415</a>. Status edisi saat ini: laman utama dan Pelajaran 00 lengkap; Pelajaran 01–12 belum diterjemahkan.</p>
<h2>MathJax</h2><p>MathJax 3.1.2 digunakan secara lokal untuk merender matematika dan tersedia di bawah Apache License 2.0. <a href="MathJax-3.1.2-LICENSE.txt">Baca teks lisensi yang disertakan</a>.</p>
<h2>Provenans</h2><p>{PROVENANCE}. Seluruh kredit sumber dan kontributor manusia tetap dipertahankan.</p>
</main></div><footer class="site-footer"><div class="site-footer__inner">Koleksi C140 mempertahankan identitas dan lisensi setiap komponen; tidak ada relisensi seragam.</div></footer></body></html>
"""
    return html.encode("utf-8")


def manifest_payload(reader: dict[PurePosixPath, bytes]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=("relative_path", "bytes", "sha256"), lineterminator="\n")
    writer.writeheader()
    for path in sorted(reader, key=lambda value: value.as_posix().casefold()):
        data = reader[path]
        writer.writerow({"relative_path": path.as_posix(), "bytes": len(data), "sha256": sha256(data)})
    return output.getvalue().encode("utf-8")


def compute() -> dict[str, bytes]:
    segments, translations = load_translations()
    adverse = load_jsonl(ADVERSE)
    expected_corrections = {f"O006-PSU-ADV-{i:04d}" for i in range(1, 15)}
    if {row.get("correction_id") for row in adverse} != expected_corrections:
        raise RuntimeError("adverse ledger does not contain the exact fourteen admitted corrections")
    alt_text = json.loads(ALT_TEXT.read_text("utf-8"))
    if not isinstance(alt_text, dict) or len(alt_text) != 13:
        raise RuntimeError("course-card alt-text catalog differs")

    reader: dict[PurePosixPath, bytes] = {}
    target_outputs: dict[str, bytes] = {}
    correction_rows: list[dict[str, object]] = []
    document_rows: list[dict[str, object]] = []
    for component, filename, doc_id, source_url in DOCS:
        document_soup, main, target_nodes, source_math = translate_main(filename, doc_id, translations[doc_id])
        if component == "Lesson00":
            correction_rows.extend(apply_lesson_corrections(document_soup, main, target_nodes))
            make_solutions_accessible(document_soup, main)
        normalize_chrome(main, component, alt_text)
        target_math = [node.get_text() for node in main.select(".math")]
        if len(source_math) != len(target_math):
            raise RuntimeError(f"math-node count differs: {filename}")
        payload = page_document(main, component, source_url)
        reader[PurePosixPath(filename)] = payload
        target_outputs[f"source/id-ID/{filename}"] = payload
        document_rows.append({
            "schema": "o006.stat415.document.v1", "document_id": doc_id,
            "component_id": component, "source_url": source_url,
            "source_path": f"source/normalized/en-US/{filename}",
            "target_path": f"source/id-ID/{filename}", "locale": "id-ID",
            "translation_status": "complete", "math_nodes": len(target_math),
            "source_math_sha256": sha256("\n".join(source_math).encode("utf-8")),
            "target_math_sha256": sha256("\n".join(target_math).encode("utf-8")),
            "target_bytes": len(payload), "target_sha256": sha256(payload),
        })

    if {row["correction_id"] for row in correction_rows} != expected_corrections or len(correction_rows) != 14:
        raise RuntimeError("build did not apply exactly the fourteen admitted corrections")

    css = CSS.read_bytes()
    runtime = (RUNTIME / "tex-svg.js").read_bytes()
    runtime_license = (RUNTIME / "LICENSE.txt").read_bytes()
    if len(runtime) != 1704911 or sha256(runtime) != "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a":
        raise RuntimeError("MathJax runtime differs")
    if len(runtime_license) != 11358 or sha256(runtime_license) != "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30":
        raise RuntimeError("MathJax licence differs")
    reader[PurePosixPath("assets/reader.css")] = css
    reader[PurePosixPath("assets/MathJax/tex-svg.js")] = runtime
    reader[PurePosixPath("licenses/index.html")] = license_page()
    reader[PurePosixPath("licenses/MathJax-3.1.2-LICENSE.txt")] = runtime_license

    with ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        asset_rows = list(csv.DictReader(stream))
    if len(asset_rows) != 13:
        raise RuntimeError("first-unit asset manifest differs")
    for row in asset_rows:
        filename = PurePosixPath(row["relative_path"]).name
        data = (ASSETS / filename).read_bytes()
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            raise RuntimeError(f"first-unit asset differs: {filename}")
        reader[PurePosixPath(f"assets/{filename}")] = data

    manifest = manifest_payload(reader)
    corrections_payload = canonical_jsonl(sorted(correction_rows, key=lambda row: row["correction_id"]))
    documents_payload = canonical_jsonl(document_rows)
    outputs: dict[str, bytes] = dict(target_outputs)
    for path, data in reader.items():
        outputs[f"build/html-id/{path.as_posix()}"] = data
    outputs[CORRECTIONS.relative_to(ROOT).as_posix()] = corrections_payload
    outputs[DOCUMENTS_BACKEND.relative_to(ROOT).as_posix()] = documents_payload
    outputs[MANIFEST.relative_to(ROOT).as_posix()] = manifest

    receipt = {
        "schema": "o006.stat415.first-unit-build.v1", "status": "built",
        "coverage": {"complete_documents": ["index", "Lesson00"], "complete_count": 2, "corpus_document_count": 14, "next_document": "Lesson01"},
        "locale": "id-ID", "translation_provenance": PROVENANCE,
        "translation_segments": len(segments), "structural_units_normalized": 562,
        "math_nodes": {"index": 0, "Lesson00": 331, "total": 331},
        "corrections": {"count": len(correction_rows), "path": CORRECTIONS.relative_to(ROOT).as_posix(), "bytes": len(corrections_payload), "sha256": sha256(corrections_payload)},
        "documents_backend": {"path": DOCUMENTS_BACKEND.relative_to(ROOT).as_posix(), "bytes": len(documents_payload), "sha256": sha256(documents_payload)},
        "reader": {"path": BUILD.relative_to(ROOT).as_posix(), "files": len(reader), "bytes": sum(len(data) for data in reader.values()), "manifest_path": MANIFEST.relative_to(ROOT).as_posix(), "manifest_bytes": len(manifest), "manifest_sha256": sha256(manifest)},
        "rights": {"Penn State content": "CC BY-NC 4.0 except where otherwise noted", "MathJax 3.1.2": "Apache-2.0", "aggregate_uniform_relicense": False},
        "offline": {"external_runtime_requests": 0, "analytics": False, "cookies": False, "local_mathjax": True},
        "target_documents": [{"path": row["target_path"], "bytes": row["target_bytes"], "sha256": row["target_sha256"]} for row in document_rows],
    }
    outputs[RECEIPT.relative_to(ROOT).as_posix()] = canonical_json(receipt)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            atomic_write(ROOT / relative, payload)
        state = "written"
    else:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"first-unit build output differs: {relative}")
        state = "verified"
    receipt = json.loads(outputs[RECEIPT.relative_to(ROOT).as_posix()])
    print(json.dumps({"mode": state, "documents": 2, "segments": 523, "reader_files": receipt["reader"]["files"], "reader_bytes": receipt["reader"]["bytes"], "receipt_sha256": sha256(outputs[RECEIPT.relative_to(ROOT).as_posix()])}, sort_keys=True))


if __name__ == "__main__":
    main()
