#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative STAT 415 Lesson 03 checkpoint.

The mature Lesson 01 publisher remains the transaction engine.  This adapter
admits only the exact 5-of-14 package and can create a new version only inside
the existing Zenodo concept 10.5281/zenodo.22077422.  It has no code path that
creates a new deposition/concept.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

import requests
import truststore

import publish_zenodo_through_lesson01 as engine


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
RELEASE = ROOT / "release"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON03_PACKAGE_RECEIPT.json"
DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-25_THROUGH_LESSON03.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-25_THROUGH_LESSON03.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-25_THROUGH_LESSON03.json"
LINEAGE = ROOT / "00_control" / "ZENODO_LINEAGE.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-25_THROUGH_LESSON03.json"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia (5 dari 14 Dokumen)"
VERSION = "2026.08.25.5of14"
PACKAGE_SCHEMA = "o006.stat415.through-lesson03-package.v1"
PUBLICATION_SCHEMA = "o006.stat415.zenodo-through-lesson03-publication.v1"
RELEASE_ROOT_SCHEMA = "o006.stat415.through-lesson03-release-root.v1"
FILES = (
    "00_stat415-id-through-lesson03-offline-reader.zip",
    "10_stat415-id-through-lesson03-source-backend.zip",
    "20_THROUGH_LESSON03_RELEASE_NOTES.md",
    "30_THROUGH_LESSON03_LICENSE.md",
    "40_THROUGH_LESSON03_QA_RECEIPT.json",
    "41_THROUGH_LESSON03_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON03_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON03.txt",
    "60_THROUGH_LESSON03_RELEASE_ROOT_RECEIPT.json",
)
ROOT_RECEIPT = FILES[-1]
COMPLETE_DOCUMENTS = ("index", "Lesson00", "Lesson01", "Lesson02", "Lesson03")
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"


