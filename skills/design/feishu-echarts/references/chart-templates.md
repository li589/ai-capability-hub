# Feishu ECharts — Chart Configuration Templates

Complete chart configuration templates with Feishu color palette applied.

> See [color-palette.md](color-palette.md) for the full color system.

## Line Chart with Multiple Series

```js
function buildLineOption(dates, seriesData) {
  return {
    color: ["#3370FF", "#00C7C7", "#FF9F40"],
    grid: { top: 40, right: 20, bottom: 80, left: 50 },
    tooltip: {
      trigger: "axis",
      formatter: function(params) {
        if (!params || !params.length) return "";
        let result = params[0].axisValue + "\n";
        params.forEach(function(item) {
          let val = item.value;
          if (typeof val === "number") val = val.toLocaleString();
          result += item.marker + " " + item.seriesName + ": " + val + "\n";
        });
        return result;
      },
    },
    legend: {
      bottom: 0,
      type: "scroll",
      textStyle: { color: "#333333", fontSize: 11 },
    },
    xAxis: {
      type: "category",
      data: dates,
      axisLine: { lineStyle: { color: "#EEEEEE" } },
      axisLabel: { color: "#666666", rotate: 30, fontSize: 10 },
      boundaryGap: false,
    },
    yAxis: {
      type: "value",
      axisLine: { lineStyle: { color: "#EEEEEE" } },
      axisLabel: { color: "#666666", fontSize: 10 },
      splitLine: { lineStyle: { color: "#F2F2F2" } },
    },
    dataZoom: [
      { type: "inside", startValue: dates.length - 12, endValue: dates.length - 1 },
      { type: "slider", startValue: dates.length - 12, endValue: dates.length - 1 },
    ],
    series: seriesData.map(function(item) {
      return {
        name: item.name,
        type: "line",
        smooth: true,
        data: item.data,
        areaStyle: { opacity: 0.1 },
      };
    }),
  };
}
```

## Pie Chart with Dynamic Colors

```js
const SERIES_19 = [
  "#765BAB", "#9275CC", "#B39AD8", "#D4BCEC", "#EADBFD",
  "#DD562F", "#EB6F4D", "#FF9C71", "#FFAD4D", "#FFC14E",
  "#FFD28F", "#D6E463", "#C6D22F", "#A3D7B2", "#8FC3A6",
  "#BAD2F5", "#9CBEEE", "#708FCB", "#5577BA",
];

function buildPieOption(dataList) {
  return {
    color: SERIES_19,
    series: [{
      type: "pie",
      radius: "65%",
      data: dataList.map(function(item) {
        return {
          value: item.value,
          name: item.name + " " + item.formattedValue,
        };
      }),
      silent: true,
      label: { show: false },
      emphasis: {
        label: {
          show: true,
          position: "center",
          fontSize: 14,
          fontWeight: "bold",
          color: "#22211F",
        },
      },
    }],
  };
}
```

## Gauge (Half-Circle Progress)

```js
function buildGaugeOption(percent, valid) {
  return {
    series: [{
      type: "gauge",
      startAngle: 180,
      endAngle: 0,
      radius: "90%",
      min: 0,
      max: 100,
      progress: {
        show: true,
        width: 14,
        roundCap: true,
        itemStyle: { color: "#3370FF" },
      },
      axisLine: {
        lineStyle: { width: 14, color: [[1, "#E8E8E8"]] },
      },
      pointer: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        fontSize: 24,
        fontWeight: "bold",
        color: "#22211F",
        offsetCenter: [0, "10%"],
        formatter: function(value) {
          return valid ? value.toFixed(0) + "%" : "—";
        },
      },
      data: [{ value: valid ? percent : 0 }],
    }],
  };
}
```

## Gauge with Threshold Colors

```js
function buildThresholdGaugeOption(percent, valid) {
  return {
    series: [{
      type: "gauge",
      startAngle: 180,
      endAngle: 0,
      radius: "90%",
      min: 0,
      max: 100,
      axisLine: {
        lineStyle: {
          width: 14,
          color: [
            [0.6, "#F54A45"],
            [0.8, "#FFC14E"],
            [1, "#34C724"],
          ],
        },
      },
      progress: { show: true, width: 14, roundCap: true },
      pointer: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        valueAnimation: true,
        fontSize: 24,
        fontWeight: "bold",
        color: "#22211F",
        offsetCenter: [0, "10%"],
        formatter: "{value}%",
      },
      data: [{ value: valid ? percent : 0 }],
    }],
  };
}
```

