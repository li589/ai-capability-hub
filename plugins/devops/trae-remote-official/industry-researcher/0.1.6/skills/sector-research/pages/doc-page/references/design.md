# Design Reference

Use this reference when deciding document structure and visual language.

## Reader Experience

The output should feel like a polished PDF-like A4 document rendered in HTML:

- a gray viewer background;
- centered white A4 paper surfaces;
- small, consistent gaps between pages;
- page numbers;
- quiet headings, rules, tables, captions, form lines, or section dividers appropriate to the document type;
- no marketing hero, dashboard cards, or decorative backgrounds.

The first screen should show the actual document. Do not create a landing page or explanatory UI around it unless the user asks for tooling controls.

## Document Type Fit

Match the document genre before choosing style:

- reports and research memos need narrative hierarchy, captions, evidence tables, and source lists;
- image-led reports need a clear image role, such as cover visual, evidence figure, explanatory diagram, or product/place/person signal;
- forms and records need precise table geometry, merged cells, writable spaces, and minimal decoration;
- resumes need compact scanning, strong entry hierarchy, and dense but readable bullets;
- schedules and rosters need stable grids, repeated labels, and handwritten space where useful;
- directories, manuals, and formal notices need numbering, TOC or clause structure, and restrained typography.

A document can combine these, but the dominant use should drive the first-page impression.

## Content And Layout Separation

Keep the content model independent of pagination:

- Write the document once as continuous HTML.
- Mark natural content units with `.flow-block`.
- Let the pagination framework create pages.
- Do not write "page 1", "page 2" sections by hand except for deliberate cover/table-of-contents layouts.

This prevents content edits from forcing manual repagination.

## Visual Tone

Use a restrained document palette:

- primary text: near black;
- secondary text: neutral gray;
- accent: one deep blue or similar institutional color;
- paper: white;
- viewer background: light gray.

Avoid one-note decorative palettes, gradient backgrounds, floating cards, or ornamental effects. The paper is the frame.

For scientific or research-heavy reports, choose a topic-specific theme from `research-palettes.md` before writing CSS. Color should support domain semantics such as ecology, clinical risk, policy divergence, or engineering benchmarks; it should not make the document feel like a themed poster.

For operational forms, records, resumes, schedules, and formal letters, mostly use black, white, gray, and one subtle accent only when it clarifies structure.

## Opening And Title Blocks

The first page should feel authored for the document, not copied from a generic report sample. Design the title cluster after deciding the genre:

- Research memos often work well with a small kicker, a clear title, a subtitle, and a compact metadata band.
- Formal forms may need a centered title and table-like metadata rows instead of a report header.
- Resumes need identity and contact information, not a report subtitle.
- Schedules need period, owner, and grid context close to the title.

Avoid repeating the same large left title rule, full-width divider, and rigid metadata line across unrelated documents. Those elements are acceptable only when they support the specific document's tone. Metadata should be compact and readable; it should not dominate the first viewport or make the page feel like a template preview.

## Images And Covers

Use images when they help the document do its job:

- cover images for polished reports, proposals, portfolios, and place/product/person-focused documents;
- figures, screenshots, and photos for evidence or explanation;
- logos, portraits, signatures, and seals when the genre expects identity or authorization.

Do not add generic decorative images to fill space. If an image is used, give it stable print dimensions, preserve important subject matter, and keep captions or source notes close to the image.

For evidence or product photos, prefer a normal figure with preserved subject readability. A shallow banner crop can look polished, but it is risky for hands, faces, products, screenshots, and objects the reader needs to inspect. If using a crop, validate that the important subject is not cut off, stretched, or visually pinned to an edge. Captions need positive spacing from image borders; avoid negative margins.

## Page Density

Aim for a printed-paper feel:

- headings are clear but not presentation-scale;
- paragraphs are dense enough for the genre, but not cramped;
- tables are compact and readable;
- captions provide evidence context when the document uses figures or sources;
- page margins feel intentional.

When a page has too much empty space, first check block granularity. A large next block may have been pushed to the next page.
