#!/bin/bash

echo -e "Сборка двух образов"
# Устанавливаем режим "fail fast", чтобы скрипт прекращал работу при первой ошибке.
# 'e' - выход при ошибке, 'u' - выход при использовании необъявленной переменной,
# 'o pipefail' - выход, если команда в конвейере (pipe) завершается с ошибкой.
set -euo pipefail

IMAGE_NAME="python-app-yandex" # Исправлена опечатка в имени
VERSION="latest"
BUILD_CONTEXT_DIR="./python-app"
DOCKERFILE_PATH="${BUILD_CONTEXT_DIR}/Dockerfile-yandex"

DOCKER_BUILDKIT=1 docker build --progress=plain \
    --file "${DOCKERFILE_PATH}" \
    --tag "${IMAGE_NAME}:${VERSION}" \
    "${BUILD_CONTEXT_DIR}"

echo -e "\nСобран образ: ${IMAGE_NAME}:${VERSION}"

docker tag "$IMAGE_NAME:$VERSION" gayrat/"$IMAGE_NAME:$VERSION"
docker push gayrat/"$IMAGE_NAME:$VERSION"

echo "docker push gayrat/$IMAGE_NAME:$VERSION"