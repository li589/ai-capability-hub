# TDX MCP 数据工具协议

本文件为通达信 MCP 15 工具的完整调用规范。执行时以根目录 SKILL.md 为准，本文件仅供参考。

---

## 工具路由表

| 数据需求 | 工具 | 必填参数 | 可选参数 | 备注 |
|----------|------|----------|----------|------|
| 代码定位 | `tdx_lookup_stock` | query | range | |
| 实时行情 | `tdx_quotes` | code, setcode | hasCwInfo="1"（需估值数据时必传） | |
| 历史 K 线 | `tdx_kline` | code, setcode, period | start, end | |
| 财务指标对比 | `tdx_indicator_select` | message | — | |
| 条件选股 | `tdx_screener` | message | rang(注意拼写非range), pageSize | |
| 深度资料 F9/F10 | `tdx_security_deep_info` | query, entity_type | — | |
| 研报与评级 | `wenda_report_query` | name | bdate, edate | |
| 公告 | `wenda_notice_query` | name | bdate, edate | |
| 新闻 | `wenda_news_query` | name | bdate, edate | |
| 宏观指标 | `wenda_macro_query` | query | — | |

### 扩展工具（当前版本未启用）

以下工具已接入但当前子技能均未使用，仅列出供后续扩展参考：

| 工具 | 用途 | 必填参数 |
|------|------|----------|
| `tdx_futures_quotes` | 期货行情 | code |
| `tdx_futures_deep_info` | 期货深度资料 | query |
| `tdx_option_t_quote` | 期权 T 型报价 | code |
| `tdx_ai_listening` | AI 盯盘 | — |
| `tdx_api_data` | 通用数据接口 | message |

---

## 调用规则

调用以上工具时必须严格遵守以下规则：

### 数据冲突优先级

当同一指标从多个来源获取且数值不一致时，按以下层级取用：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1 | TDX MCP 实时接口（tdx_quotes、tdx_indicator_select） | 交易所级别数据，最高信任 |
| 2 | 公司公告原文（wenda_notice_query） | 审计后披露数据 |
| 3 | 卖方研报（wenda_report_query） | 有明确分析师归属的预测与估算 |
| 4 | WebSearch 降级获取 | 标注 [WEB-FALLBACK]，仅在前三级不可用时使用 |

冲突处理规则：
- 同一指标多源不一致且差异 ≤10%：取优先级更高来源
- 差异 >10%：标注 `[CONFLICT]` 并附两个数据值与各自来源
- 永远不得无来源估计

### 调用规范

1. 先定位后取数。遇到中文名称或代码不确定时，先调用 `tdx_lookup_stock` 获取 code、setcode、entity_type，再调用后续工具。
2. 所有工具使用结构化参数调用。`tdx_indicator_select` 与 `tdx_screener` 的 message 字段为自然语言入口，直接描述需求。
3. 日期参数格式为 YYYYMMDD 绝对日期。禁止使用"最近 30 天""上个季度"等相对表达。
4. **并行调用**。同一个 LLM turn 内允许同时发起多个 MCP 工具调用。多股取数时，在一个 turn 中并行调用多个 `tdx_quotes`（每只一个调用），或一次性在 `tdx_indicator_select` 的 message 中描述多家公司对比需求（最多 5 家）。禁止串行逐只发起独立 turn。
5. `tdx_screener` 返回结果可能被引擎放宽条件，必须对返回数据按原始条件二次过滤。
6. `tdx_quotes` 需要估值数据时必须传 `hasCwInfo="1"`，否则仅返回行情。
7. `wenda_report_query`、`wenda_notice_query`、`wenda_news_query` 的 name 字段传公司简称，bdate/edate 传 YYYYMMDD。

### 并行调用示例

对比 5 家白酒公司估值数据的单 turn 并行方案：

```
同一 turn 并行发起：
  tdx_quotes(code="600519", setcode="1", hasCwInfo="1")
  tdx_quotes(code="000858", setcode="0", hasCwInfo="1")
  tdx_quotes(code="000568", setcode="0", hasCwInfo="1")
  tdx_quotes(code="002304", setcode="0", hasCwInfo="1")
  tdx_quotes(code="603369", setcode="1", hasCwInfo="1")
```

财务指标对比的单调用方案：

```
tdx_indicator_select(message="对比贵州茅台、五粮液、泸州老窖、洋河股份、舍得酒业的 ROE、净利率、营收增速、毛利率")
```

原则：能一次调用解决的用一次调用；必须逐只调用的（如 `tdx_quotes`）在同一 turn 并行发起。

---

## 参数详细说明

### tdx_lookup_stock

- query：公司名称、代码、拼音缩写均可
- range：限定搜索范围，如 "A股"、"港股"

### tdx_quotes

- code：6 位数字代码
- setcode：市场代码，0=深圳，1=上海，71=港股
- hasCwInfo："1" 表示附带财务估值数据

### tdx_kline

- code：6 位数字代码
- setcode：市场代码
- period：K 线周期，day/week/month/min5/min15/min30/min60

### tdx_indicator_select

- message：自然语言描述所需指标与对比维度，如"对比贵州茅台、五粮液、泸州老窖的 ROE、净利率、营收增速"

### tdx_screener

- message：自然语言描述筛选条件，如"A股中 PE 低于 20 且 ROE 大于 15% 的白酒股"
- rang：市场范围
- pageSize：返回条数上限

### tdx_security_deep_info

- query：公司名称或代码
- entity_type：实体类型，stock/fund/bond/index

### wenda_report_query / wenda_notice_query / wenda_news_query

- name：公司简称
- bdate：起始日期 YYYYMMDD
- edate：结束日期 YYYYMMDD

### wenda_macro_query

- query：宏观指标名称或描述，如"中国 CPI 同比"

---

## WebSearch 适用范围

仅以下数据允许使用 WebSearch 获取：

- 市场规模、TAM、行业增长率
- 产业链上下游关系
- 具体事件与政策解读原文
- 个股北向/南向资金（A股查北向资金；港股查南向资金持仓/港股通持股比例）

其余数据一律通过 MCP 或 dataSupplement 获取。
