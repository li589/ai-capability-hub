# Images And Media Reference

Use this reference when a paged document includes or may benefit from images, screenshots, diagrams, scanned material, logos, portraits, signatures, seals, or cover artwork.

## Core Rule

Images in paper documents must have a job. Decide the image role before choosing size, crop, placement, and export strategy.

Common roles:

- cover image: establishes the subject, place, product, event, or visual identity;
- evidence image: screenshot, scanned record, field photo, chart export, or annotated figure;
- explanatory image: diagram, process map, architecture drawing, timeline, or layout;
- identity image: logo, portrait, certificate photo, seal, or signature;
- reference image: visual material the user provides to match a layout or style.

Avoid decorative stock-like images unless the document type genuinely needs a visual cover or brand signal. In operational forms, legal documents, resumes, and meeting records, images should be sparse and functional.

## Placement Patterns

### Cover Image

Use for formal reports, portfolios, proposals, travel/place documents, product documents, and polished long-form deliverables when a first-page visual is useful.

When the document needs a true unnumbered cover, place the cover in `#cover-source.has-cover` rather than inside the paginated `#source` flow. This lets the cover use a zero-margin `@page cover` print rule, full-page image treatment, and no folio, while body content starts at page 1 with normal margins.

Recommended patterns:

- full-width image band above or below the title block;
- full-bleed page background only when print-safe and text contrast is guaranteed;
- image with title overlay only when the text remains highly readable;
- logo plus image only when both support the document identity.

Avoid:

- tiny generic thumbnails on a cover;
- dark blurred atmospheric backgrounds when the subject needs inspection;
- cover images in documents that are primarily forms, schedules, or legal records unless requested.

### Inline Figure

Use for evidence, diagrams, screenshots, photos, or visual explanations inside a report or manual.

Recommended structure:

```html
<figure class="flow-block figure-block">
  <img src="..." alt="...">
  <figcaption>图 1. 简短说明和来源。</figcaption>
</figure>
```

Keep the figure and caption together in one `.flow-block`. If the image is large, make it its own block so the paginator can move it cleanly to the next page.

For object, product, robot, hand, face, interface, or other inspection-oriented images, prefer a normal figure that preserves the subject over a shallow banner crop. A useful pattern is a two-column evidence figure: image on the left, source note or caption on the right. This keeps the image readable while avoiding a generic cover-banner look.

```html
<figure class="flow-block figure-pair">
  <img src="..." alt="...">
  <figcaption><strong>图 1. 标题</strong>说明、观察重点和来源。</figcaption>
</figure>
```

Do not use negative margins to pull captions over or into image borders. If a caption feels too far away, reduce the figure margin or caption font size instead.

### Mermaid Or SVG Diagram

Use Mermaid when a flowchart, process map, sequence diagram, state diagram, or architecture sketch is easier to maintain as text. Render the Mermaid source to SVG before inserting it into the report:

```bash
node <SKILL_ROOT>/scripts/render-mermaid-to-svg.mjs diagrams/process.mmd assets/process.svg
```

Then insert it as a normal figure:

```html
<figure class="flow-block figure-block diagram-block">
  <img src="assets/process.svg" alt="流程图说明">
  <figcaption>图 2. 流程图说明。</figcaption>
</figure>
```

Prefer SVG for PDF because it stays sharp at print scale. Keep Mermaid source files such as `diagrams/process.mmd` in the deliverable folder for maintainability. Avoid loading Mermaid JavaScript in the final report unless runtime interactivity is required; pre-rendered SVG is more reliable for PDF and print.

### Image Grid

Use for product comparisons, field photos, before/after examples, evidence galleries, or portfolio samples.

Recommended structure:

- two-column grid for image-heavy reports;
- three-column grid only for small thumbnails or contact sheets;
- each image has a label or caption when the reader needs to compare items.

Avoid image grids in forms unless they are part of an inspection or evidence record.

### Logo, Portrait, Seal, Or Signature

Use only when the document genre expects it.

Recommended patterns:

- logo in a formal header, cover, certificate, or letterhead;
- portrait in resumes, bios, certificates, or people profiles;
- signature/seal in formal letters, approvals, certificates, or contracts;
- fixed dimensions with `object-fit: contain` to avoid distortion.

Do not stretch identity images. Preserve aspect ratio.

## Sizing And Print Quality

Use stable physical dimensions for print-oriented images:

```css
.figure-block img {
  display: block;
  max-width: 100%;
  height: auto;
}

.cover-image {
  width: 100%;
  height: 86mm;
  object-fit: cover;
}

.logo {
  width: 28mm;
  height: 12mm;
  object-fit: contain;
}
```

Guidelines:

- Prefer images with enough resolution for their printed size. Aim for roughly 150-300 DPI for important print images.
- For screenshots, avoid scaling them so small that UI text becomes unreadable.
- Use `object-fit: cover` only when cropping is acceptable; use `object-fit: contain` when the full image must be visible.
- Reserve enough caption and margin space so images do not collide with page numbers.
- Do not encode oversized images unnecessarily; compress large photos before embedding when file size becomes a problem.

## Pagination Behavior

Images are common sources of page gaps and clipping.

Rules:

- Keep image plus caption in one `.flow-block`.
- If a figure is taller than the page content area, reduce the image size, split the figure, or move supporting text outside the block.
- Do not let `.page-content { overflow: hidden; }` hide the bottom of an image or caption.
- For galleries, split rows into separate `.flow-block`s when a full grid is too tall.
- When an image must sit next to text, validate both desktop preview and print output; side-by-side layouts are fragile on narrow pages.

## Accessibility And Semantics

- Provide meaningful `alt` text for informative images.
- Use empty `alt=""` only for purely decorative images.
- Use `<figure>` and `<figcaption>` for report figures and evidence images.
- Preserve source or credit text when required.
- For reference screenshots provided by the user, do not include them in the final document unless they are part of the requested deliverable.

## Editable Export Notes

Images can export to DOCX only when the exporter or downstream converter can access the image bytes.

Prefer:

- local relative image files near the HTML when building a portable package;
- data URLs only for small images where portability matters more than file size;
- ordinary `<img>` elements over CSS background images when the image should be editable/exportable;
- real tables and captions around images rather than canvas-only composites.

Avoid relying on:

- CSS background images for important content;
- canvas-rendered charts without an alternate image or semantic table;
- complex SVG with text if editable DOCX fidelity is required;
- remote images that may fail offline or during export.

## Image Validation Checklist

- The image role is clear: cover, evidence, explanation, identity, or reference.
- The image is not clipped, stretched, blurred, or too small to read.
- Cropping is intentional and does not remove important subject matter.
- Captions stay with figures.
- Print output preserves image size and contrast.
- The document still works without decorative images if they fail to load.
- Export requirements are considered when Word, Google Docs, Feishu Docs, or editable output is requested.
