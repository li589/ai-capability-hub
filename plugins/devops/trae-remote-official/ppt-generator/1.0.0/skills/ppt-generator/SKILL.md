---
name: ppt-generator
description: Create single-file HTML slide decks from user-provided documents, images, links, or written briefs.
---

# PPT Generator · Single-File HTML Presentations

Create a **single-file HTML slide deck** from user-provided content such as documents, images, and written descriptions.

## Generation Workflow

### Step 1 · Plan the Story

Plan the deck-level narrative before choosing layouts, styles, or image slots.

1. Identify the audience, purpose, source material, language, and desired audience response. Ask for clarification when a missing answer would materially change the story; otherwise proceed with reasonable assumptions.
2. Set the total slide count. **When the user does not specify a count, create exactly 8–10 slides in total, including the cover, agenda if used, and closing slide. Use a different total when the user explicitly requests one.**
3. Write a one-sentence **narrative thesis**: the central point the audience should understand, believe, decide, or do after the deck.
4. Build a deliberate arc:
   - **Opening**: establish the subject, tension, question, or reason to care.
   - **Development**: provide the context, evidence, mechanism, comparison, or progression needed to understand the thesis.
   - **Resolution**: land the implication, recommendation, decision, next step, or memorable conclusion.
   Adapt the arc to the material. Use a problem–solution arc when it genuinely fits the subject.
5. Give every slide exactly one **narrative job** and one **main idea**. Make the sequence cumulative: each slide should create a clear reason for the next slide to exist.
6. Produce a first-pass **Story Plan** using only these columns:

| Slide | Narrative job | Main idea | Supporting content/evidence | Link to next slide |
|---|---|---|---|---|

Keep the Story Plan focused on these narrative fields and lock the story sequence before proceeding. Add layout IDs, style presets, decorative treatments, and image slots in their designated later steps.

### Step 2 · Plan Evidence and Visuals

After the Story Plan is stable, decide what each slide needs to make its main idea credible and clear:

- **Images are the default, not the exception.** A slide deck is a visual medium — most slides should carry a real image, screenshot, chart, diagram, or generated concept image. Reach for a visual first and only fall back to text-only when a slide genuinely reads better as pure typography (see the text-only criteria below). Do not skip an image merely because sourcing it takes an extra search or feels uncertain.
- Prefer real, source-backed images and current official screenshots for real subjects. Use generated imagery (`image_gen`) for fictional, unpublished, confidential, unavailable, or deliberately illustrative content — generation is a first-class option, so an unavailable photo is a reason to *generate*, not to drop the visual.
- Identify the strongest supporting form for each slide: source-backed image, screenshot, chart, diagram, generated concept image, or — only when it truly communicates best — text.
- **Coverage floor:** aim for a strong majority of content slides to carry a visual. For image-forward decks (people, companies, products, places, travel, events, portfolios, art, architecture, objects, history), target **roughly 70%+ of content slides with real or generated imagery**; for strategy/technical/analytical decks, cover most slides with diagrams, charts, screenshots, or data visuals. Treat a run of consecutive text-only slides as a signal to add evidence, not as an acceptable default.
- Treat visuals as evidence, explanation, context, or emotion—not as decoration.
- For slides needing images, define the visual job and write 2–3 specific English search terms closely tied to the content. Replace broad terms such as "technology," "nature," or "business" with concrete subjects, actions, contexts, and media.
- Read Sections 1–2 of [`references/image-pipeline.md`](references/image-pipeline.md) to plan the visual intent and source strategy. Use its search, generation, and placement sections after layout and style selection.
- Extend the Story Plan with `Evidence/visual role` and `Source strategy/search terms`. Reserve layout selection for Step 3.

**When text-only is the right choice** (the exception, and it needs a positive reason — not just "sourcing felt hard"): definitions, arguments, manifesto/transition moments, pull quotes, and compact metric statements where typography carries the point, or genuinely sensitive subjects where a literal image would be inappropriate. In every other case, default to a visual — a reliable source plus descriptive `alt` text is all that is required to commit to an image; no browser/preview check exists or is needed, so uncertainty about post-hoc verification is not a reason to avoid images.

### Step 3 · Select Layouts

Choose a suitable layout from `layouts/` for every slide.

Choose layouts after the narrative job, main idea, content quantity, and evidence/visual role are clear. Select the layout that best serves the planned story.

