# Document Types Reference

Use this reference before choosing a document shape. The goal is flexible document composition, not a growing set of rigid templates.

## Core Rule

Start by identifying the document genre and the user’s practical need:

- Is it meant to be filled in, signed, or checked?
- Is it meant to be read as a narrative report?
- Is it meant to scan quickly, like a schedule or directory?
- Is it meant to present a person, role, or portfolio?
- Is it meant to preserve formal wording, clauses, or meeting records?

Then compose the page from document components that fit that need. Do not force every request into the default research-report title, subtitle, sections, and evidence-table pattern.

## Common Document Shapes

### Research Report Or Paper Memo

Use when the user asks for a report, research summary, literature review, analytical memo, evidence review, or paper-like writeup.

Typical components:

- title cluster with date, author, scope, and purpose;
- abstract or executive summary;
- narrative sections with headings;
- evidence tables, figures, charts, and captions;
- source list split into small flow blocks.

Tone:

- serif body text, restrained accent color, clear headings, compact but comfortable tables;
- topic-driven palette when scientific, policy, medical, engineering, humanities, or data-heavy.

### Form Or Table Record

Use when the user asks for a meeting record, duty roster, registration form, inspection sheet, approval sheet, handover sheet, receipt, checklist, or any document resembling a Word/WPS form.

Typical components:

- centered formal title;
- one large bordered table;
- metadata rows with merged cells via `colspan` and `rowspan`;
- fixed label columns and writable value cells;
- long content cell for notes, meeting minutes, or observations;
- signature, reviewer, or date fields.

Tone:

- mostly black lines and white background;
- little or no color unless it helps status or section grouping;
- table geometry matters more than decorative hierarchy.

Implementation notes:

- Use real HTML tables for form geometry.
- Keep a whole short form as one `.flow-block`.
- If a table or long cell exceeds one page, either split the form into multiple semantic tables with repeated labels, use a compact-fit mode, or switch to a stronger paged-media engine. Never allow clipping.

### Resume Or CV

Use when the user asks for a resume, CV, bio sheet, profile, one-page introduction, or candidate summary.

Typical components:

- compact identity header;
- contact and role summary;
- experience entries with company, role, dates, and bullets;
- education, skills, projects, awards;
- optional sidebar only when it improves scanning.

Tone:

- dense, professional, and scan-friendly;
- avoid report-style chapter headings and long paragraphs;
- use subtle rules, small caps, or compact section labels.

Implementation notes:

- Entries should be separate `.flow-block`s so pagination can move them cleanly.
- Avoid absolute positioning unless the resume is intentionally one-page and content is known to fit.

### Directory, TOC, Or Manual

Use when the user asks for a table of contents, handbook, rules, policy document, guide, SOP, or long formal document.

Typical components:

- cover or title block if appropriate;
- table of contents;
- numbered sections and subsections;
- definitions, clauses, appendices, and revision history;
- running section markers only if they do not consume excessive page space.

Tone:

- formal and navigable;
- hierarchy and numbering are more important than decoration.

Implementation notes:

- Use semantic headings for export and accessibility.
- Keep TOC entries and appendix items in small blocks to avoid gaps.

### Schedule, Roster, Or Grid

Use when the user asks for a duty table, timetable, curriculum schedule, shift plan, meal plan, project calendar, or weekly/monthly grid.

Typical components:

- title and period fields;
- grid with days, times, people, rooms, or tasks;
- notes, rules, handover, or signature areas;
- optional repeated headers for multi-page grids.

Tone:

- operational, legible, and writable;
- stable row/column sizing matters more than narrative styling.

Implementation notes:

- Use `table-layout: fixed` for predictable printable grids.
- Keep row heights sufficient for handwritten notes when the output is meant to be printed and filled.

### Formal Letter, Memo, Contract, Or Notice

Use when the user asks for an announcement, letter, notice, formal memo, agreement, contract, statement, or certification.

Typical components:

- issuing organization or recipient;
- title or subject line;
- body paragraphs, clauses, or numbered terms;
- effective dates, attachments, signatories, seals, and contact fields.

Tone:

- formal, low-color, stable, and spacious enough for reading;
- avoid research-report captions and chart styling unless evidence is part of the document.

Implementation notes:

- Keep clauses as separate `.flow-block`s when the document spans pages.
- Avoid splitting signatures from their preceding declaration.

## Composition Heuristics

- Start from the simplest shape that honestly matches the document.
- Prefer reusable components over fixed full templates: title block, metadata table, long content cell, section stack, checklist, schedule grid, signature block, source list.
- Let content length decide density: one-page forms may use compact-fit; long reports need smaller flow blocks and more pages.
- Match the user’s reference image or known document genre when one is provided.
- Preserve editability: use real headings, paragraphs, lists, and tables rather than drawing text with absolute-positioned boxes.

## Anti-Patterns

- Using a research-report hero/title cluster for a form, resume, schedule, or meeting record.
- Adding decorative colors to operational forms.
- Treating one sample template as the required visual identity for all documents.
- Making a whole long table one unsplittable block and clipping the bottom.
- Shrinking body text globally to hide pagination problems.
