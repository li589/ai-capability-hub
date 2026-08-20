# 模式：financial-forensics（财务鉴证）

> 数据来源与停止规则见 SKILL.md「数据来源与停止规则」。鉴证主数据缺失时必须停止；市场不支持的可选维度可标注省略，但不得支撑结论。

核心理念：利润表展示的是管理层"希望你看到的"，现金流量表展示的是"实际发生的"。系统性背离往往先于股价暴露风险。

触发："对 XX 跑一遍财务鉴证 / 财务体检"、"这家公司财报有没有水分"、"利润质量怎么样"、"是不是在粉饰报表"。

## 数据获取

| 需要的数据 | 稳定命令 | 说明 |
|---|---|---|
| 公司定位 | `westock search <名称>` | 用户给名称时先转代码 |
| 近 12 期三大报表 | `westock finance <code> --fields all --limit 12` | 鉴证主数据（排雷需应收/存货/合同负债/无形资产等明细字段，必须 `--fields all`，默认窄表不含） |
| 利润表 | `westock finance <code> --type income --fields all --limit 12` | 各市场（A股/港股/美股）统一用 `income`（旧值 lrb/zhsy 已弃用） |
| 资产负债表 | `westock finance <code> --type balance --fields all --limit 12` | 应收/存货/递延/无形资产/开发支出 |
| 现金流量表 | `westock finance <code> --type cashflow --fields all --limit 12` | 经营现金流、资本开支、股份支付 |
| 估值与股本 | `westock quote <code>` | PE/PB、总股本/流通股本（判断稀释） |
| 股东结构 | `westock shareholder <code>` | A 股 / 港股稀释分析与股本变化交叉核对 |
| 风险事件 | `westock risk <code>` | A 股质押、减持、诉讼、ST 等红旗线索；市场不支持时标注省略 |
| 公司简况 | `westock profile <code>` | 行业、主营，判断 DSO 异常是否有业务原因 |
| 业绩预告 / 扣非线索 | `westock disclosure <code>` | 财报预约披露日及业绩快报 / 预告线索（替代已弃用的旧 reserve 命令） |
| 公告列表 | `westock notice list <code> --type 1` | 用标题 / id 做交叉核对 |
| 公告全文 | `westock notice detail <id>` | id 来自 notice list 结果；也可用 `westock-finsearch query "公告标题或 id"` |

## 工作流

### Step 1 - 定位与拉数

1. 若用户给公司名，先用 `westock search <名称>` 拿到唯一代码。
2. 拉取核心数据：`westock finance <code> --fields all --limit 12`（含三大报表 12 期；`--fields all` 保证应收/存货/合同负债/无形资产等排雷明细字段，默认窄表会缺）。
3. 可并发补充：`westock quote <code>`（股本/估值）、`westock shareholder <code>`（股东结构/稀释线索）、`westock risk <code>`（A 股风险事件）、`westock profile <code>`（业务背景）、`westock disclosure <code>`（扣非线索及披露日期）、`westock notice list <code> --type 1`（公告列表）。
4. **鉴证主数据缺失时停止**；港美股无法取得某些 A 股专有字段时，如实标注，不要用估算填补。

### Step 2 - 逐项跑 6 大鉴证模式

对每个模式：计算指标，核对趋势，对照判定标准，给出干净 / 关注 / 存疑 / 红旗评分，并附支撑数字。

### Step 3 - 汇总输出

输出一句话定调、6 模式评分一览表、逐模式详述、红旗清单、数据与引用。

## 六大鉴证模式与判定标准

### 模式 1：自由现金流与净利润背离

- **测量**：近 3 年累计 FCF / 累计净利润（FCF = 经营现金流 − 资本开支），以及缺口趋势。
- **数据**：`westock finance <code> --type cashflow --fields all --limit 12`（经营现金流、购建固定资产等资本开支）+ `westock finance <code> --type income --fields all --limit 12`（净利润）。
- **判定**：🟢 Clean 比率 >0.85 且稳定；🟡 Watch 0.70–0.85 或单年波动；🟠 Concerning <0.70 且连续 3 年以上扩大；🔴 Red Flag 净利润持续为正但 FCF 持续为负。

### 模式 2：股权激励（SBC）稀释

- **测量**：股份支付占营收/营业利润比例；总股本/流通股本 CAGR vs 净利润 CAGR。
- **数据**：`westock finance <code> --type cashflow --fields all --limit 12`（股份支付科目/现金流量表附注）+ `westock quote <code>`（总股本、流通股本，多期对比）+ `westock shareholder <code>`（股东结构和限制性股票 / 激励相关线索）。
- **判定**：🟢 SBC < 营收 5% 且股本持平或回购；🟡 SBC 5%–10%；🟠 SBC > 营收 10% 且股本增速快于净利润；🔴 靠增发/激励持续摊薄，EPS 增长被股本扩张吞噬。
- **A股说明**：若现金流量表未单列股份支付，用"股本逐期变化 + 限制性股票/期权激励公告（`westock notice detail <id>`）"作为替代证据，并标注口径。

