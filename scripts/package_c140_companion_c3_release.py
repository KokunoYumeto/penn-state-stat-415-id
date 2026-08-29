#!/usr/bin/env python3
"""Package the cumulative C140 original-companion C3 checkpoint.

The local contract preserves the anonymously verified 41-file C2 replay-fix
publication byte for byte and appends eight compact C3 artifacts.  It performs
no browser, network, credential, Git, or publication operation.  Only
``--write`` creates the new local release files and package receipt.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any, Iterable

import package_c140_companion_c1_release as shared


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "c140-companion"
RELEASE = ROOT / "release"

BASE_PACKAGE_RECEIPT = (
    ROOT / "build" / "C140_COMPANION_C2_REPLAY_FIX_RELEASE_PACKAGE_RECEIPT.json"
)
BASE_PUBLIC_READBACK = (
    ROOT
    / "00_control"
    / "ZENODO_PUBLIC_READBACK_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
)
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C3_RELEASE_PACKAGE_RECEIPT.json"

OFFLINE_NAME = "04_C140_COMPANION_C3_OFFLINE_READER.zip"
SOURCE_NAME = "14_C140_COMPANION_C3_SOURCE_BACKEND.zip"
NOTES_NAME = "24_C140_COMPANION_C3_RELEASE_NOTES.md"
LICENSE_NAME = "34_C140_COMPANION_C3_LICENSE.md"
QA_NAME = "44_C140_COMPANION_C3_STATIC_QA_EVIDENCE.zip"
MANIFEST_NAME = "94_C140_COMPANION_C3_FULL_UNION_MANIFEST.csv"
CHECKSUM_NAME = "SHA256SUMS_C140_COMPANION_C3.txt"
ROOT_NAME = "95_C140_COMPANION_C3_FULL_UNION_ROOT_RECEIPT.json"

VERSION = "2026.08.29.c140-companion-c3"
SCHEMA = "o006.c140.companion-c3-release-package.v1"
BASE_SCHEMA = "o006.c140.companion-c2-replay-fix-release-package.v1"
BASE_READBACK_SCHEMA = (
    "o006.c140.zenodo-c140-companion-c2-replay-fix-publication.v1"
)
BASE_VERSION = "2026.08.29.c140-companion-c2-replay-fix"
BASE_RECORD_ID = "22160621"
BASE_RECORD_DOI = "10.5281/zenodo.22160621"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"

BASE_PACKAGE_RECEIPT_BYTES = 23_739
BASE_PACKAGE_RECEIPT_SHA256 = (
    "c51b7c89030b9f9be8ed740a2a7a39e2ef1b28de40357eb7dc188a723eee2bfd"
)
BASE_PUBLIC_READBACK_BYTES = 16_719
BASE_PUBLIC_READBACK_SHA256 = (
    "0f17f4f63eb2284563f547d35349d102c12244fd1d092898df0390ef5d7c11fa"
)
BASE_FILE_COUNT = 41
BASE_TOTAL_BYTES = 91_249_199
MAX_PUBLICATION_BYTES = 500_000_000

PINNED_RECEIPTS = {
    "build/C1_SIMULATION_RECEIPT.json": (
        5_468,
        "834c8a20025d51bf53ef4e8d0f7d805489af21c34065238131366a734df7e213",
    ),
    "build/C2_SIMULATION_RECEIPT.json": (
        2_187,
        "de89e57c10c178915ddd96e12d368e5e11b40baa47b6fc31c2e3df5adbd63bd2",
    ),
    "build/C3_SIMULATION_RECEIPT.json": (
        3_389,
        "c7f176380b2e30b9931cc44bcc2e39bb541559030cf65b1c41f32045c13b1040",
    ),
    "build/C1_BUILD_RECEIPT.json": (
        4_070,
        "1f9c746e723259ec46419586ac2c6f4b6ef7684deb9427e3eeb9cbc488e9ba35",
    ),
    "build/C1_QA_RECEIPT.json": (
        2_263,
        "c6b5977feb035d0f1425438dfd88b12cf8fc876820ddb04287fd62b6c37cfd67",
    ),
    "build/C2_BUILD_RECEIPT.json": (
        5_770,
        "6417c7a8764082ce74e397ccdb79d337534d27c888d8d2cc12830d6947d7c0a1",
    ),
    "build/C2_QA_RECEIPT.json": (
        3_128,
        "0f118dae5488a68098aa9fef5c03a4135968eee2c74f509f67b0817e05bc38ef",
    ),
    "build/C3_BUILD_RECEIPT.json": (
        6_780,
        "79661673ad7f4d74eff997cebd6fca1f46d2a74cbab5930147ca109762ef37ca",
    ),
    "build/C3_QA_RECEIPT.json": (
        3_697,
        "6f53a1f54d3a1b3e23b874a3c13adda9726bc0a8456d2fb4a8315d11912f72d7",
    ),
}

HTML_MANIFEST_BYTES = 6_195
HTML_MANIFEST_SHA256 = (
    "18b3ab09539eee0baa355dcb7f7edc2cec00f0960c5508a9419bf2bde7bb1273"
)
BACKEND_MANIFEST_BYTES = 277
BACKEND_MANIFEST_SHA256 = (
    "2c5b84d662713a037b512a6751dd9e8e7eb2504a69141d6268993db859e83d66"
)
C3_SIMULATION_MANIFEST_BYTES = 549
C3_SIMULATION_MANIFEST_SHA256 = (
    "64557d83097e30885ce6a9be08accd184efff745fcf532a8397f7839379e10f0"
)
LICENSE_BYTES = 642
LICENSE_SHA256 = (
    "f8913e62477ebb57d3370abb52469ac54292e2b2053db9a41fa3cb3cb02967f2"
)
COLLECTION_LICENSE_BYTES = 2_295
COLLECTION_LICENSE_SHA256 = (
    "1d7c6e8f38292dc66153a83034475341e9e6e4efe7b28b42b323f182c8aca4df"
)
ENVIRONMENT_BYTES = 178
ENVIRONMENT_SHA256 = (
    "3c5c8901ca9582e42d84ffae3aab3d9505988be6ad16eaac04d4791c601260b0"
)

EXPECTED_DOCUMENT_IDS = {
    "O006-C140-CMP-INDEX",
    "O006-C140-CMP-CA01",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 14)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 7)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(7, 13)),
}
EXPECTED_HTML_FILES = 57
EXPECTED_HTML_BYTES = 2_713_731
EXPECTED_BACKEND_FILES = 4
EXPECTED_BACKEND_BYTES = 269_101
EXPECTED_BACKEND_ENTITIES = 812
EXPECTED_BACKEND_RELATIONS = 1_084
EXPECTED_SOURCE_BYTES = 528_082
EXPECTED_PROBLEMS = 58
EXPECTED_SIMULATIONS = 6
EXPECTED_C3_SIMULATION_FILES = 5
EXPECTED_C3_SIMULATION_BYTES = 18_273


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def csv_bytes(fieldnames: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def read_identity(
    path: Path, expected_bytes: int, expected_sha256: str, label: str
) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"missing or unsafe {label}: {path}")
    payload = path.read_bytes()
    if len(payload) != expected_bytes or sha256(payload) != expected_sha256:
        raise RuntimeError(f"{label} identity differs")
    return payload


def json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def deterministic_zip(
    entries: dict[str, bytes], *, inventory_name: str
) -> tuple[bytes, dict[str, Any]]:
    if inventory_name in entries:
        raise RuntimeError(f"inventory collision: {inventory_name}")
    inventory_rows: list[dict[str, object]] = []
    findings: list[dict[str, str]] = []
    for name, payload in sorted(entries.items()):
        shared.validate_relative(name)
        inventory_rows.append(
            {"entry": name, "bytes": len(payload), "sha256": sha256(payload)}
        )
        for finding in shared.privacy_findings(name, payload):
            findings.append({"entry": name, "finding": finding})
    if findings:
        raise RuntimeError(f"privacy findings in archive inputs: {findings}")
    inventory_payload = canonical_json(
        {
            "entries": inventory_rows,
            "entry_count": len(inventory_rows),
            "schema": "o006.c140.companion-c3-archive-inventory.v1",
            "status": "pass",
            "total_bytes": sum(int(row["bytes"]) for row in inventory_rows),
        }
    )
    combined = dict(entries)
    combined[inventory_name] = inventory_payload
    stream = io.BytesIO()
    with zipfile.ZipFile(
        stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, payload in sorted(combined.items()):
            info = zipfile.ZipInfo(name, shared.ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(
                info,
                payload,
                compress_type=zipfile.ZIP_DEFLATED,
                compresslevel=9,
            )
    payload = stream.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        if archive.namelist() != sorted(combined):
            raise RuntimeError(f"archive order differs: {inventory_name}")
        for name in archive.namelist():
            if archive.read(name) != combined[name]:
                raise RuntimeError(f"archive payload differs: {name}")
        if archive.testzip() is not None:
            raise RuntimeError(f"archive CRC verification failed: {inventory_name}")
    return payload, {
        "archive_method": (
            "ZIP_DEFLATED level 9; fixed 1980-01-01 timestamps; canonical entry order"
        ),
        "bytes": len(payload),
        "entries": len(combined),
        "inventory": {
            "entry": inventory_name,
            "bytes": len(inventory_payload),
            "sha256": sha256(inventory_payload),
        },
        "sha256": sha256(payload),
        "uncompressed_bytes": sum(len(value) for value in combined.values()),
        "privacy": {"forbidden_markers_found": 0},
    }


def exact_files(paths: Iterable[tuple[str, Path]]) -> dict[str, bytes]:
    return shared.exact_files(paths)


def validate_base_public_union() -> tuple[
    dict[str, bytes], list[dict[str, Any]], dict[str, Any]
]:
    receipt_payload = read_identity(
        BASE_PACKAGE_RECEIPT,
        BASE_PACKAGE_RECEIPT_BYTES,
        BASE_PACKAGE_RECEIPT_SHA256,
        "C2 replay-fix package receipt",
    )
    readback_payload = read_identity(
        BASE_PUBLIC_READBACK,
        BASE_PUBLIC_READBACK_BYTES,
        BASE_PUBLIC_READBACK_SHA256,
        "C2 replay-fix anonymous public readback",
    )
    receipt = json_object(receipt_payload, "C2 replay-fix package receipt")
    readback = json_object(readback_payload, "C2 replay-fix public readback")
    publication = receipt.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    gates = receipt.get("gates")
    lineage = receipt.get("lineage")
    if (
        receipt.get("schema") != BASE_SCHEMA
        or receipt.get("status") != "ready"
        or receipt.get("version") != BASE_VERSION
        or not isinstance(rows, list)
        or not all(isinstance(row, dict) for row in rows)
        or len(rows) != BASE_FILE_COUNT
        or publication.get("file_count") != BASE_FILE_COUNT
        or publication.get("bytes") != BASE_TOTAL_BYTES
        or not isinstance(gates, dict)
        or gates.get("browser_processes_used") is not False
        or gates.get("credential_access") is not False
        or gates.get("git_operations") is not False
        or gates.get("network_access") is not False
        or gates.get("publication_side_effects") is not False
        or not isinstance(lineage, dict)
        or lineage.get("concept_record_id") != CONCEPT_RECORD_ID
        or lineage.get("concept_doi") != CONCEPT_DOI
    ):
        raise RuntimeError("C2 replay-fix package contract differs")

    public = readback.get("public")
    public_rows = public.get("files") if isinstance(public, dict) else None
    if (
        readback.get("schema") != BASE_READBACK_SCHEMA
        or readback.get("version") != BASE_VERSION
        or readback.get("credential_access") is not False
        or not isinstance(public, dict)
        or public.get("anonymous_readback") is not True
        or public.get("reader_first") is not True
        or public.get("record_id") != BASE_RECORD_ID
        or public.get("doi") != BASE_RECORD_DOI
        or public.get("concept_record_id") != CONCEPT_RECORD_ID
        or public.get("concept_doi") != CONCEPT_DOI
        or public.get("version") != BASE_VERSION
        or public.get("file_count") != BASE_FILE_COUNT
        or public.get("total_bytes") != BASE_TOTAL_BYTES
        or not isinstance(public_rows, list)
        or len(public_rows) != BASE_FILE_COUNT
    ):
        raise RuntimeError("C2 replay-fix public readback contract differs")

    outputs: dict[str, bytes] = {}
    for expected_order, (row, public_row) in enumerate(
        zip(rows, public_rows, strict=True), start=1
    ):
        name = str(row.get("filename", ""))
        shared.validate_relative(name)
        path = RELEASE / name
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"missing inherited public asset: {name}")
        payload = path.read_bytes()
        if (
            row.get("upload_order") != expected_order
            or row.get("source_path") != f"release/{name}"
            or len(payload) != row.get("bytes")
            or sha256(payload) != row.get("sha256")
            or not isinstance(public_row, dict)
            or public_row.get("name") != name
            or public_row.get("bytes") != row.get("bytes")
            or public_row.get("sha256") != row.get("sha256")
            or name in outputs
        ):
            raise RuntimeError(f"inherited public identity/order differs: {name}")
        outputs[name] = payload

    if (
        rows[0].get("filename")
        != "00_00_stat415-pengantar-statistika-matematis-id.pdf"
        or rows[0].get("primary_reader") is not True
        or rows[0].get("media_type") != "application/pdf"
        or rows[1].get("filename")
        != "00_01_stat415-pengantar-statistika-matematis-id.epub"
        or rows[1].get("media_type") != "application/epub+zip"
    ):
        raise RuntimeError("reader-first PDF/EPUB order differs")
    return outputs, [dict(row) for row in rows], readback


def validate_pinned_receipts() -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for relative, (expected_bytes, expected_hash) in PINNED_RECEIPTS.items():
        payload = read_identity(
            COMPONENT / relative,
            expected_bytes,
            expected_hash,
            relative,
        )
        result[relative] = {
            "bytes": len(payload),
            "sha256": sha256(payload),
        }
    return result


def directory_identity(root: Path) -> tuple[int, int]:
    entries = shared.files_from_directory(root)
    return len(entries), sum(len(payload) for payload in entries.values())


def validate_c3_boundary() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, dict[str, object]]
]:
    receipt_identities = validate_pinned_receipts()
    build = json_object(
        (COMPONENT / "build" / "C3_BUILD_RECEIPT.json").read_bytes(),
        "C3 build receipt",
    )
    qa = json_object(
        (COMPONENT / "build" / "C3_QA_RECEIPT.json").read_bytes(),
        "C3 QA receipt",
    )
    ids = build.get("cumulative_required_ids")
    html = build.get("html")
    backend = build.get("backend")
    source_rows = build.get("source")
    simulation_receipts = build.get("simulation_receipts")
    if (
        build.get("schema") != "o006.c140.companion-cumulative-c3-build.v1"
        or build.get("status") != "pass"
        or build.get("boundary") != "cumulative-through-c3"
        or build.get("browser_processes_used") is not False
        or build.get("network_access") is not False
        or build.get("translation_provenance")
        != "OpenAI Codex gpt-5.6-sol, Ultra"
        or not isinstance(ids, list)
        or set(ids) != EXPECTED_DOCUMENT_IDS
        or len(ids) != len(EXPECTED_DOCUMENT_IDS)
        or build.get("cumulative_documents") != len(EXPECTED_DOCUMENT_IDS)
        or not isinstance(html, dict)
        or html.get("files") != EXPECTED_HTML_FILES
        or html.get("bytes") != EXPECTED_HTML_BYTES
        or html.get("manifest_sha256") != HTML_MANIFEST_SHA256
        or not isinstance(backend, dict)
        or backend.get("files") != EXPECTED_BACKEND_FILES
        or backend.get("bytes") != EXPECTED_BACKEND_BYTES
        or backend.get("entities") != EXPECTED_BACKEND_ENTITIES
        or backend.get("relations") != EXPECTED_BACKEND_RELATIONS
        or backend.get("manifest_sha256") != BACKEND_MANIFEST_SHA256
        or not isinstance(source_rows, list)
        or len(source_rows) != len(EXPECTED_DOCUMENT_IDS)
        or not isinstance(simulation_receipts, list)
        or len(simulation_receipts) != 3
    ):
        raise RuntimeError("C3 cumulative build contract differs")

    expected_simulation_receipts = {
        "c1": PINNED_RECEIPTS["build/C1_SIMULATION_RECEIPT.json"][1],
        "c2": PINNED_RECEIPTS["build/C2_SIMULATION_RECEIPT.json"][1],
        "c3": PINNED_RECEIPTS["build/C3_SIMULATION_RECEIPT.json"][1],
    }
    if {
        str(row.get("batch")): str(row.get("sha256"))
        for row in simulation_receipts
        if isinstance(row, dict)
    } != expected_simulation_receipts:
        raise RuntimeError("C3 build simulation-receipt closure differs")

    seen_sources: set[str] = set()
    for row in source_rows:
        if not isinstance(row, dict):
            raise RuntimeError("C3 source row is malformed")
        relative = str(row.get("path", ""))
        shared.validate_relative(relative)
        if relative in seen_sources:
            raise RuntimeError(f"duplicate C3 source row: {relative}")
        seen_sources.add(relative)
        path = COMPONENT / relative
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"missing C3 source: {relative}")
        payload = path.read_bytes()
        if len(payload) != row.get("bytes") or sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"C3 source identity differs: {relative}")
    if sum(int(row["bytes"]) for row in source_rows) != EXPECTED_SOURCE_BYTES:
        raise RuntimeError("C3 source-byte census differs")

    if (
        qa.get("schema") != "o006.c140.companion-cumulative-c3-qa.v1"
        or qa.get("status") != "pass"
        or qa.get("browser_processes_used") is not False
        or qa.get("network_access") is not False
        or qa.get("translation_provenance")
        != "OpenAI Codex gpt-5.6-sol, Ultra"
        or qa.get("build_receipt_sha256")
        != PINNED_RECEIPTS["build/C3_BUILD_RECEIPT.json"][1]
        or qa.get("source", {}).get("documents") != len(EXPECTED_DOCUMENT_IDS)
        or qa.get("source", {}).get("source_bytes") != EXPECTED_SOURCE_BYTES
        or qa.get("source", {}).get("problems") != EXPECTED_PROBLEMS
        or qa.get("simulations", {}).get("simulations") != EXPECTED_SIMULATIONS
        or qa.get("html", {}).get("files") != EXPECTED_HTML_FILES
        or qa.get("html", {}).get("manifest_sha256") != HTML_MANIFEST_SHA256
        or qa.get("backend", {}).get("entities") != EXPECTED_BACKEND_ENTITIES
        or qa.get("backend", {}).get("relations") != EXPECTED_BACKEND_RELATIONS
        or qa.get("backend", {}).get("manifest_sha256")
        != BACKEND_MANIFEST_SHA256
    ):
        raise RuntimeError("C3 cumulative QA contract differs")

    read_identity(
        COMPONENT / "build" / "html-id" / "MANIFEST.csv",
        HTML_MANIFEST_BYTES,
        HTML_MANIFEST_SHA256,
        "C3 HTML manifest",
    )
    read_identity(
        COMPONENT / "backend" / "MANIFEST.csv",
        BACKEND_MANIFEST_BYTES,
        BACKEND_MANIFEST_SHA256,
        "C3 backend manifest",
    )
    read_identity(
        COMPONENT / "generated" / "simulations" / "c3" / "MANIFEST.csv",
        C3_SIMULATION_MANIFEST_BYTES,
        C3_SIMULATION_MANIFEST_SHA256,
        "C3 simulation manifest",
    )
    read_identity(
        COMPONENT / "LICENSE.md", LICENSE_BYTES, LICENSE_SHA256, "component license"
    )
    read_identity(
        COMPONENT / "environment.lock.json",
        ENVIRONMENT_BYTES,
        ENVIRONMENT_SHA256,
        "environment lock",
    )
    if directory_identity(COMPONENT / "build" / "html-id") != (
        EXPECTED_HTML_FILES,
        EXPECTED_HTML_BYTES,
    ):
        raise RuntimeError("C3 live offline-reader directory census differs")
    if directory_identity(COMPONENT / "backend") != (
        EXPECTED_BACKEND_FILES,
        EXPECTED_BACKEND_BYTES,
    ):
        raise RuntimeError("C3 live backend directory census differs")
    if directory_identity(COMPONENT / "generated" / "simulations" / "c3") != (
        EXPECTED_C3_SIMULATION_FILES,
        EXPECTED_C3_SIMULATION_BYTES,
    ):
        raise RuntimeError("C3 generated-simulation directory census differs")
    return build, qa, receipt_identities


def release_notes(build: dict[str, Any], qa: dict[str, Any]) -> bytes:
    html = build["html"]
    backend = build["backend"]
    source = qa["source"]
    simulations = qa["simulations"]
    return (
        "# C140 original companion — C3 checkpoint\n\n"
        "Status: **partial but coherent**. The complete Penn State STAT 415 "
        "Indonesian spine, exact Random completeness donor, and all 41 "
        "anonymously verified C2 replay-fix files remain byte-identical. This "
        "version adds the complete bounded C3 Bayesian–frequentist comparison "
        "and calibration batch.\n\n"
        "C3 adds D012–D013 on priors, likelihood, posterior and predictive "
        "distributions, decision and loss, Bayes and frequentist risk, conjugacy, "
        "improper priors, credible sets versus confidence procedures, fixed-"
        "parameter versus prior-averaged calibration, Bayes factors, predictive "
        "checks, p-values, and optional stopping; seeded SIM006; and MS11 with "
        "eight fully worked problems.\n\n"
        f"The cumulative original companion now has {build['cumulative_documents']} "
        f"reader documents, {source['problems']} fully solved problems, "
        f"{simulations['simulations']} seeded simulations, {html['files']} offline "
        f"reader files / {html['bytes']} bytes, and a backend with "
        f"{backend['entities']} entities / {backend['relations']} relations. "
        "Deterministic build, numerical, mathematics, reference, rights, privacy, "
        "static accessibility/reflow, archive, and byte-replay gates pass. No "
        "browser process or network access was used.\n\n"
        "The inherited PDF and EPUB remain first in the cumulative inventory; "
        "C3 itself is supplied as the current offline HTML reader plus compact "
        "resumable source/backend. Overall C140 remains incomplete: remaining "
        "mastery sets, three further cumulative assessments, and two capstones "
        "still remain.\n\n"
        "Production provenance: `OpenAI Codex gpt-5.6-sol, Ultra`. Penn State, "
        "Random, and original-companion rights remain component-separated.\n"
    ).encode("utf-8")


def new_entry(
    filename: str, payload: bytes, *, role: str, lineage: str
) -> dict[str, object]:
    return shared.entry(filename, payload, role=role, lineage=lineage)


def compute() -> tuple[dict[str, bytes], bytes]:
    outputs, rows, _readback = validate_base_public_union()
    build, qa, receipt_identities = validate_c3_boundary()
    notes_payload = release_notes(build, qa)
    license_payload = read_identity(
        COMPONENT / "LICENSE.md", LICENSE_BYTES, LICENSE_SHA256, "component license"
    )
    collection_license_payload = read_identity(
        ROOT / "LICENSE.md",
        COLLECTION_LICENSE_BYTES,
        COLLECTION_LICENSE_SHA256,
        "collection license",
    )

    offline_entries = shared.files_from_directory(COMPONENT / "build" / "html-id")
    offline_payload, offline_gate = deterministic_zip(
        offline_entries, inventory_name="OFFLINE_READER_INVENTORY.json"
    )

    source_entries: dict[str, bytes] = {"README_RELEASE.md": notes_payload}
    source_entries.update(
        exact_files(
            [
                ("LICENSE.md", COMPONENT / "LICENSE.md"),
                ("environment.lock.json", COMPONENT / "environment.lock.json"),
                (
                    "scripts/package_c140_companion_c1_release.py",
                    ROOT / "scripts" / "package_c140_companion_c1_release.py",
                ),
                (
                    "scripts/package_c140_companion_c3_release.py",
                    Path(__file__).resolve(),
                ),
                (
                    "scripts/build_companion.py",
                    COMPONENT / "scripts" / "build_companion.py",
                ),
                (
                    "scripts/qa_companion.py",
                    COMPONENT / "scripts" / "qa_companion.py",
                ),
                (
                    "simulations/run_c1_simulations.py",
                    COMPONENT / "simulations" / "run_c1_simulations.py",
                ),
                (
                    "simulations/run_c2_simulations.py",
                    COMPONENT / "simulations" / "run_c2_simulations.py",
                ),
                (
                    "simulations/run_c3_simulations.py",
                    COMPONENT / "simulations" / "run_c3_simulations.py",
                ),
                (
                    "00_control/CONTENT_CONTRACT.md",
                    COMPONENT / "00_control" / "CONTENT_CONTRACT.md",
                ),
                (
                    "00_control/WORKFLOW.md",
                    COMPONENT / "00_control" / "WORKFLOW.md",
                ),
                (
                    "00_control/C2_MATRIX_BATCH_CONTRACT.md",
                    COMPONENT / "00_control" / "C2_MATRIX_BATCH_CONTRACT.md",
                ),
                (
                    "00_control/C3_BAYESIAN_COMPARISON_BATCH_CONTRACT.md",
                    COMPONENT
                    / "00_control"
                    / "C3_BAYESIAN_COMPARISON_BATCH_CONTRACT.md",
                ),
                *[
                    (relative, COMPONENT / relative)
                    for relative in PINNED_RECEIPTS
                ],
            ]
        )
    )
    source_entries["COLLECTION_LICENSE.md"] = collection_license_payload
    source_entries.update(
        shared.files_from_directory(COMPONENT / "source" / "id-ID", "source/id-ID")
    )
    for batch in ("c1", "c2", "c3"):
        source_entries.update(
            shared.files_from_directory(
                COMPONENT / "generated" / "simulations" / batch,
                f"generated/simulations/{batch}",
            )
        )
    source_entries.update(shared.files_from_directory(COMPONENT / "backend", "backend"))
    source_payload, source_gate = deterministic_zip(
        source_entries, inventory_name="SOURCE_BACKEND_PACKAGE_INVENTORY.json"
    )

    qa_entries = exact_files(
        [
            ("environment.lock.json", COMPONENT / "environment.lock.json"),
            *[(Path(relative).name, COMPONENT / relative) for relative in PINNED_RECEIPTS],
            (
                "HTML_MANIFEST.csv",
                COMPONENT / "build" / "html-id" / "MANIFEST.csv",
            ),
            ("BACKEND_MANIFEST.csv", COMPONENT / "backend" / "MANIFEST.csv"),
            (
                "C1_SIMULATION_MANIFEST.csv",
                COMPONENT / "generated" / "simulations" / "c1" / "MANIFEST.csv",
            ),
            (
                "C2_SIMULATION_MANIFEST.csv",
                COMPONENT / "generated" / "simulations" / "c2" / "MANIFEST.csv",
            ),
            (
                "C3_SIMULATION_MANIFEST.csv",
                COMPONENT / "generated" / "simulations" / "c3" / "MANIFEST.csv",
            ),
            (
                "C2_REPLAY_FIX_RELEASE_PACKAGE_RECEIPT.json",
                BASE_PACKAGE_RECEIPT,
            ),
            (
                "C2_REPLAY_FIX_ZENODO_PUBLIC_READBACK.json",
                BASE_PUBLIC_READBACK,
            ),
        ]
    )
    qa_payload, qa_gate = deterministic_zip(
        qa_entries, inventory_name="QA_EVIDENCE_INVENTORY.json"
    )

    additions = [
        new_entry(
            OFFLINE_NAME,
            offline_payload,
            role="partial-c3-offline-html-reader",
            lineage="c140-original-companion-c3",
        ),
        new_entry(
            SOURCE_NAME,
            source_payload,
            role="partial-c3-resumable-source-backend",
            lineage="c140-original-companion-c3",
        ),
        new_entry(
            NOTES_NAME,
            notes_payload,
            role="partial-c3-scope-status-provenance",
            lineage="c140-original-companion-c3",
        ),
        new_entry(
            LICENSE_NAME,
            license_payload,
            role="partial-c3-component-rights",
            lineage="c140-original-companion-c3",
        ),
        new_entry(
            QA_NAME,
            qa_payload,
            role="partial-c3-browser-free-static-qa-evidence",
            lineage="c140-original-companion-c3",
        ),
    ]
    for row, payload in zip(
        additions,
        [offline_payload, source_payload, notes_payload, license_payload, qa_payload],
        strict=True,
    ):
        name = str(row["filename"])
        if name in outputs:
            raise RuntimeError(f"C3 release filename collides: {name}")
        outputs[name] = payload
        rows.append(row)

    for upload_order, row in enumerate(rows, start=1):
        row["upload_order"] = upload_order
    fields = [
        "upload_order",
        "filename",
        "bytes",
        "sha256",
        "role",
        "lineage",
        "media_type",
        "primary_reader",
        "source_path",
    ]
    manifest_payload = csv_bytes(fields, rows)
    manifest_row = new_entry(
        MANIFEST_NAME,
        manifest_payload,
        role="c3-cumulative-union-manifest",
        lineage="c140-original-companion-c3-union",
    )
    manifest_row["upload_order"] = len(rows) + 1
    outputs[MANIFEST_NAME] = manifest_payload

    checksum_covered = rows + [manifest_row]
    checksum_payload = "".join(
        f"{row['sha256']}  {row['filename']}\n" for row in checksum_covered
    ).encode("utf-8")
    checksum_row = new_entry(
        CHECKSUM_NAME,
        checksum_payload,
        role="c3-cumulative-union-checksums",
        lineage="c140-original-companion-c3-union",
    )
    checksum_row["upload_order"] = len(rows) + 2
    outputs[CHECKSUM_NAME] = checksum_payload

    root_covered = rows + [manifest_row, checksum_row]
    root_payload = canonical_json(
        {
            "concept_doi": CONCEPT_DOI,
            "coverage": {
                "c140_course": "incomplete after coherent original-companion C3 checkpoint",
                "c140_original_companion": (
                    "partial: D001-D013, SIM001-SIM006, MS07-MS12, CA01"
                ),
                "c3_batch": "complete on its admitted D012-D013, SIM006, MS11 boundary",
                "penn_state_spine": "complete: landing/index plus Lesson00-Lesson12",
                "random_completeness_donor": "complete: exact one-page donor",
                "remaining": (
                    "remaining mastery sets, three cumulative assessments, and two capstones"
                ),
            },
            "execution_claims": {
                "browser_processes_used": False,
                "credential_access": False,
                "git_operations": False,
                "network_access": False,
                "publication_side_effects": False,
            },
            "file_count": len(root_covered),
            "files": root_covered,
            "preservation": {
                "base_public_readback_bytes": BASE_PUBLIC_READBACK_BYTES,
                "base_public_readback_sha256": BASE_PUBLIC_READBACK_SHA256,
                "inherited_files_byte_identical": True,
                "inherited_file_count": BASE_FILE_COUNT,
                "new_structural_file_count": 3,
                "new_substantive_file_count": 5,
            },
            "reader_order": {
                "first": "00_00_stat415-pengantar-statistika-matematis-id.pdf",
                "second": "00_01_stat415-pengantar-statistika-matematis-id.epub",
            },
            "rights": {
                "aggregate_uniform_relicense": False,
                "collection_license_bytes": COLLECTION_LICENSE_BYTES,
                "collection_license_sha256": COLLECTION_LICENSE_SHA256,
                "component_licenses_unchanged": True,
                "platform_license": "other-open",
            },
            "schema": "o006.c140.companion-c3-full-union-root.v1",
            "self_exclusion": {
                "filename": ROOT_NAME,
                "reason": "non-self-referential cryptographic root",
            },
            "status": "ready",
            "total_bytes_excluding_self": sum(
                int(row["bytes"]) for row in root_covered
            ),
            "version": VERSION,
        }
    )
    root_row = new_entry(
        ROOT_NAME,
        root_payload,
        role="c3-cumulative-union-root-receipt",
        lineage="c140-original-companion-c3-union",
    )
    root_row["upload_order"] = len(rows) + 3
    outputs[ROOT_NAME] = root_payload
    final_rows = rows + [manifest_row, checksum_row, root_row]

    if len(final_rows) != BASE_FILE_COUNT + 8:
        raise RuntimeError("C3 publication file count differs")
    publication_bytes = sum(int(row["bytes"]) for row in final_rows)
    if publication_bytes > MAX_PUBLICATION_BYTES:
        raise RuntimeError("C3 publication exceeds the 500,000,000-byte cap")
    if tuple(outputs) != tuple(str(row["filename"]) for row in final_rows):
        raise RuntimeError("C3 output order differs from upload inventory")
    privacy_findings = []
    for row in final_rows[BASE_FILE_COUNT:]:
        name = str(row["filename"])
        for finding in shared.privacy_findings(name, outputs[name]):
            privacy_findings.append({"filename": name, "finding": finding})
    if privacy_findings:
        raise RuntimeError(f"privacy findings in new C3 outputs: {privacy_findings}")

    receipt = canonical_json(
        {
            "base_public_union": {
                "anonymous_readback": True,
                "bytes": BASE_TOTAL_BYTES,
                "concept_doi": CONCEPT_DOI,
                "concept_record_id": CONCEPT_RECORD_ID,
                "file_count": BASE_FILE_COUNT,
                "package_receipt": {
                    "bytes": BASE_PACKAGE_RECEIPT_BYTES,
                    "sha256": BASE_PACKAGE_RECEIPT_SHA256,
                },
                "public_readback": {
                    "bytes": BASE_PUBLIC_READBACK_BYTES,
                    "sha256": BASE_PUBLIC_READBACK_SHA256,
                },
                "record_doi": BASE_RECORD_DOI,
                "record_id": BASE_RECORD_ID,
                "version": BASE_VERSION,
            },
            "coverage": {
                "c140_course": "incomplete",
                "c140_original_companion": "C3 coherent partial checkpoint complete",
                "c3_batch": "complete",
                "penn_state_spine": "complete",
                "random_completeness_donor": "complete",
                "remaining": (
                    "remaining mastery sets, three cumulative assessments, and two capstones"
                ),
            },
            "gates": {
                "archives": {
                    OFFLINE_NAME: offline_gate,
                    SOURCE_NAME: source_gate,
                    QA_NAME: qa_gate,
                },
                "c3_boundary": {
                    "backend_entities": EXPECTED_BACKEND_ENTITIES,
                    "backend_relations": EXPECTED_BACKEND_RELATIONS,
                    "documents": len(EXPECTED_DOCUMENT_IDS),
                    "html_files": EXPECTED_HTML_FILES,
                    "problems": EXPECTED_PROBLEMS,
                    "simulations": EXPECTED_SIMULATIONS,
                    "status": "pass",
                },
                "input_receipts": receipt_identities,
                "privacy": {"forbidden_markers_found": 0},
                "publication_size": {
                    "bytes": publication_bytes,
                    "cap_bytes": MAX_PUBLICATION_BYTES,
                    "status": "pass",
                },
            },
            "lineage": {
                "base_record_doi": BASE_RECORD_DOI,
                "base_record_id": BASE_RECORD_ID,
                "concept_doi": CONCEPT_DOI,
                "concept_record_id": CONCEPT_RECORD_ID,
                "create_competing_concept": False,
            },
            "outputs": {
                "checksums": {
                    "filename": CHECKSUM_NAME,
                    "bytes": len(checksum_payload),
                    "sha256": sha256(checksum_payload),
                },
                "manifest": {
                    "filename": MANIFEST_NAME,
                    "bytes": len(manifest_payload),
                    "sha256": sha256(manifest_payload),
                },
                "root_receipt": {
                    "filename": ROOT_NAME,
                    "bytes": len(root_payload),
                    "sha256": sha256(root_payload),
                },
            },
            "packager": {
                "browser_processes_used": False,
                "credential_access": False,
                "git_operations": False,
                "network_access": False,
                "path": "scripts/package_c140_companion_c3_release.py",
                "publication_side_effects": False,
                "recursive_repository_discovery": False,
                "source_bytes": Path(__file__).resolve().stat().st_size,
                "source_sha256": sha256(Path(__file__).resolve().read_bytes()),
            },
            "preservation": {
                "inherited_files_byte_identical": True,
                "inherited_file_count": BASE_FILE_COUNT,
                "new_file_count": len(final_rows) - BASE_FILE_COUNT,
                "new_substantive_file_count": 5,
            },
            "publication_inventory": {
                "bytes": publication_bytes,
                "file_count": len(final_rows),
                "files": final_rows,
            },
            "reader_order": {
                "inherited_union_first": True,
                "pdf_upload_order": 1,
                "epub_upload_order": 2,
                "c3_first_upload_order": BASE_FILE_COUNT + 1,
            },
            "rights": {
                "aggregate_uniform_relicense": False,
                "collection_license_bytes": COLLECTION_LICENSE_BYTES,
                "collection_license_sha256": COLLECTION_LICENSE_SHA256,
                "component_license_bytes": LICENSE_BYTES,
                "component_license_sha256": LICENSE_SHA256,
                "component_licenses_unchanged": True,
                "platform_license": "other-open",
            },
            "schema": SCHEMA,
            "status": "ready",
            "version": VERSION,
        }
    )
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
    if args.contract_only:
        state = "contract-only"
    elif args.write:
        RELEASE.mkdir(parents=True, exist_ok=True)
        for name in tuple(outputs)[BASE_FILE_COUNT:]:
            (RELEASE / name).write_bytes(outputs[name])
        PACKAGE_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        PACKAGE_RECEIPT.write_bytes(receipt)
        errors = verify_outputs(outputs, receipt)
        if errors:
            raise RuntimeError("written C3 package differs: " + ", ".join(errors[:40]))
        state = "written"
    else:
        errors = verify_outputs(outputs, receipt)
        if errors:
            raise RuntimeError("C3 package replay differs: " + ", ".join(errors[:40]))
        state = "verified"

    print(
        json.dumps(
            {
                "bytes": package["publication_inventory"]["bytes"],
                "credential_access": False,
                "files": package["publication_inventory"]["file_count"],
                "inherited_files": BASE_FILE_COUNT,
                "mode": state,
                "network_access": False,
                "new_files": package["preservation"]["new_file_count"],
                "receipt_sha256": sha256(receipt),
                "status": "pass",
                "version": VERSION,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
