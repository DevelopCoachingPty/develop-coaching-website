#!/usr/bin/env python3
"""Validate breadcrumb ordering, including nested legacy JSON-LD graphs."""

import json
import unittest

from test_video_schema import ROOT, SCRIPT_RE, walk_json


class BreadcrumbSchemaTest(unittest.TestCase):
    def test_breadcrumb_positions(self):
        failures = []
        count = 0
        paths = sorted((ROOT / "www").rglob("*.html")) + [
            ROOT / "export/reference/podcast__how-4d-tech-can-improve-your-delivery.html"
        ]
        for path in paths:
            page_count = 0
            for raw in SCRIPT_RE.findall(path.read_text(encoding="utf-8")):
                for node in walk_json(json.loads(raw)):
                    types = node.get("@type", [])
                    types = [types] if isinstance(types, str) else types
                    if "BreadcrumbList" not in types:
                        continue
                    count += 1
                    page_count += 1
                    items = node.get("itemListElement")
                    label = f"{path.relative_to(ROOT)} breadcrumb {page_count}"
                    if not isinstance(items, list) or not items:
                        failures.append(f"{label}: missing breadcrumb items")
                        continue
                    for expected, item in enumerate(items, 1):
                        value = item.get("position") if isinstance(item, dict) else None
                        valid = type(value) is int or (
                            isinstance(value, str) and value.isascii() and value.isdigit()
                        )
                        if not valid or int(value) != expected:
                            failures.append(
                                f"{label} item {expected}: position {value!r}, expected {expected}"
                            )
        self.assertGreater(count, 0, "No breadcrumbs detected")
        self.assertEqual([], failures, "\n" + "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
