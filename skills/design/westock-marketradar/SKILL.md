---
name: westock-marketradar
description: A股盘面微观结构画像，分两个模块——资金分析（主力资金/龙虎榜/两融/筹码/北向五维资金面温度计）+ 事件雷达（解禁/质押/增发/ST/业绩预告等临近事件按影响度排时间轴）。回答"现在是谁在买卖、临近有没有利空"。当用户要"资金面怎么样/主力还是游资在买/筹码集中度高吗/有没有解禁质押增发风险/近期有什么事件"时命中。全市场资金排行转 westock screen ranking，结构化明细转 westock-data。基于 cc-equity-research开源社区skills方法论进行优化。
---

# 盘面雷达（westock-marketradar）

A 股独有的盘面微观结构画像，回答“**现在是谁在买卖 + 临近有没有利空**”。本 Skill 分两个模块：**资金分析**（主力资金 / 龙虎榜 / 两融 / 筹码 / 北向标的池）和 **事件雷达**（解禁 / 质押 / 增发 / ST / 诉讼 / 业绩披露等临近事件）。

数据访问统一走 `westock-data`，覆盖 A 股 / 港股 / 美股；本 Skill 的完整微观结构分析能力仅适用于 A 股，港美股按“适用范围与降级分支”处理。

## 1. 数据来源强制规范

| 数据类型 | 唯一允许的来源 | 禁止行为 |
|---|---|---|
| 结构化数据（行情、资金流、龙虎榜、两融、筹码、事件标签、公告列表等） | `westock-data` | 禁止使用 `web_search` / HTTP 直连 / 编造 / 推算 |
| 非结构化数据（公告原文、新闻、研报原文、事件描述） | `westock-finsearch query` | 禁止使用 `web_search` / 引用来源不明的片段 |

表中 `westock-data` / `westock-finsearch` 等为依赖 Skill 的调用简写；实际执行形态以其 SKILL.md 顶部「调用方式」为准。

当 `westock-data` 或 `westock-finsearch query` 无法返回所需数据时，最多按原意补查 1 次（如扩大日期范围或缩窄事件类型）；仍失败则立即停止当前分析步骤。不得用占位符、估算值、外部搜索或训练数据填充。必须明确告知用户缺失哪条数据、已尝试哪个命令或查询、为什么无法继续，并等待用户决定是否降低分析深度、更换标的，或接受“数据不足，无法给出结论”。

**`web_search` 在本 Skill 内永久禁用。** 上表为唯一允许的数据分层；正文与 catalyst 不得引用来源不明的片段。

## 2. 触发场景与模块路由

| 用户这么问（示例） | 路由到模块 |
|---|---|
| “宁德今天主力资金净流入多少” | 单指标查询，转 `westock fund flow <code>` |
| “宁德最近资金面怎么样” | 资金分析（简版雷达） |
| “宁德最近资金面怎么样，是主力还是游资在买” | 资金分析（简版雷达，可补龙虎榜） |
| “东财筹码集中度高吗、套牢盘多不多” | 资金分析（筹码结构） |
| “立讯近期有没有解禁 / 质押 / 增发的风险” | 事件雷达 |
| “宁德最近资金面如何，临近有没有利空” | 资金分析 + 事件雷达（组合） |
| “做一份完整盘面微观结构画像 / 雷达报告” | 完整画像 |

**边界反例（不要命中本 Skill）**：

| 用户这么问 | 应路由到 |
|---|---|
| “只给我宁德最近 5 日主力资金流水表，不要分析” | `westock-data`（纯结构化明细：`westock fund flow <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD>`） |
| “筛选 PE<15、ROE>15% 的 A 股” | `westock screen condition`（纯条件选股） |

## 3. 适用范围与降级分支

| 市场 | 执行方式 |
|---|---|
| A 股 | 按用户意图选择单指标查询、简版雷达或完整画像；默认不进入完整画像。 |
| 港股 | 先说明本模块为 A 股微观结构设计，`westock chip` / `westock lhb` / `westock fund margin` / `westock connect` 不适用；仅使用 `westock fund flow <code>`（资金流向）、`westock fund short <code>`（卖空 / 空头）、`westock fund south-holding <code>`（南下持仓）等有限资金 / 公告维度，并按港元 / 美元标注。 |
| 美股 | 先说明本模块为 A 股微观结构设计，A 股特有微观结构命令不适用；仅使用 `westock fund short <code>` 等有限卖空 / 公告维度，并按美元标注。 |

## 4. 执行深度

