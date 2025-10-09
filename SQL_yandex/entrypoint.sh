#!/usr/bin/env bash
set -euo pipefail

# Переходим в директорию yc, установленную для root
cd /root/yandex-cloud

yc iam key create \
        --service-account-name sc-scheduller-srv-acc \
        --output key.json \
        --folder-id b1gbgjv35qvro3lmgaci

yc config profile create default
yc config set service-account-key key.json
yc config set cloud-id b1gib03pgvqrrfvhl3kb
yc config set folder-id b1gbgjv35qvro3lmgaci

cd /app
yc-secrets-get.sh
set -a
source .env
set +a
make-mysql-certs-full.sh

## Эта команда будет удерживать контейнер в рабочем состоянии
tail -f /dev/null
