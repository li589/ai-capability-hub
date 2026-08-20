---
name: 盈绰服务云
category:
version: 2.3.4
author: 盈绰数科
description: |
  盈绰服务云物业运营助手，只负责把请求路由到当前 Go 版 CLI 已注册的业务模块，并执行最小必要的全局守卫。
  支持微信 Agent Pay（X402）付费资源流程：付费前置检查 weixinpay、HTTP 402 支付触发、支付后重试与 X-Out-Trade-No 订单号传递。
  Use when the user asks about 收费、催缴、欠费、列表筛选、以上/以下、分组、汇总、排行、Top N、前 N、短信、短信黑名单、黑名单、拉黑、禁止发短信、模板、收银台、应收管理、分享账单、缴费、缴款明细、缴款汇总、今日收款、当日收费、收费金额、收款日期、按收款时间查询、押金退款、退押金、押金可退、退款申请、退款审核、租客、租户、业主、房屋、房屋管理、添加租客、添加业主、客户管理、编辑客户、修改客户、客户信息编辑、修改手机号、修改客户姓名、房屋客户关系、员工、员工管理、员工状态、在职、离职、启用员工、关闭员工、账号状态、员工角色、工单、报事、报修、派单、认领、审批、转派、退回、撤销、评价、附件、多经、多业态营收、旅游、旅行团、跟团、旅游订单、店铺权限、闪购、日报、注册量、下单量、配送、送货上门, or related `yc-cloud` business workflows.
  Read the matching module file before execution. Do not use for guessed APIs, generic chat, or commands outside module allowlists.
---

# 盈绰服务云

## 欠费聚合快捷命令（催缴/欠费/排行/汇总/Top N 直接用）

范围确定后一条命令出结果，**不要探索文件系统、不要加 `--limit`**。`collection sms-task preview --query-plan` 内部按每页 500 自动翻页取全量（上限 50000），Agent 不要自己翻页。`count` 聚合**禁止带 `field`**（细节见 list-query.md）。

```bash
sh ./scripts/yc-cloud.sh collection sms-task preview --project-id <id> --require-page false --query-plan '<JSON计划>'
```

计划字段与合同见 [references/list-query.md](references/list-query.md)。展示场景不加 `--json`（stdout 已是表）；仅当结果要喂给下一条命令时才加 `--json`。

## Role

本文件只做三件事：

1. 判断请求属于哪个业务模块
2. 应用全局守卫
3. 把执行细节下沉到对应模块文件

本文件不承载参数细节，不承载长示例，不承载完整命令白名单。

## Scope

当前只覆盖以下已注册业务模块：

- `collection`
- `deposit-refund`
- `house`
- `employee`
- `order`
- `rebate`
- `travel`
- `flash`

另覆盖文档模块（非 CLI 子命令 allowlist）：

- `pay-x402`：微信 Agent Pay / X402 付费契约（HTTP 履约）

不覆盖：

- 泛化聊天
- 猜接口
- 历史命令
- 未在模块 allowlist 中出现的命令

## Global Truth

全局事实源顺序固定如下：

1. `AGENTS.md`
2. `references/runtime.md`（CLI 启动与调用方式）
3. `internal/app/app.go`
4. `docs/COMMAND_SPEC.md`
5. `references/list-query.md`（仅列表统计意图）
6. 对应模块文件
7. 对应模块源码

以下材料不是事实源：

- `dist/`
- 历史发布包说明
- 其他仓库同名实现
- README 中与当前源码冲突的描述

## Routing

- 付费资源、Agent Pay、X402、微信支付付费、`WeixinPay-Required`、支付服务
  - 先读 [pay-x402.md](references/pay-x402.md)，按其中付费前置检查 → 支付触发 → 重试 → 订单号传递 → 异常处理执行
  - 支付服务：`https://higress-gateway-test.evertro.tech/agentpay/api/resource`（独立 **agentpay-api**）
  - 未支付完成前，不得改走业务 CLI 命令履约同一付费内容

先判断是否为列表统计意图：请求同时包含业务对象，且包含“筛选、以上/以下、大于/小于、分组、汇总、合计、排行、Top N、前 N”之一。

- 命中列表统计意图：先读 [runtime.md](references/runtime.md) 和 [list-query.md](references/list-query.md)。
- `list-query.md` 已接入的数据源：直接按其查询计划合同执行，不先通读大型业务模块文件。
- 未接入、转为明细查询或进入写操作：再路由到下方对应模块。

按关键词进入模块（收费系统已按子域拆分为多个模块文件）：

- 催缴、欠费、收银台、分享账单、催缴通知单、违约金减免、短信、模板、短信黑名单、黑名单、拉黑、`collection sms-blacklist`、`collection`
  - 读 [collection.md](references/collection.md)
- 应收管理、应收入账、缴款明细、缴款汇总、今日收款、当日收费、收款日期、按收款时间查询、收缴率、预收余额、押金余额、欠费明细表、收费订单、票据更正、撤销订单、变更缴款人、账单调整、导入、多经、多业态营收
  - 读 [receivable.md](references/receivable.md)
