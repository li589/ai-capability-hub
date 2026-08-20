---
name: amazon-fba-calculator
description: "Amazon FBA profit calculator. Input product price, COGS, dimensions, weight, and ad spend — get true net profit, margin, ROI, and break-even ACoS. Triggers: fba calculator, fba fees, amazon profit calculator, fba profit, amazon margin, fba fee calculator, amazon net profit, fba cost, product profitability, amazon roi, break-even acos, fba revenue calculator, amazon seller profit, cogs calculator, fba fulfillment fee"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-fba-calculator
install_source: official
install_method: download
skill_id: official_whJFYqtq
enabled_at: 1787231850281
version: 1.0.0
name_zh: 亚马逊 FBA 利润计算器
---

# Amazon FBA Profit Calculator

Calculate true net profit for any Amazon product — accounting for all fees, costs, and ad spend. Know your real margin before you source.

## Commands

```
fba calc                        # interactive profit calculation
fba calc [price] [cogs] [weight]  # quick calculation with known values
fba fees                        # show current FBA fee schedule
fba break-even                  # calculate break-even ACoS
fba compare [price1] [price2]   # compare two price points
fba save [product-name]         # save product profile
fba history                     # show saved products
```

## What Data to Provide

- **Sale price** — your selling price on Amazon
- **COGS** — product cost + freight to Amazon warehouse
- **Dimensions & weight** — for FBA fulfillment fee calculation
- **Category** — for referral fee %
- **Ad spend / ACoS** — optional, for true profit with PPC
- **Other costs** — prep fees, photography, samples

No API keys needed. Works from verbal descriptions or exact numbers.

## Fee Structure (2024–2025)

### Amazon Referral Fees by Category
| Category | Referral Fee |
|----------|-------------|
| Most categories | 15% |
| Electronics | 8% |
| Clothing & Accessories | 17% |
| Jewelry | 20% (up to $250) |
| Books, Music, Video | 15% |
| Computers | 8% |
| Furniture | 15% (+ $30 min) |
| Automotive | 12% |

### FBA Fulfillment Fees (2025 US)
| Size Tier | Weight | Fee |
|-----------|--------|-----|
| Small Standard | ≤4 oz | $3.06 |
| Small Standard | 4–8 oz | $3.15 |
| Small Standard | 8–12 oz | $3.24 |
| Large Standard | ≤4 oz | $3.68 |
| Large Standard | 1 lb | $4.51 |
| Large Standard | 2 lb | $5.22 |
| Large Standard | +1 lb | +$0.38/lb |
| Large Bulky | up to 50 lb | $9.73 + $0.42/lb over 1lb |

### Additional Fees to Include
- **FBA Storage**: $0.78/cubic foot/month (Jan–Sep), $2.40 (Oct–Dec)
- **Monthly Storage**: estimate based on sell-through rate
- **Prep/Labeling**: $0.55/unit (Amazon prep service)
- **Returns**: ~2–5% of revenue depending on category

## Calculation Formula

```
Gross Revenue       = Sale Price
- Referral Fee      = Sale Price × Referral %
- FBA Fee           = Based on size/weight tier
- COGS              = Product cost + inbound freight
- PPC Cost          = Sale Price × ACoS
- Storage           = (Units/month × cubic feet × rate) / units sold
- Other Costs       = Prep + photography amortized
─────────────────────────────────────
Net Profit          = Revenue - All costs above
Net Margin %        = Net Profit / Sale Price × 100
ROI                 = Net Profit / COGS × 100
Break-even ACoS     = Net Margin % (before PPC)
```

## Output Format

Every calculation outputs:
1. **P&L Table** — line-by-line cost breakdown
2. **Key Metrics** — Net Profit / Margin / ROI / Break-even ACoS
3. **Sensitivity Analysis** — profit at ±10%, ±20% price changes
4. **Risk Flags** — margin below 15%, storage risk, high referral fee categories
5. **Optimization Tips** — specific suggestions to improve margin

## Rules

1. Always show full fee breakdown — never hide line items
2. Flag when margin is below 15% (risky for Amazon sellers)
3. Include seasonal storage surcharge warning for Q4
4. Show both pre-PPC and post-PPC margins
5. Ask for category if not provided — referral fee varies significantly
6. Note when estimated values are used vs. exact inputs

## Benchmarks

| Metric | Healthy | Warning | Danger |
|--------|---------|---------|--------|
| Net Margin | >25% | 15–25% | <15% |
| ROI | >50% | 30–50% | <30% |
| Break-even ACoS | >25% | 15–25% | <15% |
| Storage/Revenue | <3% | 3–8% | >8% |
