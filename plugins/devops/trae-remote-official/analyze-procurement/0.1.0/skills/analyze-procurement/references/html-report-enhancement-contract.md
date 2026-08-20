# System HTML-report enhancement contract

Use this reference before authoring any substantive procurement HTML. Load the current built-in `html-report` skill first and treat it as the controlling renderer contract. This package extends procurement meaning and page choreography; it does not replace the renderer.

## Contents

1. Ownership boundary
2. Minimum visible enhancement
3. Required system pipeline
4. Semantic token mapping
5. Chart reliability baseline
6. Procurement chart enhancement levels
7. Optional page interaction layer
8. Forbidden collisions
9. Authoring-trace firewall
10. Handoff brief
11. Acceptance

## 1. Ownership boundary

The built-in `html-report` capability owns:

- report scaffold and directory structure;
- entry HTML and required renderer comment/header;
- `_shared/js/` and `_shared/fonts/`;
- font copying and `@font-face`;
- CSS variable definitions and base responsive/print behavior;
- ECharts and Mermaid libraries;
- quantitative chart mounting in external `assets/charts.js`;
- report-local asset paths.

This procurement skill owns:

- decision spine and TRACE evidence;
- procurement architecture and chapter score;
- comparison basis, units, periods, gates, and reversal variables;
- chart question and chart-type choice;
- baseline, threshold, direct annotation, evidence state, and fallback content;
- optional scoped navigation, card, table, or disclosure enhancements.

If the two disagree about scaffolding, fonts, library loading, chart mounting, asset paths, or base responsive behavior, follow the current built-in `html-report` contract.

## 2. Minimum visible enhancement

The procurement layer must produce visible decision value beyond a generic system report:

1. The first viewport states a procurement action, exposure, and binding condition.
2. A report longer than six major sections provides a real contents plate, persistent chapter navigation, or both.
3. Chapters alternate open and dense compositions instead of repeating one component grid.
4. At least two standard-report chapters are card-free.
5. Every bounded card represents a named supplier, option, lane, scenario, exception, gate, action, or evidence bundle.
6. The dominant chart reaches Level 1: baseline/threshold, direct recommendation label, decision annotation, exact basis, and static fallback.
7. All charts share the same system tokens, label hierarchy, tooltip treatment, grid weight, and number formatting.
8. Knockout gates remain separate from weighted scores and decorative status colors.
9. The closing field contains action, owner, timing, gate, fallback, and verification.
10. No bounded surface uses a chromatic strip on only one edge; recommendation, risk, gate, finding, and condition callouts use type, spacing, a complete neutral border, a full-surface fill, or an inset mark instead.

If removing procurement terminology and data leaves the same generic hero/KPI/chart/card layout, or if emphasis repeatedly takes the form `tinted rectangle + colored left rail + label + paragraph`, the enhancement failed. Rework the chapter score and dominant objects before styling further.

## 3. Required system pipeline

Before writing HTML:

1. load the current built-in `html-report` skill;
2. complete its plan with the procurement architecture, curatorial, editorial, chart, and visual briefs as inputs;
3. scaffold the report through its current workflow;
4. copy only the system libraries actually used;
5. author all chart definitions in report-local external JavaScript.

After writing the HTML and report-local assets, stop the HTML workflow. Do not invoke the system HTML checker/validator, the procurement validator, a linter, a renderer, or any runtime inspection. Do not start a local server, open a browser, or take screenshots.

Preserve the system directory contract:

```text
report/
├── report.html
├── assets/
│   ├── charts.js
│   ├── report.css
│   └── optional procurement-report-ui.css/js
└── _shared/
    ├── js/echarts.min.js
    └── fonts/...
```

Use relative paths only. Do not link into this procurement skill or the built-in renderer with an absolute path.

## 4. Semantic token mapping

Use the renderer's seven theme variables. Do not introduce a competing procurement palette:

| System token | Procurement meaning |
|---|---|
| `--bg` | selected route's page field |
| `--bg2` | named surface or quiet evidence field |
| `--ink` | baseline, body text, most marks |
| `--muted` | metadata, basis, secondary labels |
| `--rule` | structural hairlines and chart grid |
| `--accent` | recommendation, active path, primary series |
| `--accent2` | failed gate or reversal trigger; keep restrained |

