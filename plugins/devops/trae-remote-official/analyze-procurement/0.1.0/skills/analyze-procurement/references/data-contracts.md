# Procurement data contracts

Use these contracts to reconcile heterogeneous files. Keep the user's original columns; add normalized fields rather than overwriting source values.

## Contents

1. Provenance fields
2. Shared normalization fields
3. Minimal schemas
4. Missingness and identity
5. Reconciliation checks

## 1. Provenance fields

Attach these fields to each decision-critical table or source group:

- `source_name`
- `source_type` — quote, PO, receipt, invoice, contract, forecast, inventory, scorecard, public source
- `source_owner`
- `source_period`
- `retrieved_at`
- `effective_at`
- `jurisdiction_or_market`
- `evidence_status` — observed, sourced, derived, assumed, unknown
- `transformation_note`

Retain source row identifiers so a normalized row can be traced back.

## 2. Shared normalization fields

Create only the fields relevant to the route:

- canonical supplier/entity ID;
- canonical item/service/specification ID;
- source unit and normalized unit;
- source quantity and normalized quantity;
- source currency, FX rate, FX date, and normalized currency;
- tax included/excluded and recoverability;
- Incoterm and named place;
- origin, destination, site, and lane;
- order, ship, receipt, invoice, or consumption date;
- validity start/end;
- inclusion boundary for freight, duties, insurance, fees, implementation, support, and rebates.

Use a conversion table with source, factor, effective date, and owner for each nontrivial unit or pack conversion.

## 3. Minimal schemas

### Supplier offer

`supplier_id, offer_id, item_id, specification, quantity_tier, source_unit, normalized_unit, currency, fx_rate, fx_date, unit_price, tax_basis, incoterm, named_place, freight, duty, insurance, fees, rebate, minimum_commitment, payment_terms, lead_time, validity_end, inclusions, exclusions, evidence_status`

For services or AI usage, add:

`billing_meter, input_rate, output_rate, cached_input_rate, batch_rate, fine_tuning_rate, storage_or_hosting, minimum_spend, committed_use_discount, region, rate_limit, context_limit, SLA, support_tier`

### Purchase order line

`po_id, line_id, supplier_id, item_id, specification, order_date, promised_date, receipt_date, ordered_qty, received_qty, unit, currency, unit_price, tax_basis, site, freight_or_surcharge, status`

Do not analyze cancelled lines as purchases. Define treatment for returns, credits, partial receipts, and price amendments.

### Supplier performance

`supplier_id, period, site, item_family, ordered_lines, on_time_lines, in_full_lines, received_units, rejected_units, defects_or_ppm, complaints, escapes, capa_open, capa_overdue, capacity_committed, capacity_demonstrated, lead_time_mean, lead_time_std, audit_status, mandatory_gate_status`

Record metric definitions. “On time” may mean ship date, requested receipt date, or promised receipt date.

### Inventory and demand

`snapshot_date, site, item_id, specification, on_hand, blocked, allocated, in_transit, open_po, backorder, demand_history, forecast, unit, lead_time_mean, lead_time_std, review_period, service_target, moq, order_multiple, shelf_life, expiry_date, substitute_group`

Keep usable stock separate from physical stock:

`usable_stock = on_hand - blocked - allocated`

### Logistics quote

`quote_id, provider, mode, origin, destination, port_pair, equipment, container_or_weight_basis, currency, base_freight, origin_charges, destination_charges, fuel_or_peak_surcharge, insurance, brokerage, duty, tax, free_time, demurrage_basis, transit_time, schedule_frequency, validity_end, incoterm, exclusions, hs_code_status, origin_status, compliance_status`

## 4. Missingness and identity

Use explicit states:

- missing — no value supplied;
- not applicable — field does not apply;
- not disclosed — supplier refused or has not disclosed;
- disputed — sources conflict;
- provisional — unverified or temporary;
- zero — measured numeric zero.

Do not impute decision-critical commercial or gate values unless the analysis is explicitly a scenario. Label imputed values and show the scenario separately.

Resolve supplier identity across legal entity, trading name, site, parent, and manufacturer. Preserve all source names and state which level is being scored or awarded.

## 5. Reconciliation checks

Run before calculation:

1. count source rows, included rows, excluded rows, and unmatched rows;
2. reconcile quantity and spend totals to the declared source scope;
3. test duplicate PO/quote/invoice identifiers;
4. test unit and currency consistency after normalization;
5. test validity periods and stale quotes;
6. test negative quantity/price and unexpected zero values;
7. test cancelled, returned, credited, and amended lines;
8. test supplier/item/site mapping coverage;
9. test weights sum to one and score directions are correct;
10. preserve an exception table rather than silently dropping failures.

State the analysis denominator after all exclusions.
