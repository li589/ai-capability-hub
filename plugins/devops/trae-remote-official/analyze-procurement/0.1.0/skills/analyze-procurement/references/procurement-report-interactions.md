# Procurement report interaction runtime

Use the bundled runtime only when the chosen architecture calls for a scroll-snap shelf, switch card, tabs, master/detail comparison, question-help popover, or linked entity highlighting. Do not copy it into a static report that does not need interaction.

## Contents

1. Files
2. Chart-runtime boundary
3. Report navigation
4. Scroll-snap shelf
5. Hover/focus switch card
6. Scenario tabs
7. Master/detail comparison
8. Question-help popover
9. Enhanced comparison table
10. Linked entity highlighting
11. Requirements

## Files

- `assets/procurement-report-ui/procurement-report-ui.css`
- `assets/procurement-report-ui/procurement-report-ui.js`

Copy only the files the report uses into the report-local `assets/` directory and reference them with relative paths. The optional stylesheet consumes the built-in renderer's `--bg`, `--bg2`, `--ink`, `--muted`, `--rule`, `--accent`, and `--accent2` variables; it never defines a root palette.

```html
<link rel="stylesheet" href="assets/procurement-report-ui.css">
...
<script src="./_shared/js/echarts.min.js"></script>
<script src="assets/charts.js"></script>
<script src="assets/procurement-report-ui.js"></script>
```

The runtime initializes on `DOMContentLoaded` and dispatches `pui:panelchange` after a carousel, switch card, or tab changes. Keep report-local chart mounting in `assets/charts.js`; when a chart sits in a hidden panel, let that file listen for `pui:panelchange` and resize the native ECharts instance.

## Report navigation

Use for a sticky chapter rail, horizontal chapter strip, or the persistent portion of a hybrid contents system. Keep a standalone contents plate as ordinary deep-link anchors; add `data-pui-report-nav` only when active-chapter tracking is useful.

```html
<nav class="pui-report-nav" data-pui-report-nav aria-label="报告目录">
  <p class="pui-report-nav__label">目录</p>
  <ol>
    <li><a href="#chapter-01" aria-current="true" aria-label="01 授标建议"><span>01</span>授标</a></li>
    <li><a href="#chapter-02" aria-label="02 成本证据"><span>02</span>成本</a></li>
    <li><a href="#chapter-03" aria-label="03 风险门槛"><span>03</span>门槛</a></li>
  </ol>
</nav>

<main data-pui-report-main>
  <section id="chapter-01" data-pui-section
    data-primary-object="decision-stage" data-density="open">...</section>
  <section id="chapter-02" data-pui-section
    data-primary-object="cost-bridge" data-density="dense">...</section>
</main>
```

The runtime:

- observes every linked `data-pui-section`;
- updates `aria-current` on the matching anchor;
- keeps the active link visible in a horizontal strip;
- uses deep links and native anchor behavior as the no-JS fallback;
- uses smooth scrolling only when reduced motion is not requested.

Every navigation link must point to one unique section ID. Keep numbers and semantic roots aligned with the chapter score and contents plate. A compact rail may abbreviate the visible topic label when its `aria-label` preserves the full canonical topic.

## Chart-runtime boundary

Read `html-report-enhancement-contract.md`. The built-in renderer owns ECharts inclusion and native chart mounting in `assets/charts.js`. This optional runtime never initializes charts.

For a Level 2 linked chart, implement the linkage in report-local `assets/charts.js`:

- listen for `pui:keychange` from a DOM card/table selection;
- dispatch `procurement:charthover`, `procurement:chartleave`, or `procurement:chartselect` only when another report view consumes the event;
- use the same stable supplier/item/lane key;
- preserve the system chart baseline and script order;
- keep the default decision visible without the linkage.

Do not reference `procurement-echarts.js` or call `ProcurementCharts.mount`.

## Scroll-snap shelf

