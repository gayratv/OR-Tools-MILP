# --- Этап 1: Сборщик с YC CLI ---
FROM python:3.12 AS builder

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
COPY requirements.txt .

# Копируем скрипты в /usr/local/bin, чтобы они были доступны в PATH
COPY scripts/*.sh /usr/local/bin/

# Устанавливаем зависимости в отдельный каталог /wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip wheel setuptools && \
    pip wheel --wheel-dir=/wheels -r requirements.txt


# --- Этап 2: Финальный образ ---
FROM python:3.12

# Устанавливаем только runtime-зависимости для pyodbc
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        unixodbc \
        bash \
        curl \
        mc \
        default-mysql-client \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя без root-прав
RUN useradd -m appuser

ENV PYTHONUNBUFFERED=1 \
    PATH="/home/appuser/yandex-cloud/bin:/app/scripts:${PATH}"

WORKDIR /app

# Копируем YC CLI из сборщика
COPY --from=builder --chown=appuser:appuser /root/yandex-cloud /home/appuser/yandex-cloud

# Копируем "колеса" зависимостей и устанавливаем их
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

# Копируем код приложения
# Копируем скрипты и делаем их исполняемыми
#COPY --chown=appuser:appuser . .
COPY . .

 # Создаем директорию для выходных файлов и меняем владельца всего приложения
RUN mkdir -p /app/output && \
     chown -R appuser:appuser /app && \
     chmod +x /app/scripts/*.sh


# Переключаемся на пользователя
USER appuser

## ========== 3) dev/prod: только разный ENTRYPOINT ==========
ENTRYPOINT ["/app/scripts/entrypoint-dev.sh"]
