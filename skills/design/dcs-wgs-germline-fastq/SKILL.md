---
name: dcs-wgs-germline-fastq
display_name: WGS 胚系变异检测
display_name_en: WGS Germline Variant Detection
description: 'DCS Cloud WDL "DCS_WGS_Germline_FASTQ" (v2.0.1) parameter guide: WGS germline variant calling from FASTQ (QC, alignment, BQSR, HaplotypeCaller; supports non-diploid). Use when the user mentions DCS_WGS_Germline_FASTQ, WGS Germline, whole-genome germline, Ploidy, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「DCS_WGS_Germline_FASTQ」(v2.0.1) 流程说明与填参指南：从 FASTQ 做 WGS 胚系变异检测（质控、比对、BQSR、HC，支持非二倍体）。用户提到 DCS_WGS_Germline_FASTQ、WGS Germline、全基因组胚系、Ploidy，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "DCS_WGS_Germline_FASTQ" (v2.0.1) parameter guide: WGS germline variant calling from FASTQ (QC, alignment, BQSR, HaplotypeCaller; supports non-diploid). Use when the user mentions DCS_WGS_Germline_FASTQ, WGS Germline, whole-genome germline, Ploidy, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 2.0.2
author: DCS Genpilot
---
# DCS_WGS_Germline_FASTQ（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `DCS_WGS_Germline_FASTQ` |
| **文档版本对应流程** | V2.0.1 |
| **类型** | 全基因组测序 (WGS) 胚系变异检测 |
| **适用输入** | 原始 FASTQ / arcseq + 参考目录 |
| **主要功能** | 质控、比对去重、BQSR、SNP/Indel 检测与综合报告 |
| **支持倍性** | 二倍体 (`Ploidy=2`) 与非二倍体 (`Ploidy≠2`) |

## 何时使用

- 用户要跑 / 了解 **DCS_WGS_Germline_FASTQ**
- 需要通用 WGS 胚系流程（可配物种参考、倍性、开关模块）；人类固定 hg38 且参数极简时优先考虑 `DCS_WGS_Germline_FASTQ_HumanOnly`

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n DCS_WGS_Germline_FASTQ` 核对线上最新规格。

## 流程简介

从原始测序数据执行过滤 → 比对排序 MarkDup → BQSR → 变异检测，输出 VCF/gVCF 与可视化报告。兼容 SE/PE；`Ploidy=2` 走常规 HC，`Ploidy≠2` 走 jointcaller + merge。

V2.0.1：优化 SE 分析与非二倍体兼容。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| `lush_aligner` | 过滤、比对、排序、MarkDup、QC | 始终执行 |
| `make_unmapped_reads` | 未比对 reads → FASTQ | `OutputUnmappedReads = true` |
| `lush_bqsr` | 碱基质量重校正 | `ApplyBQSR = true` 且存在 known sites/dbSNP |
| `lush_HC` | 二倍体变异检测 + 报告 | `Ploidy = 2` 且 `ApplyHaplotypeCaller` |
| `lush_HC_jointcaller` | 非二倍体联合检测 | `Ploidy ≠ 2` 且 `ApplyHaplotypeCaller` |
| `merge_ploidy_vcf` | 合并非二倍体分块结果 | `Ploidy ≠ 2` 且 `ApplyHaplotypeCaller` |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SampleID` | String | **必填** | 无 | 样本唯一 ID。例：`NA12878` |
| `FASTQ` | Array[Array[File]] | **必填** | 无 | 支持多 Lane；PE `[[R1,R2]]`，SE `[[Read]]`；`.fq.gz` 或 arc |
| `ReferenceDir` | File | **必填** | 无 | 参考目录，须含 `reference_info.json` |
| `arcDir` | File? | 选填 | 无 | arc 依赖目录；标准 FASTQ 留空 |
| `Adapter1` | String | 选填 | `AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA` | Read1 接头 |
| `Adapter2` | String | 选填 | `AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG` | Read2 接头 |
| `Ploidy` | Int | 选填 | `2` | 染色体倍性；人类常规为 2 |
| `SOAPnukeLowQual` | String | 选填 | `"12"` | 低质量碱基阈值 |
| `SOAPnukeLowQualityRate` | String | 选填 | `"0.5"` | 单 read 低质量比例上限 |
| `SOAPnukeNRate` | String | 选填 | `"0.1"` | 单 read N 比例上限 |
| `StandCallConf` | String | 选填 | `"30"` | 变异调用置信度阈值 |
| `IncludeNonVariantSites` | Boolean | 选填 | `false` | 是否保留非变异位点 |
| `OutputUnmappedReads` | Boolean | 选填 | `false` | 是否输出未比对 FASTQ |
| `OutputSortMarkdupBam` | Boolean | 选填 | `false` | 是否输出排序去重 BAM |
| `OutputBqsrBam` | Boolean | 选填 | `false` | 是否输出 BQSR BAM |
| `ApplyFilter` | Boolean | 选填 | `true` | 比对前过滤 |
| `ApplyBQSR` | Boolean | 选填 | `true` | 启用 BQSR（依赖参考库） |
| `ApplyHaplotypeCaller` | Boolean | 选填 | `true` | 是否做变异检测；false 则止于比对 |
| `AlignerMemorySet` | Int | 选填 | `128` | 比对内存 GB（≥32） |
| `BQSRMemorySet` | Int | 选填 | `64` | BQSR 内存 GB（≥32） |
| `HaplotypeCallerMemorySet` | Int | 选填 | `64` | HC 内存 GB（≥32） |

