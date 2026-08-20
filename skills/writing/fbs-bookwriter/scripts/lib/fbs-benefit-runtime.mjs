import fs from 'fs';
import os from 'os';
import path from 'path';

import { getMemberTier } from '../wecom/verify-member.mjs';

const DEFAULT_CONNECTOR_NAME = 'connector:fbs-connector';
const DEFAULT_SERVICE_URL = process.env.FBS_SERVICE_MCP_URL || 'https://api2.u3w.com/fbs-mcp/mcp';

const DEFAULT_ENTRY = {
  entryPromptCode: 'wb_fbs_bookwriter_3_0_review',
  entrySurface: 'workbuddy_project',
  entryId: 'fbs-bookwriter-3-0-review',
  assetType: 'resume-progress-card',
  intentFamily: 'long_document_production',
  profileSegment: 'longdoc_writer',
  semanticSource: 'codex_runtime_bridge',
};

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8').replace(/^\uFEFF/, ''));
}

function findConnectorConfig() {
  const envPath = process.env.FBS_CONNECTOR_MCP_JSON;
  if (envPath && fs.existsSync(envPath)) return path.resolve(envPath);
  const connectorsRoot = path.join(os.homedir(), '.workbuddy', 'connectors');
  if (!fs.existsSync(connectorsRoot)) return null;
  for (const entry of fs.readdirSync(connectorsRoot, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const candidate = path.join(connectorsRoot, entry.name, 'mcp.json');
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

function loadConnectorServer(configPath, connectorName = DEFAULT_CONNECTOR_NAME) {
  const cfg = readJson(configPath);
  const server = cfg?.mcpServers?.[connectorName];
  if (!server?.url) throw new Error(`未在 ${configPath} 找到有效的 ${connectorName}`);
  return server;
}

function resolveServerCandidates(transport = 'auto') {
  const candidates = [];
  const direct = {
    mode: 'direct',
    url: DEFAULT_SERVICE_URL,
    type: 'streamableHttp',
    timeout: 30000,
    staticHeaders: {},
  };
  if (transport === 'direct') return [direct];

  if (transport === 'connector-config') {
    const configPath = findConnectorConfig();
    if (!configPath) return [];
    return [{ mode: 'connector-config', ...loadConnectorServer(configPath) }];
  }

  candidates.push(direct);
  const configPath = findConnectorConfig();
  if (configPath) {
    candidates.push({ mode: 'connector-config', ...loadConnectorServer(configPath) });
  }
  return candidates;
}

async function rpcCall(server, body) {
  const headers = {
    'Content-Type': 'application/json',
    ...(server.staticHeaders || {}),
    ...(server.headers || {}),
  };
  const response = await fetch(server.url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  const text = await response.text();
  let json = null;
  try {
    json = JSON.parse(text);
  } catch {
    // ignore
  }
  return { status: response.status, text, json };
}

function parseTextJson(text) {
  try {
    return JSON.parse(String(text || '').trim());
  } catch {
    return null;
  }
}

function extractPayload(rawRpc) {
  const contents = rawRpc?.json?.result?.content;
  if (!Array.isArray(contents)) return null;
  for (const item of contents) {
    const parsed = parseTextJson(item?.text);
    if (parsed && typeof parsed === 'object') return parsed;
  }
  return null;
}

function extractNextToolCall(rawRpc) {
  const contents = rawRpc?.json?.result?.content;
  if (!Array.isArray(contents)) return null;
  for (const item of contents) {
    const text = String(item?.text || '');
    const marker = 'NEXT_TOOL_CALL_JSON:';
    const idx = text.indexOf(marker);
    if (idx === -1) continue;
    try {
      return JSON.parse(text.slice(idx + marker.length).trim());
    } catch {
      // ignore
    }
  }
  return null;
}

async function initializeServer(server) {
  return rpcCall(server, {
    jsonrpc: '2.0',
    id: 1,
    method: 'initialize',
    params: {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: {
        name: 'fbs-benefit-runtime',
        version: '0.1.0',
      },
    },
  });
}

async function callTool(server, toolName, args = {}) {
  const raw = await rpcCall(server, {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: args,
    },
  });
  return {
    raw,
    payload: extractPayload(raw),
    nextToolCall: extractNextToolCall(raw),
  };
}

function buildNextToolInfo(step) {
  return {
    nextTool:
      step?.nextToolCall?.tool ||
      step?.payload?.nextAction?.tool ||
      step?.payload?.actionEnvelope?.tool ||
      null,
    sameBindingRequired: !!step?.nextToolCall?.sameBindingRequired,
  };
}

export async function collectBenefitRuntimeSnapshot(options = {}) {
  const {
    transport = 'auto',
    whoamiArgs = DEFAULT_ENTRY,
  } = options;

  const local = getMemberTier();
  const snapshot = {
    benefitSource: local.benefitSource,
    memberTier: local.tier,
    creditsState: local.creditsState,
    localLedgerBalance: local.balance,
    serviceTransport: null,
    serviceAvailable: false,
    serviceWhoamiStatus: null,
    serviceBindingId: null,
    anonymousUserCodeHash: null,
    scenePackId: null,
    nextTool: null,
    lebaoStatus: {
      available: false,
      statusCode: null,
      pointsBalance: null,
      claimState: null,
      voucherCount: 0,
    },
    warnings: [],
  };

  const effectiveTransport = process.env.FBS_BENEFIT_RUNTIME_TRANSPORT || transport;
  if (['offline', 'local', 'local-only'].includes(effectiveTransport)) {
    snapshot.benefitSource = snapshot.benefitSource || 'local_cache';
    snapshot.warnings.push(`service_probe_skipped:${effectiveTransport}`);
    return snapshot;
  }

  const candidates = resolveServerCandidates(effectiveTransport);
  for (const server of candidates) {
    try {
      const initialize = await initializeServer(server);
      if (initialize.status !== 200) {
        snapshot.warnings.push(`${server.mode}: initialize=${initialize.status}`);
        continue;
      }

      const whoami = await callTool(server, 'skill_whoami', whoamiArgs);
      snapshot.serviceWhoamiStatus = whoami.raw.status;
      if (whoami.raw.status !== 200 || !whoami.payload) {
        snapshot.warnings.push(`${server.mode}: whoami_failed`);
        continue;
      }

      snapshot.serviceTransport = server.mode;
      snapshot.serviceAvailable = true;
      snapshot.serviceBindingId = whoami.payload?.binding?.serverBindingId || null;
      snapshot.anonymousUserCodeHash = whoami.payload?.binding?.anonymousUserCodeHash || null;
      snapshot.scenePackId =
        whoami.payload?.scenePack?.scenePackId ||
        whoami.payload?.nextAction?.scenePackId ||
        null;
      snapshot.nextTool = buildNextToolInfo(whoami).nextTool;

      const lebaoArgs = {};
      if (snapshot.serviceBindingId) lebaoArgs.serverBindingId = snapshot.serviceBindingId;
      if (snapshot.anonymousUserCodeHash) lebaoArgs.anonymousUserCodeHash = snapshot.anonymousUserCodeHash;
      if (Object.keys(lebaoArgs).length) {
        const lebao = await callTool(server, 'lebao_status', lebaoArgs);
        snapshot.lebaoStatus.statusCode = lebao.raw.status;
        snapshot.lebaoStatus.available = lebao.raw.status === 200 && !!lebao.payload?.success;
        snapshot.lebaoStatus.pointsBalance =
          typeof lebao.payload?.pointsBalance === 'number' ? lebao.payload.pointsBalance : null;
        snapshot.lebaoStatus.claimState = lebao.payload?.claimState || null;
        snapshot.lebaoStatus.voucherCount = Array.isArray(lebao.payload?.vouchers) ? lebao.payload.vouchers.length : 0;
      }
      break;
    } catch (error) {
      snapshot.warnings.push(`${server.mode}: ${error.message}`);
    }
  }

  return snapshot;
}
