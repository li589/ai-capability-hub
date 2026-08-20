# Ecommerce visual enhancement for system html-report

## Contents

1. Purpose and renderer boundary
2. Selection model
3. Page geometries
4. Visual systems
5. Weighted visual variation
6. Typography
7. Summary patterns
8. Components and hierarchy
9. Charts and business diagrams
10. Interaction
11. Story routing
12. Evidence expression
13. Ecommerce visual assets
14. Lightweight verification

## 1. Purpose and renderer boundary

Use this reference every time HTML is routed from `omnichannel-commerce-assistant`. Produce a high-end e-commerce design brief for the current system `html-report`; do not maintain HTML templates, fonts, libraries, or renderer assets in this package.

The system renderer is plan-driven, not tied to fixed named templates. It already owns scaffolding, local fonts/runtime assets, CSS variables, ECharts, Mermaid, responsive behavior, citations, and HTML/CSS/JS authoring. This enhancement owns the commercial visual direction: page geometry, visual system, hierarchy, summary form, component grammar, chart/diagram form, interaction restraint, anti-repetition, and a small set of optional original e-commerce SVG primitives.

Follow the system renderer when mechanics conflict. Never copy another design library's template or source code; use only transferable design principles.

## 2. Selection model

Do not route every report to one shell. Select six independent dimensions:

1. **Scene spine** — decision sequence and evidence story.
2. **Page geometry** — long reading page, wide storyboard, hybrid, or navigator.
3. **Visual system** — palette + type personality + geometry + signature device.
4. **Depth mode** — intentionally flat or intentionally layered; never a timid midpoint.
5. **Summary pattern** — one concise opening form, not a universal card.
6. **Diagram language** — editorial HTML/CSS process, ECharts, or restrained Mermaid.

For reports with five or more sections or three or more visuals, require the system renderer to create `plan.md` and include:

```markdown
## Ecommerce Visual Brief
- **Decision**: [decision the reader must make]
- **Scene spine**: [name]
- **Page geometry**: [name]
- **Visual system**: [name]
- **Visual bucket**: [Light / High contrast / Dark]
- **Depth mode**: [Flat / Layered]
- **Summary pattern**: [name]
- **Diagram language**: [HTML/CSS process / ECharts / Mermaid / none]
- **Interaction level**: [print-first none / restrained 1–4]
- **Density**: [reading-first / presentation-like / hybrid]
- **Selection basis**: [audience + evidence shape + density + lightweight variation]
- **Primary visual**: [one visual carrying the main argument]
- **Recent visual avoided**: [immediate prior system in this task, or none]
- **Surface pairs**: [surface → foreground pairs, including inverse cards]
- **Color budget**: [one primary hue family + neutrals + one semantic signal]
- **Type scale**: [five allowed sizes plus optional caption]
- **H1 semantic chunks**: [largest-title phrases that may wrap only between chunks]
- **Asset choice**: [asset path or none]
- **Summary mark**: [none or abstract mark ID + placement]
- **Clarity guardrail**: [what must remain visually dominant and readable]
- **Explicit bans**: left-accent cards; filled evidence badges; long summary prose; generic engineering flowchart
```

Do not default to `Executive Pulse`, one exact visual system, a boxed hero, or three equal cards. Use the lightweight weighted selection in section 5. When recent task context is visible, avoid only the immediately previous visual system; do not maintain complex history.

## 3. Page geometries

Choose one geometry before styling components.

| Geometry | Use when | Composition |
|---|---|---|
| Reading Journal | async reading, research, diagnosis, evidence depth | responsive long page; 760–880px narrative column with 1100–1280px evidence breaks; asymmetrical section rhythm |
| Wide Storyboard | operating plan, leadership briefing, phase roadmap, user wants PPT-like width | wide 16:9-inspired chapter panels in a vertical page; each panel carries one decision; generous negative space; no presenter chrome |
| Hybrid Brief | most substantive plans and reviews | concise wide opening + two or three full-width decision canvases + readable detail sections |
| Split Navigator | long recurring review, many chapters, desktop-heavy consumption | compact sticky section rail + wide content; rail collapses on mobile |
| Data Gallery | portfolio, bestseller ranking, channel/category comparison | alternating full-width chart bands and compact evidence grids; avoid a dashboard of identical tiles |

Rules:

