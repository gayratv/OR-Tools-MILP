#!/bin/bash
echo "Подключаюсь к $VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: $SECONDS сек."
export VM_EXTERNAL_IP=158.160.40.209
ssh -i ~/.ssh/ya-cloud/priv yc-user@158.160.40.209
