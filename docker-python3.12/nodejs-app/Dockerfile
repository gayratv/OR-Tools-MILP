# --- Этап 1: Сборка ---
FROM node:20-alpine AS builder

WORKDIR /app

# Копируем package.json и package-lock.json (если есть)
COPY package*.json ./

# Устанавливаем зависимости для сборки
RUN npm install

# Копируем исходный код
COPY . .

# Собираем TypeScript в JavaScript
RUN npm run build

# --- Этап 2: Финальный образ ---
FROM node:20-alpine

# Устанавливаем curl и bash для отладки
RUN apk add --no-cache curl bash

# Устанавливаем Yandex Cloud CLI
RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем скрипты (если они нужны)
COPY scripts/ /app/scripts/

# Копируем только необходимые для запуска файлы из этапа сборки
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist

# Устанавливаем production-зависимости
RUN npm install --omit=dev

# Добавляем yc и скрипты в PATH (пути для пользователя root)
ENV PATH="/root/yandex-cloud/bin:/app/scripts:${PATH}"

# Делаем скрипты исполняемыми
RUN chmod +x /app/scripts/*.sh

# Копируем и делаем исполняемым entrypoint скрипт
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 3000 8000

ENTRYPOINT ["/app/entrypoint.sh"]

# Команда по умолчанию для запуска приложения
CMD ["node", "dist/index.js"]
