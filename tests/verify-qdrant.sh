#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${QDRANT_ENV_FILE:-${ROOT_DIR}/infrastructure/qdrant/.env}"

api_key="$(sed -n 's/^QDRANT_API_KEY=//p' "${ENV_FILE}" | tail -n 1)"
curl --fail --silent --show-error --max-time 10 \
  --header "api-key: ${api_key}" \
  "${QDRANT_HOST:-http://127.0.0.1:6333}/healthz" >/dev/null
