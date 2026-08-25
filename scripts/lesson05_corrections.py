#!/usr/bin/env python3
"""Apply and register every admitted Lesson 05 target-only correction."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson05_source_findings.md"
DOCUMENT_ID = "O006-PSU-006"
FIRST_CORRECTION_ORDINAL = 82
SEEDED_PLOT = ROOT / "source" / "id-ID" / "assets" / "lesson05" / "seeded-z1000.png"
SOURCE_PLOT = (
    ROOT / "authority" / "assets" / "stat415" / "lesson05" / "Lesson05_files"
    / "figure-html" / "unnamed-chunk-28-1.png"
)
SEEDED_PLOT_BYTES = 26_489
SEEDED_PLOT_SHA256 = "10db41ec1a607f9eb38f7ec5af4bf3ce589ffe91497a69fe5ce40f344e8a6974"
SOURCE_PLOT_BYTES = 12_162
SOURCE_PLOT_SHA256 = "322c8262267b94c40ab278c6e1b12ae6392d4fa8c791728c8aeb7fc237ffeed1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_math(main: Tag, short_id: str, expected: str, target: str) -> dict[str, object]:
    target = target.replace(r"\n", "\n")
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson05 correction math identity differs: {math_id}")
    node = nodes[0]
    source = node.get_text()
    if source != expected:
        raise RuntimeError(f"Lesson05 correction math source differs: {math_id}: {source!r}")
    if source == target:
        raise RuntimeError(f"Lesson05 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def replace_unit_text(main: Tag, short_id: str, expected: str, target: str) -> dict[str, object]:
    unit_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-id="{unit_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson05 correction unit identity differs: {unit_id}")
    node = nodes[0]
    source = node.get_text()
    if source != expected:
        raise RuntimeError(f"Lesson05 correction unit source differs: {unit_id}: {source!r}")
    if source == target:
        raise RuntimeError(f"Lesson05 correction makes no unit change: {unit_id}")
    strings = [value for value in node.descendants if isinstance(value, NavigableString)]
    if not strings:
        node.append(NavigableString(target))
    else:
        strings[0].replace_with(NavigableString(target))
        for value in strings[1:]:
            value.replace_with(NavigableString(""))
    if node.get_text() != target:
        raise RuntimeError(f"Lesson05 corrected unit did not materialize: {unit_id}")
    return {
        "surface": "structural-unit-text",
        "unit_id": unit_id,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def segment_surfaces(rows: list[dict[str, str]], short_ids: list[str]) -> list[dict[str, object]]:
    by_id = {row["segment_id"]: row for row in rows}
    surfaces: list[dict[str, object]] = []
    for short_id in short_ids:
        segment_id = f"{DOCUMENT_ID}-{short_id}"
        row = by_id.get(segment_id)
        if row is None:
            raise RuntimeError(f"Lesson05 correction segment missing: {segment_id}")
        source = row["source_text"]
        target = row["target_text"]
        if row["status"] != "translated" or not target.strip():
            raise RuntimeError(f"Lesson05 correction segment unfinished: {segment_id}")
        if sha256(source.encode("utf-8")) != row["source_sha256"]:
            raise RuntimeError(f"Lesson05 correction source binding differs: {segment_id}")
        if source == target:
            raise RuntimeError(f"Lesson05 admitted prose correction is unchanged: {segment_id}")
        surfaces.append({
            "surface": "translation-segment",
            "segment_id": segment_id,
            "source_surface_sha256": row["source_sha256"],
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })
    return surfaces


def record(defect_number: int, surfaces: list[dict[str, object]], note: str) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson05 defect has no target evidence: D{defect_number:03d}")
    return {
        "correction_id": f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}",
        "source_defect_id": f"L05-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


def seeded_plot_surface(main: Tag) -> dict[str, object]:
    source = SOURCE_PLOT.read_bytes()
    target = SEEDED_PLOT.read_bytes()
    if len(source) != SOURCE_PLOT_BYTES or sha256(source) != SOURCE_PLOT_SHA256:
        raise RuntimeError("Lesson05 authority simulation plot differs")
    if len(target) != SEEDED_PLOT_BYTES or sha256(target) != SEEDED_PLOT_SHA256:
        raise RuntimeError("Lesson05 seeded simulation plot differs")
    image = main.select_one('[data-o006-asset-id="O006-PSU-006-A0004"]')
    if image is None or image.get("src") != "Lesson05_files/figure-html/unnamed-chunk-28-1.png":
        raise RuntimeError("Lesson05 simulation image route differs")
    image["src"] = "assets/lesson05/seeded-z1000.png"
    image["data-derivative-seed"] = "4150505"
    return {
        "surface": "asset",
        "asset_id": "O006-PSU-006-A0004",
        "source_path": SOURCE_PLOT.relative_to(ROOT).as_posix(),
        "target_path": SEEDED_PLOT.relative_to(ROOT).as_posix(),
        "source_bytes": len(source),
        "target_bytes": len(target),
        "source_surface_sha256": sha256(source),
        "target_surface_sha256": sha256(target),
        "seed": 4150505,
        "runtime": "R 4.3.0 via webR 0.2.0",
    }


def replace_videos(main: Tag) -> list[dict[str, object]]:
    iframes = main.select('iframe[data-o006-dependency-id="O006-PSU-006-D0001"]')
    if len(iframes) != 2 or len({node.get("src") for node in iframes}) != 1:
        raise RuntimeError("Lesson05 external-video surface differs")
    messages = (
        "Pengganti statis Video 5.1: mulai dari nilai awal, evaluasi fungsi skor h, gambar garis singgung h, lalu gunakan titik potongnya dengan sumbu horizontal sebagai iterasi berikutnya.",
        "Pengganti statis Video 5.2: ulangi pembaruan Newton–Raphson pada fungsi skor hingga perubahan kecil; setelah itu tetap periksa domain dan bahwa akar tersebut memaksimumkan fungsi log-kemungkinan.",
    )
    surfaces: list[dict[str, object]] = []
    for ordinal, (node, message) in enumerate(zip(iframes, messages), start=1):
        source = str(node)
        wrapper = node.parent
        if not isinstance(wrapper, Tag) or "padding-bottom:2 %>% %" not in str(wrapper.get("style")):
            raise RuntimeError("Lesson05 malformed video wrapper differs")
        node.name = "div"
        node.attrs = {
            "class": ["static-video-fallback"],
            "data-o006-dependency-id": "O006-PSU-006-D0001",
            "data-video-occurrence": str(ordinal),
            "role": "note",
        }
        node.clear()
        node.append(NavigableString(message))
        wrapper.attrs.pop("style", None)
        wrapper["class"] = sorted(set([*wrapper.get("class", []), "static-video-container"]))
        target = str(node)
        surfaces.append({
            "surface": "external-dependency",
            "dependency_id": "O006-PSU-006-D0001",
            "occurrence": ordinal,
            "source_surface_sha256": sha256(source.encode("utf-8")),
            "target_surface_sha256": sha256(target.encode("utf-8")),
            "disposition": "external iframe removed; complete static explanation retained",
        })
    return surfaces


def replace_adjacent_text(
    main: Tag,
    parent_unit_id: str,
    child_unit_id: str,
    expected: str,
    target: str,
) -> dict[str, object]:
    parent = main.select_one(f'[data-o006-id="{DOCUMENT_ID}-{parent_unit_id}"]')
    child = main.select_one(f'[data-o006-id="{DOCUMENT_ID}-{child_unit_id}"]')
    if parent is None or child is None or child.parent is not parent:
        raise RuntimeError(f"Lesson05 adjacent-text surface differs: {parent_unit_id}/{child_unit_id}")
    sibling = child.next_sibling
    if not isinstance(sibling, NavigableString) or str(sibling) != expected:
        raise RuntimeError(f"Lesson05 adjacent text differs: {parent_unit_id}")
    source = parent.get_text()
    sibling.replace_with(NavigableString(target))
    rendered = parent.get_text()
    return {
        "surface": "structural-unit-text",
        "unit_id": f"{DOCUMENT_ID}-{parent_unit_id}",
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(rendered.encode("utf-8")),
    }


def localize_reader_ui(main: Tag) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    comment_targets = {
        "## log base e of e = 1": "## log basis e dari e = 1",
        "## log base e of 10 does NOT = 1": "## log basis e dari 10 TIDAK = 1",
        "## Vectors": "## Vektor",
        "## element-wise operations": "## operasi per elemen",
        "## Subsetting vectors": "## Membuat subset vektor",
        "## logical statements": "## pernyataan logis",
        "## subsetting using logical arguments": "## membuat subset dengan argumen logis",
        "## starting value": "## nilai awal",
        "## first iteration": "## iterasi pertama",
        "## 2nd iteration": "## iterasi ke-2",
        "## 3rd iteration": "## iterasi ke-3",
        "## 4th iteration": "## iterasi ke-4",
        "## 5th iteration": "## iterasi ke-5",
        "## 6th iteration": "## iterasi ke-6",
        "## 7th iteration": "## iterasi ke-7",
        "## 8th iteration": "## iterasi ke-8",
    }
    comments = [node for node in main.select("span.do") if node.get_text()]
    if len(comments) != len(comment_targets) or {node.get_text() for node in comments} != set(comment_targets):
        raise RuntimeError("Lesson05 code-comment localization surface differs")
    for node in comments:
        source = node.get_text()
        target = comment_targets[source]
        parent = node.parent
        anchor = parent.select_one(":scope > a[data-o006-id]") if isinstance(parent, Tag) else None
        if anchor is None:
            raise RuntimeError("Lesson05 code-comment stable anchor is missing")
        node.string = target
        surfaces.append({
            "surface": "code-comment",
            "anchor_unit_id": str(anchor.get("data-o006-id")),
            "source_surface_sha256": sha256(source.encode("utf-8")),
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })

    buttons = main.select('button.code-copy-button[title="Copy to Clipboard"]')
    if len(buttons) != 97:
        raise RuntimeError(f"Lesson05 copy-button title census differs: {len(buttons)}")
    for node in buttons:
        unit_id = str(node.get("data-o006-id") or "")
        source = str(node.get("title"))
        target = "Salin ke papan klip"
        node["title"] = target
        surfaces.append({
            "surface": "ui-attribute",
            "unit_id": unit_id,
            "attribute": "title",
            "source_surface_sha256": sha256(source.encode("utf-8")),
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })

    lightboxes = [
        node for node in main.select("a.lightbox[title]")
        if str(node.get("title", "")).startswith("Fig\u00a0")
    ]
    if len(lightboxes) != 4:
        raise RuntimeError(f"Lesson05 lightbox-title census differs: {len(lightboxes)}")
    for node in lightboxes:
        unit_id = str(node.get("data-o006-id") or "")
        source = str(node.get("title"))
        target = "Gambar" + source[3:]
        node["title"] = target
        surfaces.append({
            "surface": "ui-attribute",
            "unit_id": unit_id,
            "attribute": "title",
            "source_surface_sha256": sha256(source.encode("utf-8")),
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })
    return surfaces


def repair_figure_ids(main: Tag) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for native_id in ("fig-boxplotcornyield", "fig-histogramcornyield", "fig-scattercornyield"):
        nodes = main.select(f'[id="{native_id}"]')
        if len(nodes) != 2 or sorted(node.name for node in nodes) != ["div", "img"]:
            raise RuntimeError(f"Lesson05 duplicate figure ID surface differs: {native_id}")
        image = next(node for node in nodes if node.name == "img")
        image["id"] = native_id + "-image"
        surfaces.append({
            "surface": "dom-id",
            "unit_id": image.get("data-o006-id"),
            "source_value": native_id,
            "target_value": image["id"],
            "source_surface_sha256": sha256(native_id.encode("utf-8")),
            "target_surface_sha256": sha256(str(image["id"]).encode("utf-8")),
        })
    return surfaces


def repair_image_alternatives(main: Tag) -> list[dict[str, object]]:
    alternatives = {
        "O006-PSU-006-A0001": "Dua diagram kotak hasil panen jagung untuk Pupuk X dan Pupuk Y, dengan median dan sebaran kelompok ditampilkan berdampingan.",
        "O006-PSU-006-A0002": "Histogram hasil panen jagung dari seluruh petak percobaan.",
        "O006-PSU-006-A0003": "Diagram pencar hasil panen terhadap nomor petak, dengan titik setiap petak percobaan.",
        "O006-PSU-006-A0004": "Histogram deterministik 1.000 simulasi Eksponensial berlaju 2 dengan seed 4150505; frekuensi terbesar berada dekat nol dan menurun ke kanan.",
        "O006-PSU-006-A0005": "Histogram 15 amatan Eksponensial yang digunakan untuk menduga parameter rataan atau skala theta.",
        "O006-PSU-006-A0006": "Kurva fungsi kemungkinan terhadap theta pada pencarian grid; puncaknya berada dekat theta sama dengan 8,9.",
        "O006-PSU-006-A0007": "Beberapa kurva Normal untuk nilai theta yang berbeda, mengilustrasikan perubahan fungsi objektif saat parameter bergeser.",
        "O006-PSU-006-A0008": "Bingkai Newton–Raphson 1: dari theta 5, garis singgung fungsi skor memotong sumbu pada theta sekitar 6,5183.",
        "O006-PSU-006-A0009": "Bingkai Newton–Raphson 2: pembaruan berikutnya bergerak dari sekitar 6,5183 ke 7,8832.",
        "O006-PSU-006-A0010": "Bingkai Newton–Raphson 3: pembaruan bergerak dari sekitar 7,8832 ke 8,6703, semakin dekat ke akar fungsi skor.",
        "O006-PSU-006-A0011": "Bingkai Newton–Raphson 4: pembaruan bergerak dari sekitar 8,6703 ke 8,8582.",
        "O006-PSU-006-A0012": "Bingkai Newton–Raphson 5: iterasi mencapai sekitar 8,8667 dan garis pembaruan hampir vertikal di dekat akar.",
        "O006-PSU-006-A0013": "Histogram 15 titik data Eksponensial tetap yang digunakan dalam Contoh 5.1.",
        "O006-PSU-006-A0014": "Histogram 30 amatan Normal yang dibangkitkan dengan seed 123, rataan benar minus 3, dan varians benar 16.",
    }
    surfaces: list[dict[str, object]] = []
    for asset_id, target in alternatives.items():
        nodes = main.select(f'[data-o006-asset-id="{asset_id}"]')
        if len(nodes) != 1 or nodes[0].name != "img":
            raise RuntimeError(f"Lesson05 image alternative surface differs: {asset_id}")
        node = nodes[0]
        source = str(node.get("alt") or "")
        node["alt"] = target
        surfaces.append({
            "surface": "image-alternative",
            "asset_id": asset_id,
            "source_surface_sha256": sha256(source.encode("utf-8")),
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })
    return surfaces


def apply_lesson05_corrections(
    main: Tag, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    finding_ids = re.findall(r"^### (L05-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE)
    expected_findings = [f"L05-D{i:03d}" for i in range(1, 32)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson05 admitted finding sequence differs: {finding_ids}")

    records: list[dict[str, object]] = []
    records.append(record(1, segment_surfaces(rows, ["S0078", "S0080", "S0250", "S0251", "S0252"]), "distinguish density, mass, joint density and likelihood"))
    records.append(record(2, segment_surfaces(rows, ["S0087", "S0096", "S0097", "S0098", "S0099", "S0100"]), "align the stored one-value x example and remove ten-observation claims"))

    simulation_surfaces = [
        replace_unit_text(main, "U0648", "rnorm(n=1,mean=3,sd=2)", "set.seed(4150501)\nrnorm(n=1,mean=3,sd=2)"),
        replace_unit_text(main, "U0653", "[1] 4.580174", "[1] 6.688992"),
        replace_unit_text(main, "U0662", "rnorm(n=10,mean=3,sd=2)", "set.seed(4150502)\nrnorm(n=10,mean=3,sd=2)"),
        replace_unit_text(main, "U0667", " [1] 2.6761275 1.8122462 4.9407564 3.5186309 1.7039966 2.8509964 3.2628886\n [8] 2.7733769 0.2348553 3.2150708", " [1] -1.9913396  5.7018791  2.7175272  3.9104060  1.8026764  9.2187028\n [7] -0.2472842  3.3046301  2.2024390 -0.6402799"),
        replace_unit_text(main, "U0674", "x=rnorm(n=1,mean=3,sd=2)\n\nx", "set.seed(4150503)\nx=rnorm(n=1,mean=3,sd=2)\n\nx"),
        replace_unit_text(main, "U0681", "[1] 3.265162", "[1] 3.880108"),
        replace_unit_text(main, "U0719", "[1] 0.1977257", "[1] 0.1810632"),
        replace_unit_text(main, "U0731", "[1] 0.1977257", "[1] 0.1810632"),
        replace_unit_text(main, "U0743", "[1] -1.620875", "[1] -1.708909"),
        replace_unit_text(main, "U0756", "[1] 0.1977257", "[1] 0.1810632"),
        replace_unit_text(main, "U0766", "[1] -1.620875", "[1] -1.708909"),
        replace_unit_text(main, "U0776", "z=rexp(n=30,rate=2)\nz", "set.seed(4150504)\nz=rexp(n=30,rate=2)\nz"),
        replace_unit_text(main, "U0782", " [1] 0.46705460 0.13549008 0.59298057 0.15507703 0.48047756 0.05794372\n [7] 2.49577748 0.16406064 0.06812573 0.86453227 0.20257271 0.75935034\n[13] 0.13467089 0.51720819 0.30552624 0.09729556 0.40618003 0.42356514\n[19] 0.77848292 1.26786815 0.20875659 0.67108327 0.01352500 0.57952264\n[25] 0.05873649 1.74906687 0.34446049 0.01367921 0.17598810 0.16136436", " [1] 0.902386372 0.279482659 0.013538371 0.169541551 0.516750996 0.221434825\n [7] 0.437782802 0.364390418 0.012766121 0.104971642 0.097908754 0.007348964\n[13] 0.041360434 0.224170113 0.924014265 0.368705531 0.009524764 0.690829892\n[19] 0.046744257 0.500347289 0.624012383 0.841702328 0.019394894 0.621367328\n[25] 0.017981748 0.048043481 1.555176392 1.321141629 0.341612630 0.330359658"),
        replace_unit_text(main, "U0794", "[1] 0.4783474", "[1] 0.3884931"),
        replace_unit_text(main, "U0804", "[1] 0.3249934", "[1] 0.3049212"),
        replace_unit_text(main, "U0812", "z=rexp(n=1000,rate=2)", "set.seed(4150505)\nz=rexp(n=1000,rate=2)"),
        replace_unit_text(main, "U0855", "[1] 870", "[1] 856"),
        replace_unit_text(main, "U0866", "[1] 0.87", "[1] 0.856"),
        replace_unit_text(main, "U0879", "[1] 1.137955e-131", "[1] 1.352596e-141"),
        replace_unit_text(main, "U0892", "[1] 1.137955e-131", "[1] 1.352596e-141"),
        seeded_plot_surface(main),
        *segment_surfaces(rows, ["S0083", "S0086", "S0087", "S0108", "S0112", "S0114"]),
    ]
    records.append(record(3, simulation_surfaces, "seed and replay every retained random output and regenerate the 1000-draw histogram"))

    records.append(record(4, [
        apply_math(main, "M0009", r"\(L(X_1,\ldots,X_{10}) = \prod_i f_X(X_i)\)", r"\(L(\mu,\sigma;\mathbf{x})=\prod_{i=1}^{n}f(x_i\mid\mu,\sigma)\)"),
        apply_math(main, "M0010", r"\(l(X_1,\ldots,X_10)=\sum_i log(f_X(X_i))\)", r"\(\ell(\mu,\sigma;\mathbf{x})=\sum_{i=1}^{n}\log f(x_i\mid\mu,\sigma)\)"),
        *segment_surfaces(rows, ["S0096", "S0097", "S0098", "S0099", "S0100", "S0122", "S0123", "S0124"]),
    ], "write likelihood as a parameter function for fixed observations"))

    records.append(record(5, [
        replace_unit_text(main, "U0986", "lik.vals=rep(NA,length(theta.vals))", "lik.vals=rep(NA_real_,length(theta.vals))\nfor(i in seq_along(theta.vals)){\n  lik.vals[i]=lik.exp.2(theta.vals[i],x)\n}"),
        *segment_surfaces(rows, ["S0146", "S0147"]),
    ], "fill the grid-likelihood vector before plotting or maximizing it"))

    records.append(record(6, [
        apply_math(main, "M0026", r"\[\hat{\theta}=\text{argmax}{L(\theta,\mathbf{x})}\]", r"\[\hat{\theta}=\operatorname*{arg\,max}_{\theta>0}L(\theta;\mathbf{x})\]"),
        apply_math(main, "M0032", r"\(\hat{\theta}_{grid}=8.9\)", r"\(\hat{\theta}_{\mathrm{grid}}=8.9,\quad \hat{\theta}_{\mathrm{ML}}=133/15\approx8.866667\)"),
        *segment_surfaces(rows, ["S0149", "S0152", "S0153", "S0216"]),
    ], "distinguish the finite-grid approximation from the analytic MLE"))

    records.append(record(7, [
        apply_math(main, "M0041", r"\(h(\theta)=\frac{d}{d\theta} \ell(\theta)=0\)", r"\(h(\theta)=\frac{d}{d\theta}\ell(\theta)\)"),
        apply_math(main, "M0049", r"\(h(\theta^{(0)}=\frac{d}{d\theta}\ell(\theta^{(0)})\)", r"\(h(\theta^{(0)})=\frac{d}{d\theta}\ell(\theta^{(0)})\)"),
        *segment_surfaces(rows, ["S0172", "S0173", "S0174", "S0175", "S0176", "S0177"]),
    ], "define the score as a function and separately solve for its root"))

    records.append(record(8, segment_surfaces(rows, ["S0178", "S0179", "S0180", "S0182", "S0190", "S0191", "S0192"]), "take Newton tangents to the score and require maximum/domain checks"))
    records.append(record(9, [
        apply_math(main, "M0062", r"\(t=1, 2, \ldots\)", r"\(t=0,1,2,\ldots\)"),
        *segment_surfaces(rows, ["S0194", "S0195", "S0196", "S0197"]),
    ], "start the first Newton update at t=0"))
    records.append(record(10, [
        apply_math(main, "M0065", r"""\[
\ell(\theta)=\log(L(\theta))=\log\left(\prod_{i=1}^n f_X(x_i,\theta)\right)=\sum_{i=1}^n \log f_X(x_i)=\sum_{i=1}^n\left(-\log(\theta) -\frac{ x_i}{\theta}\right)
\]""", r"""\[
\ell(\theta;\mathbf{x})=\sum_{i=1}^{n}\log f(x_i\mid\theta)=\sum_{i=1}^{n}\left[-\log\theta-\frac{x_i}{\theta}\right],\qquad \theta>0
\]"""),
    ], "retain explicit parameter conditioning in the exponential log-likelihood"))
    records.append(record(11, segment_surfaces(rows, ["S0200", "S0201", "S0221", "S0223", "S0338", "S0339"]), "separate Newton-Raphson from the explicitly chosen L-BFGS-B optimizer"))
    records.append(record(12, [
        apply_math(main, "M0085", r"\(x_i\sim Exp(\theta)\)", r"\(x_i\sim\operatorname{Exp}(\text{rate}=1/\theta),\qquad\theta>0\)"),
        *segment_surfaces(rows, ["S0242", "S0243"]),
    ], "treat theta as exponential mean/scale and 1/theta as rate"))

    exponential_domain = [
        replace_unit_text(main, "U1292", "nll.exp=function(theta,x){\n  -sum(dexp(x,rate=1/theta,log=TRUE))\n}", "nll.exp=function(theta,x){\n  if(!is.finite(theta) || theta<=0) return(Inf)\n  -sum(dexp(x,rate=1/theta,log=TRUE))\n}"),
        replace_unit_text(main, "U1308", "out=optim(2,nll.exp,x=x)", 'out=optim(2,nll.exp,x=x,method="L-BFGS-B",lower=.Machine$double.eps)'),
        replace_unit_text(main, "U1377", "out2=optim(0.5,nll.exp,x=x)\nout2", 'out2=optim(0.5,nll.exp,x=x,method="L-BFGS-B",lower=.Machine$double.eps)\nout2'),
        *segment_surfaces(rows, ["S0231", "S0257", "S0258", "S0259", "S0260"]),
    ]
    records.append(record(13, exponential_domain, "enforce the positive exponential domain during optimization"))
    records.append(record(14, segment_surfaces(rows, ["S0279", "S0280", "S0281", "S0282", "S0283", "S0284"]), "diagnose every optimizer warning and repair domain violations"))
    records.append(record(15, [
        replace_unit_text(main, "U1358", "nll.exp(0.112793,x)", "nll.exp(out$par,x)"),
        *segment_surfaces(rows, ["S0288", "S0289"]),
    ], "evaluate the objective at the implemented mean/scale estimate"))
    records.append(record(16, [
        replace_unit_text(main, "U1349", "$par\n[1] 8.865625\n\n$value\n[1] 47.73448\n\n$counts\nfunction gradient \n      30       NA \n\n$convergence\n[1] 0\n\n$message\nNULL", '$par\n[1] 8.866665\n\n$value\n[1] 47.73448\n\n$counts\nfunction gradient \n      12       12 \n\n$convergence\n[1] 0\n\n$message\n[1] "CONVERGENCE: REL_REDUCTION_OF_F <= FACTR*EPSMCH"'),
        *segment_surfaces(rows, ["S0285", "S0286", "S0290"]),
    ], "report objective and numerical-gradient evaluations rather than iterations"))
    records.append(record(17, segment_surfaces(rows, ["S0291", "S0292", "S0293", "S0294", "S0295", "S0299", "S0300", "S0301", "S0302", "S0303", "S0327", "S0328", "S0329"]), "treat convergence code zero as a stopping result, not proof of a valid global optimum"))
    records.append(record(18, [
        replace_unit_text(main, "U1383", "$par\n[1] 8.86875\n\n$value\n[1] 47.73448\n\n$counts\nfunction gradient \n      34       NA \n\n$convergence\n[1] 0\n\n$message\nNULL", '$par\n[1] 8.866664\n\n$value\n[1] 47.73448\n\n$counts\nfunction gradient \n      15       15 \n\n$convergence\n[1] 0\n\n$message\n[1] "CONVERGENCE: REL_REDUCTION_OF_F <= FACTR*EPSMCH"'),
        *segment_surfaces(rows, ["S0296", "S0297", "S0298"]),
    ], "report the two bounded optimizer estimates accurately"))

    records.append(record(19, [
        replace_unit_text(main, "U1433", "nll.norm <- function(theta,y){\n    ## get parameters\n    mu=theta[1]\n    s2=theta[2]\n    ## calculate loglikelihood\n    loglik=sum(dnorm(y,mean=mu,sd=sqrt(s2),log=TRUE))\n    ## return negative loglikelihood\n    -loglik\n}", "nll.norm <- function(theta,y){\n    ## ambil parameter\n    mu=theta[1]\n    s2=theta[2]\n    if(!is.finite(s2) || s2<=0) return(Inf)\n    ## hitung log-kemungkinan\n    loglik=sum(dnorm(y,mean=mu,sd=sqrt(s2),log=TRUE))\n    ## kembalikan negatif log-kemungkinan\n    -loglik\n}"),
        replace_unit_text(main, "U1459", "out=optim(c(-1,1),nll.norm,y=y)\nout", 'out=optim(c(-1,1),nll.norm,y=y,method="L-BFGS-B",\n          lower=c(-Inf,.Machine$double.eps))\nout'),
        replace_unit_text(main, "U1465", "$par\n[1] -3.186135 14.885294\n\n$value\n[1] 83.07392\n\n$counts\nfunction gradient \n      77       NA \n\n$convergence\n[1] 0\n\n$message\nNULL", '$par\n[1] -3.188414 14.885495\n\n$value\n[1] 83.07392\n\n$counts\nfunction gradient \n      17       17 \n\n$convergence\n[1] 0\n\n$message\n[1] "CONVERGENCE: REL_REDUCTION_OF_F <= FACTR*EPSMCH"'),
        apply_math(main, "M0108", r"\(\hat{\sigma^2}_{ML}=14.885\)", r"\(\widehat{\sigma^2}_{\mathrm{ML}}=14.885495\)"),
        *segment_surfaces(rows, ["S0308", "S0323", "S0324", "S0325", "S0326", "S0327", "S0328", "S0329", "S0335"]),
    ], "enforce the positive Normal variance domain and compare against the exact benchmark"))
    records.append(record(20, [
        apply_math(main, "M0106", r"\(\hat{\theta}_{ML}=-3.186\)", r"\(\hat{\mu}_{\mathrm{ML}}=-3.188414\)"),
        *segment_surfaces(rows, ["S0332", "S0333", "S0334"]),
    ], "label the Normal mean estimate with mu"))
    records.append(record(21, segment_surfaces(rows, ["S0004", "S0005", "S0006", "S0007", "S0008", "S0009", "S0010"]), "replace stale Lesson 03 categories with Lesson 05 categories"))
    records.append(record(22, segment_surfaces(rows, ["S0046"]), "use quotation marks for R character values and correct the local cross-reference"))
    records.append(record(23, segment_surfaces(rows, ["S0087"]), "remove the unmatched closing quotation mark"))
    records.append(record(24, segment_surfaces(rows, ["S0160"]), "replace interactively with iteratively"))
    records.append(record(25, segment_surfaces(rows, ["S0180"]), "replace tangent like with tangent line"))
    records.append(record(26, segment_surfaces(rows, ["S0213"]), "state that this example derives and codes derivatives manually"))
    records.append(record(27, [
        replace_unit_text(main, "U1314", "NAME", "nama"),
        replace_unit_text(main, "U1318", "loglikelihood", "log-kemungkinan"),
        replace_unit_text(main, "U1332", "OPTIM", "optim"),
        replace_unit_text(main, "U1336", "OPTIM", "optim"),
        replace_adjacent_text(main, "U1337", "U1338", "menghasilkan keluaran berikut", " menghasilkan keluaran berikut"),
        *segment_surfaces(rows, ["S0285", "S0290"]),
    ], "repair optimizer terminology, adjacent grammar, and the stopping-criterion description"))
    records.append(record(28, replace_videos(main), "remove duplicated third-party iframes and preserve complete static explanations"))
    records.append(record(29, repair_figure_ids(main), "make every native figure DOM ID unique"))
    records.append(record(30, [
        *repair_image_alternatives(main),
        *localize_reader_ui(main),
    ], "provide Indonesian image alternatives and localize reader-control attributes"))
    records.append(record(31, segment_surfaces(rows, ["S0156"]), "replace the exposed internal authoring note with a reader-facing transition"))

    expected_correction_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(82, 113)]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson05 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson05 correction/finding binding differs")
    return records
