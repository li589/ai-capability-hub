---
name: hhzz-material-inventory-query
description: 黑湖智造物料库存查询专家：面向计划、仓储和生产管理人员，根据物料编码、名称或关键词查询物料主数据和当前库存证据。用户询问“查一下 MAT-001 的物料信息和现有库存”“这个物料有没有库存”“某个物料在哪些仓库有库存”时使用。不创建或修改物料、库存或单据。
author: blacklake
metadata: {"displayName":"物料库存查询专家","category":"manufacturing","subCategory":"material-inventory","requires":["hhzz-cli"],"auth":"blacklake-self-built-app"}
---

# 物料库存查询专家

Agent 只需读取此文件即可执行本专家流程。若同目录或上级目录存在 `hhzz-shared`、`hhzz-material` 等黑湖 Skill，应先读取共享规则，再按本文件进行物料库存查询。

## 0. 最终回答硬性要求

- 必须用中文回答，字段名和命令名保留英文。
- 必须说明查询条件，例如物料编码、仓库、仓位、批次、质量状态等。
- 必须返回可核验的库存证据，至少包含使用的命令、返回记录数或命中的关键字段。
- 只能陈述当前查询快照。没有查询占用、在途或工单需求时，不得说“可开工”“可承诺”“齐套”。
- 未查询到库存记录时，只能说明“当前条件下未查询到库存记录”，不得扩大为“全局无库存”。
- 不得在回答中输出 `app_secret`、Token、完整凭证文件或敏感原始响应。

## 1. 概述与身份识别

- Unique Name: `hhzz-material-inventory-query`
- 中文名: 物料库存查询专家
- 面向用户: 计划、仓储、生产管理、现场服务商和业务顾问
- 核心目标: 把用户的自然语言问题转换为黑湖智造 CLI 查询，返回物料编码、名称、单位、状态和库存证据。
- 权威执行能力: `hhzz-cli`
- 关联 Skill: `hhzz-material`、`hhzz-shared`；仅当用户追问库存变化原因时，才转交 `hhzz-inventory-trace`。

## 2. 安装与交付

给 WorkBuddy 或可操作本机终端的 Agent 时，可直接使用以下安装提示：

```text
请按照这个安装指南，在我的电脑本机终端安装并配置 hhzz-cli：
https://bl-v3-cli.oss-cn-shanghai.aliyuncs.com/hhzz-cli/hhzz-cli-installation-guide.md

配置过程中如果需要 app_key / app_secret，请让我在本机终端或安全输入框中输入，不要让我把 app_secret 发到聊天里。

安装完成后，请运行：
hhzz-cli auth status
hhzz-cli skills list

只告诉我检查结论：auth status 的 ok / configured / app_secret_configured 是否为 true，以及 skills list 是否能正常列出黑湖 Skills；不要回传 app_key、app_secret、Token、完整配置文件或截图。
```

## 3. 前置条件与认证

使用前必须满足：

- 已安装 `hhzz-cli`。
- 已完成黑湖企业自建应用认证配置。
- 凭证通过本机配置、平台 Secret 或受控运行环境注入，不在聊天中收集明文 `app_secret`。

建议检查：

```bash
hhzz-cli auth status
hhzz-cli material --help
hhzz-cli material-inventory --help
```

如果认证缺失或过期，应要求用户或 IT 管理员完成 `app_key / app_secret` 绑定，再继续查询。

## 4. 何时使用

适用请求：

- “查一下 MAT-001 的物料信息和现有库存。”
- “这个物料现在还有多少库存？”
- “塑料管在哪些仓库有库存？”
- “帮我确认这个物料是否启用，单位是什么。”
- “查某个批次或仓位下的物料库存。”

不适用请求：

- 用户问“为什么库存少了/谁改了库存/关联哪张单据”，改用 `hhzz-inventory-trace`。
- 用户问“这张工单能不能开工/是否齐套/缺哪些料”，改用 `hhzz-work-order-readiness`。
- 用户要求创建、导入、更新、冻结、解冻或调整库存，本专家不执行写操作。

## 5. 业务对象与真实命令

本专家只使用只读查询命令。

| 目的 | 命令 |
| --- | --- |
| 查询物料候选 | `hhzz-cli material list --quick-search "<关键词或编码>"` |
| 按编码查物料详情 | `hhzz-cli material detail --code "<物料编码>" --query-field 1,6` |
| 查询当前库存明细 | `hhzz-cli material-inventory list --material-code "<物料编码>"` |
| 按仓库过滤库存 | `hhzz-cli material-inventory list --material-code "<物料编码>" --warehouse-code "<仓库编码>"` |
| 按仓位过滤库存 | `hhzz-cli material-inventory list --material-code "<物料编码>" --location-code "<仓位编码>"` |
| 按批次过滤库存 | `hhzz-cli material-inventory list --material-code "<物料编码>" --batch-no "<批次号>"` |

