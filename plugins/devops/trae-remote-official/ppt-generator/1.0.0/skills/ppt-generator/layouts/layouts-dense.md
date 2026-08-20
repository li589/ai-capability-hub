#Layouts · High Density Pages

Information-intensive layout - used to display large amounts of data, multi-row tables, indicator matrices, comparative analysis and other scenarios that require high-density information to be carried on a single page.

See `layouts-structural.md` for canvas constraints and general font size benchmarks.

**Design Principles**:
- The overall font size is reduced (main text 12-13px) to maximize information capacity
- Tightening of line spacing (1.3-1.4) to reduce vertical waste
- padding inherits the global slide spacing (`var(--pad-y) var(--pad-x)`) and does not override it separately
- Replace large spaced partitions with very fine dividers (1px) and subtle background color differences
- The title area (`.dense-head`) is consistent with other layouts: grid two-column layout, left column kicker + title (`.h-1`), right column description (`.lead`) bottom-aligned
- **Vertically centered, not forced to fill up** - Use `auto auto` (not `auto 1fr`) for grid row height, and use `align-content: center` to center the title + content vertically. The content is arranged according to the natural height and does not stretch to fill the page.

---

## T18 · Dense Table · Data table page

**Purpose**: Display structured tabular data (5-8 rows × 4-6 columns), such as function comparison, specifications, pricing plans, etc.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Top: kicker + title (compact)
- Body: full width table area

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Title (`.h-1`, consistent with global) |
| lead(optional) | One line description (`.lead`, right column bottom aligned) |
| table-header | Table header row (4-6 columns) |
| table-rows × 5-8 | data rows |

**HTML skeleton**:
```html
<section class="slide s-dense-table">
  <div class="dense-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="dense-table stagger">
    <div class="dt-row dt-header">
      <span>[Column 1]</span>
      <span>[Column 2]</span>
      <span>[Column 3]</span>
      <span>[Column 4]</span>
      <span>[Column 5]</span>
    </div>
    <div class="dt-row">
      <span class="dt-label">[row title]</span>
      <span>[value]</span>
      <span>[value]</span>
      <span>[value]</span>
      <span>[value]</span>
    </div>
    <!-- Repeat lines 5-8 -->
  </div>
</section>
```

**Layout Details**:
- `.s-dense-table`: `grid-template-rows: auto auto; align-content: center; gap: 20px` (padding inherits global)
- `.dense-head`: `display: grid; grid-template-columns: auto 1fr; align-items: end; gap: 32px`
- `.dense-head .h-1`: `font-size: 42px; line-height: 1.1; margin-top: 12px`
- `.dense-head .lead`: `max-width: 48ch; font-size: 15px; align-self: end`
- `.dense-table`: `display: flex; flex-direction: column; gap: 0`
- `.dt-row`: `display: grid; grid-template-columns: 180px repeat(auto-fit, 1fr); padding: 12px 16px; border-bottom: 1px solid var(--line); align-items: center; font-size: 13px`
- `.dt-header`: `font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; background: var(--bg-muted)`
- `.dt-label`: `font-weight: 600; font-size: 13px`
- Alternating background color of the table: odd-numbered rows are transparent, even-numbered rows have a gray background
- Key values ​​can be highlighted with accent colors

---

## T19 · Metric Matrix · Indicator Matrix Page

**Purpose**: Display 6-12 KPI/indicator numbers on a single page, suitable for business reports and quarterly summaries.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Top: kicker + title
- Body: 3×2 or 4×3 indicator grid

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Title (`.h-1`, consistent with global) |
| lead(optional) | description (`.lead`, right column bottom aligned) |
| metrics × 6-12 | Big number + label + trend (optional) |

**HTML skeleton**:
```html
<section class="slide s-metrics">
  <div class="dense-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="metrics-grid stagger">
    <div class="metric-cell">
      <span class="metric-value">[number]</span>
      <span class="metric-label">[label]</span>
      <span class="metric-delta positive">↑ [change]</span>
    </div>
    <!-- Repeat 6-12 times-->
  </div>
</section>
```

**Layout Details**:
- `.s-metrics`: `grid-template-rows: auto auto; align-content: center; gap: 20px` (padding inherits global)
- `.dense-head`: Same as above (grid two columns + `.h-1` + `.lead`)
- `.metrics-grid`: `grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--line)` (use gap as separator line)
- `.metrics-grid.cols-4`: `grid-template-columns: repeat(4, 1fr)`
- `.metric-cell`: `padding: 28px 24px; background: var(--bg); display: flex; flex-direction: column; gap: 6px`
- `.metric-value`: `font-size: 36px; font-weight: 200; letter-spacing: -0.02em` (light fonts and large numbers, emphasis colors are marked with `<b>`)
- `.metric-label`: `font-size: 12px; color: var(--text-muted)`
- `.metric-delta`: `font-size: 11px; font-weight: 600`
- `.metric-delta.positive`: use green or accent color
- `.metric-delta.negative`: use red or warning color

---

## T20 · Dense List · High-density list page

**Purpose**: Display 6-10 pieces of detailed information on a single page, such as function list, timeline intensive events, and multi-item comparison.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Top: kicker + title
- Body: two-column compact list

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Title (`.h-1`, consistent with global) |
| lead(optional) | description (`.lead`, right column bottom aligned) |
| items × 6-10 | Serial number/icon + title + description (1 line) |

**HTML skeleton**:
```html
<section class="slide s-dense-list">
  <div class="dense-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="dense-list-grid stagger">
    <div class="dl-item">
      <span class="dl-idx">[serial number]</span>
      <div>
        <div class="dl-title">[title]</div>
        <div class="dl-desc">[Description]</div>
      </div>
    </div>
    <!-- Repeat 6-10 times-->
  </div>
</section>
```

