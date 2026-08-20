# Style · Privy Editorial

An editorial crypto-fintech style based on the Privy Design System—near-monochrome canvas, a single violet accent band, heavy-ink buttons, and typography-driven brand identity.

Best for: fintech product demos, Web3/Crypto reports, designer portfolios, and editorial-style content.

---

## §1 CSS Variables

```css
:root {
  --iris: #635bff;
  --deep-teal: #072723;
  --obsidian: #010110;
  --carbon: #111117;
  --graphite: #22222a;
  --fog: #73737c;
  --ash: #d9d9d9;
  --canvas: #ffffff;

  --font-display: 'ABC Favorit', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;

  --radius-pill: 100px;
  --radius-card: 8px;
  --radius-icon: 2px;
}
```

---

## §2 Typography

```css
.h-display { font-family: var(--font-display); font-size: 64px; font-weight: 400; line-height: 1.06; letter-spacing: -0.03em; color: var(--obsidian); }
.h-1 { font-family: var(--font-display); font-size: 48px; font-weight: 400; line-height: 1.1; letter-spacing: -0.03em; color: var(--obsidian); }
.h-2 { font-family: var(--font-display); font-size: 28px; font-weight: 400; line-height: 1.2; letter-spacing: -0.02em; color: var(--obsidian); }
.lead { font-family: var(--font-body); font-size: 18px; font-weight: 400; line-height: 1.5; color: var(--fog); }
.body { font-family: var(--font-body); font-size: 16px; line-height: 1.45; color: var(--obsidian); }
.kicker { font-family: var(--font-body); font-size: 13px; font-weight: 500; letter-spacing: 0.02em; text-transform: uppercase; color: var(--iris); }
```

Display type (≥26px) uses ABC Favorit at weight 400; body text uses Inter. Headings are not bolded—they build force through size and negative tracking.

---

## §3 Backgrounds & Surfaces

| Scene | Background | Foreground |
|---|---|---|
| Page canvas | `var(--canvas)` #ffffff | `var(--obsidian)` #010110 |
| Light card | `var(--canvas)` #ffffff | `var(--obsidian)` |
| Dark feature card | `var(--graphite)` #22222a | `var(--canvas)` #ffffff |
| Accent surface (cover/closing) | `var(--obsidian)` #010110 | `var(--canvas)` |
| Announcement bar | `var(--iris)` #635bff | `var(--canvas)` |
| Chrome | transparent | `var(--fog)` #73737c |

Card border: `1px solid rgba(1, 1, 16, .08)`; dark card border: `1px solid rgba(255, 255, 255, .06)`.

---

## §4 Color Usage

| Token | Use |
|---|---|
| `--obsidian` | Main headings, body text, primary button fill |
| `--carbon` | Dark-mode surfaces |
| `--graphite` | Feature cards, floating panels |
| `--fog` | Secondary text, descriptions, timestamps |
| `--ash` | Borders, dividers, inactive states |
| `--iris` | Announcement bars, links, decorative lines—**the only accent color** |
| `--deep-teal` | Decorative large-area background accents |
| `--canvas` | Page base color |

---

## §5 Shape & Elevation

- Buttons / tags / badges: `border-radius: 100px` (pill shape)
- Cards / images / panels: `border-radius: 8px`
- Icons: `border-radius: 2px`
- **Strict binary system**: only two radius values exist—pill (100px) and square corner (8px)—never mixed
- Borders: `1px solid rgba(1, 1, 16, .08)` (light surfaces) / `rgba(255, 255, 255, .06)` (dark surfaces)
- No shadows—hierarchy is built with borders and surface contrast

---

## §6 Chart & SVG

```css
.chart-bar-primary { fill: var(--obsidian); }
.chart-bar-secondary { fill: var(--ash); }
.chart-line { stroke: var(--obsidian); stroke-width: 2; fill: none; }
.chart-line-accent { stroke: var(--iris); stroke-width: 2; }
.chart-dot { fill: var(--obsidian); }
.chart-grid-line { stroke: rgba(1, 1, 16, .08); stroke-width: 1; }
.chart-label { fill: var(--fog); font-size: 10px; }
.chart-value { fill: var(--obsidian); font-size: 11px; }
```

Charts are primarily Obsidian + Ash greyscale; Iris is used only when a single data series needs emphasis.

---

## §7 Design Principles

1. **Iris Pulse is the only accent**: violet is used only for announcement bars, links, and decorative lines—**never for CTA button fills**.
2. **Display type at weight 400**: ABC Favorit is used at ≥26px, keeping Regular weight + negative tracking, never bolded.
3. **Pill vs. square-corner binary**: buttons/tags at 100px, cards/images at 8px—intermediate values are forbidden.
4. **Near-monochrome tonality**: the overall composition is primarily black/white/grey, with Iris appearing as the sole "breathing color."
5. **No shadows**: hierarchy is built through borders and surface contrast.
6. **Obsidian buttons**: the primary CTA uses an Obsidian fill + Canvas text, not Iris.
7. **Typography as brand**: visual identity is built through type-size hierarchy, whitespace, and negative tracking rather than decorative elements.
8. **Chrome top/bottom bars**: no borders or dividers (transparent, text-only overlay).
