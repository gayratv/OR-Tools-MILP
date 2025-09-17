#!/bin/bash
#Создайте ВМ Linux:

# зарезервировать IP адрес:
# yc vpc address create --external-ipv4 zone=ru-central1-a
# ya-cloud/create-docker.sh

# 16 ГБ RAM, 4 ядра, 50 ГБ диск
# ./ya-cloud/create-docker.sh gayrat-docker1 16 4 50 standard-v3
# ./ya-cloud/create-docker.sh gayrat-docker2 2 2 20 standard-v3
# ./ya-cloud/create-docker.sh gayrat-docker1 80 80 30 highfreq-v4a
    

# Используем первый аргумент как имя ВМ, или 'default-docker-vm' если аргумент не передан.
VM_NAME=${1:-"gayrat-docker1"}
# Используем второй аргумент для памяти (в ГБ), по умолчанию 80.
MEMORY=${2:-2}
# Используем третий аргумент для количества ядер, по умолчанию 80.
CORES=${3:-2}
# Используем четвертый аргумент для размера диска (в ГБ), по умолчанию 30.
DISK_SIZE=${4:-20}

PLATFORM=${5:-"standard-v3"}

echo "Создание ВМ с именем: $VM_NAME, Память: ${MEMORY}GB, Ядра: $CORES, Диск: ${DISK_SIZE}GB" >&2

yc compute instance create-with-container \
  --name "$VM_NAME" \
  --zone ru-central1-a \
  --platform "$PLATFORM" \
  --preemptible \
  --memory "$MEMORY" \
  --cores "$CORES" \
  --create-boot-disk size=$DISK_SIZE \
  --ssh-key ~/.ssh/ya-cloud/priv.pub \
  --public-ip \
  --container-name=python312 \
  --container-image=gayrat/school_scheduler:latest \
  --container-command=sleep \
  --format json