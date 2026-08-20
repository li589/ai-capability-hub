# S5 区域经营报告

---
id: S5
name: 区域经营报告
level: region
period: daily/weekly
triggers:
  - 区域报告
  - 我负责的门店怎么样
  - 辖区经营情况
  - 区域对比
  - 片区报告
---

## 数据计划

### API-1: 辖区门店营收（按门店维度）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{regionShopIds}}",
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopId, shopName, saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, orderPeopleCnt, reopenTableRate
- **用途**: 门店对比 + 区域汇总

### API-2: 辖区门店营收（对比周期）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**: 同 API-1，dateRange 改为 {{comparePeriod}}
- **用途**: 环比计算

### API-3: 辖区菜品销售
- **路径**: `/open/standard/report/orderItem/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{regionShopIds}}",
    "countLatitude": {"countCollectType": 0, "countType": 1},
    "sellLatitude": {"sellCollectType": false, "countType": "SINGLE_PACKAGE"}
    "orderSourceCondition": {"orderSourceType": 0},
    "orderTypeCondition": {"orderType": 0},
    "goodsTempFlag": 0,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: values[].item[].name, shopName, salePrice, actualAmt, goodsSpotQty
- **用途**: 各店菜品偏好对比

### API-4: 辖区就餐人数分析
- **路径**: `/open/standard/report/dinner/numberAnalysis`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{regionShopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: peopleCnt, orderReceivedAmt, busiOrderNoCount, perCapitaPost
- **用途**: 客流与人效分析

---

## 报告模板

### 板块1: 区域总览
- **图表类型**: kpi-card
- **数据来源**: API-1 汇总
- **指标**:
  | 指标 | 计算 |
  |------|------|
  | 辖区门店数 | count(shops) |
  | 区域总营业额 | sum(saleAmt) |
  | 区域总订单数 | sum(orderCnt) |
  | 区域平均客单价 | avg(avgCustomerAmtAfterDiscount) |
  | 区域总就餐人数 | sum(orderPeopleCnt) |
  | 区域均翻台率 | avg(reopenTableRate) |

### 板块2: 辖区门店对比（雷达图）
- **图表类型**: radar
- **数据来源**: API-1
- **逻辑**:
  1. 每个门店作为一个数据系列
  2. 5维度：营业额/客单价/订单数/翻台率/就餐人数
  3. 归一化处理（区域内最大值=100）
- **展示**: 所有辖区门店叠加雷达图

### 板块3: 门店排行对比
- **图表类型**: bar-ranking + data-table
- **数据来源**: API-1 + API-2
- **逻辑**: 按 saleAmt 降序，标注环比
- **展示**: 柱状图 + 表格

### 板块4: 客流与人效
- **图表类型**: bar-ranking
- **数据来源**: API-4
- **逻辑**:
  - 人效 = orderReceivedAmt / peopleCnt（折后人均）
  - 各店人效对比
- **展示**: 人效对比柱状图

### 板块5: 菜品偏好差异
- **图表类型**: data-table
- **数据来源**: API-3
- **逻辑**:
  1. 各门店分别取 Top5 菜品
  2. 对比各店热销菜品是否一致
  3. 标注差异化菜品
- **展示**: 多列对比表格

### 板块6: 区域行动建议
- **图表类型**: 文本
- **AI 生成**: 针对辖区门店差异的行动建议

---

## AI 分析指令

### 异动判定规则
- 辖区内门店之间差距 > 3x → 严重分化
- 某店环比下降 >20% 而其他店正常 → 个体问题
- 辖区整体下降 >10% → 区域性问题

### 洞察生成规则
1. 对比分析为核心（门店之间横向对比）
2. 找出最优门店的可复制做法
3. 找出最差门店的改进空间
4. 识别区域共性趋势（天气/竞品/季节）

### 建议模板
- 差异化建议："{{优秀门店}}的{{做法}}值得推广至{{落后门店}}，预计可提升{{百分比}}%"
- 统一行动："区域整体{{趋势}}，建议统一{{动作}}"

---

## ECharts 配置

### chart-1: 区域KPI
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 门店雷达对比
- **引用**: charts/_chart-registry.md#radar

### chart-3: 门店排行
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-4: 人效对比
- **引用**: charts/_chart-registry.md#bar-ranking
