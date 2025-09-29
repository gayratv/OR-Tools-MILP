import express from "express";
import { corsMw } from "../middlewares/cors.js";
import { errorHandler } from "../middlewares/error.js";
import { buildRoutes } from "./routes.js";

export function createServer() {
  const app = express();

  app.disable("x-powered-by");
  app.use(corsMw);

  app.use(buildRoutes());
  app.use(errorHandler);

  return app;
}
