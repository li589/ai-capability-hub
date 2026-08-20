---
name: doc-page
description: Create polished printable document pages for reports, forms, schedules, resumes, memos, and records, with clean A4 layout and optional PDF or DOCX export when needed.
---

# Doc Page

## Overview

Use this skill to create document-style HTML outputs that look like paged A4 paper in the browser and print/export cleanly. The core pattern is: write content once as a continuous semantic document, then generate a paged screen preview from that same flow while letting browser print handle final A4 fragmentation.

This is a paged-document framework, not a single research-report template. Before choosing any visual treatment, identify the document type and compose the page from appropriate document components. Do not force form records, resumes, schedules, directories, letters, or tables into a research report shape.

Do not hand-author the document as page 1, page 2, page 3 unless the user explicitly wants manual layout. Keep content and pagination separate.

## Workflow

1. Read `references/document-types.md` before choosing the document shape. Use it to classify the request and select a flexible composition strategy.
2. Read `references/design.md` before choosing visual tone, reader experience, density, and whether the output should feel like a report, form, resume, schedule, letter, or directory.
3. Read `references/research-palettes.md` before choosing colors for scientific, medical, policy, environmental, engineering, humanities, or other evidence-heavy reports. For operational forms and plain documents, prefer neutral ink and sparse accent color.
4. Read `references/pagination.md` before building or modifying the A4 pagination framework.
5. Read `references/content-blocks.md` before defining sections, tables, figures, source lists, form rows, directory items, resume entries, or block granularity.
6. Read `references/images-media.md` when the document includes or may benefit from cover images, inline figures, screenshots, diagrams, photos, logos, portraits, seals, signatures, scanned material, or image-based references.
7. Read `references/typography-print.md` before setting font sizes, margins, line height, tables, images, and print CSS.
8. If the user may need Word, Google Docs, Feishu Docs, or editable docs output, keep `#source` semantic from the start and plan to use `scripts/export-paper-to-docx.mjs` after HTML validation. Do not treat the generated `.page-frame` preview DOM as the editable document source.
9. Create one dedicated document folder in the user's output directory before authoring. The folder name should be a filesystem-safe slug or title for the document.
10. Put the title-named HTML file inside that folder, then start from `assets/paged-report-template.html` as the reusable pagination shell and compose the source content and CSS components around the specific document.
11. Put document content in a hidden continuous source container such as `#source`, using clean semantic elements and `.flow-block` only where grouping still matters.
12. Let the screen paginator generate visible `.page-frame > .page > .page-content` page slices into `#pages`; it should not hand-split tables into artificial continuation blocks.
13. Verify with `references/validation.md`: refresh the browser, inspect page gaps, check table crossing behavior, and scan for large accidental whitespace. Do not export PDF during the default flow unless the user explicitly asks for PDF, print-ready delivery, or another final format that requires a PDF file.

## Required Architecture

Use this architecture unless there is a strong local reason not to:

- `#source`: hidden continuous document content and the source used for print/PDF.
- `#cover-source`: optional hidden authored cover page. Use only when the document needs an unnumbered cover that does not participate in flow pagination.
- `.doc-flow`: shared styling scope for the source, measurement flow, and visible page slices.
- `.flow-block`: semantic grouping for headings, figures, callouts, or short sections; it is not a hard page-break contract.
- `#pages`: empty visible container populated by the screen paginator.
- `.viewer-tools`: optional-but-default transient screen preview controls for zooming paper pages; hidden in print.
- `.page-frame`: scaled screen preview wrapper.
- `.page`: fixed A4 paper surface.
- `.page-content`: fixed printable content area inside page margins.
- `.page-slice`: a column-fragment view of the continuous source for one screen page.
- `.folio`: generated screen page number.

