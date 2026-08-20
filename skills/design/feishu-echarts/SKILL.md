---
name: feishu-echarts
description: Guide for integrating ECharts charts in Feishu mini programs and uni-app projects using the lime-echart component wrapper. Covers component import, canvas initialization, tooltip formatting, height configuration, data deep copy optimization, and common chart patterns. Use when working with ECharts in Feishu/uni-app environments, encountering chart rendering issues, tooltip display problems, chart height being zero, circular reference errors, or when the user asks to add/fix/optimize charts in a mini program.
install_source: official
install_method: download
skill_id: 6dd9c5d0-503d-4ea3-98c7-39050ea3d024
enabled_at: 1787231572212
version: 1.0.0
name_zh: 飞书小程序适配Echarts图表库
---

# Feishu ECharts Integration

Integrate ECharts in Feishu mini programs (飞书小程序) and uni-app via the `lime-echart` component wrapper.

## 1. Import & Registration

```js
// Import ECharts core (use the bundled min.js, NOT npm echarts)
import * as echarts from "@/components/uni_modules/lime-echart/static/echarts.min.js";
// Import the l-echart component
import lEchart from "@/components/uni_modules/lime-echart/components/l-echart/l-echart.vue";

export default {
  components: { lEchart },
  // ...
}
```

> **Critical**: Always use the bundled `echarts.min.js` from lime-echart's `static/` directory. Importing from `npm install echarts` causes circular reference errors in mini programs.

## 2. Template Usage

```html
<template>
  <l-echart
    ref="lineChart"
    canvasId="lineChart"
    :customStyle="chartStyle"
    @finished="onChartFinished"
  ></l-echart>
</template>
```

### Height Configuration

Chart height **must** be set via the `customStyle` prop — CSS `height` on the `<l-echart>` tag does **not** work in Feishu mini programs.

```js
data() {
  return {
    chartStyle: "width: 100%; height: 300px;",
  }
}
```

For charts inside scroll containers or flex layouts, use a computed property or inline binding to ensure the height is applied before initialization.

## 3. ECharts Instance — Never in `data()`

**Do not** store the ECharts instance in Vue's `data()`. The instance contains non-serializable internal objects that trigger Vue's recursive reactivity watcher, causing:

- Circular reference errors
- Infinite console warnings
- Potential page freeze

```js
// ❌ WRONG — causes circular reference
data() {
  return {
    chart: null,  // NEVER do this
  }
}

// ✅ CORRECT — store as instance property
methods: {
  initChart() {
    this.$refs.lineChart.init(echarts, (chart) => {
      // Attach to `this` directly, NOT in data()
      this.chart = chart;
      chart.setOption(this.option);
    });
  }
}
```

## 4. Initialization Pattern

Always wrap initialization in `$nextTick` + `setTimeout` to ensure the canvas is ready:

```js
methods: {
  async loadData() {
    const res = await fetchData();
    this.option = this.buildOption(res);

    this.$nextTick(() => {
      setTimeout(() => {
        if (this.$refs.lineChart) {
          this.$refs.lineChart.init(echarts, (chart) => {
            this.chart = chart;
            chart.setOption(this.option);
          });
        }
      }, 300); // 300ms is the recommended minimum delay
    });
  }
}
```

> The `beforeDelay` prop on `<l-echart>` defaults to 30ms. For complex charts or first render, use the explicit `setTimeout(300)` pattern above.

## 5. Tooltip Formatter — No HTML

Feishu mini program renders tooltips on **canvas**, not DOM. HTML tags (`<div>`, `<br/>`, `<span>`) will not be parsed.

```js
tooltip: {
  trigger: "axis",
  formatter: function(params) {
    if (!params || !params.length) return "";
    // ✅ Use \n for line breaks
    let result = params[0].axisValue + "\n";
    params.forEach(function(item) {
      let val = item.value;
      if (typeof val === "number") {
        val = val.toLocaleString();
      }
      result += item.marker + " " + item.seriesName + ": " + val + "\n";
    });
    return result;
  },
}
```

> Avoid `'<0%'` in formatter strings — the angle bracket may be misinterpreted as an HTML tag by the renderer. Escape it or restructure the expression.

## 6. Chart Data Deep Copy

Replace `JSON.parse(JSON.stringify(arr))` with `arr.map(item => ({...item}))` for chart data arrays. The objects in chart data typically contain only primitive properties (string, number, boolean), making a one-level shallow copy equivalent but **3-10x faster**.

```js
// ❌ Slow — full serialization round-trip
this.orgCharData = JSON.parse(JSON.stringify(lineData));

// ✅ Fast — shallow copy of each object
this.orgCharData = lineData.map(item => ({...item}));
```

> For data with nested objects/arrays (e.g., table rows, selection state), keep `JSON.parse(JSON.stringify())`.

