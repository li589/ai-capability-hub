# 复购健康度

## 适用意图

- 21/60/90 天历史回看窗口复购率对比
- 复购健康度、召回窗口判断

## 前置：门店与时间

- 时间：DataCube 左闭右开；21/60/90 天以 `endDate` 为截止点**向前回看**
- 默认分别执行三次 `periodDays=21/60/90`

## 输入参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `startDate` | 是 | 基准统计开始 |
| `endDate` | 是 | 基准统计结束/观察截止，左闭右开 |
| `periodDays` | 是 | `21`、`60`、`90` 分别执行 |
| `omShopCodes` | 否 | 指定门店 |

## 固定执行

```bash
sl datacube task-260506152653001371 --format json --exeTaskId "260506152653000946" \
  --startDate "<yyyy-MM-dd HH:mm:ss>" \
  --endDate "<yyyy-MM-dd HH:mm:ss>" \
  --periodDays "<21|60|90>"
```

指定门店追加 `--omShopCodes "'<omShopCode>'"`。默认执行 21、60、90 三条。

### 图片脚本（用户未拒绝图片时）

```bash
node skills/会员-消费行为分析/scripts/render_repurchase_health_card.js \
  --startDate "<yyyy-MM-dd HH:mm:ss>" \
  --endDate "<yyyy-MM-dd HH:mm:ss>" \
  --outDir "repurchase-health-card-runs"
```

## 输出字段

| 字段 | 说明 |
|---|---|
| `period_days` / `periodDays` | 回看窗口天数 |
| `repurchase_rate` | 周期复购率 |
| `repurchase_member_count` | 复购会员数 |
| `consume_member_count` | 消费会员数 |
| `avg_repurchase_count` | 平均复购次数 |

## 解释规则

1. 复购增益 = 相邻周期 `repurchase_rate` 差值。
2. 21天高且60/90平稳 → 近期健康；21天低但60/90补足 → 召回周期偏长；三周期都低 → 风险较高。
3. 禁止写「未来窗口未走完」口径。

## 失败处理

| 情况 | 处理 |
|---|---|
| 某一 period 失败 | 只输出成功周期 |
| 字段缺失 | 停止确定性结论 |
| 样本过少 | 提示不下长期结论 |

## 路由测试用例

| 用户说法 | 预期行为 |
|---------|---------|
| 21/60/90天复购健康度 | 执行三条 periodDays |
| 复购召回窗口多长 | 比较三周期 repurchase_rate |
| 复购健康度卡片 | 执行 render 脚本 |
| 60天比21天高多少 | 计算复购增益 |