When no signal color is needed, keep `--accent2` in the same family as `--accent` or use an ink-derived value. Do not add `--main`, `--signal`, `--jump`, or a second root token system.

The optional procurement UI stylesheet consumes the system tokens. It must not redefine them.

## 5. Chart reliability baseline

Every quantitative chart must first satisfy the built-in renderer's stable baseline:

```html
<figure class="chart-figure">
  <figcaption>供应商到厂成本与交付表现</figcaption>
  <p class="chart-basis">CNY/件 · 最近 12 个月 · 含运费，不含可抵扣增值税</p>
  <div id="chart-supplier-frontier" class="chart-container"
    data-chart-level="1"
    role="img" aria-label="供应商成本与 OTIF 对比；A 位于建议区域"></div>
</figure>

<div data-chart-fallback>...</div>

<script src="./_shared/js/echarts.min.js"></script>
<script src="assets/charts.js"></script>
```

In `assets/charts.js`:

- use an IIFE;
- read `--accent`, `--accent2`, `--ink`, `--muted`, `--rule`, and `--bg2` once;
- call `echarts.init(..., { renderer: 'svg' })`;
- give every mount a declared `height` or `min-height` so ECharts never initializes into a zero-height container;
- include `tooltip.appendToBody: true`;
- set `animation: false`;
- resize every instance on window resize;
- keep chart logic outside inline HTML scripts;
- use only ECharts for quantitative charts;
- keep a visible title and adjacent fallback.

Script order is non-negotiable:

`echarts.min.js → assets/charts.js → optional procurement-report-ui.js`

Do not place another ECharts adapter between the library and `assets/charts.js`.

## 6. Procurement chart enhancement levels

Choose the lowest level that answers the question reliably.

### Level 0 — renderer baseline

Use for a simple supporting chart:

- visible title and basis;
- exact tooltip;
- system palette;
- SVG rendering;
- resize;
- static fallback.

### Level 1 — decision annotation

Use by default for the dominant procurement chart:

- everything in Level 0;
- visible baseline, target, or gate;
- direct label on the recommended path;
- one or two decision-driving annotations;
- explicit missing values;
- caption states the conclusion, unit, and period.

### Level 2 — linked exploration

Use only when selecting a supplier, lane, period, exception, or scenario changes another decision view:

- everything in Level 1;
- click or keyboard selection with a persistent visible state;
- one stable entity key shared with the linked table/card;
- Escape or a visible control clears selection;
- print and no-JS output preserve the default decision.

Do not require Level 2 for every chart. If a click would be a no-op, stop at Level 1.

For reliability, keep every readable fallback visible in the HTML before JavaScript runs. Put each custom Level 2 initializer behind its own guard/`try…catch` so one interaction error cannot blank unrelated charts. If reliability is uncertain before authoring, use the built-in Level 0/1 ECharts pattern or the exact fallback table instead of custom SVG, canvas, or image-based quantitative drawing. Do not test the generated HTML afterward.

## 7. Optional page interaction layer

The packaged `procurement-report-ui.css/js` may enhance:

- active chapter navigation;
- scroll-snap option shelves;
- scenario tabs;
- master/detail;
- switch cards;
- question-help popovers;
- DOM-only linked highlighting;
- enhanced tables.

Copy it only when one of these behaviors is selected. Keep all classes and attributes under the `pui-` / `data-pui-` namespace.

The page runtime must not:

- initialize ECharts;
- load fonts;
- redefine root theme variables;
- inject report data;
- rewrite the renderer scaffold;
- add a second responsive framework.

Implement Level 2 chart linkage in report-local `assets/charts.js` by listening for or dispatching stable custom events. Keep the chart mount itself native to the system renderer contract.

## 8. Forbidden collisions

Do not:

