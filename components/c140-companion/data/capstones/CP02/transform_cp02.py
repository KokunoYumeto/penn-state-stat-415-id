#!/usr/bin/env python3
"""Deterministic, offline CP02 ingestion and clean-table construction.

The script has two deliberately small execution modes:

* ``--write`` builds the complete clean payload in memory and atomically
  replaces the five owned clean artifacts plus the transform receipt.
* ``--check-only`` rebuilds the same payload in memory and compares names and
  bytes.  It never opens an output path for writing.

Only Python's standard library is used.  Network and subprocess modules are
intentionally absent.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SCHEMA_ID = "o006.c140.cp02-transform.v1"
EXPECTED_HEADER = [
    "Transmitter",
    "Year",
    "No_nests",
    "Total_method_1",
    "Total_method_2",
]
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
PRIMARY_DENOMINATOR_COLUMN = "Total_method_1"
SECONDARY_DENOMINATOR_COLUMN = "Total_method_2"
INTEGER_TOKEN = re.compile(r"^(0|[1-9][0-9]*)$")
INT64_MAX = 2**63 - 1

SCRIPT_PATH = Path(__file__).resolve()
DATA_ROOT = SCRIPT_PATH.parent
COMPONENT_ROOT = SCRIPT_PATH.parents[3]
CLEAN_ROOT = DATA_ROOT / "clean"
BUILD_ROOT = COMPONENT_ROOT / "build"
RECEIPT_PATH = BUILD_ROOT / "CP02_TRANSFORM_RECEIPT.json"

RAW_IDENTITIES = {
    "raw/nest_propensity.csv": {
        "role": "numeric_input",
        "manifest_role": "aggregate_data",
        "bytes": 285,
        "sha256": "8790b4dfa29a5b39228e758e40e02cbb48612c38b8440020aa108c85ca0673c4",
        "encoding": "UTF-8_ASCII-subset_no-BOM",
        "newlines": "CRLF",
    },
    "raw/README.md": {
        "role": "dictionary",
        "manifest_role": "data_dictionary",
        "bytes": 4139,
        "sha256": "43a53f9a451a4030b8d3edb2a7517c48863d8ef23d7ae4986d15c20d7f8f5459",
        "encoding": "UTF-8_ASCII-subset_no-BOM",
        "newlines": "LF",
    },
}

EXPECTED_CELL_SOURCE_RECORDS = {
    ("VHF", 2015): 1,
    ("VHF", 2016): 2,
    ("VHF", 2017): 3,
    ("VHF", 2018): 4,
    ("VHF", 2019): 5,
    ("VHF", 2020): 6,
    ("VHF", 2021): 7,
    ("VHF", 2022): 8,
    ("PTT", 2019): 9,
    ("PTT", 2020): 10,
    ("PTT", 2021): 11,
    ("PTT", 2022): 12,
}
GROUP_RANK = {"VHF": 0, "PTT": 1}


class ContractError(RuntimeError):
    """Raised when a frozen CP02 assertion fails."""


def fail(assertion: str, relative_path: str, detail: str) -> None:
    raise ContractError(f"{assertion}: {relative_path}: {detail}")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
        separators=(",", ": "),
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


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
        writer.writerow({key: row.get(key, "") for key in header})
    return buffer.getvalue().encode("utf-8")


def one_csv_record(values: list[Any]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(values)
    return buffer.getvalue().encode("utf-8")


def read_verified_bytes(relative_path: str, expected: dict[str, Any]) -> bytes:
    path = DATA_ROOT / Path(relative_path)
    if not path.is_file():
        fail("raw_asset_present", relative_path, "file is missing")
    data = path.read_bytes()
    if len(data) != expected["bytes"]:
        fail("raw_asset_bytes", relative_path, f"expected {expected['bytes']}, got {len(data)}")
    digest = sha256_bytes(data)
    if digest != expected["sha256"]:
        fail("raw_asset_sha256", relative_path, f"expected {expected['sha256']}, got {digest}")
    return data


def verify_input_manifest() -> bytes:
    relative_path = "INPUT_MANIFEST.csv"
    path = DATA_ROOT / relative_path
    if not path.is_file():
        fail("input_manifest_present", relative_path, "file is missing")
    payload = path.read_bytes()
    try:
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
    except (UnicodeDecodeError, csv.Error) as exc:
        fail("input_manifest_parse", relative_path, str(exc))
    if len(rows) != 2:
        fail("input_manifest_rows", relative_path, f"expected 2, got {len(rows)}")
    by_path = {row.get("local_path", ""): row for row in rows}
    if set(by_path) != set(RAW_IDENTITIES):
        fail("input_manifest_paths", relative_path, "raw path inventory differs from frozen contract")
    for raw_path, expected in RAW_IDENTITIES.items():
        row = by_path[raw_path]
        checks = {
            "role": expected["manifest_role"],
            "bytes": str(expected["bytes"]),
            "sha256": expected["sha256"],
            "encoding": expected["encoding"],
            "newlines": expected["newlines"],
        }
        for field, value in checks.items():
            if row.get(field) != value:
                fail(
                    "input_manifest_identity",
                    relative_path,
                    f"{raw_path} field {field!r}: expected {value!r}, got {row.get(field)!r}",
                )
    return payload


def verify_contract_metadata() -> dict[str, bytes]:
    paths = ["SCHEMA.json", "DATASET_PROVENANCE.json", "RIGHTS_EVIDENCE.md"]
    payloads: dict[str, bytes] = {}
    for relative_path in paths:
        path = DATA_ROOT / relative_path
        if not path.is_file():
            fail("contract_metadata_present", relative_path, "file is missing")
        payloads[relative_path] = path.read_bytes()
    try:
        schema = json.loads(payloads["SCHEMA.json"].decode("utf-8"))
        provenance = json.loads(payloads["DATASET_PROVENANCE.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail("contract_metadata_json", "SCHEMA.json/DATASET_PROVENANCE.json", str(exc))
    schema_names = [column.get("name") for column in schema.get("columns", [])]
    required_schema = {
        "source_file": "raw/nest_propensity.csv",
        "dictionary_file": "raw/README.md",
    }
    for field, value in required_schema.items():
        if schema.get(field) != value:
            fail("schema_identity", "SCHEMA.json", f"{field} differs from {value!r}")
    if schema_names != EXPECTED_HEADER:
        fail("schema_header", "SCHEMA.json", f"expected {EXPECTED_HEADER!r}, got {schema_names!r}")
    shape = schema.get("shape", {})
    if shape.get("data_rows") != 12 or shape.get("columns") != 5:
        fail("schema_shape", "SCHEMA.json", "expected 12 data rows and 5 columns")
    policy = schema.get("denominator_policy", {})
    if policy.get("primary", {}).get("column") != PRIMARY_DENOMINATOR_COLUMN:
        fail("primary_denominator_lock", "SCHEMA.json", "primary denominator is not Total_method_1")
    if policy.get("sensitivity", {}).get("column") != SECONDARY_DENOMINATOR_COLUMN:
        fail("secondary_denominator_lock", "SCHEMA.json", "secondary denominator is not Total_method_2")
    resolution = schema.get("documentation_resolution", {})
    if "lima" not in resolution.get("resolution", "").lower():
        fail("six_vs_five_resolution", "SCHEMA.json", "frozen five-column resolution is absent")
    dataset = provenance.get("dataset", {})
    if dataset.get("version_id") != 268230 or dataset.get("version_number") != 3:
        fail("provenance_version", "DATASET_PROVENANCE.json", "expected Dryad version 3 / ID 268230")
    if provenance.get("license", {}).get("identifier") != "CC0-1.0":
        fail("provenance_license", "DATASET_PROVENANCE.json", "expected CC0-1.0")
    rights_text = payloads["RIGHTS_EVIDENCE.md"].decode("utf-8")
    if "CC0-1.0" not in rights_text or "10.5061/dryad.573n5tbf3" not in rights_text:
        fail("rights_evidence_binding", "RIGHTS_EVIDENCE.md", "CC0 or DOI binding is absent")
    return payloads


def parse_raw_table(raw: bytes) -> list[dict[str, Any]]:
    relative_path = "raw/nest_propensity.csv"
    if raw.startswith(b"\xef\xbb\xbf"):
        fail("raw_no_bom", relative_path, "UTF-8 BOM is forbidden")
    if b"\x00" in raw:
        fail("raw_no_nul", relative_path, "NUL byte is forbidden")
    if not raw.endswith(b"\r\n"):
        fail("raw_final_newline", relative_path, "expected final CRLF")
    if raw.replace(b"\r\n", b"").find(b"\r") >= 0 or raw.replace(b"\r\n", b"").find(b"\n") >= 0:
        fail("raw_newline_style", relative_path, "expected CRLF only")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("raw_utf8", relative_path, str(exc))
    if any(ord(character) > 127 for character in text):
        fail("raw_ascii_subset", relative_path, "non-ASCII code point encountered")
    records = text.split("\r\n")
    if records[-1] != "":
        fail("raw_final_record", relative_path, "missing final empty split record")
    records = records[:-1]
    if len(records) != 13:
        fail("raw_record_count", relative_path, f"expected 13 physical records, got {len(records)}")
    try:
        parsed = list(csv.reader(records, strict=True))
    except csv.Error as exc:
        fail("raw_csv_parse", relative_path, str(exc))
    if parsed[0] != EXPECTED_HEADER:
        fail("raw_header", relative_path, f"expected {EXPECTED_HEADER!r}, got {parsed[0]!r}")
    data_records = parsed[1:]
    if len(data_records) != 12 or any(len(record) != 5 for record in data_records):
        fail("raw_shape", relative_path, "expected exactly 12 records with five fields each")

    rows: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, int]] = set()
    for source_record, tokens in enumerate(data_records, 1):
        for column, token in zip(EXPECTED_HEADER, tokens, strict=True):
            if token == "" or token != token.strip():
                fail("raw_missing_or_whitespace", relative_path, f"record {source_record}, column {column}")
        transmitter = tokens[0]
        if transmitter not in GROUP_RANK:
            fail("raw_group_domain", relative_path, f"record {source_record}: {transmitter!r}")
        parsed_ints: list[int] = []
        for column, token in zip(EXPECTED_HEADER[1:], tokens[1:], strict=True):
            if not INTEGER_TOKEN.fullmatch(token):
                fail("raw_integer_grammar", relative_path, f"record {source_record}, column {column}: {token!r}")
            number = int(token, 10)
            if number > INT64_MAX:
                fail("raw_int64_overflow", relative_path, f"record {source_record}, column {column}")
            parsed_ints.append(number)
        year, successes, primary, secondary = parsed_ints
        key = (transmitter, year)
        if key in seen_keys:
            fail("raw_unique_group_year", relative_path, f"duplicate key {key!r}")
        seen_keys.add(key)
        if key not in EXPECTED_CELL_SOURCE_RECORDS:
            fail("raw_cell_inventory", relative_path, f"unexpected key {key!r}")
        if EXPECTED_CELL_SOURCE_RECORDS[key] != source_record:
            fail("raw_source_record_mapping", relative_path, f"key {key!r} appears at record {source_record}")
        if not (0 <= successes <= primary <= secondary and primary > 0 and secondary > 0):
            fail(
                "raw_binomial_domain",
                relative_path,
                f"record {source_record}: require 0 <= y <= n_primary <= n_secondary and positive denominators",
            )
        rows.append(
            {
                "cell_id": f"CP02-{transmitter}-{year}",
                "source_record": source_record,
                "transmitter": transmitter,
                "year": year,
                "nests_initiated": successes,
                "hens_available_primary": primary,
                "hens_available_secondary": secondary,
            }
        )
    if seen_keys != set(EXPECTED_CELL_SOURCE_RECORDS):
        fail("raw_cell_inventory", relative_path, "expected cell set is incomplete")
    rows.sort(key=lambda row: (row["year"], GROUP_RANK[row["transmitter"]]))
    for cell_order, row in enumerate(rows, 1):
        row["cell_order"] = cell_order
    return rows


def column_manifest(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specifications = [
        ("", "", 1, "cell_id", "trace_id", "stable cell identifier", "string", "CP02-{VHF|PTT}-{year}", "derived from transmitter and year"),
        ("", "", 2, "source_record", "trace_record", "one-based source data record", "int64", "1..12", "one-based physical data-record position"),
        ("", "", 3, "cell_order", "canonical_order", "canonical analysis row order", "int64", "1..12", "sort by year then group rank VHF=0,PTT=1"),
        (1, "Transmitter", 4, "transmitter", "group", "published transmitter group", "categorical_string", "VHF|PTT", "exact rename; no case folding"),
        (2, "Year", 5, "year", "time", "published study year", "int64", "frozen cell inventory 2015..2022", "canonical unsigned decimal to int64"),
        (3, "No_nests", 6, "nests_initiated", "success_count", "nests initiated in the aggregate cell", "int64", "0<=y<=n_primary", "canonical unsigned decimal to int64"),
        (4, "Total_method_1", 7, "hens_available_primary", "primary_trial_count", "conservative hens-available denominator", "int64", "positive; y<=n_primary<=n_secondary", "canonical unsigned decimal to int64"),
        (5, "Total_method_2", 8, "hens_available_secondary", "secondary_trial_count", "liberal hens-available denominator", "int64", "positive; n_secondary>=n_primary", "canonical unsigned decimal to int64"),
    ]
    output: list[dict[str, Any]] = []
    for source_position, source_name, clean_position, clean_name, role, definition, semantic_type, domain, transformation in specifications:
        values = [row[clean_name] for row in rows]
        canonical_column = (clean_name + "\n" + "".join(f"{value}\n" for value in values)).encode("utf-8")
        output.append(
            {
                "source_position": source_position,
                "source_name": source_name,
                "clean_position": clean_position,
                "clean_name": clean_name,
                "semantic_role": role,
                "definition": definition,
                "semantic_type": semantic_type,
                "domain": domain,
                "allowed_missing_codes": "none",
                "transformation": transformation,
                "missing_count": 0,
                "unique_count": len({str(value) for value in values}),
                "canonical_column_sha256": sha256_bytes(canonical_column),
            }
        )
    return output


def output_inventory(payloads: dict[str, bytes], roles: dict[str, str]) -> list[dict[str, Any]]:
    return [
        {
            "path": path,
            "role": roles[path],
            "bytes": len(payloads[path]),
            "sha256": sha256_bytes(payloads[path]),
        }
        for path in sorted(payloads)
    ]


def build_expected_payload() -> tuple[dict[str, bytes], bytes]:
    input_manifest = verify_input_manifest()
    metadata = verify_contract_metadata()
    raw_payloads = {
        path: read_verified_bytes(path, expected)
        for path, expected in RAW_IDENTITIES.items()
    }
    readme = raw_payloads["raw/README.md"]
    if readme.startswith(b"\xef\xbb\xbf") or b"\x00" in readme or b"\r" in readme or not readme.endswith(b"\n"):
        fail("dictionary_encoding_newlines", "raw/README.md", "expected UTF-8 ASCII subset, LF, final newline, no BOM/NUL")
    try:
        readme_text = readme.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("dictionary_utf8", "raw/README.md", str(exc))
    if any(ord(character) > 127 for character in readme_text):
        fail("dictionary_ascii_subset", "raw/README.md", "non-ASCII code point encountered")
    if "6 columns" not in readme_text or "Total_method_1" not in readme_text or "Total_method_2" not in readme_text:
        fail("dictionary_six_vs_five_evidence", "raw/README.md", "frozen discrepancy or denominator definitions absent")

    # The denominator lock above is completed before outcome tokens are parsed.
    rows = parse_raw_table(raw_payloads["raw/nest_propensity.csv"])
    clean_payload = csv_bytes(CLEAN_HEADER, rows)

    row_rows: list[dict[str, Any]] = []
    for clean_record, row in enumerate(rows, 1):
        row_rows.append(
            {
                "cell_id": row["cell_id"],
                "source_record": row["source_record"],
                "source_line": row["source_record"] + 1,
                "clean_record": clean_record,
                "transmitter": row["transmitter"],
                "year": row["year"],
                "canonical_row_sha256": sha256_bytes(one_csv_record([row[field] for field in CLEAN_HEADER])),
                "disposition": "kept",
                "exclusion_reason": "",
            }
        )
    row_header = [
        "cell_id",
        "source_record",
        "source_line",
        "clean_record",
        "transmitter",
        "year",
        "canonical_row_sha256",
        "disposition",
        "exclusion_reason",
    ]
    column_header = [
        "source_position",
        "source_name",
        "clean_position",
        "clean_name",
        "semantic_role",
        "definition",
        "semantic_type",
        "domain",
        "allowed_missing_codes",
        "transformation",
        "missing_count",
        "unique_count",
        "canonical_column_sha256",
    ]
    core_payloads = {
        "CP02_cells_clean.csv": clean_payload,
        "ROW_MANIFEST.csv": csv_bytes(row_header, row_rows),
        "COLUMN_MANIFEST.csv": csv_bytes(column_header, column_manifest(rows)),
    }
    core_roles = {
        "CP02_cells_clean.csv": "canonical_clean_table",
        "ROW_MANIFEST.csv": "source_to_clean_row_lineage",
        "COLUMN_MANIFEST.csv": "source_to_clean_column_lineage",
    }
    ledger = {
        "schema": "o006.c140.cp02-transform-ledger.v1",
        "contract": {
            "source_rows": 12,
            "source_columns": 5,
            "clean_rows": 12,
            "clean_columns": 8,
            "primary_denominator_column": PRIMARY_DENOMINATOR_COLUMN,
            "secondary_denominator_column": SECONDARY_DENOMINATOR_COLUMN,
            "denominator_locked_before_outcome_parse": True,
            "raw_assets_immutable": True,
            "numeric_input_allowlist": ["raw/nest_propensity.csv"],
        },
        "input_hashes_before_parse": [
            {
                "path": path,
                "bytes": len(raw_payloads[path]),
                "sha256": sha256_bytes(raw_payloads[path]),
            }
            for path in sorted(raw_payloads)
        ],
        "steps": [
            {"order": 1, "operation": "verify_manifest_metadata_and_rights", "rows_before": 12, "rows_after": 12},
            {"order": 2, "operation": "lock_primary_and_secondary_denominators", "rows_before": 12, "rows_after": 12},
            {"order": 3, "operation": "parse_exact_five_field_records_as_strings", "rows_before": 12, "rows_after": 12},
            {"order": 4, "operation": "validate_missing_integer_domain_and_unique_keys", "rows_before": 12, "rows_after": 12},
            {"order": 5, "operation": "rename_and_convert_canonical_integer_types", "rows_before": 12, "rows_after": 12},
            {"order": 6, "operation": "derive_trace_fields_and_sort_year_then_group_rank", "rows_before": 12, "rows_after": 12},
            {"order": 7, "operation": "serialize_lf_utf8_no_bom_and_verify", "rows_before": 12, "rows_after": 12},
        ],
        "renames": dict(zip(EXPECTED_HEADER, CLEAN_HEADER[3:], strict=True)),
        "type_conversions": {
            "Year": "canonical unsigned decimal token -> int64",
            "No_nests": "canonical unsigned decimal token -> int64",
            "Total_method_1": "canonical unsigned decimal token -> int64",
            "Total_method_2": "canonical unsigned decimal token -> int64",
        },
        "sorting": {"keys": ["year ascending", "group_rank ascending"], "group_rank": GROUP_RANK},
        "exclusions": [],
        "imputation": False,
        "assertions": {
            "all_rows_five_fields": True,
            "all_tokens_nonmissing_and_untrimmed": True,
            "all_integer_tokens_canonical_int64": True,
            "all_rows_binomial_domain": True,
            "all_group_year_keys_unique": True,
            "expected_cell_inventory_exact": True,
            "source_to_clean_bijection": True,
            "row_count_preserved_12": True,
            "primary_secondary_never_combined": True,
            "raw_hashes_unchanged_after_serialization": True,
        },
        "outputs": output_inventory(core_payloads, core_roles),
        "recursive_container_note": "The ledger binds the three lineage/data payloads; clean/MANIFEST.csv binds this ledger, and the external receipt binds the manifest.",
    }
    core_payloads["TRANSFORM_LEDGER.json"] = canonical_json_bytes(ledger)
    core_roles["TRANSFORM_LEDGER.json"] = "canonical_transform_ledger"

    manifest_rows = output_inventory(core_payloads, core_roles)
    manifest_header = ["path", "role", "bytes", "sha256"]
    clean_payloads = dict(core_payloads)
    clean_payloads["MANIFEST.csv"] = csv_bytes(manifest_header, manifest_rows)
    clean_roles = dict(core_roles)
    clean_roles["MANIFEST.csv"] = "clean_directory_manifest"

    for path, expected in RAW_IDENTITIES.items():
        after = (DATA_ROOT / path).read_bytes()
        if sha256_bytes(after) != expected["sha256"] or len(after) != expected["bytes"]:
            fail("raw_hash_after_transform", path, "raw bytes changed during in-memory construction")

    input_inventory = [
        {
            "path": f"data/capstones/CP02/{path}",
            "role": RAW_IDENTITIES[path]["role"],
            "bytes": len(raw_payloads[path]),
            "sha256": sha256_bytes(raw_payloads[path]),
        }
        for path in sorted(raw_payloads)
    ]
    for relative_path, payload in sorted(metadata.items()):
        input_inventory.append(
            {
                "path": f"data/capstones/CP02/{relative_path}",
                "role": "frozen_contract_metadata",
                "bytes": len(payload),
                "sha256": sha256_bytes(payload),
            }
        )
    input_inventory.append(
        {
            "path": "data/capstones/CP02/INPUT_MANIFEST.csv",
            "role": "frozen_input_manifest",
            "bytes": len(input_manifest),
            "sha256": sha256_bytes(input_manifest),
        }
    )
    input_inventory.sort(key=lambda item: item["path"])

    complete_output_inventory = output_inventory(clean_payloads, clean_roles)
    producer_code = SCRIPT_PATH.read_bytes()
    receipt = {
        "schema": SCHEMA_ID,
        "status": "pass",
        "code": [
            {
                "path": "data/capstones/CP02/transform_cp02.py",
                "bytes": len(producer_code),
                "sha256": sha256_bytes(producer_code),
            }
        ],
        "contract": {
            "mode_interface": ["--write", "--check-only"],
            "source_shape": {"rows": 12, "columns": 5},
            "clean_shape": {"rows": 12, "columns": 8},
            "primary_denominator_column": PRIMARY_DENOMINATOR_COLUMN,
            "secondary_denominator_column": SECONDARY_DENOMINATOR_COLUMN,
            "raw_assets_immutable": True,
        },
        "inputs": input_inventory,
        "environment": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
            "stdlib_only": True,
        },
        "assertions": {
            "input_hashes_verified_before_parse": True,
            "input_hashes_verified_after_payload_build": True,
            "rights_and_provenance_verified": True,
            "schema_header_shape_and_discrepancy_verified": True,
            "denominator_locked_before_outcome_parse": True,
            "integer_missing_domain_and_uniqueness_checks_passed": True,
            "source_to_clean_bijection_verified": True,
            "canonical_order_verified": True,
            "no_imputation_aggregation_or_exclusion": True,
            "manifest_excludes_only_itself": True,
        },
        "outputs": complete_output_inventory,
        "manifest": {
            "path": "data/capstones/CP02/clean/MANIFEST.csv",
            "closure": "lists every other file in clean/ and excludes only itself",
            "bytes": len(clean_payloads["MANIFEST.csv"]),
            "sha256": sha256_bytes(clean_payloads["MANIFEST.csv"]),
        },
        "replay": {
            "check_only_writes": False,
            "comparison": "exact relative path and byte identity",
            "required_external_check_only_replays": 2,
        },
        "network_access": False,
        "browser_processes_used": False,
    }
    return clean_payloads, canonical_json_bytes(receipt)


def verify_exact_directory(root: Path, expected: dict[str, bytes], label: str) -> None:
    if not root.is_dir():
        fail("check_output_directory", label, "directory is missing")
    actual_names = sorted(path.name for path in root.iterdir() if path.is_file())
    expected_names = sorted(expected)
    if actual_names != expected_names:
        fail("check_output_inventory", label, f"expected {expected_names!r}, got {actual_names!r}")
    non_files = [path.name for path in root.iterdir() if not path.is_file()]
    if non_files:
        fail("check_output_inventory", label, f"unexpected non-files: {sorted(non_files)!r}")
    for name in expected_names:
        actual = (root / name).read_bytes()
        if actual != expected[name]:
            fail(
                "check_output_bytes",
                f"{label}/{name}",
                f"expected sha256 {sha256_bytes(expected[name])}, got {sha256_bytes(actual)}",
            )


def preflight_clean_directory(expected_names: set[str]) -> None:
    if not CLEAN_ROOT.exists():
        return
    if not CLEAN_ROOT.is_dir():
        fail("write_clean_directory", "clean", "path exists and is not a directory")
    unexpected = sorted(path.name for path in CLEAN_ROOT.iterdir() if path.name not in expected_names)
    if unexpected:
        fail("write_clean_inventory", "clean", f"unexpected existing entries: {unexpected!r}")


def atomic_write_many(clean_payloads: dict[str, bytes], receipt_payload: bytes) -> None:
    preflight_clean_directory(set(clean_payloads))
    CLEAN_ROOT.mkdir(parents=True, exist_ok=True)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    targets: list[tuple[Path, bytes]] = [
        (CLEAN_ROOT / name, payload) for name, payload in sorted(clean_payloads.items())
    ]
    targets.append((RECEIPT_PATH, receipt_payload))
    temporary: list[tuple[Path, Path]] = []
    try:
        for target, payload in targets:
            temp = target.with_name(f".{target.name}.cp02-transform.tmp")
            if temp.exists():
                fail("write_temporary_absent", target.name, f"stale temporary file {temp.name!r}")
            temp.write_bytes(payload)
            if temp.read_bytes() != payload:
                fail("write_temporary_verify", target.name, "temporary byte readback differs")
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
    mode.add_argument("--write", action="store_true", help="write the canonical clean payload and receipt")
    mode.add_argument("--check-only", action="store_true", help="compare canonical bytes without writing")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        clean_payloads, receipt_payload = build_expected_payload()
        if args.write:
            atomic_write_many(clean_payloads, receipt_payload)
            verify_exact_directory(CLEAN_ROOT, clean_payloads, "data/capstones/CP02/clean")
            if RECEIPT_PATH.read_bytes() != receipt_payload:
                fail("write_receipt_verify", "build/CP02_TRANSFORM_RECEIPT.json", "byte readback differs")
            mode = "write"
        else:
            verify_exact_directory(CLEAN_ROOT, clean_payloads, "data/capstones/CP02/clean")
            if not RECEIPT_PATH.is_file():
                fail("check_receipt_present", "build/CP02_TRANSFORM_RECEIPT.json", "file is missing")
            actual_receipt = RECEIPT_PATH.read_bytes()
            if actual_receipt != receipt_payload:
                fail(
                    "check_receipt_bytes",
                    "build/CP02_TRANSFORM_RECEIPT.json",
                    f"expected {sha256_bytes(receipt_payload)}, got {sha256_bytes(actual_receipt)}",
                )
            mode = "check-only"
        print(
            json.dumps(
                {
                    "status": "ok",
                    "mode": mode,
                    "schema": SCHEMA_ID,
                    "clean_files": len(clean_payloads),
                    "manifest_sha256": sha256_bytes(clean_payloads["MANIFEST.csv"]),
                    "receipt_sha256": sha256_bytes(receipt_payload),
                    "writes_performed": bool(args.write),
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except ContractError as exc:
        print(f"CP02 transform contract failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
