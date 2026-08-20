# Signal visual encoding

## Contents

1. Core rule
2. Two-layer information architecture
3. Text budgets
4. Multi-signal overview router
5. Signal card grammar
6. Full evidence disclosure
7. Interaction contract
8. Visual density by signal count
9. HTML audit hooks
10. Completion gate

## 1. Core rule

A Signal Stack is an analytical model, not a visible prose template.

Never print these seven labels as a vertical series of paragraphs:

`Event / Evidence / Delta / Meaning / Exposure / Move / Next trigger`

Encode them into comparison, change, impact, action, and evidence components. Preserve the complete
reasoning in the detail layer, but keep the default HTML reading surface visual and scannable.

## 2. Two-layer information architecture

### Layer 1: decision surface

Visible by default:

- one multi-signal overview;
- one primary interactive visual;
- concise signal cards;
- one act / validate / watch object;
- a compact evidence count and confidence cue.

The decision surface answers:

1. what changed;
2. which change matters most;
3. how it differs from the baseline;
4. what to do next;
5. where uncertainty remains.

### Layer 2: evidence surface

Open by click, keyboard activation, or print expansion:

- dated event history;
- primary and confirming sources;
- exact factual delta;
- inference and exposure;
- bounded move, owner, timing, and trigger;
- caveats and evidence gaps.

Use a side drawer, anchored detail panel, or native `<details>` structure. Do not hide material facts
behind hover alone.

## 3. Text budgets

These are hard maximums for the default visible surface:

| Element | Chinese/Japanese | English |
|---|---:|---:|
| display verdict | `22` characters | `8` words |
| support line | `48` characters | `30` words |
| section introduction | `44` characters | `28` words |
| signal title | `18` characters | `7` words |
| baseline side of delta | `14` characters | `6` words |
| changed side of delta | `14` characters | `6` words |
| impact line | `36` characters | `22` words |
| action line | `30` characters | `18` words |
| next trigger | `28` characters | `18` words |
| visible signal summary total | `120` characters | `75` words |

Additional limits:

- no visible paragraph may exceed `70` Chinese/Japanese characters or `50` English words;
- no default-visible paragraph may exceed three desktop lines or four mobile lines;
- show no more than two source references per signal on the decision surface;
- place owner, deadline, priority, date, and confidence in compact fields rather than prose;
- use at most three compact metadata cues beside a signal title;
- remove explanatory sentences that merely restate a label or chart.

When copy exceeds a limit, compress, split into visual fields, or move it to the evidence surface.
Never reduce the font to force excess text into a card.

## 4. Multi-signal overview router

Choose one overview:

| Evidence shape | Overview |
|---|---|
| repeated fields across `3–6` signals | exact comparison table or signal matrix |
| dated events | interactive timeline |
| entities × themes | interactive matrix/heatmap when values are comparable |
| impact × urgency | RISE scatter field |
| baseline → changed state | delta lanes |
| actions by horizon | act / validate / watch board |

An overview is not followed by paragraphs that repeat every cell. Signal cards add evidence,
implication, and action—not the same headline in another shape.

## 5. Signal card grammar

Use one coherent card grammar for all peer signals. Cards may be square or rounded according to the
selected layout blueprint. Every visible signal card must declare `data-card-role="signal"` and
must pass the anti-card test in `curatorial-framework.md`.

### Header

- rank or signal ID;
- concise title;
- priority;
- one combined domain cue;
- risk/opportunity state only when decision-relevant.

Do not turn every field into a colored badge. Keep metadata neutral and let one selected signal use
the accent.

### Body

Use three visual rows:

1. **Delta lane** — `baseline → changed state`;
2. **Impact line** — one decision consequence;
3. **Action line** — verb, owner, and horizon in separate aligned fields.

### Footer

- evidence count or strongest source tier;
- exact date or date status;
- next trigger;
- a short `查看证据` / `View evidence` control.

The full event list and source citations do not sit in the card body.

### Card selection

