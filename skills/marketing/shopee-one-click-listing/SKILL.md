---
name: shopee-one-click-listing
description: "Shopee one-click product listing and cross-platform publishing agent. Efficiently create, optimize, and publish Shopee listings, enable one-click cross-listing across multiple platforms, and manage product catalog operations. Triggers: shopee listing, shopee publish, shopee product upload, one-click listing, shopee cross-listing, shopee catalog, product listing creation, shopee image, shopee description, multi-platform listing, shopee store management"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/shopee-one-click-listing
install_source: official
install_method: download
skill_id: official_ebhrvm29
enabled_at: 1787231150017
version: 1.0.0
name_zh: Shopee 一键商品上架代理
---

# Shopee One-Click Listing Agent

Create optimized Shopee product listings in one step — from raw product data to publish-ready listing with SEO-optimized title, compelling description, strategic pricing, and category configuration. Cross-list to multiple Shopee markets effortlessly.

## Commands

```
listing create <product>          # create full Shopee listing from product info
listing optimize <listing>        # optimize existing Shopee listing
listing localize <listing> <market> # adapt listing for specific SEA market
listing cross-publish <listing>   # generate listings for multiple markets
listing category <product>        # find correct Shopee category path
listing attributes <category>     # list required attributes for a category
listing image guide <product>     # image requirements and optimization guide
listing price <product> <market>  # pricing recommendation for market
listing checklist <listing>       # pre-publish quality checklist
listing report <product>          # full listing optimization report
```

## What Data to Provide

- **Product information** — name, description, specs, materials, dimensions
- **Images** — number and type of images you have
- **Cost price** — for pricing recommendation
- **Target market** — which Shopee market (SG, MY, TH, ID, PH, VN, TW)
- **Competitor listings** — similar products for benchmarking

## Shopee Listing Framework

### Listing Elements Checklist

```
Required:
[ ] Product title (max 120 chars)
[ ] Category path (accurate)
[ ] Price (in local currency)
[ ] Stock quantity
[ ] Shipping weight and dimensions
[ ] At least 1 image (recommend 9 images)

Strongly Recommended:
[ ] 6-9 images including lifestyle shots
[ ] Short description (highlights/bullets)
[ ] Long description (detailed info)
[ ] All product attributes filled
[ ] Variations set up (if applicable)
[ ] Wholesale pricing configured
```

### Title Optimization

**Shopee title formula:**
`[Brand (if applicable)] [Product Type] [Key Feature] [Attribute: Size/Color/Material] [Use Case/Occasion]`

**Title rules:**
- 100-120 characters (use close to max)
- Lead with highest-search keyword
- Include 2-3 key attributes buyers filter by
- Avoid ALL CAPS (poor readability)
- Include local language terms for SEA markets

**Title examples:**
```
Bad:  "Water Bottle"
Good: "Stainless Steel Water Bottle 500ml Insulated Thermos Coffee Tea Hot Cold Gym Sport"

Bad:  "Phone Case iPhone"
Good: "iPhone 15 Pro Max Case Transparent MagSafe Compatible Shockproof Anti-Yellow TPU Cover"
```

**Market-specific title adaptations:**
```
SG/MY: English-first, include product specs precisely
ID:    Bahasa Indonesia terms, include "premium" or "import" for trust
TH:    Thai keywords in description minimum, English OK in title
PH:    English with Filipino lifestyle context
VN:    Vietnamese-friendly terms, quality signals important
TW:    Traditional Chinese preferred, quality and certification focus
```

### Image Requirements and Optimization

**Image specifications:**
- Minimum: 500×500 pixels
- Recommended: 2000×2000 pixels (allows zoom)
- Format: JPG, PNG, or BMP
- Main image: Product on white or clean background
- Maximum 9 images per listing

**Image sequence strategy:**
```
Image 1: Main product (white background, hero shot)
Image 2: Product from different angle / multiple pieces
Image 3: Lifestyle shot (product in use context)
Image 4: Key feature close-up / infographic
Image 5: Size comparison or dimension callout
Image 6: Material / quality detail shot
Image 7: Packaging / what's in the box
Image 8: Use case / occasion shot
Image 9: Brand story / certificate / guarantee
```

### Description Framework

