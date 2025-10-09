#!/usr/bin/env bash
set -euo pipefail
echo "--- Starting container entrypoint ---"

exec docker-entrypoint.sh mysqld
