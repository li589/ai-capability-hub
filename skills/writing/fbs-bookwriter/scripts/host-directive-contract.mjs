#!/usr/bin/env node
import crypto from 'crypto';
import fs from 'fs';
import path from 'path';
import { pathToFileURL } from 'url';

export const HOST_DIRECTIVE_SCHEMA_VERSION = 'fbs.hostDirective.v1';
export const HOST_DIRECTIVE_RECEIPT_SCHEMA_VERSION = 'fbs.hostDirectiveReceipt.v1';

export const SUPPORTED_HOST_DIRECTIVE_TYPES = [
  'launch_skill',
  'launch_expert',
  'invoke_builtin_capability',
  'start_subtask',
];

const TARGET_KIND_BY_TYPE = {
  launch_skill: 'skill',
  launch_expert: 'expert',
  invoke_builtin_capability: 'builtin_capability',
  start_subtask: 'subtask',
};

const DEFAULT_PERMISSION_BY_TYPE = {
  launch_skill: 'host_confirm',
  launch_expert: 'host_confirm',
  invoke_builtin_capability: 'host_policy',
  start_subtask: 'host_confirm',
};

const BUILTIN_CAPABILITY_HINTS = new Set([
  'preview_url',
  'open_result_view',
  'read_file',
  'write_file',
  'find-skills',
  'docx',
  'pdf',
  'xlsx',
  'playwright-cli',
  'web_search',
]);

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => stableJson(item)).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function buildDirectiveId(seed) {
  const hash = crypto.createHash('sha256').update(stableJson(seed)).digest('hex').slice(0, 12);
  return `hd_${hash}`;
}

function normalizeTarget(input, type) {
  const target = input && typeof input === 'object' ? { ...input } : {};
  const expectedKind = TARGET_KIND_BY_TYPE[type] || 'host_target';
  return {
    kind: target.kind || expectedKind,
    id: target.id || target.name || null,
    displayName: target.displayName || target.title || null,
    version: target.version || null,
  };
}

export function buildHostDirective(input = {}) {
  const type = input.type || 'invoke_builtin_capability';
  const target = normalizeTarget(input.target, type);
  const now = input.createdAt || new Date().toISOString();
  const base = {
    schemaVersion: HOST_DIRECTIVE_SCHEMA_VERSION,
    directiveId: input.directiveId || null,
    type,
    target,
    arguments: input.arguments && typeof input.arguments === 'object' ? input.arguments : {},
    sameBindingRequired: input.sameBindingRequired !== false,
    permissionMode: input.permissionMode || DEFAULT_PERMISSION_BY_TYPE[type] || 'host_confirm',
    fallback: input.fallback || {
      type: 'user_visible_instruction',
      message: '宿主暂不支持该动作时，请把下一步操作说明展示给用户，并保留当前写作链路。',
    },
    receiptEventType: input.receiptEventType || 'host_directive_receipt',
    reason: input.reason || null,
    evidenceRef: input.evidenceRef || null,
    createdAt: now,
    status: input.status || 'proposed',
    executionBoundary: 'service_or_skill_only_proposes_host_executes',
    serviceExecutionClaim: false,
  };
  return {
    ...base,
    directiveId: base.directiveId || buildDirectiveId({
      type: base.type,
      target: base.target,
      arguments: base.arguments,
      createdAt: base.createdAt,
    }),
  };
}

export function validateHostDirective(directive) {
  const errors = [];
  const warnings = [];
  if (!directive || typeof directive !== 'object') {
    return { ok: false, errors: ['directive_must_be_object'], warnings };
  }
  if (directive.schemaVersion !== HOST_DIRECTIVE_SCHEMA_VERSION) {
    errors.push(`schemaVersion_must_be_${HOST_DIRECTIVE_SCHEMA_VERSION}`);
  }
  if (!SUPPORTED_HOST_DIRECTIVE_TYPES.includes(directive.type)) {
    errors.push(`unsupported_type:${directive.type || 'missing'}`);
  }
  if (!directive.directiveId || typeof directive.directiveId !== 'string') {
    errors.push('directiveId_required');
  }
  if (!directive.target || typeof directive.target !== 'object') {
    errors.push('target_required');
  } else {
    const expectedKind = TARGET_KIND_BY_TYPE[directive.type];
    if (expectedKind && directive.target.kind !== expectedKind) {
      errors.push(`target.kind_must_be_${expectedKind}`);
    }
    if (!directive.target.id || typeof directive.target.id !== 'string') {
      errors.push('target.id_required');
    }
  }
  if (!directive.receiptEventType) {
    errors.push('receiptEventType_required');
  }
  if (directive.serviceExecutionClaim !== false) {
    errors.push('serviceExecutionClaim_must_be_false');
  }
  if (directive.type === 'invoke_builtin_capability' && directive.target?.id && !BUILTIN_CAPABILITY_HINTS.has(directive.target.id)) {
    warnings.push(`builtin_capability_not_in_known_hints:${directive.target.id}`);
  }
  if (directive.type === 'start_subtask') {
    const args = directive.arguments || {};
    if (!args.title && !args.taskTitle) warnings.push('start_subtask_missing_title');
    if (!args.outputRelativePath) warnings.push('start_subtask_missing_outputRelativePath');
  }
  return {
    ok: errors.length === 0,
    errors,
    warnings,
  };
}

