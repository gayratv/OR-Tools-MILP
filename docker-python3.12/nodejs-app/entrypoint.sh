#!/bin/sh
# Выходим при любой ошибке
set -e

# Конфигурируем Yandex Cloud CLI
yc config set service-account-key ${YC_SERVICE_ACCOUNT_KEY_FILE}
yc config set folder-id b1gbgjv35qvro3lmgaci
yc config set cloud-id b1gib03pgvqrrfvhl3kb
# Запускаем команду, переданную в CMD (или в docker run)
exec "$@"