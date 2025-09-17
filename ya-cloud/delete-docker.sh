#!/bin/bash
# Скрипт для удаления ВМ в Yandex Cloud

# ./ya-cloud/delete-docker.sh gayrat-docker2

# Используем первый аргумент как имя ВМ, или 'gayrat-docker1' если аргумент не передан.
VM_NAME=${1:-"gayrat-docker1"}

echo "Удаление ВМ с именем: $VM_NAME" >&2

yc compute instance delete \
  --name "$VM_NAME"