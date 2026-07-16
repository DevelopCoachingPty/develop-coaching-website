#!/usr/bin/env python3
"""Mirror webpack lazy-loaded chunks for Elementor / Elementor Pro.

The chunk id -> name/hash maps live inside the webpack runtime files, which
are already mirrored. Parse them, reconstruct every chunk URL, download.
"""
import concurrent.futures as cf
import os
import re
import urllib.request

DOMAIN = "https://develop-coaching.com"
RUNTIMES = [
    "www/wp-content/plugins/elementor/assets/js/webpack.runtime.min.js",
    "www/wp-content/plugins/elementor-pro/assets/js/webpack-pro.runtime.min.js",
]


def chunk_urls(runtime_path):
    src = open(runtime_path, encoding="utf-8", errors="ignore").read()
    base = os.path.dirname(runtime_path.replace("www", "", 1))
    files = set(re.findall(r'"([^"]+\.bundle\.min\.js)"', src))
    return [f"{base}/{f}" for f in files]


def download(path):
    dest = os.path.join("www", path.lstrip("/"))
    if os.path.exists(dest):
        return "have"
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    try:
        req = urllib.request.Request(DOMAIN + path, headers={"User-Agent": "dc-mirror/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return "ok"
    except Exception as e:
        return f"FAIL {path}: {e}"


all_urls = []
for rt in RUNTIMES:
    if os.path.exists(rt):
        urls = chunk_urls(rt)
        print(f"{rt}: {len(urls)} chunks")
        all_urls.extend(urls)
    else:
        print(f"MISSING runtime: {rt}")

results = {"ok": 0, "have": 0}
fails = []
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for res in ex.map(download, all_urls):
        if res in results:
            results[res] += 1
        else:
            fails.append(res)
print(f"downloaded: {results['ok']}, already had: {results['have']}, failed: {len(fails)}")
for f in fails[:10]:
    print(" ", f)
