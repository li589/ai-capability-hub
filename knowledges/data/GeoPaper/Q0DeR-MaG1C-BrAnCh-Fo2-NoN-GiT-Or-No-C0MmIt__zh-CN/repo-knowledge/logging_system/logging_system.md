---
kind: "repo_knowledge"
category: "logging_system"
title: "日志系统：基于 Python 标准库 logging 的分散式文件+控制台输出"
scopes: ["**"]
updated_at: "2026-07-30T06:34:50Z"
---

# 日志系统：基于 Python 标准库 logging 的分散式文件+控制台输出

本仓库未采用统一的日志框架或集中式日志配置，而是以 Python 标准库 `logging` 为主、辅以大量 `print()` 语句的分散式记录方式。具体表现如下：

1. **使用的框架与工具**
   - 核心依赖为 Python 内置 `logging` 模块，通过 `logging.basicConfig(...)` 在脚本入口处配置根 logger。
   - 同时广泛使用 `print()` 直接输出到 stdout，尤其在训练循环、数据预处理等脚本中作为进度/调试信息。
   - 无第三方日志库（如 loguru、structlog、python-json-logger）的使用痕迹。

2. **关键文件与位置**
   - `Code/li/insert_ALL_2_CSV.py`：在模块级调用 `logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler("data_aug_v3_fix.log"), logging.StreamHandler()])`，同时写入本地 `data_aug_v3_fix.log` 和 stdout。
   - `PlusCode/Data/Landslide/refresh_landsat_veg_batches.py`：提供 `configure_logging(log_path)` 函数，统一设置带线程名的格式 `%(asctime)s [%(threadName)s] %(message)s`，并强制 `force=True`，同时输出到文件与控制台。
   - 其他脚本（如 `EM-DAT/*.py`、`TCDF-master/TCDF.py`、各 `train_*.py`）基本仅用 `print()` 输出训练进度与中间结果，未见结构化日志。

3. **架构与约定**
   - **无全局 logger 单例**：每个脚本各自初始化自己的 `basicConfig`，不存在跨模块共享的 logger 实例。
   - **日志级别策略**：普遍使用 `INFO` 作为默认级别；错误路径使用 `logging.error(...)`，警告使用 `logging.warning(...)`，正常流程使用 `logging.info(...)`。
   - **输出目标**：均为“文件 + 控制台”双写，文件名多为脚本同目录下的 `.log` 文件（如 `data_aug_v3_fix.log`、`data_aug_safe.log`），部分空日志文件表明曾经运行过但无输出。
   - **结构化程度低**：日志格式为简单字符串拼接，未使用 JSON 或其他结构化字段，不利于后续聚合分析。
   - **并发场景**：`refresh_landsat_veg_batches.py` 中使用线程名 `[%(threadName)s]` 区分并发任务，体现对并行批处理任务的日志可追踪性考虑。

4. **开发者应遵循的规则（现状与建议）**
   - 当前规范不统一：不同脚本的 `basicConfig` 格式、级别、handler 各不相同，建议未来统一封装一个 `setup_logging(name, log_dir)` 工具函数。
   - 避免混用 `print` 与 `logging`：调试信息建议使用 `logging.debug/info`，便于按级别过滤；生产环境应关闭 DEBUG 输出。
   - 建议引入结构化日志（如 JSON 格式）以便集中采集与分析。
   - 对于长时运行的批处理任务，应确保日志文件有轮转策略，避免无限增长。
   - 建议在 `project_config.py` 或独立 `logging_config.py` 中集中管理日志路径、级别、格式等配置项。