## Horizontal Bar Chart (Positive/Negative)

```js
function buildBarOption(categories, values) {
  return {
    color: ["#3370FF"],
    grid: { top: 20, right: 80, bottom: 20, left: 100 },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: function(params) {
        let item = params[0];
        return item.name + "\n" + item.marker + " " + item.value + "%";
      },
    },
    xAxis: {
      type: "value",
      max: function(val) {
        return Math.ceil(Math.max(Math.abs(val.min), Math.abs(val.max)) * 1.1);
      },
      axisLabel: { color: "#666666", formatter: "{value}%" },
      splitLine: { lineStyle: { color: "#F2F2F2" } },
    },
    yAxis: {
      type: "category",
      data: categories,
      axisLine: { lineStyle: { color: "#EEEEEE" } },
      axisLabel: { color: "#333333", fontSize: 10 },
    },
    series: [{
      type: "bar",
      data: values,
      itemStyle: {
        color: function(params) {
          return params.value >= 0 ? "#3370FF" : "#F54A45";
        },
      },
      label: {
        show: true,
        position: "right",
        formatter: "{c}%",
        fontSize: 10,
        color: "#666666",
      },
      barWidth: "60%",
    }],
  };
}
```

## Stacked Column Chart

```js
function buildStackedOption(categories, seriesList) {
  return {
    color: ["#3370FF", "#00C7C7", "#FF9F40", "#765BAB"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
    },
    legend: {
      bottom: 0,
      textStyle: { color: "#333333", fontSize: 11 },
    },
    grid: { top: 30, right: 20, bottom: 60, left: 50 },
    xAxis: {
      type: "category",
      data: categories,
      axisLine: { lineStyle: { color: "#EEEEEE" } },
      axisLabel: { color: "#666666", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      axisLine: { lineStyle: { color: "#EEEEEE" } },
      axisLabel: { color: "#666666", fontSize: 10 },
      splitLine: { lineStyle: { color: "#F2F2F2" } },
    },
    series: seriesList.map(function(item) {
      return {
        name: item.name,
        type: "bar",
        stack: "total",
        data: item.data,
        barWidth: "50%",
      };
    }),
  };
}
```

## Number Formatting Helpers

```js
function formatInt(val) {
  if (val == null || val === "" || (typeof val === "number" && isNaN(val))) {
    return "0";
  }
  const str = String(Math.round(Number(val)));
  return str.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function formatDecimal(val) {
  if (val == null || val === "" || (typeof val === "number" && isNaN(val))) {
    return "0.00";
  }
  const num = Number(val).toFixed(2);
  const parts = num.split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return parts.join(".");
}

function parsePercent(str) {
  if (str == null || str === "" || str === "-" || str === "—") {
    return { valid: false, value: 0 };
  }
  const cleaned = String(str).replace(/%/g, "").trim();
  const num = parseFloat(cleaned);
  return {
    valid: !isNaN(num) && isFinite(num),
    value: isNaN(num) ? 0 : num,
  };
}
```

## Chart Data Deep Copy

```js
// For chart data with only primitive properties
const copy = source.map(item => ({...item}));

// For data with nested objects/arrays
const deepCopy = JSON.parse(JSON.stringify(source));
```

## Complete Page Integration Template

```vue
<template>
  <view>
    <l-echart
      ref="chart"
      canvasId="myChart"
      :customStyle="'width: 100%; height: 300px;'"
    ></l-echart>
  </view>
</template>

<script>
import * as echarts from "@/components/uni_modules/lime-echart/static/echarts.min.js";
import lEchart from "@/components/uni_modules/lime-echart/components/l-echart/l-echart.vue";

export default {
  components: { lEchart },
  data() {
    return { option: null };
  },
  async onLoad() {
    await this.fetchAndRender();
  },
  onShow() {
    if (this.chart) this.chart.resize();
  },
  beforeDestroy() {
    if (this.chart) { this.chart.dispose(); this.chart = null; }
  },
  methods: {
    async fetchAndRender() {
      const res = await this.fetchData();
      this.option = this.buildOption(res);
      this.$nextTick(() => {
        setTimeout(() => {
          if (this.$refs.chart) {
            this.$refs.chart.init(echarts, (chart) => {
              this.chart = chart;
              chart.setOption(this.option);
            });
          }
        }, 300);
      });
    },
    buildOption(data) {
      // Use templates above
    },
  },
};
</script>
```
