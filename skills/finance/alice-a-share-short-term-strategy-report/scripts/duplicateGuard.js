// 重复提交防护：检测 Agent 换 prompt 重试导致的"多次新建任务"。
//
// 触发场景（现场已多次出现）：
//   1) Agent 第一次发 `--prompt "生成今日 A 股短线策略报告"`，被沙箱杀进程；
//   2) 误判失败 → 改短 prompt `--prompt "帮我复盘今天的 A 股市场"`，再次新建任务；
//   3) 服务端因此并发跑两条几乎相同的任务，浪费额度且 Agent 拿不到稳定结果。
//
// 解决思路：新建任务前，遍历 N 分钟（默认 10min）内的 running 记录，对比 prompt
// 是否"实质相同"。命中即拒绝提交并引导 Agent 改用 --no-wait 续接 / --new 强制。
//
// 本模块完全 pure（不依赖文件系统 / 网络），便于单测覆盖各种相似形态。

/** 最小可比较长度：避免极短 prompt 误判（"分析" 这种 2 字命中所有任务）。 */
const MIN_LEN_FOR_COMPARE = 8;

/** Jaccard 相似度阈值：bigram 集合的 |A∩B|/|A∪B| ≥ 该值视为相似。 */
const JACCARD_THRESHOLD = 0.7;

/** 默认相似度检查时间窗口（毫秒）。 */
export const DEFAULT_DUPLICATE_GUARD_WINDOW_MS = 10 * 60 * 1000;

/** check-conflict 对 completed 任务的「可重放」检查窗口（毫秒）。 */
export const DEFAULT_REPLAY_GUARD_WINDOW_MS = 24 * 60 * 60 * 1000;

/** trim + 折叠所有连续空白为单空格；与 computePromptHash 的归一化保持一致。 */
export function normalizePromptForGuard(value) {
  return String(value ?? "").trim().replace(/\s+/g, " ");
}

/** 把字符串拆成字符 bigram 集合；中英文混合 prompt 都按字符级处理。 */
function buildBigrams(text) {
  const set = new Set();
  const len = text.length;
  if (len === 0) return set;
  if (len === 1) {
    set.add(text);
    return set;
  }
  for (let i = 0; i < len - 1; i++) {
    set.add(text.slice(i, i + 2));
  }
  return set;
}

function jaccardSimilarity(a, b) {
  if (a.size === 0 && b.size === 0) return 0;
  const [small, large] = a.size <= b.size ? [a, b] : [b, a];
  let inter = 0;
  for (const token of small) {
    if (large.has(token)) inter += 1;
  }
  const union = a.size + b.size - inter;
  return union === 0 ? 0 : inter / union;
}

/**
 * 对两个 normalized prompt 做相似度判定。
 *
 * @param {string} a normalized prompt（调用方应先用 normalizePromptForGuard 处理）
 * @param {string} b normalized prompt
 * @returns {{kind: "identical"|"prefix"|"contained"|"jaccard"|"none", score: number}}
 */
export function compareNormalizedPrompts(a, b) {
  if (typeof a !== "string" || typeof b !== "string") {
    return { kind: "none", score: 0 };
  }
  if (a === b) {
    return { kind: "identical", score: 1 };
  }
  const longer = a.length >= b.length ? a : b;
  const shorter = a.length >= b.length ? b : a;
  if (shorter.length < MIN_LEN_FOR_COMPARE) {
    return { kind: "none", score: 0 };
  }
  if (longer.startsWith(shorter)) {
    return { kind: "prefix", score: 1 };
  }
  if (longer.includes(shorter)) {
    return { kind: "contained", score: 1 };
  }
  const score = jaccardSimilarity(buildBigrams(a), buildBigrams(b));
  if (score >= JACCARD_THRESHOLD) {
    return { kind: "jaccard", score };
  }
  return { kind: "none", score };
}

/** A股短线策略报告 replay 预检用的通用词（不作为主体 token）。 */
const REPLAY_SUBJECT_STOPWORDS = new Set([
  "A股",
  "短线",
  "策略",
  "报告",
  "涨停",
  "涨停板",
  "收盘",
  "综述",
  "复盘",
  "市场",
  "主线",
  "热点",
  "概念",
  "板块",
  "轮动",
  "行业",
  "资金",
  "流向",
  "涨跌停",
  "指数",
  "成交额",
  "生成",
  "查看",
  "今日",
  "今天",
  "最近",
  "最新",
  "帮我",
  "给我一份",
  "给我做一份",
  "帮我做一份",
  "帮我生成",
  "出一份",
  "的",
  "了",
  "做",
  "给",
  "帮",
  "看",
  "出",
  "一份",
  "下",
  "A股短线策略报告",
  "短线策略报告",
  "涨停板分析报告",
  "涨停板复盘",
]);

