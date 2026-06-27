#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${POSTGRES_ENV_FILE:-${ROOT_DIR}/infrastructure/postgres/.env}"

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" \
  postgres "${ENV_FILE}" POSTGRES_PASSWORD 16
