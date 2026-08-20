# Styles · Clean/Natural

A warm, restrained natural aesthetic—serif-driven typographic hierarchy, warm-white base tones, olive-green accents, generous white space, and no decorative elements.
Use together with `../layouts.md` (the pure structural framework).

> This file defines visual tokens and key rules. When generating, define CSS variables and typographic parameters accordingly, while the layout skeleton is still drawn from layouts.md.

---

## CSS Variables

```css
:root {
  --bg: #fafaf8;
  --bg-2: #f4f3f0;
  --surface: #edecea;
  --line: rgba(0,0,0,.06);
  --line-strong: rgba(0,0,0,.12);
  --text: #1a1816;
  --text-2: #5c5650;
  --text-3: #9a928a;
  --accent: #2d4a3e;
  --accent-soft: rgba(45,74,62,.08);
  --serif: 'Cormorant Garamond','Noto Serif SC',Georgia,serif;
  --sans: 'Inter','Noto Sans SC',system-ui,sans-serif;
  --pad-x: clamp(64px, 8vw, 120px);
  --pad-y: clamp(48px, 6vw, 80px);
}
```

---

## Google Fonts

```html
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=Inter:wght@300;400;500&family=Noto+Sans+SC:wght@300;400;500&family=Noto+Serif+SC:wght@300;400;500;600&display=swap" rel="stylesheet">
```

---

## Typography System

| Class | Definition |
|---|---|
| `.h-serif` | Cormorant Garamond, weight 300, `clamp(52px, 7vw, 96px)`, line-height .95, letter-spacing -.02em |
| `.h-2-serif` | weight 400, `clamp(36px, 4.5vw, 64px)`, line-height 1.05 |
| `.h-3-serif` | weight 400, `clamp(28px, 3vw, 42px)`, line-height 1.15 |
| `.label` | sans 11px, letter-spacing .12em, uppercase, text-3 color |
| `.body` | sans 15px, line-height 1.8, text-2 color, max-width 52ch |
| `.body-sm` | sans 13px, line-height 1.7, text-2 color |

**Rules**:
- All headings use the serif font (Cormorant Garamond)
- Body text uses sans (Inter)
- No kicker line decoration—use `.label` instead of `.kicker`
- Emphasized words use `<em>` italic + accent color, rather than bold

---

## Background & Canvas

- Primary background: warm white `#fafaf8` (not pure white)
- Off-canvas background (body): `#f0efec`
- **No ASCII canvas background**—white space itself is the stylistic signature

---

## Cards & Containers

```css
/* Card */
background: var(--bg-2);
border-radius: 16px;
border: none;  /* No border */
padding: 28px;

/* Image container */
border-radius: 12px-16px;
border: none;
overflow: hidden;
```

**Rules**:
- Corner radii are larger than TRAE-work: 16px (cards), 12-16px (images)
- No borders—distinguish layers through background tonal contrast
- Hover effect: `transform: translateY(-3px)`, with no border-color change
- No badge component

---

## Motion

```css
.slide {
  transition: opacity .8s cubic-bezier(.4,0,.2,1), transform .8s cubic-bezier(.4,0,.2,1);
  transform: translateY(8px);
}
.slide.active { opacity: 1; transform: translateY(0); }

/* Stagger: slower and softer */
.slide.active .stagger > * {
  animation: fadeUp .9s cubic-bezier(.25,.8,.25,1) both;
}
/* Child elements get an incrementing delay at 100ms intervals */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
```

**Differences from TRAE-work**:
- Slower animation (.9s vs .7s)
- Smaller displacement (12px vs 18px)
- Wider intervals (100ms vs 70ms)
- Smoother easing (cubic-bezier(.25,.8,.25,1))

---

## Chrome

- Top brand bar (report name on the left + year/label on the right) + bottom page-number bar (series name on the left + page number on the right), consistent with the global rules
- **Chrome top/bottom bars add no borders or divider lines** (transparent, plain text overlay)

```css
.chrome-top, .chrome-bottom {
  position: absolute; left: var(--pad-x); right: var(--pad-x);
  display: flex; align-items: center; justify-content: space-between;
  font-family: var(--sans); font-size: 11px; letter-spacing: .06em;
  color: var(--text-3); z-index: 20; pointer-events: none;
}
.chrome-top { top: 0; padding-top: 20px; }
.chrome-bottom { bottom: 0; padding-bottom: 20px; }
```

> Chrome and nav are `position:absolute` **children of the scaling canvas**, not `position:fixed` — so they track the 1280×720 canvas edges and scale with it. Anchoring them to the viewport with `fixed` makes them float to the window top/bottom and drift out of the slide once the canvas is letterboxed.

---

## Navigation

```css
#nav i { width: 16px; height: 2px; background: var(--line-strong); border-radius: 1px; }
#nav i.active { background: var(--accent); width: 24px; }
```

**Differences from TRAE-work**:
- Navigation bars are smaller (16px vs 22px, active 24px vs 44px)
- No frosted-glass background container
- Bottom dots navigation only, no left/right toggle arrows

---

## Color Rules

1. The accent color is olive green `#2d4a3e` (not purple)
2. All numbers/metrics use the serif font + accent color
3. Large color blocks appear only on the left half of the Closing page
4. Text overlaid on images uses a `linear-gradient(to top, rgba(0,0,0,.5), transparent)` mask

---

## Key Differences vs TRAE-work

| Dimension | TRAE-work | Clean/Natural |
|---|---|---|
| Primary background | pure white `#fff` | warm white `#fafaf8` |
| Accent color | purple `#4B3FE3` | olive green `#2d4a3e` |
| Heading font | Inter (sans) | Cormorant Garamond (serif) |
| Heading weight | 200-300 | 300-400 |
| Card radius | 12px | 16px |
| Card border | 1px solid line | no border |
| Background decoration | ASCII canvas breathing field | none (pure white space) |
| Top chrome | present (mono + dot) | none |
| Kicker style | mono + purple left line | plain label (no decorative line) |
| Animation speed | .7s / 70ms | .9s / 100ms |
| Visual character | tech-forward, SaaS product | editorial, natural and humanistic |
