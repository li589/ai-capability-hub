#!/usr/bin/env node
/**
 * PPT Craft Master v2.0 - 生产级演示文稿生成脚本
 * --------------------------------------------------
 * 落地新版 SKILL.md（ppt-craft-master）的核心规则：
 *  1) 页数档位 → 结构骨架（--pages 数字 或 mini/standard/advanced/deep）
 *  2) 风格选择（--style 18 种预设 → 配色 + 字体）或显式 --palette
 *  3) 28 种版式库，强制「逐页版式分配 + 相邻不重复 + 全局≤2」防雷同
 *  4) 文字安全区与防溢出：safeText 强制 0.5in/0.4in 安全边距 + 按"真实行高"(行距倍数+段后距)
 *     预计算字号兜底 + margin:0 消除默认内缩歧义 + fit:'shrink' 仅作 PowerPoint 双保险
 *     + 字数预算自检（标题≤20字、正文≤260字、单条≤38字、要点≤6）
 *  5) 设计令牌系统（DESIGN_TOKENS）：间距/圆角/阴影/字号梯度/网格统一视觉语法
 *
 * 依赖：pptxgenjs  (npm i pptxgenjs)
 * 用法示例：
 *   node generate.js --title "2026 消费趋势" --style 商务简约 --pages standard
 *   node generate.js --title "AI 简史" --palette emerald --pages 14 --data mydata.json
 *   node generate.js --list-styles        # 列出可选风格
 *   node generate.js --list-palettes      # 列出可选配色
 *   node generate.js --list-tokens        # 列出设计令牌
 */

const PptxGenJS = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// ===================== 画布与安全区常量 =====================
const W = 13.33; // 16:9 宽（英寸）
const H = 7.5;   // 高
const M = { left: 0.5, right: 0.5, top: 0.4, bottom: 0.4 }; // 安全边距（文字/图形距边）

// ===================== 设计令牌系统（与 SKILL.md 一致） =====================
// 统一视觉"语法"：间距走刻度、圆角统一、阴影克制、字号梯度、12 列网格。
const DESIGN_TOKENS = {
  safeMargin: { left: 0.5, right: 0.5, top: 0.4, bottom: 0.4 }, // 安全边距（in）
  space: { xs: 0.15, sm: 0.25, md: 0.5, lg: 1.0 },              // 间距刻度（in）
  radius: { card: 8, block: 18, pill: 999 },                    // 圆角（pt）
  shadow: { blur: 8, transparency: 20 },                        // 轻投影（pt/百分比）
  typeScale: { title: 40, section: 22, cardTitle: 18, body: 15, caption: 11 }, // 字号（pt）
  grid: { columns: 12, baseline: 0.5 }                          // 隐形网格
};

// ===================== 27 套配色（与 SKILL.md 一致） =====================
// mode: light=亮底深字 / dark=暗底浅字
const PALETTES = {
  midnight:       { name: '午夜商务', primary: '1E2761', secondary: 'CADCFC', accent: 'FFFFFF', mode: 'light', text: '1E2761', textLight: '6B7280' },
  techDark:       { name: '科技深空', primary: '0D1117', secondary: '161B22', accent: '58A6FF', mode: 'dark',  text: 'F0F6FC', textLight: '8B949E', bgDark: '0D1117' },
  coral:          { name: '珊瑚活力', primary: 'F96167', secondary: 'F9E795', accent: '2F3C7E', mode: 'light', text: '1F2937', textLight: '6B7280' },
  terracotta:     { name: '暖陶简约', primary: 'B85042', secondary: 'E7E8D1', accent: 'A7BEAE', mode: 'light', text: '3D3D3D', textLight: '6B7280' },
  ocean:          { name: '海洋渐变', primary: '065A82', secondary: '1C7293', accent: '21295C', mode: 'light', text: '065A82', textLight: '6B7280' },
  charcoal:       { name: '炭灰极简', primary: '36454F', secondary: 'F2F2F2', accent: '212121', mode: 'light', text: '36454F', textLight: '8B949E' },
  teal:           { name: '青绿信任', primary: '028090', secondary: '00A896', accent: '02C39A', mode: 'light', text: '065A60', textLight: '374151' },
  berry:          { name: '莓果奶油', primary: '6D2E46', secondary: 'A26769', accent: 'ECE2D0', mode: 'light', text: '3D3D3D', textLight: '6B7280' },
  sage:           { name: '鼠尾草静', primary: '84B59F', secondary: '69A297', accent: '50808E', mode: 'light', text: '3D4F4E', textLight: '6B7280' },
  cherry:         { name: '樱桃大胆', primary: '990011', secondary: 'FCF6F5', accent: '2F3C7E', mode: 'light', text: '1F2937', textLight: '6B7280' },
  blackGold:      { name: '高级黑金', primary: '0D1117', secondary: '1A1A1A', accent: 'C9A24B', mode: 'dark',  text: 'F5F5F0', textLight: 'C9A24B', bgDark: '0D1117' },
  gradientTech:   { name: '渐变科技', primary: '667EEA', secondary: '0F0F23', accent: 'F093FB', mode: 'dark',  text: 'F0F0FF', textLight: 'B7B7E0', bgDark: '0F0F23' },
  mbe:            { name: 'MBE 插画', primary: 'FFD600', secondary: 'FFFFFF', accent: '9C27B0', mode: 'light', text: '222222', textLight: '888888', stroke: '222222' },
  morandiBrown:   { name: '莫兰迪棕', primary: '8B6E4E', secondary: 'F5F0E6', accent: '5D4037', mode: 'light', text: '4A3B2A', textLight: '8A7B66' },
  milkTea:        { name: '奶茶莫兰迪', primary: 'D4C8B8', secondary: 'F8F3E6', accent: '7A6A53', mode: 'light', text: '5A4B38', textLight: '9A8B73' },
  avocado:       { name: '牛油果绿', primary: 'A9B388', secondary: 'F5F5F0', accent: '5C674F', mode: 'light', text: '3E4636', textLight: '7E8A6A' },
  mujiRed:        { name: 'MUJI 酒红', primary: 'A81820', secondary: 'F5F5F0', accent: '000000', mode: 'light', text: 'A81820', textLight: '555555' },
  milkYellow:     { name: '奶黄卡通', primary: 'FFE68A', secondary: 'F8F5E6', accent: '333333', mode: 'light', text: '333333', textLight: '777777', stroke: '333333' },
  peach:          { name: '蜜桃粉',   primary: 'FFB6B9', secondary: 'FFCAD4', accent: '6D2E46', mode: 'light', text: '6D2E46', textLight: 'B07A82' },
  hazeBlue:       { name: '雾霾蓝',   primary: '2E4756', secondary: 'A7C4D9', accent: 'F4A261', mode: 'light', text: '2E4756', textLight: '5E7280' },
  caramel:        { name: '焦糖棕',   primary: 'C08552', secondary: 'E6CCB2', accent: '8B5E34', mode: 'light', text: '5A3E22', textLight: '9A7650' },
  emerald:        { name: '祖母绿',   primary: '0B6E4F', secondary: '3BA776', accent: 'F2C94C', mode: 'light', text: '0B6E4F', textLight: '4E7A66' },
  electricPurple: { name: '电光紫',   primary: '6C2BD9', secondary: 'B388EB', accent: '00E5FF', mode: 'dark',  text: 'F3ECFF', textLight: 'B9A4E8', bgDark: '1A0B33' },
  desertOrange:   { name: '沙漠橙',   primary: 'E07A5F', secondary: 'F2CC8F', accent: '3D405B', mode: 'light', text: '3D405B', textLight: '8A6A55' },
  glacier:        { name: '冰川白',   primary: 'EAF4F4', secondary: 'BFD7D5', accent: '2C5545', mode: 'light', text: '2C5545', textLight: '5E7A72' },
  cherryBlossom:  { name: '樱花粉紫', primary: 'C8A2C8', secondary: 'EAD7E8', accent: '7A4F91', mode: 'light', text: '5B3A5B', textLight: '9A7A9A' },
  mistGrayGreen:  { name: '晨雾灰绿', primary: '9CAF88', secondary: 'DDE5D0', accent: '5B6B4A', mode: 'light', text: '3F4A33', textLight: '6E7A5E' }
};

