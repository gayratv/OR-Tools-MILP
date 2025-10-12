#!/bin/bash
echo "Подключаюсь к $VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: $SECONDS сек."
export VM_EXTERNAL_IP=51.250.86.32
ssh -i ~/.ssh/ya-cloud/priv yc-user@51.250.86.32
