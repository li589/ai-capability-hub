# branch_pcap — 抓包（pcap）分支规范

进入本文档的两种入口：

| 入口 | 触发 | `--query-text` 格式 | `--task-id` / `--start-time` / `--end-time` | `--session-id` |
|------|------|---------------------|---|----------------|
| **A 跟进型** | 主分析报告含 `🔍 抓包分析候选列表`，用户回复序号 | 从 `pcap_candidates` 候选项取 `structured_json` 字段 | ✅ **三件套必传**：`task-id` 从候选项 `task_id` 字段取，`start=end=probe_time` | ✅ **必传**（主分析 JSON 的 `session_id` 字段） |
| **B 直达型** | 用户自然语言要抓包 | 统一模板格式（`进行抓包分析`） | ✅ **三件套必传**：`task-id` 从原话抽取，`probe_time` 推断出毫秒戳后用作时间锚点（`start=probe_time-5min`，`end=probe_time+5min`，或按用户指定窗口） | ❌ 不传 |

> **入口 A（跟进型）原则**：payload 原样透传，标签保留，`probe_time` 不改；同时从候选项中提取 `task_id` 和 `probe_time` 补齐三件套（`--task-id` / `--start-time` / `--end-time`），**两入口三件套均必传**（见 5b.2 示例）。
>
> **入口 B（直达型）原则**：`--query-text` 使用统一模板格式（`进行抓包分析` 或 `对{城市}{运营商}进行抓包分析`），`--task-id` / `--start-time` / `--end-time` **三件套必须齐**——这是本版本的硬约束，和错误/整体/性能分析一致。缺 `task-id` 必须先追问；缺明确拨测时间点时以"最近 3 小时"窗口兜底。

承接 SKILL.md 的 Step 3 / Step 4 同步执行机制，不重复。

---

## Step 5a — 主动提醒候选列表（仅入口 A）

主分析脚本成功返回（JSON `code=0`）且 `pcap_candidates` 非空时，在完整报告之后追加**独立一条消息**：

```
📋 本次分析检测到以下抓包分析候选项，可选择一项进行深入抓包分析：

  1. 城市: 慕尼黑 | 运营商: Germany_COLT | 错误码: 600 | 任务ID: task-xxx | 拨测时间: 2026-03-17 07:06:35 | 拨测点: xxx
  2. ...

请回复序号（如 `1`）选择要分析的项，或回复"跳过"结束本轮。
💡 企微群内请 **@机器人** 回复。
```

候选项优先从 JSON 的 `pcap_candidates` 数组取，每项含 `index`/`city`/`operator`/`error_id`/`task_id`/`probe_time`(毫秒时间戳)/`code`/`structured_json`，按 `index` 排序列出即可。若 `pcap_candidates` 为空或不可用，回退用 `awk '/🔍 抓包分析候选列表/,0' "<md_path>"` 从报告文件中提取（`md_path` 取自 JSON）。

---

## Step 5b — 调用 pcap 脚本

### 5b.1 按序号读 payload（入口 A）

用户回复序号 `N` 后，**必须**取现成 payload，**禁止**自行拼 JSON（易在毫秒戳、字段顺序、转义上出错）：

**优先**从 JSON 的 `pcap_candidates` 数组取：
- 找 `index == N` 的项，取其 `structured_json` 字段值

**回退**从 `json_file` 文件读取（`pcap_candidates` 为空或不可用时）：
```bash
JSON_FILE=<JSON 输出的 json_file 路径>
PAYLOAD=$(awk -v n="$N" '
  $0 ~ "^## "n"\\. " {grab=1; next}
  grab && /^## [0-9]+\./ {grab=0}
  grab && /<structured_json>/ {print; exit}
' "$JSON_FILE")
```

取到后：
- **原样**作为 `--query-text` 传入（标签 `<structured_json>...</structured_json>` 完整保留，`probe_time` 不改）
- 同时从候选项提取 `task_id` 和 `probe_time`，补齐三件套：`--task-id` = 候选项 `task_id`，`--start-time` = `--end-time` = `probe_time`
- 文本描述（如"第二项"）先转数字
- 两种方式都找不到对应候选 → 若用户意图实为入口 B，按 B 处理；否则提示先跑一次带 pcap 意图的分析

