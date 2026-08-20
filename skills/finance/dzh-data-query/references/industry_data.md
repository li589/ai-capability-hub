# 产业数据（industry_data）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询行业指数、产业链、板块指数、大宗商品价格、产业景气数据等宏观/中观数据。

## 典型问题

- 白酒板块指数最近表现？
- 光伏产业链上游硅料价格？
- 波罗的海干散货指数当前是多少？
- 新能源车板块今天涨幅？

## 推荐工具

### 1. market-quote-getQuoteDyna — 行业指数/板块指数实时行情

- 参数说明：
	- `stockCode`：必填，数组，例如 `["SH000300"]`

```json
{"name": "market-quote-getQuoteDyna",
 "params": {"stockCode": ["<STCODE>"]}}
```

### 2. stock-profile-getF10Information — 概念/产业链关联

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10Information",
 "params": {"stockCode": "<STCODE>"}}
```

## 注意事项

- 板块代码由大智慧内部分配，使用时应替换为标准 `<STCODE>`。
- 大宗商品价格仅部分品种通过指数形式可查。
- 指数或板块快照工具仍要求 `stockCode` 为数组。
