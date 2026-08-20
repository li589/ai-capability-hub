# Procurement editorial and aesthetic system

Use this reference after choosing the report architecture and before writing HTML/CSS. Treat content volume, typography, spacing, color, shape, and interaction as one composition. A beautiful report is not a decorated document; it is a controlled field of information objects.

## Contents

1. Aesthetic position
2. Five-level type system
3. Visible-text budget
4. Semantic line composition
5. Spacing and density rhythm
6. Color budget
7. Shape, depth, and cards
8. Tables, cards, charts, and prose
9. Interaction and microcopy
10. Editorial brief
11. Acceptance

## 1. Aesthetic position

Use these principles together:

- **clarity before decoration** — every visible mark must explain, compare, locate, or enable an action;
- **controlled contrast** — hierarchy comes from a few decisive differences, not many small differences;
- **semantic scale** — large type is earned by decision importance and therefore carries fewer words;
- **composed density** — alternate open, quiet stages with compact analytical fields; do not make the whole page uniformly sparse or uniformly dense;
- **object over paragraph** — turn comparable, sequential, conditional, or causal content into a visual object;
- **one visual voice** — page, cards, tables, charts, controls, and tooltips share the same type, color, geometry, and selection language;
- **procurement specificity** — let quotes, thresholds, suppliers, routes, periods, gates, and evidence create the visual structure.

Do not imitate a reference layout literally. Extract its underlying discipline—scale, grid, cropping, rhythm, or material treatment—and rebuild it around the procurement decision.

## 2. Five-level type system

Use no more than five visible size roles:

| Role | Desktop | Mobile | Line height | Content limit |
|---|---:|---:|---:|---|
| Hero | `48–64px` | `36–48px` | `0.98–1.12` | one short title or one metric; no paragraph |
| Section | `28–36px` | `24–30px` | `1.16–1.28` | one conclusion or question |
| Object | `18–22px` | `17–20px` | `1.28–1.4` | card, chart, table, or local object title |
| Body | `15–17px` | `15–16px` | `1.6–1.75` | short explanation only |
| Meta | `12–13px` | `12–13px` | `1.35–1.5` | unit, basis, source, date, compact control |

The page title and the single dominant metric share the Hero scale. Do not create separate display, H1, KPI, quote, intro, and deck sizes.

Use exactly these weight roles:

- `400` — body, values, chart labels, table body, large metrics;
- `600` — headings, active controls, table headers, direct labels;
- `700` — optional and rare; one verdict, failed mandatory gate, or final total.

Do not use `300`, `500`, `800`, or `900`. Scale, placement, and whitespace already create hierarchy.

Use one Chinese-capable sans family whenever possible. At most:

1. one Chinese family;
2. one compatible Latin family;
3. one exceptional face for codes or a brand-supplied display moment.

Do not use both a mono face and a decorative face merely to add variety. A third family must have a named semantic role and appear in less than 5% of visible text.

Use tabular numerals. Keep values with `%`, currency, units, periods, comparison signs, and basis markers.

## 3. Visible-text budget

HTML must visibly outperform Markdown. Treat uninterrupted prose as a scarce material.

### Page budgets

- Keep the first viewport under roughly `55` Chinese characters of explanatory prose, excluding labels, units, and table/chart text.
- Allow at most one visible introductory paragraph before the first analytical object.
- Do not place more than two prose paragraphs consecutively.
- Keep each visible paragraph to one finding, normally `30–70` Chinese characters and no more than three lines at desktop width.
- Keep prose below roughly one third of the visible report area. Charts, structured tables, cards, diagrams, controls, and whitespace should dominate.
- Permit at most one text-led major section in a standard report. All other sections need a primary visual object.

### Component budgets

| Component | Visible copy budget |
|---|---|
| Hero title | two semantic lines; normally `8–16` Chinese characters total |
| Hero support | one sentence; normally `20–40` Chinese characters |
| Large metric | value + unit + label + one short consequence |
| Card face | one title, one primary fact/action, up to three compact supporting facts |
| Chart annotation | one finding per annotation; normally `8–22` Chinese characters |
| Tooltip | identity + values + basis + action cue; no essay |
| Button | verb + object, usually `2–6` Chinese characters |
| Section lead | one sentence or one short paragraph |

