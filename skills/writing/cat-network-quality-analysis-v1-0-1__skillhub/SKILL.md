---
name: cat-network-quality-analysis
description: "Use this skill when the user wants to analyze CAT (Cloud Automated Testing) task errors, overall quality, performance, packet-capture (pcap) analysis, or compare multiple tasks. Five intents: (1) error, (2) overall, (3) performance, (4) pcap, (5) multi-task compare. Pcap has two entries — direct (user asks for pcap, no SessionID needed) and follow-up (user replies with a candidate number from a prior report's 抓包分析候选列表, triggering a structured_json payload with SessionID). Multi-task compare: max 1 primary + 5 compare tasks; if the user does not state which is primary, or gives 1/0 task IDs, ask to complete the list first. Run the script synchronously (max 300s, fully silent), parse the JSON result on stdout, and post the report field as the chat message body — not as a file attachment. Trigger phrases: CAT分析, 拨测错误分析, 拨测网络质量, 报错分析, 整体分析, 整体报告, 性能分析, 慢速分析, 抓包分析, 抓包报告, 多任务对比, 对比分析, 任务对比, 比较任务, analyze CAT errors, compare tasks, or any CAT network-quality ask."
---

# Tencent Cloud CAT — Network Quality Analysis

调用 CAT AI Console 做网络质量 / 错误 / 抓包分析。脚本全程静默执行（不输出流式日志），最终只输出一个 JSON 到 stdout，助手解析 JSON 后把 `report` 字段内容**作为聊天消息正文**回复用户（非附件）。

JSON 输出格式：

```json
// 成功
{"code": 0, "report": "# 错误分析报告\\n...", "md_path": "/abs/path/report.md", "session_id": "xxx", "json_file": "/abs/path/json.md", "pcap_candidates": [{"index": 1, "city": "...", "operator": "...", "error_id": "...", "task_id": "...", "probe_time": "...", "code": "...", "structured_json": "<structured_json>{...}</structured_json>"}], "incomplete": false}

// 失败
{"code": 1, "error": "错误信息"}
```

## 0. 必读约束（⚠️ 每次执行前自查）

1. **绝不通过附件/上传通道发 `.md`**；必须解析 JSON 后把 `report` 字段内容作为消息正文回复。
2. **时间戳一律毫秒（13 位）**，绝不用秒。
3. **执行期间全程沉默**：不发"正在分析…"、不转发输出、不主动健康检查。脚本同步运行，等待其返回 JSON 即可。
4. **意图识别优先级**：**多任务对比 > 抓包 > 错误 > 整体 > 性能**。一旦消息里出现"抓包 / pcap / 抓个包 / 抓一下包"，一律走抓包直达，**不要**先跑错误/整体/性能再让用户选候选。
5. **Pcap 报告必须独立发送**：抓包场景脚本成功返回后，JSON 的 `report` 字段内容必须作为**一条独立消息**立刻发给用户，不拼接任何额外结论。
6. **三件套参数硬约束**：**所有调用一律必须齐传** `--start-time` / `--end-time`（`branch_pcap.md` 里两入口均已要求三件套）。`--task-id` 仅**多任务对比场景可省略**（任务 ID 由 query-text 内 `<structured_json>` 承载），其余场景必传。来源因场景而异：<br>
   - 普通语言分析（error/overall/performance）：用户指定或默认最近 3h，`--task-id` 从原话抽取。<br>
   - 抓包跟进型：从 `pcap_candidates` 候选项取 `task_id` / `probe_time`，`--start-time` = `--end-time` = `probe_time`。<br>
   - 抓包直达型：从用户原话抽取 `task_id`；用户指定时间范围时按指定范围，否则围绕 `probe_time` ±5min，均缺失时兜底 3h。<br>
   - 多任务对比：`--task-id` **不传**，任务 ID 全部放进 query-text 的 `<structured_json>`（`main_task_id` + `compare_task_ids`）；`--start-time` / `--end-time` **仍必传**，取值同普通分析（用户指定或默认最近 3h）。

## 1. References（按需查阅）

