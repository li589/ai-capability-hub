# CLI 参数 Schema

`scripts/cat_network_quality_analysis.py` 的命令行约束。**AI 每次构造命令前必须对照本表**。

> 脚本内部自动选择后端（tcproxycli 代理 / TC3-HMAC-SHA256 签名），CLI 参数完全一致，AI 无需区分模式。

## 完整签名

```bash
# 所有场景统一：三件套必传（多任务对比场景 --task-id 可省略）
python3 ${SKILL_DIR}/scripts/cat_network_quality_analysis.py \
  --query-text <TEXT> \
  [--task-id <TASK_ID>] \
  --start-time <MS> \
  --end-time <MS> \
  [--analyze-action <ACTION>] \
  [--session-id <SESSION_ID>] \
  [--suppress-pcap-candidates] \
  [--output <PATH.md>]
```

## 参数表

| 参数 | 必填 | 取值约束 | 示例 |
|------|:---:|---|---|
| `--query-text` | ✅ | 非空；**仅**抓包跟进型与多任务对比用 `<structured_json>...</structured_json>` 标签，其余场景（含抓包直达）一律自然语言 | `"请总结最近3小时的错误情况"` |
| `--analyze-action` | ❌ | `Console` / `PcapAnalysis` / `MultiTaskCompare`。缺省按 query-text **自动推断**（含 `compare_task_ids` → MultiTaskCompare；含 `probe_time`+`code` 的 `<structured_json>` → PcapAnalysis；其余 → Console）。显式传时优先 | `MultiTaskCompare` |
| `--task-id` | ⚠️ | `task-[a-z0-9]+`。**除多任务对比场景外一律必传**。抓包跟进型从 `pcap_candidates` 候选项的 `task_id` 字段提取；**多任务对比场景忽略**（任务 ID 全部由 query-text 内 `<structured_json>` 承载） | `task-xxxxxxxx` |
| `--start-time` | ✅ | **毫秒**级 Unix（13 位）。**所有场景一律必传**（含多任务对比；用户未指定时默认 `end-10800000`）。抓包跟进型取 `probe_time` 作为起始时间 | `1776489777000` |
| `--end-time` | ✅ | **毫秒**级 Unix（13 位）。**所有场景一律必传**（含多任务对比；用户未指定时默认 `当前ms`）。抓包跟进型取 `probe_time` 作为截止时间（`start = end = probe_time`） | `1776662577000` |
| `--session-id` | ❌ | 来自上一次 JSON 输出的 `session_id` 字段。**只有**抓包跟进型（5b.1）需要；错误/整体分析、抓包直达型**一律不传** | `17f5753184bed224055354` |
| `--suppress-pcap-candidates` | ❌ | 抑制 `pcap_check.done` 副作用（不追加候选列表到 `.md`、不导出 `_json.md`、JSON 中 `json_file` 为空）。**抓包分析（直达 / 跟进）一律显式带上**，避免报告末尾混入无意义候选。未显式传入时，若命令行带 `--session-id` 或 `--query-text` 含 `<structured_json>` 标签，脚本会自动启用该行为 | — |
| `--output` / `-o` | ❌ | `.md` 结尾；**工作区相对路径**（不得放 `/tmp/`）。缺省 `{task_id}_{report_type}_{YYYYMMDD_HHmmss}.md`（report_type 由 query_text 推断；多任务对比取 payload 的 `main_task_id` 作前缀） | `task-xxx/task-xxx_error_report_20260420_132257.md` |

> ¹ 必填方式：用户没提时间范围 → **所有场景（含多任务对比）** 一律按"最近 3 小时"默认（`end=当前ms`，`start=end-10800000`）；用户没提 `task-id` → **必须先追问**（企微群内提醒 `@机器人` 回复），**禁止**用 `adhoc` 或留空调起脚本。**多任务对比例外**：`--task-id` 不传，任务 ID 全部由 query-text 内 `<structured_json>` 承载，但 `--start-time` / `--end-time` 仍必传（用户指定或默认 3h）。抓包直达型同样适用——哪怕用户原话再自然，也要抽出 / 追问到 `task-id` + 时间点再调。

## 硬规则

### 1. 时间戳必须是毫秒

```bash
# ❌ 10 位秒级
--start-time 1776489777

# ✅ 13 位毫秒级
--start-time 1776489777000
```

常用区间（ms）：1h=`3600000` / 3h=`10800000` / 12h=`43200000` / 24h=`86400000` / 48h=`172800000` / 7d=`604800000`

```bash
END_TIME=$(date +%s)000
START_TIME=$((END_TIME - 10800000))   # 默认 3h
```

### 2. `--query-text` 的三种格式

