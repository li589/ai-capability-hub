# S2 经营周报

---
id: S2
name: 经营周报
level: brand
period: weekly
triggers:
  - 经营周报
  - 本周经营总结
  - 周报
  - 这周表现怎么样
  - 上周经营情况
---

## 数据计划

### API-1: 本周日趋势（品牌汇总）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisWeekStart}}", "endDate": "{{thisWeekEnd}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: date, saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, orderPeopleCnt, reopenTableRate
- **用途**: 日营收趋势折线图 + 周度汇总

### API-2: 上周日趋势（品牌汇总，用于同比）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{lastWeekStart}}", "endDate": "{{lastWeekEnd}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: 同 API-1
- **用途**: 上周对比线 + 环比计算

### API-3: 门店排行（本周汇总）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisWeekStart}}", "endDate": "{{thisWeekEnd}}"},
    "shopIds": [],
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopId, shopName, saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, reopenTableRate
- **用途**: 门店多维排行

### API-4: 优惠构成统计
- **路径**: `/open/standard/report/business/income/promo/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisWeekStart}}", "endDate": "{{thisWeekEnd}}"},
    "shopIds": [],
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: orderPromoItems, paymentPromoItems, orderExpenseItems
- **用途**: 优惠使用分析

### API-5: 菜品销售 Top10
- **路径**: `/open/standard/report/orderItem/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisWeekStart}}", "endDate": "{{thisWeekEnd}}"},
    "shopIds": [],
    "countLatitude": {"countCollectType": 0, "countType": 1},
    "sellLatitude": {"sellCollectType": false, "countType": "SINGLE_PACKAGE"}
    "orderSourceCondition": {"orderSourceType": 0},
    "orderTypeCondition": {"orderType": 0},
    "goodsTempFlag": 0,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: values[].item[].name, salePrice, actualAmt, goodsSpotQty, returnCnt, returnRatio
- **用途**: 菜品排行 + 退菜预警

### API-6: 套餐销售统计
- **路径**: `/open/standard/report/combo/sale/statistics`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisWeekStart}}", "endDate": "{{thisWeekEnd}}"},
    "shopIds": [],
    "countType": 1,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: `countType` 必填（1=按套餐汇总）
- **取数字段**: comboName, itemSalePrice, itemSaleQty, actualAmt
- **用途**: 套餐表现

---

## 报告模板

### 板块1: 周度总览
- **图表类型**: kpi-card
- **数据来源**: API-1 汇总 + API-2 汇总
- **指标清单**:
  | 指标名 | 计算方式 | 环比 |
  |--------|---------|------|
  | 本周营业额 | sum(API-1.saleAmt) | vs 上周总额 |
  | 本周营业收入 | sum(API-1.businessIncomeAmt) | vs 上周 |
  | 本周订单数 | sum(API-1.orderCnt) | vs 上周 |
  | 周均客单价 | avg(API-1.avgCustomerAmtAfterDiscount) | vs 上周 |
  | 本周就餐人数 | sum(API-1.orderPeopleCnt) | vs 上周 |
  | 平均翻台率 | avg(API-1.reopenTableRate) | 差值对比 |

### 板块2: 日营收趋势
- **图表类型**: line-trend
- **数据来源**: API-1 + API-2
- **逻辑**:
  - X轴: 周一~周日（7天）
  - 本周线: API-1 各日 saleAmt
  - 上周线: API-2 各日 saleAmt（虚线对比）
- **展示**: 双线折线图，面积填充

### 板块3: 门店表现排行
- **图表类型**: bar-ranking + data-table
- **数据来源**: API-3
- **逻辑**:
  1. 多维排行表格：营业额/客单价/翻台率/订单数
  2. Top5 柱状图（营业额维度）
  3. 异动门店标记（环比 > ±20%）
- **展示**: 上方柱状图 + 下方排行表格

### 板块4: 菜品 Top10 & 退菜预警
- **图表类型**: bar-ranking + 预警列表
- **数据来源**: API-5
- **逻辑**:
  1. 按 actualAmt 降序取 Top10 → 柱状图
  2. 按 returnRatio 降序取 Top5 退菜率 → 红色预警列表
- **展示**: 左侧销售排行 + 右侧退菜预警

### 板块5: 优惠使用分析
- **图表类型**: stacked-bar
- **数据来源**: API-4
- **逻辑**:
  1. 订单优惠 (orderPromoItems.subTotal)
  2. 支付优惠 (paymentPromoItems.subTotal)
  3. 订单支出 (orderExpenseItems.subTotal)
  4. 计算优惠占营业额比例
- **展示**: 堆叠柱图 + 占比标注

### 板块6: 套餐表现
- **图表类型**: data-table
- **数据来源**: API-6
- **逻辑**: 按 actualAmt 降序排列套餐
- **展示**: 表格（套餐名/销量/金额/收入）

### 板块7: 本周洞察 + 下周建议
- **图表类型**: insight-card + action-card
- **AI 生成**:
  - **洞察** (insight-card): 3~5 条，每条标注 good/warn/info/risk
  - **建议** (action-card): 2~3 条，每条带 P1/P2 优先级
  - 覆盖维度：营收趋势 > 门店差异 > 菜品变化 > 优惠力度
- **展示**: 分色洞察卡片 + 下方行动卡片

---

## AI 分析指令

### 异动判定规则
- 周环比涨跌 ±10% → 「显著变化」
- 周环比涨跌 ±25% → 「异常波动」
- 本周内连续4天下降 → 「持续下滑趋势」
- 周末(周六日)营收 > 工作日均值×1.5 → 正常
- 周末营收 < 工作日均值 → 「周末表现低迷」

### 洞察生成规则
1. 必须对比上周同期数据
2. 每条洞察格式：「[现象]：[数据]，[原因分析]」
3. 覆盖维度：营收趋势 > 门店差异 > 菜品变化 > 优惠力度
4. 建议维度：门店运营 > 菜品调整 > 营销策略

### 下周建议模板
- "建议{{动作}}，原因：{{依据}}，预期效果：{{目标}}"
- 示例："建议加大周中营销活动力度，原因：本周周中日均营收仅为周末的45%，预期提升周中客流15%"

---

## ECharts 配置

### chart-1: 周度KPI卡片
- **引用**: charts/_chart-registry.md#kpi-card
- **指标数**: 6

### chart-2: 日营收趋势
- **引用**: charts/_chart-registry.md#line-trend
- **系列数**: 2（本周 + 上周）
- **X轴**: 周一~周日

### chart-3: 门店排行
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据**: Top5 门店 saleAmt

### chart-4: 菜品Top10
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据**: Top10 菜品 actualAmt

### chart-5: 优惠构成
- **引用**: charts/_chart-registry.md#stacked-bar
- **分类**: 订单优惠/支付优惠/订单支出

### chart-6: 本周洞察
- **引用**: charts/_chart-registry.md#insight-card
- **分类**: good / warn / info / risk
- **数量**: 3~5 条

### chart-7: 下周建议
- **引用**: charts/_chart-registry.md#action-card
- **优先级**: P1 / P2
