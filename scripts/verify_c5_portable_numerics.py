#!/usr/bin/env python3
"""Replay frozen capstone numerics without rewriting published artifacts.

This is a separate, explicitly portable numerical check, not a byte-exact
producer replay.  Only float leaves in eight explicitly named computed fields
of the CP01 ledger's conditioning certificate may differ, by at most 1e-12
relative error and zero absolute tolerance.  Normative constants, source
identities, discrete data, other output bytes, and receipt fields stay exact.
Analysis modes run the unmodified producers' complete scientific assertions,
then compare every substantive CSV with exact structure/discrete fields and
explicit decimal tolerances. Frozen rendered artifacts keep exact identities;
their recomputed bytes are not claimed to be identical.
"""

from __future__ import annotations

import argparse
import copy
import csv
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import io
from itertools import zip_longest
import json
import math
from pathlib import Path
import platform
import re
import stat
import sys
from typing import Any


sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "c140-companion"
DATA = COMPONENT / "data" / "capstones" / "CP01"
PRODUCER = DATA / "transform_cp01.py"
RECEIPT = COMPONENT / "build" / "CP01_TRANSFORM_RECEIPT.json"
BUILD = COMPONENT / "build" / "C5_BUILD_RECEIPT.json"
QA = COMPONENT / "build" / "C5_QA_RECEIPT.json"
BUILD_IDENTITY = (13951, "cc9e6002edcbb5adbe5a348233fb73f5588728a4fbc330a93061c1f18807f372")
QA_IDENTITY = (9279, "aef36e757fca2d3ad1593087af12a5102120697f16715acf210248d94d296bfd")
OUTPUT_PREFIX = "data/capstones/CP01/clean/"
OUTPUT_NAMES = {
    "COLUMN_MANIFEST.csv",
    "ROW_MANIFEST.csv",
    "TRANSFORM_LEDGER.json",
    "concrete_compressive_strength.csv",
}
RELATIVE_TOLERANCE = 1e-12
ABSOLUTE_TOLERANCE = 0.0
COMPUTED_CONDITIONING_FIELDS = {
    "predictor_means",
    "predictor_sample_sd",
    "singular_values_raw_desc",
    "singular_values_scaled_desc",
    "tau_raw",
    "tau_scaled",
    "kappa2_raw",
    "kappa2_scaled",
}
MAX_INPUT_BYTES = 2_000_000
MAX_ANALYSIS_FILE_BYTES = 160_000_000
MAX_DIFFERENCE_EXAMPLES = 25

