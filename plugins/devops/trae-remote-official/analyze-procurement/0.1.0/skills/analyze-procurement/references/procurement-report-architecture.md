# Procurement report architecture catalog

Use this reference after the decision spine is stable and before choosing components. Build a report from a scene-specific architecture, not from a default dashboard grid.

## Contents

1. Assembly rule
2. Anti-document translation
3. Architecture families
4. Opening patterns
5. Section and object patterns
6. Summary and decision surfaces
7. Scene routing
8. Variation rules
9. Responsive behavior
10. Architecture brief
11. Acceptance

## 1. Assembly rule

Build each report from:

`one architecture family + one opening + one navigation model + three to six body patterns + one execution close`

The decision controls the structure. Do not select components first and pour content into them.

Before choosing a family, classify the material:

`compare · rank · threshold · change · flow · concentration · uncertainty · action · evidence`

Translate each class into a visual object before drafting prose. A section that starts as several paragraphs should be redesigned until its primary object is clear.

Before authoring, write a compact architecture fingerprint:

```text
family / opening / dominant visual / navigation / interaction / density / closing
```

Example:

```text
negotiation room / verdict rail / quote ladder / sticky sections / scenario tabs / dense / concession gates
```

Do not reuse the same fingerprint for materially different procurement scenes. Within one report:

- do not repeat the same card count in consecutive sections;
- do not use the same column ratio more than twice;
- use at least three scales in reports longer than six sections;
- allow at most one KPI-style summary cluster;
- keep at least one major section card-free;
- make the dominant visual occupy more area than its supporting commentary.

At the same pre-authoring stage, lock the surface grammar: no card, callout, recommendation, finding, KPI, evidence object, figure, table wrapper, navigation object, section frame, or page frame may use a chromatic strip on only one edge. Do not express emphasis with a physical or logical one-sided border, an edge pseudo-element, a narrow nested rail, an inset shadow, a narrow gradient, a background image, mask, or SVG edge strip. This is part of composition selection, not a post-generation check.

After selecting the family, read `procurement-curatorial-framework.md`. Turn the architecture into a visitor route and numbered chapter score before selecting cards. Reports longer than six major sections require a contents plate, sticky chapter rail, horizontal chapter strip, or hybrid orientation.

## 2. Anti-document translation

HTML must not read like a Markdown article with cards around it.

Use this conversion ladder:

| Raw material | Default HTML expression |
|---|---|
| several peer facts | aligned comparison object or enhanced table |
| one conclusion with conditions | decision stage plus compact gate object |
| repeated supplier descriptions | interactive option shelf or master/detail |
| chronological explanation | time strip with a pinned event detail |
| calculation narrative | bridge, formula rail, or expandable calculation ledger |
| risks and controls | gate matrix, bow-tie, or linked failure path |
| alternative scenarios | scenario switcher with consequence view |
| action list | owner/timing/trigger execution register |
| definitions or evidence notes | question-help popover, details drawer, or appendix ledger |

Draft each major section as:

`short finding → primary object → one or two decision annotations → optional evidence detail`

In rendered HTML, mark each major section with:

```html
<section data-primary-object="gate-matrix" data-density="dense">...</section>
```

Use only `open`, `dense`, or `transitional` for `data-density`.

Do not draft:

`heading → three paragraphs → generic summary cards`

At most one major section may be led by prose. Even that section must contain a visual anchor such as a quote, number, image, calculation, or evidence object.

Use large text, cards, tables, charts, and controls as different materials:

- large type creates a pause and must remain short;
- cards isolate named objects and should not become paragraph containers;
- tables organize exact comparisons and may be interactive;
- charts reveal relationships, thresholds, or change;
- controls change a decision view, not merely decorate it.

## 3. Architecture families

Choose one primary family. A long report may borrow one pattern from a second family without becoming a hybrid dashboard.

### A. Executive docket

Use for award, budget, pilot, or policy approval.

```text
decision stamp
→ one-sentence verdict and exposure
→ option ledger
→ economics bridge
→ knockout gates
→ approval conditions
→ owner/timing/fallback
```

Use a narrow decision rail beside a wide evidence field. Keep methodology after the decision.

