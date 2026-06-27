#!/usr/bin/env bash
set -euo pipefail

curl --fail --silent --show-error --max-time 10 \
  http://127.0.0.1:3001/api/health >/dev/null
curl --fail --silent --show-error --max-time 10 \
  http://127.0.0.1:9090/-/ready >/dev/null
curl --fail --silent --show-error --max-time 10 \
  http://127.0.0.1:3100/ready >/dev/null

echo "Monitoring services are reachable."
