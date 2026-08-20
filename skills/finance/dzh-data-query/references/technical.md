# 技术指标（technical）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询技术分析指标：MACD、KDJ、均线（MA5/10/20/60）、布林带 BOLL、RSI、压力位、支撑位、指数估值等。

## 典型问题

- 贵州茅台 MACD 当前是金叉还是死叉？
- 比亚迪 5 日、10 日均线是多少？
- 沪深300 BOLL 上下轨？
- 宁德时代 RSI 处于什么水平？
- 上证综指当前估值百分位？

## 推荐工具

### 1. market-quote-getIndicatorCalc — 技术指标计算（旧版）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
	- `name`：建议显式传入，字符串枚举，支持 `MA`、`BOLL`、`VOL`、`KDJ`、`MACD`、`RSI`、`DDX`、`DDY`、`DDZ`
	- `beginTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
	- `endTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
	- `split`：可选，字符串，`0` 不复权、`1` 前复权、`2` 后复权，默认 `1`
	- `start`：可选，整数
	- `count`：可选，整数

```json
{"name": "market-quote-getIndicatorCalc",
 "params": {"stockCode": "<STCODE>", "name": "MACD", "split": "1", "count": 30}}
```

### 2. market-quote-getIndicatorCalcNew — 技术指标计算（新版，推荐）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
	- `nameEnum`：必填，字符串枚举，支持 `DBJJ`、`TT`、`TS`、`XSDF`、`QXZD`、`LDS`、`ACY`、`ZLMC`、`QSZZ`、`SQDXH`、`LMSJ`
	- `periodEnum`：必填，字符串枚举，支持 `MIN`、`MIN_1`、`MIN_5`、`MIN_15`、`MIN_30`、`MIN_60`、`DAY_1`、`WEEK`、`MONTH`、`YEAR`
	- `beginTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
	- `endTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
	- `start`：可选，整数
	- `count`：可选，整数
- 常用映射：`TS=九转`、`TT=双突`、`DBJJ=底部狙击`、`QXZD=情绪转点`、`ACY=涨跌动能`、`QSZZ=趋势追踪`
- 参数模板：

```json
{"name": "market-quote-getIndicatorCalcNew",
 "params": {"stockCode": "<STCODE>", "nameEnum": "TS", "periodEnum": "DAY_1", "count": 30}}
```

### 3. market-quote-getIndexevaluation — 指数估值

- 参数说明：
	- `stockCode`：必填，数组，例如 `["SH000300"]`

```json
{"name": "market-quote-getIndexevaluation",
 "params": {"stockCode": ["<STCODE>"]}}
```

### 4. market-quote-getQuoteDyna — 实时价用于辅助判断

- 参数说明：
	- `stockCode`：必填，数组，例如 `["SH600519"]`

## 注意事项

- 旧版指标工具使用参数名 `name`，新版指标工具使用 `nameEnum` 和 `periodEnum`，不要写成 `indicator`、`period`。
- 技术指标对周期敏感，必须显式传周期；旧版工具没有 `period` 参数，新版工具必须传 `periodEnum`。
- 指数估值仅对宽基/行业指数有效。
