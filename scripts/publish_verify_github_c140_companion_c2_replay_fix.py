#!/usr/bin/env python3
"""Publish/verify the narrowly versioned C2 cross-platform replay repair.

This is a thin adapter over the hardened C140 GitHub release engine.  The
41-file target is the exact corrected C2 union; the prior C2 release is only a
lineage witness. ``--contract-only`` is local and side-effect free.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote

import package_c140_companion_c2_replay_fix_release as packager
import publish_verify_github_c140_companion_c2 as c2pub


engine = c2pub.engine
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RELATIVE = "build/C140_COMPANION_C2_REPLAY_FIX_RELEASE_PACKAGE_RECEIPT.json"
PACKAGE_RECEIPT = ROOT / PACKAGE_RELATIVE
VERIFICATION_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
)
PUBLICATION_RECEIPT = (
    ROOT / "00_control" / "GITHUB_RELEASE_PUBLICATION_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
)

PACKAGE_SCHEMA = packager.SCHEMA
PACKAGE_VERSION = packager.VERSION
VERIFICATION_SCHEMA = "o006.c140.companion-c2-replay-fix.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.companion-c2-replay-fix.github-release-publication.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TAG = "v2026.08.29.c140-companion-c2-replay-fix"
PRIOR_TAG = "v2026.08.29.c140-companion-c2"
PRIOR_RELEASE_ID = 378_822_880
PRIOR_COMMIT = "e01231d2f95722269a796629cd33ecb365cb037b"
# Revalidated by the hardened publication transaction.  The local contract
# remains network-free; the prior public receipt supplies this immutable hint.
PRIOR_TAG_OBJECT = "720573dc6d889372333ce76697d7512180aa60c1"

TITLE = "O006/C140 Statistika Matematis — C2 deterministic replay repair"
BODY = (
    packager.REPAIR_STATEMENT
    + " This corrective release republishes the exact current 41-file union. "
    "It adds no lesson, proof, exercise, formula, simulation result, or scope; "
    "C140 remains incomplete beyond the coherent C2 checkpoint. Component "
    "rights and all source credits remain unchanged. Production provenance: "
    + MODEL_PROVENANCE
    + "."
)
TAG_MESSAGE = "O006/C140 C2 deterministic cross-platform receipt repair (2026-08-29)"

EXPECTED_NAMES = tuple(c2pub.EXPECTED_NAMES)
BASE_SPECS = packager.base_specs()
EXPECTED_COVERAGE = {
    "c140_course": "incomplete",
    "c140_original_companion": "C2 coherent partial checkpoint complete",
    "penn_state_spine": "complete",
    "random_completeness_donor": "complete",
}


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def computed_contract() -> tuple[dict[str, bytes], bytes, dict[str, Any], list[dict[str, Any]]]:
    outputs, receipt = packager.compute()
    package = json.loads(receipt)
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    repair = package.get("repair")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != PACKAGE_VERSION
        or package.get("status") != "ready"
        or package.get("coverage") != EXPECTED_COVERAGE
        or not isinstance(rows, list)
        or tuple(row.get("filename") for row in rows if isinstance(row, dict)) != EXPECTED_NAMES
        or publication.get("file_count") != 41
        or publication.get("bytes") != 91_249_199
        or not isinstance(repair, dict)
        or repair.get("changed_file_count") != 7
        or repair.get("pedagogical_content_unchanged") is not True
        or repair.get("substantive_sim005_outputs_unchanged") is not True
    ):
        raise RuntimeError("computed C2 replay-fix package contract differs")
    return outputs, receipt, package, rows


def snapshot() -> engine.Snapshot:
    outputs, receipt, package, rows = computed_contract()
    if not PACKAGE_RECEIPT.is_file() or PACKAGE_RECEIPT.read_bytes() != receipt:
        raise RuntimeError("written replay-fix receipt differs; run replay-fix packager --write")
    changed = set(package["repair"]["changed_filenames"])
    artifacts: list[engine.Artifact] = []
    for index, row in enumerate(rows):
        name = str(row.get("filename", ""))
        relative = engine.canonical_relative(row.get("source_path"), f"replay-fix row {index} path")
        payload = engine.read_confined(relative, f"replay-fix asset {name}")
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_NAMES[index]
            or relative != f"release/{name}"
            or engine.SAFE_NAME_RE.fullmatch(name) is None
            or engine.SENSITIVE_NAME_RE.search(name) is not None
            or row.get("primary_reader") is not (index == 0)
            or outputs.get(name) != payload
            or len(payload) != row.get("bytes")
            or sha256(payload) != row.get("sha256")
        ):
            raise RuntimeError(f"replay-fix asset contract differs: {name}")
        artifacts.append(engine.Artifact(
            name=name,
            path=relative,
            bytes=len(payload),
            sha256=sha256(payload),
            payload=payload,
            role=str(row.get("role")),
            lineage=str(row.get("lineage")),
            media_type=str(row.get("media_type")),
        ))
    inherited = tuple(item for item in artifacts if item.name not in changed)
    replacements = tuple(item for item in artifacts if item.name in changed)
    if len(inherited) != 34 or len(replacements) != 7:
        raise RuntimeError("replay-fix changed/unchanged partition differs")
    return engine.Snapshot(
        package=package,
        package_receipt_bytes=len(receipt),
        package_receipt_sha256=sha256(receipt),
        files=tuple(artifacts),
        inherited_files=inherited,
        additions=replacements,
    )


def prior_release_witness(
    snap: engine.Snapshot,
    control_session: Any | None = None,
) -> dict[str, object]:
    """Verify the complete prior 41-file release, not just unchanged targets."""
    control = control_session or engine.public_session()
    ref_url = f"{engine.REPOSITORY_API}/git/ref/tags/{quote(PRIOR_TAG, safe='')}"
    ref = engine.api_json(control, "GET", ref_url, action="read prior C2 tag ref", timeout=120)
    obj = ref.get("object")
    if (
        ref.get("ref") != f"refs/tags/{PRIOR_TAG}"
        or not isinstance(obj, dict)
        or obj.get("type") != "tag"
        or obj.get("sha") != PRIOR_TAG_OBJECT
    ):
        raise RuntimeError("prior C2 annotated-tag witness differs")
    tag = engine.api_json(
        control, "GET", f"{engine.REPOSITORY_API}/git/tags/{PRIOR_TAG_OBJECT}",
        action="peel prior C2 annotated tag", timeout=120,
    )
    target = tag.get("object")
    if (
        tag.get("sha") != PRIOR_TAG_OBJECT
        or tag.get("tag") != PRIOR_TAG
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != PRIOR_COMMIT
    ):
        raise RuntimeError("prior C2 annotated tag no longer peels to its fixed commit")
    release = engine.release_by_tag(control, PRIOR_TAG, allow_missing=False)
    assert release is not None
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    by_name = {str(row.get("name")): row for row in assets}
    expected = {name: (size, digest) for name, size, digest in BASE_SPECS}
    if (
        release.get("id") != PRIOR_RELEASE_ID
        or release.get("draft") is not False
        or release.get("prerelease") is not False
        or len(assets) != 41
        or set(by_name) != set(expected)
    ):
        raise RuntimeError("prior C2 release witness differs")
    inventory = []
    for name, size, digest in BASE_SPECS:
        row = by_name[name]
        if row.get("size") != size or row.get("state") != "uploaded":
            raise RuntimeError(f"prior C2 asset metadata differs: {name}")
        inventory.append({"name": name, "bytes": size, "sha256": digest})
    witness = {
        "release_id": PRIOR_RELEASE_ID,
        "tag": PRIOR_TAG,
        "url": f"{engine.REPOSITORY_URL}/releases/tag/{PRIOR_TAG}",
        "annotated_tag": {
            "ref_url": ref_url,
            "tag_object": PRIOR_TAG_OBJECT,
            "peeled_commit": PRIOR_COMMIT,
        },
        "files": inventory,
        "file_count": 41,
        "total_bytes": sum(size for _name, size, _digest in BASE_SPECS),
    }
    return {**witness, "witness_sha256": sha256(engine.canonical_json(witness))}


def receipt_base(snap: engine.Snapshot, commit: str) -> dict[str, object]:
    return {
        "version": PACKAGE_VERSION,
        "repository": engine.REPOSITORY_URL,
        "tag": TAG,
        "commit": commit,
        "release_scope": EXPECTED_COVERAGE,
        "repair_statement": packager.REPAIR_STATEMENT,
        "component_separated_rights": True,
        "aggregate_uniform_relicense": False,
        "local_inventory": [
            {"name": item.name, "bytes": item.bytes, "sha256": item.sha256,
             "role": item.role, "lineage": item.lineage}
            for item in snap.files
        ],
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "prior_c2_files": 41,
        "unchanged_files": len(snap.inherited_files),
        "replacement_files": len(snap.additions),
        "package_receipt": {"path": PACKAGE_RELATIVE, "bytes": snap.package_receipt_bytes,
                            "sha256": snap.package_receipt_sha256},
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
    _outputs, receipt, package, rows = computed_contract()
    return {
        "annotated_tag_required": True,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "credential_access": False,
        "files": len(rows),
        "mode": "contract-only",
        "network_access": False,
        "package_receipt_sha256": sha256(receipt),
        "prior_release_id": PRIOR_RELEASE_ID,
        "prior_tag_object_validation": "deferred-to-publication",
        "replacement_files": package["repair"]["changed_file_count"],
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "tag": TAG,
        "version": PACKAGE_VERSION,
    }


def contract_summary(snap: engine.Snapshot) -> dict[str, object]:
    return {**local_contract_summary(), "mode": "contract-check", "primary_file": snap.files[0].name}


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
    engine.HEADERS = {**engine.HEADERS, "User-Agent": "O006-C140-c2-replay-fix/2026.08.29"}
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
