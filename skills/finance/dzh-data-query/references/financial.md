# 财务指标（financial）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询上市公司的财务报表与衍生指标：营收、净利润、毛利率、净利率、ROE、PE、PB、EPS、TTM、资产负债率、现金流等。

## 典型问题

- 贵州茅台最新季度净利润是多少？
- 比亚迪去年 ROE 多少？
- 宁德时代 PE TTM 是多少？
- 五粮液近三年营收增长情况？
- 万科 A 资产负债率多高？

## 推荐工具

| 工具 | 用途 |
|------|------|
| `finance-getStockFinanceData` | 综合财务数据（营收、净利、毛利率等） |
| `finance-getStockCorpProfit` | 公司利润表 |
| `finance-getStockSecuProfit` | 证券利润数据 |
| `finance-getStockInsProfit` | 保险/机构利润 |
| `finance-getStockPrgbincstatement` | 利润表（分项） |
| `finance-getStockXjllData` | 现金流量表 |
| `finance-getBalanceSheetMetrics` | 资产负债指标 |
| `finance-getStockYynlfx` | 营运能力分析 |
| `finance-getStockSyzlfx` | 收益质量分析 |
| `finance-getStockCznlfx` | 偿债能力分析 |
| `finance-getDjcwData` | 杜邦财务分解 |
| `finance-getTtmcwData` | TTM 财务指标 |
| `finance-getZbjgfx` | 指标结构分析 |
| `stock-profile-getF10JggdzbData` | F10 机构估值指标 |
| `market-quote-getQuoteDyna` | 实时 PE/PB（市场快照） |

## 参数说明

### 财务类主工具共用参数

以下工具的输入参数结构一致：

- `finance-getStockFinanceData`
- `finance-getStockCorpProfit`
- `finance-getStockSecuProfit`
- `finance-getStockInsProfit`
- `finance-getStockPrgbincstatement`
- `finance-getStockXjllData`
- `finance-getBalanceSheetMetrics`
- `finance-getStockYynlfx`
- `finance-getStockSyzlfx`
- `finance-getStockCznlfx`
- `finance-getDjcwData`
- `finance-getTtmcwData`
- `finance-getZbjgfx`

参数定义：

- `stockCode`：必填，字符串，股票代码，例如 `SH600519`
- `endDate`：可选，数组，按报告期筛选；数组元素格式为 `{ "operator": "EQ|GT|GTE|LT|LTE", "value": 20250331 }`

说明：

- `endDate` 是数组，不是单个字符串，也不是 `reportPeriod`
- `value` 必须是整数日期，格式为 `yyyyMMdd`，例如 `20250331`
- 查询单个报告期时，通常使用 `[{"operator":"EQ","value":20250331}]`
- 做区间筛选时，可重复传多个条件，例如 `GTE + LTE`

通用模板：

```json
{"name": "finance-getStockFinanceData",
 "params": {"stockCode": "<STCODE>", "endDate": [{"operator": "EQ", "value": 20250331}]}}
```

### 特殊工具参数

#### stock-profile-getF10JggdzbData

- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10JggdzbData",
 "params": {"stockCode": "<STCODE>"}}
```

#### market-quote-getQuoteDyna

- `stockCode`：必填，数组，数组元素为股票代码字符串，例如 `["SH600519"]`

```json
{"name": "market-quote-getQuoteDyna",
 "params": {"stockCode": ["<STCODE>"]}}
```

## 注意事项

- 禁止使用 `finance-getStockCenznlfx`（业务限制）。
- PE/PB TTM 与盘中实时口径可能不同，明确口径再选工具。
- 财务类工具应优先显式传 `endDate`，不要编造 `reportPeriod`、`beginTime`、`endTime` 这类字段。
