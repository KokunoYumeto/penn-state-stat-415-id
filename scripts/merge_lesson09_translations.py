#!/usr/bin/env python3
"""Configure the deterministic translation merger for Lesson 09."""

from pathlib import Path

import merge_lesson07_translations as merger


ROOT = Path(__file__).resolve().parents[1]
merger.TEMPLATE = ROOT / "working" / "lesson09_segments.csv"
merger.TARGET = ROOT / "source" / "id-ID" / "lesson09_translation.csv"
merger.BINDINGS = ROOT / "backend" / "lesson09_translation_bindings.jsonl"
merger.RECEIPT = ROOT / "build" / "LESSON09_TRANSLATION_RECEIPT.json"
merger.TERMINOLOGY_QA = ROOT / "working" / "lesson09_terminology_qa.md"
merger.SOURCE_FINDINGS = ROOT / "working" / "lesson09_source_findings.md"
merger.MATH_AUDIT = ROOT / "working" / "lesson09_math_audit.md"
merger.ASSET_CLOSURE = ROOT / "working" / "lesson09_asset_closure.json"
merger.NORMALIZATION_RECEIPT = ROOT / "build" / "LESSON09_NORMALIZATION_RECEIPT.json"
merger.SCRIPT = ROOT / "scripts" / "merge_lesson09_translations.py"
merger.PARTS = {
    name: ROOT / "working" / f"lesson09_translation_part_{name}.json"
    for name in ("a", "b", "c")
}
merger.NOTES = {
    name: ROOT / "working" / f"lesson09_translation_part_{name}_notes.md"
    for name in merger.PARTS
}
merger.DOCUMENT_ID = "O006-PSU-010"
merger.COMPONENT_ID = "Lesson09"
merger.SEGMENT_COUNT = 443
merger.GLOSSARY_BYTES = 14_687
merger.GLOSSARY_SHA256 = "d0f8baa72ac1be3a3be1e5774db5608ce8655aa83aed910363727e05322b45f0"
merger.GLOSSARY_ROWS = 142
merger.GLOSSARY_LAST_TERM_ID = "O006-TERM-0142"
merger.PART_RANGES = {"a": (1, 148), "b": (149, 296), "c": (297, 443)}
merger.GLOSSARY_SCOPE = "exact cumulative glossary through the twenty Lesson 09 decisions"
merger.RECEIPT_SCHEMA = "o006.stat415.lesson09-translation.v1"
merger.TERMINOLOGY_RULE = "cumulative component glossary through O006-TERM-0142"
merger.REQUIRED_TERMS = (
    "uji hipotesis",
    "hipotesis nol",
    "hipotesis alternatif",
    "tingkat signifikansi",
    "statistik uji",
    "daerah penolakan",
    "menolak hipotesis nol",
    "gagal menolak hipotesis nol",
    "galat tipe i",
    "galat tipe ii",
    "nilai-p",
    "kuasa uji",
    "uji satu sisi",
    "dua sisi",
    "sekurang-kurangnya sama ekstrem",
)
merger.FORBIDDEN_TERMS = (
    "null hypothesis",
    "alternative hypothesis",
    "p-value",
    "type i error",
    "type ii error",
    "test statistic",
    "significance level",
)


if __name__ == "__main__":
    merger.main()
