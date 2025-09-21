import dotenv from "dotenv";
import express from "express";

// Загружаем переменные окружения из файла .env
dotenv.config();

const app = express();
const port = Number(process.env.NODE_PORT ?? 3000);

app.get("/", (_req, res) => {
  res.json({ message: "Hello from Express + TypeScript!" });
});

app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Node.js (TS) server listening on port ${port}`);
});
