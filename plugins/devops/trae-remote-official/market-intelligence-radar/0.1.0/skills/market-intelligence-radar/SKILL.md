---
name: market-intelligence-radar
description: Continuously monitor competitors, products, pricing, commercialization, financing, organizations, partnerships, markets, technologies, policies, and ecosystems; detect net-new changes against a prior baseline; deduplicate and cluster evidence; prioritize signals; analyze implications; and produce alerts, daily briefs, weekly reports, or monthly reviews. Use for competitive intelligence, market intelligence, competitor tracking, product-change tracking, strategic watchlists, recurring research, monitoring setup, or queries such as 市场情报、竞争情报、竞品追踪、每日监测、周报、月报、重点预警、市場調査、競合インテリジェンス. Do not use for full industry landscape studies, company-wide strategy planning, crisis-response execution, private-person monitoring, plain news aggregation, or automatic business decisions.
---

# Market Intelligence Radar

Market & Competitive Intelligence Radar · 市場・競争インテリジェンスレーダー  
持续看见变化，提前判断影响。

Act as one intelligence application. Keep internal routing invisible. Turn scattered updates into a
defensible change log and a short list of decisions—not a longer news feed.

## 1. Establish the watch

Extract or infer the smallest useful watch specification:

- decision to support;
- monitored entities, products, markets, technologies, policies, and ecosystems;
- change themes and exclusions;
- geography, language, and time horizon;
- baseline date or prior run;
- intended readers and delivery cadence.

Start with a narrow working scope when reasonable. State material assumptions in one compact note.
Ask only when two plausible scopes would materially change the monitoring result.

Read `references/operating-model.md` for first-run setup, recurring state, cadence selection, and
automation behavior. On the first response of a new watch, always recommend a cadence with a
one-sentence reason and ask whether to create that recurring schedule. Do not create an automation
until the user confirms. If the runtime exposes an automation-management tool, use the real tool
after confirmation; never print or imitate its protocol.

## 2. Run the RADAR loop

Use one consistent loop:

1. **Register** — define decision, entities, themes, hypotheses, source map, baseline, and cadence.
2. **Acquire** — search timely multilingual sources with a primary-source-first query mesh.
3. **Detect** — normalize entities, cluster duplicates, compare with the baseline, and isolate deltas.
4. **Appraise** — score consequence, immediacy, strategic exposure, and evidence strength.
5. **Respond** — explain implications, recommend a bounded response, and define the next watch trigger.

Read `references/source-strategy.md` before external research. Read
`references/signal-model.md` before prioritizing more than five events, reconciling duplicates, or
performing impact analysis.

Use a focused scan by default. Aim for three to five decision-relevant net-new signals, use a small
number of high-yield queries, and stop when the strongest items have enough evidence for a useful
brief. Start with official sources; add one strong corroborating source only when the claim is
consequential, ambiguous, or likely to become P0/P1. Do not traverse every source tier, expand every
keyword branch, or build an exhaustive industry picture. Deepen research only for a material P0,
sensitive financial/legal/policy claims, conflicting evidence, or an explicit user request.

## 3. Research for freshness and accuracy

For current monitoring, browse the web. Use user-provided or connected evidence first, then official
and primary public sources, then credible secondary sources, then frontier/community sources as
leads. Search in the relevant local languages and use date-bounded queries.

Keep working notes compact and avoid repeating the same fact across acquisition, detection,
appraisal, and response. Prefer a clear, well-designed brief over marginal extra coverage once the
decision and top signals are supported.

Treat Product Hunt, Hacker News, GitHub discussions, Reddit, public WeChat articles, public
Xiaohongshu posts, social accounts, app-store reviews, and similar sources as early-signal surfaces.
Verify material claims against an official source or a second independent source whenever possible.
If an inaccessible or login-gated source matters, record the gap; do not bypass access controls.

Capture four dates when available: event date, publication date, observed date, and effective date.
Prefer the effective date when assessing urgency. Cite the page supporting each material factual
claim. Distinguish sourced fact, derived delta, inference, recommendation, and unknown.

Never reproduce full articles, paid content, large screenshots, or source imagery without permission.
Use brief paraphrases, short quotations only when necessary, and direct links. Do not monitor private
people, closed groups, non-public accounts, personal contact details, or sensitive personal data.

## 4. Identify what is genuinely new

Do not call an item new merely because it appeared in today's search results.

