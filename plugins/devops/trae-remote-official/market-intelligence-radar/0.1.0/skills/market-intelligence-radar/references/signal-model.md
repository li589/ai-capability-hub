# Signal model

## Change taxonomy

Classify each candidate into one primary type:

| Code | Type | Examples |
|---|---|---|
| PROD | Product capability | model, feature, integration, availability, performance claim |
| COMM | Pricing and commercialization | price, packaging, limits, discount, enterprise terms |
| ORG | Organization and capital | financing, acquisition, leadership, hiring direction, restructuring |
| PART | Partnership and distribution | cloud, channel, OEM, marketplace, strategic alliance |
| MKT | Market behavior | demand, segment movement, adoption, procurement pattern |
| TECH | Technology | benchmark, architecture, standard, open-source dependency |
| POL | Policy and regulation | rule, consultation, enforcement, compliance deadline |
| ECO | Ecosystem | developer activity, complements, plugins, community workflow |

Use one primary type and up to two secondary tags. Classification is not importance.

## Signal identity and clustering

Normalize:

- canonical entity and product names;
- UTC or ISO-8601 dates while retaining the display timezone;
- currency and billing period;
- region and availability;
- URLs without tracking parameters;
- claims into a concise `what changed` sentence.

Cluster events when they share the same entity, change type, underlying event, and effective window.
Cross-posts, rewrites, translations, syndicated media, and commentary about the same release belong to
one cluster.

Keep evidence roles:

- `origin` — earliest credible announcement or record;
- `confirmation` — independent or official corroboration;
- `reaction` — customer, developer, analyst, or ecosystem response;
- `context` — background that explains significance.

## Newness states

Assign exactly one:

| State | Meaning | Reporting rule |
|---|---|---|
| NEW | First observed material event after baseline | Eligible for priority ranking |
| EVIDENCE | Stronger evidence for an existing event | Report only if confidence or implication changes |
| REVISION | A known fact, term, date, or scope changed | Show old → new explicitly |
| CONTINUATION | More activity without a decision-relevant delta | Keep in ledger; usually omit |
| RECIRCULATION | Old event resurfaced | Exclude from new-signal count |

## RISE priority

Score each dimension from 0 to 5:

- **Reach (R)**: 0 isolated; 3 meaningful segment; 5 market/value-chain wide.
- **Impact (I)**: 0 cosmetic; 3 roadmap or economics shift; 5 business-model, regulatory, or
  competitive discontinuity.
- **Speed (S)**: 0 no visible window; 3 action within a quarter; 5 action within days.
- **Evidence (E)**: 0 anonymous/contradicted; 3 one credible source; 5 primary plus independent
  confirmation.

Compute:

`RISE = 0.25R + 0.35I + 0.20S + 0.20E`

Map the weighted score:

- `P0`: 4.25–5.00 and Speed ≥4 and Evidence ≥3;
- `P1`: 3.25–4.24;
- `P2`: 2.00–3.24;
- `P3`: below 2.00.

Override only with a written reason. A negative business impact is not automatically higher priority
than a positive opportunity. Priority measures decision urgency, not sentiment.

## Impact lenses

Assess only lenses relevant to the user:

1. **Customer value** — new expectation, switching driver, trust, workflow, or willingness to pay.
2. **Product position** — parity gap, differentiation, dependency, integration, or roadmap timing.
3. **Commercial model** — price anchor, margin, packaging, sales motion, procurement, or channel.
4. **Execution exposure** — data, talent, infrastructure, partner, compliance, or operational burden.
5. **Strategic option** — build, buy, partner, wait, segment, localize, defend, or exit.

For each P0/P1, state:

- affected user, segment, product, or market;
- expected direction and time horizon;
- confidence and the evidence driving it;
- reversible response within the user's authority;
- metric or observable trigger that would confirm or invalidate the interpretation.

## Signal Stack

Write P0/P1 items in this order:

1. **Event** — one sentence describing the verified event.
2. **Evidence** — strongest source, date, and corroboration.
3. **Delta** — prior state → current state.
4. **Meaning** — why the change matters, not what the article says.
5. **Exposure** — the user's product, segment, economics, or decision affected.
6. **Move** — one bounded next action, owner type, and review window.
7. **Next trigger** — observable condition that changes the recommendation.

Separate fact from inference. Use `we infer` or equivalent when meaning is not directly stated by a
source.

## Opportunity and risk labels

Use one of:

- opportunity;
- risk;
- mixed;
- watch.

Do not force a binary label. Many signals create a competitor advantage and a partnership or market
opportunity simultaneously.

