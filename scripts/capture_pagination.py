#!/usr/bin/env python3
"""Discover and capture paginated archive pages from the live site.

These were missed by the original capture because the sitemaps do not list
them and they are only reachable through pagination controls. Losing them
would mean /blog/page/2/ onwards (13+ real pages of article listings) 404ing
after cutover.

Runs deliberately slowly: the live WordPress host is heavily loaded and
rate-limits parallel requests, so this walks one page at a time with a pause
between each. Resumable, it skips anything already captured.
"""
import os
import time
import urllib.error
import urllib.request

LIVE = "https://develop-coaching.com"
UA = {"User-Agent": "Mozilla/5.0 (compatible; dc-migration/1.0)"}
REF = "export/reference"
BASES = [
    "/blog/",
    "/podcast/",
    "/podcast-transcript/",
    "/category/attract/",
    "/category/convert/",
    "/category/deliver/",
    "/category/plan/",
    "/category/scale/",
    "/category/uncategorized/",
]
MAX_PAGE = 40
PAUSE = 1.5


def refname(path):
    return path.strip("/").replace("/", "__") + ".html"


def fetch(path, retries=3):
    """Return (status, body). status 0 means the request failed outright."""
    url = f"{LIVE}{path}?phast=-phast&ao_noptimize=1"
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, r.read().decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception:
            time.sleep(3 * (attempt + 1))  # back off, the host is throttling
    return 0, ""


captured, found = [], []
for base in BASES:
    n = 2
    misses = 0
    while n <= MAX_PAGE:
        path = f"{base}page/{n}/"
        dest = os.path.join(REF, refname(path))
        if os.path.exists(dest):
            found.append(path)
            n += 1
            continue
        status, body = fetch(path)
        if status == 200 and body:
            open(dest, "w", encoding="utf-8").write(body)
            captured.append(path)
            found.append(path)
            print(f"captured  {path}", flush=True)
            misses = 0
            n += 1
        elif status == 0:
            # transient failure, do not treat as end of pagination
            misses += 1
            print(f"RETRY-FAIL {path}", flush=True)
            if misses >= 2:
                print(f"giving up on {base} at page {n}", flush=True)
                break
        else:
            print(f"end of {base} at page {n} (status {status})", flush=True)
            break
        time.sleep(PAUSE)

print(f"\nnewly captured: {len(captured)}")
print(f"total paginated pages present: {len(found)}")
open("export/pagination-urls.txt", "w").write(
    "\n".join(LIVE + p for p in sorted(found)) + "\n"
)
