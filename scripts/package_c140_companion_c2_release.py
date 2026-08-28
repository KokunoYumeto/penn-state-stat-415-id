#!/usr/bin/env python3
"""Package the cumulative Penn + donor + original companion C2 checkpoint.

This local-only packager preserves the complete 33-file public C1 union byte
for byte, then appends eight C2-specific artifacts.  It performs no network,
credential, browser, Git, or publication operation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import package_c140_companion_c1_release as c1


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "c140-companion"
RELEASE = ROOT / "release"
PRIOR_RECEIPT = ROOT / "build" / "C140_COMPANION_C1_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C2_RELEASE_PACKAGE_RECEIPT.json"

OFFLINE_NAME = "03_C140_COMPANION_C2_OFFLINE_READER.zip"
SOURCE_NAME = "13_C140_COMPANION_C2_SOURCE_BACKEND.zip"
NOTES_NAME = "23_C140_COMPANION_C2_RELEASE_NOTES.md"
LICENSE_NAME = "33_C140_COMPANION_C2_LICENSE.md"
QA_NAME = "43_C140_COMPANION_C2_STATIC_QA_EVIDENCE.zip"
MANIFEST_NAME = "92_C140_COMPANION_C2_FULL_UNION_MANIFEST.csv"
CHECKSUM_NAME = "SHA256SUMS_C140_COMPANION_C2.txt"
ROOT_NAME = "93_C140_COMPANION_C2_FULL_UNION_ROOT_RECEIPT.json"

PRIOR_RECEIPT_BYTES = 19_580
PRIOR_RECEIPT_SHA256 = "8e7043ee5d7085941f7b30e589af23440db0c67a1ba47754494eaa07e970b181"
PRIOR_FILE_COUNT = 33
PRIOR_TOTAL_BYTES = 90_175_090
VERSION = "2026.08.29.c140-companion-c2"
SCHEMA = "o006.c140.companion-c2-release-package.v1"
EXPECTED_DOCUMENT_IDS = {
    "O006-C140-CMP-INDEX",
    "O006-C140-CMP-CA01",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 12)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 6)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in (7, 8, 9, 10, 12)),
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


def deterministic_zip(entries: dict[str, bytes], *, inventory_name: str) -> tuple[bytes, dict[str, Any]]:
    if inventory_name in entries:
        raise RuntimeError(f"inventory collision: {inventory_name}")
    inventory_rows = []
    findings = []
    for name, payload in sorted(entries.items()):
        c1.validate_relative(name)
        inventory_rows.append({"entry": name, "bytes": len(payload), "sha256": sha256(payload)})
        for finding in c1.privacy_findings(name, payload):
            findings.append({"entry": name, "finding": finding})
    if findings:
        raise RuntimeError(f"privacy findings in archive inputs: {findings}")
    inventory_payload = canonical_json({
        "entries": inventory_rows,
        "entry_count": len(inventory_rows),
        "schema": "o006.c140.companion-c2-archive-inventory.v1",
        "status": "pass",
        "total_bytes": sum(int(row["bytes"]) for row in inventory_rows),
    })
    combined = dict(entries)
    combined[inventory_name] = inventory_payload
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, payload in sorted(combined.items()):
            info = zipfile.ZipInfo(name, c1.ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        names = archive.namelist()
        if names != sorted(combined):
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


def json_file(path: Path, label: str) -> dict[str, object]:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"missing or unsafe {label}: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def validate_prior() -> tuple[dict[str, object], list[dict[str, object]]]:
    payload = PRIOR_RECEIPT.read_bytes()
    if len(payload) != PRIOR_RECEIPT_BYTES or sha256(payload) != PRIOR_RECEIPT_SHA256:
        raise RuntimeError("public C1 package receipt identity differs")
    prior = json.loads(payload)
    publication = prior.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if (
        prior.get("schema") != "o006.c140.companion-c1-release-package.v1"
        or prior.get("status") != "ready"
        or not isinstance(rows, list)
        or len(rows) != PRIOR_FILE_COUNT
        or publication.get("file_count") != PRIOR_FILE_COUNT
        or publication.get("bytes") != PRIOR_TOTAL_BYTES
    ):
        raise RuntimeError("public C1 package contract differs")
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or row.get("upload_order") != index:
            raise RuntimeError(f"malformed C1 inventory row {index}")
        name = str(row.get("filename", ""))
        source_path = str(row.get("source_path", ""))
        if source_path != f"release/{name}":
            raise RuntimeError(f"C1 source binding differs: {name}")
        path = ROOT / source_path
        payload = path.read_bytes()
        if len(payload) != row.get("bytes") or sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"inherited C1 asset identity differs: {name}")
    return prior, rows


def validate_c2_boundary() -> tuple[dict[str, object], dict[str, object]]:
    build_path = COMPONENT / "build" / "C2_BUILD_RECEIPT.json"
    qa_path = COMPONENT / "build" / "C2_QA_RECEIPT.json"
    build = json_file(build_path, "C2 build receipt")
    qa = json_file(qa_path, "C2 QA receipt")
    ids = build.get("cumulative_required_ids")
    if (
        build.get("schema") != "o006.c140.companion-cumulative-c2-build.v1"
        or build.get("status") != "pass"
        or build.get("boundary") != "cumulative-through-c2"
        or build.get("browser_processes_used") is not False
        or build.get("network_access") is not False
        or not isinstance(ids, list)
        or set(ids) != EXPECTED_DOCUMENT_IDS
        or len(ids) != len(EXPECTED_DOCUMENT_IDS)
        or build.get("cumulative_documents") != len(EXPECTED_DOCUMENT_IDS)
    ):
        raise RuntimeError("C2 build receipt does not bind the admitted cumulative boundary")
    if (
        qa.get("schema") != "o006.c140.companion-cumulative-c2-qa.v1"
        or qa.get("status") != "pass"
        or qa.get("browser_processes_used") is not False
        or qa.get("network_access") is not False
        or qa.get("build_receipt_sha256") != sha256(build_path.read_bytes())
        or qa.get("translation_provenance") != "OpenAI Codex gpt-5.6-sol, Ultra"
    ):
        raise RuntimeError("C2 QA receipt does not bind the live build")
    html = build.get("html")
    backend = build.get("backend")
    qa_source = qa.get("source")
    qa_sim = qa.get("simulations")
    if (
        not isinstance(html, dict)
        or not isinstance(backend, dict)
        or not isinstance(qa_source, dict)
        or not isinstance(qa_sim, dict)
        or qa_source.get("documents") != len(EXPECTED_DOCUMENT_IDS)
        or qa_source.get("problems") != 50
        or qa_sim.get("simulations") != 5
        or qa.get("html", {}).get("manifest_sha256") != html.get("manifest_sha256")
        or qa.get("backend", {}).get("manifest_sha256") != backend.get("manifest_sha256")
    ):
        raise RuntimeError("C2 build/QA census differs")
    html_manifest = COMPONENT / "build" / "html-id" / "MANIFEST.csv"
    backend_manifest = COMPONENT / "backend" / "MANIFEST.csv"
    if sha256(html_manifest.read_bytes()) != html.get("manifest_sha256"):
        raise RuntimeError("live C2 HTML manifest differs from build receipt")
    if sha256(backend_manifest.read_bytes()) != backend.get("manifest_sha256"):
        raise RuntimeError("live C2 backend manifest differs from build receipt")
    return build, qa


def release_notes(build: dict[str, object], qa: dict[str, object]) -> bytes:
    html = build["html"]
    backend = build["backend"]
    source = qa["source"]
    simulations = qa["simulations"]
    return (
        "# C140 original companion — C2 checkpoint\n\n"
        "Status: **partial but coherent**. The complete Penn State STAT 415 "
        "Indonesian spine, exact Random completeness donor, and byte-identical "
        "C1 publication files remain preserved. This version adds the complete "
        "C2 matrix-Gaussian linear-model bridge.\n\n"
        "C2 adds D008–D011 on fixed-design projection geometry, OLS and Gaussian "
        "MLE, Gauss–Markov, exact sampling laws, t/F inference, confidence and "
        "prediction intervals, ANOVA, diagnostics, leverage, influence, "
        "misspecification, and heteroskedasticity; SIM005; and MS12 with eight "
        "fully worked problems.\n\n"
        f"The cumulative companion now has {build['cumulative_documents']} reader "
        f"documents, {source['problems']} fully solved assessment problems, "
        f"{simulations['simulations']} seeded simulations, {html['files']} offline "
        f"reader files / {html['bytes']} bytes, and a backend with "
        f"{backend['entities']} entities / {backend['relations']} relations. "
        "Deterministic build, numerical, mathematics, reference, rights, privacy, "
        "static accessibility/reflow, archive, and byte-replay gates pass. No "
        "browser process was launched.\n\n"
        "Overall C140 remains incomplete: the Bayesian–frequentist comparison, "
        "remaining mastery sets, three further cumulative assessments, and two "
        "capstones still remain.\n\n"
        "Production provenance: `OpenAI Codex gpt-5.6-sol, Ultra`. Penn State, "
        "Random, and original-companion rights remain component-separated.\n"
    ).encode("utf-8")


def compute() -> tuple[dict[str, bytes], bytes]:
    prior, prior_rows = validate_prior()
    build, qa = validate_c2_boundary()
    outputs: dict[str, bytes] = {}
    rows: list[dict[str, object]] = []
    for row in prior_rows:
        name = str(row["filename"])
        payload = (ROOT / str(row["source_path"])).read_bytes()
        outputs[name] = payload
        rows.append(dict(row))

    offline_entries = c1.files_from_directory(COMPONENT / "build" / "html-id")
    offline_payload, offline_gate = deterministic_zip(
        offline_entries, inventory_name="OFFLINE_READER_INVENTORY.json"
    )

    source_entries: dict[str, bytes] = {}
    source_entries.update(c1.exact_files([
        ("README.md", COMPONENT / "README.md"),
        ("LICENSE.md", COMPONENT / "LICENSE.md"),
        ("environment.lock.json", COMPONENT / "environment.lock.json"),
        ("simulations/run_c1_simulations.py", COMPONENT / "simulations" / "run_c1_simulations.py"),
        ("simulations/run_c2_simulations.py", COMPONENT / "simulations" / "run_c2_simulations.py"),
        ("scripts/build_companion.py", COMPONENT / "scripts" / "build_companion.py"),
        ("scripts/qa_companion.py", COMPONENT / "scripts" / "qa_companion.py"),
        ("build/C1_SIMULATION_RECEIPT.json", COMPONENT / "build" / "C1_SIMULATION_RECEIPT.json"),
        ("build/C2_SIMULATION_RECEIPT.json", COMPONENT / "build" / "C2_SIMULATION_RECEIPT.json"),
        ("build/C1_BUILD_RECEIPT.json", COMPONENT / "build" / "C1_BUILD_RECEIPT.json"),
        ("build/C1_QA_RECEIPT.json", COMPONENT / "build" / "C1_QA_RECEIPT.json"),
        ("build/C2_BUILD_RECEIPT.json", COMPONENT / "build" / "C2_BUILD_RECEIPT.json"),
        ("build/C2_QA_RECEIPT.json", COMPONENT / "build" / "C2_QA_RECEIPT.json"),
    ]))
    source_entries.update(c1.files_from_directory(COMPONENT / "00_control", "00_control"))
    source_entries.update(c1.files_from_directory(COMPONENT / "source" / "id-ID", "source/id-ID"))
    source_entries.update(c1.files_from_directory(COMPONENT / "generated" / "simulations" / "c1", "generated/simulations/c1"))
    source_entries.update(c1.files_from_directory(COMPONENT / "generated" / "simulations" / "c2", "generated/simulations/c2"))
    source_entries.update(c1.files_from_directory(COMPONENT / "backend", "backend"))
    source_payload, source_gate = deterministic_zip(
        source_entries, inventory_name="SOURCE_BACKEND_PACKAGE_INVENTORY.json"
    )

    qa_entries = c1.exact_files([
        ("environment.lock.json", COMPONENT / "environment.lock.json"),
        ("C1_SIMULATION_RECEIPT.json", COMPONENT / "build" / "C1_SIMULATION_RECEIPT.json"),
        ("C2_SIMULATION_RECEIPT.json", COMPONENT / "build" / "C2_SIMULATION_RECEIPT.json"),
        ("C2_BUILD_RECEIPT.json", COMPONENT / "build" / "C2_BUILD_RECEIPT.json"),
        ("C2_QA_RECEIPT.json", COMPONENT / "build" / "C2_QA_RECEIPT.json"),
        ("HTML_MANIFEST.csv", COMPONENT / "build" / "html-id" / "MANIFEST.csv"),
        ("BACKEND_MANIFEST.csv", COMPONENT / "backend" / "MANIFEST.csv"),
        ("C1_SIMULATION_MANIFEST.csv", COMPONENT / "generated" / "simulations" / "c1" / "MANIFEST.csv"),
        ("C2_SIMULATION_MANIFEST.csv", COMPONENT / "generated" / "simulations" / "c2" / "MANIFEST.csv"),
    ])
    qa_payload, qa_gate = deterministic_zip(
        qa_entries, inventory_name="QA_EVIDENCE_INVENTORY.json"
    )
    notes_payload = release_notes(build, qa)
    license_payload = (COMPONENT / "LICENSE.md").read_bytes()

    additions = [
        c1.entry(OFFLINE_NAME, offline_payload, role="partial-c2-offline-html-reader", lineage="c140-original-companion-c2"),
        c1.entry(SOURCE_NAME, source_payload, role="partial-c2-resumable-source-backend", lineage="c140-original-companion-c2"),
        c1.entry(NOTES_NAME, notes_payload, role="partial-c2-scope-status-provenance", lineage="c140-original-companion-c2"),
        c1.entry(LICENSE_NAME, license_payload, role="partial-c2-component-rights", lineage="c140-original-companion-c2"),
        c1.entry(QA_NAME, qa_payload, role="partial-c2-browser-free-static-qa-evidence", lineage="c140-original-companion-c2"),
    ]
    for item, payload in zip(
        additions,
        [offline_payload, source_payload, notes_payload, license_payload, qa_payload],
        strict=True,
    ):
        name = str(item["filename"])
        if name in outputs:
            raise RuntimeError(f"C2 release filename collides: {name}")
        outputs[name] = payload
        rows.append(item)

    for index, row in enumerate(rows, start=1):
        row["upload_order"] = index
    fields = ["upload_order", "filename", "bytes", "sha256", "role", "lineage", "media_type", "primary_reader", "source_path"]
    manifest_payload = csv_bytes(fields, rows)
    manifest_row = c1.entry(MANIFEST_NAME, manifest_payload, role="c2-cumulative-union-manifest", lineage="c140-original-companion-c2-union")
    manifest_row["upload_order"] = len(rows) + 1
    outputs[MANIFEST_NAME] = manifest_payload

    checksum_covered = rows + [manifest_row]
    checksum_payload = "".join(
        f"{row['sha256']}  {row['filename']}\n" for row in checksum_covered
    ).encode("utf-8")
    checksum_row = c1.entry(CHECKSUM_NAME, checksum_payload, role="c2-cumulative-union-checksums", lineage="c140-original-companion-c2-union")
    checksum_row["upload_order"] = len(rows) + 2
    outputs[CHECKSUM_NAME] = checksum_payload

    root_covered = rows + [manifest_row, checksum_row]
    root_payload = canonical_json({
        "concept_doi": "10.5281/zenodo.22077422",
        "coverage": {
            "c140_course": "incomplete after coherent original-companion C2 checkpoint",
            "c140_original_companion": "partial: D001-D011, SIM001-SIM005, MS07-MS10, MS12, CA01",
            "penn_state_spine": "complete: landing/index plus Lesson00-Lesson12",
            "random_completeness_donor": "complete: exact one-page donor",
        },
        "file_count": len(root_covered),
        "files": root_covered,
        "preservation": {
            "prior_files_byte_identical": True,
            "prior_file_count": PRIOR_FILE_COUNT,
            "new_substantive_file_count": 5,
        },
        "rights": {"aggregate_uniform_relicense": False, "platform_license": "other-open"},
        "schema": "o006.c140.companion-c2-full-union-root.v1",
        "self_exclusion": {"filename": ROOT_NAME, "reason": "non-self-referential cryptographic root"},
        "status": "ready",
        "total_bytes_excluding_self": sum(int(row["bytes"]) for row in root_covered),
        "version": VERSION,
    })
    root_row = c1.entry(ROOT_NAME, root_payload, role="c2-cumulative-union-root-receipt", lineage="c140-original-companion-c2-union")
    root_row["upload_order"] = len(rows) + 3
    outputs[ROOT_NAME] = root_payload
    final_rows = rows + [manifest_row, checksum_row, root_row]

    receipt = canonical_json({
        "coverage": {
            "c140_course": "incomplete",
            "c140_original_companion": "C2 coherent partial checkpoint complete",
            "penn_state_spine": "complete",
            "random_completeness_donor": "complete",
        },
        "gates": {
            "archives": {OFFLINE_NAME: offline_gate, SOURCE_NAME: source_gate, QA_NAME: qa_gate},
            "c2_build": {
                "bytes": (COMPONENT / "build" / "C2_BUILD_RECEIPT.json").stat().st_size,
                "sha256": sha256((COMPONENT / "build" / "C2_BUILD_RECEIPT.json").read_bytes()),
                "status": "pass",
            },
            "c2_qa": {
                "bytes": (COMPONENT / "build" / "C2_QA_RECEIPT.json").stat().st_size,
                "sha256": sha256((COMPONENT / "build" / "C2_QA_RECEIPT.json").read_bytes()),
                "status": "pass",
            },
            "prior_release": {
                "bytes": PRIOR_TOTAL_BYTES,
                "file_count": PRIOR_FILE_COUNT,
                "identity_verified": True,
                "receipt_bytes": len(PRIOR_RECEIPT.read_bytes()),
                "receipt_sha256": sha256(PRIOR_RECEIPT.read_bytes()),
                "schema": prior["schema"],
            },
            "privacy": {"forbidden_markers_found": 0},
        },
        "lineage": {
            "base_record_doi": "10.5281/zenodo.22148810",
            "base_record_id": "22148810",
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
            "path": "scripts/package_c140_companion_c2_release.py",
            "publication_side_effects": False,
            "recursive_repository_discovery": False,
        },
        "publication_inventory": {
            "bytes": sum(int(row["bytes"]) for row in final_rows),
            "file_count": len(final_rows),
            "files": final_rows,
        },
        "rights": {"aggregate_uniform_relicense": False, "platform_license": "other-open"},
        "schema": SCHEMA,
        "status": "ready",
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
    if args.contract_only:
        state = "contract-only"
    elif args.write:
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
        "inherited_files": PRIOR_FILE_COUNT,
        "mode": state,
        "new_files": value["publication_inventory"]["file_count"] - PRIOR_FILE_COUNT,
        "receipt_sha256": sha256(receipt),
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
