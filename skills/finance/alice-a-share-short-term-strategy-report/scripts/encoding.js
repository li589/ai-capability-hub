import { spawnSync } from "node:child_process";
import { appendFileSync, closeSync, existsSync, mkdirSync, openSync, readFileSync, unlinkSync, writeFileSync, writeSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { format } from "node:util";
import { resolveDataDir } from "./dataDir.js";

// 在 Windows 上，Node.js 默认按 UTF-8 把字符串写入 stdout/stderr 字节流。
// 而宿主环境（cmd / PowerShell / 各种沙箱）默认会按系统代码页解码这些字节，
// 中文 Windows 通常是 936 (GBK)，于是中文输出在沙箱里全部变成乱码。
//
// 这里通过两步把"编码 = UTF-8、解码也 = UTF-8"对齐：
//   1) 调用 `chcp 65001` 把当前控制台代码页切换为 UTF-8；
//      子进程通过 stdio: ['inherit', 'ignore', 'ignore'] 共享父进程的 console
//      句柄，从而真正修改父级 cmd / PowerShell 的输出代码页，且不会让
//      `Active code page: 65001` 这一行污染我们的 stdout。
//   2) 显式声明 process.stdout / process.stderr 的默认写入编码为 UTF-8，
//      作为兜底；某些极端环境下默认编码可能不是 UTF-8。
//
// 非 TTY（Trae run_command 管道捕获）时 chcp 无效，额外把 stdout/stderr
// tee 到带 BOM 的会话日志，Agent 可读 ALICE_SESSION_LOG= 路径避免乱码。
//
// 仅在 Windows 上执行，其它平台直接返回。任何步骤失败都吞掉异常，
// 因为编码修复只是"更好显示"的辅助，不应影响主流程。

/** UTF-8 BOM：让 PowerShell Get-Content 默认识别为 UTF-8，避免按 GBK 解码乱码 */
export const UTF8_BOM = Buffer.from([0xef, 0xbb, 0xbf]);

/**
 * 向已打开的日志 fd 写入 UTF-8 BOM（detach / 会话日志专用）。
 * 日志文件本身是 UTF-8 无 BOM 时，PowerShell 5.x 默认按系统 ANSI(GBK) 读会乱码。
 */
export function writeUtf8BomToFd(fd) {
  if (typeof fd !== "number" || fd < 0) return;
  try {
    writeSync(fd, UTF8_BOM);
  } catch {}
}

export function ensureWindowsUtf8Stdio() {
  if (process.platform !== "win32") return;

  try {
    spawnSync("chcp", ["65001"], {
      stdio: ["inherit", "ignore", "ignore"],
      shell: true,
      windowsHide: true,
    });
  } catch {}

  try {
    process.stdout.setDefaultEncoding?.("utf8");
  } catch {}
  try {
    process.stderr.setDefaultEncoding?.("utf8");
  } catch {}
}

/** session.log 主路径和回退路径。主路径走 resolveDataDir("logs")，固定在 ~/.wind-alice/logs/（跨会话稳定）；不可写时回退到临时目录。 */
const SESSION_LOG_DIR_PRIMARY = resolveDataDir("logs");
const SESSION_LOG_DIR_FALLBACK = join(tmpdir(), "alice-session-logs");

/** 缓存已确认可写的 session.log 目录。 */
let _writableSessionLogDir = null;

/**
 * 确定可写的 session.log 目录：优先主路径，不可写时回退到临时目录。
 */
function resolveWritableSessionLogDir() {
  if (_writableSessionLogDir) return _writableSessionLogDir;
  for (const dir of [SESSION_LOG_DIR_PRIMARY, SESSION_LOG_DIR_FALLBACK]) {
    try {
      mkdirSync(dir, { recursive: true });
      const testFile = join(dir, ".write-test");
      writeFileSync(testFile, "1", "utf8");
      unlinkSync(testFile);
      _writableSessionLogDir = dir;
      return dir;
    } catch {
      continue;
    }
  }
  return null;
}

/**
 * 查找给定 promptHash 对应的 session.log 文件路径。
 * 优先返回主路径（即使文件不存在——让调用方 existsSync 判断），
 * 回退路径也检查是否存在旧文件（上次在沙箱环境下可能写到了临时目录）。
 */
export function sessionLogPathForPrompt(promptHash) {
  // 主路径（即使不可写，旧文件可能在那里）
  const primaryPath = join(SESSION_LOG_DIR_PRIMARY, `${promptHash}.session.log`);
  if (existsSync(primaryPath)) return primaryPath;

  // 回退路径
  const fallbackPath = join(SESSION_LOG_DIR_FALLBACK, `${promptHash}.session.log`);
  if (existsSync(fallbackPath)) return fallbackPath;

  // 都不存在：返回可写目录下的路径（新文件将写到这里）
  const writableDir = resolveWritableSessionLogDir();
  if (writableDir) return join(writableDir, `${promptHash}.session.log`);

  // 全部不可用：返回主路径作为默认
  return primaryPath;
}

/**
 * 上一次 installWindowsSessionLogTee 覆盖 session.log 前读到的旧内容。
 * 供 tryRecoverFromSessionLog 在 session.log 已被覆盖后仍能恢复旧任务信息。
 * key = promptHash, value = 旧文件内容字符串。
 */
const preTeeSessionLogCache = new Map();

/** 获取 installWindowsSessionLogTee 覆盖前缓存的旧 session.log 内容。 */
export function getPreTeeSessionLogContent(promptHash) {
  return preTeeSessionLogCache.get(promptHash) ?? null;
}

/**
 * Windows 非 TTY 场景（Trae / IDE 管道捕获 stdout）下，live 中文常按 GBK 误解码。
 * 将 console 输出同步 tee 到 ~/.wind-alice/logs/<promptHash>.session.log（UTF-8 BOM）。
 *
 * 覆盖前会把旧 session.log 内容缓存到 preTeeSessionLogCache，
 * 供 tryRecoverFromSessionLog 在 session.log 被覆盖后仍能恢复旧任务信息。
 *
 * @param {{ promptHash: string, skip?: boolean }} opts
 * @returns {{ logPath: string | null, uninstall: () => void }}
 */
export function installWindowsSessionLogTee({ promptHash, skip = false }) {
  const noop = { logPath: null, uninstall: () => {} };
  if (process.platform !== "win32" || skip) return noop;
  if (process.stdout.isTTY) return noop;
  if (process.env.ALICE_DETACH_LOG) return noop;
  if (!promptHash || typeof promptHash !== "string") return noop;

  // 确定可写的日志目录（优先主路径，回退到临时目录）
  const logDir = resolveWritableSessionLogDir();
  if (!logDir) return noop;

  const logPath = join(logDir, `${promptHash}.session.log`);

  // 覆盖前缓存旧内容，供 tryRecoverFromSessionLog 恢复用
  try {
    if (existsSync(logPath)) {
      const oldContent = readFileSync(logPath, "utf8");
      if (oldContent && oldContent.trim()) {
        preTeeSessionLogCache.set(promptHash, oldContent);
      }
    }
  } catch {}

  let fd;
  try {
    mkdirSync(logDir, { recursive: true });
    fd = openSync(logPath, "w");
    writeUtf8BomToFd(fd);
    const boundary = [
      `ALICE_SESSION_LOG_BOUNDARY promptHash=${promptHash}`,
      `ALICE_SESSION_LOG=${logPath}`,
      "[CLI] 只读本文件；禁止 view_folder / 按 mtime 扫描 logs/ 挑其它 .session.log。",
      "[CLI] 其它 prompt（哪怕同一公司）会落在不同文件名；其中的 DONE 行对本次无效。",
      "",
    ].join("\n");
    writeSync(fd, boundary, "utf8");
  } catch {
    return noop;
  }

  const append = (args) => {
    try {
      appendFileSync(fd, `${format(...args)}\n`, "utf8");
    } catch {}
  };

  const origLog = console.log.bind(console);
  const origErr = console.error.bind(console);
  console.log = (...args) => {
    append(args);
    origLog(...args);
  };
  console.error = (...args) => {
    append(args);
    origErr(...args);
  };

  return {
    logPath,
    uninstall: () => {
      console.log = origLog;
      console.error = origErr;
      try {
        closeSync(fd);
      } catch {}
    },
  };
}

/** 将文本转为带 UTF-8 BOM 的 Buffer（供 writeFileSync 等使用）。 */
export function utf8BufferWithBom(content) {
  return Buffer.concat([UTF8_BOM, Buffer.from(String(content ?? ""), "utf8")]);
}

/** 写入 UTF-8 文本文件并在开头加 BOM（便于 Windows PowerShell 正确读取 .md）。 */
export function writeUtf8FileWithBom(path, content) {
  let fd;
  try {
    fd = openSync(path, "w");
    writeSync(fd, utf8BufferWithBom(content));
  } finally {
    if (fd !== undefined) {
      try {
        closeSync(fd);
      } catch {}
    }
  }
}
