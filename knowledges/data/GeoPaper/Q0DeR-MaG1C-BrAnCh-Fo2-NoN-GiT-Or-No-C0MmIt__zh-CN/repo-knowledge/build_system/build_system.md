---
kind: "repo_knowledge"
category: "build_system"
title: "Python 脚本化构建与实验流水线（无统一构建系统）"
scopes: ["**"]
updated_at: "2026-07-30T06:35:46Z"
---

# Python 脚本化构建与实验流水线（无统一构建系统）

本仓库没有采用 Makefile、Dockerfile、CI/CD 或包管理工具（如 pip/conda/pyproject.toml）等标准构建系统，而是以 **Python 脚本 + Shell 启动脚本** 的方式组织实验与数据分析流程。构建与运行完全依赖本地 Python 虚拟环境（venv），通过 shell 脚本调用各版本的训练与分析脚本。

### 1. 使用的系统与工具
- **Python 虚拟环境**：`Code/venv`（基于 Python 3.11.9），由 `project_config.py` 中的 `GEOPAPER_VENV_DIR` 环境变量控制路径。
- **Shell 启动脚本**：`PlusCode/Hyper-TCDF/V7.1/run_full_analysis.sh` 和 `server_quickstart.sh` 作为入口，负责参数解析、环境变量设置、目录初始化，然后调用 Python 流水线。
- **Python 流水线编排**：`run_full_analysis_pipeline.py` 顺序执行因果分析、解释性阈值、物理分层、事件链、基准对比、总览仪表盘等步骤，并记录运行元数据。
- **版本隔离**：每个 Hyper-TCDF 版本（V1.0 ~ V8.0）独立存放一套 `config.py`、`train.py`、`data_loader.py`、`model.py` 等脚本，互不共享代码。

### 2. 关键文件与位置
- **项目配置**：`PlusCode/project_config.py` — 定义根路径、数据目录、虚拟环境路径、绘图字体等全局常量。
- **版本配置**：`PlusCode/Hyper-TCDF/V8.0/config.py`（684 行）— 集中管理所有路径、超参数、特征列、分析输出目录、实验参数等，支持通过 `TCDF_*` 环境变量覆写。
- **流水线入口**：
  - `PlusCode/Hyper-TCDF/V7.1/run_full_analysis.sh` — Bash 入口，解析 `files_dir`、`other_dir`、`shp_dir` 及 `--skip-benchmark` 参数。
  - `PlusCode/Hyper-TCDF/V7.1/server_quickstart.sh` — 快速启动索引构建与可选训练。
  - `PlusCode/Hyper-TCDF/V7.1/run_full_analysis_pipeline.py` — Python 主调度器，按固定顺序执行各分析步骤。
- **训练脚本**：`PlusCode/Hyper-TCDF/V6.1/train.py`（示例）— 包含完整的 PyTorch 训练循环、梯度裁剪、混合精度、早停、checkpoint 保存逻辑。
- **数据准备脚本**：`PlusCode/Data/Landslide/assemble_tcdf_from_local_cache_2000plus.py`、`export_gee_hazard_cache_2000plus.py` 等用于 GEE 缓存导出与 TCDF 序列组装。

### 3. 架构与约定
- **目录结构约定**：`Data/files`（点级逐日 CSV）、`Data/Other`（索引、模型、日志、过滤清单）、`Data/Shp`（空间辅助数据，可选）三输入模式，由 `config.py` 的 `_env_or_default` 机制统一处理。
- **版本演进策略**：每个 `Vx.y` 目录是完整快照，新增功能通过新建版本号实现，而非向后兼容修改。
- **结果输出规范**：`config.py` 中预定义所有中间表、图表、报告的路径（如 `CAUSAL_RESULT_DIR`、`STRATIFIED_RESULT_DIR`、`EVENT_CHAIN_RESULT_DIR`），并通过 `ensure_analysis_result_dirs()` 自动创建。
- **环境变量优先**：所有路径与开关均支持 `TCDF_*` 环境变量覆盖，便于服务器部署时动态调整。

### 4. 开发者应遵循的规则
- **不要直接修改硬编码路径**：通过 `TCDF_FILES_DIR`、`TCDF_OTHER_DIR`、`TCDF_SHP_DIR` 等环境变量配置数据路径。
- **新增实验需新建版本号**：在 `Hyper-TCDF/Vx.y/` 下复制现有模板，保持版本间隔离。
- **使用 shell 脚本启动**：通过 `run_full_analysis.sh` 或 `server_quickstart.sh` 运行，避免直接调用 Python 脚本导致环境变量缺失。
- **依赖管理**：当前无 `requirements.txt`，依赖安装记录散落在 Jupyter Notebook 输出中（如 manim、torch、numpy 等），建议后续统一为 `requirements.txt` 或 `pyproject.toml`。
- **无 CI/CD**：所有构建、训练、分析均在本地或服务器手动执行，缺乏自动化测试与持续集成。

