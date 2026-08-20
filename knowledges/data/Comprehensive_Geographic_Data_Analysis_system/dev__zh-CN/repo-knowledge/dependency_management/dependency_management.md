---
kind: "repo_knowledge"
category: "dependency_management"
title: "Python/Node.js 依赖管理与版本锁定策略"
scopes: ["**"]
updated_at: "2026-07-29T19:23:05Z"
---

# Python/Node.js 依赖管理与版本锁定策略

## 1. 使用的系统与工具
- **后端（Python）**：使用 `pip` + `requirements.txt` / `requirements-dev.txt` 声明依赖，无 `pyproject.toml`、`poetry`、`conda` 或 `venv` 锁定文件。
- **前端（Node.js/Vue）**：使用 `npm`（`package.json` + `package-lock.json`），通过 `.npmrc` 显式启用 `legacy-peer-deps=true` 以兼容 peer 冲突。
- **CI**：`.github/workflows/ci.yml` 中分别对 Python 和 Node.js 执行 `pip install -r requirements-dev.txt` 与 `npm ci`，确保可重现构建。
- **容器化**：`Code/backend/docker-compose.yml` 定义 Redis、MinIO、Open-Meteo 等运行时服务镜像版本，作为“基础设施依赖”的版本管理。

## 2. 关键文件与位置
- `Code/backend/requirements.txt` — 生产运行时依赖（FastAPI、Celery、MinIO、GDAL/NetCDF 系列等）
- `Code/backend/requirements-dev.txt` — 开发期依赖（mypy、ruff、pre-commit），通过 `-r requirements.txt` 包含生产依赖
- `Code/frontend/package.json` — 前端依赖声明（Vue3、Cesium、MapLibre、Vite、TypeScript 等）
- `Code/frontend/package-lock.json` — npm 依赖树锁定文件（lockfileVersion 3）
- `Code/frontend/.npmrc` — 强制 `legacy-peer-deps=true` 解决 TypeScript 6.x 与 openapi-typescript 7.x 的 peer 冲突
- `.github/workflows/ci.yml` — CI 中安装 Python 与 Node.js 依赖的步骤
- `Code/backend/docker-compose.yml` — 运行时服务镜像版本（redis:7-alpine、minio/minio:latest、自定义 Open-Meteo 镜像）
- `Code/backend/.env.example` — 运行时配置（GEE、Weather Engine、Open-Meteo、远程存储等）

## 3. 架构与约定
- **前后端依赖分离**：Python 依赖集中在 `Code/backend/`，Node.js 依赖集中在 `Code/frontend/`，互不干扰。
- **开发与生产依赖解耦**：`requirements-dev.txt` 通过 `-r requirements.txt` 引用生产依赖，避免重复声明，同时保持生产镜像精简。
- **版本锁定策略**：
  - Python：未使用 `pip freeze` 生成 `*.txt` 锁定文件，仅用 `==` 精确 pin 核心包（如 `fastapi==0.116.1`、`celery[redis]==5.4.0`），其余使用 `>=` 宽松约束。
  - Node.js：使用 `package-lock.json` 完整锁定依赖树，配合 `npm ci` 保证 CI 与本地一致。
- **私有/本地包**：前端通过 `file:datapool-guangdong.geojson-1.0.1.tgz` 引入本地 tgz 包，适合团队内共享 GeoJSON 数据。
- **基础设施即依赖**：Docker Compose 中的镜像版本（如 `redis:7-alpine`、`minio/minio:latest`）作为外部依赖的版本来源。

## 4. 开发者应遵循的规则
- **新增依赖时**：
  - Python 依赖添加到 `requirements.txt`（生产）或 `requirements-dev.txt`（开发工具），优先使用 `==` 精确版本，避免 `>=` 导致的不确定性。
  - Node.js 依赖通过 `npm install --save` 更新 `package.json` 和 `package-lock.json`，禁止手动修改 lock 文件。
- **peer 依赖冲突**：前端已全局启用 `legacy-peer-deps=true`，无需在每次安装时加 `--legacy-peer-deps`。
- **CI 一致性**：所有环境必须能通过 `.github/workflows/ci.yml` 中的安装命令，禁止绕过 `requirements-dev.txt` 或 `package-lock.json`。
- **私有包管理**：本地 tgz 包需随代码提交，确保其他开发者可直接 `npm ci` 安装。
- **环境变量安全**：敏感配置（如 GEE 密钥、MinIO 凭据）通过 `.env` 文件注入，不得硬编码到代码或依赖文件中。
- **镜像版本更新**：Docker Compose 中的镜像版本应由运维统一维护，避免随意升级导致运行时行为变化。

