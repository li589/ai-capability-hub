# Market Radar visual contract

## Contents

1. Ownership and enforcement
2. Information restraint
3. Framework and whitespace
4. Typography
5. Spacing and density
6. Color budget
7. Geometry and depth
8. Data visualization and interaction
9. Tooltip and help behavior
10. Reference transfer
11. Shared HTML and Dynamic UI identity
12. Verification

## 1. Ownership and enforcement

This package owns the intelligence-specific visible information architecture. The current
`html-report` runtime owns the report engine: scaffold, canonical variables, offline libraries,
local fonts, responsive plumbing, citations, accessibility, print, and base validation. Follow
`html-report-integration.md`; preserve that foundation and replace only sample content or generic
composition that does not express the stabilized evidence.

Before rendering:

1. stabilize evidence;
2. run `scripts/select_visual_style.py` once and accept its framework, blueprint, and asset without
   filtering or rerolling;
3. write one Radar Style Contract;
4. set type, spacing, color, geometry, and interaction budgets;
5. generate HTML, then Dynamic UI from the same contract.

After authoring, check files and JavaScript syntax, then run `scripts/report_visual_audit.py`
against the HTML and local chart script. Treat audit failures as incomplete work. Do not invoke a
built-in HTML validator, start a local server, open a browser, use browser automation, or capture
screenshots.

## 2. Information restraint

Every visible character must earn its place.

- Delete navigation, labels, descriptions, and buttons that do not change interpretation or action.
- Prefer exact nouns and verbs over conversational filler.
- Convert repeated analytical fields into tables, delta lanes, action rails, or cards; do not retain
  Markdown paragraph structure inside HTML.
- Do not repeat the same conclusion in the title, summary, chart subtitle, card, and action rail.
- A display title states one conclusion; its support line contains the qualifier or consequence.
- Do not place source methodology, caveats, and definitions inside the hero. Put them beside the
  relevant evidence or behind an accessible help control.
- Button labels are short verb-object phrases. Avoid vague labels such as `Learn more`, `Explore`,
  `Discover`, or ornamental calls to action.
- Do not pad a layout with extra signals, metrics, cards, quotations, illustrations, or captions.
- Apply `signal-visual-encoding.md` text budgets to every multi-signal report.
- Unknown, checked/no-change, and not-applicable are distinct states and remain visible.
- Never invent values, dates, scores, entities, sources, or product imagery.

## 3. Framework and whitespace

Framework is the report's reading architecture, not a decorative shell. Use the framework assigned
by the random style router and `curatorial-framework.md` for implementation. Do not select it from
report length or evidence shape.

- A contents page is a threshold, not a wall of navigation cards. Use large chapter numbers,
  concise titles, one-line promises, and generous blank field.
- A side rail is a locator, not application chrome. It contains only chapter number, short title,
  active state, and an optional compact progress cue.
- Place a chapter title before the object it governs. Keep it optically attached to the first chart,
  matrix, or argument block, never stranded midway between two sections.
- Give the primary chart enough uninterrupted width to become an exhibit. Put interpretation beside
  or directly below it; never alternate unrelated text and charts in equal little boxes.
- Use asymmetry to signal importance. One large field plus two small supporting fields is preferable
  to three equal cards when the evidence is not equal.
- Leave intentional empty cells in a grid when they create hierarchy. Never fill them with weak
  metrics, decoration, or duplicate explanation.

## 4. Typography

### Families

Use at most:

- one Chinese family;
- one Latin family;
- one optional display family used only once.

Follow a verified product system when available. Otherwise inherit the runtime's local typography
and record `runtime typography`. Do not name or import a fashionable default without a product
reason.

### Size roles

Use three roles by default and four only when metadata genuinely needs separation:

| Role | Desktop range | Use |
|---|---:|---|
| display | `48–72px` | one short verdict only |
| section | `24–30px` | H2 and major figure |
| body | `15–18px` | paragraphs, H3, table cells |
| meta | `12–14px` | sources, dates, units, compact labels |

