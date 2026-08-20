---
name: saw-st-v8-realign
display_name: 空间转录组重配准与重分析
display_name_en: Spatial Transcriptomics Realignment and Reanalysis
description: 'DCS Cloud WDL "SAW-ST-V8-realign" (v1.2.2) parameter guide: rerun spatial registration and downstream analysis (Cellbin, clustering, report) from manually corrected images/IPR or Lasso GeoJSON. Use when the user mentions SAW-ST-V8-realign, realign, Stereo-seq re-registration, manual-alignment reanalysis, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「SAW-ST-V8-realign」(v1.2.2) 流程说明与填参指南：基于手动校正图像/IPR 或 Lasso GeoJSON 重做空间配准与下游（Cellbin、聚类、报告）。用户提到 SAW-ST-V8-realign、realign、Stereo-seq 重配准、手动配准后重分析，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "SAW-ST-V8-realign" (v1.2.2) parameter guide: rerun spatial registration and downstream analysis (Cellbin, clustering, report) from manually corrected images/IPR or Lasso GeoJSON. Use when the user mentions SAW-ST-V8-realign, realign, Stereo-seq re-registration, manual-alignment reanalysis, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.2.3
author: DCS Genpilot
---
# SAW-ST-V8-realign（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `SAW-ST-V8-realign` |
| **文档版本对应流程** | V1.2.2 |
| **类型** | 空间转录组数据重配准与重分析 |
| **适用输入** | CountData + ImageTar + IPR；可选 LassoGeojson |
| **主要功能** | 用手动校正的配准/选区重算表达矩阵、细胞分割、聚类与报告 |
| **支持平台** | MGI STOmics / Stereo-seq |

## 何时使用

- 用户要跑 / 了解 **SAW-ST-V8-realign**
- 自动配准或组织截取不理想，已在 StereoMap 手动校正图像/IPR，或导出了 Lasso GeoJSON
- 需在不重跑全流程比对的前提下重启 Cellbin / 聚类 / 报告

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n SAW-ST-V8-realign` 核对线上最新规格。

## 流程简介

当标准 SAW 自动配准或组织截取未达预期时，用客户端手动调整后的图像包与 IPR 更新配准；若不提供图像路径逻辑优先，也可直接用 StereoMap 导出的 Lasso GeoJSON。流程基于更准的空间映射重生成表达矩阵，并执行 Cellbin、空间聚类与可视化报告。**若提供 `LassoGeojson`，优先按该多边形选区重启分析，而非仅依赖新图像。**

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| make_tar | 解压图像包，用新 IPR 替换配置后重新打包 | 始终执行 |
| realign | 加载 CountData 与重配准信息（优先 LassoGeojson，否则用重构 ImageTar），重跑组织识别、掩模、聚类与归档 | 始终执行 |

## 输入参数

（源 `_param.md` 为空；以下摘自主文档内嵌参数表。）

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `ID` | String | **必填** | 无 | 样本唯一 ID |
| `SN` | String | **必填** | 无 | 芯片 SN。例：`Y40008CE11` |
| `CountData` | File | **必填** | 无 | 上游计数/比对基底数据 |
| `ImageTar` | File | **必填** | 无 | 手动调整后的形态学图像 `.tar.gz` |
| `IPR` | File | **必填** | 无 | 校正后的配准配置 `.ipr` |
| `LassoGeojson` | File? | 选填 | 无 | StereoMap 套索选区；提供则优先按此选区重启 |
| `CreateGem` | Boolean | 选填 | `false` | 是否额外生成 `.gem` |
| `SkipCellbin` | Boolean | 选填 | `false` | 跳过 Cellbin |
| `SkipClustering` | Boolean | 选填 | `false` | 跳过聚类（仅矩阵等） |
| `ExtraImageEnhance` | Int | 选填 | `0` | 图像增强档位（≥0） |
| `AdjustedDistance` | Int | 选填 | `10` | 细胞核边界外扩/归属距离阈值（≥0） |
| `Memory` | Int | 选填 | `90` | realign 步骤内存上限 GB（≥30） |

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n SAW-ST-V8-realign --output json

dcs workflow run -n SAW-ST-V8-realign -e 001 \
  -i ID='Sample_01' \
  -i SN='Y40008CE11' \
  -i CountData='/Files/path/to/count_data' \
  -i ImageTar='/Files/path/to/image.tar.gz' \
  -i IPR='/Files/path/to/corrected.ipr' \
  -i LassoGeojson='/Files/path/to/lasso.geojson' \
  -i CreateGem='false' \
  -i SkipCellbin='false' \
  -i SkipClustering='false' \
  -i Memory='90' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。无 Lasso 时可省略 `LassoGeojson`。

## 输出

主要结果在 `result/<SN>/`：

| 路径 | 说明 |
|------|------|
| `outs/analysis/` | bin20/bin50/cellbin 的 `.h5ad`、marker CSV 等 |
| `outs/bam/` | 带空间注释的 BAM + 索引 |
| `outs/feature_expression/` | `.gef`（raw/tissue/cellbin 等）及文本表达表 |
| `outs/image/` | 配准图、mask、tissue cut 等 `.tif` |
| `outs/report/report.html` | 交互式重分析报告 |
| `outs/visualization/` | StereoMap 项目包 `.tar.gz` 等 |
| `pipeline-logs/` | 运行配置快照 |
| `STEREO_ANALYSIS_WORKFLOW_PROCESSING/` | 中间诊断与分模块日志 |

```text
result/Y40008CE11/
├── outs/
│   ├── analysis/            # *.h5ad, *.marker_features.csv
│   ├── bam/annotated_bam/
│   ├── feature_expression/  # *.gef, *_raw_barcode_gene_exp.txt
│   ├── image/               # *_mask.tif, *_regist.tif, *_tissue_cut.tif
│   ├── report/report.html
│   └── visualization/
├── pipeline-logs/
└── STEREO_ANALYSIS_WORKFLOW_PROCESSING/
```

## 资源建议

| 任务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| make_tar | 8 | 30 | 固定 |
| realign | 8 | `Memory`（默认 90） | 大芯片 OOM 时上调至 128+ |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 同系列：`saw-st-v8`

## Agent 约定

1. 引用本流程时使用确切名称 **`SAW-ST-V8-realign`**（投递 `-n`）。
2. 必填：`ID`、`SN`、`CountData`、`ImageTar`、`IPR`；有 Lasso 时优先用 `LassoGeojson`。
3. 填参以线上 `check_parameter` 为准（独立 `_param.md` 为空时尤须核对线上）；本文与线上不一致时以线上为准并告知用户。
4. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

