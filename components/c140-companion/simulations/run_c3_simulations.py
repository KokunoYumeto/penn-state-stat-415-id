#!/usr/bin/env python3
"""Generate deterministic Bayesian-calibration evidence for C3 without SciPy."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "generated" / "simulations" / "c3"
RECEIPT = ROOT / "build" / "C3_SIMULATION_RECEIPT.json"
PYTHON_VERSION = "3.13.9"
NUMPY_VERSION = "2.4.4"
SEED = 2026082906
BIT_GENERATOR = "numpy.random.Generator(PCG64)"
N = 20
PRIOR_A = 2
PRIOR_B = 2
ALPHA = 0.05
GRID_REPLICATIONS = 80_000
PRIOR_REPLICATIONS = 500_000
GRID = tuple(index / 100.0 for index in range(1, 100))
BISECTION_STEPS = 80


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def quantized(value: float, digits: int = 10) -> str:
    """Serialize a summary float as a fixed-width, cross-platform decimal string."""

    rounded = round(float(value), digits)
    if abs(rounded) < 0.5 * 10.0 ** (-digits):
        rounded = 0.0
    return f"{rounded:.{digits}f}"


def csv_bytes(fields: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def beta_cdf_integer(value: float, a: int, b: int) -> float:
    """Evaluate I_value(a,b) by its exact finite-binomial-sum identity.

    This implementation is deliberately bounded to positive integer shapes.
    For m=a+b-1, I_z(a,b)=P{Binomial(m,z)>=a}.  C3 uses shapes at most 23,
    so direct summation is stable and avoids a SciPy/runtime dependency.
    """

    if a <= 0 or b <= 0:
        raise ValueError("beta shapes must be positive integers")
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    m = a + b - 1
    complement = 1.0 - value
    return math.fsum(
        math.comb(m, index) * value**index * complement ** (m - index)
        for index in range(a, m + 1)
    )


def beta_quantile_integer(probability: float, a: int, b: int) -> float:
    """Invert the integer-shape beta CDF with a fixed 80-step bisection."""

    if probability <= 0.0:
        return 0.0
    if probability >= 1.0:
        return 1.0
    lower, upper = 0.0, 1.0
    for _ in range(BISECTION_STEPS):
        midpoint = (lower + upper) / 2.0
        if beta_cdf_integer(midpoint, a, b) < probability:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def binomial_pmf(n: int, x: int, p: float) -> float:
    return math.comb(n, x) * p**x * (1.0 - p) ** (n - x)


def beta_binomial_pmf(n: int, x: int, a: int, b: int) -> float:
    log_value = (
        math.log(math.comb(n, x))
        + math.lgamma(a + x)
        + math.lgamma(b + n - x)
        - math.lgamma(a + b + n)
        - math.lgamma(a)
        - math.lgamma(b)
        + math.lgamma(a + b)
    )
    return math.exp(log_value)


def construct_intervals() -> list[dict[str, float | int]]:
    intervals: list[dict[str, float | int]] = []
    lower_probability = ALPHA / 2.0
    upper_probability = 1.0 - lower_probability
    for x in range(N + 1):
        posterior_a = PRIOR_A + x
        posterior_b = PRIOR_B + N - x
        bayes_lower = beta_quantile_integer(lower_probability, posterior_a, posterior_b)
        bayes_upper = beta_quantile_integer(upper_probability, posterior_a, posterior_b)
        posterior_mass = beta_cdf_integer(
            bayes_upper, posterior_a, posterior_b
        ) - beta_cdf_integer(bayes_lower, posterior_a, posterior_b)
        cp_lower = (
            0.0
            if x == 0
            else beta_quantile_integer(lower_probability, x, N - x + 1)
        )
        cp_upper = (
            1.0
            if x == N
            else beta_quantile_integer(upper_probability, x + 1, N - x)
        )
        intervals.append(
            {
                "x": x,
                "posterior_a": posterior_a,
                "posterior_b": posterior_b,
                "bayes_lower": bayes_lower,
                "bayes_upper": bayes_upper,
                "bayes_posterior_mass": posterior_mass,
                "cp_lower": cp_lower,
                "cp_upper": cp_upper,
            }
        )
    return intervals


def exact_conditional(
    p: float, intervals: list[dict[str, float | int]], key_lower: str, key_upper: str
) -> tuple[float, float]:
    probabilities = [binomial_pmf(N, x, p) for x in range(N + 1)]
    coverage = math.fsum(
        probabilities[x]
        for x, interval in enumerate(intervals)
        if float(interval[key_lower]) <= p <= float(interval[key_upper])
    )
    expected_width = math.fsum(
        probabilities[x]
        * (float(interval[key_upper]) - float(interval[key_lower]))
        for x, interval in enumerate(intervals)
    )
    return coverage, expected_width


def conditional_coverage_svg(rows: list[dict[str, Any]]) -> bytes:
    width, height = 960, 560
    left, right, top, bottom = 92, 34, 58, 86
    plot_width = width - left - right
    plot_height = height - top - bottom

    def sx(value: float) -> float:
        return left + (value - 0.01) / 0.98 * plot_width

    def sy(value: float) -> float:
        return top + (1.0 - value) * plot_height

    bayes_points = " ".join(
        f"{sx(float(row['p'])):.2f},{sy(float(row['bayes_exact'])):.2f}" for row in rows
    )
    cp_points = " ".join(
        f"{sx(float(row['p'])):.2f},{sy(float(row['cp_exact'])):.2f}" for row in rows
    )
    title = "SIM006: cakupan bersyarat selang binomial pada grid parameter"
    description = (
        "Garis biru penuh menunjukkan cakupan bersyarat selang kredibel berekor sama "
        "Beta(2,2), yang berubah menurut p dan jatuh ke nol pada p 0,01 serta 0,99. "
        "Garis hijau putus-putus menunjukkan selang kepercayaan Clopper-Pearson, yang "
        "berada pada atau di atas garis target merah bertitik 0,95 di seluruh grid "
        "p 0,01 sampai 0,99."
    )
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(title)}</title>',
        f'<desc id="desc">{html.escape(description)}</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17202a}.axis{stroke:#273746;stroke-width:1.5}.grid{stroke:#d5d8dc;stroke-width:1}.label{font-size:14px}.heading{font-size:20px;font-weight:700}.legend{font-size:13px}</style>',
        f'<text class="heading" x="{left}" y="31">{html.escape(title)}</text>',
    ]
    for index in range(6):
        y_value = index / 5.0
        y_pixel = sy(y_value)
        parts.append(
            f'<line class="grid" x1="{left}" y1="{y_pixel:.2f}" x2="{left + plot_width}" y2="{y_pixel:.2f}"/>'
        )
        parts.append(
            f'<text class="label" text-anchor="end" x="{left - 10}" y="{y_pixel + 5:.2f}">{y_value:.1f}</text>'
        )
    for x_value in (0.01, 0.25, 0.50, 0.75, 0.99):
        x_pixel = sx(x_value)
        parts.append(
            f'<line class="grid" x1="{x_pixel:.2f}" y1="{top}" x2="{x_pixel:.2f}" y2="{top + plot_height}"/>'
        )
        parts.append(
            f'<text class="label" text-anchor="middle" x="{x_pixel:.2f}" y="{top + plot_height + 24}">{x_value:.2f}</text>'
        )
    target_y = sy(1.0 - ALPHA)
    parts.extend(
        [
            f'<line class="axis" x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
            f'<line x1="{left}" y1="{target_y:.2f}" x2="{left + plot_width}" y2="{target_y:.2f}" stroke="#922b21" stroke-width="2" stroke-dasharray="2 4"/>',
            f'<polyline fill="none" stroke="#1f618d" stroke-width="3" points="{bayes_points}"/>',
            f'<polyline fill="none" stroke="#148f77" stroke-width="3" stroke-dasharray="9 5" points="{cp_points}"/>',
            f'<text class="label" text-anchor="middle" x="{left + plot_width / 2:.2f}" y="{height - 24}">parameter pembangkit tetap p</text>',
            f'<text class="label" text-anchor="middle" transform="translate(24 {top + plot_height / 2:.2f}) rotate(-90)">cakupan bersyarat</text>',
            f'<line x1="{left + 18}" y1="{top + 20}" x2="{left + 52}" y2="{top + 20}" stroke="#1f618d" stroke-width="3"/>',
            f'<text class="legend" x="{left + 60}" y="{top + 25}">kredibel Beta(2,2), garis penuh</text>',
            f'<line x1="{left + 18}" y1="{top + 42}" x2="{left + 52}" y2="{top + 42}" stroke="#148f77" stroke-width="3" stroke-dasharray="9 5"/>',
            f'<text class="legend" x="{left + 60}" y="{top + 47}">kepercayaan Clopper–Pearson, putus-putus</text>',
            f'<line x1="{left + 18}" y1="{top + 64}" x2="{left + 52}" y2="{top + 64}" stroke="#922b21" stroke-width="2" stroke-dasharray="2 4"/>',
            f'<text class="legend" x="{left + 60}" y="{top + 69}">target 0,95</text>',
            "</svg>",
        ]
    )
    return ("\n".join(parts) + "\n").encode("utf-8")


def experiment() -> tuple[dict[str, bytes], dict[str, Any]]:
    intervals = construct_intervals()
    rng = np.random.Generator(np.random.PCG64(SEED))
    internal_rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, object]] = []

    for p in GRID:
        bayes_exact, bayes_width = exact_conditional(
            p, intervals, "bayes_lower", "bayes_upper"
        )
        cp_exact, cp_width = exact_conditional(p, intervals, "cp_lower", "cp_upper")
        samples = rng.binomial(N, p, size=GRID_REPLICATIONS)
        bayes_lower = np.asarray(
            [float(interval["bayes_lower"]) for interval in intervals], dtype=np.float64
        )
        bayes_upper = np.asarray(
            [float(interval["bayes_upper"]) for interval in intervals], dtype=np.float64
        )
        cp_lower = np.asarray(
            [float(interval["cp_lower"]) for interval in intervals], dtype=np.float64
        )
        cp_upper = np.asarray(
            [float(interval["cp_upper"]) for interval in intervals], dtype=np.float64
        )
        bayes_mc = float(
            np.mean((bayes_lower[samples] <= p) & (p <= bayes_upper[samples]))
        )
        cp_mc = float(np.mean((cp_lower[samples] <= p) & (p <= cp_upper[samples])))
        internal = {
            "p": p,
            "bayes_exact": bayes_exact,
            "bayes_mc": bayes_mc,
            "cp_exact": cp_exact,
            "cp_mc": cp_mc,
            "bayes_width": bayes_width,
            "cp_width": cp_width,
        }
        internal_rows.append(internal)
        coverage_rows.append(
            {
                "p": quantized(p, 2),
                "replications": GRID_REPLICATIONS,
                "bayes_exact_coverage": quantized(bayes_exact),
                "bayes_mc_coverage": quantized(bayes_mc),
                "clopper_pearson_exact_coverage": quantized(cp_exact),
                "clopper_pearson_mc_coverage": quantized(cp_mc),
                "bayes_expected_width": quantized(bayes_width),
                "clopper_pearson_expected_width": quantized(cp_width),
            }
        )

    predictive = [
        beta_binomial_pmf(N, x, PRIOR_A, PRIOR_B) for x in range(N + 1)
    ]
    predictive_sum = math.fsum(predictive)
    bayes_prior_average = math.fsum(
        predictive[x] * float(intervals[x]["bayes_posterior_mass"])
        for x in range(N + 1)
    )
    cp_prior_average = math.fsum(
        predictive[x]
        * (
            beta_cdf_integer(
                float(intervals[x]["cp_upper"]), PRIOR_A + x, PRIOR_B + N - x
            )
            - beta_cdf_integer(
                float(intervals[x]["cp_lower"]), PRIOR_A + x, PRIOR_B + N - x
            )
        )
        for x in range(N + 1)
    )

    prior_p = rng.beta(PRIOR_A, PRIOR_B, size=PRIOR_REPLICATIONS)
    prior_x = rng.binomial(N, prior_p)
    bayes_lower_array = np.asarray(
        [float(interval["bayes_lower"]) for interval in intervals], dtype=np.float64
    )
    bayes_upper_array = np.asarray(
        [float(interval["bayes_upper"]) for interval in intervals], dtype=np.float64
    )
    cp_lower_array = np.asarray(
        [float(interval["cp_lower"]) for interval in intervals], dtype=np.float64
    )
    cp_upper_array = np.asarray(
        [float(interval["cp_upper"]) for interval in intervals], dtype=np.float64
    )
    bayes_prior_mc = float(
        np.mean(
            (bayes_lower_array[prior_x] <= prior_p)
            & (prior_p <= bayes_upper_array[prior_x])
        )
    )
    cp_prior_mc = float(
        np.mean(
            (cp_lower_array[prior_x] <= prior_p)
            & (prior_p <= cp_upper_array[prior_x])
        )
    )

    min_bayes = min(internal_rows, key=lambda row: (row["bayes_exact"], row["p"]))
    max_bayes = max(internal_rows, key=lambda row: (row["bayes_exact"], -row["p"]))
    min_cp = min(internal_rows, key=lambda row: (row["cp_exact"], row["p"]))
    max_bayes_mc_error = max(
        abs(row["bayes_exact"] - row["bayes_mc"]) for row in internal_rows
    )
    max_cp_mc_error = max(abs(row["cp_exact"] - row["cp_mc"]) for row in internal_rows)
    max_posterior_mass_error = max(
        abs(float(interval["bayes_posterior_mass"]) - (1.0 - ALPHA))
        for interval in intervals
    )
    bayes_symmetry_error = max(
        abs(internal_rows[index]["bayes_exact"] - internal_rows[-1 - index]["bayes_exact"])
        for index in range(len(internal_rows))
    )
    cp_symmetry_error = max(
        abs(internal_rows[index]["cp_exact"] - internal_rows[-1 - index]["cp_exact"])
        for index in range(len(internal_rows))
    )

    assertions = {
        "posterior_interval_mass_is_0_95": max_posterior_mass_error < 5e-13,
        "beta_binomial_predictive_sums_to_one": abs(predictive_sum - 1.0) < 5e-13,
        "bayes_prior_average_identity_is_0_95": abs(bayes_prior_average - 0.95) < 5e-13,
        "bayes_prior_monte_carlo_within_0_002": abs(bayes_prior_mc - 0.95) < 0.002,
        "clopper_pearson_grid_coverage_at_least_0_95": float(min_cp["cp_exact"]) >= 0.95 - 5e-13,
        "bayes_fixed_parameter_coverage_not_uniform": float(min_bayes["bayes_exact"]) < 0.90,
        "grid_bayes_monte_carlo_max_error_below_0_008": max_bayes_mc_error < 0.008,
        "grid_cp_monte_carlo_max_error_below_0_008": max_cp_mc_error < 0.008,
        "symmetric_prior_gives_symmetric_bayes_coverage": bayes_symmetry_error < 5e-13,
        "clopper_pearson_coverage_is_symmetric": cp_symmetry_error < 5e-13,
        "all_interval_endpoints_are_ordered": all(
            0.0 <= float(interval["bayes_lower"]) <= float(interval["bayes_upper"]) <= 1.0
            and 0.0 <= float(interval["cp_lower"]) <= float(interval["cp_upper"]) <= 1.0
            for interval in intervals
        ),
    }
    if not all(assertions.values()):
        raise RuntimeError(f"SIM006 assertion failed: {assertions}")

    interval_rows = [
        {
            "x": int(interval["x"]),
            "n": N,
            "posterior_a": int(interval["posterior_a"]),
            "posterior_b": int(interval["posterior_b"]),
            "bayes_lower": quantized(float(interval["bayes_lower"]), 12),
            "bayes_upper": quantized(float(interval["bayes_upper"]), 12),
            "bayes_posterior_mass": quantized(
                float(interval["bayes_posterior_mass"]), 12
            ),
            "clopper_pearson_lower": quantized(float(interval["cp_lower"]), 12),
            "clopper_pearson_upper": quantized(float(interval["cp_upper"]), 12),
        }
        for interval in intervals
    ]
    summary_rows = [
        {"metric": "n", "value": str(N)},
        {"metric": "prior", "value": f"Beta({PRIOR_A},{PRIOR_B})"},
        {"metric": "alpha", "value": quantized(ALPHA)},
        {"metric": "nominal_probability", "value": quantized(1.0 - ALPHA)},
        {"metric": "grid", "value": "0.01:0.01:0.99"},
        {"metric": "grid_replications_per_p", "value": str(GRID_REPLICATIONS)},
        {"metric": "prior_joint_replications", "value": str(PRIOR_REPLICATIONS)},
        {"metric": "bayes_grid_min_coverage", "value": quantized(float(min_bayes["bayes_exact"]))},
        {"metric": "bayes_grid_min_at_p", "value": quantized(float(min_bayes["p"]), 2)},
        {"metric": "bayes_grid_max_coverage", "value": quantized(float(max_bayes["bayes_exact"]))},
        {"metric": "bayes_grid_max_at_p_first", "value": quantized(float(max_bayes["p"]), 2)},
        {"metric": "clopper_pearson_grid_min_coverage", "value": quantized(float(min_cp["cp_exact"]))},
        {"metric": "clopper_pearson_grid_min_at_p_first", "value": quantized(float(min_cp["p"]), 2)},
        {"metric": "bayes_prior_average_exact", "value": quantized(bayes_prior_average, 12)},
        {"metric": "bayes_prior_average_monte_carlo", "value": quantized(bayes_prior_mc, 12)},
        {"metric": "clopper_pearson_prior_average_exact", "value": quantized(cp_prior_average, 12)},
        {"metric": "clopper_pearson_prior_average_monte_carlo", "value": quantized(cp_prior_mc, 12)},
        {"metric": "beta_binomial_predictive_sum", "value": quantized(predictive_sum, 12)},
        {"metric": "max_posterior_mass_error", "value": quantized(max_posterior_mass_error, 15)},
        {"metric": "max_grid_bayes_mc_error", "value": quantized(max_bayes_mc_error, 12)},
        {"metric": "max_grid_cp_mc_error", "value": quantized(max_cp_mc_error, 12)},
    ]

    payloads = {
        "SIM006_beta_binomial_conditional_coverage.csv": csv_bytes(
            list(coverage_rows[0]), coverage_rows
        ),
        "SIM006_beta_binomial_intervals.csv": csv_bytes(
            list(interval_rows[0]), interval_rows
        ),
        "SIM006_beta_binomial_calibration.csv": csv_bytes(
            ["metric", "value"], summary_rows
        ),
        "SIM006_beta_binomial_coverage.svg": conditional_coverage_svg(internal_rows),
    }
    summary = {
        "id": "O006-C140-CMP-SIM006",
        "seed": SEED,
        "model": {
            "sampling": f"X|p~Binomial({N},p)",
            "prior": f"p~Beta({PRIOR_A},{PRIOR_B})",
            "bayesian_interval": f"equal-tail posterior {quantized(1.0 - ALPHA, 2)}",
            "frequentist_interval": f"two-sided Clopper-Pearson {quantized(1.0 - ALPHA, 2)}",
        },
        "fixed_parameter_grid": {
            "first": "0.01",
            "last": "0.99",
            "step": "0.01",
            "points": len(GRID),
            "replications_per_point": GRID_REPLICATIONS,
            "bayes_min_coverage": quantized(float(min_bayes["bayes_exact"])),
            "bayes_min_at_p": quantized(float(min_bayes["p"]), 2),
            "bayes_max_coverage": quantized(float(max_bayes["bayes_exact"])),
            "bayes_max_at_p_first": quantized(float(max_bayes["p"]), 2),
            "clopper_pearson_min_coverage": quantized(float(min_cp["cp_exact"])),
            "clopper_pearson_min_at_p_first": quantized(float(min_cp["p"]), 2),
            "max_bayes_monte_carlo_error": quantized(max_bayes_mc_error, 12),
            "max_clopper_pearson_monte_carlo_error": quantized(max_cp_mc_error, 12),
        },
        "prior_averaged": {
            "replications": PRIOR_REPLICATIONS,
            "bayes_exact": quantized(bayes_prior_average, 12),
            "bayes_monte_carlo": quantized(bayes_prior_mc, 12),
            "clopper_pearson_exact": quantized(cp_prior_average, 12),
            "clopper_pearson_monte_carlo": quantized(cp_prior_mc, 12),
            "predictive_probability_sum": quantized(predictive_sum, 12),
        },
        "numerics": {
            "beta_cdf": "finite binomial sum for positive integer shapes",
            "beta_quantile": f"fixed bisection, {BISECTION_STEPS} steps",
            "serialized_summary_floats": "fixed decimal strings, quantized before JSON/CSV serialization",
            "max_posterior_mass_error": quantized(max_posterior_mass_error, 15),
        },
        "assertions": assertions,
    }
    return payloads, summary


def manifest(payloads: dict[str, bytes]) -> bytes:
    rows = [
        {
            "path": f"generated/simulations/c3/{name}",
            "bytes": len(payload),
            "sha256": sha256(payload),
        }
        for name, payload in sorted(payloads.items())
    ]
    return csv_bytes(["path", "bytes", "sha256"], rows)


def compute() -> tuple[dict[str, bytes], bytes]:
    import sys

    if sys.version.split()[0] != PYTHON_VERSION:
        raise RuntimeError(f"Python version differs: {sys.version.split()[0]}")
    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(f"NumPy version differs: {np.__version__}")
    payloads, summary = experiment()
    payloads["MANIFEST.csv"] = manifest(payloads)
    receipt = canonical_json(
        {
            "schema": "o006.c140.companion-c3-simulations.v1",
            "status": "pass",
            "browser_processes_used": False,
            "network_access": False,
            "environment": {
                "python": PYTHON_VERSION,
                "numpy": NUMPY_VERSION,
                "generator": BIT_GENERATOR,
            },
            "summary": summary,
            "outputs": [
                {
                    "path": f"generated/simulations/c3/{name}",
                    "bytes": len(payload),
                    "sha256": sha256(payload),
                }
                for name, payload in sorted(payloads.items())
            ],
            "all_assertions_pass": True,
            "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        }
    )
    return payloads, receipt


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payloads, receipt = compute()
    expected = set(payloads)
    if args.write:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        actual = {path.name for path in OUTPUT.iterdir() if path.is_file()}
        unexpected = actual - expected
        if unexpected:
            raise RuntimeError(f"unexpected C3 simulation output: {sorted(unexpected)}")
        for name, payload in payloads.items():
            atomic_write(OUTPUT / name, payload)
        atomic_write(RECEIPT, receipt)
        state = "written"
    else:
        actual = {path.name for path in OUTPUT.iterdir() if path.is_file()} if OUTPUT.is_dir() else set()
        if actual != expected:
            raise RuntimeError("C3 simulation output inventory differs")
        for name, payload in payloads.items():
            if (OUTPUT / name).read_bytes() != payload:
                raise RuntimeError(f"C3 simulation output differs: {name}")
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != receipt:
            raise RuntimeError("C3 simulation receipt differs")
        state = "verified"
    print(
        json.dumps(
            {
                "mode": state,
                "status": "pass",
                "simulations": 1,
                "files": len(payloads),
                "bytes": sum(len(value) for value in payloads.values()),
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
