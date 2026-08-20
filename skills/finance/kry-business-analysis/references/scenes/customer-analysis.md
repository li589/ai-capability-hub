# S8 客流消费分析

---
id: S8
name: 客流消费分析
level: store
period: weekly/monthly
triggers:
  - 客流分析
  - 客单价分析
  - 人均消费
  - 就餐人数
  - 桌均消费
  - 翻台率分析
  - 客流趋势
  - 哪种桌消费最高
---

## 数据计划

### API-1: 就餐人数分析（按人数）
- **路径**: `/open/standard/report/dinner/numberAnalysis`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: peopleCnt, orderReceivedAmt, orderAmt, promoAmt, busiOrderNoCount, perCapitaPre, perCapitaPost, openTableCnt
- **用途**: 就餐人数分布 + 人均消费

### API-2: 桌台类型分析
- **路径**: `/open/standard/report/dinner/tableTypeAnalysis`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: orderReceivedAmt, orderAmt, orderPeopleCnt, perCapitaPre, perCapitaPost, busiOrderNoCount(动态字段名)
- **用途**: 散台/包厢/宴会桌对比

### API-3: 桌均消费区间
- **路径**: `/open/standard/report/order/table-avg/page`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "tableAvgCountType": "CUSTOMER_AMT",
    "statisticsByShop": false,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: `tableAvgCountType` 必填（“CUSTOMER_AMT”=按客单价区间），`statisticsByShop` 必填
- **取数字段**: range, orderPeopleCnt, openTableCnt, orderCnt, orderAmt, orderReceiveAmt, orderCntRatio, orderAmtRatio
- **用途**: 消费区间分布

### API-4: 客单价趋势（多日）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: date, avgCustomerAmtAfterDiscount, avgCustomerAmtPreDiscount, orderPeopleCnt, orderCnt, reopenTableRate
- **用途**: 客单价 + 客流日趋势

---

## 报告模板

### 板块1: 客流总览
- **图表类型**: kpi-card
- **数据来源**: API-4 汇总
- **指标**:
  | 指标 | 计算 |
  |------|------|
  | 总就餐人数 | sum(orderPeopleCnt) |
  | 日均客流 | avg(orderPeopleCnt) |
  | 平均客单价(折后) | avg(avgCustomerAmtAfterDiscount) |
  | 平均客单价(折前) | avg(avgCustomerAmtPreDiscount) |
  | 平均翻台率 | avg(reopenTableRate) |

### 板块2: 客流与客单价趋势
- **图表类型**: line-trend
- **数据来源**: API-4
- **逻辑**:
  - 主Y轴: 客流人数(柱状)
  - 副Y轴: 客单价(折线)
  - X轴: 日期
- **展示**: 柱线混合图

### 板块3: 就餐人数分布
- **图表类型**: bar-ranking
- **数据来源**: API-1
- **逻辑**:
  - X轴: 就餐人数（1人/2人/3人/4人/5人+）
  - Y轴: 订单笔数 + 人均消费标注
- **展示**: 竖向柱状图，柱顶标注人均消费

### 板块4: 桌均消费区间分布
- **图表类型**: bar-ranking (histogram)
- **数据来源**: API-3
- **逻辑**:
  - X轴: 消费区间（0~50 / 50~100 / 100~200 / 200~500 / 500+）
  - Y轴: 订单数占比
  - 标注: 营业额占比
- **展示**: 直方图 + 双轴标注

### 板块5: 桌台类型消费对比
- **图表类型**: radar
- **数据来源**: API-2
- **逻辑**:
  - 各桌台类型（散台/包厢/宴会）
  - 4维度: 营业收入/人均消费/订单数/客流
  - 归一化对比
- **展示**: 雷达图

### 板块6: 客群洞察
- **图表类型**: 文本
- **AI 生成**:
  1. 主力客群画像（几人桌贡献最大）
  2. 高价值客群识别（哪个区间贡献最多营收）
  3. 翻台率优化建议
  4. 客单价提升策略

---

## AI 分析指令

### 异动判定规则
- 客单价连续3天下降 → 趋势预警
- 某就餐人数段订单占比 > 40% → 客群集中
- 桌均消费 0~50 区间占比 > 30% → 低消费预警
- 翻台率 < 平均值×0.7 → 效率偏低

### 洞察生成规则
1. 识别主力客群（贡献最大的就餐人数段）
2. 识别高价值客群（人均消费最高的桌台类型）
3. 对比周末vs工作日客流差异
4. 提出针对性提升建议（套餐设计/桌台优化/时段运营）

### 建议维度
- 客单价提升："{{就餐人数}}人桌人均仅{{金额}}元，建议设计{{类型}}套餐拉升"
- 翻台率提升："平均就餐时长偏长，建议优化{{环节}}"
- 客群拓展："{{客群}}占比偏低，建议通过{{渠道}}引流"

---

## ECharts 配置

### chart-1: 客流KPI
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 客流趋势
- **引用**: charts/_chart-registry.md#line-trend (混合柱线)

### chart-3: 就餐人数分布
- **引用**: charts/_chart-registry.md#bar-ranking (竖向)

### chart-4: 桌均消费直方图
- **引用**: charts/_chart-registry.md#bar-ranking (histogram)

### chart-5: 桌台类型雷达
- **引用**: charts/_chart-registry.md#radar
