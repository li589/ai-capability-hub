# qimo-conversation-insights MCP 与只读 SQL 使用规范

本文件是七陌会话洞察中 MCP 使用的权威参考。任何需要实际查询 Doris 数据的任务，都应先按本文件确认 `mcporter call`、工具参数、元数据流程、account 隔离和 SQL 安全边界。

## 目录

- MCP 调用方式
- 常用工具
- 调用示例
- 强制 SQL 安全规则
- 三段式表名
- account 数据隔离
- 元数据优先流程
- SQL 编写规范与原则
- 数据查询基本策略
- 性能与返回规模
- 错误处理
- 用户可见输出中的 SQL

## MCP 调用方式

固定 MCP URL：

```text
https://mcp-ykfdoris.7moor.com/mcp
```

macOS / Linux：

```bash
mcporter call "https://mcp-ykfdoris.7moor.com/mcp" "<工具名>" --args '<JSON 参数>'
```

Windows PowerShell：

```powershell
chcp 65001 >nul && mcporter call "https://mcp-ykfdoris.7moor.com/mcp" "<工具名>" --args "{<JSON 参数，双引号用反引号转义>}"
```

Token 不写进 `--args`。Token 由 mcporter 本地配置注入，配置方式见 `references/auth.md`。

## 常用工具

工具精确参数以实际 MCP 返回 schema 为准。常用工具如下：

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `get_account` | 获取当前 Token 对应的服务端认证 account | 无 |
| `get_catalog_list` | 获取 catalog 列表 | `random_string`（必填，仅作占位校验，值随意） |
| `get_db_list` | 获取数据库列表 | `catalog_name` 可选 |
| `get_db_table_list` | 获取库下表列表 | `catalog_name`, `db_name` 可选 |
| `get_table_schema` | 获取表结构、列名、类型、注释 | `catalog_name`, `db_name`, `table_name` |
| `get_table_column_comments` | 获取列注释 | `catalog_name`, `db_name`, `table_name` |
| `get_table_comment` | 获取表注释 | `catalog_name`, `db_name`, `table_name` |
| `get_table_basic_info` | 获取表行数、列数、分区、大小等基本信息 | `catalog_name`, `db_name`, `table_name` |
| `get_table_indexes` | 获取索引信息 | `catalog_name`, `db_name`, `table_name` |
| `get_table_data_size` | 获取表数据大小 | `db_name`, `table_name`, `single_replica` |
| `exec_query` | 执行只读 SQL | `sql`, `max_rows`, `timeout`（**不要传 `catalog_name`/`db_name`**，见下方说明） |
| `get_sql_explain` | 获取 Doris 执行计划 | `sql`, `catalog_name`, `db_name`, `verbose` |
| `get_sql_profile` | 获取 SQL profile | `sql`, `catalog_name`, `db_name`, `timeout` |
| `get_adbc_connection_info` | 查看 ADBC 连接状态 | 无 |
| `get_recent_audit_logs` | 查看近期审计日志 | `days`, `limit` |

WorkBuddy 一期 `webchat_export` Token 只开放 `get_account`、元数据查询、`exec_query` 和 `get_sql_explain` 等白名单工具；`profile`、ADBC、审计、监控和治理类工具默认不可见或返回 403。

运维/监控/分析类工具只在排查性能、血缘、资源或数据新鲜度时使用，例如 `analyze_data_access_patterns`、`analyze_resource_growth_curves`。

## 调用示例

连接验证：

```bash
mcporter call "https://mcp-ykfdoris.7moor.com/mcp" "get_catalog_list" --args '{"random_string":"check"}'
```

获取表结构：

```bash
mcporter call "https://mcp-ykfdoris.7moor.com/mcp" "get_table_schema" --args '{"catalog_name":"internal","db_name":"<DB_NAME>","table_name":"<TABLE_NAME>"}'
```

执行只读 SQL：

```bash
mcporter call qimo-conversation-insights.exec_query --args "{\"sql\":\"SELECT COUNT(*) AS session_cnt FROM internal.ods_chat.ods_chat_session WHERE create_time >= '2026-06-19 00:00:00' LIMIT 1\",\"max_rows\":10,\"timeout\":30}"
```

