#!/usr/bin/env node
/**
 * fbs-connector-bridge.mjs
 *
 * 脚本模式直连 FBS 服务侧 / 连接器 MCP。
 * 默认 direct 直连 API2；connector-config 仅作补充；auto 为服务优先、连接器回落。
 */

import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const DEFAULT_CONNECTOR_NAME = 'connector:fbs-connector';
const DEFAULT_SERVICE_URL = process.env.FBS_SERVICE_MCP_URL || 'https://api2.u3w.com/fbs-mcp/mcp';
const DEFAULT_ENTRY = {
  entryPromptCode: 'wb_fbs_bookwriter_3_0_review',
  entrySurface: 'workbuddy_project',
  entryId: 'fbs-bookwriter-3-0-review',
  assetType: 'resume-progress-card',
  intentFamily: 'long_document_production',
  profileSegment: 'longdoc_writer',
  semanticSource: 'codex_script_bridge',
};

export function parseArgs(argv) {
  const args = {
    command: 'help',
    transport: 'direct',
    connectorName: DEFAULT_CONNECTOR_NAME,
    configPath: null,
    url: DEFAULT_SERVICE_URL,
    headersJson: null,
    json: false,
    jsonOut: null,
    withConsume: false,
    whoamiArgs: { ...DEFAULT_ENTRY },
    explicitToolName: null,
    explicitToolArgs: {},
    fromFile: null,
  };

  let i = 2;
  if (argv[i] && !argv[i].startsWith('--')) {
    args.command = argv[i++];
  }

  for (; i < argv.length; i++) {
    const token = argv[i];
    if (token === '--transport' && argv[i + 1]) args.transport = argv[++i];
    else if (token === '--use-connector-config') args.transport = 'connector-config';
    else if (token === '--connector-name' && argv[i + 1]) {
      args.connectorName = argv[++i];
      if (args.transport === 'direct') args.transport = 'connector-config';
    } else if (token === '--config' && argv[i + 1]) {
      args.configPath = argv[++i];
      if (args.transport === 'direct') args.transport = 'connector-config';
    } else if (token === '--url' && argv[i + 1]) args.url = argv[++i];
    else if (token === '--headers-json' && argv[i + 1]) args.headersJson = JSON.parse(argv[++i]);
    else if (token === '--json') args.json = true;
    else if (token === '--json-out' && argv[i + 1]) args.jsonOut = path.resolve(argv[++i]);
    else if (token === '--with-consume') args.withConsume = true;
    else if (token === '--from' && argv[i + 1]) args.fromFile = path.resolve(argv[++i]);
    else if (token === '--tool' && argv[i + 1]) args.explicitToolName = argv[++i];
    else if (token === '--tool-args' && argv[i + 1]) args.explicitToolArgs = JSON.parse(argv[++i]);
    else if (token === '--entry-prompt-code' && argv[i + 1]) args.whoamiArgs.entryPromptCode = argv[++i];
    else if (token === '--entry-surface' && argv[i + 1]) args.whoamiArgs.entrySurface = argv[++i];
    else if (token === '--entry-id' && argv[i + 1]) args.whoamiArgs.entryId = argv[++i];
    else if (token === '--asset-type' && argv[i + 1]) args.whoamiArgs.assetType = argv[++i];
    else if (token === '--intent-family' && argv[i + 1]) args.whoamiArgs.intentFamily = argv[++i];
    else if (token === '--profile-segment' && argv[i + 1]) args.whoamiArgs.profileSegment = argv[++i];
    else if (token === '--semantic-source' && argv[i + 1]) args.whoamiArgs.semanticSource = argv[++i];
  }

  return args;
}

function printHelp() {
  console.log(`fbs-connector-bridge — FBS 服务侧 / 连接器脚本互通入口

用法：
  node scripts/fbs-connector-bridge.mjs flow --json
  node scripts/fbs-connector-bridge.mjs flow --with-consume --json
  node scripts/fbs-connector-bridge.mjs flow --transport auto --with-consume --json
  node scripts/fbs-connector-bridge.mjs whoami --json
  node scripts/fbs-connector-bridge.mjs lebao-status --json
  node scripts/fbs-connector-bridge.mjs tool --tool skill_consume --tool-args '{"...": "..."}' --json

说明：
  - 默认 direct 直连 API2：${DEFAULT_SERVICE_URL}
  - --transport connector-config：显式复用 ~/.workbuddy/connectors/*/mcp.json
  - --transport auto：先直连 API2，失败时回落到 connector-config
  - 可通过 --url / --headers-json 覆盖服务侧地址和请求头
  - 不依赖 wecom-cli
`);
}

function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  fs.mkdirSync(dir, { recursive: true });
}

