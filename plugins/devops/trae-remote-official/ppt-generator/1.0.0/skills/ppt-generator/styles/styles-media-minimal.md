# Style · Media Minimal

A visual system based on Refero Minimal Design—pure white canvas, neutral black as the only contrast color, minimalist Helvetica Neue type, zero ornamentation, extra-large whitespace, and media content as the sole protagonist.

Best for: images and video, photography portfolios, creative showcases, visual case studies, and imagery-driven content reports.

---

## §1 CSS Variables

```css
:root {
  --black: #000000;
  --charcoal: #1a1a1a;
  --graphite: #333333;
  --steel: #555555;
  --grey: #888888;
  --silver: #aaaaaa;
  --light: #d4d4d4;
  --mist: #eeeeee;
  --snow: #f7f7f7;
  --white: #ffffff;

  --font-display: 'Helvetica Neue', 'Arial', sans-serif;
  --font-body: 'Helvetica Neue', 'Arial', sans-serif;
  --font-mono: 'SF Mono', 'Monaco', monospace;

  --radius-card: 0px;
  --radius-btn: 0px;
  --radius-pill: 0px;
}
```

---

## §2 Typography

| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `.h-display` | 80px | 300 | 0.92 | -0.03em | Cover main title |
| `.h-1` | 52px | 300 | 1.02 | -0.02em | Page title |
| `.h-2` | 32px | 400 | 1.15 | -0.01em | Section heading |
| `.h-3` | 20px | 500 | 1.3 | 0 | Card title |
| `.lead` | 18px | 300 | 1.7 | 0 | Description paragraph |
| `.body` | 15px | 400 | 1.7 | 0.01em | Body text / lists |
| `.kicker` | 10px | 500 | 1 | 0.12em | Uppercase label / tag |
| `.caption` | 11px | 400 | 1.4 | 0.04em | Note / figure caption |
| `.mono` | 12px | 400 | 1.5 | 0 | Metadata |

Ultra-thin weight (300) headings + large sizes create a light, modern feel. The uppercase kicker is extremely small and light.

---

## §3 Surfaces & Backgrounds

| Scene | Background | Foreground |
|---|---|---|
| Main canvas | `var(--white)` #ffffff | `var(--charcoal)` #1a1a1a |
| Card / panel | `var(--snow)` #f7f7f7 | `var(--graphite)` #333333 |
| Elevated panel | `var(--mist)` #eeeeee | `var(--black)` #000000 |
| Chrome top/bottom bar | transparent | `var(--grey)` #888888 |
| Dark contrast page | `var(--black)` #000000 | `var(--white)` #ffffff |

Minimalist pure-white mode. Images/video are the only source of color.

---

## §4 Color Usage

- **Black `#000000`**: the only accent—heading text, key figure captions.
- **Achromatic system**: the entire style uses no color accents; all differentiation relies on black/white/grey brightness differences.
- **Charcoal → Grey → Silver**: builds the text hierarchy.
- **Snow/Mist**: subtle background differences to separate regions.
- **The image itself is the color**: all color expression is handed to the media content.

---

## §5 Shape & Border

- Cards / panels: `border-radius: 0px` (hard corners, gallery-grade)
- Buttons / inputs: `border-radius: 0px`
- Borders: `1px solid var(--mist)` — an ultra-light grey line, nearly invisible
- No shadows, no rounded corners, no ornamentation—return to the image itself
- Images have no borders and no rounded corners, shown edge-to-edge

---

## §6 Chrome

```css
.chrome {
  position: absolute; top: 0; left: 0; right: 0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 72px;
  font-size: 10px; font-weight: 500; letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--grey);
}
.chrome-bottom {
  position: absolute; bottom: 0; left: 0; right: 0;
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 72px;
  font-size: 10px; color: var(--grey);
}
.chrome-bottom .page-num { font-weight: 500; color: var(--steel); }
```

---

## §7 T01 Cover

```css
.s-cover {
  background: var(--white);
  color: var(--graphite);
}
.s-cover .h-display {
  font-size: 80px; font-weight: 300;
  line-height: 0.92; letter-spacing: -0.03em;
  color: var(--black);
}
.s-cover .kicker {
  color: var(--grey);
}
.s-cover .lead {
  color: var(--steel);
  font-weight: 300;
  max-width: 48ch;
}
```

---

## §8 T01-B Cover Split

