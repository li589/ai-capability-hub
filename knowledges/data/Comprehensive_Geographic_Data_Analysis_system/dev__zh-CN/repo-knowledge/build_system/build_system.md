---
kind: "repo_knowledge"
category: "build_system"
title: "CGDA 跨平台构建与发布系统"
scopes: ["**"]
updated_at: "2026-07-29T19:24:14Z"
---

# CGDA 跨平台构建与发布系统

## 构建系统与工具链概览

CGDA 项目采用**多语言、多组件**的混合构建体系，通过 Python 编写的跨平台启动器统一管理后端（FastAPI + Celery）、前端（Vue 3 + Vite）和 Docker 基础设施的生命周期。构建流程由 GitHub Actions CI 驱动，pre-commit 钩子在本地保证代码质量。

### 核心构建工具
- **Python 环境**: 强制使用仓库内 `Env/Python312`，通过 `launch.py` 自动切换解释器
- **前端构建**: Vite 8 + Vue 3.5 + TypeScript 6.0，npm 包管理器锁定版本
- **容器编排**: Docker Compose 管理 Redis、MinIO、Open-Meteo 服务
- **CI/CD**: GitHub Actions 执行 pre-commit、pytest、vitest、OpenAPI 契约检查

### 关键构建文件与职责

**入口脚本层**
- `launch.py`: 跨平台启动器薄入口，处理 Windows UTF-8 编码和 Python 环境切换
- `start.sh`/`stop.sh`: Unix 平台的一键启动/停止脚本
- `start.bat`/`stop.bat`: Windows 平台的对应脚本

**命令实现层** (`launch/` 包)
- `commands.py`: 所有 CLI 子命令实现 (start/stop/status/restart/logs/sync/flush/reset-db)
- `docker_manager.py`: Docker 容器生命周期管理
- `process_manager.py`: 进程监控和管理 (FastAPI、Celery Workers、Frontend)
- `subprocess_utils.py`: 跨平台子进程操作工具

**依赖管理**
- `Code/backend/requirements.txt`: Python 依赖锁定 (FastAPI 0.116.1, Celery 5.4.0, MinIO 7.2.7)
- `Code/frontend/package.json`: Node.js 依赖锁定 (Node >=22 <23, npm >=10)
- `.pre-commit-config.yaml`: 统一的代码质量钩子配置

### 构建流水线架构

**本地开发流程**:
```bash
./start.sh                    # 启动全部服务
./start.sh start docker       # 仅启动 Docker 基础设施
./start.sh start fastapi      # 仅启动后端 API
./start.sh start frontend     # 仅启动前端开发服务器
./start.sh stop               # 停止所有服务
```

**CI 流水线** (`github/workflows/ci.yml`):
1. **pre-commit**: 全量代码检查和格式化
2. **pytest**: 后端单元测试 (Redis 服务依赖)
3. **vitest**: 前端单元测试
4. **check:openapi**: 前后端接口契约漂移检测

### 容器化架构

**运行栈** (`Code/backend/docker-compose.yml`):
- `redis:7-alpine`: Celery 消息代理和缓存
- `minio/minio:latest`: 对象存储 (端口 9100/9101)
- `cgda-open-meteo`: 气象数据 API (端口 8080)
- `minio-init`: 初始化存储桶和权限

**数据同步** (`Code/infra/data-sync/`):
- 独立的 Docker Compose 配置，用于一次性数据下载任务
- 支持 PowerShell 和 Shell 脚本，跨平台兼容

### 代码质量与类型检查

**Python 静态分析**:
- Ruff: 代码检查和格式化 (v0.5.0)
- MyPy: 类型检查 (宽松模式，逐步收紧)
- 配置文件: `ruff.toml`, `Code/backend/mypy.ini`

**前端代码质量**:
- ESLint + TypeScript ESLint: 代码检查
- Prettier: 代码格式化
- Vitest: 单元测试框架

### 开发者约定与约束

**环境要求**:
- 必须使用仓库内 `Env/Python312` (Windows: `Env\Python312\python.exe`)
- Node.js 版本锁定在 `>=22 <23`
- Docker Desktop 或 Docker Engine

**提交前检查**:
- pre-commit 自动运行 ruff、mypy、eslint、prettier
- Conventional Commits 规范 (feat/fix/refactor/perf/chore/docs/test/style/build/ci)
- 禁止提交 >1MB 的文件
- 检测私钥等敏感信息

**构建产物**:
- 前端: `Code/frontend/dist/` (Vite 构建输出)
- 日志: `logs/` 目录 (按组件分离)
- 缓存: `Code/backend/.data/cache/` (天气数据和计算缓存)
- 工作流状态: `.data/workflow_state/` (SQLite 数据库)

### 特殊构建特性

**OpenAPI 契约管理**:
- 后端自动生成 OpenAPI schema
- 前端通过 `openapi-typescript` 生成类型定义
- CI 中执行契约漂移检测，防止前后端接口不一致

**工作流引擎初始化**:
- `reset-db` 命令支持清空运行时状态并重新 seed 系统工作流
- 自动创建带时间戳的快照备份
- 支持保留用户自定义工作流或完全重置

**跨平台兼容性**:
- Python 启动器自动处理 Windows/Linux/macOS 差异
- Docker Compose 统一容器化依赖
- PowerShell 和 Shell 脚本双支持