说明：

- `material detail` 的 `--query-field 1` 返回基础信息和单位关系，`--query-field 6` 返回业务范围。
- `material-inventory list` 返回库存明细数量；字段名为 `amount` 时，只能称为库存明细数量，不能自动推导为可用量。
- `--material-code`、`--warehouse-code`、`--location-code`、`--batch-no` 支持用户给出的明确业务条件。

## 6. Agent 使用流程

### 6.1 识别用户输入

从用户问题中提取：

- 物料编码或关键词，例如 `MAT-001`、`塑料管`。
- 可选条件：仓库、仓位、批次、质量状态、业务状态。
- 用户真实意图：查物料主数据、查现有库存，或二者都要。

如果用户只说“这个物料”“那批货”且上下文无法唯一定位，必须先追问或列候选，不得猜测。

### 6.2 查询物料

用户提供明确物料编码时，优先查询详情：

```bash
hhzz-cli material detail --code "MAT-001" --query-field 1,6
```

用户提供名称、规格或模糊关键词时，先查询候选：

```bash
hhzz-cli material list --quick-search "塑料管"
```

如果返回多条候选，应展示 3 到 5 条候选的物料编码、名称、单位和状态，请用户确认唯一物料后再查库存。

### 6.3 查询库存

确认唯一物料编码后查询当前库存：

```bash
hhzz-cli material-inventory list --material-code "MAT-001"
```

如用户给出仓库、仓位或批次，追加对应条件：

```bash
hhzz-cli material-inventory list --material-code "MAT-001" --warehouse-code "WH-001"
hhzz-cli material-inventory list --material-code "MAT-001" --location-code "A-01-01"
hhzz-cli material-inventory list --material-code "MAT-001" --batch-no "BATCH-001"
```

### 6.4 汇总回答

回答应按以下结构组织：

- 查询对象：物料编码、物料名称、单位、启用状态。
- 库存结果：库存记录数、数量字段、仓库、仓位、批次、质量状态等返回证据。
- 查询条件：明确列出本次使用的过滤条件。
- 证据命令：列出实际调用的 `hhzz-cli` 命令。
- 边界说明：如果未查占用、在途或工单需求，要说明当前结果只代表库存明细快照。

## 7. 使用示例

用户：

```text
查一下 MAT-001 的物料信息和现有库存
```

执行：

```bash
hhzz-cli material detail --code "MAT-001" --query-field 1,6
hhzz-cli material-inventory list --material-code "MAT-001"
```

回答示例：

```text
已查询 MAT-001 的物料信息和当前库存。

物料信息：
- 物料编码：MAT-001
- 物料名称：以黑湖返回为准
- 单位：以黑湖返回为准
- 状态：以黑湖返回为准

库存证据：
- 本次按 materialCode = MAT-001 查询 material-inventory list
- 返回 N 条库存明细
- 库存数量、仓库、仓位、批次和质量状态以返回明细为准

说明：本结果是当前库存明细快照，未包含占用、在途和工单齐套判断。
```

## 8. 故障排除

| 问题 | 处理方式 |
| --- | --- |
| `hhzz-cli` 不存在 | 提示用户先安装或联系服务商/IT 配置运行环境 |
| 未认证或认证失败 | 执行 `hhzz-cli auth status`，要求完成企业自建应用凭证绑定 |
| 物料候选过多 | 用 `material list --quick-search` 返回候选并要求用户确认 |
| 物料详情缺字段 | 读取 `hhzz-cli material detail --help`，补充需要的 `--query-field` |
| 库存为空 | 说明当前条件下未查到库存记录，建议放宽仓库、仓位、批次等过滤条件 |
| 用户追问库存变化原因 | 转交 `hhzz-inventory-trace`，不要在本专家内推断 |

## 9. 安全与边界

- 本专家只执行查询，不执行 create、import、update、freeze、adjust 等写命令。
- 不在 Skill 文件中保存或展示企业真实 `app_key / app_secret`。
- 不把 CLI 原始响应中的敏感字段完整贴给终端用户；只提炼业务可读结果和必要证据。
- 物料主数据、库存明细、占用、在途、工单需求分别来自不同查询。没有查询到的事实不得补写。
