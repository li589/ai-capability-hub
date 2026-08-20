#Layouts · Image Page

Visually driven layout - with images as the main body and a small amount of text description.Suitable for displaying screenshots, product interfaces, design cases, photography, etc.

See `layouts-structural.md` for canvas constraints and general font size benchmarks.

## Content area height constraint

All image page layouts must ensure that the image container does not invade the Chrome safe zone:

- **Effective content area height**: `608px` (canvas 720px − padding-top 56px − padding-bottom 56px)
- For layouts that use universal padding (56px 72px) (such as T10 Feature Split), the image container must set `max-height: 608px`
- For layouts using custom padding-top/padding-bottom (such as T09/T11, etc. using 80px/84px), the effective height = `720px − padding-top − padding-bottom`, the image area is automatically constrained by `1fr`, and usually does not overflow
- The picture element itself should also set `max-height` consistent with the container, and cooperate with `object-fit: cover` to prevent deformation

### ⚠️ Grid/Flex subitem overflow prevention (mandatory)

When the image container is in a flexible allocation row of `grid-template-rows: 1fr` or `flex:1`, the following conditions must be met to prevent the image from bursting the grid according to its natural size:

1. **Grid container** (such as `.gallery-grid` / `.duo-grid` / `.penta-grid` / `.hexa-grid` / `.mosaic-grid`): `min-height: 0; overflow: hidden`
2. **Card container** (such as `.gallery-card` / `.duo-card` / `.trio-main` / `.penta-card` / `.hexa-card` / `.mosaic-card`): `min-height: 0; overflow: hidden`
3. **Image container** (such as `.gallery-img` / `.duo-img` / `.trio-img`): `flex: 1; min-height: 0; overflow: hidden`
4. **img element**: `width: 100%; height: 100%; object-fit: cover` (**It is prohibited to set only `width:100%` without `height:100%`**)

**Reason**: CSS Grid/Flex sub-items default to `min-height: auto`, which does not allow compression to be smaller than the content size.The natural height calculated by `width:100%` for the image will burst the container.`min-height:0` allows the container to shrink, and `height:100%` causes the image to fill the available space rather than expand to its natural size.

---

## T09 · Gallery Grid · Four-picture grid page

**Purpose**: Display 4 pictures, visual priority.

**Grid structure**: `grid-template-rows: auto 1fr`
- Top: title area (left title + right lead)
- Body: 2×2 image grid

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cards × 4 | image + tag + title |

**HTML skeleton**:
```html
<section class="slide s-gallery">
  <div class="gallery-head stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
    </div>
    <p class="lead">[Description]
  </div>
  <div class="gallery-grid stagger">
    <div class="gallery-card">
      <div class="gallery-img"><img src="[URL]" alt="[Description]"></div>
      <div class="gallery-cap"><span class="label">[label]</span><span class="title">[title]</span></div>
    </div>
    <!-- Repeat 4 pictures-->
  </div>
</section>
```

**Layout Details**:
- `.s-gallery`: `padding-top: 80px; padding-bottom: 84px; gap: 16px`
- `.gallery-head`: `grid-template-columns: auto 1fr; align-items: end; gap: 32px`
- `.gallery-head .h-1`: `font-size: 40px; margin-top: 12px`
- `.gallery-head .lead`: `font-size: 14px`
- `.gallery-grid`: `grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 12px; min-height: 0; overflow: hidden`
- `.gallery-card`: `min-height: 0; overflow: hidden` (**required** to prevent flex/grid items from exploding the grid according to the natural height of the image)
- `.gallery-img`: `flex: 1; min-height: 0; overflow: hidden` (**must** set `min-height:0`, otherwise `flex:1` will not be compressed smaller than the content size)
- `.gallery-img img`: `width: 100%; height: 100%; object-fit: cover` (in line with container constraints, it is prohibited to set `width:100%` without `height:100%`)
- `.gallery-cap`: `display: flex; align-items: center; gap: 14px`
- `.gallery-cap .label`: `font-size: 11px`
- `.gallery-cap .title`: `font-size: 15px; font-weight: 500`

