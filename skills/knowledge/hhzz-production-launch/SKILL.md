---
name: hhzz-production-launch
description: 黑湖智造新品投产专家：面向产品、工艺、计划和服务商，根据新品成品、投入物料、工艺路线、BOM 和计划数量，把已确认的生产定义推进到工单下发和生产任务生成。
author: blacklake
metadata: {"displayName":"新品投产专家","category":"manufacturing","subCategory":"production-launch","requires":["hhzz-cli"],"auth":"blacklake-self-built-app"}
---

# 新品投产专家

Agent 只需读取此文件即可执行本专家流程。若同目录或上级目录存在 `hhzz-shared`、`hhzz-material`、`hhzz-bom`、`hhzz-work-order` 等黑湖 Skill，应先读取共享规则，再按本文件推进新品投产。

## 0. 最终回答硬性要求

- 必须用中文回答，字段名和命令名保留英文。
- 必须说明投产对象，例如成品编码、BOM 版本、工艺路线、工单编号和生产任务编号。
- 必须返回可核验的阶段证据，至少包含主数据、生产定义、BOM、工单和生产任务的查询结果。
- 终点只能描述为“生产任务已生成”或“投产准备推进到某一步”。没有领料、投料、报工或完工证据时，不得说生产已经开始或完成。
- 写操作必须先 `--dry-run`，用户明确确认后才能 `--confirm`。
- 不得在回答中输出 `app_secret`、Token、完整凭证文件或敏感原始响应。

## 1. 概述与身份识别

- Unique Name: `hhzz-production-launch`
- 中文名: 新品投产专家
- 面向用户: 产品、工艺、计划、生产管理、现场服务商和业务顾问
- 核心目标: 把用户已确认的新品生产定义，通过黑湖智造 CLI 推进到工单下发和待执行生产任务。
- 权威执行能力: `hhzz-cli`
- 关联 Skill: `hhzz-shared`、`hhzz-material`、`hhzz-bom`、`hhzz-work-order`、`hhzz-produce-task`。

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
- 当前企业自建应用具备物料、单位、工序、工作中心、工艺路线、BOM、工单和生产任务相关权限。
- 凭证通过本机配置、平台 Secret 或受控运行环境注入，不在聊天中收集明文 `app_secret`。

建议检查：

```bash
hhzz-cli auth status
hhzz-cli skills list
hhzz-cli schema work-order import
hhzz-cli schema work-order issue
```

如果认证缺失、权限不足或写入合同无法读取，应要求用户或 IT 管理员补齐权限后再继续。

## 4. 何时使用

允许在完成业务审计、`--dry-run` 和用户确认后调用 `work-order issue` 下发生产工单，并回查生成的生产任务。该能力只推进计划状态，不执行领料、投料、报工、完工或库存变化。

适用请求：

- “帮我把这个新品投产，并生成生产任务。”
- “为这个成品建立工艺路线、BOM 和生产工单。”
- “把这张新品工单下发，并确认任务是否生成。”
- “我已经确认成品、用料和工序，帮我走到待执行生产任务。”

不适用请求：

- 用户只想查询或维护单个物料、BOM、工艺路线或工单时，改用对应单对象能力。
- 用户要求领料、投料、报工、完工或现实生产执行时，本专家不继续执行。
- 用户没有确认成品、投入物料、工序、计划数量和时间时，不直接创建生产对象。

## 5. 业务对象与真实命令

本专家会使用查询和写入命令。写入命令必须先预览，再确认执行。

