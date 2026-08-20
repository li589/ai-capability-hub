# Procurement curatorial framework

Use this reference after selecting the report architecture and before locking typography or components. Treat the report as an exhibition of evidence: the framework directs movement, chapters control pacing, objects hold evidence, and cards are only one kind of object.

## Contents

1. Definitions
2. Curatorial spine
3. Navigation models
4. Chapter composition
5. Whitespace choreography
6. Card ontology and states
7. Chart-and-text relationships
8. Controlled variation
9. Original direction cues
10. Curatorial brief
11. Acceptance

## 1. Definitions

### Framework

The framework is the page-scale system that controls:

- where the reader enters;
- how the decision and chapters are sequenced;
- how navigation remains available;
- where the page becomes open or dense;
- how chapters change composition without losing continuity;
- how evidence, action, and references close the story.

A framework is not a repeated component grid. `summary cards → section cards → references` is content containment, not page architecture.

### Card

A card is a bounded, selectable view of one real decision object:

- supplier or option;
- route or lane;
- scenario;
- exception;
- gate;
- action;
- evidence bundle.

A card is not a default rectangle around text. If removing the boundary does not change identity, selection, comparison, or interaction, remove the card.

### Section

A section is one chapter-sized decision scene. It should feel like one coherent presentation slide:

`one question or finding + one dominant object + one supporting relation + one exit cue`

Do not force every section into the same composition. Preserve the same grid, type roles, colors, number treatment, rules, and interaction states while varying the placement of objects.

## 2. Curatorial spine

Build the report as five spatial acts:

1. **Threshold** — state the decision, exposure, and recommendation.
2. **Orientation** — show the table of contents or persistent chapter map.
3. **Exhibition** — move through three to six analytical chapters with alternating density.
4. **Decision room** — bring options, gates, and reversal variables onto one field.
5. **Exit** — close with owner, timing, trigger, fallback, verification, and references.

For a compact report, combine Threshold and Orientation. For a report longer than six major sections, do not omit Orientation.

Write a visitor route before authoring:

```text
enter → locate → compare → challenge → decide → act → verify
```

Every chapter must advance one verb. Remove a section that only repeats what the previous one established.

Use chapter numbering as orientation, not decoration:

- use `01`, `02`, `03` or `1.0`, `2.0`, `3.0` consistently;
- pair the number with a short noun or decision question;
- show the current number in the navigation and chapter heading;
- never number cards as if they were chapters.

Use three related naming roles instead of repeating one line:

- **contents plate** — canonical topic noun, such as `成本证据`;
- **persistent rail** — short orientation label, such as `成本`;
- **chapter heading** — the resolved finding or question, such as `组合方案节省 19.2 万元`.

Keep the number and semantic root stable. Keep the chapter heading short enough to work as large type; move basis, period, and qualifiers to Meta text.

## 3. Navigation models

Choose one navigation model and make it part of the framework.

### A. Contents plate

Use for linear executive reports, print-heavy review, or 5–9 chapters.

- Make the contents a real opening chapter, not a dropdown.
- Use a large `目录 / Contents` title and a ruled list of chapter links.
- Add one short thesis or reading instruction beside the list.
- Use visible chapter numbers and concise titles.
- Make the whole row clickable and preserve deep links.
- Mark the current or recommended starting chapter with one compact signal.

### B. Sticky chapter rail

Use for analytical reports read on desktop.

- Reserve `12–18rem` at the edge of the content grid.
- Keep the rail visually quiet; use text, number, and one active rule.
- Highlight the active chapter through weight, ink/`--accent` color, and a short marker.
- Never place KPI cards, promotional copy, or secondary charts in the rail.
- Release the rail before the execution close when the closing needs full width.

### C. Horizontal chapter strip

Use for operational reports, tablets, or a smaller number of peer chapters.

- Keep it sticky below the report header when useful.
- Allow horizontal scrolling with the current chapter kept visible.
- Use text labels, not icon-only navigation.
- Maintain 44px touch targets without making the strip visually heavy.

### D. Hybrid orientation

Use for long reports that must work both as a presentation and a reference.

- Open with a contents plate.
- Continue with a reduced sticky rail or horizontal strip.
- Use the same numbers and semantic roots in both. Keep the full topic name in the contents plate; abbreviate the rail only when space requires it and preserve the full topic in the accessible label.
- Do not add a third navigation grammar.

Runtime contract:

