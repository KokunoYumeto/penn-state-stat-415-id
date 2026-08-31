#!/usr/bin/env python3
"""Generate the four deterministic, browser-free C1 simulation families."""

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
OUTPUT = ROOT / "generated" / "simulations" / "c1"
RECEIPT = ROOT / "build" / "C1_SIMULATION_RECEIPT.json"
PYTHON_VERSION = "3.13.9"
NUMPY_VERSION = "2.4.4"
REPLICATIONS = {
    "SIM001": 120_000,
    "SIM002": 160_000,
    "SIM003": 160_000,
    "SIM004": 500_000,
}
SEEDS = {
    "SIM001": 140_001,
    "SIM002": 140_002,
    "SIM003": 140_003,
    "SIM004": 140_004,
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def q(value: float, digits: int = 10) -> float:
    return round(float(value), digits)


def csv_bytes(fields: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


def line_svg(
    *,
    title: str,
    description: str,
    series: list[tuple[str, list[tuple[float, float]], str]],
    x_label: str,
    y_label: str,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
) -> bytes:
    width, height = 900, 520
    left, right, top, bottom = 92, 32, 56, 78
    plot_w = width - left - right
    plot_h = height - top - bottom

    def sx(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y: float) -> float:
        return top + (y_max - y) / (y_max - y_min) * plot_h

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(title)}</title>',
        f'<desc id="desc">{html.escape(description)}</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17202a}.axis{stroke:#273746;stroke-width:1.5}.grid{stroke:#d5d8dc;stroke-width:1}.label{font-size:14px}.heading{font-size:20px;font-weight:700}.legend{font-size:13px}</style>',
        f'<text class="heading" x="{left}" y="30">{html.escape(title)}</text>',
    ]
    for i in range(6):
        x = x_min + (x_max - x_min) * i / 5
        px = sx(x)
        parts.append(f'<line class="grid" x1="{px:.2f}" y1="{top}" x2="{px:.2f}" y2="{top + plot_h}"/>')
        parts.append(f'<text class="label" text-anchor="middle" x="{px:.2f}" y="{top + plot_h + 24}">{x:.2g}</text>')
        y = y_min + (y_max - y_min) * i / 5
        py = sy(y)
        parts.append(f'<line class="grid" x1="{left}" y1="{py:.2f}" x2="{left + plot_w}" y2="{py:.2f}"/>')
        parts.append(f'<text class="label" text-anchor="end" x="{left - 10}" y="{py + 5:.2f}">{y:.3g}</text>')
    parts.extend(
        [
            f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
            f'<text class="label" text-anchor="middle" x="{left + plot_w / 2:.2f}" y="{height - 22}">{html.escape(x_label)}</text>',
            f'<text class="label" text-anchor="middle" transform="translate(22 {top + plot_h / 2:.2f}) rotate(-90)">{html.escape(y_label)}</text>',
        ]
    )
    for index, (label, points, color) in enumerate(series):
        coordinates = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in points)
        parts.append(f'<polyline fill="none" stroke="{color}" stroke-width="3" points="{coordinates}"/>')
        for x, y in points:
            parts.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="4" fill="{color}"/>')
        ly = top + 18 * index
        parts.append(f'<line x1="{left + plot_w - 170}" y1="{ly}" x2="{left + plot_w - 140}" y2="{ly}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text class="legend" x="{left + plot_w - 132}" y="{ly + 5}">{html.escape(label)}</text>')
    parts.append("</svg>\n")
    return "\n".join(parts).encode("utf-8")