| 目的 | 命令 |
| --- | --- |
| 检查认证 | `hhzz-cli auth status` |
| 查询单位 | `hhzz-cli unit list --quick-search "<单位名称或编码>"` |
| 查询物料 | `hhzz-cli material list --quick-search "<物料编码或关键词>"` |
| 查询物料详情 | `hhzz-cli material detail --code "<物料编码>" --query-field 1,6,8` |
| 导入物料 | `hhzz-cli material import --body-json '<JSON>' --dry-run` |
| 导入工序 | `hhzz-cli process import --body-json '<JSON>' --dry-run` |
| 导入工作中心 | `hhzz-cli work-center import --body-json '<JSON>' --dry-run` |
| 导入工艺路线 | `hhzz-cli process-route import --body-json '<JSON>' --dry-run` |
| 查询工艺路线 | `hhzz-cli process-route detail --code "<工艺路线编码>"` |
| 导入 BOM | `hhzz-cli bom import --body-json '<JSON>' --dry-run` |
| 启用 BOM | `hhzz-cli bom update status --body-json '<JSON>' --dry-run` |
| 查询 BOM | `hhzz-cli bom detail --material-code "<成品编码>" --version "<BOM版本>"` |
| 导入工单 | `hhzz-cli work-order import --body-json '<JSON>' --dry-run` |
| 查询工单基本信息 | `hhzz-cli work-order detail base --code "<工单编号>"` |
| 查询工单产出 | `hhzz-cli work-order detail output --code "<工单编号>"` |
| 查询工单用料 | `hhzz-cli work-order detail input-material --code "<工单编号>"` |
| 查询工单工序计划 | `hhzz-cli work-order detail process-plan --code "<工单编号>"` |
| 下发工单 | `hhzz-cli work-order issue --body-json '<JSON>' --dry-run` |
| 查询生产任务 | `hhzz-cli produce-task list --quick-search "<工单或任务编号>"` |
| 查询生产任务详情 | `hhzz-cli produce-task detail --task-code "<生产任务编号>"` |
| 查询任务计划数 | `hhzz-cli produce-task list planned-amount --task-code "<生产任务编号>"` |

说明：

- `material detail` 查询成品时必须包含 `--query-field 6,8`，用于确认业务范围和生产信息。
- `bom import` 后不能只凭 `ok: true` 进入下一步，必须用 `bom detail` 回查结构和状态。
- `work-order import` 和 `work-order issue` 均为写操作，真实执行必须把 `--dry-run` 替换为 `--confirm`，且需要用户明确确认。

## 6. Agent 使用流程

### 6.1 识别用户输入

从用户问题中提取：

- 成品编码、成品名称、生产单位和计划生产数量。
- 投入物料编码、用量、单位和投料工序。
- 工序顺序、工作中心和工艺路线编码。
- BOM 版本、工单编号、计划开始时间和计划结束时间。

如果用户只说“这个新品”“按上次一样”且上下文无法唯一定位，必须先追问或列候选，不得猜测。

### 6.2 查询和验收主数据

先查询单位、成品和投入物料：

```bash
hhzz-cli unit list --quick-search "根"
hhzz-cli material detail --code "FG-001" --query-field 1,6,8
hhzz-cli material detail --code "RM-001" --query-field 1,6
```

验收要求：

- 单位存在且可用。
- 投入物料存在且可用。
- 成品的 `bizRange` 包含自制业务范围，且生产单位有效。
- 对象编码和用户业务含义一致；同编码对象含义冲突时停止。

### 6.3 准备生产定义

按用户确认的工序和工作中心准备生产定义：

```bash
hhzz-cli process import --body-json '<JSON>' --dry-run
hhzz-cli work-center import --body-json '<JSON>' --dry-run
hhzz-cli process-route import --body-json '<JSON>' --dry-run
hhzz-cli process-route detail --code "ROUTE-FG-001"
```

验收要求：

- 工序顺序、工作中心、适用成品、单位和启用状态与目标一致。
- 工艺路线未启用或关系不一致时停止，不进入 BOM 阶段。

### 6.4 准备并启用 BOM

先导入停用状态 BOM，回查结构正确后再启用：

```bash
hhzz-cli bom import --body-json '<JSON>' --dry-run
hhzz-cli bom detail --material-code "FG-001" --version "V1"
hhzz-cli bom update status --body-json '<JSON>' --dry-run
hhzz-cli bom detail --material-code "FG-001" --version "V1"
```

验收要求：

- 父项成品、投入物料、用量、单位、BOM 版本和关联工艺路线正确。
- 指定工序投料必须能解析到真实路线节点。
- BOM 启用后才能进入工单阶段。

