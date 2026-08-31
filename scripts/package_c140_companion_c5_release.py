#!/usr/bin/env python3
"""Package the cumulative C140 original-companion C5 checkpoint.

The local contract preserves the anonymously verified 57-file C4 publication
byte for byte and appends exactly eight compact C5 artifacts.  It performs no
browser, network, credential, Git, or publication operation.  Only ``--write``
creates the new local release files and package receipt.

All C5 build, QA, data-transform, capstone-analysis, manifest, source, rights,
and provenance inputs are bound below by exact byte count and SHA-256.  Every
packaging mode fails closed if an identity or semantic contract differs.
``--base-only`` independently validates the already-public C4 union.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import os
import re
import stat
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

import package_c140_companion_c1_release as shared


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "c140-companion"
RELEASE = ROOT / "release"

BASE_PACKAGE_RECEIPT = (
    ROOT / "build" / "C140_COMPANION_C4_RELEASE_PACKAGE_RECEIPT.json"
)
BASE_PUBLIC_READBACK = (
    ROOT
    / "00_control"
    / "ZENODO_PUBLIC_READBACK_2026-08-29_C140_COMPANION_C4.json"
)
PACKAGE_RECEIPT = ROOT / "build" / "C140_COMPANION_C5_RELEASE_PACKAGE_RECEIPT.json"

OFFLINE_NAME = "06_C140_COMPANION_C5_OFFLINE_READER.zip"
SOURCE_NAME = "16_C140_COMPANION_C5_SOURCE_BACKEND_DATA_RIGHTS.zip"
NOTES_NAME = "26_C140_COMPANION_C5_RELEASE_NOTES.md"
LICENSE_NAME = "36_C140_COMPANION_C5_COMPONENT_AND_DATASET_LICENSES.md"
QA_NAME = "46_C140_COMPANION_C5_STATIC_QA_EVIDENCE.zip"
MANIFEST_NAME = "98_C140_COMPANION_C5_FULL_UNION_MANIFEST.csv"
CHECKSUM_NAME = "SHA256SUMS_C140_COMPANION_C5.txt"
ROOT_NAME = "99_C140_COMPANION_C5_FULL_UNION_ROOT_RECEIPT.json"

VERSION = "2026.08.31.c140-companion-c5"
SCHEMA = "o006.c140.companion-c5-release-package.v1"
BASE_SCHEMA = "o006.c140.companion-c4-release-package.v1"
BASE_READBACK_SCHEMA = "o006.c140.zenodo-c140-companion-c4-publication.v1"
BASE_VERSION = "2026.08.29.c140-companion-c4"
BASE_RECORD_ID = "22164344"
BASE_RECORD_DOI = "10.5281/zenodo.22164344"
CONCEPT_RECORD_ID = "22077422"
CONCEPT_DOI = "10.5281/zenodo.22077422"

BASE_PACKAGE_RECEIPT_BYTES = 34_142
BASE_PACKAGE_RECEIPT_SHA256 = (
    "45c0fceb27af175689e5ee8ac92271d395a41cdf96c32621eacf8d60a8222f7f"
)
BASE_PUBLIC_READBACK_BYTES = 22_171
BASE_PUBLIC_READBACK_SHA256 = (
    "fe92ec27c63d8af29ea30bf46977fd8694e6febcdc3375db29f8bf2db60acf8d"
)
BASE_FILE_COUNT = 57
BASE_TOTAL_BYTES = 93_850_993
MAX_PUBLICATION_BYTES = 500_000_000
MAX_PUBLIC_FILE_BYTES = 100_000_000
MAX_INPUT_FILE_BYTES = MAX_PUBLICATION_BYTES
MAX_SNAPSHOT_BYTES = MAX_PUBLICATION_BYTES
MAX_SNAPSHOT_FILES = 100_000
MAX_ZIP_MEMBERS = 65_535

WINDOWS_RESERVED_COMPONENTS = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}

# These historical identities remain immutable.  The C5 identities below are
# patched only after the producers declare their artifacts frozen.
FROZEN_HISTORICAL_INPUTS: dict[str, tuple[int, str]] = {
    "build/C1_SIMULATION_RECEIPT.json": (
        5_468,
        "834c8a20025d51bf53ef4e8d0f7d805489af21c34065238131366a734df7e213",
    ),
    "build/C2_SIMULATION_RECEIPT.json": (
        2_187,
        "de89e57c10c178915ddd96e12d368e5e11b40baa47b6fc31c2e3df5adbd63bd2",
    ),
    "build/C3_SIMULATION_RECEIPT.json": (
        3_389,
        "c7f176380b2e30b9931cc44bcc2e39bb541559030cf65b1c41f32045c13b1040",
    ),
    "build/C1_BUILD_RECEIPT.json": (
        4_070,
        "1f9c746e723259ec46419586ac2c6f4b6ef7684deb9427e3eeb9cbc488e9ba35",
    ),
    "build/C1_QA_RECEIPT.json": (
        2_263,
        "c6b5977feb035d0f1425438dfd88b12cf8fc876820ddb04287fd62b6c37cfd67",
    ),
    "build/C2_BUILD_RECEIPT.json": (
        5_770,
        "6417c7a8764082ce74e397ccdb79d337534d27c888d8d2cc12830d6947d7c0a1",
    ),
    "build/C2_QA_RECEIPT.json": (
        3_128,
        "0f118dae5488a68098aa9fef5c03a4135968eee2c74f509f67b0817e05bc38ef",
    ),
    "build/C3_BUILD_RECEIPT.json": (
        6_780,
        "79661673ad7f4d74eff997cebd6fca1f46d2a74cbab5930147ca109762ef37ca",
    ),
    "build/C3_QA_RECEIPT.json": (
        3_697,
        "6f53a1f54d3a1b3e23b874a3c13adda9726bc0a8456d2fb4a8315d11912f72d7",
    ),
    "build/C4_BUILD_RECEIPT.json": (
        8_209,
        "c21aecda780cf8e56eb82a41d19b9b0a112e81caf583f38041a5d9fd4ffc0ac1",
    ),
    "build/C4_QA_RECEIPT.json": (
        4_514,
        "dfadcc6338ad44d9dadd13fa2f7ef19d9b9e19e428f25f3fe7607852bfa8e2e7",
    ),
}

FROZEN_HISTORICAL_MANIFESTS: dict[str, tuple[int, str]] = {
    "generated/simulations/c1/MANIFEST.csv": (
        1_128,
        "8644723b24a1afa06076d77ac55e96d93540a726df18f449b6f2efc3808d8fb8",
    ),
    "generated/simulations/c2/MANIFEST.csv": (
        345,
        "49d4b956a278c251458932dc9fcbdf66ef5e73d187f69398620601cf39b3c1b1",
    ),
    "generated/simulations/c3/MANIFEST.csv": (
        549,
        "64557d83097e30885ce6a9be08accd184efff745fcf532a8397f7839379e10f0",
    ),
}

# C5 corrects Indonesian SVG labels in the live C1/C2 simulation outputs.
# Their previously published identities above remain historical evidence;
# the inherited release files are still validated byte-for-byte separately.
FROZEN_C5_SIMULATION_INPUT_OVERRIDES: dict[str, tuple[int, str]] = {
    "build/C1_SIMULATION_RECEIPT.json": (
        5_468,
        "d577080010cc99c2bc34fc74c4b059830a459ac010d97e9bd27ecd9265d18a8c",
    ),
    "build/C2_SIMULATION_RECEIPT.json": (
        2_187,
        "2dcb763ef4f4576260eb8483c06927eef2d50f616dc3c67e919553f1381c13f3",
    ),
}
FROZEN_C5_SIMULATION_MANIFEST_OVERRIDES: dict[str, tuple[int, str]] = {
    "generated/simulations/c1/MANIFEST.csv": (
        1_128,
        "926bfad374a0dfa0881c8d4c23b3881b8c20039af2e0c197a19cc3d90fa2dc7d",
    ),
    "generated/simulations/c2/MANIFEST.csv": (
        345,
        "eff4b1c03f0bbb180d4f9ed7da8fd6b20635d2e24e3803486be7b292caed3275",
    ),
}
CURRENT_PRIOR_BATCH_INPUTS = {
    **FROZEN_HISTORICAL_INPUTS,
    **FROZEN_C5_SIMULATION_INPUT_OVERRIDES,
}
CURRENT_PRIOR_BATCH_MANIFESTS = {
    **FROZEN_HISTORICAL_MANIFESTS,
    **FROZEN_C5_SIMULATION_MANIFEST_OVERRIDES,
}

REQUIRED_C5_INPUTS = {
    "build/C5_BUILD_RECEIPT.json",
    "build/C5_QA_RECEIPT.json",
    "build/CP01_TRANSFORM_RECEIPT.json",
    "build/CP02_TRANSFORM_RECEIPT.json",
    "build/CP02_ANALYSIS_RECEIPT.json",
    "generated/capstones/CP01/CP01_REPLAY_RECEIPT.json",
}

# Fail-closed placeholder.  Each value becomes (byte_count, SHA-256) only after
# the corresponding producer has finished deterministic write/check replays.
FROZEN_C5_INPUTS: dict[str, tuple[int, str]] = {
    "build/C5_BUILD_RECEIPT.json": (
        13_951,
        "cc9e6002edcbb5adbe5a348233fb73f5588728a4fbc330a93061c1f18807f372",
    ),
    "build/C5_QA_RECEIPT.json": (
        9_279,
        "aef36e757fca2d3ad1593087af12a5102120697f16715acf210248d94d296bfd",
    ),
    "build/CP01_TRANSFORM_RECEIPT.json": (
        2_465,
        "177848b6be8282fdcc1be402b4e1214eaa7d79019af5a3c02fbd977fa7e5efdc",
    ),
    "build/CP02_ANALYSIS_RECEIPT.json": (
        9_272,
        "8905654384a792e718eb824313e7233f8576b6ae8b55132db42e2740c63beb73",
    ),
    "build/CP02_TRANSFORM_RECEIPT.json": (
        3_988,
        "a993996a6dedf374c7ad5efe1846ae773779a1218863ea7f50d9efa6930eea2a",
    ),
    "generated/capstones/CP01/CP01_REPLAY_RECEIPT.json": (
        15_079,
        "3afee61bc95dd93a23f6d847c02dffde30299c4f62c83f7ae7ebcfa3267724e1",
    ),
}

REQUIRED_C5_MANIFESTS = {
    "build/html-id/MANIFEST.csv",
    "backend/MANIFEST.csv",
    "generated/capstones/CP01/MANIFEST.csv",
    "generated/capstones/CP02/MANIFEST.csv",
    "data/capstones/CP02/clean/MANIFEST.csv",
}
FROZEN_C5_MANIFESTS: dict[str, tuple[int, str]] = {
    "backend/MANIFEST.csv": (
        14_134,
        "67defeb90b216f3306c9a49dcbe08bf8da51206cd8d9a9f53a0339374b001bf3",
    ),
    "build/html-id/MANIFEST.csv": (
        15_206,
        "cf5f75feececdf98bb02e9cbd8bb8144b457f3434622f9038af26ae7c89c2f46",
    ),
    "data/capstones/CP02/clean/MANIFEST.csv": (
        490,
        "b79f206caea52b557e29b839ccec6b4659960601cc002100cb7c7e36e8d9b6b8",
    ),
    "generated/capstones/CP01/MANIFEST.csv": (
        3_195,
        "e298964a34c31110db0944f2f6feb54efb1a9ef88e49aa657ede3a00be2bca9b",
    ),
    "generated/capstones/CP02/MANIFEST.csv": (
        2_373,
        "2f147d50378558730ce2fb334193e1761b2636ee96ee2ba6498bd91849f3d98b",
    ),
}

REQUIRED_C5_SUPPORT_INPUTS = {
    "LICENSE.md",
    "environment.lock.json",
    "capstones/run_cp01_analysis.py",
    "capstones/run_cp02_analysis.py",
    "scripts/build_companion.py",
    "scripts/qa_companion.py",
    "simulations/run_c1_simulations.py",
    "simulations/run_c2_simulations.py",
    "simulations/run_c3_simulations.py",
    "data/capstones/CP01/DATASET_PROVENANCE.json",
    "data/capstones/CP01/SHA256SUMS",
    "data/capstones/CP01/transform_cp01.py",
    "data/capstones/CP01/http/cc-by-4.0-legalcode.html.headers",
    "data/capstones/CP01/http/concrete+compressive+strength.zip.headers",
    "data/capstones/CP01/http/data.csv.headers",
    "data/capstones/CP01/http/doi-10.24432-C5PK67-csl.json.headers",
    "data/capstones/CP01/http/doi-10.24432-C5PK67-resolved.html.headers",
    "data/capstones/CP01/http/uci-dataset-165-api.json.headers",
    "data/capstones/CP01/http/uci-dataset-165-record.html.headers",
    "data/capstones/CP01/raw/archive/Concrete_Data.xls",
    "data/capstones/CP01/raw/data.csv",
    "data/capstones/CP01/raw/concrete+compressive+strength.zip",
    "data/capstones/CP01/raw/archive/Concrete_Readme.txt",
    "data/capstones/CP01/witnesses/cc-by-4.0-legalcode.html",
    "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-csl.json",
    "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-resolved.html",
    "data/capstones/CP01/witnesses/uci-dataset-165-api.json",
    "data/capstones/CP01/witnesses/uci-dataset-165-record.html",
    "data/capstones/CP02/DATASET_PROVENANCE.json",
    "data/capstones/CP02/INPUT_MANIFEST.csv",
    "data/capstones/CP02/RIGHTS_EVIDENCE.md",
    "data/capstones/CP02/SCHEMA.json",
    "data/capstones/CP02/transform_cp02.py",
    "data/capstones/CP02/http/cc0-1.0-legalcode.html.headers",
    "data/capstones/CP02/http/datacite-doi-10.5061-dryad.573n5tbf3.json.headers",
    "data/capstones/CP02/http/dataset-doi-10.5061-dryad.573n5tbf3-api.json.headers",
    "data/capstones/CP02/http/doi-10.5061-dryad.573n5tbf3-resolved.html.headers",
    "data/capstones/CP02/http/dryad-reuse-guide.html.headers",
    "data/capstones/CP02/http/file-2765112.json.headers",
    "data/capstones/CP02/http/file-2765118.json.headers",
    "data/capstones/CP02/http/nest_propensity.csv.headers",
    "data/capstones/CP02/http/README.md.headers",
    "data/capstones/CP02/http/version-268230-files.json.headers",
    "data/capstones/CP02/http/version-268230.json.headers",
    "data/capstones/CP02/raw/nest_propensity.csv",
    "data/capstones/CP02/raw/README.md",
    "data/capstones/CP02/witnesses/cc0-1.0-legalcode.html",
    "data/capstones/CP02/witnesses/datacite-doi-10.5061-dryad.573n5tbf3.json",
    "data/capstones/CP02/witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json",
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redacted.html",
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redistribution-redaction.json",
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-resolved.html",
    "data/capstones/CP02/witnesses/dryad-reuse-guide.html",
    "data/capstones/CP02/witnesses/file-2765112.json",
    "data/capstones/CP02/witnesses/file-2765118.json",
    "data/capstones/CP02/witnesses/version-268230-files.json",
    "data/capstones/CP02/witnesses/version-268230.json",
}
FROZEN_C5_SUPPORT_INPUTS: dict[str, tuple[int, str]] = {
    "capstones/run_cp01_analysis.py": (
        134_413,
        "3557247402e41950580f79c5dc78ac0b60311be181b4d6a5bef710e71ee1bf9b",
    ),
    "capstones/run_cp02_analysis.py": (
        130_738,
        "2c156dcba81126dd9fe0f457424e309b43bf6d1fec2ee5e8a007902a660c3c28",
    ),
    "data/capstones/CP01/DATASET_PROVENANCE.json": (
        16_885,
        "08cd61239545c65900eabc0912cc01181314134d8c59afe2b11c5a026cd33fa0",
    ),
    "data/capstones/CP01/http/cc-by-4.0-legalcode.html.headers": (
        315,
        "14ce2179f398bf81f3df6738c26defd4c7a7f5832f996ca1fae4b06d0400c11b",
    ),
    "data/capstones/CP01/http/concrete+compressive+strength.zip.headers": (
        130,
        "128b5481bf03f61ce8ebedaf0ab1272e41e1df2814e68d1b07d403347f21b3cc",
    ),
    "data/capstones/CP01/http/data.csv.headers": (
        130,
        "6416234f55b2194602866263cb1cbb4a5ed76213ff887eff8199b040eec5088f",
    ),
    "data/capstones/CP01/http/doi-10.24432-C5PK67-csl.json.headers": (
        1_492,
        "8afb3f7a45e359a8150986110ad96085c71d1ec21b320350c0aac9613e171282",
    ),
    "data/capstones/CP01/http/doi-10.24432-C5PK67-resolved.html.headers": (
        1_204,
        "98449b14ab79c25b836dc2e518896ff1ac244256df3fe0056d60691b05f8c539",
    ),
    "data/capstones/CP01/http/uci-dataset-165-api.json.headers": (
        170,
        "ce03e93e32431647cf52bcdca3430e2c3f6907553a51ebeec8093e265d4c6b10",
    ),
    "data/capstones/CP01/http/uci-dataset-165-record.html.headers": (
        192,
        "9a4651bec4ff5722784703eca4f5927167ff46751aaa4d1b56f9c12ed3acb39b",
    ),
    "data/capstones/CP01/raw/archive/Concrete_Data.xls": (
        124_928,
        "710076c66b9ca3f8050e7942f3dcbdbe04013534daeb0077ffd3079a52d8e0c4",
    ),
    "data/capstones/CP01/raw/archive/Concrete_Readme.txt": (
        3_808,
        "5cd3cdb31d3cfd68287daa6b22ed0541d6932113e83ee0980ced63641af3441d",
    ),
    "data/capstones/CP01/raw/concrete+compressive+strength.zip": (
        34_444,
        "dad85d14de8aee4e07479daa774e6b569a313715b71a3b92c95a07cf91c2c9a7",
    ),
    "data/capstones/CP01/raw/data.csv": (
        41_472,
        "8d4b15b6fc68cd932d745cbd663d5ceae66dd54422e99c1e4865f2936ab7e2af",
    ),
    "data/capstones/CP01/SHA256SUMS": (
        1_635,
        "f11ee0fc23691482863a42330004eff024d65dd5c71809a815dc2b02e73028b8",
    ),
    "data/capstones/CP01/transform_cp01.py": (
        26_527,
        "696a329e2aa5d7af0154c83c48be7b869ba1a0bef1ff0e5177c87a5a8707cc11",
    ),
    "data/capstones/CP01/witnesses/cc-by-4.0-legalcode.html": (
        48_970,
        "6d55b998ed5c54f43426d059a8c549ed58a3321e5463e6a6af1c6b56ab78c333",
    ),
    "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-csl.json": (
        376,
        "53482e0939fcbc55c7e9f1a16029d8735c7d2c060798b1c85be98425e06512cd",
    ),
    "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-resolved.html": (
        119_937,
        "d66b9a8327138a98807b0bb9de31b75649617c481b1aba110a364e43d8e3bafb",
    ),
    "data/capstones/CP01/witnesses/uci-dataset-165-api.json": (
        3_971,
        "e6bf60c33164024edd612f205e429b48cf66a08b639184567e24536c5e3f8e03",
    ),
    "data/capstones/CP01/witnesses/uci-dataset-165-record.html": (
        119_937,
        "ed33939f897be461aeb9ac491e68e9eedc1c54b34ceea6977ce6557d204dd296",
    ),
    "data/capstones/CP02/DATASET_PROVENANCE.json": (
        8_255,
        "a044cf3353794031a169189623b273e3aeb116c7d33784e7520eaf1311dac49a",
    ),
    "data/capstones/CP02/http/cc0-1.0-legalcode.html.headers": (
        356,
        "783ece46c1887b1ed838c6faebfa4ae84de01c1e3eff7277379aabd137644e30",
    ),
    "data/capstones/CP02/http/datacite-doi-10.5061-dryad.573n5tbf3.json.headers": (
        355,
        "8b4f9a544c12c0b658964d62d31d84f7304c75ee1bbc0129ca5b3aa6bdb23b7b",
    ),
    "data/capstones/CP02/http/dataset-doi-10.5061-dryad.573n5tbf3-api.json.headers": (
        402,
        "a8a098b190f8c9e753235315dda9eae423faad458a9457fcbb0e771d744cfbcf",
    ),
    "data/capstones/CP02/http/doi-10.5061-dryad.573n5tbf3-resolved.html.headers": (
        506,
        "9b5614cb1deefeed51f5c34cf8663d9723127594a81f4134d61be1d9a2d8c3e8",
    ),
    "data/capstones/CP02/http/dryad-reuse-guide.html.headers": (
        345,
        "621906ce04a8f8d2e447db01eafbdc6e6ee3e5bb64fc0825752134dc6e042b54",
    ),
    "data/capstones/CP02/http/file-2765112.json.headers": (
        374,
        "425be8499e12260a0a0e51a1a572af6c12af68bc28776e6ccab702757ba76274",
    ),
    "data/capstones/CP02/http/file-2765118.json.headers": (
        374,
        "dcc186f2ed3a14d51e5d0a38a602beeaa4aae32b77b545e71183ff790e96db4b",
    ),
    "data/capstones/CP02/http/nest_propensity.csv.headers": (
        747,
        "94d4a334b2cef34c5a3cc31a7ac47bac9bfb4a8af6db716e44e2ade691d21ca8",
    ),
    "data/capstones/CP02/http/README.md.headers": (
        738,
        "bb6f4cd8a052ee3aadcc96535d605b632336c238f0db17ec595bff3cf4570c8b",
    ),
    "data/capstones/CP02/http/version-268230-files.json.headers": (
        383,
        "b2ce37b708a6ac1119a91f510952e7db46d1aef90d800f3bb62605c771263b0b",
    ),
    "data/capstones/CP02/http/version-268230.json.headers": (
        377,
        "2a51f5f4576d9ee0a909b61498e6c7dabfc3e5f3c1c4dd77311c694376d4ffd9",
    ),
    "data/capstones/CP02/INPUT_MANIFEST.csv": (
        913,
        "4e191caad7a1c4a971dd619039bd5891cae264cbc078ff8fffc23ed5f27669ff",
    ),
    "data/capstones/CP02/raw/nest_propensity.csv": (
        285,
        "8790b4dfa29a5b39228e758e40e02cbb48612c38b8440020aa108c85ca0673c4",
    ),
    "data/capstones/CP02/raw/README.md": (
        4_139,
        "43a53f9a451a4030b8d3edb2a7517c48863d8ef23d7ae4986d15c20d7f8f5459",
    ),
    "data/capstones/CP02/RIGHTS_EVIDENCE.md": (
        3_089,
        "1017d9ba16aa5f64e4c6d19c59a648b677c113ab20b78e8bd87e5d99739ae665",
    ),
    "data/capstones/CP02/SCHEMA.json": (
        4_770,
        "367597e96a39f50d29a67f1a3ac31c0642e61c0439879253a59c1de9f37627e4",
    ),
    "data/capstones/CP02/transform_cp02.py": (
        30_366,
        "b0f78101208eb52da9e8536153e9183a5202704fbedca91a34bf49bf618f54ae",
    ),
    "data/capstones/CP02/witnesses/cc0-1.0-legalcode.html": (
        32_451,
        "001e3d1c905c18b1d034b34200cc952026abb38457c2294c23eaef7f6bda64df",
    ),
    "data/capstones/CP02/witnesses/datacite-doi-10.5061-dryad.573n5tbf3.json": (
        25_057,
        "b781ca972d4af2c351cf18de65c30cb68c9bc5f84b7651e92c6213188ef0a14b",
    ),
    "data/capstones/CP02/witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json": (
        4_844,
        "86de401cda5e1966253174504c4c786fd48e6cf39ecb4b77c8f826ca7a9b8d74",
    ),
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redacted.html": (
        45_103,
        "3a03d836ebdb80191a70ff71d4faaa810eee966307482bdae5d04b430d5c8f9f",
    ),
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redistribution-redaction.json": (
        662,
        "5398e6f32c2d0eb81475e37c7a9ea35a8f1833ee387c6119376e308fefa92543",
    ),
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-resolved.html": (
        45_777,
        "d48e208611a080220e5b3b884ff733702c4553b67105b197728ba8f8e453a64f",
    ),
    "data/capstones/CP02/witnesses/dryad-reuse-guide.html": (
        18_229,
        "a132d3541d7edd5f1bc0b7eb25aaff540e7536b9113f6811101bbb34299e87e9",
    ),
    "data/capstones/CP02/witnesses/file-2765112.json": (
        620,
        "2aea32ad275de7b69df068119eb55357dedf8bc49e0efdcdf421f80e1c75b021",
    ),
    "data/capstones/CP02/witnesses/file-2765118.json": (
        617,
        "14a7f7e510f5770bfdc5af267ca04316ee4952c32a4802f0f189f0c06c7676ec",
    ),
    "data/capstones/CP02/witnesses/version-268230-files.json": (
        4_517,
        "c2b8c7e77f5f2a591cca3a4e904b180877833ccbd426cfef7bb2841830abfb34",
    ),
    "data/capstones/CP02/witnesses/version-268230.json": (
        4_718,
        "8f40dea26fcd64a3c0fac26467ada54bce1818b427f2317519e400b4785d0331",
    ),
    "environment.lock.json": (
        429,
        "5fe445dbaa2456f4b60ee69dfa0842cefdfed7d2cfd02784472918a51d8fd5c3",
    ),
    "LICENSE.md": (
        2_213,
        "7143863ecddf588c1be53a3b37cdcba498177b10f7623ddd01909b0392f299a9",
    ),
    "scripts/build_companion.py": (
        88_390,
        "aa8525e715f2cfd69d868d3713295c62344e24847e90d552424390449f1059a2",
    ),
    "scripts/qa_companion.py": (
        58_041,
        "f56ee4f7a1a5901a2a4892f70ec861bad51678a8e4646e90847fc596bbc94722",
    ),
    "simulations/run_c1_simulations.py": (
        20_460,
        "f5f98c9ad4a029e5f2633ab04e4a31c786f1f85facd7d88176059831ed5cb450",
    ),
    "simulations/run_c2_simulations.py": (
        14_340,
        "b5e8f3ccc6e7fbc9a8e3808eeee4bbc498cb14a525241a39b4beed53df127ab2",
    ),
    "simulations/run_c3_simulations.py": (
        24_333,
        "52f92a16b523e7d72dc5800d18eb2275777c59f161f1afb6ee8420fc67701a72",
    ),
}

REQUIRED_C5_ROOT_SUPPORT_INPUTS = {
    "LICENSE.md",
    "00_control/RIGHTS_AND_COMPONENTS.md",
    "scripts/hydrate_cp02_coverage.py",
    "scripts/package_c140_companion_c1_release.py",
    "components/c140-companion/00_control/CONTENT_CONTRACT.md",
    "components/c140-companion/00_control/WORKFLOW.md",
    "components/c140-companion/00_control/C2_MATRIX_BATCH_CONTRACT.md",
    "components/c140-companion/00_control/C3_BAYESIAN_COMPARISON_BATCH_CONTRACT.md",
    "components/c140-companion/00_control/C4_MASTERY_BATCH_CONTRACT.md",
    "components/c140-companion/00_control/C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md",
}
FROZEN_C5_ROOT_SUPPORT_INPUTS: dict[str, tuple[int, str]] = {
    "00_control/RIGHTS_AND_COMPONENTS.md": (
        3_557,
        "c4202f9fd10339b430f810193847d36db60ddb58be691011798abb6deb79ae92",
    ),
    "components/c140-companion/00_control/C2_MATRIX_BATCH_CONTRACT.md": (
        2_291,
        "dc35205d96af469789d63b9496e24c7ecec19964bbe3cf4f0640410a1e3abf75",
    ),
    "components/c140-companion/00_control/C3_BAYESIAN_COMPARISON_BATCH_CONTRACT.md": (
        2_732,
        "3a393b508d59b695f2450a1a7396b9c927c9d46a7e41ee269aeffc50326d15d7",
    ),
    "components/c140-companion/00_control/C4_MASTERY_BATCH_CONTRACT.md": (
        2_246,
        "bf4196d397f8e038d1ed70b0aab6ff1a9d9c0a5689d64c76cee2352ccd446771",
    ),
    "components/c140-companion/00_control/C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md": (
        8_647,
        "0c03be892981d49edfceba6645f4327d04b79602ce143794e51510efdc11d56d",
    ),
    "components/c140-companion/00_control/CONTENT_CONTRACT.md": (
        1_388,
        "d54194f43ad496ad67b6be46365ae1bef47c14f72f8f273c7012359ca4267a0e",
    ),
    "components/c140-companion/00_control/WORKFLOW.md": (
        5_269,
        "2611252a1d69a42119713c372c15a9230e07dfee1d8df5408d71b717e3d05aa9",
    ),
    "LICENSE.md": (
        4_356,
        "7b8d94baedb054c6b705b0c345fbd8d27c489ca95e6251cb64c70cef7687d965",
    ),
    "scripts/hydrate_cp02_coverage.py": (
        6_085,
        "2ed11ef418ab05c5e9791f75ddb064c93a5dc2351bcdc89c6e4071baf59ece4e",
    ),
    "scripts/package_c140_companion_c1_release.py": (
        19_180,
        "b1b308f15081b3ecb8e2702b93055a01dc7f7f2d19d2e7c183a3a8e41688adf3",
    ),
}

REQUIRED_C5_REPOSITORY_CONTEXT_INPUTS = {
    "00_control/RIGHTS_AND_COMPONENTS.md",
    "backend/through_lesson12_documents.jsonl",
    "build/html-id/assets/MathJax/input/tex/extensions/boldsymbol.js",
    "build/html-id/assets/MathJax/input/tex/extensions/cancel.js",
    "build/html-id/assets/MathJax/input/tex/extensions/color.js",
    "build/html-id/assets/MathJax/input/tex/extensions/enclose.js",
    "build/html-id/assets/MathJax/tex-svg.js",
    "build/html-id/licenses/MathJax-3.1.2-LICENSE.txt",
    "components/random-completeness/backend/adverse_records.jsonl",
    "components/random-completeness/backend/entities.jsonl",
    "components/random-completeness/LICENSE_AND_ATTRIBUTION.md",
    "components/random-completeness/source/id-ID/random/point/Sufficient.html",
    "LICENSE.md",
}
FROZEN_C5_REPOSITORY_CONTEXT_INPUTS: dict[str, tuple[int, str]] = {
    "00_control/RIGHTS_AND_COMPONENTS.md": (
        3_557,
        "c4202f9fd10339b430f810193847d36db60ddb58be691011798abb6deb79ae92",
    ),
    "backend/through_lesson12_documents.jsonl": (
        9_446,
        "fa1f2fe90748937ec3760dfd625255fd2d683be006b4ad990b0b4d273701689f",
    ),
    "build/html-id/assets/MathJax/input/tex/extensions/boldsymbol.js": (
        4_709,
        "716cf8735d00abfb1627f8adbbf4aeb915ac9b5c55d47aeaf276e73dac6a2aa1",
    ),
    "build/html-id/assets/MathJax/input/tex/extensions/cancel.js": (
        4_029,
        "6b5ede35a63fb92d69e0648755746867efdbaebbf452506ebd878c33568aadf0",
    ),
    "build/html-id/assets/MathJax/input/tex/extensions/color.js": (
        9_192,
        "412863c1ea3db035795f39a6850f963261b81d260de61862c85013b2c96c01d7",
    ),
    "build/html-id/assets/MathJax/input/tex/extensions/enclose.js": (
        3_071,
        "fed0d0fca9402ad9f23bba26a158cc6a802a267f900c238769e16ed30b4410ab",
    ),
    "build/html-id/assets/MathJax/tex-svg.js": (
        1_704_911,
        "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a",
    ),
    "build/html-id/licenses/MathJax-3.1.2-LICENSE.txt": (
        11_358,
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    ),
    "components/random-completeness/backend/adverse_records.jsonl": (
        9_584,
        "aa99bbd7e97f77f6f5663b557bc65ab9425b5b5c5d486d875a67d9215552a007",
    ),
    "components/random-completeness/backend/entities.jsonl": (
        566_058,
        "abe158a6c768cd96a299ea6cb7c26ce66ad8ebb07afd853cd1ae689abdd2e007",
    ),
    "components/random-completeness/LICENSE_AND_ATTRIBUTION.md": (
        2_197,
        "d6aad0f8d75ef1083b5fc7d7dc3c50282e093d24e9ea45f75466eb5cc7c8b66b",
    ),
    "components/random-completeness/source/id-ID/random/point/Sufficient.html": (
        60_900,
        "18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197",
    ),
    "LICENSE.md": (
        4_356,
        "7b8d94baedb054c6b705b0c345fbd8d27c489ca95e6251cb64c70cef7687d965",
    ),
}


EXPECTED_DOCUMENT_IDS = {
    "O006-C140-CMP-INDEX",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 14)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 7)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(0, 13)),
    *(f"O006-C140-CMP-CA{i:02d}" for i in range(1, 5)),
    *(f"O006-C140-CMP-CP{i:02d}" for i in range(1, 3)),
}
EXPECTED_DOCUMENTS = 39
EXPECTED_PROBLEMS = 146
EXPECTED_SIMULATIONS = 6
EXPECTED_ASSESSMENTS = 4
EXPECTED_CAPSTONES = 2
CP02_ANALYSIS_SCHEMA = "o006.c140.cp02-analysis.v1"

TEXT_SUFFIXES = {
    ".css",
    ".csv",
    ".htm",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".ipynb",
    ".bib",
    ".lock",
    ".md",
    ".py",
    ".qmd",
    ".rst",
    ".sql",
    ".svg",
    ".tex",
    ".toml",
    ".tsv",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
STRICT_PRIVACY_PATTERNS = {
    "windows_user_path": re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]+", re.I),
    "unix_home_path": re.compile(rb"/(?:home|Users)/[A-Za-z0-9._-]+/"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "credential_assignment": re.compile(
        rb"(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)"
        rb"\s*[:=]\s*[\"']?[^\s<\"']{8,}",
        re.I,
    ),
    "authorization_bearer": re.compile(
        rb"Authorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I
    ),
    "github_token": re.compile(
        rb"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{10,}"
    ),
    "url_credential": re.compile(
        rb"[?&](?:access_token|api_key|apikey|token|password|secret)="
        rb"[^&#\s]{8,}",
        re.I,
    ),
    "email_address": re.compile(
        rb"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    ),
}

# These exact upstream evidence files deliberately preserve public contact
# addresses printed by the dataset publisher or Creative Commons.  Their
# identities are frozen below before packaging.  Email detection remains
# strict everywhere else, including all authored source, generated output,
# receipts, manifests, and release metadata.
PUBLIC_SOURCE_EMAIL_ALLOWLIST = {
    "data/capstones/CP01/raw/archive/Concrete_Readme.txt": (
        "data/capstones/CP01/raw/archive/Concrete_Readme.txt"
    ),
    "data/capstones/CP01/witnesses/cc-by-4.0-legalcode.html": (
        "data/capstones/CP01/witnesses/cc-by-4.0-legalcode.html"
    ),
    "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-resolved.html": (
        "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-resolved.html"
    ),
    "data/capstones/CP01/witnesses/uci-dataset-165-record.html": (
        "data/capstones/CP01/witnesses/uci-dataset-165-record.html"
    ),
    "data/capstones/CP02/witnesses/cc0-1.0-legalcode.html": (
        "data/capstones/CP02/witnesses/cc0-1.0-legalcode.html"
    ),
    "data/capstones/CP02/witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json": (
        "data/capstones/CP02/witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json"
    ),
    "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redacted.html": (
        "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redacted.html"
    ),
    "data/capstones/CP02/witnesses/version-268230.json": (
        "data/capstones/CP02/witnesses/version-268230.json"
    ),
    "backend/source/capstones/CP01/data/raw/archive/Concrete_Readme.txt": (
        "data/capstones/CP01/raw/archive/Concrete_Readme.txt"
    ),
    "backend/source/capstones/CP01/data/witnesses/cc-by-4.0-legalcode.html": (
        "data/capstones/CP01/witnesses/cc-by-4.0-legalcode.html"
    ),
    "backend/source/capstones/CP01/data/witnesses/doi-10.24432-C5PK67-resolved.html": (
        "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-resolved.html"
    ),
    "backend/source/capstones/CP01/data/witnesses/uci-dataset-165-record.html": (
        "data/capstones/CP01/witnesses/uci-dataset-165-record.html"
    ),
    "backend/source/capstones/CP02/data/witnesses/cc0-1.0-legalcode.html": (
        "data/capstones/CP02/witnesses/cc0-1.0-legalcode.html"
    ),
    "backend/source/capstones/CP02/data/witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json": (
        "data/capstones/CP02/witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json"
    ),
    "backend/source/capstones/CP02/data/witnesses/doi-10.5061-dryad.573n5tbf3-redacted.html": (
        "data/capstones/CP02/witnesses/doi-10.5061-dryad.573n5tbf3-redacted.html"
    ),
    "backend/source/capstones/CP02/data/witnesses/version-268230.json": (
        "data/capstones/CP02/witnesses/version-268230.json"
    ),
}

CP02_CREDENTIAL_BEARING_WITNESS = (
    "data/capstones/CP02/witnesses/"
    "doi-10.5061-dryad.573n5tbf3-resolved.html"
)
CP02_REDACTED_WITNESS = (
    "data/capstones/CP02/witnesses/"
    "doi-10.5061-dryad.573n5tbf3-redacted.html"
)
CP02_REDACTION_RECEIPT = (
    "data/capstones/CP02/witnesses/"
    "doi-10.5061-dryad.573n5tbf3-redistribution-redaction.json"
)
CP02_COVERAGE_RAW = "CP02_coverage.csv"
CP02_COVERAGE_GZIP = "assets/capstones/CP02/CP02_coverage.csv.gz"


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def csv_bytes(fieldnames: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def assert_bounded_nonreparse(path: Path, *, label: str) -> None:
    try:
        relative = path.absolute().relative_to(ROOT.absolute())
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes the repository boundary") from exc
    if any(
        ":" in part or any(ord(character) < 32 for character in part)
        for part in relative.parts
    ):
        raise RuntimeError(f"{label} has an unsafe local path component")
    current = ROOT
    if is_reparse(current):
        raise RuntimeError("repository root is a reparse point")
    for part in relative.parts:
        current = current / part
        if is_reparse(current):
            raise RuntimeError(f"{label} traverses a reparse point")


def stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        int(value.st_dev),
        int(value.st_ino),
        int(value.st_mode),
        int(value.st_size),
        int(value.st_mtime_ns),
        int(getattr(value, "st_file_attributes", 0)),
    )


def validate_regular_stat(
    value: os.stat_result, *, label: str, max_bytes: int
) -> None:
    if not stat.S_ISREG(value.st_mode):
        raise RuntimeError(f"missing or unsafe {label}")
    if int(getattr(value, "st_file_attributes", 0)) & int(
        getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise RuntimeError(f"reparse-point {label}")
    if value.st_size < 0 or value.st_size > max_bytes:
        raise RuntimeError(f"{label} exceeds the bounded read limit")


def validate_directory_stat(value: os.stat_result, *, label: str) -> None:
    if not stat.S_ISDIR(value.st_mode):
        raise RuntimeError(f"missing or unsafe {label}")
    if int(getattr(value, "st_file_attributes", 0)) & int(
        getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise RuntimeError(f"reparse-point {label}")


def safe_read_file(
    path: Path, *, label: str, max_bytes: int = MAX_INPUT_FILE_BYTES
) -> bytes:
    """Take one bounded, regular-file, non-reparse snapshot.

    The path chain and target identity are checked before and after the opened
    handle is read.  This closes the check/open and replacement windows that a
    separate ``is_file()`` followed by ``read_bytes()`` would leave open.
    """

    assert_bounded_nonreparse(path, label=label)
    try:
        before = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"missing or unsafe {label}") from exc
    validate_regular_stat(before, label=label, max_bytes=max_bytes)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_BINARY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        handle = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"cannot open {label}") from exc
    try:
        opened = os.fstat(handle)
        validate_regular_stat(opened, label=label, max_bytes=max_bytes)
        if stat_identity(opened) != stat_identity(before):
            raise RuntimeError(f"{label} changed while opening")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(handle, min(1_048_576, max_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"{label} exceeds the bounded read limit")
        after_handle = os.fstat(handle)
        if stat_identity(after_handle) != stat_identity(opened):
            raise RuntimeError(f"{label} changed while reading")
    finally:
        os.close(handle)
    assert_bounded_nonreparse(path, label=label)
    try:
        after_path = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"{label} disappeared while reading") from exc
    validate_regular_stat(after_path, label=label, max_bytes=max_bytes)
    if stat_identity(after_path) != stat_identity(opened):
        raise RuntimeError(f"{label} was replaced while reading")
    payload = b"".join(chunks)
    if len(payload) != opened.st_size:
        raise RuntimeError(f"{label} byte count changed while reading")
    return payload


def safe_files_from_directory(root: Path, prefix: str = "") -> dict[str, bytes]:
    assert_bounded_nonreparse(root, label="package input directory")
    try:
        root_before = root.lstat()
    except OSError as exc:
        raise RuntimeError("missing or unsafe package input directory") from exc
    validate_directory_stat(root_before, label="package input directory")
    result: dict[str, bytes] = {}
    total_bytes = 0

    def visit(directory: Path, relative_parent: Path) -> None:
        nonlocal total_bytes
        assert_bounded_nonreparse(directory, label="package input directory")
        try:
            before = directory.lstat()
        except OSError as exc:
            raise RuntimeError("missing package input directory") from exc
        validate_directory_stat(before, label="package input directory")
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            try:
                entry_stat = path.lstat()
            except OSError as exc:
                raise RuntimeError("package input entry disappeared") from exc
            if int(getattr(entry_stat, "st_file_attributes", 0)) & int(
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            ) or stat.S_ISLNK(entry_stat.st_mode):
                raise RuntimeError("reparse point in package input directory")
            relative = relative_parent / path.name
            if stat.S_ISDIR(entry_stat.st_mode):
                visit(path, relative)
            elif stat.S_ISREG(entry_stat.st_mode):
                local = relative.as_posix()
                name = f"{prefix}/{local}" if prefix else local
                shared.validate_relative(name)
                if len(result) >= MAX_SNAPSHOT_FILES:
                    raise RuntimeError("package input directory exceeds the file-count cap")
                payload = safe_read_file(path, label="package input file")
                total_bytes += len(payload)
                if total_bytes > MAX_SNAPSHOT_BYTES:
                    raise RuntimeError("package input directory exceeds the byte cap")
                result[name] = payload
            else:
                raise RuntimeError("non-file entry in package input directory")
        assert_bounded_nonreparse(directory, label="package input directory")
        try:
            after = directory.lstat()
        except OSError as exc:
            raise RuntimeError("package input directory disappeared") from exc
        validate_directory_stat(after, label="package input directory")
        if stat_identity(after) != stat_identity(before):
            raise RuntimeError("package input directory changed while enumerating")

    visit(root, Path())
    assert_bounded_nonreparse(root, label="package input directory")
    try:
        root_after = root.lstat()
    except OSError as exc:
        raise RuntimeError("package input directory disappeared") from exc
    validate_directory_stat(root_after, label="package input directory")
    if stat_identity(root_after) != stat_identity(root_before):
        raise RuntimeError("package input directory changed while snapshotting")
    return result


def validate_portable_relative(name: str) -> str:
    """Validate a deterministic, cross-platform ZIP/publication member name.

    The returned key models case-insensitive NFC extraction so aliases that are
    distinct in a POSIX ZIP but overwrite one another on common reader systems
    can be rejected before an archive or publication inventory is produced.
    """

    shared.validate_relative(name)
    if unicodedata.normalize("NFC", name) != name:
        raise RuntimeError(f"non-NFC archive path: {name}")
    encoded = name.encode("utf-8")
    if len(encoded) > 65_535:
        raise RuntimeError(f"archive path exceeds the ZIP name limit: {name}")
    for component in name.split("/"):
        if (
            component.endswith((" ", "."))
            or any(ord(character) < 32 for character in component)
            or any(character in '<>:"\\|?*' for character in component)
            or component.split(".", 1)[0].upper() in WINDOWS_RESERVED_COMPONENTS
        ):
            raise RuntimeError(f"non-portable archive path: {name}")
    return unicodedata.normalize("NFC", name).casefold()


def validate_portable_namespace(names: list[str], *, label: str) -> None:
    seen: dict[str, str] = {}
    for name in names:
        key = validate_portable_relative(name)
        prior = seen.get(key)
        if prior is not None:
            raise RuntimeError(
                f"{label} has a case/normalization collision: {prior} / {name}"
            )
        seen[key] = name


def read_identity(
    path: Path, expected_bytes: int, expected_sha256: str, label: str
) -> bytes:
    payload = safe_read_file(path, label=label)
    if len(payload) != expected_bytes or sha256(payload) != expected_sha256:
        raise RuntimeError(f"{label} identity differs")
    return payload


def json_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def privacy_findings(name: str, payload: bytes) -> list[str]:
    suffix = Path(name).suffix.casefold()
    if suffix not in TEXT_SUFFIXES:
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError:
            return []
    findings = {
        label for label, pattern in STRICT_PRIVACY_PATTERNS.items() if pattern.search(payload)
    }
    public_origin = PUBLIC_SOURCE_EMAIL_ALLOWLIST.get(name)
    public_identity = (
        FROZEN_C5_SUPPORT_INPUTS.get(public_origin)
        if public_origin is not None
        else None
    )
    if (
        public_identity is not None
        and len(payload) == public_identity[0]
        and sha256(payload) == public_identity[1]
    ):
        findings.discard("email_address")
    local_account = Path.home().name.encode("utf-8", errors="ignore").lower()
    if len(local_account) >= 3 and local_account in payload.lower():
        findings.add("local_account_name")
    findings.update(shared.privacy_findings(name, payload))
    return sorted(findings)


def redact_cp02_public_client_key(payload: bytes) -> tuple[bytes, bytes]:
    """Remove the public-page client key from the redistribution derivative.

    The exact upstream landing-page bytes remain frozen and validated locally,
    but credential-like material is never copied into a release archive.  The
    derivative receives a distinct filename and an identity-only receipt.
    """

    pattern = STRICT_PRIVACY_PATTERNS["credential_assignment"]
    matches = list(pattern.finditer(payload))
    if len(matches) != 1 or not matches[0].group(0).lstrip().lower().startswith(
        b"apikey"
    ):
        raise RuntimeError("CP02 public-page credential redaction contract differs")
    redacted = (
        payload[: matches[0].start()]
        + b"redactedClientField: ''"
        + payload[matches[0].end() :]
    )
    remaining = privacy_findings(CP02_REDACTED_WITNESS, redacted)
    if remaining:
        raise RuntimeError(
            f"CP02 redacted witness still has privacy findings: {remaining}"
        )
    receipt = canonical_json(
        {
            "derivative": {
                "bytes": len(redacted),
                "path": CP02_REDACTED_WITNESS,
                "sha256": sha256(redacted),
            },
            "excluded_original": {
                "bytes": len(payload),
                "path": CP02_CREDENTIAL_BEARING_WITNESS,
                "sha256": sha256(payload),
            },
            "redactions": [
                {
                    "count": 1,
                    "field": "apiKey",
                    "reason": "credential-like public client key excluded from redistribution",
                }
            ],
            "schema": "o006.c140.cp02-witness-redaction.v1",
            "status": "pass",
        }
    )
    return redacted, receipt


def deterministic_zip(
    entries: dict[str, bytes], *, inventory_name: str
) -> tuple[bytes, dict[str, Any]]:
    if inventory_name in entries:
        raise RuntimeError(f"inventory collision: {inventory_name}")
    if len(entries) + 1 > MAX_ZIP_MEMBERS:
        raise RuntimeError(f"archive has too many members: {inventory_name}")
    validate_portable_namespace(
        [*entries, inventory_name], label=f"archive {inventory_name}"
    )
    inventory_rows: list[dict[str, object]] = []
    findings: list[dict[str, str]] = []
    for name, payload in sorted(entries.items()):
        inventory_rows.append(
            {"entry": name, "bytes": len(payload), "sha256": sha256(payload)}
        )
        for finding in privacy_findings(name, payload):
            findings.append({"entry": name, "finding": finding})
    if findings:
        raise RuntimeError(f"privacy findings in archive inputs: {findings}")
    inventory_payload = canonical_json(
        {
            "entries": inventory_rows,
            "entry_count": len(inventory_rows),
            "schema": "o006.c140.companion-c5-archive-inventory.v1",
            "status": "pass",
            "total_bytes": sum(int(row["bytes"]) for row in inventory_rows),
        }
    )
    combined = dict(entries)
    combined[inventory_name] = inventory_payload
    uncompressed_bytes = sum(len(value) for value in combined.values())
    # ZIP_STORED cannot make the payload smaller.  Bound the exact member bytes
    # and a conservative local/central-directory overhead before allocating the
    # in-memory archive, then enforce the actual serialized size below.
    estimated_stored_bytes = (
        uncompressed_bytes
        + 22
        + sum(76 + 2 * len(name.encode("utf-8")) for name in combined)
    )
    if (
        uncompressed_bytes > MAX_PUBLIC_FILE_BYTES
        or estimated_stored_bytes > MAX_PUBLIC_FILE_BYTES
    ):
        raise RuntimeError(f"archive exceeds the public-file cap: {inventory_name}")
    stream = io.BytesIO()
    with zipfile.ZipFile(
        stream,
        "w",
        compression=zipfile.ZIP_STORED,
        allowZip64=False,
        strict_timestamps=True,
    ) as archive:
        for name, payload in sorted(combined.items()):
            info = zipfile.ZipInfo(name, shared.ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.flag_bits |= 0x800
            archive.writestr(info, payload, compress_type=zipfile.ZIP_STORED)
    payload = stream.getvalue()
    if len(payload) > MAX_PUBLIC_FILE_BYTES:
        raise RuntimeError(f"archive exceeds the public-file cap: {inventory_name}")
    with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
        infos = archive.infolist()
        if [info.filename for info in infos] != sorted(combined):
            raise RuntimeError(f"archive order differs: {inventory_name}")
        if len(infos) != len(combined):
            raise RuntimeError(f"archive member count differs: {inventory_name}")
        for info in infos:
            name = info.filename
            if (
                info.compress_type != zipfile.ZIP_STORED
                or info.date_time != shared.ZIP_TIMESTAMP
                or info.create_system != 3
                or (info.external_attr >> 16) != 0o100644
                or info.file_size != len(combined[name])
                or info.compress_size != len(combined[name])
                or info.flag_bits not in {0, 0x800}
            ):
                raise RuntimeError(f"archive metadata differs: {name}")
            if archive.read(name) != combined[name]:
                raise RuntimeError(f"archive payload differs: {name}")
        if archive.testzip() is not None:
            raise RuntimeError(f"archive CRC verification failed: {inventory_name}")
    return payload, {
        "archive_method": (
            "ZIP_STORED; fixed 1980-01-01 timestamps; canonical entry order; "
            "independent of zlib compression-version output"
        ),
        "bytes": len(payload),
        "entries": len(combined),
        "inventory": {
            "entry": inventory_name,
            "bytes": len(inventory_payload),
            "sha256": sha256(inventory_payload),
        },
        "privacy": {"forbidden_markers_found": 0},
        "sha256": sha256(payload),
        "uncompressed_bytes": uncompressed_bytes,
    }


def merge_unique(
    target: dict[str, bytes], incoming: dict[str, bytes], *, label: str
) -> None:
    for name, payload in incoming.items():
        if name in target:
            raise RuntimeError(f"{label} entry collision: {name}")
        target[name] = payload


def directory_identity(root: Path) -> tuple[int, int]:
    entries = safe_files_from_directory(root)
    return len(entries), sum(len(payload) for payload in entries.values())


def validate_base_public_union() -> tuple[
    dict[str, bytes], list[dict[str, Any]], dict[str, Any]
]:
    receipt_payload = read_identity(
        BASE_PACKAGE_RECEIPT,
        BASE_PACKAGE_RECEIPT_BYTES,
        BASE_PACKAGE_RECEIPT_SHA256,
        "C4 package receipt",
    )
    readback_payload = read_identity(
        BASE_PUBLIC_READBACK,
        BASE_PUBLIC_READBACK_BYTES,
        BASE_PUBLIC_READBACK_SHA256,
        "C4 anonymous public readback",
    )
    receipt = json_object(receipt_payload, "C4 package receipt")
    readback = json_object(readback_payload, "C4 public readback")
    publication = receipt.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    gates = receipt.get("gates")
    execution = receipt.get("packager")
    lineage = receipt.get("lineage")
    if (
        receipt.get("schema") != BASE_SCHEMA
        or receipt.get("status") != "ready"
        or receipt.get("version") != BASE_VERSION
        or not isinstance(rows, list)
        or not all(isinstance(row, dict) for row in rows)
        or len(rows) != BASE_FILE_COUNT
        or publication.get("file_count") != BASE_FILE_COUNT
        or publication.get("bytes") != BASE_TOTAL_BYTES
        or not isinstance(gates, dict)
        or not isinstance(execution, dict)
        or execution.get("browser_processes_used") is not False
        or execution.get("credential_access") is not False
        or execution.get("git_operations") is not False
        or execution.get("network_access") is not False
        or execution.get("publication_side_effects") is not False
        or not isinstance(lineage, dict)
        or lineage.get("concept_record_id") != CONCEPT_RECORD_ID
        or lineage.get("concept_doi") != CONCEPT_DOI
    ):
        raise RuntimeError("C4 package contract differs")

    public = readback.get("public")
    public_rows = public.get("files") if isinstance(public, dict) else None
    if (
        readback.get("schema") != BASE_READBACK_SCHEMA
        or readback.get("version") != BASE_VERSION
        or readback.get("credential_access") is not False
        or not isinstance(public, dict)
        or public.get("anonymous_readback") is not True
        or public.get("reader_first") is not True
        or public.get("record_id") != BASE_RECORD_ID
        or public.get("doi") != BASE_RECORD_DOI
        or public.get("concept_record_id") != CONCEPT_RECORD_ID
        or public.get("concept_doi") != CONCEPT_DOI
        or public.get("version") != BASE_VERSION
        or public.get("file_count") != BASE_FILE_COUNT
        or public.get("total_bytes") != BASE_TOTAL_BYTES
        or not isinstance(public_rows, list)
        or len(public_rows) != BASE_FILE_COUNT
    ):
        raise RuntimeError("C4 public readback contract differs")

    outputs: dict[str, bytes] = {}
    publication_names = [str(row.get("filename", "")) for row in rows]
    validate_portable_namespace(publication_names, label="inherited C4 publication")
    for expected_order, (row, public_row) in enumerate(
        zip(rows, public_rows, strict=True), start=1
    ):
        name = str(row.get("filename", ""))
        path = RELEASE / name
        payload = safe_read_file(path, label=f"inherited public asset {name}")
        if (
            row.get("upload_order") != expected_order
            or row.get("source_path") != f"release/{name}"
            or len(payload) != row.get("bytes")
            or sha256(payload) != row.get("sha256")
            or not isinstance(public_row, dict)
            or public_row.get("name") != name
            or public_row.get("bytes") != row.get("bytes")
            or public_row.get("sha256") != row.get("sha256")
            or name in outputs
        ):
            raise RuntimeError(f"inherited public identity/order differs: {name}")
        outputs[name] = payload

    if (
        sum(len(payload) for payload in outputs.values()) != BASE_TOTAL_BYTES
        or sum(int(row["bytes"]) for row in rows) != BASE_TOTAL_BYTES
    ):
        raise RuntimeError("inherited C4 cumulative byte census differs")

    if (
        rows[0].get("filename")
        != "00_00_stat415-pengantar-statistika-matematis-id.pdf"
        or rows[0].get("primary_reader") is not True
        or rows[0].get("media_type") != "application/pdf"
        or rows[1].get("filename")
        != "00_01_stat415-pengantar-statistika-matematis-id.epub"
        or rows[1].get("media_type") != "application/epub+zip"
    ):
        raise RuntimeError("reader-first PDF/EPUB order differs")
    return outputs, [dict(row) for row in rows], {
        "package_receipt": receipt_payload,
        "public_readback": readback_payload,
        "public_readback_json": readback,
    }


def require_frozen_c5_contract() -> None:
    if set(FROZEN_C5_REPOSITORY_CONTEXT_INPUTS) != REQUIRED_C5_REPOSITORY_CONTEXT_INPUTS:
        raise RuntimeError("C5 repository-context input closure differs")
    if set(FROZEN_C5_SIMULATION_INPUT_OVERRIDES) != {
        "build/C1_SIMULATION_RECEIPT.json",
        "build/C2_SIMULATION_RECEIPT.json",
    } or set(FROZEN_C5_SIMULATION_MANIFEST_OVERRIDES) != {
        "generated/simulations/c1/MANIFEST.csv",
        "generated/simulations/c2/MANIFEST.csv",
    }:
        raise RuntimeError("C5 current simulation override closure differs")
    missing_inputs = sorted(REQUIRED_C5_INPUTS - FROZEN_C5_INPUTS.keys())
    extra_inputs = sorted(FROZEN_C5_INPUTS.keys() - REQUIRED_C5_INPUTS)
    missing_manifests = sorted(REQUIRED_C5_MANIFESTS - FROZEN_C5_MANIFESTS.keys())
    extra_manifests = sorted(FROZEN_C5_MANIFESTS.keys() - REQUIRED_C5_MANIFESTS)
    missing_support = sorted(
        REQUIRED_C5_SUPPORT_INPUTS - FROZEN_C5_SUPPORT_INPUTS.keys()
    )
    extra_support = sorted(
        FROZEN_C5_SUPPORT_INPUTS.keys() - REQUIRED_C5_SUPPORT_INPUTS
    )
    missing_root_support = sorted(
        REQUIRED_C5_ROOT_SUPPORT_INPUTS - FROZEN_C5_ROOT_SUPPORT_INPUTS.keys()
    )
    extra_root_support = sorted(
        FROZEN_C5_ROOT_SUPPORT_INPUTS.keys() - REQUIRED_C5_ROOT_SUPPORT_INPUTS
    )
    if not CP02_ANALYSIS_SCHEMA:
        raise RuntimeError("C5 input contract is not frozen: CP02 analysis schema pending")
    missing_email_origins = sorted(
        set(PUBLIC_SOURCE_EMAIL_ALLOWLIST.values())
        - FROZEN_C5_SUPPORT_INPUTS.keys()
    )
    if (
        missing_inputs
        or extra_inputs
        or missing_manifests
        or extra_manifests
        or missing_support
        or extra_support
        or missing_root_support
        or extra_root_support
        or missing_email_origins
    ):
        raise RuntimeError(
            "C5 input contract is not frozen: "
            f"missing_inputs={missing_inputs}; extra_inputs={extra_inputs}; "
            f"missing_manifests={missing_manifests}; extra_manifests={extra_manifests}; "
            f"missing_support={missing_support}; extra_support={extra_support}; "
            f"missing_root_support={missing_root_support}; "
            f"extra_root_support={extra_root_support}; "
            f"missing_email_origins={missing_email_origins}"
        )
    for group_name, identities in (
        ("input", FROZEN_C5_INPUTS),
        ("manifest", FROZEN_C5_MANIFESTS),
        ("support", FROZEN_C5_SUPPORT_INPUTS),
        ("root support", FROZEN_C5_ROOT_SUPPORT_INPUTS),
        ("repository context", FROZEN_C5_REPOSITORY_CONTEXT_INPUTS),
        ("current simulation receipt", FROZEN_C5_SIMULATION_INPUT_OVERRIDES),
        ("current simulation manifest", FROZEN_C5_SIMULATION_MANIFEST_OVERRIDES),
    ):
        for relative, identity in identities.items():
            if (
                not isinstance(identity, tuple)
                or len(identity) != 2
                or not isinstance(identity[0], int)
                or identity[0] <= 0
                or identity[0] > MAX_INPUT_FILE_BYTES
                or not isinstance(identity[1], str)
                or re.fullmatch(r"[0-9a-f]{64}", identity[1]) is None
            ):
                raise RuntimeError(f"invalid frozen C5 {group_name} identity: {relative}")


def validate_frozen_files(
    identities: dict[str, tuple[int, str]], *, label: str, base: Path = COMPONENT
) -> tuple[dict[str, dict[str, object]], dict[str, bytes]]:
    result: dict[str, dict[str, object]] = {}
    payloads: dict[str, bytes] = {}
    for relative, (expected_bytes, expected_hash) in identities.items():
        payload = read_identity(
            base / relative,
            expected_bytes,
            expected_hash,
            f"{label} {relative}",
        )
        result[relative] = {"bytes": len(payload), "sha256": sha256(payload)}
        payloads[relative] = payload
    return result, payloads


def bool_map_all_true(value: object, label: str) -> None:
    if not isinstance(value, dict) or not value or any(item is not True for item in value.values()):
        raise RuntimeError(f"{label} assertion map differs")


def verify_receipt_rows(
    rows: object,
    *,
    base: Path,
    label: str,
    path_prefix: str = "",
) -> set[str]:
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"{label} rows are missing")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError(f"{label} row is malformed")
        relative = str(row.get("path", ""))
        shared.validate_relative(relative)
        if relative in seen:
            raise RuntimeError(f"duplicate {label} row: {relative}")
        seen.add(relative)
        local = relative
        if path_prefix:
            if not relative.startswith(path_prefix):
                raise RuntimeError(f"{label} prefix differs: {relative}")
            local = relative[len(path_prefix) :]
        path = base / local
        payload = safe_read_file(path, label=f"{label} payload {relative}")
        if len(payload) != row.get("bytes") or sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"{label} payload identity differs: {relative}")
    return seen


def verify_rows_against_snapshot(
    rows: object,
    *,
    snapshot: dict[str, bytes],
    label: str,
    path_prefix: str = "",
) -> set[str]:
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"{label} rows are missing")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError(f"{label} row is malformed")
        relative = str(row.get("path", ""))
        shared.validate_relative(relative)
        local = relative
        if path_prefix:
            if not relative.startswith(path_prefix):
                raise RuntimeError(f"{label} prefix differs: {relative}")
            local = relative[len(path_prefix) :]
        shared.validate_relative(local)
        if local in seen:
            raise RuntimeError(f"duplicate {label} row: {relative}")
        seen.add(local)
        payload = snapshot.get(local)
        if payload is None:
            raise RuntimeError(f"missing {label} snapshot payload: {relative}")
        if len(payload) != row.get("bytes") or sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"{label} snapshot identity differs: {relative}")
    return seen


def capture_manifest_directory(
    *,
    root: Path,
    manifest_payload: bytes,
    label: str,
    path_prefix: str = "",
    path_field: str = "path",
    allowed_unlisted: set[str] | None = None,
) -> dict[str, bytes]:
    try:
        text = manifest_payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{label} manifest is not UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames is None or not {path_field, "bytes", "sha256"}.issubset(reader.fieldnames):
        raise RuntimeError(f"{label} manifest header differs")
    rows = list(reader)
    if not rows:
        raise RuntimeError(f"{label} manifest is empty")
    snapshot = safe_files_from_directory(root)
    listed: set[str] = set()
    for row in rows:
        relative = str(row.get(path_field, ""))
        shared.validate_relative(relative)
        local = relative
        if path_prefix:
            if not relative.startswith(path_prefix):
                raise RuntimeError(f"{label} manifest prefix differs: {relative}")
            local = relative[len(path_prefix) :]
        shared.validate_relative(local)
        if local in listed:
            raise RuntimeError(f"duplicate {label} manifest path: {relative}")
        listed.add(local)
        payload = snapshot.get(local)
        if payload is None:
            raise RuntimeError(f"missing {label} manifest payload: {relative}")
        try:
            expected_bytes = int(str(row.get("bytes", "")))
        except ValueError as exc:
            raise RuntimeError(f"invalid {label} byte count: {relative}") from exc
        if len(payload) != expected_bytes or sha256(payload) != row.get("sha256"):
            raise RuntimeError(f"{label} manifest identity differs: {relative}")
    allowed = {"MANIFEST.csv"} if allowed_unlisted is None else set(allowed_unlisted)
    if set(snapshot) != listed | allowed:
        missing = sorted((set(snapshot) - allowed) - listed)
        extra = sorted(listed - set(snapshot))
        unexpected = sorted(set(snapshot) - listed - allowed)
        raise RuntimeError(
            f"{label} manifest closure differs: missing={missing}; "
            f"extra={extra}; unexpected={unexpected}"
        )
    return snapshot


def validate_current_simulations(
    receipt_payloads: dict[str, bytes], manifest_payloads: dict[str, bytes]
) -> dict[str, dict[str, bytes]]:
    result: dict[str, dict[str, bytes]] = {}
    schemas = {
        "c1": "o006.c140.companion-c1-simulations.v1",
        "c2": "o006.c140.companion-c2-simulations.v1",
        "c3": "o006.c140.companion-c3-simulations.v1",
    }
    expected_ids = {
        "c1": {f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 5)},
        "c2": {"O006-C140-CMP-SIM005"},
        "c3": {"O006-C140-CMP-SIM006"},
    }
    for batch in ("c1", "c2", "c3"):
        receipt_key = f"build/{batch.upper()}_SIMULATION_RECEIPT.json"
        manifest_key = f"generated/simulations/{batch}/MANIFEST.csv"
        receipt = json_object(receipt_payloads[receipt_key], f"{batch} simulation receipt")
        if (
            receipt.get("schema") != schemas[batch]
            or receipt.get("status") != "pass"
            or receipt.get("browser_processes_used") is not False
            or receipt.get("network_access") is not False
        ):
            raise RuntimeError(f"{batch} simulation receipt contract differs")
        snapshot = capture_manifest_directory(
            root=COMPONENT / "generated" / "simulations" / batch,
            manifest_payload=manifest_payloads[manifest_key],
            label=f"{batch} simulation",
            path_prefix=(f"generated/simulations/{batch}/" if batch != "c2" else ""),
            path_field=("filename" if batch == "c2" else "path"),
        )
        if batch in {"c1", "c3"} and receipt.get("all_assertions_pass") is not True:
            raise RuntimeError(f"{batch} simulation assertions differ")
        if batch == "c1":
            simulations = receipt.get("simulations")
            if not isinstance(simulations, list) or {
                str(row.get("id")) for row in simulations if isinstance(row, dict)
            } != expected_ids[batch]:
                raise RuntimeError("c1 simulation ID closure differs")
            for row in simulations:
                bool_map_all_true(row.get("assertions"), f"{row.get('id')} simulation")
            manifest = receipt.get("manifest")
            expected_manifest = CURRENT_PRIOR_BATCH_MANIFESTS[manifest_key]
            if (
                not isinstance(manifest, dict)
                or manifest.get("path") != manifest_key
                or manifest.get("bytes") != expected_manifest[0]
                or manifest.get("sha256") != expected_manifest[1]
            ):
                raise RuntimeError("c1 simulation-manifest binding differs")
            if (
                receipt.get("files") != len(snapshot)
                or receipt.get("bytes") != sum(len(payload) for payload in snapshot.values())
            ):
                raise RuntimeError("c1 simulation directory census differs")
        elif batch == "c2":
            summary = receipt.get("summary")
            if not isinstance(summary, dict):
                raise RuntimeError("c2 simulation summary is missing")
            bool_map_all_true(summary.get("assertions"), "c2 simulation")
            if summary.get("seed") != 2026082805:
                raise RuntimeError("c2 simulation seed differs")
            paths = verify_rows_against_snapshot(
                receipt.get("outputs"),
                snapshot=snapshot,
                path_prefix="generated/simulations/c2/",
                label="c2 simulation outputs",
            )
            if paths != set(snapshot):
                raise RuntimeError("c2 simulation output closure differs")
        else:
            summary = receipt.get("summary")
            if (
                not isinstance(summary, dict)
                or summary.get("id") not in expected_ids[batch]
                or summary.get("seed") != 2026082906
            ):
                raise RuntimeError("c3 simulation summary differs")
            bool_map_all_true(summary.get("assertions"), "c3 simulation")
            paths = verify_rows_against_snapshot(
                receipt.get("outputs"),
                snapshot=snapshot,
                path_prefix="generated/simulations/c3/",
                label="c3 simulation outputs",
            )
            if paths != set(snapshot):
                raise RuntimeError("c3 simulation output closure differs")
        result[batch] = snapshot
    return result


def validate_cp01_contract(
    receipt_payloads: dict[str, bytes],
    generated_snapshot: dict[str, bytes],
    clean_snapshot: dict[str, bytes],
    support_payloads: dict[str, bytes],
) -> None:
    transform = json_object(
        receipt_payloads["build/CP01_TRANSFORM_RECEIPT.json"],
        "CP01 transform receipt",
    )
    if (
        transform.get("schema") != "o006.c140.cp01-transform-replay.v1"
        or transform.get("status") != "pass"
        or transform.get("browser_processes_used") is not False
        or transform.get("network_access") is not False
        or transform.get("all_assertions_pass") is not True
        or transform.get("seed") is not None
    ):
        raise RuntimeError("CP01 transform receipt contract differs")
    transform_outputs = verify_rows_against_snapshot(
        transform.get("outputs"),
        snapshot=clean_snapshot,
        path_prefix="data/capstones/CP01/clean/",
        label="CP01 transform outputs",
    )
    expected_transform_outputs = {
        "data/capstones/CP01/clean/COLUMN_MANIFEST.csv",
        "data/capstones/CP01/clean/ROW_MANIFEST.csv",
        "data/capstones/CP01/clean/TRANSFORM_LEDGER.json",
        "data/capstones/CP01/clean/concrete_compressive_strength.csv",
    }
    expected_transform_local = {
        path.removeprefix("data/capstones/CP01/clean/")
        for path in expected_transform_outputs
    }
    if transform_outputs != expected_transform_local or set(clean_snapshot) != expected_transform_local:
        raise RuntimeError("CP01 clean output closure differs")
    transform_code_paths = verify_rows_against_snapshot(
        [transform.get("code")],
        snapshot=support_payloads,
        label="CP01 transform code",
    )
    if transform_code_paths != {"data/capstones/CP01/transform_cp01.py"}:
        raise RuntimeError("CP01 transform-code closure differs")
    verify_rows_against_snapshot(
        [transform.get("canonical_input")],
        snapshot={
            "raw/data.csv": support_payloads[
                "data/capstones/CP01/raw/data.csv"
            ]
        },
        label="CP01 canonical input",
    )
    expected_transform_witnesses = {
        "raw/concrete+compressive+strength.zip",
        "raw/archive/Concrete_Data.xls",
        "raw/archive/Concrete_Readme.txt",
    }
    transform_witness_snapshot = {
        path: support_payloads[f"data/capstones/CP01/{path}"]
        for path in expected_transform_witnesses
    }
    transform_witness_paths = verify_rows_against_snapshot(
        transform.get("witness_assets"),
        snapshot=transform_witness_snapshot,
        label="CP01 transform witnesses",
    )
    if transform_witness_paths != expected_transform_witnesses:
        raise RuntimeError("CP01 transform-witness closure differs")

    replay = json_object(
        receipt_payloads["generated/capstones/CP01/CP01_REPLAY_RECEIPT.json"],
        "CP01 analysis replay receipt",
    )
    if (
        replay.get("schema") != "o006.c140.cp01-analysis-replay.v2"
        or replay.get("status") != "pass"
        or replay.get("browser_processes_used") is not False
        or replay.get("network_access") is not False
        or replay.get("all_assertions_pass") is not True
        or replay.get("seed") is not None
    ):
        raise RuntimeError("CP01 analysis replay contract differs")
    bool_map_all_true(replay.get("assertions"), "CP01 analysis")
    transform_binding = replay.get("transform_receipt")
    expected_transform = FROZEN_C5_INPUTS["build/CP01_TRANSFORM_RECEIPT.json"]
    if (
        not isinstance(transform_binding, dict)
        or transform_binding.get("path") != "build/CP01_TRANSFORM_RECEIPT.json"
        or transform_binding.get("bytes") != expected_transform[0]
        or transform_binding.get("sha256") != expected_transform[1]
    ):
        raise RuntimeError("CP01 transform/replay binding differs")
    clean_paths = verify_rows_against_snapshot(
        replay.get("clean_inputs"),
        snapshot=clean_snapshot,
        path_prefix="data/capstones/CP01/clean/",
        label="CP01 clean inputs",
    )
    if clean_paths != set(clean_snapshot):
        raise RuntimeError("CP01 replay clean-input closure differs")
    rights_paths = verify_rows_against_snapshot(
        replay.get("rights_provenance_inputs"),
        snapshot=support_payloads,
        label="CP01 rights/provenance inputs",
    )
    expected_rights = {
        "data/capstones/CP01/DATASET_PROVENANCE.json",
        "data/capstones/CP01/SHA256SUMS",
        "data/capstones/CP01/http/cc-by-4.0-legalcode.html.headers",
        "data/capstones/CP01/http/concrete+compressive+strength.zip.headers",
        "data/capstones/CP01/http/data.csv.headers",
        "data/capstones/CP01/http/doi-10.24432-C5PK67-csl.json.headers",
        "data/capstones/CP01/http/doi-10.24432-C5PK67-resolved.html.headers",
        "data/capstones/CP01/http/uci-dataset-165-api.json.headers",
        "data/capstones/CP01/http/uci-dataset-165-record.html.headers",
        "data/capstones/CP01/raw/archive/Concrete_Data.xls",
        "data/capstones/CP01/raw/archive/Concrete_Readme.txt",
        "data/capstones/CP01/raw/concrete+compressive+strength.zip",
        "data/capstones/CP01/raw/data.csv",
        "data/capstones/CP01/witnesses/cc-by-4.0-legalcode.html",
        "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-csl.json",
        "data/capstones/CP01/witnesses/doi-10.24432-C5PK67-resolved.html",
        "data/capstones/CP01/witnesses/uci-dataset-165-api.json",
        "data/capstones/CP01/witnesses/uci-dataset-165-record.html",
    }
    if rights_paths != expected_rights:
        raise RuntimeError("CP01 rights/provenance-input closure differs")
    code_paths = verify_rows_against_snapshot(
        replay.get("code"), snapshot=support_payloads, label="CP01 analysis code"
    )
    if code_paths != {
        "data/capstones/CP01/transform_cp01.py",
        "capstones/run_cp01_analysis.py",
    }:
        raise RuntimeError("CP01 analysis-code closure differs")
    output_paths = verify_rows_against_snapshot(
        replay.get("outputs"),
        snapshot=generated_snapshot,
        path_prefix="generated/capstones/CP01/",
        label="CP01 analysis outputs",
    )
    expected_outputs = {
        name for name in generated_snapshot if name != "CP01_REPLAY_RECEIPT.json"
    }
    if output_paths != expected_outputs:
        raise RuntimeError("CP01 replay output closure differs")
    closure = replay.get("manifest_closure")
    if (
        not isinstance(closure, dict)
        or closure.get("MANIFEST.csv")
        != "lists substantive payloads; excludes MANIFEST.csv and CP01_REPLAY_RECEIPT.json"
        or closure.get("receipt_outputs")
        != "lists substantive payloads plus MANIFEST.csv; excludes receipt itself"
    ):
        raise RuntimeError("CP01 manifest-closure declaration differs")


def validate_cp02_transform(
    receipt_payloads: dict[str, bytes],
    clean_snapshot: dict[str, bytes],
    support_payloads: dict[str, bytes],
) -> None:
    transform = json_object(
        receipt_payloads["build/CP02_TRANSFORM_RECEIPT.json"],
        "CP02 transform receipt",
    )
    if (
        transform.get("schema") != "o006.c140.cp02-transform.v1"
        or transform.get("status") != "pass"
        or transform.get("browser_processes_used") is not False
        or transform.get("network_access") is not False
    ):
        raise RuntimeError("CP02 transform receipt contract differs")
    bool_map_all_true(transform.get("assertions"), "CP02 transform")
    replay = transform.get("replay")
    if (
        not isinstance(replay, dict)
        or replay.get("check_only_writes") is not False
        or replay.get("required_external_check_only_replays") != 2
    ):
        raise RuntimeError("CP02 transform replay contract differs")
    code_paths = verify_rows_against_snapshot(
        transform.get("code"), snapshot=support_payloads, label="CP02 transform code"
    )
    if code_paths != {"data/capstones/CP02/transform_cp02.py"}:
        raise RuntimeError("CP02 transform-code closure differs")
    input_paths = verify_rows_against_snapshot(
        transform.get("inputs"),
        snapshot=support_payloads,
        label="CP02 transform inputs",
    )
    if input_paths != {
        "data/capstones/CP02/DATASET_PROVENANCE.json",
        "data/capstones/CP02/INPUT_MANIFEST.csv",
        "data/capstones/CP02/RIGHTS_EVIDENCE.md",
        "data/capstones/CP02/SCHEMA.json",
        "data/capstones/CP02/raw/README.md",
        "data/capstones/CP02/raw/nest_propensity.csv",
    }:
        raise RuntimeError("CP02 transform-input closure differs")
    output_rows = transform.get("outputs")
    output_paths = verify_rows_against_snapshot(
        output_rows,
        snapshot=clean_snapshot,
        label="CP02 transform outputs",
    )
    if output_paths != {
        "COLUMN_MANIFEST.csv",
        "CP02_cells_clean.csv",
        "MANIFEST.csv",
        "ROW_MANIFEST.csv",
        "TRANSFORM_LEDGER.json",
    }:
        raise RuntimeError("CP02 clean output closure differs")
    if set(clean_snapshot) != output_paths:
        raise RuntimeError("CP02 clean directory closure differs")
    manifest = transform.get("manifest")
    expected = FROZEN_C5_MANIFESTS["data/capstones/CP02/clean/MANIFEST.csv"]
    if (
        not isinstance(manifest, dict)
        or manifest.get("path") != "data/capstones/CP02/clean/MANIFEST.csv"
        or manifest.get("bytes") != expected[0]
        or manifest.get("sha256") != expected[1]
    ):
        raise RuntimeError("CP02 transform manifest binding differs")


def validate_cp02_analysis(
    receipt_payloads: dict[str, bytes],
    generated_snapshot: dict[str, bytes],
    support_payloads: dict[str, bytes],
) -> None:
    analysis = json_object(
        receipt_payloads["build/CP02_ANALYSIS_RECEIPT.json"],
        "CP02 analysis receipt",
    )
    if (
        analysis.get("schema") != CP02_ANALYSIS_SCHEMA
        or analysis.get("status") != "pass"
        or analysis.get("browser_processes_used") is not False
        or analysis.get("network_access") is not False
    ):
        raise RuntimeError("CP02 analysis receipt contract differs")
    bool_map_all_true(analysis.get("assertions"), "CP02 analysis")
    rng = analysis.get("rng")
    environment = analysis.get("environment")
    prior = analysis.get("prior")
    policy = analysis.get("denominator_policy")
    if (
        not isinstance(rng, dict)
        or rng.get("seed") != 2026083002
        or rng.get("contrast_draws") != 100000
        or rng.get("posterior_predictive_replications") != 100000
        or not isinstance(environment, dict)
        or environment.get("python") != "3.13.9"
        or environment.get("numpy") != "2.4.4"
        or not isinstance(prior, dict)
        or prior.get("primary_kappa") != 4.0
        or prior.get("primary_shape") != [2.0, 2.0]
        or prior.get("proper_under_M0_and_every_M1_cell") is not True
        or not isinstance(policy, dict)
        or policy.get("primary") != "primary_conservative_method_1"
        or policy.get("secondary_sensitivity") != "secondary_liberal_method_2"
        or policy.get("secondary_changes_estimand") is not True
    ):
        raise RuntimeError("CP02 numerical replay/prior/denominator contract differs")
    canonical = analysis.get("canonical_input")
    canonical_identity = FROZEN_C5_SUPPORT_INPUTS[
        "data/capstones/CP02/raw/nest_propensity.csv"
    ]
    if (
        not isinstance(canonical, dict)
        or canonical.get("path")
        != "data/capstones/CP02/raw/nest_propensity.csv"
        or canonical.get("bytes") != canonical_identity[0]
        or canonical.get("sha256") != canonical_identity[1]
    ):
        raise RuntimeError("CP02 canonical-input binding differs")
    clean = analysis.get("clean_inputs")
    manifest_binding = clean.get("manifest") if isinstance(clean, dict) else None
    transform_binding = (
        clean.get("transform_receipt") if isinstance(clean, dict) else None
    )
    clean_manifest_identity = FROZEN_C5_MANIFESTS[
        "data/capstones/CP02/clean/MANIFEST.csv"
    ]
    transform_identity = FROZEN_C5_INPUTS["build/CP02_TRANSFORM_RECEIPT.json"]
    if (
        not isinstance(manifest_binding, dict)
        or manifest_binding.get("path")
        != "data/capstones/CP02/clean/MANIFEST.csv"
        or manifest_binding.get("entries") != 4
        or manifest_binding.get("bytes") != clean_manifest_identity[0]
        or manifest_binding.get("sha256") != clean_manifest_identity[1]
        or not isinstance(transform_binding, dict)
        or transform_binding.get("path") != "build/CP02_TRANSFORM_RECEIPT.json"
        or transform_binding.get("schema") != "o006.c140.cp02-transform.v1"
        or transform_binding.get("bytes") != transform_identity[0]
        or transform_binding.get("sha256") != transform_identity[1]
    ):
        raise RuntimeError("CP02 clean/transform binding differs")
    rights_paths = verify_rows_against_snapshot(
        analysis.get("rights_provenance_inputs"),
        snapshot=support_payloads,
        label="CP02 analysis rights inputs",
    )
    expected_rights_paths = {
        "data/capstones/CP02/DATASET_PROVENANCE.json",
        "data/capstones/CP02/INPUT_MANIFEST.csv",
        "data/capstones/CP02/RIGHTS_EVIDENCE.md",
        "data/capstones/CP02/SCHEMA.json",
        "data/capstones/CP02/raw/README.md",
        "data/capstones/CP02/raw/nest_propensity.csv",
    }
    if rights_paths != expected_rights_paths:
        raise RuntimeError("CP02 analysis rights-input closure differs")
    code_paths = verify_rows_against_snapshot(
        analysis.get("code"),
        snapshot=support_payloads,
        label="CP02 analysis code",
    )
    if code_paths != {
        "data/capstones/CP02/transform_cp02.py",
        "capstones/run_cp02_analysis.py",
    }:
        raise RuntimeError("CP02 analysis-code closure differs")
    output_paths = verify_rows_against_snapshot(
        analysis.get("outputs"),
        snapshot=generated_snapshot,
        path_prefix="generated/capstones/CP02/",
        label="CP02 analysis outputs",
    )
    if (
        len(generated_snapshot) != 19
        or len(output_paths) != 19
        or output_paths != set(generated_snapshot)
    ):
        raise RuntimeError("CP02 analysis-output closure differs")
    closure = analysis.get("manifest_closure")
    expected_manifest = FROZEN_C5_MANIFESTS[
        "generated/capstones/CP02/MANIFEST.csv"
    ]
    if (
        not isinstance(closure, dict)
        or closure.get("manifest_path")
        != "generated/capstones/CP02/MANIFEST.csv"
        or closure.get("manifest_lists")
        != "all 18 substantive files and excludes only itself"
        or closure.get("manifest_bytes") != expected_manifest[0]
        or closure.get("manifest_sha256") != expected_manifest[1]
        or closure.get("receipt_path") != "build/CP02_ANALYSIS_RECEIPT.json"
        or closure.get("receipt_lists")
        != "all substantive files plus MANIFEST.csv and excludes itself"
    ):
        raise RuntimeError("CP02 analysis manifest closure differs")


def validate_support_contract(
    support_payloads: dict[str, bytes], root_support_payloads: dict[str, bytes]
) -> tuple[dict[str, Any], dict[str, Any]]:
    environment = json_object(
        support_payloads["environment.lock.json"], "C5 environment lock"
    )
    if (
        environment.get("schema") != "o006.c140.companion-environment.v2"
        or environment.get("status") != "locked"
        or environment.get("browser_processes_permitted") is not False
        or environment.get("locale") != "id-ID"
        or environment.get("numeric_locale") != "C"
        or environment.get("python") != "3.13.9"
        or environment.get("numpy") != "2.4.4"
        or environment.get("scipy") != "1.17.1"
        or environment.get("required_process_environment")
        != {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
    ):
        raise RuntimeError("C5 environment lock differs")

    cp01 = json_object(
        support_payloads["data/capstones/CP01/DATASET_PROVENANCE.json"],
        "CP01 dataset provenance",
    )
    cp01_identity = cp01.get("dataset_identity")
    cp01_rights = cp01.get("rights")
    cp01_assets = cp01.get("assets")
    if (
        cp01.get("schema_version") != "1.0"
        or cp01.get("freeze_status") != "frozen"
        or cp01.get("canonical_analysis_asset") != "raw/data.csv"
        or not isinstance(cp01_identity, dict)
        or cp01_identity.get("uci_id") != 165
        or cp01_identity.get("doi") != "10.24432/C5PK67"
        or cp01_identity.get("formal_version") is not None
        or not isinstance(cp01_rights, dict)
        or cp01_rights.get("spdx_expression") != "CC-BY-4.0"
        or cp01_rights.get("separation_rule") is None
        or not isinstance(cp01_assets, list)
    ):
        raise RuntimeError("CP01 dataset identity/rights contract differs")
    cp01_asset_rows = {
        str(row.get("path")): row for row in cp01_assets if isinstance(row, dict)
    }
    expected_cp01_assets = {
        "raw/data.csv",
        "raw/concrete+compressive+strength.zip",
        "raw/archive/Concrete_Data.xls",
        "raw/archive/Concrete_Readme.txt",
        "witnesses/uci-dataset-165-api.json",
        "witnesses/uci-dataset-165-record.html",
        "witnesses/doi-10.24432-C5PK67-resolved.html",
        "witnesses/doi-10.24432-C5PK67-csl.json",
        "witnesses/cc-by-4.0-legalcode.html",
    }
    if set(cp01_asset_rows) != expected_cp01_assets:
        raise RuntimeError("CP01 provenance asset closure differs")
    expected_cp01_headers = {
        "raw/data.csv": "http/data.csv.headers",
        "raw/concrete+compressive+strength.zip": (
            "http/concrete+compressive+strength.zip.headers"
        ),
        "witnesses/uci-dataset-165-api.json": (
            "http/uci-dataset-165-api.json.headers"
        ),
        "witnesses/uci-dataset-165-record.html": (
            "http/uci-dataset-165-record.html.headers"
        ),
        "witnesses/doi-10.24432-C5PK67-resolved.html": (
            "http/doi-10.24432-C5PK67-resolved.html.headers"
        ),
        "witnesses/doi-10.24432-C5PK67-csl.json": (
            "http/doi-10.24432-C5PK67-csl.json.headers"
        ),
        "witnesses/cc-by-4.0-legalcode.html": (
            "http/cc-by-4.0-legalcode.html.headers"
        ),
    }
    for local_path in sorted(expected_cp01_assets):
        row = cp01_asset_rows.get(local_path)
        support_key = f"data/capstones/CP01/{local_path}"
        identity = FROZEN_C5_SUPPORT_INPUTS[support_key]
        if (
            not isinstance(row, dict)
            or row.get("bytes") != identity[0]
            or row.get("sha256") != identity[1]
        ):
            raise RuntimeError(f"CP01 provenance asset binding differs: {local_path}")
        header_path = expected_cp01_headers.get(local_path)
        header = row.get("header_capture")
        if header_path is None:
            if header is not None:
                raise RuntimeError(
                    f"unexpected CP01 header binding: {local_path}"
                )
        else:
            header_key = f"data/capstones/CP01/{header_path}"
            header_identity = FROZEN_C5_SUPPORT_INPUTS[header_key]
            if (
                not isinstance(header, dict)
                or header.get("path") != header_path
                or header.get("bytes") != header_identity[0]
                or header.get("sha256") != header_identity[1]
            ):
                raise RuntimeError(
                    f"CP01 provenance header binding differs: {local_path}"
                )
    raw_structure = cp01_asset_rows["raw/data.csv"].get("structure")
    if (
        not isinstance(raw_structure, dict)
        or raw_structure.get("data_rows") != 1030
        or raw_structure.get("columns") != 9
        or raw_structure.get("missing_cells") != 0
    ):
        raise RuntimeError("CP01 raw-data structure contract differs")
    checksum_text = support_payloads["data/capstones/CP01/SHA256SUMS"].decode("ascii")
    for local_path, support_key in (
        ("raw/data.csv", "data/capstones/CP01/raw/data.csv"),
        (
            "raw/archive/Concrete_Readme.txt",
            "data/capstones/CP01/raw/archive/Concrete_Readme.txt",
        ),
    ):
        expected_line = f"{FROZEN_C5_SUPPORT_INPUTS[support_key][1]}  {local_path}\n"
        if expected_line not in checksum_text:
            raise RuntimeError(f"CP01 checksum binding differs: {local_path}")

    cp02 = json_object(
        support_payloads["data/capstones/CP02/DATASET_PROVENANCE.json"],
        "CP02 dataset provenance",
    )
    dataset = cp02.get("dataset")
    license_row = cp02.get("license")
    privacy = cp02.get("privacy")
    assets = cp02.get("frozen_assets")
    if (
        not isinstance(dataset, dict)
        or dataset.get("doi") != "10.5061/dryad.573n5tbf3"
        or dataset.get("version_number") != 3
        or dataset.get("version_id") != 268230
        or dataset.get("visibility") != "public"
        or not isinstance(license_row, dict)
        or license_row.get("identifier") != "CC0-1.0"
        or not isinstance(privacy, dict)
        or not isinstance(assets, list)
    ):
        raise RuntimeError("CP02 dataset identity/rights contract differs")
    analytic = privacy.get("analytic_data_scope")
    if (
        not isinstance(analytic, dict)
        or analytic.get("individual_microdata_imported") is not False
        or analytic.get("direct_study_subject_identifiers_imported") is not False
        or analytic.get("location_fields_imported") is not False
    ):
        raise RuntimeError("CP02 privacy scope differs")
    cp02_asset_rows = {
        str(row.get("local_path")): row for row in assets if isinstance(row, dict)
    }
    for local_path, support_key in (
        ("raw/nest_propensity.csv", "data/capstones/CP02/raw/nest_propensity.csv"),
        ("raw/README.md", "data/capstones/CP02/raw/README.md"),
    ):
        row = cp02_asset_rows.get(local_path)
        identity = FROZEN_C5_SUPPORT_INPUTS[support_key]
        if (
            not isinstance(row, dict)
            or row.get("bytes") != identity[0]
            or row.get("sha256") != identity[1]
            or row.get("publisher_digest_match") is not True
        ):
            raise RuntimeError(f"CP02 provenance asset binding differs: {local_path}")
    witness_rows = cp02.get("witnesses")
    if not isinstance(witness_rows, list):
        raise RuntimeError("CP02 provenance witness census is missing")
    cp02_witnesses = {
        str(row.get("local_path")): row
        for row in witness_rows
        if isinstance(row, dict)
    }
    expected_cp02_witnesses = {
        "witnesses/version-268230.json",
        "witnesses/version-268230-files.json",
        "witnesses/file-2765112.json",
        "witnesses/file-2765118.json",
        "witnesses/dataset-doi-10.5061-dryad.573n5tbf3-api.json",
        "witnesses/datacite-doi-10.5061-dryad.573n5tbf3.json",
        "witnesses/doi-10.5061-dryad.573n5tbf3-resolved.html",
        "witnesses/dryad-reuse-guide.html",
        "witnesses/cc0-1.0-legalcode.html",
    }
    if set(cp02_witnesses) != expected_cp02_witnesses:
        raise RuntimeError("CP02 provenance witness closure differs")
    for local_path, row in sorted(cp02_witnesses.items()):
        support_key = f"data/capstones/CP02/{local_path}"
        identity = FROZEN_C5_SUPPORT_INPUTS[support_key]
        if row.get("bytes") != identity[0] or row.get("sha256") != identity[1]:
            raise RuntimeError(
                f"CP02 provenance witness binding differs: {local_path}"
            )
    expected_cp02_headers = {
        "http/cc0-1.0-legalcode.html.headers",
        "http/datacite-doi-10.5061-dryad.573n5tbf3.json.headers",
        "http/dataset-doi-10.5061-dryad.573n5tbf3-api.json.headers",
        "http/doi-10.5061-dryad.573n5tbf3-resolved.html.headers",
        "http/dryad-reuse-guide.html.headers",
        "http/file-2765112.json.headers",
        "http/file-2765118.json.headers",
        "http/nest_propensity.csv.headers",
        "http/README.md.headers",
        "http/version-268230-files.json.headers",
        "http/version-268230.json.headers",
    }
    for local_path in expected_cp02_headers:
        if f"data/capstones/CP02/{local_path}" not in support_payloads:
            raise RuntimeError(f"CP02 HTTP evidence is missing: {local_path}")
    schema = json_object(
        support_payloads["data/capstones/CP02/SCHEMA.json"], "CP02 data schema"
    )
    shape = schema.get("shape")
    policy = schema.get("denominator_policy")
    integrity = schema.get("integrity_checks")
    if (
        schema.get("source_file") != "raw/nest_propensity.csv"
        or schema.get("source_file_id") != 2765112
        or not isinstance(shape, dict)
        or shape.get("data_rows") != 12
        or shape.get("columns") != 5
        or not isinstance(policy, dict)
        or policy.get("primary", {}).get("column") != "Total_method_1"
        or policy.get("sensitivity", {}).get("column") != "Total_method_2"
        or not isinstance(integrity, dict)
        or integrity.get("all_rows_have_five_fields") is not True
        or integrity.get("missing_values") != 0
    ):
        raise RuntimeError("CP02 schema/denominator contract differs")
    manifest_rows = list(
        csv.DictReader(
            io.StringIO(
                support_payloads["data/capstones/CP02/INPUT_MANIFEST.csv"].decode("utf-8"),
                newline="",
            )
        )
    )
    if len(manifest_rows) != 2:
        raise RuntimeError("CP02 input manifest row count differs")
    by_path = {str(row.get("local_path")): row for row in manifest_rows}
    for local_path, support_key in (
        ("raw/nest_propensity.csv", "data/capstones/CP02/raw/nest_propensity.csv"),
        ("raw/README.md", "data/capstones/CP02/raw/README.md"),
    ):
        row = by_path.get(local_path)
        identity = FROZEN_C5_SUPPORT_INPUTS[support_key]
        if (
            row is None
            or int(str(row.get("bytes", "-1"))) != identity[0]
            or row.get("sha256") != identity[1]
        ):
            raise RuntimeError(f"CP02 input-manifest binding differs: {local_path}")
    rights_text = support_payloads["data/capstones/CP02/RIGHTS_EVIDENCE.md"].decode("utf-8")
    for witness in ("CC0-1.0", "10.5061/dryad.573n5tbf3", "268230"):
        if witness not in rights_text:
            raise RuntimeError(f"CP02 rights evidence omits {witness}")
    rights_surfaces = {
        "component license": support_payloads["LICENSE.md"].decode("utf-8"),
        "collection license": root_support_payloads["LICENSE.md"].decode("utf-8"),
        "rights register": root_support_payloads[
            "00_control/RIGHTS_AND_COMPONENTS.md"
        ].decode("utf-8"),
    }
    for label, text in rights_surfaces.items():
        for marker in (
            "10.24432/C5PK67",
            "CC BY 4.0",
            "10.5061/dryad.573n5tbf3",
            "268230",
            "CC0",
        ):
            if marker not in text:
                raise RuntimeError(f"{label} omits rights marker {marker}")
    return cp01, cp02


def validate_capstone_receipt_bindings(
    build: dict[str, Any], qa: dict[str, Any]
) -> None:
    expected = {
        "build/CP01_TRANSFORM_RECEIPT.json": {
            "capstone": "CP01",
            "role": "transform",
            "schema": "o006.c140.cp01-transform-replay.v1",
        },
        "generated/capstones/CP01/CP01_REPLAY_RECEIPT.json": {
            "capstone": "CP01",
            "role": "analysis",
            "schema": "o006.c140.cp01-analysis-replay.v2",
        },
        "build/CP02_TRANSFORM_RECEIPT.json": {
            "capstone": "CP02",
            "role": "transform",
            "schema": "o006.c140.cp02-transform.v1",
        },
        "build/CP02_ANALYSIS_RECEIPT.json": {
            "capstone": "CP02",
            "role": "analysis",
            "schema": CP02_ANALYSIS_SCHEMA,
        },
    }
    qa_capstones = qa.get("capstones")
    qa_rows = qa_capstones.get("receipts") if isinstance(qa_capstones, dict) else None
    for label, rows in (
        ("C5 build capstone receipts", build.get("capstone_receipts")),
        ("C5 QA capstone receipts", qa_rows),
    ):
        if not isinstance(rows, list) or len(rows) != len(expected):
            raise RuntimeError(f"{label} closure differs")
        seen: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"{label} row is malformed")
            path = str(row.get("path", ""))
            contract = expected.get(path)
            frozen = FROZEN_C5_INPUTS.get(path)
            if (
                contract is None
                or frozen is None
                or path in seen
                or row.get("capstone") != contract["capstone"]
                or row.get("role") != contract["role"]
                or row.get("schema") != contract["schema"]
                or row.get("bytes") != frozen[0]
                or row.get("sha256") != frozen[1]
            ):
                raise RuntimeError(f"{label} binding differs: {path}")
            seen.add(path)
        if seen != set(expected):
            raise RuntimeError(f"{label} path closure differs")


def validate_cp02_publication_redaction(
    build: dict[str, Any],
    backend_snapshot: dict[str, bytes],
    support_payloads: dict[str, bytes],
) -> None:
    original = support_payloads[CP02_CREDENTIAL_BEARING_WITNESS]
    redacted = support_payloads[CP02_REDACTED_WITNESS]
    receipt_payload = support_payloads[CP02_REDACTION_RECEIPT]
    replay_redacted, replay_receipt = redact_cp02_public_client_key(original)
    if redacted != replay_redacted or receipt_payload != replay_receipt:
        raise RuntimeError("CP02 durable publication redaction replay differs")

    rows = build.get("witness_redactions")
    expected_record = {
        "derivative": {
            "bytes": len(redacted),
            "path": CP02_REDACTED_WITNESS,
            "sha256": sha256(redacted),
        },
        "excluded_original": {
            "bytes": len(original),
            "path": CP02_CREDENTIAL_BEARING_WITNESS,
            "sha256": sha256(original),
        },
        "receipt": {
            "bytes": len(receipt_payload),
            "path": CP02_REDACTION_RECEIPT,
            "sha256": sha256(receipt_payload),
        },
        "schema": "o006.c140.cp02-witness-redaction.v1",
        "status": "pass",
    }
    if not isinstance(rows, list) or rows != [expected_record]:
        raise RuntimeError("C5 build CP02 witness-redaction binding differs")

    backend_original = (
        "source/capstones/CP02/data/witnesses/"
        "doi-10.5061-dryad.573n5tbf3-resolved.html"
    )
    backend_redacted = (
        "source/capstones/CP02/data/witnesses/"
        "doi-10.5061-dryad.573n5tbf3-redacted.html"
    )
    backend_receipt = (
        "source/capstones/CP02/data/witnesses/"
        "doi-10.5061-dryad.573n5tbf3-redistribution-redaction.json"
    )
    if (
        backend_original in backend_snapshot
        or backend_snapshot.get(backend_redacted) != redacted
        or backend_snapshot.get(backend_receipt) != receipt_payload
    ):
        raise RuntimeError("C5 backend CP02 publication redaction closure differs")


def validate_cp02_coverage_derivative(
    build: dict[str, Any],
    html_snapshot: dict[str, bytes],
    backend_snapshot: dict[str, bytes],
    generated_snapshot: dict[str, bytes],
) -> None:
    raw = generated_snapshot.get(CP02_COVERAGE_RAW)
    derivative = backend_snapshot.get(CP02_COVERAGE_GZIP)
    if raw is None or derivative is None:
        raise RuntimeError("CP02 coverage redistribution derivative is missing")
    if html_snapshot.get(CP02_COVERAGE_GZIP) != derivative:
        raise RuntimeError("CP02 HTML/backend coverage derivative differs")
    expected_record = {
        "compression": {
            "algorithm": "gzip",
            "compresslevel": 9,
            "header_filename": CP02_COVERAGE_RAW,
            "mtime": 0,
        },
        "public_derivative": {
            "bytes": len(derivative),
            "path": CP02_COVERAGE_GZIP,
            "sha256": sha256(derivative),
        },
        "source": {
            "bytes": len(raw),
            "path": f"generated/capstones/CP02/{CP02_COVERAGE_RAW}",
            "sha256": sha256(raw),
        },
        "status": "pass",
    }
    if build.get("public_derivatives") != [expected_record]:
        raise RuntimeError("C5 build CP02 coverage-derivative binding differs")
    if len(derivative) > MAX_PUBLIC_FILE_BYTES:
        raise RuntimeError("CP02 coverage derivative exceeds the public-file cap")
    if (
        len(derivative) < 12
        or derivative[:3] != b"\x1f\x8b\x08"
        or derivative[3] != 0x08
        or int.from_bytes(derivative[4:8], "little") != 0
        or derivative[8] != 0x02
        or derivative[9] != 0xFF
    ):
        raise RuntimeError("CP02 coverage gzip header differs")
    filename_end = derivative.find(b"\x00", 10)
    if (
        filename_end < 0
        or derivative[10:filename_end] != CP02_COVERAGE_RAW.encode("ascii")
    ):
        raise RuntimeError("CP02 coverage gzip filename differs")
    digest = hashlib.sha256()
    decompressed_bytes = 0
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(derivative), mode="rb") as stream:
            while True:
                chunk = stream.read(1_048_576)
                if not chunk:
                    break
                digest.update(chunk)
                decompressed_bytes += len(chunk)
                if decompressed_bytes > len(raw):
                    raise RuntimeError("CP02 coverage gzip expands beyond its source")
    except (EOFError, OSError) as exc:
        raise RuntimeError("CP02 coverage gzip verification failed") from exc
    if decompressed_bytes != len(raw) or digest.hexdigest() != sha256(raw):
        raise RuntimeError("CP02 coverage gzip/source identity differs")


def validate_c5_coverage_counts(build: dict[str, Any], qa: dict[str, Any]) -> None:
    source = qa.get("source")
    simulations = qa.get("simulations")
    if not isinstance(source, dict) or not isinstance(simulations, dict):
        raise RuntimeError("C5 QA coverage census is missing")
    assessments = source.get("assessments")
    capstones = source.get("capstones")
    if not isinstance(assessments, list) or not isinstance(capstones, list):
        raise RuntimeError("C5 QA assessment/capstone census is missing")
    expected_assessments = {f"O006-C140-CMP-CA{i:02d}" for i in range(1, 5)}
    expected_capstones = {f"O006-C140-CMP-CP{i:02d}" for i in range(1, 3)}
    if (
        len(assessments) != EXPECTED_ASSESSMENTS
        or {str(row.get("document_id")) for row in assessments if isinstance(row, dict)}
        != expected_assessments
        or any(
            not isinstance(row, dict)
            or row.get("problems") != 10
            or row.get("rubrics") != 11
            or not isinstance(row.get("solution_words"), int)
            or row.get("solution_words") <= 0
            for row in assessments
        )
    ):
        raise RuntimeError("C5 assessment census differs")
    if (
        len(capstones) != EXPECTED_CAPSTONES
        or {str(row.get("document_id")) for row in capstones if isinstance(row, dict)}
        != expected_capstones
        or any(
            not isinstance(row, dict)
            or row.get("problems") != 1
            or row.get("rubrics") != 9
            or not isinstance(row.get("solution_words"), int)
            or row.get("solution_words") <= 0
            for row in capstones
        )
    ):
        raise RuntimeError("C5 capstone census differs")
    if source.get("problems") != EXPECTED_PROBLEMS:
        raise RuntimeError("C5 total problem census differs")
    if simulations.get("simulations") != EXPECTED_SIMULATIONS:
        raise RuntimeError("C5 simulation census differs")
    expected_simulation_ids = {
        f"O006-C140-CMP-SIM{i:03d}" for i in range(1, EXPECTED_SIMULATIONS + 1)
    }
    if set(simulations.get("simulation_ids", [])) != expected_simulation_ids:
        raise RuntimeError("C5 simulation ID closure differs")
    build_rows = build.get("simulation_receipts")
    if not isinstance(build_rows, list) or len(build_rows) != 3:
        raise RuntimeError("C5 build simulation-receipt closure differs")
    expected_receipts = {
        f"build/C{i}_SIMULATION_RECEIPT.json": (f"c{i}", identity)
        for i, identity in (
            (1, CURRENT_PRIOR_BATCH_INPUTS["build/C1_SIMULATION_RECEIPT.json"]),
            (2, CURRENT_PRIOR_BATCH_INPUTS["build/C2_SIMULATION_RECEIPT.json"]),
            (3, CURRENT_PRIOR_BATCH_INPUTS["build/C3_SIMULATION_RECEIPT.json"]),
        )
    }
    seen: set[str] = set()
    for row in build_rows:
        if not isinstance(row, dict):
            raise RuntimeError("C5 build simulation-receipt row is malformed")
        path = str(row.get("path", ""))
        contract = expected_receipts.get(path)
        if (
            contract is None
            or path in seen
            or row.get("batch") != contract[0]
            or row.get("bytes") != contract[1][0]
            or row.get("sha256") != contract[1][1]
        ):
            raise RuntimeError(f"C5 build simulation-receipt binding differs: {path}")
        seen.add(path)
    if seen != set(expected_receipts):
        raise RuntimeError("C5 build simulation-receipt path closure differs")
    batch_rows = simulations.get("batches")
    expected_batches = {
        "c1": (4, 9, CURRENT_PRIOR_BATCH_MANIFESTS[
            "generated/simulations/c1/MANIFEST.csv"
        ][1], CURRENT_PRIOR_BATCH_INPUTS["build/C1_SIMULATION_RECEIPT.json"][1]),
        "c2": (1, 3, CURRENT_PRIOR_BATCH_MANIFESTS[
            "generated/simulations/c2/MANIFEST.csv"
        ][1], CURRENT_PRIOR_BATCH_INPUTS["build/C2_SIMULATION_RECEIPT.json"][1]),
        "c3": (1, 4, CURRENT_PRIOR_BATCH_MANIFESTS[
            "generated/simulations/c3/MANIFEST.csv"
        ][1], CURRENT_PRIOR_BATCH_INPUTS["build/C3_SIMULATION_RECEIPT.json"][1]),
    }
    if not isinstance(batch_rows, list) or len(batch_rows) != 3:
        raise RuntimeError("C5 QA simulation-batch closure differs")
    seen_batches: set[str] = set()
    for row in batch_rows:
        if not isinstance(row, dict) or row.get("batch") not in expected_batches:
            raise RuntimeError("C5 QA simulation-batch row differs")
        batch = str(row["batch"])
        if batch in seen_batches:
            raise RuntimeError(f"duplicate C5 QA simulation batch: {batch}")
        seen_batches.add(batch)
        expected = expected_batches[batch]
        if (
            row.get("simulations") != expected[0]
            or row.get("files") != expected[1]
            or row.get("manifest_sha256") != expected[2]
            or row.get("receipt_sha256") != expected[3]
        ):
            raise RuntimeError(f"C5 QA simulation batch differs: {batch}")
    if seen_batches != set(expected_batches):
        raise RuntimeError("C5 QA simulation-batch path closure differs")
    if simulations.get("files") != 16:
        raise RuntimeError("C5 QA simulation file census differs")


def validate_c5_boundary() -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, object]],
    dict[str, dict[str, bytes]],
]:
    require_frozen_c5_contract()
    historical, historical_payloads = validate_frozen_files(
        CURRENT_PRIOR_BATCH_INPUTS, label="C5 current prior-batch receipt"
    )
    inputs, input_payloads = validate_frozen_files(
        FROZEN_C5_INPUTS, label="C5 receipt"
    )
    manifests, manifest_payloads = validate_frozen_files(
        FROZEN_C5_MANIFESTS, label="C5 manifest"
    )
    historical_manifests, historical_manifest_payloads = validate_frozen_files(
        CURRENT_PRIOR_BATCH_MANIFESTS, label="C5 current prior-batch manifest"
    )
    support, support_payloads = validate_frozen_files(
        FROZEN_C5_SUPPORT_INPUTS, label="C5 support input"
    )
    root_support, root_support_payloads = validate_frozen_files(
        FROZEN_C5_ROOT_SUPPORT_INPUTS,
        label="C5 root support input",
        base=ROOT,
    )
    repository_context, repository_context_payloads = validate_frozen_files(
        FROZEN_C5_REPOSITORY_CONTEXT_INPUTS,
        label="C5 reproducibility repository context",
        base=ROOT,
    )
    mathjax_prefix = "build/html-id/assets/MathJax/"
    expected_mathjax = {
        relative.removeprefix(mathjax_prefix): payload
        for relative, payload in repository_context_payloads.items()
        if relative.startswith(mathjax_prefix)
    }
    if safe_files_from_directory(
        ROOT / "build" / "html-id" / "assets" / "MathJax"
    ) != expected_mathjax:
        raise RuntimeError("C5 repository-context MathJax file closure differs")
    for relative in ("LICENSE.md", "00_control/RIGHTS_AND_COMPONENTS.md"):
        if repository_context_payloads[relative] != root_support_payloads[relative]:
            raise RuntimeError(f"C5 repository-context rights binding differs: {relative}")

    build = json_object(
        input_payloads["build/C5_BUILD_RECEIPT.json"],
        "C5 build receipt",
    )
    qa = json_object(
        input_payloads["build/C5_QA_RECEIPT.json"],
        "C5 QA receipt",
    )
    ids = build.get("cumulative_required_ids")
    source_rows = build.get("source")
    html = build.get("html")
    backend = build.get("backend")
    build_environment = build.get("environment")
    environment_identity = FROZEN_C5_SUPPORT_INPUTS["environment.lock.json"]
    if (
        build.get("schema") != "o006.c140.companion-cumulative-c5-build.v1"
        or build.get("status") != "pass"
        or build.get("boundary") != "cumulative-through-c5"
        or build.get("browser_processes_used") is not False
        or build.get("network_access") is not False
        or build.get("translation_provenance")
        != "OpenAI Codex gpt-5.6-sol, Ultra"
        or not isinstance(ids, list)
        or set(ids) != EXPECTED_DOCUMENT_IDS
        or len(ids) != EXPECTED_DOCUMENTS
        or build.get("cumulative_documents") != EXPECTED_DOCUMENTS
        or not isinstance(source_rows, list)
        or len(source_rows) != EXPECTED_DOCUMENTS
        or not isinstance(html, dict)
        or not isinstance(backend, dict)
        or not isinstance(build_environment, dict)
        or build_environment.get("path") != "environment.lock.json"
        or build_environment.get("bytes") != environment_identity[0]
        or build_environment.get("sha256") != environment_identity[1]
    ):
        raise RuntimeError("C5 cumulative build contract differs")

    source_snapshot = safe_files_from_directory(
        COMPONENT / "source" / "id-ID", "source/id-ID"
    )
    seen_sources = verify_rows_against_snapshot(
        source_rows, snapshot=source_snapshot, label="C5 source"
    )
    if seen_sources != set(source_snapshot):
        raise RuntimeError("C5 source-directory closure differs")

    html_manifest = manifests["build/html-id/MANIFEST.csv"]
    backend_manifest = manifests["backend/MANIFEST.csv"]
    if (
        html.get("manifest_sha256") != html_manifest["sha256"]
        or backend.get("manifest_sha256") != backend_manifest["sha256"]
    ):
        raise RuntimeError("C5 build manifest binding differs")
    html_snapshot = capture_manifest_directory(
        root=COMPONENT / "build" / "html-id",
        manifest_payload=manifest_payloads["build/html-id/MANIFEST.csv"],
        label="C5 HTML",
    )
    backend_snapshot = capture_manifest_directory(
        root=COMPONENT / "backend",
        manifest_payload=manifest_payloads["backend/MANIFEST.csv"],
        label="C5 backend",
    )
    if (len(html_snapshot), sum(map(len, html_snapshot.values()))) != (
        html.get("files"),
        html.get("bytes"),
    ):
        raise RuntimeError("C5 live offline-reader directory census differs")
    if (len(backend_snapshot), sum(map(len, backend_snapshot.values()))) != (
        backend.get("files"),
        backend.get("bytes"),
    ):
        raise RuntimeError("C5 live backend directory census differs")
    validate_cp02_publication_redaction(build, backend_snapshot, support_payloads)

    simulation_snapshots = validate_current_simulations(
        historical_payloads, historical_manifest_payloads
    )
    cp01_generated = capture_manifest_directory(
        root=COMPONENT / "generated" / "capstones" / "CP01",
        manifest_payload=manifest_payloads["generated/capstones/CP01/MANIFEST.csv"],
        label="CP01 generated",
        path_prefix="generated/capstones/CP01/",
        allowed_unlisted={"MANIFEST.csv", "CP01_REPLAY_RECEIPT.json"},
    )
    cp02_generated = capture_manifest_directory(
        root=COMPONENT / "generated" / "capstones" / "CP02",
        manifest_payload=manifest_payloads["generated/capstones/CP02/MANIFEST.csv"],
        label="CP02 generated",
        allowed_unlisted={"MANIFEST.csv"},
    )
    validate_cp02_coverage_derivative(
        build, html_snapshot, backend_snapshot, cp02_generated
    )
    cp01_clean = safe_files_from_directory(
        COMPONENT / "data" / "capstones" / "CP01" / "clean"
    )
    cp02_clean = capture_manifest_directory(
        root=COMPONENT / "data" / "capstones" / "CP02" / "clean",
        manifest_payload=manifest_payloads[
            "data/capstones/CP02/clean/MANIFEST.csv"
        ],
        label="CP02 clean",
    )
    for capstone, clean_snapshot in (
        ("CP01", cp01_clean),
        ("CP02", cp02_clean),
    ):
        prefix = f"data/capstones/{capstone}/"
        expected_data_tree = {
            relative.removeprefix(prefix): payload
            for relative, payload in support_payloads.items()
            if relative.startswith(prefix)
        }
        expected_data_tree.update(
            {f"clean/{name}": payload for name, payload in clean_snapshot.items()}
        )
        live_data_tree = safe_files_from_directory(
            COMPONENT / "data" / "capstones" / capstone
        )
        if live_data_tree != expected_data_tree:
            missing = sorted(set(live_data_tree) - set(expected_data_tree))
            extra = sorted(set(expected_data_tree) - set(live_data_tree))
            differing = sorted(
                name
                for name in set(live_data_tree) & set(expected_data_tree)
                if live_data_tree[name] != expected_data_tree[name]
            )
            raise RuntimeError(
                f"{capstone} dataset evidence closure differs: "
                f"unregistered={missing}; absent={extra}; differing={differing}"
            )
    validate_cp01_contract(
        input_payloads, cp01_generated, cp01_clean, support_payloads
    )
    validate_cp02_transform(input_payloads, cp02_clean, support_payloads)
    validate_cp02_analysis(input_payloads, cp02_generated, support_payloads)
    validate_support_contract(support_payloads, root_support_payloads)

    qa_source = qa.get("source")
    qa_html = qa.get("html")
    qa_backend = qa.get("backend")
    qa_runtime = qa.get("runtime")
    expected_process_environment = {
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
    }
    if (
        qa.get("schema") != "o006.c140.companion-cumulative-c5-qa.v1"
        or qa.get("status") != "pass"
        or qa.get("browser_processes_used") is not False
        or qa.get("network_access") is not False
        or qa.get("translation_provenance")
        != "OpenAI Codex gpt-5.6-sol, Ultra"
        or qa.get("build_receipt_sha256")
        != FROZEN_C5_INPUTS["build/C5_BUILD_RECEIPT.json"][1]
        or qa.get("environment_sha256") != environment_identity[1]
        or not isinstance(qa_runtime, dict)
        or qa_runtime.get("python") != "3.13.9"
        or qa_runtime.get("numpy") != "2.4.4"
        or qa_runtime.get("scipy") != "1.17.1"
        or qa_runtime.get("numeric_locale") != "C"
        or qa_runtime.get("process_environment")
        != expected_process_environment
        or not isinstance(qa_source, dict)
        or qa_source.get("documents") != EXPECTED_DOCUMENTS
        or qa_source.get("problems") != EXPECTED_PROBLEMS
        or not isinstance(qa_html, dict)
        or qa_html.get("files") != html.get("files")
        or qa_html.get("manifest_sha256") != html_manifest["sha256"]
        or not isinstance(qa_backend, dict)
        or qa_backend.get("entities") != backend.get("entities")
        or qa_backend.get("relations") != backend.get("relations")
        or qa_backend.get("manifest_sha256") != backend_manifest["sha256"]
    ):
        raise RuntimeError("C5 cumulative QA contract differs")
    validate_capstone_receipt_bindings(build, qa)
    validate_c5_coverage_counts(build, qa)

    snapshots = {
        "html": html_snapshot,
        "backend": backend_snapshot,
        "source": source_snapshot,
        "simulation_c1": simulation_snapshots["c1"],
        "simulation_c2": simulation_snapshots["c2"],
        "simulation_c3": simulation_snapshots["c3"],
        "cp01_generated": cp01_generated,
        "cp02_generated": cp02_generated,
        "cp01_clean": cp01_clean,
        "cp02_clean": cp02_clean,
        "support": support_payloads,
        "root_support": root_support_payloads,
        "repository_context": repository_context_payloads,
        "historical_receipts": historical_payloads,
        "c5_receipts": input_payloads,
        "historical_manifests": historical_manifest_payloads,
        "c5_manifests": manifest_payloads,
    }
    return (
        build,
        qa,
        {**historical, **inputs},
        {**historical_manifests, **manifests},
        {
            **support,
            **{f"root/{key}": value for key, value in root_support.items()},
            **{
                f"repository-context/{key}": value
                for key, value in repository_context.items()
            },
        },
        snapshots,
    )


def simulation_label_correction_metadata() -> dict[str, object]:
    bindings: dict[str, object] = {}
    for historical, current in (
        (FROZEN_HISTORICAL_INPUTS, FROZEN_C5_SIMULATION_INPUT_OVERRIDES),
        (FROZEN_HISTORICAL_MANIFESTS, FROZEN_C5_SIMULATION_MANIFEST_OVERRIDES),
    ):
        for relative, identity in sorted(current.items()):
            bindings[relative] = {
                "historical": {
                    "bytes": historical[relative][0],
                    "sha256": historical[relative][1],
                },
                "current_c5": {"bytes": identity[0], "sha256": identity[1]},
            }
    return {
        "bindings": bindings,
        "historical_identity_maps_preserved": True,
        "inherited_public_files_byte_identical": True,
        "reason": "C5 Indonesian SVG-label corrections in current C1/C2 simulations",
        "scope": "current C5 source, reader, backend, and QA evidence only",
    }


def repository_context_manifest() -> bytes:
    return canonical_json(
        {
            "schema": "o006.c140.companion-c5-repository-context.v1",
            "status": "frozen",
            "installation_root": "fresh repository root, not the component directory",
            "component_directory": "components/c140-companion",
            "files": [
                {"path": relative, "bytes": identity[0], "sha256": identity[1]}
                for relative, identity in sorted(FROZEN_C5_REPOSITORY_CONTEXT_INPUTS.items())
            ],
            "file_count": len(FROZEN_C5_REPOSITORY_CONTEXT_INPUTS),
            "total_bytes": sum(
                identity[0] for identity in FROZEN_C5_REPOSITORY_CONTEXT_INPUTS.values()
            ),
            "rights": "component-separated; preserve all bundled notices and provenance",
            "scope": "minimal offline external authorities and runtime for C5 build/QA",
            "metadata_not_installed": ["CONTEXT_MANIFEST.json", "COPYING.md"],
        }
    )


def repository_context_copying() -> bytes:
    return (
        "# C5 source reconstruction in a fresh repository layout\n\n"
        "Do not install into an existing checkout or overwrite live repository files. "
        "Create a new empty directory called `fresh-repo`, then extract this source "
        "ZIP into `fresh-repo/components/c140-companion`. The ZIP is deliberately "
        "component-relative; the builder locates its repository two levels above "
        "that component directory.\n\n"
        "Read `repository-context/CONTEXT_MANIFEST.json`. For each listed `path`, "
        "copy `repository-context/<path>` to `fresh-repo/<path>` with the same "
        "relative directory structure. Create only missing parent directories; "
        "refuse any existing destination file. Verify the listed byte count and "
        "SHA-256 both before and after copying. Do not install this `COPYING.md` "
        "or `CONTEXT_MANIFEST.json` at repository root.\n\n"
        "The context is a bounded build dependency subset, not a replacement Penn "
        "State or Random reader. It preserves the Penn State document registry, "
        "current Random donor entity/translation bindings and exact translated "
        "target, donor change records and attribution notice, the five pinned "
        "MathJax runtime files with Apache-2.0 license, and repository rights "
        "notices. Penn State, Random, MathJax, companion, and dataset rights remain "
        "separate; do not remove source credits or relicense this mixed context.\n\n"
        "Use the versions in `environment.lock.json` (Python 3.13.9, NumPy 2.4.4, "
        "SciPy 1.17.1 and the other locked dependencies). Set `TZ=UTC`, "
        "`PYTHONHASHSEED=0`, `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, "
        "`MKL_NUM_THREADS=1`, and `NUMEXPR_NUM_THREADS=1` in the process environment. "
        "From `fresh-repo/components/c140-companion`, run:\n\n"
        "```text\n"
        "python -B ci/hydrate_cp02_coverage.py --component-root . --write\n"
        "python -B scripts/build_companion.py --write --c5\n"
        "python -B scripts/build_companion.py --check-only --c5\n"
        "python -B scripts/qa_companion.py --check-only --c5\n"
        "```\n\n"
        "Hydration restores the exact canonical coverage ledger from the bundled "
        "backend gzip. Build-write reconstructs the offline reader and backend; "
        "the two checks must reproduce the bundled frozen C5 build and QA receipt "
        "identities. No network or browser is required. The credential-bearing "
        "original CP02 witness is intentionally absent: the pinned public redacted "
        "witness and redaction receipt support deterministic replay without it.\n"
    ).encode("utf-8")


def release_notes(build: dict[str, Any], qa: dict[str, Any]) -> bytes:
    html = build["html"]
    backend = build["backend"]
    source = qa["source"]
    return (
        "# C140 original companion — complete C5 checkpoint\n\n"
        "Status: **complete on the admitted C5 boundary**. The complete Penn "
        "State STAT 415 Indonesian spine, exact Random completeness donor, and "
        "all 57 anonymously verified C4 files remain byte-identical. This version "
        "adds the completed original rigor, simulation, mastery, assessment, and "
        "two-capstone companion.\n\n"
        "The current C5 C1/C2 simulation figures include corrected Indonesian "
        "SVG labels. Their current receipts and manifests are bound separately "
        "from the preserved historical identities; no inherited C1–C4 public "
        "release file is rewritten. The QA archive records both sets of hashes "
        "and this label-correction reason.\n\n"
        "C5 closes CA02–CA04 and CP01–CP02. The first capstone develops a fully "
        "reproducible fixed-design multiple-regression analysis of the UCI Concrete "
        "Compressive Strength data. The second performs an exact Bayesian–frequentist "
        "comparison on the frozen aggregate Dryad transmitter-by-year table. Both "
        "preserve deterministic data transforms, complete worked solutions, rubrics, "
        "static figures or text alternatives, and dataset-level rights.\n\n"
        "The exact CP02 DOI landing-page witness remains frozen and validated "
        "locally. Because that public HTML embeds a credential-like client key, "
        "the redistribution package excludes the original page and supplies a "
        "deterministically redacted derivative plus an identity-only redaction "
        "receipt. No credential-like value is redistributed.\n\n"
        "The canonical 135,581,717-byte CP02 coverage ledger remains locally "
        "receipt- and manifest-bound. Public HTML/backend and the resumable "
        "source package carry its deterministic gzip derivative instead; the "
        "C5 build receipt binds both identities and compression settings. No "
        "individual public file exceeds 100,000,000 bytes.\n\n"
        "For reproducibility, extract the source ZIP into a new empty repository "
        "at `fresh-repo/components/c140-companion`, and install only the exact "
        "manifest-listed `repository-context/` files at that fresh repository "
        "root. Never overwrite an existing checkout. Follow "
        "`repository-context/COPYING.md`: use the locked runtime, hydrate the "
        "coverage ledger, run C5 build-write, then build-check and QA-check. "
        "The context binds the required Penn State/Random authorities, current "
        "donor provenance, MathJax runtime, and separate rights notices; all "
        "reconstruction steps are offline and browser-free.\n\n"
        f"The cumulative original companion has {build['cumulative_documents']} "
        f"reader documents, {source['problems']} fully solved problems, "
        f"{html['files']} offline reader files / {html['bytes']} bytes, and a "
        f"backend with {backend['entities']} entities / {backend['relations']} "
        "relations. Deterministic build, numerical replay, mathematics, reference, "
        "rights, privacy, static accessibility/reflow, archive, and byte-replay "
        "gates pass. No browser process was used; content build, QA, and package "
        "replay used no network. Publication transport is a separate HTTPS step.\n\n"
        "The inherited PDF and EPUB remain first in the cumulative inventory. C5 "
        "is supplied as the complete offline HTML reader, a compact resumable "
        "source/backend/data-rights package, a component-and-dataset license notice, "
        "and static QA evidence. The staged cryptographic inventory is explicitly "
        "non-self-referential: the full-union CSV lists the 62 files that precede "
        "it, SHA256SUMS covers those 62 plus the CSV, and the root receipt covers "
        "those 63 plus SHA256SUMS while excluding only itself. Together these layers "
        "close the complete 65-file publication union.\n\n"
        "Production provenance: `OpenAI Codex gpt-5.6-sol, Ultra`. Penn State, "
        "Random, original-companion, UCI dataset, and Dryad dataset rights remain "
        "component-separated.\n"
    ).encode("utf-8")


def license_notice(support_payloads: dict[str, bytes]) -> bytes:
    cp01_provenance = json_object(
        support_payloads["data/capstones/CP01/DATASET_PROVENANCE.json"],
        "CP01 dataset provenance",
    )
    cp02_provenance = json_object(
        support_payloads["data/capstones/CP02/DATASET_PROVENANCE.json"],
        "CP02 dataset provenance",
    )
    cp01_rights = cp01_provenance.get("rights")
    cp02_license = cp02_provenance.get("license")
    if (
        not isinstance(cp01_rights, dict)
        or cp01_rights.get("spdx_expression") != "CC-BY-4.0"
        or cp01_rights.get("required_attribution")
        != (
            "Yeh, I. (1998). Concrete Compressive Strength [Dataset]. UCI "
            "Machine Learning Repository. https://doi.org/10.24432/C5PK67."
        )
        or not isinstance(cp02_license, dict)
        or cp02_license.get("identifier") != "CC0-1.0"
    ):
        raise RuntimeError("dataset rights contract differs")
    return (
        "# C140 C5 — lisensi komponen dan dataset\n\n"
        "Koleksi ini **bukan** satu karya yang dilisensikan ulang secara seragam. "
        "Setiap komponen mempertahankan lisensinya sendiri.\n\n"
        "## Pendamping orisinal C140\n\n"
        "Teks, kode, solusi, rubrik, dan aset orisinal dalam pendamping C140 "
        "dilisensikan berdasarkan Creative Commons Attribution-ShareAlike 4.0 "
        "International (CC BY-SA 4.0): "
        "https://creativecommons.org/licenses/by-sa/4.0/.\n\n"
        "Provenans produksi materi: `OpenAI Codex gpt-5.6-sol, Ultra`.\n\n"
        "## Dataset CP01\n\n"
        "Dataset *Concrete Compressive Strength* oleh I-Cheng Yeh, UCI Machine "
        "Learning Repository, DOI `10.24432/C5PK67`, tetap berlisensi CC BY 4.0 "
        "dan tidak dilisensikan ulang sebagai CC BY-SA. Atribusi yang dipertahankan:\n\n"
        "> Yeh, I. (1998). Concrete Compressive Strength [Dataset]. UCI Machine "
        "Learning Repository. https://doi.org/10.24432/C5PK67.\n\n"
        "README asli UCI juga meminta agar pemberitahuan hak cipta I-Cheng Yeh "
        "dan rujukan berikut dipertahankan:\n\n"
        "> Yeh, I.-C. (1998). “Modeling of strength of high-performance concrete "
        "using artificial neural networks.” *Cement and Concrete Research*, "
        "28(12), 1797–1808. "
        "https://doi.org/10.1016/S0008-8846(98)00165-3.\n\n"
        "## Dataset CP02\n\n"
        "Dua aset analitik dari versi 3 deposit Dryad "
        "`10.5061/dryad.573n5tbf3` tetap CC0-1.0. Dedikasi itu tidak diubah oleh "
        "lisensi pendamping. Sitasi ilmiah dipertahankan untuk provenans:\n\n"
        "> Stevens, Bryan; Conway, Courtney; Tisdale, Cody; Denny, Kylie; Meyers, "
        "Andrew; Makela, Paul (2023). *Supporting data for assessing impacts of "
        "satellite GPS transmitters on survival, nesting propensity, and nest "
        "success of greater sage-grouse*. Dryad, Dataset. "
        "https://doi.org/10.5061/dryad.573n5tbf3\n\n"
        "## Saksi hak dan provenans eksternal\n\n"
        "Saksi halaman, API, legal-code, dan tajuk HTTP yang disimpan verbatim "
        "hanya berfungsi sebagai bukti publik. Saksi itu berstatus `NOASSERTION`, "
        "tidak dilisensikan ulang sebagai materi pendamping, dan tetap tunduk pada "
        "hak atau ketentuan sumbernya masing-masing. Turunan redistribusi yang "
        "disunting demi keamanan memakai nama serta rekam perubahan terpisah.\n\n"
        "## Komponen yang diwarisi\n\n"
        "Aset Penn State STAT 415 (CC BY-NC 4.0 kecuali dinyatakan lain) dan "
        "donor *Random* Kyle Siegrist (saksi CC BY 2.0 pada laman utama; "
        "`Credits.html` menautkan CC BY 1.0) tetap terpisah. Tidak ada dukungan "
        "penerbit atau penulis sumber yang tersirat. MathJax 3.1.2 tetap berada "
        "di bawah Apache License 2.0; teks lisensinya disertakan dalam pembaca "
        "luring. Metadata platform untuk "
        "koleksi multi-lisensi ini adalah `other-open`.\n"
    ).encode("utf-8")


def compact_data_entries(snapshots: dict[str, dict[str, bytes]]) -> dict[str, bytes]:
    support = snapshots["support"]
    result = {
        relative: payload
        for relative, payload in support.items()
        if relative.startswith("data/capstones/")
    }
    credential_bearing = result.pop(CP02_CREDENTIAL_BEARING_WITNESS, None)
    if credential_bearing is None:
        raise RuntimeError("CP02 credential-bearing witness is missing")
    redacted, redaction_receipt = redact_cp02_public_client_key(
        credential_bearing
    )
    if (
        result.get(CP02_REDACTED_WITNESS) != redacted
        or result.get(CP02_REDACTION_RECEIPT) != redaction_receipt
    ):
        raise RuntimeError("durable CP02 redaction artifacts differ")
    merge_unique(
        result,
        {
            f"data/capstones/CP01/clean/{name}": payload
            for name, payload in snapshots["cp01_clean"].items()
        },
        label="CP01 clean data",
    )
    merge_unique(
        result,
        {
            f"data/capstones/CP02/clean/{name}": payload
            for name, payload in snapshots["cp02_clean"].items()
        },
        label="CP02 clean data",
    )
    return result


def new_entry(
    filename: str, payload: bytes, *, role: str, lineage: str
) -> dict[str, object]:
    return shared.entry(filename, payload, role=role, lineage=lineage)


def compute() -> tuple[dict[str, bytes], bytes]:
    outputs, rows, base_evidence = validate_base_public_union()
    (
        build,
        qa,
        receipt_identities,
        manifest_identities,
        support_identities,
        snapshots,
    ) = validate_c5_boundary()
    notes_payload = release_notes(build, qa)
    context_manifest_payload = repository_context_manifest()
    context_copying_payload = repository_context_copying()
    licenses_payload = license_notice(snapshots["support"])
    component_license = snapshots["support"]["LICENSE.md"]
    collection_license = snapshots["root_support"]["LICENSE.md"]
    rights_ledger = snapshots["root_support"]["00_control/RIGHTS_AND_COMPONENTS.md"]
    offline_entries = snapshots["html"]
    offline_payload, offline_gate = deterministic_zip(
        offline_entries, inventory_name="OFFLINE_READER_INVENTORY.json"
    )

    source_entries: dict[str, bytes] = {
        "README_RELEASE.md": notes_payload,
        "COMPONENT_AND_DATASET_LICENSES.md": licenses_payload,
        "LICENSE.md": component_license,
        "COLLECTION_LICENSE.md": collection_license,
        "RIGHTS_AND_COMPONENTS.md": rights_ledger,
        "repository-context/CONTEXT_MANIFEST.json": context_manifest_payload,
        "repository-context/COPYING.md": context_copying_payload,
    }
    merge_unique(
        source_entries,
        {
            f"repository-context/{relative}": payload
            for relative, payload in snapshots["repository_context"].items()
        },
        label="C5 reproducibility repository context",
    )
    static_source_entries = {
        "ci/hydrate_cp02_coverage.py": snapshots["root_support"][
            "scripts/hydrate_cp02_coverage.py"
        ],
        "ci/package_c140_companion_c1_release.py": snapshots["root_support"][
            "scripts/package_c140_companion_c1_release.py"
        ],
        "ci/package_c140_companion_c5_release.py": safe_read_file(
            Path(__file__).resolve(), label="C5 packager source"
        ),
    }
    for name in (
        "CONTENT_CONTRACT.md",
        "WORKFLOW.md",
        "C2_MATRIX_BATCH_CONTRACT.md",
        "C3_BAYESIAN_COMPARISON_BATCH_CONTRACT.md",
        "C4_MASTERY_BATCH_CONTRACT.md",
        "C5_ASSESSMENT_CAPSTONE_BATCH_CONTRACT.md",
    ):
        static_source_entries[f"00_control/{name}"] = snapshots["root_support"][
            f"components/c140-companion/00_control/{name}"
        ]
    merge_unique(source_entries, static_source_entries, label="static source")
    merge_unique(
        source_entries,
        {
            "environment.lock.json": snapshots["support"]["environment.lock.json"],
            "capstones/run_cp01_analysis.py": snapshots["support"][
                "capstones/run_cp01_analysis.py"
            ],
            "capstones/run_cp02_analysis.py": snapshots["support"][
                "capstones/run_cp02_analysis.py"
            ],
        },
        label="runtime and capstone source",
    )
    for relative in (
        "scripts/build_companion.py",
        "scripts/qa_companion.py",
        "simulations/run_c1_simulations.py",
        "simulations/run_c2_simulations.py",
        "simulations/run_c3_simulations.py",
    ):
        merge_unique(
            source_entries,
            {relative: snapshots["support"][relative]},
            label="build and simulation source",
        )
    merge_unique(source_entries, snapshots["source"], label="reader source")
    for batch in ("c1", "c2", "c3"):
        merge_unique(
            source_entries,
            {
                f"generated/simulations/{batch}/{name}": payload
                for name, payload in snapshots[f"simulation_{batch}"].items()
            },
            label=f"{batch} generated simulation",
        )
    for capstone in ("CP01", "CP02"):
        if capstone == "CP01" and snapshots["cp01_generated"].get(
            "CP01_REPLAY_RECEIPT.json"
        ) != snapshots["c5_receipts"][
            "generated/capstones/CP01/CP01_REPLAY_RECEIPT.json"
        ]:
            raise RuntimeError("CP01 generated/frozen replay receipt bytes differ")
        merge_unique(
            source_entries,
            {
                f"generated/capstones/{capstone}/{name}": payload
                for name, payload in snapshots[f"{capstone.casefold()}_generated"].items()
                if not (capstone == "CP02" and name == CP02_COVERAGE_RAW)
                and not (capstone == "CP01" and name == "CP01_REPLAY_RECEIPT.json")
            },
            label=f"{capstone} generated output",
        )
    merge_unique(
        source_entries,
        {f"backend/{name}": payload for name, payload in snapshots["backend"].items()},
        label="backend snapshot",
    )
    merge_unique(
        source_entries,
        compact_data_entries(snapshots),
        label="dataset evidence",
    )
    merge_unique(
        source_entries,
        snapshots["historical_receipts"],
        label="historical receipt",
    )
    merge_unique(
        source_entries,
        snapshots["c5_receipts"],
        label="C5 receipt",
    )
    if (
        f"generated/capstones/CP02/{CP02_COVERAGE_RAW}" in source_entries
        or source_entries.get(f"backend/{CP02_COVERAGE_GZIP}")
        != snapshots["backend"].get(CP02_COVERAGE_GZIP)
    ):
        raise RuntimeError("C5 source archive coverage-derivative policy differs")
    oversized_source_members = [
        name
        for name, payload in source_entries.items()
        if len(payload) > MAX_PUBLIC_FILE_BYTES
    ]
    if oversized_source_members:
        raise RuntimeError(
            "C5 source archive has oversized members: "
            f"{sorted(oversized_source_members)}"
        )
    source_payload, source_gate = deterministic_zip(
        source_entries, inventory_name="SOURCE_BACKEND_DATA_RIGHTS_INVENTORY.json"
    )

    qa_entries: dict[str, bytes] = {
        "environment.lock.json": snapshots["support"]["environment.lock.json"],
        "C4_RELEASE_PACKAGE_RECEIPT.json": base_evidence["package_receipt"],
        "C4_ZENODO_PUBLIC_READBACK.json": base_evidence["public_readback"],
        "C5_COMPONENT_LICENSE.md": component_license,
        "C5_COLLECTION_LICENSE.md": collection_license,
        "C5_RIGHTS_AND_COMPONENTS.md": rights_ledger,
        "C5_CURRENT_SIMULATION_BINDINGS.json": canonical_json(
            simulation_label_correction_metadata()
        ),
        "C5_REPOSITORY_CONTEXT_MANIFEST.json": context_manifest_payload,
        "CP01_DATASET_PROVENANCE.json": snapshots["support"][
            "data/capstones/CP01/DATASET_PROVENANCE.json"
        ],
        "CP01_DATASET_SHA256SUMS.txt": snapshots["support"][
            "data/capstones/CP01/SHA256SUMS"
        ],
        "CP02_DATASET_PROVENANCE.json": snapshots["support"][
            "data/capstones/CP02/DATASET_PROVENANCE.json"
        ],
        "CP02_INPUT_MANIFEST.csv": snapshots["support"][
            "data/capstones/CP02/INPUT_MANIFEST.csv"
        ],
        "CP02_RIGHTS_EVIDENCE.md": snapshots["support"][
            "data/capstones/CP02/RIGHTS_EVIDENCE.md"
        ],
        "CP02_SCHEMA.json": snapshots["support"][
            "data/capstones/CP02/SCHEMA.json"
        ],
    }
    for group in ("historical_receipts", "c5_receipts"):
        for relative, payload in sorted(snapshots[group].items()):
            name = Path(relative).name
            if name in qa_entries:
                raise RuntimeError(f"QA evidence filename collision: {name}")
            qa_entries[name] = payload
    for group in ("historical_manifests", "c5_manifests"):
        for relative, payload in sorted(snapshots[group].items()):
            name = relative.replace("/", "__")
            if name in qa_entries:
                raise RuntimeError(f"QA evidence filename collision: {name}")
            qa_entries[name] = payload
    qa_payload, qa_gate = deterministic_zip(
        qa_entries, inventory_name="QA_EVIDENCE_INVENTORY.json"
    )

    additions = [
        new_entry(
            OFFLINE_NAME,
            offline_payload,
            role="complete-c5-offline-html-reader",
            lineage="c140-original-companion-c5",
        ),
        new_entry(
            SOURCE_NAME,
            source_payload,
            role="complete-c5-resumable-source-backend-data-rights",
            lineage="c140-original-companion-c5",
        ),
        new_entry(
            NOTES_NAME,
            notes_payload,
            role="complete-c5-scope-status-provenance",
            lineage="c140-original-companion-c5",
        ),
        new_entry(
            LICENSE_NAME,
            licenses_payload,
            role="complete-c5-component-and-dataset-rights",
            lineage="c140-original-companion-c5",
        ),
        new_entry(
            QA_NAME,
            qa_payload,
            role="complete-c5-browser-free-static-qa-evidence",
            lineage="c140-original-companion-c5",
        ),
    ]
    for row, payload in zip(
        additions,
        [offline_payload, source_payload, notes_payload, licenses_payload, qa_payload],
        strict=True,
    ):
        name = str(row["filename"])
        if name in outputs:
            raise RuntimeError(f"C5 release filename collides: {name}")
        outputs[name] = payload
        rows.append(row)

    for upload_order, row in enumerate(rows, start=1):
        row["upload_order"] = upload_order
    structural_names = {MANIFEST_NAME, CHECKSUM_NAME, ROOT_NAME}
    structural_collisions = sorted(structural_names & outputs.keys())
    if structural_collisions:
        raise RuntimeError(
            f"C5 structural filename collisions: {structural_collisions}"
        )
    fields = [
        "upload_order",
        "filename",
        "bytes",
        "sha256",
        "role",
        "lineage",
        "media_type",
        "primary_reader",
        "source_path",
    ]
    manifest_payload = csv_bytes(fields, rows)
    manifest_row = new_entry(
        MANIFEST_NAME,
        manifest_payload,
        role="c5-cumulative-union-manifest",
        lineage="c140-original-companion-c5-union",
    )
    manifest_row["upload_order"] = len(rows) + 1
    outputs[MANIFEST_NAME] = manifest_payload

    checksum_covered = rows + [manifest_row]
    checksum_payload = "".join(
        f"{row['sha256']}  {row['filename']}\n" for row in checksum_covered
    ).encode("utf-8")
    checksum_row = new_entry(
        CHECKSUM_NAME,
        checksum_payload,
        role="c5-cumulative-union-checksums",
        lineage="c140-original-companion-c5-union",
    )
    checksum_row["upload_order"] = len(rows) + 2
    outputs[CHECKSUM_NAME] = checksum_payload

    root_covered = rows + [manifest_row, checksum_row]
    structural_inventory = {
        "publication_file_count": BASE_FILE_COUNT + 8,
        "manifest": {
            "filename": MANIFEST_NAME,
            "covered_file_count": len(rows),
            "excluded_later_or_self_referential_files": [
                MANIFEST_NAME,
                CHECKSUM_NAME,
                ROOT_NAME,
            ],
        },
        "checksums": {
            "filename": CHECKSUM_NAME,
            "covered_file_count": len(checksum_covered),
            "excluded_later_or_self_referential_files": [
                CHECKSUM_NAME,
                ROOT_NAME,
            ],
        },
        "root_receipt": {
            "filename": ROOT_NAME,
            "covered_file_count": len(root_covered),
            "excluded_self_referential_files": [ROOT_NAME],
        },
        "status": "complete-staged-non-self-referential-union",
    }
    root_payload = canonical_json(
        {
            "concept_doi": CONCEPT_DOI,
            "coverage": {
                "c140_course": "complete on the admitted component-separated boundary",
                "c140_original_companion": (
                    "complete: D001-D013, SIM001-SIM006, MS00-MS12, "
                    "CA01-CA04, CP01-CP02"
                ),
                "c5_batch": "complete",
                "penn_state_spine": "complete: landing/index plus Lesson00-Lesson12",
                "random_completeness_donor": "complete: exact one-page donor",
                "remaining": "none within the admitted C140 production boundary",
            },
            "execution_claims": {
                "browser_processes_used": False,
                "credential_access": False,
                "git_operations": False,
                "network_access": False,
                "publication_side_effects": False,
            },
            "file_count": len(root_covered),
            "files": root_covered,
            "preservation": {
                "base_public_readback_bytes": BASE_PUBLIC_READBACK_BYTES,
                "base_public_readback_sha256": BASE_PUBLIC_READBACK_SHA256,
                "inherited_files_byte_identical": True,
                "inherited_file_count": BASE_FILE_COUNT,
                "new_structural_file_count": 3,
                "new_substantive_file_count": 5,
            },
            "reader_order": {
                "first": "00_00_stat415-pengantar-statistika-matematis-id.pdf",
                "second": "00_01_stat415-pengantar-statistika-matematis-id.epub",
            },
            "rights": {
                "aggregate_uniform_relicense": False,
                "collection_license_bytes": len(collection_license),
                "collection_license_sha256": sha256(collection_license),
                "component_license_bytes": len(component_license),
                "component_license_sha256": sha256(component_license),
                "companion_license": "CC-BY-SA-4.0",
                "rights_ledger_bytes": len(rights_ledger),
                "rights_ledger_sha256": sha256(rights_ledger),
                "cp01_dataset_license": "CC-BY-4.0",
                "cp02_dataset_license": "CC0-1.0",
                "mathjax_license": "Apache-2.0",
                "penn_state_license": "CC-BY-NC-4.0-except-where-noted",
                "platform_license": "other-open",
                "public_contact_evidence_relicensed": False,
                "random_license_witnesses": ["CC-BY-2.0", "CC-BY-1.0"],
            },
            "schema": "o006.c140.companion-c5-full-union-root.v1",
            "self_exclusion": {
                "filename": ROOT_NAME,
                "reason": "non-self-referential cryptographic root",
            },
            "status": "ready",
            "structural_inventory": structural_inventory,
            "total_bytes_excluding_self": sum(
                int(row["bytes"]) for row in root_covered
            ),
            "version": VERSION,
        }
    )
    root_row = new_entry(
        ROOT_NAME,
        root_payload,
        role="c5-cumulative-union-root-receipt",
        lineage="c140-original-companion-c5-union",
    )
    root_row["upload_order"] = len(rows) + 3
    outputs[ROOT_NAME] = root_payload
    final_rows = rows + [manifest_row, checksum_row, root_row]

    if len(final_rows) != BASE_FILE_COUNT + 8:
        raise RuntimeError("C5 publication file count differs")
    final_names = [str(row["filename"]) for row in final_rows]
    validate_portable_namespace(final_names, label="C5 publication")
    if final_names != list(outputs):
        raise RuntimeError("C5 output order differs from upload inventory")
    if [int(row["upload_order"]) for row in final_rows] != list(
        range(1, BASE_FILE_COUNT + 9)
    ):
        raise RuntimeError("C5 publication upload-order closure differs")
    oversized = [
        str(row["filename"])
        for row in final_rows
        if int(row["bytes"]) > MAX_PUBLIC_FILE_BYTES
    ]
    if oversized:
        raise RuntimeError(f"C5 publication has oversized files: {oversized}")
    publication_bytes = sum(int(row["bytes"]) for row in final_rows)
    if publication_bytes > MAX_PUBLICATION_BYTES:
        raise RuntimeError("C5 publication exceeds the 500,000,000-byte cap")
    output_privacy_findings: list[dict[str, str]] = []
    for row in final_rows[BASE_FILE_COUNT:]:
        name = str(row["filename"])
        for finding in privacy_findings(name, outputs[name]):
            output_privacy_findings.append({"filename": name, "finding": finding})
    if output_privacy_findings:
        raise RuntimeError(
            f"privacy findings in new C5 outputs: {output_privacy_findings}"
        )

    public_email_evidence = [
        {
            "archive_path": archive_path,
            "bytes": FROZEN_C5_SUPPORT_INPUTS[origin_path][0],
            "origin_path": origin_path,
            "sha256": FROZEN_C5_SUPPORT_INPUTS[origin_path][1],
        }
        for archive_path, origin_path in sorted(
            PUBLIC_SOURCE_EMAIL_ALLOWLIST.items()
        )
    ]

    receipt = canonical_json(
        {
            "base_public_union": {
                "anonymous_readback": True,
                "bytes": BASE_TOTAL_BYTES,
                "concept_doi": CONCEPT_DOI,
                "concept_record_id": CONCEPT_RECORD_ID,
                "file_count": BASE_FILE_COUNT,
                "package_receipt": {
                    "bytes": BASE_PACKAGE_RECEIPT_BYTES,
                    "sha256": BASE_PACKAGE_RECEIPT_SHA256,
                },
                "public_readback": {
                    "bytes": BASE_PUBLIC_READBACK_BYTES,
                    "sha256": BASE_PUBLIC_READBACK_SHA256,
                },
                "record_doi": BASE_RECORD_DOI,
                "record_id": BASE_RECORD_ID,
                "version": BASE_VERSION,
            },
            "coverage": {
                "c140_course": "complete on admitted boundary",
                "c140_original_companion": "C5 complete checkpoint",
                "c5_batch": "complete",
                "penn_state_spine": "complete",
                "random_completeness_donor": "complete",
                "remaining": "none within admitted C140 boundary",
            },
            "gates": {
                "archives": {
                    OFFLINE_NAME: offline_gate,
                    SOURCE_NAME: source_gate,
                    QA_NAME: qa_gate,
                },
                "c5_boundary": {
                    "assessments": EXPECTED_ASSESSMENTS,
                    "backend_entities": build["backend"]["entities"],
                    "backend_relations": build["backend"]["relations"],
                    "capstones": EXPECTED_CAPSTONES,
                    "documents": EXPECTED_DOCUMENTS,
                    "html_files": build["html"]["files"],
                    "problems": EXPECTED_PROBLEMS,
                    "simulations": EXPECTED_SIMULATIONS,
                    "status": "pass",
                },
                "input_receipts": receipt_identities,
                "manifests": manifest_identities,
                "support_inputs": support_identities,
                "current_simulation_label_corrections": (
                    simulation_label_correction_metadata()
                ),
                "repository_context": {
                    "file_count": len(FROZEN_C5_REPOSITORY_CONTEXT_INPUTS),
                    "manifest_bytes": len(context_manifest_payload),
                    "manifest_path": "repository-context/CONTEXT_MANIFEST.json",
                    "manifest_sha256": sha256(context_manifest_payload),
                    "status": "frozen",
                },
                "package_replay_contract": {
                    "post_write_full_recomputations": 2,
                    "post_write_output_byte_checks": 2,
                    "required_external_check_only_invocations": 2,
                    "status": "enforced-by-write-mode",
                },
                "privacy": {
                    "forbidden_markers_found": 0,
                    "public_source_email_evidence": public_email_evidence,
                    "public_source_email_policy": (
                        "allowed only at exact named archive aliases when bytes and "
                        "SHA-256 match a frozen publisher/legal-contact evidence origin"
                    ),
                },
                "publication_size": {
                    "bytes": publication_bytes,
                    "cap_bytes": MAX_PUBLICATION_BYTES,
                    "file_cap_bytes": MAX_PUBLIC_FILE_BYTES,
                    "maximum_file_bytes": max(
                        int(row["bytes"]) for row in final_rows
                    ),
                    "status": "pass",
                },
                "structural_inventory": structural_inventory,
            },
            "lineage": {
                "base_record_doi": BASE_RECORD_DOI,
                "base_record_id": BASE_RECORD_ID,
                "concept_doi": CONCEPT_DOI,
                "concept_record_id": CONCEPT_RECORD_ID,
                "create_competing_concept": False,
            },
            "outputs": {
                "checksums": {
                    "filename": CHECKSUM_NAME,
                    "bytes": len(checksum_payload),
                    "sha256": sha256(checksum_payload),
                },
                "manifest": {
                    "filename": MANIFEST_NAME,
                    "bytes": len(manifest_payload),
                    "sha256": sha256(manifest_payload),
                },
                "root_receipt": {
                    "filename": ROOT_NAME,
                    "bytes": len(root_payload),
                    "sha256": sha256(root_payload),
                },
            },
            "packager": {
                "browser_processes_used": False,
                "credential_access": False,
                "git_operations": False,
                "network_access": False,
                "path": "scripts/package_c140_companion_c5_release.py",
                "publication_side_effects": False,
                "recursive_repository_discovery": False,
                "source_bytes": len(
                    static_source_entries[
                        "ci/package_c140_companion_c5_release.py"
                    ]
                ),
                "source_sha256": sha256(
                    static_source_entries[
                        "ci/package_c140_companion_c5_release.py"
                    ]
                ),
            },
            "preservation": {
                "inherited_files_byte_identical": True,
                "inherited_file_count": BASE_FILE_COUNT,
                "new_file_count": len(final_rows) - BASE_FILE_COUNT,
                "new_substantive_file_count": 5,
            },
            "publication_inventory": {
                "bytes": publication_bytes,
                "file_count": len(final_rows),
                "files": final_rows,
            },
            "reader_order": {
                "inherited_union_first": True,
                "pdf_upload_order": 1,
                "epub_upload_order": 2,
                "c5_first_upload_order": BASE_FILE_COUNT + 1,
            },
            "rights": {
                "aggregate_uniform_relicense": False,
                "collection_license_bytes": len(collection_license),
                "collection_license_sha256": sha256(collection_license),
                "component_license_bytes": len(component_license),
                "component_license_sha256": sha256(component_license),
                "component_licenses_unchanged": True,
                "companion_license": "CC-BY-SA-4.0",
                "cp01_dataset_license": "CC-BY-4.0",
                "cp02_dataset_license": "CC0-1.0",
                "mathjax_license": "Apache-2.0",
                "penn_state_license": "CC-BY-NC-4.0-except-where-noted",
                "platform_license": "other-open",
                "public_contact_evidence_relicensed": False,
                "random_license_witnesses": ["CC-BY-2.0", "CC-BY-1.0"],
                "rights_ledger_bytes": len(rights_ledger),
                "rights_ledger_sha256": sha256(rights_ledger),
            },
            "schema": SCHEMA,
            "status": "ready",
            "version": VERSION,
        }
    )
    return outputs, receipt


def verify_outputs(outputs: dict[str, bytes], receipt: bytes) -> list[str]:
    errors: list[str] = []
    for name, payload in outputs.items():
        path = RELEASE / name
        if is_reparse(path):
            errors.append(f"unsafe-reparse:{name}")
        elif not path.is_file():
            errors.append(f"missing:{name}")
        elif safe_read_file(path, label=f"release output {name}") != payload:
            errors.append(f"mismatch:{name}")
    if is_reparse(PACKAGE_RECEIPT):
        errors.append("unsafe-reparse:package-receipt")
    elif not PACKAGE_RECEIPT.is_file():
        errors.append("missing:package-receipt")
    elif safe_read_file(PACKAGE_RECEIPT, label="package receipt output") != receipt:
        errors.append("mismatch:package-receipt")
    return errors


def is_reparse(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    return path.is_symlink() or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def atomic_write(path: Path, payload: bytes) -> None:
    relative_label = path.absolute().relative_to(ROOT.absolute()).as_posix()
    assert_bounded_nonreparse(path, label="package output")
    if is_reparse(path) or is_reparse(path.parent):
        raise RuntimeError(f"refusing reparse-point output: {relative_label}")
    if path.exists() and not path.is_file():
        raise RuntimeError(f"refusing non-file output target: {relative_label}")
    path.parent.mkdir(parents=True, exist_ok=True)
    assert_bounded_nonreparse(path.parent, label="package output directory")
    if is_reparse(path.parent):
        raise RuntimeError(f"unsafe output directory: {relative_label}")
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="xb", dir=path.parent, prefix=f".{path.name}.c5-", delete=False
        ) as stream:
            temp_path = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        assert_bounded_nonreparse(temp_path, label="temporary package output")
        if (
            is_reparse(temp_path)
            or safe_read_file(temp_path, label="temporary package output") != payload
        ):
            raise RuntimeError(f"temporary output verification failed: {relative_label}")
        assert_bounded_nonreparse(path.parent, label="package output directory")
        os.replace(temp_path, path)
        temp_path = None
        assert_bounded_nonreparse(path, label="package output")
        if (
            is_reparse(path)
            or safe_read_file(path, label="package output") != payload
        ):
            raise RuntimeError(f"atomic output verification failed: {relative_label}")
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--base-only", action="store_true")
    mode.add_argument("--contract-only", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.base_only:
        outputs, rows, _readback = validate_base_public_union()
        print(
            json.dumps(
                {
                    "bytes": sum(len(payload) for payload in outputs.values()),
                    "files": len(rows),
                    "mode": "base-only",
                    "status": "pass",
                    "version": BASE_VERSION,
                },
                sort_keys=True,
            )
        )
        return

    outputs, receipt = compute()
    package = json.loads(receipt)
    if args.contract_only:
        state = "contract-only"
    elif args.write:
        RELEASE.mkdir(parents=True, exist_ok=True)
        for name in tuple(outputs)[BASE_FILE_COUNT:]:
            atomic_write(RELEASE / name, outputs[name])
        atomic_write(PACKAGE_RECEIPT, receipt)
        errors = verify_outputs(outputs, receipt)
        if errors:
            raise RuntimeError("written C5 package differs: " + ", ".join(errors[:40]))
        for replay_index in range(1, 3):
            replay_outputs, replay_receipt = compute()
            if replay_outputs != outputs or replay_receipt != receipt:
                raise RuntimeError(
                    f"post-write C5 recomputation {replay_index} differs"
                )
            replay_errors = verify_outputs(replay_outputs, replay_receipt)
            if replay_errors:
                raise RuntimeError(
                    f"post-write C5 byte replay {replay_index} differs: "
                    + ", ".join(replay_errors[:40])
                )
        state = "written"
    else:
        errors = verify_outputs(outputs, receipt)
        if errors:
            raise RuntimeError("C5 package replay differs: " + ", ".join(errors[:40]))
        state = "verified"

    print(
        json.dumps(
            {
                "bytes": package["publication_inventory"]["bytes"],
                "credential_access": False,
                "files": package["publication_inventory"]["file_count"],
                "inherited_files": BASE_FILE_COUNT,
                "mode": state,
                "network_access": False,
                "new_files": package["preservation"]["new_file_count"],
                "receipt_sha256": sha256(receipt),
                "status": "pass",
                "version": VERSION,
            },
            sort_keys=True,
        )
    )


def sanitized_error(exc: BaseException) -> str:
    message = str(exc)
    for path, replacement in (
        (str(COMPONENT), "<component>"),
        (str(ROOT), "<repository>"),
    ):
        message = message.replace(path, replacement)
    message = re.sub(
        r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s]+", "<local-user-path>", message
    )
    message = re.sub(r"/(?:home|Users)/[^/\s]+", "<local-user-path>", message)
    return message


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        raise SystemExit(f"ERROR: {sanitized_error(exc)}") from None
