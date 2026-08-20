# TCOP SRE Agent 写操作与恢复 SOP

本文件是流程性操作的唯一规则源。涉及创建、修改、删除、启停、触发、配置能力、认证恢复或首次激活时，按对应步骤执行，不自由改序。

## 1. 通用门禁

### 1.1 字段分级

| 级别 | 定义 | 处理 |
|---|---|---|
| 协议必填 | API 不传即失败 | 缺失就追问，不调用 API |
| 语义必填 | API 可接受，但结果不可用 | 缺失就追问或用真实模板预填 |
| 可选 | 有合理默认 | 使用默认值并允许用户裁剪 |

语义必填项：

- 创建任务：`PromptTemplate` 非空。
- 创建 cron 任务：`CronExpr` 非空且已向用户解释自然语言含义。
- 修改任务执行内容：新 `PromptTemplate` 非空。
- 任务从 manual/webhook 改为 cron：同时提供 `CronExpr`。
- 创建分身：`Instruction.RolePosition` 与 `Instruction.CoreDuty` 非空。
- 修改分身身份：先获取完整 Instruction 五要素，修改目标项后整体回传。

多个缺口一次性列全，禁止分多轮挤牙膏。任一门禁未通过时，宁可不写，也不创建空壳对象。

### 1.2 先拉取再操作

| 目标字段 | 前置查询 |
|---|---|
| `AgentId` | `agent_api.py list` |
| `SkillIds` | `resource_api.py skills`；反查当前绑定时加 `--all` |
| `MCPIds/McpEndpointIds` | `resource_api.py mcps`；反查当前绑定时加 `--all` |
| `ResourceMapId` | `resource_api.py maps` |
| `NotifyIds` | `resource_api.py notices` |
| 任务模板 | `task_api.py templates` |

能列真实候选的信息必须工具化收集：给用户结构化候选并让其选择。只有名称、PromptTemplate、Instruction 等自由文本允许开放式追问。

### 1.3 高危确认

以下操作在调用 API 前必须展示对象、当前值、目标值和影响，并得到“确认 + 对象名/ID”的明确答复：

- 删除分身或任务。
- 修改分身或任务。
- 启用/停用任务。
- 修改任务归属分身。
- 写回 Skill/MCP/资源地图/通知关联。
- 手动触发可能产生外部副作用的任务。

用户未明确确认、只说“看看/可以吗/试试”，或确认对象不一致时，停止写操作。

### 1.4 默认值策略

采用“默认完整、用户裁剪”：

- 新任务默认 `Enabled=true`，确认创建即代表同意启用。
- 新任务优先匹配真实模板；模板的 `PromptTemplate` 与 `SkillIds` 用于预填。
- 任务 Skill 候选只来自所属分身已绑定的 Skill；模板 Skill 取其与分身 Skill 的交集。
- 新分身 Skill 默认从平台真实候选中全选后让用户裁剪；MCP、资源地图默认不绑定。
- 通知默认不绑定，但创建任务时必须主动询问是否需要通知。
- 任何 ID 都不得臆造、拼接或从历史记忆读取。

## 2. 创建任务

触发示例：“建个任务”“给告警分身加每日巡检”。固定六步：

1. **确定归属分身**
   - 用户直给 AgentId 时校验格式并 Describe。
   - 用户给名称时 List 后精确匹配；0 条或多条时让用户选择。
   - Gate：唯一 AgentId 已确认。
2. **拉取并匹配模板**
   - 调 `task_api.py templates`。
   - 按用户意图匹配真实模板；用户明确说自定义时才跳过。
   - Gate：已匹配模板，或用户明确选择自定义。
3. **确定名称、执行内容和 Skill**
   - 模板路径：显式采用模板 Name/PromptTemplate；SkillIds 取“模板 Skill ∩ 分身 Skill”。
   - 自定义路径：PromptTemplate 必须非空；Skill 只能从分身已绑定集合中选。
   - 先 `agent_api.py describe` 获取 `Agent.SkillIds`，再用 `resource_api.py skills --skill-ids ... --all` 反查名称。
   - Gate：PromptTemplate 非空且 `Task.SkillIds ⊆ Agent.SkillIds`。
