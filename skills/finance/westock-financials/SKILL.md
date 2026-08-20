---
name: westock-financials
description: 围绕公司财务做有观点的分析，统合三大子能力：财报分析（季度业绩 beat/miss 与预期修正）、财报前瞻（发布前预期模型与牛/基准/熊情景）、财务排雷（利润质量与财务粉饰 6 大鉴证模式和红旗清单）。用户问「业绩怎么样/财报点评/利润大增怎么看」默认轻量财报点评；明确问完整财报分析、下季度重点、利润质量、水分、非经常性损益、现金流背离或财务排雷时使用。纯行情/财务表取数转 westock-data，估值贵不贵转 westock-valuation。基于anthropics的financial-services开源skills方法论进行优化。
---

# westock-financials - 财务分析

围绕公司财报、财报发布前预期和利润质量做有观点的深度分析。命中后先确认公司代码与财报发布状态，再进入对应子模块，禁止直接按用户字面跳过路由。

## 适用场景

| 用户这么问（示例） | 路径 |
|---|---|
| "做一份比亚迪上季度的财报分析"、"分析下小米最新业绩"、"英伟达财报 beat 还是 miss" | 财报分析 |
| "宁德下季度财报重点看什么"、"茅台财报前瞻一下"、"英伟达下次财报市场预期多少" | 财报前瞻 |
| "茅台财报有没有水分/利润质量怎么样"、"是不是靠非经常性损益撑的"、"赚的是账面利润但没现金吗" | 财务排雷 |
| "财报出来了，业绩怎么样、有没有水分" | 财报分析；财务排雷 |

边界反例：

| 用户这么问 | 应路由到 |
|---|---|
| "查招行最近4期利润表"、"腾讯现在股价/市盈率多少" | `westock-data` |
| "筛选 PE<15、ROE>15% 的 A 股" | `westock screen condition` |

## 数据来源与停止规则

| 数据类型 | 稳定来源 | 规则 |
|---|---|---|
| 结构化数字、代码定位、行情、财务、估值、评级、公告 / 研报列表元数据 | `westock-data` | 数字只认命令返回，不手算替代、不用网页搜索填充 |
| 公告正文、研报正文、新闻正文、业绩会纪要原文 | `westock-finsearch query "标题或 id 关键词"` | 先用 `westock notice list <code> --type 1` 或 `westock report list <code> --limit 10` 拿标题 / id，再串行查询正文 |

表中 `westock-data` / `westock-finsearch` 等为依赖 Skill 的调用简写；实际执行形态以其 SKILL.md 顶部「调用方式」为准。

关键数据缺失时按路径处理：轻量财报点评至少需要公司代码、目标报告期或最新财报线索、核心财务数字和行情反应；完整 beat/miss 分析才要求一致预期、正式财报发布状态和正文证据；财务排雷才要求 12 期三表和排雷主数据。空结果最多按同一数据需求补查 1 次（换公司代码、报告期或公告关键词）；仍失败则输出可核实部分、缺失数据和无法继续的维度，不把轻量点评升级为完整排雷。

可选或市场不支持维度只可标注省略，不得支撑结论。例如期权隐含波动率、whisper number、港美股弱一致预期、A 股专属风险事件在不可得时标注"无可靠数据源 / 当前市场不支持"，但不能据此推断。

## 意图分流

| 判断条件 | 路径 | 必读 reference |
|---|---|---|
| 用户问“业绩怎么样 / 财报点评 / 利润大增怎么看”，未要求完整报告 | **轻量财报点评** | **无**；按稳定命令集拉核心数字，**不读 reference** |
| 已确认完整财报已发布，用户明确要求 beat/miss、预期修正、完整分析 | 财报分析 | `references/earnings-analysis.md` |
| 尚未发布完整财报，或只有业绩预告 / 快报，用户问下季度、前瞻、重点指标 | 财报前瞻 | `references/earnings-preview.md`；轻量前瞻可不读 |
| 用户问利润质量、水分、非经常性损益、现金流背离、财务粉饰 | 财务排雷 | `references/financial-forensics.md` |
| 用户同时问业绩表现与利润质量 | 财报分析；财务排雷 | 两个 reference 都读 |

