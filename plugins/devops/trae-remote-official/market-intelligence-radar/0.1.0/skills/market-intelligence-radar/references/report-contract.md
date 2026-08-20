# Report contract

## Contents

1. Shared evidence contract
2. Alert, daily, weekly, and monthly structures
3. Mandatory dual delivery
4. Shared Radar Style Contract
5. HTML chart and diagram routing
6. Dynamic UI routing
7. Completion and chat handoff

## 1. Shared evidence contract

Every material signal includes:

- event and effective date;
- newness state;
- priority and RISE components;
- strongest evidence with direct links;
- factual delta from baseline;
- impact interpretation and confidence;
- risk/opportunity label;
- bounded action or watch trigger.

Use exact dates and the report timezone. Preserve source titles in their original language where
helpful. Never invent values, entities, dates, scores, or sources to complete a layout.

Name the primary report directory and file with the run date in the report timezone:

- alert, daily, monthly, or one-off: `<topic>-YYYY-MM-DD`;
- weekly: `<topic>-YYYY-MM-DD-wNN`, using the ISO week of that same date.

Generate the basename with `scripts/report_name.py` before invoking `html-report`. Use the same
basename for export variants. Do not rename runtime-owned internal assets.

## 2. Report structures

### Priority alert

Trigger only for `P0`:

1. what changed;
2. response window;
3. exposure;
4. recommended move;
5. evidence and unknowns;
6. next trigger.

Keep it readable in under two minutes. Do not wait for the next scheduled digest.

### Daily pulse

Cover changes since the latest successful run:

1. verdict line;
2. compact signal overview;
3. concise P0/P1 cards, then P2 rows;
4. revisions and new evidence;
5. checked themes with no material change;
6. coverage gaps and next scan time.

If there are no verified deltas, say so and show the coverage ledger.

### Weekly synthesis

Default to the three to five most important net-new signals, but publish fewer when fewer qualify:

1. executive thesis;
2. one interactive overview matrix, timeline, or priority field;
3. one concise card per qualifying signal;
4. cross-signal pattern and implication visual;
5. act / validate / watch board;
6. synchronized evidence drawer or detail panel;
7. changed watchlist and source/coverage ledger.

The pattern section must synthesize rather than repeat headlines. Keep the full Signal Stack in the
evidence surface; never display it as seven labeled paragraphs.

### Monthly review

Emphasize movement over event count:

- persistent versus temporary patterns;
- competitor posture;
- product and price trajectory;
- capital, organization, and partnership implications;
- policy/technology phase changes;
- thesis updates and invalidated assumptions;
- decisions made and next month's watch priorities.

Chart only metrics collected consistently across runs.

For every structure, apply `signal-visual-encoding.md` when two or more signals are present.

## 3. Mandatory dual delivery

Every substantive alert, daily pulse, weekly synthesis, monthly review, competitor analysis, or
monitoring result must produce:

1. a complete HTML Report;
2. one focused Dynamic UI widget;
3. a concise chat handoff.

The same stabilized evidence and decision spine drives both visual outputs. Finish the HTML artifact
first, then invoke the current built-in `dynamic-ui` skill and call the real `PureShowWidget` tool.
Do not print widget code, fake tool syntax, or claim success before the runtime confirms it.

The Dynamic UI is not a mini HTML report. It visualizes one focal relationship: priority, change
trajectory, competitor matrix, impact propagation, evidence strength, or next decision.

Exempt only:

- the first scheduling-confirmation turn;
- a blocking clarification turn;
- a narrow fact or definition that is not a monitoring result;
- an explicit user instruction limiting formats.

If either capability is unavailable, state that the required dual delivery is incomplete. Do not
silently omit one output.

## 4. Shared Radar Style Contract

Stabilize this contract once and pass it to both system skills:

```markdown
## Radar Style Contract
- Decision:
- Audience:
- Report type:
- Time window and timezone:
- Executive thesis:
- Focal signal or relationship:
- Selected visual bucket:
- Selected curatorial framework:
- Navigation model and chapter count:
- Selected layout blueprint:
- Random selection mode: uniform-random
- Random selection ID:
- Selected style asset:
- Selected Dynamic UI companion ID:
- Selected Dynamic UI companion asset:
- Selected page background:
- Summary pattern:
- Primary visual:
- Dynamic UI scene and material intent:
- Dynamic UI companion focal/support slots:
- Product/owner brand guidance:
- Display title:
- Semantic display-title lines:
- Type roles and weight set:
- Spacing tokens and macro/micro density plan:
- HTML runtime style mode:
- Canonical HTML tokens (`--bg / --bg2 / --ink / --muted / --rule / --accent / --accent2`):
- Chromatic budget (`primary / secondary / optional pop`; maximum three):
- Neutral ink family:
- Light surface/foreground pairs:
- Dark surface/foreground pairs:
- Typography source:
- Dynamic UI role-token mapping:
- Radius model and depth:
- Card roles and shared selected-state key:
- Signal count:
- Multi-signal overview:
- Signal card grammar and visible-copy budget:
- Evidence disclosure model:
- Unified SVG icon source:
- Colored edge-strip check across cards, sidebar/rail, top bar/header, navigation, tables, sections,
  and headings: none
- 80/20 scene-specific choice:
- HTML chart and interaction contract:
- Dynamic UI interaction:
- Evidence ledger:
- Missing-data expression:
- Runtime assets copied and verified:
- Internal-artifact check: none exposed
- Accessibility and print guardrails:
```

