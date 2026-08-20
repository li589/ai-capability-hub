---
kind: "repo_knowledge"
category: "configuration_system"
title: "配置系统 — Python 脚本级 config.py + 环境变量驱动"
scopes: ["**"]
updated_at: "2026-07-30T06:33:47Z"
---

# 配置系统 — Python 脚本级 config.py + 环境变量驱动

## 1. 使用的系统与工具
- **Python 模块级配置文件**：每个实验版本（V1.0–V6.1）及 EM-DAT 子项目均通过独立的 `config.py` / `config_emdat.py` 暴露全局常量，被同目录下的训练、数据加载、分析脚本直接 `import config`。
- **环境变量（os.environ / os.getenv）**：PlusCode 的数据构建与 GEE 导出脚本通过 `TCDF_*` 前缀的环境变量控制批处理、时间窗口、数据集选择与运行标签；`GEOPAPER_VENV_DIR` 用于切换 Python 虚拟环境路径。
- **Pathlib 集中式路径管理**：`PlusCode/project_config.py` 提供 `PLUSCODE_ROOT`、`DATA_DIR`、`LANDSLIDE_DIR`、`HYPER_TCDF_DIR` 等统一路径入口，并通过 `_env_path` 支持环境变量覆盖。

## 2. 核心文件与位置
- `Code/Hyper-TCDF/V*.0/config.py`：各版本 Hyper-TCDF 的核心配置（路径、序列长度、模型超参、训练参数、静态/动态特征列、物理衍生特征、采样策略等）。
- `Code/Hyper-TCDF/EM-DAT/config_emdat.py`：EM-DAT 专用配置，包含地理学增强版特征列与更细粒度的 Subregion One-Hot。
- `PlusCode/project_config.py`：PlusCode 项目的根路径与环境变量解析中心。
- `PlusCode/Data/Landslide/build_tcdf_point_timeseries_test.py`、`assemble_tcdf_from_local_cache_2000plus.py`、`export_gee_hazard_cache_2000plus.py`：通过 `TCDF_BATCH_SIZE`、`TCDF_BATCH_INDEX`、`TCDF_GLOBAL_START_DATE`、`TCDF_GLOBAL_END_DATE`、`TCDF_SOURCE_DATASET`、`TCDF_RUN_TAG`、`GEE_PROJECT_ID` 等环境变量控制数据流水线。

## 3. 架构与设计约定
- **按版本隔离配置**：每个 Vx.y 目录自带独立 `config.py`，避免跨版本污染；EM-DAT 子项目另建 `config_emdat.py` 以区分数据集与特征。
- **分层配置结构**：每个 `config.py` 内部按“路径 → 数据核心参数 → 模型超参 → 训练超参 → 特征工程 → 解释性排除列”顺序组织，便于快速定位与修改。
- **环境变量优先于硬编码路径**：`project_config._env_path` 允许通过 `GEOPAPER_VENV_DIR` 覆盖默认路径；数据构建脚本通过 `TCDF_*` 环境变量实现无参运行时的灵活装配。
- **命名规范**：所有运行时开关统一使用 `TCDF_` 前缀的环境变量，便于在批量任务中识别与过滤。

## 4. 开发者应遵循的规则
1. **新增实验版本时复制现有 `config.py`**：在对应 Vx.y 目录下维护独立配置，不要跨版本共享同一文件。
2. **敏感路径与外部依赖走环境变量**：如 GEE 项目 ID、数据源筛选、批大小等，通过 `os.getenv("TCDF_*")` 读取，避免硬编码。
3. **保持配置字段命名一致**：`SEQUENCE_LENGTH`、`PREDICT_WINDOW`、`MODEL_PARAMS`、`TRAIN_PARAMS`、`STATIC_COLS`、`DYNAMIC_COLS_BASE`、`PHYSICS_COLS` 等键名在各版本间保持一致，便于脚本复用。
4. **使用 `project_config.py` 管理项目级路径**：新增数据或输出目录时，先在 `project_config.py` 中定义 Path 常量，再在脚本中引用，减少散落的字符串路径。
5. **环境变量布尔/整型解析统一**：参考 `get_bool_env`、`get_int_env`、`get_optional_int_env` 的写法，对空值、`None`、`true/false` 等做规范化处理。