Remove empty phrases such as “值得注意的是”, “从数据可以看出”, “进一步分析发现”, “总体而言”, and ornamental English labels. State the finding directly.

When detail is necessary:

- attach a question-mark help trigger to the relevant label;
- expose a polished hover/focus/click popover;
- use `<details>` for evidence or formulas;
- move audit detail to a table or appendix;
- never hide a verdict, failed gate, unit, or essential condition.

## 4. Semantic line composition

Treat every Hero and Section heading as typeset composition.

- Author Hero titles as one or two semantic lines; use a third only for an indispensable qualifier.
- Keep each Hero line to roughly `5–12` Chinese characters.
- Break at a clause, noun phrase, named option, or contrast boundary.
- Never split a supplier, product/model, currency-value, quantity-unit, percentage, date, Incoterm, or evidence token.
- Avoid a one-character final line, punctuation-only line, orphaned number, or detached qualifier.
- Shorten the copy before shrinking it below its role.
- Move scope, period, basis, and date to Meta text.
- For Latin text, use balanced wrapping but never hyphenate a product or supplier name.

```html
<h1>
  <span class="semantic-line">年度树脂成本</span>
  <span class="semantic-line">与供应商授标</span>
</h1>
```

```css
h1, h2, .display-copy {
  text-wrap: balance;
  word-break: keep-all;
  overflow-wrap: normal;
  line-break: strict;
}
.semantic-line { display: block; }
.value-unit, .supplier-name, .model-name { white-space: nowrap; }
p, li { text-wrap: pretty; }
```

Do not insert `<br>` after a fixed character count.

## 5. Spacing and density rhythm

Use an 8px family:

`4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128`

Use the same space for the same relationship:

| Relationship | Space |
|---|---:|
| label → value | `8px` |
| title → support | `12–16px` |
| dense row → dense row | `8–12px` |
| object internal gap | `16–24px` |
| object padding | `24–32px` |
| sibling analytical objects | `24–32px` |
| subsection → subsection | `48–64px` |
| major section → major section | `64–96px` |
| one deliberate editorial pause | `96–128px` |

Do not improvise near-duplicate values such as `18`, `20`, `22`, `27`, and `30px`.

Read the whitespace choreography in `procurement-curatorial-framework.md` before assigning section padding. Distinguish macro chapter pauses, meso object relationships, and micro scanning rhythm. Every large gap must balance a focal object, separate a narrative act, or isolate a conclusion; empty viewport filling is not whitespace design.

Apply “疏可跑马、密不透风” as contrast, not chaos:

- choose one or two **open stages** per report: large short title or dominant chart, limited supporting copy, `64–128px` breathing room;
- choose **dense evidence fields** for matrices, ledgers, timelines, and comparison rows: tight alignment, `8–16px` internal rhythm, no ornamental gaps;
- place an open stage before or after a dense field so each strengthens the other;
- do not repeat the same density for three consecutive sections;
- do not use empty space that lacks a focal object;
- do not compress unlike information into a dense field merely to appear sophisticated.

Keep narrative measure around `28–42` Chinese characters per line. Annotations may be narrower.

## 6. Color budget

Use at most three chromatic hues across the whole report: one primary, one auxiliary, and one optional pop color. The renderer's white/background roles and one ink-derived neutral family may supply ink, muted text, rules, and quiet surfaces without becoming additional chromatic hues; do not introduce multiple unrelated gray families.

Use the built-in renderer's seven roles:

1. `--bg`: the selected route's page field;
2. `--bg2`: the selected route's one quiet or auxiliary surface;
3. `--ink`: one tested foreground ink;
4. `--muted`: one muted ink tone;
5. `--rule`: one structural rule;
6. `--accent`: recommendation and primary series;
7. `--accent2`: optional failed-gate or reversal signal.

Structural rules may use a low-opacity form of the same ink; do not create another named gray. Prefer whitespace over gray panels.

```css
:root {
  --bg: #ffffff;
  --bg2: #f7f8fa;
  --ink: #172033;
  --muted: #687083;
  --rule: #d8dce3;
  --accent: #2856a3;
  --accent2: #c44d32;
}
```

Rules:

