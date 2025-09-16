import express from "express";
import { RowDataPacket } from "mysql2";
import { pool } from "./db.js";

const app = express();
const port = Number(process.env.NODE_PORT || 3000);

app.get("/", async (_req, res) => {
  try {
    const [rows] = await pool.query<({ now: string } & RowDataPacket)[]>("SELECT NOW() AS now");
    res.json({ status: "ok", db_time: rows[0].now });
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(500).json({ error: msg });
  }
});

app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Node.js (TS) listening on ${port}`);
});
