import randomUUID from "./uuidv7.js";
import { createHash } from "node:crypto";
import {
  chmodSync,
  createWriteStream,
  existsSync,
  mkdirSync,
  readFileSync,
  statSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { homedir, tmpdir } from "node:os";
import { dirname, join, parse as parsePath, resolve } from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { pathToFileURL } from "node:url";
import { resolveDataDir } from "./dataDir.js";
import { ensureWindowsUtf8Stdio, getPreTeeSessionLogContent, installWindowsSessionLogTee, sessionLogPathForPrompt, UTF8_BOM } from "./encoding.js";
import { openRegistry, REGISTRY_PATHS, saveResultFile } from "./tasksRegistry.js";
import {
  buildDuplicateGuardMessage,
  buildReplayGuardMessage,
  computeSubjectKey,
  findSimilarCompleted,
  findSimilarRunning,
  normalizePromptForGuard,
  DEFAULT_REPLAY_GUARD_WINDOW_MS,
} from "./duplicateGuard.js";
import { buildArtifactGuardLines } from "./artifactGuard.js";
import { findReusableDownload, runDownloadWithLock, releaseDownloadLock, sleep, tryAcquireDownloadLock } from "./downloadGuard.js";
import {
  __getServerUsageSessionForTesting,
  announceServerUsage,
  notePeerFinalize,
  printServerUsageSummary,
} from "./serverUsage.js";
import { sanitizeAgentResultTextForDelivery } from "./agentResultSanitize.js";
import {
  resolveSessionContextId,
  saveCurrentSession,
} from "./sessionState.js";

// 在 Windows 沙箱 / 控制台中把代码页切到 UTF-8，避免中文输出被默认 GBK 解码乱码。
// 这里再调一次是为了支持"直接 node scripts/request.js"独立运行的场景；
// 由 cli.mjs spawn 启动时父进程已切过一次，重复调用是幂等的。
ensureWindowsUtf8Stdio();

const DEFAULT_API_URL = "https://alice.wind.com.cn/Weaver/ChatAgent";
// 获取 / 重置 / 查看 API Key 的精确入口：万得 Alice → 设置 → 账户 标签页
const WIND_ALICE_KEY_PAGE = "https://alice.wind.com.cn/settings?tab=account";

// API Key 唯一存放位置：~/.wind-alice/config.env（dotenv: WIND_API_KEY=...）
// 故意不支持环境变量和 skill 目录内 config.json，避免 Key 泄漏到当前会话或被打包到 skill 目录。
// 历史版本写入的是无后缀 ~/.wind-alice/config，读取时向后兼容；apikey-set 会自动迁移到 config.env。
const KEY_CONFIG_DIR = join(homedir(), ".wind-alice");
const KEY_CONFIG_FILE = join(KEY_CONFIG_DIR, "config.env");
const LEGACY_KEY_CONFIG_FILE = join(KEY_CONFIG_DIR, "config");

/**
 * 找到当前实际存在的 Key 配置文件路径：优先 config.env，回退到老的无后缀 config。
 * 都不存在时返回 null；调用方据此决定走"未配置"分支。
 */
function resolveExistingKeyConfigPath() {
  if (existsSync(KEY_CONFIG_FILE)) return KEY_CONFIG_FILE;
  if (existsSync(LEGACY_KEY_CONFIG_FILE)) return LEGACY_KEY_CONFIG_FILE;
  return null;
}

// 本 CLI 仅承载万得 Alice 的「公司一页纸」技能。
// 服务端通过 prompt 文本前缀 `使用「<Skill 名>」技能：` 识别 Skill。
const ALICE_SKILL_NAME_ZH = "公司一页纸";

// ChatAgent 请求渠道标识，供服务端识别调用来源。
const ALICE_CHANNEL = "Tencent.Workbuddy";

// 服务端在 agentResult 中给出的 `/project/xxx` 是 Alice 工作区相对路径，需要拼成
// 完整下载 URL 才能由 CLI 自动拉取：
//   ${WIND_PROJECT_FILES_PREFIX}<contextId>/project/<filename>
// 其中 contextId 取自本次请求体里 `params.message.contextId`。
// 公开 API 路径前缀（非密钥）；可通过环境变量 WIND_PROJECT_FILES_PREFIX 覆盖。
const DEFAULT_WIND_PROJECT_FILES_PREFIX = [
  "https://alice.wind.com.cn",
  "/weaver/files/",
  "alice-convo-",
  "1416751125",
  "/sessions/",
].join("");
const WIND_PROJECT_FILES_PREFIX =
  process.env.WIND_PROJECT_FILES_PREFIX ?? DEFAULT_WIND_PROJECT_FILES_PREFIX;

// 当前请求的 contextId，供下载阶段把相对路径补全为完整 URL；每次请求开始前重置。
let currentSessionContextId = null;

// 本次调用是否通过 --context-id 显式指定了要复用的 contextId。
// 非空时：复用它续接（优先级最高）。工作区隔离下仍会把最新 contextId 落盘到
// <process.cwd()>/.wind-alice/（见 maybeSaveCurrentSession），供后续自动续接。
// 每次 main 开始前设置。
let currentExplicitContextId = null;

// 落盘当前会话（contextId）到工作区文件 <process.cwd()>/.wind-alice/，供下次调用
// 默认自动续接。工作区隔离已取代旧版"显式 --context-id 路径不碰共享文件"的防串号
// 策略：现在无论是否显式传 --context-id，都把（可能被服务端重绑的）最新 contextId
// 落盘，保证后续自动续接拿到的是最新值。
function maybeSaveCurrentSession(opts) {
  return saveCurrentSession({ ...opts, workspaceDir: opts?.workspaceDir ?? process.cwd() });
}

// 任务幂等性（跨进程 attach）配置：
// - ATTACH_RESUME_WINDOW_MS：registry 中 running 任务允许 attach 的最大时间窗口；
//   超过该窗口的 running 记录视为可疑僵尸，不再 attach，走新建任务流程。
// - ATTACH_FIRST_EVENT_TIMEOUT_MS：attach 后等待"首个 SSE 事件"的超时时间；
//   超时即取消订阅并回退到新建任务（防止服务端 task 已死透但 resubscribe 表面 200）。
const ATTACH_RESUME_WINDOW_MS = 60 * 60 * 1000;
const ATTACH_FIRST_EVENT_TIMEOUT_MS = 60 * 1000;

// 历史任务过期阈值：超过此时间的 completed / running 记录视为过期，
// 不再 replay / attach，而是清除后新建（避免用户拿到很久以前的旧报告）。
const STALE_TASK_THRESHOLD_MS = 30 * 60 * 1000;

/** @internal 单测 */
export { STALE_TASK_THRESHOLD_MS };

/** @internal 单测：判断 record 是否已过期（超过 STALE_TASK_THRESHOLD_MS） */
export function isStaleRecord(record, now = Date.now()) {
  if (!record) return false;
  const ref =
    record.status === "completed" && typeof record.completedAt === "number" && Number.isFinite(record.completedAt)
      ? record.completedAt
      : record.startedAt;
  if (typeof ref !== "number" || !Number.isFinite(ref)) return false;
  return now - ref > STALE_TASK_THRESHOLD_MS;
}

// 本地 failed 但服务端任务可能仍在跑 / 已完成（典型：SSE 断流、沙箱杀进程、
// stdout 截断后 Agent 又用普通模式重发）。窗口内先用 tasks/get 对齐服务端，避免重复 message/stream。
const RECOVERABLE_LOCAL_FAIL_REASONS = [
  /^no agentResult$/,
  /^stream error:/,
  /^network error:/,
  /^read body error:/,
  /^jsonrpc error$/,
  /^non-stream error$/,
];

// --no-wait 模式 SSE 先行阶段超时（毫秒）。
// 提交任务后先持续读 SSE 流，如果在这个窗口内服务端推送了 agentResult（任务完成），
// 则直接拿到结果、零延迟交付；超时或流断开后降级到 tasks/get 轮询。
// 设为 120s：覆盖大部分 2 分钟内完成的简单分析场景，同时在终端 3-5 分钟超时窗口内
// 仍有余量进入 tasks/get 自旋。
const NO_WAIT_SSE_PHASE_TIMEOUT_MS = 120 * 1000;

/** @internal 单测 */
export function isWithinResumeWindow(record, now = Date.now()) {
  if (!record || typeof record.startedAt !== "number") return false;
  return now - record.startedAt < ATTACH_RESUME_WINDOW_MS;
}

/** @internal 单测 */
export function isRecoverableLocalFailure(record) {
  if (!record || record.status !== "failed") return false;
  const reason = String(record.failReason ?? "").trim();
  if (!reason) return true;
  return RECOVERABLE_LOCAL_FAIL_REASONS.some((re) => re.test(reason));
}

/** @internal 单测：resume 窗口内、且有 taskId 的 failed 记录应先探针服务端 */
export function shouldProbeFailedRecord(record, now = Date.now()) {
  if (!record || record.status !== "failed") return false;
  if (!record.taskId || !record.contextId) return false;
  if (!isWithinResumeWindow(record, now)) return false;
  return isRecoverableLocalFailure(record);
}

/**
 * 体验账户额度耗尽、服务繁忙等场景下，服务端会通过 status-update / UIState /
 * A2A.Markdown 等通道投递用户可见提示。命中后原样打印接口返回文案并停止后续处理，
 * 避免下游误以为还会有正常报告产出。
 */
let serverUserNoticeHandled = false;

// 跟踪本次请求的关键状态：是否收到过最终 agentResult 事件、是否已打印过 jsonrpc 顶层错误。
// 用于在 SSE 流静默结束时给出明确的失败提示，避免只看到 `[完成] 总耗时 1s` 误导用户。
let agentResultSeen = false;
let jsonRpcErrorReported = false;

// 累积本次会话中通过 UIState artifact-update 推送的 A2A.Markdown 文案。
// 不立即打断流（UIState 在正常流程也会刷新中间态），只在 SSE 流结束且没有
// agentResult 的失败分支里把它当作最权威的失败原因打印出来。例如：
// "很抱歉，今日已超出体验期任务限额，欢迎您明日再来尝试。"
const pendingUiStateNotices = [];

function resetSessionState() {
  serverUserNoticeHandled = false;
  agentResultSeen = false;
  jsonRpcErrorReported = false;
  pendingUiStateNotices.length = 0;
  lastServerUserNoticeInfo = null;
  collectedDownloads.clear();
  collectedAgentResultValues.length = 0;
}

// ---------------------------------------------------------------------------
// DONE 标志 + strict 模式：单一确定的"任务真正完成"信号
// ---------------------------------------------------------------------------
// 历史问题：Agent 把"被沙箱杀掉的 cli.mjs 进程"当成成功——SSE 流被中断、
// agentResult 没收到、tasks.json 永远停在 running，但宿主终端报告 exit code 0。
//
// 修复策略：
//   1) 任务真正完成（落盘 + 下载完毕）时，在 stdout 打一行机器可读的 DONE 标志：
//        ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE taskId=<id> promptHash=<hash> reportFile=<abs> reportFullFile=<abs>
//      Agent 只需匹配该行就能确认成功，比解析 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=COMPLETED
//      更鲁棒（DONE 行有具体路径，便于 Agent 直接读文件）。
//   2) strict 模式（默认开启）：进程退出钩子里检查——若声明了 strictRequired
//      但从未 emit DONE 且 exitCode 仍为 0，强制改成 EXIT_STRICT_NO_DONE(6)。
//      被沙箱信号杀死时根本走不到 emit 路径，DONE 必然缺失，strict 兜底就生效。
//   3) 子命令（apikey-*）、help、--no-wait 探针仍在 working 等场景不要求 emit DONE，
//      由主流程显式调用 strictRequired = true 来圈出"需要保证产出"的路径。
let analysisDoneEmitted = false;
let strictRequired = false;
let strictDisabled = false;
let lastReportFilePath = null;
let lastReportFullFilePath = null;
let lastDoneTaskId = null;
let lastDonePromptHash = null;

/** 由 persistAgentResultIfAny / replayCompletedArtifacts 在落盘 REPORT_FILE 后调用。 */
function rememberReportFile(path) {
  if (typeof path === "string" && path) lastReportFilePath = path;
}
/** 由 printReportFullFileTag 在打出 REPORT_FULL_FILE= 之前调用。 */
function rememberReportFullFile(path) {
  if (typeof path === "string" && path) lastReportFullFilePath = path;
}
/** 任务对应的 taskId（最近一次完成路径上拿到的）。 */
function rememberDoneTaskId(taskId) {
  if (typeof taskId === "string" && taskId) lastDoneTaskId = taskId;
}
/** 任务对应的 promptHash（与 DONE 行绑定，供 Agent 核对是否误读其它任务）。 */
function rememberDonePromptHash(promptHash) {
  if (typeof promptHash === "string" && promptHash) lastDonePromptHash = promptHash;
}

/**
 * 输出 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 行。幂等：同一进程内只输出一次。
 * 必须在 stdout 输出（与其它机器可读标记同流），最末尾再单独 println 一次以方便 Agent
 * 用 "tail -n 1 / endsWith" 匹配。
 */
function emitAnalysisDone({ taskId, promptHash } = {}) {
  if (analysisDoneEmitted) return;
  analysisDoneEmitted = true;
  // 任务完成时释放提交锁，允许同一 prompt 的后续 CLI 重新提交
  const doneHash = promptHash || lastDonePromptHash;
  if (doneHash) releaseAllSubmitLocks(doneHash);
  printServerUsageSummary();
  const effectiveTaskId = taskId || lastDoneTaskId;
  const effectivePromptHash = promptHash || lastDonePromptHash;
  // 把生效的 taskId 回写到模块状态，便于 __getAnalysisDoneStateForTesting 反查，
  // 同时让后续诊断日志也能引用到同一 taskId。
  if (effectiveTaskId) lastDoneTaskId = effectiveTaskId;
  if (effectivePromptHash) lastDonePromptHash = effectivePromptHash;
  const parts = ["ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE"];
  if (effectiveTaskId) parts.push(`taskId=${effectiveTaskId}`);
  if (effectivePromptHash) parts.push(`promptHash=${effectivePromptHash}`);
  // 供 Agent 下一轮用 --context-id 续接：取本字段值原样传回，即可复用同一会话上下文。
  if (currentSessionContextId) parts.push(`contextId=${currentSessionContextId}`);
  if (lastReportFilePath) parts.push(`reportFile=${lastReportFilePath}`);
  if (lastReportFullFilePath) parts.push(`reportFullFile=${lastReportFullFilePath}`);
  if (lastReportFullFilePath) {
    const presentablePaths = [lastReportFullFilePath];
    for (const line of [
      "================ ⚠️ present_files 提醒（必须执行）================",
      "DONE 行含 reportFullFile=（如 .md 报告）时，",
      "你必须在交付 agentResult.value 正文之前：",
      "· 从 DONE 行提取 reportFullFile= 路径",
      "· 路径已在工作空间（CLI 统一下载到 process.cwd()），无需 cp",
      "· 在【独立一条消息】里调 present_files",
      "· 🔴 present_files 这条消息只准有 present_files，不得有 Bash/Read/Edit/Write/文件操作等任何其它工具调用--否则整条折叠、卡片隐藏（高乐股份现场已复现）",
      "· 随后在【另一条纯文本消息】里逐字输出 agentResult.value（禁任何工具调用）",
      "====================================================",
    ]) {
      console.log(line);
    }
    for (const p of presentablePaths) {
      console.log(`ALICE_PRESENT_FILES=1 path=${p}`);
    }
  }
  console.log(parts.join(" "));
  console.log(
    "[CLI] 上一行 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 是本进程任务"
      + "真正完成"
      + "的唯一确定标志；缺失即视为未完成（strict 模式会强制 exit=6）。",
  );
  console.log(
    "[CLI] Agent 交付前必须核对 DONE 行中的 promptHash= 与本次 --prompt 一致；"
      + "禁止改读其它 taskId / results/ / download/ 里同名或带 (1)(2) 后缀的文件。",
  );
  console.log(
    "[CLI] 交付用户：将 stdout 中 agentResult.value 原文交给用户（禁止概括）；"
      + "stdout 被截断时读 reportFile= 兜底。禁止读取 reportFullFile= / download/ 附件向用户展示。",
  );
  console.log(
    "[CLI] reportFullFile= 仅表示附件已静默下载到本地，供用户自行打开，不是 Agent 交付正文。",
  );
  if (lastReportFilePath) {
    console.log(
      "[CLI] 路径区分：reportFile= 指向 ~/.wind-alice/results/（agentResult 摘要副本，"
        + "不是完整报告）；禁止对用户说「完整报告在 results/」。",
    );
  }
  if (lastReportFullFilePath) {
    console.log(
      `[CLI] 路径区分：reportFullFile= 才是完整报告附件（工作空间 process.cwd()）：${lastReportFullFilePath}`,
    );
    console.log(
      "[CLI] Agent 必须把上述 reportFullFile= 绝对路径转告用户；"
        + "禁止只说「已下载」「可本地查阅」而不写路径。",
    );
    console.log(
      `ALICE_USER_DOWNLOAD_HINT=完整报告已保存到：${lastReportFullFilePath}`,
    );
  } else {
    // 显式标记本次服务端未返回任何可下载附件，提醒 Agent 不要编造「完整报告已保存」文案。
    // 解决现场问题：服务端没返回附件时，Agent 仍把 results/<taskId>.md（agentResult 落盘副本）
    // 当成「完整报告路径」转告用户——那是临时落盘文件，不是完整报告。
    console.log(
      "[CLI] 本次服务端未返回可下载的完整报告附件（reportFullFile 为空）。",
    );
    console.log(
      "[CLI] Agent 交付时：只把 stdout 中 agentResult.value 原文呈现给用户；"
        + "禁止向用户提示任何「报告已保存到 / 完整报告在 ... 路径」文案，"
        + "更禁止把 reportFile=（results/ 落盘副本）当成完整报告路径转告用户。",
    );
    console.log("ALICE_NO_DOWNLOADABLE_REPORT=1");
  }
}

/** @internal 单测：读取本进程 DONE 状态 */
export function __getAnalysisDoneStateForTesting() {
  return {
    emitted: analysisDoneEmitted,
    reportFile: lastReportFilePath,
    reportFullFile: lastReportFullFilePath,
    taskId: lastDoneTaskId,
    promptHash: lastDonePromptHash,
  };
}

/** @internal 单测：重置 DONE / strict 状态 */
export function __resetAnalysisDoneStateForTesting() {
  analysisDoneEmitted = false;
  strictRequired = false;
  strictDisabled = false;
  lastReportFilePath = null;
  lastReportFullFilePath = null;
  lastDoneTaskId = null;
  lastDonePromptHash = null;
}

/** @internal 单测：把 promptHash 推入 rememberDonePromptHash 状态 */
export function __rememberDonePromptHashForTesting(promptHash) {
  return rememberDonePromptHash(promptHash);
}

/** @internal 单测：直接调用 emitAnalysisDone（绕开主流程入口） */
export function __emitAnalysisDoneForTesting(opts) {
  return emitAnalysisDone(opts);
}

/** @internal 单测：把 path 推入 rememberReportFile 状态 */
export function __rememberReportFileForTesting(path) {
  return rememberReportFile(path);
}

/** @internal 单测：把 path 推入 rememberReportFullFile 状态 */
export function __rememberReportFullFileForTesting(path) {
  return rememberReportFullFile(path);
}

/** 主流程调用：声明本次进程必须打出 DONE，否则 strict 模式会改 exit 码。 */
function markStrictRequired() {
  strictRequired = true;
}

/** 单进程仅注册一次 exit hook：strict 模式兜底校验。 */
let strictExitHookInstalled = false;
function installStrictExitHook() {
  if (strictExitHookInstalled) return;
  strictExitHookInstalled = true;
  process.on("exit", () => {
    if (!strictRequired || strictDisabled) return;
    if (analysisDoneEmitted) return;
    const code = process.exitCode;
    if (code != null && code !== 0) return;
    process.exitCode = EXIT_STRICT_NO_DONE;
    try {
      console.error(
        "[CLI][strict] 进程退出但未输出 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE；强制退出码="
          + EXIT_STRICT_NO_DONE
          + "。",
      );
      console.error(
        "[CLI][strict] 典型原因：① 被沙箱 / IDE 终端强制结束；② 异常路径未触达完成出口。",
      );
      console.error(
        "[CLI][strict] 任务可能仍在服务端执行，请用相同 prompt 加 --no-wait 续接；不要直接当成成功。",
      );
    } catch {}
  });
}

export class ServerUserNotice extends Error {
  constructor(info = {}) {
    const messages = info.messages ?? [];
    super(messages[0] || "SERVER_USER_NOTICE");
    this.name = "ServerUserNotice";
    this.kind = info.kind ?? "generic";
    this.messages = messages;
    this.primaryMessage = info.primaryMessage ?? messages[0] ?? "SERVER_USER_NOTICE";
    this.exitCode = info.exitCode ?? EXIT_SERVER_NOTICE;
    this.noRetry = info.noRetry ?? false;
  }
}

/** @deprecated 兼容旧导出名称 */
export class WindTrialQuotaExceeded extends ServerUserNotice {
  constructor() {
    super();
    this.name = "WindTrialQuotaExceeded";
  }
}

/** @deprecated 兼容旧导出名称 */
export class WindServiceBusy extends ServerUserNotice {
  constructor() {
    super();
    this.name = "WindServiceBusy";
  }
}

const SERVER_NOTICE_CHANNEL_MARKERS = ["A2A.Markdown", "UIState"];
const TERMINAL_STATUS_STATES = new Set(["failed", "canceled", "rejected"]);

// 服务端用户可见提示的退出码：75 = 临时性失败（并发上限 / 服务繁忙 / 积分不足），智能体应停止重试并等待
const EXIT_SERVER_TEMPORARY = 75;
const EXIT_SERVER_NOTICE = 1;

// --no-wait 探针模式专用退出码：
// - 4 = 服务端任务仍在执行中（status: working / submitted），且已达 CLI 全过程自旋上限
// - 5 = 本地 tasks.json 找不到对应 promptHash 的 running 记录，需要先用普通模式提交一次
const EXIT_PROBE_STILL_RUNNING = 4;
const EXIT_PROBE_NO_TASK = 5;

// strict 模式专用退出码：
// - 6 = 进程退出时未输出 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE，且 exitCode 仍为 0；
//   典型于进程被沙箱 / IDE 终端强制结束、信号兜底未触发的场景。strict 模式（默认开启）
//   会把它强制改成 6，避免 Agent 把"被杀进程"误判为成功完成。
const EXIT_STRICT_NO_DONE = 6;

// 重复提交防护退出码：
// - 76 = 检测到 N 分钟内已有相似 prompt 的 running 任务，疑似 Agent 换 prompt 重试；
//   要绕过请加 --new，或用相同 prompt 加 --no-wait 续接已有任务。
const EXIT_DUPLICATE_LIKELY = 76;

// check-conflict 子命令专用退出码：
// - 11 = 检测到可能冲突的 running 任务（同 promptHash 或相似 prompt），Agent 必须
//   把详情列给用户、由用户在 attach / --new / cancel 三选项中决定。
//   不消耗服务端额度（纯本地 registry 检查，不发请求）。
const EXIT_CONFLICT_DETECTED = 11;

// check-conflict：24h 内已有相似 completed 任务，可重放而非新建（多 Agent 串台防护）。
const EXIT_REPLAY_AVAILABLE = 12;

// status 子命令：本地无此 prompt 记录，但存在相似已完成任务——禁止扫 download/ 误读。
const EXIT_STATUS_MISLEAD_RISK = 77;

// 沙箱环境持久化失败：tasks.json 不可写（EPERM / 权限不足），阻止提交以防重复扣积分。
// Agent 应告知用户开启完全访问权限或换用支持持久化的环境。
const EXIT_SANDBOX_NO_PERSIST = 78;

// 重复提交防护：在多大时间窗口内对 running 任务做相似 prompt 检查。
const DUPLICATE_GUARD_WINDOW_MS = 10 * 60 * 1000;

// check-conflict 对 completed 任务的 replay 检查窗口（与 duplicateGuard 默认一致）。
const CONFLICT_CHECK_REPLAY_WINDOW_MS = DEFAULT_REPLAY_GUARD_WINDOW_MS;

// --no-wait 模式下 tasks/get HTTP 请求超时（毫秒）。
// 探针必须快返，所以即使服务端网络抖动也要尽快退出让上层重试。
const PROBE_HTTP_TIMEOUT_MS = 15 * 1000;

// --no-wait 内部自旋（原 --watch）默认参数。
// - 自 vNext：`--no-wait` **默认**开启内部自旋，Agent 无需再叠 `--watch` 或外层 Start-Sleep。
// - `--once`：退化为单次探针（旧版 --no-wait 行为，仅供脚本 / 调试）。
// - WATCH_DEFAULT_INTERVAL_SEC: 两次 probe 之间的 sleep。
// - WATCH_DEFAULT_TIMEOUT_SEC: **每一轮**自旋片段的上限（到点自动续下一轮，不退出）。
// - WATCH_ABSOLUTE_MAX_SEC: 单次 CLI 进程**全过程**自旋上限，触顶才 exit=4。
// - WATCH_MAX_TIMEOUT_SEC: --watch-timeout 用户可配上限（单轮）。
// - WATCH_MIN_INTERVAL_SEC: 防御性下限，避免一秒一 probe 把服务端打爆。
const WATCH_DEFAULT_INTERVAL_SEC = 60;
const WATCH_DEFAULT_TIMEOUT_SEC = 30 * 60;
const WATCH_ABSOLUTE_MAX_SEC = 60 * 60;
const WATCH_MAX_TIMEOUT_SEC = 30 * 60;
const WATCH_MIN_INTERVAL_SEC = 5;

// 渐进式探针间隔（accelerating probe）：任务运行越久，越接近完成，探针间隔逐步缩短。
// - 前期（0~3min）  60s 间隔：任务大概率在排队/初始化，密集探针无意义
// - 中期（3~8min）  30s 间隔：任务已 working，需要更及时感知状态变化
// - 后期（8min+）   15s 间隔：任务大概率接近完成，缩短感知延迟
const PROBE_ACCEL_TIERS = [
  { afterSec: 8 * 60, intervalSec: 15 },
  { afterSec: 3 * 60, intervalSec: 30 },
  { afterSec: 0,       intervalSec: 60 },
];

/**
 * 根据任务已运行时间，按 PROBE_ACCEL_TIERS 返回渐进缩短的探针间隔（秒）。
 * 运行越久 → 间隔越短 → 越快感知到服务端 completed。
 *
 * 规则：
 * - 渐进 tier 的 intervalSec 只在 **低于** baseInterval 时才缩短（不会比用户设定更长）；
 * - 渐进缩短的下限受 WATCH_MIN_INTERVAL_SEC 保护；
 * - 用户显式传入较大 --watch-interval 时，渐进 tier 不会覆盖用户意图（tier 更大时取 baseInterval）。
 *
 * @param {number} elapsedMs  任务已运行毫秒数
 * @param {number} baseInterval 用户传入或默认的基础间隔（秒）
 * @returns {number} 本轮探针后应 sleep 的秒数
 */
export function getAcceleratedIntervalSec(elapsedMs, baseInterval) {
  const elapsedSec = elapsedMs / 1000;
  for (const tier of PROBE_ACCEL_TIERS) {
    if (elapsedSec >= tier.afterSec) {
      // 渐进间隔比用户设定短 → 缩短（加速感知）；比用户设定长 → 保留用户值
      const accelerated = Math.min(tier.intervalSec, baseInterval);
      return Math.max(WATCH_MIN_INTERVAL_SEC, accelerated);
    }
  }
  return baseInterval;
}

// 按文案关键词归类服务端提示，用于决定退出码与是否禁止智能体立即重试
const SERVER_NOTICE_CLASSIFIERS = [
  {
    kind: "concurrency",
    patterns: [
      /最大同步执行任务/,
      /同步执行任务数目/,
      /并发.*限制/,
      /请等待其他任务执行完成/,
      /Maximum concurrent tasks limit/i,
      /Please wait for other tasks to complete/i,
    ],
    noRetry: true,
  },
  {
    kind: "busy",
    patterns: [/服务繁忙/, /系统繁忙/, /请稍后重试/],
    noRetry: true,
  },
  {
    kind: "points",
    patterns: [
      /积分不足/,
      /Points not enough/i,
      /insufficient\s+points/i,
    ],
    noRetry: true,
  },
];

let lastServerUserNoticeInfo = null;

function classifyServerUserNotice(messages) {
  const list = Array.isArray(messages)
    ? messages.map((m) => String(m).trim()).filter(Boolean)
    : [];
  const text = list.join("\n");
  for (const { kind, patterns, noRetry } of SERVER_NOTICE_CLASSIFIERS) {
    if (patterns.some((re) => re.test(text))) {
      return {
        kind,
        messages: list,
        primaryMessage: list[0] || text,
        exitCode: EXIT_SERVER_TEMPORARY,
        noRetry,
      };
    }
  }
  return {
    kind: "generic",
    messages: list,
    primaryMessage: list[0] || "SERVER_USER_NOTICE",
    exitCode: EXIT_SERVER_NOTICE,
    noRetry: false,
  };
}

/**
 * 将服务端用户提示打到 stderr：
 *   - 与"主输出在 stdout（agentResult.value / SSE 正文）"分流，避免被报告正文裹挟；
 *   - 避免在合并显示 stdout+stderr 的终端中出现每条横幅重复打印 2 次的视觉噪声；
 *   - Agent / 上层调用方通常会读 stderr，机器可读标记不会丢失。
 * 并发限制等临时性失败会输出 [严重] 横幅，明确禁止智能体立即换 prompt 重试。
 */
function emitServerUserNoticeBanner(info) {
  const primary = info.primaryMessage || info.messages?.[0] || "服务端返回了提示";
  const lines = [];

  if (info.kind === "concurrency") {
    lines.push(
      "[严重] 并发上限：当前账号下已有任务在执行，达到同时进行的数量上限，本次未能发起。",
      `[严重] 服务端原文：${primary}`,
      "[严重] 请勿立即重试、请勿换 prompt、请勿 --new（都会再占用并发槽）。",
      "[严重] 等该账号下已在执行的任务全部完成后，请用户把刚才的问题再发一遍，用相同 prompt 重跑。",
      `[严重] 退出码=${EXIT_SERVER_TEMPORARY}（临时性失败，非 CLI 故障）。`,
      "[严重] 交付用户：告知「您这边还有别的分析任务正在跑，已达到同时进行的上限，这次没发起。等那些任务完成后，请您把刚才的问题再发一遍，我立刻为您重新分析」；**不要**说「稍等几分钟 / 过会儿重试」（那是服务繁忙的话术）。",
    );
  } else if (info.kind === "busy") {
    lines.push(
      "[严重] 服务繁忙：服务端当前较忙，暂未接受本次任务。",
      `[严重] 服务端原文：${primary}`,
      "[严重] 请勿连续重试或换 prompt；稍后请用户把刚才的问题再发一遍，用相同 prompt 重跑。",
      `[严重] 退出码=${EXIT_SERVER_TEMPORARY}（临时性失败，非 CLI 故障）。`,
      "[严重] 交付用户：告知「服务端现在比较忙，暂时没接上这次请求。请您稍等一会儿，把刚才的问题再发一遍，我立刻为您重新分析」；**不要**说「等已有任务执行完」（那是并发上限的话术）。",
    );
  } else if (info.kind === "points") {
    lines.push(
      "[严重] 积分不足：账户 Alice 积分已用完，本次分析未能发起（非网络/操作出错）。",
      `[严重] 服务端原文：${primary}`,
      "[严重] 充值地址：https://alice.wind.com.cn/settings?tab=recharge （万得 Alice → 设置 → 充值）。",
      "[严重] 充值后请用户把刚才的问题再发一遍，用原 prompt 重新跑（不要由 Agent 自行接着跑）。",
      "[严重] 充值前请勿重试或换 prompt（积分未到账仍会失败，且不退回）。",
      `[严重] 退出码=${EXIT_SERVER_TEMPORARY}（临时性失败，非 CLI 故障）。`,
      "[严重] 交付用户：用温和口语转述——「很抱歉，这次的分析没能跑起来——您的 Alice 积分已用完。烦请您前往 [万得 Alice → 设置 → 充值](https://alice.wind.com.cn/settings?tab=recharge) 充值。充值完成后，请您把刚才的问题再发一遍，我立刻为您重新分析」；链接以「万得 Alice → 设置 → 充值」为可点击文字、URL 为目标，不要把裸 URL 平铺在括号外；不要向用户提退出码 / prompt / CLI 等技术词；不要说「我直接接着跑 / 不用复述」（需用户重新发问）；不要说「等任务执行完」「稍后重试」（那是并发/繁忙话术，积分不足等再久也没用）。",
    );
  } else {
    lines.push(
      "[服务端提示] 接口未返回最终报告，下方为服务端给出的提示文案：",
      ...info.messages.map((msg) => `[服务端提示] ${msg}`),
    );
  }

  for (const line of lines) {
    console.error(line);
  }
}

function raiseServerUserNotice(messages) {
  const info = classifyServerUserNotice(messages);
  lastServerUserNoticeInfo = info;
  serverUserNoticeHandled = true;
  emitServerUserNoticeBanner(info);
  throw new ServerUserNotice(info);
}

function getServerNoticeExitCode() {
  return lastServerUserNoticeInfo?.exitCode ?? EXIT_SERVER_NOTICE;
}

/**
 * 服务端用非 200（如 429/503）+ body 文案拒绝新任务时，识别 body 中的用户提示文案
 * （并发上限 / 服务繁忙 / 积分不足）。命中则打 [严重] 横幅、置退出码（75）、
 * 标记任务 failed 并返回 info（调用方应直接 return）；未命中返回 null，走原 HTTP 错误逻辑。
 */
function handleServerNoticeInErrorBody(errorText, { registry, taskId } = {}) {
  const info = classifyServerUserNotice([errorText]);
  if (info.kind === "generic") return null;
  lastServerUserNoticeInfo = info;
  serverUserNoticeHandled = true;
  emitServerUserNoticeBanner(info);
  if (registry && taskId) registry.markFailed(taskId, info.primaryMessage);
  process.exitCode = info.exitCode;
  return info;
}

function getServerNoticeFailReason() {
  return lastServerUserNoticeInfo?.primaryMessage ?? "server user notice";
}

function eventHasServerNoticeChannel(event) {
  let serialized;
  try {
    serialized = JSON.stringify(event);
  } catch {
    return false;
  }
  return SERVER_NOTICE_CHANNEL_MARKERS.some((marker) =>
    serialized.includes(marker),
  );
}

function isServerUserNoticeEvent(event) {
  const result = event?.result;
  if (!result || result.kind !== "status-update") return false;

  const state = result.status?.state ?? result.state;
  const isFinal = result.status?.final === true || result.final === true;
  const isTerminalState = TERMINAL_STATUS_STATES.has(state);
  const hasNoticeChannel = eventHasServerNoticeChannel(event);

  if (!hasNoticeChannel && !isTerminalState && !isFinal) return false;
  return extractServerUserNoticeTexts(event).length > 0;
}

function pushNoticeText(acc, seen, text) {
  const trimmed = String(text).trim();
  if (!trimmed || seen.has(trimmed)) return;
  seen.add(trimmed);
  acc.push(trimmed);
}

function collectServerNoticeTextParts(value, acc, seen, depth = 0) {
  if (value == null || depth > 24) return;
  if (Array.isArray(value)) {
    for (const item of value) {
      collectServerNoticeTextParts(item, acc, seen, depth + 1);
    }
    return;
  }
  if (typeof value !== "object") return;

  const metaKey = value.metadata?.key;
  const inNoticeChannel =
    metaKey === "A2A.Markdown" ||
    (typeof metaKey === "string" && metaKey.includes("Markdown")) ||
    value.key === "UIState";

  // UIState artifact 内部的 UI 节点形如：
  //   { componentName: "A2A.Markdown", properties: { text: ["..."] }, children: [...] }
  // 服务端就是用这种结构推送终态提示文案（如"今日已超出体验期任务限额"），
  // 这里专门做识别，避免被外层 A2A.Markdown / UIState 兜底逻辑遗漏。
  const componentName = value.componentName;
  if (
    typeof componentName === "string" &&
    (componentName === "A2A.Markdown" || componentName.includes("Markdown"))
  ) {
    const propsText = value.properties?.text;
    if (typeof propsText === "string") {
      pushNoticeText(acc, seen, propsText);
    } else if (Array.isArray(propsText)) {
      for (const item of propsText) {
        if (typeof item === "string") pushNoticeText(acc, seen, item);
      }
    }
  }

  if (value.kind === "text" && typeof value.text === "string") {
    pushNoticeText(acc, seen, value.text);
    return;
  }

  if (inNoticeChannel || value.kind === "data") {
    if (typeof value.data === "string") {
      pushNoticeText(acc, seen, value.data);
    } else if (value.data && typeof value.data === "object") {
      for (const key of ["content", "markdown", "text", "message", "value"]) {
        if (typeof value.data[key] === "string") {
          pushNoticeText(acc, seen, value.data[key]);
        }
      }
    }
  }

  for (const key of Object.keys(value)) {
    collectServerNoticeTextParts(value[key], acc, seen, depth + 1);
  }
}

function extractServerUserNoticeTexts(event) {
  const acc = [];
  const seen = new Set();
  collectServerNoticeTextParts(event?.result?.status?.message, acc, seen);
  if (acc.length > 0) return acc;

  if (eventHasServerNoticeChannel(event)) {
    collectServerNoticeTextParts(event?.result, acc, new Set());
  }
  return acc;
}

function logServerUserNoticeIfPresent(events) {
  if (serverUserNoticeHandled || !Array.isArray(events) || events.length === 0) {
    return;
  }

  for (const ev of events) {
    if (!isServerUserNoticeEvent(ev)) continue;
    const messages = extractServerUserNoticeTexts(ev);
    raiseServerUserNotice(messages);
  }
}

function isKnownServerError(error) {
  return error instanceof ServerUserNotice;
}

const SUBCOMMANDS = new Set([
  "apikey-set",
  "apikey-get",
  "apikey-clear",
  "status",
  "check-conflict",
]);

/** 部分 Agent 终端会把 JS undefined 字面量拼进 argv，过滤以免误解析为位置参数。 */
function sanitizeArgv(argv) {
  return argv.filter((a, i) => i < 2 || (a !== "undefined" && a !== "null"));
}

// 把 --watch-interval / --watch-timeout 这类带数值的可选参数解析成正整数秒。
// 非法 / 缺失返回 undefined（让调用方走默认值），避免把 NaN 塞进 setTimeout。
function parsePositiveIntSeconds(raw) {
  if (raw === undefined || raw === null) return undefined;
  const n = Number.parseInt(String(raw), 10);
  if (!Number.isFinite(n) || n <= 0) return undefined;
  return n;
}

function parseArgs(argv) {
  const args = sanitizeArgv(argv).slice(2);
  const get = (...names) => {
    for (const name of names) {
      const idx = args.indexOf(name);
      if (idx !== -1) return args[idx + 1];
    }
    return undefined;
  };
  const has = (...names) => names.some((n) => args.includes(n));

  const head = args[0];
  const command = head && SUBCOMMANDS.has(head) ? head : undefined;
  const subArg = command ? args[1] : undefined;
  const prompt =
    command === "apikey-set" || command === "apikey-get" || command === "apikey-clear"
      ? undefined
      : get("--prompt", "-p");
  const downloadDir =
    command === "apikey-set" || command === "apikey-get" || command === "apikey-clear"
      ? undefined
      : get("--download-dir", "-d");
  // 只读 / 配置类子命令：所有"行为开关"参数一律强制为 false，避免误带。
  // analysis 主路径（command === undefined）是唯一会真正消费这些开关的入口。
  const forceNew = command ? false : (has("--new") || has("--force-new"));
  // 会话续接策略（默认 opt-in）：
  //   - 默认（都不加）→ 全新会话，contextId 每次新生成，避免跨 Agent / 跨话题污染
  //   - --continue-session → 显式请求延续上次 contextId（在 30min idle window 内）
  //   - --new-session      → 显式强制新建（与默认一致，保留兼容旧脚本；
  //                          与 --continue-session 同时给时 --new-session 胜出）
  //   与 --new 语义不同：--new 只是同一 prompt 重新分析、仍可选择续接会话；
  //   会话续接决定 contextId 是否复用，与 --new 正交。
  const newSession = command ? false : has("--new-session");
  const continueSession = command
    ? false
    : (has("--continue-session") && !newSession);
  // 会话 scope（宿主 Agent 传入的隔离标识，避免 Cursor / Trae 等
  // 宿主共享同一份 current-session.json 而互相污染）。命令行优先，其次环境变量：
  //   --session-scope <id>              → 命令行显式
  //   WIND_ALICE_SESSION_SCOPE=<id>     → 环境变量（wrapper 脚本可统一设置）
  // 命令行值为空白（如 `--session-scope "   "`）时按未传处理，回落到环境变量。
  // 只读 / 配置子命令一律忽略（scope 只影响 analysis 主路径的多轮上下文）。
  // --context-id <id>：显式复用指定 contextId（Agent 从上一轮 DONE 行取），不读不写共享
  // session 文件，同宿主多会话各自带 ID、物理上不串号（推荐）。--new-session 覆盖之。
  const cliExplicitContextId = command ? undefined : get("--context-id");
  const explicitContextId =
    !newSession && typeof cliExplicitContextId === "string"
      ? cliExplicitContextId.trim()
      : "";

  const cliSessionScope = command ? undefined : get("--session-scope");
  const envSessionScope = command ? undefined : process.env.WIND_ALICE_SESSION_SCOPE;
  const cliSessionScopeTrimmed =
    typeof cliSessionScope === "string" ? cliSessionScope.trim() : "";
  const envSessionScopeTrimmed =
    typeof envSessionScope === "string" ? envSessionScope.trim() : "";
  const sessionScope = cliSessionScopeTrimmed || envSessionScopeTrimmed || undefined;
  const noWait = command ? false : has("--no-wait");
  const once = command ? false : has("--once");
  const watchExplicit = command ? false : has("--watch", "-w");
  // --no-wait 默认内部自旋；--once 单次探针；显式 --watch 与默认等价（兼容旧命令）
  const watch = command ? false : noWait && !once;
  const watchIntervalSec = command ? undefined : parsePositiveIntSeconds(get("--watch-interval"));
  const watchTimeoutSec = command ? undefined : parsePositiveIntSeconds(get("--watch-timeout"));
  const watchAbsoluteMaxSec = command ? undefined : parsePositiveIntSeconds(get("--watch-absolute-max"));
  // strict 模式默认开启；只有 analysis 主路径会真正生效（子命令 / 帮助等忽略）。
  // --no-strict：脚本 / 调试场景关闭"必须 emit DONE 才能 exit 0"的兜底。
  const noStrict = command ? false : has("--no-strict");

  return {
    command,
    subArg,
    prompt,
    downloadDir,
    forceNew,
    newSession,
    continueSession,
    explicitContextId,
    sessionScope,
    noWait,
    once,
    watch,
    watchExplicit,
    watchIntervalSec,
    watchTimeoutSec,
    watchAbsoluteMaxSec,
    noStrict,
    help: has("--help", "-h"),
  };
}

/** @internal 单测：解析 argv */
export function __parseArgsForTesting(argv) {
  return parseArgs(argv);
}

function parseDotenv(content) {
  const env = {};
  for (const rawLine of content.split("\n")) {
    let line = rawLine.replace(/^\uFEFF/, "").trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7).trim();
    const eq = line.indexOf("=");
    if (eq <= 0) continue;
    const key = line.slice(0, eq).trim();
    let val = line.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    } else {
      const hashIdx = val.indexOf(" #");
      if (hashIdx >= 0) val = val.slice(0, hashIdx).trim();
    }
    env[key] = val;
  }
  return env;
}

