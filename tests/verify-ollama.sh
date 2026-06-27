#!/usr/bin/env bash

set -Eeuo pipefail

curl http://localhost:11434/api/tags

echo ""

echo "Ollama OK"