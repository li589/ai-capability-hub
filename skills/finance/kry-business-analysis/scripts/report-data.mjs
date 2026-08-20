#!/usr/bin/env node
/**
 * report-data.mjs — 组件数据构建库
 *
 * 职责：把 fetch.mjs 产出的原始接口数据，经【确定性代码计算】转换为各 ECharts 组件所需的数据结构，
 *       从而把 AI 的心算 / 手工聚合替换为可测试的函数，保障报告数据准确性。
 * 定位：与 HTML 渲染层对称的"数据层"。AI 只需 fetch 拿数据 → 本库产出组件数据 → 拼接组件到 HTML。
 *
 * 用法：
 *   node report-data.mjs --test
 *       运行内置单元自测（合成数据 + 断言），退出码 0=全部通过 / 1=有失败。
 *   node report-data.mjs build --manifest <场景manifest.mjs> --data-dir <fetch产物目录> --out <输出.json>
 *       按场景 manifest 声明的数据源与组件，产出组件数据 JSON。
 *
 * 约定：
 *   1. 所有 build* 均为纯函数，输入"规整后的记录数组 + 配置"，输出组件数据结构；便于单测与复用。
 *   2. 接口数值多为字符串("60473.41")、百分比带 %("18.95%")、或 null；一律经 parseNum 规整。
 *   3. fetch.mjs 输出结构为 { api, data:[...] }；不同接口记录位置不同，manifest 通过 recordPath 指定。
 */
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

// ───────────────────────── 数值与路径工具 ─────────────────────────

/** 规整为数字：去千分位逗号、去百分号、null/空/非法 → 0 */
export function parseNum(v) {
  if (v == null) return 0;
  if (typeof v === 'number') return isFinite(v) ? v : 0;
  const s = String(v).trim().replace(/,/g, '').replace(/%/g, '');
  if (s === '' || s === '-') return 0;
  const n = parseFloat(s);
  return isFinite(n) ? n : 0;
}

/** 四舍五入到 d 位小数（避免浮点误差） */
export function round(n, d = 2) {
  const p = 10 ** d;
  return Math.round((n + Number.EPSILON) * p) / p;
}

/** 安全取嵌套字段：支持 "a.b.c" 与 "data[0].item" / "data.0.item" */
export function get(obj, pathStr) {
  if (obj == null || pathStr == null || pathStr === '') return obj;
  const parts = String(pathStr).replace(/\[(\d+)\]/g, '.$1').split('.').filter(Boolean);
  let cur = obj;
  for (const p of parts) {
    if (cur == null) return undefined;
    cur = cur[p];
  }
  return cur;
}

/** 从 fetch.mjs 输出中按 recordPath 取记录数组（非数组则包装/返回空数组） */
export function collectRecords(fetchOutput, recordPath = 'data') {
  const v = get(fetchOutput, recordPath);
  if (Array.isArray(v)) return v;
  if (v == null) return [];
  return [v];
}

/** 聚合：sum/avg/max/min/count/first */
export function aggregate(records, field, method = 'sum') {
  const rows = Array.isArray(records) ? records : [];
  const nums = rows.map((r) => parseNum(get(r, field)));
  switch (method) {
    case 'sum': return nums.reduce((a, b) => a + b, 0);
    case 'avg': return nums.length ? nums.reduce((a, b) => a + b, 0) / nums.length : 0;
    case 'max': return nums.length ? Math.max(...nums) : 0;
    case 'min': return nums.length ? Math.min(...nums) : 0;
    case 'count': return rows.length;
    case 'first': return rows.length ? parseNum(get(rows[0], field)) : 0;
    default: return 0;
  }
}

/**
 * 按 keyField 分组汇总 valueFields（求和）。返回记录数组，每条含：
 *   [keyField末段名]=分组键、_key=分组键、count=条数、以及各 valueField 的求和（同名字段）。
 * 便于分组后直接喂给 buildPie / buildRanking / buildTable（字段名保持一致）。
 * 适用：品类贡献(bigTypeName)、平台分组(platformName)、券来源(couponSource)、业务类型(busiTypeName)等。
 */
