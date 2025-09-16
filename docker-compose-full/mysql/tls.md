1) Сгенерировать CA и серверный сертификат (OpenSSL)

Откройте терминал на VPS/локалке в docker-compose-full/ и выполните:

mkdir -p mysql/certs
cd mysql/certs

# 1) Ключ и самоподписанный CA (корневой)
openssl genrsa -out ca-key.pem 4096
openssl req -new -x509 -key ca-key.pem -out ca.pem -days 825 \
  -subj "/CN=MySQL-Local-CA"

# 2) Ключ сервера
openssl genrsa -out server-key.pem 2048

# 3) CSR сервера (важно указать CN ≈ ваш хостнейм/домен)
# Подставьте ваш домен/IP вместо example.com и 203.0.113.10
openssl req -new -key server-key.pem -out server.csr \
  -subj "/CN=example.com"

# 4) Подписываем серверный сертификат нашим CA
# Добавляем SAN, чтобы верификация по домену/IP проходила
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem -days 825 \
  -extfile <(printf "subjectAltName=DNS:example.com,IP:203.0.113.10")

# 5) Права на ключи
chmod 600 server-key.pem ca-key.pem


===========================

Примечания:

В subjectAltName укажите реальный домен (или локальный DNS-имя) и/или публичный IP вашего сервера.

Для старых OpenSSL без опции <(...)> можно сделать отдельный файл san.cnf с:

subjectAltName=DNS:example.com,IP:203.0.113.10


и заменить последнюю команду на:

openssl x509 -req -in server.csr -CA ca.pem -CAkey ca-key.pem -CAcreateserial \
  -out server-cert.pem -days 825 -extfile san.cnf

===========================

Перезапуск MySQL
docker compose down
docker compose up -d
docker compose logs -f db

===========================

Подключение клиентов
С самого контейнера (для проверки)
docker exec -it mysql8 mysql --ssl-mode=REQUIRED -uroot -p"$MYSQL_ROOT_PASSWORD" -e "SHOW VARIABLES LIKE 'ssl_cipher';"

С удалённой машины

Скопируйте ca.pem на клиентскую машину (например, в ~/.mysql/ca.pem) и подключайтесь:

mysql --ssl-mode=VERIFY_CA --ssl-ca=/path/to/ca.pem \
  -h example.com -P 45321 -u appuser -p


REQUIRED — примет любой валидный TLS (без проверки CA/имени хоста).

VERIFY_CA — проверит, что сертификат подписан вашим CA.

VERIFY_IDENTITY — дополнительно проверит совпадение имени хоста (CN/SAN) с -h.

Если вы правильно указали subjectAltName=DNS:example.com, смело используйте --ssl-mode=VERIFY_IDENTITY.

Права на ключи должны быть ограничены (chmod 600), иначе MySQL может отказать.

