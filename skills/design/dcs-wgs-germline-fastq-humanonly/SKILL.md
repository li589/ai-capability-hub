---
name: dcs-wgs-germline-fastq-humanonly
display_name: WGS 胚系变异检测（人类专用）
display_name_en: WGS Germline Variant Detection (Human Only)
description: 'DCS Cloud WDL "DCS_WGS_Germline_FASTQ_HumanOnly" (v2.0.1) parameter guide: minimal human hg38 WGS germline submission (QC, alignment, BQSR, HaplotypeCaller, report). Use when the user mentions DCS_WGS_Germline_FASTQ_HumanOnly, HumanOnly, human WGS germline, DCS_Reference_hg38, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「DCS_WGS_Germline_FASTQ_HumanOnly」(v2.0.1) 流程说明与填参指南：人类 hg38 WGS 胚系极简投递（质控、比对、BQSR、HC、报告）。用户提到 DCS_WGS_Germline_FASTQ_HumanOnly、HumanOnly、人类 WGS 胚系、DCS_Reference_hg38，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "DCS_WGS_Germline_FASTQ_HumanOnly" (v2.0.1) parameter guide: minimal human hg38 WGS germline submission (QC, alignment, BQSR, HaplotypeCaller, report). Use when the user mentions DCS_WGS_Germline_FASTQ_HumanOnly, HumanOnly, human WGS germline, DCS_Reference_hg38, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 2.0.2
author: DCS Genpilot
---
# DCS_WGS_Germline_FASTQ_HumanOnly（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `DCS_WGS_Germline_FASTQ_HumanOnly` |
| **文档版本对应流程** | V2.0.1 |
| **类型** | 全基因组测序 (WGS) 胚系变异检测 |
| **适用输入** | 人源 FASTQ / SeqArc + hg38 参考目录 |
| **主要功能** | 质控、比对去重、BQSR、变异检测与基因分型、综合报告 |
| **参考基因组** | 仅支持人类 hg38 |

## 何时使用

- 用户要跑 / 了解 **DCS_WGS_Germline_FASTQ_HumanOnly**
- 明确是人类 hg38 WGS，希望参数尽量少；非人源或需调倍性/模块开关时改用 `DCS_WGS_Germline_FASTQ`

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n DCS_WGS_Germline_FASTQ_HumanOnly` 核对线上最新规格。

## 流程简介

面向人类 WGS 的 GATK 最佳实践精简流程：比对 → MarkDup → BQSR → HC（gVCF→VCF）→ HTML 报告。自动推断 PE/SE；比对/BQSR/HC 始终执行。资源由 `reference_info.json` 驱动。

V2.0.1：优化 SE 自动推断与 report 体系。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| `lush_aligner` | QC、比对 hg38、排序、MarkDup、基础 QC | 始终执行 |
| `lush_bqsr` | 基于 known sites/dbSNP 的 BQSR | 始终执行 |
| `lush_HC` | gVCF → VCF + 综合 HTML 报告 | 始终执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SampleID` | String | **必填** | 无 | 样本 ID / Read Group。例：`NA12878` |
| `FASTQ` | Array[Array[File]] | **必填** | 无 | PE：`[[R1,R2]]`；SE：`[[SE]]`；`*.fq.gz` 或 `*.arc` |
| `ReferenceDir` | File | **必填** | 无 | 官方 `DCS_Reference_hg38` 类目录（含 `hg38.fa`、`reference_info.json`、`known_site/`、dbsnp） |
| `StandCallConf` | String | 选填 | `"30"` | 变异调用置信度阈值 |
| `OutputSortMarkdupBam` | Boolean | 选填 | `false` | 是否输出排序去重 BAM（IGV 核查时建议 true） |

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n DCS_WGS_Germline_FASTQ_HumanOnly --output json

dcs workflow run -n DCS_WGS_Germline_FASTQ_HumanOnly -e 001 \
  -i SampleID='NA12878' \
  -i FASTQ='[["/Files/path/to/NA12878_R1.fq.gz","/Files/path/to/NA12878_R2.fq.gz"]]' \
  -i ReferenceDir='/Files/path/to/DCS_Reference_hg38' \
  -i StandCallConf='30' \
  -i OutputSortMarkdupBam='true' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。`Array[Array[File]]` 须传嵌套 JSON 数组文本。

## 输出

| 输出变量 | 类型 | 条件 | 说明 |
|----------|------|------|------|
| `filter` | Directory | 始终 | `QC/` 质控文本 |
| `out_rmdum_sort_bam` (+ index) | File | `OutputSortMarkdupBam` | 排序去重 BAM |
| `vcf` / `vcf_index` | File | 始终 | `*.genotyper.vcf.gz` + tbi |
| `gvcf` / `gvcf_index` | File | 始终 | `*.g.vcf.gz` + tbi |
| `out_report` | Directory | 始终 | `report/` HTML + 统计表 + SVG |
| `out_hc_md5` | Directory | 始终 | `md5sum/` |

典型结构：

```text
├── <SampleID>.genotyper.vcf.gz / .tbi
├── <SampleID>.g.vcf.gz / .tbi
├── <SampleID>.sort.bam / .bai   # 可选
├── QC/
├── report/                      # *_report_cn.html / DepthDis.svg 等
└── md5sum/
```

## 资源建议

| 任务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| `lush_aligner` | 32 | 64 或 128 | 低内存索引约 64GB，默认约 128GB（由参考配置决定） |
| `lush_bqsr` | 32 | 64 | — |
| `lush_HC` | 32 | 64 | 含报告生成 |

集群需支持 `avx512` / `avx2`。

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 相关：`dcs-wgs-germline-fastq`

## Agent 约定

1. 引用本流程时使用确切名称 **`DCS_WGS_Germline_FASTQ_HumanOnly`**（投递 `-n`）。
2. 必填三项：`SampleID`、`FASTQ`、`ReferenceDir`；缺一不可投。
3. `ReferenceDir` 须为人源 hg38 官方资源包；勿与通用物种参考混用。
4. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
5. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

