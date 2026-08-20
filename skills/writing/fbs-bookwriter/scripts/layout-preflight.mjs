#!/usr/bin/env node
/**
 * BookWriter 3.0 排版导出预检。
 *
 * 当前策略：
 * - 对 md/html/txt 做结构化检查
 * - 对 docx/pdf 等不透明格式，优先寻找同名 md/html 伴随稿做代理检查
 * - 无伴随稿时给出显式预览提醒，而不是伪造“已通过”
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TEXT_EXTS = new Set(['.md', '.markdown', '.txt', '.html', '.htm']);
const OPAQUE_EXTS = new Set(['.docx', '.pdf']);

function parseArgs(argv) {
  const args = {
    input: null,
    template: 'default',
    reportFile: null,
    json: false,
    help: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const token = argv[i];
    if ((token === '--input' || token === '--file') && argv[i + 1]) args.input = argv[++i];
    else if (token === '--template' && argv[i + 1]) args.template = argv[++i];
    else if (token === '--report-file' && argv[i + 1]) args.reportFile = argv[++i];
    else if (token === '--json') args.json = true;
    else if (token === '--help' || token === '-h') args.help = true;
  }
  return args;
}

function printHelp() {
  console.log(`
用法：
  node scripts/layout-preflight.mjs --input <文件> [--template <模板>] [--json]
`);
}

function decodeHtmlEntities(text) {
  return text
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function stripHtml(html) {
  return decodeHtmlEntities(
    html
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<\/(h1|h2|h3|p|li|div|section|article)>/gi, '\n')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]+>/g, ' '),
  );
}

function normalizeText(text, ext) {
  const raw = ext === '.html' || ext === '.htm' ? stripHtml(text) : text;
  return raw.replace(/\r\n/g, '\n').replace(/\uFEFF/g, '').trim();
}

function findCompanionPath(inputPath) {
  const dir = path.dirname(inputPath);
  const ext = path.extname(inputPath).toLowerCase();
  const base = path.basename(inputPath, ext);
  const candidates = [
    `${base}.md`,
    `${base}.markdown`,
    `${base}.txt`,
    `${base}.html`,
    `${base}.htm`,
    `${base}.preview.md`,
    `${base}.preview.html`,
    `${base}-preview.md`,
    `${base}-preview.html`,
  ];
  for (const candidate of candidates) {
    const full = path.join(dir, candidate);
    if (fs.existsSync(full)) return full;
  }
  return null;
}

function analyzeMetrics(text) {
  const lines = text.split('\n');
  let headingCount = 0;
  let firstHeadingLine = -1;
  let maxLineLength = 0;
  let blankRun = 0;
  let blankRunMax = 0;
  let tocHint = false;
  let titlePageHint = false;

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    maxLineLength = Math.max(maxLineLength, line.length);
    if (!line) {
      blankRun += 1;
      blankRunMax = Math.max(blankRunMax, blankRun);
      continue;
    }
    blankRun = 0;

    if (/^#{1,3}\s+\S/.test(line)) {
      headingCount += 1;
      if (firstHeadingLine < 0) firstHeadingLine = i + 1;
    }
    if (/(目录|contents|table of contents|目次)/i.test(line)) tocHint = true;
    if (/(书名页|封面|版权页|扉页)/.test(line)) titlePageHint = true;
  }

  const titleHeadingPresent = firstHeadingLine > 0 && firstHeadingLine <= 12;
  return {
    lineCount: lines.length,
    headingCount,
    firstHeadingLine,
    maxLineLength,
    blankRunMax,
    tocHint,
    titleHeadingPresent,
    titlePageHint,
  };
}

function pushCheck(checks, id, status, summary) {
  checks.push({ id, status, summary });
}

function buildStructuredChecks(metrics) {
  const checks = [];
  pushCheck(
    checks,
    'title_heading',
    metrics.titleHeadingPresent ? 'ok' : 'warn',
    metrics.titleHeadingPresent
      ? `前 ${metrics.firstHeadingLine} 行内检测到标题型标题`
      : '前 12 行未检测到明显标题，书名页或标题页可能不足',
  );
  pushCheck(
    checks,
    'toc_or_outline',
    metrics.tocHint || metrics.headingCount >= 4 ? 'ok' : 'warn',
    metrics.tocHint || metrics.headingCount >= 4
      ? '存在目录或足够的标题层级'
      : '目录或章节层级信号较弱，导出后可能显得结构松散',
  );
  pushCheck(
    checks,
    'blank_page_risk',
    metrics.blankRunMax <= 2 ? 'ok' : 'warn',
    metrics.blankRunMax <= 2
      ? '未发现连续空行堆积'
      : `发现连续 ${metrics.blankRunMax} 行空白，导出后可能出现空白页风险`,
  );
  pushCheck(
    checks,
    'margin_risk',
    metrics.maxLineLength <= 120 ? 'ok' : 'warn',
    metrics.maxLineLength <= 120
      ? '长行长度可控'
      : `最长行 ${metrics.maxLineLength} 字符，存在页边距溢出风险`,
  );
  pushCheck(
    checks,
    'title_page_hint',
    metrics.titlePageHint || metrics.titleHeadingPresent ? 'ok' : 'warn',
    metrics.titlePageHint || metrics.titleHeadingPresent
      ? '检测到标题页或封面信号'
      : '未检测到书名页/封面信号，需人工确认标题页位置',
  );
  return checks;
}

function overallStatus(checks, opaqueWithoutCompanion) {
  if (checks.some((item) => item.status === 'fail')) return 'fail';
  if (opaqueWithoutCompanion || checks.some((item) => item.status === 'warn')) return 'warn';
  return 'ok';
}

function buildReport({ inputPath, analyzedPath, template, metrics, checks, opaqueWithoutCompanion, usedCompanion }) {
  const status = overallStatus(checks, opaqueWithoutCompanion);
  const warnings = checks.filter((item) => item.status === 'warn').map((item) => item.summary);
  if (opaqueWithoutCompanion) {
    warnings.unshift('输入文件为不透明格式，当前仅完成文件级检查；需补充同名 md/html 预览稿或人工预览 Word/PDF。');
  }

  const suggestions = [];
  if (checks.some((item) => item.id === 'margin_risk' && item.status === 'warn')) {
    suggestions.push('将超长句拆成更短段落，避免导出后超出页边距。');
  }
  if (checks.some((item) => item.id === 'blank_page_risk' && item.status === 'warn')) {
    suggestions.push('清理连续空行和孤立分页，避免出现空白页。');
  }
  if (checks.some((item) => item.id === 'title_page_hint' && item.status === 'warn')) {
    suggestions.push('补显式标题页或封面区块，并在导出前确认书名页位置。');
  }
  if (!suggestions.length) {
    suggestions.push('继续用宿主预览或 HTML 预览链做一次人工检查，确认标题页、目录和分页效果。');
  }

  const markdown = [
    '# 排版导出预检报告',
    '',
    `- 输入文件：\`${inputPath}\``,
    `- 分析来源：\`${analyzedPath}\``,
    `- 模板：\`${template}\``,
    `- 结果：\`${status}\``,
    usedCompanion ? `- 说明：原文件为不透明格式，已使用伴随稿 \`${analyzedPath}\` 代理检查。` : null,
    '',
    '## 结构指标',
    '',
    `- 行数：${metrics.lineCount}`,
    `- 标题数：${metrics.headingCount}`,
    `- 首个标题行：${metrics.firstHeadingLine > 0 ? metrics.firstHeadingLine : '未检测到'}`,
    `- 最长行长度：${metrics.maxLineLength}`,
    `- 最大连续空行：${metrics.blankRunMax}`,
    '',
    '## 检查项',
    '',
    '| 项目 | 状态 | 说明 |',
    '| --- | --- | --- |',
    ...checks.map((item) => `| ${item.id} | ${item.status} | ${item.summary} |`),
    '',
    '## 建议',
    '',
    ...suggestions.map((item) => `- ${item}`),
    '',
  ].filter(Boolean).join('\n');

  return {
    ok: status !== 'fail',
    status,
    inputPath,
    analyzedPath,
    usedCompanion,
    opaqueWithoutCompanion,
    metrics,
    checks,
    warnings,
    suggestions,
    markdown,
  };
}

export function runLayoutPreflight({ input, template = 'default', reportFile = null } = {}) {
  if (!input) throw new Error('缺少 --input <文件路径>');
  const inputPath = path.resolve(input);
  if (!fs.existsSync(inputPath)) throw new Error(`输入文件不存在：${inputPath}`);

  const ext = path.extname(inputPath).toLowerCase();
  const usedCompanion = OPAQUE_EXTS.has(ext);
  const analyzedPath = usedCompanion ? (findCompanionPath(inputPath) || inputPath) : inputPath;
  const analyzedExt = path.extname(analyzedPath).toLowerCase();

  let metrics = {
    lineCount: 0,
    headingCount: 0,
    firstHeadingLine: -1,
    maxLineLength: 0,
    blankRunMax: 0,
    tocHint: false,
    titleHeadingPresent: false,
    titlePageHint: false,
  };
  let checks = [];
  let opaqueWithoutCompanion = false;

  if (TEXT_EXTS.has(analyzedExt)) {
    const text = normalizeText(fs.readFileSync(analyzedPath, 'utf8'), analyzedExt);
    if (!text) throw new Error(`输入文件为空：${analyzedPath}`);
    metrics = analyzeMetrics(text);
    checks = buildStructuredChecks(metrics);
  } else {
    const stat = fs.statSync(inputPath);
    metrics = {
      lineCount: 0,
      headingCount: 0,
      firstHeadingLine: -1,
      maxLineLength: 0,
      blankRunMax: 0,
      tocHint: false,
      titleHeadingPresent: false,
      titlePageHint: false,
      fileBytes: stat.size,
    };
    opaqueWithoutCompanion = true;
    checks = [{
      id: 'opaque_format',
      status: 'warn',
      summary: `检测到 ${ext || '未知'} 文件，仅完成文件存在与大小检查（${stat.size} bytes）`,
    }];
  }

  const report = buildReport({
    inputPath,
    analyzedPath,
    template,
    metrics,
    checks,
    opaqueWithoutCompanion,
    usedCompanion: usedCompanion && analyzedPath !== inputPath,
  });

  const targetReportFile = path.resolve(
    reportFile || path.join(path.dirname(inputPath), `${path.basename(inputPath, ext)}.layout-preflight.md`),
  );
  fs.mkdirSync(path.dirname(targetReportFile), { recursive: true });
  fs.writeFileSync(targetReportFile, report.markdown, 'utf8');

  return {
    ...report,
    reportFile: targetReportFile,
  };
}

export function main(argv = process.argv) {
  const args = parseArgs(argv);
  if (args.help) {
    printHelp();
    return 0;
  }
  try {
    const result = runLayoutPreflight(args);
    if (args.json) {
      process.stdout.write(`${JSON.stringify({
        ok: result.ok,
        status: result.status,
        reportFile: result.reportFile,
        inputPath: result.inputPath,
        analyzedPath: result.analyzedPath,
        usedCompanion: result.usedCompanion,
        warnings: result.warnings,
      }, null, 2)}\n`);
    } else {
      process.stdout.write(`[layout-preflight] ${result.status} -> ${result.reportFile}\n`);
    }
    return result.ok ? 0 : 1;
  } catch (error) {
    if (args.json) {
      process.stdout.write(`${JSON.stringify({ ok: false, error: error.message }, null, 2)}\n`);
    } else {
      console.error(`[layout-preflight] ${error.message}`);
    }
    return 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  process.exit(main(process.argv));
}
