# 订单查询参考（query-orders / query-order-detail）

> 底层命令为 `woscli admin-api query-orders` 与 `query-order-detail`，由 woscli 统一处理登录态、商户、门店上下文。

## query-orders 参数词典

| 参数 | 说明 |
|---|---|
| `--pageNum` | 页码（从 1 开始） |
| `--pageSize` | 每页数量 |
| `--startTime` | 时间范围起点（必填，ISO 8601 UTC，如 `2026-08-04T00:00:00.000Z`，或毫秒时间戳） |
| `--endTime` | 时间范围终点（必填，ISO 8601 UTC） |
| `--queryTimeType` | 时间口径（必填，见下表） |
| `--orderStatuses` | 订单状态，多个用英文逗号分隔 |
| `--paymentStatuses` | 支付状态，多个用英文逗号分隔 |
| `--deliveryTypes` | 配送方式，多个用英文逗号分隔 |
| `--keyword` | 搜索关键词，需与 `--searchType` 配合 |
| `--searchType` | 搜索类型，见下表 |

> 不支持 `--relative` / `--days` / `--begin-date` / `--end-date` 简写：调用前先把相对时间或自然日范围换算为实际 ISO 8601 UTC 时间（某一日即起止为该日 `00:00:00.000Z` ~ `23:59:59.999Z`）。

## 时间类型（--queryTimeType）

| 值 | 含义 |
|---|---|
| `0` | 下单时间 |
| `2` | 支付时间 |
| `3` | 发货时间 |
| `4` | 预计配送时间 |
| `5` | 完成/核销时间 |

## 订单状态（--orderStatuses）

| 值 | 含义 |
|---|---|
| `0` | 创建 |
| `11` | 待确认 |
| `21` | 待发货 |
| `3` | 已发货 |
| `4` | 已完成 |
| `5` | 已取消 |

## 支付状态（--paymentStatuses）

| 值 | 含义 |
|---|---|
| `0` | 未支付 |
| `1` | 部分支付 |
| `2` | 已支付 |

## 配送方式（--deliveryTypes）

| 值 | 含义 |
|---|---|
| `1` | 商家配送 |
| `2` | 同城限时达 |
| `3` | 到店自提 |
| `4` | 门店交易 |
| `5` | 无需物流 |

## 搜索类型（--searchType）

| 值 | 含义 |
|---|---|
| `1` | 商品名称 |
| `2` | 商品编码 |
| `3` | 客户昵称 |
| `4` | 订单编号 |
| `5` | 收货人姓名 |
| `6` | 收货人手机号 |
| `7` | 交易单号 |
| `8` | 商户单号 |
| `9` | 自提点名称 |
| `10` | 提货码 |
| `37` | 通道单号 |

## query-orders 返回结构

- `totalCount`、`pageNum`、`pageSize` 或 `pageList` 内的列表项（以接口实际返回为准）。
- `orders`：订单列表，包含订单号、订单状态、支付方式、订单类型、配送方式、渠道、来源、创建/支付/完成时间、买家、商户、支付金额、物流、商品项。

## query-order-detail

参数：

- `--orderNo`：订单号，必填。

返回结构：

- `orderNo`、`status`、`statusToB`、`payStatus`、`payType`、`orderType`、`deliveryType`、`channelType`、`orderSource`
- `buyer`：wid、昵称、手机号、头像、匿名状态、买家备注
- `merchant`：商户与处理门店信息
- `payInfo`：订单金额、实付、应付、优惠、优惠券、支付明细
- `items`：商品项、SKU、数量、价格、图片、商品编码、售后信息
- `receiverInfo`、`logistics`、`discounts`、`cancelInfo`、`traceInfos`

## 示例

```bash
# 本周订单（将『本周』换算为实际 ISO 8601 时间；queryTimeType 0=下单时间）
woscli admin-api query-orders --startTime 2026-08-04T00:00:00.000Z --endTime 2026-08-10T23:59:59.999Z --queryTimeType 0
# 按订单号搜索
woscli admin-api query-orders --keyword 'SO202604230001' --searchType 4 --startTime 2026-04-01T00:00:00.000Z --endTime 2026-04-07T23:59:59.999Z --queryTimeType 0
# 指定状态（4=已完成）+ 时间范围
woscli admin-api query-orders --orderStatuses 4 --startTime 2026-04-01T00:00:00.000Z --endTime 2026-04-07T23:59:59.999Z --queryTimeType 0
# 订单详情
woscli admin-api query-order-detail --orderNo 'SO202604230001'
```
