#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${LITELLM_ENV_FILE:-${ROOT_DIR}/infrastructure/litellm/.env}"

"${ROOT_DIR}/scripts/install/_install_compose_service.sh" litellm "${ENV_FILE}"
