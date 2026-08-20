---
description: "CGDA 综合地理数据分析平台根目录：CGDA 平台的仓库根，提供跨平台一键启动器、后端辅助脚本与文档/工具/环境等子模块的统一入口与编排约定。"
module_id: "atlas:3be1c3841a8ab64ee8e5a5ec5e59eb49"
updated_at: "2026-07-29T19:22:32Z"
---

# CGDA 综合地理数据分析平台根目录

## 概述 <!-- category:overview -->
CGDA 平台的仓库根，提供跨平台一键启动器、后端辅助脚本与文档/工具/环境等子模块的统一入口与编排约定。

## 架构设计 <!-- category:architecture_design -->
根目录作为整个 CGDA 项目的统一入口层：`launch.py` 是跨平台薄入口，负责强制切换到 `Env/Python312` 解释器并委托给 `launch.cli.main`；`start.bat/start.sh` 与 `stop.bat/stop.sh` 是平台特定的推荐启动/停止脚本；`start_backend.py` 专门用于以正确 `sys.path` 直接运行 FastAPI 后端（uvicorn）。项目结构按职责分层——`Code/backend`（FastAPI + Celery）、`Code/frontend`（Vue 3 + Vite）、`Code/algorithms`（算法包）、`Code/shared`（共享契约）、`Code/infra`（数据面 compose）以及顶层的 `Doc/`、`Tools/`、`Example/`、`Env/Python312/` 运行时，所有子模块通过 `launch.py` 的命令体系（start/stop/status/restart/logs/sync/flush/reset-db）统一编排生命周期。

## 技术栈 <!-- category:tech_stack -->
Python 3.12（强制使用 `Env/Python312` 解释器）、FastAPI + Uvicorn、Celery + Redis、MinIO、Docker Compose、Vite（前端）、MapLibre GL JS / CesiumJS（地图渲染）。

## 编码规范 <!-- category:coding_conventions -->
- 所有子命令通过 `launch.py` 统一暴露，禁止绕过启动器直接调用各组件
- 严格使用 `Env/Python312` 解释器，禁止依赖系统 PATH 中的 python
- Windows 与 Linux/macOS 通过成对的 `.bat` / `.sh` 脚本保持跨平台一致性
- 代码按职责分层存放于 `Code/{frontend,backend,algorithms,shared,infra}`，顶层仅保留入口脚本与文档

## 配置与命令 <!-- category:unique_setup_and_commands -->
本地联调唯一 Python 解释器为 `Env/Python312`；Windows 推荐 `start.bat` / `stop.bat`，Linux/macOS 推荐 `./start.sh` / `./stop.sh`；也可直接调用 `python launch.py start|stop|status|restart|logs|sync|flush|reset-db`。