export function groupBy(records, keyField, valueFields = []) {
  const keyName = String(keyField).split('.').pop();
  const map = new Map();
  for (const r of records) {
    const k = String(get(r, keyField) ?? '');
    if (!map.has(k)) {
      const o = { [keyName]: k, _key: k, count: 0 };
      valueFields.forEach((f) => { o[f] = 0; });
      map.set(k, o);
    }
    const o = map.get(k);
    o.count++;
    valueFields.forEach((f) => { o[f] = round(o[f] + parseNum(get(r, f)), 4); });
  }
  return [...map.values()];
}

// ───────────────────────── 组件数据构建器（纯函数）─────────────────────────

/**
 * KPI 卡片。metrics: [{ label, field, unit, agg, decimals, compare, compareField, deltaType }]
 * deltaType='pct'(环比百分比,默认) | 'diff'(差值)。compareRecords 为对比周期记录。
 * 返回 [{ label, value, unit, delta?:{ value, dir, type } }]
 */
export function buildKpi(records, metrics, compareRecords = null) {
  return metrics.map((m) => {
    const agg = m.agg || 'sum';
    const dec = m.decimals ?? 2;
    const cur = round(aggregate(records, m.field, agg), dec);
    const item = { label: m.label, value: cur, unit: m.unit || '' };
    if (m.compare && compareRecords) {
      const prev = round(aggregate(compareRecords, m.compareField || m.field, agg), dec);
      if (m.deltaType === 'diff') {
        const d = round(cur - prev, dec);
        item.delta = { value: d, dir: d > 0 ? 'up' : d < 0 ? 'down' : 'flat', type: 'diff' };
      } else {
        const pct = prev === 0 ? null : round(((cur - prev) / Math.abs(prev)) * 100, 1);
        item.delta = {
          value: pct,
          dir: pct == null ? 'flat' : pct > 0 ? 'up' : pct < 0 ? 'down' : 'flat',
          type: 'pct',
        };
      }
    }
    return item;
  });
}

/**
 * 横向/纵向柱状排行。opt: { nameField, valueField, order, topN, bottomN, decimals }
 * topN+bottomN 同时给出时，返回 Top + Bottom 合并（去重）。返回 { categories, values }
 */
export function buildRanking(records, opt) {
  const { nameField, valueField, order = 'desc', topN, bottomN, decimals = 2 } = opt;
  const rows = records
    .map((r) => ({ name: get(r, nameField), value: round(parseNum(get(r, valueField)), decimals) }))
    .filter((r) => r.name != null && r.name !== '');
  rows.sort((a, b) => (order === 'asc' ? a.value - b.value : b.value - a.value));
  let picked = rows;
  if (topN != null || bottomN != null) {
    const top = topN != null ? rows.slice(0, topN) : [];
    const bot = bottomN != null ? rows.slice(-bottomN) : [];
    const seen = new Set(top);
    picked = [...top, ...bot.filter((b) => !seen.has(b))];
  }
  return { categories: picked.map((r) => String(r.name)), values: picked.map((r) => r.value) };
}

/**
 * 饼图/环形图。opt: { nameField, valueField, topN, mergeRest, decimals }
 * topN 之外的合并为 mergeRest（默认"其他"）。返回 { data:[{ name, value }] }
 */
export function buildPie(records, opt) {
  const { nameField, valueField, topN, mergeRest = '其他', decimals = 2 } = opt;
  let rows = records
    .map((r) => ({ name: String(get(r, nameField) ?? ''), value: round(parseNum(get(r, valueField)), decimals) }))
    .filter((r) => r.value !== 0 || r.name);
  rows.sort((a, b) => b.value - a.value);
  if (topN != null && rows.length > topN) {
    const head = rows.slice(0, topN);
    const restSum = round(rows.slice(topN).reduce((s, r) => s + r.value, 0), decimals);
    if (restSum > 0) head.push({ name: mergeRest, value: restSum });
    rows = head;
  }
  return { data: rows };
}

