#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing JDGF Lab Framework 0.10.1..."
"${ROOT_DIR}/bootstrap.sh"
"${ROOT_DIR}/verify.sh"
echo "JDGF Lab Framework installation completed."
