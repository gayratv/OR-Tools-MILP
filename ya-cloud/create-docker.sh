#Создайте ВМ Linux:

# зарезервировать IP адрес:
# yc vpc address create --external-ipv4 zone=ru-central1-a
# ya-cloud/create-docker.sh

#yc compute instance create-with-container \
#  --name gayrat-docker-python1 \
#  --zone ru-central1-a \
#  --memory 16 \
#  --cores 16 \
#  --create-boot-disk size=30 \
#  --ssh-key ~/.ssh/ya-cloud/priv.pub \
#  --public-ip \
#  --platform standard-v3 \
#  --container-name=python312 \
#  --container-image=gayrat/school_scheduler:latest \
#  --container-command=sleep


yc compute instance create-with-container \
  --name gayrat-docker-python1 \
  --zone ru-central1-a \
  --platform highfreq-v4a \
  --preemptible \
  --memory 48 \
  --cores 48 \
  --create-boot-disk size=30 \
  --ssh-key ~/.ssh/ya-cloud/priv.pub \
  --public-ip \
  --container-name=python312 \
  --container-image=gayrat/school_scheduler:latest \
  --container-command=sleep