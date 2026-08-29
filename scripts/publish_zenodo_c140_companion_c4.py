#!/usr/bin/env python3
"""Publish the cumulative C140 original-companion C4 Zenodo boundary.

The adapter creates a new public version only from anonymously verified record
22161363 in the existing concept 22077422.  Its 49 files are inherited without
replacement; exactly eight C4 files are appended.  The hardened publisher
provides owned-draft recovery, exact-union validation, anonymous full-byte
readback, zero-draft lineage audit, and credential-sanitized receipts.

``--contract-only`` is local, credential-free, network-free, browser-free, and
side-effect free.  It never reads the credential file.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import package_c140_companion_c4_release as packager
import publish_zenodo_c140_companion_c3 as c3pub


engine = c3pub.engine
ROOT = Path(__file__).resolve().parents[1]

BASE_RECORD_ID = "22161363"
BASE_RECORD_DOI = "10.5281/zenodo.22161363"
BASE_VERSION = "2026.08.29.c140-companion-c3"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
VERSION = "2026.08.29.c140-companion-c4"
TITLE = (
    "O006/C140 Statistika Matematis — STAT 415, Random, dan Pendamping "
    "Orisinal C4 (Bahasa Indonesia)"
)
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

TOKEN_FILE = (
    Path.home() / "Documents" / "Obsidian notes" / "New zenodo token.md"
)
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json"
PUBLICATION_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-29_C140_COMPANION_C4.json"
)
READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-29_C140_COMPANION_C4.json"
)
BASE_READBACK_RECEIPT = (
    ROOT / "00_control" / "ZENODO_BASE_READBACK_2026-08-29_C140_COMPANION_C4.json"
)
AUDIT_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-29_C140_COMPANION_C4.json"
)
DRAFT_MARKER = (
    ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-29_C140_COMPANION_C4.json"
)
LINEAGE_RECEIPT = (
    ROOT / "00_control" / "ZENODO_LINEAGE_2026-08-29_C140_COMPANION_C4.json"
)

PACKAGE_SCHEMA = "o006.c140.companion-c4-release-package.v1"
PUBLICATION_SCHEMA = "o006.c140.zenodo-c140-companion-c4-publication.v1"
MARKER_SCHEMA = "o006.c140.zenodo-c140-companion-c4-draft-marker.v1"
LINEAGE_SCHEMA = "o006.c140.zenodo-c140-companion-c4-lineage.v1"
BASE_READBACK_SCHEMA = "o006.c140.zenodo-base-readback-c140-companion-c4.v1"
USER_AGENT = "O006-C140-companion-c4/2026.08.29"
MAX_RELEASE_BYTES = 500_000_000

PACKAGE_RECEIPT_BYTES = 34_142
PACKAGE_RECEIPT_SHA256 = (
    "45c0fceb27af175689e5ee8ac92271d395a41cdf96c32621eacf8d60a8222f7f"
)
BASE_PACKAGE_RECEIPT_BYTES = 30_151
BASE_PACKAGE_RECEIPT_SHA256 = (
    "d78c911bdc2837a3fdddd3f71e6b7211fde46a8668d85a9c00f750cf82716637"
)
BASE_PUBLIC_READBACK_BYTES = 19_302
BASE_PUBLIC_READBACK_SHA256 = (
    "c53bd0827a06a25dd81bee46d8c6630ce4147f256f0605f089f16aa712a69bbf"
)
BASE_FILE_COUNT = 49
BASE_TOTAL_BYTES = 92_476_057
PUBLICATION_FILE_COUNT = 57
PUBLICATION_TOTAL_BYTES = 93_850_993

ADDED_SPECS = (
    (
        "05_C140_COMPANION_C4_OFFLINE_READER.zip",
        923_472,
        "92dd5d30f79f47351b1cfaeb2a05ff9b53ca1136e3c48bb6bd67f5481a960291",
    ),
    (
        "15_C140_COMPANION_C4_SOURCE_BACKEND.zip",
        367_946,
        "fe8c034a51f9c7a7acc0a764af70ebc4ed0e8e790c591003815abf1a3f723503",
    ),
    (
        "25_C140_COMPANION_C4_RELEASE_NOTES.md",
        1_472,
        "a468a26a8f9c1c9bd4245f757f54ba9dbc07f1fc45036bc5cf5e731414dfde1a",
    ),
    (
        "35_C140_COMPANION_C4_LICENSE.md",
        642,
        "f8913e62477ebb57d3370abb52469ac54292e2b2053db9a41fa3cb3cb02967f2",
    ),
    (
        "45_C140_COMPANION_C4_STATIC_QA_EVIDENCE.zip",
        34_431,
        "eac5ffe8f11b41ee4d6f375538d378169653c0c930dc085d618072e935b1d8ba",
    ),
    (
        "96_C140_COMPANION_C4_FULL_UNION_MANIFEST.csv",
        13_786,
        "3cc278085606d676946add43ba20010e007029ce7050b07f09b2d0265afdd773",
    ),
    (
        "SHA256SUMS_C140_COMPANION_C4.txt",
        6_012,
        "f1c002ac9afa6754f0ff21d217ca9bb7154121197062716afc9f79d10454af3c",
    ),
    (
        "97_C140_COMPANION_C4_FULL_UNION_ROOT_RECEIPT.json",
        27_175,
        "29c7117327743ae12982d69283917f61b53ace02c76d474e68c99af0f90d447e",
    ),
)
ADDED_NAMES = tuple(name for name, _size, _digest in ADDED_SPECS)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def base_specs() -> tuple[tuple[str, int, str], ...]:
    outputs, rows, readback = packager.validate_base_public_union()
    public = readback.get("public")
    if (
        packager.BASE_RECORD_ID != BASE_RECORD_ID
        or packager.BASE_RECORD_DOI != BASE_RECORD_DOI
        or packager.BASE_VERSION != BASE_VERSION
        or packager.CONCEPT_RECORD_ID != CONCEPT_RECORD_ID
        or packager.CONCEPT_DOI != CONCEPT_DOI
        or packager.BASE_PACKAGE_RECEIPT_BYTES != BASE_PACKAGE_RECEIPT_BYTES
        or packager.BASE_PACKAGE_RECEIPT_SHA256 != BASE_PACKAGE_RECEIPT_SHA256
        or packager.BASE_PUBLIC_READBACK_BYTES != BASE_PUBLIC_READBACK_BYTES
        or packager.BASE_PUBLIC_READBACK_SHA256 != BASE_PUBLIC_READBACK_SHA256
        or len(rows) != BASE_FILE_COUNT
        or sum(int(row["bytes"]) for row in rows) != BASE_TOTAL_BYTES
        or set(outputs) != {str(row["filename"]) for row in rows}
        or not isinstance(public, dict)
        or public.get("record_id") != BASE_RECORD_ID
        or public.get("doi") != BASE_RECORD_DOI
        or public.get("concept_record_id") != CONCEPT_RECORD_ID
        or public.get("concept_doi") != CONCEPT_DOI
        or public.get("version") != BASE_VERSION
        or public.get("anonymous_readback") is not True
        or public.get("file_count") != BASE_FILE_COUNT
        or public.get("total_bytes") != BASE_TOTAL_BYTES
    ):
        raise RuntimeError("pinned public C3 base differs")
    return tuple(
        (str(row["filename"]), int(row["bytes"]), str(row["sha256"]))
        for row in rows
    )


BASE_SPECS = base_specs()
EXPECTED_ORDER = tuple(name for name, _size, _digest in BASE_SPECS) + ADDED_NAMES


def validate_token_boundary() -> None:
    """Pin credential handling without reading or serializing the credential."""
    if engine.TOKEN_FILE != TOKEN_FILE:
        raise RuntimeError("hardened engine token-file boundary differs")
    required_hooks = (
        "read_token",
        "assert_receipt_safe",
        "owned_new_version",
        "validate_inherited_and_partial_additions",
        "upload_missing_additions",
        "exact_complete_draft",
        "anonymous_readback",
        "authenticated_zero_draft_audit",
    )
    if any(not callable(getattr(engine, name, None)) for name in required_hooks):
        raise RuntimeError("hardened engine credential/sanitization hooks are absent")
    engine.assert_receipt_safe(
        {
            "credential_access": False,
            "credential_value_persisted": False,
            "token_file_path_persisted": False,
        }
    )
    try:
        engine.assert_receipt_safe({"forbidden_path": TOKEN_FILE.as_posix()})
    except RuntimeError:
        pass
    else:
        raise RuntimeError("hardened receipt sanitizer accepted the token-file path")


def validate_metadata_boundary() -> None:
    value = metadata()
    description = value.get("description")
    required_rights = (
        "CC BY-NC 4.0",
        "CC BY 2.0",
        "CC BY 1.0",
        "CC BY-SA 4.0",
        "Apache-2.0",
    )
    if (
        value.get("version") != VERSION
        or value.get("access_right") != "open"
        or value.get("license") != "other-open"
        or value.get("language") != "ind"
        or not isinstance(description, str)
        or "C140 secara keseluruhan belum lengkap" not in description
        or any(right not in description for right in required_rights)
    ):
        raise RuntimeError("C4 public metadata/license boundary differs")
    engine.assert_receipt_safe(value)


def computed_contract() -> tuple[
    dict[str, bytes], bytes, dict[str, Any], list[dict[str, Any]]
]:
    validate_token_boundary()
    validate_metadata_boundary()
    outputs, receipt_payload = packager.compute()
    package = json.loads(receipt_payload)
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    coverage = package.get("coverage")
    lineage = package.get("lineage")
    preservation = package.get("preservation")
    reader_order = package.get("reader_order")
    rights = package.get("rights")
    packager_gate = package.get("packager")
    base = package.get("base_public_union")
    if (
        len(receipt_payload) != PACKAGE_RECEIPT_BYTES
        or sha256(receipt_payload) != PACKAGE_RECEIPT_SHA256
        or package.get("schema") != PACKAGE_SCHEMA
        or package.get("version") != VERSION
        or package.get("status") != "ready"
        or not isinstance(publication, dict)
        or not isinstance(rows, list)
        or not all(isinstance(row, dict) for row in rows)
        or publication.get("file_count") != PUBLICATION_FILE_COUNT
        or publication.get("bytes") != PUBLICATION_TOTAL_BYTES
        or len(rows) != PUBLICATION_FILE_COUNT
        or tuple(str(row.get("filename")) for row in rows) != EXPECTED_ORDER
        or coverage
        != {
            "c140_course": "incomplete",
            "c140_original_companion": "C4 coherent partial checkpoint complete",
            "c4_batch": "complete",
            "penn_state_spine": "complete",
            "random_completeness_donor": "complete",
            "remaining": "CA02-CA04 and two capstones",
        }
        or lineage
        != {
            "base_record_doi": BASE_RECORD_DOI,
            "base_record_id": BASE_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "concept_record_id": CONCEPT_RECORD_ID,
            "create_competing_concept": False,
        }
        or preservation
        != {
            "inherited_files_byte_identical": True,
            "inherited_file_count": BASE_FILE_COUNT,
            "new_file_count": len(ADDED_SPECS),
            "new_substantive_file_count": 5,
        }
        or reader_order
        != {
            "inherited_union_first": True,
            "pdf_upload_order": 1,
            "epub_upload_order": 2,
            "c4_first_upload_order": BASE_FILE_COUNT + 1,
        }
        or not isinstance(rights, dict)
        or rights.get("aggregate_uniform_relicense") is not False
        or rights.get("component_licenses_unchanged") is not True
        or rights.get("platform_license") != "other-open"
        or not isinstance(packager_gate, dict)
        or packager_gate.get("browser_processes_used") is not False
        or packager_gate.get("credential_access") is not False
        or packager_gate.get("git_operations") is not False
        or packager_gate.get("network_access") is not False
        or packager_gate.get("publication_side_effects") is not False
        or not isinstance(base, dict)
        or base.get("record_id") != BASE_RECORD_ID
        or base.get("record_doi") != BASE_RECORD_DOI
        or base.get("version") != BASE_VERSION
        or base.get("concept_record_id") != CONCEPT_RECORD_ID
        or base.get("concept_doi") != CONCEPT_DOI
        or base.get("file_count") != BASE_FILE_COUNT
        or base.get("bytes") != BASE_TOTAL_BYTES
        or base.get("anonymous_readback") is not True
        or base.get("package_receipt")
        != {
            "bytes": BASE_PACKAGE_RECEIPT_BYTES,
            "sha256": BASE_PACKAGE_RECEIPT_SHA256,
        }
        or base.get("public_readback")
        != {
            "bytes": BASE_PUBLIC_READBACK_BYTES,
            "sha256": BASE_PUBLIC_READBACK_SHA256,
        }
    ):
        raise RuntimeError("computed C4 package is not the admitted Zenodo boundary")

    names: set[str] = set()
    paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        name = row.get("filename")
        relative = engine.canonical_relative(
            row.get("source_path"), f"C4 package row {index} path"
        )
        size, digest = engine.checked_identity(row, f"C4 package row {index}")
        payload = outputs.get(str(name))
        if (
            row.get("upload_order") != index + 1
            or not isinstance(name, str)
            or name != EXPECTED_ORDER[index]
            or not engine._SAFE_NAME.fullmatch(name)
            or engine._SENSITIVE_NAME.search(name)
            or relative != f"release/{name}"
            or row.get("primary_reader") is not (index == 0)
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or not isinstance(row.get("lineage"), str)
            or not row.get("lineage")
            or not isinstance(row.get("media_type"), str)
            or "/" not in str(row.get("media_type"))
            or name in names
            or relative in paths
            or payload is None
            or (len(payload), sha256(payload)) != (size, digest)
        ):
            raise RuntimeError(f"C4 package row {index} has an unsafe identity")
        names.add(name)
        paths.add(relative)
        total += size
    if total != PUBLICATION_TOTAL_BYTES or tuple(outputs) != EXPECTED_ORDER:
        raise RuntimeError("C4 package aggregate/order differs")

    for index, expected in enumerate(BASE_SPECS):
        row = rows[index]
        actual = (row.get("filename"), row.get("bytes"), row.get("sha256"))
        if actual != expected:
            raise RuntimeError(f"C4 package changed inherited base asset: {expected[0]}")
    for offset, expected in enumerate(ADDED_SPECS, start=BASE_FILE_COUNT):
        row = rows[offset]
        actual = (row.get("filename"), row.get("bytes"), row.get("sha256"))
        if actual != expected:
            raise RuntimeError(f"C4 package addition identity differs: {expected[0]}")
    if (
        rows[0].get("filename")
        != "00_00_stat415-pengantar-statistika-matematis-id.pdf"
        or rows[0].get("media_type") != "application/pdf"
        or rows[1].get("filename")
        != "00_01_stat415-pengantar-statistika-matematis-id.epub"
        or rows[1].get("media_type") != "application/epub+zip"
    ):
        raise RuntimeError("C4 union is not reader-first")
    return outputs, receipt_payload, package, rows


def snapshot() -> engine.ReleaseSnapshot:
    outputs, receipt_payload, package, rows = computed_contract()
    if (
        not PACKAGE_RECEIPT.is_file()
        or PACKAGE_RECEIPT.read_bytes() != receipt_payload
    ):
        raise RuntimeError("written C4 package receipt differs; run packager --write")
    artifacts: list[engine.Artifact] = []
    total = 0
    for index, row in enumerate(rows):
        name = str(row["filename"])
        relative = engine.canonical_relative(
            row.get("source_path"), f"C4 package row {index} path"
        )
        size, digest = engine.checked_identity(row, f"C4 package row {index}")
        payload = engine.read_confined(relative, f"C4 release asset {name}")
        if payload != outputs[name] or (len(payload), sha256(payload)) != (
            size,
            digest,
        ):
            raise RuntimeError(f"C4 release asset differs: {name}")
        artifacts.append(engine.Artifact(name, relative, size, digest, payload))
        total += size
    if total != PUBLICATION_TOTAL_BYTES or total > MAX_RELEASE_BYTES:
        raise RuntimeError("C4 release aggregate byte count differs")
    inherited = tuple(artifacts[:BASE_FILE_COUNT])
    additions = tuple(artifacts[BASE_FILE_COUNT:])
    if (
        tuple(item.name for item in inherited)
        != tuple(name for name, _size, _digest in BASE_SPECS)
        or tuple(item.name for item in additions) != ADDED_NAMES
    ):
        raise RuntimeError("C4 inherited/addition partition differs")
    return engine.ReleaseSnapshot(
        package=package,
        receipt_bytes=len(receipt_payload),
        receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited=inherited,
        additions=additions,
    )


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-29",
        "description": (
            "Rilis kumulatif O006/C140 Bahasa Indonesia (id-ID). Versi ini "
            "mewarisi byte demi byte seluruh 49 berkas publik versi "
            "2026.08.29.c140-companion-c3, lalu menambahkan tepat delapan "
            "berkas checkpoint C4. Batch C4 melengkapi MS00–MS06: tinjauan "
            "peluang dan distribusi; statistik urutan; estimasi, bias, dan MSE; "
            "kecukupan dan faktorisasi; metode momen dan likelihood; informasi "
            "Fisher, selang kepercayaan, bootstrap, dan metode delta; serta "
            "pengujian eksak, power, p-value, dan uji Wald–score–LR. Setiap "
            "set memiliki delapan masalah nontrivial dengan petunjuk bertahap, "
            "jawaban singkat, dan solusi lengkap. Pendamping kumulatif kini "
            "memiliki 34 dokumen, enam simulasi berseed, dan 114 masalah "
            "berjawaban lengkap. Ini adalah "
            "checkpoint parsial yang koheren; C140 secara keseluruhan belum "
            "lengkap karena CA02–CA04 dan dua capstone masih harus "
            "diselesaikan. Hak komponen tidak "
            "diseragamkan: Penn State tetap CC BY-NC 4.0 kecuali dinyatakan "
            "lain; halaman Random mempertahankan saksi CC BY 2.0 pada laman "
            "utama dan tautan CC BY 1.0 pada Credits; pendamping orisinal adalah "
            "CC BY-SA 4.0; MathJax tetap Apache-2.0. Metadata agregat karena itu "
            "memakai other-open. Provenans produksi pendamping dan rekayasa "
            f"edisi: {MODEL_PROVENANCE}. Seluruh kredit sumber dipertahankan; "
            "tidak ada dukungan Penn State atau Kyle Siegrist yang tersirat."
        ),
        "creators": [
            {"name": "Penn State Department of Statistics"},
            {"name": "Siegrist, Kyle"},
            {"name": "OpenAI Codex"},
        ],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia",
            "id-ID",
            "mathematical statistics",
            "statistika matematis",
            "probability distributions",
            "order statistics",
            "estimation bias MSE",
            "sufficiency factorization",
            "method of moments",
            "maximum likelihood",
            "Fisher information",
            "confidence intervals",
            "bootstrap delta method",
            "hypothesis testing",
            "power p-value",
            "Wald score likelihood-ratio tests",
            "reproducible simulation",
            "mastery assessment",
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
                "identifier": "10.5281/zenodo.22076539",
                "relation": "isSupplementedBy",
                "resource_type": "publication-book",
                "scheme": "doi",
            },
            {
                "identifier": "https://github.com/KokunoYumeto/penn-state-stat-415-id",
                "relation": "isSupplementedBy",
                "resource_type": "software",
                "scheme": "url",
            },
        ],
    }


def verify_base_record(
    session: engine.requests.Session, snap: engine.ReleaseSnapshot
) -> dict[str, object]:
    record = engine.public_record(session, BASE_RECORD_ID)
    metadata_value = record.get("metadata")
    if (
        not isinstance(metadata_value, dict)
        or metadata_value.get("version") != BASE_VERSION
        or str(record.get("doi")) != BASE_RECORD_DOI
    ):
        raise RuntimeError("public C3 base record identity differs")
    verified = engine.download_exact(session, record, snap.inherited)
    result = {
        "record_id": BASE_RECORD_ID,
        "doi": BASE_RECORD_DOI,
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "version": BASE_VERSION,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "package_receipt": {
            "bytes": BASE_PACKAGE_RECEIPT_BYTES,
            "sha256": BASE_PACKAGE_RECEIPT_SHA256,
        },
        "prior_public_readback": {
            "bytes": BASE_PUBLIC_READBACK_BYTES,
            "sha256": BASE_PUBLIC_READBACK_SHA256,
        },
        "anonymous_readback": True,
        "environment_proxy_trust": False,
    }
    if (
        result["file_count"] != BASE_FILE_COUNT
        or result["total_bytes"] != BASE_TOTAL_BYTES
    ):
        raise RuntimeError("public C3 base byte census differs")
    engine.atomic_json(
        BASE_READBACK_RECEIPT,
        {
            "schema": BASE_READBACK_SCHEMA,
            "target_version": VERSION,
            "package_receipt_sha256": snap.receipt_sha256,
            "credential_access": False,
            "public_base": result,
        },
    )
    return result


def write_public_receipts(
    base: dict[str, object],
    public: dict[str, object],
    mode: str,
    **extra: object,
) -> None:
    engine.atomic_json(
        READBACK_RECEIPT,
        {
            **base,
            "mode": "verify-published",
            "credential_access": False,
            "environment_proxy_trust": False,
            "public": public,
        },
    )
    engine.atomic_json(
        PUBLICATION_RECEIPT,
        {
            **base,
            "mode": mode,
            "credential_access": mode != "verify-published",
            "public": public,
            **extra,
        },
    )
    engine.atomic_json(
        LINEAGE_RECEIPT,
        {
            "schema": LINEAGE_SCHEMA,
            "record_id": public["record_id"],
            "doi": public["doi"],
            "concept_record_id": CONCEPT_RECORD_ID,
            "concept_doi": CONCEPT_DOI,
            "url": public["url"],
            "version": VERSION,
        },
    )


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt_payload, package, rows = computed_contract()
    return {
        "appended_files": len(ADDED_SPECS),
        "base_package_receipt_sha256": BASE_PACKAGE_RECEIPT_SHA256,
        "base_public_readback_sha256": BASE_PUBLIC_READBACK_SHA256,
        "base_record_id": BASE_RECORD_ID,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "concept_record_id": CONCEPT_RECORD_ID,
        "credential_access": False,
        "credential_value_persisted": False,
        "files": len(rows),
        "inherited_files": len(BASE_SPECS),
        "mode": "contract-only",
        "network_access": False,
        "package_receipt_bytes": len(receipt_payload),
        "package_receipt_sha256": sha256(receipt_payload),
        "publication_side_effects": False,
        "reader_first": True,
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
        "token_file_accessed": False,
        "token_file_path_persisted": False,
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
    engine.TOKEN_FILE = TOKEN_FILE
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
    engine.ADDED_NAMES = ADDED_NAMES
    engine.EXPECTED_ORDER = EXPECTED_ORDER
    engine.snapshot = snapshot
    engine.metadata = metadata
    engine.verify_base_record = verify_base_record
    engine.write_public_receipts = write_public_receipts


def main() -> None:
    if sys.argv[1:] == ["--contract-only"]:
        print(json.dumps(local_contract_summary(), sort_keys=True))
        return
    configure_engine()
    engine.main()


if __name__ == "__main__":
    main()