HTML and Dynamic UI must share:

- the same facts, calculations, confidence, and recommendation;
- the same product brand role and accent;
- the same flat/layered personality and geometry family;
- the same focal signal and status vocabulary;
- the same distinction among verified change, checked/no change, and evidence gap.

Exact typography mechanics may differ because each runtime owns its tokens. Match visual identity and
hierarchy without violating the runtime's font or theme contract.

## 5. HTML chart and diagram routing

Invoke the runtime's current `html-report` skill after selecting a framework from
`curatorial-framework.md` and a blueprint from `layout-blueprints.md`. Follow
`html-report-integration.md`: let the runtime own the scaffold, canonical variables, asset paths,
fonts, chart loader, responsive/print foundation, citations, and validation. Add the radar's
information architecture and interaction layer after that valid base. Do not create a parallel shell
or token system.

Use its reusable mechanics selectively:

- local font files only;
- offline `echarts.min.js` for quantitative charts;
- offline `mermaid.min.js` only for genuinely branching topology;
- external `assets/charts.js` for chart initialization;
- CSS variables as the single source of color;
- SVG renderer, tooltip, resize behavior, responsive tables, print fallback, and nearby citations.

Expose the visual contract to the audit:

- set `data-radar-blueprint` on the root `<html>`;
- set `data-radar-framework` on the root `<html>`;
- set `data-radar-route="uniform-random"` on the root `<html>`;
- set `data-radar-selection-id` on the root `<html>`;
- set `data-radar-style-asset="<style-id>.svg"` on the root `<html>`;
- set `data-report-cadence` on the root `<html>`;
- set `data-run-date="YYYY-MM-DD"` on the root `<html>`;
- set `data-signal-count` on the root `<html>`;
- mark every analytical chapter with `[data-report-section]` and a stable `id`;
- when using Index Gate or Reading Rail, mark the navigation with `[data-report-nav]`, use real
  fragment anchors, and maintain one `aria-current="location"` item;
- wrap the display verdict in one to three `[data-title-line]` phrase spans;
- mark ECharts containers with `[data-interactive-chart]`;
- mark one adjacent system-native visual fallback per ECharts container with `[data-chart-status]`;
- mark the adjacent exact-data fallback with `[data-chart-table]`;
- for multi-signal reports, use the overview/card/trigger/detail markers defined in
  `signal-visual-encoding.md`;
- use only the runtime's canonical color variables: `--bg`, `--bg2`, `--ink`, `--muted`,
  `--rule`, `--accent`, and `--accent2`.

### Radar chart router

| Intelligence question | HTML form |
|---|---|
| Change cadence over time | ECharts line or interval timeline |
| Competitor × change theme | ECharts heatmap when values are consistent; otherwise exact matrix table |
| Priority trade-off | RISE scatter: impact × speed, size by reach, evidence in label/opacity |
| Price or package delta | grouped bar, slope, or exact old → new table |
| Evidence accumulation | step line or dated evidence strip |
| Ordered stage attrition | funnel, only with comparable stages and denominators |
| Comparable entity profile | radar, only for 2–3 entities and 3–6 identical normalized axes |
| One bounded threshold | gauge, only for one real bounded metric with a meaningful threshold |
| Impact propagation | restrained Mermaid only when branching; otherwise semantic HTML lanes |
| Decision sequence | semantic HTML act / validate / watch rail |

Use ECharts only when it clarifies at least three data points or a real quantitative relationship.
Keep missing values visible as `N/A`; never coerce unknown to zero. Funnel, radar, gauge, Sankey, and
other specialized forms are allowed when their data semantics are satisfied; never use them merely
for variety. Every chart needs a visible title, unit, period, source, and caveat.

Every quantitative chart must expose exact values and evidence on hover/focus, provide a visible
emphasis state, support tap, and bind click when it can lock a comparison, reveal evidence, open a
cited source, or trace an impact path. Provide keyboard access and an adjacent exact-data fallback.
Also provide a system-native visual in the same figure slot for runtime failure. Use semantic
HTML/CSS or accessible inline SVG drawn from the same stabilized data; hide it after a successful
interactive mount and reveal it when mounting fails. Do not expose a chart-load error message.
The native visual is a resilience fallback, not a reason to omit a working interactive chart.

