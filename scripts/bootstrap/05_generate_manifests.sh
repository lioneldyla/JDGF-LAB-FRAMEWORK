#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

for manifest in framework.yaml modules.yaml projects.yaml rag-engine.yaml ai-platform.yaml database-platform.yaml automation-platform.yaml knowledge-platform.yaml; do
  if [[ ! -s "${ROOT_DIR}/manifests/${manifest}" ]]; then
    echo "Missing manifest: ${manifest}" >&2
    exit 1
  fi
done

PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/jdgf" --root "${ROOT_DIR}" validate

echo "Framework manifests are present and valid."
