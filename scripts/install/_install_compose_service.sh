#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 && $# -ne 4 ]]; then
  echo "usage: $0 SERVICE ENV_FILE [SECRET_KEY MINIMUM_LENGTH]" >&2
  exit 2
fi

SERVICE="$1"
ENV_FILE="$2"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/infrastructure/${SERVICE}"

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

if [[ $# -eq 4 ]]; then
  SECRET_KEY="$3"
  MINIMUM_LENGTH="$4"
  secret="$(sed -n "s/^${SECRET_KEY}=//p" "${ENV_FILE}" | tail -n 1)"
  if [[ ${#secret} -lt ${MINIMUM_LENGTH} ]]; then
    echo "${SECRET_KEY} must contain at least ${MINIMUM_LENGTH} characters" >&2
    exit 1
  fi
fi

docker network inspect "${NETWORK}" >/dev/null 2>&1 || \
  docker network create --label jdgf.managed=true "${NETWORK}" >/dev/null

docker compose \
  --env-file "${ENV_FILE}" \
  --file "${SERVICE_DIR}/compose.yaml" \
  up --detach --wait
