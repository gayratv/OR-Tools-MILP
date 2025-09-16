import os
import mysql.connector
from dotenv import load_dotenv

# Путь к .env
ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose-full", ".env")

# Загружаем переменные окружения
load_dotenv(ENV_PATH)

# Базовый путь для .mysql (по умолчанию Windows)
MYSQL_DIR = os.environ.get("MYSQL_DIR", r"C:\Users\gena6\.mysql")

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

try:
    if not config["password"]:
        raise ValueError("MYSQL_PASSWORD не найден в .env")

    conn = mysql.connector.connect(**config)

    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("OK:", cur.fetchall())
    cur.close()

    cur = conn.cursor(dictionary=True)  # результаты в виде словаря (удобно читать)

    cur.execute("SELECT * FROM user;")
    rows = cur.fetchall()

    print("Таблица user:")
    for row in rows:
        print(row)

    cur.close()

    conn.close()

except Exception as e:
    print("Ошибка:", e)