def validate_release_root(inventory: list[dict[str, object]]) -> None:
    root_rows = [row for row in inventory if row.get("name") == ROOT_RECEIPT]
    if len(root_rows) != 1 or not isinstance(root_rows[0].get("payload"), bytes):
        raise RuntimeError("release root receipt snapshot is absent")
    value = json.loads(root_rows[0]["payload"].decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("release root receipt is not an object")
    covered = list(FILES[:-1])
    if (
        value.get("schema") != RELEASE_ROOT_SCHEMA
        or value.get("status") != "ready"
        or value.get("upload_order") != covered
        or value.get("file_count") != len(covered)
    ):
        raise RuntimeError("release root receipt has the wrong boundary or inventory")
    self_exclusion = value.get("self_exclusion")
    if not isinstance(self_exclusion, dict) or self_exclusion.get("filename") != ROOT_RECEIPT:
        raise RuntimeError("release root receipt does not declare its sole self-exclusion")
    expected = {str(row["name"]): row for row in inventory if row["name"] != ROOT_RECEIPT}
    rows = value.get("files")
    if not isinstance(rows, list):
        raise RuntimeError("release root receipt file inventory is absent")
    actual = {str(row.get("filename")): row for row in rows if isinstance(row, dict)}
    if set(actual) != set(covered) or len(rows) != len(covered):
        raise RuntimeError("release root receipt does not cover every other upload")
    for filename in covered:
        if (
            actual[filename].get("bytes") != expected[filename]["bytes"]
            or actual[filename].get("sha256") != expected[filename]["sha256"]
        ):
            raise RuntimeError(f"release root receipt identity differs: {filename}")
    if value.get("total_bytes") != sum(int(expected[name]["bytes"]) for name in covered):
        raise RuntimeError("release root receipt aggregate byte count differs")
    semantics = value.get("inventory_semantics")
    if not isinstance(semantics, dict):
        raise RuntimeError("release root receipt omits inventory semantics")
    manifest_semantics = semantics.get("release_manifest")
    checksum_semantics = semantics.get("sha256sums")
    root_semantics = semantics.get("root_receipt")
    if (
        not isinstance(manifest_semantics, dict)
        or manifest_semantics.get("covers") != list(FILES[:6])
        or manifest_semantics.get("excludes") != [FILES[6], FILES[7], ROOT_RECEIPT]
        or not isinstance(checksum_semantics, dict)
        or checksum_semantics.get("covers") != list(FILES[:7])
        or checksum_semantics.get("excludes") != [FILES[7], ROOT_RECEIPT]
        or not isinstance(root_semantics, dict)
        or root_semantics.get("covers") != covered
        or root_semantics.get("excludes") != [ROOT_RECEIPT]
    ):
        raise RuntimeError("release root receipt inventory semantics differ")


def local_inventory() -> tuple[list[dict[str, object]], dict[str, object]]:
    package = json.loads(PACKAGE_RECEIPT.read_text("utf-8"))
    if not isinstance(package, dict):
        raise RuntimeError("release package receipt is not an object")
    rows = package.get("files")
    coverage = package.get("coverage")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("upload_order") != list(FILES)
        or package.get("translation_provenance") != MODEL_PROVENANCE
        or not isinstance(rows, list)
        or not isinstance(coverage, dict)
    ):
        raise RuntimeError("release package receipt is not the admitted cumulative boundary")
    if (
        coverage.get("complete_count") != 5
        or coverage.get("corpus_document_count") != 14
        or coverage.get("complete_documents") != list(COMPLETE_DOCUMENTS)
        or coverage.get("next_document") != "Lesson04"
    ):
        raise RuntimeError("release package coverage is not exactly index plus Lessons 00–03")
    by_name = {str(row.get("filename")): row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(FILES) or len(rows) != len(FILES) or min(FILES, key=str.casefold) != FILES[0]:
        raise RuntimeError("release package file set is not exact and reader-first")
    release_root = RELEASE.resolve(strict=True)
    if RELEASE.is_symlink():
        raise RuntimeError("release directory may not be a symlink")
    inventory: list[dict[str, object]] = []
    snapshot_bytes = 0
    for filename in FILES:
        path = RELEASE / filename
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"release file missing: {filename}")
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(release_root)
        except ValueError as exc:
            raise RuntimeError(f"release file resolves outside release directory: {filename}") from exc
        size = resolved.stat().st_size
        snapshot_bytes += size
        if snapshot_bytes > 500_000_000:
            raise RuntimeError("release payload exceeds the 500 MB task cap")
        payload = resolved.read_bytes()
        if len(payload) != size:
            raise RuntimeError(f"release file changed while being snapshotted: {filename}")
        row = {
            "name": filename,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "md5": hashlib.md5(payload, usedforsecurity=False).hexdigest(),
            "payload": payload,
        }
        expected = by_name[filename]
        if row["bytes"] != expected.get("bytes") or row["sha256"] != expected.get("sha256"):
            raise RuntimeError(f"release file differs from package receipt: {filename}")
        inventory.append(row)
    validate_release_root(inventory)
    total_bytes = sum(int(row["bytes"]) for row in inventory)
    if package.get("file_count") != len(inventory) or package.get("total_bytes") != total_bytes:
        raise RuntimeError("release package aggregate counts differ")
    return inventory, coverage


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-25",
        "description": (
            "Checkpoint kumulatif yang substansial tetapi masih sebagian untuk rekonstruksi dan terjemahan "
            "Bahasa Indonesia (id-ID) rangkaian publik Penn State STAT 415, Introduction to Mathematical "
            "Statistics. Cakupan tepatnya adalah laman utama serta seluruh Pelajaran 00–03: 5 dari 14 "
            "dokumen lengkap, termasuk statistik urutan, estimasi titik, kecukupan, keluarga eksponensial, "
            "dan metode momen. Berkas pertama adalah pembaca HTML luring; paket source-backend yang ringkas, "
            "manifes, checksum, lisensi komponen, serta bukti QA deterministik dan visual turut disertakan. "
            "Pelajaran 04–12 belum diterjemahkan dan tetap menaut ke sumber resmi berbahasa Inggris. Konten "
            "Penn State beserta adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan lain; MathJax 3.1.2 tetap "
            "Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. Koleksi komponen ini tidak direlisensi "
            "secara seragam, sehingga metadata agregat memakai other-open dan LICENSE.md menjadi pernyataan "
            "hak yang mengikat. Byte sumber resmi tidak diubah. Provenans terjemahan: "
            f"{MODEL_PROVENANCE}. Seluruh kredit sumber dan kontributor manusia dipertahankan. Tidak ada "
            "dukungan atau pengesahan oleh Penn State yang tersirat."
        ),
        "creators": [{"name": "Penn State Department of Statistics"}],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia",
            "id-ID",
            "mathematical statistics",
            "statistika matematis",
            "order statistics",
            "statistik urutan",
            "point estimation",
            "sufficient statistics",
            "method of moments",
            "sampling distributions",
            "open educational resources",
            "offline HTML",
            "machine-readable curriculum",
            "AI translation",
            "partial edition",
        ],
        "language": "ind",
        "version": VERSION,
        "related_identifiers": [
            {
                "identifier": "https://online.stat.psu.edu/stat415/",
                "relation": "isDerivedFrom",
                "resource_type": "publication-other",
                "scheme": "url",
            },
            {
                "identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
                "relation": "isSupplementedBy",
                "resource_type": "software",
                "scheme": "url",
            },
        ],
    }


