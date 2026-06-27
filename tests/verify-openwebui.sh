#!/usr/bin/env bash
set -euo pipefail

OPEN_WEBUI_HOST="${OPEN_WEBUI_HOST:-http://127.0.0.1:3000}"

curl --fail --silent --show-error --max-time 10 \
  "${OPEN_WEBUI_HOST}/health" >/dev/null

echo "Open WebUI health check passed."
