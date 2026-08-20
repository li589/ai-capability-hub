// 重复提交防护：检测 Agent 换 prompt 重试导致的"多次新建任务"。
//
// 触发场景（现场已多次出现）：
//   1) Agent 第一次发 `--prompt "分析X的信用风险，重点关注..."`，被沙箱杀进程；
//   2) 误判失败 → 改短 prompt `--prompt "分析X的信用风险"`，再次新建任务；
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
 * 优先级（短路）：
 *   1) identical：字符串完全相等（通常意味着 promptHash 也相等，会走 attach 而不是新建）
 *   2) prefix：较长 prompt 以较短 prompt 开头（"分析X" / "分析X的信用风险"）
 *   3) contained：较长 prompt 包含较短 prompt 作为子串
 *   4) jaccard：bigram 集合相似度 ≥ JACCARD_THRESHOLD
 *   5) none：以上都不命中，视为两条独立任务
 *
 * 较短 prompt < MIN_LEN_FOR_COMPARE 时直接返回 none，避免短 prompt 假阳性。
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

/** 信用分析 replay 预检用的通用词（不作为主体 token）。 */
const REPLAY_SUBJECT_STOPWORDS = new Set([
  "分析",
  "信用",
  "报告",
  "资质",
  "风险",
  "公司",
  "集团",
  "股份",
  "有限",
  "信用报告",
  "分析报告",
  "信用分析报告",
  "给我一份",
  "给我做一份",
  "帮我做一份",
  "帮我分析",
  "分析一下",
  "的",
  "了",
  "做",
  "给",
  "帮",
  "看",
  "出",
  "一份",
  "下",
  "重点",
  "关注",
]);

/**
 * 从 prompt 提取可用于 replay 判定的主体 token（公司名片段 / 证券代码）。
 * @param {string} text normalized prompt
 * @returns {Set<string>}
 */
function extractReplaySubjectTokens(text) {
  const tokens = new Set();
  for (const m of String(text).matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    tokens.add(m[0].toUpperCase());
    tokens.add(m[0].slice(0, 6));
  }
  for (const m of String(text).matchAll(/[\u4e00-\u9fff]{4,16}/g)) {
    const seg = m[0];
    if (REPLAY_SUBJECT_STOPWORDS.has(seg)) continue;
    tokens.add(seg);
    if (seg.length >= 5) {
      for (let i = 0; i <= seg.length - 4; i++) {
        const sub = seg.slice(i, i + 4);
        if (!REPLAY_SUBJECT_STOPWORDS.has(sub)) tokens.add(sub);
      }
    }
  }
  return tokens;
}

function hasCreditResearchIntent(text) {
  const t = String(text);
  if (!t.includes("信用")) return false;
  return /报告|分析|资质|风险|健康度|违约|现金流/.test(t);
}

function isLikelyCompanyCoreName(name) {
  if (!name || name.length < 2) return false;
  if (/^[和与及]/.test(name)) return false;
  if (/和|与|及/.test(name)) return false;
  if (/^(财务|资质|健康|风险|现金流|分析|对比|报告)/.test(name)) return false;
  return true;
}

/**
 * 从信用分析 prompt 提取稳定的主体键（跨措辞 submit 锁 / 调度续接用）。
 * 返回 null 表示无法可靠提取（如对比多家公司 A/B）。
 *
 * @param {string} prompt
 * @returns {string|null}
 */
