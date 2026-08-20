# Curatorial framework and card system

## Contents

1. Definitions
2. Framework assignment
3. Three framework models
4. Contents and chapter choreography
5. Whitespace as structure
6. Chart, text, and evidence relationships
7. Card roles and anti-card rules
8. Shared interaction state
9. Responsive, print, and accessibility
10. Assets and implementation hooks
11. Completion gate

## 1. Definitions

Treat an intelligence report as an exhibition of evidence.

The **framework** is the report-scale reading architecture. It controls:

1. the entry threshold;
2. orientation and navigation;
3. the order and pacing of chapters;
4. the relationship between focal exhibits and interpretation;
5. the exit into references, uncertainty, and next action.

The framework is not the header, a decorative background, a dashboard shell, or a set of repeated
containers. It must remain legible even if color and decoration are removed.

A **card** is a local object with a specific interaction or comparison duty. It may:

- represent one selectable signal among peers;
- frame a real evidence artifact;
- expose a bounded decision object;
- disclose detail on demand.

A card is not the default wrapper for any block of text. A title, chapter marker, source row,
reference ledger, long explanation, or arbitrary metric does not become clearer merely because it
has padding, a radius, and a shadow.

The framework and the cards must share one reading state. If signal `S03` is active, the card,
primary chart, evidence surface, action object, and optional URL fragment all identify `S03`.

## 2. Framework assignment

Do not route frameworks from evidence or report length. Use the framework returned by
`scripts/select_visual_style.py` together with its randomly selected style:

| Styles | Framework |
|---|---|
| Alert Cut, Signal Stage | **Exhibit Path** |
| Verdict Sheet, Decision Mosaic | **Index Gate** |
| Evidence Object, Swiss Trace | **Reading Rail** |

Do not hybridize, substitute, or reroll. Adapt chapter count and navigation density inside the
assigned framework while preserving its model below.

## 3. Three framework models

### A. Exhibit Path

**Intent:** one continuous, directed viewing sequence.

Sequence:

1. reveal — verdict and response window;
2. focal exhibit — one chart, artifact, or matrix;
3. close reading — concise signal object or comparison;
4. decision — act / validate / watch;
5. source room — evidence, uncertainty, and next trigger.

Rules:

- no persistent table of contents;
- no app-like sidebar, toolbar, breadcrumb, or decorative progress meter;
- use full-width chapter changes and macro whitespace;
- a compact `Back to decision` anchor may appear after a long evidence disclosure;
- keep the first viewport readable as one decision cut.

### B. Index Gate

**Intent:** show the architecture of the argument before asking for close reading.

Sequence:

1. cover verdict;
2. contents threshold;
3. numbered chapters;
4. action close;
5. source room.

The contents threshold uses a flat grid or ordered rows with:

- two-digit chapter number;
- title of at most `12` Chinese/Japanese characters or `4` English words;
- one-line promise explaining the question answered;
- real fragment anchor;
- optional small state cue such as `3 signals` or `updated 30 Jul`.

Do not turn every index entry into a raised card. Use alignment, a bottom rule, and hover/focus
movement within the existing color budget. Keep at least one intentionally empty grid cell when it
improves hierarchy.

The cover and contents may occupy separate viewport-height fields when the report has six or more
chapters. For five chapters, a compact contents threshold is sufficient.

### C. Reading Rail

**Intent:** preserve location during a long analytical read.

Desktop structure:

- rail: `180–224px` or `2–3` of 12 columns;
- content: remaining `9–10` columns;
- rail starts after the cover verdict;
- rail becomes sticky only within the analytical article;
- one active item uses `aria-current="location"`;
- progress, if used, is subordinate to the active chapter label.

Rail content:

- report label or short run date;
- chapter number and short title;
- one source-room link;
- no logos, filters, export controls, account controls, or duplicated metadata.

Use `IntersectionObserver` to update the active anchor from section visibility. Clicking an anchor
updates location first, then scrolls. Avoid scroll-jacking and animated page-length transitions.

## 4. Contents and chapter choreography

### Chapter numbering

- Use one system from `01` onward.
- Keep the same number in contents, rail, chapter marker, and print.
- Do not number decorative bands or repeated cards as chapters.
- A nested signal may use `S01`, `S02`, and so on; do not confuse signal IDs with chapters.

