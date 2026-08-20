# S7 菜品经营分析

---
id: S7
name: 菜品经营分析
level: multi
period: weekly/monthly
triggers:
  - 菜品分析
  - 哪个菜卖得好
  - 菜品排行
  - 菜品毛利
  - 热销菜品
  - 退菜分析
  - 菜品经营
  - 菜品优化建议
  - 套餐分析
---

## 数据计划

### API-1: 菜品销售排行
- **路径**: `/open/standard/report/orderItem/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "countLatitude": {"countCollectType": 0, "countType": 1},
    "sellLatitude": {"sellCollectType": false, "countType": "SINGLE_PACKAGE"}
    "orderSourceCondition": {"orderSourceType": 0},
    "orderTypeCondition": {"orderType": 0},
    "goodsTempFlag": 0,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: values[].item[] → name, salePrice, actualAmt, goodsSpotQty, actualSaleQty, returnCnt, returnRatio, giftCnt, grossProfitRatio, grossProfitPrice
- **用途**: 菜品排行 + 退菜预警

### API-2: 分类营收
- **路径**: `/open/standard/report/orderItem/itemType/list`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "countLatitude": {"countCollectType": 0, "countType": 2},
    "sellLatitude": {"sellCollectType": false, "countType": "SINGLE_PACKAGE"}
    "orderSourceCondition": {"orderSourceType": 0},
    "orderTypeCondition": {"orderType": 0},
    "goodsTempFlag": 0,
    "pageBean": {"pageNum": 1, "pageSize": 100}
  }
  ```
- **取数字段**: values[].item[] → bigTypeName, salePrice, actualAmt, goodsSpotQty
- **用途**: 品类贡献度；当用户询问最近 N 天、3天、三天、按天或趋势时，用于构建「日期 × 品类」营收趋势
- **多天规则**: 该接口单次仅支持 1 天，`fetch.mjs` 会按天拆分调用；生成 HTML 报告时必须保留日期维度，禁止只输出汇总品类占比。

