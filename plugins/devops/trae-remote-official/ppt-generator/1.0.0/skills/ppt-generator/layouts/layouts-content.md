# Layouts · Content Page

Text-driven layout - carries information-intensive content such as core discussions, data, lists, comparisons, etc.

See `layouts-structural.md` for canvas constraints and general font size benchmarks.

---

## T03 · Brand · Brand positioning page

**Use**: product positioning + milestone card, left text and right card.

**Grid structure**: `grid-template-columns: 1fr 1fr`
- Left column: kicker + title + lead + three columns of statistics column
- Right column: Vertically stacked event cards (2-4 cards)

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| stats × 3 | big number + label |
| cards × 2-4 | number + tag + title + description + badge |

**HTML skeleton**:
```html
<section class="slide s-brand">
  <div class="brand-left stagger">
    <span class="kicker">[Number] / [Section]</span>
    <h1 class="h-1">[Title]</h1>
    <p class="lead">[Description]
    <div class="brand-stats">
      <div><div class="k"><b>[number]</b></div><div class="lbl">[label]</div></div>
      <!-- 3 items-->
    </div>
  </div>
  <div class="brand-cards stagger">
    <div class="brand-card">
      <div>[number]</div>
      <div><div class="tag">[tag]</div><div class="title">[title]</div><div class="desc">[description]</div></div>
      <div class="badge">[logo]</div>
    </div>
    <!-- Repeat -->
  </div>
</section>
```

**Layout Details**:
- `.s-brand`: `grid-template-columns: 1fr 1fr; gap: 69px; align-items: center`
- `.brand-left h1`: `margin-top: 20px`
- `.brand-left .lead`: `margin-top: 22px`
- `.brand-stats`: `margin-top: 40px; grid-template-columns: repeat(3, 1fr); gap: 24px; padding-top: 24px`
- `.brand-stats .k`: `font-size: 46px; font-weight: 200`
- `.brand-stats .lbl`: `font-size: 12px; margin-top: 8px`
- `.brand-card`: `padding: 20px 24px; grid-template-columns: 46px 1fr auto; gap: 22px`
- `.brand-card .tag`: `font-size: 11px`
- `.brand-card .title`: `font-size: 19px; font-weight: 600; margin-top: 4px`
- `.brand-card .desc`: `font-size: 13px; margin-top: 6px; line-height: 1.5`
- `.brand-card .badge`: `font-size: 11px; padding: 6px 12px`
- `.brand-cards` gap: `14px`; **hard cap**: `max-height: 582px; overflow: hidden; align-content: center`

**Overflow guard (must not enter the bottom chrome)**:
- The right column is centered (`align-items: center`) in the 582px content area (720 − 2×69px pad); a centered column overflows **symmetrically**, so stacked cards taller than 582px push their lower half into the bottom page-number chrome.
- Two layers of defense: (1) the tuned card padding/type above keep **4 cards with ≤2-line descriptions** (~128px/card ×4 + 14px gap ×3 ≈ 554px) under 582px; (2) `.brand-cards` carries `max-height: 582px; overflow: hidden` as a **hard cap** so a 5th card or over-long copy is clipped rather than spilling. Keep **≤4 cards** and **desc ≤2 lines**.
- **Do not** rescue an overflowing T03 by patching a single generated slide — shorten copy or drop a card and rely on the tuned defaults plus the hard cap.

---

## T04 · Grid Lines · Multi-column grid page

**Purpose**: Display 3-6 modules/products side by side, emphasizing equal relationships.

**Layout structure**: `display: flex; flex-direction: column; justify-content: center; gap: 32px`
- Top: title area (left title + right lead)
- Main body: 3-5 columns of equal width grid (separated by 1px gap), arranged according to the natural height of the content

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cells × 3-6 | Number + name + English + picture (optional) + description + bottom label |