- copy or reference `procurement-echarts.js`;
- call `ProcurementCharts.mount`;
- load ECharts twice;
- initialize charts inline;
- replace `_shared/js/echarts.min.js` with a CDN;
- insert procurement runtime before `assets/charts.js`;
- copy `procurement-editorial-tokens.css`;
- redefine `--bg`, `--bg2`, `--ink`, `--muted`, `--rule`, `--accent`, or `--accent2` from the optional component stylesheet;
- make every chart interactive merely to satisfy a procurement checklist;
- fail a system-valid report because it lacks click-to-pin behavior on a supporting chart.

## 9. Authoring-trace firewall

The final report must never expose planning or selection traces such as:

- `Selected signal S05`;
- `Selected style`, `Selected direction`, or `Selected template`;
- visual-direction IDs, palette IDs, or reference-plate filenames;
- `Procurement Architecture Brief`;
- `Procurement Curatorial Brief`;
- `Procurement Editorial Brief`;
- `Procurement Chart & Interaction Brief`;
- `Procurement Visual Brief`;
- internal prompts, routing notes, tool names, or model names.

These strings are authoring inputs, not report content. Remove them from visible text, comments, data attributes, and embedded JSON.

Keep `plan.md`, briefs, prompts, scratch calculations, and validation logs in a temporary authoring directory. Do not ship them beside the final HTML.

Preserve a renderer-required source comment or header when the built-in `html-report` contract requires it. Do not add a second provenance label, and never render provenance visibly.

## 10. Handoff brief

Pass one consolidated enhancement brief into `html-report` instead of multiple competing implementation instructions:

```markdown
## Procurement Enhancement Brief
- Decision spine:
- Architecture family and visitor route:
- Chapter score and density:
- Dominant procurement object:
- System visual personality:
- Selected route ID and matched asset kit:
- Matched Dynamic UI companion and route-specific composition transform for later handoff:
- System token mapping:
- Corner model and depth rule:
- Edge treatment: prohibit physical/logical one-sided colored borders, edge pseudo-elements, nested rails, inset shadows, narrow gradients, background images, masks, and SVG edge strips
- Permitted emphasis grammar and inset separation:
- State vocabulary and initially selected entity key:
- Dominant chart question and level:
- Supporting chart question and level:
- Baseline / threshold / reversal variable:
- Direct annotations:
- Static fallbacks:
- Optional PUI behaviors:
- Required evidence and execution close:
- Internal authoring labels to suppress:
```

The brief describes intent. Let `html-report` decide the exact scaffold, font files, chart mount code, and responsive CSS.

## 11. Pre-authoring contract

Build these requirements into the report before writing the final files; do not inspect or validate the generated HTML afterward:

1. The current built-in `html-report` skill was loaded before HTML authoring.
2. The system scaffold and relative-path contract remain intact.
3. ECharts loads once and before external report-local chart code.
4. Every quantitative chart initializes natively from `assets/charts.js`.
5. Every chart passes Level 0; the dominant chart normally passes Level 1.
6. Level 2 appears only when selection changes another decision view.
7. The optional procurement UI runtime neither mounts charts nor defines root theme tokens.
8. Every chart has a visible title, basis, accessible label, declared height, resize, and fallback.
9. Procurement semantics add thresholds, gates, evidence, and action without replacing renderer behavior.
10. No authoring brief, style code, selected-signal label, prompt, or renderer/tool note appears in the report.
11. The report demonstrates the minimum visible enhancement rather than only restyling the system default.
12. The delivered report directory contains no plan, brief, prompt, scratch, or validator-log file.
13. The route-manifest identity snapshot used to author HTML is passed unchanged to Dynamic UI.
14. No built-in or procurement HTML validator, local server, browser, screenshot, renderer, linter, or HTML runtime preview is invoked after generation.
15. Before markup is written, every bounded surface is assigned one of three treatments: no border, a complete neutral border, or a full-surface flat fill.
16. No card, callout, recommendation, finding, KPI object, evidence block, figure, table wrapper, sidebar, header, topbar, navigation item, section frame, or page frame uses a physical or logical one-sided colored border, edge-anchored pseudo-element, narrow child rail, inset shadow, narrow gradient, background image, mask, or SVG edge strip.
17. Any compact badge, dot, symbol, or underline remains inside the content padding with visible neutral separation from every frame edge.