### API-3: 部门销售
- **路径**: `/open/standard/report/orderItem/department/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "countLatitude": {"countCollectType": 0, "countType": 1},
    "sellLatitude": {"sellCollectType": false, "countType": "SINGLE_PACKAGE"}
    "orderSourceCondition": {"orderSourceType": 0},
    "orderTypeCondition": {"orderType": 0},
    "goodsTempFlag": 0,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: values[].item[] → departmentName, salePrice, actualAmt, goodsSpotQty
- **用途**: 部门出品对比

### API-4: 套餐销售
- **路径**: `/open/standard/report/combo/sale/statistics`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "countType": 1,
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: `countType` 必填（1=按套餐汇总）
- **取数字段**: comboName, itemSalePrice, itemSaleQty, actualAmt, subs[]
- **用途**: 套餐拆解

### API-5: 菜品毛利
- **路径**: `/open/standard/report/measure/dish/gross/profit`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "necessaryFilter": {
      "shopIds": "{{shopIds}}",
      "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"}
    },
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: dateRange 和 shopIds 嵌套在 `necessaryFilter` 内
- **取数字段**: 菜品名、毛利率、毛利、销售金额、成本价、实际销售数量
- **用途**: 毛利象限分析

### API-6: 做法偏好
- **路径**: `/open/standard/report/order/orderitem/practice/page`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "groupType": "byItem",
    "countLatitude": {"countCollectType": 0, "countType": 1},
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: `groupType` 必填（"byItem"=按菜品分组），`countLatitude` 必填
- **取数字段**: 做法名称、销售数量、销售金额
- **用途**: 口味偏好

### API-7: 规格销售
- **路径**: `/open/standard/report/order/orderitem/spec/page`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "countLatitude": {"countType": "goodsSpecCount"},
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **注意**: `countLatitude` 必填，`countType` 为 "goodsSpecCount"
- **取数字段**: 规格名称、销售数量、销售金额
- **用途**: 规格偏好

---

## 报告模板

### 板块1: 菜品销售 Top20
- **图表类型**: bar-ranking
- **数据来源**: API-1
- **逻辑**: 按 actualAmt 降序，取 Top20
- **展示**: 横向柱状图，标注销量和收入

### 板块2: 品类营收贡献与趋势
- **图表类型**: pie-doughnut + stacked-bar + line-trend
- **数据来源**: API-2
- **逻辑**:
  1. 各大类 actualAmt 占比 → 饼图
  2. 各大类 salePrice 对比 → 堆叠柱图
  3. 用户询问最近 N 天、3天、三天、按天或趋势时，按 date × bigTypeName 汇总 actualAmt → 各品类营收趋势折线图
- **展示**: 单日或汇总问题展示左饼图 + 右柱图；多天趋势问题必须展示各品类按天变化的 ECharts 趋势图，不允许只展示汇总表格或文字结论。

### 板块3: 毛利象限分析
- **图表类型**: scatter-quadrant
- **数据来源**: API-5
- **逻辑**:
  - X轴: actualSaleQty（销量）
  - Y轴: grossProfitRatio（毛利率）
  - 中线: 中位数
  - 四象限: 明星(右上)/问题(左上)/金牛(右下)/瘦狗(左下)
- **展示**: 散点图 + 象限标注 + 各象限 Top3 菜品列表

### 板块4: 套餐拆解
- **图表类型**: data-table
- **数据来源**: API-4
- **逻辑**:
  1. 各套餐按 actualAmt 排序
  2. 展开子菜明细(subs[])
  3. 计算子菜贡献占比
- **展示**: 可折叠表格

### 板块5: 退菜预警
- **图表类型**: data-table + 标记
- **数据来源**: API-1
- **逻辑**:
  1. 筛选 returnRatio > 5% 的菜品
  2. 按 returnRatio 降序
  3. 红色标记 returnRatio > 10%
- **展示**: 预警表格

### 板块6: 做法/规格偏好
- **图表类型**: bar-ranking
- **数据来源**: API-6 + API-7
- **逻辑**: Top10 做法/规格按销量排序
- **展示**: 双柱图并列

### 板块7: 菜品优化建议
- **图表类型**: 文本
- **AI 生成**:
  - 明星菜品（重点推广）
  - 问题菜品（加大曝光）
  - 金牛菜品（优化成本）
  - 瘦狗菜品（考虑下架/改良）
  - 退菜率异常菜品排查建议

---

## AI 分析指令

### 异动判定规则
- 退菜率 > 10% → 严重预警
- 退菜率 > 5% → 需关注
- 毛利率 < 30% 且销量 Top10 → 成本风险
- 单品收入占比 > 15% → 品类集中度风险

### 洞察生成规则
1. 四象限分析必须覆盖每个象限至少 1 条建议
2. 退菜预警必须列出具体菜品名和退菜率
3. 套餐分析需指出子菜贡献是否均衡
4. 做法偏好需指出可复制的爆款做法

### 建议分级
- 立即执行：退菜率 > 10% 的菜品排查
- 本周优化：瘦狗菜品调整
- 长期规划：品类结构优化

---

## ECharts 配置

### chart-1: 菜品Top20
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-2: 品类贡献饼图
- **引用**: charts/_chart-registry.md#pie-doughnut

### chart-2b: 多天品类营收趋势
- **触发**: 用户询问最近 N 天、3天、三天、按天或趋势
- **引用**: charts/_chart-registry.md#line-trend
- **数据**: `components.categoryTrend.xLabels` 作为日期轴，`components.categoryTrend.series` 作为各品类营收序列
- **要求**: 必须使用 ECharts 折线图展示各品类按天变化；无数据时展示空态卡片并说明接口返回为空。

### chart-3: 毛利象限
- **引用**: charts/_chart-registry.md#scatter-quadrant

### chart-4: 做法偏好
- **引用**: charts/_chart-registry.md#bar-ranking
