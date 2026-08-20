# Content Blocks Reference

Use this reference when structuring paged document content.

## Block Granularity

`.flow-block` is a semantic grouping hook, not a hard pagination unit in the default flow-pagination template. Choose blocks based on document meaning and export cleanliness, not because the model is trying to guess page breaks.

When the document may later become Word, Google Docs, Feishu Docs, or another editable document, keep every `.flow-block` semantically clean. The block may control pagination, but its children should still be ordinary document elements such as headings, paragraphs, lists, tables, figures, captions, form fields, and source items. Do not make essential content depend on generated page wrappers, CSS pseudo-elements, canvas-only charts, or absolute positioning.

Good blocks:

- a report title cluster;
- a form title and short metadata table;
- one resume entry;
- one schedule grid section;
- one formal clause plus its supporting list;
- one short narrative section;
- one heading plus an opening paragraph;
- one table plus its caption;
- one diagram plus its caption;
- one source-list item;
- one callout.

Risky blocks:

- an entire chapter with multiple tables;
- a whole references section;
- a long table wrapped in a keep-together block;
- a full resume with many entries;
- a long form table with an oversized notes cell;
- many unrelated subsections in one block.

## Headings

Keep headings attached to at least one paragraph when possible. If a heading is stranded at the bottom of a page, combine it with the first paragraph in the same `.flow-block`.

For references or appendices, split the heading and individual items if it helps fill leftover space. In that case, accept that the heading can appear near the bottom only if at least one item follows.

## Tables

Keep ordinary tables as real HTML tables and let browser pagination split them. This is the preferred path for simple data tables because it avoids large blank areas before the table.

Tables should have:

- compact font size around 9-9.5pt;
- clear header row;
- light zebra striping when helpful;
- a caption when the table is evidence.

Required CSS for ordinary long tables:

```css
table { break-inside: auto; page-break-inside: auto; }
thead { display: table-header-group; }
tfoot { display: table-footer-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
```

This makes PDF/print continue the table on the next page and repeat the header. The screen preview should still show the table crossing pages because it slices the same continuous flow.

### Manual Split Tables

Use manual split tables only when browser row fragmentation is not enough: merged cells, inspection forms, schedules, row groups that must stay together, or tables whose single row is taller than a page.

```html
<section class="flow-block">
  <table>
    <caption>表 1. 指标对比。</caption>
    <thead>...</thead>
    <tbody>...</tbody>
  </table>
</section>
<section class="flow-block">
  <table>
    <caption>表 1. 指标对比（续）。</caption>
    <thead>...</thead>
    <tbody>...</tbody>
  </table>
</section>
```

Do not use script-based split tables for:

- `rowspan` or `colspan` tables;
- Word/WPS-style forms with merged cells;
- rows that must stay grouped with adjacent rows;
- tables with a single row taller than the page content area.

For publication-grade table footnotes, repeated headers in both screen and print, and strict widow/orphan control, use Paged.js or Vivliostyle.

## Forms And Records

For Word/WPS-like records, use real tables with `colspan` and `rowspan` for geometry. These documents may legitimately be one large table, but they must still fit the page or be split into semantic pieces.

Good form blocks:

- title plus short metadata rows;
- one short bordered form table;
- one long content table split into page-sized sections;
- one signature or review block.

Risky form blocks:

- one table with a long notes cell that exceeds the content area;
- fixed-height cells that hide overflow;
- absolute-positioned labels that cannot export cleanly.

If a form must stay on one page, use a document-specific compact mode and validate that no content clips. If it can span pages, split it into repeated tables with clear section labels.

## Resumes And Directories

For resumes, CVs, directories, and manuals, keep each entry or section as its own `.flow-block`. A heading should travel with at least one entry. Avoid making the entire document a single block merely to preserve a layout.

## Figures And Diagrams

Keep each figure and caption together in one `.flow-block`. Use diagrams only when they clarify architecture, process, decision logic, or relationships.

Do not add decorative figures merely to fill pages.

For image-based blocks:

- use `<figure>` and `<figcaption>` for report figures, screenshots, field photos, and evidence images;
- use ordinary `<img>` elements for content images so export tools can find them;
- use CSS background images only for decorative treatment or carefully validated cover designs;
- split image grids into row-level `.flow-block`s when a full grid is too tall;
- keep logos, portraits, signatures, and seals in fixed-size containers with `object-fit: contain`.

If an image must be cropped, make the crop intentional and use `object-fit: cover`. If the full image must remain visible, use `object-fit: contain`.

### Mermaid And Diagram Blocks

Mermaid is a good source format for flowcharts, sequence diagrams, state diagrams, and simple architecture diagrams. For final paper reports, render Mermaid to SVG first and insert the SVG as a normal figure:

```html
<figure class="flow-block figure-block diagram-block">
  <img src="assets/process.svg" alt="流程图说明">
  <figcaption>图 2. 流程图说明。</figcaption>
</figure>
```

Keep the `.mmd` source file near the report, such as `diagrams/process.mmd`, so the diagram can be edited later. Avoid runtime Mermaid in final deliverables because browser timing can make PDF export unreliable.

## Source Lists

Do not put all sources in one large `.flow-block`. Use one item per block:

```html
<section class="source-items">
  <div class="flow-block"><h2>资料来源</h2></div>
  <p class="flow-block source-item">OpenAI Help Center, ...</p>
  <p class="flow-block source-item">Mem0 Docs, ...</p>
</section>
```

Use CSS counters on `.doc-flow` so numbering works in `#source`, screen page slices, and PDF export.
