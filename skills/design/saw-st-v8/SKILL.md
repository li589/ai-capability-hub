---
name: saw-st-v8
display_name: 空间转录组/多组学主分析
display_name_en: Spatial Transcriptomics / Multi-omics Main Analysis
description: 'DCS Cloud WDL "SAW-ST-V8" (v1.2.4) parameter guide: Stereo-seq spatial transcriptomics / multi-omics main analysis (alignment, spatial quantification, cell segmentation, clustering, and reporting). Use when the user mentions SAW-ST-V8, SAW, Stereo-seq, STOmics, the spatial transcriptomics main workflow, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「SAW-ST-V8」(v1.2.4) 流程说明与填参指南：Stereo-seq 空间转录组/多组学主分析（比对、空间定量、细胞分割、聚类与报告）。用户提到 SAW-ST-V8、SAW、Stereo-seq、STOmics、空间转录组主流程，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "SAW-ST-V8" (v1.2.4) parameter guide: Stereo-seq spatial transcriptomics / multi-omics main analysis (alignment, spatial quantification, cell segmentation, clustering, and reporting). Use when the user mentions SAW-ST-V8, SAW, Stereo-seq, STOmics, the spatial transcriptomics main workflow, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.2.5
author: DCS Genpilot
---
# SAW-ST-V8（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `SAW-ST-V8` |
| **文档版本对应流程** | V1.2.4（核心软件 SAW v8.2.2） |
| **类型** | 空间转录组学 / 空间多组学数据分析 |
| **适用输入** | Stereo-seq FASTQ（可含 CITE 蛋白组）+ ChipMask + 参考索引；可选显微镜图像 / ImageTar |
| **主要功能** | reads 映射至组织空间位置、量化空间特征表达、细胞分割、聚类及可视化报告 |
| **适用范围** | 仅适配 StereoMap ≥ 4.0 的芯片数据（`SN_YYMMDD_HHMMSS_4.0.x.tar.gz`） |

## 何时使用

