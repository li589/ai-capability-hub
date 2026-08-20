# 公告事件（event）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询上市公司公告、回购、增持/减持、重组、停复牌、收购、股东大会、摘帽等事件。

## 典型问题

- 贵州茅台最近有哪些公告？
- 比亚迪最近回购情况？
- 宁德时代是否有重大重组？
- 这个股票最近股东大会议案？
- 是否有停复牌信息？

## 推荐工具

### 1. stock-profile-getF10TbGgMoData — 公司重大公告/事件

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10TbGgMoData",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. stock-profile-getF10TnwData — 公司新闻/事件流

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10TnwData",
 "params": {"stockCode": "<STCODE>"}}
```

### 3. stock-profile-getF10GsjsData — 公司基础档案（辅助识别）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

## 注意事项

- 涉及"最近 / 近 N 日"等表述时，请在 query 中尽量明确时间范围。
