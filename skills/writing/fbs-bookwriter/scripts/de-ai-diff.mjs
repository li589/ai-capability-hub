#!/usr/bin/env node
/**
 * BookWriter 3.0 去 AI 味对照报告。
 *
 * 目标不是自动判定“绝对自然”，而是提供：
 * - 改写覆盖率
 * - 常见 AI 口吻标记的前后变化
 * - 供用户复核的段落级差异样本
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const STRENGTH_THRESHOLDS = { light: 0.15, medium: 0.25, strong: 0.35 };
const MARKERS = [
  ['首先', /首先/g],
  ['其次', /其次/g],
  ['再次', /再次/g],
  ['最后', /最后/g],
  ['总之', /总之|综上所述/g],
  ['值得注意', /值得注意的是|需要注意的是/g],
  ['不可忽视', /不可忽视/g],
  ['在此基础上', /在此基础上/g],
  ['赋能', /赋能/g],
  ['助力', /助力/g],
  ['高质量发展', /高质量发展/g],
  ['随着', /随着/g],
];

function parseArgs(argv) {
  const args = {
    before: null,
    after: null,
    strength: 'medium',
    reportFile: null,
    json: false,
    help: false,
  };
  for (let i = 2; i < argv.length; i++) {
    const token = argv[i];
    if (token === '--before' && argv[i + 1]) args.before = argv[++i];
    else if (token === '--after' && argv[i + 1]) args.after = argv[++i];
    else if (token === '--strength' && argv[i + 1]) args.strength = argv[++i];
    else if (token === '--report-file' && argv[i + 1]) args.reportFile = argv[++i];
    else if (token === '--json') args.json = true;
    else if (token === '--help' || token === '-h') args.help = true;
  }
  return args;
}

function printHelp() {
  console.log(`
用法：
  node scripts/de-ai-diff.mjs --before <原稿> --after <改写稿> [--strength light|medium|strong] [--json]
`);
}

function stripHtml(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<\/(h1|h2|h3|p|li|div|section|article)>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, ' ');
}

function readTextFile(inputPath) {
  const resolved = path.resolve(inputPath);
  const ext = path.extname(resolved).toLowerCase();
  const raw = fs.readFileSync(resolved, 'utf8');
  const text = (ext === '.html' || ext === '.htm' ? stripHtml(raw) : raw)
    .replace(/\r\n/g, '\n')
    .replace(/\uFEFF/g, '')
    .trim();
  return { path: resolved, text };
}

function splitParagraphs(text) {
  return text
    .split(/\n{2,}/)
    .map((part) => part.replace(/\s+/g, ' ').trim())
    .filter(Boolean);
}

function markerCounts(text) {
  const counts = {};
  for (const [label, re] of MARKERS) {
    const matches = text.match(re);
    counts[label] = matches ? matches.length : 0;
  }
  return counts;
}

function paragraphDiff(beforeParagraphs, afterParagraphs) {
  const max = Math.max(beforeParagraphs.length, afterParagraphs.length);
  let changedCount = 0;
  const samples = [];

  for (let i = 0; i < max; i++) {
    const before = beforeParagraphs[i] || '';
    const after = afterParagraphs[i] || '';
    if (before !== after) {
      changedCount += 1;
      if (samples.length < 6) {
        samples.push({
          index: i + 1,
          before: before.slice(0, 140),
          after: after.slice(0, 140),
        });
      }
    }
  }

  return {
    changedCount,
    total: max,
    changeRatio: max > 0 ? changedCount / max : 0,
    samples,
  };
}

function markerDelta(beforeCounts, afterCounts) {
  return MARKERS.map(([label]) => ({
    label,
    before: beforeCounts[label] || 0,
    after: afterCounts[label] || 0,
    delta: (afterCounts[label] || 0) - (beforeCounts[label] || 0),
  })).filter((row) => row.before > 0 || row.after > 0);
}

function buildWarnings(changeRatio, strength, markerRows) {
  const warnings = [];
  const threshold = STRENGTH_THRESHOLDS[strength] ?? STRENGTH_THRESHOLDS.medium;
  if (changeRatio < threshold) {
    warnings.push(`按 ${strength} 强度预期，改写覆盖率偏低（当前 ${(changeRatio * 100).toFixed(1)}%）。`);
  }
  const stubborn = markerRows.filter((row) => row.after >= row.before && row.after > 0);
  if (stubborn.length) {
    warnings.push(`以下高频口吻词未下降：${stubborn.map((row) => row.label).join('、')}。`);
  }
  return warnings;
}

function buildMarkdown(result) {
  const markerTable = result.markerRows.length
    ? [
        '| 标记 | 原稿 | 改写稿 | 差值 |',
        '| --- | --- | --- | --- |',
        ...result.markerRows.map((row) => `| ${row.label} | ${row.before} | ${row.after} | ${row.delta} |`),
      ].join('\n')
    : '无明显高频口吻标记。';

  return [
    '# 去 AI 味差异报告',
    '',
    `- 原稿：\`${result.beforePath}\``,
    `- 改写稿：\`${result.afterPath}\``,
    `- 强度：\`${result.strength}\``,
    `- 段落改写覆盖率：${(result.changeRatio * 100).toFixed(1)}%`,
    '',
    '## 基本统计',
    '',
    `- 原稿字符数：${result.beforeChars}`,
    `- 改写稿字符数：${result.afterChars}`,
    `- 原稿段落数：${result.beforeParagraphCount}`,
    `- 改写稿段落数：${result.afterParagraphCount}`,
    '',
    '## 口吻标记变化',
    '',
    markerTable,
    '',
    '## 段落样本',
    '',
    ...(result.samples.length
      ? result.samples.flatMap((sample) => [
          `### 段落 ${sample.index}`,
          '',
          `- 原稿：${sample.before || '（空）'}`,
          `- 改写稿：${sample.after || '（空）'}`,
          '',
        ])
      : ['无段落级差异样本。', '']),
    '## 结论',
    '',
    ...(result.warnings.length
      ? result.warnings.map((item) => `- ${item}`)
      : ['- 改写覆盖率和口吻词下降情况基本符合预期，仍建议抽样复核 3-5 段。']),
    '',
  ].join('\n');
}

export function runDeAiDiff({ before, after, strength = 'medium', reportFile = null } = {}) {
  if (!before || !after) throw new Error('缺少 --before 和 --after');
  const normalizedStrength = Object.prototype.hasOwnProperty.call(STRENGTH_THRESHOLDS, strength)
    ? strength
    : 'medium';

  const beforeFile = readTextFile(before);
  const afterFile = readTextFile(after);
  if (!beforeFile.text || !afterFile.text) {
    throw new Error('原稿或改写稿为空，无法生成差异报告');
  }

  const beforeParagraphs = splitParagraphs(beforeFile.text);
  const afterParagraphs = splitParagraphs(afterFile.text);
  const diff = paragraphDiff(beforeParagraphs, afterParagraphs);
  const beforeCounts = markerCounts(beforeFile.text);
  const afterCounts = markerCounts(afterFile.text);
  const markerRows = markerDelta(beforeCounts, afterCounts);
  const warnings = buildWarnings(diff.changeRatio, normalizedStrength, markerRows);

  const result = {
    ok: true,
    beforePath: beforeFile.path,
    afterPath: afterFile.path,
    strength: normalizedStrength,
    beforeChars: beforeFile.text.length,
    afterChars: afterFile.text.length,
    beforeParagraphCount: beforeParagraphs.length,
    afterParagraphCount: afterParagraphs.length,
    changeRatio: diff.changeRatio,
    changedParagraphs: diff.changedCount,
    markerRows,
    samples: diff.samples,
    warnings,
  };

  const markdown = buildMarkdown(result);
  const ext = path.extname(afterFile.path);
  const targetReportFile = path.resolve(
    reportFile || path.join(path.dirname(afterFile.path), `${path.basename(afterFile.path, ext)}.de-ai-diff.md`),
  );
  fs.mkdirSync(path.dirname(targetReportFile), { recursive: true });
  fs.writeFileSync(targetReportFile, markdown, 'utf8');

  return {
    ...result,
    reportFile: targetReportFile,
    markdown,
  };
}

export function main(argv = process.argv) {
  const args = parseArgs(argv);
  if (args.help) {
    printHelp();
    return 0;
  }
  try {
    const result = runDeAiDiff(args);
    if (args.json) {
      process.stdout.write(`${JSON.stringify({
        ok: true,
        reportFile: result.reportFile,
        strength: result.strength,
        changeRatio: Number(result.changeRatio.toFixed(4)),
        warnings: result.warnings,
      }, null, 2)}\n`);
    } else {
      process.stdout.write(`[de-ai-diff] ${result.reportFile}\n`);
    }
    return 0;
  } catch (error) {
    if (args.json) {
      process.stdout.write(`${JSON.stringify({ ok: false, error: error.message }, null, 2)}\n`);
    } else {
      console.error(`[de-ai-diff] ${error.message}`);
    }
    return 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  process.exit(main(process.argv));
}
