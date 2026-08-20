# 商品偏好排行

## 适用意图

- 会员消费商品/类别排行
- 会员点单偏好、喜好指数

## 前置：门店与时间

- 参数规范同消费基础指标
- `itemType`：`0` 商品名称（默认）；`1` 类别名称
- `sortField`：`1` 点单笔数；`2` 消费笔数；`order`：`1` 正序；`2` 倒序

## 输入参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `itemType` | `0` | 排行维度 |
| `sortField/order` | `null` | 排序 |
| `page/size` | `1/10` | 分页 |

## 固定执行

```bash
sl general get-product-rank \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"itemType":0,"sortField":null,"order":null,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","page":1,"size":10}' \
  --format json
```

## 输出字段

| 字段 | 说明 |
|---|---|
| `list[].itemName` | 商品或类别名称 |
| `saleAmount` | 销售金额 |
| `memberBillCount` | 会员点单笔数 |
| `memberConsumeCount` | 会员消费笔数 |
| `memberPreferencePercent` | 喜好指数 |
| `total` | 总条数 |

## 解释规则

1. 喜好指数按接口返回，不自行定义。
2. 默认展示 Top 项；用户要求类别时 `itemType=1`。
3. 当前页不等于全量排行。

## 失败处理

| 情况 | 处理 |
|---|---|
| 命令失败 | 说明排行不可用 |
| 空 list | 说明无商品数据 |
| total=0 | 合法空结果 |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 会员最爱点什么 | itemType=0 |
| 哪个类别会员消费多 | itemType=1 |
| 会员商品偏好 TOP10 | page=1,size=10 |
| 喜好指数最高的菜 | 按 memberPreferencePercent 排序解读 |
