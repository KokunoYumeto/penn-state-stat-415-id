#!/usr/bin/env python3
"""Generate deterministic matrix-regression evidence for C2 without a browser."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "generated" / "simulations" / "c2"
RECEIPT = ROOT / "build" / "C2_SIMULATION_RECEIPT.json"
SEED = 2026082805
REPLICATIONS = 12_000
PYTHON_VERSION = "3.13.9"
NUMPY_VERSION = "2.4.4"
T975_DF77 = 1.991254395
Z975 = 1.959963985


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_bytes(header: list[str], rows: list[list[object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def fmt(value: float) -> str:
    return f"{value:.8f}"


def stable_float(value: float) -> float:
    """Remove irrelevant BLAS-order noise from receipt-only numeric summaries."""

    return float(f"{value:.12g}")


def coverage_svg(classical: float, hc3: float, exact: float) -> bytes:
    width, height = 720, 430
    left, right, top, bottom = 95, 35, 45, 90
    plot_w, plot_h = width - left - right, height - top - bottom
    ymin, ymax = 0.70, 1.00

    def y(value: float) -> float:
        return top + (ymax - value) / (ymax - ymin) * plot_h

    labels = [
        ("Gaussian eksak", exact, "#2563eb"),
        ("Hetero klasik", classical, "#dc2626"),
        ("Hetero HC3", hc3, "#15803d"),
    ]
    bar_w = 105
    gap = 75
    x0 = 145
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Cakupan selang regresi pada tiga skenario</title>',
        '<desc id="desc">Diagram batang memperlihatkan cakupan selang 95 persen: Gaussian eksak sekitar 0,948, heteroskedastik dengan galat baku klasik sekitar 0,840, dan heteroskedastik dengan HC3 sekitar 0,943. Garis putus-putus menandai sasaran 0,95.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="360" y="25" text-anchor="middle" font-family="sans-serif" font-size="17">Cakupan selang 95% untuk koefisien kemiringan</text>',
    ]
    for tick in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00):
        yy = y(tick)
        parts.append(f'<line x1="{left}" y1="{yy:.2f}" x2="{width-right}" y2="{yy:.2f}" stroke="#d1d5db" stroke-width="1"/>')
        parts.append(f'<text x="{left-10}" y="{yy+5:.2f}" text-anchor="end" font-family="sans-serif" font-size="12">{tick:.2f}</text>')
    parts.append(f'<line x1="{left}" y1="{y(0.95):.2f}" x2="{width-right}" y2="{y(0.95):.2f}" stroke="#111827" stroke-width="2" stroke-dasharray="7 5"/>')
    for index, (label, value, color) in enumerate(labels):
        xx = x0 + index * (bar_w + gap)
        yy = y(value)
        bar_h = top + plot_h - yy
        parts.append(f'<rect x="{xx}" y="{yy:.2f}" width="{bar_w}" height="{bar_h:.2f}" fill="{color}"/>')
        parts.append(f'<text x="{xx+bar_w/2:.2f}" y="{yy-8:.2f}" text-anchor="middle" font-family="sans-serif" font-size="13">{value:.3f}</text>')
        parts.append(f'<text x="{xx+bar_w/2:.2f}" y="{height-53}" text-anchor="middle" font-family="sans-serif" font-size="13">{label}</text>')
    parts.extend([
        '<text x="360" y="412" text-anchor="middle" font-family="sans-serif" font-size="12">Garis putus-putus: sasaran nominal 0,95</text>',
        '</svg>',
    ])
    return ("\n".join(parts) + "\n").encode("utf-8")


def experiment() -> tuple[dict[str, bytes], dict[str, object]]:
    rng = np.random.Generator(np.random.PCG64(SEED))
    n, p = 80, 3
    x = np.linspace(-2.0, 2.0, n, dtype=np.float64)
    z = np.sin(np.linspace(0.0, 3.0 * np.pi, n, dtype=np.float64))
    z = (z - z.mean()) / z.std(ddof=0)
    X = np.column_stack((np.ones(n), x, z))
    beta = np.array([1.0, 0.8, -0.5], dtype=np.float64)
    xtx_inv = np.linalg.inv(X.T @ X)
    projection = X @ xtx_inv @ X.T
    leverage = np.diag(projection)
    transform = X @ xtx_inv
    df = n - p

    epsilon = rng.standard_normal((REPLICATIONS, n))
    y_exact = X @ beta + epsilon
    beta_exact = y_exact @ transform
    residual_exact = y_exact - beta_exact @ X.T
    s2_exact = np.einsum("ij,ij->i", residual_exact, residual_exact) / df
    se_exact = np.sqrt(s2_exact * xtx_inv[1, 1])
    t_exact = (beta_exact[:, 1] - beta[1]) / se_exact
    coverage_exact = float(np.mean(np.abs(t_exact) <= T975_DF77))

    sigma_i = 0.35 + 1.65 * (np.abs(x) / 2.0) ** 2
    y_hetero = X @ beta + rng.standard_normal((REPLICATIONS, n)) * sigma_i
    beta_hetero = y_hetero @ transform
    residual_hetero = y_hetero - beta_hetero @ X.T
    s2_hetero = np.einsum("ij,ij->i", residual_hetero, residual_hetero) / df
    se_classical = np.sqrt(s2_hetero * xtx_inv[1, 1])
    coverage_classical = float(
        np.mean(np.abs(beta_hetero[:, 1] - beta[1]) <= T975_DF77 * se_classical)
    )

    adjusted2 = (residual_hetero / (1.0 - leverage)) ** 2
    meat = np.einsum("ni,rn,nj->rij", X, adjusted2, X, optimize=True)
    sandwich = np.einsum("ab,rbc,cd->rad", xtx_inv, meat, xtx_inv, optimize=True)
    se_hc3 = np.sqrt(sandwich[:, 1, 1])
    coverage_hc3 = float(
        np.mean(np.abs(beta_hetero[:, 1] - beta[1]) <= Z975 * se_hc3)
    )

    X_base = X[:40].copy()
    y_base = X_base @ beta + np.linspace(-0.35, 0.35, 40)
    X_influence = np.vstack((X_base, np.array([1.0, 6.0, 0.0])))
    y_influence = np.append(y_base, np.array([1.0, 6.0, 0.0]) @ beta + 7.0)
    inv_influence = np.linalg.inv(X_influence.T @ X_influence)
    bhat_all = inv_influence @ X_influence.T @ y_influence
    fitted_all = X_influence @ bhat_all
    residual_all = y_influence - fitted_all
    H_all = X_influence @ inv_influence @ X_influence.T
    h_all = np.diag(H_all)
    s2_all = float(residual_all @ residual_all / (len(y_influence) - p))
    cook = residual_all**2 / (p * s2_all) * h_all / (1.0 - h_all) ** 2
    bhat_delete = np.linalg.lstsq(X_base, y_base, rcond=None)[0]
    influential = len(y_influence) - 1

    bias_exact = float(beta_exact[:, 1].mean() - beta[1])
    bias_hetero = float(beta_hetero[:, 1].mean() - beta[1])
    empirical_sd_exact = float(beta_exact[:, 1].std(ddof=1))
    empirical_sd_hetero = float(beta_hetero[:, 1].std(ddof=1))

    if abs(bias_exact) >= 0.01 or abs(bias_hetero) >= 0.015:
        raise RuntimeError("OLS bias assertion failed")
    if not (0.94 <= coverage_exact <= 0.96):
        raise RuntimeError(f"exact Gaussian coverage assertion failed: {coverage_exact}")
    if not (coverage_classical < 0.90):
        raise RuntimeError(f"classical heteroskedastic coverage did not fail: {coverage_classical}")
    if not (0.92 <= coverage_hc3 <= 0.98):
        raise RuntimeError(f"HC3 coverage assertion failed: {coverage_hc3}")
    if not (coverage_hc3 - coverage_classical >= 0.05):
        raise RuntimeError("HC3 did not materially improve coverage")
    if not (h_all[influential] > 0.65 and cook[influential] > 1.0):
        raise RuntimeError("influence construction failed")
    if not (abs(bhat_all[1] - bhat_delete[1]) > 0.20):
        raise RuntimeError("delete-one slope change is too small")
    if not np.allclose(projection, projection.T, atol=1e-12):
        raise RuntimeError("projection symmetry failed")
    if not np.allclose(projection @ projection, projection, atol=1e-12):
        raise RuntimeError("projection idempotence failed")

    coverage = csv_bytes(
        ["scenario", "replications", "coefficient", "bias", "empirical_sd", "mean_se", "coverage_95"],
        [
            ["gaussian_homoskedastic_exact_t", REPLICATIONS, "beta_1", fmt(bias_exact), fmt(empirical_sd_exact), fmt(float(se_exact.mean())), fmt(coverage_exact)],
            ["heteroskedastic_classical_t", REPLICATIONS, "beta_1", fmt(bias_hetero), fmt(empirical_sd_hetero), fmt(float(se_classical.mean())), fmt(coverage_classical)],
            ["heteroskedastic_hc3_normal", REPLICATIONS, "beta_1", fmt(bias_hetero), fmt(empirical_sd_hetero), fmt(float(se_hc3.mean())), fmt(coverage_hc3)],
        ],
    )
    influence = csv_bytes(
        ["metric", "value"],
        [
            ["influential_index_zero_based", influential],
            ["influential_leverage", fmt(float(h_all[influential]))],
            ["influential_residual", fmt(float(residual_all[influential]))],
            ["influential_cook_distance", fmt(float(cook[influential]))],
            ["slope_with_point", fmt(float(bhat_all[1]))],
            ["slope_without_point", fmt(float(bhat_delete[1]))],
            ["absolute_slope_change", fmt(float(abs(bhat_all[1] - bhat_delete[1])))],
            ["max_other_cook_distance", fmt(float(np.max(cook[:-1])))],
        ],
    )
    svg = coverage_svg(coverage_classical, coverage_hc3, coverage_exact)
    payloads = {
        "SIM005_matrix_regression_coverage.csv": coverage,
        "SIM005_matrix_regression_coverage.svg": svg,
        "SIM005_matrix_regression_influence.csv": influence,
    }
    summary = {
        "seed": SEED,
        "replications": REPLICATIONS,
        "design": {"n": n, "p": p, "rank": int(np.linalg.matrix_rank(X)), "df_residual": df},
        "gaussian": {
            "slope_bias": stable_float(bias_exact),
            "empirical_sd": stable_float(empirical_sd_exact),
            "mean_classical_se": stable_float(float(se_exact.mean())),
            "exact_t_coverage_95": stable_float(coverage_exact),
        },
        "heteroskedastic": {
            "slope_bias": stable_float(bias_hetero),
            "empirical_sd": stable_float(empirical_sd_hetero),
            "mean_classical_se": stable_float(float(se_classical.mean())),
            "mean_hc3_se": stable_float(float(se_hc3.mean())),
            "classical_t_coverage_95": stable_float(coverage_classical),
            "hc3_normal_coverage_95": stable_float(coverage_hc3),
        },
        "influence": {
            "index_zero_based": influential,
            "leverage": stable_float(float(h_all[influential])),
            "residual": stable_float(float(residual_all[influential])),
            "cook_distance": stable_float(float(cook[influential])),
            "slope_with_point": stable_float(float(bhat_all[1])),
            "slope_without_point": stable_float(float(bhat_delete[1])),
        },
        "assertions": {
            "projection_symmetric": True,
            "projection_idempotent": True,
            "ols_bias_small": True,
            "exact_t_coverage_near_nominal": True,
            "classical_heteroskedastic_undercoverage": True,
            "hc3_improves_coverage": True,
            "high_leverage_influence_detected": True,
        },
    }
    return payloads, summary


def manifest(payloads: dict[str, bytes]) -> bytes:
    rows = [[name, len(payload), sha256(payload)] for name, payload in sorted(payloads.items())]
    return csv_bytes(["filename", "bytes", "sha256"], rows)


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


def compute() -> tuple[dict[str, bytes], bytes]:
    import sys

    if sys.version.split()[0] != PYTHON_VERSION:
        raise RuntimeError(f"Python version differs: {sys.version.split()[0]}")
    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(f"NumPy version differs: {np.__version__}")
    payloads, summary = experiment()
    payloads["MANIFEST.csv"] = manifest(payloads)
    receipt = canonical_json({
        "schema": "o006.c140.companion-c2-simulations.v1",
        "status": "pass",
        "browser_processes_used": False,
        "network_access": False,
        "python": PYTHON_VERSION,
        "numpy": NUMPY_VERSION,
        "bit_generator": "PCG64",
        "summary": summary,
        "outputs": [
            {"path": f"generated/simulations/c2/{name}", "bytes": len(payload), "sha256": sha256(payload)}
            for name, payload in sorted(payloads.items())
        ],
    })
    return payloads, receipt


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payloads, receipt = compute()
    if args.write:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        expected = set(payloads)
        for candidate in OUTPUT.iterdir():
            if candidate.is_file() and candidate.name not in expected:
                raise RuntimeError(f"unexpected C2 simulation output: {candidate.name}")
        for name, payload in payloads.items():
            atomic_write(OUTPUT / name, payload)
        atomic_write(RECEIPT, receipt)
        state = "written"
    else:
        actual = {path.name for path in OUTPUT.iterdir() if path.is_file()} if OUTPUT.is_dir() else set()
        if actual != set(payloads):
            raise RuntimeError("C2 simulation output inventory differs")
        for name, payload in payloads.items():
            if (OUTPUT / name).read_bytes() != payload:
                raise RuntimeError(f"C2 simulation output differs: {name}")
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != receipt:
            raise RuntimeError("C2 simulation receipt differs")
        state = "verified"
    print(json.dumps({
        "mode": state,
        "status": "pass",
        "simulations": 1,
        "files": len(payloads),
        "bytes": sum(len(value) for value in payloads.values()),
        "receipt_sha256": sha256(receipt),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
