# Dynamic UI — Examples Index

20 reference HTML widgets covering the most common visual scenarios developers encounter when working with AI assistants. **Use them as layout and interaction blueprints — copy the technique, generate fresh content.**

## How to use

1. Match your task to the closest scenario below
2. Read the matching example file — focus on CSS structure, layout grid, color usage, and interaction patterns
3. Adapt the layout for your content. Change data, labels, colors — keep the structural approach.
4. **Do not copy content verbatim. Copy the structural approach, then fill with task-specific data.**

---

## 01 · Exploration & Planning

Three demos for when the user is exploring options, comparing approaches, or planning implementation.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 01 | `01-exploration-approaches.html` | Three code approaches side-by-side with trade-offs | 3-column cards with colored top bars (sky/indigo/amber), code snippets, mint/coral pro/con lists, recommendation box |
| 02 | `02-exploration-visual-directions.html` | Four visual design directions rendered live | 2×2 grid cards with distinct accents, mini previews, click-to-select interaction with ✓ badge |
| 03 | `03-implementation-plan.html` | Structured plan with milestones, data flow, risks | Timeline dots (sky→indigo→violet→mint), SVG data flow diagram, risk table with severity pills |

**Trigger**: "compare approaches / which way should I go / show me options / make a plan / implementation plan"

---

## 02 · Code Review & Understanding

Three demos for annotated diffs, PR writeups, and module maps.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 04 | `04-code-review-pr.html` | Annotated PR diff with severity tags and file nav | Diff lines (mint add / coral del), margin annotations with severity pills, file sidebar with risk dots |
| 05 | `05-code-review-writeup.html` | PR author's guide for reviewers | TL;DR box, before/after cards, expandable file sections, numbered review-focus list |
| 06 | `06-module-map.html` | Package architecture as boxes and arrows | SVG dependency graph, 4-layer coloring (sky/indigo/mint/amber), hot path highlight, entry point sidebar |

**Trigger**: "review this PR / explain this module / how does this code work / architecture overview"

---

## 03 · Prototyping

Two demos for micro-interactions and drag-and-drop prototypes.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 07 | `07-prototype-animation.html` | Task completion animation with tunable controls | Click-to-play demo, duration/easing sliders, keyframe timeline, Copy CSS button |
| 08 | `08-prototype-interaction.html` | Drag-to-reorder sidebar prototype | HTML5 drag/drop, ghost opacity + tilt, drop indicator, design decision callouts |

**Trigger**: "prototype this interaction / show me the animation / what does this feel like"

---

## 04 · Diagrams & Illustrations

Two demos for SVG illustrations and interactive flowcharts.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 09 | `09-svg-illustrations.html` | Three technical SVG illustrations with download | Flat-fill inline SVGs, colored nodes per category, Download SVG buttons, palette reference |
| 10 | `10-flowchart.html` | CI/CD pipeline flowchart with clickable nodes | SVG flowchart, decision diamonds, pass/fail colored paths, click for details panel, legend |

**Trigger**: "draw a diagram / flowchart / pipeline / architecture diagram / illustrate this concept"

---

## 05 · Decks & Presentations

One demo for slide decks with keyboard navigation.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 11 | `11-slide-deck.html` | 5-slide quarterly review with ←→ navigation | `<section>` per slide, keyboard nav, slide counter, opacity+translateX transitions, varied layouts per slide |

**Trigger**: "make slides / presentation / deck / a few pages to present"

---

## 06 · Research & Learning

Two demos for feature explainers and interactive concept teaching.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 12 | `12-feature-explainer.html` | How a feature works: TL;DR + steps + tabbed code + FAQ | Collapsible steps, tabbed code (YAML/Go/HTTP), amber gotcha cards, toggle FAQ |
| 13 | `13-concept-explainer.html` | Interactive concept with live diagram and glossary | Two-column + sticky glossary, animated SVG ring, hover-linked terms, comparison table |

**Trigger**: "explain how X works / teach me / what is X / break down this concept"

---

## 07 · Reports & Status

Two demos for weekly status reports and incident postmortems.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 14 | `14-status-report.html` | Weekly engineering status with KPIs and velocity chart | KPI cards with trend deltas, shipped table with risk dots, SVG bar chart, carryover pills |
| 15 | `15-incident-timeline.html` | SEV-2 postmortem with timeline and action items | Severity pill, phase-colored timeline dots, terminal log block, action checklist with owners |

**Trigger**: "write a report / status update / weekly summary / incident postmortem / what happened"

---

## 08 · Custom Editors

Three demos for interactive editing interfaces with export capabilities.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 16 | `16-triage-board.html` | Drag tickets across Now/Next/Later/Cut columns | 4 kanban columns, draggable cards with type/size pills, point totals, Copy as Markdown export |
| 17 | `17-feature-flags.html` | Toggle flags, see dependency warnings, copy diff | Collapsible groups, toggle switches, rollout sliders, dependency warnings, JSON diff export |
| 18 | `18-prompt-tuner.html` | Edit prompt template with live multi-sample preview | Left editor + right preview split, highlighted {{slots}}, live re-render, token count |

**Trigger**: "make an editor / let me configure / triage board / feature flags / tune this prompt"

---

## 09 · Dashboards & Comparisons

Two demos for metrics overview and technology comparison.

| # | File | One-liner | Key technique |
|---|------|-----------|---------------|
| 19 | `19-metrics-dashboard.html` | API monitoring with KPIs, area/bar/donut charts | 4 KPI cards, 2×2 SVG chart grid (area/bar/donut/table), filter dropdown, gradient accents |
| 20 | `20-comparison-matrix.html` | Technology options with pros/cons and recommendation | 3-column option cards, code snippets, comparison table with colored cells, verdict box |

**Trigger**: "show me metrics / dashboard / monitoring / compare X vs Y / which should I use"

---

## Quick reference: reading an example

Focus on these sections when reading any example file:

1. **CSS variables used** — which `--color-*` ramps, which `--font-*`, which `--border-radius-*`
2. **Layout structure** — grid template, flex direction, max-width
3. **Signature elements** — eyebrow placement, accent bars, pills, metric cards
4. **Color assignment** — how each category/status maps to a color ramp
5. **Interaction** — event listeners, animations, export functions

**Do not copy content verbatim. Copy the structural approach, then fill with task-specific data.**