#### Five Layout Categories

| Type | File | Included Layouts | Purpose |
|---|---|---|---|
| Structural slides | `layouts-structural.md` | T01 Cover (including B/C/D variants), T02 Agenda, T08 Closing | Open and close the narrative; **required** |
| Content slides | `layouts-content.md` | T03 Brand, T04 Grid Lines, T05 Cards, T06 List, T07 Think, T17 Chart | Present the core argument |
| Image slides | `layouts-image.md` | T09–T16 (Gallery/Split/Duo/Trio/Hero/Penta/Hexa/Mosaic) | Present visual material |
| High-density slides | `layouts-dense.md` | T18 Table, T19 Metrics, T20 Dense List, T21 Comparison, T22 Dashboard | Present dense information |
| Free layouts | `layouts-free.md` | T23 Free Single, T24 Free Dual, T25 Free Triple | Arrange content without a preset template |

#### Mandatory Rules

1. **Include structural slides within the total count**: Every deck must include a cover (T01/T01-B/T01-C/T01-D) and T08 Closing. T02 Agenda is optional and must replace, not add to, another planned slide when the deck is already at its target count.
2. **Let the story determine the mix**: Select structural, content, image, high-density, and free layouts according to their narrative jobs while preserving the planned story beats and order. No layout family is preferred by default — judge each slide on its own content and reach for a high-density layout (T18–T22) whenever the data density genuinely calls for it, rather than forcing dense material into a lighter preset that would break.
3. **Protect the target count**: Assign exactly one layout to every row in the locked Story Plan. Keep structural, transition, appendix, source, and visual-break slides within the chosen total.
4. **Keep free layouts polished**: When T23–T25 free layouts are used, keep them orderly, polished, substantial, and intentionally balanced.
5. **Vary layouts when the story allows**: Prefer a different layout on consecutive slides; T06 may appear twice in a row. Preserve the narrative sequence and target count while creating visual rhythm.
6. **Preserve the story sequence**: Keep the cover first and the closing slide last, retain the narrative order established in the Story Plan, and choose a sequence suited to each deck.
   - If T02 is used, place it on slide 2 and keep it within the chosen total.
   - Place T07 Think wherever it creates a useful chapter transition or pacing break.
   - Reconsider the layout choice for every deck, but not the already-validated story logic.

#### Layout Selection Guide

| Content Intent | Recommended Layout | Alternative |
|---|---|---|
| Classic cover/opening | T01 Cover | T01-C |
| Cover with product screenshot or visual asset | T01-B Cover Split | T01-D |
| Minimal, text-only cover | T01-C Cover Minimal | T01 |
| Immersive brand cover | T01-D Cover Hero | T01-B |
| Agenda/chapter outline | T02 Agenda | — |
| Product introduction, positioning, or milestones | T03 Brand | T06 |
| 3–4 parallel modules or product matrix | T04 Grid Lines | T05 |
| Four capabilities, roles, or feature highlights | T05 Team Cards | T04 |
| Timeline, feature list, or detailed explanation | T06 Refine List | T03 |
| Quote, vision, or chapter transition | T07 Think | — |
| Closing, summary, or CTA | T08 Closing | — |
| Four screenshots or design examples | T09 Gallery Grid | T04 |
| One large visual with explanatory text | T10 Feature Split | T03 |
| Two-image comparison | T11 Duo Images | T09 |
| Three images, one primary and two secondary | T12 Trio Images | T09 |
| Full-screen image or high-impact visual | T13 Hero Image | T07 |
| Five-image overview | T14 Penta | T09 |
| Six-image ecosystem | T15 Hexa | T14 |
| Six-plus-image portfolio waterfall | T16 Mosaic | T15 |
| Trend, KPI dashboard, or metric comparison | T17 Chart | T04 |
| Structured tabular data, specs, or pricing plans (5–8 rows × 4–6 cols) | T18 Dense Table | T21 |
| 6–12 KPI numbers or an indicator matrix | T19 Metric Matrix | T22 |
| 6–10 compact list items on one page | T20 Dense List | T06 |
| Multi-dimensional comparison of 2–3 options | T21 Comparison | T18 |
| Metrics + mini chart + highlights on one executive summary | T22 Info Dashboard | T19 |
| Free narrative, flowchart, or content that fits no preset | T23 Free Single | T06 |
| Side-by-side comparison or image/text split | T24 Free Dual | T10 |
| Three-way comparison or multi-module dashboard | T25 Free Triple | T21 |