**HTML skeleton**:
```html
<section class="slide s-lines">
  <div class="lines-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="lines-grid stagger">
    <div class="line-cell">
      <span class="num">01</span>
      <div class="name">[name]</div>
      <div class="en">[English]</div>
      <img class="cell-img" src="[image path]" alt="[description]"> <!-- Optional-->
      <div class="desc">[Description]</div>
      <div class="accent">[label]</div>
    </div>
    <!-- Repeat 3-6 blocks-->
  </div>
</section>
```

**Layout Details**:
- `.s-lines`: `display: flex !important; flex-direction: column; justify-content: center; gap: 32px` (overrides the default grid of slide, and the content is centered according to the natural height)
- `.lines-head`: `display: grid; grid-template-columns: 1fr auto; align-items: end; gap: 32px`
- `.lines-head .h-1`: `font-size: 40px`
- `.lines-head .lead`: `font-size: 14px`
- `.lines-grid`: `display: grid; grid-template-columns: repeat(N, 1fr); gap: 1px; overflow: hidden; flex-shrink: 0` (N is the number of columns, default is 4, can be set to 3-6)
- `.line-cell`: `padding: 24px 20px 20px; display: flex; flex-direction: column; gap: 8px` (no min-height, natural height)
- `.line-cell .num`: `font-size: 28px; font-weight: 200` (absolute positioning top:18px right:18px)
- `.line-cell .name`: `font-size: 18px; font-weight: 600`
- `.line-cell .en`: `font-size: 10px`
- `.line-cell .cell-img`: `width: 100%; aspect-ratio: 4/3; object-fit: cover; border-radius: 6px; margin-top: 8px` (optional, used when inserting pictures)
- `.line-cell .desc`: `font-size: 12px; margin-top: 12px; line-height: 1.5`
- `.line-cell .accent`: `font-size: 10px`
- `.lines-grid` defaults to 4 columns, which can be changed to 3, 5 or 6 columns through inline style

**Design Points**:
- The overall layout uses flexbox instead of grid to prevent cards from filling the screen vertically.
- Cards have no min-height, are arranged according to the natural height of the content and centered vertically as a whole
- The picture is an optional slot, placed after `.en` and before `.desc`, automatically cropped in 4:3

---

## T05 · Team Cards · Four card pages

**Purpose**: Demonstrate 4 juxtaposed concepts/abilities/roles.

**Grid structure**: `grid-template-columns: 40% 1fr`
- Left column: kicker + title + lead
- Right column: 2×2 card grid

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cards × 4 | Serial number + title + English subtitle + description |

**HTML skeleton**:
```html
<section class="slide s-team">
  <div class="stagger">
    <span class="kicker">[Number] / [Section]</span>
    <h1 class="h-1">[Title]</h1>
    <p class="lead">[Description]
  </div>
  <div class="team-cards stagger">
    <div class="team-card">
      <span class="idx">— 01</span>
      <div class="title">[title]</div>
      <div class="en-sub">[English]</div>
      <div class="desc">[Description]</div>
    </div>
    <!-- Repeat 4 pictures-->
  </div>
</section>
```

**Layout Details**:
- `.s-team`: `grid-template-columns: 40% 1fr; gap: 77px; align-items: center`
- `.team-cards`: `grid-template-columns: 1fr 1fr; gap: 20px; max-height: 582px; overflow: hidden; align-content: center`
- `.team-card`: `padding: 24px; min-height: 168px; flex-direction: column; gap: 12px`
- `.team-card .idx`: `font-size: 12px`
- `.team-card .title`: `font-size: 19px; font-weight: 600`
- `.team-card .desc`: `font-size: 13px; line-height: 1.55; margin-top: auto`
- `.team-card .en-sub`: `font-size: 11px; margin-top: 4px`

**Overflow guard (must not enter the bottom chrome)**:
- The right column is centered (`align-items: center`) in the 582px content area (720 − 2×69px pad); a centered column overflows **symmetrically**, so a 2×2 card block taller than 582px pushes its lower half into the bottom page-number chrome.
- `min-height` is a **floor** (keeps short cards even height); `max-height: 582px; overflow: hidden` on `.team-cards` is the hard **cap**. The tuned padding/type keep **4 cards with ≤3-line descriptions** (~228px/card ×2 rows + 20px gap ≈ 476px) under 582px. Keep `cards × 4` and **desc ≤3 lines**.
- **Do not** rescue an overflowing T05 by patching a single generated slide — shorten copy and rely on the tuned defaults.

