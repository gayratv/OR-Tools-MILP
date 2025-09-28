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

# Устанавливаем curl и bash
RUN apk add --no-cache curl bash

# Устанавливаем Yandex Cloud CLI
RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

# Создаем пользователя без root-прав
RUN addgroup -S appgroup && adduser -S -h /home/appuser -G appgroup appuser

# Устанавливаем рабочую директорию
WORKDIR /home/appuser/app

# Копируем YC CLI в домашнюю директорию нового пользователя
RUN cp -r /root/yandex-cloud /home/appuser/yandex-cloud

# Копируем скрипты
COPY scripts/ /home/appuser/scripts/

# Копируем только необходимые для запуска файлы из этапа сборки
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist

# Устанавливаем production-зависимости
RUN npm install --omit=dev

# Добавляем yc и скрипты в PATH
ENV PATH="/home/appuser/yandex-cloud/bin:/home/appuser/scripts:${PATH}"

# Меняем владельца всех файлов
RUN chown -R appuser:appgroup /home/appuser

# Переключаемся на пользователя
USER appuser

# Делаем скрипты исполняемыми
RUN chmod +x /home/appuser/scripts/*.sh

EXPOSE 3000 8000
#CMD ["node", "dist/server.js"]
CMD ["node", "dist/logs-server.js"]
