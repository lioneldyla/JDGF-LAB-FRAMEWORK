#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPORT_DIR="${ROOT_DIR}/reports/security"
mkdir -p "${REPORT_DIR}"
cd "${ROOT_DIR}"

if git ls-files | grep -E '(^|/)\.env$|\.(pem|key|p12|pfx)$'; then
  echo "Tracked secret-bearing filename detected" >&2
  exit 1
fi

if git grep -n -I -E 'BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY'; then
  echo "Tracked private key material detected" >&2
  exit 1
fi

uv export --quiet --frozen --no-dev --no-emit-project \
  --output-file "${REPORT_DIR}/runtime-requirements.txt"
uv run pip-audit --disable-pip \
  --requirement "${REPORT_DIR}/runtime-requirements.txt"

echo "Dependency and tracked-secret scans passed."