> **exec_query 不要传 `catalog_name` / `db_name` 参数**。当前服务器在收到这两个参数时会前置执行 `USE CATALOG \`<name>\``，而 Doris 对该语法报错（`Encountered: IDENTIFIER Expected: .`）。正确做法：SQL 内使用三段式表名 `internal.ods_chat.<table>`，只传 `sql`、`max_rows`、`timeout`。

## 强制 SQL 安全规则

- 只执行只读查询。禁止写入、DDL、权限操作和导出类操作。
- 禁止关键字包括：`INSERT`、`UPDATE`、`DELETE`、`DROP`、`ALTER`、`TRUNCATE`、`CREATE`、`GRANT`、`REVOKE`、`REPLACE`、`MERGE`、`LOAD`、`OUTFILE`。
- 不执行用户直接给出的原始 SQL；用户给 SQL 思路时，也要由 AI 重写为安全只读 SQL。
- **account 由服务器自动注入，业务 SQL 一律不要手写 account 条件**（详见「account 数据隔离」一节）。
- 明细查询必须带 SQL `LIMIT`，并设置 `exec_query.max_rows`。
- 不要 `SELECT *` 拉取大字段，只取分析所需字段。
- 不查询系统配置表、内部凭证表、无关业务表或数据库内置敏感表。
- SQL 中不要输出 Token、Secret、Authorization Header、连接串、完整敏感客户标识。

## 三段式表名

`exec_query` 要求所有表引用使用三段式命名：

```sql
catalog_name.db_name.table_name
```

内部表使用：

```sql
internal.db_name.table_name
```

示例：

```sql
SELECT COUNT(*) AS session_cnt
FROM internal.ods_chat.ods_chat_session
WHERE create_time >= '2026-06-19 00:00:00'
LIMIT 1
```

即使 `exec_query` 接受 `catalog_name`、`db_name` 参数，也**不要传入**（会触发 `USE CATALOG` 语法错误），SQL 中统一使用三段式表名即可。

## account 数据隔离

> **重要**：当前七陌 MCP Server 在 SQL 层强制 account 隔离并**自动注入** account 条件。这与"必须手写 account WHERE"的常见做法不同，请严格按本节执行，否则查询会被拒绝。

### 服务器行为

- Token 绑定唯一租户 account。服务器在执行前会解析 SQL，把原查询重写为：
  ```sql
  SELECT ... FROM (SELECT * FROM internal.<db>.<table> WHERE account = '<token_account>') AS <alias> ...
  ```
- 因此**不需要、也不应该**在 SQL 里手写 account 条件。不写时服务器自动注入正确 account；写了且值与 token account 不完全相等时，返回 `ACCOUNT_CONDITION_INVALID`（`account_isolation_violation`）。
- 仅当手写条件恰好等于 token account 时才通过，但没有收益，反而易错。**统一做法：业务 SQL 一律不写 account 条件，交给服务器自动注入。**

### 如何确认当前 account

- 不要用 `SELECT DISTINCT account ...`（会被 account 隔离拒绝）。
- 正确方式：调用 `get_account`，读取返回结果里的 `account`。
- account 只信 MCP Server 的认证结果，不要从 Token、`sid`、表名或 SQL 重写日志推断。token 的 `sid` 形如 `sec_N00000047886_webchat`，但实际 account 可能是 `N00000047886`，两者不能互相推导。

### 推荐写法

业务查询直接写业务条件，不加 account：

```sql
SELECT status, COUNT(*) AS cnt
FROM internal.ods_chat.ods_chat_session
WHERE create_time >= '2026-06-19 00:00:00'
  AND create_time < '2026-06-26 00:00:00'
GROUP BY status
ORDER BY cnt DESC
```

服务器会自动注入 `account = '<token_account>'`。多表 JOIN 同理，只需保证表都用三段式命名，服务器对主表注入 account。

