#!/usr/bin/env python3
"""Publish/verify the cumulative C140 companion C2 GitHub release.

The hardened release transaction remains in the Random-completeness engine.
This adapter binds it to the byte-identical 33-file C1 release plus exactly
eight C2 additions. ``--contract-only`` is wholly local and side-effect free.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import package_c140_companion_c2_release as packager
import publish_verify_github_c140_companion_c1 as c1


engine = c1.engine
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RELATIVE = "build/C140_COMPANION_C2_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / PACKAGE_RELATIVE
VERIFICATION_RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-29_C140_COMPANION_C2.json"
PUBLICATION_RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_PUBLICATION_2026-08-29_C140_COMPANION_C2.json"

PACKAGE_SCHEMA = "o006.c140.companion-c2-release-package.v1"
PACKAGE_VERSION = "2026.08.29.c140-companion-c2"
VERIFICATION_SCHEMA = "o006.c140.companion-c2.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c2.github-release-publication.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TAG = "v2026.08.29.c140-companion-c2"
PRIOR_TAG = "v2026.08.28.c140-companion-c1"
PRIOR_RELEASE_ID = 378_644_493
PRIOR_COMMIT = "cfcfb5b172f04f6b77b98fa04fb093520cdb8881"
PRIOR_TAG_OBJECT = "1d81208e7537645f8ae68252fa945c3b4d614ea4"

TITLE = "O006/C140 Statistika Matematis — Pendamping Orisinal C2 (Bahasa Indonesia)"
BODY = (
    "Rilis kumulatif O006/C140 ini mempertahankan 33 aset C1 secara "
    "byte-identik—pembaca Penn State STAT 415 lengkap, donor kelengkapan "
    "Random, dan checkpoint C1—lalu menambahkan checkpoint C2 pendamping "
    "orisinal. C2 menutup jembatan model linear Gaussian matriks melalui "
    "D008–D011, SIM005, dan MS12: geometri proyeksi desain tetap, OLS/MLE "
    "Gaussian, Gauss–Markov, hukum sampling eksak, inferensi t/F, selang "
    "kepercayaan/prediksi, ANOVA, diagnostik, leverage, pengaruh, "
    "misspecification, dan heteroskedastisitas. Pendamping kumulatif berisi "
    "23 dokumen, lima simulasi, dan 50 soal berjawab lengkap. C140 masih "
    "incomplete: perbandingan Bayesian–frequentist, set penguasaan, asesmen, "
    "dan capstone lanjutan belum termasuk. Hak tetap dipisahkan per komponen; "
    "agregat tidak direlisensi seragam. Provenans: " + MODEL_PROVENANCE + "."
)
TAG_MESSAGE = "O006/C140 original companion C2 coherent partial checkpoint (2026-08-29)"

INHERITED_NAMES = tuple(c1.EXPECTED_NAMES)
ADDITION_NAMES = (
    packager.OFFLINE_NAME,
    packager.SOURCE_NAME,
    packager.NOTES_NAME,
    packager.LICENSE_NAME,
    packager.QA_NAME,
    packager.MANIFEST_NAME,
    packager.CHECKSUM_NAME,
    packager.ROOT_NAME,
)
EXPECTED_NAMES = INHERITED_NAMES + ADDITION_NAMES
EXPECTED_ADDITION_ROLES = {
    packager.OFFLINE_NAME: "partial-c2-offline-html-reader",
    packager.SOURCE_NAME: "partial-c2-resumable-source-backend",
    packager.NOTES_NAME: "partial-c2-scope-status-provenance",
    packager.LICENSE_NAME: "partial-c2-component-rights",
    packager.QA_NAME: "partial-c2-browser-free-static-qa-evidence",
    packager.MANIFEST_NAME: "c2-cumulative-union-manifest",
    packager.CHECKSUM_NAME: "c2-cumulative-union-checksums",
    packager.ROOT_NAME: "c2-cumulative-union-root-receipt",
}
EXPECTED_ADDITION_LINEAGES = {
    **{name: "c140-original-companion-c2" for name in ADDITION_NAMES[:5]},
    **{name: "c140-original-companion-c2-union" for name in ADDITION_NAMES[5:]},
}
EXPECTED_COVERAGE = {
    "c140_course": "incomplete",
    "c140_original_companion": "C2 coherent partial checkpoint complete",
    "penn_state_spine": "complete",
    "random_completeness_donor": "complete",
}
EXPECTED_RIGHTS = {"aggregate_uniform_relicense": False, "platform_license": "other-open"}
EXPECTED_LINEAGE = {
    "base_record_doi": "10.5281/zenodo.22148810",
    "base_record_id": "22148810",
    "concept_doi": "10.5281/zenodo.22077422",
    "create_competing_concept": False,
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def computed_contract() -> tuple[dict[str, bytes], bytes, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    outputs, receipt_payload = packager.compute()
    try:
        package = json.loads(receipt_payload)
    except json.JSONDecodeError as exc:
        raise RuntimeError("computed C2 package receipt is invalid") from exc
    _, prior_rows = packager.validate_prior()
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("coverage") != EXPECTED_COVERAGE
        or package.get("rights") != EXPECTED_RIGHTS
        or package.get("lineage") != EXPECTED_LINEAGE
        or not isinstance(rows, list)
        or len(rows) != len(EXPECTED_NAMES)
        or publication.get("file_count") != len(EXPECTED_NAMES)
        or tuple(row.get("filename") for row in rows if isinstance(row, dict)) != EXPECTED_NAMES
    ):
        raise RuntimeError("computed C2 package contract differs")
    if rows[: len(prior_rows)] != prior_rows:
        raise RuntimeError("C2 package does not preserve every C1 inventory row byte-for-byte")
    by_name = {str(row.get("filename")): row for row in rows if isinstance(row, dict)}
    if len(by_name) != len(EXPECTED_NAMES):
        raise RuntimeError("C2 package filenames are duplicated or malformed")
    for name in ADDITION_NAMES:
        row = by_name[name]
        if (
            row.get("role") != EXPECTED_ADDITION_ROLES[name]
            or row.get("lineage") != EXPECTED_ADDITION_LINEAGES[name]
            or outputs.get(name) is None
            or len(outputs[name]) != row.get("bytes")
            or sha256(outputs[name]) != row.get("sha256")
        ):
            raise RuntimeError(f"C2 addition contract differs: {name}")
    return outputs, receipt_payload, package, rows, prior_rows


def snapshot() -> engine.Snapshot:
    outputs, computed_receipt, package, rows, prior_rows = computed_contract()
    if not PACKAGE_RECEIPT.is_file() or PACKAGE_RECEIPT.read_bytes() != computed_receipt:
        raise RuntimeError("written C2 package receipt is missing or differs; run the C2 packager --write")
    artifacts: list[engine.Artifact] = []
    total = 0
    for index, row in enumerate(rows):
        name = str(row["filename"])
        relative = engine.canonical_relative(row.get("source_path"), f"C2 row {index} path")
        if (
            row.get("upload_order") != index + 1
            or relative != f"release/{name}"
            or engine.SAFE_NAME_RE.fullmatch(name) is None
            or engine.SENSITIVE_NAME_RE.search(name) is not None
            or row.get("primary_reader") is not (index == 0)
        ):
            raise RuntimeError(f"C2 package row {index} is unsafe or differs")
        payload = engine.read_confined(relative, f"C2 release asset {name}")
        if payload != outputs[name] or len(payload) != row["bytes"] or sha256(payload) != row["sha256"]:
            raise RuntimeError(f"C2 release asset differs from package: {name}")
        if index < len(prior_rows) and row != prior_rows[index]:
            raise RuntimeError(f"inherited C1 asset changed: {name}")
        artifacts.append(engine.Artifact(
            name=name,
            path=relative,
            bytes=int(row["bytes"]),
            sha256=str(row["sha256"]),
            payload=payload,
            role=str(row["role"]),
            lineage=str(row["lineage"]),
            media_type=str(row["media_type"]),
        ))
        total += len(payload)
        if total > engine.MAX_RELEASE_BYTES:
            raise RuntimeError("C2 release exceeds the 500 MB task cap")
    if total != package["publication_inventory"]["bytes"]:
        raise RuntimeError("C2 cumulative package byte total differs")
    return engine.Snapshot(
        package=package,
        package_receipt_bytes=len(computed_receipt),
        package_receipt_sha256=sha256(computed_receipt),
        files=tuple(artifacts),
        inherited_files=tuple(artifacts[: len(prior_rows)]),
        additions=tuple(artifacts[len(prior_rows):]),
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
            {"name": item.name, "bytes": item.bytes, "sha256": item.sha256, "role": item.role, "lineage": item.lineage}
            for item in snap.files
        ],
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "prior_c1_files_preserved": len(snap.inherited_files),
        "companion_c2_additions": len(snap.additions),
        "package_receipt": {"path": PACKAGE_RELATIVE, "bytes": snap.package_receipt_bytes, "sha256": snap.package_receipt_sha256},
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


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt_payload, package, rows, prior_rows = computed_contract()
    return {
        "annotated_tag_required": True,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "component_separated_rights": True,
        "credential_access": False,
        "files": len(rows),
        "inherited_files": len(prior_rows),
        "mode": "contract-only",
        "network_access": False,
        "new_files": len(rows) - len(prior_rows),
        "package_receipt_sha256": sha256(receipt_payload),
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "tag": TAG,
        "version": PACKAGE_VERSION,
    }


def contract_summary(snap: engine.Snapshot) -> dict[str, object]:
    result = local_contract_summary()
    result.update({
        "mode": "contract-check",
        "primary_file": snap.files[0].name,
        "c140_course": "incomplete",
        "c140_original_companion": "C2 coherent partial checkpoint complete",
    })
    return result


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
    engine.HEADERS = {**engine.HEADERS, "User-Agent": "O006-C140-companion-c2-release/2026.08.29"}
    engine.snapshot = snapshot
    engine.receipt_base = receipt_base
    engine.verification_payload = verification_payload
    engine.contract_summary = contract_summary


def main() -> None:
    if sys.argv[1:] == ["--contract-only"]:
        print(json.dumps(local_contract_summary(), sort_keys=True))
        return
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
