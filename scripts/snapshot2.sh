#!/bin/bash
# Re-snapshot every URL with PhastPress and Autoptimize disabled
mkdir -p export/reference
fetch() {
  url="$1"
  path=$(echo "$url" | sed 's|https://develop-coaching.com||; s|/$||; s|^/||; s|/|__|g')
  [ -z "$path" ] && path="__home"
  out="export/reference/${path}.html"
  code=$(curl -sL --max-time 40 -o "$out" -w "%{http_code}" "${url}?phast=-phast&ao_noptimize=1")
  [ "$code" != "200" ] && echo "FAIL $code $url"
}
export -f fetch
xargs -P 8 -I{} bash -c 'fetch "$@"' _ {} < export/final-url-list.txt
echo "done"
