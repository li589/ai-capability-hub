#!/usr/bin/env node
/**
 * fetch.mjs - 数据编排脚本
 *
 * 功能：根据 constraints.json 中注册的接口约束，自动处理：
 *   1. date-split: 日期拆分（dateRange超限时按天/N天拆分并发调用）
 *   2. shop-batch: 门店分批（shopIds超限时分批并发调用）
 *   3. auto-page: 自动翻页（响应总数超页大小时串行翻页）
 *
 * 用法：
 *   node scripts/fetch.mjs --api <path> -b <brandId> -d '<json>' -o <output.json>
 *   node scripts/fetch.mjs --api <path> -s <shopId> -d '<json>' -o <output.json>
 *
 * 参数：
 *   --api          接口路径（必填）
 *   -b, --brand    品牌ID（品牌授权接口）
 *   -s, --shop     门店ID（门店授权接口）
 *   -d, --data     请求参数JSON（必填）
 *   -o, --output   输出文件路径（必填）
 *   --concurrency  并发数（默认5）
 */

import { execFile } from 'child_process';
import { promisify } from 'util';
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';
import sdk from './log-sdk.mjs';

const log = sdk.logger.child({ tag: 'kry-business-analysis' });

const __dirname = dirname(fileURLToPath(import.meta.url));

// ─── 参数解析 ───────────────────────────────────────────────────────────────

function parseArgs(argv) {
  const args = { concurrency: 5 };
  for (let i = 2; i < argv.length; i++) {
    switch (argv[i]) {
      case '--api':
        args.api = argv[++i]; break;
      case '-b': case '--brand':
        args.brand = argv[++i]; break;
      case '-s': case '--shop':
        args.shop = argv[++i]; break;
      case '-d': case '--data':
        args.data = argv[++i]; break;
      case '-o': case '--output':
        args.output = argv[++i]; break;
      case '--concurrency':
        args.concurrency = parseInt(argv[++i], 10); break;
    }
  }
  if (!args.api || !args.data || !args.output) {
    console.error('用法: node fetch.mjs --api <path> -b <brandId> -d \'<json>\' -o <output.json>');
    process.exit(1);
  }
  return args;
}

// ─── 约束加载 ───────────────────────────────────────────────────────────────

function loadConstraints() {
  const file = resolve(__dirname, 'constraints.json');
  const raw = JSON.parse(readFileSync(file, 'utf-8'));
  return {
    apis: raw.apis || {},
    globalDefense: raw.globalDefense || { maxPages: 80, maxTotalTasks: 200, timeout: 200 }
  };
}

// ─── 工具函数 ───────────────────────────────────────────────────────────────

/** 计算两个日期之间的天数差 */
function daysBetween(startDate, endDate) {
  const s = new Date(startDate);
  const e = new Date(endDate);
  return Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1;
}

/** 生成日期范围数组，每段最多 maxDays 天 */
function splitDateRange(startDate, endDate, maxDays) {
  const chunks = [];
  let current = new Date(startDate);
  const end = new Date(endDate);

  while (current <= end) {
    const chunkEnd = new Date(current);
    chunkEnd.setDate(chunkEnd.getDate() + maxDays - 1);
    if (chunkEnd > end) chunkEnd.setTime(end.getTime());

    chunks.push({
      startDate: fmt(current),
      endDate: fmt(chunkEnd)
    });

    current = new Date(chunkEnd);
    current.setDate(current.getDate() + 1);
  }
  return chunks;
}

/** 将门店数组拆分为 N 个批次 */
function splitShopIds(shopIds, maxSize) {
  const batches = [];
  for (let i = 0; i < shopIds.length; i += maxSize) {
    batches.push(shopIds.slice(i, i + maxSize));
  }
  return batches;
}

