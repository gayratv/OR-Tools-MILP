export const env = {
  port: Number(process.env.PORT ?? 8000),
  defaultContainer: process.env.LOGS_DEFAULT_CONTAINER ?? "python-solver",
  // Опционально: ограничить какие контейнеры можно смотреть
  allowlist: (process.env.LOGS_ALLOWLIST ?? "")
    .split(",")
    .map(s => s.trim())
    .filter(Boolean),
};
