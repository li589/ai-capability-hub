#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

function arg(argv, name, fallback) {
  const idx = argv.indexOf(`--${name}`);
  return idx >= 0 ? argv[idx + 1] : fallback;
}

function hasFlag(argv, name) {
  return argv.includes(`--${name}`);
}

function shellQuote(value) {
  return `"${String(value).replace(/(["\\$`])/g, '\\$1')}"`;
}

function splitCommand(command) {
  const parts = [];
  let current = '';
  let inSingleQuote = false;
  let inDoubleQuote = false;
  for (let i = 0; i < command.length; i += 1) {
    const ch = command[i];
    if (ch === '\\' && i + 1 < command.length && (inSingleQuote || inDoubleQuote)) {
      current += command[i + 1];
      i += 1;
    } else if (ch === "'" && !inDoubleQuote) {
      inSingleQuote = !inSingleQuote;
    } else if (ch === '"' && !inSingleQuote) {
      inDoubleQuote = !inDoubleQuote;
    } else if (/\s/.test(ch) && !inSingleQuote && !inDoubleQuote) {
      if (current) {
        parts.push(current);
        current = '';
      }
    } else {
      current += ch;
    }
  }
  if (inSingleQuote || inDoubleQuote) throw new Error('命令参数引号不完整');
  if (current) parts.push(current);
  if (!parts.length) throw new Error('命令为空');
  return parts;
}
function findAgentRoot() {
  const starts = [process.cwd(), path.dirname(fs.realpathSync(process.argv[1] || __filename)), path.dirname(fs.realpathSync(__filename))];
  for (const start of starts) {
    let dir = path.resolve(start);
    for (;;) {
      if (fs.existsSync(path.join(dir, 'skills')) && fs.existsSync(path.join(dir, '.codebuddy-plugin', 'plugin.json'))) return dir;
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }
  return path.resolve(path.dirname(__filename), '../..');
}

function parseJson(text) {
  const source = String(text || '');
  for (let i = 0; i < source.length; i += 1) {
    if (source[i] !== '[' && source[i] !== '{') continue;
    try {
      return JSON.parse(source.slice(i));
    } catch {}
  }
  return null;
}

function rowToObject(row) {
  if (!Array.isArray(row)) return row || {};
  return row.reduce((acc, item) => {
    if (item && item.colName) {
      acc[item.colName] = item.value;
      const plainName = String(item.colName).replace(/^[a-zA-Z_][\w]*\./, '');
      if (plainName && acc[plainName] === undefined) acc[plainName] = item.value;
    }
    return acc;
  }, {});
}

function rows(payload) {
  if (Array.isArray(payload)) return payload.map(rowToObject);
  if (Array.isArray(payload?.data)) return payload.data.map(rowToObject);
  return [];
}

function num(value) {
  const n = Number(String(value ?? '0').replace(/,/g, ''));
  return Number.isFinite(n) ? n : 0;
}

function div(a, b) {
  return num(b) === 0 ? 0 : num(a) / num(b);
}

function dateOnly(value) {
  const m = String(value || '').match(/^(\d{4}-\d{2}-\d{2})/);
  return m ? m[1] : String(value || '');
}

function shanghaiTodayStart() {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(new Date());
  const values = Object.fromEntries(parts.map(item => [item.type, item.value]));
  return `${values.year}-${values.month}-${values.day} 00:00:00`;
}

function shiftDateTime(value, seconds) {
  const m = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2})$/);
  if (!m) return String(value || '');
  const date = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5]), Number(m[6])) + Number(seconds || 0) * 1000);
  const pad = number => String(number).padStart(2, '0');
  return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())}`;
}

function previousSecond(value) {
  return shiftDateTime(value, -1);
}

function addDays(value, days) {
  return shiftDateTime(value, Number(days || 0) * 86400);
}

function addYears(dateText, years) {
  const m = String(dateText || '').match(/^(\d{4})-(\d{2})-(\d{2})(.*)$/);
  return m ? `${Number(m[1]) + years}-${m[2]}-${m[3]}${m[4] || ' 00:00:00'}` : dateText;
}

function money(value) {
  return `¥${Math.round(num(value)).toLocaleString('zh-CN')}`;
}

function pct(value) {
  return `${(num(value) * 100).toFixed(1)}%`;
}

function businessPct(value) {
  const n = num(value);
  return `${(Math.abs(n) <= 1 ? n * 100 : n).toFixed(1)}%`;
}

function changeText(value, type) {
  const direction = String(type) === '1' ? '上升' : String(type) === '2' ? '下降' : '变化';
  return `较上一周期${direction} ${Math.abs(num(value)).toFixed(1)}%`;
}

function fmt(value, fallback = '-') {
  return value === undefined || value === null || value === '' ? fallback : String(value);
}

function maskPhone(value) {
  const digits = String(value || '').replace(/\D/g, '');
  return digits.length >= 7 ? `${digits.slice(0, 3)}****${digits.slice(-4)}` : '****';
}

function mask(name, mobile) {
  const phone = maskPhone(mobile);
  return `${fmt(name, '会员')}(${phone})`;
}

function run(command, cwd, timeoutMs = 120000) {
  const started = Date.now();
  return new Promise(resolve => {
    const [executable, ...commandArgs] = splitCommand(command);
    const child = spawn(executable, commandArgs, { shell: false, cwd, env: process.env });
    let stdout = '';
    let stderr = '';
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
    }, timeoutMs);
    child.stdout.on('data', buf => { stdout += buf.toString(); });
    child.stderr.on('data', buf => { stderr += buf.toString(); });
    child.on('close', (code, signal) => {
      clearTimeout(timer);
      resolve({ command, code, signal, timedOut, elapsedMs: Date.now() - started, stdout, stderr });
    });
  });
}

async function datacube(agentRoot, name, taskId, exeTaskId, params = {}, timeoutMs = 120000) {
  const parts = [`sl datacube task-${taskId}`, '--format json', '--raw', '--exeTaskId', shellQuote(exeTaskId)];
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') parts.push(`--${key}`, shellQuote(value));
  }
  const command = parts.join(' ');
  const res = await run(command, agentRoot, timeoutMs);
  const parsed = parseJson(res.stdout || res.stderr);
  return {
    name,
    command,
    elapsedMs: res.elapsedMs,
    exitCode: res.code,
    timedOut: res.timedOut,
    rowCount: rows(parsed).length,
    rows: rows(parsed),
    error: res.code !== 0 || !parsed ? (res.stderr || res.stdout).slice(0, 1000) : null,
  };
}

async function scriptJson(agentRoot, name, command, timeoutMs = 180000) {
  const res = await run(command, agentRoot, timeoutMs);
  const parsed = parseJson(res.stdout || res.stderr);
  return {
    name,
    command,
    elapsedMs: res.elapsedMs,
    exitCode: res.code,
    timedOut: res.timedOut,
    data: parsed || {},
    error: res.code !== 0 || !parsed ? (res.stderr || res.stdout).slice(0, 1000) : null,
  };
}

function metric(label, value, sub = '') {
  return { label, value: fmt(value), sub: fmt(sub, '') };
}

function keywordExtract(list, good) {
  const counts = new Map();
  for (const item of list || []) {
    const star = num(item.star);
    if (star <= 0) continue;
    if (good && star < 4) continue;
    if (!good && star > 2) continue;
    const text = [item.tips, item.question_name, item.answer_value, item.remark].filter(Boolean).join(' ');
    for (const token of text.split(/[,\s，。；;、|/]+/).map(x => x.trim()).filter(x => x.length >= 2 && x.length <= 8)) {
      counts.set(token, (counts.get(token) || 0) + 1);
    }
  }
  return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k]) => k);
}

function rfmSuggestion(name) {
  if (String(name).includes('重点挽留')) return '短效唤醒券 + 店长企微回访';
  if (String(name).includes('重点保持')) return '新品权益 + 会员日提醒';
  if (String(name).includes('一般挽留')) return '低门槛回店券';
  return '节假日前触达';
}

function generalResult(batch, name) {
  const query = batch?.queries?.[name];
  if (!query || query.status !== 'ok') return null;
  return query.data?.data || query.data || null;
}

function compactProbe(probe, fallbackName) {
  return {
    name: probe?.name || fallbackName || '数据模块',
    elapsedMs: num(probe?.elapsedMs),
    rowCount: num(probe?.rowCount),
    error: probe?.error || null,
  };
}

async function buildSection(section, args, agentRoot) {
  const common = { startDate: args.startDate, endDate: args.endDate };
  if (args.omShopCodes) common.omShopCodes = args.omShopCodes;
  const topN = Number(args.topN || 5);

  if (section === 'recharge') {
    const [newRecharge, renewRecharge, oldBase] = await Promise.all([
      datacube(agentRoot, '新会员储值转化统计', '260509114426001383', '260509114426000957', common),
      datacube(agentRoot, '会员储值转化统计', '260430101252001360', '260430101252000936', common),
      datacube(agentRoot, '历史已有储值老会员基数', '260508141725001380', '260508141725000955', { startDate: args.startDate, omShopCodes: args.omShopCodes }),
    ]);
    const n = newRecharge.rows[0] || {};
    const r = renewRecharge.rows[0] || {};
    const o = oldBase.rows[0] || {};
    const renewCount = num(r.renew_recharge_user_count || r.renew_recharge_count);
    const oldCount = num(o.old_recharge_member_count);
    const avg = div(num(r.recharge_principal_amount || r.recharge_total_amount), num(r.recharge_user_count || r.recharge_count));
    return {
      title: '储值转化率分析',
      color: '#22a878',
      metrics: [
        metric('新会员消费人数', num(n.new_member_count), '统计周期首次消费'),
        metric('新会员储值转化', pct(n.new_member_recharge_rate), `${num(n.new_member_recharge_count)} 人完成首充`),
        metric('老会员续充率', pct(div(renewCount, oldCount)), `${renewCount} / ${oldCount} 人`),
        metric('平均首充金额', money(avg), '储值本金'),
      ],
      note: `新会员储值转化率 ${pct(n.new_member_recharge_rate)}，老会员续充率 ${pct(div(renewCount, oldCount))}。`,
      probes: [newRecharge, renewRecharge, oldBase],
    };
  }

  if (section === 'high-value') {
    const top = await datacube(agentRoot, '时段会员消费TOP5', '260430143537001363', '260430143537000939', { ...common, topN });
    const members = top.rows;
    const memberCodeCsv = members.map(m => m.mem_code).filter(Boolean).join(',');
    const [pref, balance] = memberCodeCsv ? await Promise.all([
      datacube(agentRoot, '会员历史消费偏好', '260430144548001364', '260430144548000940', { memberCodeCsv, historyStartDate: addYears(args.startDate, -1), endDate: args.endDate, limit: Math.max(topN * 50, 100) }),
      datacube(agentRoot, '会员卡余额明细', '260422113503001295', '260422113503000876', { memberCodeCsv, limit: 50 }),
    ]) : [{ rows: [], name: '会员历史消费偏好' }, { rows: [], name: '会员卡余额明细' }];
    const prefByMember = {};
    for (const item of pref.rows || []) {
      const code = String(item.mem_code || '');
      if (!code) continue;
      if (!prefByMember[code]) prefByMember[code] = [];
      const name = item.dish_name || item.item_name || item.food_name || item.category_name || item.menu_name;
      if (name && !prefByMember[code].includes(name)) prefByMember[code].push(name);
    }
    const balanceByMember = {};
    for (const item of balance.rows || []) {
      const code = String(item.mem_code || '');
      if (!code) continue;
      balanceByMember[code] = item;
    }
    return {
      title: '高净值会员画像 · TOP 5',
      color: '#b66a13',
      metrics: [
        metric('TOP会员数', members.length, '按本期消费排序'),
        metric('TOP消费合计', money(members.reduce((s, m) => s + num(m.consume_bill_amount), 0)), '本期'),
        metric('最高消费', money(Math.max(0, ...members.map(m => num(m.consume_bill_amount)))), '单会员'),
        metric('总账单数', members.reduce((s, m) => s + num(m.bill_count), 0), 'TOP合计'),
      ],
      tableHeaders: ['会员', '本期消费', '本期账单', '余额/历史', '消费偏好', '回访建议'],
      tableRows: members.map(m => [
        mask(m.mem_name, m.mem_mobile),
        money(m.consume_bill_amount),
        num(m.bill_count),
        money(balanceByMember[m.mem_code]?.balance_total || balanceByMember[m.mem_code]?.card_balance),
        (prefByMember[m.mem_code] || []).slice(0, 3).join('、') || '-',
        num(m.consume_bill_amount) >= 5000 ? '发专享新品' : num(m.bill_count) >= 5 ? '定制高频套餐' : '专属回访',
      ]),
      probes: [top, pref, balance].filter(Boolean),
    };
  }

  if (section === 'review') {
    const [stat, detail] = await Promise.all([
      datacube(agentRoot, '吾享评价统计', '260430165130001365', '260430165130000941', common),
      datacube(agentRoot, '吾享评价明细', '260430172204001367', '260430172204000943', { ...common, limit: Number(args.limit || 80) }),
    ]);
    const s = stat.rows[0] || {};
    const badSamples = detail.rows.filter(x => {
      const star = num(x.star);
      const closed = String(x.closed_loop_state || '');
      return (star > 0 && star <= 2) || (star > 0 && closed && closed !== '2');
    }).slice(0, 4);
    return {
      title: '评价分析',
      color: '#d5652d',
      metrics: [
        metric('评价数', num(s.review_count), '周期内'),
        metric('平均评分', num(s.avg_star).toFixed(1), '满分 5'),
        metric('好评', num(s.good_review_count), pct(div(s.good_review_count, s.review_count))),
        metric('差评', num(s.bad_review_count), pct(div(s.bad_review_count, s.review_count))),
      ],
      chips: [
        { title: '差评关键词', values: keywordExtract(detail.rows, false) },
        { title: '好评共性', values: keywordExtract(detail.rows, true) },
      ],
      tableHeaders: ['待处理评价', '星级'],
      tableRows: badSamples.map(x => [fmt(x.answer_value || x.value || x.remark || x.question_name), `${fmt(x.star)}星`]),
      probes: [stat, detail],
    };
  }

  if (section === 'rfm') {
    const rfm = await datacube(agentRoot, 'RFM分群汇总', '260511101241001391', '260511101241000965', {
      endDate: args.endDate,
      lostDays: args.lostDays || 60,
      rfmHistoryDays: args.rfmHistoryDays || 365,
      highValueAmount: args.highValueAmount || 1000,
      highFrequencyCount: args.highFrequencyCount || 5,
      omShopCodes: args.omShopCodes,
    });
    const rows = rfm.rows;
    return {
      title: '复购会员 RFM 分析 · 营销建议',
      color: '#7a64e8',
      metrics: rows.slice(0, 4).map(s => metric(s.rfm_segment || '分组', `${num(s.member_count)}人`, `有余额 ${num(s.balance_member_count)} 人`)),
      tableHeaders: ['分组', '会员数', '有余额', '平均未到店', '建议'],
      tableRows: rows.map(s => [fmt(s.rfm_segment), num(s.member_count), num(s.balance_member_count), `${fmt(s.avg_days_since_last_consume)}天`, rfmSuggestion(s.rfm_segment)]),
      note: rows.length ? `${fmt(rows[0].rfm_segment, '重点分组')} ${num(rows[0].member_count)} 人，其中有余额 ${num(rows[0].balance_member_count)} 人。` : 'RFM 汇总暂无数据。',
      probes: [rfm],
    };
  }

  if (section === 'repurchase-report') {
    const displayEndDate = previousSecond(args.endDate);
    const preBeginDate = addDays(args.startDate, -7);
    const preEndDate = previousSecond(args.startDate);
    let repurchaseCommand = `node skills/会员-消费行为分析/scripts/batch_repurchase_metrics.mjs --beginDate ${shellQuote(args.startDate)} --endDate ${shellQuote(displayEndDate)} --preBeginDate ${shellQuote(preBeginDate)} --preEndDate ${shellQuote(preEndDate)}`;
    if (args.shopFilterTypeValue) repurchaseCommand += ` --shopFilterTypeValue ${shellQuote(args.shopFilterTypeValue)}`;

    const rfmParams = {
      endDate: args.endDate,
      lostDays: args.lostDays || 60,
      rfmHistoryDays: args.rfmHistoryDays || 365,
      highValueAmount: args.highValueAmount || 1000,
      highFrequencyCount: args.highFrequencyCount || 5,
      omShopCodes: args.omShopCodes,
    };
    const healthParams = { startDate: args.startDate, endDate: args.endDate };
    if (args.omShopCodes) healthParams.omShopCodes = args.omShopCodes;

    const [repurchaseBatch, rfm, ...health] = await Promise.all([
      scriptJson(agentRoot, '复购核心指标', repurchaseCommand, 60000),
      datacube(agentRoot, 'RFM分类', '260511101241001391', '260511101241000965', rfmParams, 60000),
      ...[21, 60, 90].map(days => datacube(agentRoot, `${days}天复购健康度`, '260506152653001371', '260506152653000946', { ...healthParams, periodDays: days }, 60000)),
    ]);

    const batch = repurchaseBatch.data || {};
    const core = generalResult(batch, '复购核心指标');
    const frequency = generalResult(batch, '复购次数分布');
    const rfmRows = rfm.rows || [];
    const leadingSegment = [...rfmRows].sort((a, b) => num(b.member_count) - num(a.member_count))[0] || null;
    const healthRows = health.map((probe, index) => ({
      periodDays: [21, 60, 90][index],
      available: !probe.error && probe.rows.length > 0,
      row: probe.rows[0] || {},
    }));

    const batchProbes = Object.values(batch.queries || {}).map(query => compactProbe(query));
    if (!batchProbes.length) batchProbes.push(compactProbe(repurchaseBatch, '复购核心指标'));
    const probes = [
      ...batchProbes,
      compactProbe(rfm, 'RFM分类'),
      ...health.map((probe, index) => compactProbe(probe, `${[21, 60, 90][index]}天复购健康度`)),
    ];

    const repurchaseSummary = core ? {
      consumeMemberCount: num(core.consumeMemberCount),
      repurchaseMemberCount: num(core.twiceConsumeMemberCount),
      repurchaseRatio: businessPct(core.twiceConsumeMemberRatio),
      previousPeriodChange: changeText(core.twiceFloatRangeValue, core.twiceFloatRangeType),
    } : null;
    const rfmSummary = rfmRows.map(row => ({
      segment: fmt(row.rfm_segment),
      memberCount: num(row.member_count),
      balanceMemberCount: num(row.balance_member_count),
      averageDaysSinceLastConsume: num(row.avg_days_since_last_consume),
      suggestion: rfmSuggestion(row.rfm_segment),
    }));
    const healthSummary = healthRows.filter(item => item.available).map(item => ({
      periodDays: item.periodDays,
      repurchaseRate: pct(item.row.repurchase_rate),
      repurchaseMemberCount: num(item.row.repurchase_member_count),
      consumeMemberCount: num(item.row.consume_member_count),
      averageRepurchaseCount: num(item.row.avg_repurchase_count),
    }));

    const conclusionParts = [];
    if (repurchaseSummary) conclusionParts.push(`本期复购占比 ${repurchaseSummary.repurchaseRatio}，${repurchaseSummary.previousPeriodChange}`);
    if (leadingSegment) conclusionParts.push(`数量最多的 RFM 类别是“${fmt(leadingSegment.rfm_segment)}”，共 ${num(leadingSegment.member_count)} 人`);
    if (!conclusionParts.length) conclusionParts.push('报告已生成，但本次暂未取得可用的复购核心指标和 RFM 分类结果');

    return {
      title: '会员复购会员分析报告',
      color: '#6d5bd0',
      period: { startDate: args.startDate, endDate: args.endDate, displayEndDate, label: `${args.startDate} 至 ${displayEndDate}` },
      metrics: [
        metric('消费会员', repurchaseSummary ? `${repurchaseSummary.consumeMemberCount}人` : '暂未取得', '最近7个完整自然日'),
        metric('复购会员', repurchaseSummary ? `${repurchaseSummary.repurchaseMemberCount}人` : '暂未取得', '消费2次及以上'),
        metric('复购占比', repurchaseSummary?.repurchaseRatio || '暂未取得', repurchaseSummary?.previousPeriodChange || '上周期对比暂不可用'),
        metric('最大RFM群体', leadingSegment ? fmt(leadingSegment.rfm_segment) : '暂未取得', leadingSegment ? `${num(leadingSegment.member_count)}人` : '分类结果暂不可用'),
      ],
      chips: [
        { title: '21/60/90天复购健康度', values: healthSummary.map(item => `${item.periodDays}天 ${item.repurchaseRate}`) },
        { title: '复购次数分布', values: Array.isArray(frequency?.frequencyList) && Array.isArray(frequency?.countList) ? frequency.frequencyList.map((label, index) => `${label} ${num(frequency.countList[index])}人`) : [] },
      ],
      tableHeaders: ['RFM类别', '会员数', '有余额', '平均未到店', '建议'],
      tableRows: rfmRows.map(row => [fmt(row.rfm_segment), `${num(row.member_count)}人`, `${num(row.balance_member_count)}人`, `${fmt(row.avg_days_since_last_consume)}天`, rfmSuggestion(row.rfm_segment)]),
      note: `${conclusionParts.join('；')}。`,
      businessSummary: {
        period: `${args.startDate} 至 ${displayEndDate}`,
        conclusion: conclusionParts.join('；'),
        repurchase: repurchaseSummary,
        rfm: rfmSummary,
        health: healthSummary,
        unavailableModules: probes.filter(probe => probe.error).map(probe => probe.name),
      },
      probes,
    };
  }

  if (section === 'growth') {
    const command = `node skills/会员-增长与生命周期/scripts/member_growth_opportunity_pipeline.js --startDate ${shellQuote(args.startDate)} --endDate ${shellQuote(args.endDate)} --orderLimit ${Number(args.orderLimit || 200)} --memberLookupLimit ${Number(args.memberLookupLimit || 50)} --memberLookupConcurrency 8 --topN ${topN}`;
    const result = await scriptJson(agentRoot, '会员发展建议脚本', command, 180000);
    const summary = result.data.online_lead_summary || {};
    return {
      title: '会员发展建议 · 潜客识别',
      color: '#63a934',
      metrics: [
        metric('高消费未开卡', num(summary.high_value_unregistered_phone_count), '已检索手机号范围'),
        metric('扫码点餐留档', num(summary.distinct_phone_count), '线上手机号'),
        metric('已确认会员', num(summary.registered_phone_count), '手机号匹配'),
        metric('可回访潜客', num(summary.unregistered_phone_count), '未注册'),
      ],
      tableHeaders: ['潜客手机号', '消费金额', '订单数', '最近消费'],
      tableRows: (result.data.top_unregistered || []).slice(0, 5).map(x => [maskPhone(x.phone_masked || x.phone), money(x.total_order_amount), num(x.order_count), fmt(x.latest_order_time)]),
      note: `${num(summary.high_value_unregistered_phone_count)} 名高消费线上潜客暂未匹配会员，可优先引导开卡并沉淀企微。`,
      probes: [result],
    };
  }

  if (section === 'repurchase-health') {
    const periods = await Promise.all([21, 60, 90].map(days => datacube(agentRoot, `${days}天复购率`, '260506152653001371', '260506152653000946', { ...common, periodDays: days })));
    const normalized = periods.map((p, idx) => ({ periodDays: [21, 60, 90][idx], row: p.rows[0] || {}, hasData: p.rows.length > 0 }));
    return {
      title: '复购健康度分析',
      color: '#d84f8c',
      metrics: normalized.map(p => metric(`${p.periodDays}天复购率`, p.hasData ? pct(p.row.repurchase_rate) : '暂无数据', p.hasData ? `平均频次 ${fmt(p.row.avg_repurchase_count)}` : '当前条件无返回')),
      note: normalized.some(p => p.hasData)
        ? `按截止日向前回看，${normalized.map(p => p.hasData ? `${p.periodDays}天 ${pct(p.row.repurchase_rate)}` : `${p.periodDays}天暂无数据`).join('、')}。`
        : '复购健康度暂无数据。',
      probes: periods,
    };
  }

  if (section === 'action-feedback') {
    const command = `node skills/会员-营销活动/scripts/marketing_activity_effect_pipeline.js --startDate ${shellQuote(args.startDate)} --endDate ${shellQuote(args.endDate)} --topN ${Number(args.topN || 10)}`;
    const result = await scriptJson(agentRoot, '营销活动效果统计脚本', command, 180000);
    const s = result.data.summary || {};
    const activities = result.data.activities || [];
    return {
      title: '行动反馈 · 昨日营销活动效果',
      color: '#78806d',
      metrics: [
        metric('触达', num(s.total_touched), '人'),
        metric('领券', num(s.total_receive_coupon), '人'),
        metric('核销', num(s.total_used_coupon), '人'),
        metric('贡献金额', money(s.total_contribution_consume_amount), '活动级'),
      ],
      tableHeaders: ['活动', '触达', '领券', '核销', '贡献'],
      tableRows: activities.slice(0, 6).map(x => [fmt(x.campaign_name), num(x.touched_member_count), num(x.receive_coupon_member_count), num(x.used_coupon_member_count), money(x.contribution_consume_amount)]),
      note: '当前为活动级反馈，不等同于 AI 建议名单精确反馈。',
      probes: [result],
    };
  }

  throw new Error(`未知 section: ${section}`);
}

function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}

function renderHtml(report) {
  const metrics = (report.metrics || []).map(m => `
    <div class="metric"><div class="label">${esc(m.label)}</div><div class="value">${esc(m.value)}</div><div class="sub">${esc(m.sub)}</div></div>`).join('');
  const chips = (report.chips || []).map(g => `
    <div class="chip-group"><b>${esc(g.title)}</b><div>${(g.values || []).map(v => `<span class="tag">${esc(v)}</span>`).join('') || '<span class="small">暂无</span>'}</div></div>`).join('');
  const table = report.tableHeaders ? `
    <table><thead><tr>${report.tableHeaders.map(h => `<th>${esc(h)}</th>`).join('')}</tr></thead><tbody>
      ${(report.tableRows || []).map(row => `<tr>${row.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${report.tableHeaders.length}">暂无明细</td></tr>`}
    </tbody></table>` : '';
  return `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(report.title)}</title>
