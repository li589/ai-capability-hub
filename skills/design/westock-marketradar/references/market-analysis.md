# 模式：market-analysis（盘面分析 · A股微观结构）

> 数据来源与停止规则见 SKILL.md §1。任一所需来源返回失败或无法提供业务所需数据时，立即停止并告知用户，禁止用占位符、估算值或外部搜索填充。

**核心理念**：A股是**资金与事件驱动**的市场。基本面决定方向，但资金面与事件决定节奏与拐点。本模式分两个模块——**资金分析**（主力 / 席位、两融、筹码、北向四维资金面）回答“谁在买卖”，**事件雷达**（事件标签、解禁、质押、增发、ST、诉讼、公告与日历）回答“临近什么催化或利空”。

触发："XX 最近资金面怎么样"、"主力/北向在买吗"、"游资还是机构在炒"、"筹码集中度/获利盘"、"有没有解禁/质押/增发风险"、"近期有什么催化剂事件"。

---

## 适用范围（重要）

- **完整能力仅适用于 A股（沪深京）**。
- 港股：仅 `westock fund flow <code>`（资金流）、`westock fund short <code>`（卖空）、`westock fund south-holding <code>`（南下持仓）等有限维度可用，其余 A 股微观结构维度需明确标注不适用。
- 美股：仅 `westock fund short <code>`（卖空）等有限维度可用，其余 A 股微观结构维度需明确标注不适用。
- 命中港美股标的时，**先告知用户本模式为 A股微观结构设计**，再给可用的有限数据。

---

# 模块一：资金分析（四维资金面温度计）

回答"**现在是谁在买卖、买卖结构如何**"。

### 维度 1 — 主力资金 / 席位画像
- **数据**：`westock fund flow <code>`（主力 / 超大单 / 大单资金净流入，`--start/--end` 看趋势）+ `westock lhb --type institution,hotmoney,activeseat`（机构、游资、活跃席位榜单）。
- **看什么**：近 5/10/20 日主力资金净额方向；上榜席位性质（机构专用席位=中长线信号；知名游资席位=短线博弈）。
- **判定**：🟢 主力持续净流入 + 机构席位介入；🟡 资金中性/分歧；🟠/🔴 主力持续净流出 / 仅游资对倒。

### 维度 2 — 杠杆与情绪（两融）
- **数据**：`westock fund margin <code>`（融资余额、融资买入占比；仅沪深）。
- **看什么**：融资余额趋势及占流通市值比例；融资盘是加杠杆做多还是撤离。
- **判定**：🟢 融资余额温和上升、占比适中；🟠/🔴 融资余额畸高（拥挤）或断崖下降（去杠杆踩踏风险）。

### 维度 3 — 筹码结构
- **数据**：`westock chip <code>`（筹码成本分布、集中度、获利盘比例；仅沪深京A股，`--start/--end`）。
- **看什么**：筹码集中度（集中=控盘度高）、平均成本 vs 现价、获利盘比例（高获利盘=抛压风险）。
- **判定**：🟢 筹码集中且现价在主力成本上方不远；🟠/🔴 高度套牢盘密集上方（套牢压力）或获利盘极高（兑现风险）。

### 维度 4 — 北向 / 陆股通标的池
- **数据**：`westock connect --exchange sh` 或 `westock connect --exchange sz`（陆股通标的池）+ 结合 `westock fund flow <code> --start <YYYY-MM-DD> --end <YYYY-MM-DD>` 资金口径。
- **看什么**：是否为陆股通标的、资金流向是否配合。
- **判定**：🟢 北向标的且资金面配合；🟡 非北向或方向不明。

### 资金分析交付物
**资金面温度计表**：

| 维度 | 信号 | 关键数字 |
|---|---|---|
| 主力资金 / 席位 | 偏多/中性/偏空 | 近5日主力净额 = X 亿；龙虎榜席位性质 |
| 两融杠杆 | … | 融资余额趋势、占流通市值 X% |
| 筹码结构 | … | 集中度、获利盘 X%、平均成本 vs 现价 |
| 北向资金 | … | 是否陆股通标的、方向 |

---

# 模块二：事件雷达

回答"**临近有没有利空/催化**"，把临近事件按影响度与临近度排成时间轴。

