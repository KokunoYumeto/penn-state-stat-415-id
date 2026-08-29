#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative C140 companion C3 release.

This fail-closed adapter reuses the hardened GitHub transaction engine.  Its
local contract preserves the exact anonymously verified 41-file C2 replay-fix
release and appends only the eight artifacts admitted by the C3 packager.
``--contract-only`` performs no network, credential, Git, browser, or remote
publication operation.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote

import package_c140_companion_c3_release as packager
import publish_verify_github_c140_companion_c2_replay_fix as c2fix


engine = c2fix.engine
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RELATIVE = "build/C140_COMPANION_C3_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / PACKAGE_RELATIVE
TOKEN_FILE = (
    Path.home() / "Documents" / "Obsidian notes" / "Github Tokens.md"
)
PRIOR_RECEIPT_RELATIVE = (
    "00_control/GITHUB_RELEASE_RECEIPT_2026-08-29_"
    "C140_COMPANION_C2_REPLAY_FIX.json"
)
VERIFICATION_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-29_C140_COMPANION_C3.json"
)
PUBLICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_PUBLICATION_2026-08-29_C140_COMPANION_C3.json"
)

PACKAGE_SCHEMA = "o006.c140.companion-c3-release-package.v1"
PACKAGE_VERSION = "2026.08.29.c140-companion-c3"
PACKAGE_RECEIPT_BYTES = 30_151
PACKAGE_RECEIPT_SHA256 = (
    "d78c911bdc2837a3fdddd3f71e6b7211fde46a8668d85a9c00f750cf82716637"
)
VERIFICATION_SCHEMA = "o006.c140.companion-c3.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c3.github-release-publication.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TAG = "v2026.08.29.c140-companion-c3"
PRIOR_TAG = "v2026.08.29.c140-companion-c2-replay-fix"
PRIOR_RELEASE_ID = 378_957_927
PRIOR_COMMIT = "7f464d3704c6bbe79fcbf94d5fccd567baa1865f"
PRIOR_TAG_OBJECT = "f1cc5f2b1aeb41e9731098449f06a23ab40fb65a"
PRIOR_RECEIPT_BYTES = 48_205
PRIOR_RECEIPT_SHA256 = (
    "67e2c95af03695fa4e69de9b8987d755ac24b7f8d7151b3cbf4d68367030917d"
)
PRIOR_RECEIPT_SCHEMA = (
    "o006.c140.companion-c2-replay-fix.github-release-readback.v1"
)
PRIOR_FILE_COUNT = 41
PRIOR_TOTAL_BYTES = 91_249_199

TITLE = "O006/C140 Statistika Matematis — Pendamping Orisinal C3 (Bahasa Indonesia)"
BODY = (
    "Rilis kumulatif ini mempertahankan secara byte-identik seluruh 41 aset "
    "checkpoint C2 replay-fix yang telah dibaca balik secara anonim, lalu "
    "menambahkan tepat delapan aset C3. C3 menutup D012–D013, SIM006, dan "
    "MS11: fondasi probabilitas serta keputusan Bayesian, perbandingan dan "
    "kalibrasi Bayesian–frequentist, simulasi kalibrasi reproduktif, dan set "
    "penguasaan berjawab lengkap. Pendamping kumulatif kini mencakup "
    "D001–D013, SIM001–SIM006, MS07–MS12, dan CA01. Keseluruhan C140 masih "
    "incomplete: set penguasaan yang tersisa, tiga asesmen kumulatif, dan dua "
    "capstone belum termasuk. Hak Penn State, donor Random, dan pendamping "
    "orisinal tetap dipisahkan per komponen; agregat tidak direlisensi secara "
    "seragam. Produksi dan QA bersifat tanpa browser. Provenans: "
    + MODEL_PROVENANCE
    + "."
)
TAG_MESSAGE = "O006/C140 original companion C3 coherent partial checkpoint (2026-08-29)"