After assigning layouts, finalize the plan as:

| Slide | Narrative job | Main idea | Supporting content/evidence | Evidence/visual role | Layout |
|---|---|---|---|---|---|

### Step 4 · Match a Visual Style

Select a design style from `styles/` only after the story and layouts are established:

- If the user specifies a style, use its corresponding style file.
- If the user provides a reference URL or screenshot, analyze its visual characteristics and select the closest style file. If none fits, derive new visual tokens from the reference.
- If the style direction cannot be inferred, choose the style that best fits the audience, subject, and narrative tone.
- Apply the style to the selected layouts so it reinforces the established story structure.

Available styles:

| Style File | Visual Characteristics |
|---|---|
| `styles-trae-work.md` | White canvas, purple accents, ASCII breathing field, rounded cards, JetBrains Mono kickers |
| `styles-clean-natural.md` | Warm white, olive accents, serif headings, generous whitespace, minimal decoration |
| `styles-privy.md` | Near-monochrome canvas, Iris Pulse violet rules, ABC Favorit display type, pill controls, editorial fintech |
| `styles-peak-design.md` | High-contrast black/white, scarce Ember Red accents, Geist/Inter, Fog cards, no shadows, gallery product aesthetic |
| `styles-linear.md` | Dark canvas, Acid Lime accents, precise Inter typography, 0.5px hairlines, developer-tool aesthetic |
| `styles-airbnb.md` | Pure white, Rausch coral accent, image-led composition, generous borderless whitespace, lifestyle aesthetic |
| `styles-caldera.md` | Warm limestone, Ember Orange accents, heavy condensed uppercase headings, 40px radii, volcanic industrial aesthetic |
| `styles-ori.md` | Pure black, Ember Orange accent, TWK Everett display type, square corners, Chivo Mono terminal labels |
| `styles-compound.md` | Pure white, near-colorless grayscale, Inter 400, 20px radii, pill controls, editorial minimalism |
| `styles-media-minimal.md` | Pure white, neutral black contrast, Helvetica Neue, no decoration, media-first minimalism |
| `styles-awesomic-zinc.md` | Zinc-gray rounded cards, 1px hairlines, functional orange accents, DM Sans, soft neutral aesthetic |
| `styles-ikea-editorial.md` | Pure white, functional yellow accents, bold/regular Inter pairing, 8px radii, hard editorial grid |
| `styles-anthropic.md` | Warm ivory parchment canvas, Anthropic Serif editorial body + sans display dual-system, single Clay terracotta accent, hairline borders, paper-publication feel |
| `styles-authkit.md` | Midnight near-black canvas, frosted-glass surfaces, luminous white-on-dark text, Void Violet single accent, aeonikPro display + Untitled Sans body, glass-plate cards |
| `styles-frameio.md` | Near-black Obsidian canvas, FrameGothic geometric sans 80px headlines, single Iris Glow blue + Twilight violet border, midnight cinema projection room feel |
| `styles-huly.md` | Near-black Obsidian canvas with violet-to-amber aurora beam, Inter + Esbuild display at 84px, Electric Iris + Ember Pulse dual accent, 9999px pill + 12px cards, mixed dark/light sections |
| `styles-jeton.md` | Pure white canvas, Sequel Sans geometric grotesque at 155px, Signal Orange sole accent, flat editorial fintech, no decorative borders, magazine-spread feel |
| `styles-karl.md` | Full-bleed Signal Yellow canvas, hand-illustrated storybook scenes, Changa One chunky rounded display + Arial nav, flat saturated colors, 1440px radius as compositional device |
| `styles-resend.md` | Pure Void Black canvas, Inter body + Domaine serif 96px hero + Commit Mono code, Iris Violet gradient accent, hairline graphite borders, developer-luxury matte-glass feel |
| `styles-steep.md` | Pure white canvas, Signifier serif headlines weight 400 + Sohne body half-step weights, Blush Peach single warm accent, 24px soft cards, editorial analytics magazine feel |
| `styles-structured.md` | Warm Putty beige canvas, Davinci serif 374px wordmark + Helvetica Now utility, stark Ink black contrasts, mixed light/black sections, Renaissance gallery exhibition feel |