// ===================== 风格预设（18 种 → 配色 + 字体） =====================
const STYLE_PRESETS = {
  '商务简约': { palette: 'midnight',       font: 'Microsoft YaHei' },
  '科技未来': { palette: 'techDark',       font: 'Microsoft YaHei' },
  '国潮':     { palette: 'cherry',         font: 'Microsoft YaHei' },
  '杂志编辑': { palette: 'charcoal',       font: 'Microsoft YaHei' },
  '孟菲斯':   { palette: 'coral',          font: 'Microsoft YaHei' },
  '莫兰迪':   { palette: 'morandiBrown',   font: 'Microsoft YaHei' },
  '美食生活': { palette: 'caramel',        font: 'Microsoft YaHei' },
  '手绘插画': { palette: 'mbe',            font: 'Microsoft YaHei' },
  '极简北欧': { palette: 'glacier',        font: 'Microsoft YaHei' },
  '教育清新': { palette: 'sage',           font: 'Microsoft YaHei' },
  '医疗健康': { palette: 'ocean',          font: 'Microsoft YaHei' },
  '金融严谨': { palette: 'emerald',        font: 'Microsoft YaHei' },
  '暗黑酷炫': { palette: 'blackGold',      font: 'Microsoft YaHei' },
  '复古':     { palette: 'terracotta',     font: 'Microsoft YaHei' },
  '自然有机': { palette: 'mistGrayGreen',  font: 'Microsoft YaHei' },
  '可爱卡通': { palette: 'milkYellow',     font: 'Microsoft YaHei' },
  '高端奢华': { palette: 'blackGold',      font: 'Microsoft YaHei' },
  '数据报告': { palette: 'hazeBlue',       font: 'Microsoft YaHei' }
};

// ===================== 版式库（28 种，与 SKILL.md 一致） =====================
// 内容页候选池：assignLayouts 从中贪心选「相邻不重复 + 全局≤2」的版式。
const CONTENT_LAYOUTS = [
  'leftTextRightImage', 'iconGrid', 'bigNumber', 'timeline', 'matrix2x2',
  'comparison', 'flow', 'imageTextMix', 'cardGrid', 'centerRadiate',
  'zPattern', 'threeColumn', 'chartBar', 'donut', 'rightTextLeftImage',
  // 新增 7 种（#22–#28）：双栏论点 / 阶梯递进 / 漏斗 / 卡片清单 / 大字标语 / 三段式 / 资源联系
  'doubleColumn', 'stepLadder', 'funnel', 'cardList', 'bigSlogan', 'threeAct', 'contact'
];

// 页数档位 → 目标区间
const TIER_RANGES = {
  mini:     [6, 8],
  standard: [10, 12],
  advanced: [15, 18],
  deep:     [20, 30]
};

// ============================================================
// 工具函数
// ============================================================
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
function stripHash(c) { return (c || '').replace('#', ''); }

// 构建大纲骨架（页数档位 / 精确页数）
function buildOutline(target, topic) {
  let count;
  if (typeof target === 'string' && TIER_RANGES[target]) {
    const [lo, hi] = TIER_RANGES[target];
    count = Math.round((lo + hi) / 2);
  } else {
    count = parseInt(target, 10);
    if (isNaN(count) || count < 6) count = 11;
    if (count > 30) count = 30;
  }
  topic = topic || '演示主题';

  // 重要修复：旧版在 body 中额外插入 section，导致 --pages 12 实际生成 13 页。
  // v2 先计算“总页数预算”，再把章节页作为预算的一部分，因此始终精确等于目标页数。
  const fixed = 4; // cover, toc, summary, end
  const interior = count - fixed;
  let sectionCount = 0;
  if (count >= 10 && count <= 12) sectionCount = 1;
  else if (count >= 13 && count <= 18) sectionCount = 2;
  else if (count >= 19) sectionCount = 3;
  sectionCount = Math.min(sectionCount, Math.max(0, interior - 2));
  const contentCount = Math.max(2, interior - sectionCount);

  const pages = [
    { type: 'cover', title: topic, subtitle: 'AI 智能生成 · PPT Craft Master v2' },
    { type: 'toc', title: '目录' }
  ];

  // 均匀插入章节页，避免固定“每 4 页”造成不可控页数膨胀。
  const sectionAfter = [];
  if (sectionCount > 0) {
    for (let s = 1; s <= sectionCount; s++) {
      sectionAfter.push(Math.max(1, Math.round((s * contentCount) / (sectionCount + 1))));
    }
  }

  let contentIndex = 0;
  for (let i = 0; i < contentCount; i++) {
    contentIndex++;
    pages.push({ type: 'content', title: `核心观点 ${contentIndex}` });
    if (sectionAfter.includes(contentIndex) && pages.length < count - 2) {
      const secNo = sectionAfter.indexOf(contentIndex) + 1;
      pages.push({ type: 'section', title: `模块 ${secNo} · 深入展开`, section: `MODULE ${String(secNo).padStart(2,'0')}` });
    }
  }

  pages.push({ type: 'summary', title: '总结与展望' });
  pages.push({ type: 'end', title: '谢谢观看' });

  // 最后一道断言：无论未来怎么改算法，页数都必须精确。
  if (pages.length !== count) {
    throw new Error(`buildOutline page-count invariant failed: expected ${count}, got ${pages.length}`);
  }
  return pages;
}

// 强制「相邻不重复 + 全局≤2」的版式分配
function assignLayouts(pages, provided) {
  const used = {};
  let prev = null;
  let pi = 0;
  return pages.map((p) => {
    if (p.type === 'cover')   { return { ...p, layout: 'cover' }; }
    if (p.type === 'toc')     { return { ...p, layout: 'toc' }; }
    if (p.type === 'section') { return { ...p, layout: 'section' }; }
    if (p.type === 'summary') { return { ...p, layout: 'summary' }; }
    if (p.type === 'end')     { return { ...p, layout: 'end' }; }

    let pick = provided && provided[pi] && provided[pi] !== 'auto'
      ? provided[pi]
      : null;

    // v2：内容适配优先。默认避免相邻重复；重复次数仅作为软约束。
    if (!pick || !CONTENT_LAYOUTS.includes(pick) || pick === prev) {
      const maxPreferred = 2;
      const candidates = CONTENT_LAYOUTS.filter(L => L !== prev && (used[L] || 0) < maxPreferred);
      const pool = candidates.length ? candidates : CONTENT_LAYOUTS.filter(L => L !== prev);
      pick = (pool.length ? pool : CONTENT_LAYOUTS).slice()
        .sort((a, b) => (used[a] || 0) - (used[b] || 0))[0];
    }

    used[pick] = (used[pick] || 0) + 1;
    prev = pick;
    pi++;
    return { ...p, layout: pick };
  });
}

// ============================================================
// 生成器
// ============================================================
class PPTGenerator {
  constructor(options = {}) {
    this.pptx = new PptxGenJS();
    this.fontFace = options.font || 'Microsoft YaHei';
    this.options = {
      title: options.title || '演示文稿',
      author: options.author || 'PPT Generator Pro',
      palette: options.palette || 'midnight'
    };
    this.colors = PALETTES[this.options.palette] || PALETTES.midnight;
    this.pptx.layout = 'LAYOUT_16x9';
    this.warnings = [];
    this.pageCount = 0;
  }