For reports or proposals that need a true cover page, keep the cover outside `#source`. Add `class="has-cover"` to `#cover-source`, compose a complete A4 cover inside it, and let the paginator prepend it as a `.cover-frame`. Cover pages do not receive `.page-content` margins, do not get `.folio`, and do not count toward content folio numbering; the first generated `#source` page remains page 1. In print, the cover uses a named `@page cover { margin: 0; }` rule and `break-after: page`, while body content continues to use the normal A4 margins and browser fragmentation.

The default screen paginator should measure the continuous document as fixed-height CSS columns and create one page per column slice. This keeps the browser preview paginated while allowing paragraphs and ordinary tables to break naturally instead of forcing entire `.flow-block`s onto the next page. For PDF, print the original `#source` with `@page` margins so Chrome's print engine handles final fragmentation, table row breaks, and repeated table headers.

The screen preview should support document-viewer zoom controls by default. Use the template's transient `.viewer-tools` pattern: controls are hidden until the user zooms with trackpad/`Ctrl`/`Cmd` wheel, keyboard shortcuts, or buttons; they show the current percentage briefly, then fade out. Print output must hide the controls and render pages at true A4 scale.

## Document Composition

Choose a composition, not a rigid template:

- research report: title cluster, executive summary, narrative sections, tables, charts, source list;
- image-led report or cover document: cover visual, title block, figure captions, source/credit notes;
- form/table record: centered title, bordered metadata rows, merged cells, long text cells, signature or review rows;
- resume/CV: compact identity header, two-column or sectioned entries, timeline blocks, skills and project lists;
- directory/table of contents document: cover or title block, generated or hand-authored TOC, numbered sections, appendices;
- schedule/grid: dense grid, repeated day/time headers, notes and responsibility areas;
- letter/memo/contract: formal header, parties or recipients, clauses, date/signature fields.

Use these as document-type signals and component sets. Adapt spacing, columns, and hierarchy to the user’s content rather than copying a fixed sample.

## Authored Openings

Treat the first page as an authored document opening. Let the document's genre, audience, and argument determine the structure:

- A report can open with a thesis paragraph, research question, executive finding, abstract, evidence table, figure, or title-only header.
- A formal record can open with a centered title and table-like metadata.
- A schedule can open with period, owner, and grid context close to the title.
- Metadata should read like document information: compact, purposeful, and matched to the genre.
- If the first page includes an image, choose a role and crop strategy. Do not turn evidence photos into shallow banner strips unless the crop is intentional and the subject still reads clearly.
- Captions must sit with the image and have breathing room. Avoid negative-margin captions that visually collide with image borders.

## Output Expectations

- Make the first viewport show real paper pages, not a landing page.
- Generate a polished HTML document as the default deliverable. Do not generate a PDF unless the user explicitly requests PDF, printable/final paginated delivery, or needs a PDF for sharing/printing.
- Preserve `<!-- Generated by Trae Work -->` as the first line of every generated HTML file, including files copied from `assets/paged-report-template.html`.
- Always create a dedicated folder for the document and place the HTML file inside it. Do not leave the HTML directly in the workspace/output root.
- Name both the folder and the HTML file after the document title using a filesystem-safe slug or title, for example `值日表/值日表.html`, `会议记录表/会议记录表.html`, `非洲野兔数据调研报告/非洲野兔数据调研报告.html`, or `african-hare-data-report/african-hare-data-report.html`. Avoid generic `index.html` unless the user is explicitly asking for a website folder or deployable site.
- Keep the document folder self-contained. For pure single-HTML documents, the folder may contain only the HTML file. When there are non-HTML dependencies, include only the files required by that HTML, such as `assets/...` or `diagrams/...`.
- Use relative paths only for dependencies inside the document HTML; do not reference absolute local paths, `file://` URLs, remote CDNs, or workspace-global asset folders in the final HTML.
- Match the document genre: a form should look like a form, a resume like a resume, a schedule like a schedule, and a research memo like a serious paper.
- Use images intentionally: cover visuals, figures, screenshots, logos, portraits, seals, and signatures should match the document purpose and remain print-safe.
- Use restrained color. Choose a topic-appropriate research palette only when the document is research- or evidence-heavy; plain operational documents may use mostly black, white, gray, and one modest accent.
- Preserve real document typography; screen fitting should scale the paper preview, not shrink text inside the layout.
- Keep preview zoom behavior available unless the user explicitly asks for a static print-only file. Do not implement zoom by changing body font sizes.
- Avoid large unexplained gaps. If gaps appear, reduce block granularity or revise the document component structure before changing font size.
- Use print media rules so the same HTML can be exported as PDF.
- Do not create screenshot preview files such as `preview.png` by default. Use browser automation for validation without saving screenshots unless the user explicitly asks for an image preview or visual artifact.
- In the final response, include the final HTML document path with a `computer://` prefix so Trae can render it.

