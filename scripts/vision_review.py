#!/usr/bin/env python3
"""Batch-review every page screenshot with the Mac Studio's local vision model.

For each screenshot, asks qwen2.5vl whether the page looks like a normal,
fully-rendered marketing/blog page or shows a visible fault (broken layout,
missing image placeholders, overlapping text, blank sections, error message,
unstyled HTML). Flags are written to export/vision-flags.json for a human
(Sonnet) follow-up pass against the live site.
"""
import base64
import json
import os
import subprocess
import sys
import concurrent.futures as cf

SCREENSHOT_DIR = "export/screenshots"
HOST = "gregwilkes@gregs-studio-ai"
MODEL = "qwen2.5vl:7b"
OUT = "export/vision-flags.json"

PROMPT = (
    "This is a screenshot of a marketing/blog web page for a construction "
    "business coaching company. Look ONLY for visible technical faults: "
    "broken image icons or blank grey image boxes, obviously unstyled raw "
    "HTML, overlapping or cut-off text, large unexplained blank white "
    "gaps, error messages (404, 500, etc.), or a page that looks empty. "
    "Do not comment on design taste, colour choices, or copywriting. "
    "Reply with exactly one line: either 'OK' or 'FLAG: <short reason>'."
)


def ask_studio(png_path):
    with open(png_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    payload = json.dumps({
        "model": MODEL,
        "prompt": PROMPT,
        "images": [b64],
        "stream": False,
        "options": {"temperature": 0},
    })
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=15", HOST,
         "curl -s -X POST http://localhost:11434/api/generate -d @-"],
        input=payload, capture_output=True, text=True, timeout=90,
    )
    if proc.returncode != 0:
        return f"ERROR: ssh/curl failed: {proc.stderr[:200]}"
    try:
        resp = json.loads(proc.stdout)
        return resp.get("response", "ERROR: empty response").strip()
    except json.JSONDecodeError:
        return f"ERROR: bad JSON: {proc.stdout[:200]}"


def process_one(fname):
    path = os.path.join(SCREENSHOT_DIR, fname)
    result = ask_studio(path)
    return fname, result


def main():
    files = sorted(f for f in os.listdir(SCREENSHOT_DIR) if f.endswith(".png"))
    print(f"reviewing {len(files)} screenshots via {MODEL} on the Studio...")
    results = {}
    done = 0
    with cf.ThreadPoolExecutor(max_workers=3) as ex:
        for fname, result in ex.map(process_one, files):
            results[fname] = result
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{len(files)}")
    flags = {f: r for f, r in results.items() if not r.strip().upper().startswith("OK")}
    json.dump({"all_results": results, "flags": flags}, open(OUT, "w"), indent=1)
    print(f"\ndone. {len(flags)} flagged of {len(files)}:")
    for f, r in flags.items():
        print(f"  {f}: {r}")


if __name__ == "__main__":
    main()
