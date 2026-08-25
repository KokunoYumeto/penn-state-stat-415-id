#!/usr/bin/env python3
"""Anonymously verify the cumulative 7-of-14 tagged GitHub release."""

from __future__ import annotations

import argparse
import hashlib
import html as html_module
import json
import os
import re
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote

import requests
import truststore


ROOT = Path(__file__).resolve().parents[1]
OWNER = "KokunoYumeto"
REPO = "penn-state-stat-415-id"
TAG = "v2026.08.25.7of14"
PACKAGE = ROOT / "build" / "THROUGH_LESSON05_PACKAGE_RECEIPT.json"
PACKAGE_TREE_PATH = "build/THROUGH_LESSON05_PACKAGE_RECEIPT.json"
RECEIPT = ROOT / "00_control" / "GITHUB_RELEASE_RECEIPT_2026-08-25_THROUGH_LESSON05.json"
PACKAGE_SCHEMA = "o006.stat415.through-lesson05-package.v1"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
RIGHTS = {
    "aggregate_uniform_relicense": False,
    "mathjax_3_1_2": "Apache-2.0",
    "original_repository_layer": "CC BY-SA 4.0",
    "penn_state": "CC BY-NC 4.0 except where otherwise noted",
}
COMPLETE_DOCUMENTS = (
    "index",
    "Lesson00",
    "Lesson01",
    "Lesson02",
    "Lesson03",
    "Lesson04",
    "Lesson05",
)
EXACT_FILES = (
    "00_stat415-id-through-lesson05-offline-reader.zip",
    "10_stat415-id-through-lesson05-source-backend.zip",
    "20_THROUGH_LESSON05_RELEASE_NOTES.md",
    "30_THROUGH_LESSON05_LICENSE.md",
    "40_THROUGH_LESSON05_QA_RECEIPT.json",
    "41_THROUGH_LESSON05_VISUAL_QA_RECEIPT.json",
    "50_THROUGH_LESSON05_RELEASE_MANIFEST.csv",
    "SHA256SUMS_THROUGH_LESSON05.txt",
    "60_THROUGH_LESSON05_RELEASE_ROOT_RECEIPT.json",
)


