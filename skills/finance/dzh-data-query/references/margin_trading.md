# 融资融券（margin_trading）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询个股融资融券余额、融资买入额、融券卖出额、两融余额变动等。

## 典型问题

- 贵州茅台最新融资余额？
- 比亚迪今日融资买入额？
- 宁德时代两融余额近期变化？
- 哪些股票融券卖出量明显？

## 推荐工具

### 1. market-quote-getFinanceRzrq — 融资融券明细

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "market-quote-getFinanceRzrq",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. stock-profile-getF10GsjsData — 公司档案（辅助）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

## 注意事项

- 两融数据按交易日发布，节假日无更新。
- 涉及时间范围的查询请在 query 中明确（如"近 5 个交易日"）。
