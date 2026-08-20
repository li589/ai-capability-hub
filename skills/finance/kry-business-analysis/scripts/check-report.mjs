#!/usr/bin/env node
/**
 * check-report.mjs - HTML 报告自动质检脚本（只读，不修改文件）
 *
 * 目的：把「机器可判定」的质检项自动化，秒级定位问题，AI 只保留业务语义判断
 * （数值合理性、环比逻辑、洞察是否有数据支撑等机器判不了的部分）。
 *
 * 用法：
 *   node scripts/check-report.mjs <report.html>
 *
 * 退出码：
 *   0 = 无 ERROR（可能有 WARN，需人工确认）
 *   1 = 存在 ERROR（必须修复后重新生成）
 *   2 = 参数错误 / 文件不存在
 *
 * 检测项（ERROR=必修，WARN=人工确认）：
 *   [E] 占位符残留        {{}} / 注释占位 / undefined / NaN / N/A / 加载中
 *   [E] 空表格            <tbody></tbody>
 *   [E] 图表容器-脚本配对  .chart-box 有 id 但无 KRY.xxx / echarts.init 对应 → 白屏
 *   [E] 空数据图表        data:[] / data:[null,null,...] （series 数据为空或全 null/NaN → 白屏）
 *   [E] JS 语法错误       内联 <script> 编译失败（{{}} 残留 / 括号错配等）→ 图表白屏
 *   [E] 图表未定义变量    series/data 引用未声明标识符（如 series_data）→ 运行时 ReferenceError
 *   [E] HTML 结构         script/style 标签未配对、缺 ECharts CDN
 *   [W] 用列表代图表      <ul> 内含金额/百分比（疑似应用图表）
 *   [I] 内容数量          统计 insight / action / kpi / hero-highlight 数量，具体是否充分由 AI 结合场景判断
 *
 * 模式（--mode standard|custom，缺省按标准模板特征 class 命中数自动识别，≥3 类=standard）：
 *   standard = 标准模板，全量检查（含占位注释、图表容器配对、内容数量统计等模板专属项）
 *   custom   = 自定义 HTML，仅查技术正确性（占位符/空表格/空数据/HTML结构/JS语法/通用DOM引用配对）
 */

import { readFileSync, existsSync } from 'fs';
import vm from 'node:vm';

// ─── 参数 ────────────────────────────────────────────────────────────────
const rawArgs = process.argv.slice(2);
let file = null;
let modeArg = null;
for (let i = 0; i < rawArgs.length; i++) {
  const a = rawArgs[i];
  if (a === '--mode') { modeArg = rawArgs[++i]; continue; }
  if (a.startsWith('--mode=')) { modeArg = a.slice('--mode='.length); continue; }
  if (!file && !a.startsWith('--')) file = a;
}
if (modeArg && modeArg !== 'standard' && modeArg !== 'custom') {
  console.error(`❌ --mode 仅支持 standard | custom，收到: ${modeArg}`);
  process.exit(2);
}
if (!file) {
  console.error('用法: node scripts/check-report.mjs <report.html> [--mode standard|custom]');
  process.exit(2);
}
if (!existsSync(file)) {
  console.error(`❌ 文件不存在: ${file}`);
  process.exit(2);
}
const html = readFileSync(file, 'utf-8');

