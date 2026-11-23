"""Software pages state that every product is free for Develop Coaching members,
and carry SoftwareApplication JSON-LD that matches the prices rendered on the page.

Run from the repo root: python3 -m unittest scripts.test_software_membership
"""
import json
import re
import unittest
from pathlib import Path

from scripts.install_structured_data import install


ROOT = Path(__file__).resolve().parents[1]
SOFTWARE = ROOT / "www" / "software"
ORG = "https://develop-coaching.com/#organization"
MEMBERSHIP = "/courses/mastermind-course/"

FAQ_Q = "Is the software free for Develop Coaching members?"
FAQ_A = (
    "Yes. CostTracker Pro, FlowBuild, Architect Attractor, SiteSafe Pro, Muster and Jarvis "
    "are included free with Develop Coaching membership. Architect Attractor is UK only. "
    "SiteSafe Pro is not yet available in Australia. Not a member? Use the pricing on this page."
)

# key in the page's UK monthly price table -> product
PRODUCTS = {
    "costtracker-pro": {
        "name": "CostTracker Pro",
        "price_key": "ctp",
        "note": "CostTracker Pro is included free with Develop Coaching membership.",
    },
    "flowbuild": {
        "name": "FlowBuild",
        "price_key": "fb",
        "note": "FlowBuild is included free with Develop Coaching membership.",
    },
    "architect-attractor": {
        "name": "Architect Attractor",
        "price_key": "aa_lite",
        "note": (
            "Architect Attractor is included free with Develop Coaching membership. "
            "UK only. Not yet available in Australia."
        ),
    },
    "sitesafe-pro": {
        "name": "SiteSafe Pro",
        "price_key": "ss",
        "extra_key": "ss_ctp",
        "extra_name": "Already on CostTracker Pro",
        "note": (
            "SiteSafe Pro is included free with Develop Coaching membership. "
            "Not yet available in Australia."
        ),
    },
    "muster": {
        "name": "Muster",
        "price_key": "mu",
        "note": "Muster is included free with Develop Coaching membership.",
    },
    "jarvis": {
        "name": "Jarvis",
        "price_key": "jv",
        "note": "Jarvis is included free with Develop Coaching membership.",
    },
}


def load(path):
    return path.read_text(encoding="utf-8")


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


def uk_monthly(html, key):
    match = re.search(rf"(?<![A-Za-z0-9_]){key}:(\d+)", html)
    if not match:
        raise AssertionError(f"UK monthly price {key} is not in the page")
    return match.group(1)


def offers_of(node):
    offers = node["offers"]
    return offers if isinstance(offers, list) else [offers]


def visible_text(html, class_name):
    match = re.search(
        rf'<p class="{class_name}">(.*?)</p>', html, re.S
    )
    if not match:
        raise AssertionError(f"missing .{class_name}")
    return re.sub(r"<[^>]+>", "", match.group(1))


class SoftwareMembershipCopy(unittest.TestCase):
    def test_hub_states_all_six_are_free_for_members(self):
        html = load(SOFTWARE / "index.html")
        self.assertIn(
            "Included free for Develop Coaching members: all six products come free with "
            f'<a href="{MEMBERSHIP}">Develop Coaching membership</a>. '
            "Not a member? Use the pricing below.",
            html,
        )
        self.assertIn(f"<summary>{FAQ_Q}</summary>", html)
        self.assertEqual(visible_text(html, "member-note"), (
            "Included free for Develop Coaching members: all six products come free with "
            "Develop Coaching membership. Not a member? Use the pricing below."
        ))
        faq_html = re.search(
            rf"<summary>{re.escape(FAQ_Q)}</summary><p>(.*?)</p>", html, re.S
        ).group(1)
        self.assertEqual(re.sub(r"<[^>]+>", "", faq_html), FAQ_A)
        self.assertIn(f'href="{MEMBERSHIP}"', faq_html)

    def test_each_product_page_has_a_one_line_member_note(self):
        for slug, spec in PRODUCTS.items():
            with self.subTest(slug=slug):
                html = load(SOFTWARE / slug / "index.html")
                self.assertEqual(visible_text(html, "member-note"), spec["note"])
                self.assertIn(f'href="{MEMBERSHIP}"', html)
                self.assertNotIn("<details", html)


class SoftwareSchema(unittest.TestCase):
    def test_jsonld_parses_and_matches_visible_uk_monthly_prices(self):
        hub = load(SOFTWARE / "index.html")
        hub_nodes = jsonld_nodes(hub)
        item_list = next(node for node in hub_nodes if node["@type"] == "ItemList")
        self.assertEqual(item_list["numberOfItems"], 6)
        listed = {el["item"]["url"]: el for el in item_list["itemListElement"]}
        self.assertEqual(len(listed), 6)

        faq = next(node for node in hub_nodes if node["@type"] == "FAQPage")
        first = faq["mainEntity"][0]
        self.assertEqual(first["name"], FAQ_Q)
        self.assertEqual(first["acceptedAnswer"]["text"], FAQ_A)
        self.assertNotIn("aggregateRating", json.dumps(hub_nodes))

        for position, (slug, spec) in enumerate(PRODUCTS.items(), start=1):
            with self.subTest(slug=slug):
                html = load(SOFTWARE / slug / "index.html")
                nodes = jsonld_nodes(html)
                apps = [node for node in nodes if node["@type"] == "SoftwareApplication"]
                self.assertEqual(len(apps), 1)
                app = apps[0]
                url = f"https://develop-coaching.com/software/{slug}/"
                self.assertEqual(app["name"], spec["name"])
                self.assertEqual(app["url"], url)
                self.assertEqual(app["@id"], url + "#software")
                self.assertEqual(app["applicationCategory"], "BusinessApplication")
                self.assertEqual(app["operatingSystem"], "Web")
                self.assertIn(f">{app['description']}</p>", html)
                self.assertEqual(app["publisher"], {"@id": ORG})
                self.assertEqual(app["provider"], {"@id": ORG})
                offers = offers_of(app)
                self.assertEqual(offers[0]["price"], uk_monthly(html, spec["price_key"]))
                self.assertEqual(offers[0]["priceCurrency"], "GBP")
                self.assertEqual(offers[0]["priceSpecification"]["unitText"], "month")
                self.assertEqual(offers[0]["priceSpecification"]["referenceQuantity"]["unitCode"], "MON")
                self.assertNotIn("name", offers[0])
                if "extra_key" in spec:
                    self.assertEqual(len(offers), 2)
                    self.assertEqual(offers[1]["name"], spec["extra_name"])
                    self.assertEqual(offers[1]["price"], uk_monthly(html, spec["extra_key"]))
                    self.assertEqual(offers[1]["priceCurrency"], "GBP")
                else:
                    self.assertEqual(len(offers), 1)
                # Tiers that sit in the price script but are not shown on the page.
                shown = {offer["price"] for offer in offers}
                self.assertNotIn(uk_monthly(html, "aa_plus"), shown)
                self.assertNotIn(uk_monthly(html, "aa_pro"), shown)
                self.assertNotIn("aggregateRating", json.dumps(nodes))
                listed_item = listed[url]["item"]
                self.assertEqual(listed[url]["position"], position)
                self.assertEqual(listed[url]["url"], url)
                self.assertEqual(listed_item["name"], app["name"])
                self.assertEqual(offers_of(listed_item), offers)
                # The site installer rewrites only the data-dc-schema block.
                # Software markup has to live beside it, or the next run deletes it.
                self.assertEqual(install(html, path=SOFTWARE / slug / "index.html"), html)
        self.assertEqual(install(hub, path=SOFTWARE / "index.html"), hub)
