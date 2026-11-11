#!/usr/bin/env python3
"""Resolve ONLY unambiguous sitemap/search conflicts in an existing Git merge.

Never starts, commits, pushes or completes a merge. Conflicting changes to the
same URL, malformed indexes, and conflicts outside the allowlist need review.
Run after merging the latest target branch into an article branch.
"""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ALLOWED = {"www/post-sitemap.xml", "www/search-index.json"}
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)
MISSING = object()


def merge_records(base, ours, theirs):
    """Three-way merge by URL, including deletions; never guess same-URL intent."""
    result = {}
    for key in dict.fromkeys([*ours, *theirs, *base]):
        b, o, t = (rows.get(key, MISSING) for rows in (base, ours, theirs))
        if o == t:
            chosen = o
        elif o == b:
            chosen = t
        elif t == b:
            chosen = o
        else:
            raise ValueError(f"conflicting edits for URL {key}")
        if chosen is not MISSING:
            result[key] = chosen
    return result


def search_rows(text):
    rows = json.loads(text)
    if not isinstance(rows, list):
        raise ValueError("search index must be an array")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("u"), str) or not row["u"].startswith("/"):
            raise ValueError("invalid search index entry")
        if row["u"] in result:
            raise ValueError(f"duplicate search URL {row['u']}")
        result[row["u"]] = row
    return result


def sitemap_rows(text):
    root = ET.fromstring(text)
    if root.tag != f"{{{NS}}}urlset":
        raise ValueError("expected sitemap urlset")
    result = {}
    for node in root:
        if node.tag != f"{{{NS}}}url":
            raise ValueError("unexpected sitemap child")
        locs = node.findall(f"{{{NS}}}loc")
        if len(locs) != 1 or not locs[0].text:
            raise ValueError("sitemap URL needs exactly one loc")
        key = locs[0].text
        if key in result:
            raise ValueError(f"duplicate sitemap URL {key}")
        # Ignore indentation, but preserve every element/attribute/value.
        for child in node.iter():
            child.tail = None
            if child.text is not None and not child.text.strip():
                child.text = None
        result[key] = ET.tostring(node, encoding="unicode")
    return root.attrib, result


def reconcile(path, base, ours, theirs):
    if path == "www/search-index.json":
        merged = merge_records(*(search_rows(text) for text in (base, ours, theirs)))
        return json.dumps(list(merged.values()), ensure_ascii=False, separators=(",", ":"))
    if path == "www/post-sitemap.xml":
        parsed = [sitemap_rows(text) for text in (base, ours, theirs)]
        if not all(item[0] == parsed[0][0] for item in parsed):
            raise ValueError("sitemap root attributes changed; review required")
        merged = merge_records(*(item[1] for item in parsed))
        root = ET.Element(f"{{{NS}}}urlset", parsed[0][0])
        root.extend(ET.fromstring(value) for value in merged.values())
        ET.indent(root, space="  ")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + '\n'
    raise ValueError(f"not an allowed generated index: {path}")


def git(*args, cwd=None):
    return subprocess.check_output(["git", *args], cwd=cwd)


def resolve_merge(cwd=None):
    root = Path(git("rev-parse", "--show-toplevel", cwd=cwd).decode().strip())
    # A rebase/cherry-pick has different ours/theirs semantics; do not guess.
    merge_head = git("rev-parse", "--git-path", "MERGE_HEAD", cwd=root).decode().strip()
    if not (root / merge_head).exists():
        raise ValueError("no merge in progress; merge the target branch first")
    paths = {p.decode() for p in git("diff", "--name-only", "--diff-filter=U", "-z", cwd=root).split(b"\0") if p}
    if not paths:
        return []
    if paths - ALLOWED:
        raise ValueError("non-index conflicts need review: " + ", ".join(sorted(paths - ALLOWED)))
    outputs = {}
    for path in sorted(paths):
        if (root / path).is_symlink():
            raise ValueError(f"refusing symlink: {path}")
        stages = git("ls-files", "-u", "--", path, cwd=root).decode().splitlines()
        if len(stages) != 3 or any(not line.startswith("100644 ") for line in stages):
            raise ValueError(f"expected three regular-file stages: {path}")
        outputs[path] = reconcile(path, *(git("show", f":{stage}:{path}", cwd=root).decode() for stage in (1, 2, 3)))
    # Validate every conflict before modifying any worktree file or index entry.
    for path, text in outputs.items():
        (root / path).write_text(text, encoding="utf-8")
    git("add", "--", *outputs, cwd=root)
    return list(outputs)


def main():
    try:
        resolved = resolve_merge()
    except (ValueError, ET.ParseError, subprocess.CalledProcessError) as exc:
        raise SystemExit(f"reconcile_publish_indexes: {exc}")
    print(json.dumps({"resolved": resolved, "committed": False, "pushed": False}))


if __name__ == "__main__":
    main()
