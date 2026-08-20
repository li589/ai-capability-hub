# Query Text 模板库

`--query-text` 的推荐模板和反模式。**AI 必须套模板，不要自由发挥**（自由文本返回质量不稳定）。

> 意图识别已在 SKILL.md §2 说明；本文档只管"意图确定后，text 怎么写"。
>
> ⚠️ **多任务对比例外**：该场景不使用自然语言模板，`--query-text` 必须构造为 `<structured_json>` 格式（见[模板 5](#模板-5--多任务对比multitask_compare_report)）。

## 模板格式

所有自然语言分析场景统一格式：

```
进行{分析类型}分析
```

若用户指定了城市和运营商，则在前面补充：

```
对{城市A}{运营商A}、{城市B}{运营商B}进行{分析类型}分析
```

| 分析类型 | 对应 query-text 示例 |
|---------|---------------------|
| 错误分析 | `进行错误分析` |
| 整体分析 | `进行整体分析` |
| 性能分析 | `进行性能分析` |
| 抓包分析 | `进行抓包分析` |
| 多任务对比 | **不使用自然语言模板**，见[模板 5](#模板-5--多任务对比multitask_compare_report) |

**城市运营商组合示例**：

```
# 单组
对北京电信进行错误分析

# 多组
对北京电信、上海联通、深圳移动进行性能分析
```

> ⚠️ **query-text 中禁止出现时间描述和任务 ID**：时间信息一律通过 `--start-time` / `--end-time` 毫秒时间戳传递，任务 ID 通过 `--task-id` 传递，query-text 中**不要**写"最近 N 小时"、"从 X 到 Y"、`task-xxx` 等内容。仅允许出现城市运营商组合和分析类型。

## 模板 4 · 抓包分析（pcap_report）

两种入口，格式不同：

### 4-A 跟进型（候选列表 → 选序号）

从 `JsonFile` 按序号读取现成 payload，**原样**传入，并**必须**带 `--session-id` **和三件套**：

```bash
--query-text "<structured_json>{\"task_id\":\"task-xxxxxxxx\",\"probe_time\":1776489777000,\"code\":\"10970\"}</structured_json>"
  --task-id task-xxxxxxxx --start-time 1776489777000 --end-time 1776489777000
  --session-id "17f57xxxxxxxxxxxxxxxx5b224055354"
```

- 标签不可省、不可替换
- `probe_time` 毫秒数字，不带引号
- JSON 内部 `"` 在 shell 中转义为 `\"`
- `--task-id` 从候选项的 `task_id` 字段取，`--start-time` / `--end-time` 均设为 `probe_time`

> ⚙️ 脚本对含 `probe_time` + `code` 的 `<structured_json>` 自动推断 `AnalyzeAction=PcapAnalysis`，无需显式传 `--analyze-action`。

### 4-B 直达型（用户对话要抓包）

`--query-text` 使用统一模板格式（同上），不透传用户原话；命令行**必须**补齐 `--task-id` / `--start-time` / `--end-time` 三件套：

- `--task-id` 从原话抽取；原话没写 → **必须先追问**，**不要**直接调脚本
- 时间窗口：原话含明确时间点（"刚才"、"10 分钟前"、"2026-03-17 07:06:35"）→ 解析为毫秒 `probe_time`，`start = probe_time - 5min`、`end = probe_time + 5min`；没时间点 → 兜底 "最近 3 小时"
- 命令行**不带** `--session-id`

```bash
# ✅ 无城市运营商
--query-text "进行抓包分析" \
  --task-id task-xxxxxxxx --start-time 1773904895000 --end-time 1773905495000

# ✅ 含城市运营商
--query-text "对北京电信进行抓包分析" \
  --task-id task-xxx --start-time <probe-5min ms> --end-time <probe+5min ms>

# ❌ 原话完全没提 task-id，不能拍脑袋给 adhoc
--query-text "进行抓包分析"         # 先追问 task-id
```

## 模板 5 · 多任务对比（multitask_compare_report）

**触发条件**：用户要求做任务对比（对比/比较/多任务对比）。AnalyzeAction 为 `MultiTaskCompare`。用户给出的 task ID 可以是多个、1 个或 0 个——按「主次判定流程」补齐主任务与对比任务后再发起分析。

`--query-text` 必须构造为 `<structured_json>` 格式（不是自然语言）：

```text
<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>
```

- `main_task_id`：**主任务**（对比基准）
- `compare_task_ids`：**对比任务**列表（数组，至少 1 个、**最多 5 个**）

**主次判定流程**（按用户给出的 task ID 数量分情况）：

1. **用户给出多个 task ID**：用户明确指定主任务 → `main_task_id` = 用户指定，其余进 `compare_task_ids`；**用户没说主次** → **先追问**，让用户选主任务，回答后所选设为 `main_task_id`，其余进 `compare_task_ids`
2. **用户只给出 1 个 task ID** → **默认该任务为主任务**（`main_task_id`），**追问用户要拿这个任务和哪些任务对比**（`compare_task_ids`）
3. **用户没给任何 task ID** → **追问用户**想以哪个任务为主（`main_task_id`）、和哪些任务对比（`compare_task_ids`）

> 🔔 必须拿到**至少 1 个主任务 + 1 个对比任务**才发起 MultiTaskCompare 分析；信息不全时持续追问。

> ⚠️ **数量上限**：最多 **1 个主任务 + 5 个对比任务**。**对比任务超过 5 个** → **告知用户超限并请其重新选择**（减少对比任务或分多轮对比），**不发起分析**。

**命令行**：

```bash
--query-text '<structured_json>{"main_task_id":"task-aaaabbbb","compare_task_ids":["task-aaaa1111","task-bbbb2222"]}</structured_json>' \
  --start-time <开始ms> --end-time <结束ms>
```

- **不传** `--task-id`（脚本对 MultiTaskCompare 自动跳过 TaskID）
- `--start-time` / `--end-time` **必传**，取值规则与主流程一致：**用户指定时间范围时按指定范围**，**未指定时默认最近 3 小时**（`end=当前ms`，`start=end-10800000`）
- 脚本按 query-text 自动推断 `AnalyzeAction=MultiTaskCompare`，也可显式传 `--analyze-action MultiTaskCompare`
- `--output` 建议以 `main_task_id` 为前缀：`task-aaaabbbb/task-aaaabbbb_multitask_compare_report_<时间戳>.md`

**反模式**：

```bash
# ❌ 用自然语言，不带 structured_json
--query-text "对比 task-a 和 task-b"

# ❌ 多任务对比传了 --task-id（应省略）
--query-text '<structured_json>{"main_task_id":"task-a","compare_task_ids":["task-b"]}</structured_json>' \
  --task-id task-a --start-time 1 --end-time 2

# ❌ 没有主任务字段
--query-text '<structured_json>{"task_ids":["task-a","task-b"]}</structured_json>'

# ✅ 正确
--query-text '<structured_json>{"main_task_id":"task-a","compare_task_ids":["task-b","task-c"]}</structured_json>' \
  --start-time <开始ms> --end-time <结束ms>   # 用户未指定时间范围时默认最近 3h
```

## 反模式（❌ 禁止）

### ❌ 查询太短

```bash
--query-text "错误"
--query-text "分析"
```

返回结果会非常笼统。

### ❌ text 里包含任务 ID 或时间描述

任务 ID 和时间已通过 `--task-id` / `--start-time` / `--end-time` 传了，**不要**在 text 里再写任务 ID 或任何时间描述：

```bash
# ❌ 重复 task-id 和时间戳
--query-text "分析 task-xxxxxxxx 从 1776489777000 到 1776662577000 的错误" \
  --task-id task-xxxxxxxx --start-time 1776489777000 --end-time 1776662577000

# ❌ 包含时间描述（无论相对还是绝对）
--query-text "请总结分析最近48小时的错误情况" \
  --task-id task-xxxxxxxx --start-time <48h前ms> --end-time <当前ms>

--query-text "请总结分析从2026-07-21 11:00:00到2026-07-21 12:00:00的错误情况" \
  --task-id task-xxxxxxxx --start-time 1773696000000 --end-time 1773699600000

# ✅ 仅分析类型 + 可选城市运营商
--query-text "进行错误分析" \
  --task-id task-xxxxxxxx --start-time <开始ms> --end-time <结束ms>

--query-text "对北京电信进行错误分析" \
  --task-id task-xxxxxxxx --start-time <开始ms> --end-time <结束ms>
```

### ❌ 抓包跟进丢 `<structured_json>` 标签、或把自然语言塞进标签

```bash
# ❌ 跟进型无标签
--query-text '{"task_id":"task-xxx","probe_time":1773905195000,"code":"10970"}'

# ❌ 标签名错
--query-text "<json>{...}</json>"
--query-text "<pcap>{...}</pcap>"

# ❌ 直达型把自然语言塞进标签
--query-text "<structured_json>进行抓包分析</structured_json>"

# ❌ 多任务对比把自然语言塞进标签
--query-text "<structured_json>对比 task-a 和 task-b</structured_json>"

# ✅ 跟进型：从 JsonFile 按序号读，原样传
--query-text "<structured_json>{\"task_id\":\"task-xxx\",\"probe_time\":1773905195000,\"code\":\"10970\"}</structured_json>"

# ✅ 多任务对比：严格按 main_task_id + compare_task_ids 结构
--query-text '<structured_json>{"main_task_id":"task-a","compare_task_ids":["task-b","task-c"]}</structured_json>'

# ✅ 直达型：套统一模板
--query-text "进行抓包分析"
```

### ❌ 把用户的口语化原话当 query-text

主分析要套模板。口语化原话会让返回内容缺结构：

```
用户说："分析一下 task-xxxxxxxx 近两天的报错"
```

```bash
# ❌ 直译
--query-text "分析一下 task-xxxxxxxx 近两天的报错"

# ✅ 套模板（不含任务 ID 和时间描述）
--query-text "进行错误分析" \
  --task-id task-xxxxxxxx --start-time <48h前ms> --end-time <当前ms>
```

> 💡 **注意**：**抓包两入口（4-A / 4-B）** 均使用统一模板格式，且命令行参数都必须补齐 `--task-id` / `--start-time` / `--end-time` 三件套（见 4-A / 4-B 小节）。
