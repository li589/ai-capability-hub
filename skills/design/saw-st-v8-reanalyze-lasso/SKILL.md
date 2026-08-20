---
name: saw-st-v8-reanalyze-lasso
display_name: 空间转录组 ROI 二次分析
display_name_en: Spatial Transcriptomics ROI Reanalysis
description: 'DCS Cloud WDL "SAW-ST-V8-reanalyze-lasso" (v1.2.0) parameter guide: extract ROI expression matrices and mask images from spatial GEF (Bin or Cellbin) using GeoJSON ROIs. Use when the user mentions SAW-ST-V8-reanalyze-lasso, lasso, ROI extraction, spatial lasso reanalysis, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「SAW-ST-V8-reanalyze-lasso」(v1.2.0) 流程说明与填参指南：按 GeoJSON ROI 从空间 GEF（Bin 或 Cellbin）提取感兴趣区域表达矩阵与掩码图。用户提到 SAW-ST-V8-reanalyze-lasso、lasso、ROI 提取、空间套索二次分析，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "SAW-ST-V8-reanalyze-lasso" (v1.2.0) parameter guide: extract ROI expression matrices and mask images from spatial GEF (Bin or Cellbin) using GeoJSON ROIs. Use when the user mentions SAW-ST-V8-reanalyze-lasso, lasso, ROI extraction, spatial lasso reanalysis, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.2.1
author: DCS Genpilot
---
# SAW-ST-V8-reanalyze-lasso（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `SAW-ST-V8-reanalyze-lasso` |
| **文档版本对应流程** | V1.2.0 |
| **类型** | 空间转录组二次分析（感兴趣区域提取） |
| **适用输入** | 空间表达 GEF + GeoJSON 区域坐标 |
| **主要功能** | 按 ROI 裁剪靶向基因表达矩阵并生成掩码 TIFF |
| **支持分辨率** | 多 Bin 尺寸及 Cellbin |

## 何时使用

- 用户要跑 / 了解 **SAW-ST-V8-reanalyze-lasso**
- 已在 StereoMap 等工具圈选 ROI 并导出 GeoJSON，需从全局 GEF 提取子区域矩阵

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n SAW-ST-V8-reanalyze-lasso` 核对线上最新规格。

## 流程简介

二次分析组件之一：接收可视化系统导出的 GeoJSON 轮廓与原始 GEF（Bin 或 Cellbin），做空间域映射与过滤，输出 ROI 专属 GEF 与匹配的 mask TIFF，便于后续区域聚类 / 差异表达。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| GetMemSetting | 解析 GEF 规模，动态评估下游内存策略 | 始终执行 |
| lasso | 按 GeoJSON 做遮罩判定，输出区域 GEF 与 mask TIFF | 始终执行（Scatter 并行多组） |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SN` | String | **必填** | 无 | 样本唯一标识。例：`Y40105CC` |
| `visGEF` | Array[File] | **必填** | 无 | 全局空间表达 GEF 数组；须与 `BinSize` 外层长度一致 |
| `BinSize` | Array[Array[String]] | **必填** | 无 | 分辨率定义：Bin 填数字字符串；单细胞填 `"cellbin"`。例：`[["20","50"]]` 或 `[["cellbin"]]` |
| `geojson` | File | **必填** | 无 | ROI 轮廓 GeoJSON |

逻辑：按 `BinSize` 长度 Scatter；`BinSize[i]` 对应 `visGEF[i]`。子数组含 `"cellbin"` 走单细胞提取，否则按 bin 尺度处理。

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。Array 参数传 JSON 数组文本。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n SAW-ST-V8-reanalyze-lasso --output json

# Bin 多分辨率（示例：一组任务内含 20 与 50）
dcs workflow run -n SAW-ST-V8-reanalyze-lasso -e 001 \
  -i SN='Y40105CC' \
  -i visGEF='["/Files/path/to/Y40105CC.bin.gef"]' \
  -i BinSize='[["20","50"]]' \
  -i geojson='/Files/path/to/roi.geojson' \
  --output json

# Cellbin
dcs workflow run -n SAW-ST-V8-reanalyze-lasso -e 002 \
  -i SN='Y40105CC' \
  -i visGEF='["/Files/path/to/Y40105CC.cellbin.gef"]' \
  -i BinSize='[["cellbin"]]' \
  -i geojson='/Files/path/to/roi.geojson' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `RealigneResult` | Array[Directory] | 各并行任务的 `./lasso` 结果目录集合 |

```text
input.json
lasso/
└── IVD/                                      # 依 GeoJSON 选区标签
    ├── Y40105CC.IVD.label.cellbin.gef        # ROI 表达矩阵
    └── Y40105CC.lasso.cellbin.IVD.mask.tiff  # 空间掩码
```

## 资源建议

| 任务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| GetMemSetting | 1 | 10 | 探测矩阵规模 |
| lasso | 20 | 动态 10–150 | 由 GetMemSetting 决定，用户不可手动限幅 |

动态阶梯（示意）：cellbin 按细胞数从 ~10 GB 升至百万细胞级 150 GB；bin 按 expression 规模从 ~15 GB 升至 150 GB。

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 同系列：`saw-st-v8`

## Agent 约定

1. 引用本流程时使用确切名称 **`SAW-ST-V8-reanalyze-lasso`**（投递 `-n`）。
2. 四项均必填：`SN`、`visGEF`、`BinSize`、`geojson`；且 `visGEF` 与 `BinSize` 长度对齐。
3. `visGEF` / `BinSize` 必须用 JSON 数组文本投递。
4. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
5. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

