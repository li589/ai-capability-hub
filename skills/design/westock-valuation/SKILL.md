---
name: westock-valuation
description: 围绕「贵不贵 / 值不值 / 能不能买 / 能不能修复」做可证伪估值判断，包含估值分析（反向 DCF 反推市场隐含增速、历史估值分位、一致预期修正动量，判断低估/合理/偏高）和估值修复（识别估值被压制到历史低位的标的，判断 re-rating 条件与空间）。当用户要"贵不贵/值不值/市场已计入了多高增长/估值在历史上算贵还是便宜/一致预期上调还是下调/估值有没有修复空间/会不会戴维斯双击"时命中。筛 PE/ROE 候选转 westock screen condition，纯 PE/PB 取数转 westock-data。基于Rappaport & Mauboussin《Expectations Investing》（反向 DCF）方法论进行设计。

---

# westock-valuation - 估值分析与估值修复

本 Skill 把"贵不贵 / 能不能修复"转成可证伪的估值判断。默认先按用户关切选择轻量 / 标准 / 深度路径；只有用户明确要求深度估值、反向 DCF、历史分位或完整报告时，才读取 `references/valuation-analysis.md`。不要临场发明命令、脚本路径、HTTP 直连或网页搜索。

## 适用场景

| 用户这么问 | 路径 |
|---|---|
| "茅台现在贵不贵 / 值不值"、"能不能买" | 轻量估值判断流程 |
| "估值在历史上算贵还是便宜"、"同业里贵不贵" | 标准估值判断流程 |
| "市场 price in 了多高增长，反推一下"、"做反向 DCF" | 估值分析流程 |
| "一致预期最近在上调还是下调" | 标准估值判断流程 |
| "XX 估值被打到地板了，有没有修复空间"、"会不会戴维斯双击"、"低估值能不能回归" | 估值修复流程 |

边界反例：

| 用户这么问 | 应路由到 |
|---|---|
| "查茅台现在的 PE/PB 是多少" | `westock quote <code>` 纯取数 |
| "筛选 PE<15、ROE>15% 的 A 股" | `westock screen condition` |

## ⚠️ 数据来源强制规范（最高优先级，任何步骤不得绕过）

| 数据类型 | 唯一允许来源 | 用法边界 |
|---|---|---|
| 结构化数字：行情、估值、财务、K 线、一致预期、评级 | `westock-data` | **禁止**用 `westock-finsearch query`、训练数据或估算值替代 |
| 列表元数据：公告、研报、新闻列表及 ID | `westock-data` | 只用于定位标题、时间、ID 和列表摘要 |
| 非结构化正文：公告 / 研报 / 新闻原文、催化剂描述 | `westock-finsearch query` | 可按标题、公司、文档 ID 或关键词查询正文证据 |

表中 `westock-data` / `westock-finsearch` 等为依赖 Skill 的调用简写；实际执行形态以其 SKILL.md 顶部「调用方式」为准。

**`web_search` 在本 Skill 内永久禁用。** 任何通过 `web_search` 得到的数字、事件、订单、合同信息都视为未核实数据，**严禁写入估值结论、催化剂或风险项**。

关键数据缺失时按路径处理：轻量路径至少需要当前行情 / 估值和一个基本面锚点；标准路径需要当前估值、财务基数和历史或同业锚点；深度路径才要求历史分位样本、反向 DCF 必需输入和完整假设。空结果最多按同一数据需求补查 1 次；仍缺失时输出可核实部分、缺失项和无法继续的维度，不把轻量问题升级成长链路补证。

可选或市场不支持维度只可标注省略，不能支撑结论。例如港美股无数值化一致预期时，可用评级和研报做定性降级，但禁止据此推算精确前瞻 PE。

## 代码定位

用户给名称但未给代码时，使用 `westock search <名称>` 定位唯一代码（实际执行按上文跨 Skill 替换规则处理）；无法唯一定位时停止并等待用户确认。

## 稳定命令集

