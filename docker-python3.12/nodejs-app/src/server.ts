import dotenv from "dotenv";
import express from "express";
import { Connection } from "rabbitmq-client";

// Загружаем переменные окружения из файла .env
dotenv.config();

const app = express();
const port = Number(process.env.NODE_PORT ?? 3000);

async function setupRabbitMQ() {
  // Initialize
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const rabbit = new Connection("amqp://guest:guest@rabbitmq:5672");
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
  rabbit.on("error", (err) => {
    console.error("RabbitMQ connection error", err);
  });
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
  rabbit.on("connection", () => {
    console.log("Connection successfully (re)established");
  });

  // The example suggests creating a consumer is the way to declare a queue
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const sub = rabbit.createConsumer({
    queue: "messages",
    queueOptions: { durable: true },
  });
  // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
  sub.on("error", (err) => {
    console.error("Consumer error", err);
  });

  // Declare a publisher
  // eslint-disable-next-line @typescript-eslint/no-unsafe-assignment
  const pub = rabbit.createPublisher({
    confirm: true,
    maxAttempts: 2,
  });

  try {
    // Publish directly to a queue.
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
    await pub.send("messages", "nodejs start");
    console.log("Message 'nodejs start' sent to queue 'messages'");
  } catch (err) {
    console.error("Error sending message:", err);
  } finally {
    // Clean up
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
    await pub.close();
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
    await sub.close();
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call
    await rabbit.close();
  }
}

app.get("/", (_req, res) => {
  res.json({ message: "Hello from Express + TypeScript!" });
});

app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Node.js (TS) server listening on port ${port}`);
  void setupRabbitMQ();
});