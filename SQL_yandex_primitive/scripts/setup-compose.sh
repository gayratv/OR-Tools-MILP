#!/usr/bin/env bash
# setup-compose.sh
# Подготавливает окружение на YC VM (create-with-container):
#  - качает артефакты из репозитория (compose/Dockerfile и т.д.)
#  - по возможности получает SECRET_ID из метадаты ВМ и тянет .env из Lockbox
#  - (опционально) ждёт готовности файлов wait_for_files.sh
#  - (опционально) выполняет docker compose build/up
#
# Управление через переменные окружения (в cloud-init можно экспортировать заранее):
#   URL_WAIT         — URL скрипта wait_for_files.sh (опционально)
#   URL_COMPOSE      — URL docker-compose.yml (опционально)
#   URL_DOCKERFILE   — URL Dockerfile (опционально)
#   URL_MODEL        — URL большого бинарника (опционально)
#   URL_APP_CFG      — URL произвольного конфига (опционально)
#
#   WAIT_ENABLED=0|1 — включить ожидание файлов (по умолчанию 0 = выключено)
#   WAIT_TIMEOUT     — таймаут ожидания, сек (по умолчанию 600)
#   WAIT_MIN_SIZE    — мин. размер файла, байт (по умолчанию 1)
#   WAIT_STABLE      — "стабильность" размера, сек (по умолчанию 3)
#
#   RUN_COMPOSE=0|1  — запустить docker compose build/up (по умолчанию 0 = не запускать)
#
# Требования: curl, jq, (docker/compose уже есть в образе create-with-container)

set -euo pipefail

# ---------------------- Параметры/пути ----------------------
APP_DIR="/opt/app"
BIN_DIR="$APP_DIR/bin"
ASSETS_DIR="$APP_DIR/assets"
SECBIN_DIR="$APP_DIR/.secrets-bin"
mkdir -p "$BIN_DIR" "$ASSETS_DIR" "$SECBIN_DIR" "$APP_DIR/config"

# URLs можно задать заранее через env (cloud-init), иначе оставь пустыми — ничего страшного
URL_WAIT="${URL_WAIT:-}"                 # напр.: https://raw.githubusercontent.com/<owner>/<repo>/<ref>/scripts/wait_for_files.sh
URL_COMPOSE="${URL_COMPOSE:-}"           # напр.: https://raw.githubusercontent.com/<owner>/<repo>/<ref>/deploy/docker-compose.yml
URL_DOCKERFILE="${URL_DOCKERFILE:-}"     # напр.: https://raw.githubusercontent.com/<owner>/<repo>/<ref>/deploy/Dockerfile
URL_MODEL="${URL_MODEL:-}"               # опционально (большой бинарник)
URL_APP_CFG="${URL_APP_CFG:-}"           # опционально (конфиг)

# Ожидание файлов (по умолчанию выключено)
WAIT_ENABLED="${WAIT_ENABLED:-0}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-600}"
WAIT_MIN_SIZE="${WAIT_MIN_SIZE:-1}"
WAIT_STABLE="${WAIT_STABLE:-3}"

# Запуск compose (по умолчанию выключен, т.к. ты пока не хочешь стартовать контейнер)
RUN_COMPOSE="${RUN_COMPOSE:-0}"

log() { echo "[setup] $*" >&2; }
warn(){ echo "[setup][WARN] $*" >&2; }
err() { echo "[setup][ERROR] $*" >&2; }

# ---------------------- Утилиты ----------------------
need() { command -v "$1" >/dev/null 2>&1 || { err "требуется '$1'"; exit 1; }; }
need curl
need jq

safe_get() {
  # безопасное скачивание: не роняем скрипт при неудаче
  local url="$1" dst="$2"
  if [[ -z "$url" ]]; then
    warn "пустой URL для $dst — пропускаю"
    return 0
  fi
  log "скачиваю $url → $dst"
  install -d -m 0755 "$(dirname "$dst")"
  if curl -fsSL -o "$dst" "$url"; then
    return 0
  else
    warn "не удалось скачать $url"
    return 1
  fi
}

# ---------------------- Получить SECRET_ID (опционально) ----------------------
log "получаю SECRET_ID из метадаты ВМ (если есть)"
IMDS="http://169.254.169.254/computeMetadata/v1"
SECRET_ID="$(curl -fsS -H 'Metadata-Flavor: Google' "$IMDS/instance/attributes/secret_id" || true)"
if [[ -z "${SECRET_ID:-}" ]]; then
  warn "SECRET_ID отсутствует в метадате; шаг Lockbox будет пропущен"
fi
echo "SECRET_ID: $SECRET_ID"

