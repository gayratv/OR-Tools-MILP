#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Usage:
#   sudo ./generate-mysql-certs-all.sh
#
# Description:
#   Генерирует полный комплект SSL-сертификатов для MySQL:
#     • CA (Certificate Authority)
#     • Серверный сертификат (CN = текущий внешний IP, SAN = IP, critical)
#     • Клиентский сертификат (CN = appuser, EKU = clientAuth)
#
#   Все файлы создаются в /certs:
#     ca.pem, ca-key.pem
#     server-cert.pem, server-key.pem
#     client-cert.pem, client-key.pem
#
#   После генерации:
#     - В MySQL (mysqld):
#         require_secure_transport = ON
#         ssl-ca   = /certs/ca.pem
#         ssl-cert = /certs/server-cert.pem
#         ssl-key  = /certs/server-key.pem
#
#     - В MySQL SQL:
#         ALTER USER 'appuser'@'%' REQUIRE
#           SUBJECT '/C=RU/O=MyOrg/CN=appuser'
#           AND ISSUER '/C=RU/O=MySQL/CN=MySQL-CA'
#           AND X509;
#
# Author: ChatGPT (for VPS + Docker + MySQL SSL)
# ==============================================================================

CERT_DIR="/app/SQL_yandex_primitive2/docker_assets_primitive/certs"
CLIENT_CN="appuser"

mkdir -p "$CERT_DIR"

echo "==> Определяем текущий внешний IP..."
CURRENT_IP="$(curl -s ifconfig.co)"
CURRENT_IP="${CURRENT_IP%%[^0-9.]*}" # на случай лишних символов

if ! [[ "$CURRENT_IP" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
  echo "❌ Ошибка: не удалось получить корректный IP, got '$CURRENT_IP'"
  exit 1
fi

echo "==> Используется IP: $CURRENT_IP"
echo "==> Каталог: $CERT_DIR"

rm -f "$CERT_DIR"/{ca.srl,server.csr,client.csr} || true

# === CA ===
echo "==> Генерируем CA..."
openssl genrsa -out "$CERT_DIR/ca-key.pem" 4096
openssl req -x509 -new -key "$CERT_DIR/ca-key.pem" -sha256 -days 3650 \
  -subj "/C=RU/O=MySQL/CN=MySQL-CA" -out "$CERT_DIR/ca.pem"

# === SERVER ===
echo "==> Генерируем серверный ключ..."
openssl genrsa -out "$CERT_DIR/server-key.pem" 2048

cat > "$CERT_DIR/openssl-server.cnf" <<EOF
[ req ]
default_bits       = 2048
distinguished_name = req_dn
req_extensions     = v3_server
prompt             = no

[ req_dn ]
C  = RU
O  = MyOrg
CN = ${CURRENT_IP}

[ v3_server ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = critical,@alt_names

[ alt_names ]
IP.1 = ${CURRENT_IP}
EOF

echo "==> Создаём CSR и подписываем серверный сертификат..."
openssl req -new -key "$CERT_DIR/server-key.pem" -out "$CERT_DIR/server.csr" -config "$CERT_DIR/openssl-server.cnf"

openssl x509 -req -in "$CERT_DIR/server.csr" \
  -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/server-cert.pem" -days 3650 -sha256 \
  -extensions v3_server -extfile "$CERT_DIR/openssl-server.cnf"

# === CLIENT ===
echo "==> Генерируем клиентский ключ для $CLIENT_CN..."
openssl genrsa -out "$CERT_DIR/client-key.pem" 2048

cat > "$CERT_DIR/openssl-client.cnf" <<EOF
[ req ]
default_bits       = 2048
distinguished_name = req_dn
req_extensions     = v3_client
prompt             = no

[ req_dn ]
C  = RU
O  = MyOrg
CN = ${CLIENT_CN}

[ v3_client ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

echo "==> Создаём CSR и подписываем клиентский сертификат..."
openssl req -new -key "$CERT_DIR/client-key.pem" -out "$CERT_DIR/client.csr" -config "$CERT_DIR/openssl-client.cnf"

openssl x509 -req -in "$CERT_DIR/client.csr" \
  -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/client-cert.pem" -days 3650 -sha256 \
  -extensions v3_client -extfile "$CERT_DIR/openssl-client.cnf"

# === Права и проверка ===
chmod 600 "$CERT_DIR"/{ca-key.pem,server-key.pem,client-key.pem}
chmod 644 "$CERT_DIR"/{ca.pem,server-cert.pem,client-cert.pem}

echo "==> Проверяем SAN сервера..."
openssl x509 -in "$CERT_DIR/server-cert.pem" -noout -text | grep -A2 "Subject Alternative Name"

echo "✅ Готово. Сертификаты созданы:"
ls -l "$CERT_DIR"
