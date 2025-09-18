# Базовый образ
FROM python:3.12

# Аргументы для сборки, чтобы не хранить ID в Dockerfile
# Можно передать при сборке: --build-arg CLOUD_ID=... --build-arg FOLDER_ID=...
ARG CLOUD_ID=b1gib03pgvqrrfvhl3kb
ARG FOLDER_ID=b1gbgjv35qvro3lmgaci

# Установка Yandex Cloud CLI
RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

# Добавляем yc в PATH
ENV PATH="/root/yandex-cloud/bin:${PATH}"

# Настройка профиля yc
RUN yc config profile create my-robot-profile && \
    yc config set cloud-id ${CLOUD_ID} && \
    yc config set folder-id ${FOLDER_ID}

# Устанавливаем системные зависимости для pyodbc (unixODBC)
#RUN apt-get update && apt-get install -y \
#     unixodbc \
#     unixodbc-dev \
#     && rm -rf /var/lib/apt/lists/*


# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY PY/ .

# Копируем скрипты в /usr/local/bin, чтобы они были доступны в PATH
COPY scripts/*.sh /usr/local/bin/

# Обновляем pip и ставим зависимости
#    pip install --upgrade pip  \
RUN --mount=type=cache,target=/root/pip-cache \
    pip install --cache-dir=/root/pip-cache -r requirements.txt \
    && rm -rf /root/.cache/pip


# Команда по умолчанию (можно поменять на запуск вашего приложения)
CMD ["bash"]
