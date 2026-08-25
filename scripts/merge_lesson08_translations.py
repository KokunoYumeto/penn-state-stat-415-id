#!/usr/bin/env python3
"""Configure the deterministic translation merger for Lesson 08."""

from pathlib import Path

import merge_lesson07_translations as merger


ROOT = Path(__file__).resolve().parents[1]
merger.TEMPLATE = ROOT / "working" / "lesson08_segments.csv"
merger.TARGET = ROOT / "source" / "id-ID" / "lesson08_translation.csv"
merger.BINDINGS = ROOT / "backend" / "lesson08_translation_bindings.jsonl"
merger.RECEIPT = ROOT / "build" / "LESSON08_TRANSLATION_RECEIPT.json"
merger.TERMINOLOGY_QA = ROOT / "working" / "lesson08_terminology_qa.md"
merger.SOURCE_FINDINGS = ROOT / "working" / "lesson08_source_findings.md"
merger.MATH_AUDIT = ROOT / "working" / "lesson08_math_audit.md"
merger.ASSET_CLOSURE = ROOT / "working" / "lesson08_asset_closure.json"
merger.NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON08_NORMALIZATION_RECEIPT.json"
merger.SCRIPT = ROOT / "scripts" / "merge_lesson08_translations.py"
merger.PARTS = {
    name: ROOT / "working" / f"lesson08_translation_part_{name}.json"
    for name in ("a", "b", "c")
}
merger.NOTES = {
    name: ROOT / "working" / f"lesson08_translation_part_{name}_notes.md"
    for name in merger.PARTS
}
merger.DOCUMENT_ID = "O006-PSU-009"
merger.COMPONENT_ID = "Lesson08"
merger.SEGMENT_COUNT = 291
merger.GLOSSARY_BYTES = 12_747
merger.GLOSSARY_SHA256 = "2887e4c3d817008744f8662c966262027bdbc7bf00314f880397d8aba766c095"
merger.GLOSSARY_ROWS = 122
merger.GLOSSARY_LAST_TERM_ID = "O006-TERM-0122"
merger.PART_RANGES = {"a": (1, 100), "b": (101, 200), "c": (201, 291)}
merger.GLOSSARY_SCOPE = "exact cumulative glossary through the thirteen Lesson 08 decisions"
merger.RECEIPT_SCHEMA = "o006.stat415.lesson08-translation.v1"
merger.TERMINOLOGY_RULE = "cumulative component glossary through O006-TERM-0122"
merger.REQUIRED_TERMS = (
    "bootstrap parametrik",
    "bootstrap nonparametrik",
    "sampel bootstrap",
    "nilai dugaan bootstrap",
    "pengambilan sampel ulang",
    "dengan pengembalian",
    "kuantil empiris",
    "metode delta",
    "distribusi asimtotik",
    "parameter bentuk",
    "parameter lokasi",
)
merger.FORBIDDEN_TERMS = (
    "interval kepercayaan",
    "interval konfidensi",
    "standard error",
    "confidence interval",
    "bootstrap sample",
    "delta method",
)


if __name__ == "__main__":
    merger.main()
