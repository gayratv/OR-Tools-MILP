#!/bin/bash
echo "Подключаюсь к $VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: $SECONDS сек."
export VM_EXTERNAL_IP=
ssh -i ~/.ssh/ya-cloud/priv yc-user@
