#!/usr/bin/bash

# Устанавливаем имя выходного файла.
# Используем первый аргумент командной строки ($1), если он есть.
# В противном случае, используем ".env" по умолчанию.
OUTPUT_FILE="${1:-./responce/.env}"

#yc lockbox secret get school-scheduler-app-secrets
#yc lockbox payload get school-scheduler-app-secrets

# Запрашиваем секреты в формате JSON, обрабатываем их с помощью jq
# и сразу записываем в указанный файл.
# Этот подход намного эффективнее, чем многократный парсинг текста.
#
# Добавляем `gsub("\\r"; "")` в команду jq, чтобы удалить символы возврата каретки (\r),
# которые Yandex Lockbox может добавлять в конец текстовых значений.
yc lockbox payload get school-scheduler-app-secrets --format json | \
  jq -r '.entries[] | "\(.key)=\"\(.text_value | gsub("\\r"; ""))\u0022"' > "$OUTPUT_FILE"

echo "Файл '$OUTPUT_FILE' успешно создан."