---

## T10 · Feature Split · Picture and text column page

**Usage**: Large picture + text description to highlight a single function/product.

**Grid structure**: `grid-template-columns: 55% 1fr` (default left picture and right text)
- Variant `.reverse`: `1fr 55%` (right picture, left text)

**Content Slots**:
| Slot | Description |
|---|---|
| image | Large image (4:3 or adaptive) |
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| points × 2-3 | Serial number + title + description |

**HTML skeleton**:
```html
<section class="slide s-feature">
  <div class="feature-img stagger"><img src="[URL]" alt="[Description]"></div>
  <div class="feature-text stagger">
    <span class="kicker">[Number] / [Section]</span>
    <h1 class="h-1">[Title]</h1>
    <p class="lead">[Description]
    <div class="feature-points">
      <div class="feature-point"><span class="idx">01</span><div><div class="h">[Title]</div><div class="d">[Description]</div></div></div>
      <!-- Repeat -->
    </div>
  </div>
</section>
```

**Layout Details**:
- `.s-feature`: `grid-template-columns: 55% 1fr; gap: 64px; align-items: center`
- Variant `.reverse`: `grid-template-columns: 1fr 55%`
- `.feature-img`: `border-radius: 12px; overflow: hidden; max-height: 608px` (not exceeding the height of the effective content area)
- `.feature-img img`: `width: 100%; height: 100%; max-height: 608px; object-fit: cover`
- `.feature-text .h-1`: `font-size: 42px; line-height: 1.1` (T10 overrides the generic 72px `.h-1` down to 42px so the two-column feature title fits alongside the lead + points)
- `.feature-text .lead`: `margin-top: 18px`
- `.feature-text`: `max-height: 582px; overflow: hidden; align-self: center` — **hard cap** so an over-long text column is clipped instead of spilling into the bottom chrome
- `.feature-points`: `margin-top: 28px`
- `.feature-point`: `grid-template-columns: 60px 1fr; gap: 20px; padding: 14px 0`
- `.feature-point .idx`: `font-size: 13px; padding-top: 4px`
- `.feature-point .h`: `font-size: 18px; font-weight: 600`
- `.feature-point .d`: `font-size: 13.5px; margin-top: 5px; line-height: 1.55`

**Overflow guard (must not enter the bottom chrome)**:
- The text column is centered (`align-items: center`) in the 582px content area (720 − 2×69px pad); a centered column overflows **symmetrically**, so a text block taller than 582px pushes its lower half into the bottom page-number chrome.
- Two layers of defense: (1) the tuned type/padding above (42px title, not the generic 72px) keep the worst realistic case — **2-line title + 2-line lead + 3 points with 2-line descriptions** (~475px) — under 582px; (2) `.feature-text` carries `max-height: 582px; overflow: hidden` as a **hard cap** so even over-long copy is clipped rather than spilling. Keep **≤3 points** and **desc ≤2 lines**.
- **Do not** rescue an overflowing T10 by patching a single generated slide — shorten copy or drop a point and rely on the tuned defaults plus the hard cap.

---

## T11 · Duo Images · Double pictures side by side page

**Use**: Compare 2 images side by side or display them side by side.

**Grid structure**: `grid-template-rows: auto 1fr`
- Top: Title area (reuse `.gallery-head`)
- Body: 2 columns of images of equal width

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cards × 2 | image + tag + title + description |

**HTML skeleton**:
```html
<section class="slide s-duo">
  <div class="gallery-head stagger">
    <div><span class="kicker">[Number] / [Section]</span><h1 class="h-1">[Title]</h1></div>
    <p class="lead">[Description]
  </div>
  <div class="duo-grid stagger">
    <div class="duo-card">
      <div class="duo-img"><img src="[URL]" alt="[Description]"></div>
      <div class="duo-cap"><span class="label">[label]</span><div class="title">[title]</div><div class="desc">[description]</div></div>
    </div>
    <!-- Repeat 2 pictures-->
  </div>
</section>
```

