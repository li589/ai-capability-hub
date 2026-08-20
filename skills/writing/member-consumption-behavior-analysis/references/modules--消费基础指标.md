# 消费基础指标

## 适用意图

- SCRM 消费分析页面汇总：营业额、消费笔数、消费人数、客单价
- 会员/非会员、新老会员拆分

## 前置：门店与时间

- 门店：`shopFilterType=1`，`shopFilterTypeValue=[]` 或 `["<omShopCode>"]`
- 时间：按上层 `SKILL.md` 的「公共规范」，须含 `preBeginDate/preEndDate`

## 输入参数

| 参数 | 说明 | 默认 |
|---|---|---|
| `shopFilterType` | 门店筛选类型 | `1` |
| `shopFilterTypeValue` | 门店编码数组 | `[]` |
| `cardTypeIds` | 卡型 ID 数组 | `[]` |
| `dateType` | 趋势粒度 | `1` |
| `newMemberType` | 新会员定义 | `0` 注册；`1` 首次消费 |
| `beginDate/endDate` | 当前周期 | — |
| `preBeginDate/preEndDate` | 上一周期 | 自动计算 |

## 固定执行

```bash
sl general get-consume-base-info \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' \
  --format json
```

## 输出字段

| 板块 | 关键字段 |
|---|---|
| `turnoverInfo` | 营业额 `totalValue`、环比 `totalFloatRange` |
| `consumeAmountInfo` | 消费笔数 |
| `consumeMemberInfo` | 消费人数 |
| `customerPriceInfo` | 客单价 |
| 各卡片 | `nonMemberValue/Proportion`、`memberValue/Proportion`、`newMemberValue/oldMemberValue` |

## 解释规则

1. 优先使用接口返回的占比字段。
2. 环比用 `totalFloatRangeType/totalFloatRange`。
3. `0` 是合法值；失败/缺失不能解释为 0。

## 失败处理

| 情况 | 处理 |
|---|---|
| 命令失败 | 说明缺少核心汇总 |
| 空对象 | 说明当前筛选无数据 |
| 字段缺失 | 标注缺失 |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 近一周消费表现 | 执行 get-consume-base-info |
| 会员和非会员消费各占多少 | 读取 member/nonMember 拆分 |
| 客单价多少 | 读取 customerPriceInfo |
| 新会员消费贡献 | 读取 newMemberValue |
