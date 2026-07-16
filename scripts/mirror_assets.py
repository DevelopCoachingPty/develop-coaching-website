#!/usr/bin/env python3
"""Mirror all wp-content / wp-includes assets referenced by the built site.

Pass 1: scan www/**/*.html for asset URLs.
Pass 2: download, then scan downloaded CSS for url() references and download
those too (fonts, background images). Repeats until nothing new appears.
"""
import concurrent.futures as cf
import os
import re
import urllib.parse
import urllib.request

OUT = "www"
DOMAIN = "https://develop-coaching.com"
ASSET_RE = re.compile(r'(?:href|src|content)="(/wp-(?:content|includes)/[^"?]+)')
SRCSET_RE = re.compile(r'srcset="([^"]+)"')
CSS_URL_RE = re.compile(r'url\((["\']?)([^)"\']+)\1\)')
STYLE_URL_RE = re.compile(r'(/wp-(?:content|includes)/[^"\')\s,]+\.(?:png|jpe?g|webp|gif|svg|woff2?|ttf|eot|css|js|mp4|ico))')


def scan_html():
    urls = set()
    for root, _, files in os.walk(OUT):
        for f in files:
            if not f.endswith(".html"):
                continue
            html = open(os.path.join(root, f), encoding="utf-8", errors="ignore").read()
            urls.update(ASSET_RE.findall(html))
            for srcset in SRCSET_RE.findall(html):
                for part in srcset.split(","):
                    u = part.strip().split(" ")[0]
                    if u.startswith("/wp-"):
                        urls.add(u.split("?")[0])
            urls.update(STYLE_URL_RE.findall(html))
            # JSON-escaped refs inside Elementor data-settings attributes
            for esc in re.findall(r'\\/wp-(?:content|includes)\\/[^"\\]+(?:\\/[^"\\]+)*\.(?:png|jpe?g|webp|gif|svg|mp4|mp3)', html):
                urls.add(esc.replace("\\/", "/"))
    return urls


def scan_css():
    urls = set()
    for root, _, files in os.walk(os.path.join(OUT, "wp-content")):
        for f in files:
            if not f.endswith(".css"):
                continue
            css_path = os.path.join(root, f)
            css = open(css_path, encoding="utf-8", errors="ignore").read()
            base = "/" + os.path.relpath(root, OUT).replace(os.sep, "/") + "/"
            for _, ref in CSS_URL_RE.findall(css):
                if ref.startswith(("data:", "#", "http")):
                    continue
                full = urllib.parse.urljoin(base, ref.split("?")[0].split("#")[0])
                if full.startswith("/wp-"):
                    urls.add(full)
    return urls


def download(path):
    dest = os.path.join(OUT, path.lstrip("/"))
    if os.path.exists(dest):
        return None
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    url = DOMAIN + urllib.parse.quote(path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dc-mirror/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        if dest.endswith(".css"):
            css = data.decode("utf-8", errors="ignore")
            css = css.replace(DOMAIN + "/", "/").replace("//develop-coaching.com/", "/")
            data = css.encode("utf-8")
        with open(dest, "wb") as f:
            f.write(data)
        return len(data)
    except Exception as e:
        return f"FAIL {path}: {e}"


def run(urls):
    total, fails = 0, []
    with cf.ThreadPoolExecutor(max_workers=12) as ex:
        for res in ex.map(download, sorted(urls)):
            if isinstance(res, int):
                total += res
            elif isinstance(res, str):
                fails.append(res)
    return total, fails


def main():
    seen = set()
    round_no = 0
    grand_total = 0
    all_fails = []
    while True:
        round_no += 1
        urls = (scan_html() | scan_css()) - seen
        if not urls:
            break
        seen.update(urls)
        total, fails = run(urls)
        grand_total += total
        all_fails.extend(fails)
        print(f"round {round_no}: {len(urls)} assets, {total/1e6:.1f} MB, {len(fails)} failed")
    print(f"TOTAL: {len(seen)} assets, {grand_total/1e6:.1f} MB downloaded")
    for f in all_fails[:20]:
        print(" ", f)


if __name__ == "__main__":
    main()
