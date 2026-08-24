#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative STAT 415 Lesson 01 checkpoint.

This publisher can only create a new version inside the existing Zenodo concept
10.5281/zenodo.22077422.  It deliberately has no code path that creates a new
deposition/concept.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
API = "https://zenodo.org/api"
DEPOSITIONS = f"{API}/deposit/depositions"
RECORDS = f"{API}/records"
RELEASE = ROOT / "release"
PACKAGE_RECEIPT = ROOT / "build" / "THROUGH_LESSON01_PACKAGE_RECEIPT.json"
DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-24_THROUGH_LESSON01.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-24_THROUGH_LESSON01.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-24_THROUGH_LESSON01.json"
LINEAGE = ROOT / "00_control" / "ZENODO_LINEAGE.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-24_THROUGH_LESSON01.json"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia (3 dari 14 Dokumen)"
VERSION = "2026.08.24.3of14"
PACKAGE_SCHEMA = "o006.stat415.through-lesson01-package.v1"
FILES = (
    "00_stat415-id-through-lesson01-offline-reader.zip",
    "10_stat415-id-through-lesson01-source-backend.zip",
    "20_THROUGH_LESSON01_RELEASE_NOTES.md",
    "30_LICENSE.md",
    "40_THROUGH_LESSON01_QA_RECEIPT.json",
    "41_THROUGH_LESSON01_VISUAL_QA_RECEIPT.json",
    "50_RELEASE_MANIFEST.csv",
    "SHA256SUMS.txt",
    "60_THROUGH_LESSON01_RELEASE_ROOT_RECEIPT.json",
)
ROOT_RECEIPT = FILES[-1]
COMPLETE_DOCUMENTS = ("index", "Lesson00", "Lesson01")
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"


def atomic_json(path: Path, value: dict[str, object]) -> None:
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def read_token() -> str:
    """Read the credential only in an authenticated mode and never expose it."""
    raw = TOKEN_FILE.read_text("utf-8")
    candidates = re.findall(r"[A-Za-z0-9._~-]{40,}", raw)
    if not candidates:
        raise RuntimeError("Zenodo credential file contains no token-like value")
    return max(candidates, key=len)


def check(response: requests.Response, expected: tuple[int, ...], action: str) -> requests.Response:
    if response.status_code not in expected:
        # Never include a response body: an upstream echo could contain credentials.
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    return response


def validated_zenodo_url(
    value: object,
    context: str,
    path_prefixes: tuple[str, ...],
) -> str:
    """Admit only credential-safe HTTPS URLs on the canonical Zenodo origin."""
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{context} omitted its URL")
    parsed = urlparse(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError(f"{context} returned an invalid URL port") from exc
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "zenodo.org"
        or port not in (None, 443)
        or parsed.username is not None
        or parsed.password is not None
        or bool(parsed.query)
        or bool(parsed.fragment)
        or not any(parsed.path.startswith(prefix) for prefix in path_prefixes)
    ):
        raise RuntimeError(f"{context} returned a non-admitted Zenodo URL")
    return value


