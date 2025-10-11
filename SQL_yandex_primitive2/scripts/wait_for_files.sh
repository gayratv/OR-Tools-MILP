#!/usr/bin/env bash

# вот удобный, самодостаточный wait_for_files.sh. Подходит для cloud-init и CI. Умеет ждать набор путей/глобов до таймаута, проверять минимальный размер и «стабильность» (без изменения размера N секунд), а по готовности может применить chmod/chown и выполнить команду на каждый найденный файл.

# wait_for_files.sh — ждет появления файлов/глобов с проверкой размера и "стабильности".
# Использование (примеры):
#   wait_for_files.sh -f /opt/app/.env -t 120
#   wait_for_files.sh -p "/opt/app/assets/*.bin" --min-size 1048576 --stable 5
#   wait_for_files.sh -f /opt/app/a -f /opt/app/b --chmod 600 --chown yc-user:yc-user
#   wait_for_files.sh -p "/opt/app/*.cfg" --exec 'sha256sum "{}"' -q
#
# Опции:
#   -f, --file PATH           Явный путь к файлу (можно повторять)
#   -p, --pattern GLOB        Глоб (например, "/opt/app/*.bin") (можно повторять)
#   -d, --dir DIR             Директория, которую нужно дождаться (можно повторять)
#   -t, --timeout SEC         Таймаут ожидания, сек (по умолчанию 300)
#   -i, --interval SEC        Интервал между проверками, сек (по умолчанию 2)
#       --min-size BYTES      Минимальный размер (для каждого файла), по умолчанию 1 байт
#       --stable SEC          Требуемая "стабильность" размера: без изменений N сек (по умолчанию 0 = не проверять)
#       --chmod MODE          Применить chmod к готовым файлам, например "600" или "0640"
#       --chown USER:GROUP    Применить chown к готовым файлам, например "yc-user:yc-user"
#       --exec 'CMD "{}"'     Выполнить команду для каждого готового файла; {} заменится на путь
#   -q, --quiet               Тише (минимум логов)
#   -h, --help                Справка
#
# Код выхода:
#   0 — все условия выполнены
#   1 — таймаут/ошибка

set -uo pipefail

# ---------- Параметры по умолчанию ----------
TIMEOUT=300
INTERVAL=2
MIN_SIZE=1
STABLE_SECS=0
QUIET=0
declare -a FILES=()
declare -a PATTERNS=()
declare -a DIRS=()
CHMOD_MODE=""
CHOWN_SPEC=""
EXEC_CMD=""

log() { (( QUIET )) || echo "[wait] $*" >&2; }
err() { echo "[wait][ERROR] $*" >&2; }
usage() { sed -n '1,80p' "$0" | sed 's/^# \{0,1\}//'; }

# ---------- Парсинг аргументов ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)        FILES+=("$2"); shift 2;;
    -p|--pattern)     PATTERNS+=("$2"); shift 2;;
    -d|--dir)         DIRS+=("$2"); shift 2;;
    -t|--timeout)     TIMEOUT="$2"; shift 2;;
    -i|--interval)    INTERVAL="$2"; shift 2;;
        --min-size)   MIN_SIZE="$2"; shift 2;;
        --stable)     STABLE_SECS="$2"; shift 2;;
        --chmod)      CHMOD_MODE="$2"; shift 2;;
        --chown)      CHOWN_SPEC="$2"; shift 2;;
        --exec)       EXEC_CMD="$2"; shift 2;;
    -q|--quiet)       QUIET=1; shift;;
    -h|--help)        usage; exit 0;;
    *) err "Неизвестный аргумент: $1"; usage; exit 1;;
  esac
done

