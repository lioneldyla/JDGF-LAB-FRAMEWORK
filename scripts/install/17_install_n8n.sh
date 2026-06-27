#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${N8N_ENV_FILE:-${ROOT_DIR}/infrastructure/n8n/.env}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Create ${ENV_FILE} from .env.example first" >&2
  exit 1
fi

for requirement in N8N_DB_PASSWORD:16 N8N_REDIS_PASSWORD:16; do
  key="${requirement%%:*}"
  minimum="${requirement##*:}"
  value="$(sed -n "s/^${key}=//p" "${ENV_FILE}" 2>/dev/null | tail -n 1)"
  if [[ ${#value} -lt ${minimum} ]]; then
    echo "${key} must contain at least ${minimum} characters" >&2
    exit 1
  fi
done

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" \
  n8n "${ENV_FILE}" N8N_ENCRYPTION_KEY 32
