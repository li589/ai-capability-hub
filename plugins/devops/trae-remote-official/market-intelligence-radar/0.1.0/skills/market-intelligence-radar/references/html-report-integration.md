# HTML Report integration and enhancement contract

## Contents

1. Core principle
2. Authority boundary
3. Required execution sequence
4. Canonical design-system bridge
5. Radar enhancement layer
6. ECharts reliability contract
7. Diagram and SVG routing
8. Internal-artifact ban
9. Static-only validation gate
10. Completion checklist

## 1. Core principle

The runtime's current `html-report` skill is the report engine. Market Intelligence Radar is a
domain-specific enhancement layer.

Do not fork, imitate, replace, or partially reconstruct the runtime. Let `html-report` create and own
the deliverable directory, HTML base, relative paths, local fonts, vendored JavaScript, canonical
theme variables, chart loading, citations, responsive behavior, and print behavior. Then add the
intelligence-specific reading architecture and interactions inside that
contract.

Enhancement means:

- a stronger decision spine;
- a better framework, contents system, and chapter rhythm;
- evidence-shaped composition instead of a generic card grid;
- synchronized signal, chart, action, and evidence state;
- more disciplined chart selection and labeling;
- stricter static contract checks.

Enhancement does not mean:

- another HTML scaffold;
- another color-token family;
- another ECharts copy or loader;
- inline chart initialization;
- competing responsive or print foundations;
- internal wireframes or reference images in the final report.

## 2. Authority boundary

### `html-report` owns

- report-directory scaffolding and required HTML header;
- `<report>.html`, `assets/`, `_shared/js/`, and `_shared/fonts/`;
- local/offline dependency copying and relative paths;
- font selection and `@font-face`;
- canonical CSS variables;
- ECharts and Mermaid library inclusion;
- external `assets/charts.js` authoring architecture;
- citations and Sources markup;
- base responsive, mobile-table, and print mechanics;
- runtime-specific visual modes;
- final self-contained deliverable requirements.

### Market Intelligence Radar owns

- decision, audience, signal model, evidence, and uncertainty;
- report type and chapter content;
- curatorial framework and blueprint selection;
- information hierarchy, whitespace choreography, and exhibit/text relationship;
- card roles and the anti-card test;
- shared signal selection and evidence disclosure;
- chart question, data semantics, exact-value fallback, and source attachment;
- radar-specific static checks after the runtime output exists.

If the two contracts differ on build mechanics, paths, token names, font loading, chart inclusion, or
base responsive behavior, follow `html-report`. Adapt the radar composition rather than overriding
the runtime.

Validation is the explicit exception: do not invoke an optional or suggested `html-report`
validator, preview server, browser, browser automation, screenshot, or system HTML-checking step.
Preserve the runtime's generation mechanics, then use only the static gate in section 9.

## 3. Required execution sequence

1. Stabilize facts, calculations, citations, and missing-data states.
2. Generate the required basename with `scripts/report_name.py`: `<topic>-YYYY-MM-DD`, or
   `<topic>-YYYY-MM-DD-wNN` for weekly output.
3. Run `scripts/select_visual_style.py` exactly once, then write the Radar Style Contract from its
   uniformly random style, paired framework, asset, and selection ID. Do not filter or reroll.
   Expand to the full curatorial and blueprint references only to implement that selection.
4. Invoke the current `html-report` skill and give it the dated basename, stabilized evidence,
   chapter structure,
   Radar Style Contract, chart plan, and explicit request for the **Solid** mode unless the user or
   verified brand guidance requires another runtime-supported mode.
5. Let `html-report` scaffold the report in the requested output directory.
6. Preserve its directory structure, required HTML header, fonts, canonical tokens, base styles,
   citation structure, and local library paths.
7. Enhance the visible composition using semantic HTML and an additional radar layer after the base
   styles. Use the runtime's canonical variables.
8. Put all ECharts initialization in the runtime-owned report-local `assets/charts.js`.
9. Confirm relative files, dependency order, and JavaScript syntax, then run
   `scripts/report_visual_audit.py`.
10. Do not invoke the built-in `html-report` validator or another system HTML checker. Do not start
    a local HTTP server, open a browser, use browser automation, capture screenshots, or perform
    rendered visual QA.
11. Fix every static audit, syntax, path, stale-content, and contract failure before producing
    Dynamic UI. Do not claim that rendering or interactions were visually verified.

Never run a hand-authored fallback report in parallel with `html-report` when the runtime is
available. If the runtime is unavailable, state that the mandatory HTML delivery is incomplete.

## 4. Canonical design-system bridge

Use the runtime's variables as the single source of visual truth:

| Runtime token | Radar role |
|---|---|
| `--bg` | page field |
| `--bg2` | optional secondary surface |
| `--ink` | primary foreground |
| `--muted` | secondary text and low-emphasis chart context |
| `--rule` | borders, axes, dividers, and inactive geometry |
| `--accent` | selected signal and focus series |
| `--accent2` | optional second comparison or runtime visual mode |
| `--font` | report typography |
| `--font-mono` | dates, compact metadata, source keys, and exact technical values |
| `--max` | runtime content-width foundation |

Do not define `--radar-bg`, `--radar-fg`, `--radar-muted`, `--radar-accent`, or
`--radar-surface`. Do not duplicate a runtime color under a radar alias. Dynamic UI may map from the
canonical runtime values into its own host tokens, but the HTML keeps one token family.

The Radar Style Contract supplies the intended values and roles; `html-report` writes the canonical
variables. Additional radar CSS must reference only those variables for color.

Default market-intelligence reports to the runtime's **Solid** mode. Use another runtime-supported
mode only when the user explicitly requests it or verified brand guidance calls for it. When a
gradient/glass mode is selected:

- keep charts, tables, evidence drawers, tooltips, and source ledgers on opaque high-contrast fields;
- never place gradients behind dense copy;
- do not introduce generic purple-blue AI styling;
- retain the radar's single-focus-series logic;
- preserve print-safe evidence surfaces.

## 5. Radar enhancement layer

Apply the radar layer after the runtime base rather than replacing it.

Enhance:

- the `<main>` composition and chapter sequence;
- Index Gate or Reading Rail navigation when content requires it;
- asymmetric exhibit fields;
- signal-card state and evidence disclosure;
- primary-chart/card synchronization;
- act / validate / watch objects;
- source-to-signal traceability.

Preserve:

- the runtime page and asset structure;
- canonical variables and selected fonts;
- runtime typography mechanics unless the Radar Style Contract requests a compatible role change;
- citation and Sources behavior;
- table wrappers, mobile collapse, and print rules;
- script placement and dependency order.

Do not use the runtime's sample report title, sample colors, sample metrics, or placeholder sections.
Do not fight a valid base with a full CSS reset. Override the smallest set of visible composition
rules required to express the selected framework and blueprint.

## 6. ECharts reliability contract

Every ECharts report must satisfy the runtime contract and the radar additions below.

### Files and order

- `_shared/js/echarts.min.js` exists in the report directory and is the runtime-provided local file;
- HTML contains `<script src="./_shared/js/echarts.min.js"></script>`;
- chart logic lives in a report-local external file such as
  `<script src="./assets/charts.js"></script>`;
- the ECharts library tag appears before every chart-logic tag;
- no CDN, absolute local path, base64 library, or inline `echarts.init(...)` appears;
- all scripts are placed after the chart containers.

Do not copy or bundle ECharts inside this plugin. Always use the library supplied by the active
`html-report` runtime.

### Container and native visual fallback

Every chart has:

- a `<figure>` wrapper and visible `<figcaption>`;
- a unique, non-empty container `id`;
- an explicit `min-height`, normally at least `360px`;
- `data-interactive-chart`;
- one adjacent `[data-chart-status]` element containing a complete system-native fallback visual,
  not loading/failure text;
- an adjacent exact-value table marked `[data-chart-table]`;
- a source, unit, period/timezone, and missing-data note.

Build the fallback from the same stabilized values and show it in the same figure slot. Use semantic
HTML/CSS for bars, matrices, timelines, and simple position fields; use an accessible inline SVG
when axes or point placement are essential. Include the chart title, scale or legend where needed,
and readable data labels. Do not display "chart failed to load", "please see the table below", or
other implementation-state copy. The exact table remains available for detail and accessibility,
but it is not the visual substitute.

For a heatmap, calculate height from category count and follow the runtime's heatmap rules. Never
force a six-row heatmap into a short generic container.

### Safe boot pattern

The report-local external chart file must:

- use an IIFE;
- read `--accent`, `--accent2`, `--ink`, `--muted`, `--rule`, and `--bg2` once with
  `getComputedStyle`;
- wait for `document.fonts.ready` when supported before mounting;
- check that `window.echarts` exists;
- check each container before initialization so one missing container cannot stop later charts;
- initialize with `{ renderer: 'svg' }`;
- set `animation: false`;
- use `tooltip.appendToBody: true`;
- enable `aria` and a visible `emphasis` state;
- catch configuration or mount errors and reveal the chart's `[data-chart-status]` native visual;
- attach resize behavior required by `html-report`; a `ResizeObserver` may supplement the window
  listener for containers that change width after card/detail selection;
- dispose or reuse existing instances before remounting;
- derive colors from canonical variables rather than ECharts defaults or hardcoded values.

Recommended structure inside `assets/charts.js`:

```javascript
(function () {
  "use strict";

  function ready(callback) {
    var fonts = document.fonts && document.fonts.ready;
    if (fonts && typeof fonts.then === "function") fonts.then(callback, callback);
    else callback();
  }

  function mountChart(id, option) {
    var el = document.getElementById(id);
    var fallback = document.querySelector('[data-chart-status="' + id + '"]');
    if (!el || !window.echarts) {
      if (el) el.hidden = true;
      if (fallback) fallback.hidden = false;
      return null;
    }
    try {
      var existing = echarts.getInstanceByDom(el);
      if (existing) existing.dispose();
      var chart = echarts.init(el, null, { renderer: "svg" });
      chart.setOption(option);
      if (fallback) fallback.hidden = true;
      el.hidden = false;
      window.addEventListener("resize", function () { chart.resize(); });
      if (window.ResizeObserver) {
        new ResizeObserver(function () { chart.resize(); }).observe(el);
      }
      return chart;
    } catch (error) {
      el.hidden = true;
      if (fallback) fallback.hidden = false;
      return null;
    }
  }

  ready(function () {
    /* Read canonical CSS variables once, then mount report-specific charts. */
  });
})();
```

The snippet is an integration pattern, not a complete chart. The fallback element must contain the
finished native visual, never status text or implementation commentary.

### Interaction

When signal cards and a chart share data:

- the chart stores the same signal ID used by the card;
- chart click dispatches the shared selection event;
- card selection calls `dispatchAction` or `setOption` to emphasize the matching chart data;
- locked selection and hover preview remain visually distinct;
- keyboard users can reach the same exact values through the adjacent table;
- failure of the interaction reveals the native visual and never hides the data table.

## 7. Diagram and SVG routing

Follow the active `html-report` tool router:

- ECharts for quantitative data charts;
- Mermaid, PlantUML, or Graphviz for real structural topology;
- inline SVG for runtime-permitted minimal graphics and for an exact-data ECharts failure fallback;
- HTML/CSS for simple act / validate / watch rails and non-branching traces.

Radar-specific constraint: an inline SVG must not replace a working primary interactive exhibit.
It may occupy the same slot only as the failure fallback, with real axes, legend, and exact stabilized
data when needed. It must never depict invented evidence.

Do not ban runtime-supported SVG components globally. Route them correctly and keep exact values in
semantic HTML.

## 8. Internal-artifact ban

The final report must never contain:

- wireframes, layout studies, framework diagrams, moodboards, or screenshots used to inspire the
  design;
- plugin documentation, Radar Style Contract text, audit output, implementation notes, or code
  snippets;
- placeholder charts, skeleton loaders captured as content, gray-box studies, lorem ipsum, sample
  metrics, or sample navigation;
- names of internal blueprints or framework implementation terminology unless it is meaningful to
  the reader;
- asset inventory, tool names, runtime instructions, or descriptions of how the report was built.

Only evidence, analysis, decisions, uncertainty, and reader-facing navigation may appear.

The `assets/radar-visual-kit/` directory contains production-safe code and icons plus six internal
one-to-one layout guides. Do not copy its `layout-guides/` files or any other plugin reference file
into the report's assets.

## 9. Static-only validation gate

Use only deterministic source inspection. Acknowledge that static checks cannot prove that a chart
will render correctly; do not compensate by launching visual tooling.

Before delivery:

1. confirm every relative asset exists;
2. syntax-check every report-local JavaScript file;
3. inspect script order and local dependency paths statically;
4. run `scripts/report_visual_audit.py`;
5. verify required responsive, print, accessibility, tooltip, selection, fallback, and resize code
   exists;
6. verify source markup contains no placeholder, stale sample, or internal reference material.

If steps 1–4 already show that an interactive chart cannot initialize, replace it in the same figure
with its native visual and continue. This is part of generation, not an additional validation pass.

Explicitly prohibited:

- invoking the built-in `html-report` validator or any other system HTML checker;
- starting a local server or preview server;
- opening the report in a browser or using browser automation;
- taking screenshots, rendered captures, or visual snapshots;
- using browser console or network-panel inspection.

## 10. Completion checklist

- `html-report` generated the deliverable structure;
- no parallel scaffold, token family, library copy, or chart loader was introduced;
- canonical variables drive report and chart colors;
- the selected radar framework is visible without replacing the runtime foundation;
- internal reference material is absent;
- ECharts library and chart scripts exist and load in the correct order;
- all chart containers have titles, height, native visual fallbacks, and exact tables;
- chart code uses safe external initialization and switches a missing or failed chart to its native
  visual without reader-facing error copy;
- only static file, syntax, dependency, markup, and Radar audit checks were run;
- no server, browser, screenshot, built-in validator, or system HTML checker was used;
- the final HTML remains self-contained and offline.
