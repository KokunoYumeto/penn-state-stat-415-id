#!/usr/bin/env python3
"""Generate the deterministic, offline CP01 regression evidence package."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import locale
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "capstones" / "CP01"
CLEAN = DATA / "clean"
OUTPUT = ROOT / "generated" / "capstones" / "CP01"
TRANSFORM_RECEIPT = ROOT / "build" / "CP01_TRANSFORM_RECEIPT.json"

PYTHON_VERSION = "3.13.9"
NUMPY_VERSION = "2.4.4"
SCIPY_VERSION = "1.17.1"
ENVIRONMENT = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "TZ": "UTC",
}
RAW_SHA256 = "8d4b15b6fc68cd932d745cbd663d5ceae66dd54422e99c1e4865f2936ab7e2af"
RAW_BYTES = 41472
PROVENANCE_SHA256 = "08cd61239545c65900eabc0912cc01181314134d8c59afe2b11c5a026cd33fa0"
PROVENANCE_BYTES = 16885
SHA256SUMS_SHA256 = "f11ee0fc23691482863a42330004eff024d65dd5c71809a815dc2b02e73028b8"
SHA256SUMS_BYTES = 1635
ALPHA = 0.05
TERM_IDS = (
    "INTERCEPT",
    "CEMENT",
    "SLAG",
    "FLY_ASH",
    "WATER",
    "SUPERPLASTICIZER",
    "COARSE_AGGREGATE",
    "FINE_AGGREGATE",
    "AGE",
)
CLEAN_NAMES = (
    "cement_kg_per_m3",
    "blast_furnace_slag_kg_per_m3",
    "fly_ash_kg_per_m3",
    "water_kg_per_m3",
    "superplasticizer_kg_per_m3",
    "coarse_aggregate_kg_per_m3",
    "fine_aggregate_kg_per_m3",
    "age_days",
    "compressive_strength_mpa",
)
UNITS = (
    "MPa",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_day",
)
MODEL_FULL = "FULL_ADDITIVE_RAW"
MODEL_REDUCED = "REDUCED_NO_SLG_FLY_SP"
MODEL_LOG = "FULL_ADDITIVE_LOG_AGE_28"
MODEL_SCREEN_FULL = "FULL_ADDITIVE_RAW_SCREEN_UNION_REFIT"
MODEL_SCREEN_REDUCED = "REDUCED_NO_SLG_FLY_SP_SCREEN_UNION_REFIT"
REDUCED_COLUMNS = (0, 1, 4, 6, 7, 8)
REDUCED_TERMS = (
    "INTERCEPT",
    "CEMENT",
    "WATER",
    "COARSE_AGGREGATE",
    "FINE_AGGREGATE",
    "AGE",
)
REDUCED_SOURCE = (
    "NA",
    "cement_kg_per_m3",
    "water_kg_per_m3",
    "coarse_aggregate_kg_per_m3",
    "fine_aggregate_kg_per_m3",
    "age_days",
)
REDUCED_UNITS = (
    "MPa",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_kg_per_m3",
    "MPa_per_day",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, separators=(",", ": "))
        + "\n"
    ).encode("utf-8")


def csv_bytes(fields: list[str] | tuple[str, ...], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(fields),
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def f8(value: float) -> str:
    rounded = float(value)
    if abs(rounded) < 0.5e-8:
        rounded = 0.0
    return f"{rounded:.8f}"


def e8(value: float) -> str:
    return f"{float(value):.8e}"


def p8(value: float) -> str:
    value = float(value)
    return e8(value) if value < 1.0e-4 else f8(value)


def btext(value: bool) -> str:
    return "true" if value else "false"


def localized(value: float, digits: int) -> str:
    return f"{float(value):.{digits}f}".replace(".", ",")


def assert_close(label: str, observed: float, expected: float, absolute: float) -> None:
    if not math.isfinite(observed) or abs(observed - expected) > absolute:
        raise RuntimeError(
            f"{label} assertion differs: expected {expected:.17g}, observed {observed:.17g}, "
            f"difference {observed - expected:.17g}, tolerance {absolute:.17g}, raw_sha256 {RAW_SHA256}"
        )


def validate_environment() -> tuple[Any, Any, Any]:
    for name, expected in ENVIRONMENT.items():
        observed = os.environ.get(name)
        if observed != expected:
            raise RuntimeError(f"environment {name} must be {expected!r}, observed {observed!r}")
    if sys.version.split()[0] != PYTHON_VERSION:
        raise RuntimeError(
            f"Python version differs: expected {PYTHON_VERSION}, observed {sys.version.split()[0]}"
        )
    locale.setlocale(locale.LC_NUMERIC, "C")
    import numpy as np
    import scipy
    from scipy import optimize, stats

    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(
            f"NumPy version differs: expected {NUMPY_VERSION}, observed {np.__version__}"
        )
    if scipy.__version__ != SCIPY_VERSION:
        raise RuntimeError(
            f"SciPy version differs: expected {SCIPY_VERSION}, observed {scipy.__version__}"
        )
    return np, stats, optimize


def validate_inputs(np: Any) -> dict[str, Any]:
    raw_payload = (DATA / "raw" / "data.csv").read_bytes()
    if len(raw_payload) != RAW_BYTES or sha256(raw_payload) != RAW_SHA256:
        raise RuntimeError("CP01 raw/data.csv identity differs")
    provenance_path = DATA / "DATASET_PROVENANCE.json"
    sums_path = DATA / "SHA256SUMS"
    provenance_payload = provenance_path.read_bytes()
    sums_payload = sums_path.read_bytes()
    if (
        len(provenance_payload) != PROVENANCE_BYTES
        or sha256(provenance_payload) != PROVENANCE_SHA256
    ):
        raise RuntimeError("CP01 DATASET_PROVENANCE.json identity differs")
    if len(sums_payload) != SHA256SUMS_BYTES or sha256(sums_payload) != SHA256SUMS_SHA256:
        raise RuntimeError("CP01 SHA256SUMS identity differs")
    provenance = json.loads(provenance_payload)
    if (
        provenance.get("schema_version") != "1.0"
        or provenance.get("freeze_status") != "frozen"
        or provenance.get("canonical_analysis_asset") != "raw/data.csv"
        or provenance.get("rights", {}).get("spdx_expression") != "CC-BY-4.0"
    ):
        raise RuntimeError("CP01 rights/provenance contract differs")
    sums_rows: dict[str, str] = {}
    for line in sums_payload.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  ([!-~][ -~]*)", line)
        if match is None or match.group(2) in sums_rows:
            raise RuntimeError("CP01 SHA256SUMS syntax or uniqueness differs")
        sums_rows[match.group(2)] = match.group(1)
    provenance_asset_paths: list[str] = []
    for asset in provenance.get("assets", []):
        provenance_asset_paths.append(asset["path"])
        if "header_capture" in asset:
            provenance_asset_paths.append(asset["header_capture"]["path"])
    if len(sums_rows) != 16 or set(sums_rows) != set(provenance_asset_paths):
        raise RuntimeError("CP01 rights/provenance asset inventory differs")
    rights_provenance_inventory = [
        {
            "path": "data/capstones/CP01/DATASET_PROVENANCE.json",
            "bytes": len(provenance_payload),
            "sha256": sha256(provenance_payload),
        },
        {
            "path": "data/capstones/CP01/SHA256SUMS",
            "bytes": len(sums_payload),
            "sha256": sha256(sums_payload),
        },
    ]
    for relative, expected_hash in sorted(sums_rows.items()):
        relative_path = Path(relative)
        candidate = (DATA / relative_path).resolve()
        if relative_path.is_absolute() or not candidate.is_relative_to(DATA.resolve()):
            raise RuntimeError(f"CP01 provenance asset escapes data directory: {relative}")
        payload = candidate.read_bytes()
        if sha256(payload) != expected_hash:
            raise RuntimeError(f"CP01 provenance asset hash differs: {relative}")
        rights_provenance_inventory.append(
            {
                "path": f"data/capstones/CP01/{relative_path.as_posix()}",
                "bytes": len(payload),
                "sha256": expected_hash,
            }
        )
    if not TRANSFORM_RECEIPT.is_file():
        raise RuntimeError("CP01 transform receipt is missing")
    receipt_payload = TRANSFORM_RECEIPT.read_bytes()
    receipt = json.loads(receipt_payload)
    if receipt.get("schema") != "o006.c140.cp01-transform-replay.v1":
        raise RuntimeError("CP01 transform receipt schema differs")
    if receipt.get("status") != "pass" or not receipt.get("all_assertions_pass"):
        raise RuntimeError("CP01 transform receipt did not pass")
    expected_clean = {
        "COLUMN_MANIFEST.csv",
        "ROW_MANIFEST.csv",
        "TRANSFORM_LEDGER.json",
        "concrete_compressive_strength.csv",
    }
    actual_clean = {path.name for path in CLEAN.iterdir() if path.is_file()} if CLEAN.is_dir() else set()
    if actual_clean != expected_clean:
        raise RuntimeError(
            f"CP01 clean inventory differs: expected {sorted(expected_clean)}, observed {sorted(actual_clean)}"
        )
    receipt_outputs = {Path(item["path"]).name: item for item in receipt["outputs"]}
    if set(receipt_outputs) != expected_clean:
        raise RuntimeError("CP01 transform receipt output inventory differs")
    clean_inventory: list[dict[str, object]] = []
    for name in sorted(expected_clean):
        payload = (CLEAN / name).read_bytes()
        item = receipt_outputs[name]
        if len(payload) != item["bytes"] or sha256(payload) != item["sha256"]:
            raise RuntimeError(f"CP01 clean hash differs from transform receipt: {name}")
        clean_inventory.append(
            {"path": f"data/capstones/CP01/clean/{name}", "bytes": len(payload), "sha256": sha256(payload)}
        )
    ledger = json.loads((CLEAN / "TRANSFORM_LEDGER.json").read_bytes())
    if ledger.get("schema") != "o006.c140.cp01-transform-ledger.v1":
        raise RuntimeError("CP01 transform ledger schema differs")

    clean_payload = (CLEAN / "concrete_compressive_strength.csv").read_bytes()
    rows = list(csv.reader(io.StringIO(clean_payload.decode("utf-8"), newline=""), strict=True))
    if len(rows) != 1031 or tuple(rows[0]) != CLEAN_NAMES:
        raise RuntimeError("CP01 clean data schema differs")
    tokens = rows[1:]
    if any(len(row) != 9 for row in tokens):
        raise RuntimeError("CP01 clean data row width differs")
    data = np.asarray([[float(token) for token in row] for row in tokens], dtype=np.float64)
    if data.shape != (1030, 9) or not bool(np.all(np.isfinite(data))):
        raise RuntimeError("CP01 clean numeric matrix differs")

    row_manifest_rows = list(
        csv.DictReader(io.StringIO((CLEAN / "ROW_MANIFEST.csv").read_text(encoding="utf-8"), newline=""))
    )
    if len(row_manifest_rows) != 1030:
        raise RuntimeError("CP01 row manifest must have 1030 records")
    for index, row in enumerate(row_manifest_rows, start=1):
        expected_id = f"CP01-R{index:04d}"
        if (
            row["row_id"] != expected_id
            or int(row["source_record"]) != index
            or int(row["source_line"]) != index + 1
            or int(row["clean_record"]) != index
            or row["disposition"] != "kept"
            or row["exclusion_reason"] != ""
        ):
            raise RuntimeError(f"CP01 row manifest identity differs at {expected_id}")
        record_payload = (",".join(tokens[index - 1]) + "\n").encode("utf-8")
        if row["canonical_row_sha256"] != sha256(record_payload):
            raise RuntimeError(f"CP01 row hash differs at {expected_id}")
    column_manifest_rows = list(
        csv.DictReader(io.StringIO((CLEAN / "COLUMN_MANIFEST.csv").read_text(encoding="utf-8"), newline=""))
    )
    if len(column_manifest_rows) != 9 or tuple(row["clean_name"] for row in column_manifest_rows) != CLEAN_NAMES:
        raise RuntimeError("CP01 column manifest differs")

    profile_members: dict[tuple[str, ...], list[int]] = {}
    full_members: dict[tuple[str, ...], list[int]] = {}
    for index, row in enumerate(tokens):
        profile_members.setdefault(tuple(row[:8]), []).append(index)
        full_members.setdefault(tuple(row), []).append(index)
    repeated_profiles = [members for members in profile_members.values() if len(members) > 1]
    repeated_full = [members for members in full_members.values() if len(members) > 1]
    varying = [
        members
        for members in repeated_profiles
        if len({tokens[index][8] for index in members}) > 1
    ]
    profile_sizes: dict[int, int] = {}
    for members in repeated_profiles:
        profile_sizes[len(members)] = profile_sizes.get(len(members), 0) + 1
    full_sizes: dict[int, int] = {}
    for members in repeated_full:
        full_sizes[len(members)] = full_sizes.get(len(members), 0) + 1
    duplicate_assertion = (
        len(profile_members) == 992
        and len(repeated_profiles) == 19
        and sum(map(len, repeated_profiles)) == 57
        and profile_sizes == {2: 5, 3: 9, 4: 5}
        and len(repeated_full) == 11
        and sum(map(len, repeated_full)) == 36
        and full_sizes == {2: 1, 3: 6, 4: 4}
        and len(varying) == 9
        and sum(map(len, varying)) == 24
    )
    if not duplicate_assertion:
        raise RuntimeError("CP01 duplicate/profile inventory differs")
    return {
        "data": data,
        "tokens": tokens,
        "row_manifest": row_manifest_rows,
        "column_manifest": column_manifest_rows,
        "profile_members": profile_members,
        "clean_inventory": clean_inventory,
        "rights_provenance_inventory": rights_provenance_inventory,
        "transform_receipt": {
            "path": "build/CP01_TRANSFORM_RECEIPT.json",
            "bytes": len(receipt_payload),
            "sha256": sha256(receipt_payload),
        },
    }


def fit_model(np: Any, x: Any, y: Any, model_id: str) -> dict[str, Any]:
    n, p = x.shape
    singular = np.linalg.svd(x, full_matrices=False, compute_uv=False)
    tau = float(np.finfo(np.float64).eps * max(n, p) * singular[0])
    rank = int(np.sum(singular > tau))
    if rank != p:
        raise RuntimeError(f"{model_id} rank is {rank}, expected {p}")
    q, r = np.linalg.qr(x, mode="reduced")
    beta = np.linalg.solve(r, q.T @ y)
    fitted = x @ beta
    projection_fitted = q @ (q.T @ y)
    projection_error = float(np.max(np.abs(fitted - projection_fitted)))
    if projection_error > 2.0e-9:
        raise RuntimeError(f"{model_id} QR projection equivalence failed: {projection_error}")
    residual = y - fitted
    rss = float(residual @ residual)
    df = n - rank
    if df <= 0 or rss <= 0.0:
        raise RuntimeError(f"{model_id} residual degrees of freedom or RSS failed")
    s2 = rss / df
    s = math.sqrt(s2)
    r_inverse = np.linalg.solve(r, np.eye(p, dtype=np.float64))
    gram_inverse = r_inverse @ r_inverse.T
    leverage = np.sum(q * q, axis=1)
    if (
        float(np.min(leverage)) < -2.0e-14
        or float(np.max(leverage)) >= 1.0 - 1.0e-12
        or abs(float(np.sum(leverage)) - p) > 2.0e-11
    ):
        raise RuntimeError(f"{model_id} leverage assertion failed")
    covariance = s2 * gram_inverse
    hc3_weights = residual * residual / ((1.0 - leverage) ** 2)
    meat = x.T @ (hc3_weights[:, None] * x)
    covariance_hc3 = gram_inverse @ meat @ gram_inverse
    covariance = (covariance + covariance.T) / 2.0
    covariance_hc3 = (covariance_hc3 + covariance_hc3.T) / 2.0
    for label, matrix in (("classic", covariance), ("HC3", covariance_hc3)):
        symmetry_error = float(np.max(np.abs(matrix - matrix.T)))
        minimum_eigenvalue = float(np.min(np.linalg.eigvalsh(matrix)))
        if symmetry_error > 1.0e-10 or minimum_eigenvalue < -1.0e-10:
            raise RuntimeError(f"{model_id} {label} covariance assertion failed")

    centered = y - float(np.mean(y))
    sst = float(centered @ centered)
    r2 = 1.0 - rss / sst
    adjusted_r2 = 1.0 - (1.0 - r2) * (n - 1) / df
    predictors = x[:, 1:]
    means = np.mean(predictors, axis=0)
    sample_sd = np.std(predictors, axis=0, ddof=1)
    if not bool(np.all(np.isfinite(sample_sd) & (sample_sd > 0.0))):
        raise RuntimeError(f"{model_id} predictor standard deviations failed")
    scaled_x = np.column_stack((np.ones(n), (predictors - means) / sample_sd))
    singular_scaled = np.linalg.svd(scaled_x, full_matrices=False, compute_uv=False)
    tau_scaled = float(np.finfo(np.float64).eps * max(n, p) * singular_scaled[0])
    rank_scaled = int(np.sum(singular_scaled > tau_scaled))
    if rank_scaled != p:
        raise RuntimeError(f"{model_id} scaled rank is {rank_scaled}, expected {p}")
    kappa_raw = float(singular[0] / singular[-1])
    kappa_scaled = float(singular_scaled[0] / singular_scaled[-1])
    if not math.isfinite(kappa_scaled) or kappa_scaled >= 1.0e8:
        raise RuntimeError(f"{model_id} scaled condition-number gate failed")
    scaled_beta = np.linalg.lstsq(scaled_x, y, rcond=None)[0]
    scaled_fit_error = float(np.max(np.abs(scaled_x @ scaled_beta - fitted)))
    if scaled_fit_error > 2.0e-9:
        raise RuntimeError(f"{model_id} scaled/raw fitted-value equivalence failed")
    scaled_normal_error = float(np.max(np.abs(scaled_x.T @ residual)))
    if scaled_normal_error > 5.0e-8:
        raise RuntimeError(f"{model_id} residual orthogonality failed: {scaled_normal_error}")
    return {
        "model_id": model_id,
        "x": x,
        "y": y,
        "n": n,
        "p": p,
        "rank": rank,
        "df": df,
        "beta": beta,
        "q": q,
        "r": r,
        "gram_inverse": gram_inverse,
        "fitted": fitted,
        "residual": residual,
        "rss": rss,
        "s2": s2,
        "s": s,
        "sigma2_mle": rss / n,
        "leverage": leverage,
        "covariance": covariance,
        "covariance_hc3": covariance_hc3,
        "sst": sst,
        "ssr": sst - rss,
        "r2": r2,
        "adjusted_r2": adjusted_r2,
        "rmse_in_sample": math.sqrt(rss / n),
        "mae_in_sample": float(np.mean(np.abs(residual))),
        "singular_raw": singular,
        "singular_scaled": singular_scaled,
        "tau_raw": tau,
        "tau_scaled": tau_scaled,
        "kappa_raw": kappa_raw,
        "kappa_scaled": kappa_scaled,
        "scaled_predictor_means": means,
        "scaled_predictor_sample_sd": sample_sd,
        "projection_error": projection_error,
        "scaled_normal_error": scaled_normal_error,
    }


def infer_rows(stats: Any, fit: dict[str, Any], term_ids: tuple[str, ...], sources: tuple[str, ...], units: tuple[str, ...]) -> list[dict[str, object]]:
    tcrit = float(stats.t.ppf(1.0 - ALPHA / 2.0, fit["df"]))
    zcrit = float(stats.norm.ppf(1.0 - ALPHA / 2.0))
    classic_se = fit["covariance"].diagonal() ** 0.5
    hc3_se = fit["covariance_hc3"].diagonal() ** 0.5
    rows: list[dict[str, object]] = []
    for index, term_id in enumerate(term_ids):
        estimate = float(fit["beta"][index])
        t_value = estimate / float(classic_se[index])
        p_value = float(2.0 * stats.t.sf(abs(t_value), fit["df"]))
        z_value = estimate / float(hc3_se[index])
        p_hc3 = float(2.0 * stats.norm.sf(abs(z_value)))
        rows.append(
            {
                "model_id": fit["model_id"],
                "term_id": term_id,
                "source_column": sources[index],
                "unit": units[index],
                "n": fit["n"],
                "p": fit["p"],
                "rank": fit["rank"],
                "df": fit["df"],
                "estimate": f8(estimate),
                "se_gaussian": f8(float(classic_se[index])),
                "t": f8(t_value),
                "p_raw": p8(p_value),
                "ci95_point_lo": f8(estimate - tcrit * float(classic_se[index])),
                "ci95_point_hi": f8(estimate + tcrit * float(classic_se[index])),
                "se_HC3": f8(float(hc3_se[index])),
                "z_HC3": f8(z_value),
                "p_HC3": p8(p_hc3),
                "ci95_HC3_lo": f8(estimate - zcrit * float(hc3_se[index])),
                "ci95_HC3_hi": f8(estimate + zcrit * float(hc3_se[index])),
            }
        )
    return rows


def conditioning_values(np: Any, fit: dict[str, Any]) -> dict[str, float]:
    return {
        "kappa2_raw": float(fit["kappa_raw"]),
        "kappa2_scaled": float(fit["kappa_scaled"]),
        "kappa2_xtx_scaled": float(fit["kappa_scaled"] ** 2),
    }


def analytic_loo(np: Any, fit: dict[str, Any]) -> dict[str, Any]:
    if not bool(np.all(1.0 - fit["leverage"] > 1.0e-12)):
        raise RuntimeError(f"{fit['model_id']} has an invalid LOOCV denominator")
    error = fit["residual"] / (1.0 - fit["leverage"])
    prediction = fit["y"] - error
    press = float(error @ error)
    return {
        "error": error,
        "prediction": prediction,
        "press": press,
        "mse": press / fit["n"],
        "rmse": math.sqrt(press / fit["n"]),
        "mae": float(np.mean(np.abs(error))),
        "min_training_rank": fit["p"],
    }


def verify_explicit_loo(np: Any, fit: dict[str, Any]) -> int:
    minimum_rank = fit["p"]
    maximum_error = 0.0
    for index in range(fit["n"]):
        keep = np.arange(fit["n"]) != index
        beta, _, rank, _ = np.linalg.lstsq(fit["x"][keep], fit["y"][keep], rcond=None)
        minimum_rank = min(minimum_rank, int(rank))
        prediction = float(fit["x"][index] @ beta)
        analytic = float(fit["y"][index] - fit["residual"][index] / (1.0 - fit["leverage"][index]))
        maximum_error = max(maximum_error, abs(prediction - analytic))
    tolerance = 1.0e-9 * max(1.0, float(np.max(np.abs(fit["y"]))))
    if minimum_rank != fit["p"] or maximum_error > tolerance:
        raise RuntimeError(
            f"{fit['model_id']} explicit LOOCV verification failed: rank {minimum_rank}, error {maximum_error}"
        )
    return minimum_rank


def loppo(np: Any, fit: dict[str, Any], profile_members: dict[tuple[str, ...], list[int]], loo: dict[str, Any], row_manifest: list[dict[str, str]]) -> tuple[dict[str, Any], list[dict[str, object]]]:
    predictions = np.empty(fit["n"], dtype=np.float64)
    errors = np.empty(fit["n"], dtype=np.float64)
    ranks = np.empty(fit["n"], dtype=np.int64)
    profile_ids = [""] * fit["n"]
    profile_sizes = np.empty(fit["n"], dtype=np.int64)
    maximum_block_identity_error = 0.0
    all_indices = np.arange(fit["n"])
    for members in profile_members.values():
        group = np.asarray(members, dtype=np.int64)
        keep = ~np.isin(all_indices, group)
        beta, _, rank, _ = np.linalg.lstsq(fit["x"][keep], fit["y"][keep], rcond=None)
        if int(rank) != fit["p"]:
            raise RuntimeError(
                f"{fit['model_id']} LOPPO training rank failed for profile beginning {members[0] + 1}"
            )
        group_prediction = fit["x"][group] @ beta
        group_error = fit["y"][group] - group_prediction
        h_group = fit["q"][group] @ fit["q"][group].T
        block_error = np.linalg.solve(np.eye(len(group)) - h_group, fit["residual"][group])
        maximum_block_identity_error = max(
            maximum_block_identity_error,
            float(np.max(np.abs(group_error - block_error))),
        )
        profile_id = f"CP01-PROFILE-R{min(members) + 1:04d}"
        predictions[group] = group_prediction
        errors[group] = group_error
        ranks[group] = int(rank)
        profile_sizes[group] = len(group)
        for index in members:
            profile_ids[index] = profile_id
    tolerance = 1.0e-9 * max(1.0, float(np.max(np.abs(fit["y"]))))
    if maximum_block_identity_error > tolerance:
        raise RuntimeError(
            f"{fit['model_id']} LOPPO block/refit identity failed: {maximum_block_identity_error}"
        )
    press = float(errors @ errors)
    metrics = {
        "error": errors,
        "prediction": predictions,
        "press": press,
        "mse": press / fit["n"],
        "rmse": math.sqrt(press / fit["n"]),
        "mae": float(np.mean(np.abs(errors))),
        "min_training_rank": int(np.min(ranks)),
        "maximum_block_identity_error": maximum_block_identity_error,
    }
    rows: list[dict[str, object]] = []
    for index in range(fit["n"]):
        rows.append(
            {
                "model_id": fit["model_id"],
                "predictor_profile_id": profile_ids[index],
                "profile_size": int(profile_sizes[index]),
                "row_id": row_manifest[index]["row_id"],
                "source_record": index + 1,
                "source_line": index + 2,
                "training_rank": int(ranks[index]),
                "predicted_mpa": f8(float(predictions[index])),
                "residual_mpa": f8(float(errors[index])),
                "absolute_difference_from_rowwise_loo_mpa": f8(
                    abs(float(predictions[index] - loo["prediction"][index]))
                ),
            }
        )
    return metrics, rows


def convex_hull_certificate(np: Any, optimize: Any, z: Any, target: Any) -> dict[str, Any]:
    means = np.mean(z, axis=0)
    scales = np.std(z, axis=0, ddof=1)
    zs = (z - means) / scales
    ts = (target - means) / scales
    # Maximize a^T target+b subject to a^T z_i+b<=0 and ||a||_1<=1.
    # Split a=a_plus-a_minus so the certificate is a deterministic LP.
    a_ub = np.column_stack((zs, -zs, np.ones(len(zs))))
    a_ub = np.vstack((a_ub, np.r_[np.ones(16), 0.0]))
    b_ub = np.r_[np.zeros(len(zs)), 1.0]
    c = np.r_[-ts, ts, -1.0]
    result = optimize.linprog(
        c,
        A_ub=a_ub,
        b_ub=b_ub,
        bounds=[(0.0, None)] * 16 + [(None, None)],
        method="highs",
        options={"presolve": True},
    )
    if not result.success:
        raise RuntimeError(f"convex-hull separation LP failed operationally: {result.message}")
    margin = float(-result.fun)
    if margin <= 1.0e-8:
        raise RuntimeError(f"reference profile has no robust separating margin: {margin}")
    return {
        "in_convex_hull": False,
        "method": "deterministic_HiGHS_L1_separating_hyperplane",
        "separator_margin_standardized": margin,
        "gate": 1.0e-8,
    }


def residual_bins(np: Any, fit: dict[str, Any]) -> tuple[list[dict[str, object]], list[dict[str, float]]]:
    boundaries = np.quantile(fit["fitted"], np.linspace(0.0, 1.0, 11), method="linear")
    assignments = np.searchsorted(boundaries[1:-1], fit["fitted"], side="left")
    rows: list[dict[str, object]] = []
    internal: list[dict[str, float]] = []
    for index in range(10):
        selected = assignments == index
        fitted = fit["fitted"][selected]
        residual = fit["residual"][selected]
        record = {
            "bin_index": index + 1,
            "count": int(np.sum(selected)),
            "boundary_lo": float(boundaries[index]),
            "boundary_hi": float(boundaries[index + 1]),
            "fitted_min": float(np.min(fitted)),
            "fitted_max": float(np.max(fitted)),
            "mean_residual_mpa": float(np.mean(residual)),
            "rms_residual_mpa": math.sqrt(float(np.mean(residual * residual))),
        }
        internal.append(record)
        rows.append(
            {
                "model_id": fit["model_id"],
                "bin_index": index + 1,
                "count": record["count"],
                "boundary_lo": f8(record["boundary_lo"]),
                "boundary_hi": f8(record["boundary_hi"]),
                "fitted_min": f8(record["fitted_min"]),
                "fitted_max": f8(record["fitted_max"]),
                "mean_residual_mpa": f8(record["mean_residual_mpa"]),
                "rms_residual_mpa": f8(record["rms_residual_mpa"]),
            }
        )
    expected_counts = [103, 103, 103, 103, 103, 103, 103, 103, 104, 102]
    if [record["count"] for record in internal] != expected_counts:
        raise RuntimeError("residual-bin counts differ")
    return rows, internal


def svg_document(title: str, description: str, body: list[str], width: int, height: int, prefix: str) -> bytes:
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" lang="id" xml:lang="id" aria-labelledby="{prefix}-title {prefix}-desc">',
        f'<title id="{prefix}-title">{html.escape(title)}</title>',
        f'<desc id="{prefix}-desc">{html.escape(description)}</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#17202a}.axis{stroke:#273746;stroke-width:1.4}.grid{stroke:#d5d8dc;stroke-width:1}.label{font-size:13px}.small{font-size:11px}.heading{font-size:20px;font-weight:700}.series{fill:none;stroke-width:2}.point{fill:#2471a3;stroke:#17202a;stroke-width:.35}.square{fill:#ffffff;stroke:#922b21;stroke-width:1.8}</style>',
        f'<text class="heading" x="64" y="31">{html.escape(title)}</text>',
    ]
    parts.extend(body)
    parts.append("</svg>")
    return ("\n".join(parts) + "\n").encode("utf-8")


def residual_svg(fit: dict[str, Any], internal_residual: Any, bins: list[dict[str, float]], description: str) -> bytes:
    width, height = 1040, 720
    left, right = 82.0, 34.0
    plot_w = width - left - right
    panel_h = 245.0
    top1, top2 = 68.0, 390.0
    xmin, xmax = float(min(fit["fitted"])), float(max(fit["fitted"]))
    residual_limit = 1.08 * float(max(abs(min(fit["residual"])), abs(max(fit["residual"]))))
    scale_values = abs(internal_residual) ** 0.5
    scale_max = 1.08 * float(max(scale_values))

    def sx(value: float) -> float:
        return left + (value - xmin) / (xmax - xmin) * plot_w

    def sy1(value: float) -> float:
        return top1 + panel_h / 2.0 - value / (2.0 * residual_limit) * panel_h

    def sy2(value: float) -> float:
        return top2 + panel_h - value / scale_max * panel_h

    body = [
        f'<text class="label" x="{left}" y="53">Panel A: sisaan (MPa) terhadap nilai suaian (MPa); lingkaran mewakili 1.030 observasi pemasangan utama.</text>',
        f'<line class="axis" x1="{left}" y1="{top1 + panel_h}" x2="{left + plot_w}" y2="{top1 + panel_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top1}" x2="{left}" y2="{top1 + panel_h}"/>',
        f'<line x1="{left}" y1="{sy1(0):.2f}" x2="{left + plot_w}" y2="{sy1(0):.2f}" stroke="#922b21" stroke-width="1.8" stroke-dasharray="7 5"/>',
    ]
    for fitted, residual in zip(fit["fitted"], fit["residual"]):
        body.append(f'<circle class="point" cx="{sx(float(fitted)):.2f}" cy="{sy1(float(residual)):.2f}" r="1.65"/>')
    bin_points = " ".join(
        f"{sx((record['fitted_min'] + record['fitted_max']) / 2.0):.2f},{sy1(record['mean_residual_mpa']):.2f}"
        for record in bins
    )
    body.append(f'<polyline class="series" stroke="#117864" stroke-dasharray="3 3" points="{bin_points}"/>')
    for record in bins:
        x = sx((record["fitted_min"] + record["fitted_max"]) / 2.0)
        y = sy1(record["mean_residual_mpa"])
        body.append(f'<rect class="square" x="{x - 3:.2f}" y="{y - 3:.2f}" width="6" height="6"/>')
    body.extend(
        [
            f'<text class="label" text-anchor="middle" x="{left + plot_w / 2}" y="{top1 + panel_h + 25}">kuat tekan hasil suaian (MPa)</text>',
            f'<text class="label" text-anchor="middle" transform="translate(22 {top1 + panel_h / 2}) rotate(-90)">sisaan (MPa)</text>',
            f'<text class="label" x="{left}" y="{top2 - 15}">Panel B: lokasi-skala, akar(|sisaan terstandardisasi internal|) terhadap nilai suaian.</text>',
            f'<line class="axis" x1="{left}" y1="{top2 + panel_h}" x2="{left + plot_w}" y2="{top2 + panel_h}"/>',
            f'<line class="axis" x1="{left}" y1="{top2}" x2="{left}" y2="{top2 + panel_h}"/>',
        ]
    )
    for fitted, scale in zip(fit["fitted"], scale_values):
        body.append(f'<path d="M {sx(float(fitted)) - 1.7:.2f} {sy2(float(scale)) + 1.7:.2f} L {sx(float(fitted)):.2f} {sy2(float(scale)) - 1.7:.2f} L {sx(float(fitted)) + 1.7:.2f} {sy2(float(scale)) + 1.7:.2f} Z" fill="#7d3c98" stroke="#17202a" stroke-width=".3"/>')
    body.extend(
        [
            f'<text class="label" text-anchor="middle" x="{left + plot_w / 2}" y="{top2 + panel_h + 27}">kuat tekan hasil suaian (MPa)</text>',
            f'<text class="label" text-anchor="middle" transform="translate(22 {top2 + panel_h / 2}) rotate(-90)">akar(|sisaan terstandardisasi internal|)</text>',
            f'<text class="small" x="{left + 12}" y="{top1 + 19}">lingkaran: observasi; garis putus-putus dan persegi: rataan bin; merah putus-putus: nol</text>',
            f'<text class="small" x="{left + 12}" y="{height - 12}">Bukti diagnostik spesifikasi saja; panel tidak membuktikan sebab-akibat atau mengizinkan penghapusan.</text>',
        ]
    )
    return svg_document("Diagnostik sisaan dan lokasi-skala CP01", description, body, width, height, "cp01-rf")


def quantile_svg(np: Any, stats: Any, deleted_t: Any, row_ids: list[str], description: str) -> bytes:
    order = sorted(range(len(deleted_t)), key=lambda index: (float(deleted_t[index]), index))
    observed = np.asarray([deleted_t[index] for index in order], dtype=np.float64)
    theoretical = stats.norm.ppf((np.arange(len(observed)) + 0.5) / len(observed))
    width, height = 900, 620
    left, right, top, bottom = 78.0, 35.0, 62.0, 76.0
    plot_w, plot_h = width - left - right, height - top - bottom
    lo = float(min(theoretical.min(), observed.min()))
    hi = float(max(theoretical.max(), observed.max()))

    def sx(value: float) -> float:
        return left + (value - lo) / (hi - lo) * plot_w

    def sy(value: float) -> float:
        return top + (hi - value) / (hi - lo) * plot_h

    body = [
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
        f'<line x1="{sx(lo):.2f}" y1="{sy(lo):.2f}" x2="{sx(hi):.2f}" y2="{sy(hi):.2f}" stroke="#922b21" stroke-width="2" stroke-dasharray="8 5"/>',
    ]
    for x_value, y_value in zip(theoretical, observed):
        body.append(f'<circle class="point" cx="{sx(float(x_value)):.2f}" cy="{sy(float(y_value)):.2f}" r="2"/>')
    extreme = max(range(len(deleted_t)), key=lambda index: (abs(float(deleted_t[index])), -index))
    rank = order.index(extreme)
    ex, ey = float(theoretical[rank]), float(observed[rank])
    body.extend(
        [
            f'<text class="label" x="{sx(ex) - 105:.2f}" y="{sy(ey) - 8:.2f}">{html.escape(row_ids[extreme])}: {localized(ey, 8)}</text>',
            f'<text class="label" text-anchor="middle" x="{left + plot_w / 2}" y="{height - 26}">kuantil acuan normal baku</text>',
            f'<text class="label" text-anchor="middle" transform="translate(22 {top + plot_h / 2}) rotate(-90)">sisaan terstudentisasi penghapusan-satu</text>',
            f'<text class="small" x="{left + 12}" y="{top + 18}">lingkaran: 1.030 observasi; diagonal putus-putus: acuan normal baku</text>',
            f'<text class="small" x="{left + 12}" y="{height - 8}">Kedekatan visual bersifat deskriptif dan tidak membuktikan galat Gaussian.</text>',
        ]
    )
    return svg_document("Kuantil sisaan terstudentisasi penghapusan-satu CP01", description, body, width, height, "cp01-qq")


def influence_svg(fit: dict[str, Any], deleted_t: Any, cook: Any, row_ids: list[str], description: str) -> bytes:
    width, height = 940, 640
    left, right, top, bottom = 78.0, 42.0, 66.0, 80.0
    plot_w, plot_h = width - left - right, height - top - bottom
    xmax = 1.08 * float(max(fit["leverage"]))
    ylimit = 1.12 * float(max(abs(min(deleted_t)), abs(max(deleted_t))))

    def sx(value: float) -> float:
        return left + value / xmax * plot_w

    def sy(value: float) -> float:
        return top + (ylimit - value) / (2.0 * ylimit) * plot_h

    body = [
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
    ]
    for threshold, label in ((18.0 / 1030.0, "2p/n"), (27.0 / 1030.0, "3p/n")):
        body.append(f'<line x1="{sx(threshold):.2f}" y1="{top}" x2="{sx(threshold):.2f}" y2="{top + plot_h}" stroke="#117864" stroke-width="1.5" stroke-dasharray="{6 if label == "2p/n" else 2} 4"/>')
        body.append(f'<text class="small" x="{sx(threshold) + 4:.2f}" y="{top + 16}">{label}</text>')
    for threshold in (-3.0, -2.0, 2.0, 3.0):
        body.append(f'<line x1="{left}" y1="{sy(threshold):.2f}" x2="{left + plot_w}" y2="{sy(threshold):.2f}" stroke="#922b21" stroke-width="1" stroke-dasharray="3 4"/>')
    for leverage, t_value, cook_value in zip(fit["leverage"], deleted_t, cook):
        radius = 1.6 + 22.0 * math.sqrt(float(cook_value))
        body.append(f'<circle cx="{sx(float(leverage)):.2f}" cy="{sy(float(t_value)):.2f}" r="{radius:.2f}" fill="#f5b041" stroke="#17202a" stroke-width=".5"/>')
    selected = sorted(
        set(
            [max(range(len(cook)), key=lambda i: (float(cook[i]), -i))]
            + [max(range(len(deleted_t)), key=lambda i: (abs(float(deleted_t[i])), -i))]
            + [max(range(len(fit["leverage"])), key=lambda i: (float(fit["leverage"][i]), -i))]
        )
    )
    for index in selected:
        body.append(f'<text class="small" x="{sx(float(fit["leverage"][index])) + 7:.2f}" y="{sy(float(deleted_t[index])) - 6:.2f}">{row_ids[index]}</text>')
    body.extend(
        [
            f'<text class="label" text-anchor="middle" x="{left + plot_w / 2}" y="{height - 28}">leverage h_ii</text>',
            f'<text class="label" text-anchor="middle" transform="translate(22 {top + plot_h / 2}) rotate(-90)">sisaan terstudentisasi penghapusan-satu</text>',
            f'<text class="small" x="{left + 12}" y="{top + 18}">luas lingkaran bertambah bersama jarak Cook; pola garis menandai ambang eksploratif</text>',
            f'<text class="small" x="{left + 12}" y="{height - 9}">Penanda menggambarkan sensitivitas; penanda tidak mengizinkan penghapusan baris otomatis.</text>',
        ]
    )
    return svg_document("Leverage, sisaan penghapusan-satu, dan pengaruh Cook CP01", description, body, width, height, "cp01-inf")


def coefficient_svg(contrast_internal: list[dict[str, Any]], ratios: Any, description: str) -> bytes:
    width, height = 980, 650
    left, right, top, bottom = 170.0, 40.0, 68.0, 88.0
    plot_w, plot_h = width - left - right, height - top - bottom
    lo = min(record["hc3_lo"] for record in contrast_internal)
    hi = max(record["hc3_hi"] for record in contrast_internal)
    lo = min(lo, min(record["classic_lo"] for record in contrast_internal), 0.0)
    hi = max(hi, max(record["classic_hi"] for record in contrast_internal), 0.0)
    padding = 0.08 * (hi - lo)
    lo, hi = lo - padding, hi + padding

    def sx(value: float) -> float:
        return left + (value - lo) / (hi - lo) * plot_w

    body = [
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
        f'<line x1="{sx(0.0):.2f}" y1="{top}" x2="{sx(0.0):.2f}" y2="{top + plot_h}" stroke="#273746" stroke-width="1.5" stroke-dasharray="3 4"/>',
    ]
    for index, record in enumerate(contrast_internal):
        y = top + (index + 0.7) / len(contrast_internal) * plot_h
        body.append(f'<text class="label" text-anchor="end" x="{left - 12}" y="{y + 4:.2f}">{record["contrast_id"]} ({html.escape(record["scale_label"])})</text>')
        body.append(f'<line x1="{sx(record["classic_lo"]):.2f}" y1="{y - 4:.2f}" x2="{sx(record["classic_hi"]):.2f}" y2="{y - 4:.2f}" stroke="#1f618d" stroke-width="2"/>')
        body.append(f'<circle cx="{sx(record["estimate"]):.2f}" cy="{y - 4:.2f}" r="3.4" fill="#1f618d"/>')
        body.append(f'<line x1="{sx(record["hc3_lo"]):.2f}" y1="{y + 5:.2f}" x2="{sx(record["hc3_hi"]):.2f}" y2="{y + 5:.2f}" stroke="#922b21" stroke-width="2" stroke-dasharray="7 4"/>')
        body.append(f'<rect class="square" x="{sx(record["estimate"]) - 3:.2f}" y="{y + 2:.2f}" width="6" height="6"/>')
    body.extend(
        [
            f'<text class="label" text-anchor="middle" x="{left + plot_w / 2}" y="{height - 35}">taksiran perubahan kuat tekan (MPa)</text>',
            f'<text class="small" x="{left + 8}" y="{top + 17}">garis/lingkaran penuh: interval t Gaussian; garis/persegi putus-putus: interval normal asimtotik HC3</text>',
            f'<text class="small" x="{left + 8}" y="{height - 11}">Rasio galat baku HC3/klasik seluruh sembilan koefisien melebihi 1; maksimum {localized(float(max(ratios)), 3)} untuk UMUR. Skala berbeda menurut kontras.</text>',
        ]
    )
    return svg_document("Ketidakpastian kontras yang ditetapkan di muka — CP01", description, body, width, height, "cp01-coef")


def model_svg(metrics: dict[str, dict[str, Any]], screen_max_delta: float, description: str) -> bytes:
    models = (MODEL_FULL, MODEL_REDUCED, MODEL_LOG)
    labels = ("penuh, umur mentah", "tereduksi", "penuh, log umur")
    width, height = 900, 600
    left, right, top, bottom = 86.0, 38.0, 68.0, 112.0
    plot_w, plot_h = width - left - right, height - top - bottom
    ymax = 1.12 * max(metrics[model]["loppo"]["rmse"] for model in models)

    def sx(index: int) -> float:
        return left + (index + 0.5) / len(models) * plot_w

    def sy(value: float) -> float:
        return top + (ymax - value) / ymax * plot_h

    body = [
        f'<line class="axis" x1="{left}" y1="{top + plot_h}" x2="{left + plot_w}" y2="{top + plot_h}"/>',
        f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_h}"/>',
    ]
    loo_points: list[str] = []
    loppo_points: list[str] = []
    for index, (model, label) in enumerate(zip(models, labels)):
        x = sx(index)
        loo_y = sy(metrics[model]["loocv"]["rmse"])
        loppo_y = sy(metrics[model]["loppo"]["rmse"])
        loo_points.append(f"{x:.2f},{loo_y:.2f}")
        loppo_points.append(f"{x:.2f},{loppo_y:.2f}")
        body.append(f'<text class="label" text-anchor="middle" x="{x:.2f}" y="{top + plot_h + 25}">{html.escape(label)}</text>')
        body.append(f'<text class="small" text-anchor="middle" x="{x:.2f}" y="{min(loo_y, loppo_y) - 10:.2f}">{localized(metrics[model]["loocv"]["rmse"], 3)} / {localized(metrics[model]["loppo"]["rmse"], 3)}</text>')
    body.append(f'<polyline class="series" stroke="#1f618d" points="{" ".join(loo_points)}"/>')
    body.append(f'<polyline class="series" stroke="#922b21" stroke-dasharray="8 5" points="{" ".join(loppo_points)}"/>')
    for point in loo_points:
        x, y = point.split(",")
        body.append(f'<circle cx="{x}" cy="{y}" r="4" fill="#1f618d"/>')
    for point in loppo_points:
        x, y = point.split(",")
        body.append(f'<rect class="square" x="{float(x) - 4:.2f}" y="{float(y) - 4:.2f}" width="8" height="8"/>')
    body.extend(
        [
            f'<text class="label" text-anchor="middle" transform="translate(24 {top + plot_h / 2}) rotate(-90)">RMSE data tertahan (MPa)</text>',
            f'<text class="small" x="{left + 12}" y="{top + 18}">lingkaran penuh: LOOCV baris analitik; persegi putus-putus: LOPPO eksak 992 profil</text>',
            f'<text class="small" x="{left + 12}" y="{height - 42}">Pemasangan ulang setelah penyaringan gabungan memakai 907 baris dan tidak mempunyai taksiran CV pascapenyaringan.</text>',
            f'<text class="small" x="{left + 12}" y="{height - 22}">Prediksinya berbeda paling besar {localized(screen_max_delta, 2)} MPa dari pemasangan utama; pemasangan ulang ini bukan model pengganti.</text>',
        ]
    )
    return svg_document("Sensitivitas model dan validasi CP01", description, body, width, height, "cp01-mod")


def manifest_bytes(payloads: dict[str, bytes]) -> bytes:
    rows = [
        {
            "path": f"generated/capstones/CP01/{name}",
            "bytes": len(payload),
            "sha256": sha256(payload),
        }
        for name, payload in sorted(payloads.items())
    ]
    return csv_bytes(["path", "bytes", "sha256"], rows)


def build(np: Any, stats: Any, optimize: Any) -> tuple[dict[str, bytes], dict[str, Any]]:
    inputs = validate_inputs(np)
    data = inputs["data"]
    z = data[:, :8]
    y = data[:, 8]
    n = len(y)
    x_full = np.column_stack((np.ones(n), z))
    x_reduced = x_full[:, REDUCED_COLUMNS]
    x_log = x_full.copy()
    x_log[:, -1] = np.log(z[:, -1] / 28.0)

    full = fit_model(np, x_full, y, MODEL_FULL)
    reduced = fit_model(np, x_reduced, y, MODEL_REDUCED)
    log_fit = fit_model(np, x_log, y, MODEL_LOG)
    assert_close("full RSS", full["rss"], 110413.15315710597, 3.0e-7)
    assert_close("reduced RSS", reduced["rss"], 123782.47881340148, 3.0e-7)
    assert_close("log-age RSS", log_fit["rss"], 52119.82519362, 3.0e-7)
    assert_close("full R2", full["r2"], 0.61551987041427214, 3.0e-12)
    assert_close("full scaled condition", full["kappa_scaled"], 8.711778718605796, 3.0e-11)
    assert_close("reduced scaled condition", reduced["kappa_scaled"], 2.2235241722293844, 3.0e-11)
    assert_close("log scaled condition", log_fit["kappa_scaled"], 8.54118981, 3.0e-8)

    full_sources = ("NA",) + CLEAN_NAMES[:8]
    inference_fields = [
        "model_id", "term_id", "source_column", "unit", "n", "p", "rank", "df",
        "estimate", "se_gaussian", "t", "p_raw", "ci95_point_lo", "ci95_point_hi",
        "se_HC3", "z_HC3", "p_HC3", "ci95_HC3_lo", "ci95_HC3_hi",
    ]
    inference_rows = infer_rows(stats, full, TERM_IDS, full_sources, UNITS)
    inference_rows.extend(infer_rows(stats, reduced, REDUCED_TERMS, REDUCED_SOURCE, REDUCED_UNITS))

    classic_se = np.sqrt(np.diag(full["covariance"]))
    hc3_se = np.sqrt(np.diag(full["covariance_hc3"]))
    ratios = hc3_se / classic_se
    coefficient_comparison_rows = [
        {
            "model_id": MODEL_FULL,
            "term_id": term,
            "estimate": f8(float(full["beta"][index])),
            "se_gaussian": f8(float(classic_se[index])),
            "se_HC3": f8(float(hc3_se[index])),
            "hc3_to_gaussian_ratio": f8(float(ratios[index])),
        }
        for index, term in enumerate(TERM_IDS)
    ]
    if not bool(np.all(ratios > 1.0)):
        raise RuntimeError("expected all nine full-model HC3 SEs to exceed classical SEs")
    assert_close("age HC3/classic ratio", float(ratios[-1]), 1.57821939, 3.0e-8)

    contrast_specs = (
        ("CMT10", "CEMENT", 1, 10.0, "kg_per_m3", "+10 kg/m^3"),
        ("SLG10", "SLAG", 2, 10.0, "kg_per_m3", "+10 kg/m^3"),
        ("FLY10", "FLY_ASH", 3, 10.0, "kg_per_m3", "+10 kg/m^3"),
        ("WAT10", "WATER", 4, 10.0, "kg_per_m3", "+10 kg/m^3"),
        ("SP01", "SUPERPLASTICIZER", 5, 1.0, "kg_per_m3", "+1 kg/m^3"),
        ("CRS100", "COARSE_AGGREGATE", 6, 100.0, "kg_per_m3", "+100 kg/m^3"),
        ("FIN100", "FINE_AGGREGATE", 7, 100.0, "kg_per_m3", "+100 kg/m^3"),
        ("AGE07", "AGE", 8, 7.0, "day", "+7 hari"),
    )
    tcrit = float(stats.t.ppf(0.975, full["df"]))
    tcrit_bonf = float(stats.t.ppf(1.0 - ALPHA / 16.0, full["df"]))
    zcrit = float(stats.norm.ppf(0.975))
    zcrit_bonf = float(stats.norm.ppf(1.0 - ALPHA / 16.0))
    contrast_rows: list[dict[str, object]] = []
    contrast_internal: list[dict[str, Any]] = []
    for contrast_id, term_id, index, delta, delta_unit, scale_label in contrast_specs:
        vector = np.zeros(9)
        vector[index] = delta
        estimate = float(vector @ full["beta"])
        se = math.sqrt(float(vector @ full["covariance"] @ vector))
        se_hc3 = math.sqrt(float(vector @ full["covariance_hc3"] @ vector))
        t_value = estimate / se
        z_value = estimate / se_hc3
        p_value = float(2.0 * stats.t.sf(abs(t_value), full["df"]))
        p_hc3 = float(2.0 * stats.norm.sf(abs(z_value)))
        record = {
            "contrast_id": contrast_id,
            "term_id": term_id,
            "delta": f8(delta),
            "delta_unit": delta_unit,
            "estimate_MPa": f8(estimate),
            "se_gaussian": f8(se),
            "t": f8(t_value),
            "df": full["df"],
            "p_raw": p8(p_value),
            "ci95_point_lo": f8(estimate - tcrit * se),
            "ci95_point_hi": f8(estimate + tcrit * se),
            "p_bonferroni_m8": p8(min(1.0, 8.0 * p_value)),
            "ci95_bonf_lo": f8(estimate - tcrit_bonf * se),
            "ci95_bonf_hi": f8(estimate + tcrit_bonf * se),
            "se_HC3": f8(se_hc3),
            "z_HC3": f8(z_value),
            "p_HC3": p8(p_hc3),
            "ci95_HC3_lo": f8(estimate - zcrit * se_hc3),
            "ci95_HC3_hi": f8(estimate + zcrit * se_hc3),
            "p_HC3_bonferroni_m8": p8(min(1.0, 8.0 * p_hc3)),
            "ci95_HC3_bonf_lo": f8(estimate - zcrit_bonf * se_hc3),
            "ci95_HC3_bonf_hi": f8(estimate + zcrit_bonf * se_hc3),
        }
        contrast_rows.append(record)
        contrast_internal.append(
            {
                "contrast_id": contrast_id,
                "scale_label": scale_label,
                "estimate": estimate,
                "classic_lo": estimate - tcrit * se,
                "classic_hi": estimate + tcrit * se,
                "hc3_lo": estimate - zcrit * se_hc3,
                "hc3_hi": estimate + zcrit * se_hc3,
            }
        )

    restriction = np.zeros((3, 9))
    restriction[0, 2] = 1.0
    restriction[1, 3] = 1.0
    restriction[2, 5] = 1.0
    selected = restriction @ full["beta"]
    q_h = float(selected @ np.linalg.solve(restriction @ full["gram_inverse"] @ restriction.T, selected))
    ss_extra = reduced["rss"] - full["rss"]
    joint_f = (ss_extra / 3.0) / full["s2"]
    p_joint = float(stats.f.sf(joint_f, 3, full["df"]))
    w_hc3 = float(selected @ np.linalg.solve(restriction @ full["covariance_hc3"] @ restriction.T, selected))
    p_w_hc3 = float(stats.chi2.sf(w_hc3, 3))
    assert_close("joint F", joint_f, 41.209104485510920, 4.0e-10)
    assert_close("joint HC3 W", w_hc3, 89.67343789, 4.0e-8)
    if abs(q_h - ss_extra) > 2.0e-7:
        raise RuntimeError("joint quadratic-form and nested-RSS identities differ")
    joint_rows = [
        {
            "hypothesis_id": "SLAG_FLY_SUPERPLASTICIZER_ZERO",
            "q": 3,
            "df1": 3,
            "df2": full["df"],
            "rss_reduced": f8(reduced["rss"]),
            "rss_full": f8(full["rss"]),
            "ss_extra": f8(ss_extra),
            "Q_H": f8(q_h),
            "F": f8(joint_f),
            "p_F": p8(p_joint),
            "W_HC3": f8(w_hc3),
            "p_HC3_asymptotic": p8(p_w_hc3),
        }
    ]

    order_index = (n + 1) // 2
    reference_z = np.asarray([np.sort(z[:, index])[order_index - 1] for index in range(8)])
    expected_reference = np.asarray([272.8, 22.0, 0.0, 185.0, 6.4, 968.0, 779.3, 28.0])
    if not bool(np.array_equal(reference_z, expected_reference)):
        raise RuntimeError(f"lower-marginal-median profile differs: {reference_z}")
    reference_x = np.r_[1.0, reference_z]
    is_observed = bool(np.any(np.all(z == reference_z, axis=1)))
    hull = convex_hull_certificate(np, optimize, z, reference_z)
    muhat = float(reference_x @ full["beta"])
    h0 = float(reference_x @ full["gram_inverse"] @ reference_x)
    se_mean = full["s"] * math.sqrt(h0)
    fcrit_scheffe = float(stats.f.ppf(0.95, full["p"], full["df"]))
    scheffe_multiplier = math.sqrt(full["p"] * fcrit_scheffe)
    se_prediction = full["s"] * math.sqrt(1.0 + h0)
    assert_close("reference fit", muhat, 22.211800983590983, 4.0e-10)
    assert_close("reference leverage", h0, 0.01314956509034074, 2.0e-12)
    if is_observed or hull["in_convex_hull"]:
        raise RuntimeError("reference profile support classification differs")
    reference_rows = [
        {
            "profile_id": "LOWER_MARGINAL_MEDIANS",
            "order_index_one_based": order_index,
            "cement_kg_per_m3": f8(reference_z[0]),
            "blast_furnace_slag_kg_per_m3": f8(reference_z[1]),
            "fly_ash_kg_per_m3": f8(reference_z[2]),
            "water_kg_per_m3": f8(reference_z[3]),
            "superplasticizer_kg_per_m3": f8(reference_z[4]),
            "coarse_aggregate_kg_per_m3": f8(reference_z[5]),
            "fine_aggregate_kg_per_m3": f8(reference_z[6]),
            "age_days": f8(reference_z[7]),
            "is_observed_row": btext(is_observed),
            "in_convex_hull": btext(hull["in_convex_hull"]),
            "muhat_MPa": f8(muhat),
            "h0": f8(h0),
            "se_mean": f8(se_mean),
            "tcrit_95": f8(tcrit),
            "mean_point_lo": f8(muhat - tcrit * se_mean),
            "mean_point_hi": f8(muhat + tcrit * se_mean),
            "scheffe_Fcrit": f8(fcrit_scheffe),
            "scheffe_multiplier": f8(scheffe_multiplier),
            "mean_scheffe_lo": f8(muhat - scheffe_multiplier * se_mean),
            "mean_scheffe_hi": f8(muhat + scheffe_multiplier * se_mean),
            "se_prediction": f8(se_prediction),
            "prediction_lo": f8(muhat - tcrit * se_prediction),
            "prediction_hi": f8(muhat + tcrit * se_prediction),
        }
    ]

    leverage_order = sorted(
        range(n), key=lambda index: (float(full["leverage"][index]), index)
    )
    selector_specs = (
        ("MIN_LEVERAGE", 1, leverage_order[0], 986),
        ("MEDIAN_LOWER_LEVERAGE", n // 2, leverage_order[n // 2 - 1], 592),
        ("MAX_LEVERAGE", n, leverage_order[-1], 67),
    )
    if tuple(index + 1 for _, _, index, _ in selector_specs) != tuple(
        expected for _, _, _, expected in selector_specs
    ):
        raise RuntimeError("full-model leverage selector records differ")
    selector_interval_rows: list[dict[str, object]] = []
    for selector_id, order_rank, index, _ in selector_specs:
        fitted_value = float(full["fitted"][index])
        leverage_value = float(full["leverage"][index])
        selector_se_mean = full["s"] * math.sqrt(leverage_value)
        selector_se_prediction = full["s"] * math.sqrt(1.0 + leverage_value)
        selector_interval_rows.append(
            {
                "selector_id": selector_id,
                "row_id": inputs["row_manifest"][index]["row_id"],
                "source_record": index + 1,
                "order_index_one_based": order_rank,
                "fitted_mpa": f8(fitted_value),
                "h0": f8(leverage_value),
                "se_mean": f8(selector_se_mean),
                "tcrit_95": f8(tcrit),
                "mean_point_lo": f8(fitted_value - tcrit * selector_se_mean),
                "mean_point_hi": f8(fitted_value + tcrit * selector_se_mean),
                "se_prediction": f8(selector_se_prediction),
                "prediction_lo": f8(fitted_value - tcrit * selector_se_prediction),
                "prediction_hi": f8(fitted_value + tcrit * selector_se_prediction),
            }
        )
    assert_close(
        "minimum leverage selector",
        float(full["leverage"][selector_specs[0][2]]),
        0.0021858456716867137,
        4.0e-12,
    )
    assert_close(
        "lower-median leverage selector",
        float(full["leverage"][selector_specs[1][2]]),
        0.0066861303900601051,
        4.0e-12,
    )
    assert_close(
        "maximum leverage selector",
        float(full["leverage"][selector_specs[2][2]]),
        0.041074582668910536,
        4.0e-12,
    )

    inference_token_rows: list[dict[str, object]] = []

    def add_inference_token(
        token_id: str,
        value: object,
        value_type: str,
        unit: str,
        display_format: str,
        source_file: str,
        source_selector: str,
        inference_basis: str,
    ) -> None:
        numeric_value = ""
        text_value = ""
        if value_type in {"integer", "float64"}:
            numeric_value = str(value)
        else:
            text_value = str(value)
        inference_token_rows.append(
            {
                "token_id": token_id,
                "value_type": value_type,
                "numeric_value": numeric_value,
                "text_value": text_value,
                "unit": unit,
                "display_format": display_format,
                "source_file": source_file,
                "source_selector": source_selector,
                "inference_basis": inference_basis,
                "status": "VERIFIED_REPLAY",
            }
        )

    for component, fit in (("FULL", full), ("REDUCED", reduced)):
        selector = f"model_id={fit['model_id']}"
        for suffix, value, value_type, unit, display in (
            ("N", fit["n"], "integer", "rows", "integer"),
            ("P", fit["p"], "integer", "columns", "integer"),
            ("RANK", fit["rank"], "integer", "rank", "integer"),
            ("DF_RESIDUAL", fit["df"], "integer", "df", "integer"),
            ("RSS", f8(fit["rss"]), "float64", "MPa2", "fixed_8"),
            ("S2", f8(fit["s2"]), "float64", "MPa2", "fixed_8"),
            ("S", f8(fit["s"]), "float64", "MPa", "fixed_8"),
        ):
            add_inference_token(
                f"CP01_INF__MODEL__{component}__{suffix}", value, value_type, unit,
                display, "CP01_model_fit.csv", selector, "descriptive_model_fit",
            )
    reduced_tcrit = float(stats.t.ppf(0.975, reduced["df"]))
    for suffix, value, unit in (
        ("T_POINT95_FULL", f8(tcrit), "critical_value"),
        ("T_POINT95_REDUCED", f8(reduced_tcrit), "critical_value"),
        ("T_BONF_M8", f8(tcrit_bonf), "critical_value"),
        ("Z_POINT95", f8(zcrit), "critical_value"),
        ("Z_BONF_M8", f8(zcrit_bonf), "critical_value"),
        ("F_SCHEFFE_P9", f8(fcrit_scheffe), "critical_value"),
        ("SCHEFFE_MULTIPLIER_P9", f8(scheffe_multiplier), "critical_value"),
    ):
        add_inference_token(
            f"CP01_INF__CRIT__{suffix}", value, "float64", unit, "fixed_8",
            "CP01_inference_results.csv", "critical_value", "distribution_quantile",
        )
    coefficient_numeric = (
        ("ESTIMATE", "estimate", "coefficient", "fixed_8", "descriptive_estimate"),
        ("SE_GAUSSIAN", "se_gaussian", "coefficient_se", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("T_GAUSSIAN", "t", "t_statistic", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("DF", "df", "df", "integer", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("P_GAUSSIAN", "p_raw", "p_value", "scientific_or_fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("CI95_GAUSSIAN_LO", "ci95_point_lo", "coefficient", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("CI95_GAUSSIAN_HI", "ci95_point_hi", "coefficient", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("SE_HC3", "se_HC3", "coefficient_se", "fixed_8", "asymptotic_HC3_normal"),
        ("Z_HC3", "z_HC3", "z_statistic", "fixed_8", "asymptotic_HC3_normal"),
        ("P_HC3", "p_HC3", "p_value", "scientific_or_fixed_8", "asymptotic_HC3_normal"),
        ("CI95_HC3_LO", "ci95_HC3_lo", "coefficient", "fixed_8", "asymptotic_HC3_normal"),
        ("CI95_HC3_HI", "ci95_HC3_hi", "coefficient", "fixed_8", "asymptotic_HC3_normal"),
    )
    for row in inference_rows:
        component = "FULL" if row["model_id"] == MODEL_FULL else "REDUCED"
        base = f"CP01_INF__COEF__{component}__{row['term_id']}"
        selector = f"model_id={row['model_id']};term_id={row['term_id']}"
        add_inference_token(
            f"{base}__UNIT", row["unit"], "text", "unit", "text",
            "CP01_inference_coefficients.csv", selector, "metadata",
        )
        for suffix, field, unit, display, basis in coefficient_numeric:
            value_type = "integer" if field == "df" else "float64"
            token_unit = row["unit"] if unit in {"coefficient", "coefficient_se"} else unit
            add_inference_token(
                f"{base}__{suffix}", row[field], value_type, str(token_unit), display,
                "CP01_inference_coefficients.csv", selector, basis,
            )
    contrast_numeric = (
        ("DELTA", "delta", "predictor_increment", "fixed_8", "predefined_contrast"),
        ("ESTIMATE_MPA", "estimate_MPa", "MPa", "fixed_8", "predefined_contrast"),
        ("SE_GAUSSIAN", "se_gaussian", "MPa", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("T_GAUSSIAN", "t", "t_statistic", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("DF", "df", "df", "integer", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("P_RAW", "p_raw", "p_value", "scientific_or_fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("CI95_POINT_LO", "ci95_point_lo", "MPa", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("CI95_POINT_HI", "ci95_point_hi", "MPa", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("P_BONF_M8", "p_bonferroni_m8", "p_value", "scientific_or_fixed_8", "finite_sample_gaussian_Bonferroni_m8"),
        ("CI95_BONF_M8_LO", "ci95_bonf_lo", "MPa", "fixed_8", "finite_sample_gaussian_Bonferroni_m8"),
        ("CI95_BONF_M8_HI", "ci95_bonf_hi", "MPa", "fixed_8", "finite_sample_gaussian_Bonferroni_m8"),
        ("SE_HC3", "se_HC3", "MPa", "fixed_8", "asymptotic_HC3_normal"),
        ("Z_HC3", "z_HC3", "z_statistic", "fixed_8", "asymptotic_HC3_normal"),
        ("P_HC3", "p_HC3", "p_value", "scientific_or_fixed_8", "asymptotic_HC3_normal"),
        ("CI95_HC3_POINT_LO", "ci95_HC3_lo", "MPa", "fixed_8", "asymptotic_HC3_normal"),
        ("CI95_HC3_POINT_HI", "ci95_HC3_hi", "MPa", "fixed_8", "asymptotic_HC3_normal"),
        ("P_HC3_BONF_M8", "p_HC3_bonferroni_m8", "p_value", "scientific_or_fixed_8", "asymptotic_HC3_normal_Bonferroni_m8"),
        ("CI95_HC3_BONF_M8_LO", "ci95_HC3_bonf_lo", "MPa", "fixed_8", "asymptotic_HC3_normal_Bonferroni_m8"),
        ("CI95_HC3_BONF_M8_HI", "ci95_HC3_bonf_hi", "MPa", "fixed_8", "asymptotic_HC3_normal_Bonferroni_m8"),
    )
    for row in contrast_rows:
        base = f"CP01_INF__CONTRAST__{row['contrast_id']}"
        selector = f"contrast_id={row['contrast_id']}"
        add_inference_token(
            f"{base}__DELTA_UNIT", row["delta_unit"], "text", "unit", "text",
            "CP01_inference_contrasts.csv", selector, "metadata",
        )
        for suffix, field, unit, display, basis in contrast_numeric:
            value_type = "integer" if field == "df" else "float64"
            token_unit = row["delta_unit"] if unit == "predictor_increment" else unit
            add_inference_token(
                f"{base}__{suffix}", row[field], value_type, str(token_unit), display,
                "CP01_inference_contrasts.csv", selector, basis,
            )
    joint_field_map = (
        ("Q", "q", "df", "integer", "hypothesis_dimension"),
        ("DF1", "df1", "df", "integer", "finite_sample_gaussian_F"),
        ("DF2", "df2", "df", "integer", "finite_sample_gaussian_F"),
        ("RSS_REDUCED", "rss_reduced", "MPa2", "fixed_8", "nested_model_identity"),
        ("RSS_FULL", "rss_full", "MPa2", "fixed_8", "nested_model_identity"),
        ("SS_EXTRA", "ss_extra", "MPa2", "fixed_8", "nested_model_identity"),
        ("Q_H", "Q_H", "MPa2", "fixed_8", "nested_model_quadratic_form"),
        ("F", "F", "F", "fixed_8", "finite_sample_gaussian_F"),
        ("P_F", "p_F", "p_value", "scientific_or_fixed_8", "finite_sample_gaussian_F"),
        ("W_HC3", "W_HC3", "chi_square", "fixed_8", "asymptotic_HC3_chi_square"),
        ("P_HC3_ASYMPTOTIC", "p_HC3_asymptotic", "p_value", "scientific_or_fixed_8", "asymptotic_HC3_chi_square"),
    )
    joint_row = joint_rows[0]
    joint_base = "CP01_INF__JOINT__SLAG_FLY_SUPERPLASTICIZER_ZERO"
    for suffix, field, unit, display, basis in joint_field_map:
        value_type = "integer" if field in {"q", "df1", "df2"} else "float64"
        add_inference_token(
            f"{joint_base}__{suffix}", joint_row[field], value_type, unit, display,
            "CP01_inference_joint_F.csv",
            "hypothesis_id=SLAG_FLY_SUPERPLASTICIZER_ZERO", basis,
        )
    reference_row = reference_rows[0]
    reference_base = "CP01_INF__REFERENCE__LOWER_MARGINAL_MEDIANS"
    reference_fields = (
        ("ORDER_INDEX_ONE_BASED", "order_index_one_based", "integer", "order_index", "integer", "metadata"),
        ("CEMENT", "cement_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("SLAG", "blast_furnace_slag_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("FLY_ASH", "fly_ash_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("WATER", "water_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("SUPERPLASTICIZER", "superplasticizer_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("COARSE_AGGREGATE", "coarse_aggregate_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("FINE_AGGREGATE", "fine_aggregate_kg_per_m3", "float64", "kg/m^3", "fixed_8", "profile_coordinate"),
        ("AGE", "age_days", "float64", "day", "fixed_8", "profile_coordinate"),
        ("IS_OBSERVED_ROW", "is_observed_row", "boolean", "boolean", "literal", "support_diagnostic"),
        ("IN_CONVEX_HULL", "in_convex_hull", "boolean", "boolean", "literal", "support_diagnostic"),
        ("MUHAT_MPA", "muhat_MPa", "float64", "MPa", "fixed_8", "point_estimate"),
        ("LEVERAGE_H0", "h0", "float64", "dimensionless", "fixed_8", "design_leverage"),
        ("SE_MEAN", "se_mean", "float64", "MPa", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("TCRIT_95", "tcrit_95", "float64", "critical_value", "fixed_8", "finite_sample_gaussian_conditional_on_fixed_X"),
        ("MEAN_POINT_LO", "mean_point_lo", "float64", "MPa", "fixed_8", "finite_sample_gaussian_pointwise"),
        ("MEAN_POINT_HI", "mean_point_hi", "float64", "MPa", "fixed_8", "finite_sample_gaussian_pointwise"),
        ("SCHEFFE_FCRIT", "scheffe_Fcrit", "float64", "critical_value", "fixed_8", "finite_sample_gaussian_Scheffe"),
        ("SCHEFFE_MULTIPLIER", "scheffe_multiplier", "float64", "critical_value", "fixed_8", "finite_sample_gaussian_Scheffe"),
        ("MEAN_SCHEFFE_LO", "mean_scheffe_lo", "float64", "MPa", "fixed_8", "finite_sample_gaussian_Scheffe"),
        ("MEAN_SCHEFFE_HI", "mean_scheffe_hi", "float64", "MPa", "fixed_8", "finite_sample_gaussian_Scheffe"),
        ("SE_PREDICTION", "se_prediction", "float64", "MPa", "fixed_8", "finite_sample_gaussian_new_response"),
        ("PREDICTION_LO", "prediction_lo", "float64", "MPa", "fixed_8", "finite_sample_gaussian_new_response"),
        ("PREDICTION_HI", "prediction_hi", "float64", "MPa", "fixed_8", "finite_sample_gaussian_new_response"),
    )
    for suffix, field, value_type, unit, display, basis in reference_fields:
        add_inference_token(
            f"{reference_base}__{suffix}", reference_row[field], value_type, unit, display,
            "CP01_reference_prediction.csv", "profile_id=LOWER_MARGINAL_MEDIANS", basis,
        )
    add_inference_token(
        "CP01_INF__SELECTOR__ROW_COUNT", 3, "integer", "rows", "integer",
        "CP01_leverage_selector_intervals.csv", "all", "metadata",
    )
    add_inference_token(
        "CP01_INF__SELECTOR__SELECTION_MODEL_ID", MODEL_FULL, "text", "model_id", "text",
        "CP01_leverage_selector_intervals.csv", "all", "metadata",
    )
    for row in selector_interval_rows:
        base = f"CP01_INF__SELECTOR__{row['selector_id']}"
        selector = f"selector_id={row['selector_id']}"
        add_inference_token(
            f"{base}__ROW_ID", row["row_id"], "text", "row_id", "text",
            "CP01_leverage_selector_intervals.csv", selector, "metadata",
        )
        for suffix, field, value_type, unit in (
            ("SOURCE_RECORD", "source_record", "integer", "row"),
            ("ORDER_INDEX_ONE_BASED", "order_index_one_based", "integer", "order_index"),
            ("FITTED_MPA", "fitted_mpa", "float64", "MPa"),
            ("H0", "h0", "float64", "dimensionless"),
            ("SE_MEAN", "se_mean", "float64", "MPa"),
            ("TCRIT_95", "tcrit_95", "float64", "critical_value"),
            ("MEAN_POINT_LO", "mean_point_lo", "float64", "MPa"),
            ("MEAN_POINT_HI", "mean_point_hi", "float64", "MPa"),
            ("SE_PREDICTION", "se_prediction", "float64", "MPa"),
            ("PREDICTION_LO", "prediction_lo", "float64", "MPa"),
            ("PREDICTION_HI", "prediction_hi", "float64", "MPa"),
        ):
            add_inference_token(
                f"{base}__{suffix}", row[field], value_type, unit,
                "integer" if value_type == "integer" else "fixed_8",
                "CP01_leverage_selector_intervals.csv", selector,
                "nominal_pointwise_gaussian_t_after_X_only_leverage_selection",
            )
        add_inference_token(
            f"{base}__SELECTION_USES_RESPONSE", "false", "boolean", "boolean", "literal",
            "CP01_leverage_selector_intervals.csv", selector, "design_only_selection",
        )
        add_inference_token(
            f"{base}__INFERENCE_LABEL",
            "NOMINAL_POINTWISE_GAUSSIAN_T__POST_SELECTION_BY_FULL_MODEL_LEVERAGE__NOT_SIMULTANEOUS",
            "text", "label", "text", "CP01_leverage_selector_intervals.csv", selector,
            "nominal_post_selection_label",
        )
    internal_residual = full["residual"] / (full["s"] * np.sqrt(1.0 - full["leverage"]))
    deleted_s2 = (
        full["rss"] - full["residual"] ** 2 / (1.0 - full["leverage"])
    ) / (full["df"] - 1)
    if not bool(np.all(deleted_s2 > 0.0)):
        raise RuntimeError("deleted-case residual variance is nonpositive")
    deleted_t = full["residual"] / (np.sqrt(deleted_s2) * np.sqrt(1.0 - full["leverage"]))
    deleted_residual = full["residual"] / (1.0 - full["leverage"])
    cook = (
        full["residual"] ** 2
        / (full["p"] * full["s2"])
        * full["leverage"]
        / (1.0 - full["leverage"]) ** 2
    )
    high_h2 = full["leverage"] > 2.0 * full["p"] / n
    high_h3 = full["leverage"] > 3.0 * full["p"] / n
    high_cook = cook > 4.0 / n
    screen_union = high_h2 | high_cook
    expected_counts = (80, 40, 51, 2, 79)
    observed_counts = (
        int(np.sum(high_h2)),
        int(np.sum(high_h3)),
        int(np.sum(np.abs(deleted_t) > 2.0)),
        int(np.sum(np.abs(deleted_t) > 3.0)),
        int(np.sum(high_cook)),
    )
    if observed_counts != expected_counts:
        raise RuntimeError(f"diagnostic threshold counts differ: {observed_counts}")
    max_h = max(range(n), key=lambda index: (float(full["leverage"][index]), -index))
    max_t = max(range(n), key=lambda index: (abs(float(deleted_t[index])), -index))
    max_cook = max(range(n), key=lambda index: (float(cook[index]), -index))
    if (max_h + 1, max_t + 1, max_cook + 1) != (67, 382, 611):
        raise RuntimeError("diagnostic extreme row IDs differ")
    assert_close("maximum leverage", float(full["leverage"][max_h]), 0.041074582668910536, 4.0e-12)
    assert_close("maximum abs deleted t", abs(float(deleted_t[max_t])), 3.34637213, 4.0e-8)
    assert_close("maximum Cook", float(cook[max_cook]), 0.02699698, 4.0e-8)

    observation_rows = []
    row_ids = [row["row_id"] for row in inputs["row_manifest"]]
    for index in range(n):
        observation_rows.append(
            {
                "row_id": row_ids[index],
                "source_record": index + 1,
                "source_line": index + 2,
                "fitted_mpa": f8(float(full["fitted"][index])),
                "residual_mpa": f8(float(full["residual"][index])),
                "leverage": f8(float(full["leverage"][index])),
                "internal_standardized_residual": f8(float(internal_residual[index])),
                "deleted_studentized_residual": f8(float(deleted_t[index])),
                "deleted_residual_mpa": f8(float(deleted_residual[index])),
                "cook_distance": f8(float(cook[index])),
                "leverage_screen_2p_over_n": btext(bool(high_h2[index])),
                "cook_screen_4_over_n": btext(bool(high_cook[index])),
                "screen_union": btext(bool(screen_union[index])),
            }
        )

    residual_bin_rows, residual_bin_internal = residual_bins(np, full)
    assert_close("first residual-bin RMS", residual_bin_internal[0]["rms_residual_mpa"], 7.82705550, 4.0e-8)
    assert_close("last residual-bin RMS", residual_bin_internal[-1]["rms_residual_mpa"], 13.98223909, 4.0e-8)

    aux = fit_model(np, x_full, full["residual"] ** 2, "KOENKER_AUX_FULL")
    koenker_r2 = aux["r2"]
    koenker_lm = n * koenker_r2
    koenker_p = float(stats.chi2.sf(koenker_lm, 8))
    aux_log = fit_model(np, x_log, log_fit["residual"] ** 2, "KOENKER_AUX_LOG")
    koenker_log_r2 = aux_log["r2"]
    koenker_log_lm = n * koenker_log_r2
    koenker_log_p = float(stats.chi2.sf(koenker_log_lm, 8))
    assert_close("Koenker full LM", koenker_lm, 137.19625978, 4.0e-8)
    assert_close("Koenker log LM", koenker_log_lm, 101.83753665, 4.0e-8)

    leverage_only = high_h2 & ~high_cook
    cook_only = high_cook & ~high_h2
    intersection = high_h2 & high_cook
    if (int(sum(leverage_only)), int(sum(cook_only)), int(sum(intersection)), int(sum(screen_union))) != (44, 43, 36, 123):
        raise RuntimeError("union-screen set algebra differs")
    retained = ~screen_union
    screen_full = fit_model(np, x_full[retained], y[retained], MODEL_SCREEN_FULL)
    screen_reduced = fit_model(np, x_reduced[retained], y[retained], MODEL_SCREEN_REDUCED)
    assert_close("screen full RSS", screen_full["rss"], 55945.99928758, 4.0e-7)
    assert_close("screen full condition", screen_full["kappa_scaled"], 9.47005812, 4.0e-8)
    screen_ss_extra = screen_reduced["rss"] - screen_full["rss"]
    screen_f = (screen_ss_extra / 3.0) / screen_full["s2"]
    screen_p = float(stats.f.sf(screen_f, 3, screen_full["df"]))
    assert_close("screen block F", screen_f, 59.65025761, 4.0e-8)
    if not math.isclose(screen_p, 3.6037000926326634e-35, rel_tol=5.0e-12, abs_tol=0.0):
        raise RuntimeError(f"screen block nominal p-value differs: {screen_p:.17e}")
    screen_prediction = x_full @ screen_full["beta"]
    prediction_delta = screen_prediction - full["fitted"]

    def prediction_metrics(mask: Any) -> dict[str, float | int]:
        primary_error = y[mask] - full["fitted"][mask]
        refit_error = y[mask] - screen_prediction[mask]
        delta = prediction_delta[mask]
        return {
            "n": int(np.sum(mask)),
            "primary_rmse": math.sqrt(float(np.mean(primary_error ** 2))),
            "refit_rmse": math.sqrt(float(np.mean(refit_error ** 2))),
            "primary_mae": float(np.mean(np.abs(primary_error))),
            "refit_mae": float(np.mean(np.abs(refit_error))),
            "delta_rms": math.sqrt(float(np.mean(delta ** 2))),
            "delta_mae": float(np.mean(np.abs(delta))),
            "delta_max": float(np.max(np.abs(delta))),
        }

    prediction_by_subset = {
        "SCREEN_COMPLEMENT": prediction_metrics(retained),
        "SCREEN_UNION": prediction_metrics(screen_union),
        "ALL_ROWS": prediction_metrics(np.ones(n, dtype=bool)),
    }
    assert_close("screen retained primary RMSE", float(prediction_by_subset["SCREEN_COMPLEMENT"]["primary_rmse"]), 8.77914108, 4.0e-8)
    assert_close("screen retained refit RMSE", float(prediction_by_subset["SCREEN_COMPLEMENT"]["refit_rmse"]), 7.85381875, 4.0e-8)
    assert_close("screen flagged refit RMSE", float(prediction_by_subset["SCREEN_UNION"]["refit_rmse"]), 27.46931114, 4.0e-8)
    assert_close("screen max prediction delta", float(prediction_by_subset["ALL_ROWS"]["delta_max"]), 30.44921381, 4.0e-8)
    reference_screen = float(reference_x @ screen_full["beta"])

    full_loo = analytic_loo(np, full)
    reduced_loo = analytic_loo(np, reduced)
    log_loo = analytic_loo(np, log_fit)
    full_loo["min_training_rank"] = verify_explicit_loo(np, full)
    reduced_loo["min_training_rank"] = verify_explicit_loo(np, reduced)
    log_loo["min_training_rank"] = log_fit["p"]
    loo_by_model = {MODEL_FULL: full_loo, MODEL_REDUCED: reduced_loo, MODEL_LOG: log_loo}
    fit_by_model = {MODEL_FULL: full, MODEL_REDUCED: reduced, MODEL_LOG: log_fit}
    loppo_by_model: dict[str, dict[str, Any]] = {}
    profile_rows: list[dict[str, object]] = []
    for model_id in (MODEL_FULL, MODEL_REDUCED, MODEL_LOG):
        metrics, rows = loppo(
            np,
            fit_by_model[model_id],
            inputs["profile_members"],
            loo_by_model[model_id],
            inputs["row_manifest"],
        )
        loppo_by_model[model_id] = metrics
        profile_rows.extend(rows)
    expected_validation = {
        MODEL_FULL: (109.61075721, 109.90155878),
        MODEL_REDUCED: (122.01948455, 122.24662163),
        MODEL_LOG: (51.67434680, 51.77111417),
    }
    for model_id, (expected_loo, expected_loppo) in expected_validation.items():
        assert_close(f"{model_id} LOOCV MSE", loo_by_model[model_id]["mse"], expected_loo, 4.0e-8)
        assert_close(f"{model_id} LOPPO MSE", loppo_by_model[model_id]["mse"], expected_loppo, 4.0e-8)
    if len(profile_rows) != 3090:
        raise RuntimeError("LOPPO detail row count differs")

    loocv_rows: list[dict[str, object]] = []
    for method, source in (("ANALYTIC_LOOCV", loo_by_model), ("EXACT_LOPPO", loppo_by_model)):
        for model_id in (MODEL_FULL, MODEL_REDUCED, MODEL_LOG):
            metrics = source[model_id]
            loocv_rows.append(
                {
                    "method_id": method,
                    "model_id": model_id,
                    "n": n,
                    "press": f8(metrics["press"]),
                    "mse": f8(metrics["mse"]),
                    "rmse_mpa": f8(metrics["rmse"]),
                    "mae_mpa": f8(metrics["mae"]),
                    "min_training_rank": metrics["min_training_rank"],
                    "seed": "null",
                }
            )

    data_summary_rows: list[dict[str, object]] = []
    data_units = ("kg/m^3",) * 7 + ("day", "MPa")
    for index, name in enumerate(CLEAN_NAMES):
        column = data[:, index]
        quartiles = np.quantile(column, [0.25, 0.5, 0.75], method="linear")
        data_summary_rows.append(
            {
                "variable_id": name,
                "role": "response" if index == 8 else "predictor",
                "unit": data_units[index],
                "n": n,
                "missing": 0,
                "minimum": f8(float(np.min(column))),
                "q1_type7": f8(float(quartiles[0])),
                "median_type7": f8(float(quartiles[1])),
                "q3_type7": f8(float(quartiles[2])),
                "mean": f8(float(np.mean(column))),
                "sample_sd": f8(float(np.std(column, ddof=1))),
                "maximum": f8(float(np.max(column))),
            }
        )

    model_fit_rows = []
    for fit in (full, reduced):
        model_fit_rows.append(
            {
                "model_id": fit["model_id"], "n": fit["n"], "p": fit["p"], "rank": fit["rank"], "df": fit["df"],
                "rss": f8(fit["rss"]), "s2_unbiased": f8(fit["s2"]), "s_residual_mpa": f8(fit["s"]),
                "sigma2_mle": f8(fit["sigma2_mle"]), "rmse_in_sample_mpa": f8(fit["rmse_in_sample"]),
                "r2": f8(fit["r2"]), "adjusted_r2": f8(fit["adjusted_r2"]),
                "kappa2_raw": f8(fit["kappa_raw"]), "kappa2_scaled": f8(fit["kappa_scaled"]),
            }
        )

    anova_rows = []
    full_overall_f = (full["ssr"] / (full["p"] - 1)) / full["s2"]
    reduced_overall_f = (reduced["ssr"] / (reduced["p"] - 1)) / reduced["s2"]
    for comparison, kind, df_value, ss, ms, f_value, p_value in (
        ("CENTERED_TOTAL", "TOTAL", n - 1, full["sst"], full["sst"] / (n - 1), None, None),
        (MODEL_FULL, "REGRESSION", full["p"] - 1, full["ssr"], full["ssr"] / (full["p"] - 1), full_overall_f, float(stats.f.sf(full_overall_f, full["p"] - 1, full["df"]))),
        (MODEL_FULL, "RESIDUAL", full["df"], full["rss"], full["s2"], None, None),
        (MODEL_REDUCED, "REGRESSION", reduced["p"] - 1, reduced["ssr"], reduced["ssr"] / (reduced["p"] - 1), reduced_overall_f, float(stats.f.sf(reduced_overall_f, reduced["p"] - 1, reduced["df"]))),
        (MODEL_REDUCED, "RESIDUAL", reduced["df"], reduced["rss"], reduced["s2"], None, None),
        ("FULL_VS_REDUCED_SFP", "EXTRA", 3, ss_extra, ss_extra / 3.0, joint_f, p_joint),
    ):
        anova_rows.append(
            {
                "comparison_id": comparison,
                "row_kind": kind,
                "df": df_value,
                "ss": f8(ss),
                "ms": f8(ms),
                "F": "NA" if f_value is None else f8(f_value),
                "p_value": "NA" if p_value is None else p8(p_value),
            }
        )

    vif_values = np.diag(np.linalg.inv(np.corrcoef(z, rowvar=False)))
    expected_vif = (7.48894379, 7.27696310, 6.17063432, 7.00395670, 2.96377575, 5.07461700, 7.00508141, 1.11836652)
    for term, observed, expected in zip(TERM_IDS[1:], vif_values, expected_vif):
        assert_close(f"VIF {term}", float(observed), expected, 4.0e-8)
    conditioning_rows = []
    for fit in (full, reduced, log_fit, screen_full, screen_reduced):
        conditioning_rows.append(
            {
                "row_kind": "MODEL", "model_id": fit["model_id"], "term_id": "NA",
                "n": fit["n"], "p": fit["p"], "rank": fit["rank"],
                "kappa2_raw": f8(fit["kappa_raw"]), "kappa2_scaled": f8(fit["kappa_scaled"]),
                "kappa2_xtx_scaled": f8(fit["kappa_scaled"] ** 2), "vif": "NA",
            }
        )
    for term, vif in zip(TERM_IDS[1:], vif_values):
        conditioning_rows.append(
            {
                "row_kind": "VIF", "model_id": MODEL_FULL, "term_id": term,
                "n": "NA", "p": "NA", "rank": "NA", "kappa2_raw": "NA", "kappa2_scaled": "NA",
                "kappa2_xtx_scaled": "NA", "vif": f8(float(vif)),
            }
        )

    cook_order = sorted(range(n), key=lambda index: (-float(cook[index]), index))
    cook_rank = {index: rank + 1 for rank, index in enumerate(cook_order)}
    deleted_rows: list[dict[str, object]] = []
    maximum_standardized_shift = (-1.0, -1, -1, 0.0)
    any_sign_reversal = False
    for index in cook_order:
        delta = full["gram_inverse"] @ x_full[index] * full["residual"][index] / (1.0 - full["leverage"][index])
        deleted_beta = full["beta"] - delta
        any_sign_reversal = any_sign_reversal or bool(np.any(np.sign(full["beta"]) != np.sign(deleted_beta)))
        for term_index, term_id in enumerate(TERM_IDS):
            standardized = float(delta[term_index] / classic_se[term_index])
            if abs(standardized) > maximum_standardized_shift[0]:
                maximum_standardized_shift = (abs(standardized), index, term_index, standardized)
            deleted_rows.append(
                {
                    "row_id": row_ids[index],
                    "source_record": index + 1,
                    "source_line": index + 2,
                    "cook_rank": cook_rank[index],
                    "term_id": term_id,
                    "estimate_full": f8(float(full["beta"][term_index])),
                    "estimate_deleted": f8(float(deleted_beta[term_index])),
                    "delta_full_minus_deleted": f8(float(delta[term_index])),
                    "delta_in_primary_se": f8(standardized),
                }
            )
    if (maximum_standardized_shift[1] + 1, TERM_IDS[maximum_standardized_shift[2]]) != (225, "WATER"):
        raise RuntimeError("maximum deleted-case coefficient shift identity differs")
    assert_close("maximum deleted standardized shift", maximum_standardized_shift[0], 0.44057951, 4.0e-8)
    if any_sign_reversal:
        raise RuntimeError("unexpected deleted-case coefficient sign reversal")

    screen_rows: list[dict[str, object]] = []

    def add_screen(metric_id: str, model_id: str, subset_id: str, term_id: str, fit: dict[str, Any], value: object, unit: str) -> None:
        numeric = ""
        text = ""
        if isinstance(value, bool):
            text = btext(value)
        elif isinstance(value, str):
            text = value
        elif isinstance(value, int):
            numeric = str(value)
        else:
            numeric = p8(float(value)) if unit == "p_value" else f8(float(value))
        if metric_id == "BLOCK_SFP_P_F":
            text = "NOMINAL_POST_SELECTION_F__EXPLORATORY_SENSITIVITY_ONLY"
        screen_rows.append(
            {
                "metric_id": metric_id, "model_id": model_id, "subset_id": subset_id, "term_id": term_id,
                "n": fit["n"], "p": fit["p"], "rank": fit["rank"], "df": fit["df"],
                "numeric_value": numeric, "text_value": text, "unit": unit,
            }
        )

    for metric_id, value in (
        ("LEVERAGE_ONLY_COUNT", int(sum(leverage_only))), ("COOK_ONLY_COUNT", int(sum(cook_only))),
        ("INTERSECTION_COUNT", int(sum(intersection))), ("UNION_COUNT", int(sum(screen_union))),
        ("RETAINED_COUNT", int(sum(retained))),
    ):
        add_screen(metric_id, MODEL_FULL, "ALL_ROWS", "NA", full, value, "rows")
    for fit in (screen_full, screen_reduced):
        for metric_id, value, unit in (
            ("RSS", fit["rss"], "MPa2"), ("S2", fit["s2"], "MPa2"), ("S", fit["s"], "MPa"),
            ("R2", fit["r2"], "dimensionless"), ("KAPPA2_SCALED", fit["kappa_scaled"], "dimensionless"),
        ):
            add_screen(metric_id, fit["model_id"], "SCREEN_COMPLEMENT", "NA", fit, value, unit)
    for term_index, term_id in enumerate(TERM_IDS):
        add_screen("COEFFICIENT_ESTIMATE", MODEL_SCREEN_FULL, "SCREEN_COMPLEMENT", term_id, screen_full, float(screen_full["beta"][term_index]), UNITS[term_index])
        add_screen("COEFFICIENT_DELTA_FROM_PRIMARY", MODEL_SCREEN_FULL, "SCREEN_COMPLEMENT", term_id, screen_full, float(screen_full["beta"][term_index] - full["beta"][term_index]), UNITS[term_index])
        add_screen("COEFFICIENT_DELTA_IN_PRIMARY_SE", MODEL_SCREEN_FULL, "SCREEN_COMPLEMENT", term_id, screen_full, float((screen_full["beta"][term_index] - full["beta"][term_index]) / classic_se[term_index]), "primary_SE")
    for metric_id, value, unit in (
        ("BLOCK_SFP_SS_EXTRA", screen_ss_extra, "MPa2"), ("BLOCK_SFP_F", screen_f, "F"),
        ("BLOCK_SFP_DF1", 3, "df"), ("BLOCK_SFP_DF2", screen_full["df"], "df"),
        ("BLOCK_SFP_P_F", screen_p, "p_value"),
    ):
        add_screen(metric_id, MODEL_SCREEN_FULL, "SCREEN_COMPLEMENT", "SLAG_FLY_ASH_SUPERPLASTICIZER", screen_full, value, unit)
    screen_block_selector = (
        f"model_id={MODEL_SCREEN_FULL};subset_id=SCREEN_COMPLEMENT;"
        "term_id=SLAG_FLY_ASH_SUPERPLASTICIZER"
    )
    for suffix, metric_id, value, value_type, unit, display in (
        ("SS_EXTRA", "BLOCK_SFP_SS_EXTRA", f8(screen_ss_extra), "float64", "MPa2", "fixed_8"),
        ("F", "BLOCK_SFP_F", f8(screen_f), "float64", "F", "fixed_8"),
        ("DF1", "BLOCK_SFP_DF1", 3, "integer", "df", "integer"),
        ("DF2", "BLOCK_SFP_DF2", screen_full["df"], "integer", "df", "integer"),
        ("P_F_NOMINAL", "BLOCK_SFP_P_F", p8(screen_p), "float64", "p_value", "scientific_8"),
    ):
        add_inference_token(
            f"CP01_INF__SENSITIVITY__UNION_SCREEN__BLOCK_SFP__{suffix}",
            value,
            value_type,
            unit,
            display,
            "CP01_screen_sensitivity.csv",
            f"metric_id={metric_id};{screen_block_selector}",
            "nominal_post_selection_F__response_dependent_screen__not_exact",
        )
    add_inference_token(
        "CP01_INF__SENSITIVITY__UNION_SCREEN__BLOCK_SFP__INFERENCE_LABEL",
        "NOMINAL_POST_SELECTION_F__EXPLORATORY_SENSITIVITY_ONLY",
        "text",
        "label",
        "text",
        "CP01_screen_sensitivity.csv",
        f"metric_id=BLOCK_SFP_P_F;{screen_block_selector}",
        "nominal_post_selection_label",
    )
    inference_token_rows.sort(key=lambda row: str(row["token_id"]))
    if len(inference_token_rows) != 461 or len(
        {str(row["token_id"]) for row in inference_token_rows}
    ) != len(inference_token_rows):
        raise RuntimeError(
            f"CP01 inference token inventory differs: {len(inference_token_rows)}"
        )
    block_p_rows = [row for row in screen_rows if row["metric_id"] == "BLOCK_SFP_P_F"]
    if len(block_p_rows) != 1 or block_p_rows[0]["numeric_value"] != p8(screen_p):
        raise RuntimeError("union-screen nominal p-value serialization differs")
    if block_p_rows[0]["text_value"] != "NOMINAL_POST_SELECTION_F__EXPLORATORY_SENSITIVITY_ONLY":
        raise RuntimeError("union-screen nominal post-selection label differs")
    for subset_id, metrics in prediction_by_subset.items():
        mask_fit = full if subset_id == "ALL_ROWS" else screen_full
        for metric_id, key, unit in (
            ("PRIMARY_RMSE", "primary_rmse", "MPa"), ("REFIT_RMSE", "refit_rmse", "MPa"),
            ("PRIMARY_MAE", "primary_mae", "MPa"), ("REFIT_MAE", "refit_mae", "MPa"),
            ("PREDICTION_DELTA_RMS", "delta_rms", "MPa"), ("PREDICTION_DELTA_MAE", "delta_mae", "MPa"),
            ("PREDICTION_DELTA_MAX_ABS", "delta_max", "MPa"),
        ):
            add_screen(metric_id, MODEL_SCREEN_FULL, subset_id, "NA", mask_fit, metrics[key], unit)
    add_screen("REFERENCE_PROFILE_PRIMARY_MUHAT", MODEL_FULL, "ALL_ROWS", "NA", full, muhat, "MPa")
    add_screen("REFERENCE_PROFILE_REFIT_MUHAT", MODEL_SCREEN_FULL, "SCREEN_COMPLEMENT", "NA", screen_full, reference_screen, "MPa")
    add_screen("REFERENCE_PROFILE_DELTA", MODEL_SCREEN_FULL, "SCREEN_COMPLEMENT", "NA", screen_full, reference_screen - muhat, "MPa")

    model_sensitivity_rows = []
    sensitivity_fits = (full, reduced, log_fit, screen_full)
    for fit in sensitivity_fits:
        if fit["model_id"] == MODEL_SCREEN_FULL:
            loo_metrics = loppo_metrics = None
            fit_subset = "SCREEN_COMPLEMENT"
        else:
            loo_metrics = loo_by_model[fit["model_id"]]
            loppo_metrics = loppo_by_model[fit["model_id"]]
            fit_subset = "ALL_ROWS"
        model_sensitivity_rows.append(
            {
                "model_id": fit["model_id"], "fit_subset": fit_subset, "n_fit": fit["n"], "p": fit["p"],
                "rank": fit["rank"], "df": fit["df"], "rss": f8(fit["rss"]), "s2": f8(fit["s2"]),
                "s": f8(fit["s"]), "r2": f8(fit["r2"]), "kappa2_scaled": f8(fit["kappa_scaled"]),
                "loocv_press": "NA" if loo_metrics is None else f8(loo_metrics["press"]),
                "loocv_mse": "NA" if loo_metrics is None else f8(loo_metrics["mse"]),
                "loocv_rmse_mpa": "NA" if loo_metrics is None else f8(loo_metrics["rmse"]),
                "loocv_mae_mpa": "NA" if loo_metrics is None else f8(loo_metrics["mae"]),
                "loppo_press": "NA" if loppo_metrics is None else f8(loppo_metrics["press"]),
                "loppo_mse": "NA" if loppo_metrics is None else f8(loppo_metrics["mse"]),
                "loppo_rmse_mpa": "NA" if loppo_metrics is None else f8(loppo_metrics["rmse"]),
                "loppo_mae_mpa": "NA" if loppo_metrics is None else f8(loppo_metrics["mae"]),
            }
        )

    diagnostic_tokens: list[dict[str, object]] = []

    def add_token(token_id: str, value: object, unit: str = "dimensionless") -> None:
        if isinstance(value, bool):
            value_type, numeric, text, display = "boolean", "", btext(value), "boolean"
        elif value is None:
            value_type, numeric, text, display = "null", "", "null", "literal"
        elif isinstance(value, int):
            value_type, numeric, text, display = "integer", str(value), "", "integer"
        elif isinstance(value, str):
            value_type, numeric, text, display = "text", "", value, "text"
        else:
            numeric_value = float(value)
            use_scientific = unit == "p_value" and numeric_value < 1.0e-4
            value_type = "float64"
            numeric = e8(numeric_value) if use_scientific else f8(numeric_value)
            text = ""
            display = "scientific_8" if use_scientific else "fixed_8"
        diagnostic_tokens.append(
            {
                "token_id": token_id, "value_type": value_type, "numeric_value": numeric,
                "text_value": text, "unit": unit, "display_format": display, "status": "VERIFIED_REPLAY",
            }
        )

    for suffix, value, unit in (
        ("N", n, "rows"), ("P", full["p"], "columns"), ("RANK", full["rank"], "rank"),
        ("DF_RESIDUAL", full["df"], "df"), ("RSS", full["rss"], "MPa2"), ("S2", full["s2"], "MPa2"),
        ("S", full["s"], "MPa"), ("R2", full["r2"], "dimensionless"),
        ("RMSE_IN_SAMPLE", full["rmse_in_sample"], "MPa"), ("MAE_IN_SAMPLE", full["mae_in_sample"], "MPa"),
    ):
        add_token(f"CP01_DIAG__MODEL__FULL__{suffix}", value, unit)
    for suffix, value, unit in (
        ("R2_AUX", koenker_r2, "dimensionless"), ("LM", koenker_lm, "chi_square"),
        ("DF", 8, "df"), ("P_ASYMPTOTIC", koenker_p, "p_value"),
    ):
        add_token(f"CP01_DIAG__KOENKER__FULL__{suffix}", value, unit)
    for index, record in enumerate(residual_bin_internal, start=1):
        for suffix, key, unit in (
            ("COUNT", "count", "rows"), ("BOUNDARY_LO", "boundary_lo", "MPa"),
            ("BOUNDARY_HI", "boundary_hi", "MPa"), ("FITTED_MIN", "fitted_min", "MPa"),
            ("FITTED_MAX", "fitted_max", "MPa"), ("MEAN_RESIDUAL_MPA", "mean_residual_mpa", "MPa"),
            ("RMS_RESIDUAL_MPA", "rms_residual_mpa", "MPa"),
        ):
            add_token(f"CP01_DIAG__RESIDUAL_BIN__B{index:02d}__{suffix}", record[key], unit)
    for term_index, term_id in enumerate(TERM_IDS):
        base = f"CP01_DIAG__HC3__FULL__{term_id}"
        add_token(base + "__ESTIMATE", float(full["beta"][term_index]), UNITS[term_index])
        add_token(base + "__SE_GAUSSIAN", float(classic_se[term_index]), UNITS[term_index])
        add_token(base + "__SE_HC3", float(hc3_se[term_index]), UNITS[term_index])
        add_token(base + "__RATIO_TO_GAUSSIAN", float(ratios[term_index]))
    add_token("CP01_DIAG__HC3__BLOCK_SFP__W", w_hc3, "chi_square")
    add_token("CP01_DIAG__HC3__BLOCK_SFP__DF", 3, "df")
    add_token("CP01_DIAG__HC3__BLOCK_SFP__P_ASYMPTOTIC", p_w_hc3, "p_value")
    for label, fit in (("FULL", full), ("REDUCED", reduced), ("LOG_AGE", log_fit)):
        add_token(f"CP01_DIAG__CONDITION__{label}__KAPPA2_RAW", fit["kappa_raw"])
        add_token(f"CP01_DIAG__CONDITION__{label}__KAPPA2_SCALED", fit["kappa_scaled"])
        add_token(f"CP01_DIAG__CONDITION__{label}__KAPPA2_XTX_SCALED", fit["kappa_scaled"] ** 2)
    for term_id, vif in zip(TERM_IDS[1:], vif_values):
        add_token(f"CP01_DIAG__VIF__FULL__{term_id}__VALUE", float(vif))
    influence_scalars = (
        ("MEAN_LEVERAGE_P_OVER_N", full["p"] / n), ("THRESHOLD_H_2P_OVER_N", 2 * full["p"] / n),
        ("THRESHOLD_H_3P_OVER_N", 3 * full["p"] / n), ("THRESHOLD_COOK_4_OVER_N", 4 / n),
        ("COUNT_H_GT_2P_OVER_N", observed_counts[0]), ("COUNT_H_GT_3P_OVER_N", observed_counts[1]),
        ("COUNT_ABS_T_GT_2", observed_counts[2]), ("COUNT_ABS_T_GT_3", observed_counts[3]),
        ("COUNT_COOK_GT_4_OVER_N", observed_counts[4]), ("COUNT_COOK_GT_1", int(np.sum(cook > 1))),
    )
    for suffix, value in influence_scalars:
        add_token(f"CP01_DIAG__INFLUENCE__{suffix}", value)
    selectors = (
        ("TOP_LEVERAGE", sorted(range(n), key=lambda i: (-float(full["leverage"][i]), i))[:5]),
        ("TOP_ABS_T", sorted(range(n), key=lambda i: (-abs(float(deleted_t[i])), i))[:5]),
        ("TOP_COOK", cook_order[:5]),
    )
    for label, indexes in selectors:
        for rank_index, index in enumerate(indexes, start=1):
            base = f"CP01_DIAG__INFLUENCE__{label}__R{rank_index:02d}"
            add_token(base + "__ROW_ID", row_ids[index], "row_id")
            add_token(base + "__SOURCE_RECORD", index + 1, "record")
            add_token(base + "__SOURCE_LINE", index + 2, "line")
            add_token(base + "__LEVERAGE", float(full["leverage"][index]))
            add_token(base + "__T_DELETED", float(deleted_t[index]))
            add_token(base + "__COOK", float(cook[index]))
    max_shift_index, max_shift_term = maximum_standardized_shift[1], maximum_standardized_shift[2]
    max_shift_delta = full["gram_inverse"] @ x_full[max_shift_index] * full["residual"][max_shift_index] / (1.0 - full["leverage"][max_shift_index])
    max_shift_deleted_beta = full["beta"] - max_shift_delta
    add_token("CP01_DIAG__DELETE_ONE__MAX_STANDARDIZED_COEF_SHIFT__ROW_ID", row_ids[max_shift_index], "row_id")
    add_token("CP01_DIAG__DELETE_ONE__MAX_STANDARDIZED_COEF_SHIFT__TERM", TERM_IDS[max_shift_term], "term_id")
    add_token("CP01_DIAG__DELETE_ONE__MAX_STANDARDIZED_COEF_SHIFT__VALUE", maximum_standardized_shift[0], "primary_SE")
    add_token("CP01_DIAG__DELETE_ONE__MAX_STANDARDIZED_COEF_SHIFT__FULL_ESTIMATE", float(full["beta"][max_shift_term]), UNITS[max_shift_term])
    add_token("CP01_DIAG__DELETE_ONE__MAX_STANDARDIZED_COEF_SHIFT__DELETED_ESTIMATE", float(max_shift_deleted_beta[max_shift_term]), UNITS[max_shift_term])
    add_token("CP01_DIAG__DELETE_ONE__MAX_STANDARDIZED_COEF_SHIFT__FULL_MINUS_DELETED", float(max_shift_delta[max_shift_term]), UNITS[max_shift_term])
    add_token("CP01_DIAG__DELETE_ONE__ANY_COEF_SIGN_REVERSAL", any_sign_reversal)
    max_cook_delta = full["gram_inverse"] @ x_full[max_cook] * full["residual"][max_cook] / (1.0 - full["leverage"][max_cook])
    add_token("CP01_DIAG__DELETE_ONE__MAX_COOK_ROW__AGE_FULL", float(full["beta"][-1]), "MPa_per_day")
    add_token("CP01_DIAG__DELETE_ONE__MAX_COOK_ROW__AGE_DELETED", float(full["beta"][-1] - max_cook_delta[-1]), "MPa_per_day")

    for suffix, value in (
        ("LEVERAGE_ONLY_COUNT", int(sum(leverage_only))), ("COOK_ONLY_COUNT", int(sum(cook_only))),
        ("INTERSECTION_COUNT", int(sum(intersection))), ("UNION_COUNT", int(sum(screen_union))),
        ("RETAINED_COUNT", int(sum(retained))),
    ):
        add_token(f"CP01_DIAG__SCREEN__{suffix}", value, "rows")
    for label, fit in (("FULL_REFIT", screen_full), ("REDUCED_REFIT", screen_reduced)):
        for suffix, value, unit in (
            ("P", fit["p"], "columns"), ("RANK", fit["rank"], "rank"), ("DF_RESIDUAL", fit["df"], "df"),
            ("RSS", fit["rss"], "MPa2"), ("S2", fit["s2"], "MPa2"), ("S", fit["s"], "MPa"),
            ("R2_ON_RETAINED", fit["r2"], "dimensionless"), ("KAPPA2_SCALED", fit["kappa_scaled"], "dimensionless"),
        ):
            add_token(f"CP01_DIAG__SCREEN__{label}__{suffix}", value, unit)
    for suffix, value, unit in (
        ("SS_EXTRA", screen_ss_extra, "MPa2"), ("F", screen_f, "F"), ("DF1", 3, "df"),
        ("DF2", screen_full["df"], "df"), ("P_F", screen_p, "p_value"),
    ):
        add_token(f"CP01_DIAG__SCREEN__BLOCK_SFP__{suffix}", value, unit)
    screen_deltas_in_se = (screen_full["beta"] - full["beta"]) / classic_se
    for term_index, term_id in enumerate(TERM_IDS):
        base = f"CP01_DIAG__SCREEN__FULL_REFIT__COEF__{term_id}"
        add_token(base + "__ESTIMATE", float(screen_full["beta"][term_index]), UNITS[term_index])
        add_token(base + "__DELTA_FROM_PRIMARY", float(screen_full["beta"][term_index] - full["beta"][term_index]), UNITS[term_index])
        add_token(base + "__DELTA_IN_PRIMARY_SE", float(screen_deltas_in_se[term_index]), "primary_SE")
    for subset_id, metrics in prediction_by_subset.items():
        for suffix, key, unit in (
            ("N", "n", "rows"), ("PRIMARY_RMSE", "primary_rmse", "MPa"), ("REFIT_RMSE", "refit_rmse", "MPa"),
            ("PRIMARY_MAE", "primary_mae", "MPa"), ("REFIT_MAE", "refit_mae", "MPa"),
            ("PREDICTION_DELTA_RMS", "delta_rms", "MPa"), ("PREDICTION_DELTA_MAE", "delta_mae", "MPa"),
            ("PREDICTION_DELTA_MAX_ABS", "delta_max", "MPa"),
        ):
            add_token(f"CP01_DIAG__SCREEN__PREDICTION__{subset_id}__{suffix}", metrics[key], unit)
    add_token("CP01_DIAG__SCREEN__REFERENCE_PROFILE__PRIMARY_MUHAT_MPA", muhat, "MPa")
    add_token("CP01_DIAG__SCREEN__REFERENCE_PROFILE__REFIT_MUHAT_MPA", reference_screen, "MPa")
    add_token("CP01_DIAG__SCREEN__REFERENCE_PROFILE__DELTA_MPA", reference_screen - muhat, "MPa")
    max_screen_term = int(np.argmax(np.abs(screen_deltas_in_se)))
    add_token("CP01_DIAG__SCREEN__MAX_ABS_COEF_DELTA_IN_PRIMARY_SE", abs(float(screen_deltas_in_se[max_screen_term])), "primary_SE")
    add_token("CP01_DIAG__SCREEN__MAX_ABS_COEF_DELTA_TERM", TERM_IDS[max_screen_term], "term_id")

    log_internal = log_fit["residual"] / (log_fit["s"] * np.sqrt(1.0 - log_fit["leverage"]))
    log_deleted_s2 = (log_fit["rss"] - log_fit["residual"] ** 2 / (1.0 - log_fit["leverage"])) / (log_fit["df"] - 1)
    log_deleted_t = log_fit["residual"] / (np.sqrt(log_deleted_s2) * np.sqrt(1.0 - log_fit["leverage"]))
    log_cook = log_internal ** 2 / log_fit["p"] * log_fit["leverage"] / (1.0 - log_fit["leverage"])
    log_max_h = int(np.argmax(log_fit["leverage"]))
    log_max_t = max(range(n), key=lambda index: (abs(float(log_deleted_t[index])), -index))
    log_max_cook = int(np.argmax(log_cook))
    for suffix, value, unit in (
        ("N", n, "rows"), ("P", log_fit["p"], "columns"), ("RANK", log_fit["rank"], "rank"),
        ("DF_RESIDUAL", log_fit["df"], "df"), ("RSS", log_fit["rss"], "MPa2"), ("S2", log_fit["s2"], "MPa2"),
        ("S", log_fit["s"], "MPa"), ("R2", log_fit["r2"], "dimensionless"),
        ("KAPPA2_RAW", log_fit["kappa_raw"], "dimensionless"), ("KAPPA2_SCALED", log_fit["kappa_scaled"], "dimensionless"),
        ("DOUBLING_AGE_DELTA_MPA", float(log_fit["beta"][-1] * math.log(2.0)), "MPa"),
        ("COUNT_H_GT_2P_OVER_N", int(np.sum(log_fit["leverage"] > 2 * log_fit["p"] / n)), "rows"),
        ("COUNT_COOK_GT_4_OVER_N", int(np.sum(log_cook > 4 / n)), "rows"),
        ("MAX_LEVERAGE__ROW_ID", row_ids[log_max_h], "row_id"), ("MAX_LEVERAGE__VALUE", float(log_fit["leverage"][log_max_h]), "dimensionless"),
        ("MAX_ABS_T__ROW_ID", row_ids[log_max_t], "row_id"), ("MAX_ABS_T__VALUE", abs(float(log_deleted_t[log_max_t])), "dimensionless"),
        ("MAX_COOK__ROW_ID", row_ids[log_max_cook], "row_id"), ("MAX_COOK__VALUE", float(log_cook[log_max_cook]), "dimensionless"),
    ):
        add_token(f"CP01_DIAG__LOG_AGE__{suffix}", value, unit)
    for term_id, estimate in zip(TERM_IDS[:-1] + ("LOG_AGE_28",), log_fit["beta"]):
        add_token(f"CP01_DIAG__LOG_AGE__COEF__{term_id}__ESTIMATE", float(estimate), "MPa" if term_id == "INTERCEPT" else "coefficient")
    for suffix, value, unit in (
        ("R2_AUX", koenker_log_r2, "dimensionless"), ("LM", koenker_log_lm, "chi_square"),
        ("DF", 8, "df"), ("P_ASYMPTOTIC", koenker_log_p, "p_value"),
    ):
        add_token(f"CP01_DIAG__KOENKER__LOG_AGE__{suffix}", value, unit)

    short_model = {MODEL_FULL: "FULL", MODEL_REDUCED: "REDUCED", MODEL_LOG: "LOG_AGE"}
    for method_name, metrics_source in (("ANALYTIC_LOOCV", loo_by_model), ("EXACT_LOPPO", loppo_by_model)):
        for model_id in (MODEL_FULL, MODEL_REDUCED, MODEL_LOG):
            metrics = metrics_source[model_id]
            base = f"CP01_DIAG__RESAMPLING__{method_name}__{short_model[model_id]}"
            for suffix, key, unit in (
                ("PRESS", "press", "MPa2"), ("MSE", "mse", "MPa2"), ("RMSE_MPA", "rmse", "MPa"),
                ("MAE_MPA", "mae", "MPa"), ("MIN_TRAINING_RANK", "min_training_rank", "rank"),
            ):
                add_token(base + "__" + suffix, metrics[key], unit)
    add_token("CP01_DIAG__RESAMPLING__SEED", None, "seed")
    for method_label, source in (("LOOCV", loo_by_model), ("LOPPO", loppo_by_model)):
        for suffix, key, unit in (("MSE", "mse", "MPa2"), ("RMSE_MPA", "rmse", "MPa"), ("MAE_MPA", "mae", "MPa")):
            add_token(f"CP01_DIAG__RESAMPLING__{method_label}__REDUCED_MINUS_FULL__{suffix}", source[MODEL_REDUCED][key] - source[MODEL_FULL][key], unit)
    for suffix, key, unit in (("MSE", "mse", "MPa2"), ("RMSE_MPA", "rmse", "MPa"), ("MAE_MPA", "mae", "MPa")):
        add_token(f"CP01_DIAG__RESAMPLING__FULL__LOPPO_MINUS_LOOCV__{suffix}", loppo_by_model[MODEL_FULL][key] - loo_by_model[MODEL_FULL][key], unit)
    repeated_profile_members = [members for members in inputs["profile_members"].values() if len(members) > 1]
    size_counts = {size: sum(len(members) == size for members in repeated_profile_members) for size in (2, 3, 4)}
    for suffix, value in (
        ("UNIQUE_COUNT", len(inputs["profile_members"])), ("SINGLETON_COUNT", sum(len(members) == 1 for members in inputs["profile_members"].values())),
        ("REPEATED_COUNT", len(repeated_profile_members)), ("REPEATED_ROW_COUNT", sum(map(len, repeated_profile_members))),
        ("EXTRA_ROW_COUNT", sum(len(members) - 1 for members in repeated_profile_members)),
        ("SIZE_2_COUNT", size_counts[2]), ("SIZE_3_COUNT", size_counts[3]), ("SIZE_4_COUNT", size_counts[4]),
    ):
        add_token(f"CP01_DIAG__PROFILE__{suffix}", value, "profiles" if "ROW" not in suffix else "rows")
    repeated_indices = np.asarray([index for members in repeated_profile_members for index in members], dtype=int)
    profile_prediction_difference = np.abs(loppo_by_model[MODEL_FULL]["prediction"] - loo_by_model[MODEL_FULL]["prediction"])
    add_token("CP01_DIAG__PROFILE__FULL__MAX_ABS_PREDICTION_DIFFERENCE_FROM_LOOCV_MPA", float(np.max(profile_prediction_difference[repeated_indices])), "MPa")
    add_token("CP01_DIAG__PROFILE__FULL__MEAN_ABS_PREDICTION_DIFFERENCE_FROM_LOOCV_MPA", float(np.mean(profile_prediction_difference[repeated_indices])), "MPa")

    labels = {
        "RESIDUAL_PATTERN": "CURVATURE_AND_INCREASING_SCALE",
        "HETERO_SUMMARY": "KOENKER_STRONG_FLAG__HC3_ALL_SE_LARGER__MEAN_MISSPECIFICATION_REMAINS",
        "HC3_BLOCK": "BLOCK_REMAINS_NONZERO_UNDER_HC3_ASYMPTOTIC_WALD",
        "SCREEN_SENSITIVITY": "MATERIAL_TARGET_SHIFT_DO_NOT_REPLACE_PRIMARY",
        "PROFILE_RANKING": "LOG_AGE_BEST__FULL_SECOND__REDUCED_THIRD__MSE_AND_MAE",
        "OVERALL_STABILITY": "BLOCK_AND_FULL_VS_REDUCED_STABLE__RAW_AGE_SPECIFICATION_UNSTABLE",
        "INTERACTION_SCOPE": "UNTESTED_LIMITATION__NO_INTERACTION_MODEL_FITTED",
    }
    for label, value in labels.items():
        add_token(f"CP01_DIAG__LABEL__{label}", value, "label")

    alt_texts = {
        "CP01_residuals_fitted.svg": (
            "Dua panel diagnostik model umur mentah: rataan sisaan per bin berganti tanda, "
            f"sedangkan RMS sisaan meningkat dari {localized(residual_bin_internal[0]['rms_residual_mpa'], 2)} MPa "
            f"pada bin suaian terendah menjadi {localized(residual_bin_internal[-1]['rms_residual_mpa'], 2)} MPa pada bin tertinggi; "
            "pola meragukan linearitas rataan dan skala konstan."
        ),
        "CP01_residual_quantiles.svg": (
            f"Q--Q sisaan terstudentisasi eksternal untuk {n:,}".replace(",", ".")
            + f" campuran; {int(np.sum(deleted_t > 3))} nilai positif melewati 3 dan nilai absolut terbesar "
            + f"{localized(abs(float(deleted_t[max_t])), 3)} pada {row_ids[max_t]}, tetapi plot kuantil tidak membuktikan normalitas."
        ),
        "CP01_influence.svg": (
            "Leverage, sisaan terstudentisasi, dan jarak Cook mencapai maksimum pada tiga baris berbeda: "
            f"{row_ids[max_h]} memiliki leverage {localized(float(full['leverage'][max_h]), 4)}, "
            f"{row_ids[max_t]} memiliki sisaan terstudentisasi {localized(abs(float(deleted_t[max_t])), 3)}, dan "
            f"{row_ids[max_cook]} memiliki jarak Cook {localized(float(cook[max_cook]), 4)}; tidak ada jarak Cook di atas 1 dan penyaringan tidak memberi izin penghapusan."
        ),
        "CP01_coefficient_uncertainty.svg": (
            "Galat baku HC3 lebih besar daripada galat baku klasik untuk kesembilan koefisien penuh; "
            f"rasio terbesar {localized(float(max(ratios)), 3)} terjadi pada umur, sedangkan uji Wald HC3 blok terak, abu terbang, dan superplasticizer tetap kuat."
        ),
        "CP01_model_sensitivity.svg": (
            f"RMSE tahan model penuh adalah {localized(full_loo['rmse'], 3)} pada LOOCV dan {localized(loppo_by_model[MODEL_FULL]['rmse'], 3)} pada penghapusan satu profil; "
            f"transformasi log umur memberi sekitar {localized((log_loo['rmse'] + loppo_by_model[MODEL_LOG]['rmse']) / 2, 2)} pada keduanya, sedangkan pemasangan ulang setelah menyaring "
            f"{int(sum(screen_union))} baris mengubah prediksi sampai {localized(float(prediction_by_subset['ALL_ROWS']['delta_max']), 2)} MPa dan bukan pengganti model utama."
        ),
    }
    for name, token_name in (
        ("CP01_residuals_fitted.svg", "RESIDUALS_FITTED"),
        ("CP01_residual_quantiles.svg", "RESIDUAL_QUANTILES"),
        ("CP01_influence.svg", "INFLUENCE"),
        ("CP01_coefficient_uncertainty.svg", "COEFFICIENT_UNCERTAINTY"),
        ("CP01_model_sensitivity.svg", "MODEL_SENSITIVITY"),
    ):
        add_token(f"CP01_DIAG__ALT__{token_name}", alt_texts[name], "alt_text")
    if len({row["token_id"] for row in diagnostic_tokens}) != len(diagnostic_tokens):
        raise RuntimeError("diagnostic token IDs are not unique")

    alt_payload = "# Teks alternatif CP01\n\n" + "\n\n".join(
        f"- **{name}**: {text}" for name, text in alt_texts.items()
    ) + "\n"
    top_h = sorted(range(n), key=lambda i: (-float(full["leverage"][i]), i))[:5]
    top_t = sorted(range(n), key=lambda i: (-abs(float(deleted_t[i])), i))[:5]
    top_c = cook_order[:5]
    diagnostic_text = [
        "EKUIVALEN TEKS DIAGNOSTIK CP01",
        "===============================",
        "",
        "1. CP01_residuals_fitted.svg",
        "Sumbu/seri: kuat tekan hasil suaian (MPa) pada sumbu horizontal; sisaan (MPa) dan akar(|sisaan terstandardisasi internal|) pada dua sumbu vertikal. Seluruh 1.030 observasi menurut urutan sumber ditampilkan; panel pertama menambahkan garis nol dan sepuluh bin tipe-7 nilai suaian.",
        "Tabel bin (indeks,jumlah,batas_bawah,batas_atas,rataan_residual_mpa,rms_residual_mpa):",
    ]
    diagnostic_text.extend(
        f"{index},{record['count']},{f8(record['boundary_lo'])},{f8(record['boundary_hi'])},{f8(record['mean_residual_mpa'])},{f8(record['rms_residual_mpa'])}"
        for index, record in enumerate(residual_bin_internal, start=1)
    )
    diagnostic_text.extend(
        [
            "Kesimpulan: rataan bin berubah tanda dan RMS sisaan meningkat menuju nilai suaian tinggi, yang menandai sisa kelengkungan rataan dan perubahan skala.",
            "Batas: diagnostik ini tidak mengidentifikasi mekanisme sebab-akibat dan tidak mengizinkan penghapusan kasus.",
            "",
            "2. CP01_residual_quantiles.svg",
            "Sumbu/seri: sisaan terstudentisasi penghapusan-satu terhadap kuantil acuan normal baku; seluruh 1.030 kasus tampil bersama diagonal acuan putus-putus.",
            f"Jumlah: |t|>2={observed_counts[2]}; |t|>3={observed_counts[3]}. Lima sisaan penghapusan-satu absolut terbesar:",
        ]
    )
    diagnostic_text.extend(f"{rank},{row_ids[index]},{f8(float(deleted_t[index]))}" for rank, index in enumerate(top_t, start=1))
    diagnostic_text.extend(
        [
            "Kesimpulan: penyimpangan pada ekor atas terlihat.",
            "Batas: kedekatan Q--Q tidak membuktikan kenormalan atau independensi.",
            "",
            "3. CP01_influence.svg",
            "Sumbu/seri: leverage pada sumbu horizontal dan sisaan terstudentisasi penghapusan-satu pada sumbu vertikal; luas penanda meningkat bersama jarak Cook.",
            f"Ambang: h>2p/n={localized(2*full['p']/n, 8)} ({observed_counts[0]} kasus); h>3p/n={localized(3*full['p']/n, 8)} ({observed_counts[1]} kasus); |t|>2 ({observed_counts[2]}); |t|>3 ({observed_counts[3]}); D>4/n={localized(4/n, 8)} ({observed_counts[4]} kasus).",
            "Lima kasus leverage terbesar (peringkat,id_baris,h,t_penghapusan,Cook):",
        ]
    )
    diagnostic_text.extend(f"{rank},{row_ids[index]},{f8(float(full['leverage'][index]))},{f8(float(deleted_t[index]))},{f8(float(cook[index]))}" for rank, index in enumerate(top_h, start=1))
    diagnostic_text.append("Lima kasus Cook terbesar (peringkat,id_baris,h,t_penghapusan,Cook):")
    diagnostic_text.extend(f"{rank},{row_ids[index]},{f8(float(full['leverage'][index]))},{f8(float(deleted_t[index]))},{f8(float(cook[index]))}" for rank, index in enumerate(top_c, start=1))
    diagnostic_text.extend(
        [
            "Kesimpulan: leverage maksimum, sisaan penghapusan-satu absolut maksimum, dan jarak Cook maksimum terjadi pada baris yang berbeda.",
            "Batas: ambang adalah layar eksploratif, bukan aturan eksklusi otomatis.",
            "",
            "4. CP01_coefficient_uncertainty.svg",
            "Sumbu/seri: efek kontras yang ditetapkan di muka dalam MPa pada sumbu horizontal; satu baris per kontras. Interval lingkaran penuh adalah interval t Gaussian titik-demi-titik; interval persegi putus-putus adalah interval normal-asimtotik HC3 titik-demi-titik; garis vertikal menandai nol.",
            "Tabel kontras (id,skala,taksiran,klasik_bawah,klasik_atas,hc3_bawah,hc3_atas):",
        ]
    )
    diagnostic_text.extend(f"{record['contrast_id']},{record['scale_label']},{f8(record['estimate'])},{f8(record['classic_lo'])},{f8(record['classic_hi'])},{f8(record['hc3_lo'])},{f8(record['hc3_hi'])}" for record in contrast_internal)
    diagnostic_text.extend(
        [
            f"Seluruh sembilan rasio SE HC3/klasik melebihi satu; maksimum={localized(float(max(ratios)), 8)} untuk UMUR. Wald HC3 bersama W={localized(w_hc3, 8)}, df=3, p={p8(p_w_hc3).replace('.', ',')}.",
            "Batas: HC3 hanya mengubah kovarians; panjang efek memakai kenaikan prediktor berbeda yang ditetapkan di muka dan tidak menetapkan sebab-akibat.",
            "",
            "5. CP01_model_sensitivity.svg",
            "Sumbu/seri: RMSE data tertahan (MPa) menurut model; lingkaran penuh menunjukkan LOOCV baris analitik dan persegi putus-putus menunjukkan LOPPO eksak. Setiap fold LOPPO meninggalkan seluruh baris dalam satu dari 992 profil prediktor eksak.",
            "Tabel validasi (model,LOOCV_RMSE,LOOCV_MAE,LOPPO_RMSE,LOPPO_MAE):",
        ]
    )
    diagnostic_text.extend(f"{model_id},{f8(loo_by_model[model_id]['rmse'])},{f8(loo_by_model[model_id]['mae'])},{f8(loppo_by_model[model_id]['rmse'])},{f8(loppo_by_model[model_id]['mae'])}" for model_id in (MODEL_FULL, MODEL_REDUCED, MODEL_LOG))
    diagnostic_text.extend(
        [
            f"Layar gabungan: hanya-leverage=44, hanya-Cook=43, irisan=36, gabungan=123, dipertahankan=907; perubahan prediksi maksimum pada seluruh baris={localized(float(prediction_by_subset['ALL_ROWS']['delta_max']), 8)} MPa.",
            "Kesimpulan: log umur menurunkan loss data tertahan secara material; model penuh umur mentah tetap mengungguli model tereduksi pada kedua pengelompokan validasi; pemasangan ulang setelah penyaringan mengubah proyeksi target secara material.",
            "Batas: model memakai ruang kolom atau populasi pemasangan efektif yang berbeda; validasi bersifat internal dan tidak memberi validasi sebab-akibat atau laboratorium eksternal.",
            "",
        ]
    )
    diagnostic_text_payload = "\n".join(diagnostic_text)

    diagnostics_summary_fields = ["token_id", "value_type", "numeric_value", "text_value", "unit", "display_format", "status"]
    payloads: dict[str, bytes] = {
        "CP01_data_summary.csv": csv_bytes(["variable_id", "role", "unit", "n", "missing", "minimum", "q1_type7", "median_type7", "q3_type7", "mean", "sample_sd", "maximum"], data_summary_rows),
        "CP01_model_fit.csv": csv_bytes(["model_id", "n", "p", "rank", "df", "rss", "s2_unbiased", "s_residual_mpa", "sigma2_mle", "rmse_in_sample_mpa", "r2", "adjusted_r2", "kappa2_raw", "kappa2_scaled"], model_fit_rows),
        "CP01_inference_coefficients.csv": csv_bytes(inference_fields, inference_rows),
        "CP01_coefficients_classic_hc3.csv": csv_bytes(["model_id", "term_id", "estimate", "se_gaussian", "se_HC3", "hc3_to_gaussian_ratio"], coefficient_comparison_rows),
        "CP01_anova_nested.csv": csv_bytes(["comparison_id", "row_kind", "df", "ss", "ms", "F", "p_value"], anova_rows),
        "CP01_inference_contrasts.csv": csv_bytes(["contrast_id", "term_id", "delta", "delta_unit", "estimate_MPa", "se_gaussian", "t", "df", "p_raw", "ci95_point_lo", "ci95_point_hi", "p_bonferroni_m8", "ci95_bonf_lo", "ci95_bonf_hi", "se_HC3", "z_HC3", "p_HC3", "ci95_HC3_lo", "ci95_HC3_hi", "p_HC3_bonferroni_m8", "ci95_HC3_bonf_lo", "ci95_HC3_bonf_hi"], contrast_rows),
        "CP01_inference_joint_F.csv": csv_bytes(["hypothesis_id", "q", "df1", "df2", "rss_reduced", "rss_full", "ss_extra", "Q_H", "F", "p_F", "W_HC3", "p_HC3_asymptotic"], joint_rows),
        "CP01_inference_results.csv": csv_bytes(["token_id", "value_type", "numeric_value", "text_value", "unit", "display_format", "source_file", "source_selector", "inference_basis", "status"], inference_token_rows),
        "CP01_leverage_selector_intervals.csv": csv_bytes(["selector_id", "row_id", "source_record", "order_index_one_based", "fitted_mpa", "h0", "se_mean", "tcrit_95", "mean_point_lo", "mean_point_hi", "se_prediction", "prediction_lo", "prediction_hi"], selector_interval_rows),
        "CP01_reference_prediction.csv": csv_bytes(["profile_id", "order_index_one_based", "cement_kg_per_m3", "blast_furnace_slag_kg_per_m3", "fly_ash_kg_per_m3", "water_kg_per_m3", "superplasticizer_kg_per_m3", "coarse_aggregate_kg_per_m3", "fine_aggregate_kg_per_m3", "age_days", "is_observed_row", "in_convex_hull", "muhat_MPa", "h0", "se_mean", "tcrit_95", "mean_point_lo", "mean_point_hi", "scheffe_Fcrit", "scheffe_multiplier", "mean_scheffe_lo", "mean_scheffe_hi", "se_prediction", "prediction_lo", "prediction_hi"], reference_rows),
        "CP01_loocv_metrics.csv": csv_bytes(["method_id", "model_id", "n", "press", "mse", "rmse_mpa", "mae_mpa", "min_training_rank", "seed"], loocv_rows),
        "CP01_profile_out_sensitivity.csv": csv_bytes(["model_id", "predictor_profile_id", "profile_size", "row_id", "source_record", "source_line", "training_rank", "predicted_mpa", "residual_mpa", "absolute_difference_from_rowwise_loo_mpa"], profile_rows),
        "CP01_diagnostics_summary.csv": csv_bytes(diagnostics_summary_fields, diagnostic_tokens),
        "CP01_diagnostics_observations.csv": csv_bytes(["row_id", "source_record", "source_line", "fitted_mpa", "residual_mpa", "leverage", "internal_standardized_residual", "deleted_studentized_residual", "deleted_residual_mpa", "cook_distance", "leverage_screen_2p_over_n", "cook_screen_4_over_n", "screen_union"], observation_rows),
        "CP01_residual_bins.csv": csv_bytes(["model_id", "bin_index", "count", "boundary_lo", "boundary_hi", "fitted_min", "fitted_max", "mean_residual_mpa", "rms_residual_mpa"], residual_bin_rows),
        "CP01_conditioning.csv": csv_bytes(["row_kind", "model_id", "term_id", "n", "p", "rank", "kappa2_raw", "kappa2_scaled", "kappa2_xtx_scaled", "vif"], conditioning_rows),
        "CP01_deleted_case_sensitivity.csv": csv_bytes(["row_id", "source_record", "source_line", "cook_rank", "term_id", "estimate_full", "estimate_deleted", "delta_full_minus_deleted", "delta_in_primary_se"], deleted_rows),
        "CP01_screen_sensitivity.csv": csv_bytes(["metric_id", "model_id", "subset_id", "term_id", "n", "p", "rank", "df", "numeric_value", "text_value", "unit"], screen_rows),
        "CP01_model_sensitivity.csv": csv_bytes(["model_id", "fit_subset", "n_fit", "p", "rank", "df", "rss", "s2", "s", "r2", "kappa2_scaled", "loocv_press", "loocv_mse", "loocv_rmse_mpa", "loocv_mae_mpa", "loppo_press", "loppo_mse", "loppo_rmse_mpa", "loppo_mae_mpa"], model_sensitivity_rows),
        "ALT_TEXT.md": alt_payload.encode("utf-8"),
        "CP01_diagnostics_text.txt": diagnostic_text_payload.encode("utf-8"),
    }
    payloads["CP01_residuals_fitted.svg"] = residual_svg(full, internal_residual, residual_bin_internal, alt_texts["CP01_residuals_fitted.svg"])
    payloads["CP01_residual_quantiles.svg"] = quantile_svg(np, stats, deleted_t, row_ids, alt_texts["CP01_residual_quantiles.svg"])
    payloads["CP01_influence.svg"] = influence_svg(full, deleted_t, cook, row_ids, alt_texts["CP01_influence.svg"])
    payloads["CP01_coefficient_uncertainty.svg"] = coefficient_svg(contrast_internal, ratios, alt_texts["CP01_coefficient_uncertainty.svg"])
    validation_for_svg = {
        model_id: {"loocv": loo_by_model[model_id], "loppo": loppo_by_model[model_id]}
        for model_id in (MODEL_FULL, MODEL_REDUCED, MODEL_LOG)
    }
    payloads["CP01_model_sensitivity.svg"] = model_svg(validation_for_svg, float(prediction_by_subset["ALL_ROWS"]["delta_max"]), alt_texts["CP01_model_sensitivity.svg"])

    expected_substantive = {
        "ALT_TEXT.md", "CP01_anova_nested.csv", "CP01_coefficient_uncertainty.svg",
        "CP01_coefficients_classic_hc3.csv", "CP01_conditioning.csv", "CP01_data_summary.csv",
        "CP01_deleted_case_sensitivity.csv", "CP01_diagnostics_observations.csv",
        "CP01_diagnostics_summary.csv", "CP01_diagnostics_text.txt", "CP01_inference_coefficients.csv",
        "CP01_inference_contrasts.csv", "CP01_inference_joint_F.csv", "CP01_inference_results.csv",
        "CP01_influence.svg", "CP01_leverage_selector_intervals.csv",
        "CP01_loocv_metrics.csv", "CP01_model_fit.csv", "CP01_model_sensitivity.csv",
        "CP01_model_sensitivity.svg", "CP01_profile_out_sensitivity.csv", "CP01_reference_prediction.csv",
        "CP01_residual_bins.csv", "CP01_residual_quantiles.svg", "CP01_residuals_fitted.svg",
        "CP01_screen_sensitivity.csv",
    }
    if set(payloads) != expected_substantive:
        raise RuntimeError(f"substantive output inventory differs: {sorted(set(payloads) ^ expected_substantive)}")
    for name in [name for name in payloads if name.endswith(".svg")]:
        text = payloads[name].decode("utf-8")
        if (
            "<title " not in text
            or "<desc " not in text
            or "role=\"img\"" not in text
            or "lang=\"id\"" not in text
            or "xml:lang=\"id\"" not in text
            or "<text " not in text
        ):
            raise RuntimeError(f"SVG accessibility contract failed: {name}")
        forbidden_english = (
            "Axes/series:", "Conclusion:", "Limit:", "fitted compressive strength",
            "deleted studentized residual", "solid circles", "dashed squares",
            "Visual proximity", "Diagnostic specification evidence only",
            "Refit union-screen", "fit utama", "leave-one-profile-out",
            "linearitas mean", "residual studentized", "Cook distance",
            "Standard error", "refit layar",
        )
        if any(phrase in text for phrase in forbidden_english):
            raise RuntimeError(f"SVG id-ID localization failed: {name}")
    if any(text not in alt_payload for text in alt_texts.values()):
        raise RuntimeError("ALT_TEXT.md does not contain every computed SVG description")
    if any(
        marker in diagnostic_text_payload
        for marker in (
            "Axes/series:", "Conclusion:", "Limit:", "Five largest", "Counts:",
            "Refit union-screen", "fit utama", "leave-one-profile-out",
            "linearitas mean", "residual studentized", "Cook distance",
            "Standard error", "refit layar",
        )
    ):
        raise RuntimeError("CP01 diagnostic text id-ID localization failed")

    summary = {
        "inputs": inputs,
        "models": {MODEL_FULL: full, MODEL_REDUCED: reduced, MODEL_LOG: log_fit, MODEL_SCREEN_FULL: screen_full},
        "joint": {"F": joint_f, "p_F": p_joint, "W_HC3": w_hc3, "p_HC3": p_w_hc3},
        "reference": {"muhat": muhat, "h0": h0, "support": hull},
        "validation": validation_for_svg,
        "screen_union_count": int(sum(screen_union)),
        "screen_block_p_F_nominal": screen_p,
        "assertions": {
            "raw_and_clean_hashes": True,
            "schema_rows_columns_and_profiles": True,
            "full_reduced_and_log_rank": True,
            "projection_normal_equations_and_scaled_equivalence": True,
            "classic_and_HC3_covariance_psd": True,
            "q3_quadratic_and_nested_RSS_identity": True,
            "interval_endpoints_and_family_sizes": True,
            "diagnostic_identities_and_threshold_counts": True,
            "analytic_LOOCV_matches_explicit_refits": True,
            "exact_992_profile_LOPPO_matches_block_identity": True,
            "union_screen_is_OR_and_retains_907": True,
            "leverage_selector_records_and_intervals": True,
            "canonical_inference_long_tokens": True,
            "union_screen_nominal_p_scientific_and_post_selection_labeled": True,
            "rights_provenance_closure": True,
            "id_ID_SVG_and_text_localization": True,
            "SVG_title_desc_text_and_alt_pairs": True,
            "seed_is_null": True,
        },
        "critical_values": {
            "t_point95_full": f8(tcrit),
            "t_bonferroni_m8": f8(tcrit_bonf),
            "z_point95": f8(zcrit),
            "z_bonferroni_m8": f8(zcrit_bonf),
            "F_scheffe_p9": f8(fcrit_scheffe),
            "scheffe_multiplier_p9": f8(scheffe_multiplier),
        },
    }
    return payloads, summary


def compute(np: Any, stats: Any, optimize: Any) -> tuple[dict[str, bytes], bytes]:
    substantive, summary = build(np, stats, optimize)
    manifest = manifest_bytes(substantive)
    payloads = dict(substantive)
    payloads["MANIFEST.csv"] = manifest
    analysis_code = Path(__file__).read_bytes()
    transform_code_path = DATA / "transform_cp01.py"
    transform_code = transform_code_path.read_bytes()
    receipt = canonical_json(
        {
            "schema": "o006.c140.cp01-analysis-replay.v2",
            "status": "pass",
            "network_access": False,
            "browser_processes_used": False,
            "seed": None,
            "canonical_input": {"path": "data/capstones/CP01/raw/data.csv", "bytes": RAW_BYTES, "sha256": RAW_SHA256},
            "clean_inputs": summary["inputs"]["clean_inventory"],
            "rights_provenance_inputs": summary["inputs"]["rights_provenance_inventory"],
            "transform_receipt": summary["inputs"]["transform_receipt"],
            "code": [
                {"path": "data/capstones/CP01/transform_cp01.py", "bytes": len(transform_code), "sha256": sha256(transform_code)},
                {"path": "capstones/run_cp01_analysis.py", "bytes": len(analysis_code), "sha256": sha256(analysis_code)},
            ],
            "environment": {
                "python": PYTHON_VERSION,
                "numpy": NUMPY_VERSION,
                "scipy": SCIPY_VERSION,
                "required_process_environment": ENVIRONMENT,
                "numeric_locale": "C",
                "linear_algebra_threads": 1,
            },
            "methods": {
                "OLS": "thin_QR_solve_without_pseudoinverse",
                "rank_and_condition": "binary64_thin_SVD; tau=epsilon*max(n,p)*sigma_max; sample-SD scaling",
                "inference": "classical_Gaussian_t_F_and_asymptotic_HC3_normal_chi_square",
                "LOOCV": "analytic_e_over_one_minus_h_verified_by_explicit_refits",
                "LOPPO": "direct_refit_for_each_of_992_exact_eight_predictor_profiles_verified_by_block_hat_identity",
                "leverage_selector_intervals": "full-model leverage order ascending with source-record ascending tie-break; ranks 1, 515, 1030; nominal pointwise Gaussian t intervals conditional on fixed X; not simultaneous",
                "convex_hull": summary["reference"]["support"]["method"],
                "serialization": "UTF-8_without_BOM; LF; ASCII_CSV_headers; fixed_8_or_scientific_8",
            },
            "reader_interface": {
                "CP01_inference_results.csv": {
                    "schema": "o006.c140.cp01-inference-long-tokens.v1",
                    "rows": 461,
                    "primary_key": ["token_id"],
                    "columns": ["token_id", "value_type", "numeric_value", "text_value", "unit", "display_format", "source_file", "source_selector", "inference_basis", "status"],
                },
                "CP01_screen_sensitivity.csv": {
                    "schema": "o006.c140.cp01-screen-sensitivity.v2",
                    "rows": 71,
                    "columns": ["metric_id", "model_id", "subset_id", "term_id", "n", "p", "rank", "df", "numeric_value", "text_value", "unit"],
                    "p_value_serialization": "scientific_8_below_1e-4_otherwise_fixed_8",
                    "union_block_p_metric_id": "BLOCK_SFP_P_F",
                    "union_block_inference_label": "NOMINAL_POST_SELECTION_F__EXPLORATORY_SENSITIVITY_ONLY",
                },
                "CP01_leverage_selector_intervals.csv": {
                    "schema": "o006.c140.cp01-leverage-selector-intervals.v1",
                    "rows": 3,
                    "primary_key": ["selector_id"],
                    "columns": ["selector_id", "row_id", "source_record", "order_index_one_based", "fitted_mpa", "h0", "se_mean", "tcrit_95", "mean_point_lo", "mean_point_hi", "se_prediction", "prediction_lo", "prediction_hi"],
                    "selection_model_id": MODEL_FULL,
                    "selector_records": [986, 592, 67],
                    "tie_break": "source_record_ascending",
                    "inference_label": "NOMINAL_POINTWISE_GAUSSIAN_T__POST_SELECTION_BY_FULL_MODEL_LEVERAGE__NOT_SIMULTANEOUS",
                },
            },
            "critical_values": summary["critical_values"],
            "spot_checks": {
                "full_RSS": f8(summary["models"][MODEL_FULL]["rss"]),
                "full_s": f8(summary["models"][MODEL_FULL]["s"]),
                "full_R2": f8(summary["models"][MODEL_FULL]["r2"]),
                "full_kappa2_scaled": f8(summary["models"][MODEL_FULL]["kappa_scaled"]),
                "joint_F_q3": f8(summary["joint"]["F"]),
                "joint_p_F": p8(summary["joint"]["p_F"]),
                "joint_W_HC3": f8(summary["joint"]["W_HC3"]),
                "profiles": 992,
                "screen_union_rows": summary["screen_union_count"],
                "reference_profile_muhat_MPa": f8(summary["reference"]["muhat"]),
                "leverage_selector_records": [986, 592, 67],
                "inference_token_rows": 461,
                "union_screen_block_p_F_nominal": p8(summary["screen_block_p_F_nominal"]),
                "union_screen_block_inference_label": "NOMINAL_POST_SELECTION_F__EXPLORATORY_SENSITIVITY_ONLY",
            },
            "assertions": summary["assertions"],
            "all_assertions_pass": all(summary["assertions"].values()),
            "manifest_closure": {
                "MANIFEST.csv": "lists substantive payloads; excludes MANIFEST.csv and CP01_REPLAY_RECEIPT.json",
                "receipt_outputs": "lists substantive payloads plus MANIFEST.csv; excludes receipt itself",
            },
            "outputs": [
                {"path": f"generated/capstones/CP01/{name}", "bytes": len(payload), "sha256": sha256(payload)}
                for name, payload in sorted(payloads.items())
            ],
        }
    )
    payloads["CP01_REPLAY_RECEIPT.json"] = receipt
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
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    np, stats, optimize = validate_environment()
    before_mtime = {
        path.name: path.stat().st_mtime_ns
        for path in OUTPUT.iterdir()
        if OUTPUT.is_dir() and path.is_file()
    } if OUTPUT.is_dir() else {}
    payloads, receipt = compute(np, stats, optimize)
    expected = set(payloads)
    if args.write:
        OUTPUT.mkdir(parents=True, exist_ok=True)
        actual = {path.name for path in OUTPUT.iterdir() if path.is_file()}
        unexpected = actual - expected
        if unexpected:
            raise RuntimeError(f"unexpected CP01 generated output: {sorted(unexpected)}")
        for name, payload in payloads.items():
            atomic_write(OUTPUT / name, payload)
        state = "written"
    else:
        actual = {path.name for path in OUTPUT.iterdir() if path.is_file()} if OUTPUT.is_dir() else set()
        if actual != expected:
            raise RuntimeError(f"CP01 generated inventory differs: expected {sorted(expected)}, observed {sorted(actual)}")
        for name, payload in payloads.items():
            path = OUTPUT / name
            if path.read_bytes() != payload:
                raise RuntimeError(f"CP01 generated output differs: {name}")
        after_mtime = {path.name: path.stat().st_mtime_ns for path in OUTPUT.iterdir() if path.is_file()}
        if after_mtime != before_mtime:
            raise RuntimeError("CP01 check-only changed an output mtime")
        state = "verified"
    print(
        json.dumps(
            {
                "mode": state,
                "status": "pass",
                "files": len(payloads),
                "bytes": sum(map(len, payloads.values())),
                "profiles": 992,
                "seed": None,
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