function getApiUrl() {
  return process.env.WIND_ALICE_API_URL || DEFAULT_API_URL;
}

function die(code, message, { extraHint } = {}) {
  const payload = { code, message, ...(extraHint ? { hint: extraHint } : {}) };
  console.error(JSON.stringify(payload, null, 2));
  process.exitCode = 2;
  throw new Error(message);
}

/**
 * 把 Error 及其 cause 链格式化成可读字符串。
 * Node fetch 失败时顶层往往只有 "fetch failed"，真实原因在 e.cause（如 ECONNRESET、ENOTFOUND）。
 *
 * @param {unknown} error 捕获到的异常
 * @returns {string} 含 message 与底层 code/syscall/host 等字段的详情
 */
function formatErrorDetail(error) {
  const parts = [];
  const seen = new Set();
  let current = error;
  let depth = 0;

  while (current != null && depth < 8) {
    if (typeof current !== "object") {
      parts.push(String(current));
      break;
    }
    if (seen.has(current)) break;
    seen.add(current);

    const msg =
      current instanceof Error
        ? current.message
        : typeof current.message === "string"
          ? current.message
          : String(current);

    const extras = [];
    if (current.code) extras.push(`code=${current.code}`);
    if (current.errno != null) extras.push(`errno=${current.errno}`);
    if (current.syscall) extras.push(`syscall=${current.syscall}`);
    if (current.hostname) extras.push(`host=${current.hostname}`);
    if (current.address) {
      const port = current.port != null ? `:${current.port}` : "";
      extras.push(`addr=${current.address}${port}`);
    }

    const suffix = extras.length > 0 ? ` (${extras.join(", ")})` : "";
    parts.push(depth === 0 ? `${msg}${suffix}` : `cause: ${msg}${suffix}`);
    current = current.cause;
    depth += 1;
  }

  return parts.join("；");
}

function getApiKey() {
  const key = readApiKeyOptional();
  if (key) return key;

  die("KEY_MISSING", "WIND_API_KEY 未配置", {
    extraHint:
      `① 获取 API Key：浏览器打开 ${WIND_ALICE_KEY_PAGE}\n` +
      `   （万得 Alice → 左下角头像 → 「设置」→「账户」标签页 → 复制 / 重置 API Key；未登录会先跳转登录页）\n` +
      `② 通过 CLI 写入 Key（推荐，KEY 是裸值不要加引号）：\n` +
      `   node scripts/cli.mjs apikey-set <KEY>\n` +
      `   或手动编辑文件：${KEY_CONFIG_FILE}\n` +
      `   单行内容：WIND_API_KEY=<你的KEY>\n` +
      `③ 重试原命令\n` +
      `（出于安全考虑，仅支持此路径；不支持环境变量、不支持 skill 目录内 config.json。\n` +
      `  历史版本的无后缀 ${LEGACY_KEY_CONFIG_FILE} 仍可读取，但建议用 apikey-set 重新写入以迁移到 config.env）`,
  });
}

/** 读取 API Key；未配置时返回 null（不退出进程）。check-conflict 核实 running 任务时用。 */
function readApiKeyOptional() {
  const path = resolveExistingKeyConfigPath();
  if (!path) return null;
  try {
    const env = parseDotenv(readFileSync(path, "utf8"));
    return env.WIND_API_KEY || null;
  } catch {
    return null;
  }
}

/** 把 Key 脱敏成 `abcd****wxyz` 形式，用于回显校验。 */
function maskKey(key) {
  if (!key) return "";
  const s = String(key);
  if (s.length <= 8) return "*".repeat(s.length);
  return `${s.slice(0, 4)}${"*".repeat(Math.max(4, s.length - 8))}${s.slice(-4)}`;
}

/**
 * 把 Key 写入 ~/.wind-alice/config.env（dotenv: WIND_API_KEY=...）。
 * macOS / Linux 同时把权限收紧到 600，避免被同主机其它用户读取。
 * 如果检测到历史版本的无后缀 ~/.wind-alice/config 仍存在，写入成功后自动删除，
 * 避免出现新旧两份 Key 文件、后续读取语义不一致。
 */
function setApiKey(rawKey) {
  if (rawKey === undefined || rawKey === null) {
    die("INVALID_KEY", "缺少 Key 值", {
      extraHint:
        `用法：node scripts/cli.mjs apikey-set <KEY>\n` +
        `KEY 是裸值，不要加引号或 -p / --prompt 等前缀。`,
    });
    return;
  }
  const key = String(rawKey).trim();
  if (!key) {
    die("INVALID_KEY", "Key 不能为空", {
      extraHint: "用法：node scripts/cli.mjs apikey-set <KEY>",
    });
    return;
  }
  if (key.startsWith("-")) {
    die("INVALID_KEY", `Key 不能以 \"-\" 开头："${rawKey}"`, {
      extraHint:
        "看起来你把选项当成 Key 传入了。KEY 应该是裸值，例如：\n" +
        "  node scripts/cli.mjs apikey-set <YOUR_API_KEY>  # PLACEHOLDER 示例，非真实 Key",
    });
    return;
  }

  try {
    mkdirSync(KEY_CONFIG_DIR, { recursive: true });
    writeFileSync(KEY_CONFIG_FILE, `WIND_API_KEY=${key}\n`, { encoding: "utf8" });
    if (process.platform !== "win32") {
      try { chmodSync(KEY_CONFIG_FILE, 0o600); } catch {}
    }
  } catch (e) {
    die("WRITE_FAILED", `写入 Key 失败：${e.message}`, {
      extraHint: `请检查 ${KEY_CONFIG_DIR} 的写入权限后重试。`,
    });
    return;
  }

  let migratedFrom = null;
  if (existsSync(LEGACY_KEY_CONFIG_FILE)) {
    try {
      unlinkSync(LEGACY_KEY_CONFIG_FILE);
      migratedFrom = LEGACY_KEY_CONFIG_FILE;
    } catch {
      // 删不掉就保留，不影响新文件生效；后续读取会优先 config.env，不会拿到老 Key。
    }
  }

  console.log(JSON.stringify({
    ok: true,
    action: "apikey-set",
    path: KEY_CONFIG_FILE,
    key: maskKey(key),
    ...(migratedFrom ? { migratedFrom } : {}),
    message: migratedFrom
      ? `API Key 已写入；同时清理了历史版本的 ${migratedFrom}。`
      : "API Key 已写入。",
  }, null, 2));
}

/** 打印当前 Key 状态（脱敏），不回显完整 Key。 */
function printApiKeyStatus() {
  const path = resolveExistingKeyConfigPath();
  if (!path) {
    console.log(JSON.stringify({
      status: "missing",
      path: KEY_CONFIG_FILE,
      keyPage: WIND_ALICE_KEY_PAGE,
      hint:
        "① 打开 keyPage 地址，在「设置 → 账户」复制 API Key；" +
        " ② 执行 `node scripts/cli.mjs apikey-set <KEY>` 写入 Key。",
    }, null, 2));
    process.exitCode = 1;
    return;
  }
  let env;
  try {
    env = parseDotenv(readFileSync(path, "utf8"));
  } catch (e) {
    console.log(JSON.stringify({
      status: "error",
      path,
      error: `读取失败：${e.message}`,
    }, null, 2));
    process.exitCode = 1;
    return;
  }
  const key = env.WIND_API_KEY;
  if (!key) {
    console.log(JSON.stringify({
      status: "missing",
      path,
      reason: "config 文件存在但未找到 WIND_API_KEY 字段",
      hint: "执行 `node scripts/cli.mjs apikey-set <KEY>` 重新写入 Key。",
    }, null, 2));
    process.exitCode = 1;
    return;
  }
  const isLegacy = path === LEGACY_KEY_CONFIG_FILE;
  console.log(JSON.stringify({
    status: "configured",
    path,
    key: maskKey(key),
    ...(isLegacy
      ? {
          legacy: true,
          migrationHint:
            `检测到 Key 仍存放在历史路径 ${LEGACY_KEY_CONFIG_FILE}，` +
            `建议执行 \`node scripts/cli.mjs apikey-set <KEY>\` 重新写入，` +
            `CLI 会自动迁移到 ${KEY_CONFIG_FILE} 并删除老文件。`,
        }
      : {}),
  }, null, 2));
}

/**
 * 删除 ~/.wind-alice/config.env，并顺便清理历史版本的 ~/.wind-alice/config，幂等。
 * 任一文件删除失败时，会把失败路径回报给调用方，便于用户手动处理。
 */
function clearApiKey() {
  const targets = [KEY_CONFIG_FILE, LEGACY_KEY_CONFIG_FILE].filter((p) => existsSync(p));
  if (targets.length === 0) {
    console.log(JSON.stringify({
      ok: true,
      action: "apikey-clear",
      path: KEY_CONFIG_FILE,
      message: "Key 文件不存在，无需清除。",
    }, null, 2));
    return;
  }

  const removed = [];
  const failed = [];
  for (const path of targets) {
    try {
      unlinkSync(path);
      removed.push(path);
    } catch (e) {
      failed.push({ path, error: e.message });
    }
  }

  if (failed.length > 0) {
    die("CLEAR_FAILED", `清除 Key 失败：${failed.map((f) => `${f.path} → ${f.error}`).join("; ")}`, {
      extraHint: `请手动删除以下文件后重试：${failed.map((f) => f.path).join(", ")}`,
    });
    return;
  }

  console.log(JSON.stringify({
    ok: true,
    action: "apikey-clear",
    removed,
    message:
      removed.length === 1
        ? "API Key 已清除。"
        : `API Key 已清除（同时清理了 ${removed.length} 个历史/当前配置文件）。`,
  }, null, 2));
}

function buildHeaders(apiKey) {
  const headers = {
    Accept: "application/json, text/event-stream",
    "Content-Type": "application/json",
    "alice-channel": ALICE_CHANNEL,
  };
  if (apiKey) {
    headers.Authorization = `Bearer ${apiKey}`;
  }
  return headers;
}

function resubscribeBody({ taskId, contextId, params }) {
  return {
    jsonrpc: "2.0",
    method: "tasks/resubscribe",
    params: {
      id: taskId || params?.params?.message?.taskId,
      contextId: contextId || params?.params?.message?.contextId,
    },
    id: randomUUID(),
  };
}

/**
 * 构造 A2A 协议中的 `tasks/get` 请求体。与 `tasks/resubscribe` 不同，本接口
 * 返回**单次 JSON 响应**而非 SSE 流，可在沙箱 / Trae 等会强制结束长任务的
 * 环境里被 --no-wait 模式快速调用以同步查询任务最终状态。
 */
function tasksGetBody({ taskId, contextId }) {
  return {
    jsonrpc: "2.0",
    method: "tasks/get",
    params: { id: taskId, contextId },
    id: randomUUID(),
  };
}

/**
 * 构造调用 Alice Agent 的请求体。
 * 始终使用「公司一页纸」技能：
 *   - 文本前缀：`使用「公司一页纸」技能：<原 prompt>`
 *   - chatMode "12" + originalChatMode "4"，不携带 agentCard。
 *
 * @param {string} prompt    用户原始问题
 * @param {object} [opts]
 * @param {string} [opts.reuseContextId] 复用上次 contextId（多轮会话续接）
 */
function buildBody(prompt, { reuseContextId } = {}) {
  const text = `使用「${ALICE_SKILL_NAME_ZH}」技能：${prompt}`;
  const contextId =
    typeof reuseContextId === "string" && reuseContextId.length > 0
      ? reuseContextId
      : randomUUID();
  return {
    jsonrpc: "2.0",
    method: "message/stream",
    params: {
      message: {
        messageId: randomUUID(),
        role: "user",
        kind: "message",
        parts: [
          { kind: "text", text },
          {
            kind: "data",
            data: {
              chatMode: "12",
              originalChatMode: "4",
              switchMode: "auto",
              timezone: "Asia/Shanghai",
            },
            metadata: {
              key: "Wind.WindSearch.ChatService.A2A",
              version: "1.0.0",
            },
          },
        ],
        contextId,
        taskId: randomUUID(),
      },
    },
    id: randomUUID(),
  };
}

/** @internal 单测：暴露 buildBody 以便断言 contextId 复用行为。 */
export function __buildBodyForTesting(prompt, opts) {
  return buildBody(prompt, opts);
}

/**
 * 计算 prompt 的归一化哈希，用于跨进程任务复用查表。
 * 归一化策略（保守）：
 *   - 去除首尾空白（trim）
 *   - 把内部连续空白（含中文全角空格、换行、Tab）折叠成单个 ASCII 空格
 *   - 拼接 skill 名做 namespace，避免不同 skill 同 prompt 误命中
 * 不做大小写折叠 / 标点剥离，保持语义敏感（"宁德时代" vs "宁德时代？" 视为不同任务）。
 */
function normalizePromptForHash(prompt) {
  return String(prompt ?? "").trim().replace(/\s+/g, " ");
}

export function computePromptHash(prompt) {
  const normalized = normalizePromptForHash(prompt);
  const namespaced = `${ALICE_SKILL_NAME_ZH}::${normalized}`;
  return createHash("sha256").update(namespaced, "utf8").digest("hex");
}

/** 启动时打印 prompt / task 标识，避免 Agent 按 mtime 扫 results/ 误读其它任务报告。 */
function printPromptHashMarker(promptHash, taskId) {
  const lines = [
    `PROMPT_HASH=${promptHash}`,
    `PROMPT_HASH_SHORT=${promptHash.slice(0, 12)}`,
  ];
  if (taskId) {
    lines.push(`TASK_ID=${taskId}`);
    lines.push(`RESULTS_FILE_EXPECTED=${join(REGISTRY_PATHS.resultsDir, `${taskId}.md`)}`);
    lines.push(`[CLI] 本次任务的兜底摘要（REPORT_FILE）将写入上述 RESULTS_FILE_EXPECTED。`);
  } else {
    lines.push(
      `[CLI] 并行任务模式下每个 taskId 有独立 results 文件；status 默认展示该 prompt 最新一条任务。`,
    );
  }
  lines.push(`[CLI] 禁止按 results/ 目录修改时间取「最新」文件——那会读到其它任务的报告。`);
  lines.push(
    `[CLI] 禁止扫描 logs/ 挑 .session.log：只读 stdout 的 ALICE_SESSION_LOG=（文件名含完整 promptHash）。`,
  );
  for (const line of lines) {
    console.error(line);
  }
}

/** 续接模式：在 resume 窗口内找最近一条 running 记录。 */
function findAttachableRunning(registry, promptHash, now = Date.now()) {
  for (const record of registry.findAllByPromptHash(promptHash)) {
    if (record.status === "running" && now - record.startedAt < ATTACH_RESUME_WINDOW_MS) {
      return record;
    }
  }
  return null;
}

/** 续接模式：找最近一条可探针对齐的 failed 记录。 */
function findLatestFailedForProbe(registry, promptHash) {
  for (const record of registry.findAllByPromptHash(promptHash)) {
    if (shouldProbeFailedRecord(record)) return record;
  }
  return null;
}

/**
 * 当 tasks.json 无记录时，尝试从 session.log 恢复任务信息。
 *
 * 场景：沙箱环境下 CLI 已向服务端 message/stream 提交任务，但写 tasks.json 时被 EPERM 拦截，
 * 进程异常退出。下次启动时本地无记录，若直接 submit 会重复扣费。
 *
 * 逻辑：
 *   1. 检查 ~/.wind-alice/logs/<promptHash>.session.log 是否存在且最近 60 分钟内修改过
 *   2. 从中提取 taskId / contextId（正则匹配 CLI 输出的标记行）
 *   3. 用 tasks/get 探针确认服务端状态
 *   4. running → 恢复本地记录并返回 attach
 *   5. completed → 恢复本地记录并返回 replay_completed
 *   6. 其它 → 返回 null（不可恢复，走 submit）
 *
 * @returns {Promise<{ action: "attach"|"replay_completed", record: object } | null>}
 */
