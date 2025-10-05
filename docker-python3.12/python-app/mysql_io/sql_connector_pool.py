from typing import Any, Iterable, Optional, Sequence, Tuple, Callable, List, Union
from contextlib import contextmanager
from mysql.connector import pooling, Error
from mysql.connector.errors import InterfaceError, OperationalError, DatabaseError
import logging, time, random
import os
from dotenv import load_dotenv

# ----------------------------------------------------------
# ЛОГИРОВАНИЕ
# ----------------------------------------------------------
logger = logging.getLogger("db")
if not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)  # при желании: DEBUG

# Путь к .env
# ENV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "docker-compose-full", ".env")
ENV_PATH = r"../responce/.env"

# Загружаем переменные окружения
load_dotenv(ENV_PATH)

# Базовый путь для .mysql (по умолчанию Windows)
MYSQL_DIR = r"../responce/.mysql-out"

class Database:
    """
    Пул подключений + ретраи + профайлинг.
    - Ретраи включены по умолчанию только для SELECT (т.е. когда rows=True).
    - Для INSERT/UPDATE/DELETE можно включить retry_writes=True (по умолчанию False).
    """
    def __init__(
        self,
        pool_name: str = "dbpool",
        pool_size: int = 5,
        autocommit: bool = True,
        # Ретраи
        max_retries: int = 3,
        base_backoff: float = 0.1,   # сек
        max_backoff: float = 2.0,    # сек
        retry_writes: bool = False,  # безопаснее держать False
        # Профайлинг
        slow_query_ms: int = 200,    # логировать запросы дольше N мс
        log_sql: bool = True,        # логировать текст SQL в профайлинге

    ) -> None:

        # Конфигурация SSL (TLS)

        dbconfig = {
            "host": os.environ.get("DOMAIN", "appuser"),
            "port": os.environ.get("MYSQL_EXTERNAL_PORT", 45321),
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
        
        # Создание пула
        self._pool = pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=True,
            **dbconfig
        )


        self._autocommit = autocommit

        # retry config
        self._max_retries = max_retries
        self._base_backoff = base_backoff
        self._max_backoff = max_backoff
        self._retry_writes = retry_writes

        # profiling config
        self._slow_query_ms = slow_query_ms
        self._log_sql = log_sql

    # ------------------------ ВНУТРЕННЕЕ ------------------------
    @contextmanager
    def _conn(self):
        conn = self._pool.get_connection()
        try:
            try:
                conn.ping(reconnect=True, attempts=1, delay=0)
            except Exception:
                pass
            conn.autocommit = self._autocommit
            yield conn
        finally:
            conn.close()  # возвращаем в пул

    def _should_retry_error(self, exc: Exception) -> bool:
        """Эвристика: ретраим сетевые/транзиентные ошибки соединения."""
        transient = (InterfaceError, OperationalError)
        if isinstance(exc, transient):
            return True
        # Опционально — по SQLSTATE (у mysql-connector это в .errno/.sqlstate не всегда есть)
        # Пример: потеря соединения, таймауты, lock wait timeout — решайте по политике.
        if isinstance(exc, DatabaseError):
            msg = str(exc).lower()
            signals = [
                "lost connection", "connection lost", "gone away",
                "timeout", "deadlock", "lock wait timeout"
            ]
            return any(s in msg for s in signals)
        return False

    def _backoff_sleep(self, attempt: int) -> None:
        # экспоненциальный бектoff с небольшим джиттером
        delay = min(self._max_backoff, self._base_backoff * (2 ** (attempt - 1)))
        delay = delay * (0.9 + 0.2 * random.random())
        time.sleep(delay)

    def _run_with_retries(self, fn: Callable[[], Any], can_retry: bool, label: str):
        attempt = 1
        while True:
            try:
                return fn()
            except Exception as e:
                if not can_retry or attempt >= self._max_retries or not self._should_retry_error(e):
                    # окончательная ошибка
                    logger.error("DB error (%s), attempt %d/%d: %s", label, attempt, self._max_retries, e)
                    raise
                logger.warning("Transient DB error (%s), retry %d/%d: %s", label, attempt, self._max_retries, e)
                self._backoff_sleep(attempt)
                attempt += 1

    # Профилирование запроса: если время выполнения превышает `_slow_query_ms`, логирует предупреждение.
    def _profile(self, sql: str, started: float, label: str):
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        if elapsed_ms >= self._slow_query_ms:
            if self._log_sql:
                logger.warning("SLOW %s: %d ms | %s", label, elapsed_ms, sql)
            else:
                logger.warning("SLOW %s: %d ms", label, elapsed_ms)

    # ------------------------ ПУБЛИЧНЫЕ API ------------------------
    @contextmanager
    def transaction(self):
        """
        with db.transaction() as cur:
            cur.execute("UPDATE ...")
            cur.execute("INSERT ...")
        """
        with self._conn() as conn:
            conn.autocommit = False
            cur = conn.cursor(dictionary=True)
            try:
                yield cur
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()

    def query(
        self,
        sql: str,
        params: Optional[Sequence[Any]] = None,
        many: bool = False,
        rows: bool = True,
    ) -> Union[List[dict], Tuple[Optional[int], int], List[int]]:
        """
        Выполняет SQL-запрос и возвращает результат в зависимости от параметров.

        Возвращаемые значения:
        - List[dict]:
            Возвращается для SELECT-запросов (когда `rows=True`).
            Каждый элемент списка — это словарь, представляющий строку из результата,
            где ключи — это имена столбцов.
            Пример: db.fetch_all("SELECT id, name FROM users")

        - Tuple[Optional[int], int]:
            Возвращается для одиночных DML-операций (INSERT, UPDATE, DELETE),
            когда `rows=False` и `many=False`.
            Кортеж содержит (lastrowid, rowcount).
            - `lastrowid`: ID последней вставленной строки (для INSERT).
            - `rowcount`: Количество затронутых строк.
            Пример: db.execute("UPDATE users SET name = %s WHERE id = %s", ("John", 1))

        - List[int]:
            Возвращается для пакетных INSERT-операций с `executemany`
            (когда `rows=False`, `many=True` и SQL начинается с "INSERT").
            Список содержит новые ID, сгенерированные для вставленных строк,
            в том же порядке, в котором были переданы данные.
            Пример: db.executemany("INSERT INTO users (name) VALUES (%s)", [("Alice",), ("Bob",)])

        Ретраи: включены для SELECT (`rows=True`). Для DML — если `retry_writes=True`.
        """
        def _do():
            with self._conn() as conn:
                cur = conn.cursor(dictionary=True)
                try:
                    t0 = time.perf_counter()
                    if many:
                        if not isinstance(params, Iterable):
                            raise ValueError("params должен быть итерируемым для many=True")
                        cur.executemany(sql, params)
                    else:
                        cur.execute(sql, params)

                    if rows:
                        data = cur.fetchall()
                        return data
                    else: # DML
                        last_id = cur.lastrowid
                        affected = cur.rowcount

                        is_insert = sql.strip().lower().startswith('insert')
                        if many and is_insert and last_id is not None and last_id > 0:
                            # MySQL (InnoDB) при пакетной вставке (один INSERT с несколькими VALUES)
                            # блокирует автоинкремент и гарантирует, что ID будут идти подряд.
                            # lastrowid возвращает ID первой вставленной строки.
                            # rowcount возвращает количество вставленных строк.
                            # Поэтому этот подход безопасен при параллельных запросах.
                            # Важно: для INSERT ... ON DUPLICATE KEY UPDATE, rowcount может быть > 1 
                            # для обновленной строки, что нарушит эту логику.
                            ids = list(range(last_id, last_id + affected))
                            return ids
                        
                        return (last_id, affected)
                finally:
                    try:
                        # Профайлим по возможности (безопасно)
                        self._profile(sql, t0, "QUERY[many]" if many else "QUERY")
                    except Exception:
                        pass
                    cur.close()

        can_retry = rows or self._retry_writes
        return self._run_with_retries(_do, can_retry=can_retry, label="query")

    # Удобные обёртки
    def fetch_all(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[dict]:
        return self.query(sql, params=params, rows=True)

    def fetch_one(self, sql: str, params: Optional[Sequence[Any]] = None) -> Optional[dict]:
        def _do():
            with self._conn() as conn:
                cur = conn.cursor(dictionary=True)
                try:
                    t0 = time.perf_counter()
                    cur.execute(sql, params)
                    return cur.fetchone()
                finally:
                    try:
                        self._profile(sql, t0, "FETCH_ONE")
                    except Exception:
                        pass
                    cur.close()
        return self._run_with_retries(_do, can_retry=True, label="fetch_one")

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> Tuple[Optional[int], int]:
        return self.query(sql, params=params, rows=False)

    def executemany(self, sql: str, param_seq: Iterable[Sequence[Any]]) -> Union[List[int], Tuple[Optional[int], int]]:
        """
        Выполняет `executemany`.
        Для операторов INSERT возвращает список сгенерированных auto-increment ID.
        Для других операторов (UPDATE, DELETE) возвращает кортеж (lastrowid, rowcount).
        """
        return self.query(sql, params=param_seq, many=True, rows=False)
