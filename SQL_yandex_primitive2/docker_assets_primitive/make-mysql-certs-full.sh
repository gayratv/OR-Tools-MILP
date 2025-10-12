#!/usr/bin/env bash
set -euo pipefail

# Настройки
readonly DAYS="${DAYS:-825}"
readonly OUTDIR="/certs"

mkdir -p "$OUTDIR"
cd "$OUTDIR"

echo ">> Рабочая директория: $(pwd)" | tee -a /var/log/make-certs.log

# Проверка наличия CA
if [[ ! -f ca-key.pem ]]; then
  echo ">> Генерирую CA (корневой сертификат)..." | tee -a /var/log/make-certs.log
  openssl genrsa -out ca-key.pem 4096
  openssl req -new -x509 -key ca-key.pem -out ca.pem -days "$DAYS" -subj "/CN=MySQL-Local-CA"
  echo ">> CA-сертификаты сгенерированы." | tee -a /var/log/make-certs.log
else
  echo ">> Использую существующий CA." | tee -a /var/log/make-certs.log
fi

# Проверка наличия клиентских сертификатов
if [[ ! -f client-key.pem ]]; then
  echo ">> Генерирую клиентский ключ..." | tee -a /var/log/make-certs.log
  openssl genrsa -out client-key.pem 2048

  echo ">> Формирую CSR клиента..." | tee -a /var/log/make-certs.log
  openssl req -new -key client-key.pem -out client.csr -subj "/CN=client"

  echo ">> Подписываю клиентский сертификат нашим CA..." | tee -a /var/log/make-certs.log
  openssl x509 -req -in client.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
    -out client-cert.pem -days "$DAYS"

  rm -f client.csr

  echo ">> Клиентские сертификаты сгенерированы." | tee -a /var/log/make-certs.log
else
  echo ">> Использую существующие клиентские сертификаты." | tee -a /var/log/make-certs.log
fi

# Получаем IP из переменной окружения, если она есть, иначе пытаемся определить через curl
CURRENT_IP="${VM_EXTERNAL_IP:-$(curl -s ifconfig.co)}"
echo ">> Текущий внешний IP: $CURRENT_IP" | tee -a /var/log/make-certs.log

# Удаляем старые серверные сертификаты (если есть)
rm -f server-key.pem server-cert.pem server.csr

# SAN config (только IP)
cat > san.cnf <<EOF
[req]
default_bits = 2048
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = ${CURRENT_IP}

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = IP:${CURRENT_IP}
EOF

echo ">> Генерирую ключ сервера..." | tee -a /var/log/make-certs.log
openssl genrsa -out server-key.pem 2048

echo ">> Формирую CSR сервера (CN=${CURRENT_IP})..." | tee -a /var/log/make-certs.log
openssl req -new -key server-key.pem -out server.csr -config san.cnf -subj "/"

echo ">> Подписываю серверный сертификат нашим CA (IP: ${CURRENT_IP})..." | tee -a /var/log/make-certs.log
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem -days "$DAYS" -extfile san.cnf -extensions v3_req

rm -f server.csr san.cnf
cd - > /dev/null # Возвращаемся в исходную директорию

echo
echo "==== Серверные сертификаты обновлены! ==="  | tee -a /var/log/make-certs.log
#ls -l server-*.pem
echo
echo "==== Клиентские и CA сертификаты (не менялись): ===" | tee -a /var/log/make-certs.log
#ls -l ca-*.pem client-*.pem
echo
echo ">> Теперь можно запускать MySQL с новыми сертификатами." | tee -a /var/log/make-certs.log

#
#    # Устанавливаем владельца на сертификаты

RUN chown mysql:mysql /certs/ca.pem /certs/server-cert.pem /certs/server-key.pem && \
    chmod 644 /certs/ca.pem /certs/server-cert.pem && \
    chmod 600 /certs/server-key.pem

# Подключение с клиента:
# mysql --ssl-mode=VERIFY_IDENTITY
# --ssl-ca=ca.pem
# --ssl-cert=client-cert.pem
# --ssl-key=client-key.pem -h <IP> -u user -p