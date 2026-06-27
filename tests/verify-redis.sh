#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/infrastructure/redis"
ENV_FILE="${REDIS_ENV_FILE:-${SERVICE_DIR}/.env}"

docker compose --env-file "${ENV_FILE}" --file "${SERVICE_DIR}/compose.yaml" \
  exec --no-TTY redis sh -ec \
  'redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping | grep PONG'
