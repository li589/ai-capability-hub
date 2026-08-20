# Chart & Map Guide

## Chart.js (Inline & Panel)

Canvas in div with explicit height + `position: relative`. Set `responsive: true`, `maintainAspectRatio: false`. Load UMD via CDN.

Disable default legend, build custom HTML legend. Canvas cannot resolve CSS variables — use hardcoded hex from the color palette.

```html
<div style="position:relative; height:300px">
  <canvas id="myChart"></canvas>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
  new Chart(document.getElementById('myChart'), { /* config */ });
</script>
```

## ECharts (Panel preferred)

Best for complex, interactive charts with auto-resize. Load via CDN.

```html
<div id="chart" style="width:100%; height:400px"></div>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<script>
  const chart = echarts.init(document.getElementById('chart'));
  chart.setOption({ /* config */ });
  window.addEventListener('resize', () => chart.resize());
</script>
```

Key advantages over Chart.js for panel mode:
- Richer chart types (treemap, sunburst, sankey, gauge)
- Built-in tooltip, legend, zoom interactions
- Auto-resize with `chart.resize()`
- Better suited for dashboard-style multi-chart layouts

## D3 Choropleth (Geographic Maps)

Never invent coordinates. Three topology sources:
- `us-atlas` — US states/counties
- `world-atlas` — countries
- `datamaps` — alternative country shapes

Always `web_fetch` the topology URL first to verify availability.

Load D3 + topojson via CDN:

```html
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script src="https://cdn.jsdelivr.net/npm/topojson-client@3"></script>
```

## Interactive Explainer

HTML with sliders, buttons, live displays. No card wrapper. Use `sendPrompt()` for follow-up questions (not data export).

Range slider pattern:
```html
<input type="range" min="0" max="100" value="50"
  oninput="update(this.value)">
<span id="display">50</span>
```
