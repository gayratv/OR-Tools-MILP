#!/usr/bin/env bash
set -euo pipefail

# -------------------------------------------------------------------
# create-docker.sh
# Создаёт ВМ в Yandex Cloud и экспортирует внешний IP в VM_EXTERNAL_IP.
#
# Упрощённый ввод платформы:
#   std  → standard-v3   (по умолчанию)
#   hf   → highfreq-v4a
#
# Примеры:
#   ./create-docker.sh myvm std
#   ./create-docker.sh myvm hf 4 16 50
# -------------------------------------------------------------------

# ./ya-cloud/create-docker.sh gayrat-docker1 16 4 50 std
# ./ya-cloud/create-docker.sh gayrat-docker3 std 2 2 20
# ./ya-cloud/create-docker.sh gayrat-docker1 hf 80 80 30


# -------- Параметры с дефолтами --------------------------------------
VM_NAME=${1:-"gayrat-docker1"}

# Платформа: std / hf
PLATFORM_KEY=${2:-"std"}

# Остальные параметры
CORES=${3:-2}
MEMORY=${4:-2}     # ГБ
DISK_SIZE=${5:-20} # ГБ

# -------- Маппинг платформы ------------------------------------------
case "$PLATFORM_KEY" in
  std|s|standard) PLATFORM="standard-v3" ;;
  hf|h|highfreq)  PLATFORM="highfreq-v4a" ;;
  *)
    echo "Неизвестная платформа: $PLATFORM_KEY" >&2
    echo "Допустимые: std (standard-v3), hf (highfreq-v4a)" >&2
    exit 1
    ;;
esac

# -------- Проверки окружения -----------------------------------------
need() { command -v "$1" >/dev/null 2>&1 || { echo "Требуется '$1'." >&2; exit 1; }; }
need yc
need jq

echo "Создание ВМ: name=${VM_NAME}, platform=${PLATFORM}, cores=${CORES}, mem=${MEMORY}GB, disk=${DISK_SIZE}GB" >&2

# -------- Создание ВМ ------------------------------------------------
# Передаем user-data и подставляем в него переменную ssh_key из файла --metadata-from-file

RESP=$(
  yc compute instance create \
    --name "$VM_NAME" \
    --zone ru-central1-a \
    --platform "$PLATFORM" \
    --preemptible \
    --memory "$MEMORY" \
    --cores "$CORES" \
    --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2204-lts,size="$DISK_SIZE" \
    --public-ip \
    --service-account-name sc-scheduller-srv-acc \
    --metadata-from-file user-data=./ya-cloud/cloud-init.yaml \
    --format json
)

# -------- Парсинг JSON ------------------------------------------------
VM_EXTERNAL_IP=$(jq -r 'first(.network_interfaces[].primary_v4_address.one_to_one_nat.address // empty)' <<< "$RESP")

export VM_EXTERNAL_IP

echo "----------------------------------------"
echo "VM создана:"
jq -r '.id as $id
       | "  ID:        \($id)\n  Name:      " + .name
       + "\n  Status:    " + .status
       + "\n  FQDN:      " + (.fqdn // "")
       + "\n  Internal:  " + (first(.network_interfaces[].primary_v4_address.address // empty) // "")
       + "\n  External:  " + (first(.network_interfaces[].primary_v4_address.one_to_one_nat.address // empty) // "")' <<< "$RESP"
echo "----------------------------------------"
echo "Экспортировано: VM_EXTERNAL_IP=${VM_EXTERNAL_IP}"

echo "Ожидание доступности SSH на ${VM_EXTERNAL_IP}:22..."

#ATTEMPTS=0
#MAX_ATTEMPTS=30 # ~1 минута
#
#while ! nc -z -w 2 "$VM_EXTERNAL_IP" 22 && [[ $ATTEMPTS -lt $MAX_ATTEMPTS ]]; do
#  sleep 2
#  ATTEMPTS=$((ATTEMPTS + 1))
#  printf "."
#done
#
#echo "" # Новая строка после точек
#
#if [[ $ATTEMPTS -eq $MAX_ATTEMPTS ]]; then
#  echo "Ошибка: не удалось дождаться запуска SSH-сервера на ВМ." >&2
#  exit 1
#fi
#
#echo "SSH-сервер готов. Можно подключаться."
