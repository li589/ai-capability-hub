---
description: "CGDA 跨平台一键启动器（CLI Launcher）：CGDA 项目的跨平台 CLI 启动器，提供 start/stop/status/restart/logs/sync/flush/reset-db 等子命令，统一管理 Docker 基础设施、Celery Worker/Beat…"
module_id: "atlas:2406c4e4fe6692eb82c2d378c83a6214"
updated_at: "2026-07-29T19:22:00Z"
---

# CGDA 跨平台一键启动器（CLI Launcher）

## 概述 <!-- category:overview -->
CGDA 项目的跨平台 CLI 启动器，提供 start/stop/status/restart/logs/sync/flush/reset-db 等子命令，统一管理 Docker 基础设施、Celery Worker/Beat、FastAPI 后端与前端 Vite 开发服务器的生命周期。

## 架构设计 <!-- category:architecture_design -->
模块由 `launch/__init__.py` 作为包入口，将 `main()` 委托给 `cli.py` 中的 argparse 解析器与命令分发器。整体采用「入口层 → 命令实现层 → 基础设施层」的单向依赖结构：
- `cli.py` 仅负责构建 argparse 子命令树并调用 `commands.py` 中的 `cmd_*` 函数。
- `commands.py` 是业务编排层，组合调用 `docker_manager`（Docker Compose 栈）、`process_manager`（子进程生命周期）、`subprocess_utils`（跨平台工具）、`debug_utils`（诊断）和 `logging_setup`（日志单例）。
- `constants.py` 集中所有路径常量、服务定义（7 个 Celery Worker 队列）与默认值，被其他模块只读引用。
- `logging_setup.py` 提供全局 `log` 单例，统一彩色控制台输出与轮转文件写入。
- 依赖方向严格单向：`cli → commands → {docker_manager, process_manager, subprocess_utils, debug_utils, logging_setup, constants}`，无反向依赖。

## 技术栈 <!-- category:tech_stack -->
纯 Python 标准库实现（argparse、subprocess、logging、signal、pathlib），通过 `docker compose` 管理 Redis/MinIO/Open-Meteo 容器；前端通过 Node.js/npx/pnpm 启动 Vite 开发服务器；Windows 下使用 CREATE_NO_WINDOW 隐藏控制台窗口，Linux/macOS 使用 `tail -f` 跟踪日志。

## 编码规范 <!-- category:coding_conventions -->
- 每个 CLI 子命令对应 `commands.py` 中一个 `cmd_<name>(args) -> int` 函数，返回退出码，由 `cli._dispatch` 按字符串映射分派。
- 所有外部进程调用统一通过 `subprocess_utils.hidden_kwargs()` 注入 Windows 隐藏窗口参数，避免在调用点重复处理平台差异。
- 日志统一通过 `launch.logging_setup.log` 单例的 `info/warn/error/ok/banner/debug` 方法输出，并按类别（如 'Worker'、'Docker'、'Reset'）区分来源。
- 路径与配置常量全部集中在 `constants.py` 中，其他模块通过 `from launch.constants import ...` 只读引用，禁止硬编码路径。
- 子进程启动前统一调用 `rotate_subprocess_log_if_needed(log_file)` 进行日志轮转，确保 Windows 下 stdout 文件描述符固定时的日志不丢失。
- 需要用户确认的危险操作（flush、reset-db）通过交互式 `input('输入 yes 执行: ')` 配合 `--yes` / `-y` 标志跳过确认。

## 配置与命令 <!-- category:unique_setup_and_commands -->
通过 `python launch.py [command]` 运行，支持 `start`（默认子命令）、`stop`、`status`、`restart`、`logs`、`sync`、`flush`、`reset-db` 等子命令；Windows 还提供 `start.bat` / `stop.bat` 快捷方式，Linux/macOS 提供 `./start.sh` / `./stop.sh`。首次运行会自动创建 `.data` 目录、复制 `data-sync/.env.example` 为 `.env`，并提示安装前端依赖。

## 关系
- **相关**：[项目文档与架构设计](项目文档与架构设计.md)、[地理数据工具与运维脚本集](地理数据工具与运维脚本集.md)
