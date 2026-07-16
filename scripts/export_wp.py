#!/usr/bin/env python3
"""Export all public content from the Develop Coaching WordPress site via the REST API.

Saves one JSON file per post type into export/content/<type>.json, and a
combined manifest with slugs/URLs for cross-checking against the sitemaps.
Read-only: only GET requests against the public API.
"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "https://develop-coaching.com/wp-json/wp/v2"
# rest_base values discovered from /wp-json/wp/v2/types
TYPES = [
    "posts",
    "pages",
    "courses",
    "podcast",
    "podcast-transcript",
    "video",
    "webinars",
    "win_big_clients",
    "media",
]
OUT_DIR = "export/content"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dc-export/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        total_pages = int(r.headers.get("X-WP-TotalPages", "1"))
        return json.load(r), total_pages


def export_type(rest_base):
    items = []
    page = 1
    while True:
        url = f"{BASE}/{rest_base}?per_page=100&page={page}&context=view"
        try:
            batch, total_pages = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 400 and page > 1:
                break  # past the last page
            print(f"  ERROR {rest_base} page {page}: HTTP {e.code}")
            return items, False
        items.extend(batch)
        if page >= total_pages:
            break
        page += 1
        time.sleep(0.3)
    return items, True


def main():
    manifest = {}
    for t in TYPES:
        print(f"Exporting {t}...")
        items, ok = export_type(t)
        with open(f"{OUT_DIR}/{t}.json", "w") as f:
            json.dump(items, f, indent=1)
        manifest[t] = {
            "count": len(items),
            "ok": ok,
            "links": [i.get("link") for i in items if isinstance(i, dict)],
        }
        print(f"  {len(items)} items")
    with open(f"{OUT_DIR}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=1)
    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
