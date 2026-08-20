---
name: dcs-wes-germline-fastq
display_name: WES 胚系变异检测
display_name_en: WES Germline Variant Detection
description: 'DCS Cloud WDL "DCS_WES_Germline_FASTQ" (v1.0.1) parameter guide: WES germline variant calling from FASTQ (QC, alignment, BQSR, targeted HaplotypeCaller, report). Use when the user mentions DCS_WES_Germline_FASTQ, WES Germline, whole-exome germline, IntervalBed, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「DCS_WES_Germline_FASTQ」(v1.0.1) 流程说明与填参指南：从 FASTQ 做 WES 胚系变异检测（质控、比对、BQSR、靶区 HC、报告）。用户提到 DCS_WES_Germline_FASTQ、WES Germline、全外显子胚系、IntervalBed，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "DCS_WES_Germline_FASTQ" (v1.0.1) parameter guide: WES germline variant calling from FASTQ (QC, alignment, BQSR, targeted HaplotypeCaller, report). Use when the user mentions DCS_WES_Germline_FASTQ, WES Germline, whole-exome germline, IntervalBed, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.0.2
author: DCS Genpilot
---
# DCS_WES_Germline_FASTQ（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `DCS_WES_Germline_FASTQ` |
| **文档版本对应流程** | V1.0.1 |
| **类型** | 全外显子测序 (WES) 胚系变异检测 |
| **适用输入** | 原始 FASTQ 或 arcseq + 参考目录 + 捕获 BED |
| **主要功能** | 质控过滤、比对去重、BQSR、靶区变异检测、综合报告 |
| **测序策略** | 自动兼容 SE / PE |

## 何时使用

- 用户要跑 / 了解 **DCS_WES_Germline_FASTQ**
- 已有 WES FASTQ，需要在捕获区间内 call SNP/Indel 并出报告

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n DCS_WES_Germline_FASTQ` 核对线上最新规格。

## 流程简介

从原始 FASTQ 出发：接头/低质量过滤 → 比对排序去重 →（可选）BQSR → 限定 `IntervalBed` 做 HaplotypeCaller（gVCF→VCF）→ 汇总 QC 与 HTML 综合报告。自动按 `FASTQ` 内层数组长度推断 PE（长度 2）或 SE。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| `lush_aligner` | 过滤、比对、排序、MarkDup、基础 QC | 始终执行 |
| `make_unmapped_reads` | 提取未比对 reads → FASTQ | `OutputUnmappedReads = true` |
| `lush_bqsr` | 碱基质量重校正 | `ApplyBQSR = true` 且参考含 known sites/dbSNP |
| `lush_HC` | 靶区 gVCF/VCF + 综合报告 | `ApplyHaplotypeCaller = true` |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SampleID` | String | **必填** | 无 | 样本 ID / 输出前缀。例：`NA12878` |
| `FASTQ` | Array[Array[File]] | **必填** | 无 | PE：`[[R1,R2]]`；SE：`[[Read]]`；`.fq.gz` 或 arc |
| `ReferenceDir` | File | **必填** | 无 | 参考资源目录，须含 `reference_info.json` |
| `IntervalBed` | File | **必填** | 无 | 捕获靶区 BED（WES 特有） |
| `arcDir` | File? | 选填 | 无 | SeqArc 索引目录；标准 fq.gz 可留空 |
| `Adapter1` | String | 选填 | `AAGTCGGAGGCCA...` | Read1 接头 |
| `Adapter2` | String | 选填 | `AAGTCGGATCGTA...` | Read2 接头 |
| `SOAPnukeLowQual` | String | 选填 | `"12"` | 低质量碱基阈值 |
| `SOAPnukeLowQualityRate` | String | 选填 | `"0.5"` | 单 read 低质量碱基最大比例 |
| `SOAPnukeNRate` | String | 选填 | `"0.1"` | 单 read N 比例上限 |
| `StandCallConf` | String | 选填 | `"30"` | 变异调用置信度阈值 |
| `IncludeNonVariantSites` | Boolean | 选填 | `false` | 是否输出非变异位点 |
| `OutputUnmappedReads` | Boolean | 选填 | `false` | 是否输出未比对 FASTQ |
| `OutputSortMarkdupBam` | Boolean | 选填 | `false` | 是否输出排序去重中间 BAM |
| `OutputBqsrBam` | Boolean | 选填 | `false` | 是否输出 BQSR BAM |
| `ApplyFilter` | Boolean | 选填 | `true` | 比对前是否过滤接头/低质量 |
| `ApplyBQSR` | Boolean | 选填 | `true` | 是否启用 BQSR（依赖参考库） |
| `ApplyHaplotypeCaller` | Boolean | 选填 | `true` | 是否做变异检测与报告 |
| `AlignerMemorySet` | Int | 选填 | `128` | 比对模块内存 GB |
| `BQSRMemorySet` | Int | 选填 | `64` | BQSR 内存 GB |
| `HaplotypeCallerMemorySet` | Int | 选填 | `64` | HC 内存 GB |

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n DCS_WES_Germline_FASTQ --output json

dcs workflow run -n DCS_WES_Germline_FASTQ -e 001 \
  -i SampleID='NA12878' \
  -i FASTQ='[["/Files/path/to/NA12878_R1.fq.gz","/Files/path/to/NA12878_R2.fq.gz"]]' \
  -i ReferenceDir='/Files/path/to/reference' \
  -i IntervalBed='/Files/path/to/exome_targets.bed' \
  -i ApplyBQSR='true' \
  -i ApplyHaplotypeCaller='true' \
  -i OutputBqsrBam='true' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。`Array[Array[File]]` 须传嵌套 JSON 数组文本。

## 输出

| 输出变量 | 类型 | 条件 | 说明 |
|----------|------|------|------|
| `filter` | Directory | 始终 | QC 质控目录 |
| `out_rmdum_sort_bam` (+ index) | File | `OutputSortMarkdupBam` | 排序去重 BAM |
| `out_bqsr_bam` (+ index) | File | `OutputBqsrBam` | BQSR BAM |
| `vcf` / `gvcf` (+ index) | File | `ApplyHaplotypeCaller` | 终态 VCF / gVCF |
| `out_unmapped_read1/2` | File | `OutputUnmappedReads` | 未比对 reads |
| `out_report` | Directory | `ApplyHaplotypeCaller` | HTML/图表综合报告 |

典型结构：

```text
├── QC/
├── report/                 # *_report_cn.html / svg / *stat.xls
├── <SampleID>.genotyper.vcf.gz
├── <SampleID>.g.vcf.gz
├── <SampleID>.bqsr.bam     # 可选
└── md5sum/
```

## 资源建议

| 参数 | 默认 | 建议 | 说明 |
|------|------|------|------|
| `AlignerMemorySet` | 128 | 64–128 | 常规 100X WES 面板约 64GB 可跑 |
| `BQSRMemorySet` | 64 | 默认即可 | — |
| `HaplotypeCallerMemorySet` | 64 | 32–64 | 仅扫靶区，通常无需放大 |

各主任务默认约 32 CPU。

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 相关：`dcs-build-index-fasta`

## Agent 约定

1. 引用本流程时使用确切名称 **`DCS_WES_Germline_FASTQ`**（投递 `-n`）。
2. 必填四项：`SampleID`、`FASTQ`、`ReferenceDir`、`IntervalBed`；缺一不可投。
3. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
4. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

