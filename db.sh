#!/bin/bash

# Устанавливаем режим "fail fast", чтобы скрипт прекращал работу при первой ошибке.
# 'e' - выход при ошибке, 'u' - выход при использовании необъявленной переменной,
# 'o pipefail' - выход, если команда в конвейере (pipe) завершается с ошибкой.
set -euo pipefail

# --- Конфигурация ---
# Используйте переменные для путей, чтобы их было легко изменить.
readonly IMAGE_NAME="school_scheduler" # Исправлена опечатка в имени
readonly VERSION="latest"
readonly BUILD_CONTEXT_DIR="./docker"
readonly DOCKERFILE_PATH="${BUILD_CONTEXT_DIR}/Dockerfile"
readonly SOURCE_DIR="./src"
readonly SCRIPT_DIR="./ya-cloud"
readonly REQUIREMENTS_FILE="./requirements.txt"
readonly DEST_DIR="${BUILD_CONTEXT_DIR}/PY"

# --- Подготовка к сборке ---
# Создаем каталог для исходников, если он не существует.
mkdir -p "${DEST_DIR}"
mkdir -p "${DEST_DIR}/db"
mkdir -p "${BUILD_CONTEXT_DIR}/scripts"

# Копируем исходный код и зависимости в контекст сборки.
# Кавычки вокруг переменных предотвращают проблемы с пробелами в именах файлов.
cp "${SOURCE_DIR}"/*.py "${DEST_DIR}/"
cp "${SOURCE_DIR}"/db/rasp3-new-calculation.accdb "${DEST_DIR}/db/"
cp "${REQUIREMENTS_FILE}" "${DEST_DIR}/"

# Копируем необходимые скрипты
cp "${SCRIPT_DIR}"/{create-docker.sh,delete-docker.sh} "${BUILD_CONTEXT_DIR}/scripts/"

echo "Подготовка файлов для сборки завершена."

# --- Сборка Docker-образа ---
# Используем переменные для путей и имени образа.
#    --cache-from $IMAGE_NAME:$VERSION \
DOCKER_BUILDKIT=1 docker build --progress=plain \
    --file "${DOCKERFILE_PATH}" \
    --tag "${IMAGE_NAME}:${VERSION}" \
    "${BUILD_CONTEXT_DIR}"

echo -e "\nСобран образ: ${IMAGE_NAME}:${VERSION}"

docker tag "$IMAGE_NAME:$VERSION" gayrat/"$IMAGE_NAME:$VERSION"
docker push gayrat/"$IMAGE_NAME:$VERSION"

echo "docker push gayrat/$IMAGE_NAME:$VERSION"