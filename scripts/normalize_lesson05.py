#!/usr/bin/env python3
"""Create or byte-verify the isolated normalized-source lane for STAT 415 Lesson 05."""

from __future__ import annotations

import argparse
import json
import struct
import zlib
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin, urlparse

import bs4
from bs4 import BeautifulSoup, Comment, Tag

import normalize_lesson03 as base


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "authority" / "upstream" / "stat415" / "Lesson05.html"
ASSET_ROOT = ROOT / "authority" / "assets" / "stat415" / "lesson05"
SCRIPT = ROOT / "scripts" / "normalize_lesson05.py"
HELPER_SCRIPT = ROOT / "scripts" / "normalize_lesson03.py"

DOCUMENT_ID = "O006-PSU-006"
COMPONENT_ID = "Lesson05"
SOURCE_URL = "https://online.stat.psu.edu/stat415/Lesson05"
CATALOGUE_SCHEMA = "o006.stat415.source-catalogue.v1"
LICENSE_TEXT = "Except where otherwise noted, content on this site is licensed under a CC BY-NC 4.0 license."
EXPECTED_SOURCE_BYTES = 190_308
EXPECTED_SOURCE_SHA256 = "dac6ce7c81922118cb9c03b47c2229cf2fa505db804aa45d7960dd166ef0ef8d"
EXPECTED_HELPER_SHA256 = "0eeb260de05ebae694700cc2212966ee4ba19351f067bef49c095ec6fccd70e6"
MATH_AUDIT = ROOT / "working" / "lesson05_math_audit.md"
EXPECTED_MATH_AUDIT_SHA256 = "65c29afb0ca867fc6cb40666e1af5d2837dd488be0880e043fd13bc5df805fcd"

KALTURA_URL = (
    "https://cdnapisec.kaltura.com/p/2356971/embedPlaykitJs/uiconf_id/54679262"
    "?iframeembed=true&entry_id=1_2xwqdqgj&config%5Bprovider%5D=%7B%22widgetId%22%3A%22"
    "1_4bkcltvd%22%7D&config%5Bplayback%5D=%7B%22startTime%22%3A0%7D"
)

EXPECTED_ASSETS = [
    {
        "source_ref": "Lesson05_files/figure-html/fig-boxplotcornyield-1.png",
        "bytes": 13596,
        "sha256": "e631a597ffe9629e6018d10797d8d78acd16e54c11f6bb726b09ae1b3c18526b",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"351c-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/fig-histogramcornyield-1.png",
        "bytes": 16291,
        "sha256": "38f2c20d1047c7cb83260e3ae701433947a8095789e64a71723a25576b8f6729",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"3fa3-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/fig-scattercornyield-1.png",
        "bytes": 9076,
        "sha256": "b04556e2d0ae41786e26e7d2f5dcffac16c848b70d42a2da913b0cea1c72ae58",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"2374-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-28-1.png",
        "bytes": 12162,
        "sha256": "322c8262267b94c40ab278c6e1b12ae6392d4fa8c791728c8aeb7fc237ffeed1",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"2f82-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-33-1.png",
        "bytes": 11442,
        "sha256": "91984c9166d1f97dc06d74e2f1b9758e3b7c2c85022d72d550b0b592dea0230a",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"2cb2-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-38-1.png",
        "bytes": 13448,
        "sha256": "20d29a335b774efa90ad3c8aae736a88195aa434f4a341e0032d2e4b34b68634",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"3488-659cca3a58c80"',
    },
    {
        "source_ref": "assets/numericalmle.png",
        "bytes": 279534,
        "sha256": "beccd0ca73e2d9c356a3d055b37d1fefbfa18f3e3aa0beb33d9a4b07b9ededf4",
        "width": 6370,
        "height": 2600,
        "last_modified": "Mon, 17 Mar 2025 16:42:41 GMT",
        "etag": '"443ee-6308c7a058240"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-44-1.png",
        "bytes": 20158,
        "sha256": "4a214757b39752e2b9de29844fa84f431c31f0c4997aff0323f1d78839e55186",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"4ebe-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-44-2.png",
        "bytes": 20140,
        "sha256": "e690b5d1bda3d18867ebb88eb0b2a616d69669d83eebcccc5218a3f5d40bc874",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"4eac-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-44-3.png",
        "bytes": 20792,
        "sha256": "7a7e6edc8870fffbc9c922e033a6734ba107c7570f03ee0b97c232999ca186ff",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"5138-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-44-4.png",
        "bytes": 20594,
        "sha256": "4e2c443c46d4c117b8f838cec8084aac8f97d17e31a720afe6ff58e43877f702",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"5072-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-44-5.png",
        "bytes": 21965,
        "sha256": "727d50c5d750b52a57f0c051d99b08e43583f388190a2ab1553b2a61561ca3b8",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"55cd-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-45-1.png",
        "bytes": 11442,
        "sha256": "91984c9166d1f97dc06d74e2f1b9758e3b7c2c85022d72d550b0b592dea0230a",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"2cb2-659cca3a58c80"',
    },
    {
        "source_ref": "Lesson05_files/figure-html/unnamed-chunk-50-1.png",
        "bytes": 13880,
        "sha256": "ec5c5e908fdaba7c5a3d11eb06b04392ad7ae49f15759ad6dc3c28d4fd8be7e6",
        "width": 1344,
        "height": 960,
        "last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
        "etag": '"3638-659cca3a58c80"',
    },
]

