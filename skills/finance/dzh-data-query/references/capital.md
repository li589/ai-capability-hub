# 资金与龙虎榜（capital）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询主力资金流向、龙虎榜、北向资金、大宗交易、融资融券等资金面数据。

## 典型问题

- 贵州茅台今天主力净流入多少？
- 比亚迪近期是否上龙虎榜？
- 宁德时代北向资金持仓变化？
- 最近大宗交易折溢价情况？
- 融资融券余额怎么样？

## 推荐工具

### 1. market-quote-getCapitalinflowMin — 资金流向（分钟级）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "market-quote-getCapitalinflowMin",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. market-quote-getNorthboundStockInfo — 北向资金持股

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
	- `beginTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
	- `endTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
	- `start`：可选，整数，`0`、`1` 或不传表示从第 1 条开始
	- `count`：可选，整数，`0` 或不传表示取所有

```json
{"name": "market-quote-getNorthboundStockInfo",
 "params": {"stockCode": "<STCODE>", "beginTime": "20250201-000000", "endTime": "20250513-150000", "count": 20}}
```

### 3. market-quote-getFinanceRzrq — 融资融券明细

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "market-quote-getFinanceRzrq",
 "params": {"stockCode": "<STCODE>"}}
```

### 4. stock-profile-getF10LhbGpmxData — 龙虎榜个股明细

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
	- `tradeDate`：可选，字符串，格式 `yyyyMMdd`
	- `chgType`：可选，整数，涨跌类型

```json
{"name": "stock-profile-getF10LhbGpmxData",
 "params": {"stockCode": "<STCODE>", "tradeDate": "20250512"}}
```

### 5. stock-profile-getF10BlocktradeXwtj — 大宗交易统计

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10BlocktradeXwtj",
 "params": {"stockCode": "<STCODE>"}}
```

### 6. market-quote-getQuoteDyna — 实时盘口资金快照（辅助）

- 参数说明：
	- `stockCode`：必填，数组，例如 `["SH600519"]`

## 注意事项

- 资金类工具在涉及 `beginTime`/`endTime` 时必须显式传入。
- 北向资金按交易日统计，节假日无数据。
- 龙虎榜明细的日期参数名是 `tradeDate`，格式是 `yyyyMMdd`，不要编造 `date`、`reportDate` 等字段。
