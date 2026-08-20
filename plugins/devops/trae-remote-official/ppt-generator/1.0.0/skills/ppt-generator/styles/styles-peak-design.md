# Style · Peak Design

A gallery-grade e-commerce visual system based on Peak Design—high-contrast black/white/grey palette, scarce Ember Red accents, Geist sans-serif typography, flat and shadow-free, with a two-tone alternating layout.

Best for: product research, hardware brand showcases, photography/design reports, and minimalist e-commerce-style decks.

---

## §1 CSS Variables

```css
:root {
  --ember: #cc2e39;
  --true-black: #000000;
  --obsidian: #0c0c0c;
  --carbon-ink: #1a211e;
  --slate: #363537;
  --pewter: #4e4e4e;
  --graphite: #606562;
  --ash-border: #cccfcd;
  --mist: #e0e0e0;
  --fog: #eef1f0;
  --paper: #ffffff;

  --font-display: 'Geist', 'Inter', 'Helvetica Neue', sans-serif;
  --font-body: 'Geist', 'Inter', 'Helvetica Neue', sans-serif;

  --radius-card: 8px;
  --radius-btn: 4px;
  --radius-pill: 9999px;
}
```

---

## §2 Typography

| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `.h-display` | 108px | 700 | 0.96 | -0.04em | Cover main title |
| `.h-1` | 56px | 700 | 1.04 | -0.03em | Page title |
| `.h-2` | 36px | 600 | 1.15 | -0.02em | Section heading |
| `.h-3` | 24px | 600 | 1.2 | -0.01em | Card title |
| `.lead` | 18px | 400 | 1.6 | 0 | Description paragraph |
| `.body` | 15px | 400 | 1.55 | 0 | Body text / lists |
| `.kicker` | 12px | 600 | 1 | 0.06em | Uppercase label / tag |
| `.caption` | 11px | 500 | 1.3 | 0.02em | Note / figure caption |

Use Geist throughout (fallback Inter); headings Bold/Semibold, body text Regular.

---

## §3 Surfaces & Backgrounds

| Scene | Background | Foreground |
|---|---|---|
| Standard page | `var(--paper)` #ffffff | `var(--obsidian)` #0c0c0c |
| Dark alternating page | `var(--obsidian)` #0c0c0c | `var(--paper)` #ffffff |
| Card | `var(--fog)` #eef1f0 | `var(--carbon-ink)` #1a211e |
| Chrome (light page) | transparent | `var(--graphite)` #606562 |
| Chrome (dark page) | transparent | `rgba(255,255,255,0.3)` |

**Two-tone alternation**: covers/closings use dark, content pages use light, creating a sense of rhythm.

---

## §4 Color Usage

- **Ember Red `#cc2e39`**: reserved for key emphasis only—CTA buttons, kickers, badges, important data highlights. **Extremely restrained, no more than 2 uses per page.**
- **True Black / Obsidian**: primary text, dark-layout backgrounds.
- **Pewter / Graphite**: secondary information, description text.
- **Ash Border / Mist**: list row-level dividers.
- **Fog**: card backgrounds, secondary panels.
- **Paper White**: main canvas.

---

## §5 Shape & Border

- Cards / product images: `border-radius: 8px`
- Buttons / inputs / nav tabs: `border-radius: 4px`
- Badges / filter pills / tags: `border-radius: 9999px`
- **Cards / color blocks / image containers get no outer border**—hierarchy relies solely on the contrast between the Fog background and the Paper canvas
- Chrome top/bottom bars: no borders or dividers (transparent, text-only overlay)
- List row-level dividers (agenda-item, refine-item, take-item, etc.) keep `1px solid var(--ash-border)`
- **No shadows** (zero box-shadow)

---

## §6 Chart & SVG

```css
.chart-line { stroke: var(--obsidian); stroke-width: 2; fill: none; }
.chart-line-accent { stroke: var(--ember); stroke-width: 2; }
.chart-line-secondary { stroke: var(--ash-border); stroke-width: 1.5; }
.chart-bar-primary { fill: var(--obsidian); }
.chart-bar-secondary { fill: var(--fog); }
.chart-bar-accent { fill: var(--ember); }
.chart-dot { fill: var(--obsidian); }
.chart-grid-line { stroke: var(--mist); stroke-width: 1; }
.chart-label { fill: var(--graphite); font-size: 10px; }
.chart-value { fill: var(--obsidian); font-size: 11px; font-weight: 600; }
```

Charts are primarily black/white/grey; Ember Red is used only when a single data series needs emphasis.

---

## §7 Design Principles

1. **High contrast first**: deep-black text on pure white; refuse grey-toned text for headings.
2. **Extremely restrained Ember Red**: no more than 2 uses of red per page, only to emphasize key data / CTAs / annotations.
3. **No shadows, no outer borders**: cards / color blocks / image containers get no border, with hierarchy relying only on the Fog background contrast; Chrome has no dividers.
4. **Two-tone alternating rhythm**: dark layouts (covers / closings) alternate with light content pages to avoid monotony.
5. **Product-oriented**: prefer large product photography (product close-ups on dark backgrounds work especially well).
6. **Left-aligned dominant**: headings/body default to left alignment, centered only on covers / Think pages.
7. **Cards on Fog ground**: avoid pure-white cards losing their edge definition on a pure-white background.
