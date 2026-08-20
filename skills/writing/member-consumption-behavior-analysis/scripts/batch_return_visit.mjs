#!/usr/bin/env node
/**
 * 老客回头与未回访 - 批处理并发脚本
 * 将原来 4 条串行 DataCube 查询改为 Promise 并发执行
 *
 * 用法:
 *   node batch_return_visit.mjs \
 *     --endDate "2026-06-22 23:59:59" \
 *     [--startDate "2026-06-01 00:00:00"] \
 *     [--activeStartDate "..."] [--activeEndDate "..."] \
 *     [--returnStartDate "..."] [--returnEndDate "..."] \
 *     [--periodDays 30] [--highValueAmount 1000] \
 *     [--highFrequencyCount 3] [--limit 200] \
 *     [--omShopCodes "'xxx'"]
 */
import { runTasksViaBatch, parseArg } from './lib--run-tasks-with-limit.mjs';

const endDate = parseArg('endDate');
const startDate = parseArg('startDate');
const activeStartDate = parseArg('activeStartDate', startDate);
const activeEndDate = parseArg('activeEndDate', endDate);
const returnStartDate = parseArg('returnStartDate', startDate);
const returnEndDate = parseArg('returnEndDate', endDate);
const periodDays = parseArg('periodDays', '30');
const highValueAmount = parseArg('highValueAmount', '1000');
const highFrequencyCount = parseArg('highFrequencyCount', '3');
const limit = parseArg('limit', '200');
const omShopCodes = parseArg('omShopCodes');

if (!endDate) {
  console.error('Usage: node batch_return_visit.mjs --endDate "<end>" [--startDate "<start>"] [options]');
  process.exit(2);
}

const shopSuffix = omShopCodes ? ` --omShopCodes ${omShopCodes}` : '';

const tasks = [
  {
    name: '老客复购率趋势',
    command: `sl datacube task-260514155605001415 --format json --exeTaskId 260514155605000986 --endDate "${endDate}" --periodDays "${periodDays}"${shopSuffix}`,
  },
  {
    name: '老客平均复购周期',
    command: `sl datacube task-260514160503001416 --format json --exeTaskId 260514160503000987 --endDate "${endDate}" --periodDays "${periodDays}"${shopSuffix}`,
  },
  {
    name: '活跃期未回访概览',
    command: `sl datacube task-260514161156001417 --format json --exeTaskId 260514161156000988 --activeStartDate "${activeStartDate}" --activeEndDate "${activeEndDate}" --returnStartDate "${returnStartDate}" --returnEndDate "${returnEndDate}"${shopSuffix}`,
  },
  {
    name: '活跃期未回访名单',
    command: `sl datacube task-260514161219001418 --format json --exeTaskId 260514161219000989 --activeStartDate "${activeStartDate}" --activeEndDate "${activeEndDate}" --returnStartDate "${returnStartDate}" --returnEndDate "${returnEndDate}" --highValueAmount "${highValueAmount}" --highFrequencyCount "${highFrequencyCount}" --limit "${limit}"${shopSuffix}`,
  },
];

const result = await runTasksViaBatch(tasks, { concurrency: 4 });

result.scope = {
  endDate, startDate, activeStartDate, activeEndDate,
  returnStartDate, returnEndDate, periodDays,
  highValueAmount, highFrequencyCount, limit,
  omShopCodes: omShopCodes || null,
};

for (const [name, q] of Object.entries(result.queries)) {
  console.error(`  ${name}: ${q.elapsedMs}ms [${q.status}]${q.rowCount ? ` ${q.rowCount} rows` : ''}`);
}
console.error(`\n  总耗时: ${result.elapsedMs}ms  状态: ${result.status}`);

console.log(JSON.stringify(result, null, 2));
