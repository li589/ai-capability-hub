---
name: saw-st-v8-gef2gem
display_name: 空间转录组 GEF 转 GEM
display_name_en: Spatial Transcriptomics GEF to GEM Conversion
description: 'DCS Cloud WDL "SAW-ST-V8-gef2gem" (v1.2.0) parameter guide:
  convert SAW GEF spatial expression matrices to GEM text matrices (Square Bin
  or Cellbin). Use when the user mentions SAW-ST-V8-gef2gem, gef2gem,
  GEF-to-GEM, spatial matrix format conversion, or wants to submit this
  workflow. Submission still goes through the separate skill dcs-cli (see its
  `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run
  / task_info).'
description_zh: DCS Cloud WDL「SAW-ST-V8-gef2gem」(v1.2.0) 流程说明与填参指南：将 SAW 产出的 GEF
  空间表达矩阵转为 GEM 文本矩阵（Square Bin 或 Cellbin）。用户提到 SAW-ST-V8-gef2gem、gef2gem、GEF 转
  GEM、空间矩阵格式转换，或要投递该流程时使用。投递动作仍走独立 skill dcs-cli（详见其
  `references/dcs-wdl-manager.md`；命令：dcs workflow check_parameter / run /
  task_info）。
description_en: 'DCS Cloud WDL "SAW-ST-V8-gef2gem" (v1.2.0) parameter guide:
  convert SAW GEF spatial expression matrices to GEM text matrices (Square Bin
  or Cellbin). Use when the user mentions SAW-ST-V8-gef2gem, gef2gem,
  GEF-to-GEM, spatial matrix format conversion, or wants to submit this
  workflow. Submission still goes through the separate skill dcs-cli (see its
  `references/dcs-wdl-manager.md`; commands: dcs workflow check_parameter / run
  / task_info).'
category: bioinformatics
version: 1.2.1
author: DCS Genpilot
disable-model-invocation: true
---

# SAW-ST-V8-gef2gem（WDL 插件）

本 skill 提供该流程的**领域知识**（适用场景、参数、输出）。实际 list / check / submit / 查进度见独立 skill **dcs-cli**（WDL 细节见其 `references/dcs-wdl-manager.md`）。

| 项 | 值 |
|----|-----|
| **流程名** | `SAW-ST-V8-gef2gem` |
| **文档版本对应流程** | V1.2.0 |
| **类型** | 空间转录组数据格式转换 |
| **适用输入** | SAW 产出的 Bin 级 GEF；可选 Cellbin GEF |
| **主要功能** | GEF → GEM，便于兼容传统文本矩阵工具 |
| **计费** | free |

## 何时使用

- 用户要跑 / 了解 **SAW-ST-V8-gef2gem**
- 已有主流程 GEF，需要导出 GEM 给下游工具

不要用本 skill 代替通用投递流程；填参前仍建议 `dcs workflow check_parameter -n SAW-ST-V8-gef2gem` 核对线上最新规格。

## 流程简介

轻量辅助流程，调用 `saw convert gef2gem`：

- **Square Bin（默认）**：仅提供 `Gef`，按 `BinSize` 转对应分辨率 GEM。
- **Cellbin**：同时提供 `CellbinGef`，与 `Gef` 联合转换，输出 Cellbin GEM。

常作 `SAW-ST-V8` 下游步骤。

## 分析模块

| 模块 | 功能 | 条件 |
|------|------|------|
| gef2gem | 执行 `saw convert gef2gem`，结果写入 `result/`；有 `CellbinGef` 走 Cellbin 分支，否则按 `BinSize` 转 Square Bin | 始终执行 |

## 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `Gef` | File | **必填** | 无 | Bin 级 `.gef`；通常来自主流程 `feature_expression` |
| `CellbinGef` | File | 选填 | 无 | Cellbin `.gef`；提供则启用 Cellbin 模式 |
| `BinSize` | Int | 选填 | `1` | Square Bin 的 bin 尺寸；仅无 `CellbinGef` 时生效 |
| `Mem` | Int | **必填** | `24` | 内存 GB（≥4）；大 GEF 可上调 |

逻辑：`CellbinGef` 存在 → `--cellbin-gef --gef --cellbin-gem`；否则 → `--gef --bin-size --gem`。

## 投递示例（CLI）

路径用 DCS 规范（如 `/Files/...`）。投递前向用户确认参数摘要。

```bash
dcs workflow check_parameter -n SAW-ST-V8-gef2gem --output json

# Square Bin
dcs workflow run -n SAW-ST-V8-gef2gem -e 001 \
  -i Gef='/Files/path/to/sample.bin20.gef' \
  -i BinSize='20' \
  -i Mem='24' \
  --output json

# Cellbin
dcs workflow run -n SAW-ST-V8-gef2gem -e 002 \
  -i Gef='/Files/path/to/sample.bin.gef' \
  -i CellbinGef='/Files/path/to/sample.cellbin.gef' \
  -i Mem='32' \
  --output json

dcs workflow task_info <task-id> --output json
```

多样本用 `--table` / `-j`（见 wdl-manager）。

## 输出

| 输出变量 | 类型 | 说明 |
|----------|------|------|
| `out_gef2gem` | Directory | 转换结果目录（含生成的 GEM） |

```text
result/
├── sample_bin20.gem      # Square Bin：{Gef基名}.gem
└── sample_cellbin.gem    # Cellbin：{CellbinGef基名}.gem
```

## 资源建议

| 参数 | 默认 | 建议 | 说明 |
|------|------|------|------|
| CPU | 1（固定） | — | 不可调 |
| `Mem` | 24 | 16–64 | 常规 Bin GEF 用默认；超大/高分辨率 Cellbin 可 32–48 |

## 关联 SKILL

- 投递与查进度：`dcs-cli`（WDL 细节见其 `references/dcs-wdl-manager.md`）
- 同系列：`saw-st-v8`

## Agent 约定

1. 引用本流程时使用确切名称 **`SAW-ST-V8-gef2gem`**（投递 `-n`）。
2. 必填：`Gef`、`Mem`；`BinSize` 仅 Square Bin 模式有意义。
3. 填参以线上 `check_parameter` 为准；本文与线上不一致时以线上为准并告知用户。
4. 不在本 skill 内承诺 Hermes Plan/哨兵/离线回调自动续跑。

