# Style · Airbnb

A quiet gallery aesthetic built on the Airbnb Design System—pure white canvas, image-led layouts, and coral red as the single accent color.

Best for: travel/lifestyle content, product showcases, user stories, and human-interest research reports.

---

## §1 CSS Variables

```css
:root {
  --rausch: #ff385c;
  --rausch-dark: #e00b41;
  --hof: #222222;
  --foggy: #6a6a6a;
  --grey-500: #c1c1c1;
  --bebe: #ebebeb;
  --deco: #dddddd;
  --faint: #f7f7f7;
  --white: #ffffff;

  --font-sans: 'DM Sans', 'Inter', -apple-system, sans-serif;

  --radius-card: 12px;
  --radius-btn: 9999px;
  --radius-ghost: 8px;
}
```

---

## §2 Typography

```css
body {
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.43;
  color: var(--hof);
  -webkit-font-smoothing: antialiased;
}

.h-display {
  font-size: 56px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
  color: var(--hof);
}

.h-1 {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.43;
  color: var(--hof);
}

.h-2 {
  font-size: 22px;
  font-weight: 500;
  line-height: 1.18;
  letter-spacing: -0.02em;
  color: var(--hof);
}

.h-3 {
  font-size: 20px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.009em;
  color: var(--hof);
}

.lead {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.25;
  color: var(--hof);
}

.body {
  font-size: 14px;
  line-height: 1.43;
  color: var(--hof);
}

.kicker {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--foggy);
}

.meta {
  font-size: 13px;
  font-weight: 400;
  line-height: 1.23;
  color: var(--foggy);
}
```

---

## §3 Backgrounds & Surfaces

```css
.slide {
  background: var(--faint);
}

.card, .brand-card, .line-cell {
  background: var(--white);
  border-radius: var(--radius-card);
}

.accent-surface {
  background: var(--hof);
  color: var(--white);
}
```

---

## §4 Accent & CTA

```css
.btn-primary {
  background: var(--rausch);
  color: var(--white);
  border-radius: var(--radius-btn);
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  border: none;
}

.btn-ghost {
  background: var(--white);
  color: var(--hof);
  border: 1px solid var(--hof);
  border-radius: var(--radius-ghost);
  padding: 8px 16px;
  font-size: 14px;
  font-weight: 500;
}

.badge {
  color: var(--rausch);
  font-size: 12px;
  font-weight: 600;
}
```

---

## §5 Chart & SVG

```css
.chart-panel {
  background: var(--white);
  border-radius: var(--radius-card);
}

.chart-bar { fill: var(--hof); }
.chart-bar.highlight { fill: var(--rausch); }
.chart-line { stroke: var(--hof); stroke-width: 2; fill: none; }
.chart-dot.highlight { fill: var(--rausch); }
.chart-label { fill: var(--foggy); font-size: 12px; }
.chart-axis { stroke: var(--bebe); }
```

---

## §6 Image Treatment

```css
.gallery-card img,
.hero-img {
  border-radius: var(--radius-card);
  object-fit: cover;
  width: 100%;
}
```

---

## §7 Design Principles

- Rausch coral red is the only color accent—use it solely for CTAs, favorite hearts, and brand identity
- Never introduce any color beyond Rausch
- Cards have no borders and no shadows; layering relies on the tonal contrast between the faint #f7f7f7 canvas and white cards
- Images are full-bleed to fill the card frame—no padding, no decorative borders
- Only two corner radii: 12px (cards) and 9999px (button/control pills)
- Compact, dense typography—14px body + 22–28px headings already cover most scenarios
- Chrome top/bottom bars: no borders or divider lines (transparent, plain text overlay)
