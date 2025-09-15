-- Выполняется один раз при первом старте, если данных ещё нет
-- Создаст схему/права, более строгие гранты и host-ограничение (по IP при необходимости)
-- Пример первичной инициализации
CREATE DATABASE IF NOT EXISTS `${MYSQL_DATABASE}` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */;

-- Пример явной выдачи прав конкретному пользователю (дублирует то, что делает entrypoint, но гибче)
GRANT ALL PRIVILEGES ON `${MYSQL_DATABASE}`.* TO '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
FLUSH PRIVILEGES;