export function computeSubjectKey(prompt) {
  const normalized = normalizePromptForGuard(prompt);
  if (!normalized || !hasCreditResearchIntent(normalized)) return null;

  // 对比多家主体的 prompt 不做主体锁（如「对比万科和保利」）
  if (/对比|比较|二者|两家|两者/.test(normalized)) return null;
  if (/(?:对比|比较).{0,24}[\u4e00-\u9fff]{2,8}和[\u4e00-\u9fff]{2,8}/.test(normalized)) return null;

  const codes = new Set();
  for (const m of normalized.matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    codes.add(m[0].slice(0, 6).toUpperCase());
  }

  const coreNames = new Set();
  for (const m of normalized.matchAll(/[\u4e00-\u9fff]{4,16}/g)) {
    const stripped = stripStopwordBorders(m[0]);
    if (stripped && isLikelyCompanyCoreName(stripped) && !REPLAY_SUBJECT_STOPWORDS.has(stripped)) {
      coreNames.add(stripped);
    }
  }

  if (codes.size === 0 && coreNames.size === 0) return null;

  const nameList = [...coreNames].sort((a, b) => b.length - a.length);
  const independentNames = nameList.filter(
    (n, i) => !nameList.some((other, j) => i !== j && (n.includes(other) || other.includes(n))),
  );
  if (independentNames.length >= 2) return null;

  // 优先用公司名（含证券代码的 prompt 通常也能 strip 出公司名）
  if (nameList.length >= 1) return `name:${nameList[0]}`;
  if (codes.size === 1) return `code:${[...codes][0]}`;
  if (codes.size >= 1) return `code:${[...codes][0]}`;
  return null;
}

/**
 * 只提取正则完整匹配的主体段（公司名连续中文段 / 证券代码），不含滑窗子串。
 * 同时，对较长段去掉前缀/后缀的停用词后提取核心主体名（如「给我一份泰山石油的信用报告」→「泰山石油」）。
 * 用于 comparePromptsForReplay 的 subject 匹配，避免 4 字滑窗片段跨不同主体误匹配。
 * @param {string} text normalized prompt
 * @returns {Set<string>}
 */
function extractReplaySubjectFullSegments(text) {
  const tokens = new Set();
  for (const m of String(text).matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    tokens.add(m[0].toUpperCase());
  }
  for (const m of String(text).matchAll(/[\u4e00-\u9fff]{4,16}/g)) {
    const seg = m[0];
    if (!REPLAY_SUBJECT_STOPWORDS.has(seg)) {
      tokens.add(seg);
    }
    // Strip leading/trailing stopword runs to extract the core subject name.
    // E.g. "给我一份泰山石油的信用报告" → "泰山石油"
    const stripped = stripStopwordBorders(seg);
    if (stripped && stripped.length >= 2 && !REPLAY_SUBJECT_STOPWORDS.has(stripped)) {
      tokens.add(stripped);
    }
  }
  return tokens;
}

/**
 * 去掉中文段首尾的停用词边界，提取核心主体名。
 * 例如：「给我一份泰山石油的信用报告」→「泰山石油」
 * @param {string} seg
 * @returns {string|null}
 */
function stripStopwordBorders(seg) {
  // Build a sorted list of stopwords by length (longest first) for greedy matching
  let remaining = seg;
  // Strip leading stopwords
  let changed = true;
  while (changed && remaining.length >= 2) {
    changed = false;
    for (const sw of SORTED_STOPWORDS_BY_LEN) {
      if (remaining.startsWith(sw)) {
        remaining = remaining.slice(sw.length);
        changed = true;
        break;
      }
    }
  }
  // Strip trailing stopwords
  changed = true;
  while (changed && remaining.length >= 2) {
    changed = false;
    for (const sw of SORTED_STOPWORDS_BY_LEN) {
      if (remaining.endsWith(sw)) {
        remaining = remaining.slice(0, remaining.length - sw.length);
        changed = true;
        break;
      }
    }
  }
  return remaining.length >= 2 ? remaining : null;
}

/** REPLAY_SUBJECT_STOPWORDS 按长度降序排列，用于贪心去前缀/后缀。 */
const SORTED_STOPWORDS_BY_LEN = [...REPLAY_SUBJECT_STOPWORDS].sort(
  (a, b) => b.length - a.length,
);

/**
 * completed 任务 replay 预检用的相似度（比 running 防护略宽，捕获「信用报告」vs「信用分析报告」等措辞差异）。
 *
 * @param {string} a normalized prompt
 * @param {string} b normalized prompt
 * @returns {{kind: string, score: number}}
 */
