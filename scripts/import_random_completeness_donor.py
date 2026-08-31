#!/usr/bin/env python3
"""Vendor the exact Random completeness donor from the completed sibling edition.

The importer preserves the canonical authority and id-ID bytes, extracts only
the donor's stable backend rows, and writes no machine-local path into the
component.  The completed sibling repository is an import source, not a runtime
dependency of the resulting component.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import tempfile
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "random-completeness"
SOURCE_PATH = "random/point/Sufficient.html"
ORIGIN_REPOSITORY = "https://github.com/KokunoYumeto/mathematical-statistics-id"
ORIGIN_COMMIT = "f2aab7b9a0578dd76624e183fc47e3c1faa664e8"
SCHEMA = "o006.c140.random-completeness.import.v1"


COPY_SPECS = (
    (
        "authority/upstream/random/point/Sufficient.html",
        "authority/upstream/random/point/Sufficient.html",
        57_507,
        "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4",
    ),
    (
        "authority/upstream/random/index.html",
        "authority/witness/random/index.html",
        22_462,
        "a26f07b700c9de8c7ce83e5a2f38e1e676ed5b085fec8c4a52bb44abefaa8ba8",
    ),
    (
        "authority/upstream/random/Credits.html",
        "authority/witness/random/Credits.html",
        6_467,
        "2d28d0293b41b71d08a531d37399205f657fbed77592c8f7acd54bf2a54113bf",
    ),
    (
        "authority/upstream/random/Screen.css",
        "authority/upstream/random/Screen.css",
        5_433,
        "589035811781debb33e3aa90ca0f376532b8ade30d54fad5c56838bec5c8d707",
    ),
    (
        "authority/upstream/random/Basic.js",
        "authority/upstream/random/Basic.js",
        935,
        "006372877a2b384e20c3e1a364ddde4791890ad02020f654c22372206891b00b",
    ),
    (
        "authority/upstream/random/icons/Icon.svg",
        "authority/upstream/random/icons/Icon.svg",
        373,
        "09ccb2c9f9c50cd4d7a1c867fa112534afa56a12ef0f8a96a0d682ec6b8a9d8b",
    ),
    (
        "authority/upstream/random/icons/Plus.svg",
        "authority/upstream/random/icons/Plus.svg",
        291,
        "1bd78cdc7997d6237bc809cef5f36e074c551ec3224b226c38735be898bc439a",
    ),
    (
        "authority/upstream/random/icons/Minus.svg",
        "authority/upstream/random/icons/Minus.svg",
        223,
        "a55a72ce346d0fe73318fecfa994c7fda8766694a448c3b968122df7a916d7fc",
    ),
    (
        "authority/upstream/MathJax/tex-svg.js",
        "authority/upstream/MathJax/tex-svg.js",
        1_704_911,
        "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a",
    ),
    (
        "build/html-id/MathJax/input/tex/extensions/boldsymbol.js",
        "authority/runtime/MathJax-3.1.2/input/tex/extensions/boldsymbol.js",
        4_709,
        "716cf8735d00abfb1627f8adbbf4aeb915ac9b5c55d47aeaf276e73dac6a2aa1",
    ),
    (
        "build/html-id/licenses/MathJax-3.1.2-LICENSE.txt",
        "authority/runtime/MathJax-3.1.2/LICENSE.txt",
        11_358,
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    ),
    (
        "authority/runtime/MathJax-3.1.2/RUNTIME_RECEIPT.json",
        "provenance/sibling/MathJax-3.1.2-RUNTIME_RECEIPT.json",
        901,
        "9668ae41d64447438b777739e92844ce194783932496e63fcb016c58b157a3fe",
    ),
    (
        "source/id-ID/random/point/Sufficient.html",
        "source/id-ID/random/point/Sufficient.html",
        60_900,
        "18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197",
    ),
    (
        "scripts/localize_sufficient.py",
        "provenance/sibling/localize_sufficient.py",
        60_543,
        "87c161233cb0b4bd5c0212de683d9934d80d66aaa1bc755cc9a145a0c3a9ba43",
    ),
    (
        "00_control/SOURCE_AUTHORITY.json",
        "provenance/sibling/SOURCE_AUTHORITY.json",
        3_387,
        "3e307d3a09c029ec488fdede9de4ac093e660b2a74001921696db75c4662b936",
    ),
    (
        "00_control/RIGHTS_AND_COMPONENTS.md",
        "provenance/sibling/RIGHTS_AND_COMPONENTS.md",
        1_438,
        "0b23e73e23b28bad42bf769ec16a83a5ce418a64ff851e51565939c3856f1b39",
    ),
    (
        "LICENSE.md",
        "provenance/sibling/LICENSE.md",
        2_162,
        "1cd59cc44cb5c7cbf1a171d8920f6346b6577b7e2057e059c08258117e56565d",
    ),
    (
        "00_control/TERMINOLOGY_GLOSSARY_ID_ID.csv",
        "backend/TERMINOLOGY_GLOSSARY_ID_ID.csv",
        7_334,
        "cd7a10378ea4ce3ec9e9993812f751e475a8661ec6b9ca40a535769769153db7",
    ),
)


AUTHORITY_ROWS = (
    (
        "authority/upstream/random/point/Sufficient.html",
        "authority",
        "https://www.randomservices.org/random/point/Sufficient.html",
        57_507,
        "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4",
        "Fri, 13 Mar 2026 16:38:20 GMT",
        '"e0a3-69b43d7c-721ef416796205b5;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/witness/random/index.html",
        "rights-witness",
        "https://www.randomservices.org/random/index.html",
        22_462,
        "a26f07b700c9de8c7ce83e5a2f38e1e676ed5b085fec8c4a52bb44abefaa8ba8",
        "Fri, 13 Mar 2026 16:27:20 GMT",
        '"57be-69b43ae8-897d0fc6cf830c74;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/witness/random/Credits.html",
        "rights-witness",
        "https://www.randomservices.org/random/Credits.html",
        6_467,
        "2d28d0293b41b71d08a531d37399205f657fbed77592c8f7acd54bf2a54113bf",
        "Fri, 13 Mar 2026 20:03:52 GMT",
        '"1943-69b46da8-7813466702ad358;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/upstream/random/Screen.css",
        "asset",
        "https://www.randomservices.org/random/Screen.css",
        5_433,
        "589035811781debb33e3aa90ca0f376532b8ade30d54fad5c56838bec5c8d707",
        "Fri, 13 Mar 2026 16:27:20 GMT",
        '"1539-69b43ae8-f959d9a730bcc355;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/upstream/random/Basic.js",
        "asset",
        "https://www.randomservices.org/random/Basic.js",
        935,
        "006372877a2b384e20c3e1a364ddde4791890ad02020f654c22372206891b00b",
        "Fri, 13 Mar 2026 16:27:20 GMT",
        '"3a7-69b43ae8-72b07f6b8ff60c95;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/upstream/random/icons/Icon.svg",
        "asset",
        "https://www.randomservices.org/random/icons/Icon.svg",
        373,
        "09ccb2c9f9c50cd4d7a1c867fa112534afa56a12ef0f8a96a0d682ec6b8a9d8b",
        "Fri, 13 Mar 2026 16:36:27 GMT",
        '"175-69b43d0b-ef7e72258da55a39;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/upstream/random/icons/Plus.svg",
        "asset",
        "https://www.randomservices.org/random/icons/Plus.svg",
        291,
        "1bd78cdc7997d6237bc809cef5f36e074c551ec3224b226c38735be898bc439a",
        "Fri, 13 Mar 2026 16:36:27 GMT",
        '"123-69b43d0b-847e4398f23a9eee;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/upstream/random/icons/Minus.svg",
        "asset",
        "https://www.randomservices.org/random/icons/Minus.svg",
        223,
        "a55a72ce346d0fe73318fecfa994c7fda8766694a448c3b968122df7a916d7fc",
        "Fri, 13 Mar 2026 16:36:27 GMT",
        '"df-69b43d0b-4ed37e25e0370a27;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/upstream/MathJax/tex-svg.js",
        "runtime",
        "https://www.randomservices.org/MathJax/tex-svg.js",
        1_704_911,
        "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a",
        "Fri, 13 Mar 2026 16:51:33 GMT",
        '"1a03cf-69b44095-d1c9dbbc04e43965;;;"',
        "live-reverified-2026-08-28",
    ),
    (
        "authority/runtime/MathJax-3.1.2/input/tex/extensions/boldsymbol.js",
        "runtime",
        "https://raw.githubusercontent.com/mathjax/MathJax/3.1.2/es5/input/tex/extensions/boldsymbol.js",
        4_709,
        "716cf8735d00abfb1627f8adbbf4aeb915ac9b5c55d47aeaf276e73dac6a2aa1",
        "",
        "",
        "official-tag-live-reverified-2026-08-28",
    ),
    (
        "authority/runtime/MathJax-3.1.2/LICENSE.txt",
        "license",
        "https://github.com/mathjax/MathJax-src/blob/3.1.2/LICENSE",
        11_358,
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        "",
        "",
        "sibling-freeze",
    ),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def canonical_csv(header: Iterable[str], rows: Iterable[Iterable[object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(list(header))
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def checked_bytes(path: Path, expected_bytes: int, expected_sha256: str) -> bytes:
    payload = path.read_bytes()
    if len(payload) != expected_bytes or sha256(payload) != expected_sha256:
        raise RuntimeError(f"import source identity differs: {path.as_posix()}")
    return payload


def filter_jsonl(path: Path, predicate) -> tuple[bytes, int]:
    kept: list[bytes] = []
    for raw in path.read_bytes().splitlines():
        value = json.loads(raw.decode("utf-8"))
        if predicate(value):
            kept.append(raw)
    return b"\n".join(kept) + b"\n", len(kept)


def filter_csv(path: Path, predicate) -> tuple[bytes, int]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise RuntimeError(f"CSV has no header: {path.as_posix()}")
        rows = [row for row in reader if predicate(row)]
        header = reader.fieldnames
    return canonical_csv(header, ([row[key] for key in header] for row in rows)), len(rows)


def desired_outputs(sibling: Path) -> tuple[dict[str, bytes], dict[str, int]]:
    outputs: dict[str, bytes] = {}
    for source_rel, target_rel, size, digest in COPY_SPECS:
        outputs[target_rel] = checked_bytes(sibling / source_rel, size, digest)

    entities, entity_count = filter_jsonl(
        sibling / "backend/entities.jsonl", lambda row: row.get("source_path") == SOURCE_PATH
    )
    relations, relation_count = filter_csv(
        sibling / "backend/relations.csv", lambda row: row.get("source_path") == SOURCE_PATH
    )
    adverse, adverse_count = filter_jsonl(
        sibling / "00_control/ADVERSE_LEDGER.jsonl",
        lambda row: SOURCE_PATH in json.dumps(row, ensure_ascii=False),
    )
    ledger, ledger_count = filter_csv(
        sibling / "00_control/TRANSLATION_LEDGER.csv",
        lambda row: row.get("source_path") == SOURCE_PATH,
    )
    if (entity_count, relation_count, adverse_count, ledger_count) != (325, 474, 19, 1):
        raise RuntimeError(
            "donor subset counts differ: "
            f"entities={entity_count}, relations={relation_count}, "
            f"adverse={adverse_count}, ledger={ledger_count}"
        )
    outputs["backend/entities.jsonl"] = entities
    outputs["backend/relations.csv"] = relations
    outputs["backend/adverse_records.jsonl"] = adverse
    outputs["backend/translation_ledger.csv"] = ledger
    outputs["authority/FREEZE_MANIFEST.csv"] = canonical_csv(
        (
            "relative_path",
            "role",
            "source_url",
            "bytes",
            "sha256",
            "last_modified",
            "etag",
            "verification",
        ),
        AUTHORITY_ROWS,
    )
    outputs["authority/LIVE_REVERIFY_2026-08-28.json"] = canonical_json(
        {
            "schema": "o006.c140.random-completeness.live-authority-reverify.v1",
            "date": "2026-08-28",
            "method": "credential-free static HTTP GET; no browser process",
            "documents_and_assets": [
                {
                    "url": row[2],
                    "status": 200,
                    "bytes": row[3],
                    "sha256": row[4],
                    "last_modified": row[5] or None,
                    "etag": row[6] or None,
                }
                for row in AUTHORITY_ROWS[:-1]
            ],
            "all_expected_identities_match": True,
            "rights_witness_discrepancy": {
                "landing": "CC BY 2.0",
                "credits": "CC BY 1.0",
                "preserved": True,
            },
            "machine_local_paths_recorded": False,
        }
    )
    return outputs, {
        "entities": entity_count,
        "relations": relation_count,
        "adverse_records": adverse_count,
        "translation_ledger_rows": ledger_count,
    }


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def inventory(outputs: dict[str, bytes]) -> list[dict[str, object]]:
    return [
        {"path": path, "bytes": len(payload), "sha256": sha256(payload)}
        for path, payload in sorted(outputs.items(), key=lambda item: item[0].casefold())
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sibling-root", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    sibling = args.sibling_root.resolve()
    outputs, counts = desired_outputs(sibling)
    receipt = canonical_json(
        {
            "schema": SCHEMA,
            "component": "O006/C140 Random completeness donor",
            "origin_repository": ORIGIN_REPOSITORY,
            "origin_commit": ORIGIN_COMMIT,
            "origin_public_readback": {
                "date": "2026-08-28",
                "credential_free": True,
                "commit": ORIGIN_COMMIT,
                "files": [
                    {
                        "path": "authority/upstream/random/point/Sufficient.html",
                        "bytes": 57_507,
                        "sha256": "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4",
                    },
                    {
                        "path": "source/id-ID/random/point/Sufficient.html",
                        "bytes": 60_895,
                        "sha256": "255ac88f235727301ee341eef79b9578910be88b7e2e038d4dfecc0ed686513c",
                    },
                ],
                "all_expected_identities_match": True,
            },
            "canonical_reader_correction": {
                "date": "2026-08-31",
                "line": 548,
                "before": "bersupport tetap",
                "after": "dengan dukungan tetap",
                "byte_delta": 5,
                "classification": "reader-facing Indonesian terminology refinement",
                "mathematical_meaning_changed": False,
                "authority_bytes_changed": False,
                "base_public_readback_retained_as_historical_evidence": True,
            },
            "source_path": SOURCE_PATH,
            "source_bytes": 57_507,
            "source_sha256": "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4",
            "target_locale": "id-ID",
            "target_bytes": 60_900,
            "target_sha256": "18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197",
            "rights_discrepancy": {
                "landing_witness": "CC BY 2.0",
                "credits_witness": "CC BY 1.0",
                "preserved": True,
            },
            "live_reverification_date": "2026-08-28",
            "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
            "counts": counts,
            "files": inventory(outputs),
            "machine_local_paths_recorded": False,
        }
    )
    outputs["IMPORT_RECEIPT.json"] = receipt

    if args.check_only:
        for relative, payload in outputs.items():
            path = COMPONENT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"import replay differs: {relative}")
        print(
            json.dumps(
                {
                    "mode": "check-only",
                    "files": len(outputs),
                    **counts,
                    "status": "pass",
                },
                sort_keys=True,
            )
        )
        return

    for relative, payload in outputs.items():
        atomic_write(COMPONENT / relative, payload)
    print(
        json.dumps(
            {
                "mode": "write",
                "files": len(outputs),
                **counts,
                "status": "pass",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
