#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${ROOT_DIR}"

uv sync --frozen --extra dev
./scripts/devsecops/run-lint.sh
./verify.sh
./scripts/devsecops/security-scan.sh
./scripts/devsecops/package.sh

echo "Verified release candidate build completed without publishing."
