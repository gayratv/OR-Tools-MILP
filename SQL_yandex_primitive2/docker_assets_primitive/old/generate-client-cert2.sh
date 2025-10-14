#!/usr/bin/env bash
CERT_DIR="/certs"

echo "==> Генерируем клиентский ключ для appuser..."
openssl genrsa -out "$CERT_DIR/client-key.pem" 2048

echo "==> Пишем конфиг для клиентского cert (EKU: clientAuth)..."
cat > "$CERT_DIR/openssl-client.cnf" <<'EOF'
[ req ]
default_bits       = 2048
distinguished_name = req_dn
req_extensions     = v3_client
prompt             = no

[ req_dn ]
C  = RU
O  = MyOrg
CN = appuser

[ v3_client ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = clientAuth
EOF

echo "==> CSR и подпись клиентского сертификата..."
openssl req -new -key "$CERT_DIR/client-key.pem" \
  -out "$CERT_DIR/client.csr" -config "$CERT_DIR/openssl-client.cnf"

openssl x509 -req -in "$CERT_DIR/client.csr" \
  -CA "$CERT_DIR/ca.pem" -CAkey "$CERT_DIR/ca-key.pem" -CAcreateserial \
  -out "$CERT_DIR/client-cert.pem" -days 3650 -sha256 \
  -extensions v3_client -extfile "$CERT_DIR/openssl-client.cnf"

chmod 600 "$CERT_DIR/client-key.pem"
chmod 644 "$CERT_DIR/client-cert.pem"

# Проверка
# openssl x509 -in /certs/client-cert.pem -noout -subject -text | grep -E "Subject:|Extended Key Usage"
  ## Должно быть: Subject: CN=appuser ...  и Extended Key Usage: TLS Web Client Authentication
# Примечание: для клиентских сертификатов SAN не требуется — MySQL сверяет DN (Subject), поэтому мы задали CN=appuser.