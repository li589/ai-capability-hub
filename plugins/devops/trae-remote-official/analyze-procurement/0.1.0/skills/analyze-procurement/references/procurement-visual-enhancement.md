# Procurement visual enhancement for system HTML reports

Use this reference only after the procurement analysis is stable and after loading the current built-in `html-report` skill plus `html-report-enhancement-contract.md`. Supply procurement intent to that renderer. Do not implement a competing renderer, template, token layer, font loader, chart runtime, responsive system, or validator.

## Non-negotiable pre-authoring aesthetic invariant

Resolve this before choosing card or callout markup. It is a generation rule, not a post-generation inspection.

No bounded surface may carry a chromatic strip, rail, band, or partial accent edge on only one side. The rule applies equally to cards, callouts, recommendations, findings, KPI objects, evidence blocks, figures, table wrappers, sidebars, headers, topbars, navigation items, section frames, and page frames.

All of these implementations are prohibited:

- `border-left`, `border-right`, `border-top`, or `border-bottom` used as a chromatic accent;
- `border-inline-start`, `border-inline-end`, `border-block-start`, or `border-block-end` used as a chromatic accent;
- `::before` or `::after` anchored to one edge as a colored rail;
- a narrow first or last child positioned against an edge;
- an inset `box-shadow` that reads as a colored strip;
- a narrow gradient stop, background image, mask, or SVG used as an edge band;
- a one-sided colored outline, highlight, or continuous gutter;
- the same device made subtle, translucent, short, rounded, or theme-matched.

Never generate the generic template pattern `tinted rectangle + colored left rail + small status label + paragraph`. It remains prohibited on a dark field, on white, and on a quiet neutral surface.

Use one of these emphasis grammars instead:

- typography, spacing, alignment, or numeral scale;
- a full neutral border of equal treatment on all sides;
- a full-surface flat fill with a tested foreground pair;
- a compact badge, dot, symbol, or short underline placed inside the content padding and visibly separated from every frame edge;
- a full bounded reversed field rather than a partial edge;
- a standalone chart mark, threshold, or direct label.

This invariant travels with every style route and into Dynamic UI. Do not create a post-generation checker for it.

## Contents

1. Renderer boundary
2. Architecture handoff
3. Optional generated header image
4. Visual directions
5. Type, spacing, and anti-patterns
6. Procurement chart grammar
7. Evidence and decision grammar
8. Interaction
9. Packaged style references
10. Original visual-direction prompt
11. Procurement Visual Brief
12. Pre-authoring constraints

## 1. Renderer boundary

Let the system HTML-report workflow own:

- project scaffold and entry file;
- runtime assets and font availability;
- HTML, CSS, JavaScript, ECharts/Mermaid setup;
- accessibility and responsive behavior.

Follow its current requirements even when an older procurement reference differs. Preserve its required source-only header/comment and directory contract.

This package owns only:

- procurement report story;
- selection of a visual direction and composition;
- procurement-specific chart and decision grammar;
- an explicit-request-only generated header-image workflow;
- optional package-native SVG style references, icons, and patterns.

Keep visual-direction names, reference filenames, selection notes, prompts, and briefs internal. Never render `Selected signal S05`, a selected-style/direction/template label, or any authoring code in the final HTML.

Copy only actually used support assets and, when explicitly requested, the newly generated header raster into the report-local directory. Never link to this skill by an absolute path from the delivered report.

## 2. Architecture handoff

Choose one mode.

| Mode | Use | Default length | Core emphasis |
|---|---|---:|---|
| Approval memo | supplier award, sourcing project, budget, pilot, lane approval | 6–10 sections | verdict, alternatives, budget, gates |
| Analytical review | price, supplier, category, recurring performance | 7–12 sections | baseline, change, causes, exposure, actions |
| Exception control | inventory, late supply, CAPA, disruption | 5–8 sections | prioritized queue, timing, owners, triggers |

Read `procurement-report-architecture.md` and choose one architecture family, one opening, three to six body patterns, and one execution close. Use its architecture fingerprint and variation rules to prevent the recurring `hero → KPI cards → two charts → recommendations` structure.

Keep the mode and architecture separate:

- mode controls the report's depth and approval purpose;
- architecture controls reading order, geometry, density, and navigation;
- visual direction controls color, type, surfaces, and graphic character;
- chart/interaction selection controls how the user explores evidence.

Do not call architecture families templates in the report. Treat them as authoring briefs.

## 3. Optional generated header image

Do not generate a header image by default. Generate one only when the user explicitly requests a 头图, header image, hero image, or equivalent top visual. A polished-report request or supplied style reference is not enough. When requested, generate it after the HTML/CSS draft exists and read `header-image-workflow.md`.