  // ---- 色彩辅助 ----
  pageBg() {
    if (this.colors.mode === 'dark') return this.colors.bgDark || this.colors.primary;
    return this.colors.bgLight || 'FFFFFF';
  }
  pageText() {
    return this.colors.mode === 'dark' ? 'FFFFFF' : (this.colors.text || '1F2937');
  }
  pageTextLight() {
    return this.colors.mode === 'dark' ? (this.colors.textLight || 'AAB2C0') : (this.colors.textLight || '6B7280');
  }

  // ---- 安全区文本框（防溢出核心，根治"文字大于背景"） ----
  // 机制（关键修正）：
  //  ① 强制安全边距（所有文字不越画布）
  //  ② margin:0 显式去掉 pptxgenjs 默认 0.1in 内缩的不确定性 → 盒内可写区 = 盒子尺寸 - 预留 padding
  //  ③ 按"真实行高"预计算字号（控量为先，绝不靠 fit:'shrink' 碰运气）：
  //     真实行高 = 字号 × 行距倍数（+ 段后距），行距/段后距取自调用方传入值，
  //     彻底修正旧版固定 1.25 倍导致"开了 lineSpacingMultiple:1.4 / paraSpaceAfter 却不缩字"的漏算
  //  ④ 缩到下限(8pt)仍放不下 → 按"真实行高"截断加省略号
  //  ⑤ fit:'shrink'（normAutofit）仅作对 PowerPoint 生效的双保险；
  //     LibreOffice / 多数预览与 PDF 导出【不认】normAutofit，故 ③④ 才是真正保证
  safeText(slide, text, o = {}) {
    const defW = W - M.left - M.right;
    const defH = H - M.top - M.bottom;
    let { x = M.left, y = M.top, w = defW, h = defH, budget, fontSize = 16, ...rest } = o;
    x = Math.max(M.left, x);
    y = Math.max(M.top, y);
    w = Math.min(w, W - M.right - x);
    h = Math.min(h, H - M.bottom - y);

    // 真实行高参数（来自调用方，未传则用保守默认）
    const lineMultiple = (typeof rest.lineSpacingMultiple === 'number' && rest.lineSpacingMultiple > 0) ? rest.lineSpacingMultiple : 1.2;
    const paraSpaceAfterPt = (typeof rest.paraSpaceAfterPt === 'number' && rest.paraSpaceAfterPt > 0)
      ? rest.paraSpaceAfterPt
      : ((typeof rest.paraSpaceAfter === 'number' && rest.paraSpaceAfter > 0) ? rest.paraSpaceAfter : 0);
    const isArray = Array.isArray(text);
    // 段数：pptxgenjs 会把字符串里的 \n 拆成多个真实 <a:p> 段落，每个段落都带 lnSpc/spcAft，
    // 故段数 = 换行段数（而非 1），否则会漏掉段后距 → 高估容量 → 溢出
    const nParas = Math.max(1, this._segments(text).length);
    // 项目符号：bullet 会额外吃掉约 0.28in（缩进 + 符号），需从可写宽度中扣除
    const bulletPad = rest.bullet ? 0.28 : 0;

    const baseFont = fontSize;
    // 盒内可写区：去掉统一预留 padding + 项目符号占位（margin 已置 0，故真实可写区 = 盒子尺寸 - padding）
    const padX = 0.14, padY = 0.14;
    const we = Math.max(0.4, w - padX - bulletPad), he = Math.max(0.3, h - padY);
    const f = this.autoFitFontSize(text, we, he, baseFont, lineMultiple, paraSpaceAfterPt, isArray);
    const stillOver = this._totalLines(text, this._cpl(we, f)) > this._linesAvail(he, f, lineMultiple, paraSpaceAfterPt, nParas);
    if (stillOver) {
      const policy = rest.overflowPolicy || 'error';
      const preview = String(text).replace(/\s+/g, ' ').slice(0, 80);
      if (policy === 'clip') {
        text = this.clipToFit(text, we, he, f, lineMultiple, paraSpaceAfterPt, isArray);
        this.warnings.push(`CLIPPED TEXT: ${preview}`);
      } else {
        throw new Error(`Text overflow cannot be safely resolved (preview: ${preview}). Reduce copy, enlarge the box, or split the slide.`);
      }
    }
    if (f < baseFont) this.warnings.push(`TEXT SHRUNK: ${baseFont}pt → ${f}pt`);
    if (budget && typeof text === 'string') this.budgetWarn('文字', text, budget);

    slide.addText(text, {
      x, y, w, h,
      fontFace: this.fontFace,
      fontSize: f,
      fit: 'shrink',
      margin: 0,
      valign: rest.valign || 'top',
      ...rest
    });
  }

  // 把传入文本拆成"段落"（数组每项=一段；字符串按 \n 软换行，仍属同一段落）
  _segments(text) {
    if (Array.isArray(text)) return text.map((it) => (it && it.text != null) ? String(it.text) : String(it));
    return String(text).split('\n');
  }
  // 每行可容纳字数（CJK 取方形，偏保守 → 不会算多导致溢出）
  _cpl(wIn, fontPt) { return Math.max(1, Math.floor((wIn * 72) / fontPt)); }
  // 估算文字需要的总"行数"（按盒子可用宽度换行）
  _totalLines(text, cpl) {
    return this._segments(text).reduce((n, s) => n + Math.max(1, Math.ceil(s.length / cpl)), 0);
  }
  // 反推盒子在"真实行高"下能容纳的行数（段后距折算掉等效行高）
  _linesAvail(boxHIn, fontPt, lineMultiple, paraSpaceAfterPt, nParas) {
    const lineH = fontPt * lineMultiple;
    const spcH = Math.max(0, (nParas - 1) * paraSpaceAfterPt); // 段后距总额（pt）
    const usable = Math.max(0, boxHIn * 72 - spcH);
    return Math.max(1, Math.floor(usable / lineH));
  }
  // 自动算字号：从基准字号往下减，直到文字按"真实行高"能在盒子内放下（下限 8pt）
  autoFitFontSize(text, wIn, hIn, baseFont, lineMultiple, paraSpaceAfterPt, isArray) {
    const minF = 10;
    const nParas = isArray ? Math.max(1, text.length) : 1;
    let f = baseFont;
    while (f > minF) {
      const cpl = this._cpl(wIn, f);
      if (this._totalLines(text, cpl) <= this._linesAvail(hIn, f, lineMultiple, paraSpaceAfterPt, nParas)) break;
      f -= 1;
    }
    return f;
  }
  // 截断到盒子容量（仅当缩到下限仍放不下时），按"真实行高"估算容量
  clipToFit(text, wIn, hIn, fontPt, lineMultiple, paraSpaceAfterPt, isArray) {
    const nParas = isArray ? Math.max(1, text.length) : 1;
    const cpl = this._cpl(wIn, fontPt);
    const cap = cpl * this._linesAvail(hIn, fontPt, lineMultiple, paraSpaceAfterPt, nParas);
    if (typeof text === 'string') {
      const s = text.replace(/\n/g, '');
      return s.length > cap ? s.slice(0, Math.max(0, cap - 1)) + '…' : text;
    }
    if (Array.isArray(text)) {
      const out = []; let used = 0;
      for (const it of text) {
        const t = (it && it.text != null) ? String(it.text) : String(it);
        const rem = cap - used;
        if (rem <= 0) break;
        const cut = t.length > rem ? t.slice(0, Math.max(0, rem - 1)) + '…' : t;
        used += cut.length;
        out.push(it && it.text != null ? { ...it, text: cut } : cut);
      }
      return out;
    }
    return text;
  }

  // 安全区图形（防图形越界）
  shape(slide, type, o = {}) {
    let { x = 0, y = 0, w = 1, h = 1, ...rest } = o;
    x = Math.max(0, x); y = Math.max(0, y);
    w = Math.min(w, W - x); h = Math.min(h, H - y);
    slide.addShape(type, { x, y, w, h, ...rest });
  }

