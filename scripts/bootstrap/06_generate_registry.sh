#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

for registry in services models modules ports networks volumes projects rag ai-services database-services automation knowledge agents orchestrators workflows governance; do
  if [[ ! -s "${ROOT_DIR}/registry/${registry}.yaml" ]]; then
    echo "Missing registry: ${registry}.yaml" >&2
    exit 1
  fi
done

PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/jdgf" --root "${ROOT_DIR}" validate

echo "Framework registries are present and valid."
