# S4 门店排行榜

---
id: S4
name: 门店排行榜
level: multi
period: on_demand
triggers:
  - 门店排行
  - 哪个门店最好
  - 门店对比
  - 排行榜
  - 门店表现排名
  - 业绩排名
  - 各门店数据对比
---

## 数据计划

### API-1: 门店营收排行（指定周期）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopId, shopName, saleAmt, businessIncomeAmt, totalPromoAmt, orderCnt, avgCustomerAmtAfterDiscount, orderPeopleCnt, reopenTableRate, openTableRate
- **用途**: 多维排行数据

### API-2: 门店营收排行（对比周期）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{compareStart}}", "endDate": "{{compareEnd}}"},
    "shopIds": "{{shopIds}}",
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: 同 API-1
- **用途**: 同环比计算

### API-3: 预订门店排行（可选）
- **路径**: `/open/standard/report/booking/shopRanking`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopId, bookingOrderNo, measureArrivedResvCount, arrivedResvRatio
- **用途**: 预订维度排行

---

## 报告模板

### 板块1: 排行总览
- **图表类型**: kpi-card
- **数据来源**: API-1 汇总
- **指标**:
  | 指标 | 说明 |
  |------|------|
  | 参与门店数 | count(API-1) |
  | 品牌总营业额 | sum(saleAmt) |
  | 品牌总订单数 | sum(orderCnt) |
  | 品均营业额 | avg(saleAmt) |

### 板块2: 多维排行表格
- **图表类型**: data-table
- **数据来源**: API-1 + API-2
- **列定义**:
  | 列名 | 字段 | 排序 | 环比 |
  |------|------|------|------|
  | 排名 | 序号 | — | — |
  | 门店名称 | shopName | — | — |
  | 营业额 | saleAmt | 默认↓ | ✓ |
  | 营业收入 | businessIncomeAmt | 可选↓ | ✓ |
  | 订单数 | orderCnt | 可选↓ | ✓ |
  | 客单价 | avgCustomerAmtAfterDiscount | 可选↓ | ✓ |
  | 翻台率 | reopenTableRate | 可选↓ | ✓ |
  | 就餐人数 | orderPeopleCnt | 可选↓ | ✓ |
- **样式**: 
  - Top3 行金色底色
  - 环比下降 >20% 红色标记
  - 环比上升 >20% 绿色标记

### 板块3: 营业额排行柱状图
- **图表类型**: bar-ranking
- **数据来源**: API-1
- **逻辑**: 全部门店按 saleAmt 降序
- **展示**: 横向柱状图，Top3 高亮

### 板块4: 多维雷达对比（Top5 vs Bottom5）
- **图表类型**: radar
- **数据来源**: API-1
- **逻辑**:
  1. 取 Top3 和 Bottom3 门店
  2. 5个维度：营业额、客单价、订单数、翻台率、就餐人数
  3. 各维度归一化到 0~100 分
- **展示**: 雷达图叠加对比

### 板块5: 异动门店标记
- **图表类型**: 文本列表
- **数据来源**: API-1 + API-2
- **逻辑**:
  1. 计算每店环比变化
  2. 筛选环比下降 >20% 的门店 → 红色预警
  3. 筛选环比上升 >30% 的门店 → 绿色亮点
- **展示**: 预警/亮点卡片

### 板块6: 门店分析洞察
- **图表类型**: 文本
- **AI 生成**: 头部/中位/尾部分析 + 建议

---

## AI 分析指令

### 异动判定规则
- 门店环比下降 >20% → 需关注
- 门店环比下降 >40% → 严重预警
- 门店营业额 = 0 → 疑似歇业
- 门店在排行中下降 >5名 → 排名大幅波动

### 洞察生成规则
1. 头部分析：Top3 门店亮点归因（位置？品类？活动？）
2. 尾部分析：Bottom3 门店问题诊断
3. 中位段分析：大多数门店的共性表现
4. 分化分析：头尾差距是否过大（Top1/Bottom1 比值 > 5x → 严重分化）

### 建议模板
- 头部门店："{{门店}}持续领跑，建议提炼其{{优势}}经验推广至其他门店"
- 尾部门店："{{门店}}表现低迷，建议从{{维度}}维度排查原因，目标：下周提升{{百分比}}%"

---

## ECharts 配置

### chart-1: KPI总览
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 营业额排行
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-3: 多维雷达
- **引用**: charts/_chart-registry.md#radar
- **维度**: 营业额/客单价/订单数/翻台率/就餐人数