- map `--accent` to the primary hue; place a route-defined auxiliary hue in `--bg2` only when it is a stable supporting surface; reserve `--accent2` for the optional pop/reversal role;
- do not assign new hues to individual suppliers, statuses, cards, sections, or chart series;
- use the selected route's declared field; Acid Registry is pure white, while Night Circuit retains its near-black field;
- do not use cream, ivory, yellow-beige, or timid warm-white page backgrounds;
- do not create gray cards merely to separate sections;
- use ink for baseline and most content;
- use `--accent` for recommendation, active selection, and the primary series;
- use `--accent2` only for failed gates, material exceptions, or reversal triggers; keep it under 8% of a viewport;
- use labels, shape, line style, pattern, fill/outline, and direct annotation before adding a hue;
- do not color every supplier, status, or evidence state differently;
- allow only a single-hue tonal gradient when it encodes quantity; never use decorative rainbow or multicolor gradients;
- maintain the same semantic color mapping across page, cards, tables, charts, controls, and tooltips.

If the chosen direction uses a highly saturated field, use it as one deliberate block—not as many unrelated colored cards.

## 7. Shape, depth, and cards

Geometry belongs to the selected visual direction:

| Direction | Object corners | Depth |
|---|---:|---|
| Precision ledger / Swiss editorial | `0–4px` | rules and alignment; no shadow |
| Product stage / premium mobile | `12–20px` for named interactive objects | one soft shadow token; floating objects only |
| Signal block / neo-brutalist editorial | `0px` | flat color fields and hard grid |
| Evidence collage / technical archive | `0–8px` | overlap, crop, and annotation; little or no shadow |
| Mono audit | `0px` | line weight and spacing only |

Do not mix corner systems inside one report. Controls may be slightly rounder than structural content. Pills are only for binary status, filters, or units.

Every card must represent one real object: supplier, lane, scenario, exception, gate, action, or evidence bundle. Do not put an ordinary paragraph in a card.

### Bounded-surface edge rule

Decide surface emphasis before authoring markup. A card or callout may use a full neutral border, a full flat fill, or no border. It may never use color on only one edge.

Do not create a left-, right-, top-, or bottom-edge accent through physical borders, logical borders, pseudo-elements, narrow nested children, inset shadows, gradient stops, masks, background images, or SVG rails. This applies even when the rail is short, faint, translucent, rounded, or matches the selected route. Never use a blockquote-like colored left border as the visual grammar for a recommendation, risk, gate, finding, or condition.

Keep compact badges, dots, symbols, and underlines inside the content padding with visible neutral space between the mark and every frame edge. Prefer type scale, alignment, spacing, or a whole-surface reversal when the object needs stronger emphasis.

This rule is part of the anti-template aesthetic. Also reject repeated hero/KPI/card stacks, endless rounded containers, pill soup, default purple-blue or green dashboards, glows, decorative gradients, generic icon-per-heading systems, and color-per-status card grids. The report should derive hierarchy from the procurement decision, chapter rhythm, editorial scale, and real data objects—not from familiar AI-dashboard decoration.

Declare the object with `data-object-kind="supplier|option|lane|scenario|exception|gate|action|evidence"`. Give interactive cards stable rest, preview, pinned, and optional expanded states. Preview must not resize the card or reflow neighboring content.

Use elevation only to express stacking, dragging, an active overlay, or a mobile pass. Never apply soft shadows to every block.

## 8. Tables, cards, charts, and prose

Choose the strongest suitable representation:

`interactive chart or card → structured chart/card → enhanced table → short prose`

This is not a requirement to force every fact into a chart. It is a requirement to avoid using prose when the information has a clearer visual grammar.

| Information form | Preferred object |
|---|---|
| peers or options | comparison shelf, master/detail, ranked bars, enhanced table |
| thresholds or eligibility | gate matrix, bullet/progress object, interactive table |
| change over time | line/area/column timeline with pinned period |
| price-to-cost buildup | bridge or stepped ledger |
| sequence or handoff | route strip, process band, timeline |
| concentration or allocation | treemap, stacked share, concentration plot |
| uncertainty or trade-off | range band, frontier, scenario switcher |
| owner/timing/action | interactive execution register |
| evidence detail | help popover, progressive evidence, appendix table |

Tables are the minimum HTML visualization layer, not a failure. Upgrade them with:

