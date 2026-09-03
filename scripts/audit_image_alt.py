#!/usr/bin/env python3
"""Report image alt-attribute coverage without changing site files."""

import argparse
import json
import os
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


class ImageParser(HTMLParser):
    def __init__(self, source: Path):
        super().__init__(convert_charrefs=True)
        self.source = source
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        values = dict(attrs)
        self.images.append(
            {
                "file": str(self.source),
                "line": self.getpos()[0],
                "src": values.get("src")
                or values.get("data-src")
                or values.get("data-lazy-src")
                or "",
                "alt": values.get("alt") if "alt" in values else None,
                "height": values.get("height"),
                "width": values.get("width"),
                "style": values.get("style", ""),
            }
        )


def is_decorative_meta_pixel(image: dict) -> bool:
    url = urlparse(image["src"].replace("\n", ""))
    return (
        url.netloc == "www.facebook.com"
        and url.path == "/tr"
        and image["height"] == "1"
        and image["width"] == "1"
    )


def audit(root: Path) -> dict:
    images = []
    html_files = sorted(root.rglob("*.html"))
    for path in html_files:
        parser = ImageParser(path)
        parser.feed(path.read_text(encoding="utf-8", errors="replace"))
        images.extend(parser.images)

    missing = [image for image in images if image["alt"] is None]
    decorative = [image for image in missing if is_decorative_meta_pixel(image)]
    unresolved = [image for image in missing if not is_decorative_meta_pixel(image)]
    return {
        "root": str(root),
        "html_files": len(html_files),
        "image_references": len(images),
        "empty_alt_references": sum(image["alt"] == "" for image in images),
        "missing_alt_references": len(missing),
        "missing_alt_confirmed_decorative": len(decorative),
        "missing_alt_unresolved": len(unresolved),
        "missing_details": [
            {
                "file": os.path.relpath(image["file"], root),
                "line": image["line"],
                "src": image["src"],
                "classification": (
                    "decorative_meta_tracking_pixel"
                    if is_decorative_meta_pixel(image)
                    else "unresolved"
                ),
            }
            for image in missing
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default="www")
    parser.add_argument("--fail-on-missing", action="store_true")
    args = parser.parse_args()
    result = audit(Path(args.root))
    print(json.dumps(result, indent=2))
    return int(args.fail_on_missing and result["missing_alt_references"] > 0)


if __name__ == "__main__":
    raise SystemExit(main())
