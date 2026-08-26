#!/usr/bin/env python3
"""Anonymously verify the cumulative 13-of-14 GitHub commit and Pages reader."""

from pathlib import Path

import verify_github_checkpoint_lesson06 as verifier


ROOT = Path(__file__).resolve().parents[1]
verifier.MANIFEST_TREE_PATH = "build/THROUGH_LESSON11_MANIFEST.csv"
verifier.RECEIPT = (
    ROOT / "00_control" / "GITHUB_CHECKPOINT_RECEIPT_2026-08-26_THROUGH_LESSON11.json"
)
verifier.EXPECTED_PAGES_FILES = 96
verifier.RECEIPT_SCHEMA = "o006.stat415.github-through-lesson11-checkpoint.v1"
verifier.COVERAGE = {
    "complete_count": 13,
    "complete_documents": ["index", *[f"Lesson{i:02d}" for i in range(12)]],
    "corpus_document_count": 14,
    "next_document": "Lesson12",
}


if __name__ == "__main__":
    verifier.main()
