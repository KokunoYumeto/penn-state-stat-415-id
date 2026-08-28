#!/usr/bin/env python3
"""Package the cumulative Penn + donor + original companion C1 checkpoint."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "c140-companion"
RELEASE = ROOT / "release"
PRIOR_RECEIPT = ROOT / "build" / "RANDOM_COMPLETENESS_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C1_RELEASE_PACKAGE_RECEIPT.json"

OFFLINE_NAME = "02_C140_COMPANION_C1_OFFLINE_READER.zip"
SOURCE_NAME = "12_C140_COMPANION_C1_SOURCE_BACKEND.zip"
NOTES_NAME = "22_C140_COMPANION_C1_RELEASE_NOTES.md"
LICENSE_NAME = "32_C140_COMPANION_C1_LICENSE.md"
QA_NAME = "42_C140_COMPANION_C1_STATIC_QA_EVIDENCE.zip"
MANIFEST_NAME = "90_C140_COMPANION_C1_FULL_UNION_MANIFEST.csv"
CHECKSUM_NAME = "SHA256SUMS_C140_COMPANION_C1.txt"
ROOT_NAME = "91_C140_COMPANION_C1_FULL_UNION_ROOT_RECEIPT.json"

ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
PRIVACY_PATTERNS = {
    "windows_user_path": re.compile(rb"[A-Za-z]:\\Users\\", re.IGNORECASE),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential_assignment": re.compile(
        rb"(?:api[_-]?key|access[_-]?token|password)\s*[:=]\s*[^\s<]+",
        re.IGNORECASE,
    ),
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_bytes(fieldnames: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def validate_relative(name: str) -> None:
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"unsafe archive path: {name}")
    if path.as_posix() != name or "\\" in name:
        raise RuntimeError(f"non-canonical archive path: {name}")


def privacy_findings(name: str, payload: bytes) -> list[str]:
    suffix = PurePosixPath(name).suffix.casefold()
    if suffix not in {".md", ".txt", ".json", ".jsonl", ".csv", ".py", ".html", ".css", ".js", ".svg"}:
        return []
    return [label for label, pattern in PRIVACY_PATTERNS.items() if pattern.search(payload)]


def deterministic_zip(entries: dict[str, bytes], *, inventory_name: str) -> tuple[bytes, dict[str, Any]]:
    if inventory_name in entries:
        raise RuntimeError(f"inventory collision: {inventory_name}")
    inventory_rows = []
    findings = []
    for name, payload in sorted(entries.items()):
        validate_relative(name)
        inventory_rows.append({"entry": name, "bytes": len(payload), "sha256": sha256(payload)})
        for finding in privacy_findings(name, payload):
            findings.append({"entry": name, "finding": finding})
    if findings:
        raise RuntimeError(f"privacy findings in archive inputs: {findings}")
    inventory_payload = canonical_json({
        "entries": inventory_rows,
        "entry_count": len(inventory_rows),
        "schema": "o006.c140.companion-c1-archive-inventory.v1",
        "status": "pass",
        "total_bytes": sum(int(row["bytes"]) for row in inventory_rows),
    })
    combined = dict(entries)
    combined[inventory_name] = inventory_payload
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(combined.items()):
            info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        names = archive.namelist()
        expected = sorted(combined)
        if names != expected:
            raise RuntimeError(f"archive order/inventory differs: {inventory_name}")
        for name in names:
            if archive.read(name) != combined[name]:
                raise RuntimeError(f"archive payload differs: {name}")
        if archive.testzip() is not None:
            raise RuntimeError("archive CRC verification failed")
    return payload, {
        "archive_method": "ZIP_DEFLATED level 9; fixed 1980-01-01 timestamps; canonical entry order",
        "bytes": len(payload),
        "entries": len(combined),
        "inventory": {"entry": inventory_name, "bytes": len(inventory_payload), "sha256": sha256(inventory_payload)},
        "sha256": sha256(payload),
        "uncompressed_bytes": sum(len(value) for value in combined.values()),
        "privacy": {"forbidden_markers_found": 0},
    }


def files_from_directory(root: Path, prefix: str = "") -> dict[str, bytes]:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"missing or unsafe directory: {root}")
    result: dict[str, bytes] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"symlink in package input: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        name = f"{prefix}/{relative}" if prefix else relative
        validate_relative(name)
        result[name] = path.read_bytes()
    return result


def exact_files(paths: Iterable[tuple[str, Path]]) -> dict[str, bytes]:
    result: dict[str, bytes] = {}
    for name, path in paths:
        validate_relative(name)
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"missing or unsafe file: {path}")
        if name in result:
            raise RuntimeError(f"duplicate package entry: {name}")
        result[name] = path.read_bytes()
    return result


def release_notes() -> bytes:
    return (
        "# C140 original companion — C1 checkpoint\n\n"
        "Status: **partial but coherent**. The Penn State STAT 415 Indonesian "
        "spine and exact Random completeness donor remain complete; this version "
        "adds the first substantive original CC BY-SA 4.0 companion boundary.\n\n"
        "C1 contains seven rigorous chapters on regular likelihood, MLE "
        "asymptotics, delta method, Wald/score/LR/Wilks, nonregular cases, "
        "Neyman–Pearson/UMP, risk, efficiency, Rao–Blackwell, and "
        "Lehmann–Scheffé; four seeded simulations; four mastery sets with 32 "
        "fully solved problems; and one ten-problem cumulative assessment with "
        "a 100-point rubric.\n\n"
        "The offline reader has 35 files / 2,265,015 bytes. Its machine backend "
        "has 469 entities and 648 relations. Deterministic build, numerical, "
        "reference, mathematics, rights, privacy, static accessibility/reflow, "
        "archive, and byte-replay gates pass. Two bounded post-fix mathematical "
        "audits report no remaining high-confidence defect. No browser process "
        "was launched.\n\n"
        "Overall C140 remains incomplete: matrix Gaussian linear models, the "
        "Bayesian–frequentist comparison, remaining simulations, nine mastery "
        "sets, three cumulative assessments, and two capstones still remain.\n\n"
        "Production provenance: `OpenAI Codex gpt-5.6-sol, Ultra`. Penn State, "
        "Random, and original-companion rights remain component-separated.\n"
    ).encode("utf-8")


def media_type(name: str) -> str:
    suffix = PurePosixPath(name).suffix.casefold()
    return {
        ".pdf": "application/pdf",
        ".epub": "application/epub+zip",
        ".zip": "application/zip",
        ".md": "text/markdown",
        ".json": "application/json",
        ".csv": "text/csv",
        ".txt": "text/plain",
    }.get(suffix, "application/octet-stream")


def entry(filename: str, payload: bytes, *, role: str, lineage: str, primary: bool = False) -> dict[str, object]:
    return {
        "bytes": len(payload),
        "filename": filename,
        "lineage": lineage,
        "media_type": media_type(filename),
        "primary_reader": primary,
        "role": role,
        "sha256": sha256(payload),
        "source_path": f"release/{filename}",
    }


def compute() -> tuple[dict[str, bytes], bytes]:
    prior = json.loads(PRIOR_RECEIPT.read_text(encoding="utf-8"))
    prior_rows = prior["publication_inventory"]["files"]
    if len(prior_rows) != 25:
        raise RuntimeError("prior cumulative release does not contain exactly 25 files")
    outputs: dict[str, bytes] = {}
    rows: list[dict[str, object]] = []
    for expected_order, row in enumerate(prior_rows, start=1):
        filename = str(row["filename"])
        path = ROOT / str(row["source_path"])
        payload = path.read_bytes()
        if (
            row.get("upload_order") != expected_order
            or len(payload) != int(row["bytes"])
            or sha256(payload) != row["sha256"]
        ):
            raise RuntimeError(f"prior release identity differs: {filename}")
        outputs[filename] = payload
        retained = dict(row)
        rows.append(retained)

    offline_entries = files_from_directory(COMPONENT / "build" / "html-id")
    offline_payload, offline_gate = deterministic_zip(
        offline_entries, inventory_name="OFFLINE_READER_INVENTORY.json"
    )

    source_entries: dict[str, bytes] = {}
    source_entries.update(exact_files([
        ("README.md", COMPONENT / "README.md"),
        ("LICENSE.md", COMPONENT / "LICENSE.md"),
        ("environment.lock.json", COMPONENT / "environment.lock.json"),
        ("simulations/run_c1_simulations.py", COMPONENT / "simulations" / "run_c1_simulations.py"),
        ("scripts/build_companion.py", COMPONENT / "scripts" / "build_companion.py"),
        ("scripts/qa_companion.py", COMPONENT / "scripts" / "qa_companion.py"),
        ("build/C1_SIMULATION_RECEIPT.json", COMPONENT / "build" / "C1_SIMULATION_RECEIPT.json"),
        ("build/C1_BUILD_RECEIPT.json", COMPONENT / "build" / "C1_BUILD_RECEIPT.json"),
        ("build/C1_QA_RECEIPT.json", COMPONENT / "build" / "C1_QA_RECEIPT.json"),
    ]))
    source_entries.update(files_from_directory(COMPONENT / "00_control", "00_control"))
    source_entries.update(files_from_directory(COMPONENT / "source" / "id-ID", "source/id-ID"))
    source_entries.update(files_from_directory(COMPONENT / "generated" / "simulations" / "c1", "generated/simulations/c1"))
    source_entries.update(files_from_directory(COMPONENT / "backend", "backend"))
    source_payload, source_gate = deterministic_zip(
        source_entries, inventory_name="SOURCE_BACKEND_PACKAGE_INVENTORY.json"
    )

    qa_entries = exact_files([
        ("environment.lock.json", COMPONENT / "environment.lock.json"),
        ("C1_SIMULATION_RECEIPT.json", COMPONENT / "build" / "C1_SIMULATION_RECEIPT.json"),
        ("C1_BUILD_RECEIPT.json", COMPONENT / "build" / "C1_BUILD_RECEIPT.json"),
        ("C1_QA_RECEIPT.json", COMPONENT / "build" / "C1_QA_RECEIPT.json"),
        ("HTML_MANIFEST.csv", COMPONENT / "build" / "html-id" / "MANIFEST.csv"),
        ("BACKEND_MANIFEST.csv", COMPONENT / "backend" / "MANIFEST.csv"),
        ("SIMULATION_MANIFEST.csv", COMPONENT / "generated" / "simulations" / "c1" / "MANIFEST.csv"),
        ("PAGES_COLLECTION_RECEIPT.json", ROOT / "build" / "PAGES_COLLECTION_RECEIPT.json"),
    ])
    qa_payload, qa_gate = deterministic_zip(
        qa_entries, inventory_name="QA_EVIDENCE_INVENTORY.json"
    )
    notes_payload = release_notes()
    license_payload = (COMPONENT / "LICENSE.md").read_bytes()

    new_items = [
        entry(OFFLINE_NAME, offline_payload, role="partial-c1-offline-html-reader", lineage="c140-original-companion-c1"),
        entry(SOURCE_NAME, source_payload, role="partial-c1-resumable-source-backend", lineage="c140-original-companion-c1"),
        entry(NOTES_NAME, notes_payload, role="partial-c1-scope-status-provenance", lineage="c140-original-companion-c1"),
        entry(LICENSE_NAME, license_payload, role="partial-c1-component-rights", lineage="c140-original-companion-c1"),
        entry(QA_NAME, qa_payload, role="partial-c1-browser-free-static-qa-evidence", lineage="c140-original-companion-c1"),
    ]
    for item, payload in zip(new_items, [offline_payload, source_payload, notes_payload, license_payload, qa_payload], strict=True):
        filename = str(item["filename"])
        if filename in outputs:
            raise RuntimeError(f"new release filename collides: {filename}")
        outputs[filename] = payload
        rows.append(item)

    for index, row in enumerate(rows, start=1):
        row["upload_order"] = index
    fields = ["upload_order", "filename", "bytes", "sha256", "role", "lineage", "media_type", "primary_reader", "source_path"]
    manifest_payload = csv_bytes(fields, rows)
    manifest_row = entry(MANIFEST_NAME, manifest_payload, role="c1-cumulative-union-manifest", lineage="c140-original-companion-c1-union")
    manifest_row["upload_order"] = len(rows) + 1
    outputs[MANIFEST_NAME] = manifest_payload

    checksum_covered = rows + [manifest_row]
    checksum_payload = "".join(
        f"{row['sha256']}  {row['filename']}\n" for row in checksum_covered
    ).encode("utf-8")
    checksum_row = entry(CHECKSUM_NAME, checksum_payload, role="c1-cumulative-union-checksums", lineage="c140-original-companion-c1-union")
    checksum_row["upload_order"] = len(rows) + 2
    outputs[CHECKSUM_NAME] = checksum_payload

    root_covered = rows + [manifest_row, checksum_row]
    root_payload = canonical_json({
        "concept_doi": "10.5281/zenodo.22077422",
        "coverage": {
            "c140_course": "incomplete after coherent original-companion C1 checkpoint",
            "c140_original_companion": "partial: D001-D007, SIM001-SIM004, MS07-MS10, CA01",
            "penn_state_spine": "complete: landing/index plus Lesson00-Lesson12",
            "random_completeness_donor": "complete: exact one-page donor",
        },
        "file_count": len(root_covered),
        "files": root_covered,
        "preservation": {
            "prior_files_byte_identical": True,
            "prior_file_count": 25,
            "new_substantive_file_count": 5,
        },
        "rights": {"aggregate_uniform_relicense": False, "platform_license": "other-open"},
        "schema": "o006.c140.companion-c1-full-union-root.v1",
        "self_exclusion": {"filename": ROOT_NAME, "reason": "non-self-referential cryptographic root"},
        "status": "ready",
        "total_bytes_excluding_self": sum(int(row["bytes"]) for row in root_covered),
        "version": "2026.08.28.c140-companion-c1",
    })
    root_row = entry(ROOT_NAME, root_payload, role="c1-cumulative-union-root-receipt", lineage="c140-original-companion-c1-union")
    root_row["upload_order"] = len(rows) + 3
    outputs[ROOT_NAME] = root_payload
    final_rows = rows + [manifest_row, checksum_row, root_row]

    receipt = canonical_json({
        "coverage": {
            "c140_course": "incomplete",
            "c140_original_companion": "C1 coherent partial checkpoint complete",
            "penn_state_spine": "complete",
            "random_completeness_donor": "complete",
        },
        "gates": {
            "archives": {OFFLINE_NAME: offline_gate, SOURCE_NAME: source_gate, QA_NAME: qa_gate},
            "prior_release": {
                "bytes": sum(int(row["bytes"]) for row in prior_rows),
                "file_count": len(prior_rows),
                "identity_verified": True,
                "receipt_bytes": PRIOR_RECEIPT.stat().st_size,
                "receipt_sha256": sha256(PRIOR_RECEIPT.read_bytes()),
            },
            "privacy": {"forbidden_markers_found": 0},
        },
        "lineage": {
            "base_record_doi": "10.5281/zenodo.22143454",
            "base_record_id": "22143454",
            "concept_doi": "10.5281/zenodo.22077422",
            "create_competing_concept": False,
        },
        "outputs": {
            "checksums": {"filename": CHECKSUM_NAME, "bytes": len(checksum_payload), "sha256": sha256(checksum_payload)},
            "manifest": {"filename": MANIFEST_NAME, "bytes": len(manifest_payload), "sha256": sha256(manifest_payload)},
            "root_receipt": {"filename": ROOT_NAME, "bytes": len(root_payload), "sha256": sha256(root_payload)},
        },
        "packager": {
            "browser_processes": False,
            "credential_access": False,
            "network_access": False,
            "path": "scripts/package_c140_companion_c1_release.py",
            "publication_side_effects": False,
            "recursive_repository_discovery": False,
        },
        "publication_inventory": {
            "bytes": sum(int(row["bytes"]) for row in final_rows),
            "file_count": len(final_rows),
            "files": final_rows,
        },
        "rights": {"aggregate_uniform_relicense": False, "platform_license": "other-open"},
        "schema": "o006.c140.companion-c1-release-package.v1",
        "status": "ready",
    })
    return outputs, receipt


def verify_outputs(outputs: dict[str, bytes], receipt: bytes) -> list[str]:
    expected = set(outputs)
    errors = []
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
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs, receipt = compute()
    if args.write:
        RELEASE.mkdir(parents=True, exist_ok=True)
        for name, payload in outputs.items():
            (RELEASE / name).write_bytes(payload)
        PACKAGE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        PACKAGE_RECEIPT.write_bytes(receipt)
        state = "written"
    else:
        errors = verify_outputs(outputs, receipt)
        if errors:
            raise RuntimeError("release replay differs: " + ", ".join(errors[:40]))
        state = "verified"
    value = json.loads(receipt)
    print(json.dumps({
        "bytes": value["publication_inventory"]["bytes"],
        "files": value["publication_inventory"]["file_count"],
        "mode": state,
        "receipt_sha256": sha256(receipt),
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
