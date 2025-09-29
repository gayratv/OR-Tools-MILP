import Docker from "dockerode";
import { PassThrough, type Readable, type Writable } from "node:stream";

// Общий клиент Docker (коннект к unix:///var/run/docker.sock по умолчанию)
export const docker = new Docker();

interface DockerModem {
  demuxStream(stream: Readable, stdout: Writable, stderr: Writable): void;
}

const modem = (docker as unknown as { modem: DockerModem }).modem;

/**
 * Возвращает raw-стрим логов контейнера + раздельные stdout/stderr.
 * ВАЖНО: вызывающий обязан закрывать/уничтожать стримы.
 */
export async function openContainerLogStreams(containerId: string, opts?: {
  since?: number;
  tail?: number | "all";
}) {
  const container = docker.getContainer(containerId);
  // Проверим, что контейнер реально существует
  await container.inspect();

  const raw = (await container.logs({
    follow: true,
    stdout: true,
    stderr: true,
    tail: typeof opts?.tail === "number" ? opts.tail : 0,
    since: opts?.since ?? 0,
    timestamps: false
  })) as Readable;

  const out = new PassThrough();
  const err = new PassThrough();

  modem.demuxStream(raw, out, err);

  return {
    raw,      // мультиплексированный поток Docker
    stdout: out,
    stderr: err,
    close: () => {
      raw.destroy();
      out.destroy();
      err.destroy();
    }
  };
}
