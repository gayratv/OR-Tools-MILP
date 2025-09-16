# --- build stage ---
FROM node:20-alpine AS build
WORKDIR /usr/src/app

# Устанавливаем deps отдельно, чтобы кешировалось
COPY package.json package-lock.json* ./
RUN npm ci

# Код и конфиги
COPY tsconfig.json eslint.config.js ./
COPY src ./src

# Линт + сборка
RUN npm run lint && npm run build

# --- runtime stage ---
FROM node:20-alpine AS runtime
WORKDIR /usr/src/app
ENV NODE_ENV=production

# Минимально необходимые файлы
COPY --from=build /usr/src/app/dist ./dist
COPY package.json package-lock.json* ./
RUN npm ci --omit=dev

EXPOSE 3000
CMD ["node", "dist/server.js"]