```html
<section class="pui-carousel" data-pui-carousel aria-label="供应商方案">
  <div class="pui-carousel__toolbar">
    <p class="pui-carousel__status" data-pui-carousel-status aria-live="polite"></p>
    <div class="pui-carousel__actions">
      <button type="button" data-pui-carousel-prev aria-label="上一家供应商">←</button>
      <button type="button" data-pui-carousel-next aria-label="下一家供应商">→</button>
    </div>
  </div>
  <div class="pui-carousel__track" data-pui-carousel-track tabindex="0">
    <article class="pui-carousel__item" data-pui-carousel-item>...</article>
    <article class="pui-carousel__item" data-pui-carousel-item>...</article>
  </div>
</section>
```

Keep each item self-contained and identify the recommended item in visible text.

## Hover/focus switch card

```html
<article class="pui-switch" data-pui-switch>
  <button class="pui-switch__toggle" type="button" data-pui-switch-toggle aria-pressed="false">
    查看依据
  </button>
  <div class="pui-switch__face pui-switch__face--front"
    data-pui-switch-front aria-hidden="false">
    <h3>建议：条件授标</h3>
    <p>...</p>
  </div>
  <div class="pui-switch__face pui-switch__face--back"
    data-pui-switch-back aria-hidden="true">
    <h3>条件授标 · 依据</h3>
    <p>...</p>
  </div>
</article>
```

The runtime crossfades the alternate face on hover-capable devices and with the toggle button. Both faces occupy the same measured field so preview never moves neighboring content. Focus remains usable on touch and keyboard. Repeat the recommendation on the alternate face. Do not place focusable controls inside the alternate face; use an explicit `<details>` block for richer interactive evidence.

## Scenario tabs

```html
<section data-pui-tabs>
  <div class="pui-tabs__list" role="tablist" aria-label="需求情景">
    <button type="button" role="tab" id="tab-base" aria-controls="panel-base" aria-selected="true">基准</button>
    <button type="button" role="tab" id="tab-high" aria-controls="panel-high" aria-selected="false">高需求</button>
  </div>
  <div id="panel-base" role="tabpanel" aria-labelledby="tab-base">...</div>
  <div id="panel-high" role="tabpanel" aria-labelledby="tab-high" hidden>...</div>
</section>
```

Use left/right arrow keys to change tabs. Put the recommended scenario first and include an all-scenario table for print.

## Master/detail comparison

Use for a shortlist, lane book, exception queue, or negotiation file when peer names should stay compact and one stable detail surface should update.

```html
<section class="pui-master-detail" data-pui-master-detail>
  <div class="pui-master-detail__list" role="listbox" aria-label="供应商">
    <button class="pui-master-detail__item" type="button"
      data-pui-master-item data-pui-key="supplier-a"
      aria-controls="supplier-a-detail" aria-selected="true">
      供应商 A
    </button>
    <button class="pui-master-detail__item" type="button"
      data-pui-master-item data-pui-key="supplier-b"
      aria-controls="supplier-b-detail" aria-selected="false">
      供应商 B
    </button>
  </div>
  <article class="pui-master-detail__panel" id="supplier-a-detail">...</article>
  <article class="pui-master-detail__panel" id="supplier-b-detail" hidden>...</article>
</section>
```

Arrow keys traverse peers; Home/End move to the first/last peer. Selection dispatches `pui:panelchange` and reuses `data-pui-key` for linked chart/table highlighting. Keep the recommended or current supplier selected by default. Print all panels.

Use the contract exactly: every `data-pui-master-item` needs a unique `aria-controls`, `aria-selected`, and a matching panel ID. If the design uses one dynamically rewritten detail panel instead of one panel per item, do not add `data-pui-master-detail`; implement a separate accessible listbox controller from a known pattern.

## Question-help popover

Use this to remove explanatory clutter around a term, basis, formula, or evidence definition. Never hide a verdict, unit, failed gate, or essential condition.

```html
<span class="pui-help" data-pui-help>
  <button class="pui-help__trigger" type="button"
    data-pui-help-trigger aria-label="解释到厂总成本"
    aria-controls="help-landed-cost" aria-expanded="false">?</button>
  <span class="pui-help__popover" id="help-landed-cost"
    data-pui-help-popover role="tooltip" hidden>
    <strong>到厂总成本</strong><br>
    报价、运费、关税与不可抵扣税费；不含可抵扣增值税。
  </span>
</span>
```

