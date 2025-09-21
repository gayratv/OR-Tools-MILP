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

# Устанавливаем Yandex Cloud CLI
RUN curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash -s -- -a

WORKDIR /app

# Создаем пользователя без root-прав
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Копируем скрипты и делаем их исполняемыми
COPY --chown=appuser:appuser scripts/ /root/scripts/
RUN chmod +x /root/scripts/*.sh

RUN yc config set folder-id b1gbgjv35qvro3lmgaci \
  && yc config set cloud-id b1gib03pgvqrrfvhl3kb

# Копируем только необходимые для запуска файлы из этапа сборки
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist

RUN npm install --omit=dev

EXPOSE 3000
CMD ["node", "dist/server.js"]