import { openContainerLogStreams } from "../../lib/docker.js";
import type { Readable } from "node:stream";

/**
 * Открывает стримы логов и возвращает читатели, чтобы контроллер мог
 * подписаться и прокидывать данные в SSE.
 */
export async function getLogStreams(containerId: string, opts?: {
  since?: number;
  tail?: number | "all";
}) {
  return openContainerLogStreams(containerId, opts);
}

// Утилита: читает чанки, превращает в строки безопасно по границам
export function onReadableLines(
  stream: Readable,
  onLine: (line: string) => void
) {
  let buf = "";
  stream.setEncoding("utf8");
  stream.on("data", (chunk: string) => {
    buf += chunk;
    let idx;
    while ((idx = buf.indexOf("\n")) >= 0) {
      const line = buf.slice(0, idx);
      buf = buf.slice(idx + 1);
      onLine(line);
    }
  });
  stream.on("end", () => {
    if (buf.length) onLine(buf);
  });
}
