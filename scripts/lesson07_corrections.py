#!/usr/bin/env python3
"""Apply and register every admitted Lesson 07 target-only correction."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson07_source_findings.md"
MATH_AUDIT = ROOT / "working" / "lesson07_math_audit.md"
NORMALIZED = ROOT / "source" / "normalized" / "en-US" / "Lesson07.html"
CATALOGUE = ROOT / "backend" / "lesson07_source_catalogue.jsonl"
DOCUMENT_ID = "O006-PSU-008"
FIRST_CORRECTION_ORDINAL = 123
SEGMENT_COUNT = 237

FROZEN_INPUTS = {
    FINDINGS: (
        10_950,
        "122b6dbe009e3fce5904e51d76a223fd1267bfc7010f56f15dd6d17cc69988e7",
    ),
    MATH_AUDIT: (
        14_406,
        "a06941dbf84788deb1e4895553b264f5b926a7174a944ab647a0eb522514b385",
    ),
    NORMALIZED: (
        69_757,
        "c67926962dc23726b74668536aac11b5c054f44faf416a8a84bcefa3191aa9d8",
    ),
    CATALOGUE: (
        381_338,
        "e29f849181b67474c4ca6a8790e7dd11484c3fbaf08a9144eeaeb0e93da31116",
    ),
}

MATH_SOURCE_SHA256 = {
    "M0002": "96ed07149e99066ec22ae6fb95e6b828a051b0719d94c1176fc6c5508e933407",
    "M0043": "87b9ba067c1af34cc01000758c5686a16d9a25c68e9aebfe859731f3e0b4733b",
    "M0088": "d1e079dd590672d4f5f8065ab685cafa4721de9082dbce3c59c265735a5e57ac",
    "M0090": "488074c48fb1344c2bdc88715715e7f490f9e79d30df28dd9c3452889680683d",
    "M0093": "888628ad777409e97015a0f74cfb60504b9b3bb62b2f44441f02a026878ec9bd",
    "M0098": "3347793e7fcd5063b13d26b5ccafc7b95acfb29a4329ec8961b1fb57c066398e",
    "M0102": "9a588741f25d7fb78a1fdf4285647c04a27584df43a0ddcb72a76637668479af",
    "M0104": "065f78d538feeea193336efcd7d8bd32c4467356a5808f88488f69fb334294ad",
    "M0146": "8dcefd3fba00fd6af43e56951e025de0d3796edf18aecfaf6efbb145cc7e45c4",
    "M0147": "9ebaa7659a6378af9f445688031aaa82a49d4db3b24f93d22bc6e53063a1320e",
    "M0148": "b449d2e2425f68d11aa80672d0bfed67df1119492eb3901a1ef91d7e0f85fabc",
}

UNIT_SOURCE_SHA256 = {
    "U0038": "6ddec5d9d88155a20c7bffa58d4f201b3727febf3f0df699e06d733525ea7d02",
    "U0194": "4ff5fe9c39f9ff9bedef0742d9bf9d1083fa632d9f721edc7c7db9c84530b433",
    "U0206": "b699d6b2afd5b4882222e83f086068ce83f8c587260194fd8bf48d2e96a2882a",
    "U0224": "9dbb84c6a38b0ea900b248da8b84de050397aebb867670bc6dda788e40b95805",
    "U0309": "33df7fd836f316aafa3ff864a9d359d4c1567874ec1c972832896a0404981928",
    "U0325": "90133245bd70da81a646d10dffc8abe078bed340166f11d1cd8ad75c133b1782",
    "U0331": "e7595211e9dda720b6cd6e924d532caa37412986efd19522392308261272d85e",
    "U0344": "07ba854f2e93ba5ff434d872dd0163cc338b19168a15ce3f0912a54a3d6e49fa",
    "U0353": "6d2480f1a89be4d14aae278d593ac30b7700efc3cfeca0e10fc2428ec0ccee24",
}

# The admitted translation is also byte-bound before any target-only repair.
TRANSLATION_TARGET_SHA256 = {
    "S0010": "8dee4b7acbe75c019b50b97b8f22e7ab0edf3f9f7208c1fe1543b5c15d339962",
    "S0019": "bbb164512fc3d93c96d6b6fbd91f826c682823c5c6b5a847d1a4617acab42bb9",
    "S0020": "164c8b4a0285359df6f8d7c124ddc6b2108dc8971f2de4d7e218f0b4ea9c92ac",
    "S0021": "65b4703cacb7235a0ce6e5d8033398f8c7f811c0ac82060363c42a55e5075a68",
    "S0028": "e6ad36c5212519301340f614d81f81622fc0c950f825258f46e2c8ee399c4866",
    "S0049": "c1df27497740b2f8d7283c8e471ca51e3f5ea720030621c9881e42d88dfac840",
    "S0061": "c239dff51689977b98678bc7e140231f0de8bc47048550ded6af0d443277de12",
    "S0089": "a016e107038036023be95e8451e30d1626ae85e7f20ae4dbe07ac41dac52f441",
    "S0099": "eaf24bfd782fdb6b1d06bf0c2a24276eb2a196be44b0f4c8a6d7a74f14ac3517",
    "S0131": "2631785d000bf1510068c3f4a956826f9eb563c315ad53cd87e9526d5ceb07e4",
    "S0138": "07181df6510c2eeaceea6766797af3885f8999b30151fcac7bd2e56afcb07cf1",
    "S0152": "aaba10fe9a755c18c89c172d1301ee9234d82b82c4002acffbb72cf068ac523b",
    "S0155": "a5a9cfadc296fe74ebe5716b4171678f23e2fd6f8cc6fc3618bb2a3c252537e2",
    "S0169": "bd5ad2be8df362ca3fb4bdb2b5310581a3aa1136a3ed9b8b847f953a26d2e5e3",
    "S0177": "8e1113ea59b498b1d579e2a56eeda8a8a77c59b17e87a24452de08ab480cfe7c",
    "S0180": "b9dd722dfb18f58a02667289280ca4ff5c05d69735b8e181c4590fc5f441d975",
    "S0193": "7f98b2232ecaa276da3e3dc3a431c72664a00496f6bf31924a3cc4bf57ad5795",
    "S0196": "fac0503d7e7713af29eba9382b0bd8dd4552182aeb83afc70561c4eaaf210988",
    "S0198": "54872004952b3c6210133338e74b5884aea9382d791c0c1c05bc44e32d253115",
    "S0201": "fa33dfdac4f863198d4a6810173d0043ab1546d1ff3350cf07cc421d5acf590e",
    "S0209": "26d7a80fff779686fb17503487363943b16762e83b6e98182531ce7031cc4cf0",
    "S0213": "8a7ed6c00aaf2cf053c1a1c3994070a8a50fa38d811fac32da5a4148a01e54b6",
    "S0214": "4acf80626ddaa5a05a09f6491c024bcb331fb9b8fa8d2127cd13321057c0a20d",
    "S0215": "2daac6f8803a978789b87dc51668c6d180bfb008937dd59b3d2a2512aebfb38b",
    "S0230": "5488614f713549773cc931f451a39a4f568c5b1d75d5c2668d0352ae1be1c849",
    "S0236": "39aa51cb94ddacd8ca3ca946a9f3f0849bac35e349b848647a141cab5a0ad844",
    "S0237": "e70fbf3b4d123ffdf7abff8a5000ec6bee75fcfbaf2d166967d097eff2c48b4e",
}

ASSETS = {
    "A0001": {
        "path": ROOT
        / "authority"
        / "assets"
        / "stat415"
        / "lesson07"
        / "Lesson07_files"
        / "figure-html"
        / "unnamed-chunk-1-1.png",
        "bytes": 51_500,
        "sha256": "261e8fee2ada5d25b3cf92d4fde1825dfcce67f97629120efc6d432b06a89372",
        "src": "Lesson07_files/figure-html/unnamed-chunk-1-1.png",
        "source_alt": "Histogram of geometric distribution",
        "target_alt": (
            "Histogram sampel Geometrik: frekuensi tertinggi berada dekat 0, "
            "kemudian cepat menurun dengan ekor panjang ke kanan; sumbu horizontal "
            "menunjukkan nilai pengamatan dan sumbu vertikal menunjukkan frekuensi."
        ),
        "unit_id": f"{DOCUMENT_ID}-U0186",
        "parent_unit_id": f"{DOCUMENT_ID}-U0185",
    },
    "A0002": {
        "path": ROOT
        / "authority"
        / "assets"
        / "stat415"
        / "lesson07"
        / "Lesson07_files"
        / "figure-html"
        / "unnamed-chunk-6-1.png",
        "bytes": 49_223,
        "sha256": "18e14d1763554c43bcc8c31ba57756918ea7e47985abbf840f40ee3842460e65",
        "src": "Lesson07_files/figure-html/unnamed-chunk-6-1.png",
        "source_alt": "Histogram of normal distribution",
        "target_alt": (
            "Histogram sampel Normal berbenih tetap: bentuknya kira-kira lonceng "
            "dan berpusat dekat −7; sumbu horizontal menunjukkan nilai pengamatan "
            "dan sumbu vertikal menunjukkan frekuensi."
        ),
        "unit_id": f"{DOCUMENT_ID}-U0301",
        "parent_unit_id": f"{DOCUMENT_ID}-U0300",
    },
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(defect_number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}"


def verify_frozen_evidence() -> tuple[dict[str, dict[str, object]], Tag]:
    for path, (expected_bytes, expected_sha256) in FROZEN_INPUTS.items():
        payload = path.read_bytes()
        if len(payload) != expected_bytes or sha256(payload) != expected_sha256:
            raise RuntimeError(f"Lesson07 frozen evidence differs: {path.name}")

    finding_ids = re.findall(
        r"^## (L07-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE
    )
    expected_findings = [f"L07-D{i:03d}" for i in range(1, 13)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson07 admitted finding sequence differs: {finding_ids}")

    catalogue_rows = [
        json.loads(line)
        for line in CATALOGUE.read_text("utf-8").splitlines()
        if line
    ]
    if len(catalogue_rows) != 787:
        raise RuntimeError("Lesson07 source-catalogue row count differs")
    catalogue = {str(row["entity_id"]): row for row in catalogue_rows}
    if len(catalogue) != len(catalogue_rows):
        raise RuntimeError("Lesson07 source-catalogue identities are not unique")

    source_soup = BeautifulSoup(NORMALIZED.read_bytes(), "html.parser")
    source_main = source_soup.select_one("main#quarto-document-content")
    if source_main is None:
        raise RuntimeError("Lesson07 normalized source main is missing")
    unit_ids = [str(node.get("data-o006-id")) for node in source_main.select("[data-o006-id]")]
    math_ids = [
        str(node.get("data-o006-math-id"))
        for node in source_main.select("[data-o006-math-id]")
    ]
    if unit_ids != [f"{DOCUMENT_ID}-U{i:04d}" for i in range(1, 400)]:
        raise RuntimeError("Lesson07 normalized unit identity sequence differs")
    if math_ids != [f"{DOCUMENT_ID}-M{i:04d}" for i in range(1, 149)]:
        raise RuntimeError("Lesson07 normalized math identity sequence differs")
    return catalogue, source_main


def catalogue_record(
    catalogue: dict[str, dict[str, object]], entity_id: str, record_type: str
) -> dict[str, object]:
    row = catalogue.get(entity_id)
    if row is None or row.get("record_type") != record_type:
        raise RuntimeError(f"Lesson07 catalogue identity differs: {entity_id}")
    if row.get("document_id") != DOCUMENT_ID:
        raise RuntimeError(f"Lesson07 catalogue document binding differs: {entity_id}")
    return row


def is_target_text_node(node: NavigableString) -> bool:
    text = str(node)
    if not text.strip():
        return False
    parent = node.parent
    if (
        parent is None
        or parent.name in {"script", "style", "code"}
        or parent.find_parent(["script", "style", "code"]) is not None
        or parent.find_parent(class_="math") is not None
        or "math" in (parent.get("class") or [])
    ):
        return False
    return bool(re.search(r"[A-Za-z]", text))


def bind_target_segments(
    main: Tag,
    rows: list[dict[str, str]],
    catalogue: dict[str, dict[str, object]],
) -> tuple[dict[str, dict[str, str]], dict[str, NavigableString]]:
    expected_ids = [f"{DOCUMENT_ID}-S{i:04d}" for i in range(1, SEGMENT_COUNT + 1)]
    if len(rows) != SEGMENT_COUNT or [row.get("segment_id") for row in rows] != expected_ids:
        raise RuntimeError("Lesson07 translated segment boundary differs")
    nodes = [node for node in main.find_all(string=True) if is_target_text_node(node)]
    if len(nodes) != SEGMENT_COUNT:
        raise RuntimeError("Lesson07 target translatable-node count differs")

    by_id: dict[str, dict[str, str]] = {}
    target_nodes: dict[str, NavigableString] = {}
    for row, node in zip(rows, nodes):
        segment_id = row["segment_id"]
        source = row["source_text"]
        target = row["target_text"]
        if (
            row.get("document_id") != DOCUMENT_ID
            or row.get("component_id") != "Lesson07"
            or row.get("status") != "translated"
            or not target.strip()
            or sha256(source.encode("utf-8")) != row.get("source_sha256")
            or str(node) != target
        ):
            raise RuntimeError(f"Lesson07 translation binding differs: {segment_id}")
        entry = catalogue_record(catalogue, segment_id, "segment")
        if (
            entry.get("segment_id") != segment_id
            or entry.get("source_text") != source
            or entry.get("source_sha256") != row["source_sha256"]
        ):
            raise RuntimeError(f"Lesson07 catalogue segment binding differs: {segment_id}")
        short_id = segment_id.rsplit("-", 1)[1]
        expected_target_sha256 = TRANSLATION_TARGET_SHA256.get(short_id)
        if expected_target_sha256 and sha256(target.encode("utf-8")) != expected_target_sha256:
            raise RuntimeError(f"Lesson07 admitted translation target differs: {segment_id}")
        by_id[segment_id] = row
        target_nodes[segment_id] = node
    return by_id, target_nodes


def boundary(text: str) -> tuple[str, str]:
    leading = re.match(r"^\s*", text)
    trailing = re.search(r"\s*$", text)
    assert leading is not None and trailing is not None
    return leading.group(0), trailing.group(0)


def segment_surface(
    rows: dict[str, dict[str, str]],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
) -> dict[str, object]:
    segment_id = f"{DOCUMENT_ID}-{short_id}"
    row = rows.get(segment_id)
    if row is None:
        raise RuntimeError(f"Lesson07 correction segment missing: {segment_id}")
    source = row["source_text"]
    target = row["target_text"]
    if (
        row["status"] != "translated"
        or not target.strip()
        or source == target
        or sha256(source.encode("utf-8")) != row["source_sha256"]
    ):
        raise RuntimeError(f"Lesson07 correction segment differs: {segment_id}")
    expected_target_sha256 = TRANSLATION_TARGET_SHA256.get(short_id)
    target_sha256 = sha256(target.encode("utf-8"))
    if expected_target_sha256 is None or target_sha256 != expected_target_sha256:
        raise RuntimeError(f"Lesson07 correction target binding differs: {segment_id}")
    entry = catalogue_record(catalogue, segment_id, "segment")
    if entry.get("source_sha256") != row["source_sha256"]:
        raise RuntimeError(f"Lesson07 correction catalogue segment differs: {segment_id}")
    return {
        "surface": "translation-segment",
        "segment_id": segment_id,
        "unit_id": entry.get("parent_unit_id"),
        "source_surface_sha256": row["source_sha256"],
        "target_surface_sha256": target_sha256,
    }


def replace_segment(
    rows: dict[str, dict[str, str]],
    target_nodes: dict[str, NavigableString],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    target: str,
) -> dict[str, object]:
    segment_id = f"{DOCUMENT_ID}-{short_id}"
    row = rows.get(segment_id)
    node = target_nodes.get(segment_id)
    if row is None or node is None or str(node) != row["target_text"]:
        raise RuntimeError(f"Lesson07 target segment identity differs: {segment_id}")
    expected_target_sha256 = TRANSLATION_TARGET_SHA256.get(short_id)
    translation_sha256 = sha256(row["target_text"].encode("utf-8"))
    if expected_target_sha256 is None or translation_sha256 != expected_target_sha256:
        raise RuntimeError(f"Lesson07 target segment source differs: {segment_id}")
    if boundary(target) != boundary(row["target_text"]):
        raise RuntimeError(f"Lesson07 corrected segment whitespace differs: {segment_id}")
    if not target.strip() or target == row["target_text"]:
        raise RuntimeError(f"Lesson07 corrected segment makes no change: {segment_id}")
    entry = catalogue_record(catalogue, segment_id, "segment")
    node.replace_with(NavigableString(target))
    return {
        "surface": "translation-segment-target-repair",
        "segment_id": segment_id,
        "unit_id": entry.get("parent_unit_id"),
        "source_surface_sha256": row["source_sha256"],
        "translation_surface_sha256": translation_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def math_node(main: Tag, short_id: str) -> tuple[str, Tag]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson07 correction math identity differs: {math_id}")
    return math_id, nodes[0]


def apply_math(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    target: str,
) -> dict[str, object]:
    math_id, node = math_node(main, short_id)
    source = node.get_text()
    expected_sha256 = MATH_SOURCE_SHA256[short_id]
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson07 correction math source differs: {math_id}")
    entry = catalogue_record(catalogue, math_id, "math")
    if entry.get("source_sha256") != expected_sha256 or entry.get("source_text") != source:
        raise RuntimeError(f"Lesson07 catalogue math binding differs: {math_id}")
    if source == target:
        raise RuntimeError(f"Lesson07 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "unit_id": entry.get("parent_unit_id"),
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def math_evidence(
    source_main: Tag,
    catalogue: dict[str, dict[str, object]],
    short_id: str,
) -> dict[str, object]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = source_main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson07 source math evidence missing: {math_id}")
    source = nodes[0].get_text()
    expected_sha256 = MATH_SOURCE_SHA256[short_id]
    entry = catalogue_record(catalogue, math_id, "math")
    if (
        sha256(source.encode("utf-8")) != expected_sha256
        or entry.get("source_sha256") != expected_sha256
        or entry.get("source_text") != source
    ):
        raise RuntimeError(f"Lesson07 source math evidence differs: {math_id}")
    return {
        "surface": "source-math-evidence",
        "math_id": math_id,
        "unit_id": entry.get("parent_unit_id"),
        "source_surface_sha256": expected_sha256,
        "authority_unchanged": True,
    }


def unit_evidence(
    main: Tag,
    source_main: Tag,
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    *,
    target_unchanged: bool,
) -> dict[str, object]:
    unit_id = f"{DOCUMENT_ID}-{short_id}"
    source_nodes = source_main.select(f'[data-o006-id="{unit_id}"]')
    target_nodes = main.select(f'[data-o006-id="{unit_id}"]')
    if len(source_nodes) != 1 or len(target_nodes) != 1:
        raise RuntimeError(f"Lesson07 unit evidence identity differs: {unit_id}")
    source_text = source_nodes[0].get_text()
    expected_sha256 = UNIT_SOURCE_SHA256[short_id]
    entry = catalogue_record(catalogue, unit_id, "unit")
    if (
        sha256(source_text.encode("utf-8")) != expected_sha256
        or entry.get("text_sha256") != expected_sha256
    ):
        raise RuntimeError(f"Lesson07 unit source evidence differs: {unit_id}")
    evidence: dict[str, object] = {
        "surface": "source-unit-evidence",
        "unit_id": unit_id,
        "source_surface_sha256": expected_sha256,
        "authority_unchanged": True,
    }
    if target_unchanged:
        target_text = target_nodes[0].get_text()
        if target_text != source_text:
            raise RuntimeError(f"Lesson07 protected target unit differs: {unit_id}")
        evidence["target_surface_sha256"] = expected_sha256
        evidence["target_unchanged"] = True
    return evidence


def preserved_segment_evidence(
    rows: dict[str, dict[str, str]],
    target_nodes: dict[str, NavigableString],
    catalogue: dict[str, dict[str, object]],
    short_id: str,
) -> dict[str, object]:
    surface = segment_surface(rows, catalogue, short_id)
    segment_id = str(surface["segment_id"])
    if str(target_nodes[segment_id]) != rows[segment_id]["target_text"]:
        raise RuntimeError(f"Lesson07 preserved target segment differs: {segment_id}")
    return {
        **surface,
        "surface": "preserved-translation-segment-evidence",
        "target_unchanged": True,
    }


def add_adjacent_note(
    main: Tag,
    defect_number: int,
    anchor_short_id: str,
    expected_next_short_id: str | None,
    note_class: str,
    text: str,
) -> dict[str, object]:
    anchor_id = f"{DOCUMENT_ID}-{anchor_short_id}"
    nodes = main.select(f'[data-o006-id="{anchor_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson07 correction-note anchor differs: {anchor_id}")
    anchor = nodes[0]
    following = anchor.find_next_sibling()
    expected_next = (
        f"{DOCUMENT_ID}-{expected_next_short_id}" if expected_next_short_id else None
    )
    actual_next = str(following.get("data-o006-id")) if isinstance(following, Tag) else None
    if actual_next != expected_next:
        raise RuntimeError(f"Lesson07 correction-note adjacency differs: {anchor_id}")
    cid = correction_id(defect_number)
    if main.select(f'[data-o006-correction-id="{cid}"]'):
        raise RuntimeError(f"Lesson07 correction note already exists: {cid}")

    source_marker = "\n".join(
        (anchor_id, anchor.name, str(anchor.parent.get("data-o006-id")), str(expected_next))
    )
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction", note_class]
    note["data-o006-correction-id"] = cid
    note["role"] = "note"
    note.append(NavigableString(text))
    anchor.insert_after(note)
    target_marker = source_marker + "\n" + str(note)
    return {
        "surface": "adjacent-correction-note",
        "unit_id": anchor_id,
        "next_unit_id": expected_next,
        "source_surface_sha256": sha256(source_marker.encode("utf-8")),
        "target_surface_sha256": sha256(target_marker.encode("utf-8")),
    }


def verify_authority_assets() -> dict[str, dict[str, object]]:
    evidence: dict[str, dict[str, object]] = {}
    for short_id, spec in ASSETS.items():
        path = spec["path"]
        assert isinstance(path, Path)
        payload = path.read_bytes()
        if len(payload) != spec["bytes"] or sha256(payload) != spec["sha256"]:
            raise RuntimeError(f"Lesson07 authority asset differs: {short_id}")
        evidence[short_id] = {
            "authority_asset_bytes": len(payload),
            "authority_asset_sha256": sha256(payload),
            "authority_asset_unchanged": True,
        }
    return evidence


def replace_asset_alt(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
    short_id: str,
    authority_evidence: dict[str, object],
) -> dict[str, object]:
    spec = ASSETS[short_id]
    asset_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'img[data-o006-asset-id="{asset_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson07 asset target identity differs: {asset_id}")
    image = nodes[0]
    source_alt = str(image.get("alt") or "")
    if (
        source_alt != spec["source_alt"]
        or image.get("src") != spec["src"]
        or image.get("data-o006-id") != spec["unit_id"]
        or image.parent is None
        or image.parent.get("data-o006-id") != spec["parent_unit_id"]
    ):
        raise RuntimeError(f"Lesson07 asset target binding differs: {asset_id}")
    entry = catalogue_record(catalogue, asset_id, "asset")
    catalogue_alt_hash = sha256(
        (
            json.dumps([source_alt], ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
    )
    if (
        entry.get("source_ref") != spec["src"]
        or entry.get("first_parent_unit_id") != spec["parent_unit_id"]
        or entry.get("alt_texts") != [source_alt]
        or entry.get("alt_texts_sha256") != catalogue_alt_hash
    ):
        raise RuntimeError(f"Lesson07 asset catalogue binding differs: {asset_id}")
    target_alt = str(spec["target_alt"])
    image["alt"] = target_alt
    return {
        "surface": "attribute",
        "asset_id": asset_id,
        "unit_id": spec["unit_id"],
        "parent_unit_id": spec["parent_unit_id"],
        "attribute": "alt",
        "source_ref": spec["src"],
        "source_surface_sha256": sha256(source_alt.encode("utf-8")),
        "target_surface_sha256": sha256(target_alt.encode("utf-8")),
        **authority_evidence,
    }


def replace_code_comment(
    main: Tag,
    catalogue: dict[str, dict[str, object]],
) -> dict[str, object]:
    unit_id = f"{DOCUMENT_ID}-U0353"
    nodes = main.select(f'code[data-o006-id="{unit_id}"]')
    if len(nodes) != 1:
        raise RuntimeError("Lesson07 inverse-information code unit differs")
    code = nodes[0]
    source_unit = code.get_text()
    expected_unit_sha256 = UNIT_SOURCE_SHA256["U0353"]
    entry = catalogue_record(catalogue, unit_id, "unit")
    if (
        sha256(source_unit.encode("utf-8")) != expected_unit_sha256
        or entry.get("text_sha256") != expected_unit_sha256
        or source_unit.count("se=sqrt(diag(solve(I)))") != 1
    ):
        raise RuntimeError("Lesson07 inverse-information code evidence differs")
    comments = code.select("span.do")
    source_comment = "## standard errors = sqrt(1/I.inv[p,p])"
    target_comment = "## standard errors = sqrt(I.inv[p,p])"
    if len(comments) != 1 or comments[0].get_text() != source_comment:
        raise RuntimeError("Lesson07 inverse-information code comment differs")
    comments[0].clear()
    comments[0].append(NavigableString(target_comment))
    target_unit = code.get_text()
    if target_unit.count("se=sqrt(diag(solve(I)))") != 1:
        raise RuntimeError("Lesson07 code-comment repair altered executing expression")
    return {
        "surface": "code-comment",
        "unit_id": unit_id,
        "source_unit_text_sha256": expected_unit_sha256,
        "target_unit_text_sha256": sha256(target_unit.encode("utf-8")),
        "source_surface_sha256": sha256(source_comment.encode("utf-8")),
        "target_surface_sha256": sha256(target_comment.encode("utf-8")),
        "executing_expression_sha256": sha256(
            b"se=sqrt(diag(solve(I)))"
        ),
        "executing_expression_unchanged": True,
    }


def record(
    defect_number: int,
    surfaces: list[dict[str, object]],
    note: str,
    *,
    evidence: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson07 defect has no target repair: D{defect_number:03d}")
    row: dict[str, object] = {
        "correction_id": correction_id(defect_number),
        "source_defect_id": f"L07-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }
    if evidence:
        row["evidence"] = evidence
    return row


def apply_lesson07_corrections(
    main: Tag, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    """Apply exactly L07-D001..D012 to an already translated Lesson 07 DOM."""

    catalogue, source_main = verify_frozen_evidence()
    rows_by_id, target_nodes = bind_target_segments(main, rows, catalogue)
    authority_assets = verify_authority_assets()

    records: list[dict[str, object]] = []

    records.append(record(
        1,
        [
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0028",
                ". Namun, konsistensi saja tidak cukup untuk menyimpulkan konvergensi "
                "nilai harapan. Jika keluarga penduga memenuhi integrabilitas seragam, "
                "maka ketika ",
            ),
            add_adjacent_note(
                main,
                1,
                "U0038",
                None,
                "uniform-integrability-note",
                "Catatan koreksi: integrabilitas seragam (uniform integrability; UI), "
                "bersama konvergensi dalam peluang ke θ, menghasilkan konvergensi L¹; "
                "karena itu E(θ̂ₙ) → θ. Tanpa syarat tambahan ini, konsistensi saja "
                "tidak menjaga nilai harapan.",
            ),
        ],
        "require uniform integrability before deriving expectation convergence from consistency",
        evidence=[
            unit_evidence(
                main, source_main, catalogue, "U0038", target_unchanged=False
            )
        ],
    ))

    records.append(record(
        2,
        [
            apply_math(
                main,
                catalogue,
                "M0043",
                r"\[\begin{align*}"
                "\n"
                r"  I_n(\theta)=-E_{\theta}\left[\frac{d^2}{d\theta^2}\ell_n(\theta)\right]"
                "\n"
                r"\end{align*}\]",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0180",
                ", kita juga dapat menghampiri informasi teramati (observed information) ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0193",
                " akan menghampiri informasi teramati dan mengembalikannya dalam objek ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0196",
                " adalah hampiran informasi teramati pada titik optimum; dengan syarat "
                "keteraturan, besaran ini dapat dipakai sebagai hampiran plug-in untuk "
                "membentuk selang kepercayaan asimtotik 95% bagi parameter ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0201",
                "Jika terdapat dua parameter atau lebih, optimisasi numerik dalam R "
                "serta hampiran numerik matriks informasi teramati ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0209",
                " menghampiri matriks informasi teramati pada titik optimum.",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0215",
                "Untuk mencari selang kepercayaan bagi setiap parameter tersebut, kita "
                "menggunakan invers matriks informasi teramati ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0230",
                "informasi Fisher per pengamatan",
            ),
        ],
        "distinguish expected Fisher information from the observed Hessian returned by optim",
        evidence=[
            math_evidence(source_main, catalogue, "M0102"),
            math_evidence(source_main, catalogue, "M0146"),
            math_evidence(source_main, catalogue, "M0147"),
            math_evidence(source_main, catalogue, "M0148"),
        ],
    ))

    records.append(record(
        3,
        [
            apply_math(
                main,
                catalogue,
                "M0088",
                r"\[\begin{align*}"
                "\n"
                r"  \bar{x}\pm 1.96 \sqrt{\frac{\bar{x}(1-\bar{x})}{n}}"
                r"=0.6\pm 1.96\sqrt{\frac{0.6(1-0.6)}{10}}"
                r"=0.6\pm 0.3036=(0.2964, 0.9036)"
                "\n"
                r"\end{align*}\]",
            )
        ],
        "restore the missing 1.96 factor while preserving the correct Bernoulli endpoints",
    ))

    records.append(record(
        4,
        [
            apply_math(
                main,
                catalogue,
                "M0102",
                r"\[\begin{align*}"
                "\n"
                r"  \frac{d^2}{d\theta^2}\ell_n(\theta)"
                r"&=\frac{n}{\theta^2}-\frac{2\sum x_i}{\theta^3},\\"
                "\n"
                r"  I_n(\theta)"
                r"&=-E_{\theta}\left[\frac{d^2}{d\theta^2}\ell_n(\theta)\right]"
                r"=\frac{n}{\theta^2},\\"
                "\n"
                r"  I_n(\hat{\theta})"
                r"&=\frac{n}{\hat{\theta}^2}=\frac{n}{\bar{x}^2}"
                r"=\frac{n^3}{(\sum x_i)^2}."
                "\n"
                r"\end{align*}\]",
            ),
            apply_math(
                main,
                catalogue,
                "M0104",
                r"\[\hat{\theta}\pm 1.96\sqrt{\frac{1}{I_n(\hat{\theta})}}"
                r"=\bar{x}\pm 1.96\sqrt{\frac{\bar{x}^2}{n}}"
                r"=\bar{x}\pm 1.96\frac{\bar{x}}{\sqrt{n}}\]",
            ),
        ],
        "take the reciprocal information correctly in the exponential Wald interval",
    ))

    records.append(record(
        5,
        [
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0213",
                " adalah -6.564774 dan nilai dugaan MLE bagi ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0214",
                " adalah 12.773473.",
            ),
        ],
        "make the Normal-example prose agree with the frozen optimizer output",
        evidence=[
            unit_evidence(main, source_main, catalogue, "U0331", target_unchanged=True),
            unit_evidence(main, source_main, catalogue, "U0344", target_unchanged=True),
        ],
    ))

    records.append(record(
        6,
        [
            add_adjacent_note(
                main,
                6,
                "U0149",
                "U0154",
                "optimizer-domain-note",
                "Catatan domain: kode demonstrasi di bawah dibekukan sesuai sumber, "
                "tetapi pemanggilan optim tidak memaksakan domain parameter. Model "
                "Geometrik mensyaratkan 0 < p ≤ 1 dan model Normal mensyaratkan σ² > 0; "
                "gunakan reparameterisasi yang sah, fungsi objektif berpelindung, atau "
                "optimisasi berbatas. Kode konvergensi 0 hanya menyatakan penghentian "
                "algoritme, bukan bukti optimum global atau keamanan domain.",
            ),
            replace_asset_alt(
                main, catalogue, "A0001", authority_assets["A0001"]
            ),
            replace_asset_alt(
                main, catalogue, "A0002", authority_assets["A0002"]
            ),
        ],
        "qualify optimizer domains and complete the two frozen figures' alt descriptions",
        evidence=[
            unit_evidence(main, source_main, catalogue, short_id, target_unchanged=True)
            for short_id in ("U0194", "U0206", "U0224", "U0309", "U0325")
        ],
    ))

    records.append(record(
        7,
        [
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0177",
                "Dalam sejumlah kasus yang relatif sederhana, kita dapat membentuk "
                "selang kepercayaan 95% bagi parameter secara analitik dengan MLE sebagai "
                "pusatnya. Untuk itu, kita harus dapat mencari MLE secara analitik "
                "(dengan mengambil turunan pertama fungsi log-kemungkinan dan "
                "menyamakannya dengan nol), kemudian mencari informasi Fisher secara "
                "analitik pula (dengan mengambil turunan kedua fungsi log-kemungkinan, "
                "lalu menghitung nilai harapan terhadap ",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0198",
                "Jadi, selang kepercayaan 95% berdasarkan MLE bagi parameter ",
            ),
        ],
        "state that the confidence interval targets the parameter and is centered by the MLE",
    ))

    records.append(record(
        8,
        [
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0010",
                " untuk optimisasi numerik. Pernyataan ikhtisar sumber tentang selang "
                "bootstrap parametrik dan nonparametrik, metode Delta, inferensi "
                "transformasi dengan bootstrap, serta contoh t dan Pareto bersifat "
                "antisipatif dan tidak didukung oleh isi Pelajaran 07 yang tersedia. "
                "Isi sebenarnya mencakup sifat MLE, selang Wald asimtotik skalar dan "
                "vektor, serta demonstrasi numerik Geometrik dan Normal. Mari kita mulai.",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0236",
                "Ringkasan sumber menyatakan bahwa bootstrap parametrik dan nonparametrik "
                "telah dipelajari melalui data t dan Pareto, tetapi materi tersebut tidak "
                "terdapat dalam isi Pelajaran 07 yang tersedia.",
            ),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0237",
                "Topik bootstrap, metode Delta, serta contoh t dan Pareto merupakan "
                "materi lanjutan, bukan keterampilan yang telah diajarkan dalam pelajaran ini.",
            ),
        ],
        "label the absent bootstrap, Delta, t and Pareto claims as stale or forward-looking scope",
    ))

    records.append(record(
        9,
        [
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0138",
                "Untuk xᵢ ≥ 0 dan θ > 0, fungsi kepadatan peluang (PDF)-nya adalah ",
            )
        ],
        "call the exponential surface a density and state its support and parameter domain",
        evidence=[
            math_evidence(source_main, catalogue, "M0090"),
            math_evidence(source_main, catalogue, "M0093"),
        ],
    ))

    records.append(record(
        10,
        [replace_code_comment(main, catalogue)],
        "take the square root of the inverse-information diagonal without another reciprocal",
    ))

    records.append(record(
        11,
        [
            segment_surface(rows_by_id, catalogue, short_id)
            for short_id in (
                "S0049",
                "S0061",
                "S0089",
                "S0099",
                "S0131",
                "S0152",
                "S0155",
                "S0169",
            )
        ]
        + [
            apply_math(
                main,
                catalogue,
                "M0098",
                r"\[\begin{align*}"
                "\n"
                r"  \frac{d}{d\theta}\ell(\theta)"
                r"=-\frac{n}{\theta}+\frac{\sum x_i}{\theta^2}"
                "\n"
                r"\end{align*}\]",
            )
        ],
        "repair the nine mechanically proved grammar, duplication, capitalization and formula surfaces",
    ))

    records.append(record(
        12,
        [
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0019",
                "Parameter sebenarnya, ",
            ),
            apply_math(main, catalogue, "M0002", r"\(\theta_0\)"),
            replace_segment(
                rows_by_id,
                target_nodes,
                catalogue,
                "S0020",
                ", berada di bagian dalam ruang parameter, bukan pada batasnya. Syarat "
                "ini menyangkut ruang parameter dan tidak sama dengan himpunan dukungan data.",
            ),
        ],
        "replace the support confusion with the true parameter's interior-point condition",
        evidence=[
            preserved_segment_evidence(
                rows_by_id, target_nodes, catalogue, "S0021"
            )
        ],
    ))

    expected_correction_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(123, 135)]
    expected_findings = [f"L07-D{i:03d}" for i in range(1, 13)]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson07 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson07 correction/finding binding differs")
    if len({str(row["correction_id"]) for row in records}) != len(records):
        raise RuntimeError("Lesson07 correction identities are not unique")
    return records
