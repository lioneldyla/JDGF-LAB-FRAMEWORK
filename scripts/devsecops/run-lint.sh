#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

git ls-files -z '*.sh' | xargs -0 bash -n
uv run ruff check .
uv run ruff format --check .

echo "Shell and Python lint checks passed."
