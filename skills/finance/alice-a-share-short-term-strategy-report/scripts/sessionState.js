// A股短线策略报告 —— 跨 CLI 进程的"当前会话"追踪
//
// 背景：Alice Agent 服务端用 contextId 关联多轮对话上下文；不同 contextId 之间
// 完全隔离。本 CLI 每次调用是独立子进程，若跨调用共享 contextId，用户在同一
// 会话内的后续提问服务端就能拿到前一轮的上下文，多轮问答更连贯。
//
// **默认行为（工作区自动续接）**：每次 CLI 调用**默认在空闲窗口内自动复用**
// 上次 contextId——无需宿主 Agent 显式传 `--context-id` 或 `--continue-session`。
// 这样修复了"Agent 忘记把上一轮 contextId 接力给下一轮 → 静默退回新会话"的
// 痛点。只有 `--new-session` 才强制开新会话。
//
// **会话文件落工作区（防串号）**：会话状态写到 `<workspaceDir>/.wind-alice/
// current-session[.<scope>].json`，workspaceDir 由调用方传入（生产路径 =
// process.cwd()）。同一工作区 = 同一会话文件 → 自动续接；不同工作区 / 不同
// 宿主各自独立文件 → 物理上不串号。这与 tasks.json 不同：tasks.json 需跨会话
// 稳定用于 replay/去重，仍留全局 `~/.wind-alice/`（见 dataDir.js）；会话文件
// 只需"同一会话内稳定"，且按工作区隔离正是为了防串号，故落工作区。
//
// 历史 flag 语义：
//   - `--context-id <id>`：显式指定复用某个 contextId（从上一轮 DONE 行取）。
//     仍支持，显式优先级最高；现在也会把最新 contextId 落到工作区文件，供后续
//     自动续接。跨话题精确控制时可用，但同话题续接已无需手动传。
//   - `--continue-session`：**已废弃**（no-op）。自动续接已是默认，无需显式请求。
//   - `--new-session`：强制新建会话上下文（不复用工作区文件里的 contextId）。
//     完全无关的新话题时加，避免无关上文污染。
//
// **会话 scope 隔离（v2，现基本冗余）**：`--session-scope <id>` 把会话文件加
// `<scope>` 后缀。工作区隔离已按 process.cwd() 切分，scope 通常无需再传；仅
// 保留给同一工作区内仍想再细分会话的旧式用法，或环境变量 WIND_ALICE_SESSION_SCOPE。
//
// 落盘信息：把"最近一次成功任务的 contextId + 使用时间"写入工作区会话文件；
// 下次 CLI 调用默认在 idle window（默认 30 分钟）内自动复用。
//
// taskId 始终每次新生成——每条 prompt 对应一个新任务，只有 contextId 决定
// 是否复用会话上下文。

