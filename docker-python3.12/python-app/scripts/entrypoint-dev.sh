#!/bin/sh
set -e

yc config set service-account-key /etc/yc/sa_key.json
yc config set folder-id b1gbgjv35qvro3lmgaci
yc config set cloud-id b1gib03pgvqrrfvhl3kb

# создана в Dockerfile
#mkdir -p /app/output

echo "Контейнер успешно стартовал и ожидает команд."

yc-secrets-get.sh

#python schedule_calculator.py

# Эта команда будет удерживать контейнер в рабочем состоянии
tail -f /dev/null
