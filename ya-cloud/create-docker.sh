#!/bin/bash
#Создайте ВМ Linux:

# зарезервировать IP адрес:
# yc vpc address create --external-ipv4 zone=ru-central1-a
# ya-cloud/create-docker.sh

# Используем первый аргумент как имя ВМ, или 'default-docker-vm' если аргумент не передан.
VM_NAME=${1:-"gayrat-docker1"}

echo "Создание ВМ с именем: $VM_NAME" >&2

yc compute instance create-with-container \
  --name "$VM_NAME" \
  --zone ru-central1-a \
  --memory 4 \
  --cores 4 \
  --platform standard-v3 \
  --create-boot-disk size=30 \
  --ssh-key ~/.ssh/ya-cloud/priv.pub \
  --public-ip \
  --container-name=python312 \
  --container-image=gayrat/school_scheduler:latest \
  --container-command=sleep \
  --format json


#yc compute instance create-with-container \
#  --name gayrat-docker-python4 \
#  --zone ru-central1-a \
#  --platform highfreq-v4a \
#  --preemptible \
#  --memory 80 \
#  --cores 80 \
#  --create-boot-disk size=30 \
#  --ssh-key ~/.ssh/ya-cloud/priv.pub \
#  --public-ip \
#  --container-name=python312 \
#  --container-image=gayrat/school_scheduler:latest \
#  --container-command=sleep \
#  --format json