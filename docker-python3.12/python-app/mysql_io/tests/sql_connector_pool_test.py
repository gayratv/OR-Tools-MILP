from mysql_io.sql_connector_pool import Database
from pprint import pprint

db = Database()

users = db.fetch_all("SELECT id, name FROM core_users WHERE id >= %s", (0,))
pprint(users)
one = db.fetch_one("SELECT * FROM core_users WHERE id = %s", (1,))
pprint(one)

# last_id, affected = db.execute("INSERT INTO core_users (name,phone) VALUES (%s, %s)", ("Alice", "30-30"))
# print("last_id, affected",last_id,affected)

# Пример с executemany для core_users
users_to_insert = [
    ("Bob", "40-40"),
    ("Charlie", "50-50")
]
last_id, affected = db.executemany("INSERT INTO core_users (name, phone) VALUES (%s, %s)", users_to_insert)
print(f"executemany: last_id={last_id}, affected={affected}")



# Политика ретраев (важно)
#
# SELECT — безопасно ретраить (включено).
#
# INSERT/UPDATE/DELETE — по умолчанию не ретраим,
# чтобы не выполнить операцию дважды при сетевом сбое после фактического выполнения.
# Включайте retry_writes=True только если вы точно понимаете идемпотентность операции
# (например, INSERT ... ON DUPLICATE KEY UPDATE с детерминированными значениями или внешняя дедупликация по бизнес-ключу).