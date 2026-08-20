# S3 月度经营总结

---
id: S3
name: 月度经营总结
level: brand
period: monthly
triggers:
  - 月度经营总结
  - 月报
  - 上月经营情况
  - 本月总结
  - 月度分析
  - 经营月报
---

## 数据计划

### API-1: 本月日趋势（品牌汇总）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisMonthStart}}", "endDate": "{{thisMonthEnd}}"},
    "shopIds": [],
    "periodType": "BY_DAY",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: date, saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, orderPeopleCnt, reopenTableRate, extraFeeActualAmt, itemActualReceivedAmt
- **用途**: 日趋势 + 月度汇总

### API-2: 上月汇总（品牌汇总，环比）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{lastMonthStart}}", "endDate": "{{lastMonthEnd}}"},
    "shopIds": [],
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: 同 API-1
- **用途**: 月环比对比

### API-3: 门店排行（本月汇总）
- **路径**: `/open/standard/report/business/income/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisMonthStart}}", "endDate": "{{thisMonthEnd}}"},
    "shopIds": [],
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_SHOP",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 500}
  }
  ```
- **取数字段**: shopId, shopName, saleAmt, businessIncomeAmt, orderCnt, avgCustomerAmtAfterDiscount, reopenTableRate
- **用途**: 门店排行 + 贡献度

### API-4: 分类营收统计
- **路径**: `/open/standard/report/orderItem/itemType/list`
- **fetchMode**: script
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisMonthStart}}", "endDate": "{{thisMonthEnd}}"},
    "shopIds": [],
    "countLatitude": {"countCollectType": 0, "countType": 2},
    "sellLatitude": {"sellCollectType": false, "countType": "SINGLE_PACKAGE"}
    "orderSourceCondition": {"orderSourceType": 0},
    "orderTypeCondition": {"orderType": 0},
    "goodsTempFlag": 0,
    "pageBean": {"pageNum": 1, "pageSize": 100}
  }
  ```
- **取数字段**: values[].item[].bigTypeName, salePrice, actualAmt, goodsSpotQty
- **用途**: 品类贡献度

### API-6: 收款汇总
- **路径**: `/open/standard/report/paid/income/v6/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisMonthStart}}", "endDate": "{{thisMonthEnd}}"},
    "shopIds": [],
    "periodType": "BY_TOTAL",
    "tabType": "TOTAL_INCOME",
    "statisticsByBusi": false,
    "statisticsByOrderType": false,
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: totalIncome.incomeAmt, payMethodList[].payTypeName, payMethodList[].incomeAmt
- **用途**: 收款结构

### API-7: 优惠构成
- **路径**: `/open/standard/report/business/income/promo/v3/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisMonthStart}}", "endDate": "{{thisMonthEnd}}"},
    "shopIds": [],
    "periodType": "BY_TOTAL",
    "orgStatisticsType": "BY_BRAND",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: orderPromoItems, paymentPromoItems, orderExpenseItems
- **用途**: 成本结构（优惠占比 + 订单支出）

### API-8: 单品销售 Top10
- **路径**: `/open/standard/report/orderItem/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{thisMonthStart}}", "endDate": "{{thisMonthEnd}}"},
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
- **用途**: 单品爬榜 + 退菜预警

---

## 报告模板

> **必选板块规则**：板块1~4、6、7、11、15、16 为必选板块，禁止跳过。
> 若对应 API 返回空数据，仍须保留板块标题并显示“本月无数据，可能原因：XXX”提示卡片，禁止整块省略。

### 板块1: 月度 KPI 仪表盘
- **图表类型**: kpi-card + stats-inline
- **数据来源**: API-1 汇总 + API-2
- **指标清单**:
  | 指标 | 计算 | 环比 |
  |------|------|------|
  | 月营业额 | sum(API-1.saleAmt) | vs 上月 |
  | 月营业收入 | sum(API-1.businessIncomeAmt) | vs 上月 |
  | 月订单数 | sum(API-1.orderCnt) | vs 上月 |
  | 月就餐总人数 | sum(orderPeopleCnt) | vs 上月 |
  | 折后单均价 | avg(avgCustomerAmtAfterDiscount) | vs 上月 |
  | 优惠占比 | |totalPromoAmt|/saleAmt | vs 上月 |
- **stats-inline 辅助指标**:
  - 最高单日：max(API-1 按日) → 日期 + 金额
  - 最低单日：min(API-1 按日) → 日期 + 金额
  - 周末日均：周六日平均营业额
  - 工作日日均：周一~周五平均营业额
  - 周末溢价：(周末日均-工作日日均)/工作日日均×100%

