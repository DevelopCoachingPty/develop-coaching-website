#!/usr/bin/env python3
"""Flatten redirect chains whose final destination is a built local page."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
MANUAL = ROOT / "export/manual-redirects.json"
VERCEL = WWW / "vercel.json"
BLOG_ARCHIVE_RULE = (
    "/blog/:path(.+)/:slug([^/]+)",
    "/:slug/",
)


def normalise(value):
    parsed = urlsplit(value)
    if parsed.scheme and parsed.netloc not in {
        "develop-coaching.com",
        "www.develop-coaching.com",
    }:
        return value
    path = parsed.path
    return path.rstrip("/") or "/"


def destination(path):
    return "/" if path == "/" else path + "/"


def local_pages():
    pages = set()
    for index in WWW.rglob("index.html"):
        relative = index.parent.relative_to(WWW).as_posix()
        pages.add("/" + relative if relative != "." else "/")
    return pages


def exact_map(redirects):
    result = {}
    for redirect in redirects:
        source = redirect["source"]
        if any(marker in source for marker in (":", "(", "*")):
            continue
        key = normalise(source)
        result.setdefault(key, normalise(redirect["destination"]))
    return result


def require_routing_contract(redirects):
    configured = {
        (redirect["source"], redirect["destination"])
        for redirect in redirects
    }
    if BLOG_ARCHIVE_RULE not in configured:
        raise ValueError("the blog archive redirect pattern has changed")


def next_path(path, redirects):
    if path in redirects:
        return redirects[path]
    if path.startswith(("http://", "https://")):
        return None
    match = re.fullmatch(r"/blog/.+/(?P<slug>[^/]+)", path)
    if match:
        return "/" + match.group("slug")
    return None


def flattenable(redirects, pages):
    replacements = {}
    for source, first in redirects.items():
        current = first
        seen = {source}
        hops = 1
        while current not in seen:
            seen.add(current)
            following = next_path(current, redirects)
            if following is None:
                break
            current = following
            hops += 1
        if hops > 1 and current in pages:
            replacements[source] = current
    return replacements


def update_redirects(redirects, replacements):
    changed = 0
    matched = set()
    for redirect in redirects:
        source = normalise(redirect["source"])
        if source not in replacements:
            continue
        matched.add(source)
        final = destination(replacements[source])
        if redirect["destination"] != final:
            redirect["destination"] = final
            changed += 1
    return changed, matched


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    manual = json.loads(MANUAL.read_text())
    vercel = json.loads(VERCEL.read_text())
    require_routing_contract(manual)
    require_routing_contract(vercel["redirects"])
    replacements = flattenable(exact_map(manual), local_pages())
    manual_changed, manual_matched = update_redirects(manual, replacements)
    vercel_changed, vercel_matched = update_redirects(vercel["redirects"], replacements)

    missing_manual = replacements.keys() - manual_matched
    missing_vercel = replacements.keys() - vercel_matched
    if missing_manual or missing_vercel:
        raise SystemExit(
            f"missing sources: manual={sorted(missing_manual)}, "
            f"vercel={sorted(missing_vercel)}"
        )

    print(
        f"flattenable routes: {len(replacements)}; "
        f"manual rules changed: {manual_changed}; "
        f"vercel rules changed: {vercel_changed}"
    )
    if not args.write:
        print("dry run only, pass --write to update both redirect files")
        return

    MANUAL.write_text(json.dumps(manual, indent=1) + "\n")
    VERCEL.write_text(json.dumps(vercel, indent=1) + "\n")


if __name__ == "__main__":
    main()
