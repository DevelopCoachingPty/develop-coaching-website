#!/bin/bash
# Render a full-page screenshot of every built page via headless Chrome.
# Requires the dc-site-preview static server running on localhost:4180.
set -euo pipefail
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT_DIR="export/screenshots"
mkdir -p "$OUT_DIR"

shoot() {
  url="$1"
  path=$(echo "$url" | sed 's|https://develop-coaching.com||; s|/$||; s|^/||; s|/|__|g')
  [ -z "$path" ] && path="__home"
  out="$OUT_DIR/${path}.png"
  [ -f "$out" ] && return
  local_url="http://localhost:4180${url#https://develop-coaching.com}"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --window-size=1280,1600 \
    --screenshot="$out" \
    --virtual-time-budget=4000 \
    "$local_url" > /dev/null 2>&1
}
export -f shoot
export CHROME OUT_DIR

xargs -P 4 -I{} bash -c 'shoot "$@"' _ {} < export/final-url-list.txt
echo "screenshots: $(ls "$OUT_DIR" | wc -l)"