**Explicit text color is mandatory.** Some style files are token-only (design tokens and rules, no ready-made CSS) — for these you synthesize the deck CSS yourself. When you do, **set an explicit `color` on the canvas element and on every heading/text helper** (`.h-display`, `.h-1`, `.h-2`, `.lead`, `.kicker`, body). Never let text fall back to the browser default black: on a dark-canvas style (e.g. huly `#303236`, linear/frameio/resend/authkit near-black) an uncolored heading renders black-on-dark and disappears. Give the canvas a default `color` matching its dominant surface (white text on dark canvases, near-black on light canvases), and for **mixed dark/light** styles scope per-section overrides (e.g. `.s-light .h-1 { color: #050506; }`) — decide each section's mode first, then color its text as a block. Verify every heading meets contrast against its actual background, not the browser default.

### Step 5 · Acquire Visual Assets

Use the finalized story, evidence plan, layout slots, and visual style to search for or generate production assets.

Use source search as the default path for real people, products, companies, places, events, objects, interfaces, and documentary subjects. Use image generation as the specialized path for concepts and subjects that call for an original illustration.

1. Finalize each slot's ratio, fit behavior, crop allowance, and source strategy.
2. For real named subjects, run a separate image search for each distinct visual intent, compare 2–3 candidates, open their source pages, and select the most credible asset that fits the slot.
3. For fictional, unavailable, confidential, or deliberately illustrative subjects, create one focused generation prompt per slot using the selected style's visual language.
4. Save selected assets to the deck's `images/` working directory with semantic filenames and record their sources or generated-concept labels.
5. When a real photo is unavailable, **generate a concept image** for the slot rather than dropping the visual; reserve a text-only treatment for slides that meet the positive text-only criteria (Step 2), always preserving the slide's narrative job.

### Step 6 · Generate the HTML

Combine the story and content from Step 1, the evidence plan from Step 2, the layout skeletons from Step 3, the visual system from Step 4, and the localized assets from Step 5.