/** 日期格式化 yyyy-MM-dd */
function fmt(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** 深度合并默认参数（defaults 被 user 覆盖，用户参数优先） */
function mergeDefaults(defaults, user) {
  if (!defaults) return user;
  const result = { ...defaults };
  for (const key of Object.keys(user)) {
    if (user[key] !== undefined && user[key] !== null) {
      if (typeof user[key] === 'object' && !Array.isArray(user[key]) &&
        typeof result[key] === 'object' && !Array.isArray(result[key])) {
        result[key] = { ...result[key], ...user[key] };
      } else {
        result[key] = user[key];
      }
    }
  }
  return result;
}

function valueType(value) {
  if (value === undefined || value === null) return 'missing';
  if (Array.isArray(value)) return 'array';
  return typeof value === 'object' ? 'object' : typeof value;
}

function validateShape(actual, expected, prefix = '') {
  const errors = [];
  if (!expected || typeof expected !== 'object' || Array.isArray(expected)) return errors;
  for (const key of Object.keys(expected)) {
    const path = prefix ? `${prefix}.${key}` : key;
    const expectedValue = expected[key];
    const actualValue = actual?.[key];
    const expectedType = valueType(expectedValue);
    const actualType = valueType(actualValue);
    if (actualType === 'missing') {
      errors.push(`缺少参数 ${path}`);
      continue;
    }
    if (expectedType !== actualType) {
      errors.push(`${path} 类型错误：期望 ${expectedType}，实际 ${actualType}`);
      continue;
    }
    if (expectedType === 'object') errors.push(...validateShape(actualValue, expectedValue, path));
  }
  return errors;
}

function validateParams(apiPath, params, constraint, args) {
  if (!constraint._registered) return [];
  const errors = [];
  const nesting = constraint.paramsNesting;
  const dateFieldMode = constraint.dateFieldMode || 'range';
  const root = nesting ? params?.[nesting] : params;

  if (nesting && valueType(root) !== 'object') {
    errors.push(`缺少参数 ${nesting}，该接口的 dateRange/shopIds 必须放在 ${nesting} 内`);
  }

  if (dateFieldMode === 'flat') {
    if (typeof params.startDate !== 'string' || typeof params.endDate !== 'string') {
      errors.push('缺少平铺日期参数 startDate/endDate，或类型不是 string');
    }
  } else {
    const dateRange = root?.dateRange;
    if (valueType(dateRange) !== 'object' || typeof dateRange.startDate !== 'string' || typeof dateRange.endDate !== 'string') {
      errors.push(`${nesting ? `${nesting}.` : ''}dateRange 必须为 { startDate:string, endDate:string }`);
    }
  }

  if (args.brand) {
    const shopIds = root?.shopIds;
    if (!Array.isArray(shopIds)) {
      errors.push(`${nesting ? `${nesting}.` : ''}shopIds 必须为字符串数组；全部门店请传 []`);
    } else if (shopIds.some((id) => typeof id !== 'string')) {
      errors.push(`${nesting ? `${nesting}.` : ''}shopIds 内元素必须是 string，不能传 number`);
    }
  }

  errors.push(...validateShape(params, constraint.defaultParams));

  const forbiddenFields = [
    ['shopIdList', '请使用 shopIds，且类型为 Array<string>'],
    ['sellType', '请使用 sellLatitude.sellCollectType + sellLatitude.countType'],
    ['pageNo', '报表类接口通常使用 pageBean；请先核对 kry-cli view 与 field-map/_spec.md'],
    ['pageSize', '报表类接口通常使用 pageBean；请先核对 kry-cli view 与 field-map/_spec.md'],
  ];
  for (const [field, hint] of forbiddenFields) {
    if (Object.prototype.hasOwnProperty.call(params, field)) errors.push(`疑似错误字段 ${field}：${hint}`);
  }

  return [...new Set(errors)].map((msg) => `${apiPath}: ${msg}`);
}

function buildParamSuggestion(errors) {
  return `${errors.join('；')}。请先执行 kry-cli view <接口路径> 查看官方示例，并核对 references/field-map/_spec.md 的请求参数常见错误。`;
}

/** 并发控制执行 */
async function concurrent(tasks, concurrency) {
  const results = [];
  let idx = 0;

  async function worker() {
    while (idx < tasks.length) {
      const i = idx++;
      results[i] = await tasks[i]();
    }
  }

  const workers = Array.from({ length: Math.min(concurrency, tasks.length) }, () => worker());
  await Promise.all(workers);
  return results;
}

/** 全局QPS控制 - 每秒最多10次调用 */
let lastCallTime = 0;
const MIN_INTERVAL = 100; // ms between calls (10 QPS)

async function rateLimitedCall(fn) {
  const now = Date.now();
  const wait = Math.max(0, MIN_INTERVAL - (now - lastCallTime));
  if (wait > 0) await new Promise(r => setTimeout(r, wait));
  lastCallTime = Date.now();
  return fn();
}

// ─── kry-cli call 封装 ──────────────────────────────────────────────────────

const execFileAsync = promisify(execFile);

/**
 * 调用 kry-cli，异步执行以支持 concurrent() 真正并发（execFileSync 会阻塞事件循环导致并发失效）。
 * 失败自动重试（指数退避）：仅对进程异常/超时/网络/限流/JSON解析失败等瞬时错误重试；
 * 服务端业务错误（code 非0，如参数错）不重试（重试无意义）。
 */
async function callApi(apiPath, authFlag, authId, params, retries = 2) {
  const paramsJson = JSON.stringify(params);
  const isWin = process.platform === 'win32';

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const { stdout } = await execFileAsync('kry-cli',
        ['call', apiPath, authFlag, authId, '-d', paramsJson],
        {
          encoding: 'utf-8',
          maxBuffer: 50 * 1024 * 1024, // 50MB（execFile 默认仅 1MB，必须显式保留，否则大响应被截断→数据不全）
          timeout: 30000, // 30s per call
          shell: isWin // 仅 Windows 需要 shell 解析 .cmd shim；macOS/Linux 直接传参避免 JSON 被 shell 拆散
        }
      );
      const parsed = JSON.parse(stdout);
      // traceId 用于链路追踪：kry-cli 响应的链路标识字段为 messageUuid（已实测确认），其余为兜底
      const traceId = parsed?.messageUuid || parsed?.traceId || parsed?.result?.traceId || parsed?.requestId || null;
      // 正常响应: {result: {data: {...}}, code: null/0, ...}
      // 服务端业务错误: {code: 3000, message: "系统错误,..."} —— 参数/业务问题，重试无意义，直接返回
      if (parsed.code && parsed.code !== 200 && parsed.code !== 0) {
        const errMsg = parsed.message || parsed.apiMessage || 'server error';
        // ★ 主链路上报: 接口调用失败（服务端业务错误）——入参/出参/traceId/错误码
        log.error(`接口调用失败`, { api: apiPath, brandId: authId, traceId, code: parsed.code, message: errMsg, params, response: parsed });
        console.error(`[fetch] ❌ 接口错误: api=${apiPath}, code=${parsed.code}, traceId=${traceId}, ${errMsg}`);
        return { _error: true, code: parsed.code, message: errMsg };
      }
      // ★ 主链路上报: 接口调用成功——入参/出参/traceId
      log.info(`接口调用成功`, { api: apiPath, brandId: authId, traceId, params, response: parsed });
      return parsed;
    } catch (err) {
      // 进程异常/超时/网络/限流/JSON解析失败等瞬时错误，重试兼底
      const output = (err.stdout || '') + (err.stderr || '');
      const errMsg = output.slice(0, 500) || err.message?.slice(0, 300);
      if (attempt < retries) {
        const backoff = 500 * Math.pow(2, attempt); // 500ms → 1000ms
        console.error(`[fetch] ⚠ 调用失败(第${attempt + 1}/${retries + 1}次)，${backoff}ms后重试: api=${apiPath}, ${errMsg}`);
        await new Promise(r => setTimeout(r, backoff));
        continue;
      }
      // ★ 主链路上报: 接口调用异常（重试耗尽）——入参/错误信息/CLI原始输出（JSON解析失败通常无traceId）
      log.error(`接口调用异常`, { api: apiPath, brandId: authId, params, error: errMsg, output: output.slice(0, 1000) });
      console.error(`[fetch] ❌ 接口异常(重试${retries}次后仍失败): api=${apiPath}, ${errMsg}`);
      return { _error: true, message: errMsg };
    }
  }
}

