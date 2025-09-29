import { Router } from "express";
import { logsRouter } from "../features/logs/routes.js";

export function buildRoutes() {
  const r = Router();
  r.use(logsRouter);

  r.get("/healthz", (_req, res) => res.json({ ok: true }));
  return r;
}