路径名必须对应正文同名 `##` 小节；组合问题用多个正文小节标题并列表示。财务排雷可以与财报分析串联；未发布完整财报时禁止做 beat/miss 解读，只能做财报前瞻。用户未明确问“水分 / 排雷 / 造假 / 现金流背离”时，不进入 12 期三表排雷。

## 发布状态前置判断

1. 用户给公司名时，使用 `westock search <名称>` 定位唯一代码（实际执行按上文跨 Skill 替换规则处理）；无法唯一定位时停止并等待用户确认。
2. 已有代码后，先串行检查发布状态：
   - `westock notice list <code> --type 1`：确认是否有目标报告期的正式年报 / 季报 / 中报公告。
   - `westock disclosure <code>`：确认财报披露预约日及业绩快报 / 预告线索。
   - `westock calendar --event financial_report --market hs`：确认未来财报发布的日历事件。
3. 状态判定：
   - 用户只要轻量点评：允许在确认最新财务数字和行情反应后先输出可核实部分，并标注是否为正式财报、快报或预告。
   - 正式财报已发布：进入财报分析；若用户问水分，再叠加财务排雷。
   - 未发布完整财报，或只有预告 / 快报：进入财报前瞻；若使用预告 / 快报，必须标注"未经审计、科目不全、不能做完整 beat/miss"。
   - 发布状态无法确认：轻量路径输出可核实财务 / 行情部分并列缺口；完整路径停止，列出已尝试命令，等待用户提供报告期或公告线索。

## 常用数据访问（统一走 westock-data）

本 Skill **不直接访问任何数据源**，全部通过 `westock-data` CLI。完整命令见 `references/data-mapping.md`。最常用：

| 数据 | 命令 | 主要服务子模块 |
|---|---|---|
| 代码定位 | `westock search <名称>` | 全部 |
| 三大报表多期 | `westock finance <code> --limit 8`（排雷用 `--limit 12`） | 全部 |
| 一致预期（A股） | `westock consensus <code>` | 财报分析、财报前瞻 |
| 财报披露预约日 | `westock disclosure <code>` | 全部（披露日期及业绩快报 / 预告线索） |
| 财报日历 | `westock calendar --event financial_report --market hs` | 财报前瞻、发布状态判断 |
| 实时行情 / 估值 / 股本 | `westock quote <code>` | 全部 |
| 股价对财报反应 | `westock kline <code> --period day --limit 10` | 财报分析、财报前瞻 |
| 机构评级 | `westock rating <code>` | 财报分析、财报前瞻 |
| 研报列表 | `westock report list <code> --limit 10` | 财报分析、财报前瞻 |
| 财报相关公告列表 | `westock notice list <code> --type 1` | 全部 |
| 公告全文 | `westock notice detail <id>` | 全部（id 来自 notice list） |
| 风险事件（A股） | `westock risk <code>` | 财务排雷 |
| 股东结构（A股 / 港股） | `westock shareholder <code>` | 财务排雷（稀释分析） |
| 公司简况 | `westock profile <code>` | 财务排雷（DSO 异常业务背景） |

> 港股 / 美股利润表均用 `westock finance <code> --type income --limit 8`（旧的 --type zhsy 已弃用）；美股一致预期较弱时回退 `westock rating <code>` / `westock report list <code> --limit 10` 并注明，不编造 consensus。港股 / 美股缺字段时最多补查 1 轮，随后输出可核实部分。期权隐含波动率（options-implied move）无法提供，需标注省略。公告正文也可通过 `westock-finsearch query "公告标题或 id"` 搜索获取。

## 轻量财报点评

用户问“业绩怎么样 / 财报出来怎么看 / 利润暴增有没有体现”，但没有要求完整报告、beat/miss 或排雷时，走本路径。

最低采集骨架：

