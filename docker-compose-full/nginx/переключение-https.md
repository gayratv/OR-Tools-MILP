Как переключаться между режимами

# HTTP-режим (по умолчанию, без сертификата):

# оставьте только HTTP-конфиг активным
mv nginx/conf.d/app.https.conf nginx/conf.d/app.https.conf.off 2>/dev/null || true
docker compose exec -T nginx nginx -t && docker compose exec -T nginx nginx -s reload

# Переход на HTTPS:

# верните https-конфиг и пропишите ваш домен внутри файла
mv nginx/conf.d/app.https.conf.off nginx/conf.d/app.https.conf 2>/dev/null || true

# поднимите стек (на 80-м уже слушает nginx)
docker compose up -d

# разовый выпуск сертификата
export DOMAIN=example.com   # ваш домен
export LETSENCRYPT_EMAIL=you@example.com
docker compose run --rm certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" --email "$LETSENCRYPT_EMAIL" --agree-tos --no-eff-email

# перезагрузите nginx, чтобы подхватил сертификаты
docker compose exec -T nginx nginx -t && docker compose exec -T nginx nginx -s reload


Пока сертификата нет, не держите включённым app.https.conf — nginx не стартует, если пути к fullchain.pem/privkey.pem отсутствуют.


сделаем Nginx-конфиги как шаблоны и будем подставлять домен из .env через envsubst при старте контейнера. Это удобно: поменяли DOMAIN в .env → перезапустили nginx → всё подхватилось.

==================
ШАБЛОН
Если вы пока работаете без сертификата, держите только app.http.conf.template (а https-шаблон можно просто оставить в каталоге — он не помешает; см. шаг 2 — мы контролируем, что рендерить).

# Как пользоваться
Только HTTP (до сертификата)
docker compose up -d nginx
# сайт доступен по http://example.com

Выпустить сертификат (один раз)
docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d "$DOMAIN" \
  --email "$LETSENCRYPT_EMAIL" --agree-tos --no-eff-email

Включить HTTPS

Просто перезапустите nginx (команда из compose сама увидит файлы certbot и срендерит https-конфиг):

docker compose restart nginx