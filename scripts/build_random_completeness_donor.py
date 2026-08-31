#!/usr/bin/env python3
"""Build the isolated id-ID Random completeness donor without a browser.

The admitted translation is an immutable import.  This builder copies its
closed first-party/runtime dependencies, rewrites only relative HTML links to
the already published complete Random edition, and adds one clearly identified
C140 collection notice to the derived reader page.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "random-completeness"
AUTHORITY = COMPONENT / "authority"
TARGET = COMPONENT / "source" / "id-ID" / "random" / "point" / "Sufficient.html"
BACKEND = COMPONENT / "backend"
BUILD = COMPONENT / "build" / "html-id"
MANIFEST = COMPONENT / "build" / "MANIFEST.csv"
RECEIPT = COMPONENT / "build" / "BUILD_RECEIPT.json"

PROVENANCE = "OpenAI Codex gpt-5.6-sol, Ultra"
COMPONENT_ID = "O006-C140-RANDOM-COMPLETENESS"
NOTICE_ID = "o006.c140.random-completeness.component-notice"
SOURCE_URL = "https://www.randomservices.org/random/point/Sufficient.html"
PUBLISHED_RANDOM_BASE = (
    "https://kokunoyumeto.github.io/mathematical-statistics-id/"
    "random/point/Sufficient.html"
)

SOURCE_BYTES = 57_507
SOURCE_SHA256 = "4d7402f2a960ea2b4232e57e4ee5992ac29801b9269f300f17f8e83074d5a0e4"
TARGET_BYTES = 60_900
TARGET_SHA256 = "18b0305dc25a19a834204fdf84029ff67408f98262024717abf597c745a00197"

# Every frozen payload used by the reader is pinned independently of the
# import receipt.  Paths are component-relative and therefore portable.
FROZEN_IDENTITIES: dict[PurePosixPath, tuple[int, str]] = {
    PurePosixPath("authority/upstream/random/point/Sufficient.html"): (
        SOURCE_BYTES,
        SOURCE_SHA256,
    ),
    PurePosixPath("authority/upstream/random/Screen.css"): (
        5_433,
        "589035811781debb33e3aa90ca0f376532b8ade30d54fad5c56838bec5c8d707",
    ),
    PurePosixPath("authority/upstream/random/Basic.js"): (
        935,
        "006372877a2b384e20c3e1a364ddde4791890ad02020f654c22372206891b00b",
    ),
    PurePosixPath("authority/upstream/random/icons/Icon.svg"): (
        373,
        "09ccb2c9f9c50cd4d7a1c867fa112534afa56a12ef0f8a96a0d682ec6b8a9d8b",
    ),
    PurePosixPath("authority/upstream/random/icons/Plus.svg"): (
        291,
        "1bd78cdc7997d6237bc809cef5f36e074c551ec3224b226c38735be898bc439a",
    ),
    PurePosixPath("authority/upstream/random/icons/Minus.svg"): (
        223,
        "a55a72ce346d0fe73318fecfa994c7fda8766694a448c3b968122df7a916d7fc",
    ),
    PurePosixPath("authority/upstream/MathJax/tex-svg.js"): (
        1_704_911,
        "dba9c7e8646389650c445e0547023942bed229b3fdb9513b1c6c01237af0b81a",
    ),
    PurePosixPath(
        "authority/runtime/MathJax-3.1.2/input/tex/extensions/boldsymbol.js"
    ): (
        4_709,
        "716cf8735d00abfb1627f8adbbf4aeb915ac9b5c55d47aeaf276e73dac6a2aa1",
    ),
    PurePosixPath("authority/runtime/MathJax-3.1.2/LICENSE.txt"): (
        11_358,
        "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    ),
    PurePosixPath("authority/witness/random/index.html"): (
        22_462,
        "a26f07b700c9de8c7ce83e5a2f38e1e676ed5b085fec8c4a52bb44abefaa8ba8",
    ),
    PurePosixPath("authority/witness/random/Credits.html"): (
        6_467,
        "2d28d0293b41b71d08a531d37399205f657fbed77592c8f7acd54bf2a54113bf",
    ),
}

COPY_MAP: dict[PurePosixPath, PurePosixPath] = {
    PurePosixPath("authority/upstream/random/Screen.css"):
        PurePosixPath("random/Screen.css"),
    PurePosixPath("authority/upstream/random/Basic.js"):
        PurePosixPath("random/Basic.js"),
    PurePosixPath("authority/upstream/random/icons/Icon.svg"):
        PurePosixPath("random/icons/Icon.svg"),
    PurePosixPath("authority/upstream/random/icons/Plus.svg"):
        PurePosixPath("random/icons/Plus.svg"),
    PurePosixPath("authority/upstream/random/icons/Minus.svg"):
        PurePosixPath("random/icons/Minus.svg"),
    PurePosixPath("authority/upstream/MathJax/tex-svg.js"):
        PurePosixPath("MathJax/tex-svg.js"),
    PurePosixPath(
        "authority/runtime/MathJax-3.1.2/input/tex/extensions/boldsymbol.js"
    ): PurePosixPath("MathJax/input/tex/extensions/boldsymbol.js"),
    PurePosixPath("authority/runtime/MathJax-3.1.2/LICENSE.txt"):
        PurePosixPath("licenses/MathJax-3.1.2-LICENSE.txt"),
}

HREF_RE = re.compile(
    r"(?P<prefix>\bhref\s*=\s*)(?P<quote>['\"])(?P<value>.*?)(?P=quote)",
    re.IGNORECASE,
)


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


def component_path(relative: PurePosixPath) -> Path:
    return COMPONENT / Path(relative.as_posix())


def identity(relative: PurePosixPath, payload: bytes) -> dict[str, object]:
    return {
        "path": relative.as_posix(),
        "bytes": len(payload),
        "sha256": sha256(payload),
    }


def validate_frozen_inputs() -> dict[PurePosixPath, bytes]:
    payloads: dict[PurePosixPath, bytes] = {}
    for relative, (expected_bytes, expected_sha) in FROZEN_IDENTITIES.items():
        path = component_path(relative)
        if not path.is_file():
            raise RuntimeError(f"missing frozen donor input: {relative.as_posix()}")
        data = path.read_bytes()
        if len(data) != expected_bytes or sha256(data) != expected_sha:
            raise RuntimeError(f"frozen donor identity differs: {relative.as_posix()}")
        payloads[relative] = data

    target = TARGET.read_bytes()
    if len(target) != TARGET_BYTES or sha256(target) != TARGET_SHA256:
        raise RuntimeError("canonical imported donor target differs")

    import_receipt_path = COMPONENT / "IMPORT_RECEIPT.json"
    import_receipt = json.loads(import_receipt_path.read_bytes())
    expected_import = {
        "source_bytes": SOURCE_BYTES,
        "source_sha256": SOURCE_SHA256,
        "target_bytes": TARGET_BYTES,
        "target_sha256": TARGET_SHA256,
        "target_locale": "id-ID",
        "translation_provenance": PROVENANCE,
    }
    if any(import_receipt.get(key) != value for key, value in expected_import.items()):
        raise RuntimeError("component import receipt identity differs")

    with (AUTHORITY / "FREEZE_MANIFEST.csv").open(
        "r", encoding="utf-8", newline=""
    ) as stream:
        rows = list(csv.DictReader(stream))
    by_path = {row["relative_path"]: row for row in rows}
    for relative, (expected_bytes, expected_sha) in FROZEN_IDENTITIES.items():
        row = by_path.get(relative.as_posix())
        if (
            row is None
            or int(row["bytes"]) != expected_bytes
            or row["sha256"] != expected_sha
        ):
            raise RuntimeError(
                f"authority freeze manifest differs: {relative.as_posix()}"
            )
    return payloads


def rewrite_relative_html_hrefs(text: str) -> tuple[str, list[dict[str, str]]]:
    rewrites: list[dict[str, str]] = []

    def replace(match: re.Match[str]) -> str:
        value = match.group("value")
        parsed = urlsplit(value)
        if (
            parsed.scheme
            or parsed.netloc
            or value.startswith("#")
            or not parsed.path.lower().endswith((".html", ".htm"))
        ):
            return match.group(0)
        destination = urljoin(PUBLISHED_RANDOM_BASE, value)
        if not destination.startswith(
            "https://kokunoyumeto.github.io/mathematical-statistics-id/"
        ):
            raise RuntimeError(f"relative HTML rewrite escaped publication: {value}")
        rewrites.append({"source": value, "target": destination})
        return (
            match.group("prefix")
            + match.group("quote")
            + destination
            + match.group("quote")
        )

    result = HREF_RE.sub(replace, text)
    return result, rewrites


def donor_page(target: bytes) -> tuple[bytes, list[dict[str, str]]]:
    text = target.decode("utf-8")
    rewritten, rewrites = rewrite_relative_html_hrefs(text)
    if len(rewrites) != 31:
        raise RuntimeError("relative HTML link rewrite census differs")
    if rewritten.count("<body>") != 1 or NOTICE_ID in rewritten:
        raise RuntimeError("canonical donor body/notice insertion point differs")
    notice = f'''<section id="{NOTICE_ID}" class="c140-component-notice" aria-label="Status komponen C140" style="border:2px solid #163b72;border-radius:.35rem;background:#f3f7fc;padding:.75rem 1rem;margin:0 0 1.25rem 0;max-width:100%;box-sizing:border-box;">
\t<p style="margin:.15rem 0;"><strong>Komponen donor C140.</strong> Unit lengkap tentang statistik cukup, lengkap, dan ancillary ini melengkapi rangkaian STAT 415; unit ini tetap merupakan adaptasi terpisah dari karya Kyle Siegrist dan bukan materi Penn State.</p>
\t<p style="margin:.35rem 0 .15rem 0;">Provenans terjemahan dan rekonstruksi: {PROVENANCE}. Hak, atribusi, dan riwayat perubahan komponen dipertahankan secara terpisah.</p>
</section>'''
    derived = rewritten.replace("<body>", "<body>\n\n" + notice, 1).encode("utf-8")

    # Parsing is a build-time static integrity check only; it launches no reader.
    soup = BeautifulSoup(derived, "html.parser")
    if soup.html is None or soup.html.get("lang") != "id-ID":
        raise RuntimeError("derived donor locale differs")
    found_notice = soup.find(id=NOTICE_ID)
    if found_notice is None or PROVENANCE not in found_notice.get_text(" ", strip=True):
        raise RuntimeError("C140 component notice/provenance differs")
    return derived, rewrites


def shell_style() -> str:
    return """