# ---------------------- Скачиваем helper: wait_for_files.sh ----------------------
if [[ -n "$URL_WAIT" ]]; then
  safe_get "$URL_WAIT" "$BIN_DIR/wait_for_files.sh" || true
  [[ -f "$BIN_DIR/wait_for_files.sh" ]] && chmod +x "$BIN_DIR/wait_for_files.sh" || true
else
  warn "URL_WAIT не задан — ожидание файлов (если включено) будет пропущено"
fi

# ---------------------- Скачиваем файлы приложения ----------------------
log "скачиваю файлы приложения (если заданы URL)"
declare -A FILES=()
[[ -n "$URL_COMPOSE"    ]] && FILES["$APP_DIR/docker-compose.yml"]="$URL_COMPOSE"
[[ -n "$URL_DOCKERFILE" ]] && FILES["$APP_DIR/Dockerfile"]="$URL_DOCKERFILE"

if (( ${#FILES[@]} > 0 )); then
  for dst in "${!FILES[@]}"; do
    url="${FILES[$dst]}"
    safe_get "$url" "$dst" || true
  done
else
  log "FILES пуст — скачивать нечего"
fi

# ---------------------- .env из Lockbox (если SECRET_ID есть) ----------------------
ENV_FILE="$APP_DIR/.env"
if [[ -n "${SECRET_ID:-}" ]]; then
  log "тяну .env из Lockbox по IAM-токену ВМ"
  IAM_TOKEN="$(curl -fsS -H 'Metadata-Flavor: Google' \
    "$IMDS/instance/service-accounts/default/token" | jq -r .access_token || true)"
  if [[ -n "$IAM_TOKEN" ]]; then
    PAYLOAD_JSON="$(curl -fsS -H "Authorization: Bearer ${IAM_TOKEN}" \
      "https://payload.lockbox.api.cloud.yandex.net/lockbox/v1/secrets/${SECRET_ID}/payload" || true)"
    if [[ -n "$PAYLOAD_JSON" ]]; then
      {
        echo "# generated from Lockbox $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
        echo "$PAYLOAD_JSON" \
          | jq -r '.entries[]? | select(.textValue != null) | "\(.key)=\(.textValue)"'
      } > "$ENV_FILE" || true
      [[ -s "$ENV_FILE" ]] && chmod 600 "$ENV_FILE" || warn ".env пустой или не создан"

      # бинарные значения (если есть)
      echo "$PAYLOAD_JSON" \
        | jq -c '.entries[]? | select(.binaryValue != null) | {key, value: .binaryValue}' \
        | while read -r line; do
            k="$(echo "$line" | jq -r '.key')"
            v_b64="$(echo "$line" | jq -r '.value')"
            out="$SECBIN_DIR/$k"
            log "пишу бинарный секрет $out"
            echo "$v_b64" | base64 --decode > "$out" || true
            chmod 600 "$out" || true
          done
    else
      warn "не удалось получить payload Lockbox; пропускаю .env"
    fi
  else
    warn "не удалось получить IAM-токен; пропускаю .env"
  fi
else
  log "SECRET_ID не задан — шаг .env пропущен"
fi

# ---------------------- (Опционально) Ожидание файлов ----------------------
if [[ "${WAIT_ENABLED}" == "1" && -x "$BIN_DIR/wait_for_files.sh" ]]; then
  log "ожидаю готовности файлов (timeout=${WAIT_TIMEOUT}s, min_size=${WAIT_MIN_SIZE}B, stable=${WAIT_STABLE}s)"
  # Пример ожидания: .env и любые большие бинарники
  "$BIN_DIR/wait_for_files.sh" \
    -f "$ENV_FILE" \
    -p "$ASSETS_DIR/*.bin" \
    --min-size "${WAIT_MIN_SIZE}" \
    --stable "${WAIT_STABLE}" \
    --timeout "${WAIT_TIMEOUT}" || warn "ожидание завершилось неуспешно"
else
  log "ожидание отключено (WAIT_ENABLED!=1) или нет wait_for_files.sh — пропускаю"
fi

# ---------------------- (Опционально) Docker compose ----------------------
if [[ "${RUN_COMPOSE}" == "1" ]]; then
  # Требуются docker/compose (в create-with-container уже есть)
  need docker
  log "docker compose build && up -d"
  cd "$APP_DIR"
  if [[ -f docker-compose.yml ]]; then
    docker compose config >/dev/null || warn "compose config warning"
    docker compose build || warn "compose build завершился с предупреждением"
    docker compose up -d || warn "compose up завершился с предупреждением"
  else
    warn "нет $APP_DIR/docker-compose.yml — пропускаю compose"
  fi
else
  log "RUN_COMPOSE=0 — контейнеры НЕ запускаем (как и просили)"
fi

log "готово. ВМ ожидает подключения по SSH."
exit 0
