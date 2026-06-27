#!/usr/bin/env bash
set -euo pipefail

curl --fail --silent --show-error --max-time 10 \
  http://127.0.0.1:5678/healthz >/dev/null

echo "n8n is reachable."
