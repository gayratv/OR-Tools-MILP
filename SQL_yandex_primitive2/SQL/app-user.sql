-- если пользователя ещё нет:
CREATE USER 'appuser'@'%' IDENTIFIED BY 'СЛОЖНЫЙ_ПАРОЛЬ';

# CREATE USER IF NOT EXISTS '${APP_USER}'@'%' IDENTIFIED BY '${APP_PASSWORD}' REQUIRE X509;

-- привязать к DN (Subject) и нашему CA (Issuer):
ALTER USER 'appuser'@'%' REQUIRE
  SUBJECT '/C=RU/O=MyOrg/CN=appuser'
  AND ISSUER  '/C=RU/O=MySQL/CN=MySQL-CA'
  AND X509;

-- права (пример):
GRANT ALL PRIVILEGES ON school_sheduller.* TO 'appuser'@'%';
FLUSH PRIVILEGES;
