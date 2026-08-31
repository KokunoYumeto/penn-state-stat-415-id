#!/usr/bin/env python3
"""Generate the C5 allowlist from this narrow repository's exact staged blobs."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess

import verify_github_content_c140_companion_c5 as verifier


ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main() -> None:
    if ROOT.name != "penn-state-stat-415-id":
        raise RuntimeError("Wrong bounded repository")
    if Path(git("rev-parse", "--show-toplevel").decode().strip()).resolve() != ROOT:
        raise RuntimeError("Git root differs from the bounded component repository")
    parts = git("diff", "--cached", "--no-renames", "--name-status", "-z").decode().split("\0")
    if parts[-1] != "" or (len(parts) - 1) % 2:
        raise RuntimeError("Malformed staged name/status inventory")
    changes = list(zip(parts[:-1:2], parts[1:-1:2]))
    if not changes or len(changes) > 1000:
        raise RuntimeError("Staged count exceeds the bounded C5 transaction")
    rows = []
    for status, path in changes:
        if status not in {"A", "M"}:
            raise RuntimeError("C5 publication does not admit staged deletions or renames")
        if path == verifier.COMMIT_MANIFEST_PATH:
            continue
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise RuntimeError("Unsafe staged relative path")
        payload = git("show", ":" + path)
        local = ROOT / path
        if local.is_symlink() or not local.is_file() or local.read_bytes() != payload:
            raise RuntimeError("Staged/local bytes differ: " + path)
        if not payload or len(payload) > verifier.MAX_PUBLIC_FILE_BYTES:
            raise RuntimeError("Staged file size is inadmissible: " + path)
        findings = verifier.privacy_findings(path, payload)
        if findings:
            raise RuntimeError("Privacy classification requires resolution: " + path + ": " + ",".join(findings))
        rows.append({"status": status, "path": path, "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()})
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=verifier.MANIFEST_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(sorted(rows, key=lambda row: str(row["path"])))
    payload = stream.getvalue().encode("utf-8")
    verifier.parse_manifest(payload)
    destination = ROOT / verifier.COMMIT_MANIFEST_PATH
    verifier.atomic_write(destination, payload)
    print(json.dumps({"status": "pass", "files": len(rows), "manifest_bytes": len(payload), "manifest_sha256": hashlib.sha256(payload).hexdigest()}))


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from None
