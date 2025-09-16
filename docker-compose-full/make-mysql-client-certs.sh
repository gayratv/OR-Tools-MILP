#!/usr/bin/env bash
set -euo pipefail

# chmod +x make-mysql-client-certs.sh, затем запустите.

export DOMAIN="uroktime.store"
export IP_ADDR="217.12.38.229"
export OUTDIR="mysql/certs"

cd /docker-compose-full
OUTDIR="mysql/certs"   # подставьте ваш, если другой
DAYS=825               # как в скрипте
CN="appuser"           # можно любое описательное имя

cd "$OUTDIR"

# 1) Ключ клиента
openssl genrsa -out client-key.pem 2048

# 2) CSR клиента (укажем CN для удобства идентификации)
openssl req -new -key client-key.pem -out client.csr -subj "/CN=${CN}"

# 3) Расширения для клиентского серта (важно: extendedKeyUsage = clientAuth)
cat > client-ext.cnf <<'EOF'
basicConstraints=CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

# 4) Подписываем CSR клиентский тем же CA
openssl x509 -req -in client.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out client-cert.pem -days "$DAYS" -extfile client-ext.cnf

# Итоговые файлы:
#  - client-key.pem   (приватный ключ клиента)
#  - client-cert.pem  (сертификат клиента, подписанный вашим CA)
#  - ca.pem           (корневой CA — уже есть)
