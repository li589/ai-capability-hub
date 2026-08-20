---
name: pangenie-wgs-sv
display_name: WGS 结构变异检测与分型
display_name_en: WGS Structural Variant Detection and Genotyping
description: 'DCS Cloud WDL "PanGenie_WGS_SV" (v1.2.0) parameter guide:
  pangenome-based WGS structural-variant genotyping from FASTQ, plus filtering,
  AnnotSV annotation, and Circos visualization. Use when the user mentions
  PanGenie, PanGenie_WGS_SV, WGS SV, structural variants, graph pangenome, or
  wants to submit this workflow. Submission still goes through the separate
  skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow
  check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「PanGenie_WGS_SV」(v1.2.0) 流程说明与填参指南：基于泛基因组从 FASTQ 做
  WGS 结构变异基因分型、过滤、AnnotSV 注释与 Circos 可视化。用户提到 PanGenie、PanGenie_WGS_SV、WGS
  SV、结构变异、图泛基因组，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其
  `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run /
  task_info）。
description_en: 'DCS Cloud WDL "PanGenie_WGS_SV" (v1.2.0) parameter guide:
  pangenome-based WGS structural-variant genotyping from FASTQ, plus filtering,
  AnnotSV annotation, and Circos visualization. Use when the user mentions
  PanGenie, PanGenie_WGS_SV, WGS SV, structural variants, graph pangenome, or
  wants to submit this workflow. Submission still goes through the separate
  skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow
  check_parameter / run / task_info).'
category: bioinformatics
version: 1.2.2
author: DCS Genpilot
disable-model-invocation: true
---

# PanGenie_WGS_SV（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `PanGenie_WGS_SV` |
| **文档版本对应流程** | V1.2.0 |
| **类型** | WGS 结构变异检测与基因型分型 |
| **适用输入** | 原始/质控后 FASTQ + 泛基因组参考 + AnnotSV 注释库 |
| **主要功能** | PanGenie SV 分型、双等位转换、AF 过滤、AnnotSV、Circos |
| **核心算法** | PanGenie, AnnotSV, Circos |

## 何时使用

- 用户要跑 / 了解 **PanGenie_WGS_SV**
- 短读长 WGS 需要基于图泛基因组的 SV 分型（尤其大插入、重复区变异）

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n PanGenie_WGS_SV` 核对线上最新规格。

## 流程简介

通过对 read 做 k-mer 计数并结合单倍型参考面板推断基因型，相对传统比对法在大型插入与重复区更具优势。流程覆盖 FASTQ→Bubble VCF→biallelic→SV 过滤→AnnotSV 注释→Circos 可视化。

V1.2.0：增强 SV 过滤与 Circos 输出。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| `RefRead` | 解析 `RefDir` 配置，映射泛基因组索引路径 | 始终执行 |
| `CheckAndMerge` | 检查/解压 FASTQ，多样本 lane 合并为单一 FASTQ | 始终执行 |
| `runPangenie` | k-mer + 面板推断，输出 Bubble VCF 与 histo | 始终执行 |
| `bubble2biallelic` | Bubble → 标准双等位 VCF，排序压缩建索引 | 始终执行 |
| `ExtractSVs` | 提取 SV 并按 AF 过滤 | 始终执行 |
| `AnnotSV` | 功能/临床注释、SV 类型计数、Circos 图 | 始终执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SampleID` | String | **必填** | 无 | 样本唯一 ID。例：`1X-test` |
| `FqFile` | Array[File] | **必填** | 无 | FASTQ 列表（SE/PE、`.fq`/`.fastq`/`.gz` 均可；内部合并） |
| `RefDir` | File | **必填** | 无 | 泛基因组参考目录，须含 `ref.json` |
| `AnnotationRef` | File | **必填** | 无 | AnnotSV 注释参考目录 |
| `Threads` | Int | 选填 | `24` | PanGenie 等核心模块线程数（≥1） |

`RefDir` 通常还含 `assemblies-all-samples-biallelic.vcf`、`assemblies-all-graph.vcf` 及 `.gf`/`.idx` 等（由 `ref.json` 指引）。

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n PanGenie_WGS_SV --output json

dcs workflow run -n PanGenie_WGS_SV -e 001 \
  -i SampleID='NA12878' \
  -i FqFile='["/Files/path/to/NA12878_R1.fq.gz","/Files/path/to/NA12878_R2.fq.gz"]' \
  -i RefDir='/Files/path/to/pangenie_ref' \
  -i AnnotationRef='/Files/path/to/AnnotSV_ref' \
  -i Threads='24' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。`Array[File]` 须传 JSON 数组文本。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `bubble_results` | File | 原始 Bubble/图谱节点 VCF |
| `histo_results` | File | k-mer 频率直方图 |
| `biallelic_results` | Directory | 双等位全量变异目录 |
| `sv_results` | File | 过滤后最终 SV VCF（`.vcf.gz`） |
| `svtbi_results` | File | 最终 SV VCF 的 Tabix 索引 |
| `annotation_results` | Directory | AnnotSV 注释目录（含 TSV） |
| `png` / `svg` | File | Circos 全基因组 SV 圈图 |
| `counts` | File | SV 类型计数（如 INS/DEL） |

典型结构：

```text
├── <SampleID>-*-filtered-sv.vcf.gz / .tbi
├── <SampleID>_AnnotSV/*.annotated.tsv
├── circos.png / circos.svg
├── pangenie-biallelic/
├── pangenie-results_genotyping.vcf
├── pangenie-results_histogram.histo
└── sv_type_counts.txt
```

## 资源建议

| 任务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| `RefRead` | 1 | 1 | 配置解析 |
| `CheckAndMerge` | 1 | 5 | I/O 合并 |
| `runPangenie` | `Threads`(24) | 50 | CPU/内存密集；>50X 可提到 64–128GB |
| `bubble2biallelic` | 1 | 30 | 加载参考面板 |
| `ExtractSVs` | 1 | 1 | 流式过滤 |
| `AnnotSV` | 1 | 20 | 注释与绘图 |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）

## Agent 约定

1. 引用本流程时使用确切名称 **`PanGenie_WGS_SV`**（投递 `-n`）。
2. 必填四项：`SampleID`、`FqFile`、`RefDir`、`AnnotationRef`；缺一不可投。
3. `RefDir` 与普通 germline `ReferenceDir` 不同，须为含 `ref.json` 的泛基因组包。
4. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
5. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

