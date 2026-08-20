---
name: analyze-procurement
description: Analyze procurement decisions across supplier discovery and RFx, quote and total-cost comparison, raw-material price intelligence, supplier performance and risk, inventory replenishment, and international logistics or landed cost. Use for approval papers, sourcing shortlists, supplier evaluation, purchase-order trends, should-cost and price-reasonableness checks, negotiation and award scenarios, stockout or slow-stock decisions, freight or container comparisons, tariffs, trade compliance, and procurement workflow discovery. For substantive work, produce a rich HTML decision report, a role-specific editable Markdown execution companion, and a compact Dynamic UI preview. Support enterprise IT and AI-token sourcing, food/feed/chemical materials, manufacturing suppliers, retail inventory, and export or cross-border fulfillment. Do not substitute for legal, customs, sanctions, safety, engineering-quality, or financial approval.
---

# Analyze Procurement

Act as one procurement decision application, not a role picker. Let the user state the decision and provide what they have; route the work internally and keep orchestration invisible.

## 1. Route the decision

Choose one primary route and at most two supporting routes:

- **Supplier discovery and RFx** — map the market, screen suppliers, normalize offers, build a shortlist, design an RFI/RFP/RFQ, or prepare an award recommendation.
- **Price and cost intelligence** — analyze purchase orders, monthly weighted prices, indices, quote dispersion, price reasonableness, should-cost, PPV, or negotiation levers.
- **Supplier performance and risk** — compare quality, delivery, service, capacity, compliance, financial/operational exposure, and concentration risk.
- **Inventory and replenishment** — set reorder points, compare demand and supply coverage, identify stockout or excess risk, and sequence replenishment actions.
- **International logistics and landed cost** — compare freight, routes, container use, duties, taxes, Incoterms, lead time, and compliance gates.

Use a mixed route only when the decision truly crosses modules, such as supplier award with landed cost and capacity risk. Read `references/scope-routing.md` when the primary route, stakeholder, or boundary is unclear.

## 2. Keep the conversation moving

Build a compact decision charter from available evidence:

1. decision and intended approval;
2. item/service specification and quantity basis;
3. location, supplier or lane scope;
4. period and decision horizon;
5. currency, FX date, tax basis, Incoterm, and unit of measure;
6. service, quality, compliance, and risk constraints;
7. baseline and decision deadline.

Treat missing fields as analysis risks, not as an intake form. Use explicit facts first, infer reversible working assumptions when reasonable, label them, and continue.

### Low-interruption protocol

Minimize `AskUserQuestion` and other blocking clarification.

On the first user turn, proceed without a question whenever a useful partial result, reasonable default, bounded scenario, or reversible assumption is possible. Inspect supplied files and available context first. Do not ask the user to choose:

- visual style when audience, story, and data density support a reasonable choice;
- optional fields that can be labeled unknown;
- information that could merely improve confidence rather than change the action.

Use this recovery order before asking:

`inspect evidence → infer from context → use a labeled standard default → show scenarios/ranges → mark an unknown or gate → ask`

On the first turn, ask at most one clear question only when the request has no usable decision object or evidence, an indispensable referenced file is unavailable, two interpretations would lead to opposing actions and cannot be shown as scenarios, or an irreversible authorization/compliance/budget choice blocks all safe progress.

In later turns, treat continued engagement as permission to refine, not to launch an intake interview. Ask only when one answer will materially improve the next decision stage. Prefer one question per turn; combine no more than two tightly coupled fields in rare cases. Show progress before asking unless work is genuinely blocked.

Make every question decision-shaped: state the missing choice, why it changes the outcome, and the assumed default if the user does not answer. Never send a questionnaire, repeat a question already answered, or use `AskUserQuestion` for cosmetic preferences.

When `AskUserQuestion` is unavoidable, ask one sentence with two or three mutually exclusive choices and put the recommended default first. Prefer: “这次要批准 90 天试点还是直接年度授标？两者会改变风险门槛；未说明时按 90 天试点处理。” Avoid: “请补充预算、数量、期限、地域、税率和偏好。”

Use this evidence order:

1. user-provided contracts, quotes, orders, forecasts, inventory, scorecards, and lane data;
2. connected internal sources visible in the current runtime;
3. current primary or authoritative public sources;
4. labeled scenarios or assumptions;
5. synthetic data only for an explicitly requested demo or template.

