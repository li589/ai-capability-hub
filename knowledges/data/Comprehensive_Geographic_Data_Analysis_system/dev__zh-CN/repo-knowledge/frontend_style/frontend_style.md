---
kind: "repo_knowledge"
category: "frontend_style"
title: "前端样式系统：Vue 3 + Vite + MapLibre/Cesium 地理可视化风格"
scopes: ["**"]
updated_at: "2026-07-29T19:24:43Z"
---

# 前端样式系统：Vue 3 + Vite + MapLibre/Cesium 地理可视化风格

## 样式系统与架构

该项目的 `Code/frontend` 目录是一个基于 **Vue 3 + TypeScript + Vite** 的前端工程，采用现代前端技术栈进行地理数据可视化开发。

### 核心技术栈
- **框架**: Vue 3.5.34 + TypeScript 6.0.2
- **构建工具**: Vite 8.0.12
- **状态管理**: Pinia 3.0.4
- **路由**: Vue Router 5.1.0
- **地图引擎**: MapLibre GL 5.24.0（矢量瓦片）+ Cesium 1.142.0（三维地球）
- **代码质量**: ESLint 10.7.0 + Prettier 3.9.5

### 样式方法论
从依赖配置可以看出项目主要使用 **原生 CSS/SCSS** 进行样式开发，未引入 Tailwind CSS、Styled Components 等原子化或 CSS-in-JS 方案。项目结构遵循 Vue 单文件组件的 `<style>` 标签约定。

### 地理可视化特色
项目专注于地理空间数据展示，核心视觉元素包括：
- **MapLibre GL** 用于二维矢量地图渲染
- **Cesium** 用于三维地球场景和地形可视化
- **html2canvas + jsPDF** 支持地图截图和报告导出功能
- **proj4** 处理坐标系统转换

### 构建与优化
Vite 配置中针对大型地理库进行了分包优化：
- `vendor-maplibre`: MapLibre 独立打包
- `vendor-html2canvas`: 截图功能独立
- `vendor-jspdf`: PDF 生成独立
- `vendor-framework`: Vue/Pinia 框架共享

### 开发规范
- 使用 `@` 别名指向 `src` 目录
- 通过环境变量 `VITE_API_BASE_URL` 配置后端接口地址
- 开发时通过 Vite proxy 代理所有 API 请求
- 代码格式统一由 Prettier 管理，支持 TS/TSX/Vue/JS/CSS/SCSS

### 设计约束
由于是地理数据分析平台，样式设计需要重点考虑：
- 地图容器的全屏显示需求
- 图层控制面板的交互设计
- 大数据量渲染的性能优化
- 多坐标系显示的准确性

该项目尚未发现统一的 UI 组件库或设计令牌系统，样式实现相对分散在各组件中。
