# 分红送转（dividend）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询上市公司的现金分红、送股转股、股息率、登记日、除权除息日等。

## 典型问题

- 贵州茅台今年分红多少？
- 五粮液近三年累计分红？
- 这个股票什么时候除权？
- 当前股息率是多少？
- 历史送转比例如何？

## 推荐工具

### 1. stock-profile-getF10DividentsData — 分红明细

- 包含：方案、登记日、除权日、派息日、每股派现、每股送转
- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
	- `yearDate`：可选，数组；数组元素格式为 `{ "operator": "EQ|GT|GTE|LT|LTE", "value": 2025 }`
- 参数模板：

```json
{"name": "stock-profile-getF10DividentsData",
 "params": {"stockCode": "<STCODE>", "yearDate": [{"operator": "EQ", "value": 2025}]}}
```

### 2. stock-profile-getF10FhrzGxlData — 分红融资股息率

- 包含：股息率、累计分红、累计融资
- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
- 参数模板：

```json
{"name": "stock-profile-getF10FhrzGxlData",
 "params": {"stockCode": "<STCODE>"}}
```

### 3. market-quote-getQuoteDyna — 实时静态/动态股息率

- 用于补充当前价对应的股息率快照
- 参数说明：
	- `stockCode`：必填，数组，例如 `["SH600519"]`

## 注意事项

- 涉及"近 N 年"的查询，请在 query 中清晰表达年份范围。
- 分红明细的年份筛选参数名是 `yearDate`，类型是数组，不要写成 `year`、`reportYear`。
