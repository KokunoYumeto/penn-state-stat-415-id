#!/usr/bin/env python3
"""Build the canonical consolidated HTML source for PDF and EPUB.

The reader pages remain the authority for the derivative.  This normalizer
extracts only their instructional main surfaces, makes disclosure content
unconditionally visible, namespaces only colliding DOM IDs, rewrites internal
links, and appends one component-rights/provenance appendix.  It never mutates
the complete HTML reader.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup, Tag


ROOT = Path(__file__).resolve().parents[1]
READER_DIR = ROOT / "build" / "html-id"
BOOK_DIR = ROOT / "build" / "book"
OUTPUT_HTML = BOOK_DIR / "stat415-id-book.html"
OUTPUT_RECEIPT = ROOT / "build" / "CONSOLIDATED_BOOK_SOURCE_RECEIPT.json"
READER_MANIFEST = ROOT / "build" / "THROUGH_LESSON12_MANIFEST.csv"
EXPECTED_READER_MANIFEST_BYTES = 11_573
EXPECTED_READER_MANIFEST_SHA256 = (
    "697c9ee8e23cc10469fea4d1894e16471ffb4276edd1f0d25bebfb5be0dbe79e"
)
DOCUMENTS = ["index.html"] + [f"Lesson{i:02}.html" for i in range(13)]
DOCUMENT_KEYS = {
    "index.html": "index",
    **{f"Lesson{i:02}.html": f"lesson{i:02}" for i in range(13)},
}
SOURCE_DATE = "2026-08-26"
PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
BOOK_FORMAT_REPAIRS = {
    "O006-PSU-001-M0304": {
        "document": "Lesson00.html",
        "replacement": (
            r"\[\begin{aligned}"
            r"0.3&=P(X=1)+P(X=2),\\"
            r"P(X=2)&=0.3-P(X=1)=0.3-0.1=0.2"
            r"\end{aligned}\]"
        ),
        "rationale": (
            "normalize a display-alignment marker into an equivalent two-line "
            "derivation for portable print/MathML rendering"
        ),
    },
    "O006-PSU-012-M0134": {
        "document": "Lesson11.html",
        "replacement": (
            r"\[k(p|y)=\frac{\Gamma(5+y)}{\Gamma(4)\Gamma(y+1)}"
            r"p^{4-1}(1-p)^{(y+1)-1}\]"
        ),
        "rationale": (
            "remove a redundant nested align environment and literal \\n control "
            "sequence for portable print/MathML rendering"
        ),
    },
    "O006-PSU-013-M0272": {
        "document": "Lesson12.html",
        "replacement": (
            r"\[\begin{aligned}"
            r"E(\hat{\beta})"
            r"&=\frac{1}{\sum (x_i-\bar{x})^2}"
            r"\sum E\left[(x_i-\bar{x})Y_i\right]\\"
            r"&=\frac{1}{\sum (x_i-\bar{x})^2}"
            r"\sum (x_i-\bar{x})(\alpha+\beta(x_i-\bar{x}))\\"
            r"&=\frac{1}{\sum (x_i-\bar{x})^2}"
            r"\left[\alpha\sum (x_i-\bar{x})"
            r"+\beta\sum (x_i-\bar{x})^2\right]\\"
            r"&=\beta"
            r"\end{aligned}\]"
        ),
        "rationale": (
            "replace an invalid display-level line break with an equivalent "
            "aligned derivation that reflows on the page"
        ),
    },
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_html_bytes(text: str) -> bytes:
    return (text.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n").encode(
        "utf-8"
    )


def source_document(name: str) -> tuple[bytes, BeautifulSoup, Tag]:
    path = READER_DIR / name
    data = path.read_bytes()
    text = data.decode("utf-8")
    soup = BeautifulSoup(text, "html.parser")
    main = soup.select_one("main#quarto-document-content")
    if main is None:
        raise RuntimeError(f"Missing main#quarto-document-content in {name}")
    return data, soup, main


def local_document_name(href: str) -> str | None:
    parsed = urlparse(href)
    if parsed.scheme or parsed.netloc:
        return None
    path = unquote(parsed.path).replace("\\", "/")
    if not path:
        return None
    name = Path(path).name
    for document in DOCUMENTS:
        if name.casefold() == document.casefold():
            return document
    return None


def replace_details(soup: BeautifulSoup, main: Tag) -> int:
    replaced = 0
    for details in list(main.select("details")):
        wrapper = soup.new_tag("div")
        wrapper["class"] = ["expanded-disclosure"]
        wrapper["data-book-expanded"] = "true"
        for key, value in details.attrs.items():
            if key not in {"class", "open"}:
                wrapper[key] = value
        summary = details.find("summary", recursive=False)
        if summary is not None:
            heading = soup.new_tag("p")
            heading["class"] = ["expanded-disclosure-title"]
            strong = soup.new_tag("strong")
            strong.extend(list(summary.contents))
            heading.append(strong)
            wrapper.append(heading)
            summary.extract()
        for child in list(details.contents):
            wrapper.append(child.extract())
        details.replace_with(wrapper)
        replaced += 1
    return replaced


def remove_interactive_chrome(main: Tag) -> int:
    removed = 0
    selectors = (
        "button.code-copy-button",
        ".code-copy-button",
        ".anchorjs-link",
        "script",
        "style",
    )
    for selector in selectors:
        for node in list(main.select(selector)):
            node.decompose()
            removed += 1
    return removed


def apply_book_format_repairs(main: Tag, name: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for stable_id, specification in BOOK_FORMAT_REPAIRS.items():
        if specification["document"] != name:
            continue
        node = main.select_one(f'[data-o006-math-id="{stable_id}"]')
        if node is None:
            raise RuntimeError(f"Missing book-format repair target {stable_id}")
        before = node.get_text()
        replacement = str(specification["replacement"])
        if before == replacement:
            raise RuntimeError(f"Book-format repair unexpectedly already applied: {stable_id}")
        node.clear()
        node.append(replacement)
        records.append(
            {
                "document": name,
                "stable_math_id": stable_id,
                "before_sha256": sha256_bytes(before.encode("utf-8")),
                "after_sha256": sha256_bytes(replacement.encode("utf-8")),
                "rationale": specification["rationale"],
                "scope": "consolidated-book-format-only",
            }
        )
    return records


def rewrite_local_resource(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or value.startswith(("#", "data:")):
        return value
    normalized = value.replace("\\", "/")
    if normalized.startswith("../html-id/"):
        return normalized
    return f"../html-id/{normalized.lstrip('./')}"


def rewrite_id_reference(value: str, mapping: dict[str, str]) -> str:
    tokens = value.split()
    return " ".join(mapping.get(token, token) for token in tokens)


def normalize_document(
    name: str,
    soup: BeautifulSoup,
    main: Tag,
    id_maps: dict[str, dict[str, str]],
) -> tuple[str, dict[str, int], list[dict[str, object]]]:
    key = DOCUMENT_KEYS[name]
    main = BeautifulSoup(str(main), "html.parser").select_one("main")
    if main is None:
        raise RuntimeError(f"Failed to clone main for {name}")

    removed = remove_interactive_chrome(main)
    repairs = apply_book_format_repairs(main, name)
    disclosures = replace_details(soup, main)
    mapping = id_maps[name]

    for node in main.select("[id]"):
        old = str(node["id"])
        new = mapping[old]
        if old != new:
            node["data-book-original-id"] = old
            node["id"] = new

    for node in main.select("[for], [aria-labelledby], [aria-describedby]"):
        if node.has_attr("for"):
            node["for"] = mapping.get(str(node["for"]), str(node["for"]))
        for attr in ("aria-labelledby", "aria-describedby"):
            if node.has_attr(attr):
                node[attr] = rewrite_id_reference(str(node[attr]), mapping)

    for anchor in main.select("a[href]"):
        href = str(anchor.get("href", ""))
        parsed = urlparse(href)
        if parsed.scheme or parsed.netloc:
            continue
        target_name = local_document_name(href)
        if target_name is not None:
            fragment = unquote(parsed.fragment)
            if fragment:
                target = id_maps[target_name].get(fragment, fragment)
                anchor["href"] = f"#{target}"
            else:
                anchor["href"] = f"#{DOCUMENT_KEYS[target_name]}--document"
        elif not parsed.path and parsed.fragment:
            fragment = unquote(parsed.fragment)
            anchor["href"] = f"#{mapping.get(fragment, fragment)}"

    for node in main.select("[src], [poster]"):
        for attr in ("src", "poster"):
            if node.has_attr(attr):
                node[attr] = rewrite_local_resource(str(node[attr]))
    for node in main.select("[srcset]"):
        candidates = []
        for candidate in str(node["srcset"]).split(","):
            fields = candidate.strip().split()
            if fields:
                fields[0] = rewrite_local_resource(fields[0])
                candidates.append(" ".join(fields))
        node["srcset"] = ", ".join(candidates)

    wrapper = soup.new_tag("section")
    wrapper["class"] = ["book-document"]
    wrapper["id"] = f"{key}--document"
    wrapper["data-book-source-document"] = name
    wrapper["data-book-source-component-id"] = str(
        main.get("data-component-id", Path(name).stem)
    )
    for child in list(main.contents):
        wrapper.append(child.extract())

    stats = {
        "code_blocks": len(wrapper.select("pre")),
        "disclosures_expanded": disclosures,
        "figures": len(wrapper.select("figure")),
        "images": len(wrapper.select("img")),
        "interactive_nodes_removed": removed,
        "math_nodes": len(wrapper.select(".math")),
        "book_format_repairs": len(repairs),
        "tables": len(wrapper.select("table")),
    }
    return str(wrapper), stats, repairs


def rights_appendix() -> str:
    return """
