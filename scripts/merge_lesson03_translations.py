#!/usr/bin/env python3
"""Merge the three bounded Lesson 03 translation maps deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "working" / "lesson03_segments.csv"
TARGET = ROOT / "source" / "id-ID" / "lesson03_translation.csv"
BINDINGS = ROOT / "backend" / "lesson03_translation_bindings.jsonl"
RECEIPT = ROOT / "build" / "LESSON03_TRANSLATION_RECEIPT.json"
GLOSSARY = ROOT / "00_control" / "TERMINOLOGY_GLOSSARY_ID_ID.csv"
TERMINOLOGY_QA = ROOT / "working" / "lesson03_terminology_qa.md"
SOURCE_FINDINGS = ROOT / "working" / "lesson03_source_findings.md"
ZERO_ASSET_CLOSURE = ROOT / "working" / "lesson03_zero_asset_closure.json"
PARTS = {
    "a": ROOT / "working" / "lesson03_translation_part_a.json",
    "b": ROOT / "working" / "lesson03_translation_part_b.json",
    "c": ROOT / "working" / "lesson03_translation_part_c.json",
}
FIELDS = (
    "segment_id", "document_id", "component_id", "section_id", "source_sha256",
    "source_text", "target_text", "status",
)
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
PUNCTUATION_BOUNDARY_EXCEPTIONS = {
    "O006-PSU-004-S0246": ",",
    "O006-PSU-004-S0248": ",",
    "O006-PSU-004-S0306": ".",
    "O006-PSU-004-S0419": ",",
}
WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS = {
    "O006-PSU-004-S0135",
    "O006-PSU-004-S0137",
    "O006-PSU-004-S0208",
    "O006-PSU-004-S0209",
    "O006-PSU-004-S0263",
    "O006-PSU-004-S0501",
    "O006-PSU-004-S0504",
    "O006-PSU-004-S0521",
    "O006-PSU-004-S0523",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def canonical_jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def expected_part_keys() -> dict[str, set[str]]:
    return {
        "a": {f"O006-PSU-004-S{i:04d}" for i in range(1, 178)},
        "b": {f"O006-PSU-004-S{i:04d}" for i in range(178, 355)},
        "c": {f"O006-PSU-004-S{i:04d}" for i in range(355, 532)},
    }


def load_template() -> tuple[list[dict[str, str]], bytes]:
    data = TEMPLATE.read_bytes()
    try:
        rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise RuntimeError(f"invalid Lesson 03 segment CSV: {exc}") from exc
    if not rows or tuple(rows[0].keys()) != FIELDS or len(rows) != 531:
        raise RuntimeError("Lesson 03 segment CSV header or row count differs")
    expected_ids = [f"O006-PSU-004-S{i:04d}" for i in range(1, 532)]
    if [row["segment_id"] for row in rows] != expected_ids:
        raise RuntimeError("Lesson 03 segment IDs are not the admitted sequential boundary")
    if any(
        row["document_id"] != "O006-PSU-004"
        or row["component_id"] != "Lesson03"
        or row["target_text"]
        or row["status"] != "pending"
        for row in rows
    ):
        raise RuntimeError("Lesson 03 pending template fields differ")
    return rows, data


def load_parts() -> tuple[dict[str, str], list[dict[str, object]]]:
    expected = expected_part_keys()
    merged: dict[str, str] = {}
    evidence: list[dict[str, object]] = []
    for name in ("a", "b", "c"):
        data = PARTS[name].read_bytes()
        try:
            values = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"invalid Lesson 03 translation part {name}: {exc}") from exc
        if not isinstance(values, dict) or set(values) != expected[name]:
            raise RuntimeError(f"Lesson 03 translation part {name} has the wrong key set")
        if any(not isinstance(value, str) or not value.strip() for value in values.values()):
            raise RuntimeError(f"Lesson 03 translation part {name} has an empty target")
        if set(merged).intersection(values):
            raise RuntimeError("Lesson 03 translation partitions overlap")
        merged.update(values)
        evidence.append(
            {
                "part": name,
                "path": PARTS[name].relative_to(ROOT).as_posix(),
                "segments": len(values),
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    return merged, evidence


def input_evidence(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def compute() -> dict[str, bytes]:
    rows, template_data = load_template()
    translations, part_evidence = load_parts()
    expected_ids = {row["segment_id"] for row in rows}
    if set(translations) != expected_ids:
        raise RuntimeError("Lesson 03 translation parts do not cover all segments")

    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    binding_rows: list[dict[str, object]] = []
    translated_text: list[str] = []
    for ordinal, row in enumerate(rows, start=1):
        source = row["source_text"]
        raw_target = translations[row["segment_id"]]
        leading = re.match(r"^\s*", source).group(0)
        trailing = re.search(r"\s*$", source).group(0)
        if row["segment_id"] in PUNCTUATION_BOUNDARY_EXCEPTIONS:
            expected_punctuation = PUNCTUATION_BOUNDARY_EXCEPTIONS[row["segment_id"]]
            if not raw_target.lstrip().startswith(expected_punctuation):
                raise RuntimeError(f"punctuation-boundary exception differs: {row['segment_id']}")
            if expected_punctuation == "," and not leading:
                raise RuntimeError(f"registered pre-comma source space is absent: {row['segment_id']}")
            leading = ""
        if row["segment_id"] in WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS:
            if not raw_target.startswith(" "):
                raise RuntimeError(f"word-boundary leading space is absent: {row['segment_id']}")
            leading = " "
        target = leading + raw_target.strip() + trailing
        if not target.strip():
            raise RuntimeError(f"normalized target is empty: {row['segment_id']}")
        complete = dict(row)
        complete["target_text"] = target
        complete["status"] = "translated"
        writer.writerow(complete)
        translated_text.append(target)
        binding_rows.append(
            {
                "schema": "o006.stat415.translation-binding.v1",
                "segment_id": row["segment_id"],
                "document_id": row["document_id"],
                "component_id": row["component_id"],
                "section_id": row["section_id"] or None,
                "ordinal": ordinal,
                "locale": "id-ID",
                "source_sha256": row["source_sha256"],
                "target_sha256": sha256(target.encode("utf-8")),
                "status": "translated",
            }
        )

    joined = "\n".join(translated_text).casefold()
    required_terms = (
        "statistik cukup", "teorema faktorisasi", "fungsi satu-satu",
        "bentuk eksponensial", "kriteria eksponensial", "metode momen",
        "momen teoretis", "momen sampel", "distribusi empiris",
    )
    missing_terms = [term for term in required_terms if term not in joined]
    if missing_terms:
        raise RuntimeError(f"required Lesson 03 terminology absent: {missing_terms}")
    forbidden_terms = (
        "statistik sufisien", "teorema pemfaktoran", "one-to-one function",
        "method of moments", "sample mean",
    )
    present_forbidden = [term for term in forbidden_terms if term in joined]
    if present_forbidden:
        raise RuntimeError(f"superseded Lesson 03 terminology present: {present_forbidden}")
    if "\ufffd" in joined:
        raise RuntimeError("Lesson 03 translation contains a replacement character")

    csv_payload = output.getvalue().encode("utf-8")
    bindings_payload = canonical_jsonl(binding_rows)
    receipt = {
        "schema": "o006.stat415.lesson03-translation.v1",
        "status": "complete",
        "document": "Lesson03",
        "document_id": "O006-PSU-004",
        "segment_count": len(binding_rows),
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "boundary_whitespace_rule": (
            "exact source-node leading/trailing whitespace wrapped around translated prose core, except "
            "registered punctuation repairs and word-after-math leading-space repairs"
        ),
        "punctuation_boundary_exceptions": [
            {"segment_id": segment_id, "punctuation": PUNCTUATION_BOUNDARY_EXCEPTIONS[segment_id]}
            for segment_id in sorted(PUNCTUATION_BOUNDARY_EXCEPTIONS)
        ],
        "word_boundary_leading_space_exceptions": sorted(WORD_BOUNDARY_LEADING_SPACE_EXCEPTIONS),
        "terminology_rule": "component glossary plus the Lesson 03 continuity and precision decision",
        "template": {
            "path": TEMPLATE.relative_to(ROOT).as_posix(),
            "bytes": len(template_data),
            "sha256": sha256(template_data),
        },
        "parts": part_evidence,
        "terminology_inputs": [input_evidence(GLOSSARY), input_evidence(TERMINOLOGY_QA)],
        "source_findings": input_evidence(SOURCE_FINDINGS),
        "zero_asset_closure": input_evidence(ZERO_ASSET_CLOSURE),
        "translation_csv": {
            "path": TARGET.relative_to(ROOT).as_posix(),
            "bytes": len(csv_payload),
            "sha256": sha256(csv_payload),
        },
        "bindings": {
            "path": BINDINGS.relative_to(ROOT).as_posix(),
            "bytes": len(bindings_payload),
            "sha256": sha256(bindings_payload),
        },
    }
    return {
        TARGET.relative_to(ROOT).as_posix(): csv_payload,
        BINDINGS.relative_to(ROOT).as_posix(): bindings_payload,
        RECEIPT.relative_to(ROOT).as_posix(): canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    outputs = compute()
    if args.write:
        for relative, payload in outputs.items():
            atomic_write(ROOT / relative, payload)
        state = "written"
    else:
        for relative, payload in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"Lesson 03 translation output differs: {relative}")
        state = "verified"
    receipt_payload = outputs[RECEIPT.relative_to(ROOT).as_posix()]
    print(
        json.dumps(
            {"mode": state, "segments": 531, "receipt_sha256": sha256(receipt_payload)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
