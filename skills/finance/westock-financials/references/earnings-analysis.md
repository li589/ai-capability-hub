# 模式：earnings-analysis（财报分析）

> 数据来源与停止规则见 SKILL.md「数据来源与停止规则」。关键数据缺失必须停止并说明已尝试命令。

## 用途

为数据可由 `westock-data` / `westock-finsearch` 获取且有足够历史口径的公司撰写季度业绩更新，聚焦"什么是新的"：beat/miss、预期修正、投资逻辑影响。

- 篇幅：核心 1-3 张汇总表，不做全量三表罗列。
- 时效：财报发布后尽快，聚焦新信息，不重复公司背景。
- 触发："做一份 XX 的财报分析 / 季度更新"、"分析 XX 季度业绩"、"XX Q3 业绩点评"。

不适用：未发布完整财报、只要数字查询、只要一句话快讯。

## 数据获取

| 方法论需要 | 稳定命令 |
|---|---|
| 定位公司 | `westock search <名称>` |
| 确认正式财报已发布 | `westock notice list <code> --type 1` |
| 本期 vs 历史业绩 | `westock finance <code> --limit 8` |
| 利润表细项 | `westock finance <code> --type income --limit 8`（各市场统一，旧值 lrb/zhsy 已弃用） |
| beat/miss 基准 | `westock consensus <code>`；港美股弱或空时用 `westock rating <code>` 与 `westock report list <code> --limit 10` 做定性基准 |
| 业绩预告 / 快报边界 | `westock disclosure <code>` |
| 估值与股本 | `westock quote <code>` |
| 股价对财报反应 | `westock kline <code> --period day --limit 10` |
| 公告 / 研报正文 | `westock-finsearch query "标题或 id 关键词"` |

## 工作流

### Phase 1 - 数据采集

1. 用 `westock search <名称>` 定位代码；已有代码则复核市场和公司名。
2. 用 `westock notice list <code> --type 1` 与 `westock disclosure <code>` 确认目标报告期是否为正式财报，避免把预告 / 快报当完整财报。
3. 公司代码和报告期确认后，可并发拉取 `westock finance <code> --limit 8`、`westock consensus <code>`、`westock quote <code>`、`westock kline <code> --period day --limit 10`、`westock rating <code>`、`westock report list <code> --limit 10`。
4. 需要管理层指引、公告原文或业绩会纪要时，先从列表命令取标题 / id，再串行执行 `westock-finsearch query "标题或 id 关键词"`。

### Phase 2 - 分析

- Beat/Miss：逐项对比实际 vs 一致预期，量化偏差并解释原因；A 股若无 consensus，可用预告区间或研报基准并注明口径。
- 分部 / 结构：拆解营收结构、毛利率、营业利润率、净利率的环比和同比变化。
- 指引：从可追溯公告、研报或业绩会纪要中提取管理层指引，与市场预期对比。
- 更新预期：给出旧值 vs 新值、变化幅度和理由，不编造 forward 估计。

### Phase 3 - 关键图表

如当前环境已提供绘图能力，可基于已获取数据生成季度营收、EPS、利润率、beat/miss 汇总、预期修正和估值图表；否则用表格替代，不额外寻找工具。

### Phase 4 - 报告结构

1. 业绩摘要：一句话定调 + 核心量化结论。
2. beat/miss 归因表：实际、预期 / 同比基准、差值、原因。
3. 关键指标与指引：分部、利润率、现金流或管理层指引。
4. 投资逻辑更新：本期结果对原 thesis 的影响。
5. 数据与不确定性：来源、报告期、缺失项和边界。

## 输出规范

- 1-3 张汇总表，量化为先。
- beat/miss 必须标注预期来源与日期。
- 末尾附"数据来源：westock-data（腾讯自选股行情数据接口）；非结构化内容：westock-finsearch"，注明报告期范围与引用的公告 / 研报 id。

## A 股本地化

- 一致预期优先使用 `westock consensus <code>`；港美股弱时改用评级 / 研报目标价并注明。
- 披露源使用交易所公告标题 / id，不使用 SEC 10-Q / earnings release 口径。
- GAAP vs 调整后在 A 股中对应净利润 vs 扣非归母净利润，需结合 `westock finance <code> --type income --limit 8` 与 `westock disclosure <code>`。

## 衔接

- 本期触发利润质量疑虑时，叠加财务排雷。
- 用户需要重算估值时，转 `westock-valuation`，本路径只说明本期业绩对估值输入的影响。
