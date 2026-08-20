# Procurement style routing

Use this reference before reading a route's palette or preview. The six routes are peers; none is the default.

## Selection

1. If the user explicitly requests a visual direction, choose the closest route and do not randomize.
2. Otherwise run `python3 scripts/select_style_route.py` exactly once.
3. Keep the returned route ID, seven tokens, corners, depth, composition, chart grammar, Dynamic UI companion path, edge treatment, and emphasis grammar as the shared HTML/Dynamic UI identity snapshot. Do not reroll because another route feels easier or more familiar.
4. Read only the selected preview and kit first. Use another route only when the selected route violates an explicit accessibility, print, or brand constraint; record that reason and choose once from the remaining routes.
5. Never expose the route name, preview filename, routing command, or selection note in the report.

Do not infer the route from procurement topic. AI sourcing, price analysis, supplier risk, logistics, and inventory are all eligible for all six routes. This prevents repeated blue/orange output.

For reproducible tests only, pass a seed: `python3 scripts/select_style_route.py --seed "<test-id>"`.

## Global route invariant

Every route carries the same non-negotiable surface rule. Before authoring HTML or Dynamic UI, copy the selected manifest's `edge_treatment` and `emphasis` fields into the production identity snapshot.

No bounded surface may use a chromatic strip on only one edge. The prohibition covers physical borders, logical borders, edge-anchored pseudo-elements, narrow nested children, inset shadows, narrow gradients, background images, masks, SVG rails, and partial colored outlines. A subtle, translucent, short, rounded, or route-matched rail is still prohibited.

Use type, spacing, alignment, a complete neutral border, a full-surface flat fill with a tested foreground, or a compact mark inset from every frame edge. Never fall back to `tinted rectangle + colored left rail + label + paragraph`.

## Six equal-weight routes

| ID | Visual identity | Composition grammar | Chart grammar | Asset kit |
|---|---|---|---|---|
| `precision-ledger` | white, cobalt, restrained rust | ruled ledger, asymmetric evidence columns, hard rectangles | cobalt primary series, ink-opacity peers, rust exception only | `style-kits/precision-ledger.svg` |
| `product-stage` | white, electric blue, deep ink | large stage, named rounded objects, generous gaps | direct labels, one blue focus series, dark decision block | `style-kits/product-stage.svg` |
| `signal-docket` | white/black, vermilion, muted gold | large editorial type, alternating light/dark acts, strict docket rows | vermilion decision marks, gold threshold, neutral peers | `style-kits/signal-docket.svg` |
| `mono-audit` | black, white, one gray family | strict grid, line-weight hierarchy, card-free evidence | hatch/outline/marker semantics without chromatic color | `style-kits/mono-audit.svg` |
| `acid-registry` | pure-white field, acid chartreuse, black | compact modular registry, condensed display blocks, irregular spans | chartreuse focus marks, black comparison field, outlined peers | `style-kits/acid-registry.svg` |
| `night-circuit` | near-black field, emerald surface, cyan, optional yellow | dark editorial stage, offset modules, large numbered acts | cyan primary, emerald supporting surface, yellow reversal only | `style-kits/night-circuit.svg` |

## Complete-kit rule

Every route has:

- one full-page preview in `style-previews/`;
- one lightweight SVG symbol kit in `style-kits/` containing a route marker, pattern, focus field, and chart mark;
- one lightweight Dynamic UI companion SVG containing six numbered procurement layout panels—award frontier, price pulse, risk lens, exception queue, landed flow, and execution track;
- one shared machine-readable Dynamic UI companion manifest in `assets/procurement-dynamic-ui/dynamic-ui-layouts.json` defining built-in scene/template compatibility and route-specific composition transforms;
- one complete machine-readable identity in `style-routes.json` containing all seven HTML tokens, geometry, depth, composition, chart grammar, edge treatment, and permitted emphasis grammar;
- palette, composition, type, corners, and chart rules in `procurement-visual-enhancement.md`.

Do not mix the preview from one route with the kit or palette from another. Do not discard a selected route merely because its kit requires a different composition.

For Dynamic UI, do not randomize again. Read the already selected route's companion, choose the numbered panel by focal relationship, and keep the built-in Dynamic UI scene and ready-template router authoritative. The companion is a layout reference, not a widget asset or replacement template; never embed it or copy its sample marks.

The supplied user references are not packaged. The six kits are original SVG assets built from abstract cues only; never trace reference imagery, logos, people, copy, or distinctive layouts.
