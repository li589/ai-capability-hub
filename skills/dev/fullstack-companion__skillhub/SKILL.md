---
name: fullstack-companion
description: 全栈开发伴侣 — 自动检测当前项目类型（前端/后端/全栈），路由到对应的开发模式，内置后端开发、前端开发、代码规范三套子流程
---

# 全栈开发伴侣

## 任务定位

这是一个 **自动项目检测 + 开发模式路由** 的入口 skill。

启动后自动分析当前项目类型，引导用户进入正确的开发流程。

内置三套子流程（均为本 skill 的内部资源）：
- `backend-dev.md` — 后端开发流程
- `frontend-dev.md` — 前端开发流程
- `code-style.md` — 前端代码规范（被 frontend-dev 引用）

---

## 第一步：项目类型检测

扫描当前项目根目录，按以下规则判断项目类型：

### 前端项目特征（命中任意一条即判定为前端）

| 检测项 | 文件 / 目录 |
|--------|------------|
| Vue 项目 | `package.json` 含 `vue` 依赖，或存在 `vite.config.ts` / `vue.config.js` |
| React 项目 | `package.json` 含 `react` 依赖，或存在 `next.config.*` |
| 通用前端 | `package.json` 含 `webpack` / `vite` / `rollup` 等构建工具 |
| 纯 Node 前端 | 存在 `src/views/` 或 `src/pages/` 或 `src/components/` 目录 |

### 后端项目特征（命中任意一条即判定为后端）

| 检测项 | 文件 / 目录 |
|--------|------------|
| PHP / Laravel | `composer.json` 存在，或存在 `artisan` 文件，或存在 `routes/api.php` |
| Go / Gin | `go.mod` 存在，或存在 `main.go` |
| Python / Django | `manage.py` 存在，或存在 `requirements.txt` + `wsgi.py` |
| Python / FastAPI | `requirements.txt` 或 `pyproject.toml` 含 `fastapi` |
| Python / Flask | `requirements.txt` 或 `pyproject.toml` 含 `flask` |
| Node / Express | `package.json` 含 `express` 依赖且无前端框架依赖 |
| Node / NestJS | `package.json` 含 `@nestjs/core` |
| Java / Spring | `pom.xml` 或 `build.gradle` 存在 |
| Rust | `Cargo.toml` 存在 |

### 全栈项目特征

同时命中前端和后端特征 → 全栈项目。

### 无法判断

以上规则均未命中 → 询问用户。

---

## 第二步：输出检测结果

向用户展示检测结果，格式如下：

```
项目类型检测结果：

- 项目类型：{前端 / 后端 / 全栈}
- 框架：{Laravel / Vue3 / Go+Gin / ...}
- 检测依据：{命中的特征文件}

即将进入 {对应开发模式}，是否确认？
- 输入 y 或回车确认
- 输入 frontend / backend 手动指定模式
```

等待用户确认后再进入对应流程。

---

## 第三步：路由到对应开发流程

根据检测结果（或用户手动指定），读取本 skill 目录下的对应资源文件并激活：

| 项目类型 | 激活流程 | 资源文件 |
|---------|---------|---------|
| 后端项目 | 后端开发 | 读取 `backend-dev.md`（与本 SKILL.md 同目录） |
| 前端项目 | 前端开发 | 读取 `frontend-dev.md`（与本 SKILL.md 同目录） |
| 全栈项目 | 询问用户本次工作范围，再路由 | — |

### 全栈项目处理

如果检测到全栈项目，额外询问：

> 检测到全栈项目。本次开发聚焦哪个方向？
> 1. 后端开发（进入后端开发流程）
> 2. 前端开发（进入前端开发流程）
> 3. 全栈开发（先后端再前端，顺序执行）

选择全栈开发时：
1. 先执行 `backend-dev.md` 流程，完成后端实现和接口文档
2. 再执行 `frontend-dev.md` 流程，基于刚生成的接口文档实现前端

---

## 第四步：激活目标流程

读取目标资源文件，按照其中定义的流程执行。

从目标流程的第一步开始，完整执行其定义的开发流程。

**前端流程额外说明**：当 `frontend-dev.md` 中提到代码规范 skill 时，默认读取同目录下的 `code-style.md` 作为默认代码规范。

---

## 内部资源说明

本 skill 目录下包含以下资源文件：

| 文件 | 说明 |
|------|------|
| `SKILL.md` | 本文件 — 入口 skill，项目检测与流程路由 |
| `backend-dev.md` | 后端开发流程（需求分析 → 实现 → 接口文档同步） |
| `frontend-dev.md` | 前端开发流程（读取接口文档 → 页面实现） |
| `code-style.md` | 前端代码规范（Vue3 模板 + 文件拆分规范），被 frontend-dev 引用 |