def load_lineage() -> dict[str, object]:
    value = json.loads(LINEAGE.read_text("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo lineage is not an object")
    if str(value.get("concept_record_id")) != CONCEPT_RECORD_ID or value.get("concept_doi") != CONCEPT_DOI:
        raise RuntimeError("Zenodo lineage is not the admitted existing concept")
    record_id = str(value.get("record_id", ""))
    if not record_id.isdigit() or not str(value.get("doi", "")).startswith("10.5281/zenodo."):
        raise RuntimeError("Zenodo lineage omits a valid published version")
    return value


def load_draft_marker() -> dict[str, object] | None:
    if not DRAFT_MARKER.is_file():
        return None
    value = json.loads(DRAFT_MARKER.read_text("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo draft marker is not an object")
    draft_id = str(value.get("draft_id", ""))
    prior_record_id = str(value.get("prior_record_id", ""))
    if (
        value.get("schema") != "o006.stat415.zenodo-draft-marker.v1"
        or value.get("status") not in ("created", "owned")
        or value.get("concept_record_id") != CONCEPT_RECORD_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("target_version") != VERSION
        or not draft_id.isdigit()
        or not prior_record_id.isdigit()
        or not isinstance(value.get("prior_version"), str)
        or not value.get("prior_version")
    ):
        raise RuntimeError("Zenodo draft marker is not the admitted owned draft")
    return value


def write_draft_marker(
    draft_id: str,
    prior_record_id: str,
    prior_version: str,
    status: str,
) -> None:
    if not draft_id.isdigit() or not prior_record_id.isdigit() or not prior_version:
        raise RuntimeError("cannot write an incomplete Zenodo draft marker")
    if status not in ("created", "owned"):
        raise RuntimeError("cannot write a Zenodo draft marker with an invalid status")
    atomic_json(
        DRAFT_MARKER,
        {
            "schema": "o006.stat415.zenodo-draft-marker.v1",
            "status": status,
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "prior_record_id": prior_record_id,
            "prior_version": prior_version,
            "target_version": VERSION,
            "draft_id": draft_id,
        },
    )


def remove_draft_marker(expected_draft_id: str) -> None:
    marker = load_draft_marker()
    if marker is None:
        return
    if str(marker["draft_id"]) != expected_draft_id:
        raise RuntimeError("refusing to remove a marker for a different Zenodo draft")
    DRAFT_MARKER.unlink()


def validate_release_root(inventory: list[dict[str, object]]) -> None:
    root_rows = [row for row in inventory if row.get("name") == ROOT_RECEIPT]
    if len(root_rows) != 1 or not isinstance(root_rows[0].get("payload"), bytes):
        raise RuntimeError("release root receipt snapshot is absent")
    value = json.loads(root_rows[0]["payload"].decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("release root receipt is not an object")
    covered = list(FILES[:-1])
    if (
        value.get("schema") != "o006.stat415.through-lesson01-release-root.v1"
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
        or manifest_semantics.get("excludes")
        != [FILES[6], FILES[7], ROOT_RECEIPT]
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
        coverage.get("complete_count") != 3
        or coverage.get("corpus_document_count") != 14
        or coverage.get("complete_documents") != list(COMPLETE_DOCUMENTS)
        or coverage.get("next_document") != "Lesson02"
    ):
        raise RuntimeError("release package coverage is not exactly index plus Lessons 00–01")
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
        "publication_date": "2026-08-24",
        "description": (
            "Checkpoint kumulatif yang substansial tetapi masih sebagian untuk rekonstruksi dan terjemahan "
            "Bahasa Indonesia (id-ID) rangkaian publik Penn State STAT 415, Introduction to Mathematical "
            "Statistics. Cakupan tepatnya adalah laman utama, seluruh Pelajaran 00, dan seluruh Pelajaran 01 "
            "tentang statistik urutan: 3 dari 14 dokumen lengkap. Berkas pertama adalah pembaca HTML luring; "
            "paket source-backend yang ringkas, manifes, checksum, lisensi komponen, serta bukti QA deterministik "
            "dan visual turut disertakan. Pelajaran 02–12 belum diterjemahkan dan tetap menaut ke sumber resmi "
            "berbahasa Inggris. Konten Penn State beserta adaptasinya tetap CC BY-NC 4.0 kecuali dinyatakan "
            "lain; MathJax 3.1.2 tetap Apache-2.0; lapisan asli repositori tetap CC BY-SA 4.0. Koleksi komponen "
            "ini tidak direlisensi secara seragam, sehingga metadata agregat memakai other-open dan LICENSE.md "
            "menjadi pernyataan hak yang mengikat. Byte sumber resmi tidak diubah. Provenans terjemahan: "
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
    if public:
        license_row = actual.get("license")
        if not isinstance(license_row, dict) or license_row.get("id") != expected.get("license"):
            raise RuntimeError("Zenodo public licence metadata mismatch")
    else:
        for key in ("upload_type", "publication_type", "access_right", "license"):
            if actual.get(key) != expected.get(key):
                raise RuntimeError(f"Zenodo draft metadata mismatch: {key}")
    if creator_names(actual.get("creators")) != creator_names(expected.get("creators")):
        raise RuntimeError("Zenodo creator metadata mismatch")
    if set(actual.get("keywords") or []) != set(expected.get("keywords") or []):
        raise RuntimeError("Zenodo keyword metadata mismatch")
    if actual.get("related_identifiers") != expected.get("related_identifiers"):
        raise RuntimeError("Zenodo related-identifier metadata mismatch")


def record_concept_identity(record: dict[str, object]) -> tuple[str, str]:
    concept_id = str(record.get("conceptrecid") or record.get("concept_record_id") or "")
    concept_doi = str(record.get("conceptdoi") or record.get("concept_doi") or "")
    return concept_id, concept_doi


def assert_existing_concept(record: dict[str, object], context: str) -> None:
    concept_id, concept_doi = record_concept_identity(record)
    if concept_id != CONCEPT_RECORD_ID or concept_doi != CONCEPT_DOI:
        raise RuntimeError(f"{context} is outside the admitted Zenodo concept")


def authenticated_concept_drafts(session: requests.Session) -> list[dict[str, object]]:
    drafts: list[dict[str, object]] = []
    seen: set[str] = set()
    page = 1
    while True:
        response = check(
            session.get(
                DEPOSITIONS,
                params={
                    "q": f"conceptrecid:{CONCEPT_RECORD_ID}",
                    "all_versions": "true",
                    "size": 100,
                    "page": page,
                },
                timeout=120,
            ),
            (200,),
            "list authenticated Zenodo concept depositions",
        )
        value = response.json()
        if not isinstance(value, list):
            raise RuntimeError("authenticated Zenodo deposition search is not a list")
        batch = [row for row in value if isinstance(row, dict)]
        for row in batch:
            deposition_id = str(row.get("id", ""))
            if not deposition_id.isdigit() or deposition_id in seen:
                raise RuntimeError("authenticated Zenodo search returned an invalid or duplicate deposition id")
            seen.add(deposition_id)
            concept_id, concept_doi = record_concept_identity(row)
            if concept_id != CONCEPT_RECORD_ID:
                if not bool(row.get("submitted")):
                    raise RuntimeError(
                        "concept-scoped Zenodo search returned an ambiguous unpublished draft"
                    )
                continue
            if concept_doi and concept_doi != CONCEPT_DOI:
                raise RuntimeError("authenticated Zenodo deposition has conflicting concept identity")
            if not bool(row.get("submitted")):
                drafts.append(row)
        if len(batch) < 100:
            break
        page += 1
    return drafts


def public_concept_versions(session: requests.Session) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    page = 1
    while True:
        response = check(
            session.get(
                RECORDS,
                params={
                    "q": f"conceptrecid:{CONCEPT_RECORD_ID}",
                    "all_versions": "true",
                    "size": 100,
                    "page": page,
                },
                timeout=120,
            ),
            (200,),
            "list public Zenodo concept versions",
        )
        value = response.json()
        hits = value.get("hits", {}).get("hits", []) if isinstance(value, dict) else []
        batch = [row for row in hits if isinstance(row, dict)]
        batch_ids = [str(row.get("id", "")) for row in batch]
        if (
            any(not record_id.isdigit() for record_id in batch_ids)
            or len(batch_ids) != len(set(batch_ids))
            or any(record_id in seen for record_id in batch_ids)
        ):
            raise RuntimeError("public Zenodo search returned invalid or repeated record ids")
        seen.update(batch_ids)
        rows.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    admitted = [
        row
        for row in rows
        if record_concept_identity(row) == (CONCEPT_RECORD_ID, CONCEPT_DOI)
    ]
    return admitted


def anonymous_readback(record_id: str, inventory: list[dict[str, object]]) -> dict[str, object]:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-Zenodo-anonymous-readback/2.0"})
    record = check(session.get(f"{RECORDS}/{record_id}", timeout=120), (200,), "read public Zenodo record").json()
    if not isinstance(record, dict):
        raise RuntimeError("public Zenodo record is not an object")
    assert_existing_concept(record, "public Zenodo record")
    validate_metadata(record.get("metadata"), metadata(), public=True)
    files = [row for row in record.get("files") or [] if isinstance(row, dict)]
    by_name = {str(row.get("key")): row for row in files}
    if set(by_name) != set(FILES) or len(files) != len(FILES):
        raise RuntimeError("public Zenodo files are not exact")
    expected = {str(row["name"]): row for row in inventory}
    verified: list[dict[str, object]] = []
    for filename in FILES:
        row = by_name[filename]
        url = row.get("links", {}).get("content") or row.get("links", {}).get("self")
        download_url = validated_zenodo_url(
            url,
            f"public Zenodo file {filename}",
            ("/api/records/", "/api/files/", "/records/"),
        )
        response = check(session.get(download_url, stream=True, timeout=900), (200,), f"download public Zenodo file {filename}")
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
        "record_id": str(record.get("id")),
        "doi": str(record.get("doi")),
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "url": str(record.get("links", {}).get("html") or f"https://zenodo.org/records/{record_id}"),
        "version": record.get("metadata", {}).get("version"),
        "files": verified,
        "reader_first": True,
        "anonymous_readback": True,
    }


def refetch(session: requests.Session, deposition_id: str) -> dict[str, object]:
    value = check(
        session.get(f"{DEPOSITIONS}/{deposition_id}", timeout=120),
        (200,),
        "fetch Zenodo deposition",
    ).json()
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo deposition response is not an object")
    return value


def exact_draft_files(draft: dict[str, object], inventory: list[dict[str, object]]) -> bool:
    expected = {str(row["name"]): row for row in inventory}
    current_rows = [row for row in draft.get("files") or [] if isinstance(row, dict)]
    current = {str(row.get("filename")): row for row in current_rows}
    if set(current) != set(expected) or len(current_rows) != len(FILES):
        return False
    for name, wanted in expected.items():
        checksum = str(current[name].get("checksum", ""))
        checksum = checksum[4:] if checksum.startswith("md5:") else checksum
        if int(current[name].get("filesize", -1)) != int(wanted["bytes"]) or checksum != wanted["md5"]:
            return False
    return True


def sort_draft_files(session: requests.Session, draft: dict[str, object]) -> dict[str, object]:
    deposition_id = str(draft["id"])
    current = {str(row.get("filename")): row for row in draft.get("files") or [] if isinstance(row, dict)}
    if set(current) != set(FILES) or any(not current[name].get("id") for name in FILES):
        raise RuntimeError("Zenodo draft cannot be sorted into reader-first order")
    order = [{"id": current[name]["id"]} for name in FILES]
    check(
        session.put(f"{DEPOSITIONS}/{deposition_id}/files", json=order, timeout=120),
        (200,),
        "sort Zenodo draft files",
    )
    draft = refetch(session, deposition_id)
    actual_order = [str(row.get("filename")) for row in draft.get("files") or [] if isinstance(row, dict)]
    if actual_order != list(FILES):
        raise RuntimeError("Zenodo draft file order is not reader-first")
    return draft


def upload_files(
    session: requests.Session,
    draft: dict[str, object],
    inventory: list[dict[str, object]],
) -> dict[str, object]:
    deposition_id = str(draft["id"])
    marker = load_draft_marker()
    if (
        marker is None
        or marker["status"] != "owned"
        or str(marker["draft_id"]) != deposition_id
    ):
        raise RuntimeError("refusing to alter files in an unowned Zenodo draft")
    validate_owned_draft(
        draft,
        deposition_id,
        str(marker["prior_record_id"]),
        str(marker["prior_version"]),
    )
    if not exact_draft_files(draft, inventory):
        for row in draft.get("files") or []:
            if not isinstance(row, dict) or not row.get("id"):
                raise RuntimeError("Zenodo draft contains an unidentifiable inherited file")
            check(
                session.delete(f"{DEPOSITIONS}/{deposition_id}/files/{row['id']}", timeout=120),
                (204,),
                "clear inherited Zenodo draft file",
            )
        draft = refetch(session, deposition_id)
        bucket = validated_zenodo_url(
            draft.get("links", {}).get("bucket"),
            "Zenodo draft upload bucket",
            ("/api/files/",),
        ).rstrip("/")
        for row in inventory:
            filename = str(row["name"])
            payload = row.get("payload")
            if not isinstance(payload, bytes):
                raise RuntimeError(f"release snapshot is absent: {filename}")
            upload_url = validated_zenodo_url(
                f"{bucket}/{quote(filename, safe='')}",
                f"Zenodo upload target for {filename}",
                ("/api/files/",),
            )
            check(
                session.put(
                    upload_url,
                    data=payload,
                    timeout=900,
                    allow_redirects=False,
                ),
                (200, 201),
                f"upload Zenodo file {filename}",
            )
        draft = refetch(session, deposition_id)
    if not exact_draft_files(draft, inventory):
        raise RuntimeError("Zenodo draft file inventory differs after upload")
    return sort_draft_files(session, draft)


def target_public_record(versions: list[dict[str, object]]) -> dict[str, object] | None:
    matches = [row for row in versions if row.get("metadata", {}).get("version") == VERSION]
    if len(matches) > 1:
        raise RuntimeError("multiple published target versions exist in the admitted concept")
    return matches[0] if matches else None


def newest_public_record(versions: list[dict[str, object]]) -> dict[str, object]:
    if not versions:
        raise RuntimeError("the admitted Zenodo concept has no public versions")
    return max(versions, key=lambda row: int(str(row.get("id", "0"))))


def latest_public_record(versions: list[dict[str, object]], lineage: dict[str, object]) -> dict[str, object]:
    latest = newest_public_record(versions)
    if str(latest.get("id")) != str(lineage["record_id"]):
        raise RuntimeError("Zenodo has a newer concept version than the durable local lineage")
    return latest


def validate_owned_draft(
    draft: dict[str, object],
    draft_id: str,
    latest_record_id: str,
    prior_version: str,
) -> None:
    if (
        bool(draft.get("submitted"))
        or str(draft.get("id")) != draft_id
        or draft_id == latest_record_id
    ):
        raise RuntimeError("Zenodo did not provide the exact owned unpublished draft")
    concept_id, concept_doi = record_concept_identity(draft)
    if concept_id != CONCEPT_RECORD_ID:
        raise RuntimeError("owned Zenodo draft has the wrong concept record id")
    if concept_doi and concept_doi != CONCEPT_DOI:
        raise RuntimeError("owned Zenodo draft has the wrong concept DOI")
    draft_meta = draft.get("metadata") if isinstance(draft.get("metadata"), dict) else {}
    if draft_meta.get("version") not in (prior_version, VERSION):
        raise RuntimeError("owned Zenodo draft has the wrong prior or target version")


def create_or_reuse_owned_new_version(
    session: requests.Session,
    latest_record_id: str,
    prior_version: str,
) -> tuple[dict[str, object], bool]:
    marker = load_draft_marker()
    drafts = authenticated_concept_drafts(session)
    drafts_by_id = {str(row["id"]): row for row in drafts}
    if marker is not None:
        draft_id = str(marker["draft_id"])
        if (
            str(marker["prior_record_id"]) != latest_record_id
            or marker["prior_version"] != prior_version
        ):
            raise RuntimeError("owned Zenodo draft marker belongs to a different prior version")
        if set(drafts_by_id) != {draft_id}:
            raise RuntimeError("owned Zenodo draft is absent or another concept draft exists")
        draft = refetch(session, draft_id)
        validate_owned_draft(draft, draft_id, latest_record_id, prior_version)
        if marker["status"] != "owned":
            write_draft_marker(draft_id, latest_record_id, prior_version, "owned")
        return draft, True

    if drafts:
        raise RuntimeError("an unmanaged unpublished draft already exists in the admitted concept")

    response = check(
        session.post(f"{DEPOSITIONS}/{latest_record_id}/actions/newversion", json={}, timeout=180),
        (201,),
        "create Zenodo new-version draft",
    ).json()
    if not isinstance(response, dict):
        raise RuntimeError("Zenodo new-version response is not an object")
    latest_draft = validated_zenodo_url(
        response.get("links", {}).get("latest_draft"),
        "Zenodo new-version response",
        ("/api/deposit/depositions/",),
    )
    draft_id = urlparse(latest_draft).path.rstrip("/").rsplit("/", 1)[-1]
    if not draft_id.isdigit() or draft_id == latest_record_id:
        raise RuntimeError("Zenodo new-version response omitted a distinct numeric draft id")

    # This durable, credential-free marker is written before any inherited
    # file can be deleted.  A failed later step can therefore reuse only this
    # exact draft; an unmanaged draft always aborts.
    write_draft_marker(draft_id, latest_record_id, prior_version, "created")
    draft = refetch(session, draft_id)
    validate_owned_draft(draft, draft_id, latest_record_id, prior_version)
    write_draft_marker(draft_id, latest_record_id, prior_version, "owned")
    return draft, False


def write_success_receipts(
    base: dict[str, object],
    public: dict[str, object],
    mode: str,
    *,
    update_lineage: bool = True,
    **extra: object,
) -> None:
    publication = {**base, "mode": mode, "credential_access": mode not in ("verify-published",), "public": public, **extra}
    atomic_json(DEFAULT_RECEIPT, publication)
    if update_lineage:
        atomic_json(
            LINEAGE,
            {
                "schema": "o006.stat415.zenodo-lineage.v1",
                **{key: public[key] for key in ("record_id", "doi", "concept_record_id", "concept_doi", "url", "version")},
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

    inventory, coverage = local_inventory()
    lineage = load_lineage()
    base: dict[str, object] = {
        "schema": "o006.stat415.zenodo-through-lesson01-publication.v1",
        "version": VERSION,
        "coverage": coverage,
        "local_files": len(inventory),
        "local_bytes": sum(int(row["bytes"]) for row in inventory),
        "local_inventory": [
            {key: row[key] for key in ("name", "bytes", "sha256")} for row in inventory
        ],
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
        public = anonymous_readback(args.record_id, inventory)
        receipt = {**base, "mode": "verify-published", "credential_access": False, "public": public}
        atomic_json(READBACK_RECEIPT, receipt)
        print(json.dumps({"mode": "verify-published", "record_id": args.record_id, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    # From this point onward the credential is read at runtime. It is used only
    # in an Authorization header and is never persisted or printed.
    token = read_token()
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": "O006-STAT415-Zenodo-new-version/2.0"})
    public_session = requests.Session()
    public_session.headers.update({"User-Agent": "O006-STAT415-Zenodo-concept-check/2.0"})
    versions = public_concept_versions(public_session)
    published_target = target_public_record(versions)

    if args.audit_lineage:
        if published_target is None:
            raise RuntimeError("the target cumulative version is not published")
        public = anonymous_readback(str(published_target["id"]), inventory)
        concept_drafts = authenticated_concept_drafts(session)
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
        atomic_json(AUDIT_RECEIPT, audit)
        marker = load_draft_marker()
        if marker is not None:
            remove_draft_marker(str(public["record_id"]))
        print(json.dumps({"mode": "audit-lineage", "record_id": public["record_id"], "submitted": 1, "drafts": 0, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    if published_target is not None:
        public = anonymous_readback(str(published_target["id"]), inventory)
        newest = newest_public_record(versions)
        target_is_newest = str(newest["id"]) == str(published_target["id"])
        mode_name = "already-published" if target_is_newest else "already-published-superseded"
        write_success_receipts(
            base,
            public,
            mode_name,
            update_lineage=target_is_newest,
            newest_record_id=str(newest["id"]),
        )
        marker = load_draft_marker()
        if marker is not None:
            remove_draft_marker(str(public["record_id"]))
        print(json.dumps({"mode": mode_name, "record_id": public["record_id"], "doi": public["doi"], "concept_doi": public["concept_doi"], "newest_record_id": str(newest["id"]), "lineage_updated": target_is_newest, "files": len(FILES), "status": "pass"}, sort_keys=True))
        return

    latest = latest_public_record(versions, lineage)
    prior_version = str(latest.get("metadata", {}).get("version", ""))
    if prior_version != str(lineage.get("version")):
        raise RuntimeError("latest public Zenodo version differs from the durable local lineage")
    draft, reused = create_or_reuse_owned_new_version(session, str(latest["id"]), prior_version)
    draft = upload_files(session, draft, inventory)
    deposition_id = str(draft["id"])
    check(
        session.put(f"{DEPOSITIONS}/{deposition_id}", json={"metadata": metadata()}, timeout=120),
        (200,),
        "update Zenodo new-version metadata",
    )
    draft = refetch(session, deposition_id)
    validate_metadata(draft.get("metadata"), metadata())
    if not exact_draft_files(draft, inventory):
        raise RuntimeError("Zenodo new-version draft failed its final inventory check")
    published = check(
        session.post(f"{DEPOSITIONS}/{deposition_id}/actions/publish", json={}, timeout=180),
        (202,),
        "publish Zenodo new version",
    ).json()
    if not isinstance(published, dict):
        raise RuntimeError("Zenodo publish response is not an object")
    record_id = str(published.get("record_id") or published.get("id") or "")
    if not record_id.isdigit() or record_id == str(latest["id"]):
        raise RuntimeError("Zenodo publish response omitted a distinct new record id")
    public = anonymous_readback(record_id, inventory)
    write_success_receipts(base, public, "publish", draft_id=deposition_id, draft_reused=reused, prior_record_id=str(latest["id"]))
    remove_draft_marker(deposition_id)
    print(json.dumps({"mode": "publish", "record_id": record_id, "doi": public["doi"], "concept_doi": public["concept_doi"], "files": len(FILES), "status": "pass"}, sort_keys=True))


if __name__ == "__main__":
    main()
