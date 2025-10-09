#!/usr/bin/env bash
set -euo pipefail
echo "--- Starting container entrypoint ---"

echo "--- Generating SSL certificates ---"
make-mysql-certs-full.sh

echo "--- Setting permissions for certificates ---"
# Устанавливаем правильного владельца и права на сгенерированные сертификаты
chown -R mysql:mysql /certs
chmod 600 /certs/*-key.pem
chmod 644 /certs/*-cert.pem /certs/ca.pem

echo "--- Permissions set. Handing over to MySQL daemon ---"

# Передаем управление стандартной точке входа образа mysql.
# mysqld будет запущен с правильными параметрами, включая --ssl-ca, --ssl-cert, --ssl-key,
# так как мы их указали в my.cnf.
exec docker-entrypoint.sh mysqld
