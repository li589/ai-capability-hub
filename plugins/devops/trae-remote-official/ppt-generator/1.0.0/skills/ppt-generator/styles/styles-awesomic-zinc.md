# Style · Awesomic Zinc

A neutral zinc-gray aesthetic built on the Awesomic Design System—gray canvas with large-radius cards, 1px hairline borders, functional orange accents, and the geometric sans-serif DM Sans.

Best for: design-service/agency showcases, product feature walkthroughs, team collaboration reports, and neutral, soft-toned decks.

---

## §1 CSS Variables

```css
:root {
  --bg: #f4f4f5;
  --bg-2: #ffffff;
  --surface: #fafafa;
  --line: #ececee;
  --line-strong: #d4d4d8;
  --text: #09090b;
  --text-2: #52525b;
  --text-3: #71717a;
  --accent: #ff5a00;
  --accent-2: #fe45e2;
  --accent-soft: rgba(255, 90, 0, .08);
  --link: #ff5a00;

  --font-sans: 'DM Sans', 'Inter', 'Noto Sans SC', ui-sans-serif, system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;

  --radius-card: 36px;
  --radius-btn: 14px;
  --radius-badge: 12px;
}
```

---

## §2 Typography

```css
.h-display { font-size: clamp(52px, 7.8vw, 112px); font-weight: 700; line-height: 1.12; letter-spacing: normal; }
.h-1 { font-size: clamp(32px, 5vw, 48px); font-weight: 700; line-height: 1.28; letter-spacing: normal; }
.h-2 { font-size: clamp(20px, 2.8vw, 32px); font-weight: 600; line-height: 1.35; }
.lead { font-size: 15px; font-weight: 400; line-height: 1.5; color: var(--text-2); }
.body { font-size: 15px; font-weight: 400; line-height: 1.5; color: var(--text-2); }
.kicker { font-size: 12px; font-weight: 500; letter-spacing: 0.03em; text-transform: uppercase; color: var(--text-2); }
.kicker::before { content: ""; width: 24px; height: 3px; background: var(--accent); border-radius: 2px; }
```

Use DM Sans (geometric sans-serif) globally, with only two weights: 400 (body) and 600/700 (headings). Pair with Noto Sans SC for Chinese.

---

## §3 Backgrounds & Surfaces

| Scenario | Background | Foreground |
|---|---|---|
| Page canvas | `var(--bg)` #f4f4f5 | `var(--text)` #09090b |
| Highlight card surface | `var(--bg-2)` #ffffff | `var(--text)` #09090b |
| Secondary panel | `var(--surface)` #fafafa | `var(--text-2)` #52525b |
| Dark layout (cover/Think) | `var(--text)` #09090b | `var(--bg-2)` #ffffff |
| Chrome | transparent | `var(--text-2)` #52525b |

**The canvas base color is #f4f4f5 (zinc gray), not pure white.** #fff is reserved for highlight card surfaces only.

---

## §4 Color Usage

- **Accent Orange `#ff5a00`**: functional accent—marker lines, kicker decorative bars, badges, active-state indicators. **Never use for large fills.**
- **Accent Pink `#fe45e2`**: secondary decorative color, used very sparingly (chart secondary color or gradient endpoint).
- **Text `#09090b`**: main headings, primary button fills.
- **Text-2 `#52525b`**: body text, descriptions.
- **Text-3 `#71717a`**: supporting information, Chrome text.
- **Line `#ececee`**: thin borders, divider lines.
- **Line-strong `#d4d4d8`**: emphasis borders, navigation dots.

---

## §5 Shape & Border

- Cards/large panels: `border-radius: 36px` (extra-large radius)
- Buttons/input fields: `border-radius: 14px`
- Badge/Tag: `border-radius: 12px`
- Border: `1px solid var(--line)` — uniform hairline
- **No thick borders** (≥2px)
- Navigation arrow buttons: 14px rounded rectangles (**not circles**)
- Establish hierarchy through borders + background tonal contrast
- The only permitted shadow: hover state `0 4px 12px rgba(0,0,0,.04)`

---

## §6 Chart & SVG

```css
.chart-bar-primary { fill: var(--text); }
.chart-bar-secondary { fill: var(--line-strong); }
.chart-bar-accent { fill: var(--accent); }
.chart-line { stroke: var(--text); stroke-width: 2; fill: none; }
.chart-line-accent { stroke: var(--accent); stroke-width: 2; }
.chart-dot { fill: var(--text); }
.chart-grid-line { stroke: var(--line); stroke-width: 1; }
.chart-label { fill: var(--text-3); font-size: 10px; }
.chart-value { fill: var(--text); font-size: 11px; font-weight: 600; }
```

---

## §7 Design Principles

1. **Zinc-gray canvas**: base color is #f4f4f5, not pure white. #fff is reserved for highlight card surfaces only.
2. **Extra-large radius**: cards at 36px convey a soft, approachable feel. Buttons at 14px.
3. **Functional accent usage**: #ff5a00 is used only for marker lines/badges/active states, never for large fills.
4. **Hairline borders**: 1px hairline throughout the system; thick borders are forbidden.
5. **No shadows for hierarchy**: establish layering through borders + background tonal contrast.
6. **Kicker decorative bar**: a 24px × 3px accent-colored bar precedes the kicker.
7. **Sans-serif/no handwritten fonts**: only DM Sans, with Noto Sans SC for Chinese.
8. **Chrome top/bottom bars**: no borders or divider lines (transparent, plain text overlay).
8. **Non-negative letter-spacing**: keep it at normal or positive values.
9. **Hover feedback**: on card hover, border-color shifts to the accent or a subtle shadow appears.
10. **No decorative backgrounds**: no ASCII patterns, no textures, no gradient base colors.
