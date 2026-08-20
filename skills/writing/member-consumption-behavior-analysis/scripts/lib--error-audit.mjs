import { existsSync, mkdirSync, renameSync, rmSync, statSync, appendFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import os from 'node:os';

const LOG_RELATIVE_PATH = 'logs/workbuddy-error-events.ndjson';
const MAX_LOG_BYTES = 10 * 1024 * 1024;
const MAX_STRING_LENGTH = 4000;

export function recordSkillError(event = {}) {
  if (/^(1|true|yes)$/i.test(String(process.env.WORKBUDDY_ERROR_LOG_DISABLED || ''))) return;
  try {
    const agentRoot = findAgentRoot(process.cwd());
    const logFile = process.env.WORKBUDDY_ERROR_LOG_FILE
      ? resolve(process.env.WORKBUDDY_ERROR_LOG_FILE)
      : join(agentRoot, LOG_RELATIVE_PATH);
    rotateIfNeeded(logFile);
    mkdirSync(dirname(logFile), { recursive: true });
    const payload = sanitizeValue({
      schema: 'workbuddy-error-event/v1',
      event_id: createEventId(),
      recorded_at: new Date().toISOString(),
      source: event.source || 'skill-script',
      severity: event.severity || 'error',
      agent_root: agentRoot,
      cwd: process.cwd(),
      host: os.hostname(),
      pid: process.pid,
      node: process.version,
      ...event,
    });
    appendFileSync(logFile, `${JSON.stringify(payload)}\n`, 'utf8');
  } catch {
    // Diagnostic logging must never affect the business workflow.
  }
}

function findAgentRoot(startDir) {
  let dir = resolve(startDir || process.cwd());
  for (;;) {
    if (
      existsSync(join(dir, 'skills')) &&
      existsSync(join(dir, '.codebuddy-plugin', 'plugin.json'))
    ) return dir;
    const parent = dirname(dir);
    if (parent === dir) return resolve(startDir || process.cwd());
    dir = parent;
  }
}

function rotateIfNeeded(logFile) {
  try {
    if (!existsSync(logFile)) return;
    if (statSync(logFile).size <= MAX_LOG_BYTES) return;
    const rotated = `${logFile}.1`;
    try { rmSync(rotated, { force: true }); } catch { /* ignore */ }
    renameSync(logFile, rotated);
  } catch {
    // ignore
  }
}

function createEventId() {
  return createHash('sha256')
    .update(`${Date.now()}-${process.pid}-${Math.random()}`)
    .digest('hex')
    .slice(0, 24);
}

function sanitizeValue(value, depth = 0) {
  if (depth > 5) return '[DEPTH_LIMIT]';
  if (typeof value === 'string') return redactString(truncate(value, MAX_STRING_LENGTH));
  if (typeof value === 'number' || typeof value === 'boolean' || value === null || value === undefined) return value;
  if (value instanceof Error) {
    return {
      name: value.name,
      message: redactString(truncate(value.message || '', MAX_STRING_LENGTH)),
      stack: redactString(truncate(value.stack || '', MAX_STRING_LENGTH * 2)),
    };
  }
  if (Array.isArray(value)) return value.slice(0, 80).map((item) => sanitizeValue(item, depth + 1));
  if (typeof value === 'object') {
    const out = {};
    for (const [key, item] of Object.entries(value)) {
      out[key] = isSensitiveKey(key) ? '[REDACTED]' : sanitizeValue(item, depth + 1);
    }
    return out;
  }
  return redactString(String(value));
}

function isSensitiveKey(key) {
  return /token|authorization|cookie|password|passwd|secret|api[_-]?key|encryptData|credential|session/i.test(key);
}

function redactString(input) {
  return String(input || '')
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, 'Bearer [REDACTED]')
    .replace(/[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}/g, '[REDACTED_JWT]')
    .replace(/((?:token|authorization|cookie|password|passwd|secret|api[_-]?key|encryptData|access_token|refresh_token|fxscmToken|sly_remote_token)\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,}]+)/gi, '$1[REDACTED]')
    .replace(/(Access-Token-Shop|Fx-Token|Sly-Token|sly_token)(\s*[:=]\s*)("[^"]*"|'[^']*'|[^\s,}]+)/gi, '$1$2[REDACTED]');
}

function truncate(text, maxLength) {
  const value = String(text || '');
  if (value.length <= maxLength) return value;
  return `${value.slice(0, maxLength)}...[truncated ${value.length - maxLength} chars]`;
}
