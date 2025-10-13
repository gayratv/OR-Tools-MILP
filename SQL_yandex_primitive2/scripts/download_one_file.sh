#!/bin/bash
# Скрипт для скачивания одного файла из Yandex Object Storage.

# Функция для вывода справки
usage() {
    echo "Использование: $0 <имя_файла_в_бакете> <целевая_директория>"
    echo ""
    echo "Пример: $0 SQL_yandex_primitive2/some_file.txt /app/data"
    exit 1
}

# Проверка, что передано два аргумента
if [ "$#" -ne 2 ]; then
    echo "Ошибка: неверное количество аргументов."
    usage
fi

FILE_KEY="$1"
TARGET_DIR="$2"
BUCKET_NAME="mysql8-asset-files"

mkdir -p "$TARGET_DIR"

S3_SOURCE="s3://$BUCKET_NAME/$FILE_KEY"
LOCAL_DESTINATION="$TARGET_DIR/$(basename "$FILE_KEY")"

echo "Скачивание файла '$S3_SOURCE' в '$LOCAL_DESTINATION'..."

# Скачиваем один файл
/home/yc-user/yandex-cloud/bin/yc storage s3 cp "$S3_SOURCE" "$LOCAL_DESTINATION"

echo "✅ Скачивание завершено."