base.DOCUMENT_ID = DOCUMENT_ID
base.COMPONENT_ID = COMPONENT_ID
base.SOURCE_URL = SOURCE_URL
base.CATALOGUE_SCHEMA = CATALOGUE_SCHEMA


def normalized_html(source_soup: BeautifulSoup, main: Tag) -> bytes:
    title = (
        source_soup.title.get_text(" ", strip=True)
        if source_soup.title
        else "5 Maximum Likelihood Estimation (MLE) (Part II)"
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


def code_with(codes: list[str], *markers: str) -> str | None:
    return next((text for text in codes if all(marker in text for marker in markers)), None)


def source_defects(main: Tag) -> list[dict[str, object]]:
    """Return only exact source defects corroborated by direct algebra/code inspection."""
    formulas = base.formula_texts(main)
    codes = [node.get_text() for node in main.select("pre code")]
    prose = main.get_text(" ", strip=True)
    defects: list[dict[str, object]] = []

    def add(defect_id: str, kind: str, evidence: object, note: str) -> None:
        defects.append({"defect_id": defect_id, "kind": kind, "evidence": evidence, "note": note})

    if (
        "Calculating the pdf or pmf or likelihood of a distribution at a given observed value" in prose
        and "dXXX" in prose
        and "probability density function" in prose
    ):
        add(
            "L05-D001",
            "density-mass-likelihood-conflation",
            "The generic dXXX explanation calls density, mass, and likelihood the same returned quantity.",
            "A d* function returns a density or mass value; it is a likelihood factor only when data are fixed and the parameter varies.",
        )

    assigned_one = code_with(codes, "x=rnorm(n=1,mean=3,sd=2)")
    ten_claim = "ten simulated data points in" in prose
    if assigned_one and ten_claim:
        add(
            "L05-D002",
            "normal-simulation-size-contradiction",
            assigned_one,
            "x receives one draw, but the following prose/formulas/outputs repeatedly claim that x contains ten draws.",
        )

    unseeded = [
        text
        for text in codes
        if any(marker in text for marker in ("rnorm(n=1,mean=3,sd=2)", "rnorm(n=10,mean=3,sd=2)", "rexp(n=30,rate=2)", "rexp(n=1000,rate=2)"))
        and "set.seed" not in text
    ]
    if len(unseeded) >= 4:
        add(
            "L05-D003",
            "unseeded-reported-simulations",
            unseeded,
            "Exact downstream random outputs are reported without a preceding seed or a frozen generated vector.",
        )

    random_likelihood = formula_with(formulas, r"L(X_1,\ldots,X_{10})")
    random_loglikelihood = formula_with(formulas, r"l(X_1,\ldots,X_10)")
    if random_likelihood and random_loglikelihood:
        add(
            "L05-D004",
            "likelihood-as-random-data-function",
            [random_likelihood, random_loglikelihood],
            "These are joint-density expressions; likelihood/log-likelihood must be functions of parameters for fixed observations.",
        )

    empty_grid = code_with(codes, "lik.vals=rep(NA,length(theta.vals))")
    if empty_grid and not any("lik.vals[" in text for text in codes):
        add(
            "L05-D005",
            "missing-grid-search-computation",
            empty_grid,
            "The visible code never assigns computed likelihoods into lik.vals before plotting and which.max.",
        )

    grid = code_with(codes, "theta.vals=seq(1,100,by=0.1)")
    grid_estimate = formula_with(formulas, r"\hat{\theta}_{grid}=8.9")
    if grid and grid_estimate and "given the values that we tried, our MLE is" in prose:
        add(
            "L05-D006",
            "grid-approximation-called-exact-mle",
            [grid, grid_estimate],
            "8.9 is the maximizer on a 0.1-spaced grid; the exact exponential-mean MLE for the listed data is 133/15.",
        )

    score_equation = formula_with(formulas, r"h(\theta)=\frac{d}{d\theta} \ell(\theta)=0")
    malformed_score_eval = formula_with(formulas, r"h(\theta^{(0)}=\frac{d}{d\theta}")
    if score_equation and malformed_score_eval:
        add(
            "L05-D007",
            "score-definition-and-delimiter",
            [score_equation, malformed_score_eval],
            "Define h(theta)=ell'(theta), then solve h(theta)=0; the evaluation h(theta^(0)) also lacks a closing parenthesis.",
        )

    if "We evaluate the log likelihood function at that value. Then we find the tangent line" in prose:
        add(
            "L05-D008",
            "newton-tangent-of-wrong-function",
            "The narrative evaluates/takes the tangent of the log-likelihood after deriving Newton root-finding for its score.",
            "The tangent and x-intercept update apply to h=ell', and a score root still requires maximum/domain checks.",
        )

    wrong_start = formula_with(formulas, r"t=1, 2, \ldots")
    recurrence = formula_with(formulas, r"\theta^{(t+1)}", r"h^\prime(\theta^{(t)})")
    if wrong_start and recurrence:
        add(
            "L05-D009",
            "newton-index-start",
            [wrong_start, recurrence],
            "Given theta^(0), the displayed recurrence's first update occurs at t=0, not t=1.",
        )

    dropped_parameter = formula_with(
        formulas,
        r"f_X(x_i,\theta)",
        r"\log f_X(x_i)",
    )
    if dropped_parameter:
        add(
            "L05-D010",
            "loglikelihood-parameter-notation",
            dropped_parameter,
            "The same equality first writes f_X(x_i,theta) and then drops theta from every log-density term.",
        )

    optim_calls = [text for text in codes if "optim(" in text]
    if optim_calls and "algorithms like Newton" in prose and all("method=" not in text for text in optim_calls):
        add(
            "L05-D011",
            "optim-method-ambiguity",
            optim_calls,
            "The hand recurrence is Newton-Raphson, whereas optim() without method defaults to Nelder-Mead; the source does not distinguish them.",
        )

    exp_objective = code_with(codes, "dexp(x,rate=1/theta,log=TRUE)")
    if exp_objective and "unknown rate parameter" in prose:
        add(
            "L05-D012",
            "exponential-rate-scale-reversal",
            exp_objective,
            "The prose calls theta a rate, but rate=1/theta makes theta the mean/scale.",
        )

    unconstrained_exp = code_with(codes, "optim(2,nll.exp,x=x)")
    if unconstrained_exp and "method=" not in unconstrained_exp and "lower=" not in unconstrained_exp:
        add(
            "L05-D013",
            "unconstrained-positive-exponential-parameter",
            unconstrained_exp,
            "A positive start does not keep optim from evaluating a nonpositive exponential mean/scale.",
        )

    if "IGNORE MOST WARNINGS FROM" in prose and "values of" in prose and "were negative" in prose:
        add(
            "L05-D014",
            "unsafe-warning-advice",
            "The source explicitly tells readers to ignore most optim warnings, including invalid negative trial parameters.",
            "Domain violations and nonfinite objectives must be prevented/diagnosed, not dismissed.",
        )

    reciprocal_check = "nll.exp(0.112793,x)"
    if reciprocal_check in prose and exp_objective:
        add(
            "L05-D015",
            "objective-check-uses-reciprocal-parameter",
            reciprocal_check,
            "Under the implemented mean parameterization, the reported objective 47.73448 is evaluated near theta=8.865625, not theta=0.112793.",
        )

    optim_output = code_with(codes, "$counts", "30", "NA", "$convergence")
    if optim_output and "32 iterations" in prose:
        add(
            "L05-D016",
            "optim-counts-misinterpreted",
            [optim_output, "32 iterations"],
            "optim $counts records objective/gradient evaluations (30 and NA here), not 32 algorithmic iterations.",
        )

    if "Since the convergence is 0" in prose and "we can trust the results" in prose:
        add(
            "L05-D017",
            "convergence-code-overclaim",
            "convergence=0 is treated as proof that the numerical MLE is trustworthy.",
            "Code 0 only reports the optimizer's stopping condition; domain, objective, sensitivity, and derivative/benchmark checks remain necessary.",
        )

    if "8.6875 vs 8.65625" in prose:
        add(
            "L05-D018",
            "misreported-optimizer-estimates",
            "8.6875 vs 8.65625",
            "The two displayed outputs are 8.865625 and 8.86875, not the values quoted in the comparison prose.",
        )

    normal_objective = code_with(codes, "dnorm(y,mean=mu,sd=sqrt(s2),log=TRUE)")
    unconstrained_normal = code_with(codes, "optim(c(-1,1),nll.norm,y=y)")
    if normal_objective and unconstrained_normal:
        add(
            "L05-D019",
            "unguarded-normal-variance-domain",
            [normal_objective, unconstrained_normal],
            "The objective is invalid for s2<=0, but the unconstrained optimizer may trial such values; a log-variance or positive bound is required.",
        )

    wrong_mean_symbol = formula_with(formulas, r"\hat{\theta}_{ML}=-3.186")
    if wrong_mean_symbol:
        add(
            "L05-D020",
            "normal-mean-estimate-symbol",
            wrong_mean_symbol,
            "The first Normal parameter is mu, so the displayed estimate must be labeled mu-hat rather than theta-hat.",
        )

    categories = [node.get_text(" ", strip=True) for node in main.select(".quarto-category")]
    stale = [
        "Point Estimation", "Unbiased Estimation", "Bias", "Variance and Mean Square",
        "Factorization", "Sufficiency", "Method of Moments",
    ]
    if categories == stale:
        add(
            "L05-D021",
            "stale-title-categories",
            categories,
            "These are Lesson 03 topics, not Lesson 05's R and numerical-MLE content.",
        )

    if "put letters in parentheses" in prose and "See Section 3.2" in prose:
        add(
            "L05-D022",
            "character-vector-instruction-and-crossreference",
            "put letters in parentheses ... See Section 3.2",
            "Character values require quotation marks, and the local scalar/vector subsection is 5.1.2 rather than Section 3.2.",
        )

    future_use = next(
        (node.get_text(" ", strip=True) for node in main.find_all("p") if "future use" in node.get_text(" ", strip=True)),
        None,
    )
    if future_use and future_use.rstrip().endswith("”"):
        add("L05-D023", "unmatched-closing-quotation-mark", future_use, "Remove the unmatched closing quotation mark.")

    if "Interactively finding a sequence of new parameters" in prose:
        add("L05-D024", "word-choice-typo", "Interactively finding", "The intended word is Iteratively.")

    if "tangent like at the current value" in prose:
        add("L05-D025", "word-choice-typo", "tangent like", "The intended phrase is tangent line.")

    if "R can’t directly calculate derivatives of a function" in prose:
        add(
            "L05-D026",
            "overbroad-r-derivative-claim",
            "R can’t directly calculate derivatives of a function",
            "Base R has limited symbolic derivative facilities (D/deriv); say that this example derives and codes the derivatives manually.",
        )

    if "optim s output is as follows" in prose.replace("’", " ") and "stopping criteria" in prose:
        add(
            "L05-D027",
            "surface-grammar",
            ["optim's missing possessive", "a stopping criteria"],
            "Use optim's and the singular phrase a stopping criterion.",
        )

    iframes = main.select("iframe[src]")
    malformed_wrappers = main.select('div[style*="padding-bottom:2 %>% %"]')
    if (
        len(iframes) == 2
        and len({tag.get("src") for tag in iframes}) == 1
        and [tag.get("id") for tag in iframes] == ["kaltura_player", "kaltura_player"]
        and len(malformed_wrappers) == 2
    ):
        add(
            "L05-D028",
            "duplicate-video-surface",
            {"iframe_occurrences": 2, "unique_urls": 1, "duplicate_id": "kaltura_player", "malformed_wrappers": 2},
            "Both numbered videos embed the same URL/id and both wrappers contain malformed padding CSS; deduplicate or identify distinct media and supply static fallback.",
        )

    native_ids = [tag.get("id") for tag in main.select("[id]")]
    duplicate_figure_ids = sorted(
        value
        for value, count in Counter(native_ids).items()
        if count > 1 and value in {"fig-boxplotcornyield", "fig-histogramcornyield", "fig-scattercornyield"}
    )
    if duplicate_figure_ids == ["fig-boxplotcornyield", "fig-histogramcornyield", "fig-scattercornyield"]:
        add(
            "L05-D029",
            "duplicate-figure-native-ids",
            duplicate_figure_ids,
            "Each ID is duplicated between a container and its image; native DOM IDs must be unique.",
        )

    images = main.select("img[src]")
    missing_alts = [tag.get("src") for tag in images if not tag.get("alt")]
    vague_alts = [tag.get("src") for tag in images if (tag.get("alt") or "").strip() == "A series of  graphs showing the Newton method."]
    if missing_alts == ["Lesson05_files/figure-html/unnamed-chunk-28-1.png"] and len(vague_alts) == 5:
        add(
            "L05-D030",
            "image-alternative-text",
            {"missing": missing_alts, "vague_newton_sequence": vague_alts},
            "One plot has no alt text and five iteration frames reuse a non-specific description; each needs mathematical, frame-specific alternative text.",
        )

    editorial_note = "---I moved this from under the single header!--"
    comments = [str(value) for value in main.find_all(string=lambda value: isinstance(value, Comment))]
    if editorial_note in comments:
        add(
            "L05-D031",
            "exposed-editorial-note",
            editorial_note,
            "Replace the internal authoring note with a reader-facing transition into numerical optimization.",
        )

    return defects


def assign_dependencies(main: Tag) -> list[dict[str, object]]:
    """Assign stable identity to non-image semantic-main dependencies."""
    rows: list[dict[str, object]] = []
    by_key: dict[tuple[str, str], list[Tag]] = {}
    for tag in main.select("iframe[src]"):
        by_key.setdefault(("iframe", str(tag.get("src"))), []).append(tag)
    for ordinal, ((kind, source_ref), tags) in enumerate(by_key.items(), start=1):
        entity_id = f"{DOCUMENT_ID}-D{ordinal:04d}"
        for tag in tags:
            tag["data-o006-dependency-id"] = entity_id
        rows.append(
            {
                "schema": CATALOGUE_SCHEMA,
                "record_type": "dependency",
                "entity_id": entity_id,
                "dependency_id": entity_id,
                "document_id": DOCUMENT_ID,
                "component_id": COMPONENT_ID,
                "ordinal": ordinal,
                "dependency_kind": kind,
                "source_ref": source_ref,
                "source_url": source_ref,
                "occurrences": len(tags),
                "native_ids": [tag.get("id") for tag in tags],
                "titles": [tag.get("title") for tag in tags],
                "parent_unit_ids": [base.nearest_unit_id(tag) for tag in tags],
                "section_ids": [base.section_id(tag) for tag in tags],
                "external": urlparse(source_ref).netloc != urlparse(SOURCE_URL).netloc,
                "source_sha256": base.sha256(source_ref.encode("utf-8")),
            }
        )
    return rows


def validate_png(payload: bytes) -> dict[str, object]:
    if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError("frozen Lesson05 asset is not PNG")
    cursor = 8
    chunks: list[str] = []
    width = height = bit_depth = color_type = interlace = None
    crc_valid = True
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise RuntimeError("truncated Lesson05 PNG chunk")
        length = struct.unpack(">I", payload[cursor:cursor + 4])[0]
        chunk_type = payload[cursor + 4:cursor + 8]
        data = payload[cursor + 8:cursor + 8 + length]
        stored_crc = struct.unpack(">I", payload[cursor + 8 + length:cursor + 12 + length])[0]
        crc_valid = crc_valid and (zlib.crc32(chunk_type + data) & 0xFFFFFFFF) == stored_crc
        name = chunk_type.decode("ascii")
        chunks.append(name)
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filter, interlace = struct.unpack(">IIBBBBB", data)
        cursor += 12 + length
        if chunk_type == b"IEND":
            break
    if not chunks or chunks[0] != "IHDR" or chunks[-1] != "IEND" or cursor != len(payload) or not crc_valid:
        raise RuntimeError("Lesson05 PNG structural validation failed")
    metadata = [name for name in chunks if name in {"tEXt", "zTXt", "iTXt", "eXIf", "iCCP"}]
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "interlace": interlace,
        "chunk_crc_valid": crc_valid,
        "metadata_chunks": metadata,
        "trailing_bytes": 0,
    }


