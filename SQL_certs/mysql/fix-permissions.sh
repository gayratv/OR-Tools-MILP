#!/bin/bash

# Проверяем, существуют ли файлы сертификатов, перед тем как менять права
if [ -f /certs/ca-key.pem ]; then
  echo "Fixing certificate permissions..."
  # Устанавливаем безопасные права на ключи и сертификаты
  chmod 600 /certs/*-key.pem
  chmod 644 /certs/*-cert.pem /certs/ca.pem
  echo "Permissions fixed."
else
  echo "Certificates not found, skipping permission fix."
fi

echo "Starting MySQL..."
# Запускаем оригинальный entrypoint MySQL, передавая ему все аргументы
exec docker-entrypoint.sh "$@"