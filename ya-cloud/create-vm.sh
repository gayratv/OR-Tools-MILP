#Создайте ВМ Linux:
#yc compute instance create --help
# ya-cloud/create-vm.sh

#--platform "Intel Ice Lake Compute-Optimized" \
#--network-interface subnet-name=default-ru-central1-a,nat-ip-version=ipv4,ipv4-address=nat \
# max ядер - 80

#yc compute instance create \
#  --name gayrat1 \
#  --preemptible \
#  --public-ip \
#  --create-boot-disk image-folder-id=standard-images,image-id=fd80bm0rh4rkepi5ksdi,size=22GB \
#  --platform highfreq-v4a \
#  --zone ru-central1-a \
#  --memory 4 \
#  --cores 2 \
#  --ssh-key ~/.ssh/ya-cloud/priv.pub


# зарезервировать IP адрес:
# yc vpc address create --external-ipv4 zone=ru-central1-a

yc compute instance create \
  --name gayrat1 \
  --preemptible \
  --public-ip \
  --create-boot-disk image-folder-id=standard-images,image-id=fd888dplf7gt1nguheht,size=30GB \
  --zone ru-central1-a \
  --memory 2 \
  --cores 2 \
  --ssh-key ~/.ssh/ya-cloud/priv.pub