- hover/focus reveals emphasis and a concise source preview;
- click locks selection, synchronizes the primary chart, and opens the evidence surface;
- the trigger is a native button with `data-signal-id`, `aria-pressed`, and, when it opens evidence,
  `aria-expanded` plus `aria-controls`;
- selected state uses the single accent; peers remain neutral;
- compare mode may lock at most two cards;
- cards must remain readable without hover.

## 6. Full evidence disclosure

The evidence surface uses structured objects, not seven narrative paragraphs:

| Signal Stack field | Detail encoding |
|---|---|
| Event | dated event timeline or compact fact list |
| Evidence | source table: title, tier, date, role, link |
| Delta | two-column baseline → changed comparison |
| Meaning | one inference block, explicitly labeled |
| Exposure | product / commercial / strategic impact cells |
| Move | action table: action, owner, horizon, dependency |
| Next trigger | single watch condition with next-check date |

Use short cells and bullets. A source title may remain long when exact attribution requires it.
Preserve the complete structured evidence record, not the full text of an external article, post, or
paid source. Use concise paraphrases, rights-safe excerpts only when necessary, and direct links.
Print expands the evidence surface and preserves links.

## 7. Interaction contract

For multi-signal reports:

- card selection filters or emphasizes the primary chart;
- chart selection locks the corresponding card;
- source hover/focus shows title, publication/effective date, tier, and role;
- click on a source opens the cited page or evidence row;
- question-icon help explains RISE, confidence, or evidence state;
- filters are limited to dimensions that materially change the decision;
- keyboard, mouse, and touch produce equivalent access;
- Escape closes drawers and returns focus to the invoking control.
- selection uses one shared signal ID across card, chart, evidence surface, and optional URL hash;
- transitions stay within `120–180ms` and become immediate under reduced motion.

Use one interaction model consistently. Do not mix click-to-expand, hover-only popovers, modal
windows, and accordion behavior for equivalent objects.

## 8. Visual density by signal count

### One signal

Use one focal visual, one compact signal object, and one evidence disclosure. Do not create a grid.

### Two signals

Use a direct comparison, two cards, and one shared decision rail.

### Three to six signals

Use:

- one overview matrix/chart;
- one signal deck with one card per signal;
- one action board;
- one synchronized evidence panel.

Cards may form a `2 + 3` or `1 + 2 + 2` editorial composition. One selected card may span two
columns. Do not create different colors or component grammars for each card.

### Seven to twelve signals

Use an overview table/matrix and one selected detail card. Do not show twelve full cards at once.
Allow filtering or pagination while preserving a complete exact table.

### More than twelve signals

Show clusters, priority distribution, and a searchable exact table. Detail appears only for the
active signal.

Use at most one primary chart and two supporting interactive components on one page. More chart
types do not create better analysis.

## 9. HTML audit hooks

Expose structure for `report_visual_audit.py`:

- set `data-signal-count` on the root `<html>`;
- mark the overview with `[data-signal-overview]`;
- mark each peer card with `[data-signal-card]`;
- declare `data-card-role="signal"` and the same `[data-signal-id]` on each peer card;
- wrap default-visible card copy with `[data-signal-summary]`;
- mark the native activating button with `[data-signal-trigger]`, `[data-signal-id]`, and
  `aria-pressed`;
- mark the expandable evidence surface with `[data-signal-detail]`;
- mark exact source rows with `[data-evidence-row]`.

For reports with three to six signals, the audit expects one overview, one card and trigger per
signal, and no Markdown-like seven-field stack on the default surface.

## 10. Completion gate

Verify:

1. no seven-paragraph Signal Stack is visible by default;
2. every signal satisfies the visible text budget;
3. repeated facts are encoded once;
4. cards share one grammar, palette, radius, and interaction model;
5. one primary visual and no more than two supporting components carry the analysis;
6. hover/focus/click synchronize card, chart, and evidence;
7. full evidence remains accessible and printable;
8. unknown values remain `N/A` or `待验证`, never zero;
9. no card is added merely to fill the grid;
10. HTML and Dynamic UI use the same selected signal and evidence state.