### Chapter openings

Each analytical chapter opens with:

1. a small number or noun label;
2. one title that states the question or conclusion;
3. an optional support line;
4. the first governed object within `24–32px`.

Place the title on the same grid as its primary object. Do not center every title. Left alignment is
the default; right or vertical placement is allowed only when it creates a deliberate relationship
with a large adjacent object and remains readable on mobile.

### Chapter sequence

Use the rhythm:

`orientation → evidence → interpretation → decision → reference`

Do not repeat `headline → three cards → paragraph` for every chapter. Alternate:

- open verdict field;
- dense exact matrix;
- asymmetric focal exhibit;
- compact decision rail;
- quiet source room.

The change in density should match the change in cognitive task.

## 5. Whitespace as structure

Whitespace expresses hierarchy and grouping.

Use three scales:

- **micro, `8–16px`** — label/value, icon/text, source metadata;
- **component, `24–48px`** — rows inside a card, chart/caption, related objects;
- **chapter, `72–96px`** — a genuine change of question.

Rules:

- equal gaps imply equal relationships; do not use the same gap everywhere;
- captions sit closer to the exhibit than to surrounding prose;
- a chapter title belongs to the content below it and therefore has more space above than below;
- leave a quiet field around the primary verdict or chart;
- keep tables and source ledgers compact so the surrounding whitespace remains meaningful;
- do not repair an awkward empty area with a decorative metric, generic icon, stock image, or extra
  card;
- intentional empty grid cells are permitted; accidental stranded copy is not.

For a 12-column desktop grid, useful patterns include:

- verdict `7` + decision note `5`;
- chart `8` + interpretation `4`;
- artifact `7` + annotated claim `5`;
- active signal `6` + two peer signals `3 + 3`;
- contents `4 + 4 + 4`, with one later cell intentionally open when only five chapters exist.

Avoid `4 + 4 + 4` as a universal reflex.

## 6. Chart, text, and evidence relationships

Choose one relationship per analytical chapter:

### Exhibit first

Use when the data pattern is the argument. Give the chart `7–9` columns. Put the title and one
interpretive note in the remaining field or directly above. Keep exact values adjacent below.

### Claim first

Use when the decision sentence must be read before the evidence. Give the claim a short open field,
then a full-width chart or object. Do not place three summary cards between claim and evidence.

### Annotated object

Use when a product screenshot, price table, policy excerpt, or source artifact is the strongest
evidence. Number annotations on the object and map them to short claims beside it. Preserve the real
artifact and citation.

### Comparison field

Use when peers share comparable dimensions. One exact matrix or synchronized chart provides the
overview; cards add implication and action only. Do not restate every matrix cell inside each card.

Charts are exhibits, not wallpaper. Never place a chart as a background behind body text. Never use
an illustration where a source artifact or exact table is required.

## 7. Card roles and anti-card rules

### Signal card

Use for `3–6` peer signals when selection changes the primary chart or evidence surface.

Anatomy:

- ID and short title;
- priority plus at most two neutral metadata cues;
- baseline `→` changed state;
- one impact line;
- action / owner / horizon;
- evidence count, date, and `View evidence`.

The entire header or one clear button may activate selection. Do not nest several competing primary
buttons.

### Evidence object

Use for a real screenshot, exact source excerpt, dated comparison, or document artifact. The
artifact receives visual priority; its citation is attached. Only this role may use a larger radius
when the selected blueprint permits it.

### Decision object

Use for a bounded action. Expose:

- verb and object;
- owner;
- horizon or deadline;
- dependency;
- next trigger.

Prefer one horizontal rail or exact table over three equal motivational cards.

### Index entry

Use only in Index Gate or the mobile form of Reading Rail. It is a navigation object, not a content
summary card. Keep it flat and concise.

### Source row

Always render as a table or aligned ledger row. Preserve title, source tier, event/publication/
effective date, evidence role, and link. Never turn dozens of sources into rounded cards.

### Anti-card test

Before creating a card, answer:

1. Is it compared with a peer?
2. Is it selected or expanded?
3. Does it frame a real artifact?
4. Does it contain a bounded operational object?

If all four answers are no, use typography, whitespace, a rule, a row, or a section instead.

## 8. Shared interaction state

Use one signal identifier such as `S03` as the state key.

