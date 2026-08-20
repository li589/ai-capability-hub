# westock-financials 数据映射

> 结构化数字只通过 `westock-data` 获取；公告 / 研报 / 新闻正文只通过 `westock-finsearch query` 获取；禁止 HTTP 直连和凭记忆补数。完整合规底线见 SKILL.md。

## 调用方式

```bash
westock <command> [args] [flags]
westock-finsearch query "公告标题或关键词"
```

## 代码格式

| 市场 | 格式 | 示例 |
|---|---|---|
| 沪市 / 科创板 | `sh` + 6 位 | `sh600519`、`sh688981` |
| 深市 | `sz` + 6 位 | `sz000001` |
| 北交所 | `bj` + 6 位 | `bj430047` |
| 港股 | `hk` + 5 位 | `hk00700` |
| 美股 | `us` + 代码 | `usAAPL` |

未知代码先执行 `westock search <名称>`；无法唯一定位时先问用户确认。

## 财务报表命令

| 维度 | 命令 | 批量 | 说明 |
|---|---|---:|---|
| 三大报表（分析 / 前瞻默认） | `westock finance <code> --limit 8` | 逗号批量 | 8 期三大报表 |
| 三大报表（排雷默认） | `westock finance <code> --fields all --limit 12` | 逗号批量 | 12 期三大报表；排雷需明细字段，`--fields all` 必带（默认窄表不含应收/存货/合同负债/无形资产等） |
| 利润表明细（排雷，各市场） | `westock finance <code> --type income --fields all --limit N` | 逗号批量 | 扣非、归母、利润率；扣非（NPDeductNonRecurringPL）等明细需 `--fields all`；A股旧值 lrb、港股旧值 zhsy 均已弃用，统一用 `income` |
| 资产负债表明细（排雷，各市场） | `westock finance <code> --type balance --fields all --limit N` | 逗号批量 | 应收、存货、合同负债、无形资产、开发支出；均需 `--fields all`；A股旧值 zcfz 已弃用 |
| 现金流量表明细（排雷，各市场） | `westock finance <code> --type cashflow --fields all --limit N` | 逗号批量 | 经营现金流、资本开支、股份支付；资本开支/股份支付等明细需 `--fields all`；A股旧值 xjll 已弃用 |

## 预期与评级命令

| 维度 | 命令 | 批量 | 说明 |
|---|---|---:|---|
| 实时行情 / 估值 / 股本 | `westock quote <code>` | 逗号批量 | PE/PB、总 / 流通股本、股息率 TTM |
| 财报前后股价反应 | `westock kline <code> --period day --limit 10` | 否 | 对齐披露日前后表现 |
| A 股一致预期 | `westock consensus <code>` | 逗号批量 | 港美股弱或空时不可编造 |
| 机构评级 | `westock rating <code>` | 逗号批量 | 港美股 consensus 弱时定性修正 |
| 研报列表 | `westock report list <code> --limit 10` | 否 | 只拿标题 / id / 日期；正文用 `westock-finsearch query` |

## 事件与公告命令

| 维度 | 命令 | 批量 | 说明 |
|---|---|---:|---|
| 财报披露预约日 / 快报线索 | `westock disclosure <code>` | 逗号批量 | 财报预约披露日及业绩快报 / 预告线索（替代旧 reserve 命令） |
| 财报日历 | `westock calendar --event financial_report --market hs` | 否 | 发布状态前置判断；`--market` 可换 `hk`/`us` |
| 财报相关公告列表 | `westock notice list <code> --type 1` | 否 | **列表元数据入口**（标题 / id / 日期） |
| 公告全文 | `westock notice detail <id>` | 否 | id 来自 `westock notice list <code> --type 1`；也可用 `westock-finsearch query "公告标题或 id"` |
| 个股新闻列表 | `westock news list <code> --limit 10` | 否 | 仅在财报相关事实需要新闻元数据交叉核对时使用；正文用 `westock-finsearch query` |
| 新闻详情 | `westock news detail <id>` | 否 | id 来自 `westock news list <code> --limit 10` |

## 公司基本面命令

| 维度 | 命令 | 批量 | 说明 |
|---|---|---:|---|
| 公司简况 | `westock profile <code>` | 否 | 判断 DSO 异常是否有业务原因（排雷模式 3） |
| 分红记录 | `westock dividend list <code>` | 否 | 分红政策分析、核对现金回报 |
| 股东结构 | `westock shareholder <code>` | 否 | 排雷模式 2 稀释分析（仅 A 股 / 港股） |
| 风险事件（A 股） | `westock risk <code>` | 否 | 质押 / 减持 / 诉讼 / ST；主要适用于 A 股 |

## 非结构化正文

公告、研报、新闻、业绩会纪要原文统一通过 `westock-finsearch query` 获取：

- 先用 `westock notice list <code> --type 1` 或 `westock report list <code> --limit 10` 拿**列表元数据入口**（标题 / id / 日期）
- 再用 `westock-finsearch query "公告标题或 id"` 查正文证据
- 结构化数字不可来自 `westock-finsearch query`；非结构化正文不可来自未核实片段

## 并发与终止条件

- `westock search <名称>` 必须先串行确认代码；代码确认后，`westock finance <code>`、`westock consensus <code>`、`westock rating <code>`、`westock quote <code>`、`westock kline <code> --period day --limit 10`、`westock disclosure <code>`、`westock notice list <code> --type 1`、`westock report list <code> --limit 10`、`westock calendar --event financial_report --market hs` 互不依赖，可同轮并发。
- 公告列表 / 研报列表只作列表元数据入口；获取 id 后再串行查正文（`westock notice detail <id>` 或 `westock-finsearch query`）。
- 关键数据缺失时停止并等待用户决策；空结果最多补查 1 次，仍失败则说明缺失项和已尝试命令，不改用估算值。

## 已知限制

| 限制 | 处理方式 |
|---|---|
| 风险事件仅 A 股 | 港美股财务排雷不可用时标注 |
| 股东结构仅 A 股 / 港股 | 美股不可用时标注 |
| `westock consensus <code>` 为 A 股一致预期 | 港美股弱或空时用 `westock rating <code>` / `westock report list <code> --limit 10` 做定性判断，并注明不是 consensus 数字 |
| 无期权隐含波动率 | 标注"无可靠数据源"，不得编造 |
| whisper number 无可靠来源 | 标注来源缺失，不纳入结论 |
| 港美股币种不同 | 港股标港元 / 美元，美股标美元，禁止使用人民币符号 |

## 跨 Skill 边界

| 需求 | 入口 |
|---|---|
| 单只标的数字 / 财务 / 行情查询 | `westock-data` |
| 非结构化金融正文搜索 | `westock-finsearch query` |
| 条件选股 / 筛选（PE<20 等） | `westock screen condition` |
| 排行榜 / TOP | `westock screen ranking` |
| 估值模型 / 反向 DCF | `westock-valuation` |