def configure_engine() -> None:
    values = {
        "TOKEN_FILE": TOKEN_FILE,
        "RELEASE": RELEASE,
        "PACKAGE_RECEIPT": PACKAGE_RECEIPT,
        "DEFAULT_RECEIPT": DEFAULT_RECEIPT,
        "READBACK_RECEIPT": READBACK_RECEIPT,
        "AUDIT_RECEIPT": AUDIT_RECEIPT,
        "LINEAGE": LINEAGE,
        "DRAFT_MARKER": DRAFT_MARKER,
        "CONCEPT_RECORD_ID": CONCEPT_RECORD_ID,
        "CONCEPT_DOI": CONCEPT_DOI,
        "TITLE": TITLE,
        "VERSION": VERSION,
        "PACKAGE_SCHEMA": PACKAGE_SCHEMA,
        "FILES": FILES,
        "ROOT_RECEIPT": ROOT_RECEIPT,
        "COMPLETE_DOCUMENTS": COMPLETE_DOCUMENTS,
        "MODEL_PROVENANCE": MODEL_PROVENANCE,
    }
    for name, value in values.items():
        setattr(engine, name, value)
    engine.validate_release_root = validate_release_root
    engine.local_inventory = local_inventory
    engine.metadata = metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local-preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify-published", action="store_true")
    mode.add_argument("--audit-lineage", action="store_true")
    parser.add_argument("--record-id")
    args = parser.parse_args()

    configure_engine()
    inventory, coverage = local_inventory()
    lineage = engine.load_lineage()
    base: dict[str, object] = {
        "schema": PUBLICATION_SCHEMA,
        "version": VERSION,
        "coverage": coverage,
        "local_files": len(inventory),
        "local_bytes": sum(int(row["bytes"]) for row in inventory),
        "local_inventory": [{key: row[key] for key in ("name", "bytes", "sha256")} for row in inventory],
        "translation_provenance": MODEL_PROVENANCE,
        "required_concept_record_id": CONCEPT_RECORD_ID,
        "required_concept_doi": CONCEPT_DOI,
    }
    if args.local_preflight:
        base.update({"mode": "local-preflight", "credential_access": False, "network_access": False})
        print(json.dumps(base, ensure_ascii=False, sort_keys=True))
        return

    truststore.inject_into_ssl()
    if args.verify_published:
        if not args.record_id or not args.record_id.isdigit():
            raise RuntimeError("--verify-published requires numeric --record-id")
        public = engine.anonymous_readback(args.record_id, inventory)
        receipt = {**base, "mode": "verify-published", "credential_access": False, "public": public}
        engine.atomic_json(READBACK_RECEIPT, receipt)
        print(json.dumps({"mode": "verify-published", "record_id": args.record_id, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    # The credential is read only here, at runtime.  It is used only in an
    # Authorization header and is never persisted, logged, copied, or printed.
    token = engine.read_token()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": "O006-STAT415-Zenodo-new-version/5.0"})
    public_session = requests.Session()
    public_session.headers.update({"User-Agent": "O006-STAT415-Zenodo-concept-check/5.0"})
    versions = engine.public_concept_versions(public_session)
    published_target = engine.target_public_record(versions)

    if args.audit_lineage:
        if published_target is None:
            raise RuntimeError("the target cumulative version is not published")
        public = engine.anonymous_readback(str(published_target["id"]), inventory)
        concept_drafts = engine.authenticated_concept_drafts(session)
        if concept_drafts:
            raise RuntimeError("an unpublished draft remains in the admitted Zenodo concept")
        audit = {
            **base,
            "mode": "audit-lineage",
            "credential_access": True,
            "submitted_matching_versions": 1,
            "unsubmitted_matching_drafts": 0,
            "public": public,
        }
        engine.atomic_json(AUDIT_RECEIPT, audit)
        marker = engine.load_draft_marker()
        if marker is not None:
            engine.remove_draft_marker(str(public["record_id"]))
        print(json.dumps({"mode": "audit-lineage", "record_id": public["record_id"], "submitted": 1, "drafts": 0, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    if published_target is not None:
        public = engine.anonymous_readback(str(published_target["id"]), inventory)
        newest = engine.newest_public_record(versions)
        target_is_newest = str(newest["id"]) == str(published_target["id"])
        mode_name = "already-published" if target_is_newest else "already-published-superseded"
        engine.write_success_receipts(
            base,
            public,
            mode_name,
            update_lineage=target_is_newest,
            newest_record_id=str(newest["id"]),
        )
        marker = engine.load_draft_marker()
        if marker is not None:
            engine.remove_draft_marker(str(public["record_id"]))
        print(json.dumps({"mode": mode_name, "record_id": public["record_id"], "doi": public["doi"], "concept_doi": public["concept_doi"], "newest_record_id": str(newest["id"]), "lineage_updated": target_is_newest, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    latest = engine.latest_public_record(versions, lineage)
    prior_version = str(latest.get("metadata", {}).get("version", ""))
    if prior_version != str(lineage.get("version")):
        raise RuntimeError("latest public Zenodo version differs from the durable local lineage")
    draft, reused = engine.create_or_reuse_owned_new_version(session, str(latest["id"]), prior_version)
    draft = engine.upload_files(session, draft, inventory)
    deposition_id = str(draft["id"])
    engine.check(
        session.put(engine.DEPOSITIONS + f"/{deposition_id}", json={"metadata": metadata()}, timeout=120),
        (200,),
        "update Zenodo new-version metadata",
    )
    draft = engine.refetch(session, deposition_id)
    engine.validate_metadata(draft.get("metadata"), metadata())
    if not engine.exact_draft_files(draft, inventory):
        raise RuntimeError("Zenodo new-version draft failed its final inventory check")
    published = engine.check(
        session.post(engine.DEPOSITIONS + f"/{deposition_id}/actions/publish", json={}, timeout=180),
        (202,),
        "publish Zenodo new version",
    ).json()
    if not isinstance(published, dict):
        raise RuntimeError("Zenodo publish response is not an object")
    record_id = str(published.get("record_id") or published.get("id") or "")
    if not record_id.isdigit() or record_id == str(latest["id"]):
        raise RuntimeError("Zenodo publish response omitted a distinct new record id")
    public = engine.anonymous_readback(record_id, inventory)
    engine.write_success_receipts(
        base,
        public,
        "publish",
        draft_id=deposition_id,
        draft_reused=reused,
        prior_record_id=str(latest["id"]),
    )
    engine.remove_draft_marker(deposition_id)
    print(json.dumps({"mode": "publish", "record_id": record_id, "doi": public["doi"], "concept_doi": public["concept_doi"], "files": len(FILES), "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
