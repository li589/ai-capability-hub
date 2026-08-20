#!/usr/bin/env node
/**
 * BookWriter 3.0 本地事件写入器。
 *
 * 用途：
 * - API2 / 连接器不可用时，将最小事件账本写入书稿根 `.fbs/events/`
 * - 保留 benefitSource / memberTier / creditsState 等 3.0 观测字段
 * - 同步向 trace logger 追加精简轨迹，便于宿主侧排障
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { appendTraceEvent } from './lib/fbs-trace-logger.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const EVENT_VERSION = 1;
const ALLOWED_BENEFIT_SOURCES = new Set(['api2', 'connector', 'local_cache', 'offline_default']);
const ALLOWED_MEMBER_TIERS = new Set(['T0', 'T1', 'T2', 'T3', 'unknown']);
const ALLOWED_CREDITS_STATES = new Set(['available', 'insufficient', 'offline_cache', 'unverified', 'unknown']);

function parseArgs(argv) {
  const args = {
    bookRoot: null,
    eventType: null,
    bindingId: null,
    traceId: null,
    skillVersion: null,
    connectorPackageVersion: null,
    benefitSource: 'offline_default',
    memberTier: 'unknown',
    creditsState: 'unknown',
    valueStage: null,
    commercialStage: null,
    assetType: null,
    intentFamily: null,
    notes: null,
    payloadJson: null,
    payloadFile: null,
    json: false,
    help: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const token = argv[i];
    if (token === '--book-root' && argv[i + 1]) args.bookRoot = argv[++i];
    else if ((token === '--event' || token === '--event-type') && argv[i + 1]) args.eventType = argv[++i];
    else if (token === '--binding-id' && argv[i + 1]) args.bindingId = argv[++i];
    else if (token === '--trace-id' && argv[i + 1]) args.traceId = argv[++i];
    else if (token === '--skill-version' && argv[i + 1]) args.skillVersion = argv[++i];
    else if (token === '--connector-version' && argv[i + 1]) args.connectorPackageVersion = argv[++i];
    else if (token === '--benefit-source' && argv[i + 1]) args.benefitSource = argv[++i];
    else if (token === '--member-tier' && argv[i + 1]) args.memberTier = argv[++i];
    else if (token === '--credits-state' && argv[i + 1]) args.creditsState = argv[++i];
    else if (token === '--value-stage' && argv[i + 1]) args.valueStage = argv[++i];
    else if (token === '--commercial-stage' && argv[i + 1]) args.commercialStage = argv[++i];
    else if (token === '--asset-type' && argv[i + 1]) args.assetType = argv[++i];
    else if (token === '--intent-family' && argv[i + 1]) args.intentFamily = argv[++i];
    else if (token === '--notes' && argv[i + 1]) args.notes = argv[++i];
    else if (token === '--payload-json' && argv[i + 1]) args.payloadJson = argv[++i];
    else if (token === '--payload-file' && argv[i + 1]) args.payloadFile = argv[++i];
    else if (token === '--json') args.json = true;
    else if (token === '--help' || token === '-h') args.help = true;
  }

  return args;
}

function printHelp() {
  console.log(`
用法：
  node scripts/event-writer.mjs --book-root <书稿根> --event <eventType> [--json]

常用参数：
  --binding-id <id>
  --trace-id <id>
  --benefit-source api2|connector|local_cache|offline_default
  --member-tier T0|T1|T2|T3|unknown
  --credits-state available|insufficient|offline_cache|unverified|unknown
  --payload-json <json>
  --payload-file <json-file>
`);
}

function sanitizeScalar(value, maxLen = 500) {
  if (value == null) return null;
  return String(value).trim().slice(0, maxLen) || null;
}

function sanitizeObject(input, depth = 0) {
  if (input == null) return {};
  if (depth > 3) return {};
  if (Array.isArray(input)) {
    return input.slice(0, 20).map((item) => {
      if (item && typeof item === 'object') return sanitizeObject(item, depth + 1);
      if (typeof item === 'string') return item.slice(0, 300);
      return item;
    });
  }
  if (typeof input !== 'object') return {};

  const out = {};
  for (const [key, value] of Object.entries(input)) {
    if (value == null) out[key] = null;
    else if (typeof value === 'string') out[key] = value.slice(0, 1000);
    else if (typeof value === 'number' || typeof value === 'boolean') out[key] = value;
    else if (Array.isArray(value)) out[key] = sanitizeObject(value, depth + 1);
    else if (typeof value === 'object') out[key] = sanitizeObject(value, depth + 1);
  }
  return out;
}

function readPayload(args) {
  if (args.payloadJson) {
    return sanitizeObject(JSON.parse(args.payloadJson));
  }
  if (args.payloadFile) {
    const payloadPath = path.resolve(args.payloadFile);
    return sanitizeObject(JSON.parse(fs.readFileSync(payloadPath, 'utf8')));
  }
  return {};
}

function normalizeEnum(raw, allowed, fallback) {
  const value = sanitizeScalar(raw, 64) || fallback;
  return allowed.has(value) ? value : fallback;
}

function resolveBookRoot(raw) {
  const resolved = path.resolve(String(raw || '').trim());
  if (!resolved || resolved === path.resolve('.')) {
    throw new Error('缺少 --book-root <书稿根目录>');
  }
  fs.mkdirSync(resolved, { recursive: true });
  return resolved;
}

function eventsDir(bookRoot) {
  return path.join(bookRoot, '.fbs', 'events');
}

function eventLogPath(bookRoot) {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return path.join(eventsDir(bookRoot), `bookwriter-events-${y}-${m}-${d}.jsonl`);
}

function buildEventId() {
  return `bw3_${Date.now().toString(36)}_${process.pid.toString(36)}`;
}

export function buildBookwriterEvent(raw) {
  const bookRoot = resolveBookRoot(raw.bookRoot);
  const eventType = sanitizeScalar(raw.eventType || raw.event, 120);
  if (!eventType) {
    throw new Error('缺少 --event <eventType>');
  }

  return {
    v: EVENT_VERSION,
    eventId: buildEventId(),
    ts: new Date().toISOString(),
    eventType,
    bookRoot,
    bindingId: sanitizeScalar(raw.bindingId, 120),
    traceId: sanitizeScalar(raw.traceId, 120),
    skillVersion: sanitizeScalar(raw.skillVersion, 40),
    connectorPackageVersion: sanitizeScalar(raw.connectorPackageVersion, 40),
    benefitSource: normalizeEnum(raw.benefitSource, ALLOWED_BENEFIT_SOURCES, 'offline_default'),
    memberTier: normalizeEnum(raw.memberTier, ALLOWED_MEMBER_TIERS, 'unknown'),
    creditsState: normalizeEnum(raw.creditsState, ALLOWED_CREDITS_STATES, 'unknown'),
    valueStage: sanitizeScalar(raw.valueStage, 80),
    commercialStage: sanitizeScalar(raw.commercialStage, 80),
    assetType: sanitizeScalar(raw.assetType, 80),
    intentFamily: sanitizeScalar(raw.intentFamily, 120),
    notes: sanitizeScalar(raw.notes, 500),
    payloadSummary: sanitizeObject(raw.payloadSummary || {}),
  };
}

export function appendBookwriterEvent(event) {
  const dir = eventsDir(event.bookRoot);
  fs.mkdirSync(dir, { recursive: true });
  const logPath = eventLogPath(event.bookRoot);
  fs.appendFileSync(logPath, `${JSON.stringify(event)}\n`, 'utf8');

  appendTraceEvent({
    bookRoot: event.bookRoot,
    skillRoot: path.resolve(__dirname, '..'),
    script: 'event-writer.mjs',
    event: event.eventType,
    exitCode: 0,
    payloadSummary: {
      eventId: event.eventId,
      benefitSource: event.benefitSource,
      memberTier: event.memberTier,
      creditsState: event.creditsState,
      valueStage: event.valueStage,
      commercialStage: event.commercialStage,
      assetType: event.assetType,
    },
  });

  return { path: logPath, event };
}

export function main(argv = process.argv) {
  const args = parseArgs(argv);
  if (args.help) {
    printHelp();
    return 0;
  }

  try {
    const event = buildBookwriterEvent({
      ...args,
      payloadSummary: readPayload(args),
    });
    const result = appendBookwriterEvent(event);
    if (args.json) {
      process.stdout.write(`${JSON.stringify({
        ok: true,
        eventId: result.event.eventId,
        path: result.path,
        eventType: result.event.eventType,
        benefitSource: result.event.benefitSource,
        memberTier: result.event.memberTier,
        creditsState: result.event.creditsState,
      }, null, 2)}\n`);
    } else {
      process.stdout.write(
        `[event-writer] 已写入 ${result.event.eventType} -> ${result.path}\n` +
        `  benefitSource=${result.event.benefitSource} memberTier=${result.event.memberTier} creditsState=${result.event.creditsState}\n`,
      );
    }
    return 0;
  } catch (error) {
    if (args.json) {
      process.stdout.write(`${JSON.stringify({ ok: false, error: error.message }, null, 2)}\n`);
    } else {
      console.error(`[event-writer] ${error.message}`);
    }
    return 1;
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  process.exit(main(process.argv));
}
