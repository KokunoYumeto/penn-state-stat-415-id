#!/usr/bin/env python3
"""Freeze or verify the exact MathJax 3.1.2 offline runtime and licence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
from pathlib import Path

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "authority" / "runtime" / "MathJax-3.1.2"
RECEIPT = RUNTIME / "FREEZE_RECEIPT.json"
MANIFEST = RUNTIME / "URL_MANIFEST.csv"
FILES = (
    (
        "tex-svg.js",
        "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/tex-svg.js",
        1704911,
        "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a",
    ),
    (
        "LICENSE.txt",
        "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/LICENSE",
        11358,
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    ),
    (
        "input/tex/extensions/color.js",
        "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/input/tex/extensions/color.js",
        9192,
        "412863c1ea3db035795f39a6850f963261b81d260de61862c85013b2c96c01d7",
    ),
    (
        "input/tex/extensions/enclose.js",
        "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/input/tex/extensions/enclose.js",
        3071,
        "fed0d0fca9402ad9f23bba26a158cc6a802a267f900c238769e16ed30b4410ab",
    ),
    (
        "input/tex/extensions/cancel.js",
        "https://cdn.jsdelivr.net/npm/mathjax@3.1.2/es5/input/tex/extensions/cancel.js",
        4029,
        "6b5ede35a63fb92d69e0648755746867efdbaebbf452506ebd878c33568aadf0",
    ),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(data)
        temporary = Path(stream.name)
    temporary.replace(path)


def evidence_payloads(file_payloads: dict[str, bytes]) -> dict[str, bytes]:
    rows = []
    for filename, url, expected_bytes, expected_sha in FILES:
        data = file_payloads[filename]
        if len(data) != expected_bytes or sha256(data) != expected_sha:
            raise RuntimeError(f"MathJax authority identity differs: {filename}")
        rows.append(
            {
                "relative_path": filename,
                "url": url,
                "bytes": len(data),
                "sha256": sha256(data),
                "component": "MathJax 3.1.2",
                "license": "Apache-2.0",
            }
        )
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=tuple(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    manifest = output.getvalue().encode("utf-8")
    receipt = {
        "schema": "o006.stat415.mathjax-freeze.v1",
        "component": "MathJax",
        "version": "3.1.2",
        "license": "Apache-2.0",
        "distribution": "official npm mathjax package served by jsDelivr",
        "files": rows,
        "file_count": len(rows),
        "total_bytes": sum(len(value) for value in file_payloads.values()),
        "manifest": {
            "path": MANIFEST.relative_to(ROOT).as_posix(),
            "bytes": len(manifest),
            "sha256": sha256(manifest),
        },
    }
    return {
        MANIFEST.relative_to(ROOT).as_posix(): manifest,
        RECEIPT.relative_to(ROOT).as_posix(): canonical_json(receipt),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    if args.write:
        truststore.inject_into_ssl()
        session = requests.Session()
        file_payloads: dict[str, bytes] = {}
        for filename, url, _, _ in FILES:
            response = session.get(url, timeout=90)
            response.raise_for_status()
            file_payloads[filename] = response.content
        evidence = evidence_payloads(file_payloads)
        for filename, data in file_payloads.items():
            atomic_write(RUNTIME / filename, data)
        for relative, data in evidence.items():
            atomic_write(ROOT / relative, data)
        state = "written"
    else:
        file_payloads = {}
        for filename, _, _, _ in FILES:
            path = RUNTIME / filename
            if not path.is_file():
                raise RuntimeError(f"missing MathJax authority: {filename}")
            file_payloads[filename] = path.read_bytes()
        evidence = evidence_payloads(file_payloads)
        for relative, data in evidence.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != data:
                raise RuntimeError(f"MathJax evidence differs: {relative}")
        state = "verified"
    receipt_data = evidence[RECEIPT.relative_to(ROOT).as_posix()]
    print(json.dumps({"mode": state, "files": len(FILES), "bytes": sum(map(len, file_payloads.values())), "receipt_sha256": sha256(receipt_data)}, sort_keys=True))


if __name__ == "__main__":
    main()
