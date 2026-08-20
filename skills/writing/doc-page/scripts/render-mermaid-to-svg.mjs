#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";

const args = process.argv.slice(2);
const positional = args.filter((arg) => !arg.startsWith("--"));
const inputFile = positional[0];
const outputFile = positional[1];
const mmdcArg = readOption("--mmdc");
const theme = readOption("--theme") || "neutral";
const background = readOption("--backgroundColor") || "transparent";
const quiet = args.includes("--quiet");

if (!inputFile || !outputFile) {
  console.error([
    "Usage:",
    "  node render-mermaid-to-svg.mjs diagram.mmd diagram.svg [options]",
    "",
    "Options:",
    "  --mmdc=/path/to/mmdc              Use a specific Mermaid CLI executable.",
    "  --theme=neutral                  Mermaid theme: default, neutral, forest, dark, base.",
    "  --backgroundColor=transparent    SVG background color.",
    "  --quiet                          Print only the output path.",
    "",
    "Renders Mermaid source to SVG for insertion into Build Doc figures.",
  ].join("\n"));
  process.exit(2);
}

const inputPath = path.resolve(inputFile);
const outputPath = path.resolve(outputFile);

if (!fs.existsSync(inputPath)) {
  fail(`Input Mermaid file not found: ${inputPath}`);
}

const mmdc = mmdcArg || findExecutable("mmdc");
if (!mmdc) {
  fail([
    "Mermaid CLI (mmdc) was not found.",
    "Install it with: npm install -g @mermaid-js/mermaid-cli",
    "Then rerun this script, or pass --mmdc=/path/to/mmdc.",
  ].join("\n"));
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
const result = spawnSync(mmdc, [
  "-i", inputPath,
  "-o", outputPath,
  "--theme", theme,
  "--backgroundColor", background,
], {
  encoding: "utf8",
  maxBuffer: 1024 * 1024 * 10,
});

if (result.error) fail(`Failed to run mmdc: ${result.error.message}`);
if (result.status !== 0) {
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  process.exit(result.status || 1);
}

if (!quiet) {
  console.log(`Wrote SVG: ${outputPath}`);
} else {
  console.log(outputPath);
}

function readOption(name) {
  const prefix = `${name}=`;
  const found = args.find((arg) => arg.startsWith(prefix));
  return found ? found.slice(prefix.length) : "";
}

function findExecutable(command) {
  const local = path.resolve("node_modules/.bin", command);
  if (fs.existsSync(local)) return local;
  const userLocal = path.join(os.homedir(), ".local/bin", command);
  if (fs.existsSync(userLocal)) return userLocal;
  const result = spawnSync("command", ["-v", command], {
    encoding: "utf8",
    shell: true,
  });
  if (result.status === 0) return result.stdout.trim().split(/\r?\n/)[0];
  return "";
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