# Complementary columns are always exact, including identifiers, integer counts,
# decisions, fixed design settings, selectors, hashes, units and prose tokens.
CSV_FLOAT_COLUMNS = {
    "CP01_anova_nested.csv": "ss ms F p_value",
    "CP01_coefficients_classic_hc3.csv": "estimate se_gaussian se_HC3 hc3_to_gaussian_ratio",
    "CP01_conditioning.csv": "kappa2_raw kappa2_scaled kappa2_xtx_scaled vif",
    "CP01_data_summary.csv": "minimum q1_type7 median_type7 q3_type7 mean sample_sd maximum",
    "CP01_deleted_case_sensitivity.csv": "estimate_full estimate_deleted delta_full_minus_deleted delta_in_primary_se",
    "CP01_diagnostics_observations.csv": "fitted_mpa residual_mpa leverage internal_standardized_residual deleted_studentized_residual deleted_residual_mpa cook_distance",
    "CP01_diagnostics_summary.csv": "numeric_value",
    "CP01_inference_coefficients.csv": "estimate se_gaussian t p_raw ci95_point_lo ci95_point_hi se_HC3 z_HC3 p_HC3 ci95_HC3_lo ci95_HC3_hi",
    "CP01_inference_contrasts.csv": "estimate_MPa se_gaussian t p_raw ci95_point_lo ci95_point_hi p_bonferroni_m8 ci95_bonf_lo ci95_bonf_hi se_HC3 z_HC3 p_HC3 ci95_HC3_lo ci95_HC3_hi p_HC3_bonferroni_m8 ci95_HC3_bonf_lo ci95_HC3_bonf_hi",
    "CP01_inference_joint_F.csv": "rss_reduced rss_full ss_extra Q_H F p_F W_HC3 p_HC3_asymptotic",
    "CP01_inference_results.csv": "numeric_value",
    "CP01_leverage_selector_intervals.csv": "fitted_mpa h0 se_mean tcrit_95 mean_point_lo mean_point_hi se_prediction prediction_lo prediction_hi",
    "CP01_loocv_metrics.csv": "press mse rmse_mpa mae_mpa",
    "CP01_model_fit.csv": "rss s2_unbiased s_residual_mpa sigma2_mle rmse_in_sample_mpa r2 adjusted_r2 kappa2_raw kappa2_scaled",
    "CP01_model_sensitivity.csv": "rss s2 s r2 kappa2_scaled loocv_press loocv_mse loocv_rmse_mpa loocv_mae_mpa loppo_press loppo_mse loppo_rmse_mpa loppo_mae_mpa",
    "CP01_profile_out_sensitivity.csv": "predicted_mpa residual_mpa absolute_difference_from_rowwise_loo_mpa",
    "CP01_reference_prediction.csv": "muhat_MPa h0 se_mean tcrit_95 mean_point_lo mean_point_hi scheffe_Fcrit scheffe_multiplier mean_scheffe_lo mean_scheffe_hi se_prediction prediction_lo prediction_hi",
    "CP01_residual_bins.csv": "boundary_lo boundary_hi fitted_min fitted_max mean_residual_mpa rms_residual_mpa",
    "CP01_screen_sensitivity.csv": "numeric_value",
    "CP02_cells_clean.csv": "observed_rate observed_rate_secondary",
    "CP02_posterior_summary.csv": "posterior_mean posterior_variance credible_low_95 credible_high_95 credible_mass prob_gt_threshold posterior_loss_a0 posterior_loss_a1 predictive_next_success predictive_rep_mean predictive_rep_variance beta_binomial_mass_sum",
    "CP02_model_comparison.csv": "log_evidence log_m0 log_m1 log_bf10 bf10 posterior_odds_10 posterior_prob_m0 posterior_prob_m1 posterior_loss_a0 posterior_loss_a1",
    "CP02_frequentist_comparison.csv": "observed_rate wilson_low_95 wilson_high_95 cp_low_95 cp_high_95 exact_p_value actual_size holm_adjusted_p power grid_min grid_max grid_argmin grid_argmax coverage_at_threshold observed_deviance",
    "CP02_coverage.csv": "interval_low interval_high interval_width p_fixed coverage grid_min grid_max grid_argmin grid_argmax coverage_at_threshold prior_average_coverage posterior_mass",
    "CP02_posterior_predictive.csv": "predictive_probability predictive_mean predictive_variance mass_sum",
    "CP02_diagnostics.csv": "observed_median observed_low_95 observed_high_95 replicate_median replicate_low_95 replicate_high_95 mcse minimum_standardized_eigenvalue",
    "CP02_dispersion_profile.csv": "kappa optimized_mean log_likelihood delta_from_profile_max",
    "CP02_sensitivity.csv": "posterior_mean posterior_median credible_low_95 credible_high_95 prob_gt_threshold log_bf10 bf10 posterior_odds_10 observed_rate delta_posterior_mean abs_delta_posterior_mean delta_observed_rate abs_delta_observed_rate delta_log_bf10 delta_primary_target delta_from_primary",
    "CP02_influence.csv": "full_value loo_value signed_change absolute_change",
    "CP02_contrasts.csv": "posterior_mean posterior_median credible_low_95 credible_high_95 mcse",
}
INTEGER_TOKEN = re.compile(r"[+-]?[0-9]+\Z")
DECIMAL_TOKEN = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def regular_file(path: Path) -> None:
    relative = path.relative_to(ROOT)
    if not relative.parts or ".." in relative.parts:
        raise RuntimeError("unsafe portable replay input path")
    for index in range(len(relative.parts) + 1):
        node = ROOT.joinpath(*relative.parts[:index])
        metadata = node.lstat()
        if stat.S_ISLNK(metadata.st_mode) or (
            getattr(metadata, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise RuntimeError("linked portable replay input: " + path.relative_to(ROOT).as_posix())
        is_leaf = index == len(relative.parts)
        if not (stat.S_ISREG(metadata.st_mode) if is_leaf else stat.S_ISDIR(metadata.st_mode)):
            raise RuntimeError("invalid portable replay input type: " + path.relative_to(ROOT).as_posix())


def read_identity(path: Path, identity: tuple[int, str]) -> bytes:
    regular_file(path)
    before = path.stat()
    if before.st_size > MAX_INPUT_BYTES:
        raise RuntimeError("portable replay input byte cap exceeded")
    payload = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise RuntimeError("portable replay input changed while reading")
    if (len(payload), digest(payload)) != identity:
        raise RuntimeError("frozen identity mismatch: " + path.relative_to(ROOT).as_posix())
    return payload


def json_object(payload: bytes, label: str) -> dict[str, Any]:
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict) or canonical_json(value) != payload:
        raise RuntimeError(label + " is not a canonical JSON object")
    return value


def compare_ledger(frozen: object, recomputed: object) -> list[dict[str, object]]:
    differences: list[dict[str, object]] = []

    def visit(left: object, right: object, parts: tuple[str, ...]) -> None:
        label = "ledger." + ".".join(parts)
        if type(left) is not type(right):
            raise RuntimeError("type differs at " + label)
        if isinstance(left, dict):
            if left.keys() != right.keys():
                raise RuntimeError("keys differ at " + label)
            for key in sorted(left):
                visit(left[key], right[key], (*parts, key))
        elif isinstance(left, list):
            if len(left) != len(right):
                raise RuntimeError("list length differs at " + label)
            for index, (old, new) in enumerate(zip(left, right)):
                visit(old, new, (*parts, str(index)))
        elif (
            isinstance(left, float)
            and len(parts) >= 2
            and parts[0] == "conditioning"
            and parts[1] in COMPUTED_CONDITIONING_FIELDS
        ):
            if not math.isfinite(left) or not math.isfinite(right):
                raise RuntimeError("nonfinite certificate value at " + label)
            if not math.isclose(left, right, rel_tol=RELATIVE_TOLERANCE, abs_tol=ABSOLUTE_TOLERANCE):
                raise RuntimeError(
                    f"numerical tolerance exceeded at {label}: frozen={left:.17g}, "
                    f"recomputed={right:.17g}, rtol={RELATIVE_TOLERANCE}, atol=0"
                )
            if left != right:
                differences.append({
                    "path": label,
                    "frozen": left,
                    "recomputed": right,
                    "absolute_error": abs(left - right),
                    "relative_error": abs(left - right) / max(abs(left), abs(right)),
                })
        elif left != right:
            raise RuntimeError("exact value differs at " + label)

    visit(frozen, recomputed, ())
    return differences


def output_records(payloads: dict[str, bytes]) -> list[dict[str, object]]:
    if set(payloads) != OUTPUT_NAMES:
        raise RuntimeError("CP01 transform output names differ")
    return [
        {"path": OUTPUT_PREFIX + name, "bytes": len(payload), "sha256": digest(payload)}
        for name, payload in sorted(payloads.items())
    ]


def compare_receipt(
    frozen_payload: bytes,
    recomputed_payload: bytes,
    frozen_outputs: dict[str, bytes],
    recomputed_outputs: dict[str, bytes],
) -> None:
    frozen = json_object(frozen_payload, "frozen CP01 transform receipt")
    recomputed = json_object(recomputed_payload, "recomputed CP01 transform receipt")
    if frozen.get("outputs") != output_records(frozen_outputs):
        raise RuntimeError("frozen receipt does not bind every frozen output")
    if recomputed.get("outputs") != output_records(recomputed_outputs):
        raise RuntimeError("recomputed receipt does not bind every recomputed output")
    old_ledger = json_object(frozen_outputs["TRANSFORM_LEDGER.json"], "frozen ledger")
    new_ledger = json_object(recomputed_outputs["TRANSFORM_LEDGER.json"], "recomputed ledger")
    compare_ledger(old_ledger, new_ledger)
    for receipt, ledger, label in (
        (frozen, old_ledger, "frozen"),
        (recomputed, new_ledger, "recomputed"),
    ):
        echoed = receipt["summary"]["kappa2_scaled"]
        if type(echoed) is not float or echoed != ledger["conditioning"]["kappa2_scaled"]:
            raise RuntimeError(label + " receipt conditioning echo differs")
    normalized = copy.deepcopy(recomputed)
    for old, new in zip(frozen["outputs"], normalized["outputs"]):
        if new["path"] == OUTPUT_PREFIX + "TRANSFORM_LEDGER.json":
            # This one derived binding was verified against its own payload above.
            # It is normalized only after the certificate comparison has passed.
            new["bytes"], new["sha256"] = old["bytes"], old["sha256"]
    normalized["summary"]["kappa2_scaled"] = frozen["summary"]["kappa2_scaled"]
    if canonical_json(normalized) != frozen_payload:
        raise RuntimeError("receipt differs outside the two explicitly normalized ledger bindings")


def decimal_difference(old: str, new: str, label: str) -> dict[str, str]:
    """Allow relative error plus one quantum of the FROZEN displayed value."""
    if INTEGER_TOKEN.fullmatch(old) or INTEGER_TOKEN.fullmatch(new):
        raise RuntimeError("integer token differs at " + label)
    if not DECIMAL_TOKEN.fullmatch(old) or not DECIMAL_TOKEN.fullmatch(new):
        raise RuntimeError("nondecimal or missing token differs at " + label)
    with localcontext() as context:
        context.prec = 80
        left, right = Decimal(old), Decimal(new)
        if not left.is_finite() or not right.is_finite():
            raise RuntimeError("nonfinite CSV value at " + label)
        quantum = Decimal(1).scaleb(left.as_tuple().exponent)
        # A coarser new serialization must not manufacture a larger allowance.
        if Decimal(1).scaleb(right.as_tuple().exponent) > quantum:
            raise RuntimeError("recomputed decimal precision decreased at " + label)
        error = abs(left - right)
        scale = max(abs(left), abs(right))
        allowance = Decimal("1e-12") * scale + quantum
        if error > allowance:
            raise RuntimeError(
                f"CSV tolerance exceeded at {label}: frozen={old}, recomputed={new}, "
                f"absolute_error={error}, allowed={allowance}"
            )
        return {
            "frozen": old, "recomputed": new, "absolute_error": str(error),
            "relative_error": str(error / scale if scale else Decimal(0)),
            "frozen_display_quantum": str(quantum), "allowed_error": str(allowance),
        }


def compare_csv(name: str, frozen_stream: Any, recomputed_stream: Any) -> dict[str, object]:
    if name not in CSV_FLOAT_COLUMNS:
        raise RuntimeError("unclassified substantive CSV: " + name)
    old_reader = csv.reader(frozen_stream, strict=True)
    new_reader = csv.reader(recomputed_stream, strict=True)
    header = next(old_reader, None)
    if not header or header != next(new_reader, None) or len(header) != len(set(header)):
        raise RuntimeError("CSV header differs or is duplicated: " + name)
    allowed = set(CSV_FLOAT_COLUMNS[name].split())
    if not allowed <= set(header):
        raise RuntimeError("CSV numerical column contract differs: " + name)
    examples: list[dict[str, object]] = []
    count = rows = 0
    max_absolute = max_relative = Decimal(0)
    for rows, pair in enumerate(zip_longest(old_reader, new_reader), start=1):
        old_row, new_row = pair
        if old_row is None or new_row is None:
            raise RuntimeError(f"CSV row count differs: {name} at row {rows}")
        if len(old_row) != len(header) or len(new_row) != len(header):
            raise RuntimeError(f"CSV row width differs: {name} at row {rows}")
        old_values = dict(zip(header, old_row))
        for column, old, new in zip(header, old_row, new_row):
            label = f"{name}.row[{rows}].{column}"
            numeric = column in allowed
            # These quantiles count boundary cells, not a continuous statistic.
            if name == "CP02_diagnostics.csv" and old_values.get("discrepancy") == "boundary_cell_count" and column.startswith(("observed_", "replicate_")):
                numeric = False
            if column == "numeric_value" and old_values.get("value_type") == "integer":
                numeric = False
            if numeric and (old.lower() in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"} or new.lower() in {"nan", "inf", "+inf", "-inf", "infinity", "+infinity", "-infinity"}):
                raise RuntimeError("nonfinite CSV value at " + label)
            if old == new:
                continue
            if not numeric:
                raise RuntimeError("exact CSV token differs at " + label)
            difference = decimal_difference(old, new, label)
            count += 1
            max_absolute = max(max_absolute, Decimal(difference["absolute_error"]))
            max_relative = max(max_relative, Decimal(difference["relative_error"]))
            if len(examples) < MAX_DIFFERENCE_EXAMPLES:
                examples.append({"row": rows, "column": column, **difference})
    return {
        "file": name, "rows": rows, "differing_cells": count,
        "max_absolute_error": str(max_absolute), "max_relative_error": str(max_relative),
        "difference_examples": examples, "examples_truncated": count > len(examples),
    }


def identity_records(value: object) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        if {"path", "bytes", "sha256"} <= value.keys():
            return [value]
        return [item for child in value.values() for item in identity_records(child)]
    if isinstance(value, list):
        return [item for child in value for item in identity_records(child)]
    return []


def compare_analysis_derived(
    frozen: dict[str, Any], recomputed: dict[str, Any], capstone: str,
) -> list[dict[str, object]]:
    """Compare typed receipt observations before normalizing derived bindings."""
    allowed = {
        "critical_values": set("F_scheffe_p9 scheffe_multiplier_p9 t_bonferroni_m8 t_point95_full z_bonferroni_m8 z_point95".split()),
        "spot_checks": set("full_R2 full_RSS full_kappa2_scaled full_s joint_F_q3 joint_W_HC3 joint_p_F reference_profile_muhat_MPa union_screen_block_p_F_nominal".split()),
    } if capstone == "CP01" else {
        "spot_checks": {"bf10", "clopper_pearson_grid_minimum", "log_bf10", "posterior_odds_10"},
    }
    differences: list[dict[str, object]] = []
    for section, fields in allowed.items():
        left, right = frozen[section], recomputed[section]
        if type(left) is not dict or type(right) is not dict or left.keys() != right.keys() or not fields <= left.keys():
            raise RuntimeError("receipt observation keys/type differ at " + section)
        for key in sorted(left):
            old, new = left[key], right[key]
            label = f"{capstone}.receipt.{section}.{key}"
            if type(old) is not type(new):
                raise RuntimeError("receipt observation type differs at " + label)
            if key not in fields:
                if canonical_json(old) != canonical_json(new):
                    raise RuntimeError("exact receipt observation differs at " + label)
            elif capstone == "CP01":
                if type(old) is not str or not DECIMAL_TOKEN.fullmatch(old) or not DECIMAL_TOKEN.fullmatch(new):
                    raise RuntimeError("receipt decimal observation type differs at " + label)
                if old != new:
                    differences.append({"path": label, **decimal_difference(old, new, label)})
            else:
                if type(old) is not float or not math.isfinite(old) or not math.isfinite(new):
                    raise RuntimeError("receipt finite-float observation type differs at " + label)
                if not math.isclose(old, new, rel_tol=RELATIVE_TOLERANCE, abs_tol=0.0):
                    raise RuntimeError(f"receipt observation tolerance exceeded at {label}: frozen={old:.17g}, recomputed={new:.17g}")
                if old != new:
                    differences.append({"path": label, "frozen": old, "recomputed": new, "absolute_error": abs(old - new), "relative_error": abs(old - new) / max(abs(old), abs(new))})
    return differences


def manifest_records(payload: bytes, capstone: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True)
    header = ["path", "bytes", "sha256"] if capstone == "CP01" else ["path", "role", "bytes", "sha256"]
    if reader.fieldnames != header:
        raise RuntimeError(capstone + " manifest header differs")
    rows = list(reader)
    if any(set(row) != set(header) or None in row.values() for row in rows):
        raise RuntimeError(capstone + " manifest row width differs")
    if [row["path"] for row in rows] != sorted({row["path"] for row in rows}):
        raise RuntimeError(capstone + " manifest ordering/uniqueness differs")
    return rows


def verify_manifest_bindings(
    payload: bytes, capstone: str, outputs: list[dict[str, object]],
    frozen_roles: dict[str, str],
) -> None:
    prefix = f"generated/capstones/{capstone}/"
    expected = []
    for item in outputs:
        name = str(item["path"])[len(prefix):]
        if name in {"MANIFEST.csv", "CP01_REPLAY_RECEIPT.json"}:
            continue
        row = {"path": str(item["path"]) if capstone == "CP01" else name,
               "bytes": str(item["bytes"]), "sha256": str(item["sha256"])}
        if capstone == "CP02":
            row["role"] = frozen_roles[name]
        expected.append(row)
    if manifest_records(payload, capstone) != expected:
        raise RuntimeError(capstone + " manifest does not bind its complete substantive payloads")


def analysis_main(capstone: str) -> None:
    observed: dict[Path, tuple[int, str, int]] = {}

    def verify_file(path: Path, identity: tuple[int, str]) -> None:
        regular_file(path)
        before = path.stat()
        if before.st_size != identity[0] or before.st_size > MAX_ANALYSIS_FILE_BYTES:
            raise RuntimeError("frozen size differs or exceeds cap: " + path.relative_to(ROOT).as_posix())
        checksum = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1_048_576), b""):
                checksum.update(block)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or checksum.hexdigest() != identity[1]:
            raise RuntimeError("frozen identity changed: " + path.relative_to(ROOT).as_posix())
        previous = observed.get(path)
        record = (identity[0], identity[1], after.st_mtime_ns)
        if previous is not None and previous != record:
            raise RuntimeError("frozen replay input changed during analysis")
        observed[path] = record

    def bound_read(path: Path, identity: tuple[int, str]) -> bytes:
        verify_file(path, identity)
        return read_identity(path, identity)

    build = json_object(bound_read(BUILD, BUILD_IDENTITY), "C5 build authority")
    qa = json_object(bound_read(QA, QA_IDENTITY), "C5 QA authority")
    binding = [row for row in build["capstone_receipts"] if row["capstone"] == capstone and row["role"] == "analysis"]
    if len(binding) != 1:
        raise RuntimeError("analysis authority binding is not unique")
    receipt_path = COMPONENT / binding[0]["path"]
    frozen_receipt = bound_read(receipt_path, (binding[0]["bytes"], binding[0]["sha256"]))
    receipt = json_object(frozen_receipt, "frozen analysis receipt")
    for item in identity_records(receipt):
        verify_file(COMPONENT / item["path"], (item["bytes"], item["sha256"]))
    for item in receipt["code"]:
        matching = [row for row in qa["scripts"] if row["path"] == item["path"]]
        if len(matching) != 1 or matching[0]["sha256"] != item["sha256"]:
            raise RuntimeError("C5 QA source identity differs: " + item["path"])
    if capstone == "CP02":
        clean = receipt["clean_inputs"]
        transform = json_object((COMPONENT / clean["transform_receipt"]["path"]).read_bytes(), "CP02 transform receipt")
        for item in transform["outputs"]:
            verify_file(COMPONENT / "data/capstones/CP02/clean" / item["path"], (item["bytes"], item["sha256"]))

    prefix = f"generated/capstones/{capstone}/"
    frozen_outputs = receipt["outputs"]
    names = []
    for item in frozen_outputs:
        if not item["path"].startswith(prefix):
            raise RuntimeError("analysis output path is outside its capstone")
        name = item["path"][len(prefix):]
        if not name or "/" in name or "\\" in name or name in {".", ".."}:
            raise RuntimeError("analysis output is not a safe basename")
        names.append(name)
    if names != sorted(set(names)):
        raise RuntimeError("analysis output inventory is not sorted/unique")
    expected_names = set(names) | ({"CP01_REPLAY_RECEIPT.json"} if capstone == "CP01" else set())
    directory = COMPONENT / "generated" / "capstones" / capstone
    if {path.name for path in directory.iterdir()} != expected_names:
        raise RuntimeError("frozen generated directory is not closed: " + capstone)
    manifest_payload = (directory / "MANIFEST.csv").read_bytes()
    roles = {row["path"]: row["role"] for row in manifest_records(manifest_payload, capstone)} if capstone == "CP02" else {}
    verify_manifest_bindings(manifest_payload, capstone, frozen_outputs, roles)
    source = COMPONENT / "capstones" / f"run_{capstone.lower()}_analysis.py"
    spec = importlib.util.spec_from_file_location("c5_frozen_" + capstone.lower() + "_analysis", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("analysis import specification unavailable")
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    print(json.dumps({"capstone": capstone, "status": "replaying_original_scientific_assertions", "writes_performed": False}), flush=True)
    if capstone == "CP01":
        payloads, replay_receipt = producer.compute(*producer.validate_environment())
    else:
        payloads, replay_receipt, _ = producer.build_expected_payload()
    if set(payloads) != expected_names:
        raise RuntimeError("recomputed analysis output inventory differs")
    if capstone == "CP01" and payloads["CP01_REPLAY_RECEIPT.json"] != replay_receipt:
        raise RuntimeError("CP01 generated replay receipt is not the returned receipt")
    recomputed = json_object(replay_receipt, "recomputed analysis receipt")
    actual_outputs = [
        {"path": prefix + name, "bytes": len(payloads[name]), "sha256": digest(payloads[name])}
        for name in names
    ]
    if recomputed["outputs"] != actual_outputs:
        raise RuntimeError("recomputed receipt does not bind every recomputed analysis output")
    verify_manifest_bindings(payloads["MANIFEST.csv"], capstone, actual_outputs, roles)
    receipt_differences = compare_analysis_derived(receipt, recomputed, capstone)
    normalized = copy.deepcopy(recomputed)
    normalized["outputs"] = receipt["outputs"]
    # Only normalize after the derived observations passed their explicit
    # numerical comparisons and all discrete receipt observations stayed exact.
    for key in ("critical_values", "spot_checks"):
        if key in receipt:
            normalized[key] = receipt[key]
    if capstone == "CP02":
        closure = normalized["manifest_closure"]
        if closure["manifest_bytes"] != len(payloads["MANIFEST.csv"]) or closure["manifest_sha256"] != digest(payloads["MANIFEST.csv"]):
            raise RuntimeError("CP02 recomputed manifest closure identity differs")
        closure["manifest_bytes"] = receipt["manifest_closure"]["manifest_bytes"]
        closure["manifest_sha256"] = receipt["manifest_closure"]["manifest_sha256"]
    if canonical_json(normalized) != frozen_receipt:
        raise RuntimeError("analysis receipt source/data/environment/method/assertion fields differ")
    csv_reports = []
    rendered = []
    for name in sorted(expected_names - {"MANIFEST.csv", "CP01_REPLAY_RECEIPT.json"}):
        if name.endswith(".csv"):
            with (directory / name).open(encoding="utf-8", newline="") as old_stream, io.TextIOWrapper(io.BytesIO(payloads[name]), encoding="utf-8", newline="") as new_stream:
                report = compare_csv(name, old_stream, new_stream)
            csv_reports.append(report)
            print(json.dumps({"capstone": capstone, "csv_comparison": report}, sort_keys=True), flush=True)
        else:
            rendered.append({"file": name, "frozen_sha256": next(item["sha256"] for item in frozen_outputs if item["path"] == prefix + name), "recomputed_sha256": digest(payloads[name]), "comparison": "frozen_identity_exact; recomputed_rendered_bytes_not_asserted_equal"})
    for path, (size, checksum, _) in list(observed.items()):
        verify_file(path, (size, checksum))
    print(json.dumps({
        "schema": "o006.c140.c5-portable-analysis-check.v1", "status": "pass", "capstone": capstone,
        "mode": "portable-numerical-check-not-byte-exact-producer-replay",
        "python": platform.python_version(), "platform": sys.platform,
        "rtol": "1e-12", "absolute_allowance": "at most one frozen displayed decimal quantum; integer tokens exact",
        "csv_tables_compared": len(csv_reports), "csv_rows_compared": sum(row["rows"] for row in csv_reports),
        "csv_differing_cells": sum(row["differing_cells"] for row in csv_reports),
        "max_csv_absolute_error": str(max(Decimal(row["max_absolute_error"]) for row in csv_reports)),
        "max_csv_relative_error": str(max(Decimal(row["max_relative_error"]) for row in csv_reports)),
        "frozen_files_verified_unchanged": len(observed),
        "frozen_receipt_sha256": digest(frozen_receipt), "recomputed_receipt_sha256": digest(replay_receipt),
        "recomputed_manifest_and_receipt_bind_recomputed_outputs": True,
        "receipt_derived_comparison": "explicit numerical fields tolerance-checked; all other keys/types/observations exact",
        "receipt_differing_observations": len(receipt_differences), "receipt_differences": receipt_differences,
        "rendered_artifact_scope": rendered, "original_scientific_assertions_pass": True,
        "writes_performed": False, "network_access": False,
    }, sort_keys=True), flush=True)


def transform_main() -> None:
    observed: dict[Path, tuple[int, str, int]] = {}

    def frozen_read(path: Path, identity: tuple[int, str]) -> bytes:
        payload = read_identity(path, identity)
        observed[path] = (len(payload), digest(payload), path.stat().st_mtime_ns)
        return payload

    build = json_object(frozen_read(BUILD, BUILD_IDENTITY), "frozen C5 build authority")
    qa = json_object(frozen_read(QA, QA_IDENTITY), "frozen C5 QA authority")
    bound = [item for item in build["capstone_receipts"] if item["capstone"] == "CP01" and item["role"] == "transform"]
    if len(bound) != 1 or bound[0]["path"] != "build/CP01_TRANSFORM_RECEIPT.json":
        raise RuntimeError("C5 build authority CP01 transform binding differs")
    frozen_receipt = frozen_read(RECEIPT, (bound[0]["bytes"], bound[0]["sha256"]))
    receipt = json_object(frozen_receipt, "frozen CP01 transform receipt")
    source_identity = receipt["code"]
    if source_identity["path"] != "data/capstones/CP01/transform_cp01.py":
        raise RuntimeError("CP01 transform source path differs")
    frozen_read(PRODUCER, (source_identity["bytes"], source_identity["sha256"]))
    script_rows = [item for item in qa["scripts"] if item["path"] == source_identity["path"]]
    if len(script_rows) != 1 or script_rows[0]["sha256"] != source_identity["sha256"]:
        raise RuntimeError("C5 QA authority CP01 transform source binding differs")
    for item in [receipt["canonical_input"], *receipt["witness_assets"]]:
        frozen_read(DATA / item["path"], (item["bytes"], item["sha256"]))
    frozen_outputs: dict[str, bytes] = {}
    for item in receipt["outputs"]:
        path = item["path"]
        if not path.startswith(OUTPUT_PREFIX) or path[len(OUTPUT_PREFIX):] not in OUTPUT_NAMES:
            raise RuntimeError("frozen clean output path differs")
        frozen_outputs[path[len(OUTPUT_PREFIX):]] = frozen_read(COMPONENT / path, (item["bytes"], item["sha256"]))
    if set(frozen_outputs) != OUTPUT_NAMES:
        raise RuntimeError("frozen clean output inventory differs")
    if {path.name for path in (DATA / "clean").iterdir()} != OUTPUT_NAMES:
        raise RuntimeError("live clean output directory is not closed")
    spec = importlib.util.spec_from_file_location("c5_frozen_cp01_transform", PRODUCER)
    if spec is None or spec.loader is None:
        raise RuntimeError("CP01 producer import specification is unavailable")
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    recomputed_outputs, recomputed_receipt = producer.compute()
    for name in OUTPUT_NAMES - {"TRANSFORM_LEDGER.json"}:
        if recomputed_outputs.get(name) != frozen_outputs[name]:
            raise RuntimeError("byte-exact clean output differs: " + name)
    differences = compare_ledger(
        json_object(frozen_outputs["TRANSFORM_LEDGER.json"], "frozen ledger"),
        json_object(recomputed_outputs["TRANSFORM_LEDGER.json"], "recomputed ledger"),
    )
    compare_receipt(frozen_receipt, recomputed_receipt, frozen_outputs, recomputed_outputs)
    for path, (size, checksum, mtime_ns) in observed.items():
        read_identity(path, (size, checksum))
        if path.stat().st_mtime_ns != mtime_ns:
            raise RuntimeError("read-only replay changed an input mtime")
    import numpy as np
    print(json.dumps({
        "schema": "o006.c140.c5-cp01-portable-transform-check.v1",
        "status": "pass",
        "mode": "portable-numerical-check-not-byte-exact-producer-replay",
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": sys.platform,
        "machine": platform.machine(),
        "rtol": RELATIVE_TOLERANCE,
        "atol": ABSOLUTE_TOLERANCE,
        "tolerance_scope": "only float leaves of explicitly named computed conditioning fields",
        "computed_conditioning_fields": sorted(COMPUTED_CONDITIONING_FIELDS),
        "conditioning_differing_paths_count": len(differences),
        "conditioning_differences": differences,
        "frozen_ledger_sha256": digest(frozen_outputs["TRANSFORM_LEDGER.json"]),
        "recomputed_ledger_sha256": digest(recomputed_outputs["TRANSFORM_LEDGER.json"]),
        "frozen_receipt_sha256": digest(frozen_receipt),
        "recomputed_receipt_sha256": digest(recomputed_receipt),
        "exact_nonledger_outputs": 3,
        "frozen_files_verified_unchanged": len(observed),
        "recomputed_receipt_binds_recomputed_outputs": True,
        "writes_performed": False,
        "network_access": False,
    }, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("cp01-transform", "cp01-analysis", "cp02-analysis"), default="cp01-transform")
    arguments = parser.parse_args()
    if arguments.mode == "cp01-transform":
        transform_main()
    else:
        analysis_main(arguments.mode[:4].upper())
