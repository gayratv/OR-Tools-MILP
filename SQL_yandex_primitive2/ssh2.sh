#!/bin/bash
echo "Подключаюсь к $VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: $SECONDS сек."
export VM_EXTERNAL_IP=46.21.244.190
ssh -i ~/.ssh/ya-cloud/priv yc-user@46.21.244.190