---

## T06 · Refine List · List details page

**Purpose**: Display detailed information of 3-6 items.

**Grid structure**: `grid-template-columns: 34% 1fr`
- Left column: kicker + title + lead
- Right column: vertical entry list (border separated)

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| items × 3-6 | number label + title + description |

**HTML skeleton**:
```html
<section class="slide s-refine">
  <div class="stagger">
    <span class="kicker">[Number] / [Section]</span>
    <h1 class="h-1">[Title]</h1>
    <p class="lead">[Description]
  </div>
  <div class="refine-list stagger">
    <div class="refine-item">
      <span class="idx"><b>01</b> · [tag]</span>
      <div><div class="h">[Title]</div><div class="d">[Description]</div></div>
    </div>
    <!-- Repeat -->
  </div>
</section>
```

**Layout Details**:
- `.s-refine`: `grid-template-columns: 34% 1fr; gap: 72px; align-items: center`
- `.refine-list`: `align-content: center; max-height: 582px; overflow: hidden` — the list is vertically centered inside the 582px content area (720 − 2×69px pad); `max-height` + `overflow: hidden` is the **hard cap** so it can never spill past it into the bottom chrome.
- `.refine-item`: `grid-template-columns: 90px 1fr; gap: 32px; padding: 18px 0; align-items: start`
- `.refine-item .idx`: `font-size: 13px; padding-top: 5px`
- `.refine-item .h`: `font-size: 22px; font-weight: 600`
- `.refine-item .d`: `font-size: 13.5px; line-height: 1.55; margin-top: 6px; max-width: 68ch`

**Overflow guard (must not enter the bottom chrome)**:
- The right list plus its own centering must stay within the 582px content area. The default spacing above is tuned so **5 items with 1–2 line descriptions** fit without touching the bottom page-number chrome.
- Cap at **6 items**. For a genuine 6-item list, add `refine-dense` on `.refine-list` (tighter padding/type) rather than editing per-item values.
- **Do not** fix an overflowing T06 by bolting an ad-hoc compact class onto one generated slide — that only patches a single deck and the next deck overflows again. Keep item count ≤6, descriptions ≤2 lines, and rely on the tuned defaults / `refine-dense`.

---

## T07 · Think · Manifesto Page

**Use**: Chapter transition, golden sentence display, vision statement.

**Grid structure**: `grid-template-columns: 1fr; align-items: center` (single column centered)
- max-width: 1100px
- Content: kicker → main sentence with giant characters → auxiliary paragraphs → optional note block

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | English label |
| statement | Main sentence with huge characters (1-3 lines max, including emphasis words) |
| sub | auxiliary description paragraph (≤2-3 lines) |
| note (optional) | tag + one sentence summary (≤2 notes) |

**HTML skeleton**:
```html
<section class="slide s-think">
  <div class="think-wrap stagger">
    <div class="think-kicker">[label]</div>
    <div class="think-q">[Main Sentence]<br><em>[Emphasis Word]</em><br>[Final Sentence]</div>
    <p class="think-sub">[auxiliary description]
    <div class="think-note"><b>[Label]</b><span>[Summary]</span></div>
  </div>
</section>
```

**Layout Details**:
- `.s-think`: `grid-template-columns: 1fr; align-items: center`
- `.think-wrap`: `max-width: 1100px; max-height: 582px; overflow: hidden` — the `max-height` + `overflow: hidden` is the **hard cap** so an over-long statement is clipped instead of spilling into the bottom chrome
- `.think-kicker`: `font-size: 13px`
- `.think-q`: `margin-top: 22px; font-size: 76px; font-weight: 200; line-height: 1.04`
- `.think-sub`: `margin-top: 26px; font-size: 15px; line-height: 1.65; max-width: 72ch`
- `.think-note`: `margin-top: 20px; padding: 16px 20px; font-size: 15px`; use `display:flex; width:fit-content` (block-level) so multiple notes stack reliably — do not use `inline-flex`.

