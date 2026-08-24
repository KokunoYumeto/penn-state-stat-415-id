#!/usr/bin/env python3
"""Create deterministic reader-first preservation packages for the first unit."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
READER = ROOT / "build" / "html-id"
READER_MANIFEST = ROOT / "build" / "FIRST_UNIT_MANIFEST.csv"
QA = ROOT / "build" / "FIRST_UNIT_QA_RECEIPT.json"
VISUAL_QA = ROOT / "build" / "FIRST_UNIT_VISUAL_QA_RECEIPT.json"
LICENSE = ROOT / "LICENSE.md"
READER_ZIP = "00_stat415-id-first-unit-offline-reader.zip"
SOURCE_ZIP = "10_stat415-id-first-unit-source-backend.zip"
RELEASE_NOTES = "20_FIRST_UNIT_RELEASE_NOTES.md"
RELEASE_MANIFEST = "50_RELEASE_MANIFEST.csv"
CHECKSUMS = "SHA256SUMS.txt"
RECEIPT = ROOT / "build" / "FIRST_UNIT_PACKAGE_RECEIPT.json"
ZIP_TIME = (2026, 8, 24, 0, 0, 0)
SOURCE_ROOTS = (
    ".github", "00_control", "authority", "backend", "scripts", "source", "working",
)
SOURCE_FILES = (".gitattributes", ".gitignore", "LICENSE.md", "README.md", "requirements.txt")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=path.name + ".", suffix=".tmp", delete=False) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def archive(files: dict[PurePosixPath, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(files, key=lambda value: value.as_posix().casefold()):
            info = zipfile.ZipInfo(path.as_posix(), ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            bundle.writestr(info, files[path], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    payload = output.getvalue()
    with zipfile.ZipFile(io.BytesIO(payload), "r") as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError("release ZIP integrity test failed")
        names = bundle.namelist()
        if names != [path.as_posix() for path in sorted(files, key=lambda value: value.as_posix().casefold())]:
            raise RuntimeError("release ZIP entry inventory differs")
        for name, expected in ((path.as_posix(), data) for path, data in files.items()):
            if bundle.read(name) != expected:
                raise RuntimeError(f"release ZIP entry identity differs: {name}")
    return payload


def reader_package() -> tuple[bytes, int, int]:
    with READER_MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    files: dict[PurePosixPath, bytes] = {}
    for row in rows:
        relative = PurePosixPath(row["relative_path"])
        data = (READER / Path(relative.as_posix())).read_bytes()
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {relative}")
        files[PurePosixPath("stat415-id-first-unit") / relative] = data
    files[PurePosixPath("stat415-id-first-unit/FIRST_UNIT_MANIFEST.csv")] = READER_MANIFEST.read_bytes()
    return archive(files), len(files), sum(len(value) for value in files.values())


def source_package() -> tuple[bytes, int, int]:
    files: dict[PurePosixPath, bytes] = {}
    for filename in SOURCE_FILES:
        path = ROOT / filename
        if not path.is_file():
            raise RuntimeError(f"source-package file missing: {filename}")
        files[PurePosixPath("penn-state-stat-415-id") / PurePosixPath(filename)] = path.read_bytes()
    for dirname in SOURCE_ROOTS:
        base = ROOT / dirname
        for path in sorted(base.rglob("*"), key=lambda value: value.as_posix().casefold()):
            if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                continue
            relative = PurePosixPath(path.relative_to(ROOT).as_posix())
            files[PurePosixPath("penn-state-stat-415-id") / relative] = path.read_bytes()
    for path in (
        ROOT / "build" / "FIRST_UNIT_NORMALIZATION_RECEIPT.json",
        ROOT / "build" / "FIRST_UNIT_TRANSLATION_RECEIPT.json",
        ROOT / "build" / "FIRST_UNIT_BUILD_RECEIPT.json",
        ROOT / "build" / "FIRST_UNIT_MANIFEST.csv",
        ROOT / "build" / "FIRST_UNIT_QA_RECEIPT.json",
        ROOT / "build" / "FIRST_UNIT_VISUAL_QA_RECEIPT.json",
    ):
        files[PurePosixPath("penn-state-stat-415-id") / PurePosixPath(path.relative_to(ROOT).as_posix())] = path.read_bytes()
    return archive(files), len(files), sum(len(value) for value in files.values())


def notes_payload() -> bytes:
    return (
        "# STAT 415 — edisi Bahasa Indonesia: unit pertama\n\n"
        "Status: **sebagian; 2 dari 14 dokumen lengkap**. Paket ini memuat laman "
        "utama dan seluruh Pelajaran 00 dalam Bahasa Indonesia. Pelajaran 01–12 "
        "belum diterjemahkan dan tetap menaut ke sumber resmi berbahasa Inggris.\n\n"
        "Pembaca luring adalah berkas utama. Ekstrak ZIP pembaca dan buka "
        "`index.html` melalui peladen HTTP statis. Paket source-backend memuat "
        "otoritas beku, terjemahan, backend modular, skrip reproduksi, lisensi, "
        "dan bukti QA yang diperlukan untuk melanjutkan edisi.\n\n"
        "Konten Penn State tetap CC BY-NC 4.0 kecuali dinyatakan lain; MathJax "
        "3.1.2 tetap Apache-2.0; lapisan asli repositori memiliki lisensi "
        "terpisah. Lihat `LICENSE.md`. Tidak ada dukungan atau pengesahan oleh "
        "Penn State yang tersirat.\n\n"
        "Provenans terjemahan: OpenAI Codex gpt-5.6-sol, Ultra.\n"
    ).encode("utf-8")


def compute() -> tuple[dict[str, bytes], bytes]:
    reader_zip, reader_entries, reader_uncompressed = reader_package()
    source_zip, source_entries, source_uncompressed = source_package()
    notes = notes_payload()
    payloads: dict[str, bytes] = {
        READER_ZIP: reader_zip,
        SOURCE_ZIP: source_zip,
        RELEASE_NOTES: notes,
        "30_LICENSE.md": LICENSE.read_bytes(),
        "40_FIRST_UNIT_QA_RECEIPT.json": QA.read_bytes(),
        "41_FIRST_UNIT_VISUAL_QA_RECEIPT.json": VISUAL_QA.read_bytes(),
    }
    manifest_output = io.StringIO(newline="")
    writer = csv.DictWriter(manifest_output, fieldnames=("filename", "bytes", "sha256", "role"), lineterminator="\n")
    writer.writeheader()
    roles = {
        READER_ZIP: "primary-offline-reader",
        SOURCE_ZIP: "resumable-source-backend",
        RELEASE_NOTES: "scope-and-status",
        "30_LICENSE.md": "component-rights",
        "40_FIRST_UNIT_QA_RECEIPT.json": "deterministic-qa",
        "41_FIRST_UNIT_VISUAL_QA_RECEIPT.json": "desktop-mobile-qa",
    }
    for filename, data in payloads.items():
        writer.writerow({"filename": filename, "bytes": len(data), "sha256": sha256(data), "role": roles[filename]})
    manifest = manifest_output.getvalue().encode("utf-8")
    payloads[RELEASE_MANIFEST] = manifest
    checksums = "".join(f"{sha256(data)}  {filename}\n" for filename, data in payloads.items()).encode("utf-8")
    payloads[CHECKSUMS] = checksums
    receipt = {
        "schema": "o006.stat415.first-unit-package.v1", "status": "ready",
        "coverage": "landing/index plus complete Lesson00; 2 of 14 documents",
        "files": [{"filename": filename, "bytes": len(data), "sha256": sha256(data)} for filename, data in payloads.items()],
        "file_count": len(payloads), "total_bytes": sum(len(data) for data in payloads.values()),
        "reader_zip": {"entries": reader_entries, "uncompressed_bytes": reader_uncompressed},
        "source_zip": {"entries": source_entries, "uncompressed_bytes": source_uncompressed},
        "upload_order": list(payloads),
    }
    return payloads, canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    payloads, receipt = compute()
    outputs = {f"release/{name}": data for name, data in payloads.items()}
    outputs[RECEIPT.relative_to(ROOT).as_posix()] = receipt
    if args.write:
        for relative, data in outputs.items():
            atomic_write(ROOT / relative, data)
        state = "written"
    else:
        for relative, data in outputs.items():
            path = ROOT / relative
            if not path.is_file() or path.read_bytes() != data:
                raise RuntimeError(f"release-package output differs: {relative}")
        state = "verified"
    info = json.loads(receipt)
    print(json.dumps({"mode": state, "files": info["file_count"], "bytes": info["total_bytes"], "receipt_sha256": sha256(receipt)}, sort_keys=True))


if __name__ == "__main__":
    main()
