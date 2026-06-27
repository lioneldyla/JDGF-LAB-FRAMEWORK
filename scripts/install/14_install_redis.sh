#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${REDIS_ENV_FILE:-${ROOT_DIR}/infrastructure/redis/.env}"

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" \
  redis "${ENV_FILE}" REDIS_PASSWORD 16
