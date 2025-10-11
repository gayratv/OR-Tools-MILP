#!/usr/bin/env bash
set -euo pipefail

VM_NAME=${1:-"mysql8"}
PLATFORM_KEY=${2:-"std"}
CORES=${3:-2}
MEMORY=${4:-2}
DISK_SIZE=${5:-20}

case "$PLATFORM_KEY" in
  std|s|standard) PLATFORM="standard-v3" ;;
  hf|h|highfreq)  PLATFORM="highfreq-v4a" ;;
  *) echo "Неизвестная платформа: $PLATFORM_KEY" >&2; exit 1 ;;
esac

need() { command -v "$1" >/dev/null 2>&1 || { echo "Требуется '$1'." >&2; exit 1; }; }
need yc
need jq

SSH_PUBLIC_KEY_PATH="$HOME/.ssh/ya-cloud/priv.pub"
[[ -f "$SSH_PUBLIC_KEY_PATH" ]] || { echo "Нет ключа $SSH_PUBLIC_KEY_PATH"; exit 1; }

echo "Создаю ВМ $VM_NAME ($PLATFORM ${CORES}CPU/${MEMORY}GB/$DISK_SIZE GB)..."

RESP=$(
  yc compute instance create-with-container \
    --name "$VM_NAME" \
    --zone ru-central1-a \
    --platform "$PLATFORM" \
    --preemptible \
    --memory "$MEMORY" \
    --cores "$CORES" \
    --create-boot-disk size=$DISK_SIZE \
    --public-ip \
    --service-account-name sc-scheduller-srv-acc \
    --metadata-from-file user-data=cloud-init-compose2.yaml \
    --metadata "ssh-keys=yc-user:$(cat "$HOME/.ssh/ya-cloud/priv.pub")" \
    --metadata secret_id=e6qdqbmm78930tvi4kdj \
    --format json \
    --container-image alpine:3 \
    --container-command sh \
    --container-arg -c \
    --container-arg "sleep infinity"
)

VM_EXTERNAL_IP=$(jq -r 'first(.network_interfaces[].primary_v4_address.one_to_one_nat.address // empty)' <<< "$RESP")
export VM_EXTERNAL_IP

cat <<EOF > ssh2.sh
#!/bin/bash
echo "Подключаюсь к \$VM_EXTERNAL_IP..."
echo "Время выполнения скрипта: \$SECONDS сек."
export VM_EXTERNAL_IP=$VM_EXTERNAL_IP
ssh -i ~/.ssh/ya-cloud/priv yc-user@$VM_EXTERNAL_IP
EOF

echo "----------------------------------------"
echo "ВМ создана, внешний IP: $VM_EXTERNAL_IP"
echo "----------------------------------------"

# Общее время в секундах
TOTAL_SECONDS=70

echo "Запускаю таймер на $TOTAL_SECONDS секунд..."
# Цикл для обратного отсчета
for (( i=$TOTAL_SECONDS; i>0; i-- )); do
    # Выводим оставшееся время в ту же строку
    # Используем printf для надежной обработки \r (возврат каретки)
    printf "Осталось: %s секунд...  \r" "$i"
    sleep 1
done

# Очищаем строку с таймером и переходим на новую
echo "                                \r"

# Выводим финальное сообщение
echo "Прошло $TOTAL_SECONDS секунд!"
ssh -i ~/.ssh/ya-cloud/priv yc-user@"$VM_EXTERNAL_IP"