async function tryRecoverFromSessionLog({
  promptHash,
  prompt,
  url,
  headers,
  apiKey,
  downloadDir,
  registry,
  logPrefix = "[CLI]",
  now = Date.now(),
}) {
  const sessionLogPath = sessionLogPathForPrompt(promptHash);

  // 优先从 preTeeSessionLogCache 获取旧内容（installWindowsSessionLogTee 覆盖前缓存），
  // 因为 main() 中 installWindowsSessionLogTee 在 tryRecoverFromSessionLog 之前调用，
  // 直接读文件只能拿到被覆盖后的空文件。
  let logContent = getPreTeeSessionLogContent(promptHash);

  let logStat;
  let logPath = sessionLogPath;
  if (logContent) {
    // 从缓存恢复：用当前 session.log 的 stat 获取 mtime（文件已被覆盖但 mtime 反映的是旧写入时间之前）
    try {
      logStat = statSync(sessionLogPath);
    } catch {}
    console.log(
      `${logPrefix} tasks.json 无记录，但 installWindowsSessionLogTee 在覆盖 session.log 前缓存了旧内容，` +
      `尝试从中恢复任务信息。`,
    );
  } else {
    // 无缓存：回退到直接读文件（非 Windows 或 TTY 模式下 installWindowsSessionLogTee 不覆盖）
    if (!existsSync(sessionLogPath)) return null;
    try {
      logStat = statSync(sessionLogPath);
    } catch {
      return null;
    }
    const SESSION_LOG_RECOVERY_WINDOW_MS = 60 * 60 * 1000;
    if (now - logStat.mtimeMs > SESSION_LOG_RECOVERY_WINDOW_MS) {
      return null;
    }
    try {
      logContent = readFileSync(sessionLogPath, "utf8");
    } catch {
      return null;
    }
  }

  if (!logContent || !logContent.trim()) return null;

  // 只恢复 60 分钟内的 session.log（与 ATTACH_RESUME_WINDOW_MS 对齐）
  const SESSION_LOG_RECOVERY_WINDOW_MS = 60 * 60 * 1000;
  // 对于缓存内容，用缓存时的 mtime 判断时效性
  if (logStat && now - logStat.mtimeMs > SESSION_LOG_RECOVERY_WINDOW_MS) {
    return null;
  }

  // 从 session.log 中提取 taskId / contextId
  // 匹配 CLI 输出格式：
  //   "server taskId    = 019ef893..."   (服务端重绑后)
  //   "client taskId    = 019ef893..."   (首次写入)
  //   "taskId = 019ef893..."             (attach banner)
  const taskIdMatch = logContent.match(/(?:server|client)?\s*taskId\s*=\s*([0-9a-f-]{20,})/i);
  const contextIdMatch = logContent.match(/(?:server|client)?\s*contextId\s*=\s*([0-9a-f-]{20,})/i);
  if (!taskIdMatch) return null;

  const recoveredTaskId = taskIdMatch[1];
  const recoveredContextId = contextIdMatch?.[1] ?? "";

  // ── promptHash 交叉校验 ──
  // session.log 文件名虽按 promptHash 命名，但并发 CLI 进程可能交叉写入，
  // 导致文件内包含其它 prompt 的 taskId。提取 session.log 中所有的
  // PROMPT_HASH / REPORT_PROMPT_HASH / ALICE_SESSION_LOG_PROMPT_HASH 标记，
  // 校验至少有一个与当前 promptHash 一致；否则拒绝恢复。
  const allHashMarkers = logContent.match(/(?:PROMPT_HASH|REPORT_PROMPT_HASH|ALICE_SESSION_LOG_PROMPT_HASH)=([0-9a-f]{20,})/gi);
  const logHashes = allHashMarkers
    ? [...new Set(allHashMarkers.map(m => m.split("=")[1]))]
    : [];
  const hashMatch = logHashes.length === 0 || logHashes.includes(promptHash);
  if (!hashMatch) {
    console.log(
      `${logPrefix} session.log 中的 promptHash 标记 (${logHashes.join(", ")}) ` +
      `与当前 promptHash (${promptHash}) 不一致，拒绝恢复（可能为并发写入交叉污染）。` +
      `将新建任务。`,
    );
    return null;
  }

  console.log(
    `${logPrefix} tasks.json 无记录但发现 session.log（${formatElapsed(now - logStat.mtimeMs)}前），` +
    `尝试从中恢复任务：taskId=${recoveredTaskId}`,
  );

  // 用 tasks/get 探针确认服务端状态
  resetSessionState();
  currentSessionContextId = recoveredContextId;
  const probe = await probeTaskOnce({
    url,
    headers,
    taskId: recoveredTaskId,
    contextId: recoveredContextId,
  });

  if (probe.kind === "working") {
    // 服务端确认仍在执行 → 恢复本地记录并走 attach
    console.log(
      `${logPrefix} session.log 恢复成功：服务端任务仍在执行（state=${probe.state}），已恢复本地记录，将续接（不新建）。`,
    );
    const recoveredRecord = {
      promptHash,
      skill: ALICE_SKILL_NAME_ZH,
      promptPreview: buildPromptPreview(prompt),
      promptNormalized: normalizePromptForGuard(prompt),
      taskId: recoveredTaskId,
      contextId: recoveredContextId,
      status: "running",
      startedAt: logStat.mtimeMs,
      lastSeenAt: now,
      completedAt: null,
      downloadDir: downloadDir || null,
      recoveredFrom: "session_log",
    };
    registry.upsert(recoveredRecord);
    return { action: "attach", record: registry.findByTaskId(recoveredTaskId) || recoveredRecord };
  }

  if (probe.kind === "completed") {
    // 服务端已确认完成 → 恢复本地记录并走 replay
    console.log(
      `${logPrefix} session.log 恢复成功：服务端任务已完成，已恢复本地记录，将重放结果（不新建、不扣积分）。`,
    );
    const recoveredRecord = {
      promptHash,
      skill: ALICE_SKILL_NAME_ZH,
      promptPreview: buildPromptPreview(prompt),
      promptNormalized: normalizePromptForGuard(prompt),
      taskId: recoveredTaskId,
      contextId: recoveredContextId,
      status: "completed",
      startedAt: logStat.mtimeMs,
      completedAt: now,
      lastSeenAt: now,
      downloadDir: downloadDir || null,
      recoveredFrom: "session_log",
    };
    registry.upsert(recoveredRecord);
    // 同步服务端结果到本地
    const ok = await finalizeTaskFromProbeCompleted({
      probe,
      registry,
      taskId: recoveredTaskId,
      promptHash,
      prompt,
      apiKey,
      downloadDir,
      logPrefix,
    });
    if (ok) {
      return { action: "replay_completed", record: registry.findByTaskId(recoveredTaskId) || recoveredRecord };
    }
    // finalize 失败，继续走 submit
    return null;
  }

  // 服务端未找到 / failed / 探针不可用 → 不可恢复
  console.log(
    `${logPrefix} session.log 中的 taskId=${recoveredTaskId} 在服务端状态为 ${probe.kind}，不可恢复，将新建任务。`,
  );
  return null;
}

/**
 * 根据本地 registry 决定主路径动作（--no-wait 与阻塞 SSE 共用）。
 *
 * 默认策略（用户未要求 --new）：
 *   - 无记录 → 新建
 *   - completed → 阻塞 SSE：清除后新建；--no-wait（preferReplayOnCompleted）：重放落盘，不新建
 *   - running → 续接（不新建）
 *   - failed → 先 reconcile；仍 failed 则 abort
 *
 * --new：清除该 prompt 全部本地记录后新建（并行任务；Agent 须 check-conflict 询问用户）。
 *
 * @returns {Promise<
 *   | { action: "submit" }
 *   | { action: "attach", record: object }
 *   | { action: "replay_completed", record: object }
 *   | { action: "abort_failed", record: object | null }
 * >}
 */
async function resolveTaskDispatchPlan({
  registry,
  promptHash,
  prompt,
  forceNew = false,
  url,
  headers,
  apiKey,
  downloadDir,
  logPrefix = "[CLI]",
  preferReplayOnCompleted = false,
}) {
  if (forceNew) {
    registry.remove(promptHash);
    console.log(
      `${logPrefix} --new：已清除该 prompt 的全部本地记录；将新建独立任务（并行消耗服务端额度）。`,
    );
    console.log(
      `${logPrefix} 若已有 running 任务，须先 check-conflict 列给用户并由用户确认后再 --new。`,
    );
    return { action: "submit" };
  }

  let record = registry.findLatestByPromptHash(promptHash);

  if (!record) {
    // 本地无记录时，先尝试从 session.log 恢复（防止 EPERM 导致重复提交）
    const recovered = await tryRecoverFromSessionLog({
      promptHash,
      prompt,
      url,
      headers,
      apiKey,
      downloadDir,
      registry,
      logPrefix,
    });
    if (recovered) return recovered;

    const similarRunning = findSimilarRunning(registry.records, prompt, {
      skipPromptHash: promptHash,
      windowMs: STALE_TASK_THRESHOLD_MS,
    });
    if (similarRunning) {
      console.log(
        `${logPrefix} 检测到同主体相似 prompt 的 running 任务，自动续接（不新建）：taskId=${similarRunning.record.taskId}`,
      );
      console.log(
        `${logPrefix} 匹配方式=${similarRunning.match.kind}；请勿换措辞重试，否则会重复消耗积分。`,
      );
      return { action: "attach", record: similarRunning.record };
    }

    if (preferReplayOnCompleted) {
      const similarCompleted = findSimilarCompleted(registry.records, prompt, {
        skipPromptHash: promptHash,
        windowMs: STALE_TASK_THRESHOLD_MS,
      });
      if (similarCompleted.length > 0) {
        const top = similarCompleted[0];
        console.log(
          `${logPrefix} 检测到同主体相似 prompt 的 completed 任务，自动重放（不提交新任务）：taskId=${top.record.taskId}`,
        );
        console.log(
          `${logPrefix} 匹配方式=${top.match.kind}；若需重新分析，请加 --new。`,
        );
        return { action: "replay_completed", record: top.record };
      }
    }

    console.log(`${logPrefix} 本地无该 prompt 记录，将新建分析任务。`);
    return { action: "submit" };
  }

  if (record.status === "completed") {
    const completedRef =
      typeof record.completedAt === "number" && Number.isFinite(record.completedAt)
        ? record.completedAt
        : record.startedAt;
    const isStale = typeof completedRef === "number" && Date.now() - completedRef > STALE_TASK_THRESHOLD_MS;
    if (isStale) {
      clearCompletedRecordForResubmit(registry, promptHash, { logPrefix });
      console.log(
        `${logPrefix} 本地任务已完成但超过 ${STALE_TASK_THRESHOLD_MS / 60000} 分钟，视为过期，将提交新的分析任务。`,
      );
      return { action: "submit" };
    }
    if (preferReplayOnCompleted) {
      console.log(
        `${logPrefix} 本地任务已完成；--no-wait 直接复用落盘结果（不提交新任务、不消耗新额度）。`,
      );
      console.log(`${logPrefix} 若需对同一 prompt 重新分析，请加 --new。`);
      return { action: "replay_completed", record };
    }
    clearCompletedRecordForResubmit(registry, promptHash, { logPrefix });
    console.log(`${logPrefix} 本地任务已完成，将提交新的分析任务（不复用旧报告）。`);
    return { action: "submit" };
  }

  if (record.status === "running") {
    const isStale = typeof record.startedAt === "number" && Date.now() - record.startedAt > STALE_TASK_THRESHOLD_MS;
    if (isStale) {
      console.log(
        `${logPrefix} 同 prompt 有 running 记录但超过 ${STALE_TASK_THRESHOLD_MS / 60000} 分钟，视为僵尸任务，将新建分析任务。`,
      );
      return { action: "submit" };
    }
    // attach 前先 tasks/get 确认服务端是否其实已完成（防止沙箱杀进程后永远卡在 running）。
    // 本次广钢气体现场：服务端 5 分钟完成，但 CLI 每次都被杀在第一轮 probe 之前，
    // 本地永远停在 running → 下次 attach → 再次被杀。此探针打破死循环。
    const reconciled = await reconcileRunningRecordViaProbe({
      registry,
      promptHash,
      prompt,
      url,
      headers,
      apiKey,
      downloadDir,
      logPrefix,
    });
    if (reconciled === "completed") {
      record = registry.findLatestByPromptHash(promptHash);
      if (record?.status === "completed") {
        console.log(
          `${logPrefix} attach 前探针发现服务端已完成，直接复用落盘结果（不进 SSE、不消耗新额度）。`,
        );
        return { action: "replay_completed", record };
      }
    }
    console.log(
      `${logPrefix} 同 prompt 已有 running 任务，默认续接（不新建）：taskId=${record.taskId}`,
    );
    return { action: "attach", record };
  }

  if (record.status === "failed") {
    const reconciled = await reconcileFailedRecordViaProbe({
      registry,
      promptHash,
      prompt,
      url,
      headers,
      apiKey,
      downloadDir,
      logPrefix,
    });
    if (reconciled === "completed") {
      record = registry.findLatestByPromptHash(promptHash);
      return { action: "replay_completed", record };
    }
    if (reconciled === "failed" || reconciled === "unchanged") {
      return { action: "abort_failed", record: registry.findLatestByPromptHash(promptHash) };
    }
    record = registry.findLatestByPromptHash(promptHash);
    if (record?.status === "running") {
      console.log(
        `${logPrefix} failed 记录在服务端仍在执行，续接：taskId=${record.taskId}`,
      );
      return { action: "attach", record };
    }
    if (record?.status === "completed") {
      clearCompletedRecordForResubmit(registry, promptHash, { logPrefix });
      console.log(`${logPrefix} reconcile 后任务已完成，将提交新的分析任务。`);
      return { action: "submit" };
    }
    return { action: "abort_failed", record };
  }

  console.log(`${logPrefix} 未知本地状态，将新建分析任务。`);
  return { action: "submit" };
}

/** @internal 单测：仅根据本地 record 状态推断动作（不含 reconcile 网络探针） */
export function __planTaskDispatchFromLocalRecordForTesting(record, { forceNew = false } = {}) {
  if (forceNew) return { action: "submit" };
  if (!record) return { action: "submit" };
  if (record.status === "completed") return { action: "submit" };
  if (record.status === "running") return { action: "attach" };
  if (record.status === "failed") return { action: "reconcile_failed" };
  return { action: "submit" };
}

/** @internal 单测 */
export async function __resolveTaskDispatchPlanForTesting(opts) {
  return resolveTaskDispatchPlan(opts);
}

export async function __tryRecoverFromSessionLogForTesting(opts) {
  return tryRecoverFromSessionLog(opts);
}

function printArtifactGuardHints({ prompt, promptHash, registry, downloadDir, kind = "no_local_record" }) {
  const lines = buildArtifactGuardLines({ prompt, promptHash, registry, downloadDir, kind });
  for (const line of lines) {
    console.log(line);
  }
}

/** 任务仍在执行时提醒 Agent 勿误读 download/ 旧报告（新提交 / 续接 / 轮询 / status 共用）。 */
function printAwaitingResultArtifactGuard({ prompt, promptHash, registry, downloadDir }) {
  printArtifactGuardHints({
    prompt,
    promptHash,
    registry,
    downloadDir: resolveDownloadDir(downloadDir),
    kind: "awaiting_result",
  });
}

/**
 * 从 ~/.wind-alice/results/<taskId>.md 读取 agentResult 正文（跳过 HTML 注释头与 BOM）。
 * @returns {string|null}
 */
function readAgentResultBodyFromSavedFile(filePath) {
  if (!filePath || !existsSync(filePath)) return null;
  try {
    let text = readFileSync(filePath, "utf8");
    if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
    const lines = text.split(/\r?\n/);
    while (lines.length > 0) {
      const trimmed = lines[0].trim();
      if (!trimmed || trimmed.startsWith("<!--")) {
        lines.shift();
        continue;
      }
      break;
    }
    const body = lines.join("\n").trim();
    return body || null;
  } catch {
    return null;
  }
}

/**
 * 重放 tasks.json 中 completed 任务的落盘路径（不访问服务端）。
 * 若存在 resultPath，会把 agentResult.value 重新打印到 stdout，避免 Agent 误读 results/ 并自行概括。
 * runProbeStep / status 子命令 / completed 短路复用共用。
 */
function replayCompletedArtifacts({ registry, taskId, promptHash, logPrefix = "[CLI]" }) {
  const record = taskId
    ? registry.findByTaskId(taskId)
    : registry.findLatestByPromptHash(promptHash);
  if (!record || record.status !== "completed") return false;

  rememberDoneTaskId(record.taskId);
  rememberDonePromptHash(record.promptHash);
  const verifyLines = [
    `REPORT_TASK_ID=${record.taskId}`,
    `REPORT_PROMPT_HASH=${record.promptHash}`,
  ];
  if (record.promptPreview) {
    verifyLines.push(`REPORT_PROMPT_PREVIEW=${record.promptPreview}`);
  }
  verifyLines.push(
    `${logPrefix} 读取报告前必须核对 REPORT_PROMPT_HASH 与本次 PROMPT_HASH 一致；不一致即误读其它任务。`,
  );
  for (const line of verifyLines) {
    console.error(line);
  }

  if (record.resultPath) {
    rememberReportFile(record.resultPath);
    const body = readAgentResultBodyFromSavedFile(record.resultPath);
    if (body) {
      agentResultSeen = true;
      console.log(formatValueOutput(body));
      console.log(
        `${logPrefix} [重放] 已将落盘 agentResult.value 重新打印到 stdout；请直接读 stdout 原样交付，禁止 view_files results/ 或自行概括。`,
      );
    }
    const lines = [
      `REPORT_FILE=${record.resultPath}`,
      `${logPrefix} REPORT_FILE 是 agentResult.value 落盘副本（stdout 截断时 Agent 可读此文件正文交付用户）：`,
      `${logPrefix}   ${record.resultPath}`,
    ];
    for (const line of lines) {
      console.error(line);
    }
  } else {
    console.log(`${logPrefix} 本地未保存 agentResult 兜底文件（旧版本任务）。`);
  }

  const downloadedFiles = registry.getDownloadedFiles(record.taskId);
  if (downloadedFiles.length > 0) {
    const mdFiles = downloadedFiles.filter((e) => /\.md$/i.test(e.path));
    const present = mdFiles.filter((e) => existsSync(e.path));
    const missing = mdFiles.filter((e) => !existsSync(e.path));

    if (present.length > 0) {
      console.log(`${logPrefix} 已登记的完整报告附件（跨进程复用，未重新下载）：`);
      for (const { path: absPath, filename } of present) {
        console.log(`  - ${filename ?? absPath}`);
        console.log(`    ${absPath}`);
        printReportFullFileTag(absPath, {
          reused: true,
          taskId: record.taskId,
          promptHash: record.promptHash,
        });
      }
    }
    if (missing.length > 0) {
      console.log(`${logPrefix} 警告：以下附件曾下载但本地已不存在：`);
      for (const { path: absPath, filename } of missing) {
        console.log(`  - ${filename ?? absPath} → ${absPath}`);
      }
      console.log(`${logPrefix} 如需完整报告，请加 --new 重新跑任务。`);
    }
  } else {
    console.log(
      `${logPrefix} tasks.json 未登记完整报告附件；如需正文请加 --new 重新跑任务。`,
    );
  }
  return true;
}

/**
 * 用户再次对同一 prompt 发起完整分析时，清除本地 completed 记录以便重新提交。
 * 仅查询历史落盘路径请用 `status` 子命令或 `--no-wait --once`。
 *
 * @returns {boolean} 是否清除了 completed 记录
 */
function clearCompletedRecordForResubmit(registry, promptHash, { logPrefix = "[CLI]" } = {}) {
  const existing = registry.findLatestByPromptHash(promptHash);
  if (existing?.status !== "completed") return false;
  console.log(
    `${logPrefix} 本地已有 completed 记录；按用户本次指令重新提交分析任务。`,
  );
  console.log(
    `${logPrefix} 若只需查询历史落盘路径，请用：alice-company-one-page-investment-memo status -p "<同一问题>"`,
  );
  const staleMd = (registry.getDownloadedFiles(existing.taskId) ?? []).filter((e) =>
    /\.md$/i.test(e.path ?? ""),
  );
  if (staleMd.length > 0) {
    console.log(
      `${logPrefix} 将提交新分析任务；以下旧报告附件**禁止**当作本次结果：`,
    );
    for (const { path: stalePath } of staleMd) {
      console.log(`STALE_REPORT_CANDIDATE path=${stalePath} reason=resubmit_same_prompt`);
    }
  }
  registry.removeByTaskId(existing.taskId);
  return true;
}

function buildPromptPreview(prompt) {
  const normalized = normalizePromptForHash(prompt);
  return normalized.length > 80 ? normalized.slice(0, 80) + "…" : normalized;
}

/**
 * 在"新建任务"动作发生前调用，检测时间窗口内是否已有相似 prompt 的 running 任务。
 *
 * 命中且未带 --new 时：
 *   - 把引导文字写到 stderr；
 *   - 设置 process.exitCode = EXIT_DUPLICATE_LIKELY(76)；
 *   - 返回 true，调用方应立即 return 终止后续提交。
 *
 * 未命中或显式 --new 时返回 false，主流程照常继续。
 *
 * 注意：同 promptHash 的 running 记录被自动跳过（这种 case 主流程应走 attach /
 * continue 续接，不算"重复提交"）。
 *
 * @returns {boolean} true=已触发防护并设置好退出码，调用方应 return
 */
async function enforceDuplicateGuard({
  registry,
  prompt,
  promptHash,
  forceNew,
  url,
  headers,
  apiKey,
}) {
  if (forceNew) return false;
  const hit = findSimilarRunning(registry.records, prompt, {
    skipPromptHash: promptHash,
    windowMs: STALE_TASK_THRESHOLD_MS,
  });
  if (!hit) return false;
  const outcome = await reconcileRunningRecordIfStale(registry, hit.record, {
    url,
    headers,
    apiKey,
    prompt,
    promptHash,
    logPrefix: "[CLI][duplicate-guard]",
  });
  if (outcome !== "still_running" && outcome !== "probe_skipped") {
    return false;
  }
  const lines = buildDuplicateGuardMessage({
    prompt,
    existing: registry.findByTaskId(hit.record.taskId) ?? hit.record,
    match: hit.match,
  });
  for (const line of lines) console.error(line);
  process.exitCode = EXIT_DUPLICATE_LIKELY;
  return true;
}

function isCompletedRecordWithinWindow(record, now, windowMs) {
  if (!record || record.status !== "completed") return false;
  const ref =
    typeof record.completedAt === "number" && Number.isFinite(record.completedAt)
      ? record.completedAt
      : record.startedAt;
  if (typeof ref !== "number" || !Number.isFinite(ref)) return false;
  // 过期阈值优先于传入的窗口：超过 STALE_TASK_THRESHOLD_MS 的记录不再作为重放候选
  const effectiveWindow = Math.min(windowMs, STALE_TASK_THRESHOLD_MS);
  return now - ref <= effectiveWindow;
}

/**
 * check-conflict 用的 replay 候选：相似 completed + 同 promptHash 的本地 completed（后者曾被 skipPromptHash 漏检）。
 */
function buildReplayCandidatesForCheckConflict({
  registry,
  prompt,
  promptHash,
  now,
  windowMs,
}) {
  const similar = findSimilarCompleted(registry.records, prompt, {
    skipPromptHash: promptHash,
    now,
    windowMs: Math.min(windowMs, STALE_TASK_THRESHOLD_MS),
  });
  const exactLocal = registry.findLatestByPromptHash(promptHash);
  if (
    exactLocal &&
    isCompletedRecordWithinWindow(exactLocal, now, windowMs) &&
    !similar.some((c) => c.record?.taskId === exactLocal.taskId)
  ) {
    return [{ record: exactLocal, match: { kind: "exact", score: 1 } }, ...similar];
  }
  return similar;
}

/**
 * check-conflict 专用：纯本地检测 session.log + results 残留。
 * 当 tasks.json 无记录（沙箱 EPERM 等）但磁盘上有 session.log 和对应 results 文件时，
 * 推断该 prompt 可能有可重放的 completed 结果，无需发网络请求。
 *
 * @returns {{ taskId: string, resultPath: string|null } | null}
 */
function detectSessionLogReplayCandidate({ promptHash, now = Date.now() }) {
  const SESSION_LOG_RECOVERY_WINDOW_MS = 60 * 60 * 1000;
  const logPath = sessionLogPathForPrompt(promptHash);
  if (!logPath || !existsSync(logPath)) return null;

  let logStat;
  try {
    logStat = statSync(logPath);
  } catch {
    return null;
  }
  // session.log 必须在恢复窗口内（与 tryRecoverFromSessionLog 一致）
  if (now - logStat.mtimeMs > SESSION_LOG_RECOVERY_WINDOW_MS) return null;

  // 也检查 preTeeSessionLogCache（installWindowsSessionLogTee 覆盖前的旧内容）
  let logContent = getPreTeeSessionLogContent(promptHash);
  if (!logContent) {
    try {
      logContent = readFileSync(logPath, "utf8");
    } catch {
      return null;
    }
  }
  if (!logContent || !logContent.trim()) return null;

  // 从 session.log 提取 taskId
  const taskIdMatch = logContent.match(/(?:server|client)?\s*taskId\s*=\s*([0-9a-f-]{20,})/i);
  if (!taskIdMatch) return null;
  const taskId = taskIdMatch[1];

  // promptHash 交叉校验（与 tryRecoverFromSessionLog 一致）：
  // 防止并发写入交叉污染导致提取到其它 prompt 的 taskId
  const allHashMarkers = logContent.match(/(?:PROMPT_HASH|REPORT_PROMPT_HASH|ALICE_SESSION_LOG_PROMPT_HASH)=([0-9a-f]{20,})/gi);
  const logHashes = allHashMarkers
    ? [...new Set(allHashMarkers.map(m => m.split("=")[1]))]
    : [];
  if (logHashes.length > 0 && !logHashes.includes(promptHash)) {
    return null;
  }

  // 检查 results/<taskId>.md 是否存在（推断服务端已完成）
  const resultsDir = REGISTRY_PATHS.resultsDir;
  const resultPath = join(resultsDir, `${taskId}.md`);
  if (!existsSync(resultPath)) {
    // 有 session.log 但无 results → 可能仍在 running（沙箱 EPERM 导致 tasks.json 丢失）
    // 返回一个 resultPath=null 的候选，让 check-conflict 报 exit=11（可能冲突）
    return { taskId, resultPath: null, mtimeMs: logStat?.mtimeMs ?? null };
  }

  return { taskId, resultPath, mtimeMs: logStat?.mtimeMs ?? null };
}

