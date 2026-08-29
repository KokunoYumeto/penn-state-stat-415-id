#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative C140 companion C4 release.

This fail-closed adapter reuses the hardened GitHub transaction engine.  Its
local contract preserves the exact anonymously verified 49-file C3
release and appends only the eight artifacts admitted by the C4 packager.
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

import package_c140_companion_c4_release as packager
import publish_verify_github_c140_companion_c3 as c3pub


engine = c3pub.engine
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RELATIVE = "build/C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / PACKAGE_RELATIVE
TOKEN_FILE = (
    Path.home() / "Documents" / "Obsidian notes" / "Github Tokens.md"
)
PRIOR_RECEIPT_RELATIVE = (
    "00_control/GITHUB_RELEASE_RECEIPT_2026-08-29_"
    "C140_COMPANION_C3.json"
)
VERIFICATION_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-29_C140_COMPANION_C4.json"
)
PUBLICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_PUBLICATION_2026-08-29_C140_COMPANION_C4.json"
)

PACKAGE_SCHEMA = "o006.c140.companion-c4-release-package.v1"
PACKAGE_VERSION = "2026.08.29.c140-companion-c4"
PACKAGE_RECEIPT_BYTES = 34_142
PACKAGE_RECEIPT_SHA256 = (
    "45c0fceb27af175689e5ee8ac92271d395a41cdf96c32621eacf8d60a8222f7f"
)
VERIFICATION_SCHEMA = "o006.c140.companion-c4.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c4.github-release-publication.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TAG = "v2026.08.29.c140-companion-c4"
PRIOR_TAG = "v2026.08.29.c140-companion-c3"
PRIOR_RELEASE_ID = 378_973_936
PRIOR_COMMIT = "1c8f97f02e9bccfdbe4df91dd77af969cd6e33d6"
PRIOR_TAG_OBJECT = "9a6fa0b27bd663e47e67d7f7b145f1da4f3ee6e3"
PRIOR_RECEIPT_BYTES = 55_062
PRIOR_RECEIPT_SHA256 = (
    "bce4ab1a9144d3a147bb813b51b6efd1711d2744e22a4bbdf4fe84cb96ad6e16"
)
PRIOR_RECEIPT_SCHEMA = (
    "o006.c140.companion-c3.github-release-readback.v1"
)
PRIOR_FILE_COUNT = 49
PRIOR_TOTAL_BYTES = 92_476_057

TITLE = "O006/C140 Statistika Matematis — Pendamping Orisinal C4 (Bahasa Indonesia)"
BODY = (
    "Rilis kumulatif ini mempertahankan secara byte-identik seluruh 49 aset "
    "checkpoint C3 yang telah dibaca balik secara anonim, lalu menambahkan "
    "tepat delapan aset C4. C4 menambahkan batch penguasaan mandiri lengkap "
    "MS00–MS06: tinjauan probabilitas/distribusi, statistik terurut, estimasi "
    "dan bias/MSE, kecukupan dan faktorisasi, metode momen dan likelihood, "
    "informasi Fisher/selang/bootstrap/delta, serta pengujian eksak, power, "
    "p-value, Wald, score, dan LR. Ketujuh set memuat 56 soal nontrivial "
    "berjawab lengkap. Keseluruhan C140 masih incomplete: CA02–CA04 dan dua "
    "capstone belum termasuk. Hak Penn State, donor Random, dan pendamping "
    "orisinal tetap dipisahkan per komponen; agregat tidak direlisensi secara "
    "seragam. Produksi dan QA bersifat tanpa browser. Provenans: "
    + MODEL_PROVENANCE
    + "."
)
TAG_MESSAGE = "O006/C140 original companion C4 coherent partial checkpoint (2026-08-29)"

