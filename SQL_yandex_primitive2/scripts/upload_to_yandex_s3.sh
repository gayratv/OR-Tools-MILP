#!/bin/bash
# Скрипт для загрузки всех файлов из локальной папки в Yandex Object Storage
# с сохранением поддиректорий и префикса ключа

# Функция для вывода справки
usage() {
    echo "Использование: $0 [опции]"
    echo "  -b, --bucket <name>    Имя бакета в Yandex Object Storage"
    echo "  -f, --folder <path>    Локальная папка с файлами для загрузки (не используется с --delete)"
    echo "  -p, --prefix <prefix>  Префикс ключа (путь) в бакете"
    echo "  -d, --delete           Удалить все объекты по указанному префиксу в бакете"
    echo "  -h, --help             Показать эту справку"
    echo ""
    echo "Пример загрузки: $0 --bucket my-bucket --folder /path/to/files --prefix my-prefix"
    echo "Пример удаления: $0 --bucket my-bucket --prefix my-prefix --delete"
    exit 1
}

# Переменные для опций
DELETE_FLAG=0

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
        -d|--delete)
        DELETE_FLAG=1
        shift # past argument
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

# Проверка, что базовые обязательные аргументы предоставлены
if [ -z "${BUCKET_NAME}" ] || [ -z "${KEY_PREFIX}" ]; then
    echo "Ошибка: не указаны обязательные параметры --bucket и --prefix."
    usage
fi

#if [ "$DELETE_FLAG" -eq 1 ]; then
#    # Логика удаления
#    echo "Внимание: вы собираетесь удалить все объекты в 's3://$BUCKET_NAME/$KEY_PREFIX/'.'"
#    read -p "Вы уверены? [y/N] " -n 1 -r
#    echo # перенос строки
#    if [[ $REPLY =~ ^[Yy]$ ]]; then
#        echo "Удаление объектов из 's3://$BUCKET_NAME/$KEY_PREFIX/'.'"
#        yc storage s3 rm "s3://$BUCKET_NAME/$KEY_PREFIX/" --recursive
#        echo "✅ Удаление завершено."
#    else
#        echo "Удаление отменено."
#        exit 0
#    fi

if [ "$DELETE_FLAG" -eq 1 ]; then
    # Логика удаления
    echo "Внимание: вы собираетесь удалить все объекты в 's3://$BUCKET_NAME/$KEY_PREFIX/'.'"
    echo "Удаление объектов из 's3://$BUCKET_NAME/$KEY_PREFIX/'.'"
    yc storage s3 rm "s3://$BUCKET_NAME/$KEY_PREFIX/" --recursive
    echo "✅ Удаление завершено."
else
    # Логика загрузки (существующий код)
    # Проверка, что папка для загрузки указана
    if [ -z "${LOCAL_FOLDER}" ]; then
        echo "Ошибка: для загрузки необходимо указать параметр --folder."
        usage
    fi

    # Проверка, что папка существует
    if [ ! -d "$LOCAL_FOLDER" ]; then
        echo "Ошибка: папка '$LOCAL_FOLDER' не существует."
        exit 1
    fi

    echo "Загрузка файлов из '$LOCAL_FOLDER' в бакет 's3://$BUCKET_NAME/$KEY_PREFIX/'.'"

    # Перебираем все файлы рекурсивно, исключая .env
    find "$LOCAL_FOLDER" -type f -not -name ".env" | while read -r FILE; do
        # Относительный путь файла относительно корневой папки
        REL_PATH="${FILE#$LOCAL_FOLDER/}"
        # Полный путь в бакете
        DEST="s3://$BUCKET_NAME/$KEY_PREFIX/$REL_PATH"
        echo "→ Копирую: $FILE → $DEST"
        yc storage s3 cp "$FILE" "$DEST"
    done

    echo "✅ Все файлы успешно загружены."
fi
