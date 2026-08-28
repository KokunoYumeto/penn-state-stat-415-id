#!/usr/bin/env python3
"""Offline contract for the complete STAT 415 PDF/EPUB release union.

This module has no network or credential code.  Publication adapters use its
single immutable snapshot so that a changed reader, QA receipt, or release
asset aborts before any remote transaction can begin.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RECEIPT = ROOT / "build" / "CONSOLIDATED_READERS_PACKAGE_RECEIPT.json"
EXPECTED_SCHEMA = "o006.stat415.consolidated-readers-package.v1"
EXPECTED_PACKAGE_VERSION = "2026.08.28.complete-stat415-readers"
PUBLICATION_VERSION = "2026.08.28.14of14-pdf-epub"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_RELEASE_BYTES = 500_000_000

PDF_SOURCE = "output/pdf/stat415-pengantar-statistika-matematis-id.pdf"
EPUB_SOURCE = "output/epub/stat415-pengantar-statistika-matematis-id.epub"
REQUIRED_QA = {
    "build/CONSOLIDATED_PDF_QA_RECEIPT.json":
        "o006.stat415.consolidated-pdf-qa.v1",
    "build/CONSOLIDATED_PDF_VISUAL_QA_RECEIPT.json":
        "o006.stat415.consolidated-pdf-visual-qa.v1",
    "build/CONSOLIDATED_EPUB_QA_RECEIPT.json":
        "o006.stat415.consolidated-epub-qa.v1",
    "build/CONSOLIDATED_EPUB_STATIC_REFLOW_QA_RECEIPT.json":
        "o006.stat415.consolidated-epub-static-reflow-qa.v1",
}

# A new Zenodo version must preserve the complete prior release inventory.
# These exact files are the public union inherited from record 22105616.
INHERITED_RELEASE_FILES = {
    "00_stat415-id-through-lesson12-offline-reader.zip",
    "10_stat415-id-through-lesson12-source-backend.zip",
    "20_THROUGH_LESSON12_RELEASE_NOTES.md",
    "30_THROUGH_LESSON12_LICENSE.md",
    "40_THROUGH_LESSON12_QA_RECEIPT.json",
    "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON12.txt",
    "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json",
}
EXPECTED_UPLOAD_ORDER = (
    "00_00_stat415-pengantar-statistika-matematis-id.pdf",
    "00_01_stat415-pengantar-statistika-matematis-id.epub",
    "20_COMPLETE_CONSOLIDATED_READERS_RELEASE_NOTES.md",
    "30_COMPLETE_CONSOLIDATED_READERS_LICENSE.md",
    "40_COMPLETE_CONSOLIDATED_READERS_QA_EVIDENCE.zip",
    "00_stat415-id-through-lesson12-offline-reader.zip",
    "10_stat415-id-through-lesson12-source-backend.zip",
    "20_THROUGH_LESSON12_RELEASE_NOTES.md",
    "30_THROUGH_LESSON12_LICENSE.md",
    "40_THROUGH_LESSON12_QA_RECEIPT.json",
    "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON12.txt",
    "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json",
    "50_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_MANIFEST.csv",
    "SHA256SUMS_COMPLETE_CONSOLIDATED_READERS.txt",
    "60_COMPLETE_CONSOLIDATED_READERS_FULL_UNION_ROOT_RECEIPT.json",
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,254}")
_SENSITIVE = re.compile(
    r"(?:^|[._+-])(token|credential|secret|password|cookie|session)(?:[._+-]|$)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Artifact:
    """A release asset snapshotted in memory before remote mutation."""

    name: str
    path: str
    bytes: int
    sha256: str
    payload: bytes


@dataclass(frozen=True)
class ReleaseSnapshot:
    """Fully validated, immutable local publication boundary."""

    package: dict[str, Any]
    package_receipt_bytes: int
    package_receipt_sha256: str
    files: tuple[Artifact, ...]
    pdf: Artifact
    epub: Artifact
    qa_identities: dict[str, dict[str, object]]

    @property
    def total_bytes(self) -> int:
        return sum(item.bytes for item in self.files)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


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
    resolved_root = ROOT.resolve(strict=True)
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RuntimeError(f"{label} resolves outside the repository: {canonical}") from exc
    before = resolved.stat()
    payload = resolved.read_bytes()
    after = resolved.stat()
    if (
        before.st_size != len(payload)
        or after.st_size != len(payload)
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise RuntimeError(f"{label} changed while being snapshotted: {canonical}")
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


def _qa_contract() -> tuple[dict[str, dict[str, object]], dict[str, tuple[int, str]]]:
    identities: dict[str, dict[str, object]] = {}
    readers: dict[str, tuple[int, str]] = {}
    for relative, schema in REQUIRED_QA.items():
        payload = read_confined(relative, "required QA receipt")
        value = decode_object(payload, relative)
        actual_schema = value.get("schema")
        schema_matches = (
            actual_schema == schema
            or (
                relative == "build/CONSOLIDATED_EPUB_STATIC_REFLOW_QA_RECEIPT.json"
                and isinstance(actual_schema, str)
                and actual_schema.startswith("o006.stat415.consolidated-epub-static-reflow")
            )
        )
        if not schema_matches or value.get("status") not in ("pass", "passed"):
            raise RuntimeError(f"required QA gate is not passed: {relative}")
        artifact = value.get("artifact")
        size, digest = checked_identity(artifact, f"{relative} artifact")
        artifact_path = canonical_relative(
            artifact.get("path") if isinstance(artifact, dict) else None,
            f"{relative} artifact path",
        )
        if artifact_path not in (PDF_SOURCE, EPUB_SOURCE):
            raise RuntimeError(f"required QA receipt binds an unexpected artifact: {relative}")
        source_payload = read_confined(artifact_path, "QA-bound reader")
        if (len(source_payload), sha256(source_payload)) != (size, digest):
            raise RuntimeError(f"required QA receipt is stale: {relative}")
        previous = readers.setdefault(artifact_path, (size, digest))
        if previous != (size, digest):
            raise RuntimeError(f"QA receipts disagree about the reader: {artifact_path}")
        identities[relative] = {
            "bytes": len(payload),
            "sha256": sha256(payload),
            "schema": actual_schema,
            "artifact_path": artifact_path,
            "artifact_bytes": size,
            "artifact_sha256": digest,
        }
    if set(readers) != {PDF_SOURCE, EPUB_SOURCE}:
        raise RuntimeError("QA receipts do not close both consolidated readers")
    return identities, readers


def snapshot() -> ReleaseSnapshot:
    """Validate and snapshot the exact full-union release without side effects."""

    receipt_payload = read_confined(
        PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
        "consolidated package receipt",
    )
    package = decode_object(receipt_payload, "consolidated package receipt")
    qa_identities, reader_identities = _qa_contract()
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    order = publication.get("upload_order") if isinstance(publication, dict) else None
    coverage = package.get("coverage")
    lineage = package.get("lineage")
    gates = package.get("gates")
    if (
        package.get("schema") != EXPECTED_SCHEMA
        or package.get("status") != "ready"
        or package.get("version") != EXPECTED_PACKAGE_VERSION
        or package.get("translation_provenance") != MODEL_PROVENANCE
        or not isinstance(rows, list)
        or not rows
        or not isinstance(order, list)
        or not isinstance(coverage, dict)
        or coverage.get("complete_count") != 14
        or coverage.get("corpus_document_count") != 14
        or coverage.get("complete_documents") != ["index", *[f"Lesson{i:02d}" for i in range(13)]]
        or not isinstance(lineage, dict)
        or lineage.get("concept_doi") != "10.5281/zenodo.22077422"
        or lineage.get("prior_record_id") != "22105616"
        or lineage.get("create_competing_concept") is not False
        or not isinstance(gates, dict)
        or not isinstance(gates.get("pdf"), dict)
        or not isinstance(gates.get("epub"), dict)
        or gates.get("prior_release", {}).get("file_count") != 9
        or gates.get("prior_release", {}).get("bytes") != 55_312_500
        or gates.get("prior_release", {}).get("identity_verified") is not True
        or not isinstance(publication, dict)
        or publication.get("fields") != [
            "upload_order",
            "filename",
            "bytes",
            "sha256",
            "role",
            "lineage",
            "media_type",
            "primary_reader",
            "source_path",
        ]
    ):
        raise RuntimeError("package receipt is not the admitted complete full-union boundary")

    artifacts: list[Artifact] = []
    names: list[str] = []
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
            or not isinstance(name, str)
            or not _SAFE_NAME.fullmatch(name)
            or _SENSITIVE.search(name)
            or PurePosixPath(relative).name != name
            or relative != f"release/{name}"
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or row.get("lineage") not in (
                "current-consolidated-readers",
                "preserved-zenodo-record-22105616",
            )
            or not isinstance(row.get("media_type"), str)
            or "/" not in row.get("media_type", "")
            or not isinstance(row.get("primary_reader"), bool)
            or row.get("primary_reader") is not (index == 0)
            or name in names
            or relative in paths
        ):
            raise RuntimeError(f"package file row {index} has an unsafe or duplicate name/path")
        payload = read_confined(relative, "release asset")
        if (len(payload), sha256(payload)) != (declared_size, declared_sha):
            raise RuntimeError(f"release asset differs from the package receipt: {name}")
        total += len(payload)
        if total > MAX_RELEASE_BYTES:
            raise RuntimeError("release payload exceeds the 500 MB task cap")
        artifacts.append(Artifact(name, relative, len(payload), declared_sha, payload))
        names.append(name)
        paths.add(relative)

    if (
        tuple(order) != EXPECTED_UPLOAD_ORDER
        or names != list(EXPECTED_UPLOAD_ORDER)
        or publication.get("file_count") != len(artifacts)
        or publication.get("file_count") != 17
        or publication.get("total_bytes") != total
        or publication.get("reader_first") is not True
    ):
        raise RuntimeError("package upload order or aggregate identity differs")
    if not INHERITED_RELEASE_FILES.issubset(names):
        raise RuntimeError("full-union package omits a file inherited from record 22105616")

    pdf_rows = [item for item in artifacts if item.name.casefold().endswith(".pdf")]
    epub_rows = [item for item in artifacts if item.name.casefold().endswith(".epub")]
    if len(pdf_rows) != 1 or len(epub_rows) != 1:
        raise RuntimeError("full-union package must expose exactly one PDF and one EPUB reader")
    pdf, epub = pdf_rows[0], epub_rows[0]
    if artifacts[0] != pdf or publication.get("primary_file") != pdf.name:
        raise RuntimeError("the PDF reader is not the first and primary release asset")
    if artifacts[1] != epub or publication.get("secondary_reader") != epub.name:
        raise RuntimeError("the EPUB reader is not the second release asset")
    if (pdf.bytes, pdf.sha256) != reader_identities[PDF_SOURCE]:
        raise RuntimeError("packaged PDF differs from its current QA-bound reader")
    if (epub.bytes, epub.sha256) != reader_identities[EPUB_SOURCE]:
        raise RuntimeError("packaged EPUB differs from its current QA-bound reader")

    for label, gate, artifact in (
        ("PDF", gates.get("pdf"), pdf),
        ("EPUB", gates.get("epub"), epub),
    ):
        bound = gate.get("artifact") if isinstance(gate, dict) else None
        source = PDF_SOURCE if label == "PDF" else EPUB_SOURCE
        if (
            not isinstance(bound, dict)
            or bound.get("path") != source
            or bound.get("bytes") != artifact.bytes
            or bound.get("sha256") != artifact.sha256
        ):
            raise RuntimeError(f"package receipt has a stale {label} artifact gate")

    packager = package.get("packager")
    if not isinstance(packager, dict):
        raise RuntimeError("package receipt omits its packager identity")
    packager_path = canonical_relative(packager.get("path"), "packager path")
    packager_payload = read_confined(packager_path, "packager")
    packager_bytes, packager_sha = checked_identity(packager, "packager")
    if (
        (len(packager_payload), sha256(packager_payload)) != (packager_bytes, packager_sha)
        or packager.get("network_access") is not False
        or packager.get("browser_processes") is not False
        or packager.get("credential_access") is not False
        or packager.get("publication_side_effects") is not False
    ):
        raise RuntimeError("package receipt has a stale or unsafe packager identity")

    gate_bindings = {
        "build/CONSOLIDATED_PDF_QA_RECEIPT.json": gates.get("pdf", {}).get("structural_qa"),
        "build/CONSOLIDATED_PDF_VISUAL_QA_RECEIPT.json": gates.get("pdf", {}).get("visual_qa"),
        "build/CONSOLIDATED_EPUB_QA_RECEIPT.json": gates.get("epub", {}).get("qa_receipt"),
        "build/CONSOLIDATED_EPUB_STATIC_REFLOW_QA_RECEIPT.json": gates.get("epub", {}).get("static_reflow_qa"),
    }
    for relative, identity in qa_identities.items():
        binding = gate_bindings.get(relative)
        if (
            not isinstance(binding, dict)
            or binding.get("path") != relative
            or binding.get("bytes") != identity["bytes"]
            or binding.get("sha256") != identity["sha256"]
        ):
            raise RuntimeError(f"package receipt has a stale QA binding: {relative}")

    evidence = next(
        (item for item in artifacts if item.name == "40_COMPLETE_CONSOLIDATED_READERS_QA_EVIDENCE.zip"),
        None,
    )
    if evidence is None:
        raise RuntimeError("full-union package omits the compact QA evidence archive")
    try:
        with zipfile.ZipFile(io.BytesIO(evidence.payload), "r") as archive:
            if archive.testzip() is not None:
                raise RuntimeError("QA evidence archive failed CRC verification")
            for relative, identity in qa_identities.items():
                entry = f"final-static/{PurePosixPath(relative).name}"
                payload = archive.read(entry)
                if (len(payload), sha256(payload)) != (
                    int(identity["bytes"]),
                    str(identity["sha256"]),
                ):
                    raise RuntimeError(f"QA evidence archive has stale bytes: {entry}")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise RuntimeError("QA evidence archive does not close all required QA receipts") from exc

    # Detect a package receipt replacement during the potentially expensive
    # release snapshot.  Publication consumes exactly one frozen contract.
    final_receipt = read_confined(
        PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
        "consolidated package receipt",
    )
    if final_receipt != receipt_payload:
        raise RuntimeError("package receipt changed while being snapshotted")
    return ReleaseSnapshot(
        package=package,
        package_receipt_bytes=len(receipt_payload),
        package_receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        pdf=pdf,
        epub=epub,
        qa_identities=qa_identities,
    )


def preflight_summary(value: ReleaseSnapshot) -> dict[str, object]:
    return {
        "mode": "local-preflight",
        "schema": EXPECTED_SCHEMA,
        "package_version": EXPECTED_PACKAGE_VERSION,
        "publication_version": PUBLICATION_VERSION,
        "files": len(value.files),
        "bytes": value.total_bytes,
        "primary_file": value.pdf.name,
        "pdf": {"bytes": value.pdf.bytes, "sha256": value.pdf.sha256},
        "epub": {"bytes": value.epub.bytes, "sha256": value.epub.sha256},
        "qa_receipts": value.qa_identities,
        "package_receipt": {
            "path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
            "bytes": value.package_receipt_bytes,
            "sha256": value.package_receipt_sha256,
        },
        "credential_access": False,
        "network_access": False,
    }