```css
.s-cover-split {
  background: var(--white);
}
.cover-split-text .kicker { color: var(--grey); }
.cover-split-text .h-display {
  font-size: 64px; font-weight: 300;
  color: var(--black);
}
.cover-split-text .lead { color: var(--steel); }
.cover-split-tags span {
  border: 1px solid var(--light);
  color: var(--grey);
}
.cover-split-img { overflow: hidden; }
```

---

## §9 T01-C Cover Minimal

```css
.s-cover-min {
  background: var(--white);
}
.s-cover-min .kicker { color: var(--grey); }
.s-cover-min .h-display {
  font-size: 80px; font-weight: 300;
  color: var(--black);
}
.s-cover-min .lead { color: var(--steel); }
.s-cover-min .rule {
  width: 32px; height: 1px;
  background: var(--black);
}
```

---

## §10 T01-D Cover Full-bleed

```css
.s-cover-full {
  background: var(--black);
}
.s-cover-full .overlay {
  background: linear-gradient(180deg, rgba(0,0,0,0) 30%, rgba(0,0,0,0.7) 100%);
}
.s-cover-full .h-display {
  font-size: 80px; font-weight: 300;
  color: var(--white);
}
.s-cover-full .kicker { color: var(--silver); }
.s-cover-full .lead { color: var(--light); }
```

---

## §11 T02 Agenda

```css
.s-agenda { background: var(--white); }
.s-agenda .h-1 { color: var(--black); font-weight: 300; }
.s-agenda .lead { color: var(--steel); }
.agenda-item {
  border-bottom: 1px solid var(--mist);
}
.agenda-item .idx {
  font-size: 28px; font-weight: 300;
  color: var(--light);
}
.agenda-item .name {
  font-size: 34px; font-weight: 300;
  color: var(--charcoal);
}
.agenda-item .en { color: var(--grey); }
```

---

## §12 T03 Brand

```css
.s-brand { background: var(--white); }
.brand-left .kicker { color: var(--grey); }
.brand-left .h-1 { color: var(--black); font-weight: 300; }
.brand-left .lead { color: var(--steel); }
.brand-stats { border-top: 1px solid var(--mist); }
.brand-stats .k {
  font-size: 44px; font-weight: 300;
  color: var(--black);
}
.brand-stats .lbl { color: var(--grey); }
.brand-card {
  background: var(--snow);
  border: 1px solid var(--mist);
}
.brand-card .tag { color: var(--grey); }
.brand-card .title { color: var(--charcoal); }
.brand-card .desc { color: var(--steel); }
.brand-card .badge {
  background: var(--black); color: var(--white);
  font-weight: 500;
}
```

---

## §13 T04 Grid Lines

```css
.s-lines { background: var(--white); }
.lines-head .kicker { color: var(--grey); }
.lines-head .h-1 { color: var(--black); font-weight: 300; }
.line-cell {
  background: var(--snow);
  border: 1px solid var(--mist);
}
.line-cell .num { font-weight: 300; color: var(--light); }
.line-cell .name { color: var(--charcoal); }
.line-cell .en { color: var(--grey); }
.line-cell .micro-rule { background: var(--mist); }
.line-cell .desc { color: var(--steel); }
.line-cell .accent { color: var(--black); }
```

---

## §14 T05 Team Cards

```css
.s-team { background: var(--white); }
.s-team .kicker { color: var(--grey); }
.s-team .h-1 { color: var(--black); font-weight: 300; }
.s-team .lead { color: var(--steel); }
.team-card {
  background: var(--snow);
  border: 1px solid var(--mist);
}
.team-card .idx { color: var(--light); }
.team-card .title { color: var(--charcoal); }
.team-card .en-sub { color: var(--grey); }
.team-card .desc { color: var(--steel); }
```

---

## §15 T06 Refine List

```css
.s-refine { background: var(--white); }
.s-refine .kicker { color: var(--grey); }
.s-refine .h-1 { color: var(--black); font-weight: 300; }
.s-refine .lead { color: var(--steel); }
.refine-item { border-bottom: 1px solid var(--mist); }
.refine-item .idx { color: var(--black); font-weight: 500; }
.refine-item .h { color: var(--charcoal); }
.refine-item .d { color: var(--steel); }
```

---

## §16 T07 Think