export function buildHostDirectiveReceipt(directive, input = {}) {
  const validation = validateHostDirective(directive);
  return {
    schemaVersion: HOST_DIRECTIVE_RECEIPT_SCHEMA_VERSION,
    directiveId: directive?.directiveId || null,
    directiveType: directive?.type || null,
    receiptEventType: directive?.receiptEventType || 'host_directive_receipt',
    status: input.status || (validation.ok ? 'accepted' : 'rejected'),
    hostExecutor: input.hostExecutor || 'dry-run',
    executedAt: input.executedAt || new Date().toISOString(),
    sameBindingPreserved: input.sameBindingPreserved ?? null,
    outputRef: input.outputRef || null,
    error: input.error || null,
    validation,
    executionBoundary: 'host_receipt_only_proves_host_side_handling',
  };
}

export function buildHostDirectiveContractSummary(input = {}) {
  return {
    contractVersion: input.contractVersion || '1',
    schemaVersion: HOST_DIRECTIVE_SCHEMA_VERSION,
    documentationRelativePath: input.documentationRelativePath || 'references/06-plugin/host-directive-contract.md',
    builderScript: input.builderScript || 'scripts/host-directive-contract.mjs',
    firstResponseJsonPath: input.firstResponseJsonPath || 'firstResponseContext.hostDirectiveContract',
    receiptEventType: input.receiptEventType || 'host_directive_receipt',
    supportedTypes: [...SUPPORTED_HOST_DIRECTIVE_TYPES],
    permissionModes: input.permissionModes || ['host_policy', 'host_confirm', 'user_confirm', 'dry_run_only'],
    executionBoundary: '服务侧或 Skill 只返回 directive；宿主或 Agent 执行后必须返回 receipt。',
    notProofOf: [
      '不证明服务侧已经直接启动 skill/expert',
      '不证明宿主已完成 UI 动作',
      '不证明自然 same-binding 业务闭环已经 join',
    ],
    sampleDirectiveShape: {
      schemaVersion: HOST_DIRECTIVE_SCHEMA_VERSION,
      directiveId: 'hd_<sha12>',
      type: 'launch_skill|launch_expert|invoke_builtin_capability|start_subtask',
      target: { kind: 'skill|expert|builtin_capability|subtask', id: '<host-visible-id>' },
      arguments: {},
      sameBindingRequired: true,
      permissionMode: 'host_confirm',
      fallback: { type: 'user_visible_instruction', message: '<fallback>' },
      receiptEventType: 'host_directive_receipt',
      serviceExecutionClaim: false,
    },
  };
}

function slugify(value) {
  return String(value || 'host-directive')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 48) || 'host-directive';
}

function extractQuotedPath(cmd) {
  const match = String(cmd || '').match(/"([^"]+)"/);
  return match?.[1] || null;
}

function buildDirectiveFromAction(action, context = {}) {
  if (!action || typeof action !== 'object') return null;
  const label = String(action.label || 'host action');
  const cmd = String(action.cmd || '').trim();
  if (!cmd && !action.action) return null;

  if (/^read_file\b/i.test(cmd)) {
    const targetPath = extractQuotedPath(cmd);
    return buildHostDirective({
      type: 'invoke_builtin_capability',
      target: { id: 'read_file', displayName: '读取文件' },
      arguments: {
        path: targetPath,
        command: cmd,
        label,
      },
      sameBindingRequired: false,
      permissionMode: action.required ? 'host_confirm' : 'host_policy',
      reason: action.reason || '读取用户授权范围内的书稿台账或恢复工件。',
      evidenceRef: context.source || 'intake-router.actions',
      receiptEventType: context.receiptEventType || 'host_directive_receipt',
    });
  }

  if (/^(node|npm|pnpm|yarn)\b/i.test(cmd)) {
    return buildHostDirective({
      type: 'start_subtask',
      target: { id: slugify(label), displayName: label },
      arguments: {
        title: label,
        command: cmd,
        goalImpact: action.goalImpact || null,
        outputRelativePath: `.fbs/host-directives/${slugify(label)}.json`,
      },
      sameBindingRequired: true,
      permissionMode: action.required ? 'host_confirm' : 'dry_run_only',
      reason: action.reason || '将可执行脚本动作显式交给宿主或 worker 层处理并回执。',
      evidenceRef: context.source || 'intake-router.actions',
      receiptEventType: context.receiptEventType || 'host_directive_receipt',
    });
  }

  return null;
}

export function buildHostDirectivesFromIntakeActions(actions = [], context = {}) {
  if (!Array.isArray(actions)) return [];
  return actions
    .map((action) => buildDirectiveFromAction(action, context))
    .filter(Boolean);
}