| 数据需求 | 命令 | 说明 |
|---|---|---|
| 名称转代码 | `westock search <名称>` | 代码未知时串行前置 |
| 当前行情 / 当前估值 | `westock quote <code>` | 市值、PE、PB、股本、股息率等 |
| 历史估值截面 | `westock quote <code> --date <历史日>` | 多个历史日组成 3-5 年分位样本 |
| 价格序列 | `westock kline <code> --period day --start <日期> --end <日期>` | 截面不足时配合 EPS 自算估值序列 |
| 多期财务 | `westock finance <code> --type income --limit 12` | 净利、营收、ROE、毛利率趋势；仅深度分析需现金流/资产负债时再补 `--type` |
| 一致预期 | `westock consensus <code>` | A 股为主；港美股无数值化时降级 |
| 机构评级 | `westock rating <code>` | 评级和目标价趋势，用于预期方向 |
| 研报列表 / 详情 | `westock report list <code> --limit 10`、`westock report detail <id>` | 列表和公开详情入口；正文证据仍优先 `westock-finsearch query` |
| 公告列表 / 详情 | `westock notice list <code> --limit 10`、`westock notice detail <id>` | 列表和公开详情入口；正文证据仍优先 `westock-finsearch query` |
| 正文证据检索 | `westock-finsearch query "<公司> 催化剂 公告 研报" "doc id"` | 多关键词组一次传入，不拆多次串行 |

完整命令口径见 `references/data-mapping.md`。本 Skill 不提供自身 CLI，不调用脚本路径。

## 执行深度

| 深度 | 触发依据 | 数据采集 | 输出 |
|---|---|---|---|
| 轻量 | 用户问“贵不贵 / 值不值 / 能不能买 / 怎么看”，未要求完整报告 | `westock search <名称>`（如需）→ `westock quote <code>` → `westock finance <code> --type income --limit 4`；可选 `westock consensus <code>` / `westock rating <code>` 其一 | 一句话定调 + 2-4 个关键依据 + 风险等级 + 不构成投资建议；**不读 reference** |
| 标准 | 用户要求历史位置、同业比较、一致预期或表格 | 轻量路径 + 3-5 个历史 `westock quote <code> --date <历史日>` 截面或同业 / 板块锚点 + `westock consensus <code>` / `westock rating <code>` | 分层结论 + 估值锚点表 + 触发条件和风险 |
| 深度 | 用户明确要求深度估值、反向 DCF、完整历史分位、估值报告 | 读取 `references/valuation-analysis.md`，按方法论补历史分位、反向 DCF、一致预期、催化剂 | 完整估值报告 + 假设披露 + 敏感性和数据缺口 |

默认规则：

- 未明确“深度 / 完整 / 反向 DCF / 历史分位报告”时，不读方法论 reference，不做完整 DCF。
- 轻量路径有足够数据时立即输出“极端高估 / 偏高 / 合理 / 低估但需催化 / 数据不足”之一。
- “能不能买”必须改写为条件化帮助：风险等级、观察条件、失效条件和仓位纪律提示；不得直接给买卖指令。
- 港股 / 美股缺少数值化一致预期时，只降级该维度，不反复寻找等价字段超过 1 轮。

## 轻量估值判断流程

1. 代码未知时先 `westock search <名称>`；无法唯一定位再请用户确认。
2. 拉当前估值和基本面：`westock quote <code>` + `westock finance <code> --type income --limit 4`。
3. 根据问题选择一个最有效锚点：
   - 用户问“贵不贵”：优先当前 PE/PB、利润增速、ROE、现金流；
   - 用户问“能不能修复”：优先当前估值压制 + 基本面是否改善；
   - 用户问“市场预期”：优先 `westock consensus <code>` 或 `westock rating <code>`。
4. 输出风险分层：
   - 极端高估：估值显著脱离基本面，除非增长继续超预期；
   - 偏高：估值不便宜，需要业绩兑现；
   - 合理：估值与盈利质量大体匹配；
   - 低估但需催化：估值低，但需要业绩、政策或行业景气改善；
   - 数据不足：关键数据缺失，只给可核实部分。

