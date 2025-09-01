import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

# надо установить Microsoft Access Database Engine 2016 Redistributable
# https://www.microsoft.com/en-us/download/details.aspx?id=54920&utm_source=chatgpt.com

# путь к вашей базе Access (.mdb или .accdb)
db_file = r"F:\_prg\python\OR-Tools-MILP\src\db\rasp2.accdb"

# строка подключения (для новых версий Access — драйвер "Microsoft Access Driver (*.mdb, *.accdb)")
conn_str_raw = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    fr"DBQ={db_file};"
)

# Для подавления UserWarning и соответствия лучшим практикам pandas
# рекомендуется использовать SQLAlchemy для создания соединения.
quoted_conn_str = quote_plus(conn_str_raw)
engine = create_engine(f"access+pyodbc:///?odbc_connect={quoted_conn_str}")

# пример: читаем таблицу MyTable в DataFrame
df = pd.read_sql("SELECT NAIME FROM vCLASS", engine)
classes = df["NAIME"].tolist()


print(f"\n--- Полученный список классов из столбца NAIME ---")
print(classes)

print(type(classes))

# subjects = ["math", "cs", "eng", "labor", "history"]