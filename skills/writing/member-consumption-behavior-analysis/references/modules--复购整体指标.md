# 复购整体指标

## 适用意图

- 消费会员数、消费1次/2次及以上会员及占比
- 复购率趋势、新老会员结构、次数分布、复购排行

## 前置：门店与时间

- 门店：`shopFilterType=1`，`shopFilterTypeValue`
- `repurchaseMode`：默认 `1` 实际消费次数；市别汇总用 `2`
- 须用 `--params '<完整 JSON>' --format json`，不可拆成多个 flag
- 直接执行 `sl general` 时日期须用 `yyyy-MM-dd HH:mm:ss`；推荐批量查询脚本可接受 `yyyy-MM-dd` 并自动补齐起止时间。

## 输入参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `repurchaseMode` | `1` | 复购模式 |
| `dimensionType` | `2` | 排行：1门店/2城市/3品牌 |
| `page/size` | `1/10` | 排行分页 |

## 固定执行

> **推荐批量查询**：`node "skills/会员-消费行为分析/scripts/batch_repurchase_metrics.mjs" --beginDate "<beginDate>" --endDate "<endDate>" --preBeginDate "<preBeginDate>" --preEndDate "<preEndDate>"` 可一次同时获取下述 5 条查询。可选参数：`--shopFilterTypeValue`、`--repurchaseMode`。
> 若脚本不可用，退回下方逐条执行。

### 1. 复购核心指标

```bash
sl general get-data-indicators \
  --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' \
  --format json
```

### 2. 复购增长趋势

```bash
sl general get-re-purchase-growth-trend \
  --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' \
  --format json
```

### 3. 复购群体趋势

```bash
sl general get-re-purchase-group-trend \
  --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' \
  --format json
```

### 4. 复购次数分布

```bash
sl general get-repurchase-frequency-data \
  --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1}' \
  --format json
```

### 5. 复购会员排行

```bash
sl general get-ranking-repurchase-members \
  --params '{"beginDate":"<beginDate>","endDate":"<endDate>","preBeginDate":"<preBeginDate>","preEndDate":"<preEndDate>","dateType":1,"shopFilterType":1,"shopFilterTypeValue":[],"repurchaseMode":1,"dimensionType":2,"page":1,"size":10}' \
  --format json
```

## 输出字段

| 接口 | 关键字段 |
|---|---|
| 核心指标 | `consumeMemberCount`、`onceConsumeMemberCount/Ratio`、`twiceConsumeMemberCount/Ratio` |
| 增长趋势 | `dateList`、`repurchaseRatioList` |
| 群体趋势 | `totalMemberCount`、`newMemberCount`、`oldMemberCount` |
| 次数分布 | `frequencyList`、`countList` |
| 排行 | `list[].repurchaseRatio`、`consumeMemberCount` |

## 解释规则

1. 复购率优先用 `repurchaseRatioList` 或排行 `repurchaseRatio`。
2. 次数分布两数组长度不一致时停止解释。
3. 排行维度不可混排比较。

## 失败处理

| 情况 | 处理 |
|---|---|
| 核心指标失败 | 可继续趋势，须标注缺汇总 |
| 单接口失败 | 标注失败模块 |
| 空列表 | 说明无复购数据 |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 复购率怎么样 | 核心指标+增长趋势 |
| 消费2次及以上占比 | 读取 twiceConsumeMemberRatio |
| 复购次数分布 | get-repurchase-frequency-data |
| 哪个城市复购率高 | 排行 dimensionType=2 |
