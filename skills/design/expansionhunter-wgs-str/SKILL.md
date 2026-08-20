---
name: expansionhunter-wgs-str
display_name: WGS 短串联重复扩增检测
display_name_en: WGS Short Tandem Repeat Expansion Detection
description: 'DCS Cloud WDL "ExpansionHunter_WGS_STR" (v1.1.0) parameter guide: detect short tandem repeat (STR) expansions from WGS BAM with sex-aware genotyping. Use when the user mentions ExpansionHunter, ExpansionHunter_WGS_STR, WGS STR, short tandem repeats, triplet-repeat disorders, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
description_zh: DCS Cloud WDL「ExpansionHunter_WGS_STR」(v1.1.0) 流程说明与填参指南：基于 BAM 做 WGS 短串联重复(STR)扩增检测与性别感知基因分型。用户提到 ExpansionHunter、ExpansionHunter_WGS_STR、WGS STR、短串联重复、三联体扩增病，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其 `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run / task_info）。
description_en: 'DCS Cloud WDL "ExpansionHunter_WGS_STR" (v1.1.0) parameter guide: detect short tandem repeat (STR) expansions from WGS BAM with sex-aware genotyping. Use when the user mentions ExpansionHunter, ExpansionHunter_WGS_STR, WGS STR, short tandem repeats, triplet-repeat disorders, or wants to submit this workflow. Submission still goes through the separate skill dcs-cli (see its `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run / task_info).'
category: bioinformatics
version: 1.1.1
author: DCS Genpilot
---
# ExpansionHunter_WGS_STR（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `ExpansionHunter_WGS_STR` |
| **文档版本对应流程** | V1.1.0 |
| **类型** | WGS 短串联重复序列 (STR) 扩增检测 |
| **适用输入** | 坐标排序 BAM + BAI + 参考目录 |
| **主要功能** | 致病相关 STR 扩增检测、性别感知基因分型 |
| **开源协议** | Apache-2.0 |

## 何时使用

- 用户要跑 / 了解 **ExpansionHunter_WGS_STR**
- 已有排序 BAM，需要 STR 扩增 call（遗传病相关重复位点）

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n ExpansionHunter_WGS_STR` 核对线上最新规格。

## 流程简介

基于 ExpansionHunter，针对 WGS BAM 结合致病性 STR Variant Catalog 做扩增分析与基因分型；V1.1.0 将性别改为布尔参数 `Male`（`true`→male，`false`→female），便于防错配置。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| STR 变异检测 | 调用 ExpansionHunter，结合参考与 Variant Catalog 做性别特异性 STR 分型 | 始终执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `SampleID` | String | **必填** | 无 | 样本唯一 ID。例：`NA12878` |
| `ReferenceDir` | File | **必填** | 无 | 参考目录，须含 `reference_info.json`（解析 `ref_fasta`） |
| `Male` | Boolean | **必填** | 无 | 性别：`true`=男性，`false`=女性 |
| `Bam` | File | **必填** | 无 | 坐标排序 BAM |
| `BamIndex` | File | **必填** | 无 | 对应 `.bai`，须与 Bam 匹配 |
| `cpu` | Int | 选填 | `10` | CPU 线程数（≥1） |

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n ExpansionHunter_WGS_STR --output json

dcs workflow run -n ExpansionHunter_WGS_STR -e 001 \
  -i SampleID='NA12878' \
  -i ReferenceDir='/Files/path/to/reference' \
  -i Male='true' \
  -i Bam='/Files/path/to/sample.bam' \
  -i BamIndex='/Files/path/to/sample.bam.bai' \
  -i cpu='10' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `STR_DIR` | Directory | ExpansionHunter 全部结果（JSON / realigned BAM / VCF） |

典型结构：

```text
STR/
├── <SampleID>.json              # STR 详细统计与报告
├── <SampleID>_realigned.bam     # 目标区重比对（IGV 核查）
└── <SampleID>.vcf               # 标准 STR 基因型 VCF
```

## 资源建议

| 参数 | 默认 | 建议 | 说明 |
|------|------|------|------|
| `cpu` | 10 | 8–16 | 按节点与 BAM 规模调整 |
| 内存 | 20 GB（任务固定） | — | 磁盘预留需覆盖 BAM + 参考 |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）

## Agent 约定

1. 引用本流程时使用确切名称 **`ExpansionHunter_WGS_STR`**（投递 `-n`）。
2. 必填五项：`SampleID`、`ReferenceDir`、`Male`、`Bam`、`BamIndex`；缺一不可投。
3. 务必向用户确认性别对应的 `Male` 布尔值，勿默认猜测。
4. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
5. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

