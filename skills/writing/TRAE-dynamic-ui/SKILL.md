---
name: TRAE-dynamic-ui
user-invocable: true
disable-model-invocation: false
description: 动态 UI 渲染技能 — 通过 PureShowWidget 工具生成可视化内容，支持两种模式：inline（对话流内紧凑可视化）和 panel（独立面板大型可视化）。触发条件：用户要求图表、可视化、报告、对比、看板，或提到动态UI/图表/可视化。当用户要求构建独立网站、Web 应用或生成 HTML 文件时，请勿触发。
---

# TRAE-dynamic-ui — Dynamic Visual Rendering

## File Paths

`c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui` 代表本 `SKILL.md` 文件所在的目录，即当前 Skill 被安装到的实际路径。

无论本 Skill 安装在何处，请务必根据 `SKILL.md` 文件的绝对路径推导内部资源的绝对路径来读取。

```
c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/
├── SKILL.md                              ← 本文件
├── references/
│   ├── design-system.md                  ← 色彩/字体/组件规范（必读）
│   ├── inline-mode.md                    ← inline 模式规则
│   ├── panel-mode.md                     ← panel 模式规则
│   ├── svg-guide.md                      ← SVG 绘图指南
│   └── chart-guide.md                    ← 图表指南
└── examples/
    ├── INDEX.md                          ← 场景索引（必读）
    ├── 01-exploration-approaches.html    ← 多方案探索
    ├── 02-exploration-visual-directions.html ← 视觉方向探索
    ├── 03-implementation-plan.html       ← 实现计划
    ├── 04-code-review-pr.html            ← PR 注释审查
    ├── 05-code-review-writeup.html       ← PR 说明文档
    ├── 06-module-map.html                ← 模块架构图
    ├── 07-prototype-animation.html       ← 动画原型
    ├── 08-prototype-interaction.html     ← 交互原型
    ├── 09-svg-illustrations.html         ← SVG 技术插图
    ├── 10-flowchart.html                 ← 流程图
    ├── 11-slide-deck.html                ← 幻灯片
    ├── 12-feature-explainer.html         ← 功能解释器
    ├── 13-concept-explainer.html         ← 概念教学
    ├── 14-status-report.html             ← 周报/状态
    ├── 15-incident-timeline.html         ← 事故复盘
    ├── 16-triage-board.html              ← 工单分诊看板
    ├── 17-feature-flags.html             ← Feature Flag 编辑器
    ├── 18-prompt-tuner.html              ← Prompt 调优器
    ├── 19-metrics-dashboard.html         ← 监控仪表盘
    └── 20-comparison-matrix.html         ← 技术方案对比
```

## Scope

This skill renders visuals via the `PureShowWidget` tool. It is NOT for:
- Building standalone web pages, websites, or web apps
- Creating full HTML projects or landing pages
- Generating HTML files to disk
- Scaffolding frontend projects

**Rule of thumb**: if the intent is a *deliverable web project*, do NOT use this skill. If the intent is a *visual explanation or interactive widget* alongside chat, use this skill.

## Tool Binding

**You MUST call the `PureShowWidget` tool** to output visual content. Parameters:

- `mode`: `"inline"` (default) or `"panel"`
- `loading_messages`: 1-4 short messages shown during render
- `title`: snake_case identifier for this visual
- `widget_code`: SVG or HTML code to render

### ⚠️ Streaming Output Order (Hard Rule)

`widget_code` 内容按 token 逐步流式渲染。**必须严格按以下顺序输出**：

1. **`<style>` 块最先输出** — 确保样式在内容出现前已就绪
2. **HTML 内容** — 有了样式，内容一出现就是正确的视觉效果
3. **`<script>` 最后输出** — 脚本放在末尾，不阻塞视觉渲染

违反此顺序会导致流式渲染时内容先以无样式状态闪烁，体验极差。**任何模式下（inline / panel）都必须遵守。**

### ⚠️ Event Binding (Hard Rule)

**Never bind the same event on an element twice** — pick ONE approach and stick with it:
- Either use `onclick` attribute on the HTML element (no `<script>` needed), OR
- Use `addEventListener` inside a `<script>` block (no `onclick` attribute on elements).