`ReferenceDir` 至少含 `*.fa`+索引与 `reference_info.json`；`known_site/`、dbSNP 为 BQSR 推荐资源。

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n DCS_WGS_Germline_FASTQ --output json

dcs workflow run -n DCS_WGS_Germline_FASTQ -e 001 \
  -i SampleID='NA12878' \
  -i FASTQ='[["/Files/path/to/NA12878_R1.fq.gz","/Files/path/to/NA12878_R2.fq.gz"]]' \
  -i ReferenceDir='/Files/path/to/reference' \
  -i Ploidy='2' \
  -i ApplyBQSR='true' \
  -i ApplyHaplotypeCaller='true' \
  -i OutputBqsrBam='true' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。`Array[Array[File]]` 须传嵌套 JSON 数组文本。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `filter` | Directory | QC 统计 |
| `out_rmdum_sort_bam` (+ index) | File | 排序去重 BAM（开关控制） |
| `out_bqsr_bam` (+ index) | File | BQSR BAM（开关控制） |
| `vcf` / `vcf_ploidy` (+ index) | File | 终态 VCF |
| `gvcf` / `gvcf_ploidy` (+ index) | File | gVCF |
| `out_unmapped_read1/2` | File | 未比对 reads（开关控制） |
| `out_report` | Directory | HTML/图表综合报告 |

典型结构：

```text
├── QC/
├── report/                 # *_report_cn.html / DepthDis.svg 等
├── <SampleID>.genotyper.vcf.gz
├── <SampleID>.g.vcf.gz
├── <SampleID>.bqsr.bam     # 可选
└── md5sum/
```

## 资源建议

| 任务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| `lush_aligner` | 32 | `AlignerMemorySet`=128 | 人类 30X 建议 ≥64，默认 128 |
| `lush_bqsr` | 32 | `BQSRMemorySet`=64 | — |
| `lush_HC` | 32 | `HaplotypeCallerMemorySet`=64 | 极高深度可放宽 |
| `make_unmapped_reads` | 8 | 16 | I/O 轻量 |
| `merge_ploidy_vcf` | 2 | 8 | 仅非二倍体 |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 相关：`dcs-wgs-germline-fastq-humanonly`、`dcs-build-index-fasta`

## Agent 约定

1. 引用本流程时使用确切名称 **`DCS_WGS_Germline_FASTQ`**（投递 `-n`）。
2. 必填三项：`SampleID`、`FASTQ`、`ReferenceDir`；缺一不可投。
3. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
4. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

