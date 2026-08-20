---
name: cnvpytor-wgs-cnv
display_name: WGS 拷贝数变异检测
display_name_en: WGS Copy Number Variation Detection
description: 'DCS Cloud WDL "CNVpytor_WGS_CNV" (v1.0.0) parameter guide: detect copy-number variation (CNV) from WGS BAM. Use when the user mentions CNVpytor, CNVpytor_WGS_CNV, WGS CNV, copy-number variation, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「CNVpytor_WGS_CNV」(v1.0.0) 流程说明与填参指南：基于 BAM 做 WGS 拷贝数变异(CNV)检测。用户提到 CNVpytor、CNVpytor_WGS_CNV、WGS CNV、拷贝数变异检测，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "CNVpytor_WGS_CNV" (v1.0.0) parameter guide: detect copy-number variation (CNV) from WGS BAM. Use when the user mentions CNVpytor, CNVpytor_WGS_CNV, WGS CNV, copy-number variation, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.0.1
author: DCS Genpilot
---
# CNVpytor_WGS_CNV（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `CNVpytor_WGS_CNV` |
| **文档版本对应流程** | V1.0.0 |
| **类型** | WGS 拷贝数变异 (CNV) 检测 |
| **适用输入** | 比对后的 BAM + BAI |
| **主要功能** | 基于测序深度与 BAF 检测 CNV，并生成可视化图表 |

## 何时使用

- 用户要跑 / 了解 **CNVpytor_WGS_CNV**
- 已有坐标排序 BAM，需要 CNV call、曼哈顿图、深度统计

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n CNVpytor_WGS_CNV` 核对线上最新规格。

## 流程简介

针对 WGS 数据中的拷贝数变异（CNV/CNA）分析：从 BAM 提取深度与 B 等位基因频率（BAF）似然信息，做窗口化深度统计、分区检测与可视化；BAF 也是识别拷贝数中性杂合性缺失（cnLOH）的重要补充证据。

默认仅分析主要常染色体及性染色体：`chr1`–`chr22`、`chrX`、`chrY`。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| CNV_Detection_Module | 按 `winsize` 统计深度、分区检测、曼哈顿图与深度分布作图、CNV 类型计数 | 始终执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SampleID` | String | **必填** | 无 | 样本唯一 ID，用于输出命名；建议字母数字、无特殊字符。例：`NA12878` |
| `Bam` | File | **必填** | 无 | 标准 `.bam` |
| `BamIndex` | File | **必填** | 无 | 对应 `.bai`，须与 Bam 匹配 |
| `winsize` | Int | 选填 | `1000` | 深度/CNV 窗口（bp）；低深度可加大（如 10000 / 100000） |
| `outdir` | String | 选填 | `"./"` | 结果根目录；实际写入其下 `cnv_results/` |
| `cpu` | Int | 选填 | `8` | CPU 核数（≥1） |
| `mem` | Int | 选填 | `30` | 内存 GB（≥4）；极小窗口时需加大 |

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n CNVpytor_WGS_CNV --output json

dcs workflow run -n CNVpytor_WGS_CNV -e 001 \
  -i SampleID='NA12878' \
  -i Bam='/Files/path/to/sample.bam' \
  -i BamIndex='/Files/path/to/sample.bam.bai' \
  -i winsize='1000' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `result` | Directory | 综合结果目录（内含 `cnv_results/`） |

典型结构：

```text
cnv_results/
├── <SampleID>_*.CNV.call.txt              # CNV 呼叫表（类型、区间、深度、e-value 等）
├── <SampleID>_*.CNV.manhattan.global.0000.png
├── <SampleID>_*.CNV.rdstat.stat.0000.png
├── cnv_type_counts.txt
└── out.pytor                              # HDF5 工程文件（RD/BAF/分区等）
```

## 资源建议

| 参数 | 默认 | 建议 | 说明 |
|------|------|------|------|
| `cpu` | 8 | 4–16 | BAM 很大时可提到 16 |
| `mem` | 30 GB | 16–64 | 常规 30X WGS 用默认；`winsize` < 1000 时加内存 |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）

## Agent 约定

1. 引用本流程时使用确切名称 **`CNVpytor_WGS_CNV`**（投递 `-n`）。
2. 必填三项：`SampleID`、`Bam`、`BamIndex`；缺一不可投。
3. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
4. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

