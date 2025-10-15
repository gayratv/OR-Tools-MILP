#!/usr/bin/env bash

# выполнить на Host

TOTAL_SECONDS=1

echo "Запускаю таймер на $TOTAL_SECONDS секунд..."
# Цикл для обратного отсчета
for (( i=$TOTAL_SECONDS; i>0; i-- )); do
    # Выводим оставшееся время в ту же строку
    # Используем printf для надежной обработки \r (возврат каретки)
    printf "Осталось: %s секунд...  \r" "$i"
    sleep 1
done

# Очищаем строку с таймером и переходим на новую
echo -e "\r"

# Выводим финальное сообщение
echo "Прошло $TOTAL_SECONDS секунд!"



VM_NAME=${1:-mysql8_3}
export VM_EXTERNAL_IP=$(yc compute instance get --name "$VM_NAME" --format json | jq -r '.network_interfaces[].primary_v4_address.one_to_one_nat.address')
echo $VM_EXTERNAL_IP

# копирование сертфикатов
ssh -i ~/.ssh/ya-cloud/priv yc-user@$VM_EXTERNAL_IP \
  "sudo chmod +r /app/SQL_yandex_primitive2/docker_assets_primitive/certs/client-key.pem"

scp -i ~/.ssh/ya-cloud/priv -r \
 yc-user@$VM_EXTERNAL_IP:/app/SQL_yandex_primitive2/docker_assets_primitive/certs \
  /mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex_primitive2/docker_assets_primitive/

# === создать пользовательские конфигурации
# выполнить на Host
cd /mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex_primitive2

./scripts/mysql-conf.sh $VM_EXTERNAL_IP
# создать appuser
./SQL/deploy-user.sh ./SQL/app-user.sql

# restore database
./scripts/restore_school_db.sh

echo "VM_EXTERNAL_IP: $VM_EXTERNAL_IP"