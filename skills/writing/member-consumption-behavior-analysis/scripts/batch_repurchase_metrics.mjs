#!/usr/bin/env node
/**
 * 复购整体指标 - 批处理并发脚本
 * 将原来 5 条串行 general 查询改为 Promise 并发执行
 *
 * 用法:
 *   node batch_repurchase_metrics.mjs \
 *     --beginDate "2026-06-01 00:00:00" --endDate "2026-06-22 23:59:59" \
 *     --preBeginDate "2026-05-10 00:00:00" --preEndDate "2026-05-31 23:59:59" \
 *     [--shopFilterTypeValue '["xxx"]'] [--repurchaseMode 1]
 *
 * 也可传 yyyy-MM-dd，脚本会自动补齐起止时间。
 */
import { runTasksViaBatch, parseArg, normalizeDateTime } from './lib--run-tasks-with-limit.mjs';

const beginDate = normalizeDateTime(parseArg('beginDate'), 'start');
const endDate = normalizeDateTime(parseArg('endDate'), 'end');
const preBeginDate = normalizeDateTime(parseArg('preBeginDate'), 'start');
const preEndDate = normalizeDateTime(parseArg('preEndDate'), 'end');
const shopFilterTypeValue = parseArg('shopFilterTypeValue', '[]');
const repurchaseMode = parseArg('repurchaseMode', '1');

if (!beginDate || !endDate || !preBeginDate || !preEndDate) {
  console.error('Usage: node batch_repurchase_metrics.mjs --beginDate <B> --endDate <E> --preBeginDate <PB> --preEndDate <PE>');
  process.exit(2);
}

const baseParams = {
  beginDate, endDate, preBeginDate, preEndDate,
  dateType: 1,
  shopFilterType: 1,
  shopFilterTypeValue: JSON.parse(shopFilterTypeValue),
  repurchaseMode: Number(repurchaseMode),
};

function makeCommand(action, extraParams = {}) {
  const params = JSON.stringify({ ...baseParams, ...extraParams });
  return `sl general ${action} --params '${params}' --format json`;
}

const tasks = [
  { name: '复购核心指标', command: makeCommand('get-data-indicators') },
  { name: '复购增长趋势', command: makeCommand('get-re-purchase-growth-trend') },
  { name: '复购群体趋势', command: makeCommand('get-re-purchase-group-trend') },
  { name: '复购次数分布', command: makeCommand('get-repurchase-frequency-data') },
  { name: '复购会员排行', command: makeCommand('get-ranking-repurchase-members', { dimensionType: 2, page: 1, size: 10 }) },
];

const result = await runTasksViaBatch(tasks, { concurrency: 6 });

result.scope = { beginDate, endDate, preBeginDate, preEndDate, shopFilterTypeValue, repurchaseMode };

for (const [name, q] of Object.entries(result.queries)) {
  console.error(`  ${name}: ${q.elapsedMs}ms [${q.status}]${q.rowCount ? ` ${q.rowCount} rows` : ''}`);
}
console.error(`\n  总耗时: ${result.elapsedMs}ms  状态: ${result.status}`);

console.log(JSON.stringify(result, null, 2));
