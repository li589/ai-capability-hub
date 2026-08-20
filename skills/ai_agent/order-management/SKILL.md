---
name: order-management
description: 订单与售后查询助手，覆盖订单列表、订单详情、售后列表、售后详情，支持显式时间范围、订单状态、支付状态、配送方式与关键词筛选。触发词：查订单、订单详情、查售后、看退款单、本周订单。
displayName:
  zh: 订单与售后管理
  en: Order and After-sales Management
displayDescription:
  zh: 查询订单和售后单的列表与详情，支持按时间、状态、支付、配送方式及关键词进行筛选。
  en: Search order and after-sales lists or details using filters for time range,
    status, payment, delivery method, and keywords.
disable-model-invocation: true
---

# 订单管理

## 功能说明

本 skill 让 WAI 代表商家查询交易与售后单据，结果全部来自微盟商家后台真实接口（`woscli admin-api`），不做汇总建模，也不做数据写入。

| 能力 | 命令 | 产出 |
|---|---|---|
| 订单列表 | `woscli admin-api query-orders` | 分页订单明细列表 |
| 订单详情 | `woscli admin-api query-order-detail` | 单笔订单完整信息 |
| 售后列表 | `woscli admin-api query-rights` | 分页售后单明细列表 |
| 售后详情 | `woscli admin-api query-rights-detail` | 单笔售后单完整信息 |

### 前置条件

- 当前登录态、商户、门店上下文由 Weimob Assistant 上层统一提供，woscli 自动注入。
- 本 skill 不负责获取或写入会话级上下文数据。
- **重要：只能查询当前店铺的数据，禁止使用其他店铺的 bos_id、vid 等标识进行查询。**
- 列表类查询必须显式传入时间范围，不支持 `--relative` 简写（见「调用方式」）。

## 触发场景

- 查订单、看订单列表、翻页看订单、看本周/今天/近 7 天订单
- 查订单详情、按订单号查订单、看某笔订单的商品与物流
- 查售后、查退款、查退货、查换货、看售后单列表
- 查售后详情、按售后单号查处理进度
- 按订单状态、支付状态、配送方式筛选订单
- 按买家昵称、收货人手机号、交易单号搜订单

## 调用方式

```bash
woscli admin-api <command> [args]
```

### 通用调用约定

- 命令入口：`woscli admin-api <command> [args]`，底层为微盟商家后台真实接口，由 woscli 统一处理登录态、商户、门店上下文。
- 命令与能力对应：`query-orders`（订单列表）、`query-order-detail`（订单详情）、`query-rights`（售后列表）、`query-rights-detail`（售后详情）。
- **时间范围必须显式传入**：`query-orders` 与 `query-rights` 要求必填 `--startTime`、`--endTime`（ISO 8601 UTC，如 `2026-08-04T00:00:00.000Z`，或毫秒时间戳）与 `--queryTimeType`（`0`=下单时间、`2`=支付时间、`3`=发货时间、`4`=预计配送时间、`5`=完成/核销时间）；原 `--relative`/`--days`/`--begin-date` 简写不再支持，调用前先把相对时间换算为实际 ISO 8601 时间。
- 依赖上层提供登录态、当前商户、当前门店；缺失时按命令返回提示上层补齐。

### 能力路由

| 用户意图 | 处理方式 |
|---|---|
| 查订单列表、按时间/状态筛订单 | `query-orders` 并组合筛选参数 |
| 用户给出完整订单号 | `query-order-detail --orderNo` |
| 疑似订单号但不确定是否完整 | `query-orders --keyword ... --searchType 4` |
| 查退款、退货、换货、售后进度 | `query-rights` 或 `query-rights-detail` |
| 用户给出完整售后单号 | `query-rights-detail --rightsOrderNo` |
| 经营汇总、GMV 趋势、销量排行 | 不属于本 skill，转数据分析能力 |

## 支持的操作

### 1. 订单列表查询（query-orders）

| 用途 | 关键参数 |
|---|---|
| 分页 | `--pageNum`、`--pageSize` |
| 时间范围（必填） | `--startTime`、`--endTime`、`--queryTimeType` |
| 状态筛选 | `--orderStatuses`、`--paymentStatuses`、`--deliveryTypes` |
| 关键词搜索 | `--keyword` + `--searchType` |
| 按买家筛选 | 通过 `--keyword` + `--searchType 6`（收货人手机号）等 |

