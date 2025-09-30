#!/bin/sh
set -e

cd /home/appuser/yandex-cloud
export PATH="/home/appuser/yandex-cloud/bin:$PATH"

yc iam key create \
        --service-account-name sc-scheduller-srv-acc \
        --output key.json \
        --folder-id b1gbgjv35qvro3lmgaci

yc config profile create default
yc config set service-account-key key.json
yc config set cloud-id b1gib03pgvqrrfvhl3kb
yc config set folder-id b1gbgjv35qvro3lmgaci

cd /home/appuser/app
mkdir -p /home/appuser/app/output
python schedule_calculator.py

# Эта команда будет удерживать контейнер в рабочем состоянии
tail -f /dev/null