- Route **presentation to others, leadership decisions, phased plans, and meeting-led reviews** to Wide Storyboard or Hybrid Brief by default.
- Route **self-reading, personal analysis, evidence review, and reusable reference material** to Reading Journal or Split Navigator by default.
- Route mixed use to Hybrid Brief: wide decision canvases first, long-form evidence and methodology afterward.
- Honor an explicit user preference for wide or long form over these defaults.
- Keep one geometry for the report; do not switch shells every section.
- Wide Storyboard is presentation-like, not a slide deck: retain one HTML reading flow and accessible mobile fallback.
- Break a long argument into more sections instead of shrinking type or packing nested cards.
- Do not enclose the whole hero with a heavy border by default.

## 4. Visual systems

Choose one cohesive system and one depth mode. The report UI uses neutrals, one primary hue family, and at most one semantic signal hue. Tints and shades of the primary hue are not additional semantic colors. A packaged illustration may contain internal tonal variation, but its full palette must not spread into headings, cards, controls, and charts. Every filled surface must declare its own foreground pair; never let body text inherit into an inverse card.

| System | Personality / mode | `--bg` | `--surface` | `--ink` | `--muted` | `--strong` / `--on-strong` | Accents |
|---|---|---:|---:|---:|---:|---:|---:|
| Monochrome Signal | executive black/white/gray; Flat | `#F2F2EF` | `#FFFFFF` | `#111111` | `#555555` | `#111111` / `#FFFFFF` | red `#C83A31` |
| Swiss Commerce | strict grid and IKB anchor; Flat | `#F4F3EE` | `#FCFCF9` | `#101114` | `#555A61` | `#002FA7` / `#FFFFFF` | black `#111111` |
| Carbon Ledger | dark operating room; Flat | `#0B0C0E` | `#16181B` | `#F4F3EF` | `#A8AFB8` | `#F4F3EF` / `#111111` | lime `#B9E769` |
| Market Pulse | white commerce field with sculpted green data objects; Layered | `#FFFFFF` | `#F6F7F4` | `#080808` | `#5B615E` | `#087F79` / `#FFFFFF` | mint `#6DDA82`; lime `#A7F000` |
| Liquid Commerce | cool liquid-tech presentation; Layered | `#F7F7FC` | `#FFFFFFCC` | `#08163D` | `#626A86` | `#3428C8` / `#FFFFFF` | violet `#7255E9`; lavender tint `#C9C4F6`; rose signal `#B85769` |
| Signal Pop | bold flat commercial signal, presentation only; Flat | `#00ED82` | `#FFFFFF` | `#090909` | `#343434` | `#090909` / `#FFFFFF` | green tint `#B2FF00`; violet signal `#7A27B8` |
| Forest Ink | dark organic editorial atmosphere; Layered | `#0C1110` | `#151B19CC` | `#F4F0E8` | `#AAAFA8` | `#F4F0E8` / `#111412` | moss `#6C8067`; pale mineral signal `#A9BBC1` |
| Aura Operations | white operating canvas with fused metric fields; Layered | `#FFFFFF` | `#F4F5F2` | `#1D2226` | `#656B68` | `#22272B` / `#FFFFFF` | yolk `#FFD633`; coral signal `#C84E43` |
| Orbit Noir | black-and-white strategic horizon; Flat | `#050505` | `#111111` | `#F4F4F1` | `#A5A5A1` | `#F4F4F1` / `#080808` | silver `#BFC1C4` |
| Quiet Porcelain | near-white editorial simplicity; Layered | `#F4F4F2` | `#FFFFFFE8` | `#171717` | `#6A6A67` | `#171717` / `#FFFFFF` | stone `#B8B8B3` |
| Tech Frost | light precision for electronics and technology; Layered | `#F2F7F8` | `#FFFFFFD9` | `#10232A` | `#5E747B` | `#0E6675` / `#FFFFFF` | cyan `#4CB7C5`; ice `#B9E5EA` |
| Midnight Exchange | navy, ice text, controlled amber; Flat | `#0D1728` | `#152238` | `#F3F6FB` | `#AAB6C8` | `#F3F6FB` / `#101827` | blue `#82B8FF`; amber `#E4A83E` |
| Cobalt Studio | crisp content-commerce experiments; Flat | `#EEF2F7` | `#FCFDFE` | `#172235` | `#526074` | `#245AA5` / `#FFFFFF` | coral `#B9443F` |

