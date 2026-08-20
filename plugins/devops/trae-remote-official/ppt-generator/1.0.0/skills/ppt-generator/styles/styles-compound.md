# Style · Compound

An editorial minimalist aesthetic built on the Compound Design System—near-total color silence, a single typeface at a single weight, hierarchy established solely through font size and white space, and large-radius pill buttons.

Best for: fintech product intros, SaaS product showcases, minimalist reports, premium brand decks, and editorial content presentations.

---

## §1 CSS Variables

```css
:root {
  --ink: #171717;
  --carbon: #222222;
  --pewter: #5e5e5e;
  --slate: #6f6f6f;
  --ash: #a0a0a0;
  --stone: #c7c7c7;
  --graphite: #e5e7eb;
  --vellum: #f3f3f3;
  --paper: #ffffff;
  --cream-notice: #ffe9bf;

  --font-display: 'Inter', 'General Sans', ui-sans-serif, system-ui, sans-serif;
  --font-body: 'Inter', 'General Sans', ui-sans-serif, system-ui, sans-serif;

  --radius-card: 20px;
  --radius-card-lg: 24px;
  --radius-card-sm: 8px;
  --radius-btn: 9999px;
  --radius-list: 28px;
}
```

Note: The original Compound uses Monument Grotesk; substitute Inter when generating. **Use only weight 400 globally.**

---

## §2 Typography

**Core constraint: a single weight of 400, no bold, no italic.**

| Token | Size | Weight | Line-height | Use |
|---|---|---|---|---|
| `.h-display` | 72px | 400 | 1.0 | Cover main title |
| `.h-1` | 48px | 400 | 1.11 | Page title |
| `.h-2` | 36px | 400 | 1.25 | Section title |
| `.h-3` | 18px | 400 | 1.38 | Card title/subtitle |
| `.lead` | 16px | 400 | 1.5 | Description paragraph |
| `.body` | 14px | 400 | 1.43 | Body text/lists |
| `.kicker` | 12px | 400 | 1.5 | Annotation/label |

Hierarchy is established entirely through differences in font size. **Never use any bold or semi-bold weight.**

---

## §3 Surfaces & Backgrounds

| Scenario | Background | Foreground |
|---|---|---|
| Page canvas | `var(--paper)` #ffffff | `var(--ink)` #171717 |
| Secondary panel/card | `var(--vellum)` #f3f3f3 | `var(--ink)` #171717 |
| Notice/emphasis area | `var(--cream-notice)` #ffe9bf | `var(--ink)` #171717 |
| Chrome | transparent | `var(--slate)` #6f6f6f |

**There is no dark layout.** The entire system uses only light surfaces, establishing hierarchy through the subtle grayscale differences of paper → vellum → graphite.

---

## §4 Color Usage

- **Ink `#171717`**: primary text, filled buttons—the only dark anchor in the system.
- **Pewter / Slate**: secondary text, descriptive notes, metadata.
- **Ash `#a0a0a0`**: tertiary text, placeholders, disabled states.
- **Graphite `#e5e7eb`**: all structural borders and dividers—the most frequently used color in the system.
- **Vellum `#f3f3f3`**: secondary surface fills (card backgrounds).
- **Stone `#c7c7c7`**: decorative fills (used only for SVG graphics/gradients, never for text or borders).
- **Cream Notice `#ffe9bf`**: **the only warm tone in the system**, used extremely sparingly (at most 1-2 instances per deck).
- **Never introduce any saturated color outside of notices/special annotations.**

---

## §5 Shape & Border

- Cards: `border-radius: 20px`
- Large cards/containers: `border-radius: 24px`
- Buttons/pill labels: `border-radius: 9999px` (fully pill-shaped)
- List items: `border-radius: 28px`
- Small cards/input fields: `border-radius: 8px`
- Border: `1px solid var(--graphite)` (#e5e7eb)—light hairline
- **Border color must not be darker than #dbdbdb**
- Shadows are extremely restrained: used only on product-preview cards, with opacity < 0.10
- **No right angles**—every element must have rounded corners
- Chrome top/bottom bars: no borders or divider lines (transparent, plain text overlay)

---

## §6 Chart & SVG

```css
/* Charts are grayscale only; never introduce color */
.chart-bar-primary { fill: var(--ink); }
.chart-bar-secondary { fill: var(--stone); }
.chart-bar-tertiary { fill: var(--graphite); }
.chart-line { stroke: var(--ink); stroke-width: 2; fill: none; }
.chart-line-secondary { stroke: var(--stone); stroke-width: 1.5; }
.chart-dot { fill: var(--ink); }
.chart-area { fill: var(--ink); opacity: 0.04; }
.chart-grid-line { stroke: var(--graphite); stroke-width: 1; }
.chart-label { fill: var(--slate); font-size: 10px; }
.chart-value { fill: var(--ink); font-size: 10px; }
```

---

## §7 Design Principles

1. **Color silence**: grayscale tones only; the sole warm tone, Cream Notice, is used extremely sparingly.
2. **Single weight**: all text uses only 400; hierarchy is built through font-size differences and white space. No bold.
3. **Large radius**: cards at 20px, buttons as pills (9999px); no right angles.
4. **Restrained shadows**: opacity no higher than 0.10, and most elements have no shadow at all.
5. **Pure white primary tone**: no dark layout. An overall white/light-gray tonality that conveys refinement through subtraction.
6. **Abundant white space**: block spacing ≥ 80px, giving elements ample breathing room.
7. **Center-first**: cover and Think page titles are center-aligned, creating an editorial, print-like feel.
8. **Image style**: image pages favor product screenshots or abstract graphics; choose images with solid-color backgrounds/minimalist compositions, avoiding lifestyle photography.
