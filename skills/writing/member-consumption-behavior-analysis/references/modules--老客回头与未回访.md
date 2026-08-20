# 老客回头与未回访

## 适用意图

- 30/60/90天老客复购率及趋势
- 平均复购周期、活跃期未回访概览与名单

## 前置：门店与时间

- `endDate` 左闭右开；用户说「本月」默认 startDate 本月1日，endDate 下月1日
- 未回访：活跃期与回访观察期须在回复中分别说明

## 输入参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `endDate` | — | 复购分析截止 |
| `periodDays` | `30,60,90` | 复购率/周期窗口 |
| `activeStartDate/activeEndDate` | 上月至本月 | 未回访活跃期 |
| `returnStartDate/returnEndDate` | 本月 | 未回访观察期 |
| `highValueAmount` | `1000` | 高价值阈值（元） |
| `highFrequencyCount` | `3` | 高频阈值（次） |
| `limit` | `200` | 名单上限 |
| `omShopCodes` | — | 指定门店 |

## 固定执行

> **推荐批量查询**：`node "skills/会员-消费行为分析/scripts/batch_return_visit.mjs" --startDate "<startDate>" --endDate "<endDate>"` 可一次同时获取下述 4 条查询，耗时从串行 ~1s 降至 ~240ms。可选参数：`--periodDays`、`--activeStartDate`、`--activeEndDate`、`--returnStartDate`、`--returnEndDate`、`--highValueAmount`、`--highFrequencyCount`、`--limit`、`--omShopCodes`。
> 若脚本不可用，退回下方逐条执行。

### 1. 老客复购率趋势

```bash
sl datacube task-260514155605001415 --format json \
  --exeTaskId "260514155605000986" \
  --endDate "<endDate>" --periodDays "<30|60|90>"
```

### 2. 老客平均复购周期

```bash
sl datacube task-260514160503001416 --format json \
  --exeTaskId "260514160503000987" \
  --endDate "<endDate>" --periodDays "<30|60|90>"
```

### 3. 活跃期未回访概览

```bash
sl datacube task-260514161156001417 --format json \
  --exeTaskId "260514161156000988" \
  --activeStartDate "<activeStartDate>" --activeEndDate "<activeEndDate>" \
  --returnStartDate "<returnStartDate>" --returnEndDate "<returnEndDate>"
```

### 4. 活跃期未回访名单

```bash
sl datacube task-260514161219001418 --format json \
  --exeTaskId "260514161219000989" \
  --activeStartDate "<activeStartDate>" --activeEndDate "<activeEndDate>" \
  --returnStartDate "<returnStartDate>" --returnEndDate "<returnEndDate>" \
  --highValueAmount "<highValueAmount>" --highFrequencyCount "<highFrequencyCount>" \
  --limit "<limit>"
```

指定门店时四条均追加 `--omShopCodes "'<omShopCode>'"`。

## 输出字段

| 模块 | 关键字段 |
|---|---|
| 复购率 | `repurchase_rate`、`window_label`、`base_member_count` |
| 复购周期 | `avg_repurchase_cycle_days`、`cycle_member_count` |
| 未回访概览 | `not_return_member_count`、`not_return_rate`、`not_return_active_consume_amount` |
| 未回访名单 | `mem_name`、`mem_mobile`（脱敏）、`not_return_level`、`active_consume_amount` |

## 解释规则

1. 复购率趋势差值 = 当前窗口 - 上一窗口 `repurchase_rate`。
2. 周期变长（差值为正）表示复购变慢。
3. 高优先级名单：`not_return_level = HIGH_VALUE_NOT_RETURN`。
4. 名单为空但概览有未回访人数 → 检查 limit/阈值。

## 失败处理

| 情况 | 处理 |
|---|---|
| 某 period 为空 | 不用其它周期估算 |
| 名单截断 | 标注 limit 影响 |
| 展示明细 | 手机号脱敏 |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 会员回头率怎么样 | 复购率 30/60/90 |
| 老客平均多久来一次 | 复购周期查询 |
| 有多少老客没回来 | 未回访概览 |
| 要优先唤回哪些老客 | 未回访名单 |
