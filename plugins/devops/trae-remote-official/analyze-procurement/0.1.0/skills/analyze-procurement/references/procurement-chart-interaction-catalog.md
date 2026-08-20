# Procurement chart and interaction catalog

Use this reference after selecting the architecture and editorial system. Prefer a small, polished chart suite over novelty. System-provided ECharts funnel, radar, gauge, and other charts remain valid when they fit the question and meet the interaction contract.

## Contents

1. Selection rule
2. Core chart suite
3. Funnel, radar, and gauge
4. Scene recipes
5. Enhancement levels and system contract
6. Linked behavior
7. Visual consistency
8. Accessibility and fallback
9. Chart brief
10. Acceptance

## 1. Selection rule

For every chart, write:

`question → comparison basis → chart → threshold → enhancement level → tooltip/direct annotation → optional linked action → static fallback`

Reject a chart when a sentence or table answers the question faster.

Use:

- one dominant chart;
- zero to two supporting chart types in a standard report;
- more only in a clearly separated analytical appendix.

Do not vary chart type merely to make sections look different. Reuse one chart grammar when questions are comparable.

Read `html-report-enhancement-contract.md` before authoring charts. The interaction bullets below describe available Level 2 behavior, not a mandatory burden for every chart. Every chart must pass Level 0; the dominant chart normally reaches Level 1; use Level 2 only when selection changes another decision view.

## 2. Core chart suite

### A. Ranked comparison

Use a horizontal bar, dot, lollipop, dumbbell, or bullet construction for:

- normalized quotes;
- supplier performance;
- lead time;
- capacity headroom;
- target versus actual.

Choose one mark family and keep it across comparable sections. Show direct labels and a target line.

Level 2 option:

- hover: exact value, unit, basis, rank, target delta, evidence state;
- click: pin a supplier/item and synchronize its detail;
- keyboard: arrow through items, Enter pins, Escape clears.

### B. Time and uncertainty

Use an annotated line with optional quantity/range band for:

- PO or benchmark price;
- projected inventory;
- OTIF/quality trend;
- freight or lead time.

Level 2 option:

- hover: axis pointer with date, value, denominator, and event note;
- click: pin a date or event and open its evidence note;
- optional data zoom only when the visible period is dense.

### C. Cost or variance bridge

Use a waterfall/bridge for:

- quote to TCO;
- landed cost;
- PPV;
- mix, FX, freight, duty, or rebate effects.

Level 2 option:

- hover: component amount, sign, formula/basis, cumulative total;
- click: select a component and reveal the source rows or scenario control;
- keep total and baseline visible without interaction.

### D. Trade-off frontier

Use scatter/bubble or threshold quadrants for:

- cost versus capability;
- cost versus lead time;
- risk versus value;
- coverage versus inventory value.

Level 2 option:

- hover: named option and both axes with units plus bubble basis;
- click: pin the option across report views;
- legend/filter: only for one meaningful grouping;
- show threshold lines and selected option labels in the default view.

### E. Matrix

Use heatmap, gate matrix, or compact table visualization for:

- mandatory qualification;
- supplier × metric;
- item × site;
- risk × control;
- exception timing.

Level 2 option:

- hover: row, column, exact value/status, denominator, evidence date;
- click: pin a cell and open the underlying evidence;
- keep `PASS / FAIL / COND / UNK` in text, not color alone.

### F. Portfolio and concentration

Use Pareto bars or treemap for:

- supplier/category spend;
- inventory value;
- concentration and long tail;
- single-source exposure.

Level 2 option:

- hover: value, share, cumulative share, and material count;
- click: filter/highlight the selected supplier/category in other views;
- do not use decorative treemap rectangles without labels.

### G. Flow and sequence

Use Sankey, route strip, timeline, or Gantt for:

- allocation flow;
- sourcing stages;
- logistics handoffs;
- CAPA, onboarding, and execution gates.

Level 2 option:

- hover: from/to, quantity/cost/time, owner, and gate;
- click: pin a node, link, stage, or milestone and show dependencies;
- do not hide critical-path or failed-gate labels.

### H. Distribution

Use box plot, range bar, or histogram only when row-level comparable observations support it.

Level 2 option:

- hover: quartiles/range/bin, count, exclusions, and period;
- click: reveal the contributing observations;
- never infer a distribution from a few summary values.

## 3. Funnel, radar, and gauge

These system chart types are allowed. Use them deliberately.

### Funnel

Use when the question is true stage attrition: invited → responded → qualified → finalist → awarded.

- Show count and conversion denominator at every stage.
- Hover reveals stage basis, exclusions, and conversion rate.
- Click filters the supplier list to that stage.
- Do not use a funnel for a generic process sequence.

### Radar

Use for at most three finalists and three to six normalized dimensions when shape comparison is genuinely useful.

- Show scale direction, normalization formula, weights, and missing-data handling outside the tooltip.
- Keep knockout gates separate.
- Hover emphasizes one supplier and shows raw plus normalized values.
- Click pins one supplier and synchronizes its evidence card.
- Provide a comparison table fallback.

### Gauge or progress ring

Use for one current value against one target/tolerance, such as OTIF, utilization, or budget consumed.

- Show the number, unit, target, and status in text.
- Hover reveals basis and period.
- Click opens the trend or denominator detail.
- Do not repeat many gauges in a grid; use bullet charts for peer comparison.

## 4. Scene recipes

