---
name: customization-data-export
description: 数据导出与下载。当用户要导出业务数据、生成 Excel/CSV、对数据做排名/求和/统计/分组并出文件时使用。流程：调数据分析 MCP 取数 → 立即写本地 raw.csv → 跑 scripts/data_export.py 聚合 → 生成 时间-描述.xlsx 到本地 → 回路径+Top10 摘要。全程只回小摘要，不把明细打回上下文。不处理纯查询/直播复盘/考试分析。
category: 数据分析
version: 0.1.1
author: xiaoe workbuddy 对接人
---

# 数据导出与下载

本 skill 给 workbuddy 的 AI 提供"把业务数据导出成可下载文件"的一致做法。前提：workbuddy 客户端已连接数据分析类 MCP 工具（agent-gateway-mcp 的 `data_analysis_*` 系列）。

只处理"导出/分析 + 生成文件"场景。不处理纯查询回答（直接调 MCP 查询接口即可）、不处理直播复盘报告、不处理考试分析等不涉及导出文件的场景；遇到这些请换用对应能力。

## 硬规则（先读，不可违反）

1. **导出 = 生成可下载文件 + 回绝对路径**。用户说"导出/下载/出 Excel/出表"时，必须生成一个本地文件并把绝对路径回给用户——**不要只在聊天里甩个 markdown 表就完事**。
2. **上下文纪律（本 skill 存在的核心理由）**：MCP 返回的 `data.list`、整页接口响应、原始明细行**一律不准打回回复正文**。拿到数据后**立即写本地 `raw.csv`**（一次性写入），回复里只回小摘要 JSON（总行数、Top10 预览、文件名、本地路径）。
3. **翻页要克制（关键）**：MCP 每翻一页，这页的**传参和返回的 `data.list` 都会留在对话上下文里**（上下文是追加式的，写本地文件不会把它们从历史里删掉）。所以**只翻很少几页**（约 1–5 页内）；翻页多了必然撑爆上下文。终止条件：某页 `list` 为空数组、或某页返回条数 < `page_size` 时停；接口无 `total` 字段时**禁止用 `total` 判断总页数**。拿到每页后立即追加写本地 `raw.csv`——这**不是**为了把明细"移出上下文"（移不出去），而是避免你在回复正文里再复述一遍明细造成双倍占用。
4. **数据量边界**：本 skill 面向小到中等数据量（能在上下文走一个来回不爆，约数千行以内）。判断数据量可能过大（单页很大、或翻页数过多）时，**主动提示用户缩小范围**（缩短时间范围、收窄业务维度、分批导出），**不要硬撑上下文**。超大范围明细导出暂不支持，明说。
5. **只读**：本 skill 只读取数 + 分析 + 生成文件，不做任何写入/删除/发布/改价等业务变更。
6. **不编造**：字段、枚举、响应结构、错误原因一律以 MCP 返回为准；失败引用返回的 `code`/`msg`，不猜。
7. **不碰凭证**：本 skill 不接触 Cookie/Token/`app_id` 等任何凭证——取数由服务端 MCP 侧处理（`app_id` 由 session 派生注入 header，不入 MCP input）。脚本/回复里禁止出现凭证明文。

## 流程

### 第一步：取数（调 MCP，立即落盘）

调 workbuddy 已连接的数据分析 MCP 取数。**不确定 domain/action 时先调 `data_analysis_series_course_list_data_apis` 拿 catalog**，再调 `data_analysis_series_course_query_data` 按 `domain`+`action` 取数；用户要特定数据时选对应域 tool（live / course_learning / clue / member_catalog / playback 系列）。各 tool 的输入以 catalog 和 tool 自身描述为准，**勿凭经验写死字段**。

拿到 `data.list` 后立即写本地 `./data-export-output/raw.csv`（utf-8-sig，兼容 Excel 中文）。翻页时每页追加写入。写完只回 `{"total_rows": N}`，不复述明细。

### 第二步：处理（跑 data_export.py）

读 `raw.csv`，按用户意图做聚合（分组/求和/排名/统计/求差）。优先调本 skill 自带脚本：

```bash
python3 scripts/data_export.py \
  --input ./data-export-output/raw.csv \
  --recipe ./data-export-output/recipe.json \
  --out ./data-export-output \
  --format xlsx \        # 或 csv，默认 xlsx
  --desc "学习统计Top10"  # 中文描述，用于文件名
```

`recipe.json` 声明式，举例：

```json
{
  "group_by": ["resource_id", "resource_name"],
  "rename": {"resource_id": "资源ID", "resource_name": "资源名称"},
  "agg": [
    {"out_field": "学习次数", "func": "sum", "field": "view_count"},
    {"out_field": "学习人数", "func": "nunique", "field": "user_id"}
  ],
  "sort": {"by": "学习次数", "asc": false},
  "rank": true,
  "rank_field": "排名"
}
```

支持 `func`：`sum` / `count` / `mean` / `nunique` / `max` / `min`。输出列名用 `out_field`（中文）。脚本产出 `<时间>-<desc>.xlsx`（默认 xlsx），stdout 回 `{"total":N,"top10":[...],"file":"<绝对路径>"}`。

**recipe 覆盖不到的复杂场景**（如求差/本期 vs 上期增长/自定义逻辑）：用 Bash 跑自写 Python，但守同样规则——只回小摘要 JSON、输出列名中文、文件写本地输出目录、无副作用。

### 第三步：回复用户

- 用简洁表格展示 Top10 预览（中文列名）。
- 说明总记录数、涉及业务范围、聚合口径。
- 给出本地文件的**绝对路径**作为下载入口。
- 不展示原始 JSON、请求头、Cookie、内部接口地址。
- 数据为空时说"所选范围在当前条件下没有数据"，不编造。

## 约定

- **输出目录**：默认 `./data-export-output/`（跨平台用 `pathlib`），用户指定则用用户的。
- **文件名**：`时间-描述.xlsx` 或 `.csv`，时间用脚本内 `datetime.now().strftime("%Y%m%d%H%M%S")`；描述按用户意图简短中文命名。原始落盘文件用 `raw.csv`。不要用 `result_xxx.xlsx` 这类无语义名。
- **列名**：输出文件列名一律中文（面向商家）。计算用原始字段、输出前 rename 改中文。
- **格式**：用户要 CSV 就 `csv`，要 Excel 就 `xlsx`，没明说默认 `xlsx`。
- **stdout**：脚本/命令只打印 JSON 摘要（`json.dumps(..., ensure_ascii=False)`），异常打 `{"error":"..."}` 退出码非 0。

## 依赖

- Python 3 + `pandas` + `openpyxl`。`scripts/data_export.py` 启动时检测依赖，缺失则 `pip install --user pandas openpyxl`，失败面向用户说明依赖不可用，**不要静默继续**。

## 边界与不处理

- 大表导出（撑爆上下文）不支持，提示缩小范围；超大范围明细导出留待未来服务端 export MCP。
- 取数口径以 MCP catalog / tool 描述为准，本 skill 不绑定具体 domain/action。
- 纯查询（不需要文件）直接调 MCP 查询接口，不走本 skill。
