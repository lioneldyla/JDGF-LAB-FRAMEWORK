#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

PYTHONDONTWRITEBYTECODE=1 \
  "${ROOT_DIR}/.venv/bin/python" -m pytest -p no:cacheprovider \
  "${ROOT_DIR}/tests/test_rag.py"