### Header contract

- Be the first visible report block.
- Match the exact width of the report shell.
- Stay shallow: approximately 3.2:1 on desktop and 2:1 on mobile.
- Use a newly generated raster; never use a packaged illustration as the final header.
- Match the report's primary and signal colors.
- Reflect the decision object: narrowing suppliers, price movement, supplier resilience, stock flow, route/landed cost, or a mixed decision.
- Keep the art text-free; place live report title, scope, as-of date, and decision posture in HTML after the image or in tested negative space.
- Keep important forms within the central 70% for responsive cropping.
- Provide descriptive alt text that names the analytical metaphor, not “decorative image.”
- Use the hard horizontal rule transition by default; use color carry, gradient, or a diagonal only when the report draft already supports it.

### First content after the header

Show only:

- semantic report title;
- one-line decision question;
- scope and as-of date;
- approval posture or status label;
- optional one-sentence verdict teaser.

Do not place a wall of KPI cards over the image. Do not place methodology, table of contents, or more than two badges above the fold.

### Title wrapping

Break the largest title by meaning, not by fixed character count. Use two or three lines with deliberate contrast:

`AI Token 供应商`  
`寻源与预算决策`

Avoid widows, single punctuation, and one oversized English word beside tiny Chinese copy.

## 4. Visual directions

Read `procurement-editorial-system.md` before selecting colors, type, spacing, or object geometry. Keep all neutral roles within one ink-derived family. Map procurement roles onto the built-in renderer variables: `--bg`, `--bg2`, `--ink`, `--muted`, `--rule`, `--accent`, and `--accent2`. Do not introduce a parallel `--main` / `--signal` palette in the final report.

Preview paths in this reference are relative to `assets/procurement-visual-kit/`.

Read `procurement-style-routing.md` and use its selector. All six routes are equally eligible unless the user explicitly chooses a direction.

| Direction | Background / surface | Ink | Primary | Auxiliary | Optional pop | Corners | Preview / kit |
|---|---|---|---|---|---|---|---|
| Precision Ledger | `#FFFFFF` / `#F7F8FA` | `#172033` | `#2856A3` | none | `#C44D32` | `0–4px` | `02-cobalt-forge-preview.svg` / `precision-ledger.svg` |
| Product Stage | `#FFFFFF` / `#F5F7FC` | `#162033` | `#2B63E8` | none | none | `12–20px` named objects | `07-cerulean-cocoa-preview.svg` / `product-stage.svg` |
| Signal Docket | `#FFFFFF` / `#F8F6F5` | `#201918` | `#A23A2B` | none | `#D39B36` | `0–3px` | `09-vermilion-docket-preview.svg` / `signal-docket.svg` |
| Mono Audit | `#FFFFFF` / `#F4F4F4` | `#111111` | none | none | none | `0px` | `08-mono-grid-preview.svg` / `mono-audit.svg` |
| Acid Registry | `#FFFFFF` / `#F4F4F6` | `#111111` | `#D6F52A` | none | none | `8–14px` | `10-acid-registry-preview.svg` / `acid-registry.svg` |
| Night Circuit | `#111315` / `#16302B` | `#F6F7F8` | `#20C7E8` | emerald surface | `#F2E923` | `8–16px` | `11-night-circuit-preview.svg` / `night-circuit.svg` |

Do not replace the selected route with Precision Ledger, Product Stage, or any familiar palette. Do not combine two route identities. A procurement topic does not imply a route.

These direction names are authoring shorthand only. Translate the chosen direction into the renderer's visual-personality, layout, component, and palette plan fields; never print the direction name or preview cue in the report.

For every direction, use one muted ink tone and low-opacity structural rules. Prefer deliberate open space over extra surfaces. Do not introduce unrelated gray, gray-blue, gray-green, or gray-purple values outside the selected route.

This package intentionally provides no cream or beige-background report system. Use pure white for five routes, including Acid Registry. Keep the near-black field only for Night Circuit; do not silently normalize that route back to white.

### Hard color budget

- Use no more than three chromatic hues across the full page: one primary, one auxiliary, and one optional pop color. White/background roles and a single ink-derived neutral family may serve as background, ink, muted text, rules, and quiet surfaces; they are not permission to introduce extra chromatic gray-blue, gray-green, or gray-purple families.
- Declare `background`, `ink`, `main`, and optional `signal` before rendering.
- Count every gray, tint, border, chart mark, badge, callout, diagram, table highlight, tooltip, and header color.
- Keep the signal color below roughly 8% of the visible page and reserve it for a failed gate, material exception, or reversal trigger.
- Build chart series from ink opacity, main-color opacity, line styles, markers, direct labels, and fill/outline before adding another hue.
- Do not assign a separate color to every evidence token or status. Use text labels, symbols, fill/outline, or patterns.
- Do not use a multicolor gradient, rainbow scale, or decorative spectrum.
- If a requested generated header introduces a competing hue, regenerate or neutralize it before insertion.