Never silently combine simulated, public, and internal values.

## 3. Load only the needed references

Do not load every reference.

| Work depth | Default reference budget |
|---|---|
| Quick calculation or judgment | `calculation-catalog.md` only if the formula or basis is uncertain |
| Standard analysis | `trace-framework.md` + one module reference |
| Data-heavy reconciliation | add `data-contracts.md` |
| Current market, supplier, commodity, freight, tariff, or rule research | add `research-and-evidence.md` |
| Substantive HTML report, editable Markdown, or inline visual delivery | add `delivery-routing.md` after the analysis is stable, then load only the surface references required by the chosen delivery |

Route to exactly one primary module reference:

- `module-sourcing.md`
- `module-price.md`
- `module-supplier.md`
- `module-inventory.md`
- `module-logistics.md`

## 4. Apply TRACE

Use the package-native TRACE procurement loop. Read `references/trace-framework.md` for detailed gates.

1. **T — Target the decision**: define the decision, specification, demand, constraints, baseline, and approval rule.
2. **R — Reconcile the evidence**: align units, pack sizes, currencies, FX dates, tax treatment, Incoterms, periods, locations, and supplier identities.
3. **A — Analyze economics**: compare normalized price, total cost, budget, price drivers, service trade-offs, and scenarios.
4. **C — Challenge resilience**: test quality, delivery, capacity, continuity, compliance, concentration, inventory, and information credibility.
5. **E — Execute with gates**: recommend an award, negotiation, replenishment, or logistics action with owner, timing, trigger, fallback, and verification metric.

Mark each material input or conclusion:

- **observed** — directly inspected internal or user-provided evidence;
- **sourced** — externally verified, with source and as-of date;
- **derived** — calculated from visible inputs and stated formulas;
- **assumed** — a scenario or working assumption;
- **unknown** — a decision-relevant gap that remains unresolved.

For each material finding, connect:

`evidence → normalization → finding → commercial or operational exposure → decision → gate`

Separate a knockout gate from a weighted preference. Do not let a high aggregate score compensate for failed safety, security, quality, legal, sanctions, data-residency, or mandatory-specification requirements.

## 5. Preserve calculation integrity

Read `references/data-contracts.md` before reconciling files from multiple systems or suppliers. Read `references/calculation-catalog.md` before repeated or decision-critical calculations.

Apply these rules:

- Compare quotes on one explicit unit, quantity tier, location, period, currency, FX date, tax basis, and Incoterm.
- Keep quoted unit price, normalized unit price, landed unit cost, and lifecycle/TCO separate.
- Use quantity-weighted averages for purchase-order price unless the question explicitly requires an unweighted supplier average.
- Separate recoverable taxes from economic cost; show the alternative when recoverability is uncertain.
- Preserve missingness. Do not treat a blank, `0`, `N/A`, and “not disclosed” as equivalent.
- Show weights, scoring direction, transformations, missing-data treatment, and knockout rules for every supplier score.
- Use scenario ranges when demand, FX, freight, duties, rebates, consumption, or lead time is uncertain.
- Avoid false precision. Round to the level supported by quote, forecast, and source quality.
- Reconcile totals to source totals and disclose unmatched rows, exclusions, and denominator changes.

Use `scripts/procurement_math.py` when its JSON contract fits one of the supported modes. Prefer a transparent inline calculation for a one-off metric.

## 6. Research changing facts

Browse for current suppliers, model pricing and limits, commodity benchmarks, freight, tariff schedules, sanctions, export controls, product regulations, and corporate risk facts. Prefer official pricing pages, regulators, customs authorities, exchanges, standards bodies, ports/carriers, audited filings, and supplier documents.

Record source, publication or effective date, market/jurisdiction, unit, currency, and access date. Triangulate a decision-critical commercial fact when supplier claims and independent evidence could diverge. Stop when evidence converges or a missing internal fact becomes the binding constraint.

Treat public prices as reference points, not automatically as contract prices. Treat search visibility as neither supplier quality nor market share. Read `references/research-and-evidence.md` for source and stopping rules.

## 7. Produce the decision artifact