### B. Competitive decision room

Use for RFx, quote normalization, shortlist, or allocation.

```text
shortlist headline
→ full-width comparison stage
→ hover/focus option detail
→ gate matrix
→ award frontier
→ allocation scenarios
→ negotiation queue
```

Let named options, not generic KPIs, anchor the page.

### C. Price investigation notebook

Use for price reasonableness, PPV, benchmark, or should-cost.

```text
price question and basis
→ weighted trend
→ annotated change points
→ cost-driver bridge
→ supplier/mix decomposition
→ decision range
→ negotiation triggers
```

Use margin notes, calculation callouts, and evidence footnotes. Avoid a wall of summary cards.

### D. Supplier portfolio atlas

Use for supplier performance, capacity, concentration, and risk.

```text
portfolio map
→ filterable supplier strip
→ performance small multiples
→ dependency or concentration view
→ failure paths and controls
→ action tiers
→ next review
```

Show the portfolio before opening individual suppliers. Keep knockout gates outside weighted scores.

### E. Exception command queue

Use for inventory exposure, late supply, CAPA, or disruption.

```text
time-to-impact horizon
→ horizontally scrollable exception queue
→ selected exception detail
→ supply-demand or critical-path visual
→ action/owner/trigger table
→ unresolved evidence
```

Sort by decision urgency or first exposure date, not by arbitrary category.

### F. Route and landed-cost book

Use for international logistics, route choice, Incoterm, or container decisions.

```text
origin-to-destination route strip
→ cost-time frontier
→ landed-cost bridge by lane
→ handoff and compliance gates
→ disruption scenarios
→ booking decision
```

Use spatial or sequential sections. A map is optional and must add information.

### G. Negotiation room

Use for negotiation preparation, bid leveling, or contract renewal.

```text
target / walk-away / BATNA
→ quote ladder
→ concession exchange table
→ scenario switcher
→ supplier-specific argument cards
→ sequence and approval limits
```

Use interactive scenario switching only when the static default still shows the recommended position.

### H. Audit dossier

Use for governance, traceability, or print-heavy review.

```text
decision register
→ basis and scope
→ reconciliation ledger
→ finding/evidence pairs
→ exceptions
→ approvals and signatures
→ source appendix
```

Use a monochrome or low-chroma system, strict headings, visible identifiers, and expandable evidence on screen with fully expanded print output.

## 4. Opening patterns

Choose one. Do not automatically open with four equal metric cards.

| Opening | Shape | Best use |
|---|---|---|
| Decision stamp | large verdict, one exposure number, compact conditions | approval |
| Split thesis | 60/40 recommendation and decisive evidence | executive review |
| Comparison masthead | two to five named options on one plane | award or lane choice |
| Time-to-impact horizon | dates and exposure windows | inventory/disruption |
| Price tape | current, baseline, variance, and basis on one horizontal line | price |
| Route strip | origin, handoffs, destination, time, cost, gates | logistics |
| Evidence ledger | fact/derived/assumed/unknown counts plus binding gap | audit-heavy work |
| Contents plate | ruled, clickable numbered chapter map plus one reading thesis | reports with 5–9 chapters |
| Question-led opening | explicit decision question followed by a short answer | ambiguous or investigative work |

When summary metrics are useful, vary their geometry:

- inline metric sentence;
- one large anchor number with three annotations;
- horizontal tape with separators;
- ranked metric list;
- stacked baseline/current/threshold;
- scroll-snap option shelf;
- compact two-row decision ledger.

Do not follow the opening with another sparse summary section. Move from the opening into a dense decision object, comparison field, or timeline.

## 5. Section and object patterns

Make analytical objects dominant and use prose as connective tissue.

### Heading patterns

- **Numbered chapter** — large section number and short title for long reports.
- **Question heading** — use when the section resolves one decision uncertainty.
- **Finding heading** — state the conclusion, then support it below.
- **Label + title** — compact eyebrow for evidence state or workstream, followed by a plain title.
- **Timeline heading** — date/window on the left and event or gate on the right.
- **Margin heading** — narrow sticky label beside dense analytical content.
- **Contents heading** — oversized `目录 / Contents` title beside a ruled chapter index.

