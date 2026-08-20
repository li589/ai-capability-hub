# Layouts · Structure page

Opening and closing layouts: cover, table of contents, and closing. Each deck **must include** a cover page (T01) and a closing page (T08), both counted within the target slide total. The table of contents page (T02) is optional and must replace another planned slide rather than increase the total.

For visual styles, see the corresponding styles file in the `../styles/` directory.

---

## Canvas constraints

- Fixed canvas: **1280×720 px**
- **Layout size** must be a fixed `px` value (padding, gap, margin, width, height, etc.)
- **Exception**: The font size auxiliary classes (such as `.h-display`, `.h-1`, `.lead`) and Chrome padding (`--pad-x`) in the styles file allow the use of `clamp()` for font scaling adaptation, but the layout structural size must still be fixed px
- **It is forbidden** to use `vw` and `vh` as width, height/padding/gap values ​​in the layout structure
- Each slide is wrapped using `<section class="slide s-xxx">`
- All slides are based on CSS Grid layout by default; except for the layout marked `display:flex` in the layout file

## Common font size benchmark

| class name | font-size | line-height | additional |
|---|---|---|---|
| `.h-display` | 108px | .96 | font-weight: 200 |
| `.h-1` | 64px | 1.02 | — |
| `.h-2` | 36px | 1.15 | — |
| `.lead` | 18px | 1.7 | max-width: 62ch |
| `.body` | 15px | 1.7 | — |
| `.kicker` | 11px | — | — |

## Chrome Safe Zone

Each page always contains a top brand bar (40px) and a bottom page number bar (40px). The content area must be avoided:

- **Top Safe Area**: `0 ~ 48px` (Chrome 40px + 8px spacing) - no content allowed
- **Bottom Safe Area**: `672px ~ 720px` (Chrome 40px + 8px spacing) - no content is allowed
- **Effective content area**: `y: 48px ~ 672px` (height 624px)

## Universal padding

- Horizontal padding: `72px` (72px on the left and right)
- Vertical padding: `padding-top: 56px; padding-bottom: 56px` (Chrome safe area included)
- **Actual meaning**: The content starts at 56px from the top and ends at 56px from the bottom to ensure that it does not invade the Chrome area

## Full screen background image rules

When you need a picture to cover the entire slide (such as T01-D Cover Hero):

- **Must use** CSS `background-image` + `background-size: cover` + `background-position: center` (set on `<section>` through inline style)
- **Forbidden to use** `<div><img>` + `position: absolute; inset: 0`
- **Cause**: `display: grid` of `.slide` will cause absolutely positioned child elements to not correctly fill 100% of the height of the parent container under certain rendering conditions.
- Gradient mask is implemented through `::before` pseudo-element, and the foreground content needs to be set `position: relative; z-index: 2`

---

## T01 · Cover · Cover page

**Purpose**: deck starts, showing name + core positioning.

**Grid structure**: `grid-template-rows: 1fr auto`
- Upper part (1fr): main visual area - large title + subtitle, left-aligned and top-aligned (single column, no left hero word)
- Bottom (auto): four-column meta-information grid (border-top separated)

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | brand identity |
| title | Chinese title (1-2 lines) |
| subtitle | lead description (1-2 lines) |
| meta × 4 | tag + value (such as PRODUCT / TOPIC / DECK) |

**HTML skeleton**:
```html
<section class="slide s-cover active">
  <div class="cover-main stagger">
    <span class="kicker">[Brand Identity]</span>
    <div class="cover-chinese">
      <span>[main title]</span>
      <span>[subtitle]</span>
    </div>
    <p class="cover-sub lead">[description]</p>
  </div>
  <div class="cover-meta">
    <div>[LABEL] <strong>[Value]</strong></div>
    <!-- Repeat 4 items-->
  </div>
</section>
```