## Resources

- `references/design.md`: reader experience and visual principles.
- `references/document-types.md`: flexible document-type selection and component composition.
- `references/research-palettes.md`: topic-driven scientific color palettes and CSS theme tokens.
- `references/pagination.md`: content/layout separation and A4 paginator rules.
- `references/content-blocks.md`: block granularity, lists, tables, figures, and source sections.
- `references/images-media.md`: image roles, cover images, figures, screenshots, logos, print sizing, and export considerations.
- `references/typography-print.md`: A4 dimensions, margins, font sizes, line heights, and print behavior.
- `references/validation.md`: QA checklist and common failure modes.
- `assets/paged-report-template.html`: reusable single-file HTML starting point.
- `scripts/export-paper-to-pdf.mjs`: browser-print exporter for the visible paginated paper preview.
- `scripts/export-paper-to-docx.mjs`: optional exporter that extracts optional `#cover-source.has-cover` plus semantic `#source` into clean conversion HTML and uses Pandoc when available to create `.docx`.
- `scripts/render-mermaid-to-svg.mjs`: optional Mermaid CLI wrapper for rendering `.mmd` diagrams to SVG.

## Large Tables

For ordinary large tables, prefer native browser pagination rather than AI-authored or script-authored "continued table" chunks:

```html
<table>
  <thead>...</thead>
  <tbody>...</tbody>
</table>
```

Required table CSS:

```css
table { break-inside: auto; page-break-inside: auto; }
thead { display: table-header-group; }
tfoot { display: table-footer-group; }
tr { break-inside: avoid; page-break-inside: avoid; }
```

This allows Chrome print/PDF to continue a table on the next page and repeat the header without leaving a large blank area before the table. The screen preview uses column slices of the same source, so it also shows the table crossing page boundaries, though repeated headers in the screen preview may differ from the final PDF.

Use manual split tables only for complex merged-cell forms, inspection sheets, schedules, or any table where row grouping must stay exact. For publication-grade footnotes, cross-references, widow/orphan control, or exact table header behavior in both screen and print, use Paged.js or Vivliostyle.

## Mermaid Diagrams

Use Mermaid as diagram source, but insert rendered SVG into the final paper report. Do not depend on runtime Mermaid rendering in the final HTML unless the user specifically wants an interactive HTML artifact.

Recommended workflow:

1. Write Mermaid source under `diagrams/name.mmd`.
2. Render SVG:

```bash
node <SKILL_ROOT>/scripts/render-mermaid-to-svg.mjs \
  diagrams/name.mmd \
  assets/name.svg
```

3. Insert the SVG as a normal figure:

```html
<figure class="flow-block figure-block diagram-block">
  <img src="assets/name.svg" alt="流程图说明">
  <figcaption>图 1. 流程图说明。</figcaption>
</figure>
```

SVG is preferred for PDF export because it remains sharp and stable. For DOCX export, SVG may need to be converted or embedded as an image depending on the downstream converter. Keep the `.mmd` source file near the report so the diagram remains maintainable.

## PDF Export