- frozen identifiers where useful;
- aligned and tabular numbers;
- direct unit/basis labels;
- sortable or filterable columns only when they change a decision;
- row hover/focus and click-to-pin;
- expandable evidence rows;
- inline bars, status marks, deltas, or sparklines;
- responsive priority columns and a complete print view.

Use one dominant chart and up to two supporting chart types in a standard report. More interactive objects are allowed only when they reuse the same interaction grammar and remain subordinate to the decision.

## 9. Interaction and microcopy

Use a small, consistent interaction vocabulary:

- **hover/focus** previews;
- **click/Enter/Space** pins or opens;
- **second click or Escape** clears;
- **arrow keys** traverse peers;
- **selection** persists across linked cards, tables, and charts;
- **print/no-JS** exposes a complete static state.

Interactive cards may use:

- scroll-snap peer shelf;
- switch face for result versus basis;
- master/detail comparison;
- expandable evidence;
- linked selection across card, table, and chart.

Use one motion curve and one state language across the report. Keep preview motion to `140–180ms`, pin/expand motion to `180–240ms`, and physical movement to `0–2px`. Animate opacity, color, rule length, or a small internal reveal; do not use 3D flips, spring overshoot, or hover-triggered expansion.

Do not make card movement, parallax, glass, or 3D tilt the purpose of interaction.

For question-mark help:

- use a compact icon-only button with an accessible label;
- open on hover and focus; click pins it on touch;
- use a pure-white tooltip with ink text, one thin ink-derived rule, `8–12px` radius only when the visual direction permits, and a single quiet shadow;
- limit width to `18–24rem`;
- use a short title and up to three compact lines;
- keep the pointer visually aligned to its trigger;
- avoid yellow help bubbles, black browser-default tooltips, and paragraph-length definitions.

Write interface copy with nouns and verbs. Prefer `固定供应商`, `查看口径`, `清除选择`, `切换情景`. Remove banter, filler, redundant instructions, and ornamental bilingual labels.

## 10. Editorial brief

```markdown
## Procurement Editorial Brief
- Aesthetic direction:
- Hero semantic lines and total character count:
- Five type roles:
- Font families and the role of each:
- Weight roles: 400 / 600 / optional 700:
- Visible prose budget:
- Open stages:
- Dense evidence fields:
- Spacing steps used:
- Renderer variables: bg / bg2 / ink / muted / rule / accent / optional accent2:
- Object corners and elevation rule:
- Bounded-surface edge invariant:
- Permitted emphasis grammar and inset separation:
- Card-free sections:
- Primary object for every major section:
- Large-number count per viewport:
- Tooltip/help treatment:
- Chart and card selection mapping:
```

## 11. Acceptance

Resolve these as authoring commitments before generating HTML. They are not instructions to inspect the finished HTML:

1. The report uses no more than five visible size roles and three weights.
2. Hero copy is short, deliberately broken, and never split inside a semantic unit.
3. No visible paragraph exceeds three desktop lines without a strong reason.
4. No more than two prose paragraphs appear consecutively.
5. Every major section except at most one has a primary visual object.
6. Open stages and dense fields alternate deliberately.
7. All spacing uses the declared rhythm.
8. The page field matches the selected route; Acid Registry is pure white and Night Circuit is the only routed near-black field.
9. Gray and tints are counted; the report uses the renderer's seven declared roles without adding a parallel procurement palette.
10. Card geometry and shadow follow one direction rather than a global rounded-card default.
11. Cards represent real procurement objects, not paragraphs.
12. Charts, cards, tables, controls, and tooltips share one visual and interaction language.
13. Tooltips are concise, accessible, and polished.
14. Units, values, supplier names, dates, and evidence tokens do not split across lines.
15. The report would lose meaningful capability if converted directly to Markdown.
16. Macro, meso, and micro whitespace each express a named relationship.
17. Interactive cards preserve their dimensions between rest, preview, and pinned states.
18. Every card declares a real object kind.
19. No bounded surface uses a physical or logical one-sided colored border, edge pseudo-element, nested rail, inset shadow, narrow gradient, background image, mask, or SVG strip.
20. Every compact color mark remains visibly separated from the frame edge; stronger emphasis uses type, spacing, a full neutral border, or a whole-surface fill.