4. **确定触发方式**
   - `cron`：生成 CronExpr，向用户回显表达式及自然语言含义。
   - `manual/webhook`：无需 CronExpr。
   - Gate：TriggerType 明确；cron 时 CronExpr 已确认。
5. **确定通知**
   - 主动询问是否通知；需要时先列通知模板候选。
   - Gate：用户明确要或不要；需要时 NotifyIds 来自真实查询。
6. **汇总确认并创建**
   - 回显分身、名称、PromptTemplate 摘要、触发方式、时间、Skill、通知、Enabled。
   - 用户明确确认后调用 `task_api.py create`。
   - 创建成功后按名称回执，不展示 TaskId。

注意：`TemplateId` 只用于识别模板，不能传给 CreateAIWorkbenchTask；必须把模板的 PromptTemplate 和过滤后的 SkillIds 展开传入。

## 3. 修改任务

固定五步：

1. **确定任务**：先定 AgentId，再在该分身范围内 `task_api.py list` 精确找到任务。
2. **取当前快照**：`task_api.py describe` 获取完整现状。
3. **生成变更集**：把自然语言映射为字段，只保留实际变化项。
4. **解析关联字段**：涉及 Skill/MCP/通知/资源地图时先列候选；Skill 仍受所属分身集合限制。
5. **展示 diff 并确认**：逐项展示旧值 → 新值；确认后调用 `task_api.py update`。

附加门禁：

- 只传变更字段；不动的字段不传，禁止传 `null`。
- 修改执行内容时 PromptTemplate 不得为空。
- 改为 cron 时必须同时传 CronExpr。
- `Enabled` 必须是显式布尔值。
- 清空 repeated 字段理论上需要 UpdateMask；当前 `task_api.py` 未暴露 UpdateMask，禁止声称已支持清空全部。
- 当前 CLI 不支持变更 AgentId、WebhookSecret、Metadata；需要时明确说明能力边界，不手写请求绕过。

## 4. 创建分身

固定五步：

1. **确定名称**：名称非空且用户确认。
2. **确定身份定义**：至少收集 RolePosition 与 CoreDuty；CoreTruths、Boundaries、Vibe 可选。
3. **确定资源地图**：默认不绑定；需要时先列真实地图候选。
4. **确定能力**：`resource_api.py skills --all` 拉 Skill，默认全选后让用户裁剪；MCP 默认不绑，需要时 `mcps --all` 列候选。
5. **汇总确认并创建**：展示名称、身份定义、资源地图、Skill、MCP，确认后调用 `agent_api.py create`。

禁止在 RolePosition 或 CoreDuty 为空时创建。创建成功优先展示分身名称与 AgentId。

## 5. 修改分身

固定五步：

1. **确定分身**：List 后按名称精确解析 AgentId。
2. **取当前快照**：Describe 获取完整 Instruction 和能力关联。
3. **生成变更集**：只保留实际变化项。
4. **解析关联字段**：涉及 Skill/MCP/资源地图时先列真实候选并反查名称。
5. **展示 diff 并确认**：确认后调用 `agent_api.py update`。

Instruction 是嵌套对象：修改任一项时，必须将当前五要素复制为新对象，只替换目标项，再整体回传，防止其它项被清空。

当前 CLI 只支持 Name、Description、Instruction、SkillIds、MCPIds、ResourceMapId、DisableWriteTodo。Icon、Category、Tags、LLMConfig、KnowledgeBaseIds、Status、UpdateMask 未暴露；禁止声称这些字段可通过当前脚本修改。

## 6. 配置 Skill/MCP

仅查询候选时不进入本 SOP；要写回分身配置时固定五步：

