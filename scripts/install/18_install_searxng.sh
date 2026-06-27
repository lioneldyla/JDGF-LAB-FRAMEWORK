#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${SEARXNG_ENV_FILE:-${ROOT_DIR}/infrastructure/searxng/.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Create ${ENV_FILE} from .env.example first" >&2
  exit 1
fi

redis_password="$(sed -n 's/^REDIS_PASSWORD=//p' "${ENV_FILE}" 2>/dev/null | tail -n 1)"
if [[ ${#redis_password} -lt 16 ]]; then
  echo "REDIS_PASSWORD must contain at least 16 characters" >&2
  exit 1
fi

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" \
  searxng "${ENV_FILE}" SEARXNG_SECRET 32
