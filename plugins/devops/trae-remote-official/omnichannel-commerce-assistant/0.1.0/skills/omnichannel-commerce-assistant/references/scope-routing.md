# Scope and routing

## Market family

Classify by operating market, not seller nationality or platform name alone.

| Family | Include | Typical channels |
|---|---|---|
| China domestic | Commerce primarily serving mainland-China consumers | Taobao/Tmall, JD, Pinduoduo, Douyin, Kuaishou, Xiaohongshu, WeChat/private domain |
| Cross-border | A China-based or China-serving seller selling into overseas markets | Amazon, TikTok Shop, Shopee, Lazada, AliExpress, Temu, eBay, Walmart Marketplace, DTC |

If both apply, diagnose each market separately before reconciling shared supply, cash, and portfolio decisions.

## Capability routing

| Decision | Primary capability | Useful support |
|---|---|---|
| Why did sales or profit change? | Store diagnosis | Traffic/conversion, pricing, inventory |
| What should we sell, add, or discontinue? | Product/category | Inventory, pricing, research |
| Which product can become a bestseller, and how should it be built or scaled? | Bestseller analysis | Product/category, traffic/conversion, inventory/supply |
| How should traffic or conversion improve? | Traffic/conversion | Product, pricing, retention |
| How should price or promotion change? | Pricing/promotion | Margin, inventory, traffic |
| How much should we buy, make, or send? | Inventory/supply | Forecast, promotion, cash |
| How should repeat purchase improve? | Retention/membership | Cohorts, product cadence, economics |

Use one primary capability and no more than two supporting capabilities by default.

## Working focus

Use category + primary platform/site + period as the focus frame. These are not mandatory questions.

- Use explicit values when provided.
- Infer a category from the product, customer need, price, or examples when the fit is clear.
- Recommend one primary platform/site when absent; explain the fit and keep the first pass on that platform rather than producing a broad platform survey.
- Select a decision-appropriate period when absent and state it.
- Treat business stage, objective, and a binding constraint as helpful context, not prerequisites.

Use `AskUserQuestion` only when the request remains too ambiguous to narrow responsibly, an essential referenced artifact is missing, or a hard-to-reverse market/compliance/budget decision cannot be represented as a scenario. Prefer one short question and never ask users to choose an internal module or professional role.

Do not treat absent attachments as a normal intake gap. Request a re-upload only when the prompt explicitly refers to a missing artifact required for the requested operation. Otherwise continue with public evidence, a focused recommendation, or labeled assumptions.

Use examples as signals, not as audited facts. State any inferred platform, category, budget, or economics that materially affects the recommendation.

## Boundaries

| Requested execution | Useful in-scope handoff |
|---|---|
| Product images, copy, or video | Conversion diagnosis, creative brief, test matrix, acceptance criteria |
| Operate an ad account | Campaign structure, budget guardrails, experiment and monitoring plan |
| Reply to customers or sell | VOC themes, policy recommendation, escalation taxonomy |
| Build WMS/logistics software | Inventory requirements, data fields, exception rules, vendor criteria |
| Build a general data platform | Metric dictionary, reporting requirements, minimum data-mart scope |
| Define brand identity | Channel/category implications and e-commerce positioning inputs |

Complete the analytical portion and hand off the execution brief without adding a formal boundary section to the user-facing result.