  // 字数预算自检
  budgetWarn(label, text, max) {
    const len = (text || '').replace(/\s/g, '').length;
    if (len > max) this.warnings.push(`⚠️ ${label}超预算：实测 ${len} 字 > 上限 ${max} 字，建议删减（收缩仅兜底）`);
  }

  // 插图占位面板（无图片时绘制几何插画面板，避免纯文字页）
  imagePanel(slide, x, y, w, h) {
    x = Math.max(M.left, x); y = Math.max(M.top, y);
    w = Math.min(w, W - M.right - x); h = Math.min(h, H - M.bottom - y);
    this.shape(slide, 'roundRect', { x, y, w, h, rectRadius: 0.08,
      fill: { color: this.colors.secondary }, line: { color: this.colors.primary, width: 1 } });
    this.shape(slide, 'ellipse', { x: x + w / 2 - 0.55, y: y + h / 2 - 0.55, w: 1.1, h: 1.1,
      fill: { color: this.colors.accent } });
    this.shape(slide, 'triangle', { x: x + w / 2 - 0.4, y: y + h / 2 - 0.2, w: 0.8, h: 0.6,
      fill: { color: this.colors.primary } });
  }

  newSlide(bg) {
    const s = this.pptx.addSlide();
    s.background = { color: bg || this.pageBg() };
    this.pageCount++;
    return s;
  }

  // ---- 通用装饰 ----
  topBand(slide, color) {
    this.shape(slide, 'rectangle', { x: 0, y: 0, w: W, h: 0.12, fill: { color: color || this.colors.primary } });
  }
  decorCircle(slide, x, y, d, color, transparency = 88) {
    this.shape(slide, 'ellipse', { x, y, w: d, h: d, fill: { color, transparency } });
  }

  // ============================================================
  // 21 种版式渲染
  // ============================================================
  render(page, data) {
    let name = 'render_' + page.layout;
    if (page.layout === 'summary') name = 'render_cardGrid'; // 总结页复用卡片网格
    if (page.layout === 'quote') name = 'render_quote';       // 金句页（可通过 --data 指定）
    const fn = this[name] || this.render_leftTextRightImage;
    fn.call(this, page, data);
  }

  render_cover(p) {
    const s = this.newSlide(this.colors.primary);
    this.decorCircle(s, 9, -1.5, 5, this.colors.accent, 90);
    this.decorCircle(s, -1, 5, 4, this.colors.accent, 90);
    this.safeText(s, p.title, {
      x: 0.8, y: 2.4, w: 11.5, h: 1.6, fontSize: 46, bold: true, color: 'FFFFFF', align: 'center', budget: 20
    });
    if (p.subtitle) this.safeText(s, p.subtitle, {
      x: 0.8, y: 4.2, w: 11.5, h: 0.8, fontSize: 20, color: this.colors.secondary, align: 'center'
    });
    this.shape(s, 'rectangle', { x: 5.5, y: 5.4, w: 2.5, h: 0.05, fill: { color: this.colors.accent } });
  }

  render_toc(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.safeText(s, p.title || '目录', { x: 0.8, y: 0.5, w: 11.5, h: 0.8, fontSize: 34, bold: true, color: this.colors.primary });
    this.shape(s, 'rectangle', { x: 0.8, y: 1.5, w: 0.1, h: 5.4, fill: { color: this.colors.primary } });
    const items = (data && data.toc) || [];
    const startY = 1.8, itemH = Math.min(0.95, 5.4 / Math.max(items.length, 1));
    items.forEach((it, i) => {
      this.safeText(s, String(i + 1).padStart(2, '0'), { x: 1.2, y: startY + i * itemH, w: 0.7, h: 0.6, fontSize: 22, bold: true, color: this.colors.primary });
      this.safeText(s, it.title || it, { x: 2.1, y: startY + i * itemH, w: 9, h: 0.6, fontSize: 17, color: this.pageText() });
      if (i < items.length - 1) this.shape(s, 'rectangle', { x: 2.1, y: startY + i * itemH + 0.72, w: 9, h: 0.01, fill: { color: 'E5E5E5' } });
    });
  }

  render_section(p) {
    const s = this.newSlide(this.colors.primary);
    this.decorCircle(s, 9.5, 1, 4, this.colors.accent, 85);
    this.safeText(s, p.section || 'CHAPTER', { x: 0.9, y: 2.4, w: 6, h: 0.6, fontSize: 18, bold: true, color: this.colors.accent });
    this.safeText(s, p.title, { x: 0.9, y: 3.0, w: 7.5, h: 1.6, fontSize: 40, bold: true, color: 'FFFFFF', budget: 24 });
  }

  render_leftTextRightImage(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    this.safeText(s, (data.bullets || []).join('\n'), {
      x: 0.8, y: 1.7, w: 5.6, h: 5, fontSize: 16, color: this.pageText(), lineSpacingMultiple: 1.4,
      bullet: { code: '2022' }, paraSpaceAfterPt: 10, budget: 260
    });
    if (data.image) s.addImage({ path: data.image, x: 6.8, y: 1.7, w: 5.8, h: 5, rounding: true });
    else this.imagePanel(s, 6.8, 1.7, 5.8, 5);
    this.quoteHint(s, data.hint);
  }

  render_rightTextLeftImage(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    if (data.image) s.addImage({ path: data.image, x: 0.8, y: 1.7, w: 5.8, h: 5, rounding: true });
    else this.imagePanel(s, 0.8, 1.7, 5.8, 5);
    this.safeText(s, (data.bullets || []).join('\n'), {
      x: 6.8, y: 1.7, w: 5.8, h: 5, fontSize: 16, color: this.pageText(), lineSpacingMultiple: 1.4,
      bullet: { code: '2022' }, paraSpaceAfterPt: 10, budget: 260
    });
    this.quoteHint(s, data.hint);
  }

  render_iconGrid(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const cards = data.cards || defaultCards(4);
    const cols = cards.length <= 4 ? cards.length : 3;
    const rows = Math.ceil(cards.length / cols);
    const gx = 0.8, gy = 1.8, gw = (W - 1.6 - (cols - 1) * 0.4) / cols, gh = (H - gy - 0.4 - (rows - 1) * 0.4) / rows;
    cards.forEach((c, i) => {
      const cx = gx + (i % cols) * (gw + 0.4);
      const cy = gy + Math.floor(i / cols) * (gh + 0.4);
      this.shape(s, 'roundRect', { x: cx, y: cy, w: gw, h: gh, rectRadius: 0.08, fill: { color: this.colors.secondary } });
      this.shape(s, 'ellipse', { x: cx + 0.3, y: cy + 0.3, w: 0.6, h: 0.6, fill: { color: this.colors.primary } });
      this.safeText(s, c.title || '', { x: cx + 0.3, y: cy + 1.0, w: gw - 0.6, h: 0.5, fontSize: 16, bold: true, color: this.colors.primary, budget: 14 });
      this.safeText(s, c.desc || '', { x: cx + 0.3, y: cy + 1.5, w: gw - 0.6, h: gh - 1.7, fontSize: 13, color: this.pageTextLight(), budget: 60 });
    });
  }

  render_bigNumber(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const nums = data.numbers || defaultNumbers(4);
    const n = nums.length, gap = 0.5, cw = (W - 1.6 - (n - 1) * gap) / n, ch = 3, cy = 2.2;
    nums.forEach((it, i) => {
      const cx = 0.8 + i * (cw + gap);
      this.shape(s, 'roundRect', { x: cx, y: cy, w: cw, h: ch, rectRadius: 0.1, fill: { color: this.colors.primary } });
      this.safeText(s, it.value || '', { x: cx, y: cy + 0.4, w: cw, h: 1.4, fontSize: 46, bold: true, color: 'FFFFFF', align: 'center', budget: 8 });
      this.safeText(s, it.label || '', { x: cx, y: cy + 1.9, w: cw, h: 0.8, fontSize: 14, color: this.colors.secondary, align: 'center', budget: 18 });
    });
  }

