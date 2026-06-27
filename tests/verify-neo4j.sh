#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/infrastructure/neo4j"
ENV_FILE="${NEO4J_ENV_FILE:-${SERVICE_DIR}/.env}"

docker compose --env-file "${ENV_FILE}" --file "${SERVICE_DIR}/compose.yaml" \
  exec --no-TTY neo4j sh -ec \
  'cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" >/dev/null'