- Use a fixed 1280×720px canvas with proportional JS scaling.
- Canvas centering scheme: **do not rely on chained-height centering via `body{display:flex; align-items:center}` + `html,body{height:100%}`**. You must use `position:fixed; top:50%; left:50%` + JS `translate(-50%,-50%) scale(s)` to anchor the canvas at the exact center of the viewport.
- The canvas structure must be **single-layer**: the centering `translate(-50%,-50%)` **may appear only once** across the entire DOM chain, and only on the single canvas element. **Do not** split the canvas into an outer positioning container + an inner scaling container (e.g. `#stage` wrapping `#canvas`) with each layer writing its own `translate(-50%,-50%)`—the two displacements stack and push the whole canvas toward the top-left corner, so the canvas ends up off-center. Positioning (`top/left:50%`) and scaling (`scale`) must be merged onto the **same element** as a single `transform: translate(-50%,-50%) scale(s)`.
- When JS updates the scale it must **rewrite the entire** `transform` and always keep the centering displacement, i.e. assign `el.style.transform = 'translate(-50%,-50%) scale(' + s + ')'`. **Do not** write only `scale(s)` (that would drop `translate(-50%,-50%)` and snap the canvas anchor from the center back to the top-left).
- Do not let a parent compress the canvas. In the recommended `position:fixed` centering the canvas is anchored to the viewport and is **not** a flex/grid item, so its width stays a hard 1280px and `scale()` is the only transform acting on it. If you ever nest the canvas inside a `display:flex`/`grid` parent that could shrink it, set `flex-shrink:0` so the parent cannot compress its width *before* `scale()` applies — otherwise the width is shrunk once by the parent and again by `scale()`, double-scaling with a shifted origin.
- **No viewport units inside the canvas.** Because the canvas is a fixed 1280×720 block whose only responsive mechanism is the outer `scale(s)`, every size inside it must be a **fixed px** value. **Do not** use `vw`/`vh`/`100vw`/`100vh` or viewport-dependent `min()`/`max()`/`clamp()` (e.g. `min(7vw,12vh)`, `max(14px,1vw)`, `clamp(60px,9.4vw,148px)`) for any font-size, spacing, padding, gap, or dimension — these bypass the scale and re-scale against the live window, producing a "window-response × scale" double-scaling. Convert design values by evaluating them once at the 1280×720 canvas (1vw≈12.8px, 1vh≈7.2px) and hard-coding the px result.
- **No media queries for layout.** The canvas width is always 1280px, so aspect-ratio/width breakpoints (e.g. `@media (max-aspect-ratio: 4/3)`) never fire and only invite drift from the scale model. Rely solely on the JS `scale(s)` for fit.
- **Keep the canvas edge visible against the page.** The scaled canvas is letterboxed inside the browser viewport, so the off-canvas area (`html, body`) must not share the canvas's own background — otherwise the two blend and the canvas edge disappears. Give `html, body` an off-canvas background that contrasts with the canvas surface (for a white/light canvas use a light gray such as `#e8e8ec`; for a dark canvas the body may stay near-black or one step darker), set the canvas element's own `background` explicitly (do not let it inherit the body), and add a `box-shadow` to the canvas (e.g. `0 10px 60px rgba(0,0,0,.16), 0 2px 8px rgba(0,0,0,.08)`) so it visibly floats above the page. This matters most for light-canvas styles where an unset body defaults to white and merges with the canvas.
- **Persistent chrome lives inside the canvas — never `position:fixed`.** The top brand bar, bottom page-number bar, and nav dots must be **children of the scaling canvas element** and positioned with `position:absolute` relative to it (e.g. `.chrome-top{ position:absolute; top:0 }`, `.chrome-bottom{ position:absolute; bottom:0 }`, nav likewise). **Never** anchor them with `position:fixed` and never place them outside the canvas: `fixed` pins them to the browser viewport, not the 1280×720 canvas, so once the canvas is scaled and letterboxed the bars float to the very top/bottom of the window and drift out of the slide — they stop tracking the canvas edges and no longer scale with it. Everything that must scale with the deck (backdrop layers, chrome bars, nav) belongs inside the canvas subtree.
- Inline all CSS and JavaScript.
- Include keyboard, wheel, touch, and dot navigation.
- Include staggered entrance animation.
- Slide transition: **do not toggle visibility via `display:none` ↔ `display:grid`** (the `display` property cannot be transitioned by CSS, causing an instant hard cut with no animation). You must use an `opacity` + `visibility` combination for a pure fade in/out:
  - Inactive: `opacity:0; visibility:hidden`
  - Active: `opacity:1; visibility:visible`
  - Transition curve: `transition: opacity .5s cubic-bezier(.2,.7,.2,1), visibility .5s`
  - **Do not** stack `transform: scale()` on the transition state—a `scale` on the slide would combine with the canvas JS scaling, producing a jarring zoom where the slide "pops bigger" on each switch; scaling is handled solely by the canvas container's `translate(-50%,-50%) scale(s)`.

### Step 7 · Self-Check

- The deck follows the locked Story Plan: one narrative job and one main idea per slide, with a coherent progression from opening to resolution.
- No slide overflows at 16:9.
- **Vertically-centered accumulating containers have a hard height cap.** Any container that stacks a variable number of items/cards/points and is vertically centered (`align-items:center` / `align-content:center`, e.g. `.brand-cards`, `.team-cards`, `.refine-list`, `.feature-text`, `.think-wrap`) overflows **symmetrically** — its lower half spills into the bottom page-number chrome the moment content exceeds the 582px content area (720 − 2×69px pad). Tuned padding/type alone is only a soft guard against the *expected* worst case; it does **not** stop real over-long copy or an extra item. Each such container **must also** carry a hard cap — `max-height:582px; overflow:hidden` (plus `align-content:center`, or `align-self:center` for a centered grid child) — so over-length content is clipped instead of drifting into the chrome. Never rely on the soft guard alone.
- No `vw`/`vh`/`100vw`/`100vh` or viewport-dependent `min()`/`max()`/`clamp()` appears inside the canvas; all inner sizes are fixed px, and no layout `@media` breakpoints remain.
- The chrome bars and nav dots are inside the canvas element and use `position:absolute` (never `position:fixed`), so they track the canvas edges and scale with it instead of pinning to the window and drifting out of the slide when the canvas is letterboxed.
- Image layouts retain at least 80px of bottom safe space.
- Every image container using `flex:1` or `grid-template-rows: 1fr` must set `min-height:0; overflow:hidden`.
- Images inside those containers set `width:100%; height:100%; object-fit:cover`.
- Consecutive slides use different layouts when practical; T06 may repeat once.
- The deck consistently follows the selected style file's colors, typography, radii, and decorative language.
- Every heading and text helper has an explicit `color` that contrasts with its actual background (no reliance on the browser default black); on dark-canvas or mixed styles, no heading is left uncolored where it would render dark-on-dark.
- The canvas edge is visible against the page: `html, body` use an off-canvas background that differs from the canvas surface, the canvas sets its own `background`, and it carries a `box-shadow` so it floats rather than blending into the browser background.
- **Visual coverage meets the floor:** a strong majority of content slides carry a visual (real image, generated concept image, screenshot, chart, or diagram) — roughly 70%+ for image-forward decks, most slides for analytical decks. Every text-only slide has a positive reason from the Step 2 criteria; if visuals are sparse or several text-only slides run consecutively, add imagery (generate a concept image when a real photo is unavailable) before finishing.
- Every `<img>` uses a reliable source (user asset, verified official/search source, or a `text_to_image` URL) and carries descriptive `alt` text so a failed load is still recoverable; prefer sources confirmed during Step 5 over guessed URLs. No browser/preview step is required to finish the deck.