**Layout Details**:
- `.s-duo`: `padding-top: 80px; padding-bottom: 84px; gap: 20px; grid-template-rows: auto 1fr`
- The title area reuses the `.gallery-head` parameter (same as T09)
- `.duo-grid`: `grid-template-columns: 1fr 1fr; gap: 20px; min-height: 0; overflow: hidden` (**required**)
- `.duo-card`: `display: flex; flex-direction: column; gap: 12px; min-height: 0; overflow: hidden` (**required**)
- `.duo-img`: `border-radius: 12px; overflow: hidden; flex: 1; min-height: 0` (**must** set `min-height:0`)
- `.duo-img img`: `width: 100%; height: 100%; object-fit: cover` (**disabled** only set `width:100%`)
- `.duo-cap .label`: `font-size: 11px`
- `.duo-cap .title`: `font-size: 18px; font-weight: 600; margin-top: 6px`
- `.duo-cap .desc`: `font-size: 14px; margin-top: 6px; max-width: 52ch`

---

## T12 · Trio Images · Three picture layout page

**Usage**: 1 big picture + 2 small pictures, with clear priority.

**Grid structure**: `grid-template-rows: auto 1fr`
- Top: title area
- Main body: 2-column grid, the left column is full of tall images, and the right column is filled with 2 small images of equal height.

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| main | Large image + tag title |
| side × 2 | thumbnail + tag title |

**HTML skeleton**:
```html
<section class="slide s-trio">
  <div class="gallery-head stagger">
    <div><span class="kicker">[Number] / [Section]</span><h1 class="h-1">[Title]</h1></div>
    <p class="lead">[Description]
  </div>
  <div class="trio-grid stagger">
    <div class="trio-main">
      <div class="trio-img"><img src="[Large Image]" alt="[Semantic Description]"></div>
      <div class="trio-cap"><span class="label">[label]</span><span class="title">[title]</span></div>
    </div>
    <div class="trio-side">
      <div class="trio-card"><div class="trio-img"><img src="[small picture]" alt="[semantic description]"></div><div class="trio-cap"><span class="label">[label]</span><span class="title">[title]</span></div></div>
      <div class="trio-card"><div class="trio-img"><img src="[small picture]" alt="[semantic description]"></div><div class="trio-cap"><span class="label">[label]</span><span class="title">[title]</span></div></div>
    </div>
  </div>
</section>
```

**Layout Details**:
- `.s-trio`: `padding-top: 80px; padding-bottom: 84px; gap: 16px`
- The title area reuses the `.gallery-head` parameter (same as T09)
- `.trio-grid`: `grid-template-columns: 1fr 1fr; gap: 16px; min-height: 0; overflow: hidden` (**required**)
- `.trio-side`: `display: grid; grid-template-rows: 1fr 1fr; gap: 16px; min-height: 0`
- `.trio-main, .trio-card`: `min-height: 0; overflow: hidden` (**required**, same as T09 gallery-card reason)
- `.trio-img`: `flex: 1; min-height: 0; overflow: hidden`
- `.trio-img img`: `width: 100%; height: 100%; object-fit: cover`
- `.trio-cap`: `display: flex; align-items: center; gap: 12px`
- `.trio-cap .label`: `font-size: 11px`
- `.trio-cap .title`: `font-size: 14px; font-weight: 500`

---

## T13 · Hero Image · Large picture leading page

**Purpose**: Use a large picture as the main body and match it with the text area at the bottom to create a visual impact.

**Grid structure**: `grid-template-rows: 1fr auto`
- Upper part (1fr): large image container (rounded corners + overflow hidden)
- Lower part (auto): text area - left side (kicker + title + lead) + right side (meta tag)