<section class="book-document book-rights" id="edition-rights--document">
<h1 id="edition-rights">Provenans, hak, dan perubahan</h1>
<p><strong>Sumber.</strong> Rangkaian publik Penn State STAT 415,
<em>Introduction to Mathematical Statistics</em>, laman utama dan Pelajaran
00-12. Distribusi resmi yang tersedia adalah HTML semantik hasil Quarto; edisi
ini tidak mengklaim sebagai fork sumber QMD yang tidak dipublikasikan.</p>
<p><strong>Hak.</strong> Konten Penn State dan adaptasi Bahasa Indonesianya
tetap berada di bawah CC BY-NC 4.0 kecuali jika suatu komponen menyatakan lain.
MathJax tetap berada di bawah Apache-2.0. Lapisan asli repositori mempunyai
identitas lisensi terpisah sebagaimana dijelaskan dalam <code>LICENSE.md</code>;
koleksi ini tidak direlisensi sebagai satu karya dengan lisensi seragam.</p>
<p><strong>Perubahan.</strong> Struktur, rumus, contoh, solusi, kode, gambar,
tabel, dan hubungan sumber dipertahankan. Perbaikan turunan yang terbukti
dicatat secara terpisah; byte sumber resmi tidak diubah. Tidak ada dukungan
atau pengesahan oleh Penn State yang tersirat.</p>
<p><strong>Provenans terjemahan dan rekonstruksi.</strong>
OpenAI Codex gpt-5.6-sol, Ultra.</p>
<p><strong>Tautan.</strong> Sumber resmi:
<a href="https://online.stat.psu.edu/stat415/">online.stat.psu.edu/stat415</a>.
Repositori edisi:
<a href="https://github.com/KokunoYumeto/penn-state-stat-415-id">penn-state-stat-415-id</a>.
Konsep preservasi:
<a href="https://doi.org/10.5281/zenodo.22077422">10.5281/zenodo.22077422</a>.</p>
</section>
""".strip()


def build() -> tuple[bytes, dict[str, object]]:
    manifest_bytes = READER_MANIFEST.read_bytes()
    if len(manifest_bytes) != EXPECTED_READER_MANIFEST_BYTES:
        raise RuntimeError("Reader manifest byte count changed")
    if sha256_bytes(manifest_bytes) != EXPECTED_READER_MANIFEST_SHA256:
        raise RuntimeError("Reader manifest SHA-256 changed")

    parsed: dict[str, tuple[bytes, BeautifulSoup, Tag]] = {
        name: source_document(name) for name in DOCUMENTS
    }
    all_ids: Counter[str] = Counter()
    per_document_ids: dict[str, list[str]] = {}
    for name, (_data, _soup, main) in parsed.items():
        ids = [str(node["id"]) for node in main.select("[id]")]
        if len(ids) != len(set(ids)):
            raise RuntimeError(f"Source reader has duplicate IDs inside {name}")
        per_document_ids[name] = ids
        all_ids.update(ids)

    id_maps: dict[str, dict[str, str]] = {}
    for name, ids in per_document_ids.items():
        key = DOCUMENT_KEYS[name]
        id_maps[name] = {
            old: (f"{key}--{old}" if all_ids[old] > 1 else old) for old in ids
        }

    document_html: list[str] = []
    format_repairs: list[dict[str, object]] = []
    source_inventory: list[dict[str, object]] = []
    totals: Counter[str] = Counter()
    for ordinal, name in enumerate(DOCUMENTS, start=1):
        data, soup, main = parsed[name]
        normalized, stats, repairs = normalize_document(name, soup, main, id_maps)
        document_html.append(normalized)
        format_repairs.extend(repairs)
        totals.update(stats)
        source_inventory.append(
            {
                "bytes": len(data),
                "document": name,
                "ordinal": ordinal,
                "sha256": sha256_bytes(data),
                **stats,
            }
        )

    body = "\n".join(document_html + [rights_appendix()])
    html = f"""<!doctype html>
