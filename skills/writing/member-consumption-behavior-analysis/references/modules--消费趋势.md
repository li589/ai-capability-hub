# 消费趋势

## 适用意图

- 会员/非会员消费金额、笔数、客单价趋势

## 前置：门店与时间

- 参数规范同「消费基础指标」
- `hasTakeOut`：金额/笔数趋势默认 `0`；用户要求外卖参与时传 `1`
- 命令名须保持 `comsume` 拼写，不可改为 `consume`

## 输入参数

通用 `--params` 含 `shopFilterType`、`shopFilterTypeValue`、`cardTypeIds`、`dateType`、`newMemberType`、`beginDate`、`endDate`、`preBeginDate`、`preEndDate`、`hasTakeOut`（金额/笔数）。

## 固定执行

### 消费金额趋势

```bash
sl general get-comsume-amount-analysis \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"hasTakeOut":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' \
  --format json
```

### 消费笔数趋势

```bash
sl general get-comsume-nums-analysis \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"hasTakeOut":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' \
  --format json
```

### 消费客单价趋势

```bash
sl general get-unit-price-analysis \
  --params '{"shopFilterType":1,"shopFilterTypeValue":[],"cardTypeIds":[],"dateType":1,"newMemberType":0,"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>"}' \
  --format json
```

## 输出字段

| 接口 | 字段 |
|---|---|
| 金额 | `dateList`、`memberConsumeAmountList`、`notMemberConsumeAmountList` |
| 笔数 | `dateList`、`memberConsumeNumsList`、`notMemberConsumeNumsList` |
| 客单价 | `dateList`、`memberUnitPriceList`、`notMemberUnitPriceList` |

## 解释规则

1. 只有 `dateList` 与序列长度一致时才按下标解释。
2. 客单价优先用接口值，不用金额/笔数重算覆盖。
3. 识别高低点和异常波动。

## 失败处理

| 情况 | 处理 |
|---|---|
| 单接口失败 | 标注失败趋势类型 |
| 空数组 | 说明无趋势点 |
| 序列长度不一致 | 标注异常 |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 消费金额趋势 | get-comsume-amount-analysis |
| 会员消费笔数变化 | get-comsume-nums-analysis |
| 客单价涨还是跌 | get-unit-price-analysis |
| 会员非会员消费对比趋势 | 金额+笔数两条 |
