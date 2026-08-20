# Price and cost intelligence

Use this module for purchase-order trends, price reasonableness, benchmark analysis, should-cost, PPV, anomalies, buy timing, and negotiation.

## 1. Fix the price object

Define the comparable object:

- item/grade/specification;
- unit and pack;
- site/region and delivery basis;
- currency, FX, tax, and Incoterm;
- quantity tier;
- order/receipt/invoice date;
- quality/yield/moisture/purity adjustment where relevant;
- included freight, surcharge, rebate, and payment term.

Do not calculate a “monthly average” until the date field and weighting basis are selected.

## 2. Build the internal price spine

For each month and comparable item:

- quantity;
- quantity-weighted price;
- spend;
- supplier mix;
- price range and quote dispersion;
- order count and data coverage;
- specification/site mix;
- exceptional surcharges, credits, or amendments.

Use order date for purchasing commitment analysis, receipt date for realized supply timing, and invoice date for accounting analysis. Do not mix them.

## 3. Explain change

Decompose price movement into:

- market/input driver;
- supplier price change;
- specification or grade;
- supplier mix;
- location/freight;
- FX and tax;
- quantity/tier;
- timing/lag;
- residual.

Use a waterfall or bridge when several components are additive. Use a small multiple or indexed series when comparing items with different price levels.

## 4. Triangulate reasonableness

Use three evidence layers:

1. **internal execution** — comparable PO, receipt, invoice, and quote history;
2. **external market** — applicable spot/index/futures/input and freight evidence;
3. **supplier economics** — conversion, yield, energy, logistics, margin, and contract adjustment.

Create an explainable range, not a single “fair price,” when basis, lag, or specification is uncertain.

For raw materials such as soybean meal, bran, feed ingredients, or chemicals, align grade, protein/purity/moisture, region, delivery basis, benchmark contract/month, tax, and freight. Separate outright price from basis.

## 5. Detect anomalies

Flag, then investigate:

- duplicate or amended lines;
- price with zero/negative quantity;
- unit/pack conversion errors;
- stale contract price;
- price outside a robust historical band;
- supplier deviation after controlling for spec/site/timing;
- unexplained surcharge or rebate;
- split orders that change tier economics;
- price movement inconsistent with contract formula.

Do not label an outlier as overpayment until comparability is proven.

## 6. Convert analysis into action

Choose one:

- accept or release;
- request clarification/credit;
- renegotiate formula or basis;
- change quantity/timing;
- rebalance supplier share;
- switch specification/source/location;
- stagger purchases;
- investigate data/process control.

State target range, evidence, deadline, volume at stake, walk-away or escalation condition, and the next price review trigger.