| 文件 | 用途 |
|------|------|
| `references/cli_schema.md` | CLI 参数取值约束（构造命令前必查） |
| `references/query_text_templates.md` | `--query-text` 模板与反模式（含多任务对比 `<structured_json>` 格式） |
| `references/sse_events.md` | stderr 事件语义（辅助理解） |
| `references/error_handling.md` | 脚本失败（JSON `code=1`）分类应对 |
| `references/branch_pcap.md` | **抓包分支**完整规范（5a 候选提醒 / 5b 两入口调用） |

## 2. 意图路由

| 用户输入特征 | 意图 | report_type | 入口文档 |
|------|------|------|------|
| 用户要求做**任务对比**（对比/比较/多任务对比） | **多任务对比** | `multitask_compare_report` | 本文档 §3-多任务对比 |
| 含"抓包/pcap/抓个包" | **抓包直达** | `pcap_report` | `branch_pcap.md` 5b.2（入口 B） |
| 上一轮报告含候选列表，用户回复序号 | **抓包跟进** | `pcap_report` | `branch_pcap.md` 5b.1 → 5b.2（入口 A） |
| 含"错误/报错/排查/诊断" | **错误分析** | `error_report` | 本文档 Step 1–4 |
| 含"整体/全面/汇总/概况" | **整体分析** | `overall_report` | 本文档 Step 1–4 |
| 含"慢/延迟/性能" | **性能分析** | `performance_report` | 本文档 Step 1–4 |
| 意图不明 | 默认 | `error_report` | 本文档 Step 1–4 |

> ⚠️ **用户不得直接粘贴 `<structured_json>`**：`<structured_json>` 仅由 agent 内部从 `pcap_candidates` 提取并作为 `--query-text` 传入抓包跟进型（入口 A），或由 agent 为多任务对比构造（§3-多任务对比）。用户无权直接提供此类 payload。

> ⚠️ **整体 > 性能优先级**：当消息同时包含"整体/全面/汇总/概况"和"慢/延迟/性能"关键词时（如"整体性能分析"），优先匹配**整体分析**。路由表从上到下匹配，整体分析排在性能分析之前。

> ⚠️ **抓包直达 vs 错误/整体/性能的歧义**：即使用户同一句话同时包含抓包 + 错误/整体/性能关键词（例如"抓包分析这个任务的报错"），**一律走抓包直达**——不要先跑一次 error/overall/performance 再让用户选候选序号。

## 3. 主流程（error / overall / performance）

### Step 1 — 参数收集

必填：
- `QueryText`（按 `query_text_templates.md` 选模板）
- `TaskID`（**缺失必须先问用户**，并提醒企微群需 `@机器人`）
- `StartTime` / `EndTime`（**必传**；用户未指定时间范围时默认最近 3 小时：`EndTime = 当前ms`，`StartTime = EndTime - 10800000`；用户给出具体时间范围时解析为对应毫秒戳传入。**时间信息只通过此参数传递，query-text 中不要出现任何时间描述**）

**不需要**：`SessionID`（主流程任何场景都不传）。

> 🔔 抓包两入口（`branch_pcap.md` 入口 A/B）均要求三件套齐全——入口 A 从候选项的 `task_id` / `probe_time` 字段提取；入口 B 从用户原话抽取，用户指定时间范围时按指定范围，否则围绕 `probe_time` ±5min，均缺失时兜底 3h。

### Step 2 — 输出路径

```
{task_id}/{task_id}_{report_type}_{YYYYMMDD_HHmmss}.md
```

- `{task_id}` 取命令行 `--task-id`；抓包跟进型从 `<structured_json>` payload 的 `task_id` 取；**多任务对比型**从 payload 的 `main_task_id` 取（不传 `--task-id`）
- `{report_type}` = `error_report` / `overall_report` / `performance_report` / `pcap_report` / `multitask_compare_report`
- 执行前 `mkdir -p {task_id}`
- 必须是**工作区相对路径**，不得放 `/tmp/`

### Step 3 — 同步执行（最多等待 300 秒）

`cat_network_quality_analysis.py` **内部自动判断**执行后端（tcproxycli 优先，TC3-HMAC-SHA256 签名 fallback），AI 无需关心底层走哪条路径。脚本全程静默，内部已有 300 秒硬超时，最终只输出一个 JSON 到 stdout。

