import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
ENV_PATH = os.path.join(BASE_DIR, "responce", ".env")
MYSQL_DIR = os.path.join(BASE_DIR, "responce", ".mysql-out")


# Загружаем переменные окружения
load_dotenv(ENV_PATH)


__all__ = ["BASE_DIR", "ENV_PATH", "MYSQL_DIR"]