INHERITED_NAMES = tuple(c3pub.EXPECTED_NAMES)
ADDITION_SPECS = (
    (
        packager.OFFLINE_NAME,
        923_472,
        "92dd5d30f79f47351b1cfaeb2a05ff9b53ca1136e3c48bb6bd67f5481a960291",
        "partial-c4-offline-html-reader",
        "c140-original-companion-c4",
        "application/zip",
    ),
    (
        packager.SOURCE_NAME,
        367_946,
        "fe8c034a51f9c7a7acc0a764af70ebc4ed0e8e790c591003815abf1a3f723503",
        "partial-c4-resumable-source-backend",
        "c140-original-companion-c4",
        "application/zip",
    ),
    (
        packager.NOTES_NAME,
        1_472,
        "a468a26a8f9c1c9bd4245f757f54ba9dbc07f1fc45036bc5cf5e731414dfde1a",
        "partial-c4-scope-status-provenance",
        "c140-original-companion-c4",
        "text/markdown",
    ),
    (
        packager.LICENSE_NAME,
        642,
        "f8913e62477ebb57d3370abb52469ac54292e2b2053db9a41fa3cb3cb02967f2",
        "partial-c4-component-rights",
        "c140-original-companion-c4",
        "text/markdown",
    ),
    (
        packager.QA_NAME,
        34_431,
        "eac5ffe8f11b41ee4d6f375538d378169653c0c930dc085d618072e935b1d8ba",
        "partial-c4-browser-free-static-qa-evidence",
        "c140-original-companion-c4",
        "application/zip",
    ),
    (
        packager.MANIFEST_NAME,
        13_786,
        "3cc278085606d676946add43ba20010e007029ce7050b07f09b2d0265afdd773",
        "c4-cumulative-union-manifest",
        "c140-original-companion-c4-union",
        "text/csv",
    ),
    (
        packager.CHECKSUM_NAME,
        6_012,
        "f1c002ac9afa6754f0ff21d217ca9bb7154121197062716afc9f79d10454af3c",
        "c4-cumulative-union-checksums",
        "c140-original-companion-c4-union",
        "text/plain",
    ),
    (
        packager.ROOT_NAME,
        27_175,
        "29c7117327743ae12982d69283917f61b53ace02c76d474e68c99af0f90d447e",
        "c4-cumulative-union-root-receipt",
        "c140-original-companion-c4-union",
        "application/json",
    ),
)
ADDITION_NAMES = tuple(item[0] for item in ADDITION_SPECS)
EXPECTED_NAMES = INHERITED_NAMES + ADDITION_NAMES
EXPECTED_ADDITION_ROLES = {item[0]: item[3] for item in ADDITION_SPECS}
EXPECTED_ADDITION_LINEAGES = {item[0]: item[4] for item in ADDITION_SPECS}
EXPECTED_FILE_COUNT = 57
EXPECTED_TOTAL_BYTES = 93_850_993