Use `scripts/export-paper-to-pdf.mjs` only when the user explicitly asks for PDF, printable output, or final paginated delivery. The default deliverable for Doc Page tasks is the HTML file with print CSS and paged preview; PDF export is an opt-in follow-up, not a routine validation step. In the default flow-pagination template, the script waits for the visible `#pages` preview, then prints the semantic `#source` through browser print CSS so final PDF pagination uses native A4 fragmentation. Older fixed-page templates may still print the visible `.page-frame` preview.

```bash
node <SKILL_ROOT>/scripts/export-paper-to-pdf.mjs \
  path/to/report.html \
  path/to/report.pdf
```

Common options:

- `--chrome=/path/to/Chrome`: use a specific Chrome or Chromium executable.
- `--render-dir=tmp/pdfs`: render PDF pages to PNGs with Poppler for visual QA.
- `--pdfinfo=/path/to/pdfinfo`: use a specific Poppler `pdfinfo`.
- `--pdftoppm=/path/to/pdftoppm`: use a specific Poppler `pdftoppm`.
- `--timeout-ms=30000`: adjust the browser wait timeout for slow images or scripts.
- `--no-validate`: skip `pdfinfo` validation when Poppler is unavailable.
- `--quiet`: print only the output path.

Export behavior:

- waits for `.page-frame` pages and all `<img>` elements to load;
- checks visible preview pages for vertical clipping;
- prints with `format: "A4"`, `printBackground: true`, and `preferCSSPageSize: true`;
- validates page count and A4 size with `pdfinfo` when available;
- optionally renders PNG page previews when `--render-dir` is provided.

After PDF export, visually inspect rendered pages when layout matters. Confirm images, tables, captions, page numbers, and final references are not clipped or overlapping.

## Docs Export

Use `scripts/export-paper-to-docx.mjs` only when the user explicitly asks for Word, `.docx`, Google Docs, Feishu Docs, or an editable document deliverable. The script ignores the paginated browser preview and exports from optional `#cover-source.has-cover` followed by `#source`.

```bash
node <SKILL_ROOT>/scripts/export-paper-to-docx.mjs \
  path/to/report.html \
  path/to/report.docx \
  --keep-clean-html
```

Options:

- `--html-only`: write a clean conversion HTML file without creating DOCX.
- `--clean-html=path/to/report.clean.html`: choose the clean HTML output path.
- `--reference-doc=path/to/reference.docx`: pass a Word style template through to Pandoc.
- `--pandoc=/path/to/pandoc`: use a specific Pandoc binary.
- `--python=/path/to/python3`: use a specific Python runtime for the fallback exporter.
- `--no-python-fallback`: fail instead of using the Python fallback when Pandoc is unavailable.
- `--keep-clean-html`: keep the intermediate clean HTML after DOCX export.

Dependency notes:

- DOCX export prefers Pandoc. If Pandoc is missing, the script uses the bundled Python fallback when `python-docx` and `lxml` are available.
- The Python fallback maps common Doc Page structures to editable Word objects: headings with bottom rules, callouts with a shaded one-cell table and left border, compact styled tables with fixed `tblGrid` column widths, captions/source items, and native Word chart parts for simple `.bar-row` bar charts.
- For Google Docs, import the generated `.docx` when possible; importing the clean HTML is a fallback.
- For Feishu/Lark Docs, use the `.docx` or the clean semantic HTML as the import/source material. For strict editable fidelity, native Docx block creation is still better than importing the paginated browser view.

Editable export limitations:

- CSS pagination, page shadows, generated folios, and browser-only preview wrappers do not map to Docs.
- Headings, paragraphs, lists, real tables, captions, source items, and simple `.bar-row` charts map best.
- Arbitrary CSS layout, canvas-only visuals, complex SVG, pseudo-elements, and browser-specific typography still require custom export mapping or a commercial DOCX engine for high fidelity.
