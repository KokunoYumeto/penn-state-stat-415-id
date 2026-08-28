#!/usr/bin/env python3
"""Publish and verify the cumulative C140 original-companion C1 release.

This is a deliberately thin, fail-closed adapter over the already hardened
Random-completeness GitHub release engine.  The engine itself is pinned by
byte count and SHA-256 before its transaction code may be used.  This adapter
replaces the donor snapshot, metadata, schemas, and receipt fields with the
exact 33-file C1 cumulative union:

* the first 25 assets are the byte-identical public Random-completeness union;
* the final eight assets are the coherent partial C1 companion checkpoint;
* the target is one annotated tag and one public GitHub release; and
* every released asset is downloaded again without credentials.

``--contract-check`` is local, credential-free, network-free, and browser-free.
The inherited engine has no browser dependency in any mode.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import publish_verify_github_random_completeness as engine


ROOT = Path(__file__).resolve().parents[1]
ENGINE_RELATIVE = "scripts/publish_verify_github_random_completeness.py"
PACKAGE_RELATIVE = "build/C140_COMPANION_C1_RELEASE_PACKAGE_RECEIPT.json"
PRIOR_PACKAGE_RELATIVE = "build/RANDOM_COMPLETENESS_RELEASE_PACKAGE_RECEIPT.json"
PACKAGER_RELATIVE = "scripts/package_c140_companion_c1_release.py"

PACKAGE_RECEIPT = ROOT / PACKAGE_RELATIVE
PRIOR_PACKAGE_RECEIPT = ROOT / PRIOR_PACKAGE_RELATIVE
VERIFICATION_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-28_C140_COMPANION_C1.json"
)
PUBLICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_PUBLICATION_2026-08-28_C140_COMPANION_C1.json"
)

EXPECTED_ENGINE_BYTES = 52_465
EXPECTED_ENGINE_SHA256 = "b6da88fef227b7ec9df8da8ef1887275b04fd990dd87e110d610ace7edf3f949"
EXPECTED_PACKAGER_BYTES = 19_180
EXPECTED_PACKAGER_SHA256 = "b1b308f15081b3ecb8e2702b93055a01dc7f7f2d19d2e7c183a3a8e41688adf3"
EXPECTED_PACKAGE_RECEIPT_BYTES = 19_580
EXPECTED_PACKAGE_RECEIPT_SHA256 = "8e7043ee5d7085941f7b30e589af23440db0c67a1ba47754494eaa07e970b181"
EXPECTED_PRIOR_RECEIPT_BYTES = 24_065
EXPECTED_PRIOR_RECEIPT_SHA256 = "61da36364ec719e9af966b3a20eaa459863390b71fce7622c8b365f02818641c"

PACKAGE_SCHEMA = "o006.c140.companion-c1-release-package.v1"
PACKAGE_VERSION = "2026.08.28.c140-companion-c1"
VERIFICATION_SCHEMA = "o006.c140.companion-c1.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c1.github-release-publication.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TAG = "v2026.08.28.c140-companion-c1"
PRIOR_TAG = "v2026.08.28.c140-random-completeness"
PRIOR_RELEASE_ID = 378_436_672
PRIOR_COMMIT = "517301bb0cb782a43a3e412b0a07363371f78fe4"
PRIOR_TAG_OBJECT = "6a6a1103257cf17c0f58068d5b5edf7f45c2cd69"

TITLE = "O006/C140 Statistika Matematis — Pendamping Orisinal C1 (Bahasa Indonesia)"
BODY = (
    "Rilis kumulatif O006/C140 ini mempertahankan pembaca lengkap Penn State "
    "STAT 415 dan donor kelengkapan Kyle Siegrist/Random secara byte-identik, "
    "lalu menambahkan checkpoint C1 pendamping orisinal dalam Bahasa Indonesia. "
    "C1 adalah coherent partial checkpoint: tujuh unit teori (D001–D007), empat "
    "simulasi reproduktif (SIM001–SIM004), empat set penguasaan (MS07–MS10), "
    "dan asesmen kumulatif CA01. Keseluruhan mata kuliah C140 masih incomplete; "
    "model linear Gaussian matriks, perbandingan Bayesian, serta asesmen dan "
    "capstone lanjutan belum termasuk. Hak tetap dipisahkan per komponen: Penn "
    "State, donor Random, dan pendamping orisinal mempertahankan lisensinya "
    "masing-masing; agregat tidak direlisensi secara seragam. Provenans: "
    f"{MODEL_PROVENANCE}."
)
TAG_MESSAGE = "O006/C140 original companion C1 coherent partial checkpoint (2026-08-28)"

INHERITED_NAMES = tuple(engine.EXPECTED_NAMES)
ADDITION_NAMES = (
    "02_C140_COMPANION_C1_OFFLINE_READER.zip",
    "12_C140_COMPANION_C1_SOURCE_BACKEND.zip",
    "22_C140_COMPANION_C1_RELEASE_NOTES.md",
    "32_C140_COMPANION_C1_LICENSE.md",
    "42_C140_COMPANION_C1_STATIC_QA_EVIDENCE.zip",
    "90_C140_COMPANION_C1_FULL_UNION_MANIFEST.csv",
    "SHA256SUMS_C140_COMPANION_C1.txt",
    "91_C140_COMPANION_C1_FULL_UNION_ROOT_RECEIPT.json",
)
EXPECTED_NAMES = INHERITED_NAMES + ADDITION_NAMES
EXPECTED_FIELDS = (
    "upload_order",
    "filename",
    "bytes",
    "sha256",
    "role",
    "lineage",
    "media_type",
    "primary_reader",
    "source_path",
)
EXPECTED_ADDITION_ROLES = {
    "02_C140_COMPANION_C1_OFFLINE_READER.zip": "partial-c1-offline-html-reader",
    "12_C140_COMPANION_C1_SOURCE_BACKEND.zip": "partial-c1-resumable-source-backend",
    "22_C140_COMPANION_C1_RELEASE_NOTES.md": "partial-c1-scope-status-provenance",
    "32_C140_COMPANION_C1_LICENSE.md": "partial-c1-component-rights",
    "42_C140_COMPANION_C1_STATIC_QA_EVIDENCE.zip": "partial-c1-browser-free-static-qa-evidence",
    "90_C140_COMPANION_C1_FULL_UNION_MANIFEST.csv": "c1-cumulative-union-manifest",
    "SHA256SUMS_C140_COMPANION_C1.txt": "c1-cumulative-union-checksums",
    "91_C140_COMPANION_C1_FULL_UNION_ROOT_RECEIPT.json": "c1-cumulative-union-root-receipt",
}
EXPECTED_ADDITION_LINEAGES = {
    **{name: "c140-original-companion-c1" for name in ADDITION_NAMES[:5]},
    **{name: "c140-original-companion-c1-union" for name in ADDITION_NAMES[5:]},
}
EXPECTED_COVERAGE = {
    "c140_course": "incomplete",
    "c140_original_companion": "C1 coherent partial checkpoint complete",
    "penn_state_spine": "complete",
    "random_completeness_donor": "complete",
}
EXPECTED_RIGHTS = {
    "aggregate_uniform_relicense": False,
    "platform_license": "other-open",
}
EXPECTED_LINEAGE = {
    "base_record_doi": "10.5281/zenodo.22143454",
    "base_record_id": "22143454",
    "concept_doi": "10.5281/zenodo.22077422",
    "create_competing_concept": False,
}
EXPECTED_PACKAGER = {
    "browser_processes": False,
    "credential_access": False,
    "network_access": False,
    "path": PACKAGER_RELATIVE,
    "publication_side_effects": False,
    "recursive_repository_discovery": False,
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def exact_payload(relative: str, label: str, size: int, digest: str) -> bytes:
    payload = engine.read_confined(relative, label)
    if len(payload) != size or sha256(payload) != digest:
        raise RuntimeError(f"{label} identity differs")
    return payload


def json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not a UTF-8 JSON object") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def validate_package_contract(
    package: dict[str, Any], prior: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    prior_publication = prior.get("publication_inventory")
    prior_rows = (
        prior_publication.get("files") if isinstance(prior_publication, dict) else None
    )
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("coverage") != EXPECTED_COVERAGE
        or package.get("rights") != EXPECTED_RIGHTS
        or package.get("lineage") != EXPECTED_LINEAGE
        or package.get("packager") != EXPECTED_PACKAGER
        or not isinstance(publication, dict)
        or publication.get("file_count") != len(EXPECTED_NAMES)
        or publication.get("bytes") != 90_175_090
        or not isinstance(rows, list)
        or len(rows) != len(EXPECTED_NAMES)
    ):
        raise RuntimeError("C1 package receipt is not the admitted coherent partial boundary")
    if (
        prior.get("schema") != "o006.c140.random-completeness-release-package.v1"
        or prior.get("status") != "ready"
        or not isinstance(prior_publication, dict)
        or prior_publication.get("file_count") != len(INHERITED_NAMES)
        or prior_publication.get("total_bytes") != 89_238_225
        or not isinstance(prior_rows, list)
        or len(prior_rows) != len(INHERITED_NAMES)
        or tuple(row.get("filename") for row in prior_rows) != INHERITED_NAMES
    ):
        raise RuntimeError("prior Random-completeness package contract differs")

    gates = package.get("gates")
    prior_gate = gates.get("prior_release") if isinstance(gates, dict) else None
    archives = gates.get("archives") if isinstance(gates, dict) else None
    if (
        not isinstance(gates, dict)
        or gates.get("privacy") != {"forbidden_markers_found": 0}
        or prior_gate
        != {
            "bytes": 89_238_225,
            "file_count": 25,
            "identity_verified": True,
            "receipt_bytes": EXPECTED_PRIOR_RECEIPT_BYTES,
            "receipt_sha256": EXPECTED_PRIOR_RECEIPT_SHA256,
        }
        or not isinstance(archives, dict)
        or set(archives)
        != {
            "02_C140_COMPANION_C1_OFFLINE_READER.zip",
            "12_C140_COMPANION_C1_SOURCE_BACKEND.zip",
            "42_C140_COMPANION_C1_STATIC_QA_EVIDENCE.zip",
        }
    ):
        raise RuntimeError("C1 package gates differ")

    by_name = {row.get("filename"): row for row in rows if isinstance(row, dict)}
    if len(by_name) != len(EXPECTED_NAMES):
        raise RuntimeError("C1 package filenames are duplicated or malformed")
    for name, gate in archives.items():
        row = by_name.get(name)
        if (
            not isinstance(gate, dict)
            or not isinstance(row, dict)
            or gate.get("bytes") != row.get("bytes")
            or gate.get("sha256") != row.get("sha256")
            or gate.get("privacy") != {"forbidden_markers_found": 0}
            or not isinstance(gate.get("entries"), int)
            or gate.get("entries") <= 0
        ):
            raise RuntimeError(f"C1 archive gate differs: {name}")

    outputs = package.get("outputs")
    expected_outputs = {
        "checksums": "SHA256SUMS_C140_COMPANION_C1.txt",
        "manifest": "90_C140_COMPANION_C1_FULL_UNION_MANIFEST.csv",
        "root_receipt": "91_C140_COMPANION_C1_FULL_UNION_ROOT_RECEIPT.json",
    }
    if not isinstance(outputs, dict) or set(outputs) != set(expected_outputs):
        raise RuntimeError("C1 package output bindings differ")
    for key, name in expected_outputs.items():
        row = by_name[name]
        if outputs[key] != {
            "filename": name,
            "bytes": row["bytes"],
            "sha256": row["sha256"],
        }:
            raise RuntimeError(f"C1 package output binding differs: {key}")
    return rows, prior_rows


def snapshot() -> engine.Snapshot:
    """Freeze and validate the exact 33-file local union."""

    exact_payload(
        ENGINE_RELATIVE,
        "hardened GitHub release engine",
        EXPECTED_ENGINE_BYTES,
        EXPECTED_ENGINE_SHA256,
    )
    exact_payload(
        PACKAGER_RELATIVE,
        "C1 release packager",
        EXPECTED_PACKAGER_BYTES,
        EXPECTED_PACKAGER_SHA256,
    )
    prior_payload = exact_payload(
        PRIOR_PACKAGE_RELATIVE,
        "prior Random-completeness package receipt",
        EXPECTED_PRIOR_RECEIPT_BYTES,
        EXPECTED_PRIOR_RECEIPT_SHA256,
    )
    receipt_payload = exact_payload(
        PACKAGE_RELATIVE,
        "C1 package receipt",
        EXPECTED_PACKAGE_RECEIPT_BYTES,
        EXPECTED_PACKAGE_RECEIPT_SHA256,
    )
    prior = json_object(prior_payload, "prior Random-completeness package receipt")
    package = json_object(receipt_payload, "C1 package receipt")
    rows, prior_rows = validate_package_contract(package, prior)

    artifacts: list[engine.Artifact] = []
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    total = 0
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            raise RuntimeError(f"C1 package row {index} is malformed")
        name = raw.get("filename")
        relative = engine.canonical_relative(raw.get("source_path"), f"C1 row {index} path")
        declared_bytes = raw.get("bytes")
        declared_sha = raw.get("sha256")
        role = raw.get("role")
        lineage = raw.get("lineage")
        media_type = raw.get("media_type")
        if (
            raw.get("upload_order") != index + 1
            or name != EXPECTED_NAMES[index]
            or not isinstance(name, str)
            or engine.SAFE_NAME_RE.fullmatch(name) is None
            or engine.SENSITIVE_NAME_RE.search(name) is not None
            or relative != f"release/{name}"
            or isinstance(declared_bytes, bool)
            or not isinstance(declared_bytes, int)
            or declared_bytes <= 0
            or not isinstance(declared_sha, str)
            or engine.SHA256_RE.fullmatch(declared_sha) is None
            or not isinstance(role, str)
            or not role
            or not isinstance(lineage, str)
            or not lineage
            or not isinstance(media_type, str)
            or "/" not in media_type
            or raw.get("primary_reader") is not (index == 0)
            or name in seen_names
            or relative in seen_paths
        ):
            raise RuntimeError(f"C1 package row {index} is unsafe or differs")
        payload = engine.read_confined(relative, f"C1 release asset {name}")
        if len(payload) != declared_bytes or sha256(payload) != declared_sha:
            raise RuntimeError(f"C1 release asset differs from its receipt: {name}")
        if index < len(INHERITED_NAMES):
            if raw != prior_rows[index]:
                raise RuntimeError(f"inherited Random-completeness asset changed: {name}")
        elif (
            role != EXPECTED_ADDITION_ROLES.get(name)
            or lineage != EXPECTED_ADDITION_LINEAGES.get(name)
        ):
            raise RuntimeError(f"C1 addition role or lineage differs: {name}")
        artifacts.append(
            engine.Artifact(
                name=name,
                path=relative,
                bytes=declared_bytes,
                sha256=declared_sha,
                payload=payload,
                role=role,
                lineage=lineage,
                media_type=media_type,
            )
        )
        total += declared_bytes
        if total > engine.MAX_RELEASE_BYTES:
            raise RuntimeError("C1 release exceeds the 500 MB task cap")
        seen_names.add(name)
        seen_paths.add(relative)

    if total != package["publication_inventory"]["bytes"]:
        raise RuntimeError("C1 cumulative package byte total differs")
    if engine.read_confined(PACKAGE_RELATIVE, "C1 package receipt") != receipt_payload:
        raise RuntimeError("C1 package receipt changed during snapshot")
    inherited_count = len(INHERITED_NAMES)
    return engine.Snapshot(
        package=package,
        package_receipt_bytes=len(receipt_payload),
        package_receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited_files=tuple(artifacts[:inherited_count]),
        additions=tuple(artifacts[inherited_count:]),
    )


def receipt_base(snap: engine.Snapshot, commit: str) -> dict[str, object]:
    return {
        "version": PACKAGE_VERSION,
        "repository": engine.REPOSITORY_URL,
        "tag": TAG,
        "commit": commit,
        "release_scope": EXPECTED_COVERAGE,
        "component_separated_rights": True,
        "aggregate_uniform_relicense": False,
        "local_inventory": [
            {
                "name": item.name,
                "bytes": item.bytes,
                "sha256": item.sha256,
                "role": item.role,
                "lineage": item.lineage,
            }
            for item in snap.files
        ],
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "prior_random_completeness_files_preserved": len(snap.inherited_files),
        "companion_c1_additions": len(snap.additions),
        "package_receipt": {
            "path": PACKAGE_RELATIVE,
            "bytes": snap.package_receipt_bytes,
            "sha256": snap.package_receipt_sha256,
        },
        "translation_provenance": MODEL_PROVENANCE,
        "browser_processes_used": False,
        "machine_local_paths_recorded": False,
    }


def verification_payload(
    snap: engine.Snapshot,
    commit: str,
    public: dict[str, object],
    prior: dict[str, object],
    *,
    control_plane_credential_access: bool,
) -> dict[str, object]:
    return {
        "schema": VERIFICATION_SCHEMA,
        "status": "pass",
        **receipt_base(snap, commit),
        "mode": "public-byte-verification",
        "public_asset_readback_anonymous": True,
        "control_plane_credential_access": control_plane_credential_access,
        "credential_access": control_plane_credential_access,
        "remote_writes": False,
        "prior_release_untouched": True,
        "prior_release_witness": prior,
        "public": public,
    }


def contract_summary(snap: engine.Snapshot) -> dict[str, object]:
    return {
        "mode": "contract-check",
        "status": "pass",
        "schema": PACKAGE_SCHEMA,
        "version": PACKAGE_VERSION,
        "tag": TAG,
        "annotated_tag_required": True,
        "files": len(snap.files),
        "bytes": snap.total_bytes,
        "inherited_files": len(snap.inherited_files),
        "additions": len(snap.additions),
        "primary_file": snap.files[0].name,
        "c140_course": "incomplete",
        "c140_original_companion": "C1 coherent partial checkpoint complete",
        "component_separated_rights": True,
        "package_receipt_sha256": snap.package_receipt_sha256,
        "credential_access": False,
        "network_access": False,
        "browser_processes_used": False,
    }


def configure_engine() -> None:
    engine.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    engine.VERIFICATION_RECEIPT = VERIFICATION_RECEIPT
    engine.PUBLICATION_RECEIPT = PUBLICATION_RECEIPT
    engine.TAG = TAG
    engine.PRIOR_TAG = PRIOR_TAG
    engine.PRIOR_RELEASE_ID = PRIOR_RELEASE_ID
    engine.PRIOR_COMMIT = PRIOR_COMMIT
    engine.PRIOR_TAG_OBJECT = PRIOR_TAG_OBJECT
    engine.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    engine.PACKAGE_VERSION = PACKAGE_VERSION
    engine.VERIFICATION_SCHEMA = VERIFICATION_SCHEMA
    engine.PUBLICATION_SCHEMA = PUBLICATION_SCHEMA
    engine.MODEL_PROVENANCE = MODEL_PROVENANCE
    engine.TITLE = TITLE
    engine.BODY = BODY
    engine.TAG_MESSAGE = TAG_MESSAGE
    engine.EXPECTED_NAMES = EXPECTED_NAMES
    engine.EXPECTED_ADDITION_ROLES = EXPECTED_ADDITION_ROLES
    engine.EXPECTED_ADDITION_LINEAGES = EXPECTED_ADDITION_LINEAGES
    engine.HEADERS = {
        **engine.HEADERS,
        "User-Agent": "O006-C140-companion-c1-release/2026.08.28",
    }
    engine.snapshot = snapshot
    engine.receipt_base = receipt_base
    engine.verification_payload = verification_payload
    engine.contract_summary = contract_summary


if __name__ == "__main__":
    configure_engine()
    engine.main()