<html lang="id-ID">
<head>
<meta charset="utf-8">
<meta name="generator" content="scripts/normalize_consolidated_book.py">
<meta name="translation-provenance" content="{PROVENANCE}">
<meta name="source-date" content="{SOURCE_DATE}">
<title>STAT 415: Pengantar Statistika Matematis - edisi Bahasa Indonesia</title>
<link rel="stylesheet" href="../../source/book/book-source.css">
<script>
window.MathJax = {{
  loader: {{load: ['[tex]/color', '[tex]/cancel']}},
  tex: {{packages: {{'[+]': ['color', 'cancel']}}}},
  svg: {{fontCache: 'local'}}
}};
</script>
<script defer src="../html-id/assets/MathJax/tex-svg.js"></script>
</head>
<body>
{body}
</body>
</html>
"""
    html_bytes = canonical_html_bytes(html)
    normalized = BeautifulSoup(html_bytes.decode("utf-8"), "html.parser")
    final_ids = [str(node["id"]) for node in normalized.select("[id]")]
    duplicates = sorted(key for key, count in Counter(final_ids).items() if count > 1)
    if duplicates:
        raise RuntimeError(f"Consolidated book has duplicate IDs: {duplicates[:10]}")
    images = normalized.select("img")
    missing_alt = [node.get("src", "") for node in images if not node.get("alt", "").strip()]
    if missing_alt:
        raise RuntimeError(f"Images without nonempty alternatives: {missing_alt[:10]}")

    receipt: dict[str, object] = {
        "book_html": {
            "bytes": len(html_bytes),
            "path": OUTPUT_HTML.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(html_bytes),
        },
        "book_format_repairs": format_repairs,
        "colliding_source_id_values": sum(1 for count in all_ids.values() if count > 1),
        "date": SOURCE_DATE,
        "documents": source_inventory,
        "input_reader_manifest": {
            "bytes": len(manifest_bytes),
            "path": READER_MANIFEST.relative_to(ROOT).as_posix(),
            "sha256": sha256_bytes(manifest_bytes),
        },
        "normalized_unique_ids": len(final_ids),
        "rights_appendices": 1,
        "schema": "o006.stat415.consolidated-book-source.v1",
        "source_documents": len(DOCUMENTS),
        "status": "passed",
        "totals": dict(sorted(totals.items())),
        "translation_provenance": PROVENANCE,
        "unique_image_sources": len({str(node.get("src")) for node in images}),
    }
    return html_bytes, receipt


def compare(path: Path, expected: bytes) -> None:
    if not path.exists():
        raise RuntimeError(f"Missing expected output: {path.relative_to(ROOT)}")
    actual = path.read_bytes()
    if actual != expected:
        raise RuntimeError(
            f"Deterministic output mismatch: {path.relative_to(ROOT)} "
            f"expected={sha256_bytes(expected)} actual={sha256_bytes(actual)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    html_bytes, receipt = build()
    receipt_bytes = canonical_json_bytes(receipt)
    if args.check_only:
        compare(OUTPUT_HTML, html_bytes)
        compare(OUTPUT_RECEIPT, receipt_bytes)
        mode = "verified"
    else:
        BOOK_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_HTML.write_bytes(html_bytes)
        OUTPUT_RECEIPT.write_bytes(receipt_bytes)
        mode = "written"
    print(
        json.dumps(
            {
                "documents": receipt["source_documents"],
                "html_bytes": receipt["book_html"]["bytes"],
                "html_sha256": receipt["book_html"]["sha256"],
                "mode": mode,
                "totals": receipt["totals"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