| 场景 | 格式 | `--task-id` / `--start-time` / `--end-time` | `--analyze-action` | `--session-id` | `--suppress-pcap-candidates` |
|------|------|---|---|---|---|
| 错误 / 整体 / 性能分析 | **自然语言**（按 `query_text_templates.md` 模板） | ✅ 必传三件套 | Console（自动推断） | ❌ 不传 | ❌ 不传（需要候选列表） |
| 多任务对比 | **`<structured_json>`**（`main_task_id` + `compare_task_ids`） | ⚠️ **`--task-id` 不传**；`--start-time` / `--end-time` 必传（用户指定或默认最近 3h） | MultiTaskCompare（自动推断） | ❌ 不传 | ❌ 不传 |
| 抓包直达型（用户对话直接要抓包） | 统一模板格式（`进行抓包分析`） | ✅ 必传三件套（用户指定时间范围时按指定范围；否则从 `probe_time` 推断 ±5min 窗口；均缺失时兜底 3h） | Console（自动推断） | ❌ 不传 | ✅ **建议显式传**（避免报告末尾混入候选） |
| 抓包跟进型（候选列表 → 选序号） | 从 `pcap_candidates` 候选项取 `structured_json` 字段 | ✅ 必传（从候选项提取 `task_id`，`--start-time` = `--end-time` = `probe_time`） | PcapAnalysis（自动推断） | ✅ 必传 | ✅ **建议显式传**（避免报告末尾再出候选） |

**抓包跟进型**示例：

```bash
--query-text "<structured_json>{\"task_id\":\"task-xxxxxxxx\",\"probe_time\":1776489777000,\"code\":\"10970\"}</structured_json>"
```

**多任务对比**示例：

```bash
--query-text '<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>'
```

- 标签严格是 `<structured_json>...</structured_json>`
- JSON 内的 `"` 在 shell 中转义为 `\"`
- `probe_time` 是毫秒数字，不带引号
- 多任务对比不传 `--task-id`，任务 ID 全部由 payload 承载

### 3. `--output` 路径

```bash
--output {task_id}/{task_id}_{report_type}_{YYYYMMDD_HHmmss}.md
```

- `{task_id}` 取命令行 `--task-id`；多任务对比取 payload 的 `main_task_id`
- `{report_type}` = `error_report` / `overall_report` / `performance_report` / `pcap_report` / `multitask_compare_report`
- 执行前 `mkdir -p {task_id}`
- ❌ 禁用 `/tmp/`、`/var/tmp/`、`~/Desktop/` 等非工作区路径

### 4. 互斥规则

- `--session-id` **只**和**抓包跟进型**（`structured_json` payload）配对使用
- **所有场景** `--start-time` / `--end-time` **两个必传**；`--task-id` **除多任务对比外**必传（多任务对比下任务 ID 由 query-text 承载）
- `--suppress-pcap-candidates` 在**所有抓包场景**（直达 / 跟进）都**显式带上**；错误/整体分析**不要**带（否则无法触发候选列表 → Step 5a 也拿不到候选）

## 非法调用（禁止生成）

```bash
# ❌ 秒级时间戳
--start-time 1776489777

# ❌ start > end
--start-time 1776662577000 --end-time 1776489777000

# ❌ 空 query-text
--query-text ""

# ❌ 抓包跟进丢了 structured_json 标签
--query-text '{"task_id":"task-xxx","probe_time":1773905195000,"code":"10970"}'

# ❌ 把自然语言硬塞进 structured_json（直达型场景错误示范）
--query-text "<structured_json>对 task-xxx 抓包</structured_json>"

# ❌ output 非 .md
--output report.pdf

# ❌ 错误/整体/抓包直达/抓包跟进缺 task-id 或时间戳（三件套必须齐）
--query-text "请总结最近3小时的错误情况"
--query-text "对 task-xxx 抓包分析" --task-id task-xxx        # 缺 start/end
--query-text "<structured_json>...</structured_json>" --session-id xxx  # 缺三件套
```

**多任务对比的合法调用**（`--task-id` 省略）：

```bash
--query-text '<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>' \
  --start-time 1773658839444 --end-time 1773745239444
```

## 输出格式

脚本全程静默，最终只输出一行 JSON 到 stdout：

```json
// 成功
{"code": 0, "report": "# 报告正文...", "md_path": "/abs/path/report.md", "session_id": "xxx", "json_file": "/abs/path/json.md", "pcap_candidates": [{...}], "incomplete": false}

// 失败
{"code": 1, "error": "错误信息"}
```

| 字段 | 成功时 | 失败时 | 说明 |
|------|--------|--------|------|
| `code` | `0` | `1` | 结果码 |
| `report` | ✅ | ❌ | 报告正文（已从第一个一级标题截取） |
| `md_path` | ✅ | ❌ | 归档 `.md` 文件路径 |
| `session_id` | ✅ 可能为空 | ❌ | 会话 ID（抓包跟进时需要） |
| `json_file` | ✅ 可能为空 | ❌ | 抓包候选 structured_json 清单文件路径（归档用） |
| `pcap_candidates` | ✅ 可能为空 | ❌ | 抓包候选列表，每项含 `index`/`city`/`operator`/`error_id`/`task_id`/`probe_time`(毫秒时间戳)/`code`/`structured_json`，agent 取 `structured_json` 用于 `--query-text`，取 `task_id`/`probe_time` 用于三件套 |
| `error` | ❌ | ✅ | 错误信息 |
| `incomplete` | ✅ | ❌ | `true` 表示 SSE 流未正常收到 `agent.done`，报告可能不完整 |