Selection guidance:

- Treat system names as visual vocabularies, not industry routes.
- `Signal Pop` remains presentation-like and works best with concise copy. `Forest Ink` uses atmosphere only in the hero and returns to clear evidence surfaces. These are compatibility checks, not category mapping.
- A blurred atmospheric field is a hero device, not a body background. A dashboard-inspired composition must still follow the report's decision story and must not become a generic control panel.
- Use one primary hue family over the large field and one semantic signal sparingly. Do not introduce a third UI hue for decoration.
- Charts use the primary hue in light/dark values, neutrals for context, and the signal hue for one exception or decision series. Do not assign a new hue to every series.
- Keep asset colors self-contained. Selecting an illustration does not authorize copying each illustration color into the surrounding UI.
- Use sharp accents, not neon glow. For dark systems, keep large areas near-black rather than saturated blue/purple.
- On a dark surface, set headings and body copy to a light neutral such as ivory, white, or pale gray. Never use dark blue, burgundy, forest green, dark violet, or another low-luminance chromatic color for text on a dark field merely because the hues differ.
- When surface relative luminance is below `0.15`, target at least `7:1` for primary text and `4.5:1` for muted text. Use chromatic accents as shapes, rules, or selected states unless they independently meet the text threshold and remain visibly lighter than the surface.
- Keep ordinary metadata and eyebrow lines neutral. Do not color a phrase merely because it sits above the title.
- Use color for a selected state, primary metric, decision gate, chart highlight, section field, or signature illustration. Do not use it for every label, evidence state, divider, and heading simultaneously.
- **Flat mode:** hard fills, hairlines, almost no shadow, and graphic contrast. **Layered mode:** one coherent atmospheric gradient, intentional translucency/depth, and at most two shadow recipes. Never mix flat neon panels with soft glass cards in the same report.
- Never use generic purple-on-white AI gradients, rainbow charts, or uncontrolled glassmorphism.
- Ensure text and any accent used as text meet WCAG AA against their actual background.
- Record and test these pairs: `bg/ink`, `surface/ink`, `strong/on-strong`, every accent used behind text, and every glass surface at its least favorable underlying color.

## 5. Weighted visual variation

Honor an explicit user or brand choice first. Otherwise select the visual system independently of industry using this approximate mix:

| Bucket | Approximate share | Systems |
|---|---:|---|
| Light | 50% | Market Pulse, Liquid Commerce, Aura Operations, Quiet Porcelain, Tech Frost, Cobalt Studio |
| High contrast | 35% | Monochrome Signal, Swiss Commerce, Signal Pop |
| Dark | 15% | Carbon Ledger, Forest Ink, Orbit Noir, Midnight Exchange |

This is lightweight model variation, not a statistical requirement. Do not call a random tool, calculate a seed, build a scoring matrix, browse, or ask the user. Make one quick nondeterministic choice from the weighted buckets. If the immediately previous system in the same task is selected, redraw once. If the selected system conflicts with content density or readability, redraw once from Light or High contrast; do not keep optimizing.

Industry may influence imagery or one line of tone, but it does not select the visual system by default. Do not explain the randomness in the delivered report. Record only the chosen bucket and system in the visual brief.

Maintain approachable luxury regardless of selection: generous whitespace, one radius family, at most two elevation levels, subtle informative hover, and no sacrifice of legibility for atmosphere.

## 6. Typography

Use one primary Chinese family and at most one companion for Latin/numerals.

### Chinese

- **Analytical/default**: readable modern sans fallback such as `PingFang SC`, `Microsoft YaHei`, or available Noto CJK sans.
- **Editorial premium**: Chinese serif only for major headings; keep body text sans.
- Do not add letter spacing to Chinese headings.
- Do not use monospaced type for Chinese body copy.

### Local renderer profiles

| Profile | Heading / numerals | Body | Mono labels | Best fit |
|---|---|---|---|---|
| Swiss Precision | Outfit Bold | Work Sans | Geist Mono | Swiss, Monochrome, Cobalt |
| Executive Ledger | Bricolage Grotesque Bold | Work Sans | IBM Plex Mono | Carbon, Midnight, Slate |
| Editorial Commerce | Instrument Serif | Work Sans | Red Hat Mono | Forest, Quiet Porcelain, Reading Journal |
| Documentary Finance | IBM Plex Serif Bold | Work Sans | IBM Plex Mono | pricing, contribution, evidence-heavy review |

