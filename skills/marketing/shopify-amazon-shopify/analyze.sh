#!/usr/bin/env bash
# shopify-amazon-shopify — Amazon to Shopify migration and dual-channel strategy
set -euo pipefail

INPUT="${*:-}"
if [ -z "$INPUT" ]; then
  echo "Usage: Amazon to Shopify strategy: <product category>"
  exit 1
fi

SESSION_ID="shopify-amz-migration-$(date +%s)"

PROMPT="You are a Shopify ecommerce expert specializing in Amazon-to-Shopify migrations, DTC brand building for marketplace sellers, and dual-channel commerce strategy. Build a complete Amazon-to-Shopify strategy for: ${INPUT}

Produce a complete migration and dual-channel strategy report with these sections:

## 1. Strategic Assessment: Migration Options
- Full migration: moving all sales to Shopify — pros, cons, risk analysis
- Dual-channel: running Amazon and Shopify simultaneously — management complexity
- Shopify-first strategy: prioritizing DTC growth while maintaining Amazon
- Decision framework: revenue threshold, brand equity, and margin analysis

## 2. DTC Brand Building for Amazon Sellers
- Differentiating from generic Amazon listings: brand story, design, voice
- Packaging and unboxing experience design to delight DTC customers
- Product photography upgrade: lifestyle vs white background comparison
- Building brand identity elements: logo, colors, typography for Shopify

## 3. Traffic Acquisition Strategy
- Paid social (Meta, TikTok): cold traffic campaigns for brand awareness
- SEO and content: product-focused blog strategy for organic traffic
- Email marketing from day one: list building priority for new Shopify store
- Google Ads: Shopping campaigns for product discovery

## 4. Amazon Customer Email Capture (Legal Methods)
- Insert card strategy: driving Amazon buyers to Shopify with incentive
- Product registration flow: warranty or bonus content email capture
- Review request email sequences (compliant with Amazon TOS) with DTC offer
- Brand story inserts that build awareness of your direct store

## 5. Shopify Store Foundation for Ex-Amazon Sellers
- Store design priorities: trust signals that Amazon provides automatically
- Review collection: importing Amazon reviews and building new ones
- Checkout optimization: Amazon buyers expect seamless checkout
- Shipping expectations: Prime-like delivery communication

## 6. Dual-Channel Operations Management
- Inventory allocation: percentage split between Amazon and Shopify
- Pricing strategy: MAP enforcement and channel-specific pricing
- Fulfillment routing: FBA for Amazon, 3PL or in-house for Shopify
- Analytics: measuring each channel's contribution and true margin

## 7. 90-Day Migration Roadmap
- Immediate actions (week 1): Shopify store setup, domain, first products live
- Short-term (month 1): first paid traffic, email list building, DTC order experience
- Long-term (month 3+): DTC at 20%+ of revenue, loyalty program, brand asset building

Include specific metrics: Amazon vs Shopify margin comparison (Amazon takes 15%+ fees), LTV advantage of owning customer data, and typical 6-month revenue ramp for Amazon sellers launching Shopify."

openclaw agent --local --message "${PROMPT}" --session "${SESSION_ID}"
