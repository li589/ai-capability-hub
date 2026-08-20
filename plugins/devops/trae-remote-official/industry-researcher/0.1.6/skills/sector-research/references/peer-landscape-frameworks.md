# 竞争格局可视化框架

## 一、定位矩阵轴对参考

### A股/港股常见板块轴对组合

| 板块 | 轴对组合 |
|------|----------|
| 半导体/电子 | 国产替代程度 × 技术壁垒；产品线宽度 × 下游客户集中度 |
| 白酒/消费 | 价格带(高端-次高端-大众) × 渠道结构；全国化 × 区域深耕 |
| 创新药/医药 | 管线创新度(me-too/me-better/first-in-class) × 商业化能力；国内市场 × 出海 |
| 新能源(锂电/光伏) | 一体化程度 × 成本曲线位置；产能规模 × 技术路线领先性 |
| 银行/金融 | 规模 × 专业化；对公-零售结构 × 区域布局 |
| 军工 | 总装 × 配套层级；型号壁垒 × 民品拓展 |
| 通用制造/工业 | 定制化 × 规模；地域范围 × 垂直聚焦 |
| 互联网/科技(港股) | 产品广度 × 用户分层；生态整合深度 × 变现能力 |

未列出的板块选取投资者与产业界通常使用的两个核心竞争维度作为轴。

---

## 二、可视化类型选择规则

| 图表类型 | 适用场景 | 不适用 |
|----------|----------|--------|
| 2x2 定位矩阵（散点图） | 两个核心竞争维度、公司数 5-15 | 单维度排名 |
| 雷达图 | 多维度（4-8 维）综合对比、少量公司（≤5） | 维度过多（>8）或公司过多（>6） |
| 分层/分群气泡图 | 存在明确战略群组、需展示第三维度（如市值） | 群组划分不明确 |
| 横向柱状对比图 | 单指标排名、公司数较多 | 多维度同时展示 |

选择优先级：先判断维度数量，再判断公司数量，最后考虑是否需要展示附加维度（市值/营收等）。

---

### ECharts 实现规范

> 以下为 ECharts 配置模板，供 Step 6 报告生成使用。模板为 **JavaScript 对象格式（非严格 JSON）**——`// placeholder` 行为填写提示，生成实际代码时替换为真实值。

通用配置：
- 配色：主色 `#1a3a5c`（深蓝）、辅色 `#4a90d9`、`#67b7dc`、`#f5a623`、`#d0021b`
- 字体：中文 `"PingFang SC", "Microsoft YaHei", sans-serif`；数字 `"DIN Alternate", "Helvetica Neue", monospace`
- 响应式：容器宽度 100%，高度 400-500px
- `// placeholder` 标注处需替换为实际数据

### 3.1 2x2 定位矩阵（散点图）

```json
{
  "tooltip": {
    "trigger": "item",
    "formatter": "{b}<br/>{a}：({c})",
    // placeholder: 自定义 formatter 函数，显示公司名 + X轴值 + Y轴值 + 单位
  },
  "grid": {
    "left": "12%",
    "right": "8%",
    "top": "10%",
    "bottom": "12%"
  },
  "xAxis": {
    "type": "value",
    "name": "// placeholder: X轴维度名称（如"国产替代程度"）",
    "nameLocation": "middle",
    "nameGap": 30,
    "nameTextStyle": {
      "fontFamily": "PingFang SC, Microsoft YaHei",
      "fontSize": 13,
      "color": "#1a3a5c"
    },
    "splitLine": { "show": false }
  },
  "yAxis": {
    "type": "value",
    "name": "// placeholder: Y轴维度名称（如"技术壁垒"）",
    "nameLocation": "middle",
    "nameGap": 40,
    "nameTextStyle": {
      "fontFamily": "PingFang SC, Microsoft YaHei",
      "fontSize": 13,
      "color": "#1a3a5c"
    },
    "splitLine": { "show": false }
  },
  "series": [
    {
      "name": "竞争格局",
      "type": "scatter",
      "symbolSize": 18,
      "itemStyle": { "color": "#4a90d9" },
      "label": {
        "show": true,
        "position": "right",
        "formatter": "{b}",
        "fontFamily": "PingFang SC, Microsoft YaHei",
        "fontSize": 11
      },
      "markLine": {
        "silent": true,
        "lineStyle": { "type": "dashed", "color": "#999", "width": 1 },
        "data": [
          { "xAxis": "// placeholder: X轴中位数" },
          { "yAxis": "// placeholder: Y轴中位数" }
        ],
        "label": { "show": false }
      },
      "data": [
        // placeholder: [[x1, y1, '公司A'], [x2, y2, '公司B'], ...]
      ]
    }
  ],
  "graphic": [
    // placeholder: 四象限背景矩形，使用半透明填充区分象限
    // 左下象限示例：
    {
      "type": "rect",
      "left": "12%", "top": "50%",
      "shape": { "width": "// placeholder", "height": "// placeholder" },
      "style": { "fill": "rgba(208,2,27,0.03)" }
    },
    // 右上象限示例：
    {
      "type": "rect",
      "right": "8%", "top": "10%",
      "shape": { "width": "// placeholder", "height": "// placeholder" },
      "style": { "fill": "rgba(74,144,217,0.05)" }
    }
  ]
}
```

