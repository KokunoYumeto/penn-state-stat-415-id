#!/usr/bin/env python3
"""Apply and register every admitted Lesson 09 target-only correction."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson09_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson09_math_audit.md"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson09.html"
CATALOGUE = ROOT / "backend" / "lesson09_source_catalogue.jsonl"
ASSET_MANIFEST = ROOT / "authority" / "LESSON09_ASSET_MANIFEST.csv"
DOCUMENT_ID = "O006-PSU-010"
FIRST_CORRECTION_ORDINAL = 152

CONTROL_IDENTITIES = {
    FINDINGS: (9_355, "f09446950ab9bd655973f31a0d9e56fab2f25dfb237fbff6d352eb93645aa695"),
    MATH_AUDIT: (11_871, "12a4f5311c1b96a8a5419620e8c19a04dcf320a00f47e314d167d76507d45fb9"),
    NORMALIZED: (82_797, "d2c7f39369911013434920b937daa060d4271dff2004faa10c116584b3277140"),
    CATALOGUE: (527_701, "57a87c3be5340a69d4695499e5d7c4271c3381932b85706d8e3e69f89c41a991"),
    ASSET_MANIFEST: (3_524, "231b8b3d41af64c5a9c16dca79b39f7913bca3dc704508c5852954e52c68edca"),
}

IMAGE_CONFIG = {
    "A0001": {
        "unit_id": "U0208",
        "parent_unit_id": "U0207",
        "source_alt": "4 sided die",
        "caption_unit_id": None,
        "alt": (
            "Foto dadu tetrahedral bersisi empat yang tembus cahaya; sisi bernomor 2 dan 4 "
            "tampak. Dadu ini mengilustrasikan percobaan pada Contoh 9.3."
        ),
        "caption": (
            "Dadu tetrahedral bersisi empat pada Contoh 9.3; setiap lemparan menghasilkan "
            "salah satu dari empat sisi."
        ),
    },
    "A0002": {
        "unit_id": "U0234",
        "parent_unit_id": "U0233",
        "source_alt": "Normal distribution showing area shaded above 0.29.",
        "caption_unit_id": "U0235",
        "alt": (
            "Kurva Normal bagi distribusi penarikan sampel p-hat di bawah H₀: p = 0,25; "
            "garis batas berada di p-hat = 0,29 dan ekor kanan memuat hasil yang sekurang-kurangnya "
            "sama ekstrem dengan pengamatan."
        ),
        "caption": (
            "Gambar 9.1 — Distribusi Normal hampiran bagi p-hat ketika H₀: p = 0,25; "
            "luas ekor kanan mulai 0,29 adalah peluang memperoleh hasil yang sekurang-kurangnya "
            "sama ekstrem dengan hasil teramati."
        ),
    },
    "A0003": {
        "unit_id": "U0254",
        "parent_unit_id": "U0253",
        "source_alt": "Normal distribution showing area shaded above 0.273.",
        "caption_unit_id": "U0255",
        "alt": (
            "Kurva Normal hampiran bagi p-hat di bawah H₀: p = 0,25; batas penolakan diskret "
            "berada di p-hat = 0,273 dan ekor kanan adalah daerah penolakan hampiran bertaraf 0,05."
        ),
        "caption": (
            "Gambar 9.2 — Daerah penolakan ekor kanan mulai p-hat = 0,273 untuk uji proporsi; "
            "aturan diskretnya adalah menolak H₀ ketika Y ≥ 273."
        ),
    },
    "A0004": {
        "unit_id": "U0283",
        "parent_unit_id": "U0282",
        "source_alt": "Normal curve with center at 0.25 showing right tail critical area for alpha of .05.",
        "caption_unit_id": "U0284",
        "alt": (
            "Kurva Normal berpusat di p = 0,25 dengan batas p-hat = 0,273, yang setara dengan "
            "Z = 1,645; ekor kanan bertanda α = 0,05 adalah daerah penolakan H₀."
        ),
        "caption": (
            "Gambar 9.3 — Di bawah H₀: p = 0,25, batas Z = 1,645 atau p-hat = 0,273 "
            "memisahkan daerah gagal menolak dari daerah penolakan ekor kanan dengan α ≈ 0,05."
        ),
    },
    "A0005": {
        "unit_id": "U0303",
        "parent_unit_id": "U0302",
        "source_alt": None,
        "caption_unit_id": None,
        "alt": (
            "Kurva Normal baku untuk uji ekor kiri: batas kritis Z = −1,645; luas ekor kiri "
            "α = 0,05 adalah daerah penolakan H₀."
        ),
        "caption": (
            "Uji ekor kiri bertaraf 0,05: tolak H₀ bila Z ≤ −1,645; di sebelah kanan batas itu, "
            "gagal menolak H₀."
        ),
    },
    "A0006": {
        "unit_id": "U0313",
        "parent_unit_id": "U0312",
        "source_alt": "Normal curve with center at 0 showing left-tail critical area for alpha of 0.01.",
        "caption_unit_id": "U0314",
        "alt": (
            "Kurva Normal baku untuk uji ekor kiri dengan batas kritis Z = −2,33; luas ekor kiri "
            "α = 0,01 adalah daerah penolakan H₀."
        ),
        "caption": (
            "Gambar 9.4 — Pada taraf 0,01, tolak H₀ bila Z ≤ −2,33; nilai Z = −1,92 "
            "berada di luar daerah penolakan."
        ),
    },
    "A0007": {
        "unit_id": "U0324",
        "parent_unit_id": "U0323",
        "source_alt": "Normal curve with center at 0 showing left-tail critical area below the test statistic of -1.92.",
        "caption_unit_id": "U0325",
        "alt": (
            "Kurva Normal baku dengan statistik teramati Z = −1,92; luas ekor kiri hingga −1,92 "
            "adalah nilai-p 0,0274, sehingga H₀ ditolak pada taraf 0,05."
        ),
        "caption": (
            "Gambar 9.5 — Nilai-p uji ekor kiri adalah luas di bawah kurva Normal baku untuk "
            "Z ≤ −1,92, yaitu 0,0274; karena 0,0274 ≤ 0,05, H₀ ditolak."
        ),
    },
    "A0008": {
        "unit_id": "U0342",
        "parent_unit_id": "U0341",
        "source_alt": "Normal curve with center at 0 showing two-tail critical area for alpha of .05.",
        "caption_unit_id": "U0343",
        "alt": (
            "Kurva Normal baku untuk uji dua sisi dengan batas kritis −1,96 dan 1,96; tiap ekor "
            "memiliki luas 0,025 dan H₀ ditolak bila |Z| ≥ 1,96."
        ),
        "caption": (
            "Gambar 9.6 — Daerah penolakan uji dua sisi bertaraf 0,05 berada pada Z ≤ −1,96 "
            "dan Z ≥ 1,96; nilai teramati Z = −1,92 tidak masuk daerah itu."
        ),
    },
    "A0009": {
        "unit_id": "U0373",
        "parent_unit_id": "U0372",
        "source_alt": "Normal curve with center at 0 showing two-tail critical area for alpha of .05.",
        "caption_unit_id": "U0374",
        "alt": (
            "Kurva Normal baku untuk uji ekor kiri dengan batas kritis Z = −1,645; luas ekor kiri "
            "α = 0,05 adalah daerah penolakan H₀."
        ),
        "caption": (
            "Gambar 9.7 — Pada uji rataan ekor kiri bertaraf 0,05, batas kritisnya −1,645; "
            "statistik Z = −1,75 berada di daerah penolakan."
        ),
    },
    "A0010": {
        "unit_id": "U0380",
        "parent_unit_id": "U0379",
        "source_alt": "Normal curve with center at 0 showing two-tail critical area for alpha of .05.",
        "caption_unit_id": "U0381",
        "alt": (
            "Kurva Normal baku dengan statistik teramati Z = −1,75; luas ekor kiri hingga −1,75 "
            "adalah nilai-p 0,0401, sehingga H₀ ditolak pada taraf 0,05."
        ),
        "caption": (
            "Gambar 9.8 — Nilai-p uji ekor kiri adalah P(Z ≤ −1,75) = 0,0401; karena "
            "0,0401 ≤ 0,05, H₀ ditolak."
        ),
    },
}

DUPLICATE_ID_CONFIG = {
    "fig-rttailcritical1645": ("U0279", "U0283"),
    "fig-ht6": ("U0309", "U0313"),
    "fig-ht7": ("U0320", "U0324"),
    "fig-ht8": ("U0338", "U0342"),
    "fig-h10": ("U0369", "U0373"),
    "fig-h11": ("U0376", "U0380"),
}

TABLE_CONFIG = {
    "U0060": "Keputusan pengujian menurut keadaan hipotesis nol (tanpa label galat).",
    "U0080": "Keputusan, keadaan hipotesis nol, serta galat tipe I dan tipe II.",
    "U0148": "Keputusan uji keselamatan bangunan menurut keadaan sebenarnya.",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(defect_number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}"


def verify_control_identities() -> None:
    for path, (expected_bytes, expected_sha256) in CONTROL_IDENTITIES.items():
        payload = path.read_bytes()
        if len(payload) != expected_bytes or sha256(payload) != expected_sha256:
            raise RuntimeError(f"Lesson09 admitted control differs: {path.relative_to(ROOT)}")


def load_catalogue() -> dict[str, dict[str, object]]:
    records = [json.loads(line) for line in CATALOGUE.read_text("utf-8").splitlines()]
    by_id = {str(row["entity_id"]): row for row in records}
    if len(by_id) != len(records):
        raise RuntimeError("Lesson09 catalogue entity identities are not unique")
    document = by_id.get(DOCUMENT_ID)
    if document is None or document.get("record_type") != "document" or document.get("unit_count") != 414:
        raise RuntimeError("Lesson09 catalogue document record differs")
    if document.get("formula_count") != 219 or document.get("segment_count") != 443:
        raise RuntimeError("Lesson09 catalogue census differs")
    if document.get("duplicate_native_ids") != sorted(DUPLICATE_ID_CONFIG):
        raise RuntimeError("Lesson09 catalogue duplicate-ID census differs")
    return by_id


def load_asset_manifest() -> dict[str, dict[str, str]]:
    with ASSET_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected = [f"{DOCUMENT_ID}-A{i:04d}" for i in range(1, 11)]
    if [row["asset_id"] for row in rows] != expected:
        raise RuntimeError("Lesson09 asset manifest sequence differs")
    result = {row["asset_id"]: row for row in rows}
    for asset_id, row in result.items():
        path = ROOT / row["local_path"]
        payload = path.read_bytes()
        if len(payload) != int(row["bytes"]) or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"Lesson09 authority asset differs: {asset_id}")
    return result


def catalogue_entry(
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    record_type: str,
) -> tuple[str, dict[str, object]]:
    entity_id = f"{DOCUMENT_ID}-{short_id}"
    row = catalogue.get(entity_id)
    if row is None or row.get("record_type") != record_type or row.get("document_id") != DOCUMENT_ID:
        raise RuntimeError(f"Lesson09 catalogue binding differs: {entity_id}")
    return entity_id, row


def math_node(main: Tag, short_id: str) -> tuple[str, Tag]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson09 correction math identity differs: {math_id}")
    return math_id, nodes[0]


def apply_math(main: Tag, short_id: str, expected_sha256: str, target: str) -> dict[str, object]:
    math_id, node = math_node(main, short_id)
    source = node.get_text()
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson09 correction math source differs: {math_id}")
    if source == target:
        raise RuntimeError(f"Lesson09 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def row_for_segment(
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
) -> tuple[str, dict[str, str], dict[str, object]]:
    segment_id = f"{DOCUMENT_ID}-{short_id}"
    matches = [row for row in rows if row["segment_id"] == segment_id]
    if len(matches) != 1:
        raise RuntimeError(f"Lesson09 correction segment identity differs: {segment_id}")
    row = matches[0]
    _, source_record = catalogue_entry(catalogue, short_id, "segment")
    source = row["source_text"]
    target = row["target_text"]
    if (
        row["status"] != "translated"
        or not target.strip()
        or sha256(source.encode("utf-8")) != row["source_sha256"]
        or source_record.get("source_sha256") != row["source_sha256"]
        or source_record.get("source_text") != source
    ):
        raise RuntimeError(f"Lesson09 correction segment binding differs: {segment_id}")
    return segment_id, row, source_record


def segment_surface(
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    required: tuple[str, ...] = (),
) -> dict[str, object]:
    segment_id, row, source_record = row_for_segment(rows, catalogue, short_id)
    target = row["target_text"]
    if row["source_text"] == target or any(token not in target for token in required):
        raise RuntimeError(f"Lesson09 admitted prose correction is absent: {segment_id}")
    return {
        "surface": "translation-segment",
        "segment_id": segment_id,
        "parent_unit_id": source_record["parent_unit_id"],
        "source_surface_sha256": row["source_sha256"],
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def correct_segment(
    main: Tag,
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    corrected: str,
) -> dict[str, object]:
    segment_id, row, source_record = row_for_segment(rows, catalogue, short_id)
    admitted_target = row["target_text"]
    matches = [
        node
        for node in main.find_all(string=True)
        if isinstance(node, NavigableString) and str(node) == admitted_target
    ]
    if admitted_target != corrected:
        if len(matches) != 1:
            raise RuntimeError(f"Lesson09 translated correction surface differs: {segment_id}")
        matches[0].replace_with(NavigableString(corrected))
    elif not matches:
        raise RuntimeError(f"Lesson09 translated surface is missing: {segment_id}")
    return {
        "surface": "translation-segment-correction",
        "segment_id": segment_id,
        "parent_unit_id": source_record["parent_unit_id"],
        "authority_source_sha256": row["source_sha256"],
        "source_surface_sha256": sha256(admitted_target.encode("utf-8")),
        "target_surface_sha256": sha256(corrected.encode("utf-8")),
        "translation_layer_changed": admitted_target != corrected,
    }


def add_boundary_note(main: Tag, catalogue: dict[str, dict[str, object]]) -> dict[str, object]:
    unit_id, unit = catalogue_entry(catalogue, "U0185", "unit")
    nodes = main.select(f'[data-o006-id="{unit_id}"]')
    if len(nodes) != 1 or unit.get("tag") != "p":
        raise RuntimeError("Lesson09 critical-boundary anchor differs")
    anchor = nodes[0]
    note_text = (
        "Konvensi batas edisi ini: tolak H₀ bila |T*| ≥ c dan gagal menolaknya bila |T*| < c. "
        "Untuk hukum nol kontinu yang sesuai, kejadian |T*| = c biasanya berpeluang nol. "
        "Pada uji diskret bertaraf eksak, tindakan pada himpunan kesamaan harus ditetapkan "
        "secara deterministik atau diacak agar ukuran yang diminta tercapai."
    )
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction", "decision-boundary-note"]
    note["data-o006-correction-id"] = correction_id(3)
    note["role"] = "note"
    note.append(NavigableString(note_text))
    source_marker = f"{unit_id}\n{unit['text_sha256']}"
    anchor.insert_after(note)
    return {
        "surface": "adjacent-correction-note",
        "unit_id": unit_id,
        "catalogue_text_sha256": unit["text_sha256"],
        "source_surface_sha256": sha256(source_marker.encode("utf-8")),
        "target_surface_sha256": sha256((source_marker + "\n" + str(note)).encode("utf-8")),
    }


def repair_image_accessibility(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    manifest: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for short_asset_id, config in IMAGE_CONFIG.items():
        asset_id, asset_record = catalogue_entry(catalogue, short_asset_id, "asset")
        manifest_row = manifest[asset_id]
        unit_id = f"{DOCUMENT_ID}-{config['unit_id']}"
        parent_unit_id = f"{DOCUMENT_ID}-{config['parent_unit_id']}"
        images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
        if len(images) != 1:
            raise RuntimeError(f"Lesson09 image identity differs: {asset_id}")
        image = images[0]
        if (
            image.get("data-o006-id") != unit_id
            or image.get("src") != asset_record.get("source_ref")
            or asset_record.get("unit_ids") != [unit_id]
            or asset_record.get("first_parent_unit_id") != parent_unit_id
            or image.get("alt") != config["source_alt"]
        ):
            raise RuntimeError(f"Lesson09 image/catalogue surface differs: {asset_id}")

        source_alt = image.get("alt")
        source_caption = ""
        target_caption = str(config["caption"])
        caption_short = config["caption_unit_id"]
        if caption_short is None:
            parent = image.find_parent(attrs={"data-o006-id": parent_unit_id})
            if parent is None or parent.name != "p":
                raise RuntimeError(f"Lesson09 bare-image parent differs: {asset_id}")
            caption_id = f"{asset_id.lower()}-caption-id"
            if main.select(f'#{caption_id}'):
                raise RuntimeError(f"Lesson09 target caption already exists: {asset_id}")
            fragment = BeautifulSoup("", "html.parser")
            caption = fragment.new_tag("span")
            caption["id"] = caption_id
            caption["class"] = ["figure-caption", "d-block"]
            caption["data-o006-correction-id"] = correction_id(15)
            caption.append(NavigableString(target_caption))
            image.insert_after(caption)
            parent["role"] = "group"
        else:
            caption_unit_id = f"{DOCUMENT_ID}-{caption_short}"
            _, caption_record = catalogue_entry(catalogue, str(caption_short), "unit")
            captions = main.select(f'figcaption[data-o006-id="{caption_unit_id}"]')
            if len(captions) != 1 or caption_record.get("tag") != "figcaption":
                raise RuntimeError(f"Lesson09 figure-caption identity differs: {asset_id}")
            caption = captions[0]
            caption_id = str(caption.get("id") or f"{asset_id.lower()}-caption-id")
            source_caption = caption.get_text(" ", strip=True)
            caption["id"] = caption_id
            caption.clear()
            caption.append(NavigableString(target_caption))
            caption["class"] = [
                name for name in caption.get("class", []) if name != "quarto-uncaptioned"
            ]
            caption["data-o006-correction-id"] = correction_id(15)
        image["alt"] = str(config["alt"])
        image["aria-describedby"] = caption_id
        lightbox = image.find_parent("a", class_="lightbox")
        if lightbox is not None:
            lightbox["title"] = target_caption

        surfaces.append({
            "surface": "image-alt-caption",
            "asset_id": asset_id,
            "unit_id": unit_id,
            "parent_unit_id": parent_unit_id,
            "source_ref": asset_record["source_ref"],
            "authority_asset_bytes": int(manifest_row["bytes"]),
            "authority_asset_sha256": manifest_row["sha256"],
            "authority_asset_unchanged": True,
            "source_alt_sha256": sha256((source_alt or "").encode("utf-8")),
            "target_alt_sha256": sha256(str(config["alt"]).encode("utf-8")),
            "source_caption_sha256": sha256(source_caption.encode("utf-8")),
            "target_caption_sha256": sha256(target_caption.encode("utf-8")),
            "caption_id": caption_id,
        })
    return surfaces


def repair_duplicate_ids(
    main: Tag, catalogue: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    source_ids = [str(node["id"]) for node in main.select("[id]")]
    duplicates = sorted(name for name, count in Counter(source_ids).items() if count > 1)
    if duplicates != sorted(DUPLICATE_ID_CONFIG):
        raise RuntimeError(f"Lesson09 duplicate native-ID surface differs: {duplicates}")
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
            raise RuntimeError(f"Lesson09 duplicate-ID catalogue binding differs: {native_id}")
        target_id = f"{native_id}-image"
        if main.select(f'#{target_id}'):
            raise RuntimeError(f"Lesson09 target image ID already exists: {target_id}")
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
        raise RuntimeError("Lesson09 reader still contains duplicate DOM IDs")
    return surfaces


def retag(cell: Tag, name: str) -> None:
    if cell.name not in {"td", "th"}:
        raise RuntimeError("Lesson09 table cell tag differs")
    cell.name = name


def repair_tables(
    main: Tag, catalogue: dict[str, dict[str, object]]
) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for table_index, (short_id, caption_text) in enumerate(TABLE_CONFIG.items(), start=1):
        table_id, table_record = catalogue_entry(catalogue, short_id, "unit")
        tables = main.select(f'table[data-o006-id="{table_id}"]')
        if len(tables) != 1 or table_record.get("tag") != "table":
            raise RuntimeError(f"Lesson09 table identity differs: {table_id}")
        table = tables[0]
        if table.find("caption", recursive=False) is not None:
            raise RuntimeError(f"Lesson09 table unexpectedly has a caption: {table_id}")
        source_html = str(table)
        source_nonempty = [
            cell.get_text(" ", strip=True)
            for cell in table.select("th, td")
            if cell.get_text(" ", strip=True)
        ]
        rows = table.select("tr")
        if len(rows) not in {3, 4}:
            raise RuntimeError(f"Lesson09 table row census differs: {table_id}")

        fragment = BeautifulSoup("", "html.parser")
        caption = fragment.new_tag("caption")
        caption_id = f"o006-psu-010-table-{table_index}-caption"
        caption["id"] = caption_id
        caption["data-o006-correction-id"] = correction_id(17)
        caption.append(NavigableString(caption_text))
        table.insert(0, caption)
        table["aria-describedby"] = caption_id

        if table_index in {1, 2}:
            if len(rows) != 4 or any(len(row.find_all(["td", "th"], recursive=False)) != 3 for row in rows):
                raise RuntimeError(f"Lesson09 decision-table geometry differs: {table_id}")
            top = rows[0].find_all(["td", "th"], recursive=False)
            sub = rows[1].find_all(["td", "th"], recursive=False)
            if top[2].get_text(" ", strip=True) or sub[0].get_text(" ", strip=True):
                raise RuntimeError(f"Lesson09 decision-table empty headers differ: {table_id}")
            for cell in [*top, *sub]:
                retag(cell, "th")
            decision_id = f"o006-psu-010-table-{table_index}-decision"
            reality_id = f"o006-psu-010-table-{table_index}-reality"
            true_id = f"o006-psu-010-table-{table_index}-h0-true"
            false_id = f"o006-psu-010-table-{table_index}-h0-false"
            top[0].attrs.update({"id": decision_id, "scope": "col", "rowspan": "2"})
            top[1].attrs.update({"id": reality_id, "scope": "colgroup", "colspan": "2"})
            top[2].attrs.update({"scope": "col", "aria-hidden": "true", "hidden": ""})
            top[2].attrs.update({"hidden": "", "aria-hidden": "true"})
            sub[0].attrs.update({"hidden": "", "aria-hidden": "true"})
            sub[1].attrs.update({"id": true_id, "scope": "col", "headers": reality_id})
            sub[2].attrs.update({"id": false_id, "scope": "col", "headers": reality_id})
            sub[0].attrs.update({"scope": "col", "aria-hidden": "true", "hidden": ""})
            for row_index, row in enumerate(rows[2:], start=1):
                cells = row.find_all(["td", "th"], recursive=False)
                row_header_id = f"o006-psu-010-table-{table_index}-row-{row_index}"
                retag(cells[0], "th")
                cells[0].attrs.update({"id": row_header_id, "scope": "row", "headers": decision_id})
                cells[1]["headers"] = f"{row_header_id} {true_id}"
                cells[2]["headers"] = f"{row_header_id} {false_id}"
        else:
            if len(rows) != 3 or len(rows[0].find_all(["td", "th"], recursive=False)) != 3:
                raise RuntimeError(f"Lesson09 applied-table geometry differs: {table_id}")
            headers = rows[0].find_all(["td", "th"], recursive=False)
            header_ids = []
            for column, cell in enumerate(headers, start=1):
                retag(cell, "th")
                header_id = f"o006-psu-010-table-{table_index}-column-{column}"
                header_ids.append(header_id)
                cell.attrs.update({"id": header_id, "scope": "col"})
                if column == 1 and not cell.get_text(" ", strip=True):
                    cell["aria-label"] = "Keputusan pengujian"
            for row_index, row in enumerate(rows[1:], start=1):
                cells = row.find_all(["td", "th"], recursive=False)
                row_header_id = f"o006-psu-010-table-{table_index}-row-{row_index}"
                retag(cells[0], "th")
                cells[0].attrs.update({"id": row_header_id, "scope": "row"})
                cells[1]["headers"] = f"{row_header_id} {header_ids[1]}"
                cells[2]["headers"] = f"{row_header_id} {header_ids[2]}"

        target_nonempty = [
            cell.get_text(" ", strip=True)
            for cell in table.select("th, td")
            if cell.get_text(" ", strip=True)
        ]
        if target_nonempty != source_nonempty:
            raise RuntimeError(f"Lesson09 table correction altered decision/error content: {table_id}")
        target_html = str(table)
        surfaces.append({
            "surface": "semantic-table",
            "table_unit_id": table_id,
            "catalogue_text_sha256": table_record["text_sha256"],
            "caption_id": caption_id,
            "source_surface_sha256": sha256(source_html.encode("utf-8")),
            "target_surface_sha256": sha256(target_html.encode("utf-8")),
            "decision_error_content_unchanged": True,
        })
    return surfaces


def disclose_frozen_plots(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    manifest: dict[str, dict[str, str]],
) -> list[dict[str, object]]:
    surfaces: list[dict[str, object]] = []
    for asset_short, figure_short in (("A0002", "U0227"), ("A0003", "U0247")):
        asset_id, asset_record = catalogue_entry(catalogue, asset_short, "asset")
        figure_id, figure_record = catalogue_entry(catalogue, figure_short, "unit")
        figures = main.select(f'figure[data-o006-id="{figure_id}"]')
        if len(figures) != 1 or figure_record.get("role") != "figure":
            raise RuntimeError(f"Lesson09 generated-plot figure differs: {figure_id}")
        note_text = (
            "Catatan reprodusibilitas: gambar ini adalah keluaran beku dari sumber resmi. "
            "Sumber tidak memublikasikan kode pembangkit, data masukan, kunci lingkungan, "
            "atau keadaan acak; karena itu yang dapat diverifikasi secara deterministik di sini "
            "hanyalah bita keluaran gambar, bukan regenerasi plot dari sumber."
        )
        fragment = BeautifulSoup("", "html.parser")
        note = fragment.new_tag("p")
        note["class"] = ["target-only-correction", "reproducibility-note"]
        note["data-o006-correction-id"] = correction_id(19)
        note["data-o006-related-asset-id"] = asset_id
        note["role"] = "note"
        note.append(NavigableString(note_text))
        marker = "\n".join((
            figure_id,
            str(figure_record["text_sha256"]),
            asset_id,
            str(manifest[asset_id]["sha256"]),
        ))
        figures[0].insert_after(note)
        surfaces.append({
            "surface": "generated-output-disclosure",
            "figure_unit_id": figure_id,
            "asset_id": asset_id,
            "source_ref": asset_record["source_ref"],
            "authority_asset_bytes": int(manifest[asset_id]["bytes"]),
            "authority_asset_sha256": manifest[asset_id]["sha256"],
            "authority_asset_unchanged": True,
            "source_surface_sha256": sha256(marker.encode("utf-8")),
            "target_surface_sha256": sha256((marker + "\n" + str(note)).encode("utf-8")),
            "source_level_reproduction_claimed": False,
        })
    return surfaces


def record(defect_number: int, surfaces: list[dict[str, object]], note: str) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson09 defect has no target evidence: D{defect_number:03d}")
    return {
        "correction_id": correction_id(defect_number),
        "source_defect_id": f"L09-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


def apply_lesson09_corrections(
    main: Tag, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    verify_control_identities()
    finding_ids = re.findall(r"^## (L09-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE)
    expected_findings = [f"L09-D{i:03d}" for i in range(1, 20)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson09 admitted finding sequence differs: {finding_ids}")
    audit_text = MATH_AUDIT.read_text("utf-8")
    try:
        audit_register = audit_text.split(
            "## High-confidence correction register", 1
        )[1].split("## Translation traps", 1)[0]
    except IndexError as exc:
        raise RuntimeError("Lesson09 mathematical audit register is missing") from exc
    audit_ids = [int(value) for value in re.findall(r"^(\d+)\. ", audit_register, re.MULTILINE)]
    if audit_ids != list(range(1, 20)):
        raise RuntimeError("Lesson09 mathematical audit register differs")
    catalogue = load_catalogue()
    manifest = load_asset_manifest()
    stable_ids_before = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    if len(stable_ids_before) != 414:
        raise RuntimeError("Lesson09 target stable-unit census differs before correction")
    if main.select('[data-o006-correction-id^="O006-PSU-ADV-"]'):
        raise RuntimeError("Lesson09 corrections have already been applied")

    records: list[dict[str, object]] = []
    records.append(record(
        1,
        [
            correct_segment(
                main,
                rows,
                catalogue,
                "S0089",
                "Pada nilai parameter alternatif tertentu θ, kuasa uji adalah peluang menolak "
                "hipotesis nol ketika nilai θ itu benar, yaitu ",
            ),
            apply_math(
                main,
                "M0021",
                "a71336cca295e73332f60259df96e8b23616c35139ed1fd717761a72e9e18936",
                r"\(\operatorname{kuasa}(\theta)=1-\beta(\theta)\)",
            ),
            apply_math(
                main,
                "M0023",
                "b11c91bb2934fd170c713aa9d4ac0240dc5d0404a2e3729c80a269642ae6baa9",
                r"\(\beta(\theta)\)",
            ),
            apply_math(
                main,
                "M0025",
                "b11c91bb2934fd170c713aa9d4ac0240dc5d0404a2e3729c80a269642ae6baa9",
                r"\(\beta(\theta)\)",
            ),
        ],
        "make beta and power explicit functions of the specified true alternative parameter",
    ))
    records.append(record(
        2,
        [correct_segment(
            main,
            rows,
            catalogue,
            "S0091",
            " adalah peluang melakukan galat, sehingga kita menginginkan keduanya kecil. "
            "Untuk ukuran sampel, keluarga uji, dan nilai parameter alternatif yang tetap, "
            "penurunan salah satunya umumnya menaikkan yang lain. Namun, penambahan informasi—"
            "misalnya dengan memperbesar ukuran sampel—dapat menurunkan keduanya. Ketika ",
        )],
        "limit the alpha/beta tradeoff to a fixed design and specified alternative",
    ))
    records.append(record(
        3,
        [
            apply_math(
                main,
                "M0055",
                "138882e54f26c00c4f32e508b1981259517dcfb2d4b7e056d7e5a23a7c8d1fdf",
                r"\(|T^*|\ge c\)",
            ),
            add_boundary_note(main, catalogue),
        ],
        "close the generic equality boundary and disclose exact discrete boundary randomization",
    ))
    records.append(record(
        4,
        [correct_segment(
            main,
            rows,
            catalogue,
            "S0156",
            " Nilai-p adalah peluang, di bawah hipotesis nol, memperoleh statistik uji yang "
            "sekurang-kurangnya sama ekstrem dengan nilai teramati. Dalam edisi ini, H₀ ditolak "
            "ketika nilai-p ≤ α. Daerah penolakan ditentukan dengan menggunakan alfa untuk mencari "
            "nilai kritis; daerah penolakan adalah wilayah yang sekurang-kurangnya sama ekstrem "
            "dengan batas kritis. Misalkan statistik uji kita dilambangkan dengan ",
        )],
        "define the p-value inclusively and state one complete p-value decision convention",
    ))
    records.append(record(
        5,
        [apply_math(
            main,
            "M0086",
            "9c5ece0f0f54d7959ef899610014af4604054d1faf4267647836d32cc8bdb0b7",
            r"\[Z>1.645\Longleftrightarrow \hat{p}>0.272525\ldots"
            r"\Longleftrightarrow Y\ge273\Longleftrightarrow \hat{p}\ge0.273\]",
        )],
        "restore the exact discrete equivalence after rounding the one-proportion cutoff",
    ))
    records.append(record(
        6,
        [
            correct_segment(
                main,
                rows,
                catalogue,
                "S0227",
                "Dengan hampiran Normal yang digunakan di sini, ‘ukuran’ daerah kritis sekitar "
                "0,05, bukan tepat 0,05. Untuk aturan diskret Y ≥ 273, ukuran Binomial eksaknya "
                "0,0511947; tingkat eksak 0,05 memerlukan pengacakan pada Y = 273. Hal ini akan "
                "berkaitan dengan peluang galat yang dibahas di bawah.",
            ),
            apply_math(
                main,
                "M0099",
                "2fcc3d4a8d7f6168b1c71319a53ae1ccce6fc1fe4efd77c165324fcb70542e16",
                r"\[\begin{aligned}"
                r"\beta(0.27)&=P_{p=0.27}(\hat{p}<0.273)\\"
                r"&\approx P\!\left(Z<\frac{0.273-0.27}{\sqrt{0.27(0.73)/1000}}\right)"
                r"=P(Z<0.214)\approx0.5847"
                r"\end{aligned}\]",
            ),
        ],
        "label the Normal size and beta calculations as approximations and give the exact size witness",
    ))
    records.append(record(
        7,
        [correct_segment(
            main,
            rows,
            catalogue,
            "S0143",
            "Jika data sampel tidak konsisten dengan hipotesis nol, tetapi konsisten dengan "
            "hipotesis alternatif, kita menolak hipotesis nol. Data itu memberikan bukti yang "
            "cukup untuk mendukung hipotesis alternatif, tetapi tidak membuktikannya benar karena "
            "galat tipe I tetap mungkin terjadi.",
        )],
        "replace certainty about the alternative with controlled inferential evidence",
    ))
    records.append(record(
        8,
        [
            segment_surface(rows, catalogue, "S0340", ("ekor kiri",)),
            segment_surface(rows, catalogue, "S0341", ("ekor kanan",)),
            segment_surface(rows, catalogue, "S0342", ("ekuivalen",)),
        ],
        "restore both left- and right-tail rejection conditions in the reader prose",
    ))
    records.append(record(
        9,
        [
            segment_surface(rows, catalogue, "S0370", ("sampel acak iid", "tidak ada ukuran sampel")),
            segment_surface(rows, catalogue, "S0371", ("hampiran",)),
            segment_surface(rows, catalogue, "S0372", ("menghampiri",)),
        ],
        "replace the universal n=25 CLT claim with exact-Normal and qualified approximation conditions",
    ))
    records.append(record(
        10,
        [apply_math(
            main,
            "M0175",
            "7d7cde733dbc40b6c62ae7c6c3b48d4c4cb09eb7a07076f50c23b72d04d78dd6",
            r"\(=0.0401<\alpha=0.05\)",
        )],
        "correct the misplaced decimal in the Example 9.6 p-value comparison",
    ))
    records.append(record(
        11,
        [apply_math(
            main,
            "M0192",
            "2e030e590cfcbf967257be3244d75553f9ce30c51118b93bc1411498542c6de2",
            r"\(t\le -t_{0.025,99}=-1.9842\)",
        )],
        "give the lower critical value the negative of the upper-tail t quantile",
    ))
    records.append(record(
        12,
        [
            apply_math(
                main,
                "M0200",
                "aa31712b2c37f73920c13019abf04c4bead02bf9b78e0ecc8536ac3685a541d9",
                r"\[\begin{aligned}"
                r"p&=2P(T_{99}\ge4.762)\\"
                r"&\approx0.00000656<0.01<0.05"
                r"\end{aligned}\]",
            ),
            segment_surface(rows, catalogue, "S0423", ("0,00000656",)),
        ],
        "supply the two-sided t-tail calculation that proves the stronger p-value bound",
    ))
    records.append(record(
        13,
        [segment_surface(rows, catalogue, "S0402", ("sampel acak iid", "Normal"))],
        "state the iid Normal random-sample assumption for the exact one-sample t law",
    ))
    records.append(record(
        14,
        [segment_surface(rows, catalogue, "S0434", ("hipotesis nol", "hipotesis alternatif"))],
        "restore both hypothesis subjects in the summary definition of Type II error",
    ))
    records.append(record(
        15,
        repair_image_accessibility(main, catalogue, manifest),
        "provide complete Indonesian, non-color-dependent alt and caption semantics for all ten images",
    ))
    records.append(record(
        16,
        repair_duplicate_ids(main, catalogue),
        "mint unique reader image IDs while preserving every stable catalogue binding",
    ))
    records.append(record(
        17,
        repair_tables(main, catalogue),
        "add captions, column headers, row headers, scopes, and explicit header associations to all tables",
    ))
    records.append(record(
        18,
        [
            segment_surface(rows, catalogue, "S0136", ("menyatakan bahwa bangunan itu tidak aman",)),
            segment_surface(rows, catalogue, "S0182", ("diuraikan",)),
            segment_surface(rows, catalogue, "S0187", ("lebih sering",)),
            segment_surface(rows, catalogue, "S0190", ("mari kita pilih",)),
            segment_surface(rows, catalogue, "S0208", ("“nilai kritis”", "“daerah kritis”")),
        ],
        "repair the five proved duplicated-word, agreement, comparison, apostrophe, and quotation defects",
    ))
    records.append(record(
        19,
        disclose_frozen_plots(main, catalogue, manifest),
        "identify both generated plots as verified frozen outputs without claiming source-level regeneration",
    ))

    expected_correction_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(152, 171)]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson09 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson09 correction/finding binding differs")
    if len({str(row["correction_id"]) for row in records}) != len(records):
        raise RuntimeError("Lesson09 correction identities are not unique")
    stable_ids_after = [str(node["data-o006-id"]) for node in main.select("[data-o006-id]")]
    if stable_ids_after != stable_ids_before:
        raise RuntimeError("Lesson09 corrections altered stable unit identities or order")
    return records
