---
description: "滑坡 TCDF 模型与数据工程（PlusCode）：基于 Hyper-TCDF 的滑坡时序预测项目，整合 GEE 原始缓存、TCDF 点级序列构建、区域训练与因果/空间异质性/级联效应等 V8.0 实验分析链。"
module_id: "atlas:d3b87c5c7fcf4942f0a9663ba071c2b3"
updated_at: "2026-07-30T06:31:49Z"
---

# 滑坡 TCDF 模型与数据工程（PlusCode）

## 概述 <!-- category:overview -->
基于 Hyper-TCDF 的滑坡时序预测项目，整合 GEE 原始缓存、TCDF 点级序列构建、区域训练与因果/空间异质性/级联效应等 V8.0 实验分析链。

## 架构设计 <!-- category:architecture_design -->
模块以 `project_config.py` 为全局路径与环境入口，统一导出 `DATA_DIR / TOOLS_DIR / HYPER_TCDF_DIR / LANDSLIDE_*` 等常量，所有脚本通过该配置解析 `files + other (+shp)` 三目录结构。
- `Data/Landslide/`：数据管线层，包含 GEE 两段式导出（`export_gee_point_cache_2000plus.py`）、本地组装（`assemble_tcdf_from_local_cache_2000plus.py`）、自动总控（`auto_run_tcdf_2000plus_pipeline.py`），输入来自 `Input/` 下的 Shapefile/GDB/CSV，输出到 `Output/` 与 `analysis_outputs/`。
- `Data/Other/`：共享辅助数据层，存放文件张量缓存（`input/file_tensor_cache_v8/`）、元数据清单（`metadata/`）、过滤清单（`filters/`）与区域运行产物（`regional_runs/<run_name>/`）。
- `Hyper-TCDF/V{6.1,7.0,7.1,8.0}/`：模型代码按版本隔离，当前唯一活跃主线为 `V8.0`，每个版本内部遵循固定脚本编号约定：`1_analyze_and_index.py` → `2_train.py` → `exp_XX_*.py` 实验脚本，由 `run_experiments_v8.py` / `run_full_analysis_pipeline.py` 统一调度。
- `Tools/`：独立工具脚本（文件列表、同步、合并），不依赖 Hyper-TCDF 包。
- 依赖方向单向：`Data/*` 脚本 → `config.py` → `data_loader.py` / `model.py`；实验脚本只读 `config.py` 导出的路径与参数，不反向修改数据层。

## 技术栈 <!-- category:tech_stack -->
Python + PyTorch（`torch.nn` 自定义 `SpatialHyperNet`、PhysicsContextGate 等模块），GeoPandas/fiona 处理 Shapefile，Google Earth Engine Python API 拉取 GEE 缓存，libpysal/esda 用于 LISA 空间自相关分析，matplotlib/seaborn 绘图，pickle/json/csv 作为中间格式。

## 编码规范 <!-- category:coding_conventions -->
- 所有路径与策略均通过 `config.py` 中的 `_env_or_default/_env_flag/_env_int` 等辅助函数从环境变量读取，禁止硬编码绝对路径。
- 结果输出严格遵循 `config.py` 中定义的 `RESULT_PATH` 子目录规范（`00_run_registry`、`01_model_outputs`、`02_causal`、`03_stratified`、`04_event_chain`、`05_benchmark`、`06_overview`、`07_experiments`、`99_docs`），每个子目录再分 `raw/tables/figures/reports`。
- 实验脚本统一采用 `exp_XX_<name>.py` 命名前缀，并由 `run_experiments_v8.py` 或 `run_full_analysis_pipeline.py` 集中调度，避免散落调用。
- 版本隔离通过 `Hyper-TCDF/V{6.1,7.0,7.1,8.0}` 目录实现，每个版本内保持相同的脚本编号顺序（1→2→exp_*），仅 `V8.0` 为当前活跃主线。
- 数据加载失败、索引失败等异常统一记录到 `OTHER_ROOT/metadata/` 下的 `*_failures_v8.csv` 日志文件，而非静默丢弃。
- 分组切分统一使用 `FILE_KEY_COL='file_key'` 与 `SPLIT_GROUP_KEY=FILE_KEY_COL` 做 grouped train/val/test，防止同文件窗口泄漏。

## 配置与命令 <!-- category:unique_setup_and_commands -->
通过环境变量覆写路径与策略：`TCDF_FILES_DIR`、`TCDF_OTHER_DIR`、`TCDF_SHP_DIR`、`TCDF_TRAINING_MANIFEST_PATH`、`TCDF_REUSE_EXISTING_INDEX`、`TCDF_PHASE2_PARALLEL_WORKERS`、`TCDF_PHASE2_BATCH_SIZE`、`TCDF_PREFER_FILE_TENSOR_CACHE`、`TCDF_RUN_NAMESPACE` 等；Windows/Linux 分别提供 `server_quickstart.ps1/.sh` 与 `run_experiments_v8.ps1/.sh` 一键部署/运行脚本。