Use `clamp()` for responsive display and section type without creating new semantic roles. H3 shares
the body size. A large numeric value uses the display or section role; it does not create another
size.

### Display-copy limits

A display title is intentionally short:

- Chinese: target `8–18` characters; hard maximum `22`;
- English: target `2–6` words; hard maximum `8` words or `48` characters;
- Japanese: target `10–22` characters; hard maximum `28`.

If a conclusion exceeds the limit, edit the title and move detail to the support line. Do not shrink
an essay into a hero.

### Semantic wrapping

- Compose one to three complete phrase lines using explicit spans.
- Break at punctuation, clause, product name, or complete noun/verb phrase boundaries.
- Never split a product name, number and unit, modifier and head noun, or a semantic compound.
- Avoid a single Chinese/Japanese character or one short English word stranded on its own line.
- Use `text-wrap: balance`, `word-break: keep-all`, and normal overflow for display text.
- Never use `word-break: break-all` or `overflow-wrap: anywhere` on headings.
- On small screens, shorten display copy before allowing an awkward fourth line.
- Keep one accessible full title even when visual phrase spans control line breaks.

### Weight and line height

Use no more than three weights across the entire report. Preferred set:

- `400` for reading;
- `600` for labels, H3, and controls;
- `700` for display and H2 only.

Do not alternate `400 / 500 / 600 / 650 / 700 / 800` to simulate hierarchy. Use space and position
first.

Line-height ranges:

- display: `0.98–1.08`;
- section: `1.12–1.24`;
- body: `1.55–1.72`;
- meta: `1.35–1.50`.

Keep paragraph measure near `32–46` Chinese characters or `58–72ch` in English. Chinese headings
must not use tracking. English all-caps metadata may use at most `0.06em`.

## 5. Spacing and density

Use a deliberate rhythm rather than one uniform gap.

Allowed spacing tokens:

`8 / 12 / 16 / 24 / 32 / 48 / 72 / 96px`

Apply them by relationship:

- icon to label, metadata pairs, dense table cells: `8–12px`;
- title to support, claim to immediate evidence: `16–24px`;
- related signal blocks: `24–32px`;
- major section transitions: `72–96px`;
- page edges: `32–72px` depending on viewport.

Framework-specific rhythm:

- directory threshold: `96px` before the index and `72px` after it;
- chapter marker to chapter title: `12–16px`;
- chapter title to first governed object: `24–32px`;
- primary exhibit to its caption or interpretation: `12–24px`;
- end of evidence detail to next chapter: `72–96px`;
- rail item to rail item: `16–24px`, with no boxed container per link.

Use the principle **open at the macro level, dense at the micro level**:

- a major conclusion receives generous empty space;
- evidence rows, dates, units, and sources become tightly aligned;
- open and dense regions alternate;
- do not surround every block with `24px` padding and `24px` gaps;
- whitespace is not repaired with filler copy or extra cards.

Align content to one grid. Repeated rows share baselines. Captions sit closer to their object than to
the next section. Avoid accidental near-equal gaps that make unrelated elements appear grouped.

## 6. Color budget

Gray belongs to the neutral ink family. It does not consume a chromatic slot, but it must not become
a second unrelated warm/cool neutral system.

Across the whole page, use at most three chromatic colors:

1. one primary color;
2. one secondary color;
3. one optional pop color.

Use fewer whenever possible. Derive background, surface, text, muted text, and rules from one
coherent ink family rather than mixing blue-gray, green-gray, warm-gray, and black systems. The
seven canonical runtime variables are role slots, not permission to introduce seven unrelated
colors: `--bg`, `--bg2`, `--ink`, `--muted`, and `--rule` form the neutral ink family;
`--accent` and `--accent2` consume chromatic roles.

Use `html-report`'s canonical color variables and no parallel token family:

