import { Router } from "express";
import { streamContainerLogs } from "./controller.js";
import { env } from "../../config/env.js";

export const logsRouter = Router();

logsRouter.get("/logs/:container", streamContainerLogs);
// alias на дефолтный контейнер (как было у вас)
logsRouter.get("/logsf", (_req, res) =>
  res.redirect(`/logs/${env.defaultContainer}`)
);