**Layout Details**:
- `.cover-main`: `align-self: center` — the title block is vertically centered in the upper area, left-aligned
- `.cover-chinese`: `font-size: 120px; line-height: .95; font-weight: 200`
- `.cover-sub`: `margin-top: 22px`
- `.cover-meta`: `grid-template-columns: repeat(4, 1fr); gap: 32px; padding-top: 32px`
- `.cover-meta` tag: `font-size: 11px`
- `.cover-meta strong`: `font-size: 18px; margin-top: 8px`

---

## T01-B · Cover Split · Split screen cover

**Usage**: Magazine-style cover with text on the left and picture on the right, suitable for scenes with product screenshots or brand visuals.

**Grid structure**: `grid-template-columns: 1fr 1fr; padding: 0`
- Left half: text area (kicker + title + description + bottom label line)
- Right half: Full height picture area

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | brand/chapter logo |
| title | Large title (1-3 lines) |
| lead | description paragraph |
| tags | Bottom tag group (2-4) |
| image | Full height image on the right |

**HTML skeleton**:
```html
<section class="slide s-cover-split active">
  <div class="cover-split-text stagger">
    <span class="kicker">[Brand Identity]</span>
    <h1 class="h-display">[main title]</h1>
    <p class="lead">[Description]
    <div class="cover-split-tags">
      <span>[Tag 1]</span><span>[Tag 2]</span><span>[Tag 3]</span>
    </div>
  </div>
  <div class="cover-split-img">
    <img src="[image URL]" alt="[semantic description]">
  </div>
</section>
```

**Layout Details**:
- `.s-cover-split`: `grid-template-columns: 1fr 1fr; padding: 0`
- `.cover-split-text`: `padding: 40px 52px; display: flex; flex-direction: column; justify-content: center; gap: 0`
- `.cover-split-text .h-display`: `font-size: 72px; line-height: .96; margin-top: 20px`
- `.cover-split-text .lead`: `margin-top: 24px; max-width: 38ch`
- `.cover-split-tags`: `margin-top: 28px; display: flex; gap: 16px` — a **fixed** margin, not `margin-top: auto`. The text column is a centered flex column (`justify-content: center`); `margin-top: auto` there absorbs all leftover vertical space and shoves the tags to the column bottom, opening a large gap between the title block and the tags. Keep the tags grouped with the title/lead via a fixed margin.
- `.cover-split-tags span`: `font-size: 11px; padding: 6px 14px`
- `.cover-split-img`: `overflow: hidden`
- `.cover-split-img img`: `width: 100%; height: 100%; object-fit: cover`

---

## T01-C · Cover Minimal · Minimalist cover

**Purpose**: A minimalist cover driven purely by typography, without pictures, relying on font size contrast and a lot of white space to create a high-end feel.

**Grid structure**: `grid-template-rows: auto 1fr auto` (three lines: top navigation bar/centered title area/bottom information row)
- Top (auto): brand name + date
- Middle (1fr): Centered giant title + subtitle
- Bottom (auto): a row of meta information horizontally

**Content Slots**:
| Slot | Description |
|---|---|
| brand | top brand name |
| date | top date |
| title | giant main title (1 line) |
| subtitle | subtitle/description |
| meta-left | Bottom left copywriting |
| meta-right | Copywriting on the right side of the bottom |

**HTML skeleton**:
```html
<section class="slide s-cover-min active">
  <div class="cover-min-top">
    <span>[brand name]</span>
    <span>[Date]</span>
  </div>
  <div class="cover-min-center stagger">
    <h1 class="h-display">[main title]</h1>
    <p class="lead">[Subtitle/Description]
  </div>
  <div class="cover-min-bottom">
    <span>[Information on the left]</span>
    <span>[Information on the right]</span>
  </div>
</section>
```

**Layout Details**:
- `.s-cover-min`: `grid-template-rows: auto 1fr auto; gap: 0`
- `.cover-min-top`: `display: flex; justify-content: space-between; align-items: center; font-size: 12px; padding-bottom: 24px`
- `.cover-min-center`: `display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 0`
- `.cover-min-center .h-display`: `font-size: 128px; line-height: .92; font-weight: 200`
- `.cover-min-center .lead`: `margin-top: 28px; max-width: 52ch; font-size: 16px`
- `.cover-min-bottom`: `display: flex; justify-content: space-between; align-items: center; font-size: 12px; padding-top: 24px`

