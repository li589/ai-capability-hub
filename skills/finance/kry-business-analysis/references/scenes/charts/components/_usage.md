# 组件使用指南

## 渲染策略决策树

```
商户需求
├─ 预制场景（老板日报/周报/月报/菜品分析等12个） → 标准路径
├─ 自由查询（用户自定义分析维度）              → 混合路径
└─ 完全自定义（独特配色/布局/新图表类型）       → 自由路径
```

---

## 标准路径（预制场景，推荐）

### 步骤

0. **（首先）跑构建库拿组件数据**：`node scripts/report-data.mjs build --manifest scripts/manifests/<场景>.mjs --data-dir <fetch产物目录> --out report-data.json`，得到 `{ components, facts }`。下文所有「填充数据」均从 `report-data.json` 的 `components.<组件名>` 取值，禁止心算/手工汇总
1. **复制骨架**：将 `report-shell.html` 作为报告文件起点
2. **填充 Hero 区域**：替换标题、日期范围、品牌名、核心 KPI 数字（取自 `components.kpi`）
3. **插入组件**：在 `<!-- 各板块 section -->` 处，按场景需要逐个插入组件
4. **替换数据**：将组件中的 `<!-- DATA: ... -->` 和占位内容替换为 `report-data.json` 对应组件的真实数据
5. **追加洞察/行动卡片**：插入 `insight-card.html` 和 `action-card.html`（以 `facts` 为依据）
6. **完成**：无需手写 CSS，shell 已包含全部样式

### 示例

```
cp report-shell.html → output/report.html
→ 填 hero（标题/日期/品牌/highlight数字）
→ 在 container 内插入 kpi-card 组件，填充 KPI 数据
→ 插入 bar-ranking 组件，填充门店排行数据
→ 插入 line-trend 组件，填充营收趋势数据
→ 插入 insight-card 组件，填充洞察
→ 插入 action-card 组件，填充行动建议
```

---

## 混合路径（自由查询）

在标准路径基础上：
- 可以在 shell 的 `<style>` 标签内追加自定义 CSS
- 可以手写不在组件库中的自定义板块（直接写 `<div class="section">...</div>`）
- 可以混用组件 + 自定义板块

---

## 自由路径（完全自定义）

当商户需求与标准组件完全不匹配时：
- AI 可完全不使用 shell，从空白 HTML 手写
- 能力与之前完全一致，不受组件库约束
- 但仍建议复用 shell 中的 CSS 变量/色板保持品牌一致性

---

## 组件速查

| 组件文件 | 用途 | 数据格式（report-data.json 的 components.<组件>） |
|----------|------|----------|
| `kpi-card.html` | 核心指标卡片（3~6个） | 逐个填充 label/value/unit/delta |
| `bar-ranking.html` | 横向柱图排行 | `{ categories:[名称...], values:[数值...] }`（两个平行数组） |
| `line-trend.html` | 折线趋势图 | `{ xLabels:[...], series:[{name,data}] }` |
| `pie-doughnut.html` | 饼图/环形图 | `{ data:[{name,value}] }` |
| `stacked-bar.html` | 堆叠柱图 | `{ xLabels:[...], series:[{name,stack,data}] }` |
| `radar.html` | 雷达图 | `{ indicator:[{name,max}], data:[{value:[],name}] }` |
| `heatmap.html` | 热力图 | `{ xLabels:[...], yLabels:[...], data:[[x,y,value]] }` |
| `scatter-quadrant.html` | 四象限散点图 | `{ data:[[x,y,name]], medianX, medianY }` |
| `insight-card.html` | 洞察卡片 | 逐条填充 type(good/warn/info/risk) + title + content |
| `action-card.html` | 行动项卡片 | 逐条填充 prio(p0/p1/p2) + title + desc |
| `data-table.html` | 数据表格 | thead + tbody 行数据 |

> ⚠ **数据契约红线（防图表白屏）**：填充 ECharts 数据时，**直接内联 `report-data.json` 里 `components.<组件>` 的数组**，严格按上表结构取字段，**禁止自造 helper 函数猜数据结构**。
> 典型错误：`bar-ranking` 返回的是 `{categories:[名称], values:[数值]}` 两个**平行数组**，若误当对象数组写 `data.values.map(v => v.name)`，因数值没有 `.name/.value`，会得到 `[null,null,...]` → 图表全白屏。
> 正确写法：`yAxis.data = components.xxx.categories`、`series.data = components.xxx.values`。

---

## 全局色板常量

```javascript
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

const HERO_GRADIENT = 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #ec4899 100%)';
const SECTION_BORDER = 'linear-gradient(180deg, #6366f1, #ec4899)';

const CHART_GRADIENTS = {
  primary: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    { offset: 0, color: 'rgba(99,102,241,0.35)' },
    { offset: 1, color: 'rgba(99,102,241,0)' }
  ]),
  bar: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
    { offset: 0, color: '#6366f1' },
    { offset: 1, color: '#ec4899' }
  ])
};

const TOOLTIP = {
  trigger: 'axis',
  backgroundColor: 'rgba(255,255,255,0.95)',
  borderColor: '#e5e7eb',
  textStyle: { color: '#374151', fontSize: 13 }
};

const GRID = { top: 60, right: 30, bottom: 40, left: 60, containLabel: true };
```

---

## 注意事项

1. **ECharts ID 唯一性**：每个图表的 `id` 必须全局唯一，建议用 `chart-{sectionName}-{index}` 格式
2. **resize 处理**：shell 底部已包含全局 resize 监听，无需在每个组件中重复
3. **图表高度**：默认 400px，可通过添加 class `tall`(480px) 或 `short`(320px) 调整
4. **响应式**：shell 已包含 `@media` 断点，KPI 卡片和 grid 布局会自动适配移动端