**Overflow guard (must not enter the bottom chrome)**:
- `.s-think` centers content in the 582px content area (720 − 2×69px pad); a centered grid overflows **symmetrically**, so any excess pushes the lower half straight into the `bottom` page-number chrome.
- Two layers of defense: (1) the tuned defaults above keep the worst realistic case — **3-line question + 2–3 line sub + two notes** — under 582px; (2) `.think-wrap` carries `max-height: 582px; overflow: hidden` as a **hard cap** so even over-long copy is clipped rather than spilling. Keep the statement to **≤3 lines** and **≤2 notes**; shorten copy or drop the note rather than shrinking one slide by hand.
- **Do not** fix an overflowing T07 by patching a single generated slide (ad-hoc font/margin overrides) — that only saves one deck. Rely on the tuned defaults, the content caps above, and the hard cap.

---

## T17 · Chart · Chart page

**Use**: Data visualization - use SVG inline charts to display quantitative information such as trends, distributions, comparisons, etc.

**Grid structure**: `grid-template-rows: auto 1fr; gap: 18px`
- Top: title area (`.chart-head`, left title + right lead)
- Body: chart grid (`.chart-grid`, rounded border container, 1px divider)

**Chart Grid Variants**:

| variant class | number of columns | purpose |
|---|---|---|
| (Default) | `1fr 1fr` | 2 images side by side |
| `.cols-1` | `1fr` | Single image full width |
| `.cols-2x2` | `1fr 1fr` × 2 rows | 4 images (2×2) |
| `.cols-3` | `repeat(3, 1fr)` | 3 pictures side by side|
| `.cols-3x2` | `repeat(3, 1fr)` × 2 lines | 6 images (3×2) |

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | Chapter identifier (e.g. "04.3 / Analytics") |
| title | Single-line title (such as "Growing trends.") |
| lead | description copy |
| chart-panel × N | Each panel: English label + Chinese subtitle + SVG chart area |

**HTML skeleton**:
```html
<section class="slide s-chart">
  <div class="chart-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Single line title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="chart-grid [cols-1|cols-2x2|cols-3|cols-3x2] stagger">
    <div class="chart-panel">
      <div class="chart-cap">
        <span class="chart-title">[English label]</span>
        <span class="chart-subtitle">[Chinese subtitle · Unit]</span>
      </div>
      <div class="chart-area">
        <svg viewBox="0 0 [W] [H]" preserveAspectRatio="xMidYMid meet">
          <!-- SVG chart content-->
        </svg>
      </div>
    </div>
    <!-- Repeat N chart-panels -->
  </div>
</section>
```

**Layout Details**:
- `.s-chart`: `grid-template-rows: auto 1fr; gap: 18px; padding-top: 80px; padding-bottom: 84px`
- `.chart-head`: `grid-template-columns: auto 1fr; align-items: end; gap: 32px`
- `.chart-head .h-1`: `font-size: 36px; margin-top: 12px`
- `.chart-head .lead`: `font-size: 14px`
- `.chart-grid`: `grid-template-columns: 1fr 1fr; gap: 1px; overflow: hidden`
- `.chart-grid.cols-1`: `grid-template-columns: 1fr`
- `.chart-grid.cols-2x2`: `grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr`
- `.chart-grid.cols-3`: `grid-template-columns: repeat(3, 1fr)`
- `.chart-grid.cols-3x2`: `grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr 1fr`
- `.chart-panel`: `padding: 20px 22px; flex-direction: column; gap: 10px`
- `.chart-cap`: `display: flex; align-items: center; gap: 14px`
- `.chart-title`: `font-size: 11px`
- `.chart-subtitle`: `font-size: 15px; font-weight: 500`
- Common types of SVG charts: line/area chart, horizontal bar chart, donut chart, vertical bar chart
- Recommended SVG viewBox: single image `800×200`, double image `400×220`, four image `300×140`, six image `200×100`
