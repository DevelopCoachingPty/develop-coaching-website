#!/usr/bin/env python3
"""developcoaching.com.au retirement redirects (plan v3, 13 Oct 2026).

Single source of truth: export/comau-redirect-map.csv. Generates host-scoped
301 rules that only fire on (www.)developcoaching.com.au and must sit at the
FRONT of vercel.json "redirects" (catch-all /:path(.*) last within the block).

  python3 scripts/comau_redirects.py --check        # exit 1 if www/vercel.json is out of date
  python3 scripts/comau_redirects.py --write        # splice regenerated rules into www/vercel.json
  python3 scripts/comau_redirects.py --out FILE     # write the spliced config elsewhere (for diffing)
"""
import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "export/comau-redirect-map.csv"
VERCEL = ROOT / "www/vercel.json"
HOST_VALUE = "(www\\.)?developcoaching\\.com\\.au"
OLD_HOST = "developcoaching.com.au"
NEW_PREFIX = "https://develop-coaching.com/"


def _source(path):
    if path.endswith("/*"):
        return path[:-2] + "/:path(.*)"
    if path == "/":
        return "/"
    if not path.endswith("/"):
        raise ValueError(f"expected trailing slash: {path}")
    return path[:-1] + "{/}?"


def build_rules(csv_path=CSV):
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    ordered = [r for r in rows if r["match_type"] != "rule"] + [
        r for r in rows if r["match_type"] == "rule"]
    rules = []
    for row in ordered:
        url = urlparse(row["source_url"])
        if url.netloc != OLD_HOST or url.query:
            raise ValueError(f"bad source: {row['source_url']}")
        if not row["target_url"].startswith(NEW_PREFIX):
            raise ValueError(f"bad target: {row['target_url']}")
        rules.append({
            "source": _source(url.path),
            "has": [{"type": "host", "value": HOST_VALUE}],
            "destination": row["target_url"],
            "statusCode": 301,
        })
    sources = [r["source"] for r in rules]
    if len(set(sources)) != len(sources):
        raise ValueError("duplicate sources")
    if sources[-1] != "/:path(.*)":
        raise ValueError("catch-all must be last")
    return rules


def is_comau(rule):
    return any(h.get("type") == "host" and h.get("value") == HOST_VALUE
               for h in rule.get("has", []))


def apply(redirects, csv_path=CSV):
    """Return redirects with the .com.au block (re)placed at the front."""
    return build_rules(csv_path) + [r for r in redirects if not is_comau(r)]


def dump(config):
    return json.dumps(config, indent=1, ensure_ascii=True) + "\n"


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--write", action="store_true")
    g.add_argument("--out")
    a = ap.parse_args()
    current = VERCEL.read_text()
    config = json.loads(current)
    config["redirects"] = apply(config["redirects"])
    text = dump(config)
    if a.check:
        ok = text == current
        print("vercel.json comau block up to date" if ok else "vercel.json comau block OUT OF DATE")
        return 0 if ok else 1
    Path(a.out or VERCEL).write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
