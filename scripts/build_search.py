#!/usr/bin/env python3
"""Replace the WordPress search with a static, client-side equivalent.

The live search form does GET / with ?s=term, which WordPress turns into a
results page. A static build has no server to do that, so this script:

  1. builds search-index.json from the built pages (title, url, summary)
  2. writes /search/ which reads ?s= and renders matches in the browser
  3. repoints the existing search form at /search/

The results page is styled from scratch rather than cloned from WordPress,
because there is no WordPress search results template in the export to copy.
It deliberately stays plain so it reads as part of the site rather than
competing with it.
"""
import html as htmllib
import json
import os
import re

OUT = "www"
DOMAIN = "https://develop-coaching.com"

# Content types worth searching. Media and drafts are excluded.
TYPES = ["posts", "pages", "podcast", "podcast-transcript", "courses", "webinars"]

built = set()
for root, dirs, files in os.walk(OUT):
    rel = os.path.relpath(root, OUT)
    if rel.split(os.sep)[0] in ("wp-content", "wp-includes"):
        dirs[:] = []
        continue
    if "index.html" in files:
        p = "/" + os.path.relpath(root, OUT).replace(os.sep, "/")
        built.add("/" if p == "/." else p.rstrip("/") + "/")

TAG_RE = re.compile(r"<[^>]+>")


def clean(s, limit=200):
    s = TAG_RE.sub(" ", s or "")
    s = htmllib.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:limit]


index = []
seen = set()
for t in TYPES:
    path = f"export/content/{t}.json"
    if not os.path.exists(path):
        continue
    for item in json.load(open(path)):
        if not isinstance(item, dict) or item.get("status") != "publish":
            continue
        link = item.get("link") or ""
        if not link.startswith(DOMAIN):
            continue
        rel = link[len(DOMAIN):] or "/"
        if not rel.endswith("/"):
            rel += "/"
        if rel not in built or rel in seen:
            continue
        seen.add(rel)
        title = clean(item.get("title", {}).get("rendered", ""), 160)
        excerpt = clean(item.get("excerpt", {}).get("rendered", ""), 220)
        if not excerpt:
            excerpt = clean(item.get("content", {}).get("rendered", ""), 220)
        if not title:
            continue
        index.append({"t": title, "u": rel, "s": excerpt, "k": t})

index.sort(key=lambda x: x["t"].lower())
json.dump(index, open(os.path.join(OUT, "search-index.json"), "w"), separators=(",", ":"))
print(f"search-index.json: {len(index)} entries")

LABELS = {
    "posts": "Article",
    "pages": "Page",
    "podcast": "Podcast",
    "podcast-transcript": "Transcript",
    "courses": "Course",
    "webinars": "Webinar",
}