// ─── 模式识别：standard（标准模板·全量检查）/ custom（自定义·仅技术正确性）───
// 显式 --mode 优先；否则按标准模板特征 class 命中数自动判定（≥3 类视为标准模板）
const TEMPLATE_MARKERS = [
  /class\s*=\s*["'][^"']*\bhero-highlight\b/,
  /class\s*=\s*["'][^"']*\bkpi-card\b/,
  /class\s*=\s*["'][^"']*\bkpi-grid\b/,
  /class\s*=\s*["'][^"']*\bchart-box\b/,
  /class\s*=\s*["'][^"']*\bsection-title\b/,
  /class\s*=\s*["'][^"']*\binsight\b/,
  /class\s*=\s*["'][^"']*\baction-card\b/,
];
const markerHits = TEMPLATE_MARKERS.filter((re) => re.test(html)).length;
const mode = modeArg || (markerHits >= 3 ? 'standard' : 'custom');
const isStandard = mode === 'standard';

const errors = [];
const warns = [];
const passes = [];
const E = (item, detail) => errors.push({ item, detail });
const W = (item, detail) => warns.push({ item, detail });
const P = (item) => passes.push(item);

// ─── 1. 占位符残留 ────────────────────────────────────────────────────────
const placeholderRules = [
  { re: /\{\{[^}]*\}\}/g, name: '{{变量}} 未替换' },
  { re: /\bundefined\b/g, name: 'undefined 残留' },
  { re: /\bNaN\b/g, name: 'NaN 残留' },
  { re: />\s*N\/A\s*</g, name: 'N/A 残留' },
  { re: /(数据加载中|加载中|loading\.\.\.)/gi, name: '临时占位文案(加载中/loading)' },
];
// 占位注释是标准模板专属标记，仅 standard 模式检查
if (isStandard) {
  placeholderRules.push(
    { re: /\/\*\s*(DATA|CHART_ID|UNIT|SUB|TITLE)\b[^*]*\*\//gi, name: '/* 占位注释 */ 未替换' },
    { re: /<!--\s*(DATA|CHART_ID|TITLE|SUB|HERO|SECTIONS|FOOTER)\b[^>]*-->/gi, name: '<!-- 占位注释 --> 未替换' },
  );
}
let placeholderHit = false;
for (const r of placeholderRules) {
  const m = html.match(r.re);
  if (m && m.length) {
    placeholderHit = true;
    E('占位符残留', `${r.name} × ${m.length}（示例: ${m[0].slice(0, 40)}）`);
  }
}
if (!placeholderHit) P('占位符残留：无');

// ─── 2. 空表格 <tbody></tbody> ───────────────────────────────────────────
const emptyTbody = html.match(/<tbody>\s*<\/tbody>/gi);
if (emptyTbody && emptyTbody.length) {
  E('空表格', `<tbody></tbody> × ${emptyTbody.length}（应有数据行或降级为「暂无数据」卡片）`);
} else {
  P('空表格：无');
}

// ─── 3. 图表容器-脚本配对 ─────────────────────────────────────────────────
// 提取所有初始化引用的 id：KRY.xxx('id') 或 getElementById('id')
const initIds = new Set();
const initRe = /(?:getElementById\(\s*["']([^"']+)["']|KRY\.\w+\(\s*["']([^"']+)["'])/g;
let im;
while ((im = initRe.exec(html)) !== null) {
  initIds.add(im[1] || im[2]);
}
// 提取含 chart-box 且带 id 的 div 容器（供 standard 配对与后续 usesChart 判断）
const boxIds = [];
const divTagRe = /<div\b[^>]*>/gi;
let dm;
while ((dm = divTagRe.exec(html)) !== null) {
  const tag = dm[0];
  if (/class\s*=\s*["'][^"']*\bchart-box\b/.test(tag)) {
    const idM = tag.match(/\bid\s*=\s*["']([^"']+)["']/);
    if (idM) boxIds.push(idM[1]);
    else if (isStandard) E('图表容器缺id', `存在 .chart-box 容器但无 id，无法绑定图表`);
  }
}
if (isStandard) {
  // 标准模板：chart-box 容器必须有配对的 KRY/echarts.init
  const orphanBoxes = boxIds.filter((id) => !initIds.has(id));
  if (orphanBoxes.length) {
    E('图表白屏(容器无初始化)', `容器 id 无配对的 KRY/echarts.init: ${orphanBoxes.join(', ')}`);
  } else if (boxIds.length) {
    P(`图表容器-脚本配对：${boxIds.length} 个全部配对`);
  }
} else {
  // 自定义 HTML：通用配对——echarts.init/getElementById 引用的 DOM id 必须真实存在
  const domIds = new Set();
  const idAttrRe = /\bid\s*=\s*["']([^"']+)["']/g;
  let idm;
  while ((idm = idAttrRe.exec(html)) !== null) domIds.add(idm[1]);
  const missingDom = [...initIds].filter((id) => !domIds.has(id));
  if (missingDom.length) {
    E('图表白屏(引用不存在的DOM)', `echarts.init/getElementById 引用了 HTML 中不存在的 id: ${missingDom.join(', ')}`);
  } else if (initIds.size) {
    P(`图表 DOM 引用校验：${initIds.size} 个引用全部存在`);
  }
}

// ─── 4. 空数据图表 data:[] / 全 null·NaN 数组 ─────────────────────────────
// data:[] = series 数据为空；data:[null,null,...] = 数组有长度但全为 null/NaN，
// 多因字段映射错误（如把 {categories,values} 平行数组当对象数组访问 v.name/v.value）→ 白屏
const emptyData = html.match(/data\s*:\s*\[\s*\]/g);
const nullData = html.match(/data\s*:\s*\[\s*(?:null|NaN|undefined)\s*(?:,\s*(?:null|NaN|undefined)\s*)+\]/g);
if (emptyData && emptyData.length) {
  E('空数据图表', `data:[] × ${emptyData.length}（series 数据为空，图表无意义）`);
}
if (nullData && nullData.length) {
  E('全空值数据图表(白屏)', `data:[null/NaN...] × ${nullData.length}（数组全为 null/NaN，多因字段映射错误——如把 {categories,values} 当对象数组访问 v.name/v.value；应直接内联组件数组）`);
}
if (!(emptyData && emptyData.length) && !(nullData && nullData.length)) {
  P('空数据图表：无');
}

// ─── 5. HTML 结构完整性 ───────────────────────────────────────────────────
const scriptOpen = (html.match(/<script\b/gi) || []).length;
const scriptClose = (html.match(/<\/script>/gi) || []).length;
if (scriptOpen !== scriptClose) E('HTML结构', `<script> ${scriptOpen} 个 vs </script> ${scriptClose} 个 未配对`);
const styleOpen = (html.match(/<style\b/gi) || []).length;
const styleClose = (html.match(/<\/style>/gi) || []).length;
if (styleOpen !== styleClose) E('HTML结构', `<style> ${styleOpen} 个 vs </style> ${styleClose} 个 未配对`);
const hasEcharts = /echarts(\.min)?\.js|echarts@/.test(html);
const usesChart = boxIds.length > 0 || /echarts\.init|KRY\./.test(html);
if (usesChart && !hasEcharts) E('HTML结构', '使用了图表但缺少 ECharts CDN 引用');
if (scriptOpen === scriptClose && styleOpen === styleClose && (!usesChart || hasEcharts)) P('HTML结构完整性：通过');

// ─── 5.5 JS 语法 + 未定义变量校验（图表白屏根因，零依赖 node:vm）─────────────
// 抽取所有内联 <script>（跳过带 src 的外链 CDN），逐段编译 + 静态扫描
const inlineScripts = [];
const scriptTagRe = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
let stm;
while ((stm = scriptTagRe.exec(html)) !== null) {
  if (/\bsrc\s*=/i.test(stm[1] || '')) continue; // 外链 CDN 跳过
  if (stm[2] && stm[2].trim()) inlineScripts.push(stm[2]);
}
let jsAllOk = inlineScripts.length > 0;
inlineScripts.forEach((code, i) => {
  // (1) 语法校验：new vm.Script 只编译不执行，抓 {{}} 残留 / 括号错配 等语法错误
  try {
    new vm.Script(code);
  } catch (e) {
    jsAllOk = false;
    E('JS语法错误(图表白屏)', `第 ${i + 1} 段 <script> 编译失败: ${String(e.message).split('\n')[0]}（该脚本块内图表将全部无法渲染）`);
    return; // 语法都不过，跳过后续变量检查
  }
  // (2) 未定义变量：series/data 引用裸标识符但未在同段脚本声明 → 运行时 ReferenceError
  const declared = new Set();
  let m2;
  const declRe = /\b(?:var|let|const|function)\s+([A-Za-z_$][\w$]*)/g;
  while ((m2 = declRe.exec(code)) !== null) declared.add(m2[1]);
  // 收集函数/箭头函数参数，避免误报
  const argRe = /(?:function\s*[\w$]*\s*|=>\s*)?\(([^()]*)\)\s*(?:=>|\{)/g;
  while ((m2 = argRe.exec(code)) !== null) {
    m2[1].split(',').forEach((p) => { const n = p.trim().split(/[=\s:]/)[0]; if (/^[A-Za-z_$][\w$]*$/.test(n)) declared.add(n); });
  }
  const refRe = /\b(?:series|data)\s*:\s*([A-Za-z_$][\w$]*)\b/g;
  const literals = new Set(['null', 'undefined', 'true', 'false', 'function', 'new', 'this']);
  while ((m2 = refRe.exec(code)) !== null) {
    const id = m2[1];
    if (literals.has(id) || declared.has(id)) continue;
    jsAllOk = false;
    E('图表引用未定义变量(白屏)', `第 ${i + 1} 段 <script> 的 series/data 引用了未声明的 "${id}"（运行时 ReferenceError，图表白屏）`);
  }
});
if (jsAllOk && inlineScripts.length) P(`JS语法/变量校验：${inlineScripts.length} 段内联脚本全部通过`);

// ─── 6. 用列表代图表（WARN） ──────────────────────────────────────────────
if (isStandard) {
const ulBlocks = html.match(/<ul\b[\s\S]*?<\/ul>/gi) || [];
let suspectUl = 0;
for (const ul of ulBlocks) {
  if (/([0-9][\d,\.]*\s*(元|万|亿|%|¥))/.test(ul)) suspectUl++;
}
if (suspectUl) W('疑似用列表代图表', `<ul> 内含金额/百分比 × ${suspectUl}（金额占比类应使用 ECharts 图表）`);

  // ─── 7. 内容数量统计（INFO，具体是否充分由 AI 结合场景判断） ────────────────
const countInsight = (html.match(/class\s*=\s*["'][^"']*\binsight\s+(good|warn|info|risk)\b/gi) || []).length;
const countAction = (html.match(/class\s*=\s*["']action-card["']/gi) || []).length;
const countKpi = (html.match(/class\s*=\s*["']kpi-card["']/gi) || []).length;
const heroBlock = (html.match(/hero-highlight[\s\S]*?<\/div>\s*<\/div>/i) || [''])[0];
const countHero = (heroBlock.match(/h-val/gi) || []).length;

  P(`内容数量统计：KPI 卡片 ${countKpi} 个，核心洞察 ${countInsight} 条，行动建议 ${countAction} 条，hero-highlight 数字 ${countHero} 个（不设固定阈值，由 AI 结合场景判断是否充分）`);
}

// ─── 输出报告 ─────────────────────────────────────────────────────────────
console.log('\n═══════════════════════════════════════════');
console.log(`  HTML 报告质检: ${file}`);
console.log(`  模式: ${isStandard ? 'standard 标准模板·全量检查' : 'custom 自定义·仅技术正确性'} ${modeArg ? '[显式指定]' : `[自动识别·特征命中 ${markerHits}/7]`}`);
console.log('═══════════════════════════════════════════');
if (passes.length) {
  console.log(`\n✅ 通过 (${passes.length}):`);
  passes.forEach((p) => console.log(`   ✓ ${p}`));
}
if (warns.length) {
  console.log(`\n⚠️  警告 (${warns.length}) — 需人工确认:`);
  warns.forEach((w) => console.log(`   ⚠ [${w.item}] ${w.detail}`));
}
if (errors.length) {
  console.log(`\n❌ 错误 (${errors.length}) — 必须修复:`);
  errors.forEach((e) => console.log(`   ✗ [${e.item}] ${e.detail}`));
}
console.log('\n───────────────────────────────────────────');
console.log(`结果: ${errors.length ? '❌ FAIL' : '✅ PASS'}  (错误 ${errors.length} · 警告 ${warns.length})`);
console.log('注: 数值合理性、环比逻辑、洞察数据支撑等业务语义仍需 AI 人工核对');
console.log('───────────────────────────────────────────\n');

process.exit(errors.length ? 1 : 0);
