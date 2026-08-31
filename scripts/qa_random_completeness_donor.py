#!/usr/bin/env python3
"""Browser-free deterministic QA for the isolated Random completeness donor."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from bs4 import BeautifulSoup, NavigableString


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "random-completeness"
BUILD = COMPONENT / "build" / "html-id"
MANIFEST = COMPONENT / "build" / "MANIFEST.csv"
BUILD_RECEIPT = COMPONENT / "build" / "BUILD_RECEIPT.json"
QA_RECEIPT = COMPONENT / "build" / "QA_RECEIPT.json"
SOURCE = COMPONENT / "authority" / "upstream" / "random" / "point" / "Sufficient.html"
TARGET = COMPONENT / "source" / "id-ID" / "random" / "point" / "Sufficient.html"
ENTITIES = COMPONENT / "backend" / "entities.jsonl"
RELATIONS = COMPONENT / "backend" / "relations.csv"
LEDGER = COMPONENT / "backend" / "translation_ledger.csv"
LANDING_WITNESS = COMPONENT / "authority" / "witness" / "random" / "index.html"
CREDITS_WITNESS = COMPONENT / "authority" / "witness" / "random" / "Credits.html"
MATHJAX_LICENSE = COMPONENT / "authority" / "runtime" / "MathJax-3.1.2" / "LICENSE.txt"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
NOTICE_ID = "o006.c140.random-completeness.component-notice"
SOURCE_BYTES = 57_507
SOURCE_SHA256 = "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4"
TARGET_BYTES = 60_900
TARGET_SHA256 = "18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197"
MATHJAX_LICENSE_BYTES = 11_358
MATHJAX_LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
PUBLISHED_PREFIX = "https://kokunoyumeto.github.io/mathematical-statistics-id/"

ENTITY_TYPES = {
    "asset": 8,
    "disclosure": 26,
    "document": 1,
    "internal_link": 116,
    "math_text": 117,
    "section": 18,
    "unit": 39,
}
RELATION_TYPES = {
    "asset-target",
    "contains",
    "details-parent",
    "internal-link-reference",
    "internal-link-target",
}
SENSITIVE_RE = re.compile(
    r"(?:[A-Za-z]:[\\/](?:Users|Documents|Downloads|AppData)[\\/])"
    r"|(?:/(?:Users|home|root|tmp)/)"
    r"|(?:github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+)"
    r"|(?:\b(?:zenodo|figshare|github)[-_ ]?(?:api[-_ ]?)?token\b\s*[:=])"
    r"|(?:\bBearer\s+[A-Za-z0-9._~+/=-]{12,})",
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.IGNORECASE)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=path.name + ".",
        suffix=".tmp",
        delete=False,
    ) as stream:
        stream.write(payload)
        temporary = Path(stream.name)
    temporary.replace(path)


def component_relative(path: Path) -> str:
    return path.relative_to(COMPONENT).as_posix()


def file_identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {
        "path": component_relative(path),
        "bytes": len(data),
        "sha256": sha256(data),
    }


def load_builder():
    path = ROOT / "scripts" / "build_random_completeness_donor.py"
    spec = importlib.util.spec_from_file_location("o006_random_donor_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load donor builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_identity(path: Path, expected_bytes: int, expected_sha: str, label: str) -> bytes:
    if not path.is_file():
        raise RuntimeError(f"missing {label}")
    data = path.read_bytes()
    if len(data) != expected_bytes or sha256(data) != expected_sha:
        raise RuntimeError(f"{label} identity differs")
    return data


def tex_opening_count(soup: BeautifulSoup) -> int:
    return sum(
        str(node).count(r"\(") + str(node).count(r"\[")
        for node in soup.find_all(string=True)
        if isinstance(node, NavigableString)
    )


def structural_gate() -> dict[str, object]:
    source_data = validate_identity(SOURCE, SOURCE_BYTES, SOURCE_SHA256, "authority source")
    target_data = validate_identity(TARGET, TARGET_BYTES, TARGET_SHA256, "canonical target")
    source = BeautifulSoup(source_data, "html.parser")
    target = BeautifulSoup(target_data, "html.parser")

    source_elements = len(source.find_all(True))
    target_elements = len(target.find_all(True))
    if source_elements != 436 or target_elements != 444:
        raise RuntimeError("source/canonical-target element census differs")
    if tex_opening_count(source) != 804 or tex_opening_count(target) != 804:
        raise RuntimeError("source/canonical-target TeX span census differs")
    if len(source.select("div.unit")) != 39 or len(target.select("div.unit")) != 39:
        raise RuntimeError("instructional unit census differs")
    if len(source.select("details")) != 26 or len(target.select("details")) != 26:
        raise RuntimeError("derivation disclosure census differs")

    target_ids = [str(node["id"]) for node in target.select("[id]")]
    if len(target_ids) != 51 or len(target_ids) != len(set(target_ids)):
        raise RuntimeError("canonical target stable-ID census/uniqueness differs")
    fragment_refs = []
    for node in target.select("[href]"):
        parsed = urlsplit(str(node["href"]))
        if parsed.fragment and not parsed.path:
            fragment_refs.append(parsed.fragment)
    if len(fragment_refs) != 44 or not set(fragment_refs).issubset(set(target_ids)):
        raise RuntimeError("canonical target fragment bindings differ")

    return {
        "source": {
            "elements": source_elements,
            "tex_spans": tex_opening_count(source),
            "units": len(source.select("div.unit")),
            "disclosures": len(source.select("details")),
        },
        "canonical_target": {
            "elements_before_additive_wrapper": target_elements,
            "tex_spans": tex_opening_count(target),
            "units": len(target.select("div.unit")),
            "disclosures": len(target.select("details")),
            "unique_dom_ids": len(target_ids),
            "local_fragment_references": len(fragment_refs),
        },
    }


def build_replay_gate() -> tuple[dict[str, object], dict[str, bytes]]:
    builder = load_builder()
    expected: dict[str, bytes] = builder.compute_outputs()
    for relative, payload in expected.items():
        path = COMPONENT / Path(PurePosixPath(relative).as_posix())
        if not path.is_file() or path.read_bytes() != payload:
            raise RuntimeError(f"deterministic donor build replay differs: {relative}")
    build_receipt = json.loads(expected["build/BUILD_RECEIPT.json"])
    if (
        build_receipt.get("status") != "built"
        or build_receipt.get("translation_provenance") != PROVENANCE
        or build_receipt.get("canonical_import_preserved") is not True
        or build_receipt.get("transformation", {}).get("relative_html_href_rewrites") != 31
    ):
        raise RuntimeError("donor build receipt contract differs")
    return (
        {
            "outputs_replayed": len(expected),
            "build_receipt": file_identity(BUILD_RECEIPT),
            "canonical_import_preserved": True,
            "relative_html_href_rewrites": 31,
        },
        expected,
    )


def manifest_gate(expected: dict[str, bytes]) -> tuple[list[dict[str, str]], set[PurePosixPath]]:
    with MANIFEST.open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    expected_paths = {
        PurePosixPath(relative.removeprefix("build/html-id/"))
        for relative in expected
        if relative.startswith("build/html-id/")
    }
    row_paths = {PurePosixPath(row["relative_path"]) for row in rows}
    actual_paths = {
        PurePosixPath(path.relative_to(BUILD).as_posix())
        for path in BUILD.rglob("*")
        if path.is_file()
    }
    if row_paths != expected_paths or actual_paths != expected_paths or len(rows) != 18:
        raise RuntimeError("reader manifest/inventory path set differs")
    for row in rows:
        path = BUILD / Path(PurePosixPath(row["relative_path"]).as_posix())
        data = path.read_bytes()
        if len(data) != int(row["bytes"]) or sha256(data) != row["sha256"]:
            raise RuntimeError(f"reader manifest identity differs: {row['relative_path']}")
    return rows, expected_paths


def normalize_local(owner: PurePosixPath, reference: str) -> tuple[PurePosixPath, str | None]:
    parsed = urlsplit(reference)
    combined = owner if not parsed.path else owner.parent / PurePosixPath(parsed.path)
    parts: list[str] = []
    for part in combined.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise RuntimeError(f"local dependency escapes reader: {owner} -> {reference}")
            parts.pop()
        else:
            parts.append(part)
    return PurePosixPath(*parts), parsed.fragment or None


def link_and_dependency_gate(expected_paths: set[PurePosixPath]) -> dict[str, object]:
    html_paths = sorted(
        (path for path in expected_paths if path.suffix.lower() in {".html", ".htm"}),
        key=lambda path: path.as_posix(),
    )
    pages = {
        path: BeautifulSoup((BUILD / Path(path.as_posix())).read_bytes(), "html.parser")
        for path in html_paths
    }
    local_edges: list[dict[str, str]] = []
    external_links: list[str] = []
    rewritten_html_links: list[str] = []

    for owner, soup in pages.items():
        for tag, attribute in (
            ("a", "href"),
            ("link", "href"),
            ("script", "src"),
            ("img", "src"),
        ):
            for node in soup.select(f"{tag}[{attribute}]"):
                reference = str(node[attribute])
                parsed = urlsplit(reference)
                if parsed.scheme or parsed.netloc:
                    if parsed.scheme != "https":
                        raise RuntimeError(f"non-HTTPS external dependency: {owner} -> {reference}")
                    external_links.append(reference)
                    if (
                        owner == PurePosixPath("random/point/Sufficient.html")
                        and reference.startswith(PUBLISHED_PREFIX)
                        and parsed.path.lower().endswith((".html", ".htm"))
                    ):
                        rewritten_html_links.append(reference)
                    continue
                resolved, fragment = normalize_local(owner, reference)
                if resolved not in expected_paths:
                    raise RuntimeError(f"missing local dependency: {owner} -> {reference}")
                if fragment and resolved.suffix.lower() in {".html", ".htm"}:
                    target_page = pages[resolved]
                    if target_page.find(id=fragment) is None:
                        raise RuntimeError(f"missing local fragment: {owner} -> {reference}")
                local_edges.append(
                    {
                        "owner": owner.as_posix(),
                        "reference": reference,
                        "resolved": resolved.as_posix(),
                    }
                )

    if len(rewritten_html_links) != 31:
        raise RuntimeError("published Random HTML routing census differs")

    css_path = PurePosixPath("random/Screen.css")
    css_text = (BUILD / Path(css_path.as_posix())).read_text("utf-8")
    css_edges: list[dict[str, str]] = []
    for match in CSS_URL_RE.finditer(css_text):
        reference = match.group(2)
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or reference.startswith("data:"):
            continue
        resolved, _ = normalize_local(css_path, reference)
        if resolved not in expected_paths:
            raise RuntimeError(f"missing CSS dependency: {css_path} -> {reference}")
        css_edges.append(
            {
                "owner": css_path.as_posix(),
                "reference": reference,
                "resolved": resolved.as_posix(),
            }
        )
    if len(css_edges) != 11 or len({edge["resolved"] for edge in css_edges}) != 9:
        raise RuntimeError("Screen.css dependency census differs")

    boldsymbol = BUILD / "MathJax" / "input" / "tex" / "extensions" / "boldsymbol.js"
    if (
        len(boldsymbol.read_bytes()) != 4_709
        or sha256(boldsymbol.read_bytes())
        != "716cf8735d00abfb1627f8adbbf4aeb915ac9b5c55d47aeaf276e73dac6a2aa1"
    ):
        raise RuntimeError("dynamic MathJax boldsymbol dependency differs")

    return {
        "html_pages": len(pages),
        "local_html_dependency_edges": len(local_edges),
        "css_dependency_edges": len(css_edges),
        "https_external_references": len(external_links),
        "rewritten_published_random_html_links": len(rewritten_html_links),
        "dynamic_mathjax_boldsymbol_closed": True,
        "all_external_references_https": True,
    }


def semantic_accessibility_gate() -> dict[str, object]:
    index = BeautifulSoup((BUILD / "index.html").read_bytes(), "html.parser")
    donor = BeautifulSoup(
        (BUILD / "random" / "point" / "Sufficient.html").read_bytes(),
        "html.parser",
    )
    rights = BeautifulSoup((BUILD / "licenses" / "index.html").read_bytes(), "html.parser")

    for name, soup in (("index", index), ("donor", donor), ("rights", rights)):
        if soup.html is None or soup.html.get("lang") != "id-ID":
            raise RuntimeError(f"reader locale missing: {name}")
        ids = [str(node["id"]) for node in soup.select("[id]")]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"duplicate DOM ID: {name}")
        if "\ufffd" in str(soup):
            raise RuntimeError(f"Unicode replacement character present: {name}")
        for image in soup.select("img"):
            if not str(image.get("alt", "")).strip():
                raise RuntimeError(f"image lacks alternative text: {name}")

    for name, soup in (("index", index), ("rights", rights)):
        if soup.select_one("main#main") is None or soup.select_one("h1") is None:
            raise RuntimeError(f"accessible primary structure missing: {name}")
        skip = soup.select_one('a.skip[href="#main"]')
        if skip is None or not skip.get_text(" ", strip=True):
            raise RuntimeError(f"skip link missing: {name}")

    notice = donor.find(id=NOTICE_ID)
    if (
        notice is None
        or notice.get("aria-label") != "Status komponen C140"
        or PROVENANCE not in notice.get_text(" ", strip=True)
    ):
        raise RuntimeError("stable C140 notice/provenance missing")
    if len(donor.find_all(True)) != 448:
        raise RuntimeError("derived donor additive-wrapper element census differs")
    donor_ids = [str(node["id"]) for node in donor.select("[id]")]
    if len(donor_ids) != 52 or len(set(donor_ids)) != 52:
        raise RuntimeError("derived donor stable-ID census differs")
    if len(donor.select("div.unit")) != 39 or len(donor.select("details")) != 26:
        raise RuntimeError("derived donor unit/disclosure census differs")
    if tex_opening_count(donor) != 804:
        raise RuntimeError("derived donor TeX span census differs")
    for details in donor.select("details"):
        summary = details.find("summary", recursive=False)
        if summary is None or not summary.get_text(" ", strip=True):
            raise RuntimeError("empty disclosure summary")
    buttons = donor.select("button")
    if len(buttons) != 4:
        raise RuntimeError("expand/contract control census differs")
    for button in buttons:
        if not button.get("title") and not button.get("aria-label"):
            raise RuntimeError("donor button lacks accessible name")

    return {
        "component_index_accessible": True,
        "rights_page_accessible": True,
        "derived_donor_elements": 448,
        "derived_donor_unique_dom_ids": 52,
        "stable_component_notice_id": NOTICE_ID,
        "images_with_alt": len(donor.select("img")),
        "accessible_disclosures": len(donor.select("details")),
        "accessible_expand_contract_buttons": len(buttons),
        "exact_model_provenance_present": True,
    }


def rights_gate() -> dict[str, object]:
    landing = LANDING_WITNESS.read_text("utf-8")
    credits = CREDITS_WITNESS.read_text("utf-8")
    target = TARGET.read_text("utf-8")
    rights = (BUILD / "licenses" / "index.html").read_text("utf-8")
    if "creativecommons.org/licenses/by/2.0/" not in landing:
        raise RuntimeError("Random landing CC BY 2.0 witness missing")
    if "creativecommons.org/licenses/by/1.0/" not in credits:
        raise RuntimeError("Random Credits CC BY 1.0 witness missing")
    for version in ("1.0", "2.0"):
        marker = f"https://creativecommons.org/licenses/by/{version}/"
        if marker not in target or marker not in rights:
            raise RuntimeError(f"derived rights discrepancy marker missing: {version}")
    validate_identity(
        MATHJAX_LICENSE,
        MATHJAX_LICENSE_BYTES,
        MATHJAX_LICENSE_SHA256,
        "MathJax licence",
    )
    built_license = BUILD / "licenses" / "MathJax-3.1.2-LICENSE.txt"
    validate_identity(
        built_license,
        MATHJAX_LICENSE_BYTES,
        MATHJAX_LICENSE_SHA256,
        "built MathJax licence",
    )
    if "Apache License" not in built_license.read_text("utf-8"):
        raise RuntimeError("MathJax Apache licence text differs")
    return {
        "Random_landing_witness": "CC BY 2.0",
        "Random_Credits_witness": "CC BY 1.0",
        "discrepancy_preserved": True,
        "MathJax_3.1.2": "Apache-2.0",
        "aggregate_uniform_relicense": False,
    }


def backend_gate() -> dict[str, object]:
    entity_rows = [
        json.loads(line)
        for line in ENTITIES.read_text("utf-8").splitlines()
        if line
    ]
    with RELATIONS.open("r", encoding="utf-8", newline="") as stream:
        relation_rows = list(csv.DictReader(stream))
    with LEDGER.open("r", encoding="utf-8", newline="") as stream:
        ledger_rows = list(csv.DictReader(stream))

    if len(entity_rows) != 325 or len(relation_rows) != 474:
        raise RuntimeError("modular backend row census differs")
    type_counts = Counter(str(row.get("entity_type")) for row in entity_rows)
    if dict(type_counts) != ENTITY_TYPES:
        raise RuntimeError("modular backend entity-type census differs")
    entity_ids = {str(row["entity_id"]) for row in entity_rows}
    if len(entity_ids) != 325:
        raise RuntimeError("modular backend entity IDs repeat")
    if sorted(int(row["source_order"]) for row in entity_rows) != list(range(1, 326)):
        raise RuntimeError("modular backend entity order differs")
    required_binding = {
        "source_path": "random/point/Sufficient.html",
        "source_sha256": SOURCE_SHA256,
        "translation_target_path": "source/id-ID/random/point/Sufficient.html",
        "translation_target_sha256": TARGET_SHA256,
        "translation_target_bytes": TARGET_BYTES,
        "translation_target_locale": "id-ID",
        "translation_status": "complete",
    }
    for row in entity_rows:
        if any(row.get(key) != value for key, value in required_binding.items()):
            raise RuntimeError(f"entity target binding differs: {row.get('entity_id')}")

    relation_ids = {row["relation_id"] for row in relation_rows}
    if len(relation_ids) != 474 or {row["relation_type"] for row in relation_rows} != RELATION_TYPES:
        raise RuntimeError("modular backend relation identity/type set differs")
    for row in relation_rows:
        if row["source_path"] != "random/point/Sufficient.html":
            raise RuntimeError("relation source binding differs")
        if row["source_entity_id"] not in entity_ids:
            raise RuntimeError(f"relation source entity missing: {row['relation_id']}")
        if (
            row["target_entity_id"]
            and row["target_entity_id"] not in entity_ids
            and not row["target_ref"]
        ):
            raise RuntimeError(f"unbound external relation target: {row['relation_id']}")

    if len(ledger_rows) != 1:
        raise RuntimeError("translation ledger row census differs")
    ledger = ledger_rows[0]
    expected_ledger = {
        "ordinal": "16",
        "source_path": "random/point/Sufficient.html",
        "target_path": "source/id-ID/random/point/Sufficient.html",
        "status": "complete",
        "source_bytes": str(SOURCE_BYTES),
        "source_sha256": SOURCE_SHA256,
        "target_bytes": str(TARGET_BYTES),
        "target_sha256": TARGET_SHA256,
    }
    if any(ledger.get(key) != value for key, value in expected_ledger.items()):
        raise RuntimeError("translation ledger target binding differs")

    return {
        "entities": len(entity_rows),
        "relations": len(relation_rows),
        "entity_types": dict(sorted(type_counts.items())),
        "source_orders_contiguous": True,
        "entity_ids_unique": True,
        "translation_target_bindings_complete": True,
        "translation_ledger_rows": len(ledger_rows),
    }


def privacy_gate(expected_paths: set[PurePosixPath]) -> dict[str, object]:
    scan_paths = [
        COMPONENT / "IMPORT_RECEIPT.json",
        COMPONENT / "authority" / "FREEZE_MANIFEST.csv",
        ENTITIES,
        RELATIONS,
        LEDGER,
        MANIFEST,
        BUILD_RECEIPT,
    ]
    scan_paths.extend(BUILD / Path(path.as_posix()) for path in expected_paths)
    scanned = 0
    for path in scan_paths:
        if path.suffix.lower() in {".js"} or path.name.endswith("LICENSE.txt"):
            # Third-party runtime/licence bytes are independently hash-bound;
            # privacy scanning their minified/legal vocabulary adds no signal.
            continue
        text = path.read_bytes().decode("utf-8", errors="strict")
        if SENSITIVE_RE.search(text):
            raise RuntimeError(f"sensitive or machine-local surface found: {component_relative(path)}")
        scanned += 1
    return {
        "text_files_scanned": scanned,
        "sensitive_values_found": 0,
        "machine_local_paths_found": 0,
        "receipt_paths_relative": True,
    }


def compute_payload() -> bytes:
    structure = structural_gate()
    replay, expected = build_replay_gate()
    manifest_rows, expected_paths = manifest_gate(expected)
    links = link_and_dependency_gate(expected_paths)
    semantics = semantic_accessibility_gate()
    rights = rights_gate()
    backend = backend_gate()
    privacy = privacy_gate(expected_paths)

    receipt = {
        "schema": "o006.c140.random-completeness.qa.v1",
        "status": "pass",
        "component": "O006/C140 Random completeness donor",
        "locale": "id-ID",
        "browser_processes_used": False,
        "structure_and_math": structure,
        "deterministic_build_replay": replay,
        "reader": {
            "files": len(manifest_rows),
            "bytes": sum(int(row["bytes"]) for row in manifest_rows),
            "manifest": file_identity(MANIFEST),
        },
        "links_and_dependency_closure": links,
        "semantics_accessibility_and_provenance": semantics,
        "rights": rights,
        "modular_backend": backend,
        "privacy": privacy,
        "gates": [
            "exact-authority-and-canonical-target-identities",
            "436-source-and-444-canonical-target-elements",
            "804-tex-spans",
            "39-units-and-26-disclosures",
            "stable-ids-and-fragments",
            "deterministic-build-replay",
            "manifest-identities-and-exact-inventory",
            "local-html-css-and-dynamic-mathjax-closure",
            "https-external-links",
            "accessible-index-rights-and-controls",
            "cc-by-2.0-and-1.0-discrepancy-preserved",
            "mathjax-apache-2.0-license",
            "325-entity-and-474-relation-backend",
            "translation-target-bindings",
            "relative-path-and-sensitive-value-scan-clear",
            "browser-free-static-qa",
        ],
    }
    return canonical_json(receipt)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    payload = compute_payload()
    if args.write:
        atomic_write(QA_RECEIPT, payload)
        state = "written"
    else:
        if not QA_RECEIPT.is_file() or QA_RECEIPT.read_bytes() != payload:
            raise RuntimeError("donor QA receipt differs")
        state = "verified"

    data = json.loads(payload)
    print(
        json.dumps(
            {
                "mode": state,
                "status": data["status"],
                "reader_files": data["reader"]["files"],
                "reader_bytes": data["reader"]["bytes"],
                "receipt_sha256": sha256(payload),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
