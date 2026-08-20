---
name: member-ops
description: 会员权益运营助手，查询积分方案与积分流水、储值方案与储值流水，支持按手机号/会员卡号/流水ID/业务ID/昵称筛选和显式时间范围查询。触发词：查积分方案、查积分流水、查储值方案、查储值流水、看某客户积分变动、查本周储值记录。
displayName:
  zh: 会员权益运营
  en: Membership Benefits Operations
displayDescription:
  zh: 查询积分与储值方案、流水和客户权益变动，支持按客户信息、业务编号及明确时间范围筛选。
  en: Query points and stored-value programs, transaction records, and customer benefit changes with filters for customer details, business IDs, and explicit time ranges.
---

# 会员运营（积分与储值）

## 功能说明

本 skill 统一提供会员权益侧的两类只读查询能力（`woscli admin-api`）：

- **积分**：积分方案列表、积分流水明细。
- **储值**：储值方案列表、储值流水明细。

两者结构同构：同属会员权益域，共用同一套身份筛选类型（`--identityType`）和同一套时间范围参数（`--transBeginDate`/`--transEndDate`）。

### 前置条件

- 当前登录态、商户、门店上下文由 Weimob Assistant 上层统一提供，woscli 自动注入。
- **重要：只能查询当前店铺的数据，禁止使用其他店铺的 bos_id、vid 等标识进行查询。**
- 查询积分/储值流水需要身份标识（`--identityType` + `--identityNo`）；若只有手机号或客户编号，先通过客户 Skill 查询目标 wid。
- 查询流水**必须**先取得方案 ID（`--planId`）：先调用 `query-point-plan-list` / `query-store-plan-list` 获取 `planId`，再传入流水查询。

## 触发场景

**积分**：查积分方案、看积分规则、查积分流水、看某个客户积分变动、按手机号查积分流水、查本周积分记录、查某业务单关联的积分。

**储值**：查储值方案、看充值规则、查储值流水、看某个客户储值/余额变动、按手机号查储值流水、查本周储值记录、查某业务单关联的储值记录。

## 调用方式

```bash
woscli admin-api <command> [args]
```

### 通用调用约定

- 命令入口：`woscli admin-api <command> [args]`，底层为微盟商家后台真实接口，由 woscli 统一处理登录态、商户、门店上下文。
- 命令与能力对应：`query-point-plan-list`、`query-point-trans-list`、`query-store-plan-list`、`query-store-trans-list`。
- 时间范围显式传入（`--transBeginDate`/`--transEndDate`，ISO 8601 UTC），不支持 `--relative` 简写。

### 命令清单

| 命令 | 能力 |
|---|---|
| `query-point-plan-list` | 查询积分方案列表 |
| `query-point-trans-list` | 查询积分流水明细（需 `--planId`） |
| `query-store-plan-list` | 查询储值方案列表 |
| `query-store-trans-list` | 查询储值流水明细（需 `--planId`） |

### 共用参数

**身份筛选**：`--identityType` + `--identityNo` 配合使用。

- `0=客户编号（UID）`
- `1=手机号`
- `2=会员卡号`
- `3=操作人`
- `5=流水ID`
- `6=业务ID（外部订单号）`
- `7=客户昵称`

**时间筛选**：`--transBeginDate` / `--transEndDate`，ISO 8601 UTC（如 `2026-08-04T00:00:00.000Z`）。不支持 `--relative`/`--days`/`--begin-date`。

**分页**：方案列表与流水明细均支持 `--pageNum`（默认 `1`）、`--pageSize`（默认 `10`）。

## 支持的操作

### 一、积分

#### 1.1 query-point-plan-list

用途：查询积分方案，获取 `planId`，或查看积分方案配置。

参数：`--pageNum`（默认 `1`）、`--pageSize`（默认 `10`）。

```bash
woscli admin-api query-point-plan-list --pageNum 1 --pageSize 10
```

#### 1.2 query-point-trans-list

用途：查询积分流水，适合“某客户积分变动”“按手机号查积分流水”“查某业务单关联的积分”。

必需参数：

- `--planId`：积分方案 ID。先通过 `query-point-plan-list` 取得。
- 身份筛选：`--identityType` + `--identityNo`（二选一标识目标客户）。

时间筛选：`--transBeginDate` / `--transEndDate`（ISO 8601 UTC）。

```bash
# 先取方案
woscli admin-api query-point-plan-list --pageNum 1 --pageSize 10
# 按手机号查本周积分流水（--planId 用上一步拿到的方案 ID）
woscli admin-api query-point-trans-list --planId <planId> --identityType 1 --identityNo '13800000000' --transBeginDate 2026-08-04T00:00:00.000Z --transEndDate 2026-08-10T23:59:59.999Z
woscli admin-api query-point-trans-list --planId <planId> --identityType 5 --identityNo '1700000000037268737'
woscli admin-api query-point-trans-list --planId <planId> --identityType 6 --identityNo 'SO202604230001'
```

