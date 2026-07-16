#!/bin/bash
# Fetch rendered HTML of every URL into export/reference/, filename = URL path
mkdir -p export/reference
fetch() {
  url="$1"
  path=$(echo "$url" | sed 's|https://develop-coaching.com||; s|/$||; s|^/||; s|/|__|g')
  [ -z "$path" ] && path="__home"
  out="export/reference/${path}.html"
  code=$(curl -sL --max-time 30 -o "$out" -w "%{http_code}" "$url")
  [ "$code" != "200" ] && echo "FAIL $code $url"
}
export -f fetch
xargs -P 8 -I{} bash -c 'fetch "$@"' _ {} < export/snapshot-urls.txt
echo "done: $(ls export/reference | wc -l) files"