---

## T01-D · Cover Hero · Full cover

**Usage**: An immersive cover with full-screen images + text overlay, suitable for visually driven scenarios such as brand promotion and product launches.

**Grid structure**: `grid-template-rows: 1fr auto` (no padding, full of pictures)
- Image layer: filled with CSS `background-image` (**It is forbidden to use `<img>` + absolute positioning**, which will cause the grid container to be full)
- Gradient mask: use `::before` pseudo-element
- Foreground: Title area at the bottom left

**Content Slots**:
| Slot | Description |
|---|---|
| image | Full screen background image (set background-image via inline style) |
| kicker | brand/chapter logo |
| title | Large title (1-2 lines) |
| lead | description |
| meta | Meta information on the right side of the bottom (1-2 items) |

**HTML skeleton**:
```html
<section class="slide s-cover-hero active" style="background: var(--obsidian) url('[image URL]') center/cover no-repeat;">
  <div class="cover-hero-content stagger">
    <span class="kicker">[Brand Identity]</span>
    <h1 class="h-display">[main title]</h1>
    <p class="lead">[Description]
  </div>
  <div class="cover-hero-meta">
    <span>[Message 1]</span>
    <span>[Message 2]</span>
  </div>
</section>
```

**Layout Details**:
- `.s-cover-hero`: `grid-template-rows: 1fr auto; padding: 0; overflow: hidden`
- `.s-cover-hero::before`: `content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(to top, rgba(0,0,0,.75) 0%, rgba(0,0,0,.2) 50%, transparent 100%); z-index:1` (Gradient Mask)
- `.cover-hero-content`: `position: relative; z-index: 2; padding: 0 52px 28px; align-self: end; max-width: 70%`
- `.cover-hero-content .h-display`: `font-size: 96px; line-height: .94; font-weight: 200; margin-top: 16px`
- `.cover-hero-content .lead`: `margin-top: 20px; max-width: 48ch; font-size: 16px`
- `.cover-hero-meta`: `position: relative; z-index: 2; padding: 18px 52px; display: flex; justify-content: flex-end; gap: 32px; font-size: 12px`

**⚠️ Key rules**: The full-screen background image** must use CSS `background-image`**, and the `<img>` + `position: absolute` method is not allowed.Reason: `display: grid` of `.slide` will cause absolutely positioned child elements to not correctly fill the parent container under certain rendering conditions.

---

## T02 · Agenda · Contents page

**Purpose**: Show the content structure of 3-6 chapters.

**Grid structure**: `grid-template-columns: 330px 1fr`
- Left column: title area (kicker + title + lead)
- Right column: list area (one line for each item, separated by border)

**Content Slots**:
| Slot | Description |
|---|---|
| kicker | "Table of Contents" |
| title | Big title |
| lead | description |
| items × 3-6 | Number + Chinese name + English label |

**HTML skeleton**:
```html
<section class="slide s-agenda">
  <div class="stagger">
    <span class="kicker">[logo]</span>
    <h2 class="h-1">[Title]</h2>
    <p class="lead">[Description]
  </div>
  <div class="agenda-list stagger">
    <div class="agenda-item">
      <span class="idx">01</span>
      <span class="name">[Chapter name]</span>
      <span class="en">[English]</span>
    </div>
    <!-- Repeat -->
  </div>
</section>
```

**Layout Details**:
- `.s-agenda`: `grid-template-columns: 330px 1fr; gap: 72px; align-items: center`
- `.agenda-list`: `display: flex; flex-direction: column; min-height: 0; overflow: hidden` (**required** to prevent the list from stretching out of the content area)
- `.agenda-side .lead`: `margin-top: 24px`
- `.agenda-item`: `grid-template-columns: 60px 1fr auto; padding: 18px 0; gap: 20px`
- `.agenda-item .idx`: `font-size: 22px; font-weight: 200`
- `.agenda-item .name`: `font-size: 26px; font-weight: 500`
- `.agenda-item .en`: `font-size: 12px`

