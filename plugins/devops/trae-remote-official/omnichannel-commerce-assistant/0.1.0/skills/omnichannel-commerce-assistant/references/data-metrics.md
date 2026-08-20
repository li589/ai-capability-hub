# Data and metrics

Use the business's official definition when available. State any substituted definition.

## Core definitions

| Metric | Default formula | Required caveat |
|---|---|---|
| Net revenue | GMV - refunds - discounts not already netted | Avoid double subtraction |
| Conversion rate | paid orders / unique visitors | Name the denominator |
| Average order value | GMV / paid orders | Keep currency and period consistent |
| ROAS | attributed revenue / ad spend | State attribution window and revenue basis |
| Ad cost ratio | ad spend / GMV or net revenue | Name the denominator |
| Gross margin | (net revenue - COGS) / net revenue | State freight/tax treatment |
| Contribution margin | (net revenue - COGS - platform fees - fulfillment - ad spend - variable returns) / net revenue | List omitted variable costs |
| Refund rate | refunded orders / paid orders, or refund amount / GMV | Do not mix count and value basis |
| Repeat-buyer rate | repeat buyers / cohort buyers | Define cohort and observation window |
| Sell-through | units sold / (units sold + ending sellable units) | Adjust for receipts on long periods |
| In-stock rate | in-stock eligible days / available days | Define SKU weighting |
| Inventory days | average inventory value / COGS × period days | Invalid when COGS is zero |
| Sales velocity | paid units / eligible selling days | Exclude or label stockout days |
| Net contribution per 1,000 visits | contribution profit / visits × 1,000 | Keep attribution and cost basis consistent |
| Bestseller concentration | hero-SKU net revenue / total net revenue | Pair with contribution and stock-risk views |

## Integrity checks

Before diagnosis, check:

1. totals reconcile with visible dimensions;
2. order/SKU/date keys are not unexpectedly duplicated;
3. dates, channels, SKUs, and statuses are complete;
4. compared periods have comparable days, campaign phases, and stock availability;
5. test orders, bulk orders, cancellations, refunds, and outliers are isolated;
6. attribution is not treated as causality without a valid test;
7. discontinued or out-of-stock SKUs are not silently excluded;
8. currency, tax, timezone, and refund basis are consistent.

Quantify the impact of data issues when possible and lower conclusion confidence when integrity is weak.

## Minimal schemas

Daily store:

```text
date, market, platform, currency, impressions, visitors, product_views,
add_to_carts, paid_orders, paid_buyers, gmv, refunds, ad_spend, cogs
```

SKU performance:

```text
sku, category, list_price, paid_price, impressions, clicks, visitors,
orders, units_sold, gmv, refunds, ad_spend, cogs
```

Bestseller evidence:

```text
date, platform, sku, category, price_band, exposure, product_clicks,
paid_orders, units_sold, net_revenue, contribution_profit, refunds,
organic_share, paid_share, creator_or_content_id, sellable_stock,
stockout_flag, rating_or_review_signal
```

Customer/cohort:

```text
customer_id, first_order_date, cohort, order_date, order_id,
net_revenue, category, acquisition_channel, membership_tier
```

Request pseudonymous or aggregated data when personal data is unnecessary. When inputs are incomplete, use labeled low/base/high scenarios and show which assumption drives the range.