1. List 分身，唯一确定 AgentId。
2. `skills --all` / `mcps --all` 列真实候选，让用户选择。
3. Describe 分身获取当前 SkillIds/MCPIds；用 `--skill-ids/--mcp-ids ... --all` 反查当前名称。
4. 本地增删、去重，展示名称级 diff，例如 `+ 文件解析`、`- RUM MCP`。
5. 用户明确确认后，将完整新列表传给 `agent_api.py update`。

候选为 0 时：关键词可能不准则换词重搜；用户要自研 Skill/MCP 时说明当前 Skill 不支持创建或接入，不编造 ID。

当前 CLI 传空列表无法可靠表达 UpdateMask 清空语义；“清空全部”应明确告知暂不支持，而不是假装成功。

## 7. 删除、启停与手动触发

### 删除

1. List/Describe 获取对象现状和关联信息。
2. 展示不可恢复风险及影响对象。
3. 要求“确认删除 + 对象名/ID”。
4. 确认一致后调用 delete。
5. 删除后重新 List 验证对象已不存在；用名称回执。

### 启停任务

1. Describe 获取当前 Enabled。
2. 若已是目标状态，直接回执，无需写 API。
3. 展示 old → new 并确认。
4. 调 `task_api.py update --enabled true|false`。
5. Describe 验证。

启停任务定义不会取消已在运行的执行；需要中止执行时引导用户到工作台。

### 手动触发

1. Describe 确认任务存在、归属和执行内容。
2. 提示可能产生的通知或外部副作用。
3. 获得明确确认后调用 `task_api.py trigger`。
4. 通过执行记录或工作台验证结果。

## 8. 认证恢复

认证失败、凭据缺失或 TokenFailure 时只执行一轮恢复：

1. 静默运行 `python3 scripts/credential_refresh.py`。
2. `REFRESH_OK`：重试原调用一次。
3. `REFRESH_SKIP`：原凭据无需刷新，重试原调用一次。
4. `REFRESH_FAILED`：尝试有头 OAuth 登录；设置短超时，失败或超时后转无头路径。
5. 无头路径运行 `tccli auth login --browser no`，仅把授权 URL 发给用户。
6. 用户回贴 Base64 OAuth 验证码后运行 `credential_from_code.py '<code>'`；不回显验证码内容。
7. `LOGIN_OK` 后重试原调用一次；仍失败则停止自动处理，给出错误码并让用户自行配置环境变量或运行 `tccli configure`。

安全红线：不询问、不接收、不回显 SecretId/SecretKey；不运行 `env`、`cat`、`grep` 等可能暴露凭据的命令。OAuth Base64 验证码只交给凭据脚本落盘，不在回复或日志中复述。

## 9. 首次激活

1. 静默检查 SDK；缺失时在受控环境安装，最终失败才告知用户。
2. 静默检查并恢复凭据：`~/.tccli/default.credential` 优先，到期走认证恢复；均无可用凭据时回退环境变量。headless 环境（无 tccli 凭据且无浏览器）引导用户把 `TENCENTCLOUD_SECRET_ID`/`TENCENTCLOUD_SECRET_KEY` 持久化到 shell rc 文件——先 `echo $SHELL`/`uname -a` 探测，zsh→`~/.zshrc`、bash→`~/.bashrc`（macOS bash 用 `~/.bash_profile`），只展示对应环境的一种方案，密钥入口 `https://console.cloud.tencent.com/cam/capi`。
3. 调 ListAIWorkbenchAgents 探活；鉴权失败回到认证恢复，网络失败只重试一次。
4. 0 个分身：引导到 `https://console.cloud.tencent.com/monitor/ai/agent/create`，创建后继续。
5. 至少 1 个分身：仅输出一句连接成功提示，然后立即处理原请求。

## 10. 失败收敛与验证

- 相同请求不得盲目无限重试；按错误码修正参数，最多重试两次。
- 写操作失败后重新 Describe/List，判断是否“请求失败但服务端已生效”，避免重复创建或重复触发。
- 对话失败不自动重复发送用户正文；保留 session/run 信息并给出可继续追问或工作台路径。
- API 成功后必须做读后验证；验证结果与预期不一致时报告差异，不伪造成功。
