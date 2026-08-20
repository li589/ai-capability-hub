---
name: tcop-sre-agents
description: "腾讯云可观测平台 SRE 数字分身。用于与数字分身对话，管理分身和自动化任务，查询资源地图、资源实例、Skill、MCP
  与通知模板，以及返回 AI Workbench 深链。用户提到数字分身、SRE 分身、AI Workbench、分身任务、资源地图，或使用 #分身名
  时触发。"
description_zh: 腾讯云可观测平台SRE数字分身，支持个性化的数字分身能力，通过与分身对话进行资源查询、健康巡检、异常根因分析，自动化的任务机制实现AI自主分析，还可以管理数字分身和任务，满足可观测全场景的智能运维诉求。
description_en: "Operate Tencent Cloud TCOP AI Workbench SRE digital twins:
  chat, manage twins and tasks, query resources, and return workbench deep
  links. Trigger for digital-twin, SRE-agent, AI Workbench, task, resource-map,
  or #agent-name requests."
version: 1.2.0
author: 终端监控与智能化产品组
disable-model-invocation: true
---

# TCOP SRE 数字分身

## 使用原则

- 固定 API 只通过本目录脚本调用，不手写 OpenAPI 请求。
- 先读本文件完成意图路由；涉及写操作再读 [references/sop.md](references/sop.md)；需要参数、输出、鉴权、错误或深链细节时读 [references/agent-api.md](references/agent-api.md)。
- 内部环境检查、凭据读取、状态维护、ID 反查全部静默，仅输出最终结果、必要追问或首次欢迎语。
- 所有命令从 Skill 根目录解析：`${CLAUDE_SKILL_DIR:-.}`。

## 首次激活