Do not decorate every heading with an icon, pill, gradient, or colored rail.

### Short-text patterns

- **Editorial lead** — one sentence or one compact paragraph before the dominant visual.
- **Finding/evidence pair** — conclusion in the wide column, evidence and basis in a narrow column.
- **Claim/counterweight** — recommendation beside the strongest reason it could reverse.
- **Annotated steps** — short paragraphs aligned to stages in a chart or route.
- **Decision notes** — compact numbered observations after a chart, limited to the few that change action.
- **Margin evidence** — source, date, unit, and caveat beside the relevant paragraph.
- **Progressive detail** — concise visible summary with native `<details>` for formulas or row-level evidence.

Keep paragraphs readable and rare. Prefer 30–70 Chinese characters per paragraph; redesign when a paragraph contains more than one finding. Do not place more than two paragraphs together.

### Body patterns

Use these as building blocks:

- clickable contents plate with stable chapter anchors;
- sticky chapter rail or horizontal chapter strip;
- full-width dominant chart with direct annotations;
- asymmetric 2/3 + 1/3 evidence split;
- sticky decision rail beside scrolling evidence;
- horizontally scrollable option or exception shelf;
- comparison table with a pinned identifier column;
- timeline band with expanded selected stage;
- small-multiple strip;
- scenario tabs with one chart and one consequence table;
- decision tree or failure path;
- before/after or baseline/proposal toggle;
- compact action register;
- source appendix with anchors.

### Density compositions

Choose a section-level composition instead of repeating generic columns:

- **stage → ledger** — one open verdict or number followed by a dense exact comparison;
- **ledger → aperture** — dense evidence resolves into one isolated recommendation;
- **filmstrip → detail** — peer options move horizontally while one detail field stays fixed;
- **timeline → pinned evidence** — a continuous time axis controls a compact evidence panel;
- **matrix → exception drawer** — dense gate state opens only the selected exception;
- **split tension** — recommendation and reversal variable occupy unequal opposing fields;
- **full-bleed object → margin notes** — one dominant visual carries direct annotations at the edge;
- **stacked ranks** — oversized rank/value fields align vertically without becoming KPI cards.

Do not reuse a composition in consecutive sections. Alternate one or two open stages with dense fields so the report has a designed cadence.

## 6. Summary and decision surfaces

Every bounded surface must represent a real object.

Use cards for:

- one supplier or lane;
- one scenario;
- one exception;
- one gate;
- one action with owner and timing;
- one evidence bundle.

Do not use cards merely to hold ordinary paragraphs.

Every bounded surface follows one complete edge treatment:

- no border;
- one neutral structural border applied consistently to the whole frame;
- one full-surface flat fill with a tested foreground.

Never combine a quiet fill with a chromatic rail on one side. Place any badge, dot, symbol, or underline inside the content padding with visible separation from every frame edge. Use type, spacing, alignment, or whole-surface reversal for emphasis.

Available surface behaviors:

- **Static decision card** — recommendation, exposure, gate, fallback.
- **Flip-on-focus comparison** — default shows result; hover/focus/click reveals basis. Never hide the result on the back.
- **Scroll-snap shelf** — 3–8 peer options or exceptions with visible previous/next controls.
- **Master/detail** — compact list controls one stable detail surface.
- **Progressive evidence** — native `<details>` with a count and evidence state in the summary.
- **Linked highlight** — hovering or focusing a supplier highlights the same supplier across table, chart, and notes.
- **Help popover** — a compact question trigger explains a term, basis, or formula without adding visible prose.

Use the bundled runtime only for these small behaviors. Read `procurement-report-interactions.md` before copying it.

## 7. Scene routing

| Primary scene | Preferred families | Dominant opening | Body emphasis |
|---|---|---|---|
| Supplier discovery / RFx | Competitive decision room, Negotiation room | comparison masthead | option shelf, gate matrix, award frontier |
| Price / cost | Price investigation notebook, Executive docket | price tape | trend, bridge, decomposition, target range |
| Supplier performance / risk | Supplier portfolio atlas, Audit dossier | portfolio map | small multiples, dependency, failure controls |
| Inventory / replenishment | Exception command queue | time-to-impact horizon | exception shelf, projected inventory, action register |
| Logistics / landed cost | Route and landed-cost book | route strip | frontier, landed bridge, handoff gates |
| Mixed approval | Executive docket | decision stamp | one supporting pattern from the binding route |

