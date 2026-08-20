import { createHash } from "node:crypto";
import { closeSync, existsSync, mkdirSync, openSync, unlinkSync } from "node:fs";
import { join } from "node:path";
import { resolveDataDir } from "./dataDir.js";

// 与 tasksRegistry 的 LOCKS_DIR 对齐：走 resolveDataDir("locks")，固定落 ~/.wind-alice/locks
const LOCK_DIR = resolveDataDir("locks");
const LOCK_POLL_MS = 200;
const LOCK_MAX_WAIT_MS = 120_000;

function lockFilePath(taskId, url) {
  const h = createHash("sha256").update(`${taskId}\0${url}`, "utf8").digest("hex").slice(0, 20);
  return join(LOCK_DIR, `${h}.lock`);
}

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 跨进程互斥：同一 taskId + URL 只允许一个进程执行 HTTP 下载。
 * @returns {{ acquired: boolean, path: string, fd?: number, error?: unknown }}
 */
export function tryAcquireDownloadLock(taskId, url) {
  mkdirSync(LOCK_DIR, { recursive: true });
  const path = lockFilePath(taskId, url);
  try {
    const fd = openSync(path, "wx");
    return { acquired: true, path, fd };
  } catch (e) {
    if (e?.code === "EEXIST") return { acquired: false, path };
    return { acquired: false, path, error: e };
  }
}

export function releaseDownloadLock(handle) {
  if (!handle?.path) return;
  try {
    if (typeof handle.fd === "number" && handle.fd >= 0) closeSync(handle.fd);
  } catch {}
  try {
    unlinkSync(handle.path);
  } catch {}
}

/** registry 中该 taskId 的 URL 是否已有本地文件可复用（会先 reload 磁盘）。 */
export function findReusableDownload(registry, taskId, url) {
  if (!registry || !taskId || !url) return null;
  registry.reload?.(taskId);
  const entry = registry.getDownloadedFiles(taskId).find((e) => e?.url === url);
  if (entry?.path && existsSync(entry.path)) return { ...entry };
  return null;
}

export async function waitForReusableDownload(
  registry,
  taskId,
  url,
  { maxWaitMs = LOCK_MAX_WAIT_MS } = {},
) {
  const deadline = Date.now() + maxWaitMs;
  while (Date.now() < deadline) {
    const found = findReusableDownload(registry, taskId, url);
    if (found) return found;
    await sleep(LOCK_POLL_MS);
  }
  return null;
}

/**
 * 在下载锁保护下执行 fn；若其它进程已落盘则直接复用。
 * @param {() => Promise<{ ok: boolean, path?: string, error?: string }>} fn
 * @returns {Promise<{ kind: "reused", entry: object } | { kind: "downloaded", result: object } | { kind: "failed", result: object }>}
 */
export async function runDownloadWithLock(registry, taskId, url, fn) {
  if (!taskId || !url) {
    const result = await fn();
    return result?.ok
      ? { kind: "downloaded", result }
      : { kind: "failed", result };
  }

  let pre = findReusableDownload(registry, taskId, url);
  if (pre) return { kind: "reused", entry: pre };

  let lock = tryAcquireDownloadLock(taskId, url);
  if (!lock.acquired) {
    pre = await waitForReusableDownload(registry, taskId, url);
    if (pre) return { kind: "reused", entry: pre, waited: true };

    lock = tryAcquireDownloadLock(taskId, url);
    if (!lock.acquired) {
      pre = await waitForReusableDownload(registry, taskId, url, { maxWaitMs: 5_000 });
      if (pre) return { kind: "reused", entry: pre, waited: true };
    }
  }

  if (!lock.acquired) {
    pre = await waitForReusableDownload(registry, taskId, url, { maxWaitMs: LOCK_MAX_WAIT_MS });
    if (pre) return { kind: "reused", entry: pre, waited: true };
    return {
      kind: "failed",
      result: {
        ok: false,
        error:
          "下载锁竞争超时：其它 CLI 进程正在落盘同一附件；请阻塞等待其 DONE 或执行 status，禁止连发多条 CLI",
      },
      lockContention: true,
    };
  }

  try {
    pre = findReusableDownload(registry, taskId, url);
    if (pre) return { kind: "reused", entry: pre, lockHeld: true };

    const result = await fn();
    return result?.ok
      ? { kind: "downloaded", result, lockHeld: true }
      : { kind: "failed", result, lockHeld: true };
  } finally {
    releaseDownloadLock(lock);
  }
}