<style>
:root{--bg:#f7f8fa;--card:#fff;--ink:#111827;--muted:#667085;--line:#d9dee7;--soft:#f3f1eb;--blue:#2f80ed}
*{box-sizing:border-box}html,body{margin:0;width:max-content;min-width:0;background:var(--bg)}body{color:var(--ink);font:18px/1.42 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif}
.wrap{width:1040px;padding:20px 24px}.card{background:#fff;border:1.5px solid var(--line);border-radius:16px;padding:28px 30px;box-shadow:0 1px 0 rgba(17,24,39,.03)}
.title{display:flex;align-items:center;gap:10px;margin:0 0 22px;font-size:26px;font-weight:850;color:#354052}.dot{width:12px;height:12px;border-radius:50%;background:${esc(report.color || '#2f80ed')}}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-bottom:22px}.metric{min-height:108px;padding:18px 20px;background:var(--soft);border-radius:12px}
.label{color:#414957;font-size:17px;margin-bottom:6px}.value{font-size:30px;line-height:1.08;font-weight:850}.sub{color:var(--muted);font-size:15px;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:15px}th,td{text-align:left;border-bottom:1px solid var(--line);padding:8px 7px;vertical-align:top}th{color:#475467;font-weight:800}
.note{margin:18px 0 0;color:#565c67;font-size:18px;font-weight:700}.chip-group{margin:0 0 12px}.tag{display:inline-block;border-radius:6px;padding:3px 8px;background:#e8f4ff;color:#1f6eb3;font-size:14px;margin:4px 5px 0 0}.small{color:var(--muted)}
</style></head><body><main class="wrap"><section class="card">
<h1 class="title"><span class="dot"></span>${esc(report.title)}</h1>
<div class="metrics">${metrics}</div>${chips}${table}<p class="note">${esc(report.note || `统计周期：${report.period?.label || ''}`)}</p>
</section></main></body></html>`;
}

function screenshotSize(report) {
  const rowCount = Math.max((report.tableRows || []).length, report.tableHeaders ? 1 : 0);
  const chipGroups = (report.chips || []).length;
  const metricRows = Math.ceil(Math.max((report.metrics || []).length, 1) / 4);
  const height = 40 + 58 + metricRows * 130 + chipGroups * 54 + rowCount * 38 + (report.note ? 56 : 28);
  return {
    width: 1040,
    height: Math.min(Math.max(height, 330), 900),
  };
}

async function screenshot(htmlFile, pngFile, agentRoot, report) {
  const candidates = ['google-chrome', 'chromium', 'chromium-browser', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'];
  let chrome = null;
  for (const bin of candidates) {
    if (path.isAbsolute(bin) && fs.existsSync(bin)) {
      chrome = bin;
      break;
    }
    const probe = spawnSync(bin, ['--version'], { encoding: 'utf8' });
    if (probe.status === 0) {
      chrome = bin;
      break;
    }
  }
  if (!chrome) return { ok: false, error: '未找到 Chrome/Chromium，无法生成 PNG' };
  const userDataDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'member-section-shot-'));
  const size = screenshotSize(report || {});
  const args = ['--headless=new', '--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage', '--hide-scrollbars', `--user-data-dir=${userDataDir}`, `--window-size=${size.width},${size.height}`, `--screenshot=${pngFile}`, `file://${htmlFile}`];
  const started = Date.now();
  const res = spawnSync(chrome, args, { cwd: agentRoot, encoding: 'utf8', timeout: 60000 });
  fs.rmSync(userDataDir, { recursive: true, force: true });
  const ok = fs.existsSync(pngFile) && fs.statSync(pngFile).size > 0;
  return { ok, elapsedMs: Date.now() - started, width: size.width, height: size.height, command: [shellQuote(chrome), ...args.map(shellQuote)].join(' '), error: ok ? null : String(res.stderr || res.stdout || res.error?.message || '截图失败').slice(0, 500) };
}

async function main(defaultSection) {
  const argv = process.argv.slice(2);
  const section = arg(argv, 'section', defaultSection);
  if (!section) throw new Error('Usage: render card script --startDate "yyyy-MM-dd HH:mm:ss" --endDate "yyyy-MM-dd HH:mm:ss"');
  let startDate = arg(argv, 'startDate', null);
  const requestedEndDate = arg(argv, 'endDate', null);
  const endDate = requestedEndDate === 'auto' ? shanghaiTodayStart() : requestedEndDate;
  const dataFile = arg(argv, 'dataFile', null);
  const autoEndSections = new Set(['rfm', 'repurchase-report']);
  if (!dataFile && autoEndSections.has(section) && !endDate) throw new Error(`${section} 缺少 --endDate`);
  if (!dataFile && autoEndSections.has(section) && !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(endDate)) throw new Error(`${section} 的 --endDate 必须是 yyyy-MM-dd HH:mm:ss`);
  if (!dataFile && section === 'repurchase-report' && !startDate) startDate = addDays(endDate, -7);
  if (!dataFile && section === 'repurchase-report' && !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(startDate)) throw new Error('repurchase-report 的 --startDate 必须是 yyyy-MM-dd HH:mm:ss');
  if (!dataFile && !autoEndSections.has(section) && (!startDate || !endDate)) throw new Error('缺少 --startDate/--endDate');
  const agentRoot = findAgentRoot();
  const outDirArg = arg(argv, 'outDir', `${section}-card-runs`);
  const outDir = path.isAbsolute(outDirArg) ? outDirArg : path.resolve(agentRoot, outDirArg);
  fs.mkdirSync(outDir, { recursive: true });
  const args = Object.fromEntries(['startDate', 'endDate', 'omShopCodes', 'shopFilterTypeValue', 'topN', 'limit', 'lostDays', 'rfmHistoryDays', 'highValueAmount', 'highFrequencyCount', 'orderLimit', 'memberLookupLimit'].map(k => [k, arg(argv, k, null)]));
  args.startDate = startDate;
  args.endDate = endDate;

  const report = dataFile ? JSON.parse(fs.readFileSync(path.resolve(dataFile), 'utf8')) : await buildSection(section, args, agentRoot);
  report.generatedAt = new Date().toISOString();
  if (!report.period && section === 'rfm') {
    const displayEndDate = previousSecond(endDate);
    report.period = { displayEndDate, label: `截至 ${displayEndDate}` };
  } else {
    report.period = report.period || { startDate, endDate, label: `${dateOnly(startDate)} - ${dateOnly(endDate)}` };
  }
  report.coverage = { gaps: (report.probes || []).filter(p => p.error).map(p => ({ module: p.name, reason: '命令失败或 JSON 解析失败', detail: p.error })) };

  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const runId = `${section}-${dateOnly(startDate || 'from-data')}_${dateOnly(endDate || '')}_${stamp}`.replace(/[^0-9A-Za-z\u4e00-\u9fa5_-]+/g, '-');
  const jsonFile = path.join(outDir, `${runId}.json`);
  const htmlFile = path.join(outDir, `${runId}.html`);
  const pngFile = path.join(outDir, `${runId}.png`);
  const relativeHtmlFile = path.relative(agentRoot, htmlFile).split(path.sep).join('/');
  const reportLinkMarkdown = `打开完整复购分析报告（通过 WorkBuddy 文件附件返回）`;
  report.artifacts = { dataFile: jsonFile, htmlFile, imageFile: pngFile, pngFile };
  fs.writeFileSync(htmlFile, renderHtml(report));
  if (!hasFlag(argv, 'noScreenshot')) report.screenshot = await screenshot(htmlFile, pngFile, agentRoot, report);
  fs.writeFileSync(jsonFile, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify({ status: 'ok', section, dataFile: jsonFile, htmlFile, imageFile: pngFile, pngFile, reportLinkMarkdown, screenshot: report.screenshot || null, gapCount: report.coverage.gaps.length, businessSummary: report.businessSummary || null }, null, 2));
}

main("repurchase-health").catch(err => {
  console.error(err.stack || err.message);
  process.exit(1);
});
