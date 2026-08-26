#!/usr/bin/env python3
"""Apply and register the admitted Lesson 11 target-only corrections."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_ID = "O006-PSU-012"
FINDINGS = ROOT / "working" / "lesson11_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson11_math_audit.md"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson11.html"
CATALOGUE = ROOT / "backend" / "lesson11_source_catalogue.jsonl"
ASSET_MANIFEST = ROOT / "authority" / "LESSON11_ASSET_MANIFEST.csv"
FIRST_CORRECTION_ORDINAL = 199

CONTROL_IDENTITIES = {
    FINDINGS: (4_908, "72de17541e6e76d2e28ab64c47b21e0fffd7a46fae2eabb37d11c1e7aabc397f"),
    MATH_AUDIT: (1_228, "5d97555b9526f82c028a231846b61221b5825692b5fbc7f0c14b95f2871202b5"),
    NORMALIZED: (64_019, "5f009b3812125b8d969a2661d99ebebfd2874b660352fe7b23338ccb6b8a9663"),
    CATALOGUE: (417_966, "dd0baf2ed2e8ad4ea1bfd922cb073e830893efce420c71dd844a613f49c8bc48"),
    ASSET_MANIFEST: (434, "a10a6bc2c5ba7738916eeb2ac1cb12d2ed52a77d505e9843190ffa39a726379b"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + number - 1:04d}"


def verify_controls() -> None:
    for path, (size, digest) in CONTROL_IDENTITIES.items():
        payload = path.read_bytes()
        if len(payload) != size or sha256(payload) != digest:
            raise RuntimeError(f"Lesson11 admitted control differs: {path.relative_to(ROOT)}")


def load_catalogue() -> dict[str, dict[str, object]]:
    rows = [json.loads(line) for line in CATALOGUE.read_text("utf-8").splitlines()]
    by_id = {str(row["entity_id"]): row for row in rows}
    document = by_id.get(DOCUMENT_ID)
    if (
        len(by_id) != 884
        or document is None
        or document.get("unit_count") != 264
        or document.get("formula_count") != 264
        or document.get("segment_count") != 354
        or document.get("asset_count") != 1
    ):
        raise RuntimeError("Lesson11 catalogue census differs")
    return by_id


def entry(catalogue: dict[str, dict[str, object]], short_id: str, kind: str) -> tuple[str, dict[str, object]]:
    entity_id = f"{DOCUMENT_ID}-{short_id}"
    row = catalogue.get(entity_id)
    if row is None or row.get("record_type") != kind:
        raise RuntimeError(f"Lesson11 catalogue binding differs: {entity_id}")
    return entity_id, row


def row_for(rows: list[dict[str, str]], catalogue: dict[str, dict[str, object]], short_id: str) -> tuple[str, dict[str, str], dict[str, object]]:
    segment_id, source_record = entry(catalogue, short_id, "segment")
    matches = [row for row in rows if row.get("segment_id") == segment_id]
    if len(matches) != 1:
        raise RuntimeError(f"Lesson11 translated segment differs: {segment_id}")
    row = matches[0]
    if (
        row.get("status") != "translated"
        or not row.get("target_text", "").strip()
        or "\ufffd" in row.get("target_text", "")
        or row.get("source_text") != source_record.get("source_text")
        or row.get("source_sha256") != source_record.get("source_sha256")
    ):
        raise RuntimeError(f"Lesson11 translated binding differs: {segment_id}")
    return segment_id, row, source_record


def find_target_node(main: Tag, source_record: dict[str, object], target: str) -> NavigableString:
    unit_id = str(source_record["parent_unit_id"])
    parents = main.select(f'[data-o006-id="{unit_id}"]')
    if len(parents) != 1:
        raise RuntimeError(f"Lesson11 target parent differs: {unit_id}")
    matches = [node for node in parents[0].find_all(string=True) if str(node) == target]
    if len(matches) != 1:
        raise RuntimeError(f"Lesson11 target text occurrence differs: {unit_id}: {len(matches)}")
    return matches[0]


def replace_segment(
    main: Tag,
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    old: str,
    new: str,
) -> dict[str, object]:
    segment_id, row, source_record = row_for(rows, catalogue, short_id)
    target = row["target_text"]
    if target.count(old) != 1:
        raise RuntimeError(f"Lesson11 correction substring differs: {segment_id}")
    corrected = target.replace(old, new, 1)
    if (target[: len(target) - len(target.lstrip())], target[len(target.rstrip()) :]) != (
        corrected[: len(corrected) - len(corrected.lstrip())],
        corrected[len(corrected.rstrip()) :],
    ):
        raise RuntimeError(f"Lesson11 correction changed boundary whitespace: {segment_id}")
    node = find_target_node(main, source_record, target)
    node.replace_with(NavigableString(corrected))
    return {
        "surface": "translation-segment",
        "segment_id": segment_id,
        "parent_unit_id": source_record["parent_unit_id"],
        "source_surface_sha256": sha256(target.encode("utf-8")),
        "target_surface_sha256": sha256(corrected.encode("utf-8")),
    }


def segment_evidence(
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_ids: tuple[str, ...],
    required: tuple[str, ...] = (),
    forbidden: tuple[str, ...] = (),
) -> dict[str, object]:
    admitted = [row_for(rows, catalogue, short_id) for short_id in short_ids]
    joined = "\n".join(row["target_text"] for _, row, _ in admitted).casefold()
    if any(token.casefold() not in joined for token in required) or any(
        token.casefold() in joined for token in forbidden
    ):
        raise RuntimeError(f"Lesson11 translation evidence differs: {short_ids}")
    return {
        "surface": "translation-segment-group",
        "segment_ids": [segment_id for segment_id, _, _ in admitted],
        "parent_unit_ids": [source["parent_unit_id"] for _, _, source in admitted],
        "source_surface_sha256": sha256("\n".join(row["source_sha256"] for _, row, _ in admitted).encode("utf-8")),
        "target_surface_sha256": sha256("\n".join(row["target_text"] for _, row, _ in admitted).encode("utf-8")),
    }


def apply_math(main: Tag, catalogue: dict[str, dict[str, object]], short_id: str, target: str) -> dict[str, object]:
    math_id, source_record = entry(catalogue, short_id, "math")
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson11 math node differs: {math_id}")
    source = nodes[0].get_text()
    if source != source_record.get("source_text") or sha256(source.encode("utf-8")) != source_record.get("source_sha256"):
        raise RuntimeError(f"Lesson11 math source differs: {math_id}")
    nodes[0].clear()
    nodes[0].append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": source_record["source_sha256"],
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def add_note(main: Tag, catalogue: dict[str, dict[str, object]], number: int, anchor_short: str, css: str, text: str) -> dict[str, object]:
    unit_id, source_record = entry(catalogue, anchor_short, "unit")
    anchors = main.select(f'[data-o006-id="{unit_id}"]')
    if len(anchors) != 1:
        raise RuntimeError(f"Lesson11 note anchor differs: {unit_id}")
    cid = correction_id(number)
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction", css]
    note["data-o006-correction-id"] = cid
    note["role"] = "note"
    note.append(NavigableString(text))
    anchors[0].insert_after(note)
    marker = f"{unit_id}\n{source_record['text_sha256']}"
    return {
        "surface": "adjacent-correction-note",
        "unit_id": unit_id,
        "source_surface_sha256": sha256(marker.encode("utf-8")),
        "target_surface_sha256": sha256((marker + "\n" + str(note)).encode("utf-8")),
    }


def add_solution_heading(main: Tag, catalogue: dict[str, dict[str, object]]) -> dict[str, object]:
    unit_id, source_record = entry(catalogue, "U0209", "unit")
    anchors = main.select(f'[data-o006-id="{unit_id}"]')
    if len(anchors) != 1 or main.select("#solusi-contoh-11-6"):
        raise RuntimeError("Lesson11 Example 11.6 solution boundary differs")
    soup = BeautifulSoup("", "html.parser")
    heading = soup.new_tag("h4", id="solusi-contoh-11-6")
    heading["class"] = ["anchored", "target-only-solution-heading"]
    heading["data-o006-correction-id"] = correction_id(11)
    heading.append(NavigableString("Solusi"))
    anchors[0].insert_before(heading)
    marker = f"{unit_id}\n{source_record['text_sha256']}"
    return {
        "surface": "additive-solution-heading",
        "unit_id": unit_id,
        "source_surface_sha256": sha256(marker.encode("utf-8")),
        "target_surface_sha256": sha256((marker + "\n" + str(heading)).encode("utf-8")),
    }


def repair_table(main: Tag, catalogue: dict[str, dict[str, object]]) -> dict[str, object]:
    table_id, source_record = entry(catalogue, "U0041", "unit")
    tables = main.select(f'table[data-o006-id="{table_id}"]')
    if len(tables) != 1:
        raise RuntimeError("Lesson11 horse table differs")
    table = tables[0]
    source_surface = str(table)
    headers = table.select("thead th")
    body_rows = table.select("tbody tr")
    if len(headers) != 2 or len(body_rows) != 5 or table.find("caption") is not None:
        raise RuntimeError("Lesson11 source table census differs")
    for index, header in enumerate(headers, start=1):
        header["scope"] = "col"
        header["id"] = f"lesson11-horse-col-{index}"
    for row in body_rows:
        first = row.find("td", recursive=False)
        if first is None:
            raise RuntimeError("Lesson11 source row header differs")
        first.name = "th"
        first["scope"] = "row"
    soup = BeautifulSoup("", "html.parser")
    caption = soup.new_tag("caption", id="lesson11-horse-table-caption")
    caption.append(NavigableString("Jumlah taruhan pada tiap kuda sebelum pengurangan 17% untuk pengelola arena."))
    table.insert(0, caption)
    table["aria-describedby"] = caption["id"]
    target_surface = str(table)
    return {
        "surface": "semantic-table",
        "unit_id": table_id,
        "catalogue_text_sha256": source_record["text_sha256"],
        "source_surface_sha256": sha256(source_surface.encode("utf-8")),
        "target_surface_sha256": sha256(target_surface.encode("utf-8")),
    }


def repair_figure(main: Tag, catalogue: dict[str, dict[str, object]]) -> list[dict[str, object]]:
    figure_id, _ = entry(catalogue, "U0018", "unit")
    image_id, _ = entry(catalogue, "U0021", "unit")
    caption_id, _ = entry(catalogue, "U0022", "unit")
    figure = main.select_one(f'figure[data-o006-id="{figure_id}"]')
    image = main.select_one(f'img[data-o006-id="{image_id}"]')
    caption = main.select_one(f'figcaption[data-o006-id="{caption_id}"]')
    if figure is None or image is None or caption is None or image.get("src") != "assets/bayes.png":
        raise RuntimeError("Lesson11 portrait binding differs")
    source_surface = str(figure)
    figure["class"] = sorted(set(figure.get("class", [])) | {"reader-full-width-figure"})
    image.attrs.pop("style", None)
    image["class"] = [name for name in image.get("class", []) if name not in {"float-lg-end", "w-50", "ps-3"}]
    image["class"] = sorted(set(image.get("class", [])) | {"lesson11-portrait", "reader-responsive-image"})
    image["alt"] = "Potret hitam-putih Thomas Bayes dalam bingkai oval, menghadap sedikit ke kiri."
    link = image.find_parent("a")
    if link is not None:
        link["title"] = "Gambar 11.1: Thomas Bayes"
    caption.clear()
    caption.append(NavigableString("Gambar 11.1 — Potret Thomas Bayes, tokoh yang namanya digunakan untuk metode Bayesian."))
    target_surface = str(figure)
    note = add_note(
        main,
        catalogue,
        18,
        "U0018",
        "asset-rights-note",
        "Hak komponen: gambar resmi ini dibekukan byte demi byte dari laman sumber dan dipertahankan di bawah pemberitahuan CC BY-NC 4.0 tingkat laman; tidak ditemukan pengecualian khusus aset.",
    )
    return [
        {
            "surface": "figure-accessibility-layout",
            "unit_id": figure_id,
            "asset_id": f"{DOCUMENT_ID}-A0001",
            "source_surface_sha256": sha256(source_surface.encode("utf-8")),
            "target_surface_sha256": sha256(target_surface.encode("utf-8")),
        },
        note,
    ]


def record(number: int, surfaces: list[dict[str, object]], note: str) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson11 correction lacks evidence: D{number:03d}")
    return {
        "correction_id": correction_id(number),
        "source_defect_id": f"L11-D{number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


def apply_lesson11_corrections(main: Tag, rows: list[dict[str, str]]) -> list[dict[str, object]]:
    verify_controls()
    finding_ids = re.findall(r"\|\s*(L11-D\d{3})\s*\|", FINDINGS.read_text("utf-8"))
    expected_findings = [f"L11-D{i:03d}" for i in range(1, 21)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson11 finding sequence differs: {finding_ids}")
    expected_segments = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, 355)]
    if len(rows) != 354 or [row.get("segment_id") for row in rows] != expected_segments:
        raise RuntimeError("Lesson11 translated segment boundary differs")
    catalogue = load_catalogue()
    stable_units = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    stable_math = [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")]
    if len(stable_units) != 264 or len(stable_math) != 264:
        raise RuntimeError("Lesson11 stable topology differs before correction")

    records: list[dict[str, object]] = []
    records.append(record(1, [replace_segment(main, rows, catalogue, "S0018", "parameter tak diketahui, .", "parameter tak diketahui, θ.")], "restore the missing parameter symbol in Objective 2"))
    records.append(record(2, [
        replace_segment(main, rows, catalogue, "S0032", "menentukan kemungkinan, yakni peluang", "menetapkan peluang subjektif"),
        add_note(main, catalogue, 2, "U0073", "odds-definition-note", "Istilah odds melawan kemenangan A menyatakan rasio P(A tidak menang)/P(A menang) = (1 − P(A))/P(A); pembayaran total berikutnya juga mengembalikan nilai taruhan awal."),
    ], "avoid conflating an event probability with likelihood and define the displayed odds ratio"))
    records.append(record(3, [add_note(main, catalogue, 3, "U0119", "poisson-rounding-note", "Catatan ketelitian: nilai eksak massa Poisson adalah 0,02160403145 untuk λ = 3 dan 0,10444486296 untuk λ = 5; nilai itu memberi peluang posterior P(λ = 3 | X = 7) = 0,32552803889. Angka 0,328 di atas berasal dari massa yang terlebih dahulu dibulatkan menjadi 0,022 dan 0,105.")], "make the rounded-table Poisson update reproducible and explicit"))
    records.append(record(4, [apply_math(main, catalogue, "M0057", r"\[k_1(y)=\int_{\Theta} k(y, \theta)d\theta=\int_{\Theta} g(y|\theta)h(\theta)d\theta\]")], "integrate over the actual parameter space"))
    records.append(record(5, [
        replace_segment(main, rows, catalogue, "S0095", "PDF bersama", "hukum bersama campuran"),
        replace_segment(main, rows, catalogue, "S0119", "PDF bersama", "hukum bersama campuran"),
        replace_segment(main, rows, catalogue, "S0127", "PDF marginal", "fungsi massa peluang marginal"),
        replace_segment(main, rows, catalogue, "S0133", "PDF marginal", "fungsi massa peluang marginal"),
    ], "distinguish discrete mass functions, continuous densities, and mixed joint laws"))
    records.append(record(6, [apply_math(main, catalogue, "M0118", r"\(k_1(y)\)")], "correct the normalizing marginal's argument"))
    records.append(record(7, [apply_math(main, catalogue, "M0134", r"\[\begin{align*}\n  k(p|y)=\frac{\Gamma(5+y)}{\Gamma(4)\Gamma(y+1)}p^{4-1}(1-p)^{(y+1)-1}\n\end{align*}\]")], "correct the Beta(4,y+1) normalizing constant"))
    records.append(record(8, [segment_evidence(rows, catalogue, ("S0042", "S0057", "S0211", "S0215"), required=("pengelola arena", "selang waktu", "bernoulli", "posterior"), forbidden=("bernouli", "posteriour"))], "repair the admitted mechanical prose defects in translation"))
    records.append(record(9, [replace_segment(main, rows, catalogue, "S0219", "mencari distribusi bersama", "membentuk kernel bersama")], "identify h(theta)L(theta) as the joint/posterior kernel rather than the normalized posterior"))
    records.append(record(10, [add_note(main, catalogue, 10, "U0202", "loss-regularity-note", "Catatan keputusan: rataan posterior meminimumkan kerugian posterior harapan untuk galat kuadrat jika momen kedua yang diperlukan hingga; untuk galat absolut, setiap median posterior merupakan peminimum, dan peminimum tidak harus tunggal.")], "state the moment condition and median nonuniqueness for Bayes loss minimizers"))
    records.append(record(11, [add_solution_heading(main, catalogue)], "restore a semantic solution heading for Example 11.6"))
    records.append(record(12, [segment_evidence(rows, catalogue, ("S0270", "S0272"), required=("posterior", "beta"), forbidden=("bets",))], "restore beta in the Example 11.6 posterior description"))
    records.append(record(13, [
        replace_segment(main, rows, catalogue, "S0288", "parameter yang diketahui", "parameter yang tetap tetapi tidak diketahui"),
        replace_segment(main, rows, catalogue, "S0293", "dua nilai dari", "dua batas parameter yang bergantung pada data"),
    ], "describe the frequentist parameter and posterior interval endpoints correctly"))
    records.append(record(14, [replace_segment(main, rows, catalogue, "S0307", "PDF", "PMF")], "identify the discrete geometric law as a probability mass function"))
    records.append(record(15, [apply_math(main, catalogue, "M0253", r"\[0.90=\int_{a(y)}^{b(y)}\frac{\Gamma(8)}{\Gamma(4)\Gamma(4)}p^3(1-p)^3dp=\int_{a(y)}^{b(y)}140p^3(1-p)^3dp\]")], "correct the Beta(4,4) density coefficient"))
    records.append(record(16, [apply_math(main, catalogue, "M0263", r"\(k(\theta|y)=\frac{g(y|\theta)h(\theta)}{k_1(y)}\)")], "restore the omitted prior factor in the posterior formula"))
    records.append(record(17, [repair_table(main, catalogue)], "add caption and explicit column/row header semantics to the horse table"))
    records.append(record(18, repair_figure(main, catalogue), "center and reflow the portrait with substantive Indonesian description and component rights"))
    records.append(record(19, [add_note(main, catalogue, 19, "U0253", "r-runtime-note", "Kontrak reproduksi: kedua perintah memakai fungsi stats::qbeta dalam Base R. Keluaran yang diharapkan adalah 0,2253216 dan 0,7746784 (nilai lebih lengkap 0,2253215840 dan 0,7746784160); tidak ada bilangan acak sehingga seed tidak diperlukan.")], "declare the open Base-R runtime and exact expected outputs"))
    records.append(record(20, [replace_segment(main, rows, catalogue, "S0354", "yang merupakan padanan Bayesian bagi selang kepercayaan", "yang memakai peluang posterior—berbeda dari cakupan pengulangan-sampel pada selang kepercayaan")], "distinguish credible-interval posterior probability from confidence coverage"))

    if [row["correction_id"] for row in records] != [f"O006-PSU-ADV-{i:04d}" for i in range(199, 219)]:
        raise RuntimeError("Lesson11 correction identity sequence differs")
    if [row["source_defect_id"] for row in records] != expected_findings:
        raise RuntimeError("Lesson11 correction/finding sequence differs")
    if [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")] != stable_units:
        raise RuntimeError("Lesson11 corrections changed stable unit order")
    if [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")] != stable_math:
        raise RuntimeError("Lesson11 corrections changed stable math order")
    if len(main.select(".math")) != 264:
        raise RuntimeError("Lesson11 corrected math census differs")
    if any(count > 1 for count in Counter(str(node["id"]) for node in main.select("[id]")).values()):
        raise RuntimeError("Lesson11 target retains duplicate DOM IDs")
    table = main.select_one('[data-o006-id="O006-PSU-012-U0041"]')
    image = main.select_one('[data-o006-id="O006-PSU-012-U0021"]')
    if table is None or len(table.select('th[scope="col"]')) != 2 or len(table.select('th[scope="row"]')) != 5:
        raise RuntimeError("Lesson11 corrected table semantics differ")
    if image is None or image.get("style") or "float-lg-end" in image.get("class", []) or not image.get("alt", "").strip():
        raise RuntimeError("Lesson11 corrected portrait semantics differ")
    return records
