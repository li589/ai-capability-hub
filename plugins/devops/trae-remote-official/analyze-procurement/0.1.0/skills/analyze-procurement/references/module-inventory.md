# Inventory and replenishment

Use this module for reorder decisions, stockout risk, excess and slow stock, open-PO control, service levels, and replenishment policy.

## 1. Select the operational grain

Analyze at:

`item × site × date × usable status`

Add supplier, substitute group, customer/channel, lot/expiry, and order constraints only when they affect the decision.

Define the demand signal: consumption, shipment, sales order, forecast, or a blend. Do not mix signals without a hierarchy.

## 2. Reconcile supply and demand

Separate:

- usable, blocked, quality-hold, allocated, expired, and in-transit stock;
- firm, planned, late, and uncertain open POs;
- backorders and committed demand;
- baseline, promotion/project, and exceptional demand;
- mean and variability of actual lead time;
- MOQ, order multiple, shelf life, capacity, and budget.

Build a time-phased inventory projection. Static days-of-supply is a screening signal, not a complete replenishment decision.

## 3. Segment policy

Segment by the dimensions that change policy:

- value/working capital;
- demand variability/intermittency;
- criticality and substitution;
- lead time and supply risk;
- shelf life/obsolescence;
- service target.

Do not apply one service level or safety-stock formula to every item.

## 4. Detect the exception queue

Prioritize exceptions by decision impact:

- projected stockout before the next feasible receipt;
- late PO on the critical path;
- demand spike or forecast error;
- excess after open supply;
- slow, obsolete, blocked, or expiring stock;
- MOQ/order-multiple distortion;
- supplier capacity or lead-time shift;
- conflicting item/site master data.

For each exception, show date of exposure, quantity, value, affected demand, root-cause hypothesis, and available actions.

## 5. Simulate actions

Compare:

- place or increase order;
- expedite;
- defer or cancel;
- transfer between sites;
- substitute;
- split allocation;
- change mode or supplier;
- consume/return/rework/liquidate excess;
- hold and monitor.

Apply MOQ, pack, container, shelf-life, budget, and capacity constraints after calculating the raw need.

## 6. Recommend with service and cash

Report:

- recommended action and quantity;
- order/ship/receipt timing;
- service or stockout effect;
- working-capital and excess effect;
- supplier/logistics feasibility;
- trigger, fallback, and review date.

Do not optimize average inventory while hiding tail stockout risk.
