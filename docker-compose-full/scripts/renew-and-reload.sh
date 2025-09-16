#!/usr/bin/env bash
set -euo pipefail

# Путь к корню проекта (правьте при необходимости)
PROJECT_DIR="/home/user/mysql-on-vps"
cd "$PROJECT_DIR"

# 1) Продлить сертификаты (если требуется)
docker compose run --rm certbot certbot renew --webroot -w /var/www/certbot --quiet

# 2) Проверка конфига Nginx
docker compose exec -T nginx nginx -t

# 3) Перезагрузка Nginx, чтобы подхватить обновления
docker compose exec -T nginx nginx -s reload

echo "[renew] $(date '+%F %T') - done"