### 3.2 雷达图

```json
{
  "tooltip": {
    "trigger": "item",
    // placeholder: formatter 显示各维度具体数值
  },
  "legend": {
    "top": "2%",
    "textStyle": {
      "fontFamily": "PingFang SC, Microsoft YaHei",
      "fontSize": 12
    },
    "data": ["// placeholder: 公司A", "// placeholder: 公司B"]
  },
  "radar": {
    "indicator": [
      // placeholder: 从数据动态生成，格式为 { "name": "维度名", "max": 100 }
      { "name": "// placeholder: 维度1", "max": 100 },
      { "name": "// placeholder: 维度2", "max": 100 },
      { "name": "// placeholder: 维度3", "max": 100 },
      { "name": "// placeholder: 维度4", "max": 100 },
      { "name": "// placeholder: 维度5", "max": 100 }
    ],
    "radius": "65%",
    "nameGap": 8,
    "name": {
      "textStyle": {
        "fontFamily": "PingFang SC, Microsoft YaHei",
        "fontSize": 12,
        "color": "#333"
      }
    },
    "splitArea": { "areaStyle": { "color": ["rgba(26,58,92,0.02)", "rgba(26,58,92,0.05)"] } }
  },
  "series": [
    {
      "type": "radar",
      "data": [
        {
          "value": [80, 70, 90, 65, 85],
          // placeholder: 替换为实际数据
          "name": "// placeholder: 公司A",
          "lineStyle": { "color": "#1a3a5c", "width": 2 },
          "areaStyle": { "color": "rgba(26,58,92,0.15)" },
          "itemStyle": { "color": "#1a3a5c" }
        },
        {
          "value": [60, 85, 70, 80, 55],
          // placeholder: 替换为实际数据
          "name": "// placeholder: 公司B",
          "lineStyle": { "color": "#f5a623", "width": 2 },
          "areaStyle": { "color": "rgba(245,166,35,0.15)" },
          "itemStyle": { "color": "#f5a623" }
        }
      ]
    }
  ]
}
```

### 3.3 分层气泡图

```json
{
  "tooltip": {
    "trigger": "item",
    "formatter": "// placeholder: function(params) 返回 公司名/X值/Y值/市值"
  },
  "legend": {
    "top": "2%",
    "data": ["// placeholder: 群组1", "// placeholder: 群组2", "// placeholder: 群组3"],
    "textStyle": { "fontFamily": "PingFang SC, Microsoft YaHei", "fontSize": 12 }
  },
  "grid": {
    "left": "10%", "right": "10%", "top": "12%", "bottom": "12%"
  },
  "xAxis": {
    "type": "value",
    "name": "// placeholder: X轴维度",
    "nameTextStyle": { "fontFamily": "PingFang SC, Microsoft YaHei", "fontSize": 13 }
  },
  "yAxis": {
    "type": "value",
    "name": "// placeholder: Y轴维度",
    "nameTextStyle": { "fontFamily": "PingFang SC, Microsoft YaHei", "fontSize": 13 }
  },
  "series": [
    {
      "name": "// placeholder: 群组1（如龙头企业）",
      "type": "scatter",
      "itemStyle": { "color": "#1a3a5c" },
      "symbolSize": "// placeholder: function(val) { return Math.sqrt(val[2]) * 缩放系数; }",
      "label": { "show": true, "position": "top", "formatter": "{b}", "fontSize": 10 },
      "data": [
        // placeholder: [[x, y, 市值, '公司名'], ...]
      ]
    },
    {
      "name": "// placeholder: 群组2（如挑战者）",
      "type": "scatter",
      "itemStyle": { "color": "#4a90d9" },
      "symbolSize": "// placeholder: function(val) { return Math.sqrt(val[2]) * 缩放系数; }",
      "label": { "show": true, "position": "top", "formatter": "{b}", "fontSize": 10 },
      "data": [
        // placeholder: [[x, y, 市值, '公司名'], ...]
      ]
    },
    {
      "name": "// placeholder: 群组3（如细分龙头）",
      "type": "scatter",
      "itemStyle": { "color": "#67b7dc" },
      "symbolSize": "// placeholder: function(val) { return Math.sqrt(val[2]) * 缩放系数; }",
      "label": { "show": true, "position": "top", "formatter": "{b}", "fontSize": 10 },
      "data": [
        // placeholder: [[x, y, 市值, '公司名'], ...]
      ]
    }
  ]
}
```