import {
  existsSync,
  mkdirSync,
  readFileSync,
  renameSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { resolveDataDir } from "./dataDir.js";

// 会话文件名（落在工作区 .wind-alice/ 下，或测试覆盖路径下）
const DEFAULT_SESSION_FILENAME = "current-session.json";

/**
 * 解析会话文件所在目录。
 * 优先级：
 *   1. 环境变量 ALICE_SESSION_DIR（测试 / 显式覆盖）
 *   2. workspaceDir（生产路径 = process.cwd()）→ <workspaceDir>/.wind-alice/
 *   3. resolveDataDir()（~/.wind-alice/，向后兼容：调用方未传 workspaceDir 时）
 *
 * @param {string} [workspaceDir] 工作区目录（process.cwd()）
 * @returns {string} 绝对路径
 */
function getSessionDir(workspaceDir) {
  const override = process.env.ALICE_SESSION_DIR;
  if (override && String(override).trim()) return String(override).trim();
  if (workspaceDir && String(workspaceDir).trim()) {
    return join(String(workspaceDir).trim(), ".wind-alice");
  }
  return resolveDataDir();
}

/** 默认会话空闲窗口：30 分钟。超过这个时长没提问，视为新会话。 */
export const DEFAULT_SESSION_IDLE_MS = 30 * 60 * 1000;

/** scope 允许的字符集：字母数字与常见分隔符；其余字符统一替换成 `_`。 */
const SCOPE_SAFE_CHARS = /[^A-Za-z0-9._\-]/g;
/** scope 长度上限（避免文件名过长；超出时截断）。 */
const SCOPE_MAX_LENGTH = 64;

/**
 * 将宿主 Agent 传入的会话 scope 规范化为合法文件名后缀。
 * - null / undefined / 空串 → 返回 ""（表示落回默认文件名）
 * - 其它 → 替换非法字符、截断长度
 *
 * @param {string|null|undefined} raw
 * @returns {string} 规范化后的 scope；空串表示走默认文件名
 */
export function sanitizeSessionScope(raw) {
  if (raw === null || raw === undefined) return "";
  const trimmed = String(raw).trim();
  if (!trimmed) return "";
  const safe = trimmed.replace(SCOPE_SAFE_CHARS, "_");
  return safe.slice(0, SCOPE_MAX_LENGTH);
}

/**
 * 计算本次读写落盘用的会话文件路径。
 * 单测可用 `ALICE_SESSION_FILE` 环境变量覆盖为临时文件路径，此时无视 scope / workspaceDir。
 *
 * @param {string|null|undefined} sessionScope 已由 `sanitizeSessionScope` 处理或原始值
 * @param {string} [workspaceDir] 工作区目录（process.cwd()）；不传则回落全局 ~/.wind-alice/
 * @returns {string} 绝对路径
 */
function sessionFilePath(sessionScope, workspaceDir) {
  const override = process.env.ALICE_SESSION_FILE;
  if (override && String(override).trim()) return String(override).trim();
  const dir = getSessionDir(workspaceDir);
  const scope = sanitizeSessionScope(sessionScope);
  if (!scope) return join(dir, DEFAULT_SESSION_FILENAME);
  return join(dir, `current-session.${scope}.json`);
}

/** 高级用户/测试：通过环境变量覆盖 idle window。 */
function readEnvIdleMs() {
  const raw = process.env.WIND_ALICE_SESSION_IDLE_MS;
  if (!raw) return null;
  const n = Number.parseInt(String(raw), 10);
  if (!Number.isFinite(n) || n < 0) return null;
  return n;
}

/**
 * 读取当前 scope / 工作区对应的 session 文件；文件不存在 / 损坏 / 字段不合法均返回 null。
 * @param {object} [opts]
 * @param {string} [opts.sessionScope] 宿主 Agent 会话标识；不传走默认文件名
 * @param {string} [opts.workspaceDir] 工作区目录（process.cwd()）；不传回落全局 ~/.wind-alice/
 * @returns {{contextId: string, lastUsedAt: number, lastTaskId?: string, lastPromptHash?: string} | null}
 */
export function loadCurrentSession({ sessionScope, workspaceDir } = {}) {
  const file = sessionFilePath(sessionScope, workspaceDir);
  try {
    if (!existsSync(file)) return null;
    const text = readFileSync(file, "utf8");
    const parsed = JSON.parse(text);
    if (
      parsed &&
      typeof parsed === "object" &&
      typeof parsed.contextId === "string" &&
      parsed.contextId.length > 0 &&
      typeof parsed.lastUsedAt === "number" &&
      Number.isFinite(parsed.lastUsedAt)
    ) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * 决定本次调用应使用的 contextId（默认自动续接）：
 *   - forceNewSession=true（`--new-session`） → 返回 null（buildBody 生成新 UUID，全新会话）
 *   - 否则：读会话文件（工作区优先），若存在且 lastUsedAt 在 idleWindowMs 内
 *       → 返回其 contextId（服务端继承前一轮上下文）
 *   - 会话不存在 / 过期 → 返回 null（新会话）
 *
 * `continueSession` 参数已废弃（自动续接已是默认），保留仅为向后兼容，不再 gating。
 *
 * @param {object} [opts]
 * @param {boolean} [opts.forceNewSession] `--new-session` 强制新建；true 时返回 null。
 * @param {boolean} [opts.continueSession] **已废弃**（no-op）；自动续接为默认行为。
 * @param {string}  [opts.workspaceDir]
 *   工作区目录（process.cwd()）；传入则会话文件落 `<workspaceDir>/.wind-alice/`，
 *   按工作区隔离防串号。不传则回落全局 ~/.wind-alice/（向后兼容）。
 * @param {string}  [opts.sessionScope]
 *   宿主 Agent 会话标识；工作区隔离下通常无需传。传入则在文件名加 `<scope>` 后缀。
 * @param {number} [opts.now=Date.now()]
 * @param {number} [opts.idleWindowMs] 默认读环境变量；未设置则用 DEFAULT_SESSION_IDLE_MS
 * @returns {string|null}
 */
export function resolveSessionContextId({
  forceNewSession = false,
  continueSession = false,
  sessionScope,
  workspaceDir,
  now = Date.now(),
  idleWindowMs,
} = {}) {
  if (forceNewSession) return null;
  // continueSession 已废弃：自动续接为默认，无需显式请求。
  void continueSession;
  const window = typeof idleWindowMs === "number" && idleWindowMs >= 0
    ? idleWindowMs
    : (readEnvIdleMs() ?? DEFAULT_SESSION_IDLE_MS);
  const state = loadCurrentSession({ sessionScope, workspaceDir });
  if (!state) return null;
  if (now - state.lastUsedAt > window) return null;
  return state.contextId;
}

/**
 * 写入 / 更新当前会话状态：contextId + 最近使用时间 (+ 可选 taskId / promptHash 供调试)。
 * 采用 tmp + rename 原子写入，避免读到半写文件。
 * 写盘失败静默返回 false（不阻塞主流程；沙箱只读环境常见）。
 *
 * @param {object} params
 * @param {string} params.contextId
 * @param {string} [params.taskId]
 * @param {string} [params.promptHash]
 * @param {string} [params.sessionScope] 宿主 Agent 会话标识；不传走默认文件名
 * @param {string} [params.workspaceDir] 工作区目录（process.cwd()）；不传回落全局 ~/.wind-alice/
 * @param {number} [params.now]
 * @returns {boolean} 是否成功写盘
 */
export function saveCurrentSession({
  contextId,
  taskId,
  promptHash,
  sessionScope,
  workspaceDir,
  now = Date.now(),
}) {
  if (!contextId || typeof contextId !== "string") return false;
  const file = sessionFilePath(sessionScope, workspaceDir);
  const tmp = `${file}.tmp`;
  try {
    mkdirSync(getSessionDir(workspaceDir), { recursive: true });
    const payload = {
      contextId,
      lastUsedAt: typeof now === "number" && Number.isFinite(now) ? now : Date.now(),
      lastTaskId: typeof taskId === "string" && taskId ? taskId : undefined,
      lastPromptHash:
        typeof promptHash === "string" && promptHash ? promptHash : undefined,
    };
    writeFileSync(tmp, JSON.stringify(payload, null, 2), "utf8");
    renameSync(tmp, file);
    return true;
  } catch {
    try {
      if (existsSync(tmp)) unlinkSync(tmp);
    } catch {}
    return false;
  }
}

/**
 * 清除当前 scope / 工作区对应的会话状态（测试辅助；生产路径无需主动调用——过期自然不复用即可）。
 * @param {object} [opts]
 * @param {string} [opts.sessionScope] 宿主 Agent 会话标识；不传走默认文件名
 * @param {string} [opts.workspaceDir] 工作区目录（process.cwd()）；不传回落全局 ~/.wind-alice/
 */
export function clearCurrentSession({ sessionScope, workspaceDir } = {}) {
  try {
    const file = sessionFilePath(sessionScope, workspaceDir);
    if (existsSync(file)) unlinkSync(file);
    return true;
  } catch {
    return false;
  }
}

/** @internal 单测：暴露解析后的 idle 窗口，避免测试硬编码 DEFAULT_SESSION_IDLE_MS。 */
export function __getEffectiveIdleWindowForTesting(overrideMs) {
  if (typeof overrideMs === "number" && overrideMs >= 0) return overrideMs;
  return readEnvIdleMs() ?? DEFAULT_SESSION_IDLE_MS;
}

/** @internal 单测：暴露 scope / workspace → 文件路径的映射，便于测试断言隔离。 */
export function __resolveSessionFilePathForTesting(sessionScope, workspaceDir) {
  return sessionFilePath(sessionScope, workspaceDir);
}