// ─── 自动翻页 ───────────────────────────────────────────────────────────────

async function autoPage(apiPath, authFlag, authId, params, constraint, defense) {
  const allData = [];
  const errors = [];
  let pageNum = 1;
  let pageSize = getPageSize(params, constraint);
  let totalCount = Infinity;
  let retryWithSmallerPage = false;

  while ((pageNum - 1) * pageSize < totalCount) {
    const pageParams = setPageNum(params, pageNum, constraint);
    // 如果需要降级页大小，更新pageSize
    if (retryWithSmallerPage) {
      if (pageParams.pageBean) pageParams.pageBean.pageSize = pageSize;
    }
    const result = await callApi(apiPath, authFlag, authId, pageParams);

    if (result._error) {
      // 精确匹配“响应体过大”错误：仅当 message 包含 buffer/bytes 关键词时才触发降级
      const msg = result.message || '';
      const isBufferOverflow = msg.includes('buffer') || msg.includes('Buffer') || msg.includes('bytes to buffer');
      if (isBufferOverflow && pageSize > 200 && !retryWithSmallerPage) {
        // ★ 主链路上报: 响应过大降级
        log.warn(`响应过大，自动降级pageSize`, { api: apiPath, fromPageSize: pageSize, toPageSize: 200 });
        console.error(`[fetch] 响应过大，自动降级 pageSize ${pageSize}→200 重试`);
        pageSize = 200;
        retryWithSmallerPage = true;
        pageNum = 1;
        allData.length = 0;
        continue;
      }
      errors.push({ page: pageNum, reason: result.message });
      break;
    }

    // ─── 统一分页容器定位：一次拿到数据数组 + 总数（覆盖 data.list / data.values / data.item.values）───
    const { records: pageData, total } = resolvePageContainer(result);
    totalCount = total;

    // ─── 首页预检：拿到 totalCount 后判断翻页量是否超限 ───
    if (pageNum === 1 && totalCount > 0) {
      const totalPages = Math.ceil(totalCount / pageSize);
      if (totalPages > defense.maxPages) {
        // ★ 主链路上报: 首页预检拒绝
        const reason = `数据量过大：共${totalCount}条需${totalPages}页（上限${defense.maxPages}页=${defense.maxPages * pageSize}条）`;
        log.warn(`首页预检拒绝：翻页量超限`, { api: apiPath, totalCount, totalPages, maxPages: defense.maxPages, maxRecords: defense.maxPages * pageSize });
        console.error(`[fetch] ⚠ 首页预检拒绝: ${reason}`);
        return {
          rejected: true,
          reason,
          suggestion: '建议选择具体门店、缩短时间范围、或使用品牌维度汇总',
          data: [], totalRecords: totalCount
        };
      }
    }

    allData.push(...pageData);

    // 如果本页数据不足 pageSize，说明已是最后一页
    if (pageData.length < pageSize) break;

    pageNum++;
  }

  // declaredTotal: 接口声明的总记录数（来源: response.result.data.totalSize 或 totalCount）
  return { data: allData, errors, declaredTotal: totalCount === Infinity ? 0 : totalCount };
}