### Surface and foreground pairing

Every dark or chromatic surface must explicitly define its foreground. Never inherit the page's dark ink into a dark component.

| Surface | Required text | Muted text | Rule/border |
|---|---|---|---|
| light neutral | dark ink with contrast ≥ 4.5:1 | darker neutral gray with contrast ≥ 4.5:1 | neutral or declared main color |
| dark neutral | `#F7F8FA` or equivalent light ink | no darker than approximately `#B5BEC9` | light neutral or declared main color |
| saturated main color | tested `on-main` light or dark pair | tonal pair that still meets contrast | tonal variant |
| signal color | use only for short labels/marks with tested `on-signal` pair | avoid paragraphs | same hue or neutral |

Treat every callout, table header, footer, badge, evidence tag, chart tooltip, and generated-image overlay as a separate surface. On dark reports, body copy, secondary copy, citations, labels, and inactive table text must all remain visibly light.

### Color semantics

- Use ink/neutral for observed baseline.
- Use `main` for the recommended path, selected option, and primary series.
- Use `signal` for adverse exposure, failed gate, or decision trigger.
- Use tints only for grouping; keep text dark enough.
- Label status with words or symbols; never rely on red/green alone.

## 5. Type, spacing, and anti-patterns

Follow `procurement-editorial-system.md`. Use its five-level type hierarchy, `400/600/700` weight roles, visible-text budget, open-stage/dense-field rhythm, semantic title-line rules, color budget, and direction-specific corner table. Express these choices in the built-in renderer plan; never copy a procurement root-token stylesheet.

Build contrast through scale, whitespace, alignment, and one main color. Keep large text short. Do not solve hierarchy by adding more grays, arbitrary weights, or colored panels.

### No colored edge bands

Apply the pre-authoring invariant at the top of this reference. Never attach a chromatic accent band to the top, bottom, left, or right edge of a card, sidebar, header, topbar, navigation item, callout, recommendation, finding, section, table wrapper, or page frame. This includes:

- an accent `border-top`, `border-bottom`, `border-left`, or `border-right`;
- an accent logical border such as `border-inline-start` or `border-block-start`;
- a colored pseudo-element anchored to any edge;
- a narrow filled rectangle, rail, or strip running along an edge;
- an inset shadow that imitates an accent border;
- a gradient edge band or continuous colored gutter;
- a background image, SVG, mask, or nested child that imitates an edge band;
- a stripe that visually merges with a component border.

Use one of these instead:

- a full-surface flat fill with a tested foreground pair;
- a compact inline status mark;
- a short underline or symbol near the label that remains separated from every frame edge;
- a standalone chart mark or direct label;
- type scale and whitespace only.

Neutral structural hairlines, table grid borders, and standalone report-level dividers may remain when necessary. They must be neutral, thin, and structural—not chromatic accent bands attached to a frame.

Avoid:

- endless rounded cards;
- soft pastel dashboards without a focal decision;
- cream, ivory, parchment, or yellow-beige page backgrounds;
- gradient blobs, glassmorphism, glow, or floating capsules used as filler; one bounded floating layer is allowed in Product Stage when it carries an interactive object;
- a uniform three-column grid repeated down the page;
- decorative robot, handshake, factory, truck, coin, or globe clip art;
- five or more accent colors;
- more than two type families;
- icons beside every heading;
- radar charts with hidden scales or more than six dimensions;
- unlabelled gauge/donut charts without a target and interaction;
- fake precision and chart junk;
- generic “insight / challenge / opportunity” cards disconnected from a decision;
- large empty areas that do not establish hierarchy or meaning.
- colored vertical accent rails on any side of a component;
- dark or mid-gray text on a dark surface;
- more than one main color plus one signal color.
- more than two visible prose paragraphs in sequence;
- an HTML report whose major sections could be copied to Markdown without losing structure or behavior.

## 6. Procurement chart grammar

Read `procurement-chart-interaction-catalog.md` for the full selection matrix and scene recipes. Prefer charts that expose commercial basis, thresholds, uncertainty, and decision reversal.

### Sourcing and quotes