def sim001() -> tuple[dict[str, bytes], dict[str, Any]]:
    rng = np.random.Generator(np.random.PCG64(SEEDS["SIM001"]))
    reps = REPLICATIONS["SIM001"]
    critical = 1.959963984540054
    rows: list[dict[str, object]] = []
    points: list[tuple[float, float]] = []
    for n in (10, 30, 100):
        means = rng.normal(0.0, 1.0 / math.sqrt(n), size=reps)
        bias = float(np.mean(means))
        variance = float(np.var(means, ddof=1))
        coverage = float(np.mean(np.abs(np.sqrt(n) * means) <= critical))
        wald = n * means**2
        score = (np.sqrt(n) * means) ** 2
        likelihood_ratio = 2.0 * (0.5 * n * means**2)
        max_statistic_difference = float(
            max(
                np.max(np.abs(wald - score)),
                np.max(np.abs(wald - likelihood_ratio)),
                np.max(np.abs(score - likelihood_ratio)),
            )
        )
        row = {
            "n": n,
            "replications": reps,
            "bias_mle": q(bias),
            "variance_mle": q(variance),
            "n_times_variance": q(n * variance),
            "wald_95_coverage": q(coverage),
            "max_statistic_difference_wald_score_lr": q(max_statistic_difference, 16),
        }
        rows.append(row)
        points.append((float(n), coverage))
    assertions = {
        "absolute_bias_below_0_01": all(abs(float(row["bias_mle"])) < 0.01 for row in rows),
        "scaled_variance_between_0_97_and_1_03": all(0.97 < float(row["n_times_variance"]) < 1.03 for row in rows),
        "coverage_between_0_945_and_0_955": all(0.945 < float(row["wald_95_coverage"]) < 0.955 for row in rows),
        "wald_score_lr_max_difference_below_5e_14": all(float(row["max_statistic_difference_wald_score_lr"]) < 5e-14 for row in rows),
    }
    if not all(assertions.values()):
        raise RuntimeError(f"SIM001 assertion failed: {assertions}")
    csv_payload = csv_bytes(list(rows[0]), rows)
    svg_payload = line_svg(
        title="SIM001: cakupan selang Wald pada model lokasi normal",
        description="Cakupan Monte Carlo mendekati 0,95 untuk n 10, 30, dan 100; prosedur Wald, skor, dan rasio fungsi kemungkinan identik pada model ini.",
        series=[("cakupan", points, "#1f77b4"), ("sasaran 0,95", [(10.0, 0.95), (100.0, 0.95)], "#c0392b")],
        x_label="ukuran sampel n",
        y_label="cakupan",
        x_min=10,
        x_max=100,
        y_min=0.94,
        y_max=0.96,
    )
    return {
        "SIM001_normal_location.csv": csv_payload,
        "SIM001_normal_location.svg": svg_payload,
    }, {
        "id": "O006-C140-CMP-SIM001",
        "seed": SEEDS["SIM001"],
        "replications": reps,
        "assertions": assertions,
        "rows": rows,
    }


