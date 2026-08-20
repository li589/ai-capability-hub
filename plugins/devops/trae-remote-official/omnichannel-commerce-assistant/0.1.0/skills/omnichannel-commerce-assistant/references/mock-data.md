# Generate rare mock data

Use this reference only after the parent Skill's rare mock-data gate is satisfied. It provides e-commerce scenario design, not a bundled dataset or a general fallback for missing evidence.

## Contents

- Trigger and refusal gate
- Generation workflow
- Scenario modules
- Coherence and anomaly rules
- File and presentation rules
- Validation checklist

## Trigger and refusal gate

Generate mock data only when one of these conditions holds:

- the user explicitly requests mock, sample, synthetic, fictional, or demo data;
- the user wants to trial an analysis workflow before connecting real data;
- a prototype, template, operating workbench, or dashboard needs populated states to demonstrate behavior;
- the parent Skill selected the smallest labeled simulation for an explicitly requested prototype or demo with no real data.

Do not generate it merely because real store data is absent. Do not offer it for ordinary strategy, platform planning, market sizing, trend research, bestseller discovery, competitor benchmarking, or factual diagnosis. Use public research for observable external facts and labeled assumptions for planning. Mock data must never support a claim about the user's actual business, a real category, a platform, or a competitor.

If the user explicitly asks for a realistic simulation of a named real brand or competitor, fictionalize entity names and state that the distributions are illustrative unless the user supplies authorized source data.

## Generation workflow

1. Define the demonstration decision: what should the user be able to inspect, filter, diagnose, or decide?
2. Select one primary scenario module and no more than two supporting modules.
3. Set grain, time range, entity count, currency, timezone, channel, category, and lifecycle stage.
4. Create only the tables and fields needed to demonstrate that decision.
5. Plant one to three interpretable patterns or anomalies with explicit causal relationships.
6. Generate values from coherent equations and shared keys, not independent random numbers.
7. Validate identities, dates, totals, ranges, and cross-table joins.
8. Mark the dataset, file metadata, visible UI, charts, and derived conclusions as simulated, using the user's language.

When a standalone `.xlsx`, `.csv`, or similar file is needed, use the current official/runtime spreadsheet or file skill for creation, formulas, formatting, and validation. This reference only controls business schema and simulation logic. When the data exists solely to populate a workbench prototype, generate it in the application's required local format instead of creating a redundant workbook.

## Scenario modules

Choose the smallest sufficient module set.

### Store health and conversion funnel

Use for operating-overview, decline diagnosis, target tracking, or daily cockpit demonstrations.

Recommended grain: one row per date × platform/store, usually 28–90 days.

Core fields: `date`, `platform`, `store_id`, `impressions`, `visitors`, `product_viewers`, `add_to_cart_users`, `order_buyers`, `orders`, `gmv`, `refund_amount`, `ad_spend`, `new_buyers`.

Derived identities: conversion rate = buyers / visitors; AOV = GMV / orders; refund rate uses one declared denominator; ROAS = attributed GMV / ad spend. Keep funnel stages non-increasing when they represent the same cohort.

Useful patterns: traffic rises while conversion falls; campaign GMV grows but net revenue and margin deteriorate; a tracking break creates a visible discontinuity.

### Product and category portfolio

Use for SKU matrix, assortment, hero-product, price-band, or category-role demonstrations.

Recommended grain: one row per date/week × SKU.

Core fields: `sku_id`, `product_name`, `category`, `product_role`, `list_price`, `paid_price`, `units`, `gmv`, `product_cost`, `platform_fee`, `ad_spend`, `refund_units`, `rating`, `review_count`.

Useful patterns: high-GMV loss leader; high-margin low-exposure opportunity; hero SKU concentration risk; price-band cannibalization; new-product ramp with incomplete reviews.

### Traffic, content, and conversion

Use for channel mix, content-commerce, live-stream, short-video, search, recommendation, or creator-analysis demonstrations.

Recommended grain: one row per date × source/content/account.

Core fields: `source`, `content_id`, `account_id`, `content_type`, `publish_time`, `impressions`, `clicks`, `product_visitors`, `buyers`, `attributed_gmv`, `spend`, `engagements`, `live_duration_minutes`.

Useful patterns: high engagement but weak product click-through; paid traffic hides declining organic conversion; one creator drives volume but has high refund or low contribution margin.

Do not label simulated rankings or sales estimates as data from any real intelligence vendor or platform.

### Pricing and promotion

Use for discount ladders, campaign economics, coupon rules, bundle testing, or price-sensitivity demonstrations.

Recommended grain: one row per campaign × SKU × day or test cell.

