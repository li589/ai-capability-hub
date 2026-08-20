---
name: saw-st-v8-makeref
display_name: 空间转录组参考基因组构建
display_name_en: Spatial Transcriptomics Reference Genome Construction
description: 'DCS Cloud WDL "SAW-ST-V8-makeRef" (v1.2.0) parameter guide: build the reference genome index (e.g. STAR) or custom database directory required by SAW count. Use when the user mentions SAW-ST-V8-makeRef, makeRef, SAW reference genome, STAR index construction, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「SAW-ST-V8-makeRef」(v1.2.0) 流程说明与填参指南：构建 SAW count 所需的参考基因组索引（如 STAR）或自定义数据库目录。用户提到 SAW-ST-V8-makeRef、makeRef、SAW 参考基因组、STAR 索引构建，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "SAW-ST-V8-makeRef" (v1.2.0) parameter guide: build the reference genome index (e.g. STAR) or custom database directory required by SAW count. Use when the user mentions SAW-ST-V8-makeRef, makeRef, SAW reference genome, STAR index construction, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.2.1
author: DCS Genpilot
---
# SAW-ST-V8-makeRef（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `SAW-ST-V8-makeRef` |
| **文档版本对应流程** | V1.2.0 |
| **类型** | 空间转录组参考基因组构建 |
| **适用输入** | 参考 FASTA、GTF/GFF、可选 rRNA FASTA；或预设 Database |
| **主要功能** | 构建比对索引（默认 STAR）及标准参考目录，供后续 SAW count 使用 |

## 何时使用

- 用户要跑 / 了解 **SAW-ST-V8-makeRef**
- 尚无现成 SAW 参考索引，需从 FASTA/GTF 构建后再投 `SAW-ST-V8`
- 需要按 Database 模式组装特定库（如 Kraken 类）

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n SAW-ST-V8-makeRef` 核对线上最新规格。

## 流程简介

SAW 主分析前置准备：接收基因组 FASTA 与注释 GTF/GFF（及可选 rRNA），构建高效比对索引与标准参考目录；若提供 `Database`，则切到自定义数据库组装模式。产出目录是后续 count 的必备输入。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| 标准参考基因组构建 | 基于 FASTA + GTF（+ rRNA）建标准目录与 STAR 等索引 | 未提供 `Database` |
| 自定义数据库构建 | 以特定模式处理 FASTA 并重组目标数据库（如微生物鉴定） | 提供 `Database` |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `ReferenceName` | String | **必填** | 无 | 参考名，亦为输出根目录名。例：`mm10`、`GRCh38` |
| `Mode` | String | **必填** | 无 | 构建模式，如 `"STAR"`；影响目录层级 |
| `Fasta` | Array[File] | 选填 | 无 | 参考 FASTA（可多文件）；标准模式强烈建议提供 |
| `GTF` | File | 选填 | 无 | `.gtf` / `.gff` 注释 |
| `rRNAfasta` | File | 选填 | 无 | rRNA FASTA，供后续过滤 rRNA |
| `Database` | File | 选填 | 无 | 预设数据库源；提供则切至 krakenDB 类分支，忽略 GTF 等 |
| `ParamsConfig` | String | 选填 | `""` | 额外底层参数配置路径或字符串 |
| `Mem` | Int | 选填 | `90` | 基础内存 GB（≥16）；实际申请 `Mem + 10` |

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。Array 参数传 JSON 数组文本。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n SAW-ST-V8-makeRef --output json

dcs workflow run -n SAW-ST-V8-makeRef -e 001 \
  -i ReferenceName='mm10' \
  -i Mode='STAR' \
  -i Fasta='["/Files/path/to/GRCm38.primary_assembly.genome.fa"]' \
  -i GTF='/Files/path/to/gencode.vM23.annotation.gtf' \
  -i rRNAfasta='/Files/path/to/rrna.fa' \
  -i Mem='90' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `out_count` | Directory | 以 `ReferenceName` 命名的参考/索引结果目录 |

标准模式结构示意（`ReferenceName=mm10`, `Mode=STAR`）：

```text
input.json
mm10/
└── STAR/
    ├── *_ref.log
    ├── fasta/          # 参考 FASTA
    ├── genes/          # GTF
    └── STAR/           # Genome / SA / SAindex / sjdb* / *Info.tab 等
```

人/小鼠完整 STAR 索引子目录通常约 25–30 GB。

## 资源建议

| 任务 | CPU | 内存 | 说明 |
|------|-----|------|------|
| makeRef | 8 | `Mem + 10`（默认约 100） | 多线程构建 |

| 物种规模 | 建议 `Mem` |
|----------|------------|
| 哺乳动物（人/小鼠） | `90` |
| 植物/大基因组 | `120+` |
| 微生物/小基因组 | `16`–`32` |

索引构建偏内存与 I/O；节点内存与磁盘不足易超时或 OOM。

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 同系列：`saw-st-v8`

## Agent 约定

1. 引用本流程时使用确切名称 **`SAW-ST-V8-makeRef`**（投递 `-n`；大小写与线上一致）。
2. 必填：`ReferenceName`、`Mode`；标准模式务必准备好 `Fasta`（及通常 `GTF`）。
3. `Fasta` 为 `Array[File]`，投递用 JSON 数组文本。
4. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
5. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

