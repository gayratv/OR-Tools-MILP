#!/bin/bash

echo -e "Сборка образа"
# Устанавливаем режим "fail fast", чтобы скрипт прекращал работу при первой ошибке.
# 'e' - выход при ошибке, 'u' - выход при использовании необъявленной переменной,
# 'o pipefail' - выход, если команда в конвейере (pipe) завершается с ошибкой.
set -euo pipefail

IMAGE_NAME="yandex-mysql" # Исправлена опечатка в имени
VERSION="latest"
BUILD_CONTEXT_DIR="."
DOCKERFILE_PATH="${BUILD_CONTEXT_DIR}/Dockerfile"

DOCKER_BUILDKIT=1 docker build --progress=plain \
    --file "${DOCKERFILE_PATH}" \
    --tag "${IMAGE_NAME}:${VERSION}" \
    "${BUILD_CONTEXT_DIR}"

echo -e "\nСобран образ: ${IMAGE_NAME}:${VERSION}"
