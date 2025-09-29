# SSE Logs API (ESM + TypeScript)

Минималистичный сервер на Express, который стримит логи Docker-контейнера через Server-Sent Events (SSE). 
Архитектура разбита по слоям: `lib/` (SSE и Docker), `features/logs` (роуты/контроллер/сервис), `server/` и `middlewares/`.

## Требования
- Node.js 18+
- Доступ к Docker (`/var/run/docker.sock` по умолчанию)

## Установка и запуск
```bash
npm i
npm run dev
# или
npm run build && npm start
```

Переменные окружения:
```bash
export PORT=8000
export LOGS_DEFAULT_CONTAINER=python-solver
# export LOGS_ALLOWLIST="python-solver,nginx"
```

Эндпоинты:
- `GET /logs/:container` — SSE поток логов указанного контейнера.
  - query: `?since=<unixTs>&tail=all|<n>`
- `GET /logsf` — алиас на контейнер из `LOGS_DEFAULT_CONTAINER`.
- `GET /healthz` — healthcheck.

Пример:
```bash
curl -N http://localhost:8000/logs/python-solver
curl -N 'http://localhost:8000/logs/python-solver?tail=100'
curl -N http://localhost:8000/logsf
```