Hierarchy:

- Define exactly five reusable size tokens plus one optional caption token. Do not add one-off sizes inside components.
- Reading mode: `15 / 18 / 24 / 36 / 64px`; optional caption `12–13px`.
- Wide mode: `18 / 24 / 36 / 64 / 96px`; optional caption `13–14px`.
- H1 uses the largest token and stays within two lines. H2 uses token four; H3 uses token three; body and support copy use tokens one and two.
- A section index such as `01` must either share the H2 size and baseline or become an intentionally oversized anchor. Never make it a random smaller number beside the heading.
- Metadata, evidence notation, and eyebrows use the body-small token with neutral color; uppercase tracking is reserved for short Latin labels.
- Body line-height is 1.55–1.75; wide headlines may use 0.95–1.1.
- Keep Chinese headline lines short; move explanation into a smaller dek.
- Use only three main weights. Let scale and space create hierarchy.

### Largest-title semantic wrapping

Apply semantic wrapping only to H1, hero titles, or the largest title token. Let smaller headings and body copy wrap normally.

Before rendering the largest title:

1. identify indivisible entities: platform + category phrases, product/model names, campaign names, numeric values + units, and date/time expressions;
2. group the title into two to four short semantic chunks such as time horizon, action + subject, and outcome;
3. allow wrapping only between chunks by using inline-block phrase spans or safe `<wbr>` positions;
4. keep punctuation with its phrase and do not strand a one-character function word;
5. use one or two preferred breakpoints on desktop; add a second safe internal phrase boundary only when a long chunk cannot fit mobile.

Do not insert a break inside a product, platform, or category compound. Do not use arbitrary character-count wrapping. Prefer responsive phrase spans over hard `<br>`; reserve a hard line break for a deliberate Wide Storyboard title composition. If a protected chunk still cannot fit, step down within the approved H1 type token or revise the title—not the business meaning.

## 7. Summary patterns

Choose exactly one. A summary is a decision device, not a paragraph container.

| Pattern | Form | Best fit |
|---|---|---|
| Editorial Lead | no card; oversized conclusion + one quiet evidence line | strategy, research, narrative review |
| Inverted Verdict | full-width dark or accent field; short verdict left, one gate/metric right | leadership decision, go/hold/no-go |
| Briefing Strip | three compact columns: decision / why now / next gate | operating plan, campaign review |
| Metric Monument | one dominant number, one comparison, one implication | diagnosis with a decisive KPI |
| Split Thesis | 40/60 split: concise conclusion versus evidence/gates | pricing, margin, market entry |
| Gate Stack | three short horizontal rows: scale / watch / stop | phased plan, bestseller incubation |
| Evidence Caption | one-line thesis above the primary chart; no surrounding card | data-led diagnosis |
| Gallery Switcher | two to four large rounded frames; click/focus changes one shared metric, image, or implication | wide brief, portfolio, phase story |
| Liquid Focus | one active glass frame over a calm field; compact tabs switch evidence views | layered systems only |

Hard limits:

- Headline: preferably ≤26 Chinese characters or ≤14 English words.
- Support: one or two short lines; normally ≤60 Chinese characters total.
- Show at most one dominant metric and two gates.
- Never paste the executive summary paragraph into a card.
- Do not place three equal stage cards under every summary. Use a rail, staggered sequence, comparison, or no secondary cards depending on the story.
- For `Gallery Switcher` or `Liquid Focus`, use real buttons, visible focus, arrow-key support when practical, no autoplay, and a noninteractive print fallback.
- Large summary frames may use a 20–28px radius when they are the signature interactive object. This is an intentional exception to ordinary component radii.

### Summary signature marks

A decorative summary mark is optional, never required. Use a rough 60/40 variation: about 60% of reports use one abstract mark and about 40% use none. Do not calculate the ratio or call a random tool.

When used:

- choose one mark from `icons/abstract-marks.svg`; avoid the immediately previous mark when visible;
- vary placement among edge overlap, beside the dominant metric, open negative space, or a low-opacity watermark below the summary;
- vary treatment among bare line mark, cutout, restrained glass lens, or tonal watermark;
- do not default to a small icon inside the same colored circle at the top-right;
- keep one mark maximum in the summary and do not repeat it at every section;
- set abstract decorative marks to `aria-hidden="true"`;
- use `commerce-icons.svg` only when an icon carries real business meaning, not as generic summary decoration.

## 8. Components and hierarchy

### Explicit bans

- Never use a card or callout whose main decoration is a colored left border.
- Never use a colored left rule for H2/H3 hierarchy.
- Never wrap every paragraph in a card.
- Never use nested rounded cards more than one level deep.
- Never default to three or four equal summary/KPI cards.
- Never use pill shapes for ordinary labels, stages, or metadata.
- Never render `observed`, `sourced`, `derived`, `assumed`, or `unknown` as a filled colored badge by default.
- Never repeat one conclusion in a hero, summary card, chart, table, and paragraph.
- Never place dark text on a dark/inverse card or light text on a light card. Every inverse component must set its foreground explicitly.
- Never use a merely different dark hue as contrast on a dark surface.

### Preferred component grammar

- Use whitespace, grid alignment, type scale, full-field inversion, hairline rules, top/bottom rules, or background bands.
- Use square or mildly rounded geometry for analytical systems. Consumer light systems may use a consistent 16–24px radius family, but must not mix many radii.
- Layer only meaningful groups: one raised focal card, flat supporting cards, and the page field. Do not turn prose paragraphs into cards.
- Use at most two shadow/elevation recipes. Shadows establish focus; they are not outlines around every component.
- Keep metadata as a compact line, table, or corner ledger rather than a row of pills.
- Alternate full-width evidence bands, asymmetrical splits, margin notes, and quiet reading sections.
- Use one signature device per report: oversized index, grid crosshair, numbered rail, black field, or thin frame—not all at once.

### Apple-style liquid glass

Use liquid glass only for `Liquid Commerce`, `Liquid Focus`, or one focal summary object in another light Layered system. It must read as polished Apple-like material rather than generic glassmorphism:

- translucent neutral fill around 42–72% opacity over a calm tonal field;
- `backdrop-filter` blur around 18–28px with restrained saturation around 120–140%;
- a one-pixel bright edge, a soft inner highlight, and one low-opacity outer shadow;
- a subtle top-left specular gradient rather than a glowing colored border;
- explicit `--glass-ink` and `--glass-muted` colors meeting the same contrast rules as solid cards;
- an opaque light/dark fallback for print, reduced transparency, or unsupported backdrop filtering;
- at most one or two focal glass objects; never frost the entire report.

On a white page, place glass over a faint tonal wash, chart field, or illustration so refraction is visible. Avoid purple neon haze, excessive bloom, blurry text, multiple colored rims, and large stacks of nested glass cards.

### Tables

- Use full width for four or more columns.
- Emphasize one decision column or exception row; do not zebra-stripe by default.
- Keep headers short, units explicit, and rows aligned by numeric meaning.

## 9. Charts and business diagrams

### Quantitative charts

Use ECharts through the system renderer. Keep charts visually integrated:

- derive colors from report variables;
- use direct labels when they reduce legend lookup;
- lighten grid lines and remove unnecessary axes;
- highlight one decision series; mute context series;
- include title, unit, period, platform/site, source, and caveat;
- use tooltips and legend filtering as the primary chart interaction;
- prefer exact tables when there are too few data points.

| Evidence | Preferred form |
|---|---|
| revenue/profit change | line or bridge/waterfall |
| funnel | compact funnel plus segment exceptions |
| bestseller candidates | ranked dot plot or momentum–contribution scatter |
| product roles | portfolio matrix |
| pricing/promotion | price-to-contribution waterfall |
| inventory | risk matrix or days-cover distribution |
| retention | cohort heatmap |
| phased target | bullet/progress view; gauge only for one critical target |

### Business process diagrams

Do not use Python-rendered Graphviz or PlantUML for e-commerce roadmaps, operating processes, stage gates, or decision flows. They produce an engineering-diagram aesthetic and static images that do not match the report.

Prefer native semantic HTML/CSS rendered by the system:

