# 证券基本信息（security_info）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询股票/指数/ETF 的基础档案：上市时间、行业、板块、概念、股本、流通股、ST 状态、证券代码、公司全称简称等。

## 典型问题

- 贵州茅台是什么时候上市的？
- 比亚迪属于哪个行业、什么概念？
- 宁德时代总股本和流通股是多少？
- 这个股票是 ST 吗？
- 五粮液的公司全称是什么？

## 推荐工具

### 1. stock-profile-getF10GsjsData — 公司基本档案

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
- 关键字段：`compname`（全称）、`compsname`（简称）、`symbol`、`zjhlevel`（行业）、`setype`（证券类型）、`listdate`（上市日期）
- 参数模板：

```json
{"name": "stock-profile-getF10GsjsData",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. stock-profile-getF10Information — 概念、题材、所属板块

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
- 关键字段：所属概念、题材、关联板块
- 参数模板：

```json
{"name": "stock-profile-getF10Information",
 "params": {"stockCode": "<STCODE>"}}
```

### 3. market-quote-getQuoteDyna — 当前股本/市值快照

- 用于补充总股本、流通股本、总市值、流通市值
- 参数说明：
	- `stockCode`：必填，数组，例如 `["SH600519"]`
- 参数模板：

```json
{"name": "market-quote-getQuoteDyna",
 "params": {"stockCode": ["<STCODE>"]}}
```

## 注意事项

- 上市日期、行业归属优先取 `getF10GsjsData`。
- ST/*ST 状态在公司档案与名称前缀中均可判断。
- `getQuoteDyna` 的 `stockCode` 必须是数组，不能写成字符串。
