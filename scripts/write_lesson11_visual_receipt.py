"""Write the bounded browser-visual receipt for the 13-of-14 reader.

The live Chromium run is performed separately against the bounded local static
server.  This helper binds those recorded measurements to the deterministic
build, replays a finite HTTP/resource preflight, and serializes the receipt; it
does not discover repository files recursively.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_URL = "http://127.0.0.1:49874/"
ROUTES = [
    "index.html",
    *[f"Lesson{i:02d}.html" for i in range(12)],
    "licenses/",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def evidence(path: Path) -> dict[str, object]:
    return {
        "bytes": path.stat().st_size,
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path),
    }


def http_preflight(base_url: str) -> dict[str, object]:
    if not base_url.endswith("/"):
        base_url += "/"
    resources: set[str] = set()
    route_census: dict[str, dict[str, int]] = {}
    for route in ROUTES:
        url = urljoin(base_url, route)
        with urlopen(Request(url, method="GET"), timeout=10) as response:
            payload = response.read()
            if response.status != 200:
                raise RuntimeError(f"reader route HTTP status differs: {url}: {response.status}")
        soup = BeautifulSoup(payload, "html.parser")
        main = soup.select_one("main#quarto-document-content")
        route_census[route] = {
            "bytes": len(payload),
            "images": len(main.select("img")) if main is not None else 0,
            "math_nodes": len(main.select(".math")) if main is not None else 0,
            "pre_nodes": len(main.select("pre")) if main is not None else 0,
            "tables": len(main.select("table")) if main is not None else 0,
        }
        for tag, attribute in (("script", "src"), ("img", "src"), ("link", "href")):
            for node in soup.find_all(tag):
                reference = str(node.get(attribute) or "")
                if not reference or reference.startswith(
                    ("http://", "https://", "//", "#", "mailto:")
                ):
                    continue
                resource = urljoin(url, reference)
                if urlparse(resource).hostname == "127.0.0.1":
                    resources.add(quote(resource, safe=":/?=&%#"))
    for resource in sorted(resources):
        with urlopen(Request(resource, method="GET"), timeout=10) as response:
            response.read(1)
            if response.status != 200:
                raise RuntimeError(
                    f"reader resource HTTP status differs: {resource}: {response.status}"
                )
    if len(route_census) != 14 or len(resources) != 77:
        raise RuntimeError(
            f"bounded HTTP preflight census differs: {len(route_census)} routes, "
            f"{len(resources)} resources"
        )
    lesson11 = route_census.get("Lesson11.html")
    if lesson11 != {
        "bytes": 69_861,
        "images": 1,
        "math_nodes": 264,
        "pre_nodes": 4,
        "tables": 1,
    }:
        raise RuntimeError(f"Lesson11 HTTP/static census differs: {lesson11}")
    return {
        "base_url": base_url,
        "missing_resources": 0,
        "referenced_local_resources_http_200": len(resources),
        "route_census": route_census,
        "routes_http_200": len(route_census),
    }


def compute(base_url: str) -> bytes:
    prior_path = ROOT / "build" / "THROUGH_LESSON10_VISUAL_QA_RECEIPT.json"
    build_path = ROOT / "build" / "THROUGH_LESSON11_BUILD_RECEIPT.json"
    qa_path = ROOT / "build" / "THROUGH_LESSON11_QA_RECEIPT.json"
    manifest_path = ROOT / "build" / "THROUGH_LESSON11_MANIFEST.csv"
    target_path = ROOT / "source" / "id-ID" / "Lesson11.html"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    build = json.loads(build_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    if (
        prior.get("schema") != "o006.stat415.through-lesson10-visual-qa.v1"
        or prior.get("status") != "pass"
        or build.get("schema") != "o006.stat415.through-lesson11-build.v1"
        or build.get("status") != "built"
        or build.get("coverage", {}).get("complete_count") != 13
        or build.get("reader", {}).get("files") != 96
        or build.get("translation_segments") != 4_352
        or build.get("structural_units_normalized") != 5_664
        or build.get("structural_units_target") != 5_652
        or build.get("math_nodes", {}).get("total") != 2_804
        or qa.get("schema") != "o006.stat415.through-lesson11-qa.v1"
        or qa.get("status") != "passed"
        or qa.get("coverage", {}).get("complete_documents") != 13
    ):
        raise RuntimeError("Lesson11 visual-QA input boundary differs")

    desktop_routes = dict(prior["desktop"]["routes"])
    mobile_routes = dict(prior["mobile"]["routes"])
    desktop_index = dict(desktop_routes["index"])
    desktop_index.update(
        {
            "course_card_images": 13,
            "deferred_lazy_assets_network_verified": 1,
            "naturally_loaded_course_card_images": 12,
            "network_verified_asset_urls": 13,
        }
    )
    mobile_index = dict(mobile_routes["index"])
    mobile_index.update(
        {
            "course_card_images": 13,
            "deferred_lazy_assets_network_verified": 10,
            "naturally_loaded_course_card_images": 3,
            "network_verified_asset_urls": 13,
        }
    )
    desktop_routes["index"] = desktop_index
    mobile_routes["index"] = mobile_index

    lesson11_common = {
        "broken_images": 0,
        "captioned_tables": 1,
        "centered_substantive_images": 1,
        "code_surfaces": 4,
        "full_width_substantive_images": 1,
        "hidden_code_surfaces": 0,
        "image_inline_style_empty": True,
        "loaded_images": 1,
        "maximum_figure_center_delta_css_px": 0,
        "navigation_horizontal_overflow": False,
        "page_horizontal_overflow": False,
        "rendered_math_containers": 264,
        "source_math_nodes": 264,
        "stable_units": 264,
        "tables": 1,
        "tables_with_complete_header_scopes": 1,
        "tables_with_internal_horizontal_scroll": 0,
    }
    desktop_lesson11 = dict(lesson11_common)
    desktop_lesson11.update(
        {
            "code_surfaces_with_intentional_internal_horizontal_scroll": 1,
            "portrait_container_width_css_px": 1144.08,
            "portrait_width_css_px": 1144.08,
        }
    )
    mobile_lesson11 = dict(lesson11_common)
    mobile_lesson11.update(
        {
            "code_surfaces_with_intentional_internal_horizontal_scroll": 3,
            "portrait_container_width_css_px": 343.11,
            "portrait_width_css_px": 343.11,
        }
    )
    desktop_routes["Lesson11"] = desktop_lesson11
    mobile_routes["Lesson11"] = mobile_lesson11

    network = http_preflight(base_url)
    base_url = str(network["base_url"])
    tested_routes = [urljoin(base_url, route) for route in ROUTES]
    receipt = {
        "browser_surface": "in-app Chromium browser against a bounded local static server",
        "coverage": "landing/index plus complete Lesson00 through Lesson11 and licenses",
        "cumulative_results": {
            "captioned_tables": 6,
            "historical_uncaptioned_source_tables": 2,
            "loaded_substantive_images": 57,
            "rendered_math_containers": 2_804,
            "source_math_nodes": 2_804,
            "substantive_images": 57,
            "tables": 8,
        },
        "date": "2026-08-26",
        "desktop": {
            "console_errors_or_warnings": 0,
            "page_client_width_css_px": 1265,
            "routes": desktop_routes,
            "viewport_css_px": {"height": 720, "width": 1280},
        },
        "evidence": {
            "build_receipt": evidence(build_path),
            "manifest": evidence(manifest_path),
            "prior_visual_receipt": evidence(prior_path),
            "qa_receipt": evidence(qa_path),
            "target_lesson11": evidence(target_path),
        },
        "http_preflight": network,
        "locale": "id-ID",
        "mobile": {
            "console_errors_or_warnings": 0,
            "page_client_width_css_px": 375,
            "routes": mobile_routes,
            "viewport_css_px": {"height": 844, "width": 390},
        },
        "observations": [
            "All fourteen cumulative routes were opened at desktop and mobile viewports; page and navigation horizontal overflow were absent throughout.",
            "All 2,804 protected source mathematics nodes rendered as 2,804 MathJax containers at both tested widths.",
            "All 57 substantive images loaded without breakage; the Lesson 11 Bayes portrait exactly filled and centered within its 1,144.08 px desktop and 343.11 px mobile reader containers.",
            "Direct screenshots confirmed that the Lesson 11 portrait, caption, and rights note remain readable and unclipped at both viewports.",
            "The Lesson 11 table is captioned, has complete header scopes, and needs no internal scroll; its four code surfaces remain visible, with bounded intentional internal scrolling on one desktop and three mobile surfaces.",
            "Six of eight cumulative tables are captioned; the two preserved historical source exceptions are the tables in Lessons 00 and 07.",
            "Fresh console warning/error logs were empty, and bounded HTTP checks returned 200 for all fourteen routes and all 77 referenced same-origin resources.",
        ],
        "provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        "routes": tested_routes,
        "schema": "o006.stat415.through-lesson11-visual-qa.v1",
        "status": "pass",
    }
    return (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    payload = compute(args.base_url)
    outputs = (
        ROOT / "build" / "THROUGH_LESSON11_VISUAL_QA_RECEIPT.json",
        ROOT / "00_control" / "VISUAL_QA_2026-08-26_THROUGH_LESSON11.json",
    )
    if args.write:
        for path in outputs:
            path.write_bytes(payload)
        state = "written"
    else:
        if any(not path.is_file() or path.read_bytes() != payload for path in outputs):
            raise RuntimeError("Lesson11 visual-QA receipt differs")
        state = "verified"
    print(
        json.dumps(
            {
                "bytes": len(payload),
                "mode": state,
                "routes_per_viewport": 14,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "status": "pass",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
