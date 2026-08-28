#!/usr/bin/env python3
"""Build the original C140 companion with deterministic, browser-free tooling."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from markdown_it import MarkdownIt


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent.parent
SOURCE = ROOT / "source" / "id-ID"
GENERATED_BATCHES = {
    "c1": ROOT / "generated" / "simulations" / "c1",
    "c2": ROOT / "generated" / "simulations" / "c2",
}
SIMULATION_RECEIPTS = {
    "c1": ROOT / "build" / "C1_SIMULATION_RECEIPT.json",
    "c2": ROOT / "build" / "C2_SIMULATION_RECEIPT.json",
}
HTML_TARGET = ROOT / "build" / "html-id"
BACKEND_TARGET = ROOT / "backend"
RECEIPT_TARGET = ROOT / "build" / "C2_BUILD_RECEIPT.json"
MATHJAX_SOURCE = REPO / "build" / "html-id" / "assets" / "MathJax"
MATHJAX_LICENSE = REPO / "build" / "html-id" / "licenses" / "MathJax-3.1.2-LICENSE.txt"

REQUIRED_METADATA = {
    "id",
    "type",
    "title",
    "locale",
    "license",
    "provenance",
    "prerequisites",
    "objectives",
    "relations",
    "status",
}
REQUIRED_C1 = {
    "O006-C140-CMP-INDEX",
    *(f"O006-C140-CMP-D{i:03d}" for i in range(1, 8)),
    *(f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 5)),
    *(f"O006-C140-CMP-MS{i:02d}" for i in range(7, 11)),
    "O006-C140-CMP-CA01",
}
REQUIRED_CUMULATIVE_C2 = REQUIRED_C1 | {
    *(f"O006-C140-CMP-D{i:03d}" for i in range(8, 12)),
    "O006-C140-CMP-SIM005",
    "O006-C140-CMP-MS12",
}
ANCHOR_RE = re.compile(r'<a\s+id="([A-Za-z0-9._:-]+)"\s*></a>')
REF_RE = re.compile(r"\[ref:([A-Za-z0-9._:-]+)\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
DISPLAY_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)
INLINE_RE = re.compile(r"\\\((.+?)\\\)")
DOLLAR_DISPLAY_RE = re.compile(r"\$\$(.+?)\$\$", re.DOTALL)
DOLLAR_INLINE_RE = re.compile(r"(?<!\\)\$(?!\$)(.+?)(?<!\\)\$(?!\$)")


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def csv_payload(fieldnames: list[str], rows: list[dict[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


@dataclass(frozen=True)
class Document:
    path: Path
    source_rel: str
    output_rel: str
    raw: bytes
    body: str
    metadata: dict[str, Any]
    anchors: tuple[str, ...]
    headings: dict[str, str]
    references: tuple[str, ...]


def normalized_relations(document: Document) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for relation in document.metadata["relations"]:
        if isinstance(relation, str) and ":" in relation:
            predicate, target = relation.split(":", 1)
        elif isinstance(relation, dict):
            predicate, target = relation.get("predicate"), relation.get("target")
        else:
            raise RuntimeError(f"Invalid relation in {document.source_rel}: {relation!r}")
        if not isinstance(predicate, str) or not predicate or not isinstance(target, str) or not target:
            raise RuntimeError(f"Incomplete relation in {document.source_rel}: {relation!r}")
        rows.append({"predicate": predicate, "target": target})
    return rows


def parse_document(path: Path) -> Document:
    raw = path.read_bytes()
    if b"\r" in raw:
        raise RuntimeError(f"Non-LF newline in {rel(path)}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"Non-UTF-8 source {rel(path)}") from exc
    lines = text.splitlines()
    if len(lines) < 4 or lines[0] != "---" or lines[2] != "---":
        raise RuntimeError(f"Front matter must be exactly three lines in {rel(path)}")
    try:
        metadata = json.loads(lines[1])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid one-line JSON in {rel(path)}: {exc}") from exc
    missing = REQUIRED_METADATA - set(metadata)
    if missing:
        raise RuntimeError(f"Missing metadata {sorted(missing)} in {rel(path)}")
    if metadata["locale"] != "id-ID" or metadata["license"] != "CC-BY-SA-4.0":
        raise RuntimeError(f"Locale/license mismatch in {rel(path)}")
    if metadata["provenance"] != "OpenAI Codex gpt-5.6-sol, Ultra":
        raise RuntimeError(f"Provenance mismatch in {rel(path)}")
    if not isinstance(metadata["relations"], list):
        raise RuntimeError(f"relations is not a list in {rel(path)}")
    body = "\n".join(lines[3:]) + "\n"
    anchors = tuple(ANCHOR_RE.findall(body))
    if len(anchors) != len(set(anchors)):
        raise RuntimeError(f"Duplicate anchor inside {rel(path)}")
    body_lines = body.splitlines()
    headings: dict[str, str] = {}
    for index, line in enumerate(body_lines):
        match = ANCHOR_RE.fullmatch(line.strip())
        if not match:
            continue
        cursor = index + 1
        while cursor < len(body_lines) and not body_lines[cursor].strip():
            cursor += 1
        if cursor < len(body_lines):
            heading = re.match(r"^#{1,6}\s+(.+?)\s*$", body_lines[cursor])
            if heading:
                headings[match.group(1)] = heading.group(1).replace("*", "")
    source_rel = path.relative_to(SOURCE).as_posix()
    return Document(
        path=path,
        source_rel=source_rel,
        output_rel=PurePosixPath(source_rel).with_suffix(".html").as_posix(),
        raw=raw,
        body=body,
        metadata=metadata,
        anchors=anchors,
        headings=headings,
        references=tuple(REF_RE.findall(body)),
    )


def load_documents() -> list[Document]:
    documents = [parse_document(path) for path in SOURCE.rglob("*.md")]
    order = {"index": 0, "theory": 1, "simulation": 2, "mastery": 3, "assessment": 4, "capstone": 5}
    documents.sort(key=lambda item: (order.get(str(item.metadata["type"]), 99), str(item.metadata["id"])))
    ids = [str(item.metadata["id"]) for item in documents]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Duplicate document ID")
    missing = sorted(REQUIRED_CUMULATIVE_C2 - set(ids))
    if missing:
        raise RuntimeError(f"Cumulative C2 source boundary incomplete; missing {missing}")
    unexpected = sorted(set(ids) - REQUIRED_CUMULATIVE_C2)
    if unexpected:
        raise RuntimeError(f"Cumulative C2 source boundary has unexpected documents {unexpected}")
    all_anchors = [anchor for item in documents for anchor in item.anchors]
    duplicates = sorted({anchor for anchor in all_anchors if all_anchors.count(anchor) > 1})
    if duplicates:
        raise RuntimeError(f"Cross-document duplicate anchors: {duplicates}")
    return documents


def load_external_targets() -> tuple[dict[str, str], dict[str, str]]:
    urls: dict[str, str] = {}
    titles: dict[str, str] = {}
    penn = REPO / "backend" / "through_lesson12_documents.jsonl"
    for line in penn.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        document_id = row["document_id"]
        component = row["component_id"]
        suffix = "" if component == "index" else f"{component}.html"
        urls[document_id] = f"https://kokunoyumeto.github.io/penn-state-stat-415-id/{suffix}"
        titles[document_id] = "Penn State STAT 415" if component == "index" else component
    donor = REPO / "components" / "random-completeness" / "backend" / "entities.jsonl"
    donor_base = "https://kokunoyumeto.github.io/penn-state-stat-415-id/components/random-completeness/"
    for line in donor.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        entity_id = row["entity_id"]
        urls[entity_id] = donor_base if row.get("entity_type") == "document" else donor_base + "#" + entity_id
        label = row.get("target_text") or row.get("source_text") or entity_id
        titles[entity_id] = str(label).replace("\n", " ")[:120]
    return urls, titles


def relative_href(current: str, target: str, anchor: str | None = None) -> str:
    start = PurePosixPath(current).parent.as_posix()
    if start == ".":
        start = ""
    value = posixpath.relpath(target, start=start or ".")
    return value + (f"#{anchor}" if anchor else "")


def render_markdown(
    document: Document,
    local_paths: dict[str, tuple[str, str | None]],
    titles: dict[str, str],
    external_urls: dict[str, str],
) -> str:
    tokens: dict[str, str] = {}
    counter = 0

    def token(markup: str, kind: str) -> str:
        nonlocal counter
        counter += 1
        key = f"@@O006{kind}{counter:06d}@@"
        tokens[key] = markup
        return key

    def display(match: re.Match[str]) -> str:
        math_text = html.escape(match.group(1).strip(), quote=False)
        return "\n\n" + token(f'<div class="math-display" role="math">\\[{math_text}\\]</div>', "MATHD") + "\n\n"

    def inline(match: re.Match[str]) -> str:
        math_text = html.escape(match.group(1), quote=False)
        return token(f'<span class="math-inline" role="math">\\({math_text}\\)</span>', "MATHI")

    working = DOLLAR_DISPLAY_RE.sub(display, document.body)
    working = DISPLAY_RE.sub(display, working)
    working = INLINE_RE.sub(inline, working)
    working = DOLLAR_INLINE_RE.sub(inline, working)

    def reference(match: re.Match[str]) -> str:
        target_id = match.group(1)
        label = html.escape(titles.get(target_id, target_id))
        if target_id in local_paths:
            target_page, anchor = local_paths[target_id]
            href = relative_href(document.output_rel, target_page, anchor)
            markup = f'<a class="xref" data-target-id="{target_id}" href="{html.escape(href, quote=True)}">{label}</a>'
        elif target_id in external_urls:
            markup = f'<a class="xref external" data-target-id="{target_id}" href="{html.escape(external_urls[target_id], quote=True)}">{label}</a>'
        else:
            raise RuntimeError(f"Unresolved reference {target_id} in {document.source_rel}")
        return token(markup, "REF")

    working = REF_RE.sub(reference, working)
    renderer = MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    rendered = renderer.render(working)
    for key, markup in tokens.items():
        rendered = rendered.replace(f"<p>{key}</p>", markup)
        rendered = rendered.replace(key, markup)

    asset_prefix = relative_href(document.output_rel, "assets/placeholder").rsplit("/", 1)[0]
    rendered = rendered.replace('src="assets/', f'src="{asset_prefix}/')
    rendered = rendered.replace('href="assets/', f'href="{asset_prefix}/')
    return rendered


STYLE = """\
:root{color-scheme:light;--ink:#17202a;--muted:#566573;--rule:#d5d8dc;--accent:#154360;--paper:#fff;--wash:#f4f6f7}
*{box-sizing:border-box}html{font-size:18px;scroll-behavior:smooth}body{margin:0;background:var(--wash);color:var(--ink);font-family:Georgia,'Times New Roman',serif;line-height:1.62}
.shell{display:grid;grid-template-columns:minmax(15rem,21rem) minmax(0,52rem);gap:2rem;max-width:78rem;margin:0 auto;padding:1.25rem}.sidebar{align-self:start;position:sticky;top:1rem;max-height:calc(100vh - 2rem);overflow:auto;background:var(--paper);border:1px solid var(--rule);border-radius:.5rem;padding:1rem}.sidebar h2{font:700 1rem Arial,sans-serif;margin:.2rem 0 .8rem}.sidebar ol{padding-left:1.4rem;margin:0}.sidebar li{margin:.35rem 0}.sidebar a{color:var(--accent)}main{min-width:0;background:var(--paper);border:1px solid var(--rule);border-radius:.5rem;padding:clamp(1.25rem,4vw,3.5rem)}h1,h2,h3,h4{font-family:Arial,sans-serif;line-height:1.2;color:#102a43;margin-top:2em}h1{font-size:2.05rem;margin-top:0}h2{font-size:1.45rem}h3{font-size:1.18rem}a{color:#0b5e8e;text-underline-offset:.15em}.metadata{font-family:Arial,sans-serif;font-size:.88rem;color:var(--muted);border-bottom:1px solid var(--rule);padding-bottom:1rem;margin-bottom:2rem}.math-display{max-width:100%;overflow-x:auto;padding:.6rem .25rem;margin:1rem 0}.math-inline{white-space:nowrap}figure{margin:2rem 0}figure img{display:block;width:100%;height:auto;margin:0 auto;border:1px solid var(--rule);background:#fff}figcaption{font:italic .9rem Arial,sans-serif;color:var(--muted);margin-top:.5rem}pre,code{font-family:'Cascadia Mono',Consolas,monospace}pre{overflow:auto;background:#f7f9fa;padding:1rem;border-radius:.3rem}blockquote{border-left:.25rem solid #7fb3d5;margin-left:0;padding-left:1rem;color:#34495e}.xref{font-weight:600}.license{margin-top:3rem;padding-top:1rem;border-top:1px solid var(--rule);font:0.85rem Arial,sans-serif;color:var(--muted)}
@media(max-width:780px){html{font-size:16px}.shell{display:block;padding:.5rem}.sidebar{position:static;max-height:none;margin-bottom:.75rem}main{padding:1.1rem;border-radius:.25rem}h1{font-size:1.7rem}.math-display{margin-left:-.25rem;margin-right:-.25rem}}
@media print{body{background:#fff}.shell{display:block;max-width:none;padding:0}.sidebar{display:none}main{border:0;padding:0}.xref{color:inherit}}
"""


def page_template(document: Document, body_html: str, documents: list[Document]) -> bytes:
    css_href = relative_href(document.output_rel, "assets/style.css")
    mathjax_href = relative_href(document.output_rel, "assets/MathJax/tex-svg.js")
    nav_items = []
    for item in documents:
        href = relative_href(document.output_rel, item.output_rel)
        nav_items.append(f'<li><a href="{html.escape(href, quote=True)}">{html.escape(str(item.metadata["title"]))}</a></li>')
    metadata = document.metadata
    page = f"""<!doctype html>
<html lang="id-ID">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="generator" content="OpenAI Codex gpt-5.6-sol, Ultra">
<title>{html.escape(str(metadata['title']))}</title>
<link rel="stylesheet" href="{html.escape(css_href, quote=True)}">
<script>window.MathJax={{loader:{{load:['[tex]/boldsymbol']}},tex:{{packages:{{'[+]':['boldsymbol']}},inlineMath:[['\\\\(','\\\\)']],displayMath:[['\\\\[','\\\\]']]}},svg:{{fontCache:'local'}}}};</script>
<script defer src="{html.escape(mathjax_href, quote=True)}"></script>
</head>
<body>
<div class="shell">
<nav class="sidebar" aria-label="Daftar isi pendamping"><h2>Isi pendamping</h2><ol>{''.join(nav_items)}</ol></nav>
<main>
<div class="metadata"><strong>{html.escape(str(metadata['id']))}</strong> · id-ID · CC BY-SA 4.0 · {html.escape(str(metadata['provenance']))}</div>
{body_html}
<footer class="license">Materi pendamping orisinal berlisensi CC BY-SA 4.0. Komponen Penn State dan Random tetap berada di bawah lisensinya masing-masing dan tidak direlisensikan oleh halaman ini.</footer>
</main>
</div>
</body>
</html>
"""
    return page.encode("utf-8")


def generated_asset_id(batch: str, path: Path) -> str:
    name = path.name
    if name == "MANIFEST.csv":
        return f"O006-C140-CMP-{batch.upper()}-SIM-MANIFEST"
    stem = path.stem.upper()
    prefix = stem.split("_", 1)[0]
    suffix = stem.split("_", 1)[1] if "_" in stem else "OUTPUT"
    suffix = re.sub(r"[^A-Z0-9]+", "-", suffix)
    return f"O006-C140-CMP-{prefix}-ASSET-{suffix}-{path.suffix[1:].upper()}"


def generated_output_rel(batch: str, path: Path) -> str:
    if path.name == "MANIFEST.csv":
        return f"assets/simulations/manifests/{batch}.csv"
    return f"assets/simulations/{path.name}"


def iter_generated_assets() -> list[tuple[str, Path, str]]:
    rows: list[tuple[str, Path, str]] = []
    output_paths: set[str] = set()
    for batch, directory in GENERATED_BATCHES.items():
        if not directory.is_dir():
            raise RuntimeError(f"{batch.upper()} simulation outputs are missing")
        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue
            output_rel = generated_output_rel(batch, path)
            if output_rel in output_paths:
                raise RuntimeError(f"Simulation output collision: {output_rel}")
            output_paths.add(output_rel)
            rows.append((batch, path, output_rel))
    return rows


def collect_static_payloads() -> dict[str, bytes]:
    if not MATHJAX_SOURCE.is_dir() or not MATHJAX_LICENSE.is_file():
        raise RuntimeError("Frozen local MathJax closure is missing")
    payloads: dict[str, bytes] = {"assets/style.css": STYLE.encode("utf-8")}
    for path in sorted(MATHJAX_SOURCE.rglob("*")):
        if path.is_file():
            suffix = path.relative_to(MATHJAX_SOURCE).as_posix()
            payloads[f"assets/MathJax/{suffix}"] = path.read_bytes()
    payloads["licenses/MathJax-3.1.2-LICENSE.txt"] = MATHJAX_LICENSE.read_bytes()
    for _batch, path, output_rel in iter_generated_assets():
        payloads[output_rel] = path.read_bytes()
    for batch, path in SIMULATION_RECEIPTS.items():
        if not path.is_file():
            raise RuntimeError(f"{batch.upper()} simulation receipt is missing")
        payloads[f"assets/simulations/receipts/{path.name}"] = path.read_bytes()
    return payloads


def build_payloads(documents: list[Document]) -> tuple[dict[str, bytes], dict[str, bytes], bytes]:
    external_urls, external_titles = load_external_targets()
    local_paths: dict[str, tuple[str, str | None]] = {}
    titles = dict(external_titles)
    for document in documents:
        document_id = str(document.metadata["id"])
        local_paths[document_id] = (document.output_rel, None)
        titles[document_id] = str(document.metadata["title"])
        for anchor in document.anchors:
            local_paths[anchor] = (document.output_rel, anchor)
            titles[anchor] = document.headings.get(anchor, anchor)

    for document in documents:
        for relation in normalized_relations(document):
            target = relation.get("target")
            if target not in local_paths and target not in external_urls:
                raise RuntimeError(f"Unresolved metadata relation {target} in {document.source_rel}")

    html_payloads = collect_static_payloads()
    for document in documents:
        body_html = render_markdown(document, local_paths, titles, external_urls)
        html_payloads[document.output_rel] = page_template(document, body_html, documents)

    manifest_rows = [
        {"path": path, "bytes": len(payload), "sha256": sha256(payload)}
        for path, payload in sorted(html_payloads.items())
    ]
    html_payloads["MANIFEST.csv"] = csv_payload(["path", "bytes", "sha256"], manifest_rows)

    entities: list[dict[str, object]] = []
    relations: set[tuple[str, str, str, str]] = set()
    documents_backend: list[dict[str, object]] = []
    for order, document in enumerate(documents, start=1):
        document_id = str(document.metadata["id"])
        entities.append({
            "entity_id": document_id,
            "entity_type": "document",
            "license": document.metadata["license"],
            "locale": document.metadata["locale"],
            "order": order,
            "output_path": document.output_rel,
            "provenance": document.metadata["provenance"],
            "source_path": f"source/id-ID/{document.source_rel}",
            "source_sha256": sha256(document.raw),
            "title": document.metadata["title"],
        })
        documents_backend.append({
            "anchors": len(document.anchors),
            "bytes": len(document.raw),
            "document_id": document_id,
            "output_path": document.output_rel,
            "references": len(document.references),
            "sha256": sha256(document.raw),
            "source_path": f"source/id-ID/{document.source_rel}",
            "status": document.metadata["status"],
            "title": document.metadata["title"],
            "type": document.metadata["type"],
        })
        for anchor_index, anchor in enumerate(document.anchors, start=1):
            suffix = re.search(r"-([A-Z]+)\d+$", anchor)
            entities.append({
                "document_id": document_id,
                "entity_id": anchor,
                "entity_type": suffix.group(1).lower() if suffix else "anchor",
                "locale": "id-ID",
                "order": anchor_index,
                "source_path": f"source/id-ID/{document.source_rel}",
                "title": document.headings.get(anchor, ""),
            })
            relations.add((anchor, "belongs_to", document_id, "local"))
        for relation in normalized_relations(document):
            target = str(relation["target"])
            scope = "local" if target in local_paths else "external"
            relations.add((document_id, str(relation["predicate"]), target, scope))
        for target in document.references:
            scope = "local" if target in local_paths else "external"
            if scope == "external" and target not in external_urls:
                raise RuntimeError(f"Unresolved body reference {target} in {document.source_rel}")
            relations.add((document_id, "references", target, scope))

    for batch, path, output_rel in iter_generated_assets():
        asset_id = generated_asset_id(batch, path)
        payload = path.read_bytes()
        entities.append({
            "batch": batch,
            "bytes": len(payload),
            "entity_id": asset_id,
            "entity_type": "simulation_asset",
            "license": "CC-BY-SA-4.0",
            "locale": "id-ID",
            "output_path": output_rel,
            "sha256": sha256(payload),
            "source_path": f"generated/simulations/{batch}/{path.name}",
        })
        match = re.match(r"(SIM\d{3})_", path.name)
        if match:
            relations.add((asset_id, "generated_by", f"O006-C140-CMP-{match.group(1)}", "local"))

    batch_simulations = {
        "c1": [f"O006-C140-CMP-SIM{i:03d}" for i in range(1, 5)],
        "c2": ["O006-C140-CMP-SIM005"],
    }
    for batch, path in SIMULATION_RECEIPTS.items():
        payload = path.read_bytes()
        receipt_id = f"O006-C140-CMP-{batch.upper()}-SIM-RECEIPT"
        entities.append({
            "batch": batch,
            "bytes": len(payload),
            "entity_id": receipt_id,
            "entity_type": "simulation_receipt",
            "license": "CC-BY-SA-4.0",
            "locale": "id-ID",
            "output_path": f"assets/simulations/receipts/{path.name}",
            "sha256": sha256(payload),
            "source_path": f"build/{path.name}",
        })
        for simulation_id in batch_simulations[batch]:
            relations.add((receipt_id, "evidences", simulation_id, "local"))

    entity_lines = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in sorted(entities, key=lambda row: str(row["entity_id"])))
    relation_rows = [
        {"subject": subject, "predicate": predicate, "object": obj, "scope": scope}
        for subject, predicate, obj, scope in sorted(relations)
    ]
    document_lines = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in documents_backend)
    backend_payloads = {
        "entities.jsonl": entity_lines.encode("utf-8"),
        "relations.csv": csv_payload(["subject", "predicate", "object", "scope"], relation_rows),
        "documents.jsonl": document_lines.encode("utf-8"),
    }
    backend_manifest_rows = [
        {"path": path, "bytes": len(payload), "sha256": sha256(payload)}
        for path, payload in sorted(backend_payloads.items())
    ]
    backend_payloads["MANIFEST.csv"] = csv_payload(["path", "bytes", "sha256"], backend_manifest_rows)

    source_rows = [
        {"path": f"source/id-ID/{document.source_rel}", "bytes": len(document.raw), "sha256": sha256(document.raw)}
        for document in documents
    ]
    receipt = canonical_json({
        "backend": {
            "bytes": sum(len(value) for value in backend_payloads.values()),
            "entities": len(entities),
            "files": len(backend_payloads),
            "manifest_sha256": sha256(backend_payloads["MANIFEST.csv"]),
            "relations": len(relation_rows),
        },
        "browser_processes_used": False,
        "boundary": "cumulative-through-c2",
        "cumulative_documents": len(documents),
        "cumulative_required_ids": sorted(REQUIRED_CUMULATIVE_C2),
        "html": {
            "bytes": sum(len(value) for value in html_payloads.values()),
            "files": len(html_payloads),
            "manifest_sha256": sha256(html_payloads["MANIFEST.csv"]),
        },
        "network_access": False,
        "schema": "o006.c140.companion-cumulative-c2-build.v1",
        "simulation_receipts": [
            {
                "batch": batch,
                "bytes": path.stat().st_size,
                "path": f"build/{path.name}",
                "sha256": sha256(path.read_bytes()),
            }
            for batch, path in SIMULATION_RECEIPTS.items()
        ],
        "source": source_rows,
        "status": "pass",
        "translation_provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
    })
    return html_payloads, backend_payloads, receipt


def write_payloads(target: Path, payloads: dict[str, bytes]) -> None:
    if target.exists():
        shutil.rmtree(target)
    for name, payload in sorted(payloads.items()):
        path = target / PurePosixPath(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


def compare_payloads(target: Path, payloads: dict[str, bytes]) -> list[str]:
    expected = set(payloads)
    actual = {path.relative_to(target).as_posix() for path in target.rglob("*") if path.is_file()} if target.is_dir() else set()
    errors = [f"missing:{name}" for name in sorted(expected - actual)]
    errors.extend(f"extra:{name}" for name in sorted(actual - expected))
    for name in sorted(expected & actual):
        if (target / PurePosixPath(name)).read_bytes() != payloads[name]:
            errors.append(f"mismatch:{name}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    documents = load_documents()
    html_payloads, backend_payloads, receipt = build_payloads(documents)
    if args.write:
        write_payloads(HTML_TARGET, html_payloads)
        write_payloads(BACKEND_TARGET, backend_payloads)
        RECEIPT_TARGET.parent.mkdir(parents=True, exist_ok=True)
        RECEIPT_TARGET.write_bytes(receipt)
        mode_name = "written"
    else:
        errors = compare_payloads(HTML_TARGET, html_payloads)
        errors.extend(f"backend/{item}" for item in compare_payloads(BACKEND_TARGET, backend_payloads))
        if not RECEIPT_TARGET.is_file():
            errors.append("missing:C2_BUILD_RECEIPT.json")
        elif RECEIPT_TARGET.read_bytes() != receipt:
            errors.append("mismatch:C2_BUILD_RECEIPT.json")
        if errors:
            raise RuntimeError("Deterministic replay failed: " + ", ".join(errors[:40]))
        mode_name = "verified"
    print(json.dumps({
        "backend_files": len(backend_payloads),
        "documents": len(documents),
        "html_files": len(html_payloads),
        "mode": mode_name,
        "receipt_sha256": sha256(receipt),
        "status": "pass",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