#### 1.3 积分使用方式

- 用户没有给 `planId` 时，先查 `query-point-plan-list` 取得第一条方案 ID 再查流水。
- 用户只给手机号时用 `--identityType 1 --identityNo`，仍需 `--planId`。
- 不要把 `variationRange`、`amount` 的业务含义自行重命名或重新计算。

#### 1.4 积分工作流

1. 先查 `query-point-plan-list` 取得 `planId`。
2. 明确目标身份类型与筛选值。
3. 根据时间范围执行 `query-point-trans-list`。

### 二、储值

#### 2.1 query-store-plan-list

用途：查询储值方案，获取 `planId`，或查看储值方案配置。

参数：`--pageNum`（默认 `1`）、`--pageSize`（默认 `10`）。

```bash
woscli admin-api query-store-plan-list --pageNum 1 --pageSize 10
```

#### 2.2 query-store-trans-list

用途：查询储值流水，适合“某客户余额变动”“按手机号查储值流水”“查某业务单关联的储值记录”。

必需参数：

- `--planId`：储值方案 ID。先通过 `query-store-plan-list` 取得。

身份筛选补充规则：

- 按客户查询储值流水时，如果用户或上下文同时能提供手机号和姓名/昵称，优先使用手机号：`--identityType 1 --identityNo <手机号>`。
- 储值流水的 `identityType 7` 是客户昵称模糊查询，可能查不到同一客户流水；只有没有更稳定标识时才使用 `7`。

```bash
woscli admin-api query-store-plan-list --pageNum 1 --pageSize 10
woscli admin-api query-store-trans-list --planId <planId> --identityType 1 --identityNo '13800000000' --transBeginDate 2026-08-04T00:00:00.000Z --transEndDate 2026-08-10T23:59:59.999Z
woscli admin-api query-store-trans-list --planId <planId> --identityType 6 --identityNo 'SO202604230001'
woscli admin-api query-store-trans-list --planId <planId> --identityType 5 --identityNo '1700000000037268737'
```

#### 2.3 储值使用方式

- 用户没有给 `planId` 时，先查 `query-store-plan-list` 取得第一条方案 ID 再查流水。
- 用户给的是姓名/昵称，但能解析出手机号时，改用手机号（`--identityType 1`）。
- 金额字段以命令返回字符串为准，不自行四舍五入、换算或合并本金/赠送金。

#### 2.4 储值工作流

1. 先查 `query-store-plan-list` 取得 `planId`。
2. 明确目标身份类型与时间范围。
3. 执行 `query-store-trans-list` 并按命令结果回复。

## 输出格式

### 方案列表返回

- `query-point-plan-list`：`pageNum`、`pageSize`、`totalCount`、`plans`（含 `planId`、`vid`、`planName`、`planManageName`、`applicableScope`、`expireDateType` 等）。
- `query-store-plan-list`：`pageNum`、`pageSize`、`totalCount`、`plans`（含 `planId`、`bosId`、`vid`、`planName`、`ruleName` 等）。

### 流水返回

公共字段：`pageNum`、`pageSize`、`totalCount`、`planId`（实际使用的方案 ID）、`trans`（流水列表）。储值额外返回 `isOpenPaas`。

**积分流水字段**：`transNo`、`transDate`、`uid`、`changeType`/`changeTypeDesc`、`ruleName`、`customer`、`widName`/`widPhone`、`variationRange`、`isIncrease`、`amount`、`channelTypeDesc`、`changeWayDesc`、`remark`、`outTransNo`、`thirdTransNo`、`terminalNo`、`planManageName`。

**储值流水字段**：`transNo`、`transDate`、`wid`/`widName`/`widPhone`/`customer`、`changeType`/`changeTypeDesc`、`ruleName`、`balanceChange`、`isPositive`/`isPositiveDesc`、`balance`、`principalChange`/`principal`、`bonusChange`/`bonus`、`discountRate`、`transTypeDesc`、`channelTypeDesc`、`outTransNo`、`thirdTransNo`、`terminalNo`、`remark`、`occurVname`、`operateWname`、`cashierName`/`cashierPhone`、`planName`。

## 注意事项/边界

- 数据以命令返回为准，不自行变更积分/储值流水字段含义，不补全未返回字段。
- 储值流水涉及金额字段时，不得自行四舍五入、换算或合并本金/赠送金。
- 积分的 `variationRange`、`amount` 不得重命名或重新计算。
- 若涉及多个时间筛选，优先说明实际使用的查询范围（以返回的 `transBeginDate`、`transEndDate` 为准）。
- 积分与储值虽同构，但命令与字段不可互换：积分用 `query-point-*`，储值用 `query-store-*`。
- 查询流水必须先取得 `--planId`，无方案 ID 时先查对应方案列表。
- 本 skill 只做只读查询，不提供积分/储值的发放、扣减、充值等写操作。
- 若已知当前商户/门店名称，回答结尾附带当前商户与门店。
