# Style · Caldera

A volcanic lava aesthetic built on the Caldera Design System—warm limestone base tones, lava-orange accents, and ultra-bold condensed typography.

Best for: blockchain/Web3 projects, startup pitches, tech product launches, and high-energy brand showcases.

---

## §1 CSS Variables

```css
:root {
  --ember: #fc5000;
  --plasma-violet: #524ae9;
  --sulfur: #f5f28e;
  --obsidian: #070607;
  --pumice: #e2e2df;
  --limestone: #f7f6f2;
  --chalk: #ffffff;

  --font-display: 'Bebas Neue', 'Anton', Impact, sans-serif;
  --font-body: 'DM Sans', 'Inter', sans-serif;

  --radius-card: 40px;
  --radius-sm: 16px;
  --radius-btn: 800px;
}
```

---

## §2 Typography

```css
body {
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--obsidian);
  -webkit-font-smoothing: antialiased;
}

.h-display {
  font-family: var(--font-display);
  font-size: 96px;
  font-weight: 400;
  line-height: 0.95;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--obsidian);
}

.h-1 {
  font-family: var(--font-display);
  font-size: 64px;
  font-weight: 400;
  line-height: 1.0;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--obsidian);
}

.h-2 {
  font-family: var(--font-display);
  font-size: 48px;
  font-weight: 400;
  line-height: 1.0;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--obsidian);
}

.h-3 {
  font-family: var(--font-body);
  font-size: 30px;
  font-weight: 500;
  line-height: 1.3;
  color: var(--obsidian);
}

.lead {
  font-size: 18px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--obsidian);
}

.body {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.55;
  color: var(--obsidian);
}

.kicker {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ember);
}
```

---

## §3 Backgrounds & Surfaces

```css
.slide {
  background: var(--pumice);
}

.card, .brand-card, .line-cell {
  background: var(--limestone);
  border-radius: var(--radius-card);
}

.card--accent {
  background: var(--ember);
  color: var(--obsidian);
  border-radius: var(--radius-card);
}

.slide--dark {
  background: var(--obsidian);
  color: var(--chalk);
}

.slide--dark .card {
  background: rgba(255,255,255,0.06);
}
```

---

## §4 Accent & CTA

```css
.btn-primary {
  background: var(--ember);
  color: var(--obsidian);
  border-radius: var(--radius-btn);
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  border: none;
}

.btn-outline {
  background: transparent;
  color: var(--obsidian);
  border: 1.5px solid var(--obsidian);
  border-radius: var(--radius-btn);
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
}

.tag {
  background: var(--sulfur);
  color: var(--obsidian);
  border-radius: var(--radius-btn);
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 500;
}
```

---

## §5 Chart & SVG

```css
.chart-panel {
  background: var(--limestone);
  border-radius: var(--radius-card);
}

.chart-bar { fill: var(--obsidian); }
.chart-bar.highlight { fill: var(--ember); }
.chart-line { stroke: var(--ember); stroke-width: 2.5; fill: none; }
.chart-dot.highlight { fill: var(--ember); }
.chart-label { fill: var(--obsidian); font-size: 12px; font-weight: 500; }
.chart-axis { stroke: var(--pumice); }
```

---

## §6 Design Principles

- Heading fonts must be 48px or larger—condensed ultra-bold typefaces lose their industrial feel at small sizes
- Buttons are always pill-shaped (800px radius), cards use a 40px radius—this is non-negotiable
- Completely shadow-free: hierarchy is achieved through tonal contrast (Pumice base → Limestone cards → Ember highlights)
- Body text uses only DM Sans 500 (Medium)—Regular is too weak, and Bold competes with headings for visual weight
- Ember orange is the only aggressive color; Plasma Violet is used solely for hero decoration
- Sulfur yellow is used only for small labels/badges
- All headings are uppercase (text-transform: uppercase)
- Chrome top/bottom bars: no borders or divider lines (transparent, plain text overlay)
