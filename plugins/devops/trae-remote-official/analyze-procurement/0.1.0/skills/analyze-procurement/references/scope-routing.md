# Scope routing

Use this reference only when the stakeholder, decision, or primary route is unclear.

## 1. Stakeholder and route map

| Stakeholder | Common setting | Typical query | Primary route | Decision output |
|---|---|---|---|---|
| Procurement manager / strategic sourcing | Finance, enterprise IT | Screen 15 model vendors and compare price, capability, security, and budget for AI-token procurement | Supplier discovery and RFx | shortlist, evaluation matrix, budget scenarios, approval gates |
| Raw-material buyer | Food, feed, chemical | Analyze monthly weighted purchase price and trend for soybean meal, bran, or chemicals | Price and cost intelligence | price baseline, driver bridge, reasonableness range, buying/negotiation action |
| Supplier management / SQE | Manufacturing, automotive, electronics | Compare supplier price, delivery, quality, capacity, and risk | Supplier performance and risk | gated scorecard, failure-mode view, allocation/CAPA recommendation |
| PMC / inventory manager | Manufacturing, retail, distribution | Combine inventory, sales, and purchase plans to identify reorder, stockout, and slow stock | Inventory and replenishment | exception queue, order proposal, service and cash scenarios |
| International logistics / trade operations | Export manufacturing, cross-border commerce | Compare freight quotes, container plans, duties, time, and compliance | International logistics and landed cost | feasible lane set, landed-cost comparison, document/compliance gates |

Route by the decision, not job title. A sourcing manager comparing ocean-freight quotations belongs in the logistics route; an inventory planner examining supplier lead-time reliability may need the supplier module as support.

## 2. Decision-object routing

| Decision object | Use as primary when the user must decide… | Common supporting route |
|---|---|---|
| Supplier shortlist | who deserves diligence or an RFx | supplier risk |
| RFx design | what to ask, how to normalize, and how to evaluate | price or logistics |
| Award / allocation | who gets what share under which gates | supplier risk + TCO |
| Price reasonableness | whether a paid or quoted price is defensible | sourcing |
| Negotiation | what target, walk-away, and evidence to use | price + supplier |
| Supplier remediation | whether to develop, cap, pause, or exit | price |
| Replenishment | what, when, and how much to order | supplier lead time |
| Stock disposition | expedite, transfer, reduce, return, or liquidate | price |
| Lane / Incoterm | which fulfillment design is feasible and economical | supplier |
| Procurement approval | whether to approve, conditionally approve, pilot, or reject | any relevant route |

## 3. Discovery prompts

Use these as internal prompts for evidence inspection and analysis planning. Do not turn them into an intake questionnaire. Follow the low-interruption protocol in `SKILL.md`: infer, assume, scenario, or mark unknown first; ask only the single currently blocking question.

### Procurement manager / sourcing

- How are potential suppliers found today, and which sources are trusted?
- Which requirements are knockout gates versus scored preferences?
- Which price components, usage assumptions, and contract terms drive the budget?
- What part of the approval paper consumes the most manual time: market map, quote normalization, security/legal review, evaluation, or budget scenarios?
- What evidence would make the decision auditable six months later?

### Raw-material buyer

- Is “average price” quantity-weighted, receipt-weighted, invoice-weighted, or order-weighted?
- Which benchmark, basis, freight, grade, moisture/purity, region, and timing are comparable?
- How are market prices, purchase orders, inventory, and supplier quotations combined today?
- Which deviations represent timing or specification differences rather than overpayment?
- What is the target action: buy now, stagger, renegotiate, switch source, hedge, or monitor?

### Supplier management / SQE

- Which defects, delivery failures, capacity claims, or risk fields are hardest to obtain or easiest to game?
- Are quality and delivery definitions identical across sites and suppliers?
- Which events are mandatory gates regardless of weighted score?
- How are missing data, disputes, CAPA aging, and provisional suppliers handled?
- What allocation, development, audit, or exit action should the scorecard drive?

### PMC / inventory

- Which demand signal controls replenishment: orders, shipment, consumption, forecast, or min/max?
- How are lead-time variability, MOQ, pack size, shelf life, and open POs handled?
- Which stockout, excess, and slow-moving exceptions still rely on manual discovery?
- What service-level or working-capital constraint dominates?
- Which orders can be expedited, postponed, cancelled, transferred, or substituted?

### International logistics / trade

- Are quotes comparable by origin/destination, container, charge scope, Incoterm, validity, and free time?
- Which duties, taxes, brokerage, insurance, demurrage, and destination charges are included?
- Which HS classification, origin, licensing, product, sanctions, or documentation questions remain gates?
- Where do quote, schedule, capacity, time, and compliance information most often stall?
- Which decision matters: lowest expected cost, fastest feasible time, lowest tail risk, or a portfolio?

## 4. Boundary rules

- Treat supplier selection as a commercial recommendation, not certification.
- Treat public benchmarks as context, not proof of a supplier's executable price.
- Treat quality, security, sanctions, customs, and legal requirements as owned gates.
- Do not mix an operational purchase recommendation with a financial hedge recommendation unless the user explicitly requests both and qualified evidence is available.
- Do not infer demand approval, budget authority, or purchase authorization from an analysis request.
