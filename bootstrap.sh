#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v uv >/dev/null 2>&1; then
    echo "JDGF bootstrap requires uv: https://docs.astral.sh/uv/" >&2
    exit 1
fi

uv sync \
  --project "${ROOT_DIR}" \
  --python 3.12 \
  --locked \
  --no-editable \
  --extra dev
PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/jdgf" --root "${ROOT_DIR}" validate

echo "JDGF foundation is ready."
