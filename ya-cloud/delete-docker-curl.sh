#!/bin/bash
# Скрипт для удаления ВМ в Yandex Cloud
# Имя ВМ берём из метаданных GCP

# Получаем ID текущего инстанса (ВМ, на которой запущен скрипт) через YC CLI.
# Это надежнее, чем curl, так как использует настроенный SDK.
INSTANCE_ID=$(yc compute instance get-credentials --format json | jq -r .instance_id)

# Проверяем успешность запроса
if [[ -z "$INSTANCE_ID" ]]; then
  echo "Ошибка: не удалось получить ID инстанса через YC CLI." >&2
  exit 1
fi

echo "Запрос на удаление текущей ВМ с ID: $INSTANCE_ID" >&2

yc compute instance delete --id "$INSTANCE_ID"