| Scene | Dominant chart | Supporting chart | Optional system chart |
|---|---|---|---|
| RFx / shortlist | ranked quote comparison or frontier | gate matrix | funnel for genuine stage attrition |
| Price / cost | annotated line or cost bridge | ranked comparison | gauge only for one budget/target |
| Supplier portfolio | frontier or Pareto | bullet strip / matrix | radar for ≤3 finalists |
| Inventory | projected line with range | exception matrix | gauge for one coverage target |
| Logistics | cost-time frontier or route flow | landed-cost bridge | funnel rarely appropriate |
| Approval | one comparison or bridge | gate matrix | no chart required when evidence is simple |

## 5. Enhancement levels and system contract

Use the current built-in `html-report` chart runtime exactly as described in `html-report-enhancement-contract.md`. Do not copy a second ECharts adapter.

### Level 0 — renderer baseline

Require for every quantitative chart:

1. visible title and nearby unit/basis/period;
2. exact tooltip with `appendToBody: true`;
3. report-token colors;
4. SVG rendering;
5. `animation: false`;
6. resize on window change;
7. adjacent static/print fallback.

### Level 1 — decision annotation

Use for the dominant chart and any chart that carries a decision:

1. everything in Level 0;
2. visible baseline, target, or gate;
3. direct label on the recommended/default path;
4. one or two decision-driving annotations;
5. explicit `N/A` / `UNK` handling.

### Level 2 — linked exploration

Use only when selecting a mark changes another meaningful view:

1. everything in Level 1;
2. click or keyboard selection with persistent visible state;
3. one stable entity key shared with the linked table/card/detail;
4. Enter/Space selects and Escape or a visible control clears;
5. responsive resize after a hidden panel becomes visible;
6. static/print output preserves the recommended default.

A supporting chart does not fail because it stops at Level 0 or Level 1. Do not invent click behavior to satisfy a checklist.

## 6. Linked behavior

Use this section only for Level 2. Use stable `data-pui-key` identifiers for suppliers, items, lanes, scenarios, and dates.

- DOM hover/focus highlights the matching chart mark.
- Chart hover may softly emphasize matching DOM content.
- Chart click pins the key across chart, table, and narrative.
- Escape clears the pinned key.
- Scenario tabs update chart and consequence table together.
- A hidden chart resizes after `pui:panelchange`.

Do not match on display text. Names can contain punctuation or change.

## 7. Visual consistency

Read colors and typography from CSS variables:

- `--ink` for baseline marks and text;
- ink-opacity variants for secondary series, rules, and inactive marks;
- `--accent` for recommended/selected state;
- `--accent2` only for failed gates or reversal triggers;
- `--bg` / `--bg2` for tooltip and selection foreground pairing.

Rules:

- Do not use the ECharts default palette.
- Do not assign one hue per supplier.
- Use at most three chromatic hues across the full report: one primary, one auxiliary, and one optional pop/reversal hue.
- Reuse the same supplier marker/line convention across charts.
- Use `400` for chart labels and numbers, `600` for titles/selected labels, and `700` only for one decisive total or exception.
- Keep tooltip radius and chart container geometry aligned with the selected visual direction.
- Avoid gradients, shadows, glow, and 3D effects.

## 8. Accessibility and fallback

- Give every chart a visible title and nearby basis line.
- Add an accessible chart label summarizing the question and default conclusion.
- Keep the selected/recommended option directly labeled.
- Do not hide thresholds, failed gates, or the verdict in tooltips.
- Respect reduced motion.
- Keep touch targets at least 44px for explicit controls.
- In print, show the default state plus a compact comparison table.
- If interaction cannot be implemented reliably, use a system chart with supported interaction or use a table; do not ship a decorative static custom chart.
- Decide reliability before authoring. When uncertain, use a built-in Level 0/1 chart or table rather than custom Level 2 code; do not test the generated HTML afterward.

## 9. Chart brief

```markdown
## Procurement Chart & Interaction Brief
- Dominant question:
- Dominant chart:
- Enhancement level: Level 0 / Level 1 / Level 2
- Why this chart is clearer than a table:
- Comparison basis / unit / period:
- Baseline / target / threshold:
- Hover content:
- Linked action, only for Level 2:
- Keyboard traversal, only for Level 2:
- Persistent selection treatment, only for Level 2:
- Linked entity key, only for Level 2:
- Supporting chart:
- System funnel/radar/gauge use, if any:
- Mobile behavior:
- Static and print fallback:
- Ink / main / signal mapping:
```

## 10. Authoring constraints

Apply before writing the final HTML:

1. A standard report uses no more than three chart types.
2. Every chart answers one written question.
3. Funnel, radar, and gauge are used only under their stated conditions.
4. Every chart passes Level 0; the dominant chart normally passes Level 1.
5. Level 2 is used only when click/keyboard selection changes a meaningful linked state.
6. Units, basis, period, baseline, target, and threshold appear where relevant.
7. Missing data remains `N/A` or `UNK`.
8. Gates remain separate from scores.
9. Every chart uses the report's ink/main/signal palette and weight roles.
10. No custom chart ships as a static decorative graphic.
11. ECharts loads once through the built-in renderer and chart code remains in external `assets/charts.js`.
12. No procurement-specific adapter competes with the system chart mount.
13. Every chart mount declares `data-chart-level="0|1|2"` for consistent authoring semantics.
14. Custom Level 2 behavior is used only when its implementation is already known; otherwise use the built-in Level 0/1 pattern or exact table fallback.

Do not run chart linting, runtime smoke tests, a local server, a browser, screenshots, or post-render validation after the HTML is generated.
