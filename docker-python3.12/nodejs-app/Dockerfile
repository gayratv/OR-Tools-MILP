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

WORKDIR /app

# Создаем пользователя без root-прав
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Копируем только необходимые для запуска файлы из этапа сборки
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/dist ./dist

RUN npm install --omit=dev

EXPOSE 3000
CMD ["node", "dist/server.js"]