def asset_closure(
    source_payload: bytes,
    source_soup: BeautifulSoup,
    main: Tag,
    asset_rows: list[dict[str, object]],
    dependency_rows: list[dict[str, object]],
) -> bytes:
    source_refs = list(dict.fromkeys(tag.get("src") for tag in main.select("img[src]")))
    expected_refs = [row["source_ref"] for row in EXPECTED_ASSETS]
    if source_refs != expected_refs or len(asset_rows) != 14:
        raise RuntimeError("Lesson05 image inventory differs from the frozen boundary")
    if len(dependency_rows) != 1 or dependency_rows[0]["source_ref"] != KALTURA_URL or dependency_rows[0]["occurrences"] != 2:
        raise RuntimeError("Lesson05 external iframe inventory differs")
    if LICENSE_TEXT not in source_soup.get_text(" ", strip=True):
        raise RuntimeError("Lesson05 page-level CC BY-NC 4.0 witness is missing")
    main_text = main.get_text(" ", strip=True).casefold()
    for marker in ("source:", "credit:", "copyright", "permission", "licensed under"):
        if marker in main_text:
            raise RuntimeError(f"unexpected per-asset rights marker in Lesson05 main: {marker}")

    frozen: list[dict[str, object]] = []
    for expected, catalogue_row in zip(EXPECTED_ASSETS, asset_rows):
        source_ref = str(expected["source_ref"])
        local = ASSET_ROOT / Path(source_ref)
        if not local.is_file():
            raise RuntimeError(f"frozen Lesson05 asset missing: {source_ref}")
        data = local.read_bytes()
        if len(data) != expected["bytes"] or base.sha256(data) != expected["sha256"]:
            raise RuntimeError(f"frozen Lesson05 asset differs: {source_ref}")
        validation = validate_png(data)
        if validation["width"] != expected["width"] or validation["height"] != expected["height"]:
            raise RuntimeError(f"Lesson05 PNG dimensions differ: {source_ref}")
        if validation["metadata_chunks"]:
            raise RuntimeError(f"Lesson05 PNG contains embedded rights metadata requiring review: {source_ref}")
        tags = main.select(f'img[src="{source_ref}"]')
        lightboxes = main.select(f'a[href="{source_ref}"]')
        official_url = urljoin(SOURCE_URL, source_ref)
        if urlparse(official_url).netloc != urlparse(SOURCE_URL).netloc:
            raise RuntimeError(f"Lesson05 image is not same-origin: {source_ref}")
        frozen.append(
            {
                "asset_id": catalogue_row["asset_id"],
                "source_ref": source_ref,
                "official_url": official_url,
                "local_path": f"authority/assets/stat415/lesson05/{source_ref}",
                "img_occurrences": len(tags),
                "lightbox_href_occurrences": len(lightboxes),
                "alt_texts": [tag.get("alt") for tag in tags],
                "bytes": len(data),
                "sha256": base.sha256(data),
                "http_audit": {
                    "status": 200,
                    "content_type": "image/png",
                    "content_length": expected["bytes"],
                    "last_modified": expected["last_modified"],
                    "etag": expected["etag"],
                    "redirected": False,
                    "checked_on": "2026-08-25",
                },
                "png_validation": validation,
                "rights": {
                    "applied_license": "CC BY-NC 4.0",
                    "same_origin": True,
                    "per_asset_exception_in_main": False,
                    "embedded_rights_metadata": False,
                    "clearance": "cleared-for-noncommercial-derivative-freeze-under-official-page-notice",
                },
                "visual_validation": "matches the graph/plot role and surrounding Lesson05 context",
                "disposition": "freeze",
            }
        )

    remote = {
        "dependency_id": dependency_rows[0]["dependency_id"],
        "kind": "iframe",
        "url": KALTURA_URL,
        "url_sha256": base.sha256(KALTURA_URL.encode("utf-8")),
        "occurrences": 2,
        "unique_urls": 1,
        "duplicate_native_id": "kaltura_player",
        "title": "STAT 415: Newton's Method [no sound]",
        "rights": "third-party Kaltura media grant not established by the Penn State page notice",
        "disposition": "do-not-bundle; replace with optional external link and complete static derivation/fallback",
        "required_for_mathematical_comprehension": False,
    }
    closure = {
        "schema": "o006.stat415.lesson05-asset-closure.v1",
        "status": "same-origin-images-closed-external-video-excluded-reader-remediation-required",
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "source": {
            "path": "authority/upstream/stat415/Lesson05.html",
            "url": SOURCE_URL,
            "bytes": len(source_payload),
            "sha256": base.sha256(source_payload),
        },
        "boundary": "main#quarto-document-content",
        "dependency_census": base.dependency_census(main),
        "counts": {
            "image_occurrences": len(main.select("img[src]")),
            "unique_image_references": len(source_refs),
            "frozen_png_files": len(frozen),
            "frozen_png_bytes": sum(int(row["bytes"]) for row in frozen),
            "unique_frozen_payloads": len({row["sha256"] for row in frozen}),
            "same_asset_lightbox_hrefs": sum(int(row["lightbox_href_occurrences"]) for row in frozen),
            "external_iframe_occurrences": 2,
            "unique_external_iframe_urls": 1,
        },
        "rights": {
            "page_license": "CC BY-NC 4.0",
            "license_url": "https://creativecommons.org/licenses/by-nc/4.0/",
            "witness_text": LICENSE_TEXT,
            "per_image_exception_in_main": False,
            "external_video_covered_by_page_notice": False,
        },
        "temporal_provenance": {
            "html_manifest_last_modified": "Wed, 19 Aug 2026 19:23:11 GMT",
            "generated_png_last_modified": "Mon, 24 Aug 2026 15:28:34 GMT",
            "hand_authored_png_last_modified": "Mon, 17 Mar 2025 16:42:41 GMT",
            "disposition": (
                "frozen PNGs are the exact current official same-origin bytes checked on 2026-08-25; "
                "they are not claimed to be a byte-synchronous export from the older HTML timestamp"
            ),
        },
        "frozen_images": frozen,
        "external_dependencies": [remote],
        "accessibility_gate": {
            "missing_alt_asset_ids": ["O006-PSU-006-A0004"],
            "vague_sequence_alt_asset_ids": [
                "O006-PSU-006-A0008", "O006-PSU-006-A0009", "O006-PSU-006-A0010",
                "O006-PSU-006-A0011", "O006-PSU-006-A0012",
            ],
            "reader_repairs_required": 6,
        },
        "closure": {
            "same_origin_image_reference_inventory_complete": True,
            "same_origin_image_bytes_complete": True,
            "same_origin_image_rights_disposition_complete": True,
            "unresolved_same_origin_asset_bytes": 0,
            "third_party_video_bytes_frozen": 0,
            "third_party_video_exclusion_complete": True,
            "normalization_may_proceed": True,
            "offline_reader_gate": (
                "replace both duplicate iframes with an optional external link/static derivation; "
                "repair six image descriptions and duplicate native IDs before claiming accessibility closure"
            ),
        },
    }
    return base.canonical_json(closure)