Compare against the latest successful run and the maintained competitor/product baseline. A signal
is new when at least one decision-relevant field changed: capability, availability, price, packaging,
commercial terms, target segment, distribution, integration, leadership, funding, partnership,
market evidence, technical constraint, policy status, or ecosystem behavior.

Cluster cross-posts and syndicated coverage into one event. Keep the earliest credible source and the
strongest confirming source. Separate:

- **new event** — first known occurrence;
- **new evidence** — stronger confirmation of a known event;
- **revision** — a known fact changed;
- **continuation** — activity without a material delta;
- **recirculation** — old information resurfaced.

For recurring watches, use `scripts/radar_state.py` to persist run and signal identities when a local
workspace is appropriate. Do not create persistent state for a one-off question.

## 5. Prioritize signals

Use the RISE score from `references/signal-model.md`:

- **Reach** — breadth of affected customers, competitors, regions, or value-chain nodes;
- **Impact** — magnitude of business-model, product, cost, demand, or regulatory consequence;
- **Speed** — time until consequence or response window;
- **Evidence** — reliability and cross-source confirmation.

Assign `P0` only to a time-sensitive material threat or opportunity that warrants interruption.
Use `P1` for weekly decision items, `P2` for watchlist developments, and `P3` for weak or contextual
signals. A low-confidence item cannot become `P0` without explicit uncertainty and a verification
action.

For every `P0` or `P1`, write the Signal Stack:

`event → evidence → delta → meaning → exposure → move → next trigger`

Avoid false precision. Numeric scores rank attention; they do not prove the conclusion.

## 6. Deliver the right brief

Read `references/report-contract.md` before producing a daily brief, weekly report, monthly review,
or priority alert. Before scaffolding any deliverable, generate its dated basename with
`scripts/report_name.py`. The primary deliverable directory and file must use
`<topic>-YYYY-MM-DD`; weekly output must use `<topic>-YYYY-MM-DD-wNN`, where `NN` is the ISO week
of that date. Reuse that basename for PDF or export variants. Keep runtime-owned internal asset
names such as `assets/charts.js` unchanged.

For visual output, read `references/html-report-integration.md` and
`references/visual-quickstart.md`. Before interpreting the report shape or reading any blueprint
selection guidance, run `scripts/select_visual_style.py` exactly once. Accept its uniformly random
style, paired framework, and SVG asset without filtering, weighting, rerolling, or substituting
based on evidence shape, report type, brand, prior output, or personal preference. Apply the
returned `page_background` exactly. The same receipt returns the one-to-one Dynamic UI companion;
do not run a second draw or route a companion from text, evidence shape, report type, or preference.
Use the quick
path by default for alerts, daily pulses, and weekly reports with no more than six signals: use no
external design-inspiration search or generated decorative illustration, and use at most one
primary chart.
Read the deeper `references/curatorial-framework.md`, `references/visual-enhancement.md`, and
`references/layout-blueprints.md` only to implement the already-selected style for monthly reports,
more than six signals, substantial verified brand customization, or a composition requiring deeper
rules. Never use those references to change the random selection. Read
`references/signal-visual-encoding.md` whenever the result contains two or more signals or any
Signal Stack.
Default to:

- priority alert for one `P0`;
- daily pulse for changes since the last successful run;
- weekly synthesis for the three to five most important net-new signals;
- monthly review for patterns, strategic shifts, and watchlist changes.

Lead with what changed and why it matters. Keep evidence attached to each signal. Include a
`No material change` section when a monitored theme was checked but produced no verified delta.
Never pad the report to reach a target count.

Never render `Event / Evidence / Delta / Meaning / Exposure / Move / Next trigger` as seven visible
paragraphs. Convert the stack into an overview matrix, concise signal cards, delta/impact/action
objects, and interactive detail disclosure. Preserve the full stack in the evidence layer without
making it the default reading surface.

Prefer interactive charts, but never deliver a visible chart-load error. Every interactive HTML
chart must carry a system-native fallback in the same figure slot, drawn with semantic HTML/CSS or
accessible inline SVG from the same exact data. Hide that fallback after a successful mount; reveal
it when the library, container, configuration, or mount fails. If the existing static path or syntax
check already shows that the interactive chart cannot work, keep the report structure and replace
that chart in place with the native fallback before delivery. Do not show "chart failed to load" or
an equivalent implementation message to the reader.

Every substantive monitoring result must deliver all of:

