import { createServer } from "./server/createServer.js";
import { env } from "./config/env.js";

const app = createServer();
app.listen(env.port, () => {
  // eslint-disable-next-line no-console
  console.log(`SSE logs API listening on :${env.port}`);
});
