#!/usr/bin/env python3
"""developcoaching.com.au retirement redirects stay generated, host-scoped and first."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import comau_redirects as comau  # noqa: E402


class ComauRedirectTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "www/vercel.json").read_text())
        self.rules = comau.build_rules()

    def test_vercel_json_matches_generator(self):
        regenerated = dict(self.config, redirects=comau.apply(self.config["redirects"]))
        self.assertEqual(comau.dump(regenerated), (ROOT / "www/vercel.json").read_text())

    def test_block_is_first_and_catch_all_last(self):
        n = len(self.rules)
        self.assertEqual(n, 277)
        self.assertEqual(self.config["redirects"][:n], self.rules)
        self.assertFalse(any(comau.is_comau(r) for r in self.config["redirects"][n:]))
        self.assertEqual(self.rules[-1]["source"], "/:path(.*)")

    def test_host_condition_never_matches_dot_com(self):
        rx = re.compile("^(?:" + comau.HOST_VALUE + ")$")
        for host in ("develop-coaching.com", "www.develop-coaching.com",
                     "develop-coaching-site.vercel.app"):
            self.assertIsNone(rx.search(host))
            self.assertIsNone(re.search(comau.HOST_VALUE, host))
        for host in ("developcoaching.com.au", "www.developcoaching.com.au"):
            self.assertTrue(rx.match(host))
        for rule in self.rules:
            self.assertEqual(rule["statusCode"], 301)
            self.assertNotIn("permanent", rule)

    def test_bulk_redirects_cannot_fire_on_comau(self):
        bulk = json.loads((ROOT / "www" / self.config["bulkRedirectsPath"]).read_text())
        for rule in bulk:
            host = re.match(r"https://([^/]+)/", rule["source"])
            self.assertIsNotNone(host, rule["source"])
            self.assertIn(host.group(1), ("develop-coaching.com", "www.develop-coaching.com"))

    def test_route_budget(self):
        c = self.config
        self.assertLessEqual(len(c["redirects"]) + len(c.get("rewrites", [])) + len(c.get("headers", [])), 2048)


if __name__ == "__main__":
    unittest.main()