def sim002() -> tuple[dict[str, bytes], dict[str, Any]]:
    rng = np.random.Generator(np.random.PCG64(SEEDS["SIM002"]))
    reps = REPLICATIONS["SIM002"]
    n = 50
    rows: list[dict[str, object]] = []
    plot: list[tuple[float, float]] = []
    for theta in (0.0, 0.2, 1.0):
        means = rng.normal(theta, 1.0 / math.sqrt(n), size=reps)
        transformed = means**2
        empirical_variance = float(np.var(np.sqrt(n) * (transformed - theta**2), ddof=1))
        delta_variance = 4.0 * theta**2
        scaled_at_zero = n * transformed if theta == 0.0 else np.array([], dtype=float)
        row = {
            "theta": theta,
            "n": n,
            "replications": reps,
            "empirical_variance_sqrt_n_g_error": q(empirical_variance),
            "first_order_delta_variance": q(delta_variance),
            "variance_ratio_empirical_to_delta": "undefined" if theta == 0.0 else q(empirical_variance / delta_variance),
            "mean_n_times_g_at_theta_zero": q(float(np.mean(scaled_at_zero))) if theta == 0.0 else "not-applicable",
            "q95_n_times_g_at_theta_zero": q(float(np.quantile(scaled_at_zero, 0.95))) if theta == 0.0 else "not-applicable",
        }
        rows.append(row)
        plot.append((theta, empirical_variance))
    zero = rows[0]
    one = rows[2]
    assertions = {
        "regular_theta_1_variance_ratio_between_0_96_and_1_05": 0.96 < float(one["variance_ratio_empirical_to_delta"]) < 1.05,
        "theta_0_scaled_mean_between_0_98_and_1_02": 0.98 < float(zero["mean_n_times_g_at_theta_zero"]) < 1.02,
        "theta_0_scaled_q95_between_3_75_and_3_93": 3.75 < float(zero["q95_n_times_g_at_theta_zero"]) < 3.93,
        "first_order_delta_degenerate_at_theta_0": float(zero["first_order_delta_variance"]) == 0.0,
    }
    if not all(assertions.values()):
        raise RuntimeError(f"SIM002 assertion failed: {assertions}")
    return {
        "SIM002_delta_boundary.csv": csv_bytes(list(rows[0]), rows),
        "SIM002_delta_boundary.svg": line_svg(
            title="SIM002: metode delta reguler dan titik turunan nol",
            description="Varians empiris dari akar-n kali galat transformasi dibandingkan dengan varians metode delta orde pertama untuk parameter θ bernilai 0, 0,2, dan 1.",
            series=[("varians empiris", plot, "#117864"), ("varians delta", [(0.0, 0.0), (0.2, 0.16), (1.0, 4.0)], "#af601a")],
            x_label="parameter θ",
            y_label="varians asimtotik",
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=4.3,
        ),
    }, {
        "id": "O006-C140-CMP-SIM002",
        "seed": SEEDS["SIM002"],
        "replications": reps,
        "assertions": assertions,
        "rows": rows,
    }


def sim003() -> tuple[dict[str, bytes], dict[str, Any]]:
    rng = np.random.Generator(np.random.PCG64(SEEDS["SIM003"]))
    reps = REPLICATIONS["SIM003"]
    rows: list[dict[str, object]] = []
    rate_points: list[tuple[float, float]] = []
    mass_points: list[tuple[float, float]] = []
    for n in (10, 30, 100):
        maxima = rng.random(reps) ** (1.0 / n)
        endpoint_statistic = n * (1.0 - maxima)
        bootstrap_includes_original_maximum = 0
        remaining = reps
        batch_size = 4000
        while remaining:
            batch = min(batch_size, remaining)
            original = rng.random((batch, n))
            original_maximum_indices = np.argmax(original, axis=1)
            bootstrap_indices = rng.integers(0, n, size=(batch, n))
            bootstrap_includes_original_maximum += int(
                np.sum(
                    np.any(
                        bootstrap_indices == original_maximum_indices[:, None],
                        axis=1,
                    )
                )
            )
            remaining -= batch
        bootstrap_zero_mass = bootstrap_includes_original_maximum / reps
        row = {
            "n": n,
            "replications": reps,
            "mean_n_times_endpoint_gap": q(float(np.mean(endpoint_statistic))),
            "q95_n_times_endpoint_gap": q(float(np.quantile(endpoint_statistic, 0.95))),
            "q95_n_times_endpoint_gap_exact": q(n * (1.0 - 0.05 ** (1.0 / n))),
            "mean_sqrt_n_times_endpoint_gap": q(float(np.mean((1.0 - maxima) * math.sqrt(n)))),
            "bootstrap_mass_at_zero_empirical": q(bootstrap_zero_mass),
            "bootstrap_mass_at_zero_exact": q(1.0 - (1.0 - 1.0 / n) ** n),
        }
        rows.append(row)
        rate_points.append((float(n), float(row["mean_n_times_endpoint_gap"])))
        mass_points.append((float(n), float(row["bootstrap_mass_at_zero_empirical"])))
    assertions = {
        "endpoint_n_rate_mean_between_0_90_and_1_02": all(0.90 < float(row["mean_n_times_endpoint_gap"]) < 1.02 for row in rows),
        "endpoint_q95_matches_exact_within_0_08": all(abs(float(row["q95_n_times_endpoint_gap"]) - float(row["q95_n_times_endpoint_gap_exact"])) < 0.08 for row in rows),
        "bootstrap_zero_mass_between_0_61_and_0_66": all(0.61 < float(row["bootstrap_mass_at_zero_empirical"]) < 0.66 for row in rows),
        "sqrt_n_gap_decreases": float(rows[2]["mean_sqrt_n_times_endpoint_gap"]) < float(rows[1]["mean_sqrt_n_times_endpoint_gap"]) < float(rows[0]["mean_sqrt_n_times_endpoint_gap"]),
    }
    if not all(assertions.values()):
        raise RuntimeError(f"SIM003 assertion failed: {assertions}")
    return {
        "SIM003_uniform_endpoint.csv": csv_bytes(list(rows[0]), rows),
        "SIM003_uniform_endpoint.svg": line_svg(
            title="SIM003: laju n dan kegagalan bootstrap pada batas sebaran seragam",
            description="Rata-rata statistik n kali celah ke batas mendekati satu, sedangkan massa bootstrap di nol mendekati 0,632.",
            series=[("E[n(1-Mn)]", rate_points, "#6c3483"), ("massa bootstrap nol", mass_points, "#2874a6")],
            x_label="ukuran sampel n",
            y_label="nilai",
            x_min=10,
            x_max=100,
            y_min=0.55,
            y_max=1.05,
        ),
    }, {
        "id": "O006-C140-CMP-SIM003",
        "seed": SEEDS["SIM003"],
        "replications": reps,
        "assertions": assertions,
        "rows": rows,
    }