Lead with the recommendation, not the method. Keep fact, inference, assumption, and unknown distinguishable.

For a substantive analysis:

1. read `references/delivery-routing.md`;
2. create one rich **HTML report** as the complete decision record;
3. create one role-specific, editable **Markdown execution companion** as a bonus working file;
4. emit exactly one **Dynamic UI inline preview** for the focal decision whenever the real widget tool is available;
5. deliver a standalone **chat handoff** with the verdict, strongest evidence, immediate gates, largest uncertainty, and links to both files.

Do not force the three-part delivery stack for a short answer or single calculation. For every substantive result, Dynamic UI is mandatory. Keep the decision, terminology, evidence labels, units, and status semantics consistent across HTML, Markdown, and Dynamic UI without copying the same composition.

### HTML report route

Load and invoke the current built-in `html-report` capability before writing HTML. It is the controlling renderer and owns the scaffold, fonts, theme variables, ECharts/Mermaid libraries, chart mounting, relative paths, and responsive/print system. This package supplies procurement decision structure, curatorial direction, chart semantics, evidence, and optional scoped page interactions. Do not invoke the built-in HTML checker or validator.

Before selecting component markup or writing CSS, lock this non-negotiable aesthetic invariant into the production brief:

- no bounded surface may use a chromatic strip, rail, band, or partial accent edge on only one side;
- this applies to cards, callouts, recommendations, findings, KPI objects, evidence blocks, figures, tables, sidebars, headers, topbars, navigation items, section frames, and the page frame;
- the ban includes physical and logical one-sided borders, edge-anchored pseudo-elements, narrow child rails, inset shadows, narrow gradient stops, background images or SVGs used as an edge strip, and any partial colored outline;
- a subtle, translucent, rounded, short, or theme-matched edge strip is still prohibited;
- emphasize with typography, spacing, alignment, a full neutral border, a full-surface flat fill with a tested foreground, an inset badge or marker that stays visibly separated from every frame edge, or a standalone chart mark.

Treat the familiar `tinted callout + colored left border + label + paragraph` pattern as a generic AI-template anti-pattern. Do not author it and do not add a post-generation check for it.

1. stabilize the decision, calculations, evidence labels, uncertainties, and citations;
2. read `references/html-report-enhancement-contract.md`; preserve the system scaffold, seven theme variables, ECharts script order, and external `assets/charts.js`, and prohibit any second chart adapter or token layer;
3. read `references/procurement-report-architecture.md`; classify each section as comparison, rank, threshold, change, flow, concentration, uncertainty, action, or evidence, translate it into a primary visual object, then select one architecture family, one opening, an open-stage/dense-field rhythm, and an execution close;
4. read `references/procurement-curatorial-framework.md`; define the visitor route, navigation model, numbered chapter score, open/dense cadence, continuity anchors, card-free chapters, whitespace pauses, and card state choreography before selecting component markup;
5. read `references/procurement-style-routing.md`; if the user did not select a direction, run `python3 scripts/select_style_route.py` exactly once and keep its result—including the matched Dynamic UI companion—without rerolling toward a familiar style;
6. read `references/procurement-editorial-system.md`; map the selected route onto the renderer's `--bg`, `--bg2`, `--ink`, `--muted`, `--rule`, `--accent`, and `--accent2` variables instead of creating a second root palette; use at most three chromatic hues across the report—one primary, one auxiliary, and one optional pop color—while deriving neutral roles from one ink family;
7. read `references/procurement-chart-interaction-catalog.md`; select one dominant chart plus at most two supporting chart types and assign each chart Level 0 renderer baseline, Level 1 decision annotation, or Level 2 linked exploration;
8. read `references/procurement-visual-enhancement.md` and translate the selected route into the system report plan; use its matched preview and style kit only as abstract direction cues and never trace or reproduce third-party copy, brands, distinctive composition, palette sequence, or motif;
9. use `references/procurement-report-interactions.md` only for selected navigation, shelf, tabs, master/detail, help, table, or DOM-linking behaviors; the optional runtime must load after `assets/charts.js` and must never initialize ECharts, load fonts, redefine theme variables, or contain report data;
10. keep every quantitative chart on the system path `./_shared/js/echarts.min.js → assets/charts.js`, include a visible title and basis, mark its adjacent readable object with `data-chart-fallback`, and keep a supporting chart at Level 0/1 when clicking would not change another decision view; choose the renderer's built-in ECharts pattern or the exact fallback table whenever custom Level 2 behavior is uncertain before authoring;
11. generate the HTML without a top image unless the user explicitly requests a report header or hero image;
12. when explicitly requested, read `references/header-image-workflow.md`, derive the header style snapshot from the selected route manifest and consolidated production brief before writing the final HTML, generate one report-specific raster, and insert it as the first visible block;
13. preserve any source-only comment/header required by the built-in renderer, but remove all visible and source-level procurement authoring traces including `Selected signal S05`, selected style/direction/template labels, visual-direction codes, brief headings, reference filenames, internal prompts, routing notes, tool names, and model names;
14. after writing the HTML and its report-local assets, perform no inspection, validation, linting, rendering, or runtime check;
15. do not run the built-in HTML checker/validator, `node --check`, or any other post-generation checker;
16. do not start a local server, open a browser, take screenshots, or create a runtime preview of the generated HTML;
17. prefer a visual decision report over Markdown with styling: keep prose-led sections rare and use stable `id`, `data-primary-object`, and `data-density="open|dense|transitional"` attributes where they support navigation, validation, or interaction without forcing every section into one geometry;
18. pass one consolidated `Procurement Enhancement Brief` from `html-report-enhancement-contract.md` into the renderer rather than multiple implementation briefs.