/** trim + 折叠空白，并将 "A 股" 规范为 "A股"（Agent 措辞常见）。 */
function normalizeAshareIntentText(text) {
  return normalizePromptForGuard(text).replace(/A\s*股/g, "A股");
}

/**
 * 提取交易日标识（用于主体锁区分不同期次）。
 * @param {string} text
 * @returns {string|null}
 */
export function extractTradingDate(text) {
  const t = normalizeAshareIntentText(text);
  const ymd = t.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (ymd) {
    return `${ymd[1]}-${ymd[2].padStart(2, "0")}-${ymd[3].padStart(2, "0")}`;
  }
  const md = t.match(/(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (md) {
    const year = new Date().getFullYear();
    return `${year}-${md[1].padStart(2, "0")}-${md[2].padStart(2, "0")}`;
  }
  if (/今天|今日|盘后|当日/.test(t)) return "latest";
  if (/昨天|昨日/.test(t)) return "previous-trading-day";
  if (/最近|最新|近期/.test(t)) return "latest";
  return null;
}

function hasShortTermStrategyReportIntent(text) {
  const t = normalizeAshareIntentText(text);
  if (
    /A股短线策略报告|短线策略报告|涨停板分析|涨停板复盘|收盘综述|涨停板.*热点|市场主线|板块方向|A股日报/.test(
      t,
    )
  ) {
    return true;
  }
  if (/A股|沪深/.test(t)) {
    return /短线|涨停|收盘|复盘|板块|轮动|主线|热点|概念|策略|报告|涨跌停|资金.*方向|市场.*主线/.test(
      t,
    );
  }
  return /涨停|涨跌停|板块轮动|市场主线|热点概念|短线策略/.test(t) && /市场|A股|沪深|短线/.test(t);
}

/**
 * 从 A股短线策略报告 prompt 提取稳定的主体键（交易日，跨措辞 submit 锁 / 调度续接用）。
 * 返回 null 表示无法可靠提取（如非本技能意图）。
 *
 * @param {string} prompt
 * @returns {string|null}
 */
export function computeSubjectKey(prompt) {
  const normalized = normalizeAshareIntentText(prompt);
  if (!normalized || !hasShortTermStrategyReportIntent(normalized)) return null;

  const date = extractTradingDate(normalized) || "latest";
  return `a-share-short-term:${date}`;
}

/**
 * completed 任务 replay 预检用的相似度（比 running 防护略宽，捕获措辞差异）。
 *
 * @param {string} a normalized prompt
 * @param {string} b normalized prompt
 * @returns {{kind: string, score: number}}
 */
export function comparePromptsForReplay(a, b) {
  if (!hasShortTermStrategyReportIntent(a) || !hasShortTermStrategyReportIntent(b)) {
    return compareNormalizedPrompts(a, b);
  }

  const dateA = extractTradingDate(a);
  const dateB = extractTradingDate(b);
  if (dateA && dateB && dateA !== dateB) {
    return { kind: "none", score: 0 };
  }

  const direct = compareNormalizedPrompts(a, b);
  if (direct.kind !== "none") return direct;

  const keyA = computeSubjectKey(a);
  const keyB = computeSubjectKey(b);
  if (keyA && keyB && keyA === keyB) {
    return { kind: "subject", score: 0.85 };
  }

  const resolvedA = dateA || "latest";
  const resolvedB = dateB || "latest";
  if (resolvedA === resolvedB) {
    return { kind: "subject", score: 0.85 };
  }

  return { kind: "none", score: direct.score };
}

/**
 * 在 registry 记录中查找时间窗口内"实质相同"的 running 任务。
 */
export function findSimilarRunning(records, prompt, opts = {}) {
  if (!Array.isArray(records) || records.length === 0) return null;
  const now = typeof opts.now === "number" ? opts.now : Date.now();
  const windowMs =
    typeof opts.windowMs === "number" && opts.windowMs > 0
      ? opts.windowMs
      : DEFAULT_DUPLICATE_GUARD_WINDOW_MS;
  const skipPromptHash = typeof opts.skipPromptHash === "string" ? opts.skipPromptHash : null;
  const normalized = normalizePromptForGuard(prompt);
  if (!normalized) return null;

  for (const r of records) {
    if (!r || r.status !== "running") continue;
    if (typeof r.startedAt !== "number") continue;
    if (now - r.startedAt > windowMs) continue;
    if (skipPromptHash && r.promptHash === skipPromptHash) continue;
    const candidate = normalizePromptForGuard(r.promptNormalized || r.promptPreview || "");
    if (!candidate) continue;
    const match = comparePromptsForReplay(normalized, candidate);
    if (match.kind !== "none") {
      return { record: r, match };
    }
  }
  return null;
}

/**
 * 在 registry 记录中查找时间窗口内「实质相同」的 completed 任务（多 Agent 串台防护）。
 */
export function findSimilarCompleted(records, prompt, opts = {}) {
  if (!Array.isArray(records) || records.length === 0) return [];
  const now = typeof opts.now === "number" ? opts.now : Date.now();
  const windowMs =
    typeof opts.windowMs === "number" && opts.windowMs > 0
      ? opts.windowMs
      : DEFAULT_REPLAY_GUARD_WINDOW_MS;
  const skipPromptHash = typeof opts.skipPromptHash === "string" ? opts.skipPromptHash : null;
  const normalized = normalizePromptForGuard(prompt);
  if (!normalized) return [];

  const hits = [];
  for (const r of records) {
    if (!r || r.status !== "completed") continue;
    if (skipPromptHash && r.promptHash === skipPromptHash) continue;
    const anchor =
      typeof r.completedAt === "number"
        ? r.completedAt
        : typeof r.startedAt === "number"
          ? r.startedAt
          : null;
    if (anchor === null || now - anchor > windowMs) continue;
    const candidate = normalizePromptForGuard(r.promptNormalized || r.promptPreview || "");
    if (!candidate) continue;
    const match = comparePromptsForReplay(normalized, candidate);
    if (match.kind !== "none") {
      hits.push({ record: r, match });
    }
  }

  return hits.sort(
    (a, b) =>
      (b.record.completedAt ?? b.record.startedAt ?? 0) -
      (a.record.completedAt ?? a.record.startedAt ?? 0),
  );
}

export function buildReplayGuardMessage({ prompt, candidates }) {
  const hasExact = candidates.some((c) => c.match?.kind === "exact");
  const lines = [
    "[CLI][conflict-check] 检测到 24h 内已有实质相同的已完成任务（疑似另一 Agent 已跑完）。",
  ];
  if (hasExact) {
    lines.push(
      "[CLI][conflict-check] 其中含 matchKind=exact（本地**完全相同 prompt**）：直接 --no-wait = 重放（0 额度、不发请求）；--new --no-wait = 新建扣费。",
    );
  }
  lines.push(
    "[CLI][conflict-check] 禁止读取 download/ 同名报告或 tasks.json 里其它 taskId——promptHash 不同则不是本次结果。",
    "[CLI][conflict-check] Agent 必须把下列候选项列给用户、由用户三选一：",
    "  ① 用已有任务的**原 prompt** 重放（推荐，0 次新额度）：",
  );
  const top = candidates[0]?.record;
  const replayPrompt = top?.promptNormalized || top?.promptPreview || prompt;
  lines.push(`       node scripts/cli.mjs --prompt ${JSON.stringify(replayPrompt)} --no-wait`);
  lines.push("  ② 用户确认要用**当前措辞**重新分析（将按积分扣费，须加 --new）：");
  lines.push(`       node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --new --no-wait`);
  lines.push("  ③ 取消本次提问。");
  lines.push("");
  lines.push(
    "[CLI][conflict-check] exit=12 = 可重放已完成任务；未发起任何服务端请求，不扣积分。",
  );
  return lines;
}

export function buildDuplicateGuardMessage({ prompt, existing, match, now = Date.now() }) {
  const elapsedMs = Math.max(0, now - (existing?.startedAt ?? now));
  const elapsedSec = Math.round(elapsedMs / 1000);
  const elapsed =
    elapsedSec < 60
      ? `${elapsedSec}s`
      : elapsedSec < 3600
        ? `${Math.floor(elapsedSec / 60)}m${elapsedSec % 60}s`
        : `${Math.floor(elapsedSec / 3600)}h${Math.floor((elapsedSec % 3600) / 60)}m`;
  const existingPrompt =
    existing?.promptNormalized || existing?.promptPreview || "(无 prompt 预览)";
  const lines = [
    "[CLI][重复提交防护] 检测到时间窗口内已有实质相同的 running 任务，疑似 Agent 换 prompt 重试，已拒绝提交：",
    `  匹配方式     = ${match?.kind ?? "?"}（score=${(match?.score ?? 0).toFixed(2)}）`,
    `  已有任务     = taskId=${existing?.taskId ?? "?"} 已运行 ${elapsed}`,
    `  已有 prompt = ${existingPrompt}`,
    `  本次 prompt = ${prompt}`,
    "",
    "[CLI][重复提交防护] 正确做法（任选其一）：",
    "  ① 用相同 prompt 续接已有任务（推荐，最省额度）：",
    `       node scripts/cli.mjs --prompt \"${existingPrompt}\" --no-wait`,
    "  ② 若确认就是要新建独立任务，请加 --new：",
    `       node scripts/cli.mjs --prompt \"${prompt}\" --new --no-wait`,
    "",
    "[CLI][重复提交防护] 退出码 76 = EXIT_DUPLICATE_LIKELY；不消耗任何服务端额度。",
  ];
  return lines;
}
