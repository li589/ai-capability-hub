# Procurement enhancement for the built-in Dynamic UI

Use this for the mandatory compact inline preview that accompanies every substantive procurement delivery. It enhances the current built-in `dynamic-ui` skill; it does not create a report, working file, dashboard, or separate app.

## Built-in boundary

Before creating the widget, load:

1. the current built-in `dynamic-ui` `SKILL.md`;
2. the routed scene;
3. `templates/manifest.json`;
4. the selected template's `template.md`;
5. the built-in visual-token reference.

Let the built-in skill own widget structure, tool protocol, template constraints, responsiveness, accessibility, and host light/dark behavior. Call the real widget tool as the next user-visible action. Never print a fake tool payload or `mode: panel`.

Then read `assets/procurement-dynamic-ui/dynamic-ui-layouts.json` and the selected route's `dynamic_ui_companion` SVG. These procurement assets are composition companions only:

- use the manifest to select one layout family that matches the focal relationship;
- use only the matching numbered panel in the companion as a proportion, alignment, rhythm, and support-block reference;
- keep the built-in scene, ready template, template data boundary, token roles, fallback, tooltip, root selector, responsiveness, and interaction contract authoritative;
- never embed the companion SVG in the widget, copy its sample labels or marks, create a procurement template ID, or skip a matching ready material because a custom SVG looks easier;
- translate the companion through built-in spacing, type, radius, surface, chart-series, and host-theme tokens rather than copying literal SVG coordinates or colors.

The selected route remains the only random choice. Do not reroll for Dynamic UI. The focal relationship selects the companion panel and built-in material by intent; randomizing an incompatible chart or template would violate the system scene router.

Create the widget only after the route-manifest identity and stabilized report facts are fixed. Do not inspect or parse the generated HTML to recover that identity. Do not claim completion until the real widget runtime confirms success.

## Mandatory preview rule

For every substantive result with an HTML report and editable Markdown companion, emit exactly one Dynamic UI preview through the real widget tool.

Choose the smallest honest focal point supported by the evidence. Do not omit the widget because the report contains a related chart. For a narrow definition or one arithmetic answer that does not require the delivery stack, do not force a widget. If the real tool is unavailable, deliver both files and explicitly state that the inline preview could not be emitted.

The preview is not a miniature report, working-file checklist, or artifact-status card. It must answer one focal question.

## Scene and template routing

Use the built-in scene router first. These are procurement defaults, not substitutes for reading the selected template:

| Focal question | Procurement layout family | Scene / likely template |
|---|---|---|
| Which 2–4 finalists should advance? | `award-frontier` | comparison and decision / `comparison-cards`, or `scatter-chart` when two numeric axes are the relationship |
| How has normalized price changed? | `price-pulse` | data visualization / `line-trend` |
| Where is supplier performance or risk concentrated? | `risk-lens` | data visualization / `heatmap-chart`, bounded radar, or comparison cards |
| Which inventory items hit a critical date first? | `exception-queue` | comparison and decision / compact table, cards, or `gantt-chart` |
| Which lane balances cost and time? | `landed-flow` | data visualization / `scatter-chart`, grouped bars, or comparison cards |
| How do verified weighted impacts flow? | `landed-flow` | data visualization / `sankey-chart` only when real non-negative weights exist |
| What action sequence or gate is due now? | `execution-track` | architecture and flow / `gantt-chart`, sequence, tree, or node-flow |
| Where does the sourcing pipeline narrow? | `execution-track` | data visualization / `funnel-bar-chart` only when attrition itself is the focal question |
| Which priorities are unusual? | `award-frontier` or `exception-queue` | data visualization / `scatter-chart`, or a compact ranked register |
| Where is topic intensity concentrated? | `risk-lens` | data visualization / `heatmap-chart` |
| How do two options compare on identical dimensions? | `risk-lens` | radar only when dimensions share a defensible scale |

Keep to the built-in density limits: one focal point, usually 2–4 options/series, and one useful interaction. Consolidate long tails into “Other” when the template requires it.

Vary the focal encoding with the question. Prefer a ranked dot/lollipop, dumbbell, bullet strip, small multiple, cost bridge, threshold scatter, time-to-impact strip, route strip, or gate matrix when the selected template can express it. Do not default to funnels, radar charts, donuts, or gauges.

## Shared visual identity

Treat the route-manifest identity and stabilized facts used to author the HTML report as the source of truth. Pass that same identity snapshot into the widget without rerouting:

- selected route ID and its composition grammar;
- selected route's companion asset, matching layout-family ID, and route-specific composition transform;
- exact HTML `--bg`, `--bg2`, `--ink`, `--muted`, `--rule`, `--accent`, and `--accent2` values;
- primary, auxiliary, and optional pop-color meanings;
- corner model and depth rule;
- edge-treatment invariant and permitted emphasis grammar from the selected route manifest;
- state vocabulary and evidence labels;
- selected entity/signal key and default decision state.

Map the snapshot semantically:

