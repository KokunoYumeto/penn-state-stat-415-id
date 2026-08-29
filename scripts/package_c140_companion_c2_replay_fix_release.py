#!/usr/bin/env python3
"""Package the cross-platform C2 receipt repair without changing C2 content.

The publication payload is the exact current 41-file C2 union produced by
``package_c140_companion_c2_release.py``.  This wrapper adds a new, narrowly
versioned package receipt and proves which files differ from public Zenodo
record 22151570.  It performs no network, credential, browser, Git, or remote
publication operation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import package_c140_companion_c2_release as c2


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
LIVE_RECEIPT = ROOT / "build" / "C140_COMPANION_C2_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = (
    ROOT / "build" / "C140_COMPANION_C2_REPLAY_FIX_RELEASE_PACKAGE_RECEIPT.json"
)
BASE_READBACK = (
    ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-29_C140_COMPANION_C2.json"
)

VERSION = "2026.08.29.c140-companion-c2-replay-fix"
SCHEMA = "o006.c140.companion-c2-replay-fix-release-package.v1"
BASE_RECORD_ID = "22151570"
BASE_VERSION = "2026.08.29.c140-companion-c2"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"

EXPECTED_LIVE_RECEIPT_BYTES = 23_679
EXPECTED_LIVE_RECEIPT_SHA256 = (
    "755e15161e06636e9c19030560966a506ca59ba490140a76f83c16b499f8c197"
)
EXPECTED_LIVE_FILES = 41
EXPECTED_LIVE_BYTES = 91_249_199
EXPECTED_BASE_READBACK_BYTES = 16_411
EXPECTED_BASE_READBACK_SHA256 = (
    "9b0a15b281167d85c0d768b0572aa93317c6d34f3f68877c447ba2031255bd74"
)
EXPECTED_BASE_BYTES = 91_249_203

REPAIR_STATEMENT = (
    "Deterministic cross-platform receipt repair only: pedagogical C2 "
    "source, prose, formulas, and substantive SIM005 CSV/SVG outputs are "
    "unchanged; only generator-receipt quantization and dependent manifests, "
    "receipts, and QA archives changed."
)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _rows_from_package(package: dict[str, Any], label: str) -> list[dict[str, Any]]:
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise RuntimeError(f"{label} publication inventory is malformed")
    return rows


def live_contract() -> tuple[dict[str, bytes], bytes, dict[str, Any], list[dict[str, Any]]]:
    outputs, receipt = c2.compute()
    if (
        len(receipt) != EXPECTED_LIVE_RECEIPT_BYTES
        or sha256(receipt) != EXPECTED_LIVE_RECEIPT_SHA256
        or not LIVE_RECEIPT.is_file()
        or LIVE_RECEIPT.read_bytes() != receipt
    ):
        raise RuntimeError("live corrected C2 package receipt identity differs")
    package = json.loads(receipt)
    rows = _rows_from_package(package, "live C2")
    publication = package["publication_inventory"]
    if (
        package.get("schema") != c2.SCHEMA
        or package.get("status") != "ready"
        or len(rows) != EXPECTED_LIVE_FILES
        or publication.get("file_count") != EXPECTED_LIVE_FILES
        or publication.get("bytes") != EXPECTED_LIVE_BYTES
        or tuple(row.get("filename") for row in rows) != tuple(outputs)
    ):
        raise RuntimeError("live corrected C2 package boundary differs")
    for index, row in enumerate(rows, start=1):
        name = str(row.get("filename", ""))
        payload = outputs.get(name)
        if (
            row.get("upload_order") != index
            or row.get("source_path") != f"release/{name}"
            or payload is None
            or len(payload) != row.get("bytes")
            or sha256(payload) != row.get("sha256")
        ):
            raise RuntimeError(f"live corrected C2 asset differs: {name}")
    return outputs, receipt, package, rows


def base_specs() -> tuple[tuple[str, int, str], ...]:
    payload = BASE_READBACK.read_bytes()
    if (
        len(payload) != EXPECTED_BASE_READBACK_BYTES
        or sha256(payload) != EXPECTED_BASE_READBACK_SHA256
    ):
        raise RuntimeError("public C2 Zenodo readback witness identity differs")
    witness = json.loads(payload)
    public = witness.get("public")
    files = public.get("files") if isinstance(public, dict) else None
    if (
        not isinstance(files, list)
        or public.get("record_id") != BASE_RECORD_ID
        or public.get("doi") != f"10.5281/zenodo.{BASE_RECORD_ID}"
        or public.get("version") != BASE_VERSION
        or public.get("concept_record_id") != CONCEPT_RECORD_ID
        or public.get("concept_doi") != CONCEPT_DOI
        or public.get("file_count") != EXPECTED_LIVE_FILES
        or public.get("total_bytes") != EXPECTED_BASE_BYTES
    ):
        raise RuntimeError("public C2 Zenodo readback contract differs")
    specs: list[tuple[str, int, str]] = []
    for row in files:
        if not isinstance(row, dict):
            raise RuntimeError("public C2 Zenodo file row is malformed")
        specs.append((str(row.get("name")), int(row.get("bytes", -1)), str(row.get("sha256"))))
    if len({name for name, _size, _digest in specs}) != EXPECTED_LIVE_FILES:
        raise RuntimeError("public C2 Zenodo filenames are duplicated")
    return tuple(specs)


def compute() -> tuple[dict[str, bytes], bytes]:
    outputs, live_receipt, live_package, rows = live_contract()
    base = base_specs()
    base_map = {name: (size, digest) for name, size, digest in base}
    if tuple(base_map) != tuple(row["filename"] for row in rows):
        raise RuntimeError("public C2 base and corrected union orders differ")
    changed = [
        str(row["filename"])
        for row in rows
        if base_map[str(row["filename"])] != (int(row["bytes"]), str(row["sha256"]))
    ]
    unchanged = [str(row["filename"]) for row in rows if str(row["filename"]) not in changed]
    expected_changed = [
        c2.OFFLINE_NAME,
        c2.SOURCE_NAME,
        c2.NOTES_NAME,
        c2.QA_NAME,
        c2.MANIFEST_NAME,
        c2.CHECKSUM_NAME,
        c2.ROOT_NAME,
    ]
    if changed != expected_changed or len(unchanged) != 34:
        raise RuntimeError(f"corrective replacement set differs: {changed}")
    receipt = canonical_json({
        "base_public_inventory": {
            "bytes": EXPECTED_BASE_BYTES,
            "file_count": EXPECTED_LIVE_FILES,
            "record_id": BASE_RECORD_ID,
            "version": BASE_VERSION,
        },
        "coverage": live_package.get("coverage"),
        "gates": {
            "browser_processes_used": False,
            "credential_access": False,
            "git_operations": False,
            "live_corrected_c2": {
                "bytes": EXPECTED_LIVE_BYTES,
                "file_count": EXPECTED_LIVE_FILES,
                "receipt_bytes": len(live_receipt),
                "receipt_sha256": sha256(live_receipt),
                "status": "pass",
            },
            "network_access": False,
            "publication_side_effects": False,
        },
        "lineage": {
            "base_record_doi": f"10.5281/zenodo.{BASE_RECORD_ID}",
            "base_record_id": BASE_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "concept_record_id": CONCEPT_RECORD_ID,
            "create_competing_concept": False,
        },
        "packager": "scripts/package_c140_companion_c2_replay_fix_release.py",
        "publication_inventory": {
            "bytes": EXPECTED_LIVE_BYTES,
            "file_count": EXPECTED_LIVE_FILES,
            "files": rows,
        },
        "repair": {
            "changed_file_count": len(changed),
            "changed_filenames": changed,
            "statement": REPAIR_STATEMENT,
            "substantive_sim005_outputs_unchanged": True,
            "pedagogical_content_unchanged": True,
            "unchanged_file_count": len(unchanged),
            "unchanged_filenames": unchanged,
        },
        "rights": live_package.get("rights"),
        "schema": SCHEMA,
        "status": "ready",
        "version": VERSION,
    })
    return outputs, receipt


def verify_outputs(outputs: dict[str, bytes], receipt: bytes) -> list[str]:
    errors: list[str] = []
    for name, payload in outputs.items():
        path = RELEASE / name
        if not path.is_file():
            errors.append(f"missing:{name}")
        elif path.read_bytes() != payload:
            errors.append(f"mismatch:{name}")
    if not PACKAGE_RECEIPT.is_file():
        errors.append("missing:package-receipt")
    elif PACKAGE_RECEIPT.read_bytes() != receipt:
        errors.append("mismatch:package-receipt")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--contract-only", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs, receipt = compute()
    package = json.loads(receipt)
    if args.write:
        RELEASE.mkdir(parents=True, exist_ok=True)
        for name, payload in outputs.items():
            (RELEASE / name).write_bytes(payload)
        PACKAGE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        PACKAGE_RECEIPT.write_bytes(receipt)
        state = "written"
    elif args.check_only:
        errors = verify_outputs(outputs, receipt)
        if errors:
            raise RuntimeError("corrective package replay differs: " + ", ".join(errors[:40]))
        state = "verified"
    else:
        state = "contract-only"
    print(json.dumps({
        "base_record_id": BASE_RECORD_ID,
        "bytes": package["publication_inventory"]["bytes"],
        "changed_files": package["repair"]["changed_file_count"],
        "credential_access": False,
        "files": package["publication_inventory"]["file_count"],
        "mode": state,
        "network_access": False,
        "receipt_sha256": sha256(receipt),
        "status": "pass",
        "version": VERSION,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
