import type { Response } from "express";

/**
 * Простая SSE-обёртка: устанавливает заголовки, даёт методы send/close,
 * пингует каждые 15s, корректно отписывается.
 */
export function createSSE(res: Response) {
  res.status(200);
  res.setHeader("Content-Type", "text/event-stream; charset=utf-8");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no"); // Disable Nginx buffering
  (res as Response & { flushHeaders?: () => void }).flushHeaders?.();

  // начальный комментарий, чтобы некоторые прокси «проснулись»
  res.write(`: connected ${new Date().toISOString()}\n\n`);

  const heartbeat = setInterval(() => {
    res.write(`: ping ${Date.now()}\n\n`);
  }, 20000);

  // let lastId = 0;

  function send(data: string, opts?: { event?: string; id?: number }) {
    // const id = (opts?.id ?? ++lastId);
    // if (opts?.event) res.write(`event: ${opts.event}\n`);
    // res.write(`id: ${id}\n`);
    // data может быть многострочной
    for (const line of data.split(/\r?\n/)) {
      res.write(`${line}`);
    }
    res.write("\n");
  }

  function close() {
    clearInterval(heartbeat);
    // Отдельный 'comment' чтобы корректно завершить у клиентов
    res.write(`: closing\n\n`);
    res.end();
  }

  // Если клиент отвалился, закрываем сердцебиение
  res.on("close", close);

  return { send, close };
}