body{font:1rem/1.55 system-ui,-apple-system,Segoe UI,sans-serif;color:#172033;background:#f4f7fb;margin:0}
.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.6rem;z-index:2}
main{width:min(72rem,calc(100% - 2rem));margin:2rem auto;background:#fff;padding:clamp(1rem,3vw,2.5rem);box-sizing:border-box;border:1px solid #d7dfeb;border-radius:.5rem}
h1{line-height:1.2;color:#173d72}a{color:#075fb5}.card{border-left:.35rem solid #173d72;background:#f2f6fb;padding:1rem;margin:1.25rem 0}
code{overflow-wrap:anywhere}footer{width:min(72rem,calc(100% - 2rem));margin:0 auto 2rem;color:#445}
""".strip()


def index_page() -> bytes:
    html = f"""<!doctype html>
<html lang="id-ID"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Komponen C140 — Statistik Cukup, Lengkap, dan Ancillary</title><style>{shell_style()}</style></head><body>
<a class="skip" href="#main">Lewati ke isi utama</a><main id="main"><h1>Statistik Cukup, Lengkap, dan Ancillary</h1>
<p>Komponen donor tunggal untuk O006/C140, diimpor dari edisi Bahasa Indonesia lengkap <cite>Random</cite> karya Kyle Siegrist.</p>
<div class="card"><h2>Baca unit</h2><p><a href="random/point/Sufficient.html">Buka unit lengkap Bahasa Indonesia</a>.</p></div>
<h2>Status dan cakupan</h2><p>Lengkap untuk satu unit donor: kecukupan, kelengkapan, statistik ancillary, Rao–Blackwell, Lehmann–Scheffé, Basu, keluarga distribusi khusus, dan keluarga eksponensial.</p>
<h2>Hak dan provenans</h2><p>Situs Random menyatakan CC BY 2.0 pada halaman depan, sedangkan halaman Kredit menautkan CC BY 1.0. Perbedaan itu dipertahankan, bukan diseragamkan. Runtime MathJax 3.1.2 tetap Apache-2.0.</p>
<p><a href="licenses/index.html">Baca atribusi, perubahan, dan lisensi komponen</a>. Sumber resmi: <a href="{SOURCE_URL}">Random Services</a>.</p>
<p>Provenans terjemahan dan rekonstruksi: {PROVENANCE}.</p></main>
<footer>Komponen beridentitas stabil <code>{COMPONENT_ID}</code>.</footer></body></html>\n"""
    return html.encode("utf-8")


def rights_page() -> bytes:
    html = f"""<!doctype html>
<html lang="id-ID"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Atribusi, perubahan, dan lisensi — donor Random C140</title><style>{shell_style()}</style></head><body>
<a class="skip" href="#main">Lewati ke isi utama</a><main id="main"><h1>Atribusi, perubahan, dan lisensi</h1>
<h2>Konten Random</h2><p>Karya asal: <cite>Random: Probability, Mathematical Statistics, and Stochastic Processes</cite> oleh Kyle Siegrist. Halaman sumber: <a href="{SOURCE_URL}">Sufficient, Complete and Ancillary Statistics</a>.</p>
<p>Halaman depan resmi menyatakan <a rel="license" href="https://creativecommons.org/licenses/by/2.0/">CC BY 2.0</a>, sedangkan halaman <a href="https://www.randomservices.org/random/Credits.html">Credits</a> menautkan <a rel="license" href="https://creativecommons.org/licenses/by/1.0/">CC BY 1.0</a>. Edisi ini mempertahankan kedua saksi dan memenuhi atribusi serta pemberitahuan perubahan; tidak ada pelabelan ulang seragam.</p>
<h2>Perubahan</h2><p>Perubahan yang diwarisi dari edisi Bahasa Indonesia mencakup penerjemahan, ID stabil tambahan, pengalihan tautan, serta koreksi matematis, ejaan, dan struktur yang tercatat. Rekonstruksi komponen C140 menambahkan satu pemberitahuan koleksi dan mengarahkan tautan HTML relatif ke edisi Random Bahasa Indonesia yang telah diterbitkan. Byte target impor kanonis tetap tidak diubah.</p>
<h2>MathJax</h2><p>MathJax 3.1.2 disertakan di bawah Apache License 2.0. <a href="MathJax-3.1.2-LICENSE.txt">Baca teks lisensi yang disertakan</a>.</p>
<h2>Provenans</h2><p>{PROVENANCE}. Seluruh kredit pengarang dan kontributor manusia dipertahankan. Tidak ada dukungan atau pengesahan oleh Kyle Siegrist, Random Services, Penn State, atau MathJax yang tersirat.</p>
<p><a href="../index.html">Kembali ke indeks komponen</a>.</p></main></body></html>\n"""
    return html.encode("utf-8")


def fallback_svg(label: str, colour: str) -> bytes:
    # Screen.css references three dice images that are not direct dependencies
    # in the admitted freeze.  Original text-only SVG fallbacks keep the
    # isolated reader closed without misrepresenting them as Random assets.
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18" role="img" aria-label="{label}">
<rect x="1" y="1" width="16" height="16" rx="3" fill="{colour}"/><circle cx="9" cy="9" r="2.25" fill="white"/>
</svg>\n'''
    return svg.encode("utf-8")


def manifest_payload(reader: dict[PurePosixPath, bytes], roles: dict[PurePosixPath, str]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=("relative_path", "role", "bytes", "sha256"),
        lineterminator="\n",
    )
    writer.writeheader()
    for relative in sorted(reader, key=lambda path: path.as_posix()):
        data = reader[relative]
        writer.writerow(
            {
                "relative_path": relative.as_posix(),
                "role": roles[relative],
                "bytes": len(data),
                "sha256": sha256(data),
            }
        )
    return stream.getvalue().encode("utf-8")


def backend_counts() -> dict[str, int]:
    entities = [
        json.loads(line)
        for line in (BACKEND / "entities.jsonl").read_text("utf-8").splitlines()
        if line
    ]
    with (BACKEND / "relations.csv").open("r", encoding="utf-8", newline="") as stream:
        relations = list(csv.DictReader(stream))
    if len(entities) != 325 or len(relations) != 474:
        raise RuntimeError("donor backend census differs")
    return {"entities": len(entities), "relations": len(relations)}


def compute_outputs() -> dict[str, bytes]:
    frozen = validate_frozen_inputs()
    target = TARGET.read_bytes()
    page, rewrites = donor_page(target)

    reader: dict[PurePosixPath, bytes] = {
        PurePosixPath("index.html"): index_page(),
        PurePosixPath("random/point/Sufficient.html"): page,
        PurePosixPath("licenses/index.html"): rights_page(),
    }
    roles: dict[PurePosixPath, str] = {
        PurePosixPath("index.html"): "component-index",
        PurePosixPath("random/point/Sufficient.html"): "derived-reader-page",
        PurePosixPath("licenses/index.html"): "rights-and-attribution",
    }
    for source_relative, output_relative in COPY_MAP.items():
        reader[output_relative] = frozen[source_relative]
        roles[output_relative] = (
            "runtime-license"
            if output_relative.name.endswith("LICENSE.txt")
            else "frozen-runtime"
            if output_relative.parts[0] == "MathJax"
            else "frozen-first-party-asset"
        )

    fallbacks = {
        PurePosixPath("random/icons/DieGreen5.svg"): fallback_svg("Definisi", "#197443"),
        PurePosixPath("random/icons/DieBlue5.svg"): fallback_svg("Hasil matematis", "#1757a6"),
        PurePosixPath("random/icons/DieRed5.svg"): fallback_svg("Aplikasi", "#a62323"),
        PurePosixPath("random/icons/Step.svg"): fallback_svg("Langkah", "#665099"),
        PurePosixPath("random/icons/Stop.svg"): fallback_svg("Berhenti", "#8f2525"),
        PurePosixPath("random/icons/Run.svg"): fallback_svg("Jalankan", "#197443"),
        PurePosixPath("random/icons/Reset.svg"): fallback_svg("Atur ulang", "#73521e"),
    }
    for relative, payload in fallbacks.items():
        reader[relative] = payload
        roles[relative] = "original-build-only-css-fallback"

    manifest = manifest_payload(reader, roles)
    outputs = {
        f"build/html-id/{relative.as_posix()}": payload
        for relative, payload in reader.items()
    }
    outputs["build/MANIFEST.csv"] = manifest

    import_receipt_data = (COMPONENT / "IMPORT_RECEIPT.json").read_bytes()
    freeze_manifest_data = (AUTHORITY / "FREEZE_MANIFEST.csv").read_bytes()
    receipt = {
        "schema": "o006.c140.random-completeness.build.v1",
        "status": "built",
        "component_id": COMPONENT_ID,
        "locale": "id-ID",
        "translation_provenance": PROVENANCE,
        "canonical_import_preserved": True,
        "authority": {
            "source": {
                "path": "authority/upstream/random/point/Sufficient.html",
                "url": SOURCE_URL,
                "bytes": SOURCE_BYTES,
                "sha256": SOURCE_SHA256,
            },
            "target": {
                "path": "source/id-ID/random/point/Sufficient.html",
                "bytes": TARGET_BYTES,
                "sha256": TARGET_SHA256,
            },
            "import_receipt": identity(
                PurePosixPath("IMPORT_RECEIPT.json"), import_receipt_data
            ),
            "freeze_manifest": identity(
                PurePosixPath("authority/FREEZE_MANIFEST.csv"),
                freeze_manifest_data,
            ),
        },
        "transformation": {
            "derived_page": "build/html-id/random/point/Sufficient.html",
            "relative_html_href_rewrites": len(rewrites),
            "rewrite_destination": (
                "https://kokunoyumeto.github.io/mathematical-statistics-id/"
            ),
            "component_notice_id": NOTICE_ID,
            "other_canonical_target_mutations": 0,
        },
        "backend": backend_counts(),
        "reader": {
            "path": "build/html-id",
            "files": len(reader),
            "bytes": sum(len(payload) for payload in reader.values()),
            "manifest_path": "build/MANIFEST.csv",
            "manifest_bytes": len(manifest),
            "manifest_sha256": sha256(manifest),
            "build_only_css_fallbacks": len(fallbacks),
        },
        "rights": {
            "Random landing witness": "CC BY 2.0",
            "Random Credits witness": "CC BY 1.0",
            "MathJax 3.1.2": "Apache-2.0",
            "discrepancy_preserved": True,
            "aggregate_uniform_relicense": False,
        },
        "offline": {
            "direct_local_dependencies_closed": True,
            "dynamic_mathjax_boldsymbol_closed": True,
            "browser_used": False,
            "analytics": False,
        },
    }
    outputs["build/BUILD_RECEIPT.json"] = canonical_json(receipt)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    outputs = compute_outputs()
    if args.write:
        for relative, payload in outputs.items():
            atomic_write(component_path(PurePosixPath(relative)), payload)
        state = "written"
    else:
        for relative, payload in outputs.items():
            path = component_path(PurePosixPath(relative))
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f"donor build output differs: {relative}")
        state = "verified"

    receipt = outputs["build/BUILD_RECEIPT.json"]
    data = json.loads(receipt)
    print(
        json.dumps(
            {
                "mode": state,
                "status": data["status"],
                "reader_files": data["reader"]["files"],
                "reader_bytes": data["reader"]["bytes"],
                "receipt_sha256": sha256(receipt),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
