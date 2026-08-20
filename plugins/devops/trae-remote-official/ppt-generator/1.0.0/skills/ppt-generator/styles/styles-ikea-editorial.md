# Style · IKEA Editorial

Built on the IKEA editorial visual system—high-contrast flat design, functional yellow accents, binary Inter weights, uniform 8px corner radius, and a rigid grid.

Best for: retail/e-commerce product showcases, brand manifestos, feature lists, and headline-driven decks.

---

## §1 CSS Variables

```css
:root {
  --bg: #ffffff;
  --bg-2: #fffefb;
  --surface: #fffefb;
  --line: #111111;
  --line-strong: #111111;
  --text: #111111;
  --text-2: #818181;
  --text-3: #818181;
  --accent: #ffdb00;
  --accent-2: #e6c600;
  --accent-soft: rgba(255, 219, 0, .12);
  --link: #0159a3;

  --font-sans: 'Inter', 'DM Sans', 'Noto Sans SC', ui-sans-serif, system-ui, sans-serif;

  --radius: 8px;
}
```

---

## §2 Typography

```css
.h-display { font-size: clamp(56px, 8.4vw, 132px); font-weight: 700; line-height: 1; letter-spacing: -1.48px; }
.h-1 { font-size: clamp(36px, 5.6vw, 51px); font-weight: 700; line-height: 1.08; letter-spacing: -0.97px; }
.h-2 { font-size: clamp(20px, 3vw, 36px); font-weight: 700; line-height: 1.2; letter-spacing: -0.54px; }
.lead { font-size: 16px; font-weight: 400; line-height: 1.57; color: var(--text-2); }
.body { font-size: 16px; font-weight: 400; line-height: 1.57; color: var(--text-2); }
.kicker { font-size: 13px; font-weight: 700; letter-spacing: 0.02em; text-transform: uppercase; color: var(--text); }
.kicker::before { content: ""; width: 28px; height: 3px; background: var(--accent); }
```

Only two weights: 400 (body) and 700 (headings)—never introduce a third. Display-level text must use negative letter-spacing.

---

## §3 Backgrounds & Surfaces

| Scenario | Background | Foreground |
|---|---|---|
| Page canvas | `var(--bg)` #ffffff | `var(--text)` #111111 |
| Card/panel | `var(--bg-2)` #fffefb | `var(--text)` #111111 |
| Accent surface (CTA/special block) | `var(--accent)` #ffdb00 | `var(--text)` #111111 |
| Dark layout (cover/Think) | `var(--text)` #111111 | `var(--bg)` #ffffff |
| Chrome | transparent | `var(--text)` #111111 |

The Chrome top-bar brand mark includes an 8px circular accent-colored dot.

---

## §4 Color Usage

- **Accent Yellow `#ffdb00`**: CTA button fills, kicker decorative bars, hover feedback color. Functional use only, never as a large canvas fill.
- **Text `#111111`**: main headings, body text, Chrome text, dark panel backgrounds—the only black in the system.
- **Text-2 `#818181`**: description text, supporting information.
- **Link Blue `#0159a3`**: used only for text links, **never for buttons/CTAs**.
- **Line `#111111`**: dividers use pure black (2px) for a hard-edged look.

---

## §5 Shape & Border

- **The system's single corner radius: 8px** — used uniformly for cards, buttons, images, and badges
- Border: hard-edged black dividers (`2px solid var(--line)` or row-level `height: 2px`)
- Navigation arrows: 50% circular black buttons that turn accent yellow on hover
- **No shadows**: zero box-shadow, zero elevation; hierarchy is achieved through color contrast and spacing
- Navigation dot container: `border-radius: 20px`, semi-transparent white background + 1px border

---

## §6 Chart & SVG

```css
.chart-bar-primary { fill: var(--text); }
.chart-bar-secondary { fill: var(--text-2); }
.chart-bar-accent { fill: var(--accent); }
.chart-line { stroke: var(--text); stroke-width: 2; fill: none; }
.chart-line-accent { stroke: var(--accent); stroke-width: 2.5; }
.chart-dot { fill: var(--text); }
.chart-grid-line { stroke: var(--text-2); stroke-width: 1; opacity: 0.2; }
.chart-label { fill: var(--text-2); font-size: 10px; }
.chart-value { fill: var(--text); font-size: 11px; font-weight: 700; }
```

---

## §7 Design Principles

1. **High contrast**: pure black #111 headings + white background, delivering direct, forceful visual impact.
2. **Functional yellow**: #ffdb00 is used only for CTAs/markers/hover feedback, never as a large canvas fill.
3. **Uniform 8px radius**: the system's single corner radius, with no exceptions.
4. **Two weights**: only 400 and 700; 300/500/600 are not allowed.
5. **Zero shadows**: all hierarchy is achieved through color contrast and spacing.
6. **Negative letter-spacing**: display-level headings must use negative letter-spacing to create condensed power.
7. **Blue for links only**: #0159a3 is used only for text links; buttons/CTAs use only yellow or black.
8. **Chrome top/bottom bars**: no borders or divider lines (transparent, plain text overlay).
8. **No gradients**: surfaces allow solid fills only (white/#fffefb/yellow/black).
9. **Hover feedback**: on card hover, the background turns yellow or a displacement feedback occurs.
10. **Text over images requires an overlay**: never place text directly on an image; first add a gradient-to-black overlay (30-60% opacity).
