#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import reconcile_publish_indexes as r


def search(*names):
    return json.dumps([{'u': f'/{n}/', 't': n, 's': '', 'k': 'posts'} for n in names])


def sitemap(*names):
    return f'<urlset xmlns="{r.NS}">' + ''.join(f'<url><loc>https://develop-coaching.com/{n}/</loc><lastmod>2026-11-01</lastmod></url>' for n in names) + '</urlset>'


class ReconcileTests(unittest.TestCase):
    def test_concurrent_articles_preserved_and_idempotent(self):
        for path, make, parse in [('www/search-index.json', search, r.search_rows), ('www/post-sitemap.xml', sitemap, lambda s: r.sitemap_rows(s)[1])]:
            with self.subTest(path=path):
                merged = r.reconcile(path, make('old'), make('old', 'markup'), make('old', 'snagging'))
                self.assertEqual(len(parse(merged)), 3)
                self.assertEqual(r.reconcile(path, merged, merged, merged), merged)
                self.assertIn('markup', merged)
                self.assertIn('snagging', merged)

    def test_three_way_updates_deletes_and_identical_adds(self):
        self.assertEqual(r.merge_records({'a': 1, 'b': 2}, {'a': 3, 'b': 2, 'c': 4}, {'a': 1, 'c': 4}), {'a': 3, 'c': 4})
        for ours, theirs in [({'a': 2}, {'a': 3}), ({}, {'a': 2})]:
            with self.assertRaises(ValueError):
                r.merge_records({'a': 1}, ours, theirs)

    def test_invalid_and_duplicate_inputs_refused(self):
        for bad in ['{}', '[{}]', search('same', 'same')]:
            with self.assertRaises(ValueError):
                r.reconcile('www/search-index.json', search(), bad, search())
        for bad in ['<urlset/>', sitemap('same', 'same')]:
            with self.assertRaises(ValueError):
                r.reconcile('www/post-sitemap.xml', sitemap(), bad, sitemap())
        with self.assertRaises(ValueError):
            r.reconcile('www/index.html', '', '', '')

    def test_real_git_conflict_and_second_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def git(*args, check=True):
                return subprocess.run(['git', *args], cwd=tmp, check=check, capture_output=True, text=True)
            git('init', '-b', 'main')
            git('config', 'user.email', 'test@example.invalid')
            git('config', 'user.name', 'Test')
            (root / 'www').mkdir()
            def write(*names):
                (root / 'www/search-index.json').write_text(search(*names))
                (root / 'www/post-sitemap.xml').write_text(sitemap(*names))
            def commit(msg):
                git('add', 'www/search-index.json', 'www/post-sitemap.xml')
                git('commit', '-m', msg)
            write('old'); commit('base')
            git('checkout', '-b', 'article')
            write('old', 'markup'); commit('article')
            git('checkout', 'main')
            write('old', 'snagging'); commit('concurrent')
            git('checkout', 'article')
            head = git('rev-parse', 'HEAD').stdout
            self.assertNotEqual(git('merge', '--no-commit', 'main', check=False).returncode, 0)
            self.assertEqual(set(r.resolve_merge(tmp)), r.ALLOWED)
            self.assertEqual(r.resolve_merge(tmp), [])
            self.assertEqual(git('rev-parse', 'HEAD').stdout, head)
            self.assertEqual(git('diff', '--name-only', '--diff-filter=U').stdout, '')
            self.assertEqual(len(r.search_rows((root / 'www/search-index.json').read_text())), 3)
            self.assertEqual(len(r.sitemap_rows((root / 'www/post-sitemap.xml').read_text())[1]), 3)

    def test_all_files_validated_before_any_write(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / '.git').mkdir()
            (root / '.git/MERGE_HEAD').write_text('head')
            (root / 'www').mkdir()
            for name in ('post-sitemap.xml', 'search-index.json'):
                (root / 'www' / name).write_text('conflict markers')
            calls = []
            def fake_git(*args, **kwargs):
                calls.append(args)
                if args == ('rev-parse', '--show-toplevel'):
                    return str(root).encode()
                if args[:2] == ('rev-parse', '--git-path'):
                    return b'.git/MERGE_HEAD'
                if args[0] == 'diff':
                    return b'www/post-sitemap.xml\0www/search-index.json\0'
                if args[0] == 'ls-files':
                    return b'100644 abc 1\tfile\n100644 abc 2\tfile\n100644 abc 3\tfile\n'
                if args[0] == 'show':
                    return (sitemap('old') if args[1].endswith('.xml') else 'invalid json').encode()
                self.fail(f'unexpected mutation: {args}')
            with patch.object(r, 'git', fake_git), self.assertRaises(ValueError):
                r.resolve_merge(tmp)
            self.assertEqual((root / 'www/post-sitemap.xml').read_text(), 'conflict markers')
            self.assertFalse(any(call[0] == 'add' for call in calls))

    def test_non_index_conflict_leaves_all_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            def git(*args):
                return subprocess.run(['git', *args], cwd=tmp, capture_output=True)
            git('init', '-b', 'main'); git('config', 'user.email', 'test@example.invalid'); git('config', 'user.name', 'Test')
            p = Path(tmp) / 'page.html'
            p.write_text('base'); git('add', 'page.html'); git('commit', '-m', 'base')
            git('checkout', '-b', 'article'); p.write_text('ours'); git('commit', '-am', 'ours')
            git('checkout', 'main'); p.write_text('theirs'); git('commit', '-am', 'theirs')
            git('checkout', 'article'); git('merge', 'main')
            before = p.read_bytes()
            with self.assertRaisesRegex(ValueError, 'non-index conflicts'):
                r.resolve_merge(tmp)
            self.assertEqual(p.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