State sequence:

1. **rest** — all peer signals readable;
2. **hover/focus** — preview emphasis only;
3. **selected** — one signal locked across card, chart, and details;
4. **expanded** — the selected signal's evidence surface is open.

Requirements:

- card buttons expose `aria-pressed`;
- evidence triggers expose `aria-expanded` and `aria-controls`;
- selected card uses a complete border, contained mark, or full-field inversion—never a colored
  colored edge strip on any side;
- hover never displaces adjacent content;
- interaction transitions use one `120–180ms` curve;
- a chart click selects the same ID and updates the card before opening detail;
- `Escape` closes the evidence surface and returns focus to the invoking control;
- deep linking may use `#signal-S03` when it is useful and stable;
- URL/hash, card, chart, and detail must never show different active IDs;
- native links and buttons remain usable before JavaScript loads;
- reduced motion makes changes immediate.

Use `assets/radar-visual-kit/radar-interactions.js` as an optional local starting point. It emits and
accepts `radar:select-signal` events so the chart initializer can share the same state. Adapt IDs and
detail behavior to the evidence; do not copy it blindly.

## 9. Responsive, print, and accessibility

### Mobile

- Exhibit Path remains a single narrative column.
- Index Gate becomes one or two flat columns according to title length.
- Reading Rail becomes a compact chapter index before the article or a horizontally scrollable
  anchor list with visible focus and no hidden essential chapters.
- Preserve narrative DOM order: title, support, exhibit, interpretation, exact values.
- Avoid sticky elements that consume more than `20%` of viewport height.

### Print

- expand all evidence details;
- print a compact contents block for Index Gate and Reading Rail;
- remove sticky positioning, hover-only previews, and interactive-only controls;
- preserve chapter numbers, exact values, units, dates, source links, and uncertainty;
- move dark evidence ledgers to white with black text.

### Accessibility

- provide a skip link to the decision surface;
- use native anchors for navigation and native buttons for selection;
- mark the active chapter with `aria-current="location"`;
- use `scroll-margin-top` rather than scroll offsets that hide headings;
- keep focus outlines visible and distinct from selected state;
- announce material selection changes in one polite live region;
- do not announce every scroll-based chapter change.

## 10. Assets and implementation hooks

The visual kit contains:

- `radar-interactions.css` — token-based motion and state recipe;
- `radar-interactions.js` — optional progressive enhancement for chapter navigation and shared
  signal selection;
- `icons/radar-icons.svg` — unified line icons.

All visual-kit code must use the canonical `html-report` variables and live inside the runtime's
report-local `assets/` directory when copied. The plugin contains no report-ready wireframe or
moodboard asset. Never expose framework studies, reference screenshots, layout notes, blueprint
names, or implementation commentary to the report reader.

Required HTML hooks:

- `<html data-radar-framework="exhibit-path|index-gate|reading-rail">`;
- `<html data-radar-blueprint="...">`;
- `[data-report-nav]` for Index Gate or Reading Rail;
- `[data-report-section]` plus a stable `id` on every analytical chapter;
- `[data-card-role="signal|evidence|decision|index"]` on actual cards;
- `[data-signal-card]`, `[data-signal-trigger]`, and `[data-signal-id]` for signal selection;
- `[data-signal-detail]` and `[data-evidence-row]` for evidence;
- one `[data-radar-live]` polite live region when selection changes meaningfully.

Do not add hooks to blocks merely to satisfy an audit. The visible composition must still make the
framework and role obvious.

## 11. Completion gate

Before delivery, verify:

1. framework matches the result returned by `select_visual_style.py`;
2. the report has a clear entry, orientation, chapter path, decision close, and source exit;
3. five or more analytical chapters have purposeful navigation;
4. contents and rail links use real anchors and one active location;
5. chapter titles are attached to their governed object;
6. macro whitespace and micro density visibly alternate;
7. charts and text have one explicit relationship per chapter;
8. every card passes the anti-card test and declares one role;
9. signal card, chart, evidence, and optional hash share one state key;
10. hover, focus, selected, and expanded states are distinct without layout jump;
11. motion remains within `120–180ms` and respects reduced motion;
12. mobile and print rules preserve orientation and evidence;
13. no reference composition, palette, brand object, internal framework artifact, or decorative
    filler was copied.
