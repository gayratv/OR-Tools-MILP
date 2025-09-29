import express, {Request, Response} from "express";
import {PassThrough, type Readable, type Writable} from "stream";
import Docker from "dockerode";

const PORT = 8000;
const DEFAULT_CONTAINER = "python-solver";

const app = express();
const docker = new Docker(); // подключение к unix:///var/run/docker.sock

// Типизация для docker.modem, так как в @types/dockerode он 'any'
interface DockerModem {
    demuxStream(
        stream: Readable,
        stdout: Writable,
        stderr: Writable
    ): void;
}

// Заголовки для SSE
function sseHead(res: Response): void {
    res.setHeader("Content-Type", "text/event-stream");
    res.setHeader("Cache-Control", "no-cache");
    res.setHeader("Connection", "keep-alive");
    res.setHeader("X-Accel-Buffering", "no"); // важно для Nginx
    if (typeof res.flushHeaders === 'function') {
        res.flushHeaders();
    }
}

// Отправка одного SSE-сообщения
function sseSend(
    res: Response,
    opts: { data: string; event?: string; id?: number | string }
): void {
    const {data, event = "log", id} = opts;
    // if (event) res.write(`event: ${event}\n`);
    // if (id) res.write(`id: ${id}\n`);
    for (const line of data.split(/\r?\n/)) {
        // if (line.length) res.write(`data: ${line}\n`);
        if (line.length) res.write(`${line}\n`);
    }
    res.write("\n");
}

// Healthcheck
app.get("/healthz", (_req: Request, res: Response) => {
    res.status(200).send("ok");
});

async function handleLogStream(req: Request, res: Response, containerName: string): Promise<void> {
    const tail = (req.query.tail as string) ?? "100";
    // const timestamps = ((req.query.ts as string) ?? "true") === "true";
    // не запрашивать временные метки
    const timestamps = ((req.query.ts as string) ?? "false") === "true";
    sseHead(res);

    try {
        const container = docker.getContainer(containerName);
        await container.inspect(); // проверка, что контейнер существует

        const logStream = await container.logs({
            follow: true,
            stdout: true,
            stderr: true,
            tail: parseInt(tail, 10),
            timestamps,
        });

        let id = 0;

        // Функция для отправки данных в SSE-поток
        const sendLog = (chunk: Buffer) => {
            id += 1;
            sseSend(res, {
                data: chunk.toString("utf8"),
                event: "log",
                id,
            });
        };

        // Docker мультиплексирует stdout и stderr. Нам нужно их разделить.
        // stdout и stderr будут пустыми потоками, в которые demuxStream будет писать данные.
        const stdout = new PassThrough();
        const stderr = new PassThrough();

        stdout.on("data", sendLog);
        stderr.on("data", sendLog);

        (docker.modem as DockerModem).demuxStream(logStream as Readable, stdout, stderr);

        logStream.on("end", () => {
            sseSend(res, {data: "stream ended", event: "end"});
            res.end();
        });

        req.on("close", () => {
            // Клиент отключился, уничтожаем поток, чтобы не было утечек ресурсов.
            (logStream as Readable).destroy();
        });
    } catch (e: unknown) {
        const message = e instanceof Error ? e.message : String(e);
        sseSend(res, {data: `error: ${message}`, event: "error"});
        res.end();
    }
}

// Алиас /logs → /logs/:container
app.get("/logs", (req: Request, res: Response) => {
    const name = (req.query.container as string) || DEFAULT_CONTAINER;
    // Не нужно вызывать await, т.к. Express обработает промис
    void handleLogStream(req, res, name);
});

// SSE endpoint
app.get("/logs/:container", (req: Request, res: Response) => {
    void handleLogStream(req, res, req.params.container);
});

app.get("/logsf", (req: Request, res: Response) => {
    void handleLogStream(req, res, DEFAULT_CONTAINER);
});

app.listen(PORT, () => {
    console.log(`SSE logs API listening on :${PORT}`);
});