def binomial_pmf(n: int, x: int, p: float) -> float:
    return math.comb(n, x) * p**x * (1.0 - p) ** (n - x)


def randomized_power(p: float, gamma: float) -> float:
    return sum(binomial_pmf(4, x, p) for x in (3, 4)) + gamma * binomial_pmf(4, 2, p)


def sim004() -> tuple[dict[str, bytes], dict[str, Any]]:
    rng = np.random.Generator(np.random.PCG64(SEEDS["SIM004"]))
    reps = REPLICATIONS["SIM004"]
    p0, p1, alpha = 0.25, 0.60, 0.10
    p0_ge3 = sum(binomial_pmf(4, x, p0) for x in (3, 4))
    p0_eq2 = binomial_pmf(4, 2, p0)
    gamma = (alpha - p0_ge3) / p0_eq2
    curve_rows: list[dict[str, object]] = []
    points: list[tuple[float, float]] = []
    for i in range(21):
        p = i / 20
        power = randomized_power(p, gamma)
        curve_rows.append({"p": q(p), "exact_rejection_probability": q(power)})
        points.append((p, power))

    empirical: dict[str, float] = {}
    for label, p in (("null", p0), ("alternative", p1)):
        samples = rng.binomial(4, p, size=reps)
        uniforms = rng.random(reps)
        reject = (samples >= 3) | ((samples == 2) & (uniforms < gamma))
        empirical[label] = float(np.mean(reject))
    exact_power = randomized_power(p1, gamma)
    assertions = {
        "gamma_in_unit_interval": 0.0 < gamma < 1.0,
        "exact_size_equals_alpha": abs(randomized_power(p0, gamma) - alpha) < 1e-14,
        "empirical_size_within_0_002": abs(empirical["null"] - alpha) < 0.002,
        "empirical_power_within_0_002": abs(empirical["alternative"] - exact_power) < 0.002,
        "power_at_p1_exceeds_size": exact_power > alpha,
    }
    if not all(assertions.values()):
        raise RuntimeError(f"SIM004 assertion failed: {assertions}")
    summary_rows = [{
        "n": 4,
        "p0": p0,
        "p1": p1,
        "alpha": alpha,
        "reject_if_x_at_least": 3,
        "randomize_if_x_equals": 2,
        "randomization_gamma": q(gamma),
        "exact_size": q(randomized_power(p0, gamma)),
        "empirical_size": q(empirical["null"]),
        "exact_power_at_p1": q(exact_power),
        "empirical_power_at_p1": q(empirical["alternative"]),
        "replications_per_parameter": reps,
    }]
    return {
        "SIM004_neyman_pearson_summary.csv": csv_bytes(list(summary_rows[0]), summary_rows),
        "SIM004_neyman_pearson_power.csv": csv_bytes(list(curve_rows[0]), curve_rows),
        "SIM004_neyman_pearson_power.svg": line_svg(
            title="SIM004: fungsi daya uji Neyman–Pearson teracak",
            description="Probabilitas penolakan eksak untuk X binomial dengan n empat; randomisasi pada X sama dengan dua menghasilkan ukuran uji tepat 0,10 ketika p sama dengan 0,25.",
            series=[("daya eksak", points, "#b03a2e"), ("taraf 0,10", [(0.0, 0.1), (1.0, 0.1)], "#1f618d")],
            x_label="parameter p",
            y_label="probabilitas penolakan",
            x_min=0,
            x_max=1,
            y_min=0,
            y_max=1,
        ),
    }, {
        "id": "O006-C140-CMP-SIM004",
        "seed": SEEDS["SIM004"],
        "replications": reps,
        "gamma": q(gamma),
        "exact_size": q(randomized_power(p0, gamma)),
        "exact_power_at_p1": q(exact_power),
        "empirical": {key: q(value) for key, value in empirical.items()},
        "assertions": assertions,
    }