```bash
# 本周订单（将『本周』换算为实际 ISO 8601 时间；queryTimeType 0=下单时间）
woscli admin-api query-orders --startTime 2026-08-04T00:00:00.000Z --endTime 2026-08-10T23:59:59.999Z --queryTimeType 0
# 按订单号搜索
woscli admin-api query-orders --keyword 'SO202604230001' --searchType 4 --startTime 2026-04-01T00:00:00.000Z --endTime 2026-04-07T23:59:59.999Z --queryTimeType 0
# 指定状态（4=已完成）+ 时间范围
woscli admin-api query-orders --orderStatuses 4 --startTime 2026-04-01T00:00:00.000Z --endTime 2026-04-07T23:59:59.999Z --queryTimeType 0
```

完整枚举值（订单状态、支付状态、配送方式、时间类型、搜索类型）见 `@references/orders.md`。

### 2. 订单详情查询（query-order-detail）

| 用途 | 关键参数 |
|---|---|
| 按订单号查详情 | `--orderNo`（必填） |

```bash
woscli admin-api query-order-detail --orderNo 'SO202604230001'
```

### 3. 售后列表查询（query-rights）

| 用途 | 关键参数 |
|---|---|
| 分页 | `--pageNum`、`--pageSize` |
| 时间范围（必填） | `--startTime`、`--endTime`、`--queryTimeType`（售后固定 `0`=创建时间） |
| 状态筛选 | `--rightsStatuses`（多个用逗号分隔） |
| 类型筛选 | `--rightsTypes`：`1=退货退款`、`2=仅退款`、`5=换货` |

```bash
# 近 7 天售后，状态 1,2,6
woscli admin-api query-rights --startTime 2026-08-04T00:00:00.000Z --endTime 2026-08-10T23:59:59.999Z --queryTimeType 0 --rightsStatuses 1,2,6
```

完整售后状态枚举见 `@references/rights.md`。

### 4. 售后详情查询（query-rights-detail）

| 用途 | 关键参数 |
|---|---|
| 按售后单号查详情 | `--rightsOrderNo`（必填） |

```bash
woscli admin-api query-rights-detail --rightsOrderNo 'R202604230001'
```

### 5. 工作流

1. 先确定查询对象是订单还是售后，以及需要列表还是详情。
2. 组合时间（必填）、状态、关键词等筛选参数后执行命令。
3. 直接使用命令真实返回结果回复。
4. 若缺少认证、商户或门店上下文，明确提示上层补齐后再继续。

## 输出格式

### query-orders / query-rights 列表返回

- `totalCount`、`pageNum`、`pageSize` 或 `pageList` 内的列表项（以接口实际返回为准）。
- 订单项含订单号、订单状态、支付方式、订单类型、配送方式、渠道、来源、创建/支付/完成时间、买家、商户、支付金额、物流、商品项。
- 售后项含售后单号、申请 ID、状态、类型、来源、渠道、买家、退款金额、创建时间、原订单号、售后商品。

### query-order-detail 返回

- 单据主体：`orderNo`、`status`、`statusToB`、`payStatus`、`payType`、`orderType`、`deliveryType`、`channelType`、`orderSource`。
- 关联对象：`buyer`、`merchant`、`payInfo`、`items`、`receiverInfo`、`logistics`、`discounts`、`cancelInfo`、`traceInfos`。

### query-rights-detail 返回

- 售后单号、申请 ID、状态、类型、来源、原因、自动处理时间、退款失败原因。
- 买家信息、商户信息、原订单、退款详情、售后商品、退货物流、售后轨迹、标记信息。

### 回复要求

- 列表、详情、售后单据都只返回命令真实结果，不捏造、不补全字段。
- 若使用了显式时间范围，回答中注明实际查询的时间范围。
- 若已知当前商户/门店名称，回答结尾附带当前商户与门店。

## 注意事项/边界

- 订单与售后数据包含手机号、收货地址、买家姓名等敏感字段，自然语言回复中只展开完成任务必需的字段。
- 不向用户暴露 token、bosId、vid 等内部标识。
- 本 skill 只做单据明细查询，不做经营汇总、趋势、同环比、排行分析；此类诉求转交数据分析能力。
- 本 skill 不做任何写操作，不支持改价、发货、审核售后、取消订单。
- `query-orders` 的 `--keyword` 必须与 `--searchType` 配合使用；不确定手机号是买家还是收货人时，用 `--searchType 6`（收货人手机号）。
