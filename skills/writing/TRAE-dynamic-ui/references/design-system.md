# Shared Design System

All visual output — inline or panel — shares this design foundation.

## Philosophy

- **Seamless**: Integrate visually with the IDE — match its rhythm, not fight it.
- **Expressive**: Use color boldly to encode meaning, create hierarchy, and make information scannable. Flat ≠ boring.
- **Compact**: Show the essential visually. Explain the rest in text.
- **Separation**: Text goes in your response, visuals go in the tool — all explanatory text, descriptions, introductions, and summaries must be written as normal response text OUTSIDE the tool call. The tool output should contain ONLY the visual element.

## Visual Richness — Be Bold With Color

**Default is colorful, not monochrome.** A widget that is entirely black-white-gray is visually dead. Always apply at least one accent color.

### Default Accent

When you need a general-purpose accent (links, highlights, primary actions, active states), use **sky** (`--color-sky-*`). It is neutral, professional, and works in both light/dark modes.

For secondary accent, pair with **indigo** or **violet**.

### Color Usage Patterns (apply these actively)

- **KPI / hero numbers**: Use accent color (sky-60 or indigo-60) for the number, secondary text for the label
- **Section eyebrows**: 11px monospace uppercase labels above headings — use `--color-text-tertiary` or a muted accent
- **Card left accent bar**: A 3-4px colored left border on cards to indicate category (`border-left: 3px solid var(--color-sky-5)`)
- **Status indicators**: green=success, amber=warning, coral=error — use filled dots or pill badges with light fill + strong text
- **Flow/architecture nodes**: Each layer/category gets its own color ramp. Never make all nodes the same gray.
- **Interactive hover**: Background shifts from transparent to `--color-background-overlay-l2` with accent border
- **Progress / metrics**: Use colored bars, not just numbers. A horizontal bar in sky/mint/amber instantly communicates magnitude.
- **Tables**: Alternate row backgrounds using `--color-background-overlay-l1`. Header row uses subtle accent background.
- **Tags / badges / pills**: Light fill (ramp-10) + strong text (ramp-70). e.g. `background: var(--color-sky-1); color: var(--color-sky-7)`

### Allowed Visual Embellishments

You ARE encouraged to use:
- Subtle `box-shadow` for elevated cards: `var(--shadow-sm)` or `var(--shadow-md)`
- Colored left/top borders on cards and sections
- Dot/circle decorative elements for timelines and step indicators
- Animated transitions on hover/click (transform, opacity, background-color)
- Colored icon badges (small colored circles behind icons)

### What Still Not To Do

- **No gradient backgrounds** — no `linear-gradient`, `radial-gradient`, or any multi-color gradient fills on containers, headers, or hero sections. Backgrounds must be flat solid colors using CSS variables.
- No neon glow, no heavy drop shadows, no 3D effects
- No full-bleed colored backgrounds (the host provides outer bg)
- No mesh/noise texture images
- No multiple competing saturated colors fighting for attention (pick 1 primary + 1 secondary accent)

## CSS Variables

**Backgrounds**: `--color-background-primary` (white), `-secondary` (surfaces), `-tertiary` (page bg), `-info`, `-danger`, `-success`, `-warning`

**Text**: `--color-text-primary` (black), `-secondary` (muted), `-tertiary` (hints), `-info`, `-danger`, `-success`, `-warning`

**Borders**: `--color-border-tertiary` (0.15α, default), `-secondary` (0.3α, hover), `-primary` (0.4α), semantic `-info/-danger/-success/-warning`

**Typography**: `--font-sans`, `--font-serif`, `--font-mono`

**Layout**: `--border-radius-md` (8px), `--border-radius-lg` (10px), `--border-radius-xl` (12px)

All auto-adapt to light/dark mode.

## Color Palette

10 color ramps, 10 stops each. Use them generously — they exist to be used, not admired in a table.

| Ramp | Purpose suggestion | Light fill | Strong accent | Text on fill |
|------|-------------------|-----------|---------------|-------------|
| coral | Error, alerts, hot metrics | 1-2 | 6-7 | 8-9 |
| amber | Warnings, in-progress, medium priority | 1-2 | 6-7 | 8-9 |
| lime | Success secondary, growth, positive delta | 1-2 | 6-7 | 8-9 |
| mint | Success primary, complete, healthy | 1-2 | 6-7 | 8-9 |
| teal | Info secondary, data, neutral-positive | 1-2 | 6-7 | 8-9 |
| sky | **Primary accent**, links, active, info | 1-2 | 5-6 | 7-8 |
| indigo | **Secondary accent**, special, premium | 1-2 | 5-6 | 7-8 |
| violet | Creative, AI-related, unique | 1-2 | 5-6 | 7-8 |
| magenta | Attention, new, promotional | 1-2 | 6-7 | 8-9 |
| slate | Neutral, structural, disabled | 1-2 | 6-7 | 8-9 |

Full hex values (Open Color based; 1=lightest near-white, 10=darkest):