export function buildReviewDirectiveSuite() {
  const directives = [
    buildHostDirective({
      type: 'launch_skill',
      target: { id: 'humanizer', displayName: '去 AI 味 / 风格统一 Skill' },
      arguments: {
        intent: 'de_ai_polish',
        inputRef: 'deliverables/de-ai-diff.md',
        outputRelativePath: '.fbs/host-directives/humanizer-result.json',
      },
      reason: '成稿后处理场景需要可选调用宿主已安装写作增强 Skill。',
    }),
    buildHostDirective({
      type: 'launch_expert',
      target: { id: 'fbs-researcher', displayName: '资料核查专家' },
      arguments: {
        task: '核对长文档事实来源与引用缺口',
        outputRelativePath: '.fbs/host-directives/researcher-fact-check.json',
      },
      reason: '事实核查应由宿主可见 expert/agent 承担，Skill 只保留落盘和门禁事实。',
    }),
    buildHostDirective({
      type: 'invoke_builtin_capability',
      target: { id: 'preview_url', displayName: '打开预览' },
      arguments: {
        url: 'http://127.0.0.1:0/preview.html',
        source: 'host-consume-presentation',
      },
      permissionMode: 'host_policy',
      reason: '展示类能力继续沿用宿主执行边界。',
    }),
    buildHostDirective({
      type: 'start_subtask',
      target: { id: 'post-draft-qc-worker', displayName: '后处理质检子任务' },
      arguments: {
        title: '生成版式预检与改写差异摘要',
        timeoutSeconds: 900,
        outputRelativePath: '.fbs/host-directives/post-draft-qc-worker.json',
      },
      reason: '耗时质检应与主对话解耦，并把输出路径回传给主链路。',
    }),
  ];
  return {
    generatedAt: new Date().toISOString(),
    contract: buildHostDirectiveContractSummary(),
    directives,
    validation: directives.map((directive) => ({
      directiveId: directive.directiveId,
      type: directive.type,
      ...validateHostDirective(directive),
    })),
  };
}

function parseArgs(argv) {
  const args = {
    command: 'summary',
    json: false,
    jsonOut: null,
    from: null,
    status: null,
    type: null,
    targetKind: null,
    targetId: null,
    targetName: null,
    argumentsJson: null,
  };
  let i = 2;
  if (argv[i] && !argv[i].startsWith('--')) args.command = argv[i++];
  for (; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--json') args.json = true;
    else if (token === '--json-out' && argv[i + 1]) args.jsonOut = path.resolve(argv[++i]);
    else if (token === '--from' && argv[i + 1]) args.from = path.resolve(argv[++i]);
    else if (token === '--status' && argv[i + 1]) args.status = argv[++i];
    else if (token === '--type' && argv[i + 1]) args.type = argv[++i];
    else if (token === '--target-kind' && argv[i + 1]) args.targetKind = argv[++i];
    else if (token === '--target-id' && argv[i + 1]) args.targetId = argv[++i];
    else if (token === '--target-name' && argv[i + 1]) args.targetName = argv[++i];
    else if (token === '--arguments-json' && argv[i + 1]) args.argumentsJson = JSON.parse(argv[++i]);
  }
  return args;
}

function readPayload(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8').replace(/^\uFEFF/, ''));
}

function writePayload(args, payload) {
  const text = `${JSON.stringify(payload, null, 2)}\n`;
  if (args.jsonOut) {
    fs.mkdirSync(path.dirname(args.jsonOut), { recursive: true });
    fs.writeFileSync(args.jsonOut, text, 'utf8');
  }
  if (args.json || !args.jsonOut) process.stdout.write(text);
}

export async function main(argv = process.argv) {
  const args = parseArgs(argv);
  let payload;
  if (args.command === 'suite') {
    payload = buildReviewDirectiveSuite();
  } else if (args.command === 'validate') {
    if (!args.from) throw new Error('validate requires --from <json>');
    const input = readPayload(args.from);
    const directives = Array.isArray(input) ? input : (input.directives || [input]);
    payload = {
      checkedAt: new Date().toISOString(),
      validation: directives.map((directive) => ({
        directiveId: directive.directiveId || null,
        type: directive.type || null,
        ...validateHostDirective(directive),
      })),
    };
    payload.ok = payload.validation.every((item) => item.ok);
  } else if (args.command === 'receipt') {
    if (!args.from) throw new Error('receipt requires --from <json>');
    const input = readPayload(args.from);
    const directive = Array.isArray(input.directives) ? input.directives[0] : input;
    payload = buildHostDirectiveReceipt(directive, { status: args.status || 'accepted' });
  } else if (args.command === 'directive') {
    payload = buildHostDirective({
      type: args.type,
      target: {
        kind: args.targetKind,
        id: args.targetId,
        displayName: args.targetName,
      },
      arguments: args.argumentsJson || {},
    });
  } else {
    payload = buildHostDirectiveContractSummary();
  }
  writePayload(args, payload);
}

const isDirectRun = process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;
if (isDirectRun) {
  main().catch((error) => {
    console.error(error.message || error);
    process.exit(1);
  });
}