Core fields: `campaign_id`, `sku_id`, `mechanic`, `start_date`, `end_date`, `reference_price`, `paid_price`, `coupon_cost`, `platform_subsidy`, `merchant_subsidy`, `units`, `gmv`, `gross_margin`, `incremental_orders`.

Useful patterns: nominal discount differs from customer-paid discount; GMV uplift fails to cover subsidy; promotion pulls demand forward; bundles raise AOV but reduce attach-rate quality.

### Inventory and supply

Use for stockout risk, replenishment, aging, fulfillment, or supply-planning demonstrations.

Recommended grain: one row per date × SKU × warehouse.

Core fields: `warehouse_id`, `sku_id`, `on_hand`, `available`, `in_transit`, `reserved`, `daily_sales`, `lead_time_days`, `reorder_point`, `stockout_hours`, `aged_days`, `fulfillment_time_hours`, `cancelled_units`.

Useful patterns: hero SKU stockout suppresses conversion; excess tail inventory ties up cash; lead-time variability invalidates a static reorder point; inventory totals reconcile with movements.

### Orders, retention, and membership

Use for cohort, repurchase, lifecycle, member-tier, or CRM workbench demonstrations.

Recommended grain: order line plus customer snapshot or cohort aggregate; use fictional customer IDs only.

Core fields: `order_id`, `customer_id`, `order_time`, `sku_id`, `quantity`, `paid_amount`, `refund_amount`, `first_order_date`, `acquisition_channel`, `member_tier`, `coupon_used`, `days_since_previous_order`.

Useful patterns: acquisition grows but 30/60/90-day repeat weakens; a member tier has high revenue but low incremental lift; one acquisition channel has strong first order and weak retained value.

Never generate names, phones, addresses, emails, government identifiers, payment credentials, or realistic personal data.

### Cross-border unit economics and fulfillment

Use for marketplace/site comparison, landed margin, return exposure, currency, or fulfillment-route demonstrations.

Recommended grain: one row per order/SKU × destination × fulfillment route, plus an exchange-rate table when needed.

Core fields: `site`, `destination_country`, `currency`, `fx_rate`, `sku_id`, `local_price`, `units`, `product_cost_cny`, `international_freight`, `duty_tax`, `marketplace_fee`, `payment_fee`, `fulfillment_fee`, `return_cost`, `ad_spend`, `contribution_margin`, `delivery_days`.

Useful patterns: revenue growth loses margin after freight and returns; FX movement changes contribution; faster fulfillment lifts conversion but raises fixed inventory exposure.

Use fictional fee and tax values unless sourced current values are kept in a separate evidence table. Never blend sourced rules into simulated observations without an explicit field-level label.

## Coherence and anomaly rules

- Use stable IDs and valid foreign keys across tables.
- State currency, timezone, tax treatment, attribution window, and refund denominator once in a data dictionary.
- Make totals reconcile within declared rounding tolerance.
- Keep prices, units, stock, costs, and dates non-negative unless a documented adjustment row requires otherwise.
- Avoid pure random noise. Add seasonality, weekday effects, campaign windows, lifecycle curves, or lead-time effects only when they help the demonstration.
- Preserve believable lag: content precedes attributed orders, replenishment follows lead time, refunds follow purchases, and repeat purchases follow first orders.
- Include a compact `scenario_notes` or data-dictionary sheet/table identifying planted signals and intended tests; keep it separate from the analyst-facing tables when a blind demonstration is desired.
- Prefer 30–500 rows for a simple walkthrough and 500–5,000 rows for filter/performance demonstrations. Generate more only when scale behavior itself is under test.

## File and presentation rules

- Name generated files for the scenario, not `mock-template`; for example `simulated-douyin-store-funnel.xlsx`.
- Put `SIMULATED` in the title or first visible sheet/header and in the final delivery summary.
- Include a concise data dictionary with table name, grain, key, field meaning, unit, and formula/relationship.
- Do not conceal planted anomalies as discovered real facts. Explain that findings demonstrate the workflow.
- Do not combine simulated rows and real/user/public rows in one unlabeled table or chart. If comparison is explicitly required, separate them into visibly labeled layers and prevent aggregate totals across evidence classes.
- If real data later arrives, rerun the analysis from the real source and retire all mock-derived conclusions.

## Validation checklist

Before delivery, verify:

- the rare trigger was genuinely satisfied;
- the dataset answers the stated demonstration decision;
- every table has declared grain, key, units, and date scope;
- formulas and aggregate identities reconcile;
- joins have no unintended orphan or duplicate keys;
- planted patterns are detectable but not mechanically obvious;
- no personal, confidential, or deceptive real-world data appears;
- every artifact and conclusion is visibly labeled as simulated;
- no simulated value is cited as public or store evidence.
