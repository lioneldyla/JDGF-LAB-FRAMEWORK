#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/infrastructure/open-webui"
ENV_FILE="${OPEN_WEBUI_ENV_FILE:-${SERVICE_DIR}/.env}"

command -v docker >/dev/null 2>&1 || {
  echo "Docker is required" >&2
  exit 1
}
docker compose version >/dev/null

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Create ${SERVICE_DIR}/.env from .env.example first" >&2
  exit 1
fi

network_from_file="$(sed -n 's/^JDGF_NETWORK=//p' "${ENV_FILE}" | tail -n 1)"
NETWORK="${JDGF_NETWORK:-${network_from_file:-jdgf-network}}"

secret="$(sed -n 's/^WEBUI_SECRET_KEY=//p' "${ENV_FILE}" | tail -n 1)"
if [[ ${#secret} -lt 32 ]]; then
  echo "WEBUI_SECRET_KEY must contain at least 32 characters" >&2
  exit 1
fi

docker network inspect "${NETWORK}" >/dev/null 2>&1 || \
  docker network create --label jdgf.managed=true "${NETWORK}" >/dev/null

docker compose \
  --env-file "${ENV_FILE}" \
  --file "${SERVICE_DIR}/compose.yaml" \
  up --detach --wait
