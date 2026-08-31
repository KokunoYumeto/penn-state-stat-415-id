#!/usr/bin/env python3
"""Build or byte-check the offline CP02 statistical artifact set.

The mathematical calculations are exact/deterministic under the stated
working probability laws except for explicitly labelled PCG64 posterior-
predictive and contrast summaries.  The aggregate source does not establish
disjoint independent Bernoulli units or one qualifying initiation per hen;
every inferential output therefore carries an explicit conditional,
illustrative applicability status.

No network, browser, JavaScript, or subprocess facility is imported or used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import platform
import statistics
import sys
from functools import lru_cache
from html import escape as xml_escape
from pathlib import Path
from typing import Any, Iterable, Iterator

import numpy as np


SCHEMA_ID = "o006.c140.cp02-analysis.v1"
SEED = 2026083002
PPC_REPLICATIONS = 100_000
CONTRAST_DRAWS = 100_000
ALPHA = 0.05
THRESHOLD = 0.5
C10 = 2.0
C01 = 1.0
ACTION_PROBABILITY_THRESHOLD = C10 / (C10 + C01)
PRIOR_ODDS_10 = 1.0
KAPPAS = (1.0, 2.0, 4.0, 8.0, 16.0)
PRIMARY_KAPPA = 4.0
PRIMARY_DENOMINATOR_ID = "primary_conservative_method_1"
SECONDARY_DENOMINATOR_ID = "secondary_liberal_method_2"
MODEL_ASSUMPTION_STATUS = (
    "conditional_illustrative: aggregate evidence does not prove disjoint "
    "independent Bernoulli units or one qualifying initiation per hen"
)
EMPIRICAL_TEST_SCOPE = (
    "reference_distribution_exact_conditionally; empirical applicability "
    "is illustrative pending unit-independence evidence"
)
Z_975 = statistics.NormalDist().inv_cdf(0.975)
NUMERIC_TOLERANCE = 1e-10
IDENTIFIABILITY_TOLERANCE = 1e-6
PROFILE_LOG_KAPPA_MIN = -4.0
PROFILE_LOG_KAPPA_MAX = 12.0
PROFILE_LOG_KAPPA_STEP = 0.5

SCRIPT_PATH = Path(__file__).resolve()
COMPONENT_ROOT = SCRIPT_PATH.parent.parent
DATA_ROOT = COMPONENT_ROOT / "data" / "capstones" / "CP02"
CLEAN_ROOT = DATA_ROOT / "clean"
GENERATED_ROOT = COMPONENT_ROOT / "generated" / "capstones" / "CP02"
BUILD_ROOT = COMPONENT_ROOT / "build"
RECEIPT_PATH = BUILD_ROOT / "CP02_ANALYSIS_RECEIPT.json"
TRANSFORM_RECEIPT_PATH = BUILD_ROOT / "CP02_TRANSFORM_RECEIPT.json"

CLEAN_HEADER = [
    "cell_id",
    "source_record",
    "cell_order",
    "transmitter",
    "year",
    "nests_initiated",
    "hens_available_primary",
    "hens_available_secondary",
]


class ContractError(RuntimeError):
    """Raised for a frozen-input, mathematical, or replay-contract failure."""


def fail(assertion: str, relative_path: str, detail: str) -> None:
    raise ContractError(f"{assertion}: {relative_path}: {detail}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fmt(value: Any) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, (bool, np.bool_)):
        return "true" if bool(value) else "false"
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    if isinstance(value, (float, np.floating)):
        number = float(value)
        if not math.isfinite(number):
            raise ContractError(f"non-finite numeric serialization requested: {number!r}")
        if number == 0.0:
            return "0"
        return format(number, ".15g")
    return str(value)


def fmt_id(value: Any) -> str:
    """Format reader-visible numbers with the Indonesian decimal separator."""
    return fmt(value).replace(".", ",")


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            separators=(",", ": "),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def csv_bytes(header: list[str], rows: Iterable[dict[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=header,
        extrasaction="raise",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: fmt(row.get(column, "")) for column in header})
    return buffer.getvalue().encode("utf-8")


def log_beta(a: float, b: float) -> float:
    if not (a > 0.0 and b > 0.0):
        raise ContractError(f"improper Beta parameters: a={a}, b={b}")
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _beta_continued_fraction(a: float, b: float, x: float) -> float:
    max_iterations = 500
    epsilon = 2.5e-14
    floor = sys.float_info.min / epsilon
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < floor:
        d = floor
    d = 1.0 / d
    h = d
    for iteration in range(1, max_iterations + 1):
        twice = 2 * iteration
        aa = iteration * (b - iteration) * x / ((qam + twice) * (a + twice))
        d = 1.0 + aa * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + aa / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        h *= d * c
        aa = -(a + iteration) * (qab + iteration) * x / ((a + twice) * (qap + twice))
        d = 1.0 + aa * d
        if abs(d) < floor:
            d = floor
        c = 1.0 + aa / c
        if abs(c) < floor:
            c = floor
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) <= epsilon:
            return h
    raise ContractError(f"incomplete-Beta continued fraction did not converge: a={a}, b={b}, x={x}")


def regularized_beta(x: float, a: float, b: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(a * math.log(x) + b * math.log1p(-x) - log_beta(a, b))
    if x < (a + 1.0) / (a + b + 2.0):
        answer = front * _beta_continued_fraction(a, b, x) / a
    else:
        answer = 1.0 - front * _beta_continued_fraction(b, a, 1.0 - x) / b
    return min(1.0, max(0.0, answer))


@lru_cache(maxsize=None)
def beta_ppf(probability: float, a: float, b: float) -> float:
    if probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return 1.0
    low = 0.0
    high = 1.0
    for _ in range(180):
        middle = (low + high) / 2.0
        if middle == low or middle == high:
            break
        if regularized_beta(middle, a, b) < probability:
            low = middle
        else:
            high = middle
    candidate = (low + high) / 2.0
    if not (0.0 <= candidate <= 1.0):
        raise ContractError("Beta quantile escaped [0,1]")
    return candidate


def log_combination(n: int, k: int) -> float:
    if not 0 <= k <= n:
        return -math.inf
    return math.lgamma(n + 1.0) - math.lgamma(k + 1.0) - math.lgamma(n - k + 1.0)


@lru_cache(maxsize=None)
def binomial_pmf(n: int, p: float) -> tuple[float, ...]:
    if p <= 0.0:
        return tuple([1.0] + [0.0] * n)
    if p >= 1.0:
        return tuple([0.0] * n + [1.0])
    probabilities = [math.comb(n, k) * (p**k) * ((1.0 - p) ** (n - k)) for k in range(n + 1)]
    total = math.fsum(probabilities)
    if abs(total - 1.0) > 5e-12:
        fail("binomial_mass", "in-memory", f"n={n}, p={p}, mass={total}")
    return tuple(probabilities)


def binomial_upper_tail(n: int, threshold_count: int, p: float) -> float:
    if threshold_count <= 0:
        return 1.0
    if threshold_count > n:
        return 0.0
    return math.fsum(binomial_pmf(n, p)[threshold_count:])


@lru_cache(maxsize=None)
def beta_binomial_pmf(n: int, a: float, b: float) -> tuple[float, ...]:
    probabilities = [
        math.exp(log_combination(n, k) + log_beta(a + k, b + n - k) - log_beta(a, b))
        for k in range(n + 1)
    ]
    total = math.fsum(probabilities)
    if abs(total - 1.0) > 2e-11:
        fail("beta_binomial_mass", "in-memory", f"n={n}, a={a}, b={b}, mass={total}")
    return tuple(probabilities)


def posterior_stats(y: int, n: int, kappa: float) -> dict[str, float | int]:
    a0 = kappa / 2.0
    b0 = kappa / 2.0
    a = a0 + y
    b = b0 + n - y
    mean = a / (a + b)
    variance = a * b / ((a + b) ** 2 * (a + b + 1.0))
    low = beta_ppf(ALPHA / 2.0, a, b)
    high = beta_ppf(1.0 - ALPHA / 2.0, a, b)
    mass = regularized_beta(high, a, b) - regularized_beta(low, a, b)
    probability = 1.0 - regularized_beta(THRESHOLD, a, b)
    probability = min(1.0, max(0.0, probability))
    loss_a0 = C01 * probability
    loss_a1 = C10 * (1.0 - probability)
    action = 1 if probability > ACTION_PROBABILITY_THRESHOLD else 0
    if not (a > 0.0 and b > 0.0 and 0.0 <= low <= high <= 1.0 and abs(mass - 0.95) < 5e-10):
        fail("posterior_interval", "in-memory", f"y={y}, n={n}, kappa={kappa}, mass={mass}")
    if action == 1 and loss_a1 > loss_a0 + NUMERIC_TOLERANCE:
        fail("bayes_action_loss", "in-memory", "action 1 does not minimize posterior loss")
    if action == 0 and loss_a0 > loss_a1 + NUMERIC_TOLERANCE:
        fail("bayes_action_loss", "in-memory", "action 0 does not minimize posterior loss")
    predictive_variance = n * a * b * (a + b + n) / ((a + b) ** 2 * (a + b + 1.0))
    return {
        "prior_alpha": a0,
        "prior_beta": b0,
        "posterior_alpha": a,
        "posterior_beta": b,
        "posterior_mean": mean,
        "posterior_variance": variance,
        "credible_low_95": low,
        "credible_high_95": high,
        "credible_mass": mass,
        "prob_gt_threshold": probability,
        "posterior_loss_a0": loss_a0,
        "posterior_loss_a1": loss_a1,
        "bayes_action": action,
        "predictive_next_success": mean,
        "predictive_rep_mean": n * mean,
        "predictive_rep_variance": predictive_variance,
    }


@lru_cache(maxsize=None)
def interval_for(procedure: str, n: int, y: int, kappa: float = PRIMARY_KAPPA) -> tuple[float, float]:
    if procedure == "bayes_equal_tail_primary" or procedure.startswith("bayes_equal_tail_kappa_"):
        a = kappa / 2.0 + y
        b = kappa / 2.0 + n - y
        return beta_ppf(ALPHA / 2.0, a, b), beta_ppf(1.0 - ALPHA / 2.0, a, b)
    if procedure == "clopper_pearson":
        low = 0.0 if y == 0 else beta_ppf(ALPHA / 2.0, float(y), float(n - y + 1))
        high = 1.0 if y == n else beta_ppf(1.0 - ALPHA / 2.0, float(y + 1), float(n - y))
        if 0.0 < low < 1.0:
            low = math.nextafter(low, 0.0)
        if 0.0 < high < 1.0:
            high = math.nextafter(high, 1.0)
        return low, high
    if procedure == "wilson":
        estimate = y / n
        denominator = 1.0 + Z_975 * Z_975 / n
        center = (estimate + Z_975 * Z_975 / (2.0 * n)) / denominator
        half = (
            Z_975
            / denominator
            * math.sqrt(estimate * (1.0 - estimate) / n + Z_975 * Z_975 / (4.0 * n * n))
        )
        low = 0.0 if y == 0 else max(0.0, center - half)
        high = 1.0 if y == n else min(1.0, center + half)
        return low, high
    raise ContractError(f"unknown interval procedure {procedure!r}")


def coverage_at(n: int, p: float, intervals: list[tuple[float, float]]) -> float:
    probabilities = binomial_pmf(n, p)
    return math.fsum(
        probability
        for probability, (low, high) in zip(probabilities, intervals, strict=True)
        if low <= p <= high
    )


def model_comparison(y_values: list[int], n_values: list[int], kappa: float) -> dict[str, float | str]:
    a = kappa / 2.0
    b = kappa / 2.0
    total_y = sum(y_values)
    total_n = sum(n_values)
    combinatorial = math.fsum(log_combination(n, y) for y, n in zip(y_values, n_values, strict=True))
    log_m0 = combinatorial + log_beta(a + total_y, b + total_n - total_y) - log_beta(a, b)
    log_m1 = math.fsum(
        log_combination(n, y) + log_beta(a + y, b + n - y) - log_beta(a, b)
        for y, n in zip(y_values, n_values, strict=True)
    )
    log_bf10 = log_m1 - log_m0
    bf10 = math.exp(log_bf10)
    posterior_odds = PRIOR_ODDS_10 * bf10
    probability_m1 = posterior_odds / (1.0 + posterior_odds)
    probability_m0 = 1.0 - probability_m1
    loss_a0 = probability_m1
    loss_a1 = probability_m0
    selected = "M1" if loss_a1 < loss_a0 else "M0"
    if abs(log_bf10 - (log_m1 - log_m0)) > 1e-12:
        fail("log_bf_identity", "in-memory", "log BF differs from evidence difference")
    if abs(posterior_odds - PRIOR_ODDS_10 * bf10) > max(1e-15, abs(posterior_odds) * 1e-12):
        fail("posterior_odds_identity", "in-memory", "posterior odds identity failed")
    if selected == "M0" and loss_a0 > loss_a1 + NUMERIC_TOLERANCE:
        fail("model_action_loss", "in-memory", "M0 selected with larger posterior loss")
    if selected == "M1" and loss_a1 > loss_a0 + NUMERIC_TOLERANCE:
        fail("model_action_loss", "in-memory", "M1 selected with larger posterior loss")
    return {
        "log_m0": log_m0,
        "log_m1": log_m1,
        "log_bf10": log_bf10,
        "bf10": bf10,
        "prior_odds_10": PRIOR_ODDS_10,
        "posterior_odds_10": posterior_odds,
        "posterior_prob_m0": probability_m0,
        "posterior_prob_m1": probability_m1,
        "posterior_loss_a0": loss_a0,
        "posterior_loss_a1": loss_a1,
        "selected_action": selected,
    }


def deviance_contribution(x: int, n: int, pooled: float) -> float:
    value = 0.0
    if x > 0:
        value += x * math.log(x / (n * pooled))
    failures = n - x
    if failures > 0:
        value += failures * math.log(failures / (n * (1.0 - pooled)))
    return 2.0 * value


def exact_conditional_homogeneity(y_values: list[int], n_values: list[int]) -> dict[str, Any]:
    total_y = sum(y_values)
    total_n = sum(n_values)
    if total_y in (0, total_n):
        return {
            "exact_conditional_p": 1.0,
            "conditional_space_mass": 1.0,
            "observed_deviance": 0.0,
            "informative": False,
            "enumeration_nodes": 1,
        }
    # The conditional law and likelihood-ratio deviance are invariant when
    # successes and failures are exchanged.  Enumerating the smaller total
    # makes the exact branch-and-bound state space much narrower for this
    # near-boundary dataset without changing a probability or test rule.
    if total_y > total_n - total_y:
        y_values = [n - y for y, n in zip(y_values, n_values, strict=True)]
        total_y = total_n - total_y
    pooled = total_y / total_n
    # Visit the most diagnostically extreme observed cells first.  This is a
    # deterministic search-order optimization only; fsum, integer weights,
    # the conditional sample space, and the tail definition are unchanged.
    ordered = sorted(
        enumerate(zip(y_values, n_values, strict=True)),
        key=lambda item: (
            -deviance_contribution(item[1][0], item[1][1], pooled),
            -item[1][1],
            item[0],
        ),
    )
    y_values = [pair[0] for _, pair in ordered]
    n_values = [pair[1] for _, pair in ordered]
    scores = [[deviance_contribution(x, n, pooled) for x in range(n + 1)] for n in n_values]
    combination_weights = [[math.comb(n, x) for x in range(n + 1)] for n in n_values]
    observed = math.fsum(scores[index][y] for index, y in enumerate(y_values))
    groups = len(n_values)
    suffix_n = [0] * (groups + 1)
    for index in range(groups - 1, -1, -1):
        suffix_n[index] = suffix_n[index + 1] + n_values[index]

    infinity = float("inf")
    minimum = [[infinity] * (total_y + 1) for _ in range(groups + 1)]
    maximum = [[-infinity] * (total_y + 1) for _ in range(groups + 1)]
    minimum[groups][0] = 0.0
    maximum[groups][0] = 0.0
    for index in range(groups - 1, -1, -1):
        n = n_values[index]
        for remaining in range(total_y + 1):
            lower_x = max(0, remaining - suffix_n[index + 1])
            upper_x = min(n, remaining)
            for x in range(lower_x, upper_x + 1):
                tail_remaining = remaining - x
                if minimum[index + 1][tail_remaining] != infinity:
                    candidate = scores[index][x] + minimum[index + 1][tail_remaining]
                    minimum[index][remaining] = min(minimum[index][remaining], candidate)
                if maximum[index + 1][tail_remaining] != -infinity:
                    candidate = scores[index][x] + maximum[index + 1][tail_remaining]
                    maximum[index][remaining] = max(maximum[index][remaining], candidate)

    denominator = math.comb(total_n, total_y)
    tolerance = 2e-12 * max(1.0, abs(observed))
    tail_weight = 0
    nodes = 0

    def recurse(index: int, remaining: int, accumulated: float, prefix_weight: int) -> None:
        nonlocal tail_weight, nodes
        nodes += 1
        if remaining < 0 or remaining > suffix_n[index]:
            return
        if index == groups:
            if remaining == 0 and accumulated >= observed - tolerance:
                tail_weight += prefix_weight
            return
        lower_bound = minimum[index][remaining]
        upper_bound = maximum[index][remaining]
        if lower_bound == infinity:
            return
        if accumulated + lower_bound >= observed - tolerance:
            tail_weight += prefix_weight * math.comb(suffix_n[index], remaining)
            return
        if accumulated + upper_bound < observed - tolerance:
            return
        n = n_values[index]
        lower_x = max(0, remaining - suffix_n[index + 1])
        upper_x = min(n, remaining)
        for x in range(lower_x, upper_x + 1):
            recurse(
                index + 1,
                remaining - x,
                accumulated + scores[index][x],
                prefix_weight * combination_weights[index][x],
            )

    recurse(0, total_y, 0.0, 1)
    p_value = tail_weight / denominator
    if not 0.0 <= p_value <= 1.0:
        fail("homogeneity_probability", "in-memory", f"tail probability {p_value}")
    return {
        "exact_conditional_p": p_value,
        "conditional_space_mass": math.comb(total_n, total_y) / denominator,
        "observed_deviance": observed,
        "informative": True,
        "enumeration_nodes": nodes,
    }


def prior_id(kappa: float) -> str:
    mapping = {1.0: "beta_0p5_0p5", 2.0: "beta_1_1", 4.0: "beta_2_2", 8.0: "beta_4_4", 16.0: "beta_8_8"}
    return mapping[kappa]


def scenario_id_for_prior(kappa: float) -> str:
    return "primary" if kappa == PRIMARY_KAPPA else f"prior_kappa_{fmt(kappa)}"


def load_clean_cells() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    required_clean = {"CP02_cells_clean.csv", "ROW_MANIFEST.csv", "COLUMN_MANIFEST.csv", "TRANSFORM_LEDGER.json"}
    manifest_path = CLEAN_ROOT / "MANIFEST.csv"
    if not manifest_path.is_file():
        fail("clean_manifest_present", "data/capstones/CP02/clean/MANIFEST.csv", "file is missing")
    try:
        manifest_rows = list(csv.DictReader(io.StringIO(manifest_path.read_text(encoding="utf-8"), newline="")))
    except (UnicodeDecodeError, csv.Error) as exc:
        fail("clean_manifest_parse", "data/capstones/CP02/clean/MANIFEST.csv", str(exc))
    if {row.get("path", "") for row in manifest_rows} != required_clean:
        fail("clean_manifest_closure", "data/capstones/CP02/clean/MANIFEST.csv", "manifest must list every other clean file")
    for row in manifest_rows:
        path = CLEAN_ROOT / row["path"]
        if not path.is_file():
            fail("clean_output_present", f"data/capstones/CP02/clean/{row['path']}", "file is missing")
        data = path.read_bytes()
        if str(len(data)) != row.get("bytes") or sha256_bytes(data) != row.get("sha256"):
            fail("clean_output_identity", f"data/capstones/CP02/clean/{row['path']}", "bytes or SHA-256 differ")
    if not TRANSFORM_RECEIPT_PATH.is_file():
        fail("transform_receipt_present", "build/CP02_TRANSFORM_RECEIPT.json", "file is missing")
    transform_receipt = json.loads(TRANSFORM_RECEIPT_PATH.read_text(encoding="utf-8"))
    if transform_receipt.get("schema") != "o006.c140.cp02-transform.v1":
        fail("transform_receipt_schema", "build/CP02_TRANSFORM_RECEIPT.json", "schema differs")
    manifest_digest = sha256_bytes(manifest_path.read_bytes())
    if transform_receipt.get("manifest", {}).get("sha256") != manifest_digest:
        fail("transform_receipt_manifest", "build/CP02_TRANSFORM_RECEIPT.json", "clean manifest binding differs")

    table_path = CLEAN_ROOT / "CP02_cells_clean.csv"
    try:
        reader = csv.DictReader(io.StringIO(table_path.read_text(encoding="utf-8"), newline=""))
        if reader.fieldnames != CLEAN_HEADER:
            fail("clean_header", "data/capstones/CP02/clean/CP02_cells_clean.csv", "header differs")
        raw_rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as exc:
        fail("clean_parse", "data/capstones/CP02/clean/CP02_cells_clean.csv", str(exc))
    if len(raw_rows) != 12:
        fail("clean_row_count", "data/capstones/CP02/clean/CP02_cells_clean.csv", "expected 12 rows")
    rows: list[dict[str, Any]] = []
    for expected_order, raw in enumerate(raw_rows, 1):
        row = {
            "cell_id": raw["cell_id"],
            "source_record": int(raw["source_record"]),
            "cell_order": int(raw["cell_order"]),
            "transmitter": raw["transmitter"],
            "year": int(raw["year"]),
            "nests_initiated": int(raw["nests_initiated"]),
            "hens_available_primary": int(raw["hens_available_primary"]),
            "hens_available_secondary": int(raw["hens_available_secondary"]),
        }
        if row["cell_order"] != expected_order:
            fail("clean_canonical_order", "data/capstones/CP02/clean/CP02_cells_clean.csv", "cell_order differs")
        if not (0 <= row["nests_initiated"] <= row["hens_available_primary"] <= row["hens_available_secondary"]):
            fail("clean_binomial_domain", "data/capstones/CP02/clean/CP02_cells_clean.csv", row["cell_id"])
        row.update(
            {
                "group_label": row["transmitter"],
                "time_label": str(row["year"]),
                "cell_label": f"{row['transmitter']} — {row['year']}",
                "successes": row["nests_initiated"],
                "trials_primary": row["hens_available_primary"],
                "trials_secondary": row["hens_available_secondary"],
                "failures_primary": row["hens_available_primary"] - row["nests_initiated"],
                "failures_secondary": row["hens_available_secondary"] - row["nests_initiated"],
                "observed_rate": row["nests_initiated"] / row["hens_available_primary"],
                "observed_rate_secondary": row["nests_initiated"] / row["hens_available_secondary"],
                "denominator_id": PRIMARY_DENOMINATOR_ID,
                "model_assumption_status": MODEL_ASSUMPTION_STATUS,
            }
        )
        rows.append(row)
    return rows, manifest_rows


def build_cells_output(rows: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    header = CLEAN_HEADER + [
        "group_label",
        "time_label",
        "cell_label",
        "successes",
        "trials_primary",
        "trials_secondary",
        "failures_primary",
        "failures_secondary",
        "observed_rate",
        "observed_rate_secondary",
        "denominator_id",
        "model_assumption_status",
    ]
    return header, rows


POSTERIOR_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "prior_id",
    "kappa",
    "cell_id",
    "cell_label",
    "successes",
    "trials",
    "failures",
    "prior_alpha",
    "prior_beta",
    "posterior_alpha",
    "posterior_beta",
    "posterior_mean",
    "posterior_variance",
    "credible_low_95",
    "credible_high_95",
    "credible_mass",
    "threshold",
    "prob_gt_threshold",
    "c10",
    "c01",
    "posterior_loss_a0",
    "posterior_loss_a1",
    "bayes_action",
    "predictive_next_success",
    "predictive_rep_mean",
    "predictive_rep_variance",
    "beta_binomial_mass_sum",
    "interval_symbol_legend",
    "model_assumption_status",
    "status",
    "reason",
]


def build_primary_posterior(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    by_cell: dict[str, dict[str, Any]] = {}
    for row in rows:
        y = row["successes"]
        n = row["trials_primary"]
        summary = posterior_stats(y, n, PRIMARY_KAPPA)
        predictive_mass = math.fsum(beta_binomial_pmf(n, summary["posterior_alpha"], summary["posterior_beta"]))
        record = {
            "record_type": "cell",
            "scenario_id": "primary",
            "denominator_id": PRIMARY_DENOMINATOR_ID,
            "prior_id": prior_id(PRIMARY_KAPPA),
            "kappa": PRIMARY_KAPPA,
            "cell_id": row["cell_id"],
            "cell_label": row["cell_label"],
            "successes": y,
            "trials": n,
            "failures": n - y,
            **summary,
            "threshold": THRESHOLD,
            "c10": C10,
            "c01": C01,
            "beta_binomial_mass_sum": predictive_mass,
            "interval_symbol_legend": "circle=Bayes solid; square=Wilson dashed; diamond=Clopper-Pearson dotted",
            "model_assumption_status": MODEL_ASSUMPTION_STATUS,
            "status": "ok_conditional",
            "reason": "Exact conjugate calculation under the working Beta-Binomial model.",
        }
        output.append(record)
        by_cell[row["cell_id"]] = record
    return output, by_cell


MODEL_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "prior_id",
    "kappa",
    "model_id",
    "comparison",
    "log_evidence",
    "log_m0",
    "log_m1",
    "log_bf10",
    "bf10",
    "prior_odds_10",
    "posterior_odds_10",
    "posterior_prob_m0",
    "posterior_prob_m1",
    "posterior_loss_a0",
    "posterior_loss_a1",
    "selected_action",
    "conditional_on_model_assumptions",
    "model_assumption_status",
    "status",
    "reason",
]


def build_model_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    y = [row["successes"] for row in rows]
    n = [row["trials_primary"] for row in rows]
    comparison = model_comparison(y, n, PRIMARY_KAPPA)
    if abs(float(comparison["log_bf10"]) - (-32.1050957265)) > 5e-10:
        fail(
            "independent_log_bf_benchmark",
            "CP02_model_comparison.csv",
            f"expected approximately -32.1050957265, got {comparison['log_bf10']}",
        )
    common = {
        "scenario_id": "primary",
        "denominator_id": PRIMARY_DENOMINATOR_ID,
        "prior_id": prior_id(PRIMARY_KAPPA),
        "kappa": PRIMARY_KAPPA,
        "conditional_on_model_assumptions": True,
        "model_assumption_status": MODEL_ASSUMPTION_STATUS,
        "status": "ok_conditional",
        "reason": "Proper common Beta(kappa/2,kappa/2) priors under M0 and every M1 cell.",
    }
    output = [
        {
            **common,
            "record_type": "model",
            "model_id": "M0",
            "comparison": "",
            "log_evidence": comparison["log_m0"],
            **{key: "" for key in ("log_m0", "log_m1", "log_bf10", "bf10", "prior_odds_10", "posterior_odds_10", "posterior_prob_m0", "posterior_prob_m1", "posterior_loss_a0", "posterior_loss_a1", "selected_action")},
        },
        {
            **common,
            "record_type": "model",
            "model_id": "M1",
            "comparison": "",
            "log_evidence": comparison["log_m1"],
            **{key: "" for key in ("log_m0", "log_m1", "log_bf10", "bf10", "prior_odds_10", "posterior_odds_10", "posterior_prob_m0", "posterior_prob_m1", "posterior_loss_a0", "posterior_loss_a1", "selected_action")},
        },
        {
            **common,
            "record_type": "comparison",
            "model_id": "",
            "comparison": "M1_over_M0",
            "log_evidence": "",
            **comparison,
        },
    ]
    return output, comparison


def holm_adjustment(p_values: list[float], alpha: float) -> tuple[list[float], list[bool]]:
    ordered = sorted(enumerate(p_values), key=lambda item: (item[1], item[0]))
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, (original, p_value) in enumerate(ordered, 1):
        running = max(running, (len(p_values) - rank + 1) * p_value)
        adjusted[original] = min(1.0, running)
    rejected = [False] * len(p_values)
    still_rejecting = True
    for rank, (original, p_value) in enumerate(ordered, 1):
        threshold = alpha / (len(p_values) - rank + 1)
        if still_rejecting and p_value <= threshold:
            rejected[original] = True
        else:
            still_rejecting = False
    return adjusted, rejected


FREQUENTIST_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "cell_id",
    "cell_label",
    "procedure",
    "n",
    "p_fixed",
    "successes",
    "trials",
    "observed_rate",
    "wilson_low_95",
    "wilson_high_95",
    "cp_low_95",
    "cp_high_95",
    "exact_p_value",
    "critical_count",
    "actual_size",
    "raw_reject",
    "holm_adjusted_p",
    "holm_reject",
    "power",
    "first_p_at_or_above_80",
    "grid_points",
    "grid_min",
    "grid_max",
    "grid_argmin",
    "grid_argmax",
    "coverage_at_threshold",
    "exact_conditional_p",
    "conditional_space_mass",
    "observed_deviance",
    "informative",
    "empirical_test_scope",
    "conditional_on_model_assumptions",
    "status",
    "reason",
]


COVERAGE_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "prior_id",
    "kappa",
    "n",
    "procedure",
    "hypothetical_successes",
    "interval_low",
    "interval_high",
    "interval_width",
    "p_fixed",
    "coverage",
    "below_target",
    "target_coverage",
    "grid_point_source",
    "grid_points",
    "grid_min",
    "grid_max",
    "grid_argmin",
    "grid_argmax",
    "coverage_at_threshold",
    "prior_average_coverage",
    "posterior_mass",
    "closed_interval",
    "conditional_on_binomial_assumptions",
    "status",
    "reason",
]


def coverage_grid(interval_sets: dict[str, list[tuple[float, float]]], kappa: float) -> tuple[list[float], dict[float, str]]:
    sources: dict[float, set[str]] = {}

    def add(point: float, source: str) -> None:
        point = min(1.0, max(0.0, float(point)))
        sources.setdefault(point, set()).add(source)

    for index in range(1001):
        add(index / 1000.0, "base_0p001")
    for procedure, intervals in interval_sets.items():
        for low, high in intervals:
            for endpoint in (low, high):
                add(endpoint, f"{procedure}_endpoint")
                if 0.0 < endpoint < 1.0:
                    add(math.nextafter(endpoint, 0.0), f"{procedure}_nextdown")
                    add(math.nextafter(endpoint, 1.0), f"{procedure}_nextup")
    for probability in (ALPHA / 2.0, 1.0 - ALPHA / 2.0):
        add(beta_ppf(probability, kappa / 2.0, kappa / 2.0), "prior_tail")
    grid = sorted(sources)
    return grid, {point: "|".join(sorted(labels)) for point, labels in sources.items()}


def generate_coverage(
    rows: list[dict[str, Any]],
) -> tuple[bytes, list[dict[str, Any]], dict[int, dict[str, list[tuple[float, float]]]]]:
    summary_rows: list[dict[str, Any]] = []
    plot_curves: dict[int, dict[str, list[tuple[float, float]]]] = {}

    def records() -> Iterator[dict[str, Any]]:
        scenarios = [
            ("primary", PRIMARY_DENOMINATOR_ID, "trials_primary"),
            ("secondary_liberal", SECONDARY_DENOMINATOR_ID, "trials_secondary"),
        ]
        for scenario_id, denominator_id, trial_field in scenarios:
            for n in sorted({int(row[trial_field]) for row in rows}):
                for kappa in KAPPAS:
                    bayes_name = "bayes_equal_tail_primary" if kappa == PRIMARY_KAPPA else f"bayes_equal_tail_kappa_{fmt(kappa)}"
                    procedures = [bayes_name, "wilson", "clopper_pearson"]
                    interval_sets = {
                        procedure: [interval_for(procedure, n, y, kappa) for y in range(n + 1)]
                        for procedure in procedures
                    }
                    if coverage_at(n, 0.0, interval_sets["wilson"]) != 1.0:
                        fail("wilson_endpoint_closure", "CP02_coverage.csv", f"n={n}, p=0")
                    if coverage_at(n, 1.0, interval_sets["wilson"]) != 1.0:
                        fail("wilson_endpoint_closure", "CP02_coverage.csv", f"n={n}, p=1")
                    grid, sources = coverage_grid(interval_sets, kappa)
                    for procedure in procedures:
                        for y, (low, high) in enumerate(interval_sets[procedure]):
                            if procedure.startswith("bayes_equal_tail"):
                                a = kappa / 2.0 + y
                                b = kappa / 2.0 + n - y
                                posterior_mass = regularized_beta(high, a, b) - regularized_beta(low, a, b)
                            else:
                                posterior_mass = ""
                            yield {
                                "record_type": "interval",
                                "scenario_id": scenario_id,
                                "denominator_id": denominator_id,
                                "prior_id": prior_id(kappa),
                                "kappa": kappa,
                                "n": n,
                                "procedure": procedure,
                                "hypothetical_successes": y,
                                "interval_low": low,
                                "interval_high": high,
                                "interval_width": high - low,
                                "target_coverage": 1.0 - ALPHA,
                                "posterior_mass": posterior_mass,
                                "closed_interval": True,
                                "conditional_on_binomial_assumptions": True,
                                "status": "ok_conditional",
                                "reason": EMPIRICAL_TEST_SCOPE,
                            }
                        coverages: list[tuple[float, float]] = []
                        for p in grid:
                            coverage = coverage_at(n, p, interval_sets[procedure])
                            coverages.append((p, coverage))
                            if scenario_id == "primary" and kappa == PRIMARY_KAPPA and int(round(p * 1000)) % 10 == 0 and abs(p * 1000 - round(p * 1000)) < 1e-9:
                                plot_curves.setdefault(n, {}).setdefault(procedure, []).append((p, coverage))
                            yield {
                                "record_type": "curve",
                                "scenario_id": scenario_id,
                                "denominator_id": denominator_id,
                                "prior_id": prior_id(kappa),
                                "kappa": kappa,
                                "n": n,
                                "procedure": procedure,
                                "p_fixed": p,
                                "coverage": coverage,
                                "below_target": coverage < 1.0 - ALPHA - 1e-13,
                                "target_coverage": 1.0 - ALPHA,
                                "grid_point_source": sources[p],
                                "closed_interval": True,
                                "conditional_on_binomial_assumptions": True,
                                "status": "ok_conditional",
                                "reason": EMPIRICAL_TEST_SCOPE,
                            }
                        minimum_p, minimum_coverage = min(coverages, key=lambda item: (item[1], item[0]))
                        maximum_p, maximum_coverage = max(coverages, key=lambda item: (item[1], -item[0]))
                        threshold_coverage = coverage_at(n, THRESHOLD, interval_sets[procedure])
                        if procedure.startswith("bayes_equal_tail"):
                            predictive = beta_binomial_pmf(n, kappa / 2.0, kappa / 2.0)
                            masses = []
                            for y, (low, high) in enumerate(interval_sets[procedure]):
                                a = kappa / 2.0 + y
                                b = kappa / 2.0 + n - y
                                masses.append(regularized_beta(high, a, b) - regularized_beta(low, a, b))
                            prior_average = math.fsum(weight * mass for weight, mass in zip(predictive, masses, strict=True))
                            if abs(prior_average - 0.95) > 5e-10:
                                fail("prior_average_coverage", "CP02_coverage.csv", f"n={n}, kappa={kappa}: {prior_average}")
                        else:
                            prior_average = ""
                        if procedure == "clopper_pearson" and minimum_coverage < 0.95 - 2e-11:
                            fail("clopper_pearson_coverage", "CP02_coverage.csv", f"n={n}: grid minimum {minimum_coverage}")
                        summary = {
                            "record_type": "summary",
                            "scenario_id": scenario_id,
                            "denominator_id": denominator_id,
                            "prior_id": prior_id(kappa),
                            "kappa": kappa,
                            "n": n,
                            "procedure": procedure,
                            "target_coverage": 1.0 - ALPHA,
                            "grid_points": len(grid),
                            "grid_min": minimum_coverage,
                            "grid_max": maximum_coverage,
                            "grid_argmin": minimum_p,
                            "grid_argmax": maximum_p,
                            "coverage_at_threshold": threshold_coverage,
                            "prior_average_coverage": prior_average,
                            "closed_interval": True,
                            "conditional_on_binomial_assumptions": True,
                            "status": "ok_conditional",
                            "reason": EMPIRICAL_TEST_SCOPE + "; extrema are grid extrema, not global continuous extrema.",
                        }
                        summary_rows.append(summary)
                        yield summary

    payload = csv_bytes(COVERAGE_HEADER, records())
    return payload, summary_rows, plot_curves


def build_frequentist_rows(
    rows: list[dict[str, Any]], coverage_summaries: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    p_values = [binomial_upper_tail(row["trials_primary"], row["successes"], THRESHOLD) for row in rows]
    adjusted, rejected = holm_adjustment(p_values, ALPHA)
    output: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        n = row["trials_primary"]
        y = row["successes"]
        critical = next((k for k in range(n + 1) if binomial_upper_tail(n, k, THRESHOLD) <= ALPHA), n + 1)
        actual_size = binomial_upper_tail(n, critical, THRESHOLD)
        wilson_low, wilson_high = interval_for("wilson", n, y)
        cp_low, cp_high = interval_for("clopper_pearson", n, y)
        if actual_size > ALPHA + 1e-15:
            fail("exact_test_size", "CP02_frequentist_comparison.csv", f"n={n}, size={actual_size}")
        output.append(
            {
                "record_type": "cell",
                "scenario_id": "primary",
                "denominator_id": PRIMARY_DENOMINATOR_ID,
                "cell_id": row["cell_id"],
                "cell_label": row["cell_label"],
                "procedure": "exact_binomial_upper_tail",
                "n": n,
                "successes": y,
                "trials": n,
                "observed_rate": y / n,
                "wilson_low_95": wilson_low,
                "wilson_high_95": wilson_high,
                "cp_low_95": cp_low,
                "cp_high_95": cp_high,
                "exact_p_value": p_values[index],
                "critical_count": critical,
                "actual_size": actual_size,
                "raw_reject": p_values[index] <= ALPHA,
                "holm_adjusted_p": adjusted[index],
                "holm_reject": rejected[index],
                "empirical_test_scope": EMPIRICAL_TEST_SCOPE,
                "conditional_on_model_assumptions": True,
                "status": "ok_conditional",
                "reason": "Finite Binomial tail/interval inversion under fixed n; not unconditional empirical exactness.",
            }
        )

    for summary in coverage_summaries:
        if summary["scenario_id"] != "primary" or summary["kappa"] != PRIMARY_KAPPA:
            continue
        output.append(
            {
                "record_type": "coverage",
                "scenario_id": "primary",
                "denominator_id": PRIMARY_DENOMINATOR_ID,
                "procedure": summary["procedure"],
                "n": summary["n"],
                "grid_points": summary["grid_points"],
                "grid_min": summary["grid_min"],
                "grid_max": summary["grid_max"],
                "grid_argmin": summary["grid_argmin"],
                "grid_argmax": summary["grid_argmax"],
                "coverage_at_threshold": summary["coverage_at_threshold"],
                "empirical_test_scope": EMPIRICAL_TEST_SCOPE,
                "conditional_on_model_assumptions": True,
                "status": "ok_conditional",
                "reason": "Summary view of the full augmented-grid curve in CP02_coverage.csv.",
            }
        )

    primary_ns = sorted({row["trials_primary"] for row in rows})
    for n in primary_ns:
        critical = next((k for k in range(n + 1) if binomial_upper_tail(n, k, THRESHOLD) <= ALPHA), n + 1)
        powers = [(index / 1000.0, binomial_upper_tail(n, critical, index / 1000.0)) for index in range(1001)]
        first_p = next((p for p, power in powers if p > THRESHOLD and power >= 0.8), "")
        for p, power in powers:
            output.append(
                {
                    "record_type": "power",
                    "scenario_id": "primary",
                    "denominator_id": PRIMARY_DENOMINATOR_ID,
                    "procedure": "exact_binomial_upper_tail",
                    "n": n,
                    "p_fixed": p,
                    "critical_count": critical,
                    "power": power,
                    "first_p_at_or_above_80": first_p,
                    "empirical_test_scope": EMPIRICAL_TEST_SCOPE,
                    "conditional_on_model_assumptions": True,
                    "status": "ok_conditional",
                    "reason": "Design curve on the frozen p grid; not an estimate of observed p.",
                }
            )

    y_values = [row["successes"] for row in rows]
    primary_n = [row["trials_primary"] for row in rows]
    secondary_n = [row["trials_secondary"] for row in rows]
    primary_homogeneity = exact_conditional_homogeneity(y_values, primary_n)
    secondary_homogeneity = exact_conditional_homogeneity(y_values, secondary_n)
    for scenario, denominator, result in (
        ("primary", PRIMARY_DENOMINATOR_ID, primary_homogeneity),
        ("secondary_liberal", SECONDARY_DENOMINATOR_ID, secondary_homogeneity),
    ):
        output.append(
            {
                "record_type": "homogeneity",
                "scenario_id": scenario,
                "denominator_id": denominator,
                "procedure": "conditional_exact_deviance_ordering",
                "exact_conditional_p": result["exact_conditional_p"],
                "conditional_space_mass": result["conditional_space_mass"],
                "observed_deviance": result["observed_deviance"],
                "informative": result["informative"],
                "empirical_test_scope": EMPIRICAL_TEST_SCOPE,
                "conditional_on_model_assumptions": True,
                "status": "ok_conditional" if result["informative"] else "degenerate_not_informative",
                "reason": f"Integer-weight conditional enumeration/pruning visited {result['enumeration_nodes']} nodes; applicability remains conditional.",
            }
        )
    return output, primary_homogeneity, secondary_homogeneity


PREDICTIVE_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "model_id",
    "prior_id",
    "kappa",
    "cell_id",
    "cell_label",
    "successes",
    "trials",
    "k_rep",
    "predictive_probability",
    "predictive_mean",
    "predictive_variance",
    "mass_sum",
    "parameter_uncertainty_included",
    "conditional_on_model_assumptions",
    "status",
    "reason",
]


def build_posterior_predictive(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    y_values = [row["successes"] for row in rows]
    for scenario, denominator, trial_field in (
        ("primary", PRIMARY_DENOMINATOR_ID, "trials_primary"),
        ("secondary_liberal", SECONDARY_DENOMINATOR_ID, "trials_secondary"),
    ):
        n_values = [row[trial_field] for row in rows]
        total_y = sum(y_values)
        total_n = sum(n_values)
        for model_id in ("M0", "M1"):
            for row, y, n in zip(rows, y_values, n_values, strict=True):
                if model_id == "M0":
                    a = PRIMARY_KAPPA / 2.0 + total_y
                    b = PRIMARY_KAPPA / 2.0 + total_n - total_y
                else:
                    a = PRIMARY_KAPPA / 2.0 + y
                    b = PRIMARY_KAPPA / 2.0 + n - y
                probabilities = beta_binomial_pmf(n, a, b)
                mass = math.fsum(probabilities)
                mean = n * a / (a + b)
                variance = n * a * b * (a + b + n) / ((a + b) ** 2 * (a + b + 1.0))
                common = {
                    "scenario_id": scenario,
                    "denominator_id": denominator,
                    "model_id": model_id,
                    "prior_id": prior_id(PRIMARY_KAPPA),
                    "kappa": PRIMARY_KAPPA,
                    "cell_id": row["cell_id"],
                    "cell_label": row["cell_label"],
                    "successes": y,
                    "trials": n,
                    "predictive_mean": mean,
                    "predictive_variance": variance,
                    "mass_sum": mass,
                    "parameter_uncertainty_included": True,
                    "conditional_on_model_assumptions": True,
                    "status": "ok_conditional",
                    "reason": "Exact Beta-Binomial marginal; M0 cell marginals are cross-cell dependent.",
                }
                output.append({**common, "record_type": "summary"})
                for k_rep, probability in enumerate(probabilities):
                    output.append(
                        {
                            **common,
                            "record_type": "pmf",
                            "k_rep": k_rep,
                            "predictive_probability": probability,
                        }
                    )
    return output


DIAGNOSTICS_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "model_id",
    "prior_id",
    "kappa",
    "discrepancy",
    "observed_definition",
    "observed_median",
    "observed_low_95",
    "observed_high_95",
    "replicate_median",
    "replicate_low_95",
    "replicate_high_95",
    "tail_area",
    "replications",
    "rng",
    "rng_seed",
    "rng_stream",
    "mcse",
    "boundary_cells_observed",
    "design_id",
    "q",
    "residual_df",
    "information_rank",
    "minimum_standardized_eigenvalue",
    "identifiability_tolerance",
    "profile_log_kappa_min",
    "profile_log_kappa_max",
    "profile_step",
    "profile_boundary_maximum",
    "hyperprior_sensitivity_available",
    "dispersion_identified",
    "sequential_claim",
    "empirical_test_scope",
    "conditional_on_model_assumptions",
    "status",
    "reason",
]


def quantile_triplet(values: np.ndarray) -> tuple[float, float, float]:
    low, median, high = np.quantile(values, [0.025, 0.5, 0.975], method="linear")
    return float(median), float(low), float(high)


def contrast_edges(rows: list[dict[str, Any]]) -> list[tuple[int, int]]:
    lookup = {(row["transmitter"], row["year"]): index for index, row in enumerate(rows)}
    edges: list[tuple[int, int]] = []
    for year in (2019, 2020, 2021, 2022):
        edges.append((lookup[("PTT", year)], lookup[("VHF", year)]))
    for transmitter, years in (("VHF", range(2015, 2023)), ("PTT", range(2019, 2023))):
        year_list = list(years)
        for earlier, later in zip(year_list, year_list[1:]):
            edges.append((lookup[(transmitter, later)], lookup[(transmitter, earlier)]))
    return edges


def ppc_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    y = np.asarray([row["successes"] for row in rows], dtype=np.int64)
    edges = contrast_edges(rows)
    stream = 1
    for scenario, denominator, trial_field in (
        ("primary", PRIMARY_DENOMINATOR_ID, "trials_primary"),
        ("secondary_liberal", SECONDARY_DENOMINATOR_ID, "trials_secondary"),
    ):
        n = np.asarray([row[trial_field] for row in rows], dtype=np.int64)
        boundary_observed = int(np.sum((y == 0) | (y == n)))
        observed_rates = y / n
        observed_design = max(abs(observed_rates[left] - observed_rates[right]) for left, right in edges)
        for model_id in ("M0", "M1"):
            rng_stream = stream
            rng = np.random.Generator(np.random.PCG64(SEED).jumped(rng_stream))
            stream += 1
            if model_id == "M0":
                a = PRIMARY_KAPPA / 2.0 + int(np.sum(y))
                b = PRIMARY_KAPPA / 2.0 + int(np.sum(n - y))
                p_draw = rng.beta(a, b, size=PPC_REPLICATIONS)[:, None]
                p_matrix = np.broadcast_to(p_draw, (PPC_REPLICATIONS, len(rows)))
            else:
                a = PRIMARY_KAPPA / 2.0 + y
                b = PRIMARY_KAPPA / 2.0 + n - y
                p_matrix = rng.beta(a, b, size=(PPC_REPLICATIONS, len(rows)))
            y_rep = rng.binomial(n, p_matrix)
            safe_p = np.clip(p_matrix, np.finfo(float).tiny, np.nextafter(1.0, 0.0))
            denominator_sd = np.sqrt(n * safe_p * (1.0 - safe_p))
            z_observed = (y - n * safe_p) / denominator_sd
            z_replicate = (y_rep - n * safe_p) / denominator_sd
            observed_pearson = np.sum(z_observed * z_observed, axis=1)
            replicate_pearson = np.sum(z_replicate * z_replicate, axis=1)
            observed_max = np.max(np.abs(z_observed), axis=1)
            replicate_max = np.max(np.abs(z_replicate), axis=1)
            replicate_boundary = np.sum((y_rep == 0) | (y_rep == n), axis=1).astype(float)
            replicate_rates = y_rep / n
            replicate_design = np.maximum.reduce(
                [np.abs(replicate_rates[:, left] - replicate_rates[:, right]) for left, right in edges]
            )
            discrepancies = [
                ("pearson", "paired_draw_parameter_dependent", observed_pearson, replicate_pearson),
                ("max_abs_standardized_residual", "paired_draw_parameter_dependent", observed_max, replicate_max),
                ("boundary_cell_count", "fixed_observed_count", np.full(PPC_REPLICATIONS, boundary_observed, dtype=float), replicate_boundary),
                ("max_prespecified_design_contrast", "fixed_observed_design_contrasts", np.full(PPC_REPLICATIONS, observed_design, dtype=float), replicate_design),
            ]
            for discrepancy, observed_definition, observed_values, replicate_values in discrepancies:
                indicator = replicate_values >= observed_values
                tail = float(np.mean(indicator))
                mcse = math.sqrt(tail * (1.0 - tail) / PPC_REPLICATIONS)
                observed_median, observed_low, observed_high = quantile_triplet(observed_values)
                replicate_median, replicate_low, replicate_high = quantile_triplet(replicate_values)
                if not (0.0 <= tail <= 1.0 and 0.0 <= mcse <= 0.5 / math.sqrt(PPC_REPLICATIONS) + 1e-15):
                    fail("ppc_tail_mcse", "CP02_diagnostics.csv", f"{scenario}/{model_id}/{discrepancy}")
                output.append(
                    {
                        "record_type": "posterior_predictive",
                        "scenario_id": scenario,
                        "denominator_id": denominator,
                        "model_id": model_id,
                        "prior_id": prior_id(PRIMARY_KAPPA),
                        "kappa": PRIMARY_KAPPA,
                        "discrepancy": discrepancy,
                        "observed_definition": observed_definition,
                        "observed_median": observed_median,
                        "observed_low_95": observed_low,
                        "observed_high_95": observed_high,
                        "replicate_median": replicate_median,
                        "replicate_low_95": replicate_low,
                        "replicate_high_95": replicate_high,
                        "tail_area": tail,
                        "replications": PPC_REPLICATIONS,
                        "rng": "NumPy PCG64",
                        "rng_seed": SEED,
                        "rng_stream": rng_stream,
                        "mcse": mcse,
                        "boundary_cells_observed": boundary_observed,
                        "empirical_test_scope": "posterior_predictive_diagnostic_not_classical_p_value",
                        "conditional_on_model_assumptions": True,
                        "status": "ok_conditional_monte_carlo",
                        "reason": MODEL_ASSUMPTION_STATUS,
                    }
                )
        output.append(
            {
                "record_type": "sparsity_boundary",
                "scenario_id": scenario,
                "denominator_id": denominator,
                "model_id": "data_audit",
                "prior_id": prior_id(PRIMARY_KAPPA),
                "kappa": PRIMARY_KAPPA,
                "discrepancy": "boundary_cell_count",
                "boundary_cells_observed": boundary_observed,
                "empirical_test_scope": "descriptive_aggregate_count_audit",
                "conditional_on_model_assumptions": False,
                "status": "observed",
                "reason": "Boundary cells are valid Binomial counts; no pseudocount or continuity correction was added.",
            }
        )
    return output


DISPERSION_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "design_id",
    "q",
    "log_kappa",
    "kappa",
    "optimized_mean",
    "log_likelihood",
    "delta_from_profile_max",
    "at_profile_boundary",
    "profile_log_kappa_min",
    "profile_log_kappa_max",
    "profile_step",
    "identifiability_tolerance",
    "dispersion_identified",
    "status",
    "reason",
]


def beta_binomial_log_likelihood(y_values: list[int], n_values: list[int], mean: float, kappa: float) -> float:
    if not (0.0 < mean < 1.0 and kappa > 0.0):
        return -math.inf
    a = kappa * mean
    b = kappa * (1.0 - mean)
    return math.fsum(
        log_combination(n, y) + log_beta(y + a, n - y + b) - log_beta(a, b)
        for y, n in zip(y_values, n_values, strict=True)
    )


def logistic(eta: float) -> float:
    if eta >= 0.0:
        return 1.0 / (1.0 + math.exp(-eta))
    exponential = math.exp(eta)
    return exponential / (1.0 + exponential)


def optimize_intercept_mean(y_values: list[int], n_values: list[int], kappa: float) -> tuple[float, float, float]:
    left = -12.0
    right = 12.0
    inverse_phi = (math.sqrt(5.0) - 1.0) / 2.0
    c = right - inverse_phi * (right - left)
    d = left + inverse_phi * (right - left)
    fc = beta_binomial_log_likelihood(y_values, n_values, logistic(c), kappa)
    fd = beta_binomial_log_likelihood(y_values, n_values, logistic(d), kappa)
    for _ in range(160):
        if fc > fd:
            right, d, fd = d, c, fc
            c = right - inverse_phi * (right - left)
            fc = beta_binomial_log_likelihood(y_values, n_values, logistic(c), kappa)
        else:
            left, c, fc = c, d, fd
            d = left + inverse_phi * (right - left)
            fd = beta_binomial_log_likelihood(y_values, n_values, logistic(d), kappa)
    eta = (left + right) / 2.0
    mean = logistic(eta)
    return mean, eta, beta_binomial_log_likelihood(y_values, n_values, mean, kappa)


def observed_information(
    y_values: list[int], n_values: list[int], eta: float, log_kappa_value: float
) -> tuple[int, float]:
    step = 1e-4

    def objective(eta_value: float, log_kappa_argument: float) -> float:
        return beta_binomial_log_likelihood(
            y_values, n_values, logistic(eta_value), math.exp(log_kappa_argument)
        )

    center = objective(eta, log_kappa_value)
    d_eta_eta = (objective(eta + step, log_kappa_value) - 2.0 * center + objective(eta - step, log_kappa_value)) / (step * step)
    d_k_k = (objective(eta, log_kappa_value + step) - 2.0 * center + objective(eta, log_kappa_value - step)) / (step * step)
    mixed = (
        objective(eta + step, log_kappa_value + step)
        - objective(eta + step, log_kappa_value - step)
        - objective(eta - step, log_kappa_value + step)
        + objective(eta - step, log_kappa_value - step)
    ) / (4.0 * step * step)
    information = np.asarray([[-d_eta_eta, -mixed], [-mixed, -d_k_k]], dtype=float)
    diagonal = np.diag(information)
    if np.any(diagonal <= 0.0) or not np.all(np.isfinite(information)):
        return 0, float("-inf")
    scale = np.diag(1.0 / np.sqrt(diagonal))
    standardized = scale @ information @ scale
    eigenvalues = np.linalg.eigvalsh(standardized)
    minimum = float(np.min(eigenvalues))
    rank = int(np.sum(eigenvalues > IDENTIFIABILITY_TOLERANCE))
    return rank, minimum


def build_dispersion_profile(
    rows: list[dict[str, Any]], diagnostics: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    y_values = [row["successes"] for row in rows]
    point_count = int(round((PROFILE_LOG_KAPPA_MAX - PROFILE_LOG_KAPPA_MIN) / PROFILE_LOG_KAPPA_STEP)) + 1
    for scenario, denominator, trial_field in (
        ("primary", PRIMARY_DENOMINATOR_ID, "trials_primary"),
        ("secondary_liberal", SECONDARY_DENOMINATOR_ID, "trials_secondary"),
    ):
        n_values = [row[trial_field] for row in rows]
        profile: list[dict[str, Any]] = []
        for index in range(point_count):
            log_kappa_value = PROFILE_LOG_KAPPA_MIN + index * PROFILE_LOG_KAPPA_STEP
            kappa = math.exp(log_kappa_value)
            mean, eta, likelihood = optimize_intercept_mean(y_values, n_values, kappa)
            profile.append(
                {
                    "record_type": "profile",
                    "scenario_id": scenario,
                    "denominator_id": denominator,
                    "design_id": "intercept_only",
                    "q": 1,
                    "log_kappa": log_kappa_value,
                    "kappa": kappa,
                    "optimized_mean": mean,
                    "log_likelihood": likelihood,
                    "_eta": eta,
                }
            )
        maximum_index = max(range(len(profile)), key=lambda index: profile[index]["log_likelihood"])
        maximum = profile[maximum_index]["log_likelihood"]
        boundary = maximum_index in (0, len(profile) - 1)
        rank, minimum_eigenvalue = observed_information(
            y_values,
            n_values,
            profile[maximum_index]["_eta"],
            profile[maximum_index]["log_kappa"],
        )
        # No hyperprior family was licensed by the frozen aggregate contract.
        # The all-gates rule therefore yields a supported non-identification
        # result even if the finite-grid likelihood happens to be curved.
        hyperprior_available = False
        dispersion_identified = bool(
            len(rows) - 1 > 1
            and rank == 2
            and minimum_eigenvalue > IDENTIFIABILITY_TOLERANCE
            and not boundary
            and hyperprior_available
        )
        reason = (
            "unsupported_identification: hyperprior sensitivity is unavailable in the frozen contract; "
            "aggregate cells do not separate overdispersion, cell heterogeneity, and dependence"
        )
        for index, record in enumerate(profile):
            record.pop("_eta")
            record.update(
                {
                    "delta_from_profile_max": record["log_likelihood"] - maximum,
                    "at_profile_boundary": index in (0, len(profile) - 1),
                    "profile_log_kappa_min": PROFILE_LOG_KAPPA_MIN,
                    "profile_log_kappa_max": PROFILE_LOG_KAPPA_MAX,
                    "profile_step": PROFILE_LOG_KAPPA_STEP,
                    "identifiability_tolerance": IDENTIFIABILITY_TOLERANCE,
                    "dispersion_identified": dispersion_identified,
                    "status": "unsupported_identification",
                    "reason": reason,
                }
            )
            output.append(record)
        diagnostics.append(
            {
                "record_type": "dispersion_identifiability",
                "scenario_id": scenario,
                "denominator_id": denominator,
                "model_id": "beta_binomial_overdispersion_candidate",
                "design_id": "intercept_only",
                "q": 1,
                "residual_df": len(rows) - 1 - 1,
                "information_rank": rank,
                "minimum_standardized_eigenvalue": "" if not math.isfinite(minimum_eigenvalue) else minimum_eigenvalue,
                "identifiability_tolerance": IDENTIFIABILITY_TOLERANCE,
                "profile_log_kappa_min": PROFILE_LOG_KAPPA_MIN,
                "profile_log_kappa_max": PROFILE_LOG_KAPPA_MAX,
                "profile_step": PROFILE_LOG_KAPPA_STEP,
                "profile_boundary_maximum": boundary,
                "hyperprior_sensitivity_available": hyperprior_available,
                "dispersion_identified": dispersion_identified,
                "empirical_test_scope": "deterministic_identifiability_gate_not_a_model_selection_test",
                "conditional_on_model_assumptions": True,
                "status": "unsupported_identification",
                "reason": reason,
            }
        )
        diagnostics.append(
            {
                "record_type": "dispersion_identifiability",
                "scenario_id": scenario,
                "denominator_id": denominator,
                "model_id": "cell_specific_binomial_plus_dispersion",
                "design_id": "saturated_cell_means",
                "q": len(rows),
                "residual_df": len(rows) - len(rows) - 1,
                "information_rank": 0,
                "identifiability_tolerance": IDENTIFIABILITY_TOLERANCE,
                "profile_log_kappa_min": PROFILE_LOG_KAPPA_MIN,
                "profile_log_kappa_max": PROFILE_LOG_KAPPA_MAX,
                "profile_step": PROFILE_LOG_KAPPA_STEP,
                "profile_boundary_maximum": "",
                "hyperprior_sensitivity_available": False,
                "dispersion_identified": False,
                "empirical_test_scope": "deterministic_identifiability_gate_not_a_model_selection_test",
                "conditional_on_model_assumptions": True,
                "status": "not_identifiable_saturated",
                "reason": "Twelve free cell means leave no between-cell replication for an additional dispersion mechanism.",
            }
        )
    diagnostics.append(
        {
            "record_type": "optional_stopping",
            "scenario_id": "primary",
            "denominator_id": PRIMARY_DENOMINATOR_ID,
            "model_id": "M1_over_M0",
            "sequential_claim": False,
            "empirical_test_scope": "fixed_aggregate_dataset_only",
            "conditional_on_model_assumptions": True,
            "status": "not_available",
            "reason": "No stopping history, filtration, monitoring rule, or frozen sequential thresholds are present.",
        }
    )
    diagnostics.append(
        {
            "record_type": "assumption_scope",
            "scenario_id": "primary",
            "denominator_id": PRIMARY_DENOMINATOR_ID,
            "model_id": "all",
            "empirical_test_scope": EMPIRICAL_TEST_SCOPE,
            "conditional_on_model_assumptions": True,
            "status": "conditional_illustrative",
            "reason": MODEL_ASSUMPTION_STATUS,
        }
    )
    return output


SENSITIVITY_HEADER = [
    "record_type",
    "sensitivity_type",
    "scenario_id",
    "prior_id",
    "kappa",
    "denominator_id",
    "target_id",
    "target_label",
    "estimand_id",
    "contrast_id",
    "posterior_mean",
    "posterior_median",
    "credible_low_95",
    "credible_high_95",
    "prob_gt_threshold",
    "bayes_action",
    "log_bf10",
    "bf10",
    "prior_odds_10",
    "posterior_odds_10",
    "exact_conditional_p",
    "observed_rate",
    "delta_posterior_mean",
    "abs_delta_posterior_mean",
    "delta_observed_rate",
    "abs_delta_observed_rate",
    "delta_log_bf10",
    "delta_primary_target",
    "delta_from_primary",
    "decision_changed",
    "moment_status",
    "defined_status",
    "status",
    "reason",
]


INFLUENCE_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "prior_id",
    "kappa",
    "deleted_cell_id",
    "deleted_cell_label",
    "metric_type",
    "metric_scale",
    "full_value",
    "loo_value",
    "signed_change",
    "absolute_change",
    "defined_status",
    "status",
    "reason",
]


def build_sensitivity_and_influence(
    rows: list[dict[str, Any]],
    primary_homogeneity: dict[str, Any],
    secondary_homogeneity: dict[str, Any],
    primary_model: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sensitivity: list[dict[str, Any]] = []
    influence: list[dict[str, Any]] = []
    y_values = [row["successes"] for row in rows]
    primary_n = [row["trials_primary"] for row in rows]
    secondary_n = [row["trials_secondary"] for row in rows]
    primary_stats = {
        row["cell_id"]: posterior_stats(row["successes"], row["trials_primary"], PRIMARY_KAPPA)
        for row in rows
    }
    primary_actions = {cell_id: stats["bayes_action"] for cell_id, stats in primary_stats.items()}

    for kappa in KAPPAS:
        model = model_comparison(y_values, primary_n, kappa)
        for row in rows:
            stats = posterior_stats(row["successes"], row["trials_primary"], kappa)
            baseline = primary_stats[row["cell_id"]]
            delta_mean = stats["posterior_mean"] - baseline["posterior_mean"]
            sensitivity.append(
                {
                    "record_type": "cell",
                    "sensitivity_type": "prior",
                    "scenario_id": scenario_id_for_prior(kappa),
                    "prior_id": prior_id(kappa),
                    "kappa": kappa,
                    "denominator_id": PRIMARY_DENOMINATOR_ID,
                    "target_id": row["cell_id"],
                    "target_label": row["cell_label"],
                    "estimand_id": "cell_probability_primary",
                    "posterior_mean": stats["posterior_mean"],
                    "credible_low_95": stats["credible_low_95"],
                    "credible_high_95": stats["credible_high_95"],
                    "prob_gt_threshold": stats["prob_gt_threshold"],
                    "bayes_action": stats["bayes_action"],
                    "log_bf10": model["log_bf10"],
                    "bf10": model["bf10"],
                    "prior_odds_10": model["prior_odds_10"],
                    "posterior_odds_10": model["posterior_odds_10"],
                    "exact_conditional_p": primary_homogeneity["exact_conditional_p"],
                    "observed_rate": row["observed_rate"],
                    "delta_posterior_mean": delta_mean,
                    "abs_delta_posterior_mean": abs(delta_mean),
                    "delta_observed_rate": 0.0,
                    "abs_delta_observed_rate": 0.0,
                    "delta_log_bf10": model["log_bf10"] - primary_model["log_bf10"],
                    "delta_from_primary": delta_mean,
                    "decision_changed": stats["bayes_action"] != primary_actions[row["cell_id"]],
                    "moment_status": "finite",
                    "defined_status": "defined",
                    "status": "ok_conditional",
                    "reason": "Proper symmetric prior sensitivity with the same primary estimand.",
                }
            )
        sensitivity.append(
            {
                "record_type": "model",
                "sensitivity_type": "bf_prior_scale",
                "scenario_id": scenario_id_for_prior(kappa),
                "prior_id": prior_id(kappa),
                "kappa": kappa,
                "denominator_id": PRIMARY_DENOMINATOR_ID,
                "target_id": "M1_over_M0",
                "target_label": "M1 over M0",
                "estimand_id": "model_evidence_ratio",
                "log_bf10": model["log_bf10"],
                "bf10": model["bf10"],
                "prior_odds_10": model["prior_odds_10"],
                "posterior_odds_10": model["posterior_odds_10"],
                "delta_log_bf10": model["log_bf10"] - primary_model["log_bf10"],
                "delta_from_primary": model["log_bf10"] - primary_model["log_bf10"],
                "decision_changed": model["selected_action"] != primary_model["selected_action"],
                "moment_status": "finite",
                "defined_status": "defined",
                "status": "ok_conditional",
                "reason": "M0 and all M1 cells use the same proper Beta(kappa/2,kappa/2) prior.",
            }
        )

    secondary_model = model_comparison(y_values, secondary_n, PRIMARY_KAPPA)
    for row in rows:
        stats = posterior_stats(row["successes"], row["trials_secondary"], PRIMARY_KAPPA)
        baseline = primary_stats[row["cell_id"]]
        delta_mean = stats["posterior_mean"] - baseline["posterior_mean"]
        delta_rate = row["observed_rate_secondary"] - row["observed_rate"]
        sensitivity.append(
            {
                "record_type": "cell",
                "sensitivity_type": "denominator",
                "scenario_id": "secondary_liberal",
                "prior_id": prior_id(PRIMARY_KAPPA),
                "kappa": PRIMARY_KAPPA,
                "denominator_id": SECONDARY_DENOMINATOR_ID,
                "target_id": row["cell_id"],
                "target_label": row["cell_label"],
                "estimand_id": "cell_probability_secondary_distinct_trial_population",
                "posterior_mean": stats["posterior_mean"],
                "credible_low_95": stats["credible_low_95"],
                "credible_high_95": stats["credible_high_95"],
                "prob_gt_threshold": stats["prob_gt_threshold"],
                "bayes_action": stats["bayes_action"],
                "log_bf10": secondary_model["log_bf10"],
                "bf10": secondary_model["bf10"],
                "prior_odds_10": secondary_model["prior_odds_10"],
                "posterior_odds_10": secondary_model["posterior_odds_10"],
                "exact_conditional_p": secondary_homogeneity["exact_conditional_p"],
                "observed_rate": row["observed_rate_secondary"],
                "delta_posterior_mean": delta_mean,
                "abs_delta_posterior_mean": abs(delta_mean),
                "delta_observed_rate": delta_rate,
                "abs_delta_observed_rate": abs(delta_rate),
                "delta_log_bf10": secondary_model["log_bf10"] - primary_model["log_bf10"],
                "delta_from_primary": delta_mean,
                "decision_changed": stats["bayes_action"] != primary_actions[row["cell_id"]],
                "moment_status": "finite",
                "defined_status": "defined_distinct_estimand",
                "status": "ok_distinct_estimand",
                "reason": "The liberal denominator changes the eligible trial population and may change the estimand.",
            }
        )

    total_y = sum(y_values)
    total_n = sum(primary_n)
    pooled_full = posterior_stats(total_y, total_n, PRIMARY_KAPPA)
    full_metrics: dict[str, tuple[str, float]] = {
        "log_bf10": ("log_evidence", float(primary_model["log_bf10"])),
        "pooled_posterior_mean": ("probability", float(pooled_full["posterior_mean"])),
        "pooled_prob_gt_threshold": ("probability", float(pooled_full["prob_gt_threshold"])),
        "pooled_credible_low_95": ("probability_endpoint", float(pooled_full["credible_low_95"])),
        "pooled_credible_high_95": ("probability_endpoint", float(pooled_full["credible_high_95"])),
    }
    for deleted_index, deleted in enumerate(rows):
        loo_y = y_values[:deleted_index] + y_values[deleted_index + 1 :]
        loo_n = primary_n[:deleted_index] + primary_n[deleted_index + 1 :]
        loo_model = model_comparison(loo_y, loo_n, PRIMARY_KAPPA)
        loo_pooled = posterior_stats(sum(loo_y), sum(loo_n), PRIMARY_KAPPA)
        loo_metrics: dict[str, float] = {
            "log_bf10": float(loo_model["log_bf10"]),
            "pooled_posterior_mean": float(loo_pooled["posterior_mean"]),
            "pooled_prob_gt_threshold": float(loo_pooled["prob_gt_threshold"]),
            "pooled_credible_low_95": float(loo_pooled["credible_low_95"]),
            "pooled_credible_high_95": float(loo_pooled["credible_high_95"]),
        }
        for metric_type, (metric_scale, full_value) in full_metrics.items():
            loo_value = loo_metrics[metric_type]
            change = loo_value - full_value
            influence.append(
                {
                    "record_type": "leave_one_cell_out",
                    "scenario_id": "primary",
                    "denominator_id": PRIMARY_DENOMINATOR_ID,
                    "prior_id": prior_id(PRIMARY_KAPPA),
                    "kappa": PRIMARY_KAPPA,
                    "deleted_cell_id": deleted["cell_id"],
                    "deleted_cell_label": deleted["cell_label"],
                    "metric_type": metric_type,
                    "metric_scale": metric_scale,
                    "full_value": full_value,
                    "loo_value": loo_value,
                    "signed_change": change,
                    "absolute_change": abs(change),
                    "defined_status": "defined",
                    "status": "ok_conditional",
                    "reason": "Typed LOO metric; magnitudes are compared only within metric_type/metric_scale.",
                }
            )
        pooled_change = loo_metrics["pooled_posterior_mean"] - full_metrics["pooled_posterior_mean"][1]
        sensitivity.append(
            {
                "record_type": "loo_pooled_mean",
                "sensitivity_type": "leave_one_cell_out",
                "scenario_id": f"loo_{deleted['cell_id']}",
                "prior_id": prior_id(PRIMARY_KAPPA),
                "kappa": PRIMARY_KAPPA,
                "denominator_id": PRIMARY_DENOMINATOR_ID,
                "target_id": deleted["cell_id"],
                "target_label": deleted["cell_label"],
                "estimand_id": "pooled_posterior_mean_only",
                "posterior_mean": loo_metrics["pooled_posterior_mean"],
                "credible_low_95": loo_metrics["pooled_credible_low_95"],
                "credible_high_95": loo_metrics["pooled_credible_high_95"],
                "prob_gt_threshold": loo_metrics["pooled_prob_gt_threshold"],
                "bayes_action": loo_pooled["bayes_action"],
                "log_bf10": loo_metrics["log_bf10"],
                "bf10": loo_model["bf10"],
                "prior_odds_10": loo_model["prior_odds_10"],
                "posterior_odds_10": loo_model["posterior_odds_10"],
                "delta_log_bf10": loo_metrics["log_bf10"] - full_metrics["log_bf10"][1],
                "delta_primary_target": pooled_change,
                "delta_from_primary": pooled_change,
                "decision_changed": loo_pooled["bayes_action"] != pooled_full["bayes_action"],
                "moment_status": "finite",
                "defined_status": "defined",
                "status": "ok_conditional",
                "reason": "delta_primary_target is narrowly typed as pooled_posterior_mean; other scales live in CP02_influence.csv.",
            }
        )
    if len({record["deleted_cell_id"] for record in influence}) != len(rows):
        fail("loo_inventory", "CP02_influence.csv", "each cell must be deleted exactly once per metric")
    return sensitivity, influence


CONTRAST_HEADER = [
    "record_type",
    "scenario_id",
    "denominator_id",
    "prior_id",
    "kappa",
    "contrast_id",
    "contrast_family",
    "left_cell_id",
    "left_cell_label",
    "right_cell_id",
    "right_cell_label",
    "estimand",
    "posterior_mean",
    "posterior_median",
    "credible_low_95",
    "credible_high_95",
    "prob_gt_zero",
    "mcse",
    "draws",
    "rng",
    "rng_seed",
    "rng_stream",
    "moment_status",
    "conditional_on_model_assumptions",
    "status",
    "reason",
]


def contrast_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {(row["transmitter"], row["year"]): row for row in rows}
    output: list[dict[str, Any]] = []
    for year in (2019, 2020, 2021, 2022):
        output.append(
            {
                "contrast_id": f"PTT_minus_VHF_{year}",
                "contrast_family": "transmitter_within_shared_year",
                "left": lookup[("PTT", year)],
                "right": lookup[("VHF", year)],
            }
        )
    for transmitter, first, last in (("VHF", 2015, 2022), ("PTT", 2019, 2022)):
        for later in range(first + 1, last + 1):
            output.append(
                {
                    "contrast_id": f"{transmitter}_{later}_minus_{later - 1}",
                    "contrast_family": "adjacent_year_within_transmitter",
                    "left": lookup[(transmitter, later)],
                    "right": lookup[(transmitter, later - 1)],
                }
            )
    return output


def build_contrasts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    scenarios = [
        (scenario_id_for_prior(kappa), PRIMARY_DENOMINATOR_ID, "trials_primary", kappa)
        for kappa in KAPPAS
    ] + [("secondary_liberal", SECONDARY_DENOMINATOR_ID, "trials_secondary", PRIMARY_KAPPA)]
    stream = 1000
    for scenario_id, denominator_id, trial_field, kappa in scenarios:
        for pair in contrast_pairs(rows):
            left = pair["left"]
            right = pair["right"]
            left_a = kappa / 2.0 + left["successes"]
            left_b = kappa / 2.0 + left[trial_field] - left["successes"]
            right_a = kappa / 2.0 + right["successes"]
            right_b = kappa / 2.0 + right[trial_field] - right["successes"]
            rng_stream = stream
            stream += 1
            rng = np.random.Generator(np.random.PCG64(SEED).jumped(rng_stream))
            left_draw = rng.beta(left_a, left_b, size=CONTRAST_DRAWS)
            right_draw = rng.beta(right_a, right_b, size=CONTRAST_DRAWS)
            difference = left_draw - right_draw
            difference_median, difference_low, difference_high = quantile_triplet(difference)
            probability = float(np.mean(difference > 0.0))
            probability_mcse = math.sqrt(probability * (1.0 - probability) / CONTRAST_DRAWS)
            common = {
                "scenario_id": scenario_id,
                "denominator_id": denominator_id,
                "prior_id": prior_id(kappa),
                "kappa": kappa,
                "contrast_id": pair["contrast_id"],
                "contrast_family": pair["contrast_family"],
                "left_cell_id": left["cell_id"],
                "left_cell_label": left["cell_label"],
                "right_cell_id": right["cell_id"],
                "right_cell_label": right["cell_label"],
                "prob_gt_zero": probability,
                "mcse": probability_mcse,
                "draws": CONTRAST_DRAWS,
                "rng": "NumPy PCG64",
                "rng_seed": SEED,
                "rng_stream": rng_stream,
                "conditional_on_model_assumptions": True,
                "status": "ok_conditional_monte_carlo",
            }
            output.append(
                {
                    **common,
                    "record_type": "contrast",
                    "estimand": "probability_difference",
                    "posterior_mean": left_a / (left_a + left_b) - right_a / (right_a + right_b),
                    "posterior_median": difference_median,
                    "credible_low_95": difference_low,
                    "credible_high_95": difference_high,
                    "moment_status": "finite",
                    "reason": "Exact difference mean; PCG64 median/equal-tail interval/direction probability.",
                }
            )
            clipped_left = np.clip(left_draw, np.finfo(float).tiny, np.nextafter(1.0, 0.0))
            clipped_right = np.clip(right_draw, np.finfo(float).tiny, np.nextafter(1.0, 0.0))
            odds_ratio = (clipped_left / (1.0 - clipped_left)) / (clipped_right / (1.0 - clipped_right))
            odds_median, odds_low, odds_high = quantile_triplet(odds_ratio)
            mean_finite = left_b > 1.0 and right_a > 1.0
            moment_status = "finite_but_mean_not_reported_by_contract" if mean_finite else "infinite_moment"
            output.append(
                {
                    **common,
                    "record_type": "contrast",
                    "estimand": "odds_ratio",
                    "posterior_mean": "",
                    "posterior_median": odds_median,
                    "credible_low_95": odds_low,
                    "credible_high_95": odds_high,
                    "moment_status": moment_status,
                    "reason": (
                        "Median/equal-tail quantiles only; no finite mean is reported. "
                        + ("The mathematical posterior mean diverges for these shapes." if not mean_finite else "The mean is deliberately omitted for schema consistency.")
                    ),
                }
            )
    return output


def svg_bytes(lines: list[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_intervals_svg(
    rows: list[dict[str, Any]], posterior_rows: list[dict[str, Any]], frequentist_rows: list[dict[str, Any]]
) -> bytes:
    posterior = {row["cell_id"]: row for row in posterior_rows if row["record_type"] == "cell"}
    frequentist = {row["cell_id"]: row for row in frequentist_rows if row["record_type"] == "cell"}
    width, height = 1000, 760
    left, right = 230.0, 950.0
    top, row_gap = 105.0, 50.0

    def x_position(probability: float) -> float:
        return left + probability * (right - left)

    desc = (
        "Selang peluang bersarang per sel agregat dengan penyebut primer yang konservatif. "
        "Lingkaran bergaris utuh menunjukkan rataan posterior Beta(2,2) dan selang kredibel ekor setara; persegi bergaris putus-putus menunjukkan interval Wilson; "
        "belah ketupat bergaris titik menunjukkan interval Clopper-Pearson. Perhitungan bersifat bersyarat dan tidak mengidentifikasi efek kausal pemancar atau tahun."
    )
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="cp02-int-title cp02-int-desc">',
        '<title id="cp02-int-title">Interval sel primer CP02: Bayes, Wilson, dan Clopper-Pearson</title>',
        f'<desc id="cp02-int-desc">{xml_escape(desc)}</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial, sans-serif" fill="black">',
        '<text x="500" y="30" text-anchor="middle" font-size="18" font-weight="bold">Interval sel agregat CP02 (penyebut primer)</text>',
        '<text x="500" y="53" text-anchor="middle" font-size="12">Ringkasan model kerja bersyarat; bukan efek kausal atau jaminan empiris tanpa syarat</text>',
    ]
    for tick in range(0, 11):
        probability = tick / 10.0
        x = x_position(probability)
        lines.append(f'<line x1="{x:.3f}" y1="75" x2="{x:.3f}" y2="{top + row_gap * len(rows):.3f}" stroke="#d0d0d0" stroke-width="1"/>')
        lines.append(f'<text x="{x:.3f}" y="{top + row_gap * len(rows) + 25:.3f}" text-anchor="middle" font-size="11">{fmt_id(probability)}</text>')
    threshold_x = x_position(THRESHOLD)
    lines.append(f'<line x1="{threshold_x:.3f}" y1="75" x2="{threshold_x:.3f}" y2="{top + row_gap * len(rows):.3f}" stroke="black" stroke-width="1.5" stroke-dasharray="8 5"/>')
    for index, row in enumerate(rows):
        y_center = top + index * row_gap
        post = posterior[row["cell_id"]]
        freq = frequentist[row["cell_id"]]
        lines.append(f'<text x="{left - 12:.3f}" y="{y_center + 4:.3f}" text-anchor="end" font-size="12">{xml_escape(row["cell_label"])}</text>')
        # Posterior: solid line and circle.
        lines.append(f'<line x1="{x_position(post["credible_low_95"]):.3f}" y1="{y_center - 10:.3f}" x2="{x_position(post["credible_high_95"]):.3f}" y2="{y_center - 10:.3f}" stroke="black" stroke-width="3"/>')
        lines.append(f'<circle cx="{x_position(post["posterior_mean"]):.3f}" cy="{y_center - 10:.3f}" r="4" fill="white" stroke="black" stroke-width="2"/>')
        # Wilson: dashed line and square.
        lines.append(f'<line x1="{x_position(freq["wilson_low_95"]):.3f}" y1="{y_center:.3f}" x2="{x_position(freq["wilson_high_95"]):.3f}" y2="{y_center:.3f}" stroke="#333" stroke-width="2" stroke-dasharray="7 4"/>')
        observed_x = x_position(row["observed_rate"])
        lines.append(f'<rect x="{observed_x - 4:.3f}" y="{y_center - 4:.3f}" width="8" height="8" fill="white" stroke="#333" stroke-width="2"/>')
        # Clopper-Pearson: dotted and diamond.
        lines.append(f'<line x1="{x_position(freq["cp_low_95"]):.3f}" y1="{y_center + 10:.3f}" x2="{x_position(freq["cp_high_95"]):.3f}" y2="{y_center + 10:.3f}" stroke="#555" stroke-width="2" stroke-dasharray="2 4"/>')
        lines.append(f'<path d="M {observed_x:.3f} {y_center + 5:.3f} L {observed_x + 5:.3f} {y_center + 10:.3f} L {observed_x:.3f} {y_center + 15:.3f} L {observed_x - 5:.3f} {y_center + 10:.3f} Z" fill="white" stroke="#555" stroke-width="2"/>')
    legend_y = height - 42
    lines.extend(
        [
            f'<line x1="250" y1="{legend_y}" x2="300" y2="{legend_y}" stroke="black" stroke-width="3"/><circle cx="275" cy="{legend_y}" r="4" fill="white" stroke="black" stroke-width="2"/><text x="310" y="{legend_y + 4}" font-size="11">Bayes ekor setara</text>',
            f'<line x1="465" y1="{legend_y}" x2="515" y2="{legend_y}" stroke="#333" stroke-width="2" stroke-dasharray="7 4"/><rect x="486" y="{legend_y - 4}" width="8" height="8" fill="white" stroke="#333" stroke-width="2"/><text x="525" y="{legend_y + 4}" font-size="11">Wilson</text>',
            f'<line x1="640" y1="{legend_y}" x2="690" y2="{legend_y}" stroke="#555" stroke-width="2" stroke-dasharray="2 4"/><path d="M 665 {legend_y - 5} L 670 {legend_y} L 665 {legend_y + 5} L 660 {legend_y} Z" fill="white" stroke="#555" stroke-width="2"/><text x="700" y="{legend_y + 4}" font-size="11">Clopper-Pearson</text>',
            '</g>',
            '</svg>',
        ]
    )
    return svg_bytes(lines)


def build_coverage_svg(plot_curves: dict[int, dict[str, list[tuple[float, float]]]]) -> bytes:
    n_values = sorted(plot_curves)
    columns = 4
    panel_width, panel_height = 235, 205
    width = 1000
    rows_count = math.ceil(len(n_values) / columns)
    height = 105 + rows_count * panel_height + 70
    desc = (
        f"Panel kecil untuk {len(n_values)} penyebut primer yang berbeda. Parameter p tetap berada pada sumbu mendatar dan cakupan jumlah-hingga eksak berada pada sumbu tegak. "
        "Garis utuh, putus-putus, dan titik menunjukkan aturan ekor setara Beta(2,2), Wilson, dan Clopper-Pearson; garis acuan mendatar bernilai 0,95. "
        "Ini adalah perhitungan hukum sampling bersyarat, bukan peluang posterior atau validasi tanpa syarat atas unit agregat."
    )
    styles = {
        "bayes_equal_tail_primary": ("black", ""),
        "wilson": ("#333", "7 4"),
        "clopper_pearson": ("#666", "2 4"),
    }
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="cp02-cov-title cp02-cov-desc">',
        '<title id="cp02-cov-title">Cakupan CP02 pada parameter tetap menurut penyebut primer</title>',
        f'<desc id="cp02-cov-desc">{xml_escape(desc)}</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial, sans-serif" fill="black">',
        '<text x="500" y="28" text-anchor="middle" font-size="18" font-weight="bold">Cakupan interval pada parameter tetap menurut penyebut</text>',
        '<text x="500" y="49" text-anchor="middle" font-size="11">Penyebut primer, κ=4; jumlah Binomial hingga yang eksak pada kisi gambar yang dibekukan</text>',
    ]
    for panel_index, n in enumerate(n_values):
        column = panel_index % columns
        row = panel_index // columns
        x0 = 45 + column * panel_width
        y0 = 78 + row * panel_height
        plot_left, plot_top = x0 + 28, y0 + 22
        plot_width, plot_height = 180, 145
        lines.append(f'<rect x="{plot_left}" y="{plot_top}" width="{plot_width}" height="{plot_height}" fill="none" stroke="#aaa"/>')
        lines.append(f'<text x="{plot_left + plot_width / 2:.3f}" y="{y0 + 13}" text-anchor="middle" font-size="12" font-weight="bold">n={n}</text>')
        target_y = plot_top + (1.0 - 0.95) * plot_height
        lines.append(f'<line x1="{plot_left}" y1="{target_y:.3f}" x2="{plot_left + plot_width}" y2="{target_y:.3f}" stroke="#888" stroke-width="1" stroke-dasharray="3 3"/>')
        for procedure in ("bayes_equal_tail_primary", "wilson", "clopper_pearson"):
            points = plot_curves[n].get(procedure, [])
            coordinates = " ".join(
                f"{plot_left + p * plot_width:.3f},{plot_top + (1.0 - coverage) * plot_height:.3f}"
                for p, coverage in points
            )
            color, dash = styles[procedure]
            dash_attribute = f' stroke-dasharray="{dash}"' if dash else ""
            lines.append(f'<polyline points="{coordinates}" fill="none" stroke="{color}" stroke-width="1.5"{dash_attribute}/>' )
        lines.append(f'<text x="{plot_left}" y="{plot_top + plot_height + 15}" font-size="9">0</text>')
        lines.append(f'<text x="{plot_left + plot_width}" y="{plot_top + plot_height + 15}" text-anchor="end" font-size="9">1</text>')
        lines.append(f'<text x="{plot_left + plot_width / 2:.3f}" y="{plot_top + plot_height + 15}" text-anchor="middle" font-size="9">p tetap</text>')
    legend_y = height - 35
    lines.extend(
        [
            f'<line x1="210" y1="{legend_y}" x2="260" y2="{legend_y}" stroke="black" stroke-width="2"/><text x="270" y="{legend_y + 4}" font-size="11">Bayes ekor setara</text>',
            f'<line x1="430" y1="{legend_y}" x2="480" y2="{legend_y}" stroke="#333" stroke-width="2" stroke-dasharray="7 4"/><text x="490" y="{legend_y + 4}" font-size="11">Wilson</text>',
            f'<line x1="600" y1="{legend_y}" x2="650" y2="{legend_y}" stroke="#666" stroke-width="2" stroke-dasharray="2 4"/><text x="660" y="{legend_y + 4}" font-size="11">Clopper-Pearson</text>',
            '</g>',
            '</svg>',
        ]
    )
    return svg_bytes(lines)


def build_sensitivity_svg(
    sensitivity: list[dict[str, Any]], influence: list[dict[str, Any]]
) -> bytes:
    prior_records = [row for row in sensitivity if row["sensitivity_type"] == "prior" and row["record_type"] == "cell"]
    denominator_records = [row for row in sensitivity if row["sensitivity_type"] == "denominator"]
    bf_records = [row for row in sensitivity if row["sensitivity_type"] == "bf_prior_scale"]
    loo_records = [row for row in influence if row["metric_type"] == "pooled_posterior_mean"]
    max_prior = max(abs(float(row["delta_posterior_mean"])) for row in prior_records)
    max_denominator = max(abs(float(row["delta_observed_rate"])) for row in denominator_records)
    max_loo = max(abs(float(row["signed_change"])) for row in loo_records)
    desc = (
        f"Tiga panel sensitivitas. Perubahan rataan posterior sel pada prior wajar mencapai {fmt_id(max_prior)}; perubahan proporsi teramati pada penyebut liberal mencapai {fmt_id(max_denominator)} "
        f"dan merepresentasikan estimand populasi percobaan yang berbeda; perubahan rataan posterior gabungan pada penghapusan satu sel (LOO) mencapai {fmt_id(max_loo)}. "
        "Log faktor Bayes B₁₀ ditampilkan pada skalanya sendiri dan tidak dibandingkan secara numerik dengan perubahan peluang."
    )
    width, height = 1050, 520
    panels = [(55, "Prior / log faktor Bayes B₁₀"), (385, "Penyebut liberal"), (715, "Penghapusan satu sel (LOO)")]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="cp02-sens-title cp02-sens-desc">',
        '<title id="cp02-sens-title">Sensitivitas CP02 terhadap prior, penyebut, dan penghapusan satu sel (LOO)</title>',
        f'<desc id="cp02-sens-desc">{xml_escape(desc)}</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<g font-family="Arial, sans-serif" fill="black">',
        '<text x="525" y="28" text-anchor="middle" font-size="18" font-weight="bold">Diagnostik sensitivitas CP02 pada skala yang dipisahkan</text>',
    ]
    for x0, title in panels:
        lines.append(f'<rect x="{x0}" y="65" width="280" height="385" fill="none" stroke="#aaa"/>')
        lines.append(f'<text x="{x0 + 140}" y="88" text-anchor="middle" font-size="13" font-weight="bold">{xml_escape(title)}</text>')
        lines.append(f'<line x1="{x0 + 140}" y1="105" x2="{x0 + 140}" y2="425" stroke="#888" stroke-dasharray="4 4"/>')
    # Panel 1: maximum absolute mean delta by kappa, and BF as labelled text.
    for index, kappa in enumerate(KAPPAS):
        records = [row for row in prior_records if float(row["kappa"]) == kappa]
        value = max(abs(float(row["delta_posterior_mean"])) for row in records)
        y = 125 + index * 52
        length = 110 * (value / max(max_prior, 1e-15))
        lines.append(f'<text x="70" y="{y + 4}" font-size="11">κ={fmt_id(kappa)}</text>')
        lines.append(f'<line x1="195" y1="{y}" x2="{195 + length:.3f}" y2="{y}" stroke="black" stroke-width="4"/>')
        lines.append(f'<circle cx="{195 + length:.3f}" cy="{y}" r="4" fill="white" stroke="black"/>')
    for index, record in enumerate(bf_records):
        lines.append(f'<text x="70" y="{390 + index * 11}" font-size="8">κ={fmt_id(record["kappa"])} log faktor Bayes B₁₀={fmt_id(record["log_bf10"])}</text>')
    # Panel 2: signed observed-rate differences on a centered scale.
    scale_denominator = 115 / max(max_denominator, 1e-15)
    for index, record in enumerate(denominator_records):
        y = 115 + index * 25
        delta = float(record["delta_observed_rate"])
        x = 525 + delta * scale_denominator
        lines.append(f'<line x1="525" y1="{y}" x2="{x:.3f}" y2="{y}" stroke="#333" stroke-width="2"/>')
        lines.append(f'<rect x="{x - 3:.3f}" y="{y - 3}" width="6" height="6" fill="white" stroke="#333"/>')
        lines.append(f'<text x="405" y="{y + 3}" font-size="8">{xml_escape(record["target_label"])}</text>')
    # Panel 3: typed pooled-posterior-mean LOO differences only.
    scale_loo = 115 / max(max_loo, 1e-15)
    for index, record in enumerate(loo_records):
        y = 115 + index * 25
        delta = float(record["signed_change"])
        x = 855 + delta * scale_loo
        lines.append(f'<line x1="855" y1="{y}" x2="{x:.3f}" y2="{y}" stroke="#555" stroke-width="2" stroke-dasharray="3 3"/>')
        lines.append(f'<path d="M {x:.3f} {y - 4} L {x + 4:.3f} {y} L {x:.3f} {y + 4} L {x - 4:.3f} {y} Z" fill="white" stroke="#555"/>')
        lines.append(f'<text x="735" y="{y + 3}" font-size="8">{xml_escape(record["deleted_cell_label"])}</text>')
    lines.extend(
        [
            '<text x="525" y="478" text-anchor="middle" font-size="11">Bentuk dan pola garis membedakan panel tanpa bergantung pada warna; setiap skala khusus panel dan bertipe eksplisit.</text>',
            '<text x="525" y="497" text-anchor="middle" font-size="10">Perbedaan penyebut dapat mengubah estimand; pengaruh penghapusan satu sel (LOO) adalah diagnostik, bukan izin menghapus sel.</text>',
            '</g>',
            '</svg>',
        ]
    )
    return svg_bytes(lines)


def build_text_outputs(
    rows: list[dict[str, Any]],
    posterior: list[dict[str, Any]],
    frequentist: list[dict[str, Any]],
    coverage_summaries: list[dict[str, Any]],
    sensitivity: list[dict[str, Any]],
    influence: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    model: dict[str, Any],
) -> dict[str, bytes]:
    cell_frequentist = [record for record in frequentist if record["record_type"] == "cell"]
    widest = max(cell_frequentist, key=lambda record: record["cp_high_95"] - record["cp_low_95"])
    posterior_means = [record["posterior_mean"] for record in posterior]
    intervals_text = (
        "Interval CP02 — padanan teks yang aksesibel\n"
        f"Dua belas sel agregat pemancar–tahun memakai penyebut Total_method_1 yang konservatif. Rataan posterior di bawah Beta(2,2) berkisar dari {fmt_id(min(posterior_means))} sampai {fmt_id(max(posterior_means))}. "
        f"Interval Clopper–Pearson terlebar terdapat pada {widest['cell_label']}. SVG memakai lingkaran bergaris utuh untuk ringkasan Bayes, persegi bergaris putus-putus untuk Wilson, dan belah ketupat bergaris titik untuk Clopper–Pearson, dengan peluang pada sumbu mendatar. "
        "Semua ringkasan inferensial bersifat ilustratif dan bersyarat karena bukti agregat tidak membuktikan unit Bernoulli yang saling lepas dan independen ataupun satu inisiasi yang memenuhi syarat per betina. Gambar tidak menyatakan efek kausal pemancar atau tahun.\n"
    )
    primary_coverage = [
        record for record in coverage_summaries if record["scenario_id"] == "primary" and record["kappa"] == PRIMARY_KAPPA
    ]
    minima = {
        procedure: min(record["grid_min"] for record in primary_coverage if record["procedure"] == procedure)
        for procedure in ("bayes_equal_tail_primary", "wilson", "clopper_pearson")
    }
    coverage_text = (
        "Cakupan CP02 pada parameter tetap — padanan teks yang aksesibel\n"
        f"Sumbu mendatar adalah p tetap dari 0 sampai 1 dan panel mewakili {len({row['trials_primary'] for row in rows})} penyebut primer yang berbeda. "
        f"Minimum pada kisi yang diperluas ialah Bayes {fmt_id(minima['bayes_equal_tail_primary'])}, Wilson {fmt_id(minima['wilson'])}, dan Clopper–Pearson {fmt_id(minima['clopper_pearson'])}. "
        "Garis utuh, putus-putus, dan titik membedakan prosedur; garis acuan mendatar menandai 0,95. Ekstrem kisi tidak diklaim sebagai ekstrem global kontinu. "
        "Distribusi acuan eksak hanya di bawah model Binomial; penerapan empiris tetap ilustratif sampai tersedia bukti independensi unit.\n"
    )
    prior_rows = [record for record in sensitivity if record["sensitivity_type"] == "prior" and record["record_type"] == "cell"]
    denominator_rows = [record for record in sensitivity if record["sensitivity_type"] == "denominator"]
    loo_rows = [record for record in influence if record["metric_type"] == "pooled_posterior_mean"]
    max_prior = max(prior_rows, key=lambda record: (abs(record["delta_posterior_mean"]), record["target_id"]))
    max_denominator = max(denominator_rows, key=lambda record: (abs(record["delta_observed_rate"]), record["target_id"]))
    max_loo = max(loo_rows, key=lambda record: (abs(record["signed_change"]), record["deleted_cell_id"]))
    sensitivity_text = (
        "Sensitivitas CP02 — padanan teks yang aksesibel\n"
        f"Perubahan rataan posterior terbesar pada prior wajar ialah {fmt_id(abs(max_prior['delta_posterior_mean']))} di {max_prior['target_label']}. "
        f"Perubahan proporsi teramati terbesar pada penyebut liberal ialah {fmt_id(abs(max_denominator['delta_observed_rate']))} di {max_denominator['target_label']}; penyebut ini dapat mendefinisikan estimand populasi percobaan yang berbeda. "
        f"Perubahan rataan posterior gabungan pada penghapusan satu sel (LOO) yang terbesar ialah {fmt_id(abs(max_loo['signed_change']))} setelah {max_loo['deleted_cell_label']} dikeluarkan. "
        f"Log faktor Bayes B₁₀ primer ialah {fmt_id(model['log_bf10'])} (faktor Bayes B₁₀ {fmt_id(model['bf10'])}); log bukti marginal dan perubahan pada skala peluang tidak pernah diperingkat bersama. Tidak ada panel yang mengidentifikasi sebab biologis.\n"
    )
    ppc = [record for record in diagnostics if record["record_type"] == "posterior_predictive"]
    tails = [record["tail_area"] for record in ppc]
    dispersion = [record for record in diagnostics if record["record_type"] == "dispersion_identifiability"]
    diagnostics_text = (
        "Diagnostik CP02 — padanan teks yang aksesibel\n"
        f"PCG64 dengan benih acak {SEED} dan {PPC_REPLICATIONS} replikasi prediktif-posterior berpasangan per model/penyebut menghasilkan luas ekor diagnostik dari {fmt_id(min(tails))} sampai {fmt_id(max(tails))}; nilai ini bukan nilai-p klasik. "
        f"Profil dispersi berlebih tetap memakai intersep saja, q=1, log κ [{fmt_id(PROFILE_LOG_KAPPA_MIN)},{fmt_id(PROFILE_LOG_KAPPA_MAX)}] dengan langkah {fmt_id(PROFILE_LOG_KAPPA_STEP)} dan toleransi {fmt_id(IDENTIFIABILITY_TOLERANCE)}. "
        "Keempat baris gerbang dispersi menahan taksiran teridentifikasi karena gerbang beku lengkap tidak lolos. Klaim sekuensial: tidak. Bukti agregat tidak membuktikan unit Bernoulli yang saling lepas dan independen ataupun satu inisiasi yang memenuhi syarat per betina.\n"
    )
    return {
        "CP02_intervals.txt": intervals_text.encode("utf-8"),
        "CP02_coverage.txt": coverage_text.encode("utf-8"),
        "CP02_sensitivity.txt": sensitivity_text.encode("utf-8"),
        "CP02_diagnostics.txt": diagnostics_text.encode("utf-8"),
    }


MANIFEST_HEADER = ["path", "role", "bytes", "sha256"]


def manifest_bytes(payloads: dict[str, bytes], roles: dict[str, str]) -> bytes:
    """Return the closed substantive-output manifest (excluding itself)."""
    if set(payloads) != set(roles):
        fail(
            "manifest_role_closure",
            "generated/capstones/CP02/MANIFEST.csv",
            f"payload/role inventories differ: {sorted(set(payloads) ^ set(roles))!r}",
        )
    rows = [
        {
            "path": name,
            "role": roles[name],
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }
        for name, payload in sorted(payloads.items())
    ]
    return csv_bytes(MANIFEST_HEADER, rows)


def assert_finite_csv_payload(name: str, payload: bytes) -> None:
    """Reject accidental NaN/Infinity tokens without forbidding prose statuses."""
    text = payload.decode("utf-8")
    lowered = text.lower()
    forbidden = (",nan,", ",inf,", ",-inf,", ",infinity,", ",-infinity,")
    padded = "," + lowered.replace("\n", ",") + ","
    if any(token in padded for token in forbidden):
        fail("finite_numeric_serialization", name, "non-finite numeric token found")


def validate_scientific_contract(
    rows: list[dict[str, Any]],
    posterior_rows: list[dict[str, Any]],
    model_rows: list[dict[str, Any]],
    coverage_summaries: list[dict[str, Any]],
    frequentist_rows: list[dict[str, Any]],
    predictive_rows: list[dict[str, Any]],
    diagnostic_rows: list[dict[str, Any]],
    dispersion_rows: list[dict[str, Any]],
    sensitivity_rows: list[dict[str, Any]],
    influence_rows: list[dict[str, Any]],
    contrast_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Hard-fail the scientific invariants relied on by the CP02 reader."""
    if len(rows) != 12 or len({row["cell_id"] for row in rows}) != 12:
        fail("cell_inventory", "CP02_cells_clean.csv", "expected 12 unique cells")

    if len(posterior_rows) != 12 or any(row["scenario_id"] != "primary" for row in posterior_rows):
        fail("primary_posterior_inventory", "CP02_posterior_summary.csv", "expected 12 primary rows")
    for row in posterior_rows:
        if row["prior_id"] != "beta_2_2" or float(row["kappa"]) != PRIMARY_KAPPA:
            fail("primary_prior_lock", "CP02_posterior_summary.csv", row["cell_id"])
        if abs(float(row["credible_mass"]) - (1.0 - ALPHA)) > 5e-10:
            fail("credible_mass", "CP02_posterior_summary.csv", row["cell_id"])
        if abs(float(row["beta_binomial_mass_sum"]) - 1.0) > 5e-12:
            fail("predictive_mass", "CP02_posterior_summary.csv", row["cell_id"])

    comparisons = [row for row in model_rows if row["record_type"] == "comparison"]
    if len(comparisons) != 1:
        fail("model_comparison_inventory", "CP02_model_comparison.csv", "expected one M1/M0 comparison")
    comparison = comparisons[0]
    if comparison["prior_id"] != "beta_2_2" or float(comparison["kappa"]) != PRIMARY_KAPPA:
        fail("model_prior_symmetry", "CP02_model_comparison.csv", "common Beta(2,2) prior is not locked")
    log_bf10 = float(comparison["log_bf10"])
    bf10 = float(comparison["bf10"])
    if not (math.isfinite(log_bf10) and bf10 > 0.0 and math.isfinite(bf10)):
        fail("bayes_factor_finite", "CP02_model_comparison.csv", "log BF/BF must be finite and positive")
    if abs(math.log(bf10) - log_bf10) > 5e-12:
        fail("bayes_factor_log_identity", "CP02_model_comparison.csv", "log(BF10) differs from log_bf10")
    if abs(float(comparison["posterior_odds_10"]) - PRIOR_ODDS_10 * bf10) > 5e-18:
        fail("posterior_odds_identity", "CP02_model_comparison.csv", "posterior odds differ from prior odds times BF")

    primary_coverage = [
        row
        for row in coverage_summaries
        if row["scenario_id"] == "primary" and float(row["kappa"]) == PRIMARY_KAPPA
    ]
    if not primary_coverage:
        fail("coverage_inventory", "CP02_coverage.csv", "primary kappa=4 summaries are absent")
    cp_minima = [row["grid_min"] for row in primary_coverage if row["procedure"] == "clopper_pearson"]
    if not cp_minima or min(cp_minima) < 1.0 - ALPHA - 5e-12:
        fail("clopper_pearson_coverage", "CP02_coverage.csv", f"minimum={min(cp_minima) if cp_minima else 'missing'}")
    cell_tests = [row for row in frequentist_rows if row["record_type"] == "cell"]
    if len(cell_tests) != 12 or max(float(row["actual_size"]) for row in cell_tests) > ALPHA + 1e-15:
        fail("exact_binomial_size", "CP02_frequentist_comparison.csv", "cell inventory or size bound failed")
    homogeneity = [row for row in frequentist_rows if row["record_type"] == "homogeneity"]
    if {row["scenario_id"] for row in homogeneity} != {"primary", "secondary_liberal"}:
        fail("homogeneity_inventory", "CP02_frequentist_comparison.csv", "two denominator scenarios required")

    predictive_summaries = [row for row in predictive_rows if row["record_type"] == "summary"]
    if len(predictive_summaries) != 48:
        fail("posterior_predictive_inventory", "CP02_posterior_predictive.csv", f"expected 48 summaries, got {len(predictive_summaries)}")
    if any(abs(float(row["mass_sum"]) - 1.0) > 5e-12 for row in predictive_summaries):
        fail("posterior_predictive_mass", "CP02_posterior_predictive.csv", "a Beta-Binomial marginal does not sum to one")
    if not all("cross-cell dependent" in row["reason"] for row in predictive_summaries if row["model_id"] == "M0"):
        fail("model_conditional_dependence_note", "CP02_posterior_predictive.csv", "M0 dependence note is absent")

    ppc = [row for row in diagnostic_rows if row["record_type"] == "posterior_predictive"]
    dispersion_gate = [row for row in diagnostic_rows if row["record_type"] == "dispersion_identifiability"]
    if len(ppc) != 16 or any(int(row["replications"]) != PPC_REPLICATIONS for row in ppc):
        fail("ppc_inventory", "CP02_diagnostics.csv", f"expected 16 x {PPC_REPLICATIONS} diagnostic summaries")
    if len(dispersion_gate) != 4 or any(bool(row["dispersion_identified"]) for row in dispersion_gate):
        fail("dispersion_gate", "CP02_diagnostics.csv", "all four frozen gates must withhold identification")
    if not dispersion_rows or any(bool(row["dispersion_identified"]) for row in dispersion_rows):
        fail("dispersion_profile_gate", "CP02_dispersion_profile.csv", "profile rows must preserve non-identification")

    prior_sensitivity = [row for row in sensitivity_rows if row["sensitivity_type"] == "prior" and row["record_type"] == "cell"]
    if len(prior_sensitivity) != 12 * len(KAPPAS):
        fail("prior_sensitivity_inventory", "CP02_sensitivity.csv", "expected five proper-prior scenarios per cell")
    denominator_sensitivity = [row for row in sensitivity_rows if row["sensitivity_type"] == "denominator"]
    if len(denominator_sensitivity) != 12 or any(row["defined_status"] != "defined_distinct_estimand" for row in denominator_sensitivity):
        fail("denominator_sensitivity_estimand", "CP02_sensitivity.csv", "secondary denominator must be typed as a distinct estimand")
    metric_types = {
        "log_bf10": "log_evidence",
        "pooled_posterior_mean": "probability",
        "pooled_prob_gt_threshold": "probability",
        "pooled_credible_low_95": "probability_endpoint",
        "pooled_credible_high_95": "probability_endpoint",
    }
    if len(influence_rows) != 12 * len(metric_types):
        fail("loo_inventory", "CP02_influence.csv", f"expected {12 * len(metric_types)} typed rows")
    for row in influence_rows:
        if metric_types.get(row["metric_type"]) != row["metric_scale"]:
            fail("loo_metric_type", "CP02_influence.csv", f"{row['metric_type']}/{row['metric_scale']}")

    expected_contrast_rows = len(contrast_pairs(rows)) * 2 * (len(KAPPAS) + 1)
    if len(contrast_rows) != expected_contrast_rows:
        fail("contrast_inventory", "CP02_contrasts.csv", f"expected {expected_contrast_rows}, got {len(contrast_rows)}")
    odds_rows = [row for row in contrast_rows if row["estimand"] == "odds_ratio"]
    if any(row["posterior_mean"] != "" for row in odds_rows):
        fail("odds_mean_omitted", "CP02_contrasts.csv", "odds-ratio mean must never be serialized")
    infinite_rows = [row for row in odds_rows if row["moment_status"] == "infinite_moment"]
    for row in odds_rows:
        left = next(item for item in rows if item["cell_id"] == row["left_cell_id"])
        right = next(item for item in rows if item["cell_id"] == row["right_cell_id"])
        trial_field = "trials_secondary" if row["scenario_id"] == "secondary_liberal" else "trials_primary"
        kappa = float(row["kappa"])
        left_beta = kappa / 2.0 + left[trial_field] - left["successes"]
        right_alpha = kappa / 2.0 + right["successes"]
        expected_status = "finite_but_mean_not_reported_by_contract" if left_beta > 1.0 and right_alpha > 1.0 else "infinite_moment"
        if row["moment_status"] != expected_status:
            fail("odds_moment_status", "CP02_contrasts.csv", row["contrast_id"])

    return {
        "cell_count": len(rows),
        "primary_kappa": PRIMARY_KAPPA,
        "primary_prior": "Beta(2,2)",
        "log_bf10": log_bf10,
        "bf10": bf10,
        "posterior_odds_10": float(comparison["posterior_odds_10"]),
        "coverage_primary_summary_rows": len(primary_coverage),
        "clopper_pearson_grid_minimum": min(cp_minima),
        "ppc_rows": len(ppc),
        "dispersion_gate_rows": len(dispersion_gate),
        "dispersion_identified_rows": 0,
        "loo_metric_rows": len(influence_rows),
        "contrast_rows": len(contrast_rows),
        "odds_ratio_rows": len(odds_rows),
        "odds_ratio_infinite_mean_rows": len(infinite_rows),
    }