```bash
OUTPUT_MD="$(pwd)/<task_id>/<task_id>_<report_type>_<YYYYMMDD_HHmmss>.md"
mkdir -p "$(dirname "$OUTPUT_MD")"
RESULT=$(python3 ${SKILL_DIR}/scripts/cat_network_quality_analysis.py \
  --query-text "<QueryText>" \
  --task-id "<TaskID>" \
  --start-time <StartTimeMs> \
  --end-time <EndTimeMs> \
  --output "$OUTPUT_MD")
echo "$RESULT"
```

> ⚠️ 脚本 stdout 只有一行 JSON，**不需要重定向到日志文件**，直接捕获到变量即可。

> 💡 脚本内部自动选择后端：
> - 若 `tcproxycli` 在 PATH 中 + `TCPROXYCLI_PROXY_ENDPOINT` + `TCPROXYCLI_SESSION_KEY` 均已设置 → 走 tcproxycli 代理模式（无需本地云凭证）
> - 否则 → fallback 到 TC3-HMAC-SHA256 签名模式（需 `CAT_SECRET_ID`/`CAT_SECRET_KEY`）

### Step 4 — 解析 JSON → 交付

解析 stdout 的 JSON，根据 `code` 字段判定：

- **`code=0`（成功）** → 从 JSON 取字段，直接作为消息正文回复用户：

  ```json
  {"code": 0, "report": "# 错误分析报告...", "md_path": "...", "session_id": "...", "json_file": "...", "incomplete": false}
  ```

  字段说明：
  - `report`：**报告正文**（已从第一个一级标题截取），直接作为消息正文回复用户
  - `md_path`：归档的 `.md` 文件路径（已在服务端写入）
  - `session_id`：会话 ID（抓包跟进时需要）
  - `json_file`：抓包候选 structured_json 清单文件路径（仅非抓包场景有候选时非空）
  - `pcap_candidates`：抓包候选列表（与 `json_file` 同时非空），每项含 `index`/`city`/`operator`/`error_id`/`task_id`/`probe_time`(毫秒时间戳)/`code`/`structured_json`，agent 取 `structured_json` 用于 `--query-text`，取 `task_id`/`probe_time` 用于三件套
  - `incomplete`：`true` 表示 SSE 流未正常收到 `agent.done` 事件（连接提前中断等），当前报告可能不完整

  **交付规则**：
  - `report` 内容**完整原样**回复，不截断、不摘要、不加"以下是分析结果"前后缀
  - 格式（表格、列表、代码块、emoji）一字不改
  - 单条消息超长可拆多条连续发送，顺序累加等于完整内容
  - **若 `incomplete` 为 `true`** → `report` 正文之后另起一行追加提醒：
    > ⚠️ 本次分析未完整返回，内容可能不全。建议缩小时间范围后重试。
  - 若 `pcap_candidates` 非空（主分析含抓包候选）→ 完整报告之后**追加一条独立消息**，跳转 `branch_pcap.md` **Step 5a**（列候选 + 邀请选序号）
  - 若本次是 **pcap 报告**（`pcap_report`）→ 报告正文独立发完，流程结束
  - 若 `pcap_candidates` 为空且非 pcap 报告 → 流程结束，不加"分析完成"结语

- **`code=1`（失败 / 超时）** → 从 JSON 取 `error` 字段，按 `error_handling.md` 分类汇报（脱敏，不贴完整 traceback），不自动重试。

  ```json
  // 一般失败
  {"code": 1, "error": "[TencentCloudSDKException] code:AuthFailure.SignatureFailure ..."}

  // 300 秒超时（error 含"SSE 调用超过 300 秒"）
  {"code": 1, "error": "SSE 调用超过 300 秒硬限制，已终止"}
  ```

  - 超时（`error` 含"超过 300 秒"）→ 提示用户分析超时，建议缩小时间范围后重试
  - 其他失败 → 按 `error_handling.md` 分类矩阵匹配关键字

## 3-多任务对比（MultiTaskCompare）

