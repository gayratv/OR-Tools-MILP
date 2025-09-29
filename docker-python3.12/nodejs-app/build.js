import esbuild from "esbuild";
import { readFileSync } from "node:fs";

// Читаем package.json, чтобы получить список зависимостей
const { dependencies } = JSON.parse(readFileSync("./package.json", "utf8"));

// Конфигурация сборки
const config = {
  entryPoints: ["src/index.ts"],
  bundle: true,
  platform: "node",
  target: "node20",
  format: "esm", // Важно, так как у вас "type": "module" в package.json
  outfile: "dist/index.js",
  // Помечаем все production-зависимости как внешние
  external: Object.keys(dependencies || {}),
};

esbuild
  .build(config)
  .then(() => console.log("✅ Build successful!"))
  .catch(() => process.exit(1));