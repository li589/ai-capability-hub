// 防止 Agent 在 CLI 未完成时按 download/ mtime 或 (1)/(2) 后缀误读其它任务报告。
// 纯函数模块，便于单测；request.js 的 status / no-task 探针路径调用。

import { existsSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { compareNormalizedPrompts, comparePromptsForReplay, normalizePromptForGuard } from "./duplicateGuard.js";

/** 过短的通用词，不作为 download/ 文件名匹配 hint。 */
const GENERIC_HINTS = new Set([
  "分析",
  "报告",
  "市场",
  "数据",
  "短线",
  "策略",
  "涨停",
  "收盘",
  "复盘",
  "主线",
  "热点",
  "板块",
  "轮动",
  "生成",
  "查看",
  "今日",
  "今天",
  "最近",
  "最新",
  "帮我",
  "给我",
  "一份",
  "A股",
  "A股短线策略报告",
  "短线策略报告",
  "涨停板分析",
  "涨停板复盘",
]);

/**
 * 从 prompt 提取可用于匹配 download/ 文件名的检索 hint。
 * 优先：证券代码 → 较长中文片段 → 4 字子串。
 */
export function extractSubjectHints(prompt) {
  const normalized = normalizePromptForGuard(prompt);
  const hints = new Set();

  for (const m of normalized.matchAll(/\d{6}(?:\.(?:SZ|SH|BJ))?/gi)) {
    const raw = m[0].toUpperCase();
    hints.add(raw);
    hints.add(raw.slice(0, 6));
  }

  const ymd = normalized.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (ymd) {
    const y = ymd[1];
    const mo = ymd[2].padStart(2, "0");
    const d = ymd[3].padStart(2, "0");
    hints.add(`${y}${mo}${d}`);
    hints.add(`${y}年${Number(ymd[2])}月${Number(ymd[3])}日`);
    hints.add(`${Number(ymd[2])}月${Number(ymd[3])}日`);
  }

  for (const m of normalized.matchAll(/[\u4e00-\u9fff]{3,16}/g)) {
    const seg = m[0];
    if (GENERIC_HINTS.has(seg)) continue;
    hints.add(seg);
    if (seg.length >= 5) {
      for (let i = 0; i <= seg.length - 4; i++) {
        const sub = seg.slice(i, i + 4);
        if (!GENERIC_HINTS.has(sub)) hints.add(sub);
      }
    }
  }

  return [...hints]
    .filter((h) => h.length >= 2)
    .sort((a, b) => b.length - a.length);
}

/** @param {import("./tasksRegistry.js").TasksRegistry | { records?: object[] }} registry */
export function collectRegisteredDownloadPaths(registry) {
  const paths = new Set();
  for (const r of registry?.records ?? []) {
    for (const df of r?.downloadedFiles ?? []) {
      if (typeof df?.path === "string" && df.path) paths.add(df.path);
    }
  }
  return paths;
}

function filenameMatchesHint(filename, hint) {
  if (!filename || !hint) return false;
  if (filename.includes(hint)) return true;
  const code = hint.replace(/\.(SZ|SH|BJ)$/i, "");
  if (/^\d{6}$/.test(code) && filename.includes(code)) return true;
  return false;
}

/**
 * download/ 中与 prompt 主体相关、但未在 tasks.json 登记的 .md 文件。
 *
 * @returns {Array<{ path: string, filename: string, mtimeMs: number, matchedHint: string }>}
 */
export function findOrphanDownloadCandidates({
  prompt,
  registry,
  downloadDir,
  limit = 5,
}) {
  const hints = extractSubjectHints(prompt);
  if (hints.length === 0 || !downloadDir) return [];

  const registered = collectRegisteredDownloadPaths(registry);
  let names = [];
  try {
    if (!existsSync(downloadDir)) return [];
    names = readdirSync(downloadDir);
  } catch {
    return [];
  }

  const candidates = [];
  for (const name of names) {
    if (!/\.md$/i.test(name)) continue;
    const absPath = join(downloadDir, name);
    if (registered.has(absPath)) continue;
    const matchedHint = hints.find((h) => filenameMatchesHint(name, h));
    if (!matchedHint) continue;
    let mtimeMs = 0;
    try {
      mtimeMs = statSync(absPath).mtimeMs;
    } catch {
      continue;
    }
    candidates.push({ path: absPath, filename: name, mtimeMs, matchedHint });
  }

  return candidates
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
    .slice(0, Math.max(1, limit ?? 5));
}

/**
 * 不同 promptHash、但主体/文件名可能让 Agent 误读的 completed 任务。
 */
export function findSimilarCompletedRecords({
  prompt,
  registry,
  skipPromptHash,
  limit = 3,
}) {
  const hints = extractSubjectHints(prompt);
  if (hints.length === 0) return [];

  const normalized = normalizePromptForGuard(prompt);
  const results = [];

  for (const r of registry?.records ?? []) {
    if (!r || r.status !== "completed") continue;
    if (skipPromptHash && r.promptHash === skipPromptHash) continue;

    const preview = normalizePromptForGuard(r.promptNormalized || r.promptPreview || "");
    if (preview === normalized) continue;

    const fileMatch = hints.some((h) =>
      (r.downloadedFiles ?? []).some(
        (df) => filenameMatchesHint(df.filename ?? "", h) || filenameMatchesHint(df.path ?? "", h),
      ),
    );
    const promptMatch = hints.some((h) => preview.includes(h));
    if (!fileMatch && !promptMatch) continue;

    const match = comparePromptsForReplay(normalized, preview);
    if (match.kind === "none") continue;

    results.push({
      record: r,
      match,
    });
  }

  return results
    .sort(
      (a, b) =>
        (b.record.completedAt ?? b.record.startedAt ?? 0) -
        (a.record.completedAt ?? a.record.startedAt ?? 0),
    )
    .slice(0, Math.max(1, limit ?? 3));
}

/**
 * status / no-task 探针时输出的防误读提示行（stdout）。
 *
 * @param {object} opts
 * @param {string} opts.prompt
 * @param {string} opts.promptHash
 * @param {import("./tasksRegistry.js").TasksRegistry} opts.registry
 * @param {string} [opts.downloadDir]
 * @param {"no_local_record"|"probe_no_task"|"awaiting_result"} [opts.kind]
 */
export function buildArtifactGuardLines({
  prompt,
  promptHash,
  registry,
  downloadDir,
  kind = "no_local_record",
}) {
  const awaiting = kind === "awaiting_result";
  const lines = [
    `ALICE_ARTIFACT_GUARD kind=${kind} promptHash=${promptHash}`,
    awaiting
      ? "[CLI][artifact-guard] 新任务仍在服务端执行；禁止读取 download/ 中同名主体文件或 STALE_REPORT_CANDIDATE 列出的旧报告。"
      : "[CLI][artifact-guard] 禁止按 download/ 修改时间、(1)/(2) 后缀或公司名猜报告。",
    "[CLI][artifact-guard] 唯一可信交付：阻塞等待 DONE 后输出 stdout 的 agentResult.value 原文（截断时读 reportFile=）；不要展示 download/ 附件。",
  ];
  if (awaiting) {
    lines.push(
      "[CLI][artifact-guard] 禁止用 check_command_status / 读最新 session.log / view_files 扫 download/ 代替等待 CLI 进程结束。",
    );
    lines.push(
      "[CLI][artifact-guard] 禁止「先读已有报告、同时重新发起」——轮询期间磁盘上的同名主体文件一律无效。",
    );
  }

  const similar = findSimilarCompletedRecords({
    prompt,
    registry,
    skipPromptHash: promptHash,
  });
  if (similar.length > 0) {
    lines.push(`ALICE_MISLEAD_RISK kind=similar_completed count=${similar.length}`);
    for (const { record, match } of similar) {
      const preview = record.promptNormalized || record.promptPreview || "";
      lines.push(
        `SIMILAR_COMPLETED_TASK taskId=${record.taskId} promptHash=${record.promptHash} matchKind=${match.kind} promptPreview=${JSON.stringify(preview)}`,
      );
      const md = (record.downloadedFiles ?? []).find((df) => /\.md$/i.test(df.path ?? ""));
      if (md?.path) {
        lines.push(`SIMILAR_COMPLETED_REPORT path=${md.path}`);
        lines.push(
          `ALICE_FORBIDDEN_READ_UNTIL_DONE path=${md.path} boundPromptHash=${record.promptHash} currentPromptHash=${promptHash}`,
        );
      }
      lines.push(
        "[CLI][artifact-guard] ↑ 其它 prompt 的已完成任务；禁止读其 download/ 附件或自行概括后交给用户。",
      );
    }
  }

  if (downloadDir) {
    const orphans = findOrphanDownloadCandidates({ prompt, registry, downloadDir });
    if (orphans.length > 0) {
      lines.push(`ALICE_ORPHAN_DOWNLOAD count=${orphans.length}`);
      for (const o of orphans) {
        lines.push(
          `ORPHAN_DOWNLOAD_CANDIDATE path=${o.path} mtimeMs=${o.mtimeMs} matchedHint=${JSON.stringify(o.matchedHint)}`,
        );
      }
      lines.push(
        "[CLI][artifact-guard] ↑ 以上文件未绑定 tasks.json，可能来自其它会话/Web UI；不可直接当本次报告。",
      );
    }
  }

  return lines;
}
