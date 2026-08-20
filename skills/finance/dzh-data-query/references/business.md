# 经营业务（business）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询主营业务构成、产品占比、地区收入、出口/海外收入、经营范围。

## 典型问题

- 贵州茅台主营业务是什么？
- 比亚迪海外收入占比多少？
- 宁德时代不同产品线收入构成？
- 五粮液主要销售区域有哪些？

## 推荐工具

### 1. stock-profile-getF10BusiinfoData — 主营业务/产品/地区构成

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`
	- `typeStyle`：可选，整数，`1` 行业、`2` 产品、`3` 地区；不传取所有类型

```json
{"name": "stock-profile-getF10BusiinfoData",
 "params": {"stockCode": "<STCODE>", "typeStyle": 2}}
```

### 2. stock-profile-getF10Information — 公司经营范围、概念题材

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10Information",
 "params": {"stockCode": "<STCODE>"}}
```

### 3. stock-profile-getF10GsjsData — 公司档案（业务范围辅助）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

## 注意事项

- 主营业务构成数据按报告期发布，请在 query 中标明所需报告期。
- `typeStyle` 是整数枚举，不要写成中文字符串或自定义字段。
