#!/usr/bin/env python3
"""Convert the Redirection-plugin export (TSV) into export/manual-redirects.json.

Rules:
- Disabled (OFF) rules are skipped.
- 410 rules are skipped (static hosting serves 404 there, close enough).
- A few known regex rules are translated to Vercel syntax by hand.
- Plain source/dest rules pass through; same-domain absolute URLs made relative.
"""
import json

SRC = "export/redirections-full.tsv"
OUT = "export/manual-redirects.json"
DOMAIN = "https://develop-coaching.com"

# Hand-translated regex rules (Redirection PCRE -> Vercel path-to-regexp)
REGEX_MAP = {
    "^/author/.*$": {"source": "/author/:path*", "destination": "/"},
    "^/blog/page/\\d+/?$": {"source": "/blog/page/:n(\\d+)", "destination": "/"},
    "^/blog/category/.*$": {"source": "/blog/category/:path*", "destination": "/"},
    "^/blog/.*/([^/]+)/?$": {
        "source": "/blog/:path(.+)/:slug([^/]+)",
        "destination": "/:slug/",
    },
}
SKIP_PREFIXES = ("^(.*)\\?nocache",)  # query-string rule; harmless on static hosting


def main():
    rules = []
    skipped = []
    for line in open(SRC):
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 4:
            continue
        state, code, src, dest = parts[0], parts[1], parts[2], parts[3]
        if state == "OFF":
            continue
        if code == "410" or not dest:
            skipped.append(f"410/no-dest: {src}")
            continue
        if any(src.startswith(p) for p in SKIP_PREFIXES):
            skipped.append(f"query rule: {src}")
            continue
        if src in REGEX_MAP:
            rules.append({**REGEX_MAP[src], "permanent": True})
            continue
        if src.startswith("^"):
            skipped.append(f"unhandled regex: {src}")
            continue
        if dest.startswith(DOMAIN):
            dest = dest[len(DOMAIN):]
        src = src if src.startswith("/") else "/" + src
        if src.rstrip("/") == dest.rstrip("/"):
            continue
        rules.append({
            "source": src.rstrip("/") or "/",
            "destination": dest,
            "permanent": code == "301",
        })
    # dedupe by source, first wins (plugin order = priority order)
    seen = set()
    deduped = []
    for r in rules:
        if r["source"] in seen:
            continue
        seen.add(r["source"])
        deduped.append(r)
    json.dump(deduped, open(OUT, "w"), indent=1)
    print(f"{len(deduped)} rules written to {OUT}")
    print(f"{len(skipped)} skipped:")
    for s in skipped:
        print("  ", s)


if __name__ == "__main__":
    main()
