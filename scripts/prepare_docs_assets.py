"""Stage repository example images for the Sphinx documentation build."""

from __future__ import annotations

import shutil
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "example"
DESTINATION_DIR = PROJECT_ROOT / "docs" / "_generated" / "examples"

IMAGE_NAMES = [
    "integration-pow-forecast.png",
    "integration-corn-forecast.png",
    "integration-consolidation-profile.png",
    "nws-base-page.png",
    "nws-details-page.png",
    "nws-data-page.png",
    "nws-xml-page.png",
]


def main() -> int:
    source_images = [SOURCE_DIR / image_name for image_name in IMAGE_NAMES]
    missing_images = [image.name for image in source_images if not image.is_file()]
    if missing_images:
        raise SystemExit(f"Missing documentation images: {', '.join(missing_images)}")

    DESTINATION_DIR.mkdir(parents=True, exist_ok=True)
    source_names = {image.name for image in source_images}

    for stale_image in DESTINATION_DIR.glob("*.png"):
        if stale_image.name not in source_names:
            stale_image.unlink()

    for source_image in source_images:
        shutil.copy2(source_image, DESTINATION_DIR / source_image.name)

    print(f"Staged {len(source_images)} example images for Sphinx.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
