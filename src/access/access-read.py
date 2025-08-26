import pyodbc
import pandas as pd

# надо установить Microsoft Access Database Engine 2016 Redistributable
# https://www.microsoft.com/en-us/download/details.aspx?id=54920&utm_source=chatgpt.com

# путь к вашей базе Access (.mdb или .accdb)
db_file = r"F:\_prg\python\OR-Tools-MILP\src\db\rasp.accdb"

# строка подключения (для новых версий Access — драйвер "Microsoft Access Driver (*.mdb, *.accdb)")
conn_str = (
    r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
    fr"DBQ={db_file};"
)

# подключение
conn = pyodbc.connect(conn_str)

# пример: читаем таблицу MyTable в DataFrame
df = pd.read_sql("SELECT * FROM в_аудитории", conn)

# query = "SELECT * FROM Orders WHERE Year(OrderDate) = 2025"

# year = 2025
# query = "SELECT * FROM Orders WHERE Year(OrderDate) = ?"
# df = pd.read_sql(query, conn, params=[year])

# по умолчанию показывает первые 5 строк DataFrame. Показывает 10
# print(df.head(10))

print(df)

conn.close()
