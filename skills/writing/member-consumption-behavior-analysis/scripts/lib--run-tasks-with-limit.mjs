import { execFile } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { recordSkillError } from './lib--error-audit.mjs';

function findAgentRoot(startDir = process.cwd()) {
  let dir = path.resolve(startDir);
  for (;;) {
    if (
      existsSync(path.join(dir, 'skills')) &&
      existsSync(path.join(dir, '.codebuddy-plugin', 'plugin.json'))
    ) return dir;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

function parseArg(name, fallback = undefined) {
  const idx = process.argv.indexOf(`--${name}`);
  return idx >= 0 && idx + 1 < process.argv.length ? process.argv[idx + 1] : fallback;
}

function normalizeDateTime(value, boundary = 'start') {
  if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  return `${value} ${boundary === 'end' ? '23:59:59' : '00:00:00'}`;
}

function extractJson(text) {
  const source = String(text || '').trim();
  if (!source) return null;
  const starts = [];
  for (let i = 0; i < source.length; i += 1) {
    if (source[i] === '{' || source[i] === '[') starts.push(i);
  }
  for (const start of starts) {
    for (let end = source.length; end > start; end -= 1) {
      const candidate = source.slice(start, end).trim();
      if (!candidate) continue;
      try {
        return JSON.parse(candidate);
      } catch {
        // Keep looking; CLI output may contain logs before/after JSON.
      }
    }
  }
  return null;
}

function countRows(value) {
  if (Array.isArray(value)) return value.length;
  if (!value || typeof value !== 'object') return 0;
  const candidates = [
    value.rows,
    value.list,
    value.data,
    value.data?.rows,
    value.data?.list,
    value.result?.rows,
    value.result?.list,
    value.result?.data,
    value.result?.data?.rows,
    value.result?.data?.list,
  ];
  for (const candidate of candidates) {
    if (Array.isArray(candidate)) return candidate.length;
  }
  return 1;
}

function classifyParsedStatus(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return 'ok';
  const code = data.code ?? data.statusCode ?? data.status;
  if (code === undefined || code === null || code === '') return 'ok';
  const normalized = String(code).toLowerCase();
  return ['0', '200', 'ok', 'success'].includes(normalized) ? 'ok' : 'failed';
}

function normalizeTaskStatus(status) {
  if (status === 'ok') return 'ok';
  if (status === 'timeout') return 'timeout';
  return 'failed';
}

function readBusinessError(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return null;
  return String(data.message || data.msg || data.error || data.errorMessage || data.errorMsg || '业务返回失败');
}

function withRawOutput(command) {
  return /(?:^|\s)--raw(?:=|\s|$)/.test(command) ? command : `${command} --raw`;
}

function runSlCommand(command, { cwd, timeoutMs = 120_000 } = {}) {
  return new Promise((resolve) => {
    const effectiveCommand = withRawOutput(command);
    const started = Date.now();
    execFile('sl', parseCommandToArgs(effectiveCommand), {
      cwd,
      timeout: timeoutMs,
      maxBuffer: 50 * 1024 * 1024,
      env: process.env,
    }, (error, stdout, stderr) => {
      const elapsedMs = Date.now() - started;
      if (error) {
        const timedOut = error.killed || error.signal === 'SIGTERM' || /timed out|timeout/i.test(error.message || '');
        const status = timedOut ? 'timeout' : 'failed';
        recordSkillError({
          source: 'skill-runner',
          kind: 'sl_command_failed',
          message: error.message || String(error),
          status,
          elapsed_ms: elapsedMs,
          context: {
            command: effectiveCommand,
            stderr: stderr?.slice(0, 2000) || '',
            stdout_preview: stdout?.slice(0, 1000) || '',
          },
        });
        resolve({
          status,
          elapsedMs,
          error: error.message || String(error),
          stderr: stderr?.slice(0, 500) || '',
          stdoutPreview: stdout?.slice(0, 500) || '',
          data: null,
          rowCount: 0,
        });
        return;
      }
      const data = extractJson(stdout) ?? extractJson(stderr);
      if (!data) {
        resolve({
          status: 'ok',
          elapsedMs,
          data: stdout.trim(),
          rowCount: 0,
          error: null,
        });
        return;
      }
      const status = classifyParsedStatus(data);
      const rowCount = countRows(data);
      resolve({
        status,
        elapsedMs,
        data,
        rowCount,
        error: status === 'ok' ? null : String(data.message || data.msg || data.error || '业务返回失败'),
      });
    });
  });
}

export async function runTasksWithLimit(tasks, { concurrency = 4, cwd } = {}) {
  const agentRoot = cwd || findAgentRoot();
  const results = {};
  const started = Date.now();

  const queue = [...tasks];
  const running = new Set();

  await new Promise((done) => {
    function next() {
      while (running.size < concurrency && queue.length > 0) {
        const task = queue.shift();
        const p = runSlCommand(task.command, { cwd: agentRoot, timeoutMs: task.timeoutMs || 120_000 })
          .then((result) => {
            results[task.name] = { ...result, name: task.name };
            running.delete(p);
            next();
          });
        running.add(p);
      }
      if (running.size === 0 && queue.length === 0) done();
    }
    next();
  });

  const elapsedMs = Date.now() - started;
  const statuses = Object.values(results).map((r) => r.status);
  const overallStatus = statuses.every((s) => s === 'ok') ? 'ok'
    : statuses.every((s) => s === 'failed' || s === 'timeout') ? 'failed'
    : 'partial';

  return { status: overallStatus, elapsedMs, queries: results };
}

/**
 * 通过 `sl batch` 单进程执行多条 CLI 命令（共享 Connector 运行时上下文，零额外启动开销）。
 * 自动回退：若 batch 不可用（旧版 CLI），降级到 runTasksWithLimit。
 */
export async function runTasksViaBatch(tasks, { concurrency = 6, cwd } = {}) {
  const agentRoot = cwd || findAgentRoot();
  const started = Date.now();

  const batchInput = {
    concurrency,
    tasks: tasks.map((t, i) => ({
      id: t.name || `task_${i}`,
      args: parseCommandToArgs(t.command),
    })),
  };

  try {
    const result = await new Promise((resolve, reject) => {
      const child = execFile(
        'sl',
        ['batch'],
        { cwd: agentRoot, timeout: 180_000, maxBuffer: 50 * 1024 * 1024, env: process.env },
        (error, stdout, stderr) => {
          if (error) { reject(error); return; }
          const data = extractJson(stdout);
          if (!data) { reject(new Error('sl batch 未返回 JSON')); return; }
          resolve(data);
        },
      );
      child.stdin.write(JSON.stringify(batchInput));
      child.stdin.end();
    });

    const queries = {};
    for (const r of (result.results || [])) {
      const bizStatus = classifyParsedStatus(r.data);
      const taskStatus = normalizeTaskStatus(r.status);
      const status = taskStatus === 'ok' ? bizStatus : taskStatus;
      queries[r.id] = {
        name: r.id,
        status,
        elapsedMs: r.elapsed_ms,
        data: r.data ?? null,
        rowCount: r.data ? countRows(r.data) : 0,
        error: r.error || (status === 'ok' ? null : readBusinessError(r.data)),
      };
      if (status !== 'ok') {
        recordSkillError({
          source: 'skill-runner',
          kind: 'sl_batch_task_failed',
          message: r.error || readBusinessError(r.data) || `batch task ${r.id} failed`,
          status,
          elapsed_ms: r.elapsed_ms,
          context: {
            task_id: r.id,
            mode: 'batch',
          },
        });
      }
    }
    const statuses = Object.values(queries).map((q) => q.status);
    const overallStatus = statuses.every((s) => s === 'ok') ? 'ok'
      : statuses.every((s) => s === 'failed' || s === 'timeout') ? 'failed'
      : 'partial';

    return { status: overallStatus, elapsedMs: Date.now() - started, queries, _mode: 'batch' };
  } catch (error) {
    recordSkillError({
      source: 'skill-runner',
      kind: 'sl_batch_failed',
      message: error instanceof Error ? error.message : String(error),
      error,
      context: {
        task_count: tasks.length,
      },
    });
    return runTasksWithLimit(tasks, { concurrency, cwd });
  }
}

function parseCommandToArgs(command) {
  const parts = [];
  let current = '';
  let inSingleQuote = false;
  let inDoubleQuote = false;
  for (let i = 0; i < command.length; i++) {
    const ch = command[i];
    if (ch === "'" && !inDoubleQuote) {
      inSingleQuote = !inSingleQuote;
    } else if (ch === '"' && !inSingleQuote) {
      inDoubleQuote = !inDoubleQuote;
    } else if (ch === ' ' && !inSingleQuote && !inDoubleQuote) {
      if (current) { parts.push(current); current = ''; }
    } else {
      current += ch;
    }
  }
  if (current) parts.push(current);
  const slIdx = parts.findIndex((p) => p === 'sl' || p.endsWith('/sl'));
  const args = slIdx >= 0 ? parts.slice(slIdx + 1) : parts;
  return args.includes('--raw') ? args : [...args, '--raw'];
}

export { findAgentRoot, parseArg, normalizeDateTime, runSlCommand, extractJson, countRows };
