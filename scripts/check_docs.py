"""Acceptance checks for the built Sphinx documentation site."""

from __future__ import annotations

import re
import sys
from html import unescape
from pathlib import Path


EXPECTED_PAGES = {
    "index.html": "Ullr's Secret documentation",
    "installation.html": "Install from PyPI",
    "getting-started.html": "Getting started",
    "model.html": "Effective-temperature model",
    "limitations.html": "Limitations and field use",
    "charts/pow-plot.html": "pow-plot",
    "charts/corn-plot.html": "corn-plot",
    "charts/consolidation-plot.html": "consolidation-plot",
    "importers/openmeteo.html": "Open-Meteo",
    "importers/nws.html": "National Weather Service",
    "importers/era5.html": "ERA5 reanalysis",
    "reference/weather-format.html": "Standard weather JSON",
    "reference/terrain-snotel.html": "Terrain and SNOTEL utilities",
    "reference/python-api.html": "Python API",
}

CJK_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

NAVIGATION_TARGETS = [
    "charts/pow-plot.html",
    "charts/corn-plot.html",
    "charts/consolidation-plot.html",
    "importers/openmeteo.html",
    "importers/nws.html",
    "importers/era5.html",
]

REQUIRED_IMAGE_NAMES = [
    "integration-pow-forecast.png",
    "integration-corn-forecast.png",
    "integration-consolidation-profile.png",
    "nws-base-page.png",
    "nws-details-page.png",
    "nws-data-page.png",
    "nws-xml-page.png",
]

REAL_WORLD_CONTEXT = {
    "charts/pow-plot.html": [
        "March 14, 2026",
        "48.85868, -121.69884",
        "Bagley Lakes",
        "West North",
    ],
    "charts/corn-plot.html": [
        "April 24, 2026",
        "47.45686, -120.94978",
        "Fortune Peak",
        "East Central",
    ],
    "charts/consolidation-plot.html": [
        "April 4, 2025",
        "46.82629, -121.72638",
        "Muir Snowfield",
        "West South",
    ],
}

RETIRED_PAGES = [
    "examples/index.html",
    "examples/integration-tests.html",
    "examples/nws-import.html",
    "examples/corn-trip-planning.html",
    "examples/consolidation-profile.html",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_docs.py BUILT_HTML_DIR", file=sys.stderr)
        return 2

    output_dir = Path(sys.argv[1]).resolve()
    failures: list[str] = []

    for relative_path, required_text in EXPECTED_PAGES.items():
        page = output_dir / relative_path
        if not page.is_file():
            failures.append(f"missing built page: {relative_path}")
            continue
        content = unescape(page.read_text(encoding="utf-8")).replace("’", "'")
        if required_text not in content:
            failures.append(
                f"expected text {required_text!r} not found in {relative_path}"
            )

    project_root = Path(__file__).resolve().parents[1]
    source_dir = project_root / "docs"
    all_source_text = ""
    for source in sorted(source_dir.rglob("*")):
        if source.is_file() and source.suffix in {".rst", ".py"}:
            content = source.read_text(encoding="utf-8")
            all_source_text += content
            if CJK_PATTERN.search(content):
                failures.append(f"non-English CJK text found in {source.relative_to(source_dir)}")

    for image_name in REQUIRED_IMAGE_NAMES:
        if image_name not in all_source_text:
            failures.append(f"required image is not referenced by the docs: {image_name}")
        built_image = output_dir / "_images" / image_name
        if not built_image.is_file():
            failures.append(f"required image is missing from built site: {image_name}")

    for retired_page in RETIRED_PAGES:
        if (output_dir / retired_page).exists():
            failures.append(f"retired worked-example page still exists: {retired_page}")

    for relative_path, required_values in REAL_WORLD_CONTEXT.items():
        page = output_dir / relative_path
        if not page.is_file():
            continue
        content = unescape(page.read_text(encoding="utf-8"))
        for value in required_values:
            if value not in content:
                failures.append(
                    f"real-world context {value!r} not found in {relative_path}"
                )

    retired_markdown = project_root / "example" / "arrange-weekend-bc-destination-n-timeline.md"
    if retired_markdown.exists():
        failures.append("retired example Markdown still exists")

    index_html = (output_dir / "index.html").read_text(encoding="utf-8")
    for target in NAVIGATION_TARGETS:
        if target not in index_html:
            failures.append(f"global table of contents does not expose: {target}")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print(f"Documentation acceptance checks passed ({len(EXPECTED_PAGES)} pages checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