  render_timeline(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const nodes = data.timeline || defaultTimeline(4);
    const n = nodes.length, y = 3.6, x0 = 1.0, x1 = W - 1.0;
    this.shape(s, 'rectangle', { x: x0, y: y, w: x1 - x0, h: 0.04, fill: { color: this.colors.primary } });
    nodes.forEach((nd, i) => {
      const cx = x0 + (x1 - x0) * (i / (n - 1));
      this.shape(s, 'ellipse', { x: cx - 0.18, y: y - 0.14, w: 0.36, h: 0.36, fill: { color: this.colors.accent }, line: { color: this.colors.primary, width: 2 } });
      this.safeText(s, nd.t || '', { x: cx - 1, y: y - 1.1, w: 2, h: 0.5, fontSize: 14, bold: true, color: this.colors.primary, align: 'center', budget: 12 });
      this.safeText(s, nd.e || '', { x: cx - 1, y: y + 0.35, w: 2, h: 1.0, fontSize: 13, color: this.pageText(), align: 'center', budget: 36 });
    });
  }

  render_matrix2x2(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const quad = data.quad || ['优势', '劣势', '机会', '威胁'];
    const gx = 1.0, gy = 1.7, gw = (W - 2 - 0.4) / 2, gh = (H - gy - 0.4 - 0.4) / 2;
    const colors = [this.colors.primary, this.colors.accent, this.colors.secondary, this.colors.textLight || 'CCCCCC'];
    quad.forEach((q, i) => {
      const cx = gx + (i % 2) * (gw + 0.4);
      const cy = gy + Math.floor(i / 2) * (gh + 0.4);
      this.shape(s, 'roundRect', { x: cx, y: cy, w: gw, h: gh, rectRadius: 0.06, fill: { color: colors[i] } });
      this.safeText(s, q, { x: cx + 0.3, y: cy + 0.25, w: gw - 0.6, h: gh - 0.5, fontSize: 16, bold: true, color: (colors[i] === this.colors.secondary) ? this.colors.primary : 'FFFFFF', budget: 80 });
    });
  }

