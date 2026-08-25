import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.modernise_footer import modernise_footer


ROOT = Path(__file__).resolve().parents[1]


class RenderFivePillarsHubTests(unittest.TestCase):
    def test_renderer_removes_shared_footer_added_earlier_in_build(self):
        legacy = """<html><head></head><body class="page">
<main><p>Legacy hub</p></main>
<footer data-elementor-id="9008" class="elementor-location-footer">Legacy footer</footer>
</body></html>"""
        modernised = modernise_footer(
            legacy, "5-pillars-free-trainings/index.html"
        )
        self.assertIn("data-dc-modern-footer", modernised)

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            hub = temp / "hub.html"
            markup = temp / "markup.html"
            css = temp / "hub.css"
            hub.write_text(modernised, encoding="utf-8")
            markup.write_text(
                '<main class="fp-hub"><section class="fp-book"></section>'
                '<footer class="fp-footer"></footer></main>',
                encoding="utf-8",
            )
            css.write_text(".fp-hub{display:block}", encoding="utf-8")
            script = (
                "const {renderHub}=require("
                + repr(str(ROOT / "scripts/render_five_pillars_hub.js"))
                + ");renderHub({hubPath:"
                + repr(str(hub))
                + ",markupPath:"
                + repr(str(markup))
                + ",cssPath:"
                + repr(str(css))
                + "});"
            )
            subprocess.run(["node", "-e", script], check=True)
            result = hub.read_text(encoding="utf-8")

        self.assertIn('class="fp-footer"', result)
        self.assertNotIn("data-dc-modern-footer", result)
        self.assertNotIn('class="dc-book-award"', result)
        self.assertNotIn('id="dc-modern-footer"', result)


if __name__ == "__main__":
    unittest.main()
