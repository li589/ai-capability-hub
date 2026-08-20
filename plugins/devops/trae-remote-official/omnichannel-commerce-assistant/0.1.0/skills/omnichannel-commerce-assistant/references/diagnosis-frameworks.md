# Operating diagnosis frameworks

Use the shortest path that can explain the decision. For every branch, move from symptom to evidence, likely cause, action, and validation.

## Universal loop

1. Lock the target metric, guardrails, baseline, unit, and period.
2. Reconcile the data and segment the change.
3. Identify the largest driver and distinguish cause from correlation.
4. Rank actions by impact, confidence, effort, time-to-signal, and risk.
5. Define owner, test window, success threshold, and stop condition.

## Seven business capabilities

### Store diagnosis

Decompose profit-quality growth through traffic × conversion × order value × repeat, then subtract refunds and variable costs. Segment by date, channel, SKU/category, new/returning customer, campaign phase, and stock state. Check whether mix shift or definition changes explain the headline before claiming operational improvement or decline.

### Product and category

Classify SKUs by demand, conversion, contribution, refund burden, inventory pressure, and strategic role. Separate hero, profit, traffic, trial, and exit products only when evidence supports the role. Recommend add/hold/fix/exit with a portfolio consequence, not a score alone.

### Bestseller analysis

Define what “bestseller” means for this decision before scoring products: external category momentum, internal sales velocity, contribution quality, durable conversion, content/traffic replicability, repeat or review quality, and replenishment safety. Distinguish a validated hero product from a short promotion spike, paid-traffic artifact, ranking estimate, or stock-constrained candidate. Route deep work to `bestseller-analysis.md`; use `research-tools.md` when external rankings, competitors, creators, or content signals are material.

### Traffic and conversion

Trace exposure → click/visit → product view → cart → paid order → retained value. Separate traffic quality from page/offer conversion and from availability/fulfillment loss. Treat paid attribution as directional unless incrementality is tested.

### Pricing and promotion

Build a price waterfall from list price to paid price, net revenue, gross profit, and contribution. Separate merchant discount, platform subsidy, coupon, ad spend, fee, refund, and fulfillment. Evaluate promotions on incremental contribution and inventory effect, not GMV alone.

### Inventory and supply

Combine demand rate, lead time, safety stock, sellable inventory, inbound stock, aging, stockout exposure, and cash constraint. Separate demand miss from supply miss. Use scenarios when forecast error or promotion lift is uncertain.

### Retention and membership

Use acquisition cohorts and a defined observation window. Compare repeat rate, purchase frequency, net revenue, margin, product path, and channel. Distinguish true retention from campaign timing, subscription mechanics, or one-off stock replenishment.

## Hypothesis discipline

When evidence is insufficient, list at most three ranked hypotheses. For each, name the signal that supports it, the data that would disprove it, and the cheapest next test. Do not expand the framework merely to fill a report.
