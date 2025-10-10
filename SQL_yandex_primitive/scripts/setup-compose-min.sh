#!/usr/bin/env bash

set -euo pipefail

# ---------------------- Параметры/пути ----------------------
APP_DIR="/opt/app"
BIN_DIR="$APP_DIR/bin"
ASSETS_DIR="$APP_DIR/assets"
SECBIN_DIR="$APP_DIR/.secrets-bin"


# ==== ENV для setup-compose.sh ====
BASE_GIT_URL=https://raw.githubusercontent.com/gayratv/OR-Tools-MILP/main/SQL_yandex_primitive/scripts
export URL_COMPOSE="$BASE_GIT_URL/docker-compose.yml"
export URL_DOCKERFILE="$BASE_GIT_URL/Dockerfile"
export URL_WAIT="$BASE_GIT_URL/wait_for_files.sh"
export URL_SETUP="$BASE_GIT_URL/setup-compose.sh"

# Поведение: ничего не ждём и контейнеры не запускаем
export WAIT_ENABLED=1
export WAIT_TIMEOUT=600
export WAIT_MIN_SIZE=1
export WAIT_STABLE=3
export RUN_COMPOSE=0


# Запуск compose (по умолчанию выключен, т.к. ты пока не хочешь стартовать контейнер)
RUN_COMPOSE="${RUN_COMPOSE:-0}"

log() { echo "[setup] $*" >&2; }
warn(){ echo "[setup][WARN] $*" >&2; }
err() { echo "[setup][ERROR] $*" >&2; }


safe_get() {
  # безопасное скачивание: не роняем скрипт при неудаче
  local url="$1" dst="$2"
  if [[ -z "$url" ]]; then
    warn "пустой URL для $dst — пропускаю"
    return 0
  fi
  log "скачиваю $url → $dst"
}

# ---------------------- Скачиваем файлы приложения ----------------------
log "скачиваю файлы приложения (если заданы URL)"
declare -A FILES=()
[[ -n "$URL_COMPOSE"    ]] && FILES["$APP_DIR/docker-compose.yml"]="$URL_COMPOSE"
[[ -n "$URL_DOCKERFILE" ]] && FILES["$APP_DIR/Dockerfile"]="$URL_DOCKERFILE"

echo "BASH_VERSION $BASH_VERSION"


if (( ${#FILES[@]} > 0 )); then
  for dst in "${!FILES[@]}"; do
    url="${FILES[$dst]}"
    safe_get "$url" "$dst" || true
  done
else
  log "FILES пуст — скачивать нечего"
fi
