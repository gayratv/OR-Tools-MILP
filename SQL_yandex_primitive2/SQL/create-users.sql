-- Основной пользователь (полные права на БД).
-- Создаем его сразу с требованием X509.
-- Entrypoint его не создаст, т.к. мы используем переменные APP_USER/APP_PASSWORD, а не MYSQL_USER/MYSQL_PASSWORD.
CREATE USER IF NOT EXISTS '${APP_USER}'@'%' IDENTIFIED BY '${APP_PASSWORD}' REQUIRE X509;

GRANT ALL PRIVILEGES ON `${MYSQL_DATABASE}`.* TO '${APP_USER}'@'%';

-- Обычный пользователь (только CRUD-операции), доступен только из внутренней сети Docker
-- Диапазон 172.20.%.% соответствует подсети, заданной в docker-compose.yml
CREATE USER IF NOT EXISTS '${RW_USER}'@'172.20.%.%' IDENTIFIED BY '${RW_PASSWORD}';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON `${MYSQL_DATABASE}`.* TO '${RW_USER}'@'172.20.%.%';

FLUSH PRIVILEGES;
