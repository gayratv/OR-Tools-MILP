#!/usr/bin/env bash

rm -f ~/.my.cnf
VM_EXTERNAL_IP=${1:-158.160.33.153}

cat >> ~/.my.cnf << EOF
[clientappuser]
host=$VM_EXTERNAL_IP
port=3398
user=appuser
database=school_sheduller
ssl-ca=/mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex_primitive2/docker_assets_primitive/certs/ca.pem
ssl-cert=/mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex_primitive2/docker_assets_primitive/certs/client-cert.pem
ssl-key=/mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex_primitive2/docker_assets_primitive/certs/client-key.pem

[clientroot]
host=$VM_EXTERNAL_IP
port=3398
user=root
database=school_sheduller

EOF
