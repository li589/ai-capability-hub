# S9 运营效率分析

---
id: S9
name: 运营效率分析
level: store
period: weekly/monthly
triggers:
  - 运营效率
  - 后厨效率
  - 出品效率
  - 制作超时
  - 叫号效率
  - 出杯率
  - 员工出品
  - 哪个员工做得快
---

## 数据计划

### API-1: 后厨员工出品统计
- **路径**: `/open/standard/report/kitchen/produced/statistics`
- **入参模板**:
  ```json
  {
    "range": {"startDateTime": "{{periodStart}}", "endDateTime": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "pageBean": {"pageNum": 1, "pageSize": 50}
  }
  ```
- **注意**: 此接口用 `range`（非 dateRange），字段为 `startDateTime/endDateTime`，最大查7天
- **取数字段**: operatorName, actualSaleQty, timeoutCount, itemCount, timeoutRatio, avgCompletionTime
- **用途**: 员工出品排行 + 效率指标

### API-2: 后厨菜品出餐统计
- **路径**: `/open/standard/report/queryData`
- **入参模板**:
  ```json
  {
    "necessaryFilter": {
      "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
      "shopIds": ["{{currentShopId}}"]
    },
    "pageBean": {"pageNum": 1, "pageSize": 50}
  }
  ```
- **注意**: dateRange 和 shopIds 嵌套在 `necessaryFilter` 内
- **取数字段**: itemName, specNameConcat, actualSaleQty, timeoutCount, id(出餐次数), timeoutRatio, avgCompletionTime
- **用途**: 菜品制作时长 + 超时预警

### API-3: 取餐叫号统计
- **路径**: `/open/standard/report/CdsOrderDetailClient/statistics`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "pickFlag": false,
    "orgStatisticsType": "BY_SHOP",
    "orderSourceList": ["POS", "WECHAT_MINI_PROGRAM", "ALIPAY_MINI_PROGRAM", "PAD"],
    "orderTypeList": ["FOR_HERE"],
    "pageBean": {"pageNum": 1, "pageSize": 10}
  }
  ```
- **注意**: `pickFlag`/`orderSourceList`/`orderTypeList` 为必填；pageSize 最大 10
- **取数字段**: orderCnt, calledOrderCnt, calledOrderRate, pickedOrderCnt, pickedOrderRate, unCallOrderCnt, unPickOrderCnt, manualPickedOrderCnt
- **用途**: 叫号取餐漏斗

### API-4: 出杯率统计（茶饮/咖啡适用）
- **路径**: `/open/standard/report/measure/cup/yield/statistics`
- **入参模板**:
  ```json
  {
    "necessaryFilter": {
      "shopIds": ["{{currentShopId}}"],
      "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"}
    },
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: dateRange 和 shopIds 嵌套在 `necessaryFilter` 内
- **取数字段**: cupsSaleCnt, cupsFinishCnt, cupOutRate, pendingCupCnt
- **用途**: 出杯效率（仅茶饮/咖啡业态）

### API-5: 服务费统计
- **路径**: `/open/standard/report/extrafee/statistics`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": ["{{currentShopId}}"],
    "statisticType": "every",
    "statisticsByShop": false,
    "depositOnlyFlag": false,
    "pageBean": {"pageNum": 1, "pageSize": 50}
  }
  ```
- **注意**: `statisticType` 必填（day/week/every），`depositOnlyFlag` 必填
- **取数字段**: extraFeeName, extraFeeType, extraFeeAmt, extraFeeActualAmt, promoTotalAmt
- **用途**: 服务费收入分析

---

## 报告模板

### 板块1: 效率总览
- **图表类型**: kpi-card
- **数据来源**: API-1 汇总 + API-3 + API-4
- **指标**:
  | 指标 | 来源 |
  |------|------|
  | 平均制作时长 | avg(API-1.avgCompletionTime) |
  | 超时率 | sum(timeoutCount)/sum(itemCount) |
  | 叫号率 | API-3.calledOrderRate |
  | 取餐率 | API-3.pickedOrderRate |
  | 出杯率 | API-4.cupOutRate（如适用） |
  | 服务费收入 | sum(API-5.extraFeeActualAmt) |

### 板块2: 员工出品排行
- **图表类型**: bar-ranking
- **数据来源**: API-1
- **逻辑**:
  - 按 actualSaleQty 降序排列
  - 标注每人超时率
  - 高亮效率最高（制作量大+超时少）
- **展示**: 横向柱状图 + 超时率标注

### 板块3: 超时菜品预警
- **图表类型**: data-table
- **数据来源**: API-2
- **逻辑**:
  1. 按 timeoutRatio 降序
  2. 取超时率 > 0 的 Top10
  3. 转换 avgCompletionTime（秒→分钟）
  4. 红色标记超时率 > 30%
- **展示**: 预警表格（菜品名/超时次数/超时率/平均时长）

### 板块4: 叫号取餐漏斗
- **图表类型**: funnel
- **数据来源**: API-3
- **逻辑**:
  - 层级: 订单总数 → 已叫号 → 已取餐
  - 标注转化率
  - 标注手动取餐占比
- **展示**: 漏斗图

### 板块5: 出杯率统计（茶饮/咖啡）
- **图表类型**: kpi-card + line-trend
- **数据来源**: API-4
- **逻辑**:
  - 日出杯率趋势
  - 待出杯数预警
- **展示**: 指标卡 + 日趋势折线（如多日数据）
- **条件**: 仅茶饮/咖啡业态

### 板块6: 服务费分析
- **图表类型**: pie-doughnut
- **数据来源**: API-5
- **逻辑**: 各类服务费占比（配送费/包间费/其他）
- **展示**: 环形图

### 板块7: 效率优化建议
- **图表类型**: 文本
- **AI 生成**:
  1. 超时菜品改进建议（工序优化/人员调配）
  2. 员工培训建议（针对超时率高的员工）
  3. 叫号流程优化（降低手动取餐占比）
  4. 出杯率提升策略（如适用）

---

## AI 分析指令

### 异动判定规则
- 超时率 > 20% → 严重效率问题
- 超时率 > 10% → 需关注
- 取餐率 < 80% → 叫号流程异常
- 出杯率 < 90% → 需排查堆积原因
- 单菜平均制作时长 > 15分钟 → 效率偏低

### 洞察生成规则
1. 找出超时最严重的菜品和员工
2. 分析超时原因（复杂菜品 vs 员工效率）
3. 对比最快员工和最慢员工的差距
4. 叫号流程是否存在瓶颈

### 建议模板
- 菜品优化："{{菜品}}平均制作{{时长}}分钟，超时率{{百分比}}%，建议{{改进措施}}"
- 人员调配："{{员工}}出品量高但超时率偏高，建议{{调整方案}}"
- 流程优化："手动取餐占比{{百分比}}%，建议{{改善措施}}提升自动化率"

---

## ECharts 配置

### chart-1: 效率KPI
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 员工排行
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-3: 叫号漏斗
- **引用**: charts/_chart-registry.md#funnel

### chart-4: 服务费构成
- **引用**: charts/_chart-registry.md#pie-doughnut