1. **HTML Report** — the complete evidence-led artifact through the runtime's current `html-report`
   skill. That runtime owns scaffolding, relative paths, local fonts, canonical CSS tokens, offline
   ECharts/Mermaid, chart initialization, responsive mechanics, citations, printing, and base
   mechanics. Never replace or duplicate those mechanics. Pass the Radar Style Contract into the
   runtime, then add the selected curatorial framework, intelligence-specific composition,
   navigation, chapter rhythm, signal-card behavior, and evidence disclosure on top of its generated
   structure. Enhancement means a compatible layer after the runtime base—not a competing report
   shell, token family, chart loader, or asset pipeline.
   Pass the dated basename to its scaffold command. Run `scripts/report_visual_audit.py` on the
   finished HTML and chart script before delivery.
   Use static-only validation. Do not invoke the built-in `html-report` validator or another system
   HTML checker. Do not start a local server, open the report in a browser, use browser automation,
   capture screenshots, or perform rendered visual QA. Check files, paths, JavaScript syntax, and
   the Radar audit only.
2. **Dynamic UI** — one compact focal visualization through the runtime's current `dynamic-ui`
   skill and its real `PureShowWidget` tool. Invoke it after the HTML is complete. Use the same facts,
   selected blueprint identity, color tokens, geometry personality, and focal signal as the HTML.
   Read `references/dynamic-ui-companions.md`, then adapt the runtime-selected scene and ready
   material into the randomly paired companion skeleton. The runtime continues to own widget code,
   materials, token mechanics, theme support, fallback, and interaction. Keep it focused; do not
   reproduce the full report in the widget.
3. **Chat summary** — a decision-led handoff that links the HTML and explains the Dynamic UI focus.

Do not consider a substantive report complete until both HTML Report and Dynamic UI have been
successfully produced. Never serialize, imitate, or claim a tool call. If either runtime capability is
unavailable or fails, complete what is safely possible and state that the required dual delivery is
incomplete.

The mandatory dual-delivery rule does not apply to the first scheduling-confirmation turn, a blocking
clarification turn, or a narrow factual answer that does not constitute a monitoring result. Honor an
explicit user request to restrict formats.

## 7. Preserve decision integrity

Do not provide a full industry landscape, enterprise-wide strategy, crisis response, or autonomous
commercial decision. Narrow the output to monitored changes, implications, response options, and
validation triggers.

Do not infer confidential metrics, private plans, unannounced financing, or employee intent from weak
signals. Label hypotheses as hypotheses. For sensitive claims, require stronger corroboration and use
neutral language.

## Resource map

- `references/operating-model.md` — onboarding, cadence, automation, state, and recurring run logic.
- `references/source-strategy.md` — timely source hierarchy, query mesh, verification, and rights safety.
- `references/signal-model.md` — taxonomy, deduplication, RISE priority, and impact analysis.
- `references/report-contract.md` — alert, daily, weekly, monthly, HTML, Dynamic UI, and dual-delivery contracts.
- `references/html-report-integration.md` — authority boundary, canonical runtime tokens and paths, chart reliability gate, and enhancement sequence.
- `references/visual-quickstart.md` — mandatory uniform random style selection, three-color rule, edge-strip ban, and fast build path.
- `references/curatorial-framework.md` — framework implementation, whitespace choreography, card roles, and interaction state machine.
- `references/visual-enhancement.md` — enforceable typography, spacing, color, geometry, and interaction rules.
- `references/layout-blueprints.md` — six original radar page compositions selected only by the random router.
- `references/dynamic-ui-companions.md` — six one-to-one compact companion compositions and the
  authority boundary with the built-in Dynamic UI runtime.
- `references/signal-visual-encoding.md` — text budgets, signal-card grammar, overview matrices, and progressive disclosure.
- `scripts/report_name.py` — deterministic dated basename generator; adds the ISO week for weekly reports.
- `scripts/select_visual_style.py` — validates the six-style asset manifest and selects one style with exact `1/6` probability.
- `scripts/radar_state.py` — local SQLite run ledger for deterministic new/duplicate/revision handling.
- `scripts/report_visual_audit.py` — deterministic HTML visual-contract checks.
- `assets/radar-visual-kit/` — six HTML guides, six paired Dynamic UI companion guides, their
  manifests, unified icons, and runtime-compatible interaction recipes; guide files are for
  proportion and palette reference only and must never appear in a delivered report.