1. 静默检查 `tencentcloud-sdk-python` 可导入；最低建议版本 `3.1.93`。
2. 静默检查凭据：`~/.tccli/default.credential` 优先，环境变量兜底。
3. 凭据到期时先运行 `scripts/credential_refresh.py`；失败按 [references/sop.md#8-认证恢复](references/sop.md#8-认证恢复) 处理。
4. 调 `agent_api.py list` 探活。零分身时引导到 `https://console.cloud.tencent.com/monitor/ai/agent/create`。
5. 首次成功仅输出一行：`已连接 AI Workbench（N 个数字分身）。用 #分身名 切换，直接说话即可。`，随后继续处理原请求。

headless 环境的凭据持久化、shell 探测等细则见 [references/sop.md#9-首次激活](references/sop.md#9-首次激活)。

## 意图路由（按顺序，禁止改序）

1. 消息含 `#分身名` 或 `#agt-xxx`：强制走对话；`#` 后文本整体透传，禁止拆成管理动作。
2. “问问/问一下 + 分身名”：等价于 `#分身名`。
3. 明确的分身、任务管理意图：走管理脚本；任务操作前先解析 `AgentId`。
4. 资源地图、实例、Skill、MCP、通知模板查询：走资源脚本。
5. 工作台过程、报告、历史会话、看板、资源地图编辑等：按 API 说明书返回深链或能力边界。
6. 其余请求：兜底走数字分身对话。

## 脚本入口

| 能力 | 入口 | 子命令 |
|---|---|---|
| 对话 | `scripts/digital_twin_chat.py` | `run` `start` `poll` `wait` `status` `prune` |
| 分身 | `scripts/agent_api.py` | `list` `describe` `executions` `create` `update` `delete` |
| 任务 | `scripts/task_api.py` | `list` `describe` `create` `update` `trigger` `delete` `templates` |
| 资源 | `scripts/resource_api.py` | `maps` `map` `instances` `skills` `mcps` `notices` |
| 状态 | `scripts/digital_twin_chat_state.py` | `show` `set` `clear` |
| 凭据 | `scripts/credential_refresh.py` | 无子命令；输出刷新状态 |
| 无头登录 | `scripts/credential_from_code.py` | 传 OAuth Base64 验证码 |

参数、字段、返回值和已知限制统一见 [references/agent-api.md](references/agent-api.md)。

## stdout 契约

- `agent_api.py`、`task_api.py`、`resource_api.py`：stdout 是完整 ASCII JSON；必须整体 `json.loads()`，禁止截取原文展示。
- `digital_twin_chat.py run/wait`：stdout 是回复正文；`start` 返回 handle/session/run；`poll` 返回新增文本。
- 凭据脚本：stdout 是 `REFRESH_*` 或 `LOGIN_*` 状态行。
- `status/show/prune`：stdout 为 JSON，人类提示可能写入 stderr。

## 不可违反的硬规则

1. 不询问、不接收、不回显 SecretId/SecretKey；禁止运行会打印凭据的命令。
2. 删除、修改、启停、写回 Skill/MCP 等写操作，必须按 [references/sop.md](references/sop.md) 完成快照、字段门禁、diff 回显和明确确认。
3. 绑定 Agent、Skill、MCP、资源地图、通知、模板前，先调用 List/Describe 获取真实候选，禁止编造或从历史记忆取 ID。
4. 创建任务的 `PromptTemplate`、cron 的 `CronExpr`、创建分身的 `Instruction.RolePosition/CoreDuty` 属语义必填；缺失时不调用写 API。
5. 修改嵌套 `Instruction` 时先取完整现状，只替换目标字段，再整体回传。
6. 任务的 `SkillIds` 必须是所属分身 `SkillIds` 的子集。
7. 用户明确指定分身名或 ID 但无法唯一匹配时，停止并让用户选择；不得发送给其他分身。
8. 与分身对话时原样输出：`{分身名}：{Content}`；禁止摘要、改写、追加评论。
9. 工作台链接必须以 `https://console.cloud.tencent.com/` 开头，禁止编造。
10. 用户侧优先展示名称；隐藏 TaskId、ExecutionId、SessionId、SkillId、MCPId、NoticeId、ResourceMapId。AgentId 可按 `名称(agt-xxx)` 展示。

## 数据上报（MANDATORY）

上报失败不得阻断主任务；上报内容不得包含凭据、用户正文或未脱敏敏感信息。

```bash
# 启动
bash ${CLAUDE_SKILL_DIR:-.}/tools/report.sh init skill_invoked

# 意图分类：chat / agent_manage / task_manage / resource_query
bash ${CLAUDE_SKILL_DIR:-.}/scripts/track.sh "0WEB070Y4T4G2JL2" "tcop-sre-agents" "skill_invoked" '{"session_id":"<session_id>","source":"<source>","intent_category":"<category>"}'

# 管理操作
# operation_type 取值：agent_list / agent_describe / agent_create / agent_update / agent_delete /
#   task_list / task_describe / task_create / task_update / task_trigger / task_delete / task_templates /
#   resource_maps / resource_instances / resource_skills / resource_mcps / resource_notices
bash ${CLAUDE_SKILL_DIR:-.}/scripts/track.sh "0WEB070Y4T4G2JL2" "tcop-sre-agents" "management_operation" '{"feature_module":"<agent|task|resource>","operation_type":"<operation>","status":"<success|fail>","target_id":"<id>","target_name":"<name>"}'

# 对话结束
bash ${CLAUDE_SKILL_DIR:-.}/scripts/track.sh "0WEB070Y4T4G2JL2" "tcop-sre-agents" "digital_twin_chat" '{"agent_id":"<id>","agent_name":"<name>","chat_mode":"<hash_trigger|fallback|续聊>","status":"<success|fail>"}'

# 错误
bash ${CLAUDE_SKILL_DIR:-.}/scripts/track.sh "0WEB070Y4T4G2JL2" "tcop-sre-agents" "error_occurred" '{"error_type":"<api_error|auth_error|parse_error|network_error>","error_message":"<summary>","phase":"<init|chat|agent_crud|task_crud|resource_query>"}'

# 完成
bash ${CLAUDE_SKILL_DIR:-.}/tools/report.sh complete success
bash ${CLAUDE_SKILL_DIR:-.}/tools/report.sh complete fail '{"fail_reason":"<skill_bug|api_error|user_cancel|auth_error|timeout>"}'
```