/** 计算维度感知的有效 pageSize：命中 pageSizeOverrides 规则则降级，否则用 maxPageSize。
 *  用于 income/v3 等接口在 BY_SHOP 等大数据量维度下预防性降低 pageSize，避免服务端异常。 */
function getEffectivePageSize(params, constraint) {
  const maxSize = constraint.maxPageSize || 1000;
  const ov = constraint.pageSizeOverrides;
  if (ov && ov.field && ov.rules) {
    const nesting = constraint.paramsNesting;
    const fieldVal = nesting ? params[nesting]?.[ov.field] : params[ov.field];
    if (fieldVal != null && ov.rules[fieldVal] != null) {
      return ov.rules[fieldVal];
    }
  }
  return maxSize;
}

/** 从 params 中获取 pageSize，强制升级至有效 maxPageSize（维度感知）确保最大效率 */
function getPageSize(params, constraint) {
  return getEffectivePageSize(params, constraint);
}

/** 设置分页页码，同时强制 pageSize = maxPageSize */
function setPageNum(params, pageNum, constraint) {
  const clone = JSON.parse(JSON.stringify(params));
  const maxSize = getEffectivePageSize(params, constraint);
  if (constraint.pageBeanType === 'string') {
    if (clone.pageBean) {
      clone.pageBean.pageNum = String(pageNum);
      clone.pageBean.pageSize = String(maxSize);
    }
  } else {
    if (clone.pageBean) {
      clone.pageBean.pageNum = pageNum;
      clone.pageBean.pageSize = maxSize;
    }
  }
  return clone;
}

/** 数值化：转 Number，失败返回兜底值（防 String totalCount 拼接、防 NaN） */
function numOr(v, fallback) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