1. `--bg`;
2. `--bg2`;
3. `--ink`;
4. `--muted`;
5. `--rule`;
6. `--accent`;
7. `--accent2`.

The runtime may define all seven even when the composition uses only one accent. Do not add
`--radar-*`, `--positive`, `--negative`, per-priority, or per-competitor color tokens. Raw color
literals outside the canonical token block are prohibited. Derive chart and interface states from
the canonical variables.

### Default light logic

- Use pure white as the page field.
- Use near-black for primary text.
- Use one neutral gray for muted text, axes, and dividers.
- Use one verified brand or report accent.
- Add a separate surface only when a blueprint requires object separation.

Do not use weak cream, yellowed white, gray-green, pale blue, lavender, or pastel fog as a default
background.

### Default dark logic

- Use near-black or dark brown, never default navy.
- Use near-white or ivory foreground.
- Use one bright muted neutral.
- Use one accent.
- Every text, axis, legend, tooltip, and empty state sets a bright foreground explicitly.

For surfaces with relative luminance below `0.18`, body text must meet WCAG AA `4.5:1`. Large text
must meet at least `3:1`, targeting `4.5:1`. Never place dark gray, burgundy, navy, forest, purple,
or other dark chromatic text on a dark surface.

### Chart color

- One series receives the accent; context uses foreground/muted roles.
- Differentiate peer series with line style, symbol, direct label, pattern, or controlled opacity
  before adding hues.
- Use at most four peer series plus `Other`.
- If verified competitor brand colors are necessary for identity comparison, use at most two and
  remove the general accent; the surrounding interface remains neutral.
- Do not allocate a color to every priority, entity, evidence state, or section.
- Tints and opacity variants are not an excuse to create a disguised rainbow.

No purple-blue gradient, violet glow, dominant green field, or generic AI palette is allowed unless
the user, verified product brand, or the explicitly selected runtime style requires it. Even then,
keep evidence, tables, charts, tooltips, and source ledgers on opaque high-contrast fields.

## 7. Geometry and depth

Card shape follows the blueprint; it is not a global reflex.

- `Verdict Sheet`, `Swiss Trace`, and editorial `Decision Mosaic`: `0–4px` radius.
- `Evidence Object`: only the real artifact frame may use `20–28px`.
- product-led `Decision Mosaic`: one consistent `12–16px` radius.
- `Signal Stage`: one consistent `10–14px` radius or none.
- `Alert Cut`: `0–6px`.

Do not round every table, paragraph, source, and chart. Do not mix square evidence tables with
unrelated pill cards unless the product system explicitly calls for it.

Never attach a colored strip, rule, ribbon, partial border, or accent-colored complete border to
any edge of a card, callout, sidebar/reading rail, top bar/header, navigation item, table frame,
section, or heading. This ban applies to every edge, including inset-shadow imitations. Use a
neutral complete border, neutral bottom divider, contained mark, full-field inversion, or
whitespace.

Depth rules:

- flat is the default;
- use at most one raised focal plane and one shadow recipe;
- soft shadow is reserved for a real floating object or one focal module;
- glass or blur is allowed only when it clarifies an actual overlay relationship;
- never put blurred imagery behind dense body copy;
- no gradient orb, ambient glow, decorative sphere, or generic 3D object.

Card role rules:

- **signal card** — selectable peer object; one coherent grammar and one selected state;
- **index entry** — anchor and chapter promise; stays flat and is not a miniature content card;
- **evidence object** — source-bound artifact or exact comparison; may be framed when the object
  itself needs separation;
- **decision object** — action / owner / horizon / trigger; compact and operational;
- **source row** — citation ledger row; never a rounded card;
- **chapter marker** — typographic locator; never a container.

If a block has no selectable, comparable, expandable, or object-framing role, first try whitespace,
alignment, a neutral rule, or a table before making it a card.

## 8. Data visualization and interaction

