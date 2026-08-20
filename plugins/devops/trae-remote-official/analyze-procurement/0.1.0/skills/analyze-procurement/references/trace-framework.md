# TRACE procurement framework

Use TRACE to turn heterogeneous procurement evidence into an auditable decision. Do not present TRACE as decoration; omit the acronym from the deliverable when it does not help the audience.

## Contents

1. Decision objects
2. TRACE stages
3. Gate logic
4. Cross-module decision patterns
5. Output tests

## 1. Decision objects

Every analysis must resolve at least one decision object:

- shortlist;
- RFx design;
- supplier award or allocation;
- negotiation posture;
- price/timing decision;
- supplier remediation or exit;
- replenishment or inventory disposition;
- route, container, broker, or Incoterm choice;
- approve, conditionally approve, pilot, defer, or reject.

Name the decision object in one sentence. If the work only describes performance without changing a decision, add the nearest decision implication or label it as monitoring.

## 2. TRACE stages

### T — Target the decision

Create the decision charter:

| Field | Required meaning |
|---|---|
| Decision | exact approval or action |
| Specification | product/service, grade, region, SLA, or technical envelope |
| Demand basis | quantity, usage, forecast, or scenario |
| Horizon | analysis period and decision life |
| Constraints | budget, quality, service, capacity, compliance, time |
| Baseline | current supplier, contract, index, policy, or do-nothing case |
| Approval rule | threshold, gate, decision owner, and deadline |

Reject a vague objective such as “find the best supplier.” Replace it with a bounded statement such as “select up to three suppliers for a 90-day pilot under a ¥2.0m budget, mandatory China data residency, and p95 latency below 800 ms.”

### R — Reconcile the evidence

Create a normalization ledger before comparing:

- supplier and entity identity;
- item/specification equivalence;
- unit and pack conversion;
- quantity tier and minimum order;
- currency and FX date/source;
- tax and recoverability;
- Incoterm and cost boundary;
- origin/destination and site;
- quote validity and period;
- quality, delivery, and service definitions;
- missing, disputed, provisional, and excluded values.

Calculate coverage:

`coverage = comparable populated required fields / all required comparison fields`

Do not convert coverage into a supplier score. Use it to describe confidence and diligence workload.

### A — Analyze economics

Build economics in layers:

1. quoted commercial price;
2. normalized unit price;
3. landed or usable unit cost;
4. lifecycle or total cost;
5. budget and cash timing;
6. uncertainty range and break-even points.

Explain the largest drivers, not every variance. Use a bridge or waterfall when differences arise from several additive components. Use a scenario matrix when outcomes depend on demand, FX, freight, tariff, yield, defect, or usage.

Identify negotiation levers by economic mechanism:

- specification or service-level trade;
- volume/tier and commitment;
- payment, prepayment, or credit;
- indexation and adjustment formula;
- logistics/Incoterm;
- rebate, credit, minimum spend, or take-or-pay;
- capacity reservation;
- allocation or dual-source design.

### C — Challenge resilience

Test five resilience lenses:

| Lens | Typical evidence |
|---|---|
| Conformance | quality, security, specification, audit, certification, defect escape |
| Delivery | OTD/OTIF, lead-time distribution, schedule reliability, backlog |
| Capacity | demonstrated output, utilization, bottleneck, surge and recovery |
| Continuity | site/geography, sub-tier, financial, cyber, concentration, disaster recovery |
| Compliance | legal, sanctions, export control, customs, product, data, ESG where mandatory |

Distinguish:

- **knockout** — failure blocks award/use;
- **condition precedent** — approval allowed only after evidence or remediation;
- **weighted preference** — trades off against other preferences;
- **monitor** — not decision-critical now, but requires a trigger.

Stress at least one adverse scenario for a material decision. Use the most plausible binding shock, not a generic risk list.

### E — Execute with gates

Express the recommendation as a controlled action:

| Field | Required meaning |
|---|---|
| Action | award, allocate, negotiate, order, transfer, expedite, pilot, defer, exit |
| Owner | accountable role |
| Timing | date or trigger window |
| Gate | evidence or threshold required before action |
| Fallback | alternative if the gate fails |
| Verification | metric and review date |
| Stop condition | event that pauses, reverses, or escalates |

Do not end at “Supplier A ranks first.” State what to do with Supplier A, under which conditions, at what share or spend, and what would change the decision.

## 3. Gate logic

Evaluate in this order:

1. **Feasibility** — specification, geography, capacity, lead time, legal/compliance.
2. **Evidence sufficiency** — comparable fields, source confidence, unresolved contradictions.
3. **Economics** — normalized and total cost under relevant scenarios.
4. **Resilience** — failure exposure and recovery options.
5. **Portfolio fit** — concentration, dual source, optionality, and switching cost.
6. **Execution readiness** — owner, contract, system, QA, logistics, and approval.

A later step cannot cure failure in an earlier knockout gate.

## 4. Cross-module decision patterns

### Supplier award

`mandatory gates → normalized TCO → capability/performance score → scenario stress → allocation → contract and pilot gates`

### Price reasonableness

`spec and basis match → internal PO trend → external driver/benchmark → supplier quote bridge → explainable range → negotiation or buy timing`

### Replenishment

`usable stock + open supply → demand distribution → lead-time distribution → policy constraints → shortage/excess scenarios → exception action`

### International fulfillment

`trade feasibility → quote normalization → container/routing design → landed cost → time/reliability stress → lane portfolio and document gates`

## 5. Output tests

Before finalizing, verify:

- The recommendation changes or controls a named decision.
- Every compared price has a declared commercial basis.
- Every supplier score exposes weights, direction, gates, and missingness.
- Every risk has an owner or decision consequence.
- Every important external fact has an as-of date and jurisdiction.
- The do-nothing/current-state baseline is visible.
- The top uncertainty has a test, sensitivity, or gate.
- Totals reconcile to the stated source scope.