**Content Slots**:
| Slot | Description |
|---|---|
| image | Large image (1600×900 recommended) |
| kicker | chapter identifier |
| title | Title (single or two lines) |
| lead | description |
| meta × 2-3 | tag + value + tagline |

**HTML skeleton**:
```html
<section class="slide s-hero">
  <div class="hero-img"><img src="[Large Image URL]" alt="[Description]"></div>
  <div class="hero-bottom stagger">
    <div>
      <span class="kicker">[Number] / [Section]</span>
      <h1 class="h-1">[Title]</h1>
      <p class="lead">[Description]
    </div>
    <div class="hero-meta">
      <span>[label]<strong>[value]</strong></span>
      <span>[label]<strong>[value]</strong></span>
      <span class="tagline">[Tagline]</span>
    </div>
  </div>
</section>
```

**Layout Details**:
- `.s-hero`: `grid-template-rows: 1fr auto; gap: 0; padding: 56px 72px 56px` (**Bottom must be ≥ 56px**, aligned with global content safe area rules, prohibited from setting to 0)
- `.hero-img`: `overflow: hidden; max-height: 456px` (Tighten the height of the large image to make space for the bottom text area and prevent the image from squeezing the text into the page number area)
- `.hero-img img`: `width: 100%; height: 100%; object-fit: cover`
- `.hero-bottom`: `grid-template-columns: 1fr auto; align-items: end; gap: 32px; padding: 22px 4px 0` (the bottom padding is guaranteed by the 56px of the slide, no additional padding-bottom is needed here)
- `.hero-bottom .kicker`: `margin-bottom: 6px`
- `.hero-bottom .h-1`: `font-size: 40px`
- `.hero-bottom .lead`: `margin-top: 8px; font-size: 14px`
- `.hero-meta span`: `font-size: 11px`
- `.hero-meta strong`: `font-weight: 500; margin-left: 8px`

---

## T14 · Penta · Five-picture layout page

**Purpose**: Display 5 pictures, 1 large picture spanning two lines + 4 small pictures (2×2), suitable for multi-interface display of products.

**Grid structure**: `grid-template-rows: auto 1fr`
- Top: Title area (reuse `.gallery-head`)
- Main body: 3 columns × 2 rows grid, the first image spans row 1-2

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cards × 5 | picture + title + subtitle |

**HTML skeleton**:
```html
<section class="slide s-penta">
  <div class="gallery-head stagger">
    <div><span class="kicker">[Number] / [Section]</span><h1 class="h-1">[Title]</h1></div>
    <p class="lead">[Description]
  </div>
  <div class="penta-grid stagger">
    <div class="penta-card">
      <img src="[Large Image URL]" alt="[Description]">
      <div class="cap"><div class="title">[title]</div><div class="sub">[subtitle]</div></div>
    </div>
    <div class="penta-card">
      <img src="[URL]" alt="[Description]">
      <div class="cap"><div class="title">[title]</div><div class="sub">[subtitle]</div></div>
    </div>
    <!--Repeat 5 pictures in total-->
  </div>
</section>
```

**Layout Details**:
- `.s-penta`: `padding-top: 80px; padding-bottom: 84px; gap: 16px`
- The title area reuses the `.gallery-head` parameter (same as T09)
- `.penta-grid`: `grid-template-columns: 1fr 1fr 1fr; grid-template-rows: 1fr 1fr; gap: 12px; min-height: 0; overflow: hidden` (**required**)
- Picture 1: `grid-column: 1/2; grid-row: 1/3`
- Sheets 2-5: 2×2 padding on the right
- `.penta-card`: `min-height: 0; overflow: hidden; position: relative` (**required**)
- `.penta-card img`: `width: 100%; height: 100%; object-fit: cover`
- `.penta-card .cap`: `padding: 14px 16px` (absolutely positioned bottom)
- `.penta-card .cap .title`: `font-size: 13px; font-weight: 500`
- `.penta-card .cap .sub`: `font-size: 11px; margin-top: 2px`

