# 行情数据（market）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询股票/指数/ETF 的实时和历史行情：最新价、涨跌幅、成交量/额、换手率、今开/昨收/最高/最低、涨停/跌停状态、K 线。

## 典型问题

- 贵州茅台今天涨了多少？
- 沪深300近一个月表现怎么样？
- 比亚迪最近5天成交量多少？
- 上证综指昨收是多少？
- 宁德时代最新价、今开、最高、最低分别是多少？

## 推荐工具

### 1. market-quote-getQuoteDyna — 实时行情快照

- 参数说明：
  - `stockCode`：必填，数组，数组元素为股票代码字符串，例如 `["SH600519"]`
- 用途：拉取最新价、涨跌幅、成交量、换手率、今开、昨收、最高、最低、涨停/跌停价、总市值、流通市值
- 参数模板：

```json
{"name": "market-quote-getQuoteDyna",
 "params": {"stockCode": ["<STCODE>"]}}
```

### 2. market-quote-getQuoteKline — K 线历史

- 参数说明：
  - `stockCode`：必填，字符串，例如 `SH600519`
  - `period`：可选，字符串枚举，支持 `MIN_1`、`MIN_5`、`MIN_15`、`MIN_30`、`MIN_60`、`DAY_1`、`WEEK_1`、`MONTH_1`、`SEASON_1`、`HALFYEAR_1`、`YEAR_1`；默认 `DAY_1`
  - `beginTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
  - `endTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
  - `start`：可选，字符串，例如 `"-10"` 表示返回最新 10 条
  - `count`：可选，整数，默认 100
  - `split`：可选，字符串，`0` 不复权、`1` 前复权、`2` 后复权；接口默认 `0`
- 参数模板：

```json
{"name": "market-quote-getQuoteKline",
 "params": {"stockCode": "<STCODE>", "period": "DAY_1", "count": 30, "split": "1"}}
```

### 3. market-quote-getIndicatorCalc — 指标计算（涨跌幅/区间统计）

- 用于按时间区间计算涨跌幅、区间高低点等
- 参数说明：
  - `stockCode`：必填，字符串，例如 `SH600519`
  - `name`：建议显式传入，字符串枚举，支持 `MA`、`BOLL`、`VOL`、`KDJ`、`MACD`、`RSI`、`DDX`、`DDY`、`DDZ`
  - `beginTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
  - `endTime`：可选，字符串，格式 `yyyyMMdd-HHmmss`
  - `split`：可选，字符串，`0` 不复权、`1` 前复权、`2` 后复权，默认 `1`
  - `start`：可选，整数，`0`、`1` 或不传都表示从第 1 条开始
  - `count`：可选，整数，`0` 或不传表示取所有

```json
{"name": "market-quote-getIndicatorCalc",
 "params": {"stockCode": "<STCODE>", "name": "MACD", "beginTime": "20250101-000000", "endTime": "20250513-150000", "split": "1", "count": 30}}
```

## 注意事项

- `getQuoteDyna` 必须传数组，不能传字符串。
- `getQuoteKline` 必须传字符串，不能传数组；`start` 的类型也是字符串，不是整数。
- `getIndicatorCalc` 的指标参数名是 `name`，不是 `indicator`。
- 时间跨度与 period 搭配（防止 100 条截断）：≤5月 用 `DAY_1`，5月~2年 用 `WEEK_1`，2~8年 用 `MONTH_1`，更长用 `SEASON_1` / `HALFYEAR_1` / `YEAR_1`。
