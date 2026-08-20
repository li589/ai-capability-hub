# 股东与股本结构（shareholder）

> 本文件用于高级显式工具模式。基础查询可以只向 `dzh-data-query` 传入完整 `query`，由服务端自动选择工具；需要精确控制工具和参数时再使用本文件。

## 适用场景

查询股东户数、十大股东、机构持股、股本结构变动、限售解禁等。

## 典型问题

- 贵州茅台股东户数是多少？
- 比亚迪十大流通股东是谁？
- 宁德时代机构持仓占比？
- 最近一次股本变动情况？
- 解禁/限售情况如何？

## 推荐工具

### 1. stock-profile-getF10ShareHolderNumData — 股东户数

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10ShareHolderNumData",
 "params": {"stockCode": "<STCODE>"}}
```

### 2. stock-profile-getF10ShareStruchgData — 股本结构变动

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10ShareStruchgData",
 "params": {"stockCode": "<STCODE>"}}
```

### 3. stock-profile-getF10JgccmxData — 机构持仓明细

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

```json
{"name": "stock-profile-getF10JgccmxData",
 "params": {"stockCode": "<STCODE>"}}
```

### 4. stock-profile-getF10GsjsData — 公司基础档案（用于补充总股本/流通股）

- 参数说明：
	- `stockCode`：必填，字符串，例如 `SH600519`

### 5. stock-profile-getF10HolderDetailsData — 十大股东 / 十大流通股东

- 参数说明：
	- `symbol`：必填，字符串，例如 `SH600519`
	- `type`：可选，整数，`1` 十大股东，`2` 十大流通股东

```json
{"name": "stock-profile-getF10HolderDetailsData",
 "params": {"symbol": "<STCODE>", "type": 1}}
```

## 注意事项

- 股东户数、机构数等计数字段通常按整数理解。
- `getF10HolderDetailsData` 的参数名是 `symbol`，与其他多数工具使用的 `stockCode` 不同。
