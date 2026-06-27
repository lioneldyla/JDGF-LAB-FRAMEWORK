#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ ! -x "${ROOT_DIR}/.venv/bin/jdgf" ]]; then
  echo "Run ./install.sh before initializing Knowledge Platform contracts" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/jdgf" --root "${ROOT_DIR}" validate

echo "Knowledge Platform contracts are initialized; runtimes remain disabled."