Follow `html-report`'s visual router. Quantitative charts use its local ECharts runtime. Inline SVG
is allowed only for the runtime-permitted minimal cases such as a tiny sparkline, one progress
indicator, or at most three simple data points without axes, legends, or interaction. It must not
replace a primary matrix, timeline, funnel, radar, gauge, or evidence visualization. Structural
topology uses the runtime's Mermaid/PlantUML/Graphviz route.

### Chart selection

Use a small, refined family:

| Question | Preferred form |
|---|---|
| change over time | line, step line, or interval timeline |
| competitor × theme | interactive matrix/heatmap when comparable; exact table otherwise |
| priority trade-off | scatter field |
| price/package delta | grouped bar, slope, or exact old → new table |
| narrowing pipeline | funnel only with consistent stages and denominators |
| comparable capability profile | radar only for `2–3` entities and `3–6` identical normalized axes |
| one bounded status | gauge only for one meaningful bounded metric with a real threshold |
| branching impact | restrained Mermaid or semantic impact trace |
| next move | act / validate / watch rail |

Funnel, radar, and gauge are allowed when the data semantics justify them. Do not ban a system chart
merely because it is common; do not use it for visual variety.

### Required interaction

Every quantitative chart must:

- show exact values, unit, date/timezone, evidence status, and source or source key on hover/focus;
- provide a visible hover/emphasis state;
- bind click when a useful action exists: lock comparison, reveal evidence, open a cited source, or
  trace an impact path;
- never bind a decorative click with no state change;
- expose the same information through keyboard focus, a focusable proxy, or an adjacent exact table;
- support tap on touch devices;
- keep legend selection, focus, and locked state visually distinct using the existing color budget;
- include an empty state and `N/A` behavior;
- disable or minimize animation and respect reduced motion.

For ECharts:

- use the runtime's `_shared/js/echarts.min.js`, canonical tokens, external `assets/charts.js`, and
  SVG renderer;
- keep the runtime library before the chart script and place both after every chart container;
- give every chart a visible title, explicit height, status fallback, and adjacent exact table;
- enable `tooltip.appendToBody`, `aria`, `emphasis`, `animation: false`, and resize behavior;
- wait for fonts, guard `window.echarts` and container existence, catch errors, and avoid allowing one
  missing container to abort later charts;
- keep interaction transitions at or below `180ms`;
- direct-label the focus series when practical.

### Motion and state

- Use one motion curve and a `120–180ms` duration for hover, focus, selection, and disclosure
  feedback.
- Prefer color, complete-border, underline, number shift, and opacity changes. Avoid hover lift,
  spring motion, scale pulses, and parallax.
- Never animate layout before the user's input is acknowledged. Selection feedback appears first;
  chart emphasis and evidence disclosure follow in the same frame or immediately after.
- A signal selection is one state shared by card, chart, URL/hash when useful, and detail surface.
  Do not maintain separate active indices.
- Preserve selection during resize and when returning from a source link.
- Under `prefers-reduced-motion: reduce`, make all state changes immediate and disable nonessential
  chart animation.

For Mermaid:

- use it only for genuinely branching topology;
- keep nodes clickable/focusable only when a real evidence or source action exists;
- provide a semantic text fallback.

## 9. Tooltip and help behavior

When a term cannot be shortened without losing meaning, use one unified help control:

- a coherent `16–18px` SVG question icon inside a real button;
- hover, keyboard focus, tap, and Escape behavior;
- `aria-describedby` or equivalent accessible association;
- tooltip maximum width `280–320px`;
- body-sized or meta-sized type with `1.45–1.60` line height;
- one complete border, one high-contrast surface, and the report's existing color tokens;
- no gradient, glass blur, emoji, or oversized shadow;
- place the tooltip so it does not cover the value being explained;
- allow pointer movement into the tooltip when it contains a link;
- never make material evidence hover-only.

Use help controls sparingly. A visible label is better when space permits.

