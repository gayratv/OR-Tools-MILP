#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# yc-secrets.sh
#
# Управляет секретами в Yandex Lockbox.
# Основная функция - создание секрета из локального .env файла.
#
# Пример использования:
#   ./ya-cloud/yc-secrets.sh my-app-secrets ../docker-compose-full/.env
# -------------------------------------------------------------------

need() { command -v "$1" >/dev/null 2>&1 || { echo "Ошибка: для работы скрипта требуется '$1'." >&2; exit 1; }; }
need jq

SECRET_NAME=${1:-"school-scheduler-app-secrets"}
ENV_FILE=${2:-"../docker-compose-full/.env"} # По умолчанию ищем .env в родительской директории

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Ошибка: Файл .env не найден по пути: $ENV_FILE" >&2
    exit 1
fi

# Функция для генерации JSON-payload из .env файла
# Использует jq для корректного и безопасного формирования JSON.
generate_payload() {
    # 1. Фильтруем .env: убираем комментарии и пустые строки.
    # 2. Для каждой строки 'KEY=VALUE':
    #    - Извлекаем KEY (до первого '=')
    #    - Извлекаем VALUE (всё после первого '=')
    # 3. С помощью jq создаём JSON-массив объектов.
    grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' | \
    jq -R -n '[inputs | capture("(?<key>[^=]+)=(?<value>.*)") | {key: .key, text_value: .value}]'
}

echo "Создание секрета '$SECRET_NAME' из файла $ENV_FILE..."

PAYLOAD_JSON=$(generate_payload)

# Для отладки можно вывести сгенерированный JSON
# echo "$PAYLOAD_JSON"

yc lockbox secret create \
  --name "$SECRET_NAME" \
  --description "Секреты для приложения, созданные из .env файла" \
  --payload "$PAYLOAD_JSON"
