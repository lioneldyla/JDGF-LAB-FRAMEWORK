#!/usr/bin/env bash

set -Eeuo pipefail

curl http://localhost:4000/health

echo ""

echo "LiteLLM OK"