import type {Request, Response} from "express";
import {createSSE} from "../../lib/sse.js";
import {getQueryParamString} from "../../lib/utils.js";
import {getLogStreams, onReadableLines} from "./service.js";

/**
 * SSE-стрим логов. Поддерживает query: ?since=...&tail=...
 * Источник stdout помечаем event: "stdout", stderr — "stderr".
 */
export async function streamContainerLogs(req: Request, res: Response) {
    // Безопасно извлекаем containerId из параметров (предпочтительно) или query.
    const containerId = getQueryParamString(req.params.container) ?? getQueryParamString(req.query.container) ?? "";

    if (!containerId) return res.status(400).json({error: "container required"});

    // Валидация/allowlist (минимум — буквы/цифры, — _ .)
    if (!/^[\w.-]+$/.test(containerId)) {
        return res.status(400).json({error: "bad container id"});
    }

    // Безопасно парсим query-параметры since и tail
    const sinceRaw = getQueryParamString(req.query.since);
    const since = sinceRaw ? Number(sinceRaw) : undefined;
    const tailRaw = getQueryParamString(req.query.tail);
    const tail = tailRaw === "all" ? "all" : tailRaw ? Number(tailRaw) : undefined;

    const sse = createSSE(res);

    try {
        const {raw, stdout, stderr, close} = await getLogStreams(containerId, {since, tail});

        const cleanup = () => {
            raw.off("error", onErr);
            stdout.off("error", onErr);
            stderr.off("error", onErr);
            close();
            sse.close();
        };

        const onErr = (e: unknown) => {
            sse.send(JSON.stringify({level: "error", message: String(e)}), {event: "error"});
            cleanup();
        };

        raw.on("error", onErr);
        stdout.on("error", onErr);
        stderr.on("error", onErr);

        onReadableLines(stdout, (line) => sse.send(line, {event: "stdout"}));
        onReadableLines(stderr, (line) => sse.send(line, {event: "stderr"}));

        // Клиент отключился — чистим ресурсы
        res.on("close", cleanup);
    } catch (e) {
        sse.send(JSON.stringify({level: "error", message: String(e)}), {event: "error"});
        sse.close();
    }
}
