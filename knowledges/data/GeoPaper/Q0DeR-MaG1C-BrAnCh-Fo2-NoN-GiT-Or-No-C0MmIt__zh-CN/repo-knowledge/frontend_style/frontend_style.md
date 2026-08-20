---
kind: "repo_knowledge"
category: "frontend_style"
title: "学术汇报幻灯片前端样式系统（HTML+CSS主题化）"
scopes: ["**"]
updated_at: "2026-07-30T06:36:14Z"
---

# 学术汇报幻灯片前端样式系统（HTML+CSS主题化）

该仓库的前端样式系统是一个基于单文件 HTML 的学术汇报演示文稿框架，采用纯 CSS + 少量 JavaScript 实现，无需构建工具。核心特点如下：

**1. 样式架构与主题系统**
- 基础样式集中在 `_shared/base.css`，定义了完整的 CSS 变量设计令牌（design tokens），包括颜色（--bg, --accent, --text-*）、字体（--font-sans, --font-serif, --font-mono）、圆角、阴影等
- 主题通过独立的 CSS 文件覆盖 `:root` 变量实现，当前提供 `scholar-teal.css`（学者青主题），通过 `<html data-theme>` 和 `<link id="theme-link">` 动态切换
- 装饰效果集中在 `_shared/decorations.css`，提供扫描线、网格、光晕、渐变背景等氛围效果类
- 字体统一通过 `_shared/fonts.css` 从 Google Fonts 加载 Inter、Noto Sans SC、JetBrains Mono 等

**2. 演示文稿引擎**
- 使用 `.deck` + `.slide` 结构实现全屏幻灯片切换，支持键盘导航（左右箭头）
- 内置动画系统（`animations.css`），包含淡入、滑入、渐变色流动等效果
- 支持演讲者视图（Notes Overlay）、缩略图概览（Overview）、进度条等高级功能
- 提供滚动模式（scroll-mode）用于竖屏展示，所有 slide 依次排列并缩放适配视口

**3. 组件化 UI 体系**
- 排版系统：eyebrow、kicker、h1-h4、lede、dim 等语义化文本类
- 布局原语：stack、row、grid、center、fill 等 Flex/Grid 实用类
- 图表组件：flow（流程图）、arch（架构图）、mm（思维导图）、steps（步骤）、timeline（时间轴）
- 数据展示：table、spec-layout（技术规格）、ledger（账本式数据）、matrix（矩阵网格）
- 卡片系统：card、glass-card（毛玻璃）、macaron-grid（马卡龙色块）、plat（平台卡片）

**4. 响应式与打印支持**
- 针对超宽屏（≥2200px）优化字号和内边距，增强投影聚焦感
- 内置 print 媒体查询，打印时隐藏导航元素，每页强制分页
- 移动端通过 `@media (max-width: 900px)` 隐藏侧边栏 TOC

**5. 项目约定**
- 所有演示页面遵循 `_shared/` 目录共享资源约定
- 图片资源统一放在 `assets/` 目录，命名规范为 `fig_*.jpeg`
- 每个 HTML 文件独立完整，可直接浏览器打开运行
- 讲稿文档（dwaa-landslide-script.html）采用独立样式，与演示文稿分离
