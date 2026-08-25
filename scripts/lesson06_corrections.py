#!/usr/bin/env python3
"""Apply and register every admitted Lesson 06 target-only correction."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path(__file__).resolve().parents[1]
FINDINGS = ROOT / "working" / "lesson06_source_findings.md"
DOCUMENT_ID = "O006-PSU-007"
FIRST_CORRECTION_ORDINAL = 113
AUTHORITY_ASSET = (
    ROOT / "authority" / "assets" / "stat415" / "lesson06" / "assets" / "ci_1.png"
)
AUTHORITY_ASSET_BYTES = 67_496
AUTHORITY_ASSET_SHA256 = "2f50c34c6a91381f3700c728b7a85797d39e2eceae4a2cbd9542003b79adab8f"
FIGURE_ALT_SOURCE = "Standard normal curve showing the 1-alpha area centered in the middle."
FIGURE_ALT_TARGET = (
    "Kurva normal baku: luas tengah 1−α berada di antara nilai kritis tetap "
    "−z_(α/2) dan +z_(α/2); masing-masing ekor kiri dan kanan memiliki luas α/2."
)
FIGURE_NOTE = (
    "Catatan koreksi Gambar 6.1: kedua titik batas adalah nilai kritis tetap "
    "−z_(α/2) dan +z_(α/2) (z huruf kecil), bukan peubah acak Z; "
    "masing-masing ekor mempunyai peluang α/2."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def correction_id(defect_number: int) -> str:
    return f"O006-PSU-ADV-{FIRST_CORRECTION_ORDINAL + defect_number - 1:04d}"


def verify_authority_asset() -> None:
    payload = AUTHORITY_ASSET.read_bytes()
    if len(payload) != AUTHORITY_ASSET_BYTES or sha256(payload) != AUTHORITY_ASSET_SHA256:
        raise RuntimeError("Lesson06 authority PNG differs")


def math_node(main: Tag, short_id: str) -> tuple[str, Tag]:
    math_id = f"{DOCUMENT_ID}-{short_id}"
    nodes = main.select(f'[data-o006-math-id="{math_id}"]')
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson06 correction math identity differs: {math_id}")
    return math_id, nodes[0]


def verify_math(main: Tag, short_id: str, expected_sha256: str) -> None:
    math_id, node = math_node(main, short_id)
    source = node.get_text()
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson06 protected math source differs: {math_id}")


def apply_math(main: Tag, short_id: str, expected_sha256: str, target: str) -> dict[str, object]:
    target = target.replace(r"\n", "\n")
    math_id, node = math_node(main, short_id)
    source = node.get_text()
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise RuntimeError(f"Lesson06 correction math source differs: {math_id}")
    if source == target:
        raise RuntimeError(f"Lesson06 correction makes no math change: {math_id}")
    node.clear()
    node.append(NavigableString(target))
    return {
        "surface": "math",
        "math_id": math_id,
        "source_surface_sha256": expected_sha256,
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def segment_surfaces(rows: list[dict[str, str]], short_ids: list[str]) -> list[dict[str, object]]:
    by_id = {row["segment_id"]: row for row in rows}
    surfaces: list[dict[str, object]] = []
    for short_id in short_ids:
        segment_id = f"{DOCUMENT_ID}-{short_id}"
        row = by_id.get(segment_id)
        if row is None:
            raise RuntimeError(f"Lesson06 correction segment missing: {segment_id}")
        source = row["source_text"]
        target = row["target_text"]
        if row["status"] != "translated" or not target.strip():
            raise RuntimeError(f"Lesson06 correction segment unfinished: {segment_id}")
        if sha256(source.encode("utf-8")) != row["source_sha256"]:
            raise RuntimeError(f"Lesson06 correction source binding differs: {segment_id}")
        if source == target:
            raise RuntimeError(f"Lesson06 admitted prose correction is unchanged: {segment_id}")
        surfaces.append({
            "surface": "translation-segment",
            "segment_id": segment_id,
            "source_surface_sha256": row["source_sha256"],
            "target_surface_sha256": sha256(target.encode("utf-8")),
        })
    return surfaces


def replace_attribute(
    main: Tag,
    selector: str,
    identity: dict[str, object],
    attribute: str,
    expected: str,
    target: str,
) -> dict[str, object]:
    nodes = main.select(selector)
    if len(nodes) != 1:
        raise RuntimeError(f"Lesson06 attribute identity differs: {selector}")
    node = nodes[0]
    source = str(node.get(attribute) or "")
    if source != expected:
        raise RuntimeError(f"Lesson06 {attribute} source differs: {selector}: {source!r}")
    if source == target:
        raise RuntimeError(f"Lesson06 correction makes no attribute change: {selector}")
    node[attribute] = target
    return {
        "surface": "attribute",
        **identity,
        "attribute": attribute,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
    }


def add_figure_correction_note(main: Tag) -> dict[str, object]:
    unit_id = f"{DOCUMENT_ID}-U0051"
    asset_id = f"{DOCUMENT_ID}-A0001"
    figures = main.select(f'[data-o006-id="{unit_id}"]')
    images = main.select(f'img[data-o006-asset-id="{asset_id}"]')
    if len(figures) != 1 or len(images) != 1:
        raise RuntimeError("Lesson06 Figure 6.1 identity differs")
    figure = figures[0]
    image = images[0]
    following = figure.find_next_sibling()
    if (
        figure.get("id") != "fig-standardnormal"
        or image.get("src") != "assets/ci_1.png"
        or following is None
        or following.get("data-o006-id") != f"{DOCUMENT_ID}-U0057"
        or main.select(f'[data-o006-correction-id="{correction_id(3)}"]')
    ):
        raise RuntimeError("Lesson06 Figure 6.1 adjacent-note surface differs")

    source_marker = "\n".join((unit_id, asset_id, str(image.get("src")), str(following.get("data-o006-id"))))
    fragment = BeautifulSoup("", "html.parser")
    note = fragment.new_tag("p")
    note["class"] = ["target-only-correction", "figure-critical-value-note"]
    note["data-o006-correction-id"] = correction_id(3)
    note["role"] = "note"
    note.append(NavigableString(FIGURE_NOTE))
    figure.insert_after(note)
    target_marker = source_marker + "\n" + str(note)
    return {
        "surface": "adjacent-correction-note",
        "unit_id": unit_id,
        "asset_id": asset_id,
        "authority_asset_sha256": AUTHORITY_ASSET_SHA256,
        "authority_asset_unchanged": True,
        "source_surface_sha256": sha256(source_marker.encode("utf-8")),
        "target_surface_sha256": sha256(target_marker.encode("utf-8")),
    }


def mark_proof_role(main: Tag) -> dict[str, object]:
    unit_id = f"{DOCUMENT_ID}-U0067"
    nodes = main.select(f'section[data-o006-id="{unit_id}"]')
    if len(nodes) != 1:
        raise RuntimeError("Lesson06 proof-section identity differs")
    node = nodes[0]
    source_classes = list(node.get("class", []))
    if (
        node.get("id") != "proof"
        or source_classes != ["level4"]
        or node.get("data-o006-semantic-role") is not None
        or node.get("data-o006-correction-id") is not None
    ):
        raise RuntimeError("Lesson06 proof-role source differs")
    source = str(node)
    source_contents = node.decode_contents()
    node["class"] = [*source_classes, "proof"]
    node["data-o006-semantic-role"] = "proof"
    node["data-o006-correction-id"] = correction_id(10)
    if node.decode_contents() != source_contents:
        raise RuntimeError("Lesson06 proof-role correction altered proof contents")
    target = str(node)
    return {
        "surface": "semantic-role",
        "unit_id": unit_id,
        "source_surface_sha256": sha256(source.encode("utf-8")),
        "target_surface_sha256": sha256(target.encode("utf-8")),
        "source_class": source_classes,
        "target_class": list(node.get("class", [])),
        "semantic_role": "proof",
        "content_unchanged": True,
    }


def record(defect_number: int, surfaces: list[dict[str, object]], note: str) -> dict[str, object]:
    if not surfaces:
        raise RuntimeError(f"Lesson06 defect has no target evidence: D{defect_number:03d}")
    if any("correction_id" in surface for surface in surfaces):
        raise RuntimeError(f"Lesson06 surface duplicates correction identity: D{defect_number:03d}")
    return {
        "correction_id": correction_id(defect_number),
        "source_defect_id": f"L06-D{defect_number:03d}",
        "status": "applied-target-only",
        "replacement_count": len(surfaces),
        "surface": surfaces[0]["surface"] if len(surfaces) == 1 else "multiple",
        "surfaces": surfaces,
        "note": note,
    }


def apply_lesson06_corrections(
    main: Tag, rows: list[dict[str, str]]
) -> list[dict[str, object]]:
    finding_ids = re.findall(r"^## (L06-D\d{3})\b", FINDINGS.read_text("utf-8"), re.MULTILINE)
    expected_findings = [f"L06-D{i:03d}" for i in range(1, 11)]
    if finding_ids != expected_findings:
        raise RuntimeError(f"Lesson06 admitted finding sequence differs: {finding_ids}")
    verify_authority_asset()

    records: list[dict[str, object]] = []
    records.append(record(
        1,
        segment_surfaces(rows, ["S0014", "S0015", "S0016"]),
        "distinguish the random point estimator from its realized point estimate",
    ))
    records.append(record(
        2,
        [
            apply_math(
                main,
                "M0042",
                "1148c13eecd010e97352e51fc52e4dfba4f93e93ee487e9a492f8bfbcb5868f9",
                r"\[P\left[\bar{X}-z_{\alpha/2}\left(\frac{\sigma}{\sqrt{n}}\right)\le \mu\le \bar{X}+z_{\alpha/2}\left(\frac{\sigma}{\sqrt{n}}\right)\right]=1-\alpha\]",
            ),
        ],
        "restore the missing equality before 1-alpha",
    ))
    records.append(record(
        3,
        [add_figure_correction_note(main)],
        "identify the lowercase-z fixed critical values without altering the authority PNG",
    ))

    verify_math(
        main,
        "M0082",
        "c0fe9c8cb5abf4cf5dca5807f82e8640165896b2f3519a2e018e5b904bcb2575",
    )
    records.append(record(
        4,
        [
            apply_math(
                main,
                "M0073",
                "076fe4f2b3343862e1f405ac9ef306c1b6b2267de1ddb7112d358a5ef8c6fa34",
                r"\[q_p=F_{\chi^2_4}^{-1}(p),\qquad P\left[q_{0.05}\le \frac{2Y}{\theta}\le q_{0.95}\right]=0.90\]",
            ),
            apply_math(
                main,
                "M0074",
                "b5c28ac8e5836e9e9d6a01172e9cf38551c33b736203c7b68ea53bfd356c1d81",
                r"\[\frac{1}{q_{0.95}}\le \frac{\theta}{2Y}\le \frac{1}{q_{0.05}}\]",
            ),
            apply_math(
                main,
                "M0075",
                "7918a5a31986f840a00e7d6922c074f6cdf020883cc016771da4bb6db0e201ae",
                r"\[\frac{2Y}{q_{0.95}}\le \theta \le \frac{2Y}{q_{0.05}}\]",
            ),
            apply_math(
                main,
                "M0077",
                "5b4cfee0a22335dbe5739780981701d74ff4b0917ae13dc6ba2aa4af7c6f4ef1",
                r"\[\left[\frac{2Y}{q_{0.95}}, \frac{2Y}{q_{0.05}}\right]\]",
            ),
            *segment_surfaces(rows, ["S0132"]),
        ],
        "define q_p as the lower-tail chi-square(4) quantile and preserve the correct numerical endpoints",
    ))
    records.append(record(
        5,
        [
            apply_math(
                main,
                "M0086",
                "fa1507c9afd351ead256ed8a2b2f524bd90c7ec1a7920c27a621aca6ec88ed28",
                r"\[T_n=\frac{\hat{\theta}-\theta}{\widehat{\mathrm{SE}}(\hat{\theta})}\xrightarrow{d}N(0,1)\]",
            ),
            apply_math(
                main,
                "M0087",
                "609f605763ed06f8020272f8578ee0dfba9fe9dca892bb5a12cf1d4075b76dca",
                r"\(T_n=\frac{\hat{\theta}-\theta}{\widehat{\mathrm{SE}}(\hat{\theta})}\)",
            ),
            *segment_surfaces(
                rows,
                [
                    "S0144", "S0146", "S0147", "S0148", "S0149", "S0150",
                    "S0151", "S0152", "S0153", "S0154", "S0155",
                ],
            ),
        ],
        "require studentized convergence and a valid estimated standard error; exact unbiasedness is unnecessary",
    ))

    verify_math(
        main,
        "M0099",
        "22542cfa33ad5473eb586c895ea07d9dabb2556cc772ac165d87bce9a50224fb",
    )
    records.append(record(
        6,
        [
            apply_math(
                main,
                "M0098",
                "708a190c66d9347098b7c15059176196763042b19b230fe94357104b8619dfc0",
                r"\(\widehat{\mathrm{SE}}(\bar{X})=\frac{s}{\sqrt{64}}=\frac{16}{8}=2.\)",
            ),
            *segment_surfaces(rows, ["S0161", "S0165", "S0166"]),
        ],
        "correct the estimated standard error to s/sqrt(64)=16/8=2 and retain the correct interval",
    ))
    records.append(record(
        7,
        [
            apply_math(
                main,
                "M0102",
                "3a1a07ec1712fdf04b60066f50b983cb95f7ca87c4c516857ab213e8d4e62197",
                r"\(\bar{X}\pm t_{\alpha/2,n-1}\cdot \frac{S}{\sqrt{n}}\)",
            ),
            *segment_surfaces(rows, ["S0175"]),
        ],
        "state the exact iid-Normal t interval with n-1 degrees of freedom",
    ))
    records.append(record(
        8,
        [
            replace_attribute(
                main,
                f'[data-o006-id="{DOCUMENT_ID}-U0051"]',
                {"unit_id": f"{DOCUMENT_ID}-U0051"},
                "alt",
                FIGURE_ALT_SOURCE,
                FIGURE_ALT_TARGET,
            ),
            replace_attribute(
                main,
                f'img[data-o006-asset-id="{DOCUMENT_ID}-A0001"]',
                {"asset_id": f"{DOCUMENT_ID}-A0001", "unit_id": f"{DOCUMENT_ID}-U0055"},
                "alt",
                FIGURE_ALT_SOURCE,
                FIGURE_ALT_TARGET,
            ),
        ],
        "describe the central area, both tails, and corrected critical points in Indonesian alt text",
    ))
    records.append(record(
        9,
        segment_surfaces(
            rows,
            ["S0060", "S0110", "S0113", "S0124", "S0131", "S0133", "S0174"],
        ),
        "repair all seven mechanically proved grammar, duplication, punctuation, and typo surfaces",
    ))
    records.append(record(
        10,
        [mark_proof_role(main)],
        "add proof semantics without deleting, rewriting, or reordering the proof",
    ))

    expected_correction_ids = [f"O006-PSU-ADV-{i:04d}" for i in range(113, 123)]
    if [str(row["correction_id"]) for row in records] != expected_correction_ids:
        raise RuntimeError("Lesson06 correction identity sequence differs")
    if [str(row["source_defect_id"]) for row in records] != expected_findings:
        raise RuntimeError("Lesson06 correction/finding binding differs")
    if len({str(row["correction_id"]) for row in records}) != len(records):
        raise RuntimeError("Lesson06 correction identities are not unique")
    return records
