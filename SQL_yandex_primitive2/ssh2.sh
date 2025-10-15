#!/bin/bash
echo "Подключаюсь к $VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: $SECONDS сек."
export VM_EXTERNAL_IP=84.252.128.161
ssh -i ~/.ssh/ya-cloud/priv yc-user@84.252.128.161