| 深度 | 触发依据 | 数据采集 | 输出 |
|---|---|---|---|
| **单指标查询** | 用户只问主力资金、龙虎榜、两融、筹码、卖空等一个明确指标 | 只调用对应 `westock-data` 命令 | 数值 / 方向 + 日期 + 数据来源；**不读 reference** |
| 简版雷达 | 用户问“资金面怎么样 / 谁在买卖 / 有没有利空”，但未要求完整报告 | 资金流 + 龙虎榜 / 两融 / 筹码三选一；事件风险摘要按需 | 一句话定调 + 2-3 维证据 + 风险提示 |
| 完整画像 | 用户明确要求完整、系统、雷达报告、微观结构全景 | 读取 `references/market-analysis.md`，按命中模块拉全命令 | 四维温度计 / 事件时间轴 / 红旗清单 |

默认规则：

- 用户没有明确说“完整 / 系统 / 雷达报告 / 微观结构全景”时，不读取完整方法论，不拉全所有命令。
- 全市场资金流、板块资金流或排行问题转 `westock market-overview`、`westock sector ranking` 或 `westock screen ranking --type <指标名>`，不走单股雷达。
- 港股 / 美股卖空和空头问题优先 `westock fund short <code>`，不套 A 股雷达。
- 数据不足时输出可核实维度和缺口，不把单指标问题升级为完整画像。

## 5. 执行流程（按深度选择）

**Step 1 · 判断意图与路由**：对照“触发场景与模块路由”表，确定属于 ①资金分析 ②事件雷达 ③两者组合；用户给名称时，使用 `westock search <名称>` 定位唯一代码（实际执行按上文跨 Skill 替换规则处理）；无法唯一定位时停止并等待用户确认。非 A 股走“适用范围与降级分支”，先说明完整能力仅适用于 A 股。

**Step 2 · 选择采集粒度**：
- 单指标查询：不读 `references/market-analysis.md`，直接调用对应命令。
- 简版雷达：不读完整方法论，只按下方简版命令骨架拉数。
- 完整画像：完整读取 `references/market-analysis.md`，按其中对应模块的维度清单执行。

**Step 3 · 按模块拉数（命令清单见 `references/data-mapping.md`）**：
- **单指标查询**：主力资金用 `westock fund flow <code>`；龙虎榜用 `westock lhb --type institution,hotmoney,activeseat`；两融用 `westock fund margin <code>`；筹码用 `westock chip <code>`；港美卖空 / 空头用 `westock fund short <code>`。
- **资金分析（简版雷达）**：`westock fund flow <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` + 用户关心维度中的一个：`westock lhb --type institution,hotmoney,activeseat` / `westock fund margin <code>` / `westock chip <code>`。若用户明确问“主力还是游资”，优先补龙虎榜；问杠杆，补两融；问套牢盘，补筹码。
- **资金分析（完整画像）**：`westock fund flow <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` + `westock lhb --type institution,hotmoney,activeseat` + `westock fund margin <code>` + `westock chip <code>` + `westock connect --exchange sh` 或 `westock connect --exchange sz`。某维度因产品边界不可用时显式标注“不适用”。
- **事件雷达（简版）**：`westock events <code>` + `westock risk <code> --types pledge,unlock,lawsuit,specialtrade,seasonedissue`；只有用户追问具体事件时再补公告列表或正文。
- **事件雷达（完整）**：简版命令 + `westock notice list <code> --type 3` + `westock notice list <code> --type 4` + `westock notice list <code> --type 5` + `westock notice list <code> --type 6` + `westock disclosure <code>` + `westock dividend list <code> --all` + 必要时 `westock calendar --event financial_report,dividend,trading_halt,meeting,lockup_release,rights_issue --market hs`。
- **组合**：默认用简版资金分析 + 简版事件雷达；用户明确要求完整报告时再拉全。拿到代码后，互不依赖的命令同轮并发；多标的支持逗号批量的命令一次传入。

完整资金分析产出必须是**四维资金面温度计**：主力资金 / 席位、两融杠杆、筹码结构、北向标的池分别给偏多 / 中性 / 偏空 + 关键数字。简版雷达只输出已采集维度，不补齐四维。

**Step 4 · 按标准格式构建产出**：资金面温度计表 / 事件时间轴（按临近度 + 影响度排序）/ 红旗清单。只丢几条原始数据、不排时间轴、不出温度计，属于错误执行。

**Step 5 · 不复述方法论**：用户要的是结果，不是方法论本身。

## 6. 常用数据访问（统一走 westock-data）

| 数据 | 命令 | 所属模块 |
|---|---|---|
| 名称转代码 | `westock search <名称>` | 前置步骤 |
| 主力资金净额 | `westock fund flow <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` | 资金分析 |
| 龙虎榜席位 | `westock lhb --type institution,hotmoney,activeseat` | 资金分析 |
| 融资融券 | `westock fund margin <code>` | 资金分析 |
| 筹码结构 | `westock chip <code>` | 资金分析 |
| 北向 / 陆股通标的池 | `westock connect --exchange sh` 或 `westock connect --exchange sz` | 资金分析 |
| 事件总览 | `westock events <code>` | 事件雷达 |
| 风险事件 | `westock risk <code> --types pledge,unlock,lawsuit,specialtrade,seasonedissue` | 事件雷达 |
| 增发公告 | `westock notice list <code> --type 3` | 事件雷达 |
| 股权变动公告 | `westock notice list <code> --type 4` | 事件雷达 |
| 重大公告 | `westock notice list <code> --type 5` | 事件雷达 |
| 风险公告 | `westock notice list <code> --type 6` | 事件雷达 |
| 业绩披露日历 | `westock disclosure <code>` | 事件雷达 |
| 分红除权线索 | `westock dividend list <code> --all` | 事件雷达 |
| 公告 / 研报 / 新闻原文核对 | `westock-finsearch query "<标题或id>"` | 原文核对 |