| Business logic | Visual form |
|---|---|
| 3–6 sequential phases | horizontal numbered rail or stepped runway |
| phases with owners/metrics | swimlane grid |
| pass/watch/stop gates | compact gate band beside each phase |
| campaign calendar | editorial timeline |
| funnel-to-action path | split journey with action column |
| repeated operating loop | circular or four-quadrant loop only when the loop is real |

Diagram rules:

- Compose horizontally on desktop and stack cleanly on mobile.
- Keep each step to a short title plus one metric/gate; move detail into nearby text or expandable notes.
- Use compact connectors and aligned baselines.
- When useful, make phase nodes keyboard-focusable and let click/focus update one shared detail panel for owner, threshold, and next action; keep all core meaning visible without interaction and provide a print fallback.
- Do not use giant decision diamonds, large empty subgraph boxes, crossing arrows, curved retry loops, or labels floating on connectors.
- Do not put three or four lines of copy inside a decision node.

Use Mermaid only for genuinely branching topology that HTML/CSS cannot express cleanly. If used:

- prefer `flowchart LR`;
- keep 4–8 nodes and at most one grouping boundary;
- keep node labels to one or two lines;
- use a restrained custom palette aligned with the report;
- avoid default gray engineering styling and oversized diamonds;
- place thresholds in adjacent evidence text rather than inside a large decision shape.

## 10. Interaction

Unless the artifact is explicitly print-first, include one to three useful interaction patterns. Choose them by geometry:

- **Reading Journal / Split Navigator**: active sticky table of contents, ECharts tooltip/legend filtering, and accessible `<details>` for methodology, assumptions, or evidence notes.
- **Wide Storyboard**: compact section progress, optional keyboard/arrow navigation between chapter panels, ECharts interaction, and an optional detail drawer for evidence that should not crowd the canvas.
- **Hybrid Brief**: wide-section progress plus long-form anchor navigation; keep detailed evidence expandable.
- **Data Gallery**: chart series/category filters and cross-highlighting only when they materially improve comparison.
- Use hover/focus reveal for concise icon explanations when icons carry meaning.
- When charts exist, include at least one meaningful chart interaction by default: legend filtering, pinned tooltip, metric/dimension switcher, zoom/brush for dense series, click-to-highlight, or linked chart/table filtering.
- Prefer one linked interaction that changes the reader's comparison over several decorative hover effects.
- Summary switchers must change a shared evidence view or implication; do not make cards move merely for spectacle.

Use two to four interaction patterns total when the report contains several charts; use fewer for a short report. Avoid autoplay, parallax, WebGL effects, continuous animation, decorative particle systems, multiple competing hover behaviors, and surprise motion. Respect `prefers-reduced-motion`. Interactions must clarify the report, not advertise the renderer.

## 11. Story routing

Choose one scene spine; it controls section order, not visual appearance.

| Scene spine | Reading order | Strong primary visual |
|---|---|---|
| Executive Pulse | decision → decisive metrics → driver → actions | bridge or small multiples |
| Editorial Debrief | tension → evidence → turning point → lessons → next cycle | annotated timeline |
| Bestseller Observatory | definition → candidates → six evidence layers → scale gate | ranked dot/scatter |
| Portfolio Atlas | direction → role map → SKU evidence → portfolio moves | matrix/ladder |
| Conversion Journey | break → segment → causes → test sequence | funnel + exceptions |
| Margin Bridge | economics → bridge → sensitivity → guardrails | waterfall |
| Supply Control | exposure → exceptions → scenarios → replenishment gate | risk matrix |
| Cohort Fieldbook | cohort break → path → economics → intervention | heatmap |
| Market Radar | go/hold/no-go → evidence → economics → gates → launch | comparison/bridge |

Use one spine and at most one supporting pattern. Do not force all reports through an executive dashboard opening.

## 12. Evidence expression

Keep evidence status visible only where it changes trust. Prefer a quiet inline suffix, a column in a source ledger, or a methodology note:

- **observed**: user-provided or directly inspected;
- **sourced**: externally verified with date;
- **derived**: calculated from visible inputs;
- **assumed**: working assumption;
- **unknown**: material gap.

Do not repeat evidence status on every summary card or decorate it with a colored background. In the main narrative, write the source/date or assumption naturally when that is clearer than the taxonomy. Reserve colored warning treatment for a material risk or decision-blocking gap, not for the word `assumed`.

Use confidence only for interpretation:

- high: state directly;
- medium: label as medium confidence in the user's language;
- low: label as needs validation in the user's language.

Separate data fact, inference, and recommendation through labels, placement, or typography—not three differently colored left-border cards. Show absolute and percentage change together when valid. Declare MTD/YTD/full-period/custom time basis.

## 13. Ecommerce visual assets

This package includes optional original SVG primitives under `assets/ecommerce-visual-kit/`. They are visual vocabulary, not HTML templates, renderer assets, fonts, libraries, or a fallback rendering system.

| Asset | Use |
|---|---|
| `icons/commerce-icons.svg` | reusable symbol sprite for product, momentum, funnel, margin, inventory, retention, decision, risk, channel, and bestseller concepts |
| `icons/abstract-marks.svg` | twelve reusable abstract summary marks; choose at most one or none |
| `masks/dot-field.svg` | recolorable dot field for one quiet atmospheric corner |
| `masks/orbit.svg` | recolorable orbit/connector device for a hero or process canvas |
| `illustrations/market-bars.svg` | warm sculpted market/KPI motif for `Market Pulse` |
| `illustrations/liquid-journey.svg` | floating glass evidence journey for `Liquid Commerce` |
| `illustrations/signal-dashboard.svg` | bold flat dashboard motif for `Signal Pop` |
| `illustrations/forest-ink.svg` | dark organic atmospheric field for one `Forest Ink` hero |
| `illustrations/aura-metrics.svg` | fused metric fields and compact cells for `Aura Operations` |
| `illustrations/orbit-noir.svg` | black-and-white orbital strategy motif for `Orbit Noir` |
| `illustrations/quiet-porcelain.svg` | near-white floating evidence surface for `Quiet Porcelain` |
| `illustrations/tech-frost.svg` | light technical evidence system for `Tech Frost` |

Asset rules:

- Copy only the selected local SVG assets into the report output and reference them relatively.
- Use at most one signature illustration and one subtle mask in a report.
- Icons may support navigation, process stages, or compact KPI meaning; never place an icon in every heading.
- Use abstract marks for optional summary decoration and literal commerce icons only for semantic business meaning.
- Recolor masks and sprite icons through CSS variables. Keep illustration palette intact unless a deliberate full-system recolor is planned.
- Treat an illustration palette as self-contained. The surrounding UI still follows the one-primary-plus-one-signal color budget.
- Provide meaningful alt text for informative illustrations and empty alt text for decorative assets.
- Do not stretch, rasterize, base64-embed, or redraw the assets with Python.
- If a runtime image-generation capability is available, a scene-specific hero image may replace the packaged illustration. Keep it optional and preserve the same visual-system constraints.

## 14. Lightweight verification

Default to static checks only:

1. confirm entry HTML, assets, `_shared`, fonts, and required JS files exist;
2. confirm all relative paths resolve and no absolute local path, remote CDN, or base64 asset slipped in;
3. check HTML/JavaScript syntax with available local tools;
4. match every planned chart to one visible container ID and one initialization call;
5. confirm ECharts/Mermaid includes exist only when used;
6. parse copied SVGs as XML and confirm their relative paths resolve;
7. scan for placeholders, stale samples, debug labels, duplicate IDs, and empty visual containers;
8. statically verify every declared surface/foreground pair, including black cards and translucent surfaces, and scan for inherited text color inside inverse components;
9. count distinct font-size declarations against the selected five-token scale plus the optional caption; flag arbitrary one-off sizes.
10. inspect only the largest title for semantic phrase chunks or safe break opportunities; reject a break inside a protected platform/category/product phrase or numeric value + unit.
11. when liquid glass is used, confirm glass foreground tokens, edge/highlight, opaque fallback, and no more than two focal glass objects.
12. when a summary mark is used, confirm one mark maximum, no repeated section decoration, and a non-fixed placement/treatment.

Do not start a local HTTP server. Do not open or unlock a browser. Do not take screenshots. Do not run Playwright or any UI automation by default.

Escalate to browser rendering only when:

- the user explicitly asks for visual acceptance;
- an existing visible rendering defect is being diagnosed;
- static checks reveal a layout/runtime risk that cannot be resolved otherwise.

If browser tooling is unavailable, finish the static checks and deliver; do not create alternative servers or repeatedly retry visual verification.
