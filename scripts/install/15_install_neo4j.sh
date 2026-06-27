#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${NEO4J_ENV_FILE:-${ROOT_DIR}/infrastructure/neo4j/.env}"

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" \
  neo4j "${ENV_FILE}" NEO4J_PASSWORD 16
