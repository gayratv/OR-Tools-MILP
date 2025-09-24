#!/usr/bin/env bash
set -euo pipefail
# ya-cloud/delete-used-ip.sh

# удаляет не используемые IP

yc vpc address list --format json \
| jq -r '.[] | select(.used != true) | .id' \
| xargs -r -n1 yc vpc address delete
