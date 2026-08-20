---
description: "旱涝急转滑坡研究汇报幻灯片（Hyper-TCDF）：基于单文件 HTML 的学术汇报演示文稿，展示 Hyper-TCDF 框架在旱涝急转诱发滑坡时滞因果机制识别中的意大利实证与全球扩展成果。"
module_id: "atlas:544576cf579220419c62e282692b3192"
updated_at: "2026-07-30T06:32:58Z"
---

# 旱涝急转滑坡研究汇报幻灯片（Hyper-TCDF）

## 概述 <!-- category:overview -->
基于单文件 HTML 的学术汇报演示文稿，展示 Hyper-TCDF 框架在旱涝急转诱发滑坡时滞因果机制识别中的意大利实证与全球扩展成果。

## 架构设计 <!-- category:architecture_design -->
单一入口 `dwaa-landslide-briefing.html` 承载全部 21 张幻灯片（`<section class="slide">`），通过 `_shared/runtime.js` 提供零依赖的键盘导航、滚动模式、演讲者视图（弹出窗口 + BroadcastChannel 同步）、主题切换、编辑模式等运行时能力；图表渲染由 `_shared/echarts.min.js` 配合内联 `echarts-theme-sync.js` 完成，ECharts 实例通过 `window.__deckECharts.register()` 注册并随主题变量动态配色。动画系统分层：`_shared/animations/animations.css` + `fx-runtime.js` 负责 CSS 入场动画与 Canvas FX 插件的动态加载/生命周期管理；主题通过 `<link id="theme-link">` 指向 `_shared/themes/scholar-teal.css`，CSS 变量驱动全局配色。资源按职责划分：`assets/` 存放论文原图与封面背景，`_shared/` 为跨页面共享的样式、字体、高亮语法、ECharts 库与运行时。依赖方向单向：HTML → runtime.js / echarts / animations → 主题 CSS 与静态资源，无反向依赖。

## 技术栈 <!-- category:tech_stack -->
纯前端单页应用：原生 JavaScript（零依赖）+ CSS3 动画 + ECharts 5（UMD）用于交互式图表；BroadcastChannel API 实现主窗口与演讲者弹窗的双向同步；Canvas 2D 用于粒子/FX 特效；主题系统基于 CSS 自定义属性（`--accent`、`--surface` 等）与 `data-theme` 属性切换。

## 编码规范 <!-- category:coding_conventions -->
- 每张幻灯片以 `<section class="slide" data-title="...">` 包裹，标题文本同时用于导航缩略图和演讲者视图元数据。
- 幻灯片内嵌 `<div class="notes">` 存放演讲者逐字稿，runtime 自动提取并注入到 notes overlay 或演讲者弹窗。
- 图表初始化统一使用 `addEventListener('DOMContentLoaded', ...)` 检查 `window.echarts` 存在后创建实例，并通过 `window.__deckECharts.register(chart, fn)` 注册主题回调。
- 交互组件（翻转卡片、模块标签、图表切换）通过内联 `<script>` 块绑定事件，使用 `classList.toggle('is-active')` 切换状态而非重新渲染。
- CSS 变量命名遵循 `--text-*`、`--accent*`、`--surface`、`--border`、`--radius`、`--shadow` 等语义化前缀，主题切换仅替换 CSS 文件而不改动业务样式。
- 图片统一用 `.fig-wrap` 容器包裹，配 `.fig-cap` 说明文字，保持统一的圆角、阴影与响应式缩放行为。

## 配置与命令 <!-- category:unique_setup_and_commands -->
直接双击 `dwaa-landslide-briefing.html` 在浏览器中打开即可运行；按 F 进入全屏翻页模式，S 打开演讲者视图（弹出窗口含当前/下一页预览、逐字稿、计时器），N 显示备注覆盖层，O 生成缩略图概览，T 循环切换主题，E 进入内容可编辑模式，URL 支持 `#/N` 深链跳转与 `?preview=N` 预览模式。
