#!/usr/bin/env python3
"""Publish the cumulative C140 original-companion C2 Zenodo boundary.

The adapter creates a new version only from public C1 record 22148810 in the
existing concept 22077422.  Its 33 files are inherited unchanged; only eight
C2 files are uploaded. ``--contract-only`` is local, credential-free,
network-free, browser-free, and side-effect free.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

import package_c140_companion_c2_release as packager
import publish_zenodo_c140_companion_c1 as c1


engine = c1._engine
ROOT = Path(__file__).resolve().parents[1]
BASE_RECORD_ID = "22148810"
BASE_VERSION = "2026.08.28.c140-companion-c1"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"
VERSION = "2026.08.29.c140-companion-c2"
TITLE = "O006/C140 Statistika Matematis — STAT 415, Random, dan Pendamping Orisinal C2 (Bahasa Indonesia)"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"

PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C2_RELEASE_PACKAGE_RECEIPT.json"
PUBLICATION_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-29_C140_COMPANION_C2.json"
READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-29_C140_COMPANION_C2.json"
BASE_READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_BASE_READBACK_2026-08-29_C140_COMPANION_C2.json"
AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-29_C140_COMPANION_C2.json"
DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-29_C140_COMPANION_C2.json"
LINEAGE_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_2026-08-29_C140_COMPANION_C2.json"

PACKAGE_SCHEMA = "o006.c140.companion-c2-release-package.v1"
PUBLICATION_SCHEMA = "o006.c140.zenodo-c140-companion-c2-publication.v1"
MARKER_SCHEMA = "o006.c140.zenodo-c140-companion-c2-draft-marker.v1"
LINEAGE_SCHEMA = "o006.c140.zenodo-c140-companion-c2-lineage.v1"
BASE_READBACK_SCHEMA = "o006.c140.zenodo-base-readback-c140-companion-c2.v1"
USER_AGENT = "O006-C140-companion-c2/2026.08.29"
MAX_RELEASE_BYTES = 500_000_000

ADDED_NAMES = (
    packager.OFFLINE_NAME,
    packager.SOURCE_NAME,
    packager.NOTES_NAME,
    packager.LICENSE_NAME,
    packager.QA_NAME,
    packager.MANIFEST_NAME,
    packager.CHECKSUM_NAME,
    packager.ROOT_NAME,
)


def base_specs() -> tuple[tuple[str, int, str], ...]:
    _prior, rows = packager.validate_prior()
    return tuple((str(row["filename"]), int(row["bytes"]), str(row["sha256"])) for row in rows)


BASE_SPECS = base_specs()
EXPECTED_ORDER = tuple(row[0] for row in BASE_SPECS) + ADDED_NAMES


def computed_contract() -> tuple[dict[str, bytes], bytes, dict[str, object], list[dict[str, object]]]:
    outputs, receipt_payload = packager.compute()
    package = json.loads(receipt_payload)
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or not isinstance(rows, list)
        or publication.get("file_count") != len(EXPECTED_ORDER)
        or tuple(row.get("filename") for row in rows if isinstance(row, dict)) != EXPECTED_ORDER
        or package.get("coverage") != {
            "c140_course": "incomplete",
            "c140_original_companion": "C2 coherent partial checkpoint complete",
            "penn_state_spine": "complete",
            "random_completeness_donor": "complete",
        }
        or package.get("rights") != {"aggregate_uniform_relicense": False, "platform_license": "other-open"}
        or package.get("lineage") != {
            "base_record_doi": "10.5281/zenodo.22148810",
            "base_record_id": "22148810",
            "concept_doi": CONCEPT_DOI,
            "create_competing_concept": False,
        }
    ):
        raise RuntimeError("computed C2 package is not the admitted Zenodo boundary")
    for index, (name, size, digest) in enumerate(BASE_SPECS):
        row = rows[index]
        if (row.get("filename"), row.get("bytes"), row.get("sha256")) != (name, size, digest):
            raise RuntimeError(f"computed package changed inherited C1 asset: {name}")
    for name in ADDED_NAMES:
        row = rows[EXPECTED_ORDER.index(name)]
        payload = outputs.get(name)
        if payload is None or len(payload) != row.get("bytes") or engine.sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"computed C2 addition identity differs: {name}")
    return outputs, receipt_payload, package, rows


def snapshot() -> engine.ReleaseSnapshot:
    outputs, receipt_payload, package, rows = computed_contract()
    if not PACKAGE_RECEIPT.is_file() or PACKAGE_RECEIPT.read_bytes() != receipt_payload:
        raise RuntimeError("written C2 package receipt is missing or differs; run the C2 packager --write")
    artifacts: list[engine.Artifact] = []
    names: set[str] = set()
    paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"C2 package row {index} is malformed")
        name = row.get("filename")
        relative = engine.canonical_relative(row.get("source_path"), f"C2 package row {index} path")
        declared_size, declared_sha = engine.checked_identity(row, f"C2 package row {index}")
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_ORDER[index]
            or not isinstance(name, str)
            or not engine._SAFE_NAME.fullmatch(name)
            or engine._SENSITIVE_NAME.search(name)
            or relative != f"release/{name}"
            or row.get("primary_reader") is not (index == 0)
            or name in names
            or relative in paths
        ):
            raise RuntimeError(f"C2 package row {index} has an unsafe identity or path")
        payload = engine.read_confined(relative, f"C2 release asset {name}")
        if payload != outputs[name] or (len(payload), engine.sha256(payload)) != (declared_size, declared_sha):
            raise RuntimeError(f"C2 release asset differs from package receipt: {name}")
        total += len(payload)
        if total > MAX_RELEASE_BYTES:
            raise RuntimeError("C2 release payload exceeds the 500 MB boundary")
        artifacts.append(engine.Artifact(name, relative, len(payload), declared_sha, payload))
        names.add(name)
        paths.add(relative)
    if package["publication_inventory"]["bytes"] != total:
        raise RuntimeError("C2 package aggregate byte count differs")
    inherited_count = len(BASE_SPECS)
    return engine.ReleaseSnapshot(
        package=package,
        receipt_bytes=len(receipt_payload),
        receipt_sha256=engine.sha256(receipt_payload),
        files=tuple(artifacts),
        inherited=tuple(artifacts[:inherited_count]),
        additions=tuple(artifacts[inherited_count:]),
    )


def metadata() -> dict[str, object]:
    return {
        "title": TITLE,
        "upload_type": "publication",
        "publication_type": "book",
        "publication_date": "2026-08-29",
        "description": (
            "Rilis kumulatif O006/C140 Bahasa Indonesia (id-ID). Versi ini "
            "mewarisi byte demi byte seluruh 33 berkas versi "
            "2026.08.28.c140-companion-c1—tulang punggung Penn State STAT 415 "
            "lengkap, donor kelengkapan Random lengkap, dan checkpoint pendamping "
            "C1—lalu menambahkan tepat delapan berkas checkpoint C2. C2 menutup "
            "jembatan model linear Gaussian matriks melalui D008–D011, SIM005, "
            "dan MS12: geometri proyeksi desain tetap, OLS dan MLE Gaussian, "
            "Gauss–Markov, hukum sampling eksak, inferensi t/F, selang kepercayaan "
            "dan prediksi, ANOVA, diagnostik, leverage, pengaruh, misspecification, "
            "dan heteroskedastisitas. Pendamping kumulatif kini memiliki 23 dokumen, "
            "lima simulasi berseed, lima set penguasaan, dan satu asesmen kumulatif "
            "dengan total 50 soal serta solusi lengkap. C140 secara keseluruhan "
            "belum lengkap: perbandingan Bayesian–frequentist, set penguasaan, "
            "asesmen, dan capstone lanjutan masih harus diselesaikan. Hak komponen "
            "tidak diseragamkan: Penn State tetap CC BY-NC 4.0 kecuali dinyatakan "
            "lain; halaman Random mempertahankan saksi CC BY 2.0 pada laman utama "
            "dan tautan CC BY 1.0 pada Credits; pendamping orisinal adalah CC BY-SA "
            "4.0; MathJax tetap Apache-2.0. Metadata agregat karena itu memakai "
            "other-open. Provenans produksi pendamping dan rekayasa edisi: "
            f"{MODEL_PROVENANCE}. Seluruh kredit sumber dipertahankan; tidak ada "
            "dukungan Penn State atau Kyle Siegrist yang tersirat."
        ),
        "creators": [
            {"name": "Penn State Department of Statistics"},
            {"name": "Siegrist, Kyle"},
            {"name": "OpenAI Codex"},
        ],
        "access_right": "open",
        "license": "other-open",
        "keywords": [
            "Bahasa Indonesia", "id-ID", "mathematical statistics", "statistika matematis",
            "matrix Gaussian linear model", "fixed-design regression", "ordinary least squares",
            "Gauss-Markov theorem", "t test", "F test", "ANOVA", "prediction interval",
            "regression diagnostics", "heteroskedasticity", "reproducible simulation",
            "mastery assessment", "Penn State STAT 415", "Random", "open educational resources",
            "offline HTML", "PDF", "EPUB", "machine-readable curriculum", "AI translation",
            "component-separated licensing",
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


def verify_base_record(session: engine.requests.Session, snap: engine.ReleaseSnapshot) -> dict[str, object]:
    record = engine.public_record(session, BASE_RECORD_ID)
    if record.get("metadata", {}).get("version") != BASE_VERSION:
        raise RuntimeError("public C2 base record has the wrong version")
    verified = engine.download_exact(session, record, snap.inherited)
    doi = str(record.get("doi", ""))
    if doi != f"10.5281/zenodo.{BASE_RECORD_ID}":
        raise RuntimeError("public C2 base record DOI is unexpected")
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
    engine.atomic_json(BASE_READBACK_RECEIPT, {
        "schema": BASE_READBACK_SCHEMA,
        "target_version": VERSION,
        "package_receipt_sha256": snap.receipt_sha256,
        "credential_access": False,
        "public_base": result,
    })
    return result


def write_public_receipts(base: dict[str, object], public: dict[str, object], mode: str, **extra: object) -> None:
    engine.atomic_json(READBACK_RECEIPT, {
        **base,
        "mode": "verify-published",
        "credential_access": False,
        "environment_proxy_trust": False,
        "public": public,
    })
    engine.atomic_json(PUBLICATION_RECEIPT, {
        **base,
        "mode": mode,
        "credential_access": mode != "verify-published",
        "public": public,
        **extra,
    })
    engine.atomic_json(LINEAGE_RECEIPT, {
        "schema": LINEAGE_SCHEMA,
        "record_id": public["record_id"],
        "doi": public["doi"],
        "concept_record_id": CONCEPT_RECORD_ID,
        "concept_doi": CONCEPT_DOI,
        "url": public["url"],
        "version": VERSION,
    })


def local_contract_summary() -> dict[str, object]:
    _outputs, receipt_payload, package, rows = computed_contract()
    return {
        "base_record_id": BASE_RECORD_ID,
        "browser_processes_used": False,
        "bytes": package["publication_inventory"]["bytes"],
        "concept_record_id": CONCEPT_RECORD_ID,
        "credential_access": False,
        "files": len(rows),
        "inherited_files": len(BASE_SPECS),
        "mode": "contract-only",
        "network_access": False,
        "new_files_to_upload": len(ADDED_NAMES),
        "package_receipt_sha256": engine.sha256(receipt_payload),
        "schema": PACKAGE_SCHEMA,
        "status": "pass",
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
