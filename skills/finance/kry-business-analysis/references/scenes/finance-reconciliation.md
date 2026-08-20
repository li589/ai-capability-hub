# S10 财务对账报告

---
id: S10
name: 财务对账报告
level: multi
period: daily/weekly
triggers:
  - 财务对账
  - 收款对账
  - 打款对账
  - 结算情况
  - 支付结算
  - 到账了多少
  - 手续费多少
  - 收款明细
---

## 数据计划

### API-1: 营业收款汇总
- **路径**: `/open/standard/report/paid/income/v6/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "periodType": "BY_TOTAL",
    "tabType": "TOTAL_INCOME",
    "statisticsByBusi": true,
    "statisticsByOrderType": false,
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: busiTypeName, totalIncome.incomeAmt, totalIncome.payCnt, payMethodList[]
- **用途**: 收款总览 + 业务类型分拆

### API-2: 支付方式明细
- **路径**: `/open/standard/report/paymethod/statistics`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "periodType": "BY_TOTAL",
    "couponStatisticalType": "BY_NAME",
    "storeStatisticalType": "COMBINE",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: payMethodName, actualReceivedAmt, payDetailAmt, payCntTotal
- **用途**: 支付方式构成

### API-3: 在线支付结算对账
- **路径**: `/open/standard/report/payment/reconciliation/v4/list`
- **入参模板**:
  ```json
  {
    "dateRange": {"startDate": "{{periodStart}}", "endDate": "{{periodEnd}}"},
    "shopIds": "{{shopIds}}",
    "pageBean": {"pageNum": 1, "pageSize": 1000}
  }
  ```
- **取数字段**: shopName, channelName, merchantNo, actualReceivedAmt, actualReceivedCnt, totalFeeAmt, curReconciliationAmt, curReconciliationCnt, curOutstandingAmt, curOutstandingCnt, lastOutstandingAmt
- **用途**: 结算对账明细

---

## 报告模板

### 板块1: 收款总览
- **图表类型**: kpi-card
- **数据来源**: API-1
- **指标**:
  | 指标 | 来源 |
  |------|------|
  | 总收款金额 | totalIncome.incomeAmt (TOTAL_INCOME) |
  | 营业收款 | busiType=BUSINESS_INCOME 的 incomeAmt |
  | 会员充值 | busiType=MEMBER_INCOME 的 incomeAmt |
  | 挂账还款 | busiType=CREDIT_REPAYMENT 的 incomeAmt |
  | 总收款笔数 | totalIncome.payCnt |

### 板块2: 业务类型收款构成
- **图表类型**: pie-doughnut
- **数据来源**: API-1
- **逻辑**: 按 busiTypeName 分组，各类型 incomeAmt 占比
- **展示**: 环形图

### 板块3: 支付方式明细
- **图表类型**: bar-ranking + data-table
- **数据来源**: API-2
- **逻辑**:
  1. 按 actualReceivedAmt 降序
  2. 标注商户实收 vs 顾客支付差额（手续费）
- **展示**: 柱状图 + 明细表格

### 板块4: 在线支付结算对账
- **图表类型**: kpi-card + data-table
- **数据来源**: API-3
- **逻辑**:
  - KPI: 总应打款/已结算/未结算/上期未结
  - 表格: 按渠道分组展示结算明细
- **指标**:
  | 指标 | 字段 |
  |------|------|
  | 应打款总额 | sum(actualReceivedAmt) |
  | 已结算金额 | sum(curReconciliationAmt) |
  | 未结算金额 | sum(curOutstandingAmt) |
  | 上期遗留未结 | sum(lastOutstandingAmt) |
  | 手续费总额 | sum(totalFeeAmt) |

### 板块5: 手续费分析
- **图表类型**: pie-doughnut
- **数据来源**: API-3
- **逻辑**: 各渠道手续费占比
- **展示**: 饼图 + 费率计算（手续费/应打款）

### 板块6: 现金流提示
- **图表类型**: 文本
- **AI 生成**:
  1. 未到账金额预警
  2. 上期遗留结算提醒
  3. 手续费优化建议

---

## AI 分析指令

### 异动判定规则
- 未结算金额 > 应打款 × 30% → 结算延迟预警
- 上期未结算金额 > 0 → 历史遗留提醒
- 手续费率 > 1% → 高手续费预警
- 某渠道结算率 < 70% → 渠道结算异常

### 洞察生成规则
1. 关注资金安全：未到账金额是否异常
2. 渠道对比：哪个渠道结算最快/最慢
3. 成本分析：手续费是否有优化空间
4. 历史遗留：上期未结是否已解决

### 建议模板
- 结算延迟："渠道{{渠道名}}当前未结算{{金额}}元，建议联系渠道确认打款进度"
- 费率优化："当前综合费率{{百分比}}%，建议与渠道协商降低至{{目标}}%"

---

## ECharts 配置

### chart-1: 收款KPI
- **引用**: charts/_chart-registry.md#kpi-card

### chart-2: 业务类型构成
- **引用**: charts/_chart-registry.md#pie-doughnut

### chart-3: 支付方式排行
- **引用**: charts/_chart-registry.md#bar-ranking

### chart-4: 结算状态饼图
- **引用**: charts/_chart-registry.md#pie-doughnut
- **数据**: 已结算/未结算/上期未结
