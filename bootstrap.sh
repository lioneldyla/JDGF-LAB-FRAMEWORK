#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

command -v uv >/dev/null 2>&1 || {
  echo "uv is required: https://docs.astral.sh/uv/" >&2
  exit 1
}

echo "Bootstrapping JDGF Lab Framework from the locked environment..."
uv sync --directory "${ROOT_DIR}" --frozen --extra dev

"${ROOT_DIR}/scripts/bootstrap/05_generate_manifests.sh"
"${ROOT_DIR}/scripts/bootstrap/06_generate_registry.sh"

echo "Bootstrap completed without activating optional runtimes."
