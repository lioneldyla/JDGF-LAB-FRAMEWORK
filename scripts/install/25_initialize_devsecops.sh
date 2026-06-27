#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ ! -x "${ROOT_DIR}/.venv/bin/jdgf" ]]; then
  echo "Run ./install.sh before initializing DevSecOps contracts" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/jdgf" --root "${ROOT_DIR}" validate

echo "DevSecOps contracts are initialized; deployment and publishing remain disabled."
