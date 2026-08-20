# westock-valuation 数据映射

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

用户给名称未给代码时先执行 `westock search <名称>`，不要猜 code。

## 估值命令

| 数据需求 | 命令 | 批量 | 用途 |
|---|---|---:|---|
| 名称转代码 | `westock search <名称>` | 否 | 所有流程前置，必须先串行确认 code |
| 当前行情 / 当前估值 | `westock quote <code>` | 逗号批量 | 当前 PE/PB、市值、股本、股息率 |
| 历史估值截面 | `westock quote <code> --date <历史日>` | 多日期并发 | 3-5 年 PE/PB 分位；样本不足要标注 |
| 价格序列 | `westock kline <code> --period day --start <日期> --end <日期>` | 否 | 截面不足时配合 EPS 自算估值序列 |
| 多期财务 | `westock finance <code> --limit 12` | 逗号批量 | FCF、净利、营收、ROE、毛利率、历史 CAGR |
| 一致预期 | `westock consensus <code>` | 逗号批量 | A 股 EPS / 营收预期方向；港美股无数值化时降级 |
| 机构评级 | `westock rating <code>` | 逗号批量 | 评级与目标价趋势 |
| 研报列表 | `westock report list <code> --limit 10` | 否 | 只作为列表元数据入口 |
| 研报详情 | `westock report detail <id>` | 否 | 公开详情入口；ID 来自列表，需要 ID 后串行 |
| 公告列表 | `westock notice list <code> --limit 10` | 否 | 只作为列表元数据入口 |
| 公告详情 | `westock notice detail <id>` | 否 | 公开详情入口；ID 来自列表，需要 ID 后串行 |
| 正文证据 | `westock-finsearch query "标题或 id 关键词"` | 多关键词一次传入 | 公告 / 研报 / 新闻原文、催化剂描述 |

需要正文时使用 `westock-finsearch query "标题或 id 关键词"`；结构化数字不可来自 `westock-finsearch query`，非结构化正文不可来自未核实片段。

## 历史分位取数

优先路径：

```bash
westock quote <code>
westock quote <code> --date <历史日1>
westock quote <code> --date <历史日2>
westock quote <code> --date <历史日3>
westock finance <code> --limit 12
```

历史日期至少覆盖牛熊、财报周期和当前附近样本；样本不足 3 年时，必须标注"历史样本不足、分位参考性有限"。

截面不足时的 fallback（备选路径）：

```bash
westock kline <code> --period day --start <日期> --end <日期>
westock finance <code> --limit 12
```

用价格序列配合 EPS 或净资产口径自算 PE/PB 时，必须说明 EPS / BVPS 对齐口径和报告期；无法对齐时停止该分位判断。

## 催化剂取证

估值修复中的催化剂需要同时区分列表和正文：

```bash
westock notice list <code> --limit 10
westock report list <code> --limit 10
westock-finsearch query "<公司> 业绩预告 预增 预减 扭亏 首亏 催化剂" "doc id"
```

`westock notice list <code> --limit 10` 和 `westock report list <code> --limit 10` 只负责定位列表元数据；正文依据优先用 `westock-finsearch query`，或在 ID 已确认时用 `westock notice detail <id>` / `westock report detail <id>`。业绩预告语义必须保留：预增、预减、扭亏、首亏等方向要进入结论，不要只写"有公告"。

## 并发与终止条件

- `westock search <名称>` 依赖用户名称，必须先串行完成；后续所有命令依赖 code。
- code 已确认后，`westock quote <code>`、`westock finance <code> --limit 12`、`westock consensus <code>`、`westock rating <code>`、多个历史截面 `westock quote <code> --date <历史日>` 或 `westock kline <code> --period day --start <日期> --end <日期>` 可按互不依赖原则同轮并发。
- `westock report list <code> --limit 10` / `westock notice list <code> --limit 10` 只作列表元数据入口；获取 ID 后再串行查详情。
- 多标的比较时先分别确认 code；支持逗号批量的命令优先批量，不能批量的历史截面按标的分组并发。
- 关键估值数据缺失时停止结论，说明缺失项、已尝试命令和无法继续原因；空结果最多补查 1 次，仍无结果时不改用训练数据或估算值。

## 已知限制

| 限制 | 处理方式 |
|---|---|
| `westock consensus <code>` 对不同市场支持不一致 | A 股优先使用；港美股无数值化一致预期时，用 `westock rating <code>` 和 `westock report list <code> --limit 10` 定性降级 |
| 无 DCF / Excel 建模引擎 | 反向 DCF 为闭式反解；缺当前市值、FCF / 净利基数、历史 CAGR、WACC 或永续增长假设时停止或切相对估值 |
| 历史交易或财务样本不足 | 可输出可得样本，但必须标注样本不足，不给看似精确的高 / 低分位 |
| 公告、研报、新闻列表不等于正文证据 | 需要正文时用 `westock-finsearch query` 或公开详情命令，不能用列表摘要替代原文 |

## 跨 Skill 边界

| 需求 | 入口 |
|---|---|
| 单只标的数字 / 财务 / 行情查询 | `westock-data` |
| 非结构化金融正文搜索 | `westock-finsearch query` |
| 条件选股 / 筛选（PE<20 等） | `westock screen condition` |
| 排行榜 / TOP | `westock screen ranking` |
| 财报分析 / 财报前瞻 / 财务排雷 | `westock-financials` |