  render_comparison(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const cols = data.cols || [{ title: '方案 A', points: ['要点一', '要点二', '要点三'] }, { title: '方案 B', points: ['要点一', '要点二', '要点三'] }];
    const gx = 0.8, gy = 1.9, gw = (W - 1.6 - 0.6) / 2, gh = 4.6;
    cols.forEach((c, i) => {
      const cx = gx + i * (gw + 0.6);
      this.shape(s, 'roundRect', { x: cx, y: gy, w: gw, h: 0.8, rectRadius: 0.06, fill: { color: this.colors.primary } });
      this.safeText(s, c.title || '', { x: cx, y: gy, w: gw, h: 0.8, fontSize: 18, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', budget: 14 });
      this.safeText(s, (c.points || []).join('\n'), { x: cx + 0.3, y: gy + 1.0, w: gw - 0.6, h: gh - 1.2, fontSize: 14, color: this.pageText(), bullet: { code: '2022' }, paraSpaceAfter: 8, budget: 120 });
    });
    this.shape(s, 'rectangle', { x: W / 2 - 0.03, y: gy, w: 0.06, h: gh, fill: { color: this.colors.accent } });
  }

  render_flow(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const steps = data.steps || ['步骤一', '步骤二', '步骤三', '步骤四'];
    const n = steps.length, gap = 0.6, bw = (W - 1.6 - (n - 1) * gap) / n, bh = 2.2, by = 2.6;
    steps.forEach((st, i) => {
      const bx = 0.8 + i * (bw + gap);
      this.shape(s, 'roundRect', { x: bx, y: by, w: bw, h: bh, rectRadius: 0.1, fill: { color: this.colors.primary } });
      this.safeText(s, String(i + 1), { x: bx, y: by + 0.2, w: bw, h: 0.6, fontSize: 20, bold: true, color: this.colors.accent, align: 'center' });
      this.safeText(s, st, { x: bx + 0.15, y: by + 0.9, w: bw - 0.3, h: bh - 1.1, fontSize: 14, color: 'FFFFFF', align: 'center', budget: 40 });
      if (i < n - 1) this.shape(s, 'rightTriangle', { x: bx + bw + 0.05, y: by + bh / 2 - 0.2, w: 0.4, h: 0.4, fill: { color: this.colors.accent } });
    });
  }

  render_imageTextMix(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    if (data.image) s.addImage({ path: data.image, x: 0.8, y: 1.7, w: 4.8, h: 5, rounding: true });
    else this.imagePanel(s, 0.8, 1.7, 4.8, 5);
    this.safeText(s, (data.bullets || []).join('\n'), { x: 6.0, y: 1.7, w: 6.6, h: 5, fontSize: 15, color: this.pageText(), bullet: { code: '2022' }, paraSpaceAfter: 9, budget: 240 });
  }

  render_cardGrid(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const cards = data.cards || defaultCards(6);
    const cols = 3, rows = Math.ceil(cards.length / cols);
    const gx = 0.8, gy = 1.8, gw = (W - 1.6 - (cols - 1) * 0.4) / cols, gh = (H - gy - 0.4 - (rows - 1) * 0.4) / rows;
    cards.forEach((c, i) => {
      const cx = gx + (i % cols) * (gw + 0.4);
      const cy = gy + Math.floor(i / cols) * (gh + 0.4);
      this.shape(s, 'roundRect', { x: cx, y: cy, w: gw, h: gh, rectRadius: 0.08, fill: { color: this.colors.bgLight || 'FFFFFF' }, line: { color: this.colors.secondary, width: 1 } });
      this.safeText(s, c.title || '', { x: cx + 0.25, y: cy + 0.25, w: gw - 0.5, h: 0.5, fontSize: 15, bold: true, color: this.colors.primary, budget: 16 });
      this.safeText(s, c.desc || '', { x: cx + 0.25, y: cy + 0.85, w: gw - 0.5, h: gh - 1.1, fontSize: 12, color: this.pageTextLight(), budget: 90 });
    });
  }

  render_centerRadiate(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const cx = W / 2, cy = 4.2;
    this.shape(s, 'ellipse', { x: cx - 0.9, y: cy - 0.9, w: 1.8, h: 1.8, fill: { color: this.colors.primary } });
    this.safeText(s, data.center || p.title, { x: cx - 0.9, y: cy - 0.9, w: 1.8, h: 1.8, fontSize: 14, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', budget: 16 });
    const spokes = data.spokes || defaultCards(5);
    const n = spokes.length, R = 2.6;
    spokes.forEach((sp, i) => {
      const a = (-90 + i * (360 / n)) * Math.PI / 180;
      const px = cx + R * Math.cos(a), py = cy + R * Math.sin(a);
      this.shape(s, 'line', { x: cx, y: cy, w: px - cx, h: py - cy, line: { color: this.colors.accent, width: 2 } });
      this.shape(s, 'roundRect', { x: px - 1.2, y: py - 0.5, w: 2.4, h: 1.0, rectRadius: 0.08, fill: { color: this.colors.secondary } });
      this.safeText(s, sp.title || '', { x: px - 1.1, y: py - 0.4, w: 2.2, h: 0.8, fontSize: 12, bold: true, color: this.colors.primary, align: 'center', valign: 'middle', budget: 22 });
    });
  }

  render_zPattern(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const items = data.items || defaultCards(4);
    const pos = [[0.8, 1.8], [7.4, 1.8], [0.8, 4.4], [7.4, 4.4]];
    items.slice(0, 4).forEach((it, i) => {
      const [x, y] = pos[i];
      this.shape(s, 'roundRect', { x, y, w: 5.1, h: 2.2, rectRadius: 0.08, fill: { color: i % 2 ? this.colors.secondary : this.colors.primary } });
      this.safeText(s, it.title || '', { x: x + 0.3, y: y + 0.25, w: 4.5, h: 0.5, fontSize: 16, bold: true, color: i % 2 ? this.colors.primary : 'FFFFFF', budget: 18 });
      this.safeText(s, it.desc || '', { x: x + 0.3, y: y + 0.85, w: 4.5, h: 1.1, fontSize: 13, color: i % 2 ? this.pageText() : 'FFFFFF', budget: 70 });
    });
  }

  render_threeColumn(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const cols = data.cols || defaultCards(3);
    const n = cols.length, gap = 0.4, cw = (W - 1.6 - (n - 1) * gap) / n, cy = 1.9, ch = 4.6;
    cols.forEach((c, i) => {
      const cx = 0.8 + i * (cw + gap);
      this.shape(s, 'roundRect', { x: cx, y: cy, w: cw, h: 0.7, rectRadius: 0.06, fill: { color: this.colors.primary } });
      this.safeText(s, c.title || '', { x: cx, y: cy, w: cw, h: 0.7, fontSize: 16, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', budget: 14 });
      this.shape(s, 'roundRect', { x: cx, y: cy + 0.9, w: cw, h: ch - 0.9, rectRadius: 0.06, fill: { color: this.colors.secondary } });
      this.safeText(s, c.desc || '', { x: cx + 0.25, y: cy + 1.1, w: cw - 0.5, h: ch - 1.3, fontSize: 13, color: this.pageText(), budget: 100 });
    });
  }

  render_chartBar(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const ch = data.chart || { name: '指标', labels: ['Q1', 'Q2', 'Q3', 'Q4'], values: [20, 35, 28, 42] };
    s.addChart(this.pptx.ChartType.bar, [{ name: ch.name, labels: ch.labels, values: ch.values }], {
      x: 0.8, y: 1.8, w: 11.7, h: 5, barDir: 'col', chartColors: [this.colors.primary],
      showValue: true, dataLabelColor: this.pageText(), catAxisLabelColor: this.pageText(), valAxisLabelColor: this.pageTextLight()
    });
  }

  render_donut(p, data) {
    const s = this.newSlide(this.pageBg());
    this.topBand(s);
    this.titleBar(s, p.title);
    const d = data.donut || { labels: ['A', 'B', 'C', 'D'], values: [30, 25, 25, 20] };
    s.addChart(this.pptx.ChartType.doughnut, [{ name: '占比', labels: d.labels, values: d.values }], {
      x: 0.8, y: 1.8, w: 7, h: 5, chartColors: [this.colors.primary, this.colors.accent, this.colors.secondary, this.colors.textLight || 'AAAAAA'], showLegend: true, legendPos: 'r'
    });
    this.safeText(s, data.note || '', { x: 8.2, y: 2.5, w: 4.3, h: 3, fontSize: 14, color: this.pageText(), budget: 120 });
  }

  render_cardGrid_summary(p, data) { this.render_cardGrid(p, data); } // 别名

  render_quote(p, data) {
    const s = this.newSlide(this.colors.primary);
    this.decorCircle(s, 1, 1, 3.5, this.colors.accent, 90);
    const q = (data && data.quote) || '好的洞察，往往藏在被忽略的附近。';
    this.safeText(s, '“', { x: 0.8, y: 1.2, w: 2, h: 1.5, fontSize: 90, bold: true, color: this.colors.accent });
    this.safeText(s, q, { x: 1.2, y: 2.6, w: 10.5, h: 2.2, fontSize: 34, bold: true, color: 'FFFFFF', budget: 60 });
    if (data && data.source) this.safeText(s, '— ' + data.source, { x: 9.0, y: 5.2, w: 3.3, h: 0.6, fontSize: 16, color: this.colors.secondary, align: 'right', budget: 20 });
  }

  render_end(p) {
    const s = this.newSlide(this.colors.primary);
    this.decorCircle(s, 4, 1.5, 5, this.colors.accent, 92);
    this.safeText(s, p.title || '谢谢观看', { x: 0, y: 3, w: W, h: 1.5, fontSize: 46, bold: true, color: 'FFFFFF', align: 'center' });
  }

  // ---- 新增 7 种版式（#22–#28） ----
  render_doubleColumn(p, data) { // #22 双栏论点（正反）
    const s = this.newSlide(this.pageBg());
    this.topBand(s); this.titleBar(s, p.title);
    const cols = data.cols || [{ title: '守成派', points: ['依赖存量渠道', '决策链冗长', '风险偏好低'] }, { title: '进取派', points: ['押注新场景', '小步快跑', '敢用新流量'] }];
    const gx = 0.8, gy = 1.9, gw = (W - 1.6 - 0.6) / 2, gh = 4.4;
    cols.forEach((c, i) => {
      const cx = gx + i * (gw + 0.6);
      this.shape(s, 'roundRect', { x: cx, y: gy, w: gw, h: 0.8, rectRadius: 0.06, fill: { color: i ? this.colors.accent : this.colors.primary } });
      this.safeText(s, c.title || '', { x: cx, y: gy, w: gw, h: 0.8, fontSize: 18, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', budget: 14 });
      this.safeText(s, (c.points || []).join('\n'), { x: cx + 0.3, y: gy + 1.0, w: gw - 0.6, h: gh - 1.2, fontSize: 14, color: this.pageText(), bullet: { code: '2022' }, paraSpaceAfter: 8, budget: 120 });
    });
    this.safeText(s, data.conclusion || '结论：增量属于敢用新流量的一方。', { x: 0.8, y: gy + gh + 0.2, w: W - 1.6, h: 0.5, fontSize: 15, bold: true, color: this.colors.primary, align: 'center', budget: 30 });
  }

  render_stepLadder(p, data) { // #23 阶梯递进
    const s = this.newSlide(this.pageBg());
    this.topBand(s); this.titleBar(s, p.title);
    const steps = data.steps || ['洞察需求', '小样验证', '快速复制', '规模放量'];
    const n = steps.length, x0 = 1.0, baseY = 5.8, stepH = (baseY - 1.9) / n, bw = 9.5;
    steps.forEach((st, i) => {
      const y = baseY - (i + 1) * stepH;
      const x = x0 + i * 0.6;
      this.shape(s, 'roundRect', { x, y, w: bw - i * 0.6, h: stepH - 0.2, rectRadius: 0.06, fill: { color: this.colors.primary } });
      this.safeText(s, `${i + 1}. ${st}`, { x: x + 0.3, y, w: bw - i * 0.6 - 0.6, h: stepH - 0.2, fontSize: 15, bold: true, color: 'FFFFFF', valign: 'middle', budget: 20 });
    });
  }

  render_funnel(p, data) { // #24 漏斗模型
    const s = this.newSlide(this.pageBg());
    this.topBand(s); this.titleBar(s, p.title);
    const layers = data.funnel || [{ t: '曝光', v: '100%' }, { t: '兴趣', v: '62%' }, { t: '意向', v: '38%' }, { t: '转化', v: '21%' }];
    const n = layers.length, topW = 10, cx = W / 2, y0 = 1.9, lh = (6.0 - y0) / n;
    layers.forEach((ly, i) => {
      const wTop = topW * (1 - i / (n + 1)), wBot = topW * (1 - (i + 1) / (n + 1));
      const yTop = y0 + i * lh;
      this.shape(s, 'trapezoid', { x: cx - wTop / 2, y: yTop, w: wTop, h: lh - 0.15, fill: { color: this.colors.primary, transparency: i * 12 }, line: { color: this.colors.accent, width: 1 } });
      this.safeText(s, `${ly.t}  ${ly.v || ''}`, { x: cx - wTop / 2, y: yTop, w: wTop, h: lh - 0.15, fontSize: 14, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', budget: 14 });
    });
  }

  render_cardList(p, data) { // #25 卡片清单
    const s = this.newSlide(this.pageBg());
    this.topBand(s); this.titleBar(s, p.title);
    const cards = (data.cards || defaultCards(5)).slice(0, 5);
    const gy = 1.8, ch = (6.0 - gy - (cards.length - 1) * 0.25) / cards.length;
    cards.forEach((c, i) => {
      const cy = gy + i * (ch + 0.25);
      this.shape(s, 'roundRect', { x: 0.8, y: cy, w: W - 1.6, h: ch, rectRadius: 0.06, fill: { color: i % 2 ? this.colors.secondary : 'FFFFFF' }, line: { color: this.colors.secondary, width: 1 } });
      this.shape(s, 'ellipse', { x: 1.0, y: cy + ch / 2 - 0.22, w: 0.44, h: 0.44, fill: { color: this.colors.primary } });
      this.safeText(s, String(i + 1), { x: 1.0, y: cy + ch / 2 - 0.22, w: 0.44, h: 0.44, fontSize: 14, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle' });
      this.safeText(s, c.title || '', { x: 1.7, y: cy + 0.1, w: 3.2, h: ch - 0.2, fontSize: 16, bold: true, color: this.colors.primary, valign: 'middle', budget: 16 });
      this.safeText(s, c.desc || '', { x: 5.0, y: cy + 0.1, w: W - 1.6 - 4.4, h: ch - 0.2, fontSize: 13, color: this.pageTextLight(), valign: 'middle', budget: 60 });
    });
  }

  render_bigSlogan(p, data) { // #26 大字标语
    const s = this.newSlide(this.colors.primary);
    this.decorCircle(s, 9.5, 1, 4, this.colors.accent, 88);
    const slogan = (data && data.slogan) || p.title || '离用户越近，市场越大。';
    this.safeText(s, slogan, { x: 1.0, y: 2.6, w: 11.3, h: 1.8, fontSize: 40, bold: true, color: 'FFFFFF', align: 'center', budget: 32 });
    if (data && data.note) this.safeText(s, data.note, { x: 1.5, y: 4.6, w: 10.3, h: 0.8, fontSize: 16, color: this.colors.secondary, align: 'center', budget: 40 });
  }

  render_threeAct(p, data) { // #27 三段式故事（起因/经过/结果）
    const s = this.newSlide(this.pageBg());
    this.topBand(s); this.titleBar(s, p.title);
    const acts = data.acts || [{ t: '起因', d: '用户需求被长期误读。' }, { t: '经过', d: '用数据重新认识用户。' }, { t: '结果', d: '找到真正的增量。' }];
    const n = acts.length, gap = 0.5, cw = (W - 1.6 - (n - 1) * gap) / n, cy = 2.2, ch = 3.8;
    acts.forEach((a, i) => {
      const cx = 0.8 + i * (cw + gap);
      this.shape(s, 'roundRect', { x: cx, y: cy, w: cw, h: 0.9, rectRadius: 0.08, fill: { color: this.colors.primary } });
      this.safeText(s, a.t || '', { x: cx, y: cy, w: cw, h: 0.9, fontSize: 18, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', budget: 8 });
      this.shape(s, 'roundRect', { x: cx, y: cy + 1.1, w: cw, h: ch - 1.1, rectRadius: 0.08, fill: { color: this.colors.secondary } });
      this.safeText(s, a.d || '', { x: cx + 0.25, y: cy + 1.3, w: cw - 0.5, h: ch - 1.5, fontSize: 14, color: this.pageText(), valign: 'middle', budget: 40 });
      if (i < n - 1) this.safeText(s, '→', { x: cx + cw + 0.02, y: cy + ch / 2 - 0.3, w: gap, h: 0.6, fontSize: 22, bold: true, color: this.colors.accent, align: 'center', valign: 'middle' });
    });
  }

  render_contact(p, data) { // #28 资源/联系（收尾）
    const s = this.newSlide(this.colors.primary);
    this.decorCircle(s, -1, 5, 4, this.colors.accent, 90);
    this.safeText(s, p.title || '谢谢观看', { x: 0, y: 1.8, w: W, h: 1.2, fontSize: 40, bold: true, color: 'FFFFFF', align: 'center' });
    const items = (data && data.contact) || ['邮箱：hello@example.com', '微信：PPT-Craft-Master', '官网：craft.example.com'];
    this.safeText(s, items.join('\n'), { x: 2.0, y: 3.4, w: W - 4.0, h: 2.4, fontSize: 16, color: this.colors.secondary, align: 'center', lineSpacingMultiple: 1.6, budget: 120 });
  }

  // ---- 复用：标题条 + 金句提示 ----
  titleBar(s, title) {
    this.safeText(s, title || '', { x: 0.8, y: 0.45, w: 11.5, h: 0.8, fontSize: 30, bold: true, color: this.colors.primary, budget: 20 });
  }
  quoteHint(s, hint) {
    if (!hint) return;
    this.safeText(s, '💡 ' + hint, { x: 0.8, y: H - 0.7, w: 11.5, h: 0.4, fontSize: 12, italic: true, color: this.colors.accent, budget: 40 });
  }

  // ============================================================
  // 主流程
  // ============================================================
  generate(outline, data) {
    this.pptx.author = this.options.author;
    this.pptx.title = this.options.title;
    let ci = 0; // 内容页序号，用于按页取 data.content[i]
    outline.forEach((page) => {
      let d;
      if (page.type === 'content') {
        const per = data && data.content && (data.content[ci] || data.content[String(ci)]);
        // 优先取本页专属内容；其次退回全局 data.content；再退回整个 data（兼容扁平结构）
        d = per || (data && data.content) || data || {};
        ci++;
      } else {
        d = (data && data[pageKey(page)]) || data || {};
      }
      this.render(page, d);
    });
  }

  async save(outputPath) {
    try {
      await this.pptx.writeFile({ fileName: outputPath });
      console.log(`✅ PPT 已生成: ${outputPath}（共 ${this.pageCount} 页）`);
      if (this.warnings.length) {
        console.log(`\n⚠️ 字数预算告警（${this.warnings.length} 条，建议回炉删减而非压字）：`);
        this.warnings.forEach((w) => console.log('   ' + w));
      } else {
        console.log('✅ 未触发字数预算告警。');
      }
      return outputPath;
    } catch (e) {
      console.error('❌ 生成失败:', e);
      throw e;
    }
  }
}

// 页面 → 数据键（AI 注入内容时按此键提供；缺省用全局 data）
function pageKey(page) {
  if (page.type === 'cover') return 'cover';
  if (page.type === 'toc') return 'toc';
  if (page.type === 'summary') return 'summary';
  if (page.type === 'end') return 'end';
  return 'content'; // 内容页统一用 content，或 data.pages[i]
}

// ============================================================
// 默认演示数据（无 --data 时按版式生成合理中文内容）
// ============================================================
function defaultCards(n) {
  const pool = [
    { title: '趋势一', desc: '下沉市场成为最大增量，县域消费增速连续领先。' },
    { title: '趋势二', desc: 'AI 从工具变基础设施，重构生产力边界。' },
    { title: '趋势三', desc: '情绪价值崛起，悦己消费占比持续走高。' },
    { title: '趋势四', desc: '绿色低碳从口号落地为采购硬指标。' },
    { title: '趋势五', desc: '银发经济规模扩张，适老化产品缺口大。' },
    { title: '趋势六', desc: '内容即渠道，种草与转化边界模糊。' }
  ];
  return pool.slice(0, n);
}
function defaultNumbers(n) {
  const pool = [{ value: '+18%', label: '县域渗透提升' }, { value: '3.2亿', label: '银发用户规模' }, { value: '67%', label: '悦己消费占比' }, { value: '¥1.2万亿', label: '绿色市场体量' }];
  return pool.slice(0, n);
}
function defaultTimeline(n) {
  const pool = [{ t: '2023', e: '概念萌芽期' }, { t: '2024', e: '试点落地期' }, { t: '2025', e: '规模扩张期' }, { t: '2026', e: '生态成熟期' }];
  return pool.slice(0, n);
}

// 根据每个页面的版式，生成贴合的演示内容
function buildDemoData(outline, topic) {
  const data = {
    cover: { title: topic, subtitle: 'AI 智能生成 · 增强版' },
    toc: { title: '目录', items: [] },
    summary: { title: '总结与展望', cards: [
      { title: '核心结论', desc: '增量在曾被忽略的附近，而非远方的红利。' },
      { title: '行动建议', desc: '以数据而非直觉做决策，小步快跑验证。' },
      { title: '长期判断', desc: 'AI 与情绪价值，是未来十年的两条主线。' }
    ] },
    end: { title: '谢谢观看' }
  };
  // 目录来自各 section + 内容
  const tocItems = [];
  outline.forEach((p) => {
    if (p.type === 'section') tocItems.push({ title: p.title });
  });
  if (!tocItems.length) tocItems.push({ title: '核心观点' }, { title: '案例与数据' }, { title: '总结展望' });
  data.toc.items = tocItems;

  data.content = {}; // 按"内容页序号"细分，供 generate() 用 ci 直接取用
  let k = 0; // 内容页序号（仅 content 类型累加），与 generate() 的 ci 对齐
  outline.forEach((p) => {
    if (p.type !== 'content') return;
    data.content[k] = demoForLayout(p.layout, k, topic);
    k++;
  });
  return data;
}

function demoForLayout(layout, i, topic) {
  const bullets = [
    '事实：三线及以下城市社零增速连续 3 年跑赢一线（来源：国家统计局）',
    '洞察：需求一直都在，只是被主流视野长期低估。',
    '观点：真正的增量不在远方，在被忽略的附近。'
  ];
  const base = {
    title: viewpointTitle(i),
    bullets,
    hint: '金句预告：增量不在远处，在曾被忽略的附近。',
    image: null,
    cards: defaultCards(6),
    numbers: defaultNumbers(4),
    timeline: defaultTimeline(4),
    quad: ['优势 Strengths', '劣势 Weaknesses', '机会 Opportunities', '威胁 Threats'],
    cols: [{ title: '守成派', points: ['依赖存量渠道', '决策链冗长', '风险偏好低'] }, { title: '进取派', points: ['押注新场景', '小步快跑', '敢用新流量'] }],
    steps: ['洞察需求', '小样验证', '快速复制', '规模放量'],
    items: defaultCards(4),
    spokes: defaultCards(5),
    center: '核心',
    chart: { name: '增长', labels: ['2023', '2024', '2025', '2026'], values: [20, 35, 28, 46] },
    donut: { labels: ['存量', '增量', '海外', '其他'], values: [40, 30, 20, 10] },
    note: '增量市场占比已近三成，且增速最快。',
    funnel: [{ t: '曝光', v: '100%' }, { t: '兴趣', v: '62%' }, { t: '意向', v: '38%' }, { t: '转化', v: '21%' }],
    slogan: viewpointTitle(i),
    acts: [{ t: '起因', d: '用户需求被长期误读。' }, { t: '经过', d: '用数据重新认识用户。' }, { t: '结果', d: '找到真正的增量。' }],
    contact: ['邮箱：hello@example.com', '微信：PPT-Craft-Master', '官网：craft.example.com']
  };
  return base;
}

function viewpointTitle(i) {
  const pool = [
    '下沉市场，才是今年最大的增量池',
    'AI 不是工具，是新生产力底座',
    '情绪价值，正在重构消费逻辑',
    '绿色从口号变成采购硬指标',
    '银发经济，被低估的万亿赛道',
    '内容即渠道，种草即转化'
  ];
  return pool[i % pool.length];
}

// ============================================================
// CLI
// ============================================================
function listStyles() { console.log('可选风格（--style）：'); Object.keys(STYLE_PRESETS).forEach((k) => console.log('  - ' + k + '  →  ' + PALETTES[STYLE_PRESETS[k].palette].name)); }
function listPalettes() { console.log('可选配色（--palette）：'); Object.entries(PALETTES).forEach(([k, v]) => console.log('  - ' + k + '  (' + v.name + ' / ' + (v.mode === 'dark' ? '暗底' : '亮底') + ')')); }
function listTokens() {
  console.log('设计令牌（DESIGN_TOKENS）：');
  console.log('  安全边距 safemargin:   ' + JSON.stringify(DESIGN_TOKENS.safeMargin) + ' in');
  console.log('  间距刻度 space:        ' + JSON.stringify(DESIGN_TOKENS.space) + ' in');
  console.log('  圆角 radius(pt):       ' + JSON.stringify(DESIGN_TOKENS.radius));
  console.log('  阴影 shadow:           ' + JSON.stringify(DESIGN_TOKENS.shadow));
  console.log('  字号梯度 typeScale(pt): ' + JSON.stringify(DESIGN_TOKENS.typeScale));
  console.log('  网格 grid:             ' + JSON.stringify(DESIGN_TOKENS.grid));
}

if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.includes('--list-styles')) { listStyles(); process.exit(0); }
  if (args.includes('--list-palettes')) { listPalettes(); process.exit(0); }
  if (args.includes('--list-tokens')) { listTokens(); process.exit(0); }

  const opt = { title: '演示文稿', palette: 'midnight', style: null, pages: 'standard', lang: 'zh', author: 'PPT Generator Pro', data: null, output: null };
  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--title': case '-t': opt.title = args[++i]; break;
      case '--style': case '-s': opt.style = args[++i]; break;
      case '--palette': case '-p': opt.palette = args[++i]; break;
      case '--pages': case '--tier': opt.pages = args[++i]; break;
      case '--lang': case '-l': opt.lang = args[++i]; break;
      case '--author': opt.author = args[++i]; break;
      case '--data': opt.data = args[++i]; break;
      case '--output': case '-o': opt.output = args[++i]; break;
    }
  }

  // 风格 → 配色
  if (opt.style) {
    const preset = STYLE_PRESETS[opt.style];
    if (!preset) { console.error('❌ 未知风格：' + opt.style); listStyles(); process.exit(1); }
    opt.palette = preset.palette;
    opt.font = preset.font;
  }

  // 输出路径（仅清洗文件名，保留目录结构）
  const rawOut = opt.output || path.join(process.env.USERPROFILE || process.env.HOME || process.cwd(), 'Desktop', `${opt.title}.pptx`);
  const finalOut = path.join(path.dirname(rawOut), path.basename(rawOut).replace(/[\\/:*?"<>|]/g, '_'));

  // 大纲 + 版式分配
  const outline = buildOutline(opt.pages, opt.title);
  const provided = opt.data ? (safeLoadData(opt.data).layouts || null) : null;
  const assigned = assignLayouts(outline, provided);

  // 数据
  let data = null;
  if (opt.data) {
    const raw = safeLoadData(opt.data);
    data = raw; // 用户按 pageKey 提供 cover/toc/content[i]/summary/end
  } else {
    data = buildDemoData(assigned, opt.title);
  }

  const gen = new PPTGenerator({ title: opt.title, author: opt.author, palette: opt.palette, font: opt.font || 'Microsoft YaHei' });
  gen.generate(assigned, data);
  gen.save(finalOut).catch((e) => { console.error(e); process.exit(1); });
}

function safeLoadData(p) {
  try { return JSON.parse(fs.readFileSync(p, 'utf8')); }
  catch (e) { console.error('❌ 读取 --data 失败：' + e.message); process.exit(1); }
}

module.exports = { PPTGenerator, PALETTES, STYLE_PRESETS, DESIGN_TOKENS, buildOutline, assignLayouts };