只有元数据查询、连接验证这类非业务查询同样不需要 account 条件（服务器仍会尝试注入，若表无 account 列会按表结构处理）。

## 元数据优先流程

当用户问题依赖 Doris 数据时，按以下顺序确认数据结构：

1. `get_account`：确认当前 Token 对应的服务端认证 account；仅用于说明上下文，业务 SQL 不手写 account。
2. `get_catalog_list`：确认可用 catalog，通常内部表为 `internal`。
3. `get_db_list`：确认候选数据库。
4. `get_db_table_list`：查找候选业务表。
5. `get_table_schema`：确认列名、类型和表结构。
6. `get_table_column_comments` / `get_table_comment`：理解字段业务语义。
7. 必要时用少量聚合 SQL 检查字段分布、空值率、枚举值、时间覆盖。

不要凭经验猜测表名、字段名或字段含义。如果默认表不存在，应继续查找相近表名或相关业务表；只有确认目标表、字段和时间范围内确实无记录后，才能说明没有查询到数据。

## SQL 编写规范与原则

> 总原则：如果遇到业务语义字段，并且在当前上下文中没有明确拿到过，必须先通过 MCP 元数据能力确认实际表、字段、字段含义、数据粒度和表间关系，再根据用户问题生成 SQL。

### 字段角色识别

写 SQL 前先识别本次问题需要哪些字段角色：
如果字段语义不确定，先查询少量样本或使用列分布分析确认，不要强行套用某个测试表字段。

### 表关系识别

当存在多张业务表时，必须先判断是否需要 JOIN。

### 时间范围

- 用户指定时间时，转换为明确起止时间后写入 `WHERE`。
- 用户未指定时间时，应先根据问题判断是否需要默认时间范围；涉及“最近、当前、高频、趋势、风险”的分析通常默认最近 7 天。
- 如果表没有可用时间字段，应明确说明无法做时间范围过滤，并改用可用字段或要求补充数据。
- 避免在大表上无时间条件扫描全量数据。只有做元数据确认、极小表探测或用户明确要求全量统计时，才可以不加时间过滤。
- 输出结果时说明实际使用的时间字段和起止范围。

### 聚合优先，明细克制

默认先用 SQL 聚合回答“多少、占比、排名、趋势、异常对象”。只有以下情况才拉取明细文本：

- 用户要求解释原因、归类主题、引用原话或查看典型样本；
- 结构化字段无法直接回答，需要模型理解文本；
- 需要核验 SQL 统计出来的异常对象是否真实成立。

明细查询必须控制列数和行数，只取分析所需字段，例如主体 ID、时间、维度、文本片段、关键指标。不要 `SELECT *` 拉取大字段。

### 文本检索与语义分析

文本检索应基于实际文本字段，并将关键词限制在用户问题和业务目标相关范围内。不要一次性堆入过多关键词造成噪声。

关键词检索只能作为候选召回，不能直接等同于最终分类、情绪或风险判断。重要结论需要抽样阅读上下文。

### 指标类型与转换

指标字段可能是数值、字符串、枚举、时间戳或时长字符串。做排序、平均值或分位数前必须确认类型：

- 数值字段可直接 `AVG`、`MAX`、`MIN`、`SUM`。
- 时间戳字段可用时间差函数计算耗时。
- 字符串时长字段应先确认格式，再转换为秒或分钟。
- 枚举字段只适合分布统计，不要当作连续数值计算。

对函数兼容性不确定时，先用少量样本验证表达式，失败后换用 Doris 当前版本支持的函数，或返回原始值并说明无法稳定换算。

### 排名、占比与趋势

- Top N 排名必须有明确排序指标和 `LIMIT`。
- 占比需要同时查询分子和分母，并说明分母口径。
- 趋势分析应按合适时间粒度聚合，例如日、周、月；不要把不同粒度混在一起。
- 增长率需要有对比周期；基数很小时要提示波动风险。

### 安全边界