/**
 * 折线/趋势。opt: { xField, series:[{ name, field }], decimals, movingAvg:{ of, window, name } }
 * 返回 { xLabels, series:[{ name, data }] }（含可选移动均线系列）
 */
export function buildTrend(records, opt) {
  const { xField, series, decimals = 2, movingAvg } = opt;
  const xLabels = records.map((r) => String(get(r, xField) ?? ''));
  const out = series.map((s) => ({
    name: s.name,
    data: records.map((r) => round(parseNum(get(r, s.field)), decimals)),
  }));
  if (movingAvg) {
    const base = out.find((s) => s.name === movingAvg.of) || out[0];
    const w = movingAvg.window || 7;
    if (base) {
      const ma = base.data.map((_, i) => {
        const slice = base.data.slice(Math.max(0, i - w + 1), i + 1);
        return round(slice.reduce((a, b) => a + b, 0) / slice.length, decimals);
      });
      out.push({ name: movingAvg.name || `${w}日均线`, data: ma });
    }
  }
  return { xLabels, series: out };
}

/**
 * 堆叠柱图。opt: { xField, series:[{ name, field, stack }], decimals }
 * 返回 { xLabels, series:[{ name, stack, data }] }
 */
export function buildStacked(records, opt) {
  const { xField, series, decimals = 2 } = opt;
  const xLabels = records.map((r) => String(get(r, xField) ?? ''));
  const out = series.map((s) => ({
    name: s.name,
    stack: s.stack || 'total',
    data: records.map((r) => round(parseNum(get(r, s.field)), decimals)),
  }));
  return { xLabels, series: out };
}

/**
 * 数据表格。opt: { columns:[{ header, field, format?, decimals? }], sortBy, order, limit }
 * format: 'num'(数值) | 'pct'(补%) | 未指定=原样；field='#' 输出行号。
 * 返回 { headers, rows:[[...]] }
 */
export function buildTable(records, opt) {
  const { columns, sortBy, order = 'desc', limit } = opt;
  let rows = [...records];
  if (sortBy) {
    rows.sort((a, b) =>
      order === 'asc'
        ? parseNum(get(a, sortBy)) - parseNum(get(b, sortBy))
        : parseNum(get(b, sortBy)) - parseNum(get(a, sortBy))
    );
  }
  if (limit != null) rows = rows.slice(0, limit);
  const headers = columns.map((c) => c.header);
  const body = rows.map((r, i) =>
    columns.map((c) => {
      if (c.field === '#') return i + 1;
      const raw = get(r, c.field);
      if (c.format === 'num') return round(parseNum(raw), c.decimals ?? 2);
      if (c.format === 'pct') return `${round(parseNum(raw), c.decimals ?? 1)}%`;
      return raw ?? '';
    })
  );
  return { headers, rows: body };
}

/**
 * 雷达图。opt: { nameField, dimensions:[{ name, field }], normalize, max }
 * normalize=true 时各维度按记录集内最大值归一化到 [0, max]。
 * 返回 { indicator:[{ name, max }], data:[{ name, value:[] }] }
 */
export function buildRadar(records, opt) {
  const { nameField, dimensions, normalize = true, max = 100 } = opt;
  const maxByDim = dimensions.map((d) => Math.max(1, ...records.map((r) => parseNum(get(r, d.field)))));
  const indicator = dimensions.map((d, i) => ({ name: d.name, max: normalize ? max : round(maxByDim[i], 2) }));
  const data = records.map((r) => ({
    name: String(get(r, nameField) ?? ''),
    value: dimensions.map((d, i) =>
      normalize ? round((parseNum(get(r, d.field)) / maxByDim[i]) * max, 1) : round(parseNum(get(r, d.field)), 2)
    ),
  }));
  return { indicator, data };
}

/**
 * 漏斗图。stages: [{ name, value }]（value 可为字符串/数字）。返回 { data:[{ name, value }] }
 */
export function buildFunnel(stages) {
  return { data: stages.map((s) => ({ name: s.name, value: parseNum(s.value) })) };
}

/**
 * 区间分桶直方图。opt: { valueField, buckets:[{ label, min, max }] }（min 默认 -∞，max 默认 +∞，左闭右开）
 * 返回 { categories, values }
 */