/**
 * 统一分页容器定位：返回 { records, total }
 *
 * 底层接口输出结构不统一（数据数组可能在 data.list / data.values，
 * 团购对账则嵌一层 data.item.values），此函数用一套规则覆盖全部 13 个注册接口：
 *   1. 从 result.result.data 出发，若其直接含 list/values 数组 → 命中（12/13 接口）；
 *   2. 否则下探一层白名单包装键 item，再判定（仅团购对账 data.item.values）；
 *   3. 均未命中（如空数据仅返回 {totalSize:0}）→ records=[]，避免把容器对象兜底成脏记录。
 * total 从命中容器取 totalSize ?? totalCount，用于翻页终止 / 首页预检 / declaredTotal。
 * 注：orderItem 等聚合容器接口 records 为聚合行数组（length 可能=1），total 为内部明细数，符合预期。
 */
function resolvePageContainer(result) {
  const data = result?.result?.data;
  const pick = (node) => {
    if (!node || typeof node !== 'object') return null;
    if (Array.isArray(node)) return { records: node, total: node.length };
    if (Array.isArray(node.list)) return { records: node.list, total: numOr(node.totalSize ?? node.totalCount, node.list.length) };
    if (Array.isArray(node.values)) return { records: node.values, total: numOr(node.totalSize ?? node.totalCount, node.values.length) };
    return null;
  };
  const hit = pick(data) || pick(data?.item);
  if (hit) return hit;
  // 空数据 / 无法识别结构：返回空数组，total 尽量从顶层取
  return { records: [], total: data ? numOr(data.totalSize ?? data.totalCount, 0) : 0 };
}

// ─── 主编排逻辑 ─────────────────────────────────────────────────────────────

