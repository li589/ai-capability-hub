# Research Palettes Reference

Use this reference before choosing report colors. The goal is not decorative variety; it is topic-appropriate, print-safe, accessible color that feels native to scientific papers and research memos.

## Core Principles

- Keep the paper mostly white and text near black. Color should carry hierarchy, table structure, callouts, and chart semantics.
- Use one dominant accent, one secondary accent, one warning or emphasis color, and a small chart sequence.
- Prefer palettes that are color-blind aware, perceptually ordered, or widely used in scientific visualization.
- Never use rainbow palettes for ordered data. Use sequential or diverging schemes when the data has numeric order.
- Test charts in grayscale when possible. Important distinctions should survive without hue.
- Keep table headers dark enough for white text, and keep zebra backgrounds very pale.

## Source Families

These palette families are good defaults for report work:

- **Okabe-Ito / Color Universal Design**: reliable categorical colors for lines, classes, study arms, or species groups. Useful when categories have no natural order.
- **Scientific Colour Maps / Crameri-style maps**: perceptually uniform sequential and diverging choices for physical, environmental, and geospatial data.
- **Viridis / Cividis family**: robust sequential scales for numeric values, especially heatmaps or model outputs.
- **ColorBrewer**: practical map and policy-report schemes for sequential, diverging, and qualitative data.
- **Paul Tol-inspired schemes**: restrained qualitative and diverging colors for papers with multiple series.

Use these as inspiration and tokenized report palettes rather than copying every source palette verbatim.

## Theme Selection

Choose one `data-theme` value on the `<body>` element in the template:

```html
<body data-theme="life-science">
```

If no theme is set, the template uses `classic-blue`.

| Theme | Best for | Character | Notes |
| --- | --- | --- | --- |
| `classic-blue` | General research memo, literature review, institutional report | Deep blue, neutral gray | Safest default for serious reports. |
| `life-science` | Biology, ecology, conservation, agriculture, medicine adjacent topics | Blue-green with amber emphasis | Based on color-blind-friendly categorical thinking. Good for species, cohorts, and field data. |
| `earth-science` | Climate, geology, hydrology, remote sensing, geography | Slate, teal, muted earth yellow | Use for maps and physical gradients; avoid decorative greens. |
| `clinical` | Medicine, epidemiology, public health, clinical operations | Steel blue and restrained red | Keeps risk signals visible without making the page feel alarming. |
| `social-policy` | Economics, policy, education, demographics, social science | Blue with muted red diverging accent | Good for before/after, increase/decrease, partisan-neutral policy work. |
| `engineering` | AI, systems, robotics, infrastructure, quantitative benchmarks | Charcoal teal with viridis-like chart sequence | Works well for model metrics, ablations, and architecture reports. |
| `humanities` | History, arts, literature, cultural research | Ink, muted oxblood, warm paper tones | More archival, but still restrained and printable. |

## CSS Tokens

Each theme should define these tokens:

```css
--accent: heading and link color;
--accent-2: secondary line or chart color;
--accent-3: warning, highlight, or tertiary chart color;
--table-head: table header background;
--rule: heading rules and dividers;
--soft: zebra rows and subtle bands;
--callout-bg: callout background;
--chart-1 ... --chart-6: reusable chart series colors;
```

Keep `--ink`, `--muted`, `--paper`, and `--bg` stable unless the report has a strong reason to change them.

## Palette Recipes

### classic-blue

- Accent: `#17227d`
- Secondary: `#4267a5`
- Emphasis: `#8b5e34`
- Chart colors: `#17227d`, `#4f78b6`, `#7a9cc6`, `#9b6b43`, `#6f7d3c`, `#7b6f8f`

### life-science

- Accent: `#0072b2`
- Secondary: `#009e73`
- Emphasis: `#e69f00`
- Chart colors: `#0072b2`, `#009e73`, `#e69f00`, `#cc79a7`, `#56b4e9`, `#d55e00`

### earth-science

- Accent: `#244f5f`
- Secondary: `#4f7f6f`
- Emphasis: `#b48a2c`
- Chart colors: `#244f5f`, `#4f7f6f`, `#8aa07a`, `#c2a35a`, `#7c6b5a`, `#5f6f8f`

### clinical

- Accent: `#245a7a`
- Secondary: `#4f7f9f`
- Emphasis: `#b04a4a`
- Chart colors: `#245a7a`, `#6f9fbd`, `#94b8c9`, `#b04a4a`, `#d28b7c`, `#7c6f9f`

### social-policy

- Accent: `#2f4b7c`
- Secondary: `#4b7a9f`
- Emphasis: `#a64b4b`
- Chart colors: `#2f4b7c`, `#6c8fb3`, `#b7c7d8`, `#c9b16d`, `#a64b4b`, `#7f6a93`

### engineering

- Accent: `#264653`
- Secondary: `#2a9d8f`
- Emphasis: `#e9c46a`
- Chart colors: `#264653`, `#2a9d8f`, `#3a86a8`, `#83b97f`, `#e9c46a`, `#b56576`

### humanities

- Accent: `#4a2f35`
- Secondary: `#7a5c4f`
- Emphasis: `#9a5b45`
- Chart colors: `#4a2f35`, `#7a5c4f`, `#9a5b45`, `#5f6f52`, `#6d7188`, `#b08a5a`

## Topic Rules

- Conservation, ecology, animal data: start with `life-science`; use `earth-science` if maps, land cover, or climate variables dominate.
- Clinical trials or disease burden: use `clinical`; reserve red for risk, adverse outcomes, or alert states.
- Policy comparisons or demographic splits: use `social-policy`; use diverging colors only when the metric has a meaningful midpoint.
- AI evals, benchmark reports, system architecture: use `engineering`; use chart colors for series and keep headings charcoal/teal.
- Archival, literary, historical, or cultural reports: use `humanities`; avoid sepia-heavy pages by keeping paper white and backgrounds pale.
- Mixed-category figures with no natural order: use Okabe-Ito-style categorical colors from `life-science`.
- Ordered heatmaps or intensity maps: prefer viridis/cividis-like sequences and label the scale; do not use rainbow.

## Print Checks

- Table header background must remain readable when printed.
- Callout backgrounds should be pale enough not to dominate the page.
- Do not rely on red/green alone. Use labels, symbols, ordering, or patterns in addition to color.
- If a report has charts, choose chart colors from the active theme tokens and include clear legends.

## Useful Source Links

- Crameri, F., Shephard, G. E., & Heron, P. J. (2020). "The misuse of colour in science communication." Nature Communications. https://www.nature.com/articles/s41467-020-19160-7
- Crameri Scientific Colour Maps. https://www.fabiocrameri.ch/colourmaps/
- ColorBrewer 2.0. https://colorbrewer2.org/
- Okabe-Ito Color Universal Design palette. https://jfly.uni-koeln.de/color/
- Matplotlib colormap documentation, including viridis and cividis families. https://matplotlib.org/stable/users/explain/colors/colormaps.html
