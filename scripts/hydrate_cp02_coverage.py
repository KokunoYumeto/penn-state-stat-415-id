#!/usr/bin/env python3
"""Restore the untracked CP02 ledger from its pinned public gzip, without overwrite.

The canonical ledger exceeds GitHub's file-size limit.  CI restores these exact
bytes before independently recomputing them with run_cp02_analysis.py --check-only.
Only the missing ledger may be created; every other input remains read-only.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
from typing import BinaryIO


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "components/c140-companion/backend/assets/capstones/CP02/CP02_coverage.csv.gz"
TARGET = ROOT / "components/c140-companion/generated/capstones/CP02/CP02_coverage.csv"
COMPRESSED_BYTES = 5_761_556
COMPRESSED_SHA256 = "9f4db98147a57db21ccc424bc9e4292ceecd7c113e6733cf580ed1834b82b106"
RAW_BYTES = 135_581_717
RAW_SHA256 = "86997c120a94e342d943ae72eb827871564e96545de911d1e3a3c677a5bc347e"
CHUNK_BYTES = 1_048_576


def checked_path(path: Path, *, missing_leaf: bool = False) -> bool:
    """Reject escaping paths, symbolic links, Windows reparse points, and nonfiles."""
    relative = path.relative_to(ROOT)
    if not relative.parts or ".." in relative.parts:
        raise RuntimeError(f"unsafe hydration path: {path}")
    current = ROOT
    for index, part in enumerate(relative.parts):
        current /= part
        leaf = index == len(relative.parts) - 1
        try:
            info = current.lstat()
        except FileNotFoundError:
            if leaf and missing_leaf:
                return False
            raise RuntimeError(f"missing hydration path: {current}") from None
        if stat.S_ISLNK(info.st_mode) or (
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        ):
            raise RuntimeError(f"linked hydration path is prohibited: {current}")
        if not (stat.S_ISREG(info.st_mode) if leaf else stat.S_ISDIR(info.st_mode)):
            raise RuntimeError(f"unexpected hydration path type: {current}")
    return True


def read_only_file(path: Path) -> BinaryIO:
    checked_path(path)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise RuntimeError(f"hydration input is not a regular file: {path}")
    return os.fdopen(descriptor, "rb")


def verify_stream(
    stream: BinaryIO,
    expected_bytes: int,
    expected_sha256: str,
    label: str,
    sink: BinaryIO | None = None,
) -> None:
    digest = hashlib.sha256()
    count = 0
    while True:
        # One excess byte detects a size mismatch without expanding an unbounded gzip.
        chunk = stream.read(min(CHUNK_BYTES, expected_bytes - count + 1))
        if not chunk:
            break
        count += len(chunk)
        if count > expected_bytes:
            raise RuntimeError(f"{label} exceeds its pinned byte count {expected_bytes}")
        digest.update(chunk)
        if sink is not None:
            sink.write(chunk)
    observed_sha256 = digest.hexdigest()
    if count != expected_bytes or observed_sha256 != expected_sha256:
        raise RuntimeError(
            f"{label} identity differs: expected {expected_bytes}/{expected_sha256}, "
            f"observed {count}/{observed_sha256}"
        )


def verify_target() -> None:
    with read_only_file(TARGET) as stream:
        verify_stream(stream, RAW_BYTES, RAW_SHA256, "canonical CP02 coverage ledger")


def hydrate(*, check_only: bool) -> str:
    with read_only_file(SOURCE) as source:
        verify_stream(source, COMPRESSED_BYTES, COMPRESSED_SHA256, "public CP02 gzip")
        if checked_path(TARGET, missing_leaf=True):
            verify_target()
            return "verified"
        if check_only:
            raise RuntimeError("canonical CP02 coverage ledger is missing; run with --write")

        descriptor, name = tempfile.mkstemp(prefix=".CP02_coverage.hydrate-", dir=TARGET.parent)
        temporary = Path(name)
        try:
            with os.fdopen(descriptor, "wb") as output:
                source.seek(0)
                with gzip.GzipFile(fileobj=source, mode="rb") as archive:
                    verify_stream(archive, RAW_BYTES, RAW_SHA256, "expanded CP02 gzip", output)
                output.flush()
                os.fsync(output.fileno())
            with read_only_file(temporary) as staged:
                verify_stream(staged, RAW_BYTES, RAW_SHA256, "staged CP02 coverage ledger")
            checked_path(TARGET, missing_leaf=True)
            try:
                # Hard-link publication is atomic and never replaces an existing target.
                os.link(temporary, TARGET)
            except FileExistsError:
                verify_target()
                return "verified"
            verify_target()
            return "restored"
        finally:
            temporary.unlink(missing_ok=True)


def main() -> None:
    global SOURCE, TARGET
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument(
        "--component-root",
        type=Path,
        default=Path("components/c140-companion"),
        help="component directory relative to the script's parent root; use . in the source ZIP",
    )
    args = parser.parse_args()
    component = ROOT / args.component_root
    SOURCE = component / "backend/assets/capstones/CP02/CP02_coverage.csv.gz"
    TARGET = component / "generated/capstones/CP02/CP02_coverage.csv"
    result = hydrate(check_only=args.check_only)
    print(json.dumps({
        "status": "pass",
        "mode": result,
        "bytes": RAW_BYTES,
        "sha256": RAW_SHA256,
        "target": TARGET.relative_to(ROOT).as_posix(),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
