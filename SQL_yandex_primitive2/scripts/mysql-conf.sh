#!/usr/bin/env bash

rm -f ~/.my.cnf
VM_EXTERNAL_IP=${1:-158.160.33.153}

CERTS_DIR=/mnt/f/_prg/python/OR-Tools-MILP/SQL_yandex_primitive2/docker_assets_primitive/certs
PORT=3398
DB=school_sheduller

cat > "$HOME/.my.cnf" <<EOF
[clientappuser]
host=$VM_EXTERNAL_IP
port=$PORT
user=appuser
database=$DB
ssl-ca=$CERTS_DIR/ca.pem
ssl-cert=$CERTS_DIR/client-cert.pem
ssl-key=$CERTS_DIR/client-key.pem

[clientroot]
host=$VM_EXTERNAL_IP
port=$PORT
user=root
database=$DB
EOF

chmod 600 "$HOME/.my.cnf"