## Example Triggers

```text
Create a PPT about [topic/document/link].
Create a [style name] PPT.
Turn this document into a slide deck.
```

## Directory Structure

```text
ppt-generator/
├── SKILL.md
├── layouts/
│   ├── layouts-structural.md
│   ├── layouts-content.md
│   ├── layouts-image.md
│   ├── layouts-dense.md
│   └── layouts-free.md
├── references/
│   └── image-pipeline.md
└── styles/
    ├── styles-airbnb.md
    ├── styles-anthropic.md
    ├── styles-authkit.md
    ├── styles-awesomic-zinc.md
    ├── styles-caldera.md
    ├── styles-clean-natural.md
    ├── styles-compound.md
    ├── styles-frameio.md
    ├── styles-huly.md
    ├── styles-ikea-editorial.md
    ├── styles-jeton.md
    ├── styles-karl.md
    ├── styles-linear.md
    ├── styles-media-minimal.md
    ├── styles-ori.md
    ├── styles-peak-design.md
    ├── styles-privy.md
    ├── styles-resend.md
    ├── styles-steep.md
    ├── styles-structured.md
    └── styles-trae-work.md
```

## Core Principles

1. **Plan the story before the slides** — establish the audience, narrative thesis, arc, slide jobs, and sequence before choosing layouts or styles.
2. **Let evidence shape the page** — decide what proves or explains each main idea before selecting its layout.
3. **Prefer real visual evidence** — use source-backed images and official screenshots for real subjects; use generated imagery for conceptual, fictional, confidential, unavailable, or intentionally illustrative subjects.
4. **Let layout serve the story** — choose the structure after the story and evidence are clear, fit layouts to the content, and preserve the target slide count.
5. **Apply style last** — layouts define the skeleton; styles define the visual system and reinforce the narrative.
6. **Prefer restraint over spectacle** — use animated backgrounds when they directly serve the content.
7. **Deliver one file** — the final HTML requires no build step or server; a temporary local server is allowed during generation.

## General Constraints

- Every slide must use `<section class="slide s-xxx">`.
- Use CSS Grid by default. A few layouts are explicitly Flexbox-based — notably **T04 Grid Lines, whose slide-level `.s-lines` container is `display:flex` (the inner `.lines-grid` is still a grid)**; follow whatever `display` each layout's spec declares rather than forcing grid.
- **Slide-level classes must not override `position`** (a key constraint that prevents content from overflowing the canvas): the `.slide` base class is fixed to `position: absolute; inset: 0`, which is the **sole mechanism** by which each slide fills the 1280×720 canvas and anchors to the top-left. Any slide-level class (`.s-xxx`, such as `.s-think` / `.s-cover-hero`) **must not** set `position: relative` / `static` / `fixed`—the moment it is overridden, `inset: 0` immediately loses effect, the slide collapses to the height of its own content and detaches from the canvas anchor, causing **content to spill outside the page**.
  - If some child elements need absolute positioning (such as a full-screen background image, mask, or corner badge), there is **no need** to add `position: relative` to the slide-level class: the base class's `position: absolute` is itself a valid containing block, so `absolute` children will position correctly relative to the slide and fill it.
  - If you truly need an independent positioning context, add `position: relative` to a **child container inside** the slide, and never touch the slide itself.
  - Likewise, slide-level classes **must not** use overall displacement like `transform: translateY(...)` to push content out of the safe area; centering/alignment is always achieved via Grid/Flex `align-items` / `justify-content`.
