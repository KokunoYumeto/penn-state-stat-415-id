#!/usr/bin/env python3
"""Publish the complete STAT 415 PDF/EPUB union in its existing Zenodo line.

The sole creation endpoint in this adapter is ``POST`` new-version on public
record 22105616.  There is deliberately no endpoint that can create a new
deposition or concept.  Local preflight is credential-free and network-free;
publication concludes with anonymous byte/hash readback and an authenticated
zero-draft audit of concept 22077422.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import time
from typing import Any
from urllib.parse import quote, urlparse

import requests
import truststore

import consolidated_release_contract as contract


API = "https://zenodo.org/api"
DEPOSITIONS = f"{API}/deposit/depositions"
RECORDS = f"{API}/records"
BASE_RECORD_ID = "22105616"
BASE_VERSION = "2026.08.26.14of14"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
VERSION = contract.PUBLICATION_VERSION
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia Lengkap (PDF dan EPUB)"
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
PUBLICATION_RECEIPT = (
    contract.ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-28_CONSOLIDATED_READERS.json"
)
READBACK_RECEIPT = (
    contract.ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-28_CONSOLIDATED_READERS.json"
)
AUDIT_RECEIPT = (
    contract.ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-28_CONSOLIDATED_READERS.json"
)
DRAFT_MARKER = (
    contract.ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-28_CONSOLIDATED_READERS.json"
)
LINEAGE = contract.ROOT / "00_control" / "ZENODO_LINEAGE.json"
PUBLICATION_SCHEMA = "o006.stat415.zenodo-consolidated-readers-publication.v1"
USER_AGENT = "O006-STAT415-consolidated-readers/2026.08.28"


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_json(path: Path, value: dict[str, object]) -> None:
    payload = canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def check(response: requests.Response, expected: tuple[int, ...], action: str) -> requests.Response:
    if response.status_code not in expected:
        # Do not expose a response body: an authenticated service can echo a
        # credential or other sensitive request material.
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    return response


def zenodo_url(value: object, label: str, prefixes: tuple[str, ...]) -> str:
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label} omitted its URL")
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError(f"{label} returned an invalid port") from exc
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "zenodo.org"
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or not any(parsed.path.startswith(prefix) for prefix in prefixes)
    ):
        raise RuntimeError(f"{label} returned a non-admitted Zenodo URL")
    return value


def read_token() -> str:
    raw = TOKEN_FILE.read_text("utf-8")
    candidates = re.findall(r"[A-Za-z0-9._~-]{40,}", raw)
    if not candidates:
        raise RuntimeError("Zenodo credential file contains no token-like value")
    return max(candidates, key=len)


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-28",
        "description": (
            "Edisi Bahasa Indonesia (id-ID) lengkap dari rangkaian publik Penn State STAT 415, "
            "Introduction to Mathematical Statistics: laman utama serta Pelajaran 00–12, 14 dari "
            "14 dokumen. Versi ini mempertahankan paket HTML luring dan source/backend lengkap dari "
            "versi sebelumnya, lalu menambahkan pembaca PDF dan EPUB yang dibangun secara deterministik, "
            "beserta manifes, checksum, dan bukti QA yang mengikat byte terbitan. Status lengkap hanya "
            "berlaku untuk komponen Penn State ini; donor kelengkapan dan pendamping orisinal C140 tetap "
            "komponen terpisah. Konten Penn State beserta adaptasinya tetap CC BY-NC 4.0 kecuali "
            "dinyatakan lain; MathJax tetap Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. "
            "Koleksi komponen tidak direlisensi secara seragam, sehingga metadata agregat memakai "
            "other-open dan berkas LICENSE menjadi pernyataan hak yang mengikat. Byte sumber resmi "
            f"tidak diubah. Provenans terjemahan: {contract.MODEL_PROVENANCE}. Seluruh kredit sumber "
            "dan kontributor manusia dipertahankan. Tidak ada dukungan atau pengesahan oleh Penn State "
            "yang tersirat."
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
            "estimation",
            "sufficient statistics",
            "maximum likelihood estimation",
            "Fisher information",
            "asymptotic inference",
            "bootstrap",
            "delta method",
            "hypothesis testing",
            "Bayesian methods",
            "simple linear regression",
            "open educational resources",
            "offline HTML",
            "PDF",
            "EPUB",
            "machine-readable curriculum",
            "AI translation",
            "complete Penn State component",
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


def creator_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row.get("name")) for row in value if isinstance(row, dict)]


def validate_metadata(actual: object, *, public: bool) -> None:
    expected = metadata()
    if not isinstance(actual, dict):
        raise RuntimeError("Zenodo metadata is not an object")
    for key in ("title", "publication_date", "description", "language", "version"):
        if actual.get(key) != expected[key]:
            raise RuntimeError(f"Zenodo metadata mismatch: {key}")
    if public:
        licence = actual.get("license")
        if not isinstance(licence, dict) or licence.get("id") != "other-open":
            raise RuntimeError("Zenodo public licence metadata is not other-open")
        if actual.get("access_right") not in (None, "open"):
            raise RuntimeError("Zenodo public access metadata is not open")
    else:
        for key in ("upload_type", "publication_type", "access_right", "license"):
            if actual.get(key) != expected[key]:
                raise RuntimeError(f"Zenodo draft metadata mismatch: {key}")
    if creator_names(actual.get("creators")) != creator_names(expected["creators"]):
        raise RuntimeError("Zenodo creator metadata differs")
    if set(actual.get("keywords") or []) != set(expected["keywords"]):
        raise RuntimeError("Zenodo keyword metadata differs")
    if actual.get("related_identifiers") != expected["related_identifiers"]:
        raise RuntimeError("Zenodo related-identifier metadata differs")


def concept_identity(value: dict[str, Any]) -> tuple[str, str]:
    return (
        str(value.get("conceptrecid") or value.get("concept_record_id") or ""),
        str(value.get("conceptdoi") or value.get("concept_doi") or ""),
    )


def assert_concept(value: dict[str, Any], label: str, *, allow_blank_doi: bool = False) -> None:
    concept_id, concept_doi = concept_identity(value)
    if concept_id != CONCEPT_RECORD_ID or (
        concept_doi != CONCEPT_DOI and not (allow_blank_doi and not concept_doi)
    ):
        raise RuntimeError(f"{label} is outside the admitted Zenodo concept")


def public_record(session: requests.Session, record_id: str) -> dict[str, Any]:
    value = check(
        session.get(f"{RECORDS}/{record_id}", timeout=120),
        (200,),
        f"read public Zenodo record {record_id}",
    ).json()
    if not isinstance(value, dict) or str(value.get("id")) != record_id:
        raise RuntimeError("public Zenodo record response is malformed")
    assert_concept(value, "public Zenodo record")
    return value


def public_versions(session: requests.Session) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = 1
    while True:
        value = check(
            session.get(
                RECORDS,
                params={
                    "q": f"conceptrecid:{CONCEPT_RECORD_ID}",
                    "all_versions": "true",
                    "size": 25,
                    "page": page,
                },
                timeout=120,
            ),
            (200,),
            "list public Zenodo concept versions",
        ).json()
        hits = value.get("hits", {}).get("hits", []) if isinstance(value, dict) else []
        batch = [row for row in hits if isinstance(row, dict)]
        for row in batch:
            record_id = str(row.get("id", ""))
            if not record_id.isdigit() or record_id in seen:
                raise RuntimeError("public Zenodo search returned an invalid or duplicate record")
            seen.add(record_id)
            if concept_identity(row) == (CONCEPT_RECORD_ID, CONCEPT_DOI):
                rows.append(row)
        if len(batch) < 25:
            break
        page += 1
    return rows


def authenticated_drafts(session: requests.Session) -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    seen: set[str] = set()
    page = 1
    while True:
        value = check(
            session.get(
                DEPOSITIONS,
                params={
                    "q": f"conceptrecid:{CONCEPT_RECORD_ID}",
                    "all_versions": "true",
                    "size": 25,
                    "page": page,
                },
                timeout=120,
            ),
            (200,),
            "list authenticated Zenodo concept depositions",
        ).json()
        if not isinstance(value, list):
            raise RuntimeError("authenticated Zenodo deposition search is not a list")
        batch = [row for row in value if isinstance(row, dict)]
        for row in batch:
            deposition_id = str(row.get("id", ""))
            if not deposition_id.isdigit() or deposition_id in seen:
                raise RuntimeError("authenticated Zenodo search returned an invalid or duplicate deposition")
            seen.add(deposition_id)
            concept_id, concept_doi = concept_identity(row)
            if concept_id != CONCEPT_RECORD_ID:
                if not bool(row.get("submitted")):
                    raise RuntimeError("concept query returned an ambiguous unpublished draft")
                continue
            if concept_doi and concept_doi != CONCEPT_DOI:
                raise RuntimeError("authenticated Zenodo deposition has conflicting concept identity")
            if not bool(row.get("submitted")):
                drafts.append(row)
        if len(batch) < 25:
            break
        page += 1
    return drafts


def download_files(
    session: requests.Session,
    record: dict[str, Any],
    expected: dict[str, contract.Artifact],
) -> list[dict[str, object]]:
    files = [row for row in record.get("files") or [] if isinstance(row, dict)]
    by_name = {str(row.get("key")): row for row in files}
    if set(by_name) != set(expected) or len(files) != len(expected):
        raise RuntimeError("public Zenodo file inventory is not exact")
    verified: list[dict[str, object]] = []
    for name in expected:
        row = by_name[name]
        links = row.get("links") if isinstance(row.get("links"), dict) else {}
        url = zenodo_url(
            links.get("content") or links.get("self"),
            f"public Zenodo file {name}",
            ("/api/records/", "/api/files/", "/records/"),
        )
        response = check(
            session.get(url, stream=True, timeout=900),
            (200,),
            f"download public Zenodo file {name}",
        )
        digest = hashlib.sha256()
        total = 0
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                total += len(chunk)
                digest.update(chunk)
        wanted = expected[name]
        if total != wanted.bytes or digest.hexdigest() != wanted.sha256:
            raise RuntimeError(f"public Zenodo file differs from local union: {name}")
        verified.append({"name": name, "bytes": total, "sha256": digest.hexdigest()})
    return verified


def verify_base_union(public: requests.Session, snap: contract.ReleaseSnapshot) -> None:
    base = public_record(public, BASE_RECORD_ID)
    if base.get("metadata", {}).get("version") != BASE_VERSION:
        raise RuntimeError("public base record has the wrong version")
    inherited = {item.name: item for item in snap.files if item.name in contract.INHERITED_RELEASE_FILES}
    if set(inherited) != contract.INHERITED_RELEASE_FILES:
        raise RuntimeError("local full union omits the exact base-record inventory")
    download_files(public, base, inherited)


def anonymous_readback(record_id: str, snap: contract.ReleaseSnapshot) -> dict[str, object]:
    public = requests.Session()
    public.headers.update({"User-Agent": USER_AGENT + " anonymous"})
    record = public_record(public, record_id)
    validate_metadata(record.get("metadata"), public=True)
    expected = {item.name: item for item in snap.files}
    verified = download_files(public, record, expected)
    links = record.get("links") if isinstance(record.get("links"), dict) else {}
    return {
        "record_id": record_id,
        "doi": str(record.get("doi")),
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "url": str(links.get("html") or f"https://zenodo.org/records/{record_id}"),
        "version": VERSION,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "reader_first": verified[0]["name"] == snap.pdf.name,
        "anonymous_readback": True,
    }


def marker_value() -> dict[str, Any] | None:
    if not DRAFT_MARKER.is_file():
        return None
    value = json.loads(DRAFT_MARKER.read_text("utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("schema") != "o006.stat415.zenodo-consolidated-draft-marker.v1"
        or value.get("concept_record_id") != CONCEPT_RECORD_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("base_record_id") != BASE_RECORD_ID
        or value.get("target_version") != VERSION
        or value.get("status") not in ("created", "owned")
        or not str(value.get("draft_id", "")).isdigit()
    ):
        raise RuntimeError("Zenodo draft marker is not the admitted transaction")
    return value


def write_marker(draft_id: str, status: str) -> None:
    if not draft_id.isdigit() or status not in ("created", "owned"):
        raise RuntimeError("cannot write an invalid Zenodo draft marker")
    atomic_json(
        DRAFT_MARKER,
        {
            "schema": "o006.stat415.zenodo-consolidated-draft-marker.v1",
            "status": status,
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "base_record_id": BASE_RECORD_ID,
            "base_version": BASE_VERSION,
            "target_version": VERSION,
            "draft_id": draft_id,
        },
    )


def refetch(session: requests.Session, draft_id: str) -> dict[str, Any]:
    value = check(
        session.get(f"{DEPOSITIONS}/{draft_id}", timeout=120),
        (200,),
        "read owned Zenodo draft",
    ).json()
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo draft response is not an object")
    return value


def validate_owned_draft(draft: dict[str, Any], draft_id: str) -> None:
    if bool(draft.get("submitted")) or str(draft.get("id")) != draft_id or draft_id == BASE_RECORD_ID:
        raise RuntimeError("Zenodo draft is not the exact owned unpublished draft")
    assert_concept(draft, "owned Zenodo draft", allow_blank_doi=True)
    meta = draft.get("metadata") if isinstance(draft.get("metadata"), dict) else {}
    if meta.get("version") not in (None, "", BASE_VERSION, VERSION):
        raise RuntimeError("owned Zenodo draft has an unexpected version")


def owned_new_version(session: requests.Session) -> tuple[dict[str, Any], bool]:
    marker = marker_value()
    drafts = authenticated_drafts(session)
    drafts_by_id = {str(row["id"]): row for row in drafts}
    if marker is not None:
        draft_id = str(marker["draft_id"])
        if set(drafts_by_id) != {draft_id}:
            raise RuntimeError("owned draft is absent or another concept draft exists")
        draft = refetch(session, draft_id)
        validate_owned_draft(draft, draft_id)
        if marker["status"] != "owned":
            write_marker(draft_id, "owned")
        return draft, True
    if drafts:
        raise RuntimeError("an unmanaged unpublished draft already exists in the concept")

    # This is intentionally the only new-version creation route.  It is
    # pinned to the last verified public record, never to a search result.
    value = check(
        session.post(
            f"{DEPOSITIONS}/{BASE_RECORD_ID}/actions/newversion",
            json={},
            timeout=180,
        ),
        (201,),
        "create new version from record 22105616",
    ).json()
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo new-version response is not an object")
    links = value.get("links") if isinstance(value.get("links"), dict) else {}
    latest_draft = zenodo_url(
        links.get("latest_draft"),
        "Zenodo new-version response",
        ("/api/deposit/depositions/",),
    )
    draft_id = urlparse(latest_draft).path.rstrip("/").rsplit("/", 1)[-1]
    if not draft_id.isdigit() or draft_id == BASE_RECORD_ID:
        raise RuntimeError("Zenodo new-version response omitted a distinct draft id")
    write_marker(draft_id, "created")
    draft = refetch(session, draft_id)
    validate_owned_draft(draft, draft_id)
    write_marker(draft_id, "owned")
    return draft, False


def exact_draft_files(draft: dict[str, Any], snap: contract.ReleaseSnapshot) -> bool:
    current_rows = [row for row in draft.get("files") or [] if isinstance(row, dict)]
    current = {str(row.get("filename")): row for row in current_rows}
    expected = {item.name: item for item in snap.files}
    if set(current) != set(expected) or len(current_rows) != len(expected):
        return False
    for name, wanted in expected.items():
        checksum = str(current[name].get("checksum", ""))
        checksum = checksum[4:] if checksum.startswith("md5:") else checksum
        md5 = hashlib.md5(wanted.payload, usedforsecurity=False).hexdigest()
        if int(current[name].get("filesize", -1)) != wanted.bytes or checksum != md5:
            return False
    return True


def upload_exact_union(
    session: requests.Session,
    draft: dict[str, Any],
    snap: contract.ReleaseSnapshot,
) -> dict[str, Any]:
    draft_id = str(draft.get("id", ""))
    marker = marker_value()
    if marker is None or marker.get("status") != "owned" or str(marker.get("draft_id")) != draft_id:
        raise RuntimeError("refusing to alter files in an unowned Zenodo draft")
    validate_owned_draft(draft, draft_id)
    if not exact_draft_files(draft, snap):
        for row in draft.get("files") or []:
            if not isinstance(row, dict) or not row.get("id"):
                raise RuntimeError("owned draft contains an unidentifiable inherited file")
            check(
                session.delete(f"{DEPOSITIONS}/{draft_id}/files/{row['id']}", timeout=120),
                (204,),
                "clear inherited file from owned new-version draft",
            )
        empty = refetch(session, draft_id)
        if [row for row in empty.get("files") or [] if isinstance(row, dict)]:
            raise RuntimeError("owned Zenodo draft did not become empty")
        links = empty.get("links") if isinstance(empty.get("links"), dict) else {}
        bucket = zenodo_url(
            links.get("bucket"),
            "Zenodo draft upload bucket",
            ("/api/files/",),
        ).rstrip("/")
        for item in snap.files:
            upload_url = zenodo_url(
                f"{bucket}/{quote(item.name, safe='')}",
                f"Zenodo upload target for {item.name}",
                ("/api/files/",),
            )
            check(
                session.put(upload_url, data=item.payload, timeout=900, allow_redirects=False),
                (200, 201),
                f"upload Zenodo file {item.name}",
            )
        draft = refetch(session, draft_id)
    if not exact_draft_files(draft, snap):
        raise RuntimeError("Zenodo draft inventory differs after upload")
    return draft


def base_receipt(snap: contract.ReleaseSnapshot) -> dict[str, object]:
    return {
        "schema": PUBLICATION_SCHEMA,
        "version": VERSION,
        "coverage": snap.package["coverage"],
        "required_base_record_id": BASE_RECORD_ID,
        "required_base_version": BASE_VERSION,
        "required_concept_record_id": CONCEPT_RECORD_ID,
        "required_concept_doi": CONCEPT_DOI,
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "local_inventory": [
            {"name": item.name, "bytes": item.bytes, "sha256": item.sha256}
            for item in snap.files
        ],
        "package_receipt": {
            "path": contract.PACKAGE_RECEIPT.relative_to(contract.ROOT).as_posix(),
            "bytes": snap.package_receipt_bytes,
            "sha256": snap.package_receipt_sha256,
        },
        "translation_provenance": contract.MODEL_PROVENANCE,
    }


def remove_marker(expected_id: str) -> None:
    marker = marker_value()
    if marker is None:
        return
    if str(marker["draft_id"]) != expected_id:
        raise RuntimeError("refusing to remove a marker for a different draft")
    DRAFT_MARKER.unlink()


def write_success(
    base: dict[str, object],
    public: dict[str, object],
    mode: str,
    **extra: object,
) -> None:
    atomic_json(
        READBACK_RECEIPT,
        {
            **base,
            "mode": "verify-published",
            "credential_access": False,
            "public": public,
        },
    )
    atomic_json(
        PUBLICATION_RECEIPT,
        {
            **base,
            "mode": mode,
            "credential_access": mode != "verify-published",
            "public": public,
            **extra,
        },
    )
    atomic_json(
        LINEAGE,
        {
            "schema": "o006.stat415.zenodo-lineage.v1",
            **{
                key: public[key]
                for key in ("record_id", "doi", "concept_record_id", "concept_doi", "url", "version")
            },
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local-preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify-published", action="store_true")
    mode.add_argument("--audit-lineage", action="store_true")
    parser.add_argument("--record-id")
    args = parser.parse_args()

    snap = contract.snapshot()
    base = base_receipt(snap)
    if args.local_preflight:
        print(json.dumps({**contract.preflight_summary(snap), "adapter": "zenodo"}, ensure_ascii=False, sort_keys=True))
        return

    truststore.inject_into_ssl()
    if args.verify_published:
        if not isinstance(args.record_id, str) or not args.record_id.isdigit():
            parser.error("--verify-published requires numeric --record-id")
        public = anonymous_readback(args.record_id, snap)
        receipt = {
            **base,
            "mode": "verify-published",
            "credential_access": False,
            "public": public,
        }
        atomic_json(READBACK_RECEIPT, receipt)
        print(json.dumps({"mode": "verify-published", "record_id": args.record_id, "files": len(snap.files), "status": "pass"}, sort_keys=True))
        return

    token = read_token()
    authenticated = requests.Session()
    authenticated.headers.update({"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT})
    public_session = requests.Session()
    public_session.headers.update({"User-Agent": USER_AGENT + " public"})
    versions = public_versions(public_session)
    targets = [row for row in versions if row.get("metadata", {}).get("version") == VERSION]
    if len(targets) > 1:
        raise RuntimeError("multiple public records use the target version")
    newest = max(versions, key=lambda row: int(str(row.get("id", "0")))) if versions else None

    if args.audit_lineage:
        if not targets:
            raise RuntimeError("target consolidated version is not public")
        if newest is None or str(newest.get("id")) != str(targets[0].get("id")):
            raise RuntimeError("target consolidated version is not the newest public concept version")
        public = anonymous_readback(str(targets[0]["id"]), snap)
        drafts = authenticated_drafts(authenticated)
        if drafts:
            raise RuntimeError("an unpublished draft remains in the admitted Zenodo concept")
        audit = {
            **base,
            "mode": "audit-lineage",
            "credential_access": True,
            "submitted_matching_versions": 1,
            "unsubmitted_concept_drafts": 0,
            "public": public,
        }
        atomic_json(AUDIT_RECEIPT, audit)
        marker = marker_value()
        if marker is not None:
            remove_marker(str(marker["draft_id"]))
        print(json.dumps({"mode": "audit-lineage", "record_id": public["record_id"], "drafts": 0, "status": "pass"}, sort_keys=True))
        return

    if targets:
        if newest is None or str(newest.get("id")) != str(targets[0].get("id")):
            raise RuntimeError("target consolidated version is superseded; refusing to regress the lineage")
        public = anonymous_readback(str(targets[0]["id"]), snap)
        drafts = authenticated_drafts(authenticated)
        if drafts:
            raise RuntimeError("target is public but an unpublished concept draft remains")
        write_success(base, public, "already-published", unsubmitted_concept_drafts=0)
        atomic_json(
            AUDIT_RECEIPT,
            {
                **base,
                "mode": "audit-lineage",
                "credential_access": True,
                "submitted_matching_versions": 1,
                "unsubmitted_concept_drafts": 0,
                "public": public,
            },
        )
        marker = marker_value()
        if marker is not None:
            remove_marker(str(marker["draft_id"]))
        print(json.dumps({"mode": "already-published", "record_id": public["record_id"], "files": len(snap.files), "status": "pass"}, sort_keys=True))
        return

    if not versions:
        raise RuntimeError("admitted Zenodo concept has no public versions")
    assert newest is not None
    if str(newest.get("id")) != BASE_RECORD_ID:
        raise RuntimeError("record 22105616 is not the newest public version; refusing a different base")
    verify_base_union(public_session, snap)
    draft, reused = owned_new_version(authenticated)
    draft = upload_exact_union(authenticated, draft, snap)
    draft_id = str(draft["id"])
    check(
        authenticated.put(
            f"{DEPOSITIONS}/{draft_id}",
            json={"metadata": metadata()},
            timeout=120,
        ),
        (200,),
        "update Zenodo consolidated-reader metadata",
    )
    draft = refetch(authenticated, draft_id)
    validate_metadata(draft.get("metadata"), public=False)
    if not exact_draft_files(draft, snap):
        raise RuntimeError("Zenodo draft failed its final exact-union check")
    published = check(
        authenticated.post(
            f"{DEPOSITIONS}/{draft_id}/actions/publish",
            json={},
            timeout=180,
        ),
        (202,),
        "publish Zenodo consolidated-reader version",
    ).json()
    if not isinstance(published, dict):
        raise RuntimeError("Zenodo publish response is not an object")
    record_id = str(published.get("record_id") or published.get("id") or "")
    if not record_id.isdigit() or record_id in (BASE_RECORD_ID, CONCEPT_RECORD_ID):
        raise RuntimeError("Zenodo publish response omitted a distinct version record id")
    # Zenodo search/download visibility can lag the publish response briefly.
    last_error: Exception | None = None
    public: dict[str, object] | None = None
    for attempt in range(6):
        try:
            public = anonymous_readback(record_id, snap)
            break
        except RuntimeError as exc:
            last_error = exc
            if attempt == 5:
                raise
            time.sleep(3 * (attempt + 1))
    if public is None:
        raise RuntimeError("public readback did not complete") from last_error
    drafts = authenticated_drafts(authenticated)
    if drafts:
        raise RuntimeError("published version passed readback but a concept draft remains")
    write_success(
        base,
        public,
        "publish",
        draft_id=draft_id,
        draft_reused=reused,
        prior_record_id=BASE_RECORD_ID,
        unsubmitted_concept_drafts=0,
    )
    atomic_json(
        AUDIT_RECEIPT,
        {
            **base,
            "mode": "audit-lineage",
            "credential_access": True,
            "submitted_matching_versions": 1,
            "unsubmitted_concept_drafts": 0,
            "public": public,
        },
    )
    remove_marker(draft_id)
    print(json.dumps({"mode": "publish", "record_id": record_id, "doi": public["doi"], "files": len(snap.files), "drafts": 0, "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
