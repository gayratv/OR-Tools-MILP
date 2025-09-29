import type { ErrorRequestHandler } from "express";

export const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  let status = 500;
  let message = "Internal Server Error";

  if (err instanceof Error) {
    message = err.message;
    // Проверяем, есть ли у ошибки свойство 'status'
    if ("status" in err) {
      const statusValue = (err as { status: unknown }).status;
      if (typeof statusValue === "number") {
        status = statusValue;
      }
    }
  }

  res.status(status).json({ error: message });
};