- 已发布或疑似已发布：`westock finance <code> --limit 4` + `westock quote <code>` + `westock notice list <code> --type 1`。
- 未发布或预告阶段：`westock disclosure <code>` + `westock consensus <code>` 或 `westock rating <code>` + `westock report list <code> --limit 5`。
- 股价是否体现：补 `westock kline <code> --period day --limit 10`。

输出要求：

- 先给一句话结论：超预期 / 符合预期 / 低于预期 / 数据不足。
- 列核心数字：营收、归母净利、扣非净利、毛利率 / ROE / 现金流中最相关的 2-4 项。
- 区分正式财报、快报、预告和市场预期；不能把快报 / 预告当正式财报。
- 数据不足时允许输出“可核实部分 + 待确认项”，不要继续寻找等价字段超过 1 轮。

## 财报分析

进入本路径前必须确认完整财报已发布，且用户明确要求 beat/miss、预期修正、完整分析或系统报告；随后读取 `references/earnings-analysis.md`。输出聚焦"什么是新的"：beat/miss 归因、预期修正、投资逻辑影响。

最低采集骨架：`westock finance <code> --limit 8`、`westock consensus <code>`、`westock quote <code>`、`westock kline <code> --period day --limit 10`、`westock notice list <code> --type 1`。公告或研报正文需要标题 / id 时，再用 `westock-finsearch query "标题或 id 关键词"`。

必须给出营收、净利润、扣非、毛利率、指引等项目的实际 vs 一致预期 / 上年同期量化对比。A 股必须区分归母净利与扣非净利；业绩快报 / 预告不能当作正式财报。

## 财报前瞻

进入本路径前必须确认完整财报尚未发布，或用户明确要求发布前预期框架。用户只问“下次财报关注什么”时可走轻量前瞻；用户要求完整前瞻报告时读取 `references/earnings-preview.md`。输出财报日期、市场预期、关注指标、牛 / 基准 / 熊三情景和催化剂清单。

最低采集骨架：`westock disclosure <code>`、`westock calendar --event financial_report --market hs`、`westock consensus <code>`、`westock finance <code> --limit 8`、`westock quote <code>`、`westock kline <code> --period day --limit 10`、`westock report list <code> --limit 10`。

期权隐含波动率和 whisper number 没有可靠数据源时必须标注省略，不额外寻找工具，不编造。

## 财务排雷

只有用户问利润质量、水分、现金流背离、非经常性损益、财务粉饰、造假风险或排雷时进入本路径，并读取 `references/financial-forensics.md`。即使财报已发布，也只在用户明确要求时叠加本路径。

最低采集骨架：`westock finance <code> --fields all --limit 12`、`westock finance <code> --type income --fields all --limit 12`、`westock finance <code> --type balance --fields all --limit 12`、`westock finance <code> --type cashflow --fields all --limit 12`、`westock quote <code>`、`westock shareholder <code>`、`westock risk <code>`、`westock profile <code>`、`westock disclosure <code>`、`westock notice list <code> --type 1`。（排雷需应收/存货/合同负债/无形资产/扣非等明细字段，`westock finance` 命令必带 `--fields all`，默认窄表不含）

必须输出 6 大鉴证模式 × 四级评分表（干净 / 关注 / 存疑 / 红旗）和红旗清单，每项挂财务数字依据。红旗只能表述为"待进一步核查的信号"，不得定性为造假、做空理由或交易建议。

## 并发与批量

公司代码和目标报告期确认后，互不依赖的数据可以同轮并发获取，例如财务报表、行情估值、一致预期、评级、研报列表。依赖前一步返回的代码、公告 id、研报 id、标题或报告期的步骤必须串行。

同一命令支持批量代码时可一次查全；需要逐标题 / id 查询正文时，用 `westock-finsearch query` 一次传入 1-5 组互不依赖关键词。正文返回较大时只提炼支撑结论的事实、日期、标题和 id，不复制全文。

## 交付物自检