def compute() -> dict[str, bytes]:
    helper_payload = HELPER_SCRIPT.read_bytes()
    if base.sha256(helper_payload) != EXPECTED_HELPER_SHA256:
        raise RuntimeError("Lesson05 normalization helper differs from its frozen implementation")
    source_payload = SOURCE.read_bytes()
    if len(source_payload) != EXPECTED_SOURCE_BYTES or base.sha256(source_payload) != EXPECTED_SOURCE_SHA256:
        raise RuntimeError("Lesson05 authority differs from the frozen 14-document manifest")
    try:
        source_text = source_payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("Lesson05 authority is not valid UTF-8") from exc
    source_soup = BeautifulSoup(source_text, "html.parser")
    original_main = source_soup.select_one("main#quarto-document-content")
    if original_main is None:
        raise RuntimeError("Lesson05 authority lacks main#quarto-document-content")
    if original_main.select("script"):
        raise RuntimeError("unexpected executable script in Lesson05 semantic main")

    fragment = BeautifulSoup(str(original_main), "html.parser")
    main = fragment.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError("failed to clone Lesson05 semantic main")
    main["data-source-url"] = SOURCE_URL
    main["data-component-id"] = COMPONENT_ID
    main["data-document-id"] = DOCUMENT_ID

    source_topology_sha = base.topology_sha256(original_main)
    source_counts = base.content_counts(original_main)
    source_formulas = base.formula_texts(original_main)
    formula_payload = "\n".join(source_formulas).encode("utf-8")
    source_code_texts = [tag.get_text() for tag in original_main.select("code")]
    code_payload = "\n".join(source_code_texts).encode("utf-8")
    semantic_text_payload = original_main.get_text().encode("utf-8")
    native_ids = [tag.get("id") for tag in original_main.select("[id]")]
    duplicate_ids = sorted(key for key, count in Counter(native_ids).items() if count > 1)

    unit_rows = base.assign_units(main)
    math_rows = base.assign_math(main)
    asset_rows = base.assign_assets(main)
    dependency_rows = assign_dependencies(main)
    segment_rows = base.extract_segments(main)
    normalized_payload = normalized_html(source_soup, main)
    base.assert_preservation(original_main, normalized_payload, source_topology_sha, source_counts)
    parsed = BeautifulSoup(normalized_payload.decode("utf-8"), "html.parser")
    target_main = parsed.select_one("main#quarto-document-content")
    if target_main is None:
        raise RuntimeError("normalized Lesson05 lacks semantic main")
    if [tag.get_text() for tag in target_main.select("code")] != source_code_texts:
        raise RuntimeError("Lesson05 code-node text changed during normalization")
    if target_main.get_text() != original_main.get_text():
        raise RuntimeError("Lesson05 semantic-main text changed during normalization")
    if [tag.get("src") for tag in target_main.select("iframe[src]")] != [
        tag.get("src") for tag in original_main.select("iframe[src]")
    ]:
        raise RuntimeError("Lesson05 iframe topology changed during normalization")

    document_row: dict[str, object] = {
        "schema": CATALOGUE_SCHEMA,
        "record_type": "document",
        "entity_id": DOCUMENT_ID,
        "document_id": DOCUMENT_ID,
        "component_id": COMPONENT_ID,
        "ordinal": 6,
        "locale": "en-US",
        "source_path": "authority/upstream/stat415/Lesson05.html",
        "source_url": SOURCE_URL,
        "source_bytes": len(source_payload),
        "source_sha256": base.sha256(source_payload),
        "normalized_path": "source/normalized/en-US/Lesson05.html",
        "normalized_bytes": len(normalized_payload),
        "normalized_sha256": base.sha256(normalized_payload),
        "topology_sha256": source_topology_sha,
        "semantic_text_sha256": base.sha256(semantic_text_payload),
        "formula_count": len(source_formulas),
        "formula_sha256": base.sha256(formula_payload),
        "code_node_count": len(source_code_texts),
        "code_text_sha256": base.sha256(code_payload),
        "unit_count": len(unit_rows),
        "segment_count": len(segment_rows),
        "asset_count": len(asset_rows),
        "dependency_count": len(dependency_rows),
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
        document_row, *unit_rows, *math_rows, *asset_rows, *dependency_rows, *catalogue_segment_rows,
    ]
    csv_payload = base.segment_csv(segment_rows)
    catalogue_payload = base.canonical_jsonl(catalogue_rows)
    closure_payload = asset_closure(source_payload, source_soup, original_main, asset_rows, dependency_rows)
    defects = source_defects(original_main)
    role_counts = dict(sorted(Counter(row["role"] for row in unit_rows).items()))
    script_payload = SCRIPT.read_bytes()

    receipt = {
        "schema": "o006.stat415.lesson05-normalization.v1",
        "status": "normalized-source-ready-same-origin-assets-closed-reader-remediation-required",
        "document": document_row,
        "counts": {
            **source_counts,
            "structural_units": len(unit_rows),
            "translation_segments": len(segment_rows),
            "assets": len(asset_rows),
            "dependencies": len(dependency_rows),
            "catalogue_records": len(catalogue_rows),
            "native_id_occurrences": len(native_ids),
            "unique_native_ids": len(set(native_ids)),
        },
        "role_counts": role_counts,
        "asset_inventory": [
            {
                "asset_id": row["asset_id"],
                "source_ref": row["source_ref"],
                "source_url": row["source_url"],
                "occurrences": row["occurrences"],
                "alt_texts": row["alt_texts"],
            }
            for row in asset_rows
        ],
        "dependency_inventory": dependency_rows,
        "asset_closure": {
            "same_origin_png_files": 14,
            "same_origin_png_bytes": 484520,
            "same_origin_image_bytes_closed": True,
            "external_iframe_occurrences_excluded": 2,
            "reader_repairs_required": 6,
        },
        "duplicate_native_ids": duplicate_ids,
        "source_defects": defects,
        "source_defect_count": len(defects),
        "preservation": {
            "main_selector": "main#quarto-document-content",
            "topology_sha256": source_topology_sha,
            "semantic_text_sha256": base.sha256(semantic_text_payload),
            "formula_sha256": base.sha256(formula_payload),
            "code_text_sha256": base.sha256(code_payload),
            "formula_nodes_byte_preserved": True,
            "code_nodes_text_preserved": True,
            "semantic_main_text_preserved": True,
            "native_anchor_sequence_preserved": True,
            "link_sequence_preserved": True,
            "image_sequence_preserved": True,
            "iframe_sequence_preserved": True,
            "dependency_census_preserved": True,
            "authority_mutated": False,
        },
        "outputs": {
            "normalized": {
                "path": "source/normalized/en-US/Lesson05.html",
                "bytes": len(normalized_payload),
                "sha256": base.sha256(normalized_payload),
            },
            "segments": {
                "path": "working/lesson05_segments.csv",
                "bytes": len(csv_payload),
                "sha256": base.sha256(csv_payload),
                "rows": len(segment_rows),
            },
            "catalogue": {
                "path": "backend/lesson05_source_catalogue.jsonl",
                "bytes": len(catalogue_payload),
                "sha256": base.sha256(catalogue_payload),
                "records": len(catalogue_rows),
            },
            "asset_closure": {
                "path": "working/lesson05_asset_closure.json",
                "bytes": len(closure_payload),
                "sha256": base.sha256(closure_payload),
            },
            "script": {
                "path": "scripts/normalize_lesson05.py",
                "bytes": len(script_payload),
                "sha256": base.sha256(script_payload),
            },
            "helper_script": {
                "path": "scripts/normalize_lesson03.py",
                "bytes": len(helper_payload),
                "sha256": base.sha256(helper_payload),
            },
            "corroborating_math_audit": {
                "path": "working/lesson05_math_audit.md",
                "bytes_at_authoring": 15089,
                "sha256": EXPECTED_MATH_AUDIT_SHA256,
                "authority": False,
                "build_dependency": False,
            },
        },
        "parser": {
            "name": "beautifulsoup4/html.parser",
            "beautifulsoup_version": bs4.__version__,
            "source_decoding": "UTF-8 strict",
        },
        "source_rule": (
            "semantic main only; no authority correction; formula/code text protected; stable unit, "
            "math, asset, external-dependency, and segment IDs additive"
        ),
    }
    return {
        "source/normalized/en-US/Lesson05.html": normalized_payload,
        "working/lesson05_segments.csv": csv_payload,
        "backend/lesson05_source_catalogue.jsonl": catalogue_payload,
        "working/lesson05_asset_closure.json": closure_payload,
        "build/LESSON05_NORMALIZATION_RECEIPT.json": base.canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            base.atomic_write(ROOT / relative, payload)
        mode_name = "written"
    else:
        for relative, expected in outputs.items():
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"Lesson05 normalized output missing: {relative}")
            actual = path.read_bytes()
            if actual != expected:
                raise RuntimeError(
                    f"Lesson05 normalized output differs: {relative}; "
                    f"actual={base.sha256(actual)} expected={base.sha256(expected)}"
                )
        mode_name = "verified"

    receipt_payload = outputs["build/LESSON05_NORMALIZATION_RECEIPT.json"]
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