**触发条件**：用户要求做任务对比（如"对比这几个任务""多任务对比""对比一下 task-a 和 task-b"）。AnalyzeAction 为 `MultiTaskCompare`。用户给出的 task ID 可以是多个、1 个甚至 0 个——按「主次任务判定流程」补齐主任务与对比任务后再发起分析。

### 参数收集

- `QueryText`：**必须**构造为 `<structured_json>` 格式（见下），**不是**自然语言模板
- `StartTime` / `EndTime`：**必传**，取值规则**与主流程完全一致**——用户指定时间范围时解析为对应毫秒戳传入；**用户未指定时默认最近 3 小时**：`EndTime = 当前ms`，`StartTime = EndTime - 10800000`
- `TaskID`（`--task-id`）：**忽略，不传**——任务 ID 全部由 QueryText 内 `<structured_json>` 承载
- `SessionID`：不传

### QueryText 格式

```text
<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>
```

- `main_task_id`：**主任务**（对比基准）
- `compare_task_ids`：**对比任务**列表（数组）

### 主次任务判定流程

按用户给出的 task ID 数量分三种情况：

1. **用户给出多个 task ID**：
   - 用户明确说明哪个是主任务 → 直接用：`main_task_id` = 用户指定，其余为 `compare_task_ids`
   - **用户没说主次** → **必须先追问**（企微群内提醒 `@机器人`），列出手中的 task ID 让用户选主任务；用户回答后，把用户所选设为 `main_task_id`，其余全部放入 `compare_task_ids`
2. **用户只给出 1 个 task ID** → **默认该任务为主任务**（`main_task_id`），**追问用户要拿这个任务和哪些任务对比**（`compare_task_ids`）；用户给出对比任务后再发起分析
3. **用户没有给任何 task ID** → **追问用户**：想以哪个任务为主（`main_task_id`）、和哪些任务做对比（`compare_task_ids`）；拿到后再发起分析

> 🔔 三种情况都必须拿到**至少 1 个主任务 + 1 个对比任务**才发起 MultiTaskCompare 分析；信息不全时持续追问，不要拍脑袋构造 `<structured_json>`。

### 数量上限

- 一次多任务对比**最多 1 个主任务 + 5 个对比任务**
- **对比任务超过 5 个** → **告知用户超限**，请用户重新选择（减少对比任务或分多轮对比），**不发起分析**
- 主任务永远只有 1 个，不存在主任务数量超限问题

### 调用示例

```bash
QUERY_TEXT='<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>'
END_MS=$(date +%s)000
START_MS=$((END_MS - 10800000))
RESULT=$(python3 ${SKILL_DIR}/scripts/cat_network_quality_analysis.py \
  --query-text "$QUERY_TEXT" \
  --start-time $START_MS \
  --end-time $END_MS \
  --output "task-aaaabbbb/task-aaaabbbb_multitask_compare_report_$(date +%Y%m%d_%H%M%S).md")
echo "$RESULT"
```

- **不传** `--task-id`（脚本对 `MultiTaskCompare` 自动跳过 TaskID 参数）
- `--output` 建议以 `main_task_id` 为目录/文件名前缀
- 脚本按 query-text 自动推断 `AnalyzeAction=MultiTaskCompare`，也可显式传 `--analyze-action MultiTaskCompare`
- `--start-time` / `--end-time` 取值：**用户指定时间范围时按指定范围**，**未指定时默认最近 3 小时**（上面示例即默认 3h 兜底）
- 返回后走 **Step 4 交付**（`code=0` → report 正文回复；`code=1` → error_handling.md 分类应对）

## 4. 允许发声的三种场景（其余全程沉默）

1. **脚本失败（JSON `code=1`）** → 汇报错误
2. **脚本成功（JSON `code=0`）** → `report` 字段作为正文回复（Step 4 强制动作）
3. **成功且含抓包候选（`pcap_candidates` 非空）** → 追加 5a 提醒

## 5. 抓包分支总入口

凡是进入抓包场景——**无论直达还是跟进**——**立即跳转** `references/branch_pcap.md`，按 5a → 5b（5b.1 或 5b.1-bis → 5b.2）→ Step 4 的顺序执行。本 SKILL.md **不重复**抓包细节。
