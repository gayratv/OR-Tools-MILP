-- Выполняется один раз при первом старте, если данных ещё нет
-- Создаст схему/права, более строгие гранты и host-ограничение (по IP при необходимости)
-- Пример первичной инициализации

      -- Создание базы (если её ещё нет)
CREATE DATABASE IF NOT EXISTS `${MYSQL_DATABASE}`
  /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */;

-- Основной пользователь (полные права на БД)
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}' REQUIRE X509;
GRANT ALL PRIVILEGES ON `${MYSQL_DATABASE}`.* TO '${MYSQL_USER}'@'%';

-- Обычный пользователь (только CRUD-операции), доступен только из внутренней сети Docker
-- Диапазон 172.20.%.% соответствует подсети, заданной в docker-compose.yml
CREATE USER IF NOT EXISTS '${MYSQL_RW_USER}'@'172.20.%.%' IDENTIFIED BY '${MYSQL_RW_PASSWORD}';
GRANT SELECT, INSERT, UPDATE, DELETE
  ON `${MYSQL_DATABASE}`.* TO '${MYSQL_RW_USER}'@'172.20.%.%';

FLUSH PRIVILEGES;