| Class | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|-------|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| c-coral | #fff5f5 | #ffe3e3 | #ffc9c9 | #ffa8a8 | #ff8787 | #ff6b6b | #fa5252 | #f03e3e | #e03131 | #c92a2a |
| c-amber | #fff9db | #fff3bf | #ffec99 | #ffe066 | #ffd43b | #fcc419 | #fab005 | #f59f00 | #f08c00 | #e67700 |
| c-lime | #f4fce3 | #e9fac8 | #d8f5a2 | #c0eb75 | #a9e34b | #94d82d | #82c91e | #74b816 | #66a80f | #5c940d |
| c-mint | #e6fcf5 | #c3fae8 | #96f2d7 | #63e6be | #38d9a9 | #20c997 | #12b886 | #0ca678 | #099268 | #087f5b |
| c-teal | #e6fcfc | #c3fafa | #96f2f2 | #63e6e6 | #38d9d9 | #20c9c9 | #12b8b8 | #0ca6a6 | #099292 | #087f7f |
| c-sky | #e7f5ff | #d0ebff | #a5d8ff | #74c0fc | #4dabf7 | #339af0 | #228be6 | #1c7ed6 | #1971c2 | #1864ab |
| c-indigo | #edf2ff | #dbe4ff | #bac8ff | #91a7ff | #748ffc | #5c7cfa | #4c6ef5 | #4263eb | #3b5bdb | #364fc7 |
| c-violet | #f3f0ff | #e5dbff | #d0bfff | #b197fc | #9775fa | #845ef7 | #7950f2 | #7048e8 | #6741d9 | #5f3dc4 |
| c-magenta | #fff0f6 | #ffdeeb | #fcc2d7 | #faa2c1 | #f783ac | #f06595 | #e64980 | #d6336c | #c2255c | #a61e4d |
| c-slate | #f8f9fa | #f1f3f5 | #e9ecef | #dee2e6 | #ced4da | #adb5bd | #868e96 | #495057 | #343a40 | #212529 |

**Quick rules**:
- Every widget MUST use at least 1 non-gray color ramp
- Group related items by color; different categories = different ramps
- Light mode: 1-2 fill + 6 stroke + 8 title text
- Dark mode: 8 fill + 2 stroke + 1 title text
- Text on colored fills: use same ramp 8-9 (light) or 1-2 (dark). Never plain black/gray.

**Color assignment**: Encode meaning, not sequence. Group by category. Use gray for neutral/structural only — never as the sole color.

## SVG Pre-built Classes

- `class="t"` = sans 14px primary text
- `class="ts"` = sans 12px secondary text
- `class="th"` = sans 14px medium(500) heading text
- `class="box"` = neutral rect
- `class="node"` = clickable group
- `class="arr"` = arrow line
- `class="leader"` = dashed leader line
- `class="c-{ramp}"` = colored node (c-sky, c-teal, etc). Apply to `<g>` or shape, NOT paths.

## sendPrompt(text)

A global function that sends a message to chat as if the user typed it. Use for follow-up questions, not for data export.

## Dark Mode

Dark mode is mandatory — every color must work in both modes:

- In SVG: use pre-built color classes (`c-sky`, `c-teal`, `c-amber`, etc.) for colored nodes.
- In SVG: every `<text>` needs a class (`t`, `ts`, `th`).
- In HTML: always use CSS variables for text. Never hardcode colors.

## Typography

- Two weights only: 400 regular, 600 bold.
- h1=18px, h2=16px, h3=14px, body=14px. Never use 700.
- **Sentence case** always. Never Title Case, never ALL CAPS (except eyebrow labels).
- No mid-sentence bolding. Entity names go in code style, not bold.
- font-sans / font-serif / font-mono via CSS variables.
- Use `--font-serif` for hero/page titles in panel mode to create visual distinction.
- Use `--font-mono` at 11px with letter-spacing 0.06em for eyebrow labels, category tags, and metadata.

## Visual Signature Elements

These recurring patterns give our widgets a cohesive, recognizable look. Use them:

### Eyebrow Labels
Small monospace uppercase text above section headings — our signature rhythm marker:
```css
.eyebrow {
  font-family: var(--font-mono);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-tertiary);
  margin-bottom: 6px;
}
```

### Accent Bars
Colored left borders on cards to signal category:
```css
.card-accent { border-left: 3px solid var(--color-sky-5); }
.card-accent-warn { border-left: 3px solid var(--color-amber-5); }
.card-accent-error { border-left: 3px solid var(--color-coral-5); }
```

### Status Pills
Compact colored badges:
```css
.pill { display: inline-flex; padding: 2px 8px; border-radius: var(--border-radius-full); font-size: 11px; font-weight: 600; }
.pill-success { background: var(--color-mint-1); color: var(--color-mint-7); }
.pill-warning { background: var(--color-amber-1); color: var(--color-amber-7); }
.pill-error { background: var(--color-coral-1); color: var(--color-coral-7); }
.pill-info { background: var(--color-sky-1); color: var(--color-sky-7); }
```

### Metric Cards
Numbers that pop:
```css
.metric-value { font-size: 28px; font-weight: 600; color: var(--color-sky-6); line-height: 1.1; }
.metric-label { font-size: 12px; color: var(--color-text-secondary); margin-top: 4px; }
.metric-delta-up { color: var(--color-mint-6); }
.metric-delta-down { color: var(--color-coral-6); }
```

## Universal Prohibitions

- No emoji — use CSS shapes or SVG paths
- No neon glow, heavy drop shadows, blur filters, or 3D perspective effects
- No dark/colored backgrounds on the outermost container (transparent only — host provides the bg)
- No `position: fixed`
- No hardcoded colors (use CSS variables or palette classes)
- No `font-size` below 11px
- No comments in output (waste tokens, break streaming)
- **CDN allowlist (CSP-enforced)**: `cdnjs.cloudflare.com`, `esm.sh`, `cdn.jsdelivr.net`, `unpkg.com` only.
