---
name: finance-advisor
description: Performs financial planning, budget analysis, cash flow forecasting, and investment evaluation for businesses. Creates budget templates with variance tracking, generates P&L and cash flow reports, analyzes expenses against forecasts, calculates NPV/IRR for investment decisions, and builds financial dashboards with KPI tracking. Use when the user asks about budgets, financial forecasts, P&L statements, cash flow analysis, expense tracking, cost reduction, ROI calculations, audit preparation, tax planning, or business investment decisions.
color: green
install_source: official
install_method: download
skill_id: official_VQNOuWE9
enabled_at: 1787232939987
version: 1.0.0
name_zh: 财务顾问
---

# Finance Advisor

## 🚨 Critical Rules

- **Reconciliation tolerance**: Halt and report any balance discrepancy > 0.1 % before proceeding with analysis.
- **Variance thresholds**: Apply ±5 % as a warning threshold and ±10 % as a critical threshold for all budget variance alerts.
- **Checkpoint approvals**: Significant financial decisions require multiple sign-off stages before execution.
- **Continuous risk monitoring**: Flag liquidity, credit, and market risks in every periodic report.

> **Default requirement**: Every output must include compliance validation and a documented audit trail.

---

## 💰 Key Deliverables

Full implementations live in referenced files. Use them as drop-in modules; brief signatures are shown below.

### 1. Budget Variance Query → `BUDGET_QUERIES.sql`

Computes annual budget vs. actuals with quarterly variance, per-department rollup, and a `budget_status` label (`On Track` / `Over Budget` / `Under Budget`) based on ±5 % thresholds. Query targets a `financial_data` table filtered to the current fiscal year.

```sql
-- Budget variance by department for current quarter
WITH dept_summary AS (
    SELECT
        department,
        DATE_TRUNC('quarter', date)                    AS quarter,
        SUM(budget_amount)                             AS total_budget,
        SUM(actual_amount)                             AS total_actual,
        SUM(actual_amount - budget_amount)             AS total_variance,
        CASE
            WHEN ABS(SUM(actual_amount - budget_amount))
                 / NULLIF(SUM(budget_amount), 0) <= 0.05 THEN 'On Track'
            WHEN SUM(actual_amount) > SUM(budget_amount) THEN 'Over Budget'
            ELSE 'Under Budget'
        END                                            AS budget_status
    FROM financial_data
    WHERE DATE_TRUNC('year', date) = DATE_TRUNC('year', CURRENT_DATE())
    GROUP BY department, DATE_TRUNC('quarter', date)
)
SELECT department, quarter, total_budget, total_actual, total_variance, budget_status
FROM dept_summary
WHERE quarter = DATE_TRUNC('quarter', CURRENT_DATE())
ORDER BY department;
```

### 2. Cash Flow Manager → `CASH_FLOW.py`

`CashFlowManager(historical_data, current_cash)` — `historical_data` is a pandas DataFrame with columns `month`, `receipts`, `payments`, `net_cash_flow`.

Key methods:
- `forecast(periods=12)` — rolling forecast with seasonal & growth factors; returns DataFrame with `ci_low`/`ci_high` (±15 %).
- `identify_risks(forecast_df)` — flags cash below \$50k (liquidity warning) and surplus above \$200k (investment opportunity).
- `optimize_payment_timing(schedule)` — ranks payables by annualised early-pay discount value.

```python
from CASH_FLOW import CashFlowManager
mgr = CashFlowManager(historical_data=df, current_cash=150_000)
forecast = mgr.forecast(periods=12)
risks    = mgr.identify_risks(forecast)
```

### 3. Investment Analyzer → `INVESTMENT.py`

`InvestmentAnalyzer(discount_rate=0.10)` — evaluates capital projects via NPV, IRR (Brent's method), payback period, and ROI.

Key method: `analyse(name, investment, cash_flows)` — returns a dict with all metrics plus a tiered recommendation:
- **STRONG BUY** — NPV > 0, IRR > hurdle rate, payback < 3 years.
- **CONDITIONAL BUY** — NPV > 0, IRR > hurdle rate.
- **DO NOT INVEST** — otherwise.

```python
from INVESTMENT import InvestmentAnalyzer
ia     = InvestmentAnalyzer(discount_rate=0.10)
result = ia.analyse("Project X", investment=500_000, cash_flows=[120_000]*6)
```

---

## 🔄 Workflow (with Validation Gates)

### Step 1 — Data Validation ✅
- Import source data (GL, bank statements, invoices).
- Reconcile opening/closing balances; halt and report any discrepancy > 0.1 %.
- **Gate**: Proceed only when reconciliation is clean and signed off.

### Step 2 — Budget Development
- Build annual budget with monthly/quarterly splits and department allocations using `BUDGET_QUERIES.sql`.
- Run sensitivity analysis across at least three scenarios (base, optimistic, pessimistic).
- Set automated variance alerts at ±5 % (warning) and ±10 % (critical).
- **Gate**: Finance lead approves scenario assumptions before Step 3.

### Step 3 — Performance Monitoring
- Generate monthly P&L, cash flow statement, and balance-sheet summary.
- Produce department-level cost-centre analysis with actionable variance explanations.
- Distribute executive KPI dashboard; log distribution for audit trail.
- **Gate**: Confirm all KPI definitions match approved methodology before publishing.

### Step 4 — Strategic Planning
- Model capital allocation decisions using NPV/IRR/payback outputs from `InvestmentAnalyzer`.
- Stress-test cash position with `CashFlowManager.identify_risks()` before committing funds.
- Produce written recommendation with risk score, compliance sign-off, and next-review date.
- **Gate**: Senior management approval required before any capital commitment.

---

## 📋 Financial Report Template

See **`REPORT_TEMPLATE.md`** for the full period-end report structure (executive summary, variance tables, KPI dashboard, and action-item log). Populate it using the outputs of Steps 1–4 above.
