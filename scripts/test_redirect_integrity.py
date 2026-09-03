#!/usr/bin/env python3
"""Regression checks for redirect chains that can end on a real local page."""

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
REDIRECT_FILES = (
    ROOT / "export/manual-redirects.json",
    WWW / "vercel.json",
)


def normalise(value):
    path = urlsplit(value).path if value.startswith(("http://", "https://")) else value
    return path.rstrip("/") or "/"


def local_pages():
    pages = set()
    for index in WWW.rglob("index.html"):
        if index.parts[-2] in {"wp-content", "wp-includes"}:
            continue
        relative = index.parent.relative_to(WWW).as_posix()
        pages.add("/" + relative if relative != "." else "/")
    return pages


def redirect_map(path):
    payload = json.loads(path.read_text())
    redirects = payload["redirects"] if isinstance(payload, dict) else payload
    result = {}
    for redirect in redirects:
        source = redirect["source"]
        if any(marker in source for marker in (":", "(", "*")):
            continue
        key = normalise(source)
        destination = normalise(redirect["destination"])
        if key in result:
            if result[key] != destination:
                raise AssertionError(f"conflicting destinations for {key} in {path}")
            continue
        result[key] = destination
    return result


def next_path(path, redirects):
    if path in redirects:
        return redirects[path]
    match = re.fullmatch(r"/blog/.+/(?P<slug>[^/]+)", path)
    if match:
        return "/" + match.group("slug")
    return None


def flattenable_chains(redirects, pages):
    chains = []
    for source, first_destination in redirects.items():
        current = first_destination
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
            chains.append((source, first_destination, current))
    return chains


class RedirectIntegrityTests(unittest.TestCase):
    def test_redirects_with_known_live_pages_are_flattened(self):
        pages = local_pages()
        for path in REDIRECT_FILES:
            with self.subTest(path=path):
                chains = flattenable_chains(redirect_map(path), pages)
                self.assertEqual([], chains)

    def test_manual_redirects_are_present_in_deployed_config(self):
        manual = json.loads(REDIRECT_FILES[0].read_text())
        deployed = json.loads(REDIRECT_FILES[1].read_text())["redirects"]
        deployed_pairs = {
            (item["source"], item["destination"])
            for item in deployed
        }
        for item in manual:
            pair = (item["source"], item["destination"])
            with self.subTest(source=item["source"]):
                self.assertIn(pair, deployed_pairs)


if __name__ == "__main__":
    unittest.main()