async function orchestrate(args, constraint, defense) {
  const authFlag = args.brand ? '-b' : '-s';
  const authId = args.brand || args.shop;
  const startTime = Date.now();
  // 深度合并默认参数：defaultParams 作为底，用户参数覆盖
  const params = mergeDefaults(constraint.defaultParams, JSON.parse(args.data));
  const validationErrors = validateParams(args.api, params, constraint, args);
  if (validationErrors.length) {
    return {
      api: args.api,
      rejected: true,
      reason: '参数结构校验失败',
      suggestion: buildParamSuggestion(validationErrors),
      fetchedAt: new Date().toISOString(),
      strategies: ['param-validate'],
      totalCalls: 0,
      totalRecords: 0,
      data: [],
      elapsedMs: Date.now() - startTime
    };
  }
  const strategies = [];
  const allData = [];
  const errors = [];

  // 获取dateRange（可能嵌套在 necessaryFilter 中，或平铺 startDate/endDate）
  const nesting = constraint.paramsNesting;
  const dateFieldMode = constraint.dateFieldMode || 'range';
  const dateRange = dateFieldMode === 'flat'
    ? (params.startDate && params.endDate ? { startDate: params.startDate, endDate: params.endDate } : null)
    : (nesting ? params[nesting]?.dateRange : params.dateRange);
  const shopIds = nesting ? params[nesting]?.shopIds : params.shopIds;

  // ─── 策略1: date-split ───
  let dateChunks = [dateRange];
  if (constraint.maxDateRangeDays && dateRange) {
    const days = daysBetween(dateRange.startDate, dateRange.endDate);
    if (days > constraint.maxDateRangeDays) {
      dateChunks = splitDateRange(dateRange.startDate, dateRange.endDate, constraint.maxDateRangeDays);
      strategies.push(`date-split(${dateChunks.length}chunks)`);
    }
  }

  // ─── 策略2: shop-batch ───
  let shopBatches = [shopIds];
  if (constraint.maxShopIds && Array.isArray(shopIds) && shopIds.length > constraint.maxShopIds) {
    shopBatches = splitShopIds(shopIds, constraint.maxShopIds);
    strategies.push(`shop-batch(${shopBatches.length}batches)`);
  }

  // ─── 组合执行 ───
  const tasks = [];

  for (const dateChunk of dateChunks) {
    for (const shopBatch of shopBatches) {
      tasks.push(() => rateLimitedCall(() => {
        // 超时兜底检查
        if (Date.now() - startTime > defense.timeout * 1000) {
          console.error(`[fetch] ❌ 执行超时（${defense.timeout}秒）`);
          return { rejected: true, reason: `执行超时（${defense.timeout}秒）`, suggestion: '建议缩小查询范围', data: [], totalRecords: 0 };
        }

        // 构建单次请求参数
        const callParams = JSON.parse(JSON.stringify(params));

        if (dateFieldMode === 'flat') {
          if (dateChunk) { callParams.startDate = dateChunk.startDate; callParams.endDate = dateChunk.endDate; }
          if (shopBatch) callParams.shopIds = shopBatch;
        } else if (nesting) {
          if (dateChunk) callParams[nesting].dateRange = dateChunk;
          if (shopBatch) callParams[nesting].shopIds = shopBatch;
        } else {
          if (dateChunk) callParams.dateRange = dateChunk;
          if (shopBatch) callParams.shopIds = shopBatch;
        }

        // 执行自动翻页
        return autoPage(args.api, authFlag, authId, callParams, constraint, defense);
      }));
    }
  }

  // ★ 主链路上报: 策略确定
  log.info(`编排策略确定`, { api: args.api, brandId: authId, strategies, dateChunks: dateChunks.length, shopBatches: shopBatches.length, totalTasks: tasks.length, dateRange, shopCount: Array.isArray(shopIds) ? shopIds.length : 1 });

  // ─── Tasks 预检：任务数超限直接拒绝 ───
  if (tasks.length > defense.maxTotalTasks) {
    const result = {
      api: args.api, rejected: true,
      reason: `查询范围过大：需${tasks.length}次API调用（上限${defense.maxTotalTasks}次）`,
      suggestion: buildSuggestion(tasks.length, defense, dateChunks, shopBatches, constraint),
      data: [], totalRecords: 0, totalCalls: 0,
      fetchedAt: new Date().toISOString(), strategies, elapsedMs: Date.now() - startTime
    };
    writeFileSync(args.output, JSON.stringify(result, null, 2), 'utf-8');
    // ★ 主链路上报: 预检拒绝
    log.warn(`预检拒绝：任务数超限`, { api: args.api, taskCount: tasks.length, maxTotalTasks: defense.maxTotalTasks });
    console.error(`[fetch] ❌ 预检拒绝: ${result.reason}`);
    console.error(`[fetch] 💡 建议: ${result.suggestion}`);
    process.exit(0);
  }

  // 是否需要翻页策略标记
  // (翻页在 autoPage 内部处理，此处只标记是否可能触发)

  // 并发执行所有任务
  const results = await concurrent(tasks, args.concurrency);

  // 合并结果
  let rejected = false;
  let rejectedReason = '';
  let rejectedSuggestion = '';
  let declaredTotal = 0;
  for (const r of results) {
    if (r.rejected) {
      rejected = true;
      rejectedReason = r.reason;
      rejectedSuggestion = r.suggestion;
      break;
    }
    if (r.data) allData.push(...r.data);
    if (r.declaredTotal) declaredTotal += r.declaredTotal;
    if (r.errors?.length) errors.push(...r.errors);
  }

  if (strategies.length === 0) strategies.push('direct');

  // 首页预检或超时拒绝
  if (rejected) {
    return {
      api: args.api, rejected: true,
      reason: rejectedReason, suggestion: rejectedSuggestion,
      fetchedAt: new Date().toISOString(), strategies,
      totalCalls: tasks.length, totalRecords: 0,
      data: [], elapsedMs: Date.now() - startTime
    };
  }

  return {
    api: args.api,
    rejected: false,
    fetchedAt: new Date().toISOString(),
    strategies,
    totalCalls: tasks.length,
    totalRecords: allData.length,
    declaredTotal,
    data: allData,
    elapsedMs: Date.now() - startTime,
    ...(errors.length > 0 ? { errors, coverage: `${tasks.length - errors.length}/${tasks.length}` } : {})
  };
}

// ─── 入口 ───────────────────────────────────────────────────────────────────

