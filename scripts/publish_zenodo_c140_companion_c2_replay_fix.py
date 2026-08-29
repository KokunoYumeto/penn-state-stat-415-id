#!/usr/bin/env python3
"""Publish the C2 cross-platform receipt repair in the existing Zenodo lineage.

The hardened publisher is reused, but this adapter replaces exactly the seven
files whose bytes differ from public record 22151570.  The other 34 files and
all public base bytes remain untouched. ``--contract-only`` is local,
credential-free, network-free, browser-free, and side-effect free.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote

import package_c140_companion_c2_replay_fix_release as packager
import publish_zenodo_c140_companion_c2 as c2pub


engine = c2pub.engine
ROOT = Path(__file__).resolve().parents[1]
BASE_RECORD_ID = packager.BASE_RECORD_ID
BASE_VERSION = packager.BASE_VERSION
CONCEPT_RECORD_ID = packager.CONCEPT_RECORD_ID
CONCEPT_DOI = packager.CONCEPT_DOI
VERSION = packager.VERSION
TITLE = "O006/C140 Statistika Matematis — C2 deterministic replay repair"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C2_REPLAY_FIX_RELEASE_PACKAGE_RECEIPT.json"
PUBLICATION_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
BASE_READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_BASE_READBACK_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"
LINEAGE_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_2026-08-29_C140_COMPANION_C2_REPLAY_FIX.json"

PACKAGE_SCHEMA = packager.SCHEMA
PUBLICATION_SCHEMA = "o006.c140.zenodo-c140-companion-c2-replay-fix-publication.v1"
MARKER_SCHEMA = "o006.c140.zenodo-c140-companion-c2-replay-fix-draft-marker.v1"
LINEAGE_SCHEMA = "o006.c140.zenodo-c140-companion-c2-replay-fix-lineage.v1"
BASE_READBACK_SCHEMA = "o006.c140.zenodo-base-readback-c140-companion-c2-replay-fix.v1"
USER_AGENT = "O006-C140-companion-c2-replay-fix/2026.08.29"
MAX_RELEASE_BYTES = 500_000_000

BASE_SPECS = packager.base_specs()
EXPECTED_ORDER = tuple(name for name, _size, _digest in BASE_SPECS)
VERIFIED_BASE_MD5: dict[str, str] = {}


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
        or package.get("version") != VERSION
        or package.get("status") != "ready"
        or not isinstance(rows, list)
        or tuple(row.get("filename") for row in rows if isinstance(row, dict)) != EXPECTED_ORDER
        or publication.get("file_count") != 41
        or publication.get("bytes") != 91_249_199
        or not isinstance(repair, dict)
        or repair.get("changed_file_count") != 7
        or repair.get("statement") != packager.REPAIR_STATEMENT
    ):
        raise RuntimeError("computed C2 replay-fix Zenodo package differs")
    return outputs, receipt, package, rows


def changed_names() -> tuple[str, ...]:
    _outputs, _receipt, package, _rows = computed_contract()
    return tuple(str(name) for name in package["repair"]["changed_filenames"])


def snapshot() -> engine.ReleaseSnapshot:
    outputs, receipt, package, rows = computed_contract()
    if not PACKAGE_RECEIPT.is_file() or PACKAGE_RECEIPT.read_bytes() != receipt:
        raise RuntimeError("written replay-fix receipt differs; run replay-fix packager --write")
    changed = set(package["repair"]["changed_filenames"])
    artifacts: list[engine.Artifact] = []
    for index, row in enumerate(rows):
        name = str(row.get("filename", ""))
        relative = engine.canonical_relative(row.get("source_path"), f"replay-fix row {index} path")
        size, digest = engine.checked_identity(row, f"replay-fix row {index}")
        payload = engine.read_confined(relative, f"replay-fix asset {name}")
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_ORDER[index]
            or relative != f"release/{name}"
            or not engine._SAFE_NAME.fullmatch(name)
            or engine._SENSITIVE_NAME.search(name)
            or row.get("primary_reader") is not (index == 0)
            or outputs.get(name) != payload
            or (len(payload), sha256(payload)) != (size, digest)
        ):
            raise RuntimeError(f"replay-fix asset contract differs: {name}")
        artifacts.append(engine.Artifact(name, relative, size, digest, payload))
    inherited = tuple(item for item in artifacts if item.name not in changed)
    replacements = tuple(item for item in artifacts if item.name in changed)
    if len(inherited) != 34 or len(replacements) != 7:
        raise RuntimeError("replay-fix replacement partition differs")
    return engine.ReleaseSnapshot(
        package=package,
        receipt_bytes=len(receipt),
        receipt_sha256=sha256(receipt),
        files=tuple(artifacts),
        inherited=inherited,
        additions=replacements,
    )


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-29",
        "description": (
            packager.REPAIR_STATEMENT
            + " Versi korektif ini menerbitkan kembali union C2 yang sama, "
            "berjumlah 41 berkas. Tidak ada pelajaran, pembuktian, soal, rumus, "
            "hasil simulasi, atau cakupan baru. C140 tetap belum lengkap setelah "
            "checkpoint C2 yang koheren. Hak dipisahkan per komponen: Penn State "
            "tetap CC BY-NC 4.0 kecuali dinyatakan lain; halaman Random tetap "
            "mempertahankan saksi CC BY 2.0/tautan CC BY 1.0; pendamping orisinal "
            "tetap CC BY-SA 4.0; MathJax tetap Apache-2.0. Provenans produksi: "
            + MODEL_PROVENANCE
            + ". Seluruh kredit sumber dipertahankan."
        ),
        "creators": [
            {"name": "Penn State Department of Statistics"},
            {"name": "Siegrist, Kyle"},
            {"name": "OpenAI Codex"},
        ],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia", "id-ID", "mathematical statistics",
            "statistika matematis", "deterministic build", "cross-platform replay",
            "receipt repair", "matrix Gaussian linear model", "SIM005",
            "Penn State STAT 415", "Random", "open educational resources",
            "offline HTML", "PDF", "EPUB", "machine-readable curriculum",
            "AI translation", "component-separated licensing",
        ],
        "language": "ind",
        "version": VERSION,
        "related_identifiers": [
            {"identifier": "https://online.stat.psu.edu/stat415/", "relation": "isDerivedFrom", "resource_type": "publication-other", "scheme": "url"},
            {"identifier": "https://www.randomservices.org/random/point/Sufficient.html", "relation": "isDerivedFrom", "resource_type": "publication-other", "scheme": "url"},
            {"identifier": "10.5281/zenodo.22076539", "relation": "isSupplementedBy", "resource_type": "publication-book", "scheme": "doi"},
            {"identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id", "relation": "isSupplementedBy", "resource_type": "software", "scheme": "url"},
        ],
    }


def verify_base_record(session: Any, snap: engine.ReleaseSnapshot) -> dict[str, object]:
    """Anonymously hash every base byte and retain its server-side MD5 for draft repair."""
    global VERIFIED_BASE_MD5
    record = engine.public_record(session, BASE_RECORD_ID)
    files = [row for row in record.get("files") or [] if isinstance(row, dict)]
    by_name = {str(row.get("key")): row for row in files}
    expected = {name: (size, digest) for name, size, digest in BASE_SPECS}
    if (
        record.get("metadata", {}).get("version") != BASE_VERSION
        or str(record.get("doi")) != f"10.5281/zenodo.{BASE_RECORD_ID}"
        or len(files) != 41
        or set(by_name) != set(expected)
    ):
        raise RuntimeError("public C2 base record differs")
    verified = []
    md5_map: dict[str, str] = {}
    for name, size, digest in BASE_SPECS:
        row = by_name[name]
        links = row.get("links") if isinstance(row.get("links"), dict) else {}
        url = engine.zenodo_url(
            links.get("content") or links.get("self"), f"public C2 base file {name}",
            ("/api/records/", "/api/files/", "/records/"),
        )
        response = engine.check(session.get(url, stream=True, timeout=900), (200,), f"download C2 base {name}")
        h256 = hashlib.sha256()
        hmd5 = hashlib.md5(usedforsecurity=False)
        count = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                h256.update(chunk)
                hmd5.update(chunk)
                count += len(chunk)
        response.close()
        if (count, h256.hexdigest()) != (size, digest):
            raise RuntimeError(f"public C2 base byte readback differs: {name}")
        checksum = str(row.get("checksum", ""))
        checksum = checksum[4:] if checksum.startswith("md5:") else checksum
        if checksum and checksum != hmd5.hexdigest():
            raise RuntimeError(f"public C2 base MD5 metadata differs: {name}")
        md5_map[name] = hmd5.hexdigest()
        verified.append({"name": name, "bytes": size, "sha256": digest})
    VERIFIED_BASE_MD5 = md5_map
    result = {
        "record_id": BASE_RECORD_ID,
        "doi": f"10.5281/zenodo.{BASE_RECORD_ID}",
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "version": BASE_VERSION,
        "files": verified,
        "file_count": 41,
        "total_bytes": sum(size for _name, size, _digest in BASE_SPECS),
        "anonymous_readback": True,
        "environment_proxy_trust": False,
    }
    engine.atomic_json(BASE_READBACK_RECEIPT, {
        "schema": BASE_READBACK_SCHEMA,
        "target_version": VERSION,
        "package_receipt_sha256": snap.receipt_sha256,
        "credential_access": False,
        "public_base": result,
    })
    return result


def _draft_state(draft: dict[str, Any], snap: engine.ReleaseSnapshot) -> tuple[str, ...]:
    if len(VERIFIED_BASE_MD5) != 41:
        raise RuntimeError("public C2 base MD5 witness is absent")
    names, by_name = engine.draft_file_map(draft)
    expected = {item.name: item for item in snap.files}
    if set(names) - set(expected):
        raise RuntimeError("owned replay-fix draft contains an unexpected file")
    for item in snap.inherited:
        row = by_name.get(item.name)
        if row is None:
            raise RuntimeError(f"owned replay-fix draft lost unchanged file: {item.name}")
        engine.assert_draft_file_identity(row, item)
    ready: list[str] = []
    base_map = {name: size for name, size, _digest in BASE_SPECS}
    for item in snap.additions:
        row = by_name.get(item.name)
        if row is None:
            continue
        checksum = str(row.get("checksum", ""))
        checksum = checksum[4:] if checksum.startswith("md5:") else checksum
        if int(row.get("filesize", -1)) == item.bytes and checksum == item.md5:
            ready.append(item.name)
        elif int(row.get("filesize", -1)) != base_map[item.name] or checksum != VERIFIED_BASE_MD5[item.name]:
            raise RuntimeError(f"owned replay-fix draft has ambiguous old bytes: {item.name}")
    expected_prefix = tuple(item.name for item in snap.additions[: len(ready)])
    if tuple(ready) != expected_prefix:
        raise RuntimeError("replay-fix replacements are not an exact canonical prefix")
    return tuple(ready)


def upload_replacements(session: Any, draft: dict[str, Any], snap: engine.ReleaseSnapshot) -> dict[str, Any]:
    draft_id = str(draft.get("id", ""))
    marker = engine.marker_value(snap)
    if marker is None or marker.get("status") != "owned" or str(marker.get("draft_id")) != draft_id:
        raise RuntimeError("refusing to repair an unowned Zenodo draft")
    engine.validate_owned_draft(draft, draft_id)
    ready = _draft_state(draft, snap)
    links = draft.get("links") if isinstance(draft.get("links"), dict) else {}
    bucket = engine.zenodo_url(links.get("bucket"), "replay-fix upload bucket", ("/api/files/",)).rstrip("/")
    for item in snap.additions[len(ready):]:
        _names, by_name = engine.draft_file_map(draft)
        old = by_name.get(item.name)
        if old is not None:
            old_links = old.get("links") if isinstance(old.get("links"), dict) else {}
            delete_url = engine.zenodo_url(
                old_links.get("self"), f"replay-fix draft file {item.name}",
                ("/api/deposit/depositions/",),
            )
            engine.check(session.delete(delete_url, timeout=180, allow_redirects=False), (200, 204), f"remove stale draft clone {item.name}")
            draft = engine.refetch(session, draft_id)
            if item.name in engine.draft_file_map(draft)[1]:
                raise RuntimeError(f"stale draft clone persisted: {item.name}")
        upload_url = engine.zenodo_url(
            f"{bucket}/{quote(item.name, safe='')}", f"replay-fix upload {item.name}", ("/api/files/",),
        )
        engine.check(session.put(upload_url, data=item.payload, timeout=900, allow_redirects=False), (200, 201), f"upload replay-fix {item.name}")
        draft = engine.refetch(session, draft_id)
        engine.validate_owned_draft(draft, draft_id)
        ready = _draft_state(draft, snap)
    if ready != tuple(item.name for item in snap.additions):
        raise RuntimeError("Zenodo replay-fix draft did not acquire all replacements")
    return draft


def exact_complete_draft(draft: dict[str, Any], snap: engine.ReleaseSnapshot) -> bool:
    try:
        ready = _draft_state(draft, snap)
    except RuntimeError:
        return False
    return ready == tuple(item.name for item in snap.additions) and len(engine.draft_file_map(draft)[0]) == 41


def base_receipt(snap: engine.ReleaseSnapshot) -> dict[str, object]:
    return {
        "schema": PUBLICATION_SCHEMA,
        "version": VERSION,
        "required_base_record_id": BASE_RECORD_ID,
        "required_base_version": BASE_VERSION,
        "required_concept_record_id": CONCEPT_RECORD_ID,
        "required_concept_doi": CONCEPT_DOI,
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "unchanged_files": len(snap.inherited),
        "replacement_files": len(snap.additions),
        "public_base_untouched": True,
        "repair_statement": packager.REPAIR_STATEMENT,
        "local_inventory": [{"name": i.name, "bytes": i.bytes, "sha256": i.sha256} for i in snap.files],
        "package_receipt": {"path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(), "bytes": snap.receipt_bytes, "sha256": snap.receipt_sha256},
        "translation_provenance": MODEL_PROVENANCE,
        "component_license_metadata": "other-open",
    }


def preflight_summary(snap: engine.ReleaseSnapshot) -> dict[str, object]:
    return {
        "mode": "local-preflight", "schema": PACKAGE_SCHEMA, "publication_version": VERSION,
        "files": len(snap.files), "bytes": snap.total_bytes, "unchanged_files": len(snap.inherited),
        "replacement_files": len(snap.additions), "primary_file": snap.files[0].name,
        "package_receipt": {"path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(), "bytes": snap.receipt_bytes, "sha256": snap.receipt_sha256},
        "credential_access": False, "network_access": False, "browser_processes": False,
    }


def write_public_receipts(base: dict[str, object], public: dict[str, object], mode: str, **extra: object) -> None:
    engine.atomic_json(READBACK_RECEIPT, {**base, "mode": "verify-published", "credential_access": False, "environment_proxy_trust": False, "public": public})
    engine.atomic_json(PUBLICATION_RECEIPT, {**base, "mode": mode, "credential_access": mode != "verify-published", "public": public, **extra})
    engine.atomic_json(LINEAGE_RECEIPT, {"schema": LINEAGE_SCHEMA, "record_id": public["record_id"], "doi": public["doi"], "concept_record_id": CONCEPT_RECORD_ID, "concept_doi": CONCEPT_DOI, "url": public["url"], "version": VERSION})


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt, package, rows = computed_contract()
    return {
        "base_record_id": BASE_RECORD_ID,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "concept_record_id": CONCEPT_RECORD_ID,
        "credential_access": False,
        "files": len(rows),
        "mode": "contract-only",
        "network_access": False,
        "package_receipt_sha256": sha256(receipt),
        "replacement_files_to_upload": package["repair"]["changed_file_count"],
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "unchanged_files": package["repair"]["unchanged_file_count"],
        "version": VERSION,
    }


def configure_engine() -> None:
    engine.BASE_RECORD_ID = BASE_RECORD_ID
    engine.BASE_VERSION = BASE_VERSION
    engine.CONCEPT_RECORD_ID = CONCEPT_RECORD_ID
    engine.CONCEPT_DOI = CONCEPT_DOI
    engine.VERSION = VERSION
    engine.NEW_VERSION_URL = f"{engine.DEPOSITIONS}/{BASE_RECORD_ID}/actions/newversion"
    engine.TITLE = TITLE
    engine.MODEL_PROVENANCE = MODEL_PROVENANCE
    engine.PACKAGE_RECEIPT = PACKAGE_RECEIPT
    engine.PUBLICATION_RECEIPT = PUBLICATION_RECEIPT
    engine.READBACK_RECEIPT = READBACK_RECEIPT
    engine.BASE_READBACK_RECEIPT = BASE_READBACK_RECEIPT
    engine.AUDIT_RECEIPT = AUDIT_RECEIPT
    engine.DRAFT_MARKER = DRAFT_MARKER
    engine.LINEAGE_RECEIPT = LINEAGE_RECEIPT
    engine.PACKAGE_SCHEMA = PACKAGE_SCHEMA
    engine.PUBLICATION_SCHEMA = PUBLICATION_SCHEMA
    engine.MARKER_SCHEMA = MARKER_SCHEMA
    engine.USER_AGENT = USER_AGENT
    engine.MAX_RELEASE_BYTES = MAX_RELEASE_BYTES
    engine.BASE_SPECS = BASE_SPECS
    engine.ADDED_NAMES = changed_names()
    engine.EXPECTED_ORDER = EXPECTED_ORDER
    engine.snapshot = snapshot
    engine.metadata = metadata
    engine.verify_base_record = verify_base_record
    engine.validate_inherited_and_partial_additions = _draft_state
    engine.upload_missing_additions = upload_replacements
    engine.exact_complete_draft = exact_complete_draft
    engine.base_receipt = base_receipt
    engine.preflight_summary = preflight_summary
    engine.write_public_receipts = write_public_receipts


def main() -> None:
    if sys.argv[1:] == ["--contract-only"]:
        print(json.dumps(local_contract_summary(), sort_keys=True))
        return
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