```html
<nav class="pui-report-nav" data-pui-report-nav aria-label="报告目录">
  <p class="pui-report-nav__label">目录</p>
  <ol>
    <li><a href="#chapter-01" aria-current="true"><span>01</span>授标建议</a></li>
    <li><a href="#chapter-02"><span>02</span>成本证据</a></li>
  </ol>
</nav>

<main data-pui-report-main>
  <section id="chapter-01" data-pui-section
    data-primary-object="decision-stage" data-density="open">...</section>
</main>
```

Use the packaged runtime to update `aria-current`, keep the active mobile link visible, and respect reduced motion. The report must remain fully navigable when JavaScript is unavailable.

## 4. Chapter composition

Treat each chapter as a designed field, not a stack of components.

Choose one composition per chapter:

- **title wall + evidence aperture** — large finding occupies one field; one chart or exact object opens beside or below it;
- **margin chapter + full-width object** — number and title stay narrow while the visual field spans the page;
- **split tension** — recommendation and reversal variable face each other in an unequal split;
- **filmstrip + pinned detail** — peer cards or stages move while one detail surface remains stable;
- **ledger + isolated verdict** — dense comparison resolves into one open recommendation;
- **timeline + margin notes** — events align to evidence or gates without a prose sidebar;
- **ranked cascade** — ranked options step down the page with one shared scale;
- **full-bleed signal field** — one saturated or dark chapter marks a genuine narrative turn.

Apply these rules:

- Use one dominant object in every chapter.
- Give the dominant object `55–75%` of the available visual area.
- Keep supporting text adjacent to the exact mark, row, stage, or threshold it explains.
- End the chapter with a decision consequence or a clear transition to the next question.
- Do not repeat the same column ratio, card count, or heading placement in consecutive chapters.
- Do not change more than two structural variables between adjacent chapters.

Structural variables are:

`heading position · column ratio · dominant-object scale · background field · reading direction`

Keep at least three continuity anchors unchanged:

`content width · baseline grid · type roles · color mapping · number format · rule weight · interaction states`

## 5. Whitespace choreography

Whitespace is active separation and emphasis. Use three scales deliberately.

### Macro whitespace

Controls transitions between acts and chapters.

- Use `96–128px` before an open chapter or narrative turn.
- Use `64–96px` between standard chapters.
- Allow one edge-to-edge field to interrupt the selected route's page field when the decision changes phase.
- Do not place a gray panel behind a section merely to manufacture separation.

### Meso whitespace

Controls relationships inside a chapter.

- Keep a title, thesis, and dominant object visibly related.
- Use `32–48px` between the chapter heading and its primary object.
- Use `24–32px` between sibling evidence objects.
- Increase space before a conclusion; decrease it within a comparison group.

### Micro whitespace

Controls scanning inside objects.

- Use `8px` between label and value.
- Use `12–16px` between a value and its consequence.
- Use `8–12px` between dense rows.
- Keep table rows compact but never below a comfortable touch or reading target when interactive.

Test whitespace by asking:

1. What does this gap separate?
2. What does this gap group?
3. Where should the eye stop?
4. Is the empty area balancing a focal object or merely filling the viewport?

Do not center every object inside generous padding. Asymmetry, edge alignment, crop, and measured tension often create stronger whitespace than uniform margins.

## 6. Card ontology and states

Declare every card with `data-object-kind`:

```html
<article class="pui-object-card" data-object-kind="supplier"
  data-pui-key="supplier-a" tabindex="0">...</article>
```

Allowed kinds:

`supplier · option · lane · scenario · exception · gate · action · evidence`

Use four states consistently:

1. **Rest** — identity, decisive value/state, and one consequence are visible.
2. **Preview** — hover/focus reveals comparison emphasis or a short basis without moving surrounding layout.
3. **Pinned** — click/Enter/Space persists selection and links the same object across chart, table, and notes.
4. **Expanded** — a deliberate control opens evidence, formula, or history; it is never triggered by hover alone.

Motion rules:

- Use one easing curve: `cubic-bezier(.2,.8,.2,1)`.
- Keep hover/focus transitions within `140–180ms`.
- Keep pin/expand transitions within `180–240ms`.
- Limit movement to `0–2px` or a `4–8px` internal reveal.
- Animate opacity, color, rule length, and small translation; avoid card flips, 3D tilt, spring overshoot, and layout reflow.
- Preserve card dimensions while previewing or switching basis.
- Disable nonessential motion under `prefers-reduced-motion: reduce`.

Card anatomy:

`identity → decision state/value → consequence → basis or action`