INHERITED_NAMES = tuple(c2fix.EXPECTED_NAMES)
ADDITION_SPECS = (
    (
        packager.OFFLINE_NAME,
        851_608,
        "4dfb8f0a18c45355d8da58c12700016662751d7411afe6f151de61fc2fc6a850",
        "partial-c3-offline-html-reader",
        "c140-original-companion-c3",
        "application/zip",
    ),
    (
        packager.SOURCE_NAME,
        304_324,
        "8f47959548601a5d24caac321c70de14c815abb7bcff2b4eb894957ca1ec0e7d",
        "partial-c3-resumable-source-backend",
        "c140-original-companion-c3",
        "application/zip",
    ),
    (
        packager.NOTES_NAME,
        1_535,
        "e747bc107c6950a4dd745469a717a1503537677cb6e3e3a2bdd427e320f5d7fe",
        "partial-c3-scope-status-provenance",
        "c140-original-companion-c3",
        "text/markdown",
    ),
    (
        packager.LICENSE_NAME,
        642,
        "f8913e62477ebb57d3370abb52469ac54292e2b2053db9a41fa3cb3cb02967f2",
        "partial-c3-component-rights",
        "c140-original-companion-c3",
        "text/markdown",
    ),
    (
        packager.QA_NAME,
        28_092,
        "6bfd886cc4a10b7d91e8eb99d6db6a2acb1e464e43579f3b122c69ca8d9001a1",
        "partial-c3-browser-free-static-qa-evidence",
        "c140-original-companion-c3",
        "application/zip",
    ),
    (
        packager.MANIFEST_NAME,
        11_828,
        "8134e72d3deeef1a5a8689d262ec6a310317eb94870ba65bf70a1713de422426",
        "c3-cumulative-union-manifest",
        "c140-original-companion-c3-union",
        "text/csv",
    ),
    (
        packager.CHECKSUM_NAME,
        5_162,
        "a91fcde8ff68dd5e9ae74ab47cb7a5dda006fa3b8690be379c780be4971e7456",
        "c3-cumulative-union-checksums",
        "c140-original-companion-c3-union",
        "text/plain",
    ),
    (
        packager.ROOT_NAME,
        23_667,
        "9f0535439e08d16a76c63de7cfae7ded5afc23da209dab29bf71ccaf71ac0dcf",
        "c3-cumulative-union-root-receipt",
        "c140-original-companion-c3-union",
        "application/json",
    ),
)
ADDITION_NAMES = tuple(item[0] for item in ADDITION_SPECS)
EXPECTED_NAMES = INHERITED_NAMES + ADDITION_NAMES
EXPECTED_ADDITION_ROLES = {item[0]: item[3] for item in ADDITION_SPECS}
EXPECTED_ADDITION_LINEAGES = {item[0]: item[4] for item in ADDITION_SPECS}
EXPECTED_FILE_COUNT = 49
EXPECTED_TOTAL_BYTES = 92_476_057

