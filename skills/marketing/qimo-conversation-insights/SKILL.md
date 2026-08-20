---
name: qimo-conversation-insights
version: "0.1.0"
description: 七陌会话洞察 Skill 可以基于七陌客服会话数据，帮助团队完成会话总览、问题发现、风险识别、服务质量分析、业务结果归因和行动建议输出。它不仅能识别客户高频问题、VOC 反馈、投诉风险和典型会话样本，还能结合渠道、用户身份、会话入口、处理状态、转人工、留资、预约、成交、退款和流失等结果，帮助客服、运营、销售、产品和管理团队从真实对话中发现可跟进的业务问题。
metadata:
  description_zh: "七陌客服会话洞察：基于七陌客服会话数据，做聚类、情绪风险、客服表现、采样分析和业务报告"
  description_en: "Qimo customer service conversation insights: analyze Qimo customer service conversation data for clustering, sentiment risk, agent performance, sampling analysis, and business reporting"
  version: "0.1.0"
  display_name: "七陌会话洞察"
  author: "Qimo"
display_name: "七陌会话洞察"
display_name_en: "Qimo Conversation Insights"
description_zh: "基于七陌客服会话数据做会话总览、问题发现、风险识别、服务质量分析与业务结果归因。通过只读 SQL 查询 Doris，识别高频问题、VOC 反馈、投诉风险与典型会话，输出可跟进的业务洞察与报告。"
description_en: "Analyze Qimo customer-service conversation data for overview, issue discovery, risk detection, service-quality analysis and business attribution. Runs read-only SQL over Doris to surface top issues, VOC, complaint risks and representative conversations, producing actionable insights and reports."
visibility: "public"
---

# 七陌会话洞察 Skill

本 Skill 指导 AI 使用已配置的 `qimo-conversation-insights` MCP 对七陌客服会话数据做分析。该 MCP 是通用 Doris 查询能力，不提供固定业务分析接口；AI 需要根据用户意图读取元数据、理解表结构、编写安全只读 SQL、查询适量数据，再结合会话原文输出业务洞察。

## 文件分布

本 Skill 采用“主流程完整，细节按需读取”的组织方式：

| 文件 | 用途 | 何时读取 |
|------|------|----------|
| `SKILL.md` | 触发后默认读取；保留核心规则、默认流程、引用路由、输出硬约束 | 每次使用 |
| `references/mcp_usage.md` | `qimo-conversation-insights` 工具清单、元数据流程、只读 SQL、account 隔离、三段式表名、错误处理 | 任何需要查询 Doris 数据的任务 |
| `references/analysis_playbook.md` | 大数据采样、聚类、风险识别、客服表现、典型样本、图表和报告细则 | 复杂分析、采样分析、报告输出时 |
| `references/auth.md` | MCP 配置、Token/Header、连接验证、鉴权排障 | MCP 不可用、Token/account 不明确、连接失败时 |

不要新增自定义脚本绕过 MCP。通过 `mcporter call` 调用固定 MCP URL 和 Tool；Token 由 mcporter 本地配置注入，首次配置和鉴权排障见 `references/auth.md`。

## 前置依赖

本 Skill 通过 `mcporter` 命令行调用 MCP。

- **mcporter**：MCP 客户端 CLI，用于直连七陌 MCP Server 并在请求头注入鉴权 Token。沙箱里 mcporter 通过 `~/.workbuddy/binaries/node/cli-connector-packages/` 下的 shim 暴露到默认 PATH，AI 可直接 `mcporter call`。若 `command -v mcporter` 失败，运行一次 setup 脚本（`qimo_check_status`）会自动创建 shim，之后跨会话跨调用持久可用，无需重复安装。**版本与运行时要求**：mcporter `0.9.0` 及以上需 Node.js `≥ 20.11.0`。首次配置、Token 写入与连接验证的完整流程见 `references/auth.md`。
- **Token**：由七陌签发，绑定一个租户 `account`。Token 通过 `mcporter config add --scope home` 写入 `~/.mcporter/mcporter.json`（全局持久，跨会话保留），后续所有 `mcporter call` 自动携带。

## MCP 调用速记

七陌 MCP Server 默认使用 **Streamable HTTP** 传输（mcporter 配置 `--transport http`）。

默认 MCP URL（线上）：

```text
https://mcp-ykfdoris.7moor.com/mcp
```

本地开发/调试时可改用本机地址，例如 `http://localhost:3000/mcp`。URL 与 transport 在 `mcporter config add` 时确定，后续调用统一用配置名 `qimo-conversation-insights`，不必每次传 URL。

macOS / Linux：

```bash
mcporter call qimo-conversation-insights.<工具名> --args '<JSON 参数>'
```

Windows PowerShell：

```powershell
chcp 65001 >nul && mcporter call qimo-conversation-insights.<工具名> --args "{<JSON 参数，双引号用反引号转义>}"
```

示例：

```bash
mcporter call qimo-conversation-insights.get_catalog_list --args '{"random_string":"check"}'
```