### 5b.1-bis query-text 格式（入口 B）

**`--query-text` 原则：使用统一模板格式**。格式为 `进行抓包分析` 或 `对{城市}{运营商}进行抓包分析`（见 `query_text_templates.md`），**禁止**把自然语言塞进 `<structured_json>` 标签（标签一旦出现，后端按严格结构解析，字段对不上直接失败；标签只在入口 A 用）。

**命令行参数原则：三件套必传**。`--task-id` / `--start-time` / `--end-time` 和错误/整体/性能分析一样必须齐全：

- `--task-id`：从用户原话抽取（`task-[a-z0-9]+`）。原话里没写 → **先追问用户**（企微群提醒 `@机器人`），**不要**调脚本。
- 时间锚点：原话含明确拨测时间（如 "2026-03-17 07:06:35" / "10 分钟前" / "刚才那次"）→ 解析为毫秒 `probe_time`，取 `start = probe_time - 5*60*1000`、`end = probe_time + 5*60*1000` 作为窗口。
- 时间锚点缺失 → 兜底按 "最近 3 小时"（`end = 当前ms`，`start = end - 10800000`），不追问。

示例：

```bash
# 无城市运营商
QUERY_TEXT="进行抓包分析"
TASK_ID="task-muo4gxzs"
PROBE_MS=1773905195000                  # 2026-03-17 07:06:35 → ms
START_MS=$((PROBE_MS - 300000))
END_MS=$((PROBE_MS + 300000))

# 含城市运营商
QUERY_TEXT="对北京电信进行抓包分析"
TASK_ID="task-xxx"
PROBE_MS=$(( $(date +%s)000 - 600000 ))
START_MS=$((PROBE_MS - 300000))
END_MS=$((PROBE_MS + 300000))

# 原话彻底没时间点 → 兜底 3h 窗口
QUERY_TEXT="进行抓包分析"
TASK_ID="task-xxx"
END_MS=$(date +%s)000
START_MS=$((END_MS - 10800000))
```

### 5b.2 启动脚本（两入口参数传递不同）

- `--output` 使用 `pcap_report` 类型路径
- **两入口都显式带** `--suppress-pcap-candidates`（抓包分析场景禁止再在报告末尾追加候选列表；未带时脚本也会自动识别，但显式传更稳妥）
- 入口 A：`<structured_json>` payload + `--session-id` + `--task-id` / `--start-time` / `--end-time` **三件套必传**（从候选项提取）
- 入口 B：`--query-text`（统一模板格式）+ `--task-id` / `--start-time` / `--end-time` **三件套必传**，**不传** `--session-id`

```bash
# 入口 A：structured_json + --session-id + 三件套（从候选项提取）
RESULT=$(python3 ${SKILL_DIR}/scripts/cat_network_quality_analysis.py \
  --query-text "$PAYLOAD" \
  --task-id "$TASK_ID" \
  --start-time "$START_MS" \
  --end-time "$END_MS" \
  --session-id "<session-id-from-json-output>" \
  --suppress-pcap-candidates \
  --output task-xxx/task-xxx_pcap_report_20260319_120000.md)
echo "$RESULT"

# 入口 B：自然语言 + task-id + 时间窗口（不带 --session-id）
RESULT=$(python3 ${SKILL_DIR}/scripts/cat_network_quality_analysis.py \
  --query-text "$QUERY_TEXT" \
  --task-id "$TASK_ID" \
  --start-time "$START_MS" \
  --end-time "$END_MS" \
  --suppress-pcap-candidates \
  --output "$TASK_ID/${TASK_ID}_pcap_report_$(date +%Y%m%d_%H%M%S).md")
echo "$RESULT"
```

启动后重走 SKILL.md **Step 4 交付**（解析 JSON 的 `code` 字段判定成功/失败）。全程只在成功/失败时发声，不提"已进入抓包分析"。

pcap 报告脚本成功返回（JSON `code=0`）时：

1. **立刻**把 JSON 的 `report` 字段内容作为**独立一条消息**回复给用户。
2. 流程结束。
