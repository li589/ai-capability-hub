# S6 门店日报

---
id: S6
name: 门店日报
level: store
period: daily
triggers:
  - 门店日报
  - 今天店里怎么样
  - 本店经营情况
  - 今日营业数据
  - 店长日报
---

## 数据计划

### API-1: 门店营收
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": ["{{currentShopId}}"],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, orderPeopleCnt, reopenTableRate, openTableCnt, openTableRate, avgDiningDuration, orderTypeItems
- **用途**: 核心指标 + 订单类型

### API-2: 门店营收（前日对比）
- **路径**: 同 API-1，dateRange 改为 {{dayBeforeYesterday}}
- **用途**: 环比计算

### API-3: 收入构成
- **路径**: `/open/standard/report/business/income/constitute/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": ["{{currentShopId}}"],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: businessIncomeItems
- **用途**: 收入构成饼图

### API-4: 支付方式
- **路径**: `/open/standard/report/paymethod/statistics`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": ["{{currentShopId}}"],
    "periodType": "BY_DAY",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: payMethodName, actualReceivedAmt, payCntTotal
- **用途**: 支付方式分布

### API-5: 就餐人数分析
- **路径**: `/open/standard/report/dinner/numberAnalysis`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": ["{{currentShopId}}"],
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: peopleCnt, orderReceivedAmt, busiOrderNoCount, perCapitaPost
- **用途**: 客流画像

### API-6: 取餐叫号（快餐适用）
- **路径**: `/open/standard/report/CdsOrderDetailClient/statistics`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": ["{{currentShopId}}"],
    "pickFlag": false,
    "orgStatisticsType": "BY_SHOP",
    "orderSourceList": ["POS", "WECHAT_MINI_PROGRAM", "ALIPAY_MINI_PROGRAM", "PAD"],
    "orderTypeList": ["FOR_HERE"],
    "pageBean": {"pageNum": 1, "pageSize": 10}
  }
  ```
- **注意**: `pickFlag`/`orgStatisticsType`/`orderSourceList`/`orderTypeList` 为必填；pageSize 最大 10
- **取数字段**: orderCnt, calledOrderCnt, calledOrderRate, pickedOrderCnt, pickedOrderRate
- **用途**: 叫号取餐效率（仅快餐业态）

---

## 报告模板

### 板块1: 今日经营快照
- **图表类型**: kpi-card
- **数据来源**: API-1 + API-2
- **指标**:
  | 指标 | 字段 | 环比 |
  |------|------|------|
  | 营业额 | saleAmt | ✓ |
  | 营业收入 | businessIncomeAmt | ✓ |
  | 订单数 | orderCnt | ✓ |
  | 折后客单价 | avgCustomerAmtAfterDiscount | ✓ |
  | 就餐人数 | orderPeopleCnt | ✓ |
  | 翻台率 | reopenTableRate | ✓ |
  | 开台数 | openTableCnt | ✓ |
  | 平均就餐时长 | avgDiningDuration | — |

### 板块2: 订单类型构成
- **图表类型**: pie-doughnut
- **数据来源**: API-1 → orderTypeItems
- **逻辑**: 堂食/外带/外卖金额占比
- **展示**: 环形图

### 板块3: 客流画像
- **图表类型**: bar-ranking
- **数据来源**: API-5
- **逻辑**: 不同就餐人数的订单分布
- **展示**: 柱状图（1人桌/2人桌/3人桌/4人+桌 各多少单）

### 板块4: 收入构成
- **图表类型**: pie-doughnut
- **数据来源**: API-3
- **展示**: 饼图

### 板块5: 支付方式分布
- **图表类型**: pie-doughnut
- **数据来源**: API-4
- **展示**: 环形图

### 板块6: 叫号取餐效率（快餐业态）
- **图表类型**: funnel
- **数据来源**: API-6
- **逻辑**: 下单总数 → 已叫号 → 已取餐
- **展示**: 漏斗图
- **条件**: 仅快餐业态门店展示

### 板块7: 今日小结
- **图表类型**: 文本
- **AI 生成**: 2~3 条简短洞察

---

## AI 分析指令

### 异动判定规则
- 环比昨日 ±15% → 标记变化
- 翻台率 < 1.0 → 翻台率偏低
- 客单价环比下降 >10% → 可能存在大额优惠

### 洞察生成规则
1. 简短有力，适合店长快速阅读
2. 每条不超过 30 字
3. 必须包含数据支撑
4. 最多 3 条

---

## ECharts 配置

### chart-1: 经营快照
- **引用**: charts/_chart-registry.md#kpi-card
- **指标数**: 8

### chart-2: 订单类型
- **引用**: charts/_chart-registry.md#pie-doughnut

### chart-3: 客流分布
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-4: 收入构成
- **引用**: charts/_chart-registry.md#pie-doughnut

### chart-5: 叫号漏斗
- **引用**: charts/_chart-registry.md#funnel