EXPECTED_COVERAGE = {
    "c140_course": "incomplete",
    "c140_original_companion": "C3 coherent partial checkpoint complete",
    "c3_batch": "complete",
    "penn_state_spine": "complete",
    "random_completeness_donor": "complete",
    "remaining": "remaining mastery sets, three cumulative assessments, and two capstones",
}
EXPECTED_RIGHTS = {
    "aggregate_uniform_relicense": False,
    "collection_license_bytes": 2_295,
    "collection_license_sha256": (
        "1d7c6e8f38292dc66153a83034475341e9e6e4efe7b28b42b323f182c8aca4df"
    ),
    "component_license_bytes": 642,
    "component_license_sha256": (
        "f8913e62477ebb57d3370abb52469ac54292e2b2053db9a41fa3cb3cb02967f2"
    ),
    "component_licenses_unchanged": True,
    "platform_license": "other-open",
}
EXPECTED_LINEAGE = {
    "base_record_doi": "10.5281/zenodo.22160621",
    "base_record_id": "22160621",
    "concept_doi": "10.5281/zenodo.22077422",
    "concept_record_id": "22077422",
    "create_competing_concept": False,
}
EXPECTED_PRESERVATION = {
    "inherited_file_count": PRIOR_FILE_COUNT,
    "inherited_files_byte_identical": True,
    "new_file_count": len(ADDITION_NAMES),
    "new_substantive_file_count": 5,
}
EXPECTED_READER_ORDER = {
    "c3_first_upload_order": PRIOR_FILE_COUNT + 1,
    "epub_upload_order": 2,
    "inherited_union_first": True,
    "pdf_upload_order": 1,
}
EXPECTED_PACKAGER = {
    "browser_processes_used": False,
    "credential_access": False,
    "git_operations": False,
    "network_access": False,
    "path": "scripts/package_c140_companion_c3_release.py",
    "publication_side_effects": False,
    "recursive_repository_discovery": False,
    "source_bytes": 41_024,
    "source_sha256": "6a23e242f551497da1cb7b651acbf3dab2b0369bf47b1d9d89e3567c9f1fbc94",
}
EXPECTED_BASE = {
    "anonymous_readback": True,
    "bytes": PRIOR_TOTAL_BYTES,
    "concept_doi": "10.5281/zenodo.22077422",
    "concept_record_id": "22077422",
    "file_count": PRIOR_FILE_COUNT,
    "package_receipt": {
        "bytes": 23_739,
        "sha256": "c51b7c89030b9f9be8ed740a2a7a39e2ef1b28de40357eb7dc188a723eee2bfd",
    },
    "public_readback": {
        "bytes": 16_719,
        "sha256": "0f17f4f63eb2284563f547d35349d102c12244fd1d092898df0390ef5d7c11fa",
    },
    "record_doi": "10.5281/zenodo.22160621",
    "record_id": "22160621",
    "version": "2026.08.29.c140-companion-c2-replay-fix",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def prior_receipt_contract() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load the immutable C2 GitHub witness without network or credentials."""
    payload = engine.read_confined(PRIOR_RECEIPT_RELATIVE, "C2 GitHub public readback")
    if len(payload) != PRIOR_RECEIPT_BYTES or sha256(payload) != PRIOR_RECEIPT_SHA256:
        raise RuntimeError("C2 GitHub public-readback receipt identity differs")
    receipt = json_object(payload, "C2 GitHub public-readback receipt")
    public = receipt.get("public")
    public_files = public.get("files") if isinstance(public, dict) else None
    local = receipt.get("local_inventory")
    annotated = public.get("annotated_tag") if isinstance(public, dict) else None
    if (
        receipt.get("schema") != PRIOR_RECEIPT_SCHEMA
        or receipt.get("status") != "pass"
        or receipt.get("mode") != "public-byte-verification"
        or receipt.get("tag") != PRIOR_TAG
        or receipt.get("commit") != PRIOR_COMMIT
        or receipt.get("local_files") != PRIOR_FILE_COUNT
        or receipt.get("local_bytes") != PRIOR_TOTAL_BYTES
        or receipt.get("public_asset_readback_anonymous") is not True
        or receipt.get("credential_access") is not False
        or receipt.get("remote_writes") is not False
        or receipt.get("browser_processes_used") is not False
        or not isinstance(public, dict)
        or public.get("release_id") != PRIOR_RELEASE_ID
        or public.get("tag") != PRIOR_TAG
        or public.get("file_count") != PRIOR_FILE_COUNT
        or public.get("total_bytes") != PRIOR_TOTAL_BYTES
        or public.get("reader_first") is not True
        or public.get("public_asset_readback_anonymous") is not True
        or not isinstance(annotated, dict)
        or annotated.get("annotated") is not True
        or annotated.get("tag_object") != PRIOR_TAG_OBJECT
        or annotated.get("peeled_commit") != PRIOR_COMMIT
        or not isinstance(local, list)
        or not isinstance(public_files, list)
        or len(local) != PRIOR_FILE_COUNT
        or len(public_files) != PRIOR_FILE_COUNT
    ):
        raise RuntimeError("C2 GitHub public-readback contract differs")
    inventory: list[dict[str, Any]] = []
    for index, (local_row, public_row) in enumerate(
        zip(local, public_files, strict=True)
    ):
        if not isinstance(local_row, dict) or not isinstance(public_row, dict):
            raise RuntimeError(f"malformed C2 GitHub inventory row {index}")
        name = local_row.get("name")
        if (
            name != INHERITED_NAMES[index]
            or public_row.get("name") != name
            or public_row.get("bytes") != local_row.get("bytes")
            or public_row.get("sha256") != local_row.get("sha256")
            or public_row.get("validated_download") is not True
            or public_row.get("http_status") != 200
            or public_row.get("automatic_redirects_followed") is not False
            or not isinstance(local_row.get("bytes"), int)
            or local_row.get("bytes") <= 0
            or not isinstance(local_row.get("sha256"), str)
            or engine.SHA256_RE.fullmatch(local_row["sha256"]) is None
            or not isinstance(local_row.get("role"), str)
            or not isinstance(local_row.get("lineage"), str)
        ):
            raise RuntimeError(f"C2 GitHub inventory identity differs at row {index}")
        inventory.append(dict(local_row))
    if sum(int(row["bytes"]) for row in inventory) != PRIOR_TOTAL_BYTES:
        raise RuntimeError("C2 GitHub inventory byte total differs")
    return receipt, inventory


def computed_contract() -> tuple[
    dict[str, bytes],
    bytes,
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    outputs, receipt_payload = packager.compute()
    if (
        len(receipt_payload) != PACKAGE_RECEIPT_BYTES
        or sha256(receipt_payload) != PACKAGE_RECEIPT_SHA256
    ):
        raise RuntimeError("computed C3 package receipt identity differs")
    package = json_object(receipt_payload, "computed C3 package receipt")
    _prior_receipt, prior_inventory = prior_receipt_contract()
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != PACKAGE_VERSION
        or package.get("status") != "ready"
        or package.get("coverage") != EXPECTED_COVERAGE
        or package.get("rights") != EXPECTED_RIGHTS
        or package.get("lineage") != EXPECTED_LINEAGE
        or package.get("preservation") != EXPECTED_PRESERVATION
        or package.get("reader_order") != EXPECTED_READER_ORDER
        or package.get("packager") != EXPECTED_PACKAGER
        or package.get("base_public_union") != EXPECTED_BASE
        or not isinstance(publication, dict)
        or publication.get("file_count") != EXPECTED_FILE_COUNT
        or publication.get("bytes") != EXPECTED_TOTAL_BYTES
        or not isinstance(rows, list)
        or len(rows) != EXPECTED_FILE_COUNT
        or tuple(row.get("filename") for row in rows if isinstance(row, dict))
        != EXPECTED_NAMES
        or tuple(outputs) != EXPECTED_NAMES
    ):
        raise RuntimeError("computed C3 package contract differs")

    gates = package.get("gates")
    archives = gates.get("archives") if isinstance(gates, dict) else None
    if (
        not isinstance(gates, dict)
        or gates.get("privacy") != {"forbidden_markers_found": 0}
        or gates.get("publication_size")
        != {"bytes": EXPECTED_TOTAL_BYTES, "cap_bytes": 500_000_000, "status": "pass"}
        or gates.get("c3_boundary")
        != {
            "backend_entities": 812,
            "backend_relations": 1_084,
            "documents": 27,
            "html_files": 57,
            "problems": 58,
            "simulations": 6,
            "status": "pass",
        }
        or not isinstance(archives, dict)
        or set(archives) != {packager.OFFLINE_NAME, packager.SOURCE_NAME, packager.QA_NAME}
    ):
        raise RuntimeError("computed C3 package gates differ")

    for index, prior in enumerate(prior_inventory):
        row = rows[index]
        if (
            not isinstance(row, dict)
            or row.get("filename") != prior["name"]
            or row.get("bytes") != prior["bytes"]
            or row.get("sha256") != prior["sha256"]
            or row.get("role") != prior["role"]
            or row.get("lineage") != prior["lineage"]
        ):
            raise RuntimeError(f"inherited C2 GitHub asset changed at row {index}")

    for offset, spec in enumerate(ADDITION_SPECS, start=PRIOR_FILE_COUNT):
        name, size, digest, role, lineage, media_type = spec
        row = rows[offset]
        payload = outputs.get(name)
        if (
            not isinstance(row, dict)
            or row.get("filename") != name
            or row.get("bytes") != size
            or row.get("sha256") != digest
            or row.get("role") != role
            or row.get("lineage") != lineage
            or row.get("media_type") != media_type
            or payload is None
            or len(payload) != size
            or sha256(payload) != digest
        ):
            raise RuntimeError(f"C3 addition contract differs: {name}")
        archive = archives.get(name)
        if name in {packager.OFFLINE_NAME, packager.SOURCE_NAME, packager.QA_NAME} and (
            not isinstance(archive, dict)
            or archive.get("bytes") != size
            or archive.get("sha256") != digest
            or archive.get("privacy") != {"forbidden_markers_found": 0}
        ):
            raise RuntimeError(f"C3 archive gate differs: {name}")
    return outputs, receipt_payload, package, rows, prior_inventory


def snapshot() -> engine.Snapshot:
    outputs, receipt_payload, package, rows, prior_inventory = computed_contract()
    if not PACKAGE_RECEIPT.is_file() or PACKAGE_RECEIPT.read_bytes() != receipt_payload:
        raise RuntimeError("written C3 package receipt differs; run the C3 packager --write")
    artifacts: list[engine.Artifact] = []
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"malformed C3 package row {index}")
        name = str(row.get("filename", ""))
        relative = engine.canonical_relative(row.get("source_path"), f"C3 row {index} path")
        payload = engine.read_confined(relative, f"C3 release asset {name}")
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_NAMES[index]
            or relative != f"release/{name}"
            or engine.SAFE_NAME_RE.fullmatch(name) is None
            or engine.SENSITIVE_NAME_RE.search(name) is not None
            or row.get("primary_reader") is not (index == 0)
            or not isinstance(row.get("media_type"), str)
            or "/" not in row["media_type"]
            or name in seen_names
            or relative in seen_paths
            or outputs.get(name) != payload
            or len(payload) != row.get("bytes")
            or sha256(payload) != row.get("sha256")
        ):
            raise RuntimeError(f"C3 asset is unsafe or differs: {name}")
        if index < PRIOR_FILE_COUNT:
            prior = prior_inventory[index]
            if (
                name != prior["name"]
                or len(payload) != prior["bytes"]
                or sha256(payload) != prior["sha256"]
                or row.get("role") != prior["role"]
                or row.get("lineage") != prior["lineage"]
            ):
                raise RuntimeError(f"inherited C2 asset changed: {name}")
        artifacts.append(
            engine.Artifact(
                name=name,
                path=relative,
                bytes=len(payload),
                sha256=sha256(payload),
                payload=payload,
                role=str(row.get("role")),
                lineage=str(row.get("lineage")),
                media_type=str(row.get("media_type")),
            )
        )
        total += len(payload)
        if total > engine.MAX_RELEASE_BYTES:
            raise RuntimeError("C3 release exceeds the 500 MB task cap")
        seen_names.add(name)
        seen_paths.add(relative)
    if total != EXPECTED_TOTAL_BYTES:
        raise RuntimeError("C3 cumulative package byte total differs")
    return engine.Snapshot(
        package=package,
        package_receipt_bytes=len(receipt_payload),
        package_receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited_files=tuple(artifacts[:PRIOR_FILE_COUNT]),
        additions=tuple(artifacts[PRIOR_FILE_COUNT:]),
    )


def prior_release_witness(
    snap: engine.Snapshot,
    control_session: Any | None = None,
) -> dict[str, object]:
    """Revalidate the exact prior 41-file release and annotated tag."""
    del snap
    _receipt, inventory = prior_receipt_contract()
    control = control_session or engine.public_session()
    ref_url = f"{engine.REPOSITORY_API}/git/ref/tags/{quote(PRIOR_TAG, safe='')}"
    ref = engine.api_json(control, "GET", ref_url, action="read prior C2 replay-fix tag", timeout=120)
    obj = ref.get("object")
    if (
        ref.get("ref") != f"refs/tags/{PRIOR_TAG}"
        or not isinstance(obj, dict)
        or obj.get("type") != "tag"
        or obj.get("sha") != PRIOR_TAG_OBJECT
    ):
        raise RuntimeError("prior C2 replay-fix annotated-tag witness differs")
    tag = engine.api_json(
        control,
        "GET",
        f"{engine.REPOSITORY_API}/git/tags/{PRIOR_TAG_OBJECT}",
        action="peel prior C2 replay-fix annotated tag",
        timeout=120,
    )
    target = tag.get("object")
    if (
        tag.get("sha") != PRIOR_TAG_OBJECT
        or tag.get("tag") != PRIOR_TAG
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != PRIOR_COMMIT
    ):
        raise RuntimeError("prior C2 replay-fix tag no longer peels to its fixed commit")
    release = engine.release_by_tag(control, PRIOR_TAG, allow_missing=False)
    assert release is not None
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    by_name = {str(row.get("name")): row for row in assets}
    expected = {row["name"]: row for row in inventory}
    if (
        release.get("id") != PRIOR_RELEASE_ID
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or len(assets) != PRIOR_FILE_COUNT
        or set(by_name) != set(expected)
    ):
        raise RuntimeError("prior C2 replay-fix release witness differs")
    witness_files = []
    for item in inventory:
        remote = by_name[item["name"]]
        if remote.get("size") != item["bytes"] or remote.get("state") != "uploaded":
            raise RuntimeError(f"prior C2 replay-fix asset metadata differs: {item['name']}")
        witness_files.append(
            {"name": item["name"], "bytes": item["bytes"], "sha256": item["sha256"]}
        )
    witness = {
        "release_id": PRIOR_RELEASE_ID,
        "tag": PRIOR_TAG,
        "url": f"{engine.REPOSITORY_URL}/releases/tag/{PRIOR_TAG}",
        "annotated_tag": {
            "ref_url": ref_url,
            "tag_object": PRIOR_TAG_OBJECT,
            "peeled_commit": PRIOR_COMMIT,
        },
        "files": witness_files,
        "file_count": PRIOR_FILE_COUNT,
        "total_bytes": PRIOR_TOTAL_BYTES,
        "durable_receipt": {
            "path": PRIOR_RECEIPT_RELATIVE,
            "bytes": PRIOR_RECEIPT_BYTES,
            "sha256": PRIOR_RECEIPT_SHA256,
        },
    }
    return {**witness, "witness_sha256": sha256(engine.canonical_json(witness))}


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
        "prior_c2_replay_fix_files_preserved": len(snap.inherited_files),
        "companion_c3_additions": len(snap.additions),
        "companion_c3_replacements": 0,
        "package_receipt": {
            "path": PACKAGE_RELATIVE,
            "bytes": snap.package_receipt_bytes,
            "sha256": snap.package_receipt_sha256,
        },
        "prior_public_receipt": {
            "path": PRIOR_RECEIPT_RELATIVE,
            "bytes": PRIOR_RECEIPT_BYTES,
            "sha256": PRIOR_RECEIPT_SHA256,
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


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt, package, rows, prior = computed_contract()
    return {
        "annotated_tag_required": True,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "c140_course": "incomplete",
        "component_separated_rights": True,
        "credential_access": False,
        "files": len(rows),
        "inherited_files": len(prior),
        "mode": "contract-only",
        "network_access": False,
        "new_files": len(rows) - len(prior),
        "package_receipt_sha256": sha256(receipt),
        "prior_commit": PRIOR_COMMIT,
        "prior_public_receipt_sha256": PRIOR_RECEIPT_SHA256,
        "prior_release_id": PRIOR_RELEASE_ID,
        "prior_tag": PRIOR_TAG,
        "prior_tag_object": PRIOR_TAG_OBJECT,
        "publication_side_effects": False,
        "replacements": 0,
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "tag": TAG,
        "version": PACKAGE_VERSION,
    }


def contract_summary(snap: engine.Snapshot) -> dict[str, object]:
    return {
        **local_contract_summary(),
        "mode": "contract-check",
        "primary_file": snap.files[0].name,
        "c140_original_companion": "C3 coherent partial checkpoint complete",
    }


def configure_engine() -> None:
    engine.TOKEN_FILE = TOKEN_FILE
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
    engine.HEADERS = {**engine.HEADERS, "User-Agent": "O006-C140-companion-c3/2026.08.29"}
    engine.snapshot = snapshot
    engine.prior_release_witness = prior_release_witness
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