function writeJson(filePath, payload) {
  ensureDir(filePath);
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

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

function loadConnectorServer(configPath, connectorName) {
  const cfg = readJson(configPath);
  const server = cfg?.mcpServers?.[connectorName];
  if (!server) throw new Error(`未在 ${configPath} 找到 ${connectorName}`);
  if (!server.url) throw new Error(`${connectorName} 缺少 url`);
  return server;
}

function buildDirectServer(args) {
  if (!args.url) throw new Error('direct 模式缺少 url；可通过 --url 或 FBS_SERVICE_MCP_URL 指定');
  return {
    url: args.url,
    type: 'streamableHttp',
    timeout: 30000,
    staticHeaders: args.headersJson || {},
  };
}

function resolveServerCandidates(args) {
  if (args.transport === 'connector-config') {
    const configPath = args.configPath ? path.resolve(args.configPath) : findConnectorConfig();
    if (!configPath) throw new Error('未找到连接器 mcp.json；可通过 --config 或 FBS_CONNECTOR_MCP_JSON 指定');
    return [{ mode: 'connector-config', server: loadConnectorServer(configPath, args.connectorName) }];
  }

  if (args.transport === 'auto') {
    const candidates = [{ mode: 'direct', server: buildDirectServer(args) }];
    const configPath = args.configPath ? path.resolve(args.configPath) : findConnectorConfig();
    if (configPath) {
      candidates.push({ mode: 'connector-config', server: loadConnectorServer(configPath, args.connectorName) });
    }
    return candidates;
  }

  return [{ mode: 'direct', server: buildDirectServer(args) }];
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
  } catch {}
  return {
    status: response.status,
    headers: Object.fromEntries(response.headers.entries()),
    text,
    json,
  };
}

function parseTextJson(text) {
  try {
    return JSON.parse(String(text || '').trim());
  } catch {
    return null;
  }
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
    } catch {}
  }
  return null;
}

function extractPrimaryPayload(rawRpc) {
  const contents = rawRpc?.json?.result?.content;
  if (!Array.isArray(contents)) return null;
  for (const item of contents) {
    const parsed = parseTextJson(item?.text);
    if (parsed && typeof parsed === 'object') return parsed;
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
        name: 'fbs-service-bridge',
        version: '0.1.0',
      },
    },
  });
}

async function callTool(server, toolName, args) {
  const raw = await rpcCall(server, {
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: toolName,
      arguments: args || {},
    },
  });
  return {
    toolName,
    arguments: args || {},
    raw,
    payload: extractPrimaryPayload(raw),
    nextToolCall: extractNextToolCall(raw),
  };
}

function summarizeServer(server) {
  return {
    url: server.url,
    type: server.type || server.transportType || null,
    timeout: server.timeout || null,
    staticHeaders: server.staticHeaders || {},
  };
}

function resolveToolEnvelope(step) {
  if (!step) return null;
  if (step.nextToolCall?.arguments) {
    return {
      toolName: step.nextToolCall.serviceToolName || step.nextToolCall.tool || step.nextToolCall.toolName,
      arguments: step.nextToolCall.arguments,
      source: 'NEXT_TOOL_CALL_JSON',
    };
  }
  if (step.payload?.actionEnvelope?.toolArguments) {
    return {
      toolName: step.payload.actionEnvelope.tool || step.payload.actionEnvelope.toolName,
      arguments: step.payload.actionEnvelope.toolArguments,
      source: 'payload.actionEnvelope.toolArguments',
    };
  }
  if (step.payload?.nextAction?.toolArguments) {
    return {
      toolName: step.payload.nextAction.tool || step.payload.nextAction.toolName,
      arguments: step.payload.nextAction.toolArguments,
      source: 'payload.nextAction.toolArguments',
    };
  }
  return null;
}

async function runFlow(server, args) {
  const initialize = await initializeServer(server);
  const whoami = await callTool(server, 'skill_whoami', args.whoamiArgs);
  const scenePackEnvelope = resolveToolEnvelope(whoami);

  let scenePack = null;
  let consume = null;

  if (scenePackEnvelope?.toolName) {
    scenePack = await callTool(server, scenePackEnvelope.toolName, scenePackEnvelope.arguments);
    if (args.withConsume) {
      const consumeEnvelope = resolveToolEnvelope(scenePack);
      if (consumeEnvelope?.toolName) {
        consume = await callTool(server, consumeEnvelope.toolName, consumeEnvelope.arguments);
      }
    }
  }

  return {
    generatedAt: new Date().toISOString(),
    mode: args.withConsume ? 'whoami_scene_pack_consume' : 'whoami_scene_pack',
    connector: summarizeServer(server),
    initialize: {
      status: initialize.status,
      payload: initialize.json?.result || null,
    },
    steps: {
      whoami,
      scenePack,
      consume,
    },
  };
}

async function executeWithServerCandidates(args, executor) {
  const candidates = resolveServerCandidates(args);
  const attempts = [];
  let lastError = null;

  for (const candidate of candidates) {
    try {
      const result = await executor(candidate.server, candidate.mode);
      result.transportResolved = candidate.mode;
      if (attempts.length) result.transportAttempts = attempts;
      return result;
    } catch (error) {
      lastError = error;
      attempts.push({
        mode: candidate.mode,
        error: error?.message || String(error),
      });
    }
  }

  if (lastError && attempts.length) {
    lastError.message = `${lastError.message} | attempts=${JSON.stringify(attempts)}`;
  }
  throw lastError || new Error('未找到可用服务侧/连接器通道');
}

