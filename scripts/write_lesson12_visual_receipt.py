"""Validate and record browser observations for the complete 14-document reader.

This helper deliberately separates deterministic/static evidence from live
browser observations.  ``working/through_lesson12_visual_observations.template.json``
contains null placeholders for every browser-dependent measurement.  A final
``pass`` receipt can be written only after a separate observations file fills
every required field and the values satisfy this script's finite invariants.

The browser run itself is external to this script.  At receipt time the helper
also replays a bounded HTTP preflight against exactly the landing page,
Lesson00--Lesson12, and the licenses page.  It never recursively discovers
repository files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "working" / "through_lesson12_visual_observations.template.json"
DEFAULT_BASE_URL = "http://127.0.0.1:49874/"
ROUTES = {
    "index": "index.html",
    **{f"Lesson{i:02d}": f"Lesson{i:02d}.html" for i in range(13)},
    "licenses": "licenses/",
}
LOCAL_ROUTE_PATHS = {
    key: ("licenses/index.html" if key == "licenses" else route)
    for key, route in ROUTES.items()
}
VIEWPORTS = {
    "desktop": {"height": 720, "width": 1280},
    "mobile": {"height": 844, "width": 390},
}

# These numbers are frozen from the deterministic 14-of-14 reader DOM.  Byte
# sizes are intentionally included so a rebuilt-but-different surface cannot
# inherit observations from an earlier reader.
EXPECTED_ROUTE_CENSUS = {
    "index": {"bytes": 24_947, "images": 13, "math_nodes": 0, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson00": {"bytes": 80_541, "images": 0, "math_nodes": 331, "pre_nodes": 0, "tables": 1, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson01": {"bytes": 47_621, "images": 5, "math_nodes": 169, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson02": {"bytes": 59_365, "images": 2, "math_nodes": 209, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson03": {"bytes": 102_805, "images": 0, "math_nodes": 440, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson04": {"bytes": 81_439, "images": 1, "math_nodes": 289, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson05": {"bytes": 195_443, "images": 14, "math_nodes": 108, "pre_nodes": 176, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson06": {"bytes": 36_704, "images": 1, "math_nodes": 102, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson07": {"bytes": 74_168, "images": 2, "math_nodes": 148, "pre_nodes": 28, "tables": 1, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson08": {"bytes": 113_297, "images": 4, "math_nodes": 156, "pre_nodes": 28, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson09": {"bytes": 95_364, "images": 10, "math_nodes": 219, "pre_nodes": 0, "tables": 3, "captions": 3, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson10": {"bytes": 153_817, "images": 22, "math_nodes": 369, "pre_nodes": 8, "tables": 2, "captions": 2, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson11": {"bytes": 69_875, "images": 1, "math_nodes": 264, "pre_nodes": 4, "tables": 1, "captions": 1, "iframes": 0, "offline_video_equivalents": 0},
    "Lesson12": {"bytes": 147_382, "images": 10, "math_nodes": 352, "pre_nodes": 1, "tables": 6, "captions": 6, "iframes": 0, "offline_video_equivalents": 3},
    "licenses": {"bytes": 5_247, "images": 0, "math_nodes": 0, "pre_nodes": 0, "tables": 0, "captions": 0, "iframes": 0, "offline_video_equivalents": 0},
}
EXPECTED_LOCAL_RESOURCES = 86
EXPECTED_CUMULATIVE = {
    "captioned_tables": 12,
    "historical_uncaptioned_source_tables": 2,
    "rendered_math_containers": 3_156,
    "source_math_nodes": 3_156,
    "substantive_images": 67,
    "tables": 14,
}


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


def static_route_census() -> dict[str, dict[str, int]]:
    census: dict[str, dict[str, int]] = {}
    for key, route_path in LOCAL_ROUTE_PATHS.items():
        payload = (ROOT / "build" / "html-id" / route_path).read_bytes()
        soup = BeautifulSoup(payload, "html.parser")
        main = soup.select_one("main#quarto-document-content")
        census[key] = {
            "bytes": len(payload),
            "images": len(main.select("img")) if main is not None else 0,
            "math_nodes": len(main.select(".math")) if main is not None else 0,
            "pre_nodes": len(main.select("pre")) if main is not None else 0,
            "tables": len(main.select("table")) if main is not None else 0,
            "captions": len(main.select("table caption")) if main is not None else 0,
            "iframes": len(main.select("iframe")) if main is not None else 0,
            "offline_video_equivalents": len(main.select("details.offline-video-equivalent")) if main is not None else 0,
        }
    if census != EXPECTED_ROUTE_CENSUS:
        raise RuntimeError(f"14-of-14 static reader census differs: {census}")
    return census


def http_preflight(base_url: str) -> dict[str, object]:
    if not base_url.endswith("/"):
        base_url += "/"
    resources: set[str] = set()
    route_census: dict[str, dict[str, int]] = {}
    for key, route in ROUTES.items():
        url = urljoin(base_url, route)
        with urlopen(Request(url, method="GET"), timeout=10) as response:
            payload = response.read()
            if response.status != 200:
                raise RuntimeError(f"reader route HTTP status differs: {url}: {response.status}")
        soup = BeautifulSoup(payload, "html.parser")
        main = soup.select_one("main#quarto-document-content")
        route_census[key] = {
            "bytes": len(payload),
            "images": len(main.select("img")) if main is not None else 0,
            "math_nodes": len(main.select(".math")) if main is not None else 0,
            "pre_nodes": len(main.select("pre")) if main is not None else 0,
            "tables": len(main.select("table")) if main is not None else 0,
            "captions": len(main.select("table caption")) if main is not None else 0,
            "iframes": len(main.select("iframe")) if main is not None else 0,
            "offline_video_equivalents": len(main.select("details.offline-video-equivalent")) if main is not None else 0,
        }
        for tag, attribute in (("script", "src"), ("img", "src"), ("link", "href")):
            for node in soup.find_all(tag):
                reference = str(node.get(attribute) or "")
                if not reference or reference.startswith(("http://", "https://", "//", "#", "mailto:")):
                    continue
                resource = urljoin(url, reference)
                if urlparse(resource).hostname == urlparse(base_url).hostname:
                    resources.add(quote(resource, safe=":/?=&%#"))
    if route_census != EXPECTED_ROUTE_CENSUS:
        raise RuntimeError(f"14-of-14 HTTP route census differs: {route_census}")
    for resource in sorted(resources):
        with urlopen(Request(resource, method="GET"), timeout=10) as response:
            response.read(1)
            if response.status != 200:
                raise RuntimeError(f"reader resource HTTP status differs: {resource}: {response.status}")
    if len(resources) != EXPECTED_LOCAL_RESOURCES:
        raise RuntimeError(
            f"bounded HTTP resource census differs: {len(resources)} != {EXPECTED_LOCAL_RESOURCES}"
        )
    return {
        "base_url": base_url,
        "missing_resources": 0,
        "referenced_local_resources_http_200": len(resources),
        "route_census": route_census,
        "routes_http_200": len(route_census),
    }


def require_equal(record: dict[str, Any], key: str, expected: Any, where: str) -> None:
    if key not in record:
        raise RuntimeError(f"missing browser observation {where}.{key}")
    if record[key] != expected:
        raise RuntimeError(
            f"browser observation differs at {where}.{key}: {record[key]!r} != {expected!r}"
        )


def require_nonnegative_int(record: dict[str, Any], key: str, where: str) -> int:
    if key not in record or isinstance(record[key], bool) or not isinstance(record[key], int):
        raise RuntimeError(f"{where}.{key} must be an observed integer")
    if record[key] < 0:
        raise RuntimeError(f"{where}.{key} must be nonnegative")
    return record[key]


def route_map(view: dict[str, Any], viewport_name: str) -> dict[str, dict[str, Any]]:
    records = view.get("routes")
    if not isinstance(records, list):
        raise RuntimeError(f"{viewport_name}.routes must be a list")
    mapped: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("route"), str):
            raise RuntimeError(f"{viewport_name}.routes contains a malformed record")
        key = record["route"]
        if key in mapped:
            raise RuntimeError(f"{viewport_name}.routes duplicates {key}")
        mapped[key] = record
    if set(mapped) != set(ROUTES):
        raise RuntimeError(
            f"{viewport_name}.routes differs: {sorted(mapped)} != {sorted(ROUTES)}"
        )
    return mapped


def validate_observations(observations: dict[str, Any]) -> dict[str, Any]:
    if observations.get("schema") != "o006.stat415.through-lesson12-visual-observations.v1":
        raise RuntimeError("browser-observation schema differs")
    if not isinstance(observations.get("browser_surface"), str) or not observations["browser_surface"].strip():
        raise RuntimeError("browser_surface must identify the actual browser used")
    if not isinstance(observations.get("date"), str) or len(observations["date"]) != 10:
        raise RuntimeError("date must be an observed YYYY-MM-DD string")

    validated_views: dict[str, Any] = {}
    for viewport_name, viewport in VIEWPORTS.items():
        view = observations.get(viewport_name)
        if not isinstance(view, dict):
            raise RuntimeError(f"missing {viewport_name} browser observations")
        require_equal(view, "viewport_css_px", viewport, viewport_name)
        client_width = require_nonnegative_int(view, "page_client_width_css_px", viewport_name)
        if not 1 <= client_width <= viewport["width"]:
            raise RuntimeError(f"{viewport_name}.page_client_width_css_px is not credible")
        require_equal(view, "console_errors_or_warnings", 0, viewport_name)
        routes = route_map(view, viewport_name)

        for route_key, expected in EXPECTED_ROUTE_CENSUS.items():
            route = routes[route_key]
            where = f"{viewport_name}.routes[{route_key}]"
            require_equal(route, "source_math_nodes", expected["math_nodes"], where)
            require_equal(route, "rendered_math_containers", expected["math_nodes"], where)
            require_equal(route, "loaded_images", expected["images"], where)
            require_equal(route, "broken_images", 0, where)
            require_equal(route, "tables", expected["tables"], where)
            require_equal(route, "captioned_tables", expected["captions"], where)
            require_equal(route, "code_surfaces", expected["pre_nodes"], where)
            require_equal(route, "external_iframes", 0, where)
            require_equal(
                route,
                "offline_video_equivalents",
                expected["offline_video_equivalents"],
                where,
            )
            require_equal(route, "page_horizontal_overflow", False, where)
            require_equal(route, "navigation_horizontal_overflow", False, where)

        index = routes["index"]
        index_where = f"{viewport_name}.routes[index]"
        require_equal(index, "course_card_images", 13, index_where)
        require_equal(index, "network_verified_asset_urls", 13, index_where)
        natural = require_nonnegative_int(index, "naturally_loaded_course_card_images", index_where)
        deferred = require_nonnegative_int(index, "deferred_lazy_assets_network_verified", index_where)
        if natural + deferred != 13:
            raise RuntimeError(
                f"{index_where}: naturally loaded plus deferred verified images must equal 13"
            )

        lesson12 = routes["Lesson12"]
        lesson12_where = f"{viewport_name}.routes[Lesson12]"
        require_equal(lesson12, "centered_substantive_images", 10, lesson12_where)
        require_equal(lesson12, "full_width_substantive_images", 10, lesson12_where)
        center_delta = lesson12.get("maximum_figure_center_delta_css_px")
        if isinstance(center_delta, bool) or not isinstance(center_delta, (int, float)) or not 0 <= center_delta <= 1:
            raise RuntimeError(
                f"{lesson12_where}.maximum_figure_center_delta_css_px must be observed in [0, 1]"
            )
        require_equal(lesson12, "tables_with_complete_header_scopes", 6, lesson12_where)
        table_scroll = require_nonnegative_int(
            lesson12, "tables_with_internal_horizontal_scroll", lesson12_where
        )
        if table_scroll > 6:
            raise RuntimeError(f"{lesson12_where}: at most six tables can scroll internally")
        code_scroll = require_nonnegative_int(
            lesson12,
            "code_surfaces_with_intentional_internal_horizontal_scroll",
            lesson12_where,
        )
        if code_scroll > 1:
            raise RuntimeError(f"{lesson12_where}: at most one code surface can scroll internally")
        require_equal(lesson12, "hidden_code_surfaces", 0, lesson12_where)
        require_equal(
            lesson12,
            "offline_video_equivalents_expanded_and_inspected",
            3,
            lesson12_where,
        )
        require_equal(
            lesson12,
            "offline_video_equivalents_readable_and_unclipped",
            True,
            lesson12_where,
        )
        validated_views[viewport_name] = {
            **view,
            "routes": {key: routes[key] for key in ROUTES},
        }

    notes = observations.get("observation_notes")
    if not isinstance(notes, list) or not notes or any(
        not isinstance(note, str) or not note.strip() for note in notes
    ):
        raise RuntimeError("observation_notes must contain at least one truthful browser note")
    return {
        "browser_surface": observations["browser_surface"].strip(),
        "date": observations["date"],
        "desktop": validated_views["desktop"],
        "mobile": validated_views["mobile"],
        "observation_notes": notes,
    }


def validate_boundary() -> tuple[Path, Path, Path, Path, Path]:
    static_route_census()
    prior_path = ROOT / "build" / "THROUGH_LESSON11_VISUAL_QA_RECEIPT.json"
    build_path = ROOT / "build" / "THROUGH_LESSON12_BUILD_RECEIPT.json"
    qa_path = ROOT / "build" / "THROUGH_LESSON12_QA_RECEIPT.json"
    manifest_path = ROOT / "build" / "THROUGH_LESSON12_MANIFEST.csv"
    target_path = ROOT / "source" / "id-ID" / "Lesson12.html"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    build = json.loads(build_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    if (
        prior.get("schema") != "o006.stat415.through-lesson11-visual-qa.v1"
        or prior.get("status") != "pass"
        or build.get("schema") != "o006.stat415.through-lesson12-build.v1"
        or build.get("status") != "built"
        or build.get("coverage", {}).get("complete_count") != 14
        or build.get("reader", {}).get("files") != 106
        or build.get("translation_segments") != 4_932
        or build.get("structural_units_normalized") != 6_510
        or build.get("structural_units_target") != 6_498
        or build.get("math_nodes", {}).get("total") != 3_156
        or build.get("offline", {}).get("offline_video_equivalents") != 3
        or qa.get("schema") != "o006.stat415.through-lesson12-qa.v1"
        or qa.get("status") != "passed"
        or qa.get("coverage", {}).get("complete_documents") != 14
    ):
        raise RuntimeError("Lesson12 visual-QA input boundary differs")
    return prior_path, build_path, qa_path, manifest_path, target_path


def compute(observations_path: Path, base_url: str) -> bytes:
    prior_path, build_path, qa_path, manifest_path, target_path = validate_boundary()
    observations = json.loads(observations_path.read_text(encoding="utf-8"))
    validated = validate_observations(observations)
    network = http_preflight(base_url)
    tested_routes = [urljoin(str(network["base_url"]), route) for route in ROUTES.values()]
    receipt = {
        "browser_surface": validated["browser_surface"],
        "coverage": "landing/index plus complete Lesson00 through Lesson12 and licenses",
        "cumulative_results": {
            **EXPECTED_CUMULATIVE,
            "loaded_substantive_images": 67,
        },
        "date": validated["date"],
        "desktop": validated["desktop"],
        "evidence": {
            "browser_observations": evidence(observations_path),
            "build_receipt": evidence(build_path),
            "manifest": evidence(manifest_path),
            "prior_visual_receipt": evidence(prior_path),
            "qa_receipt": evidence(qa_path),
            "target_lesson12": evidence(target_path),
        },
        "http_preflight": network,
        "locale": "id-ID",
        "mobile": validated["mobile"],
        "observations": validated["observation_notes"],
        "provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        "routes": tested_routes,
        "schema": "o006.stat415.through-lesson12-visual-qa.v1",
        "status": "pass",
    }
    return (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def check_template() -> None:
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    if template.get("schema") != "o006.stat415.through-lesson12-visual-observations.v1":
        raise RuntimeError("Lesson12 visual-observation template schema differs")
    if template.get("browser_surface") is not None or template.get("date") is not None:
        raise RuntimeError("template must not assert a browser surface or date")
    for viewport_name, viewport in VIEWPORTS.items():
        view = template.get(viewport_name)
        if not isinstance(view, dict) or view.get("viewport_css_px") != viewport:
            raise RuntimeError(f"template {viewport_name} viewport differs")
        routes = route_map(view, viewport_name)
        for route_key, record in routes.items():
            for key, value in record.items():
                if key != "route" and value is not None:
                    raise RuntimeError(
                        f"template unexpectedly asserts {viewport_name}.{route_key}.{key}"
                    )
    print(
        json.dumps(
            {
                "mode": "template-verified",
                "path": TEMPLATE_PATH.relative_to(ROOT).as_posix(),
                "routes_per_viewport": len(ROUTES),
                "sha256": sha256(TEMPLATE_PATH),
                "status": "not-observed",
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check-template", action="store_true")
    mode.add_argument("--validate-only", action="store_true")
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check-only", action="store_true")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    if args.check_template:
        check_template()
        return
    if args.observations is None:
        parser.error("--observations is required outside --check-template")
    observations_path = args.observations.resolve()
    payload = compute(observations_path, args.base_url)
    outputs = (
        ROOT / "build" / "THROUGH_LESSON12_VISUAL_QA_RECEIPT.json",
        ROOT / "00_control" / "VISUAL_QA_2026-08-26_THROUGH_LESSON12.json",
    )
    if args.write:
        for path in outputs:
            path.write_bytes(payload)
        state = "written"
    elif args.check_only:
        if any(not path.is_file() or path.read_bytes() != payload for path in outputs):
            raise RuntimeError("Lesson12 visual-QA receipt differs")
        state = "verified"
    else:
        state = "validated-not-written"
    print(
        json.dumps(
            {
                "bytes": len(payload),
                "mode": state,
                "routes_per_viewport": len(ROUTES),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "status": "pass",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
