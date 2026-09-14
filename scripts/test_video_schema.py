#!/usr/bin/env python3
"""Verify that every VideoObject has the fields Google requires."""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_RE = re.compile(
    r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)
REQUIRED_FIELDS = ("name", "uploadDate", "description", "thumbnailUrl")


def walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)


class VideoSchemaTest(unittest.TestCase):
    def test_family_friendly_values_are_boolean(self):
        paths = [
            ROOT / "www/win-big-clients/index.html",
            ROOT / "export/reference/win-big-clients.html"
        ]
        failures = []
        checked = 0
        for path in paths:
            for raw in SCRIPT_RE.findall(path.read_text(encoding="utf-8")):
                for item in walk_json(json.loads(raw)):
                    if "isFamilyFriendly" in item:
                        checked += 1
                        if type(item["isFamilyFriendly"]) is not bool:
                            failures.append(
                                f"{path.relative_to(ROOT)}: {item.get('@id')} "
                                f"isFamilyFriendly must be Boolean"
                            )
        self.assertGreater(checked, 0, "No isFamilyFriendly properties detected")
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_video_objects_have_google_fields(self):
        failures = []

        for path in (ROOT / "www").rglob("*.html"):
            html = path.read_text(encoding="utf-8")
            for raw_json in SCRIPT_RE.findall(html):
                data = json.loads(raw_json)
                for item in walk_json(data):
                    schema_type = item.get("@type")
                    types = schema_type if isinstance(schema_type, list) else [schema_type]
                    if "VideoObject" not in types:
                        continue
                    missing = [field for field in REQUIRED_FIELDS if not item.get(field)]
                    if missing:
                        failures.append(
                            f"{path.relative_to(ROOT)}: {item.get('@id', 'VideoObject')} "
                            f"missing {', '.join(missing)}"
                        )

        self.assertEqual([], failures, "\n" + "\n".join(failures))

if __name__ == "__main__":
    unittest.main()
