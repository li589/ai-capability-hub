# Panel Mode Rules

Panel mode renders large, complex visuals in a dedicated Webview Panel. Content can scroll, contain multiple sections, and support rich interactions — no height cap.

## Streaming Output Order (Hard Rule)

Output streams token-by-token. **Structure code so styles load BEFORE content:**

1. **`<style>` block FIRST** — all CSS rules at the top, before any HTML content.
2. **HTML content SECOND** — with styles already parsed, elements render correctly immediately.
3. **`<script>` block LAST** — scripts never block visual rendering.

This prevents the "flash of unstyled content" during streaming. Never put `<style>` after HTML content.

## Key Differences from Inline

- No height limit — supports vertical scrolling.
- Multi-section page structure allowed (header / main / sidebar / footer).
- Complex scripts allowed (ECharts, D3, drag-and-drop, etc.).
- `<style>` blocks have no line limit.
- Page-level layout patterns (grid, flexbox columns) encouraged.

## Still Required (Shared Rules)

- Use framework CSS variables for all colors (auto theme adaptation).
- Background transparent — framework shell provides the base color.
- sendPrompt() is available for "ask AI to process this" interactions.
- CDN allowlist still enforced (CSP).
- **No DOCTYPE, `<html>`, `<head>`, or `<body>`** — framework shell wraps the content.
- Dark mode must work.

## Page Structure

Panel content should follow a clear section hierarchy:

```html
<!-- Header area -->
<div class="panel-header">
  <h1>Title</h1>
  <p class="subtitle">Subtitle or description</p>
</div>

<!-- Main content sections -->
<section class="panel-section">
  <h2>Section heading</h2>
  <!-- Section content -->
</section>

<!-- Repeat sections as needed -->
```

## Layout Patterns

Pick the closest pattern for your content:

**Report**: Title bar → KPI metric grid → chart area → event timeline → summary
- Best for: weekly reports, project status, post-mortems

**Comparison**: Title → side-by-side card grid → summary table → recommendation
- Best for: tech selection, proposal review, A/B analysis

**Dashboard**: Filter bar → multi-chart grid (2×2 or 3-col) → detail table
- Best for: monitoring overview, analytics, metrics deep-dive

**Timeline**: Title → vertical timeline with event cards → milestones
- Best for: project history, incident timeline, changelog

**Kanban**: Column headers → draggable cards in columns → status summary
- Best for: task management, workflow stages, content pipeline

## Visual Specifications

- Container: `max-width: 960px; margin: 0 auto; padding: 32px 24px`
- Cards: white bg + `1px solid var(--color-border-tertiary)` + `border-radius: var(--border-radius-lg)` + `padding: 1.25rem`
- Section gap: 32px (use `gap` or `margin-bottom`)
- Typography: h1=24px/600, h2=18px/600, h3=16px/500, body=14px/400
- Dividers: `1px solid var(--color-border-tertiary)`
- KPI numbers: 28px/600, labels: 13px/400 muted

## Interaction Rules

### Event Binding (Critical)

**Never bind the same event on an element twice.** Pick ONE approach:
- `onclick` attribute on the HTML element (no `<script>` listener for that element), OR
- `addEventListener` inside a `<script>` block (no `onclick` attribute on that element).

Why: The rendering engine injects HTML via `innerHTML` then separately extracts and re-executes `<script>` blocks. If you use BOTH `onclick` AND `addEventListener` on the same element, the handler fires twice — e.g., `classList.toggle('open')` toggles on then immediately off, producing zero visible effect.

```html
<!-- ✅ CORRECT — addEventListener only, no onclick attribute -->
<div class="file-header">Click to expand</div>
<script>
(function() {
  var headers = document.querySelectorAll('.file-header');
  for (var i = 0; i < headers.length; i++) {
    headers[i].addEventListener('click', function() {
      this.parentElement.classList.toggle('open');
    });
  }
})();
</script>

<!-- ✅ ALSO CORRECT — onclick only, no script listener for same element -->
<div class="file-header" onclick="this.parentElement.classList.toggle('open')">

<!-- ❌ WRONG — BOTH onclick AND addEventListener on the same element -->
<div class="file-header" onclick="this.parentElement.classList.toggle('open')">
<script>
document.querySelector('.file-header').addEventListener('click', function() {
  this.parentElement.classList.toggle('open'); // fires AGAIN → cancels out!
});
</script>
```

Recommendation:
- Prefer `addEventListener` in a `<script>` block (cleaner separation).
- Use ES5 syntax (`var`, `function`, `for` loops) for maximum compatibility.
- Wrap script content in an IIFE `(function(){ ... })();` to avoid global scope pollution.

### General

- Editor-type panels **must** include an "Export" button.
- Export via clipboard (`navigator.clipboard.writeText`) or file download (`Blob` + `URL.createObjectURL`).
- sendPrompt(text) is for "let AI continue processing" only (e.g., "help me refine this"), NOT for export.
- Complex interactions (drag, sort, filter) implemented in `<script>`.
- Charts: prefer ECharts for rich chart types and responsive resize.

## Preview Behavior

When mode="panel", the chat flow shows:
- A height-limited thumbnail preview of the content.
- An "Open in panel" button.
- Clicking the button opens the full content in a dedicated Webview Panel (same sandbox framework, no height cap).
