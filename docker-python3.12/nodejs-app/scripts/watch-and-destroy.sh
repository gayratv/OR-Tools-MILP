#!/bin/bash
# F:/_prg/python/OR-Tools-MILP/docker-python3.12/scripts/watch-and-destroy.sh

set -e

# Целевой контейнер для наблюдения
TARGET_CONTAINER_NAME=$1
# Таймаут (например, "2h", "90m", "3600s")
TIMEOUT=$2

if [ -z "$TARGET_CONTAINER_NAME" ] || [ -z "$TIMEOUT" ]; then
  echo "Ошибка: Укажите имя контейнера и таймаут."
  echo "Пример: $0 my-container-name 4h"
  exit 1
fi

echo "--- Supervisor запущен ---"
echo "Наблюдаю за контейнером: ${TARGET_CONTAINER_NAME}"
echo "Таймаут: ${TIMEOUT}"

# Получаем имя текущей VM из метаданных Yandex Cloud
# Это самый надежный способ, не требующий передачи имени VM извне.
INSTANCE_NAME=$(curl -s -H "Metadata-Flavor: Google" http://169.254.169.254/computeMetadata/v1/instance/name)
echo "Работаю на VM: ${INSTANCE_NAME}"

# Запускаем `docker wait` в фоновом режиме с таймаутом
(docker wait "${TARGET_CONTAINER_NAME}" &) | timeout "${TIMEOUT}"
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
  # Код 124 означает, что сработал таймаут
  echo "Таймаут ${TIMEOUT} достигнут! Контейнер '${TARGET_CONTAINER_NAME}' все еще работает."
  echo "Принудительно останавливаю контейнер..."
  docker stop "${TARGET_CONTAINER_NAME}"
  REASON="таймаут"
else
  # Контейнер завершился сам
  CALC_EXIT_CODE=$(docker inspect "${TARGET_CONTAINER_NAME}" --format='{{.State.ExitCode}}')
  echo "Контейнер '${TARGET_CONTAINER_NAME}' завершил работу с кодом ${CALC_EXIT_CODE}."
  REASON="завершение расчета"
fi

echo "Инициирую удаление VM '${INSTANCE_NAME}' по причине: ${REASON}..."

# Команда на самоуничтожение
# Флаг --delete-boot-disk-anyway гарантирует удаление диска, даже если VM уже остановлена
yc compute instance delete --name "${INSTANCE_NAME}" --delete-boot-disk-anyway

# Если команда удаления по какой-то причине не сработает,
# контейнер просто завершится с ошибкой.
# Но VM останется работать, что позволит вам подключиться и выяснить причину.
echo "Команда на удаление отправлена. Ожидаю отключения..."

# Бесконечный цикл, чтобы контейнер не завершился до того, как VM будет выключена
sleep infinity