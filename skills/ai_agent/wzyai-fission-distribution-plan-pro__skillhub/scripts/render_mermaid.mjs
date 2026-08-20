import { spawn } from 'node:child_process';
import { access, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';


const HERE = path.dirname(fileURLToPath(import.meta.url));
const CLI = path.join(
  HERE,
  'node_modules',
  '@mermaid-js',
  'mermaid-cli',
  'src',
  'cli.js',
);


async function exists(candidate) {
  try {
    await access(candidate);
    return true;
  } catch {
    return false;
  }
}


async function findBrowser() {
  const candidates = [
    process.env.PUPPETEER_EXECUTABLE_PATH,
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
  ].filter(Boolean);
  for (const candidate of candidates) {
    if (await exists(candidate)) return candidate;
  }
  throw new Error(
    'No supported Chrome/Edge browser found. Set PUPPETEER_EXECUTABLE_PATH.',
  );
}


function run(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [CLI, ...args], {
      windowsHide: true,
    });
    let stderr = '';
    child.stderr.on('data', (chunk) => { stderr += chunk.toString(); });
    child.on('error', reject);
    child.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(stderr || `mmdc exited ${code}`));
    });
  });
}


export async function renderMermaid(input, svgOutput, pngOutput = null) {
  if (path.extname(svgOutput).toLowerCase() !== '.svg') {
    throw new Error('primary output must use .svg');
  }
  if (pngOutput && path.extname(pngOutput).toLowerCase() !== '.png') {
    throw new Error('raster output must use .png');
  }
  if (!(await exists(input))) throw new Error(`Mermaid input not found: ${input}`);
  const browser = await findBrowser();
  const configDir = await mkdtemp(path.join(tmpdir(), 'mermaid-browser-'));
  const configPath = path.join(configDir, 'puppeteer.json');
  await writeFile(
    configPath,
    JSON.stringify({ executablePath: browser, args: ['--no-sandbox'] }),
    'utf8',
  );
  try {
    await run([
      '--input', input,
      '--output', svgOutput,
      '--backgroundColor', 'transparent',
      '--puppeteerConfigFile', configPath,
    ]);
    if (pngOutput) {
      await run([
        '--input', input,
        '--output', pngOutput,
        '--backgroundColor', 'white',
        '--width', '1800',
        '--scale', '2',
        '--puppeteerConfigFile', configPath,
      ]);
    }
  } finally {
    await rm(configDir, { recursive: true, force: true });
  }
  return { svg: svgOutput, png: pngOutput };
}


if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [input, svg, png] = process.argv.slice(2);
  if (!input || !svg) {
    throw new Error(
      'usage: node render_mermaid.mjs input.mmd output.svg [output.png]',
    );
  }
  await renderMermaid(input, svg, png || null);
}
