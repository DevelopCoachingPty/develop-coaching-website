#!/usr/bin/env python3
"""Pre-cutover readiness check against the deployed build.

Everything here is verifiable now, without touching Rochen or DNS. The point
is to establish what is genuinely ready so the only outstanding work at
cutover is the WordPress rehoming and the DNS change itself.
"""
import concurrent.futures as cf
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

BASE = "https://develop-coaching-site.vercel.app"
LIVE = "https://develop-coaching.com"
UA = {"User-Agent": "Mozilla/5.0 (compatible; dc-readiness/1.0)"}
results = []


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def get(url, timeout=45, follow_redirects=True):
    try:
        req = urllib.request.Request(url, headers=UA)
        opener = (urllib.request.build_opener() if follow_redirects
                  else urllib.request.build_opener(NoRedirect))
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, b"", dict(e.headers or {})
    except Exception as e:
        return 0, str(e).encode(), {}


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


# ---- 1. every URL in the sitemap resolves ----
status, body, _ = get(f"{BASE}/sitemap.xml")
check("sitemap.xml reachable", status == 200, f"HTTP {status}")

sub_sitemaps = re.findall(rb"<loc>([^<]+)</loc>", body)
urls = []
for sm in sub_sitemaps:
    sm_url = sm.decode().replace(LIVE, BASE)
    s, b, _ = get(sm_url)
    if s == 200:
        urls += [u.decode().replace(LIVE, BASE) for u in re.findall(rb"<loc>([^<]+)</loc>", b)]
check(f"{len(sub_sitemaps)} sub-sitemaps parsed", len(sub_sitemaps) >= 5, f"{len(urls)} urls")


def page_ok(u):
    s, _, _ = get(u, timeout=40)
    return u, s


bad = []
with cf.ThreadPoolExecutor(max_workers=10) as ex:
    for u, s in ex.map(page_ok, urls):
        if s != 200:
            bad.append((u, s))
check(f"all {len(urls)} sitemap URLs return 200", not bad,
      "; ".join(f"{s} {u}" for u, s in bad[:5]) or "no failures")

# ---- 2. media served from Blob ----
media = [
    "/wp-content/uploads/2023/10/branding-with-sapna-pieroux.mp3",
    "/wp-content/uploads/2022/12/BRADLEY-TESTIMONIAL.mp4",
]
for m in media:
    s, _, h = get(BASE + m)
    served_by = h.get("location", "") or h.get("server", "")
    check(f"media reachable {m.split('/')[-1][:34]}", s in (200, 302, 307, 308),
          f"HTTP {s}")

# ---- 3. key conversion paths present ----
s, body, _ = get(f"{BASE}/schedule-a-call/")
html = body.decode("utf-8", errors="ignore")
check("booking page loads", s == 200, f"HTTP {s}")
check("GoHighLevel booking widget present", "link.flow-build.com/widget/booking" in html)

s, body, _ = get(f"{BASE}/contact/")
html_c = body.decode("utf-8", errors="ignore")
check("contact page loads", s == 200, f"HTTP {s}")
check("contact booking widget present", "link.flow-build.com" in html_c)

s, body, _ = get(f"{BASE}/")
home = body.decode("utf-8", errors="ignore")
check("newsletter embed present (FlowBuild)",
      "link.flow-build.com/widget/form/LrwamDnwkXRzgaIuSFn2" in home)
check("GTM loader present", "GTM-T4HBRD3" in home)
check("no legacy WP discovery tags", not re.search(
    r'type="application/rss|api\.w\.org|\+oembed"|rel="EditURI"', home))
check("no www absolute links", "https://www.develop-coaching.com" not in home)

# ---- 4. security headers ----
s, _, h = get(f"{BASE}/")
for header in ("strict-transport-security", "x-content-type-options",
               "referrer-policy", "x-frame-options"):
    check(f"header {header}", header in {k.lower() for k in h})
check("preview noindex present (drops on real domain)",
      "noindex" in h.get("X-Robots-Tag", h.get("x-robots-tag", "")).lower())

# ---- 5. redirects ----
redirect_samples = [
    ("/the-5-pillars-attract/", "/5-pillars-free-trainings/attract/"),
    ("/blog/page/3/", "/blog/"),
    ("/services/mastermind-course/", "/courses/mastermind-course/"),
    ("/trades/", "/trades-pipeline-diagnostic/"),
]
for src, expect in redirect_samples:
    s, _, h = get(BASE + src, follow_redirects=False)
    loc = h.get("location", h.get("Location", ""))
    check(f"redirect {src}", s in (301, 308) and expect in loc, f"HTTP {s} -> {loc[:60]}")

# ---- 6. search + feeds ----
s, _, _ = get(f"{BASE}/search/")
check("static search page", s == 200, f"HTTP {s}")
s, b, _ = get(f"{BASE}/search-index.json")
check("search index served", s == 200 and len(json.loads(b)) > 300,
      f"{len(json.loads(b)) if s==200 else 0} entries")
s, _, _ = get(f"{BASE}/feed/podcast")
check("podcast feed preserved", s == 200, f"HTTP {s}")
s, _, _ = get(f"{BASE}/robots.txt")
check("robots.txt", s == 200, f"HTTP {s}")

print("\n" + "=" * 60)
passed = sum(1 for _, ok, _ in results if ok)
print(f"{passed}/{len(results)} checks passed")
fails = [(n, d) for n, ok, d in results if not ok]
if fails:
    print("\nFAILURES:")
    for n, d in fails:
        print(f"  {n}  {d}")
