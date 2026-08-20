---
name: amazon-pricing-strategy
description: "Amazon pricing strategy and repricing agent. Set competitive prices, build repricing rules, analyze Buy Box win rate, plan promotional pricing, and balance margin vs. volume. Works for private label and resellers. Triggers: amazon pricing, repricing, buy box, price strategy, amazon price, competitive pricing, price optimization, dynamic pricing, buy box winner, price war, margin optimization, amazon repricer, price elasticity, promotional pricing, amazon price strategy"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/amazon-pricing-strategy
install_source: official
install_method: download
skill_id: official_GTFQcY8Y
enabled_at: 1787231158850
version: 1.0.0
name_zh: 亚马逊定价策略
---

# Amazon Pricing Strategy Agent

Set the right price to win Buy Box, maximize revenue, and protect margins. From launch pricing to long-term repricing rules — your pricing co-pilot.

## Commands

```
price analyze [product]         # full pricing strategy analysis
price launch [cogs] [market]    # optimal launch price recommendation
price buybox [situation]        # Buy Box win strategy
price reprice [rules]           # set up repricing logic
price elastic [data]            # price elasticity analysis
price promo [type]              # promotional pricing plan
price floor [cogs]              # calculate minimum viable price
price compare [competitors]     # competitive price positioning
price seasonal                  # seasonal pricing calendar
```

## What Data to Provide

- **Your COGS** (landed cost per unit)
- **Current price & sales velocity**
- **Competitor prices** — paste from search results
- **Buy Box win rate** — from Seller Central
- **Target margin %** — your profit floor
- **Product stage** — launch / growth / mature / declining

## Pricing Strategy by Stage

### Stage 1: Launch Pricing (First 30–60 days)
**Goal**: Velocity over margin — get reviews and ranking fast

| Approach | Price Point | When to Use |
|----------|------------|-------------|
| Aggressive launch | 10–20% below market average | New product, competitive category |
| Parity launch | Match #1 competitor | Differentiated product, strong listing |
| Premium launch | 10–15% above average | Clear differentiation, strong brand |

**Launch pricing formula**:
```
Floor price = COGS × 1.3 (30% minimum margin during launch)
Market average = average of top 5 competitor prices
Launch price = max(Floor price, Market average × 0.85)
```

### Stage 2: Growth Pricing (60–180 days)
**Goal**: Balance velocity and margin

- Raise price $1–2 every 2 weeks as reviews accumulate
- Stop raising when sales velocity drops >15%
- Target: get to your "full price" within 90 days of launch

### Stage 3: Mature Pricing (180+ days)
**Goal**: Maximize profit, defend position

- Monitor competitor prices weekly
- Reprice within a defined band (floor to ceiling)
- Use promotions to stimulate volume during slow periods

### Stage 4: Declining (Low BSR, high competition)
**Goal**: Liquidate cleanly or relaunch

- Drop price to move inventory before storage fees spike
- Consider removal if margin-negative

## Buy Box Strategy

### How Amazon Decides Buy Box Winner (Private Label)
For your own brand (no other sellers): You win Buy Box if:
- Account Health is Good
- You have FBA inventory available
- Price is competitive vs. your own historical pricing
- Not flagged for high-price violation

### Buy Box for Resellers (Multi-Seller Competition)
Amazon's algorithm weights:
1. **Price** (most important) — lowest landed price often wins
2. **Fulfillment method** — FBA beats FBM
3. **Seller metrics** — ODR, late shipment rate
4. **Inventory availability** — in-stock wins
5. **Account health** — healthy accounts preferred

**Repricing rules for Buy Box:**
```
IF (my price > lowest FBA competitor price + $0.50):
  → Lower price by $0.25
IF (I'm winning Buy Box and margin > target):
  → Try raising price by $0.10 every 24 hours
IF (price hits floor):
  → Stop repricing, accept lower Buy Box share
```

## Price Floor Calculation

Never price below your floor. Calculate it:

```
Minimum viable price = COGS + Amazon fees + minimum profit

Example (Standard product, $9 COGS):
COGS:                    $9.00
Referral fee (15%):      $X × 15%
FBA fee:                 $3.22 (large standard, 1lb)
Min profit target:       $2.00
─────────────────────────────
Solve: Price = COGS + FBA + (Price × 0.15) + Min Profit
Price = (9 + 3.22 + 2) / (1 - 0.15) = $16.73 floor
```

## Promotional Pricing Playbook

### Lightning Deals
- Minimum discount: 15–20% off regular price
- Amazon selects eligible products (can't self-submit all products)
- Best timing: Prime Day, Black Friday, Cyber Monday
- Cost: $150–$300 per deal slot (varies by event)
- ROI: Best for BSR ranking boost, not pure profit

### Coupons
- Clip-and-save badge improves CTR (green badge visible in search)
- Set 5–20% discount (lower amounts still get the badge)
- Cost: $0.60 per redemption
- Best for: Driving trial on new products, price-sensitive categories

### Prime Exclusive Discounts
- Only shown to Prime members
- Requires: 10%+ discount, 3+ star rating
- Shows strikethrough price in search — strong CTR driver

### BOGO / Multi-unit
- "Buy 2, get 10% off" — increases average order value
- Good for consumables, multi-pack strategy

## Price Elasticity Framework

Without sales data, estimate elasticity by category:

| Category Type | Elasticity | Meaning |
|--------------|-----------|---------|
| Commodity (generic, many sellers) | High | Small price drop → big volume gain |
| Differentiated (brand, unique features) | Low | Price changes don't move volume much |
| Gift / impulse | Medium | Sweet spot pricing matters |
| Consumable / repeat purchase | Low-Medium | Loyalty reduces price sensitivity |

**To measure your elasticity**:
1. Raise price $2 for 2 weeks, note sales change
2. Drop price $2 for 2 weeks, note sales change
3. Calculate: % change in units / % change in price = elasticity coefficient

## Seasonal Pricing Calendar

| Period | Strategy |
|--------|---------|
| Jan–Feb | Hold or slight discount (post-holiday slowdown) |
| Mar–Apr | Restore full price, spring categories up |
| May–Jun | Stable, prep Prime Day inventory |
| Jul (Prime Day) | Deep discounts day-of, price back up after |
| Aug–Sep | Hold price, prep Q4 |
| Oct | Price up 5–10% before holiday rush |
| Nov (BFCM) | Lightning deals, coupons, max promotion |
| Dec 1–15 | Hold premium price (urgent gift buyers) |
| Dec 16–25 | Drop price to clear remaining inventory |

## Output Format

1. **Price Recommendation** — specific launch or target price with reasoning
2. **Floor Price Calculation** — your absolute minimum viable price
3. **Repricing Rules** — min/max band and trigger conditions
4. **Competitive Positioning** — where you sit vs. top 5 competitors
5. **Promo Calendar** — recommended discount events for next 90 days
