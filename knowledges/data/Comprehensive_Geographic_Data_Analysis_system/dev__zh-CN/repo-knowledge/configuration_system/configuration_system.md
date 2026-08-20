---
kind: "repo_knowledge"
category: "configuration_system"
title: "CGDA 后端配置系统：环境变量 + Pydantic Settings + 运行时快照投影"
scopes: ["**"]
updated_at: "2026-07-29T19:22:50Z"
---

# CGDA 后端配置系统：环境变量 + Pydantic Settings + 运行时快照投影

## 1. 使用的系统与框架
- **核心框架**：`pydantic-settings`（BaseSettings）用于类型化、可验证的配置模型；主应用使用自定义 `dataclass` + `os.getenv` 的 `Settings` 类，配合 `python-dotenv` 加载 `.env`。
- **配置来源分层**：
  1) `.env` 文件（开发/本地）→ 2) 进程环境变量 → 3) SQLite 数据库持久化覆盖（API Key、运行时开关）→ 4) 进程内运行时快照（RuntimeSnapshot）。
- **前端配置**：Vite 通过 `VITE_API_BASE_URL` 等 `VITE_` 前缀环境变量注入，示例见 `Code/frontend/.env.example`。

## 2. 关键文件与包
- `Code/backend/app/core/config.py` — 定义 `Settings` dataclass，集中所有 `BACKEND_*` 环境变量映射，默认值与路径解析。
- `Code/backend/.env.example` — 完整的环境变量清单（GEE、天气、存储、队列、Celery、SSH、Earthdata 等），实际部署时复制为 `.env`。
- `Code/backend/app/services/effective_config.py` — 运行时配置投影层：启动时从 DB 合并 API Key 与 runtime overrides，生成不可变 `RuntimeSnapshot`，提供 `get_effective_secret()`、`get_weather_cache_ttl_seconds()` 等统一读取接口。
- `Code/backend/app/services/config_service.py` — API Key 管理、DB 读写、与 `effective_config` 同步的桥接服务。
- `Code/backend/app/main.py` — FastAPI 入口，在 `lifespan` 中调用 `hydrate_effective_config()` 完成配置热初始化。
- `Code/frontend/.env.example` — 前端 Vite 环境变量示例。
- `launch/env_python.py` — 强制使用仓库内置 `Env/Python312` 解释器，避免环境不一致导致的配置/依赖差异。

## 3. 架构与设计约定
- **单一配置入口**：业务代码应通过 `app.services.effective_config` 获取运行时值，而非直接读 `os.environ` 或 `settings`，保证 DB 覆盖与加密策略生效。
- **冷启动加载**：`.env` 由 `load_dotenv` 在 `config.py` 模块导入时加载；FastAPI lifespan 中再执行 `hydrate_effective_config()` 将 DB 中的 API Key 与 runtime overrides 投影到内存快照。
- **加密策略**：非 development 环境必须设置 `BACKEND_GEE_CREDENTIALS_ENCRYPTION_KEY`，否则 `assert_encryption_policy()` 会 fail-fast 阻止启动。
- **配置项命名规范**：所有后端配置以 `BACKEND_` 前缀开头（如 `BACKEND_DATA_ROOT`、`BACKEND_MINIO_ENDPOINT`、`BACKEND_WORKFLOW_EXECUTOR`），便于区分于算法侧 `CGDA_*` 环境变量。
- **路径与运行时目录**：默认运行时根为 `I:\Geograph_DataSet\_runtime`，可通过 `BACKEND_RUNTIME_ROOT` 覆盖，子目录包括 `workflow_state`、`logs`、`artifacts`、`cache`、`python_provider`、`gee` 等。
- **多组件共享配置**：GEE 引擎、天气工作流、Provider 工作流、下载链、底图代理、Celery、SSH 等子系统均通过同一份 `Settings` 与环境变量驱动，保持配置一致性。

## 4. 开发者应遵循的规则
- **新增配置项**：在 `app/core/config.py` 的 `Settings` dataclass 中添加字段，提供合理的默认值，并在 `.env.example` 中补充注释说明。
- **读取配置**：优先使用 `app.services.effective_config` 提供的 getter（如 `get_effective_secret()`、`get_weather_cache_ttl_seconds()`），避免绕过 DB 覆盖。
- **敏感信息**：不要硬编码密钥；通过 `BACKEND_*_API_KEY` 环境变量或 DB 的 API Key 管理接口注入，生产环境必须启用加密。
- **前端配置**：仅使用 `VITE_` 前缀的环境变量，并通过 `vite.config.ts` 的 proxy 转发到后端，不直接暴露后端地址给浏览器。
- **环境隔离**：开发/测试/生产通过 `BACKEND_ENV` 区分，非开发环境缺少加密 key 时禁止启动，防止明文存储凭据。
- **路径配置**：数据根、输出根、缓存目录等路径必须通过环境变量显式设置，不得使用相对路径或硬编码绝对路径。