Hover/focus previews; click pins; outside click or Escape clears. Keep the popover on the selected route's readable surface, concise, and visually aligned to its trigger. Set `--radius-tooltip: 0` for hard-grid directions and `8–12px` for softer directions.

## Enhanced comparison table

Use an exact table when procurement basis, units, gates, or auditability matter more than pictorial form. Make it visually active without turning every cell into a badge.

```html
<div class="pui-table-wrap">
  <table class="pui-table">
    <thead>
      <tr>
        <th data-pui-sticky>供应商</th>
        <th data-pui-number>到厂成本</th>
        <th data-pui-number>OTIF</th>
        <th>门槛</th>
      </tr>
    </thead>
    <tbody>
      <tr data-pui-key="supplier-a" tabindex="0">
        <th data-pui-sticky>供应商 A</th>
        <td data-pui-number>¥ 8.72 / 件</td>
        <td data-pui-number>96.4%</td>
        <td>PASS</td>
      </tr>
    </tbody>
  </table>
</div>
```

`data-pui-key` provides hover/focus preview and click-to-pin linkage across DOM objects. Link it to a chart only for a Level 2 question implemented in report-local `assets/charts.js`. Use a sticky identifier only when it does not obscure data. Add sorting, filtering, or expandable evidence only when it changes a decision; do not add generic table controls by default.

## Linked entity highlighting

Add a stable shared key to any table row, card, note, or chart-side label:

```html
<button type="button" data-pui-key="supplier-a">供应商 A</button>
<tr data-pui-key="supplier-a">...</tr>
<aside data-pui-key="supplier-a">...</aside>
```

Hover/focus highlights matching elements. Click pins the key; Escape clears it. For ECharts linkage, listen for `pui:keychange`:

```javascript
document.addEventListener('pui:keychange', function (event) {
  var key = event.detail.key;
  // Map the stable key to the chart dataIndex, then dispatch highlight/downplay.
});
```

## Requirements

- Do not edit the runtime to contain report data.
- Do not let the runtime initialize ECharts, load fonts, define root theme variables, or rewrite the renderer scaffold.
- Keep the verdict and decision gates outside hidden panels.
- Use one interaction grammar across charts, cards, enhanced tables, help, and master/detail.
- Use one chapter navigation grammar; keep the contents topic, abbreviated rail label, and finding-led section heading semantically synchronized without repeating the same line.
- Keep buttons at least 44px on touch layouts.
- Do not rely on animation; the runtime respects reduced-motion preferences.
- Keep switch-card and linked-card dimensions stable during preview and selection.
- Declare every bounded card with `data-object-kind`; use `.pui-object-card` only for a real procurement object.
- Keep the packaged inset dot as a dot. Do not stretch it into a rail or replace it with a physical/logical one-sided border, edge pseudo-element, narrow nested child, inset shadow, gradient, background image, mask, or SVG edge strip.
- Use only neutral structural hairlines for partial rules. A recommendation or selected state must use text, the inset dot, a complete neutral border, or a full-surface fill—not a colored edge.
- Add report-specific print CSS for scenario tables and any evidence that must be expanded.
- Mark every chart's adjacent static table or equivalent readable object with `data-chart-fallback`.
- Use custom interaction code only when its implementation is already known; otherwise keep native anchors, `details`, built-in ECharts, and readable tables.
- After writing HTML, do not run `node --check`, inspect interaction wiring, start a local server, open a browser, take screenshots, or create an HTML runtime preview.
- Keep all charts on the built-in `echarts.min.js → assets/charts.js` path; add click/persistent/keyboard selection only for Level 2.
- Do not use browser-default `title` bubbles for substantive help; use the accessible question-help pattern.
- Keep card and tooltip copy within the visible-text budgets in `procurement-editorial-system.md`.
