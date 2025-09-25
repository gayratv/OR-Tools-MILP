#!/usr/bin/env bash
set -euo pipefail
# cd /mnt/f/_prg/python/OR-Tools-MILP/ya-cloud
# ./yc-secrets-common.sh

# -----------------------------------------------------------
# yc-secrets-common.sh (fixed)
# Создаёт один секрет Lockbox из .env и (опционально) PEM-файлов.
# Использование:
#   ./yc-secrets-common.sh <secret_name> <path_to_env> [path_to_mysql_cert_dir]
# Пример:
#   ./yc-secrets-common.sh my-app-secrets ../docker-compose-full/.env ./ya-cloud/.mysql
# -----------------------------------------------------------

need() { command -v "$1" >/dev/null 2>&1 || { echo "Ошибка: требуется '$1'." >&2; exit 1; }; }
need jq
need yc
need base64
need grep

SECRET_NAME=${1:-"school-scheduler-app-secrets"}
ENV_FILE=${2:-"../docker-compose-full/.env"}
MYSQL_CERT_DIR=${3:-"/mnt/f/_prg/python/OR-Tools-MILP/ya-cloud/.mysql"}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Ошибка: Файл .env не найден по пути: $ENV_FILE" >&2
  exit 1
fi

# ---------- payload из .env (text_value) ----------
generate_env_payload() {
  # Убираем комментарии и пустые строки, парсим KEY=VALUE.
  grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' \
  | jq -R -n '[inputs | capture("(?<key>[^=]+)=(?<value>.*)") | {key: .key, text_value: .value}]'
 }

#generate_env_payload() {
#  grep -v -E '^[[:space:]]*#' "$ENV_FILE" | grep -v -E '^[[:space:]]*$' \
#  | sed -E 's/^[[:space:]]*export[[:space:]]+//' \
#  | jq -R -n '
#      [ inputs
#        | capture("(?<key>[^=]+)=(?<value>.*)")
#        | { key: (.key | gsub("^\\s+|\\s+$";"")), text_value: .value }
#      ]
#    '
#}



# ---------- payload из PEM-файлов (binary_value, base64) ----------
generate_cert_payload() {
  if [[ ! -d "$MYSQL_CERT_DIR" ]]; then
    echo "Предупреждение: каталог с сертификатами не найден: $MYSQL_CERT_DIR. Пропускаю." >&2
    echo "[]"
    return
  fi

  shopt -s nullglob
  files=( "$MYSQL_CERT_DIR"/*.pem )
  if (( ${#files[@]} == 0 )); then
    echo "Предупреждение: PEM-файлы не найдены в $MYSQL_CERT_DIR. Пропускаю." >&2
    echo "[]"
    return
  fi

  tmp='['
  first=true
  for cert_file in "${files[@]}"; do
    [[ -f "$cert_file" ]] || continue
    $first || tmp+=','
    first=false
    filename=$(basename "$cert_file")
    # -w 0 для GNU coreutils; на macOS можно заменить на | tr -d '\n'
    content_b64=$(base64 -w 0 "$cert_file" 2>/dev/null || base64 < "$cert_file" | tr -d '\n')
    tmp+=$(printf '{"key":"%s","binary_value":"%s"}' "$filename" "$content_b64")
  done
  tmp+=']'
  echo "$tmp"
}

echo "Генерирую payload из .env: $ENV_FILE ..."
ENV_JSON=$(generate_env_payload)

echo "Генерирую payload из сертификатов (если есть): $MYSQL_CERT_DIR ..."
CERTS_JSON=$(generate_cert_payload)

# ---------- объединяем массивы записей ----------
COMBINED_PAYLOAD=$(jq -s '.[0] + .[1]' <(echo "$ENV_JSON") <(echo "$CERTS_JSON"))

# ---------- создаём секрет ровно один раз ----------
echo "Создаю секрет '$SECRET_NAME'..."
yc lockbox secret create \
  --name "$SECRET_NAME" \
  --description "Секреты приложения (.env + PEM)" \
  --payload "$COMBINED_PAYLOAD"

echo "Готово: секрет '$SECRET_NAME' создан."