**Layout Details**:
- `.s-dense-list`: `grid-template-rows: auto auto; align-content: center; gap: 20px` (padding inherits global)
- `.dense-head`: Same as above (grid two columns)
- `.dense-list-grid`: `display: grid; grid-template-columns: 1fr 1fr; gap: 0 32px` (double column arrangement)
- `.dl-item`: `display: grid; grid-template-columns: 36px 1fr; gap: 12px; padding: 14px 0; border-bottom: 1px solid var(--line)`
- `.dl-idx`: `font-size: 11px; font-weight: 600; color: var(--accent); padding-top: 2px`
- `.dl-title`: `font-size: 14px; font-weight: 600`
- `.dl-desc`: `font-size: 12px; margin-top: 2px; color: var(--text-muted)`

---

## T21 · Comparison · Multidimensional comparison page

**Purpose**: Multi-dimensional feature comparison of 2-3 solutions/products, with highlighted recommendation columns.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Top: kicker + title
- Main body: comparison table (dimension name in left column + 2-3 column scheme)

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Title (`.h-1`, consistent with global) |
| lead(optional) | description (`.lead`, right column bottom aligned) |
| columns × 2-3 | Plan name + price/level (optional) |
| rows × 6-10 | Dimension name + column value (text/✓/✗/number) |

**HTML skeleton**:
```html
<section class="slide s-comparison">
  <div class="dense-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="compare-table stagger">
    <div class="cmp-row cmp-header">
      <span class="cmp-dim"></span>
      <span class="cmp-col">[Option A]</span>
      <span class="cmp-col cmp-highlight">[Option B · Recommended]</span>
      <span class="cmp-col">[Option C]</span>
    </div>
    <div class="cmp-row">
      <span class="cmp-dim">[dimension]</span>
      <span>[value]</span>
      <span class="cmp-highlight">[value]</span>
      <span>[value]</span>
    </div>
    <!-- Repeat lines 6-10 -->
  </div>
</section>
```

**Layout Details**:
- `.s-comparison`: `grid-template-rows: auto auto; align-content: center; gap: 20px` (padding inherits global)
- `.dense-head`: Same as above (grid two columns)
- `.compare-table`: `display: flex; flex-direction: column`
- `.cmp-row`: `display: grid; grid-template-columns: 160px repeat(3, 1fr); padding: 11px 16px; border-bottom: 1px solid var(--line); font-size: 13px; align-items: center`
- `.cmp-header`: `font-size: 12px; font-weight: 600; text-transform: uppercase; background: var(--bg-muted)`
- `.cmp-dim`: `font-weight: 500; color: var(--text-muted)`
- `.cmp-highlight`: `background: rgba(accent, .04); font-weight: 600` (recommended column highlight background color)
- The number of columns is adjusted through grid-template-columns: 2 columns use `160px 1fr 1fr`, 3 columns use `160px repeat(3, 1fr)`

---

## T22 · Info Dashboard · Information dashboard page

**Usage**: Mixed display of numerical indicators + mini charts + key lists on a single page, suitable for comprehensive reports/executive summaries.

**Grid structure**: `grid-template-rows: auto auto 1fr`
- Top: kicker + title (compact one line)
- Middle: 4-5 indicator cards arranged horizontally
- Bottom: left and right columns - mini chart on the left + bullet point list on the right

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Title (`.h-1`, consistent with global) |
| lead(optional) | description (`.lead`, right column bottom aligned) |
| metrics × 4-5 | Number + label (horizontal small card) |
| chart | mini SVG chart |
| highlights × 3-5 | Highlights |

**HTML skeleton**:
```html
<section class="slide s-dashboard">
  <div class="dense-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="dash-metrics stagger">
    <div class="dash-metric">
      <span class="dm-value">[number]</span>
      <span class="dm-label">[label]</span>
    </div>
    <!-- Repeat 4-5 times-->
  </div>
  <div class="dash-body stagger">
    <div class="dash-chart">
      <svg viewBox="0 0 500 160" preserveAspectRatio="xMidYMid meet">
        <!-- Mini chart -->
      </svg>
    </div>
    <div class="dash-highlights">
      <div class="dash-item">
        <span class="dash-dot"></span>
        <div>
          <div class="dash-h">[title]</div>
          <div class="dash-d">[Description]</div>
        </div>
      </div>
      <!-- Repeat 3-5 times-->
    </div>
  </div>
</section>
```

**Layout Details**:
- `.s-dashboard`: `grid-template-rows: auto auto 1fr; gap: 16px` (padding inherits global)
- `.dense-head`: Same as above (grid two columns)
- `.dash-metrics`: `display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px`
- `.dash-metric`: `padding: 16px 18px; border: 1px solid var(--line); border-radius: var(--radius-sm)`
- `.dm-value`: `font-size: 28px; font-weight: 700`
- `.dm-label`: `font-size: 11px; margin-top: 4px`
- `.dash-body`: `display: grid; grid-template-columns: 1fr 1fr; gap: 20px`
- `.dash-chart`: `border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 16px`
- `.dash-item`: `display: grid; grid-template-columns: 8px 1fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--line)`
- `.dash-dot`: `width: 8px; height: 8px; border-radius: 50%; background: var(--accent); margin-top: 4px`
- `.dash-h`: `font-size: 13px; font-weight: 600`
- `.dash-d`: `font-size: 12px; color: var(--text-muted)`