/** 把秒数渲染成"5m12s" / "2h08m" 等紧凑字符串。 */
function formatElapsedSeconds(elapsedSec) {
  const s = Math.max(0, Math.round(elapsedSec));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m${(s % 60).toString().padStart(2, "0")}s`;
  return `${Math.floor(s / 3600)}h${Math.floor((s % 3600) / 60)
    .toString()
    .padStart(2, "0")}m`;
}

/** 把 prompt preview 截断到 maxLen，超出加省略号；用于 stdout 一行打印。 */
function truncateForLine(text, maxLen = 80) {
  const s = String(text ?? "");
  if (s.length <= maxLen) return s;
  return s.slice(0, maxLen - 1) + "…";
}

/**
 * 核实本地 status=running 的任务是否已在磁盘或服务端完成；若已完成则修正 registry。
 *
 * @returns {Promise<'still_running'|'reconciled_completed'|'reconciled_failed'|'reconciled_removed'|'probe_skipped'|'stale_ignored'>}
 */
async function reconcileRunningRecordIfStale(registry, record, opts = {}) {
  if (!record || record.status !== "running") {
    return "still_running";
  }
  const now = Date.now();
  if (typeof record.startedAt === "number" && now - record.startedAt > STALE_TASK_THRESHOLD_MS) {
    return "stale_ignored";
  }

  const taskId = record.taskId;
  const localResultPath = join(REGISTRY_PATHS.resultsDir, `${taskId}.md`);
  if (existsSync(localResultPath)) {
    const r = registry.findByTaskId(taskId);
    if (r && r.status !== "completed") {
      r.status = "completed";
      r.completedAt = typeof r.completedAt === "number" ? r.completedAt : now;
      r.lastSeenAt = now;
      r.resultPath = localResultPath;
      registry.save();
    }
    const logPrefix = opts.logPrefix ?? "[CLI][conflict-reconcile]";
    console.log(
      `${logPrefix} 本地 running 记录已有 results 落盘，已修正为 completed：taskId=${taskId}`,
    );
    return "reconciled_completed";
  }

  const { url, headers, apiKey, prompt, promptHash, downloadDir, logPrefix = "[CLI][conflict-reconcile]" } =
    opts;
  if (!apiKey || !url || !headers || !record.contextId) {
    return "probe_skipped";
  }

  const probe = await probeTaskOnce({
    url,
    headers,
    taskId,
    contextId: record.contextId,
  });

  if (probe.kind === "completed") {
    await finalizeTaskFromProbeCompleted({
      probe,
      registry,
      taskId,
      promptHash: record.promptHash ?? promptHash,
      prompt: record.promptNormalized || record.promptPreview || prompt,
      apiKey,
      downloadDir,
      logPrefix,
    });
    return "reconciled_completed";
  }
  if (probe.kind === "failed") {
    registry.markFailed(taskId, probe.reason ?? `服务端终态：${probe.state}`);
    console.log(`${logPrefix} 服务端已失败，已修正本地记录：taskId=${taskId}`);
    return "reconciled_failed";
  }
  if (probe.kind === "error" && isTaskNotFoundProbe(probe)) {
    registry.removeByTaskId(taskId);
    console.log(`${logPrefix} 服务端已无此 taskId，已清除本地 running 记录：taskId=${taskId}`);
    return "reconciled_removed";
  }
  if (probe.kind === "working") {
    return "still_running";
  }

  console.log(
    `${logPrefix} 无法核实任务状态（${probe.reason ?? probe.kind}），仍视为 running：taskId=${taskId}`,
  );
  return "probe_skipped";
}

/**
 * 对 check-conflict / duplicate-guard 命中的 running 记录逐一核实；已完成的从冲突列表剔除。
 */
async function reconcileRunningConflictsBeforeReport({
  registry,
  exactMatches,
  similarHit,
  prompt,
  promptHash,
  downloadDir,
}) {
  const apiKey = readApiKeyOptional();
  const url = getApiUrl();
  const headers = apiKey ? buildHeaders(apiKey) : null;
  const reconcileOpts = { url, headers, apiKey, prompt, promptHash, downloadDir };

  const stillExact = [];
  for (const r of exactMatches) {
    const outcome = await reconcileRunningRecordIfStale(registry, r, reconcileOpts);
    if (outcome === "still_running" || outcome === "probe_skipped") {
      stillExact.push(registry.findByTaskId(r.taskId) ?? r);
    }
  }

  let stillSimilar = similarHit;
  if (similarHit?.record) {
    const outcome = await reconcileRunningRecordIfStale(registry, similarHit.record, reconcileOpts);
    if (outcome === "still_running" || outcome === "probe_skipped") {
      stillSimilar = {
        record: registry.findByTaskId(similarHit.record.taskId) ?? similarHit.record,
        match: similarHit.match,
      };
    } else {
      stillSimilar = null;
    }
  }

  return { exactMatches: stillExact, similarHit: stillSimilar };
}

/**
 * check-conflict 子命令的核心实现：本地 registry 查询；命中 running 冲突时会核实磁盘/服务端是否已完成。
 *
 * 用途：在主调用前由 Agent 显式预检——同一用户在多个 Agent 中并发调用本技能时，
 * Agent 应该把已有任务列给用户看，由用户决定是续接、并行新建还是取消，而不是
 * 默默 attach（信息不透明）或默默换 prompt 重试（浪费额度）。
 *
 * 检测两类冲突：
 *   1) exact: 同 promptHash + status=running + 30min 内（超过 30min 忽略）
 *   2) similar: 不同 promptHash 但相似 + 30min 内（核实后仍 running 才报冲突）
 *
 * 退出码：
 *   0  无冲突，Agent 可以直接走主调用
 *   2  参数错误（缺 prompt 等，由 main 统一处理）
 *   11 EXIT_CONFLICT_DETECTED：检测到至少一条潜在冲突任务，Agent 必须询问用户
 *
 * 不消耗分析额度（核实 running 时仅 tasks/get 探针，不新建任务）。
 */
async function runCheckConflictCommand({ prompt, downloadDir }) {
  const promptHash = computePromptHash(prompt);
  const registry = openRegistry();
  const now = Date.now();

  let exactMatches = registry.records.filter(
    (r) =>
      r &&
      r.status === "running" &&
      r.promptHash === promptHash &&
      typeof r.startedAt === "number" &&
      now - r.startedAt <= STALE_TASK_THRESHOLD_MS,
  );

  let similarHit = findSimilarRunning(registry.records, prompt, {
    skipPromptHash: promptHash,
    now,
    windowMs: STALE_TASK_THRESHOLD_MS,
  });

  if (exactMatches.length > 0 || similarHit) {
    console.error(
      "[CLI][conflict-check] 检测到 running 冲突候选，正在核实是否已完成（超过 30 分钟的任务已忽略）…",
    );
    const reconciled = await reconcileRunningConflictsBeforeReport({
      registry,
      exactMatches,
      similarHit,
      prompt,
      promptHash,
      downloadDir,
    });
    exactMatches = reconciled.exactMatches;
    similarHit = reconciled.similarHit;
  }

  const replayCandidates = buildReplayCandidatesForCheckConflict({
    registry,
    prompt,
    promptHash,
    now,
    windowMs: CONFLICT_CHECK_REPLAY_WINDOW_MS,
  });

  const runningCount = exactMatches.length + (similarHit ? 1 : 0);
  const replayCount = replayCandidates.length;

  console.error(
    "[CLI][conflict-check] 本命令为预检，不向服务端新建分析。",
  );

  if (runningCount === 0 && replayCount === 0) {
    // 检查跨进程提交锁：另一个 CLI 进程可能正在为同一 prompt 提交/执行任务
    const lockInfo = checkSubmitLock(promptHash);
    if (lockInfo) {
      const elapsedSec = Math.round((Date.now() - lockInfo.startedAt) / 1000);
      const elapsed =
        elapsedSec < 60
          ? `${elapsedSec}s`
          : `${Math.floor(elapsedSec / 60)}m${elapsedSec % 60}s`;
      console.log(
        `ALICE_CONFLICT_CHECK kind=submit_lock pid=${lockInfo.pid} elapsed=${elapsed}`,
      );
      console.log(
        `[CLI][conflict-check] 检测到另一 CLI 进程（PID=${lockInfo.pid}）` +
        `正在为同一 prompt 提交/执行任务（已运行 ${elapsed}）。`,
      );
      console.log(
        "[CLI][conflict-check] Agent 应等待该进程完成后再发主调用，或由用户决定是否并行新建。",
      );
      for (const line of buildDuplicateGuardMessage({
        prompt,
        existing: {
          taskId: `PID:${lockInfo.pid}`,
          promptNormalized: lockInfo.promptPreview || lockInfo.promptNormalized || prompt,
          startedAt: lockInfo.startedAt,
        },
        match: { kind: "submit_lock", score: 1 },
      })) {
        console.error(line);
      }
      process.exitCode = EXIT_CONFLICT_DETECTED;
      return;
    }
    const subjectKey = computeSubjectKey(prompt);
    if (subjectKey) {
      const subjectLockInfo = checkSubjectSubmitLock(subjectKey);
      if (subjectLockInfo) {
        const elapsedSec = Math.round((Date.now() - subjectLockInfo.startedAt) / 1000);
        const elapsed =
          elapsedSec < 60
            ? `${elapsedSec}s`
            : `${Math.floor(elapsedSec / 60)}m${elapsedSec % 60}s`;
        console.log(
          `ALICE_CONFLICT_CHECK kind=subject_submit_lock subject=${subjectKey} pid=${subjectLockInfo.pid} elapsed=${elapsed}`,
        );
        console.log(
          `[CLI][conflict-check] 检测到另一 CLI 进程（PID=${subjectLockInfo.pid}）` +
          `正在为同主体（${subjectKey}）提交/执行任务（已运行 ${elapsed}，措辞可能不同）。`,
        );
        console.log(
          "[CLI][conflict-check] Agent 应等待该进程完成后再发主调用，或由用户决定是否并行新建。",
        );
        for (const line of buildDuplicateGuardMessage({
          prompt,
          existing: {
            taskId: `PID:${subjectLockInfo.pid}`,
            promptNormalized:
              subjectLockInfo.promptPreview || subjectLockInfo.promptNormalized || prompt,
            startedAt: subjectLockInfo.startedAt,
          },
          match: { kind: "subject_submit_lock", score: 1 },
        })) {
          console.error(line);
        }
        process.exitCode = EXIT_CONFLICT_DETECTED;
        return;
      }
    }
    // tasks.json 无记录，但 session.log + results 可能残留（沙箱 EPERM 导致 tasks.json 写入失败时）
    // 纯本地检测：不发网络请求，只看文件是否存在 + 能否解析出 taskId
    const sessionLogReplay = detectSessionLogReplayCandidate({ promptHash, now });
    if (sessionLogReplay) {
      if (sessionLogReplay.resultPath) {
        // 有 results 文件 → completed，可重放
        console.log(
          `ALICE_CONFLICT_CHECK kind=replay_available count=1 promptHash=${promptHash}`,
        );
        console.log(
          `REPLAY_CANDIDATE matchKind=exact score=1.00` +
          ` taskId=${sessionLogReplay.taskId} promptHash=${promptHash}` +
          ` promptPreview=${JSON.stringify(truncateForLine(prompt, 80))}`,
        );
        console.log(`REPLAY_CANDIDATE_REPORT path=${sessionLogReplay.resultPath}`);
        console.error("");
        console.error(
          "[CLI][conflict-check] 本地 tasks.json 无记录，但发现 session.log 与 results 残留" +
          "（可能因沙箱写入限制导致 tasks.json 未持久化）；" +
          "主调用 --no-wait 将自动恢复并重放已有结果（ALICE_NO_SERVER_CALL=1，不访问服务端、不扣积分）。",
        );
        for (const line of buildReplayGuardMessage({
          prompt,
          candidates: [{
            record: {
              taskId: sessionLogReplay.taskId,
              promptHash,
              promptPreview: prompt,
              promptNormalized: prompt,
            },
            match: { kind: "exact", score: 1 },
          }],
        })) {
          console.error(line);
        }
        process.exitCode = EXIT_REPLAY_AVAILABLE;
        return;
      } else {
        // 无 results 文件 → 可能仍在 running（沙箱 EPERM 导致 tasks.json 丢失）
        console.log(
          `ALICE_CONFLICT_CHECK kind=session_log_running count=1 promptHash=${promptHash}`,
        );
        console.log(
          `EXISTING_TASK matchKind=session_log_running taskId=${sessionLogReplay.taskId}` +
          ` promptHash=${promptHash}` +
          ` promptPreview=${JSON.stringify(truncateForLine(prompt, 80))}`,
        );
        console.error("");
        console.error(
          "[CLI][conflict-check] 本地 tasks.json 无记录，但发现 session.log 残留" +
          "（可能因沙箱写入限制导致 tasks.json 未持久化）；" +
          "服务端可能仍有该 prompt 的 running 任务，主调用 --no-wait 将自动续接。",
        );
        for (const line of buildDuplicateGuardMessage({
          prompt,
          existing: {
            taskId: sessionLogReplay.taskId,
            promptHash,
            promptPreview: prompt,
            promptNormalized: prompt,
            startedAt: sessionLogReplay.mtimeMs ?? now,
          },
          match: { kind: "session_log_running", score: 1 },
        })) {
          console.error(line);
        }
        process.exitCode = EXIT_CONFLICT_DETECTED;
        return;
      }
    }

    console.log("ALICE_CONFLICT_CHECK kind=none count=0");
    console.log(
      "[CLI][conflict-check] 本地无 running / completed 记录；主调用 --no-wait 将向服务端新建分析任务。",
    );
    console.log(
      `[CLI][conflict-check] 建议主调用：node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --no-wait`,
    );
    return;
  }

  if (runningCount > 0) {
    // 有 running 冲突：dominantKind 用于让 Agent 一眼区分"已有同任务（attach 候选）"还是
    // "实质相同的相似任务（换 prompt 重试嫌疑）"。两者并存时优先报 exact。
    const dominantKind = exactMatches.length > 0 ? "exact" : "similar";
    console.log(
      `ALICE_CONFLICT_CHECK kind=${dominantKind} count=${runningCount} promptHash=${promptHash}`,
    );

    for (const r of exactMatches) {
      const elapsed = formatElapsedSeconds((now - r.startedAt) / 1000);
      const preview = truncateForLine(r.promptNormalized || r.promptPreview || "", 80);
      console.log(
        `EXISTING_TASK matchKind=exact taskId=${r.taskId ?? "?"}` +
          ` elapsed=${elapsed} promptPreview=${JSON.stringify(preview)}`,
      );
    }
    if (similarHit) {
      const r = similarHit.record;
      const elapsed = formatElapsedSeconds((now - r.startedAt) / 1000);
      const preview = truncateForLine(r.promptNormalized || r.promptPreview || "", 80);
      const score = (similarHit.match?.score ?? 0).toFixed(2);
      const subKind = similarHit.match?.kind ?? "?";
      console.log(
        `EXISTING_TASK matchKind=similar(${subKind}) score=${score}` +
          ` taskId=${r.taskId ?? "?"} elapsed=${elapsed}` +
          ` promptPreview=${JSON.stringify(preview)}`,
      );
    }

    console.error("");
    console.error(
      "[CLI][conflict-check] 核实后仍有运行中任务（未向服务端新建分析，不扣积分）。",
    );
    console.error("[CLI][conflict-check] Agent 必须把上述任务列给用户、由用户三选一：");
    console.error("  ① 续接已有任务（默认行为，推荐，最省额度）：");
    console.error(
      `       node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --no-wait`,
    );
    console.error("  ② 用户确认要并行新建（消耗额外服务端额度）：");
    console.error(
      `       node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --no-wait --new`,
    );
    console.error("  ③ 取消本次提问，让用户先决定后续动作。");
    console.error(
      "[CLI][conflict-check] 同 prompt 已有 running 时，主调用默认自动续接；exit=11 用于 Agent 询问用户是否要 --new 并行新建。",
    );

    process.exitCode = EXIT_CONFLICT_DETECTED;
    return;
  }

  // 无 running 冲突，但有本地 completed 可重放（同 prompt 或相似 prompt）
  console.log(
    `ALICE_CONFLICT_CHECK kind=replay_available count=${replayCount} promptHash=${promptHash}`,
  );
  const hasExactLocalReplay = replayCandidates.some((c) => c.match?.kind === "exact");
  if (hasExactLocalReplay) {
    console.error(
      "[CLI][conflict-check] 本地已有**完全相同 prompt** 的 completed 记录；" +
        "未经用户确认直接 --no-wait 将重放本地结果（ALICE_NO_SERVER_CALL=1，不访问服务端、不扣积分）。",
    );
  }
  for (const { record: r, match } of replayCandidates) {
    const preview = truncateForLine(r.promptNormalized || r.promptPreview || "", 80);
    const score = (match?.score ?? 0).toFixed(2);
    const matchLabel =
      match?.kind === "exact" ? "exact" : `similar(${match?.kind ?? "?"})`;
    console.log(
      `REPLAY_CANDIDATE matchKind=${matchLabel} score=${score}` +
        ` taskId=${r.taskId ?? "?"} promptHash=${r.promptHash ?? "?"}` +
        ` promptPreview=${JSON.stringify(preview)}`,
    );
    const md = (r.downloadedFiles ?? []).find((df) => /\.md$/i.test(df.path ?? ""));
    if (md?.path) {
      console.log(`REPLAY_CANDIDATE_REPORT path=${md.path}`);
      console.log(
        `ALICE_FORBIDDEN_READ_UNTIL_DONE path=${md.path} boundPromptHash=${r.promptHash} currentPromptHash=${promptHash}`,
      );
    }
  }

  console.error("");
  for (const line of buildReplayGuardMessage({ prompt, candidates: replayCandidates })) {
    console.error(line);
  }

  process.exitCode = EXIT_REPLAY_AVAILABLE;
}

/** @internal 单测：直接调用 runCheckConflictCommand 内部使用的格式化函数。 */
export function __formatElapsedSecondsForTesting(s) {
  return formatElapsedSeconds(s);
}

/** @internal 单测：核实 running 记录是否应修正为 completed */
export async function __reconcileRunningRecordIfStaleForTesting(registry, record, opts) {
  return reconcileRunningRecordIfStale(registry, record, opts);
}

function printAbortFailedGuidance(record, logPrefix = "[CLI]") {
  console.error(
    `${logPrefix} 本地 failed 记录在 resume 窗口内，服务端未确认可续接；**禁止**自动重复提交。`,
  );
  if (record?.failReason) {
    console.error(`${logPrefix} 失败原因：${record.failReason}`);
  }
  console.error(
    `${logPrefix} 请用相同 prompt 加 --no-wait 等待结果；用户明确要求并行新建时加 --new --no-wait。`,
  );
}

/**
 * --no-wait 主路径：按 resolveTaskDispatchPlan 结果提交或续接，返回 taskId；null 表示已处理终态应 return。
 */
async function applyNoWaitDispatchPlan({
  plan,
  registry,
  promptHash,
  prompt,
  url,
  headers,
  apiKey,
  downloadDir,
  forceNew,
  newSession = false,
  continueSession = false,
  sessionScope,
  logPrefix = "[CLI]",
}) {
  if (plan.action === "replay_completed") {
    console.log("ALICE_NO_SERVER_CALL=1 reason=replay_completed");
    console.error(
      "[CLI] 本进程未向服务端发请求，直接重放本地 completed 结果；" +
        "serverCallsThisProcess=0。禁止向用户声称「已向服务端新建任务」。",
    );
    console.error(
      "[CLI][replay] 这不是新建分析。如需重新分析同一主体，必须加 --new 参数：" +
        `node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --new --no-wait`,
    );
    console.error(
      "[CLI][replay] 禁止删除 submit-locks/ 锁文件；禁止反复重发不加 --new 的同条命令。",
    );
    announceServerUsage({
      action: "replay",
      taskId: plan.record?.taskId,
      promptHash,
      registry,
      forceNew,
      recoveredFromOtherProcess: true,
    });
    replayCompletedArtifacts({
      registry,
      taskId: plan.record?.taskId,
      promptHash,
      logPrefix,
    });
    publishFinalStatus("completed");
    printCliRunEndNotice({ success: true, exitCode: 0, elapsed: formatElapsed(0) });
    return { done: true };
  }
  if (plan.action === "abort_failed") {
    printAbortFailedGuidance(plan.record, logPrefix);
    publishFinalStatus("failed");
    process.exitCode = 1;
    return { done: true };
  }
  if (plan.action === "attach") {
    const taskId = plan.record.taskId;
    announceServerUsage({
      action: "attach",
      taskId,
      promptHash,
      registry,
      forceNew,
    });
    printPromptHashMarker(promptHash, taskId);
    printAwaitingResultArtifactGuard({ prompt, promptHash, registry, downloadDir });
    return { done: false, taskId };
  }
  if (await enforceDuplicateGuard({
    registry,
    prompt,
    promptHash,
    forceNew,
    url,
    headers,
    apiKey,
  })) {
    return { done: true };
  }
  // 跨进程提交锁：tasks.json 写入失败时，防止同一 prompt 被并发 CLI 重复提交
  if (enforceSubmitLock({ promptHash, prompt, forceNew })) {
    return { done: true };
  }
  printAwaitingResultArtifactGuard({ prompt, promptHash, registry, downloadDir });
  const submitted = await submitTaskForNoWaitMode({
    url,
    headers,
    apiKey,
    prompt,
    registry,
    promptHash,
    downloadDir,
    forceNew,
    newSession,
    continueSession,
    sessionScope,
  });
  if (!submitted.ok) {
    if (submitted.sandboxNoPersist) {
      publishFinalStatus("failed");
      process.exitCode = EXIT_SANDBOX_NO_PERSIST;
      return { done: true };
    }
    if (submitted.serverNotice) {
      publishFinalStatus("failed");
      return { done: true };
    }
    if (!submitted.duplicate) {
      publishFinalStatus("failed");
      process.exitCode = 1;
    }
    return { done: true };
  }
  announceServerUsage({
    action: "submit",
    taskId: submitted.taskId,
    promptHash,
    registry,
    forceNew,
  });
  printPromptHashMarker(promptHash, submitted.taskId);

  // SSE 先行阶段已直接拿到结果：直接交付，不需要 tasks/get 轮询
  if (submitted.completed) {
    printAwaitingResultArtifactGuard({ prompt, promptHash, registry, downloadDir });
    publishFinalStatus("completed");
    printCliRunEndNotice({
      success: true,
      exitCode: 0,
      elapsed: formatElapsed(Date.now() - (registry.findByTaskId(submitted.taskId)?.startedAt ?? Date.now())),
    });
    return { done: true };
  }

  printAwaitingResultArtifactGuard({ prompt, promptHash, registry, downloadDir });
  return { done: false, taskId: submitted.taskId };
}

function registerNewTaskRecord({ registry, promptHash, prompt, taskId, contextId, downloadDir }) {
  const now = Date.now();
  const saved = registry.upsert({
    promptHash,
    skill: ALICE_SKILL_NAME_ZH,
    promptPreview: buildPromptPreview(prompt),
    // 持久化完整的 normalized prompt，供后续会话做"相似 prompt 重复提交检测"。
    // promptPreview 仅 80 字截断，对短 prompt 是其前缀的 case 不够稳定。
    promptNormalized: normalizePromptForGuard(prompt),
    taskId,
    contextId,
    status: "running",
    startedAt: now,
    lastSeenAt: now,
    completedAt: null,
    downloadDir: downloadDir || null,
  });
  if (!saved) {
    console.error(
      `[CLI][严重] tasks.json 写入失败（EPERM / 权限不足）；服务端任务提交后若进程异常退出，下次将无法续接，可能重复扣积分。`,
    );
    console.error(
      `[CLI][严重] 请检查 ${REGISTRY_PATHS.file} 的写入权限。`,
    );
    console.log("ALICE_REGISTRY_WRITE_FAILED=1");
  }
  return saved;
}

// ---------------------------------------------------------------------------
// 跨进程提交锁：当 tasks.json 写入失败时，用 PID 文件锁防止同一 prompt 被并发提交
// ---------------------------------------------------------------------------
// 路径策略：主路径走 resolveDataDir("submit-locks")，固定在 ~/.wind-alice/submit-locks/（跨会话稳定），不可写时回退到 os.tmpdir()/alice-submit-locks/。
// 沙箱（如 Workbuddy）常阻止用户主目录写入但允许临时目录。

const SUBMIT_LOCK_DIR_PRIMARY = resolveDataDir("submit-locks");
const SUBMIT_LOCK_DIR_FALLBACK = join(tmpdir(), "alice-submit-locks");
const SUBMIT_LOCK_TTL_MS = 10 * 60 * 1000; // 与 DEFAULT_DUPLICATE_GUARD_WINDOW_MS 一致

/** 缓存已确认可写的锁目录，避免每次都做写入测试。 */
let _writableLockDir = null;

/**
 * 确定可写的锁目录：优先主路径，不可写时回退到临时目录。
 * 通过实际创建目录+写入测试文件来判断可写性。
 */
function resolveWritableLockDir() {
  if (_writableLockDir) return _writableLockDir;

  for (const dir of [SUBMIT_LOCK_DIR_PRIMARY, SUBMIT_LOCK_DIR_FALLBACK]) {
    try {
      mkdirSync(dir, { recursive: true });
      // 写入测试文件确认可写
      const testFile = join(dir, ".write-test");
      writeFileSync(testFile, "1", "utf8");
      unlinkSync(testFile);
      _writableLockDir = dir;
      return dir;
    } catch {
      continue;
    }
  }
  // 两个目录都不可写——返回 null，锁功能降级
  return null;
}

function submitLockPath(lockKey) {
  const dir = resolveWritableLockDir();
  if (!dir) return null;
  return join(dir, `${lockKey}.pid`);
}

function subjectSubmitLockKey(subjectKey) {
  if (!subjectKey) return null;
  return createHash("sha256").update(`subject:${subjectKey}`, "utf8").digest("hex");
}

/** 本进程当前持有的主体锁键（进程退出 / DONE 时释放）。 */
let heldSubjectLockKey = null;

/**
 * 检查指定 lockKey 的提交锁。
 * @returns {object|null}
 */
function checkSubmitLockAtPath(lockPath) {
  if (!lockPath || !existsSync(lockPath)) return null;
  let content;
  try {
    content = readFileSync(lockPath, "utf8").trim();
  } catch {
    return null;
  }
  let lock;
  try {
    lock = JSON.parse(content);
  } catch {
    return null;
  }
  if (!lock || typeof lock.pid !== "number" || typeof lock.startedAt !== "number") return null;

  const now = Date.now();
  if (now - lock.startedAt > SUBMIT_LOCK_TTL_MS) {
    try { unlinkSync(lockPath); } catch {}
    return null;
  }

  if (lock.pid === process.pid) {
    return null;
  }

  if (!isProcessAlive(lock.pid)) {
    try { unlinkSync(lockPath); } catch {}
    return null;
  }

  return lock;
}

/**
 * 检查是否有另一个 CLI 进程正在为同一 prompt 提交/执行任务。
 * 返回 null（无锁 / 锁目录不可用）或锁信息（pid、startedAt、promptPreview）。
 */
function checkSubmitLock(promptHash) {
  return checkSubmitLockAtPath(submitLockPath(promptHash));
}

function checkSubjectSubmitLock(subjectKey) {
  const key = subjectSubmitLockKey(subjectKey);
  if (!key) return null;
  return checkSubmitLockAtPath(submitLockPath(key));
}

function writeSubmitLockAtPath(lockPath, prompt, extra = {}) {
  if (!lockPath) return false;
  try {
    mkdirSync(dirname(lockPath), { recursive: true });
    const lockData = {
      pid: process.pid,
      startedAt: Date.now(),
      promptPreview: buildPromptPreview(prompt),
      promptNormalized: normalizePromptForGuard(prompt),
      ...extra,
    };
    writeFileSync(lockPath, JSON.stringify(lockData), "utf8");
    return true;
  } catch {
    return false;
  }
}

/** 创建提交锁文件。写入当前进程 PID、时间戳和 prompt 摘要。 */
function acquireSubmitLock(promptHash, prompt) {
  const ok = writeSubmitLockAtPath(submitLockPath(promptHash), prompt, { lockKind: "promptHash" });
  const subjectKey = computeSubjectKey(prompt);
  if (subjectKey) {
    const sk = subjectSubmitLockKey(subjectKey);
    heldSubjectLockKey = sk;
    writeSubmitLockAtPath(submitLockPath(sk), prompt, {
      lockKind: "subject",
      subjectKey,
    });
  }
  return ok;
}

function releaseSubmitLockAtPath(lockPath) {
  if (!lockPath) return;
  try {
    if (existsSync(lockPath)) unlinkSync(lockPath);
  } catch {}
}

/** 进程正常退出或任务终态时释放锁。 */
function releaseSubmitLock(promptHash) {
  releaseSubmitLockAtPath(submitLockPath(promptHash));
}

function releaseSubjectSubmitLock() {
  if (!heldSubjectLockKey) return;
  releaseSubmitLockAtPath(submitLockPath(heldSubjectLockKey));
  heldSubjectLockKey = null;
}

function releaseAllSubmitLocks(promptHash) {
  releaseSubmitLock(promptHash);
  releaseSubjectSubmitLock();
}

/** 检查指定 PID 的进程是否仍在运行（跨平台）。 */
function isProcessAlive(pid) {
  if (typeof pid !== "number" || pid <= 0) return false;
  try {
    // Node.js process.kill(pid, 0) 不发送信号，只检查进程是否存在
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

/**
 * 在 submit 前检查并尝试获取跨进程提交锁。
 * 如果另一个进程已持有锁（且仍在运行），拒绝提交并返回 true（表示被阻止）。
 * 否则获取锁并返回 false。
 */
function enforceSubmitLock({ promptHash, prompt, forceNew }) {
  if (forceNew) return false;

  const existing = checkSubmitLock(promptHash);
  if (existing) {
    return reportSubmitLockConflict(existing, prompt, "promptHash");
  }

  const subjectKey = computeSubjectKey(prompt);
  if (subjectKey) {
    const subjectExisting = checkSubjectSubmitLock(subjectKey);
    if (subjectExisting) {
      return reportSubmitLockConflict(subjectExisting, prompt, "subject", subjectKey);
    }
  }

  acquireSubmitLock(promptHash, prompt);
  return false;
}

function reportSubmitLockConflict(existing, prompt, lockKind, subjectKey = null) {
  const elapsedSec = Math.round((Date.now() - existing.startedAt) / 1000);
  const elapsed =
    elapsedSec < 60
      ? `${elapsedSec}s`
      : elapsedSec < 3600
        ? `${Math.floor(elapsedSec / 60)}m${elapsedSec % 60}s`
        : `${Math.floor(elapsedSec / 3600)}h${Math.floor((elapsedSec % 3600) / 60)}m`;

  const scope =
    lockKind === "subject"
      ? `同主体（${subjectKey ?? "?"}) 不同措辞`
      : "同一 prompt";

  console.error(
    `[CLI][跨进程提交锁] 检测到另一 CLI 进程（PID=${existing.pid}）` +
    `已为${scope}提交/执行任务（已运行 ${elapsed}），拒绝重复提交。`,
  );
  console.error(
    "[CLI][跨进程提交锁] 正确做法：等待该进程完成后再用相同 prompt 加 --no-wait 续接；" +
    "如需并行新建，须先 check-conflict 询问用户后加 --new。",
  );
  console.error(
    "[CLI][跨进程提交锁] 禁止手动删除锁文件（Remove-Item ...submit-locks\\...pid）；禁止绕过防重复保护。",
  );
  console.error(
    `[CLI][跨进程提交锁] 退出码 76 = EXIT_DUPLICATE_LIKELY；不消耗任何服务端额度。`,
  );
  process.exitCode = EXIT_DUPLICATE_LIKELY;
  return true;
}

/** @internal 单测 */
export function __checkSubmitLockForTesting(promptHash) {
  return checkSubmitLock(promptHash);
}
/** @internal 单测 */
export function __acquireSubmitLockForTesting(promptHash, prompt) {
  return acquireSubmitLock(promptHash, prompt);
}
/** @internal 单测 */
export function __releaseSubmitLockForTesting(promptHash) {
  return releaseSubmitLock(promptHash);
}
/** @internal 单测 */
export function __isProcessAliveForTesting(pid) {
  return isProcessAlive(pid);
}
/** @internal 单测 */
export function __enforceSubmitLockForTesting({ promptHash, prompt, forceNew }) {
  return enforceSubmitLock({ promptHash, prompt, forceNew });
}
/** @internal 单测 */
export function __checkSubjectSubmitLockForTesting(subjectKey) {
  return checkSubjectSubmitLock(subjectKey);
}
/** @internal 单测 */
export function __computeSubjectKeyForTesting(prompt) {
  return computeSubjectKey(prompt);
}

function printAttachBanner({ taskId, contextId, startedAt }) {
  const elapsed = formatElapsed(Date.now() - startedAt);
  console.log("");
  console.log("ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=RUNNING");
  console.log("[CLI] 本进程将阻塞等待直至报告完成或失败；见到 [完成] 与 agentResult.value 前请勿结束当前步骤。");
  console.log("[任务复用] 命中本地 registry，正在续接已有任务：");
  console.log(`  taskId    = ${taskId}`);
  console.log(`  contextId = ${contextId}`);
  console.log(`  已运行     = ${elapsed}`);
  console.log("[任务复用] 通过 tasks/resubscribe 接续监听，不会重复消耗服务端额度。");
  console.log("[任务复用] 任务复用不等于报告已完成；请继续等待 agentResult.value 输出。");
  console.log("[任务复用] 若想丢弃旧任务并重新发起，请按 Ctrl+C 退出后加 --new。");
}

function printNewTaskBanner({ taskId, contextId }) {
  console.log("");
  console.log("ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=RUNNING");
  console.log("[CLI] 本进程将阻塞等待直至报告完成或失败；见到 [完成] 与 agentResult.value 前请勿结束当前步骤。");
  console.log("[任务已受理] 服务端已建立新任务：");
  console.log(`  taskId    = ${taskId}`);
  console.log(`  contextId = ${contextId}`);
  console.log("[任务已受理] 服务端正在执行，预计 2-15 分钟；请勿中断进程。");
  console.log("[任务已受理] 注意：[任务已受理] 仅表示任务已提交，不等于报告已生成；必须等到 agentResult.value 与 [完成]。");
  console.log("[任务已受理] 重复发起相同 prompt（含被 Agent 自动重发）时，CLI 会自动 attach 已有任务，不会重复消耗额度。");
}

function printCliRunStartNotice() {
  const lines = [
    "ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=RUNNING",
    "[CLI] 公司一页纸已启动：本进程将阻塞运行直至成功（agentResult + [完成]）或失败，通常需 2-15 分钟。",
    "[CLI] [等待中] 心跳期间无新输出属正常；禁止用 check_command_status 轮询替代等待本进程结束。",
    "[CLI] 见到 [任务已受理] 仅表示已提交，不等于报告完成；必须等到 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=COMPLETED。",
  ];
  for (const line of lines) {
    console.error(line);
  }
}

/**
 * 任务成功完成时调用：把累积的 agentResult.value 整体落盘 + 把路径写回 tasks.json，
 * 并在 stdout/stderr 双路打印 REPORT_FILE=<abs_path> 机器可读标记。
 * 这是在沙箱终端（如 trae）的 stdout 缓冲区被截断、调用方读不到 agentResult.value
 * 时，提供的"读文件兜底"通道。
 *
 * @param {object} ctx
 * @param {import("./tasksRegistry.js").TasksRegistry} ctx.registry
 * @param {string} ctx.taskId
 * @param {string} ctx.promptHash
 * @param {string} ctx.prompt
 * @returns {string|null}  落盘后的绝对路径；若没有可落盘内容则返回 null
 */
function persistAgentResultIfAny({ registry, taskId, promptHash, prompt }) {
  const text = getJoinedAgentResultText();
  if (!text) return null;
  const header = [
    `<!-- alice-company-one-page-investment-memo：本次 Alice agentResult.value 已落盘 -->`,
    `<!-- 重要：本文件是 Alice 响应正文（agentResult.value），并不一定等于"完整一页纸投资报告"。 -->`,
    `<!-- · 成功场景：Alice 通常把核心结论摘要放在这里，把完整报告正文以 /project/<x>.md -->`,
    `<!--   附件给出。完整报告 .md 会被 CLI 下载到当前工作空间（process.cwd()）， -->`,
    `<!--   并在 CLI 输出中以 REPORT_FULL_FILE=<abs> 机器可读标记给出。 -->`,
    `<!-- · 失败/受限/数据缺失场景：本文件落盘的是服务端原始说明，仅供排查。 -->`,
    `<!-- · Agent 交付给用户时：只输出 agentResult.value 原文（stdout 或本文件正文）； -->`,
    `<!--   禁止读取 reportFullFile / download/ 附件向用户展示。 -->`,
    `<!-- generated_at: ${new Date().toISOString()} -->`,
    `<!-- prompt: ${String(prompt ?? "").replace(/-->/g, "-- >")} -->`,
    `<!-- promptHash: ${promptHash} -->`,
    `<!-- taskId: ${taskId} -->`,
    "",
  ].join("\n");
  const path = saveResultFile(taskId, header + text);
  if (!path) return null;
  rememberReportFile(path);
  rememberDoneTaskId(taskId);
  rememberDonePromptHash(promptHash);
  try {
    const r = registry.findByTaskId(taskId);
    if (r) {
      r.resultPath = path;
      r.resultBytes = Buffer.byteLength(text, "utf8");
      registry.save();
    }
  } catch {}
  const lines = [
    `REPORT_FILE=${path}`,
    `[CLI] REPORT_FILE 是 agentResult.value 落盘副本（stdout 被沙箱截断时 Agent 可读此文件正文交付用户）。`,
    `[CLI] 完整报告附件（如有）会静默下载到工作空间（process.cwd()），并以 REPORT_FULL_FILE=<abs> 标出路径——Agent 不要向用户展示附件正文。`,
    `[CLI] 交付用户时：只输出 agentResult.value 原文，禁止概括；禁止读取 REPORT_FULL_FILE 内容展示给用户。`,
    `[CLI]   REPORT_FILE 路径：${path}`,
  ];
  for (const line of lines) {
    console.error(line);
  }
  return path;
}

/**
 * SIGINT / SIGTERM 触发时的本地清理逻辑（与 process.exit 解耦，便于单测）。
 *
 * 关键修复：根据 `taskCreatedOnServer` 区分两种场景，避免"假复用 → attach 失败 → 自动回退新建"白白消耗一次额度。
 *
 *   1) `taskCreatedOnServer === true`（已收到服务端 200 响应）：
 *      保留本地 running 记录，提示用户下次会自动 tasks/resubscribe 续接。
 *
 *   2) `taskCreatedOnServer === false`（fetch 还没 200，本地 running 是乐观写入）：
 *      服务端可能根本不认这个 taskId，留着本地记录会让下次启动误判可续接，
 *      attach 必败，CLI 自动回退到新建任务 → 实际消耗一次新额度。
 *      → 直接删掉本地 running 记录，下次启动就是干净的新任务流程。
 *
 * @returns {{ cleared: boolean }} cleared=true 表示已删除 registry 记录
 */
export function handleInterruptCleanup({
  signal,
  taskCreatedOnServer,
  registry,
  promptHash,
  taskId,
  contextId,
  registryPath,
  log = console.error,
}) {
  log("");
  if (taskCreatedOnServer) {
    log(`[已中断本地监听] 收到 ${signal}，进程即将退出，但服务端任务仍在执行：`);
    log(`  taskId    = ${taskId}`);
    log(`  contextId = ${contextId}`);
    log(`  本地记录   = ${registryPath}`);
    log("");
    log("下次执行相同 prompt 请加 --no-wait 续接该任务（默认行为）。");
    log("若要丢弃进行中的旧任务并并行新建，须先 check-conflict 询问用户后加 --new。");
    return { cleared: false };
  }

  let removeError = null;
  try {
    registry.removeByTaskId(taskId);
  } catch (e) {
    removeError = e;
  }
  log(`[已中断本地监听] 收到 ${signal}，进程即将退出。`);
  log(`  本次任务尚未确认在服务端建立（未收到 HTTP 200 响应）：`);
  log(`  taskId    = ${taskId}`);
  log(`  contextId = ${contextId}`);
  if (removeError) {
    log(`  [警告] 清理本地 running 记录失败：${removeError?.message ?? removeError}`);
    log(`  请手动检查 ${registryPath} 中 taskId=${taskId} 的记录。`);
    return { cleared: false };
  }
  log(`  已删除本地 running 记录（${registryPath}），避免下次启动误判"可续接 → attach 失败 → 自动回退新建"白白消耗一次额度。`);
  log("");
  log("下次执行相同 prompt，CLI 会直接新建任务，不会先 attach 一个服务端可能不认的旧 taskId。");
  return { cleared: true };
}

function printCliRunEndNotice({ success, exitCode, elapsed }) {
  const lines = success
    ? [
        "ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=COMPLETED",
        `[CLI] Alice 任务已完成（退出码=${exitCode}，总耗时 ${elapsed}）。`,
        `[CLI] 交付用户的正确做法：`,
        `[CLI]   1) 将 stdout 中 agentResult.value 原文交给用户（禁止概括、禁止改写）；`,
        `[CLI]   2) stdout 被沙箱截断时，读 reportFile= 落盘正文（跳过 HTML 注释头）；`,
        `[CLI]   3) 不要读取 reportFullFile= / download/ 附件向用户展示——附件仅静默落盘供用户本地查阅。`,
      ]
    : [
        "ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=FAILED",
        `[CLI] 任务未成功完成（退出码=${exitCode}，总耗时 ${elapsed}）：请勿向用户宣称报告已生成。`,
      ];
  for (const line of lines) {
    console.error(line);
  }
  if (success) {
    emitAnalysisDone();
  }
}

function usage() {
  return [
    "alice-company-one-page-investment-memo — 调用万得 Alice Agent「公司一页纸」技能，为上市公司流式输出结构化一页纸投资报告",
    "",
    "Usage:",
    "  alice-company-one-page-investment-memo --prompt <QUESTION> [--download-dir <DIR>] [--new]",
    "  alice-company-one-page-investment-memo --prompt <QUESTION> --no-wait                       # 沙箱推荐：CLI 内部自旋 probe 直到完成（默认）",
    "  alice-company-one-page-investment-memo --prompt <QUESTION> --no-wait --once                # 单次探针：几秒内返回（脚本/调试）",
    "  alice-company-one-page-investment-memo --prompt <QUESTION> --no-wait \\",
    "      --watch-interval 60 --watch-timeout 1800                              # 自定义轮询节奏",
    "  alice-company-one-page-investment-memo status --prompt <QUESTION>                        # 查询落盘路径（不访问服务端）",
    "  alice-company-one-page-investment-memo check-conflict --prompt <QUESTION>                # [已废弃] 主调用 --no-wait 已内置去重，无需预检",
    "  alice-company-one-page-investment-memo apikey-set <KEY>",
    "  alice-company-one-page-investment-memo apikey-get",
    "  alice-company-one-page-investment-memo apikey-clear",
    "  alice-company-one-page-investment-memo --help",
    "",
    "Options:",
    "  --prompt,       -p <QUESTION>   用户提问，例如\"请分析一下比亚迪的投资价值\"（必填）",
    "  --download-dir, -d <DIR>        保留兼容；不影响下载目录——附件统一落当前工作空间 process.cwd()（见下文）",
    "  --new                     用户明确要求并行新建：清除该 prompt 全部本地记录后新建（须先 check-conflict 询问用户）",
    "  --context-id <ID>         【推荐续接】从上一轮 DONE 行的 contextId= 取值原样传回，CLI 直接复用该",
    "                                  contextId、不读不写共享文件，同宿主多会话各自带 ID、物理上不串号。",
    "                                  第一轮或切话题时不传。",
    "  --continue-session              （兼容，已不推荐）旧式：读共享 current-session[.<scope>].json 复用上次",
    "                                  contextId；共享文件按宿主（非按会话）切分，同宿主多会话会串号。改用 --context-id。",
    "  --new-session                   显式强制新建会话上下文（不复用上次 contextId）；切话题时可用。",
    "  --session-scope <ID>            （兼容，已不推荐）旧式宿主隔离标识；--context-id 已按会话隔离，通常无需传。",
    "                                  亦可用环境变量 WIND_ALICE_SESSION_SCOPE 统一设置（命令行 --session-scope 优先）。",
    "  --no-wait                       不挂 SSE：CLI 内部自旋 tasks/get 直到任务终态（沙箱 / Trae 推荐）；",
    "                                  全程默认最长 60 分钟，每轮 30 分钟，到轮次上限自动续轮，Agent 勿外层连发",
    "  --once                          （需配合 --no-wait）单次探针、几秒内返回；禁止 Agent 用此模式手工循环",
    "  --watch,        -w              已废弃：--no-wait 默认即内部自旋，无需再写 --watch",
    `  --watch-interval <SEC>          两次 probe 之间的 sleep 秒数（默认 ${WATCH_DEFAULT_INTERVAL_SEC}s，最少 ${WATCH_MIN_INTERVAL_SEC}s）`,
    `  --watch-timeout  <SEC>          每轮自旋最长秒数（默认 ${WATCH_DEFAULT_TIMEOUT_SEC}s，上限 ${WATCH_MAX_TIMEOUT_SEC}s）；`,
    `                                  到轮次上限 CLI 自动续下一轮；仅全程达 ${WATCH_ABSOLUTE_MAX_SEC}s 才 exit=4`,
    `  --watch-absolute-max <SEC>      单次 CLI 进程全程自旋上限（默认 ${WATCH_ABSOLUTE_MAX_SEC}s）`,
    "  --no-strict                     关闭 strict 模式（默认开启）；strict 模式下进程退出时若未输出",
    "                                  ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 行，会把 exitCode=0 强制改成 6，",
    "                                  避免 Agent 把被沙箱杀掉的进程误判为成功。仅脚本/调试场景关闭。",
    "  --help,         -h              查看帮助",
    "",
    "API Key 子命令（KEY 是裸值不要加引号；只支持写入 ~/.wind-alice/config.env）:",
    "  apikey-set <KEY>            写入 / 覆盖 API Key（自动迁移历史版本的无后缀 config）",
    "  apikey-get                  查看当前 Key 状态（脱敏回显）",
    "  apikey-clear                清除当前 Key（同时清理历史版本的无后缀 config）",
    "",
    "状态查询子命令（只读本地 tasks.json，不消耗服务端额度）:",
    "  status --prompt <QUESTION>          输出 PROMPT_HASH / REPORT_FILE / REPORT_FULL_FILE 等机器可读标记；",
    "                                      Agent 查报告路径时用此命令，禁止按 results/ 修改时间扫目录",
    "  check-conflict --prompt <QUESTION>  [已废弃] 主调用 --no-wait 已内置去重（同 prompt running 自动续接、本地 completed 自动重放、同主体相似 prompt 命中 exit=76），无需额外预检命令",
    "",
    "下载目录（固定）:",
    "  所有附件（报告 / 数据 / 图片）统一下载到当前工作空间 process.cwd()；",
    "  -d / --download-dir 保留兼容，不影响下载目录。",
    "",
    "任务调度（默认不新建并行任务）:",
    "  默认：同 prompt 有 running → 自动续接；本地 completed → 自动提交新分析；无记录 → 新建。",
    "  --new：用户明确要求并行新建时清除本地记录后新建（须先 check-conflict 询问用户）。",
    "  status 子命令：查询该 prompt 最近一条任务的落盘路径。",
    "",
    "退出码:",
    "  0   成功：必定伴随 stdout 含 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 行（Agent 判定任务完成的唯一确定信号）",
    "  1   一般失败 / 任务终态为 failed",
    "  2   参数错误 / KEY_MISSING",
    "  4   --no-wait 专用：已达全程自旋上限（默认 60min）仍未完成；Agent 再执行一次相同 --no-wait 续接",
    "  5   --no-wait 专用：--once 且本地无任务记录（默认 --no-wait 会自动提交）",
    "  6   strict 模式兜底：进程退出但未输出 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE（通常表示进程被沙箱终止）；",
    "      任务可能仍在服务端执行，请用相同 prompt 加 --no-wait 续接，不要当成失败更不要当成功",
    "  11  [已废弃] check-conflict 专用：检测到可能冲突的 running 任务",
    "  12  [已废弃] check-conflict 专用：24h 内已有相似 completed 任务可重放",
    "  77  status 专用：本地无此 prompt 记录但存在相似已完成任务；禁止扫 download/ 误读，须阻塞 --no-wait",
    "  75  服务端临时拒绝（并发上限 / 服务繁忙 / 积分不足）；禁止立即重试",
    "  76  重复提交防护命中（10 分钟内已有相似 prompt 的 running 任务）；用相同 prompt 加 --no-wait 续接，",
    "      或在用户明确需要时加 --new 重新发起",
    "",
    "Env:",
    `  WIND_ALICE_API_URL          可选；默认 ${DEFAULT_API_URL}`,
    "",
    "API Key 配置位置（仅此路径，不支持环境变量 / skill 目录内 config.json）:",
    `  ${KEY_CONFIG_FILE}  (dotenv: WIND_API_KEY=...)`,
    `  历史版本的 ${LEGACY_KEY_CONFIG_FILE}（无后缀）仍可读取，apikey-set 会自动迁移并删除老文件。`,
    "",
    `获取 API Key：${WIND_ALICE_KEY_PAGE}`,
    `（万得 Alice → 左下角头像 → 「设置」→「账户」标签页 → 复制 API Key）`,
  ].join("\n");
}

export function parseSsePayload(payload) {
  return payload
    .split(/\r?\n\r?\n/)
    .map((block) => block.trim())
    .filter(Boolean)
    .flatMap((block) => {
      const data = block
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");

      if (!data) return [];

      try {
        return [JSON.parse(data)];
      } catch (error) {
        console.error("failed to parse SSE event:");
        console.error(block);
        console.error(error);
        return [];
      }
    });
}

/**
 * 从一个 SSE 事件里提取服务端真正下发的 `taskId` / `contextId`。
 *
 * A2A 规范下 `message/stream` 服务端首事件通常是两种形态之一：
 *   1) Task 对象：    `{ result: { kind: "task", id, contextId, status, ... } }`
 *   2) status-update：`{ result: { kind: "status-update", taskId, contextId, status, ... } }`
 *
 * 客户端 `message/stream` 时虽然可以预生成 taskId 塞进 message 里，但服务端会以**自己分配**
 * 的 taskId 为准下发到 SSE 首事件——后续 `tasks/get id=<服务端 taskId>` 只认这个 ID。
 * `--no-wait` 模式必须在断开 SSE 前把它读出来，否则永远查不到任务。
 *
 * @returns {{ taskId: string, contextId: string } | null}
 *   仅当同时拿到非空 taskId 与 contextId 时返回；否则返回 null（让调用方继续读后续事件）。
 * @internal 仅供单测与 submitTaskForNoWaitMode 使用。
 */
export function extractServerTaskIds(event) {
  const result = event?.result;
  if (!result || typeof result !== "object") return null;

  const taskId =
    (typeof result.taskId === "string" && result.taskId) ||
    (typeof result.id === "string" && result.id) ||
    null;
  const contextId =
    (typeof result.contextId === "string" && result.contextId) || null;

  if (!taskId || !contextId) return null;
  return { taskId, contextId };
}

export function extractAgentResultValues(events) {
  return events.flatMap((event) => {
    const artifact = event?.result?.artifact;
    if (
      event?.result?.kind !== "artifact-update" ||
      artifact?.name !== "agentResult"
    ) {
      return [];
    }

    return (artifact.parts ?? []).flatMap((part) => {
      if (part?.kind !== "data") return [];
      const value = part?.data?.data;
      return value === undefined ? [] : [value];
    });
  });
}

const FILE_EXT_WHITELIST = new Set([
  "md",
  "markdown",
  "xlsx",
  "xls",
  "csv",
  "pdf",
  "docx",
  "doc",
  "pptx",
  "ppt",
  "txt",
  "zip",
  "rar",
  "7z",
  "png",
  "jpg",
  "jpeg",
  "svg",
  "html",
  "htm",
  "json",
]);

const MD_LINK_RE = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
// 排除 ] [ ( —— 避免把 `https://.../x.md](/project/x.md` 这类 Markdown 残片吃进 URL
const BARE_URL_RE = /https?:\/\/[^\s)<>"'`\[\]()]+/g;
// 形如 `[文件名](/project/xxx.md)` 的相对链接：仅 `/project/...` 这种 Alice 工作区路径
const PROJECT_REL_LINK_RE = /\[([^\]]+)\]\((\/project\/[^\s)]+)\)/g;
// 形如 `[文件名](file:///project/xxx.md)` —— Alice 部分场景用 file:// 协议给出工作区路径
const FILE_SCHEME_PROJECT_LINK_RE =
  /\[([^\]]+)\]\(file:\/\/\/?(\/project\/[^\s)]+)\)/gi;
