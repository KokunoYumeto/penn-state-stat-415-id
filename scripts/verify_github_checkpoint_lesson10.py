#!/usr/bin/env python3
"""Anonymously verify the cumulative 12-of-14 GitHub commit and Pages reader."""

from pathlib import Path

import verify_github_checkpoint_lesson06 as verifier


ROOT = Path(__file__).resolve().parents[1]
verifier.MANIFEST_TREE_PATH = "build/THROUGH_LESSON10_MANIFEST.csv"
verifier.RECEIPT = (
    ROOT / "00_control" / "GITHUB_CHECKPOINT_RECEIPT_2026-08-26_THROUGH_LESSON10.json"
)
verifier.EXPECTED_PAGES_FILES = 94
verifier.RECEIPT_SCHEMA = "o006.stat415.github-through-lesson10-checkpoint.v1"
verifier.COVERAGE = {
    "complete_count": 12,
    "complete_documents": ["index", *[f"Lesson{i:02d}" for i in range(11)]],
    "corpus_document_count": 14,
    "next_document": "Lesson11",
}


if __name__ == "__main__":
    verifier.main()
