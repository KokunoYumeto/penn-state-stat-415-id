#!/usr/bin/env python3
"""Deterministically materialize the frozen CP01 Concrete dataset.

The UCI CSV is the sole numerical input.  The ZIP, XLS, and README are
byte-identity witnesses only; routine replay deliberately has no XLS parser.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from fractions import Fraction
import hashlib
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


BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
RAW = BASE / "raw"
CLEAN = BASE / "clean"
RECEIPT = ROOT / "build" / "CP01_TRANSFORM_RECEIPT.json"

PYTHON_VERSION = "3.13.9"
NUMPY_VERSION = "2.4.4"
ENVIRONMENT = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "TZ": "UTC",
}

ASSETS = (
    (
        "raw/data.csv",
        41472,
        "8d4b15b6fc68cd932d745cbd663d5ceae66dd54422e99c1e4865f2936ab7e2af",
        "canonical_analysis_input",
    ),
    (
        "raw/concrete+compressive+strength.zip",
        34444,
        "dad85d14de8aee4e07479daa774e6b569a313715b71a3b92c95a07cf91c2c9a7",
        "provenance_witness",
    ),
    (
        "raw/archive/Concrete_Data.xls",
        124928,
        "710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4",
        "precision_and_header_witness_not_parsed",
    ),
    (
        "raw/archive/Concrete_Readme.txt",
        3808,
        "5cd3cdb31d3cfd68287daa6b22ed0541d6932113e83ee0980ced63641af3441d",
        "source_dictionary_and_rights_witness",
    ),
)

SOURCE_NAMES = (
    "Cement",
    "Blast Furnace Slag",
    "Fly Ash",
    "Water",
    "Superplasticizer",
    "Coarse Aggregate",
    "Fine Aggregate",
    "Age",
    "Concrete compressive strength",
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
DECIMAL_PLACES = (1, 1, 1, 1, 1, 1, 1, 0, 2)
DEFINITIONS = (
    "mass of cement in one cubic metre of mixture",
    "mass of blast-furnace slag in one cubic metre of mixture",
    "mass of fly ash in one cubic metre of mixture",
    "mass of water in one cubic metre of mixture",
    "mass of superplasticizer in one cubic metre of mixture",
    "mass of coarse aggregate in one cubic metre of mixture",
    "mass of fine aggregate in one cubic metre of mixture",
    "concrete age when compressive strength was tested",
    "measured concrete compressive strength",
)
UNITS = ("kg/m^3",) * 7 + ("day", "MPa")
SEMANTIC_TYPES = ("float64",) * 7 + ("int64", "float64")
DOMAINS = ("x>=0",) * 7 + ("integer;x>0", "x>0")
NUMBER_RE = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")

ROW_FIELDS = (
    "row_id",
    "source_record",
    "source_line",
    "clean_record",
    "canonical_row_sha256",
    "full_row_duplicate_group",
    "predictor_duplicate_group",
    "disposition",
    "exclusion_reason",
)
COLUMN_FIELDS = (
    "source_position",
    "source_name",
    "clean_position",
    "clean_name",
    "role",
    "definition",
    "semantic_type",
    "unit",
    "missing_codes",
    "transform",
    "domain",
    "missing_count",
    "nonfinite_count",
    "unique_count",
    "observed_min",
    "observed_max",
    "canonical_column_sha256",
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, separators=(",", ": "))
        + "\n"
    ).encode("utf-8")


def csv_bytes(fields: tuple[str, ...] | list[str], rows: list[dict[str, object]]) -> bytes:
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


def validate_environment() -> Any:
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

    if np.__version__ != NUMPY_VERSION:
        raise RuntimeError(
            f"NumPy version differs: expected {NUMPY_VERSION}, observed {np.__version__}"
        )
    return np


def inspect_assets() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative, expected_bytes, expected_hash, role in ASSETS:
        path = (BASE / relative).resolve(strict=True)
        try:
            path.relative_to(BASE.resolve())
        except ValueError as exc:
            raise RuntimeError(f"asset escapes CP01 directory: {relative}") from exc
        payload = path.read_bytes()
        observed_hash = sha256(payload)
        if len(payload) != expected_bytes or observed_hash != expected_hash:
            raise RuntimeError(
                f"frozen asset mismatch for {relative}: expected bytes/hash "
                f"{expected_bytes}/{expected_hash}, observed {len(payload)}/{observed_hash}"
            )
        records.append(
            {
                "path": relative,
                "role": role,
                "bytes": len(payload),
                "sha256": observed_hash,
            }
        )
    return records


def format_decimal(value: Decimal, position: int) -> str:
    places = DECIMAL_PLACES[position]
    if places == 0:
        return str(int(value))
    return f"{value:.{places}f}"


def parse_source() -> tuple[list[list[Decimal]], list[list[str]], dict[str, object]]:
    payload = (RAW / "data.csv").read_bytes()
    if payload.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError("raw/data.csv must not contain a UTF-8 BOM")
    if b"\x00" in payload:
        raise RuntimeError("raw/data.csv contains a NUL byte")
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise RuntimeError("raw/data.csv is not strict UTF-8") from exc
    if "\r\n" in text and text.replace("\r\n", "").find("\r") >= 0:
        raise RuntimeError("raw/data.csv contains mixed or bare CR line endings")
    line_ending = "CRLF" if "\r\n" in text else "LF"
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    rows = list(reader)
    if len(rows) != 1031:
        raise RuntimeError(f"raw/data.csv must have one header plus 1030 records, got {len(rows)}")
    if tuple(rows[0]) != SOURCE_NAMES:
        raise RuntimeError(f"raw/data.csv header differs: {rows[0]!r}")

    decimal_rows: list[list[Decimal]] = []
    canonical_rows: list[list[str]] = []
    for source_record, tokens in enumerate(rows[1:], start=1):
        if len(tokens) != 9:
            raise RuntimeError(f"source record {source_record} has {len(tokens)} fields, expected 9")
        parsed: list[Decimal] = []
        canonical: list[str] = []
        for position, token in enumerate(tokens):
            if not NUMBER_RE.fullmatch(token):
                raise RuntimeError(
                    f"source record {source_record}, column {position + 1} is not a canonical numeric token: {token!r}"
                )
            value = Decimal(token)
            if not value.is_finite():
                raise RuntimeError(f"nonfinite value at record {source_record}, column {position + 1}")
            quantum = Decimal(1).scaleb(-DECIMAL_PLACES[position])
            if value.quantize(quantum) != value:
                raise RuntimeError(
                    f"published precision fails at record {source_record}, column {position + 1}: {token!r}"
                )
            if position < 7 and value < 0:
                raise RuntimeError(f"negative mixture mass at record {source_record}")
            if position == 7 and (value <= 0 or value != value.to_integral_value()):
                raise RuntimeError(f"age must be a positive integer at record {source_record}")
            if position == 8 and value <= 0:
                raise RuntimeError(f"response must be positive at record {source_record}")
            if not math.isfinite(float(value)):
                raise RuntimeError(f"float64 conversion is nonfinite at record {source_record}")
            parsed.append(value)
            canonical.append(format_decimal(value, position))
        if sum(parsed[:7], Decimal(0)) <= 0:
            raise RuntimeError(f"mixture mass total must be positive at record {source_record}")
        decimal_rows.append(parsed)
        canonical_rows.append(canonical)
    return decimal_rows, canonical_rows, {
        "encoding": "UTF-8_without_BOM",
        "source_line_endings": line_ending,
        "delimiter": ",",
        "decimal_mark": ".",
        "header_rows": 1,
        "data_rows": 1030,
        "columns": 9,
        "missing_cells": 0,
        "parse_failures": 0,
        "nan_cells": 0,
        "nonfinite_cells": 0,
    }


def duplicate_groups(keys: list[tuple[str, ...]]) -> tuple[list[str], dict[str, object]]:
    members: dict[tuple[str, ...], list[int]] = {}
    for source_record, key in enumerate(keys, start=1):
        members.setdefault(key, []).append(source_record)
    repeated = [indices for indices in members.values() if len(indices) > 1]
    labels = [""] * len(keys)
    for indices in repeated:
        label = f"CP01-R{min(indices):04d}"
        for source_record in indices:
            labels[source_record - 1] = label
    size_distribution: dict[str, int] = {}
    for indices in repeated:
        key = str(len(indices))
        size_distribution[key] = size_distribution.get(key, 0) + 1
    return labels, {
        "groups": len(repeated),
        "rows": sum(len(indices) for indices in repeated),
        "extra_occurrences": sum(len(indices) - 1 for indices in repeated),
        "unique_keys": len(members),
        "group_size_distribution": dict(sorted(size_distribution.items(), key=lambda item: int(item[0]))),
    }


def determinant(matrix: list[list[Fraction]]) -> Fraction:
    work = [row[:] for row in matrix]
    result = Fraction(1)
    for column in range(len(work)):
        pivot = next((row for row in range(column, len(work)) if work[row][column]), None)
        if pivot is None:
            return Fraction(0)
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
            result = -result
        pivot_value = work[column][column]
        result *= pivot_value
        for row in range(column + 1, len(work)):
            if not work[row][column]:
                continue
            factor = work[row][column] / pivot_value
            for target in range(column + 1, len(work)):
                work[row][target] -= factor * work[column][target]
    return result


def exact_rank_certificate(rows: list[list[Decimal]]) -> dict[str, object]:
    basis: list[list[Fraction]] = []
    pivots: list[int] = []
    pivot_rows: list[int] = []
    selected: list[list[Fraction]] = []
    for source_record, values in enumerate(rows, start=1):
        candidate = [Fraction(1)] + [Fraction(value) for value in values[:8]]
        original = candidate[:]
        for pivot, basis_row in zip(pivots, basis):
            if candidate[pivot]:
                factor = candidate[pivot]
                candidate = [left - factor * right for left, right in zip(candidate, basis_row)]
        new_pivot = next((index for index, value in enumerate(candidate) if value), None)
        if new_pivot is None:
            continue
        pivot_value = candidate[new_pivot]
        candidate = [value / pivot_value for value in candidate]
        for index, basis_row in enumerate(basis):
            if basis_row[new_pivot]:
                factor = basis_row[new_pivot]
                basis[index] = [left - factor * right for left, right in zip(basis_row, candidate)]
        insertion = sum(pivot < new_pivot for pivot in pivots)
        pivots.insert(insertion, new_pivot)
        basis.insert(insertion, candidate)
        pivot_rows.append(source_record)
        selected.append(original)
        if len(basis) == 9:
            break
    if len(basis) != 9:
        raise RuntimeError(f"exact design rank is {len(basis)}, expected 9")
    det = determinant(selected)
    if not det:
        raise RuntimeError("selected exact rank minor has zero determinant")
    if pivot_rows != [1, 2, 3, 4, 5, 6, 7, 17, 185]:
        raise RuntimeError(f"exact pivot-row certificate differs: {pivot_rows}")
    if det != Fraction(-470089281375, 2):
        raise RuntimeError(f"exact minor determinant differs: {det}")
    return {
        "rank_Q": 9,
        "pivot_source_records": pivot_rows,
        "minor_determinant": str(det),
        "minor_determinant_numerator": det.numerator,
        "minor_determinant_denominator": det.denominator,
    }


def numerical_certificate(np: Any, rows: list[list[Decimal]]) -> dict[str, object]:
    z = np.asarray([[float(value) for value in row[:8]] for row in rows], dtype=np.float64)
    x = np.column_stack((np.ones(len(z), dtype=np.float64), z))
    means = np.mean(z, axis=0)
    sample_sd = np.std(z, axis=0, ddof=1)
    if not bool(np.all(np.isfinite(sample_sd) & (sample_sd > 0.0))):
        raise RuntimeError("all predictor sample standard deviations must be finite and positive")
    x_scaled = np.column_stack((np.ones(len(z), dtype=np.float64), (z - means) / sample_sd))
    singular_raw = np.linalg.svd(x, full_matrices=False, compute_uv=False)
    singular_scaled = np.linalg.svd(x_scaled, full_matrices=False, compute_uv=False)
    epsilon = float(np.finfo(np.float64).eps)
    tau_raw = epsilon * max(x.shape) * float(singular_raw[0])
    tau_scaled = epsilon * max(x_scaled.shape) * float(singular_scaled[0])
    rank_raw = int(np.sum(singular_raw > tau_raw))
    rank_scaled = int(np.sum(singular_scaled > tau_scaled))
    kappa_raw = float(singular_raw[0] / singular_raw[-1])
    kappa_scaled = float(singular_scaled[0] / singular_scaled[-1])
    if rank_raw != 9 or rank_scaled != 9 or not singular_scaled[-1] > tau_scaled:
        raise RuntimeError("numerical rank certificate failed")
    if not math.isfinite(kappa_scaled) or kappa_scaled >= 1.0e8:
        raise RuntimeError(f"scaled condition-number gate failed: {kappa_scaled}")
    if abs(kappa_raw - 106074.57306673574) > 2.0e-7:
        raise RuntimeError(f"raw condition-number assertion differs: {kappa_raw}")
    if abs(kappa_scaled - 8.711778718605796) > 2.0e-11:
        raise RuntimeError(f"scaled condition-number assertion differs: {kappa_scaled}")
    return {
        "method": "thin_SVD_binary64",
        "standardization": "source_order_mean_and_sample_sd_ddof_1",
        "epsilon_binary64": epsilon,
        "rank_threshold_formula": "epsilon*max(n,p)*sigma_max",
        "rank_raw": rank_raw,
        "rank_scaled": rank_scaled,
        "residual_df": len(rows) - rank_raw,
        "predictor_means": [float(value) for value in means],
        "predictor_sample_sd": [float(value) for value in sample_sd],
        "singular_values_raw_desc": [float(value) for value in singular_raw],
        "singular_values_scaled_desc": [float(value) for value in singular_scaled],
        "tau_raw": tau_raw,
        "tau_scaled": tau_scaled,
        "kappa2_raw": kappa_raw,
        "kappa2_scaled": kappa_scaled,
        "kappa2_scaled_gate_lt": 1.0e8,
    }


def build_payloads(np: Any) -> tuple[dict[str, bytes], dict[str, object]]:
    assets_before = inspect_assets()
    decimal_rows, canonical_rows, parsing = parse_source()

    clean_records = [dict(zip(CLEAN_NAMES, row)) for row in canonical_rows]
    clean_csv = csv_bytes(list(CLEAN_NAMES), clean_records)

    full_keys = [tuple(row) for row in canonical_rows]
    predictor_keys = [tuple(row[:8]) for row in canonical_rows]
    full_labels, full_summary = duplicate_groups(full_keys)
    predictor_labels, predictor_summary = duplicate_groups(predictor_keys)
    response_varying_groups = []
    predictor_members: dict[tuple[str, ...], list[int]] = {}
    for source_record, key in enumerate(predictor_keys, start=1):
        predictor_members.setdefault(key, []).append(source_record)
    for members in predictor_members.values():
        if len(members) > 1 and len({canonical_rows[index - 1][8] for index in members}) > 1:
            response_varying_groups.append(members)
    varying_summary = {
        "groups": len(response_varying_groups),
        "rows": sum(map(len, response_varying_groups)),
    }
    expected_duplicates = {
        "full": {
            "groups": 11,
            "rows": 36,
            "extra_occurrences": 25,
            "unique_keys": 1005,
            "group_size_distribution": {"2": 1, "3": 6, "4": 4},
        },
        "predictor": {
            "groups": 19,
            "rows": 57,
            "extra_occurrences": 38,
            "unique_keys": 992,
            "group_size_distribution": {"2": 5, "3": 9, "4": 5},
        },
        "predictor_groups_with_varying_response": {"groups": 9, "rows": 24},
    }
    observed_duplicates = {
        "full": full_summary,
        "predictor": predictor_summary,
        "predictor_groups_with_varying_response": varying_summary,
    }
    if observed_duplicates != expected_duplicates:
        raise RuntimeError(f"duplicate inventory differs: {observed_duplicates}")

    row_records: list[dict[str, object]] = []
    for source_record, canonical in enumerate(canonical_rows, start=1):
        row_bytes = (",".join(canonical) + "\n").encode("utf-8")
        row_records.append(
            {
                "row_id": f"CP01-R{source_record:04d}",
                "source_record": source_record,
                "source_line": source_record + 1,
                "clean_record": source_record,
                "canonical_row_sha256": sha256(row_bytes),
                "full_row_duplicate_group": full_labels[source_record - 1],
                "predictor_duplicate_group": predictor_labels[source_record - 1],
                "disposition": "kept",
                "exclusion_reason": "",
            }
        )
    row_manifest = csv_bytes(ROW_FIELDS, row_records)

    column_records: list[dict[str, object]] = []
    for position, (source_name, clean_name) in enumerate(zip(SOURCE_NAMES, CLEAN_NAMES)):
        tokens = [row[position] for row in canonical_rows]
        values = [row[position] for row in decimal_rows]
        column_records.append(
            {
                "source_position": position + 1,
                "source_name": source_name,
                "clean_position": position + 1,
                "clean_name": clean_name,
                "role": "response" if position == 8 else "predictor",
                "definition": DEFINITIONS[position],
                "semantic_type": SEMANTIC_TYPES[position],
                "unit": UNITS[position],
                "missing_codes": "NONE_ALLOWED",
                "transform": "rename_only;canonical_decimal_serialization",
                "domain": DOMAINS[position],
                "missing_count": 0,
                "nonfinite_count": 0,
                "unique_count": len(set(tokens)),
                "observed_min": format_decimal(min(values), position),
                "observed_max": format_decimal(max(values), position),
                "canonical_column_sha256": sha256(("\n".join(tokens) + "\n").encode("utf-8")),
            }
        )
    column_manifest = csv_bytes(COLUMN_FIELDS, column_records)

    exact = exact_rank_certificate(decimal_rows)
    numerical = numerical_certificate(np, decimal_rows)
    preliminary = {
        "concrete_compressive_strength.csv": clean_csv,
        "ROW_MANIFEST.csv": row_manifest,
        "COLUMN_MANIFEST.csv": column_manifest,
    }
    ledger = {
        "schema": "o006.c140.cp01-transform-ledger.v1",
        "status": "pass",
        "canonical_analysis_asset": "raw/data.csv",
        "xls_parser_used": False,
        "network_access": False,
        "browser_processes_used": False,
        "seed": None,
        "source_assets_before": assets_before,
        "csv_xls_relationship_frozen_witness": {
            "xls_parsed_during_replay": False,
            "positional_cells": 1030 * 9,
            "raw_value_differing_cells": 2260,
            "rounding_rule": "midpoint_ties_away_from_zero; columns_1_to_7_1dp; age_0dp; response_2dp",
            "rounding_rule_mismatches": 0,
        },
        "parsing": parsing,
        "data_schema": {
            "source_headers": list(SOURCE_NAMES),
            "clean_headers": list(CLEAN_NAMES),
            "n": 1030,
            "data_columns": 9,
            "predictors": 8,
            "response": "compressive_strength_mpa",
        },
        "row_identity": {
            "first": "CP01-R0001",
            "last": "CP01-R1030",
            "source_order_preserved": True,
            "rows_kept": 1030,
            "rows_excluded": 0,
        },
        "duplicates": observed_duplicates,
        "rank_exact": exact,
        "conditioning": numerical,
        "outputs_excluding_ledger": [
            {"path": f"clean/{name}", "bytes": len(payload), "sha256": sha256(payload)}
            for name, payload in sorted(preliminary.items())
        ],
        "assertions": {
            "asset_identity": True,
            "schema_and_domains": True,
            "no_missing_parse_nan_or_nonfinite": True,
            "source_order_and_row_ids": True,
            "duplicate_inventory": True,
            "exact_rank_9": True,
            "numerical_rank_9": True,
            "scaled_condition_below_1e8": True,
            "no_rng_seed_null": True,
        },
    }
    payloads = dict(preliminary)
    payloads["TRANSFORM_LEDGER.json"] = canonical_json(ledger)
    assets_after = inspect_assets()
    if assets_after != assets_before:
        raise RuntimeError("frozen source assets changed while transforming")
    summary = {
        "assets": assets_before,
        "duplicates": observed_duplicates,
        "rank_exact": exact,
        "conditioning": numerical,
    }
    return payloads, summary


def compute() -> tuple[dict[str, bytes], bytes]:
    np = validate_environment()
    payloads, summary = build_payloads(np)
    code_payload = Path(__file__).read_bytes()
    receipt = canonical_json(
        {
            "schema": "o006.c140.cp01-transform-replay.v1",
            "status": "pass",
            "network_access": False,
            "browser_processes_used": False,
            "seed": None,
            "canonical_input": summary["assets"][0],
            "witness_assets": summary["assets"][1:],
            "code": {
                "path": "data/capstones/CP01/transform_cp01.py",
                "bytes": len(code_payload),
                "sha256": sha256(code_payload),
            },
            "environment": {
                "python": PYTHON_VERSION,
                "numpy": NUMPY_VERSION,
                "required_process_environment": ENVIRONMENT,
                "numeric_locale": "C",
            },
            "outputs": [
                {"path": f"data/capstones/CP01/clean/{name}", "bytes": len(payload), "sha256": sha256(payload)}
                for name, payload in sorted(payloads.items())
            ],
            "summary": {
                "rows": 1030,
                "columns": 9,
                "predictor_profiles": summary["duplicates"]["predictor"]["unique_keys"],
                "rank": summary["rank_exact"]["rank_Q"],
                "residual_df": summary["conditioning"]["residual_df"],
                "kappa2_scaled": summary["conditioning"]["kappa2_scaled"],
            },
            "all_assertions_pass": True,
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
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    payloads, receipt = compute()
    expected = set(payloads)
    if args.write:
        CLEAN.mkdir(parents=True, exist_ok=True)
        actual = {path.name for path in CLEAN.iterdir() if path.is_file()}
        unexpected = actual - expected
        if unexpected:
            raise RuntimeError(f"unexpected CP01 clean output: {sorted(unexpected)}")
        for name, payload in payloads.items():
            atomic_write(CLEAN / name, payload)
        atomic_write(RECEIPT, receipt)
        state = "written"
    else:
        actual = {path.name for path in CLEAN.iterdir() if path.is_file()} if CLEAN.is_dir() else set()
        if actual != expected:
            raise RuntimeError(f"CP01 clean output inventory differs: expected {sorted(expected)}, observed {sorted(actual)}")
        for name, payload in payloads.items():
            if (CLEAN / name).read_bytes() != payload:
                raise RuntimeError(f"CP01 clean output differs: {name}")
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != receipt:
            raise RuntimeError("CP01 transform receipt differs")
        state = "verified"
    print(
        json.dumps(
            {
                "mode": state,
                "status": "pass",
                "rows": 1030,
                "files": len(payloads),
                "bytes": sum(map(len, payloads.values())),
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
