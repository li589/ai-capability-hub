# Style · Linear

A dark, precision-instrument visual system based on Linear—near-black canvas, Acid Lime fluorescent accents, precise Inter Variable typography, hairline-border hierarchy, and a low-saturation cool-grey scale.

Best for: developer tools, project management, technical product demos, dark-themed decks, and geek-style reports.

---

## §1 CSS Variables

```css
:root {
  --acid-lime: #e4f222;
  --pulse-green: #27a644;
  --coral-red: #eb5757;
  --signal-teal: #02b8cc;
  --iris-violet: #6366f1;

  --void: #08090a;
  --carbon: #0f1011;
  --obsidian: #161718;
  --graphite: #23252a;
  --smoke: #383b3f;
  --ash: #62666d;
  --fog: #8a8f98;
  --mist: #d0d6e0;
  --bone: #e5e5e6;
  --paper: #ffffff;

  --font-display: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'Berkeley Mono', 'JetBrains Mono', monospace;

  --radius-card: 12px;
  --radius-btn: 6px;
  --radius-pill: 9999px;
}
```

---

## §2 Typography

| Token | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|
| `.h-display` | 72px | 590 | 0.96 | -0.022em | Cover main title |
| `.h-1` | 48px | 590 | 1.04 | -0.022em | Page title |
| `.h-2` | 32px | 560 | 1.15 | -0.015em | Section heading |
| `.h-3` | 22px | 560 | 1.25 | -0.01em | Card title |
| `.lead` | 18px | 400 | 1.6 | 0 | Description paragraph |
| `.body` | 16px | 400 | 1.5 | 0 | Body text / lists |
| `.kicker` | 12px | 500 | 1 | 0.04em | Uppercase label / tag |
| `.mono` | 13px | 450 | 1.5 | 0 | Code / data |

Use Inter Variable throughout, with `font-feature-settings: 'cv01', 'ss03', 'zero'` enabled. Headings are Semi-bold (560-590), body text is Regular (400).

---

## §3 Surfaces & Backgrounds

| Scene | Background | Foreground |
|---|---|---|
| Main canvas | `var(--void)` #08090a | `var(--mist)` #d0d6e0 |
| Card / panel | `var(--carbon)` #0f1011 | `var(--bone)` #e5e5e6 |
| Elevated panel | `var(--obsidian)` #161718 | `var(--paper)` #ffffff |
| Chrome top/bottom bar | transparent | `var(--fog)` #8a8f98 |
| Light contrast page (optional) | `var(--paper)` #ffffff | `var(--void)` #08090a |

**Full dark mode is the default.** The foreground never uses pure white—the brightest is Mist/Bone.

---

## §4 Color Usage

- **Acid Lime `#e4f222`**: the core accent—CTA button fills, kickers, key data highlights. 1-2 uses per page; overuse destroys the precision feel.
- **Pulse Green `#27a644`**: positive metrics, growth data.
- **Coral Red `#eb5757`**: warnings / declining metrics.
- **Signal Teal `#02b8cc`**: informational / link secondary color.
- **Iris Violet `#6366f1`**: secondary accent / chart colors.
- **Neutral grey scale (Void → Paper)**: builds the overall hierarchy while keeping low-contrast reading comfort.

---

## §5 Shape & Border

- Cards / panels: `border-radius: 12px`
- Buttons / inputs: `border-radius: 6px`
- Pills / tags: `border-radius: 9999px`
- Borders: `0.5px solid var(--graphite)` or `0.5px solid var(--smoke)` — hairline-level thin borders
- No drop shadow (zero box-shadow); hierarchy relies solely on background contrast + hairline borders
- Optional inner shadow: `inset 0 0 0 0.5px rgba(255,255,255,0.06)` for floating layers
- Chrome top/bottom bars: no borders or dividers (transparent, text-only overlay)

---

## §6 Chart & SVG

```css
.chart-line { stroke: var(--acid-lime); stroke-width: 2; fill: none; }
.chart-line-secondary { stroke: var(--fog); stroke-width: 1.5; }
.chart-line-tertiary { stroke: var(--iris-violet); stroke-width: 1.5; }
.chart-bar-primary { fill: var(--acid-lime); }
.chart-bar-secondary { fill: var(--smoke); }
.chart-dot { fill: var(--acid-lime); }
.chart-grid-line { stroke: var(--graphite); stroke-width: 0.5; }
.chart-label { fill: var(--fog); font-size: 10px; }
.chart-value { fill: var(--mist); font-size: 10px; font-weight: 560; }
.chart-area { fill: var(--acid-lime); opacity: 0.08; }
```

---

## §7 Design Principles

1. **Dark first**: an all-dark base with the brightest foreground at Mist/Bone, preserving low-contrast reading comfort.
2. **Restrained fluorescence**: Acid Lime for only 1-2 key emphases. Overuse destroys the precision feel.
3. **Hairline borders**: 0.5px thin borders replace shadows, expressing a precision-engineering temperament.
4. **Precise weights**: headings at 560-590 (not conventional Bold), body at 400, avoiding a clumsy heaviness.
5. **Developer aesthetic**: use monospace fonts (Berkeley Mono / JetBrains Mono) judiciously as data ornamentation.
6. **Information density**: convey hierarchy through carefully tuned greyscale levels rather than size contrast.
