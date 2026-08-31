#!/usr/bin/env python3
"""Check CP01's floating transform certificate without rewriting frozen artifacts.

This is a separate, explicitly portable numerical check, not a byte-exact
producer replay.  Only float leaves in eight explicitly named computed fields
of the CP01 ledger's conditioning certificate may differ, by at most 1e-12
relative error and zero absolute tolerance.  Normative constants, source
identities, discrete data, other output bytes, and receipt fields stay exact.
The original CP01/CP02 analysis checks remain separate and unchanged.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
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


def main() -> None:
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
    main()
