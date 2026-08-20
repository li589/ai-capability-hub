# 市场预期（market_expectation）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询机构盈利预测、业绩预测等卖方/机构观点。

## 典型问题

- 比亚迪一致盈利预测净利润是多少？
- 这家公司近期业绩预测是上调还是下调？

## 推荐工具

### 1. stock-profile-getGgYlycData — 个股盈利预测

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getGgYlycData",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. stock-profile-getF10GsjsData — 公司基础档案（辅助）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

## 注意事项

- 盈利预测为多家机构数据汇总，关注一致预期与最新发布机构。
