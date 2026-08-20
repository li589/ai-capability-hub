#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const entry = path.resolve(scriptDir, "../dist/index.js");

if (!fs.existsSync(entry)) {
  console.error("SkillPay 启动失败：未找到 dist/index.js，请先执行 npm run build。");
  process.exit(1);
}

try {
  await import(pathToFileURL(entry).href);
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
