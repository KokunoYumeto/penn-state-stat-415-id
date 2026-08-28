#!/usr/bin/env python3
"""Assemble the Penn reader and isolated Random donor for GitHub Pages.

The Penn reader is selected from the files tracked below ``build/html-id`` and
copied byte-for-byte to ``build/pages``.  The donor is mounted below the
collision-resistant ``components/random-completeness`` prefix.  No HTML, CSS,
JavaScript, image, or other reader payload is transformed by this script.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
PENN_SOURCE = ROOT / "build" / "html-id"
DONOR_SOURCE = ROOT / "components" / "random-completeness" / "build" / "html-id"
DESTINATION = ROOT / "build" / "pages"
RECEIPT = ROOT / "build" / "PAGES_COLLECTION_RECEIPT.json"
DONOR_MOUNT = PurePosixPath("components/random-completeness")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def validate_relative(relative: PurePosixPath, *, label: str) -> None:
    if relative.is_absolute() or not relative.parts:
        raise RuntimeError(f"{label} is not a non-empty relative path: {relative}")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError(f"{label} contains an unsafe path segment: {relative}")


def tracked_penn_files() -> list[tuple[PurePosixPath, Path]]:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--", "build/html-id"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        tracked = [
            PurePosixPath(item.decode("utf-8"))
            for item in completed.stdout.split(b"\0")
            if item
        ]
    except UnicodeDecodeError as exc:
        raise RuntimeError("tracked Penn reader paths are not UTF-8") from exc

    prefix = PurePosixPath("build/html-id")
    result: list[tuple[PurePosixPath, Path]] = []
    for repository_relative in tracked:
        try:
            reader_relative = repository_relative.relative_to(prefix)
        except ValueError as exc:
            raise RuntimeError(
                f"git returned a path outside the Penn reader: {repository_relative}"
            ) from exc
        validate_relative(reader_relative, label="Penn reader path")
        source = ROOT.joinpath(*repository_relative.parts)
        if source.is_symlink() or not source.is_file():
            raise RuntimeError(f"tracked Penn reader file is missing or unsafe: {repository_relative}")
        result.append((reader_relative, source))

    if not result:
        raise RuntimeError("no tracked Penn reader files were found below build/html-id")
    return sorted(result, key=lambda item: item[0].as_posix())


def donor_files() -> list[tuple[PurePosixPath, Path]]:
    if DONOR_SOURCE.is_symlink() or not DONOR_SOURCE.is_dir():
        raise RuntimeError(
            "isolated donor reader is missing or unsafe: "
            "components/random-completeness/build/html-id"
        )

    result: list[tuple[PurePosixPath, Path]] = []
    for candidate in DONOR_SOURCE.rglob("*"):
        if candidate.is_symlink():
            raise RuntimeError(
                "isolated donor reader contains a symlink: "
                f"{candidate.relative_to(ROOT).as_posix()}"
            )
        if not candidate.is_file():
            continue
        relative = PurePosixPath(candidate.relative_to(DONOR_SOURCE).as_posix())
        validate_relative(relative, label="donor reader path")
        result.append((relative, candidate))

    if not result:
        raise RuntimeError("the isolated donor reader contains no files")
    return sorted(result, key=lambda item: item[0].as_posix())


def file_identity(path: Path) -> tuple[int, str]:
    payload = path.read_bytes()
    return len(payload), sha256(payload)


def manifest_sha256(entries: list[dict[str, object]]) -> str:
    manifest = "".join(
        f"{entry['path']}\t{entry['bytes']}\t{entry['sha256']}\n"
        for entry in entries
    ).encode("utf-8")
    return sha256(manifest)


def compute() -> tuple[dict[PurePosixPath, Path], bytes]:
    penn = tracked_penn_files()
    donor = donor_files()

    collection: dict[PurePosixPath, Path] = {}
    records: list[dict[str, object]] = []
    penn_records: list[dict[str, object]] = []
    donor_records: list[dict[str, object]] = []

    def register(
        collection_relative: PurePosixPath,
        source: Path,
        *,
        source_name: str,
        source_relative: PurePosixPath,
    ) -> None:
        validate_relative(collection_relative, label="collection path")
        if collection_relative in collection:
            raise RuntimeError(f"Pages collection collision: {collection_relative}")
        folded = collection_relative.as_posix().casefold()
        for existing in collection:
            if existing.as_posix().casefold() == folded:
                raise RuntimeError(
                    "case-insensitive Pages collection collision: "
                    f"{existing} and {collection_relative}"
                )
        size, digest = file_identity(source)
        collection[collection_relative] = source
        source_record = {
            "path": source_relative.as_posix(),
            "bytes": size,
            "sha256": digest,
        }
        collection_record = {
            "path": collection_relative.as_posix(),
            "bytes": size,
            "sha256": digest,
            "source": source_name,
            "source_path": source_relative.as_posix(),
        }
        records.append(collection_record)
        if source_name == "penn-reader":
            penn_records.append(source_record)
        else:
            donor_records.append(source_record)

    for relative, source in penn:
        register(
            relative,
            source,
            source_name="penn-reader",
            source_relative=relative,
        )
    for relative, source in donor:
        register(
            DONOR_MOUNT / relative,
            source,
            source_name="random-completeness-donor",
            source_relative=relative,
        )

    records.sort(key=lambda item: str(item["path"]))
    penn_records.sort(key=lambda item: str(item["path"]))
    donor_records.sort(key=lambda item: str(item["path"]))
    receipt = {
        "schema": "o006.c140.pages-collection.v1",
        "status": "assembled",
        "generated_by": "scripts/assemble_pages_collection.py",
        "browser_used": False,
        "inputs": {
            "penn_reader": {
                "path": "build/html-id",
                "selection": "git-tracked-files-only",
                "files": len(penn_records),
                "bytes": sum(int(item["bytes"]) for item in penn_records),
                "manifest_sha256": manifest_sha256(penn_records),
            },
            "random_completeness_donor": {
                "path": "components/random-completeness/build/html-id",
                "mount": DONOR_MOUNT.as_posix(),
                "files": len(donor_records),
                "bytes": sum(int(item["bytes"]) for item in donor_records),
                "manifest_sha256": manifest_sha256(donor_records),
            },
        },
        "collection": {
            "path": "build/pages",
            "files": len(records),
            "bytes": sum(int(item["bytes"]) for item in records),
            "manifest_sha256": manifest_sha256(records),
        },
        "verification": {
            "collisions": 0,
            "case_insensitive_collisions": 0,
            "penn_reader_files_byte_identical": True,
            "random_completeness_files_byte_identical": True,
            "payload_transformations": 0,
        },
        "files": records,
    }
    return collection, canonical_json(receipt)


def verify_directory(collection: dict[PurePosixPath, Path], root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise RuntimeError(f"Pages collection directory is missing or unsafe: {root}")

    actual: set[PurePosixPath] = set()
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise RuntimeError(
                f"Pages collection contains a symlink: {candidate.relative_to(ROOT)}"
            )
        if candidate.is_file():
            actual.add(PurePosixPath(candidate.relative_to(root).as_posix()))
    expected = set(collection)
    if actual != expected:
        missing = sorted(path.as_posix() for path in expected - actual)
        extra = sorted(path.as_posix() for path in actual - expected)
        raise RuntimeError(
            f"Pages collection inventory differs; missing={missing}, extra={extra}"
        )

    for relative, source in collection.items():
        assembled = root.joinpath(*relative.parts)
        if assembled.read_bytes() != source.read_bytes():
            raise RuntimeError(f"Pages collection payload differs: {relative}")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_collection(collection: dict[PurePosixPath, Path], receipt: bytes) -> None:
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".pages-stage-", dir=DESTINATION.parent))
    try:
        for relative, source in collection.items():
            target = stage.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        verify_directory(collection, stage)

        if DESTINATION.exists() or DESTINATION.is_symlink():
            if DESTINATION.is_symlink() or not DESTINATION.is_dir():
                raise RuntimeError("refusing to replace unsafe build/pages target")
            shutil.rmtree(DESTINATION)
        stage.rename(DESTINATION)
        verify_directory(collection, DESTINATION)
        atomic_write(RECEIPT, receipt)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    collection, receipt = compute()
    if args.check_only:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != receipt:
            raise RuntimeError("tracked Pages collection receipt differs")
        verify_directory(collection, DESTINATION)
        state = "verified"
    else:
        write_collection(collection, receipt)
        state = "written"

    parsed = json.loads(receipt)
    print(
        json.dumps(
            {
                "mode": state,
                "status": parsed["status"],
                "files": parsed["collection"]["files"],
                "bytes": parsed["collection"]["bytes"],
                "manifest_sha256": parsed["collection"]["manifest_sha256"],
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