// 正文裸文本中的 `file:///project/xxx.ext`（无 markdown 包裹）
const FILE_SCHEME_PROJECT_PATH_RE =
  /(?<![/\w-])file:\/\/\/?(\/project\/[^\s\`)<>"'，。、:：；\]\(]+\.[A-Za-z0-9]+)/gi;
// 形如 `/project/xxx.ext` 反引号包裹或正文裸文本中的工作区相对路径：
// Alice 部分场景下会用反引号或正文直述形式给出报告文件路径，而不是标准的
// [name](path) markdown 链接，此前 CLI 仅识别 markdown 链接形式，会导致报告附件漏抓 / 不下载。
// 这里要求：
//   1) 路径必须以已知扩展名结尾（FILE_EXT_WHITELIST 二次校验），避免抓到任意 /project/... 字符串；
//   2) lookbehind 排除前缀为 `/` 或字母数字 / `_` / `-` 的位置，从而跳过完整 HTTP URL（如
//      `https://host/project/xxx.md`）中已包含的 /project 片段，避免与 BARE_URL_RE 重复抓取。
// 排除 ] ( —— 避免 [/project/x.md](/project/x.md) 中 .md 后的 Markdown 残片被过度匹配
const PROJECT_REL_PATH_RE =
  /(?<![/\w-])\/project\/[^\s\`)<>"'，。、:：；\]\(]+\.[A-Za-z0-9]+/g;

function buildSessionProjectFileUrl(relativePath) {
  if (!currentSessionContextId) return null;
  let path = String(relativePath || "").trim();
  if (!path) return null;
  if (!path.startsWith("/")) path = "/" + path;
  return `${WIND_PROJECT_FILES_PREFIX}${currentSessionContextId}${path}`;
}

function deriveFilenameFromUrl(url, fallback) {
  try {
    const u = new URL(url);
    const last = u.pathname.split("/").filter(Boolean).pop();
    if (last) return decodeURIComponent(last);
  } catch {}
  return fallback || "downloaded";
}

function looksLikeFileUrl(url) {
  let path = "";
  try {
    path = new URL(url).pathname;
  } catch {
    return false;
  }
  if (path.includes("/files/")) return true;
  // 拒绝 pathname 含 Markdown 残片的畸形 URL（如 .../x.md](/project/x.md）
  if (/[\]\(\[]/.test(path)) return false;
  const lastDot = path.lastIndexOf(".");
  if (lastDot === -1) return false;
  const ext = path.slice(lastDot + 1).toLowerCase();
  return FILE_EXT_WHITELIST.has(ext);
}

// 仅供单元测试使用：在不发起真实请求的前提下注入当前会话 contextId，
// 让 collectDownloadLinks 能把 /project/xxx 拼成完整 URL。生产代码请勿调用，
// 实际 contextId 应通过 message/stream 或 tasks/get 由请求流程自动注入。
export function __setSessionContextIdForTesting(ctxId) {
  currentSessionContextId = ctxId ?? null;
}

export function collectDownloadLinks(value) {
  if (value == null) return [];
  const text = typeof value === "string" ? value : JSON.stringify(value);
  const found = new Map();

  let m;
  MD_LINK_RE.lastIndex = 0;
  while ((m = MD_LINK_RE.exec(text)) !== null) {
    const [, name, url] = m;
    if (!looksLikeFileUrl(url)) continue;
    if (!found.has(url)) {
      found.set(url, deriveFilenameFromUrl(url, name));
    }
  }

  BARE_URL_RE.lastIndex = 0;
  while ((m = BARE_URL_RE.exec(text)) !== null) {
    const url = m[0].replace(/[)\].,;]+$/, "");
    if (found.has(url)) continue;
    if (!looksLikeFileUrl(url)) continue;
    found.set(url, deriveFilenameFromUrl(url));
  }

  PROJECT_REL_LINK_RE.lastIndex = 0;
  while ((m = PROJECT_REL_LINK_RE.exec(text)) !== null) {
    const [, name, relPath] = m;
    const fullUrl = buildSessionProjectFileUrl(relPath);
    if (!fullUrl) continue;
    if (!looksLikeFileUrl(fullUrl)) continue;
    if (!found.has(fullUrl)) {
      found.set(fullUrl, deriveFilenameFromUrl(fullUrl, name));
    }
  }

  FILE_SCHEME_PROJECT_LINK_RE.lastIndex = 0;
  while ((m = FILE_SCHEME_PROJECT_LINK_RE.exec(text)) !== null) {
    const [, name, relPath] = m;
    const fullUrl = buildSessionProjectFileUrl(relPath);
    if (!fullUrl) continue;
    if (!looksLikeFileUrl(fullUrl)) continue;
    if (!found.has(fullUrl)) {
      found.set(fullUrl, deriveFilenameFromUrl(fullUrl, name));
    }
  }

  FILE_SCHEME_PROJECT_PATH_RE.lastIndex = 0;
  while ((m = FILE_SCHEME_PROJECT_PATH_RE.exec(text)) !== null) {
    const relPath = m[1];
    const dotIdx = relPath.lastIndexOf(".");
    if (dotIdx === -1) continue;
    const ext = relPath.slice(dotIdx + 1).toLowerCase();
    if (!FILE_EXT_WHITELIST.has(ext)) continue;
    const fullUrl = buildSessionProjectFileUrl(relPath);
    if (!fullUrl) continue;
    if (found.has(fullUrl)) continue;
    found.set(fullUrl, deriveFilenameFromUrl(fullUrl));
  }

  PROJECT_REL_PATH_RE.lastIndex = 0;
  while ((m = PROJECT_REL_PATH_RE.exec(text)) !== null) {
    const relPath = m[0];
    const dotIdx = relPath.lastIndexOf(".");
    if (dotIdx === -1) continue;
    const ext = relPath.slice(dotIdx + 1).toLowerCase();
    if (!FILE_EXT_WHITELIST.has(ext)) continue;
    const fullUrl = buildSessionProjectFileUrl(relPath);
    if (!fullUrl) continue;
    if (found.has(fullUrl)) continue;
    found.set(fullUrl, deriveFilenameFromUrl(fullUrl));
  }

  return Array.from(found, ([url, filename]) => ({ url, filename }));
}

const collectedDownloads = new Map();

// 累积本次任务全部 agentResult.value 文本（按服务端到达顺序拼接），
// 用于在 SSE 流结束后整体落盘到 ~/.wind-alice/results/<promptHash>.md，
// 作为终端 stdout 被沙箱截断时的兜底读取通道。
const collectedAgentResultValues = [];

function accumulateAgentResultValues(values) {
  if (!Array.isArray(values) || values.length === 0) return;
  for (const value of values) {
    if (value == null) continue;
    const text = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    if (text) collectedAgentResultValues.push(sanitizeAgentResultTextForDelivery(text, "", resolveInlineLocalPath));
  }
}

function getJoinedAgentResultText() {
  if (collectedAgentResultValues.length === 0) return "";
  return collectedAgentResultValues.join("\n\n");
}

function accumulateDownloadsFromValues(values) {
  if (!Array.isArray(values) || values.length === 0) return;
  for (const value of values) {
    for (const { url, filename } of collectDownloadLinks(value)) {
      if (!collectedDownloads.has(url)) collectedDownloads.set(url, filename);
    }
  }
}

function sanitizeFilename(name) {
  let s = String(name || "").trim();
  s = s.replace(/[\x00-\x1f<>:"/\\|?*]+/g, "_");
  s = s.replace(/^[\s.]+|[\s.]+$/g, "");
  return s || "downloaded";
}

/**
 * 默认完整报告附件落盘目录（未传 `-d` / `--download-dir` 时）。
 * Windows / macOS / Linux 均使用用户主目录下的 `Downloads`（系统标准下载文件夹）。
 */
function defaultDownloadDir() {
  return join(homedir(), "Downloads");
}

/**
 * 解析下载文件的目标目录，优先级从高到低：
 *   0. 用户在命令行通过 `--download-dir` / `-d` 传入的目录（不存在则自动创建）
 *   1. 未指定时，回落到用户主目录 `~/Downloads`（Windows: `%USERPROFILE%\Downloads`）
 *
 * @param {string|undefined} override 用户显式指定的目录（绝对或相对路径都可）
 * @returns {string} 绝对路径；调用方可直接 join 使用
 */
function resolveDownloadDir(override) {
  if (override !== undefined && override !== null) {
    const trimmed = String(override).trim();
    if (trimmed) {
      const dir = resolve(trimmed);
      try {
        mkdirSync(dir, { recursive: true });
      } catch (e) {
        console.error(`[warn] 无法创建用户指定的下载目录 ${dir}：${e.message}`);
      }
      return dir;
    }
  }

  const fallback = defaultDownloadDir();
  try {
    mkdirSync(fallback, { recursive: true });
  } catch (e) {
    console.error(`[warn] 无法创建下载目录 ${fallback}：${e.message}`);
  }
  return fallback;
}

function resolveUniqueTargetPath(dir, filename) {
  const safe = sanitizeFilename(filename);
  let candidate = join(dir, safe);
  if (!existsSync(candidate)) return candidate;
  const { name, ext } = parsePath(safe);
  for (let i = 1; i < 1000; i++) {
    candidate = join(dir, `${name} (${i})${ext}`);
    if (!existsSync(candidate)) return candidate;
  }
  return join(dir, `${name}.${Date.now()}${ext}`);
}

/**
 * 内联 /project/<filename> 时，预测该附件在本进程下载阶段真正落盘的绝对路径。
 *
 * downloadCollectedFiles 统一把附件落 process.cwd()，且同名文件不覆盖--续问同一
 * contextId 下服务端常复用同一附件名，resolveUniqueTargetPath 会给后续同名文件加
 * (1)(2)… 后缀。但若 sanitize 只把 /project/xxx 替换成 <工作区>/<filename>（基本名），
 * 续问第 2、3 轮正文内联的路径就会指向第 1 轮已存在的同名文件，present_files 便只
 * 呈现第 1 轮的文件（实际第 2 轮落的是 <filename> (1).md）。
 *
 * 本函数在 SSE 先行 / 轮询解析阶段（下载前）用与 downloadCollectedFiles 完全相同的
 * resolveUniqueTargetPath(process.cwd(), filename) 预测带后缀的真实路径。关键不变量：
 * 同一进程内、对同一文件名，本函数与 downloadCollectedFiles 看到的磁盘状态一致
 * （下载尚未发生，二者之间没有别的文件创建），故结果恒等--正文内联路径与
 * REPORT_FULL_FILE 落盘路径始终一致。
 */
function resolveInlineLocalPath(filename) {
  return resolveUniqueTargetPath(process.cwd(), filename);
}

const DOWNLOAD_404_RETRY_DELAYS_MS = [1500, 2000, 3000, 5000, 8000];

async function downloadOneFile({ url, targetPath, apiKey }) {
  for (let attempt = 0; ; attempt++) {
    let response;
    try {
      response = await fetch(url, {
        method: "GET",
        headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      });
    } catch (e) {
      return { ok: false, error: `网络错误：${formatErrorDetail(e)}` };
    }

    if (response.status === 404 && attempt < DOWNLOAD_404_RETRY_DELAYS_MS.length) {
      try { await response.text(); } catch {}
      const delay = DOWNLOAD_404_RETRY_DELAYS_MS[attempt];
      if (attempt === 0) {
        console.log(`[CLI] 文件暂未在服务端就绪（HTTP 404），${delay}ms 后重试…`);
      }
      await sleep(delay);
      continue;
    }

    if (!response.ok) {
      let snippet = "";
      try {
        const text = await response.text();
        snippet = text ? `，${text.slice(0, 200)}` : "";
      } catch {}
      return {
        ok: false,
        error: `HTTP ${response.status} ${response.statusText}${snippet}`,
      };
    }

    if (!response.body) {
      return { ok: false, error: "响应体为空" };
    }

    try {
      const ws = createWriteStream(targetPath);
      if (/\.md$/i.test(targetPath)) {
        ws.write(UTF8_BOM);
      }
      await pipeline(Readable.fromWeb(response.body), ws);
      return { ok: true, path: targetPath };
    } catch (e) {
      try { unlinkSync(targetPath); } catch {}
      return { ok: false, error: `写入失败：${e.message}` };
    }
  }
}

/**
 * 打印一条 .md 附件的 REPORT_FULL_FILE 机器可读标记（仅 stderr），
 * 供上层 Agent 准确区分 REPORT_FILE（agentResult.value 兜底摘要）与"完整
 * 报告正文附件"。只对 .md 文件打标记，避免把 Excel/PDF 等数据附件误认为
 * 报告正文。
 *
 * 仅写 stderr 的原因：
 *   - stdout 主要承载 agentResult.value / SSE 正文等"主输出"，与控制标记分流；
 *   - 在合并显示 stdout+stderr 的终端中，避免每条标记被重复打印 2 次的视觉噪声；
 *   - Agent / 上层调用方通常会同时读取 stderr，机器可读标记不会丢失。
 */
function printReportFullFileTag(absPath, { reused = false, taskId = null, promptHash = null } = {}) {
  if (!/\.md$/i.test(absPath)) return;
  rememberReportFullFile(absPath);
  const reuseHint = reused
    ? `[CLI] （本次复用了 tasks.json 已记录的此前下载结果，未重新发起 HTTP 请求；跨进程去重生效。）`
    : null;
  const tagLines = [
    `REPORT_FULL_FILE=${absPath}`,
    `[CLI] REPORT_FULL_FILE 指向静默下载的完整 Markdown 附件（供用户本地查阅，不是 Agent 交付正文）。`,
    `[CLI] Agent 向用户只交付 agentResult.value 原文；不要读取本文件内容展示给用户。`,
    `[CLI] Agent 必须把本行 REPORT_FULL_FILE 的绝对路径转告用户；禁止只说「已下载」而不写路径。`,
    `ALICE_USER_DOWNLOAD_HINT=完整报告已保存到：${absPath}`,
    ...(taskId ? [`REPORT_FULL_FILE_TASK_ID=${taskId}`] : []),
    ...(promptHash ? [`REPORT_FULL_FILE_PROMPT_HASH=${promptHash}`] : []),
    ...(reuseHint ? [reuseHint] : []),
  ];
  if (taskId || promptHash) {
    tagLines.push(
      "[CLI] REPORT_FULL_FILE 仅表示附件已静默下载；Agent 不要读取其内容展示给用户。",
    );
  }
  for (const line of tagLines) {
    console.error(line);
  }
}

/**
 * 把 collectedDownloads 中的待下载附件拉到本地。
 *
 * 同名文件不覆盖策略：
 *   - 目标目录已存在同名文件时，**绝不覆盖**、**也不静默复用**——旧文件可能
 *     来自别的任务 / 别的公司 / --new 之前的版本，内容与本次报告不一致；
 *     若按文件名复用，会把过期内容当成本次 REPORT_FULL_FILE 返给 Agent。
 *   - 因此始终走 resolveUniqueTargetPath，让新下载自动获得
 *     `<name> (1).md`、`<name> (2).md` 等后缀，旧文件原地保留。
 *
 * 同任务 URL 去重 + 跨进程下载锁（避免 Agent 连发多条 CLI 时同一附件落盘 (1)(2)…）：
 *   - registry 中同一 taskId 已记录 URL 且本地文件仍在 → 复用，零 HTTP；
 *   - 多个进程同时 completed：runDownloadWithLock 对 taskId+URL 互斥，持锁方下载并
 *     立刻 appendDownloadedFile；等待方 reload tasks.json 后复用，不再 resolveUniqueTargetPath。
 *   - 不传 registry/taskId 时（单测 / 纯命令行）无锁，仍只做进程内 Map 去重。
 *
 * @param {string} apiKey
 * @param {string|null|undefined} override     用户 -d 指定目录
 * @param {object} [ctx]
 * @param {import("./tasksRegistry.js").TasksRegistry} [ctx.registry]
 * @param {string} [ctx.taskId]
 */
async function downloadCollectedFiles(apiKey, override, ctx = {}) {
  if (collectedDownloads.size === 0) return;

  const { registry = null, taskId = null } = ctx;
  const rawItems = Array.from(collectedDownloads, ([url, filename]) => ({ url, filename }));
  collectedDownloads.clear();

  if (registry?.reload && taskId) {
    registry.reload(taskId);
  }

  const knownDownloads = registry && taskId
    ? new Map(registry.getDownloadedFiles(taskId).map((e) => [e.url, e]))
    : new Map();

  // 划分"复用"与"待下载"两组：
  //   - 复用：registry 已记录且本地文件仍存在，跳过 HTTP 请求；
  //   - 重下：registry 没记录、或记录指向的本地文件已被用户删除/移走。
  const reusable = [];
  const items = [];
  for (const item of rawItems) {
    const known = knownDownloads.get(item.url) ?? findReusableDownload(registry, taskId, item.url);
    if (known?.path && existsSync(known.path)) {
      reusable.push({ ...item, path: known.path });
    } else {
      items.push(item);
    }
  }

  const recordMeta = registry && taskId ? registry.findByTaskId(taskId) : null;
  const fileTagMeta = {
    taskId: taskId ?? null,
    promptHash: recordMeta?.promptHash ?? null,
  };

  if (reusable.length > 0) {
    console.log("");
    console.log(
      `=== 检测到 ${reusable.length} 个附件已在 tasks.json 中记录（跨进程去重命中），复用已有文件，不再重复下载 ===`,
    );
    for (const { filename, path: absPath } of reusable) {
      console.log(`- ${filename}`);
      console.log(`  复用：${absPath}`);
      printReportFullFileTag(absPath, { reused: true, ...fileTagMeta });
    }
  }

  if (items.length === 0) return;

  const workspaceDir = process.cwd();
  // 所有下载件（报告附件 / 数据附件 / 图片）统一落工作空间 process.cwd()，
  // 避免 -d 传成工作空间外目录或未传 -d（回落 ~/Downloads）时文件落外部、
  // 再由宿主 cp 到工作空间才能 present_files。
  const targetDirFor = (_filename) => workspaceDir;
  console.log("");
  console.log(`=== 检测到 ${items.length} 个可下载文件，正在下载到工作空间：${workspaceDir} ===`);

  for (const { url, filename } of items) {
    const performDownload = async () => {
      const targetPath = resolveUniqueTargetPath(targetDirFor(filename), filename);
      const result = await downloadOneFile({ url, targetPath, apiKey });
      if (result.ok && registry && taskId) {
        try {
          registry.appendDownloadedFile(taskId, {
            url,
            path: result.path,
            filename,
          });
        } catch (e) {
          console.error(`[warn] 写 tasks.json downloadedFiles 失败：${formatErrorDetail(e)}`);
        }
      }
      return result;
    };

    let outcome;
    if (registry && taskId) {
      outcome = await runDownloadWithLock(registry, taskId, url, performDownload);
    } else {
      const result = await performDownload();
      outcome = result?.ok
        ? { kind: "downloaded", result }
        : { kind: "failed", result };
    }

    if (outcome.kind === "reused") {
      const absPath = outcome.entry.path;
      console.log(`- ${filename}`);
      console.log(`  复用：${absPath}`);
      if (outcome.waited) {
        console.log("  （等待其它 CLI 进程完成下载后跨进程去重命中，未重复 HTTP）");
      }
      printReportFullFileTag(absPath, { reused: true, ...fileTagMeta });
      continue;
    }

    const result = outcome.result;
    if (result?.ok) {
      console.log(`- ${filename}`);
      console.log(`  已保存：${result.path}`);
      printReportFullFileTag(result.path, { reused: false, ...fileTagMeta });
    } else {
      console.error(`- ${filename}`);
      console.error(`  下载失败：${result?.error ?? "unknown"}`);
      console.error(`  原始 URL：${url}`);
    }
  }
}

/** @internal 单测专用 */
export function __clearCompletedRecordForResubmitForTesting(registry, promptHash) {
  return clearCompletedRecordForResubmit(registry, promptHash, { logPrefix: "[test]" });
}

/** @internal 单测专用：解析下载目录 */
export function __resolveDownloadDirForTesting(override) {
  return resolveDownloadDir(override);
}

/** @internal 单测：沙箱持久化失败退出码 */
export const __EXIT_SANDBOX_NO_PERSIST_FOR_TESTING = EXIT_SANDBOX_NO_PERSIST;

/** @internal 单测：执行 registerNewTaskRecord 并返回是否持久化成功 */
export function __registerNewTaskRecordForTesting({ registry, promptHash, prompt, taskId, contextId, downloadDir }) {
  return registerNewTaskRecord({ registry, promptHash, prompt, taskId, contextId, downloadDir });
}

/** @internal 单测专用：向 collectedDownloads 注入待下载项 */
export function __seedCollectedDownloadForTesting(url, filename) {
  collectedDownloads.set(url, filename);
}

/** @internal 单测专用：执行 downloadCollectedFiles 并返回 stdout 捕获（通过调用方 hook console.log） */
export async function __downloadCollectedFilesForTesting(apiKey, override, ctx) {
  return downloadCollectedFiles(apiKey, override, ctx);
}

function formatElapsed(ms) {
  const sec = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}m${String(s).padStart(2, "0")}s` : `${s}s`;
}

const PROGRESS_TICK_INTERVAL_MS = 20_000;
let progressTickerHandle = null;
let progressStartTime = 0;
let progressFinalReportSeen = false;
let lastProgressStatusLine = "";

function startProgressTicker(initialMessage) {
  stopProgressTicker();
  progressStartTime = Date.now();
  progressFinalReportSeen = false;
  lastProgressStatusLine = "";
  if (initialMessage) {
    console.log(`[等待中] ${initialMessage}`);
  }
  progressTickerHandle = setInterval(() => {
    const elapsed = Date.now() - progressStartTime;
    console.log(
      `[等待中] 已等待 ${formatElapsed(elapsed)}，Alice 仍在生成报告，请耐心等待...`,
    );
  }, PROGRESS_TICK_INTERVAL_MS);
  if (typeof progressTickerHandle.unref === "function") {
    progressTickerHandle.unref();
  }
}

function stopProgressTicker() {
  if (progressTickerHandle) {
    clearInterval(progressTickerHandle);
    progressTickerHandle = null;
  }
}

function elapsedSinceStart() {
  return progressStartTime ? Date.now() - progressStartTime : 0;
}

function summarizeStatusUpdate(event) {
  const result = event?.result;
  if (!result) return null;
  const state = result.status?.state ?? result.state;
  const parts = result.status?.message?.parts;
  let text = "";
  if (Array.isArray(parts)) {
    for (const p of parts) {
      if (p?.kind === "text" && typeof p.text === "string") {
        text = p.text.trim();
        if (text) break;
      }
    }
  }
  if (!text) return null;
  const prefix = state ? `状态=${state}` : "状态";
  const oneLine = text.replace(/\s+/g, " ");
  const snippet = oneLine.length > 80 ? oneLine.slice(0, 80) + "…" : oneLine;
  return `${prefix}：${snippet}`;
}

// Alice 服务端会通过 artifact-update 事件携带各种内部状态，artifact.name 命中
// 这里的黑名单时只代表"前端 UI 状态变更"等实现细节，跟用户能感知的研究进度无关，
// 直接打印形如 `[进度] artifact: UIState` 会让终端日志显得混乱怪异，统一跳过不输出。
const INTERNAL_ARTIFACT_NAMES = new Set([
  "UIState",
]);

function logProgressEvents(events) {
  if (!Array.isArray(events) || events.length === 0) return;

  for (const event of events) {
    const kind = event?.result?.kind;

    if (kind === "artifact-update") {
      const artifactName = event?.result?.artifact?.name;
      if (artifactName === "agentResult") {
        if (!progressFinalReportSeen) {
          progressFinalReportSeen = true;
          console.log(
            `[报告就绪] 用时 ${formatElapsed(elapsedSinceStart())}，开始接收最终报告...`,
          );
          stopProgressTicker();
        }
      } else if (artifactName && !INTERNAL_ARTIFACT_NAMES.has(artifactName)) {
        const line = `[进度] artifact: ${artifactName}`;
        if (line !== lastProgressStatusLine) {
          lastProgressStatusLine = line;
          console.log(line);
        }
      }
      continue;
    }

    if (kind === "status-update") {
      const summary = summarizeStatusUpdate(event);
      if (!summary) continue;
      const line = `[进度] ${summary}`;
      if (line === lastProgressStatusLine) continue;
      lastProgressStatusLine = line;
      console.log(line);
    }
  }
}

export function formatEventOutput(event) {
  return JSON.stringify(event, null, 2);
}

export function formatValueOutput(value, resolveLocalPath = null) {
  if (typeof value === "string") {
    return `agentResult.value: ${sanitizeAgentResultTextForDelivery(value, "", resolveLocalPath)}`;
  }
  return `agentResult.value: ${JSON.stringify(value, null, 2)}`;
}

function consumeSseText(state, text) {
  state.buffer += text;
  const blocks = state.buffer.split(/\r?\n\r?\n/);
  state.buffer = blocks.pop() ?? "";
  return parseSsePayload(blocks.join("\n\n"));
}

function printEvents(events) {
  for (const event of events) {
    if (
      event?.result?.kind !== "artifact-update" ||
      event?.result?.artifact?.name !== "agentResult"
    ) {
      continue;
    }
    console.log(formatEventOutput(event));
  }
}

function printAgentResultValues(values) {
  for (const value of values) {
    console.log(formatValueOutput(value, resolveInlineLocalPath));
  }
}

function logJsonRpcErrors(events) {
  if (!Array.isArray(events) || events.length === 0) return;
  for (const event of events) {
    if (!event || typeof event !== "object") continue;
    if (event.jsonrpc !== "2.0" || event.error == null) continue;
    if (event.error.code === KEY_MISSING_CODE) {
      dieKeyMissing();
      return;
    }
    if (jsonRpcErrorReported) continue;
    jsonRpcErrorReported = true;
    console.error("request failed (jsonrpc error):");
    console.error(JSON.stringify(event.error, null, 2));
    process.exitCode = 1;
  }
}

function trackAgentResultEvents(events) {
  if (agentResultSeen || !Array.isArray(events) || events.length === 0) return;
  for (const event of events) {
    const result = event?.result;
    if (
      result?.kind === "artifact-update" &&
      result?.artifact?.name === "agentResult"
    ) {
      agentResultSeen = true;
      return;
    }
  }
}

// 不打断流，只把 UIState artifact-update 里的 A2A.Markdown 文案累积起来：
// 正常对话流程中 UIState 也会被频繁刷新，无脑 throw 会误中断；
// 只在 main 里"流结束 + 无 agentResult"分支把它当作失败原因输出。
function trackUiStateNotices(events) {
  if (!Array.isArray(events) || events.length === 0) return;
  for (const event of events) {
    const result = event?.result;
    if (
      result?.kind !== "artifact-update" ||
      result?.artifact?.name !== "UIState"
    ) {
      continue;
    }
    const acc = [];
    const seen = new Set();
    collectServerNoticeTextParts(result.artifact, acc, seen);
    for (const text of acc) {
      if (!pendingUiStateNotices.includes(text)) {
        pendingUiStateNotices.push(text);
      }
    }
  }
}

function emitParsedEvents(events) {
  logServerUserNoticeIfPresent(events);
  logJsonRpcErrors(events);
  logProgressEvents(events);
  printEvents(events);
  const values = extractAgentResultValues(events);
  printAgentResultValues(values);
  accumulateAgentResultValues(values);
  accumulateDownloadsFromValues(values);
  trackAgentResultEvents(events);
  trackUiStateNotices(events);
}

function emitParsedEventsUnlessQuota(events) {
  try {
    emitParsedEvents(events);
    return false;
  } catch (e) {
    if (isKnownServerError(e)) {
      process.exitCode = e.exitCode ?? getServerNoticeExitCode();
      return true;
    }
    throw e;
  }
}

async function emitParsedEventsUnlessQuotaStreaming(reader, events) {
  try {
    emitParsedEvents(events);
    return false;
  } catch (e) {
    if (isKnownServerError(e)) {
      await reader.cancel().catch(() => {});
      process.exitCode = e.exitCode ?? getServerNoticeExitCode();
      return true;
    }
    throw e;
  }
}

const KEY_MISSING_CODE = -32603;

function dieKeyMissing() {
  die("KEY_MISSING", "WIND_API_KEY 未配置或已失效", {
    extraHint:
      `① 获取 / 重置 API Key：浏览器打开 ${WIND_ALICE_KEY_PAGE}\n` +
      `   （万得 Alice → 左下角头像 → 「设置」→「账户」标签页；旧 Key 失效时请点击「重置」生成新 Key）\n` +
      `② 通过 CLI 写入 Key（推荐）：\n` +
      `   node scripts/cli.mjs apikey-set <KEY>\n` +
      `   或手动编辑文件：${KEY_CONFIG_FILE}\n` +
      `   单行内容：WIND_API_KEY=<你的KEY>\n` +
      `③ 重试原命令\n` +
      `（出于安全考虑，仅支持此路径；不支持环境变量、不支持 skill 目录内 config.json。\n` +
      `  历史版本的无后缀 ${LEGACY_KEY_CONFIG_FILE} 仍可读取，但建议用 apikey-set 重新写入以迁移到 config.env）`,
  });
}

function consumeNonStreamBody(raw) {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) return;

  if (trimmed.includes("data:")) {
    const sseEvents = parseSsePayload(trimmed);
    if (sseEvents.length > 0) {
      if (emitParsedEventsUnlessQuota(sseEvents)) return;
      return;
    }
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) {
      if (emitParsedEventsUnlessQuota(parsed)) return;
      if (parsed.some((e) => e && typeof e === "object" && e.error != null)) {
        process.exitCode = 1;
      }
      return;
    }
    if (parsed && typeof parsed === "object") {
      if (parsed.jsonrpc === "2.0" && parsed.error != null) {
        if (parsed.error.code === KEY_MISSING_CODE) {
          dieKeyMissing();
        }
        console.error("request failed (jsonrpc error):");
        console.error(JSON.stringify(parsed.error, null, 2));
        process.exitCode = 1;
        return;
      }
      if (emitParsedEventsUnlessQuota([parsed])) return;
      return;
    }
  } catch {
    /* 非 JSON，按原文输出 */
  }

  console.log(trimmed);
}

