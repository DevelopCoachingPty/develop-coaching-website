#!/usr/bin/env python3
"""Regression checks for redirect chains that can end on a real local page."""

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WWW = ROOT / "www"
sys.path.insert(0, str(ROOT / "scripts"))
import flatten_redirect_chains as flattener  # noqa: E402

REDIRECT_FILES = (
    ROOT / "export/manual-redirects.json",
    WWW / "vercel.json",
)


def redirect_map(path):
    payload = json.loads(path.read_text())
    redirects = payload["redirects"] if isinstance(payload, dict) else payload
    return flattener.exact_map(redirects)


class RedirectIntegrityTests(unittest.TestCase):
    def test_external_destinations_stay_external(self):
        external = "https://partner.example/path/?campaign=seo"
        self.assertEqual(external, flattener.normalise(external))
        self.assertEqual(
            {},
            flattener.flattenable({"/partner": external}, {"/"}),
        )

    def test_blog_archive_routing_contract_is_current(self):
        for path in REDIRECT_FILES:
            payload = json.loads(path.read_text())
            redirects = payload["redirects"] if isinstance(payload, dict) else payload
            with self.subTest(path=path):
                flattener.require_routing_contract(redirects)

    def test_redirects_with_known_live_pages_are_flattened(self):
        pages = flattener.local_pages()
        for path in REDIRECT_FILES:
            with self.subTest(path=path):
                replacements = flattener.flattenable(redirect_map(path), pages)
                self.assertEqual({}, replacements)

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
