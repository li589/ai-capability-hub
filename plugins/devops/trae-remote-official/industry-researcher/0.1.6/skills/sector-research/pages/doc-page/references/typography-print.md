# Typography And Print Reference

Use this reference when setting paper dimensions, type, spacing, and print behavior.

## Page Style

Screen:

- body background: light gray;
- page background: white;
- centered pages;
- small page gap, usually 12-16px;
- subtle paper border and shadow.

Print:

- `@page { size: A4; margin: 23mm 24mm 20mm; }` or equivalent document margins;
- hide `#pages` and `.viewer-tools`;
- make `#source` visible and static;
- remove screen shadows, borders, and scaling from the printed source.

## Typography

Recommended Chinese report defaults:

- body: 10.5pt;
- line height: 1.65-1.75;
- table text: 9-9.5pt;
- captions: 8.5-9pt;
- H1: 20-22pt;
- H2: 15-17pt;
- H3: 12-13pt.

Use a Chinese serif stack for PDF-like reports:

```css
font-family: "Noto Serif SC", "Source Han Serif SC", "Songti SC", "SimSun", Georgia, serif;
```

Use system sans only if the report is more operational than paper-like.

## Margins

Good A4 starting point:

- top: 22-25mm;
- left/right: 22-25mm;
- bottom: 18-22mm;
- folio at 8-11mm from bottom.

If content feels too loose, reduce block spacing before reducing margins. If the page feels crowded, increase line height or block margins slightly.

## Screen Fit

Fit paper to the viewport by scaling the outer `.page`, not by changing report font sizes:

```css
.page {
  transform: scale(var(--page-scale, 1));
  transform-origin: top left;
}
```

Set `.page-frame` width/height to the scaled pixel size so pages reserve the correct visible space. In flow-pagination mode, the visible page contains a `.page-slice` of the continuous source; print CSS should print `#source` directly rather than printing the scaled preview slices.