```css
.s-think { background: var(--snow); }
.think-kicker { color: var(--grey); }
.think-q {
  font-size: 64px; font-weight: 300;
  color: var(--black);
}
.think-q em { font-style: italic; color: var(--graphite); }
.think-sub { color: var(--steel); }
.think-note {
  background: var(--white);
  border: 1px solid var(--mist);
}
.think-note b { color: var(--black); }
```

---

## §17 T08 Closing

```css
.close-left {
  background: var(--black); color: var(--light);
}
.close-left .chrome-min { color: var(--grey); }
.manifesto .meta { color: var(--silver); }
.manifesto h2 {
  font-size: 64px; font-weight: 300;
  color: var(--white);
}
.manifesto .sub { color: var(--silver); }
.close-right {
  background: var(--white);
}
.close-right .chrome-min { color: var(--grey); }
.take-item { border-bottom: 1px solid var(--mist); }
.take-item .num { font-weight: 300; color: var(--light); }
.take-item h3 { color: var(--charcoal); }
.take-item p { color: var(--steel); }
.close-right .foot { color: var(--black); }
```

---

## §18 T09 Gallery

```css
.s-gallery { background: var(--white); }
.gallery-head .kicker { color: var(--grey); }
.gallery-head .h-1 { color: var(--black); font-weight: 300; }
.gallery-card {
  border: none;
  overflow: hidden;
}
.gallery-card img { border-radius: 0; }
.gallery-cap { background: var(--white); padding-top: 12px; }
.gallery-cap .label { color: var(--grey); }
.gallery-cap .title { color: var(--charcoal); }
```

---

## §19 T10–T16 Image Pages

All image pages share:
```css
[class*="s-img"] { background: var(--white); }
[class*="s-img"] .kicker { color: var(--grey); }
[class*="s-img"] .h-1 { color: var(--black); font-weight: 300; }
[class*="s-img"] .lead { color: var(--steel); }
[class*="s-img"] img {
  border-radius: 0;
  border: none;
}
[class*="s-img"] .caption { color: var(--grey); }
```

---

## §20 T17 Chart

```css
.s-chart { background: var(--white); }
.chart-head .kicker { color: var(--grey); }
.chart-head .h-1 { color: var(--black); font-weight: 300; }
.chart-grid {
  border: 1px solid var(--mist);
  background: var(--snow);
}
.chart-panel { background: var(--snow); }
.chart-title { color: var(--grey); }
.chart-subtitle { color: var(--charcoal); }

.chart-bar-primary { fill: var(--charcoal); }
.chart-bar-accent { fill: var(--black); }
.chart-bar-secondary { fill: var(--light); }
.chart-line { stroke: var(--charcoal); stroke-width: 1.5; }
.chart-line-accent { stroke: var(--black); stroke-width: 1.5; }
.chart-dot { fill: var(--charcoal); }
.chart-dot-accent { fill: var(--black); }
.chart-area { fill: var(--black); opacity: 0.05; }
.chart-label { fill: var(--grey); font-size: 10px; }
.chart-value { fill: var(--charcoal); font-size: 10px; font-weight: 500; }
.chart-grid-line { stroke: var(--mist); stroke-width: 0.5; }
```

---

## §21 Navigation & Dots

```css
.nav-dots .dot { background: var(--light); }
.nav-dots .dot.active { background: var(--black); width: 18px; }
```

Bottom dots navigation only, with no left/right arrows.

---

## §22 Animation

```css
@keyframes rise {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
.slide.active .stagger > * {
  animation: rise 0.5s ease forwards;
}
```

---

## §23 Design Principles

1. **Content first**: images/video are the sole protagonist; all UI elements recede to minimal presence.
2. **Zero color**: no color accents are used, avoiding competition with the media content's colors.
3. **Ultra-light weight**: 300-weight headings create a light, breathing feel without stealing the visual focus.
4. **Hard-corner gallery**: 0px radius mimics a museum-hang display, with images shown edge-to-edge without borders.
5. **Maximal whitespace**: content occupies no more than 50%; whitespace itself is the design language.
6. **Uppercase micro-labels**: the kicker uses a 10px + 0.12em letter-spacing uppercase micro-label, extremely understated.
7. **Chrome top/bottom bars**: no borders or dividers (transparent, text-only overlay).

---

## §24 Font Loading

```html
<!-- Helvetica Neue is a system font; no extra loading required -->
<!-- For web-environment compatibility, Inter Light can be used as a substitute -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap" rel="stylesheet">
```