### 板块2: 日营收趋势（双 Y 轴）
- **图表类型**: line-trend + bar 双 Y 轴
- **数据来源**: API-1
- **逻辑**:
  - X轴: 1号~30/31号
  - 左Y轴: 日营业额（面积折线） + 7日移动均线（虚线）
  - 右Y轴: 日订单数（柱图）
  - 标注: 周末峰值标记
- **展示**: 双轴复合图（line + bar）

### 板块3: 品类营收贡献
- **图表类型**: pie-doughnut
- **数据来源**: API-4
- **逻辑**:
  1. 按大类汇总 actualAmt
  2. 计算各大类占总收入比例
  3. 按金额降序排列，取 Top10
- **空数据处理**: 若 API-4 返回 values 为空或无数据，仍保留本板块，显示提示卡片：“本月菜品分类数据未返回，可能原因：门店未配置菜品大类或接口时段数据未生成”
- **展示**: 环形图 + 右侧图例

### 板块4: 订单类型构成
- **图表类型**: pie-doughnut
- **数据来源**: API-1 → orderTypeItems
- **逻辑**:
  1. 遍历 orderTypeItems.itemList[]
  2. 取每个类型（堂食/平台外卖/自营外卖）的 orderAmt
  3. 计算各类型占比
- **展示**: 环形图 + 右侧图例

### 板块5: 品类明细榜
- **图表类型**: data-table
- **数据来源**: API-4
- **逻辑**: 按 actualAmt 降序取前 10 大类
- **表格字段**: 品类名 | 营业额 | 销量 | 占比
- **展示**: 纯表格，数字右对齐

### 板块6: Top10 单品销售榜
- **图表类型**: bar-ranking + data-table
- **数据来源**: API-8
- **逻辑**:
  1. 按 actualAmt 降序取 Top10
  2. 横向柱图（渐变填充）
  3. 下方表格：排名|商品|销量|销售金额
- **展示**: 柱图 + 表格

### 板块7: 门店 Top10 营收排行
- **图表类型**: bar-ranking
- **数据来源**: API-3
- **逻辑**:
  1. 按 saleAmt 降序取 Top10
  2. 标注门店名 + 月营业额
- **展示**: 横向柱图（渐变填充）

### 板块8: 门店 Bottom10 营收排行
- **图表类型**: bar-ranking
- **数据来源**: API-3
- **逻辑**:
  1. 按 saleAmt 升序取 Bottom10（营收最低的10家门店）
  2. 标注门店名 + 月营业额
  3. 颜色使用 danger 渐变（橙→红），与 Top10 的 primary 渐变区分
- **展示**: 横向柱图（danger 渐变填充）

### 板块9: 门店营收分布
- **图表类型**: bar (bucket 直方图)
- **数据来源**: API-3
- **逻辑**:
  1. 将门店按月营收分 bucket: ≥10万 / 5-10万 / 2-5万 / 1-2万 / 5k-1万 / <5k
  2. 统计每个区间门店数
- **展示**: 垂直柱图，柱顶标数字

### 板块10: 门店 Top30 完整表
- **图表类型**: data-table
- **数据来源**: API-3
- **表格字段**: # | 门店名称 | 月营业额 | 月订单数 | 折后单均
- **逻辑**: 按 saleAmt 降序取前 30 行

### 板块11: 收款结构
- **图表类型**: pie-doughnut
- **数据来源**: API-6
- **逻辑**:
  1. 按 payMethodList[].incomeAmt 降序
  2. 前 5 大支付方式独立展示，其余合并为“其他”
- **展示**: 环形图 + 右侧图例

### 板块12: 优惠与支出构成
- **图表类型**: bar-ranking (横向)
- **数据来源**: API-7
- **逻辑**:
  1. 拆解订单优惠 (orderPromoItems)、支付优惠 (paymentPromoItems)、订单支出 (orderExpenseItems)
  2. 各子项按金额降序排列
  3. 颜色区分：订单优惠=橙 | 支付优惠=粉 | 订单支出=红
- **展示**: 横向柱图 + 右侧金额标签

### 板块13: 营业额资金流向
- **图表类型**: pie-doughnut
- **数据来源**: API-1 + API-7
- **逻辑**:
  1. 营业收入(实收) = businessIncomeAmt
  2. 订单优惠 = orderPromoItems.subTotal
  3. 支付优惠 = paymentPromoItems.subTotal
  4. 外卖抽佣 + 配送支出 = orderExpenseItems 中对应项
