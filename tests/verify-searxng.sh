#!/usr/bin/env bash
set -euo pipefail

curl --fail --silent --show-error --max-time 10 \
  --request POST \
  --data-urlencode 'q=jdgf healthcheck' \
  --data 'format=json' \
  http://127.0.0.1:8080/search >/dev/null

echo "SearXNG is reachable."
