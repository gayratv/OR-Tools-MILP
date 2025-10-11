#!/bin/bash
# Скрипт для загрузки всех файлов из локальной папки в Yandex Object Storage
# с сохранением поддиректорий и префикса ключа

# Функция для вывода справки
usage() {
    echo "Использование: $0 [опции]"
    echo "  -b, --bucket <name>    Имя бакета в Yandex Object Storage"
    echo "  -f, --folder <path>    Локальная папка с файлами для загрузки"
    echo "  -p, --prefix <prefix>  Префикс ключа (путь) в бакете"
    echo "  -h, --help             Показать эту справку"
    echo ""
    echo "Пример: $0 --bucket mysql8-asset-files --folder /mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex/mysql --prefix mysql"
    exit 1
}

# Парсинг аргументов командной строки
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -b|--bucket)
        BUCKET_NAME="$2"
        shift # past argument
        shift # past value
        ;;
        -f|--folder)
        LOCAL_FOLDER="$2"
        shift # past argument
        shift # past value
        ;;
        -p|--prefix)
        KEY_PREFIX="$2"
        shift # past argument
        shift # past value
        ;;
        -h|--help)
        usage
        ;;
        *)
        echo "Неизвестный параметр: $1"
        usage
        ;;
    esac
done

# Проверка, что все обязательные аргументы предоставлены
if [ -z "${BUCKET_NAME}" ] || [ -z "${LOCAL_FOLDER}" ] || [ -z "${KEY_PREFIX}" ]; then
    echo "Ошибка: не все обязательные параметры указаны."
    usage
fi


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
