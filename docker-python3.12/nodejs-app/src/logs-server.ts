import express, {Request, Response} from "express";
import Docker from "dockerode";

const PORT = Number(process.env.PORT ?? 8000);
const DEFAULT_CONTAINER = process.env.DEFAULT_CONTAINER ?? "pyapp";

const app = express();
const docker = new Docker(); // подключение к unix:///var/run/docker.sock

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
    if (event) res.write(`event: ${event}\n`);
    if (id) res.write(`id: ${id}\n`);
    for (const line of data.split(/\r?\n/)) {
        if (line.length) res.write(`data: ${line}\n`);
    }
    res.write("\n");
}

// Healthcheck
app.get("/healthz", (_req: Request, res: Response) => {
    res.status(200).send("ok");
});

// Алиас /logs → /logs/:container
app.get("/logs", (req: Request, res: Response) => {
    const name = (req.query.container as string) || DEFAULT_CONTAINER;
    req.url = `/logs/${encodeURIComponent(name)}${
        req.url.includes("?") ? req.url.slice(req.url.indexOf("?")) : ""
    }`;

    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore: Используем внутренний роутер
    app._router.handle(req, res);
});

// SSE endpoint
app.get("/logs/:container", async (req: Request, res: Response) => {
    const name = req.params.container;
    const tail = (req.query.tail as string) ?? "100";
    const timestamps = ((req.query.ts as string) ?? "true") === "true";

    sseHead(res);

    try {
        const container = docker.getContainer(name);
        await container.inspect(); // проверка, что контейнер существует

        const logStream = await container.logs({
            follow: true,
            stdout: true,
            stderr: true,
            tail: parseInt(tail, 10),
            timestamps,
        });

        let id = 0;

        logStream.on("data", (chunk: Buffer) => {
            id += 1;
            sseSend(res, {
                data: chunk.toString("utf8"),
                event: "log",
                id,
            });
        });

        logStream.on("end", () => {
            sseSend(res, {data: "stream ended", event: "end"});
            res.end();
        });

        logStream.on("error", (e: Error) => {
            sseSend(res, {data: `stream error: ${e.message}`, event: "error"});
            res.end();
        });

        req.on("close", () => {
            // Клиент отключился, уничтожаем поток, чтобы не было утечек ресурсов.
            logStream.destroy();
        });
    } catch (e: unknown) {
        const message = e instanceof Error ? e.message : String(e);
        sseSend(res, {data: `error: ${message}`, event: "error"});
        res.end();
    }
});

app.listen(PORT, () => {
    console.log(`SSE logs API listening on :${PORT}`);
});