## 10. Reference transfer

Transfer design logic, never identifiable composition:

- from premium product pages: clear focal object, generous whitespace, one dominant module, and
  restrained depth;
- from object-centric design: real product or evidence artifact paired with concise claims;
- from Swiss editorial systems: strict grid, strong typographic scale, dense indices, and rational
  geometric state marks;
- from modular interfaces: unequal modules organized around one primary relationship;
- from high-contrast identity systems: monochrome field plus one disciplined accent.
- from editorial contents systems: chapter numbers, concise promises, directional anchors, and
  deliberate threshold whitespace;
- from exhibition design: a sequence of reveal, orientation, focal object, close reading, and source
  room.

Do not reproduce a reference's brand, exact palette, product object, copy, grid dimensions, card
arrangement, or hero structure. Do not import stock people, devices, or 3D objects merely to resemble
a design reference.

## 11. Shared HTML and Dynamic UI identity

Both outputs use one Radar Style Contract containing:

- selected framework, navigation behavior, blueprint, and bucket;
- focal signal and decision;
- display title and semantic line spans;
- type roles and weight set;
- spacing tokens and macro/micro density plan;
- canonical `html-report` color values and actual focus/accent usage;
- radius model and depth rule;
- primary chart and interaction contract;
- signal overview, card grammar, visible-copy budget, and disclosure behavior;
- Dynamic UI companion composition;
- paired Dynamic UI companion ID, guide asset, focal/support slots, and light/dark token values;
- light/dark foreground pairs;
- status vocabulary;
- 80/20 evidence-specific choice;
- uniform-random selection ID and selected asset.

Dynamic UI must use the real `PureShowWidget` tool after HTML completion. Override any default purple
or generic product palette with the selected tokens. Match the HTML's geometry and focal signal
while preserving host-theme tokens and runtime behavior.

Use the companion returned by the same uniform-random receipt as HTML. Do not draw again or route a
companion from content. Read `dynamic-ui-companions.md`; let the built-in runtime choose its scene
and ready material, then use the companion only to adapt composition and identity.

The widget contains one focal relationship and at most one supporting note. It does not recreate the
report shell or all report sections.

## 12. Verification

Before delivery:

1. use static-only checks; do not start a server, open a browser, use browser automation, capture
   screenshots, invoke the built-in HTML validator, or call another system HTML checker;
2. confirm from DOM and CSS that the selected framework and blueprint enhance the runtime foundation;
3. run file/path checks, JavaScript syntax checks, and `scripts/report_visual_audit.py`;
4. verify three type roles by default and no more than four;
5. verify display-copy length and phrase-safe wrapping;
6. verify no more than three font weights and permitted families;
7. verify spacing alternates open macro-sections with dense evidence;
8. verify only the seven canonical `html-report` color variables are defined;
9. verify no raw colors outside the token block;
10. verify radius follows one blueprint rather than a universal card style;
11. verify no colored edge strip or accent border on cards, sidebar/rail, top bar/header,
    navigation, table frames, sections, or headings;
12. verify all data charts are interactive and have exact-data fallbacks;
13. verify the source code implements mouse, keyboard, touch, and Escape behavior for help tooltips;
14. verify dark foregrounds and chart labels pass contrast;
15. verify the HTML and Dynamic UI use the same data and visual contract;
16. verify no filler copy, stale sample, unlabeled placeholder, or invented data remains;
17. verify no visible Markdown-like Signal Stack or over-budget paragraph remains;
18. verify signal cards, chart selection, and evidence disclosure synchronize;
19. verify the contents/rail markup uses real anchors, exposes `aria-current`, and includes mobile
    and print rules;
20. verify card transitions stay within `120–180ms`, share one selected state, and respect reduced
    motion;
21. verify no internal wireframe, framework study, style-contract text, audit output, sample metric,
    or implementation note is visible;
22. verify print CSS preserves evidence, priority, source links, and uncertainty.
