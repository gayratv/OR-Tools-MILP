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
    --docker-compose-file docker-compose.yml \
    --metadata-from-file user-data=cloud-init-compose.yaml \
    --metadata SECRET_ID=e6qdqbmm78930tvi4kdj \
    --format json
)

VM_EXTERNAL_IP=$(jq -r 'first(.network_interfaces[].primary_v4_address.one_to_one_nat.address // empty)' <<< "$RESP")
export VM_EXTERNAL_IP

echo "----------------------------------------"
echo "ВМ создана, внешний IP: $VM_EXTERNAL_IP"
echo "----------------------------------------"
