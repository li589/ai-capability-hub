# Feishu Chart Color Palette

Color system for ECharts charts in Feishu mini programs, derived from Feishu Design System (Lark Design).

## Core Colors

| Role | Hex | Usage |
|------|-----|-------|
| Feishu Blue (Primary) | `#3370FF` | Main data series, active states, primary actions |
| Cyan | `#00C7C7` | Secondary series, info indicators |
| Orange | `#FF9F40` | Tertiary series, warning indicators |
| Purple | `#765BAB` | Quaternary series, accent |
| Success Green | `#34C724` | Positive values, success states |
| Danger Red | `#F54A45` | Negative values, error states, alerts |
| Warning Yellow | `#FFC14E` | Caution indicators |

## Semantic Pairs

Use these pairs for positive/negative visualizations:

```js
const POSITIVE_NEGATIVE = {
  positive: "#3370FF",   // Blue for positive values
  negative: "#F54A45",   // Red for negative values
};

const UP_DOWN = {
  up: "#34C724",         // Green for increase
  down: "#F54A45",       // Red for decrease
};
```

## Multi-Series Color Sequences

### 3-Series (Line / Bar)

```js
const SERIES_3 = ["#3370FF", "#00C7C7", "#FF9F40"];
```

### 5-Series

```js
const SERIES_5 = ["#3370FF", "#00C7C7", "#FF9F40", "#765BAB", "#34C724"];
```

### 10-Series

```js
const SERIES_10 = [
  "#3370FF", "#00C7C7", "#FF9F40", "#765BAB", "#34C724",
  "#F54A45", "#FFC14E", "#5577BA", "#8FC3A6", "#D4BCEC",
];
```

### 19-Series (Pie / Distribution)

Grouped by hue families for visual distinction:

```js
const SERIES_19 = [
  // Purple family
  "#765BAB", "#9275CC", "#B39AD8", "#D4BCEC", "#EADBFD",
  // Orange family
  "#DD562F", "#EB6F4D", "#FF9C71", "#FFAD4D", "#FFC14E",
  // Yellow-green family
  "#FFD28F", "#D6E463", "#C6D22F", "#A3D7B2", "#8FC3A6",
  // Blue family
  "#BAD2F5", "#9CBEEE", "#708FCB", "#5577BA",
];
```

### 20-Series (Extended)

```js
const SERIES_20 = [
  "#765BAB", "#9275CC", "#B39AD8", "#D4BCEC", "#EADBFD",
  "#DD562F", "#EB6F4D", "#FF9C71", "#FFAD4D", "#FFC14E",
  "#FFD28F", "#D6E463", "#C6D22F", "#A3D7B2", "#8FC3A6",
  "#BAD2F5", "#9CBEEE", "#708FCB", "#5577BA", "#3370FF",
];
```

## Neutral Colors (Axes, Grid, Labels)

| Role | Hex | Usage |
|------|-----|-------|
| Text Primary | `#22211F` | Chart title, key labels |
| Text Secondary | `#333333` | Axis labels, legend text |
| Text Tertiary | `#666666` | Subtitle, secondary labels |
| Text Quaternary | `#999999` | Placeholder, disabled |
| Border | `#EEEEEE` | Grid lines, dividers |
| Background | `#F8F8F8` | Chart background |
| Track | `#E8E8E8` | Gauge track, progress bar background |

## Area Gradient Colors

For line charts with `areaStyle`, use the series color with low opacity:

```js
function areaGradient(hexColor) {
  return {
    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: hexColor + "20" },  // 12% opacity at top
      { offset: 1, color: hexColor + "00" },  // 0% opacity at bottom
    ]),
  };
}

// Usage
series: [{
  type: "line",
  areaStyle: areaGradient("#3370FF"),
  // ...
}]
```

> In mini program canvas, `LinearGradient` may not be available. Use `opacity` as fallback:
> ```js
> areaStyle: { opacity: 0.1 }
> ```

## Color Usage in ECharts Config

```js
const option = {
  // Global color sequence
  color: ["#3370FF", "#00C7C7", "#FF9F40"],

  // Axis styling
  xAxis: {
    axisLine: { lineStyle: { color: "#EEEEEE" } },
    axisLabel: { color: "#666666", fontSize: 10 },
    splitLine: { lineStyle: { color: "#F2F2F2" } },
  },
  yAxis: {
    axisLine: { lineStyle: { color: "#EEEEEE" } },
    axisLabel: { color: "#666666", fontSize: 10 },
    splitLine: { lineStyle: { color: "#F2F2F2" } },
  },

  // Legend
  legend: {
    textStyle: { color: "#333333", fontSize: 11 },
    inactiveColor: "#BFBFBF",
  },

  // Tooltip
  tooltip: {
    backgroundColor: "#22211F",
    borderColor: "#22211F",
    textStyle: { color: "#FFFFFF", fontSize: 12 },
  },
};
```

## Dynamic Color by Value

For bar charts that need color based on positive/negative:

```js
series: [{
  type: "bar",
  itemStyle: {
    color: function(params) {
      return params.value >= 0 ? "#3370FF" : "#F54A45";
    },
  },
}]
```

For gauge charts with threshold-based coloring:

```js
series: [{
  type: "gauge",
  axisLine: {
    lineStyle: {
      width: 14,
      color: [
        [0.6, "#F54A45"],   // 0-60%: Red
        [0.8, "#FFC14E"],   // 60-80%: Yellow
        [1, "#34C724"],     // 80-100%: Green
      ],
    },
  },
}]
```
