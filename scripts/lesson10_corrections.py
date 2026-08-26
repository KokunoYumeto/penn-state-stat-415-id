#!/usr/bin/env python3
"""Apply and register every admitted Lesson 10 target-only correction."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson10_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson10_math_audit.md"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson10.html"
CATALOGUE = ROOT / "backend" / "lesson10_source_catalogue.jsonl"
ASSET_MANIFEST = ROOT / "authority" / "LESSON10_ASSET_MANIFEST.csv"
DOCUMENT_ID = "O006-PSU-011"
FIRST_CORRECTION_ORDINAL = 171

CONTROL_IDENTITIES = {
    FINDINGS: (11_251, "5c7ec3ed66144b197f1fc9705775d761ae02396a5c11c82e34502077f4593842"),
    MATH_AUDIT: (4_896, "75e97dc5481067c65b663bffa927595eda0cf025b427078e159d51978648a8a7"),
    NORMALIZED: (132_877, "4b9f7c54d9606298dac3772a55f08db39e0494f8960b8ebdcd468ed0ff27c354"),
    CATALOGUE: (761_475, "58efb46b0b4d02afa2f4135258923bb40de5e009bb2be3eeecf0b472a35f7aa3"),
    ASSET_MANIFEST: (7_968, "ac8db64cf192ee43e5ffd6b51d796cbc06fd7eb2d1e20b5acb47379ab666cb2a"),
}


# asset: image unit, first catalogue parent, existing caption unit, target alt, target caption
IMAGE_CONFIG = {
    "A0001": (
        "U0173", "U0172", None,
        "Foto tumpukan batang baja tulangan yang digunakan untuk memperkuat beton dan pasangan batu.",
        "Batang baja tulangan yang menjadi konteks pengukuran kekerasan Brinell pada Contoh 10.4.",
    ),
    "A0002": (
        "U0185", "U0184", "U0186",
        "Kurva Normal untuk rataan sampel ketika μ = 170; batas 172 memisahkan daerah gagal menolak di kiri dari daerah galat tipe I di ekor kanan, yang luasnya 0,1587.",
        "Gambar 10.1 — Di bawah H₀: μ = 170, rataan sampel sekurang-kurangnya 172 berada di daerah penolakan ekor kanan; luasnya adalah α = 0,1587.",
    ),
    "A0003": (
        "U0194", "U0193", "U0195",
        "Kurva Normal baku yang menunjukkan batas Z = 1 dan luas ekor kanan 0,1587 untuk galat tipe I.",
        "Gambar 10.2 — Transformasi batas rataan sampel 172 memberi Z = 1; peluang ekor kanannya adalah 0,1587.",
    ),
    "A0004": (
        "U0207", "U0206", "U0208",
        "Kurva Normal untuk rataan sampel ketika μ = 173; daerah di bawah 172 adalah galat tipe II dengan peluang 0,3085.",
        "Gambar 10.3 — Ketika μ = 173, gagal menolak H₀ terjadi untuk rataan sampel kurang dari 172; luas daerah itu adalah β = 0,3085.",
    ),
    "A0005": (
        "U0214", "U0213", "U0215",
        "Kurva Normal baku yang menunjukkan batas terstandar untuk rataan sampel 172 dan luas galat tipe II 0,3085 ketika μ = 173.",
        "Gambar 10.4 — Setelah standardisasi di bawah μ = 173, peluang berada di bawah batas penolakan 172 adalah 0,3085.",
    ),
    "A0006": (
        "U0223", "U0222", None,
        "Foto sebuah gelas yang terisi kira-kira setengah, sebagai metafora untuk membandingkan galat tipe II dengan kuasa uji.",
        "Metafora gelas setengah kosong atau setengah penuh: kuasa uji adalah komplemen peluang galat tipe II.",
    ),
    "A0007": (
        "U0237", "U0236", "U0238",
        "Kurva Normal untuk rataan sampel ketika μ = 173; daerah sekurang-kurangnya 172 adalah kuasa uji sebesar 0,6915.",
        "Gambar 10.5 — Ketika μ = 173, peluang rataan sampel masuk ke daerah penolakan mulai 172 adalah kuasa 0,6915 = 1 − 0,3085.",
    ),
    "A0008": (
        "U0262", "U0261", "U0263",
        "Kurva Normal baku untuk uji ekor kanan dengan batas Z = 1,645 dan luas ekor α = 0,05.",
        "Gambar 10.6 — Batas Z = 1,645, yang setara dengan rataan sampel 106,58, menentukan daerah penolakan ekor kanan bertaraf 0,05.",
    ),
    "A0009": (
        "U0272", "U0271", "U0273",
        "Kurva Normal ketika μ = 108 dengan batas rataan sampel 106,58; luas di kanan batas adalah kuasa 0,6406.",
        "Gambar 10.7 — Untuk μ = 108, peluang rataan sampel sekurang-kurangnya 106,58 adalah kuasa 0,6406.",
    ),
    "A0010": (
        "U0285", "U0284", "U0286",
        "Kurva Normal ketika μ = 112 dengan batas rataan sampel 106,58; luas di kanan batas adalah kuasa 0,9131.",
        "Gambar 10.8 — Untuk μ = 112, peluang rataan sampel sekurang-kurangnya 106,58 adalah kuasa 0,9131.",
    ),
    "A0011": (
        "U0298", "U0297", "U0299",
        "Kurva Normal ketika μ = 116 dengan batas rataan sampel 106,58; luas di kanan batas adalah kuasa 0,9909.",
        "Gambar 10.9 — Untuk μ = 116, peluang rataan sampel sekurang-kurangnya 106,58 adalah kuasa 0,9909.",
    ),
    "A0012": (
        "U0315", "U0314", "U0316",
        "Grafik fungsi kuasa K(μ) untuk uji ekor kanan; kuasa meningkat ketika μ bergerak ke kanan dari 100.",
        "Gambar 10.10 — Fungsi kuasa K(μ) bagi uji H₀: μ = 100 melawan Hₐ: μ > 100 dengan n = 16 dan α = 0,05.",
    ),
    "A0013": (
        "U0325", "U0324", "U0326",
        "Grafik fungsi kuasa K(μ) yang menandai α pada μ = 100 serta kuasa dan β untuk nilai μ alternatif.",
        "Gambar 10.11 — Pada fungsi kuasa, K(100) = α; untuk μ alternatif, K(μ) adalah kuasa dan β(μ) = 1 − K(μ).",
    ),
    "A0014": (
        "U0347", "U0346", "U0348",
        "Kurva Normal baku untuk uji ekor kanan dengan batas Z = 2,326 dan luas ekor α = 0,01.",
        "Gambar 10.12 — Batas Z = 2,326, atau rataan sampel 109,304, menentukan daerah penolakan ekor kanan bertaraf 0,01.",
    ),
    "A0015": (
        "U0357", "U0356", "U0358",
        "Dua kurva Normal yang membandingkan kuasa pada μ = 108 untuk α = 0,01 dan α = 0,05.",
        "Gambar 10.13 — Pada μ = 108, kuasa adalah 0,3722 untuk α = 0,01 dan 0,6406 untuk α = 0,05.",
    ),
    "A0016": (
        "U0365", "U0364", None,
        "Dua fungsi kuasa K(μ) untuk α = 0,01 dan α = 0,05; kurva dengan α lebih besar memiliki kuasa lebih besar pada μ alternatif.",
        "Perbandingan fungsi kuasa untuk α = 0,01 dan α = 0,05 pada ukuran sampel yang sama.",
    ),
    "A0017": (
        "U0380", "U0379", "U0381",
        "Kurva Normal baku untuk n = 64 dengan batas Z = 1,645, yang setara dengan rataan sampel 103,29.",
        "Gambar 10.14 — Dengan n = 64 dan α = 0,05, daerah penolakan dimulai pada rataan sampel 103,29.",
    ),
    "A0018": (
        "U0416", "U0415", "U0417",
        "Dua fungsi kuasa K(μ) untuk n = 16 dan n = 64; kurva n = 64 lebih tinggi pada nilai μ alternatif.",
        "Gambar 10.15 — Pada α yang sama, memperbesar ukuran sampel dari 16 menjadi 64 meningkatkan kuasa untuk μ > 100.",
    ),
    "A0019": (
        "U0428", "U0427", "U0429",
        "Kurva Normal untuk rataan hasil panen di bawah μ = 40 dengan batas penolakan c di ekor kanan.",
        "Gambar 10.16 — Batas c dipilih agar peluang ekor kanan di bawah H₀: μ = 40 sama dengan taraf yang ditentukan.",
    ),
    "A0020": (
        "U0437", "U0436", "U0438",
        "Dua kurva Normal untuk μ = 40 dan μ = 45 dengan batas bersama c; ekor kanan di bawah μ = 40 mewakili α dan daerah kiri di bawah μ = 45 mewakili β.",
        "Gambar 10.17 — Satu batas c memenuhi sasaran galat tipe I di bawah μ = 40 dan galat tipe II di bawah μ = 45.",
    ),
    "A0021": (
        "U0456", "U0455", "U0457",
        "Kurva Normal hampiran di bawah p = 0,50 dengan batas Z = 2,326 atau p-hat = 0,5367 di ekor kanan.",
        "Gambar 10.18 — Dalam rancangan hampiran, batas p-hat = 0,5367 menentukan daerah penolakan ekor kanan bertarget α = 0,01.",
    ),
    "A0022": (
        "U0465", "U0464", "U0466",
        "Dua kurva Normal hampiran untuk p = 0,50 dan p = 0,55 dengan batas p-hat = 0,5367; daerahnya menunjukkan α dan β.",
        "Gambar 10.19 — Batas p-hat = 0,5367 menghubungkan sasaran hampiran α di bawah p = 0,50 dan β di bawah p = 0,55.",
    ),
}


DUPLICATE_ID_CONFIG = {
    "fig-415_rttailengineer": ("U0181", "U0185"),
    "fig-STAT-415-SEC-5-02": ("U0190", "U0194"),
    "fig-415_engineertype1": ("U0203", "U0207"),
    "fig-415_engineertype1-B": ("U0210", "U0214"),
    "fig-415_engineerpower": ("U0233", "U0237"),
    "fig-rttailcritical": ("U0258", "U0262"),
    "fig-415_IQpower": ("U0268", "U0272"),
    "fig-415_IQpowerB": ("U0281", "U0285"),
    "fig-415_IQpowerC": ("U0294", "U0298"),
    "fig-powerfunofkmu1": ("U0311", "U0315"),
    "fig-powerfunofkmu2": ("U0321", "U0325"),
    "fig-415_IQtypeI": ("U0343", "U0347"),
    "fig-STAT-415-SEC-5-13Version7": ("U0353", "U0357"),
    "fig-415_IQtypeIB": ("U0376", "U0380"),
    "fig-powerfnkmu3": ("U0412", "U0416"),
    "fig-STAT-415-SEC-5-17": ("U0424", "U0428"),
    "fig-alphabeta1": ("U0433", "U0437"),
    "fig-alphacriticalp55": ("U0452", "U0456"),
    "fig-alphabeta3": ("U0461", "U0465"),
}


TABLE_CONFIG = {
    "U0072": "Peluang massa dan peluang ekor atas untuk peubah Poisson dengan parameter 3,2.",
    "U0393": "Kuasa K(μ) untuk n = 16 dan n = 64 pada μ = 108, 112, dan 116.",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(defect_number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}"


def verify_control_identities() -> None:
    for path, (expected_bytes, expected_sha256) in CONTROL_IDENTITIES.items():
        payload = path.read_bytes()
        if len(payload) != expected_bytes or sha256(payload) != expected_sha256:
            raise RuntimeError(f"Lesson10 admitted control differs: {path.relative_to(ROOT)}")


def load_catalogue() -> dict[str, dict[str, object]]:
    records = [json.loads(line) for line in CATALOGUE.read_text("utf-8").splitlines()]
    by_id = {str(row["entity_id"]): row for row in records}
    if len(by_id) != len(records):
        raise RuntimeError("Lesson10 catalogue entity identities are not unique")
    document = by_id.get(DOCUMENT_ID)
    if (
        document is None
        or document.get("record_type") != "document"
        or document.get("unit_count") != 625
        or document.get("formula_count") != 369
        or document.get("segment_count") != 540
        or document.get("asset_count") != 22
        or document.get("duplicate_native_ids") != sorted(DUPLICATE_ID_CONFIG)
    ):
        raise RuntimeError("Lesson10 catalogue document census differs")
    return by_id


def load_asset_manifest() -> dict[str, dict[str, str]]:
    with ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, 23)]
    if [row["asset_id"] for row in rows] != expected:
        raise RuntimeError("Lesson10 asset manifest sequence differs")
    result = {row["asset_id"]: row for row in rows}
    for asset_id, row in result.items():
        path = ROOT / row["local_path"]
        payload = path.read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"Lesson10 authority asset differs: {asset_id}")
    return result


def catalogue_entry(
    catalogue: dict[str, dict[str, object]], short_id: str, record_type: str
) -> tuple[str, dict[str, object]]:
    entity_id = f"{DOCUMENT_ID}-{short_id}"
    row = catalogue.get(entity_id)
    if row is None or row.get("record_type") != record_type or row.get("document_id") != DOCUMENT_ID:
        raise RuntimeError(f"Lesson10 catalogue binding differs: {entity_id}")
    return entity_id, row


def row_for_segment(
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
) -> tuple[str, dict[str, str], dict[str, object]]:
    segment_id = f"{DOCUMENT_ID}-{short_id}"
    matches = [row for row in rows if row["segment_id"] == segment_id]
    if len(matches) != 1:
        raise RuntimeError(f"Lesson10 correction segment identity differs: {segment_id}")
    row = matches[0]
    _, source_record = catalogue_entry(catalogue, short_id, "segment")
    source = row["source_text"]
    target = row["target_text"]
    if (
        row["status"] != "translated"
        or not target.strip()
        or "\ufffd" in target
        or sha256(source.encode("utf-8")) != row["source_sha256"]
        or source_record.get("source_sha256") != row["source_sha256"]
        or source_record.get("source_text") != source
    ):
        raise RuntimeError(f"Lesson10 correction segment binding differs: {segment_id}")
    return segment_id, row, source_record


def segment_group_surface(
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_ids: tuple[str, ...],
    *,
    required_any: tuple[tuple[str, ...], ...] = (),
    forbidden: tuple[str, ...] = (),
) -> dict[str, object]:
    admitted = [row_for_segment(rows, catalogue, short_id) for short_id in short_ids]
    joined = "\n".join(row["target_text"] for _, row, _ in admitted).casefold()
    missing = [group for group in required_any if not any(token.casefold() in joined for token in group)]
    present = [token for token in forbidden if token.casefold() in joined]
    if any(row["source_text"] == row["target_text"] for _, row, _ in admitted) or missing or present:
        raise RuntimeError(
            f"Lesson10 admitted prose correction differs: ids={short_ids} missing={missing} forbidden={present}"
        )
    return {
        "surface": "translation-segment-group",
        "segment_ids": [segment_id for segment_id, _, _ in admitted],
        "parent_unit_ids": [record["parent_unit_id"] for _, _, record in admitted],
        "source_surface_sha256": sha256(
            "\n".join(row["source_sha256"] for _, row, _ in admitted).encode("utf-8")
        ),
        "target_surface_sha256": sha256(
            "\n".join(row["target_text"] for _, row, _ in admitted).encode("utf-8")
        ),
        "translation_layer_changed": True,
    }


def math_node(main: Tag, short_id: str) -> tuple[str, Tag]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson10 correction math identity differs: {math_id}")
    return math_id, nodes[0]


def apply_math(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    target: str,
) -> dict[str, object]:
    math_id, node = math_node(main, short_id)
    _, source_record = catalogue_entry(catalogue, short_id, "math")
    source = node.get_text()
    expected_sha256 = str(source_record["source_sha256"])
    if source_record.get("source_text") != source or sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson10 correction math source differs: {math_id}")
    if source == target:
        raise RuntimeError(f"Lesson10 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def add_note(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    defect_number: int,
    anchor_short: str,
    css_class: str,
    text: str,
) -> dict[str, object]:
    anchor_id, anchor_record = catalogue_entry(catalogue, anchor_short, "unit")
    anchors = main.select(f'[data-o006-id="{anchor_id}"]')
    if len(anchors) != 1:
        raise RuntimeError(f"Lesson10 correction-note anchor differs: {anchor_id}")
    correction = correction_id(defect_number)
    if main.select(f'[data-o006-correction-id="{correction}"]'):
        raise RuntimeError(f"Lesson10 correction note already exists: {correction}")
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction", css_class]
    note["data-o006-correction-id"] = correction
    note["role"] = "note"
    note.append(NavigableString(text))
    anchors[0].insert_after(note)
    source_marker = f"{anchor_id}\n{anchor_record['text_sha256']}"
    return {
        "surface": "adjacent-correction-note",
        "unit_id": anchor_id,
        "catalogue_text_sha256": anchor_record["text_sha256"],
        "source_surface_sha256": sha256(source_marker.encode("utf-8")),
        "target_surface_sha256": sha256((source_marker + "\n" + str(note)).encode("utf-8")),
    }


def repair_duplicate_ids(
    main: Tag, catalogue: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    source_ids = [str(node["id"]) for node in main.select("[id]")]
    duplicates = sorted(name for name, count in Counter(source_ids).items() if count > 1)
    if duplicates != sorted(DUPLICATE_ID_CONFIG):
        raise RuntimeError(f"Lesson10 duplicate native-ID surface differs: {duplicates}")
    surfaces: list[dict[str, object]] = []
    for native_id, (wrapper_short, image_short) in DUPLICATE_ID_CONFIG.items():
        wrapper_id, wrapper_record = catalogue_entry(catalogue, wrapper_short, "unit")
        image_id, image_record = catalogue_entry(catalogue, image_short, "unit")
        wrappers = main.select(f'[data-o006-id="{wrapper_id}"]')
        images = main.select(f'img[data-o006-id="{image_id}"]')
        if (
            len(wrappers) != 1
            or len(images) != 1
            or wrappers[0].get("id") != native_id
            or images[0].get("id") != native_id
            or wrapper_record.get("native_id_occurrence") != 1
            or image_record.get("native_id_occurrence") != 2
        ):
            raise RuntimeError(f"Lesson10 duplicate-ID catalogue binding differs: {native_id}")
        target_id = f"{native_id}-image"
        if main.select(f'#{target_id}'):
            raise RuntimeError(f"Lesson10 target image ID already exists: {target_id}")
        source_marker = f"{wrapper_id}\n{image_id}\n{native_id}\n{native_id}"
        images[0]["id"] = target_id
        images[0]["data-o006-source-native-id"] = native_id
        surfaces.append({
            "surface": "reader-dom-id",
            "wrapper_unit_id": wrapper_id,
            "image_unit_id": image_id,
            "source_native_id": native_id,
            "target_image_id": target_id,
            "source_surface_sha256": sha256(source_marker.encode("utf-8")),
            "target_surface_sha256": sha256(
                f"{wrapper_id}\n{image_id}\n{native_id}\n{target_id}".encode("utf-8")
            ),
        })
    target_ids = [str(node["id"]) for node in main.select("[id]")]
    if any(count > 1 for count in Counter(target_ids).values()):
        raise RuntimeError("Lesson10 reader still contains duplicate DOM IDs")
    return surfaces


def repair_image_accessibility(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    manifest: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for short_asset, config in IMAGE_CONFIG.items():
        image_short, parent_short, caption_short, target_alt, target_caption = config
        asset_id, asset_record = catalogue_entry(catalogue, short_asset, "asset")
        image_id, image_record = catalogue_entry(catalogue, image_short, "unit")
        parent_id, _ = catalogue_entry(catalogue, parent_short, "unit")
        manifest_row = manifest[asset_id]
        images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
        if len(images) != 1:
            raise RuntimeError(f"Lesson10 image identity differs: {asset_id}")
        image = images[0]
        if (
            image.get("data-o006-id") != image_id
            or image.get("src") != asset_record.get("source_ref")
            or asset_record.get("unit_ids") != [image_id]
            or asset_record.get("first_parent_unit_id") != parent_id
            or image_record.get("tag") != "img"
            or image.find_parent(attrs={"data-o006-id": parent_id}) is None
        ):
            raise RuntimeError(f"Lesson10 image/catalogue surface differs: {asset_id}")

        source_alt = image.get("alt") or ""
        source_caption = ""
        caption_id = f"{asset_id.lower()}-caption"
        if caption_short is not None:
            caption_unit_id, caption_record = catalogue_entry(catalogue, caption_short, "unit")
            captions = main.select(f'figcaption[data-o006-id="{caption_unit_id}"]')
            if len(captions) != 1 or caption_record.get("tag") != "figcaption":
                raise RuntimeError(f"Lesson10 figure-caption identity differs: {asset_id}")
            caption = captions[0]
            source_caption = caption.get_text(" ", strip=True)
            caption_id = str(caption.get("id") or caption_id)
            caption.clear()
            caption.append(NavigableString(target_caption))
            caption["id"] = caption_id
            caption["class"] = [
                name for name in caption.get("class", []) if name != "quarto-uncaptioned"
            ]
            caption["data-o006-correction-id"] = correction_id(22)
        else:
            if main.select(f'#{caption_id}'):
                raise RuntimeError(f"Lesson10 target caption already exists: {asset_id}")
            fragment = BeautifulSoup("", "html.parser")
            figure = image.find_parent("figure")
            if figure is None:
                parent = image.find_parent(attrs={"data-o006-id": parent_id})
                if parent is None:
                    raise RuntimeError(f"Lesson10 bare-image parent differs: {asset_id}")
                figure = fragment.new_tag("figure")
                figure["class"] = ["figure", "target-only-figure"]
                parent.wrap(figure)
            caption = fragment.new_tag("figcaption")
            caption["class"] = ["figure-caption"]
            figure.append(caption)
            caption["id"] = caption_id
            caption["data-o006-correction-id"] = correction_id(22)
            caption.append(NavigableString(target_caption))

        image["alt"] = target_alt
        image["aria-describedby"] = caption_id
        lightbox = image.find_parent("a", class_="lightbox")
        if lightbox is not None:
            lightbox["title"] = target_caption
        surfaces.append({
            "surface": "image-alt-caption",
            "asset_id": asset_id,
            "unit_id": image_id,
            "parent_unit_id": parent_id,
            "caption_unit_id": (
                f"{DOCUMENT_ID}-{caption_short}" if caption_short is not None else None
            ),
            "source_ref": asset_record["source_ref"],
            "authority_asset_bytes": int(manifest_row["bytes"]),
            "authority_asset_sha256": manifest_row["sha256"],
            "authority_asset_unchanged": True,
            "source_alt_sha256": sha256(source_alt.encode("utf-8")),
            "target_alt_sha256": sha256(target_alt.encode("utf-8")),
            "source_caption_sha256": sha256(source_caption.encode("utf-8")),
            "target_caption_sha256": sha256(target_caption.encode("utf-8")),
            "caption_id": caption_id,
        })
    return surfaces


def retag(cell: Tag, name: str) -> None:
    if cell.name not in {"td", "th"}:
        raise RuntimeError("Lesson10 table cell tag differs")
    cell.name = name


def repair_tables(
    main: Tag, catalogue: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    expected_geometry = {"U0072": (15, 3), "U0393": (3, 4)}
    for table_index, (short_id, caption_text) in enumerate(TABLE_CONFIG.items(), start=1):
        table_id, table_record = catalogue_entry(catalogue, short_id, "unit")
        tables = main.select(f'table[data-o006-id="{table_id}"]')
        if len(tables) != 1 or table_record.get("tag") != "table":
            raise RuntimeError(f"Lesson10 table identity differs: {table_id}")
        table = tables[0]
        if table.find("caption", recursive=False) is not None:
            raise RuntimeError(f"Lesson10 table unexpectedly has a caption: {table_id}")
        source_html = str(table)
        source_cells = [cell.get_text(" ", strip=True) for cell in table.select("th, td")]
        rows = table.select("tr")
        expected_rows, expected_columns = expected_geometry[short_id]
        if len(rows) != expected_rows or any(
            len(row.find_all(["td", "th"], recursive=False)) != expected_columns for row in rows
        ):
            raise RuntimeError(f"Lesson10 table geometry differs: {table_id}")

        fragment = BeautifulSoup("", "html.parser")
        caption = fragment.new_tag("caption")
        caption_id = f"o006-psu-011-table-{table_index}-caption"
        caption["id"] = caption_id
        caption["data-o006-correction-id"] = correction_id(23)
        caption.append(NavigableString(caption_text))
        table.insert(0, caption)
        table["aria-describedby"] = caption_id

        headers = rows[0].find_all(["td", "th"], recursive=False)
        header_ids: list[str] = []
        for column, cell in enumerate(headers, start=1):
            retag(cell, "th")
            header_id = f"o006-psu-011-table-{table_index}-column-{column}"
            header_ids.append(header_id)
            cell.attrs.update({"id": header_id, "scope": "col"})
        for row_index, row in enumerate(rows[1:], start=1):
            cells = row.find_all(["td", "th"], recursive=False)
            row_header_id = f"o006-psu-011-table-{table_index}-row-{row_index}"
            retag(cells[0], "th")
            cells[0].attrs.update({"id": row_header_id, "scope": "row"})
            for column, cell in enumerate(cells[1:], start=2):
                cell["headers"] = f"{row_header_id} {header_ids[column - 1]}"

        if [cell.get_text(" ", strip=True) for cell in table.select("th, td")] != source_cells:
            raise RuntimeError(f"Lesson10 table correction altered cell content: {table_id}")
        target_html = str(table)
        surfaces.append({
            "surface": "semantic-table",
            "table_unit_id": table_id,
            "catalogue_text_sha256": table_record["text_sha256"],
            "caption_id": caption_id,
            "source_surface_sha256": sha256(source_html.encode("utf-8")),
            "target_surface_sha256": sha256(target_html.encode("utf-8")),
            "cell_content_unchanged": True,
        })
    return surfaces


def replace_code_line(line: Tag, target: str) -> None:
    anchor = line.find("a", recursive=False)
    if anchor is None or not anchor.has_attr("data-o006-id"):
        raise RuntimeError(f"Lesson10 highlighted-code anchor differs: {line.get('id')}")
    for child in list(line.contents):
        if child is not anchor:
            child.extract()
    line.append(NavigableString(target))


def replace_output(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    pre_short: str,
    code_short: str,
    target: str,
) -> dict[str, object]:
    pre_id, pre_record = catalogue_entry(catalogue, pre_short, "unit")
    code_id, code_record = catalogue_entry(catalogue, code_short, "unit")
    pres = main.select(f'pre[data-o006-id="{pre_id}"]')
    codes = main.select(f'code[data-o006-id="{code_id}"]')
    if (
        len(pres) != 1
        or len(codes) != 1
        or codes[0].find_parent("pre") is not pres[0]
        or sha256(pres[0].get_text().encode("utf-8")) != pre_record.get("text_sha256")
        or sha256(codes[0].get_text().encode("utf-8")) != code_record.get("text_sha256")
    ):
        raise RuntimeError(f"Lesson10 published-code output differs: {pre_id}")
    source_html = str(pres[0])
    codes[0].clear()
    codes[0].append(NavigableString(target))
    return {
        "surface": "corrected-code-output",
        "pre_unit_id": pre_id,
        "code_unit_id": code_id,
        "source_surface_sha256": sha256(source_html.encode("utf-8")),
        "target_surface_sha256": sha256(str(pres[0]).encode("utf-8")),
        "expected_output": target,
    }


def repair_numeric_wald_code(
    main: Tag, catalogue: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    pre_id, pre_record = catalogue_entry(catalogue, "U0575", "unit")
    code_id, code_record = catalogue_entry(catalogue, "U0576", "unit")
    pres = main.select(f'pre[data-o006-id="{pre_id}"]')
    codes = main.select(f'code[data-o006-id="{code_id}"]')
    if (
        len(pres) != 1
        or len(codes) != 1
        or codes[0].find_parent("pre") is not pres[0]
        or sha256(pres[0].get_text().encode("utf-8")) != pre_record.get("text_sha256")
        or sha256(codes[0].get_text().encode("utf-8")) != code_record.get("text_sha256")
    ):
        raise RuntimeError("Lesson10 numeric-Wald source block differs")
    source_html = str(pres[0])
    expected_lines = {
        "cb4-3": "    if (!is.finite(p) || p <= 0 || p >= 1) return(Inf)",
        "cb4-4": "    -sum(dbinom(x, size=1, prob=p, log=TRUE))\n}",
        "cb4-6": (
            "out=optim(.5,nll.bern,x=x,method=\"L-BFGS-B\","
            "lower=.Machine$double.eps,upper=1-.Machine$double.eps,hessian=TRUE)"
        ),
        "cb4-9": "## distinguish numerical observed information from expected Fisher information",
        "cb4-10": (
            "I.obs=as.numeric(out$hessian)\n"
            "I.expected=n/(p.hat*(1-p.hat))\n"
            "stopifnot(isTRUE(all.equal(I.obs,I.expected,tolerance=1e-3)))\n"
            "I=I.expected"
        ),
    }
    for line_id, target in expected_lines.items():
        lines = codes[0].select(f'#{line_id}')
        if len(lines) != 1:
            raise RuntimeError(f"Lesson10 numeric-Wald source line differs: {line_id}")
        replace_code_line(lines[0], target)
    target_html = str(pres[0])
    surfaces: list[dict[str, object]] = [{
        "surface": "corrected-r-code",
        "pre_unit_id": pre_id,
        "code_unit_id": code_id,
        "source_surface_sha256": sha256(source_html.encode("utf-8")),
        "target_surface_sha256": sha256(target_html.encode("utf-8")),
        "constraint": "0 < p < 1 via L-BFGS-B machine-epsilon bounds",
        "invalid_likelihood_handling": "return Inf outside the Bernoulli parameter space",
        "information_distinction": "out$hessian is numerical observed information; expected Fisher information is separate",
        "downstream_code_unit_ids": [
            f"{DOCUMENT_ID}-U0593", f"{DOCUMENT_ID}-U0594",
            f"{DOCUMENT_ID}-U0608", f"{DOCUMENT_ID}-U0609",
        ],
    }]

    # These values follow from p-hat=1/20 and I=20/(.05*.95), independently
    # of the old unconstrained optimizer display.
    p_hat = 1.0 / 20.0
    information = 20.0 / (p_hat * (1.0 - p_hat))
    z_value = (p_hat - 0.25) / math.sqrt(1.0 / information)
    p_value = math.erfc(abs(z_value) / math.sqrt(2.0))
    if not (
        math.isclose(z_value, -4.103913408340617, rel_tol=0.0, abs_tol=1e-15)
        and math.isclose(p_value, 4.062195589053574e-05, rel_tol=0.0, abs_tol=1e-17)
    ):
        raise RuntimeError("Lesson10 corrected Bernoulli-Wald numerical witness differs")
    surfaces.append(replace_output(main, catalogue, "U0601", "U0602", "[1] -4.103913"))
    surfaces.append(replace_output(main, catalogue, "U0614", "U0615", "[1] 4.062196e-05"))
    return surfaces


def runtime_disclosure(
    main: Tag, catalogue: dict[str, dict[str, object]]
) -> dict[str, object]:
    source_pairs = (
        ("U0542", "U0543"), ("U0564", "U0565"), ("U0575", "U0576"),
        ("U0593", "U0594"), ("U0608", "U0609"),
    )
    output_pairs = (("U0552", "U0553"), ("U0601", "U0602"), ("U0614", "U0615"))
    expected_top_level = [
        f"{DOCUMENT_ID}-{short}" for short in
        ("U0542", "U0552", "U0564", "U0575", "U0593", "U0601", "U0608", "U0614")
    ]
    actual_top_level = [str(node["data-o006-id"]) for node in main.select("pre[data-o006-id]")]
    if actual_top_level != expected_top_level:
        raise RuntimeError(f"Lesson10 code/output topology differs: {actual_top_level}")
    inline_id = f"{DOCUMENT_ID}-U0570"
    inline = main.select(f'code[data-o006-id="{inline_id}"]')
    if len(inline) != 1 or inline[0].get_text(strip=True) != "optim":
        raise RuntimeError("Lesson10 inline-code surface differs")
    style_anchors = [f"{DOCUMENT_ID}-U{value:04d}" for value in (539, 561, 572, 590, 605)]
    styles = main.find_all("style")
    if len(styles) != 5 or [
        style.find_parent(attrs={"data-o006-id": True})["data-o006-id"] for style in styles
    ] != style_anchors:
        raise RuntimeError("Lesson10 R-label style topology differs")

    exceptions = {f"{DOCUMENT_ID}-U0575", f"{DOCUMENT_ID}-U0601", f"{DOCUMENT_ID}-U0614"}
    evidence: list[dict[str, object]] = []
    for short, child_short in (*source_pairs, *output_pairs):
        unit_id, record = catalogue_entry(catalogue, short, "unit")
        child_id, _ = catalogue_entry(catalogue, child_short, "unit")
        nodes = main.select(f'[data-o006-id="{unit_id}"]')
        if len(nodes) != 1:
            raise RuntimeError(f"Lesson10 code contract identity differs: {unit_id}")
        target_hash = sha256(nodes[0].get_text().encode("utf-8"))
        if unit_id not in exceptions and target_hash != record.get("text_sha256"):
            raise RuntimeError(f"Lesson10 unregistered code/output change: {unit_id}")
        evidence.append({
            "unit_id": unit_id,
            "child_code_unit_id": child_id,
            "catalogue_text_sha256": record["text_sha256"],
            "target_text_sha256": target_hash,
            "registered_d019_exception": unit_id in exceptions,
        })
    note_surface = add_note(
        main,
        catalogue,
        24,
        "U0616",
        "runtime-disclosure",
        "Catatan reproduktibilitas: sumber resmi tidak menetapkan versi R, keadaan sesi, atau kontrak keluaran. "
        "Kode ini hanya memakai fungsi R dasar dari paket stats. Edisi turunan harus menjalankannya dalam "
        "runtime R yang dipatok dan mencatat R.version.string, platform, sessionInfo(), hash setiap blok kode, "
        "serta kecocokan numerik keluaran. Blok pengoptimalan dan dua keluarannya adalah koreksi terdaftar D019.",
    )
    marker = json.dumps(evidence, ensure_ascii=False, sort_keys=True)
    return {
        "surface": "r-runtime-output-contract",
        "source_code_pairs": [[f"{DOCUMENT_ID}-{a}", f"{DOCUMENT_ID}-{b}"] for a, b in source_pairs],
        "output_pairs": [[f"{DOCUMENT_ID}-{a}", f"{DOCUMENT_ID}-{b}"] for a, b in output_pairs],
        "inline_code_unit_id": inline_id,
        "style_anchor_unit_ids": style_anchors,
        "runtime_requirement": "pinned Base R stats runtime with R.version.string, platform, and sessionInfo receipt",
        "expected_numeric_outputs": {
            f"{DOCUMENT_ID}-U0552": 4.062198e-05,
            f"{DOCUMENT_ID}-U0601": -4.103913,
            f"{DOCUMENT_ID}-U0614": 4.062196e-05,
        },
        "registered_d019_exceptions": sorted(exceptions),
        "note_surface": note_surface,
        "source_surface_sha256": sha256(marker.encode("utf-8")),
        "target_surface_sha256": sha256((marker + "\n" + str(note_surface)).encode("utf-8")),
    }


def title_evidence(
    rows: list[dict[str, str]], catalogue: dict[str, dict[str, object]]
) -> dict[str, object]:
    normalized = BeautifulSoup(NORMALIZED.read_text("utf-8"), "html.parser")
    source_title = normalized.title.get_text() if normalized.title is not None else ""
    expected_source_title = "10\u00a0 Hypothesis Tests (Part II) \u2013 STAT 415 | Introduction to Mathematical Statistics"
    if source_title != expected_source_title:
        raise RuntimeError("Lesson10 frozen source-title witness differs")
    segment_id, row, source_record = row_for_segment(rows, catalogue, "S0003")
    translated_heading = row["target_text"].strip()
    clean_title = f"10 — {translated_heading} — STAT 415"
    if "\ufffd" in clean_title or not translated_heading:
        raise RuntimeError("Lesson10 clean reader-title evidence differs")
    return {
        "surface": "reader-title-evidence",
        "document_id": DOCUMENT_ID,
        "heading_segment_id": segment_id,
        "heading_parent_unit_id": source_record["parent_unit_id"],
        "source_title_sha256": sha256(source_title.encode("utf-8")),
        "source_title_preserved_in_provenance": True,
        "target_title": clean_title,
        "target_surface_sha256": sha256(clean_title.encode("utf-8")),
        "target_contains_replacement_character": False,
    }


def record(defect_number: int, surfaces: list[dict[str, object]], note: str) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson10 defect has no target evidence: D{defect_number:03d}")
    return {
        "correction_id": correction_id(defect_number),
        "source_defect_id": f"L10-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


def apply_lesson10_corrections(
    main: Tag, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    verify_control_identities()
    finding_ids = re.findall(r"^## (L10-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE)
    expected_findings = [f"L10-D{i:03d}" for i in range(1, 29)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson10 admitted finding sequence differs: {finding_ids}")
    expected_segments = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, 541)]
    if len(rows) != 540 or [row.get("segment_id") for row in rows] != expected_segments:
        raise RuntimeError("Lesson10 translated segment boundary differs")

    catalogue = load_catalogue()
    manifest = load_asset_manifest()
    stable_ids_before = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    stable_math_before = [
        str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")
    ]
    if len(stable_ids_before) != 625 or len(stable_math_before) != 369:
        raise RuntimeError("Lesson10 target stable topology differs before correction")
    if main.select('[data-o006-correction-id^="O006-PSU-ADV-"]'):
        raise RuntimeError("Lesson10 corrections have already been applied")

    records: list[dict[str, object]] = []
    records.append(record(
        1,
        [segment_group_surface(
            rows, catalogue, ("S0009",),
            required_any=(("selang kepercayaan",), ("kuasa",)),
            forbidden=("dua populasi",),
        )],
        "state the instructional scope actually present instead of promising an absent two-population comparison",
    ))
    records.append(record(
        2,
        [
            segment_group_surface(
                rows, catalogue,
                ("S0074", "S0075", "S0076", "S0077", "S0079", "S0080"),
                required_any=(("konservatif",), ("7",)),
                forbidden=("0,1055", "0.1055"),
            ),
            apply_math(
                main, catalogue, "M0038",
                r"\[P_0(Y>c)\leq 0.10\]",
            ),
            apply_math(
                main, catalogue, "M0048",
                r"\(P_0(Y\geq 7)=0.044619100955301\approx 0.0446\leq 0.10\)",
            ),
            apply_math(main, catalogue, "M0049", r"\(Y\geq 7\)"),
            apply_math(
                main, catalogue, "M0051",
                r"\(\operatorname{size}=0.044619100955301\approx 0.0446\)",
            ),
            add_note(
                main, catalogue, 2, "U0136", "poisson-exact-level-note",
                "Catatan tingkat eksak: aturan nonacak Y ≥ 7 bersifat konservatif dengan ukuran "
                "0,044619100955301. Ukuran tepat 0,10 diperoleh dengan menolak ketika Y ≥ 7 dan, "
                "ketika Y = 6, menolak dengan peluang 0,911034807817211.",
            ),
        ],
        "replace the oversized Poisson rejection rule with a conservative level-0.10 rule and disclose exact boundary randomization",
    ))
    records.append(record(
        3,
        [apply_math(
            main, catalogue, "M0047",
            r"\(P_0(Y\geq 6)=0.105408105469177\approx 0.1054>0.10\)",
        )],
        "use one internally consistent exact and four-decimal Poisson upper-tail value",
    ))
    records.append(record(
        4,
        [segment_group_surface(
            rows, catalogue, ("S0105",),
            required_any=(("titik ujung",), ("≤", "kurang dari atau sama"), ("eksplisit",)),
        )],
        "state the closed-interval/p<alpha convention and require explicit endpoint treatment if p<=alpha is used",
    ))
    records.append(record(
        5,
        [apply_math(
            main, catalogue, "M0061",
            r"\(p=2P(T_{99}\geq 4.761904\ldots)\approx 0.00000656270>0\)",
        )],
        "replace the misleading rounded-zero p-value with a positive two-sided t-tail value",
    ))
    records.append(record(
        6,
        [
            apply_math(main, catalogue, "M0072", r"\(\alpha=P(\text{Type I error})\)"),
            apply_math(main, catalogue, "M0075", r"\(\beta=P(\text{Type II error})\)"),
        ],
        "restore the truncated error labels in both definitions",
    ))
    records.append(record(
        7,
        [segment_group_surface(
            rows, catalogue, ("S0184", "S0273", "S0313"),
            required_any=(("dewasa",), ("amerika",), ("kerangka sampel",)),
        )],
        "state explicitly that a student sample is not automatically a random sampling frame for the stated adult-American target population",
    ))
    records.append(record(
        8,
        [
            apply_math(
                main, catalogue, "M0109",
                r"\[\begin{aligned}"
                r"Z&=\frac{\bar X-\mu}{\sigma/\sqrt n},\qquad "
                r"\bar X=\mu+Z\frac{\sigma}{\sqrt n}\\"
                r"\bar X&=100+1.645\left(\frac{16}{\sqrt{16}}\right)=106.58"
                r"\end{aligned}\]",
            ),
            apply_math(
                main, catalogue, "M0112",
                r"\[\begin{aligned}"
                r"\operatorname{Power}&=P(\bar X\geq106.58\mid\mu=108)"
                r"=P\!\left(Z\geq\frac{106.58-108}{16/\sqrt{16}}\right)\\"
                r"&=P(Z\geq-0.36)=1-P(Z<-0.36)=1-\Phi(-0.36)"
                r"\end{aligned}\]",
            ),
        ],
        "close the scale-factor parenthesis and restore the missing equality in the continued power calculation",
    ))
    records.append(record(
        9,
        [
            apply_math(main, catalogue, "M0136", r"\(K(\mu)\)"),
            apply_math(main, catalogue, "M0141", r"\(K(\mu)\)"),
            apply_math(main, catalogue, "M0144", r"\(K(\mu)\)"),
            apply_math(main, catalogue, "M0146", r"\(K(\mu)\)"),
            apply_math(main, catalogue, "M0147", r"\(\beta(\mu)\)"),
            apply_math(main, catalogue, "M0149", r"\(\beta(\mu)=1-K(\mu)\)"),
            apply_math(main, catalogue, "M0150", r"\(K(\mu)=1-\beta(\mu)\)"),
        ],
        "use the declared parameter mu consistently in the power and type-II-error functions",
    ))
    records.append(record(
        10,
        [apply_math(main, catalogue, "M0175", r"\(1-0.3722=0.6278\)")],
        "subtract power, not the standardized cutoff, to obtain the type-II-error probability",
    ))
    records.append(record(
        11,
        [segment_group_surface(
            rows, catalogue, ("S0303", "S0304", "S0305"),
            required_any=(("rancangan", "desain"), ("varians", "pengukuran", "informasi")),
            forbidden=("satu-satunya",),
        )],
        "limit the simultaneous alpha/beta claim to the fixed Normal-mean design and acknowledge other information gains",
    ))
    records.append(record(
        12,
        [segment_group_surface(
            rows, catalogue, ("S0385",),
            required_any=(
                ("0,086974", "0.086974", "8,6974", "8.6974"),
                ("0,913026", "0.913026", "91,3026", "91.3026"),
            ),
            forbidden=("peluang 10% melakukan galat tipe ii",),
        )],
        "recalculate the rounded n=13 design as alpha about 0.049985, beta about 0.086974, and power about 0.913026",
    ))
    records.append(record(
        13,
        [
            segment_group_surface(
                rows, catalogue, ("S0414", "S0415", "S0416", "S0417", "S0418", "S0419", "S0420"),
                required_any=(
                    ("hampiran",), ("538",),
                    ("0,009647", "0.009647", "0,9647%", "0.9647%"),
                    ("0,203437", "0.203437", "20,3437%", "20.3437%"),
                ),
            ),
            apply_math(
                main, catalogue, "M0285",
                r"\[\begin{aligned}"
                r"\hat p>0.5367&\Longleftrightarrow X\geq538,\\"
                r"\alpha_{\mathrm{Normal}}&\approx0.01,\\"
                r"\alpha_{\mathrm{exact}}&=P_{p=0.50}(X\geq538)=0.009647335485396"
                r"\end{aligned}\]",
            ),
            apply_math(
                main, catalogue, "M0286",
                r"\[\begin{aligned}"
                r"\beta_{\mathrm{Normal}}&\approx0.199,\\"
                r"\beta_{\mathrm{exact}}&=P_{p=0.55}(X\leq537)=0.203436671383695"
                r"\end{aligned}\]",
            ),
        ],
        "label the proportion design as Normal-approximate and give its exact Binomial operating characteristics",
    ))
    records.append(record(
        14,
        [
            segment_group_surface(
                rows, catalogue, ("S0436", "S0437"),
                required_any=(
                    ("syarat keteraturan",), ("keteridentifikasian",),
                    ("nonsingular",), ("batas",),
                ),
            ),
            apply_math(
                main, catalogue, "M0297",
                r"\[\sqrt n(\hat\theta_{ML}-\theta_0)"
                r"\xrightarrow{d}N\!\left(0,I_1(\theta_0)^{-1}\right)\]",
            ),
            apply_math(
                main, catalogue, "M0305",
                r"\[\sqrt n(\hat{\boldsymbol\theta}_{ML}-\boldsymbol\theta_0)"
                r"\xrightarrow{d}N_p\!\left(\mathbf0,\mathbf I_1(\boldsymbol\theta_0)^{-1}\right)\]",
            ),
            apply_math(
                main, catalogue, "M0314",
                r"\[\hat\theta_k\approx N\!\left(\theta_{0,k},"
                r"[\mathbf I_n(\hat{\boldsymbol\theta})^{-1}]_{kk}\right)\]",
            ),
            apply_math(
                main, catalogue, "M0321",
                r"\[\hat\theta_k\approx N\!\left(\theta_{0,k},"
                r"[\mathbf I_n(\hat{\boldsymbol\theta})^{-1}]_{kk}\right)\]",
            ),
            apply_math(
                main, catalogue, "M0324",
                r"\[\hat\theta_k\approx N\!\left(c,"
                r"[\mathbf I_n(\hat{\boldsymbol\theta})^{-1}]_{kk}\right)\quad\text{under }H_0\]",
            ),
        ],
        "replace the universal MLE claim with regular-model scaled limits and identify plug-in total information",
    ))
    records.append(record(
        15,
        [apply_math(
            main, catalogue, "M0328",
            r"\[p=P_0\!\left(|T-c|\geq|\hat\theta_k-c|\right),"
            r"\qquad T\sim N(c,\widehat{se}_k^{\,2})\]",
        )],
        "center the unstandardized Wald extremeness calculation at the null value",
    ))
    records.append(record(
        16,
        [
            segment_group_surface(
                rows, catalogue, ("S0494", "S0495", "S0496", "S0497", "S0498", "S0499"),
            required_any=(("≤", "kurang dari atau sama", "batas harus ditetapkan"), ("gagal menolak",), ("bukti",)),
                forbidden=("menerima h", "membuktikan",),
            ),
            apply_math(main, catalogue, "M0346", r"\(p\leq\alpha\)"),
        ],
        "make p equals alpha a rejection boundary and replace acceptance/proof language with calibrated evidence",
    ))
    records.append(record(
        17,
        [segment_group_surface(
            rows, catalogue, ("S0525", "S0533"),
            required_any=(("0,25", "0.25"),),
        )],
        "retain the tested game win rate 0.25 in both Bernoulli conclusions",
    ))
    records.append(record(
        18,
        [segment_group_surface(
            rows, catalogue, ("S0522", "S0523", "S0524", "S0525", "S0531", "S0532", "S0533"),
            required_any=(
                ("wald",), ("tidak andal", "tidak reliabel"),
                ("0.048625249730321",), ("0.038177041808922",),
            ),
        )],
        "qualify the boundary-small-sample Wald result and compare both admitted exact two-sided calculations",
    ))
    records.append(record(
        19,
        [
            segment_group_surface(
                rows, catalogue, ("S0528",),
                required_any=(("(0,1)", "(0, 1)"), ("informasi teramati",), ("hessian",)),
            ),
            *repair_numeric_wald_code(main, catalogue),
        ],
        "constrain the Bernoulli optimizer, handle invalid probabilities, and distinguish observed from expected information",
    ))
    records.append(record(
        20,
        [segment_group_surface(
            rows, catalogue, ("S0535", "S0538", "S0540"),
            required_any=(("α",), ("uji-z", "uji z")),
        )],
        "restore alpha in both summary locations and z in the approximate-test label",
    ))
    records.append(record(
        21,
        repair_duplicate_ids(main, catalogue),
        "mint unique reader image IDs for all nineteen duplicate wrapper/image pairs while retaining stable bindings",
    ))
    records.append(record(
        22,
        repair_image_accessibility(main, catalogue, manifest),
        "provide substantive non-color-dependent Indonesian alts and captions for all twenty-two instructional images",
    ))
    records.append(record(
        23,
        repair_tables(main, catalogue),
        "add captions, scoped row and column headers, and explicit header associations to both tables",
    ))
    records.append(record(
        24,
        [runtime_disclosure(main, catalogue)],
        "state and register the Base-R runtime/output contract while preserving all code except the registered D019 correction",
    ))
    records.append(record(
        25,
        [title_evidence(rows, catalogue)],
        "derive a clean reader title from the translated stable heading while retaining the corrupt frozen source-title witness",
    ))
    records.append(record(
        26,
        [apply_math(
            main, catalogue, "M0335",
            r"\[p=P(|Z|\geq|Z^*|)=P(Z\leq-|Z^*|)+P(Z\geq|Z^*|)\]",
        )],
        "define Wald extremeness inclusively and use one boundary convention in both tails",
    ))
    records.append(record(
        27,
        [segment_group_surface(
            rows, catalogue, ("S0231", "S0232", "S0233", "S0261", "S0262", "S0263"),
            required_any=(("kanan", "lebih besar"), ("meningkat",)),
        )],
        "state the direction of power correctly for the right-tailed test rather than invoking absolute distance",
    ))
    records.append(record(
        28,
        [segment_group_surface(
            rows, catalogue, ("S0070",),
            required_any=(("diskret",),),
        )],
        "complete the Poisson transition by naming discreteness and its consequence for attainable nonrandomized size",
    ))

    expected_correction_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(171, 199)]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson10 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson10 correction/finding binding differs")
    if len({str(row["correction_id"]) for row in records}) != len(records):
        raise RuntimeError("Lesson10 correction identities are not unique")

    stable_ids_after = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    stable_math_after = [
        str(node["data-o006-math-id"]) for node in main.select("[data-o006-math-id]")
    ]
    if stable_ids_after != stable_ids_before or stable_math_after != stable_math_before:
        raise RuntimeError("Lesson10 corrections altered stable unit or math identities/order")
    if len(main.select(".math")) != 369:
        raise RuntimeError("Lesson10 target math census differs after correction")
    if any(count > 1 for count in Counter(str(node["id"]) for node in main.select("[id]")).values()):
        raise RuntimeError("Lesson10 target retains duplicate DOM IDs")
    figures = main.find_all("figure")
    captions = main.find_all("figcaption")
    if len(figures) != 22 or len(captions) != 22:
        raise RuntimeError("Lesson10 corrected figure/caption census differs")
    for image in main.find_all("img"):
        described_by = image.get("aria-describedby")
        if not described_by or len(main.select(f'#{described_by}')) != 1:
            raise RuntimeError("Lesson10 image caption association differs")
        if image.find_parent("figure") is None or not image.get("alt", "").strip():
            raise RuntimeError("Lesson10 corrected image semantics differ")
    return records