- 只查询授权范围内的业务表，避免查询数据库内置表、系统配置表或无关业务表。
- 不执行用户提供的原始 SQL；用户给出 SQL 思路时，也要按只读、安全、限量规则重写。
- SQL 中不要输出 Secret、Token、连接信息、完整敏感客户标识。

## 数据查询基本策略

### 元数据优先

当用户问题依赖 Doris 数据时，先判断是否已明确 catalog、database、table、字段、时间范围、account。任一不明确时，先用元数据工具确认。

写 SQL 前尽量确认：

- 目标表是否存在。
- 关键字段是否存在。
- 字段类型是否适合过滤、聚合或排序。
- 字段注释是否符合用户问题的业务语义。
- 时间字段和时间范围是否明确。
- 主体 ID 字段表示会话、客户、工单、订单还是消息。
- 必要时检查字段取值分布、空值率或枚举值。

### 查询计划

将 SQL 拆成两类：

- 指标 SQL：统计数量、占比、排名、趋势、响应时长、差评、风险候选等。返回几十行以内。
- 证据 SQL：按 `session_id` 抽取少量完整会话或关键消息。默认每类 2 条，单次不超过 50 条消息。

优先顺序：

1. 查时间范围内总体规模：会话数、消息数、起止时间。
2. 查聚合排名或候选会话列表。
3. 查候选 `session_id` 的完整消息上下文。

### 时间、粒度与去重

- 用户指定时间时，转换为明确起止时间后写入 `WHERE`。
- 用户未指定时间时，涉及“最近、当前、高频、趋势、风险”的分析通常默认最近 7 天，并在输出中说明。
- 避免在大表上无时间条件扫描全量数据。
- 先判断表粒度：一行是消息、会话、客户、订单、工单，还是聚合行。
- 问“多少会话/客户/工单”时，优先使用对应主体 ID 去重；问“多少条消息/记录”时才使用行数。
- 明细表上一条主体可能有多行时，先按主体 ID 聚合，再做维度统计，避免重复放大。

## 性能与返回规模

- `exec_query.max_rows` 默认 100，明细查询应显式设置。
- 大查询先查规模，再决定是否聚合、采样或分批。
- 复杂 SQL、宽表、大范围查询先用 `get_sql_explain`。
- 查询超时时，缩短时间范围、减少列、先聚合、降低 LIMIT。
- 返回过多时，停止拉取明细，改为聚合或采样。

## 错误处理

| 错误/现象 | 处理 |
|-----------|------|
| 表不存在 | 用 `get_db_table_list` 查找相近表；仍找不到时说明缺少可用数据表 |
| 列不存在 | 重新读取 `get_table_schema` 和列注释，改用可用字段 |
| account 不明确 | 调用 `get_account` 获取服务端认证 account；不要做 account 探测 SQL |
| 查询超时 | 缩短时间范围、减少列、先聚合、降低 LIMIT |
| 返回过多 | 停止拉取明细，改用聚合、Top N 或分层采样 |
| SQL 语法错误 | 根据 Doris 函数兼容性重写，不暴露长错误堆栈 |
| `USE CATALOG` 兼容性错误（`Encountered: IDENTIFIER Expected: .`） | `exec_query` 传了 `catalog_name`/`db_name` 导致服务器前置 `USE CATALOG`。改为只传 `sql`+`max_rows`+`timeout`，表名用三段式 |
| `ACCOUNT_CONDITION_INVALID` / `account_isolation_violation` | SQL 里手写了 account 条件且与 token account 不等。移除手写 account 条件，交给服务器自动注入 |
| 权限不足 / forbidden | 确认 Token 权限和 account 范围 |
| 认证失败 / token invalid | 读取 `auth.md`，引导更新 MCP 配置 |
| Doris backend not alive | 数据服务故障，不能据此得出业务结论 |

## 用户可见输出中的 SQL

默认不展示内部 SQL。用户明确要求看 SQL 时，可以给脱敏后的分析 SQL：

- 可以保留 account 值，如果这是用户业务上下文的一部分。
- 不展示 Token、Header、连接信息。
- 不贴长错误堆栈。
- 说明 SQL 口径、时间范围、分母和限制。
