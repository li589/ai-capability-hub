# S1 经营日报

---
id: S1
name: 经营日报
level: brand
period: daily
triggers:
  - 经营日报
  - 每日经营概览
  - 今天生意怎么样
  - 昨天营业额多少
  - 日报
  - 早报
  - 今日总结
---

## 数据计划

### API-1: 店内营收统计（品牌汇总）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: saleAmt, businessIncomeAmt, totalPromoAmt, promoAmtProportion, orderCnt, avgCustomerAmtAfterDiscount, avgCustomerAmtPreDiscount, orderPeopleCnt, reopenTableRate, openTableRate, orderTypeItems
- **用途**: 核心指标卡片 + 订单类型构成

### API-2: 店内营收统计（门店维度）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopId, shopName, saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, reopenTableRate
- **用途**: 门店排行

### API-3: 店内营收统计（前日对比）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{dayBeforeYesterday}}", "endDate": "{{dayBeforeYesterday}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: 同 API-1
- **用途**: 环比计算

### API-4: 收入构成统计
- **路径**: `/open/standard/report/business/income/constitute/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: businessIncomeItems (itemList[].name, itemList[].amount, subTotal)
- **用途**: 收入构成饼图

### API-5: 支付方式收款统计
- **路径**: `/open/standard/report/paymethod/statistics`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{yesterday}}", "endDate": "{{yesterday}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: payMethodName, actualReceivedAmt, payCntTotal
- **用途**: 支付方式分布

---

## 报告模板

### 板块1: 核心指标卡片
- **图表类型**: kpi-card
- **数据来源**: API-1 + API-3（环比）
- **指标清单**:
  | 指标名 | 字段 | 单位 | 环比计算 |
  |--------|------|------|---------|
  | 营业额 | saleAmt | 元 | (今-昨)/昨×100% |
  | 营业收入 | businessIncomeAmt | 元 | 同上 |
  | 订单数 | orderCnt | 笔 | 同上 |
  | 折后客单价 | avgCustomerAmtAfterDiscount | 元 | 同上 |
  | 就餐人数 | orderPeopleCnt | 人 | 同上 |
  | 翻台率 | reopenTableRate | % | 差值 |

### 板块2: 门店排行 Top5 / Bottom5
- **图表类型**: bar-ranking
- **数据来源**: API-2
- **逻辑**:
  1. 按 saleAmt 降序排列
  2. 取前5名为 Top5（高亮蓝色）
  3. 取后5名为 Bottom5（高亮红色）
  4. 标注门店名 + 营业额
- **展示**: 上下两组横向柱状图

### 板块3: 订单类型构成
- **图表类型**: pie-doughnut
- **数据来源**: API-1 → orderTypeItems
- **逻辑**:
  1. 遍历 orderTypeItems.itemList[]
  2. 取每个类型（堂食/外带/外卖）的 orderAmt 指标
  3. 计算各类型占比
- **展示**: 环形图 + 右侧图例

### 板块4: 收入构成明细
- **图表类型**: pie-doughnut
- **数据来源**: API-4 → businessIncomeItems
- **逻辑**:
  1. 遍历 businessIncomeItems.itemList[]
  2. 每项 {name, amount} 作为扇区
- **展示**: 饼图

### 板块5: 支付方式分布
- **图表类型**: pie-doughnut
- **数据来源**: API-5
- **逻辑**:
  1. 按 actualReceivedAmt 降序
  2. 前 5 大支付方式独立展示
  3. 其余合并为"其他"
- **展示**: 环形图

### 板块6: 今日洞察
- **图表类型**: insight-card
- **数据来源**: 综合 API-1 ~ API-5
- **AI 生成**:
  1. 3~5 条洞察，每条标注分类：good / warn / info / risk
  2. 每条必须有数据支撑
  3. 优先级：营业额异动 > 客单价异动 > 订单数异动 > 羻台率异动
- **展示**: 分色洞察卡片（insight-card 样式）

---

## AI 分析指令

### 异动判定规则
- 环比涨跌超过 ±15% → 「显著变化」
- 环比涨跌超过 ±30% → 「需重点关注」
- 单店营业额为0 → 「疑似歇业/异常」

### 洞察生成规则
1. 优先级：营业额异动 > 客单价异动 > 订单数异动 > 翻台率异动
2. 每条洞察格式：「[指标] [变化描述]，[数据对比]，[可能原因/建议]」
3. 示例：
   - "营业额环比上涨23%，从8.5万增至10.5万，主要由外卖订单增长贡献"
   - "门店「XX店」营业额为0，可能存在歇业或数据异常，建议确认"
4. 最多5条，按影响度排序

### 结论模板
报告末尾需输出一句话总结：
- 正面："昨日整体表现{{评价}}，营业额{{金额}}元，环比{{方向}}{{百分比}}%，{{亮点}}"
- 负面："昨日营业额{{金额}}元，环比下降{{百分比}}%，{{关注点}}需重点跟进"

---

## ECharts 配置

### chart-1: 核心指标卡片
- **引用**: charts/_chart-registry.md#kpi-card
- **指标数**: 6

### chart-2: 门店排行
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据映射**:
  - categories = 门店名称（Top5 + Bottom5）
  - values = saleAmt
  - valueFormat = '{value}元'

### chart-3: 订单类型构成
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据映射**:
  - data = orderTypeItems 各类型 orderAmt
  - style = doughnut

### chart-4: 收入构成
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据映射**:
  - data = businessIncomeItems.itemList[]
  - style = pie

### chart-5: 支付方式分布
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据映射**:
  - data = paymethod Top5 + 其他
  - style = doughnut

### chart-6: 今日洞察
- **引用**: charts/_chart-registry.md#insight-card
- **分类**: good / warn / info / risk
- **数量**: 3~5 条
