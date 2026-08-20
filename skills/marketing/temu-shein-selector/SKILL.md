---
name: temu-shein-selector
description: "Temu, SHEIN, AliExpress, and TikTok product selection big data analysis agent. Identify trending products, analyze competition, estimate demand, and find sourcing opportunities across fast-fashion and marketplace platforms. Triggers: temu product selection, shein product research, aliexpress trending, tiktok shop products, temu selector, fast fashion products, temu trending, shein trends, product sourcing, dropshipping products, temu winning products"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/temu-shein-selector
install_source: official
install_method: download
skill_id: official_hhVMAbcO
enabled_at: 1787231044379
version: 1.0.0
name_zh: Temu/SHEIN/AliExpress/TikTok 选品助手
---

# Temu / SHEIN / AliExpress / TikTok Product Selector

Big data-driven product selection for the world's fastest-growing e-commerce platforms. Identify trending products before the market saturates, analyze competition levels, and find winning items to source.

## Commands

```
select temu <category>            # find trending products on Temu
select shein <category>           # identify SHEIN trending items
select ali <keyword>              # AliExpress trending product analysis
select tiktok <niche>             # TikTok Shop viral product identification
select score <product>            # score a product for multi-platform potential
select compare <platform1> <platform2> # compare same product across platforms
select trending                   # daily trending products across all platforms
select source <product>           # sourcing recommendations for a product
select entry <product>            # market entry analysis for new product
select report <product>           # full cross-platform product report
```

## What Data to Provide

- **Platform and category** — which platform and what type of product
- **Trending data** — paste Temu/SHEIN/TikTok trending product listings
- **Sales data** — units sold, reviews, orders shown on listing
- **Price data** — selling price and estimated cost from Alibaba
- **Competition data** — number of similar sellers, listing quality

## Product Selection Framework

### Temu Product Selection

**Temu business model specifics:**
- Seller provides cost price; Temu sets final price
- Margin = (Temu settlement price) - (your cost) - (shipping)
- Temu promotes heavily discounted items → need low COGS
- Quality standard enforcement — defect rate must stay <2%

**Temu winning product criteria:**
```
[ ] Alibaba cost price <$2 for sub-$10 Temu item (>50% margin)
[ ] Product weight <200g (shipping cost critical)
[ ] Not restricted category (no food, meds, hazmat)
[ ] Strong visual appeal (drives Temu browse behavior)
[ ] Unique or trending design (not commodity)
[ ] High order count on similar items (>500 orders = validated)
[ ] Manageable defect risk (simple product = low defect rate)
```

**Temu category opportunities:**
```
High opportunity: Home decor, phone accessories, jewelry, pet products
Medium opportunity: Clothing basics, kitchen gadgets, toy novelties
Avoid: Electronics (high defect/return), perishables, fragile items
```

### SHEIN Product Selection

**SHEIN model**: Fast fashion, 2-week trend cycles
- New styles added daily — trend speed is extreme
- Small batch production (50-100 units) acceptable
- Quality threshold: acceptable for fast fashion price point

**SHEIN winning product signals:**
```
[ ] Fashion-forward design (1-2 weeks ahead of mainstream)
[ ] Price point: $5-$25 sweet spot
[ ] Minimum 4 sizes (S/M/L/XL)
[ ] Photogenic — strong visual on model
[ ] Trending color/print for the season
[ ] Similar items already selling on SHEIN (validation)
[ ] Sourceable quickly (2-4 week turnaround)
```

**Trend identification for SHEIN:**
- Monitor TikTok fashion hashtags (#OOTD, #fashiontrend)
- Check Pinterest trending boards weekly
- Analyze SHEIN "New In" and "Trending" sections
- Use Google Trends for fashion terms

### AliExpress Product Selection

**AliExpress modes:**
- Dropshipping: sell first, ship directly from supplier
- Wholesale: buy inventory, ship yourself
- Hybrid: test with dropship, transition to stock

**AliExpress opportunity signals:**
```
Monthly orders >500:  Validated demand
Price margin >60%:    Viable for dropshipping
Seller rating >95%:   Reliable supplier
Shipping time <15d:   Acceptable for most buyers
Reviews >100:         Product quality validated
Rising trend:         Look for 20%+ order growth over 3 months
```

**Finding trending AliExpress products:**
1. Sort by "Orders" in category — find high-velocity items
2. Filter by "Ship from overseas" for faster delivery
3. Compare with Temu listings — if on Temu already at lower price, competition may be hard
4. Check launch date — recent listings with high orders = catching a trend

### TikTok Shop Product Selection

**TikTok virality requirements:**
- Product must be demonstrable in 15-60 seconds
- "Before/after" or "transformation" products perform best
- Visual impact critical (color, size reveal, satisfying mechanism)
- Relatable problem → satisfying solution format

**TikTok winning product formula:**
```
TREND × DEMO POTENTIAL × PRICE POINT = Viral Score

Trend:           Is it already viral? Google Trends rising?
Demo Potential:  Can you show compelling results in <30 seconds?
Price Point:     $10-$40 impulse buy range
```

**TikTok product categories with high viral rates:**
- Beauty gadgets (face massagers, skin tools)
- Kitchen novelties (unique tools, organizers)
- Cleaning products (satisfying demo)
- Fitness accessories (visible results)
- Home organization (before/after)
- Fashion accessories (quick styling tips)

### Cross-Platform Scoring Matrix

Score any product 1-5 on 6 dimensions:

```
1. Trend momentum (growing fast = 5, declining = 1)
2. Competition density (low competition = 5, saturated = 1)
3. Margin potential (>60% margin = 5, <20% = 1)
4. Sourcing ease (readily available = 5, custom only = 1)
5. Shipping friendliness (light/compact = 5, heavy/fragile = 1)
6. Demo/visual appeal (very photogenic = 5, boring = 1)

Total score 25+: Strong multi-platform candidate
Total score 20-24: Good for 1-2 platforms
Total score <20: Likely not worth pursuing
```

### Sourcing Intelligence

For any trending product, sourcing approach:
```
Step 1: Search Alibaba with product category terms
Step 2: Filter: Trade Assurance + >2 years in business + >4.5 rating
Step 3: Get quotes from 5+ suppliers
Step 4: Request samples before ordering (never skip)
Step 5: Negotiate: first order small (100-500 units), grow from there

Target sourcing cost: <25% of final selling price for Amazon
                      <40% of Temu settlement price
                      <30% of SHEIN wholesale price
```

## Workspace

Creates `~/product-selection/` containing:
- `trending/` — daily trending product snapshots by platform
- `evaluated/` — scored product evaluations
- `sourcing/` — supplier notes and quotes
- `pipeline/` — products under active consideration
- `reports/` — platform-specific product reports

## Output Format

Every product selection report outputs:
1. **Product Score Card** — scores on all 6 dimensions with total
2. **Platform Fit Analysis** — which platform(s) best suited and why
3. **Revenue Projection** — estimated monthly revenue at target sell-through
4. **Margin Model** — cost, fees, and net profit per unit
5. **Sourcing Guide** — recommended supplier type, MOQ, target cost
6. **Competition Assessment** — current competition level and trend direction
7. **Go/No-Go Verdict** — clear recommendation with top 3 reasons
