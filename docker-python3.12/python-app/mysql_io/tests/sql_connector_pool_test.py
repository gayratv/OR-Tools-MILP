from mysql_io.sql_connector_pool import Database
from pprint import pprint

db = Database()

def simple_tests():
    users = db.fetch_all("SELECT id, name FROM core_users WHERE id >= %s", (0,))
    pprint(users)
    one = db.fetch_one("SELECT * FROM core_users WHERE id = %s", (1,))
    pprint(one)

# last_id, affected = db.execute("INSERT INTO core_users (name,phone) VALUES (%s, %s)", ("Alice", "30-30"))
# print("last_id, affected",last_id,affected)

# Пример с executemany для core_users

def executemany_test():
    users_to_insert = [
        ("Bob", "40-40"),
        ("Charlie", "50-50")
    ]
    last_id, affected = db.executemany("INSERT INTO core_users (name, phone) VALUES (%s, %s)", users_to_insert)
    print(f"executemany: last_id={last_id}, affected={affected}")

from dataclasses import dataclass, field
from typing import Dict, Set, List

@dataclass
class ClassInfo:
    """Информация о классе: название и год обучения."""
    name: str
    grade: int

# def get_class_info_list(sql_query: str, version_id : int) -> List[ClassInfo]:
def get_class_info_list(sql_query: str, version_id : int) :
        """Читает представление и возвращает список объектов ClassInfo."""
        try:
            df = db.fetch_all(sql_query, (version_id,))

            pprint(df)
            # if df.empty:
            #     return []

            # return [ClassInfo(name=row['класс_eng'], grade=int(row['grade'])) for _, row in df.iterrows()]
            return [ClassInfo(name=row['name_eng'], grade=int(row['grade'])) for row in df]
            # return df

        except Exception as e:
            print(f"ВНИМАНИЕ: Не удалось загрузить {sql_query}. Возвращен пустой список ClassInfo. Ошибка: {e}")
            return []

version_id=1
classes = get_class_info_list("select name_eng, training_year as grade from input_classes where version_id = %s", version_id)
pprint(classes)


# Политика ретраев (важно)
#
# SELECT — безопасно ретраить (включено).
#
# INSERT/UPDATE/DELETE — по умолчанию не ретраим,
# чтобы не выполнить операцию дважды при сетевом сбое после фактического выполнения.
# Включайте retry_writes=True только если вы точно понимаете идемпотентность операции
# (например, INSERT ... ON DUPLICATE KEY UPDATE с детерминированными значениями или внешняя дедупликация по бизнес-ключу).