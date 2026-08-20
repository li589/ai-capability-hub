# Pagination Reference

Use this reference before implementing or changing the pagination framework.

## Core Model

The paginator renders a visible paged preview from a hidden continuous source document. The source remains the authority for print/PDF.

Recommended DOM:

```html
<section id="cover-source" class="has-cover" aria-hidden="true">
  <div class="cover-page">...</div>
</section>

<main id="source" class="doc-flow print-only" aria-hidden="true">
  <section class="flow-block">...</section>
  <section class="flow-block">...</section>
</main>

<div id="pages" aria-label="分页报告"></div>
<nav class="viewer-tools" aria-label="预览缩放">...</nav>
```

Generated DOM:

```html
<div class="page-frame">
  <article class="page">
    <div class="page-content">...</div>
    <div class="folio">1</div>
  </article>
</div>
```

Optional generated cover DOM:

```html
<div class="page-frame cover-frame">
  <article class="page">
    <div class="cover-page">...</div>
  </article>
</div>
```

In the default flow-pagination template, `.page-content` contains a `.page-slice` view of the same continuous `.doc-flow` content. The page slice is offset horizontally inside a fixed-height CSS multi-column layout. This gives a real paged screen preview without requiring the model to decide where paragraphs or tables should be split.

## Cover Pages

Use an authored cover when the genre expects one: formal reports, proposals, portfolios, image-led documents, or polished long-form deliverables. The cover is not part of the continuous `#source` flow.

Implementation rules:

- Keep cover markup in `#cover-source`, not inside `#source`.
- Enable it with `class="has-cover"` only when needed.
- Render it as `.cover-frame .page` with `padding: 0`; put any desired title-panel padding inside the cover component itself.
- Do not add `.folio` to the cover.
- Number generated content pages from 1, ignoring the cover.
- For print/PDF, show `#cover-source.has-cover` before `#source`, set `page: cover`, use `@page cover { margin: 0; }`, and force `break-after: page`.
- Keep the cover at exactly A4 dimensions (`var(--page-w)` by `var(--page-h)`) so screen preview and print agree.

Do not solve cover layout by adding a first `.flow-block` with negative margins or oversized images inside `#source`; it will still inherit content margins, page numbers, and column fragmentation behavior.

## Page Geometry

Use fixed A4 geometry for the page:

```css
:root {
  --page-w: 210mm;
  --page-h: 297mm;
  --page-pad-top: 23mm;
  --page-pad-x: 24mm;
  --page-pad-bottom: 20mm;
  --content-w: calc(var(--page-w) - var(--page-pad-x) * 2);
  --content-h: calc(var(--page-h) - var(--page-pad-top) - var(--page-pad-bottom));
  --column-gap: 36px;
}
```

The screen preview may scale the outer page with `transform: scale(...)`. Do not reduce the report font size for screen fit.

## Screen Preview Zoom

Paged HTML documents should behave like lightweight document viewers on screen:

- fit pages to the available viewport by default;
- allow user zoom with trackpad pinch gestures where browsers expose them as `ctrl/meta + wheel`;
- support `Ctrl/Cmd + +`, `Ctrl/Cmd + -`, and `Ctrl/Cmd + 0`;
- include small zoom buttons for discoverability;
- show zoom controls only while the user is adjusting scale, then fade them out;
- enforce a readable minimum scale and a reasonable maximum scale;
- optionally switch to two-column page preview when zoomed out and the viewport is wide enough.

Scale the `.page` with `transform: scale(var(--page-scale))` and resize `.page-frame` to reserve the scaled dimensions. Do not change the document font size for zoom.

Use print rules to hide `.viewer-tools`, reset `--page-scale` to `1`, reset preview columns to `1`, and remove screen-only frame sizing before print.

## Paginator Behavior

Algorithm:

1. Clear `#pages`.
2. If `#cover-source.has-cover` exists, clone it into an unnumbered `.cover-frame`.
3. Create a hidden measurement `.doc-flow.column-flow` with the same HTML as `#source`.
4. Measure how many fixed-height columns the source occupies.
5. Create one numbered `.page-frame` per measured column.
6. In each `.page-content`, add a `.page-slice` whose transform offsets the continuous column flow to the matching page.
7. Fit the generated page frames to the current preview zoom scale.

This is flow-level pagination. It intentionally lets the browser split paragraphs, lists, and ordinary tables in the same way print layout does. Avoid the old pattern of moving whole `.flow-block`s to the next page by default; that pattern is what creates large half-page gaps before big tables.

## Preventing Large Gaps

Large gaps usually mean the document is still using hard block-level pagination, fixed-height elements, or oversized keep-together blocks.

Fix by:

- using flow-pagination slices rather than moving whole `.flow-block`s;
- letting ordinary tables break naturally with `thead { display: table-header-group; }`;
- removing unnecessary `break-inside: avoid` from large sections;
- keeping figures and captions together only when the figure block fits within a page;
- splitting source lists into item-level blocks only when they are visually cleaner that way.

Do not fix pagination gaps by shrinking body text unless the overall document density is wrong.

## Limits

The screen preview is a close browser preview, not a full paged-media engine. Repeated table headers are reliable in Chrome print/PDF, but may not be identical in the screen column-slice preview. Footnotes, cross-references, and widow/orphan control still require a paged-media engine such as Paged.js or Vivliostyle.