## 8. Variation rules

Vary the report without sacrificing procurement semantics:

1. Pick the family from the decision, not randomly.
2. Pick a different opening when two families could serve the same scene.
3. Choose one dominant visual; subordinate all other charts.
4. Choose one primary interaction grammar and at most three linked interactive objects that answer named questions.
5. Choose a density lane: executive sparse, analytical mixed, or operational dense.
6. Close with action, owner, timing, gate, fallback, and verification.

Avoid these fingerprints unless the user asks for a classic dashboard:

- hero → four KPI cards → two charts → three cards → table;
- title → summary card grid → radar → funnel → recommendations;
- every section as `h2 + three rounded cards`;
- identical two-column sections repeated down the page;
- chart carousel that hides all charts by default.
- long-form article rhythm where each section is heading plus prose.
- large decorative typography carrying operational detail.

## 9. Responsive behavior

- At `>= 1100px`, allow sticky rails, master/detail, and asymmetric grids.
- At `720–1099px`, collapse sticky rails into top summaries and preserve horizontal shelves.
- Below `720px`, stack reading order, keep scroll-snap shelves, pin the first table column only when it does not obscure data, and provide 44px controls.
- Collapse a sticky chapter rail into a horizontally scrollable chapter strip below `1100px`; keep the active chapter visible and preserve deep links.
- Never make hover the only path to hidden content.
- In print, expand all essential evidence, remove carousel clipping, show the selected/default scenario plus a compact scenario table, and suppress purely navigational controls.

## 10. Architecture brief

Pass this with the visual brief:

```markdown
## Procurement Architecture Brief
- Decision question:
- Architecture family:
- Opening pattern:
- Dominant visual:
- Supporting body patterns:
- Summary geometry:
- Heading pattern:
- Primary visual object for every major section:
- Open stages and dense fields:
- Short-text pattern:
- Navigation model:
- Numbered chapter score:
- Card-free chapters:
- Continuity anchors:
- Structural variables allowed to change:
- Interaction 1 and question answered:
- Interaction 2 and question answered:
- Density lane:
- Mobile collapse:
- Print fallback:
- Architecture fingerprint:
- Edge treatment: no physical/logical single-side accent, edge pseudo-element, nested rail, inset shadow, narrow gradient, background image, mask, or SVG strip
- Permitted emphasis grammar and inset separation:
```

## 11. Acceptance

Resolve these commitments before generating HTML. Do not use this section as a post-generation inspection step:

1. The first viewport states the decision or the question being resolved.
2. The report has one dominant visual, not a grid of equal charts.
3. At least one major section is not enclosed in cards.
4. Consecutive sections do not repeat the same geometry.
5. Every card boundary represents a supplier, lane, scenario, exception, gate, action, or evidence bundle.
6. Every interaction answers a named procurement question and has a visible static default.
7. The executive verdict and knockout gates remain visible without interaction.
8. The mobile order follows the decision logic.
9. Print output exposes essential hidden detail.
10. The closing block contains action, owner, timing, gate, fallback, and verification.
11. No more than one major section is prose-led.
12. No more than two prose paragraphs appear consecutively.
13. Every major section declares a primary object and a density mode.
14. The report alternates open stages and dense evidence rather than repeating uniform sections.
15. Converting the report to Markdown would remove real comparison, interaction, or visual reasoning capability.
16. Reports longer than six major sections provide visible chapter navigation with stable anchors.
17. Every navigable major section has a stable `id`.
18. Standard 6–8 chapter reports keep at least two chapters card-free.
19. Adjacent chapters change no more than two structural variables while retaining at least three continuity anchors.
20. Every bounded surface uses no border, a complete neutral border, or a full-surface fill—never a one-sided chromatic rail.
21. Compact color marks remain inset from all frame edges, and no edge effect is reconstructed with a pseudo-element, nested child, shadow, gradient, mask, background, or SVG.
