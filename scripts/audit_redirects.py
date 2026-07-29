#!/usr/bin/env python3
"""Audit the deployed redirect rules for chains, loops and dead destinations.

A chain is A -> B where B itself redirects to C. Google follows chains but
they leak crawl budget and link equity, so they should be flattened to A -> C.
A loop is a cycle, which is fatal: the browser gives up.
A dead destination is a redirect pointing at a URL that does not exist in the
build and is not itself redirected, i.e. a 301 straight into a 404.
"""
import json
import os
import re

OUT = "www"
vercel = json.load(open(os.path.join(OUT, "vercel.json")))

# ---- index the build: which paths actually exist as pages/files? ----
pages = set()
for root, dirs, files in os.walk(OUT):
    rel = os.path.relpath(root, OUT)
    if rel.split(os.sep)[0] in ("wp-content", "wp-includes"):
        dirs[:] = []
        continue
    for f in files:
        full = os.path.join(root, f)
        p = "/" + os.path.relpath(full, OUT).replace(os.sep, "/")
        if f == "index.html":
            p = p[: -len("index.html")]
            pages.add(p.rstrip("/") or "/")
        else:
            pages.add(p)

# ---- build the redirect map (exact sources only; patterns handled separately) ----
exact = {}
patterns = []
for r in vercel.get("redirects", []):
    src, dest = r["source"], r["destination"]
    if "(" in src or ":" in src or "*" in src:
        patterns.append(r)
        continue
    exact[src.rstrip("/") or "/"] = dest


def norm(u):
    """Normalise a destination to a comparable local path, or None if external."""
    if u.startswith("http"):
        if "develop-coaching.com" not in u:
            return None  # external, out of scope
        u = re.sub(r"^https?://[^/]+", "", u)
    u = u.split("#")[0].split("?")[0]
    return u.rstrip("/") or "/"


chains, loops, dead = [], [], []

for src, dest in exact.items():
    seen = [src]
    cur = norm(dest)
    if cur is None:
        continue
    hops = 0
    while cur in exact and hops < 12:
        if cur in seen:
            loops.append(seen + [cur])
            break
        seen.append(cur)
        nxt = norm(exact[cur])
        if nxt is None:
            break
        cur = nxt
        hops += 1
    else:
        if len(seen) > 1:
            chains.append((src, exact[src], cur))
        # terminal destination: does it exist?
        if cur not in pages and cur not in exact:
            dead.append((src, exact[src]))
        continue
    if len(seen) > 1 and (seen, cur) not in [(c[0], c[2]) for c in chains]:
        pass

print(f"exact redirect rules: {len(exact)}")
print(f"pattern rules (not chain-checked): {len(patterns)}")
print(f"pages/files indexed in build: {len(pages)}")
print()
print(f"LOOPS: {len(loops)}")
for l in loops[:10]:
    print("   " + " -> ".join(l))
print()
print(f"CHAINS (A->B->...->C, should be flattened to A->C): {len(chains)}")
for a, b, c in chains[:25]:
    print(f"   {a}  ->  {b}   [ends at {c}]")
print()
print(f"REDIRECTS INTO A 404: {len(dead)}")
for a, b in dead[:25]:
    print(f"   {a}  ->  {b}")

json.dump(
    {"loops": loops, "chains": chains, "dead": dead},
    open("export/redirect-audit.json", "w"), indent=1,
)