### 模式 3：渠道压货信号

- **测量**：DSO（应收账款周转天数）轨迹 vs 营收增长；存货天数 vs 营收增长。
- **数据**：`westock finance <code> --type balance --fields all --limit 12`（应收账款、存货）+ `westock finance <code> --type income --fields all --limit 12`（营收、营业成本）。DSO = 应收账款 / 营收 × 期间天数。
- **判定**：🟢 DSO 持平或下降；🟡 DSO 同比扩张 10%–20%；🟠 DSO 同比扩张 >20% 且无已知业务结构变化，或存货天数扩张 >15% 且超前于营收；🔴 营收增长主要由应收账款堆积驱动。
- **核对**：DSO 异常时用 `westock profile <code>` 判断是否有业务模式变化（如转 B 端账期变长）。

### 模式 4：扣非缺口扩大（A股本地化的 Non-GAAP 检验）

- **测量**：（净利润 − 扣非归母净利润）/ 净利润，看 3 年趋势及非经常性损益构成。
- **数据**：`westock finance <code> --type income --fields all --limit 12`（净利润、扣非归母）+ `westock disclosure <code>`（业绩预告扣非线索）+ `westock notice list <code> --type 1`（资产处置/政府补助等公告列表）。
- **判定**：🟢 缺口稳定且小，主要由真正一次性项目主导；🟡 缺口 10%–25%；🟠 缺口持续扩大，"政府补助/资产处置/公允价值变动"反复贡献利润；🔴 扣非后由盈转亏。
- **说明**：美股/港股标的改用其通用披露口径（Adjusted EPS − GAAP EPS）/ Adjusted EPS，数据来自 `westock finance <code> --type income --fields all --limit 12`（各市场统一，旧的 --type zhsy 已弃用）。

### 模式 5：营运资金需求信号

- **测量**：合同负债/递延收入轨迹；应收账款增速 vs 营收增速。
- **数据**：`westock finance <code> --type balance --fields all --limit 12`（合同负债/预收款项、应收账款）+ `westock finance <code> --type income --fields all --limit 12`（营收）。
- **判定**：🟢 合同负债与营收同步或更快增长；🟡 合同负债走平；🟠 合同负债收缩，应收增速明显快于营收；🔴 靠放宽账期换增长，经营性现金被持续占用。

### 模式 6：资本化政策选择

- **测量**：研发资本化率（资本化开发支出 / 研发总投入）趋势；无形资产/开发支出同比变化。
- **数据**：`westock finance <code> --type balance --fields all --limit 12`（无形资产、开发支出）+ `westock finance <code> --type income --fields all --limit 12`（研发费用）+ `westock finance <code> --type cashflow --fields all --limit 12`（无形资产投入）。
- **判定**：🟢 资本化率稳定且适中；🟡 缓慢上升；🟠 资本化率上升恰好发生在"利润超预期/扭亏"的期间；🔴 通过把费用资本化来粉饰当期利润。

## 交付物格式

1. 结论摘要：一句话定调 + 6 模式评分一览表。

   | 模式 | 评分 | 关键数字 |
   |---|---|---|
   | 1 FCF / 净利润背离 | 🟢 Clean / 🟡 Watch / 🟠 Concerning / 🔴 Red Flag | 近 3 年累计比率 = X |
   | 2 股权激励稀释 | 🟢 / 🟡 / 🟠 / 🔴 | SBC / 营收 = X%，股本 CAGR vs 净利润 CAGR |
   | 3 渠道压货 | 🟢 / 🟡 / 🟠 / 🔴 | DSO 趋势（同比 ±X 天） |
   | 4 扣非缺口 | 🟢 / 🟡 / 🟠 / 🔴 | 缺口 = X% 且趋势 |
   | 5 营运资金 | 🟢 / 🟡 / 🟠 / 🔴 | 合同负债趋势 |
   | 6 资本化政策 | 🟢 / 🟡 / 🟠 / 🔴 | 资本化率趋势 |

2. 逐模式详述：每个模式给数字、判定理由、时间序列。
3. 红旗清单：所有存疑 / 红旗项汇总，按严重度排序。
4. 数据与引用：末尾附"数据来源：westock-data（腾讯自选股行情数据接口）；非结构化内容：westock-finsearch"，注明报告期范围。

## 规范

- 量化为先；鉴证主数据缺失时停止，不输出评分。
- 市场不支持的可选模式或字段标注"数据不足，未纳入评分"，不能写成证据。
- 港美股不得用人民币符号。
- 红旗是值得进一步核查的信号，非做空理由、造假定性或投资建议。

## 使用示例

```text
用户："帮我对贵州茅台跑一遍财务鉴证"
-> `westock search 贵州茅台` 得到 `sh600519`
-> `westock finance sh600519 --fields all --limit 12`
-> 并发：`westock quote sh600519`、`westock profile sh600519`、`westock disclosure sh600519`
-> 逐项跑 6 模式，输出评分表和红旗清单
```
