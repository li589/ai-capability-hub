---
kind: "repo_knowledge"
category: "logging_system"
title: "CGDA 平台日志系统：结构化 JSON 日志与双端输出"
scopes: ["**"]
updated_at: "2026-07-29T19:23:30Z"
---

# CGDA 平台日志系统：结构化 JSON 日志与双端输出

## 1. 使用的系统与框架
- 后端（FastAPI）：基于 Python 标准库 logging，自定义 StructuredJsonFormatter 输出结构化 JSON 日志，通过 RotatingFileHandler 实现文件轮转。
- 启动器（launch/）：独立封装的 Log 类，提供彩色控制台输出 + 轮转文件写入，用于 CLI 启动器自身日志。
- 算法模块：各 Provider 算法直接使用 logging.getLogger(__name__)，遵循标准 logger 命名空间约定。

## 2. 核心文件与位置
- Code/backend/app/core/logging.py — 后端结构化日志配置、ContextVar 上下文传播、JSON Formatter
- launch/logging_setup.py — 启动器专用日志（彩色 TTY + RotatingFileHandler）
- launch/constants.py — 启动器日志路径与轮转阈值常量
- Code/backend/app/main.py — FastAPI 应用入口，初始化日志并注入 request_id 中间件
- Code/backend/app/core/config.py — Settings 数据类，包含 log_dir、log_level 等日志相关配置项

## 3. 架构与设计决策
### 后端结构化日志
- 统一入口：configure_logging() 在应用启动时调用一次，设置 root logger 级别、清空 handlers、添加 console + file 两个 handler。
- JSON 格式：每条日志为单行 JSON，包含 timestamp(UTC ISO)、level、logger、message、request_id、run_id、task_id、module 字段，异常时附加 exception 字段。
- 上下文传播：通过 ContextVar 存储 request_id、run_id、task_id，使用 log_context 上下文管理器自动设置/恢复。
- 文件轮转：backend.log 使用 RotatingFileHandler，5MB × 5 备份，UTF-8 编码。
- 配置驱动：日志目录和级别由环境变量 BACKEND_LOG_DIR、BACKEND_LOG_LEVEL 控制。

### 启动器日志
- 彩色输出：TTY 检测后启用 ANSI 颜色，不同级别对应不同颜色（DEBUG=灰、INFO=青、OK=绿、WARN=黄、ERROR=红）。
- 固定格式：[YYYY-MM-DD HH:MM:SS] [LEVEL] [CATEGORY] message。
- 轮转策略：launcher.log 5MB × 3 备份；子进程日志超过 50MB 时重命名为 .old。

### HTTP 请求追踪
- Request ID：从 x-request-id 头获取或自动生成 UUID，通过 set_request_id() 设置到 ContextVar。
- 中间件集成：request_context_middleware 在每个请求中自动设置 request_id 并记录耗时。
- 异常处理：全局异常处理器捕获未处理异常并记录完整堆栈。

## 4. 开发者规范
### 后端服务开发
- 初始化顺序：在模块导入时调用 ensure_logging_configured() 确保日志已配置。
- 上下文管理：使用 with log_context(request_id=..., run_id=..., task_id=...) 包裹需要关联上下文的代码块。
- Logger 命名：使用 logging.getLogger(__name__) 获取模块级 logger，遵循 Python 标准命名空间。
- 结构化字段：通过 extra 参数传递结构化字段，如 logger.info("msg", extra={"key": "value"})。
- 禁止直接配置：不要在业务模块中调用 basicConfig、addHandler 等配置方法。

### 启动器脚本
- 使用共享 Log：通过 from launch.logging_setup import log 获取单例实例。
- 分类标签：所有日志必须指定 category 参数，便于过滤和聚合。
- 级别选择：DEBUG(调试)、INFO(常规)、OK(成功确认)、WARN(警告)、ERROR(错误)。

### 算法模块
- 标准 Logger：每个模块顶部定义 logger = logging.getLogger(__name__)。
- 无特殊配置：继承根 logger 的配置，无需单独初始化。
- 结构化输出：优先使用 logger.info("msg", extra={...}) 而非字符串拼接。

### 日志级别使用原则
- DEBUG：详细的调试信息，仅在开发环境开启。
- INFO：关键业务流程节点（请求开始/结束、任务提交/完成）。
- WARN：可恢复的异常情况（重试、降级、超时）。
- ERROR：导致操作失败的严重错误（异常、外部依赖失败）。
- OK：启动器专用的成功确认标记。

### 环境变量配置
- BACKEND_LOG_DIR：日志输出目录（默认 I:\Geograph_DataSet\_runtime\logs）
- BACKEND_LOG_LEVEL：日志级别（DEBUG/INFO/WARNING/ERROR）
- BACKEND_SERVICE_NAME：服务名称，影响日志中的 service_name 字段

## 5. 日志文件布局
.backend/.data/logs/
├── backend.log          # FastAPI 应用日志（JSON 格式）
├── launcher.log         # 启动器日志（文本格式）
└── *.old                # 轮转后的旧日志文件
