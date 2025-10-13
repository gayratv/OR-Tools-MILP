#!/usr/bin/env bash
set -euo pipefail

# --- Настройки ---
ENV_FILE="../.env"
SQL_FILE="${1:-app-user.sql}"

# --- Usage ---
# ./deploy-user.sh [sql_file_name]
#
# Example:
# ./deploy-user.sh app-user.sql
# ./deploy-user.sh another.sql

# Проверяем наличие файлов
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ Файл $ENV_FILE не найден!"
  exit 1
fi

if [[ ! -f "$SQL_FILE" ]]; then
  echo "❌ Файл $SQL_FILE не найден!"
  exit 1
fi

# Загружаем переменные из .env
echo "📦 Загружаем переменные из $ENV_FILE..."
# Более надежный способ загрузки переменных, который корректно обрабатывает пробелы и спецсимволы в значениях.
set -a # Автоматически экспортировать все переменные, которые будут определены далее
source <(grep -v '^#' "$ENV_FILE")
set +a # Отключить автоматический экспорт

# Проверяем, что всё есть
: "${APP_USER:?APP_USER не задан}"
: "${APP_PASSWORD:?APP_PASSWORD не задан}"
: "${DB_NAME:?DB_NAME не задан}"
: "${MYSQL_LOGIN_PATH:?MYSQL_LOGIN_PATH не задан}"
: "${MYSQL_SUFFIX:?MYSQL_SUFFIX не задан}"

# Выполняем SQL с подстановкой переменных
echo "🚀 Выполняем SQL-скрипт $SQL_FILE для базы $DB_NAME..."
envsubst < "$SQL_FILE" | mysql \
  --login-path=root \
  --defaults-group-suffix=root \
  "MYSQL_DATABASE"

echo "✅ Готово!"