def compute() -> tuple[dict[Path, bytes], bytes]:
    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(f"NumPy version differs: {np.__version__}")
    import sys

    if sys.version.split()[0] != PYTHON_VERSION:
        raise RuntimeError(f"Python version differs: {sys.version.split()[0]}")
    payloads: dict[Path, bytes] = {}
    simulations: list[dict[str, Any]] = []
    for function in (sim001, sim002, sim003, sim004):
        files, receipt = function()
        for name, payload in files.items():
            path = OUTPUT / name
            if path in payloads:
                raise RuntimeError(f"duplicate simulation output: {name}")
            payloads[path] = payload
        simulations.append(receipt)
    manifest_rows = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": len(payload),
            "sha256": sha256(payload),
        }
        for path, payload in sorted(payloads.items(), key=lambda item: item[0].as_posix())
    ]
    manifest = csv_bytes(["path", "bytes", "sha256"], manifest_rows)
    manifest_path = OUTPUT / "MANIFEST.csv"
    payloads[manifest_path] = manifest
    receipt = canonical_json({
        "schema": "o006.c140.companion-c1-simulations.v1",
        "status": "pass",
        "browser_processes_used": False,
        "network_access": False,
        "environment": {
            "python": PYTHON_VERSION,
            "numpy": NUMPY_VERSION,
            "generator": "numpy.random.Generator(PCG64)",
        },
        "simulations": simulations,
        "files": len(payloads),
        "bytes": sum(len(value) for value in payloads.values()),
        "manifest": {
            "path": manifest_path.relative_to(ROOT).as_posix(),
            "bytes": len(manifest),
            "sha256": sha256(manifest),
        },
        "all_assertions_pass": True,
        "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
    })
    return payloads, receipt


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
        ) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payloads, receipt = compute()
    outputs = dict(payloads)
    outputs[RECEIPT] = receipt
    if args.write:
        for path, payload in outputs.items():
            if path.is_symlink() or path.is_dir():
                raise RuntimeError(f"unsafe simulation output collision: {path}")
            atomic_write(path, payload)
        state = "written"
    else:
        for path, expected in outputs.items():
            if path.is_symlink() or not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"simulation replay differs: {path.relative_to(ROOT)}")
        state = "verified"
    value = json.loads(receipt)
    print(json.dumps({
        "mode": state,
        "status": value["status"],
        "simulations": len(value["simulations"]),
        "files": value["files"],
        "bytes": value["bytes"],
        "receipt_sha256": sha256(receipt),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