- 租客、租户、业主、房屋、房屋管理、添加租客、添加业主、客户管理、编辑客户、修改客户、修改手机号、房屋客户关系、`house`
  - 读 [house.md](references/house.md)
- 员工、员工管理、员工状态、在职、离职、启用员工、关闭员工、停用员工、账号状态、员工角色、内部管理、`staff-manage`、`employee`
  - 读 [employee.md](references/employee.md)
- 押金退款、退押金、押金可退、退款申请、退款审核、`deposit-refund`
  - 读 [deposit-refund.md](references/deposit-refund.md)
- 工单、报事、报修、派单、认领、审批、转派、退回、撤销、评价、附件、`order`
  - 先读 [work-order.md](references/work-order.md)
  - 如果涉及共享收费前置条件，再读对应收费模块文件
- 旅游、旅行团、跟团、店铺权限、旅游订单、路线、团期、团管理、团明细、陪团、出行人、负责人项目关系、团期审核、`travel`
  - 读 [travel.md](references/travel.md)
- 闪购、日报、注册量、下单量、配送、送货上门、商圈订单数据、商圈数据、商圈运营数据、`flash`
  - 读 [flash.md](references/flash.md)

禁止一边执行一边临时改路由。

## CLI Invocation (Hard Rule)

执行任何 `yc-cloud` 命令前，必须先读 [runtime.md](references/runtime.md)。

本 Skill 包**不含**二进制文件。所有 `yc-cloud` 命令必须通过包内脚本执行：

```bash
sh ./scripts/yc-cloud.sh <子命令> [参数...]
```

脚本会自动从 CDN 下载 loader 和加密 core，校验 SHA256 后执行。这是正式发布链路，agent **只调用脚本**，不得复刻其内部的 manifest 下载、loader 下载或 `exec` 逻辑。

以下行为**严格禁止**：

- `which yc-cloud`
- `find ~ -name "yc-cloud"`
- 直接调用 `~/.yc-cloud/loader/` 下缓存二进制
- 自行下载 manifest / loader / core
- 手动写 `~/.yc-cloud/config.json`（必须用 `config set`）
- `go run .` / `make dev` 代替正式 CLI
- CLI 启动失败时改用直接 API 调用或自建 launcher

示例：

```bash
sh ./scripts/yc-cloud.sh config set apiKey sk-xxx
sh ./scripts/yc-cloud.sh health
sh ./scripts/yc-cloud.sh collection sms-task list-projects --json
```

文档中所有 `yc-cloud ...` 均表示 `sh ./scripts/yc-cloud.sh ...`。

## Global Guards

所有模块共享以下硬规则：

1. 只承认当前 Go 版 CLI 已注册命令
2. 只承认 `apiKey` 为持久化配置项
3. `BuildAPIBaseURL` 是构建注入，不是用户配置项
4. 不得脑补 `projectId`、`customerId`、`houseId`、`workOrderId`、`templateId`、`store-ids`
5. 模块内命令必须通过对应模块 allowlist 校验
6. 轻量预检成功一次后，不得重复执行同类预检
7. 基于当前上下文的整理任务，不得额外跑脚本或读取无关本地文件

## Stop Conditions

遇到以下情况必须停止：

1. 请求不属于任何已注册模块
2. 对应模块文件不允许该命令
3. 本地 CLI 不存在该命令
4. 缺少 `apiKey`
5. 缺少必要业务参数且当前上下文无法可靠补齐
6. 预检失败
7. 文档与当前源码冲突且无法以源码直接定论

停止时只允许输出：

- 当前版本不支持
- 当前模块不覆盖
- 缺少必要条件
- 需要补充明确参数
- 需要先更新 CLI

## Execution Order

所有模块统一执行顺序：

1. 读取 [runtime.md](references/runtime.md)，确认 CLI 启动方式
2. 路由到模块
3. 读取对应模块文件
4. 校验命令是否在模块 allowlist 中
5. 校验 `apiKey`
6. 进行一次模块规定的轻量预检
7. 校验模块参数白名单与默认值
8. 通过 `sh ./scripts/yc-cloud.sh` 执行命令
9. 仅在失败时回看对应源码和 `COMMAND_SPEC`

列表统计意图是唯一快速路径：

1. 读取 [runtime.md](references/runtime.md)
2. 读取 [list-query.md](references/list-query.md)
3. 确认数据源已接入，并校验其字段 schema
4. 如缺少必要业务范围，只做一次轻量预检
5. 生成受约束查询计划，执行一次已接入的列表命令
6. 直接展示紧凑结果；禁止临时编写 Python、`jq` 或其他分析脚本

## Non-Goals

本文件不负责：

- 逐命令参数说明
- 逐命令示例大全
- API 细节映射表
- 业务长背景说明

这些内容都应在模块文件中解决。
