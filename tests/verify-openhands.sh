#!/usr/bin/env bash
set -euo pipefail

OPENHANDS_HOST="${OPENHANDS_HOST:-http://127.0.0.1:3002}"

curl --fail --silent --show-error --max-time 10 \
  "${OPENHANDS_HOST}/api/health" >/dev/null

echo "OpenHands health check passed."