- **展示**: 环形图（营业额构成分解）

### 板块15: 核心洞察
- **图表类型**: insight-card
- **AI 生成**:
  1. 按维度覆盖：营收总量 > 品类结构 > 门店分化 > 渠道结构 > 成本控制
  2. 每条洞察分类标注：good / warn / info / risk
  3. 总数 5~10 条，确保每条有数据支撑
- **展示**: 分色洞察卡片（insight-card 样式）

### 板块16: 下月行动清单
- **图表类型**: action-card
- **AI 生成**:
  1. 6~8 条行动建议，每条带 P0/P1/P2 优先级
  2. 格式：标题 + 背景描述 + 量化目标
  3. P0 不超过 2 条，P1 不超过 3 条，其余 P2
- **展示**: 2列网格 action 卡片（action-card 样式）

### 板块17: 数据说明与口径
- **图表类型**: data-quality 文本块
- **内容**:
  1. 数据来源：客如云开放平台接口清单
  2. 数据一致性：品牌汇总 vs 门店汇总差异
  3. 时间口径：营业日 / 环比对象
  4. 异常标注：降级/缺失板块原因说明
- **展示**: 蓝底说明卡片（data-quality 样式）

---

## AI 分析指令

### 异动判定规则
- 月环比 ±10% → 显著变化
- 月环比 ±20% → 需重点分析原因
- 单个门店贡献占比超过 30% → 标记集中度风险
- 优惠率超过 15% → 标记优惠过度

### 洞察生成规则
1. 维度覆盖：营收总量 > 品类结构 > 门店分化 > 渠道结构 > 成本控制
2. 归因分析：找到变化最大的贡献因素
3. 对标分析：优秀门店 vs 落后门店差异
4. 趋势判断：是持续趋势还是单月波动

### 行动项模板
- "【{{优先级}}】{{行动描述}}，背景：{{数据依据}}，目标：{{量化目标}}"
- 优先级：P0(紧急) / P1(重要) / P2(优化)

---

## ECharts 配置

### chart-1: 月度 KPI 仪表盘
- **引用**: charts/_chart-registry.md#kpi-card
- **指标数**: 6 + stats-inline 辅助行

### chart-2: 日营收趋势（双 Y 轴）
- **引用**: charts/_chart-registry.md#line-trend
- **系列**: 左Y轴=日营业额(面积折线)+7日均线(虚线) / 右Y轴=日订单数(柱图)
- **双轴**: true

### chart-3: 品类营收贡献
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据**: API-4 大类 actualAmt Top10
- **样式**: doughnut + 右侧图例

### chart-4: 订单类型构成
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据**: API-1 orderTypeItems
- **样式**: doughnut

### chart-5: 品类明细榜
- **引用**: charts/_chart-registry.md#data-table
- **字段**: 品类名 | 营业额 | 销量 | 占比

### chart-6: 单品 Top10 销售榜
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据**: API-8 actualAmt Top10
- **渐变**: primary→accent

### chart-7: 门店 Top10 营收排行
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据**: API-3 saleAmt Top10

### chart-8: 门店 Bottom10 营收排行
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据**: API-3 saleAmt Bottom10（升序取末位）
- **配色**: danger 渐变（区分 Top10）

### chart-9: 门店营收分布直方图
- **引用**: charts/_chart-registry.md#bar-ranking
- **bucket**: ≥10万 / 5-10万 / 2-5万 / 1-2万 / 5k-1万 / <5k
- **柱顶**: 门店数标注

### chart-10: 门店 Top30 表
- **引用**: charts/_chart-registry.md#data-table
- **字段**: # | 门店名称 | 月营业额 | 月订单数 | 折后单均

### chart-11: 收款结构
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据**: API-6 payMethodList Top5 + 其他

### chart-12: 优惠与支出构成
- **引用**: charts/_chart-registry.md#bar-ranking
- **数据**: API-7 三类优惠/支出
- **配色**: 订单优惠=warning / 支付优惠=accent / 订单支出=danger

### chart-13: 营业额资金流向
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据**: 营业收入 + 订单优惠 + 支付优惠 + 外卖抽佣

### chart-15: 核心洞察
- **引用**: charts/_chart-registry.md#insight-card
- **分类**: good / warn / info / risk
- **数量**: 5~10 条

