# 人物与机构（person）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询公司高管（董事长、总经理、董秘、法人）、机构股东（社保、汇金、证金）、知名自然人股东（牛散）等信息。

## 典型问题

- 贵州茅台董事长是谁？
- 比亚迪高管团队？
- 宁德时代社保基金持仓？
- 哪些机构是这个股票的前十大股东？
- 是否有牛散持仓？

## 推荐工具

### 1. stock-profile-getF10GsjsData — 公司高管与法人信息

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10GsjsData",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. stock-profile-getF10HolderDetailsData — 股东详细信息

- 参数说明：
	- `symbol`：必填，字符串，例如 `SH600519`
	- `type`：可选，整数，`1` 表示十大股东，`2` 表示十大流通股东；不传表示取所有类型

```json
{"name": "stock-profile-getF10HolderDetailsData",
 "params": {"symbol": "<STCODE>", "type": 2}}
```

### 3. stock-profile-getF10JgccmxData — 机构持仓明细（社保/汇金/证金等）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10JgccmxData",
 "params": {"stockCode": "<STCODE>"}}
```

### 4. stock-profile-getF10ShareHolderNumData — 股东户数

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

### 5. stock-profile-getF10ShareStruchgData — 股本结构变动

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

### 6. stock-profile-getF10TbGgMoData — 高管变动等公告

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

## 注意事项

- 高管信息按公司公告口径，可能存在最新任免延迟。
- `getF10HolderDetailsData` 使用的参数名是 `symbol`，不是 `stockCode`。
