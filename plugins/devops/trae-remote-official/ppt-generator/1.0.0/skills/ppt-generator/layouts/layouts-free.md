#Layouts · Free layout

Flexible layout without preset templates - only Chrome (top brand bar + bottom page number bar) and title area are fixed, and the middle content area is completely free for the model to play according to needs.

See `layouts-structural.md` for canvas constraints and general font size benchmarks.

**Design Principles**:
- The title area is consistent with other layouts: `.free-head` adopts grid two-column layout (left column kicker + title `.h-1`, right column description `.lead` bottom-aligned)
- padding inherits the global slide spacing (`var(--pad-y) var(--pad-x)`) and does not override it separately
- There is no preset HTML structure in the content area, and the model can freely combine elements (text paragraphs, cards, lists, SVG charts, pictures, quotation blocks, code snippets, etc.) according to needs.
- **Vertically centered, not forced to fill** - The free-format overall content container (title + content section) uses `align-content: center` to be vertically centered, and the row height uses `auto` instead of `1fr`, and the content is not forced to stretch to fill the page height.The content is arranged according to its natural height, and the white space above and below is evenly distributed.
- **No blank space inside the card** - There must be no large blank space or visual asymmetry inside the module/card; give priority to using equal distribution layout (`flex: 1` equal height columns, grid equal width partitions) to allow the sub-elements to fill the container evenly, to avoid content accumulation on one side and empty space on the other side
- **Multiple column heights must be aligned** - In the multi-column layout of T24/T25, the visual height difference of each column must not exceed 15% of the total height.Use `align-items: stretch` to make the grid items the same height, and use `flex: 1` to fill the main container in the column.If the content content is naturally unequal, it must be balanced by adjusting padding, font size, supplementary information, etc. It is prohibited to have a visual imbalance where one column is full and the other column only takes up half the height.
- **Enlarge and emphasize core information** - Key values, titles, and status words in the module should use a font size that is significantly larger than the main text (recommended ≥ 24px), and use font weight/color distinction to form a visual hierarchy
- **The style layer must use global variables** - the background color, border, and rounded corners of the card/module container must reference the CSS variables defined in the styles file, and hard-coded values ​​are prohibited.Specific requirements:
  - Rounded corners: Use `var(--radius)` or rounded corner variables defined in styles. It is forbidden to hard-code literals such as `8px` and `12px`
  - Border: Use the border color variable defined in styles or the border writing method consistent with the predefined layout (such as `1px solid rgba(...)` needs to maintain the same color value as the global card border). It is prohibited to invent the border color yourself.
  - Background color: Use the card background variable defined in styles or a background value consistent with the predefined layout (such as T04 `.line-cell`). It is prohibited to use different transparencies or tones at will.
  - Purpose: To ensure that the free layout page and the predefined layout page are completely unified at the visual level, and there will be no style jump when switching pages.

**Differences from template layout**:
- Template layout (T01-T22): HTML skeleton is fixed, content is filled into preset slots
- Free layout (T23-T25): only fixed shell (Chrome + title), the content area is original typesetting by the model

**Time to use**:
- When the requirements do not fit any existing template (T01-T22)
- Special content forms (mixed graphic tables, flow charts, timelines, customized information architecture, etc.)
- Users explicitly request free layout or creative expression

---

## T23 · Free Single · Free single column page

**Usage**: Single-column free typesetting, suitable for vertical information flow such as narrative paragraphs, flow charts, large paragraphs of text + interspersed charts, timelines, etc.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Title area (auto)
- Main body: single-column free content area (auto, arranged according to its own height)
- Overall vertically centered

**HTML skeleton**:
```html
<section class="slide s-free-single">
  <div class="free-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="free-body stagger">
    <!-- Free content: Models can be combined according to needs -->
  </div>
</section>
```

**Layout Details**:
- `.s-free-single`: `grid-template-rows: auto auto; gap: 24px; height: 100%; align-content: center` (padding inherits global)
- `.free-head`: `display: grid; grid-template-columns: auto 1fr; align-items: end; gap: 32px`
- `.free-head .h-1`: `font-size: 42px; line-height: 1.1; margin-top: 12px`
- `.free-head .lead`: `max-width: 48ch; font-size: 15px; align-self: end`
- `.free-body`: `display: flex; flex-direction: column; gap: 16px; overflow: hidden`

**Content area guidance**:
- Can contain any number of paragraphs, lists, cards, SVG, quote blocks, images, etc.
- **Allow the use of images as auxiliary illustrations** - Follow the SKILL.md image specification (Tier 1 user material > Tier 2 search/generate > Tier 3 Unsplash; semantic alt; adapt to slot size).Pictures can be used for: mixed arrangement of pictures and text (left picture and right text or top picture and bottom picture), pictures in cards, background decoration, case screenshots, etc.It is recommended to use `border-radius: var(--radius)` to keep the style consistent with the card, and the size can be cut and adapted through `object-fit: cover`
- Element spacing is recommended to be 12-20px
- Recommended text size is 13-15px (main text), 18-24px (subtitle)
- Content is arranged according to its natural height and centered on the page as a whole

