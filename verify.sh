#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${ROOT_DIR}/.venv/bin/jdgf" --root "${ROOT_DIR}" validate
PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/python" -m pytest -p no:cacheprovider