The rendering engine injects HTML via `innerHTML` then re-executes `<script>` blocks separately. If you use BOTH `onclick` AND `addEventListener` on the same element, the handler fires twice — e.g., `classList.toggle('open')` toggles on then immediately off, producing zero visible effect.

**Recommended**: Use `addEventListener` in a single `<script>` block at the end (cleaner separation of structure and behavior).

## Mode Routing

Choose mode based on user intent and content complexity:

### → Inline Mode

**When to use**:
- Simple flowcharts (≤5 nodes)
- Architecture overview diagrams
- Data cards (2-4 KPIs)
- Small SVG illustrations
- Interactive control demos
- Estimated HTML <100 lines

**Characteristics**: Compact, height-limited, streaming-friendly, mixed with text.

**Call**: `PureShowWidget(mode="inline", ...)`

→ **必须全文读取** `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/design-system.md` + `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/inline-mode.md`
→ If SVG diagram, also load `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/svg-guide.md`
→ If chart/map, also load `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/chart-guide.md`

### → Panel Mode

**When to use**:
- Multi-option comparison (3+ choices side by side)
- Status reports / weekly reviews (KPI + charts + timeline)
- Kanban / editors (drag-and-drop, exportable)
- Code review annotations (multi-file diff + comments)
- Concept explainers (multi-section + interactive demos)
- Dashboards (multi-chart coordination)
- Any content requiring scroll, multiple regions, or complex interaction
- Estimated HTML >200 lines

**Characteristics**: No height limit, multi-section layout, complex scripts, exportable.

**Call**: `PureShowWidget(mode="panel", ...)`

→ **必须全文读取** `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/design-system.md` + `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/panel-mode.md`
→ If charts, also load `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/chart-guide.md`

## Routing Decision Table

| Signal | → Mode |
|--------|--------|
| Estimated HTML <100 lines | inline |
| Estimated HTML >200 lines | panel |
| Needs scrolling to view | panel |
| Multiple sections/regions | panel |
| Has export functionality | panel |
| Pure SVG illustration | inline |
| "Make a report/kanban/comparison" | panel |
| "Draw a diagram/flowchart" | inline |
| 100-200 lines gray zone | Prefer inline, unless scroll/multi-region needed |

## Before You Start — Always Check Examples First

**Every widget you create should be informed by a reference example.** The examples show proven layout patterns, color usage, and interaction techniques. Do not start from scratch.

### Workflow

1. **必须全文读取** `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/design-system.md`，将其作为色彩与排版规范加载到上下文，严格遵守。
2. **必须全文读取** `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/examples/INDEX.md`，匹配当前场景对应的 1-2 个最相近示例。
3. **读取匹配的示例文件**（如 `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/examples/01-status-report.html`）— 研究其 CSS 结构、grid 布局、色彩分配和签名元素（eyebrow、pills、accent bars）。
4. **根据 Mode Routing 结果加载模式规则**：`c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/inline-mode.md` 或 `c:\Users\likr\.trae-cn\builtin_skills\TRAE-dynamic-ui/references/panel-mode.md`。
5. **生成 Widget** — 采用相同的结构手法，为用户请求填充全新内容。

### What to learn from examples

- **Layout**: grid columns, flex patterns, max-width, padding rhythm
- **Color assignment**: how categories map to color ramps (sky=primary, mint=success, coral=error, amber=warning)
- **Signature elements**: eyebrow labels, accent bars, status pills, metric cards with large colored numbers
- **Interaction**: hover states, click handlers, animations, export buttons
- **Typography**: serif for titles, mono for eyebrows/code, sans for body. Only 400 and 600 weights.

### Minimum visual quality bar

Every widget MUST have:
- At least 1 non-gray color ramp applied meaningfully
- Eyebrow label on the first section (mono 11px uppercase)
- Proper hierarchy: serif title > sans body > mono metadata
- Cards/panels with `var(--color-background-primary)` + border + rounded corners

**If your output looks like plain monochrome text in boxes, it fails the bar. Add color, add rhythm, add visual signatures.**
