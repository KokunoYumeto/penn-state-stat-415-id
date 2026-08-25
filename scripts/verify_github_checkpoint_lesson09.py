#!/usr/bin/env python3
"""Anonymously verify the cumulative 11-of-14 GitHub and Pages boundary."""

from pathlib import Path

import verify_github_checkpoint_lesson06 as verifier


ROOT = Path(__file__).resolve().parents[1]
verifier.MANIFEST_TREE_PATH = "build/THROUGH_LESSON09_MANIFEST.csv"
verifier.RECEIPT = (
    ROOT / "00_control" / "GITHUB_CHECKPOINT_RECEIPT_2026-08-25_THROUGH_LESSON09.json"
)
verifier.EXPECTED_PAGES_FILES = 71
verifier.RECEIPT_SCHEMA = "o006.stat415.github-through-lesson09-checkpoint.v1"
verifier.COVERAGE = {
    "complete_count": 11,
    "complete_documents": ["index", *[f"Lesson{i:02d}" for i in range(10)]],
    "corpus_document_count": 14,
    "next_document": "Lesson10",
}


if __name__ == "__main__":
    verifier.main()
