#!/usr/bin/bash
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1 || { echo "Ошибка: требуется '$1'." >&2; exit 1; }; }
need jq
need yc
need base64

YC_DIR=/home/yc-user/yandex-cloud/bin

# Устанавливаем имя выходного файла.
# Используем первый аргумент командной строки ($1), если он есть.
# В противном случае, используем ".env" по умолчанию.
OUTPUT_ENV_FILE="${1:-./.env}"

# Директория для восстановленных бинарных файлов (сертификатов).
OUTPUT_BINARY_DIR="${2:-./.mysql-out}"

# Извлекаем путь к директории из имени файла.
OUTPUT_ENV_DIR=$(dirname "$OUTPUT_ENV_FILE")

# Создаем директорию, если она не существует.
mkdir -p "$OUTPUT_ENV_DIR"
mkdir -p "$OUTPUT_BINARY_DIR"

# 1. Получаем весь payload секрета в виде одного JSON
echo "Получаю секреты из Yandex Lockbox..."
PAYLOAD_JSON=$(${YC_DIR}/yc lockbox payload get school-scheduler-app-secrets --format json)

# 2. Извлекаем и сохраняем текстовые значения в .env файл
echo "Восстанавливаю текстовые переменные в '$OUTPUT_ENV_FILE'..."
echo "$PAYLOAD_JSON" | \
  jq -r '
    .entries[]
    | select(.text_value != null)
    | "\(.key)=\"\(.text_value | gsub("\\r$"; ""))\""
  ' > "$OUTPUT_ENV_FILE"


# 3. Извлекаем и сохраняем бинарные файлы (сертификаты)
echo "Восстанавливаю бинарные файлы в '$OUTPUT_BINARY_DIR'..."
echo "$PAYLOAD_JSON" | \
  jq -c '
    .entries[]
    | select(.binary_value != null)
    | {key: .key, value: .binary_value}
  ' | while read -r line; do
      key=$(echo "$line" | jq -r '.key')
      value_b64=$(echo "$line" | jq -r '.value')
      output_path="$OUTPUT_BINARY_DIR/$key"

      echo " -> $output_path"
      echo "$value_b64" | base64 --decode > "$output_path"
done

echo "Готово."
echo "Файл окружения: $OUTPUT_ENV_FILE"
echo "Бинарные файлы: $OUTPUT_BINARY_DIR"