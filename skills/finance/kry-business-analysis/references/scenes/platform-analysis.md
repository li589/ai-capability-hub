# S11 外卖/团购分析

---
id: S11
name: 外卖团购分析
level: multi
period: weekly/monthly
triggers:
  - 外卖分析
  - 团购分析
  - 美团对账
  - 饿了么对账
  - 抖音外卖
  - 平台收入
  - 外卖佣金
  - 团购核销
  - 平台抽佣多少
---

## 数据计划

### API-1: 外卖对账
- **路径**: `/open/standard/report/takeout/reconciliation/query`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": "1", "pageSize": "1000"}
  }
  ```
- **注意**: 此接口 `pageBean.pageNum/pageSize` 为**字符串**类型，非数字
- **取数字段**: shopName, date, platformName, orderCnt, orderAmt, orderReceivedAmt, itemSaleAmt, shopPromoAmt, deliveryAmt, platformServiceAmt, packAndExtraAmt, totalExpenseAmt
- **用途**: 外卖收入与成本分析
- **注意**: 金额单位为**元**

### API-2: 团购对账
- **路径**: `/open/standard/report/groupCoupon/reconciliation`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopName, couponDate, couponSource, couponName, couponCheckCnt, couponCnt, faceAmt, actualPayAmt, platformServiceAmt, actualReceivedAmt, merchantPromoAmt, platformPromoAmt
- **用途**: 团购核销与收益分析
- **注意**: 金额单位为**分**，展示时 ÷100

### API-3: 营收中外卖占比
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: saleAmt, orderTypeItems → PLATFORM_TAKE_OUT 的 orderAmt
- **用途**: 外卖占总营收比例

---

## 报告模板

### 板块1: 平台收入总览
- **图表类型**: kpi-card
- **数据来源**: API-1 + API-2 + API-3
- **指标**:
  | 指标 | 计算 |
  |------|------|
  | 外卖总收入 | sum(API-1.orderReceivedAmt) |
  | 团购总收入 | sum(API-2.actualReceivedAmt) ÷ 100 |
  | 平台收入占比 | (外卖+团购) / API-3.saleAmt |
  | 外卖订单数 | sum(API-1.orderCnt) |
  | 团购核销张数 | sum(API-2.couponCnt) |

### 板块2: 平台收入对比
- **图表类型**: bar-ranking
- **数据来源**: API-1 + API-2
- **逻辑**:
  1. 按平台分组（美团/饿了么/抖音/口碑）
  2. 各平台总收入对比
- **展示**: 柱状图对比

### 板块3: 外卖利润分析
- **图表类型**: stacked-bar
- **数据来源**: API-1
- **逻辑**:
  - 收入分解: 商品总价 - 商家优惠 - 平台佣金 - 配送费 = 实际收入
  - 按平台分别展示利润构成
- **展示**: 堆叠柱图（正负双向）
  - 正向: 商品总价(itemSaleAmt)
  - 负向: 商家优惠(shopPromoAmt) + 佣金(platformServiceAmt) + 配送(deliveryAmt) + 其他支出

### 板块4: 团购核销分析
- **图表类型**: data-table + pie-doughnut
- **数据来源**: API-2
- **逻辑**:
  1. 按券来源分组汇总
  2. 计算核销率、平台抽佣率
  3. 各平台商家应得占比
- **展示**: 明细表格 + 平台分布饼图

### 板块5: 平台费率对比
- **图表类型**: data-table
- **数据来源**: API-1 + API-2
- **逻辑**:
  | 平台 | 佣金率 | 配送费率 | 商家优惠率 | 综合成本率 |
  |------|--------|---------|-----------|-----------|
  | 计算方式 | 佣金/收入 | 配送/收入 | 优惠/收入 | 总支出/收入 |
- **展示**: 对比表格 + 费率柱图

### 板块6: 平台策略建议
- **图表类型**: 文本
- **AI 生成**:
  1. 各平台投入产出比分析
  2. 佣金率优化建议
  3. 商家优惠策略调整
  4. 是否需要增减平台

---

## AI 分析指令

### 异动判定规则
- 平台综合成本率 > 35% → 利润空间紧张
- 单平台佣金率 > 20% → 佣金偏高
- 外卖占比 > 50% → 过度依赖平台
- 团购核销率 < 60% → 券效率低

### 洞察生成规则
1. 利润分析：哪个平台赚得最多/最少
2. 成本对比：各平台费率结构差异
3. 趋势判断：平台收入占比是否在增长
4. 风险提示：过度依赖某平台的风险

### 建议模板
- 费率优化："{{平台}}佣金率达{{百分比}}%，高于行业均值，建议协商降费或提价覆盖"
- 策略调整："{{平台}}综合成本率{{百分比}}%，净利仅{{金额}}元，建议{{策略}}"
- 结构优化："外卖占比已达{{百分比}}%，建议{{加强/控制}}自有渠道引流"

---

## ECharts 配置

### chart-1: 平台KPI
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 平台收入对比
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-3: 外卖利润分解
- **引用**: charts/_chart-registry.md#stacked-bar

### chart-4: 团购平台分布
- **引用**: charts/_chart-registry.md#pie-doughnut