async function drainSseStream(response, { attachMode = false } = {}) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const state = { buffer: "" };
  // 累积原始解码文本，便于"流静默结束 / 零有效事件"时把原文 dump 出来排查；
  // 累积长度做软上限，避免极端情况下吃满内存。
  let rawText = "";
  const RAW_TEXT_HARD_CAP = 64 * 1024;
  let totalEvents = 0;
  let attachTimedOut = false;

  // attach 模式下，给"收到首个 SSE 事件"加个 60s 超时：超时则主动 cancel reader，
  // 让上层据此判定 resubscribe 没拿到任何数据，回退到新建任务。
  let firstEventTimer = null;
  if (attachMode) {
    firstEventTimer = setTimeout(() => {
      attachTimedOut = true;
      reader.cancel().catch(() => {});
    }, ATTACH_FIRST_EVENT_TIMEOUT_MS);
    if (typeof firstEventTimer.unref === "function") firstEventTimer.unref();
  }

  const clearFirstEventTimer = () => {
    if (firstEventTimer) {
      clearTimeout(firstEventTimer);
      firstEventTimer = null;
    }
  };

  const appendRaw = (s) => {
    if (!s) return;
    if (rawText.length >= RAW_TEXT_HARD_CAP) return;
    const room = RAW_TEXT_HARD_CAP - rawText.length;
    rawText += s.length > room ? s.slice(0, room) : s;
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      appendRaw(chunk);
      const events = consumeSseText(state, chunk);
      if (events.length > 0) clearFirstEventTimer();
      totalEvents += events.length;
      if (await emitParsedEventsUnlessQuotaStreaming(reader, events)) {
        return { rawText, totalEvents, attachTimedOut };
      }
    }

    const remaining = decoder.decode();
    if (remaining) {
      appendRaw(remaining);
      const events = consumeSseText(state, remaining);
      if (events.length > 0) clearFirstEventTimer();
      totalEvents += events.length;
      if (await emitParsedEventsUnlessQuotaStreaming(reader, events)) {
        return { rawText, totalEvents, attachTimedOut };
      }
    }

    if (state.buffer.trim()) {
      const events = parseSsePayload(state.buffer);
      if (events.length > 0) clearFirstEventTimer();
      totalEvents += events.length;
      if (await emitParsedEventsUnlessQuotaStreaming(reader, events)) {
        return { rawText, totalEvents, attachTimedOut };
      }
    }
  } finally {
    clearFirstEventTimer();
  }

  return { rawText, totalEvents, attachTimedOut };
}

function formatStreamRawSnippet(rawText) {
  const text = rawText ?? "";
  const totalBytes = Buffer.byteLength(text, "utf8");
  const MAX_PRINT_CHARS = 4 * 1024;
  const truncated = text.length > MAX_PRINT_CHARS;
  const head = truncated ? text.slice(0, MAX_PRINT_CHARS) : text;
  return { head, totalBytes, truncated };
}

/**
 * 单次调用服务端 `tasks/get` 同步查询任务状态，不开 SSE。
 * 用于 --no-wait 探针模式：沙箱可能在数十秒内强制结束 CLI 进程，
 * 普通模式靠 SSE 等不到结果；本函数最多 15s 内返回 JSON 状态。
 *
 * 返回值：
 *   { kind: "completed", artifacts, raw }
 *   { kind: "working",   state, raw }
 *   { kind: "failed",    state, reason, raw }
 *   { kind: "unsupported", reason, raw }   服务端不支持 tasks/get
 *   { kind: "error",     reason }          网络 / 解析失败
 */
async function probeTaskOnce({ url, headers, taskId, contextId }) {
  const body = tasksGetBody({ taskId, contextId });
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), PROBE_HTTP_TIMEOUT_MS);
  let response;
  let bodyText = "";
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { ...headers, Accept: "application/json" },
      body: JSON.stringify(body),
      signal: ac.signal,
    });
  } catch (e) {
    clearTimeout(timer);
    return { kind: "error", reason: `tasks/get 请求失败：${e?.message ?? e}` };
  }
  try {
    bodyText = await response.text();
  } catch (e) {
    clearTimeout(timer);
    return { kind: "error", reason: `读取 tasks/get 响应失败：${e?.message ?? e}` };
  }
  clearTimeout(timer);

  if (!response.ok) {
    return {
      kind: "error",
      reason: `tasks/get HTTP ${response.status} ${response.statusText}：${bodyText.slice(0, 500)}`,
    };
  }

  let parsed;
  try {
    parsed = JSON.parse(bodyText);
  } catch {
    return { kind: "error", reason: `tasks/get 响应非 JSON：${bodyText.slice(0, 500)}` };
  }

  if (parsed?.error) {
    const code = parsed.error.code;
    if (code === -32601 || code === -32600) {
      return { kind: "unsupported", reason: `服务端不支持 tasks/get：${JSON.stringify(parsed.error)}`, raw: parsed };
    }
    return {
      kind: "error",
      reason: `tasks/get 返回 jsonrpc 错误：${JSON.stringify(parsed.error)}`,
      raw: parsed,
    };
  }

  const result = parsed?.result;
  const state = result?.status?.state ?? result?.state ?? "unknown";
  const artifacts = Array.isArray(result?.artifacts) ? result.artifacts : [];

  if (state === "completed") {
    return { kind: "completed", artifacts, raw: parsed };
  }
  if (TERMINAL_STATUS_STATES.has(state)) {
    const reason =
      result?.status?.message?.parts?.find?.((p) => p?.kind === "text")?.text ??
      `任务终态：${state}`;
    return { kind: "failed", state, reason, raw: parsed };
  }
  return { kind: "working", state, raw: parsed };
}

/** tasks/get 探针是否表示「旧 taskId 在服务端已不存在」（仅此情况才允许 attach 回退新建）。 */
export function isTaskNotFoundProbe(probe) {
  if (!probe || probe.kind !== "error") return false;
  const code = probe.raw?.error?.code;
  if (code === -32001 || code === -32602) return true;
  const text = `${probe.reason ?? ""} ${JSON.stringify(probe.raw?.error ?? "")}`;
  return /task not found|任务不存在|任务未找到|not found/i.test(text);
}

/**
 * 从 tasks/get 的 completed 探针结果落盘 agentResult、下载附件（SSE 主流程与 --no-wait 探针共用）。
 */
async function finalizeTaskFromProbeCompleted({
  probe,
  registry,
  taskId,
  promptHash,
  prompt,
  apiKey,
  downloadDir,
  logPrefix = "[探针]",
}) {
  registry.reload?.(taskId);
  const prior = registry.findByTaskId(taskId);
  const priorMd = registry
    .getDownloadedFiles(taskId)
    .find((e) => /\.md$/i.test(e.path ?? "") && existsSync(e.path));
  if (prior?.status === "completed" && priorMd) {
    console.log(`${logPrefix} 任务已由其它 CLI 进程完成并落盘，复用 tasks.json 记录（不再重复下载）。`);
    if (__getServerUsageSessionForTesting().action === "attach") {
      notePeerFinalize({ taskId });
    } else {
      announceServerUsage({
        action: "reuse_peer_finalize",
        taskId,
        promptHash,
        registry,
        reusedPeerFinalize: true,
      });
    }
    replayCompletedArtifacts({ registry, taskId, promptHash, logPrefix });
    return true;
  }

  let finLock = tryAcquireDownloadLock(taskId, "__finalize__");
  if (!finLock.acquired) {
    const deadline = Date.now() + 120_000;
    while (Date.now() < deadline) {
      registry.reload?.(taskId);
      const r = registry.findByTaskId(taskId);
      const md = registry
        .getDownloadedFiles(taskId)
        .find((e) => /\.md$/i.test(e.path ?? "") && existsSync(e.path));
      if (r?.status === "completed" && md) {
        console.log(`${logPrefix} 等待其它 CLI 完成落盘…已复用 tasks.json（不再重复下载）。`);
        if (__getServerUsageSessionForTesting().action === "attach") {
          notePeerFinalize({ taskId });
        } else {
          announceServerUsage({
            action: "reuse_peer_finalize",
            taskId,
            promptHash,
            registry,
            reusedPeerFinalize: true,
          });
        }
        replayCompletedArtifacts({ registry, taskId, promptHash, logPrefix });
        return true;
      }
      await sleep(200);
    }
    finLock = tryAcquireDownloadLock(taskId, "__finalize__");
    if (!finLock.acquired) {
      registry.reload?.(taskId);
      const r = registry.findByTaskId(taskId);
      const md = registry
        .getDownloadedFiles(taskId)
        .find((e) => /\.md$/i.test(e.path ?? "") && existsSync(e.path));
      if (r?.status === "completed" && md) {
        replayCompletedArtifacts({ registry, taskId, promptHash, logPrefix });
        return true;
      }
      console.error(
        `${logPrefix} 另一 CLI 仍在落盘本任务；禁止连发多条 CLI。请 status 或阻塞等待其 DONE。`,
      );
      return false;
    }
  }

  try {
    registry.reload?.(taskId);
    const again = registry.findByTaskId(taskId);
    const againMd = registry
      .getDownloadedFiles(taskId)
      .find((e) => /\.md$/i.test(e.path ?? "") && existsSync(e.path));
    if (again?.status === "completed" && againMd) {
      replayCompletedArtifacts({ registry, taskId, promptHash, logPrefix });
      return true;
    }

    console.log(
      `${logPrefix} 服务端返回 status=completed，开始解析 ${probe.artifacts.length} 个 artifact...`,
    );
    const syntheticEvents = probe.artifacts.map((artifact) => ({
      jsonrpc: "2.0",
      result: { kind: "artifact-update", artifact },
    }));
    const values = extractAgentResultValues(syntheticEvents);
    printAgentResultValues(values);
    accumulateAgentResultValues(values);
    accumulateDownloadsFromValues(values);
    if (values.length === 0) {
      console.error(`${logPrefix} 服务端报告 completed 但未提取到 agentResult.value，按失败处理。`);
      registry.markFailed(taskId, "tasks/get returned completed but no agentResult.value");
      return false;
    }
    agentResultSeen = true;
    persistAgentResultIfAny({ registry, taskId, promptHash, prompt });
    registry.markCompleted(taskId);
    await downloadCollectedFiles(apiKey, downloadDir, { registry, taskId });
    return true;
  } finally {
    if (finLock?.acquired) releaseDownloadLock(finLock);
  }
}

/**
 * 循环 tasks/get 直到任务进入终态。用于 attach 后 resubscribe 空流、但服务端任务仍在跑的场景。
 *
 * @returns {{ status: "completed"|"failed"|"not_found"|"timeout", exitCode?: number, reason?: string }}
 */
async function pollTaskUntilTerminal({
  url,
  headers,
  apiKey,
  registry,
  promptHash,
  prompt,
  taskId,
  contextId,
  downloadDir,
  logPrefix,
  firstProbe,
}) {
  const deadline = Date.now() + WATCH_MAX_TIMEOUT_SEC * 1000;
  const startedAt = Date.now();
  let probe = firstProbe;
  let round = 0;

  while (true) {
    round += 1;

    if (probe.kind === "completed") {
      const ok = await finalizeTaskFromProbeCompleted({
        probe,
        registry,
        taskId,
        promptHash,
        prompt,
        apiKey,
        downloadDir,
        logPrefix,
      });
      return { status: ok ? "completed" : "failed", exitCode: ok ? 0 : 1 };
    }

    if (probe.kind === "failed") {
      console.error(`${logPrefix} 服务端任务终态：state=${probe.state}，原因：${probe.reason}`);
      registry.markFailed(taskId, probe.reason);
      return { status: "failed", exitCode: 1 };
    }

    if (probe.kind === "error" && isTaskNotFoundProbe(probe)) {
      return { status: "not_found" };
    }

    if (Date.now() >= deadline) {
      return {
        status: "timeout",
        exitCode: 1,
        reason: `tasks/get 轮询 ${formatElapsed(WATCH_MAX_TIMEOUT_SEC * 1000)} 后任务仍未完成`,
      };
    }

    const elapsed = Date.now() - startedAt;
    const currentIntervalSec = getAcceleratedIntervalSec(elapsed, WATCH_DEFAULT_INTERVAL_SEC);
    const sleepMs = Math.min(currentIntervalSec * 1000, deadline - Date.now());

    const state = probe.kind === "working" ? probe.state : "unknown";
    if (round === 1 && probe.kind === "working") {
      console.log(
        `${logPrefix} 服务端任务仍在执行（state=${state}），进入 tasks/get 轮询等待，**不会**新建任务。`,
      );
    } else if (probe.kind === "working") {
      console.log(
        `${logPrefix} 任务仍在执行（state=${state}），${currentIntervalSec}s 后再次探针...`,
      );
    } else if (probe.kind === "unsupported") {
      console.log(`${logPrefix} ${probe.reason}`);
      console.log(
        `${logPrefix} 将继续以 ${currentIntervalSec}s 间隔轮询 tasks/get（不新建任务）...`,
      );
    } else {
      console.log(
        `${logPrefix} tasks/get 暂不可用（${probe.reason}），${currentIntervalSec}s 后重试...`,
      );
    }

    await new Promise((r) => setTimeout(r, sleepMs));
    probe = await probeTaskOnce({ url, headers, taskId, contextId });
  }
}

/**
 * attach 模式下 tasks/resubscribe 未收到 agentResult（空 SSE 或超时）时，
 * 用 tasks/get 确认服务端真实状态，避免误杀仍在运行的任务并白白新建消耗额度。
 *
 * @returns {{ handled: boolean, shouldFallbackToNew: boolean, fallbackReason?: string }}
 */
async function recoverAttachAfterEmptySse({
  drainResult,
  url,
  headers,
  apiKey,
  registry,
  promptHash,
  prompt,
  taskId,
  contextId,
  downloadDir,
}) {
  const { rawText = "", totalEvents = 0, attachTimedOut = false } = drainResult ?? {};
  const sseHint = attachTimedOut
    ? `tasks/resubscribe ${formatElapsed(ATTACH_FIRST_EVENT_TIMEOUT_MS)} 内未收到任何 SSE 事件`
    : `tasks/resubscribe 未推送有效 SSE（${totalEvents} 事件 / ${Buffer.byteLength(rawText, "utf8")} 字节）`;

  console.log(`[任务复用] ${sseHint}，改用 tasks/get 确认服务端任务是否仍在执行...`);

  resetSessionState();
  currentSessionContextId = contextId;

  const firstProbe = await probeTaskOnce({ url, headers, taskId, contextId });
  const outcome = await pollTaskUntilTerminal({
    url,
    headers,
    apiKey,
    registry,
    promptHash,
    prompt,
    taskId,
    contextId,
    downloadDir,
    logPrefix: "[任务复用]",
    firstProbe,
  });

  if (outcome.status === "completed") {
    return { handled: true, shouldFallbackToNew: false };
  }
  if (outcome.status === "failed" || outcome.status === "timeout") {
    if (outcome.status === "timeout") {
      console.error(`[任务复用] ${outcome.reason}`);
      registry.markFailed(taskId, outcome.reason);
      process.exitCode = outcome.exitCode ?? 1;
    }
    return { handled: true, shouldFallbackToNew: false };
  }
  if (outcome.status === "not_found") {
    return {
      handled: false,
      shouldFallbackToNew: true,
      fallbackReason: `${sseHint}，且 tasks/get 确认旧任务已不存在`,
    };
  }
  return { handled: false, shouldFallbackToNew: true, fallbackReason: sseHint };
}