**Anti-overflow rules**:
- The directory page supports up to 6 items.Available height = 720 − padding-top(56) − padding-bottom(56) = 608px
- The height of each item ≈ padding(18×2) + line-height(26×1.2) ≈ 67px, 6 items ≈ 402px, plus the safety margin of border and title area
- **Forbidden** `.agenda-item .name` font size exceeds 28px, **Forbidden** padding exceeds 20px
- If items ≤ 4, the font size can be appropriately enlarged to 30px / padding to 24px

---

## T08 · Closing · Closing page

**Purpose**: Deck ending, summarizing key points + brand statement.

**Grid structure**: `grid-template-columns: 1fr 1fr; padding: 0` (left and right)
- Left half: full color background + large declaration letters + top/bottom signature
- Right half: white background + 3 takeaways + bottom CTA

**Content Slots**:
| Slot | Description |
|---|---|
| manifesto | Declaration in large characters (2-3 lines) |
| sub | sublabel description |
| sig | brand+time|
| takeaways × 3 | number + title + description |
| cta | bottom call to action |

**HTML skeleton**:
```html
<section class="slide s-close">
  <div class="close-left">
    <canvas class="ascii-bg" aria-hidden="true"></canvas>
    <div class="chrome-min"><span>[page number]</span><span>Closing</span></div>
    <div class="manifesto stagger">
      <div class="meta">[tag]</div>
      <h2>[Declaration]</h2>
      <div class="sub">[subtitle]</div>
    </div>
    <div class="sig"><span>[Brand]</span><span>[Time]</span></div>
  </div>
  <div class="close-right">
    <div class="chrome-min"><span>Takeaways</span><span>03 Points</span></div>
    <div class="takeaways stagger">
      <div class="take-item"><div class="num">01</div><div><h3>[Title]</h3><p>[Description]</p></div></div>
      <!-- Repeat 3 items-->
    </div>
    <div class="foot">→ [CTA]</div>
  </div>
</section>
```

**Layout Details**:
- `.s-close`: `grid-template-columns: 1fr 1fr; padding: 0`
- Left padding: `28px 46px 28px 77px`
- Right padding: `28px 77px 28px 46px`
- `.manifesto h2`: `font-size: 80px; font-weight: 200; line-height: .96`
- `.manifesto .sub`: `font-size: 15px; margin-top: 10px`
- `.take-item`: `grid-template-columns: auto 1fr; gap: 24px; padding: 20px 0`
- `.take-item .num`: `font-size: 52px; font-weight: 200`
- `.take-item h3`: `font-size: 22px; margin-bottom: 8px`
- `.take-item p`: `font-size: 15px`
- `.chrome-min / .sig / .foot`: `font-size: 12px`

**Deck chrome must not double up**: T08 is a full-bleed split that already carries its **own** top identifiers (`.chrome-min` per column) and bottom sign-off (`.sig` / `.foot`). The persistent deck-level `.chrome-top` / `.chrome-bottom` bars would otherwise sit on top of these and produce a **doubled top brand row and doubled bottom page-number row**. Suppress the deck bars while the close slide is active (e.g. `.deck:has(.s-close.active) .chrome-top, …{ opacity:0; visibility:hidden }`); keep the nav dots. Do not delete the deck bars globally — they are needed on every other slide.

**Align the close chrome to the deck chrome**: so the ending reads as the same deck, the column padding is set to place the self-owned chrome at the **same edges as the global bars** — top/bottom `28px` and outer inset `77px` (matching `.chrome-top`/`.chrome-bottom` top/bottom:28px and `--pad-x:77px`). The inner (center-seam) inset stays `46px`. Hence left padding `28px 46px 28px 77px` (outer edge = left), right padding `28px 77px 28px 46px` (outer edge = right). Driven by column padding + `justify-content: space-between`, not absolute positioning.
