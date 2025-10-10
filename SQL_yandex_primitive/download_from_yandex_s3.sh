#!/bin/bash
# Скрипт для скачивания всех файлов из Yandex Object Storage в локальную папку
# с сохранением структуры поддиректорий.

# Функция для вывода справки
usage() {
    echo "Использование: $0 [опции]"
    echo "  -b, --bucket <name>    Имя бакета в Yandex Object Storage"
    echo "  -f, --folder <path>    Локальная папка для сохранения файлов"
    echo "  -p, --prefix <prefix>  Префикс ключа (путь) в бакете для скачивания"
    echo "  -h, --help             Показать эту справку"
    echo ""
    echo "Пример: $0 --bucket mysql8-asset-files --folder /mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex/ --prefix mysql"
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

# Формируем путь к целевой локальной папке
# Она будет включать поддиректорию с именем префикса
TARGET_FOLDER="$LOCAL_FOLDER/$KEY_PREFIX"

# Создаем целевую локальную папку, если она не существует
mkdir -p "$TARGET_FOLDER"

S3_SOURCE="s3://$BUCKET_NAME/$KEY_PREFIX/"

echo "Скачивание файлов из '$S3_SOURCE' в '$TARGET_FOLDER'..."

# Рекурсивно копируем все объекты из бакета в целевую локальную папку
# Флаг --recursive указывает на копирование всех объектов с указанным префиксом
yc storage s3 cp --recursive "$S3_SOURCE" "$TARGET_FOLDER"

echo "✅ Скачивание завершено."
