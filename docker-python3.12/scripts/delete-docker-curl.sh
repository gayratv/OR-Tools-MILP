#!/bin/bash
# Скрипт для удаления ВМ в Yandex Cloud
# Имя ВМ берём из метаданных GCP

# Получаем имя инстанса
VM_NAME=$(curl -s -H "Metadata-Flavor: Google" \
  "http://169.254.169.254/computeMetadata/v1/instance/name")

# Проверяем успешность запроса
if [[ -z "$VM_NAME" ]]; then
  echo "Ошибка: не удалось получить имя инстанса через YC CLI." >&2
  exit 1
fi

echo "Запрос на удаление текущей ВМ с ID: $VM_NAME" >&2

yc compute instance delete --name "$VM_NAME"
