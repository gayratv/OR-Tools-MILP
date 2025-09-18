# --- Этап 1: Сборщик с YC CLI ---
FROM python:3.12 as builder

# Устанавливаем системные зависимости, необходимые для сборки python-пакетов (например, pyodbc)
# В базовом образе python:3.12 уже есть build-essential, нужно доставить только unixodbc-dev
RUN apt-get update && \
    apt-get install -y --no-install-recommends unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Yandex Cloud CLI
RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY PY/requirements.txt .

# Копируем скрипты в /usr/local/bin, чтобы они были доступны в PATH
COPY scripts/*.sh /usr/local/bin/

# Устанавливаем зависимости в отдельный каталог /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip wheel setuptools && \
    pip wheel --wheel-dir=/wheels -r requirements.txt


# --- Этап 2: Финальный образ ---
FROM python:3.12-slim

# Создаем пользователя без root-прав
RUN useradd -m appuser
USER appuser

# Устанавливаем только runtime-зависимости для pyodbc
RUN apt-get update \
    && apt-get install -y --no-install-recommends unixodbc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /home/appuser/app

# Копируем YC CLI из сборщика
COPY --from=builder /root/yandex-cloud /home/appuser/yandex-cloud

# Копируем "колеса" зависимостей и устанавливаем их
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

# Копируем код приложения
COPY PY/ .

# Копируем скрипты и делаем их исполняемыми
COPY --chown=appuser:appuser scripts/ /home/appuser/scripts/
RUN chmod +x /home/appuser/scripts/*.sh

# Добавляем yc и скрипты в PATH
ENV PATH="/home/appuser/yandex-cloud/bin:/home/appuser/scripts:${PATH}"

# Команда по умолчанию для контейнера-калькулятора (пример)
CMD ["python", "main.py"]
