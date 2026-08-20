# TCOP SRE Agent API / CLI 说明书

本文件面向执行 Skill 的 Agent，记录运行入口、真实 CLI 能力、关键请求契约、输出解析、对话状态、鉴权、错误处理和工作台回流。固定 API 必须通过 `scripts/` 中的封装调用，不手写请求绕过门禁。

涉及任何写操作时，同时遵循 [sop.md](sop.md)。

## 1. 运行模型

### 1.1 端点

| 能力 | Endpoint | Service | Version | 方法 |
|---|---|---|---|---|
| 分身、任务、资源、会话快照 | `monitor.tencentcloudapi.com` | `monitor` | `2023-06-16` | `call_json` |
| 对话启动 | `fibona.tencentcloudapi.com` | `fibona` | `2025-04-15` | `call_sse` |
| 通知模板 | `monitor.tencentcloudapi.com` | `monitor` | `2018-07-24` | `call_json` |

固定 Region 为 `ap-guangzhou`。工作台 URL 只能使用 `https://console.cloud.tencent.com/` 域名。

### 1.2 凭据

优先级：

1. `~/.tccli/default.credential`；OAuth STS 到期或五分钟内到期时自动调用 refreshToken 刷新。
2. 环境变量 `TENCENTCLOUD_SECRET_ID`、`TENCENTCLOUD_SECRET_KEY`，可选 `TENCENTCLOUD_SECURITY_TOKEN`。

