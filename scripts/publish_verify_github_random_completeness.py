#!/usr/bin/env python3
"""Publish and anonymously verify the cumulative Random-completeness release.

The adapter is pinned to the new annotated tag
``v2026.08.28.c140-random-completeness``.  It consumes one immutable local
25-file package snapshot, preserves the inherited 17-file reader release
verbatim, creates no lightweight tag, and has no endpoint capable of editing
or deleting the prior release.  Existing target tags/releases are accepted
only when their commit and complete public asset union are exact.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import hashlib
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import threading
import time
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests
import truststore

import consolidated_release_contract as inherited_contract


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_RECEIPT = ROOT / "build" / "RANDOM_COMPLETENESS_RELEASE_PACKAGE_RECEIPT.json"
VERIFICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_RECEIPT_2026-08-28_RANDOM_COMPLETENESS.json"
)
PUBLICATION_RECEIPT = (
    ROOT
    / "00_control"
    / "GITHUB_RELEASE_PUBLICATION_2026-08-28_RANDOM_COMPLETENESS.json"
)

OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
TAG = "v2026.08.28.c140-random-completeness"
PRIOR_TAG = "v2026.08.28.14of14-pdf-epub"
PRIOR_RELEASE_ID = 378_391_763
PRIOR_COMMIT = "7d1012119d8bd6b8942347e44ffbbca0b8bcba07"
PRIOR_TAG_OBJECT = "fc005eedbd2694bff36c7c37aec3fd4d2126520a"
API = "https://api.github.com"
REPOSITORY_API = f"{API}/repos/{OWNER}/{REPO}"
REPOSITORY_URL = f"https://github.com/{OWNER}/{REPO}"
TOKEN_FILE = Path.home() / "Downloads" / "Github Tokens.md"

PACKAGE_SCHEMA = "o006.c140.random-completeness-release-package.v1"
PACKAGE_VERSION = "2026.08.28.c140-random-completeness"
VERIFICATION_SCHEMA = "o006.c140.random-completeness.github-release-readback.v1"
PUBLICATION_SCHEMA = "o006.c140.random-completeness.github-release-publication.v1"
MODEL_PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
MAX_RELEASE_BYTES = 500_000_000
EXPECTED_PACKAGE_RECEIPT_BYTES = 24_065
EXPECTED_PACKAGE_RECEIPT_SHA256 = (
    "61da36364ec719e9af966b3a20eaa459863390b71fce7622c8b365f02818641c"
)
EXPECTED_DONOR_GATES = {
    "donor_build": (
        "components/random-completeness/build/BUILD_RECEIPT.json",
        2_147,
        "455afd0c425260517857bc61e108d08b2abf0548dcb880095b3a2d95bdc3ac2d",
    ),
    "donor_import": (
        "components/random-completeness/IMPORT_RECEIPT.json",
        5_720,
        "f8965757775c4aa0f294aac1a7fe7bd04dece9b82f755bd63d1f39abdd52c214",
    ),
    "donor_live_authority": (
        "components/random-completeness/authority/LIVE_REVERIFY_2026-08-28.json",
        3_543,
        "a793ad1cae95b6b79fcc75147f0c94a9e2c9dcca04eb5e1f3f351a4a7ab731a5",
    ),
    "donor_static_qa": (
        "components/random-completeness/build/QA_RECEIPT.json",
        3_257,
        "5868ed14ecc03094f6fea848d927738f0fe459443c5a5c49afe2a2abbe93c83f",
    ),
}
EXPECTED_PACKAGER = (
    "scripts/package_random_completeness_release.py",
    36_313,
    "b23279a19ed8dce95a55c8d4eebcb7bc5abcf85d7437756f98f0164676860347",
)

TITLE = "STAT 415 Bahasa Indonesia + donor kelengkapan C140"
BODY = (
    "Rilis kumulatif komponen O006/C140: pembaca lengkap Penn State STAT 415 "
    "(indeks dan Pelajaran 00–12) beserta donor terpisah Kyle Siegrist/Random, "
    "Sufficient, Complete, and Ancillary Statistics, dalam Bahasa Indonesia. "
    "Donor ini menutup kelengkapan, statistik anciler, Rao–Blackwell, "
    "Lehmann–Scheffé, dan Basu; pendamping orisinal C140 masih merupakan "
    "komponen lanjutan yang terpisah. Lisensi setiap komponen dipertahankan; "
    "agregat tidak direlisensi secara seragam. Provenans: "
    f"{MODEL_PROVENANCE}."
)
TAG_MESSAGE = "O006/C140 Random completeness donor checkpoint (2026-08-28)"

EXPECTED_NAMES = (
    *inherited_contract.EXPECTED_UPLOAD_ORDER,
    "01_RANDOM_COMPLETENESS_DONOR_OFFLINE_READER.zip",
    "11_RANDOM_COMPLETENESS_DONOR_SOURCE_BACKEND.zip",
    "21_RANDOM_COMPLETENESS_DONOR_RELEASE_NOTES.md",
    "31_RANDOM_COMPLETENESS_DONOR_LICENSE_AND_ATTRIBUTION.md",
    "41_RANDOM_COMPLETENESS_DONOR_STATIC_QA_EVIDENCE.zip",
    "70_C140_RANDOM_COMPLETENESS_FULL_UNION_MANIFEST.csv",
    "SHA256SUMS_C140_RANDOM_COMPLETENESS.txt",
    "80_C140_RANDOM_COMPLETENESS_FULL_UNION_ROOT_RECEIPT.json",
)
EXPECTED_ADDITION_ROLES = {
    "01_RANDOM_COMPLETENESS_DONOR_OFFLINE_READER.zip":
        "standalone-complete-random-completeness-offline-reader",
    "11_RANDOM_COMPLETENESS_DONOR_SOURCE_BACKEND.zip":
        "compact-resumable-random-completeness-source-backend",
    "21_RANDOM_COMPLETENESS_DONOR_RELEASE_NOTES.md":
        "donor-scope-status-rights-provenance",
    "31_RANDOM_COMPLETENESS_DONOR_LICENSE_AND_ATTRIBUTION.md":
        "donor-component-rights-and-attribution",
    "41_RANDOM_COMPLETENESS_DONOR_STATIC_QA_EVIDENCE.zip":
        "compact-browser-free-static-qa-evidence",
    "70_C140_RANDOM_COMPLETENESS_FULL_UNION_MANIFEST.csv":
        "cumulative-union-substantive-manifest",
    "SHA256SUMS_C140_RANDOM_COMPLETENESS.txt":
        "cumulative-union-sha256-checksums",
    "80_C140_RANDOM_COMPLETENESS_FULL_UNION_ROOT_RECEIPT.json":
        "cumulative-union-release-root-receipt",
}
EXPECTED_ADDITION_LINEAGES = {
    **{
        name: "current-random-completeness-donor"
        for name in EXPECTED_NAMES[17:22]
    },
    **{
        name: "c140-random-completeness-cumulative-union"
        for name in EXPECTED_NAMES[22:25]
    },
}
EXPECTED_FIELDS = [
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

SHA1_RE = re.compile(r"[0-9a-f]{40}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
SAFE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,254}")
SENSITIVE_NAME_RE = re.compile(
    r"(?:^|[._+-])(token|credential|secret|password|cookie|session)(?:[._+-]|$)",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(
    r"(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})"
)
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "User-Agent": "O006-C140-random-completeness-release/2026.08.28",
    "X-GitHub-Api-Version": "2022-11-28",
}
THREAD_LOCAL = threading.local()
ALLOWED_ASSET_CDN_HOSTS = {
    "release-assets.githubusercontent.com",
    "objects.githubusercontent.com",
    "github-releases.githubusercontent.com",
}


@dataclass(frozen=True)
class Artifact:
    name: str
    path: str
    bytes: int
    sha256: str
    payload: bytes
    role: str
    lineage: str
    media_type: str


@dataclass(frozen=True)
class Snapshot:
    package: dict[str, Any]
    package_receipt_bytes: int
    package_receipt_sha256: str
    files: tuple[Artifact, ...]
    inherited_files: tuple[Artifact, ...]
    additions: tuple[Artifact, ...]

    @property
    def total_bytes(self) -> int:
        return sum(item.bytes for item in self.files)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def atomic_json(path: Path, value: dict[str, object]) -> None:
    payload = canonical_json(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def canonical_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise RuntimeError(f"{label} is not a canonical repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise RuntimeError(f"{label} is not a canonical repository-relative path")
    return path.as_posix()


def read_confined(relative: str, label: str) -> bytes:
    canonical = canonical_relative(relative, label)
    path = ROOT.joinpath(*PurePosixPath(canonical).parts)
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"{label} is missing or symlinked: {canonical}")
    root = ROOT.resolve(strict=True)
    resolved = path.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} resolves outside the repository: {canonical}") from exc
    before = resolved.stat()
    payload = resolved.read_bytes()
    after = resolved.stat()
    if (
        before.st_size != len(payload)
        or after.st_size != len(payload)
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise RuntimeError(f"{label} changed while being snapshotted: {canonical}")
    return payload


def decode_object(payload: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} is not a UTF-8 JSON object") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{label} is not a JSON object")
    return value


def snapshot() -> Snapshot:
    """Freeze the exact 25-file local union before any remote operation."""

    inherited = inherited_contract.snapshot()
    receipt_relative = PACKAGE_RECEIPT.relative_to(ROOT).as_posix()
    receipt_payload = read_confined(receipt_relative, "Random completeness package receipt")
    if (
        len(receipt_payload) != EXPECTED_PACKAGE_RECEIPT_BYTES
        or sha256(receipt_payload) != EXPECTED_PACKAGE_RECEIPT_SHA256
    ):
        raise RuntimeError("Random completeness package receipt identity differs")
    package = decode_object(receipt_payload, "Random completeness package receipt")
    publication = package.get("publication_inventory")
    rows = publication.get("files") if isinstance(publication, dict) else None
    order = publication.get("upload_order") if isinstance(publication, dict) else None
    rights = package.get("rights")
    if (
        package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("version") != PACKAGE_VERSION
        or package.get("translation_provenance") != MODEL_PROVENANCE
        or not isinstance(publication, dict)
        or publication.get("fields") != EXPECTED_FIELDS
        or publication.get("reader_first") is not True
        or publication.get("file_count") != len(EXPECTED_NAMES)
        or order != list(EXPECTED_NAMES)
        or not isinstance(rows, list)
        or len(rows) != len(EXPECTED_NAMES)
        or not isinstance(rights, dict)
        or rights.get("aggregate_uniform_relicense") is not False
    ):
        raise RuntimeError("package receipt is not the admitted cumulative donor boundary")

    gates = package.get("gates")
    packager = package.get("packager")
    base_gate = gates.get("base_package") if isinstance(gates, dict) else None
    base_receipt = base_gate.get("receipt") if isinstance(base_gate, dict) else None
    if (
        not isinstance(gates, dict)
        or not isinstance(base_gate, dict)
        or base_gate.get("file_count") != len(inherited.files)
        or base_gate.get("bytes") != inherited.total_bytes
        or base_gate.get("byte_identity_and_order_verified") is not True
        or not isinstance(base_receipt, dict)
        or base_receipt.get("path")
        != inherited_contract.PACKAGE_RECEIPT.relative_to(ROOT).as_posix()
        or base_receipt.get("bytes") != inherited.package_receipt_bytes
        or base_receipt.get("sha256") != inherited.package_receipt_sha256
    ):
        raise RuntimeError("package receipt does not bind the exact inherited base contract")
    for key, (path, byte_count, digest) in EXPECTED_DONOR_GATES.items():
        binding = gates.get(key)
        payload = read_confined(path, f"required donor gate {key}")
        if (
            binding != {"path": path, "bytes": byte_count, "sha256": digest}
            or len(payload) != byte_count
            or sha256(payload) != digest
        ):
            raise RuntimeError(f"required donor gate differs: {key}")
    packager_path, packager_bytes, packager_sha = EXPECTED_PACKAGER
    packager_payload = read_confined(packager_path, "donor release packager")
    if (
        not isinstance(packager, dict)
        or packager.get("path") != packager_path
        or packager.get("bytes") != packager_bytes
        or packager.get("sha256") != packager_sha
        or packager.get("network_access") is not False
        or packager.get("browser_processes") is not False
        or packager.get("credential_access") is not False
        or packager.get("publication_side_effects") is not False
        or packager.get("recursive_repository_discovery") is not False
        or len(packager_payload) != packager_bytes
        or sha256(packager_payload) != packager_sha
    ):
        raise RuntimeError("donor release packager identity or safety contract differs")

    inherited_by_name = {item.name: item for item in inherited.files}
    inherited_rows = inherited.package["publication_inventory"]["files"]
    artifacts: list[Artifact] = []
    seen_names: set[str] = set()
    seen_paths: set[str] = set()
    total = 0
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise RuntimeError(f"package file row {index} is malformed")
        name = row.get("filename")
        relative = canonical_relative(row.get("source_path"), f"package row {index} path")
        declared_bytes = row.get("bytes")
        declared_sha = row.get("sha256")
        role = row.get("role")
        lineage = row.get("lineage")
        media_type = row.get("media_type")
        if (
            row.get("upload_order") != index + 1
            or name != EXPECTED_NAMES[index]
            or not isinstance(name, str)
            or SAFE_NAME_RE.fullmatch(name) is None
            or SENSITIVE_NAME_RE.search(name) is not None
            or relative != f"release/{name}"
            or PurePosixPath(relative).name != name
            or isinstance(declared_bytes, bool)
            or not isinstance(declared_bytes, int)
            or declared_bytes <= 0
            or not isinstance(declared_sha, str)
            or SHA256_RE.fullmatch(declared_sha) is None
            or not isinstance(role, str)
            or not role
            or not isinstance(lineage, str)
            or not lineage
            or not isinstance(media_type, str)
            or "/" not in media_type
            or row.get("primary_reader") is not (index == 0)
            or name in seen_names
            or relative in seen_paths
        ):
            raise RuntimeError(f"package file row {index} is unsafe or differs")
        payload = read_confined(relative, f"release asset {name}")
        if len(payload) != declared_bytes or sha256(payload) != declared_sha:
            raise RuntimeError(f"release asset differs from package receipt: {name}")
        if index < len(inherited.files):
            old = inherited_by_name.get(name)
            old_row = inherited_rows[index]
            if (
                old is None
                or (old.bytes, old.sha256, old.payload)
                != (declared_bytes, declared_sha, payload)
                or {
                    key: row.get(key)
                    for key in EXPECTED_FIELDS
                }
                != {
                    key: old_row.get(key)
                    for key in EXPECTED_FIELDS
                }
            ):
                raise RuntimeError(f"inherited release asset changed: {name}")
        elif (
            role != EXPECTED_ADDITION_ROLES[name]
            or lineage != EXPECTED_ADDITION_LINEAGES[name]
        ):
            raise RuntimeError(f"new release asset role differs: {name}")
        total += declared_bytes
        if total > MAX_RELEASE_BYTES:
            raise RuntimeError("release payload exceeds the 500 MB task cap")
        artifacts.append(
            Artifact(
                name=name,
                path=relative,
                bytes=declared_bytes,
                sha256=declared_sha,
                payload=payload,
                role=role,
                lineage=lineage,
                media_type=media_type,
            )
        )
        seen_names.add(name)
        seen_paths.add(relative)

    if (
        publication.get("total_bytes") != total
        or publication.get("primary_file") != EXPECTED_NAMES[0]
        or publication.get("secondary_reader") != EXPECTED_NAMES[1]
        or tuple(item.name for item in artifacts) != EXPECTED_NAMES
    ):
        raise RuntimeError("cumulative package aggregate identity differs")
    final_receipt = read_confined(receipt_relative, "Random completeness package receipt")
    if final_receipt != receipt_payload:
        raise RuntimeError("package receipt changed while being snapshotted")
    inherited_count = len(inherited.files)
    return Snapshot(
        package=package,
        package_receipt_bytes=len(receipt_payload),
        package_receipt_sha256=sha256(receipt_payload),
        files=tuple(artifacts),
        inherited_files=tuple(artifacts[:inherited_count]),
        additions=tuple(artifacts[inherited_count:]),
    )


def new_session(*, token: str | None = None) -> requests.Session:
    session = requests.Session()
    # No ambient cookies, .netrc credentials, or proxy credentials enter
    # anonymous readback; authenticated sessions also use only the explicit token.
    session.trust_env = False
    session.headers.update(HEADERS)
    if token is not None:
        session.headers["Authorization"] = f"Bearer {token}"
    return session


def public_session() -> requests.Session:
    current = getattr(THREAD_LOCAL, "session", None)
    if current is None:
        current = new_session()
        THREAD_LOCAL.session = current
    return current


def request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    expected: tuple[int, ...],
    action: str,
    **kwargs: Any,
) -> requests.Response:
    response = session.request(
        method,
        url,
        allow_redirects=False,
        **kwargs,
    )
    if response.is_redirect or response.is_permanent_redirect:
        raise RuntimeError(f"{action} returned an unexpected redirect")
    if response.status_code not in expected:
        # Never include a response body: authenticated services can echo secrets.
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    return response


def api_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    expected: tuple[int, ...] = (200,),
    action: str,
    **kwargs: Any,
) -> dict[str, Any]:
    response = request(
        session,
        method,
        url,
        expected=expected,
        action=action,
        **kwargs,
    )
    try:
        value = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{action} returned non-JSON bytes") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{action} returned a non-object")
    return value


def api_json_or_missing(
    session: requests.Session,
    url: str,
    *,
    action: str,
) -> dict[str, Any] | None:
    response = session.get(url, timeout=120, allow_redirects=False)
    if response.is_redirect or response.is_permanent_redirect:
        raise RuntimeError(f"{action} returned an unexpected redirect")
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise RuntimeError(f"{action} failed with HTTP {response.status_code}")
    try:
        value = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{action} returned non-JSON bytes") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{action} returned a non-object")
    return value


def read_token() -> str:
    candidate = os.environ.get("GITHUB_TOKEN", "").strip()
    if TOKEN_RE.fullmatch(candidate):
        return candidate
    if not TOKEN_FILE.is_file() or TOKEN_FILE.is_symlink():
        raise RuntimeError("bounded GitHub credential source is unavailable")
    matches = TOKEN_RE.findall(TOKEN_FILE.read_text("utf-8"))
    if not matches:
        raise RuntimeError("bounded GitHub credential source has no supported token")
    return max(matches, key=len)


def public_commit(commit: str) -> dict[str, object]:
    value = api_json(
        public_session(),
        "GET",
        f"{REPOSITORY_API}/commits/{commit}",
        action="read immutable public commit",
        timeout=120,
    )
    if value.get("sha") != commit:
        raise RuntimeError("public immutable commit identity differs")
    return {
        "sha": commit,
        "api_url": f"{REPOSITORY_API}/commits/{commit}",
        "html_url": f"{REPOSITORY_URL}/commit/{commit}",
    }


def annotated_tag(
    session: requests.Session,
    commit: str,
    *,
    allow_missing: bool,
) -> dict[str, object] | None:
    ref_url = f"{REPOSITORY_API}/git/ref/tags/{quote(TAG, safe='')}"
    ref = api_json_or_missing(session, ref_url, action="read target annotated-tag ref")
    if ref is None:
        if allow_missing:
            return None
        raise RuntimeError("target annotated-tag ref is absent")
    obj = ref.get("object")
    if ref.get("ref") != f"refs/tags/{TAG}" or not isinstance(obj, dict):
        raise RuntimeError("target tag ref is malformed")
    tag_sha = obj.get("sha")
    if obj.get("type") != "tag" or not isinstance(tag_sha, str) or SHA1_RE.fullmatch(tag_sha) is None:
        raise RuntimeError("target tag is not an annotated tag")
    tag = api_json(
        session,
        "GET",
        f"{REPOSITORY_API}/git/tags/{tag_sha}",
        action="peel target annotated tag",
        timeout=120,
    )
    target = tag.get("object")
    if (
        tag.get("sha") != tag_sha
        or tag.get("tag") != TAG
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != commit
    ):
        raise RuntimeError("target annotated tag does not point directly to the supplied commit")
    return {
        "ref_url": ref_url,
        "tag_object": tag_sha,
        "annotated": True,
        "peeled_commit": commit,
    }


def create_annotated_tag(session: requests.Session, commit: str) -> dict[str, object]:
    existing = annotated_tag(session, commit, allow_missing=True)
    if existing is not None:
        return existing
    tag = api_json(
        session,
        "POST",
        f"{REPOSITORY_API}/git/tags",
        expected=(201,),
        action="create annotated tag object",
        json={
            "tag": TAG,
            "message": TAG_MESSAGE,
            "object": commit,
            "type": "commit",
        },
        timeout=120,
    )
    target = tag.get("object")
    tag_sha = tag.get("sha")
    if (
        not isinstance(tag_sha, str)
        or SHA1_RE.fullmatch(tag_sha) is None
        or tag.get("tag") != TAG
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != commit
    ):
        raise RuntimeError("annotated tag creation response differs")
    response = session.post(
        f"{REPOSITORY_API}/git/refs",
        json={"ref": f"refs/tags/{TAG}", "sha": tag_sha},
        timeout=120,
        allow_redirects=False,
    )
    if response.is_redirect or response.is_permanent_redirect:
        raise RuntimeError("annotated-tag ref creation returned an unexpected redirect")
    if response.status_code not in (201, 422):
        raise RuntimeError(
            f"annotated-tag ref creation failed with HTTP {response.status_code}"
        )
    # A 422 is accepted only as a creation race whose public/authenticated ref
    # is already the exact annotated tag.  Nothing is moved or overwritten.
    verified = annotated_tag(session, commit, allow_missing=False)
    assert verified is not None
    return verified


def release_by_tag(
    session: requests.Session,
    tag: str,
    *,
    allow_missing: bool,
) -> dict[str, Any] | None:
    url = f"{REPOSITORY_API}/releases/tags/{quote(tag, safe='')}"
    value = api_json_or_missing(session, url, action=f"read release {tag}")
    if value is None:
        if allow_missing:
            return None
        raise RuntimeError(f"release is absent: {tag}")
    if value.get("tag_name") != tag:
        raise RuntimeError(f"release response is malformed: {tag}")
    return value


def authenticated_target_release(session: requests.Session) -> dict[str, Any] | None:
    """Find the target release, including a resumable authenticated draft."""

    direct = release_by_tag(session, TAG, allow_missing=True)
    if direct is not None:
        return direct
    response = request(
        session,
        "GET",
        f"{REPOSITORY_API}/releases",
        expected=(200,),
        action="list authenticated releases for target draft",
        params={"per_page": "100", "page": "1"},
        timeout=120,
    )
    try:
        values = response.json()
    except ValueError as exc:
        raise RuntimeError("authenticated release list returned non-JSON bytes") from exc
    if not isinstance(values, list) or any(not isinstance(row, dict) for row in values):
        raise RuntimeError("authenticated release list is malformed")
    matches = [row for row in values if row.get("tag_name") == TAG]
    if len(matches) > 1:
        raise RuntimeError("multiple target releases exist for the fixed tag")
    return matches[0] if matches else None


def validate_target_metadata(value: dict[str, Any], *, draft: bool) -> None:
    if (
        value.get("tag_name") != TAG
        or value.get("name") != TITLE
        or value.get("body") != BODY
        or value.get("draft") is not draft
        or value.get("prerelease") is not False
        or not isinstance(value.get("id"), int)
        or value.get("id") == PRIOR_RELEASE_ID
    ):
        raise RuntimeError("target release metadata differs; refusing mutation")


def prior_release_witness(snap: Snapshot) -> dict[str, object]:
    ref_url = f"{REPOSITORY_API}/git/ref/tags/{quote(PRIOR_TAG, safe='')}"
    ref = api_json(
        public_session(),
        "GET",
        ref_url,
        action="read prior annotated-tag ref",
        timeout=120,
    )
    obj = ref.get("object")
    if (
        ref.get("ref") != f"refs/tags/{PRIOR_TAG}"
        or not isinstance(obj, dict)
        or obj.get("type") != "tag"
        or obj.get("sha") != PRIOR_TAG_OBJECT
    ):
        raise RuntimeError("prior annotated-tag witness differs")
    prior_tag = api_json(
        public_session(),
        "GET",
        f"{REPOSITORY_API}/git/tags/{PRIOR_TAG_OBJECT}",
        action="peel prior annotated tag",
        timeout=120,
    )
    target = prior_tag.get("object")
    if (
        prior_tag.get("sha") != PRIOR_TAG_OBJECT
        or prior_tag.get("tag") != PRIOR_TAG
        or not isinstance(target, dict)
        or target.get("type") != "commit"
        or target.get("sha") != PRIOR_COMMIT
    ):
        raise RuntimeError("prior annotated tag no longer peels to its fixed commit")
    value = release_by_tag(public_session(), PRIOR_TAG, allow_missing=False)
    assert value is not None
    assets = [row for row in value.get("assets") or [] if isinstance(row, dict)]
    expected = {item.name: item for item in snap.inherited_files}
    by_name = {str(row.get("name")): row for row in assets}
    if (
        value.get("id") != PRIOR_RELEASE_ID
        or value.get("draft") is not False
        or value.get("prerelease") is not False
        or len(assets) != len(expected)
        or set(by_name) != set(expected)
    ):
        raise RuntimeError("prior release witness differs")
    inventory: list[dict[str, object]] = []
    for item in snap.inherited_files:
        row = by_name[item.name]
        if row.get("size") != item.bytes or row.get("state") != "uploaded":
            raise RuntimeError(f"prior release asset metadata differs: {item.name}")
        inventory.append(
            {"name": item.name, "bytes": item.bytes, "sha256": item.sha256}
        )
    witness = {
        "release_id": PRIOR_RELEASE_ID,
        "tag": PRIOR_TAG,
        "url": f"{REPOSITORY_URL}/releases/tag/{PRIOR_TAG}",
        "annotated_tag": {
            "ref_url": ref_url,
            "tag_object": PRIOR_TAG_OBJECT,
            "peeled_commit": PRIOR_COMMIT,
        },
        "files": inventory,
        "file_count": len(inventory),
        "total_bytes": sum(item.bytes for item in snap.inherited_files),
    }
    return {**witness, "witness_sha256": sha256(canonical_json(witness))}


def strict_public_asset(
    job: tuple[Artifact, dict[str, Any]],
) -> dict[str, object]:
    wanted, row = job
    if (
        row.get("name") != wanted.name
        or row.get("state") != "uploaded"
        or row.get("size") != wanted.bytes
        or not isinstance(row.get("id"), int)
    ):
        raise RuntimeError(f"public asset metadata differs: {wanted.name}")
    download_url = row.get("browser_download_url")
    parsed = urlparse(str(download_url))
    expected_path = f"/{OWNER}/{REPO}/releases/download/{TAG}/{quote(wanted.name, safe='')}"
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "github.com"
        or parsed.path != expected_path
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError(f"public asset URL is not admitted: {wanted.name}")

    session = public_session()
    first = session.get(str(download_url), timeout=900, allow_redirects=False)
    if first.status_code in (301, 302, 303, 307, 308):
        # GitHub release downloads normally use one signed CDN handoff.  It is
        # validated manually; automatic, cross-scheme, credential-bearing, and
        # additional redirects are all rejected.
        location = first.headers.get("Location")
        target_url = urljoin(str(download_url), str(location or ""))
        target = urlparse(target_url)
        if (
            target.scheme.casefold() != "https"
            or (target.hostname or "").casefold() not in ALLOWED_ASSET_CDN_HOSTS
            or not target.path
            or target.fragment
            or target.username
            or target.password
        ):
            raise RuntimeError(f"public asset returned an unadmitted redirect: {wanted.name}")
        second = session.get(target_url, timeout=900, allow_redirects=False)
        if second.is_redirect or second.is_permanent_redirect or second.status_code != 200:
            raise RuntimeError(f"public asset CDN handoff did not terminate: {wanted.name}")
        payload = second.content
    elif first.status_code == 200:
        payload = first.content
    else:
        raise RuntimeError(
            f"public asset readback failed with HTTP {first.status_code}: {wanted.name}"
        )
    if len(payload) != wanted.bytes or sha256(payload) != wanted.sha256:
        raise RuntimeError(f"public asset bytes differ: {wanted.name}")
    return {
        "name": wanted.name,
        "bytes": wanted.bytes,
        "sha256": wanted.sha256,
        "asset_id": row["id"],
        "download_url": download_url,
        "http_status": 200,
        "validated_download": True,
        "redirect_policy": "no automatic redirects; at most one manually validated GitHub CDN handoff",
        "automatic_redirects_followed": False,
    }


def anonymous_readback(snap: Snapshot, commit: str) -> dict[str, object]:
    commit_witness = public_commit(commit)
    tag = annotated_tag(public_session(), commit, allow_missing=False)
    assert tag is not None
    release = release_by_tag(public_session(), TAG, allow_missing=False)
    assert release is not None
    validate_target_metadata(release, draft=False)
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    expected = {item.name: item for item in snap.files}
    by_name = {str(row.get("name")): row for row in assets}
    if len(assets) != len(expected) or set(by_name) != set(expected):
        raise RuntimeError("public release has extra, missing, or duplicate assets")
    with ThreadPoolExecutor(max_workers=6) as pool:
        verified = list(
            pool.map(
                strict_public_asset,
                [(item, by_name[item.name]) for item in snap.files],
            )
        )
    verified.sort(key=lambda row: EXPECTED_NAMES.index(str(row["name"])))
    html_url = release.get("html_url")
    parsed = urlparse(str(html_url))
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "github.com"
        or parsed.path != f"/{OWNER}/{REPO}/releases/tag/{TAG}"
        or parsed.params
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("public release page URL differs")
    return {
        "release_id": release["id"],
        "url": html_url,
        "tag": TAG,
        "commit": commit_witness,
        "annotated_tag": tag,
        "files": verified,
        "file_count": len(verified),
        "total_bytes": sum(int(row["bytes"]) for row in verified),
        "reader_first": verified[0]["name"] == EXPECTED_NAMES[0],
        "anonymous_readback": True,
        "credential_access": False,
        "automatic_redirects_followed": False,
    }


def validate_existing_target_release(
    value: dict[str, Any],
    snap: Snapshot,
    commit: str,
) -> dict[str, object]:
    """Accept an existing target only after exact anonymous full-union proof."""

    validate_target_metadata(value, draft=False)
    return anonymous_readback(snap, commit)


def upload_root(value: object, release_id: int) -> str:
    if not isinstance(value, str):
        raise RuntimeError("target release omitted its upload URL")
    base = value.split("{", 1)[0]
    parsed = urlparse(base)
    if (
        parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "uploads.github.com"
        or parsed.path != f"/repos/{OWNER}/{REPO}/releases/{release_id}/assets"
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError("target release returned a non-admitted upload URL")
    return base


def create_draft_release(session: requests.Session, commit: str) -> dict[str, Any]:
    value = api_json(
        session,
        "POST",
        f"{REPOSITORY_API}/releases",
        expected=(201,),
        action="create tag-scoped target draft release",
        json={
            "tag_name": TAG,
            "target_commitish": commit,
            "name": TITLE,
            "body": BODY,
            "draft": True,
            "prerelease": False,
            "make_latest": "false",
        },
        timeout=120,
    )
    validate_target_metadata(value, draft=True)
    assets = value.get("assets")
    if assets not in (None, []):
        raise RuntimeError("new target draft unexpectedly contains assets")
    return value


def exact_asset_subset(
    release: dict[str, Any],
    snap: Snapshot,
    *,
    require_complete: bool,
) -> dict[str, dict[str, Any]]:
    assets = [row for row in release.get("assets") or [] if isinstance(row, dict)]
    by_name = {str(row.get("name")): row for row in assets}
    expected = {item.name: item for item in snap.files}
    if len(by_name) != len(assets) or set(by_name) - set(expected):
        raise RuntimeError("target draft has unexpected or duplicate assets")
    if require_complete and set(by_name) != set(expected):
        raise RuntimeError("target draft is not the complete 25-file union")
    for name, row in by_name.items():
        wanted = expected[name]
        if (
            row.get("name") != name
            or row.get("state") != "uploaded"
            or row.get("size") != wanted.bytes
            or not isinstance(row.get("id"), int)
        ):
            raise RuntimeError(f"target draft asset metadata differs: {name}")
    return by_name


def authenticated_asset_identity(
    session: requests.Session,
    wanted: Artifact,
    row: dict[str, Any],
) -> None:
    asset_id = row.get("id")
    api_url = row.get("url")
    parsed = urlparse(str(api_url))
    if (
        not isinstance(asset_id, int)
        or parsed.scheme.casefold() != "https"
        or (parsed.hostname or "").casefold() != "api.github.com"
        or parsed.path != f"/repos/{OWNER}/{REPO}/releases/assets/{asset_id}"
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError(f"target draft asset API URL differs: {wanted.name}")
    first = session.get(
        str(api_url),
        headers={"Accept": "application/octet-stream"},
        timeout=900,
        allow_redirects=False,
    )
    if first.status_code in (301, 302, 303, 307, 308):
        location = first.headers.get("Location")
        target_url = urljoin(str(api_url), str(location or ""))
        target = urlparse(target_url)
        if (
            target.scheme.casefold() != "https"
            or (target.hostname or "").casefold() not in ALLOWED_ASSET_CDN_HOSTS
            or not target.path
            or target.fragment
            or target.username
            or target.password
        ):
            raise RuntimeError(
                f"target draft asset returned an unadmitted CDN handoff: {wanted.name}"
            )
        # Do not forward the GitHub bearer token to the signed CDN URL.
        anonymous = new_session()
        second = anonymous.get(target_url, timeout=900, allow_redirects=False)
        if second.is_redirect or second.is_permanent_redirect or second.status_code != 200:
            raise RuntimeError(f"target draft asset CDN handoff did not terminate: {wanted.name}")
        payload = second.content
    elif first.status_code == 200:
        payload = first.content
    else:
        raise RuntimeError(
            f"target draft asset readback failed with HTTP {first.status_code}: {wanted.name}"
        )
    if len(payload) != wanted.bytes or sha256(payload) != wanted.sha256:
        raise RuntimeError(f"target draft asset bytes differ: {wanted.name}")


def upload_or_resume_draft(
    session: requests.Session,
    release: dict[str, Any],
    snap: Snapshot,
) -> tuple[dict[str, Any], list[str], list[str]]:
    validate_target_metadata(release, draft=True)
    release_id = int(release["id"])
    existing = exact_asset_subset(release, snap, require_complete=False)
    expected = {item.name: item for item in snap.files}
    for item in snap.files:
        if item.name in existing:
            authenticated_asset_identity(session, item, existing[item.name])
    root = upload_root(release.get("upload_url"), release_id)
    uploaded: list[str] = []
    for item in snap.files:
        if item.name in existing:
            continue
        content_type = item.media_type or mimetypes.guess_type(item.name)[0]
        response = request(
            session,
            "POST",
            root,
            expected=(201,),
            action=f"upload target release asset {item.name}",
            params={"name": item.name},
            data=item.payload,
            headers={
                "Content-Type": content_type or "application/octet-stream",
                "Content-Length": str(item.bytes),
            },
            timeout=900,
        )
        try:
            value = response.json()
        except ValueError as exc:
            raise RuntimeError(f"asset upload returned non-JSON bytes: {item.name}") from exc
        if (
            not isinstance(value, dict)
            or value.get("name") != item.name
            or value.get("size") != item.bytes
            or value.get("state") != "uploaded"
        ):
            raise RuntimeError(f"asset upload response differs: {item.name}")
        uploaded.append(item.name)
    refreshed = authenticated_target_release(session)
    if refreshed is None or refreshed.get("id") != release_id:
        raise RuntimeError("target draft disappeared or changed identity after upload")
    validate_target_metadata(refreshed, draft=True)
    complete = exact_asset_subset(refreshed, snap, require_complete=True)
    for item in snap.files:
        authenticated_asset_identity(session, item, complete[item.name])
    return refreshed, sorted(existing, key=EXPECTED_NAMES.index), uploaded


def publish_complete_draft(
    session: requests.Session,
    release: dict[str, Any],
    snap: Snapshot,
) -> dict[str, Any]:
    validate_target_metadata(release, draft=True)
    release_id = int(release["id"])
    exact_asset_subset(release, snap, require_complete=True)
    value = api_json(
        session,
        "PATCH",
        f"{REPOSITORY_API}/releases/{release_id}",
        expected=(200,),
        action="publish exact complete target draft",
        json={"draft": False, "make_latest": "true"},
        timeout=120,
    )
    if value.get("id") != release_id:
        raise RuntimeError("published target release identity differs")
    validate_target_metadata(value, draft=False)
    exact_asset_subset(value, snap, require_complete=True)
    return value


def receipt_base(snap: Snapshot, commit: str) -> dict[str, object]:
    return {
        "version": PACKAGE_VERSION,
        "repository": REPOSITORY_URL,
        "tag": TAG,
        "commit": commit,
        "local_inventory": [
            {
                "name": item.name,
                "bytes": item.bytes,
                "sha256": item.sha256,
                "role": item.role,
                "lineage": item.lineage,
            }
            for item in snap.files
        ],
        "local_files": len(snap.files),
        "local_bytes": snap.total_bytes,
        "inherited_files_preserved": len(snap.inherited_files),
        "donor_and_cumulative_additions": len(snap.additions),
        "package_receipt": {
            "path": PACKAGE_RECEIPT.relative_to(ROOT).as_posix(),
            "bytes": snap.package_receipt_bytes,
            "sha256": snap.package_receipt_sha256,
        },
        "translation_provenance": MODEL_PROVENANCE,
        "browser_processes_used": False,
        "machine_local_paths_recorded": False,
    }


def verification_payload(
    snap: Snapshot,
    commit: str,
    public: dict[str, object],
    prior: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": VERIFICATION_SCHEMA,
        "status": "pass",
        **receipt_base(snap, commit),
        "mode": "anonymous-verification",
        "credential_access": False,
        "remote_writes": False,
        "prior_release_untouched": True,
        "prior_release_witness": prior,
        "public": public,
    }


def contract_summary(snap: Snapshot) -> dict[str, object]:
    return {
        "mode": "contract-check",
        "status": "pass",
        "schema": PACKAGE_SCHEMA,
        "version": PACKAGE_VERSION,
        "tag": TAG,
        "annotated_tag_required": True,
        "files": len(snap.files),
        "bytes": snap.total_bytes,
        "inherited_files": len(snap.inherited_files),
        "additions": len(snap.additions),
        "primary_file": snap.files[0].name,
        "package_receipt_sha256": snap.package_receipt_sha256,
        "credential_access": False,
        "network_access": False,
        "browser_processes_used": False,
    }


def require_commit(parser: argparse.ArgumentParser, value: str | None) -> str:
    if not isinstance(value, str) or SHA1_RE.fullmatch(value) is None:
        parser.error("--commit must be an explicit full lowercase 40-hex commit")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--contract-check", action="store_true")
    modes.add_argument("--publish", action="store_true")
    modes.add_argument("--write-receipt", action="store_true")
    modes.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit")
    args = parser.parse_args()

    snap = snapshot()
    if args.contract_check:
        if args.commit is not None:
            parser.error("--contract-check does not accept --commit")
        print(json.dumps(contract_summary(snap), ensure_ascii=False, sort_keys=True))
        return
    commit = require_commit(parser, args.commit)
    truststore.inject_into_ssl()

    if args.write_receipt or args.check_only:
        public = anonymous_readback(snap, commit)
        prior = prior_release_witness(snap)
        payload = verification_payload(snap, commit, public, prior)
        encoded = canonical_json(payload)
        if args.write_receipt:
            atomic_json(VERIFICATION_RECEIPT, payload)
            state = "written"
        else:
            if (
                VERIFICATION_RECEIPT.is_symlink()
                or not VERIFICATION_RECEIPT.is_file()
                or VERIFICATION_RECEIPT.read_bytes() != encoded
            ):
                raise RuntimeError("anonymous GitHub verification receipt differs")
            state = "verified"
        print(
            json.dumps(
                {
                    "mode": state,
                    "status": "pass",
                    "tag": TAG,
                    "commit": commit,
                    "files": len(snap.files),
                    "bytes": snap.total_bytes,
                    "receipt_sha256": sha256(encoded),
                },
                sort_keys=True,
            )
        )
        return

    # Local closure and immutable public commit checks precede credential access.
    public_commit(commit)
    existing_tag = annotated_tag(public_session(), commit, allow_missing=True)
    existing_release = release_by_tag(public_session(), TAG, allow_missing=True)
    prior_before = prior_release_witness(snap)
    if existing_release is not None:
        if existing_tag is None:
            raise RuntimeError("existing target release has no exact annotated tag")
        public = validate_existing_target_release(existing_release, snap, commit)
        prior_after = prior_release_witness(snap)
        if prior_after != prior_before:
            raise RuntimeError("prior release witness changed during verification")
        publication = {
            "schema": PUBLICATION_SCHEMA,
            "status": "pass",
            **receipt_base(snap, commit),
            "mode": "publish-existing-exact",
            "credential_access": False,
            "created_annotated_tag": False,
            "created_target_release": False,
            "uploaded_assets": [],
            "prior_release_untouched": True,
            "prior_release_witness": prior_after,
            "public": public,
        }
        verification = verification_payload(snap, commit, public, prior_after)
        atomic_json(PUBLICATION_RECEIPT, publication)
        atomic_json(VERIFICATION_RECEIPT, verification)
        print(
            json.dumps(
                {
                    "mode": "publish-existing-exact",
                    "status": "pass",
                    "tag": TAG,
                    "commit": commit,
                    "release_id": public["release_id"],
                    "files": len(snap.files),
                    "uploaded": 0,
                },
                sort_keys=True,
            )
        )
        return

    token = read_token()
    authenticated = new_session(token=token)
    created_tag = existing_tag is None
    tag = create_annotated_tag(authenticated, commit)
    release = authenticated_target_release(authenticated)
    if release is None:
        release = create_draft_release(authenticated, commit)
        created_release = True
    else:
        created_release = False
    if release.get("draft") is False:
        # A concurrently published target is acceptable only as the exact
        # anonymous full union.  It is never edited.
        public = validate_existing_target_release(release, snap, commit)
        resumed: list[str] = []
        uploaded: list[str] = []
    else:
        release, resumed, uploaded = upload_or_resume_draft(
            authenticated,
            release,
            snap,
        )
        publish_complete_draft(authenticated, release, snap)
        public = anonymous_readback(snap, commit)
    if tag.get("peeled_commit") != commit:
        raise RuntimeError("post-publication annotated-tag identity differs")
    prior_after = prior_release_witness(snap)
    if prior_after != prior_before:
        raise RuntimeError("prior release witness changed during target publication")
    publication = {
        "schema": PUBLICATION_SCHEMA,
        "status": "pass",
        **receipt_base(snap, commit),
        "mode": "publish",
        "credential_access": True,
        "created_annotated_tag": created_tag,
        "created_target_release": created_release,
        "transactional_draft": True,
        "resumed_existing_assets": resumed,
        "uploaded_assets": uploaded,
        "existing_assets_preserved": len(snap.files) - len(uploaded),
        "prior_release_untouched": True,
        "prior_release_witness": prior_after,
        "public": public,
    }
    verification = verification_payload(snap, commit, public, prior_after)
    atomic_json(PUBLICATION_RECEIPT, publication)
    atomic_json(VERIFICATION_RECEIPT, verification)
    print(
        json.dumps(
            {
                "mode": "publish",
                "status": "pass",
                "tag": TAG,
                "commit": commit,
                "release_id": public["release_id"],
                "files": len(snap.files),
                "uploaded": len(uploaded),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
