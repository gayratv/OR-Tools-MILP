from mysql_io.sql_connector_pool import Database
from pprint import pprint

db = Database()
print('DB иниц ', db)

def simple_tests():
    users = db.fetch_all("SELECT id, name FROM core_users WHERE id >= %s", (0,))
    pprint(users)
    one = db.fetch_one("SELECT * FROM core_users WHERE id = %s", (1,))
    pprint(one)

simple_tests()