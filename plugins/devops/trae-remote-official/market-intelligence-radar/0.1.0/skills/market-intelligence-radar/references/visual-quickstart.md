# Uniform random visual route

Use this route for every visual report. It enhances the current `html-report` runtime; it never
replaces its scaffold, tokens, fonts, chart loader, citations, responsive behavior, or validation.

## 1. Select exactly once

Before reading the evidence shape or forming a visual preference, run:

```bash
python3 scripts/select_visual_style.py
```

The script validates `assets/radar-visual-kit/styles.json` and
`assets/radar-visual-kit/dynamic-ui-companions/manifest.json`, verifies all twelve SVG assets, and
selects one paired entry using a system random source. Each HTML/Dynamic UI pair has exact
probability `1/6`.

Accept the returned `style_id`, `framework`, `page_background`, `asset`, and
`dynamic_ui_companion` as authoritative. Draw once only. Never:

- filter the pool by report type, evidence shape, signal count, brand, or content;
- apply weights, eligibility rules, taste, or a preferred default;
- avoid or favor the previous style;
- reroll because the result appears difficult or repetitive;
- replace the returned framework or asset.
- route or redraw the Dynamic UI companion from text, evidence shape, report type, or preference.

Record `selection_id`, `style_id`, `framework`, `asset`, and companion ID in the internal Radar
Style Contract. Set the matching HTML audit attributes on the root `<html>`.

## 2. Complete six-style inventory

| Style ID | Framework | Page background | HTML asset | Dynamic UI companion |
|---|---|---|---|---|
| `verdict-sheet` | `index-gate` | `#ffffff` | `verdict-sheet.svg` | `verdict-gate.svg` |
| `evidence-object` | `reading-rail` | `#ffffff` | `evidence-object.svg` | `evidence-lens.svg` |
| `swiss-trace` | `reading-rail` | `#fafafa` | `swiss-trace.svg` | `trace-index.svg` |
| `decision-mosaic` | `index-gate` | `#ffffff` | `decision-mosaic.svg` | `decision-prism.svg` |
| `signal-stage` | `exhibit-path` | `#111210` | `signal-stage.svg` | `signal-theatre.svg` |
| `alert-cut` | `exhibit-path` | `#fff4df` | `alert-cut.svg` | `response-cut.svg` |

Inspect only the selected HTML SVG and its paired companion SVG for proportions, rhythm, and palette
roles. Never copy, embed, trace, or expose either guide in a report or widget. Read
`dynamic-ui-companions.md` before adapting the companion.

## 3. Lock the visual contract

Decide only the evidence-dependent contents inside the selected style:

- one reader decision and one focal relationship;
- one primary color, one secondary color, and at most one optional pop color;
- one neutral ink family for page, surface, text, muted text, and rules;
- one primary chart only when at least three comparable data points support it.

Use `html-report`'s seven canonical token names. Treat five as neutral roles and two as chromatic
roles; the token count is not the color count.

## 4. Apply the restrained style

- Use no more than three chromatic colors across the page: primary, secondary, optional pop.
- Derive all neutrals from one ink family; do not mix unrelated warm, cool, blue, or green grays.
- Use color for focus, selection, or one emphasized field—not for decorating every section.
- Never put a colored edge strip, colored partial border, or accent border on a card, sidebar/rail,
  top bar/header, navigation item, table frame, section, or heading. This includes inset shadows.
- Prefer whitespace, neutral rules, full-field inversion, contained marks, and typography.
- Use at most one shadow recipe and only for one true floating or focal object.
- Use no generated decorative illustration, ambient gradient, glow, generic 3D object, or mood image.
- Use no external visual-inspiration search during report production.

## 5. Build with minimal visual work

1. Pass the dated basename, random selection receipt, and compact visual contract to `html-report`.
2. Keep the runtime's Solid mode unless the user or verified brand system requires another mode.
3. Add the smallest radar layer that faithfully expresses the selected guide.
4. Use semantic HTML for lanes, comparisons, and decision rails.
5. Add ECharts only for a real quantitative relationship; use one primary chart by default and give
   it a same-slot system-native HTML/CSS or accessible SVG fallback instead of failure text.
6. Add Mermaid only for genuinely branching topology.
7. Check relative files and JavaScript syntax, then run `report_visual_audit.py`.
8. Do not invoke the built-in HTML validator, start a local server, open a browser, use browser
   automation, capture screenshots, or perform rendered visual QA.
9. After HTML passes, let the built-in Dynamic UI runtime choose its scene and ready material, then
   adapt that material into the already-selected companion skeleton. Do not create a parallel
   widget template.

## 6. Load deeper implementation rules only when needed

Read `curatorial-framework.md`, `visual-enhancement.md`, and `layout-blueprints.md` when any applies:

- monthly review or more than six signals;
- substantial verified brand customization;
- more than one primary analytical visual is necessary;
- a dense Reading Rail, dark executive field, or complex interactive state needs deeper rules.

Deeper rules adapt content inside the selected style. They never authorize a reroll.