async function main() {
  const args = parseArgs(process.argv);
  const { apis, globalDefense } = loadConstraints();

  const isRegistered = Boolean(apis[args.api]);
  // 查找约束配置（未注册的接口视为无约束，直接调用）
  const constraint = isRegistered ? { ...apis[args.api], _registered: true } : {
    maxPageSize: 1000,
    maxDateRangeDays: null,
    maxShopIds: null,
    paramsNesting: null,
    mergeStrategy: 'concat-array',
    _registered: false
  };

  // 合并防护配置：接口级 defense 覆盖全局默认
  const defense = { ...globalDefense, ...(constraint.defense || {}) };

  // 提取业务上下文用于日志
  const authId = args.brand || args.shop;
  const parsedData = JSON.parse(args.data);
  const nesting = constraint.paramsNesting;
  const dateFieldMode = constraint.dateFieldMode || 'range';
  const dateRange = dateFieldMode === 'flat'
    ? (parsedData.startDate && parsedData.endDate ? { startDate: parsedData.startDate, endDate: parsedData.endDate } : undefined)
    : (nesting ? parsedData[nesting]?.dateRange : parsedData.dateRange);
  const shopIds = nesting ? parsedData[nesting]?.shopIds : parsedData.shopIds;
  const shopCount = Array.isArray(shopIds) ? shopIds.length : 1;

  // ★ 主链路上报: 启动
  log.info(`数据编排启动`, { api: args.api, brandId: authId, dateRange, shopCount, maxPageSize: constraint.maxPageSize, maxPages: defense.maxPages, maxRecords: defense.maxPages * constraint.maxPageSize, timeout: defense.timeout });
  console.error(`[fetch] API: ${args.api}`);
  console.error(`[fetch] 约束: maxDateRange=${constraint.maxDateRangeDays || '无限制'}天, maxShops=${constraint.maxShopIds || '无限制'}, maxPageSize=${constraint.maxPageSize}`);
  console.error(`[fetch] 防护: maxPages=${defense.maxPages}, maxRecords=${defense.maxPages * constraint.maxPageSize}条, maxTotalTasks=${defense.maxTotalTasks}, timeout=${defense.timeout}s`);

  const result = await orchestrate(args, constraint, defense);

  if (result.rejected) {
    // ★ 主链路上报: 编排结果-拒绝
    log.warn(`数据编排被拒绝`, { api: args.api, brandId: authId, dateRange, shopCount, reason: result.reason });
    console.error(`[fetch] ❌ 拒绝: ${result.reason}`);
    console.error(`[fetch] 💡 建议: ${result.suggestion}`);
  } else {
    // ★ 主链路上报: 编排结果-完成
    log.info(`数据编排完成`, { api: args.api, brandId: authId, dateRange, shopCount, strategies: result.strategies, totalCalls: result.totalCalls, totalRecords: result.totalRecords, declaredTotal: result.declaredTotal, elapsedMs: result.elapsedMs, hasErrors: result.errors?.length > 0 });
    console.error(`[fetch] ✅ 完成: strategies=${result.strategies.join(',')}, calls=${result.totalCalls}, records=${result.totalRecords}(declared=${result.declaredTotal}), elapsed=${result.elapsedMs}ms`);
    if (result.errors?.length) {
      console.error(`[fetch] ⚠ 部分失败: ${result.errors.length}次错误, coverage=${result.coverage}`);
    }
  }

  // 输出到文件
  writeFileSync(args.output, JSON.stringify(result, null, 2), 'utf-8');
  console.error(`[fetch] 输出: ${args.output}`);
}

// ─── 友好提示生成器 ────────────────────────────────────────────────────────

function buildSuggestion(taskCount, defense, dateChunks, shopBatches, constraint) {
  const parts = [];
  if (shopBatches && shopBatches.length > 3) {
    parts.push(`减少门店数量（当前${shopBatches.length}批×${constraint.maxShopIds || 50}店/批=${shopBatches.length * (constraint.maxShopIds || 50)}店）`);
  }
  if (dateChunks && dateChunks.length > 15) {
    parts.push(`缩短日期范围（当前${dateChunks.length}天）`);
  }
  if (!parts.length) parts.push('缩小查询范围');
  parts.push('给你带来不友好的体验，感到十分抱歉，数据性能我们正在持续优化中');
  return parts.join('；');
}

main().catch(err => {
  // ★ 主链路上报: 致命错误（开发者关注）
  log.error(`致命错误`, { err: err.message, stack: err.stack?.slice(0, 500), argv: process.argv.slice(2, 6) });
  console.error(`[fetch] 致命错误: ${err.message}`);
  process.exit(1);
});