- **数据**：`westock events <code>`（事件总览）+ `westock risk <code> --types pledge,unlock,lawsuit,specialtrade,seasonedissue`（质押 / 解禁 / 诉讼 / ST / 增发风险明细）+ `westock notice list <code> --type 3` / `westock notice list <code> --type 4` / `westock notice list <code> --type 5` / `westock notice list <code> --type 6`（增发 / 股权变动 / 重大 / 风险公告）+ `westock disclosure <code>`（财报披露日历）+ `westock dividend list <code> --all`（分红除权线索）；公告 / 事件**原文**用 `westock-finsearch query` 查询。
- **看什么**：
  - **解禁**：临近解禁时点与规模（占流通股比例），大额解禁=潜在抛压。
  - **质押**：大股东质押比例，高质押+股价下行=平仓风险。
  - **增发/定增**：摊薄与折价。
  - **ST/诉讼**：重大风险事件。
  - **业绩披露 / 预告**：结合 `westock events`、`westock notice list` 与 `westock disclosure` 判断临近披露和盈利方向线索；若公告或事件标签给出预增 / 预减 / 扭亏 / 首亏等方向，必须写入事件时间轴。
- **判定**：按事件临近度与影响度排序，标红高影响事件。

### 事件雷达交付物
1. **事件时间轴**：按日期列出临近的解禁 / 质押 / 增发 / 业绩披露 / 分红除权线索，标注影响度；无日期事件放“待核实”区。
2. **红旗清单**：高抛压/平仓/重大风险事件汇总。

---

## 工作流

1. 若用户给名称，先 `westock search <名称>` 拿代码；确认是否 A股（非 A股走“适用范围”分支）。
2. 按意图选模块并**拉全命令，不可只拉一两个**：
   - 资金分析（四维必须全跑）：`westock fund flow <code>` + `westock lhb --type institution,hotmoney,activeseat` + `westock fund margin <code>` + `westock chip <code>` + `westock connect --exchange sh` 或 `westock connect --exchange sz`；
   - 事件雷达：先 `westock events <code>` 看全貌，再拉 `westock risk <code> --types pledge,unlock,lawsuit,specialtrade,seasonedissue` + `westock notice list <code> --type 3` + `westock notice list <code> --type 4` + `westock notice list <code> --type 5` + `westock notice list <code> --type 6` + `westock disclosure <code>` + `westock dividend list <code> --all`，必要时补 `westock calendar --event financial_report,dividend,trading_halt,meeting,lockup_release,rights_issue --market hs`。
   - 任一维度数据不可用时，**显式标注"不适用/数据不足"，禁止静默跳过整个维度**。
3. 逐维度/逐事件给 偏多 / 中性 / 偏空（或影响度）+ 关键数字。
4. 汇总成"资金面温度计 + 事件时间轴（**按临近度 + 影响度排序**）+ 红旗清单"——**禁止只丢几条原始数据交差**。

---

## 交付物格式（完整盘面分析）

1. **一句话定调**：资金面温度（偏多/中性/偏空）+ 最近的高影响事件。
2. **资金面温度计表**（模块一，见上）。
3. **事件时间轴**（模块二，见上）。
4. **红旗清单**：高抛压/平仓/重大风险事件汇总。
5. **数据与引用**：末尾附"数据来源：westock-data（腾讯自选股行情数据接口）；非结构化内容：westock-finsearch"，注明数据日期。

**规范**：资金面是高频、高噪声数据，**仅供刻画交易结构与风险，不构成买卖信号，更不构成投资建议**；解禁/质押等是"值得关注的信号"而非"做空理由"；量化为先，无数据维度明确标注"不适用/数据不足"。

---

## 使用示例

```
用户："看看宁德时代最近资金面，有没有解禁风险？"
→ westock search 宁德时代 → sz300750
→ 资金分析：westock fund flow sz300750 --start ... --end ...；westock lhb --type institution,hotmoney,activeseat；westock fund margin sz300750；westock chip sz300750；westock connect --exchange sz
→ 事件雷达：westock events sz300750；westock risk sz300750 --types unlock,pledge,seasonedissue；westock notice list sz300750 --type 6
→ 输出"资金面温度计 + 事件时间轴 + 红旗清单"
```
