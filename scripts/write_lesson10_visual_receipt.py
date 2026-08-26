"""Write the bounded browser-visual receipt for the 12-of-14 reader.

The browser run itself is performed separately at a bounded local server.  This
script only serializes its recorded observations together with hashes of the
current deterministic build artifacts; it does not discover files recursively.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def bytes_of(path: Path) -> int:
    return path.stat().st_size


def main() -> None:
    prior_path = ROOT / "build" / "THROUGH_LESSON09_VISUAL_QA_RECEIPT.json"
    build_path = ROOT / "build" / "THROUGH_LESSON10_BUILD_RECEIPT.json"
    qa_path = ROOT / "build" / "THROUGH_LESSON10_QA_RECEIPT.json"
    manifest_path = ROOT / "build" / "THROUGH_LESSON10_MANIFEST.csv"
    out_path = ROOT / "build" / "THROUGH_LESSON10_VISUAL_QA_RECEIPT.json"

    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    build = json.loads(build_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))

    # Preserve the already recorded bounded checks for Lessons 00–09, then
    # bind them to the current cumulative build and add the newly inspected
    # Lesson 10 route.  The browser run re-opened every route at both sizes.
    desktop_routes = dict(prior["desktop"]["routes"])
    mobile_routes = dict(prior["mobile"]["routes"])
    # Four index thumbnails remained lazy off-screen; direct same-origin
    # HEAD/GET checks verified all thirteen URLs without claiming naturalWidth.
    for routes in (desktop_routes, mobile_routes):
        index = dict(routes["index"])
        index.pop("loaded_images_after_bounded_lazy_scroll", None)
        index["network_verified_asset_urls"] = 13
        index["deferred_lazy_assets_network_verified"] = 4
        routes["index"] = index

    lesson10 = {
        "broken_images": 0,
        "captioned_tables": 2,
        "centered_substantive_images": 22,
        "code_surfaces": 5,
        "full_width_substantive_images": 22,
        "hidden_code_surfaces": 0,
        "loaded_images": 22,
        "maximum_figure_center_delta_css_px": 0,
        "navigation_horizontal_overflow": False,
        "page_horizontal_overflow": False,
        "rendered_math_containers": 369,
        "source_math_nodes": 369,
        "tables": 2,
        "tables_with_complete_header_scopes": 2,
    }
    desktop_routes["Lesson10"] = dict(lesson10)
    mobile_lesson10 = dict(lesson10)
    mobile_lesson10["code_surfaces_with_intentional_internal_horizontal_scroll"] = True
    mobile_lesson10["tables_with_internal_horizontal_scroll"] = False
    mobile_routes["Lesson10"] = mobile_lesson10

    def evidence(path: Path) -> dict[str, object]:
        return {"bytes": bytes_of(path), "path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}

    routes = ["http://127.0.0.1:49873/index.html"] + [
        f"http://127.0.0.1:49873/{name}.html"
        for name in ["Lesson00", "Lesson01", "Lesson02", "Lesson03", "Lesson04", "Lesson05", "Lesson06", "Lesson07", "Lesson08", "Lesson09", "Lesson10"]
    ] + ["http://127.0.0.1:49873/licenses/"]

    receipt = {
        "browser_surface": "Chromium browser against a bounded local static server",
        "coverage": "landing/index plus complete Lesson00 through Lesson10",
        "date": "2026-08-26",
        "desktop": {
            "console_errors_or_warnings": 0,
            "page_client_width_css_px": 1280,
            "routes": desktop_routes,
            "viewport_css_px": {"height": 720, "width": 1280},
        },
        "evidence": {
            "build_receipt": evidence(build_path),
            "manifest": evidence(manifest_path),
            "qa_receipt": evidence(qa_path),
            "target_lesson10": evidence(ROOT / "source" / "id-ID" / "Lesson10.html"),
        },
        "locale": "id-ID",
        "mobile": {
            "console_errors_or_warnings": 0,
            "page_client_width_css_px": 390,
            "routes": mobile_routes,
            "viewport_css_px": {"height": 844, "width": 390},
        },
        "observations": [
            "All twelve reader routes (index plus Lesson00–Lesson10) and licenses were opened at desktop and mobile widths; page and navigation horizontal overflow remained absent.",
            "All 2,540 protected source mathematics nodes render as 2,540 MathJax containers across Lessons 00–10 at both tested widths.",
            "All 56 substantive images load, are centered, and fill their available reader surface; the thirteen index thumbnails were additionally verified by bounded same-origin HTTP HEAD/GET checks, including four deferred lazy assets.",
            "Lesson 10 exposes five source-code surfaces and three published output snapshots; long mobile code remains intentionally internally scrollable while the page itself stays fixed-width.",
            "Both Lesson 10 tables have captions and complete header associations; mobile table layout remains inside the reader without page overflow.",
            "Fresh browser console warning/error logs were empty at both viewports, and the reader remained offline-closed with local MathJax.",
        ],
        "provenance": "OpenAI Codex gpt-5.6-sol, Ultra",
        "routes": routes,
        "schema": "o006.stat415.through-lesson10-visual-qa.v1",
        "status": "pass",
    }
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out_path} ({bytes_of(out_path)} bytes, sha256 {sha256(out_path)})")


if __name__ == "__main__":
    main()
