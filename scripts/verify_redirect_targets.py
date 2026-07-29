#!/usr/bin/env python3
"""Empirically check every redirect destination on BOTH sites.

The point is to separate two very different things:

  parity     destination 404s on the new build AND on live WordPress.
             Pre-existing rot in the Redirection plugin, not caused by us.
             Worth cleaning up, but it is not a migration regression.

  REGRESSION destination works on live WordPress but 404s on the new build.
             That IS caused by us and must be fixed before cutover.
"""
import concurrent.futures as cf
import json
import re
import urllib.error
import urllib.request

NEW = "https://develop-coaching-site.vercel.app"
LIVE = "https://develop-coaching.com"
UA = {"User-Agent": "Mozilla/5.0 (compatible; dc-migration-audit/1.0)"}

vercel = json.load(open("www/vercel.json"))

dests = set()
for r in vercel.get("redirects", []):
    d = r["destination"]
    if "(" in r["source"] or ":" in r["source"]:
        continue  # pattern rule, destination is templated
    if d.startswith("http") and "develop-coaching.com" not in d:
        continue  # external
    d = re.sub(r"^https?://[^/]+", "", d).split("#")[0].split("?")[0]
    if d.startswith("/"):
        dests.add(d)

print(f"unique redirect destinations to check: {len(dests)}\n")


def status(base, path):
    try:
        req = urllib.request.Request(base + path, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def check(path):
    return path, status(NEW, path), status(LIVE, path)


rows = []
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for path, new_s, live_s in ex.map(check, sorted(dests)):
        rows.append((path, new_s, live_s))

regressions = [r for r in rows if r[1] >= 400 and r[2] < 400]
parity_dead = [r for r in rows if r[1] >= 400 and r[2] >= 400]
ok = [r for r in rows if r[1] < 400]

print(f"destination OK on new build:            {len(ok)}")
print(f"dead on BOTH (pre-existing, parity):    {len(parity_dead)}")
print(f"REGRESSIONS (works live, broken on new): {len(regressions)}")
print()
if regressions:
    print("REGRESSIONS, must fix before cutover:")
    for p, n, l in regressions:
        print(f"   new={n} live={l}  {p}")
else:
    print("No regressions. Every destination that works on live also works on the new build.")

json.dump(
    {
        "regressions": regressions,
        "parity_dead": parity_dead,
        "ok_count": len(ok),
    },
    open("export/redirect-target-audit.json", "w"),
    indent=1,
)