- 用户要跑 / 了解 **SAW-ST-V8** 主分析
- 已有 Stereo-seq 下机 FASTQ、ChipMask、参考索引，需要 GEF/报告等标准产出
- Stereo-CITE 联合分析（需 `AdtFastqs` + `ProteinPanel`）

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n SAW-ST-V8` 核对线上最新规格。

相关辅助流程：`SAW-ST-V8-makeRef`、`SAW-ST-V8-realign`、`SAW-ST-V8-gef2gem`、`SAW-ST-V8-reanalyze-lasso` 等。

## 流程简介

Stereo-seq Analysis Workflow (SAW) 面向华大时空组学 (STOmics)。SAW-ST-V8 结合测序与显微镜图像，经比对、空间条形码解析、表达定量等步骤，生成空间特征表达矩阵（GEF/可选 GEM）与 HTML 报告。

**核心特性（SAW v8.2.2）：** 支持 Stereo-CITE；比对默认切除接头；bin GEF 聚类优化；支持 StereoMap 配准后 `.tar.gz` 与多图像输入；报告含 bin20/bin50 聚类与 UMAP。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| 数据预处理 | 去 Tissue 空格；按 ssDNA/DAPI/HE 优先级整理图像；按 KitVersion 推断测序类型 | 初始化自动执行 |
| count | 比对、空间 barcode、Cellbin、聚类、转录组/微生态/蛋白组定量 | 始终执行 |
| 质控与报告打包 | 解压可视化包、提取 HTML 报告、归档 statistics JSON 与日志 | count 成功后自动执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `ID` | String | **必填** | 无 | 样本/项目唯一 ID，输出前缀。例：`Sample_01` |
| `SN` | String | **必填** | 无 | 芯片 SN；仅支持 StereoMap ≥4.0 规则芯片 |
| `Fastqs` | Array[Array[File]] | **必填** | 无 | 转录组 FASTQ；嵌套数组可多 Lane |
| `AdtFastqs` | Array[Array[File]]? | 选填 | 无 | Stereo-CITE 蛋白组 FASTQ；提供则开启多组学 |
| `ChipMask` | File | **必填** | 无 | 芯片 Mask（空间坐标与 Barcode 映射） |
| `Image` | Array[File]? | 选填 | 无 | 形态学图像；内部按 ssDNA/DAPI/HE 排序 |
| `ImageTar` | File? | 选填 | 无 | StereoMap 特征点配准后 `.tar.gz`；与 `Image` 同给时优先本参数 |
| `ReferenceIndex` | Array[File] | **必填** | 无 | 基因组参考索引；多文件则开启微生态检测 |
| `ProteinPanel` | File? | 选填 | 无 | CITE 蛋白 Panel（CSV/TSV）；跑 Stereo-CITE 时**必填** |
| `KitVersion` | String | **必填** | 无 | 试剂盒版本（见下表）；非法值直接报错 |
| `Organism` | String | **必填** | 无 | 物种。例：`Mouse`、`Human` |
| `Tissue` | String | **必填** | 无 | 组织类型；支持中文，自动去空格 |
| `CustomBinSize` | String | 选填 | `"20,50"` | 逗号分隔 Bin 分辨率 |
| `UniquelyMappedOnly` | Boolean | 选填 | `false` | 是否仅保留唯一比对 |
| `rRNARemove` | Boolean | 选填 | `false` | 是否剔除 rRNA |
| `NoBam` | Boolean | 选填 | `false` | `true` 跳过 BAM 输出以省磁盘 |
| `CreateGem` | Boolean | 选填 | `false` | `true` 额外生成传统 GEM |
| `SkipCellbin` | Boolean | 选填 | `false` | 跳过基于图像的细胞分割；无图像时建议开启 |
| `SkipClustering` | Boolean | 选填 | `false` | 跳过聚类以提速 |
| `Mem` | Int | 选填 | `90` | 总内存 GiB；大芯片须上调 |
| `Cores` | Int | 选填 | `32` | CPU 核数 |

### KitVersion → SequencingType（精简）

| KitVersion | SequencingType |
|------------|----------------|
| Stereo-seq T FF V1.1 / V1.2 | PE100_50+100 |
| Stereo-seq T FF V1.3 | PE75_50+100 |
| Stereo-seq N FFPE V1.0 | PE75_25+59 |
| Stereo-seq N FFPE V1.1 | PE75_50+100 |
| Stereo-CITE T FF V1.0 pooling | PE100_50+100 |
| Stereo-CITE T FF V1.1 pooling | PE75_50+100 |
| Stereo-CITE T FF V1.0 separately | PE100_50+100, PE100_50+36 |
| Stereo-CITE T FF V1.1 separately | PE75_50+100, PE75_50+36 |

不在上表则报错：`Invalid kit version`。

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。Array 参数传 JSON 数组文本。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n SAW-ST-V8 --output json

dcs workflow run -n SAW-ST-V8 -e 001 \
  -i ID='Sample_01' \
  -i SN='Y40008CE11' \
  -i Fastqs='[["/Files/path/to/S1_R1.fq.gz","/Files/path/to/S1_R2.fq.gz"]]' \
  -i ChipMask='/Files/path/to/chip.mask.gz' \
  -i ReferenceIndex='["/Files/path/to/ref_index"]' \
  -i KitVersion='Stereo-seq T FF V1.3' \
  -i Organism='Mouse' \
  -i Tissue='Brain' \
  -i Image='["/Files/path/to/ssDNA.tif"]' \
  -i CustomBinSize='20,50' \
  -i NoBam='false' \
  -i Mem='90' \
  -i Cores='32' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。Stereo-CITE 另加 `AdtFastqs` 与 `ProteinPanel`。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `out_count` | Directory | 核心结果（约对应 `./result` 及提升至工作根目录的文件） |

典型内容：

```text
report/                 # ${SN}.report.html / .tar.gz
*.statistics.json       # 比对率、UMI、细胞数等
outs/                   # .gef（bin / cellbin）；CreateGem 时另有 .gem.gz；NoBam=false 时有 .bam
output-error-log/       # 各阶段运行日志
```

## 资源建议

`UniquelyMappedOnly=false` 时内存显著升高。标准 1×1 芯片默认 `Mem=90` 通常够用；1×2 及以上或深测序须上调，否则易 OOM。

| 场景（FF, ssDNA，示意） | 峰值内存约 | 建议 |
|-------------------------|------------|------|
| 1×1 | ~77 G | 默认 90 可试 |
| 1×2 / 2×3 | ~200–250 G | `Mem` ≥ 256 |
| 3×4 / 3×5 | ~370–700 G | 大幅上调并预留磁盘 |

FFPE 1×1 实测峰值可到百 GB 以上，深度大时勿用默认硬顶。

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 同系列：`saw-st-v8-makeref`、`saw-st-v8-realign`、`saw-st-v8-gef2gem`、`saw-st-v8-reanalyze-lasso`

## Agent 约定

1. 引用本流程时使用确切名称 **`SAW-ST-V8`**（投递 `-n`）。
2. 必填：`ID`、`SN`、`Fastqs`、`ChipMask`、`ReferenceIndex`、`KitVersion`、`Organism`、`Tissue`；CITE 时另需 `ProteinPanel`（及通常 `AdtFastqs`）。
3. `Fastqs` / `ReferenceIndex` / `Image` 等 Array 用 JSON 数组，勿用逗号拼普通字符串。
4. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
5. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

