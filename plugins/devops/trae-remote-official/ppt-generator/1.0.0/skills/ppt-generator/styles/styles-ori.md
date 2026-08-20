# Style · Ori

A dark, infrastructure-grade aesthetic built on the Ori Design System—pure black canvas, Ember orange as the sole accent, 0px hard corners, and terminal-flavored Mono labels.

Best for: technical architecture, infrastructure, developer tools, data centers, and B2B SaaS product launches.

---

## §1 CSS Variables

```css
:root {
  --ember: #ff4f2b;
  --ember-dark: #e0431f;
  --void: #000000;
  --carbon: #1a1a1a;
  --graphite: #3c3c3c;
  --steel: #737373;
  --fog: #bfbfbf;
  --bone: #f5f5f5;

  --font-display: 'TWK Everett', 'Inter', -apple-system, sans-serif;
  --font-body: 'Switzer', 'Inter', -apple-system, sans-serif;
  --font-mono: 'Chivo Mono', 'JetBrains Mono', monospace;

  --radius-card: 0px;
  --radius-btn: 0px;
  --radius-ghost: 0px;
}
```

---

## §2 Typography

```css
body {
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--bone);
  -webkit-font-smoothing: antialiased;
}

.h-display {
  font-family: var(--font-display);
  font-size: 96px;
  font-weight: 300;
  line-height: 0.95;
  letter-spacing: -0.011em;
  color: var(--bone);
}

.h-1 {
  font-family: var(--font-display);
  font-size: 36px;
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: -0.011em;
  color: var(--bone);
}

.h-2 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 400;
  line-height: 1.2;
  letter-spacing: -0.011em;
  color: var(--bone);
}

.h-3 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 400;
  line-height: 1.2;
  color: var(--bone);
}

.lead {
  font-family: var(--font-body);
  font-size: 18px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--fog);
}

.body {
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.4;
  color: var(--fog);
}

.kicker {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 0;
  text-transform: uppercase;
  color: var(--steel);
}

.meta {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.2;
  color: var(--steel);
}
```

---

## §3 Backgrounds & Surfaces

```css
.slide {
  background: var(--void);
}

.card, .brand-card, .line-cell {
  background: var(--carbon);
  border: 1px solid var(--graphite);
  border-radius: var(--radius-card);
}

.accent-surface {
  background: var(--ember);
  color: var(--void);
}
```

---

## §4 Accent & CTA

```css
.btn-primary {
  background: var(--ember);
  color: var(--void);
  border-radius: var(--radius-btn);
  padding: 8px 16px;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  text-transform: uppercase;
  border: none;
}

.btn-ghost {
  background: transparent;
  color: var(--bone);
  border: 1px solid var(--bone);
  border-radius: var(--radius-ghost);
  padding: 8px 16px;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
  text-transform: uppercase;
}

.badge {
  color: var(--ember);
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 400;
}
```

---

## §5 Chart & SVG

```css
.chart-panel {
  background: var(--carbon);
  border: 1px solid var(--graphite);
  border-radius: var(--radius-card);
}

.chart-bar { fill: var(--bone); }
.chart-bar.highlight { fill: var(--ember); }
.chart-line { stroke: var(--bone); stroke-width: 2; fill: none; }
.chart-dot.highlight { fill: var(--ember); }
.chart-label { fill: var(--steel); font-family: var(--font-mono); font-size: 12px; }
.chart-axis { stroke: var(--graphite); }
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

- Ember orange (#ff4f2b) is the only chromatic accent—reserved for CTA buttons, full-bleed color bands, and key emphasis words
- Introduce no color other than Ember
- All corners are 0px—hard angles convey precision and an industrial feel
- Cards have no shadow; hierarchy is expressed through surface contrast (#000 vs #1a1a1a) and a 1px hairline border (#3c3c3c)
- Images are full-bleed with no rounded corners—dark, cinematic, infrastructure/data-center themes
- No gradients, glows, or 3D rendering
- Mono type (Chivo Mono) is used for all UI labels, nav items, and button text—a terminal/server-room texture
- Chrome top/bottom bars: no borders or dividers (transparent, text-only overlay)
- Typography is tight and rigorous; the -0.011em negative tracking on headings conveys a cold, architectural feel
- At most one full-bleed Ember color band (accent-surface) per page, used for visual rhythm
