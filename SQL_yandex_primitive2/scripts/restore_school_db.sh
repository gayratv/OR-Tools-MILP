#!/bin/bash

# === Usage ===
# ./restore_school_db.sh <path_to_dump_file>
#
# Example:
# ./restore_school_db.sh /mnt/f/_prg/python/OR-Tools-MILP/MySQL_backup/beget-2025_10_14_01_00_01-dump.sql

# === Конфигурация ===
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
DEFAULT_DUMP_FILE="/mnt/f/_prg/python/OR-Tools-MILP/MySQL_backup/beget-2025_10_14_01_00_01-dump.sql"
DUMP_FILE=${1:-$DEFAULT_DUMP_FILE}

DB_NAME="school_sheduller"

# === Проверка, существует ли дамп ===
if [ ! -f "$DUMP_FILE" ]; then
  echo "❌ Файл дампа не найден: $DUMP_FILE"
  exit 1
fi

echo "=== Начало восстановления базы данных '$DB_NAME' ==="
echo "Файл дампа: $DUMP_FILE"
echo

# === Выполнение восстановления ===
# --verbose показывает команды
# stderr (2) перенаправляется в stdout (1), чтобы tee обработал оба потока.
# grep -v отфильтровывает строки с INSERT INTO, чтобы лог был чище.
mysql --login-path=root --defaults-group-suffix=root \
  --database="$DB_NAME" --verbose < "$DUMP_FILE" 2>&1 | grep -v '^INSERT INTO'

# === Проверка результата ===
# Проверяем статус именно команды mysql. PIPESTATUS[0] - статус первой команды в пайпе.
if [ ${PIPESTATUS[0]} -eq 0 ]; then
  echo "✅ Восстановление базы '$DB_NAME' завершено УСПЕШНО!"
else
  echo "❌ Ошибка при восстановлении базы '$DB_NAME'. Подробности смотрите в выводе выше."
fi
