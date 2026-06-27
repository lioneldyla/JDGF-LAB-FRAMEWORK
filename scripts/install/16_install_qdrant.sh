#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${QDRANT_ENV_FILE:-${ROOT_DIR}/infrastructure/qdrant/.env}"

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" \
  qdrant "${ENV_FILE}" QDRANT_API_KEY 32