export async function runCommand(args) {
  if (args.command === 'help') {
    printHelp();
    return 0;
  }

  let result;
  if (args.command === 'whoami') {
    result = await executeWithServerCandidates(args, async (server) => {
      const initialize = await initializeServer(server);
      const whoami = await callTool(server, 'skill_whoami', args.whoamiArgs);
      return {
        generatedAt: new Date().toISOString(),
        mode: 'whoami',
        connector: summarizeServer(server),
        initialize: {
          status: initialize.status,
          payload: initialize.json?.result || null,
        },
        step: whoami,
      };
    });
  } else if (args.command === 'lebao-status') {
    result = await executeWithServerCandidates(args, async (server) => {
      const initialize = await initializeServer(server);
      const payloadSource = args.fromFile ? readJson(args.fromFile) : null;
      const fallbackBinding = payloadSource?.step?.payload?.binding || payloadSource?.steps?.whoami?.payload?.binding || {};
      const toolArgs = Object.keys(args.explicitToolArgs || {}).length
        ? args.explicitToolArgs
        : {
            ...(fallbackBinding.serverBindingId ? { serverBindingId: fallbackBinding.serverBindingId } : {}),
            ...(fallbackBinding.anonymousUserCodeHash ? { anonymousUserCodeHash: fallbackBinding.anonymousUserCodeHash } : {}),
          };
      const status = await callTool(server, 'lebao_status', toolArgs);
      return {
        generatedAt: new Date().toISOString(),
        mode: 'lebao-status',
        connector: summarizeServer(server),
        initialize: {
          status: initialize.status,
          payload: initialize.json?.result || null,
        },
        step: status,
      };
    });
  } else if (args.command === 'tool') {
    if (!args.explicitToolName) throw new Error('tool 模式必须提供 --tool');
    result = await executeWithServerCandidates(args, async (server) => {
      const initialize = await initializeServer(server);
      const step = await callTool(server, args.explicitToolName, args.explicitToolArgs);
      return {
        generatedAt: new Date().toISOString(),
        mode: 'tool',
        connector: summarizeServer(server),
        initialize: {
          status: initialize.status,
          payload: initialize.json?.result || null,
        },
        step,
      };
    });
  } else if (args.command === 'scene-pack') {
    result = await executeWithServerCandidates(args, async (server) => {
      const upstream = args.fromFile ? readJson(args.fromFile) : await runFlow(server, { ...args, withConsume: false });
      const whoamiStep = upstream?.step || upstream?.steps?.whoami || upstream?.whoami;
      const envelope = resolveToolEnvelope(whoamiStep);
      if (!envelope?.toolName) throw new Error('未能从 whoami 结果解析 scene-pack 跟进参数');
      const initialize = await initializeServer(server);
      const scenePack = await callTool(server, envelope.toolName, envelope.arguments);
      return {
        generatedAt: new Date().toISOString(),
        mode: 'scene-pack',
        connector: summarizeServer(server),
        initialize: {
          status: initialize.status,
          payload: initialize.json?.result || null,
        },
        fromWhoamiSource: args.fromFile || null,
        step: scenePack,
      };
    });
  } else if (args.command === 'consume') {
    result = await executeWithServerCandidates(args, async (server) => {
      const upstream = args.fromFile ? readJson(args.fromFile) : await runFlow(server, { ...args, withConsume: false });
      const scenePackStep = upstream?.step || upstream?.steps?.scenePack || upstream?.scenePack;
      const envelope = resolveToolEnvelope(scenePackStep);
      if (!envelope?.toolName) throw new Error('未能从 scene-pack 结果解析 consume 跟进参数');
      const initialize = await initializeServer(server);
      const consume = await callTool(server, envelope.toolName, envelope.arguments);
      return {
        generatedAt: new Date().toISOString(),
        mode: 'consume',
        connector: summarizeServer(server),
        initialize: {
          status: initialize.status,
          payload: initialize.json?.result || null,
        },
        fromScenePackSource: args.fromFile || null,
        step: consume,
      };
    });
  } else if (args.command === 'flow') {
    result = await executeWithServerCandidates(args, async (server) => runFlow(server, args));
  } else {
    throw new Error(`未知命令：${args.command}`);
  }

  if (args.jsonOut) writeJson(args.jsonOut, result);
  if (args.json || args.jsonOut) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else {
    process.stdout.write(`${JSON.stringify({
      mode: result.mode,
      transportResolved: result.transportResolved || null,
      connector: result.connector?.url,
      nextTool: result.steps?.whoami?.nextToolCall?.tool || result.steps?.scenePack?.nextToolCall?.tool || result.step?.nextToolCall?.tool || null,
    }, null, 2)}\n`);
  }
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  runCommand(parseArgs(process.argv)).catch((error) => {
    console.error(error.message || error);
    process.exit(1);
  });
}