EXPECTED_COVERAGE = {
    "c140_course": "incomplete",
    "c140_original_companion": "C4 coherent partial checkpoint complete",
    "c4_batch": "complete",
    "penn_state_spine": "complete",
    "random_completeness_donor": "complete",
    "remaining": "CA02-CA04 and two capstones",
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
    "base_record_doi": "10.5281/zenodo.22161363",
    "base_record_id": "22161363",
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
    "c4_first_upload_order": PRIOR_FILE_COUNT + 1,
    "epub_upload_order": 2,
    "inherited_union_first": True,
    "pdf_upload_order": 1,
}
EXPECTED_PACKAGER = {
    "browser_processes_used": False,
    "credential_access": False,
    "git_operations": False,
    "network_access": False,
    "path": "scripts/package_c140_companion_c4_release.py",
    "publication_side_effects": False,
    "recursive_repository_discovery": False,
    "source_bytes": 41_233,
    "source_sha256": "0dee3ad4de34870023dc7c8c1c52a99da6ef44b82fb43ed61d187846bda489c9",
}
EXPECTED_BASE = {
    "anonymous_readback": True,
    "bytes": PRIOR_TOTAL_BYTES,
    "concept_doi": "10.5281/zenodo.22077422",
    "concept_record_id": "22077422",
    "file_count": PRIOR_FILE_COUNT,
    "package_receipt": {
        "bytes": 30_151,
        "sha256": "d78c911bdc2837a3fdddd3f71e6b7211fde46a8668d85a9c00f750cf82716637",
    },
    "public_readback": {
        "bytes": 19_302,
        "sha256": "c53bd0827a06a25dd81bee46d8c6630ce4147f256f0605f089f16aa712a69bbf",
    },
    "record_doi": "10.5281/zenodo.22161363",
    "record_id": "22161363",
    "version": "2026.08.29.c140-companion-c3",
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
    """Load the immutable C3 GitHub witness without network or credentials."""
    payload = engine.read_confined(PRIOR_RECEIPT_RELATIVE, "C3 GitHub public readback")
    if len(payload) != PRIOR_RECEIPT_BYTES or sha256(payload) != PRIOR_RECEIPT_SHA256:
        raise RuntimeError("C3 GitHub public-readback receipt identity differs")
    receipt = json_object(payload, "C3 GitHub public-readback receipt")
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
        or receipt.get("credential_access") is not True
        or receipt.get("control_plane_credential_access") is not True
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
        raise RuntimeError("C3 GitHub public-readback contract differs")
    inventory: list[dict[str, Any]] = []
    for index, (local_row, public_row) in enumerate(
        zip(local, public_files, strict=True)
    ):
        if not isinstance(local_row, dict) or not isinstance(public_row, dict):
            raise RuntimeError(f"malformed C3 GitHub inventory row {index}")
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
            raise RuntimeError(f"C3 GitHub inventory identity differs at row {index}")
        inventory.append(dict(local_row))
    if sum(int(row["bytes"]) for row in inventory) != PRIOR_TOTAL_BYTES:
        raise RuntimeError("C3 GitHub inventory byte total differs")
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
        raise RuntimeError("computed C4 package receipt identity differs")
    package = json_object(receipt_payload, "computed C4 package receipt")
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
        raise RuntimeError("computed C4 package contract differs")

    gates = package.get("gates")
    archives = gates.get("archives") if isinstance(gates, dict) else None
    if (
        not isinstance(gates, dict)
        or gates.get("privacy") != {"forbidden_markers_found": 0}
        or gates.get("publication_size")
        != {"bytes": EXPECTED_TOTAL_BYTES, "cap_bytes": 500_000_000, "status": "pass"}
        or gates.get("c4_boundary")
        != {
            "backend_entities": 1_113,
            "backend_relations": 1_424,
            "documents": 34,
            "html_files": 64,
            "problems": 114,
            "simulations": 6,
            "status": "pass",
        }
        or not isinstance(archives, dict)
        or set(archives) != {packager.OFFLINE_NAME, packager.SOURCE_NAME, packager.QA_NAME}
    ):
        raise RuntimeError("computed C4 package gates differ")

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
            raise RuntimeError(f"inherited C3 GitHub asset changed at row {index}")

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
            raise RuntimeError(f"C4 addition contract differs: {name}")
        archive = archives.get(name)
        if name in {packager.OFFLINE_NAME, packager.SOURCE_NAME, packager.QA_NAME} and (
            not isinstance(archive, dict)
            or archive.get("bytes") != size
            or archive.get("sha256") != digest
            or archive.get("privacy") != {"forbidden_markers_found": 0}
        ):
            raise RuntimeError(f"C4 archive gate differs: {name}")
    return outputs, receipt_payload, package, rows, prior_inventory


def snapshot() -> engine.Snapshot:
    outputs, receipt_payload, package, rows, prior_inventory = computed_contract()
    if not PACKAGE_RECEIPT.is_file() or PACKAGE_RECEIPT.read_bytes() != receipt_payload:
        raise RuntimeError("written C4 package receipt differs; run the C4 packager --write")
    artifacts: list[engine.Artifact] = []
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"malformed C4 package row {index}")
        name = str(row.get("filename", ""))
        relative = engine.canonical_relative(row.get("source_path"), f"C4 row {index} path")
        payload = engine.read_confined(relative, f"C4 release asset {name}")
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
            raise RuntimeError(f"C4 asset is unsafe or differs: {name}")
        if index < PRIOR_FILE_COUNT:
            prior = prior_inventory[index]
            if (
                name != prior["name"]
                or len(payload) != prior["bytes"]
                or sha256(payload) != prior["sha256"]
                or row.get("role") != prior["role"]
                or row.get("lineage") != prior["lineage"]
            ):
                raise RuntimeError(f"inherited C3 asset changed: {name}")
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
            raise RuntimeError("C4 release exceeds the 500 MB task cap")
        seen_names.add(name)
        seen_paths.add(relative)
    if total != EXPECTED_TOTAL_BYTES:
        raise RuntimeError("C4 cumulative package byte total differs")
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
    """Revalidate the exact prior 49-file release and annotated tag."""
    del snap
    _receipt, inventory = prior_receipt_contract()
    control = control_session or engine.public_session()
    ref_url = f"{engine.REPOSITORY_API}/git/ref/tags/{quote(PRIOR_TAG, safe='')}"
    ref = engine.api_json(control, "GET", ref_url, action="read prior C3 tag", timeout=120)
    obj = ref.get("object")
    if (
        ref.get("ref") != f"refs/tags/{PRIOR_TAG}"
        or not isinstance(obj, dict)
        or obj.get("type") != "tag"
        or obj.get("sha") != PRIOR_TAG_OBJECT
    ):
        raise RuntimeError("prior C3 annotated-tag witness differs")
    tag = engine.api_json(
        control,
        "GET",
        f"{engine.REPOSITORY_API}/git/tags/{PRIOR_TAG_OBJECT}",
        action="peel prior C3 annotated tag",
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
        raise RuntimeError("prior C3 tag no longer peels to its fixed commit")
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
        raise RuntimeError("prior C3 release witness differs")
    witness_files = []
    for item in inventory:
        remote = by_name[item["name"]]
        if remote.get("size") != item["bytes"] or remote.get("state") != "uploaded":
            raise RuntimeError(f"prior C3 asset metadata differs: {item['name']}")
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
        "prior_c3_files_preserved": len(snap.inherited_files),
        "companion_c4_additions": len(snap.additions),
        "companion_c4_replacements": 0,
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
        "c140_original_companion": "C4 coherent partial checkpoint complete",
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
    engine.HEADERS = {**engine.HEADERS, "User-Agent": "O006-C140-companion-c4/2026.08.29"}
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