/**
 * 单次探针的核心逻辑：调用服务端 tasks/get → 解析响应 → 把结果写回 registry / 落盘 /
 * 拉取附件 / 打印 agentResult.value。**不会**自行设置 process.exitCode 或打印
 * `ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=...`，由调用方（单次 probe / watch 轮询）在合适
 * 时机统一发布，避免 watch 循环中每一轮都喷一行机器可读状态把 stdout 搞乱。
 *
 * 返回 { outcome, exitCode }：
 *   - "completed" / 0                  : 本地或服务端已确认任务成功完成
 *   - "failed"    / 1                  : 本地或服务端已确认任务失败 / 终态 failed/canceled/rejected
 *   - "no-task"   / EXIT_PROBE_NO_TASK : 本地 tasks.json 没有该 prompt 的 running 记录
 *   - "working"   / EXIT_PROBE_STILL_RUNNING : 服务端仍在执行；或本次 probe 临时失败 / 服务端不支持 tasks/get
 *
 * Bug 修复：completed 分支会立刻调用 downloadCollectedFiles 把 agentResult.value
 * 中识别到的可下载附件拉到当前工作空间（process.cwd()），与 SSE 主流程保持一致；以前的实现
 * 只 accumulate 但漏调 download，导致 --no-wait 模式拿到报告但不下载文件。
 */
/**
 * resume 窗口内本地 failed、但可能是客户端/SSE 误判时，用 tasks/get 对齐服务端真实状态。
 * @returns {"completed"|"failed"|"working"|"not_found"|"unchanged"}
 */
async function reconcileFailedRecordViaProbe({
  registry,
  promptHash,
  prompt,
  url,
  headers,
  apiKey,
  downloadDir,
  logPrefix = "[探针]",
}) {
  const record = findLatestFailedForProbe(registry, promptHash);
  if (!record || !shouldProbeFailedRecord(record)) return "unchanged";

  const { taskId: failedTaskId, contextId: failedContextId } = record;

  console.log(
    `${logPrefix} 本地记录为 failed（${record.failReason ?? "未知"}），但在 resume 窗口内；先用 tasks/get 确认服务端是否已完成，避免重复提交任务。`,
  );
  console.log(`${logPrefix} taskId    = ${failedTaskId}`);
  console.log(`${logPrefix} contextId = ${failedContextId}`);

  resetSessionState();
  currentSessionContextId = failedContextId;
  const probe = await probeTaskOnce({
    url,
    headers,
    taskId: failedTaskId,
    contextId: failedContextId,
  });

  if (probe.kind === "completed") {
    const ok = await finalizeTaskFromProbeCompleted({
      probe,
      registry,
      taskId: failedTaskId,
      promptHash,
      prompt,
      apiKey,
      downloadDir,
      logPrefix,
    });
    return ok ? "completed" : "failed";
  }
  if (probe.kind === "working") {
    record.status = "running";
    delete record.failReason;
    record.lastSeenAt = Date.now();
    registry.save();
    console.log(
      `${logPrefix} 服务端任务仍在执行（state=${probe.state}），本地已恢复为 running；继续轮询，**不会**新建任务。`,
    );
    return "working";
  }
  if (probe.kind === "failed") {
    registry.markFailed(failedTaskId, probe.reason ?? `服务端终态：${probe.state}`);
    return "failed";
  }
  if (probe.kind === "error" && isTaskNotFoundProbe(probe)) {
    registry.removeByTaskId(failedTaskId);
    console.log(`${logPrefix} 服务端已无此 taskId，已清除本地 failed 记录。`);
    return "not_found";
  }

  console.log(
    `${logPrefix} tasks/get 暂不可用（${probe.reason ?? probe.kind}）；保留本地 failed，不新建任务。`,
  );
  return "unchanged";
}

/**
 * attach 前对本地 running 记录做一次 tasks/get 探针，确认服务端是否其实已经 completed。
 *
 * 设计动机：沙箱 / IDE 终端短超时会杀掉 CLI 进程；被杀后本地 tasks.json 仍停在 running，
 * 但服务端可能早已完成。如果下一轮 --no-wait 直接 attach 走 SSE 等待，会再次被杀在
 * 长连接中途，Agent 永远拿不到 DONE（本次广钢气体现场即如此：服务端 5 分钟完成，
 * CLI 进程每次都被杀在第一轮 probe 之前）。此函数在 attach 前先做一次同步 tasks/get：
 *   - completed → 直接 finalize + replay，秒退交付，不再进 SSE
 *   - working   → 维持 running，正常 attach
 *   - 其它      → 维持 running，正常 attach（让后续流程兜底）
 *
 * 返回值与 reconcileFailedRecordViaProbe 对齐：
 *   "completed" | "working" | "unchanged"
 */
async function reconcileRunningRecordViaProbe({
  registry,
  promptHash,
  prompt,
  url,
  headers,
  apiKey,
  downloadDir,
  logPrefix = "[探针]",
}) {
  // 无 url（单测 / 配置缺失场景）时不探针，保持原有 attach 行为，向后兼容。
  if (!url || !headers) return "unchanged";

  const record = registry.findLatestByPromptHash(promptHash);
  if (!record || record.status !== "running") return "unchanged";

  const { taskId, contextId } = record;
  if (!taskId || !contextId) return "unchanged";

  console.log(
    `${logPrefix} 本地记录为 running，attach 前先用 tasks/get 确认服务端是否已完成，避免进 SSE 后被沙箱截断。`,
  );
  console.log(`${logPrefix} taskId    = ${taskId}`);
  console.log(`${logPrefix} contextId = ${contextId}`);

  resetSessionState();
  currentSessionContextId = contextId;
  const probe = await probeTaskOnce({ url, headers, taskId, contextId });

  if (probe.kind === "completed") {
    const ok = await finalizeTaskFromProbeCompleted({
      probe,
      registry,
      taskId,
      promptHash,
      prompt,
      apiKey,
      downloadDir,
      logPrefix,
    });
    return ok ? "completed" : "unchanged";
  }
  if (probe.kind === "working") {
    record.lastSeenAt = Date.now();
    registry.save();
    console.log(
      `${logPrefix} 服务端任务仍在执行（state=${probe.state}），继续 attach 续接。`,
    );
    return "working";
  }
  if (probe.kind === "failed") {
    registry.markFailed(taskId, probe.reason ?? `服务端终态：${probe.state}`);
    console.log(
      `${logPrefix} 服务端任务已 failed（${probe.reason ?? probe.state}）；本地已同步为 failed，将按 failed 路径处理。`,
    );
    return "unchanged";
  }

  console.log(
    `${logPrefix} tasks/get 暂不可用（${probe.reason ?? probe.kind}）；维持 running，继续 attach。`,
  );
  return "unchanged";
}

/**
 * --no-wait 专用：持续读取 message/stream SSE 流，直到收到 agentResult（完成）
 * 或超时 / 流断开。替代 readFirstServerTaskIds 的"读首事件就断开"策略。
 *
 * 返回值：
 *   { ok: true,  taskId, contextId, completed: true }  SSE 流中已完成
 *   { ok: true,  taskId, contextId, completed: false } SSE 流超时 / 断开，需降级 tasks/get 轮询
 *   { ok: false, reason }                               未能解析 taskId
 */
async function drainSseForNoWait(response, {
  clientTaskId,
  clientContextId,
  registry,
  promptHash,
  prompt,
  downloadDir,
  apiKey,
  timeoutMs = NO_WAIT_SSE_PHASE_TIMEOUT_MS,
}) {
  if (!response?.body || typeof response.body.getReader !== "function") {
    return { ok: false, reason: "响应体为空或不可读" };
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const state = { buffer: "" };
  let timedOut = false;
  let idsResolved = false;
  let resolvedTaskId = null;
  let resolvedContextId = null;

  const timer = setTimeout(() => {
    timedOut = true;
    reader.cancel().catch(() => {});
  }, timeoutMs);

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        // SSE 流正常结束
        if (idsResolved) {
          return { ok: true, taskId: resolvedTaskId, contextId: resolvedContextId, completed: agentResultSeen };
        }
        return {
          ok: false,
          reason: timedOut
            ? `${timeoutMs}ms SSE 先行超时`
            : "SSE 流在解析 taskId 前结束",
        };
      }

      const chunk = decoder.decode(value, { stream: true });
      const events = consumeSseText(state, chunk);

      for (const event of events) {
        // 提取服务端 taskId / contextId（首事件）
        if (!idsResolved) {
          const ids = extractServerTaskIds(event);
          if (ids) {
            idsResolved = true;
            resolvedTaskId = ids.taskId;
            resolvedContextId = ids.contextId;
          }
        }

        // 处理 SSE 事件（打印 agentResult.value 等）
        emitParsedEvents([event]);
      }

      // 检查是否已收到 agentResult（任务完成信号）
      if (agentResultSeen && idsResolved) {
        clearTimeout(timer);
        // 持久化 + 下载
        persistAgentResultIfAny({ registry, taskId: resolvedTaskId, promptHash, prompt });
        registry.markCompleted(resolvedTaskId);
        await downloadCollectedFiles(apiKey, downloadDir, { registry, taskId: resolvedTaskId });
        return { ok: true, taskId: resolvedTaskId, contextId: resolvedContextId, completed: true };
      }

      // 服务端用户提示（额度超限等）
      if (serverUserNoticeHandled && idsResolved) {
        clearTimeout(timer);
        return { ok: true, taskId: resolvedTaskId, contextId: resolvedContextId, completed: false };
      }
    }
  } catch (e) {
    if (idsResolved) {
      // 读取出错但已有 taskId，降级到轮询
      return { ok: true, taskId: resolvedTaskId, contextId: resolvedContextId, completed: false };
    }
    return {
      ok: false,
      reason: timedOut
        ? `${timeoutMs}ms SSE 先行超时`
        : `读取 SSE 失败：${e?.message ?? e}`,
    };
  } finally {
    clearTimeout(timer);
  }
}

/**
 * 读取 message/stream 响应体的首个 SSE 事件，提取服务端**自己分配**的 taskId / contextId。
 *
 * 背景：A2A 规范允许客户端在 message/stream 请求体里预生成 taskId/contextId，
 * 但服务端真正用来落任务、对外暴露给 tasks/get 的 ID 是它在首事件里下发的那一份。
 * --no-wait 模式过去拿到 HTTP 200 就立刻 `response.body.cancel()`，等于把这一份 ID 扔了，
 * 导致后续所有 tasks/get 都拿客户端 ID 去查 → 永远 -32001 Task not found。
 *
 * 本函数：流式 read → 解析 SSE → 命中第一个含 taskId+contextId 的事件即 cancel 并返回。
 * 全程默认 PROBE_HTTP_TIMEOUT_MS (=15s) 超时，超时 / 流提前 done / 网络错都返回 ok:false。
 */
async function readFirstServerTaskIds(
  response,
  { timeoutMs = PROBE_HTTP_TIMEOUT_MS } = {},
) {
  if (!response?.body || typeof response.body.getReader !== "function") {
    return { ok: false, reason: "响应体为空或不可读" };
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const state = { buffer: "" };
  let timedOut = false;
  const timer =
    timeoutMs > 0
      ? setTimeout(() => {
          timedOut = true;
          reader.cancel().catch(() => {});
        }, timeoutMs)
      : null;
  if (timer && typeof timer.unref === "function") timer.unref();

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        return {
          ok: false,
          reason: timedOut
            ? `${timeoutMs}ms 内未收到含 taskId 的 SSE 事件`
            : "SSE 流在拿到 taskId 前结束",
        };
      }
      const chunk = decoder.decode(value, { stream: true });
      const events = consumeSseText(state, chunk);
      for (const event of events) {
        const ids = extractServerTaskIds(event);
        if (ids) {
          await reader.cancel().catch(() => {});
          return { ok: true, ...ids };
        }
      }
    }
  } catch (e) {
    return {
      ok: false,
      reason: timedOut
        ? `${timeoutMs}ms 内未收到含 taskId 的 SSE 事件`
        : `读取 SSE 失败：${e?.message ?? e}`,
    };
  } finally {
    if (timer) clearTimeout(timer);
  }
}

/**
 * --no-wait 专用：本地无记录时自动 message/stream 提交任务，并**读取首个 SSE 事件**拿到
 * 服务端真实的 taskId/contextId 后再断开。修复历史上"提交完立刻 cancel → tasks/get 永远 404"
 * 的 bug（VS Codex / Trae 等沙箱场景极易踩中）。
 */
async function submitTaskForNoWaitMode({
  url,
  headers,
  apiKey,
  prompt,
  registry,
  promptHash,
  downloadDir,
  forceNew = false,
  newSession = false,
  continueSession = false,
  sessionScope,
}) {
  // 重复提交防护：拦截 Agent 换 prompt 重试导致的"新建第二条相似任务"。
  // --no-wait 与 --new 互斥，因此此处 forceNew 默认为 false；保留参数仅为
  // 同函数被普通模式 / 测试场景调用时的扩展性。
  if (await enforceDuplicateGuard({
    registry,
    prompt,
    promptHash,
    forceNew,
    url,
    headers,
    apiKey,
  })) {
    return { ok: false, duplicate: true };
  }
  // 跨进程提交锁：tasks.json 写入失败时，防止同一 prompt 被并发 CLI 重复提交
  if (enforceSubmitLock({ promptHash, prompt, forceNew })) {
    return { ok: false, duplicate: true };
  }
  // 会话上下文复用：默认在工作区内自动续接（process.cwd() 隔离防串号），空闲窗口内
  // 复用上次 contextId；`--new-session` 强制新会话；显式 `--context-id` 优先级最高。
  const reuseContextId = currentExplicitContextId
    || resolveSessionContextId({ forceNewSession: newSession, continueSession, sessionScope, workspaceDir: process.cwd() });
  const newTaskBody = buildBody(prompt, { reuseContextId });
  const clientTaskId = newTaskBody.params.message.taskId;
  const clientContextId = newTaskBody.params.message.contextId;
  if (reuseContextId && reuseContextId === clientContextId) {
    const scopeSuffix = sessionScope ? `；scope=${sessionScope}` : "";
    console.log(
      `[CLI] 会话续接：复用 contextId = ${clientContextId}（${currentExplicitContextId ? "--context-id 显式续接" : "工作区自动续接"}${scopeSuffix}）`,
    );
  }
  const initialSaveOk = registerNewTaskRecord({
    registry,
    promptHash,
    prompt,
    taskId: clientTaskId,
    contextId: clientContextId,
    downloadDir,
  });

  // tasks.json 不可写时阻止提交：沙箱（如 Workbuddy 不开完全访问权限）下
  // tasks.json 无法持久化，进程异常退出后下次无法续接，会导致重复扣积分。
  if (!initialSaveOk) {
    console.error(
      "[CLI] 当前环境无法保存任务状态，已阻止提交分析请求（未消耗积分）。" +
      "请在宿主工具中开启完全访问权限后重试。",
    );
    console.log("ALICE_SANDBOX_NO_PERSIST=1");
    console.log(
      `[CLI] 退出码 ${EXIT_SANDBOX_NO_PERSIST} = 环境受限，任务状态无法保存；` +
      "未向服务端发请求，不扣积分。请在宿主工具中开启完全访问权限后重试。",
    );
    return { ok: false, sandboxNoPersist: true };
  }

  currentSessionContextId = clientContextId;
  // 首次落盘会话：即便后续 server 会重绑 contextId，也确保这次调用崩溃 / 中断的话
  // 下次仍能续接上（server 重绑成功后会再覆盖一次）。sessionScope 决定落盘到哪份文件。
  maybeSaveCurrentSession({
    contextId: clientContextId,
    taskId: clientTaskId,
    promptHash,
    sessionScope,
  });

  console.log(
    "[CLI] --no-wait 自动提交：正在向服务端发起 message/stream（将读首个 SSE 事件拿真实 taskId）...",
  );
  console.log(`  client taskId    = ${clientTaskId}`);
  console.log(`  client contextId = ${clientContextId}`);

  // fetch headers 阶段单独的超时；body 阶段读首事件的超时由 readFirstServerTaskIds 控制。
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), PROBE_HTTP_TIMEOUT_MS);
  let response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(newTaskBody),
      signal: ac.signal,
    });
  } catch (e) {
    clearTimeout(timer);
    const aborted = e?.name === "AbortError";
    registry.markFailed(
      clientTaskId,
      aborted
        ? "auto-submit timeout before HTTP response"
        : `auto-submit network: ${e?.message ?? e}`,
    );
    console.error(
      `[CLI] --no-wait 自动提交失败：${
        aborted ? `${PROBE_HTTP_TIMEOUT_MS}ms 内未收到 HTTP 响应` : formatErrorDetail(e)
      }`,
    );
    return { ok: false };
  }
  clearTimeout(timer);

  if (!response.ok) {
    let errorText = "";
    try {
      errorText = await response.text();
    } catch {}
    if (handleServerNoticeInErrorBody(errorText, { registry, taskId: clientTaskId })) {
      return { ok: false, serverNotice: true };
    }
    registry.markFailed(clientTaskId, `auto-submit HTTP ${response.status}`);
    console.error(
      `[CLI] --no-wait 自动提交被拒绝：HTTP ${response.status} ${response.statusText}`,
    );
    if (errorText) console.error(errorText.slice(0, 500));
    return { ok: false };
  }

  // 关键修复：HTTP 200 后先持续读 SSE 流（SSE 先行阶段）。
  // 读到首事件提取 taskId/contextId 后不立刻断开，而是继续读：
  //   - 如果在 NO_WAIT_SSE_PHASE_TIMEOUT_MS 内收到 agentResult → 直接交付（零延迟）
  //   - 超时或流断开 → 降级到 tasks/get 轮询
  // 这样 2 分钟内完成的任务直接从 SSE 拿结果，无需轮询。
  const ssePhaseResult = await drainSseForNoWait(response, {
    clientTaskId,
    clientContextId,
    registry,
    promptHash,
    prompt,
    downloadDir,
    apiKey,
    timeoutMs: NO_WAIT_SSE_PHASE_TIMEOUT_MS,
  });

  if (!ssePhaseResult.ok) {
    // 未能从 SSE 首事件解析 taskId
    console.warn(
      `[CLI] --no-wait 未能从 SSE 流解析 taskId（${ssePhaseResult.reason}）。`,
    );
    console.warn(
      "[CLI] 将以客户端预生成 taskId 进行 tasks/get 探针；若服务端未采纳此 ID，可能反复返回 Task not found。",
    );
    registry.touch(clientTaskId);
    console.log(
      "[CLI] --no-wait 自动提交完成：进入 tasks/get 内部自旋等待结果。",
    );
    return { ok: true, taskId: clientTaskId, contextId: clientContextId, completed: false };
  }

  const { taskId: serverTaskId, contextId: serverContextId } = ssePhaseResult;
  if (serverTaskId !== clientTaskId || serverContextId !== clientContextId) {
    console.log(
      "[CLI] 服务端首事件已下发真实 taskId / contextId，正在重绑本地 tasks.json 记录：",
    );
    console.log(`  server taskId    = ${serverTaskId}`);
    console.log(`  server contextId = ${serverContextId}`);
    registry.removeByTaskId(clientTaskId);
    registerNewTaskRecord({
      registry,
      promptHash,
      prompt,
      taskId: serverTaskId,
      contextId: serverContextId,
      downloadDir,
    });
    currentSessionContextId = serverContextId;
    // server 若重绑 contextId（如复用无效被拒 → server 新签发），会话文件同步更新，
    // 下次续问才不会带着"已被服务端遗忘"的旧 contextId。
    maybeSaveCurrentSession({
      contextId: serverContextId,
      taskId: serverTaskId,
      promptHash,
      sessionScope,
    });
  } else {
    registry.touch(serverTaskId);
    // 服务端确认采纳客户端 contextId：刷新 lastUsedAt，避免长任务过程中窗口过期。
    maybeSaveCurrentSession({
      contextId: serverContextId,
      taskId: serverTaskId,
      promptHash,
      sessionScope,
    });
  }

  // SSE 先行阶段已直接拿到结果
  if (ssePhaseResult.completed) {
    console.log("[CLI] --no-wait SSE 先行：任务已在 SSE 流中完成，直接交付结果。");
    return { ok: true, taskId: serverTaskId, contextId: serverContextId, completed: true };
  }

  console.log(
    "[CLI] --no-wait 自动提交成功：进入 tasks/get 内部自旋等待结果。",
  );
  return { ok: true, taskId: serverTaskId, contextId: serverContextId, completed: false };
}

async function runProbeStep({ registry, taskId, promptHash, prompt, url, headers, apiKey, downloadDir }) {
  let record = taskId
    ? registry.findByTaskId(taskId)
    : registry.findLatestByPromptHash(promptHash);
  if (!record) {
    console.log("[探针] 本地 tasks.json 找不到该任务记录。");
    console.log("[探针] 带 --no-wait（默认内部自旋）时 CLI 会自动提交；--no-wait --once 需指定 TASK_ID 或先提交一次。");
    if (prompt && promptHash) {
      printArtifactGuardHints({
        prompt,
        promptHash,
        registry,
        downloadDir: resolveDownloadDir(downloadDir),
        kind: "probe_no_task",
      });
    }
    return { outcome: "no-task", exitCode: EXIT_PROBE_NO_TASK };
  }
  const activeTaskId = record.taskId;
  if (record.status === "completed") {
    console.log("[探针] 该任务在本地记录中已是 completed。");
    if (!__getServerUsageSessionForTesting().action) {
      announceServerUsage({
        action: "replay",
        taskId: activeTaskId,
        promptHash,
        registry,
        recoveredFromOtherProcess: true,
      });
    }
    replayCompletedArtifacts({ registry, taskId: activeTaskId, promptHash, logPrefix: "[探针]" });
    return { outcome: "completed", exitCode: 0 };
  }
  if (record.status === "failed") {
    const reconciled = await reconcileFailedRecordViaProbe({
      registry,
      promptHash,
      prompt,
      url,
      headers,
      apiKey,
      downloadDir,
      logPrefix: "[探针]",
    });
    if (reconciled === "completed") {
      return { outcome: "completed", exitCode: 0 };
    }
    if (reconciled === "working") {
      record = registry.findByTaskId(activeTaskId);
    } else if (reconciled === "failed" || reconciled === "unchanged") {
      record = registry.findByTaskId(activeTaskId);
      if (record?.status === "failed") {
        console.log(`[探针] 该任务在本地/服务端均为 failed：${record.failReason ?? "未知原因"}`);
        return { outcome: "failed", exitCode: 1 };
      }
    } else if (reconciled === "not_found") {
      return { outcome: "no-task", exitCode: EXIT_PROBE_NO_TASK };
    }
  }
  record = taskId ? registry.findByTaskId(taskId) : registry.findLatestByPromptHash(promptHash);
  if (!record) {
    return { outcome: "no-task", exitCode: EXIT_PROBE_NO_TASK };
  }

  const { taskId: probeTaskId, contextId } = record;
  currentSessionContextId = contextId;
  console.log(`[探针] 正在向服务端查询任务状态（tasks/get），最长 ${Math.round(PROBE_HTTP_TIMEOUT_MS / 1000)}s 内返回...`);
  console.log(`[探针] taskId    = ${probeTaskId}`);
  console.log(`[探针] contextId = ${contextId}`);

  resetSessionState();
  const probe = await probeTaskOnce({ url, headers, taskId: probeTaskId, contextId });

  if (probe.kind === "completed") {
    const ok = await finalizeTaskFromProbeCompleted({
      probe,
      registry,
      taskId: probeTaskId,
      promptHash,
      prompt,
      apiKey,
      downloadDir,
      logPrefix: "[探针]",
    });
    if (!ok) {
      return { outcome: "failed", exitCode: 1 };
    }
    console.log(`[探针] Alice 任务已完成。请将 stdout 中 agentResult.value 原文交给用户。`);
    console.log(`[探针]   - 禁止概括、摘录或改写 agentResult.value；`);
    console.log(`[探针]   - stdout 被截断时读 reportFile= 兜底；`);
    console.log(`[探针]   - 不要读取 reportFullFile= / download/ 附件向用户展示。`);
    return { outcome: "completed", exitCode: 0 };
  }

  if (probe.kind === "working") {
    console.log(`[探针] 服务端任务仍在执行中：state=${probe.state}`);
    console.log(
      `ALICE_POLL_HEARTBEAT status=working taskId=${probeTaskId} promptHash=${promptHash}`,
    );
    console.log(
      "[CLI] 本进程尚未输出 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE；logs/ 下其它 .session.log 内的 DONE 行与本 PROMPT_HASH 不一致则无效。",
    );
    return { outcome: "working", exitCode: EXIT_PROBE_STILL_RUNNING };
  }

  if (probe.kind === "failed") {
    console.error(`[探针] 服务端任务终态：state=${probe.state}，原因：${probe.reason}`);
    registry.markFailed(probeTaskId, probe.reason);
    return { outcome: "failed", exitCode: 1 };
  }

  if (probe.kind === "unsupported") {
    console.error(`[探针] ${probe.reason}`);
    console.error("[探针] 当前服务端不支持 tasks/get 同步查询；请去掉 --no-wait 重跑，CLI 会通过 tasks/resubscribe 续接（注意沙箱可能仍会截断长任务）。");
    return { outcome: "working", exitCode: EXIT_PROBE_STILL_RUNNING };
  }

  console.error(`[探针] ${probe.reason}`);
  return { outcome: "working", exitCode: EXIT_PROBE_STILL_RUNNING };
}

/**
 * 把 runProbeStep 的 outcome 翻译成机器可读的最终状态行 + 必要的人类可读提示。
 * 单次 probe（runProbeMode）和轮询（runWatchMode）共用同一个发布函数，确保
 * 调用方读到的 `ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=...` 语义一致。
 *
 * @param {"completed"|"failed"|"working"|"no-task"} outcome
 * @param {object} [opts]
 * @param {boolean} [opts.suggestExternalPoll] 仍在 working 时是否提示"请再次以 --no-wait 调用本 CLI"
 *   - 单次 probe 模式 = true（CLI 不会自旋，必须靠 Agent 再调一次）
 *   - watch 模式触顶超时 = true（提示 Agent 再发一次 --no-wait --watch 续轮询）
 *   - watch 模式中间某一轮还在工作 → 不应到这里（中间轮内部自己 sleep）
 */
function publishFinalStatus(outcome, { suggestExternalPoll = false } = {}) {
  switch (outcome) {
    case "completed":
      console.log("ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=COMPLETED");
      emitAnalysisDone();
      break;
    case "failed":
      console.log("ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=FAILED");
      break;
    case "no-task":
      console.log("ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=NO_TASK");
      break;
    case "working":
    default:
      if (suggestExternalPoll) {
        console.log(
          "[探针] 任务仍在执行。请再执行**一次**相同 --no-wait 命令续接；禁止 Agent 连发多条 CLI 或 Start-Sleep 循环。",
        );
        console.log(
          "[探针] 禁止读取 download/ 同名报告或 STALE_REPORT_CANDIDATE；必须见到 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 且 promptHash= 一致。",
        );
      }
      console.log("ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_STATUS=RUNNING");
      break;
  }
}

async function runStatusCommand({ prompt, downloadDir }) {
  const promptHash = computePromptHash(prompt);
  const registry = openRegistry();
  const record = registry.findLatestByPromptHash(promptHash);
  const resolvedDownloadDir = resolveDownloadDir(downloadDir);

  printPromptHashMarker(promptHash, record?.taskId);

  if (!record) {
    console.log("[status] 本地 tasks.json 无此 prompt 的记录。");
    console.log("[status] 请先执行分析命令；完成后可用本命令查询落盘路径，勿扫描 results/ 目录。");
    // 改进1：机器可读状态行（Agent 在 CLI 被反复杀死后可用此行确认是否已完成）
    console.log(
      `ALICE_TASK_STATUS=promptHash=${promptHash} status=no_task`,
    );
    printArtifactGuardHints({
      prompt,
      promptHash,
      registry,
      downloadDir: resolvedDownloadDir,
      kind: "no_local_record",
    });
    const replayCandidates = findSimilarCompleted(registry.records, prompt, {
      skipPromptHash: promptHash,
      windowMs: Math.min(CONFLICT_CHECK_REPLAY_WINDOW_MS, STALE_TASK_THRESHOLD_MS),
    });
    if (replayCandidates.length > 0) {
      console.log(
        `[status] 检测到 ${replayCandidates.length} 条相似已完成任务；禁止读取其 report 或 tasks.json 其它 taskId。`,
      );
      console.log(
        "[status] 请用 check-conflict 列给用户后，用已有任务的**原 prompt** 重放，或阻塞等待本次 --no-wait 的 DONE 行。",
      );
      process.exitCode = EXIT_STATUS_MISLEAD_RISK;
    } else {
      process.exitCode = EXIT_PROBE_NO_TASK;
    }
    publishFinalStatus("no-task");
    return;
  }

  console.log(`TASK_ID=${record.taskId}`);
  console.log(`TASK_LOCAL_STATUS=${record.status}`);
  if (record.promptPreview) {
    console.log(`TASK_PROMPT_PREVIEW=${record.promptPreview}`);
  }

  if (record.status === "completed") {
    // 改进1：机器可读完成状态行（Agent 在 CLI 被反复杀死后，跑一次 status 即可确认结果已就绪）。
    // 只读 tasks.json 注册表，不访问服务端、不猜目录文件，是沙箱被杀场景下的安全探针。
    const dlMd = registry
      .getDownloadedFiles(record.taskId)
      .find((e) => /\.md$/i.test(e.path ?? "") && existsSync(e.path));
    const parts = [
      `promptHash=${promptHash}`,
      `taskId=${record.taskId}`,
      `status=completed`,
      `resultFile=${record.resultPath ?? ""}`,
    ];
    if (dlMd?.path) parts.push(`reportFullFile=${dlMd.path}`);
    console.log(`ALICE_TASK_STATUS=${parts.join(" ")}`);
    announceServerUsage({
      action: "replay",
      taskId: record.taskId,
      promptHash,
      registry,
      recoveredFromOtherProcess: true,
    });
    replayCompletedArtifacts({ registry, promptHash, logPrefix: "[status]" });
    publishFinalStatus("completed");
    return;
  }
  if (record.status === "failed") {
    if (record.failReason) {
      console.log(`TASK_FAIL_REASON=${record.failReason}`);
    }
    console.log(
      `ALICE_TASK_STATUS=promptHash=${promptHash} taskId=${record.taskId} status=failed${record.failReason ? ` reason=${record.failReason}` : ""}`,
    );
    publishFinalStatus("failed");
    process.exitCode = 1;
    return;
  }

  console.log("[status] 任务仍在执行。请用相同 prompt 执行 --no-wait 等待完成。");
  console.log("[status] 禁止按 results/ 或 download/ 目录修改时间猜测报告文件。");
  console.log(
    `ALICE_TASK_STATUS=promptHash=${promptHash} taskId=${record.taskId} status=running`,
  );
  printAwaitingResultArtifactGuard({
    prompt,
    promptHash,
    registry,
    downloadDir,
  });
  publishFinalStatus("working");
  process.exitCode = EXIT_PROBE_STILL_RUNNING;
}

/** @internal 单测：重放 completed 落盘路径 */
export function __replayCompletedArtifactsForTesting(registry, promptHash) {
  return replayCompletedArtifacts({ registry, promptHash, logPrefix: "[test]" });
}

/** @internal 单测：attach 前对 running 记录的探针（无 url 时跳过，保持原 attach 行为） */
export async function __reconcileRunningRecordViaProbeForTesting(opts) {
  return reconcileRunningRecordViaProbe({ ...opts, logPrefix: "[test]" });
}

