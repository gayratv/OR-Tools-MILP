#!/usr/bin/env bash
set -euo pipefail

# chmod +x make-mysql-certs.sh, затем запустите.

# ==== Настройки (правьте под себя) ====
DOMAIN="${DOMAIN:-example.com}"            # ваш домен
IP_ADDR="${IP_ADDR:-203.0.113.10}"         # публичный IP (можно оставить пустым)
DAYS="${DAYS:-825}"                        # срок действия
OUTDIR="${OUTDIR:-mysql/certs}"            # куда класть файлы

# ==== Подготовка ====
mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo ">> Генерирую CA (корневой сертификат)..."
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -key ca-key.pem -out ca.pem -days "$DAYS" -subj "/CN=MySQL-Local-CA"

echo ">> Генерирую ключ сервера..."
openssl genrsa -out server-key.pem 2048

echo ">> Формирую CSR сервера (CN=${DOMAIN})..."
openssl req -new -key server-key.pem -out server.csr -subj "/CN=${DOMAIN}"

# SAN (Subject Alternative Name) — домен и/или IP
SAN_FILE="san.cnf"
echo "subjectAltName=$(printf 'DNS:%s' "$DOMAIN")${IP_ADDR:+,IP:${IP_ADDR}}" > "$SAN_FILE"

echo ">> Подписываю серверный сертификат нашим CA (с SAN: $(cat $SAN_FILE))..."
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem -days "$DAYS" -extfile "$SAN_FILE"

# Права
chmod 600 server-key.pem ca-key.pem
chmod 644 ca.pem server-cert.pem

# Итог
echo
echo "==== Готово! Файлы в $(pwd):"
ls -l
echo
echo "Важное:"
echo " - Не коммитьте приватные ключи: ca-key.pem, server-key.pem"
echo " - Оставьте публичные: ca.pem, server-cert.pem (их можно раздавать клиентам)"
echo
echo "Дальше:"
echo " 1) В docker-compose.yml убедитесь, что монтируете каталог:"
echo "      - ./mysql/certs:/certs"
echo " 2) В mysql/conf.d/my.cnf включите TLS (раскомментируйте):"
echo "      require_secure_transport = ON"
echo "      ssl-ca   = /certs/ca.pem"
echo "      ssl-cert = /certs/server-cert.pem"
echo "      ssl-key  = /certs/server-key.pem"
echo " 3) Перезапустите MySQL:  docker compose down && docker compose up -d"
echo
echo "Проверка из контейнера:"
echo "  docker exec -it mysql8 mysql --ssl-mode=REQUIRED -uroot -p\"\$MYSQL_ROOT_PASSWORD\" -e \"SHOW STATUS LIKE 'Ssl_cipher';\""
echo
echo "Подключение с клиента (проверка CA):"
echo "  mysql --ssl-mode=VERIFY_IDENTITY --ssl-ca=$(pwd)/ca.pem -h ${DOMAIN} -P <порт> -u appuser -p"