def build_expected_payload() -> tuple[dict[str, bytes], bytes, dict[str, Any]]:
    rows, clean_manifest_rows = load_clean_cells()
    cells_header, cell_rows = build_cells_output(rows)
    posterior_rows, _ = build_primary_posterior(rows)
    model_rows, primary_model = build_model_rows(rows)
    coverage_payload, coverage_summaries, plot_curves = generate_coverage(rows)
    frequentist_rows, primary_homogeneity, secondary_homogeneity = build_frequentist_rows(
        rows, coverage_summaries
    )
    predictive_rows = build_posterior_predictive(rows)
    diagnostic_rows = ppc_rows(rows)
    dispersion_rows = build_dispersion_profile(rows, diagnostic_rows)
    sensitivity_rows, influence_rows = build_sensitivity_and_influence(
        rows, primary_homogeneity, secondary_homogeneity, primary_model
    )
    contrast_rows = build_contrasts(rows)

    spot_checks = validate_scientific_contract(
        rows,
        posterior_rows,
        model_rows,
        coverage_summaries,
        frequentist_rows,
        predictive_rows,
        diagnostic_rows,
        dispersion_rows,
        sensitivity_rows,
        influence_rows,
        contrast_rows,
    )

    substantive: dict[str, bytes] = {
        "CP02_cells_clean.csv": csv_bytes(cells_header, cell_rows),
        "CP02_posterior_summary.csv": csv_bytes(POSTERIOR_HEADER, posterior_rows),
        "CP02_model_comparison.csv": csv_bytes(MODEL_HEADER, model_rows),
        "CP02_frequentist_comparison.csv": csv_bytes(FREQUENTIST_HEADER, frequentist_rows),
        "CP02_coverage.csv": coverage_payload,
        "CP02_posterior_predictive.csv": csv_bytes(PREDICTIVE_HEADER, predictive_rows),
        "CP02_diagnostics.csv": csv_bytes(DIAGNOSTICS_HEADER, diagnostic_rows),
        "CP02_dispersion_profile.csv": csv_bytes(DISPERSION_HEADER, dispersion_rows),
        "CP02_sensitivity.csv": csv_bytes(SENSITIVITY_HEADER, sensitivity_rows),
        "CP02_influence.csv": csv_bytes(INFLUENCE_HEADER, influence_rows),
        "CP02_contrasts.csv": csv_bytes(CONTRAST_HEADER, contrast_rows),
        "CP02_intervals.svg": build_intervals_svg(rows, posterior_rows, frequentist_rows),
        "CP02_coverage.svg": build_coverage_svg(plot_curves),
        "CP02_sensitivity.svg": build_sensitivity_svg(sensitivity_rows, influence_rows),
    }
    substantive.update(
        build_text_outputs(
            rows,
            posterior_rows,
            frequentist_rows,
            coverage_summaries,
            sensitivity_rows,
            influence_rows,
            diagnostic_rows,
            primary_model,
        )
    )
    roles = {
        "CP02_cells_clean.csv": "analysis_ready_cell_table",
        "CP02_posterior_summary.csv": "primary_cell_posterior_and_loss_summary",
        "CP02_model_comparison.csv": "model_evidence_odds_and_loss",
        "CP02_frequentist_comparison.csv": "interval_test_power_coverage_and_homogeneity_summary",
        "CP02_coverage.csv": "full_fixed_parameter_coverage_ledger",
        "CP02_posterior_predictive.csv": "exact_beta_binomial_predictive_marginals",
        "CP02_diagnostics.csv": "posterior_predictive_and_identifiability_diagnostics",
        "CP02_dispersion_profile.csv": "deterministic_overdispersion_identifiability_profile",
        "CP02_sensitivity.csv": "prior_denominator_and_loo_sensitivity",
        "CP02_influence.csv": "typed_leave_one_cell_out_metrics",
        "CP02_contrasts.csv": "prespecified_probability_and_odds_contrasts",
        "CP02_intervals.svg": "accessible_static_interval_figure",
        "CP02_coverage.svg": "accessible_static_coverage_figure",
        "CP02_sensitivity.svg": "accessible_static_sensitivity_figure",
        "CP02_intervals.txt": "interval_figure_text_equivalent",
        "CP02_coverage.txt": "coverage_figure_text_equivalent",
        "CP02_sensitivity.txt": "sensitivity_figure_text_equivalent",
        "CP02_diagnostics.txt": "diagnostic_text_equivalent",
    }
    if set(substantive) != set(roles):
        fail("substantive_inventory", "generated/capstones/CP02", str(sorted(set(substantive) ^ set(roles))))
    for name, payload in substantive.items():
        if name.endswith(".csv"):
            assert_finite_csv_payload(name, payload)
        if name.endswith(".svg"):
            text = payload.decode("utf-8")
            if not all(marker in text for marker in ("role=\"img\"", "<title ", "<desc ", "<text ")):
                fail("svg_accessibility", name, "role/title/desc/text contract failed")

    manifest = manifest_bytes(substantive, roles)
    payloads = dict(substantive)
    payloads["MANIFEST.csv"] = manifest
    analysis_code = SCRIPT_PATH.read_bytes()
    transform_path = DATA_ROOT / "transform_cp02.py"
    transform_code = transform_path.read_bytes()
    clean_manifest_path = CLEAN_ROOT / "MANIFEST.csv"
    transform_receipt_payload = TRANSFORM_RECEIPT_PATH.read_bytes()
    transform_receipt = json.loads(transform_receipt_payload.decode("utf-8"))
    expected_rights_provenance_paths = {
        "data/capstones/CP02/DATASET_PROVENANCE.json",
        "data/capstones/CP02/INPUT_MANIFEST.csv",
        "data/capstones/CP02/RIGHTS_EVIDENCE.md",
        "data/capstones/CP02/SCHEMA.json",
        "data/capstones/CP02/raw/README.md",
        "data/capstones/CP02/raw/nest_propensity.csv",
    }
    rights_provenance_inputs: list[dict[str, Any]] = []
    for item in sorted(transform_receipt.get("inputs", []), key=lambda entry: entry.get("path", "")):
        relative = str(item.get("path", ""))
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or relative.replace("\\", "/") != relative:
            fail("rights_provenance_safe_path", "build/CP02_ANALYSIS_RECEIPT.json", relative)
        local_path = COMPONENT_ROOT / relative_path
        if not local_path.is_file():
            fail("rights_provenance_present", relative, "file is missing")
        local_payload = local_path.read_bytes()
        if len(local_payload) != int(item.get("bytes", -1)) or sha256_bytes(local_payload) != item.get("sha256"):
            fail("rights_provenance_identity", relative, "transform-receipt identity differs from live bytes")
        rights_provenance_inputs.append(
            {
                "path": relative,
                "role": item.get("role", ""),
                "bytes": len(local_payload),
                "sha256": sha256_bytes(local_payload),
            }
        )
    if {item["path"] for item in rights_provenance_inputs} != expected_rights_provenance_paths:
        fail(
            "rights_provenance_closure",
            "build/CP02_ANALYSIS_RECEIPT.json",
            f"expected {sorted(expected_rights_provenance_paths)!r}",
        )
    receipt = {
        "schema": SCHEMA_ID,
        "status": "pass",
        "network_access": False,
        "browser_processes_used": False,
        "canonical_input": {
            "path": "data/capstones/CP02/raw/nest_propensity.csv",
            "bytes": 285,
            "sha256": "8790b4dfa29a5b39228e758e40e02cbb48612c38b8440020aa108c85ca0673c4",
        },
        "denominator_policy": {
            "primary": PRIMARY_DENOMINATOR_ID,
            "secondary_sensitivity": SECONDARY_DENOMINATOR_ID,
            "secondary_changes_estimand": True,
        },
        "working_probability_law": {
            "sampling": "conditionally_independent_Binomial_cells_given_parameters",
            "M0_note": "posterior-predictive cell marginals share one p and are cross-cell dependent after integration",
            "M1_note": "cell-specific probabilities are independent under the stated proper product prior",
            "applicability": MODEL_ASSUMPTION_STATUS,
        },
        "prior": {
            "family": "Beta(kappa/2,kappa/2)",
            "primary_kappa": PRIMARY_KAPPA,
            "primary_shape": [2.0, 2.0],
            "sensitivity_kappas": list(KAPPAS),
            "proper_under_M0_and_every_M1_cell": True,
        },
        "rng": {
            "generator": "NumPy PCG64 with jumped, non-overlapping deterministic streams",
            "seed": SEED,
            "posterior_predictive_replications": PPC_REPLICATIONS,
            "contrast_draws": CONTRAST_DRAWS,
        },
        "methods": {
            "bayesian": "exact_Beta_Binomial_conjugacy_log_evidence_BF_odds_and_loss",
            "frequentist": "Wilson_Clopper_Pearson_exact_Binomial_Holm_power_and_exact_conditional_homogeneity",
            "coverage": "exact_finite_Binomial_sums_on_augmented_endpoint_grid",
            "dispersion": "fixed_intercept_only_profile_with_all_gates_identifiability_rule",
            "influence": "typed_leave_one_cell_out_refits_without_cross_scale_ranking",
            "serialization": "UTF-8_without_BOM_LF_canonical_order_dot_decimal",
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "numeric_float": "IEEE-754_binary64",
        },
        "code": [
            {
                "path": "data/capstones/CP02/transform_cp02.py",
                "bytes": len(transform_code),
                "sha256": sha256_bytes(transform_code),
            },
            {
                "path": "capstones/run_cp02_analysis.py",
                "bytes": len(analysis_code),
                "sha256": sha256_bytes(analysis_code),
            },
        ],
        "clean_inputs": {
            "manifest": {
                "path": "data/capstones/CP02/clean/MANIFEST.csv",
                "bytes": clean_manifest_path.stat().st_size,
                "sha256": sha256_bytes(clean_manifest_path.read_bytes()),
                "entries": len(clean_manifest_rows),
            },
            "transform_receipt": {
                "path": "build/CP02_TRANSFORM_RECEIPT.json",
                "bytes": len(transform_receipt_payload),
                "sha256": sha256_bytes(transform_receipt_payload),
                "schema": transform_receipt.get("schema"),
            },
        },
        "rights_provenance_inputs": rights_provenance_inputs,
        "spot_checks": spot_checks,
        "assertions": {
            "input_and_clean_manifest_identity": True,
            "primary_Beta_2_2_prior_and_kappa_4": True,
            "log_BF_BF_and_odds_identity": True,
            "posterior_and_predictive_mass": True,
            "fixed_parameter_coverage_and_exact_size": True,
            "wilson_closed_endpoint_coverage": True,
            "model_conditional_dependence_label": True,
            "posterior_predictive_seeded_replay": True,
            "overdispersion_identification_withheld": True,
            "typed_LOO_complete": True,
            "odds_ratio_infinite_moments_typed": True,
            "SVG_title_desc_text_and_text_equivalents": True,
            "manifest_closed": True,
            "rights_provenance_inputs_closed_and_verified": True,
        },
        "manifest_closure": {
            "manifest_path": "generated/capstones/CP02/MANIFEST.csv",
            "manifest_lists": "all 18 substantive files and excludes only itself",
            "manifest_bytes": len(manifest),
            "manifest_sha256": sha256_bytes(manifest),
            "receipt_path": "build/CP02_ANALYSIS_RECEIPT.json",
            "receipt_lists": "all substantive files plus MANIFEST.csv and excludes itself",
        },
        "outputs": [
            {
                "path": f"generated/capstones/CP02/{name}",
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    if not all(receipt["assertions"].values()):
        fail("analysis_assertions", "build/CP02_ANALYSIS_RECEIPT.json", "one or more assertions failed")
    return payloads, canonical_json_bytes(receipt), spot_checks


def verify_exact_directory(root: Path, expected: dict[str, bytes]) -> None:
    if not root.is_dir():
        fail("generated_directory_present", "generated/capstones/CP02", "directory is missing")
    entries = list(root.iterdir())
    non_files = sorted(path.name for path in entries if not path.is_file())
    if non_files:
        fail("generated_directory_files_only", "generated/capstones/CP02", repr(non_files))
    actual_names = sorted(path.name for path in entries)
    expected_names = sorted(expected)
    if actual_names != expected_names:
        fail("generated_inventory", "generated/capstones/CP02", f"expected {expected_names!r}, got {actual_names!r}")
    for name in expected_names:
        actual = (root / name).read_bytes()
        if actual != expected[name]:
            fail(
                "generated_byte_identity",
                f"generated/capstones/CP02/{name}",
                f"expected {sha256_bytes(expected[name])}, got {sha256_bytes(actual)}",
            )


def preflight_output_directory(expected_names: set[str]) -> None:
    if not GENERATED_ROOT.exists():
        return
    if not GENERATED_ROOT.is_dir():
        fail("generated_directory_type", "generated/capstones/CP02", "path is not a directory")
    unexpected = sorted(path.name for path in GENERATED_ROOT.iterdir() if path.name not in expected_names)
    if unexpected:
        fail("generated_preflight_inventory", "generated/capstones/CP02", repr(unexpected))


def atomic_write_many(payloads: dict[str, bytes], receipt_payload: bytes) -> None:
    preflight_output_directory(set(payloads))
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    targets = [(GENERATED_ROOT / name, payload) for name, payload in sorted(payloads.items())]
    targets.append((RECEIPT_PATH, receipt_payload))
    temporary: list[tuple[Path, Path]] = []
    try:
        for target, payload in targets:
            temp = target.with_name(f".{target.name}.cp02-analysis.tmp")
            if temp.exists():
                fail("temporary_absent", target.name, f"stale temporary {temp.name!r}")
            temp.write_bytes(payload)
            if temp.read_bytes() != payload:
                fail("temporary_readback", target.name, "temporary bytes differ")
            temporary.append((temp, target))
        for temp, target in temporary:
            os.replace(temp, target)
    except Exception:
        for temp, _ in temporary:
            if temp.exists():
                temp.unlink()
        raise


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write the canonical CP02 generated artifacts and receipt")
    mode.add_argument("--check-only", action="store_true", help="recompute and compare exact bytes without writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    tracked_paths = [RECEIPT_PATH]
    if GENERATED_ROOT.is_dir():
        tracked_paths.extend(path for path in GENERATED_ROOT.iterdir() if path.is_file())
    before_mtime = {str(path): path.stat().st_mtime_ns for path in tracked_paths if path.is_file()}
    try:
        payloads, receipt_payload, spot_checks = build_expected_payload()
        if args.write:
            atomic_write_many(payloads, receipt_payload)
            verify_exact_directory(GENERATED_ROOT, payloads)
            if RECEIPT_PATH.read_bytes() != receipt_payload:
                fail("analysis_receipt_readback", "build/CP02_ANALYSIS_RECEIPT.json", "bytes differ")
            mode = "write"
        else:
            verify_exact_directory(GENERATED_ROOT, payloads)
            if not RECEIPT_PATH.is_file():
                fail("analysis_receipt_present", "build/CP02_ANALYSIS_RECEIPT.json", "file is missing")
            if RECEIPT_PATH.read_bytes() != receipt_payload:
                fail(
                    "analysis_receipt_identity",
                    "build/CP02_ANALYSIS_RECEIPT.json",
                    f"expected {sha256_bytes(receipt_payload)}, got {sha256_bytes(RECEIPT_PATH.read_bytes())}",
                )
            after_mtime = {
                str(path): path.stat().st_mtime_ns
                for path in [RECEIPT_PATH, *sorted(GENERATED_ROOT.iterdir())]
                if path.is_file()
            }
            if after_mtime != before_mtime:
                fail("check_only_no_write", "generated/capstones/CP02", "file mtimes changed")
            mode = "check-only"
        print(
            json.dumps(
                {
                    "status": "ok",
                    "mode": mode,
                    "schema": SCHEMA_ID,
                    "generated_files": len(payloads),
                    "generated_bytes": sum(len(payload) for payload in payloads.values()),
                    "manifest_sha256": sha256_bytes(payloads["MANIFEST.csv"]),
                    "receipt_sha256": sha256_bytes(receipt_payload),
                    "log_bf10": spot_checks["log_bf10"],
                    "bf10": spot_checks["bf10"],
                    "odds_ratio_infinite_mean_rows": spot_checks["odds_ratio_infinite_mean_rows"],
                    "dispersion_identified_rows": spot_checks["dispersion_identified_rows"],
                    "writes_performed": bool(args.write),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except ContractError as exc:
        print(f"CP02 analysis contract failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