### 6.5 创建并下发工单

创建工单前，必须再次确认成品、BOM 和工艺路线均已验收。

```bash
hhzz-cli work-order import --body-json '<JSON>' --dry-run
hhzz-cli work-order detail base --code "WO-FG-001"
hhzz-cli work-order detail output --code "WO-FG-001"
hhzz-cli work-order detail input-material --code "WO-FG-001"
hhzz-cli work-order detail process-plan --code "WO-FG-001"
```

工单产出、用料和工序计划全部一致后，才允许进入下发审计。`work-order issue` 只生成/推进生产任务，不代表现场已经开工：

```bash
hhzz-cli work-order issue --body-json '<JSON>' --dry-run
```

用户完成业务审计并明确确认后真实执行：

```bash
hhzz-cli work-order issue --body-json '<JSON>' --confirm
```

### 6.6 验收生产任务

工单下发后查询关联生产任务：

```bash
hhzz-cli produce-task list --quick-search "WO-FG-001"
hhzz-cli produce-task detail --task-code "PT-FG-001"
hhzz-cli produce-task list planned-amount --task-code "PT-FG-001"
```

验收要求：

- 生产任务能回指到目标工单。
- 工序、目标计划数量和状态与工单下发结果一致。
- 状态只能描述为待执行、执行中等系统返回状态，不得自动说生产已经完成。

## 7. 使用示例

用户：

```text
把新品 FG-001 投产，BOM 版本 V1，计划生产 100 根，并生成生产任务
```

执行摘要：

```bash
hhzz-cli material detail --code "FG-001" --query-field 1,6,8
hhzz-cli process-route detail --code "ROUTE-FG-001"
hhzz-cli bom detail --material-code "FG-001" --version "V1"
hhzz-cli work-order import --body-json '<JSON>' --dry-run
hhzz-cli work-order issue --body-json '<JSON>' --dry-run
hhzz-cli produce-task list --quick-search "WO-FG-001"
```

回答示例：

```text
已将新品 FG-001 的投产准备推进到生产任务生成。

阶段证据：
- 成品：FG-001，生产单位和自制范围已通过 material detail 验收
- 工艺路线：ROUTE-FG-001，节点和工作中心已通过 process-route detail 验收
- BOM：V1，投入物料、用量和路线关系已通过 bom detail 验收
- 工单：WO-FG-001，产出、用料和工序计划已回查一致
- 生产任务：PT-FG-001，已关联目标工单，计划数量以 produce-task 返回为准

说明：当前终点是生产任务已生成，尚未执行领料、投料、报工或完工。
```

## 8. 故障排除

| 问题 | 处理方式 |
| --- | --- |
| `hhzz-cli` 不存在 | 提示用户先安装或联系服务商/IT 配置运行环境 |
| 未认证或权限不足 | 执行 `hhzz-cli auth status`，要求完成企业自建应用凭证和权限配置 |
| 主数据不唯一 | 展示候选编码、名称和状态，请用户确认唯一对象 |
| 成品不是自制 | 停止投产流程，要求先维护成品业务范围或生产信息 |
| BOM 结构不一致 | 不启用 BOM，不进入工单阶段，返回结构差异 |
| 写入响应未知 | 先按唯一编码回查；已落库则继续验收，未落库才报告阻塞 |
| 工单已下发 | 不重复下发，只继续回查生产任务 |
| 生产任务未生成 | 返回工单已下发证据和阻塞点，不声称生产已开始 |

## 9. 安全与边界

- 本专家包含写操作，但所有写操作必须遵循 `--dry-run`、用户确认、`--confirm` 和写后回查。
- 不在 Skill 文件中保存或展示企业真实 `app_key / app_secret`。
- 不把 CLI 原始响应中的敏感字段完整贴给终端用户；只提炼业务可读结果和必要证据。
- “工单已下发”不等于已经领料、投料、报工或完工。
- 已落库对象不能因为后续失败而自动删除、覆盖或重建；应返回最短恢复点。
