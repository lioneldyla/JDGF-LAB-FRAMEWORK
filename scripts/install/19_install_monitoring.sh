#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MONITORING_DIR="${ROOT_DIR}/infrastructure/monitoring"
GRAFANA_ENV_FILE="${GRAFANA_ENV_FILE:-${MONITORING_DIR}/grafana/.env}"
PROMETHEUS_ENV_FILE="${PROMETHEUS_ENV_FILE:-${MONITORING_DIR}/prometheus/.env}"
LOKI_ENV_FILE="${LOKI_ENV_FILE:-${MONITORING_DIR}/loki/.env}"

command -v docker >/dev/null 2>&1 || {
  echo "Docker is required" >&2
  exit 1
}
docker compose version >/dev/null

if [[ ! -f "${GRAFANA_ENV_FILE}" ]]; then
  echo "Create ${GRAFANA_ENV_FILE} from .env.example first" >&2
  exit 1
fi

network_from_file="$(sed -n 's/^JDGF_NETWORK=//p' \
  "${GRAFANA_ENV_FILE}" | tail -n 1)"
NETWORK="${JDGF_NETWORK:-${network_from_file:-jdgf-network}}"

grafana_password="$(sed -n 's/^GRAFANA_ADMIN_PASSWORD=//p' \
  "${GRAFANA_ENV_FILE}" 2>/dev/null | tail -n 1)"
if [[ ${#grafana_password} -lt 16 ]]; then
  echo "GRAFANA_ADMIN_PASSWORD must contain at least 16 characters" >&2
  exit 1
fi

docker network inspect "${NETWORK}" >/dev/null 2>&1 || \
  docker network create --label jdgf.managed=true "${NETWORK}" >/dev/null

for service in loki prometheus grafana; do
  directory="${MONITORING_DIR}/${service}"
  case "${service}" in
    loki) env_file="${LOKI_ENV_FILE}" ;;
    prometheus) env_file="${PROMETHEUS_ENV_FILE}" ;;
    grafana) env_file="${GRAFANA_ENV_FILE}" ;;
  esac
  if [[ ! -f "${env_file}" ]]; then
    echo "Create ${env_file} from .env.example first" >&2
    exit 1
  fi
  docker compose --env-file "${env_file}" --file "${directory}/compose.yaml" \
    up --detach --wait
done