/** @internal 单测：runStatusCommand 的完成状态行格式化（不实际打印，避免依赖全局 console） */
export function __formatTaskStatusLineForTesting({
  promptHash,
  taskId,
  status,
  resultPath = "",
  reportFullFile = "",
  failReason = "",
}) {
  if (status === "no_task") {
    return `ALICE_TASK_STATUS=promptHash=${promptHash} status=no_task`;
  }
  if (status === "completed") {
    const parts = [
      `promptHash=${promptHash}`,
      `taskId=${taskId}`,
      `status=completed`,
      `resultFile=${resultPath}`,
    ];
    if (reportFullFile) parts.push(`reportFullFile=${reportFullFile}`);
    return `ALICE_TASK_STATUS=${parts.join(" ")}`;
  }
  if (status === "failed") {
    return `ALICE_TASK_STATUS=promptHash=${promptHash} taskId=${taskId} status=failed${failReason ? ` reason=${failReason}` : ""}`;
  }
  return `ALICE_TASK_STATUS=promptHash=${promptHash} taskId=${taskId} status=${status}`;
}

/** @internal 单测：artifact-guard 提示行 */
export function __printArtifactGuardHintsForTesting(opts) {
  return printArtifactGuardHints(opts);
}

/**
 * --no-wait 探针模式（单次）：同步查询服务端任务状态并尽快退出。
 * 设计目标：解决 Trae / 沙箱环境强制结束长任务进程后，普通模式无法
 * 通过 SSE 拿到最终报告的死锁问题；调用方反复调用此模式即可拉到结果。
 *
 * 注：调用方如果希望"一次 CLI 调用就把轮询节奏跑完"，请改用 --no-wait --watch
 * （runWatchMode），CLI 会内部 sleep + 反复 probe，免去 Agent 自己 Start-Sleep。
 */
async function runProbeMode(ctx) {
  const { outcome, exitCode } = await runProbeStep(ctx);
  publishFinalStatus(outcome, { suggestExternalPoll: outcome === "working" });
  if (exitCode) process.exitCode = exitCode;
}

/**
 * --no-wait 内部自旋：CLI 自旋 sleep + probe，直到任务进入终态或全程超时。
 *
 * 多轮 session：每轮最长 --watch-timeout（默认 30min），到点若仍未完成且未达
 * --watch-absolute-max（默认 60min），CLI **自动续下一轮**，不让 Agent 在外层连发
 * 命令（防 Trae「模型循环」熔断）。
 */
async function runWatchMode(ctx, { intervalSec, timeoutSec, absoluteMaxSec }) {
  const baseInterval = Math.max(WATCH_MIN_INTERVAL_SEC, intervalSec ?? WATCH_DEFAULT_INTERVAL_SEC);
  const sessionCapSec = Math.min(timeoutSec ?? WATCH_DEFAULT_TIMEOUT_SEC, WATCH_MAX_TIMEOUT_SEC);
  const absoluteCapSec = absoluteMaxSec ?? WATCH_ABSOLUTE_MAX_SEC;
  const absoluteStartedAt = Date.now();
  const absoluteDeadline = absoluteStartedAt + absoluteCapSec * 1000;

  console.log(
    `[轮询] 进入 --no-wait 内部自旋：初始 ${baseInterval}s 探针间隔（渐进缩短至 ${WATCH_MIN_INTERVAL_SEC}s），每轮最长 ${formatElapsed(sessionCapSec * 1000)}，全程最长 ${formatElapsed(absoluteCapSec * 1000)}。`,
  );
  console.log(
    "[轮询] 由 CLI 自行 sleep + 反复 tasks/get；到轮次上限自动续轮。Agent 禁止在外层 Start-Sleep 或连发多条 CLI。",
  );
  printAwaitingResultArtifactGuard({
    prompt: ctx.prompt,
    promptHash: ctx.promptHash,
    registry: ctx.registry,
    downloadDir: ctx.downloadDir,
  });

  let session = 0;
  while (Date.now() < absoluteDeadline) {
    session += 1;
    const sessionStartedAt = Date.now();
    const sessionDeadline = Math.min(
      sessionStartedAt + sessionCapSec * 1000,
      absoluteDeadline,
    );

    if (session > 1) {
      console.log(`[轮询] 第 ${session} 轮自旋（CLI 自动续轮，无需 Agent 再发命令）...`);
    }

    let round = 0;
    while (Date.now() < sessionDeadline) {
      round += 1;
      const absoluteElapsed = Date.now() - absoluteStartedAt;
      const sessionElapsed = Date.now() - sessionStartedAt;

      // 渐进式探针间隔：运行越久间隔越短，更快感知到服务端 completed
      const currentIntervalSec = getAcceleratedIntervalSec(absoluteElapsed, baseInterval);

      console.log(
        `[轮询] 第 ${round} 次 probe（本轮 ${formatElapsed(sessionElapsed)}，全程 ${formatElapsed(absoluteElapsed)} / ${formatElapsed(absoluteCapSec * 1000)}，下次间隔 ${currentIntervalSec}s）...`,
      );
      const { outcome, exitCode } = await runProbeStep(ctx);

      if (outcome === "completed" || outcome === "failed" || outcome === "no-task") {
        publishFinalStatus(outcome, { suggestExternalPoll: false });
        if (exitCode) process.exitCode = exitCode;
        return;
      }

      const remainingSession = sessionDeadline - Date.now();
      const remainingAbsolute = absoluteDeadline - Date.now();
      if (remainingAbsolute <= 0) break;

      if (remainingSession <= 0) break;

      const sleepMs = Math.min(currentIntervalSec * 1000, remainingSession, remainingAbsolute);
      console.log(
        `[轮询] 任务仍在执行（submitted 排队 / working 均属正常），sleep ${Math.round(sleepMs / 1000)}s 后再次 probe...`,
      );
      await new Promise((r) => setTimeout(r, sleepMs));
    }

    if (Date.now() >= absoluteDeadline) break;

    console.log(
      `[轮询] 本轮已达 --watch-timeout（${formatElapsed(sessionCapSec * 1000)}），任务仍在执行；CLI 自动进入下一轮...`,
    );
  }

  console.log(
    `[轮询] 已达全程上限 ${formatElapsed(absoluteCapSec * 1000)} 仍未完成；以 exit=${EXIT_PROBE_STILL_RUNNING} 退出。`,
  );
  console.log(
    "[轮询] Agent 只需再执行**一次**相同的 --no-wait 命令续接；禁止连发多条、禁止 --new、禁止 Start-Sleep 循环。",
  );
  publishFinalStatus("working", { suggestExternalPoll: true });
  process.exitCode = EXIT_PROBE_STILL_RUNNING;
}

async function main() {
  const argv = parseArgs(process.argv);

  if (argv.help) {
    console.log(usage());
    return;
  }

  if (argv.command === "apikey-set") {
    setApiKey(argv.subArg);
    return;
  }
  if (argv.command === "apikey-get") {
    printApiKeyStatus();
    return;
  }
  if (argv.command === "apikey-clear") {
    clearApiKey();
    return;
  }
  if (argv.command === "status") {
    if (!argv.prompt || !argv.prompt.trim()) {
      console.error("missing --prompt");
      console.error(usage());
      process.exitCode = 2;
      return;
    }
    await runStatusCommand({ prompt: argv.prompt, downloadDir: argv.downloadDir });
    return;
  }
  if (argv.command === "check-conflict") {
    if (!argv.prompt || !argv.prompt.trim()) {
      console.error("missing --prompt");
      console.error(usage());
      process.exitCode = 2;
      return;
    }
    await runCheckConflictCommand({ prompt: argv.prompt, downloadDir: argv.downloadDir });
    return;
  }

  const {
    prompt,
    downloadDir,
    forceNew,
    newSession,
    continueSession,
    explicitContextId,
    sessionScope,
    noWait,
    once,
    watch,
    watchExplicit,
    watchIntervalSec,
    watchTimeoutSec,
    watchAbsoluteMaxSec,
    noStrict,
  } = argv;
  if (!prompt || !prompt.trim()) {
    console.error("missing --prompt");
    console.error(usage());
    process.exitCode = 2;
    return;
  }

  // analysis 主路径：默认开启 strict 模式（未输出 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 即视为
  // 任务未真正完成；进程退出时若 exitCode 仍为 0，兜底改成 EXIT_STRICT_NO_DONE(6)）。
  // --once 单次探针仍在 working 时是合法的非 0 出口，strict 不会误判（exit=4）。
  markStrictRequired();
  installStrictExitHook();
  if (noStrict) {
    strictDisabled = true;
    console.error("[CLI][strict] --no-strict 已生效：未 emit DONE 也不会强制改退出码（仅调试 / 脚本场景使用）。");
  }
  if (once && !noWait) {
    console.error("[CLI] --once 需与 --no-wait 一起用。");
    process.exitCode = 2;
    return;
  }
  if (noWait && forceNew && once) {
    console.error("[CLI] --new 与 --no-wait --once 互斥：--once 仅探针不提交。");
    process.exitCode = 2;
    return;
  }
  if (watchExplicit && !noWait) {
    console.error("[CLI] --watch 已废弃：请直接用 --no-wait（默认即内部自旋）；单次探针用 --no-wait --once。");
    process.exitCode = 2;
    return;
  }

  const promptHashForLog = computePromptHash(prompt);
  // 进程退出时释放提交锁（无论成功/失败/被杀），避免残留锁文件阻塞后续 CLI
  process.on("exit", () => releaseAllSubmitLocks(promptHashForLog));
  const sessionLog = installWindowsSessionLogTee({ promptHash: promptHashForLog });
  if (sessionLog.logPath) {
    console.log(`ALICE_SESSION_LOG=${sessionLog.logPath}`);
    console.log(`ALICE_SESSION_LOG_PROMPT_HASH=${promptHashForLog}`);
    console.error(
      "[CLI] Windows 管道捕获下 live 中文可能乱码；只读 stdout 打印的 ALICE_SESSION_LOG= 路径，" +
        "Get-Content -Encoding UTF8 -Tail 200 -Wait",
    );
    console.error(
      "[CLI] 禁止 view_folder logs/ 或按 12 位前缀猜 session.log——不同 prompt（同公司）文件名不同，误读会得到旧 DONE。",
    );
  }

  const url = getApiUrl();
  const apiKey = getApiKey();
  const headers = buildHeaders(apiKey);

  // --context-id 显式续接：非空时复用该 contextId，且不读不写共享 session 文件（防串号）。
  currentExplicitContextId = explicitContextId || null;

  // --no-wait：默认 CLI 内部自旋直到终态或全程超时（沙箱 / Trae 推荐）。
  // --no-wait --once：单次探针，几秒内返回（脚本 / 调试专用）。
  if (noWait) {
    const promptHash = computePromptHash(prompt);
    const registry = openRegistry();
    let taskId = null;

    // 尽早输出：轮询开始前就列出同主体旧报告路径，防止 Agent「先读 download 再等 DONE」。
    printPromptHashMarker(promptHash);
    printAwaitingResultArtifactGuard({
      prompt,
      promptHash,
      registry,
      downloadDir: resolveDownloadDir(downloadDir),
    });
    console.log("ALICE_AGENT_REDLINE=禁止在 stdout 出现 ALICE_COMPANY_ONE_PAGE_INVESTMENT_MEMO_DONE 之前 view_files/read download/ 主体报告");

    if (once) {
      printPromptHashMarker(promptHash);
      const record = registry.findLatestByPromptHash(promptHash);
      if (!record) {
        console.log("[探针] 本地 tasks.json 找不到该 prompt 的任务记录。");
        console.log("[探针] --no-wait --once 仅探针不提交；请先执行一次完整 --no-wait 或本地无记录时将自动新建。");
        printArtifactGuardHints({
          prompt,
          promptHash,
          registry,
          downloadDir: resolveDownloadDir(downloadDir),
          kind: "probe_no_task",
        });
        publishFinalStatus("no-task");
        process.exitCode = EXIT_PROBE_NO_TASK;
        return;
      }
      taskId = record.taskId;
      printPromptHashMarker(promptHash, taskId);
    } else if (watch) {
      const plan = await resolveTaskDispatchPlan({
        registry,
        promptHash,
        prompt,
        forceNew,
        url,
        headers,
        apiKey,
        downloadDir,
        logPrefix: "[CLI]",
        preferReplayOnCompleted: true,
      });
      const applied = await applyNoWaitDispatchPlan({
        plan,
        registry,
        promptHash,
        prompt,
        url,
        headers,
        apiKey,
        downloadDir,
        forceNew,
        newSession,
        continueSession,
        sessionScope,
        logPrefix: "[CLI]",
      });
      if (applied.done) return;
      taskId = applied.taskId;
    } else {
      printPromptHashMarker(promptHash);
      const record = registry.findLatestByPromptHash(promptHash);
      if (!record) {
        console.log("[探针] 本地 tasks.json 找不到该 prompt 的任务记录。");
        publishFinalStatus("no-task");
        process.exitCode = EXIT_PROBE_NO_TASK;
        return;
      }
      taskId = record.taskId;
      printPromptHashMarker(promptHash, taskId);
    }

    const ctx = { registry, taskId, promptHash, prompt, url, headers, apiKey, downloadDir };
    if (watch) {
      await runWatchMode(ctx, {
        intervalSec: watchIntervalSec,
        timeoutSec: watchTimeoutSec,
        absoluteMaxSec: watchAbsoluteMaxSec,
      });
    } else {
      await runProbeMode(ctx);
    }
    return;
  }

  printCliRunStartNotice();

  const promptHash = computePromptHash(prompt);
  const registry = openRegistry();

  const plan = await resolveTaskDispatchPlan({
    registry,
    promptHash,
    prompt,
    forceNew,
    url,
    headers,
    apiKey,
    downloadDir,
    logPrefix: "[CLI]",
  });

  if (plan.action === "replay_completed") {
    console.log("ALICE_NO_SERVER_CALL=1 reason=replay_completed");
    console.error(
      "[CLI] 本进程未向服务端发请求，直接重放本地 completed 结果；" +
        "serverCallsThisProcess=0。禁止向用户声称「已向服务端新建任务」。",
    );
    console.error(
      "[CLI][replay] 这不是新建分析。如需重新分析同一主体，必须加 --new 参数：" +
        `node scripts/cli.mjs --prompt ${JSON.stringify(prompt)} --new --no-wait`,
    );
    console.error(
      "[CLI][replay] 禁止删除 submit-locks/ 锁文件；禁止反复重发不加 --new 的同条命令。",
    );
    announceServerUsage({
      action: "replay",
      taskId: plan.record?.taskId,
      promptHash,
      registry,
      forceNew,
      recoveredFromOtherProcess: true,
    });
    replayCompletedArtifacts({
      registry,
      taskId: plan.record?.taskId,
      promptHash,
      logPrefix: "[CLI]",
    });
    printCliRunEndNotice({ success: true, exitCode: 0, elapsed: formatElapsed(0) });
    return;
  }
  if (plan.action === "abort_failed") {
    printAbortFailedGuidance(plan.record, "[CLI]");
    process.exitCode = 1;
    return;
  }

  let attachRecord = plan.action === "attach" ? plan.record : null;
  let mode = attachRecord ? "attach" : "new";
  let taskId;
  let contextId;
  let newTaskBody = null;
  let attachStartedAt = null;

  if (mode === "attach") {
    taskId = attachRecord.taskId;
    contextId = attachRecord.contextId;
    attachStartedAt = attachRecord.startedAt;
    announceServerUsage({
      action: "attach",
      taskId,
      promptHash,
      registry,
      forceNew,
    });
    printPromptHashMarker(promptHash, taskId);
  } else {
    if (await enforceDuplicateGuard({
      registry,
      prompt,
      promptHash,
      forceNew,
      url,
      headers,
      apiKey,
    })) {
      return;
    }
    if (enforceSubmitLock({ promptHash, prompt, forceNew })) {
      return;
    }
    // 会话续接：默认工作区自动续接（process.cwd() 隔离防串号）；`--new-session` 强制新会话；
    // 显式 `--context-id` 优先级最高。
    const reuseContextId = currentExplicitContextId
      || resolveSessionContextId({ forceNewSession: newSession, continueSession, sessionScope, workspaceDir: process.cwd() });
    newTaskBody = buildBody(prompt, { reuseContextId });
    taskId = newTaskBody.params.message.taskId;
    contextId = newTaskBody.params.message.contextId;
    if (reuseContextId && reuseContextId === contextId) {
      const scopeSuffix = sessionScope ? `；scope=${sessionScope}` : "";
      console.log(
        `[CLI] 会话续接：复用 contextId = ${contextId}（${currentExplicitContextId ? "--context-id 显式续接" : "工作区自动续接"}${scopeSuffix}）`,
      );
    }
    const savedOk = registerNewTaskRecord({
      registry,
      promptHash,
      prompt,
      taskId,
      contextId,
      downloadDir,
    });
    if (!savedOk) {
      console.error(
        "[CLI] 当前环境无法保存任务状态，已阻止提交分析请求（未消耗积分）。" +
        "请在宿主工具中开启完全访问权限后重试。",
      );
      console.log("ALICE_SANDBOX_NO_PERSIST=1");
      console.log(
        `[CLI] 退出码 ${EXIT_SANDBOX_NO_PERSIST} = 环境受限，任务状态无法保存；` +
        "未向服务端发请求，不扣积分。请在宿主工具中开启完全访问权限后重试。",
      );
      process.exitCode = EXIT_SANDBOX_NO_PERSIST;
      return;
    }
    announceServerUsage({
      action: "submit",
      taskId,
      promptHash,
      registry,
      forceNew,
    });
    printPromptHashMarker(promptHash, taskId);
  }
  currentSessionContextId = contextId;
  // main 直接提交路径同样需要落盘会话，让下次调用能续接。sessionScope 决定落到哪份文件。
  maybeSaveCurrentSession({ contextId, taskId, promptHash, sessionScope });

  // SIGINT / SIGTERM：根据 taskCreatedOnServer 区分两种清理路径，避免"假复用 → 回退新建"白白消耗额度。
  // 具体逻辑见 handleInterruptCleanup 函数注释。
  let interruptShown = false;
  const onInterrupt = (signal) => {
    if (interruptShown) {
      process.exit(130);
      return;
    }
    interruptShown = true;
    stopProgressTicker();
    handleInterruptCleanup({
      signal,
      taskCreatedOnServer,
      registry,
      promptHash,
      taskId,
      contextId,
      registryPath: REGISTRY_PATHS.file,
    });
    process.exit(130);
  };
  process.on("SIGINT", onInterrupt);
  process.on("SIGTERM", onInterrupt);

  // 任务是否已在服务端成功建立（用于决定重试时该用 message/stream 还是 tasks/resubscribe）
  // - attach 模式：registry 里有记录，说明之前一定 200 过，置 true
  // - new 模式：还没发过请求，初始 false；首次 fetch 拿到 200 响应后才置 true
  // 这是为了避免 attempt=0 在网络层就失败（如 ConnectTimeout）的情况下，
  // attempt=1 错误地用 tasks/resubscribe 续订一个服务端从未见过的 taskId，
  // 导致服务端返回 -32001 Task not found。
  let taskCreatedOnServer = mode === "attach";

  // attach 模式失败回退到新建任务用的辅助函数；同一次 CLI 调用内最多回退 1 次
  let attachFallbackUsed = false;
  const switchToNewTaskMode = (reason) => {
    if (reason) console.log(`[任务复用] ${reason}，自动回退到新建任务模式...`);
    registry.removeByTaskId(taskId);
    // fallback 仍属于同一次用户提问，尊重会话续接策略（默认工作区自动续接；
    // `--new-session` 强制新会话），并沿用相同 sessionScope。
    const reuseContextIdFallback = currentExplicitContextId
      || resolveSessionContextId({ forceNewSession: newSession, continueSession, sessionScope, workspaceDir: process.cwd() });
    newTaskBody = buildBody(prompt, { reuseContextId: reuseContextIdFallback });
    taskId = newTaskBody.params.message.taskId;
    contextId = newTaskBody.params.message.contextId;
    currentSessionContextId = contextId;
    maybeSaveCurrentSession({ contextId, taskId, promptHash, sessionScope });
    const savedOk = registerNewTaskRecord({
      registry,
      promptHash,
      prompt,
      taskId,
      contextId,
      downloadDir,
    });
    if (!savedOk) {
      console.error(
        "[CLI] 当前环境无法保存任务状态，已阻止提交分析请求（未消耗积分）。" +
        "请在宿主工具中开启完全访问权限后重试。",
      );
      console.log("ALICE_SANDBOX_NO_PERSIST=1");
      console.log(
        `[CLI] 退出码 ${EXIT_SANDBOX_NO_PERSIST} = 环境受限，任务状态无法保存；` +
        "未向服务端发请求，不扣积分。请在宿主工具中开启完全访问权限后重试。",
      );
      process.exitCode = EXIT_SANDBOX_NO_PERSIST;
      return false;
    }
    mode = "new";
    attachStartedAt = null;
    attachFallbackUsed = true;
    taskCreatedOnServer = false;
    resetSessionState();
    stopProgressTicker();
    startProgressTicker();
    return true;
  };

  const MAX_RETRIES = 10;

  resetSessionState();
  startProgressTicker();
  let startBannerPrinted = false;

  try {
    try {
      mainLoop: while (true) {
        for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
          if (attempt > 0) {
            const delay = Math.min(1000 * attempt, 10000);
            console.error(
              `[reconnect] attempt ${attempt}/${MAX_RETRIES}, waiting ${delay}ms...`,
            );
            await new Promise((r) => setTimeout(r, delay));
          }

          // 构造请求体：
          // - attach 模式：始终用 resubscribe
          // - new 模式：仅当任务已确认在服务端建立（收到过 200 响应）后，重试才用 resubscribe；
          //   否则继续用 message/stream 新建，避免 ConnectTimeout 等"请求未到达服务端"的失败
          //   场景下，重试错误地续订一个服务端从未见过的 taskId 导致 -32001 Task not found。
          let requestBody;
          if (mode === "attach") {
            requestBody = resubscribeBody({ taskId, contextId });
          } else if (taskCreatedOnServer) {
            requestBody = resubscribeBody({ taskId, contextId });
          } else {
            requestBody = newTaskBody;
          }

          let response;
          try {
            response = await fetch(url, {
              method: "POST",
              headers,
              body: JSON.stringify(requestBody),
            });
          } catch (e) {
            console.error(`[network error] ${formatErrorDetail(e)}`);
            if (attempt < MAX_RETRIES) continue;
            console.error("max retries exceeded");
            registry.markFailed(taskId, "network error: max retries exceeded");
            process.exitCode = 1;
            return;
          }

          // 拿到 HTTP 响应（无论 status 多少）就说明请求确实送达了服务端。
          // 但只有 2xx 才意味着服务端真正受理并建立 / 续订了任务；4xx/5xx 不算建立成功。
          if (response.ok) {
            taskCreatedOnServer = true;
          }

          console.log("status:", response.status, response.statusText);
          console.log(
            "headers:",
            Object.fromEntries(response.headers.entries()),
          );

          if (!startBannerPrinted) {
            startBannerPrinted = true;
            if (mode === "attach") {
              printAttachBanner({ taskId, contextId, startedAt: attachStartedAt });
            } else {
              printNewTaskBanner({ taskId, contextId });
            }
            console.log(
              `[开始] 已向 Alice「${ALICE_SKILL_NAME_ZH}」技能发起请求；公司一页纸通常耗时 2-5 分钟，期间会定期播报等待进度，请勿中断。`,
            );
          }

          if (!response.ok) {
            const errorText = await response.text();
            if (handleServerNoticeInErrorBody(errorText, { registry, taskId })) return;
            console.error("request failed:");
            console.error(errorText);
            // attach 模式遇 4xx（典型 404/410）→ 旧任务已失效，回退新建
            if (
              mode === "attach" &&
              !attachFallbackUsed &&
              response.status >= 400 &&
              response.status < 500
            ) {
              switchToNewTaskMode(`服务端返回 ${response.status}，旧任务可能已过期或被清理`);
              if (process.exitCode === EXIT_SANDBOX_NO_PERSIST) return;
              startBannerPrinted = false;
              continue mainLoop;
            }
            if (response.status >= 500 && attempt < MAX_RETRIES) continue;
            registry.markFailed(taskId, `HTTP ${response.status}`);
            process.exitCode = 1;
            return;
          }

          const contentType = (response.headers.get("content-type") || "").toLowerCase();
          const useSseReader =
            contentType.includes("text/event-stream") && response.body != null;

          if (useSseReader) {
            let streamError = null;
            try {
              const drainResult = await drainSseStream(response, {
                attachMode: mode === "attach",
              });

              if (
                !agentResultSeen &&
                !jsonRpcErrorReported &&
                !serverUserNoticeHandled
              ) {
                const { rawText = "", totalEvents = 0, attachTimedOut = false } =
                  drainResult ?? {};

                // attach 模式静默 / 超时：resubscribe 可能不推送历史事件（空流≠任务已死），
                // 先用 tasks/get 确认；仅当服务端确认旧 task 不存在时才回退新建。
                if (mode === "attach" && !attachFallbackUsed) {
                  const recovery = await recoverAttachAfterEmptySse({
                    drainResult,
                    url,
                    headers,
                    apiKey,
                    registry,
                    promptHash,
                    prompt,
                    taskId,
                    contextId,
                    downloadDir,
                  });
                  if (recovery.handled) {
                    return;
                  }
                  if (recovery.shouldFallbackToNew) {
                    switchToNewTaskMode(
                      recovery.fallbackReason ??
                        `服务端无有效响应（${totalEvents} 事件 / ${Buffer.byteLength(rawText, "utf8")} 字节）`,
                    );
                    if (process.exitCode === EXIT_SANDBOX_NO_PERSIST) return;
                    startBannerPrinted = false;
                    continue mainLoop;
                  }
                }

                if (pendingUiStateNotices.length > 0) {
                  const info = classifyServerUserNotice(pendingUiStateNotices);
                  lastServerUserNoticeInfo = info;
                  serverUserNoticeHandled = true;
                  emitServerUserNoticeBanner(info);
                  registry.markFailed(taskId, info.primaryMessage);
                  process.exitCode = info.exitCode;
                  return;
                }

                const { head, totalBytes, truncated } = formatStreamRawSnippet(rawText);
                console.error(
                  "[stream error] SSE 流已结束，但未收到任何最终报告（agentResult）事件；未做自动重试，请检查服务端状态后重试原命令。",
                );
                console.error(
                  `[stream error] 流元信息：解析到 ${totalEvents} 个 SSE 事件，原始字节数=${totalBytes}。`,
                );
                if (totalBytes === 0) {
                  console.error(
                    "[stream error] 服务端没有发送任何字节（响应体为空）。可能原因：账户额度耗尽、服务端瞬时异常、接入层直接关流。",
                  );
                } else {
                  console.error(
                    `[stream error] 服务端原始响应（${truncated ? "已截断前 4KB" : "完整内容"}）：`,
                  );
                  console.error(head);
                }
                registry.markFailed(taskId, "no agentResult");
                process.exitCode = 1;
                return;
              }

              // 走到这里：拿到了 agentResult / ServerUserNotice / jsonrpc error 之一
              if (agentResultSeen) {
                persistAgentResultIfAny({ registry, taskId, promptHash, prompt });
                registry.markCompleted(taskId);
              } else if (serverUserNoticeHandled) {
                registry.markFailed(taskId, getServerNoticeFailReason());
                if (!process.exitCode) process.exitCode = getServerNoticeExitCode();
              } else if (jsonRpcErrorReported) {
                // attach 模式收到 jsonrpc 错误（如 task not found）→ 回退新建
                if (mode === "attach" && !attachFallbackUsed) {
                  switchToNewTaskMode("服务端返回 jsonrpc 错误，旧任务可能已不存在");
                  if (process.exitCode === EXIT_SANDBOX_NO_PERSIST) return;
                  startBannerPrinted = false;
                  continue mainLoop;
                }
                registry.markFailed(taskId, "jsonrpc error");
              }

              await downloadCollectedFiles(apiKey, downloadDir, { registry, taskId });
              return;
            } catch (e) {
              streamError = e;
            }

            console.error(`[stream error] ${formatErrorDetail(streamError)}`);
            if (attempt < MAX_RETRIES) continue;
            console.error("max retries exceeded");
            registry.markFailed(taskId, "stream error: max retries exceeded");
            process.exitCode = 1;
            return;
          }

          let bodyText;
          try {
            bodyText = await response.text();
          } catch (e) {
            console.error(`[read body error] ${formatErrorDetail(e)}`);
            if (attempt < MAX_RETRIES) continue;
            console.error("max retries exceeded");
            registry.markFailed(taskId, "read body error: max retries exceeded");
            process.exitCode = 1;
            return;
          }

          consumeNonStreamBody(bodyText);
          if (agentResultSeen) {
            persistAgentResultIfAny({ registry, taskId, promptHash, prompt });
            registry.markCompleted(taskId);
          } else if (serverUserNoticeHandled) {
            registry.markFailed(taskId, getServerNoticeFailReason());
            if (!process.exitCode) process.exitCode = getServerNoticeExitCode();
          } else if (jsonRpcErrorReported || process.exitCode) {
            registry.markFailed(taskId, "non-stream error");
          }
          await downloadCollectedFiles(apiKey, downloadDir, { registry, taskId });
          return;
        }
        // 内层 for 正常结束（理论上不会到这里，所有出口都是 return 或 continue mainLoop）
        break;
      }
    } catch (e) {
      if (isKnownServerError(e)) {
        registry.markFailed(taskId, e.primaryMessage || getServerNoticeFailReason());
        if (!process.exitCode) process.exitCode = e.exitCode ?? getServerNoticeExitCode();
      } else {
        console.error("request error:");
        console.error(formatErrorDetail(e));
        registry.markFailed(taskId, e?.message || "unknown error");
        if (!process.exitCode) process.exitCode = 1;
      }
    }
  } finally {
    stopProgressTicker();
    if (progressStartTime) {
      const elapsed = formatElapsed(elapsedSinceStart());
      const code = process.exitCode;
      if (code && code !== 0) {
        // 失败行写 stderr，与上方 [服务端提示] / [stream error] / request failed
        // 等错误信息保持同一输出流，避免 stdout/stderr 交错错乱顺序。
        console.error(
          `[失败] 总耗时 ${elapsed}（退出码=${code}），请检查上方错误信息。`,
        );
        printCliRunEndNotice({ success: false, exitCode: code, elapsed });
      } else {
        console.log(`[完成] 总耗时 ${elapsed}。`);
        printCliRunEndNotice({ success: true, exitCode: 0, elapsed });
      }
    }
  }
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(process.argv[1]).href
) {
  main().catch((error) => {
    stopProgressTicker();
    console.error("request error:");
    console.error(formatErrorDetail(error));
    process.exitCode = 1;
  });
}
