#!/usr/bin/env python3
"""Registered target-only repairs and additive offline closure for Lesson 12."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT_ID = "O006-PSU-013"
FIRST_CORRECTION = 219
FINDINGS = ROOT / "working" / "lesson12_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson12_math_audit.md"
ASSET_MANIFEST = ROOT / "authority" / "LESSON12_ASSET_MANIFEST.csv"

CONTROL_IDENTITIES = {
    FINDINGS: (8_203, "8b087fb8e545f14ba323afd1caa5672117d60878c3c5924a0b0455136078109c"),
    MATH_AUDIT: (2_521, "ed14d3e7c210a2c0025ea9eda55f56c2f8da3f23e7b70242d8aa7dd7cf72d14e"),
    ASSET_MANIFEST: (5_007, "47dc68c12a8eedc0a10a0010c7c73346dd2b8a8e4ef5f3ff9d769c24a9764c2a"),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION + number - 1:04d}"


def verify_controls() -> None:
    for path, (size, digest) in CONTROL_IDENTITIES.items():
        payload = path.read_bytes()
        if len(payload) != size or sha256(payload) != digest:
            raise RuntimeError(f"Lesson12 correction control differs: {path.relative_to(ROOT)}")
    text = FINDINGS.read_text("utf-8")
    expected = [f"L12-D{i:03d}" for i in range(1, 25)]
    found = [token.split()[0] for token in text.split("|") if token.strip().startswith("L12-D")]
    if found != expected:
        raise RuntimeError(f"Lesson12 source-finding sequence differs: {found}")


def evidence(surface: str, source: str, target: str, **extra: object) -> dict[str, object]:
    return {
        "surface": surface,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
        **extra,
    }


def segment_evidence(
    number: int,
    nodes: dict[str, NavigableString],
    required: tuple[str, ...],
    forbidden: tuple[str, ...] = (),
) -> dict[str, object]:
    segment_id = f"{DOCUMENT_ID}-S{number:04d}"
    value = str(nodes[segment_id])
    folded = value.casefold()
    if any(token.casefold() not in folded for token in required) or any(token.casefold() in folded for token in forbidden):
        raise RuntimeError(f"Lesson12 target segment evidence differs: {segment_id}")
    return evidence("translation-segment", segment_id, value, segment_id=segment_id)


def replace_segment(
    number: int,
    nodes: dict[str, NavigableString],
    old: str,
    new: str,
) -> dict[str, object]:
    segment_id = f"{DOCUMENT_ID}-S{number:04d}"
    node = nodes[segment_id]
    source = str(node)
    if source.count(old) != 1:
        raise RuntimeError(f"Lesson12 target substring differs: {segment_id}")
    target = source.replace(old, new, 1)
    replacement = NavigableString(target)
    node.replace_with(replacement)
    nodes[segment_id] = replacement
    return evidence("translation-segment", source, target, segment_id=segment_id)


def apply_math(main: Tag, short_id: str, target: str) -> dict[str, object]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson12 math binding differs: {math_id}")
    source = nodes[0].get_text()
    nodes[0].clear()
    nodes[0].append(NavigableString(target))
    return evidence("math", source, target, math_id=math_id)


def anchor(main: Tag, unit_id: str) -> Tag:
    nodes = main.select(f'[data-o006-id="{DOCUMENT_ID}-{unit_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson12 target anchor differs: {unit_id}")
    return nodes[0]


def add_note(main: Tag, number: int, unit_id: str, css: str, text: str) -> dict[str, object]:
    target_anchor = anchor(main, unit_id)
    soup = BeautifulSoup("", "html.parser")
    note = soup.new_tag("aside")
    note["class"] = ["target-only-note", css]
    note["data-o006-correction-id"] = correction_id(number)
    note["role"] = "note"
    note.append(NavigableString(text))
    if target_anchor.name == "li":
        target_anchor.append(note)
    else:
        target_anchor.insert_after(note)
    marker = f"{DOCUMENT_ID}-{unit_id}"
    return evidence("adjacent-correction-note", marker, str(note), unit_id=marker)


def derived_math(soup: BeautifulSoup, cid: str, ordinal: int, tex: str) -> Tag:
    node = soup.new_tag("div")
    node["class"] = ["target-derived-math"]
    node["data-o006-derived-math-id"] = f"{cid}-M{ordinal:02d}"
    node.append(NavigableString(tex))
    return node


def replace_video(main: Tag, number: int, video_ordinal: int) -> dict[str, object]:
    video_id = f"{DOCUMENT_ID}-V{video_ordinal:04d}"
    frames = main.select(f'iframe[data-o006-video-id="{video_id}"]')
    if len(frames) != 1:
        raise RuntimeError(f"Lesson12 video boundary differs: {video_id}")
    frame = frames[0]
    source = str(frame)
    source_url = str(frame.get("src"))
    soup = BeautifulSoup("", "html.parser")
    details = soup.new_tag("details")
    details["class"] = ["offline-video-equivalent"]
    details["data-o006-correction-id"] = correction_id(number)
    details["data-o006-video-id"] = video_id
    details["open"] = ""
    summary = soup.new_tag("summary")
    summary.append(NavigableString(f"Padanan teks luring untuk Video 12.{video_ordinal}"))
    details.append(summary)
    cid = correction_id(number)
    if video_ordinal == 1:
        p = soup.new_tag("p")
        p.append(NavigableString("Mulai dari jumlah kuadrat sisaan pada parameterisasi terpusat. Turunan terhadap intersep memberi persamaan normal pertama."))
        details.append(p)
        details.append(derived_math(soup, cid, 1, r"\[Q(a,b)=\sum_{i=1}^{n}\{y_i-a-b(x_i-\bar{x})\}^2\]"))
        details.append(derived_math(soup, cid, 2, r"\[\frac{\partial Q}{\partial a}=-2\sum_{i=1}^{n}\{y_i-a-b(x_i-\bar{x})\}=0\]"))
        p = soup.new_tag("p")
        p.append(NavigableString("Karena jumlah deviasi prediktor dari rata-ratanya adalah nol, persamaan ini menjadi n(ȳ−a)=0, sehingga a=ȳ."))
        details.append(p)
    elif video_ordinal == 2:
        p = soup.new_tag("p")
        p.append(NavigableString("Substitusikan a=ȳ, lalu turunkan jumlah kuadrat sisaan terhadap b. Persamaan normal kedua dan solusinya adalah:"))
        details.append(p)
        details.append(derived_math(soup, cid, 1, r"\[0=\sum_{i=1}^{n}(x_i-\bar{x})\{(y_i-\bar{y})-b(x_i-\bar{x})\}\]"))
        details.append(derived_math(soup, cid, 2, r"\[b=\frac{\sum_{i=1}^{n}(x_i-\bar{x})(y_i-\bar{y})}{\sum_{i=1}^{n}(x_i-\bar{x})^2},\qquad \hat y_i=\bar y+b(x_i-\bar x)\]"))
        p = soup.new_tag("p")
        p.append(NavigableString("Syarat aljabarnya adalah Sxx>0, yakni nilai prediktor tidak semuanya sama."))
        details.append(p)
    else:
        p = soup.new_tag("p")
        p.append(NavigableString("Untuk prediktor terpusat, rataan bersyarat skor ujian adalah α+β(xᵢ−x̄). Intersep α adalah rataan skor pada xᵢ=x̄, sedangkan β adalah perubahan rataan skor untuk setiap kenaikan satu unit prediktor. Pengamatan individual berbeda dari rataan itu sebesar εᵢ. Garis sampel mengganti α dan β dengan nilai dugaan kuadrat terkecil a dan b."))
        details.append(p)
        details.append(derived_math(soup, cid, 1, r"\[E(Y_i\mid x_i)=\alpha+\beta(x_i-\bar{x}),\qquad Y_i=E(Y_i\mid x_i)+\epsilon_i\]"))
    link_p = soup.new_tag("p")
    link = soup.new_tag("a", href=source_url)
    link["rel"] = "external noopener"
    link.append(NavigableString("Tautan provenance ke rekaman sumber eksternal"))
    link_p.append(link)
    link_p.append(NavigableString("; byte video tidak disalin atau didistribusikan dalam edisi ini."))
    details.append(link_p)
    frame.replace_with(details)
    return evidence("external-video-to-offline-text", source, str(details), video_id=video_id, source_url=source_url, redistributed=False)


def add_theorem_122_proof(main: Tag) -> dict[str, object]:
    target_anchor = anchor(main, "U0387")
    soup = BeautifulSoup("", "html.parser")
    details = soup.new_tag("details")
    details["class"] = ["target-only-proof"]
    details["data-o006-correction-id"] = correction_id(8)
    details["open"] = ""
    summary = soup.new_tag("summary")
    summary.append(NavigableString("Penurunan lengkap Teorema 12.2"))
    details.append(summary)
    p = soup.new_tag("p")
    p.append(NavigableString("Karena jumlah (xᵢ−x̄) adalah nol, pembilang dapat dipusatkan terhadap y tanpa mengubah nilainya. Mengembangkan kedua jumlah terpusat kemudian memberi bentuk komputasi."))
    details.append(p)
    details.append(derived_math(soup, correction_id(8), 1, r"\[\sum_i(x_i-\bar{x})y_i=\sum_i(x_i-\bar{x})(y_i-\bar{y})\]"))
    details.append(derived_math(soup, correction_id(8), 2, r"\[\sum_i(x_i-\bar{x})(y_i-\bar{y})=\sum_i x_i y_i-\frac{1}{n}\Big(\sum_i x_i\Big)\Big(\sum_i y_i\Big)\]"))
    details.append(derived_math(soup, correction_id(8), 3, r"\[\sum_i(x_i-\bar{x})^2=\sum_i x_i^2-\frac{1}{n}\Big(\sum_i x_i\Big)^2\]"))
    p = soup.new_tag("p")
    p.append(NavigableString("Membagi identitas kedua dengan identitas ketiga menghasilkan rumus alternatif yang dinyatakan dalam teorema, dengan syarat Sxx>0."))
    details.append(p)
    target_anchor.insert_after(details)
    return evidence("additive-proof", f"{DOCUMENT_ID}-U0387", str(details), unit_id=f"{DOCUMENT_ID}-U0387")


def repair_tables(main: Tag) -> list[dict[str, object]]:
    captions = (
        "Tabel 12.1 — Galat dan kuadrat galat untuk garis putus-putus pada data tinggi–berat.",
        "Tabel 12.2 — Galat dan kuadrat galat untuk garis utuh pada data tinggi–berat.",
        "Tabel 12.3 — Harga tepung ikan dan hasil tangkapan ikan teri Peru selama 14 tahun.",
        "Tabel 12.4 — Koefisien regresi Minitab untuk contoh ikan teri.",
        "Tabel 12.5 — Ringkasan model regresi Minitab untuk contoh ikan teri.",
        "Tabel 12.6 — Analisis varians regresi Minitab untuk contoh ikan teri.",
    )
    records: list[dict[str, object]] = []
    tables = main.select("table[data-o006-id]")
    if len(tables) != 6:
        raise RuntimeError("Lesson12 table count differs")
    for ordinal, (table, caption_text) in enumerate(zip(tables, captions), start=1):
        source = str(table)
        if table.find("caption") is not None:
            raise RuntimeError(f"Lesson12 table {ordinal} already has a caption")
        soup = BeautifulSoup("", "html.parser")
        caption = soup.new_tag("caption", id=f"lesson12-table-{ordinal}-caption")
        caption.append(NavigableString(caption_text))
        table.insert(0, caption)
        table["aria-describedby"] = caption["id"]
        table["class"] = sorted(set(table.get("class", [])) | {"reader-responsive-table"})
        for col, header in enumerate(table.select("thead th"), start=1):
            header["scope"] = "col"
            header["id"] = f"lesson12-table-{ordinal}-col-{col}"
        if ordinal in {1, 2, 3, 4, 6}:
            for row in table.select("tbody tr"):
                first = row.find("td", recursive=False)
                if first is not None:
                    first.name = "th"
                    first["scope"] = "row"
        records.append(evidence("semantic-table", source, str(table), unit_id=str(table["data-o006-id"]), table_ordinal=ordinal))
    return records


def repair_images(main: Tag, asset_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    alt_by_asset = {
        "O006-PSU-013-A0001": "Diagram pencar suhu Fahrenheit terhadap Celsius; semua titik terletak pada satu garis naik lurus.",
        "O006-PSU-013-A0002": "Diagram pencar mortalitas kanker kulit terhadap garis lintang negara bagian; garis regresi menurun saat garis lintang bertambah.",
        "O006-PSU-013-A0003": "Diagram pencar tinggi dan berat sepuluh mahasiswa dengan dua kandidat garis regresi, utuh dan putus-putus.",
        "O006-PSU-013-A0004": "Skor ujian masuk terhadap IPK sekolah menengah terpusat dengan kelompok respons pada beberapa nilai prediktor.",
        "O006-PSU-013-A0005": "Sampel diagram pencar skor ujian masuk terhadap IPK sekolah menengah terpusat beserta garis kuadrat terkecil.",
        "O006-PSU-013-A0006": "Rataan jam penyiapan proposal meningkat linear terhadap jumlah proposal; kurva normal vertikal menunjukkan variasi respons yang sama.",
        "O006-PSU-013-A0007": "Suhu Fahrenheit terhadap Celsius mengelompok rapat di sekitar garis regresi.",
        "O006-PSU-013-A0008": "Suhu Fahrenheit terhadap Celsius berpencar lebar di sekitar garis regresi.",
        "O006-PSU-013-A0009": "Kurva normal berbentuk lonceng untuk distribusi skor IQ.",
    }
    captions = (
        "Gambar 12.1 — Hubungan deterministik suhu Celsius dan Fahrenheit.",
        "Gambar 12.2 — Hubungan statistis garis lintang dan mortalitas kanker kulit.",
        "Gambar 12.3 — Tinggi dan berat badan dengan dua kandidat garis suaian.",
        "Gambar 12.4 — IPK sekolah menengah terpusat dan skor ujian masuk pada populasi.",
        "Gambar 12.5 — Sampel IPK terpusat dan skor ujian masuk beserta garis suaian.",
        "Gambar 12.6 — Model jumlah jam terhadap jumlah proposal yang disiapkan.",
        "Gambar 12.7 — Pengukuran suhu dengan pencaran kecil di sekitar garis regresi.",
        "Gambar 12.8 — Pengukuran suhu dengan pencaran besar di sekitar garis regresi.",
        "Gambar 12.9 — Distribusi normal skor IQ.",
        "Gambar 12.10 — Banyak populasi respons pada nilai prediktor yang berbeda.",
    )
    frozen = {row["asset_id"]: row for row in asset_rows}
    images = main.select("img[data-o006-asset-id]")
    if len(images) != 10 or set(frozen) != set(alt_by_asset):
        raise RuntimeError("Lesson12 image closure differs")
    records: list[dict[str, object]] = []
    for ordinal, (image, caption_text) in enumerate(zip(images, captions), start=1):
        asset_id = str(image["data-o006-asset-id"])
        row = frozen[asset_id]
        figure = image.find_parent("figure")
        caption = figure.find("figcaption") if figure else None
        if figure is None or caption is None:
            raise RuntimeError(f"Lesson12 image figure boundary differs: {asset_id}")
        source = str(figure)
        image.attrs.pop("style", None)
        image["class"] = sorted(set(image.get("class", [])) | {"reader-responsive-image", "reader-full-width-image"})
        image["width"] = row["width"]
        image["height"] = row["height"]
        image["loading"] = "lazy"
        image["decoding"] = "async"
        image["alt"] = alt_by_asset[asset_id]
        image["src"] = "../../" + row["local_path"]
        image_link = image.find_parent("a")
        if image_link is not None:
            image_link["href"] = image["src"]
            image_link["title"] = caption_text
        figure["class"] = sorted(set(figure.get("class", [])) | {"reader-full-width-figure"})
        caption.clear()
        caption.append(NavigableString(caption_text))
        records.append(evidence("figure-accessibility-layout", source, str(figure), asset_id=asset_id, occurrence=ordinal, target_src=str(image["src"]), width=int(row["width"]), height=int(row["height"])))
    return records


def repair_duplicate_ids(main: Tag) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ids = [str(node["id"]) for node in main.select("[id]")]
    duplicates = {key for key, count in Counter(ids).items() if count > 1}
    expected = {"fig-bidsgraph", "fig-bidsgraph-caption-0ceaefa1-69ba-4598-a22c-09a6ac19f8ca", "fig-iqnormal", "fig-lesson9_1", "fig-scattertemp", "fig-scattertemp2", "fig-skin-cancer"}
    if duplicates != expected:
        raise RuntimeError(f"Lesson12 duplicate native-ID set differs: {duplicates}")
    records: list[dict[str, object]] = []
    mapping: list[dict[str, object]] = []
    for source_id in sorted(duplicates):
        nodes = main.select(f'[id="{source_id}"]')
        for occurrence, node in enumerate(nodes, start=1):
            target_id = f"{source_id}--source-occurrence-{occurrence:02d}"
            reference_updates: list[dict[str, str]] = []
            scope = node.find_parent("figure") or node.parent
            if isinstance(scope, Tag):
                for referrer in scope.select("[aria-describedby], [aria-labelledby]"):
                    for attribute in ("aria-describedby", "aria-labelledby"):
                        if referrer.get(attribute) == source_id:
                            referrer[attribute] = target_id
                            reference_updates.append({
                                "attribute": attribute,
                                "referrer_stable_unit_id": str(referrer.get("data-o006-id") or ""),
                                "target_native_id": target_id,
                            })
            node["data-o006-source-native-id"] = source_id
            node["data-o006-source-native-occurrence"] = str(occurrence)
            node["id"] = target_id
            mapping.append({
                "schema": "o006.stat415.target-native-id-map.v1",
                "document_id": DOCUMENT_ID,
                "source_native_id": source_id,
                "source_occurrence": occurrence,
                "target_native_id": target_id,
                "stable_unit_id": node.get("data-o006-id"),
                "reference_updates": reference_updates,
            })
        records.append(evidence("native-id-occurrence-map", source_id, json.dumps([row for row in mapping if row["source_native_id"] == source_id], ensure_ascii=False, sort_keys=True), source_native_id=source_id, occurrences=len(nodes)))
    if any(count > 1 for count in Counter(str(node["id"]) for node in main.select("[id]")).values()):
        raise RuntimeError("Lesson12 target retains duplicate native IDs")
    live_ids = {str(node["id"]) for node in main.select("[id]")}
    for node in main.select("[aria-describedby], [aria-labelledby]"):
        for attribute in ("aria-describedby", "aria-labelledby"):
            for token in str(node.get(attribute) or "").split():
                if token not in live_ids:
                    raise RuntimeError(f"Lesson12 target has a broken {attribute} reference: {token}")
    return records, mapping


def add_recalculation(main: Tag) -> dict[str, object]:
    target_anchor = anchor(main, "U0813")
    soup = BeautifulSoup("", "html.parser")
    details = soup.new_tag("details")
    details["class"] = ["target-only-reproducibility"]
    details["data-o006-correction-id"] = correction_id(19)
    details["open"] = ""
    summary = soup.new_tag("summary")
    summary.append(NavigableString("Reproduksi terbuka untuk data ikan teri yang ditampilkan"))
    details.append(summary)
    pre = soup.new_tag("pre")
    code = soup.new_tag("code")
    code["class"] = ["language-r"]
    code["data-o006-code-id"] = f"{correction_id(19)}-CODE01"
    code.append(NavigableString(
        "catch <- c(7.23,8.53,9.82,10.26,8.96,12.27,10.28,4.45,1.87,4.00,3.30,4.30,0.80,0.50)\n"
        "price <- c(190,160,134,129,172,197,167,239,542,372,245,376,454,410)\n"
        "fit <- lm(price ~ catch)\n"
        "sxx <- sum((catch - mean(catch))^2)\n"
        "mse <- deviance(fit) / df.residual(fit)\n"
        "tc <- qt(0.975, df.residual(fit))\n"
        "c(slope=coef(fit)[2], Sxx=sxx, MSE=mse, slope_lo=coef(fit)[2]-tc*sqrt(mse/sxx), slope_hi=coef(fit)[2]+tc*sqrt(mse/sxx), intercept_lo=mean(price)-tc*sqrt(mse/length(price)), intercept_hi=mean(price)+tc*sqrt(mse/length(price)))\n"
    ))
    pre.append(code)
    details.append(pre)
    p = soup.new_tag("p")
    p.append(NavigableString("Kontrak keluaran Base R: slope = −29,3948251765; Sxx = 197,5043214286; MSE = 5202,2296650893; selang kemiringan [−40,577002713; −18,212647640]; selang intersep terpusat [228,499866913; 312,500133087]. Perhitungan deterministik ini tidak memakai bilangan acak sehingga seed tidak diperlukan."))
    details.append(p)
    target_anchor.insert_after(details)
    return evidence("reproducible-recalculation", f"{DOCUMENT_ID}-U0813", str(details), code_id=f"{correction_id(19)}-CODE01", runtime="Base R stats")


def record(number: int, surfaces: list[dict[str, object]], note: str, status: str = "applied-target-only") -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson12 correction lacks evidence: D{number:03d}")
    return {
        "schema": "o006.stat415.target-correction.v1",
        "correction_id": correction_id(number),
        "source_defect_id": f"L12-D{number:03d}",
        "document_id": DOCUMENT_ID,
        "status": status,
        "replacement_count": len(surfaces),
        "surfaces": surfaces,
        "note": note,
    }


def apply_lesson12_corrections(
    main: Tag,
    nodes: dict[str, NavigableString],
    asset_rows: list[dict[str, str]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    verify_controls()
    source_units = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    source_math_ids = [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")]
    if source_units != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, 847)] or source_math_ids != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, 353)]:
        raise RuntimeError("Lesson12 stable topology differs before correction")

    records: list[dict[str, object]] = []
    records.append(record(1, [segment_evidence(6, nodes, ("(x)", "(y)"))], "restore predictor and response symbols in the overview"))
    records.append(record(2, [add_note(main, 2, "U0030", "coverage-gap-note", "Batas cakupan sumber: tujuan inferensi untuk koefisien korelasi ρ tidak dipenuhi oleh isi Pelajaran 12. Prosedur tersebut tetap menjadi unit wajib dalam pendamping orisinal C140 dan tidak boleh dianggap tercakup di sini.")], "mark the source's unfulfilled correlation-inference objective", "dispositioned-to-original-companion"))
    records.append(record(3, [segment_evidence(7, nodes, ("kita mungkin tertarik",), ("mungkin mungkin",)), segment_evidence(20, nodes, ("dua jenis",)), segment_evidence(88, nodes, ("misalkan",), ("-misalkan",)), segment_evidence(320, nodes, (") untuk semua",), ("))",))], "repair the four registered mechanical prose defects in translation"))
    records.append(record(4, [
        apply_math(main, "M0056", r"\[\hat{y}_2=-331.2+7.1(64)=123.2 \text{ pounds}\]"),
        apply_math(main, "M0059", r"\[e_2=121-123.2=-2.2\]"),
        apply_math(main, "M0060", r"\[e^2_2=(-2.2)^2=4.84\]"),
    ], "use row 2 consistently and retain the internally consistent fitted value 123.2"))
    records.append(record(5, [segment_evidence(183, nodes, ("rumus", "kemiringan"), ("lorem ipsum",))], "replace the placeholder paragraph with the authorized computational transition"))
    records.append(record(6, [
        replace_segment(214, nodes, "satu-satunya asumsi yang digunakan dalam perhitungan di atas adalah bahwa", "perhitungan aljabar di atas tidak memerlukan asumsi bahwa"),
        replace_segment(216, nodes, "bersifat linear.", "benar-benar linear; keberadaan kemiringan hanya memerlukan Sxx > 0, sedangkan linearitas diperlukan untuk interpretasi model dan inferensi."),
        replace_segment(264, nodes, "Satu-satunya asumsi yang kita buat adalah bahwa", "Untuk menghitung garis kuadrat terkecil, kita tidak perlu mengasumsikan bahwa"),
        replace_segment(266, nodes, "bersifat linear.", "benar-benar linear; syarat aljabarnya adalah Sxx > 0. Model linear diperlukan untuk menafsirkan parameter populasi dan melakukan inferensi."),
    ], "state the actual least-squares algebraic condition and reserve linearity for model inference"))
    records.append(record(7, [replace_video(main, 7, 1), replace_video(main, 7, 2)], "replace the two external-only Theorem 12.1 videos with complete offline derivations while retaining provenance links"))
    records.append(record(8, [add_theorem_122_proof(main)], "supply the omitted centered-parameterization derivation for Theorem 12.2"))
    records.append(record(9, [apply_math(main, "M0136", r"\[Y_i=\alpha+\beta(x_i-\bar{x})+\epsilon_i\]")], "restore the predictor index in the centered model"))
    records.append(record(10, [add_note(main, 10, "U0444", "fixed-design-note", "Kondisi inferensi eksak: nilai x₁,…,xₙ diperlakukan tetap (atau semua pernyataan peluang dikondisikan pada X), Sxx = Σ(xᵢ−x̄)² > 0, suku galat saling bebas dan berdistribusi Normal dengan rataan 0 serta varians bersama σ².")], "state fixed-design and nondegeneracy conditions for the finite-sample laws"))
    records.append(record(11, [apply_math(main, "M0210", r"\[\sum_{i=1}^n\left(Y_i-\alpha-\beta(x_i-\bar{x})\right)^2\]")], "display the residual-sum-of-squares objective minimized by the Gaussian MLE"))
    records.append(record(12, [
        apply_math(main, "M0234", r"\[\dfrac{\partial \log L_{Y_i}(\alpha,\beta,\sigma^2)}{\partial \sigma^2}=-\dfrac{n}{2\sigma^2}-\dfrac{1}{2}\sum (Y_i-\alpha-\beta(x_i-\bar{x}))^2 \cdot \left(- \dfrac{1}{(\sigma^2)^2}\right)\]"),
        apply_math(main, "M0236", r"\[\frac{\partial \log L_{Y_{i}}\left(\alpha, \beta, \sigma^{2}\right)}{\partial \sigma^{2}}=\left[-\frac{n}{2 \sigma^{2}}-\frac{1}{2} \sum\left(Y_{i}-\alpha-\beta\left(x_{i}-\bar{x}\right)\right)^{2} \cdot-\frac{1}{\left(\sigma^{2}\right)^{2}} \stackrel{\operatorname{SET}}{\equiv} 0\right] 2\left(\sigma^{2}\right)^{2}\]"),
    ], "label both variance score derivatives as derivatives of log likelihood"))
    records.append(record(13, [apply_math(main, "M0241", r"\[\hat{\sigma}^2=\dfrac{\sum (Y_i-\hat{\alpha}-\hat{\beta}(x_i-\bar{x}))^2}{n}=\dfrac{\sum(Y_i-\hat{Y}_i)^2}{n}\]")], "use fitted parameter estimates in the substituted residual sum of squares"))
    records.append(record(14, [
        apply_math(main, "M0260", r"\[E(\hat{\alpha})=E(\bar{Y})=\frac{1}{n}\sum E(Y_i)=\frac{1}{n}\sum E(\alpha+\beta(x_i-\bar{x}))=\frac{1}{n}\left[n\alpha+\beta \sum(x_i-\bar{x})\right]=\frac{1}{n}(n\alpha)=\alpha\]"),
        apply_math(main, "M0272", r"\[E(\hat{\beta})=\frac{1}{\sum (x_i-\bar{x})^2}\sum E\left[(x_i-\bar{x})Y_i\right]=\frac{1}{\sum (x_i-\bar{x})^2}\sum (x_i-\bar{x})(\alpha +\beta(x_i-\bar{x}))=\frac{1}{\sum (x_i-\bar{x})^2}\left[ \alpha\sum (x_i-\bar{x}) +\beta \sum (x_i-\bar{x})^2 \right] \\=\beta\]"),
    ], "restore the missing delimiters in both expectation derivations"))
    records.append(record(15, [
        apply_math(main, "M0281", r"\[\sum\limits_{i=1}^n (Y_i-\alpha-\beta(x_i-\bar{x}))^2=n(\hat{\alpha}-\alpha)^2+(\hat{\beta}-\beta)^2\sum\limits_{i=1}^n (x_i-\bar{x})^2+\sum\limits_{i=1}^n (Y_i-\hat{Y}_i)^2\]"),
        apply_math(main, "M0283", r"\[\dfrac{\sum_{i=1}^n (Y_i-\alpha-\beta(x_i-\bar{x}))^2}{\sigma^2}=\dfrac{n(\hat{\alpha}-\alpha)^2}{\sigma^2}+\dfrac{(\hat{\beta}-\beta)^2\sum\limits_{i=1}^n (x_i-\bar{x})^2}{\sigma^2}+\dfrac{\sum (Y_i-\hat{Y}_i)^2}{\sigma^2}\]"),
    ], "restore the observation index on fitted responses inside residual sums"))
    records.append(record(16, [apply_math(main, "M0285", r"\[\underbrace{\color{black}\frac{\sum\left(Y_{i}-\alpha-\beta\left(x_{i}-\bar{x}\right)\right)^{2}}{\sigma^2}}_{\underset{\text{}}{{\color{blue}\chi^2_{(n)}}}}=\underbrace{\color{black}\frac{(\hat{\alpha}-\alpha)^{2}}{\sigma^{2}/n}}_{\underset{\text{}}{{\color{blue}\chi^2_{(1)}}}}+\underbrace{\color{black}\frac{(\hat{\beta}-\beta)^{2}}{\sigma^{2}/\sum\left(x_{i}-\bar{x}\right)^{2}}}_{\underset{\text{}}{{\color{blue}\chi^2_{(1)}}}}+\underbrace{\color{black}\frac{n\hat{\sigma}^{2}}{\sigma^{2}}}_{\underset{\text{ }}{\color{red}\text{?}}}\]")], "use chi rather than Latin x in the three chi-square labels"))
    records.append(record(17, [add_note(main, 17, "U0618", "proof-boundary-note", "Batas rigor: argumen sumber belum membuktikan dekomposisi ortogonal, peringkat ruang proyeksi, atau kebebasan komponen. Bukti matriks lengkap beserta syarat peringkat tetap menjadi unit wajib pendamping rigor orisinal C140; paragraf sumber ini tidak dipromosikan menjadi bukti lengkap.")], "record the unclosed projection/decomposition proof boundary", "dispositioned-to-original-companion"))
    numeric_surfaces = [
        apply_math(main, "M0325", r"\[\sum\limits_{i=1}^n (x_i-\bar{x})^2=197.5043214285714\]"),
        apply_math(main, "M0327", r"\[-29.3948251765 \pm 2.178812829 \sqrt{\dfrac{5202.2296650893}{197.5043214286}}\]"),
        apply_math(main, "M0328", r"\(-29.3948251765 \pm 11.182177536\)"),
        apply_math(main, "M0331", r"\(MSE = 5202.2296650893\)"),
        apply_math(main, "M0333", r"\[270.5 \pm 2.178812829 \sqrt{\dfrac{5202.2296650893}{14}}\]"),
        apply_math(main, "M0334", r"\(270.5 \pm 42.000133087\)"),
        replace_segment(543, nodes, "−40,482 dan −18,322", "−40,5770 dan −18,2126"),
        replace_segment(543, nodes, "18,322 dan 40,482", "18,2126 dan 40,5770"),
        replace_segment(552, nodes, "228,75 dan 312,25", "228,4999 dan 312,5001"),
    ]
    records.append(record(18, numeric_surfaces[:6], "replace all conflicting interval inputs with one recomputation from the displayed 14-row dataset"))
    records.append(record(19, numeric_surfaces[6:] + [add_recalculation(main)], "use the independently recomputed intervals and record a deterministic Base-R witness"))
    records.append(record(20, repair_tables(main), "add Indonesian captions and explicit column and row header scopes to all six tables"))
    duplicate_surfaces, native_mapping = repair_duplicate_ids(main)
    records.append(record(21, duplicate_surfaces, "replace every duplicated native ID with a reversible source-occurrence target mapping"))
    records.append(record(22, repair_images(main, asset_rows) + [add_note(main, 22, "U0048", "asset-rights-note", "Hak komponen gambar: sembilan PNG resmi dibekukan dan didistribusikan kembali di bawah saksi lisensi tingkat laman CC BY-NC 4.0, kecuali jika dinyatakan lain; tidak ada pengecualian aset khusus yang diklaim tanpa bukti terpisah.")], "center and reflow every image occurrence with intrinsic dimensions and substantive Indonesian alternatives"))
    records.append(record(23, [replace_video(main, 23, 3), evidence("external-video-closure", "3 iframe sources", "0 iframe binaries; 3 provenance links and 3 offline equivalents", videos=3, redistributed=False)], "remove all external runtimes and provide accessible offline equivalents while preserving source URLs"))
    records.append(record(24, [add_note(main, 24, "U0838", "mastery-companion-note", "Batas pendamping: sumber ini tidak menyediakan korpus latihan mandiri, diagnostik sisaan, selang rataan-respons/prediksi, regresi berganda, maupun kontrak R/Minitab yang lengkap. Permukaan tersebut tetap wajib dalam pendamping orisinal C140 dan tidak diatribusikan kepada Penn State.")], "record the reproducibility and mastery surfaces reserved for the original companion", "dispositioned-to-original-companion"))

    if [row["correction_id"] for row in records] != [f"O006-PSU-ADV-{i:04d}" for i in range(219, 243)] or [row["source_defect_id"] for row in records] != [f"L12-D{i:03d}" for i in range(1, 25)]:
        raise RuntimeError("Lesson12 correction sequence differs")
    if [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")] != source_units:
        raise RuntimeError("Lesson12 corrections changed stable unit order")
    if [str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")] != source_math_ids:
        raise RuntimeError("Lesson12 corrections changed stable source-math order")
    if main.select("iframe, object, embed, video, audio, source"):
        raise RuntimeError("Lesson12 target retains an external or executable media surface")
    if len(main.select("table caption")) != 6 or len(main.select('table th[scope="col"]')) != 31:
        raise RuntimeError("Lesson12 corrected table semantics differ")
    if len(main.select("img.reader-full-width-image")) != 10 or any(not image.get("width") or not image.get("height") or image.get("style") for image in main.select("img")):
        raise RuntimeError("Lesson12 corrected image semantics differ")
    return records, native_mapping