**Short description (bullet points — visible above fold):**
```
✓ [Primary benefit] — [supporting detail]
✓ [Material/quality spec]
✓ [Key feature + why it matters]
✓ [Compatibility / sizing info]
✓ [What's included in package]
```

**Long description structure:**
```
PRODUCT OVERVIEW
[2-3 sentences explaining what the product is and who it's for]

KEY FEATURES
✓ Feature 1: [Detail]
✓ Feature 2: [Detail]
✓ Feature 3: [Detail]

SPECIFICATIONS
Material: [spec]
Dimensions: [L×W×H] cm / [weight] g
Color options: [list]
Package contents: [list]

HOW TO USE / CARE INSTRUCTIONS
[Simple numbered steps if relevant]

SHIPPING & RETURNS
Ships within [X] business days
[Return policy statement]

[BRAND STORY — 1-2 sentences about brand quality commitment]
```

### Pricing Strategy for Shopee

**Pricing framework:**
1. Calculate floor price (cost + fees + minimum margin)
2. Research competitor price range on Shopee
3. Set strategic price position:

```
Penetration (new listing): Set at -10% vs. median competitor
Growth (50+ reviews): Set at market median
Premium (100+ reviews, top-rated): Set at +10-20% with strong differentiation

Shopee fees to account for:
Commission: 2-5% (varies by category and seller tier)
Transaction fee: 2%
```

**Flash sale pricing:**
- Platform flash deals require min 20% discount from regular price
- Set regular price accounting for frequent promotions
- Formula: Regular price = Target sell price / (1 - max discount %)

### Variation Setup

**Shopee variation types:**
```
Single variation: Size (S, M, L, XL, XXL)
                  Color (Red, Blue, Black, White)
                  Material (Cotton, Polyester, Silk)

Double variation: Size × Color (Red S, Red M, Blue S, Blue M...)
                  Volume × Flavor (100ml Vanilla, 100ml Chocolate...)
```

**Variation naming conventions:**
- Use clear, customer-facing names (not internal SKU codes)
- Keep consistent naming across all products
- Add "Free Size" or "One Size" for non-varying dimension

### Cross-Market Publishing

When listing in multiple Shopee markets:
```
Base: Create listing in primary market (e.g., SG)
Adapt for each market:
├── Currency: Convert price to local currency at current rate
├── Title: Add local language keywords where needed
├── Description: Localize measurements (cm vs. inches), terminology
├── Shipping: Set correct shipping from your warehouse to each country
└── Compliance: Check category restrictions per country
```

**Price conversion guide:**
```
If SG base price = SGD $25:
MY:  MYR 85   (×3.4 approx)
TH:  THB 630  (×25 approx)
ID:  IDR 295,000 (×11,800 approx)
PH:  PHP 950  (×38 approx)
VN:  VND 430,000 (×17,200 approx)
TW:  TWD 590  (×23.6 approx)
```

### Pre-Publish Checklist

```
CONTENT
[ ] Title: 100-120 chars, keyword-rich, readable
[ ] Description: short + long both filled
[ ] All product attributes completed
[ ] Correct category path selected

IMAGES
[ ] 9 images uploaded (minimum 4)
[ ] Main image: white background, product centered
[ ] At least 1 lifestyle image
[ ] At least 1 infographic/spec callout

PRICING & STOCK
[ ] Price competitive with top 10 listings
[ ] Stock quantity set accurately
[ ] Shipping weight/dimensions filled
[ ] Variations configured correctly (if applicable)

LOGISTICS
[ ] Shipping options enabled
[ ] Processing time set (1-2 days standard)
[ ] Shipping fee correctly set or free shipping enabled
```

## Workspace

Creates `~/shopee-listings/` containing:
- `drafts/` — listing drafts before publishing
- `published/` — records of published listings by market
- `images/` — image requirements and optimization notes
- `pricing/` — price sheets by market
- `reports/` — listing performance reports

## Output Format

Every listing creation outputs:
1. **Optimized Title** — final title with character count for each market
2. **Short Description** — 5 bullet points, ready to paste
3. **Long Description** — full HTML-compatible description
4. **Attribute Checklist** — required attributes for the selected category
5. **Pricing Recommendations** — suggested price per market with margin calculation
6. **Image Guide** — specific guidance on what images to prepare
7. **Pre-Publish Checklist** — complete verification before going live
8. **Cross-Market Variants** — adapted listings for each target market
