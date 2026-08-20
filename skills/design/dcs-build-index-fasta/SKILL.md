---
name: dcs-build-index-fasta
display_name: 参考基因组索引构建
display_name_en: Reference Genome Index Construction
description: 'DCS Cloud WDL "DCS_Build_Index_FASTA" (v2.0.0) parameter guide:
  build reference genome indexes, sequence dictionary, and known-sites resources
  from a raw FASTA. Use when the user mentions DCS_Build_Index_FASTA, Build
  Index FASTA, reference genome index construction, reference_info.json, or
  wants to submit this workflow. Submission still goes through the separate
  skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow
  check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「DCS_Build_Index_FASTA」(v2.0.0) 流程说明与填参指南：由原始 FASTA
  构建参考基因组索引、序列字典及已知位点资源库。用户提到 DCS_Build_Index_FASTA、Build Index
  FASTA、参考基因组索引构建、reference_info.json，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其
  `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run /
  task_info）。
description_en: 'DCS Cloud WDL "DCS_Build_Index_FASTA" (v2.0.0) parameter guide:
  build reference genome indexes, sequence dictionary, and known-sites resources
  from a raw FASTA. Use when the user mentions DCS_Build_Index_FASTA, Build
  Index FASTA, reference genome index construction, reference_info.json, or
  wants to submit this workflow. Submission still goes through the separate
  skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow
  check_parameter / run / task_info).'
category: bioinformatics
version: 2.0.1
author: DCS Genpilot
disable-model-invocation: true
---

# DCS_Build_Index_FASTA（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `DCS_Build_Index_FASTA` |
| **文档版本对应流程** | V2.0.0 |
| **类型** | 参考基因组索引构建 (Reference Index Building) |
| **适用输入** | 原始 FASTA + 可选 dbSNP / Known Sites / ALT |
| **主要功能** | 构建比对索引、`.dict`/`.fai`、微型 VCF 资源，并生成 `reference_info.json` |

## 何时使用

- 用户要跑 / 了解 **DCS_Build_Index_FASTA**
- 需要为下游 WGS/WES 胚系流程准备带 `reference_info.json` 的参考目录

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n DCS_Build_Index_FASTA` 核对线上最新规格。

## 流程简介

接收原始 FASTA，生成比对与 GATK/Picard 所需的全套索引组件；可选处理 dbSNP 与 Known Sites（微型 VCF + CSI），并汇总为统一 `reference/` 目录与 `reference_info.json`，供下游流程直接挂载。

V2.0.0：修复超长行 FASTA 导致 `.fai` 异常；支持低内存索引模式。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| 参考序列整理与基础索引 | 规范化 FASTA（及可选 ALT）；构建比对索引、`.dict`、`.fai` | 始终执行 |
| 低内存索引生成 | 额外生成 `.0123`、`.bwt.2bit.64` 等 | `UseLowMemoryIndex = true` |
| 已知变异位点处理 | Known Sites → 微型 VCF，写入 `known_site/` | 提供 `KnownSiteVcfs` |
| dbSNP 处理 | 提取微型 VCF + `.csi` | 提供 `dbsnpVcf` |
| 资源清单生成 | 写出 `reference_info.json` | 始终执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `ReferenceName` | String | **必填** | 无 | 输出前缀名。例：`hg38`、`GRCh38` |
| `ReferenceFasta` | File | **必填** | 无 | 原始参考 FASTA（`.fa` / `.fasta`） |
| `Species` | String | **必填** | 无 | 物种标记。例：`human`、`mouse` |
| `dbsnpVcf` | File? | 选填 | 无 | dbSNP VCF，建议 `.vcf.gz` |
| `KnownSiteVcfs` | Array[File]? | 选填 | 无 | 已知位点 VCF 列表（1000G/HapMap/Mills 等） |
| `ReferenceAlt` | File? | 选填 | 无 | ALT contig（常为 `.fa.alt`），提升 HLA 等区域比对 |
| `UseLowMemoryIndex` | Boolean | 选填 | `false` | 是否生成低内存比对索引 |
| `MemorySet` | Int | 选填 | `100` | 任务内存 GB（≥32）；人类 hg38 建议 100 |

逻辑要点：传入 `KnownSiteVcfs` / `dbsnpVcf` 时内部自动开启对应提取；`UseLowMemoryIndex`、`ReferenceAlt` 影响条件输出文件。

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n DCS_Build_Index_FASTA --output json

dcs workflow run -n DCS_Build_Index_FASTA -e 001 \
  -i ReferenceName='hg38' \
  -i ReferenceFasta='/Files/path/to/hg38.fa' \
  -i Species='human' \
  -i dbsnpVcf='/Files/path/to/dbsnp.vcf.gz' \
  -i KnownSiteVcfs='["/Files/path/to/1000G_omni.vcf.gz","/Files/path/to/Mills.vcf.gz"]' \
  -i ReferenceAlt='/Files/path/to/hg38.fa.alt' \
  -i UseLowMemoryIndex='false' \
  -i MemorySet='100' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。`Array[File]` 须传 JSON 数组文本。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| （结果目录） | Directory | 通常为打包后的 `reference/` 资源目录 |

典型结构：

```text
reference/
├── <ReferenceName>.fa / .fa.fai / .dict
├── <ReferenceName>.fa.amb / .ann / .pac
├── <ReferenceName>.fa.alt                    # 条件
├── <ReferenceName>.fa.0123 / .bwt.2bit.64    # UseLowMemoryIndex
├── dbsnp_*.vcf.gz / .csi                     # 条件
├── known_site/                               # 条件
│   ├── *.vcf.gz
│   └── known_site.txt
└── reference_info.json
```

## 资源建议

| 参数 | 默认 | 建议 | 说明 |
|------|------|------|------|
| CPU | 32 | 固定于任务 | 索引构建任务默认 32 核 |
| `MemorySet` | 100 GB | 64–128 | 人类基因组建议 ≥100；OOM 提至 128；小基因组可 16–32 |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 下游常用：`dcs-wgs-germline-fastq`、`dcs-wes-germline-fastq`

## Agent 约定

1. 引用本流程时使用确切名称 **`DCS_Build_Index_FASTA`**（投递 `-n`）。
2. 必填三项：`ReferenceName`、`ReferenceFasta`、`Species`；缺一不可投。
3. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
4. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