## 7. Common Chart Patterns

### Line Chart

```js
{
  grid: { top: 30, right: 20, bottom: 60, left: 50 },
  tooltip: { trigger: "axis" },
  legend: { bottom: 0 },
  xAxis: {
    type: "category",
    data: dates,
    axisLabel: { rotate: 30, fontSize: 10 },
  },
  yAxis: { type: "value" },
  dataZoom: [
    { type: "inside", startValue: len - 12, endValue: len - 1 },
    { type: "slider", startValue: len - 12, endValue: len - 1 },
  ],
  series: [{
    type: "line",
    smooth: true,
    data: values,
    areaStyle: { opacity: 0.1 },
  }],
}
```

### Pie Chart

```js
{
  series: [{
    type: "pie",
    radius: "65%",
    data: pieData,
    silent: true,           // Disable interaction for static display
    label: { show: false },  // Hide labels by default
    emphasis: {
      label: { show: true }, // Show on touch
    },
  }],
}
```

### Bar Chart (Horizontal, Positive/Negative)

```js
{
  grid: { top: 30, right: 60, bottom: 20, left: 100 },
  tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
  xAxis: { type: "value" },
  yAxis: { type: "category", data: categories },
  series: [{
    type: "bar",
    data: barData,
    itemStyle: {
      color: function(params) {
        return params.value >= 0 ? "#3370FF" : "#E64B4D";
      },
    },
    label: { show: true, position: "right" },
  }],
}
```

## 8. Data Update

Use `setOption` to update an existing chart — do **not** re-init:

```js
updateChart(newData) {
  if (this.chart) {
    this.chart.setOption({ series: [{ data: newData }] });
  }
}
```

## 9. Event Handling

```js
chart.on("click", (params) => {
  console.log("Clicked:", params.name, params.value);
});

chart.on("datazoom", (params) => {
  if (params.batch[0].end > 98) {
    // Trigger load-more logic
  }
});
```

## 10. Lifecycle Management

```js
export default {
  methods: {
    async loadData() {
      // ... fetch data ...
      this.$nextTick(() => {
        setTimeout(() => {
          this.$refs.lineChart?.init(echarts, (chart) => {
            this.chart = chart;
            chart.setOption(this.option);
          });
        }, 300);
      });
    },
  },
  // Re-render on page show (mini program lifecycle)
  onShow() {
    if (this.chart) {
      // Option A: just resize
      this.chart.resize();
      // Option B: re-fetch and setOption
      // this.loadData();
    }
  },
  // Cleanup on destroy
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
  },
}
```

## 11. Troubleshooting Quick Reference

| Symptom | Cause | Fix |
|---------|-------|-----|
| Chart height is 0 | CSS height not applied | Use `customStyle` prop |
| Circular reference error | ECharts instance in `data()` | Move to `this.chart` instance property |
| Tooltip shows raw HTML tags | Using `<br/>` or `<div>` in formatter | Replace with `\n` |
| Chart not rendering on first load | Canvas not ready when `init` called | Wrap in `$nextTick` + `setTimeout(300)` |
| Chart disappears on page switch | Instance disposed or lost | Re-init in `onShow` or resize |
| `echarts is not defined` | Wrong import source | Use bundled `echarts.min.js` path |
| Data zoom not working | Missing `dataZoom` config | Add both `inside` and `slider` types |

## 12. Feishu Color Palette

Charts should use the Feishu Design System color scheme for visual consistency.

| Role | Hex |
|------|-----|
| Primary (Blue) | `#3370FF` |
| Cyan | `#00C7C7` |
| Orange | `#FF9F40` |
| Purple | `#765BAB` |
| Success (Green) | `#34C724` |
| Danger (Red) | `#F54A45` |
| Warning (Yellow) | `#FFC14E` |
| Text Primary | `#22211F` |
| Text Secondary | `#333333` |
| Text Tertiary | `#666666` |
| Border | `#EEEEEE` |
| Track | `#E8E8E8` |

Common multi-series sequences:
```js
// 3-series
["#3370FF", "#00C7C7", "#FF9F40"]
// 5-series
["#3370FF", "#00C7C7", "#FF9F40", "#765BAB", "#34C724"]
// Positive/Negative
{ positive: "#3370FF", negative: "#F54A45" }
// Gauge thresholds
[[0.6, "#F54A45"], [0.8, "#FFC14E"], [1, "#34C724"]]
```

## Additional Resources

- For the complete color system with all sequences and usage examples, see [references/color-palette.md](references/color-palette.md)
- For full chart configuration templates (line, pie, gauge, bar, stacked), see [references/chart-templates.md](references/chart-templates.md)
- For sample chart data for testing, see [references/example-data.json](references/example-data.json)