- Every slide must include persistent chrome: top brand bar (report name on the left, year/label on the right) and bottom page bar (series name on the left, slide number and total on the right).
- Chrome sits at `top:0` / `bottom:0` and occupies roughly 40px of visual height at each edge; a style file may push it inward with an offset such as `top:28px` / `bottom:28px`. To keep slide content clear of it, set each slide's `padding-top`/`padding-bottom` to at least 56px (chrome height + breathing room). Full-screen layouts T01-B, T01-D, T08, and T13 may use `padding:0` when their internal spacing already keeps foreground text clear of chrome.
- Render the top and bottom chrome as clean, unruled text areas.
- Use bottom dots as the sole visible navigation control.

## Image Guidelines

Choose image sources using four priority tiers. Read [`references/image-pipeline.md`](references/image-pipeline.md) whenever a deck needs photos, screenshots, product images, people, places, events, concept images, or full-screen backgrounds.

**Default visual policy:** Images are the default. Give most content slides a visual and aim for the coverage floor in Step 2 (roughly 70%+ of content slides for image-forward decks; most slides for analytical decks). Use real, source-backed imagery for real subjects; use generated imagery when the subject is fictional, unpublished, confidential, unavailable at usable quality, or intentionally conceptual — an unavailable photo means **generate one**, not drop the visual. A reliable source plus descriptive `alt` text is enough to commit to an image; there is no browser/preview check, so uncertainty about after-the-fact verification is never a reason to go text-only.

| Tier | Condition | Action |
|---|---|---|
| **Tier 1** | The user provided images | Use the supplied images directly |
| **Tier 2** | Real companies, products, people, places, events, news, public interfaces, or historical objects | Use `web.image_query` to find official or traceable sources; open the source page and verify the subject, context, resolution, and usage risk |
| **Tier 3** | Fictional, unpublished, confidential, unavailable, or deliberately illustrative visuals | Use `image_gen` to generate a raster image and label it as a generated concept image |
| **Tier 4** | Deterministic information such as processes, relationships, architecture, or data | Use charts or HTML/CSS/SVG; reserve raster imagery for subjects that call for photos, people, products, places, or scenes |

### Rules

1. **Choose the slot before the image**: Define the visual job, ratio, and `cover`/`contain` behavior before searching or generating.
2. **Write specific queries**: Combine the named entity, visible object/action, context, and medium into a 4–8-word English query. Turn broad terms such as technology, nature, business, team, office, or abstract into concrete, observable descriptions.
   - Bad: `solar energy`
   - Good: `commercial rooftop photovoltaic installation documentary photo`
   - Bad: `business meeting`
   - Good: `carbon trading floor market display documentary`
3. **Verify sources during search**: Compare at least 2–3 candidates, open the source page to confirm subject, time/scene, resolution, crop margin, and provenance, and use the verified source asset.
4. **Write production-ready generation prompts**: Include the target slot and ratio, subject, scene, medium/style, composition, lighting, palette/material constraints, and clean-output requirements. Request presentation-ready imagery with clean crop areas and without visible text, watermarks, extra logos, slide titles, page numbers, or navigation elements. Use one prompt per independent slot.
5. **Localize assets**: Save selected assets to the deck's `images/` working directory using `{two-digit page number}-{semantic}.{ext}`. Embed them as data URLs by default to preserve single-file delivery. Reference localized assets or embedded data from the final HTML.
6. **Keep same-slide assets distinct**: Use different assets for multiple image slots on one slide and keep their ratio, visual scale, and tone consistent.
7. **Use the right fit**: Use `cover` for photos; default to `contain` for screenshots, maps, charts, and dense UI.
8. **Write useful alt text**: Informative images need semantic `alt` text; purely decorative images use `alt=""`.
9. **Reserve text-only for a positive reason**: Go text-only only when a slide genuinely reads best as pure typography — definitions, arguments, manifesto/transition moments, pull quotes, compact metrics, or sensitive subjects — not merely because an asset was hard to find. When a real photo is unavailable, generate a concept image (Tier 3) before defaulting to a text-only slide; when you do use text-only, make it a deliberate, strongly-typeset composition.
