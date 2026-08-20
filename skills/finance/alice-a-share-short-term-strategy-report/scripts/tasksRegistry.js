import {
  existsSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  renameSync,
  statSync,
  unlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { utf8BufferWithBom } from "./encoding.js";
import { resolveDataDir } from "./dataDir.js";

// 数据目录走 resolveDataDir()，固定在 ~/.wind-alice/（跨会话稳定，与 API Key 同目录）；
// 可用 ALICE_DATA_DIR 环境变量覆盖（测试用）。详见 dataDir.js。
const REGISTRY_DIR = resolveDataDir();
const REGISTRY_FILE = join(REGISTRY_DIR, "tasks.json");
const REGISTRY_TMP = join(REGISTRY_DIR, "tasks.json.tmp");

/** 单测可设 ALICE_REGISTRY_FILE 指向临时 tasks.json，模拟跨进程 reload。 */
function registryFilePath() {
  const override = process.env.ALICE_REGISTRY_FILE;
  return override && String(override).trim() ? String(override).trim() : REGISTRY_FILE;
}

function registryTmpPath() {
  return `${registryFilePath()}.tmp`;
}
const RESULTS_DIR = join(REGISTRY_DIR, "results");
const LOGS_DIR = join(REGISTRY_DIR, "logs");
const LOCKS_DIR = join(REGISTRY_DIR, "locks");
const SUBMIT_LOCKS_DIR_PRIMARY = join(REGISTRY_DIR, "submit-locks");
const SUBMIT_LOCKS_DIR_FALLBACK = join(tmpdir(), "alice-submit-locks");
const WATCHERS_DIR = join(REGISTRY_DIR, "watchers");
const REGISTRY_VERSION = 1;

// TTL（毫秒）：按状态分别衰减
const TTL_RUNNING = 6 * 60 * 60 * 1000;
const TTL_COMPLETED = 6 * 60 * 60 * 1000;
const TTL_FAILED = 3 * 24 * 60 * 60 * 1000;

const MAX_RECORDS = 200;
const TRIM_TO = 100;

const VALID_STATUSES = new Set(["running", "completed", "failed"]);

function isValidRecord(r) {
  return (
    r &&
    typeof r === "object" &&
    typeof r.promptHash === "string" && r.promptHash.length > 0 &&
    typeof r.taskId === "string" && r.taskId.length > 0 &&
    typeof r.contextId === "string" && r.contextId.length > 0 &&
    VALID_STATUSES.has(r.status) &&
    typeof r.startedAt === "number" && Number.isFinite(r.startedAt)
  );
}

function pruneExpired(records, now = Date.now()) {
  return records.filter((r) => {
    if (!isValidRecord(r)) return false;
    if (r.status === "running") {
      return now - r.startedAt < TTL_RUNNING;
    }
    if (r.status === "completed") {
      const ref = typeof r.completedAt === "number" ? r.completedAt : r.startedAt;
      return now - ref < TTL_COMPLETED;
    }
    if (r.status === "failed") {
      const ref = typeof r.completedAt === "number" ? r.completedAt : r.startedAt;
      return now - ref < TTL_FAILED;
    }
    return false;
  });
}

function trimRecords(records) {
  if (records.length <= MAX_RECORDS) return records;
  const sorted = [...records].sort(
    (a, b) => (a.startedAt ?? 0) - (b.startedAt ?? 0),
  );
  return sorted.slice(-TRIM_TO);
}

function pruneStaleFilesInDir(dir, maxAgeMs, now) {
  if (!dir || !existsSync(dir)) return;
  let names;
  try {
    names = readdirSync(dir);
  } catch {
    return;
  }
  for (const name of names) {
    const filePath = join(dir, name);
    try {
      const st = statSync(filePath);
      if (!st.isFile()) continue;
      if (now - st.mtimeMs >= maxAgeMs) {
        try {
          unlinkSync(filePath);
        } catch {
          // EBUSY / EPERM：文件被其它进程占用，忽略即可，下次再清理
        }
      }
    } catch {
      // 静默：清理失败不影响主流程
    }
  }
}

/**
 * 静默删除 logs/、results/、locks/、submit-locks/、watchers/ 下超过 maxAgeMs 的历史文件（默认 6 小时）。
 * submit-locks 同时清理主目录与临时目录回退路径。
 * 由 openRegistry() 在每次任务相关 CLI 调用时触发，不向用户输出任何提示。
 * 文件被其它进程占用时（EBUSY / EPERM）静默跳过，下次再清理。
 */
export function pruneStaleArtifactFiles({
  now = Date.now(),
  maxAgeMs = TTL_COMPLETED,
  logsDir = LOGS_DIR,
  resultsDir = RESULTS_DIR,
  locksDir = LOCKS_DIR,
  submitLocksDirPrimary = SUBMIT_LOCKS_DIR_PRIMARY,
  submitLocksDirFallback = SUBMIT_LOCKS_DIR_FALLBACK,
  watchersDir = WATCHERS_DIR,
} = {}) {
  pruneStaleFilesInDir(logsDir, maxAgeMs, now);
  pruneStaleFilesInDir(resultsDir, maxAgeMs, now);
  pruneStaleFilesInDir(locksDir, maxAgeMs, now);
  pruneStaleFilesInDir(submitLocksDirPrimary, maxAgeMs, now);
  pruneStaleFilesInDir(submitLocksDirFallback, maxAgeMs, now);
  pruneStaleFilesInDir(watchersDir, maxAgeMs, now);
}

function readRaw() {
  try {
    const file = registryFilePath();
    if (!existsSync(file)) return null;
    const text = readFileSync(file, "utf8");
    return JSON.parse(text);
  } catch {
    return null;
  }
}

function writeRaw(data) {
  try {
    const file = registryFilePath();
    const tmp = registryTmpPath();
    mkdirSync(REGISTRY_DIR, { recursive: true });
    writeFileSync(tmp, JSON.stringify(data, null, 2), "utf8");
    renameSync(tmp, file);
    return true;
  } catch {
    try {
      const tmp = registryTmpPath();
      if (existsSync(tmp)) unlinkSync(tmp);
    } catch {}
    return false;
  }
}

function sortByStartedAtDesc(records) {
  return [...records].sort((a, b) => (b.startedAt ?? 0) - (a.startedAt ?? 0));
}

export class TasksRegistry {
  constructor(records) {
    this.records = Array.isArray(records) ? records : [];
  }

  findByTaskId(taskId) {
    if (!taskId) return null;
    return this.records.find((r) => r.taskId === taskId) ?? null;
  }

  findAllByPromptHash(promptHash) {
    if (!promptHash) return [];
    return sortByStartedAtDesc(this.records.filter((r) => r.promptHash === promptHash));
  }

  findLatestByPromptHash(promptHash) {
    const all = this.findAllByPromptHash(promptHash);
    return all[0] ?? null;
  }

  /**
   * 兼容查询：优先按 taskId 精确匹配，否则返回该 prompt 最新一条记录。
   */
  find(id) {
    if (!id) return null;
    return this.findByTaskId(id) ?? this.findLatestByPromptHash(id);
  }

  upsert(record) {
    if (!record || typeof record.taskId !== "string" || !record.taskId) return false;
    const idx = this.records.findIndex((r) => r.taskId === record.taskId);
    if (idx >= 0) {
      this.records[idx] = { ...this.records[idx], ...record };
    } else {
      this.records.push({ ...record });
    }
    return this.save();
  }

  /** 删除同一 promptHash 下的全部本地记录（--new 等场景）。 */
  remove(promptHash) {
    const before = this.records.length;
    this.records = this.records.filter((r) => r.promptHash !== promptHash);
    if (this.records.length !== before) this.save();
  }

  removeByTaskId(taskId) {
    const before = this.records.length;
    this.records = this.records.filter((r) => r.taskId !== taskId);
    if (this.records.length !== before) this.save();
  }

  markCompleted(taskId, now = Date.now()) {
    const r = this.findByTaskId(taskId);
    if (!r) return;
    r.status = "completed";
    r.completedAt = now;
    r.lastSeenAt = now;
    this.save();
  }

  markFailed(taskId, reason, now = Date.now()) {
    const r = this.findByTaskId(taskId);
    if (!r) return;
    r.status = "failed";
    r.completedAt = now;
    r.lastSeenAt = now;
    if (reason) r.failReason = String(reason).slice(0, 500);
    this.save();
  }

  touch(taskId, now = Date.now()) {
    const r = this.findByTaskId(taskId);
    if (!r) return;
    r.lastSeenAt = now;
    this.save();
  }

  appendDownloadedFile(taskId, entry, now = Date.now()) {
    const r = this.findByTaskId(taskId);
    if (!r) return [];
    if (!entry || typeof entry !== "object") return r.downloadedFiles ?? [];
    const { url, path } = entry;
    if (typeof url !== "string" || !url || typeof path !== "string" || !path) {
      return r.downloadedFiles ?? [];
    }

    if (!Array.isArray(r.downloadedFiles)) r.downloadedFiles = [];
    const idx = r.downloadedFiles.findIndex((e) => e?.url === url);
    const record = {
      url,
      path,
      filename: typeof entry.filename === "string" ? entry.filename : undefined,
      downloadedAt:
        typeof entry.downloadedAt === "number" && Number.isFinite(entry.downloadedAt)
          ? entry.downloadedAt
          : now,
    };
    if (idx >= 0) {
      r.downloadedFiles[idx] = { ...r.downloadedFiles[idx], ...record };
    } else {
      r.downloadedFiles.push(record);
    }
    this.save();
    return r.downloadedFiles;
  }

  getDownloadedFiles(taskId) {
    const r = this.findByTaskId(taskId);
    if (!r || !Array.isArray(r.downloadedFiles)) return [];
    return r.downloadedFiles.map((e) => ({ ...e }));
  }

  reload(taskId) {
    const raw = readRaw();
    if (!raw || !Array.isArray(raw.tasks)) return this;

    if (taskId) {
      const diskRecord = raw.tasks.find((r) => r.taskId === taskId);
      const memRecord = this.findByTaskId(taskId);
      if (!diskRecord || !memRecord) return this;

      if (Array.isArray(diskRecord.downloadedFiles) && diskRecord.downloadedFiles.length > 0) {
        const merged = new Map();
        for (const e of memRecord.downloadedFiles ?? []) {
          if (e?.url) merged.set(e.url, { ...e });
        }
        for (const e of diskRecord.downloadedFiles) {
          if (e?.url) merged.set(e.url, { ...merged.get(e.url), ...e });
        }
        memRecord.downloadedFiles = Array.from(merged.values());
      }
      if (diskRecord.status === "completed" && memRecord.status !== "completed") {
        memRecord.status = "completed";
        if (typeof diskRecord.completedAt === "number") {
          memRecord.completedAt = diskRecord.completedAt;
        }
      }
      return this;
    }

    this.records = raw.tasks;
    return this;
  }

  save() {
    return writeRaw({ version: REGISTRY_VERSION, tasks: this.records });
  }
}

export function openRegistry() {
  pruneStaleArtifactFiles();
  const raw = readRaw();
  const tasks = Array.isArray(raw?.tasks) ? raw.tasks : [];
  const pruned = trimRecords(pruneExpired(tasks));
  const registry = new TasksRegistry(pruned);
  if (pruned.length !== tasks.length) registry.save();
  return registry;
}

/**
 * 把本次任务的 Alice `agentResult.value` 写到 ~/.wind-alice/results/<taskId>.md。
 */
export function saveResultFile(taskId, content) {
  if (!taskId || typeof content !== "string" || !content.trim()) return null;
  try {
    mkdirSync(RESULTS_DIR, { recursive: true });
    const target = join(RESULTS_DIR, `${taskId}.md`);
    const tmp = `${target}.tmp`;
    writeFileSync(tmp, utf8BufferWithBom(content));
    renameSync(tmp, target);
    return target;
  } catch {
    return null;
  }
}

export const REGISTRY_PATHS = Object.freeze({
  dir: REGISTRY_DIR,
  file: REGISTRY_FILE,
  resultsDir: RESULTS_DIR,
  logsDir: LOGS_DIR,
});

export const REGISTRY_TTL = Object.freeze({
  running: TTL_RUNNING,
  completed: TTL_COMPLETED,
  failed: TTL_FAILED,
});