- **quote ladder** — normalized unit or total cost, with inclusions and uncertainty;
- **gate matrix** — pass/fail/condition/unknown before scoring;
- **scenario table** — demand, tier, FX, usage, or term;
- **TCO bridge** — quoted price to landed/lifecycle cost;
- **award frontier** — economics against capability/resilience with gates overlaid.

### Price

- **weighted price line with quantity band**;
- **indexed small multiples** for different items;
- **supplier/basis bridge** for mix and explainable change;
- **price distribution or box plot** only after comparability;
- **contract-versus-benchmark lag** with source dates.

### Supplier

- **performance strip** with target and denominator;
- **gate matrix**;
- **capacity requirement/headroom bars**;
- **allocation/concentration map**;
- **risk bow-tie or failure path** when causal controls matter.

Use a radar chart only for at most three finalists and three to six normalized dimensions with visible scales, raw-value hover detail, click selection, and a comparison-table fallback. Keep gates separate.

### Inventory

- **time-phased projected inventory** with reorder receipt and stockout threshold;
- **exception horizon** sorted by first exposure date;
- **coverage/value quadrant** with action labels;
- **supply-demand bridge**;
- **open-PO critical path**.

### Logistics

- **landed-cost bridge** by lane;
- **cost-time frontier** with compliance gates;
- **route strip** from origin to destination;
- **container fill schematic** for binding weight/volume;
- **schedule and disruption window**.

### Chart rules

- Put unit, currency, tax/Incoterm basis, period, and as-of date near the title.
- Show the baseline and decision threshold.
- Annotate the one or two changes that drive the decision.
- Use direct labels when feasible.
- Keep one message per chart.
- Explain exclusions and unmatched residuals.

## 7. Evidence and decision grammar

Use a compact evidence token:

- `OBS` observed;
- `SRC` sourced;
- `DRV` derived;
- `ASM` assumed;
- `UNK` unknown.

Pair the token with source/date or calculation basis where the conclusion appears. Do not hide evidence only in the appendix.

Use this decision language:

- **approve** — gates passed, action ready;
- **conditional** — action allowed only after named conditions;
- **pilot** — uncertainty requires bounded evaluation;
- **defer** — missing evidence or timing dominates;
- **reject** — mandatory gate fails or economics/resilience is unacceptable.

For each recommendation band, display:

`action · owner · timing · gate · fallback · verification`

## 8. Interaction

Keep interaction subordinate to the report. Use one primary interaction grammar and at most three linked interactive objects in a standard report. Require each interaction to answer a named procurement question.

Available patterns include:

- scroll-snap supplier, lane, scenario, or exception shelf with visible controls;
- hover/focus/click switch card that keeps the decision visible on both faces;
- scenario tabs for tax, FX, demand, allocation, term, or Incoterm;
- master/detail comparison for a long shortlist or exception queue;
- native expandable evidence;
- linked highlighting across charts, tables, and text;
- bounded range controls with baseline, units, Reset, and Recommended actions.
- polished question-help popovers for basis, terminology, or formulas that would otherwise add visible prose.

Read `procurement-report-interactions.md` and copy the packaged CSS/JS only when the chosen interaction needs it. Keep the static default decisive, support keyboard and touch, and expose essential hidden content in print.

## 9. Packaged style references

| Asset | Reference cue | Suggested system |
|---|---|---|
| `illustrations/quote-bridge.svg` | normalized quote to total-cost buildup | Precision Ledger |
| `icons/procurement-icons.svg` | optional sprite for gate, quote, supplier, stock, route, evidence | any |
| `patterns/ledger-grid.svg` | low-opacity data/evidence field | Precision Ledger or Mono Audit |
| `style-previews/*.svg` | six original full-page direction previews; never use inside a finished report | corresponding route |
| `style-kits/*.svg` | six matched marker, pattern, focus-field, and chart-mark kits | corresponding route only |
| `../procurement-dynamic-ui/companions/*.svg` | six compact composition plates, each with six procurement layout panels | Dynamic UI planning only; never embed or copy into a widget |
| `../procurement-dynamic-ui/dynamic-ui-layouts.json` | layout-family to analysis/scene/template compatibility and route transforms | Dynamic UI planning only |

Treat a packaged illustration only as an optional composition or mood reference when the user explicitly requests a generated header or another original image. Do not insert it unchanged or require exact recreation. Use a pattern only once or twice at low opacity. Use the icon sprite only when icons carry repeated semantic meaning.

## 10. Original visual-direction prompt

Write a scene-specific prompt from principles rather than copying a style reference. Keep the prompt inside the production brief; never expose it in the final report.

