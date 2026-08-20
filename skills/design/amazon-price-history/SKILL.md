---
name: amazon-price-history
description: "Amazon product price history tracker and drop alert agent. Track price trends over time, identify the best time to buy or sell, analyze competitor pricing patterns, and set smart price alerts. Triggers: amazon price history, price tracker, price drop alert, keepa alternative, amazon price trend, historical pricing, price chart, best time to buy, price monitoring, amazon deal finder, price volatility, buy box price"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-price-history
install_source: official
install_method: download
skill_id: official_12HeON4t
enabled_at: 1787231148935
version: 1.0.0
name_zh: 亚马逊商品价格历史追踪器
---

# Amazon Price History Tracker

Track Amazon product price history, identify pricing patterns, and time your pricing decisions with precision. Alternative to Keepa for sellers who want AI-assisted price analysis.

Paste product data, price snapshots, or competitor pricing. The agent builds price timelines, detects patterns, and recommends optimal pricing windows.

## Commands

```
price add <asin> <price> [date]   # log a price data point
price trend <asin>                # analyze price trend direction
price pattern <asin>              # detect seasonal and cyclical patterns
price alert set <asin> <target>   # set alert for target price threshold
price compare <asin1> <asin2>     # compare pricing histories side-by-side
price best-time <asin>            # identify best time window to raise/lower price
price volatility <asin>           # compute price stability score
price chart <asin>                # render text-based price chart
price report <asin>               # full pricing analysis report
price save                        # save all price history to workspace
```

## What Data to Provide

- **ASIN + price data** — current or historical prices with dates
- **Buy Box price** — the winning price you see on the listing
- **Competitor prices** — other sellers on the same listing
- **Your cost structure** — COGS, FBA fees, target margin
- **Seasonal context** — any known promotions or peak periods

## Price Analysis Framework

### Price Data Points to Track

For each ASIN, capture:
```
Date | Price | Seller | Buy Box? | Coupon | Sale Event | Notes
2024-01-15 | $29.99 | Brand | Yes | 10% off | None | Normal
2024-01-20 | $24.99 | Brand | Yes | None | Flash sale | -17%
2024-02-01 | $32.99 | Brand | Yes | None | None | Post-sale
```

### Price Trend Classification

**Uptrend** (Price rising):
- Average price this month > last month by >5%
- Signal: possible demand increase, supply constraints, or brand repositioning
- Seller action: monitor for opportunity to raise your price

**Downtrend** (Price falling):
- Average price this month < last month by >5%
- Signal: increased competition, excess inventory, or market correction
- Seller action: evaluate your cost floor, avoid race-to-bottom

**Stable** (±5% range):
- Price within 5% of 90-day average
- Signal: mature market equilibrium
- Seller action: compete on other factors (listing quality, reviews, ads)

**Volatile** (Frequent swings >10%):
- Price swings more than 10% within 30 days
- Signal: heavy promotional activity or multiple sellers competing
- Seller action: dynamic repricing is essential

### Price Volatility Score

```
Volatility = (Max Price - Min Price) / Average Price × 100

Score 0-10:   Very stable — predictable market
Score 10-25:  Moderate — some promotional activity
Score 25-50:  Volatile — heavy competition or frequent sales
Score 50+:    Highly volatile — use dynamic repricing or avoid
```

### Seasonal Pattern Detection

Map price history against calendar events:
- **Q4 (Oct-Dec)**: Holiday surge — premium pricing possible
- **Prime Day (July)**: Deep discounts expected, plan inventory
- **Back to School (Aug-Sep)**: Category-specific peaks
- **Valentine's/Mother's Day**: Gift category spikes
- **Post-holiday (Jan-Feb)**: Price depression, clear inventory

### Buy Box Price Analysis

The Buy Box price matters more than list price:
- Track who holds the Buy Box at each snapshot
- Compute your price gap vs. current Buy Box winner
- Identify patterns in Buy Box rotation (if multiple sellers)

**Buy Box pricing rules:**
- New seller entering: typically prices 5-10% below current winner
- FBA advantage: can price slightly higher than FBM and still win
- Low inventory: Buy Box may shift to higher-priced seller

### Price Alert Thresholds

```
PRICE DROP ALERT:   Current price falls >10% below 30-day average
PRICE SPIKE ALERT:  Current price rises >20% above 30-day average
BUY BOX LOST:       Your price is no longer the Buy Box winner
COMPETITOR ENTRY:   New seller appears at significantly lower price
FLOOR ALERT:        Price drops below your calculated margin floor
```

### Optimal Repricing Windows

Based on historical patterns:
- **Best time to raise price**: After a competitor goes out of stock
- **Best time to lower price**: 2 weeks before Prime Day to boost velocity
- **Avoid repricing**: During major sale events (prices stabilize after)
- **Post-holiday**: Expect 15-25% price compression, plan ahead

## Margin Floor Calculation

```
Margin Floor = COGS + FBA Fees + Referral Fee + PPC Cost + Minimum Profit
Example:
  COGS:          $8.00
  FBA fees:      $4.50
  Referral (15%): price × 0.15
  PPC cost:      $2.00
  Min profit:    $2.00
  Floor = $8 + $4.50 + (price × 0.15) + $2 + $2 = solve for price
  Minimum price = ($16.50) / (1 - 0.15) = $19.41
```

## Workspace

Creates `~/price-tracker/` containing:
- `history/` — price logs per ASIN (ASIN.md files)
- `alerts/` — triggered price alerts
- `patterns/` — seasonal pattern analysis
- `reports/` — full pricing reports

## Output Format

Every price analysis outputs:
1. **Price Timeline Table** — chronological price history with key events marked
2. **Trend Direction** — current trend with confidence level
3. **Volatility Score** — 0-100 stability rating with interpretation
4. **Pattern Summary** — detected seasonal or cyclical patterns
5. **Optimal Price Window** — recommended price and timing
6. **Margin Check** — current price vs. your floor, profit per unit