export function buildBucket(records, opt) {
  const { valueField, buckets } = opt;
  const counts = buckets.map(() => 0);
  for (const r of records) {
    const v = parseNum(get(r, valueField));
    for (let i = 0; i < buckets.length; i++) {
      const min = buckets[i].min ?? -Infinity;
      const max = buckets[i].max ?? Infinity;
      if (v >= min && v < max) {
        counts[i]++;
        break;
      }
    }
  }
  return { categories: buckets.map((b) => b.label), values: counts };
}

/**
 * 四象限散点。opt: { xField, yField, nameField, decimals }
 * 返回 { data:[[x,y,name]], medianX, medianY }
 */
export function buildScatter(records, opt) {
  const { xField, yField, nameField, decimals = 2 } = opt;
  const pts = records.map((r) => [
    round(parseNum(get(r, xField)), decimals),
    round(parseNum(get(r, yField)), decimals),
    String(get(r, nameField) ?? ''),
  ]);
  const median = (arr) => {
    if (!arr.length) return 0;
    const s = [...arr].sort((a, b) => a - b);
    const m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  };
  return {
    data: pts,
    medianX: round(median(pts.map((p) => p[0])), decimals),
    medianY: round(median(pts.map((p) => p[1])), decimals),
  };
}

// ───────────────────────── 领域抽取器（处理半结构化嵌套）─────────────────────────

/**
 * 通用 itemList 抽取：{ itemList:[{ name, amount }] } → [{ name, value }]
 * 适用于 businessIncomeItems / 优惠构成等一层 code-amount 列表。
 */
export function extractItemList(obj, { nameKey = 'name', valueKey = 'amount' } = {}) {
  const list = obj?.itemList || [];
  return list
    .map((x) => ({ name: String(x[nameKey] ?? ''), value: parseNum(x[valueKey] ?? x.textVal) }))
    .filter((x) => x.name);
}

/**
 * 订单类型指标抽取：orderTypeItems（二层：类型→指标 code/amount）
 * 取每个订单类型 itemList 中 code===metricCode 的金额。返回 [{ name:类型名, value }]
 */
export function extractOrderTypeMetric(orderTypeItems, metricCode = 'orderAmt') {
  const list = orderTypeItems?.itemList || [];
  return list
    .map((t) => {
      const metric = (t.itemList || []).find((x) => x.code === metricCode);
      return { name: String(t.name ?? t.code ?? ''), value: parseNum(metric?.amount ?? metric?.textVal) };
    })
    .filter((x) => x.value !== 0);
}

/**
 * 跨订单类型汇总某指标：orderTypeItems 二层结构中，同一指标在不同类型可能带前缀
 * （如堂食 orderPeopleCnt / 外带 bringOut_orderPeopleCnt）。本函数按 code 精确匹配或 _后缀匹配，求和。
 * 用于 income/v3/list 顶层 orderPeopleCnt 等汇总字段为 null、真实值只在 orderTypeItems 的场景。
 */
export function sumOrderTypeMetric(orderTypeItems, codeSuffix) {
  const list = orderTypeItems?.itemList || [];
  let sum = 0;
  for (const t of list) {
    for (const x of t.itemList || []) {
      if (x.code === codeSuffix || String(x.code).endsWith('_' + codeSuffix)) {
        sum += parseNum(x.amount ?? x.textVal);
      }
    }
  }
  return round(sum, 2);
}

/**
 * 派生 income/v3/list 记录的汇总指标（BY_BRAND/BY_SHOP 日报聚合时，顶层人数/人均常为 null）。
 * 注入：
 *   _peopleCnt        就餐人数（orderTypeItems 跨类型求和）
 *   _avgCustomerAfter 折后人均（顶层有值则用顶层，否则 businessIncomeAmt / 就餐人数）
 * 保障日报/周报汇总场景的人数与客单价 KPI 不会因顶层 null 而归零。
 */
