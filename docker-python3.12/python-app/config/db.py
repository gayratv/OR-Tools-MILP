import os
from config import MYSQL_DIR

print("os.environ.get(MYSQL_EXTERNAL_PORT ) ",os.environ.get("MYSQL_EXTERNAL_PORT" ))

# Конфигурация SSL (TLS)
DB_CONFIG = {
    "host": os.environ.get("DOMAIN"),
    "port": int(os.environ.get("MYSQL_EXTERNAL_PORT" )),
    "user": os.environ.get("MYSQL_USER", "appuser"),
    "password": os.environ.get("MYSQL_PASSWORD"),  # ← пароль из .env
    "database": os.environ.get("MYSQL_DATABASE", "school_sheduller"),
    "charset": "utf8mb4",
    "autocommit": True,
    "connect_timeout": 10,

    "ssl_ca": os.path.join(MYSQL_DIR, "ca.pem"),
    "ssl_cert": os.path.join(MYSQL_DIR, "client-cert.pem"),
    "ssl_key": os.path.join(MYSQL_DIR, "client-key.pem"),
    "ssl_verify_cert": True,

}

DB_CONFIG_OTHER_PARAMS = {
    "slow_query_ms": 300, # логировать запросы дольше N мс
}
