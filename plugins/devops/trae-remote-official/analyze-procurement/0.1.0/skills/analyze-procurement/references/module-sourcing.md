# Supplier discovery, RFx, and award

Use this module for market mapping, longlists, shortlists, RFI/RFP/RFQ design, quote normalization, pilots, negotiation, awards, and procurement approval papers.

## 1. Frame the sourcing decision

Define:

- required outcome and workload;
- specification and mandatory gates;
- volume/usage scenarios;
- geography and delivery/service model;
- commercial term and decision horizon;
- current baseline and switching constraints;
- approval owner and deadline.

Choose the instrument:

- **RFI** for market discovery, capability, evidence, and feasibility;
- **RFP** for solution, implementation, service, and commercial design;
- **RFQ** for comparable specifications and pricing;
- **pilot/evaluation** when workload performance or integration uncertainty dominates.

Do not issue an RFQ for an under-specified problem.

## 2. Build a coverage-driven longlist

Create market segments first, then candidates. Typical segments include:

- global/full-suite providers;
- regional or jurisdiction-specific providers;
- specialists;
- open/self-hosted or private-deployment options;
- aggregators/resellers where commercially relevant;
- incumbent/adjacent suppliers.

For each candidate, record segment fit, evidence, product availability, geography, legal entity, and unresolved gate. Avoid scoring a longlist with sparse public data; use screen/pass/unknown.

Stop adding suppliers when required segments are represented and new candidates no longer change the RFx or shortlist.

## 3. Design the evaluation architecture

Separate:

1. mandatory gates;
2. workload or capability tests;
3. service/implementation requirements;
4. normalized commercial model;
5. operational and supplier risk;
6. evidence confidence;
7. negotiation variables.

Use decision-anchored dimensions, not generic labels. “Capability” must resolve into measurable requirements such as acceptance rate, latency distribution, context handling, security control, delivery window, yield, or integration effort.

## 4. AI-token and model-provider procurement

For a 15-supplier screen, use a funnel:

`market segments → 15-candidate evidence register → knockout screen → 6–8 RFI/RFP participants → 3–5 workload evaluations → 1–3 award/pilot options`

Adapt counts to market evidence; do not keep fifteen suppliers in full diligence without reason.

### Mandatory fields

- exact model/version and region;
- input, output, cached-input, batch, fine-tuning, storage/hosting, and support rates;
- context, rate limits, concurrency, availability, and latency commitment;
- data retention, training use, residency, encryption, access, audit, and incident controls;
- deployment model and integration path;
- workload evaluation result and test date;
- deprecation/version-change policy;
- minimum spend, commitment, tier, credits, rebates, and overage;
- legal entity, invoice/tax, and contract jurisdiction.

### Budget scenarios

Model at least:

- base usage;
- adoption upside;
- output-token or context expansion;
- cache/batch optimization;
- retry/fallback and multi-model routing;
- minimum-spend underuse;
- FX and regional price change where relevant.

Show cost per accepted workload unit when the test supports it. A cheaper token rate can be more expensive after output length, retries, rejection, latency, or fallback.

### Pilot gates

Require a frozen test set, acceptance rubric, version/date, region, rate-limit setup, latency metric, evaluator ownership, security/legal conditions, and a rule for workload leakage or manual overrides.

Do not use a generic public benchmark as the sole award criterion.

## 5. Normalize and compare

Create three views:

- **gate view** — pass, fail, condition precedent, unknown;
- **economic view** — normalized scenario cost and budget exposure;
- **decision view** — anchored preferences, risk, evidence confidence, and allocation.

Do not bury unknown mandatory evidence inside the score. Keep commercial and technical evaluation independent until normalization is complete.

## 6. Recommend and negotiate

State:

- shortlist or award;
- allocation and term;
- conditions precedent;
- negotiation target, walk-away, and give/get variables;
- pilot or implementation gates;
- fallback supplier or architecture;
- review trigger and exit condition.

For an approval paper, include the current baseline, market coverage, evaluation logic, normalized budget, risks, alternatives considered, and explicit approval requested.