不得读取后回显 SecretId/SecretKey，不得要求用户在聊天中发送密钥，不得把凭据写入项目文件。认证恢复见 [sop.md](sop.md#8-认证恢复)。

### 1.3 执行约定

- 使用 `python3 ${CLAUDE_SKILL_DIR:-.}/scripts/<script>.py ...`。
- 管理脚本 stdout 是 ASCII JSON；必须读取完整 stdout 并 `json.loads()`。
- 中文显示为 `\uXXXX` 说明尚未解析 JSON。
- 只向用户展示必要的名称、状态和摘要；默认隐藏 RequestId 与内部 ID。

## 2. 输出协议

| 入口 | stdout | stderr / 退出码 |
|---|---|---|
| `agent_api.py` | `{"success":true,...}` 或 `{"success":false,"error":"..."}` | 非零表示失败 |
| `task_api.py` | 同上 | 非零表示失败 |
| `resource_api.py` | 同上 | 非零表示失败 |
| `digital_twin_chat.py run/wait` | 回复正文 | 状态和告警可能在 stderr |
| `digital_twin_chat.py start` | `handle=... session_id=... run_id=...` | 非零表示启动失败 |
| `digital_twin_chat.py poll` | 本次新增文本 | stderr 含 STATUS |
| `credential_refresh.py` | `REFRESH_OK/SKIP/FAILED` | 失败原因可能在 stderr |
| `credential_from_code.py` | `LOGIN_OK/FAILED` | 不回显验证码 |
| `status/show/prune` | JSON | 人类可读说明可能在 stderr |

管理脚本已经去掉外层 `Response`；解析脚本输出时直接读取 `agents/tasks/...` 或 action 对应字段。

## 3. 分身管理 CLI

入口：`scripts/agent_api.py`

### 3.1 list

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/agent_api.py list
```

调用 `ListAIWorkbenchAgents`。关键输出：

- `agents[].AgentId`、`Name`、`Description`、`Status`
- `Instruction`、`SkillIds`、`MCPIds`、`ResourceMapId`
- `count`、`total_count`

`Status` 枚举：`standby`（就绪）/ `enable` / `disable`。

按名称选择分身时只允许精确匹配。0 条或多条都应让用户选择，不得相似匹配或默认取第一条。

### 3.2 describe

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/agent_api.py describe --agent-id agt-xxx
```

调用 `DescribeAIWorkbenchAgent`。AgentId 实际必填。用于写操作前快照、Instruction 整体 patch、能力关联反查。

### 3.3 executions

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/agent_api.py executions \
  --agent-id agt-xxx [--status completed] [--task-id tsk-xxx] \
  [--page-no 1] [--per-page 10]
```

调用 `ListAIWorkbenchExecutions`。Status 必须使用小写：`completed/failed/cancelled/timeout/running/pending`；传大写可能静默返回空列表。分页使用顶层 `PageNo/PerPage`，不使用 Limit/Offset。

关键字段：`RunId`、`SessionId`、`Name`、`Status`、`TriggerType`、`DurationMs`、`Summary`、`ErrorMsg`。TaskId、ExecutionId、SessionId 不向用户展示。

### 3.4 create

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/agent_api.py create \
  --name <name> \
  [--description <text>] \
  [--icon <value>] [--category <value>] \
  [--instruction '<json>'] \
  [--skill-ids id1,id2] [--mcp-ids id1,id2] \
  [--resource-map-id coll-xxx]
```

调用 `CreateAIWorkbenchAgent`，脚本固定传 `Source=custom`。虽然 API 协议允许缺少 Instruction，SOP 要求 `RolePosition` 与 `CoreDuty` 必须非空。

Instruction 结构：

```json
{
  "RolePosition": "角色定位",
  "CoreDuty": "核心职责",
  "CoreTruths": "核心原则",
  "Boundaries": "行为边界",
  "Vibe": "表达风格"
}
```

### 3.5 update

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/agent_api.py update \
  --agent-id agt-xxx \
  [--name <name>] [--description <text>] \
  [--instruction '<full-json>'] \
  [--skill-ids id1,id2] [--mcp-ids id1,id2] \
  [--resource-map-id coll-xxx] \
  [--disable-write-todo true|false]
```

调用 `UpdateAIWorkbenchAgent`。只传变化字段。修改 Instruction 任一项时必须先 Describe，修改本地副本，再整体回传五要素。

当前 CLI **未暴露**：`Icon`、`Category`、`Tags`、`LLMConfig`、`KnowledgeBaseIds`、`Status`、`UpdateMask`。不要声称当前脚本支持启停分身、修改 LLM、清空全部 repeated 字段或修改这些元信息。

### 3.6 delete

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/agent_api.py delete --agent-id agt-xxx
```

调用 `DeleteAIWorkbenchAgent`。不可恢复，必须先执行删除 SOP。

## 4. 任务管理 CLI

入口：`scripts/task_api.py`

### 4.1 list / describe

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py list \
  --agent-id agt-xxx [--keyword <text>] [--enabled true|false]

python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py describe --task-id tsk-xxx
```

ListAIWorkbenchTasks 的 AgentId 必填；Enabled 省略表示不过滤，禁止传 null。任务选择必须限制在已确认的分身范围内。

关键任务字段：`Name`、`Description`、`TriggerType`、`CronExpr`、`CronTimezone`、`PromptTemplate`、`OutputFormat`、`Enabled`、`NotifyIds`、`SkillIds`、`McpEndpointIds`、`ResourceMapId`、`TimeoutSec`、`RetryCount`。

### 4.2 templates

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py templates
```

调用 `ListAIWorkbenchTaskTemplates`。模板关键字段为 `TemplateId/Name/Description/Category/PromptTemplate/SkillIds`。

`TemplateId` 不能传给 CreateAIWorkbenchTask；创建时展开模板的 PromptTemplate，并将模板 SkillIds 与分身 SkillIds 求交集后传入。

### 4.3 create

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py create \
  --agent-id agt-xxx --name <name> \
  [--trigger-type cron|manual|webhook] \
  [--description <text>] [--cron '0 9 * * *'] \
  [--cron-timezone Asia/Shanghai] \
  [--prompt <text>] [--output-format markdown|json] \
  [--enabled true|false] [--notify-ids id1,id2] \
  [--timeout-sec 600] [--retry-count 0] \
  [--resource-map-id coll-xxx] \
  [--skill-ids id1,id2] [--mcp-ids id1,id2]
```

默认 `trigger-type=cron`、`enabled=true`。脚本会拦截 cron 缺 `--cron`，但不会拦截空 PromptTemplate；Agent 必须按 SOP 保证 PromptTemplate 非空。

SkillIds 必须是所属分身 SkillIds 的子集。通知、Skill、MCP、资源地图 ID 必须来自当次查询。

### 4.4 update

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py update \
  --task-id tsk-xxx \
  [--name <name>] [--description <text>] \
  [--trigger-type cron|manual|webhook] [--cron <expr>] \
  [--cron-timezone Asia/Shanghai] [--prompt <text>] \
  [--output-format markdown|json] [--enabled true|false] \
  [--notify-ids id1,id2] [--timeout-sec 600] [--retry-count 0] \
  [--resource-map-id coll-xxx] \
  [--skill-ids id1,id2] [--mcp-ids id1,id2]
```

只传变化字段。改为 cron 时脚本要求同时提供 `--cron`。当前 CLI **未暴露** `AgentId`、`WebhookSecret`、`Metadata`、`UpdateMask`；清空 repeated 字段没有可靠语义，不要绕过脚本手写请求。

### 4.5 trigger / delete

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py trigger --task-id tsk-xxx
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/task_api.py delete --task-id tsk-xxx
```

Trigger 可能产生资源查询、通知或外部动作；Delete 不可恢复。两者都先按 SOP 确认。

## 5. 资源查询 CLI

入口：`scripts/resource_api.py`

### 5.1 资源地图

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/resource_api.py maps \
  [--keyword <text>] [--page-no 1] [--per-page 20]

python3 ${CLAUDE_SKILL_DIR:-.}/scripts/resource_api.py map \
  --resource-map-id coll-xxx

python3 ${CLAUDE_SKILL_DIR:-.}/scripts/resource_api.py instances \
  --resource-map-id coll-xxx [--page-no 1] [--per-page 50]
```

特殊约束：

- `ListAIWorkbenchResourceMaps` 使用顶层 `PageNo/PerPage`。
- `ListAIWorkbenchResourceInstances` 的 ResourceMapId 实际必填，分页必须嵌套为 `PageParams={PageNo,PerPage}`；脚本已封装差异。
- 实例摘要优先读取 `TCOPMetadata`、`IdKeys`、`Region`、`IsReady`。

### 5.2 Skill / MCP

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/resource_api.py skills \
  [--skill-ids id1,id2] [--keyword <text>] [--all] \
  [--page-no 1] [--per-page 20]

python3 ${CLAUDE_SKILL_DIR:-.}/scripts/resource_api.py mcps \
  [--mcp-ids id1,id2] [--keyword <text>] [--all] \
  [--page-no 1] [--per-page 20]
```

默认只返回 Enabled=true；列配置候选或反查已绑定项时使用 `--all`，否则停用项会被静默遗漏。MCP 的 URL、AuthSecret、Headers 可能脱敏，禁止尝试恢复或展示敏感值。

### 5.3 通知模板

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/resource_api.py notices \
  [--notice-ids notice-a,notice-b]
```

调用 monitor `2018-07-24` 的 `DescribeAlarmNotices`，脚本固定补齐：

```json
{"Module":"monitor","Order":"DESC","PageNumber":1,"PageSize":50}
```

关键输出只需 `Id` 与 `Name`，用于任务 `NotifyIds`。当前 CLI 没有 `--keyword`，不要声称支持按名称参数搜索；需要名称匹配时拉列表后本地过滤。

## 6. 对话 CLI 与协议

入口：`scripts/digital_twin_chat.py`

### 6.1 命令

```bash
# 阻塞对话
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat.py run \
  --content <text> [--agent-id agt-xxx | --name <exact-name>] \
  [--session-id ses-xxx] [--output <path>] [--state-dir <dir>] \
  [--use-default-agent] [--no-state-write] [--poll-timeout <sec>] [--state-file <path>]

# 非阻塞
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat.py start \
  --content <text> [--agent-id agt-xxx | --name <exact-name>] \
  [--handle s1] [--title <text>] [--force] [--state-dir <dir>] [--state-file <path>]
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat.py poll --handle s1
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat.py wait --handle s1 [--timeout 120] [--output <path>] [--state-dir <dir>] [--state-file <path>]
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat.py status
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat.py prune [--handle s1 | --all]
```

可选参数说明：`--use-default-agent` 强制用默认分身 `agt-tmpl-default`（探索聊天模式，不写 last_used）；`--no-state-write` 临时模式，不写 `last_used_agent.json` 且结束后清理 main handle；`--poll-timeout` 轮询超时秒（默认 120）；`--state-file` 旧 state.json 路径兼容（取 dirname 作状态目录）；`--output` 把回复归档为 md 文件。

Agent 解析顺序：`--agent-id` > `--name` > last_used > `agt-tmpl-default`。但是用户显式给出名称或 ID 时，必须先确保唯一有效；脚本当前在按名失败时可能继续回退 last_used/default，调用方必须在执行前拦截，避免消息发给错误分身。

### 6.2 快照读协议

1. 调 fibona `SendAIWorkbenchChat`。
2. 请求仅包含 `SessionID`、`Content`、`AgentID`；fibona 使用全大写 `ID` 后缀。
3. 只消费 SSE 到获得 `SESSION_INFO.sessionId` 与 `RUN_STARTED.runId`，随即断开；断开不会取消服务端 run。
4. 轮询 monitor `ListAIWorkbenchMessages`；monitor 使用驼峰 `SessionId/AgentId`。
5. 只匹配 `Role==assistant && RunId==本轮 runId`。
6. `Status=streaming` 时可增量展示；`completed` 时 Content 为最终正文；`failed/interrupted` 为异常终态。

禁止回退到“最新 assistant 消息”，否则续聊可能返回上一轮旧答案。Content 为空时才从 `ContentBlocks` 的 `TEXT_MESSAGE_CONTENT.delta` 恢复文本。

SSE 还可能出现 `DIRECT_ROUTING` 事件（脚本仅写入 stderr 作诊断，不参与协议，无需消费）。

### 6.3 用户侧输出

- 格式：`{分身名}：{Content}`。
- 原样转述 Content，不摘要、不改写、不重排、不追加核查尾注。
- SessionId 与 RunId 只用于内部状态，不向用户展示。

## 7. 状态与并发

状态目录优先级：

1. `--state-dir`
2. `--state-file` 的 dirname（旧兼容）
3. `TCOP_SRE_STATE_DIR`
4. `$XDG_STATE_HOME/tcop-sre-agents`
5. macOS/Linux `~/.local/state/tcop-sre-agents`

布局：

```text
$STATE_DIR/
├── last_used_agent.json
└── sessions/
    ├── main.json
    ├── s1.json
    └── ...
```

每个会话文件保存 `agent_id/session_id/run_id/status/emitted_len`；`emitted_len` 防止 poll 重复输出。并发上限由 `TCOP_SRE_MAX_CONCURRENT` 控制，默认 5。每个 handle 独立锁和 session。

状态管理：

```bash
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat_state.py show
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat_state.py set --agent-id agt-xxx --name <name>
python3 ${CLAUDE_SKILL_DIR:-.}/scripts/digital_twin_chat_state.py clear
```

原生 Windows 当前不兼容：`state_io.py` 依赖 POSIX `fcntl`。Windows 用户应使用 WSL，或在实现跨平台锁前不要声称原生支持。

## 8. 错误处理

| 错误 | 处理 |
|---|---|
| `AuthFailure.TokenFailure/SecretIdNotFound` | 按认证恢复 SOP；成功后仅重试原调用一次 |
| `UnauthorizedOperation` | 告知账号无权限，联系管理员 |
| `RequestLimitExceeded` | 退避后重试一次 |
| `UnknownParameter` | 检查是否混用字段大小写、分页结构或传入 CLI 不支持字段 |
| 分身 0 条/多条匹配 | 不发消息，列候选让用户选择 |
| cron 缺表达式 | 补齐并解释 Cron 后再调用 |
| Instruction/PromptTemplate 为空 | 停止写操作，按 SOP 补齐 |
| 任务/会话不存在 | 告知已不存在或过期；对话可新开 session |
| 对话超时 | 交付已收到内容，保留状态，不自动重复发送 |
| API 写失败 | 先 Describe/List 判断是否已生效，再决定是否重试 |

错误回复给错误码和简短 message，不 dump traceback，不暴露凭据或内部事件数据。相同请求最多调整后重试两次。

## 9. 工作台回流

| 场景 | URL / 处理 |
|---|---|
| 单次会话过程 | `https://console.cloud.tencent.com/monitor/ai/work?id={AgentId}&tab=session&session_id={SessionId}` |
| 会话列表 | `https://console.cloud.tencent.com/monitor/ai/work?id={AgentId}&tab=session` |
| 结果报告 | `https://console.cloud.tencent.com/monitor/ai/work?id={AgentId}&tab=log` |
| 数据看板 | `https://console.cloud.tencent.com/monitor/ai/work?id={AgentId}&tab=chart` |
| 新建资源地图 | `https://console.cloud.tencent.com/monitor/ai/agent/resource-map/create` |
| 修改资源地图 | `https://console.cloud.tencent.com/monitor/ai/agent/resource-map` |
| 长期记忆条目管理 | 当前 Skill 不支持；只说明能力边界，不编造链接 |
| 自定义 Skill 开发 | 当前 Skill 只查询/配置已有 Skill，不支持开发或发布 |
| 自定义 MCP 接入 | 当前 Skill 只查询/配置已有 MCP，不接收私有凭据 |
| 多分身编排 | 当前不支持；可建议错峰定时、人工衔接或单分身多步骤 Prompt |

详细会话过程必须有 AgentId；缺 SessionId 时退化到会话列表。TaskId、ExecutionId、SessionId 不直接展示。

## 10. 已知实现边界

以下差异是现状，不应在精简文档时被误写成已实现：

1. `agent_api.py update` 未覆盖完整 OpenAPI 字段，也不支持 UpdateMask。
2. `task_api.py update` 未覆盖 AgentId、WebhookSecret、Metadata、UpdateMask。
3. `task_api.py create` 未在代码层强制 PromptTemplate 非空；依赖 SOP 门禁。
4. `agent_api.py create` 未在代码层强制 RolePosition/CoreDuty；依赖 SOP 门禁。
5. `resource_api.py notices` 不支持 `--keyword`。
6. 对话脚本按名失败可能回退到 last_used/default；调用前必须先唯一解析。
7. 状态锁使用 `fcntl`，不支持原生 Windows。
8. 某些对话异常路径可能输出 traceback 到 stderr；不得原样转发给用户。
9. 文档中的“失败自动调整参数重试”是 Agent 行为，不是管理脚本内置的通用重试器。
10. 云 API `ListAIWorkbenchSessions`（会话列表 + 会话生命周期状态 `active/archived/deleted`）当前无脚本封装，不在本 Skill 能力范围；查历史会话走 §9 工作台「会话列表」深链。本 Skill 的 `sessions/` 是本地 per-handle 轮询状态，与此 API 无关。

扩展这些能力时，先补脚本参数与测试，再更新本说明书；禁止只改文档宣称支持。
