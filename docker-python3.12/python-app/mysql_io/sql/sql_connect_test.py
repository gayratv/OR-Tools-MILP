from mysql_io.sql_connector_pool import Database
import os
import mysql.connector
from dotenv import load_dotenv

# Путь к .env
# ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose-full", ".env")
ENV_PATH = r"../responce/.env"

# Загружаем переменные окружения
load_dotenv(ENV_PATH)

# Базовый путь для .mysql (по умолчанию Windows)
MYSQL_DIR = r"../responce/.mysql-out"


config = {
    "host": "uroktime.store",
    "port": 45321,
    "user": os.environ.get("MYSQL_USER", "appuser"),
    "password": os.environ.get("MYSQL_PASSWORD"),       # ← пароль из .env
    "database": os.environ.get("MYSQL_DATABASE", "school_sheduller"),
    "ssl_ca":   os.path.join(MYSQL_DIR, "ca.pem"),
    "ssl_cert": os.path.join(MYSQL_DIR, "client-cert.pem"),
    "ssl_key":  os.path.join(MYSQL_DIR, "client-key.pem"),
    "ssl_verify_cert": True,
    "connection_timeout": 10,
}

db = Database(
    host="localhost",
    user="root",
    password="your_password",
    database="your_database",
    pool_size=10,
    max_retries=4,      # до 4 попыток
    slow_query_ms=150,  # логировать запросы дольше 150 мс
    retry_writes=False  # оставляем False, чтобы не дублировать изменения при сбоях
)

users = db.fetch_all("SELECT id, name FROM users WHERE age > %s", (18,))
one = db.fetch_one("SELECT * FROM users WHERE id = %s", (42,))
last_id, affected = db.execute("INSERT INTO users (name, age) VALUES (%s, %s)", ("Alice", 30))


# Политика ретраев (важно)
#
# SELECT — безопасно ретраить (включено).
#
# INSERT/UPDATE/DELETE — по умолчанию не ретраим,
# чтобы не выполнить операцию дважды при сетевом сбое после фактического выполнения.
# Включайте retry_writes=True только если вы точно понимаете идемпотентность операции
# (например, INSERT ... ON DUPLICATE KEY UPDATE с детерминированными значениями или внешняя дедупликация по бизнес-ключу).