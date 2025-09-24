#!/bin/bash

# Устанавливаем режим "fail fast", чтобы скрипт прекращал работу при первой ошибке.
# 'e' - выход при ошибке, 'u' - выход при использовании необъявленной переменной,
# 'o pipefail' - выход, если команда в конвейере (pipe) завершается с ошибкой.
set -euo pipefail

# --- Конфигурация ---
# Используйте переменные для путей, чтобы их было легко изменить.
readonly BUILD_CONTEXT_DIR="./docker-python3.12"
readonly SCRIPT_DIR="./ya-cloud"
readonly NODE_APP_DIR="$BUILD_CONTEXT_DIR/nodejs-app"
readonly PYTHON_APP_DIR="$BUILD_CONTEXT_DIR/python-app"

# Список каталогов приложений, куда будут копироваться скрипты.
# Это упрощает добавление новых каталогов в будущем.
readonly TARGET_APP_DIRS=(
    "$BUILD_CONTEXT_DIR"
    "$NODE_APP_DIR"
    "$PYTHON_APP_DIR"
)

# --- Подготовка к сборке ---
echo "Подготовка файлов для сборки..."

for dir in "${TARGET_APP_DIRS[@]}"; do
    # Создаем каталог для скриптов, если он не существует.
    mkdir -p "${dir}/scripts"
    # Копируем скрипты в целевой каталог.
    cp "${SCRIPT_DIR}"/*.sh "${dir}/scripts/"
done

echo "Подготовка файлов для сборки завершена."