---

## T24 · Free Dual · Free two-column page

**Purpose**: Two-column free layout, suitable for horizontal juxtaposition structures such as left-right comparison, side-by-side graphics and text, and separation of primary and secondary information.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Title area (auto)
- Main body: two-column free content area (auto, arranged according to its own height)
- Overall vertically centered

**HTML skeleton**:
```html
<section class="slide s-free-dual">
  <div class="free-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="free-body free-cols-2 stagger">
    <div class="free-col">
      <!-- Left column: Free content -->
    </div>
    <div class="free-col">
      <!-- Right column: free content -->
    </div>
  </div>
</section>
```

**Layout Details**:
- `.s-free-dual`: `grid-template-rows: auto auto; gap: 24px; height: 100%; align-content: center` (padding inherits global)
- `.free-head`: Same as T23
- `.free-body.free-cols-2`: `display: grid; grid-template-columns: 1fr 1fr; gap: 32px; overflow: hidden`
- `.free-col`: `display: flex; flex-direction: column; gap: 14px; min-height: 0`

**Content area guidance**:
- The two columns can be of unequal width (adjust the center of gravity by modifying `grid-template-columns` to `2fr 1fr` or `1fr 2fr`)
- The content of the left and right columns can be in completely different forms (such as left text and right picture, left list and right chart)
- Freely combine elements within each column

**⚠️ Height alignment between columns (mandatory rule)**:
- **Significant height asymmetry between the left and right columns is prohibited** - the visual height difference between the two columns shall not exceed 15% of the total height
- Implementation method: add `align-items: stretch` to `.free-col`, and use `flex: 1` for the internal main container (card/block) to fill evenly
- If the content of the two columns is naturally unequal, balance it through the following strategies:
  1. Columns with less content: increase padding, add auxiliary information, and use larger font sizes
  2. Columns with more content: simplify text and increase information density
  3. Use equal-height card wrapping: wrap both columns with `.card` containers, and set `height: 100%` or `flex: 1`
- CSS implementation: `.free-cols-2 { align-items: stretch; }` + `.free-col > .card { flex: 1; }`

---

## T25 · Free Triple · Free three-column page

**Purpose**: Three-column free layout, suitable for tripartite comparison, multi-module juxtaposition, information dashboard, feature matrix, etc.

**Grid structure**: `grid-template-rows: auto auto; align-content: center`
- Title area (auto)
- Main body: three-column free content area (auto, arranged according to its own height)
- Overall vertically centered

**HTML skeleton**:
```html
<section class="slide s-free-triple">
  <div class="free-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="free-body free-cols-3 stagger">
    <div class="free-col">
      <!-- Column 1: Free content -->
    </div>
    <div class="free-col">
      <!-- Column 2: Free content -->
    </div>
    <div class="free-col">
      <!-- Column 3: Free content -->
    </div>
  </div>
</section>
```

**Layout Details**:
- `.s-free-triple`: `grid-template-rows: auto auto; gap: 24px; height: 100%; align-content: center` (padding inherits global)
- `.free-head`: Same as T23
- `.free-body.free-cols-3`: `display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; overflow: hidden`
- `.free-col`: `display: flex; flex-direction: column; gap: 12px; min-height: 0`

**Content area guidance**:
- Three columns are suitable for scenes with a large amount of information. The text in a single column is recommended to be 12-13px.
- The proportion can be adjusted through `grid-template-columns` (such as `1fr 2fr 1fr` to highlight the middle column)
- Each column has an independent internal structure
- Small cards, mini charts, indicator numbers, etc. can be nested in the column

**⚠️ Height alignment between columns (mandatory rule)**:
- **Significant height asymmetry in each column is prohibited** - the visual height difference between any two columns shall not exceed 15% of the total height
- Implementation: `.free-cols-3 { align-items: stretch; }` + `.free-col > .card { flex: 1; }`
- Each column is wrapped in a card container with a uniform height. The internal content is allowed to be naturally arranged but the height of the container must be consistent.
- If there is obviously too little content in a column, fill the visual space by increasing padding, supplementing explanatory text, or using a larger font size.

---

## Common CSS reference

The following is the general style definition of free layout. `<style>` is written as needed when generating:

```css
/* Free Pages — Free layout*/
.free-head { display: grid; grid-template-columns: auto 1fr; align-items: end; gap: 32px; }
.free-head .h-1 { font-size: 42px; line-height: 1.1; margin-top: 12px; }
.free-head .lead { max-width: 48ch; font-size: 15px; align-self: end; }

.s-free-single,
.s-free-dual,
.s-free-triple { grid-template-rows: auto auto; gap: 24px; height: 100%; align-content: center; }

.free-body { overflow: hidden; }
.free-body.free-cols-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; align-items: stretch; }
.free-body.free-cols-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 24px; align-items: stretch; }
.free-col { display: flex; flex-direction: column; gap: 14px; min-height: 0; }
.free-col > .card { flex: 1; }
```
