# Image Search and Generation Pipeline

Read this file when a deck uses photos, people, products, places, events, screenshots, concept art, or full-screen backgrounds. Use it after the Story Plan identifies the visual role of each slide. Finalize exact image slots after layout selection, then acquire assets that fit those slots.

## Table of Contents

- [1. Plan Visual Intent and Slots](#1-plan-visual-intent-and-slots)
- [2. Choose Search or Generation](#2-choose-search-or-generation)
- [3. Image Search Workflow](#3-image-search-workflow)
- [4. Image Generation Workflow](#4-image-generation-workflow)
- [5. Asset Placement and Single-File Delivery](#5-asset-placement-and-single-file-delivery)
- [6. Story-Driven Image Coverage](#6-story-driven-image-coverage)
- [7. Lightweight Check](#7-lightweight-check)

## 1. Plan Visual Intent and Slots

Plan visuals in two passes.

### Pass A · Before Layout Selection

Extend the Story Plan with:

| Field | Requirement |
|---|---|
| Slide and visual role | Slide number, plus one of context, evidence, explanation, comparison, or emotion |
| Supporting need | The fact, subject, interface, place, person, product, or concept the audience needs to see |
| Asset strategy | User asset, source search, official screenshot, generated image, data visual, deterministic diagram, or intentional text-only treatment |
| Query direction | A specific English search direction or generation concept |

### Pass B · After Layout and Style Selection

Finalize the production specification:

| Field | Requirement |
|---|---|
| Slot | Hero 16:9, Split 8:9, Main 16:10, Card 3:2, Portrait 3:4, or Square 1:1 |
| Fit | Photos usually use `cover`; screenshots, maps, charts, and dense UI usually use `contain` |
| Query/prompt | Final search query or production-ready generation prompt |
| Source and note | Original page, official source, author/institution, or "generated concept image" |

Use one asset for one clear narrative task. Keep image groups consistent in ratio, visual scale, and tone.

## 2. Choose Search or Generation

Use this decision order:

1. Use original images, screenshots, logos, and brand assets supplied by the user.
2. For real companies, products, people, places, events, news, public interfaces, historical objects, films, books, artworks, and other named objects, search for official or traceable images first.
3. For real websites, apps, dashboards, and interfaces, use a current official screenshot when exact fidelity matters.
4. Generate raster images for fictional, unpublished, confidential, unavailable, low-quality, or deliberately illustrative subjects.
5. Use charts, HTML/CSS/SVG, or generated infographics for processes, relationships, architecture, data, and other deterministic explanations. Use raster imagery for subjects whose meaning depends on showing real people, products, places, objects, or scenes.
6. Only when a slide genuinely reads best as pure typography — definitions, arguments, transitions, quotes, compact metrics, or sensitive subjects — use an intentional, strongly-typeset text-only slide. A hard-to-source asset is not such a case: generate a concept image (step 4) before falling back to text-only.

Label generated imagery that could be mistaken for documentary evidence as "generated concept image" in a slide note or source note.

## 3. Image Search Workflow

### 3.1 Write Specific Queries

Prefer English queries that combine the following elements into 4–8 words:

- Named entity: full name of the brand, product, person, place, event, or organization
- Visible object/action: rooftop installation, factory line, keynote stage, dashboard screenshot
- Context: year, city, industry, historical period, official release
- Medium or source: official press kit, product screenshot, documentary photo, Wikimedia Commons

Examples:

- Broad: `solar energy`
- Specific: `commercial rooftop photovoltaic installation documentary photo`
- Broad: `AI company`
- Specific: `Anthropic Claude official product interface screenshot`
- Broad: `business meeting`
- Specific: `carbon trading floor market display documentary`

### 3.2 Use Search Tools

1. Use the environment's image-search capability. In Codex, prefer `web.image_query` and run a separate query for each distinct visual intent.
2. For brands, products, people, events, and news, also search official websites, press kits, trusted media, public institutions, or Wikimedia Commons.
3. Open each candidate's source page and evaluate the full source context.
4. Select candidates with a verified subject, correct time/scene, sufficient resolution, useful crop allowance, traceable source, clean presentation, and credible context.
5. Download the selected original image to the current deck's `images/` working directory and use that stable local asset in production.
6. Record the source page and a short note. Images of real subjects should remain traceable through slide notes, speaker notes, or delivery notes.

Compare at least 2–3 candidates and choose the image with the strongest slot composition and evidentiary value.

## 4. Image Generation Workflow

Use the dedicated image generation/editing capability provided by the environment. In Codex, use `image_gen` and follow its image input and editing rules. Write one focused prompt for each independent slot.

A production-ready prompt must include:

1. Purpose and slot: `for slide 04 hero`, `16:9`, `safe negative space on the left`
2. Subject and action: specific objects, poses, quantities, and key details
3. Scene and background: place, time, and environmental depth
4. Medium and visual language: editorial documentary photo, product render, cut-paper illustration, etc.
5. Composition: shot scale, viewpoint, subject placement, negative space, and crop-safe area
6. Lighting: natural light, soft light, restrained contrast, or a defined studio setup
7. Palette and material: align with the selected style file's primary color, accent color, and texture
8. Clean-output requirements: a presentation-ready image with a clean crop area, free of visible text, watermarks, extra logos, slide chrome, and decorative borders

Prompt template:

```text
Create a [ratio] [medium] for slide [page/slot] about [specific subject].
Scene: [environment and action].
Composition: [camera/view, subject placement, safe margin, crop behavior].
Lighting: [lighting].
Palette/materials: [style-aligned constraints].
Keep it plausible and presentation-ready, with clean image content and crop-safe
space for the slide. Render it without visible text, watermarks, extra logos,
slide titles, page numbers, navigation chrome, or decorative borders.
```

After generation:

1. Quickly inspect the subject, hands, text, logos, perspective, repeated objects, brand consistency, and crop allowance.
2. Select a usable result; when the output has fundamental defects, revise the prompt and regenerate it.
3. Copy the selected output to the deck's `images/` directory using `{page number}-{semantic}.{ext}`, such as `04-ai-product-hero.png`.
4. Reference the selected localized asset from the final deck.

## 5. Asset Placement and Single-File Delivery

- Give each deck its own `images/` working directory.
- Name files `{two-digit page number}-{semantic}.{ext}` with concise semantic names.
- Prefer JPG/WebP for photos, PNG for transparency or lossless detail, and SVG for deterministic diagrams.
- Default to single-file HTML delivery: encode local raster images as `data:image/...;base64,...` and embed them in the HTML.
- If the user explicitly allows multi-file delivery, retain relative `images/...` paths.
- Preserve source records during production even when the final images are embedded.

## 6. Story-Driven Image Coverage

- Images are the default. Let the Story Plan decide *which* visual each slide carries, not *whether* to have one — aim for a strong majority of content slides to carry a real image, generated concept image, screenshot, chart, or diagram. Every image-bearing slide gives its visual a clear job: context, evidence, explanation, comparison, or emotion.
- **Coverage floor:** for image-forward decks (people, companies, products, places, travel, events, portfolios, art, architecture, objects, history), target roughly **70%+ of content slides with real or generated imagery**, using enough source-backed imagery to make the real subject concrete and credible. For strategy, technical, analytical, or abstract decks, cover most slides with diagrams, screenshots, and data visuals where they materially improve understanding.
- Use real/source-backed images when the subject itself is visual; use code-native graphics (HTML/CSS/SVG) for deterministic explanations; generate a concept image when a real photo is unavailable.
- Reserve intentional text-only slides for the cases where typography communicates best — arguments, definitions, transitions, quotes, compact metrics, and sensitive topics — and treat a run of consecutive text-only slides as a signal to add visual evidence.
- Review the deck as a whole for visual rhythm and evidentiary strength; if visuals are sparse, add them rather than accepting a text-heavy deck as the norm.

## 7. Lightweight Check

Before finalizing the HTML (no browser or preview step required):

- Make sure every `<img>` points at a reliable source — a user asset, a source verified during search, or a `text_to_image` URL — rather than a guessed or unverified URL.
- Give every image descriptive `alt` text so a failed load stays recoverable from context.
- Review covers, full-screen images, and generated-image prompts for obvious bad crops, text obstruction, or severe generation defects, and fix them in the markup/prompt.
- Keep acceptance lightweight: verify sources and alt text, plus one focused review of visually prominent images.