export function deriveIncomeMetrics(rec) {
  const peopleCnt = sumOrderTypeMetric(rec?.orderTypeItems, 'orderPeopleCnt');
  const income = parseNum(rec?.businessIncomeAmt);
  const sale = parseNum(rec?.saleAmt);
  const topAvgAfter = parseNum(rec?.avgCustomerAmtAfterDiscount);
  const topAvgPre = parseNum(rec?.avgCustomerAmtPreDiscount);
  return {
    ...rec,
    _peopleCnt: peopleCnt,
    // 折后客单价 = 营业收入 / 就餐人数（顶层有值优先，否则派生）
    _avgCustomerAfter: topAvgAfter > 0 ? topAvgAfter : peopleCnt > 0 ? round(income / peopleCnt, 2) : 0,
    // 折前客单价 = 营业额(saleAmt) / 就餐人数（顶层有值优先，否则派生）
    _avgCustomerPre: topAvgPre > 0 ? topAvgPre : peopleCnt > 0 ? round(sale / peopleCnt, 2) : 0,
  };
}

// ───────────────────────── 导出的库对象（供 manifest.build 使用）─────────────────────────

export const lib = {
  parseNum, round, get, collectRecords, aggregate, groupBy,
  buildKpi, buildRanking, buildPie, buildTrend, buildStacked,
  buildTable, buildRadar, buildFunnel, buildBucket, buildScatter,
  extractItemList, extractOrderTypeMetric, sumOrderTypeMetric, deriveIncomeMetrics,
};

// ───────────────────────── CLI ─────────────────────────

function getArg(argv, name) {
  const i = argv.indexOf(name);
  return i >= 0 && i + 1 < argv.length ? argv[i + 1] : undefined;
}

async function runBuild(argv) {
  const manifestPath = getArg(argv, '--manifest');
  const dataDir = getArg(argv, '--data-dir') || '.';
  const out = getArg(argv, '--out') || 'report-data.json';
  if (!manifestPath) {
    console.error('[report-data] ❌ 缺少 --manifest');
    process.exit(1);
  }
  const mod = await import(pathToFileURL(path.resolve(manifestPath)).href);
  const manifest = mod.default || mod.manifest;
  if (!manifest || typeof manifest.build !== 'function') {
    console.error('[report-data] ❌ manifest 需 export default { sources, build(lib, data) }');
    process.exit(1);
  }
  const data = {};
  let missing = 0;
  for (const [key, file] of Object.entries(manifest.sources || {})) {
    try {
      data[key] = JSON.parse(readFileSync(path.resolve(dataDir, file), 'utf-8'));
    } catch {
      data[key] = null;
      missing++;
      console.error(`[report-data] ⚠️ 数据文件缺失/无法解析: ${file}（对应板块将降级）`);
    }
  }
  const result = manifest.build(lib, data);
  writeFileSync(path.resolve(out), JSON.stringify(result, null, 2), 'utf-8');
  console.error(`[report-data] ✅ 组件数据已生成: ${out}（数据源缺失 ${missing} 个）`);
}

// ───────────────────────── 内置单元自测 ─────────────────────────

