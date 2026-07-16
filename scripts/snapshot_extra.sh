#!/bin/bash
# Snapshot extra URLs; record redirects separately so they can be reproduced on Vercel
fetch() {
  url="$1"
  final=$(curl -sL --max-time 30 -o /dev/null -w "%{http_code} %{url_effective}" "$url")
  code="${final%% *}"; dest="${final#* }"
  if [ "$code" != "200" ]; then echo "FAIL $code $url" >> export/extra-results.txt; return; fi
  if [ "${dest%/}" != "${url%/}" ]; then
    echo "REDIRECT $url -> $dest" >> export/extra-results.txt; return
  fi
  path=$(echo "$url" | sed 's|https://develop-coaching.com||; s|/$||; s|^/||; s|/|__|g')
  curl -sL --max-time 30 -o "export/reference/${path}.html" "$url"
  echo "OK $url" >> export/extra-results.txt
}
export -f fetch
rm -f export/extra-results.txt
xargs -P 8 -I{} bash -c 'fetch "$@"' _ {} < export/extra-urls.txt
sort export/extra-results.txt | uniq > export/extra-results-sorted.txt && mv export/extra-results-sorted.txt export/extra-results.txt
grep -c "^OK" export/extra-results.txt; grep -c "^REDIRECT" export/extra-results.txt; grep -c "^FAIL" export/extra-results.txt || true
