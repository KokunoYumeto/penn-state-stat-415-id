#!/usr/bin/env python3
"""Publish and anonymously verify the first STAT 415 id-ID checkpoint on Zenodo."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
API = "https://zenodo.org/api"
DEPOSITIONS = f"{API}/deposit/depositions"
RELEASE = ROOT / "release"
PACKAGE_RECEIPT = ROOT / "build" / "FIRST_UNIT_PACKAGE_RECEIPT.json"
DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-24_FIRST_UNIT.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-24_FIRST_UNIT.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-24_FIRST_UNIT.json"
LINEAGE = ROOT / "00_control" / "ZENODO_LINEAGE.json"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia (Unit 1 dari 14)"
VERSION = "2026.08.24.2of14"
FILES = (
    "00_stat415-id-first-unit-offline-reader.zip",
    "10_stat415-id-first-unit-source-backend.zip",
    "20_FIRST_UNIT_RELEASE_NOTES.md",
    "30_LICENSE.md",
    "40_FIRST_UNIT_QA_RECEIPT.json",
    "41_FIRST_UNIT_VISUAL_QA_RECEIPT.json",
    "50_RELEASE_MANIFEST.csv",
    "SHA256SUMS.txt",
)
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: Path) -> str:
    digest = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict[str, object]) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def read_token() -> str:
    raw = TOKEN_FILE.read_text("utf-8")
    candidates = re.findall(r"[A-Za-z0-9._~-]{40,}", raw)
    if not candidates:
        raise RuntimeError("Zenodo credential file contains no token-like value")
    return max(candidates, key=len)


def check(response: requests.Response, expected: tuple[int, ...], action: str) -> requests.Response:
    if response.status_code not in expected:
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    return response


def local_inventory() -> list[dict[str, object]]:
    package = json.loads(PACKAGE_RECEIPT.read_text("utf-8"))
    rows = package.get("files") if isinstance(package, dict) else None
    if package.get("status") != "ready" or package.get("upload_order") != list(FILES) or not isinstance(rows, list):
        raise RuntimeError("release package receipt is not the admitted reader-first boundary")
    by_name = {str(row.get("filename")): row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(FILES) or min(FILES, key=str.casefold) != FILES[0]:
        raise RuntimeError("release package file set is not exact and reader-first")
    inventory = []
    for filename in FILES:
        path = RELEASE / filename
        if not path.is_file():
            raise RuntimeError(f"release file missing: {filename}")
        row = {
            "name": filename, "bytes": path.stat().st_size,
            "sha256": sha256_file(path), "md5": md5_file(path),
        }
        expected = by_name[filename]
        if row["bytes"] != expected.get("bytes") or row["sha256"] != expected.get("sha256"):
            raise RuntimeError(f"release file differs from package receipt: {filename}")
        inventory.append(row)
    if sum(int(row["bytes"]) for row in inventory) >= 500_000_000:
        raise RuntimeError("release payload exceeds the 500 MB task cap")
    return inventory


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-24",
        "description": (
            "Checkpoint substansial tetapi masih sebagian untuk rekonstruksi dan terjemahan Bahasa Indonesia "
            "(id-ID) rangkaian publik Penn State STAT 415, Introduction to Mathematical Statistics. Cakupan "
            "tepatnya adalah laman utama dan seluruh Pelajaran 00: 2 dari 14 dokumen lengkap, 523 segmen "
            "terjemahan, 562 unit struktural sumber, 331 permukaan matematika, lima contoh/penyelesaian, dan "
            "empat pengungkapan penyelesaian HTML aksesibel. Berkas pertama adalah pembaca HTML luring; paket "
            "source-backend yang ringkas, manifes, checksum, lisensi komponen, dan bukti QA turut disertakan. "
            "Pelajaran 01–12 belum diterjemahkan dan tetap menaut ke sumber resmi berbahasa Inggris. Konten "
            "Penn State tetap CC BY-NC 4.0 kecuali dinyatakan lain; MathJax 3.1.2 tetap Apache-2.0; lapisan "
            "asli repositori memiliki lisensi terpisah. Koleksi ini tidak direlisensi secara seragam. Byte "
            f"sumber resmi tidak diubah. Provenans terjemahan: {MODEL_PROVENANCE}. Seluruh kredit sumber dan "
            "kontributor manusia dipertahankan. Tidak ada dukungan atau pengesahan oleh Penn State yang tersirat."
        ),
        "creators": [{"name": "Penn State Department of Statistics"}],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia", "id-ID", "mathematical statistics", "statistika matematis",
            "probability review", "sampling distributions", "open educational resources",
            "offline HTML", "machine-readable curriculum", "AI translation", "partial edition",
        ],
        "language": "ind",
        "version": VERSION,
        "related_identifiers": [
            {
                "identifier": "https://online.stat.psu.edu/stat415/",
                "relation": "isDerivedFrom", "resource_type": "publication-other", "scheme": "url",
            },
            {
                "identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
                "relation": "isSupplementedBy", "resource_type": "software", "scheme": "url",
            },
        ],
    }


def creator_names(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row.get("name")) for row in value if isinstance(row, dict)]


def validate_metadata(actual: object, expected: dict[str, object], public: bool = False) -> None:
    if not isinstance(actual, dict):
        raise RuntimeError("Zenodo metadata is not an object")
    for key in ("title", "publication_date", "description", "language", "version"):
        if actual.get(key) != expected.get(key):
            raise RuntimeError(f"Zenodo metadata mismatch: {key}")
    if not public:
        for key in ("upload_type", "publication_type", "access_right", "license"):
            if actual.get(key) != expected.get(key):
                raise RuntimeError(f"Zenodo draft metadata mismatch: {key}")
    else:
        license_row = actual.get("license")
        if not isinstance(license_row, dict) or license_row.get("id") != expected.get("license"):
            raise RuntimeError("Zenodo public licence metadata mismatch")
    if creator_names(actual.get("creators")) != creator_names(expected.get("creators")):
        raise RuntimeError("Zenodo creator metadata mismatch")
    if set(actual.get("keywords") or []) != set(expected.get("keywords") or []):
        raise RuntimeError("Zenodo keyword metadata mismatch")
    if actual.get("related_identifiers") != expected.get("related_identifiers"):
        raise RuntimeError("Zenodo related-identifier metadata mismatch")


def authenticated_matches(session: requests.Session) -> list[dict[str, object]]:
    response = check(session.get(DEPOSITIONS, params={"q": "STAT 415", "size": 100, "all_versions": "true"}, timeout=120), (200,), "search Zenodo depositions")
    value = response.json()
    rows = value if isinstance(value, list) else value.get("hits", {}).get("hits", []) if isinstance(value, dict) else []
    return [row for row in rows if isinstance(row, dict) and isinstance(row.get("metadata"), dict) and row["metadata"].get("title") == TITLE]


def refetch(session: requests.Session, deposition_id: str) -> dict[str, object]:
    value = check(session.get(f"{DEPOSITIONS}/{deposition_id}", timeout=120), (200,), "fetch Zenodo deposition").json()
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo deposition response is not an object")
    return value


def exact_draft_files(draft: dict[str, object], inventory: list[dict[str, object]]) -> bool:
    expected = {str(row["name"]): row for row in inventory}
    current = {str(row.get("filename")): row for row in draft.get("files") or [] if isinstance(row, dict)}
    if set(current) != set(expected):
        return False
    for name, wanted in expected.items():
        checksum = str(current[name].get("checksum", ""))
        checksum = checksum[4:] if checksum.startswith("md5:") else checksum
        if int(current[name].get("filesize", -1)) != int(wanted["bytes"]) or checksum != wanted["md5"]:
            return False
    return True


def upload_files(session: requests.Session, draft: dict[str, object], inventory: list[dict[str, object]]) -> dict[str, object]:
    deposition_id = str(draft["id"])
    if not exact_draft_files(draft, inventory):
        for row in draft.get("files") or []:
            check(session.delete(f"{DEPOSITIONS}/{deposition_id}/files/{row['id']}", timeout=120), (204,), "clear matching Zenodo draft file")
        draft = refetch(session, deposition_id)
        bucket = str(draft.get("links", {}).get("bucket", "")).rstrip("/")
        if not bucket:
            raise RuntimeError("Zenodo draft omitted its upload bucket")
        for row in inventory:
            filename = str(row["name"])
            with (RELEASE / filename).open("rb") as stream:
                check(session.put(f"{bucket}/{quote(filename)}", data=stream, timeout=900), (200, 201), f"upload Zenodo file {filename}")
        draft = refetch(session, deposition_id)
    if not exact_draft_files(draft, inventory):
        raise RuntimeError("Zenodo draft file inventory differs after upload")
    return draft


def anonymous_readback(record_id: str, inventory: list[dict[str, object]]) -> dict[str, object]:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-Zenodo-anonymous-readback/1.0"})
    record = check(session.get(f"{API}/records/{record_id}", timeout=120), (200,), "read public Zenodo record").json()
    if not isinstance(record, dict):
        raise RuntimeError("public Zenodo record is not an object")
    validate_metadata(record.get("metadata"), metadata(), public=True)
    files = [row for row in record.get("files") or [] if isinstance(row, dict)]
    by_name = {str(row.get("key")): row for row in files}
    if set(by_name) != set(FILES) or min(by_name, key=str.casefold) != FILES[0]:
        raise RuntimeError("public Zenodo files are not exact and reader-first")
    expected = {str(row["name"]): row for row in inventory}
    verified = []
    for filename in FILES:
        row = by_name[filename]
        url = row.get("links", {}).get("content") or row.get("links", {}).get("self")
        response = check(session.get(str(url), stream=True, timeout=900), (200,), f"download public Zenodo file {filename}")
        digest = hashlib.sha256()
        total = 0
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                total += len(chunk)
                digest.update(chunk)
        if total != expected[filename]["bytes"] or digest.hexdigest() != expected[filename]["sha256"]:
            raise RuntimeError(f"public Zenodo file differs: {filename}")
        verified.append({"name": filename, "bytes": total, "sha256": digest.hexdigest()})
    return {
        "record_id": str(record.get("id")), "doi": str(record.get("doi")),
        "concept_record_id": str(record.get("conceptrecid")), "concept_doi": str(record.get("conceptdoi")),
        "url": str(record.get("links", {}).get("html") or f"https://zenodo.org/records/{record_id}"),
        "version": record.get("metadata", {}).get("version"), "files": verified,
        "reader_first": True, "anonymous_readback": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local-preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify-published", action="store_true")
    mode.add_argument("--audit-lineage", action="store_true")
    parser.add_argument("--record-id")
    args = parser.parse_args()
    truststore.inject_into_ssl()
    inventory = local_inventory()
    base = {
        "schema": "o006.stat415.zenodo-first-unit-publication.v1", "version": VERSION,
        "coverage": "landing/index plus complete Lesson00; 2 of 14 documents",
        "local_files": len(inventory), "local_bytes": sum(int(row["bytes"]) for row in inventory),
        "local_inventory": [{key: row[key] for key in ("name", "bytes", "sha256")} for row in inventory],
        "translation_provenance": MODEL_PROVENANCE,
    }
    if args.local_preflight:
        base.update({"mode": "local-preflight", "credential_access": False, "network_access": False})
        print(json.dumps(base, ensure_ascii=False, sort_keys=True))
        return
    if args.verify_published:
        if not args.record_id or not args.record_id.isdigit():
            raise RuntimeError("--verify-published requires numeric --record-id")
        base.update({"mode": "verify-published", "credential_access": False, "public": anonymous_readback(args.record_id, inventory)})
        atomic_json(READBACK_RECEIPT, base)
        print(json.dumps({"mode": "verify-published", "record_id": args.record_id, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    if args.audit_lineage:
        token = read_token()
        audit_session = requests.Session()
        audit_session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": "O006-STAT415-Zenodo-lineage-audit/1.0"})
        matches = authenticated_matches(audit_session)
        submitted = [row for row in matches if bool(row.get("submitted")) and row.get("metadata", {}).get("version") == VERSION]
        drafts = [row for row in matches if not bool(row.get("submitted"))]
        if len(submitted) != 1 or drafts:
            raise RuntimeError("Zenodo lineage is not one submitted version with zero drafts")
        record_id = str(submitted[0].get("record_id") or submitted[0].get("id"))
        public = anonymous_readback(record_id, inventory)
        base.update({"mode": "audit-lineage", "credential_access": True, "submitted_matching_versions": 1, "unsubmitted_matching_drafts": 0, "public": public})
        atomic_json(AUDIT_RECEIPT, base)
        print(json.dumps({"mode": "audit-lineage", "record_id": record_id, "submitted": 1, "drafts": 0, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    token = read_token()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": "O006-STAT415-Zenodo-publication/1.0"})
    matches = authenticated_matches(session)
    submitted = [row for row in matches if bool(row.get("submitted")) and row.get("metadata", {}).get("version") == VERSION]
    drafts = [row for row in matches if not bool(row.get("submitted"))]
    if len(submitted) > 1 or len(drafts) > 1:
        raise RuntimeError("multiple matching Zenodo records or drafts exist")
    if submitted:
        if drafts:
            raise RuntimeError("submitted target exists with an unexpected matching draft")
        record_id = str(submitted[0].get("record_id") or submitted[0].get("id"))
        public = anonymous_readback(record_id, inventory)
        base.update({"mode": "already-published", "credential_access": True, "public": public})
        atomic_json(DEFAULT_RECEIPT, base)
        atomic_json(LINEAGE, {"schema": "o006.stat415.zenodo-lineage.v1", **{key: public[key] for key in ("record_id", "doi", "concept_record_id", "concept_doi", "url", "version")}})
        print(json.dumps({"mode": "already-published", "record_id": record_id, "doi": public["doi"], "files": len(FILES), "status": "pass"}, sort_keys=True))
        return
    if matches and not drafts:
        raise RuntimeError("matching Zenodo title exists at another version; new-version workflow required")
    if drafts:
        draft = refetch(session, str(drafts[0]["id"]))
        draft_meta = draft.get("metadata") if isinstance(draft.get("metadata"), dict) else {}
        if draft_meta.get("version") not in (None, "", VERSION):
            raise RuntimeError("matching Zenodo draft belongs to another version")
        reused = True
    else:
        draft_value = check(session.post(DEPOSITIONS, json={}, timeout=120), (201,), "create Zenodo deposition").json()
        if not isinstance(draft_value, dict):
            raise RuntimeError("new Zenodo deposition response is not an object")
        draft = draft_value
        reused = False
    draft = upload_files(session, draft, inventory)
    deposition_id = str(draft["id"])
    check(session.put(f"{DEPOSITIONS}/{deposition_id}", json={"metadata": metadata()}, timeout=120), (200,), "update Zenodo metadata")
    draft = refetch(session, deposition_id)
    validate_metadata(draft.get("metadata"), metadata())
    if not exact_draft_files(draft, inventory):
        raise RuntimeError("Zenodo draft failed final inventory check")
    published = check(session.post(f"{DEPOSITIONS}/{deposition_id}/actions/publish", json={}, timeout=180), (202,), "publish Zenodo deposition").json()
    record_id = str(published.get("record_id") or published.get("id"))
    public = anonymous_readback(record_id, inventory)
    base.update({"mode": "publish", "credential_access": True, "draft_id": deposition_id, "draft_reused": reused, "public": public})
    atomic_json(DEFAULT_RECEIPT, base)
    atomic_json(LINEAGE, {"schema": "o006.stat415.zenodo-lineage.v1", **{key: public[key] for key in ("record_id", "doi", "concept_record_id", "concept_doi", "url", "version")}})
    print(json.dumps({"mode": "publish", "record_id": record_id, "doi": public["doi"], "concept_doi": public["concept_doi"], "files": len(FILES), "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
