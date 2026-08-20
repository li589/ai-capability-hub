# 模式：earnings-preview（财报前瞻）

> 数据来源与停止规则见 SKILL.md「数据来源与停止规则」。关键数据缺失必须停止并说明已尝试命令。

## 用途

在公司发布季报之前，构建预期模型、牛 / 基准 / 熊情景框架与关注指标。

触发："做一份 XX 财报前瞻"、"XX 财报要关注什么"、"预览 XX 下季度业绩"。

## 数据获取

| 方法论需要 | 稳定命令 |
|---|---|
| 公司与代码 | `westock search <名称>` |
| 是否已有预告 / 快报 | `westock disclosure <code>` |
| 财报日期 / 事件 | `westock calendar --date <YYYY-MM-DD> --event financial_report --market hs`、`westock notice list <code> --type 1` |
| 一致预期 | `westock consensus <code>`；港美股用 `westock rating <code>` 与 `westock report list <code> --limit 10` |
| 历史业绩基线 | `westock finance <code> --limit 8` |
| 近期股价表现 | `westock quote <code>`、`westock kline <code> --period day --limit 10` |
| 历史财报后股价反应 | `westock kline <code> --period day --limit 60` |
| 上季指引 / 业绩会纪要正文 | 先用 `westock report list <code> --limit 10` 取标题 / id，再用 `westock-finsearch query "标题或 id 关键词"` |
| 公告正文 | 先用 `westock notice list <code> --type 1` 取标题 / id，再用 `westock-finsearch query "标题或 id 关键词"` |

## 工作流

### Step 1 - 收集背景

1. 确认公司、代码、报告季度和完整财报尚未发布。
2. 用 `westock disclosure <code>` 检查是否已有业绩预告 / 快报。
3. 用 `westock calendar --date <YYYY-MM-DD> --event financial_report --market hs` 与 `westock notice list <code> --type 1` 找披露日期和公告线索。
4. 公司代码和报告期确认后，可并发拉取 `westock consensus <code>`、`westock finance <code> --limit 8`、`westock quote <code>`、`westock kline <code> --period day --limit 10`、`westock rating <code>`、`westock report list <code> --limit 10`。

### Step 2 - 关键指标框架

财务指标：营收 vs 预期、EPS vs 预期、毛利率 / 营业利润率 / 净利率、自由现金流、前瞻指引 vs 预期。

运营指标按行业选择：
- 科技 / SaaS：ARR、净留存、RPO、客户数。
- 零售：同店销售、客流、客单价。
- 工业：在手订单、订单出货比、量价拆分。
- 金融：净息差、信贷质量、贷款增长、手续费收入。
- 医药：处方 / 患者量、管线进展。

行业归属和主营业务可从 `westock finance <code> --limit 8`、研报列表和公告正文中交叉确认；拿不到可靠数据时标注省略，不支撑结论。

### Step 3 - 情景分析

构建 3 情景及股价含义：

| 情景 | 营收 | EPS | 关键驱动 | 股价反应 |
|---|---|---|---|---|
| 牛 |  |  |  |  |
| 基准 |  |  |  |  |
| 熊 |  |  |  |  |

每个情景说明运营上需发生什么、管理层何种评论会释放该信号、历史上类似业绩时股价如何反应。历史反应用 `westock kline <code> --period day --limit 60` 对齐披露日前后。

### Step 4 - 催化剂清单

列出 3-5 个决定股价反应的要素：指标 vs 一致预期、为何重要、买方期望听到的指引、叙事转变或重大事项。

### Step 5 - 输出

公司 + 季度 + 财报日期；一致预期表；按重要性排序的关注指标；牛 / 基准 / 熊情景表；催化剂清单；近期股价表现和不确定性。

## 规范

- 一致预期会变，必须标注 `westock consensus <code>` 的拉取日期。
- 期权隐含波动幅度没有可靠数据源时，标注"无期权隐含数据"，不得编造。
- whisper number 没有可靠来源时，标注来源缺失，不纳入结论。
- 只有业绩预告 / 快报时必须标注"未经审计、科目不全"，不得做完整 beat/miss。

## A 股本地化

- A 股一致预期优先使用 `westock consensus <code>`；港美股改用评级 / 研报目标价做定性框架。
- 财报日期用 `westock calendar --date <YYYY-MM-DD> --event financial_report --market hs` 与 `westock notice list <code> --type 1`，不使用 IR 日历口径。