```text
Design a procurement decision experience for [decision object] and [decision owner].

Composition:
- use [architecture family] with [opening pattern];
- make [dominant procurement object] the visual center;
- alternate [open stage] with [dense evidence field];
- translate comparison, thresholds, time, flow, and actions into interactive visual objects;
- keep visible prose sparse and decision-shaped.

Visual direction:
- [Precision Ledger / Product Stage / Signal Docket / Mono Audit / Acid Registry / Night Circuit];
- selected route field, [ink], one [primary], optional [auxiliary], and optional [pop] only for a stable semantic role;
- five type levels, short semantic headline lines, 400/600/rare 700 weights;
- [hard / lightly rounded / premium rounded] geometry with one declared elevation rule;
- no cream background, decorative gradients, filler cards, colored edge bands, or unrelated gray values.

Data experience:
- one dominant chart and no more than two supporting chart types;
- interactive cards or tables for [named entities];
- Level 0 system reliability for every chart, Level 1 direct decision annotation for the dominant chart, and Level 2 linked selection only when it changes another decision view;
- show units, basis, thresholds, evidence state, and print/no-JS fallback.

Quality:
- every character earns its place;
- large type carries little text;
- semantic units never split across lines;
- the result should feel authored for this procurement decision, not like a generic dashboard or a styled Markdown article.
```

Borrow at most two cues from any supplied reference, such as strict grid, floating named objects, bold block contrast, cropped evidence, or oversized ranking. Record those cues in the brief and translate them into procurement meaning. Never reproduce distinctive copy, exact color sequences, component arrangements, or branded motifs.

## 11. Procurement Visual Brief

Use this internal shape to populate the consolidated `Procurement Enhancement Brief` in `html-report-enhancement-contract.md`. Do not emit this heading or its field names in the report:

```markdown
## Procurement Visual Brief
- Decision object:
- Audience:
- Report mode:
- Architecture family:
- Opening pattern:
- Visual direction:
- Route ID and matched preview / kit:
- Borrowed cues and procurement translation:
- Header requested by user: yes / no
- If yes, header style lane:
- If yes, header decision metaphor and alt text:
- If yes, source-derived Header Style Snapshot:
- If yes, optional reference and the one cue to borrow:
- If yes, header aspect ratio, safe area, and bottom transition:
- Renderer token mapping for background / surface / ink / muted / rule / accent / accent2:
- Dynamic UI identity handoff: exact tokens / corners / depth / state vocabulary / selected entity key:
- Dynamic UI companion / numbered panel / route-specific composition transform:
- Ink-derived muted / structural rule formulas:
- Type scale / weight roles / spacing rhythm:
- Object radius and card-free sections:
- Dark-surface and chromatic-surface foreground pairs:
- Confirmation that colored edge bands are prohibited on all frame sides:
- Edge-treatment invariant: no physical/logical single-side border, pseudo-element, nested rail, inset shadow, narrow gradient, background image, mask, or SVG edge strip:
- Permitted emphasis grammar and required inset separation:
- Title semantic breaks:
- Verdict posture:
- Primary chart:
- Primary chart enhancement level:
- Secondary chart or diagram:
- Secondary chart enhancement level:
- Architecture fingerprint:
- Comparison basis to display:
- Evidence tokens:
- Decision-reversal variable and signal-color use:
- Interaction, if any:
- If requested, final generated raster to copy:
- Other asset files to copy:
```

Keep the rationale to one sentence if the runtime requires planning notes.

Add `Suppress from output: selected-signal/style/direction/template labels, direction codes, brief headings, reference filenames, prompts, renderer/tool/model notes`.

## 12. Pre-authoring constraints

Resolve these constraints in the production brief before writing the final HTML:

- use no more than five visible type levels and the declared weight roles;
- include currency, unit, period, tax, Incoterm, and as-of basis where relevant;
- keep gates separate from weighted scores and include the baseline, largest uncertainty, and reversal variable;
- use no physical or logical one-sided colored border, edge-anchored pseudo-element, nested rail, inset shadow, narrow gradient, background image, mask, or SVG edge strip on a card, sidebar, header, topbar, navigation item, callout, finding, recommendation, section, table wrapper, or page frame;
- declare readable foregrounds for every dark or chromatic surface;
- use one ink-derived neutral family and no more than three chromatic hues;
- use the selected architecture, spacing rhythm, geometry, chart levels, fallbacks, and interaction scope;
- suppress authoring labels, route names, prompts, reference filenames, tool names, and model names.

After the final HTML and report-local assets are written, perform no inspection, validation, linting, rendering, or runtime check. Do not invoke the built-in HTML checker, `node --check`, a local server, a browser, screenshots, or an HTML runtime preview.
