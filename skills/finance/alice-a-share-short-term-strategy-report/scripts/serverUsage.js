import { existsSync, mkdirSync, readFileSync, renameSync, unlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { resolveDataDir } from "./dataDir.js";

const WATCHERS_DIR = resolveDataDir("watchers");
const WATCHER_TTL_MS = 2 * 60 * 60 * 1000;

/** @typedef {"submit"|"attach"|"replay"|"reuse_peer_finalize"|"probe_only"} ServerUsageAction */

let session = {
  action: /** @type {ServerUsageAction|null} */ (null),
  taskId: null,
  promptHash: null,
  serverCallsThisProcess: 0,
  reusedPeerFinalize: false,
  forceNew: false,
  recoveredFromOtherProcess: false,
};

const registeredWatcherTaskIds = new Set();
let exitHookInstalled = false;

function isProcessAlive(pid) {
  if (!Number.isInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

function watcherFilePath(taskId) {
  const safe = String(taskId ?? "")
    .replace(/[^a-zA-Z0-9._-]+/g, "_")
    .slice(0, 120);
  return join(WATCHERS_DIR, `${safe}.json`);
}

function readWatcherFile(taskId) {
  const path = watcherFilePath(taskId);
  if (!existsSync(path)) return [];
  try {
    const data = JSON.parse(readFileSync(path, "utf8"));
    return Array.isArray(data?.watchers) ? data.watchers : [];
  } catch {
    return [];
  }
}

function writeWatcherFile(taskId, watchers) {
  mkdirSync(WATCHERS_DIR, { recursive: true });
  const path = watcherFilePath(taskId);
  const tmp = `${path}.tmp`;
  writeFileSync(tmp, JSON.stringify({ watchers, updatedAt: Date.now() }, null, 2), "utf8");
  renameSync(tmp, path);
}

function pruneWatchers(watchers, now = Date.now()) {
  return watchers.filter(
    (w) =>
      w &&
      typeof w.pid === "number" &&
      typeof w.startedAt === "number" &&
      now - w.startedAt < WATCHER_TTL_MS &&
      isProcessAlive(w.pid),
  );
}

/** 登记本 CLI 进程正在等待同一 taskId（用于统计并行 Agent 数）。 */
export function registerCliWatcher(taskId) {
  if (!taskId) return 0;
  installWatcherExitHook();
  const now = Date.now();
  const watchers = pruneWatchers(readWatcherFile(taskId), now);
  if (!watchers.some((w) => w.pid === process.pid)) {
    watchers.push({ pid: process.pid, startedAt: now });
  }
  writeWatcherFile(taskId, watchers);
  registeredWatcherTaskIds.add(taskId);
  return watchers.length;
}

export function unregisterCliWatcher(taskId) {
  if (!taskId) return;
  const watchers = pruneWatchers(readWatcherFile(taskId)).filter((w) => w.pid !== process.pid);
  const path = watcherFilePath(taskId);
  if (watchers.length === 0) {
    try {
      unlinkSync(path);
    } catch {}
  } else {
    writeWatcherFile(taskId, watchers);
  }
  registeredWatcherTaskIds.delete(taskId);
}

export function countCliWatchers(taskId) {
  if (!taskId) return 0;
  return pruneWatchers(readWatcherFile(taskId)).length;
}

function installWatcherExitHook() {
  if (exitHookInstalled) return;
  exitHookInstalled = true;
  const cleanup = () => {
    for (const taskId of [...registeredWatcherTaskIds]) {
      unregisterCliWatcher(taskId);
    }
  };
  process.once("exit", cleanup);
  process.once("SIGINT", cleanup);
  process.once("SIGTERM", cleanup);
}

/** 同 promptHash 下 status=running 的去重 taskId 数量（--new 并行时可能 >1）。 */
export function countRunningServerTasksForPrompt(registry, promptHash) {
  if (!registry || !promptHash) return 0;
  const ids = new Set();
  for (const r of registry.records ?? []) {
    if (r?.promptHash === promptHash && r.status === "running" && r.taskId) {
      ids.add(r.taskId);
    }
  }
  return ids.size;
}

/**
 * 记录本进程的服务端调用方式，并打印机器可读的 ALICE_SERVER_USAGE 标记。
 * @param {object} opts
 * @param {ServerUsageAction} opts.action
 * @param {string} [opts.taskId]
 * @param {string} [opts.promptHash]
 * @param {import("./tasksRegistry.js").TasksRegistry} [opts.registry]
 * @param {boolean} [opts.forceNew]
 * @param {boolean} [opts.reusedPeerFinalize]
 * @param {boolean} [opts.recoveredFromOtherProcess] 任务由其它进程提交并完成（如 --detach），本进程只是读取已有结果
 */
export function announceServerUsage({
  action,
  taskId = null,
  promptHash = null,
  registry = null,
  forceNew = false,
  reusedPeerFinalize = false,
  recoveredFromOtherProcess = false,
}) {
  session = {
    action,
    taskId,
    promptHash,
    serverCallsThisProcess: action === "submit" ? 1 : 0,
    reusedPeerFinalize: Boolean(reusedPeerFinalize),
    forceNew: Boolean(forceNew),
    recoveredFromOtherProcess: Boolean(recoveredFromOtherProcess),
  };

  const parallelRunning = registry && promptHash
    ? countRunningServerTasksForPrompt(registry, promptHash)
    : taskId ? 1 : 0;
  const cliPeers = taskId ? registerCliWatcher(taskId) : 0;

  const lines = [
    `ALICE_SERVER_USAGE action=${action} serverCallsThisProcess=${session.serverCallsThisProcess}`,
  ];
  if (taskId) lines.push(`ALICE_SERVER_USAGE taskId=${taskId}`);
  if (promptHash) lines.push(`ALICE_SERVER_USAGE promptHash=${promptHash}`);
  if (cliPeers > 0) lines.push(`ALICE_SERVER_USAGE concurrentCliPeers=${cliPeers}`);
  if (parallelRunning > 0) {
    lines.push(`ALICE_SERVER_USAGE parallelRunningServerTasks=${parallelRunning}`);
  }
  if (reusedPeerFinalize) {
    lines.push("ALICE_SERVER_USAGE reusedPeerFinalize=true");
  }

  for (const line of lines) {
    console.log(line);
  }
}

/** 续接过程中由其它 CLI 先完成落盘时追加机器可读标记。 */
export function notePeerFinalize({ taskId = null } = {}) {
  session.reusedPeerFinalize = true;
  if (taskId) session.taskId = taskId;
  console.log("ALICE_SERVER_USAGE reusedPeerFinalize=true");
}

/** 任务完成时输出机器可读摘要。 */
export function printServerUsageSummary() {
  if (!session.action) return;
  const cliPeers = session.taskId ? countCliWatchers(session.taskId) : 0;
  const parts = [
    "ALICE_SERVER_USAGE_SUMMARY",
    `action=${session.action}`,
    `serverCallsThisProcess=${session.serverCallsThisProcess}`,
  ];
  if (session.taskId) parts.push(`taskId=${session.taskId}`);
  if (cliPeers > 0) parts.push(`concurrentCliPeers=${cliPeers}`);
  console.log(parts.join(" "));
}

/** @internal */
export function __getServerUsageSessionForTesting() {
  return { ...session };
}

/** @internal */
export function __resetServerUsageSessionForTesting() {
  session = {
    action: null,
    taskId: null,
    promptHash: null,
    serverCallsThisProcess: 0,
    reusedPeerFinalize: false,
    forceNew: false,
    recoveredFromOtherProcess: false,
  };
  for (const taskId of [...registeredWatcherTaskIds]) {
    unregisterCliWatcher(taskId);
  }
}