class GitHubRestRateLimit(RuntimeError):
    """The anonymous REST quota is exhausted; public non-REST proof remains usable."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> bytes:
    session = requests.Session()
    session.headers.update({"User-Agent": "O006-STAT415-GitHub-release-readback/7.0"})
    for attempt in range(5):
        response = session.get(url, timeout=300, headers={"Cache-Control": "no-cache"})
        if response.status_code == 200:
            return response.content
        if (
            url.startswith("https://api.github.com/")
            and response.status_code == 403
            and (
                response.headers.get("X-RateLimit-Remaining") == "0"
                or "rate limit" in response.text.lower()
            )
        ):
            raise GitHubRestRateLimit(
                "anonymous GitHub REST quota is exhausted; using public fallback surfaces"
            )
        if response.status_code not in {429, 500, 502, 503, 504} or attempt == 4:
            raise RuntimeError(
                f"anonymous GitHub release readback failed with HTTP {response.status_code}: {url}"
            )
        time.sleep(3 * (attempt + 1))
    raise RuntimeError("unreachable retry state")


def fetch_json(url: str) -> dict[str, object]:
    try:
        value = json.loads(fetch(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"public endpoint did not return UTF-8 JSON: {url}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"public endpoint did not return a JSON object: {url}")
    return value


def release_metadata() -> dict[str, object]:
    return fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/releases/tags/{quote(TAG, safe='')}"
    )


def resolve_tag_commit(tag_ref: dict[str, object]) -> str:
    obj = tag_ref.get("object")
    if not isinstance(obj, dict):
        raise RuntimeError("GitHub tag reference omits its object")
    kind = obj.get("type")
    object_sha = str(obj.get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", object_sha):
        raise RuntimeError("GitHub tag reference omits a full object SHA")
    if kind == "commit":
        return object_sha
    if kind != "tag":
        raise RuntimeError("GitHub tag reference has an unsupported object type")
    annotated = fetch_json(
        f"https://api.github.com/repos/{OWNER}/{REPO}/git/tags/{object_sha}"
    )
    target = annotated.get("object")
    if not isinstance(target, dict) or target.get("type") != "commit":
        raise RuntimeError("annotated GitHub tag does not point directly to a commit")
    commit_sha = str(target.get("sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", commit_sha):
        raise RuntimeError("annotated GitHub tag omits its commit SHA")
    return commit_sha


def public_refs(commit_sha: str) -> dict[str, object]:
    """Prove the public branch and immutable annotated checkpoint tag."""
    remote = f"https://github.com/{OWNER}/{REPO}.git"
    wanted = (
        "refs/heads/main",
        f"refs/tags/{TAG}",
        f"refs/tags/{TAG}^{{}}",
    )
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        [
            "git",
            "-c",
            "credential.helper=",
            "-c",
            "http.extraHeader=",
            "ls-remote",
            remote,
            *wanted,
        ],
        cwd=ROOT,
        env=env,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    refs: dict[str, str] = {}
    for line in result.stdout.decode("ascii").splitlines():
        fields = line.split("\t")
        if (
            len(fields) != 2
            or not re.fullmatch(r"[0-9a-f]{40}", fields[0])
            or fields[1] in refs
        ):
            raise RuntimeError("public git ls-remote returned an invalid ref row")
        refs[fields[1]] = fields[0]
    if set(refs) != set(wanted):
        raise RuntimeError("public git ls-remote omitted the main, tag, or peeled tag ref")
    if refs[f"refs/tags/{TAG}^{{}}"] != commit_sha:
        raise RuntimeError("public peeled release tag differs from the checkpoint")
    if refs[f"refs/tags/{TAG}"] == commit_sha:
        raise RuntimeError("release tag unexpectedly lacks its distinct annotated-tag object")
    # Main may advance after this immutable content checkpoint when its
    # publication receipts are committed.  Do not bake that moving ref into a
    # deterministic checkpoint receipt.
    return {
        "main_present": True,
        "annotated_tag_object": refs[f"refs/tags/{TAG}"],
        "peeled_tag_commit": refs[f"refs/tags/{TAG}^{{}}"],
    }


def release_html_metadata(commit_sha: str) -> tuple[dict[str, object], bytes]:
    """Read exact publication metadata from the public release HTML."""
    url = f"https://github.com/{OWNER}/{REPO}/releases/tag/{quote(TAG, safe='')}"
    payload = fetch(url)
    try:
        html = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("public GitHub release page is not UTF-8") from exc
    commit_href = f'href="/{OWNER}/{REPO}/commit/{commit_sha}"'
    published = re.search(
        r'released this\s*<relative-time[^>]*\sdatetime="([^"]+)"', html
    )
    prerelease = bool(re.search(r">\s*Pre-release\s*<", html, re.IGNORECASE))
    if (
        f"/{OWNER}/{REPO}/releases/tag/{TAG}" not in html
        or f'href="/{OWNER}/{REPO}/tree/{TAG}"' not in html
        or commit_href not in html
        or published is None
    ):
        raise RuntimeError(
            "public release HTML does not bind the tag, checkpoint commit, and publication"
        )
    return (
        {
            "draft": False,
            "prerelease": prerelease,
            "tag_name": TAG,
            "target_commitish": commit_sha,
            "published_at": published.group(1),
            "html_url": url,
        },
        payload,
    )


def expanded_asset_inventory() -> tuple[dict[str, dict[str, object]], bytes, str]:
    """Parse exact public asset names and GitHub digests from expanded-assets HTML."""
    url = f"https://github.com/{OWNER}/{REPO}/releases/expanded_assets/{quote(TAG, safe='')}"
    payload = fetch(url)
    try:
        html = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError("public expanded-assets page is not UTF-8") from exc
    prefix = f'/{OWNER}/{REPO}/releases/download/{TAG}/'
    link_pattern = re.compile(r'href="' + re.escape(prefix) + r'([^"]+)"')
    assets: dict[str, dict[str, object]] = {}
    for match in link_pattern.finditer(html):
        filename = unquote(html_module.unescape(match.group(1)))
        if filename in assets:
            raise RuntimeError(f"expanded-assets inventory duplicates {filename}")
        row_end = html.find("</li>", match.end())
        if row_end < 0:
            raise RuntimeError(f"expanded-assets row is unterminated: {filename}")
        digest_match = re.search(r"sha256:([0-9a-f]{64})", html[match.end() : row_end])
        if digest_match is None:
            raise RuntimeError(f"expanded-assets row omits its SHA-256: {filename}")
        assets[filename] = {
            "name": filename,
            "state": "uploaded",
            "digest": f"sha256:{digest_match.group(1)}",
            "browser_download_url": (
                f"https://github.com/{OWNER}/{REPO}/releases/download/"
                f"{quote(TAG, safe='')}/{quote(filename, safe='')}"
            ),
        }
    if set(assets) != set(EXACT_FILES):
        raise RuntimeError("public expanded-assets inventory names differ")
    return assets, payload, url


def load_package(
    commit_sha: str,
) -> tuple[dict[str, object], dict[str, dict[str, object]], bytes]:
    local_payload = PACKAGE.read_bytes()
    public_payload = fetch(
        f"https://raw.githubusercontent.com/{OWNER}/{REPO}/{commit_sha}/{PACKAGE_TREE_PATH}"
    )
    if public_payload != local_payload:
        raise RuntimeError("local package receipt differs from the tagged public commit")
    try:
        package = json.loads(local_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("package receipt is not valid UTF-8 JSON") from exc
    rows = package.get("files") if isinstance(package, dict) else None
    coverage = package.get("coverage") if isinstance(package, dict) else None
    if (
        not isinstance(package, dict)
        or package.get("schema") != PACKAGE_SCHEMA
        or package.get("status") != "ready"
        or package.get("translation_provenance") != PROVENANCE
        or package.get("rights") != RIGHTS
        or package.get("upload_order") != list(EXACT_FILES)
        or package.get("file_count") != len(EXACT_FILES)
        or not isinstance(rows, list)
        or not isinstance(coverage, dict)
        or coverage.get("complete_documents") != list(COMPLETE_DOCUMENTS)
        or coverage.get("complete_count") != 7
        or coverage.get("corpus_document_count") != 14
        or coverage.get("next_document") != "Lesson06"
    ):
        raise RuntimeError("package receipt is not the exact ready 7-of-14 boundary")
    expected: dict[str, dict[str, object]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("package receipt contains a non-object file row")
        filename = str(row.get("filename", ""))
        if (
            filename in expected
            or filename not in EXACT_FILES
            or not isinstance(row.get("bytes"), int)
            or int(row["bytes"]) < 0
            or not re.fullmatch(r"[0-9a-f]{64}", str(row.get("sha256", "")))
        ):
            raise RuntimeError(f"package receipt has an invalid file row: {filename!r}")
        expected[filename] = row
    if set(expected) != set(EXACT_FILES):
        raise RuntimeError("package receipt file names differ")
    if package.get("total_bytes") != sum(
        int(expected[name]["bytes"]) for name in EXACT_FILES
    ):
        raise RuntimeError("package receipt aggregate bytes differ")
    return package, expected, local_payload


def compute(commit_sha: str) -> bytes:
    truststore.inject_into_ssl()
    # REST remains a strict supplementary cross-check when its anonymous quota
    # is available.  Stable public refs/release HTML form the receipt so a quota
    # reset between --write and --check-only cannot change the result.
    rest_release: dict[str, object] | None = None
    rest_assets: dict[str, dict[str, object]] | None = None
    rest_tag_commit: str | None = None
    try:
        rest_release = release_metadata()
        tag_ref = fetch_json(
            f"https://api.github.com/repos/{OWNER}/{REPO}/git/ref/tags/{quote(TAG, safe='')}"
        )
        rest_tag_commit = resolve_tag_commit(tag_ref)
        asset_rows = rest_release.get("assets")
        if not isinstance(asset_rows, list):
            raise RuntimeError("GitHub release asset inventory is absent")
        rest_assets = {
            str(row.get("name")): row for row in asset_rows if isinstance(row, dict)
        }
        if len(rest_assets) != len(asset_rows) or set(rest_assets) != set(EXACT_FILES):
            raise RuntimeError("GitHub release asset names differ")
    except GitHubRestRateLimit:
        rest_release = None
        rest_assets = None
        rest_tag_commit = None
    ref_evidence = public_refs(commit_sha)
    tag_commit = str(ref_evidence["peeled_tag_commit"])
    release, _release_page_payload = release_html_metadata(commit_sha)
    assets, _expanded_payload, expanded_url = expanded_asset_inventory()
    release_page_evidence = {
        "url": release["html_url"],
        "tag_commit_and_publication_match": True,
    }
    expanded_evidence = {
        "url": expanded_url,
        "asset_count": len(assets),
        "exact_asset_names_and_digests": True,
    }
    if (
        release.get("draft") is not False
        or release.get("prerelease") is not False
        or release.get("tag_name") != TAG
        or release.get("target_commitish") != commit_sha
        or not release.get("published_at")
    ):
        raise RuntimeError("GitHub release is not the exact published checkpoint")
    if tag_commit != commit_sha:
        raise RuntimeError("public release tag does not resolve to the checkpoint commit")

    package, expected, package_payload = load_package(commit_sha)

    if rest_release is not None:
        if (
            rest_release.get("draft") is not False
            or rest_release.get("prerelease") is not False
            or rest_release.get("tag_name") != TAG
            or rest_release.get("target_commitish") != commit_sha
            or not rest_release.get("published_at")
            or rest_tag_commit != commit_sha
            or rest_assets is None
        ):
            raise RuntimeError("supplementary REST release metadata differs")
        for filename in EXACT_FILES:
            rest_asset = rest_assets[filename]
            wanted = expected[filename]
            expected_url = (
                f"https://github.com/{OWNER}/{REPO}/releases/download/"
                f"{quote(TAG, safe='')}/{quote(filename, safe='')}"
            )
            if (
                rest_asset.get("state") != "uploaded"
                or int(rest_asset.get("size", -1)) != int(wanted["bytes"])
                or rest_asset.get("digest") != f"sha256:{wanted['sha256']}"
                or rest_asset.get("browser_download_url") != expected_url
            ):
                raise RuntimeError(
                    f"supplementary REST asset metadata differs: {filename}"
                )

    def verify(filename: str) -> dict[str, object]:
        asset = assets[filename]
        wanted = expected[filename]
        if asset.get("state") != "uploaded":
            raise RuntimeError(f"GitHub release asset metadata differs: {filename}")
        if asset.get("digest") != f"sha256:{wanted['sha256']}":
            raise RuntimeError(
                f"GitHub release asset digest metadata differs: {filename}"
            )
        expected_url = (
            f"https://github.com/{OWNER}/{REPO}/releases/download/"
            f"{quote(TAG, safe='')}/{quote(filename, safe='')}"
        )
        url = str(asset.get("browser_download_url", ""))
        if url != expected_url:
            raise RuntimeError(
                f"GitHub release asset download URL is not the predictable public URL: {filename}"
            )
        data = fetch(url)
        digest = sha256(data)
        if len(data) != wanted["bytes"] or digest != wanted["sha256"]:
            raise RuntimeError(f"GitHub release asset differs: {filename}")
        return {"name": filename, "bytes": len(data), "sha256": digest, "url": url}

    with ThreadPoolExecutor(max_workers=8) as pool:
        by_name = {row["name"]: row for row in pool.map(verify, EXACT_FILES)}
    verified = [by_name[name] for name in EXACT_FILES]
    receipt = {
        "schema": "o006.stat415.github-release-through-lesson05.v1",
        "status": "pass",
        "coverage": package["coverage"],
        "tag": TAG,
        "commit": commit_sha,
        "tag_resolves_to_commit": True,
        "public_refs": ref_evidence,
        "url": release.get("html_url"),
        "published_at": release.get("published_at"),
        "release_page_evidence": release_page_evidence,
        "expanded_assets_evidence": expanded_evidence,
        "package_receipt": {
            "path": PACKAGE_TREE_PATH,
            "bytes": len(package_payload),
            "sha256": sha256(package_payload),
            "translation_provenance": PROVENANCE,
            "rights": RIGHTS,
            "exact_tagged_commit_match": True,
        },
        "assets": verified,
        "asset_count": len(verified),
        "asset_bytes": sum(int(row["bytes"]) for row in verified),
        "verification_transport": {
            "release_and_tag_metadata": "anonymous git ls-remote and public GitHub release HTML",
            "release_assets": "public expanded-assets HTML and predictable anonymous downloads",
            "credentials_used": False,
        },
        "anonymous_readback": True,
    }
    return (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        raise RuntimeError("--commit must be a full lowercase SHA-1")
    payload = compute(args.commit)
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=RECEIPT.parent,
            prefix=RECEIPT.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(payload)
            temporary = Path(stream.name)
        temporary.replace(RECEIPT)
        mode_name = "written"
    else:
        if not RECEIPT.is_file() or RECEIPT.read_bytes() != payload:
            raise RuntimeError("GitHub release receipt differs")
        mode_name = "verified"
    value = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": mode_name,
                "status": value["status"],
                "tag": value["tag"],
                "commit": value["commit"],
                "assets": value["asset_count"],
                "bytes": value["asset_bytes"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
