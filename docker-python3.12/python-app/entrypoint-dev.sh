#!/bin/sh
set -e

yc config set service-account-key /etc/yc/sa_key.json
yc config set folder-id b1gbgjv35qvro3lmgaci
yc config set cloud-id b1gib03pgvqrrfvhl3kb

mkdir -p /home/appuser/app/output

echo "Контейнер успешно стартовал и ожидает команд."

yc-secrets-get.sh

#python rasp_or_tools.py

# Эта команда будет удерживать контейнер в рабочем состоянии
tail -f /dev/null
