# 消费来源分布

## 适用意图

- 消费会员注册来源分布
- 城市/门店/品牌维度会员消费占比排行

## 前置：门店与时间

- 参数规范同消费基础指标
- 占比统计 `dimensionType`：`1` 城市（默认）；`2` 门店；`3` 品牌
- `hasTakeOut`：占比统计默认 `0`

## 输入参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `dimensionType` | `1` | 占比维度 |
| `hasTakeOut` | `0` | 外卖是否参与 |
| `page/size` | `1/10` | 占比排行分页 |

## 固定执行

### 消费会员来源分布

```bash
sl general get-consume-member-source-distribution \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' \
  --format json
```

### 会员消费占比统计

```bash
sl general get-consume-proportion-rank \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"dimensionType":1,"hasTakeOut":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' \
  --format json
```

## 输出字段

**来源分布**

| 字段 | 说明 |
|---|---|
| `totalCount` | 消费会员总人数 |
| `resourceList[].resourceName/count` | 来源名称和人数 |
| `resourcePieList` | 饼图数据 |

**占比排行**

| 字段 | 说明 |
|---|---|
| `list[].dimension` | 维度名称 |
| `turnover` | 营业额 |
| `memberConsumeAmountProportion` | 会员消费金额占比 |
| `memberConsumeCountProportion` | 会员消费笔数占比 |
| `total` | 总条数 |

## 解释规则

1. 来源占比 = `count / totalCount`；分母为 0 不计算。
2. 城市/门店/品牌是不同维度，不可混比。
3. 优先使用接口占比字段。

## 失败处理

| 情况 | 处理 |
|---|---|
| 单接口失败 | 标注失败模块 |
| 空 list | 说明无分布数据 |
| 维度切换 | 须说明 dimensionType |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 消费会员来自哪些渠道 | get-consume-member-source-distribution |
| 各城市会员消费占比 | dimensionType=1 |
| 哪个门店会员消费占比高 | dimensionType=2 |
| 会员消费来源是否集中 | 来源分布 Top 占比 |