> 港美股降级规则见“适用范围与降级分支”；不得把 A 股特有微观结构命令静默套用于港股或美股。

## 7. 交付物自检（输出前逐项打勾，缺项即不合格）

- [ ] 是否按用户关切选择单指标、简版雷达或完整画像，避免默认拉全？
- [ ] 只有完整画像路径才完整读取 `references/market-analysis.md`；轻量 / 简版路径不得为了读方法论拖长链路。
- [ ] 命中模块的命令是否与所选深度匹配？产品边界不可用的维度是否已显式标注“不适用”（而非静默跳过）？
- [ ] **事件雷达**：完整路径是否产出**按临近度 + 影响度排序的事件时间轴**，简版路径是否至少列出高影响事件和缺口？
- [ ] **资金分析**：完整路径是否产出**四维资金面温度计表**；简版路径是否说明只覆盖已采集维度？
- [ ] 是否有**红旗清单**汇总高抛压 / 平仓 / 重大风险项？
- [ ] **组合 / 宽问法**：是否用“资金面温度 + 最近高影响事件”给**一句话定调**（而非以技术面长总结收尾）？
- [ ] 给出资金面判断或拒答买卖建议时，是否声明“资金面为高噪声数据、仅刻画交易结构、不构成买卖信号”（拒答也须挂数字与来源）？
- [ ] **港美股**：是否在开头完整说明“本模块为 A 股微观结构设计，`westock chip` / `westock lhb` / `westock fund margin` / `westock connect` 均不适用”（产品边界而非缺数据）；港股卖空 / 空头是否改用 `westock fund short <code>`，并按本币标注？
- [ ] 是否标注数据来源与数据日期、未编造任何数字？回复是否避免以“数据够了 / 现在我有足够数据了”等过程旁白或 `---` 分隔线开头？

## 8. 全局规范（必须遵守）

1. **数据真实性（合规底线）**：遵守 §1 数据来源规范；任何命令不可用或业务所需数据缺失时，必须立即停止并告知用户，严禁编造、推算或引用来源不明的数字。
2. **量化为先**：所有判断、评级、结论必须有数字支撑。
3. **货币单位**：港股标港元 / 美元，美股标美元，禁止对港美股使用人民币符号。
4. **引用纪律**：统一标注“数据来源：westock-data（腾讯自选股行情数据接口）”，并注明报告期 / 日期范围；公告 / 研报引用其标题与 id。
5. **不构成投资建议**：产出为供专业人士复核的研究草稿，不构成证券投资咨询或交易建议；解禁 / 质押等是“值得关注的信号”而非“做空理由”。
6. **A 股本地化**：SEC EDGAR → 交易所公告；Non-GAAP → 扣非净利润；10-K / 10-Q → 年报 / 季报。
7. **数据不足强制停止**：`westock-data` 或 `westock-finsearch query` 无法返回所需数据时，禁止用占位符 / 估算值填充；必须如实标注“数据不足，无法核实”，停止当前分析步骤，并等待用户决策。
8. **输出可达性（受众自适应）**：专业用户保留术语与完整量化表；散户提问时用大白话 + 红 / 黄 / 绿信号解释，但数字与风险提示绝不简化。
9. **输出格式**：用户可见的第一条文本必须是最终结论 / 报告本身，禁止“数据都齐了”“信息收集充分了”“现在来整理”“数据已收集完毕”等过渡句开头；这类文本即使出现在较早 payload 也视为格式违规。最终输出必须是纯 Markdown，禁止 `<span>`、`<div>` 等原始 HTML 标签；强调颜色或状态时用 Markdown 加粗、表格或 emoji 代替。

## 10. 重要声明

> 1. 本技能仅基于公开市场数据提供客观研究分析，不构成证券投资咨询服务或交易建议。
> 2. 数据可能存在延迟与口径差异，请以交易所 / 公司官方披露为准。
> 3. 投资有风险，决策需谨慎。如需专业投资建议，请咨询持牌证券投资顾问机构。

**数据来源**：westock-data（腾讯自选股行情数据接口）

## References

- `references/data-mapping.md`：盘面雷达相关命令、市场限制和字段口径。
- `references/market-analysis.md`：完整画像方法论，仅在用户明确要求完整雷达报告时读取。
