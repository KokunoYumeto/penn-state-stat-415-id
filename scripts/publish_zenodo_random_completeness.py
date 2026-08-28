#!/usr/bin/env python3
"""Publish the cumulative Random-completeness boundary in its Zenodo lineage.

The adapter is intentionally narrow.  Its only deposition-creation request is
``POST /api/deposit/depositions/22142292/actions/newversion``.  A new version
must inherit the 17 files of public record 22142292 byte-for-byte; this script
never deletes or replaces those inherited draft files and uploads only the
eight appended Random-donor release files.  Publication ends with anonymous
byte/hash readback and an authenticated zero-draft lineage audit.

``--local-preflight`` is network- and credential-free.  Anonymous sessions do
not trust environment proxy configuration.  No response body from an
authenticated request is ever included in an error or receipt.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tempfile
import time
from typing import Any
from urllib.parse import quote, urlparse

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
API = "https://zenodo.org/api"
DEPOSITIONS = f"{API}/deposit/depositions"
RECORDS = f"{API}/records"

BASE_RECORD_ID = "22142292"
BASE_VERSION = "2026.08.28.14of14-pdf-epub"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
VERSION = "2026.08.28.c140-random-completeness"
NEW_VERSION_URL = f"{DEPOSITIONS}/{BASE_RECORD_ID}/actions/newversion"

TITLE = (
    "O006/C140 Statistika Matematis — STAT 415 dan Donor Kelengkapan Random "
    "(Bahasa Indonesia)"
)
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
TOKEN_FILE = Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
PACKAGE_RECEIPT = ROOT / "build" / "RANDOM_COMPLETENESS_RELEASE_PACKAGE_RECEIPT.json"
PUBLICATION_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-28_RANDOM_COMPLETENESS.json"
)
READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-28_RANDOM_COMPLETENESS.json"
)
BASE_READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_BASE_READBACK_2026-08-28_RANDOM_COMPLETENESS.json"
)
AUDIT_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-28_RANDOM_COMPLETENESS.json"
)
DRAFT_MARKER = (
    ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-28_RANDOM_COMPLETENESS.json"
)
LINEAGE_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_2026-08-28_RANDOM_COMPLETENESS.json"
)

PACKAGE_SCHEMA = "o006.c140.random-completeness-release-package.v1"
PUBLICATION_SCHEMA = "o006.c140.zenodo-random-completeness-publication.v1"
MARKER_SCHEMA = "o006.c140.zenodo-random-completeness-draft-marker.v1"
USER_AGENT = "O006-C140-random-completeness/2026.08.28"
MAX_RELEASE_BYTES = 500_000_000

BASE_SPECS = (
    ("00_00_stat415-pengantar-statistika-matematis-id.pdf", 20_170_549,
     "f39c1c438cc3e793fe9522eb11f5b02704d89fcdc7aecb2207a599087d458964"),
    ("00_01_stat415-pengantar-statistika-matematis-id.epub", 12_301_415,
     "e122d65348971b91a5ac0c7a8219e0fa3e0eabedb92d130c661648e399e3c574"),
    ("20_COMPLETE_CONSOLIDATED_READERS_RELEASE_NOTES.md", 1_142,
     "c7f8f330bf0db8400eb7f164be3b9c9e5bc9ab4b0f8a72638e949be095b41f40"),
    ("30_COMPLETE_CONSOLIDATED_READERS_LICENSE.md", 1_515,
     "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d"),
    ("40_COMPLETE_CONSOLIDATED_READERS_QA_EVIDENCE.zip", 44_505,
     "bdfb9612b64c9a5280d6533b6bf756fd07b7fea0a85755e01d5d69994546945d"),
    ("00_stat415-id-through-lesson12-offline-reader.zip", 17_648_138,
     "e6c5829452e9d023ae7c54e802673a0e1fb0ddf220716d8f5156f1169ecb01e1"),
    ("10_stat415-id-through-lesson12-source-backend.zip", 37_621_137,
     "510bd0255f1ddbb925f3abb8594b04eac51fa688f0c0f5b184259033e578ada0"),
    ("20_THROUGH_LESSON12_RELEASE_NOTES.md", 1_213,
     "7db90c69118f75e41fef99d0ddd0704471710ff97b1b58957aa8e86a0b36f339"),
    ("30_THROUGH_LESSON12_LICENSE.md", 1_515,
     "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d"),
    ("40_THROUGH_LESSON12_QA_RECEIPT.json", 12_428,
     "d12c9dcb4293de0ec929cc2d2c330e197d936a86e17e27adc20dede10bef15db"),
    ("41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json", 21_702,
     "02583cecceba1db5f8a9f7561f567ebd98585c441a6e4cae5ba1ef92f8710d6e"),
    ("50_THROUGH_LESSON12_RELEASE_MANIFEST.csv", 854,
     "92fb966e8e2d6df14810571bdb171eafa2305e9c0241f7a87f5c3c85545c1528"),
    ("SHA256SUMS_THROUGH_LESSON12.txt", 750,
     "ed97539fb0dd796edcc287cae67920acb04e62bb5e65cd0775e8afbfb7d3d663"),
    ("60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json", 4_763,
     "d9306b66b26a5faf0b90cfc7c1266001cba9a4159cef1394692fb07b6cc7ac49"),
    ("50_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_MANIFEST.csv", 3_655,
     "a55022c0c3f601f6bb25d9b0f41a761f75132f681d869412c7e4cb09a643d9fd"),
    ("SHA256SUMS_COMPLETE_CONSOLIDATED_READERS.txt", 1_661,
     "1b9fdbc6e88b50983488e41eb3df01ea38853f243a319375cfa73bd403aff03e"),
    ("60_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_ROOT_RECEIPT.json", 11_484,
     "a88abbdaac65574089d155613e422ec91896c49ae842b3eaab7935037727260a"),
)

ADDED_NAMES = (
    "01_RANDOM_COMPLETENESS_DONOR_OFFLINE_READER.zip",
    "11_RANDOM_COMPLETENESS_DONOR_SOURCE_BACKEND.zip",
    "21_RANDOM_COMPLETENESS_DONOR_RELEASE_NOTES.md",
    "31_RANDOM_COMPLETENESS_DONOR_LICENSE_AND_ATTRIBUTION.md",
    "41_RANDOM_COMPLETENESS_DONOR_STATIC_QA_EVIDENCE.zip",
    "70_C140_RANDOM_COMPLETENESS_FULL_UNION_MANIFEST.csv",
    "SHA256SUMS_C140_RANDOM_COMPLETENESS.txt",
    "80_C140_RANDOM_COMPLETENESS_FULL_UNION_ROOT_RECEIPT.json",
)
EXPECTED_ORDER = tuple(row[0] for row in BASE_SPECS) + ADDED_NAMES

_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,254}")
_SENSITIVE_NAME = re.compile(
    r"(?:^|[._+-])(token|credential|secret|password|cookie|session)(?:[._+-]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Artifact:
    name: str
    path: str
    bytes: int
    sha256: str
    payload: bytes

    @property
    def md5(self) -> str:
        return hashlib.md5(self.payload, usedforsecurity=False).hexdigest()


@dataclass(frozen=True)
class ReleaseSnapshot:
    package: dict[str, Any]
    receipt_bytes: int
    receipt_sha256: str
    files: tuple[Artifact, ...]
    inherited: tuple[Artifact, ...]
    additions: tuple[Artifact, ...]

    @property
    def total_bytes(self) -> int:
        return sum(item.bytes for item in self.files)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def assert_receipt_safe(value: object) -> None:
    """Reject the only sensitive material this adapter could accidentally persist."""
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if re.search(r"(?i)authorization\s*[:=]|bearer\s+[A-Za-z0-9._~-]+", text):
        raise RuntimeError("refusing to persist credential-shaped receipt content")
    token_path = TOKEN_FILE.as_posix().casefold()
    if token_path in text.replace("\\", "/").casefold():
        raise RuntimeError("refusing to persist the credential-file path")


def atomic_json(path: Path, value: dict[str, object]) -> None:
    assert_receipt_safe(value)
    payload = canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def canonical_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RuntimeError(f"{label} is not a canonical repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise RuntimeError(f"{label} is not a canonical repository-relative path")
    return path.as_posix()


def read_confined(relative: str, label: str) -> bytes:
    canonical = canonical_relative(relative, label)
    path = ROOT.joinpath(*PurePosixPath(canonical).parts)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"{label} is missing or symlinked: {canonical}")
    root = ROOT.resolve(strict=True)
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} resolves outside the repository") from exc
    before = resolved.stat()
    payload = resolved.read_bytes()
    after = resolved.stat()
    if (
        before.st_size != len(payload)
        or after.st_size != len(payload)
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise RuntimeError(f"{label} changed while being snapshotted")
    return payload


def decode_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not a UTF-8 JSON object") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def checked_identity(value: object, label: str) -> tuple[int, str]:
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} identity is absent")
    size = value.get("bytes")
    digest = value.get("sha256")
    if (
        isinstance(size, bool)
        or not isinstance(size, int)
        or size <= 0
        or not isinstance(digest, str)
        or not _SHA256.fullmatch(digest)
    ):
        raise RuntimeError(f"{label} identity is malformed")
    return size, digest


def snapshot() -> ReleaseSnapshot:
    relative_receipt = PACKAGE_RECEIPT.relative_to(ROOT).as_posix()
    receipt_payload = read_confined(relative_receipt, "Random-completeness package receipt")
    package = decode_object(receipt_payload, "Random-completeness package receipt")
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    order = publication.get("upload_order") if isinstance(publication, dict) else None
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("version") != VERSION
        or package.get("translation_provenance") != MODEL_PROVENANCE
        or not isinstance(publication, dict)
        or not isinstance(rows, list)
        or not isinstance(order, list)
        or publication.get("file_count") != len(EXPECTED_ORDER)
        or publication.get("reader_first") is not True
        or publication.get("primary_file") != EXPECTED_ORDER[0]
        or tuple(order) != EXPECTED_ORDER
        or len(rows) != len(EXPECTED_ORDER)
    ):
        raise RuntimeError("package receipt is not the admitted cumulative donor boundary")

    artifacts: list[Artifact] = []
    names: set[str] = set()
    paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"package file row {index} is malformed")
        name = row.get("filename")
        relative = canonical_relative(row.get("source_path"), f"package file row {index} path")
        declared_size, declared_sha = checked_identity(row, f"package file row {index}")
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_ORDER[index]
            or not isinstance(name, str)
            or not _SAFE_NAME.fullmatch(name)
            or _SENSITIVE_NAME.search(name)
            or relative != f"release/{name}"
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or not isinstance(row.get("lineage"), str)
            or not row.get("lineage")
            or not isinstance(row.get("media_type"), str)
            or "/" not in row.get("media_type", "")
            or row.get("primary_reader") is not (index == 0)
            or name in names
            or relative in paths
        ):
            raise RuntimeError(f"package file row {index} has an unsafe identity or path")
        payload = read_confined(relative, f"release asset {name}")
        if (len(payload), sha256(payload)) != (declared_size, declared_sha):
            raise RuntimeError(f"release asset differs from package receipt: {name}")
        total += len(payload)
        if total > MAX_RELEASE_BYTES:
            raise RuntimeError("release payload exceeds the 500 MB boundary")
        artifacts.append(Artifact(name, relative, len(payload), declared_sha, payload))
        names.add(name)
        paths.add(relative)

    if publication.get("total_bytes") != total:
        raise RuntimeError("package aggregate byte count is stale")
    for item, (name, size, digest) in zip(artifacts[: len(BASE_SPECS)], BASE_SPECS):
        if (item.name, item.bytes, item.sha256) != (name, size, digest):
            raise RuntimeError(f"package changed an inherited base asset: {name}")
    if tuple(item.name for item in artifacts[len(BASE_SPECS):]) != ADDED_NAMES:
        raise RuntimeError("package appended inventory differs from the admitted donor files")

    final_receipt = read_confined(relative_receipt, "Random-completeness package receipt")
    if final_receipt != receipt_payload:
        raise RuntimeError("package receipt changed while being snapshotted")
    return ReleaseSnapshot(
        package=package,
        receipt_bytes=len(receipt_payload),
        receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited=tuple(artifacts[: len(BASE_SPECS)]),
        additions=tuple(artifacts[len(BASE_SPECS):]),
    )


def check(response: requests.Response, expected: tuple[int, ...], action: str) -> requests.Response:
    if response.status_code not in expected:
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    return response


def anonymous_session(label: str) -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"User-Agent": f"{USER_AGENT} {label}"})
    return session


def authenticated_session(token: str) -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    session.headers.update({"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT})
    return session


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
            "Rilis kumulatif O006/C140 Bahasa Indonesia (id-ID). Rilis ini mempertahankan, "
            "byte demi byte, 17 berkas dari versi lengkap Penn State STAT 415 sebelumnya "
            "(laman utama dan Pelajaran 00–12; PDF, EPUB, pembaca luring, sumber/backend, "
            "manifes, checksum, dan bukti QA), lalu menambahkan tepat satu donor eksternal: "
            "Kyle Siegrist, Random, 'Sufficient, Complete, and Ancillary Statistics'. Donor "
            "mencakup kecukupan, kelengkapan, ancillary statistics, Rao–Blackwell, "
            "Lehmann–Scheffé, dan Basu, beserta pembaca luring, sumber/backend, hak, manifes, "
            "checksum, dan bukti QA statis. Status lengkap berlaku bagi tulang punggung Penn "
            "State dan donor satu halaman ini; pendamping rigor, simulasi, regresi berganda, "
            "dan mastery orisinal C140 masih merupakan komponen terpisah yang belum selesai. "
            "Hak komponen tidak diseragamkan: materi Penn State/adaptasinya tetap CC BY-NC "
            "4.0 kecuali dinyatakan lain; halaman Random mempunyai saksi CC BY 2.0 pada laman "
            "utama sementara Credits menautkan CC BY 1.0, dan rilis mempertahankan perbedaan "
            "itu serta memenuhi atribusi/pemberitahuan perubahan keduanya; MathJax tetap "
            "Apache-2.0; lapisan orisinal repositori tetap CC BY-SA 4.0. Karena itu metadata "
            "agregat memakai other-open dan berkas lisensi/atribusi per komponen bersifat "
            "mengikat. Byte sumber resmi tidak diubah. Provenans terjemahan dan rekayasa "
            f"edisi: {MODEL_PROVENANCE}. Seluruh kredit sumber dan kontributor manusia "
            "dipertahankan; tidak ada dukungan Penn State atau Kyle Siegrist yang tersirat."
        ),
        "creators": [
            {"name": "Penn State Department of Statistics"},
            {"name": "Siegrist, Kyle"},
        ],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia",
            "id-ID",
            "mathematical statistics",
            "statistika matematis",
            "sufficient statistics",
            "complete statistics",
            "ancillary statistics",
            "Rao-Blackwell theorem",
            "Lehmann-Scheffe theorem",
            "Basu theorem",
            "Penn State STAT 415",
            "Random",
            "open educational resources",
            "offline HTML",
            "PDF",
            "EPUB",
            "machine-readable curriculum",
            "AI translation",
            "component-separated licensing",
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
                "identifier": "https://www.randomservices.org/random/point/Sufficient.html",
                "relation": "isDerivedFrom",
                "resource_type": "publication-other",
                "scheme": "url",
            },
            {
                "identifier": "https://doi.org/10.5281/zenodo.22076539",
                "relation": "isSupplementedBy",
                "resource_type": "publication-book",
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
            raise RuntimeError("Zenodo public license metadata is not other-open")
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
                raise RuntimeError("authenticated deposition has conflicting concept identity")
            if not bool(row.get("submitted")):
                drafts.append(row)
        if len(batch) < 25:
            break
        page += 1
    return drafts


def download_exact(
    session: requests.Session,
    record: dict[str, Any],
    expected: tuple[Artifact, ...],
) -> list[dict[str, object]]:
    rows = [row for row in record.get("files") or [] if isinstance(row, dict)]
    names = [str(row.get("key")) for row in rows]
    expected_names = [item.name for item in expected]
    # Zenodo's record API does not preserve upload order; bind the exact set and
    # emit the verified result in our canonical reader-first package order.
    if len(names) != len(set(names)) or set(names) != set(expected_names):
        raise RuntimeError("public Zenodo file inventory is not exact")
    by_name = dict(zip(names, rows))
    verified: list[dict[str, object]] = []
    for item in expected:
        row = by_name[item.name]
        links = row.get("links") if isinstance(row.get("links"), dict) else {}
        url = zenodo_url(
            links.get("content") or links.get("self"),
            f"public Zenodo file {item.name}",
            ("/api/records/", "/api/files/", "/records/"),
        )
        response = check(
            session.get(url, stream=True, timeout=900),
            (200,),
            f"download public Zenodo file {item.name}",
        )
        digest = hashlib.sha256()
        total = 0
        for chunk in response.iter_content(1024 * 1024):
            if chunk:
                digest.update(chunk)
                total += len(chunk)
        if (total, digest.hexdigest()) != (item.bytes, item.sha256):
            raise RuntimeError(f"public Zenodo file differs from the local contract: {item.name}")
        verified.append({"name": item.name, "bytes": total, "sha256": digest.hexdigest()})
    return verified


def verify_base_record(session: requests.Session, snap: ReleaseSnapshot) -> dict[str, object]:
    record = public_record(session, BASE_RECORD_ID)
    if record.get("metadata", {}).get("version") != BASE_VERSION:
        raise RuntimeError("public base record has the wrong version")
    verified = download_exact(session, record, snap.inherited)
    doi = str(record.get("doi", ""))
    if doi != f"10.5281/zenodo.{BASE_RECORD_ID}":
        raise RuntimeError("public base record DOI is unexpected")
    result = {
        "record_id": BASE_RECORD_ID,
        "doi": doi,
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "version": BASE_VERSION,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "anonymous_readback": True,
        "environment_proxy_trust": False,
    }
    atomic_json(
        BASE_READBACK_RECEIPT,
        {
            "schema": "o006.c140.zenodo-base-readback-random-completeness.v1",
            "target_version": VERSION,
            "package_receipt_sha256": snap.receipt_sha256,
            "credential_access": False,
            "public_base": result,
        },
    )
    return result


def anonymous_readback(
    session: requests.Session,
    record_id: str,
    snap: ReleaseSnapshot,
) -> dict[str, object]:
    record = public_record(session, record_id)
    validate_metadata(record.get("metadata"), public=True)
    verified = download_exact(session, record, snap.files)
    doi = str(record.get("doi", ""))
    if doi != f"10.5281/zenodo.{record_id}":
        raise RuntimeError("public target DOI is unexpected")
    links = record.get("links") if isinstance(record.get("links"), dict) else {}
    html_url = zenodo_url(
        links.get("html") or f"https://zenodo.org/records/{record_id}",
        "public Zenodo record page",
        ("/records/",),
    )
    return {
        "record_id": record_id,
        "doi": doi,
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "url": html_url,
        "version": VERSION,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "reader_first": verified[0]["name"] == EXPECTED_ORDER[0],
        "anonymous_readback": True,
        "environment_proxy_trust": False,
    }


def marker_value(snap: ReleaseSnapshot) -> dict[str, Any] | None:
    if not DRAFT_MARKER.is_file():
        return None
    value = json.loads(DRAFT_MARKER.read_text("utf-8"))
    if (
        not isinstance(value, dict)
        or value.get("schema") != MARKER_SCHEMA
        or value.get("status") not in ("created", "owned")
        or value.get("concept_record_id") != CONCEPT_RECORD_ID
        or value.get("concept_doi") != CONCEPT_DOI
        or value.get("base_record_id") != BASE_RECORD_ID
        or value.get("base_version") != BASE_VERSION
        or value.get("target_version") != VERSION
        or value.get("package_receipt_sha256") != snap.receipt_sha256
        or not str(value.get("draft_id", "")).isdigit()
    ):
        raise RuntimeError("Zenodo donor draft marker is not the admitted transaction")
    return value


def write_marker(draft_id: str, status: str, snap: ReleaseSnapshot) -> None:
    if not draft_id.isdigit() or draft_id in (BASE_RECORD_ID, CONCEPT_RECORD_ID):
        raise RuntimeError("cannot mark an invalid Zenodo donor draft")
    if status not in ("created", "owned"):
        raise RuntimeError("cannot mark an invalid Zenodo donor draft state")
    atomic_json(
        DRAFT_MARKER,
        {
            "schema": MARKER_SCHEMA,
            "status": status,
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "base_record_id": BASE_RECORD_ID,
            "base_version": BASE_VERSION,
            "target_version": VERSION,
            "package_receipt_sha256": snap.receipt_sha256,
            "draft_id": draft_id,
        },
    )


def remove_marker(expected_id: str, snap: ReleaseSnapshot) -> None:
    marker = marker_value(snap)
    if marker is None:
        return
    if str(marker["draft_id"]) != expected_id:
        raise RuntimeError("refusing to remove a marker for a different draft")
    DRAFT_MARKER.unlink()


def refetch(session: requests.Session, draft_id: str) -> dict[str, Any]:
    value = check(
        session.get(f"{DEPOSITIONS}/{draft_id}", timeout=120),
        (200,),
        "read owned Zenodo donor draft",
    ).json()
    if not isinstance(value, dict):
        raise RuntimeError("Zenodo donor draft response is not an object")
    return value


def validate_owned_draft(draft: dict[str, Any], draft_id: str) -> None:
    if bool(draft.get("submitted")) or str(draft.get("id")) != draft_id:
        raise RuntimeError("Zenodo donor draft is not the exact owned unpublished draft")
    if draft_id in (BASE_RECORD_ID, CONCEPT_RECORD_ID):
        raise RuntimeError("Zenodo donor draft is not distinct from the pinned lineage")
    assert_concept(draft, "owned Zenodo donor draft", allow_blank_doi=True)
    meta = draft.get("metadata") if isinstance(draft.get("metadata"), dict) else {}
    if meta.get("version") not in (None, "", BASE_VERSION, VERSION):
        raise RuntimeError("owned Zenodo donor draft has an unexpected version")


def owned_new_version(
    session: requests.Session,
    snap: ReleaseSnapshot,
) -> tuple[dict[str, Any], bool]:
    marker = marker_value(snap)
    drafts = authenticated_drafts(session)
    drafts_by_id = {str(row["id"]): row for row in drafts}
    if marker is not None:
        draft_id = str(marker["draft_id"])
        if set(drafts_by_id) != {draft_id}:
            raise RuntimeError("managed donor draft is absent or another concept draft exists")
        draft = refetch(session, draft_id)
        validate_owned_draft(draft, draft_id)
        if marker["status"] != "owned":
            write_marker(draft_id, "owned", snap)
        return draft, True
    if drafts:
        raise RuntimeError("an unmanaged unpublished draft already exists in the concept")

    # This is the sole deposition-creation request in the adapter.  It is a
    # literal new-version action on the verified public base, never a generic
    # deposition/concept creation endpoint and never a discovered search row.
    value = check(
        session.post(NEW_VERSION_URL, json={}, timeout=180),
        (201,),
        "create pinned Random-completeness Zenodo version",
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
    if not draft_id.isdigit() or draft_id in (BASE_RECORD_ID, CONCEPT_RECORD_ID):
        raise RuntimeError("Zenodo new-version response omitted a distinct draft id")
    write_marker(draft_id, "created", snap)
    draft = refetch(session, draft_id)
    validate_owned_draft(draft, draft_id)
    write_marker(draft_id, "owned", snap)
    return draft, False


def draft_file_map(draft: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    rows = [row for row in draft.get("files") or [] if isinstance(row, dict)]
    names = [str(row.get("filename")) for row in rows]
    if len(names) != len(set(names)):
        raise RuntimeError("owned donor draft contains duplicate filenames")
    return names, dict(zip(names, rows))


def assert_draft_file_identity(row: dict[str, Any], item: Artifact) -> None:
    checksum = str(row.get("checksum", ""))
    checksum = checksum[4:] if checksum.startswith("md5:") else checksum
    if int(row.get("filesize", -1)) != item.bytes or checksum != item.md5:
        raise RuntimeError(f"owned donor draft has mismatched bytes: {item.name}")


def validate_inherited_and_partial_additions(
    draft: dict[str, Any],
    snap: ReleaseSnapshot,
) -> tuple[str, ...]:
    names, by_name = draft_file_map(draft)
    expected = {item.name: item for item in snap.files}
    unexpected = set(names) - set(expected)
    if unexpected:
        raise RuntimeError("owned donor draft contains an unexpected file")
    for item in snap.inherited:
        row = by_name.get(item.name)
        if row is None:
            raise RuntimeError(f"owned donor draft lost inherited base file: {item.name}")
        assert_draft_file_identity(row, item)
    present_additions = tuple(item.name for item in snap.additions if item.name in by_name)
    # The deposit API also returns inherited files in an arbitrary order.  The
    # package manifest remains the order authority; this gate binds the exact
    # filename set and every server-side MD5/byte identity instead.
    if set(names) != {item.name for item in snap.inherited} | set(present_additions):
        raise RuntimeError("owned donor draft filename set is ambiguous")
    expected_prefix = tuple(item.name for item in snap.additions[: len(present_additions)])
    if present_additions != expected_prefix:
        raise RuntimeError("owned donor draft additions are not an exact upload-order prefix")
    for name in present_additions:
        assert_draft_file_identity(by_name[name], expected[name])
    return present_additions


def upload_missing_additions(
    session: requests.Session,
    draft: dict[str, Any],
    snap: ReleaseSnapshot,
) -> dict[str, Any]:
    draft_id = str(draft.get("id", ""))
    marker = marker_value(snap)
    if marker is None or marker.get("status") != "owned" or str(marker.get("draft_id")) != draft_id:
        raise RuntimeError("refusing to upload into an unowned Zenodo donor draft")
    validate_owned_draft(draft, draft_id)
    present = validate_inherited_and_partial_additions(draft, snap)
    links = draft.get("links") if isinstance(draft.get("links"), dict) else {}
    bucket = zenodo_url(
        links.get("bucket"),
        "Zenodo donor upload bucket",
        ("/api/files/",),
    ).rstrip("/")
    for item in snap.additions[len(present):]:
        upload_url = zenodo_url(
            f"{bucket}/{quote(item.name, safe='')}",
            f"Zenodo donor upload target for {item.name}",
            ("/api/files/",),
        )
        check(
            session.put(upload_url, data=item.payload, timeout=900, allow_redirects=False),
            (200, 201),
            f"upload Zenodo donor file {item.name}",
        )
        draft = refetch(session, draft_id)
        validate_owned_draft(draft, draft_id)
        present = validate_inherited_and_partial_additions(draft, snap)
    if present != tuple(item.name for item in snap.additions):
        raise RuntimeError("Zenodo donor draft did not acquire every appended file")
    return draft


def exact_complete_draft(draft: dict[str, Any], snap: ReleaseSnapshot) -> bool:
    try:
        present = validate_inherited_and_partial_additions(draft, snap)
    except RuntimeError:
        return False
    return present == tuple(item.name for item in snap.additions)


def base_receipt(snap: ReleaseSnapshot) -> dict[str, object]:
    return {
        "schema": PUBLICATION_SCHEMA,
        "version": VERSION,
        "required_base_record_id": BASE_RECORD_ID,
        "required_base_version": BASE_VERSION,
        "required_concept_record_id": CONCEPT_RECORD_ID,
        "required_concept_doi": CONCEPT_DOI,
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "inherited_files": len(snap.inherited),
        "appended_files": len(snap.additions),
        "inherited_files_untouched": True,
        "local_inventory": [
            {"name": item.name, "bytes": item.bytes, "sha256": item.sha256}
            for item in snap.files
        ],
        "package_receipt": {
            "path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
            "bytes": snap.receipt_bytes,
            "sha256": snap.receipt_sha256,
        },
        "translation_provenance": MODEL_PROVENANCE,
        "component_license_metadata": "other-open",
    }


def preflight_summary(snap: ReleaseSnapshot) -> dict[str, object]:
    return {
        "mode": "local-preflight",
        "schema": PACKAGE_SCHEMA,
        "publication_version": VERSION,
        "files": len(snap.files),
        "bytes": snap.total_bytes,
        "inherited_files": len(snap.inherited),
        "appended_files": len(snap.additions),
        "primary_file": snap.files[0].name,
        "package_receipt": {
            "path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
            "bytes": snap.receipt_bytes,
            "sha256": snap.receipt_sha256,
        },
        "credential_access": False,
        "network_access": False,
        "browser_processes": False,
    }


def write_public_receipts(
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
            "environment_proxy_trust": False,
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
        LINEAGE_RECEIPT,
        {
            "schema": "o006.c140.zenodo-random-completeness-lineage.v1",
            "record_id": public["record_id"],
            "doi": public["doi"],
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "url": public["url"],
            "version": VERSION,
        },
    )


def matching_target(versions: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    targets = [row for row in versions if row.get("metadata", {}).get("version") == VERSION]
    if len(targets) > 1:
        raise RuntimeError("multiple public records use the target donor version")
    newest = max(versions, key=lambda row: int(str(row.get("id", "0")))) if versions else None
    return targets, newest


def authenticated_zero_draft_audit(
    authenticated: requests.Session,
    public: dict[str, object],
    base: dict[str, object],
) -> None:
    drafts = authenticated_drafts(authenticated)
    if drafts:
        raise RuntimeError("an unpublished draft remains in the admitted Zenodo concept")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--local-preflight", action="store_true")
    mode.add_argument("--publish", action="store_true")
    mode.add_argument("--verify-published", action="store_true")
    mode.add_argument("--audit-lineage", action="store_true")
    parser.add_argument("--record-id")
    args = parser.parse_args()
    if args.record_id is not None and not args.verify_published:
        parser.error("--record-id is valid only with --verify-published")

    snap = snapshot()
    base = base_receipt(snap)
    if args.local_preflight:
        print(json.dumps(preflight_summary(snap), ensure_ascii=False, sort_keys=True))
        return

    truststore.inject_into_ssl()
    public_session = anonymous_session("anonymous")
    verify_base_record(public_session, snap)

    if args.verify_published:
        if not isinstance(args.record_id, str) or not args.record_id.isdigit():
            parser.error("--verify-published requires numeric --record-id")
        public = anonymous_readback(public_session, args.record_id, snap)
        atomic_json(
            READBACK_RECEIPT,
            {
                **base,
                "mode": "verify-published",
                "credential_access": False,
                "environment_proxy_trust": False,
                "public": public,
            },
        )
        print(json.dumps({
            "mode": "verify-published",
            "record_id": args.record_id,
            "files": len(snap.files),
            "status": "pass",
        }, sort_keys=True))
        return

    versions = public_versions(public_session)
    targets, newest = matching_target(versions)
    token = read_token()
    authenticated = authenticated_session(token)

    if args.audit_lineage:
        if not targets:
            raise RuntimeError("target Random-completeness version is not public")
        if newest is None or str(newest.get("id")) != str(targets[0].get("id")):
            raise RuntimeError("target Random-completeness version is not the newest public concept version")
        public = anonymous_readback(public_session, str(targets[0]["id"]), snap)
        authenticated_zero_draft_audit(authenticated, public, base)
        marker = marker_value(snap)
        if marker is not None:
            remove_marker(str(marker["draft_id"]), snap)
        print(json.dumps({
            "mode": "audit-lineage",
            "record_id": public["record_id"],
            "drafts": 0,
            "status": "pass",
        }, sort_keys=True))
        return

    if targets:
        if newest is None or str(newest.get("id")) != str(targets[0].get("id")):
            raise RuntimeError("target donor version is superseded; refusing to regress the lineage")
        public = anonymous_readback(public_session, str(targets[0]["id"]), snap)
        authenticated_zero_draft_audit(authenticated, public, base)
        marker = marker_value(snap)
        if marker is not None:
            remove_marker(str(marker["draft_id"]), snap)
        write_public_receipts(base, public, "already-published", unsubmitted_concept_drafts=0)
        print(json.dumps({
            "mode": "already-published",
            "record_id": public["record_id"],
            "files": len(snap.files),
            "status": "pass",
        }, sort_keys=True))
        return

    if not versions or newest is None:
        raise RuntimeError("admitted Zenodo concept has no public versions")
    if str(newest.get("id")) != BASE_RECORD_ID:
        raise RuntimeError("record 22142292 is not the newest public version; refusing a different base")
    if newest.get("metadata", {}).get("version") != BASE_VERSION:
        raise RuntimeError("newest public base has the wrong pinned version")

    draft, reused = owned_new_version(authenticated, snap)
    draft = upload_missing_additions(authenticated, draft, snap)
    draft_id = str(draft["id"])
    check(
        authenticated.put(
            f"{DEPOSITIONS}/{draft_id}",
            json={"metadata": metadata()},
            timeout=120,
        ),
        (200,),
        "update Zenodo Random-completeness metadata",
    )
    draft = refetch(authenticated, draft_id)
    validate_owned_draft(draft, draft_id)
    validate_metadata(draft.get("metadata"), public=False)
    if not exact_complete_draft(draft, snap):
        raise RuntimeError("Zenodo donor draft failed its final inherited-plus-additions check")

    published = check(
        authenticated.post(
            f"{DEPOSITIONS}/{draft_id}/actions/publish",
            json={},
            timeout=180,
        ),
        (202,),
        "publish Zenodo Random-completeness version",
    ).json()
    if not isinstance(published, dict):
        raise RuntimeError("Zenodo publish response is not an object")
    record_id = str(published.get("record_id") or published.get("id") or "")
    if not record_id.isdigit() or record_id in (BASE_RECORD_ID, CONCEPT_RECORD_ID):
        raise RuntimeError("Zenodo publish response omitted a distinct version record id")

    last_error: Exception | None = None
    public: dict[str, object] | None = None
    for attempt in range(6):
        try:
            public = anonymous_readback(public_session, record_id, snap)
            break
        except RuntimeError as exc:
            last_error = exc
            if attempt == 5:
                raise
            time.sleep(3 * (attempt + 1))
    if public is None:
        raise RuntimeError("public Random-completeness readback did not complete") from last_error

    authenticated_zero_draft_audit(authenticated, public, base)
    write_public_receipts(
        base,
        public,
        "publish",
        draft_id=draft_id,
        draft_reused=reused,
        prior_record_id=BASE_RECORD_ID,
        unsubmitted_concept_drafts=0,
    )
    remove_marker(draft_id, snap)
    print(json.dumps({
        "mode": "publish",
        "record_id": record_id,
        "doi": public["doi"],
        "files": len(snap.files),
        "drafts": 0,
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
