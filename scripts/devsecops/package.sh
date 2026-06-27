#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"

rm -rf "${DIST_DIR}"
uv build --directory "${ROOT_DIR}" --out-dir "${DIST_DIR}"

if command -v sha256sum >/dev/null 2>&1; then
  (cd "${DIST_DIR}" && sha256sum ./*.whl ./*.tar.gz > SHA256SUMS)
else
  (cd "${DIST_DIR}" && shasum -a 256 ./*.whl ./*.tar.gz > SHA256SUMS)
fi

echo "Release candidate artifacts created in ${DIST_DIR}."