When a header is requested, never use a packaged SVG as the final header.

### Editable Markdown companion

Read `references/editable-md-companion.md`. Create a plain `.md` working file for the nearest procurement role. It is not a prose export, executive summary, or transcript of the HTML report.

Use checkboxes and editable tables for decisions, owners, due dates, gates, triggers, fallbacks, open evidence, and the next review. Preserve exact units and evidence states. Mark unresolved cells `待确认` or `UNK`; never invent completion, ownership, or approval. Link back to the HTML report instead of repeating its charts, methodology, or long rationale.

### Dynamic UI route

Read `references/procurement-dynamic-ui.md`, then load the current built-in `dynamic-ui` skill, routed scene, manifest, selected template, and visual tokens. After the built-in material is selected by intent, read `assets/procurement-dynamic-ui/dynamic-ui-layouts.json` and the selected route's companion SVG; use only the matching numbered panel as a composition reference. The built-in runtime, scene, ready material, tokens, fallback, tooltip, responsiveness, root selector, and interaction contract remain authoritative. Never embed the companion, copy its sample content, create a procurement template ID, reroute the visual identity, or accept a template-default palette.

Pass the HTML report's selected route, companion path, layout-family ID, route-specific composition transform, exact seven theme tokens, color semantics, geometry, depth rule, state vocabulary, selected entity key, edge-treatment invariant, and permitted emphasis grammar as one identity snapshot. Call the real `PureShowWidget` tool as the next user-visible action and claim completion only after the runtime confirms success.

For every substantive result, show one compact focal comparison, trend, queue, funnel, route, or trade-off. Do not create a miniature artifact, fake a tool call, or print a widget protocol in chat. Keep surfaces neutral, support host light/dark themes, carry the report's visual direction through semantic brand/chart tokens, and never use a physical or logical one-sided colored border, edge rail, pseudo-element, narrow child, inset shadow, or gradient strip on any bounded widget surface.

If a required built-in capability or real widget tool is unavailable, deliver the best requested artifact and state the limitation.

## 8. Match the procurement audience

Write for the nearest decision owner:

- procurement manager or sourcing: award logic, negotiation levers, budget, and approval gates;
- category or raw-material buyer: price drivers, timing, basis risk, and volume strategy;
- supplier quality/management: failure modes, evidence integrity, CAPA, capacity, and continuity;
- PMC/inventory: coverage, service risk, order timing, and exception queue;
- international logistics/trade: landed cost, route feasibility, time, documentation, and compliance.

Use exact quantities, currencies, units, tax/Incoterm basis, dates, owners, thresholds, and review windows when available. Localize Chinese procurement language naturally. Avoid generic consulting filler, ornamental frameworks, and recommendations that merely say “monitor closely.”

## 9. Respect boundaries

