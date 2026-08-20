# Procurement calculation catalog

Use this reference for formulas and interpretation. Declare the commercial basis before calculating. Rates are decimals unless otherwise stated.

## Contents

1. Quote and total cost
2. Price and benchmark analysis
3. Supplier performance and scoring
4. Inventory and replenishment
5. Logistics and trade
6. Sensitivity and decision quality

## 1. Quote and total cost

### Normalized extended cost

`extended_cost = normalized_quantity × normalized_unit_price`

Normalize unit, pack, grade/specification, currency, FX date, tax basis, quantity tier, location, and Incoterm before comparison.

### Landed cost

`landed_cost = goods + origin_charges + main_freight + insurance + duty + nonrecoverable_tax + brokerage + destination_charges + expected_accessorials`

`landed_unit_cost = landed_cost / usable_received_quantity`

Do not count recoverable VAT/GST as economic cost by default. Show cash requirement separately when timing matters. Use expected accessorials only when the probability or historical basis is visible.

### Lifecycle or total cost

`TCO = acquisition + implementation + integration + operation + support + switching + expected_failure_cost - credits - rebates - residual_value`

Keep contractual minimum spend and committed-but-unused capacity visible. Do not call a total “TCO” if it only includes invoice price and freight.

### AI or usage-based services

For each workload class:

`usage_cost = input_tokens_m × input_rate + output_tokens_m × output_rate + cached_input_tokens_m × cached_input_rate + batch_tokens_m × batch_rate`

Then add platform, hosting, fine-tuning, storage, support, minimum-spend shortfall, and expected retry/fallback cost.

`effective_cost_per_accepted_unit = scenario_total_cost / accepted_workload_units`

Use accepted workloads, successful tasks, or quality-adjusted output only when acceptance criteria are defined and measured consistently.

### Savings

`savings = baseline_comparable_cost - proposed_comparable_cost`

State the baseline: last price, current contract, budget, market/index adjusted baseline, or counterfactual. Separate:

- hard savings;
- cost avoidance;
- cash-flow timing;
- one-time implementation cost;
- demand reduction.

## 2. Price and benchmark analysis

### Quantity-weighted average price

`WAP = Σ(quantity_i × comparable_unit_price_i) / Σ(quantity_i)`

Use positive, included quantities only. State treatment for returns, credits, cancellations, partial receipts, and amended prices.

### Price variance / PPV

`PPV = (actual_price - baseline_price) × actual_quantity`

Choose the sign convention once. Label adverse/favorable rather than relying on sign alone.

### Price index

`price_index_t = WAP_t / WAP_base × 100`

Keep specification, site, and currency constant or show a composition-adjusted series.

### Supplier mix bridge

Decompose spend or unit-price change into:

- within-supplier price change;
- supplier-mix change;
- specification/grade change;
- location/freight change;
- FX/tax change;
- unmatched residual.

Do not attribute the residual to negotiation.

### Volatility

`coefficient_of_variation = standard_deviation(price) / mean(price)`

Use only for positive prices and comparable items. For outlier-heavy data, report median and median absolute deviation alongside mean and standard deviation.

### Market-adjusted variance

`market_adjusted_variance = actual_price_change - comparable_benchmark_change`

Align lag, grade, region, unit, and currency. A benchmark relationship is evidence only after checking historical co-movement and contract adjustment rules.

## 3. Supplier performance and scoring

### Delivery

`OTD = on_time_deliveries / eligible_deliveries`

`OTIF = on_time_and_in_full_deliveries / eligible_deliveries`

Declare tolerance window and whether the date is requested, confirmed, ship, or receipt date.

### Quality

`rejection_rate = rejected_units / received_units`

`PPM = defect_units / inspected_or_received_units × 1,000,000`

Do not compare PPM across incompatible inspection coverage or defect definitions.

### Capacity headroom

`headroom = demonstrated_available_capacity - required_capacity`

`headroom_rate = headroom / required_capacity`

Use demonstrated capacity at the relevant bottleneck, not nameplate capacity.

### Weighted score

After gates:

`supplier_score = Σ(weight_j × normalized_metric_j) / Σ(active_weight_j)`

Require:

- weights sum to one within a scenario;
- direction is explicit;
- scale transformation is visible;
- missing values are not converted to zero;
- inactive weights and missing-data treatment are disclosed;
- gate failure is shown separately.

For a benefit metric:

`normalized = (x - minimum) / (maximum - minimum)`

For a cost/risk metric:

`normalized = (maximum - x) / (maximum - minimum)`

Avoid min-max scaling when the candidate set is tiny or unstable; use decision thresholds or anchored scoring instead.

### Concentration

`supplier_share = supplier_spend / total_scope_spend`

`HHI = Σ(supplier_share²)`

Use concentration as exposure, not proof of risk. Add switching time, substitutability, and site/sub-tier commonality.

## 4. Inventory and replenishment

### Inventory position

`inventory_position = usable_on_hand + scheduled_receipts - backorders - committed_demand`

Keep blocked, allocated, expired, and quality-hold stock separate.

### Reorder point

For stable independent demand:

`ROP = expected_demand_during_lead_time + safety_stock`

When daily demand variability dominates:

`safety_stock = z × demand_std_daily × sqrt(lead_time_days)`

When both demand and lead time vary independently:

`safety_stock = z × sqrt(lead_time_mean × demand_variance_daily + demand_mean_daily² × lead_time_variance)`

Validate distribution assumptions. Use simulation or empirical quantiles for intermittent, seasonal, censored, or promotion-driven demand.

### Order proposal

`order_qty_raw = target_inventory_position - current_inventory_position`

Then apply MOQ, order multiple, capacity, shelf life, budget, and container constraints. Show both raw and constrained quantities.

### Coverage and inventory days

`days_of_supply = usable_stock / average_daily_demand`

`inventory_turnover = annualized_cogs / average_inventory_value`

Do not use average demand alone when near-term demand is seasonal or lumpy.

### Excess and slow stock

Use explicit policy horizons:

`excess_qty = max(0, projected_available_at_horizon - target_stock_at_horizon)`

Separate excess, slow-moving, obsolete, blocked, and expiring stock; each has a different action.

## 5. Logistics and trade

### Container utilization

`weight_utilization = cargo_weight / allowable_payload`

`volume_utilization = cargo_volume / usable_container_volume`

The binding utilization is the larger ratio. Validate dimensions, stacking, dangerous-goods segregation, floor load, and packaging constraints.

### Freight allocation

Allocate by the economic driver agreed for the analysis:

- chargeable weight;
- volume;
- pallets;
- containers;
- units;
- value for insurance only.

Do not allocate all charges using one driver when charges have different bases.

### Duty

`customs_value = jurisdiction_specific_valuation_basis`

`duty = customs_value × applicable_duty_rate`

Never assume the valuation basis, HS classification, origin qualification, trade remedy, or tax treatment. Treat them as jurisdiction-specific gates.

### Cost-time comparison

Report at least:

- expected landed cost;
- expected door-to-door time;
- p90/p95 or adverse-case cost/time when evidence supports it;
- schedule frequency/capacity;
- compliance feasibility;
- cash and inventory implication.

## 6. Sensitivity and decision quality

Use break-even analysis for the variable most likely to reverse the recommendation:

`break_even_x = value of x where option A total outcome = option B total outcome`

For scenario tables, vary only decision-relevant uncertain drivers. Label:

- base;
- downside;
- upside;
- stress or gate-failure case.

Report the recommendation's **decision stability**: the range of assumptions under which it remains unchanged. Do not hide a fragile decision behind an average.
