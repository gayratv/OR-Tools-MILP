#!/bin/sh
set -e

# entrypoint.sh
#
# Этот скрипт выполняется при старте контейнера.
# Его задача - предоставить пользователю 'appuser' доступ к Docker-сокету,
# который монтируется с хост-машины.

DOCKER_SOCKET=/var/run/docker.sock

# Проверяем, существует ли Docker-сокет
if [ -S "$DOCKER_SOCKET" ]; then
    # Получаем GID (ID группы) файла сокета
    DOCKER_GID=$(stat -c '%g' "$DOCKER_SOCKET")

    # Создаем группу 'docker' с таким же GID, если она еще не существует
    if ! getent group "$DOCKER_GID" >/dev/null; then
        addgroup -g "$DOCKER_GID" -S docker
    fi

    # Добавляем нашего пользователя 'appuser' в эту группу
    adduser appuser docker
fi

# Запускаем основную команду контейнера (CMD) от имени 'appuser'
# su-exec - это легковесная замена 'sudo' или 'gosu'
exec su-exec appuser "$@"