通用：
- [ ] 路由前已确认财报发布状态，子模块选择与之匹配。
- [ ] 是否先判断轻量点评、完整分析、前瞻或排雷，避免普通业绩问题默认跑 12 期三表？
- [ ] 所有行情、财务、预期数字来自 `westock-data`；所有正文引用来自 `westock-finsearch query`。
- [ ] 关键数据缺失时已输出可核实部分和缺口，且不用占位符、估算值或 `web_search` 填充。
- [ ] 注明数据来源、报告期、日期范围；公告 / 研报引用标题与 id。
- [ ] 港股标港元 / 美元，美股标美元，禁止对港美股使用人民币符号。

财报分析：
- [ ] 给出营收 / 净利 / 扣非 / 毛利率 / 指引的实际 vs 预期或同比量化对比。
- [ ] A 股区分归母净利与扣非净利；快报 / 预告边界已标注。

财报前瞻：
- [ ] 给出牛 / 基准 / 熊三情景表、关键假设、催化剂清单和披露日期。
- [ ] 期权隐含波动率、whisper number 等不可得维度已标注省略。

财务排雷：
- [ ] 输出 6 大鉴证模式 × 四级评分表和红旗清单。
- [ ] 红旗表述为待进一步核查的信号，非造假定性、做空理由或交易建议。

## 全局规范（必须遵守）

1. **数据真实性（合规底线）**：遵守上文「数据来源与停止规则」；命令不可用/失败时必须立即停止并告知用户，**严禁编造、推算或引用来源不明的行情、财务、催化剂数字**。
2. **量化为先**：所有判断、评级、结论必须有数字支撑。
3. **货币单位**：港股标港元/美元、美股标美元，**禁止对港美股使用人民币符号**。
4. **引用纪律**：统一标注"数据来源：westock-data（腾讯自选股行情数据接口）"，并注明报告期/日期范围；公告/研报引用其标题与 id。
5. **不构成投资建议**：产出为供专业人士复核的研究草稿，不构成证券投资咨询或交易建议；财务排雷的红旗是"值得进一步核查的信号"，非"做空理由"。
6. **A股本地化**：SEC EDGAR→交易所公告；Non-GAAP→扣非净利润；10-K/10-Q→年报/季报。
7. **数据不足强制停止**：`westock-data` 或 `westock-finsearch` 无法返回所需数据时，**禁止用占位符/估算值填充**，必须如实标注「数据不足，无法核实」并停止该维度的推论，等待用户决策。
8. **输出可达性（受众自适应）**：专业用户保留术语与完整量化表；散户提问时用大白话 + 红/黄/绿信号解释，但**数字与风险提示绝不简化**。
9. **输出格式**：用户可见的第一条文本必须是最终结论/报告本身，禁止"数据都齐了""信息收集充分了""现在来整理""数据已收集完毕"等过渡句开头；这类文本即使出现在较早 payload 也视为格式违规。最终输出必须是纯 Markdown，禁止 `<span>`、`<div>` 等原始 HTML 标签；强调颜色或状态时用 Markdown 加粗、表格或 emoji 代替。

## 边界和声明

不要复述方法论；用户要的是结论、依据和不确定性。本 Skill 不做选股筛选、估值重算、持仓诊断、模拟交易或交易建议。需要这些能力时转对应 Skill。

## 重要声明

> 1. 本技能仅基于公开市场数据提供客观研究分析，不构成证券投资咨询服务或交易建议。
> 2. 数据可能存在延迟与口径差异，请以交易所/公司官方披露为准。
> 3. 投资有风险，决策需谨慎。如需专业投资建议，请咨询持牌证券投资顾问机构。

**数据来源**：westock-data（腾讯自选股行情数据接口）

## References

- `references/data-mapping.md`：完整命令清单、市场限制、字段和数据来源边界。
- `references/earnings-analysis.md`：已发布财报的 beat/miss 分析方法论。
- `references/earnings-preview.md`：未发布财报的前瞻模型与情景分析。
- `references/financial-forensics.md`：利润质量与财务粉饰 6 大鉴证模式。