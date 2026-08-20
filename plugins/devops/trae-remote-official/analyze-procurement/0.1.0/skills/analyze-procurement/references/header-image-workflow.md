# Optional report header-image workflow

Use this reference only when the user explicitly asks for a 头图, header image, hero image, or equivalent report-top visual. A style reference, visual-system choice, or request for a polished report does not imply permission to generate one.

## 1. Invariants

Call the asset **头图 / report header image**.

Require all of the following:

- newly generated for the current report;
- first visible report block;
- same declared width as the report shell;
- shallow panoramic frame, approximately 3.2:1 desktop and 2:1 mobile;
- visually derived from the report's selected palette, geometry, type rhythm, and tone;
- related to the decision without encoding the data;
- no baked title, labels, prices, chart axes, UI cards, logos, or watermark;
- local relative asset path;
- descriptive alt text.

Never use a packaged SVG as the final header. Packaged art is a mood or composition reference only.

## 2. Pre-authoring sequence

Do not start a local server, open a browser, or take screenshots.

1. Complete TRACE analysis and select the report mode, composition, and visual direction.
2. Derive a **Header Style Snapshot** from the selected route manifest and production brief before writing HTML:
   - exact background, ink, main, and optional signal colors;
   - type contrast and title scale;
   - corner, rule, grid, line, and panel geometry;
   - texture or material language;
   - report density and decision severity;
   - intended header frame and bottom transition.
3. Choose one decision metaphor and one style lane.
4. Load the current official image-generation skill completely. Use Seedream when exposed by the runtime.
5. Generate one candidate from the style snapshot and optional reference asset.
6. Inspect the generated image itself before HTML authoring for palette, crop safety, accidental text/logos, noise, and bottom-edge behavior.
7. Make at most two targeted single-change iterations.
8. Copy the selected raster into the planned report-local assets.
9. Write the final HTML once with the header as its first visible block.

After writing the final HTML, perform no inspection or validation. Do not invoke an HTML checker, local server, browser, screenshot, renderer, linter, or HTML runtime preview.

## 3. Style routing

Choose one lane from the report tone and audience.

| Style lane | Good fit | Avoid |
|---|---|---|
| Abstract editorial | sourcing, approval, price, portfolio | generic blobs, weak pastels |
| Generative signal | price, inventory, capacity, route, evidence flow | literal charts or readable labels |
| Tactile modular | operational reports, inventory, logistics | glossy app mockups |
| Collage / halftone | supplier landscapes, category stories | busy scrapbook and copied logos |
| Cute operational | approachable recurring internal review | childish treatment of serious gates |
| Cinematic industrial | continuity, capacity, disruption | generic truck/factory glamour shot |
| Photographic still life | physical goods and materiality | staged catalog cliché |

Use playful art only when audience, writing, and decision severity support it.

## 4. Reference roles

Use no more than two references:

- **Optional Image 1 — package or user mood reference:** borrow only one stated cue such as screenprint grain, route composition, color-block energy, or tactile material.
- **Optional Image 2 — subject reference:** use only when a physical material, route, product, or environment must be depicted accurately.

The HTML source is not an image reference. Convert it into the textual Header Style Snapshot instead.

## 5. Seedream prompt contract

```text
Use case: <stylized-concept | photorealistic-natural | illustration-story>
Asset type: full-width procurement HTML report header image
Primary request: Create a new panoramic image expressing <one decision metaphor>.
Report style snapshot:
- palette: <exact HEX values>
- contrast: <high / restrained>
- geometry: <rules, grids, curves, blocks, or route lines>
- texture/material: <grain, paper, ink, clay, metal, photographic>
- tone: <decision severity and audience>
Optional reference: use only <one named cue>; do not reproduce the image.
Scene/backdrop: <flat field, material scene, abstract space, or physical environment>
Subject: <one central visual idea, not a list of procurement icons>
Composition/framing: very wide panoramic composition around 3.2:1; important content inside the central 70%; strong horizontal flow; safe responsive crop.
Color palette: use only the declared background, ink, main, optional signal, and ink-derived neutral values; do not introduce another hue.
Bottom-edge behavior: <hard clean edge | bottom 15% resolves to exact next-section background | one matching diagonal>.
Constraints: no text, numbers, letters, logos, trademarks, watermark, chart axes, tables, dashboards, UI cards, generic procurement clip art, colored edge bands, or low-contrast wash.
Avoid: robots, handshakes, currency coins, shopping carts, generic globes, literal scorecards, and random floating capsules.
```

Keep all report titles and decision-critical information as live HTML.

## 6. Iteration

Generate one candidate by default. Create another only when the first violates the brief.

Check the image directly for:

- exact palette and contrast;
- one legible metaphor;
- no accidental words, logos, watermarks, UI, or charts;
- central 70% crop safety;
- a bottom edge compatible with the selected transition;
- density appropriate to the report;
- no competing chromatic hue.

Use one-change iteration instructions such as:

- “keep composition and palette; simplify background density”;
- “keep the subject; make the bottom 15% exact `#FFFFFF`”;
- “keep everything else; remove letter-like marks and UI-card shapes”;
- “keep the style; move important forms into the central safe area.”

Repeat constraints on every edit.

## 7. Placement and transition

Declare:

- width `100%` of the report shell;
- no side inset mismatch;
- desktop aspect approximately `3.2 / 1`;
- mobile aspect approximately `2 / 1`;
- `object-fit: cover`;
- explicit `object-position`;
- local PNG/WebP path;
- source width around 1600–2000 px;
- optimized file size around 1.2 MB or less when practical.

Choose one transition:

1. **Hard rule — default:** clean image edge, 1–3 px neutral ink separator, then HTML content; the separator is report-level and must not become a component accent band.
2. **Color carry:** bottom 10–15% resolves to the exact next-section background.
3. **Controlled gradient:** only when the report already uses the same declared gradient.
4. **Diagonal cut:** only when the report already uses that angle.

Do not use a soft fade by default. Do not overlay the title unless the generated image has deliberate negative space and the source declares a tested foreground pair.

## 8. Pre-authoring constraints

Set these in the production brief before writing HTML:

1. place the image as the first visible report block;
2. align shell and image widths;
3. declare desktop and mobile aspect/crop rules;
4. choose one bottom transition;
5. match the selected route palette;
6. keep all critical text outside the bitmap;
7. use a local relative path and descriptive alt text;
8. keep the report color budget and prohibit colored edge bands.

Do not check these conditions after the final HTML is written.
