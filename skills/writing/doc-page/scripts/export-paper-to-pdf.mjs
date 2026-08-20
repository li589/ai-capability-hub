#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";
import { spawnSync } from "node:child_process";

const args = process.argv.slice(2);
const positional = args.filter((arg) => !arg.startsWith("--"));
const inputFile = positional[0];
const outputFile = positional[1];

const chromeArg = readOption("--chrome");
const pdfinfoArg = readOption("--pdfinfo");
const pdftoppmArg = readOption("--pdftoppm");
const renderDirArg = readOption("--render-dir");
const timeoutMs = Number(readOption("--timeout-ms") || 30000);
const skipValidation = args.includes("--no-validate");
const quiet = args.includes("--quiet");

if (!inputFile || !outputFile) {
  console.error([
    "Usage:",
    "  node export-paper-to-pdf.mjs report.html report.pdf [options]",
    "",
    "Options:",
    "  --chrome=/path/to/Chrome        Use a specific Chrome/Chromium executable.",
    "  --pdfinfo=/path/to/pdfinfo      Use a specific Poppler pdfinfo executable.",
    "  --pdftoppm=/path/to/pdftoppm    Use a specific Poppler pdftoppm executable.",
    "  --render-dir=tmp/pdfs           Render PDF pages to PNGs for visual QA.",
    "  --timeout-ms=30000              Browser wait timeout.",
    "  --no-validate                  Skip PDF metadata validation.",
    "  --quiet                        Print only the output path.",
    "",
    "Exports a Build Doc HTML file to A4 PDF. Flow-pagination templates print #source; legacy fixed-page templates may print #pages.",
  ].join("\n"));
  process.exit(2);
}

const inputPath = path.resolve(inputFile);
const outputPath = path.resolve(outputFile);

if (!fs.existsSync(inputPath)) {
  fail(`Input file not found: ${inputPath}`);
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });

const playwright = loadPlaywright();
const chromePath = chromeArg || findChrome();
const launchOptions = chromePath ? { headless: true, executablePath: chromePath } : { headless: true };

const browser = await playwright.chromium.launch(launchOptions);
try {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 1600 },
    deviceScaleFactor: 1,
  });
  page.setDefaultTimeout(timeoutMs);
  await page.goto(pathToFileUrl(inputPath), { waitUntil: "load" });
  await waitForPaperReady(page);
  const preflight = await inspectPaper(page);
  if (preflight.overflows.length) {
    const pages = preflight.overflows.map((item) => item.page).join(", ");
    fail(`HTML preview has overflowing page content on page(s): ${pages}`);
  }
  await page.emulateMedia({ media: "print" });
  await page.pdf({
    path: outputPath,
    format: "A4",
    printBackground: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" },
    preferCSSPageSize: true,
  });
} finally {
  await browser.close();
}

const checks = skipValidation ? null : validatePdf(outputPath);
if (renderDirArg) {
  renderPdf(outputPath, path.resolve(renderDirArg));
}

if (quiet) {
  console.log(outputPath);
} else {
  console.log(`Wrote PDF: ${outputPath}`);
  if (checks) {
    console.log(`Pages: ${checks.pages || "unknown"}`);
    if (checks.pageSize) console.log(`Page size: ${checks.pageSize}`);
  }
  if (renderDirArg) console.log(`Rendered PNG pages: ${path.resolve(renderDirArg)}`);
}

function readOption(name) {
  const prefix = `${name}=`;
  const found = args.find((arg) => arg.startsWith(prefix));
  return found ? found.slice(prefix.length) : "";
}

function fail(message) {
  console.error(message);
  process.exit(1);
}

