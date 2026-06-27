#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/infrastructure/postgres"
ENV_FILE="${POSTGRES_ENV_FILE:-${SERVICE_DIR}/.env}"

docker compose --env-file "${ENV_FILE}" --file "${SERVICE_DIR}/compose.yaml" \
  exec --no-TTY postgres sh -ec 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