HTML may contain several visuals when the report needs them, but one primary visual must carry the
main argument. Use local/offline system assets—never a CDN.

## 6. Dynamic UI routing

Always invoke the current built-in `dynamic-ui` skill for a substantive result and use its real
`PureShowWidget` tool. Let that system own widget code, token mechanics, ready material selection,
fallback behavior, host-theme support, and interaction binding.

Read `dynamic-ui-companions.md`. Use the `dynamic_ui_companion` returned by the original random
style receipt. Never run a second draw and never select a companion from report wording, evidence
shape, report type, brand, or preference. Let the built-in Dynamic UI runtime route the factual
relationship to a scene and ready material first; then adapt that material into the selected
companion's focal/support geometry without changing its data, fallback, tooltip, or interaction
contract. The companion guide is not widget code and must never be embedded or shipped.

Pass the Radar Style Contract and explicitly map the canonical HTML color roles and blueprint
identity into the widget runtime. Preserve the Dynamic UI runtime contract while enforcing:

- no purple-blue or green default;
- no gradients, glows, decorative orbs, or page shell;
- no colored edge strip or accent border on any card, cell, sidebar/rail, header/top bar,
  navigation item, table frame, section, or heading;
- map the HTML's canonical color roles into the widget runtime without introducing a generic
  rainbow;
- one focal relationship;
- at most four peer series plus `Other`;
- no emoji icons;
- verified data only;
- readable light and dark theme pairs;
- the same brand, accent, radius personality, blueprint identity, and focal signal as the HTML.
- the paired companion identity, geometry, and token values returned by the same random receipt.

If a ready Dynamic UI material uses a colored edge strip or accent border, adapt it to a neutral
complete border, text/badge cue, or full-field focus without changing the runtime behavior.

### Dynamic UI material router

| Focal relationship | Preferred scene/material intent |
|---|---|
| Change trend | `data-visualization` / `line-trend` |
| Two-peer magnitude comparison | `data-visualization` / `bar-chart-multiple` |
| Priority and outliers | `data-visualization` / `scatter-chart` |
| Competitor-theme intensity | `data-visualization` / `heatmap-chart` |
| Weighted impact flow | `data-visualization` / `sankey-chart`, only when weights are real |
| Two-entity profile on identical scales | `data-visualization` / radar material |
| Two to four choices | `comparison-and-decision` / `comparison-cards`, adapted without edge strips |
| Three to six intelligence signals | custom `signal-explorer`: compact selector, active detail, synchronized plot |
| Sparse or mixed evidence | custom `compact-table-visual` fallback |
| Act / validate / watch | custom `decision-cards` or compact decision rail |

Keep the widget compact. Use one primary visual and at most one supporting note. Put extended
interpretation in the surrounding chat response, not inside a chart-only widget. Preserve hover,
focus, tap, and useful click behavior supplied by the runtime.

The material router above is factual scene routing owned by Dynamic UI; it must not influence the
six-style random route. Any ready material may be composed through any of the six companions when
its own use/avoid limits are satisfied.

For dark HTML systems, provide explicit paired widget tokens: light defaults for a light host and
bright foreground overrides for a dark host. Never place dark gray, burgundy, navy, forest, or dark
chromatic text on a dark surface.

## 7. Completion and chat handoff

Do not finalize until:

- the HTML artifact exists and passes static file, syntax, path, and Radar audit checks;
- the HTML preserves the runtime foundation and visibly adds the selected radar blueprint;
- the HTML visibly uses the selected curatorial framework and its real navigation behavior;
- `scripts/report_visual_audit.py` passes on the report and local chart script;
- no built-in HTML validator, system HTML checker, local server, browser, browser automation, or
  screenshot validation was used;
- no internal wireframe, framework study, style-contract text, audit output, sample metric, or
  implementation note is visible;
- multi-signal results use a visual overview, concise cards, and synchronized evidence disclosure;
- no Markdown-like Signal Stack or over-budget paragraph is visible by default;
- Dynamic UI has been rendered through the actual tool;
- both outputs use the same evidence and Radar Style Contract;
- the Dynamic UI uses the companion paired to the HTML style, with no second draw or text routing;
- the widget does not contradict or embellish the report;
- citations remain in the HTML near material claims;
- any missing runtime capability is explicitly disclosed.

The chat response must:

- lead with the most important verified change and recommended direction;
- link the HTML artifact;
- identify what the Dynamic UI visualizes;
- state the strongest uncertainty;
- repeat the scheduling question only when unanswered;
- end with the nearest decision or confirmed next run.
