# Inline Mode Rules

Inline mode renders compact visuals embedded directly in the chat response. Content appears alongside the AI's text, so it must be concise and streaming-friendly.

## Hard Limits

- No DOCTYPE, `<html>`, `<head>`, or `<body>` — content fragments only.
- Height is auto-fit but the host enforces a MAX_HEIGHT cap.
- Single SVG or compact HTML fragment per tool call.
- `<style>` blocks ≤15 lines. Prefer inline `style="..."`.
- No nested scrolling — content must fit without scroll.
- No `position: fixed`.
- No tabs, carousels, or `display: none` (not streaming-friendly).

## Complexity Budget

- SVG: ≤5 nodes per diagram, viewBox 680px fixed width.
- Horizontal tier: ≤4 boxes at full width (~140px each). 5+ boxes → shrink to ≤110px OR wrap to 2 rows OR split into overview + detail.
- Colors: ≤2 color ramps per diagram. If colors encode meaning, add a 1-line legend.
- Scripts: tail-loaded only, CDN allowlist applies. **Never bind the same event twice** (onclick + addEventListener on same element causes double-fire).
- Box subtitles: ≤5 words. Detail goes in sendPrompt or prose — not the box.

## Streaming Output Order (Hard Rule)

Output streams token-by-token. **Structure code so styles load BEFORE content:**

- **HTML order**: `<style>` FIRST → content HTML → `<script>` LAST. Never reverse this.
- **SVG order**: `<defs>` (markers) → visual elements immediately.
- Prefer inline `style="..."` over `<style>` blocks for inline mode (keeps style closer to element).
- Gradients, shadows, and blur flash during streaming DOM diffs. Use solid flat fills.
- No `display:none` toggling — elements should render progressively.

**Why**: Streaming means user sees partial output. If styles come after content, user sees unstyled flash — unacceptable.

## Output Principles

- Text explanation goes OUTSIDE the tool call, in your response text.
- The tool output contains ONLY the visual element.
- Background must be transparent — host provides the background color.
- The widget container is `display: block; width: 100%`. No wrapper div needed.

## UI Components

**Tokens**: Borders = `0.5px solid var(--color-border-tertiary)`. Cards = white bg, 0.5px border, border-radius-lg, padding 1rem 1.25rem. Buttons: transparent bg, 0.5px border, sendPrompt gets ↗ arrow.

**Metric cards**: muted 13px label, 24px/500 number. bg-base-secondary, no border, radius-md, padding 1rem. Grid of 2-4.

**Layout**: Editorial = no card wrapper. Card = single raised card. No tables in tool output.

**Round every displayed number** — use Math.round(), .toFixed(n), or Intl.NumberFormat.

**Corners**: `border-radius: var(--border-radius-md)` (or `--border-radius-lg` for cards) in HTML. In SVG, `rx="4"` default. No rounded corners on single-sided borders.

**Icon sizing**: emoji=16px, SVG icons=16px×16px. Decorative icons 24px max.

## Modules

After loading inline mode, pick the closest sub-module:

- **diagram** — SVG flowcharts, structural diagrams, illustrative diagrams
- **mockup** — UI mockups, forms, cards, dashboards
- **interactive** — interactive explainers with controls
- **chart** — charts, data analysis, geographic maps (Chart.js, D3)
- **art** — illustration and generative art

## Compare Options

Side-by-side card grid. Recommended option gets 2px info border + badge.

## Data Record

Single raised card. Avatar/initials circle for people.

## Mockup Presentation

Contained mockups need background surface. Full-width mockups don't.
