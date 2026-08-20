# Radar layout blueprints

## Contents

1. Runtime augmentation rule
2. Framework pairing
3. Uniform random selection
4. Six original HTML compositions
5. Dynamic UI companions
6. Responsive and print behavior
7. Blueprint completion gate

## 1. Runtime augmentation rule

Run `scripts/select_visual_style.py` before invoking `html-report` and pass its blueprint as
composition context. Preserve that
runtime's scaffold, canonical tokens, fonts, relative paths, chart loader, citations, responsive
foundation, and validation. The radar blueprint enhances the visible composition inside the valid
runtime output; it is not a second shell.

Reject or replace:

- a generic report header followed by three equal KPI cards;
- a dashboard shell with navigation, breadcrumbs, sidebars, or a toolbar unrelated to the decision;
- repeated rounded cards containing every paragraph;
- identical two- or three-column sections from top to bottom;
- a generic hero title, subtitle, and decorative gradient;
- framework sample copy, sample metrics, default colors, and placeholder charts.

The final DOM must visibly express the selected framework's navigation and chapter rhythm plus the
selected blueprint's grid, focal object, density rhythm, and section sequence. A palette swap on the
runtime's default scaffold does not count.

## 2. Fixed framework pairing

The asset manifest pairs each style with one framework. Use the pair returned by the script:

| Blueprint | Framework |
|---|---|
| Verdict Sheet | Index Gate |
| Evidence Object | Reading Rail |
| Swiss Trace | Reading Rail |
| Decision Mosaic | Index Gate |
| Signal Stage | Exhibit Path |
| Alert Cut | Exhibit Path |

Do not select or change the framework from report length, evidence shape, or content. Adapt the
number of chapters and navigation density inside the returned framework.

## 3. Uniform random selection

The six blueprints form one unfiltered pool. `scripts/select_visual_style.py` selects each with exact
probability `1/6` using a system random source. No style has a default, weight, eligibility gate, or
content affinity.

Run once per report. Do not filter, weight, reroll, avoid repetition, honor a model preference, or
replace the returned style. The descriptions below are implementation instructions only.

## 4. Six original HTML compositions

### A. Verdict Sheet

**Composition intent:** open editorial conclusion with a focal exhibit and compact signal deck.  
**Bucket:** light editorial.  
**Page field:** pure white (`--bg: #ffffff`).  
**Geometry:** flat white editorial sheet; no card shell.

Desktop sequence:

1. compact run metadata;
2. one short display verdict occupying 7 of 12 columns;
3. decision note occupying the remaining 5 columns;
4. one full-width interactive plot;
5. a concise signal deck synchronized with the plot;
6. dense source ledger;
7. final act / validate / watch line.

The hero contains no more than the verdict and one support sentence. Section changes use whitespace
and a full-width neutral rule, not containers around every block. Radius is `0–2px`.

### B. Evidence Object

**Composition intent:** asymmetric claim-and-evidence object with source-bound annotations.  
**Bucket:** light editorial / object-led.  
**Page field:** pure white (`--bg: #ffffff`).  
**Geometry:** asymmetric 5/7 split.

The 5-column side contains a short display verdict, effective date, and one action. The 7-column
side contains the real product screenshot, documented table, source excerpt, or interface object
with numbered annotations. Below, one evidence strip connects annotations to implications.

The artifact—not a stock 3D object—carries visual weight. Only the artifact frame may use a large
`20–28px` radius and one soft shadow. Supporting evidence remains flat. Never distort, recolor, or
crop away information needed to verify the claim.

### C. Swiss Trace

**Composition intent:** strict grid with one quantitative trace and dense exact ledger.  
**Bucket:** high-contrast grid.  
**Geometry:** strict 12-column grid, black rules, `0px` radius.

Use one large title block, one compact legend, then a full-width interactive matrix or timeline.
The lower half becomes a source-index grid with deliberately dense rows. Alternate very open
macro-sections with tightly packed evidence, rather than applying one gap everywhere.

Geometric marks encode state only when a text label also exists. No decorative collage, archival
image, or technical line may imply evidence that is not actually present.

### D. Decision Mosaic

