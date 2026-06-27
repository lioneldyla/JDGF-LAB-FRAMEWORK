#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${OLLAMA_ENV_FILE:-${ROOT_DIR}/infrastructure/ollama/.env}"

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" ollama "${ENV_FILE}"
