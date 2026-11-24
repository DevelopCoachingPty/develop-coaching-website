"""The member-software differentiator is visible, in the FAQs, and on the
Organization. Reinstalling structured data must not drop it.

Run from the repo root: python3 -m unittest scripts.test_software_differentiator
"""
import json
import re
import unittest
from pathlib import Path

from scripts.install_structured_data import (
    ORG_DESCRIPTION, ORG_ID, ROOT, install, is_page,
)


WWW = ROOT / "www"
ORG = ORG_ID

LINE = (
    "The only construction business coaching that includes "
    "six pieces of software free for members: CostTracker Pro, FlowBuild, "
    "Architect Attractor, SiteSafe Pro, Muster and Jarvis."
)
# The linked phrase sits inside the sentence. Attributes on the anchor may vary.
LINE_RE = re.compile(
    r"The only construction business coaching that includes "
    r'<a\b[^>]*\bhref="/software/"[^>]*>six pieces of software</a> '
    r"free for members: CostTracker Pro, FlowBuild, Architect Attractor, "
    r"SiteSafe Pro, Muster and Jarvis\."
)
FAQ_Q = "How is Develop Coaching different from other business coaches?"
FAQ_A = (
    "Develop Coaching is the only construction business coaching that includes "
    "six pieces of software free for members: CostTracker Pro, FlowBuild, "
    "Architect Attractor, SiteSafe Pro, Muster and Jarvis. "
    "That software sits alongside coaching built around the Five Pillars: "
    "Plan, Attract, Convert, Deliver and Scale."
)
FAQ_A_RE = re.compile(
    r"Develop Coaching is the only construction business coaching that includes "
    r'<a\b[^>]*\bhref="/software/"[^>]*>six pieces of software</a> '
    r"free for members: CostTracker Pro, FlowBuild, Architect Attractor, "
    r"SiteSafe Pro, Muster and Jarvis\. "
    r"That software sits alongside coaching built around the Five Pillars: "
    r"Plan, Attract, Convert, Deliver and Scale\."
)

VISIBLE = {
    "www/index.html": True,
    "www/courses/mastermind-course/index.html": True,
    "www/about-greg-wilkes/index.html": False,
}


def load(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def jsonld_nodes(html):
    blocks = re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S
    )
    nodes = []
    for block in blocks:
        data = json.loads(block)
        if isinstance(data.get("@graph"), list):
            nodes.extend(data["@graph"])
        else:
            nodes.append(data)
    return nodes


def org_node(nodes):
    for node in nodes:
        if not isinstance(node, dict) or node.get("@id") != ORG:
            continue
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if "Organization" in types:
            return node
    return None


def faq_page(nodes):
    for node in nodes:
        if not isinstance(node, dict):
            continue
        types = node.get("@type")
        types = types if isinstance(types, list) else [types]
        if "FAQPage" in types:
            return node
    return None


class DifferentiatorCopy(unittest.TestCase):
    def test_source_description_is_the_approved_sentence(self):
        self.assertEqual(ORG_DESCRIPTION, LINE)
        self.assertNotIn("\u2014", LINE)
        self.assertNotIn("\u2014", FAQ_A)
        self.assertNotIn("developcoaching.com.au", LINE + FAQ_A)
        self.assertNotIn("VAT", LINE + FAQ_A)

    def test_key_pages_show_the_line_and_link_the_software_page(self):
        for rel, has_faq in VISIBLE.items():
            with self.subTest(rel=rel):
                html = load(rel)
                self.assertRegex(html, LINE_RE)
                self.assertEqual(install(html, path=ROOT / rel), html)
                nodes = jsonld_nodes(html)
                org = org_node(nodes)
                self.assertIsNotNone(org)
                self.assertEqual(org["description"], LINE)
                if has_faq:
                    self.assertRegex(html, FAQ_A_RE)
                    self.assertRegex(html, r">\s*" + re.escape(FAQ_Q) + r"\s*<")
                    faq = faq_page(nodes)
                    self.assertIsNotNone(faq)
                    match = [q for q in faq["mainEntity"] if q.get("name") == FAQ_Q]
                    self.assertEqual(len(match), 1)
                    self.assertEqual(match[0]["acceptedAnswer"]["text"], FAQ_A)
                else:
                    self.assertIsNone(faq_page(nodes))


class OrganizationDescription(unittest.TestCase):
    def test_every_page_org_description_parses_and_survives_reinstall(self):
        pages = [
            path for path in sorted(WWW.rglob("*.html"))
            if "wp-content" not in path.relative_to(WWW).parts
        ]
        self.assertGreater(len(pages), 100)
        checked = 0
        for path in pages:
            html = path.read_text(encoding="utf-8")
            if not is_page(html):
                continue
            nodes = jsonld_nodes(html)
            org = org_node(nodes)
            self.assertIsNotNone(org, str(path))
            self.assertEqual(org["description"], LINE, str(path))
            self.assertEqual(install(html, path=path), html, str(path))
            checked += 1
        self.assertGreater(checked, 100)


if __name__ == "__main__":
    unittest.main()
