#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# yc-secrets.sh
#
# Управляет секретами в Yandex Lockbox.
# Основная функция - создание секрета из локального .env файла.
#
# Пример использования:
#   ./ya-cloud/yc-secrets.sh create my-app-secrets
# -------------------------------------------------------------------

SECRET_NAME=${1:-"my-app-secrets"}
ENV_FILE="../docker-compose-full/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Ошибка: Файл .env не найден по пути: $ENV_FILE" >&2
    exit 1
fi

generate_payload() {
    local entries=()
    # Читаем .env, игнорируя комментарии и пустые строки
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        # Пропускаем комментарии и пустые строки
        [[ "$key" =~ ^\s*#.*$ ]] && continue
        [[ -z "$key" ]] && continue

        # Формируем запись для JSON, экранируя одинарные кавычки в значении
        local escaped_value="${value//\'/\'\\\'\'}"
        entries+=("{'key': '$key', 'text_value': '$escaped_value'}")
    done < <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')

    # Объединяем все записи в одну строку через запятую
    local joined_entries
    joined_entries=$(IFS=,; echo "${entries[*]}")

    echo "--payload \"[${joined_entries}]\""
}

#echo "Создание секрета '$SECRET_NAME' из файла $ENV_FILE..."
#yc lockbox secret create \
# --name "$SECRET_NAME" \
# --description "Секреты для приложения, созданные из .env файла" \
# $(generate_payload)

echo $(generate_payload)
