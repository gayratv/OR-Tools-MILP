# Базовый образ
FROM python:3.12

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