- HTML `--accent` → built-in `--brand` or the primary chart series;
- the route's auxiliary role → secondary series or one supporting surface, never a new default purple/blue or green;
- HTML `--accent2` → exception/reversal emphasis only when that is its HTML meaning;
- HTML neutral roles → widget surface, text, muted, and border tokens;
- HTML selected entity key → the widget's initially selected or pinned object.

Do not choose another route, substitute a template's default palette, or reinterpret state colors. The widget may use a denser composition than the HTML report, but its color roles, geometry, visual personality, selected object, facts, calculations, confidence, and recommendation must remain the same.

When the selected built-in material offers a brand `border-left`, colored header edge, or accent frame as an optional focus treatment, apply the procurement user's explicit override: keep the entire frame neutral and complete, then use a badge, text cue, inset marker, or chart mark. Preserve keyboard visibility with a complete high-contrast neutral focus outline or neutral full-frame border. This adapts an optional visual state; it does not replace the built-in component, tokens, or interaction contract.

Keep host light/dark support. Translate the same route into each host theme rather than forcing an identical page field. On dark surfaces, explicitly set high-contrast foregrounds for body text, muted text, labels, axes, and controls; never place dark gray, navy, burgundy, dark green, or dark purple text on a dark surface.

Use neutral cards. Do not fill every supplier or KPI card with a brand color. For a recommended option, use typography, spacing, a compact badge, marker, symbol, selected state, complete neutral border, or full-surface fill. Keep every compact mark inside the content padding and visibly separated from all frame edges.

Never attach or simulate a colored band, rail, strip, or partial accent edge on the top, bottom, left, or right of a card, cell, sidebar, header, topbar, navigation item, callout, table wrapper, figure, or page frame. This explicitly prohibits physical and logical one-sided borders, edge-anchored pseudo-elements, narrow nested children, inset shadows, narrow gradients, background images, masks, SVG rails, and partial colored outlines. Reject the familiar `tinted rectangle + colored left rail + label + paragraph` composition before building the widget.

## Semantic consistency with Markdown

Use the same option names, figures, units, evidence states, gate labels, and recommendation posture as the editable workpaper. Visual matching is required only between HTML and Dynamic UI; Markdown remains plain text.

## Visual discipline

- no gradients, glow, glass, noise, or decorative artwork;
- at most three chromatic hues across the widget—one primary, one auxiliary, and one optional pop color—and no more than four chart series;
- preserve missing values as `N/A`; never coerce them to zero;
- do not introduce facts, calculations, confidence, or recommendations that are absent from the HTML report;
- do not copy the HTML title, navigation, chapter list, complete signal list, or source ledger;
- no physical or logical one-sided colored border, edge pseudo-element, nested rail, inset shadow, narrow gradient, background image, mask, SVG strip, or partial colored outline on any bounded surface;
- readable foreground on every dark or chromatic mark or surface;
- one visual hierarchy, compact spacing, tokenized radius/type;
- direct labels and symbols before extra colors;
- never rely on red/green alone;
- do not use Emoji as icons;
- require hover, keyboard focus, and tap behavior; a click must pin a comparison, switch evidence, or trace an impact rather than merely animate;
- keep recommendation rationale in surrounding chat, not inside a chart-only UI.

## Dynamic UI Brief

```markdown
## Procurement Dynamic UI Brief
- Focal question:
- Audience and time window:
- Report identity / route ID:
- Built-in scene:
- Selected built-in template:
- HTML layout blueprint:
- Procurement companion asset and numbered panel:
- Procurement layout-family ID:
- Route-specific composition transform:
- Exact HTML theme tokens:
- Primary / auxiliary / optional pop semantics:
- Corner model and depth rule:
- Edge-treatment invariant from route manifest:
- Permitted emphasis grammar and inset separation:
- State vocabulary and evidence labels:
- HTML selected entity key and default state:
- Brand / primary-series mapping:
- Secondary-series mapping:
- Exception / reversal mapping:
- Options, series, or milestones:
- Unit / currency / period / basis:
- Missing values and uncertainty:
- One interaction:
- Recommendation cue without an edge band:
- Conclusion that remains in surrounding chat:
```

## Acceptance

1. A real widget tool call was used.
2. The widget answers one procurement question and is useful inline.
3. The routed scene, manifest, template, and token references were followed.
4. The selected procurement companion and layout-family panel informed composition without being embedded or copied.
5. Both host light and dark modes remain readable.
6. Surfaces follow the selected route; saturated fields remain deliberate and limited rather than becoming a color-per-card system.
7. No bounded surface uses a physical or logical one-sided colored border, edge pseudo-element, nested rail, inset shadow, narrow gradient, background image, mask, SVG strip, or partial colored outline.
8. Route ID, token values, geometry, depth, state vocabulary, and selected entity match the HTML identity snapshot.
9. Terms, values, evidence states, calculations, confidence, and recommendation posture match the HTML report and Markdown companion.
10. No template-default palette, missing-value coercion, Emoji, or invented information appears.
11. The selected interaction creates a real persistent state change and remains usable by pointer, keyboard, and touch.
12. Any compact badge, dot, symbol, or underline stays visibly separated from every frame edge.
