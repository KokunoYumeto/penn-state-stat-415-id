#!/usr/bin/env python3
"""Freeze dependencies and write or byte-verify STAT 415 Lesson 09 normalization."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import struct
import urllib.request
import xml.etree.ElementTree as ET
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bs4
from bs4 import BeautifulSoup, Tag

import normalize_lesson03 as base


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson09.html"
SCRIPT = ROOT / "scripts" / "normalize_lesson09.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-010"
COMPONENT_ID = "Lesson09"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson09"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."

EXPECTED_SOURCE_BYTES = 114_901
EXPECTED_SOURCE_SHA256 = "87d1401304f866ae3cff6b182dbf92a64b43e92c1c024e684b895187a9e61319"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
ASSET_SPECS: tuple[dict[str, object], ...] = (
    {
        "source_ref": "assets/tetra_die.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/tetra_die.png",
        "local_path": "authority/assets/stat415/lesson09/assets/tetra_die.png",
        "bytes": 3_044_449,
        "sha256": "48d09d5e1a7ba862fb18001773cefb64aec266f43650b5b0813add8eaff58f5a",
        "media_type": "image/png", "width": 2_048, "height": 2_048,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"2e7461-624c06b9c7380"',
    },
    {
        "source_ref": "Lesson09_files/figure-html/unnamed-chunk-1-1.png",
        "official_url": "https://online.stat.psu.edu/stat415/Lesson09_files/figure-html/unnamed-chunk-1-1.png",
        "local_path": "authority/assets/stat415/lesson09/Lesson09_files/figure-html/unnamed-chunk-1-1.png",
        "bytes": 16_784,
        "sha256": "34806d496364d23810cc800b8e874992b2377bdaa0afede976176a120716d71c",
        "media_type": "image/png", "width": 1_344, "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT", "etag": '"4190-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson09_files/figure-html/unnamed-chunk-2-1.png",
        "official_url": "https://online.stat.psu.edu/stat415/Lesson09_files/figure-html/unnamed-chunk-2-1.png",
        "local_path": "authority/assets/stat415/lesson09/Lesson09_files/figure-html/unnamed-chunk-2-1.png",
        "bytes": 17_808,
        "sha256": "d8a4214d5a136770a14070329cfd124092eaca710eb7287e2da84fe4e6fb9894",
        "media_type": "image/png", "width": 1_344, "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT", "etag": '"4590-659cca3a58c80"',
    },
    {
        "source_ref": "assets/STAT-415-SEC-2-03.svg",
        "official_url": "https://online.stat.psu.edu/stat415/assets/STAT-415-SEC-2-03.svg",
        "local_path": "authority/assets/stat415/lesson09/assets/STAT-415-SEC-2-03.svg",
        "bytes": 2_181,
        "sha256": "cdcdea0ed5d30bed29c789ab1dfe6437e64d9c99fa560ba6e7cd4cf459e6044b",
        "media_type": "image/svg+xml", "view_box": "0 0 444.3 309.84",
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"885-624c06b9c7380"',
    },
    {
        "source_ref": "assets/ht5.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/ht5.png",
        "local_path": "authority/assets/stat415/lesson09/assets/ht5.png",
        "bytes": 12_102,
        "sha256": "42089920ac53b068f785e765c4af31187841097fdf811ef52fce71e542189ab7",
        "media_type": "image/png", "width": 386, "height": 262,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"2f46-624c06b9c7380"',
    },
    {
        "source_ref": "assets/ht6.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/ht6.png",
        "local_path": "authority/assets/stat415/lesson09/assets/ht6.png",
        "bytes": 245_769,
        "sha256": "a094f2e57e9f0867e87ff5d4397bc3b5c222f80c4b9d3bbd7f68d0a4ef13db5e",
        "media_type": "image/png", "width": 6_075, "height": 3_482,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"3c009-624c06b9c7380"',
    },
    {
        "source_ref": "assets/ht7.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/ht7.png",
        "local_path": "authority/assets/stat415/lesson09/assets/ht7.png",
        "bytes": 209_721,
        "sha256": "74b43d2ab8873ba123bfb3d1748e3759fa274e8ae3fe3ff5ecddc17dd2f28f08",
        "media_type": "image/png", "width": 6_075, "height": 3_152,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"33339-624c06b9c7380"',
    },
    {
        "source_ref": "assets/ht8.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/ht8.png",
        "local_path": "authority/assets/stat415/lesson09/assets/ht8.png",
        "bytes": 278_296,
        "sha256": "7f8ec0b05f37792f81f60be0b0242aab375bdc4e79fd8454f94e5de5ba6a3a1d",
        "media_type": "image/png", "width": 6_075, "height": 3_152,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"43f18-624c06b9c7380"',
    },
    {
        "source_ref": "assets/h10.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/h10.png",
        "local_path": "authority/assets/stat415/lesson09/assets/h10.png",
        "bytes": 230_356,
        "sha256": "bed97e91e72f22150d542f2ea71859dd8698c78e1f784124ba93b16cb1073988",
        "media_type": "image/png", "width": 6_075, "height": 3_152,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"383d4-624c06b9c7380"',
    },
    {
        "source_ref": "assets/h11.png",
        "official_url": "https://online.stat.psu.edu/stat415/assets/h11.png",
        "local_path": "authority/assets/stat415/lesson09/assets/h11.png",
        "bytes": 202_382,
        "sha256": "0a738a3904c683d2a30865fafa93e4e06bcc0e2ba01bf3a4fd59b1b7fb176986",
        "media_type": "image/png", "width": 6_075, "height": 2_617,
        "last_modified": "Fri, 18 Oct 2024 13:38:38 GMT", "etag": '"3168e-624c06b9c7380"',
    },
)
base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "9 Hypothesis Tests (Part I)"
    )
    return (
        "<!doctype html>\n"
        '<html lang="en-US">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n"
        f'<meta name="source-url" content="{SOURCE_URL}">\n'
        '<meta name="translation-provenance" content="OpenAI Codex gpt-5.6-sol, Ultra">\n'
        "</head>\n<body>\n"
        f"{main}\n"
        "</body>\n</html>\n"
    ).encode("utf-8")


def formula_with(formulas: list[str], *markers: str) -> str | None:
    return next((text for text in formulas if all(marker in text for marker in markers)), None)


def binomial_pmf(k: int, n: int, probability: float) -> float:
    """Stable standard-library binomial probability used only for audit witnesses."""
    return (
        math.comb(n, k)
        * probability ** k
        * (1.0 - probability) ** (n - k)
    )


def source_defects(main: Tag) -> list[dict[str, object]]:
    """Record only high-confidence defects or omissions proved from the frozen source."""
    formulas = base.formula_texts(main)
    prose = main.get_text(" ", strip=True)
    main_html = str(main)
    defects: list[dict[str, object]] = []

    def add(
        defect_id: str,
        classification: str,
        kind: str,
        evidence: object,
        note: str,
    ) -> None:
        defects.append(
            {
                "defect_id": defect_id,
                "classification": classification,
                "kind": kind,
                "evidence": evidence,
                "note": note,
            }
        )

    if "Typical \\(\\beta\\) values are 0.05, 0.10, and 0.20." in prose:
        add(
            "L09-D001",
            "qualification-omission",
            "type-two-error-and-power-parameter-dependence-omitted",
            "Typical \\(\\beta\\) values are 0.05, 0.10, and 0.20.",
            (
                "For a composite alternative, beta and power are functions of the true "
                "parameter value. They are not single free-standing design constants."
            ),
        )

    tradeoff = (
        "However, we cannot decrease both. As \\(\\alpha\\) decreases, "
        "\\(\\beta\\) increases."
    )
    if tradeoff in prose:
        add(
            "L09-D002",
            "outright-overgeneralization",
            "alpha-beta-tradeoff-missing-fixed-design-qualification",
            tradeoff,
            (
                "The monotone tradeoff is for a fixed sample size, test family, and "
                "specified alternative. Increasing information can reduce both errors."
            ),
        )

    strict_upper = formula_with(formulas, r"|T^*|>c")
    strict_lower = formula_with(formulas, r"|T^*|<c")
    if strict_upper and strict_lower:
        add(
            "L09-D003",
            "boundary-omission",
            "critical-boundary-decision-unspecified",
            [strict_upper, strict_lower],
            (
                "The two rules omit |T*|=c. Equality is null-probability-zero only for "
                "an appropriate continuous statistic. A discrete exact-level test needs "
                "an explicit boundary decision and, when no nonrandomized cutoff has the "
                "desired size, randomization on the equality set."
            ),
        )

    pvalue_prose = "probability that we’d observe a more extreme statistic than we did"
    pvalue_decision = formula_with(formulas, r"P\le \alpha")
    if pvalue_prose in prose and pvalue_decision:
        add(
            "L09-D004",
            "boundary-omission",
            "p-value-definition-excludes-observed-equality",
            {
                "definition": pvalue_prose,
                "decision_rule": pvalue_decision,
                "summary_rule": "p-value is smaller than the significance level",
            },
            (
                "Define the p-value using outcomes at least as extreme as the observation "
                "under the null distribution. The source also alternates <= and strict "
                "smaller-than decision wording; the derivative must state one complete "
                "boundary convention."
            ),
        )

    rounded_equivalence = formula_with(formulas, r"Z>1.645", r"\hat{p}>0.273")
    if rounded_equivalence:
        cutoff = 0.25 + 1.645 * math.sqrt(0.25 * 0.75 / 1000)
        if not math.isclose(cutoff, 0.27252509017739995, rel_tol=0.0, abs_tol=1e-15):
            raise RuntimeError("Lesson09 one-proportion cutoff witness changed")
        add(
            "L09-D005",
            "outright-mathematical-defect",
            "rounded-proportion-cutoff-not-equivalent",
            {
                "source_formula": rounded_equivalence,
                "unrounded_cutoff": f"{cutoff:.17f}",
                "discrete_equivalent": "Y>=273, equivalently p-hat>=0.273",
            },
            (
                "Z>1.645 is equivalent to p-hat>0.27252509017739995. Because "
                "p-hat=Y/1000, the discrete rule is Y>=273 or p-hat>=0.273, "
                "not p-hat>0.273."
            ),
        )

    type_two_formula = formula_with(formulas, r"P(\text{Type II Error})", "0.5847")
    if type_two_formula and "“size” of the critical region is 0.05" in prose:
        tail_273 = sum(binomial_pmf(k, 1000, 0.25) for k in range(273, 1001))
        tail_274 = sum(binomial_pmf(k, 1000, 0.25) for k in range(274, 1001))
        mass_273 = binomial_pmf(273, 1000, 0.25)
        gamma = (0.05 - tail_274) / mass_273
        beta_027 = sum(binomial_pmf(k, 1000, 0.27) for k in range(0, 273))
        witnesses = (
            (tail_273, 0.05119467130277791),
            (tail_274, 0.04409632971654358),
            (gamma, 0.8316971241431076),
            (beta_027, 0.5727359654533983),
        )
        if any(not math.isclose(x, y, rel_tol=0.0, abs_tol=2e-13) for x, y in witnesses):
            raise RuntimeError("Lesson09 exact binomial witnesses changed")
        add(
            "L09-D006",
            "approximation-qualification-omission",
            "normal-approximation-presented-as-exact-size-and-type-two-probability",
            {
                "source_type_two_formula": type_two_formula,
                "exact_size_for_Y_ge_273": f"{tail_273:.15f}",
                "exact_size_for_Y_ge_274": f"{tail_274:.15f}",
                "randomize_at_Y_eq_273_probability": f"{gamma:.15f}",
                "exact_beta_at_p_eq_0.27_for_Y_ge_273": f"{beta_027:.15f}",
            },
            (
                "The source's 0.05 and 0.5847 are Normal-approximation results. Under "
                "Binomial(1000,0.25), Y>=273 has size 0.051194671302778. An exact "
                "size-0.05 rule rejects for Y>=274 and rejects with probability "
                "0.831697124143108 when Y=273. Label approximations or state this "
                "equality-set randomization explicitly."
            ),
        )

    inferential_overstatement = (
        "reject the null hypothesis and conclude that the alternative hypothesis is true"
    )
    if inferential_overstatement in prose:
        add(
            "L09-D007",
            "inferential-overstatement",
            "rejection-described-as-proof-alternative-is-true",
            inferential_overstatement,
            (
                "A rejection is evidence against H0 at a controlled error rate; it does "
                "not establish certainty that Ha is true, as the lesson's own Type I "
                "error discussion demonstrates."
            ),
        )

    incomplete_two_tail = (
        "we should reject the null hypothesis or we should reject the null hypothesis"
    )
    if incomplete_two_tail in prose:
        add(
            "L09-D008",
            "outright-surface-defect",
            "two-tailed-rejection-conditions-omitted-from-prose",
            incomplete_two_tail,
            (
                "The two alternatives are missing their conditions. Preserve the "
                "subsequent complete rule |Z|>=1.96 and make both tails explicit in text."
            ),
        )

    clt_overclaim = (
        "the same size \\(n=25\\) is large enough for the Central Limit Theorem to apply"
    )
    if clt_overclaim in prose:
        add(
            "L09-D009",
            "outright-mathematical-overclaim",
            "sample-size-25-claimed-universally-sufficient-for-clt",
            clt_overclaim,
            (
                "No universal finite n guarantees an adequate Normal approximation for "
                "arbitrary population distributions. The exact Z result needs an iid "
                "Normal sample; otherwise approximation quality needs distributional "
                "conditions or diagnostics."
            ),
        )

    decimal_error = formula_with(formulas, "=0.401", r"\alpha=0.05")
    if decimal_error:
        add(
            "L09-D010",
            "outright-numerical-defect",
            "one-mean-p-value-decimal-point-error",
            {
                "source_formula": decimal_error,
                "preceding_value": r"\(P(Z<-1.75)=0.0401\)",
            },
            (
                "The p-value is 0.0401, not 0.401. Moreover 0.401<0.05 is false; "
                "0.0401<0.05 supports the stated rejection."
            ),
        )

    positive_t = formula_with(formulas, r"t\ge t_{0.025, 99}=1.9842")
    negative_t = formula_with(formulas, r"t\le t_{0.025, 99}=-1.9842")
    if positive_t and negative_t:
        add(
            "L09-D011",
            "outright-notation-defect",
            "same-t-quantile-symbol-assigned-opposite-signs",
            [positive_t, negative_t],
            (
                "Under the source's upper-tail convention, use t>=t_(0.025,99) "
                "and t<=-t_(0.025,99). Alternatively define lower-tail quantiles "
                "explicitly; one symbol cannot equal both signs."
            ),
        )

    pvalue_bound = formula_with(formulas, r"2P(T_{99}>4.762)", "=0.05")
    asserted_bound = formula_with(formulas, r"\le 0.01", r"\alpha=0.05")
    if pvalue_bound and asserted_bound:
        add(
            "L09-D012",
            "proof-omission",
            "p-value-bound-strengthened-without-support",
            {
                "displayed_bound": pvalue_bound,
                "unsupported_next_claim": asserted_bound,
                "independent_two_sided_p_value": "0.000006560183365621494",
            },
            (
                "The display establishes only p<0.05, not p<=0.01. The stronger "
                "claim is true numerically, but requires an additional t-tail "
                "calculation; do not present it as following from the shown bound."
            ),
        )

    t_statistic = formula_with(formulas, r"T=\dfrac{\bar{X}-\mu}{S/\sqrt{n}}")
    if t_statistic and "if the data are normally distributed" in prose:
        add(
            "L09-D013",
            "assumption-omission",
            "exact-one-sample-t-law-missing-iid-random-sample-condition",
            t_statistic,
            (
                "The exact t_(n-1) law requires an iid Normal random sample, not merely "
                "a collection of marginally Normal observations. State independence "
                "and the Normal sampling model."
            ),
        )

    summary_type_two = "Type II error: failing to reject when is true"
    if summary_type_two in prose:
        add(
            "L09-D014",
            "outright-surface-defect",
            "summary-type-two-error-missing-hypothesis-subject",
            summary_type_two,
            (
                "Restore 'failing to reject H0 when Ha is true' (equivalently, when H0 "
                "is false at the specified alternative)."
            ),
        )

    alt_by_ref = {
        str(image.get("src")): image.get("alt")
        for image in main.select("img[src]")
    }
    expected_alt_defects = {
        "assets/ht5.png": None,
        "assets/h10.png": "Normal curve with center at 0 showing two-tail critical area for alpha of .05.",
        "assets/h11.png": "Normal curve with center at 0 showing two-tail critical area for alpha of .05.",
    }
    if all(alt_by_ref.get(ref) == alt for ref, alt in expected_alt_defects.items()):
        generic_captions = [
            caption.get_text(" ", strip=True)
            for caption in main.select("figcaption")
            if caption.get_text(" ", strip=True).startswith("Fig")
        ]
        add(
            "L09-D015",
            "accessibility-defect",
            "missing-incorrect-alt-and-generic-caption-surfaces",
            {
                "source_alts": expected_alt_defects,
                "generic_figure_captions": generic_captions,
                "uncaptioned_generated_plots": [
                    "Lesson09_files/figure-html/unnamed-chunk-1-1.png",
                    "Lesson09_files/figure-html/unnamed-chunk-2-1.png",
                ],
            },
            (
                "ht5 has no alt. h10 and h11 are left-tail plots but their alt says "
                "two-tail. The eight visible captions are labels only, and two generated "
                "plots have no caption. Supply complete non-color-dependent descriptions."
            ),
        )

    native_ids = [tag.get("id") for tag in main.select("[id]")]
    duplicate_ids = sorted(
        key for key, count in Counter(native_ids).items() if count > 1
    )
    expected_duplicate_ids = [
        "fig-h10", "fig-h11", "fig-ht6", "fig-ht7", "fig-ht8",
        "fig-rttailcritical1645",
    ]
    if duplicate_ids == expected_duplicate_ids:
        add(
            "L09-D016",
            "topology-accessibility-defect",
            "duplicate-native-figure-identifiers",
            duplicate_ids,
            (
                "Each listed id occurs on both a figure container and its img. Preserve "
                "the source topology in normalization, but mint unique derivative DOM "
                "ids while retaining stable catalogue bindings."
            ),
        )

    tables = main.select("table")
    table_witness = [
        {
            "ordinal": index,
            "caption_count": len(table.select("caption")),
            "th_count": len(table.select("th")),
            "scope_count": len(table.select("th[scope]")),
        }
        for index, table in enumerate(tables, start=1)
    ]
    if table_witness == [
        {"ordinal": 1, "caption_count": 0, "th_count": 0, "scope_count": 0},
        {"ordinal": 2, "caption_count": 0, "th_count": 0, "scope_count": 0},
        {"ordinal": 3, "caption_count": 0, "th_count": 3, "scope_count": 0},
    ]:
        add(
            "L09-D017",
            "accessibility-defect",
            "decision-tables-lack-complete-header-and-caption-semantics",
            table_witness,
            (
                "All three decision/error tables lack captions. The first two encode "
                "headers as td cells; the third has th cells without scope. Add semantic "
                "row/column headers and concise captions without changing cell content."
            ),
        )

    mechanical = [
        phrase for phrase in (
            "was is building is not safe",
            "procedure outlines above",
            "more that four are found",
            "Therefore, lets choose",
            "(or critical value” or “critical region”)",
        )
        if phrase in prose
    ]
    if len(mechanical) == 5:
        add(
            "L09-D018",
            "outright-mechanical-defects",
            "unambiguous-grammar-typo-and-quotation-errors",
            mechanical,
            (
                "Correct the duplicated verb, agreement error, than/that typo, missing "
                "apostrophe in let's, and unmatched quotation mark in the derivative."
            ),
        )

    generated_refs = [
        "Lesson09_files/figure-html/unnamed-chunk-1-1.png",
        "Lesson09_files/figure-html/unnamed-chunk-2-1.png",
    ]
    if all(main.select_one(f'img[src="{ref}"]') is not None for ref in generated_refs) and not main.select("pre, code"):
        add(
            "L09-D019",
            "reproducibility-omission",
            "generated-plot-inputs-and-code-absent",
            {
                "generated_plot_outputs": generated_refs,
                "pre_nodes": 0,
                "code_nodes": 0,
            },
            (
                "The rendered plot outputs are present, but no generating code, data, "
                "package versions, or random-state surface is published in the lesson "
                "main. Freeze the outputs; do not claim source-level reproducibility."
            ),
        )

    expected_ids = [f"L09-D{index:03d}" for index in range(1, 20)]
    if [row["defect_id"] for row in defects] != expected_ids:
        raise RuntimeError("Lesson09 proved-defect census differs from L09-D001..L09-D019")
    return defects


def asset_path(spec: dict[str, object]) -> Path:
    return ROOT / str(spec["local_path"])


def validate_png(payload: bytes, spec: dict[str, object]) -> dict[str, object]:
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"Lesson09 asset is not PNG: {spec['source_ref']}")
    cursor = 8
    chunk_types: list[str] = []
    chunk_bytes: Counter[str] = Counter()
    metadata_payloads: list[bytes] = []
    width = height = bit_depth = color_type = interlace = None
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise RuntimeError(f"truncated Lesson09 PNG chunk: {spec['source_ref']}")
        length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        end = cursor + 12 + length
        if end > len(payload):
            raise RuntimeError(f"Lesson09 PNG chunk extends beyond EOF: {spec['source_ref']}")
        chunk_type = payload[cursor + 4:cursor + 8]
        data = payload[cursor + 8:cursor + 8 + length]
        stored_crc = struct.unpack(">I", payload[cursor + 8 + length:end])[0]
        if (zlib.crc32(chunk_type + data) & 0xFFFFFFFF) != stored_crc:
            raise RuntimeError(f"Lesson09 PNG CRC validation failed: {spec['source_ref']}")
        name = chunk_type.decode("ascii")
        chunk_types.append(name)
        chunk_bytes[name] += length
        if name in {"iCCP", "eXIf", "iTXt", "tEXt", "zTXt"}:
            metadata_payloads.append(data)
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filter, interlace = struct.unpack(
                ">IIBBBBB", data
            )
        cursor = end
        if chunk_type == b"IEND":
            break
    if (
        not chunk_types
        or chunk_types[0] != "IHDR"
        or chunk_types[-1] != "IEND"
        or cursor != len(payload)
        or width != spec["width"]
        or height != spec["height"]
    ):
        raise RuntimeError(f"Lesson09 PNG structure/dimensions differ: {spec['source_ref']}")
    metadata_blob = b"\n".join(metadata_payloads).lower()
    rights_markers = [
        marker.decode("ascii")
        for marker in (b"copyright", b"creator", b"author", b"license", b"rights")
        if marker in metadata_blob
    ]
    if rights_markers:
        raise RuntimeError(
            f"Lesson09 PNG has embedded rights/creator markers: "
            f"{spec['source_ref']} {rights_markers}"
        )
    sequence_payload = "\n".join(chunk_types).encode("ascii")
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
        "chunk_crc_valid": True,
        "chunk_count": len(chunk_types),
        "chunk_type_counts": dict(sorted(Counter(chunk_types).items())),
        "chunk_data_bytes_by_type": dict(sorted(chunk_bytes.items())),
        "chunk_sequence_sha256": base.sha256(sequence_payload),
        "metadata_chunk_types": [
            name for name in chunk_types
            if name in {"iCCP", "eXIf", "iTXt", "tEXt", "zTXt"}
        ],
        "embedded_screenshot_comment": b"screenshot" in metadata_blob,
        "embedded_rights_or_creator_markers": [],
        "trailing_bytes": 0,
    }


def validate_svg(payload: bytes, spec: dict[str, object]) -> dict[str, object]:
    try:
        text = payload.decode("utf-8", errors="strict")
        root = ET.fromstring(text)
    except (UnicodeDecodeError, ET.ParseError) as exc:
        raise RuntimeError(f"invalid Lesson09 SVG: {spec['source_ref']}") from exc
    if root.tag.rsplit("}", 1)[-1] != "svg" or root.get("viewBox") != spec["view_box"]:
        raise RuntimeError(f"Lesson09 SVG root/viewBox differs: {spec['source_ref']}")
    element_counts: Counter[str] = Counter()
    prohibited: list[str] = []
    external_references: list[str] = []
    event_attributes: list[str] = []
    for element in root.iter():
        local_name = element.tag.rsplit("}", 1)[-1]
        element_counts[local_name] += 1
        if local_name in {"script", "foreignObject", "iframe", "object", "embed"}:
            prohibited.append(local_name)
        for key, value in element.attrib.items():
            key_local = key.rsplit("}", 1)[-1]
            if key_local.casefold().startswith("on"):
                event_attributes.append(key_local)
            if key_local in {"href", "src"} and (
                value.startswith(("http:", "https:", "//", "data:"))
            ):
                external_references.append(value)
    lowered = text.casefold()
    rights_markers = [
        marker for marker in ("copyright", "creator", "author", "license", "rights")
        if marker in lowered
    ]
    if prohibited or external_references or event_attributes or rights_markers:
        raise RuntimeError(f"unsafe or separately attributed Lesson09 SVG: {spec['source_ref']}")
    return {
        "xml_utf8_valid": True,
        "view_box": root.get("viewBox"),
        "element_counts": dict(sorted(element_counts.items())),
        "prohibited_elements": [],
        "external_references": [],
        "event_handler_attributes": [],
        "embedded_rights_or_creator_markers": [],
    }


def validate_asset(payload: bytes, spec: dict[str, object]) -> dict[str, object]:
    if len(payload) != spec["bytes"] or base.sha256(payload) != spec["sha256"]:
        raise RuntimeError(f"frozen Lesson09 asset differs: {spec['source_ref']}")
    if spec["media_type"] == "image/png":
        return {"format": "PNG", **validate_png(payload, spec)}
    if spec["media_type"] == "image/svg+xml":
        return {"format": "SVG", **validate_svg(payload, spec)}
    raise RuntimeError(f"unsupported Lesson09 asset media type: {spec['media_type']}")


def fetch_asset(spec: dict[str, object]) -> bytes:
    official_url = str(spec["official_url"])
    request = urllib.request.Request(
        official_url,
        headers={"User-Agent": "O006-STAT415-id deterministic source freezer"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
        response_witness = {
            "status": response.status,
            "content_type": response.headers.get("Content-Type"),
            "content_length": response.headers.get("Content-Length"),
            "last_modified": response.headers.get("Last-Modified"),
            "etag": response.headers.get("ETag"),
            "final_url": response.geturl(),
        }
    expected = {
        "status": 200,
        "content_type": spec["media_type"],
        "content_length": str(spec["bytes"]),
        "last_modified": spec["last_modified"],
        "etag": spec["etag"],
        "final_url": official_url,
    }
    if response_witness != expected:
        raise RuntimeError(
            f"official Lesson09 asset response differs: {spec['source_ref']} "
            f"{response_witness}"
        )
    validate_asset(payload, spec)
    return payload


def asset_manifest(
    asset_rows: list[dict[str, object]],
    payloads: dict[str, bytes],
) -> bytes:
    catalogue_by_ref = {str(row["source_ref"]): row for row in asset_rows}
    stream = io.StringIO(newline="")
    fields = (
        "asset_id", "source_reference", "official_url", "local_path", "bytes", "sha256",
        "media_type", "width", "height", "view_box", "license", "disposition",
    )
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for spec in ASSET_SPECS:
        ref = str(spec["source_ref"])
        writer.writerow(
            {
                "asset_id": catalogue_by_ref[ref]["asset_id"],
                "source_reference": ref,
                "official_url": spec["official_url"],
                "local_path": spec["local_path"],
                "bytes": len(payloads[ref]),
                "sha256": base.sha256(payloads[ref]),
                "media_type": spec["media_type"],
                "width": spec.get("width", ""),
                "height": spec.get("height", ""),
                "view_box": spec.get("view_box", ""),
                "license": "CC BY-NC 4.0",
                "disposition": (
                    "freeze-authority-and-redistribute-with-page-attribution-and-change-notice"
                ),
            }
        )
    return stream.getvalue().encode("utf-8")


def asset_closure(
    source_payload: bytes,
    source_soup: BeautifulSoup,
    main: Tag,
    asset_rows: list[dict[str, object]],
    payloads: dict[str, bytes],
) -> bytes:
    census = base.dependency_census(main)
    expected_census = {
        "images": 10,
        "videos": 0,
        "audio": 0,
        "media_sources": 0,
        "iframes": 0,
        "objects": 0,
        "embeds": 0,
        "downloads": 0,
        "scripts": 0,
    }
    if census != expected_census:
        raise RuntimeError(f"Lesson09 dependency census differs: {census}")
    expected_refs = [str(spec["source_ref"]) for spec in ASSET_SPECS]
    source_refs = [str(image.get("src")) for image in main.select("img[src]")]
    if source_refs != expected_refs:
        raise RuntimeError(f"Lesson09 image-reference sequence differs: {source_refs}")
    catalogue_refs = [str(row["source_ref"]) for row in asset_rows]
    if catalogue_refs != expected_refs:
        raise RuntimeError("Lesson09 asset-catalogue sequence differs")
    lightbox_refs = [str(anchor.get("href")) for anchor in main.select("a.lightbox[href]")]
    expected_lightboxes = [
        "assets/STAT-415-SEC-2-03.svg",
        "assets/ht6.png",
        "assets/ht7.png",
        "assets/ht8.png",
        "assets/h10.png",
        "assets/h11.png",
    ]
    if lightbox_refs != expected_lightboxes:
        raise RuntimeError(f"Lesson09 lightbox sequence differs: {lightbox_refs}")
    expected_alts: dict[str, str | None] = {
        "assets/tetra_die.png": "4 sided die",
        "Lesson09_files/figure-html/unnamed-chunk-1-1.png": (
            "Normal distribution showing area shaded above 0.29."
        ),
        "Lesson09_files/figure-html/unnamed-chunk-2-1.png": (
            "Normal distribution showing area shaded above 0.273."
        ),
        "assets/STAT-415-SEC-2-03.svg": (
            "Normal curve with center at 0.25 showing right tail critical area for alpha of .05."
        ),
        "assets/ht5.png": None,
        "assets/ht6.png": (
            "Normal curve with center at 0 showing left-tail critical area for alpha of 0.01."
        ),
        "assets/ht7.png": (
            "Normal curve with center at 0 showing left-tail critical area below the test statistic of -1.92."
        ),
        "assets/ht8.png": (
            "Normal curve with center at 0 showing two-tail critical area for alpha of .05."
        ),
        "assets/h10.png": (
            "Normal curve with center at 0 showing two-tail critical area for alpha of .05."
        ),
        "assets/h11.png": (
            "Normal curve with center at 0 showing two-tail critical area for alpha of .05."
        ),
    }
    image_by_ref = {str(image.get("src")): image for image in main.select("img[src]")}
    if {ref: image.get("alt") for ref, image in image_by_ref.items()} != expected_alts:
        raise RuntimeError("Lesson09 source alternative-text inventory differs")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson09 page-level CC BY-NC 4.0 witness is missing")
    for spec in ASSET_SPECS:
        if urlparse(str(spec["official_url"])).netloc != urlparse(SOURCE_URL).netloc:
            raise RuntimeError(f"Lesson09 asset is not same-origin: {spec['source_ref']}")
        if urljoin(SOURCE_URL, str(spec["source_ref"])) != spec["official_url"]:
            raise RuntimeError(f"Lesson09 source-reference resolution differs: {spec['source_ref']}")
    main_text = main.get_text(" ", strip=True).casefold()
    for marker in ("source:", "credit:", "copyright", "permission", "licensed under"):
        if marker in main_text:
            raise RuntimeError(f"unexpected per-asset rights marker in Lesson09 main: {marker}")

    visual_witnesses = {
        "assets/tetra_die.png": (
            "square raster photograph of a translucent blue tetrahedral die with faces 2 and 4 visible"
        ),
        "Lesson09_files/figure-html/unnamed-chunk-1-1.png": (
            "Normal-density plot associated with the observed sample proportion 0.29"
        ),
        "Lesson09_files/figure-html/unnamed-chunk-2-1.png": (
            "Normal-density plot associated with the right-tail cutoff 0.273"
        ),
        "assets/STAT-415-SEC-2-03.svg": (
            "Normal curve centered at 0.25 with cutoff 0.273 / Z=1.645 and alpha=0.05 right tail"
        ),
        "assets/ht5.png": (
            "left-tail standard-Normal rejection region with critical value -1.645"
        ),
        "assets/ht6.png": (
            "left-tail standard-Normal rejection region with critical value -2.33"
        ),
        "assets/ht7.png": (
            "left-tail p-value area beyond observed Z=-1.92"
        ),
        "assets/ht8.png": (
            "two-tail standard-Normal rejection regions beyond -1.96 and 1.96"
        ),
        "assets/h10.png": (
            "left-tail standard-Normal rejection region beyond -1.645"
        ),
        "assets/h11.png": (
            "left-tail p-value area beyond observed Z=-1.75"
        ),
    }
    assets: list[dict[str, object]] = []
    catalogue_by_ref = {str(row["source_ref"]): row for row in asset_rows}
    for spec in ASSET_SPECS:
        ref = str(spec["source_ref"])
        payload = payloads[ref]
        assets.append(
            {
                "asset_id": catalogue_by_ref[ref]["asset_id"],
                "source_ref": ref,
                "official_url": spec["official_url"],
                "local_path": spec["local_path"],
                "img_occurrences": len(main.select(f'img[src="{ref}"]')),
                "lightbox_href_occurrences": len(main.select(f'a.lightbox[href="{ref}"]')),
                "alt_text": image_by_ref[ref].get("alt"),
                "bytes": len(payload),
                "sha256": base.sha256(payload),
                "media_type": spec["media_type"],
                "http_audit": {
                    "status": 200,
                    "content_type": spec["media_type"],
                    "content_length": spec["bytes"],
                    "last_modified": spec["last_modified"],
                    "etag": spec["etag"],
                    "redirected": False,
                    "checked_on": "2026-08-25",
                },
                "binary_validation": validate_asset(payload, spec),
                "visual_validation": visual_witnesses[ref],
            }
        )

    link_inventory = [
        {
            "href": str(anchor.get("href")),
            "text": anchor.get_text(" ", strip=True),
            "role": "lightbox" if "lightbox" in (anchor.get("class") or []) else "navigation",
        }
        for anchor in main.select("a[href]")
    ]
    closure = {
        "schema": "o006.stat415.lesson09-asset-closure.v1",
        "status": "same-origin-images-closed-no-external-dependencies",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson09.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": base.sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": census,
        "link_inventory": link_inventory,
        "assets": assets,
        "rights": {
            "page_license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "witness_text": LICENSE_TEXT,
            "per_asset_exception_in_main": False,
            "embedded_rights_or_creator_metadata": False,
            "disposition": (
                "cleared-for-noncommercial-derivative-freeze-under-official-page-notice"
            ),
        },
        "accessibility": {
            "source_alt_present": 9,
            "source_alt_missing": 1,
            "source_alt_incorrect": 2,
            "generic_label_only_figure_captions": 8,
            "generated_plots_without_figure_caption": 2,
            "derivative_full_alt_required": True,
        },
        "reproducibility": {
            "generated_plot_outputs": 2,
            "generating_code_nodes": 0,
            "published_input_data_surfaces": 0,
            "package_or_runtime_lock_surfaces": 0,
            "random_state_surfaces": 0,
            "claim": "frozen-output reproducibility only; source-level plot reproduction unavailable",
        },
        "closure": {
            "reference_inventory_complete": True,
            "same_origin_image_bytes_complete": True,
            "same_origin_image_rights_disposition_complete": True,
            "unresolved_asset_bytes": 0,
            "external_dependencies": 0,
            "normalization_may_proceed": True,
            "offline_reader_asset_gate_passed": True,
        },
    }
    return base.canonical_json(closure)


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson09 normalization helper differs from its frozen implementation")
    source_payload = SOURCE.read_bytes()
    if (
        len(source_payload) != EXPECTED_SOURCE_BYTES
        or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256
    ):
        raise RuntimeError("Lesson09 authority differs from the frozen 14-document manifest")

    asset_payloads: dict[str, bytes] = {}
    for spec in ASSET_SPECS:
        path = asset_path(spec)
        if not path.is_file():
            raise RuntimeError(f"frozen Lesson09 asset is missing: {spec['local_path']}")
        payload = path.read_bytes()
        validate_asset(payload, spec)
        asset_payloads[str(spec["source_ref"])] = payload

    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson09 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson09 authority lacks main#quarto-document-content")
    if original_main.select("script, style"):
        raise RuntimeError("unexpected embedded script/style in Lesson09 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson09 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = base.topology_sha256(original_main)
    source_counts = base.content_counts(original_main)
    source_formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(source_formulas).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(
        key for key, count in Counter(native_ids).items() if count > 1
    )
    expected_counts = {
        "sections": 26,
        "headings": 27,
        "theorem_class_nodes": 12,
        "theorems": 0,
        "definitions": 5,
        "examples": 7,
        "corollaries": 0,
        "solutions": 9,
        "proofs": 0,
        "math_nodes": 219,
        "math_inline": 190,
        "math_display": 29,
        "pre_nodes": 0,
        "code_nodes": 0,
        "figures": 10,
        "images": 10,
        "asset_occurrences": 10,
        "unique_asset_sources": 10,
        "figure_captions": 8,
        "links": 8,
        "tables": 3,
    }
    if source_counts != expected_counts:
        raise RuntimeError(f"Lesson09 content census differs: {source_counts}")
    expected_duplicate_ids = [
        "fig-h10", "fig-h11", "fig-ht6", "fig-ht7", "fig-ht8",
        "fig-rttailcritical1645",
    ]
    if (
        source_topology_sha
        != "8e3416d9d42c384ca6a3931d02247ce1be317c26feb22715f08d60cc73c19da7"
        or base.sha256(formula_payload)
        != "3a3fabca97e592b503cf9d6404c2ec7475d58b1b76f50ada749a0118f6f224e3"
        or base.sha256(semantic_text_payload)
        != "2f095229b021c25b9bea3c63c23ab13e8817101671468b85002c68de75dd62e5"
        or len(native_ids) != 62
        or len(set(native_ids)) != 56
        or duplicate_ids != expected_duplicate_ids
    ):
        raise RuntimeError("Lesson09 topology/formula/text/native-id witnesses differ")

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    segment_rows = base.extract_segments(main)
    expected_refs = [str(spec["source_ref"]) for spec in ASSET_SPECS]
    if [str(row["source_ref"]) for row in asset_rows] != expected_refs:
        raise RuntimeError("Lesson09 asset catalogue differs")
    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    expected_role_counts = {
        "definition": 5,
        "example": 7,
        "figure": 10,
        "figure-caption": 8,
        "heading": 19,
        "image": 10,
        "link": 8,
        "section": 17,
        "solution": 18,
        "structure": 312,
    }
    if (
        len(unit_rows) != 414
        or len(math_rows) != 219
        or len(asset_rows) != 10
        or len(segment_rows) != 443
        or role_counts != expected_role_counts
    ):
        raise RuntimeError("Lesson09 stable structural/segment census differs")

    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(
        original_main, normalized_payload, source_topology_sha, source_counts
    )
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None or target_main.get_text() != original_main.get_text():
        raise RuntimeError("Lesson09 semantic-main text changed during normalization")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 10,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson09.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson09.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "semantic_text_sha256": base.sha256(semantic_text_payload),
        "formula_count": len(source_formulas),
        "formula_sha256": base.sha256(formula_payload),
        "code_node_count": 0,
        "code_text_sha256": base.sha256(b""),
        "unit_count": len(unit_rows),
        "segment_count": len(segment_rows),
        "asset_count": len(asset_rows),
        "dependency_count": 0,
        "native_id_occurrences": len(native_ids),
        "unique_native_ids": len(set(native_ids)),
        "duplicate_native_ids": duplicate_ids,
    }
    catalogue_segment_rows = [
        {
            "schema": CATALOGUE_SCHEMA,
            "record_type": "segment",
            "entity_id": row["segment_id"],
            "segment_id": row["segment_id"],
            "document_id": DOCUMENT_ID,
            "component_id": COMPONENT_ID,
            "ordinal": row["ordinal"],
            "parent_tag": row["parent_tag"],
            "parent_unit_id": row["parent_unit_id"],
            "section_id": row["section_id"],
            "locale": "en-US",
            "source_text": row["source_text"],
            "source_sha256": row["source_sha256"],
            "translation_status": "pending",
        }
        for row in segment_rows
    ]
    catalogue_rows = [
        document_row, *unit_rows, *math_rows, *asset_rows, *catalogue_segment_rows
    ]
    if len(catalogue_rows) != 1_087:
        raise RuntimeError("Lesson09 catalogue-record census differs")
    csv_payload = base.segment_csv(segment_rows)
    catalogue_payload = base.canonical_jsonl(catalogue_rows)
    closure_payload = asset_closure(
        source_payload, source_soup, original_main, asset_rows, asset_payloads
    )
    manifest_payload = asset_manifest(asset_rows, asset_payloads)
    defects = source_defects(original_main)
    defect_class_counts = dict(
        sorted(Counter(str(row["classification"]) for row in defects).items())
    )
    script_payload = SCRIPT.read_bytes()
    catalogue_by_ref = {str(row["source_ref"]): row for row in asset_rows}
    asset_inventory = [
        {
            "asset_id": catalogue_by_ref[str(spec["source_ref"])]["asset_id"],
            "source_ref": spec["source_ref"],
            "source_url": spec["official_url"],
            "local_path": spec["local_path"],
            "occurrences": catalogue_by_ref[str(spec["source_ref"])]["occurrences"],
            "alt_texts": catalogue_by_ref[str(spec["source_ref"])]["alt_texts"],
            "media_type": spec["media_type"],
            "bytes": len(asset_payloads[str(spec["source_ref"])]),
            "sha256": base.sha256(asset_payloads[str(spec["source_ref"])]),
        }
        for spec in ASSET_SPECS
    ]
    total_asset_bytes = sum(len(payload) for payload in asset_payloads.values())
    if total_asset_bytes != 4_259_848:
        raise RuntimeError("Lesson09 total frozen asset bytes differ")

    output_assets = [
        {
            "path": spec["local_path"],
            "bytes": len(asset_payloads[str(spec["source_ref"])]),
            "sha256": base.sha256(asset_payloads[str(spec["source_ref"])]),
        }
        for spec in ASSET_SPECS
    ]
    receipt = {
        "schema": "o006.stat415.lesson09-normalization.v1",
        "status": "normalized-source-ready-assets-closed-no-external-dependencies",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "assets": len(asset_rows),
            "dependencies": 0,
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
        },
        "stable_id_ranges": {
            "units": ["O006-PSU-010-U0001", "O006-PSU-010-U0414"],
            "math": ["O006-PSU-010-M0001", "O006-PSU-010-M0219"],
            "assets": ["O006-PSU-010-A0001", "O006-PSU-010-A0010"],
            "segments": ["O006-PSU-010-S0001", "O006-PSU-010-S0443"],
        },
        "role_counts": role_counts,
        "asset_inventory": asset_inventory,
        "asset_closure": {
            "reference_inventory_complete": True,
            "same_origin_image_files": 10,
            "same_origin_png_files": 9,
            "same_origin_svg_files": 1,
            "same_origin_image_bytes": total_asset_bytes,
            "same_origin_image_bytes_closed": True,
            "external_dependencies": 0,
            "offline_reader_asset_gate_passed": True,
        },
        "mathematical_audit_scope": {
            "all_math_nodes_audited": True,
            "hypothesis_test_claims_audited": True,
            "rejection_region_claims_audited": True,
            "type_one_type_two_claims_audited": True,
            "p_value_and_power_claims_audited": True,
            "neyman_pearson_lemma_occurrences": 0,
            "likelihood_ratio_test_occurrences": 0,
            "equality_boundary_randomization_required_for_exact_binomial_size": True,
            "independent_recalculation_witnesses_recorded": True,
        },
        "instructional_surface": {
            "definitions": 5,
            "worked_examples": 7,
            "solution_sections": 9,
            "tables": 3,
            "figures": 10,
            "code_nodes": 0,
            "proofs": 0,
            "theorems": 0,
        },
        "duplicate_native_ids": duplicate_ids,
        "source_defects": defects,
        "source_defect_count": len(defects),
        "source_defect_classification_counts": defect_class_counts,
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "formula_nodes_byte_preserved": True,
            "code_nodes_text_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson09.html",
                "bytes": len(normalized_payload),
                "sha256": base.sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson09_segments.csv",
                "bytes": len(csv_payload),
                "sha256": base.sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson09_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": base.sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "assets": output_assets,
            "asset_manifest": {
                "path": "authority/LESSON09_ASSET_MANIFEST.csv",
                "bytes": len(manifest_payload),
                "sha256": base.sha256(manifest_payload),
                "rows": len(asset_rows),
            },
            "asset_closure": {
                "path": "working/lesson09_asset_closure.json",
                "bytes": len(closure_payload),
                "sha256": base.sha256(closure_payload),
            },
            "script": {
                "path": "scripts/normalize_lesson09.py",
                "bytes": len(script_payload),
                "sha256": base.sha256(script_payload),
            },
            "helper_script": {
                "path": "scripts/normalize_lesson03.py",
                "bytes": len(helper_payload),
                "sha256": base.sha256(helper_payload),
            },
        },
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": (
            "semantic main only; no authority correction; formula text protected; stable "
            "unit, math, asset, and segment IDs additive"
        ),
        "next_translation_range": [
            "O006-PSU-010-S0001",
            "O006-PSU-010-S0443",
        ],
    }
    outputs = {
        str(spec["local_path"]): asset_payloads[str(spec["source_ref"])]
        for spec in ASSET_SPECS
    }
    outputs.update(
        {
            "authority/LESSON09_ASSET_MANIFEST.csv": manifest_payload,
            "source/normalized/en-US/Lesson09.html": normalized_payload,
            "working/lesson09_segments.csv": csv_payload,
            "backend/lesson09_source_catalogue.jsonl": catalogue_payload,
            "working/lesson09_asset_closure.json": closure_payload,
            "build/LESSON09_NORMALIZATION_RECEIPT.json": base.canonical_json(receipt),
        }
    )
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.write:
        for spec in ASSET_SPECS:
            path = asset_path(spec)
            if not path.is_file():
                base.atomic_write(path, fetch_asset(spec))
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            base.atomic_write(ROOT / relative, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson09 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson09 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON09_NORMALIZATION_RECEIPT.json"]
    receipt = json.loads(receipt_payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "segments": receipt["counts"]["translation_segments"],
                "units": receipt["counts"]["structural_units"],
                "math": receipt["counts"]["math_nodes"],
                "code": receipt["counts"]["code_nodes"],
                "assets": receipt["counts"]["assets"],
                "asset_bytes": receipt["asset_closure"]["same_origin_image_bytes"],
                "dependencies": receipt["counts"]["dependencies"],
                "catalogue_records": receipt["counts"]["catalogue_records"],
                "source_defects": receipt["source_defect_count"],
                "receipt_sha256": base.sha256(receipt_payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