Token 不应写进 `--args`。首次配置（含 URL、transport、Token 写入）和鉴权排障见 `references/auth.md`。

## 核心原则

- 所有数据操作必须基于 `qimo-conversation-insights` MCP tools，并按上方 `mcporter call` 方式调用。
- 查询 Doris 数据前读取 `references/mcp_usage.md`，尤其是只读 SQL、account 隔离、三段式表名和 LIMIT 规则。
- account 由服务器在 SQL 层自动注入，业务 SQL **一律不要手写 account 条件**（手写且与 token account 不等会被拒绝）；详见 `references/mcp_usage.md` 的「account 数据隔离」一节。
- 只执行只读查询。禁止 `INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`TRUNCATE`、`CREATE`、`GRANT`、`REVOKE` 等写入、DDL 或权限操作。
- `exec_query` 不要传 `catalog_name`/`db_name` 参数（会触发 `USE CATALOG` 语法错误），SQL 内统一用三段式表名 `internal.<db>.<table>`。
- 不凭记忆假设 catalog、database、table、字段、字段类型或业务含义；先用 MCP 元数据能力确认。
- 优先做聚合统计，再抽取少量典型会话原文做解释和证据。
- 明细查询必须限制列数和行数，不要 `SELECT *` 拉取大字段。
- 结论必须来自查询结果和会话原文。数据不足、SQL 失败、字段缺失或样本不足时，要明确说明限制。
- 不向用户暴露 Token、Authorization Header、底层连接信息、无关内部 SQL 或长错误堆栈。
- 不把鉴权失败、连接失败、Doris 后端不可用解释为“业务无数据”。

## 默认执行流程

1. 理解用户问题：明确分析目标、时间范围、业务对象、主体粒度、是否需要图表、是否需要典型会话。
2. 确认 account：服务器自动注入 token 绑定的 account，业务 SQL 不需要手写 account 条件。若需知道当前 account 值，执行任意不带 account 的查询，从返回结果 `metadata.query` 中读取服务器重写后 SQL 里的 `account = '<...>'`（注意：`SELECT DISTINCT account` 会被 account 隔离拒绝，不要用）。
3. 读取 `references/mcp_usage.md`，按 `qimo-conversation-insights` 的元数据流程确认 catalog、database、table、schema、列注释、时间字段、主体 ID 字段、文本字段。
4. 先查规模：查询目标时间范围内会话数、消息数、起止时间、关键维度覆盖情况。
5. 做聚合：用只读 SQL 计算数量、占比、趋势、排名、异常候选。
6. 抽证据：只在需要解释原因、主题、风险、原话或样本时，按候选 `session_id` 查询少量完整上下文。
7. 涉及复杂文本分析、分层采样、聚类、风险识别、客服表现、典型会话、图表或报告输出时，先读取 `references/analysis_playbook.md` 再制定方案。
8. 输出结论：区分精确统计和模型归纳，说明数据范围、字段限制和抽样边界。

## MCP/SQL 执行前置条件

凡是需要读取 Doris 元数据、编写 SQL、调用 `exec_query`、调用 `get_sql_explain`，或通过 MCP 获取业务数据的任务，必须先完整读取 `references/mcp_usage.md`。

在读取并遵守 `references/mcp_usage.md` 前，不要生成业务 SQL，不要调用 `exec_query`，也不要根据记忆假设 catalog、database、table、字段、account 或表关系。

读取 `references/mcp_usage.md` 后，按其中流程执行：

1. 先用 MCP 元数据工具确认 catalog、database、table、schema、列注释和字段含义。
2. account 由服务器自动注入，业务 SQL 不要手写 account 条件。
3. 使用三段式表名编写只读 SQL。
4. 对明细查询同时设置 SQL `LIMIT` 和 `exec_query.max_rows`。
5. `exec_query` 只传 `sql`、`max_rows`、`timeout`，不传 `catalog_name`/`db_name`（避免 `USE CATALOG` 语法错误）。
6. 禁止执行用户原始 SQL；用户提供 SQL 思路时，也要重写为安全只读 SQL。
7. 查询失败、超时、权限不足、字段缺失或返回过多时，按 `references/mcp_usage.md` 的错误处理规则调整。

本文件只保留 MCP/SQL 的加载门禁；工具参数、SQL 安全细则、元数据优先流程、性能限制和错误处理均以 `references/mcp_usage.md` 为准。

## 通用分析查询策略

本节只描述分析策略，不提供 SQL 模板。AI 应根据实际元数据、表关系和用户问题自行生成 SQL。

### 1. 数据规模与时间覆盖

先确认目标时间范围内的数据量、主体数量和时间覆盖情况。若数据量为 0、时间范围不匹配或样本极少，应先说明限制，不要继续做复杂归因。

​	注意：当前数据同步为T+1方式，无法查询和统计当天数据。

### 2. 表选择与连接策略

优先选择与用户问题最直接相关的业务表。若一个问题需要多类信息，应判断这些信息是否来自主表、明细表、标签表或维表，并确认连接键是否可靠。

JOIN 前必须确认：

- 两张表的连接字段语义一致；
- 连接后不会造成主体记录重复放大；
- 是否需要先在明细表聚合到主体粒度再连接；
- 是否需要使用左连接保留主表主体，避免丢失无明细记录的对象。

### 3. 维度分布与 Top N

用于回答“最多的是哪些”“主要集中在哪些”“哪些对象最异常”。应选择语义明确、空值率可接受的维度字段，并说明排序口径。若维度值过多，应只返回 Top N，并把长尾合并或说明未展开。

### 4. 占比分析

占比必须有清晰分母。输出时说明分母是会话数、客户数、消息数、工单数还是样本数。不要在明细表上直接用行数占比冒充主体占比。

### 5. 趋势分析

趋势分析要选择合适时间粒度，并保证各时间段口径一致。若分析增长率，必须有对比周期；若基数很小，应提示增长率可能被少量样本放大。

### 6. 文本候选召回

文本关键词查询只用于召回候选，不等于最终结论。召回后应抽取上下文样本，由模型判断主题、情绪、风险或原因。关键词应来自用户问题、字段分布、样本观察和业务常识，不要无边界扩展。

### 7. 指标排名与异常识别

指标排名前要确认指标类型、单位、统计口径和空值情况。对于耗时、满意度、评分、金额、次数等指标，应避免混用不同单位。异常对象需要结合样本或上下文解释，不要只给排名。

### 8. 分层采样

当数据量较大且需要文本理解时，应按时间、渠道、业务线、客服组、产品、地区或其他关键维度做分层采样。避免只取最新记录或单一维度样本导致偏差。

### 9. 证据上下文

形成初步结论后，再查询少量候选主体的必要上下文。证据查询应围绕候选主体 ID、时间顺序、关键文本、关键指标和必要维度展开，只取支撑结论所需字段。

### 10. 结果可信度

如果结论来自抽样、关键词召回、模型语义归类或不完整字段，应在结果中说明可信度边界。精确统计和模型判断要区分表达：前者可以说“统计显示”，后者应说“样本中显示”或“模型归纳为”。

## 分析 Playbook 路由

当任务涉及以下任一场景时，先读取 `references/analysis_playbook.md`，再制定 SQL、采样和输出方案：

- 大数据量会话原文分析：需要聚合、分层采样、局部扩展或分批沉淀。
- 聚类/主题归因：需要从会话内容中归纳问题类型、原因或主题。
- 情绪/投诉/流失风险识别：需要结合上下文判断风险，而不是只看关键词。
- 客服表现分析：需要评价响应时效、服务质量、重复追问、未解决或解释不清。
- 典型会话/原话引用：需要抽取样本、引用片段或给出代表性案例。
- 图表、复杂报告或业务建议：需要选择图表、组织报告结构或输出行动建议。
- 可信度说明：需要解释采样边界、字段缺失、模型判断边界或复核建议。

不要仅凭本文件中的核心原则完成上述任务；`analysis_playbook.md` 是这些场景的执行依据。简单计数、普通 Top N、单次元数据查询或单次 SQL 查询不需要读取该文件。

## 输出规则

保持结果“业务可理解、结论可复核、动作可执行”。

- 简单问题直接给出核心结果、数据范围和关键口径。
- 精确统计和模型判断分开表达：前者说“统计显示”，后者说“样本中显示”或“模型归纳为”。
- 不暴露 Token、Authorization Header、底层连接信息、无关内部 SQL 或长错误堆栈。
- 不把采样归纳包装成全量精确统计。
- 复杂分析、图表、样本证据、报告结构、业务建议和可信度说明必须先读取 `references/analysis_playbook.md`。

## 异常处理路由

详细处理见 `references/mcp_usage.md` 和 `references/auth.md`。

| 问题 | 处理 |
|------|------|
| MCP 工具不可见 / mcporter 未配置 | 读取 `references/auth.md`，按其中配置方式与连接验证流程排查 |
| 表不存在 | 用元数据工具查找相近表；仍找不到时说明缺少可用数据表 |
| 列不存在 | 重新读取 schema 和列注释，改用可用列 |
| 查询超时 | 缩短时间范围、减少列、先聚合、降低 LIMIT |
| 返回过多 | 停止继续拉取明细，先聚合或抽样 |
| SQL 语法错误 | 根据 Doris 函数兼容性重写，不暴露长错误堆栈 |
| `401` / token invalid | Token 失效，按 `references/auth.md` 引导更新 mcporter 配置 |
| `403` / forbidden | Token 有效但无权访问目标 account/表，确认 Token 范围和 account |
| 后端副本不可用或连接异常 | 说明当前数据服务暂不可查询，不能据此得出业务结论 |
| `USE CATALOG` 兼容性错误 | 使用三段式表名，或调整 catalog/db 参数后重试 |