### 3.4 横向柱状对比图

```json
{
  "tooltip": {
    "trigger": "axis",
    "axisPointer": { "type": "shadow" },
    "formatter": "// placeholder: 显示公司名 + 指标值 + 单位"
  },
  "grid": {
    "left": "18%", "right": "12%", "top": "8%", "bottom": "8%"
  },
  "xAxis": {
    "type": "value",
    "name": "// placeholder: 指标名称（如"毛利率 %"）",
    "nameTextStyle": {
      "fontFamily": "DIN Alternate, Helvetica Neue",
      "fontSize": 12
    },
    "axisLabel": { "fontFamily": "DIN Alternate, Helvetica Neue" }
  },
  "yAxis": {
    "type": "category",
    "inverse": true,
    "axisLabel": {
      "fontFamily": "PingFang SC, Microsoft YaHei",
      "fontSize": 12
    },
    "data": [
      // placeholder: 按指标值从大到小排列的公司名列表
      "// placeholder: 公司A（最大值）",
      "// placeholder: 公司B",
      "// placeholder: 公司C",
      "// placeholder: 公司D（最小值）"
    ]
  },
  "series": [
    {
      "type": "bar",
      "barWidth": "55%",
      "label": {
        "show": true,
        "position": "right",
        "fontFamily": "DIN Alternate, Helvetica Neue",
        "fontSize": 11,
        "color": "#333"
      },
      "itemStyle": {
        "color": "// placeholder: function(params) 判断是否为目标公司，是则 #f5a623 高亮，否则 #4a90d9"
      },
      "data": [
        // placeholder: 对应 yAxis.data 顺序的数值数组
      ]
    }
  ]
}
```

---

## 四、图表生成规则

> **用途说明**：以下规则供 Step 6 报告生成时使用。

1. **最低配置要求**：每份 peer-landscape 报告至少包含 1 个定位矩阵 + 1 个辅助图表（雷达/气泡/柱状中选一）。
2. **数据来源**：图表数据从当前对话上下文中 Step 2-5 的结构化摘要获取（对标表、估值表、战略群组等）。
3. **ECharts 版本**：指定 5.x，CDN 引用：
   ```html
   <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
   ```
4. **div id 命名规范**：`chart-<type>-<sector>`，例如：
   - `chart-scatter-semiconductor`（半导体散点图）
   - `chart-radar-liquor`（白酒雷达图）
   - `chart-bubble-newenergy`（新能源气泡图）
   - `chart-bar-pharma`（医药柱状图）
5. **容器样式**：
   ```html
   <div id="chart-scatter-semiconductor" style="width:100%; height:450px;"></div>
   ```
6. **初始化模式**：使用响应式初始化，监听窗口变化自动 resize：
   ```javascript
   const chart = echarts.init(document.getElementById('chart-scatter-semiconductor'));
   window.addEventListener('resize', () => chart.resize());
   ```
7. **数据加载顺序**：先 fetch JSON → 解析 → 设置 option → 渲染，确保数据就绪后再初始化图表。
8. **可访问性**：所有图表必须附带文字说明段落，概述图表结论，供无法加载图表时阅读。

---

## 五、常用轴对速查

以下为分行业推荐的 2x2 定位矩阵轴对，供快速选择。若行业未列出或竞争格局特殊，仍按§一的轴选择原则自行确定。

| 行业 | 推荐 X 轴 | 推荐 Y 轴 | 备选第三维度（气泡） |
|------|-----------|-----------|---------------------|
| 白酒/食品饮料 | 品牌溢价（吨价） | 渠道深度（经销商数） | 市值 |
| 半导体 | 技术节点/品类广度 | 国产替代进度 | 研发投入 |
| 创新药 | 管线丰富度（临床阶段加权） | 商业化能力（销售规模） | 市值 |
| 新能源 | 一体化程度 | 成本优势（单位成本） | 产能规模 |
| 互联网/平台 | 用户规模（MAU） | 变现效率（ARPU） | 营收增速 |
| 银行 | 规模（总资产） | 质量（ROE × 拨备覆盖率） | PB 估值 |
| 物业管理 | 在管面积 | 增值服务收入占比 | 利润率 |
| 消费电子 | 品类宽度 | 单品 ASP | 出货量增速 |
| 券商 | 经纪市占率 | 自营/资管收入占比 | ROE |
| CXO | 在手订单规模 | 海外收入占比 | 产能利用率 |

使用说明：
- 表中推荐适用于"行业内竞争格局定位"场景
- 跨行业对比（如新能源 vs 传统能源）应自行选定可比维度
- 气泡维度仅在选择 bubble 图类型时使用
