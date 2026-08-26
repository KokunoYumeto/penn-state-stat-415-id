#!/usr/bin/env python3
"""Publish the source-reproducibility correction inside the existing concept.

This adapter has no concept-creation path. It reuses the complete 14-of-14
publisher while hard-binding the corrected LF-normalized package and distinct
sanitized receipt paths. Importing or running ``--local-preflight`` does not
read the credential or access the network.
"""

from __future__ import annotations

from pathlib import Path

import publish_zenodo_through_lesson12 as base


ROOT = Path(__file__).resolve().parents[1]
VERSION = "2026.08.26.14of14-r1"
TITLE = "STAT 415: Pengantar Statistika Matematis — Edisi Bahasa Indonesia Lengkap (Revisi Reproduksibilitas)"
ORIGINAL_METADATA = base.metadata


def metadata() -> dict[str, object]:
    value = ORIGINAL_METADATA()
    value["title"] = TITLE
    value["version"] = VERSION
    value["description"] = (
        str(value["description"])
        + " Revisi ini tidak mengubah byte pembaca. Revisi hanya menyelaraskan "
        "identitas satu saksi temuan Markdown dengan kebijakan LF repositori "
        "(8.209 menjadi 8.203 byte), lalu memperbarui bukti reproduksi, QA, dan "
        "paket source-backend yang bergantung padanya."
    )
    return value


def configure_revision() -> None:
    base.VERSION = VERSION
    base.TITLE = TITLE
    base.DEFAULT_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLICATION_RECEIPT_2026-08-26_THROUGH_LESSON12_LF_REPAIR.json"
    base.READBACK_RECEIPT = ROOT / "00_control" / "ZENODO_PUBLIC_READBACK_2026-08-26_THROUGH_LESSON12_LF_REPAIR.json"
    base.AUDIT_RECEIPT = ROOT / "00_control" / "ZENODO_LINEAGE_AUDIT_2026-08-26_THROUGH_LESSON12_LF_REPAIR.json"
    base.DRAFT_MARKER = ROOT / "00_control" / "ZENODO_DRAFT_MARKER_2026-08-26_THROUGH_LESSON12_LF_REPAIR.json"
    base.metadata = metadata
    base.EXPECTED_PACKAGE_RECEIPT_BYTES = 4_428
    base.EXPECTED_PACKAGE_RECEIPT_SHA256 = "f0bb765a9d5134e88a9f52fb2f0860c0db53147ef319358c7fb5d53b43b42821"
    base.EXPECTED_RELEASE_MANIFEST_BYTES = 854
    base.EXPECTED_RELEASE_MANIFEST_SHA256 = "266fef654115e8731239f3ee793a43d835f9b6cb3a37012e58c0dc63dec8b0f9"
    base.EXPECTED_RELEASE_ROOT_BYTES = 4_763
    base.EXPECTED_RELEASE_ROOT_SHA256 = "66de90462f0ce8e9afdb72c681df41fc9270920dc11ae5833a7a525f4bd76db2"
    base.EXPECTED_TOTAL_BYTES = 55_310_251
    base.EXPECTED_RELEASE_IDENTITIES = {
        "00_stat415-id-through-lesson12-offline-reader.zip": (17_648_138, "e6c5829452e9d023ae7c54e802673a0e1fb0ddf220716d8f5156f1169ecb01e1"),
        "10_stat415-id-through-lesson12-source-backend.zip": (37_618_888, "8c3713d0ab05b7866ef9e48a1e0c2f07b1f69a73964aedafacd090a3aad859ad"),
        "20_THROUGH_LESSON12_RELEASE_NOTES.md": (1_213, "7db90c69118f75e41fef99d0ddd0704471710ff97b1b58957aa8e86a0b36f339"),
        "30_THROUGH_LESSON12_LICENSE.md": (1_515, "cea22cdb06aae5db47989d4daebbe3e36b7eac697e23a6726398744a9812a48d"),
        "40_THROUGH_LESSON12_QA_RECEIPT.json": (12_428, "44a0fd8e432f81da65776b45f33cccda0e462db32bb04bf8ecdb6d11eeca5560"),
        "41_THROUGH_LESSON12_VISUAL_QA_RECEIPT.json": (21_702, "2fe1f40b8748b0dcc67e08e6a87e6ba402b5323b581744f73e35c787ae583d5f"),
        "50_THROUGH_LESSON12_RELEASE_MANIFEST.csv": (854, "266fef654115e8731239f3ee793a43d835f9b6cb3a37012e58c0dc63dec8b0f9"),
        "SHA256SUMS_THROUGH_LESSON12.txt": (750, "4a1560061f552b26b4dace141dec0798cfa528c2c90aa0af88e98d52724dd26e"),
        "60_THROUGH_LESSON12_RELEASE_ROOT_RECEIPT.json": (4_763, "66de90462f0ce8e9afdb72c681df41fc9270920dc11ae5833a7a525f4bd76db2"),
    }


def main() -> None:
    configure_revision()
    base.main()


if __name__ == "__main__":
    main()