page = """<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, follow">
<title>Search - Develop Coaching</title>
<link rel="canonical" href="DOMAIN/search/">
<style>
  :root {
    --ink: #414042;
    --ink-soft: #6b6b6d;
    --blue: #0069b1;
    --yellow: #fdce36;
    --rule: #e2e5e8;
    --bg: #ffffff;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
  }
  .wrap { max-width: 780px; margin: 0 auto; padding: 56px 24px 96px; }
  .back { display: inline-block; margin-bottom: 28px; color: var(--blue);
          text-decoration: none; font-size: 14px; font-weight: 600; }
  .back:hover { text-decoration: underline; }
  h1 { font-size: 30px; margin: 0 0 20px; font-weight: 700; }
  form { display: flex; gap: 10px; margin-bottom: 12px; }
  input[type=search] {
    flex: 1; padding: 13px 16px; font-size: 16px; font-family: inherit;
    border: 2px solid var(--rule); border-radius: 8px; color: var(--ink);
  }
  input[type=search]:focus { outline: none; border-color: var(--blue); }
  button {
    padding: 13px 26px; font-size: 15px; font-weight: 700; font-family: inherit;
    background: var(--yellow); color: var(--ink); border: none;
    border-radius: 8px; cursor: pointer;
  }
  button:hover { filter: brightness(0.95); }
  button:focus-visible { outline: 3px solid var(--blue); outline-offset: 2px; }
  .count { color: var(--ink-soft); font-size: 14px; margin: 0 0 28px; }
  ul { list-style: none; margin: 0; padding: 0; }
  li { padding: 20px 0; border-bottom: 1px solid var(--rule); }
  li:first-child { border-top: 1px solid var(--rule); }
  .kind {
    display: inline-block; font-size: 11px; letter-spacing: .06em;
    text-transform: uppercase; color: var(--blue); font-weight: 700;
    margin-bottom: 5px;
  }
  a.result { display: block; color: var(--ink); text-decoration: none; font-size: 19px;
             font-weight: 700; margin-bottom: 5px; }
  a.result:hover { color: var(--blue); }
  p.snippet { margin: 0; color: var(--ink-soft); font-size: 15px; }
  mark { background: var(--yellow); color: var(--ink); padding: 0 2px; }
  .empty { color: var(--ink-soft); padding: 32px 0; }
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="/blog/">&#8592; Back to the blog</a>
  <h1>Search</h1>
  <form id="f" role="search">
    <input type="search" id="q" name="s" placeholder="Search articles, podcasts and pages..." aria-label="Search">
    <button type="submit">Search</button>
  </form>
  <p class="count" id="count"></p>
  <ul id="results"></ul>
</div>
<script>
const LABELS = LABELS_JSON;
const params = new URLSearchParams(location.search);
const term = (params.get('s') || '').trim();
document.getElementById('q').value = term;

function esc(s){return s.replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function hl(s, t){
  if(!t) return esc(s);
  const re = new RegExp('(' + t.replace(/[.*+?^${}()|[\\]\\\\]/g,'\\\\$&') + ')','ig');
  return esc(s).replace(re, '<mark>$1</mark>');
}

document.getElementById('f').addEventListener('submit', e => {
  e.preventDefault();
  const v = document.getElementById('q').value.trim();
  location.search = v ? '?s=' + encodeURIComponent(v) : '';
});

async function run(){
  const countEl = document.getElementById('count');
  const list = document.getElementById('results');
  if(!term){ countEl.textContent = 'Type something above to search the site.'; return; }
  let data;
  try {
    data = await (await fetch('/search-index.json')).json();
  } catch (err) {
    countEl.textContent = 'Search is temporarily unavailable. Please try again shortly.';
    return;
  }
  const t = term.toLowerCase();
  const scored = [];
  for(const r of data){
    const inTitle = r.t.toLowerCase().includes(t);
    const inBody = r.s.toLowerCase().includes(t);
    if(inTitle || inBody) scored.push([inTitle ? 0 : 1, r]);
  }
  scored.sort((a,b) => a[0]-b[0] || a[1].t.localeCompare(b[1].t));
  countEl.textContent = scored.length
    ? scored.length + ' result' + (scored.length===1?'':'s') + ' for "' + term + '"'
    : 'No results for "' + term + '"';
  if(!scored.length){
    list.innerHTML = '<li class="empty">Try a shorter or more general word, or <a href="/blog/">browse the blog</a>.</li>';
    return;
  }
  list.innerHTML = scored.map(([,r]) =>
    '<li><span class="kind">' + (LABELS[r.k] || 'Page') + '</span>' +
    '<a class="result" href="' + r.u + '">' + hl(r.t, term) + '</a>' +
    (r.s ? '<p class="snippet">' + hl(r.s, term) + '</p>' : '') + '</li>'
  ).join('');
}
run();
</script>
</body>
</html>
"""

page = page.replace("DOMAIN", DOMAIN).replace("LABELS_JSON", json.dumps(LABELS))
os.makedirs(os.path.join(OUT, "search"), exist_ok=True)
open(os.path.join(OUT, "search", "index.html"), "w", encoding="utf-8").write(page)
print("search/index.html written")

# ---- repoint the existing search form ----
patched = 0
for root, dirs, files in os.walk(OUT):
    rel = os.path.relpath(root, OUT)
    if rel.split(os.sep)[0] in ("wp-content", "wp-includes"):
        dirs[:] = []
        continue
    if "index.html" not in files:
        continue
    fp = os.path.join(root, "index.html")
    h = open(fp, encoding="utf-8", errors="ignore").read()
    if 'class="elementor-search-form" action="/"' not in h:
        continue
    h = h.replace(
        '<form class="elementor-search-form" action="/" method="get">',
        '<form class="elementor-search-form" action="/search/" method="get">',
    )
    open(fp, "w", encoding="utf-8").write(h)
    patched += 1
print(f"search forms repointed to /search/: {patched}")