function runTest() {
  let pass = 0;
  let fail = 0;
  const eq = (name, got, exp) => {
    const g = JSON.stringify(got);
    const e = JSON.stringify(exp);
    if (g === e) {
      pass++;
    } else {
      fail++;
      console.error(`❌ ${name}\n   期望: ${e}\n   实际: ${g}`);
    }
  };

  // parseNum
  eq('parseNum 字符串金额', parseNum('60473.41'), 60473.41);
  eq('parseNum 百分比', parseNum('18.95%'), 18.95);
  eq('parseNum 千分位', parseNum('1,234.5'), 1234.5);
  eq('parseNum null', parseNum(null), 0);
  eq('parseNum 短横', parseNum('-'), 0);
  eq('parseNum 数字', parseNum(50), 50);

  // get / collectRecords
  eq('get 嵌套', get({ a: { b: [{ c: 9 }] } }, 'a.b[0].c'), 9);
  eq('collectRecords data[0].item', collectRecords({ data: [{ item: [1, 2] }] }, 'data.0.item'), [1, 2]);
  eq('collectRecords 空', collectRecords({ data: [] }, 'data'), []);

  // aggregate
  const rec = [{ v: '10' }, { v: '20' }, { v: null }];
  eq('aggregate sum', aggregate(rec, 'v', 'sum'), 30);
  eq('aggregate avg', aggregate(rec, 'v', 'avg'), 10);
  eq('aggregate count', aggregate(rec, 'v', 'count'), 3);

  // buildKpi 环比
  const cur = [{ saleAmt: '100' }];
  const prev = [{ saleAmt: '80' }];
  eq('buildKpi 环比pct', buildKpi(cur, [{ label: '营业额', field: 'saleAmt', unit: '元', compare: true }], prev), [
    { label: '营业额', value: 100, unit: '元', delta: { value: 25, dir: 'up', type: 'pct' } },
  ]);
  eq('buildKpi 差值diff', buildKpi([{ r: '3' }], [{ label: '翻台率', field: 'r', unit: '', compare: true, deltaType: 'diff' }], [{ r: '2' }]), [
    { label: '翻台率', value: 3, unit: '', delta: { value: 1, dir: 'up', type: 'diff' } },
  ]);
  eq('buildKpi 除0保护', buildKpi([{ v: '5' }], [{ label: 'x', field: 'v', compare: true }], [{ v: '0' }]), [
    { label: 'x', value: 5, unit: '', delta: { value: null, dir: 'flat', type: 'pct' } },
  ]);

  // buildRanking Top+Bottom
  const shops = [{ n: 'A', s: '30' }, { n: 'B', s: '10' }, { n: 'C', s: '50' }, { n: 'D', s: '20' }];
  eq('buildRanking desc', buildRanking(shops, { nameField: 'n', valueField: 's' }), {
    categories: ['C', 'A', 'D', 'B'], values: [50, 30, 20, 10],
  });
  eq('buildRanking Top1+Bottom1', buildRanking(shops, { nameField: 'n', valueField: 's', topN: 1, bottomN: 1 }), {
    categories: ['C', 'B'], values: [50, 10],
  });

  // buildPie topN + 其他
  const pie = [{ n: 'a', v: '50' }, { n: 'b', v: '30' }, { n: 'c', v: '10' }, { n: 'd', v: '10' }];
  eq('buildPie Top2+其他', buildPie(pie, { nameField: 'n', valueField: 'v', topN: 2 }), {
    data: [{ name: 'a', value: 50 }, { name: 'b', value: 30 }, { name: '其他', value: 20 }],
  });

  // buildTrend + 移动均线
  const days = [{ d: '1', s: '10' }, { d: '2', s: '20' }, { d: '3', s: '30' }];
  eq('buildTrend 双系列', buildTrend(days, { xField: 'd', series: [{ name: '营业额', field: 's' }] }), {
    xLabels: ['1', '2', '3'], series: [{ name: '营业额', data: [10, 20, 30] }],
  });
  eq('buildTrend 移动均线', buildTrend(days, { xField: 'd', series: [{ name: 'S', field: 's' }], movingAvg: { of: 'S', window: 2, name: 'MA2' } }).series[1], {
    name: 'MA2', data: [10, 15, 25],
  });

  // buildStacked
  eq('buildStacked', buildStacked([{ x: 'P', a: '1', b: '2' }], { xField: 'x', series: [{ name: 'A', field: 'a', stack: 't' }, { name: 'B', field: 'b', stack: 't' }] }), {
    xLabels: ['P'], series: [{ name: 'A', stack: 't', data: [1] }, { name: 'B', stack: 't', data: [2] }],
  });

  // buildTable 排序+行号+格式
  eq('buildTable', buildTable(shops, { columns: [{ header: '#', field: '#' }, { header: '店', field: 'n' }, { header: '额', field: 's', format: 'num' }], sortBy: 's', limit: 2 }), {
    headers: ['#', '店', '额'], rows: [[1, 'C', 50], [2, 'A', 30]],
  });

  // buildRadar 归一化
  eq('buildRadar 归一化', buildRadar([{ n: 'A', x: '50', y: '100' }, { n: 'B', x: '100', y: '50' }], { nameField: 'n', dimensions: [{ name: 'X', field: 'x' }, { name: 'Y', field: 'y' }] }), {
    indicator: [{ name: 'X', max: 100 }, { name: 'Y', max: 100 }],
    data: [{ name: 'A', value: [50, 100] }, { name: 'B', value: [100, 50] }],
  });

  // buildBucket
  eq('buildBucket', buildBucket([{ v: '3' }, { v: '15' }, { v: '150' }], { valueField: 'v', buckets: [{ label: '<10', max: 10 }, { label: '10-100', min: 10, max: 100 }, { label: '≥100', min: 100 }] }), {
    categories: ['<10', '10-100', '≥100'], values: [1, 1, 1],
  });

  // buildFunnel
  eq('buildFunnel', buildFunnel([{ name: '预订', value: '100' }, { name: '到店', value: '70' }]), {
    data: [{ name: '预订', value: 100 }, { name: '到店', value: 70 }],
  });

  // buildScatter 中位数
  eq('buildScatter', buildScatter([{ x: '1', y: '10', n: 'a' }, { x: '3', y: '30', n: 'b' }, { x: '5', y: '20', n: 'c' }], { xField: 'x', yField: 'y', nameField: 'n' }), {
    data: [[1, 10, 'a'], [3, 30, 'b'], [5, 20, 'c']], medianX: 3, medianY: 20,
  });

  // groupBy 分组汇总
  const catRecs = [{ t: '热菜', a: '100' }, { t: '凉菜', a: '50' }, { t: '热菜', a: '30' }];
  eq('groupBy 汇总', groupBy(catRecs, 't', ['a']), [{ t: '热菜', _key: '热菜', count: 2, a: 130 }, { t: '凉菜', _key: '凉菜', count: 1, a: 50 }]);
  eq('groupBy+buildPie 品类占比', buildPie(groupBy(catRecs, 't', ['a']), { nameField: 't', valueField: 'a' }), { data: [{ name: '热菜', value: 130 }, { name: '凉菜', value: 50 }] });

  // extractOrderTypeMetric（真实 orderTypeItems 形态）
  const oti = { itemList: [{ name: '堂食', itemList: [{ code: 'orderAmt', amount: '60086.93' }] }, { name: '外带', itemList: [{ code: 'orderAmt', amount: '56.00' }] }] };
  eq('extractOrderTypeMetric', extractOrderTypeMetric(oti, 'orderAmt'), [{ name: '堂食', value: 60086.93 }, { name: '外带', value: 56 }]);

  // sumOrderTypeMetric（跨类型求和，含 _前缀匹配）
  const oti2 = { itemList: [{ name: '堂食', itemList: [{ code: 'orderPeopleCnt', amount: '70' }] }, { name: '外带', itemList: [{ code: 'bringOut_orderPeopleCnt', amount: '1' }] }] };
  eq('sumOrderTypeMetric 就餐人数', sumOrderTypeMetric(oti2, 'orderPeopleCnt'), 71);

  // deriveIncomeMetrics（顶层 null 时派生人均）
  const incRec = { businessIncomeAmt: '49010.82', avgCustomerAmtAfterDiscount: null, orderTypeItems: oti2 };
  const derived = deriveIncomeMetrics(incRec);
  eq('deriveIncomeMetrics 人数', derived._peopleCnt, 71);
  eq('deriveIncomeMetrics 派生人均', derived._avgCustomerAfter, 690.29);

  console.error(`\n[report-data 自测] 通过 ${pass} / 失败 ${fail}`);
  process.exit(fail ? 1 : 0);
}

// ───────────────────────── 入口 ─────────────────────────

const argv = process.argv.slice(2);
const isMain = pathToFileURL(process.argv[1] || '').href === import.meta.url;
if (isMain) {
  if (argv.includes('--test')) runTest();
  else if (argv[0] === 'build') runBuild(argv);
  else {
    console.error('用法:\n  node report-data.mjs --test\n  node report-data.mjs build --manifest <f.mjs> --data-dir <dir> --out <out.json>');
    process.exit(1);
  }
}
