#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/infrastructure/openhands"
ENV_FILE="${OPENHANDS_ENV_FILE:-${SERVICE_DIR}/.env}"

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

risk_acceptance="$(sed -n 's/^OPENHANDS_ACCEPT_DOCKER_SOCKET_RISK=//p' "${ENV_FILE}" | tail -n 1)"
workspace="$(sed -n 's/^OPENHANDS_WORKSPACE=//p' "${ENV_FILE}" | tail -n 1)"
if [[ "${risk_acceptance}" != "yes" ]]; then
  echo "Explicit Docker socket risk acceptance is required" >&2
  exit 1
fi
if [[ "${workspace}" != /* || ! -d "${workspace}" || "${workspace}" == "/" ]]; then
  echo "OPENHANDS_WORKSPACE must be an existing dedicated absolute directory" >&2
  exit 1
fi

docker network inspect "${NETWORK}" >/dev/null 2>&1 || \
  docker network create --label jdgf.managed=true "${NETWORK}" >/dev/null

docker compose \
  --profile dangerous-local-agent \
  --env-file "${ENV_FILE}" \
  --file "${SERVICE_DIR}/compose.yaml" \
  up --detach --wait
