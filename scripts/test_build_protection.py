"""A snapshot rebuild must not delete or overwrite hand-written pages.

The fixture is a temporary site. The real www/ tree is never the output
directory, and the test process changes to the temp directory before
building so a relative www/ path cannot land in the repo.

Run from the repo root: python3 -m unittest scripts.test_build_protection
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site  # noqa: E402


EXPECTED_PROTECTED = (
    "software/index.html",
    "software/costtracker-pro/index.html",
    "software/flowbuild/index.html",
    "software/architect-attractor/index.html",
    "software/sitesafe-pro/index.html",
    "software/muster/index.html",
    "software/jarvis/index.html",
)

KEPT_BESIDE_PAGES = (
    "search/index.html",
    "wp-content/plugins/demo/index.html",
    "feeds/podcast.xml",
    "software/assets/software.css",
)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tree_state(root: Path) -> dict:
    found = {}
    for path in root.rglob("*"):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            found[rel] = (path.read_bytes(), path.stat().st_mtime_ns)
    return found


def marker(rel: str) -> str:
    return f"HANDWRITTEN {rel}\n"


def snapshot_html(token: str) -> str:
    return f"<html><head><title>{token}</title></head><body>{token}</body></html>"


class ProtectedListTests(unittest.TestCase):
    def test_list_is_the_software_hub_and_six_products(self):
        self.assertEqual(build_site.PROTECTED_PAGES, EXPECTED_PROTECTED)

    def test_snapshot_names_map_to_the_protected_paths(self):
        self.assertEqual(build_site.page_relpath("__home.html"), "index.html")
        self.assertEqual(build_site.page_relpath("software.html"), "software/index.html")
        self.assertEqual(
            build_site.page_relpath("software__costtracker-pro.html"),
            "software/costtracker-pro/index.html",
        )
        self.assertIn(
            build_site.page_relpath("software.html"),
            build_site.PROTECTED_PAGES,
        )
        self.assertIn(
            build_site.page_relpath("software__jarvis.html"),
            build_site.PROTECTED_PAGES,
        )


class RebuildProtectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.real_bytes = {
            rel: (ROOT / "www" / rel).read_bytes() for rel in EXPECTED_PROTECTED
        }

    @classmethod
    def tearDownClass(cls):
        for rel, data in cls.real_bytes.items():
            current = (ROOT / "www" / rel).read_bytes()
            if current != data:
                raise AssertionError(f"real www page changed: {rel}")

    def make_site(self, tmp: Path, unexpected: bool) -> tuple:
        ref = tmp / "ref"
        out = tmp / "site-out"
        write(ref / "__home.html", snapshot_html("SNAPSHOT-HOME"))
        write(ref / "about.html", snapshot_html("SNAPSHOT-ABOUT"))
        write(ref / "software.html", snapshot_html("SNAPSHOT-SOFTWARE"))
        write(
            ref / "software__costtracker-pro.html",
            snapshot_html("SNAPSHOT-CTP"),
        )
        for rel in EXPECTED_PROTECTED:
            write(out / rel, marker(rel))
        write(out / "about/index.html", "OLD-ABOUT\n")
        write(out / "index.html", "OLD-HOME\n")
        write(out / "search/index.html", "SEARCH-TOOL\n")
        write(out / "wp-content/plugins/demo/index.html", "KEEP-WP\n")
        write(out / "feeds/podcast.xml", "<rss>KEEP</rss>\n")
        write(out / "software/assets/software.css", "KEEP-CSS\n")
        write(out / "vercel.json", '{"old": true}\n')
        if unexpected:
            write(out / "extra-hand/index.html", "HAND-EXTRA\n")
            write(out / "software/not-a-product/index.html", "NOT-A-PRODUCT\n")
        self.assertNotEqual(out.resolve(), (ROOT / "www").resolve())
        self.assertFalse(str(out.resolve()).startswith(str((ROOT / "www").resolve()) + os.sep))
        return ref, out

    def run_build(self, out: Path, ref: Path, argv) -> str:
        stdout = io.StringIO()
        previous = os.getcwd()
        os.chdir(out.parent)
        try:
            with mock.patch.object(build_site, "OUT", str(out)), mock.patch.object(
                build_site, "REF", str(ref)
            ), contextlib.redirect_stdout(stdout):
                build_site.main(list(argv))
        finally:
            os.chdir(previous)
        self.assertFalse((out.parent / "www").exists())
        for rel, data in self.real_bytes.items():
            self.assertEqual((ROOT / "www" / rel).read_bytes(), data, rel)
        return stdout.getvalue()

    def test_guard_stops_before_deleting_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref, out = self.make_site(Path(tmp), unexpected=True)
            before = tree_state(out)
            with self.assertRaises(SystemExit) as caught:
                self.run_build(out, ref, [])
            message = str(caught.exception)
            listed = [
                line.strip() for line in message.splitlines() if line.startswith("  ")
            ]
            self.assertEqual(
                listed,
                ["extra-hand/index.html", "software/not-a-product/index.html"],
            )
            self.assertIn("Nothing was changed", message)
            self.assertIn("--allow-delete", message)
            for rel in EXPECTED_PROTECTED:
                self.assertNotIn(rel, listed)
            self.assertEqual(tree_state(out), before)
            self.assertEqual((out / "about/index.html").read_text(encoding="utf-8"), "OLD-ABOUT\n")
            self.assertEqual((out / "vercel.json").read_text(encoding="utf-8"), '{"old": true}\n')

    def test_protected_pages_survive_a_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref, out = self.make_site(Path(tmp), unexpected=False)
            before = tree_state(out)
            output = self.run_build(out, ref, [])
            after = tree_state(out)
            for rel in EXPECTED_PROTECTED + KEPT_BESIDE_PAGES:
                self.assertEqual(after[rel], before[rel], rel)
            for rel in EXPECTED_PROTECTED:
                self.assertIn(rel, output)
            about = after["about/index.html"][0]
            home = after["index.html"][0]
            self.assertIn(b"SNAPSHOT-ABOUT", about)
            self.assertIn(b"data-preview-guard", about)
            self.assertIn(b"SNAPSHOT-HOME", home)
            self.assertNotEqual(about, before["about/index.html"][0])
            hub = after["software/index.html"][0]
            product = after["software/costtracker-pro/index.html"][0]
            self.assertNotIn(b"SNAPSHOT-SOFTWARE", hub)
            self.assertNotIn(b"SNAPSHOT-CTP", product)
            self.assertNotIn(b"data-preview-guard", hub)
            vercel = json.loads(after["vercel.json"][0])
            self.assertTrue(vercel["trailingSlash"])
            self.assertNotEqual(after["vercel.json"][0], before["vercel.json"][0])
            self.assertNotIn("extra-hand/index.html", after)

    def test_allow_delete_removes_unknown_pages_and_keeps_protected_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref, out = self.make_site(Path(tmp), unexpected=True)
            before = tree_state(out)
            self.run_build(out, ref, ["--allow-delete"])
            after = tree_state(out)
            self.assertNotIn("extra-hand/index.html", after)
            self.assertNotIn("software/not-a-product/index.html", after)
            for rel in EXPECTED_PROTECTED + KEPT_BESIDE_PAGES:
                self.assertEqual(after[rel], before[rel], rel)
            self.assertIn(b"SNAPSHOT-ABOUT", after["about/index.html"][0])
            self.assertNotIn(b"SNAPSHOT-SOFTWARE", after["software/index.html"][0])
            self.assertFalse((out / "extra-hand/index.html").exists())

    def test_snapshot_does_not_create_a_missing_protected_page(self):
        with tempfile.TemporaryDirectory() as tmp:
            ref, out = self.make_site(Path(tmp), unexpected=False)
            hub = out / "software/index.html"
            hub.unlink()
            before_product = (out / "software/jarvis/index.html").read_bytes()
            self.run_build(out, ref, [])
            self.assertFalse(hub.exists())
            self.assertEqual(
                (out / "software/jarvis/index.html").read_bytes(),
                before_product,
            )
            self.assertIn(b"SNAPSHOT-ABOUT", (out / "about/index.html").read_bytes())
            written = b"".join(data for data, _mtime in tree_state(out).values())
            self.assertIn(b"SNAPSHOT-SOFTWARE", (ref / "software.html").read_bytes())
            self.assertNotIn(b"SNAPSHOT-SOFTWARE", written)


if __name__ == "__main__":
    unittest.main()