if (( ${#FILES[@]} == 0 && ${#PATTERNS[@]} == 0 && ${#DIRS[@]} == 0 )); then
  err "Нужно указать хотя бы один -f/--file, -p/--pattern или -d/--dir"
  usage; exit 1
fi

# ---------- Подготовка ----------
shopt -s nullglob dotglob

deadline=$(( $(date +%s) + TIMEOUT ))

# Для проверки "стабильности" запоминаем последний размер и момент времени
declare -A LAST_SIZE=()
declare -A STABLE_SINCE=()

# ---------- Функции проверки ----------
# exists_and_ready FILE -> 0/1
exists_and_ready() {
  local f="$1"

  # Проверка существования и минимального размера
  [[ -e "$f" ]] || return 1
  local sz
  sz=$(stat -c '%s' "$f" 2>/dev/null || echo 0)
  if (( sz < MIN_SIZE )); then
    return 1
  fi

  # Проверка стабильности размера
  if (( STABLE_SECS > 0 )); then
    local prev="${LAST_SIZE[$f]:-}"
    local now=$(date +%s)
    if [[ -z "$prev" || "$prev" != "$sz" ]]; then
      LAST_SIZE[$f]="$sz"
      STABLE_SINCE[$f]="$now"
      return 1
    else
      local since="${STABLE_SINCE[$f]:-$now}"
      local delta=$(( now - since ))
      (( delta >= STABLE_SECS )) || return 1
    fi
  fi

  return 0
}

# collect_targets -> заполняет массив TARGETS итоговым списком путей для проверки
collect_targets() {
  TARGETS=()
  local p
  # Явные файлы
  for p in "${FILES[@]}"; do
    TARGETS+=("$p")
  done
  # Глоб-паттерны
  local gl
  for p in "${PATTERNS[@]}"; do
    # расширяем глоб в список путей; если пока ничего не матчится — добавим сам паттерн,
    # чтобы было что ждать (exists_and_ready вернет 1 до появления реальных файлов)
    local matched=0
    for gl in $p; do
      TARGETS+=("$gl")
      matched=1
    done
    if (( matched == 0 )); then
      TARGETS+=("$p")
    fi
  done
}

# dirs_ready -> проверка директорий
dirs_ready() {
  local d
  for d in "${DIRS[@]}"; do
    [[ -d "$d" ]] || return 1
  done
  return 0
}

# ---------- Основной цикл ожидания ----------
log "Ожидаю объекты: files=${#FILES[@]} patterns=${#PATTERNS[@]} dirs=${#DIRS[@]}, timeout=${TIMEOUT}s, interval=${INTERVAL}s, min-size=${MIN_SIZE}B, stable=${STABLE_SECS}s"
collect_targets

while :; do
  now=$(date +%s)
  if (( now > deadline )); then
    err "Таймаут ${TIMEOUT}s. Не все цели готовы."
    err "Последний список целей: ${TARGETS[*]:-<пусто>}"
    exit 1
  fi

  # Проверяем директории
  if ! dirs_ready; then
    sleep "$INTERVAL"
    continue
  fi

  # Проверяем файлы/паттерны (все должны быть готовы)
  collect_targets
  ready_all=1

  for tgt in "${TARGETS[@]}"; do
    # Если это еще не раскрывшийся глоб (нет ни одного совпавшего файла),
    # то exists_and_ready вернет 1 — ждем.
    if ! exists_and_ready "$tgt"; then
      ready_all=0
      break
    fi
  done

  if (( ready_all )); then
    log "Все цели готовы."
    break
  fi

  sleep "$INTERVAL"
done

# ---------- Пост-обработка ----------
# Применяем chmod/chown и exec для реальных файлов (разворачиваем паттерны еще раз)
REAL_FILES=()
for f in "${FILES[@]}"; do REAL_FILES+=("$f"); done
for p in "${PATTERNS[@]}"; do
  for f in $p; do REAL_FILES+=("$f"); done
done

# Удаляем дубликаты
if (( ${#REAL_FILES[@]} > 0 )); then
  mapfile -t REAL_FILES < <(printf "%s\n" "${REAL_FILES[@]}" | awk 'NF' | sort -u)
fi

#if [[ -n "$CHMOD_MODE" && ${#REAL_FILES[@]} -gt 0 ]]; then
#  log "chmod ${CHMOD_MODE} для ${#REAL_FILES[@]} файла(ов)"
#  chmod "$CHMOD_MODE" "${REAL_FILES[@]}"
#fi
#
#if [[ -n "$CHOWN_SPEC" && ${#REAL_FILES[@]} -gt 0 ]]; then
#  log "chown ${CHOWN_SPEC} для ${#REAL_FILES[@]} файла(ов)"
#  chown "$CHOWN_SPEC" "${REAL_FILES[@]}"
#fi

#if [[ -n "$EXEC_CMD" && ${#REAL_FILES[@]} -gt 0 ]]; then
#  for f in "${REAL_FILES[@]}"; do
#    # Подставляем {} на путь
#    cmd="${EXEC_CMD//\{\}/$f}"
#    log "exec: $cmd"
#    bash -lc "$cmd"
#  done
#fi

exit 0