## 标准估值判断流程

用户要求历史位置、同业比较、一致预期、表格或多个估值锚点时，走本路径；不读完整方法论，不做反向 DCF。

1. 在轻量路径基础上补 3-5 个最相关锚点：历史 `westock quote <code> --date <历史日>` 截面、同业 / 板块估值，或 `westock consensus <code>` / `westock rating <code>`。
2. 历史截面只用于解释“当前处于偏高 / 合理 / 偏低区间”，样本不足时标注限制，不把标准路径升级成完整分位报告。
3. 输出估值锚点表、触发条件、失效条件和不构成投资建议声明。

## 估值分析流程

仅当用户明确要求深度估值、反向 DCF、完整历史分位或系统报告时执行。

1. 读取 `references/valuation-analysis.md` 的估值分析方法论。
2. 拉当前估值与财务基数：`westock quote <code>` + `westock finance <code> --type income --limit 12`。
3. 做三件套：
   - 反向 DCF：用当前市值 / 企业价值、FCF 或净利基数、历史 CAGR、WACC 和永续增长反解市场隐含增速；净利为负、FCF 为负或现金流不稳时，标注 DCF 不适用并切相对估值。
   - 历史估值分位：优先用 `westock quote <code> --date <历史日>` 多点实算近 3-5 年 PE/PB 分位；样本不足时用 `westock kline <code> --period day --start <日期> --end <日期>` + 财务 EPS 自算，并标注样本限制。
   - 预期修正动量：用 `westock consensus <code>` 和 `westock rating <code>` 判断预期上修 / 下修；临近或刚过财报时提示一致预期可能滞后。
4. 输出"低估 / 合理 / 偏高 / 极端定价"一句话定调、关键数字、假设披露、日期范围和数据来源；不要复述完整方法论。

## 估值修复流程

估值修复必须先确认低分位，再谈催化剂和空间。

1. 先走轻量或标准路径确认当前估值是否确实偏低；用户明确要求完整修复报告时再读取 `references/valuation-analysis.md`。
2. 前置确认：用当前估值、历史 / 同业锚点判断当前 PE/PB 是否处于低分位。若当前分位不低或无法确认低分位，停止修复判断，回退为普通估值分析。
3. 三步判定：
   - 估值压制：当前估值低于历史 25% 分位，极端低位可看 10% 分位。
   - 修复触发：用 `westock finance <code> --type income --limit 12` 看基本面拐点，用 `westock consensus <code>` / `westock rating <code>` 看预期是否止跌回升，用 `westock notice list <code> --limit 10`、`westock report list <code> --limit 10` 和 `westock-finsearch query "<公司> 业绩预告 预增 预减 扭亏 首亏 催化剂"` 找催化剂证据。
   - 修复空间：以历史中枢分位或同业合理倍数测算区间，区分"仅估值回归"与"估值 + 盈利双击"。
4. 输出"修复条件具备 / 等待右侧 / 价值陷阱"定调、修复评估表、空间区间、假设披露和不构成投资建议声明。

## 并发与批量

- `westock search <名称>` 依赖用户名称，必须先串行完成；后续所有命令依赖 code。
- code 已确认后，`westock quote <code>`、`westock finance <code> --type income --limit 12`、`westock consensus <code>`、`westock rating <code>`、历史 `westock quote <code> --date <历史日>` 或 `westock kline <code> --period day --start <日期> --end <日期>` 可按互不依赖原则同轮并发。
- 多关键词催化剂检索一次传给 `westock-finsearch query`；需要 report / notice ID 后再查详情时串行。
- 多标的比较时，先分别确认 code；支持逗号批量的 `westock quote <code1,code2>`、`westock finance <code1,code2> --type income --limit 12`、`westock consensus <code1,code2>`、`westock rating <code1,code2>` 优先批量，不能批量的历史分位按标的分组并发。

## 边界和诱导处理

