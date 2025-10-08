import os
from dotenv import load_dotenv


# BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
# ENV_PATH = os.path.join(BASE_DIR, "responce", ".env")
# MYSQL_DIR = os.path.join(BASE_DIR, "responce", ".mysql-out")

#  Для локального SQL-certs
BASE_DIR = r"F:\_prg\python\OR-Tools-MILP\SQL_certs"
ENV_PATH = os.path.join(BASE_DIR, ".env")
MYSQL_DIR = os.path.join(BASE_DIR, "mysql","certs")

# Загружаем переменные окружения
# print("ENV_PATH ",ENV_PATH)
# print("MYSQL_DIR ",MYSQL_DIR)
load_dotenv(ENV_PATH)

__all__ = ["BASE_DIR", "ENV_PATH", "MYSQL_DIR"]