---

## T15 · Hexa · Six-picture layout page

**Purpose**: Display 6 pictures, 3×2 uniform grid, suitable for ecological modules or multi-dimensional screenshots.

**Grid structure**: `grid-template-rows: auto 1fr`
- Top: Title area (reuse `.gallery-head`)
- Main body: 3 columns × 2 rows equally divided grid

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cards × 6 | picture + title + subtitle |

**HTML skeleton**:
```html
<section class="slide s-hexa">
  <div class="gallery-head stagger">
    <div><span class="kicker">[Number] / [Section]</span><h1 class="h-1">[Title]</h1></div>
    <p class="lead">[Description]
  </div>
  <div class="hexa-grid stagger">
    <div class="hexa-card">
      <img src="[URL]" alt="[Description]">
      <div class="cap"><div class="title">[title]</div><div class="sub">[subtitle]</div></div>
    </div>
    <!--Repeat 6 pictures in total-->
  </div>
</section>
```

**Layout Details**:
- `.s-hexa`: `padding-top: 80px; padding-bottom: 84px; gap: 16px`
- The title area reuses the `.gallery-head` parameter (same as T09)
- `.hexa-grid`: `grid-template-columns: repeat(3, 1fr); grid-template-rows: 1fr 1fr; gap: 12px; min-height: 0; overflow: hidden` (**required**)
- 6 pictures are of equal size, no crossing rows or columns
- `.hexa-card`: `min-height: 0; overflow: hidden` (**required**, same as T09 gallery-card reason)
- `.hexa-card img`: `width: 100%; height: 100%; object-fit: cover`
- `.hexa-card .cap`: `padding: 12px 14px` (absolutely positioned bottom)
- `.hexa-card .cap .title`: `font-size: 12px; font-weight: 500`
- `.hexa-card .cap .sub`: `font-size: 10px; margin-top: 2px`

---

## T16 · Mosaic · Multi-picture waterfall page

**Use**: Display 6 or more pictures, the irregular grid creates a magazine waterfall feel, suitable for portfolios/case collections.

**Grid structure**: `grid-template-rows: auto 1fr`
- Top: Title area (reuse `.gallery-head`)
- Main body: 4 columns × 2 rows irregular grid

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | chapter identifier |
| title | Big title |
| lead | description |
| cards × 6 | picture + title |

**HTML skeleton**:
```html
<section class="slide s-mosaic">
  <div class="gallery-head stagger">
    <div><span class="kicker">[Number] / [Section]</span><h1 class="h-1">[Title]</h1></div>
    <p class="lead">[Description]
  </div>
  <div class="mosaic-grid stagger">
    <div class="mosaic-card">
      <img src="[URL]" alt="[Description]">
      <div class="cap"><div class="title">[title]</div></div>
    </div>
    <!--Repeat 6 pictures in total-->
  </div>
</section>
```

**Layout Details**:
- `.s-mosaic`: `padding-top: 80px; padding-bottom: 84px; gap: 16px`
- The title area reuses the `.gallery-head` parameter (same as T09)
- `.mosaic-grid`: `grid-template-columns: repeat(4, 1fr); grid-template-rows: 1fr 1fr; gap: 10px; min-height: 0; overflow: hidden` (**required**)
- Picture 1: `grid-column: 1/3`
- Picture 3: `grid-row: 1/3`
- The rest is automatically filled in
- `.mosaic-card`: `min-height: 0; overflow: hidden; position: relative` (**required**)
- `.mosaic-card img`: `width: 100%; height: 100%; object-fit: cover`
- `.mosaic-card .cap`: `padding: 10px 12px` (absolutely positioned bottom)
- `.mosaic-card .cap .title`: `font-size: 11px; font-weight: 500`