Do not use:

- nested cards;
- icon + heading + paragraph cards repeated as a section;
- a card for every metric;
- hover effects on noninteractive surfaces;
- different shadows or radii to imply importance.

## 7. Chart-and-text relationships

Choose one relationship for each chart:

- **Annotation-led** — write findings on the relevant point, bar, band, or threshold.
- **Margin evidence** — place source, unit, date, and caveat beside the chart edge.
- **Shared-axis narrative** — align short chapter notes to the same vertical or horizontal positions as the data.
- **Chart + decision ledger** — pair a relationship view with exact numbers, gates, or actions.
- **Linked master/detail** — use one chart as the overview and update one stable detail field.
- **Before/after aperture** — reveal proposal versus baseline without changing the chart scale.

Rules:

- The chart title states the question or finding; the caption states unit, basis, and period.
- Put the strongest finding closest to the mark that proves it.
- Keep commentary shorter than the chart is wide.
- Do not repeat every plotted value in prose.
- Do not place a decorative chart beside text that carries the actual analysis.
- Use the same `--ink` / `--accent` / optional `--accent2` mapping, rule weight, radius, and selected state as the rest of the report.
- Preserve the default recommendation, threshold, and static data fallback without interaction.

## 8. Controlled variation

Create variety through composition, not random styling.

Across a standard 6–8 chapter report:

- use two open chapters;
- use two or three dense chapters;
- use one transitional chapter;
- use at most one full-bleed dark or saturated field;
- use at most one KPI-style cluster;
- keep at least two chapters card-free;
- use at least three chapter compositions;
- reuse the same primary interaction grammar across the report.

Build a chapter score before authoring:

| Chapter | Role | Density | Composition | Dominant object | Interaction | Exit cue |
|---|---|---|---|---|---|---|
| 01 | threshold | open | title wall | decision stage | none | why |
| 02 | compare | dense | ledger + verdict | supplier ledger | linked pin | cost |
| 03 | challenge | transitional | split tension | gate matrix | details | conditions |

Reject a sequence when three adjacent rows share the same density, composition, or card count.

## 9. Original direction cues

No raster reference plates are packaged. This keeps the skill small and prevents accidental reuse of third-party or reference imagery. Preserve the strong v0.0.14 visual language through these abstract, non-exclusive cues:

- numbered chapters, a hard editorial grid, scale contrast, and dark/light cadence;
- ruled contents, asymmetry, generous white space, and a restrained primary color;
- controlled variation, diagram-led chapters, and one deliberate focal field;
- a single pop color, large numeric hierarchy, and calm card-free composition.

Use the lightweight original SVG previews in `assets/procurement-visual-kit/style-previews/` for internal direction selection only. Borrow at most two abstract cues, then produce a new composition. Never trace or reproduce third-party copy, brands, distinctive layout, exact palette sequence, or motif.

## 10. Curatorial brief

```markdown
## Procurement Curatorial Brief
- Visitor route:
- Spatial acts:
- Navigation model:
- Chapter numbering:
- Chapter score:
- Open chapters:
- Dense chapters:
- Transitional chapter:
- Card-free chapters:
- Dominant object and area share for each chapter:
- Continuity anchors:
- Variables allowed to change:
- Whitespace pauses:
- Card kinds used:
- Card rest / preview / pinned / expanded behavior:
- Chart-and-text relationship for each chart:
- Reference cues borrowed:
- Mobile navigation:
- Print navigation:
```

## 11. Acceptance

Confirm:

1. The report has an explicit entrance, orientation, analytical route, decision room, and exit.
2. Reports longer than six major sections include a contents plate, sticky rail, chapter strip, or hybrid navigation.
3. Navigation links use stable deep-link targets and expose the current chapter accessibly.
4. Every chapter resolves one question and has one dominant object.
5. The dominant object occupies more area than explanatory prose.
6. Consecutive chapters do not repeat the same composition, density, and card count.
7. Adjacent chapters change no more than two structural variables.
8. Macro, meso, and micro whitespace each express a named relationship.
9. At least two chapters are card-free in a standard report.
10. Every card declares a real object kind and exposes a useful rest state.
11. Preview and pin states do not reflow surrounding content.
12. Expanded detail requires an explicit action and remains available to keyboard and touch users.
13. Chart annotations are attached to evidence rather than repeated in detached prose.
14. One interaction and selection language spans cards, tables, charts, and navigation.
15. The report remains readable, navigable, and decision-complete without animation or JavaScript.