- 被要求给单一精确目标价：拒绝虚假精确，但继续给低估 / 合理 / 偏高定调、关键假设和区间判断，并声明不构成投资建议。
- 反向 DCF 不适用：净利为负、FCF 为负、现金流不稳或关键输入缺失时，不硬套 DCF，不反推精确股价。
- 港美股无数值化一致预期：用 `westock rating <code>` 和 `westock report list <code> --limit 10` 定性，不推算精确前瞻 PE。
- 上市历史过短：可以给可得样本分位，但必须标注"历史样本不足、分位参考性有限"。

## 交付物自检

- [ ] 是否先判断用户需要轻量、标准还是深度路径，避免把“贵不贵”升级成完整 DCF？
- [ ] 结论是否建立在当前估值、财务锚点、历史 / 同业锚点、反向 DCF 隐含增速中的至少一个可追溯依据上，而非凭记忆口述区间？
- [ ] 深度路径中的关键假设 WACC、永续增长、目标分位、修复目标分位是否显式披露？
- [ ] 所有结构化数字是否来自 `westock-data`，所有非结构化正文证据是否来自 `westock-finsearch query` 或依赖 Skill 公开详情入口？
- [ ] 估值修复是否先确认低分位；前置不成立时是否回退普通估值分析？
- [ ] 是否区分修复机会、等待右侧和价值陷阱？
- [ ] 散户提问时是否用红 / 黄 / 绿信号灯解释，同时保留数字和风险？
- [ ] 是否包含标的代码、日期范围、数据来源和"不构成投资建议"声明？

## 全局规范

1. **数据真实性（合规底线）**：遵守上文「数据来源强制规范」；任何命令不可用 / 失败时必须立即停止并告知用户，**禁止编造、推算或引用来源不明的数据**。
2. **量化为先**：所有判断必须有数字或可追溯证据支撑；估值假设（WACC / 永续增长 / 分位区间 / 修复目标分位）必须显式披露，杜绝虚假精确。
3. **货币单位**：港股标港元 / 美元，美股标美元，**禁止对港美股使用人民币符号**。
4. **引用纪律**：统一标注"数据来源：westock-data（腾讯自选股行情数据接口）；非结构化内容：westock-finsearch"，并注明报告期 / 日期范围；公告 / 研报引用标题与 ID。
5. **不构成投资建议**：本技能仅基于公开市场数据提供研究草稿，不构成证券投资咨询服务或交易建议；分位、隐含增速和修复空间是客观锚，不是买卖信号。
6. **A 股本地化**：SEC EDGAR 对应交易所公告；Non-GAAP 对应扣非净利润；10-K / 10-Q 对应年报 / 季报。
7. **数据不足强制停止**：`westock-data` 或 `westock-finsearch` 无法返回所需数据时，**禁止用占位符 / 估算值填充**，必须如实标注"数据不足，无法核实"并停止该维度推论，等待用户决策。
8. **输出可达性（受众自适应）**：专业用户保留术语与完整量化表；散户提问时用大白话 + 🟢/🟡/🔴 信号灯解释，**数字与风险提示绝不简化**。
9. **输出格式**：用户可见的第一条文本必须是最终结论 / 报告本身，禁止"数据都齐了""信息收集充分了""现在来整理""数据已收集完毕"等过渡句开头；这类文本即使出现在较早 payload 也视为格式违规。最终输出必须是纯 Markdown，禁止 `<span>`、`<div>` 等原始 HTML 标签；强调颜色或状态时用 Markdown 加粗、表格或 emoji 代替。

## 重要声明

> 1. 本技能仅基于公开市场数据提供客观研究分析，不构成证券投资咨询服务或交易建议。
> 2. 估值分位、隐含增速和修复空间是研究锚点，不是买卖信号或目标价承诺。
> 3. 投资有风险，决策需谨慎。如需专业投资建议，请咨询持牌证券投资顾问机构。

**数据来源**：westock-data（腾讯自选股行情数据接口）；非结构化内容：westock-finsearch。

## References

- `references/valuation-analysis.md`：估值分析与估值修复方法论、计算口径和交付物模板。
- `references/data-mapping.md`：稳定命令、数据来源分层、市场限制和失败处理。
