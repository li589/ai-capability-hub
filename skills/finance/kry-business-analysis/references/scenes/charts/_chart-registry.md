# ECharts 图表注册表

本文件定义全局色板常量和图表选型指南。具体组件模板见 `components/` 目录，页面骨架见 `report-shell.html`。

---

## 全局样式规范

```javascript
// 全局色板（紫粉渐变主题）
const COLORS = {
  primary: '#6366f1',       // indigo
  secondary: '#8b5cf6',    // violet
  accent: '#ec4899',       // pink
  success: '#10b981',      // emerald
  danger: '#ef4444',       // red
  warning: '#f59e0b',      // amber
  info: '#3b82f6',         // blue
  palette: ['#6366f1', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#06b6d4', '#14b8a6', '#a855f7', '#94a3b8']
};

// Hero 渐变（3色）
const HERO_GRADIENT = 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)';

// Section 标题竖线渐变
const SECTION_BORDER = 'linear-gradient(180deg, #6366f1, #ec4899)';

// 图表系列渐变生成器
const CHART_GRADIENTS = {
  primary: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(99,102,241,0.35)' },
    { offset: 1, color: 'rgba(99,102,241,0)' }
  ]),
  bar: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: '#6366f1' },
    { offset: 1, color: '#ec4899' }
  ]),
  bar_alt: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: '#8b5cf6' },
    { offset: 1, color: '#f59e0b' }
  ])
};

// 通用 tooltip 配置
const TOOLTIP = {
  trigger: 'axis',
  backgroundColor: 'rgba(255,255,255,0.95)',
  borderColor: '#e5e7eb',
  textStyle: { color: '#374151', fontSize: 13 }
};

// 通用 grid 配置
const GRID = { top: 60, right: 30, bottom: 40, left: 60, containLabel: true };
```

---

## 图表选型速查

| 数据场景                   | 推荐图表     | 组件文件                           |
| -------------------------- | ------------ | ---------------------------------- |
| 核心 KPI 概览（3~6个指标） | KPI 卡片     | `components/kpi-card.html`         |
| 排行榜（门店/菜品/员工）   | 横向柱图     | `components/bar-ranking.html`      |
| 日/周/月趋势（营收/客流）  | 折线图       | `components/line-trend.html`       |
| 占比构成（收入/支付方式）  | 环形图       | `components/pie-doughnut.html`     |
| 品类贡献/构成趋势          | 堆叠柱图     | `components/stacked-bar.html`      |
| 多维对比（门店/区域）      | 雷达图       | `components/radar.html`            |
| 时段×维度交叉分析          | 热力图       | `components/heatmap.html`          |
| 双维象限分析（销量vs毛利） | 四象限散点图 | `components/scatter-quadrant.html` |
| AI 经营洞察                | 洞察卡片     | `components/insight-card.html`     |
| 行动建议                   | 行动项卡片   | `components/action-card.html`      |
| 明细数据/排行表格          | 数据表格     | `components/data-table.html`       |

---

## 使用方式

1. **页面骨架**：使用 `report-shell.html` 作为 HTML 报告起点（含完整 CSS + Hero + Container + Footer + resize 处理）
2. **按需组装**：从 `components/` 中选择所需组件，插入到 container 区域
3. **数据替换**：将组件中 `<!-- DATA: ... -->` 占位替换为真实数据
4. **详细指南**：参见 `components/_usage.md`
