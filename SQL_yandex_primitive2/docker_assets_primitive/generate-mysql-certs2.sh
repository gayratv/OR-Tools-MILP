#!/bin/bash
set -e

CERT_DIR="/certs"
mkdir -p "$CERT_DIR"

echo "==> Генерируем CA..."
openssl genrsa -out "$CERT_DIR/ca-key.pem" 4096
openssl req -x509 -new -nodes -key "$CERT_DIR/ca-key.pem" -sha256 -days 3650 \
  -subj "/C=RU/O=MySQL/CN=MySQL-CA" -out "$CERT_DIR/ca.pem"

echo "==> Генерируем серверный ключ..."
openssl genrsa -out "$CERT_DIR/server-key.pem" 2048

CURRENT_IP="$(curl -s ifconfig.co)}"
echo ">> Текущий внешний IP: $CURRENT_IP" | tee -a /var/log/make-certs.log

echo "==> Создаём конфиг для SAN..."
cat > "$CERT_DIR/openssl.cnf" <<EOF
[ req ]
default_bits       = 2048
distinguished_name = req_distinguished_name
req_extensions     = v3_req
prompt = no

[ req_distinguished_name ]
C  = RU
O  = MySQL
CN = ${CURRENT_IP}

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = critical,@alt_names

[ alt_names ]
IP.1  = ${CURRENT_IP}
EOF

echo "==> Генерируем запрос и сертификат сервера..."
openssl req -new -key "$CERT_DIR/server-key.pem" -out "$CERT_DIR/server.csr" \
  -config "$CERT_DIR/openssl.cnf"

openssl x509 -req -in "$CERT_DIR/server.csr" \
  -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/server-cert.pem" -days 3650 -sha256 \
  -extensions v3_req -extfile "$CERT_DIR/openssl.cnf"

chmod 600 "$CERT_DIR"/*.pem

echo "==> Проверяем результат:"
openssl x509 -in "$CERT_DIR/server-cert.pem" -noout -subject -text | grep -A3 "Subject Alternative Name"

echo "✅ Сертификаты готовы:"
ls -l "$CERT_DIR"

chown mysql:mysql /certs/ca.pem /certs/server-cert.pem /certs/server-key.pem && \
    chmod 644 /certs/ca.pem /certs/server-cert.pem && \
    chmod 600 /certs/server-key.pem