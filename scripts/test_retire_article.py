#!/usr/bin/env python3
"""Tests for the article retirement helper."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import retire_article


class RetireSourceTests(unittest.TestCase):
    def test_removes_all_existing_managed_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            (source_dir / "old.json").write_text("{}", encoding="utf-8")
            (source_dir / "old.body.html").write_text("<p>Old</p>", encoding="utf-8")
            with mock.patch.object(retire_article, "BLOG_SYSTEM", source_dir), mock.patch.object(
                retire_article.subprocess, "run"
            ) as run:
                self.assertEqual(retire_article.retire_sources("old", check=False), 2)

        run.assert_called_once()
        command = run.call_args.args[0]
        self.assertEqual(command[:5], ["git", "rm", "-q", "--", str(source_dir / "old.json")])
        self.assertEqual(command[5], str(source_dir / "old.body.html"))
        self.assertTrue(run.call_args.kwargs["check"])

    def test_check_mode_reports_sources_without_deleting(self):
        with tempfile.TemporaryDirectory() as tmp:
            source_dir = Path(tmp)
            (source_dir / "old.json").write_text("{}", encoding="utf-8")
            with mock.patch.object(retire_article, "BLOG_SYSTEM", source_dir), mock.patch.object(
                retire_article.subprocess, "run"
            ) as run:
                self.assertEqual(retire_article.retire_sources("old", check=True), 1)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