export function comparePromptsForReplay(a, b) {
  const direct = compareNormalizedPrompts(a, b);
  if (direct.kind !== "none") return direct;

  if (!hasCreditResearchIntent(a) || !hasCreditResearchIntent(b)) {
    return { kind: "none", score: direct.score };
  }

  // Only match on full subject segments (from the regex match, not sliding-window subs).
  // Sliding-window 4-char subs like "件的信用" easily appear across different prompts
  // and cause false positives (e.g. "江苏中威软件" vs "ST海华" both contain "的信用").
  // Also, a.includes(token) is a self-reference tautology (token was extracted from a),
  // so it must not be used — it caused every pair of credit-analysis prompts to match.
  const fullSegsA = extractReplaySubjectFullSegments(a);
  const fullSegsB = extractReplaySubjectFullSegments(b);
  for (const seg of fullSegsA) {
    if (seg.length < 3) continue;
    if (fullSegsB.has(seg) || b.includes(seg)) {
      return { kind: "subject", score: 0.85 };
    }
  }
  for (const seg of fullSegsB) {
    if (seg.length < 3) continue;
    if (fullSegsA.has(seg) || a.includes(seg)) {
      return { kind: "subject", score: 0.85 };
    }
  }
  return { kind: "none", score: direct.score };
}

/**
 * 在 registry 记录中查找时间窗口内"实质相同"的 running 任务。
 *
 * @param {Array<object>} records tasks.json 中的 records 数组
 * @param {string} prompt 本次准备提交的原始 prompt（内部会 normalize）
 * @param {object} [opts]
 * @param {number} [opts.now=Date.now()]
 * @param {number} [opts.windowMs=DEFAULT_DUPLICATE_GUARD_WINDOW_MS]
 * @param {string} [opts.skipPromptHash] 同一 promptHash 的记录跳过（这种情况
 *   主流程会走 attach / continue 续接路径，不算重复）
 * @returns {{record: object, match: {kind: string, score: number}} | null}
 *   命中相似任务则返回；否则返回 null。
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
    // 与 completed replay 共用 comparePromptsForReplay，捕获「信用报告」vs「信用分析报告」等同主体措辞差异
    const match = comparePromptsForReplay(normalized, candidate);
    if (match.kind !== "none") {
      return { record: r, match };
    }
  }
  return null;
}

/**
 * 在 registry 记录中查找时间窗口内「实质相同」的 completed 任务（多 Agent 串台防护）。
 *
 * @param {Array<object>} records tasks.json 中的 records 数组
 * @param {string} prompt 本次准备提交的原始 prompt（内部会 normalize）
 * @param {object} [opts]
 * @param {number} [opts.now=Date.now()]
 * @param {number} [opts.windowMs=DEFAULT_REPLAY_GUARD_WINDOW_MS]
 * @param {string} [opts.skipPromptHash] 同一 promptHash 跳过（主流程会走 replay_completed）
 * @returns {Array<{record: object, match: {kind: string, score: number}}>}
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

/**
 * 构造 check-conflict 命中「相似已完成任务」时的 stderr 引导文案。
 *
 * @param {object} ctx
 * @param {string} ctx.prompt 本次 prompt
 * @param {Array<{record: object, match: object}>} ctx.candidates
 * @returns {string[]}
 */
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

/**
 * 构造命中重复提交防护时输出到 stderr 的引导文案。pure 函数便于单测断言。
 *
 * @param {object} ctx
 * @param {string} ctx.prompt 本次要提交的原始 prompt
 * @param {object} ctx.existing registry record（含 taskId、promptPreview 等）
 * @param {{kind: string, score: number}} ctx.match compareNormalizedPrompts 返回值
 * @param {number} [ctx.now] 用于计算已运行多久
 * @returns {string[]} 待按顺序写入 stderr 的多行字符串
 */
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
    "[CLI][重复提交防护] 检测到时间窗口内已有"
      + "实质相同"
      + "的 running 任务，疑似 Agent 换 prompt 重试，已拒绝提交：",
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
