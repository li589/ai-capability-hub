# S12 预订经营分析

---
id: S12
name: 预订经营分析
level: multi
period: weekly/monthly
triggers:
  - 预订分析
  - 预订情况
  - 到店率
  - 预订排行
  - 哪些客户预订多
  - 预订商品排行
  - 预订员工业绩
---

## 数据计划

### API-1: 预订商品排行
- **路径**: `/open/standard/report/booking/goodsRanking`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 30}
  }
  ```
- **取数字段**: itemSkuName, itemType, quantity, unitName, shopId
- **用途**: 热门预订商品

### API-2: 预订客户排行
- **路径**: `/open/standard/report/booking/customerRanking`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 30}
  }
  ```
- **取数字段**: customerName, customerPhoneNo, bookingOrderNo, measureArrivedResvCount, measureResvCancelCount, measureResvNoshowCount, arrivedResvRatio
- **用途**: 高频客户画像

### API-3: 预订业绩排行
- **路径**: `/open/standard/report/booking/performanceRanking`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 30}
  }
  ```
- **取数字段**: creatorName, bookingOrderNo, measureArrivedResvCount, measureResvCancelCount, arrivedResvRatio
- **用途**: 员工预订业绩

### API-4: 预订门店排行（仅总部层级）
- **路径**: `/open/standard/report/booking/shopRanking`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopId, bookingOrderNo, measureArrivedResvCount, measureResvCancelCount, measureResvNoshowCount, measureResvOverdueCount, arrivedResvRatio
- **用途**: 门店预订量对比
- **条件**: 仅 level=brand 时调用

---

## 报告模板

### 板块1: 预订总览
- **图表类型**: kpi-card
- **数据来源**: API-2/API-4 汇总
- **指标**:
  | 指标 | 计算 |
  |------|------|
  | 预订总量 | sum(bookingOrderNo) |
  | 到店预订数 | sum(measureArrivedResvCount) |
  | 到店率 | 到店数/总量 × 100% |
  | 取消数 | sum(measureResvCancelCount) |
  | 未到店数 | sum(measureResvNoshowCount) |
  | 取消率 | 取消数/总量 × 100% |

### 板块2: 热门预订商品
- **图表类型**: bar-ranking
- **数据来源**: API-1
- **逻辑**: 按 quantity 降序取 Top15
- **展示**: 横向柱状图（商品名 + 数量）

### 板块3: 高频客户画像
- **图表类型**: data-table
- **数据来源**: API-2
- **逻辑**:
  1. 按 bookingOrderNo 降序
  2. 标注到店率（arrivedResvRatio × 100%）
  3. 低到店率客户红色标记
- **展示**: 表格（客户名/手机号/预订数/到店数/到店率）

### 板块4: 员工预订业绩
- **图表类型**: bar-ranking
- **数据来源**: API-3
- **逻辑**: 按 bookingOrderNo 降序
- **展示**: 横向柱状图 + 到店率标注

### 板块5: 门店预订量对比（仅总部）
- **图表类型**: bar-ranking
- **数据来源**: API-4
- **逻辑**: 按 bookingOrderNo 降序
- **展示**: 柱状图
- **条件**: 仅 level=brand 时展示

### 板块6: 预订漏斗
- **图表类型**: funnel
- **数据来源**: API-2 汇总
- **逻辑**: 预订总量 → 到店 → （差额=取消+未到店+逾期）
- **展示**: 漏斗图

### 板块7: 到店率提升建议
- **图表类型**: 文本
- **AI 生成**:
  1. 到店率偏低的原因分析
  2. 高频取消客户的跟进建议
  3. 员工预订能力差异分析
  4. 热门商品备货建议

---

## AI 分析指令

### 异动判定规则
- 到店率 < 70% → 需重点改善
- 取消率 > 20% → 取消过多
- 未到店率 > 15% → 需加强提醒
- 某员工到店率显著低于团队均值 → 培训需求

### 洞察生成规则
1. 到店率分析：与行业水平对比
2. 客户画像：高频客户的行为特征
3. 员工差异：最优/最差员工对比
4. 商品趋势：哪些商品预订增长/下降

### 建议模板
- 到店率提升："到店率仅{{百分比}}%，建议{{措施}}（如提前1小时短信/电话确认）"
- 客户管理："客户{{姓名}}累计取消{{次数}}次，建议{{策略}}"
- 员工指导："{{员工}}到店率{{百分比}}%低于团队均值{{均值}}%，建议强化{{技能}}"

---

## ECharts 配置

### chart-1: 预订KPI
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 商品排行
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-3: 员工业绩排行
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-4: 门店对比
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-5: 预订漏斗
- **引用**: charts/_chart-registry.md#funnel