function loadPlaywright() {
  const localRequire = createRequire(import.meta.url);
  const candidates = [
    "",
    path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"),
    process.env.NODE_PATH || "",
  ].filter(Boolean);

  for (const moduleDir of candidates) {
    try {
      const req = moduleDir ? createRequire(path.join(moduleDir, "noop.js")) : localRequire;
      return req("playwright");
    } catch {
      // Try the next likely runtime location.
    }
  }

  fail([
    "Could not load the Playwright Node package.",
    "Run with the Codex bundled Node runtime, set NODE_PATH to a node_modules directory containing playwright,",
    "or install playwright in the current project.",
  ].join(" "));
}

function findChrome() {
  const envChrome = process.env.CHROME_PATH || process.env.PLAYWRIGHT_CHROME_EXECUTABLE;
  if (envChrome && fs.existsSync(envChrome)) return envChrome;

  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/snap/bin/chromium",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate)) || "";
}

async function waitForPaperReady(page) {
  await page.waitForFunction(() => {
    const pages = document.querySelectorAll(".page-frame");
    const images = Array.from(document.images);
    return pages.length > 0 && images.every((img) => img.complete && img.naturalWidth > 0);
  });
}

async function inspectPaper(page) {
  return page.evaluate(() => {
    const pageContent = Array.from(document.querySelectorAll(".page-content"));
    const overflows = pageContent
      .map((el, index) => ({
        page: index + 1,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
      }))
      .filter((item) => item.scrollHeight > item.clientHeight + 1);
    return {
      pages: document.querySelectorAll(".page-frame").length,
      overflows,
      images: Array.from(document.images).map((img) => ({
        src: img.getAttribute("src") || "",
        complete: img.complete,
        naturalWidth: img.naturalWidth,
        naturalHeight: img.naturalHeight,
      })),
    };
  });
}

function validatePdf(pdfPath) {
  const pdfinfo = pdfinfoArg || findExecutable("pdfinfo");
  if (!pdfinfo) {
    console.warn("pdfinfo was not found; skipped PDF metadata validation.");
    return null;
  }
  const result = spawnSync(pdfinfo, [pdfPath], { encoding: "utf8" });
  if (result.error) fail(`Failed to run pdfinfo: ${result.error.message}`);
  if (result.status !== 0) {
    if (result.stderr) process.stderr.write(result.stderr);
    fail("pdfinfo validation failed.");
  }

  const pages = matchLine(result.stdout, /^Pages:\s+(.+)$/m);
  const pageSize = matchLine(result.stdout, /^Page size:\s+(.+)$/m);
  if (pageSize && !/\bA4\b/i.test(pageSize)) {
    console.warn(`Warning: expected A4 page size, got: ${pageSize}`);
  }
  return { pages, pageSize };
}

function renderPdf(pdfPath, renderDir) {
  const pdftoppm = pdftoppmArg || findExecutable("pdftoppm");
  if (!pdftoppm) {
    console.warn("pdftoppm was not found; skipped PNG rendering.");
    return;
  }
  fs.mkdirSync(renderDir, { recursive: true });
  const prefix = path.join(renderDir, path.basename(pdfPath, path.extname(pdfPath)));
  const result = spawnSync(pdftoppm, ["-png", "-r", "120", pdfPath, prefix], {
    encoding: "utf8",
  });
  if (result.error) fail(`Failed to run pdftoppm: ${result.error.message}`);
  if (result.status !== 0) {
    if (result.stderr) process.stderr.write(result.stderr);
    fail("pdftoppm rendering failed.");
  }
}

function findExecutable(command) {
  const bundled = path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin", command);
  if (fs.existsSync(bundled)) return bundled;
  const result = spawnSync("command", ["-v", command], {
    encoding: "utf8",
    shell: true,
  });
  if (result.status === 0) return result.stdout.trim().split(/\r?\n/)[0];
  return "";
}

function matchLine(text, pattern) {
  const match = text.match(pattern);
  return match ? match[1].trim() : "";
}

function pathToFileUrl(filePath) {
  let resolved = path.resolve(filePath).replace(/\\/g, "/");
  if (!resolved.startsWith("/")) resolved = `/${resolved}`;
  return `file://${encodeURI(resolved)}`;
}
