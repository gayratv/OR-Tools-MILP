#!/bin/bash
# Скрипт для загрузки всех файлов из локальной папки в Yandex Object Storage
# с сохранением поддиректорий и префикса ключа

# Проверка аргументов
if [ "$#" -ne 3 ]; then
    echo "Использование: $0 <bucket_name> <local_folder> <key_prefix>"
    echo "Пример: $0 mysql8-asset-files /mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex/mysql mysql"
    exit 1
fi

BUCKET_NAME="$1"
LOCAL_FOLDER="$2"
KEY_PREFIX="$3"

# Проверка, что папка существует
if [ ! -d "$LOCAL_FOLDER" ]; then
    echo "Ошибка: папка '$LOCAL_FOLDER' не существует."
    exit 1
fi

echo "Загрузка файлов из '$LOCAL_FOLDER' в бакет 's3://$BUCKET_NAME/$KEY_PREFIX/'..."

# Перебираем все файлы рекурсивно
find "$LOCAL_FOLDER" -type f | while read -r FILE; do
    # Относительный путь файла относительно корневой папки
    REL_PATH="${FILE#$LOCAL_FOLDER/}"

    # Полный путь в бакете
    DEST="s3://$BUCKET_NAME/$KEY_PREFIX/$REL_PATH"

    echo "→ Копирую: $FILE → $DEST"
    yc storage s3 cp "$FILE" "$DEST"
done

echo "✅ Все файлы успешно загружены."