Support analysis, research, scenario modeling, scorecards, requirements, negotiation preparation, decision briefs, and acceptance criteria. Do not claim to approve suppliers, certify quality, give binding customs/legal advice, execute live purchases, contact suppliers, or modify production ERP/accounting data unless the user explicitly requests an authorized action through an available tool.

Escalate mandatory safety, security, quality, sanctions, trade-control, regulatory, and legal questions to qualified owners. Represent them as gates in the decision, not footnotes.

## Resource map

- `references/scope-routing.md`: stakeholders, trigger queries, primary routes, boundaries, and discovery prompts.
- `references/trace-framework.md`: TRACE stages, gates, decision objects, and output logic.
- `references/data-contracts.md`: minimal schemas, normalization rules, provenance, missingness, and reconciliation checks.
- `references/calculation-catalog.md`: formulas and caveats for price, TCO, supplier, inventory, and logistics analysis.
- `references/research-and-evidence.md`: public research hierarchy, citation fields, triangulation, and stop conditions.
- `references/module-sourcing.md`: supplier landscape, RFx, AI-token sourcing, shortlist, and award workflow.
- `references/module-price.md`: PO price trends, benchmark triangulation, should-cost, anomalies, and negotiation.
- `references/module-supplier.md`: performance, quality, delivery, capacity, risk, gates, and scorecards.
- `references/module-inventory.md`: replenishment, stockout/excess detection, policy simulation, and exception queues.
- `references/module-logistics.md`: freight, container, Incoterm, duty, compliance, and landed-cost comparison.
- `references/delivery-routing.md`: defines the fixed HTML report + editable Markdown + mandatory Dynamic UI delivery stack.
- `references/html-report-enhancement-contract.md`: controlling boundary with the built-in HTML renderer, seven-token mapping, reliable ECharts pipeline, chart enhancement levels, optional PUI scope, and authoring-trace firewall.
- `references/procurement-report-architecture.md`: anti-document translation, scene-specific report families, primary visual objects, open/dense compositions, responsive collapse, and variation rules.
- `references/procurement-curatorial-framework.md`: framework/card definitions, contents and sidebar navigation, chapter-scale composition, whitespace choreography, card states, chart-text relationships, controlled variation, and reference-plate routing.
- `references/procurement-editorial-system.md`: five-level type scale, visible-text budgets, semantic line composition, open/dense spacing rhythm, strict color budget, geometry, interaction, and HTML-over-Markdown acceptance.
- `references/procurement-chart-interaction-catalog.md`: focused chart suite, valid funnel/radar/gauge use, system baseline/decision annotation/linked exploration levels, and static fallbacks.
- `references/procurement-report-interactions.md`: optional renderer-compatible markup/runtime for navigation, scroll shelves, switch cards, tabs, master/detail, question-help popovers, enhanced tables, and DOM linking.
- `references/procurement-style-routing.md`: equal-weight six-route selection, no-default rule, shared HTML/Dynamic UI identity, and complete-kit/companion contract.
- `references/procurement-visual-enhancement.md`: six procurement-native visual directions, original prompt synthesis, color/type discipline, decision grammar, and renderer brief.
- `references/editable-md-companion.md`: role-specific editable execution workpaper distinct from the analytical report.
- `references/procurement-dynamic-ui.md`: mandatory inline preview routing, six procurement layout families, companion-asset boundary, and shared token semantics for the built-in Dynamic UI.
- `references/header-image-workflow.md`: optional, explicit-request-only Seedream workflow and pre-authoring constraints for a full-width report top image.
- `assets/procurement-visual-kit/`: machine-readable six-route manifest, six lightweight original style previews, six matched SVG support kits, icon sprite, illustration, and patterns; use each selected route as one complete identity and never as third-party imitation or final header artwork.
- `assets/procurement-report-ui/`: optional renderer-token-compatible CSS and dependency-free page interaction runtime; copy only for selected page behaviors and never use it to mount charts.
- `scripts/procurement_math.py`: deterministic JSON calculator for quote, price, supplier, inventory, and landed-cost modes.
- `scripts/select_style_route.py`: unbiased six-route selector with optional seeded reproducibility for tests.
- `scripts/validate_style_routes.py`: verifies all six routed previews and complete SVG support kits.
