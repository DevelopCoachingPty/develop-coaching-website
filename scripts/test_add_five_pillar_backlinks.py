import tempfile
import unittest
from collections import Counter
from pathlib import Path

from scripts.add_five_pillar_backlinks import TARGETS, add_backlink, apply_targets


class AddFivePillarBacklinksTests(unittest.TestCase):
    def test_exact_verified_target_set(self):
        self.assertEqual(len(TARGETS), 18)
        self.assertEqual(
            Counter(TARGETS.values()),
            {"plan": 3, "attract": 4, "convert": 3, "deliver": 4, "scale": 4},
        )

    def test_inserts_once_before_main_and_preserves_head_casing(self):
        html = "<html><head></HEAD><body><main><p>Article</p></main></body></html>"
        result = add_backlink(html, "plan")
        self.assertIn("</HEAD>", result)
        self.assertLess(result.index('data-dc-pillar-backlink="plan"'), result.index("</main>"))
        self.assertEqual(result.count('id="dc-pillar-backlink-style"'), 1)
        self.assertEqual(result.count('href="/5-pillars-free-trainings/plan/"'), 1)
        self.assertEqual(add_backlink(result, "plan"), result)

    def test_uses_book_award_or_footer_as_fallback(self):
        book_html = '<html><head></head><body><section class="dc-book-award"></section></body></html>'
        footer_html = "<html><head></head><body><footer></footer></body></html>"
        book_result = add_backlink(book_html, "attract")
        footer_result = add_backlink(footer_html, "deliver")
        self.assertLess(book_result.index("dc-pillar-backlink"), book_result.index("dc-book-award"))
        self.assertLess(footer_result.index("dc-pillar-backlink"), footer_result.index("<footer"))

    def test_existing_markup_is_refreshed_without_duplication(self):
        html = "<html><head></head><body><main>Article</main></body></html>"
        first = add_backlink(html, "scale")
        stale = first.replace("Continue with the Scale pillar", "Old heading")
        refreshed = add_backlink(stale, "scale")
        self.assertIn("Continue with the Scale pillar", refreshed)
        self.assertNotIn("Old heading", refreshed)
        self.assertEqual(refreshed.count('data-dc-pillar-backlink="scale"'), 1)

    def test_apply_is_idempotent_for_all_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = "<html><head></head><body><main>Article</main></body></html>"
            for relative_path in TARGETS:
                path = root / relative_path / "index.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")
            self.assertEqual(apply_targets(root), 18)
            self.assertEqual(apply_targets(root), 0)
            self.assertEqual(apply_targets(root, check=True), 0)


if __name__ == "__main__":
    unittest.main()