### chart-16: 下月行动清单
- **引用**: charts/_chart-registry.md#action-card
- **优先级**: P0(≤2) / P1(≤3) / P2(其余)

### chart-17: 数据说明
- **引用**: charts/_chart-registry.md#data-quality
- **内容**: 数据来源 + 口径 + 异常标注

---

## 生成验收清单

> ❗ **强制执行**：HTML 报告生成完成后、输出给用户前，**必须** 逐项核对以下清单。任何一项不通过则必须先修复再输出。

### 板块完整性核对

| 板块 | 名称                   | 必选  | 渲染方式                         | 核对要点                                     |
| ---- | ---------------------- | :---: | -------------------------------- | -------------------------------------------- |
| 1    | 月度 KPI 仪表盘        |   ✅   | kpi-card + stats-inline          | 6个 KPI 卡片 + 5个辅助指标，环比均已计算     |
| 2    | 日营收趋势             |       | ECharts line-trend + bar 双 Y 轴 | 必须有 `echarts.init` + 30天数据点           |
| 3    | 品类营收贡献           |   ✅   | ECharts pie-doughnut             | 环形图或“暂无数据”提示卡片                   |
| 4    | 订单类型构成           |   ✅   | ECharts pie-doughnut             | 环形图或“暂无数据”提示卡片                   |
| 5    | 品类明细榜             |       | data-table                       | 表格有数据行或提示卡片                       |
| 6    | 单品 Top10 销售榜      |   ✅   | ECharts bar-ranking + data-table | **禁止空 tbody**，必须有柱图+表格或提示卡片  |
| 7    | 门店 Top10 营收排行    |   ✅   | ECharts bar-ranking              | 横向柱图（渐变填充）                         |
| 8    | 门店 Bottom10 营收排行 |       | ECharts bar-ranking              | 横向柱图（danger 渐变），升序取末位10家      |
| 9    | 门店营收分布           |       | ECharts bar (直方图)             | 6个 bucket 柱图                              |
| 10   | 门店 Top30 完整表      |       | data-table                       | 表格 ≤30 行                                  |
| 11   | 收款结构               |   ✅   | ECharts pie-doughnut             | **禁止用 `<ul>` 列表**，必须环形图           |
| 12   | 优惠与支出构成         |       | ECharts bar-ranking              | **禁止用 `<ul>` 列表**，必须横向柱图         |
| 13   | 营业额资金流向         |       | ECharts pie-doughnut             | 环形图                                       |
| 15   | 核心洞察               |   ✅   | insight-card                     | **最少 5 条，最多 10 条**                    |
| 16   | 下月行动清单           |   ✅   | action-card                      | **最少 6 条，最多 8 条**（P0≤2/P1≤3/P2其余） |
| 17   | 数据说明与口径         |       | data-quality                     | 蓝底说明卡片                                 |

### 图表渲染核对

检查 `<script>` 标签内必须包含：

- [ ] 每个图表容器 (`.chart-box`) 都有对应的 `echarts.init(document.getElementById('xxx'))` 调用
- [ ] 每个 chart 对象都执行了 `chart.setOption({...})` 且 option 内容非空
- [ ] `series[].data` 是具体数据数组，不是空数组 `[]`
- [ ] 所有图表容器有明确宽高（使用 `.chart-box` 类名，默认 height:400px）
- [ ] 窗口 resize 监听已绑定

### 内容数量核对

| 项目                  |                        最少数量                        | 当前报告是否满足 |
| --------------------- | :----------------------------------------------------: | :--------------: |
| KPI 卡片              |                           6                            |        ☐         |
| stats-inline 辅助指标 |                           5                            |        ☐         |
| ECharts 图表数        | ≥6（趋势+品类饼+订单饼+门店Top柱+门店Bottom柱+收款饼） |        ☐         |
| 核心洞察              |                        5~10 条                         |        ☐         |
| 行动建议              |                         6~8 条                         |        ☐         |
| hero-highlight 数字   |                         3~4 个                         |        ☐         |

### 常见错误自检

生成完成后用以下关键词检索 HTML 源码，确认**不存在**以下情况：

```
禁止出现：
- <ul>...<li>...金额    → 应用 ECharts 图表
- <tbody></tbody>        → 应有数据行或提示卡片
- echarts.min.js 引入但无 echarts.init  → 必须有图表初始化
- 仅 3 条 insight   → 必须 5~10 条
- 仅 3 条 action    → 必须 6~8 条
```
