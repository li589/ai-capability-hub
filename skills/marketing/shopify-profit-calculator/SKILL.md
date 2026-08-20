---
name: shopify-profit-calculator
description: "Shopify profit calculation agent. Computes true net profit per product or order by subtracting COGS, Shopify fees, Stripe/payment fees, ad spend, and shipping from revenue. Tracks margin trends and flags unprofitable SKUs. Triggers: shopify profit, profit calculator, shopify margin, true profit, net profit, cogs, shopify fees, profit per product, ecommerce profit, shopify p&l, gross margin, contribution margin"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/shopify-profit-calculator
install_source: official
install_method: download
skill_id: official_9irfHtQk
enabled_at: 1787231143166
version: 1.0.0
name_zh: Shopify 利润计算器
---

# Shopify Profit Calculator

AI-powered profit analysis agent for Shopify stores — calculates your true net profit after every fee, cost, and ad dollar is accounted for.

Paste your order data, describe your cost structure verbally, or ask about specific products. The agent computes real margins, flags danger zones, and shows exactly where your money is going.

## Commands

```
profit calc                        # calculate net profit (paste order/product data or describe)
profit by product                  # break down profit margin for each SKU
profit by order                    # compute net profit for a specific order
profit trend                       # show margin trend over time (requires saved data)
set cogs <product> <cost>          # save COGS for a product to memory
profit report                      # generate full P&L summary report
profit save <store-name>           # save store profile and COGS table to workspace
```

## What Data to Provide

The agent works with:
- **Order exports** — paste Shopify order CSV rows (revenue, product, shipping collected)
- **Verbal description** — "I sell a $49 product, COGS $12, Shopify Basic plan, running $800/mo Facebook ads, average shipping $6"
- **Product details** — price, COGS, ad spend per unit, shipping cost, return rate
- **Screenshots** — Shopify analytics, ad dashboards, payment processor summaries

No API keys needed. No setup required.

## Workspace

Creates `~/shopify-profit/` containing:
- `memory.md` — saved store profiles, COGS tables, fee structures
- `reports/` — past profit reports (markdown)
- `products.md` — per-SKU cost and margin records

## Fee Structure Reference

### Shopify Platform Fees (transaction fees on top of plan cost)
| Plan | Transaction Fee (non-Shopify Payments) |
|------|----------------------------------------|
| Basic | 2.0% |
| Shopify | 1.0% |
| Advanced | 0.5% |
| Plus | 0.15% |
| Shopify Payments | 0% transaction fee |

### Payment Processing Fees (Shopify Payments)
| Plan | Online Rate |
|------|-------------|
| Basic | 2.9% + 30¢ |
| Shopify | 2.6% + 30¢ |
| Advanced | 2.4% + 30¢ |

### Stripe (if used instead of Shopify Payments)
- Standard: 2.9% + 30¢ per transaction
- Plus Shopify transaction fee on top

## Analysis Framework

### 1. Revenue Breakdown
- Gross revenue (order total)
- Refunds and chargebacks deducted
- Net revenue = Gross - Refunds

### 2. Cost Stack (deducted from net revenue)
1. **COGS** — product cost, packaging, manufacturing
2. **Shopify platform fee** — transaction % based on plan
3. **Payment processing fee** — Stripe/Shopify Payments % + fixed
4. **Shipping cost** — label cost minus any shipping collected from customer
5. **Ad spend attribution** — ad spend / units sold (blended) or per-order if tracked
6. **Returns/refunds reserve** — estimated return rate × avg order value
7. **Other variable costs** — fulfillment center fees, insert cards, etc.

### 3. Profit Margin Benchmarks
| Status | Net Margin | Action |
|--------|-----------|--------|
| Healthy | > 20% | Maintain, scale ad spend |
| Warning | 10–20% | Audit fees and COGS, reduce waste |
| Danger | < 10% | Stop scaling, fix cost structure immediately |
| Loss | < 0% | Pause ads, renegotiate COGS or raise price |

### 4. Contribution Margin Analysis
- Contribution Margin = Revenue - Variable Costs (COGS + fees + shipping + ads)
- Fixed costs (Shopify plan, apps, staff) allocated across unit volume
- Break-even units = Fixed Costs / Contribution Margin per Unit

### 5. Ad Attribution Methods
- **Blended ROAS**: Total Revenue / Total Ad Spend (store-wide view)
- **Per-product**: Ad spend tagged to product × units sold
- **MER (Marketing Efficiency Ratio)**: Total Revenue / Total Marketing Spend (most reliable for multi-channel)

### 6. Trend Analysis
- Month-over-month margin movement
- Margin erosion detection (fees crept up, COGS increased, shipping surcharge added)
- Best and worst performing SKUs by net margin

## Output Format

Every profit calculation outputs:
1. **Net Profit Summary** — revenue, total costs, net profit, net margin %
2. **Cost Waterfall** — each deduction line-item with $ amount and % of revenue
3. **Margin Status** — Healthy / Warning / Danger / Loss with color signal
4. **Highest Impact Fix** — single biggest lever to improve margin
5. **Comparison** — vs. industry benchmark and vs. prior period if data available

## Rules

1. Always ask for COGS and Shopify plan before calculating — these are the two biggest variables
2. Never assume payment processor; ask if Shopify Payments or Stripe/other is in use
3. Show every deduction line by line — no black-box totals
4. Flag if ad spend attribution is blended vs. per-order (blended understates product-level margin)
5. Warn when a product's contribution margin is positive but net margin is negative (fixed cost allocation issue)
6. Save COGS data to `~/shopify-profit/products.md` when set cogs command is used
7. Always express margin as both $ per unit and % of revenue
