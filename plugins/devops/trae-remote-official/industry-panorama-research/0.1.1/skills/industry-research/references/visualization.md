# Agent 图文表达规则

研究 Agent 根据已经采用的证据决定是否画图、画什么以及采用哪种结构；发布程序只校验数据并渲染 Agent 写出的结果。每个专题最多包含两个 `chart` 或 `visual` 数据块，没有合适内容时不画。多对象、多字段比较优先使用 Markdown 表格。

## 数值图表

Agent 根据业务关系选择具体类型：

- 时间变化：`purpose: trend`，选择 `type: line` 或 `type: area`。
- 同口径对象比较：`purpose: comparison`，使用 `type: bar`。
- 同一分母构成：`purpose: composition`，合计约为 100% 时使用 `type: donut`，否则使用 `type: bar`。
- 两个可比指标的关系：`purpose: relationship`，使用 `type: scatter`。
- 上下限或情景区间：`purpose: range`，使用 `type: range`。

使用 fenced `chart`：

```text
title: <业务标题>
purpose: trend|comparison|composition|relationship|range
type: line|area|bar|donut|scatter|range
unit: <单位>
period: <时期>
geography: <地域>
property: 实际|跟踪统计|估算|预测|混合
source: [n]
item: <数据行>
```

`trend`、`comparison` 和 `composition` 的数据行为 `item: 对象或时点 | 数值 | 展示值 | 数据性质`。`relationship` 改用 `x-axis`、`x-unit`、`y-axis`、`y-unit`，数据行为 `item: 对象 | X数值 | Y数值 | 展示值 | 数据性质`。`range` 的数据行为 `item: 对象 | 下限 | 上限 | 展示值 | 数据性质`。

所有数值必须在正文或表格中出现并带引用。不同地域、时期、指标、单位、定义或数据性质不能放入同一图。

## 业务结构图

Agent 根据业务关系选择 `timeline`、`chain`、`matrix` 或 `comparison`，使用 fenced `visual`：

```text
type: timeline|chain|matrix|comparison
title: <业务标题>
source: [n]
item: <实际对象> | <已确认信息> | <业务含义>
```

写 2—8 个实际节点，不写表头或占位字段。政策和事件演进用 `timeline`，上下游和影响传导用 `chain`，两个明确维度的定位用 `matrix`，多对象同组事实用 `comparison`。

`snapshot` 只供完整报告撰写步骤在行业概览中使用，每行写 `item: <简短名称> | <数值或状态> | <业务含义及直接引用 [n]>`，保留 2—5 项。
