#!/bin/bash
echo "Подключаюсь к $VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: $SECONDS сек."
export VM_EXTERNAL_IP=158.160.123.22
ssh -i ~/.ssh/ya-cloud/priv yc-user@158.160.123.22