**Composition intent:** one dominant thesis module plus unequal supporting modules.  
**Bucket:** high contrast on a pure-white page field.  
**Page field:** pure white (`--bg: #ffffff`); do not switch the page to dark or tinted.  
**Geometry:** one dominant module spanning at least half the canvas plus two or three subordinate
modules of unequal size.

The dominant module carries the thesis and primary interactive chart. A coordinated signal deck
uses one concise card per qualifying signal; one active card may span two columns while peers remain
compact. Supporting modules contain one implication or action each. Do not add modules merely to
complete a rectangle. Radius is either `0–4px` for an editorial system or `12–16px` for a product
system—never a mixture.

### E. Signal Stage

**Composition intent:** near-black executive field with one bright evidence stage and decision rail.  
**Bucket:** dark executive.  
**Geometry:** one bright evidence stage on a near-black field plus a narrow decision rail.

Use one short two-line display statement, one interactive plot, and a three-step impact path. Dense
citations move to a white print-safe evidence sheet below. Radius is `10–14px` or zero, selected
once. No dark gray or chromatic dark text may appear on the dark field.

### F. Alert Cut

**Composition intent:** one-screen decision cut followed by one exact evidence table.  
**Bucket:** light editorial or high contrast.  
**Geometry:** one-screen decision cut followed by one evidence table.

The first screen contains: change, response window, exposure, one action, and one uncertainty.
Below it, one compact exact-value table carries dates and sources. No navigation, chart gallery,
monthly-history section, or decorative hero is allowed.

## 5. Dynamic UI companions

The original uniform random style receipt pairs the HTML blueprint with exactly one companion. Do
not choose a companion from the evidence or draw again.

| HTML blueprint | Paired companion | Compact signature |
|---|---|---|
| Verdict Sheet | Verdict Gate | wide focal field, right verdict gate, one trigger line |
| Evidence Object | Evidence Lens | large evidence object, three anchors, inspection rail |
| Swiss Trace | Trace Index | strict coordinate field, direct labels, source index |
| Decision Mosaic | Decision Prism | one dominant plane and one bifurcated evidence rail |
| Signal Stage | Signal Theatre | focal stage and narrow act/validate/watch cue rail |
| Alert Cut | Response Cut | diagonal response-window measure and exact evidence line |

Read `dynamic-ui-companions.md` for the authority boundary and adaptation order. The built-in
Dynamic UI runtime still chooses the scene and ready material from the factual relationship. The
companion only arranges that material inside the paired geometry and maps selected identity values
onto the runtime's existing tokens.

Do not reproduce the HTML header, report navigation, source ledger, or all signals in the widget.
Do not embed the guide SVG. The widget has one focal interaction and at most one supporting note.

## 6. Responsive and print behavior

- Collapse asymmetric grids in narrative order, not DOM convenience.
- Convert the Reading Rail to a compact horizontal chapter index or native disclosure on small
  screens; never leave a narrow sticky sidebar beside a squeezed article.
- Print Index Gate as a real contents page with page-independent anchor labels. Print Reading Rail
  as a compact contents block before the first analytical chapter.
- Keep display-title phrase spans intact on mobile; shorten the display copy when needed.
- Convert hover-only detail to tap/focus behavior.
- Preserve exact values, source links, status labels, and uncertainty in print.
- A dark report prints dense evidence on white and uses black text.
- Do not turn desktop modules into a long stack of indistinguishable rounded cards.

## 7. Blueprint completion gate

Before delivery, verify:

1. the selected framework and blueprint are expressed in the DOM and CSS;
2. the opening is not the runtime's generic header/KPI-card scaffold;
3. one module clearly dominates;
4. repeated modules have a content reason and do not form a filler card wall;
5. radius follows the selected blueprint;
6. the display title satisfies the word-count and semantic-wrap rules;
7. the HTML and Dynamic UI share the same visual identity;
8. interactive charts expose exact evidence through hover/focus and useful clicks;
9. print and mobile rules preserve reading order;
10. navigation state, card state, chart state, and evidence disclosure do not contradict one another;
11. no system sample content or stale placeholder remains.
